# Source-backed Scientific Validation Adapters

The permanent scientific-validation gate uses five external evidence sources. The
repository stores the **source contract**, not mutable external benchmark data.

| ID | Source | Role | Evidence requirement |
|---|---|---|---|
| `star_embed_ztf_40k` | StarEmbed ZTF_40k | ground truth | immutable dataset/split/schema hashes |
| `ztf_periodic_781k` | ZTF CPVS / DR2 | parent catalogue / source reference | Zenodo attachment and catalog hashes |
| `ztf_periodic_730k` | published 730,184-object quality subset | published membership reference (not independent astrophysical ground truth) | immutable membership hash + explicit name-to-Seq crosswalk |
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


## 730k published membership and reconstruction boundary

The published 730,184-object Table 4 membership is an immutable catalogue-membership reference. It is not an independent astrophysical ground-truth label set. The parent Table 2 contains 781,602 unique Seq identifiers. The name-to-Seq crosswalk has been source-verified. Historical reconstruction attempts retain 741,786 candidates, including all 730,184 published members and 11,602 candidate-only IDs. This candidate list is retained historical evidence; it has not been freshly re-derived on the current main revision.

The study describes at least one 2.5σ g-band and one 3σ r-band detection. The latest source review has not established that the positive gmag, rmag, Per-g, and Per-r diagnostic predicate was the publisher's exact rule. That four-field condition must remain diagnostic and must not be adopted as a production selector without primary-source evidence or author clarification. A matching count is not proof of method. Keep Issue #170 open and fail closed for any claim of exact reproduction.


## DR24 HATS versus Zubercal

The DR24 Lightcurves HATS collection is a native DR24 time-series product. Zubercal is a separate recalibrated PSF-photometry product. They must have separate source adapters and provenance contracts. The project does not currently establish that HATS is an equivalent substitute for the Zubercal product named in the Park dossier. See [DR24 HATS and Zubercal source-product contract v0.1](../architecture/DR24_HATS_VS_ZUBERCAL_SOURCE_CONTRACT_v0.1.md). The primary-product decision remains open until it is confirmed against the approved deliverable.


## DR24 HATS and Zubercal DR20

These products are separate streams. DR24 HATS provides native ZTF lightcurves by ZTF OID. Zubercal DR20 provides PS1-matched recalibrated PSF detections; its `objectid` is a PS1 ID, its time field is MJD(TDB), and its stored `magerr` is scaled by 10,000. Zubercal does not cover sources without suitable PS1 matches. Use DR24 HATS as the primary discovery stream and Zubercal as a supplementary calibration stream. Preserve all source-native fields and match ambiguity. See [DR24 HATS and Zubercal source-product contract v0.1](../architecture/DR24_HATS_VS_ZUBERCAL_SOURCE_CONTRACT_v0.1.md).
