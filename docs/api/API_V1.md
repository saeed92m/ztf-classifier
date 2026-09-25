# ZTF Classifier API v1

## Scope

This contract is part of the v1 Web/API foundation milestone.

The API is the HTTP adapter around the existing application inference service. It does not own scientific inference logic, model artifact loading rules, feature semantics, or provenance construction.

## Server configuration

The server reads:

- `ZTF_API_REGISTRY_DIR`: filesystem model registry visible to the server.
- `ZTF_API_DEFAULT_MODEL_VERSION`: optional default registered model.
- `ZTF_API_KEY`: optional bearer credential protecting versioned `/v1/` endpoints when configured.

Clients never submit arbitrary artifact or registry filesystem paths.

## Endpoints

| Method | Path | Purpose |
| --- | --- | --- |
| GET | `/health` | Liveness |
| GET | `/ready` | Model-registry readiness |
| GET | `/v1/model` | Default model metadata |
| GET | `/v1/features/backends` | Registered scientific feature backend metadata |
| POST | `/v1/predict` | Synchronous inference |
| POST | `/v1/batch` | Synchronous multi-row inference |
| GET | `/v1/objects/{oid}` | Normalized object summary |
| GET | `/v1/objects/{oid}/observations` | Normalized observation stream |
| POST | `/v1/objects/{oid}/analysis` | Source-backed object analysis |
| POST | `/v1/objects/{oid}/jobs` | Durable analysis job submission |
| GET | `/v1/jobs` | Bounded durable analysis-job listing |
| GET | `/v1/jobs/{job_id}` | Durable analysis job state |
| GET | `/v1/jobs/{job_id}/result` | Canonical durable job result |
| GET | `/v1/results/{result_id}` | Durable result by stable ID |
| GET | `/v1/objects/{oid}/results/latest` | Latest durable result for an object |
| GET | `/v1/catalog/results` | Paginated scientific catalog query |
| GET | `/v1/catalog/results.csv` | Deterministic catalog CSV export |
| GET | `/v1/results/{result_id}/report` | Deterministic Markdown scientific report |

OpenAPI is generated directly by FastAPI from the versioned HTTP schemas.

## Prediction request

```json
{
  "model_version": "baseline_v0.2",
  "records": [
    {
      "oid": "ZTF17example",
      "feature_1": 0.123
    }
  ]
}
```

The production model currently requires its frozen feature schema. The HTTP boundary accepts row-oriented records and converts them to the application-layer DataFrame contract.

## Response guarantees

Responses preserve:

- selected model version and family;
- calibrated probabilities when available;
- conformal prediction-set diagnostics when available;
- OOD diagnostics when available;
- diagnostic availability/status;
- model provenance;
- warnings.

Internal filesystem paths are removed from public provenance responses.

## Error contract

Errors are JSON objects with:

- `code`: stable machine-readable identifier;
- `message`: safe human-readable message;
- `request_id`: echoed from `X-Request-ID` when supplied;
- `details`: structured validation details where applicable.

Initial error codes include:

- `model_not_configured`
- `model_registry_unavailable`
- `model_version_required`
- `model_not_found`
- `request_validation_failed`
- `empty_dataset`
- `inference_failed`
- `inference_result_invalid`

## UI/UX boundary

The future Scientific Analysis Workbench consumes this API contract. UI visual identity is intentionally not embedded here; typography, color system, density, chart styling, theme defaults, and branding remain presentation-layer decisions.


## Observation endpoints

- GET /v1/objects/{oid} returns an object summary derived from normalized observations.
- GET /v1/objects/{oid}/observations returns normalized ZTF photometry and acquisition provenance.

The endpoints use the existing ALeRCE acquisition adapter, Parquet cache, and strict light-curve normalization/QC contract. Observation responses preserve MJD, filter id, magnitude/error, corrected/raw photometry where available, coordinates, QC flags, and source provenance.

Server-side observation caching is configured with ZTF_API_OBSERVATION_CACHE_DIR. Clients cannot provide filesystem paths.


## Complete object analysis

- `POST /v1/objects/{oid}/analysis` runs the source-backed observation stream through the unified scientific feature engine and the explicitly selected registered production model.
- The response contains normalized observations, feature values and provenance, calibrated classification output, conformal/OOD diagnostics, model provenance, and source provenance.
- The model is selected by server-side registry version; clients cannot submit artifact filesystem paths.
- The workflow fails explicitly when observations cannot be acquired or validated; it does not fabricate scientific observations or features.


## Persistent analysis jobs

- `POST /v1/objects/{oid}/jobs` persists an analysis request and returns HTTP 202 with a durable job id.
- `GET /v1/jobs/{job_id}` returns the current durable state.
- The initial implementation uses SQLite and explicit states: `queued`, `running`, `succeeded`, and `failed`.
- Server configuration: `ZTF_API_JOB_STORE` selects the SQLite path; the default is `data/jobs/jobs.sqlite3`.
- Job persistence is deliberately separated from execution. A worker/orchestrator can claim queued jobs without changing the public API contract.

## Durable scientific results

Completed jobs persist their scientific payload through `ScientificResultStore`.

- `GET /v1/jobs/{job_id}/result` returns the canonical durable result for a completed job.
- `GET /v1/results/{result_id}` returns the same versioned result by stable result id.
- The result response includes `result_id`, `job_id`, object/survey/model metadata, schema version, creation time, and the persisted scientific payload.
- A queued or running job returns `job_result_not_ready` with HTTP 409.
- A missing result returns a stable 404 error.
- Server configuration: `ZTF_API_RESULT_STORE` selects the SQLite result database; the default is `data/results/results.sqlite3`.
- The job queue remains the lifecycle boundary; `ScientificResultStore` is the canonical scientific-history boundary.

### Latest durable object result

**GET** `/v1/objects/{oid}/results/latest?survey=ztf`

Returns the newest persisted scientific result for the object and survey. The endpoint reads only from the canonical `ScientificResultStore`; it does not execute inference. If no durable result exists, the API returns `404 scientific_result_not_found`.


## Scientific feature backend selection

Object-analysis and asynchronous job requests may provide:

- feature_backend: registered ScientificFeatureEngine backend name;
- feature_parameters: backend-specific deterministic parameters.

The default backend is native, preserving the frozen v0.2 42-feature contract. Backend selection is recorded in feature provenance and the durable result payload.


## Security boundary

When ZTF_API_KEY is configured, versioned API endpoints require Authorization: Bearer <key>. Liveness/readiness endpoints remain public for deployment probes. The API never returns the configured credential.

Every HTTP response receives an X-Request-ID. Clients may provide one; otherwise the server generates a UUID. The request ID is also included in stable API error envelopes.
