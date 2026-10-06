# ZTF Classifier — v1.0 Product Architecture Index

Canonical product: Astronomical Data Analysis & Discovery Platform.

Runtime flow: source data → ingestion → normalization/QC → scientific feature/context layers → analysis modes → uncertainty/calibration/OOD → candidate ranking → evidence/provenance → human/scientific validation → reproducible discovery outputs.

The v0.2.0 scientific baseline remains immutable. Classification uncertainty, calibration, conformal prediction, OOD, scientific anomaly evidence, catalog evidence, and explainability evidence are separate channels.

Scientific Validation is release-blocking at product level. Exact historical CPVS reconstruction is a separate claim-specific external evidence lane and remains unresolved.

Current next phase: user-facing workflows, independent scientific benchmarking, catalog/cross-match enrichment, discovery candidate workflows, human review, and future multimodal analysis.