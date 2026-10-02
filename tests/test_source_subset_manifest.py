from pathlib import Path

import pytest

from ztf_classifier.dataset.artifact import sha256_file
from ztf_classifier.reproducibility.source_manifest import (
    SourceArtifact,
    SourceSubsetManifest,
)


def _manifest(tmp_path: Path, artifact_path: Path) -> SourceSubsetManifest:
    return SourceSubsetManifest(
        source="ztf_dr24",
        source_version="dr24",
        retrieval_utc="2026-10-01T12:00:00+00:00",
        selection={"object_id_column": "oid", "limit": 3},
        object_ids=("ZTF0001", "ZTF0002", "ZTF0003"),
        artifacts=(SourceArtifact("subset.txt", sha256_file(artifact_path)),),
        normalization_contract="ztf.observation.v1",
        temporal_cutoff_mjd=59447.224132,
    )


def test_source_subset_manifest_round_trips_and_verifies(tmp_path: Path) -> None:
    artifact = tmp_path / "subset.txt"
    artifact.write_text("ZTF0001\nZTF0002\nZTF0003\n", encoding="utf-8")

    manifest = _manifest(tmp_path, artifact)
    path = manifest.write(tmp_path / "manifest.json")

    restored = SourceSubsetManifest.from_dict(__import__("json").loads(path.read_text()))
    restored.verify_artifacts(tmp_path)
    assert restored.to_dict() == manifest.to_dict()


def test_source_subset_manifest_fails_closed_on_artifact_drift(tmp_path: Path) -> None:
    artifact = tmp_path / "subset.txt"
    artifact.write_text("original\n", encoding="utf-8")
    manifest = _manifest(tmp_path, artifact)
    artifact.write_text("changed\n", encoding="utf-8")

    with pytest.raises(ValueError, match="checksum mismatch"):
        manifest.verify_artifacts(tmp_path)


def test_source_subset_manifest_rejects_unsorted_or_duplicate_ids(tmp_path: Path) -> None:
    artifact = tmp_path / "subset.txt"
    artifact.write_text("x\n", encoding="utf-8")
    digest = sha256_file(artifact)

    with pytest.raises(ValueError, match="deterministically sorted"):
        SourceSubsetManifest(
            source="ztf_dr24",
            source_version="dr24",
            retrieval_utc="2026-10-01T12:00:00+00:00",
            selection={"limit": 2},
            object_ids=("ZTF0002", "ZTF0001"),
            artifacts=(SourceArtifact("subset.txt", digest),),
            normalization_contract="ztf.observation.v1",
        )

    with pytest.raises(ValueError, match="unique"):
        SourceSubsetManifest(
            source="ztf_dr24",
            source_version="dr24",
            retrieval_utc="2026-10-01T12:00:00+00:00",
            selection={"limit": 2},
            object_ids=("ZTF0001", "ZTF0001"),
            artifacts=(SourceArtifact("subset.txt", digest),),
            normalization_contract="ztf.observation.v1",
        )
