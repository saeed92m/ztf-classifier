# CPVS Discrepancy — Scientific Status, 2026-10-25

**Status: UNRESOLVED (scientific) / PARTIALLY VERIFIED (engineering).**
The 11,602-object difference is now characterised exactly and its mechanism is
identified from primary sources. The equivalence between that mechanism and the
publisher's *documented* rule remains unproven, and one required input is not
reachable from this environment.

This document supersedes nothing. It records the current evidentiary state and
keeps every earlier claim that is still true, plus the reason any earlier claim
was narrowed. Three labels are used strictly:

- **VERIFIED FACT** — proven by a primary source, a reproducible run, or an
  arithmetic identity over published numbers.
- **HYPOTHESIS** — a plausible explanation consistent with the evidence, not
  proven.
- **UNKNOWN / BLOCKED** — the evidence or input needed does not exist here.

---

## 1. The question

Chen+ 2020 (`J/ApJS/249/18`) publishes 781,602 periodic variables. Chan+ 2022
(`J/ApJ/932/118`) use 730,184 of them. A reconstruction of the selection produces
741,786 candidates, of which 11,602 are absent from the published set and 0
published members are missing from the reconstruction.

Arithmetic constraint that any explanation must satisfy (**VERIFIED FACT**, by
definition of the reported partition):

    741,786 − 730,184 = 11,602   candidate-only
    730,184 − 741,786 < 0        published-only = 0

## 2. What the publisher actually wrote

**VERIFIED FACT** — verbatim from Chan+ 2022, §II.1, and repeated in the CDS
ReadMe for `J/ApJ/932/118` under "Description":

> We extract 730,184 out of 781,602 available periodic variable star light curves
> in the ZTF CPVS [] which contain at least one 2.5σ and 3σ detection in g- and
> r-band, respectively.

Immediately after, the same section states the light curves are phase-folded using
"their common period provided by Table 2" — a single period τ, not a separate
period per band.

**VERIFIED FACT** — therefore the documented rule is a *per-detection significance
threshold applied to the light curves*, evaluated per band. It is not a statement
about catalogue columns being positive.

## 3. What the predicate in use actually is

The reconstruction's discriminating predicate is

    gmag > 0 AND rmag > 0 AND Per-g > 0 AND Per-r > 0

**VERIFIED FACT** — from the CDS ReadMe for `J/ApJS/249/18`, these are exactly the
four nullable fields of `table2.dat`:

| Bytes | Format | Label | Range as printed | Nullable |
|---|---|---|---|---|
| 90-95 | F6.3 | `gmag` | `[11.7/22]?=0` | yes |
| 97-102 | F6.3 | `rmag` | `[11.2/21.4]?=0` | yes |
| 104-116 | F13.7 | `Per-g` | `[0.02/18340]?=0` | yes |
| 118-130 | F13.7 | `Per-r` | `[0.02/13242]?=0` | yes |

The `?=0` in CDS notation marks a nullable field whose null is encoded as `0`.
**(HYPOTHESIS, strongly supported)** The predicate is therefore the *null-exclusion*
predicate: "all four nullable astrometric/period fields are present". Reading it as
"positivity" is misleading; reading it as "presence" makes the mechanism
immediate, because an object with no measured mean magnitude or no measured
per-band period is one the publisher could not have used to build a phase-folded
light curve at all.

**VERIFIED FACT (arithmetic)** — this predicate reproduces the published count
exactly: 741,786 filtered by all four conditions leaves 730,184.

**UNKNOWN / BLOCKED** — that it *is* the publisher's rule. The paper states the
rule in terms of detection significance. No source retrieved here equates the two.

## 4. Reconstructing the reported findings, and reconciling them

Three separate findings were previously reported. They are not alternatives; two
are the same result at different granularity and the third is a different
measurement entirely.

### 4.1 "Finding A" vs the four-way partition — **VERIFIED, they agree**

| Source | Partition | Sum |
|---|---|---|
| Earlier finding (2-way) | 11,585 lack both a positive finite magnitude pair and a positive period pair; 17 remain | 11,602 |
| Issue #170 and the cycle record (4-way) | 11,580 fail both pairs; 17 have valid magnitudes but an incomplete period pair; 5 have valid periods but an incomplete `gmag`; 0 pass all four | 11,602 |

Arithmetic identity (**VERIFIED FACT**):

    11,580 + 5 = 11,585
    11,580 + 17 + 5 + 0 = 11,602

The 4-way partition *refines* the 2-way one. It does not contradict it. The
5-object group — valid `Per-g` and `Per-r` but a null `gmag` — is exactly the
part of the 11,585 that the 2-way grouping had merged into "lacks both".

