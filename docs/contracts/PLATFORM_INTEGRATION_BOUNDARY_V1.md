# Platform Integration Boundary — Contract v1

**Status:** declared, not implemented. Version `1.0.0` (2026-10-24).
**Applies to:** `saeed92m/ztf-classifier` (provider) and
`saeed92m/Company-Platform` (optional future consumer).

This document defines the *only* permitted coupling between the two projects. It
exists so that a future integration cannot quietly make the scientific product
depend on a company platform.

## 1. Repository independence

| Property | ZTF Classifier | Company-Platform |
|---|---|---|
| Repository | `saeed92m/ztf-classifier` | `saeed92m/Company-Platform` |
| Identity | Scientific analysis and classification product | Company platform (projects, services, UI) |
| Versioning | Own semver, own tags (`v1.0.1`, baseline `v0.2.0`) | Own semver, own tags |
| Release cycle | Own; gated by Scientific Validation | Own |
| Licence | Own (currently `Proprietary` in `pyproject.toml`) | Own |
| Documentation authority | `docs/README.md` | Its own |

Neither repository may consume the other's release artifacts, tags, version
numbers or documentation as if they were its own.

## 2. Hard non-dependency rule

ZTF Classifier **must remain fully functional with no access to
Company-Platform, Supabase or any cloud service.**

Verified current state: the repository contains **zero** references to
`supabase`, `company-platform` or any company endpoint in code, configuration,
workflows or documentation. The local product path is CPU-first and
offline-capable except for explicit, opt-in external data acquisition.

Any change that would introduce a runtime requirement on Company-Platform
requires an explicit architectural decision recorded in
`docs/knowledge/ARCHITECTURAL_DECISIONS.md` and a new contract version.

## 3. Permitted integration direction

One direction only, and only optionally:

```
Company-Platform  ──HTTP──►  ZTF Classifier /v1 API
      (consumer)                  (provider)
```

- ZTF Classifier is the **provider** and never calls out to Company-Platform.
- Company-Platform is the **consumer** and holds no scientific logic.
- The transfer medium is the versioned HTTP API described in
  `docs/api/API_V1.md`. No shared database, no shared schema, no shared
  filesystem, no shared credentials.

## 4. Data contract

The wire format is the API v1 surface. Consumer obligations:

1. **Contract version is the URL prefix.** `v1` endpoints are stable within the
   major version. Breaking changes require `/v2/` and a new version of this
   contract; `/v1/` remains served until the consumer migrates.
2. **Consumers must tolerate additive change.** New optional response fields
   may appear in a `v1` response without a version bump. Consumers must ignore
   unknown fields.
3. **Scientific status is carried, never inferred.** Every scientific result
   carries its own status vocabulary (`PASS`, `BLOCKED`, `UNRESOLVED`,
   `FAIL`). A consumer must not upgrade `BLOCKED` or `UNRESOLVED` to success,
   and must not present a blocked result as a validated claim.
4. **Provenance travels with the result.** Model identity, feature-schema
   version, dataset manifest hash and the preprocessing contract version are
   part of the payload, not consumer-side assumptions.
5. **No scientific reimplementation.** Mean magnitudes, per-band periods, SNR
   thresholds, CPVS membership predicates, feature definitions and calibration
   are computed by ZTF Classifier only. A consumer may not re-derive or
   approximate them.

## 5. Security boundary

- Authentication: bearer token (`ZTF_API_KEY`) configured by the provider. The
  consumer stores it in its own secret manager and never in source.
- Transport: HTTPS only. No plaintext.
- Trust direction: the provider never trusts consumer-supplied scientific
  parameters that would change the selection predicate.
- Data sent to the provider must be the minimum needed for inference. The
  provider does not store consumer tenants.
- The API exposes no filesystem path, no database credential and no internal
  model registry path.

## 6. Scientific logic ownership

| Concern | Owner |
|---|---|
| Feature engineering and schemas | ZTF Classifier |
| Model, calibration, conformal, OOD | ZTF Classifier |
| Scientific validation and claim vocabulary | ZTF Classifier |
| Provenance and reproducibility records | ZTF Classifier |
| Project/tenant management | Company-Platform |
| Billing, service catalogue, customer UI | Company-Platform |
| Marketing claims about scientific accuracy | Neither: only ZTF Classifier may state a scientific result, and only in its documented vocabulary |

## 7. Change protocol

A change that crosses this boundary requires:

1. An entry in `docs/knowledge/ARCHITECTURAL_DECISIONS.md` with date, rationale,
   version and consequence.
2. A new version of this contract file (`..._V2.md`), keeping V1 for history.
3. Compatibility assessment recorded in the pull request: what breaks for the
   other repository if it does nothing.
4. Evidence that the ZTF Classifier standalone path still passes CI.

A change on the Company-Platform side that would require a ZTF Classifier
change must be proposed as a ZTF Classifier issue first. It must not be
implemented by duplicating scientific logic in the platform.

## 8. Current verification status

| Item | Status | Evidence |
|---|---|---|
| ZTF Classifier has no Company-Platform dependency | **Verified** | `grep -rniE "supabase\|company[-_ ]platform"` returns nothing |
| ZTF Classifier has no Supabase dependency | **Verified** | Same grep; issue #183 records evaluation-only |
| Company-Platform repository contents | **Unverified — access blocked** | GitHub API and `git ls-remote` return HTTP 403 for the automation identity. No claim is made about that repository's contents, structure, versioning, documentation or licence. |
| Contract actually exercised | **Not implemented** | No consumer exists yet. This is a declared boundary, not a working integration. |

The Company-Platform row is a hard limitation. Per repo rule 7, it is reported
as unverified rather than assumed. Verifying it requires a GitHub identity with
read access to `saeed92m/Company-Platform`.
