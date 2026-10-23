"""Diagnostic-only raw-epoch provenance for CPVS membership residuals."""
from __future__ import annotations
import argparse, csv, hashlib, json, math
from pathlib import Path
from ztf_classifier.validation.derivation import _iter_rows, _open_text, _path_member_matches_header

FACTOR = 1.0857362047581296
SPECS = {"g": ("e_gmag", "gmag", "g_flag", 2.5), "r": ("e_rmag", "rmag", "r_flag", 3.0)}
SUFFIXES = {".csv", ".txt", ".dat", ".json", ".gz", ""}

def sha256_file(path):
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()

def files(root, required):
    if not root.is_dir(): return [root]
    return sorted(p for p in root.rglob("*") if p.is_file()
        and p.suffix.lower() in SUFFIXES and _path_member_matches_header(p, required))

def read_published_ztf_names(path: Path) -> list[str]:
    """Extract ZTF object names from VizieR TSV, whitespace, or fixed-width rows."""
    names: list[str] = []
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        fixed_name = line[:22].strip()
        if fixed_name.upper().startswith("ZTFJ"):
            names.append(fixed_name.upper())
            continue
        for token in stripped.replace("\\t", " ").split():
            if token.upper().startswith("ZTFJ"):
                names.append(token.upper())
                break
    if not names:
        raise ValueError(f"could not parse any published ZTF names from {path}")
    return names


def read_vizier(path: Path, parent_catalog: dict[int, dict[str, object]]) -> set[int]:
    """Map Table 4 ZTF names to parent Table2's explicit SourceIDs.

    Table 4's numeric ID is internal to that catalog; it must never be
    compared directly with the SourceID used by the light-curve archives.
    """
    names = read_published_ztf_names(path)
    if len(names) != len(set(names)):
        raise ValueError("published Table 4 contains duplicate ZTF object names")
    parent_mapping: dict[str, int] = {}
    for source_id, row in parent_catalog.items():
        name = str(row["catalog_object_name"]).upper()
        if name in parent_mapping:
            raise ValueError(f"duplicate ZTF name in parent catalog: {name}")
        parent_mapping[name] = int(source_id)
    unmapped = sorted(set(names) - set(parent_mapping))
    if unmapped:
        raise ValueError(
            f"{len(unmapped)} published Table 4 ZTF names do not map to "
            f"the parent Table2 catalog; sample={unmapped[:10]!r}"
        )
    return {parent_mapping[name] for name in names}

def field(row, name):
    normalized = {key.strip().lower(): value for key, value in row.items()}
    return normalized.get(name.lower(), "")

def read_parent_catalog(path):
    owner, raw = _open_text(path)
    catalog = {}
    row_ordinal = 0
    try:
        for encoded in raw:
            line = encoded.decode("utf-8", errors="replace").strip()
            if not line.startswith("ZTF"):
                continue
            fields = line.split()
            if len(fields) < 12:
                continue
            try:
                oid = int(fields[1])
                values = {
                    "catalog_row_ordinal": row_ordinal + 1,
                    "catalog_object_name": fields[0],
                    "Per": float(fields[4]),
                    "gmag": float(fields[8]),
                    "rmag": float(fields[9]),
                    "Per_g": float(fields[10]),
                    "Per_r": float(fields[11]),
                }
            except (TypeError, ValueError):
                continue
            row_ordinal += 1
            if oid in catalog:
                raise ValueError(f"Duplicate Table2 SourceID: {oid}")
            catalog[oid] = values
    finally:
        raw.close()
        if owner is not None:
            owner.close()
    if row_ordinal != 781602:
        raise ValueError(f"Expected 781602 Table2 catalog rows, got {row_ordinal}")
    return catalog

