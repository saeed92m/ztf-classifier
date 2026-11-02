# CPVS selection-rule evidence and identifier integrity

**Status: evidence narrowed; scientific reproduction remains blocked.** This document separates statements made by the paper, VizieR's data-format contract, and inferences from our reconstruction. It does not authorize changing the production selection predicate or closing issue #170.

## Primary sources

1. Chan et al. (2022), *Searching for Anomalies in the ZTF Catalog of Periodic Variable Stars*, Section II.1: https://arxiv.org/html/2112.03306v1#S2.SS1
2. Official CDS/VizieR ReadMe for Chen et al. (2020), catalogue J/ApJS/249/18: https://cdsarc.cds.unistra.fr/viz-bin/ReadMe/J/ApJS/249/18?format=html&tex=true
3. CPVS original data record: https://doi.org/10.5281/zenodo.3886372

## What the paper explicitly says

Section II.1 states that the authors extracted 730,184 of 781,602 CPVS light curves that contain at least one 2.5-sigma and 3-sigma detection in the g and r bands, respectively. It says they phase-fold both bands using the common period provided in Table 2.

The paper does **not** explicitly state in this passage that an object must have non-null Table 2 values for both mean magnitudes (gmag, rmag) and both band-specific periods (Per-g, Per-r). Therefore, the four-field predicate must not be described as the proven historical selection rule.

The paper later defines the mean-color feature from the mean g and r magnitudes. That makes missing mean magnitudes relevant to downstream processing, but does not alone prove they were used as an upstream membership filter.

## VizieR table semantics

The official ReadMe specifies Table 2's byte layout:
- ID: bytes 1–22, ZTF catalogue identifier.
- Seq: bytes 24–29, internal source identifier.
- gmag: bytes 90–95, ?=0.
- rmag: bytes 97–102, ?=0.
- Per-g: bytes 104–116, ?=0.
- Per-r: bytes 118–130, ?=0.
- Ng and Nr: detection counts in g and r, bytes 132–135 and 137–140.

In CDS ReadMe notation, ?=0 marks a nullable numeric field whose null sentinel is zero. Thus positive values are evidence that the relevant summary field is present; they do not by themselves prove the paper required every such field for sample membership.

The ReadMe also reports 781,602 Table 2 records and a Seq range of [1/781604]. Because the declared range extends two above the row count, Seq is not equivalent to a one-based row ordinal. The parser must preserve authoritative Seq values, including legitimate gaps, while rejecting malformed, out-of-range, or duplicate identifiers.

## Current reconstructed membership evidence

The retained source-backed artifact reports:
- Parent Table 2 objects: 781,602.
- Rowwise-SNR candidates: 741,786.
- Published Table 4 membership: 730,184.
- Candidate-only: 11,602.
- Published-only: 0.

On the retained historical candidate snapshot C and the full Table 2 four-field set F, the intersection C ∩ F contains exactly 730,184 IDs and equals the raw Table 4 membership P. The four-field set F alone contains 55 objects outside P, so F alone is refuted as the published selector. This is exact empirical set equivalence for the archived inputs, not proof of author intent or validation of a fresh derivation.

One reported partition of the 11,602 extras is:
- 11,580 fail both the mean-magnitude pair and the per-band-period pair.
- 17 have both mean magnitudes but a missing per-band period.
- 5 have both per-band periods but a missing g-band mean magnitude.

This partition sums to 11,602. A separate earlier field-pattern report used a different mutually exclusive grouping (11,465 with both gmag=0 and Per-g=0; 115 with rmag=0 and Per-r=0; 10 with only Per-g=0; 7 with only Per-r=0; and 5 with only gmag=0). These summaries use different grouping rules and must not be mixed as if they were the same partition; the row-level artifact should be used to reconcile them if needed.

## Identifier-integrity defect and remediation

The current main implementation of _source_ids_from_catalog counts ZTF-named rows and assigns one-based ordinals instead of reading the official Seq field. That contradicts the published source schema and can silently misalign light-curve joins if a row is skipped or Seq is non-contiguous.

