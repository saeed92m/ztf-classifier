# Architectural Decisions Knowledge

| ID | Status | Decision | Evidence / rationale | Propagated to |
|---|---|---|---|---|
| AD-CI-001 | VERIFIED | Scientific validation is a permanent product-level gate. | Registry, executable gate, release fail-closed contract. | Release, roadmap, testing |
| AD-CI-002 | VERIFIED | Ground truth and independent reference agreement remain separate. | Manifest evaluation-role contract and regression tests. | Benchmarks, reports |
| AD-CI-003 | VERIFIED | External scientific datasets are not committed to Git. | Reproducibility and provenance contract. | Benchmark registry |
| AD-CI-004 | VERIFIED | Cumulative learning is a lifecycle control, not documentation-only. | Stage contract, ledger, knowledge layer, and executable validation. | All future stages |
| AD-CI-005 | VERIFIED | Local optimization cannot override scientific validity or release integrity. | Multi-objective quality vector and trade-off rules. | Model, feature, performance, release |
| AD-CI-006 | VERIFIED | Historical external-benchmark reconstruction is a claim-specific evidence scope and is not the product execution path. | CPVS 730k discrepancy analysis and PR #124 recovery architecture. | Scientific validation gate, roadmap, CI |


| AD-PROD-001 | ADOPTED | The product is a cross-platform Astronomical Data Analysis & Discovery Platform, not classifier-only. | Ecosystem review and existing platform architecture. | README, handbook, architecture, roadmap |
| AD-PROD-002 | ADOPTED | Desktop GUI is a product layer over stable scientific Core contracts; CLI/API remain supported. | Prevents GUI-driven scientific-core rewrites and preserves automation. | Architecture, packaging, UX |
| AD-PROD-003 | ADOPTED | Normal users must have self-contained installation on Windows/macOS/Linux without Python/pip/venv/Git/terminal. | User-path review and product usability requirement. | Packaging, release, installation |
| AD-PROD-004 | ADOPTED | Object/Source Explorer and provenance/evidence UI are first-class product capabilities. | Scientific discovery workflows require source-level inspection and reproducibility. | GUI, results, reports |
| AD-PROD-005 | ADOPTED | Cross-match, similar-object search, human review, discovery ranking, and Real/Bogus are explicit architectural boundaries. | Ecosystem review identified these as reusable patterns with clear scientific semantics. | Discovery architecture, analysis modes |
| AD-PROD-006 | ADOPTED | OOD, uncertainty, scientific anomaly, catalog evidence, and explainability remain separate evidence channels. | Prevents semantic overclaiming. | Result contracts, UI, validation |
| AD-PROD-007 | ADOPTED | Future alert/streaming support must be enabled by contracts without weakening deterministic offline/batch workflows. | Preserves reproducibility while allowing operational scaling. | Ingestion, orchestration |

## Decisions — product alignment round (2026-10-24)

Recorded during the alignment audit in `docs/PRODUCT_ALIGNMENT_2026-10-24.md`.
Each entry states the consequence so a later reader can see what it forces.

| ID | Status | Decision | Evidence / rationale | Consequence |
|---|---|---|---|---|
| AD-ALIGN-001 | ADOPTED | A cross-platform claim is only valid when a per-operating-system CI job exercises it. | Before this round all eight CI jobs ran on `ubuntu-latest` while `pyproject.toml` declared `Operating System :: POSIX :: Linux` only; no macOS or Windows job existed anywhere. | `ci.yml` gains a `cross-platform` matrix job wired into `CI Gate`. A platform that is not in the matrix is not a supported platform and must not be described as one. |
| AD-ALIGN-002 | ADOPTED | Documentation authority is encoded as a machine-checked map, not as convention. | 14 near-duplicate handbook files, 4 roadmap files, three filename/version mismatches, and a README that called an 87-line amendment the canonical handbook. | `docs/README.md` is the authority map; `tests/test_documentation_authority.py` fails when a document is unlisted, a canonical target is missing, the frozen handbook series grows, or a recorded defect changes silently. |
| AD-ALIGN-003 | ADOPTED | ZTF Classifier has no runtime dependency on Company-Platform or Supabase, and any future integration is one-directional and versioned. | Verified zero references to either system in code, configuration, workflows and documentation; Supabase account holds only projects belonging to other products. | `docs/contracts/PLATFORM_INTEGRATION_BOUNDARY_V1.md`. Company-Platform may call ZTF's `/v1` API; ZTF never calls out. A breaking change requires a new contract version and a decision record. |
| AD-ALIGN-004 | ADOPTED | `requirements.lock` is a Linux/x86-64 freeze, not a cross-platform lock. The portable installation path is `pyproject.toml`. | The lock pins `nvidia-nccl-cu12` (CUDA, Linux x86-64), `jeepney` and `SecretStorage` (Linux). `pip install -r requirements.lock` cannot succeed on macOS or Windows. | Documentation must not present the lock as cross-platform. Per-platform locks are required work before Windows/macOS can claim a hermetic install. |
| AD-ALIGN-005 | OPEN — BLOCKER | The packaging requirement in AD-PROD-003 (self-contained install with no Python, pip, venv, Git or terminal) is **not met**. | Releases attach only `ztf_classifier-1.0.1-py3-none-any.whl` and `ztf_classifier-1.0.1.tar.gz`. There is no installer, no bundled runtime, and the package is not on PyPI (verified HTTP 404). | Until an installer exists, the product is installable only by a user with a Python 3.11 toolchain. Describing it as an end-user desktop product would be an overclaim. Tracked as remaining work item 10 in `docs/PRODUCT_ALIGNMENT_2026-10-24.md`. |
| AD-ALIGN-006 | ADOPTED | Unreferenced artefacts are archived by `git mv`, never deleted. | Four root files had zero inbound references; they record provenance of past fixes. | `docs/archive/` preserves them with history; `tests/test_documentation_authority.py` asserts they are neither deleted nor returned to the root. |
