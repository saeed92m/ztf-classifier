# ZTF DR24 HATS raw light-curve payload probe — 2026-11-03

## Disposition

**Raw-source acquisition: VERIFIED for the four listed OIDs and the recorded retrieval.**  
**Application integration and scientific validity: NOT VERIFIED.**

This report records a bounded live retrieval from the official IRSA ZTF DR24 Lightcurves HATS catalog. It does not certify the production API adapter, Workbench UI, astrophysical object identity, feature extraction, or classifier performance.

## Source and method

- Source: IRSA ZTF DR24 Lightcurves HATS
- Catalog URI: `s3://ipac-irsa-ztf/ztf/enhanced/dr24/lc/hats`
- Lookup index: `objectid`
- Probe implementation: `scripts/probe_ztf_dr24_lightcurve_payload.py`
- Workflow: [DR24 Lightcurve Payload Probe, run 41674952418](https://github.com/saeed92m/ztf-classifier/actions/runs/41674952418)
- Independent repeat: [run 41674221225](https://github.com/saeed92m/ztf-classifier/actions/runs/41674221225)
- Retrieval time (run 41674952418): `2026-11-03T16:35:50.070311+00:00`
- Runtime: Python 3.11.16, LSDB 0.10.4, pandas 2.3.3, s3fs 2026.9.0
- Catalog schema: 13 columns
- Schema column-name SHA-256: `9114cbba3b014cab91193e225bcdebf2f89878c10a1bab890dd9e683aa5a23f9`

The workflow requested four OIDs. It returned all four. The manifest reports no missing OIDs. The total payload contains 626 epoch rows.

## Per-OID results

| Object ID | Filter | Field | Quadrant | Epochs | catflags=0 | catflags=32768 |
|---:|---:|---:|---:|---:|---:|---:|
| 264114400013085 | g (1) | 264 | 55 | 78 | 71 | 7 |
| 264214400000912 | r (2) | 264 | 55 | 123 | 115 | 8 |
| 278115200026587 | g (1) | 278 | 57 | 216 | 191 | 25 |
| 278215200018105 | r (2) | 278 | 57 | 209 | 193 | 16 |
| **Total** | | | | **626** | **570** | **56** |

For all four OIDs, the returned payload row count matches the catalog `nepochs` value.

Across all 626 epochs:

- `hmjd`, `mag`, and `magerr` are finite.
- All 626 `magerr` values are positive.
- `catflags` contains 570 zero values and 56 values equal to 32768.
- The payload includes `hmjd`, `mag`, `magerr`, `clrcoeff`, and `catflags`.
- No rows were removed by a quality filter.

## Integrity evidence

Artifact: [download from workflow run 41674952418](https://github.com/saeed92m/ztf-classifier/actions/runs/41674952418)

- Artifact ID: `13251350175`
- Artifact SHA-256: `8c17485d3b5ba651a997d5bc5ad5bca7528655685e8204fdf416af08176fccc7`
- Epoch CSV: 61,875 bytes
- Epoch CSV SHA-256: `c37f4d7ac4e294b14a3f2e87b9b35bacaf79a4baf02b30ab85df2984b1d29bbd`
- Summary JSON SHA-256: `020f7febb47b3fd95720b383d6302254d88c6b2a54a8d080eef6375ebb989835`
- Manifest JSON SHA-256: `fd5936378eca2ffb5ec2d71ecf9d643c7a95f6656510cb36846dda45a4db0865`

The artifact ZIP digest and the two output-file digests were recomputed from the downloaded artifact. Both output hashes match the manifest. The manifest, summary, and epoch CSV agree on the 626-row count and four OIDs.

The independent run 41674221225 produced the same epoch CSV SHA-256 and summary JSON SHA-256. This supports repeatability for this exact bounded query and source snapshot. It does not establish that the source is immutable or that all DR24 objects behave identically.

## Scientific and engineering boundaries

The probe retains source-native values:

- `hmjd` remains HMJD. It is not converted or relabeled as MJD.
- `mag` remains in the native DR24 photometric system.
- `clrcoeff` is retained separately. No color correction is applied.
- `catflags` is retained. Bit-15 rows are visible and are not silently dropped.
- OIDs remain separate. No cross-OID identity inference or grouping is performed.

The probe does not implement a validated DR24 quality policy, feature contract, classifier input mapping, calibration, abstention, OOD detection, anomaly detection, or astrophysical identity resolution.

## What this evidence proves

1. The public DR24 HATS catalog can be queried by the `objectid` index for these four OIDs.
2. The returned payload contains 626 epochs across both g and r filters.
3. Catalog `nepochs` values match the returned epoch counts for all four OIDs.
4. The raw fields and payload hashes can be retained in a compact reproducibility artifact.
5. The bounded probe repeated with identical output hashes in two independent runs.

## What remains unverified

1. PR #264's FastAPI endpoint has not yet been verified against a live HATS retrieval.
2. PR #267's Workbench view has not yet passed browser interaction tests against the live API.
3. The 5–10 object application smoke test has not been accepted.
4. The 30–50 object guided Park demonstration has not been completed.
5. OID-to-astrophysical-source grouping requires a curated, evidence-backed crosswalk.
6. No DR24 feature contract or DR24-specific classifier has been validated.
7. No classification accuracy, calibration, anomaly performance, or scientific discovery claim follows from this raw acquisition probe.

## Next acceptance sequence

1. Complete the isolated repeat on PR #268 and compare its artifact hashes.
2. Verify PR #264's API route against the same OIDs and compare the raw response with the probe artifact.
3. Verify PR #267's browser view against the API response. Test valid, missing, invalid, and source-failure cases.
4. Add a 5–10 object smoke-test manifest with explicit success, skip, and failure reasons.
5. Only then expand to the 30–50 object guided demonstration.

References:
- [IRSA ZTF DR24 data release and access](https://irsa.ipac.caltech.edu/Missions/ztf.html)
- [ZTF DR24 release notes](https://irsa.ipac.caltech.edu/data/ZTF/docs/releases/dr24/ztf_release_notes_dr24.pdf)
- [Probe workflow source](https://github.com/saeed92m/ztf-classifier/blob/main/.github/workflows/dr24-lightcurve-payload-probe.yml)
