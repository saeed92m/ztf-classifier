# ZTF Classifier — v0.3 Architecture

> Status: Draft — Architecture Contract Phase
> Base release: v0.2.0
> Base commit: c1955676f9feeef10d480d8b8abd8452555c61d3
> Branch: feature/v0.3-architecture-contracts

## 1. Purpose

This document defines the target architecture and contract boundaries for ZTF Classifier v0.3 and later product development.

The v0.3 architecture extends the frozen v0.2 scientific baseline. It does not redefine, mutate, or weaken any frozen v0.2 scientific contract.

## 2. Frozen v0.2 Boundary

The following remain immutable compatibility contracts:

- frozen 15-class model taxonomy
- canonical v0.2 42-feature schema
- canonical v0.2 feature extraction semantics
- frozen v0.2 model configuration
- v0.2 model artifact format
- v0.2 provenance compatibility
- v0.2 benchmark dataset
- v0.2 historical evaluation protocol
- v0.2 reproducibility guarantees

New application-level contracts must wrap or adapt these interfaces rather than silently changing their semantics.

## 3. Target Architecture

The target system is organized as a layered scientific application:

```text
INPUT SOURCES
     |
Input Adapters
     |
Canonical Dataset
     |
Validation
     |
+----+------------------+
|                       |
Feature Engine     Data Analysis
|                       |
Model Inference    Analysis Results
|                       |
+----------+------------+
           |
       Provenance
           |
       Job / Storage
           |
          API
           |
    Web Workbench
```

The architecture separates scientific computation from transport, presentation, and persistence concerns.

## 4. Layering

### 4.1 Domain Layer

The domain layer owns canonical scientific data models, versioned contracts, result models, and the error taxonomy.

### 4.2 Application Layer

The application layer orchestrates ingestion, validation, analysis, inference, and jobs. It must not depend on HTTP or UI implementations.

### 4.3 Infrastructure Layer

The infrastructure layer provides dataset storage, raw observation storage, model artifact storage, model registry persistence, and job persistence.

### 4.4 API Layer

The API layer translates external requests into application contracts and application results into versioned transport responses.

### 4.5 Presentation Layer

The presentation layer contains the Web Workbench, reports, and future desktop clients. Scientific logic must remain outside this layer.

## 5. Domain Contracts

The following contracts define the stable boundaries between scientific and application components.

### 5.1 Canonical Observation Contract

A canonical observation represents one astronomical observation and must preserve the observational values and metadata required for downstream analysis.

The contract may include MJD, flux or magnitude, uncertainty, filter or band, quality information, coordinates, and source metadata.

### 5.2 Canonical Object Contract

A canonical object groups observations belonging to a single astronomical source and provides a stable object identifier together with object-level metadata.

### 5.3 Dataset Contract

A dataset is a versioned collection of canonical objects with explicit schema, provenance, validation status, and deterministic identity.

## 6. Validation Contract

Validation is an explicit application boundary between external or stored data and scientific processing.

Validation must distinguish structural validity, semantic validity, scientific suitability, and provenance validity.

Existing dataset and raw-data validators should be reused through application-level adapters rather than duplicated.

A validation result must identify the dataset or object being validated, the contract version, validation status, detected errors, and relevant diagnostics.

Validation failures must be deterministic and machine-readable so that API, batch, and user-interface layers can handle them consistently.

## 7. Feature Contract

The feature contract defines the feature schema consumed by scientific models and analysis components.

The frozen v0.2 feature contract remains authoritative for the baseline model:

- feature schema version: v0.2
- feature count: 42
- feature order is deterministic
- feature names are explicit and versioned
- feature extraction semantics remain unchanged

Production data may contain arbitrary numbers of astronomical objects, but model inference against the v0.2 baseline must continue to produce the exact canonical feature vector required by that model.

Future feature schemas must receive explicit versions and must not silently replace the v0.2 schema.

## 8. Inference Contract

The inference contract separates model execution from data ingestion, transport, and presentation.

Production inference accepts a validated dataset or canonical feature representation and returns a PredictionResult compatible with the frozen v0.2 model contract when the v0.2 artifact is selected.

