#!/usr/bin/env python3
"""Recompute published IC 10 per-OID statistics from frozen ZTF DR15 Parquet files.

The public light-curve API can serve a newer release than a paper's frozen
catalog. This check therefore reads the archived DR15 Parquet files directly,
downloads only the field/CCD/quadrant/filter files required by a deterministic
sample, and records file hashes and object-level provenance.
"""
from __future__ import annotations

import hashlib
import http.client
import io
import json
import re
import time
import urllib.error
import urllib.parse
import urllib.request
from html.parser import HTMLParser
from pathlib import Path
from tempfile import TemporaryDirectory

import numpy as np
import pandas as pd

BASE = "https://zenodo.org/records/14979711/files"
DR15_BASE = "https://irsa.ipac.caltech.edu/data/ZTF/lc/lc_dr15"
FILES = {
    "df_zr.csv": "0589a1bda6abd960145ad6116275851d",
    "df_zg.csv": "3cb5b49b1064a2bac0bc7ab9201fa0e0",
}
SAMPLE_PER_BAND = 10
SAMPLE_SEED = 20261020
TOLERANCE_MAG = 1e-3
CUTOFF_MJD = 59892.0
FILTER_CODE = {1: "zg", 2: "zr", 3: "zi"}
EXPECTED_FILTER = {"g": 1, "r": 2}


class HrefParser(HTMLParser):
    """Collect links from the IRSA directory listing."""

    def __init__(self) -> None:
        super().__init__()
        self.hrefs: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag.lower() == "a":
            for key, value in attrs:
                if key.lower() == "href" and value:
                    self.hrefs.append(value)


def request_bytes(url: str, timeout: int = 90) -> tuple[bytes, int]:
    request = urllib.request.Request(
        url,
        headers={"User-Agent": "ztf-classifier-independent-validation/1.0"},
    )
    for attempt in range(3):
        try:
            with urllib.request.urlopen(request, timeout=timeout) as response:
                return response.read(), attempt + 1
        except urllib.error.HTTPError as exc:
            if exc.code not in (408, 429) and exc.code < 500:
                raise
            if attempt == 2:
                raise
            time.sleep(2**attempt)
        except (urllib.error.URLError, http.client.HTTPException, TimeoutError, OSError):
            if attempt == 2:
                raise
            time.sleep(2**attempt)
    raise RuntimeError(f"Could not retrieve {url}")


def download_catalog(name: str, root: Path) -> tuple[pd.DataFrame, dict[str, object]]:
    url = f"{BASE}/{name}?download=1"
    payload, attempts = request_bytes(url, timeout=60)
    md5 = hashlib.md5(payload).hexdigest()
    if md5 != FILES[name]:
        raise RuntimeError(f"{name}: publisher MD5 mismatch: {md5}")
    path = root / name
    path.write_bytes(payload)
    frame = pd.read_csv(path, dtype={"SourceID": "string", "OID": "string"})
    required = {"SourceID", "OID", "numobs", "mean", "std", "min", "max"}
    if not required.issubset(frame.columns):
        raise RuntimeError(f"{name}: missing columns {sorted(required - set(frame.columns))}")
    return frame, {
        "url": url,
        "bytes": len(payload),
        "attempts": attempts,
        "md5": md5,
        "sha256": hashlib.sha256(payload).hexdigest(),
        "rows": int(len(frame)),
        "unique_source_ids": int(frame["SourceID"].nunique()),
    }


def parse_oid(oid: str) -> dict[str, int]:
    value = str(oid).strip()
    if not value.isdigit() or len(value) not in (15, 16):
        raise ValueError(f"Unsupported ZTF OID encoding: {oid!r}")
    parts = {
        "fieldid": int(value[:-12]),
        "filterid": int(value[-12]),
        "ccdid": int(value[-11:-9]),
        "qid": int(value[-9]),
        "object_index": int(value[-8:]),
    }
    if parts["filterid"] not in FILTER_CODE or not 1 <= parts["ccdid"] <= 16 or not 1 <= parts["qid"] <= 4:
        raise ValueError(f"OID components out of range for {oid}: {parts}")
    parts["rcid"] = (parts["ccdid"] - 1) * 4 + parts["qid"] - 1
    return parts


