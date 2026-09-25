"""Source-backed benchmark adapter contracts."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

from ztf_classifier.validation.manifest import BenchmarkManifest
from ztf_classifier.validation.sources import ValidationSource, get_source


class AdapterContractError(ValueError):
    """Raised when a benchmark cannot satisfy its canonical adapter contract."""


@dataclass(frozen=True)
class AdapterPlan:
    """Deterministic acquisition/derivation plan for one benchmark."""

    benchmark_id: str
    source_id: str
    source_version: str
    role: str
    urls: tuple[str, ...]
    destination_name: str
    query_manifest: dict[str, Any] | None = None
    parent_benchmark_id: str | None = None

    def validate(self) -> None:
        if not self.urls:
            raise AdapterContractError("adapter plan must contain at least one source URL")
        if any(not isinstance(url, str) or not url.startswith(("http://", "https://")) for url in self.urls):
            raise AdapterContractError("adapter plan contains an invalid source URL")
        if not self.destination_name or Path(self.destination_name).name != self.destination_name:
            raise AdapterContractError("destination_name must be a plain file name")


AdapterBuilder = Callable[[BenchmarkManifest], AdapterPlan]


def _source_plan(manifest: BenchmarkManifest, source: ValidationSource) -> AdapterPlan:
    if manifest.input_contract.get("adapter") != source.source_id:
        raise AdapterContractError(
            f"manifest adapter {manifest.input_contract.get('adapter')!r} "
            f"does not match canonical source {source.source_id!r}"
        )
    if source.source_id != "ztf_periodic_730k" and manifest.version != source.version:
        raise AdapterContractError(
            f"benchmark/source version drift: benchmark={manifest.version!r}, source={source.version!r}"
        )
    plan = AdapterPlan(
        benchmark_id=manifest.benchmark_id,
        source_id=source.source_id,
        source_version=source.version,
        role=manifest.evaluation_role,
        urls=(source.acquisition_url or source.url,),
        destination_name=f"{manifest.benchmark_id}.snapshot",
    )
    plan.validate()
    return plan


def _derived_730k_plan(manifest: BenchmarkManifest) -> AdapterPlan:
    source = get_source("ztf_periodic_730k")
    if manifest.input_contract.get("adapter") != source.source_id:
        raise AdapterContractError("730k manifest is not bound to the canonical 730k adapter")
    parent = manifest.ground_truth_provenance.get("parent_benchmark")
    if parent != "ztf_periodic_781k":
        raise AdapterContractError("730k adapter requires parent_benchmark=ztf_periodic_781k")
    plan = AdapterPlan(
        benchmark_id=manifest.benchmark_id,
        source_id=source.source_id,
        source_version=source.version,
        role=manifest.evaluation_role,
        urls=(get_source("ztf_periodic_781k").acquisition_url or get_source("ztf_periodic_781k").url,),
        destination_name=f"{manifest.benchmark_id}.derived",
        query_manifest={
            "operation": "deterministic_quality_selection",
            "parent_benchmark_id": "ztf_periodic_781k",
            "selection": "published g/r detection-quality criteria; implementation must be pinned before derivation",
        },
        parent_benchmark_id="ztf_periodic_781k",
    )
    plan.validate()
    return plan


def _dr24_plan(manifest: BenchmarkManifest) -> AdapterPlan:
    plan = _source_plan(manifest, get_source("ztf_dr24_source_subset"))
    query = manifest.input_contract.get("query")
    if not isinstance(query, dict) or not query:
        raise AdapterContractError("DR24 adapter requires input_contract.query for a pinned source subset")
    return AdapterPlan(**{**plan.__dict__, "query_manifest": dict(query)})


def _alerce_plan(manifest: BenchmarkManifest) -> AdapterPlan:
    plan = _source_plan(manifest, get_source("alerce_reference"))
    query = manifest.input_contract.get("query")
    if not isinstance(query, str) or not query.strip():
        raise AdapterContractError("ALeRCE adapter requires a non-empty TAP query")
    return AdapterPlan(**{**plan.__dict__, "query_manifest": {"tap_query": query}})


def build_adapter_plan(manifest: BenchmarkManifest) -> AdapterPlan:
    """Build the canonical plan without acquiring or fabricating external data."""
    builders: dict[str, AdapterBuilder] = {
        "star_embed_ztf_40k": lambda m: _source_plan(m, get_source("star_embed_ztf_40k")),
        "ztf_periodic_781k": lambda m: _source_plan(m, get_source("ztf_periodic_781k")),
        "ztf_periodic_730k": _derived_730k_plan,
        "ztf_dr24_source_subset": _dr24_plan,
        "alerce_reference": _alerce_plan,
    }
    try:
        builder = builders[manifest.benchmark_id]
    except KeyError as exc:
        raise AdapterContractError(f"no canonical adapter for {manifest.benchmark_id!r}") from exc
    return builder(manifest)