The inference layer must preserve:

- model version and model family
- class ordering
- prediction row alignment
- probability matrices
- predicted class indices and labels
- optional calibration diagnostics
- optional conformal diagnostics
- optional out-of-distribution diagnostics

Inference must never silently substitute a different model, feature schema, class ordering, or preprocessing policy.

## 9. Prediction Contract

PredictionResult is the canonical application-level representation of model predictions.

The contract requires:

- a two-dimensional probability matrix aligned with source rows
- deterministic class ordering
- predicted class indices aligned with labels
- finite and valid probability values
- consistent sample counts across all diagnostics
- optional calibrated predictions
- optional conformal diagnostics
- optional OOD diagnostics

Prediction objects are immutable after construction. Downstream components must treat prediction alignment and class ordering as invariants.

## 10. Analysis Result Contract

An analysis result represents the combined scientific output for an astronomical object or dataset.

It may contain:

- canonical object metadata
- observational statistics
- light-curve analysis results
- feature values and feature quality indicators
- model predictions and probabilities
- scientific diagnostics
- provenance references
- analysis timestamp

Analysis results must be serializable into stable machine-readable formats and must retain references to the source dataset and model artifacts used to produce them.

## 11. Provenance Contract

Provenance is a first-class contract and must be preserved across ingestion, validation, analysis, inference, storage, and export.

Model-level provenance already exists in the v0.2 artifact system and remains backward compatible.

The v0.3 application layer must additionally preserve result-level provenance, including:

- source dataset identity and version
- source dataset content hash when available
- feature schema version and identity
- model artifact version and identity
- application and pipeline version
- Git commit when available
- analysis or inference timestamp
- runtime and dependency information when required for reproducibility

Provenance must be explicit rather than inferred from filenames, directory names, or mutable application state.

## 12. Job Contract

A job represents an executable unit of ingestion, validation, analysis, inference, or report generation.

A job must have a stable identifier, operation type, lifecycle state, creation time, and result or error reference.

The initial v0.3 implementation may execute jobs synchronously. The contract must not require a specific execution engine so that asynchronous workers can be introduced later without changing the external scientific semantics.

Recommended lifecycle states are:

- pending
- running
- succeeded
- failed
- cancelled

Job state transitions must be explicit and invalid transitions must be rejected.

## 13. Error Contract

Application errors must be categorized so that scientific failures, invalid inputs, infrastructure failures, and transport failures are distinguishable.

The v0.3 error taxonomy builds on the existing application error hierarchy.

At minimum, the system must distinguish:

- invalid input
- schema or contract violation
- validation failure
- feature extraction failure
- model or artifact failure
- inference failure
- provenance failure
- storage failure
- job failure
- unexpected internal failure

Errors exposed through the API must use stable machine-readable error codes while avoiding leakage of internal filesystem paths, credentials, or implementation details.

## 14. Model Registry Boundary

The model registry boundary provides a stable interface for discovering, validating, and selecting model artifacts.

The existing v0.2 model artifact format remains the compatibility source for baseline_v0.2.

The registry must treat model artifacts as immutable versioned objects.

Model selection must be explicit. A request must identify the model version or a clearly defined registry policy; the system must never silently replace a requested model with another version.

The registry boundary must expose sufficient metadata to validate model compatibility with the requested feature schema, class taxonomy, and inference contract.

The registry implementation may initially be filesystem-based. A database-backed or remote registry can be introduced later without changing the application-level contract.

## 15. Storage Boundary

Storage is an infrastructure concern and must remain replaceable from the application layer.

The architecture separates at least four storage categories:

- raw observational data
- processed datasets and feature artifacts
- model artifacts and registry metadata
- analysis results, reports, and job state

Storage interfaces must use stable identifiers and explicit version or content identity where applicable.

Scientific services must not depend directly on a particular filesystem layout, database engine, cloud provider, or object-storage implementation.

Storage failures must be translated into the application error contract without changing the underlying scientific semantics.

## 16. API Boundary

