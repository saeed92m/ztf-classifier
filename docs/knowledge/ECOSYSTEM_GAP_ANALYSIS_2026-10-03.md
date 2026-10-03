# ZTF Classifier — ZTF Ecosystem Gap Analysis

**Date:** 2026-10-04

**Follow-up:** Public repository review was converted into implementation changes and frozen-reference contracts on 2026-10-04.  
**Scope:** comparison of `saeed92m/ztf-classifier` with representative public ZTF/time-domain astronomy ML repositories discovered through GitHub repository search.

## Executive conclusion

The project is not missing a fundamental classifier capability. Its current architecture is already stronger in reproducibility, provenance, uncertainty handling, artifact contracts, registry-backed inference, and scientific release gating than many small ZTF classifier repositories.

The comparison identifies platform capabilities that should now be explicitly represented in the roadmap and architecture:

1. **External catalog / cross-match layer** — P0/P1 architecture requirement.
2. **Strict semantic separation of classification uncertainty, OOD, and scientific anomaly** — permanent architecture invariant.
3. **Active-learning and human-in-the-loop discovery** — P1/P2 discovery capability.
4. **Explainability contract** — P1/P2 analysis capability; having SHAP as a dependency is not an explainability contract.
5. **Image/cutout modality readiness** — future architecture boundary, not immediate implementation.
6. **Multimodal readiness** — future architecture boundary for light curves + images + catalog context.
7. **Specialized model families** — real/bogus, transient/variable classification, anomaly/specialized detectors as independent analysis modes.
8. **Candidate → evidence → human validation → discovery loop** — future product workflow.

## Representative ecosystem signals

The comparison included repositories such as:

- `snad-space/flare-classifier`: staged ML pipeline, external data storage/versioning, metrics and DVC workflow.
- `PaulaSanchezSaez/ZTF-DR11-classifier`: multiband/external-catalog feature context and explicit feature-name lineage.
- `snad-space/snad-binary-classifiers` and related SNAD work: specialized binary classifiers and reusable classification patterns.
- `WizardEternal/ztf-kn-vetting`: event-specific vetting direction.
- `StevieG47/ztf-machine-learning`: sequence/light-curve modeling direction.
- `Chacon-Miguel/TESS-ZTF-Light-Curve-Classifier`: cross-survey/light-curve classification direction.
- Broader ZTF real/bogus and anomaly-detection projects: image-based and anomaly-oriented analysis rather than only taxonomy classification.

These projects are architectural signals, not authoritative implementation templates.

## What we should adopt

### 1. Cross-match / external catalog context

Define a first-class cross-match contract with catalog/version, retrieval date, matching policy, source and matched identifiers, match quality/probability, and provenance/hash where applicable. The layer should support future catalogs such as Gaia, PS1 and WISE without coupling the core model to any one catalog.

### 2. Three-way diagnostic separation

The platform must never equate:

`low classification confidence == OOD == astrophysical anomaly`.

- **classification uncertainty:** uncertainty among supported model hypotheses;
- **OOD:** evidence that the input differs from the model/reference distribution;
- **scientific anomaly:** an object or behavior that is scientifically unusual or worthy of investigation.

This distinction must appear in result schemas, reports, UI semantics, tests, and documentation.

### 3. Human-in-the-loop discovery

Introduce:

`candidate ranking -> human review -> structured feedback -> controlled learning/recalibration -> candidate ranking`.

Human labels must be provenance-bearing and must never silently become training truth. Feedback-to-retraining requires explicit dataset/version/temporal/leakage controls.

### 4. Explainability

Add an explainability result contract. For tabular models this can expose feature contributions and top contributing features. Future image models may use image-specific attribution methods. Explainability is supplementary evidence and does not replace independent validation, calibration, provenance, or scientific evidence.

## Future readiness, not immediate scope

### Image/cutout modality

Define a modality-neutral observation boundary capable of referencing a light curve, image/cutout, metadata, and catalog context. Do not add GPU/CNN infrastructure merely for parity with other projects.

### Multimodal analysis

Future analysis requests should be able to declare required modalities. A model must explicitly declare which modalities it consumes; missing modalities must be represented as a contract state, not silently fabricated.

### Specialized model families

Treat analysis modes as first-class registry objects. Examples include real/bogus, transient taxonomy, variable-source taxonomy, anomaly detection, and event-specific vetting. The frozen v0.2 classifier remains one compatible model family.

## What we explicitly do NOT adopt merely for parity

- DVC solely because another project uses it; our manifest/hash/provenance contracts remain authoritative.
- GPU/deep-learning infrastructure solely because other projects use CNNs or neural networks.
- LLM/VLM components solely because newer astronomy benchmarks use them.
- Kubernetes or distributed infrastructure without a product requirement.
- Any external model, catalog, or benchmark as ground truth without an explicit evaluation role and source evidence.

## Scientific validation implications

The ecosystem comparison strengthens the existing Product-level Scientific Validation Gate. Future release evidence should distinguish internal benchmark performance, independent catalog/reference agreement, source-backed reproduction, OOD/failure behavior, discovery candidate quality, and human/scientific validation evidence.

## Decision

The platform direction is confirmed as:

`source data → canonical observations → QC → scientific feature/context layers → analysis modes → uncertainty/calibration/OOD → candidate ranking → evidence/provenance → human/scientific validation → reproducible discovery outputs`

The frozen v0.2.0 scientific baseline is unchanged.

## 2026-10-04 implementation outcome

The ecosystem review found a direct solution to the current validation deadlock:

- ALeRCE historical data has an immutable Zenodo reference (4279623).
- CPVS published 730,184 membership has an immutable Zenodo release (5764899).
- The 781,602 parent has an immutable Zenodo release (3886372).
- These are now first-class benchmark contracts in the repository.
- Live ALeRCE and current-source CPVS reconstruction remain diagnostic/drift lanes.

This closes the architectural gap identified by the comparison. The remaining work is execution: acquire, hash-verify, execute, and attach evidence to #51/#63 and the final scientific gate.
