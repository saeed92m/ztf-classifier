"""Canonical external sources used by the scientific-validation product gate.

This module deliberately contains source metadata and acquisition contracts only.
It never treats a mutable live service as an immutable benchmark snapshot.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ValidationSource:
    """Versioned description of an external scientific-validation source."""

    source_id: str
    name: str
    source_type: str
    version: str
    url: str
    provenance_role: str
    acquisition: str
    immutable_evidence_required: bool = True


SOURCES: tuple[ValidationSource, ...] = (
    ValidationSource(
        source_id="star_embed_ztf_40k",
        name="StarEmbed ZTF_40k",
        source_type="dataset",
        version="2026-05 dataset snapshot",
        url="https://huggingface.co/datasets/StarEmbed/ZTF_40k",
        provenance_role="ground_truth",
        acquisition="Hugging Face dataset snapshot; record split/schema/content hashes.",
    ),
    ValidationSource(
        source_id="ztf_periodic_781k",
        name="ZTF Catalog of Periodic Variable Stars",
        source_type="catalog",
        version="v1 published 2020-06-11",
        url="https://zenodo.org/records/3886372",
        provenance_role="ground_truth",
        acquisition="Zenodo release; record attachment hashes and catalog row/object counts.",
    ),
    ValidationSource(
        source_id="ztf_periodic_730k",
        name="ZTF CPVS quality-selected 730k subset",
        source_type="derived_dataset",
        version="derived subset from Zenodo 3886372 / ZTF DR2",
        url="https://doi.org/10.3847/1538-4357/ac69d4",
        provenance_role="ground_truth",
        acquisition=(
            "Derive only from the pinned 781,602-object CPVS snapshot using the "
            "published g/r detection criteria; record parent hash and selection code version."
        ),
    ),
    ValidationSource(
        source_id="ztf_dr24_source_subset",
        name="ZTF Data Release 24",
        source_type="survey_release",
        version="DR24",
        url="https://irsa.ipac.caltech.edu/data/ZTF/docs/releases/dr24/",
        provenance_role="ground_truth",
        acquisition=(
            "Use the official DR24 archive/API; pin release metadata, source/object IDs, "
            "query parameters, and returned-artifact hashes."
        ),
    ),
    ValidationSource(
        source_id="alerce_reference",
        name="ALeRCE ZTF reference system",
        source_type="reference_system",
        version="live service; pin response manifest per run",
        url="https://tap.alerce.online/tap",
        provenance_role="reference_system",
        acquisition=(
            "Query the ALeRCE TAP service through an explicit query manifest; store "
            "query text, retrieval timestamp, response hashes, and schema metadata."
        ),
    ),
)


def get_source(source_id: str) -> ValidationSource:
    """Return a canonical source descriptor or raise KeyError."""
    for source in SOURCES:
        if source.source_id == source_id:
            return source
    raise KeyError(source_id)


def source_ids() -> tuple[str, ...]:
    """Return source identifiers in stable order."""
    return tuple(source.source_id for source in SOURCES)
