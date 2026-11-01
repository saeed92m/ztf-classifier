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

This conjunction remains an empirical hypothesis. The paper does not state the four-field requirement. Per-object light-curve SNR diagnostics for the 55 controls are not in the retained historical artifact. The exact historical selector and the current-head fresh derivation remain unresolved. Do not change the production selector or scientific gate.


## Staged membership diagnostic — current derivation boundary

The historical candidate set C contains 741,786 objects. Applying both positive Table 2 mean magnitudes M leaves 730,201 objects, with 17 candidate-only residuals and zero reference-only IDs. All 17 have both mean magnitudes, but lack one band-specific period: 10 lack Per-g and 7 lack Per-r. Adding the two per-band period fields Q gives C ∩ M ∩ Q = P exactly (730,184).

The current derive_730k function implements the SNR and both-mean-magnitude conditions. It does not test Per-g or Per-r. On the archived diagnostics, that predicate leaves 17 extras and therefore reaches the existing fail-closed expected-count mismatch. Do not add the period-pair condition until the original published method supports it.

The five other residuals in the original 11,602 have both per-band periods but lack a mean magnitude; all five lack gmag. The 11,602 residual partition is therefore consistent with a staged metadata-completeness hypothesis, but it does not prove author intent.

The approximate magnitude-error SNR formula, the exact inverse magnitude-error transform, and 1/e_mag produced the same historical 741,786-object candidate set and 11,602 residuals. The tested SNR formula choice is not the cause. A zero-catalog-flag condition is also refuted as a substitute because it loses 5,472 reference members.

