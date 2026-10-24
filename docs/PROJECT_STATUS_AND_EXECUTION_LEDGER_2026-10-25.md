# Project Status & Execution Ledger — 2026-10-25

## Purpose

This document is the dated, evidence-conscious coordination point for the ZTF Classifier project. It does not replace the immutable v0.2.0 scientific baseline, release notes, source manifests, or issue-level evidence. It distinguishes verified repository state from unresolved science and planned work.

## Verified repository state at review time

- Default branch: `main`, at `d88e54a2eb70d5e4531bc950341ef3136c29a5e2`.
- Current immutable software release documented by the repository: `v1.0.1`.
- Frozen scientific baseline: `v0.2.0`; production model: `baseline_v0.2`; preserve the 42-feature `final_feature_set_v0.2`, frozen class order, historical cutoff `59447.224132`, diagnostics schema 1.1, and fail-closed scientific gate.
- Security PR [#223](https://github.com/saeed92m/ztf-classifier/pull/223) is open and unmerged. Its latest recorded CI, Product Scope Audit, Scientific Validation workflow, and CodeQL runs succeeded. A successful workflow is not authorization to merge; inspect the current checks again before any merge.
- CPVS report PR [#224](https://github.com/saeed92m/ztf-classifier/pull/224) is open and draft. Its latest recorded CI failed at Dependency Audit while the base branch still had vulnerable dependency pins. The report implementation/tests are not equivalent to a generated, source-backed 11,602-row deliverable.
- [Issue #170](https://github.com/saeed92m/ztf-classifier/issues/170) remains the scientific membership-reconstruction blocker.
- [Issue #222](https://github.com/saeed92m/ztf-classifier/issues/222) defines a separate 100-object external benchmark using raw/source-level data and independent reference analyses.

## CPVS discrepancy: what is and is not established

The currently recorded full-set result is:

| Population | Recorded count |
|---|---:|
| CPVS Table 2 parent rows / source objects | 781,602 |
| Published Table 4 reference IDs | 730,184 |
| Seq-based reconstructed candidates | 741,786 |
| Shared IDs | 730,184 |
| Candidate-only IDs | 11,602 |
| Published-only IDs | 0 |

The recorded diagnostic partition of candidate-only IDs is 11,580 failing at least one condition in both the parent mean-magnitude pair and per-band-period pair; 17 with positive mean magnitudes but a missing/nonpositive period; and 5 with both periods but missing/nonpositive `gmag`. The four-field predicate (`gmag > 0`, `rmag > 0`, `Per-g > 0`, `Per-r > 0`) has been recorded as matching Table 4 membership exactly for the source-backed diagnostic artifacts.

**Interpretation boundary:** this establishes a reproducible diagnostic set relation for the recorded artifacts; it does not prove that the four-field predicate is the publisher's historical selection rule, nor that any candidate-only object is a new discovery. Keep Issue #170 open until the source versions, exact publisher semantics, provenance, and independent evidence are resolved. Re-verify artifact hashes, row/object counts, and command provenance before reusing these counts in a release or public scientific claim.

## Workstreams and acceptance criteria

### A. CPVS discrepancy report

1. Re-fetch and freeze the authoritative parent metadata, published Table 4 membership, and Seq-based candidate IDs; record source URLs, retrieval timestamps, row counts, schema, and SHA-256.
2. Run the report builder from PR #224 against those exact inputs. Confirm the CSV has exactly 11,602 unique candidate-only object IDs, every ID maps to an authoritative parent record, and the manifest hashes match the generated files.
3. Review every diagnostic reason; missing and invalid values must remain explicit, never imputed silently.
4. Generate HTML/CSV/Markdown/JSON outputs and verify internal count consistency and deterministic rebuild behavior.
5. Keep raw-light-curve review and external catalog cross-match as `NOT_ASSESSED` until their evidence is actually present.
6. Do not close Issue #170 merely because the report is generated.

### B. Independent 100-object validation

- Use 100 object-level cases, not 100 individual photometry rows.
- Capture source study/catalog/paper, DOI or URL, identifiers, coordinates, survey/instrument, bands, time window, license/access, retrieval time, source version, and SHA-256.
- Preserve raw data unchanged; store QC, normalized data, features, predictions, and references as separate versioned artifacts.
- Record independently reported class and quantitative analysis (period/parameters and uncertainties where applicable); a class label alone is insufficient for quantitative parity.
- Audit object-level and temporal leakage against training, feature selection, calibration, and threshold tuning before scoring.
- Pre-register metrics and comparison rules; report exact match separately from calibrated performance, uncertainty, abstention, and failure cases.
- Keep this benchmark distinct from the 150-object/15-class ALeRCE v0.2 benchmark and from CPVS membership reproduction. ALeRCE labels are benchmark labels, not independent ground truth.

### C. New ZTF inputs and identity/provenance tests

- Test at least one source-backed ZTF input outside the CPVS reconstruction, using documented object IDs and immutable input hashes.
- Verify the pipeline preserves authoritative source identifiers (including non-contiguous Seq values where applicable), does not substitute row ordinals, handles duplicates/missing values deterministically, and produces stable object-level outputs on rebuild.
- Distinguish a catalog-membership discrepancy from ML classification error and from a genuinely new/previously uncatalogued object.
- Do not extrapolate the CPVS discrepancy rate to unrelated ZTF datasets without measured evidence.

### D. Cross-platform experimental distribution

- Target operating systems: Windows, Ubuntu Linux, and macOS; target remains CPU-first.
- Repository metadata currently declares Python `>=3.11,<3.12`. Do not claim broader Python-version support without updating dependencies and passing the full supported matrix.
- Build a clean-machine matrix covering install, import, CLI/API startup, representative data ingestion, inference, export, and uninstall/reinstall. Record OS version, Python version, dependency lock, architecture, commands, and results.
- Produce platform-specific install instructions and artifacts only for environments actually tested. A source package or Linux CI pass alone does not establish a Windows/macOS installer.
- Preserve the core scientific engine and CLI/API independently of GUI; optional GUI must not fork scientific logic or mutate the frozen baseline.

### E. GUI / UI / UX

- Audit existing API and Workbench routes before building a second interface. The repository documents a FastAPI API and a `/workbench/` view; that is existing UI surface, not proof of a polished desktop GUI.
- Prioritize user journeys: select/import source data; validate schema/provenance; run analysis; inspect classification, confidence/uncertainty/OOD and abstention; inspect light curves/features; browse discrepancies; export a traceable report.
- Provide clear states for missing data, failed analysis, unsupported inputs, and unassessed scientific evidence.
- Add end-to-end UI tests and accessibility/usability checks before describing the GUI as ready for general users.

### F. Company-Platform integration

- Keep ZTF Classifier independently installable and usable. Company-Platform integration is an optional future integration, not a runtime dependency.
- Define a versioned API/export contract, authentication and least-privilege rules, job/result identifiers, provenance fields, error handling, and data-retention boundaries before connecting systems.
- Do not write production database rows or change database schemas until a concrete, versioned integration requirement and migration/test plan exist.

### G. Security, lifecycle and documentation

- Re-check PR #223's current CI and dependency audit; do not bypass the audit.
- Rebase/re-run PR #224 after the security dependency fix is accepted through the repository's normal review process; do not merge either PR automatically.
- Update README, handbook, roadmap, issue records, and release notes from verified evidence. Do not report workflow success as scientific validation when scientific jobs are skipped.
- Preserve raw scientific data outside Git unless explicitly approved and licensed. Store manifests and small provenance metadata, not large catalogs or credentials.
- Treat GitHub wiki and repository description updates separately from source-doc updates; do not claim they changed unless a write is verified.

## Current blockers

1. Exact historical CPVS selection semantics are not independently proven; Issue #170 remains open.
2. The actual 11,602-row report has not yet been verified as generated from the source-backed artifacts by the current report PR.
3. Raw light-curve inspection and a full external-catalog cross-match have not been established for all 11,602 objects.
4. The 100-object independent benchmark has a protocol issue but no verified completed evaluation results in this status record.
5. Windows/macOS clean-machine packaging and a user-ready GUI have not been verified by this review.
6. PR #223 and #224 remain unmerged at the time of this record.

## Next execution sequence

1. Verify current branch/PR/workflow state and security audit.
2. Use authoritative source-backed artifacts to generate and audit the CPVS report.
3. Re-run CPVS reporting CI on a base that contains the reviewed dependency remediation.
4. Execute the 100-object benchmark only after reference data, licenses, provenance, and leakage audit are ready.
5. Implement and test cross-platform packaging and GUI incrementally.
6. Define Company-Platform API integration after the independent product workflows are stable.

No scientific blocker is considered resolved solely by this document.
