# DR24 Fixed-OID Evidence Bundle

This workflow is a bounded operational capture for the two predeclared DR24
OIDs `264114400013085` and `264214400000912`. It is an acquisition and
provenance record, not a scientific validation result. Run it only through the
GitHub Actions **workflow_dispatch** event in `.github/workflows/dr24-evidence-capture.yml`.

## Byte scopes

The bundle distinguishes these byte sequences and never calls decoded API
content original HATS/Parquet bytes:

| File or digest | Exact bytes covered |
| --- | --- |
| `api_response_file_sha256` | Exact bytes saved as `api_response.json`, the HTTP API's decoded DR24 records and provenance serialized as JSON. |
| `canonical_epoch_sha256` | UTF-8 canonical JSON of one OID's decoded epoch array, sorted object keys, compact separators, original epoch array order preserved. |
| `canonical_epoch_file_sha256` | Exact bytes saved in that OID's `canonical/oid_<OID>_epochs.json`; currently the canonical JSON bytes above. |
| `workbench_export_file_sha256` | Exact bytes saved as `workbench_export.json`. The default export is explicitly labeled as derived from the same single API response, not a browser download. |
| `manifest_file_sha256` | Exact bytes of `manifest.json`, recorded in the detached `checksums.json` sidecar to avoid a self-referential hash. |
| `checksums.json` file entry | Exact bytes of each other bundle file, including `capture.log`, when present. |

`checksums.json` cannot contain a self-digest. GitHub's uploaded artifact digest
is separate metadata; it is not represented as a digest inside this bundle.

The DR24 adapter exposes decoded native records; this path does not preserve
the original HATS/Parquet object bytes. Accordingly,
`original_source_files_available` is false and
`original_source_file_sha256` is null. The source catalog URI and API endpoint
are recorded separately.

## Bundle contents

- `manifest.json`: versioned request, source, run, OID, count and digest
  metadata. It records requested, returned and missing IDs through the API
  provenance and fails validation unless the exact pinned pair is returned.
- `api_response.json`: exact response body bytes from one request through the
  existing DR24 API boundary.
- `workbench_export.json`: export wrapper built from that same payload, so no
  second acquisition can create a mismatched provenance chain. It is not
  evidence that a browser was opened or a user clicked Download.
- `canonical/oid_<OID>_epochs.json`: canonical decoded epochs per object.
- `checksums.json`: detached manifest hash plus exact file-byte hashes and
  lengths for the bundle files.
- `capture.log`: bounded event log with fixed requested IDs, HTTP status,
  returned IDs and response size. It contains no environment dump or headers.

The manifest records filter ID and band, catalog and independently counted
epoch numbers, source query, UTC capture times, software commit, Python version,
SHA-256 for both `requirements.lock` and `requirements-dr24.lock`, and result
status. The fixed OID epoch-count and canonical digest gates use the checked-in
parity contract. A mismatch fails closed. These gates do not assert a
physical-source identity or scientific classification.

## Validation and retention

The workflow is dispatch-only, uses the public DR24 HATS source, fixes the
request to two OIDs, applies a 12-minute command timeout and a 25-minute job
timeout, then validates file and manifest digests before returning success.
GitHub Actions installs the two pinned lockfiles before the local project.
The DR24 lock was derived from the existing Python 3.11.18 `.venv-park`
runtime's installed dependency closure; a clean runner installation has not
yet been executed. GitHub Actions uploads the scoped evidence directory on
success or failure with a 30-day retention period. The workflow requests only `contents: read`,
does not configure secrets, disables checkout credential persistence, and
does not upload caches or the runner home directory. Dispatch requires an
authorized GitHub Actions user, but the source query itself requires no
credential.

Runner logs and a static setup-failure marker sit alongside the `bundle/`
directory in the artifact and are not represented as source data. Full setup
logs remain in the GitHub Actions job log instead of the uploaded artifact.
No live acquisition is run
by unit tests or ordinary push/PR workflows.
