<!--
PREPARED, NOT POSTED.

This text was written as a comment for issue #170 but could not be posted: the
automation identity has read access to issues and pull requests in this
repository (gh issue view succeeds) but writing returns

    HTTP 403 "Resource not accessible by integration"

for both `gh issue comment` and the REST comments endpoint. The same applies to
editing the PR #224 description. Pushing branches works, so this is a
write-permission boundary specific to issues/PRs, not a general repository
problem.

To publish it, a maintainer can either post the body below verbatim, or grant the
integration Issues write permission. Nothing in this document should be treated
as having been delivered to issue #170.
-->

## Evidence update — 2026-10-25: primary sources retrieved; status stays UNRESOLVED

Branch `arena/5d244d9d-ztf-classifier` (HEAD `5abe6d6`). CI run [40181965764](https://github.com/saeed92m/ztf-classifier/actions/runs/40181965764) — 8/8 jobs successful, including `Dependency Audit`.

### 1. The publisher's rule, quoted rather than paraphrased

Chan+ 2022 §II.1, repeated in the CDS ReadMe for `J/ApJ/932/118` under "Description":

> We extract 730,184 out of 781,602 available periodic variable star light curves in the ZTF CPVS which contain at least one 2.5σ and 3σ detection in g- and r-band, respectively.

The same paragraph phase-folds using **"their common period provided by Table 2"** — one period τ, not one per band. This confirms the earlier reading that the documented rule is a per-detection significance threshold on the light curves, not a condition on catalogue-column positivity.

### 2. The predicate in use is null-exclusion, not "positivity"

From the `J/ApJS/249/18` ReadMe, `gmag` (90-95), `rmag` (97-102), `Per-g` (104-116) and `Per-r` (118-130) are exactly the four nullable fields of `table2.dat`, each printed `?=0`. In CDS notation that is the null marker.

So `gmag>0 AND rmag>0 AND Per-g>0 AND Per-r>0` is the **null-exclusion** predicate: all four nullable fields must be present. That supplies a mechanism for why it reproduces 730,184 — an object with a null mean magnitude or a null per-band period cannot supply the two-band phase-folded light curve Chan+ 2022 needed — rather than leaving the match as a coincidence.

It is still **not** the documented rule, and this comment does not promote it to one.

### 3. The reported partitions reconcile exactly

| Source | Partition | Sum |
|---|---|---|
| Earlier 2-way report | 11,585 + 17 | 11,602 |
| This issue / 4-way | 11,580 + 17 + 5 + 0 | 11,602 |

`11,580 + 5 = 11,585` — the 4-way *refines* the 2-way; they do not conflict. The 5-object group (valid `Per-g`/`Per-r`, null `gmag`) is the part the 2-way grouping had merged into "lacks both". The 4-way labels are the actual group names emitted by `src/ztf_classifier/validation/cpvs_discrepancy_report.py` (PR #224), so the partition traces to code.

Also consistent: `730,201 − 730,184 = 17` for the magnitude-pair-only variant.

### 4. The SNR/flag finding is self-consistent only under a testable prediction

`10,887 + 171 + 680 = 11,738 > 11,602`, so those three categories cannot be disjoint. Inclusion–exclusion forces **|nonzero flag in g AND r| = 136**. Finding B therefore predicts exactly 136 objects with a nonzero qualifying flag in both bands. Unverified — the artifact bytes are unreachable from this environment. This finding measures detection flags, not catalogue nullability, so it is **not** merged with §3.

### 5. Identifier question settled from the ReadMes

| Catalogue | File | Bytes | Label | Range | Meaning |
|---|---|---|---|---|---|
| Chen+ 2020 | `table2.dat` (781,602 rows) | 24-29 | `Seq` | `[1/781604]` | Internal source identifier |
| Chan+ 2022 | `table4.dat` (730,184 rows) | 24-29 | `ID` | `[1/781604]` | Catalog internal identifier |

Same bytes, same range, same role. `table4.dat` has 730,184 rows, so its `ID` cannot be a position within itself; it must reference the parent. The two are one namespace — this is the documentary relationship a ruling on the ID join requires.

Independently confirmed: the parent `Seq` cannot be replaced by a row ordinal, because 781,602 rows span 781,604 `Seq` values, so 2 values are absent and every object after the first gap would silently get the wrong parent.

Consequently the audit now resolves membership **by name** and, with `--crosscheck-published-ids`, **independently by the documented ID column**, and requires the two to agree. Disagreement aborts without reporting a count.

### 6. Artifact audit — what is and is not verified

| Item | Status |
|---|---|
| Run 38635891449 | **VERIFIED** — success, `pull_request`, head `d9c6ac4` |
| Artifact 11935357767 (34,104,786 B) | **VERIFIED** — exists, not expired, created 2026-10-14T23:23:18Z |
| Revision `a5d3e27…` | **VERIFIED** — the ephemeral PR merge commit "Merge d9c6ac4 into c658853", hence on no branch |
| The four SHA-256 values quoted in this issue's first comment | **BLOCKED** — artifact bytes need `*.blob.core.windows.net`, unreachable here; the hashes appear nowhere in the repository |
| `cpvs_fixed_1000_sample_ids.json` (SHA-256 `94b4c966…`) | **NOT PRESENT** — no such file in any branch |

This means the derivation recorded in the opening comment **cannot be re-executed from this checkout**. It is not contradicted; it is unre-verified, and this comment does not claim otherwise.

### 7. Rejected attribution

Objects `194424` and `195452` are not used to explain the difference. A change of 2 cannot account for 11,602, and no code path here hard-codes either identifier. Kept as UNKNOWN.

### 8. The decisive test and exactly what it needs

With `ztf2g.dat` and `ztf2r.dat` (89,697,393 rows each, Lrecl 75, columns `Seq`, `MJD`, `mag`, `e_mag`, `Flag`), count per `Seq` the detections with SNR ≥ 2.5 in `g` and ≥ 3 in `r`, keep objects with at least one in each band, then compare that set to `table4.dat` by name **and** by documented ID. Three outcomes, all decidable without judgment:

1. reproduces 730,184 exactly → documented rule confirmed; the four-field predicate is an equivalent proxy on this dataset;
2. reproduces it as a set but the predicate does not → the proxy is wrong and the difference is a reconstruction defect;
3. does not reproduce 730,184 → a further undocumented step existed, and the gap stays open with a narrower question.

**Blocker is access, not inference.** One download of two public files turns this into a single computable comparison. From this environment `cdsarc.cds.unistra.fr` and the Actions blob host are both unreachable.

### 9. Engineering fixed in the same branch (kept separate from the science)

- Fixed-width Table 2 fallback no longer derives the parent ID from row ordinal; it reads `Seq` from columns 24-29 and refuses the file on layout mismatch.
- Duplicate normalized names, duplicate `Seq`, malformed short rows and empty parent files now raise instead of being skipped; a short row previously vanished silently.
- An unreadable/unparseable published file previously returned an empty set, which made `published_only = 0` and mimicked a clean result. It now fails.
- Exit codes are distinct: 1 = could not evaluate, 2 = evaluated and the sets differ.
- Stale `test_read_vizier_accepts_commented_tsv_header` repaired: it asserted `{1, 730184}` internal IDs, i.e. it encoded the very defect the join-key correction removed. It now asserts normalized names.
- `filelock` 4.0.3 → 4.2.1 (CVE-2026-112940, -112913, -112907) and `setuptools` 84.0.0 → 84.1.0 (GHSA-xmj3-9gf7-h52w). Reproduced then fixed: `pip_audit` exit 1 with 4 advisories → exit 0.

Suite: 606 passed, 4 skipped. The 4 skips are missing-artifact guards (`data/raw/alerce` cache and `runs/model_baseline_v0.2_production/artifact` are absent from the checkout), not auto-passes.

**Status: UNRESOLVED.** Membership is reproducible; the method is not established. Scientific gate stays closed. No threshold, SNR definition, selection rule, baseline, model, tag or release was changed.
