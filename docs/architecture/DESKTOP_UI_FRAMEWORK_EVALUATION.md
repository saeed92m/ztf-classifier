# Desktop UI Framework Evaluation

**Status:** Proposed evaluation plan — no framework migration approved  
**Date:** 2026-11-28  
**Scope:** Desktop presentation layer only  
**Protected baseline:** Preview 5 and scientific baseline v0.2.0 remain unchanged

## 1. Current verified position

The active Windows desktop preview uses a WebView-based Workbench. The Python application and local API provide the application and scientific services. The current DR24 workspace-state correction is still under review and has not passed its acceptance workflow.

No Qt Quick/QML or .NET/WPF implementation is present in this change. No comparative performance measurements are available. Therefore, a framework migration cannot be justified yet.

## 2. Architectural direction

Keep the scientific engine and application services independent of the desktop presentation technology.

The intended boundary is:

```text
Desktop presentation
  WebView2 (current) | Qt Quick/QML (candidate)
                 |
       Versioned local API contract
                 |
       Python application services
                 |
       Scientific Python core
```

The desktop UI must use documented application/API contracts. It must not import scientific implementation modules or mutate scientific state directly.

The local API remains usable without the desktop UI. The UI must not become a required dependency for CLI, API, batch processing, or reproducible scientific workflows.

## 3. Framework position

### WebView2 — retain as the current baseline

- It is the existing implementation and the basis of Preview 5.
- It already uses the local Workbench and Python service boundary.
- Keep it operational while the evaluation runs.
- Do not assume that the current UI defects require a framework replacement. Fix lifecycle and state-management defects at their root.

### Qt Quick / QML — preferred candidate for a controlled prototype

- Evaluate Qt Quick/QML for a future cross-platform desktop presentation layer.
- Evaluate PySide6 only as the Python-to-Qt integration option; do not add it to production dependencies before the prototype gate.
- Reuse the same local API contracts and Python services.
- Test Windows, Ubuntu, and macOS packaging before selecting it as the product direction.

### .NET / WPF — not the primary product path

- WPF is Windows-specific.
- The product target includes Windows, Ubuntu, and macOS.
- Do not add a separate .NET application stack unless a future Windows-only requirement or a proven integration need justifies it.
- .NET is not selected for the scientific core.

## 4. Controlled prototype

Build one equivalent Overview screen in the current WebView2 UI and a separate Qt Quick/QML prototype.

Both prototypes must:
- Use the same versioned API responses.
- Display the same real application state.
- Show explicit empty, unavailable, and error states.
- Avoid mock astronomical measurements and invented operational metrics.
- Preserve the existing visual hierarchy and navigation intent of Preview 5.
- Leave the scientific engine, model artifacts, taxonomy, feature schema, and validation rules untouched.

Do not build the complete application twice. The prototype is a decision instrument, not a second product.

## 5. Evaluation protocol

Record raw measurements and environment details for each platform. Do not compare results from different machines or configurations as if they were equivalent.

| Dimension | Required evidence |
|---|---|
| Startup | Cold and warm start time |
| Memory | Idle and representative active-workflow RAM |
| CPU | Idle and representative active-workflow utilization |
| Responsiveness | Navigation, chart update, table rendering and large-result interaction |
| Packaging | Installer/app size, clean install, upgrade, uninstall and rollback |
| Portability | Build and smoke tests on Windows, Ubuntu and macOS |
| Reliability | UI automation, crash recovery, long-session behavior |
| Accessibility | Keyboard navigation, focus order, scaling and screen-reader semantics |
| Maintainability | Dependency footprint, build complexity, testability and developer workflow |
| Security | Local API authentication, origin restrictions and update/package integrity |

Record hardware, OS version, runtime versions, build configuration, test commands, raw outputs and artifact hashes.

## 6. Decision gates

1. **Workspace reliability gate:** the active Workspace/DR24 lifecycle tests and Windows acceptance workflow must pass.
2. **API boundary gate:** the Overview prototype must use stable, documented API contracts.
3. **Prototype gate:** both implementations must provide equivalent behavior and evidence.
4. **Cross-platform gate:** Qt must build and pass smoke tests on all three target operating systems.
5. **Architecture decision:** select a framework only after reviewing measured results, risks, maintenance cost and packaging evidence.

A successful prototype does not authorize an immediate full migration.

## 7. Migration constraints

If Qt is selected:
- Migrate one screen at a time.
- Keep the existing WebView2 preview available until Qt reaches feature parity for the accepted scope.
- Do not duplicate scientific algorithms in QML or C#.
- Keep API and data contracts versioned.
- Preserve workspace isolation, provenance, raw data, export semantics and explicit persistence boundaries.
- Require regression tests for each migrated workflow.

## 8. Current decision

**Decision: DEFER FULL MIGRATION; PROTOTYPE Qt Quick/QML AGAINST WEBVIEW2.**

WebView2 remains the current desktop implementation. Qt Quick/QML is the preferred candidate for evaluation, not an approved replacement. .NET/WPF is not selected for the multi-platform product path.

No performance, usability, or packaging winner has been established.
