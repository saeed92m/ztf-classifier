# Scientific Analysis Workbench UI v0.1

## Product role

The Workbench is the presentation layer for the astronomical analysis platform. It consumes versioned API contracts and does not embed domain or inference logic.

Primary layout:

- top bar: identity, connection state, appearance;
- left rail: analysis/workspace navigation;
- center canvas: scientific analysis;
- right inspector: object identity, analysis state, provenance;
- responsive fallback: inspector collapses first, navigation collapses on small screens.

## Appearance contract

The application supports five user-facing modes:

1. **Auto** — default; follows the local system clock.
2. **System** — follows the operating system/browser `prefers-color-scheme` preference.
3. **Deep Space** — fixed dark scientific/observatory theme.
4. **Alpha Theme** — fixed dark Alpha Team brand theme.
5. **Light** — fixed light research-lab theme.

Auto schedule defaults to 06:00 day start and 18:00 night start and is configurable by the user. Preferences are persisted locally.

Theme selection changes semantic presentation tokens only. It must not alter scientific data, API semantics, layout contracts, typography scale, spacing, or component behavior.

## Design-token contract

Components consume semantic variables:

- `--color-bg`
- `--color-surface`
- `--color-surface-2`
- `--color-primary`
- `--color-primary-hover`
- `--color-accent`
- `--color-text-primary`
- `--color-text-secondary`
- `--color-brand-gray`
- `--color-border`
- `--color-success`
- `--color-warning`
- `--color-error`
- radius and shadow tokens

Brand colors:

- Alpha Blue: `#003C91`
- Alpha Gray: `#8A8A8A`

Scientific chart palettes are intentionally separate from UI branding. Class colors, uncertainty scales, heatmaps, and publication graphics must remain legible and scientifically meaningful across all UI themes.

## Scientific information hierarchy

The Workbench distinguishes:

1. observations and quality control;
2. derived features;
3. periodicity/scientific measurements;
4. model prediction;
5. calibrated probability;
6. conformal prediction sets;
7. OOD/anomaly diagnostics;
8. provenance and reproducibility.

No scientific result is represented only by a visual state. Important values remain accessible as text/table data.

## Current implementation slice

The initial shell is served by the API at:

`/workbench/`

It currently provides:

- API-backed object analysis;
- API-backed light-curve visualization;
- durable scientific-result hydration;
- classification probability surface;
- scientific metadata/provenance inspector;
- batch/catalog/report navigation placeholders;
- appearance selector with all five modes;
- responsive layout;
- semantic status states.

The Workbench now hydrates its light curve from the normalized observation API and hydrates classification/provenance panels from the durable scientific-result API when a persisted result exists. It does not fabricate scientific values when data is unavailable.

## Evolution rules

- API/domain contracts remain independent of UI implementation.
- Components must consume semantic tokens rather than hard-coded theme colors.
- Scientific chart colors must not inherit branding accidentally.
- UI changes must preserve accessibility and data readability.
- A future component framework may replace the current dependency-light shell without changing API contracts.
- Workbench modules should be independently routable and progressively hydrated from API data.


## Scientific Validation Dashboard

The Workbench must expose a release-scoped Scientific Validation surface backed by the executable validation report.

Required panels:

- gate status: PASS / NOT_VERIFIED;
- benchmark registry and evaluation role;
- population/source/version and retrieval metadata;
- benchmark metrics and calibration/OOD diagnostics;
- leakage status for every release-blocking check;
- regression history and disposition;
- known failure cases and out-of-domain scope;
- provenance completeness and input hashes;
- release decision evidence.

The dashboard is evidence presentation only. It must not convert reference-system agreement into ground truth or suppress unresolved scientific blockers.


## Desktop Scientific Mission Control — UI revision

The Windows desktop preview uses the Mission Control layout as its dashboard reference. The dashboard is an evidence view. It must read current application state from the versioned local API.

### Mission Control banner artwork

The top application header uses a local SVG banner with a restrained nebula and spiral-galaxy composition. It is static decorative artwork only. It must not display or imply a specific real astronomical observation. The file is packaged with the Workbench and checked by the frozen self-test.

### Brand asset

The desktop Workbench header and web favicon use the local `ztf-logo.svg` vector asset. The existing `ztf-logo.ico` remains the Windows executable/shortcut icon asset and fallback. The SVG is included in the frozen application self-test. This change does not by itself prove that the installed desktop shortcut displays the intended icon; that remains a separate visual acceptance check.

### Desktop-wide visual system

The visual language applies to the dashboard and all existing desktop views. It uses the same header, navigation, typography, panel treatment, form controls, buttons and color contrast. A page must not fall back to the old Workbench grey surfaces.

### Dashboard composition

- Header banner: product identity, current page and the exact scientific gate status.
- Summary cards: configured primary source, active workspaces, saved scientific result records and scientific validation status.
- Main row: a light-curve panel and a Mission Status panel.
- Lower row: saved analysis results, recent asynchronous analysis jobs and system health.
- Navigation order: Overview, DR24 Explorer, Workspaces, Result Catalog, Analysis Jobs, Data Sources, Provenance, Scientific Validation, Reports and Exports, Settings and Help.

### DR24 workspace preflight

Before a DR24 request, the desktop client must verify that a workspace is active. If none exists, show a workspace requirement, record the acquisition as NOT RUN in the UI, keep export disabled, and do not send a request to the DR24 source. If the workspace-state endpoint is unavailable, report that the preflight could not be completed. Neither case may be labelled as a DR24 acquisition failure.

The Help page must explain the correct sequence: create/open a workspace, then acquire DR24 records, review raw data and diagnostic QC, inspect provenance, and export.

### Data-binding rules

| UI element | API source | Interpretation |
| --- | --- | --- |
| Local API | `GET /health` | Process liveness only; not model or scientific readiness. |
| Active workspaces | `GET /v1/workspaces` and `GET /v1/workspaces/active` | Count only workspaces explicitly marked active. |
| Model registry | `GET /v1/model` | Model metadata is available; this does not prove scientific acceptance. |
| Scientific gate | `GET /v1/scientific-validation` | Display the exact fail-closed status and blocker count. |
| Recent operations | `GET /v1/jobs?limit=5` | Display persisted asynchronous analysis jobs only. |
| Saved results | `GET /v1/catalog/results?limit=8` | Display persisted scientific result records only. |
| Light curve | Latest saved result with an observation array | Plot only returned observation values. Show an empty state when no result contains observations. |

### Scientific and UX constraints

- Do not insert sample object IDs, synthetic light-curve points, made-up probabilities, fake queue rows, fake uptime, or fabricated service health.
- Do not describe an OOD score as a scientific anomaly.
- Do not describe a model registry response as a passed scientific validation gate.
- Keep the DR24 raw-data path separate from normalized observation data. Preserve the source time field and its units.
- The dashboard must remain useful when one API call fails. Show an explicit unavailable state for that service.
- Keep the original scientific validation screen and its fail-closed meaning.
- The visual theme must not alter API contracts, data transformations, model behavior, or scientific thresholds.
- The desktop splash and startup handoff are protected regression requirements.

### Verification

The UI contract test checks the required API bindings, Mission Control markup and style layer. The Windows preview workflow must also pass JavaScript syntax checks, packaged self-test, and real WebView2 GUI smoke tests. A CI pass alone does not prove visual fidelity; the installed application must be captured and compared with the reference screen before the UI redesign is accepted.
