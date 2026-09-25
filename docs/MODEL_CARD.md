# ZTF Classifier — Model Card

## Model identity
- Software milestone: 0.4.0
- Scientific baseline: v0.2.0
- Production model version: baseline_v0.2
- Model family: XGBoost
- Feature schema: v0.2, 42 frozen features
- Artifact schemas: 1.0 and 1.1

## Intended use
The model is intended for research-oriented screening and classification of ZTF transient/variable objects represented by the project's feature contract.

It is not a substitute for expert astrophysical classification and should not be interpreted as population-level ZTF performance from the current benchmark alone.

## Outputs
Production inference can expose:
- raw class probabilities;
- temperature-calibrated probabilities when calibration is available;
- conformal prediction diagnostics;
- OOD/anomaly diagnostics;
- model, artifact, and feature-schema provenance metadata.

Calibration, conformal prediction, and OOD diagnostics are separate components. Availability of one does not imply availability of the others.

## Training/evaluation data
The frozen production artifact is associated with benchmark_v0.2 and its persisted provenance metadata. The benchmark contains 150 objects across 15 classes.

## Limitations
- Small benchmark size.
- Reference/weak labels from ALeRCE rather than independent ground truth.
- No claim of full-ZTF population representativeness.
- Real-world OOD behavior and temporal degradation require independent validation.
- Probability quality depends on calibration coverage and similarity between inference data and the calibration/reference distribution.

## Safety and scientific interpretation
Predictions should be treated as decision-support signals for scientific analysis. Low-confidence, OOD, or diagnostically incomplete outputs require additional investigation rather than automatic scientific conclusions.

## Compatibility
The v0.2.0 scientific baseline and baseline_v0.2 model identity are immutable. Future model improvements must use a new model version and preserve compatibility or provide explicit migration rules.
