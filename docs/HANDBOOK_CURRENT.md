# ZTF Classifier — Current Operational Handbook

**Reviewed:** 2026-10-23 UTC  
**Current published release observed:** v1.0.1  
**Frozen scientific baseline:** v0.2.0  
**Governing documents:** [Project Charter](PROJECT_CHARTER_AND_SOURCE_OF_TRUTH.md), [Project State Register](PROJECT_STATE_REGISTER.md), [Platform Expansion Roadmap](roadmap/PLATFORM_EXPANSION_ROADMAP.md).

> This is the current operational handbook, not a declaration that every planned capability is implemented. The exact main commit and open PR state must be checked before reporting current status.

## Product identity

The product is an **Astronomical Data Analysis & Discovery Platform**. ZTF is the first established scientific domain, not the exclusive input. Astronomers should be able to import their own supported datasets or select supported public sources, inspect observations, run appropriate analyses, assess uncertainty, investigate candidates, review evidence and export reproducible results.

It is not only a CPVS reconstruction tool or a single-purpose classifier. CPVS exact membership is a separate unresolved scientific blocker and must not prevent independent product-platform work.

## Core workflow

Source selection/import → provenance capture → explicit schema mapping → normalization and quality control → source-compatible features/context → analysis selection → model/method compatibility gate → uncertainty/calibration/conformal/OOD and separate anomaly evidence → candidate ranking and human review → reproducible reports and exports.

## Data contract

Every source adapter must make explicit:
- Object/source identifier and stable grouping semantics.
- Observation time value, format and scale.
- Passband/filter and mapping.
- Measurement type (magnitude, flux or another declared quantity), unit and photometric convention when applicable.
- Uncertainty, quality/mask flags, upper-limit/sentinel semantics and optional coordinates.
- Source survey/product/version, retrieval date, usage terms, checksums and source-row provenance.

Do not silently convert flux to magnitude, mix AB/Vega systems, assume time scales, erase duplicates, drop rows, or infer unknown units. Record any conversion as a named, tested transformation with input/output units and provenance.

## Four independent support states

1. **Import-supported:** file/source format, explicit mapping, provenance and row/object accounting pass pinned tests.
2. **Analysis-supported:** declared QC, features or statistical analysis pass deterministic tests for that source.
3. **Model-compatible:** exact artifact, schema, preprocessing, units, bands, taxonomy and training domain match.
4. **Scientifically validated:** source-backed, leakage-safe evaluation and reproducibility/failure gates pass for a declared task and domain.

Do not conflate these states. Successful parsing, unit tests, green CI, or a matching column count does not prove scientific validity. Unsupported inputs must produce actionable diagnostics or abstention.

## Analysis channels must remain distinct

- Classification / class probabilities.
- Probability calibration and uncertainty.
- Conformal prediction sets and coverage.
- Out-of-distribution (OOD) scoring.
- Scientific anomaly evidence.
- Real/Bogus classification.
- Catalog/cross-match evidence.
- Explainability evidence and candidate-ranking rationale.

Do not present OOD as a proven scientific anomaly detector or call candidate rankings discoveries without review/evidence.

## Frozen scientific baseline

Recorded v0.2.0 baseline: 150 benchmark objects, 15 ALeRCE reference classes, 10 objects per class, 42 features in `final_feature_set_v0.2`, XGBoost artifact `model_baseline_v0.2_production/artifact`, historical cutoff `59447.224132`, schema 1.1 diagnostics, frozen class order and fail-closed scientific gate. Verify these values against actual repository artifacts before using them as fresh evidence.

ALeRCE labels are reference/benchmark labels, not independent ground truth. Historical ALeRCE snapshot Zenodo 4279623 (through 2020-06-09) is frozen reference data; live ALeRCE is monitoring/context.

## CPVS blocker

The latest recorded Seq-based comparison reports 781,602 parent IDs, 730,184 published IDs, 741,786 reconstructed candidates, 11,602 candidate-only and zero published-only. Treat these as last-recorded values, not a fresh run unless reverified against current artifacts. Exact reconstruction remains unresolved. Do not tune thresholds/flags to force equality or claim the original published selection rule has been reproduced without source-backed evidence.

## Architecture boundaries

- Source adapters own survey-specific acquisition/parsing.
- The canonical observation schema preserves declared semantics and original provenance.
- The scientific core owns deterministic scientific computation and model contracts.
- Application services orchestrate workflows for GUI/CLI/API without bypassing gates.
- Presentation layers display diagnostics and evidence; they do not decide scientific validity.
- Provenance connects source → transformations → features → model/analysis → report.
- Scientific datasets stay outside Git. Version-control schemas, manifests, small fixtures, hashes, configurations and compact evidence reports.

## Platform capabilities (target scope; status varies)

Data Manager; object/source explorer; light-curve visualization; statistical and periodicity analysis; model management; calibrated uncertainty and conformal sets; OOD and anomaly workflows; cross-match/context; discovery candidate ranking; human review; reproducible reports/exports; contextual Help/Troubleshooting; clean-machine desktop distribution; CLI/API; future streaming and additional survey/image/catalog adapters.

Do not mark any capability complete based on presence in a roadmap. Use the [State Register](PROJECT_STATE_REGISTER.md) and actual code/tests/workflow evidence.

## Cross-survey validation

Candidate source families include ZTF DR24/CPVS, StarEmbed, TESS/MAST/TGLC and TESS Transients, OGLE, AAVSO, ATLAS, ASAS-SN, Gaia variability, and PLAsTiCC/ELAsTiCC. This list is a test matrix, not proof of adapters. Pin source version, terms, retrieval date, schema and checksums. Start with bounded public samples. Validate import, normalization, semantics, feature availability, model compatibility, scientific performance, domain shift and reproducibility separately.

## Change and release rules

- Main and immutable tagged releases are authoritative for shipped code/artifacts.
- Open PRs are proposals, not releases.
- Keep v0.2.0 immutable unless a separately reviewed and scientifically validated change supersedes it.
- Every meaningful change includes regression tests, lifecycle evidence, updated docs, known limitations, compatibility/rollback notes and explicit next steps.
- Every release includes complete notes, tests, scientific gates, provenance, checksums and outstanding risks.
- Missing/skipped/inconclusive required evidence is not PASS.
- Preserve historical handbook snapshots; update this current handbook and index instead of rewriting old versions.

## Current external documentation surfaces

As of 2026-10-23, repository metadata reports GitHub Wiki enabled but write access is unverified; GitHub Pages disabled; and no ZTF-specific Supabase project/schema verified in the connected account. The Notion archive ZIP is known to be stale and has not been refreshed. Do not claim any of these surfaces or systems were updated without verified write/readback evidence.