def field_directory(fieldid: int) -> str:
    return f"{DR15_BASE}/{fieldid // 1000}/field{fieldid:04d}"


def list_parquet_links(directory_url: str) -> list[str]:
    payload, _ = request_bytes(directory_url, timeout=20)
    parser = HrefParser()
    parser.feed(payload.decode("utf-8", errors="replace"))
    return [
        urllib.parse.urljoin(directory_url + "/", href)
        for href in parser.hrefs
        if urllib.parse.urlparse(href).path.lower().endswith(".parquet")
    ]


def find_parquet_url(
    oid: str,
    band: str,
    directory_cache: dict[int, list[str]],
) -> tuple[str, dict[str, int]]:
    parts = parse_oid(oid)
    if parts["filterid"] != EXPECTED_FILTER[band]:
        raise RuntimeError(
            f"OID {oid} encodes filterid={parts['filterid']}, but catalog band is {band}"
        )
    fieldid = parts["fieldid"]
    if fieldid not in directory_cache:
        directory_url = field_directory(fieldid)
        try:
            links = list_parquet_links(directory_url)
        except urllib.error.HTTPError as exc:
            raise RuntimeError(
                f"Could not access DR15 field directory {directory_url} for OID {oid}: HTTP {exc.code}"
            ) from exc
        if not links:
            raise RuntimeError(
                f"DR15 field directory {directory_url} is accessible but contains no Parquet links"
            )
        directory_cache[fieldid] = links
    code = FILTER_CODE[parts["filterid"]]
    pattern = re.compile(
        rf"_{code}_c{parts['ccdid']:02d}_q{parts['qid']}(?:_|\.)",
        flags=re.IGNORECASE,
    )
    matches = [
        url for url in directory_cache[fieldid]
        if pattern.search(urllib.parse.urlparse(url).path.rsplit("/", 1)[-1])
    ]
    if len(matches) != 1:
        examples = [url.rsplit("/", 1)[-1] for url in matches[:10]]
        raise RuntimeError(
            f"Expected one DR15 Parquet file for OID {oid}; found {len(matches)} "
            f"in {directory_url}; matches={examples}"
        )
    return matches[0], parts


def load_parquet(url: str, file_cache: dict[str, tuple[pd.DataFrame, dict[str, object]]]) -> tuple[pd.DataFrame, dict[str, object]]:
    if url in file_cache:
        return file_cache[url]
    payload, attempts = request_bytes(url, timeout=120)
    digest = hashlib.sha256(payload).hexdigest()
    frame = pd.read_parquet(io.BytesIO(payload), engine="pyarrow")
    required = {"objectid", "fieldid", "filterid", "rcid", "nepochs", "hmjd", "mag", "magerr", "catflags"}
    if not required.issubset(frame.columns):
        raise RuntimeError(f"{url}: Parquet missing columns {sorted(required - set(frame.columns))}")
    meta = {
        "url": url,
        "filename": url.rsplit("/", 1)[-1],
        "bytes": len(payload),
        "attempts": attempts,
        "sha256": digest,
        "rows_in_file": int(len(frame)),
    }
    file_cache[url] = (frame, meta)
    return frame, meta


