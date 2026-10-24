# ZTF Classifier — Documentation Index and Authority Map

This file is the **single entry point for documentation authority**. When two
documents disagree, the one named as *canonical* for that topic here wins. If a
topic is not listed, no document is authoritative and the topic is a
documentation gap.

Machine-checked by `tests/test_documentation_authority.py`. That test fails if a
document exists under `docs/` without being listed here, or if a canonical
document is missing.

## 1. Canonical document per topic

| Topic | Canonical document | Notes |
|---|---|---|
| Product identity, status, release state | [`../README.md`](../README.md) | Single source for the published software release and the immutable scientific baseline. |
| Installation | [`INSTALLATION.md`](INSTALLATION.md) | Includes the supported-platform matrix. |
| Quick start | [`QUICK_START.md`](QUICK_START.md) | |
| User workflows | [`USER_GUIDE.md`](USER_GUIDE.md) | |
| Troubleshooting | [`TROUBLESHOOTING.md`](TROUBLESHOOTING.md) | |
| Scientific method and claim boundaries | [`SCIENTIFIC_METHODOLOGY.md`](SCIENTIFIC_METHODOLOGY.md) | Claims must match the "Verified" vs "Unverified" vocabulary in [`knowledge/SCIENTIFIC_FINDINGS.md`](knowledge/SCIENTIFIC_FINDINGS.md). |
| Benchmark dataset | [`SCIENTIFIC_VALIDATION_BENCHMARK.md`](SCIENTIFIC_VALIDATION_BENCHMARK.md) + [`DATA_CARD.md`](DATA_CARD.md) | |
| Feature definition | [`FEATURE_PROVENANCE_CONTRACT.md`](FEATURE_PROVENANCE_CONTRACT.md) + [`SCIENTIFIC_FEATURE_ENGINE_v0.1.md`](SCIENTIFIC_FEATURE_ENGINE_v0.1.md) | |
| Model card | [`MODEL_CARD.md`](MODEL_CARD.md) | |
| API v1 surface | [`api/API_V1.md`](api/API_V1.md) | |
| Architecture and core boundary | [`architecture/APPLICATION_CORE_BOUNDARY.md`](architecture/APPLICATION_CORE_BOUNDARY.md), [`architecture/ARCHITECTURE_v0.3.md`](architecture/ARCHITECTURE_v0.3.md) | |
| Scientific validation architecture | [`architecture/SCIENTIFIC_VALIDATION_ARCHITECTURE.md`](architecture/SCIENTIFIC_VALIDATION_ARCHITECTURE.md) | |
| Architectural decisions log | [`knowledge/ARCHITECTURAL_DECISIONS.md`](knowledge/ARCHITECTURAL_DECISIONS.md) | Append-only decision record with rationale, date, version and consequence. |
| Failure and lessons record | [`knowledge/FAILURE_DATABASE.md`](knowledge/FAILURE_DATABASE.md) | |
| Known limitations | [`knowledge/DATA_QUALITY_FINDINGS.md`](knowledge/DATA_QUALITY_FINDINGS.md) | |
| Release policy | [`RELEASE_CUMULATIVE_IMPROVEMENT_POLICY.md`](RELEASE_CUMULATIVE_IMPROVEMENT_POLICY.md) | |
| Production acceptance | [`PRODUCTION_ACCEPTANCE_CHECKLIST.md`](PRODUCTION_ACCEPTANCE_CHECKLIST.md) | |
| Repository and branch hygiene | [`REPOSITORY_HYGIENE_POLICY.md`](REPOSITORY_HYGIENE_POLICY.md) | |
| Product alignment audit | [`PRODUCT_ALIGNMENT_2026-10-24.md`](PRODUCT_ALIGNMENT_2026-10-24.md) | Point-in-time audit. |
| Integration boundary with Company-Platform | [`contracts/PLATFORM_INTEGRATION_BOUNDARY_V1.md`](contracts/PLATFORM_INTEGRATION_BOUNDARY_V1.md) | Versioned contract. |
| CPVS selection-rule evidence | [`scientific_validation/CPVS_SELECTION_RULE_EVIDENCE.md`](scientific_validation/CPVS_SELECTION_RULE_EVIDENCE.md) | On `main` only after that work lands; until then this row is a declared gap. |

## 2. Continuity handbooks are historical snapshots

