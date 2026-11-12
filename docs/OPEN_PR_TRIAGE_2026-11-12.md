# Open Pull Request Triage — 2026-11-12

**Repository:** saeed92m/ztf-classifier  
**Snapshot:** 2026-11-12  
**Current main:** `f681408fae8d8062dd72ff74791872c1590f6ee8`  
**Method:** Read-only inspection of all open pull requests returned by GitHub at this snapshot. A PR being open or mergeable does not mean it is current, reviewed, validated, or safe to merge.

## Summary

GitHub returned **29 open PRs**. Many are historical, stacked on old branches, or duplicate work that later merged through a newer implementation chain. Do not mass-merge, mass-close, or delete branches. Preserve evidence until the owner-reviewed disposition is recorded.

## Active review queue

| PR | Topic | Snapshot status | Recommended action |
|---|---|---|---|
| #281 | Unified project baseline and documentation | Draft; current documentation branch; checks running | Complete current-head checks, review diff, then mark ready. Documentation-only; no scientific blockers closed. |
| #280 | v0.2 OOD sensitivity to missing features | Draft; based on older main snapshot; mergeable flag true | Rebase; review as diagnostic experiment only. Do not set production OOD thresholds from reconstructed artifacts. |
| #279 | Per-row data adequacy and OOD basis | Draft; based on older main snapshot; mergeable flag true | Rebase; review data adequacy and OOD semantics separately. No inference that data adequacy equals anomaly. |
| #266 | Park MVP delivery plan and acceptance gates | Draft; older base; mergeable flag true | Rebase and reconcile Persian Park addendum with current #158/#253 evidence. Retain only unique, current acceptance material. |
| #265 | CPVS Seq 615170/615172 archive identity | Draft; current research branch; mergeable flag true | Continue as bounded CPVS research. Preserve both IDs and raw provenance; do not infer identity from proximity alone. |
| #263 | Bounded BTS-to-DR24 recovery tooling | Open, non-draft; mergeable flag true; last updated Nov 3 | Review unique tooling and tests against merged DR24 adapter chain; decide whether to retain or supersede. |
| #268 | Bounded live DR24 payload probe | Draft; older main snapshot | Compare against current merged probe workflows and retain only unique reproducible evidence. |
| #269 | DR24 HATS payload evidence documentation | Draft; older main snapshot | Check whether current docs already contain its evidence; avoid duplicate status documents. |
| #270 | Live DR24 API payload parity | Draft; stacked on older feature branch | Compare with current API and live-source tests; rebase only if unique coverage remains. |
| #252 | CIN architecture and roadmap | Draft; mergeable false at snapshot | Keep as proposed architecture. Rebase after product critical path review; do not start runtime or public-scale collection. |

## Historical / stacked PRs requiring evidence extraction before disposition

| PR | Topic | Snapshot mergeable flag | Recommended action |
|---|---|---:|---|
| #247 | v1.0.1 guide and Nov 3 status sync | false | Likely superseded by current documentation convergence. Compare unique guide changes; do not merge stale status. |
| #240 | CPVS independent artifact recheck | false | Preserve research evidence; reconcile with current CPVS issue and artifact provenance. |
| #235 | CPVS non-finite SNR attribution audit | true | Review whether its diagnostic findings are already in #170/#180 and current reports. |
| #230 | CPVS report from authoritative Table 2 archive | false | Review source parser and output provenance; do not merge stale report generation blindly. |
| #229 | CPVS report name-crosswalk contract | true | Compare with current name-to-Seq evidence; retain contract if not duplicated. |
| #227 | Real DR24 lightcurves through feature engine | true | Preserve smoke evidence, but do not treat it as model compatibility or scientific acceptance. |
| #221 | Portable peak-memory diagnostics | true | Rebase and validate if the portability fix is not already in main. |
| #211 | Parallel independent validation and ecosystem audit | false | Extract unique audit requirements; rebase or supersede after review. |
| #206 | CPVS SNR handling and parent identity audit | false | Compare with merged fixes and current CPVS reports; preserve raw evidence. |
| #204 | CPVS residual membership parent scope | false | Stacked on diagnostic branch; do not merge as a standalone main PR. |
| #201 | CPVS residual epoch provenance | false | Extract row-level evidence into #170/#180; retain source hashes. |
| #199 | CPVS lifecycle record schema validation | true | Verify whether current lifecycle schema/gates supersede it; do not merge an old stack without rebase. |
| #189 | Auditable multi-source validation protocol | false | Retain useful requirements; reconcile with current scientific validation roadmap. |
| #187 | Ecosystem review handbook/roadmap sync | false | Historical documentation; compare unique findings with current master and archive if superseded. |
| #184 | CPVS row-level membership audit evidence | false | Preserve evidence; rebase only if current audit lacks it. |
| #182 | CPVS deterministic samples and full-vs-batch tooling | false | Preserve research tooling and historical sample manifests; no stale stack merge. |
| #179 | CPVS parent metadata candidate diagnosis | false | Historical stacked diagnostic; extract useful evidence to #170/#180. |
| #177 | CPVS extra-member diagnosis and artifact trim | false | Historical stacked diagnostic; preserve artifacts and methods, do not merge as a stack. |
| #176 | CPVS membership by ZTF name and heavy readiness | false | Historical stacked implementation; review against current Seq parser and fail-closed workflow. |

## Cross-cutting observations

1. Current product critical path remains Issues #158 and #253.
2. CPVS research remains under Issues #170 and #180; it is not a Park MVP gate.
3. AOIC remains a design tracker under Issue #249.
4. CIN remains proposed under Issue #251 and PR #252.
5. Artifact recovery is tracked in Issue #282.
6. Merged PRs #264, #273, #274, #275, #276 and #277 are the current DR24/Zubercal component chain; older PRs #267, #270, #271 and #272 must not be treated as the current delivery chain without comparison.
7. PR #281 is the current documentation convergence branch. It must not silently close any scientific or product acceptance issue.

## Required triage protocol

For each old PR, before any merge or closure:

- Compare its base and head with current main.
- Inspect the full diff and all review comments.
- Identify unique code, tests, data manifests and scientific evidence.
- Check whether that content already exists in a later merged PR.
- Re-run relevant tests on a current-main-based branch.
- Preserve the old PR URL and evidence in the canonical issue before closure.
- Close only after a documented disposition and owner review.

**No PR is merged or closed by this triage document.** It records a read-only snapshot and a safe order for future review.
