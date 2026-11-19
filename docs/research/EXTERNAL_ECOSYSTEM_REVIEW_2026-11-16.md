# ZTF Classifier — External Ecosystem Review and Adoption Decisions

**Document ID:** ZTF-RESEARCH-ECOSYSTEM-2026-11-16  
**Review date:** 2026-11-16  
**Status:** Research review completed; implementation decisions are proposals pending normal engineering and scientific gates  
**Parent project:** ZTF Classifier  
**Scope:** 35 user-supplied GitHub repositories, pull requests, skills, and discussions  
**Baseline:** Preserve the v0.2.0 scientific baseline and existing product architecture

---

## 1. Executive decision

The review found useful methods and design patterns. It did not identify a reason to replace the current scientific core, its 42-feature contract, its XGBoost production baseline, or its fail-closed validation policy.

The highest-value outcomes are:

1. Define a canonical photometric-band registry and versioned input adapters.
2. Strengthen the ALeRCE and future multi-survey adapter boundary.
3. Keep Real/Bogus image vetting separate from astrophysical object classification.
4. Use BTSbot and braai as references for a future optional image-based analysis path.
5. Use the Harbor task proposal as a blueprint for controlled image-subtraction benchmarks, not as an existing validated benchmark.
6. Improve scientific artifact and experiment provenance. Consider ASDF only for use cases where its schema and array model add value.
7. Use astroML, Astroquery, and the ALeRCE client as references or optional integrations. Do not add all of them as mandatory runtime dependencies.
8. Keep large broker and image-processing infrastructures out of the initial CPU-first desktop product.

The current repository already records many of these directions in:

- `docs/ECOSYSTEM_REVIEW_PRODUCT_EXPANSION_2026-10-08.md`
- `docs/architecture/V1_PRODUCT_ARCHITECTURE.md`

This review supplements those records. It does not replace them.

## 2. Non-negotiable controls

- Do not change the frozen v0.2.0 benchmark, feature contract, class order, model artifact, or acceptance criteria as part of this review.
- Do not treat ALeRCE labels as independent astrophysical ground truth.
- Do not combine Real/Bogus, OOD, scientific anomaly, classification uncertainty, and class probability into one score.
- Do not treat human annotations or synthetic data as benchmark truth.
- Do not add a dependency only because an external project uses it.
- Record source version, retrieval time, schema, units, identifiers, transformations, and hashes for every adopted data path.
- Test old and new input schemas. Reject unknown or ambiguous units and band labels.
- Keep CPU-first operation as the default. GPU-based image models remain optional research extensions.
- Do not claim a capability is implemented until code, tests, documentation, and evidence confirm it.

## 3. High-value findings and proposed actions

### 3.1 Photometric band registry — priority P0

**Evidence:** NASA Fornax demo-notebooks PR #753 describes a real interface mismatch. The light-curve collector changed band names, while downstream notebooks still expected older names. The PR adds compatibility renames for stored files and supports current collector output.

**Proposed action:**

Create a versioned band registry and normalization contract. Each band record should include:

- Raw source label.
- Canonical band identifier.
- Survey and instrument.
- Effective wavelength, where known and sourced.
- Flux or magnitude unit.
- Magnitude system, where applicable.
- Error-column mapping.
- Time system and conversion requirements.
- Source adapter and schema version.
- Validity and conversion rules.

Preserve the original source label and raw value. Store normalized values as derived data with an explicit transformation record. Do not silently convert units or infer a band from an unknown string.

Add regression tests for historical and current labels from ZTF, Pan-STARRS, WISE, Gaia, and Rubin/LSST. Test missing bands, unknown labels, duplicate aliases, and incompatible units.

**Reference:** https://github.com/nasa-fornax/fornax-demo-notebooks/pull/753

### 3.2 Multi-survey and ALeRCE adapter — priority P1

**Evidence:** TOM Toolkit PR #1686 extends its ALeRCE DataService to use TAP/ADQL for LSST object searches while retaining REST access for supported ZTF and light-curve operations. It distinguishes `diaObject` and `ssObject`, handles MPC aliases, converts nJy to AB magnitude, maps Rubin bands to ugrizy, converts TAI to UTC, and adds tests for error handling and target creation.

The ALeRCE Python client README documents access to objects, detections, non-detections, forced photometry, stamps, classifiers, and catsHTM cross-matches. It also documents explicit survey selection for ZTF and LSST.

