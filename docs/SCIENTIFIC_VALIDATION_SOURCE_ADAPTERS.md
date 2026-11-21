# Source-backed Scientific Validation Adapters

The permanent scientific-validation gate uses five external evidence sources. The
repository stores the **source contract**, not mutable external benchmark data.

| ID | Source | Role | Evidence requirement |
|---|---|---|---|
| `star_embed_ztf_40k` | StarEmbed ZTF_40k | candidate benchmark; ground-truth status not accepted | immutable dataset/split/schema hashes and completed leakage audit |
| `ztf_periodic_781k` | ZTF CPVS / DR2 | historical parent population | Zenodo attachment and catalog hashes |
| `ztf_periodic_730k` | published 730,184-object quality subset | historical membership reference | immutable publisher snapshot and membership hashes |
| `ztf_dr24_source_subset` | official ZTF DR24 | source-backed | release metadata + query/artifact hashes |
| `alerce_reference` | ALeRCE TAP | independent reference | query + response hashes + schema |

The 730k **published membership** is now pinned separately to Zenodo 5764899. It is the exact historical membership benchmark. The existing deterministic derivation from the 781,602-parent snapshot remains valuable, but is explicitly diagnostic: a current-source reconstruction is not allowed to replace the published membership when validating the historical release.

ALeRCE now has two distinct lanes: the live TAP adapter remains useful for current-source drift monitoring, while Zenodo 4279623 is the immutable historical reference snapshot for the 2020-06-09 classifier/features/output state.

ALeRCE remains an independent reference system. Its predictions cannot satisfy
ground-truth provenance requirements.

## Completion contract

An adapter is accepted only when it can produce an immutable evidence package
containing provenance, source/version identifiers, object/file hashes, schema
metadata, and the checks required by the release gate. Live-source success alone
does not close a historical reproducibility blocker.

StarEmbed is modeled as a five-artifact Parquet package. The adapter now requires a verified 40-character Hugging Face commit SHA before acquisition; unverified revisions or hashes are rejected. Acquisition binds all five artifacts into one evidence manifest. The 781k adapter pins the Zenodo Table2 attachment. DR24 and ALeRCE remain query-driven and fail closed until their returned artifacts are actually acquired.\n\nThe actual benchmark data are intentionally not committed to Git.


## CPVS membership reconstruction — unresolved

The published 730,184-object membership snapshot is the historical reference. A current-source reconstruction is diagnostic only and must not replace the published membership.

The recorded Seq-based comparison reports 781,602 parent rows, 730,184 published members, and 741,786 reconstructed candidates:
- intersection: 730,184;
- candidate-only: 11,602;
- published-only: 0.

The 11,602 candidate-only objects remain unexplained. Exact historical reconstruction is **UNRESOLVED**. Reverify source files, versions, and hashes before treating these counts as a fresh run. Do not tune a threshold or quality flag to force the candidate count to 730,184. Preserve all discrepant IDs and their provenance.

The historical four-field rule is a hypothesis until the real source artifacts, fixed samples, and full object-level comparison reproduce it. Synthetic tests do not establish historical author intent.

## Current source-evidence snapshot — 2026-11-19

Scientific Validation run #44515762163 acquired:
- a 150-row DR24 Objects Table response;
- a separate 150-row live ALeRCE reference response;
- the immutable historical ALeRCE reference manifest.

The DR24 and ALeRCE responses are not cross-matched. They are not one labeled cohort and must not be used as a model-evaluation dataset. The run proves bounded source acquisition and evidence-manifest creation only.

## DR24 HATS versus Zubercal

The DR24 Lightcurves HATS collection is a native DR24 time-series product. Zubercal is a separate recalibrated PSF-photometry product. They must have separate source adapters and provenance contracts. The project does not currently establish that HATS is an equivalent substitute for the Zubercal product named in the Park dossier. See [DR24 HATS and Zubercal source-product contract v0.1](../architecture/DR24_HATS_VS_ZUBERCAL_SOURCE_CONTRACT_v0.1.md). The primary-product decision remains open until it is confirmed against the approved deliverable.


## DR24 HATS and Zubercal DR20

These products are separate streams. DR24 HATS provides native ZTF lightcurves by ZTF OID. Zubercal DR20 provides PS1-matched recalibrated PSF detections; its `objectid` is a PS1 ID, its time field is MJD(TDB), and its stored `magerr` is scaled by 10,000. Zubercal does not cover sources without suitable PS1 matches. Use DR24 HATS as the primary discovery stream and Zubercal as a supplementary calibration stream. Preserve all source-native fields and match ambiguity. See [DR24 HATS and Zubercal source-product contract v0.1](../architecture/DR24_HATS_VS_ZUBERCAL_SOURCE_CONTRACT_v0.1.md).
