# Desktop Workspace Session Lifecycle

**Status:** Implemented on a feature branch; awaiting CI and Windows acceptance verification  
**Scope:** Windows desktop workbench, DR24 Explorer session state  
**Related issue:** [#324](https://github.com/saeed92m/ztf-classifier/issues/324)  
**Baseline:** Preview 5 remains unchanged and immutable

## Problem

The desktop workbench reconstructs the DR24 Explorer DOM when the user changes views. The previous implementation also cleared the module-level DR24 payload and export references during view construction. The OID text field and rendered results therefore disappeared even though the active workspace had not changed.

The server-side workspace operation ledger and explicit export store do not replace the live view session. Operation metadata records what was requested and returned; an export is persisted only when the user explicitly saves/downloads it.

## Decision

Keep an in-memory DR24 session registry in the desktop renderer, keyed by the active workspace ID.

Each session retains:
- OID input text.
- Last successful raw DR24 response.
- Raw JSON export envelope.
- Whether the export has already been persisted.
- Rendered result markup for the returned OIDs.
- Acquisition provenance text.
- Acquisition status text.

On each view entry, resolve the active workspace and restore only that workspace's session. A newly created workspace receives a new empty session. Switching workspaces must not expose another workspace's data. Sessions remain available while the desktop application process is running.

## Lifecycle and persistence boundary

- **Menu navigation:** preserve the session; do not issue another DR24 request.
- **Workspace switch:** activate the session keyed to the newly active workspace.
- **Return to a previously active workspace in the same process:** restore its in-memory session.
- **New workspace:** begin with an empty session.
- **Application exit:** in-memory, unexported state is released.
- **Explicit raw JSON export:** retain the existing durable workspace export behavior and SHA-256 metadata.

This change does not claim that an unexported in-memory session survives an application restart. That requires a separate durable session/artifact contract and is outside this focused fix.

## Scientific and product guardrails

This is a UI/workspace lifecycle correction only. It does not change:
- DR24 source payloads or their hashes.
- Raw HMJD, magnitude, magnitude-error, or catflags values.
- QC selection or filtering rules.
- Time or photometry conversions.
- Feature extraction or model inference.
- v0.2.0 scientific baseline, taxonomy, feature schema, or acceptance criteria.
- Preview 5 release artifacts.

A failed new acquisition must not erase the last successful result in the active in-memory session. The failure status must identify the failed attempt and make clear which earlier OIDs still have a successful result.

Every asynchronous DR24 request must capture its originating workspace ID and session before the acquisition awaits. The completed response must update that captured session only. It may update the visible page only when the captured workspace is still active. A late response must never write its payload or export envelope into a different workspace.

Restoring a saved raw export must reset the rendered-result state. The UI must not display plots or provenance from an earlier payload beside a newly restored export. Until the light-curve view is rebuilt, show an explicit restored-export state.

## Acceptance

The issue acceptance tests in #324 are authoritative. At minimum, verify navigation round trips, no duplicate acquisition, workspace isolation, return to an earlier workspace in the same process, new-workspace emptiness, and retention of the last successful payload after a failed subsequent request.

The focused test suite and Windows desktop packaging workflow must pass before merge or publication of a subsequent Preview release. The browser acceptance suite must also cover a delayed in-flight request while switching workspaces, export restoration without stale rendered state, and retention of the last successful result after a failed later request.