**Proposed action:**

- Define a stable survey-neutral adapter interface.
- Keep survey-specific identifiers and object types explicit.
- Keep ZTF OID, ALeRCE OID, LSST diaObjectId, ssObjectId, and MPC designation as distinct identifier types.
- Preserve raw timestamps and time scales. Store converted UTC values separately.
- Preserve original flux and magnitude values, units, zero points, and conversion metadata.
- Add idempotent ingestion tests and graceful remote-service failure handling.
- Add TAP/ADQL support only when an actual survey use case requires it.

Do not add TOM Toolkit as a runtime dependency. Reuse its interface and test lessons.

**References:**
- https://github.com/TOMToolkit/tom_base/pull/1686
- https://github.com/alercebroker/alerce_client

### 3.3 Real/Bogus as an independent analysis channel — priority P1

**Evidence:** braai is a ZTF real/bogus CNN that distinguishes astrophysical detections from subtraction artifacts. BTSbot uses image triplets and metadata for supernova identification and follow-up. These systems solve a different problem from 15-class light-curve classification.

**Proposed action:**

Keep a separate Real/Bogus stage and contract. A future stage may accept:

- Science image cutout.
- Reference image cutout.
- Difference image cutout.
- Image-quality and detector metadata.
- Source-detection and photometry metadata.

Its output must include model identity, input provenance, real/bogus score, calibration state, and quality flags.

Do not feed its score into the existing v0.2 model as a feature. Do not change the benchmark labels or class probabilities. Any future fusion must be a separately versioned model and evaluation.

BTSbot provides a reference for multi-modal image-plus-metadata workflows. braai provides a reference for real/bogus screening. Neither is a drop-in replacement for the current model.

**References:**
- https://github.com/nabeelre/BTSbot
- https://github.com/dmitryduev/braai
- https://github.com/Theodlz/bts-ml-ztf-summer-school

### 3.4 Controlled image-subtraction benchmark — research priority

**Evidence:** Harbor discussion #2067 proposes a CPU-only benchmark for difference imaging on real ZTF science/reference images with hidden injected sources. The proposal describes ten field pairs, 500 injected sources, crowded and saturated-star environments, a separate development field, neutral real-variable/transient sources, and a leakage audit. It calls for sub-pixel registration, spatially varying PSF modelling, Alard–Lupton or ZOGY subtraction, noise-weighted detection, artifact rejection, and uncertainty-aware flux measurement.

The discussion is a task proposal. It is not evidence that a released benchmark dataset or a completed scientific pipeline exists.

**Proposed action:**

Use the proposal as a design reference if the project later adds raw-image processing. Require:

- Immutable input images and SHA-256 manifests.
- Public development truth and hidden evaluation truth.
- Seeded injection with recorded PSF, flux, position, and noise.
- Neutral-source lists to avoid false credit or penalties.
- A leakage audit before evaluation.
- Separate completeness, purity, astrometric, and photometric-error metrics.
- Deterministic verification in an isolated process.
- CPU and memory limits that match the intended product.

Do not add this image-processing workload to the current light-curve audit or claim it validates the v0.2 classifier.

**Reference:** https://github.com/harbor-framework/terminal-bench-science/discussions/2067

### 3.5 Scientific methods and reference implementations — priority P1

**astroML** provides astronomy-focused statistical and machine-learning routines, dataset loaders, and examples. Use it as a method and tutorial reference. Compare individual methods against the project's scientific requirements before reuse.

**Astroquery** provides service-specific interfaces to online astronomical archives. Use it as an optional adapter source for catalog discovery and cross-match workflows.

**ASDF** provides hierarchical YAML metadata, binary arrays, schema validation, memory mapping, and compression. Evaluate it for portable scientific bundles or complex model metadata. Keep Parquet for tabular light curves and JSON for current CLI contracts unless a benchmark proves a better format is needed.

**ccdproc** provides CCD reduction tools with error propagation and bad-pixel tracking. It is relevant only if raw optical/IR image reduction enters the product scope.

**References:**
- https://github.com/astroML/astroML
- https://github.com/astropy/astroquery
- https://github.com/asdf-format/asdf
- https://github.com/astropy/ccdproc

### 3.6 Broker and discovery-platform architecture — reference only

