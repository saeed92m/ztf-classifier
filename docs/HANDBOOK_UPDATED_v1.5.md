# ZTF Classifier — Project Continuity Handbook v1.5

## 1. Canonical state

- Repository: `saeed92m/ztf-classifier`
- Default branch: `main`
- Current merged production baseline: `457b887b1a08ede4fdce3f2ca2e3ce6c2b3a47d8`
- Immutable scientific baseline: tag `v0.2.0`
- Python: 3.11.16
- Runtime: Ubuntu 26.04 LTS under WSL2
- Environment: pyenv + `.venv`
- Handbook v1.5 supersedes v1.4 for current project continuity.
- Software milestone `v0.4.0` is merged to `main` at `457b887b1a08ede4fdce3f2ca2e3ce6c2b3a47d8` and has been published as the official GitHub release `v0.4.0`.
- Current post-release `main` may contain continuity/documentation commits after the v0.4.0 merge; the v0.4.0 release target remains immutable.
- The project has now entered the Web/API product implementation phase.

## 2. Completed production path

The following production-facing capabilities are now implemented and merged:

- v0.3 domain/data architecture contracts
- ALeRCE object and detection acquisition
- historical-full-requery acquisition strategy
- canonical object manifest and provenance normalization
- deterministic 42-feature dataset construction
- reproducibility and dataset manifests
- model artifact schema 1.1
- calibration
- split-conformal diagnostics
- IsolationForest OOD diagnostics
- production single-object inference
- registry-backed model selection
- production batch inference
- explicit model-selection contract for CLI
- registry-backed predict E2E validation
- registry-backed batch E2E validation
- production validation hardening for external inputs and feature schemas
- CI dependency and workflow hardening

## 3. Verified benchmark and artifacts

Benchmark contract:

- 15 classes
- 10 objects per class
- 150 objects total
- 42 frozen model features
- deterministic OID ordering
- ALeRCE reference labels
- targeted ZTF light-curve retrieval

Verified production model artifact:

- model version: `baseline_v0.2`
- model family: XGBoost
- artifact schema: 1.1
- 42 features
- 15 classes
- temperature calibration
- conformal diagnostics at alpha 0.05, 0.1, 0.2
- IsolationForest OOD diagnostics
- persisted provenance
- persisted artifact manifest

## 4. Production model-selection contract

Production inference supports exactly one explicit model-selection mode:

1. direct artifact:
   `--artifact PATH`

or

2. registry selection:
   `--registry-dir PATH --model-version VERSION`

Supplying both modes is rejected as ambiguous.

Registry selection resolves the requested immutable artifact and preserves model/provenance identity through the application response and CLI outputs.

## 5. Production E2E validation

PR #11 validated the real production path, rather than a stubbed registry service.

Validated paths:

- registry -> artifact loader -> inference -> predict CLI -> JSON output
- registry -> artifact loader -> inference -> batch service -> batch CLI -> Parquet output

CI run #90 passed on the final PR #13 head before merge.

PR #11 merged as:

`375d7f0469a247f6a810ec2fd56029f9fe9b7768`

## 6. CI / validation policy

The main CI workflow currently performs:

1. Python 3.11.16 setup
2. editable installation with development dependencies
3. `pip check`
4. Ruff
5. full pytest suite
6. package import verification

The final PR #13 CI gate passed on run #90. Earlier full-suite counts are historical and are not treated as the current release result.

The six warnings are known third-party warnings documented in v1.1.

The full suite remains the release gate.

## 7. Scientific immutability

The `v0.2.0` tag is an immutable scientific baseline and must not be rewritten.

The newer production implementation does not silently redefine the historical training contract.

Generated datasets, caches, model runs, and local outputs remain separate from source-controlled code.

## 8. Engineering rules

For each remaining implementation slice:

1. inspect the existing contract and current main;
2. make the smallest coherent change;
3. add boundary tests;
4. run focused tests;
5. run the full suite at release checkpoints;
6. verify formatting and diff cleanliness;
7. push through a dedicated branch;
8. verify CI;
9. merge only after explicit approval;
10. record the resulting merge SHA.

Do not create repeated audits when implementation can proceed directly.

## 9. Release-readiness and v0.3.0 closeout

The core scientific and production inference path is implemented and PR #13 has been merged to `main` as `375d7f0469a247f6a810ec2fd56029f9fe9b7768`.

The `v0.3.0` package metadata and changelog are now part of `main`. The remaining release actions are verification/tag/publication steps, not model-pipeline reconstruction.

1. verify post-merge `main` CI and clean/reproducible installation;
2. perform final end-to-end release validation against the merged `main` state;
3. verify the immutable `v0.2.0` scientific baseline remains unchanged;
4. create/publish the `v0.3.0` tag and GitHub release metadata;
5. close the release gate and move to the application/API product layer.

No claim of final public release should be made until post-merge verification and the `v0.3.0` tag/release publication are complete.

## 10. Recovery and source of truth

