from pathlib import Path

from ztf_classifier.validation.acquisition import request_from_benchmark


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


from ztf_classifier.validation.acquisition import AcquisitionError


def test_request_from_benchmark_uses_canonical_adapter_plan_when_urls_omitted():
    request = request_from_benchmark(
        "configs/benchmarks",
        "star_embed_ztf_40k",
        destination="/tmp/star_embed.snapshot",
        urls=(),
    )
    assert request.urls == ("https://huggingface.co/datasets/StarEmbed/ZTF_40k",)


def test_730k_request_requires_parent_evidence_binding():
    import pytest

    with pytest.raises(AcquisitionError, match="parent_evidence_sha256"):
        request_from_benchmark(
            "configs/benchmarks",
            "ztf_periodic_730k",
            destination="/tmp/cpvs-730k.derived",
            urls=(),
        )