Kowalski, Fritz, and the Fink Science Portal show mature patterns for API-driven archives, alert ingestion, indexed search, user-defined filters, collaborative review, active learning, and candidate presentation.

Their infrastructure choices include MongoDB, Kafka, Dask, HBase, and multi-service deployments. These are not requirements for this project.

**Proposed action:**

Reuse the architectural patterns only where justified:

- Stable API contracts.
- Search indexes suited to actual query patterns.
- Explicit candidate and review states.
- Human review with provenance.
- Optional alert-stream adapters.
- Fine-grained access control if multi-user collaboration is implemented.

Do not clone their infrastructure or introduce a distributed broker stack into the initial desktop application.

**References:**
- https://github.com/skyportal/kowalski
- https://github.com/fritz-marshal/fritz
- https://github.com/astrolabsoftware/ztf.fink-portal.org

### 3.7 Physical light-curve modelling and augmentation — research only

**ztfparsnip** retrains Parsnip for ZTF and describes augmentation with redshift changes, K-corrections, noise, time perturbations, and sampling changes.

**Proposed action:**

Evaluate template-based physical light-curve modelling as an independent research mode for suitable transient classes. Keep synthetic augmentation confined to training. Record the parent object, transformation parameters, random seed, and generated-child identity. Keep parent objects together across train/validation/test splits to prevent leakage.

Do not use augmented samples to inflate the frozen benchmark or to claim independent validation.

**Reference:** https://github.com/simeonreusch/ztfparsnip

### 3.8 Forced photometry and multi-object retrieval — optional data tools

- **fpbot** provides a ZTF forced-photometry workflow based on ztfquery and related tools. Its README requires IPAC access and a MongoDB instance; AMPEL access is optional.
- **ZTFMultiObjectTool** documents a manual IRSA multi-object search workflow and a method to retain one light curve with the most epochs per source and filter.
- **ALeRCE client** already offers a more direct programmatic path for several object and light-curve operations.

**Proposed action:**

Use these tools to investigate source identity, photometry coverage, and acquisition edge cases. Do not make fpbot or MongoDB mandatory. Prefer the simplest authorized source that meets the data contract. Preserve every returned row and record the grouping rule; never select the longest light curve without documenting the scientific reason.

**References:**
- https://github.com/simeonreusch/fpbot
- https://github.com/ra1nL/ZTFMultiObjectTool
- https://github.com/alercebroker/alerce_client

### 3.9 Future multi-messenger analysis — research roadmap

GW_AGN_watcher combines LVK HEALPix sky maps, ZTF alerts, AGN catalogs, temporal and spatial filters, classifier scores, host association, and candidate ranking.

**Proposed action:**

Treat gravitational-wave counterpart search as a future independent discovery workflow. A possible adapter may ingest a versioned HEALPix probability map and rank ZTF candidates by sky probability, time consistency, distance posterior, host association, and independent photometric evidence.

Keep this separate from the current classifier benchmark. Do not claim a validated multi-messenger capability until independent event-level tests exist.

**Reference:** https://github.com/Hemanthb1/GW_AGN_watcher

## 4. NVIDIA skills review

The three supplied NVIDIA skills were inspected at the exact commit IDs in the supplied URLs.

| Skill | Domain | Assessment |
|---|---|---|
| `tao-finetune-clip` at `d7e1e2c728579ad38174443ef22382d0fb4615b5` | CLIP image/text embedding, retrieval, zero-shot classification, fine-tuning and deployment | Possible future image-stamp embedding experiment. Requires Docker and NVIDIA Container Toolkit. Not a CPU-first core dependency. |
| `tao-train-reid` at `894f2d7dfee49085e84e21c1aad2513bc44a5b6d` | Person re-identification across camera views | Not relevant to astronomical object classification. Do not adopt. |
| `tao-run-deft-pas` at `029363a2023c0b24b1a75ddbeac11cd286d74afb` | Iterative CLIP/SigLIP retrieval improvement using attribute-gap analysis, mining, retraining and KPI stopping | The orchestration ideas may inform reproducible experiments. The workflow itself is for image/text retrieval and requires supported GPU execution. Do not use as the astronomical model pipeline. |

Useful process patterns from the DEFT skill:

- Schema-validated experiment configuration.
- Deterministic stage boundaries.
- Resumable disk-backed run state.
- Explicit platform selection.
- History-aware sample selection.
- Evaluation after each iteration.
- Defined stopping conditions.
- Separate control and execution environments.

These patterns can inform future ZTF experiment orchestration. They do not justify importing TAO, CLIP, ReID, or GPU infrastructure.

Licensing and version checks are required before copying any code or skill content. The supplied CLIP skill declares Apache-2.0. The supplied DEFT skill declares Apache-2.0 AND CC-BY-4.0. The supplied ReID skill declares Apache-2.0.

**References:**
- https://github.com/NVIDIA/skills/tree/d7e1e2c728579ad38174443ef22382d0fb4615b5/skills/tao-finetune-clip
- https://github.com/NVIDIA/skills/tree/894f2d7dfee49085e84e21c1aad2513bc44a5b6d/skills/tao-train-reid
- https://github.com/NVIDIA/skills/tree/029363a2023c0b24b1a75ddbeac11cd286d74afb/skills/tao-run-deft-pas

## 5. Remaining supplied resources and disposition

| Resource | Finding | Decision |
|---|---|---|
| `indomiekwah/ztf-classifier` | Student project using a shared Python package, 1D-CNN/GRU, ALeRCE light curves, three macro classes, and a Streamlit interface. | Review code patterns if needed. Do not merge its model or taxonomy into the frozen baseline. |
| `datacarpentry/astronomy-python` | The repository states that the curriculum is retired and archived. | Learning reference only. |
| `casacore/casacore` | C++ libraries for radio-astronomy data processing with substantial native dependencies. | Out of scope for optical ZTF light-curve core. |
| `astroML/sklearn_tutorial` | The repository explicitly says the tutorial is extremely out of date. | Do not use as a current implementation guide. |
| `mpi-astronomy/awesome-astro-datascience` | Curated astronomy data-science books, courses, repositories, and community resources. | Keep as a discovery index, not a software dependency. |
| `spacetelescope/astronify` | Astronomical data sonification, including time-series and light-curve use cases. | Optional accessibility and exploratory UX feature. |
| `apace7/local_volume_database` | Versioned astronomy catalogs in CSV, FITS, and ECSV, with release and DOI citation practices. | Reuse release/provenance practices for future catalog exports. |
| `taka-tanaka-zz/astronomy-to-data-science` | Career-transition resource, not an astronomy software component. | No product integration. |
| `russell-archer/ACPLogAnalyzer` | Windows tool for read-only analysis of telescope-control logs and observing metrics. | Not part of the public-ZTF data core. |
| `acceleroto/AstroFlatAnalyzer` | Desktop FITS flat-frame illumination and vignetting analysis. | Separate calibration utility; not a light-curve classifier dependency. |
| `zuds-survey/zuds-pipeline` | Image coaddition, subtraction, forced photometry, source detection, and alerts; requires external image-processing tools and a database. | Future raw-image research only. |
| `simeonreusch/ztfnuclear` | Repository describes analysis of a ZTF nuclear-transient sample. | Potential science use case; insufficient README detail for a software adoption decision. |
| `emirkmo/GeminiReductionsZTF` | README describes an old, minimally maintained IRAF/Python 2.7 reduction workflow and warns that it is barely used. | Do not adopt. |
| `alercebroker/ztf_explorer` | Nuxt-based ZTF Explorer front end. | UX reference only; inspect current status and license before reuse. |

## 6. Think-tank conclusions by expert role

The 16-role review reached the following cross-disciplinary conclusions:

1. **Chief Scientist:** Preserve the distinction between astrophysical class, real/bogus status, OOD, anomaly evidence, and uncertainty.
2. **ZTF Survey/Data Specialist:** Treat survey, release, object ID, filter, time scale, and photometry provenance as explicit data contracts.
3. **Transient and Variable-Object Astrophysicist:** Keep the current taxonomy stable. Add specialist science workflows as separate analysis modes.
4. **Astronomical Statistics Specialist:** Require uncertainty-aware transformations, time-aware validation, and independent evaluation for every new method.
5. **Astroinformatics/Data Engineer:** Use adapters and bounded data access. Do not introduce a distributed database without measured need.
6. **Cross-Matching Specialist:** Store match method, separation, candidate alternatives, catalog release, and retrieval provenance.
7. **Machine-Learning Scientist:** Evaluate image models and physical models as separate experiments. Do not replace the frozen XGBoost baseline by assumption.
8. **Benchmark/Validation Scientist:** Use hidden injections, neutral-source lists, leakage checks, fixed samples, and independent verifiers for future image benchmarks.
9. **Software Architect:** Extend through versioned interfaces and modules. Avoid a monolithic broker architecture.
10. **Backend Engineer:** Implement survey adapters, band normalization, and error handling behind stable contracts.
11. **MLOps/Security Engineer:** Pin model, dataset, skill, container, and dependency versions. Treat untrusted model checkpoints as untrusted input.
12. **QA/Reliability Engineer:** Add contract, compatibility, regression, failure-path, and deterministic tests.
13. **Scientific UX Designer:** Expose provenance, data quality, uncertainty, and model evidence in the Object Explorer.
14. **Product Manager:** Prioritize robust data contracts and the independent desktop product before GPU-heavy extensions.
15. **Scientific Documentation Specialist:** Record source status, license, version, adoption decision, and limits for every external component.
16. **Independent Red Team:** Challenge hidden leakage, false confidence, unit mismatches, object identity errors, and unsupported claims.

## 7. Prioritized implementation backlog

| Priority | Proposed work | Acceptance evidence |
|---|---|---|
| P0 | Photometric Band Registry and alias tests | Raw labels preserved; canonical mapping versioned; unknown labels fail closed; old/new fixtures pass |
| P0 | Survey-neutral object identity contract | Identifier types remain distinct; object-level lineage tests pass |
| P1 | ALeRCE/TAP adapter design | Contract tests for query, pagination, missing results, service failure, units, and time scales |
| P1 | Real/Bogus extension contract | Independent schema, model identity, calibration and evaluation; no change to v0.2 |
| P1 | External catalog cross-match evidence | Separation, method, source release, alternatives, and provenance are recorded |
| P1 | Reproducible experiment-run manifest | Input hashes, code revision, environment, seed, configuration, outputs, and stopping rule are recorded |
| P2 | Image-subtraction benchmark design | Injection truth, neutral sources, leakage audit, hidden evaluation, and deterministic verifier |
| P2 | Optional image-stamp embedding experiment | CPU/GPU cost measured; independent split and benchmark; no baseline contamination |
| P2 | ASDF format evaluation | A real use case and benchmark show value beyond current Parquet/JSON artifacts |
| P3 | Multi-messenger GW/AGN analysis mode | Independent scientific specification and event-level validation |

No code change to the frozen scientific pipeline is authorized by this research review alone.

## 8. Explicit non-adoption decisions

Do not add the following to the current core:

- NVIDIA TAO Toolkit, CLIP, ReID, or DEFT runtime.
- MongoDB, Kafka, HBase, Dask, or a full broker stack.
- casacore radio-astronomy libraries.
- IRAF/Python 2 reduction workflows.
- A mandatory forced-photometry service with external credentials.
- A new model that replaces the v0.2 production artifact.
- A single combined score for OOD, anomaly, real/bogus, and class confidence.

A future proposal may revisit these decisions with measured requirements and a separate acceptance review.

## 9. Evidence limits and follow-up

- The supplied GitHub pages and README files were inspected. A README review does not replace a full source-code, dependency, security, or license audit.
- TOM Toolkit PR #1686 describes 101 tests and live ALeRCE TAP checks. Its current merge status was not established by this review snapshot.
- NASA Fornax PR #753 was shown as awaiting review and not deployed when inspected. Recheck before relying on it as an upstream merged implementation.
- Harbor discussion #2067 is a closed task proposal. Do not treat it as a released dataset or completed benchmark.
- The NVIDIA skills were inspected at the exact commit IDs supplied by the user. Do not silently substitute a newer version.
- Several small or older repositories provide limited implementation detail. Their inclusion in the inventory is not an endorsement.

## 10. Next action

The next operational step remains the local scientific artifact audit. Run it from the intended project checkout and preserve its complete stdout, stderr, exit code, and generated artifact paths:

```bash
cd ~/projects/ztf-classifier
python scripts/audit_scientific_artifacts.py
```

Do not modify scientific artifacts before reviewing the audit output. The CPVS discrepancy remains a separate scientific validation blocker until its root cause is supported by reproducible evidence.
