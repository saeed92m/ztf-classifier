# CPVS Discrepancy — Scientific Status, 2026-10-25

**Status: UNRESOLVED (scientific) / PARTIALLY VERIFIED (engineering).**
The 11,602-object difference is characterised arithmetically, but its mechanism
is **not** proven. The candidate mechanism (null-exclusion on four nullable
fields) is consistent with the documented counts and reproduces them
arithmetically; it has **not** been demonstrated on the primary data, because
`table2.dat`, `table4.dat`, `ztf2g.dat` and `ztf2r.dat` are not reachable from
this environment. An earlier revision of this document labelled two such
relationships VERIFIED FACT; both are downgraded below, with the reason.

This document supersedes nothing. It records the current evidentiary state and
keeps every earlier claim that is still true, plus the reason any earlier claim
was narrowed. Four labels are used strictly:

- **VERIFIED FACT** — proven by a primary source, a reproducible run, or an
  arithmetic identity over published numbers.
- **HYPOTHESIS** — a plausible explanation consistent with the evidence, not
  proven.
- **CORROBORATING** — evidence consistent with a conclusion that does not
  establish it. Specifically: agreement that cannot distinguish the conclusion
  from its alternatives.
- **UNKNOWN / BLOCKED** — the evidence or input needed does not exist here.

### Revision log

**Rev 3 (2026-10-25, commit `21faaf5` and later).** Added: Chan+ 2022's silence on
the sigma definition, the flag and per-exposure count (§2.1); Chen+ 2020's actual
photometry cut (§2.2); the commit/test-count/CI table with the missing green run
for `c7066a5` stated plainly (§9); the documented `catflags != 32768` policy
replacing the undocumented "flag = 0" assumption; and the parse-failure guard.

**Rev 2 (2026-10-25, commit `c7066a5`).** Two earlier labels are withdrawn:

- `table4.ID` = `table2.Seq` was labelled VERIFIED FACT. It is now
  **CORROBORATING** (§5.2). Same byte span, same printed range and the same role
  wording are evidence, not proof; no source states the equivalence. The two joins
  are therefore computed independently and compared, and the ID join is never a
  substitute for the name join.
- The four-way partition of the 11,602 was labelled VERIFIED FACT. It is now
  **REPORTED, NOT RE-EXECUTED** (§4.1, §7), because it derives from artifact bytes
  that are not retrievable here.
- The count match on null-exclusion is explicitly **not** treated as the cause
  (§3). A count match cannot distinguish mechanisms: any rule removing 11,602 of
  741,786 rows produces the same total. Only object identity separates them.
- Added: the publisher's own `SourceID` statement (§5.1), the SNR-definition
  finding (§8.1), the ready harness (§8.2), publisher checksums (§8.3), and the
  record of what was attempted against the real data (§9.1).

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

### 2.1 What Chan+ 2022 does *not* say

The full sentence was re-read from the arXiv HTML rather than from a summary. It
gives the two sigma values and nothing else. It does **not** say:

- how σ is computed — flux significance or magnitude divided by its error;
- whether any photometric flag was applied before counting detections;
- which exposures enter the count.

These are the three quantities that determine the answer, and the paper is silent
on all three. This is why §8.1 and §8.2 compute the alternatives instead of
picking one, and it is the direct answer to "settle the definition from the
paper's method": the paper does not contain that definition.

### 2.2 Chen+ 2020 *does* state the photometry cut

The parent-catalogue paper is more forthcoming. Chen+ 2020, §III, verbatim:

> Second, poor-quality images and photometry were excluded by adopting INFOBITS <
> 33,554,432 and catflags ≠ 32,768, respectively.

