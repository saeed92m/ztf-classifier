# ZTF Classifier — Model Card

## Model identity
- Software release: v1.0.0
- Scientific baseline: v0.2.0 (immutable)
- Production model version: baseline_v0.2
- Model family: XGBoost
- Feature schema: v0.2, 42 frozen features
- Artifact schemas: 1.0 and 1.1

## Intended use
The model is intended for research-oriented screening and classification of ZTF transient/variable objects represented by the project's feature contract.

It is a component of the broader Astronomical Data Analysis & Discovery Platform. It is not a substitute for expert astrophysical classification and should not be interpreted as population-level ZTF performance from the current benchmark alone.

## Training/evaluation data
The frozen production artifact is associated with benchmark_v0.2:
- 150 ZTF objects
- 15 classes
- 10 objects per class
- ALeRCE reference/weak labels

ALeRCE labels are benchmark/reference labels, not independent astrophysical ground truth.

## Outputs
Production inference can expose:
- class probabilities;
- calibrated probabilities when calibration is available;
- conformal prediction diagnostics;
- OOD diagnostics;
- model, artifact, feature-schema, and software provenance metadata.

Calibration, conformal prediction, OOD, and scientific-anomaly evidence are separate semantic channels.

## Scientific-anomaly boundary
The production baseline_v0.2 model does not claim to be a scientific-anomaly detector.

A high OOD score is not, by itself, evidence of an astrophysical anomaly. Scientific anomaly evidence is a separately versioned analysis mode and remains not_evaluated unless such an analysis supplies explicit evidence.

## Limitations
- The benchmark is small and balanced.
- ALeRCE labels are reference/weak labels rather than independent ground truth.
- No claim of full-ZTF population representativeness is made from this benchmark.
- Real-world OOD behavior and temporal degradation require independent validation.
- Probability quality depends on calibration coverage and similarity between inference data and the calibration/reference distribution.
- Exact historical CPVS selection reconstruction remains an external claim-specific unresolved question; it is not a product classification error.

## Safety and scientific interpretation
Predictions are decision-support signals for scientific analysis. Low-confidence, OOD, or diagnostically incomplete outputs require additional investigation rather than automatic scientific conclusions.

## Compatibility and lineage
The v0.2.0 scientific baseline and baseline_v0.2 model identity are immutable. Future model improvements must use a new model version and preserve compatibility or provide explicit migration rules.

The software package milestone v1.0.0 does not imply that the scientific model itself became v1.0; the two version lines are intentionally independent.