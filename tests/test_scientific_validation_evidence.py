import json

import pytest

from ztf_classifier.validation.evidence import (
    EvidenceArtifact,
    EvidenceManifest,
    write_evidence_manifest,
)


def test_evidence_artifact_hashes_are_reproducible(tmp_path):
    artifact = tmp_path / "snapshot.bin"
    artifact.write_bytes(b"immutable scientific evidence")
    item = EvidenceArtifact.from_path(artifact, "source_snapshot")
    assert len(item.sha256) == 64
    assert item.size_bytes == artifact.stat().st_size

def test_manifest_round_trip_and_verify(tmp_path):
    artifact = tmp_path / "snapshot.bin"
    artifact.write_bytes(b"snapshot")
    item = EvidenceArtifact.from_path(artifact, "source_snapshot")
    path = tmp_path / "evidence.json"
    manifest = write_evidence_manifest(path, benchmark_id="star_embed_ztf_40k", source_id="star_embed_ztf_40k", acquisition_timestamp="2026-09-25T20:00:00Z", code_version="test", artifacts=[item])
    loaded = EvidenceManifest.from_dict(json.loads(path.read_text()))
    assert loaded.verify(tmp_path) == []
    assert manifest.to_dict() == loaded.to_dict()

def test_manifest_round_trip_preserves_integer_row_count(tmp_path):
    artifact = tmp_path / "snapshot.bin"
    artifact.write_bytes(b"snapshot")
    item = EvidenceArtifact.from_path(artifact, "source_snapshot")
    path = tmp_path / "evidence.json"
    manifest = write_evidence_manifest(
        path,
        benchmark_id="ztf_periodic_781k",
        source_id="ztf_periodic_781k",
        acquisition_timestamp="2026-09-26T20:00:00Z",
        code_version="test",
        artifacts=[item],
        row_count=781602,
    )
    payload = json.loads(path.read_text())
    assert payload["row_count"] == 781602
    assert isinstance(payload["row_count"], int)
    loaded = EvidenceManifest.from_dict(payload)
    assert loaded.row_count == 781602
    assert manifest.to_dict() == loaded.to_dict()


def test_manifest_rejects_non_integer_row_count():
    with pytest.raises(ValueError, match="row_count"):
        EvidenceManifest.from_dict({
            "benchmark_id": "star_embed_ztf_40k",
            "source_id": "star_embed_ztf_40k",
            "source_version": "ICML-2026 dataset release",
            "acquisition_timestamp": "2026-09-25T20:00:00Z",
            "code_version": "test",
            "artifacts": [{
                "path": "snapshot.bin",
                "sha256": "0" * 64,
                "size_bytes": 1,
                "role": "source_snapshot",
            }],
            "row_count": "781602",
        })


def test_manifest_detects_mutation(tmp_path):
    artifact = tmp_path / "snapshot.bin"
    artifact.write_bytes(b"snapshot")
    item = EvidenceArtifact.from_path(artifact, "source_snapshot")
    manifest = EvidenceManifest("star_embed_ztf_40k","star_embed_ztf_40k","ICML-2026 dataset release","2026-09-25T20:00:00Z","test",(item,))
    artifact.write_bytes(b"mutated")
    assert any("hash mismatch" in error for error in manifest.verify(tmp_path))

def test_manifest_rejects_source_version_drift():
    with pytest.raises(ValueError, match="source version mismatch"):
        EvidenceManifest.from_dict({"benchmark_id":"star_embed_ztf_40k","source_id":"star_embed_ztf_40k","source_version":"mutable-live-version","acquisition_timestamp":"2026-09-25T20:00:00Z","code_version":"test","artifacts":[{"path":"snapshot.bin","sha256":"0"*64,"size_bytes":1,"role":"source_snapshot"}]})

def test_manifest_requires_immutable_evidence():
    with pytest.raises(ValueError, match="immutable"):
        EvidenceManifest.from_dict({"benchmark_id":"star_embed_ztf_40k","source_id":"star_embed_ztf_40k","source_version":"2026-05 dataset snapshot","acquisition_timestamp":"2026-09-25T20:00:00Z","code_version":"test","immutable":False,"artifacts":[{"path":"snapshot.bin","sha256":"0"*64,"size_bytes":1,"role":"source_snapshot"}]})
