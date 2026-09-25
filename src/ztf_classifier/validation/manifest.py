"""Versioned scientific benchmark manifest contracts."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

REQUIRED_FIELDS = (
    "benchmark_id", "dataset_name", "source", "version", "retrieval_date",
    "object_id_column", "label_column", "label_taxonomy", "class_mapping",
    "split_definition", "leakage_exclusions", "preprocessing_contract",
    "input_contract", "ground_truth_provenance", "reference_system_provenance",
    "benchmark_code_version",
)


@dataclass(frozen=True)
class BenchmarkManifest:
    """Immutable manifest describing one reproducible validation benchmark."""

    benchmark_id: str
    dataset_name: str
    source: str
    version: str
    retrieval_date: str
    object_id_column: str
    label_column: str
    label_taxonomy: str
    class_mapping: dict[str, str]
    split_definition: dict[str, Any]
    leakage_exclusions: list[str]
    preprocessing_contract: dict[str, Any]
    input_contract: dict[str, Any]
    ground_truth_provenance: dict[str, Any]
    reference_system_provenance: dict[str, Any]
    benchmark_code_version: str
    source_url: str | None = None
    doi: str | None = None
    license: str | None = None
    file_object_ids: list[str] | None = None
    hashes: dict[str, str] | None = None
    probability_columns: list[str] | None = None
    ood_label_column: str | None = None
    ood_score_column: str | None = None
    accepted_column: str | None = None
    required_leakage_checks: tuple[str, ...] = (
        "object_overlap", "duplicate_objects", "target_leakage",
        "future_data_leakage", "benchmark_trained_artifacts",
        "preprocessing_consistency",
    )

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> BenchmarkManifest:
        missing = [key for key in REQUIRED_FIELDS if key not in payload]
        if missing:
            raise ValueError("Benchmark manifest missing required fields: " + ", ".join(missing))
        for key in ("benchmark_id", "dataset_name", "source", "version"):
            if not isinstance(payload[key], str) or not payload[key].strip():
                raise ValueError(f"Benchmark manifest field must be non-empty: {key}")
        if not isinstance(payload["class_mapping"], dict) or not payload["class_mapping"]:
            raise ValueError("class_mapping must be a non-empty object")
        if not isinstance(payload["leakage_exclusions"], list):
            raise TypeError("leakage_exclusions must be a list")
        required = payload.get("required_leakage_checks", list(cls.required_leakage_checks))
        if not isinstance(required, list) or not required:
            raise ValueError("required_leakage_checks must be a non-empty list")
        return cls(
            benchmark_id=payload["benchmark_id"], dataset_name=payload["dataset_name"],
            source=payload["source"], version=payload["version"],
            retrieval_date=payload["retrieval_date"], object_id_column=payload["object_id_column"],
            label_column=payload["label_column"], label_taxonomy=payload["label_taxonomy"],
            class_mapping=dict(payload["class_mapping"]), split_definition=dict(payload["split_definition"]),
            leakage_exclusions=list(payload["leakage_exclusions"]),
            preprocessing_contract=dict(payload["preprocessing_contract"]),
            input_contract=dict(payload["input_contract"]),
            ground_truth_provenance=dict(payload["ground_truth_provenance"]),
            reference_system_provenance=dict(payload["reference_system_provenance"]),
            benchmark_code_version=payload["benchmark_code_version"],
            source_url=payload.get("source_url"), doi=payload.get("doi"), license=payload.get("license"),
            file_object_ids=list(payload["file_object_ids"]) if payload.get("file_object_ids") is not None else None,
            hashes=dict(payload["hashes"]) if payload.get("hashes") is not None else None,
            probability_columns=list(payload["probability_columns"]) if payload.get("probability_columns") is not None else None,
            ood_label_column=payload.get("ood_label_column"), ood_score_column=payload.get("ood_score_column"),
            accepted_column=payload.get("accepted_column"),
            required_leakage_checks=tuple(required),
        )

    @classmethod
    def from_json(cls, path: str | Path) -> BenchmarkManifest:
        return cls.from_dict(json.loads(Path(path).read_text(encoding="utf-8")))

    def to_dict(self) -> dict[str, Any]:
        return {
            "benchmark_id": self.benchmark_id, "dataset_name": self.dataset_name,
            "source": self.source, "version": self.version, "retrieval_date": self.retrieval_date,
            "source_url": self.source_url, "doi": self.doi, "license": self.license,
            "object_id_column": self.object_id_column, "label_column": self.label_column,
            "label_taxonomy": self.label_taxonomy, "class_mapping": self.class_mapping,
            "split_definition": self.split_definition, "leakage_exclusions": self.leakage_exclusions,
            "preprocessing_contract": self.preprocessing_contract,
            "input_contract": self.input_contract, "ground_truth_provenance": self.ground_truth_provenance,
            "reference_system_provenance": self.reference_system_provenance,
            "benchmark_code_version": self.benchmark_code_version, "file_object_ids": self.file_object_ids,
            "hashes": self.hashes, "probability_columns": self.probability_columns,
            "ood_label_column": self.ood_label_column, "ood_score_column": self.ood_score_column,
            "accepted_column": self.accepted_column, "required_leakage_checks": list(self.required_leakage_checks),
        }
