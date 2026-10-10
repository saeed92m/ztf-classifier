# ZTF Classifier — Troubleshooting

## Installation problems

### Python version rejected

The v1.0.0 package supports Python 3.11 and requires:

```text
>=3.11,<3.12
```

Create a fresh Python 3.11 virtual environment rather than modifying an incompatible environment.

### Command not found

After activating the virtual environment, verify:

```bash
python -m pip show ztf-classifier
ztf-classifier --help
```

If the package is installed but the command is unavailable, verify that the virtual environment's `bin` directory is active.

## Input problems

### Input Parquet does not exist

The CLI fails closed when the input path does not exist. Check the path and file permissions before rerunning.

### Feature/schema errors

The production baseline requires the frozen v0.2 feature contract. Do not repair a schema mismatch by renaming columns or filling scientifically undefined features without an explicit, versioned preprocessing contract.

### Empty input or output

Empty scientific datasets are rejected by the production batch contract. Check the upstream acquisition/QC stage and retain its provenance and diagnostics.

## Model-selection problems

### Ambiguous model selection

Use exactly one mode:

```text
--artifact PATH
```

or:

```text
--registry-dir PATH --model-version baseline_v0.2
```

Do not combine them.

### Model version not found

For registry-backed inference, verify that the registry contains the requested version and that the server/CLI can read the configured registry directory.

Do not silently substitute another model version.

## Output problems

### Output file already exists

Batch inference intentionally refuses to overwrite an existing output. Choose a new output path or archive the previous result first.

### Unexpected diagnostics

Calibration, conformal prediction, and OOD are explicit diagnostic channels. Their availability/status fields must be read together with their values. Missing diagnostics are not permission to infer a scientific conclusion.

## API problems

### `/health` succeeds but `/ready` fails

This normally means the HTTP process is alive but the configured model registry is not ready. Check:

- `ZTF_API_REGISTRY_DIR`;
- `ZTF_API_DEFAULT_MODEL_VERSION`;
- registry readability;
- model-version availability.

### HTTP 401/403

If `ZTF_API_KEY` is configured, versioned `/v1/` endpoints require a bearer credential. Do not put the credential in source control, URLs, or logs.

### HTTP 404 for a scientific result

The result store is the canonical durable scientific-history boundary. A missing result means no durable result with that identifier is available; it does not mean a fresh analysis should be fabricated.

### HTTP 409 for a job result

A queued or running job does not yet have a canonical result. Poll the job state and retrieve the result after the job reaches `succeeded`.

## Scientific interpretation problems

### High OOD score

A high OOD score means the observation is unusual relative to the OOD reference distribution. It does not by itself establish an astrophysical anomaly.

### Low classification confidence

Low confidence indicates uncertainty in the classification output. It is not proof that the object belongs to a new astrophysical class.

### CPVS reproduction mismatch

The pre-fix source-backed run reported 741,787 candidates, including 11,604 candidate-only IDs. PR #173 corrected a real defect in which finite, non-zero magnitude qualification was not applied to the final g/r intersection. This correction is necessary but not sufficient: independent diagnostics that already applied finite/non-zero magnitude filtering reported 741,785 candidates. A full post-fix source-backed derivation and independent membership audit are still required; exact reconstruction remains UNRESOLVED under Issue #170. Do not hardcode IDs or tune thresholds to force the published count. This remains a claim-specific historical reconstruction boundary.

Do not tune thresholds merely to force the reconstructed count to 730,184.

## Data acquisition problems

The platform uses targeted/lazy source acquisition. A source or network failure should be reported as an acquisition/provenance failure, not replaced with fabricated observations.

When reporting an acquisition issue, retain the source, retrieval context, object identifier, error/failure code, and relevant cache state.

## Security

Production model artifacts can contain executable `joblib` payloads. Only load trusted artifacts and verify their manifest/checksum integrity. Never accept untrusted model artifacts in a public inference service.

## When filing a bug

Include:

1. software version;
2. Python version;
3. operating system;
4. exact command or API request;
5. model version;
6. input schema/version;
7. sanitized error output;
8. relevant provenance or request ID;
9. whether the issue is reproducible from a clean environment.

Never attach API keys or other secrets.


A separate audit-join defect was also identified: Table 4's internal ID was being compared directly with the parent catalog's row-ordinal SourceID. PR #176 changes the audit to map published ZTF object names to parent SourceIDs and adds regression tests. This is an audit-correctness fix, not proof that the remaining candidate-only population has been explained; wait for CI and fresh source-backed evidence.
