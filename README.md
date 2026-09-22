# ZTF Classifier

A CPU-oriented machine-learning research pipeline for classification of astronomical transient and variable objects using public Zwicky Transient Facility (ZTF) light-curve data.

## Project status

**Version:** v0.2.0
**Status:** Validated research prototype / reproducible benchmark pipeline

The v0.2 core pipeline is finalized. It includes feature extraction, multiclass classification, probability calibration, conformal prediction, out-of-distribution (OOD) scoring, and historical/temporal evaluation.

The current benchmark contains 150 ZTF objects across 15 ALeRCE classes. ALeRCE classifications are used as benchmark labels and are not treated as independent ground truth.

## Scientific objective

The project investigates whether public ZTF light curves can be used to construct a reproducible CPU-oriented classifier that provides:

- multiclass object classification;
- class probabilities;
- calibrated confidence estimates;
- set-valued predictions through conformal prediction;
- anomaly / out-of-distribution scores;
- reproducible historical and temporal evaluation.

The intended long-term system is designed for scalable transient and variable-source screening without requiring the full ZTF DR24 archive to be downloaded locally.

## Data strategy

The project uses targeted ZTF light-curve retrieval rather than downloading the complete DR24 catalog.

The current benchmark dataset was acquired through the ALeRCE ZTF interface and cached locally as per-object Parquet light curves.

The project is designed around lazy / targeted access so that the full DR24-scale data volume is not required for development or experimentation.

## Benchmark dataset

Current v0.2 benchmark:

- Objects: **150**
- Classes: **15**
- Objects per class: **10**
- Label source: **ALeRCE**
- Light curves: ZTF
- Bands: g and r where available
- Benchmark labels: weak / reference labels, not independent ground truth

Classes:

- SNIa
- SNIbc
- SNII
- SLSN
- QSO
- AGN
- Blazar
- CV/Nova
- YSO
- LPV
- E
- DSCT
- RRL
- CEP
- Periodic-Other

## Feature engineering

The frozen v0.2 model uses **42 features**.

The final feature groups are:

1. Cross-band features
2. Observation-quality features
3. Periodicity features
4. Photometric-level features

The frozen feature definition is stored in:

```text
reports/tables/final_feature_set_v0.2.parquet