def raw_lightcurve(
    oid: str,
    band: str,
    directory_cache: dict[int, list[str]],
    file_cache: dict[str, tuple[pd.DataFrame, dict[str, object]]],
) -> tuple[pd.DataFrame, dict[str, object]]:
    url, parts = find_parquet_url(oid, band, directory_cache)
    frame, file_meta = load_parquet(url, file_cache)
    object_ids = pd.to_numeric(frame["objectid"], errors="coerce")
    matches = frame.loc[object_ids == int(oid)]
    if len(matches) != 1:
        raise RuntimeError(f"{url}: expected one row for OID {oid}, found {len(matches)}")
    row = matches.iloc[0]
    if int(row["fieldid"]) != parts["fieldid"] or int(row["filterid"]) != parts["filterid"] or int(row["rcid"]) != parts["rcid"]:
        raise RuntimeError(f"DR15 Parquet metadata does not agree with encoded OID {oid}")
    hmjd = np.asarray(row["hmjd"], dtype=float).reshape(-1)
    mag = np.asarray(row["mag"], dtype=float).reshape(-1)
    magerr = np.asarray(row["magerr"], dtype=float).reshape(-1)
    catflags = np.asarray(row["catflags"], dtype=float).reshape(-1)
    lengths = {len(hmjd), len(mag), len(magerr), len(catflags)}
    if len(lengths) != 1:
        raise RuntimeError(f"OID {oid}: inconsistent Parquet array lengths {sorted(lengths)}")
    lightcurve = pd.DataFrame({"mjd": hmjd, "mag": mag, "magerr": magerr, "catflags": catflags})
    meta = {
        "source": "ZTF DR15 archived Parquet",
        "parquet_url": url,
        "parquet_filename": file_meta["filename"],
        "parquet_bytes": file_meta["bytes"],
        "parquet_sha256": file_meta["sha256"],
        "fieldid": parts["fieldid"],
        "filterid": parts["filterid"],
        "ccdid": parts["ccdid"],
        "qid": parts["qid"],
        "rcid": parts["rcid"],
        "time_column": "hmjd",
        "raw_rows": int(len(lightcurve)),
        "parquet_nepochs": int(row["nepochs"]),
        "negative_magerr_count": int((np.isfinite(magerr) & (magerr < 0)).sum()),
        "catflags_zero_count": int((catflags == 0).sum()),
    }
    return lightcurve, meta


def stats(frame: pd.DataFrame) -> dict[str, float | int]:
    values = pd.to_numeric(frame["mag"], errors="coerce").to_numpy(dtype=float)
    values = values[np.isfinite(values)]
    if not len(values):
        raise RuntimeError("No finite magnitudes after filtering")
    return {
        "n": int(len(values)),
        "mean": float(np.mean(values)),
        "std": float(np.std(values, ddof=0)),
        "min": float(np.min(values)),
        "max": float(np.max(values)),
    }


def profiles(raw: pd.DataFrame, band: str) -> dict[str, dict[str, float | int]]:
    finite = raw[np.isfinite(raw["mjd"]) & np.isfinite(raw["mag"])].copy()
    good = finite[finite["catflags"] == 0].copy()
    cutoff = good[good["mjd"] < CUTOFF_MJD].copy()
    paper = cutoff.copy()
    if band == "r":
        for low, high in ((58481.0, 58482.0), (58472.0, 58474.0), (59032.0, 59033.0)):
            paper = paper[(paper["mjd"] < low) | (paper["mjd"] > high)]
    return {
        "raw_finite": stats(finite),
        "dr15_clean": stats(good),
        "dr15_clean_before_cutoff": stats(cutoff),
        "paper_plot_filters": stats(paper),
    }