GitHub `main`, immutable tag `v0.2.0`, and merged commit history are the primary source of truth for source code.

Scientific artifacts should have an external backup containing, as applicable:

- dataset artifacts
- raw/cache data
- model artifacts
- reports
- reproducibility manifests
- handbook and release metadata

Do not rely on an untracked local WSL directory as the only copy of a scientific artifact.


## 11. Product vision and data architecture

The project scope is now explicitly broader than a fixed benchmark classifier. The long-term product is an astronomical data analysis and discovery platform whose ML classifier is a core analysis engine.

The system must not require bundling large scientific source datasets into the Git repository. Scientific data is external to the source tree and may enter through:

1. user-provided datasets;
2. supported external scientific archives/APIs;
3. scheduled or continuous ingestion from supported sources.

Canonical flow:

user/external source -> ingestion -> validation/QC -> normalization -> feature extraction -> ML inference -> uncertainty/OOD -> cross-match/enrichment -> database -> report/catalog/API/web publication.

The ingestion layer must preserve source provenance, acquisition metadata, schema/version information, and enough lineage to reproduce or audit derived results.

The benchmark dataset remains a controlled validation asset, not the intended production data boundary.

## 12. Continuous analysis platform

The planned production system may operate continuously against supported online sources.

Required architectural capabilities for this phase include:

- incremental ingestion rather than repeated full reprocessing;
- source-specific connectors and rate/availability handling;
- deduplication and object identity resolution;
- quality-control gates before scientific inference;
- persistent analysis provenance;
- repeatable model-version selection;
- report generation;
- machine-readable catalog/export generation;
- database persistence of derived scientific results;
- retry/error handling for source and analysis jobs.

The architecture must separate raw/source data, normalized observations, derived features, model predictions, scientific reports, and publication/catalog records.

## 13. Public, catalog, and commercial data layer

The product may expose different access levels, for example:

- public/basic object information;
- detailed derived scientific results;
- bulk datasets;
- programmatic/API access;
- paid access to eligible derived datasets or analysis products.

Commercial publication or redistribution of external-source data is subject to the source's license, terms of use, attribution requirements, and applicable law. The product should therefore distinguish source-owned/raw material from analysis-derived products and retain licensing/provenance metadata.

A future commercial workflow is:

source data -> analysis/enrichment -> persisted derived record -> quality/review state -> catalog/report/API publication -> access control/billing -> authorized data delivery.

Payment and access control must never be treated as a substitute for scientific provenance or data licensing validation.

## 14. Product roadmap after v0.3.0

The implementation sequence is:

1. v0.3.0 release closeout;
2. v0.4.0 reproducibility/production-hardening release;
3. production Web/API layer around the existing inference engine;
4. ingestion/connectors for user-provided and supported external data;
5. persistent scientific database and job/analysis orchestration;
6. Web application for single-object, batch, report, catalog, and analysis workflows;
7. continuous/incremental source processing;
8. publication/catalog integrations;
9. commercial access, billing, entitlements, and secure data delivery;
10. production observability, security, deployment, and MLOps;
11. larger-scale scientific validation and ML v0.4+.

The database is not a prerequisite for the current local inference core, but it becomes a required product component once persistent analysis history, continuous ingestion, catalogs, or commercial delivery are implemented.

Large external datasets must remain outside Git. Repository size and application size are therefore intentionally decoupled from scientific-data volume.


## 15. v0.4.0 reproducibility and hardening closeout

The complete upgrade patch has been implemented on branch `chore/complete-upgrade-v0.4` without changing the immutable scientific baseline.

Implemented controls:

- canonical `requirements.lock` captured from the verified Python 3.11.16 Ubuntu CI environment;
- SHA-256 streaming utility for reproducibility;
- artifact manifest hash and additive software/dataset/feature/model provenance metadata;
- backward-compatible legacy artifact checksum warnings;
- independent calibration, conformal, and OOD diagnostic status fields;
- strict ALeRCE validation for MJD, filter, photometry, coordinates, duplicates, and corrected/raw fallback;
- structured ALeRCE ingestion diagnostics;
- additive CLI and batch provenance/status metadata;
- Data Card, Model Card, and feature provenance/leakage contract;
- security warning for trusted-only joblib model artifacts;
- CI gates for locked installation, pip check, Ruff lint, scoped Ruff format validation, full pytest coverage reporting, wheel build/install, import verification, and pip-audit.

### Executable validation

Final successful PR CI run:

- run #138
- commit: `80557eac1c8964409d3c45772efc8d644a9dfea6`
- 364 passed, 4 skipped, 6 warnings
- total coverage: 83%
- package build: passed
- wheel installation: passed
- package import: passed
- pip check: passed
- pip-audit: no known vulnerabilities reported

The pip-audit job explicitly notes that the local project package `ztf-classifier` is not published on PyPI and therefore cannot itself be audited by that service; third-party dependencies returned no known vulnerabilities.

