# ZTF Classifier — Model Card

## Model identity

- Software release at this project snapshot: **v1.0.1** (published; immutable)
- Scientific baseline: **v0.2.0** (immutable)
- Production model version: **baseline_v0.2**
- Model family: XGBoost
- Feature contract: `final_feature_set_v0.2`, 42 frozen features
- Historical cutoff: MJD 59447.224132
- Frozen production artifact schema: **1.0**
- Later diagnostic/artifact schema: **1.1**; not a substitute for the frozen production artifact

Software release version, scientific baseline, model version, feature schema, CLI/API output schema, and model-artifact schema are separate version domains.

## Intended use

The model is intended for research-oriented screening and classification of ZTF transient and variable objects represented by the frozen feature contract.

It is one component of the Astronomical Data Analysis & Discovery Platform. It is not a substitute for expert astrophysical classification. Results from the current benchmark must not be interpreted as population-level ZTF performance.

## Training and evaluation data

The frozen v0.2.0 benchmark contains:

- 150 ZTF objects
- 15 classes
- 10 objects per class
- ALeRCE reference/weak labels

ALeRCE labels are benchmark/reference labels. They are not independent astrophysical ground truth.

The benchmark is small and balanced. It is not representative of the full ZTF population.

## Feature contract

The frozen production model uses 42 features from `final_feature_set_v0.2`. Do not add, remove, reorder, or reinterpret these features in the frozen baseline. A future feature contract requires a new version, provenance, regression coverage, and scientific validation.

## Outputs

The production inference contract can expose class probabilities and, where supported by the loaded artifact, calibrated probabilities, conformal prediction diagnostics, OOD diagnostics, and model/feature/artifact provenance.

Calibration, conformal prediction, OOD, data adequacy, and scientific-anomaly evidence are separate semantic channels.

## Scientific-anomaly boundary

The frozen `baseline_v0.2` classifier is not, by itself, a scientific-anomaly detector.

A high OOD score does not prove an astrophysical anomaly. Scientific anomaly analysis requires a separate, versioned method and independent evaluation. Until that evidence exists, the scientific-anomaly state must remain not evaluated.

## Artifact provenance and availability

The frozen production artifact is expected at:

`runs/model_baseline_v0.2_production/artifact/`

Its artifact schema is 1.0. A read-only local audit script is available at `scripts/audit_scientific_artifacts.py`. The audit checks declared paths and internal manifest/file hashes. It does not authenticate the artifact against an independently pinned original hash or establish scientific performance.

As of 2026-11-12, the local WSL audit output has not been reviewed in this status snapshot. Therefore the original production artifact remains **UNRECOVERED / NOT AUTHENTICATED** from the accessible evidence. Do not infer availability from the presence of the audit script or a successful test fixture.

The separate 2026-10-27 lab-smoke artifact is a different run and uses schema 1.1. It is not eligible for production inference and must not be copied, symlinked, or renamed into the frozen production path.

## Limitations

- The benchmark is small and balanced.
- ALeRCE labels are reference/weak labels, not independent ground truth.
- The benchmark does not establish population-level ZTF performance.
- Temporal degradation and real-world OOD behavior require independent validation.
- Probability quality depends on calibration coverage and similarity between inference data and the calibration/reference distribution.
- DR24 HATS raw data are not automatically compatible with the frozen v0.2 feature/model contract.
- Exact historical CPVS selection reconstruction remains a separate unresolved research question. It is not evidence of classifier accuracy or failure.

## Safety and scientific interpretation

Predictions are decision-support signals. Low-confidence, OOD, or diagnostically incomplete outputs require further investigation. A prediction, model score, catalogue non-match, or anomaly flag must not be presented as a confirmed discovery.

## Compatibility and lineage

The v0.2.0 scientific baseline and `baseline_v0.2` model identity are immutable. Future model improvements must use a new model version, preserve lineage, and provide explicit compatibility and migration rules.

The software release is v1.0.1. This release identifier does not change the scientific model version.