The isolated branch fix/cpvs-seq-authoritative-ids-20261024 reads bytes 24–29 as the authoritative Seq, preserves gaps, and fails closed on malformed, truncated, out-of-range, or duplicate identifiers. Regression tests cover valid fixed-width rows, a legitimate Seq gap, an out-of-range value, a duplicate Seq, a malformed Seq, and a truncated row. This branch is not merged; CI and a source-backed run must confirm behavior against the full official parent file before adoption.

## Next scientific checks

1. Run the new parser tests and normal CI on the isolated branch.
2. Run a source-backed heavy validation against the official Table 2 file; inspect the actual Seq gaps and duplicate/invalid IDs before accepting any membership count.
3. Query Ng and Nr for all 11,602 candidate-only objects, retaining query timestamp, response bytes, and hashes. Nonzero counts alongside null summary fields would support a catalogue-summary inconsistency hypothesis, but not prove the original paper's exact selection rule.
4. Compare the original Zenodo ztf2g/ztf2r files with the VizieR attachments for the same identifiers, with per-object provenance.
5. Keep issue #170 open until the identifier mapping and the remaining selection semantics are supported by reproducible evidence. Keep #196 open until strict JSON output is regenerated and verified, not merely until a test passes.

## Guardrails

No production membership rule, threshold, model baseline, acceptance criterion, release artifact, or issue status is changed by this investigation. A matching count is not a scientific validation result by itself.


## Non-finite SNR guard regression

The derivation must explicitly reject non-finite SNR before comparing it to the per-band threshold. In Python, `NaN < threshold` is false, so a negative-only threshold predicate can admit invalid errors. A focused regression test now covers NaN, positive infinity, zero and negative errors, unparseable error text, and one valid row. This guard fixes a demonstrated predicate defect; it does not by itself establish the root cause or resolve the full CPVS membership discrepancy.


## Raw CDS reconciliation and fixed diagnostic samples — 2026-11-02

The byte-preserving reconciliation workflow 41360681445 completed successfully. It verified raw CDS Table 2 and Table 4 against the corresponding IOP/AAS publisher MRT records. It found 781,602 Table 2 rows, 730,184 Table 4 rows, zero row mismatches against the publisher files, zero unmapped ZTF names, and zero differences between Table 4 ID and Table 2 Seq for all 730,184 rows.

For the archived historical candidate set:

- C = 741,786 two-band SNR candidates.
- F = 730,239 parent rows with all four nullable fields positive.
- P = 730,184 raw Table 4 members.
- C ∩ F = P exactly.
- F \ C = 55 objects. These 55 are absent from Table 4 and from the historical SNR candidate list.

The 11,602 candidate-only objects partition into 11,580 with both field pairs incomplete, 17 with both mean magnitudes but an incomplete per-band period pair, and 5 with both per-band periods but an incomplete mean-magnitude pair.

The revised SHA-256-ranked sample design includes four strata: reference-and-candidate, candidate-only, four-field-only controls, and parent-neither. The 100-object sample contains 50/25/10/15 objects. The 1,000-object sample contains 500/250/55/195 objects and includes all 55 four-field-only controls. The samples are diagnostic oversamples, not prevalence estimates.

This conjunction remains an empirical hypothesis. The paper does not state the four-field requirement. A separate partial original-photometry audit of all 55 controls is now available; see the section below. The exact historical selector and the current-head fresh derivation remain unresolved. Do not change the production selector or scientific gate.


## Staged membership diagnostic — current derivation boundary

The historical candidate set C contains 741,786 objects. Applying both positive Table 2 mean magnitudes M leaves 730,201 objects, with 17 candidate-only residuals and zero reference-only IDs. All 17 have both mean magnitudes, but lack one band-specific period: 10 lack Per-g and 7 lack Per-r. Adding the two per-band period fields Q gives C ∩ M ∩ Q = P exactly (730,184).