The pre-change WSL2 baseline commands were not executable through the repository connector and are therefore recorded as NOT VERIFIED rather than fabricated.

### Compatibility

- scientific baseline `v0.2.0`: unchanged;
- dataset contract `benchmark_v0.2`: unchanged;
- frozen feature schema: v0.2 / 42 features;
- production model identity: `baseline_v0.2`;
- artifact schemas 1.0 and 1.1: retained;
- existing CLI fields: retained; new fields are additive.

### Release state

v0.4.0 is merged to `main` as `457b887b1a08ede4fdce3f2ca2e3ce6c2b3a47d8` after green CI and is published as the official `v0.4.0` release. The immutable `v0.2.0` tag must never be rewritten. The next implementation source of truth is the Web/API product layer.

## 16. v0.4.0 release publication and current source of truth

The `v0.4.0` release is published. Its release target is the merged hardening commit:

`457b887b1a08ede4fdce3f2ca2e3ce6c2b3a47d8`

The release is the reproducibility and production-hardening milestone. It must not be rewritten or retagged.

The current development branch for the next product slice is based on post-release `main`. Documentation must distinguish release targets from later continuity commits.

## 17. Web/API foundation — implementation contract

The Web/API layer is an adapter around the existing application/domain services. Scientific inference logic remains outside FastAPI.

Initial API surface:

- `GET /health` — process liveness;
- `GET /ready` — server readiness against the configured model registry;
- `GET /v1/model` — selected/default model metadata;
- `POST /v1/predict` — synchronous feature-row inference;
- `POST /v1/batch` — synchronous multi-row inference using the same stable prediction contract.

The HTTP client may select a registered `model_version`, but it may not submit arbitrary server filesystem paths. If no model version is supplied, the server may use the explicitly configured `ZTF_API_DEFAULT_MODEL_VERSION`.

Server-side model configuration:

- `ZTF_API_REGISTRY_DIR`
- `ZTF_API_DEFAULT_MODEL_VERSION`

The API response preserves model identity, diagnostic status, prediction probabilities, conformal diagnostics, OOD diagnostics, warnings, and provenance. Internal filesystem paths are not exposed.

Stable API errors use machine-readable codes rather than leaking internal exception text. Request-validation errors are separated from model-selection and inference failures.

## 18. Web/API dependency and reproducibility policy

The project retains a dedicated `web` optional dependency group. FastAPI and Uvicorn compatibility ranges are pinned in `pyproject.toml`, while the reproducible CI environment records the resolved web stack in `requirements.lock`.

The API implementation follows the current FastAPI error-handling model and remains suitable for deployment behind an ASGI server. The API is not itself the scientific domain layer.

## 19. Scientific Analysis Workbench UI/UX direction

The future web product is a Scientific Analysis Workbench rather than a generic administrative dashboard.

Planned primary surfaces:

- landing / project entry;
- analysis workbench;
- single-object analysis;
- light-curve viewer;
- observations and QC;
- feature explorer;
- periodicity analysis;
- classification and uncertainty;
- cross-match/enrichment;
- provenance;
- batch analysis;
- jobs;
- catalog;
- reports;
- advanced scientist controls;
- administration/operations.

Interaction design must support scientific inspection without hiding the high-level one-click workflow.

The visual identity is intentionally **not locked yet**. Color palette, typography, density, dark/light default, accent treatment, chart palette, and branding direction will be selected with the project owner before frontend implementation. Until then, UI code must avoid embedding irreversible visual assumptions into the API or domain contracts.

## 20. UI/UX design decision checkpoint

Recommended starting direction for discussion:

- dark scientific workstation as the primary mode;
- near-black/graphite structural surfaces;
- restrained electric-blue/cyan accent for interactive scientific states;
- neutral high-contrast typography;
- semantic colors reserved for status/alerts rather than branding;
- dense desktop analysis layout with responsive fallback;
- publication-quality plots and tables;
- clear distinction between raw observations, derived features, model output, uncertainty, and provenance.

Alternative directions remain open:

1. **Deep-space / observatory** — dark navy/black, blue-cyan accents, minimal glow;
2. **Scientific instrument** — graphite, neutral panels, restrained blue, data-first;
3. **Light research lab** — off-white, slate, blue accents, very high print/readability;
4. **Alpha Team signature** — white/blue brand language integrated with the scientific workbench.

No option is treated as final until the project owner chooses or asks for a custom visual system.

## 21. Next implementation sequence

The immediate implementation sequence is:

1. complete Web/API contract and boundary tests;
2. verify locked web dependencies and CI;
3. merge the Web/API foundation;
4. update this handbook with the merge SHA;
5. implement the Scientific Feature Engine with a unified feature contract;
6. add source/feature backends, including an adapter boundary for SCoPe-compatible workflows;
7. build persistent jobs/database orchestration;
8. implement the Scientific Analysis Workbench frontend against the stable API contracts.

Do not couple frontend design decisions to the internal Python application service layout.