def metrics(row, band):
    err_key, mag_key, flag_key, threshold = SPECS[band]
    try: oid = int(field(row, "SourceID").strip())
    except (TypeError, ValueError): return None, None, None, False
    try: mag, err = float(field(row, mag_key)), float(field(row, err_key))
    except (TypeError, ValueError): return oid, None, None, False
    valid = math.isfinite(mag) and mag != 0 and math.isfinite(err) and err > 0
    snr = FACTOR / err if valid else None
    return oid, mag, snr, bool(valid and snr >= threshold)

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--g", type=Path, required=True); p.add_argument("--r", type=Path, required=True)
    p.add_argument("--parent", type=Path, required=True)
    p.add_argument("--g-archive", type=Path, required=True)
    p.add_argument("--r-archive", type=Path, required=True)
    p.add_argument("--published", type=Path, required=True); p.add_argument("--output", type=Path, required=True)
    p.add_argument("--code-version", default="unknown")
    a = p.parse_args()
    parent_catalog = read_parent_catalog(a.parent)
    published = read_vizier(a.published, parent_catalog)
    paths, qualified, band_counts = {}, {"g": set(), "r": set()}, {}
    for band, root in (("g", a.g), ("r", a.r)):
        ek, mk, fk, threshold = SPECS[band]; req = ("SourceID", ek, mk)
        paths[band] = files(root, req)
        if not paths[band]: raise RuntimeError(f"No parseable {band}-band inputs at {root}")
        rows = valid = qrows = 0
        for path in paths[band]:
            for row in _iter_rows(path, required_columns=req):
                rows += 1; oid, mag, snr, q = metrics(row, band)
                if oid is None: continue
                if mag is not None: valid += 1
                if q: qrows += 1; qualified[band].add(oid)
        band_counts[band] = {"files": len(paths[band]), "parsed_rows": rows,
            "valid_measurement_rows": valid, "qualifying_epoch_rows": qrows,
            "objects_with_qualifying_epoch": len(qualified[band])}
    candidate = qualified["g"] & qualified["r"]
    cand_only, pub_only = candidate - published, published - candidate
    targets = cand_only | pub_only
    epochs = {oid: {"g": [], "r": []} for oid in targets}
    for band in ("g", "r"):
        ek, mk, fk, threshold = SPECS[band]; req = ("SourceID", ek, mk)
        for path in paths[band]:
            try: rel = str(path.relative_to(a.g if band == "g" else a.r))
            except ValueError: rel = path.name
            for ordinal, row in enumerate(_iter_rows(path, required_columns=req), 1):
                oid, mag, snr, q = metrics(row, band)
                if oid not in targets: continue
                epochs[oid][band].append({"source_file": rel, "parsed_data_row_ordinal": ordinal,
                    "magnitude": mag, "magnitude_error": field(row, ek), "snr": snr,
                    "snr_threshold": threshold, "qualifies": q, "flag": field(row, fk)})
    a.output.parent.mkdir(parents=True, exist_ok=True)
    tsv = a.output.with_suffix(".tsv")
    cols = ["SourceID","published_member","snr_candidate","membership_relation","parent_catalog_present",
        "parent_catalog_row_ordinal","parent_catalog_object_name","parent_Per","parent_gmag","parent_rmag","parent_Per_g","parent_Per_r",
        "g_epoch_count","g_qualifying_epoch_count","g_max_snr","g_epochs_json",
        "r_epoch_count","r_qualifying_epoch_count","r_max_snr","r_epochs_json"]
    with tsv.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=cols, delimiter="\t", lineterminator="\n"); w.writeheader()
        for oid in sorted(targets):
            rec = {"SourceID": oid, "published_member": oid in published, "snr_candidate": oid in candidate,
                "membership_relation": "candidate_only" if oid in cand_only else "published_only"}
            parent_row = parent_catalog.get(oid)
            rec["parent_catalog_present"] = parent_row is not None
            if parent_row is not None:
                for key, value in parent_row.items():
                    rec[f"parent_{key}"] = value
            for band in ("g", "r"):
                es = epochs[oid][band]
                rec[f"{band}_epoch_count"] = len(es)
                rec[f"{band}_qualifying_epoch_count"] = sum(x["qualifies"] for x in es)
                rec[f"{band}_max_snr"] = max((x["snr"] for x in es if x["snr"] is not None), default="")
                rec[f"{band}_epochs_json"] = json.dumps(es, separators=(",", ":"), sort_keys=True)
            w.writerow(rec)
    h = hashlib.sha256(tsv.read_bytes()).hexdigest()
    report = {"status":"DIAGNOSTIC_ONLY_NOT_A_MEMBERSHIP_RULE","code_version":a.code_version,
        "source_urls":{"g":"https://zenodo.org/records/3886372/files/ztf2g.zip?download=1",
          "r":"https://zenodo.org/records/3886372/files/ztf2r.zip?download=1",
          "published":"https://vizier.cds.unistra.fr/viz-bin/asu-tsv?-source=J/ApJ/932/118/table4&-out=ZTF,ID&-out.max=1000000"},
        "parent_table2":{"path":str(a.parent),"row_count":len(parent_catalog),"sha256":sha256_file(a.parent),"source_id_mapping":"explicit SourceID column in Table2 catalog row"},
        "source_archive_sha256":{"g":sha256_file(a.g_archive),"r":sha256_file(a.r_archive)},
        "verified_archive_md5":{"g":"850fcef561dd7407fbe8e19e99100d7a","r":"daa7bc45c67579253eebe6b1c09dfbd9"},
        "snr_formula":"1.0857362047581296 / magnitude_error","thresholds":{"g":2.5,"r":3.0},
        "counts":{"published":len(published),"snr_candidates_both_bands":len(candidate),
          "candidate_only_relative_to_published":len(cand_only),"published_only_relative_to_snr_rule":len(pub_only),
          "audited_discrepant_objects":len(targets)},
        "band_scan":band_counts,
        "row_reference_semantics":"relative source file plus parsed data-row ordinal; not publisher-issued row ID",
        "output_tsv":tsv.name,"output_tsv_sha256":h,
        "interpretation":"Table 4 is a reference comparison, not independent astrophysical ground truth. This audit does not assert SNR alone is the complete published membership rule."}
    a.output.write_text(json.dumps(report, indent=2, sort_keys=True)+"\n", encoding="utf-8")
    print(json.dumps(report["counts"], indent=2, sort_keys=True))
    print(f"TSV SHA256: {h}")
if __name__ == "__main__": raise SystemExit(main())
