# Project Status & Execution Ledger — 2026-10-27

**Purpose:** current, evidence-based execution state. This file supersedes older status snapshots only where dates and evidence explicitly overlap; it does not erase historical records.

## Source revisions and workflow evidence

- Repository default branch `main`: `b56c90bafe9e6e0c5630dd4b96c9843dbd26301c` at time of this update.
- ALeRCE empty-response fix: [PR #231](https://github.com/saeed92m/ztf-classifier/pull/231), open, draft, unmerged.
- PR branch: `fix/alerce-empty-response-fallback-20261027`.
- PR head: `4a6ddd786ebb37551253349ef483ca968a8f00ac`.
- Base revision: `b56c90bafe9e6e0c5630dd4b96c9843dbd26301c`.
- Current-head [CI #40496914251](https://github.com/saeed92m/ztf-classifier/actions/runs/40496914251), [CodeQL #40496914236](https://github.com/saeed92m/ztf-classifier/actions/runs/40496914236), [Product Scope Audit #40496914533](https://github.com/saeed92m/ztf-classifier/actions/runs/40496914533), and [Scientific Validation #40496914362](https://github.com/saeed92m/ztf-classifier/actions/runs/40496914362) completed successfully.
- CI passed format, lint, lifecycle gate, test suite, runtime smoke, package build, dependency audit, and CI gate. CodeQL and Product Scope Audit passed.
- Scientific Validation is **not a full source-backed scientific pass**: the registry/lifecycle contract job passed, while these jobs were skipped by workflow conditions: immutable historical ALeRCE/CPVS reference verification; DR24/ALeRCE source-backed evidence; source provenance acquisition/scientific gate readiness; source-backed benchmark acquisition/derivation.
- PR #231 is not merged. Do not merge or claim complete scientific validation from these checks alone.

## Laboratory version

- A local lab artifact was reported at `runs/lab-smoke-20261027T104951Z/artifact`.
- Its manifest declares artifact schema `1.1`, model version `baseline_v0.2`, model family XGBoost, the frozen feature-set/dataset hashes, and source revision `a5fca3ac2f7b69b5469bd03c17bdc87ebecd9e69` (the lab artifact's recorded build commit; distinct from the current GitHub `main` base).
- The artifact is local diagnostic output, not a published release asset. The user's local uncommitted working-tree state is not observable from GitHub and remains subject to terminal verification.
- Local test output reported in the conversation: `tests/test_model_production_inference.py` — 9 passed, 7 skipped; two focused ALeRCE/backend modules — 7 passed. Exact skip reasons and the latest local diff are pending the user's terminal output. These are not new GitHub workflow results.

## ALeRCE evidence and outstanding work

- Live API probe recorded 30/30 successful query responses; at primary probability threshold 0.9, six classes returned an empty/no-column response; at 0.5 all 15 classes returned three rows. 72 object occurrences were unique, with no threshold violations in that probe.
- A separate 45-object diagnostic acquisition recorded 45/45 requested objects, successful acquisition/normalization/feature generation, and 42/42 features per object. Report SHA-256: `610326ab3e52dcf4eb3c2601ddde6444fcaae49210135269288ef21e51f3b194`; summary CSV SHA-256: `067c742293db5cd238c16b64f200f070e1bd754b1ec2deecc0986bfbcf4852e3`.
- This 45-object diagnostic does **not** independently prove the policy-level fallback experiment ran with explicit `fallback_on_empty`, nor that the requested selection policy reproducibly yields three objects per class.
- Next: execute the explicit `fallback_on_empty` selection configuration; persist the effective configuration, primary/fallback thresholds, per-class counts, selected object IDs, source/query timestamps, manifest, output dataset, and SHA-256 hashes. Inspect NaN versus ±Inf behavior and the string-serialized `normalization_diagnostics` field before treating the acquisition as production-quality evidence.

## Frozen scientific baseline and release

- Software release `v1.0.1` remains published and immutable.
- Scientific baseline `v0.2.0` remains immutable: 150 benchmark objects, 15 ALeRCE benchmark classes, 42 features in `final_feature_set_v0.2`, XGBoost `baseline_v0.2`, historical cutoff `59447.224132`, and schema 1.1 diagnostics.
- ALeRCE labels are benchmark labels, not independent ground truth. Live ALeRCE queries are operational/reference monitoring, not the frozen historical benchmark.
- Do not alter baseline artifacts, class order, features, thresholds, or acceptance criteria merely to satisfy a gate.

## CPVS discrepancy — SCIENTIFIC BLOCKER

The last recorded Seq-based reconstruction reported 781,602 parent IDs, 730,184 published IDs, 741,786 candidates, 11,602 candidate-only IDs, and zero published-only IDs. These are **previously recorded figures, not a fresh full-dataset rerun in this update**.

- The exact historical selection semantics remain unresolved.
- The four-field diagnostic predicate that matches the published cardinality remains diagnostic-only unless independent source evidence proves it is the historical publisher rule.
- Required evidence: verify source versions/hashes/schema; trace every candidate to original Table 2 `Seq` and source record; compare full object-level membership; run reproducible 100-object diagnostics and a fixed 1,000-object sample containing reference members and non-members; calculate explicit false positives/false negatives; record discrepant IDs, commands, provenance, and intermediate hashes; perform full comparison where feasible.
- Keep [Issue #170](https://github.com/saeed92m/ztf-classifier/issues/170) open until a reproducible root cause or evidence-based disposition exists. Do not tune thresholds to force cardinality equality.

## Application proposal files reviewed

Two attached Persian application documents were inspected as source materials: the 13-page Science & Technology Park presentation and the 21-page project proposal (version 1.0, September 2026). Both frame the deliverable as a demonstrable prototype and describe a planned end-to-end pipeline. They are proposal artifacts, not execution evidence. Before reissuing or replacing them, reconcile every present-tense claim about demo readiness, validation, performance, and reproducibility against the verified lab acceptance record. Preserve the original submitted PDFs; create a clearly versioned revision rather than silently overwriting them. No PDF was edited in this pass.

## Acceptance sequence

1. Inspect the local diff and run `pytest -rs`; classify every skipped test and confirm whether 1.1 artifact tests execute.
2. Complete the explicit ALeRCE fallback-policy acquisition and audit its manifest/data/hashes.
3. Push only reviewed local changes to PR #231; re-check workflows on the exact new head.
4. Continue CPVS source-level reproduction independently and fail closed on missing evidence.
5. After evidence is verified, align README, handbook, scientific/product roadmaps, model card, release notes, install/user guides, API/data contracts, and the Notion mirrors. Keep local experiment data out of Git unless a small, policy-compliant evidence manifest is intended.

## Scope and limitations

This ledger is a status/control document, not a claim that the product is release-ready. No main-branch merge, release publication, scientific baseline mutation, or production-data mutation is performed by this documentation change.