The 4-way labels are the actual group names emitted by
`src/ztf_classifier/validation/cpvs_discrepancy_report.py` on PR #224:
`magnitude_and_period_pair_incomplete`, `valid_magnitudes_period_pair_incomplete`,
`valid_periods_gmag_incomplete`, `other_combination_review_required`. The
partition is therefore traceable to code, not only to prose.

**Also verified (arithmetic):** the companion claim that applying only the
magnitude pair leaves 17 candidate-only is consistent — `730,201 − 730,184 = 17`.

### 4.2 "Finding B" (SNR/flag counts) — **HYPOTHESIS, self-consistent, unverified**

Reported: all 11,602 have `g.snr_exact == r.snr_exact == true`; 10,887 have no
nonzero qualifying flag in either band, 171 in `g`, 680 in `r`.

**VERIFIED FACT (arithmetic):** those three categories cannot be disjoint, because
`10,887 + 171 + 680 = 11,738 > 11,602`. Inclusion–exclusion forces

    |nonzero in g AND r| = 171 + 680 − (11,602 − 10,887) = 136

so Finding B is internally consistent only if exactly **136** objects carry a
nonzero qualifying flag in both bands. That is a falsifiable prediction.

**UNKNOWN / BLOCKED:** it has not been checked against the artifact. The artifact
bytes are unreachable (§6). Finding B also does not address the same quantity as
§4.1 — one is about detection flags, the other about catalogue nullability — so
they are not competing explanations and must not be merged.

### 4.3 The two historical identifiers (194424, 195452) — **UNKNOWN**

Earlier work attributed a candidate-count change from 741,788 to 741,786 to
NaN-SNR handling in these two objects. Without object-level access their
contribution cannot be confirmed, and no code path here hard-codes them. They are
**not** an explanation for 11,602. A change of 2 cannot explain a difference of
11,602, and treating a small correction as the root cause would be a
miscount-to-count inference of exactly the kind this investigation forbids.

## 5. The identifier question, settled from the ReadMes

This is the one place where a documentary answer exists.

| Catalogue | File | Bytes | Label | Documented range | Documented meaning |
|---|---|---|---|---|---|
| Chen+ 2020 | `table2.dat` (781,602 rows) | 24-29 | `Seq` | `[1/781604]` | Internal source identifier |
| Chan+ 2022 | `table4.dat` (730,184 rows) | 24-29 | `ID` | `[1/781604]` | Catalog internal identifier |

**VERIFIED FACT:** the two columns occupy the same bytes, carry the same
documented range, and are described with the same role. `table4.dat` has 730,184
rows, so its `ID` cannot be a position within itself; it must reference the
parent catalogue. The two are one namespace, and this is the documentary
relationship that a ruling on the ID join requires.

**VERIFIED FACT:** the parent's `Seq` cannot be replaced by a row ordinal.
`table2.dat` holds 781,602 rows while `Seq` spans 781,604 values, so 2 values are
absent. From the first gap onward, row position is strictly less than `Seq` and
every later object would silently receive the wrong parent identifier.

**Consequence.** Both a name-based and an ID-based join are now *permitted*.
Neither is adopted alone: the audit resolves membership by normalized object name
(which fails closed on ambiguity) and, with `--crosscheck-published-ids`,
independently by the documented ID column, requiring the two to select the same
objects. Disagreement is an error, not a tie to be broken.

## 6. Artifact and provenance audit

| Item | Value | Status |
|---|---|---|
| Workflow run | 38635891449 | **VERIFIED** — conclusion success, event `pull_request`, head `d9c6ac4` |
| Artifact | `scientific-validation-heavy`, ID 11935357767, 34,104,786 bytes | **VERIFIED** — exists, not expired, created 2026-10-14T23:23:18Z |
| Revision reported for the artifact | `a5d3e27…` | **VERIFIED** — it is the ephemeral PR merge commit "Merge d9c6ac4 into c658853", hence on no branch |
| Artifact bytes | — | **BLOCKED** — download requires `*.blob.core.windows.net`, unreachable from this environment |
| `parent_metadata.tsv` SHA-256 `3675b127…` | — | **BLOCKED** — bytes unreachable; hash is recorded in issue #170 but appears nowhere in the repository |
| `selected.tsv` SHA-256 `699ff34b…` | — | **BLOCKED** — same |
| `selection_diagnostics.json` SHA-256 `7e763d88…` | — | **BLOCKED** — same |
| `membership_audit.json` SHA-256 `4c1a0825…` | — | **BLOCKED** — same |
| `cpvs_fixed_1000_sample_ids.json`, SHA-256 `94b4c966…` | — | **NOT PRESENT** — no such file exists in any branch of this repository |

The four hashes are quoted in issue #170 but are absent from the repository, so
they cannot be cross-checked against a committed manifest. The 1,000-object sample
file is not committed anywhere in the repository, in any branch. Neither fact
means the numbers are wrong; both mean they are **not verifiable from this
checkout**, and neither is reported as confirmed.

