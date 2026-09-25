from pathlib import Path

import pytest

from ztf_classifier.validation.acquisition import AcquisitionError, request_from_benchmark


def test_request_from_benchmark_binds_canonical_source_and_version():
    request = request_from_benchmark(
        "configs/benchmarks",
        "ztf_periodic_781k",
        destination="/tmp/cpvs.parquet",
        urls=("https://example.test/cpvs",),
    )
    assert request.benchmark_id == "ztf_periodic_781k"
    assert request.source_id == "ztf_periodic_781k"
    assert request.source_version == "v1 published 2020-06-11"


def test_request_from_benchmark_rejects_version_drift(tmp_path: Path):
    with pytest.raises(AcquisitionError, match="benchmark/source version drift"):
        request_from_benchmark(
            "configs/benchmarks",
            "star_embed_ztf_40k",
            destination=tmp_path / "snapshot.bin",
            urls=("https://example.test/snapshot",),
        )
