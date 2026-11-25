# ZTF Classifier — Model Card

## Model identity

- Software release: v1.0.1 (immutable)
- Scientific baseline: v0.2.0 (immutable)
- Intended production model identity: `baseline_v0.2`
- Model family: XGBoost
- Feature schema: v0.2, 42 frozen features
- Historical cutoff: 59447.224132
- Expected original production artifact schema: 1.0

## Artifact availability

The original frozen `baseline_v0.2` production artifact has not been recovered or authenticated from the accessible repository, release assets, retained CI artifacts, or connected remote storage searches. See [Issue #282](https://github.com/saeed92m/ztf-classifier/issues/282).

The v1.0.1 package does not include model weights. A separate schema-1.1 lab-smoke artifact is not a production substitute. Do not rebuild or replace the original model and call it the frozen artifact.

The software contains artifact-loading and inference contracts. Their presence does not establish that the original model is available or that production inference can run on the current checkout.

## Intended use

When the original artifact is recovered and authenticated, the model is intended for research-oriented screening and classification of ZTF objects represented by the frozen 42-feature contract.

It is not a substitute for expert astrophysical classification. Performance on the small reference benchmark is not a claim about the full ZTF population.

## Training and evaluation reference

The frozen v0.2.0 benchmark is recorded as:
- 150 ZTF objects;
- 15 ALeRCE reference classes;
- 10 objects per class;
- 42 frozen features.

ALeRCE labels are reference/weak labels, not independent astrophysical ground truth.

## Outputs and semantics

The inference contract can expose class probabilities, calibration status, conformal diagnostics, OOD diagnostics, and provenance metadata when the required trusted artifact and compatible inputs are available.

Keep these channels separate:
- classification output;
- calibrated probability;
- conformal prediction set;
- OOD diagnostics;
- scientific-anomaly evidence.

The baseline does not claim to be a validated scientific-anomaly detector. A high OOD score is not, by itself, evidence of an astrophysical anomaly.

## DR24 boundary

The raw DR24 Explorer preserves source-native observations and provides diagnostic QC, provenance, and export. It does not generate the frozen v0.2.0 feature vector or run this model on DR24. DR24-to-v0.2 feature parity and source-specific time/photometry/QC contracts are not accepted.

## Limitations

- The benchmark is small and balanced.
- ALeRCE labels are weak/reference labels.
- Population-level ZTF performance is not established.
- Temporal and cross-survey generalization require independent validation.
- Probability quality requires an authenticated artifact and suitable held-out calibration data.
- CPVS historical selection reconstruction remains a separate unresolved research question.

## Lineage

The v0.2.0 scientific baseline and `baseline_v0.2` model identity are immutable. Any future model must receive a new version, model card, dataset manifest, split contract, and independent validation. It must not overwrite the original baseline.
