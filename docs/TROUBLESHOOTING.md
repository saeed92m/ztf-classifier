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

The prior run reported 741,787 candidates, but its membership metrics must not be trusted: the audit converted published object names to physical row ordinals, while CPVS lightcurve `SourceID` is Table2's documented `Seq` identifier (bytes 24–29). The 725,101 intersection, 16,686 candidate-only and 5,083 published-only figures in run [#38095650470](https://github.com/saeed92m/ztf-classifier/actions/runs/38095650470) are invalid because the identifiers are not in the same namespace. PR #176 corrects both the parent source-ID universe and audit mapping to use Seq; rerun source-backed validation before interpreting new counts. Source: https://cdsarc.cds.unistra.fr/viz-bin/ReadMe/J/ApJS/249/18?format=html&tex=true

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


A separate audit-join defect was also identified: Table 4's internal ID was being compared directly with the parent catalog's row-ordinal SourceID. PR #176 changes the audit to map published ZTF object names to parent SourceIDs and adds regression tests. This is an audit-correctness fix, not proof of the size or cause of any remaining candidate-only population; wait for CI and fresh source-backed evidence.


**Audit status update (2026-10-11):** Run [#38092797735](https://github.com/saeed92m/ztf-classifier/actions/runs/38092797735) had an invalid zero-row parse. The parser was hardened, but source-schema review exposed a second defect: published names were mapped to parent row ordinals rather than the documented `Seq` / lightcurve `SourceID` values. Consequently, the 725,101 / 16,686 / 5,083 counts in [run #38095650470](https://github.com/saeed92m/ztf-classifier/actions/runs/38095650470) do **not** establish a valid mismatch and are superseded. PR #176 now reads official Seq identifiers in derivation and audit. Keep Issue #170 open until fresh heavy evidence resolves or accurately dispositions the selection discrepancy.


### Follow-up checks after the Seq-key correction (2026-10-11)

A second implementation defect was found in the SNR threshold guard: `_snr_from_mag_error` represents malformed, zero, negative, or non-finite errors as NaN, but comparing NaN with `< sigma` returns false. Without an explicit finiteness check, an invalid SNR could pass the selection guard. PR #176 adds `math.isfinite(snr)` before accepting a detection and regression rows for `nan`, zero, and negative magnitude errors. This does not modify thresholds or the documented selection rule.

The independent diagnostic now reports a flag-zero-per-band variant separately from the baseline SNR predicate. Treat it as a hypothesis only: the cited Chan et al. paper states at least one 2.5σ g-band detection and one 3σ r-band detection, but does not explicitly state a flag-zero requirement. Do not add such a filter to production selection just because it improves cardinality matching.

The fresh heavy runs are tracked at [#38120880783](https://github.com/saeed92m/ztf-classifier/actions/runs/38120880783), [#38121390203](https://github.com/saeed92m/ztf-classifier/actions/runs/38121390203), and latest-head [#38121913146](https://github.com/saeed92m/ztf-classifier/actions/runs/38121913146). Accept only the Seq-keyed current membership results, not the superseded row-ordinal counts. PR #176 also excludes raw and normalized per-epoch lightcurves from uploaded artifacts while retaining compact provenance, selection diagnostics, and membership evidence.