**Consequence for the reported claim.** Issue #170 derives its strongest statement
— that the 11,602 all fail at least one of the four fields, and that filtering
742k candidates by all four leaves exactly 730,184 — from these artifacts. That
derivation is internally consistent and arithmetically reconciled above, but it
**cannot be re-executed here**. It is reported as recorded, not as re-verified.

## 7. What the 11,602 are

**VERIFIED FACT:** every one of the 11,602 is an object present in the
reconstruction and absent from the published set, and — on the recorded partition
— each fails at least one of the four nullable catalogue fields.

**HYPOTHESIS (mechanism, strongly supported):** they are objects for which Chen+
2020 provides no usable measurement of mean `g` magnitude, mean `r` magnitude,
`g`-band period, or `r`-band period. Without those, a phase-folded two-band light
curve cannot be built, which is precisely what Chan+ 2022 needed. Under this
reading the reconstruction's predicate and the publisher's pipeline failure mode
coincide, which is why the count matches to the object.

**UNKNOWN:** whether the publisher applied null-exclusion, a detection-significance
cut, or some combination that happens to coincide on this sample. The paper
documents the second. Matching a count is not establishing a rule, and the
predicate must not be promoted to "the publisher's rule" on the strength of the
match.

## 8. What would settle it

The documented rule is computable and needs no new science — only the light-curve
files.

| Requirement | Why | Status |
|---|---|---|
| `ztf2g.dat` (89,697,393 rows, Lrecl 75) and `ztf2r.dat` (same) from `J/ApJS/249/18` | carry per-detection `Seq`, `MJD`, `mag`, `e_mag`, `Flag` — the only inputs from which "at least one 2.5σ g and 3σ r detection" can be computed per object | **BLOCKED** — host unreachable |
| `table4.dat` from `J/ApJ/932/118` | the published membership, needed for an object-level comparison rather than a count | **BLOCKED** — host unreachable |
| The retained artifact (ID 11935357767) | the recorded candidate-only list and parent metadata | **BLOCKED** — blob host unreachable |

With `ztf2g.dat` and `ztf2r.dat`, the decisive test is one query: for each `Seq`,
count detections with SNR ≥ 2.5 in `g` and ≥ 3 in `r`, keep objects with at least
one in each, and compare the resulting set against `table4.dat` by name **and** by
documented ID. Three outcomes are distinguishable and none requires a judgement
call:

1. the SNR rule reproduces 730,184 exactly → the documented rule is confirmed and
   the four-field predicate is an equivalent proxy on this dataset;
2. the SNR rule reproduces 730,184 as a set but the four-field predicate does not
   → the proxy is wrong and the discrepancy is a reconstruction defect;
3. the SNR rule does not reproduce 730,184 → the published set involved a further
   undocumented step, and the gap stays open with a new, narrower question.

## 9. Engineering status, kept separate

Engineering success is not scientific resolution and is recorded separately.

**VERIFIED:** the audit pipeline now fails closed rather than producing a
plausible-looking number from an unvalidated crosswalk. Fixed and regression-tested
in this branch: the ordinal-derived parent identifier, silent skipping of
malformed rows, no duplicate detection on either side, no rejection of a reused
`Seq`, an unreadable input returning an empty published set (which yielded
`published_only = 0` and mimicked a clean result), and a stale test that asserted
the defective ID-based membership.

**VERIFIED:** `Dependency Audit` failed for a real reason and is fixed —
`filelock` 4.0.3 carried CVE-2026-112940, CVE-2026-112913 and CVE-2026-112907,
`setuptools` 84.0.0 carried GHSA-xmj3-9gf7-h52w. Both raised to the fixed versions;
`pip_audit` goes from exit 1 with 4 advisories to exit 0.

**Not claimed:** that a green suite means the CPVS question is answered. It does
not. The scientific gate stays closed.

## 10. Conclusions

1. The difference is not a counting artefact and not a rounding error. It is
   11,602 specific objects, each failing at least one of four nullable catalogue
   fields. **VERIFIED FACT** on the recorded partition; not re-executed here.
2. Those four fields are exactly `table2.dat`'s nullable columns, so the predicate
   in use is null-exclusion. **VERIFIED FACT** from the ReadMe.
3. The published rule is a per-detection significance threshold, documented
   verbatim. **VERIFIED FACT** from the paper.
4. Null-exclusion reproducing the count is explainable and expected, because an
   object with null magnitude or period cannot supply a two-band light curve.
   **HYPOTHESIS**, not proof.
5. Therefore: the *membership* is reproducible; the *method* is not yet
   established. The honest status is **UNRESOLVED** with a named next test, not
   PASS and not "explained".
6. The blocker is access, not inference. One download of two public files turns
   §8 into a single computable comparison.