This is a specific bit value on the photometry flag, not "flag = 0". It corrects a
plausible but undocumented assumption: a reconstruction that discards every
nonzero flag is stricter than the published cut and would shrink the selected set
silently. The harness therefore carries three named policies — `none` (closest to
Chan+ 2022, which states no flag cut), `catflags_32768` (Chen's documented value),
and `any_nonzero` (undocumented, sensitivity check only).

### 2.3 The flag question is now resolved, and it retires a policy

The CDS ReadMe for `J/ApJS/249/18` gives the `Flag` column of `ztf2[gr].dat` as
bytes **72-75, I4, range `[0/4628]`**. That resolves the layout uncertainty in the
direction of the existing offsets — and it also settles the flag-policy question:

**Chen's documented cut cannot be applied to this file.** `catflags != 32768`
removes a value that lies outside the documented range, so it never occurs. The cut
is already reflected in the files (or the column is a post-mask value); either way,
re-applying it changes nothing. Shipping it as a distinct "documented" policy would
have implied a test that can never fail, so the `catflags_32768` policy was
**removed**, and a test now pins its absence.

What remains is honest:

| Policy | Status |
|---|---|
| `none` | closest to Chan+ 2022, which states no flag cut |
| `any_nonzero` | undocumented — sensitivity check only, labelled as such |

**UNKNOWN, and not approximated:** `INFOBITS < 33,554,432` is an image-level
bitmask present in none of the four files. It cannot be reproduced here.

**Documented and counted:** the ReadMe gives `e_mag` the range `[-0.005/0.4]`, so
negative uncertainties occur in the real data. They cannot produce a meaningful
significance under either SNR definition, so they are excluded from qualifying
detections while being counted separately as `nonpositive_error`. They are never
silently dropped.

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

**VERIFIED FACT (arithmetic only)** — the four conditions applied to 741,786
rows leave 730,184. This is arithmetic on published numbers, and it is all that
it is.

**NOT PROVEN — the count match is not an explanation.** Matching the published
total is a necessary condition, not a sufficient one. Three things remain: the
arithmetic was never run on the primary file, so it is not known that the 11,602
removed rows are *the same objects* the publisher removed; the partition has never
been re-executed against a hashed version of `table2.dat`; and the resulting set
has never been compared object-by-object with the published detection criterion
(2.5σ g / 3σ r). Until all three are done, the four-field predicate is a
**candidate mechanism**, not the cause.

A count match also cannot distinguish competing mechanisms: any rule that removes
11,602 of 741,786 rows reproduces the same total. Only object identity separates
them.

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

Arithmetic identity (**VERIFIED FACT** — the addition is certain; the
*provenance of the four numbers* is not, because they come from an artifact whose
bytes are not retrievable from here):

    11,580 + 5 = 11,585
    11,580 + 17 + 5 + 0 = 11,602

The distinction matters. That the two partitions are mutually consistent is an
arithmetic fact about the reported figures. That those figures are correct
descriptions of the real catalogue is an unverified claim about an artifact.
The partition is therefore **reported, not confirmed**, and §6 records why the
artifact could not be re-read.

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

## 5. The identifier question — what is documented and what is not

### 5.1 What the publisher states explicitly

The Zenodo record for the Chen+ 2020 light curves — the dataset cited in the
paper itself — describes its own key:

> "SourceID is the internal source identifier joins these attachments to Table 2.
> Example: For variable star ZTFJ000000.19+320847.2 in Table 2, the SourceID=3 is
> adopted to search corresponding single-exposure information in both 'ztf2g'
> and ''ztf2r'."

**VERIFIED FACT (publisher statement).** For `ztf2g`/`ztf2r`, the key that joins
photometry to `table2.dat` is `SourceID`, and it is `table2.Seq`. This settles
the photometry-to-parent join, which is the join the documented detection
criterion actually needs.

The worked example is worth recording for a second reason. `ZTFJ000000.19+320847.2`
encodes RA 00h00m00.19s — the minimum right ascension in the catalogue, so it is
plausibly the first row of `table2.dat`. The publisher assigns it `SourceID=3`,
not 1. **That is direct publisher evidence that `Seq` is not a row ordinal**,
independent of the gap-counting argument below. The row position of that object
is not stated in the record, so the example is strong but not itself conclusive;
the gap argument does not depend on it.

### 5.2 What is *not* established: `table4.ID` = `table2.Seq`

| Catalogue | File | Bytes | Label | Documented range | Documented meaning |
|---|---|---|---|---|---|
| Chen+ 2020 | `table2.dat` (781,602 rows) | 24-29 | `Seq` | `[1/781604]` | Internal source identifier |
| Chan+ 2022 | `table4.dat` (730,184 rows) | 24-29 | `ID` | `[1/781604]` | Catalog internal identifier |

These two columns share a byte span, a documented range, a role description and
a referenced catalogue. `table4.dat` has 730,184 rows, so its `ID` cannot be a
dense index within itself, and Chan+ 2022 Appendix F labels the column "Catalog
Internal Identifier".

**CORROBORATING, NOT PROVEN.** Each of those facts is *consistent with* the two
being one namespace. None of them *states* it. No retrieved source says in one
sentence that `table4.ID` is `table2.Seq`. An earlier revision of this document
called this VERIFIED FACT. That was wrong: identical byte position and a similar
integer range are evidence, not proof, and treating them as proof is exactly the
inference this project must not make. A confirmation requires either an explicit
statement of the identifier's meaning in the primary documentation, or a
real-data match of both joins.

**Consequence for the code.** The audit therefore resolves membership by
normalized object name — documented, and the primary route — and offers the
documented-ID join only as an independent cross-check (`--crosscheck-published-ids`),
requiring the two to select the same objects. Disagreement raises rather than
being resolved in favour of either. The ID route is never a substitute for the
name route.

### 5.3 What is proven about ordinals

**VERIFIED FACT.** `table2.dat` holds 781,602 rows while `Seq` spans 781,604
values, so 2 values are absent. From the first gap onward, row position is
strictly less than `Seq`, and every later object would silently receive the
wrong parent identifier. Ordinal-derived identifiers were used in an earlier
implementation and are unsound for this reason. The publisher example in §5.1
points the same way.

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

**REPORTED, NOT CONFIRMED:** every one of the 11,602 was recorded as an object
present in the reconstruction and absent from the published set, and — on the
recorded partition — as failing at least one of the four nullable catalogue
fields. This has not been re-executed object-by-object against a hashed copy of
`table2.dat`, so it remains a description of the earlier run rather than a fact
this document can certify.

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

### 8.1 The SNR definition is not documented, and the choice is decisive

"SNR ≥ 2.5σ" has two standard readings, and the source does not say which was
used. They are not equivalent:

| Detection | `f/σ_f = 1.0857/σ_m` SNR | shortcut `m/σ_m` | passes 2.5σ? |
|---|---|---|---|
| g=18.0, σ=0.10 | 10.86 | 180.0 | yes / yes |
| g=18.0, σ=0.30 | 3.62 | 60.0 | yes / yes |
| g=18.0, σ=0.50 | 2.17 | 36.0 | **no** / yes |
| g=20.0, σ=1.00 | 1.09 | 20.0 | **no** / yes |
| g=20.0, σ=7.00 | 0.16 | 2.86 | **no** / yes |

The first is magnitude independent by construction: `f ∝ 10^(-0.4m)` and
`σ_f ∝ f·σ_m·ln10/2.5`, so the magnitude cancels. The second scales with
magnitude, and since `e_mag` would have to exceed `m/2.5` — about 7 mag at r=18 —
for a real detection to fail, it is nearly vacuous. Under that reading the
criterion would select essentially all 781,602 objects rather than 730,184.

This is a genuine finding, not pedantry: the two readings are observations apart,
so a reproduction that does not state which was used is not reproducible, and a
result that happens to match under one reading does not validate the other. The
harness therefore computes **all** of them and refuses to pick a winner.

### 8.2 The harness that is ready for the data

`scripts/reconstruct_cpvs_from_photometry.py` implements the documented rule
without adopting any unproven premise. It parses all four files at the byte
offsets the ReadMes specify, evaluates both SNR definitions and both flag
policies, and reports, per route:

- SHA-256 and md5 of every input, plus row counts;
- both joins (normalized name, and documented ID) with an explicit
  `AGREE` / `DISAGREE` verdict;
- the full set difference against the published membership, with the size of each
  side, `produced_only`, `reference_only`, and object-level rows for every
  discrepancy (capped, with truncation counts stated);
- the null-exclusion route alongside, so the two mechanisms are compared on
  identity rather than on arithmetic.

It writes `cpvs_documented_rule_report.json` with `status: UNRESOLVED` and
`validated_on_real_data: false` baked in, so a report can never be mistaken for a
confirmation. `--manifest configs/cpvs/cpvs_input_acquisition.json` verifies the
publisher's md5 before analysis, and treats an input with no publisher checksum as
`NO_PUBLISHER_CHECKSUM` rather than as a pass.

25 tests cover it (`tests/test_cpvs_documented_rule.py`), including fixtures
written at the documented byte offsets, decoy detection for a shifted layout, and
the equal-count/different-membership case that a count-only check would wrongly
pass. **The tests prove the code does what it claims. They say nothing about the
real catalogues, because nothing here has been run on them.**

### 8.3 Publisher checksums, so the download can be verified

| File | Size | md5 (published on Zenodo 3886372) |
|---|---|---|
| `Table2.txt.zip` (contains `Table2.txt`, 175.1 MB) | 64.0 MB | `24dd4cf138a2687901d64b2d029cc624` |
| `ztf2g.zip` | 753.7 MB | `850fcef561dd7407fbe8e19e99100d7a` |
| `ztf2r.zip` | 881.5 MB | `daa7bc45c67579253eebe6b1c09dfbd9` |
| `Table6.txt.zip` | — | `fcad26b036c8dbee29f6d868fecc9697` |

`table4.dat` has no publisher checksum; its provenance rests on the CDS ReadMe for
`J/ApJ/932/118` and is recorded as unverifiable against a publisher value.

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

**VERIFIED:** `scripts/reconstruct_cpvs_from_photometry.py` and its tests are
committed as `c7066a5`, extended by `21faaf5`. The tests found a real defect in the
first version (`read_table4` returns a name→id mapping, which `build_report`
subtracted as if it were a set).

Test counts are quoted against a specific commit because a bare number is not
auditable. The following table is the only correct way to read them:

| Commit | Tests in `test_cpvs_documented_rule.py` | Suite result | CI run | CI conclusion |
|---|---|---|---|---|
| `c630701` | — | 606 passed, 4 skipped | 40182831760 | success (8/8) |
| `c7066a5` | 25 | 631 passed, 4 skipped | 40191856009 | **cancelled** — superseded by the next push, `concurrency: cancel-in-progress` |
| `21faaf5` | 30 | 636 passed, 4 skipped | 40192030836 | success (8/8) |

The 631 → 636 step is the five new document-guard tests added in `21faaf5`;
`git diff c7066a5..21faaf5 -- tests/` shows exactly those five functions. So the
two numbers are not in conflict — but the earlier report quoted 631 without
saying that **no green CI run exists for `c7066a5`**. Only `21faaf5` carries a
completed 8/8 run. That is a real reporting gap and it is corrected here.

The later commit also strengthens the parser against the defect that caused the
original false result: unparseable rows are now counted and reported per band, and
a wholesale parse failure (more than 1% of rows, at least 100) raises instead of
returning a small set that would look like agreement.

This is engineering evidence and nothing more.

**Not claimed:** that a green suite means the CPVS question is answered. It does
not. The scientific gate stays closed. A test suite over synthetic fixtures cannot
confirm anything about 781,602 real objects, and no number in this document should
be read as if it did.

### 9.1 What was actually attempted against the real data, and what refused

The blocker is stated precisely because "no data" is not a useful report:

| Attempt | Result |
|---|---|
| `curl` to `cdsarc.cds.unistra.fr`, `zenodo.org`, `vizier.u-strasbg.fr` | HTTP `000` — no connection |
| `curl` to `*.blob.core.windows.net` (Actions artifacts) | HTTP `000` |
| `curl` to `results-receiver.actions.githubusercontent.com` | HTTP `000` |
| `curl` to `api.github.com` | HTTP `200` |
| `fetch_page` on the Zenodo record page | works — text only (this is where §5.1 and §8.3 come from) |
| `fetch_page` on the Zenodo file preview | returns the filename and size, **no rows** |
| `gh api .../actions/artifacts/11935357767/zip` | `EOF`; the artifact is metadata-only here |

So: the documentary evidence in §5.1 and §8.3 is genuinely obtained, the data is
publicly available but unreachable, and no amount of further work in this
environment will produce a row-level comparison. That is an access limitation, and
it is **not** a reason to declare the four-field hypothesis correct.

## 10. Conclusions

1. The difference is not a counting artefact and not a rounding error. On the
   recorded partition it is 11,602 specific objects, each failing at least one of
   four nullable catalogue fields. **REPORTED, NOT RE-EXECUTED** — the artifact
   bytes are not retrievable from here, so this is not certified by this document.
2. Those four fields are exactly `table2.dat`'s nullable columns, so the predicate
   in use is null-exclusion. **VERIFIED FACT** from the ReadMe.
3. The published rule is a per-detection significance threshold, documented
   verbatim. **VERIFIED FACT** from the paper. **The two are not the same rule**,
   and nothing retrieved equates them.
4. Null-exclusion reproducing the count is explainable and expected, because an
   object with null magnitude or period cannot supply a two-band light curve.
   **HYPOTHESIS**, not proof.
5. Therefore: the *membership* is reproducible; the *method* is not yet
   established. The honest status is **UNRESOLVED** with a named next test, not
   PASS and not "explained".
6. The blocker is access, not inference. One download of two public files turns
   §8 into a single computable comparison.