`docs/HANDBOOK_UPDATED_v*.md` are **historical point-in-time snapshots**, not
the current source of truth for anything. They are retained because releases and
Notion pages cite them.

Known defects in this series, recorded rather than silently fixed:

| File | Internal title says | Defect |
|---|---|---|
| `HANDBOOK_UPDATED_v1.3.md` | v1.4 | Filename/version mismatch |
| `HANDBOOK_UPDATED_v2.2.md` | v2.3 | Filename/version mismatch |
| `HANDBOOK_UPDATED_v2.3.md` | v2.3 | — |
| `HANDBOOK_UPDATED_v2.4.md` | v2.3 | Filename/version mismatch **and** stale content reissued under a new number |
| `HANDBOOK_UPDATED_v2.7.md` | v2.7 | 46 lines: an amendment, not a handbook |
| `HANDBOOK_UPDATED_v2.8.md` | v2.8 | 87 lines: an amendment, not a handbook |

`README.md` links `HANDBOOK_UPDATED_v2.8.md` as the "canonical continuity
handbook". That is inaccurate: v2.8 is an *amendment* layered on the last full
handbook, `HANDBOOK_UPDATED_v2.6.md`. Treat `README.md` §1 of this table as
authoritative for product state, and the handbook series as history.

**Rule:** do not add `HANDBOOK_UPDATED_v*.md`. Continuity updates belong in
`docs/knowledge/` or in a dated document under `docs/`. This is enforced by
`tests/test_documentation_authority.py`.

## 3. Roadmap authority

| File | Internal title says | Status |
|---|---|---|
| `roadmap/CUMULATIVE_LEARNING_ROADMAP_v2.4.md` | v2.4 | **Canonical** cumulative-learning roadmap |
| `roadmap/CUMULATIVE_LEARNING_ROADMAP_v2.3.md` | v2.3 | Superseded |
| `roadmap/CUMULATIVE_LEARNING_ROADMAP_v2.2.md` | v2.4 | Superseded; filename/version mismatch |
| `roadmap/CUMULATIVE_LEARNING_ROADMAP.md` | unversioned | Superseded |
| `roadmap/PLATFORM_EXPANSION_ROADMAP.md` | — | Canonical for product/platform expansion |
| `roadmap/SCIENTIFIC_VALIDATION_ROADMAP.md` | — | Canonical for scientific validation |

## 4. Archived material

`docs/archive/` holds files that were previously in the repository root and had
**zero** inbound references. They are preserved for provenance, not maintained.

| Archived file | Original location | Reason |
|---|---|---|
| `archive/P0_FIXES.patch.md` | `/P0_FIXES.patch` | Unreferenced patch artifact; superseded by merged code |
| `archive/ZTF_CLASSIFIER_COMPLETE_UPGRADE_PATCH.md` | `/` | Unreferenced historical plan |
| `archive/FINAL_SESSION_SUMMARY.md` | `/` | Unreferenced session log; its verified-fact table is duplicated in [`knowledge/SCIENTIFIC_FINDINGS.md`](knowledge/SCIENTIFIC_FINDINGS.md) |
| `archive/notebooks/01_environment_and_first_ztf_lightcurve.ipynb` | `/` | 3.1 MB unreferenced exploratory notebook |

## 5. Platform support status

The product vision targets **Windows, macOS and Ubuntu**. The verified state is:

| Platform | Verified install path | Evidence |
|---|---|---|
| Ubuntu (x86-64) | `requirements.lock` (hermetic freeze) | CI `Test Suite`, `Build & Verify Package` |
| Ubuntu (x86-64) | `pip install -e ".[dev]"` from `pyproject.toml` | CI `Cross-platform (ubuntu-latest)` |
| macOS (arm64) | `pip install -e ".[dev]"` from `pyproject.toml`, plus `brew install libomp` | CI `Cross-platform (macos-latest)` |
| Windows (x64) | `pip install -e ".[dev]"` from `pyproject.toml` | CI `Cross-platform (windows-latest)` |

