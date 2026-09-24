# ZTF Classifier — Project Continuity Handbook v1.1

## 1. Current canonical state

- Repository: `saeed92m/ztf-classifier`
- Default branch: `main`
- Current merged baseline: `e66bedc52f4b6264431ebb1fec999a3c948de803`
- Immutable scientific baseline: tag `v0.2.0` at `c1955676f9feeef6d...`
- v0.2.0 must never be rewritten or amended.
- Python: 3.11.16
- Runtime: Ubuntu 26.04 LTS under WSL2
- Project environment: pyenv + `.venv`

## 2. Completed implementation

The v0.3 domain/data implementation path is merged into `main`.

Completed:
- v0.3 architecture contracts
- ALeRCE-backed object acquisition
- ALeRCE-backed detection acquisition
- historical-full-requery object selection strategy
- canonical object manifest and provenance normalization
- raw cache validation
- deterministic feature-dataset construction
- dataset artifact and reproducibility manifests
- production model artifact schema v1.1
- temperature calibration
- split-conformal diagnostics
- IsolationForest OOD diagnostics
- single-sample production inference
- batch production inference
- integration tests and full-suite validation

## 3. Verified benchmark

Configuration:
- 15 classes
- 10 objects per class
- primary probability threshold: 0.9
- fallback threshold: 0.5
- page size: 10
- strategy: `historical_full_requery`

Verified dataset:
- 150 objects
- 15 classes
- exactly 10 objects/class
- 42 frozen features
- 51 total columns
- deterministic OID ordering

Historical acquisition behavior:
- 15 primary availability queries
- 15 fallback acquisition queries
- total expected object API queries: 30

## 4. Model and inference state

Training remains tied to the frozen v0.2 training contract:
- training dataset shape: 150 × 56
- feature schema: 42 features
- 15 classes
- 5 folds, 30 rows/fold
- model family: XGBoost
- artifact schema: 1.1

Production artifact v1.1 contains:
- model
- model contract
- feature schema
- calibration
- conformal diagnostics
- OOD configuration
- OOD model
- provenance
- artifact manifest

Verified batch inference:
- 150 rows
- 150 unique OIDs
- 15 predicted classes
- 37 output columns

## 5. Validation baseline

Latest authoritative full-suite result before merge:
`353 passed, 6 warnings`

The six warnings are known third-party warnings:
- four Astropy Lomb-Scargle RuntimeWarnings
- two scikit-learn single-label confusion-matrix UserWarnings

Do not treat these known warnings as unexplained failures.

## 6. Engineering lessons from implementation

### 6.1 Establish the baseline before changing code
Always record:
1. current branch
2. current commit
3. remote branch state
4. working-tree status
5. immutable tags
6. latest test result

Never assume the local branch and remote base are synchronized.

### 6.2 Reconcile before merge
If a feature branch is behind `origin/main`, reconcile it first and rerun the full suite. Do not attempt to merge a dirty PR and discover conflicts at the final step.

### 6.3 Preserve both sides of a conflict
When resolving a conflict, inspect the semantic intent of both branches. In the v0.3 reconciliation, validation hardening from main and provenance enrichment from the feature branch were both required.

### 6.4 Separate immutable contracts from mutable caches
Raw caches may contain additional objects over time. Validation should distinguish:
- canonical objects required by the benchmark
- missing objects
- incomplete detection pairs
- schema errors
- mutable cache extras

Tests must not hard-code mutable cache counts unless the cache itself is an immutable artifact.

### 6.5 Validate at system boundaries
ALeRCE responses are external inputs. Normalize and validate:
- DataFrame type
- required columns
- OID validity
- probability validity
- classifier
- survey
- classifier version
- duplicate OIDs

Do not defer all validation to downstream builders.

### 6.6 Preserve provenance at acquisition time
The canonical manifest must retain source, label type, label probability, classifier version, and survey. Provenance should be derived from explicit configuration rather than inferred later.

### 6.7 Do not rebuild immutable scientific artifacts unnecessarily
The frozen v0.2 model-training inputs remain the training contract. The new 150-object benchmark dataset is an evaluation/inference artifact and must not silently replace the historical training dataset.

### 6.8 Prefer deterministic outputs
Sort by OID, freeze feature order, validate exact schemas, hash artifacts, and record reproducibility metadata. Determinism reduces debugging time and makes failures reproducible.

### 6.9 Avoid expensive full-suite runs during trivial edits
Use the shortest validation path that proves the change:
- syntax/import check
- focused unit tests
- targeted integration tests
- full suite only at meaningful checkpoints

The full suite remains the release gate.

### 6.10 Never use repeated audits as a substitute for implementation
Once the contract is sufficiently established, implement directly. Create a new audit only when a concrete uncertainty blocks implementation or release.

### 6.11 Treat generated artifacts separately from source
Generated datasets, model runs, caches, and temporary outputs should be ignored or stored in controlled artifact locations. Source commits should remain small and reviewable.

### 6.12 Merge only after explicit human approval
The merge step is a release boundary. Verify the exact PR head SHA immediately before merging and record the resulting merge SHA.

## 7. Recommended execution protocol from now on

For every implementation slice:

1. Read the existing contract.
2. Inspect current code and tests.
3. Make the smallest coherent change.
4. Run focused tests.
5. Run integration tests if boundaries changed.
6. Run full suite at checkpoint/release boundaries.
7. Check `git diff --check`.
8. Verify working-tree cleanliness.
9. Commit with one semantic purpose.
10. Push.
11. Merge only after explicit approval.
12. Record commit/merge SHA and validation result.

## 8. Current next phase

The v0.3 domain/data path is complete. The next work should focus on product completion rather than rebuilding completed contracts.

Priority order:
1. verify `main` locally against merged commit
2. establish the next product milestone from the existing architecture
3. implement the next production-facing capability
4. add tests at its boundaries
5. validate end-to-end
6. document the resulting contract
7. release through the same controlled Git workflow

## 9. Backup and recovery principle

GitHub `main`, immutable tag `v0.2.0`, and merged commit history are the primary source-of-truth for source code.

For local/generated scientific artifacts, maintain a separate external backup containing:
- dataset artifacts
- raw/cache data when legally and operationally appropriate
- model artifacts
- reports
- reproducibility manifests
- project handbook
- release metadata

Never rely on an untracked local WSL directory as the only copy of a scientific artifact.

