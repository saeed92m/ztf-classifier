# CPVS parent-population stratified sample audit — 2026-11-01

## Disposition

**Partial diagnostic evidence only. CPVS scientific validation remains BLOCKED.**

This audit creates deterministic 100-object and 1,000-object samples from the retained historical parent metadata artifact. It does not establish the publisher's intended selection method. It does not replace a fresh comparison against the original Table 4 bytes or a source-backed rerun on the current main revision.

## Retained source artifact

GitHub Actions run: [38635891449](https://github.com/saeed92m/ztf-classifier/actions/runs/38635891449)  
Artifact: `scientific-validation-heavy` (artifact ID `11935357767`)

Verified input hashes:

| Input | SHA-256 |
|---|---|
| `parent_metadata.tsv` | `3675b1274f73fcb15d47e7a780f194ef8fa335cd248c6ff53ea4f01559c86591` |
| `selected.tsv` | `699ff34bcf8dd4b5043eed48384973cb5109fd86ca260f831a502097370238df` |
| `selection_diagnostics.json` | `7e763d8804a57d75d1633d0a4089a4a6ac5aa40bb4695964d35e645b67ad5b61` |
| `membership_audit.json` | `4c1a082569820af26cbca80320a4913a00e1849446b0ca0205fc872b5ce89c5c` |

The parent TSV contains 781,602 unique `Seq` values. The ID range is 1–781,604. The candidate TSV contains 741,786 unique IDs. The retained membership audit records 730,184 published objects, 730,184 candidate/reference intersection, 11,602 candidate-only objects, and zero published-only objects.

**Membership caveat:** the retained artifact does not contain the raw Table 4 bytes or the full published-ID list. For this sample, the 730,184 reference-member IDs were reconstructed as `candidate IDs − candidate_only_all_objects`, using the retained audit's zero published-only result. The sample labels are therefore marked *inferred from the retained membership audit*. They are not a fresh independent Table 4 join.

## Full candidate-only diagnostic

The retained object-level diagnostics contain all 11,602 candidate-only IDs.

- 11,602/11,602 have `snr_exact=true` in both g and r in the retained diagnostics.
- 11,585 fail at least one of the parent mean-magnitude fields `gmag` or `rmag`.
- 17 have both parent mean magnitudes, but one band-specific period field is missing or non-positive.
- Within the 11,585 objects that fail the parent mean-magnitude pair, 11,580 also fail at least one band-specific period field; 5 have both period fields but fail the g-band mean-magnitude field.
- 14 have zero in at least one parent detection-count field (`Ng` or `Nr`).

These associations reproduce the historical diagnostic pattern. They do not prove that the four-field condition was the publisher's selection rule. The paper documents per-band SNR detections and use of the common period; it does not explicitly require both band-specific period fields and both parent mean magnitudes to be positive.

## Sampling method

The sample is stratified across three disjoint groups:

1. `published_inferred`: candidate IDs not listed in the retained candidate-only set.
2. `candidate_only`: the 11,602 retained candidate-only IDs.
3. `parent_not_candidate`: parent IDs absent from the candidate set.

Selection within each group is deterministic. Objects are ranked by the SHA-256 digest of:

`CPVS-parent-sample-v1|<stratum>|<SourceID>`

The lowest digests are selected. The sample is not a simple random sample. It is a fixed stratified diagnostic sample that includes reference-member and non-member populations.

| Sample | Inferred reference members | Candidate-only | Parent non-candidates | Total |
|---|---:|---:|---:|---:|
| 100-object | 50 | 25 | 25 | 100 |
| 1,000-object | 500 | 250 | 250 | 1,000 |

## Sample results

### 100-object sample

- Inferred reference members: 50/50 have all four metadata fields positive.
- Candidate-only: 0/25 have all four fields positive; all 25 fail `gmag` and `Per-g`.
- Parent non-candidates: 0/25 have all four fields positive; 15 fail `gmag` and `Per-g`, and 10 fail `rmag` and `Per-r`.

Sorted SourceID-list SHA-256: `78e3bd319f2ec71f7d413019885b68e4e3c8aea66a340b6c1b7fb5b8149d2027`  
CSV SHA-256: `ba0b09f432f338d2a74f1bb761489c569d13e2613e9ce892beb9f7d0d789e5cb`

### 1,000-object sample

- Inferred reference members: 500/500 have all four metadata fields positive.
- Candidate-only: 0/250 have all four fields positive; 247 fail `gmag` and `Per-g`, and 3 fail `rmag` and `Per-r`.
- Parent non-candidates: 1/250 has all four fields positive; 165 fail `gmag` and `Per-g`, and 84 fail `rmag` and `Per-r`.

Sorted SourceID-list SHA-256: `89fbd76e8d23241547dc3b6d5b01b258a9468e67cae0f2576ad502e5a4f6da3d`  
CSV SHA-256: `86395f0be5946f428ddea86b114d7fc6dd5a614102b006def3bd954b314a6d00`

Per-stratum sorted ID hashes:

| Sample | Stratum | Count | SHA-256 |
|---|---|---:|---|
| 100 | published_inferred | 50 | `29385a60155db98c1dade586ebf2e917db2810f1c700c5c02eccd2e0d10cad34` |
| 100 | candidate_only | 25 | `1847b66fdc47c54c86c4a6a055257c00cf2d14dd5612a57debb956dd94d6211b` |
| 100 | parent_not_candidate | 25 | `d26a957d379ccf6a628b36eb8f54f9d800791fd2a22e6012f6d67766619d0f40` |
| 1,000 | published_inferred | 500 | `116288f81afd8bf9762e00d0bbb6f44debf57ad2db9b2f638d774a2e34647663` |
| 1,000 | candidate_only | 250 | `2d45eeac883529fc4102a000b7c3c84d36b953d3a55c9f6f56c8461b8d35f5b0` |
| 1,000 | parent_not_candidate | 250 | `6976381368c7f5450cc9290ac5e4063f553baac5f3022ca3ddf812feac9998a8` |

## Interpretation and next gates

The samples support the historical association between candidate-only status and incomplete/non-positive parent metadata. They do not establish causality. The 11,602 objects still pass the retained per-band SNR diagnostics. The scientific question remains why the documented SNR/detection rule, when reconstructed from the available photometry, admits these objects while the frozen published reference excludes them.

Required next actions:

1. Re-run the audit on a current-main source revision with a validated Table 2 crosswalk and a fresh independent published membership source.
2. Preserve and hash the exact Table 2 and Table 4/Zenodo membership bytes. Do not treat a matching row count as proof of object-level identity.
3. Reconcile all 11,602 candidate-only IDs against source-level photometry and reference membership.
4. Complete the same fixed samples against the fresh reference membership and retain the sample IDs, hashes, commands, and intermediate outputs.
5. Establish the documented SNR/detection semantics or record a supported limitation. Do not change the production selector or acceptance criteria to force a match.

No production selector, SNR threshold, model, feature set, v0.2.0 baseline artifact, class order, or scientific acceptance criterion was changed.
