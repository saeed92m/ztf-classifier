"""Command-line entry point for scientific benchmark validation."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from ztf_classifier.validation.acquisition import AcquisitionRequest, acquire_source
from ztf_classifier.validation.gate import write_release_gate_report
from ztf_classifier.validation.registry import BenchmarkRegistry
from ztf_classifier.validation.report import write_scientific_validation_report
from ztf_classifier.validation.runner import run_table_benchmark


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python -m ztf_classifier.validation")
    parser.add_argument("--registry-dir", type=Path, default=Path("configs/benchmarks"))
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("list", help="List registered benchmarks")

    validate = subparsers.add_parser("validate", help="Run a tabular benchmark")
    validate.add_argument("--benchmark-id", required=True)
    validate.add_argument("--input", required=True, type=Path)
    validate.add_argument("--output-dir", required=True, type=Path)

    acquire = subparsers.add_parser("acquire", help="Acquire one source-backed scientific evidence artifact")
    acquire.add_argument("--benchmark-id", required=True)
    acquire.add_argument("--source-id", required=True)
    acquire.add_argument("--url", action="append", required=True, dest="urls")
    acquire.add_argument("--output", required=True, type=Path)
    acquire.add_argument("--code-version", default="working-tree")
    acquire.add_argument("--expected-sha256")
    acquire.add_argument("--query-manifest", type=Path)

    gate = subparsers.add_parser("gate", help="Evaluate the fail-closed product release gate")
    gate.add_argument("--evidence-dir", type=Path, default=Path("reports/scientific_validation"))
    gate.add_argument(
        "--output",
        type=Path,
        default=Path("reports/scientific_validation/release_gate.json"),
    )

    report = subparsers.add_parser("report", help="Render a scientific validation report")
    report.add_argument("--gate", type=Path, required=True)
    report.add_argument("--output", type=Path, required=True)

    args = parser.parse_args(argv)
    registry = BenchmarkRegistry(args.registry_dir)

    try:
        if args.command == "list":
            for benchmark_id in registry.validate_all():
                print(benchmark_id)
            return 0

        if args.command == "report":
            output = write_scientific_validation_report(args.gate, args.output)
            print(f"report={output}")
            return 0

        if args.command == "acquire":
            query_manifest = None
            if args.query_manifest:
                query_manifest = __import__("json").loads(args.query_manifest.read_text(encoding="utf-8"))
            result = acquire_source(
                AcquisitionRequest(
                    benchmark_id=args.benchmark_id,
                    source_id=args.source_id,
                    destination=args.output,
                    urls=tuple(args.urls),
                    expected_sha256=args.expected_sha256,
                    query_manifest=query_manifest,
                ),
                code_version=args.code_version,
            )
            report = args.output.with_name(args.output.name + ".acquisition.json")
            report.write_text(
                __import__("json").dumps(result.to_dict(), indent=2, sort_keys=True) + "\\n",
                encoding="utf-8",
            )
            print(f"acquisition={result.status}")
            print(f"report={report}")
            return 0 if result.status == "ACQUIRED" else 2

        if args.command == "gate":
            result = write_release_gate_report(
                output_path=args.output,
                registry_dir=args.registry_dir,
                evidence_dir=args.evidence_dir,
            )
            print(f"scientific_gate={result['status']}")
            print(f"report={args.output}")
            return 0 if result["status"] == "PASS" else 2

        manifest = registry.load(args.benchmark_id)
        result = run_table_benchmark(
            manifest=manifest,
            input_path=args.input,
            output_dir=args.output_dir,
        )
        print(f"benchmark={result.benchmark_id}")
        print(f"status={result.status}")
        print(f"report={result.output_path}")
        return 0 if result.passed else 2
    except (FileNotFoundError, OSError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
