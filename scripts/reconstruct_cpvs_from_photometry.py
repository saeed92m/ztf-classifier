"""Reconstruct CPVS membership from the publisher's documented criterion.

Why this exists
---------------
The selection rule actually documented by Chan+ 2022 (J/ApJ/932/118, §II.1, and
repeated in the CDS ReadMe) is:

    "We extract 730,184 out of 781,602 available periodic variable star light
     curves in the ZTF CPVS which contain at least one 2.5-sigma and 3-sigma
     detection in g- and r-band, respectively."

That rule is computable from the single-exposure photometry in
``J/ApJS/249/18/ztf2g.dat`` and ``ztf2r.dat``. Until this script existed, the
project had never evaluated it: the predicate in use is

    gmag > 0 AND rmag > 0 AND Per-g > 0 AND Per-r > 0

which is the *null-exclusion* predicate over the four nullable columns of
``table2.dat``. That predicate reproducing the published count is evidence, but it
is not evidence about the documented rule. This script evaluates the documented
rule directly so the two can be compared on the same hashed inputs.

What it deliberately does NOT do
--------------------------------
It does not decide which route is correct. It reports the exact set difference
between every route and refuses to emit a "resolved" verdict. Choosing the route
that matches 730,184 is precisely the kind of count-driven inference this
investigation forbids.

Two definitions are genuinely unknown and are therefore made explicit instead of
being silently assumed:

``snr_method``
    ZTF photometry publishes magnitude and magnitude error, not flux. For
    ``m = -2.5 log10(f)``, ``sigma_m = (1.0857 / f) sigma_f``, so the physically
    correct signal-to-noise is ``f / sigma_f = 1.0857 / sigma_m``, which is
    independent of the magnitude. A common but physically incorrect shortcut is
    ``m / sigma_m``. The two give materially different answers for faint
    detections, so both are computed and the disagreement is reported.

``flag_policy``
    Chan+ 2022 states the sigma criterion and says nothing about flags. Chen+
    2020 section III does state the cut used to build the parent catalogue:
    ``INFOBITS < 33,554,432`` and ``catflags != 32768``. Neither is reproduced,
    for two checkable reasons. The CDS ReadMe gives the Flag column of
    ztf2[gr].dat the range ``[0/4628]``, so the value Chen removes (32768) never
    occurs here and re-applying the cut would be a no-op. ``INFOBITS`` is image
    level and appears in no file. Two policies remain meaningful: no cut
    (closest to Chan+ 2022) and "any nonzero flag", which is explicitly a
    sensitivity check because nothing documents it.

A run is only interpretable if the caller states, in the output, which definitions
were used. The manifest does that.

Status
------
This script is exercised by ``tests/test_cpvs_documented_rule.py`` against
synthetic fixtures only. It has **not** been run against the real catalogues,
because ``cdsarc.cds.unistra.fr`` and the GitHub Actions artifact host are not
reachable from the environment where it was written. Any report it produces
records ``"validated_on_real_data": false`` until that changes.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from dataclasses import asdict, dataclass
from pathlib import Path

# 1.0857 = 2.5 / ln(10): the factor converting a relative flux error to a
# magnitude error, hence the inverse for signal-to-noise from magnitude error.
MAG_TO_FLUX_SNR_FACTOR = 2.5 / 2.302585092994046

# CDS J/ApJS/249/18 ztf2[gr].dat, Lrecl 75. Slice end is exclusive.
PHOTOMETRY_FIXED_WIDTH = {
    "seq": slice(0, 6),
    "mjd": slice(31, 44),
    "mag": slice(45, 55),
    "e_mag": slice(56, 70),
    "flag": slice(71, 75),
}

# CDS J/ApJS/249/18 table2.dat, Lrecl 228.
TABLE2_FIXED_WIDTH = {
    "name": slice(0, 22),
    "seq": slice(23, 29),
    "per": slice(50, 61),
    "gmag": slice(89, 95),
    "rmag": slice(96, 102),
    "per_g": slice(103, 116),
    "per_r": slice(117, 130),
}

# CDS J/ApJ/932/118 table4.dat, Lrecl 63.
TABLE4_FIXED_WIDTH = {
    "name": slice(0, 22),
    "id": slice(23, 29),
}


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def md5_file(path: Path) -> str:
    """md5 is not a security primitive; it is used only because the publisher
    of Zenodo record 3886372 publishes md5, so it is the one checksum that can
    actually be compared against a source that predates this work."""
    digest = hashlib.md5()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def verify_publisher_checksums(
    paths: dict[str, Path], manifest_path: Path
) -> list[dict[str, object]]:
    """Compare local files against the md5 values declared in the acquisition
    manifest. Publisher md5 is preferred because it is independent of us; when
    the publisher supplies none the entry is reported as unverifiable rather
    than as a pass.
    """
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    declared = {entry["id"]: entry for entry in manifest["inputs"]}

    results: list[dict[str, object]] = []
    for label, path in paths.items():
        entry = declared.get(label)
        if entry is None:
            raise ValueError(f"manifest declares no input {label!r}")
        expected = entry.get("md5_published_by_publisher")
        actual = md5_file(path)
        if expected is None:
            verdict = "NO_PUBLISHER_CHECKSUM"
        elif actual == expected:
            verdict = "MATCH"
        else:
            verdict = "MISMATCH"
        results.append(
            {
                "input": label,
                "md5_actual": actual,
                "md5_expected": expected,
                "verdict": verdict,
            }
        )

    mismatched = [r["input"] for r in results if r["verdict"] == "MISMATCH"]
    if mismatched:
        raise ValueError(
            "downloaded files do not match the publisher checksums: "
            + ", ".join(sorted(mismatched))
        )
    return results


def normalize_name(value: str) -> str:
    """Case and whitespace only; conservative by design."""
    return "".join(value.split()).upper()


# Flag policies.
#
# Chen+ 2020 section III states the photometry cut it applied when building the
# parent catalogue: "INFOBITS < 33,554,432 and catflags != 32,768". That cut is
# NOT reproduced here, and the reason is quotable rather than assumed: the CDS
# ReadMe for J/ApJS/249/18 gives the Flag column of ztf2[gr].dat the range
# [0/4628]. Since 32768 is outside that range, the value Chen's cut removes does
# not occur in these files - the cut has already been applied upstream, so
# re-applying it would be a provable no-op and could not be presented as a
# distinct policy without misleading the reader.
#
# INFOBITS is an image-level bitmask that appears in none of the four files, so
# it cannot be reproduced at all. It is recorded as UNKNOWN, not approximated.
#
# Chan+ 2022 states only the 2.5-sigma/3-sigma criterion and says nothing about
# flags. Two policies therefore remain meaningful.
FLAG_POLICIES = {
    "none": "no flag cut; closest to Chan+ 2022, which states none",
    "any_nonzero": "exclude any nonzero flag; undocumented, sensitivity check only",
}


def flag_is_usable(flag_policy: str, flag: int | None) -> bool:
    if flag_policy == "none":
        return True
    if flag_policy == "any_nonzero":
        return flag == 0
    raise ValueError(f"unknown flag_policy: {flag_policy!r}")


@dataclass(frozen=True)
class DetectionRule:
    """The documented criterion, with the details the sources leave open.

    ``snr_method`` and ``flag_policy`` are NOT settled by the primary source; see
    FLAG_POLICIES above and the module docstring. Both are evaluated rather than
    chosen, because choosing either would be an unstated assumption.
    """

    g_sigma: float = 2.5
    r_sigma: float = 3.0
    snr_method: str = "inverse_error"
    flag_policy: str = "none"

    def __post_init__(self) -> None:
        if self.flag_policy not in FLAG_POLICIES:
            raise ValueError(f"unknown flag_policy: {self.flag_policy!r}")

    def signal_to_noise(self, magnitude: float, magnitude_error: float) -> float:
        if magnitude_error <= 0.0:
            return 0.0
        if self.snr_method == "inverse_error":
            return MAG_TO_FLUX_SNR_FACTOR / magnitude_error
        if self.snr_method == "magnitude_over_error":
            return magnitude / magnitude_error
        raise ValueError(f"unknown snr_method: {self.snr_method!r}")


def read_table2(path: Path) -> dict[int, dict[str, object]]:
    """Parse ``table2.dat``: Seq, object name, and the four nullable fields."""
    rows: dict[int, dict[str, object]] = {}
    names: set[str] = set()
    with path.open("r", encoding="utf-8-sig", errors="replace") as handle:
        for line_number, line in enumerate(handle, start=1):
            if not line.strip() or line.lstrip().startswith("#"):
                continue
            raw_seq = line[TABLE2_FIXED_WIDTH["seq"]].strip()
            raw_name = line[TABLE2_FIXED_WIDTH["name"]].strip()
            if not raw_seq and not raw_name:
                continue
            if not raw_seq.isdigit():
                raise ValueError(
                    f"{path}:{line_number}: Seq is not an integer ({raw_seq!r}); "
                    "the fixed-width layout does not match the ReadMe"
                )
            seq = int(raw_seq)
            if seq in rows:
                raise ValueError(f"{path}:{line_number}: duplicate Seq {seq}")
            name = normalize_name(raw_name)
            if name in names:
                raise ValueError(
                    f"{path}:{line_number}: duplicate normalized object name {raw_name!r}"
                )
            names.add(name)
            rows[seq] = {
                "name": name,
                "gmag": _nullable_float(line[TABLE2_FIXED_WIDTH["gmag"]]),
                "rmag": _nullable_float(line[TABLE2_FIXED_WIDTH["rmag"]]),
                "per_g": _nullable_float(line[TABLE2_FIXED_WIDTH["per_g"]]),
                "per_r": _nullable_float(line[TABLE2_FIXED_WIDTH["per_r"]]),
            }
    if not rows:
        raise ValueError(f"{path}: no rows parsed")
    return rows


def _nullable_float(raw: str) -> float | None:
    """Parse a CDS ``?=0`` nullable numeric field. Null is None, never 0.0.

    Treating the ``0`` sentinel as a real value of zero is what makes a
    positivity test accidentally work as a presence test. Keeping None distinct
    forces the predicate to say which it means.
    """
    text = raw.strip()
    if not text:
        return None
    try:
        value = float(text)
    except ValueError:
        return None
    if value == 0.0:
        return None
    return value


def read_table4(path: Path) -> tuple[dict[str, int], set[int]]:
    """Return (name -> table4 ID, set of table4 IDs)."""
    name_to_id: dict[str, int] = {}
    ids: set[int] = set()
    with path.open("r", encoding="utf-8-sig", errors="replace") as handle:
        for line_number, line in enumerate(handle, start=1):
            if not line.strip() or line.lstrip().startswith("#"):
                continue
            raw_name = line[TABLE4_FIXED_WIDTH["name"]].strip()
            raw_id = line[TABLE4_FIXED_WIDTH["id"]].strip()
            if not raw_id.isdigit():
                raise ValueError(
                    f"{path}:{line_number}: Table 4 ID is not an integer ({raw_id!r})"
                )
            object_id = int(raw_id)
            name = normalize_name(raw_name)
            if not name:
                raise ValueError(f"{path}:{line_number}: blank object name")
            if name in name_to_id:
                raise ValueError(
                    f"{path}:{line_number}: duplicate object name {raw_name!r}"
                )
            if object_id in ids:
                raise ValueError(
                    f"{path}:{line_number}: duplicate Table 4 ID {object_id}"
                )
            name_to_id[name] = object_id
            ids.add(object_id)
    if not ids:
        raise ValueError(f"{path}: no rows parsed")
    return name_to_id, ids


# A layout error produces wholesale parse failure, not an occasional blank field.
# Any failure rate above this is treated as "the parser does not match this file"
# and aborts. It is a guard against silent miscounting, not a scientific cut: it
# never changes which rows qualify, only whether we trust the parse at all.
MAX_UNPARSED_FRACTION = 0.01

# Both conditions must hold before the guard fires. The count floor keeps a small
# fixture with one legitimately blank field from looking like a wholesale layout
# mismatch, while an 89,697,393-row file with the wrong offsets trips it at once.
MIN_UNPARSED_TO_ABORT = 100


def qualifying_sequences(
    path: Path,
    rule: DetectionRule,
    sigma: float,
    stats: dict[str, int] | None = None,
) -> set[int]:
    """Sequences with at least one detection at or above ``sigma``.

    Streams the file: ``ztf2g.dat`` and ``ztf2r.dat`` are 89,697,393 rows each, so
    the only state kept is the set of qualifying sequences (bounded by 781,604).

    Rows that cannot be parsed are counted, never silently dropped. An earlier
    implementation in this project skipped unreadable rows, which turned a parse
    failure into an empty set and therefore into a plausible-looking "clean"
    result. A high failure rate now raises instead.
    """
    qualifying: set[int] = set()
    counts = stats if stats is not None else {}
    for key in ("rows", "unparsed", "nonpositive_error", "blank"):
        counts.setdefault(key, 0)

    with path.open("r", encoding="utf-8-sig", errors="replace") as handle:
        for line_number, line in enumerate(handle, start=1):
            if not line.strip():
                counts["blank"] += 1
                continue
            if line.lstrip().startswith("#"):
                counts["blank"] += 1
                continue
            raw_seq = line[PHOTOMETRY_FIXED_WIDTH["seq"]].strip()
            if not raw_seq.isdigit():
                raise ValueError(
                    f"{path}:{line_number}: Seq is not an integer ({raw_seq!r})"
                )
            counts["rows"] += 1
            seq = int(raw_seq)
            if seq in qualifying:
                continue
            if rule.flag_policy != "none":
                raw_flag = line[PHOTOMETRY_FIXED_WIDTH["flag"]].strip()
                parsed_flag = int(raw_flag) if raw_flag.isdigit() else None
                if not flag_is_usable(rule.flag_policy, parsed_flag):
                    continue
            try:
                magnitude = float(line[PHOTOMETRY_FIXED_WIDTH["mag"]])
                magnitude_error = float(line[PHOTOMETRY_FIXED_WIDTH["e_mag"]])
            except ValueError:
                counts["unparsed"] += 1
                continue
            if magnitude_error <= 0.0:
                counts["nonpositive_error"] += 1
                continue
            if rule.signal_to_noise(magnitude, magnitude_error) >= sigma:
                qualifying.add(seq)

    if (
        counts["rows"]
        and counts["unparsed"] >= MIN_UNPARSED_TO_ABORT
        and counts["unparsed"] / counts["rows"] > MAX_UNPARSED_FRACTION
    ):
        raise ValueError(
            f"{path}: {counts['unparsed']} of {counts['rows']} rows have an "
            f"unparseable mag/e_mag ({counts['unparsed'] / counts['rows']:.1%}), "
            "which indicates the fixed-width offsets do not match this file"
        )
    return qualifying


def null_exclusion_sequences(table2: dict[int, dict[str, object]]) -> set[int]:
    """Sequences whose four nullable fields are all present (the current predicate)."""
    return {
        seq
        for seq, row in table2.items()
        if row["gmag"] is not None
        and row["rmag"] is not None
        and row["per_g"] is not None
        and row["per_r"] is not None
    }


def compare_sets(
    routes: dict[str, set[int]],
    reference: set[int],
    table2: dict[int, dict[str, object]],
) -> dict[str, object]:
    """Set-level and object-level comparison of every route against the reference."""
    report: dict[str, object] = {"reference_size": len(reference), "routes": {}}
    for label, produced in routes.items():
        only_produced = sorted(produced - reference)
        only_reference = sorted(reference - produced)
        report["routes"][label] = {
            "size": len(produced),
            "intersection": len(produced & reference),
            "produced_only": len(only_produced),
            "reference_only": len(only_reference),
            "exact_set_equality": produced == reference,
            # The complete ID lists, never truncated. A capped sample is fine for
            # a human reader but useless for traceability: reporting 200 of
            # 11,602 would leave 11,402 objects unaccounted for. These two arrays
            # are the authoritative record of the difference.
            "produced_only_ids": only_produced,
            "reference_only_ids": only_reference,
            # Object-level rows are what make a difference auditable rather than
            # merely counted. Names are included so the entry can be checked
            # against the published table without re-deriving the join. These are
            # a convenience sample; produced_only_ids/reference_only_ids above are
            # exhaustive.
            "produced_only_objects": [
                {
                    "seq": seq,
                    "name": table2[seq]["name"] if seq in table2 else None,
                    "gmag": table2[seq]["gmag"] if seq in table2 else None,
                    "rmag": table2[seq]["rmag"] if seq in table2 else None,
                    "per_g": table2[seq]["per_g"] if seq in table2 else None,
                    "per_r": table2[seq]["per_r"] if seq in table2 else None,
                }
                for seq in only_produced[:200]
            ],
            "reference_only_objects": [
                {
                    "seq": seq,
                    "name": table2[seq]["name"] if seq in table2 else None,
                }
                for seq in only_reference[:200]
            ],
            "produced_only_sample_truncated": max(0, len(only_produced) - 200),
            "reference_only_sample_truncated": max(0, len(only_reference) - 200),
        }
    return report


def build_report(
    *,
    table2_path: Path,
    table4_path: Path,
    ztf2g_path: Path,
    ztf2r_path: Path,
    output_dir: Path,
    rules: list[DetectionRule],
) -> dict[str, object]:
    output_dir.mkdir(parents=True, exist_ok=True)

    table2 = read_table2(table2_path)
    published_name_to_id, published_ids = read_table4(table4_path)
    published_names = set(published_name_to_id)

    # Membership is resolved by object name, which is the route that fails closed
    # on ambiguity. The published ID column is carried alongside as an
    # independent check, not as a substitute.
    name_to_seq = {str(row["name"]): seq for seq, row in table2.items()}
    unmapped = sorted(published_names - set(name_to_seq))
    if unmapped:
        raise ValueError(
            f"{len(unmapped)} published names are absent from table2; "
            f"examples={unmapped[:10]}"
        )
    reference_by_name = {name_to_seq[name] for name in published_names}

    inputs = {}
    for label, path in (
        ("table2", table2_path),
        ("table4", table4_path),
        ("ztf2g", ztf2g_path),
        ("ztf2r", ztf2r_path),
    ):
        inputs[label] = {
            "path": path.name,
            "bytes": path.stat().st_size,
            "sha256": sha256_file(path),
            "md5": md5_file(path),
        }

    routes: dict[str, set[int]] = {"null_exclusion": null_exclusion_sequences(table2)}

    detection_runs = []
    for rule in rules:
        g_stats: dict[str, int] = {}
        r_stats: dict[str, int] = {}
        g_ok = qualifying_sequences(ztf2g_path, rule, rule.g_sigma, g_stats)
        r_ok = qualifying_sequences(ztf2r_path, rule, rule.r_sigma, r_stats)
        produced = g_ok & r_ok
        label = f"documented_rule[{rule.snr_method},{rule.flag_policy}]"
        routes[label] = produced
        detection_runs.append(
            {
                "label": label,
                "rule": asdict(rule),
                "g_band_objects": len(g_ok),
                "r_band_objects": len(r_ok),
                "both_bands_objects": len(produced),
                # Per-band parse accounting. A non-zero 'unparsed' here is a
                # defect signal, not a data-quality remark.
                "g_band_rows": g_stats,
                "r_band_rows": r_stats,
            }
        )

    comparison = compare_sets(routes, reference_by_name, table2)
    comparison["detection_runs"] = detection_runs

    # Whether the documented ID column selects the same objects as the name join.
    comparison["published_id_vs_name_join"] = (
        "AGREE" if published_ids == reference_by_name else "DISAGREE"
    )
    comparison["published_id_count"] = len(published_ids)
    comparison["published_name_join_count"] = len(reference_by_name)

    manifest = {
        "schema": "cpvs-documented-rule-reconstruction/1.0",
        "status": "UNRESOLVED",
        "validated_on_real_data": False,
        "note": (
            "The documented detection criterion is evaluated here for comparison "
            "with the null-exclusion predicate and the published membership. No "
            "route is declared correct, and a count match is not treated as "
            "evidence that a rule is the publisher's rule."
        ),
        "inputs": inputs,
        "table2_rows": len(table2),
        "table4_rows": len(published_ids),
        "comparison": comparison,
    }
    (output_dir / "cpvs_documented_rule_report.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return manifest


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--table2", type=Path, required=True)
    parser.add_argument("--table4", type=Path, required=True)
    parser.add_argument("--ztf2g", type=Path, required=True)
    parser.add_argument("--ztf2r", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument(
        "--manifest",
        type=Path,
        default=None,
        help=(
            "acquisition manifest declaring the publisher md5 of each input; "
            "when given, a download that does not match aborts the run"
        ),
    )
    args = parser.parse_args(argv)

    # Both SNR definitions and both flag policies are evaluated, because neither
    # is settled by the primary source and the difference is informative.
    rules = [
        DetectionRule(snr_method="inverse_error", flag_policy="none"),
        DetectionRule(snr_method="inverse_error", flag_policy="any_nonzero"),
        DetectionRule(snr_method="magnitude_over_error", flag_policy="none"),
    ]

    try:
        manifest = build_report(
            table2_path=args.table2,
            table4_path=args.table4,
            ztf2g_path=args.ztf2g,
            ztf2r_path=args.ztf2r,
            output_dir=args.output_dir,
            rules=rules,
        )
    except (ValueError, OSError) as error:
        sys.stderr.write(f"reconstruct_cpvs_from_photometry: {error}\n")
        return 1

    if args.manifest is not None:
        try:
            checksums = verify_publisher_checksums(
                {
                    "table2": args.table2,
                    "table4": args.table4,
                    "ztf2g": args.ztf2g,
                    "ztf2r": args.ztf2r,
                },
                args.manifest,
            )
        except (ValueError, OSError) as error:
            sys.stderr.write(f"reconstruct_cpvs_from_photometry: {error}\n")
            return 1
        print(json.dumps(checksums, indent=2))

    print(json.dumps(manifest["comparison"]["detection_runs"], indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