The API is an external transport boundary over the application layer.

The API must not contain scientific feature extraction, model logic, dataset construction, or provenance decisions that belong to the domain or application layers.

API responsibilities include:

- request validation and deserialization
- authentication and authorization enforcement at the boundary
- mapping requests to application contracts
- mapping application results to versioned responses
- stable error-code translation
- API versioning

The initial v0.3 implementation may define the API contracts before implementing an HTTP server.

Future HTTP implementations must preserve the application-layer contracts and must not make the scientific core depend on a specific web framework.

## 17. Security Boundary

Security controls are enforced at external boundaries and infrastructure interfaces.

The architecture must provide explicit boundaries for authentication, authorization, input validation, secret handling, filesystem access, and external service access.

Secrets must never be stored in source code, model artifacts, dataset artifacts, reports, logs, or API responses.

User-provided paths, identifiers, query parameters, and uploaded data must be validated before reaching filesystem or infrastructure operations.

Internal exception details, credentials, local filesystem paths, and infrastructure configuration must not be exposed through public API responses.

## 18. Test Strategy

Testing must preserve the scientific guarantees of v0.2 while validating the new production architecture.

The test strategy has four levels:

1. Unit tests for domain contracts and deterministic scientific utilities.
2. Integration tests for application services, storage adapters, model artifacts, and provenance.
3. Contract tests for API and serialization boundaries.
4. End-to-end tests covering ingestion through analysis, inference, and export.

Existing v0.2 scientific tests remain authoritative for frozen behavior.

New v0.3 tests must verify arbitrary dataset sizes, row alignment, contract validation, provenance propagation, deterministic errors, and compatibility with frozen v0.2 artifacts.

No v0.3 change may be considered complete without appropriate automated tests.

## 19. Versioning Policy

Scientific contracts, data schemas, model artifacts, API contracts, and serialized result formats are versioned independently when their compatibility requirements differ.

Breaking changes must receive an explicit new version and migration or compatibility strategy.

Non-breaking additions may be introduced within an existing version only when existing consumers remain valid.

The v0.2 scientific baseline is a permanent compatibility reference for the lifetime of the product unless a future release explicitly documents a deliberate compatibility boundary.

## 20. v0.3 Implementation Order

Implementation proceeds incrementally from contracts toward infrastructure and presentation:

1. Define and test canonical observation and object contracts.
2. Define dataset and validation adapters around existing validators.
3. Define analysis and result contracts.
4. Define provenance propagation across application services.
5. Define model registry interfaces around the existing artifact system.
6. Define storage interfaces and initial adapters.
7. Define job contracts and lifecycle handling.
8. Define API request and response contracts.
9. Implement the production API.
10. Add web workbench integration.

Each step follows the project workflow:

PLAN -> IMPLEMENT -> TEST -> VALIDATE -> DOCUMENT -> COMMIT

## 21. Architectural Invariants

The following invariants are mandatory:

1. v0.2.0 remains immutable.
2. The frozen v0.2 benchmark remains unchanged.
3. Existing v0.2 model artifacts remain readable.
4. The canonical v0.2 feature schema remains reproducible.
5. Production datasets are not limited to the 150-object benchmark.
6. Scientific logic remains independent of HTTP and UI frameworks.
7. Application services remain independent of presentation implementations.
8. Storage implementations remain replaceable.
9. Provenance is preserved across ingestion, analysis, inference, and export.
10. Prediction rows remain aligned with their source objects.
11. Contract changes are explicit and versioned.
12. Scientific semantics are never silently mutated.

## 22. Non-Goals

The following are outside the initial v0.3 architecture-contract phase:

- implementing FastAPI or another HTTP framework
- implementing the React Web Workbench
- database migrations or production database deployment
- authentication implementation
- asynchronous worker infrastructure
- desktop packaging
- introducing new machine-learning algorithms
- replacing the frozen v0.2 feature pipeline
- changing the frozen v0.2 model configuration
- changing the frozen v0.2 scientific benchmark

These capabilities may be implemented in later phases while conforming to the architecture and contracts defined here.