**Status as of 2026-10-24:** all three operating systems install the package and
pass the full test suite. CI run
[`40104989502`](https://github.com/saeed92m/ztf-classifier/actions/runs/40104989502)
reported 11 of 11 jobs successful, including all three `Cross-platform` matrix
entries. Reaching that state required fixing six defects, each recorded in
[`PRODUCT_ALIGNMENT_2026-10-24.md`](PRODUCT_ALIGNMENT_2026-10-24.md) §2.1–§2.7:
a `dev` extra without an HTTP client, a test asserting a sandbox snapshot, a
setup-python patch pin that does not exist for macOS arm64 or Windows, a
POSIX-only `import resource`, OS-specific separators in provenance, and macOS
needing the OpenMP runtime.

Windows and macOS are verified through the **portable** install path only. The
hermetic `requirements.lock` path remains Linux/x86-64, so do not describe the
product as hermetically reproducible on macOS or Windows.

`requirements.lock` is a **Linux/x86-64 freeze**. It pins CUDA-only
(`nvidia-nccl-cu12`) and Linux-only (`jeepney`, `SecretStorage`) distributions
and therefore cannot be installed on macOS or Windows. Do not present it as a
cross-platform lock. Per-platform locks are tracked as remaining work in
[`PRODUCT_ALIGNMENT_2026-10-24.md`](PRODUCT_ALIGNMENT_2026-10-24.md).

## 6. External systems

| System | Status | Authority |
|---|---|---|
| Supabase | **Not used.** Two projects exist in the account, neither belongs to this project. | Issue #183: evaluation only, adoption not authorised. No schema, migration or credential is part of this repository. |
| Company-Platform (separate repository) | **No runtime dependency.** Optional future consumer via a versioned boundary contract. | [`contracts/PLATFORM_INTEGRATION_BOUNDARY_V1.md`](contracts/PLATFORM_INTEGRATION_BOUNDARY_V1.md) |
| Notion | Narrative handbook, roadmap and decision mirror. Not authoritative for code or contract facts. | This file wins on conflict. |

## 7. Complete document inventory

Every Markdown file under `docs/` is listed here. `tests/test_documentation_authority.py`
fails if a new file appears without being added to this inventory.

### 7.1 Root of `docs/`

| Document | Role |
|---|---|
| [`README.md`](README.md) | **This file** — documentation authority map |
| [`PRODUCT_ALIGNMENT_2026-10-24.md`](PRODUCT_ALIGNMENT_2026-10-24.md) | Point-in-time product alignment audit |
| [`INSTALLATION.md`](INSTALLATION.md) | Canonical installation |
| [`QUICK_START.md`](QUICK_START.md) | Canonical quick start |
| [`USER_GUIDE.md`](USER_GUIDE.md) | Canonical user workflows |
| [`TROUBLESHOOTING.md`](TROUBLESHOOTING.md) | Canonical troubleshooting |
| [`DATA_CARD.md`](DATA_CARD.md) | Dataset card |
| [`MODEL_CARD.md`](MODEL_CARD.md) | Model card |
| [`SCIENTIFIC_METHODOLOGY.md`](SCIENTIFIC_METHODOLOGY.md) | Canonical scientific method |
| [`SCIENTIFIC_VALIDATION_BENCHMARK.md`](SCIENTIFIC_VALIDATION_BENCHMARK.md) | Benchmark definition |
| [`SCIENTIFIC_VALIDATION_SOURCE_ADAPTERS.md`](SCIENTIFIC_VALIDATION_SOURCE_ADAPTERS.md) | Source adapter contracts |
| [`SCIENTIFIC_FEATURE_ENGINE_v0.1.md`](SCIENTIFIC_FEATURE_ENGINE_v0.1.md) | Feature engine specification |
| [`SCIENTIFIC_FEATURE_ENGINE_CUMULATIVE_POLICY.md`](SCIENTIFIC_FEATURE_ENGINE_CUMULATIVE_POLICY.md) | Feature-engine change policy |
| [`FEATURE_PROVENANCE_CONTRACT.md`](FEATURE_PROVENANCE_CONTRACT.md) | Feature provenance contract |
| [`RELEASE_CUMULATIVE_IMPROVEMENT_POLICY.md`](RELEASE_CUMULATIVE_IMPROVEMENT_POLICY.md) | Release policy |
| [`PRODUCTION_ACCEPTANCE_CHECKLIST.md`](PRODUCTION_ACCEPTANCE_CHECKLIST.md) | Production acceptance |
| [`TESTING_STRATEGY_CUMULATIVE_LEARNING.md`](TESTING_STRATEGY_CUMULATIVE_LEARNING.md) | Testing strategy |
| [`REPOSITORY_HYGIENE_POLICY.md`](REPOSITORY_HYGIENE_POLICY.md) | Branch/PR/release hygiene |
| [`ECOSYSTEM_REVIEW_PRODUCT_EXPANSION_2026-10-08.md`](ECOSYSTEM_REVIEW_PRODUCT_EXPANSION_2026-10-08.md) | Historical ecosystem review |
| [`ECOSYSTEM_GAP_MATRIX_2026-10-24.md`](ECOSYSTEM_GAP_MATRIX_2026-10-24.md) | Ecosystem gap matrix + licence corrections |
| [`HF_TOKEN_GUIDE.md`](HF_TOKEN_GUIDE.md) | Scoped read-only Hugging Face token guide |

### 7.2 `docs/architecture/`

| Document | Role |
|---|---|
| [`architecture/APPLICATION_CORE_BOUNDARY.md`](architecture/APPLICATION_CORE_BOUNDARY.md) | **Canonical** core boundary |
| [`architecture/ARCHITECTURE_v0.3.md`](architecture/ARCHITECTURE_v0.3.md) | **Canonical** architecture |
| [`architecture/SCIENTIFIC_VALIDATION_ARCHITECTURE.md`](architecture/SCIENTIFIC_VALIDATION_ARCHITECTURE.md) | **Canonical** validation architecture |
| [`architecture/V1_PRODUCT_ARCHITECTURE.md`](architecture/V1_PRODUCT_ARCHITECTURE.md) | v1 product architecture |
| [`architecture/CUMULATIVE_LEARNING_ARCHITECTURE.md`](architecture/CUMULATIVE_LEARNING_ARCHITECTURE.md) | Cumulative-learning architecture |
| [`architecture/DISCOVERY_PLATFORM_EXTENSIONS_v0.1.md`](architecture/DISCOVERY_PLATFORM_EXTENSIONS_v0.1.md) | Discovery platform extensions |

### 7.3 `docs/api/`

| Document | Role |
|---|---|
| [`api/API_V1.md`](api/API_V1.md) | **Canonical** API v1 surface |
| [`api/ANALYSIS_JOB_WORKER.md`](api/ANALYSIS_JOB_WORKER.md) | Durable job worker |
| [`api/INCREMENTAL_ANALYSIS.md`](api/INCREMENTAL_ANALYSIS.md) | Incremental analysis |
| [`api/SCIENTIFIC_CATALOG.md`](api/SCIENTIFIC_CATALOG.md) | Scientific catalog export |
| [`api/SCIENTIFIC_REPORTS.md`](api/SCIENTIFIC_REPORTS.md) | Scientific reports |
| [`api/SCIENTIFIC_RESULT_REPOSITORY.md`](api/SCIENTIFIC_RESULT_REPOSITORY.md) | Result repository |

### 7.4 `docs/knowledge/`

| Document | Role |
|---|---|
| [`knowledge/README.md`](knowledge/README.md) | Knowledge-base index |
| [`knowledge/ARCHITECTURAL_DECISIONS.md`](knowledge/ARCHITECTURAL_DECISIONS.md) | **Canonical** decision log |
| [`knowledge/FAILURE_DATABASE.md`](knowledge/FAILURE_DATABASE.md) | **Canonical** failure record |
| [`knowledge/DATA_QUALITY_FINDINGS.md`](knowledge/DATA_QUALITY_FINDINGS.md) | **Canonical** data-quality findings |
| [`knowledge/SCIENTIFIC_FINDINGS.md`](knowledge/SCIENTIFIC_FINDINGS.md) | **Canonical** verified/unverified scientific facts |
| [`knowledge/PROJECT_KNOWLEDGE_BASE.md`](knowledge/PROJECT_KNOWLEDGE_BASE.md) | Accumulated project knowledge |
| [`knowledge/CUMULATIVE_IMPROVEMENT_LEDGER.md`](knowledge/CUMULATIVE_IMPROVEMENT_LEDGER.md) | Improvement ledger |
| [`knowledge/BENCHMARK_LESSONS.md`](knowledge/BENCHMARK_LESSONS.md) | Benchmark lessons |
| [`knowledge/MODEL_FINDINGS.md`](knowledge/MODEL_FINDINGS.md) | Model findings |
| [`knowledge/PERFORMANCE_LESSONS.md`](knowledge/PERFORMANCE_LESSONS.md) | Performance lessons |
| [`knowledge/RELEASE_LESSONS.md`](knowledge/RELEASE_LESSONS.md) | Release lessons |
| [`knowledge/TESTING_LESSONS.md`](knowledge/TESTING_LESSONS.md) | Testing lessons |
| [`knowledge/ECOSYSTEM_GAP_ANALYSIS_2026-10-03.md`](knowledge/ECOSYSTEM_GAP_ANALYSIS_2026-10-03.md) | Historical ecosystem gap analysis |

### 7.5 `docs/roadmap/`

| Document | Role |
|---|---|
| [`roadmap/CUMULATIVE_LEARNING_ROADMAP_v2.4.md`](roadmap/CUMULATIVE_LEARNING_ROADMAP_v2.4.md) | **Canonical** cumulative-learning roadmap |
| [`roadmap/PLATFORM_EXPANSION_ROADMAP.md`](roadmap/PLATFORM_EXPANSION_ROADMAP.md) | **Canonical** platform expansion roadmap |
| [`roadmap/SCIENTIFIC_VALIDATION_ROADMAP.md`](roadmap/SCIENTIFIC_VALIDATION_ROADMAP.md) | **Canonical** validation roadmap |
| [`roadmap/V1_PRODUCT_SCOPE_AUDIT_20261005.md`](roadmap/V1_PRODUCT_SCOPE_AUDIT_20261005.md) | v1 scope audit |

### 7.6 Other directories

| Document | Role |
|---|---|
| [`contracts/PLATFORM_INTEGRATION_BOUNDARY_V1.md`](contracts/PLATFORM_INTEGRATION_BOUNDARY_V1.md) | **Canonical** Company-Platform boundary contract v1 |
| [`ui/SCIENTIFIC_WORKBENCH_UI_v0.1.md`](ui/SCIENTIFIC_WORKBENCH_UI_v0.1.md) | Workbench UI specification |
| [`integrations/scrapegraphai.md`](integrations/scrapegraphai.md) | ScrapeGraphAI probe notes |

### 7.7 Historical handbook series (frozen)

All 14 files, historical only, superseded:
[`HANDBOOK_UPDATED_v1.1.md`](HANDBOOK_UPDATED_v1.1.md),
[`HANDBOOK_UPDATED_v1.3.md`](HANDBOOK_UPDATED_v1.3.md),
[`HANDBOOK_UPDATED_v1.6.md`](HANDBOOK_UPDATED_v1.6.md),
[`HANDBOOK_UPDATED_v1.7.md`](HANDBOOK_UPDATED_v1.7.md),
[`HANDBOOK_UPDATED_v1.9.md`](HANDBOOK_UPDATED_v1.9.md),
[`HANDBOOK_UPDATED_v2.0.md`](HANDBOOK_UPDATED_v2.0.md),
[`HANDBOOK_UPDATED_v2.1.md`](HANDBOOK_UPDATED_v2.1.md),
[`HANDBOOK_UPDATED_v2.2.md`](HANDBOOK_UPDATED_v2.2.md),
[`HANDBOOK_UPDATED_v2.3.md`](HANDBOOK_UPDATED_v2.3.md),
[`HANDBOOK_UPDATED_v2.4.md`](HANDBOOK_UPDATED_v2.4.md),
[`HANDBOOK_UPDATED_v2.5.md`](HANDBOOK_UPDATED_v2.5.md),
[`HANDBOOK_UPDATED_v2.6.md`](HANDBOOK_UPDATED_v2.6.md),
[`HANDBOOK_UPDATED_v2.7.md`](HANDBOOK_UPDATED_v2.7.md),
[`HANDBOOK_UPDATED_v2.8.md`](HANDBOOK_UPDATED_v2.8.md)

### 7.8 Archive (`docs/archive/`, preserved, not maintained)

[`archive/P0_FIXES.patch.md`](archive/P0_FIXES.patch.md),
[`archive/ZTF_CLASSIFIER_COMPLETE_UPGRADE_PATCH.md`](archive/ZTF_CLASSIFIER_COMPLETE_UPGRADE_PATCH.md),
[`archive/FINAL_SESSION_SUMMARY.md`](archive/FINAL_SESSION_SUMMARY.md),
[`archive/notebooks/01_environment_and_first_ztf_lightcurve.ipynb`](archive/notebooks/01_environment_and_first_ztf_lightcurve.ipynb)
