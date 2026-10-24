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

In the retained metadata diagnostic, all 11,602 candidate-only objects fail at least one of gmag > 0, rmag > 0, Per-g > 0, and Per-r > 0. The diagnostic four-field predicate reduces the candidate set to 730,184 and matches the published membership set in that artifact. This is a strong correlation, not independent proof of author intent.

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
