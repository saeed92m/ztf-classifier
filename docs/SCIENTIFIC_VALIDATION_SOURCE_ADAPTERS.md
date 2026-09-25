# Source-backed Scientific Validation Adapters

The permanent scientific-validation gate uses five external evidence sources. The
repository stores the **source contract**, not mutable external benchmark data.

| ID | Source | Role | Evidence requirement |
|---|---|---|---|
| `star_embed_ztf_40k` | StarEmbed ZTF_40k | ground truth | immutable dataset/split/schema hashes |
| `ztf_periodic_781k` | ZTF CPVS / DR2 | ground truth | Zenodo attachment and catalog hashes |
| `ztf_periodic_730k` | published 730,184-object quality subset | ground truth | parent snapshot hash + deterministic selection |
| `ztf_dr24_source_subset` | official ZTF DR24 | source-backed | release metadata + query/artifact hashes |
| `alerce_reference` | ALeRCE TAP | independent reference | query + response hashes + schema |

The 730k source is a **derived, deterministic subset** of the pinned ZTF CPVS
snapshot; it is not treated as a second independent catalog.

ALeRCE remains an independent reference system. Its predictions cannot satisfy
ground-truth provenance requirements.

## Completion contract

An adapter is accepted only when it can produce an immutable evidence package
containing provenance, source/version identifiers, object/file hashes, schema
metadata, and the checks required by the release gate. Live-source success alone
does not close a historical reproducibility blocker.

StarEmbed is modeled as a five-artifact Parquet package. The adapter now requires a verified 40-character Hugging Face commit SHA before acquisition; unverified revisions or hashes are rejected. Acquisition binds all five artifacts into one evidence manifest. The 781k adapter pins the Zenodo Table2 attachment. DR24 and ALeRCE remain query-driven and fail closed until their returned artifacts are actually acquired.\n\nThe actual benchmark data are intentionally not committed to Git.


## 730k deterministic derivation

The 730,184-object release is not treated as an independently downloadable source. The derivation runner consumes the pinned 781,602-object CPVS parent plus the published ZTF2 g/r light-curve artifacts. It requires at least one g-band detection at 2.5σ and one r-band detection at 3σ, and fails closed unless the resulting object count is exactly 730,184. The published study describes the same 730,184/781,602 selection and thresholds. The runner writes a content hash of the selected SourceID manifest and a derivation manifest containing the selection parameters and output hash.

The derivation runner requires the parent evidence SHA and emits an immutable evidence manifest for the derived snapshot. It fails closed if the parent count or derived count does not match the published 781,602 / 730,184 populations. The repository still does not claim that derivation evidence exists until the real source artifacts have been acquired and the runner has produced the expected count.
