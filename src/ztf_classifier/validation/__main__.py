"""Command-line entry point for scientific benchmark validation."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys

from ztf_classifier.validation.registry import BenchmarkRegistry
from ztf_classifier.validation.runner import run_table_benchmark


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python -m ztf_classifier.validation")
    parser.add_argument(
        "--registry-dir",
        type=Path,
        default=Path("configs/benchmarks"),
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    list_command = subparsers.add_parser("list", help="List registered benchmarks")
    list_command.set_defaults(command_name="list")

    validate = subparsers.add_parser("validate", help="Run a tabular benchmark")
    validate.add_argument("--benchmark-id", required=True)
    validate.add_argument("--input", required=True, type=Path)
    validate.add_argument("--output-dir", required=True, type=Path)

    args = parser.parse_args(argv)
    registry = BenchmarkRegistry(args.registry_dir)

    try:
        if args.command == "list":
            for benchmark_id in registry.validate_all():
                print(benchmark_id)
            return 0

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