def main() -> None:
    report: dict[str, object] = {
        "dataset": "ZTF IC 10 variable catalog",
        "doi": "10.5281/zenodo.14979711",
        "test": "published per-OID mean/std/min/max versus archived ZTF DR15 Parquet light curves",
        "archive_base": DR15_BASE,
        "sample_per_band": SAMPLE_PER_BAND,
        "sample_seed": SAMPLE_SEED,
        "tolerance_magnitude": TOLERANCE_MAG,
        "time_note": "DR15 Parquet stores HMJD rather than the API's MJD; statistics use magnitudes, and time cuts are diagnostic. The frozen DR15 archive already bounds the release's observation span.",
        "filter_profiles": {
            "raw_finite": "finite magnitudes from archived DR15 light curve",
            "dr15_clean": "finite magnitudes with catflags == 0; primary acceptance profile",
            "dr15_clean_before_cutoff": "catflags == 0 and HMJD < 59892",
            "paper_plot_filters": "previous profile; for r also excludes three MJD intervals used by the authors' public plotting code",
        },
        "limitations": [
            "Only a deterministic 10-OID sample per band is recomputed.",
            "This does not evaluate classifier accuracy or reproduce all variability/period filters.",
        ],
        "catalogs": {},
        "comparisons": [],
        "parquet_files": [],
    }
    directory_cache: dict[int, list[str]] = {}
    file_cache: dict[str, tuple[pd.DataFrame, dict[str, object]]] = {}
    with TemporaryDirectory(prefix="ztf-ic10-dr15-validation-") as tmp:
        root = Path(tmp)
        samples: dict[str, pd.DataFrame] = {}
        try:
            for filename, band in (("df_zr.csv", "r"), ("df_zg.csv", "g")):
                frame, meta = download_catalog(filename, root)
                sample = frame.sample(
                    n=min(SAMPLE_PER_BAND, len(frame)),
                    random_state=SAMPLE_SEED,
                ).sort_values(["SourceID", "OID"])
                samples[band] = sample
                report["catalogs"][band] = meta

            known_field_url = f"{DR15_BASE}/0/field0697"
            try:
                known_links = list_parquet_links(known_field_url)
            except Exception as exc:
                report["archive_root_probe"] = {
                    "url": known_field_url,
                    "status": "UNAVAILABLE",
                    "error": f"{type(exc).__name__}: {exc}",
                }
                report["result"] = "BLOCKED"
                print(json.dumps(report, indent=2, sort_keys=True))
                raise SystemExit(2) from exc
            report["archive_root_probe"] = {
                "url": known_field_url,
                "status": "AVAILABLE",
                "parquet_link_count": len(known_links),
            }
            if not known_links:
                report["archive_root_probe"]["status"] = "NO_PARQUET_LINKS"
                report["result"] = "BLOCKED"
                print(json.dumps(report, indent=2, sort_keys=True))
                raise SystemExit(2)
            directory_cache[697] = known_links

            comparisons = report["comparisons"]
            for band in ("r", "g"):
                for row in samples[band].to_dict(orient="records"):
                    oid = str(row["OID"])
                    raw, raw_meta = raw_lightcurve(oid, band, directory_cache, file_cache)
                    by_profile = profiles(raw, band)
                    entry: dict[str, object] = {
                        "band": band,
                        "SourceID": str(row["SourceID"]),
                        "OID": oid,
                        "catalog_numobs": int(row["numobs"]),
                        "published": {key: float(row[key]) for key in ("mean", "std", "min", "max")},
                        "raw": raw_meta,
                        "profiles": {},
                    }
                    for profile_name, observed in by_profile.items():
                        deltas = {
                            key: abs(float(observed[key]) - float(row[key]))
                            for key in ("mean", "std", "min", "max")
                        }
                        entry["profiles"][profile_name] = {
                            "observed": observed,
                            "absolute_deltas": deltas,
                            "within_tolerance": max(deltas.values()) <= TOLERANCE_MAG,
                        }
                    comparisons.append(entry)
            report["parquet_files"] = sorted(file_cache.values(), key=lambda item: str(item[1]["url"]))
            report["parquet_files"] = [meta for _, meta in report["parquet_files"]]
        except Exception as exc:
            report["source_failure"] = {
                "error": f"{type(exc).__name__}: {exc}",
                "completed_comparisons_before_failure": len(report["comparisons"]),
                "downloaded_parquet_files": len(file_cache),
                "field_directories_inspected": sorted(directory_cache),
            }
            report["parquet_files"] = [meta for _, meta in file_cache.values()]
            report["result"] = "BLOCKED"
            print(json.dumps(report, indent=2, sort_keys=True))
            raise SystemExit(2) from exc

    comparisons = report["comparisons"]
    global_profiles: dict[str, object] = {}
    for profile_name in ("raw_finite", "dr15_clean", "dr15_clean_before_cutoff", "paper_plot_filters"):
        passing_oids = sum(
            1 for entry in comparisons
            if entry["profiles"][profile_name]["within_tolerance"]
        )
        global_profiles[profile_name] = {
            "oids_within_tolerance": passing_oids,
            "sampled_oids": len(comparisons),
            "all_oids_within_tolerance": passing_oids == len(comparisons),
        }
    primary = global_profiles["dr15_clean"]
    report["summary"] = {
        "sampled_oids": len(comparisons),
        "global_profile_results": global_profiles,
        "catalog_numobs_matches_parquet_nepochs": sum(
            1 for entry in comparisons
            if entry["catalog_numobs"] == entry["raw"]["parquet_nepochs"]
        ),
        "pass": primary["all_oids_within_tolerance"],
        "pass_rule": "All sampled OIDs must reproduce published mean/std/min/max within 0.001 mag using the same frozen DR15 archive and catflags == 0. Plot-only date exclusions cannot rescue a mismatch.",
    }
    report["result"] = "PASS" if report["summary"]["pass"] else "FAIL"
    print(json.dumps(report, indent=2, sort_keys=True))
    if report["result"] != "PASS":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
