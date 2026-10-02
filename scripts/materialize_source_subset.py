"""Materialize a normalized, checksummed source subset from an acquired response."""

from __future__ import annotations

import argparse
import json
from datetime import UTC, datetime
from pathlib import Path

import pandas as pd

from ztf_classifier.data.source_subset import (
    SOURCE_SUBSET_NORMALIZATION_CONTRACT,
    normalize_source_subset,
)
from ztf_classifier.reproducibility.source_manifest import (
    SourceArtifact,
    SourceSubsetManifest,
)
from ztf_classifier.dataset.artifact import sha256_file


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input-tsv", type=Path, required=True)
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--source", required=True)
    parser.add_argument("--source-version", required=True)
    parser.add_argument("--retrieval-utc", default=None)
    parser.add_argument("--temporal-cutoff-mjd", type=float, default=None)
    args = parser.parse_args()

    frame = pd.read_csv(args.input_tsv, sep="\t")
    normalized = normalize_source_subset(frame)

    root = args.output_root
    root.mkdir(parents=True, exist_ok=True)
    subset_path = root / "subset.tsv"
    normalized.to_csv(subset_path, sep="\t", index=False, lineterminator="\n")

    retrieval_utc = args.retrieval_utc or datetime.now(UTC).isoformat()
    manifest = SourceSubsetManifest(
        source=args.source,
        source_version=args.source_version,
        retrieval_utc=retrieval_utc,
        selection={
            "method": "materialized_source_response",
            "input": str(args.input_tsv),
            "normalization_contract": SOURCE_SUBSET_NORMALIZATION_CONTRACT,
            "row_count": len(normalized),
        },
        object_ids=tuple(normalized["oid"].astype(str)),
        artifacts=(
            SourceArtifact(
                path=subset_path.name,
                sha256=sha256_file(subset_path),
            ),
        ),
        normalization_contract=SOURCE_SUBSET_NORMALIZATION_CONTRACT,
        temporal_cutoff_mjd=args.temporal_cutoff_mjd,
    )
    manifest_path = manifest.write(root / "source_subset_manifest.json")
    manifest.verify_artifacts(root)

    qc = {
        "input_rows": len(frame),
        "output_rows": len(normalized),
        "dropped_rows": len(frame) - len(normalized),
        "required_columns": list(normalized.columns[:4]),
        "object_id_sorted": normalized["oid"].tolist()
        == sorted(normalized["oid"].tolist()),
    }
    (root / "qc_report.json").write_text(
        json.dumps(qc, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(f"materialized={subset_path}")
    print(f"manifest={manifest_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
