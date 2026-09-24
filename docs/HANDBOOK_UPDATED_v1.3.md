# ZTF Classifier — Project Continuity Handbook v1.3

## 1. Canonical state

- Repository: `saeed92m/ztf-classifier`
- Default branch: `main`
- Current merged production baseline: `375d7f0469a247f6a810ec2fd56029f9fe9b7768`
- Immutable scientific baseline: tag `v0.2.0`
- Python: 3.11.16
- Runtime: Ubuntu 26.04 LTS under WSL2
- Environment: pyenv + `.venv`
- Handbook v1.3 supersedes v1.2 for current project continuity.
- Software milestone `v0.3.0` is merged to `main`; the GitHub release/tag operation remains a release-metadata step.

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
