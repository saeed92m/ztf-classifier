# Initial GitHub Ecosystem Gap Audit

Status date: 2026-10-22
Status: INITIAL SAMPLE ONLY — NOT AN EXHAUSTIVE ECOSYSTEM REVIEW
Scope: public GitHub repository search and read-only inspection of selected README, source, project metadata, and license files.

## Executive summary

The initial repository sample supports a clear distinction: several adjacent projects solve useful parts of the overall workflow, but the evidence reviewed so far does not show that any one of them is a drop-in replacement for this project's intended product. The most useful comparisons are complementary: a ZTF data viewer, specialized binary classifiers, light-curve visualization, periodicity-analysis utilities, and a broader astronomical data platform.

The audit does not yet establish a complete competitor inventory, full license compatibility for every candidate, comparative scientific performance, or a feature-by-feature code audit. Search results are candidate discovery, not proof of implementation quality.

## Initial inspected repositories

### 1. SNAD ZTF viewer
- Repository: https://github.com/snad-space/ztf-viewer
- Evidence inspected: README, LICENSE, pyproject.toml.
- Verified: README describes a ZTF Data Release light-curve viewer; documented setup includes Docker Compose and a local uv-based development path. The project metadata declares MIT licensing, version 2026.9.1, Python >=3.14, and a stack including Dash/FastAPI, pandas, Astropy, Astroquery, Plotly, and external catalog/service clients.
- Reusable design lessons: source/object visualization, catalog context, caching boundaries, explicit service configuration, and a scientist-facing viewer.
- Constraints: it is a viewer/service rather than evidence of a generic analysis engine. Its declared Python >=3.14 and dependencies do not directly match this project's pinned Python 3.11.16 baseline. Do not adopt dependencies without compatibility, footprint, and license review.

### 2. SNAD binary classifiers
- Repository: https://github.com/snad-space/snad-binary-classifiers
- Evidence inspected: README and search-indexed training scripts/notebooks.
- Verified: README describes classifiers for ZTF DR23 features, including real/bogus and supernova-vs-non-supernova use cases. Search-indexed training code uses scikit-learn RandomForestClassifier and train/test/cross-validation utilities; notebooks also show CatBoost usage.
- Reusable design lessons: keep real/bogus screening distinct from astrophysical class inference; record training population, label construction, split protocol, and evaluation metrics.
- Constraints: specialized classifiers on a predefined DR23 feature set are not a general user-facing platform. A root LICENSE file was not found at the exact path checked; license status must be confirmed before reuse or redistribution.

### 3. ZTF light-curve explorer
- Repository: https://github.com/phuijse/light_curve_explorer
- Evidence inspected: README.
- Verified: README describes a ZTF light-curve explorer using HoloViews and the ALeRCE API; it generates a static dashboard from a script and environment file.
- Reusable design lessons: lightweight visual exploration and fast sharing of plots.
- Constraints: the README alone does not establish current maintenance, scientific validation coverage, license compatibility, or support for general analysis workflows. Inspect source/tests/license before any adoption decision.

### 4. ZTF Light Curve Tools
- Repository: https://github.com/astrojoeg/ZTF-Light-Curve-Tools
- Evidence inspected: README.
- Verified: README describes a script that estimates a Lomb–Scargle false-alarm threshold through bootstrap resampling of ZTF time series, with a stated 10,000-resample procedure; other described functionality is noted as in development.
- Reusable design lessons: independently validate periodicity/statistical significance methods and preserve the sampling assumptions and randomization procedure.
- Constraints: this is a focused analysis utility, not a complete platform. Its current scientific implementation and tests need inspection before reuse.

### 5. SNAD binary-classifier and ZTF viewer ecosystem
These repositories are related but have distinct responsibilities: model training/classification versus interactive data exploration. This reinforces the architecture choice to separate scientific core, data adapters, visualization, and review workflows instead of forcing all responsibilities into one module.

### 6. SkyPortal
- Repository discovered: https://github.com/dannygoldstein/skyportal
- Evidence inspected: README excerpt only.
- Verified: README describes it as an astronomical data platform and points users to external project documentation.
- Next step: inspect architecture, workflows, license, maintenance, and operational requirements before making any implementation recommendation. No feature parity claim is made from the README excerpt.

### 7. TESS-ZTF Light Curve Classifier
- Repository: https://github.com/Chacon-Miguel/TESS-ZTF-Light-Curve-Classifier
- Evidence inspected: README only; it contains a project title and no substantive description in the fetched content.
- Conclusion: insufficient evidence for a technical recommendation. Inspect repository files and license before further conclusions.

## Initial gap matrix

