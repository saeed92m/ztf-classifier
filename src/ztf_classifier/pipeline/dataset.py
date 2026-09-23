"""Production orchestration for canonical dataset construction."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from ztf_classifier.dataset.artifact import (
    DatasetArtifact,
    DatasetArtifactWriter,
)
from ztf_classifier.dataset.builder import ObjectManifestBuilder
from ztf_classifier.dataset.config import DatasetConfig
from ztf_classifier.dataset.features import (
    FeatureDataset,
    FeatureDatasetBuilder,
)
from ztf_classifier.dataset.selection import ObjectSelectionPolicy
from ztf_classifier.dataset.validation import (
    DatasetArtifactValidationResult,
    DatasetArtifactValidator,
)
from ztf_classifier.io.detection_acquisition import (
    DetectionAcquisitionBackend,
)
from ztf_classifier.io.object_acquisition import (
    ObjectAcquisitionBackend,
)
from ztf_classifier.reproducibility.manifest import (
    ReproducibilityManifest,
    ReproducibilityManifestBuilder,
)
from ztf_classifier.reproducibility.validation import (
    ReproducibilityValidationResult,
    ReproducibilityValidator,
)


@dataclass(frozen=True)
class DatasetPipelineResult:
    """Complete result of one production dataset-construction run."""

    config: DatasetConfig
    object_manifest: Any
    dataset: FeatureDataset
    artifact: DatasetArtifact
    artifact_validation: DatasetArtifactValidationResult
    reproducibility_manifest: ReproducibilityManifest
    reproducibility_validation: ReproducibilityValidationResult


class DatasetPipeline:
    """Orchestrate canonical dataset construction and validation."""

    def __init__(
        self,
        *,
        config: DatasetConfig,
        object_acquisition_backend: ObjectAcquisitionBackend,
        detection_acquisition_backend: DetectionAcquisitionBackend,
        project_root: Path,
        output_dir: Path,
        feature_schema_path: Path,
    ) -> None:
        self._config = config
        self._object_acquisition_backend = object_acquisition_backend
        self._detection_acquisition_backend = detection_acquisition_backend
        self._project_root = project_root.resolve()
        self._output_dir = output_dir.resolve()
        self._feature_schema_path = feature_schema_path.resolve()

    def run(
        self,
        *,
        command: str | None = None,
        purpose: str = "production_dataset_build",
        configuration: dict[str, Any] | None = None,
    ) -> DatasetPipelineResult:
        """Build, persist, and validate one canonical dataset."""

        object_manifest = self._build_object_manifest()

        dataset = FeatureDatasetBuilder(
            manifest=object_manifest,
            acquisition_backend=self._detection_acquisition_backend,
            feature_schema_version="v0.2",
        ).build()

        input_manifest_sha256 = self._write_object_manifest(
            object_manifest
        )

        artifact = DatasetArtifactWriter().write(
            dataset=dataset,
            output_dir=self._output_dir,
            input_manifest_sha256=input_manifest_sha256,
        )

        artifact_validation = DatasetArtifactValidator().validate(
            artifact_path=artifact.artifact_path,
            manifest_path=artifact.manifest_path,
        )

        reproducibility_manifest_path = (
            self._output_dir / "reproducibility_manifest.json"
        )

        repro_configuration = {
            "dataset": self._config.selection_policy(),
            "source": self._config.source,
            "classifier": self._config.classifier,
            "survey": self._config.survey,
        }

        if configuration:
            repro_configuration.update(configuration)

        reproducibility_manifest = ReproducibilityManifestBuilder().build(
            project_root=self._project_root,
            dataset_path=artifact.artifact_path,
            feature_schema_path=self._feature_schema_path,
            output_path=reproducibility_manifest_path,
            purpose=purpose,
            command=command,
            configuration=repro_configuration,
            object_count=dataset.object_count,
            feature_count=dataset.feature_count,
            dataset_version=dataset.dataset_version,
            feature_schema_version=dataset.feature_schema_version,
        )

        reproducibility_manifest.write()

        reproducibility_validation = ReproducibilityValidator().validate(
            manifest_path=reproducibility_manifest_path,
            project_root=self._project_root,
            verify_files=True,
        )

        return DatasetPipelineResult(
            config=self._config,
            object_manifest=object_manifest,
            dataset=dataset,
            artifact=artifact,
            artifact_validation=artifact_validation,
            reproducibility_manifest=reproducibility_manifest,
            reproducibility_validation=reproducibility_validation,
        )

    def _build_object_manifest(self) -> Any:
        """Acquire objects using the configured selection policy."""

        objects = ObjectSelectionPolicy(
            self._config
        ).acquire_all(
            backend=self._object_acquisition_backend,
        )

        if objects.empty:
            raise ValueError("Object acquisition returned no object records.")

        return ObjectManifestBuilder(self._config).build(objects)

    def _write_object_manifest(self, manifest: Any) -> str:
        """Persist the canonical object manifest and return its SHA-256."""

        path = self._output_dir / "object_manifest.parquet"
        self._output_dir.mkdir(parents=True, exist_ok=True)

        data = (
            manifest.objects
            .sort_values("oid")
            .reset_index(drop=True)
        )

        data.to_parquet(path, index=False)

        from ztf_classifier.dataset.artifact import sha256_file

        return sha256_file(path)
