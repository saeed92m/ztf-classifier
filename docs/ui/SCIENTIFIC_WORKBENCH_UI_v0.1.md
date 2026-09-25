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