| Area | Evidence from sample | Implication for ZTF Classifier | Next action |
|---|---|---|---|
| Object/light-curve visualization | SNAD viewer and light_curve_explorer focus on browsing/plotting | Preserve a distinct visualization layer over stable scientific services | Compare plot types, source context, performance, accessibility, and tests |
| Specialized model channels | SNAD repo separates real/bogus and supernova classification | Keep Real/Bogus separate from astrophysical classification | Audit current result contracts and ensure the UI communicates channel semantics |
| Periodicity validation | ZTF-Light-Curve-Tools documents bootstrap false-alarm thresholds | Add/reference tested known-answer periodicity checks when the supported analysis scope warrants it | Inspect algorithm, assumptions, license, and test coverage |
| General-purpose analysis | Sampled specialist tools do not demonstrate arbitrary-schema scientific analysis | Generic file import must not be described as generic scientific interpretation | Audit core schemas and define versioned adapters/feature backends |
| Reproducibility and provenance | Repositories expose different levels of metadata in the inspected excerpts | Compare manifests, stable IDs, hashes, model/data provenance, and deterministic exports | Inspect source/tests/docs across a broader sample |
| Desktop/offline packaging | SNAD viewer README primarily documents service/Docker deployment | Desktop installer and offline workflows remain a separate product requirement | Evaluate packaging alternatives without inheriting a server stack by default |
| Licensing and dependency fit | Viewer explicitly declares MIT and Python >=3.14; SNAD classifier root license path unresolved | Compatibility and license review are mandatory before reuse | Verify licenses and supported Python/runtime constraints per repository |

## Search coverage and limits

Searches included phrases related to ZTF light curves, ZTF classifiers, astronomical light-curve machine learning, astronomy time-series analysis, astronomical anomaly detection, ZTF machine learning, and astronomy data platforms. Results included, among others, SNAD ZTF viewer, SNAD binary classifiers, ZTF Light Curve Tools, light_curve_explorer, TESS-ZTF-Light-Curve-Classifier, and SkyPortal.

GitHub search is not exhaustive. The following areas still need deeper targeted search and inspection: AMPEL, Lasair/needle, BRAAI, SCoPe, cesium, broader survey brokers, public feature stores, and benchmark datasets such as StarEmbed ZTF_40k. Repository activity, license, test coverage, and source implementation should be checked directly before prioritizing any code reuse.

## Decisions

1. Do not copy code or add dependencies based on README descriptions alone.
2. Keep real/bogus, astrophysical classification, scientific anomaly evidence, OOD, uncertainty, and catalog context as separate channels.
3. Treat visualization and review workflow lessons as architectural input, not as proof that the current product already provides them.
4. Treat the current native 42-feature backend as a versioned model contract, not a universal feature schema.
5. Keep the v0.2.0 baseline immutable and CPVS exact reconstruction unresolved.
6. Continue the audit under Issue #210; this document is an initial evidence snapshot and must be updated as more repositories are inspected.


## Additional candidates inspected — 2026-10-22

### 8. Lasair4 alert broker
- Repository: https://github.com/lsst-uk/lasair4
- Evidence inspected: README and LICENSE.
- Verified: README describes Lasair as a UK alert-stream broker and transient-science platform, developed to serve Rubin LSST alerts while currently processing public ZTF alert streams. The repository's LICENSE file is Apache License 2.0.
- Reusable lessons: alert-stream ingestion, broker/query workflows, and user-facing transient-science services.
- Constraints: this is an operational alert broker/platform, not a drop-in local desktop scientific analysis engine. Deployment and operational requirements need separate review.

### 9. cesium time-series feature platform
- Repository: https://github.com/cesium-ml/cesium
- Evidence inspected: README, setup.py, LICENSE.txt.
- Verified: README describes a library for extracting features from raw time series, building ML models from those features, and predicting on new data. The source distribution builds a Cython extension for Lomb–Scargle functionality. LICENSE.txt is a 3-clause BSD license.
- Reusable lessons: a reusable time-series feature library and a clear feature-extraction-to-model workflow are relevant comparisons for the planned feature-backend architecture.
- Constraints: dependency/build compatibility, scientific feature definitions, license notices, and fit with the frozen v0.2.0 feature contract must be evaluated before adoption. No dependency is proposed by this audit alone.

## Updated initial conclusions

The broader sample now spans (a) specialized ZTF classifiers, (b) interactive ZTF viewers, (c) a general time-series feature/model library, and (d) an alert-stream transient-science platform. This supports a modular architecture with distinct ingestion adapters, versioned feature backends, analysis/model modes, visualization/review, and provenance. It does not prove that the current implementation already provides arbitrary-feature scientific analysis.

Potentially reusable ideas are architectural references only. Before implementing or importing code, inspect relevant source files, tests, data assumptions, dependency footprint, supported Python versions, license obligations, and scientific validation. The full repository inventory and prioritized gap matrix remain open under Issue #210.


## Independent-dataset execution gap — 2026-10-23

Source inspection confirms the current StarEmbed adapter supports acquisition, but not yet an end-to-end product prediction path from raw StarEmbed light curves. The registered benchmark runner expects a prepared table with `sourceid`, `class_str`, and `y_pred`; it computes evaluation metrics on predictions rather than generating them from raw data. The heavy scientific-validation workflow acquires StarEmbed and then proceeds to large CPVS source downloads, with no StarEmbed raw-light-curve inference step found in the inspected workflow.

This is a concrete capability gap, not evidence that the model failed. End-to-end validation remains blocked until the dataset schema/units and preprocessing are inspected, a versioned compatible feature/model path is established, split and OOD boundaries are preserved, predictions and provenance are recorded, and the benchmark evaluator is run. The frozen v0.2 42-feature contract must not be silently applied to incompatible data. A dedicated StarEmbed workflow should avoid coupling the independent dataset test to large CPVS downloads.
