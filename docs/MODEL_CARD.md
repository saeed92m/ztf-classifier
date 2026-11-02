# ZTF Classifier — Model Card

## Model identity

- Software release: v1.0.1
- Scientific baseline: v0.2.0 (immutable)
- Production model version: `baseline_v0.2`
- Model family: XGBoost
- Feature schema: v0.2, 42 frozen features
- Artifact schemas: 1.0 and 1.1
- Historical cutoff: 59447.224132

The software version and scientific model version are separate. Software release v1.0.1 does not change the frozen v0.2.0 model baseline.

## Intended use

The model is intended for research-oriented screening and classification of ZTF transient and variable objects that satisfy the project's feature contract.

It is a component of the broader Astronomical Data Analysis & Discovery Platform. It is not a substitute for expert astrophysical classification. Current benchmark results do not establish population-level performance across all ZTF objects.

## Training and evaluation data

The frozen production artifact is associated with `benchmark_v0.2`:

- 150 ZTF objects
- 15 classes
- 10 objects per class
- ALeRCE reference/weak labels

ALeRCE labels are benchmark/reference labels. They are not independent astrophysical ground truth.

## Inputs and features

The model expects the frozen 42-feature v0.2 schema. Input preparation must preserve feature order, names, units, missing-value policy, and schema hash.

The model must not be used with an incompatible feature table. Any new feature contract requires a new model version and separate validation.

## Outputs

Production inference can expose:

- predicted class;
- class probabilities;
- calibrated probabilities when calibration is available;
- conformal prediction diagnostics when available;
- OOD diagnostics when available;
- model, artifact, feature-schema, software, and provenance metadata.

Calibration, conformal prediction, OOD, and scientific-anomaly evidence are separate semantic channels.

## Scientific-anomaly boundary

The production `baseline_v0.2` model does not claim to be a validated scientific-anomaly detector.

A high OOD score is not, by itself, evidence of an astrophysical anomaly. Scientific-anomaly evidence is a separately versioned analysis mode. It remains `not_evaluated` unless that analysis supplies explicit evidence.

## Limitations

- The benchmark is small and balanced.
- ALeRCE labels are reference/weak labels, not independent astrophysical ground truth.
- No claim of full-ZTF population representativeness is made.
- Real-world OOD behavior and temporal degradation require independent validation.
- Probability quality depends on calibration coverage and similarity between inference data and the calibration/reference distribution.
- Product-level source-backed validation and leakage audits remain incomplete.
- Exact historical CPVS reconstruction is a separate external-reproduction claim and remains unresolved. It is not treated as a model-accuracy result.

## Safety and scientific interpretation

Predictions are decision-support signals for scientific analysis. Low-confidence, OOD, or diagnostically incomplete outputs require additional investigation. Do not treat them as automatic scientific conclusions.

## Compatibility and lineage

The v0.2.0 scientific baseline and `baseline_v0.2` model identity are immutable. Future model improvements must use a new model version and preserve compatibility or provide explicit migration rules.
