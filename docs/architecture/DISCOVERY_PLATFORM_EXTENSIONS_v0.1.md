# Discovery Platform Extensions v0.1

## Purpose

This document extends the v0.3 architecture contracts toward the long-term Astronomical Data Analysis & Discovery Platform without modifying the frozen v0.2.0 scientific baseline.

## 1. Canonical observation package

Future observations may carry independent, optional modality/context references:

```text
Observation
├── photometry / light_curve
├── image / cutout (optional)
├── object metadata
├── quality information
└── external catalog matches (optional)
```

Each component has its own schema/version/provenance. Optional data is never silently substituted.

## 2. Catalog / cross-match contract

A cross-match result must identify source catalog, source version, retrieval timestamp, matching method, radius/policy, source identifier, matched identifier, match quality/probability, and provenance where available.

Cross-match data is contextual evidence. It is not automatically ground truth.

## 3. Analysis-mode contract

The model registry is extended conceptually from one classifier family to explicit analysis modes. A mode declares task type, consumed modalities/features, taxonomy/label semantics, model artifact, training/evaluation dataset identities, calibration/uncertainty support, OOD support, explainability support, and known failure modes.

Example modes include real/bogus, transient classification, variable classification, anomaly detection, and specialized event vetting.

## 4. Diagnostic semantics

The result contract must preserve independent fields for classification uncertainty, calibration status, conformal prediction status, OOD status/score, scientific anomaly status/score, explainability evidence, and external/catalog evidence.

No field may imply that another field is equivalent to it.

## 5. Discovery candidate contract

A discovery candidate is not simply a low-confidence prediction. It is a versioned scientific result assembled from analysis outputs and evidence.

A candidate should reference source observation/object; analysis mode and model artifact; feature/context versions; uncertainty/OOD diagnostics; anomaly evidence if applicable; external catalog evidence; provenance; candidate-generation rule/version; and review status.

## 6. Human review contract

Human review is an evidence-producing operation. A review record must include reviewer identity or controlled pseudonymous identity, timestamp, candidate version, evidence presented, structured decision/label, and provenance.

Human feedback cannot silently mutate benchmark labels or training data.

## 7. Feedback-to-learning contract

Feedback may enter retraining/recalibration only through an explicit versioned dataset and validation workflow. Temporal leakage, duplicate-object overlap, label provenance, and evaluation-role separation remain mandatory.

## 8. Explainability contract

For applicable models, explanation output may include top feature contributions, attribution values, or modality-specific explanations. Explanations are diagnostic evidence, not proof of scientific correctness.

## 9. Multimodal readiness

The application layer should accept modality declarations and report missing/unsupported modalities deterministically. The architecture does not require GPU execution or a specific ML framework.

## 10. Invariants

1. v0.2.0 remains immutable.
2. ALeRCE remains reference evidence, not absolute ground truth.
3. Uncertainty, OOD, anomaly, and scientific evidence remain distinct.
4. Cross-match data retains provenance and evaluation role.
5. Human feedback is versioned evidence, not implicit truth.
6. Optional modalities are explicit and never fabricated.
7. Analysis modes are independently versioned and registered.
8. CPU-first operation remains a supported product constraint.
9. Scientific validation remains release-blocking at product level.
10. Large external scientific datasets remain outside Git.
## 11. Implemented diagnostic-semantics boundary

The production result contract now carries **scientific anomaly evidence separately from OOD**.

- `ood` describes deviation from the model/reference input distribution.
- `scientific_anomaly` is a separate evidence channel and is not populated merely because an OOD score is high.
- `scientific_anomaly_status` is explicitly one of `available`, `unavailable`, or `not_evaluated`.
- When scientific anomaly evidence is available, its method and evidence version are required and its score/flag arrays must align with the prediction sample count.
- API consumers receive separate `ood` and `scientific_anomaly` fields.

The current production v0.2 model does **not** claim a scientific-anomaly detector. Therefore its scientific-anomaly state remains `not_evaluated` unless a future, explicitly registered scientific anomaly analysis mode supplies evidence.

This prevents the historical ambiguity in which an Isolation Forest OOD diagnostic could be rendered or interpreted as an astrophysical anomaly finding.