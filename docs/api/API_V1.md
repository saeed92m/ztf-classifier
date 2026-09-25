# ZTF Classifier API v1

## Scope

This contract is part of the v1 Web/API foundation milestone.

The API is the HTTP adapter around the existing application inference service. It does not own scientific inference logic, model artifact loading rules, feature semantics, or provenance construction.

## Server configuration

The server reads:

- `ZTF_API_REGISTRY_DIR`: filesystem model registry visible to the server.
- `ZTF_API_DEFAULT_MODEL_VERSION`: optional default registered model.

Clients never submit arbitrary artifact or registry filesystem paths.

## Endpoints

| Method | Path | Purpose |
| --- | --- | --- |
| GET | `/health` | Liveness |
| GET | `/ready` | Model-registry readiness |
| GET | `/v1/model` | Default model metadata |
| POST | `/v1/predict` | Synchronous inference |
| POST | `/v1/batch` | Synchronous multi-row inference |

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