Correction from direct source inspection (2026-11-02): the current `derive_730k()` implementation does **not** read Table 2 mean `gmag` or `rmag`, and it does not test `Per-g` or `Per-r`. `_qualified_ids()` records an object in `valid_magnitude` when an SNR-qualified per-epoch photometry row has a finite, non-zero magnitude. `derive_730k()` intersects those per-epoch validity sets. Therefore, the 730,201-object result and 17 residuals above belong to the separate `baseline_plus_nonzero_parent_mean_magnitudes_diagnostic`; they are not the demonstrated output of `derive_730k()`. A fresh current-head source-backed run (GitHub Actions run 41417144949, commit 377cfd17aa6ef6f3b6c938edc1453ecb66977bf7) is in progress to establish the actual output. Do not add a metadata or period-pair condition until the current run and original published method support it.

The five other residuals in the original 11,602 have both per-band periods but lack a mean magnitude; all five lack gmag. The 11,602 residual partition is therefore consistent with a staged metadata-completeness hypothesis, but it does not prove author intent.

The approximate magnitude-error SNR formula, the exact inverse magnitude-error transform, and 1/e_mag produced the same historical 741,786-object candidate set and 11,602 residuals. The tested SNR formula choice is not the cause. A zero-catalog-flag condition is also refuted as a substitute because it loses 5,472 reference members.



## Original Zenodo photometry coverage audit — 2026-11-02

