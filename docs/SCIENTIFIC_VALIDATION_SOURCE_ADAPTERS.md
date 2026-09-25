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

The actual benchmark data are intentionally not committed to Git.
