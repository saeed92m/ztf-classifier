"""CLI for building a CPVS candidate-only discrepancy report."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from ztf_classifier.validation.cpvs_discrepancy_report import (
    build_cpvs_discrepancy_report,
)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--parent-metadata", type=Path, required=True)
    parser.add_argument("--candidate-ids", type=Path, required=True)
    parser.add_argument("--published-ids", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--source-revision", required=True, help="revision that produced the input artifacts")
    args = parser.parse_args()
    summary = build_cpvs_discrepancy_report(
        parent_metadata=args.parent_metadata,
        candidate_ids=args.candidate_ids,
        published_ids=args.published_ids,
        output_dir=args.output_dir,
        source_revision=args.source_revision,
    )
    print(json.dumps(summary["counts"], indent=2, sort_keys=True))
    print(f"Report written to {args.output_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