This audit used the published Zenodo v1 attachments for DOI `10.5281/zenodo.3886372`. Both downloaded ZIP files match the published MD5 values. The g-band full-layout diagnostic is GitHub Actions run [41410496155](https://github.com/saeed92m/ztf-classifier/actions/runs/41410496155), artifact `13126290795`. The 55-control photometry audit is retained in raw reconciliation run [41367972395](https://github.com/saeed92m/ztf-classifier/actions/runs/41367972395), artifact `13108147605`.

### g-band full-archive counts

- Zenodo `ztf2g.zip` MD5: `850fcef561dd7407fbe8e19e99100d7a` (published value).
- ZIP SHA-256: `47cd1823b3ccdb69fa3085381cf63ff0605f6d841fc3bc37489dce023ddc19b9`.
- Extracted photometry SHA-256: `366aaf3539f83955bb1e29799df9e63005a9eb682f4f56d0807545a3534b0f16`.
- Parsed CSV rows: 89,697,393; all rows have seven fields; malformed rows: 0.
- Sum of Table 2 `Ng`: 89,702,309. The archive contains 4,916 fewer rows than this sum.
- 91 Table 2 Seq values have a direct row-count mismatch: 35 have more archive rows than `Ng`; 56 have fewer. Of the 56, 55 have no g-band archive rows despite positive Table 2 `Ng`.
- One archive-only Seq, `615172`, has 132 rows. Table 2 has gaps at Seq 615171 and 615172; Table 2 Seq 615170 has `Ng=132` but no g archive rows. A coordinate crosswalk found no coordinate match for Table 2 Seq 615170. The equal count of 132 is not evidence that Seq 615172 belongs to Seq 615170. Do not merge these identities.
- A coordinate diagnostic for the 91 mismatch targets found 23 objects with coordinate-matched archive rows and 68 with none. It found zero ambiguous coordinate rows and no Seq mismatch among the 23 matches. For those 23, 22 archive row counts exceed `Ng` and one is lower. This is a diagnostic crosscheck, not a replacement identifier join.

### The 55 four-field-only controls

All 55 controls have positive Table 2 `Ng` and `Nr`, but the published Zenodo attachments do not contain both bands for any control:

- g band: 1 of 55 objects has photometry; its 119 rows match Table 2 `Ng` and it passes the g threshold. The other 54 have no g archive rows.
- r band: 51 of 55 objects have photometry; all 51 row counts match Table 2 `Nr` and all 51 pass the r threshold. The other 4 have no r archive rows.
- No control has both g and r archive coverage. Therefore none can be reconstructed as a two-band SNR candidate from these attachments.

The previous report labels these objects as failed g/r SNR. That wording is too broad: for the missing band, no SNR test is possible because there are no rows. The correct interpretation is missing archive coverage. Table 2 reports positive detection counts for these same objects, so the attachment-to-catalogue coverage discrepancy remains a separate source-integrity issue.

### Overlap with the 11,602 candidate-only objects

14 of the 11,602 historical candidate-only IDs also occur in the 91-object g row-count mismatch set:
- 13 have Table 2 `Ng=0` but have g-band archive rows.
- Seq `339262` has Table 2 `Ng=83` and 85 archive rows.
- The other 11,588 candidate-only IDs have no g row-count mismatch in this diagnostic.

This demonstrates that the Table 2 summary counts and the Zenodo g attachment are not identical for every object. It does not explain the 11,602 membership residuals.

### Source hashes and limitations

- Zenodo `ztf2r.zip` MD5: `daa7bc45c67579253eebe6b1c09dfbd9` (published value).
- ZIP SHA-256: `48331ba1157afc993a1399e094b97752a82d8d0f736d2fdf63fd7b2a82281b74`.
- The 55-control r audit is not a full 781,602-object r row-count reconciliation.
- The g coordinate crosswalk uses a 2e-5 degree tolerance against Table 2 coordinates rounded to five decimal places. It is not a proof of source identity for unmatched objects.
- The audit does not infer the authors' selection rule and does not establish the cause of the 11,602 residuals.

Keep the source-coverage issue separate from the candidate-membership issue. Do not change the selector, thresholds, baseline, or acceptance criteria based on these diagnostics alone.


## Independent frozen-membership crosswalk — 2026-11-02

The current branch CI completed a full object-level crosswalk from the independent frozen Zenodo membership file (DOI `10.5281/zenodo.5764899`, `1st_layer.csv`) through Table 2 ZTF names to authoritative Table 2 `Seq` values.

- Workflow run: [41417954609](https://github.com/saeed92m/ztf-classifier/actions/runs/41417954609).
- Artifact: `13128218475`, `cpvs-full-zenodo-membership-crosswalk.zip`.
- Manifest status: `VERIFIED`.
- Table 2 rows and unique Seq values: 781,602.
- Frozen Zenodo rows, unique names, and unique Seq values: 730,184.
- Unmapped published names: 0.
- Sorted published Seq SHA-256: `18fba7523a4f66fa2314d017433e3ef8bdbe85f1980557bc1f1e0dc61094774c`.
- This hash is identical to the raw CDS Table 4 / Zenodo membership hash already verified in the raw reconciliation.
- Zenodo Table 2 source SHA-256: `9139e4edea0c129772a1d9ac994512183733907e9585aaf1a6f35e4e1cd2e6ff`.
- Frozen Zenodo membership CSV SHA-256: `c235df101bf7a130b5dccdd95b786ac347f2b7ef24fc49ed7ae989aa8625437`.
- Output `published_membership_seq.tsv` SHA-256: `ee5062c8cd6368579e803f2df66f0d2e991a5b2cc9cfaa6d6662ba335f677721`.
- The workflow did not use raw Table 4. This is an independent membership crosswalk, not a direct byte comparison.

The 17 residual IDs listed above have zero intersection with this independently reconstructed 730,184-member set. This confirms their non-membership in the frozen reference; it does not explain why the paper excluded them.


## Direct 17-object frozen-reference audit — 2026-11-02

The dedicated 17-object audit completed in workflow run [41417954609](https://github.com/saeed92m/ztf-classifier/actions/runs/41417954609), artifact `13129155423`.

- Status: `COMPLETED`.
- Target IDs: 17.
- Present in frozen Zenodo `1st_layer.csv`: 0.
- Absent from frozen Zenodo `1st_layer.csv`: 17.
- Join: Table 2 ZTF `ID` string, crosswalked through authoritative Table 2 `Seq`.
- JSON SHA-256: `d8d8e3382450d85446988b70c1b65f82ddde1b4cb2da2c106391bf1ce6aee50a`.
- Table 2 input SHA-256 for this audit: `db1c5e547e5abf68733a79fd5ff3fbd6b835dfb2e7509be7897ce519ac8e647c`.
- Frozen Zenodo membership CSV SHA-256: `c235df101bf7a130b5dccdd95b786ac347f2b7ef24fc49ed7ae989aa8625437`.

The direct audit confirms that the 17 residual IDs are not members of the frozen reference. It does not establish why they were excluded.

The 17 have both mean magnitudes, a positive common period, and substantial Table 2 detection counts. Their missing per-band period is not explained by one uniform FAP state: 10 have `log(FAP)=0` in the band with the missing period, while 7 have a negative value. Do not claim that all 17 failed the same FAP threshold.

The audit also found that the Table 2 `recno` value differs from authoritative `Seq` for Seq 657950 and 732333. The crosswalk correctly uses ZTF name to `Seq`; it must not use `recno` as a replacement identifier.

The paper states that both bands are phase-folded using the common period and that mean colour `m_gr` is appended to the isolation-forest features. It does not explicitly require both `Per-g` and `Per-r` to be positive. Therefore the 17-object exclusion remains a scientific-method ambiguity. The next test must examine the authors' data-preparation or MGPR preprocessing behavior, or obtain author clarification. Do not add a per-band-period gate to the production selector based only on this exact set match.


## Candidate-only detection-count strata — 2026-11-02

The 11,602 historical candidate-only objects split into five mutually exclusive missing-field groups. Table 2 detection-count summaries are:

| Missing fields | Objects | Ng min / median / max | Nr min / median / max | Both Ng,Nr ≥ 11 |
|---|---:|---:|---:|---:|
| gmag + Per-g | 11,465 | 0 / 5 / 22 | 12 / 119 / 1,078 | 23 |
| rmag + Per-r | 115 | 35 / 46 / 198 | 0 / 8 / 722 | 1 |
| Per-g only | 10 | 51 / 105 / 171 | 50 / 122 / 187 | 10 |
| Per-r only | 7 | 62 / 149 / 245 | 63 / 150 / 204 | 7 |
| gmag only | 5 | 6 / 11 / 12 | 78 / 177 / 1,062 | 4 |

Most candidate-only objects have few detections in the band whose mean magnitude and per-band period are missing. This is consistent with insufficient or unsuccessful band-specific fitting. It is not proof of the authors' selection rule.

The 17 period-only residuals are different: they have substantial detection counts in both bands, positive mean magnitudes, and a positive common period. A simple `Ng/Nr >= 11` rule is not sufficient: 45 candidate-only objects satisfy that count condition. Do not add a detection-count threshold as a substitute for source evidence.


## Primary-paper selection wording — explicit reproducibility gap

The full arXiv text for Chan et al. (2022), [arXiv:2112.03306](https://arxiv.org/abs/2112.03306), Section II.1, states that the authors extract 730,184 of 781,602 objects because each selected light curve contains at least one 2.5σ g-band and one 3σ r-band detection. It then states that both bands are phase-folded using the **common period** from Chen et al. Table 2.

The stated selection paragraph does not specify:
- a minimum `Ng` or `Nr` count;
- positive Table 2 mean magnitudes `gmag` and `rmag`;
- positive band-specific periods `Per-g` and `Per-r`;
- a Table 2 complete-case filter.

Section III.3 says unphysical MGPR interpolations could not be completely eliminated and were manually checked to be below 0.01% of the sample. It does not say these objects were removed from the 730,184 sample.

This creates an explicit reproducibility gap: the published text describes the two-band SNR rule, but the historical reconstruction gives 741,786 candidates. The empirical four-field intersection is exact, but it is not a documented selection rule. The 17/MGPR connection remains a testable hypothesis only. Do not treat it as the cause of the 11,602 difference without direct MGPR evidence or author clarification.
