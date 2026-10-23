# Project Glossary and Status Vocabulary

This glossary is normative for README, handbook, roadmap, API/CLI/GUI text, reports and Notion mirrors. When a term has multiple meanings in astronomy/ML, use the definition below or qualify the intended meaning.

## Product and data terms

- **Astronomical Data Analysis & Discovery Platform:** the complete product: ingestion, quality control, analysis, uncertainty, evidence, candidate workflows, review and reproducible outputs. Not synonymous with the classifier alone.
- **Source adapter:** versioned code that retrieves or parses a specific source/product and maps its metadata/semantics into the platform's input contract.
- **User-supplied data:** files or tables chosen by an astronomer. This is a core input mode, subject to supported-format and explicit schema/semantics checks.
- **Survey-neutral observation schema:** a common representation of observations that preserves the original source meaning, source identifiers, time semantics, passband, measurement type, units, uncertainty, quality flags and provenance. “Neutral” does not mean all surveys are scientifically interchangeable.
- **Object-level identity:** the complete stable identifier for an astronomical source. Splits, joins, deduplication and comparisons must operate at the source/object level, not at individual observation rows or physical row ordinals.
- **Provenance:** machine-readable record of source/version, retrieval, identifiers, hashes, schema mapping, transformations, filters/exclusions, software/environment, features, model/configuration, validation split, diagnostics and outputs.
- **Data contract:** versioned schema plus semantic constraints, units, allowed values, missingness/quality rules, compatibility requirements and error behavior.
- **Quality control (QC):** checks and flags for malformed values, non-finite measurements, uncertainties, cadence, duplicates, masks, passbands and other source-specific quality conditions. QC must report counts and named rules; it must not silently erase evidence.
- **Photometric measurement type:** the physical/logarithmic meaning of a value, such as flux or magnitude. Values of different kinds or units cannot be mixed without an explicit, tested conversion.
- **Time format / time scale:** distinct declarations. Format describes representation/reference convention (for example MJD or BTJD); scale describes time standard (for example UTC or TDB). Neither may be guessed from numeric magnitude alone.
- **Passband:** a survey/filter response label such as ZTF g/r, TESS, or an OGLE filter. Band mapping must be explicit and does not by itself make feature distributions equivalent.
- **Feature:** a derived numerical descriptor with a versioned definition, units/meaning, input requirements, missingness behavior and provenance.
- **Feature availability:** whether a feature can be validly computed from a particular input. Missing/inapplicable features must not be silently coerced into a model schema.
- **Taxonomy:** the exact class vocabulary and mapping used for labels, training, evaluation and predictions. Similar names across surveys do not prove equivalent labels.
- **Reference label / pseudo-label:** a label useful for comparison or training but not necessarily independent ground truth. ALeRCE labels in the frozen benchmark are reference/benchmark labels, not independent truth.
- **Independent ground truth:** labels supported by an independently justified process/source and not merely copied from the model, broker or benchmark being evaluated.
- **Frozen baseline:** a versioned model/data/schema/configuration accepted as a fixed comparator. It must not be silently modified to make a new test pass.
- **Model artifact:** complete inference bundle, including trained estimator, preprocessing, feature schema, class order/taxonomy, calibration, diagnostics, metadata and provenance needed to interpret results.
- **Domain compatibility:** evidence that the input domain (survey, units, bands, cadence, noise, labels and preprocessing) is compatible with the declared model task.
- **Cross-survey validation:** evaluation on a distinct survey/domain with source-backed provenance, compatible label definitions, leakage-safe splits and explicit limitations. Importing a second survey is not cross-survey scientific validation.

## ML and scientific-evidence terms

- **Classification:** assigning one or more declared classes to an input under a defined taxonomy.
- **Probability calibration:** agreement between predicted probabilities and empirical event frequencies under a stated evaluation distribution.
- **Confidence:** avoid using this word as a synonym for raw model probability unless calibrated meaning is explicit. State what is calibrated, on which data and under which assumptions.
- **Uncertainty:** a broader term for predictive uncertainty and limitations; report the specific method/quantity rather than a generic confidence badge.
- **Conformal prediction:** a method that can return a set of plausible labels with a coverage guarantee under stated exchangeability/assumption conditions. A set-valued output is not automatically a calibrated single-label probability.
- **Abstention / unknown:** explicit decision not to assert a class when evidence or compatibility is insufficient. Include a reason code; do not force a class.
- **Out-of-distribution (OOD):** an input that differs from the training/reference distribution according to a declared detector/score. OOD is not identical to scientific novelty or a physical anomaly.
- **Scientific anomaly:** a candidate with evidence of unusual scientific behavior under a defined analysis; requires domain-specific interpretation and review. It is not synonymous with a high OOD score.
- **Real/Bogus:** assessment of whether a detection is astrophysical or an artifact, distinct from astrophysical class classification.
- **Candidate ranking:** transparent ordering for triage based on stated evidence and weights. It is not a discovery claim and should preserve score components and limitations.
- **Leakage:** information from held-out/test objects, future observations, labels, or downstream outcomes influencing training, feature selection, calibration, thresholding or evaluation.
- **Object-disjoint split:** a split in which no source/object identity appears across train/validation/test partitions.
- **Temporal split:** training on an earlier time range and evaluating on a later range to test time transfer, with object identity overlap controlled.
- **Risk–coverage:** relationship between retained predictions/coverage after abstention and the error/risk on retained predictions.
- **Full-vs-batch equivalence:** check that processing the same full input or bounded batches yields the same object-level membership/results under the same rules.
- **Scientific gate:** predeclared evidence-based release criterion. Missing, skipped, failed or inconclusive required checks do not pass.
- **Fail-closed:** reject or block a claim/action if a required invariant or evidence is missing, rather than assuming success.

## Status vocabulary

- **Planned:** requirement described; implementation not demonstrated.
- **Implemented:** code is present; behavior may not yet be verified.
- **Import-supported:** source/file import and normalization pass pinned tests.
- **Analysis-supported:** declared analysis/features pass deterministic source-specific tests.
- **Model-compatible:** the exact model contract matches the input.
- **Scientifically validated:** the declared task/domain passes required independent/source-backed scientific gates.
- **Blocked / unresolved:** evidence is missing, contradictory or fails; reason and next evidence are recorded.
- **Deprecated:** no longer recommended; replacement and compatibility window are documented.
- **Open PR:** proposed change not yet merged; never call it shipped.
- **Release:** immutable, tagged/published artifact; verify exact tag/assets/checksums.
- **Current snapshot:** human-readable mirror pinned to an exact source revision/date. It is not current if the recorded SHA is stale.

## Fixed project references

- Product charter: [PROJECT_CHARTER_AND_SOURCE_OF_TRUTH.md](PROJECT_CHARTER_AND_SOURCE_OF_TRUTH.md)
- Current handbook: [HANDBOOK_CURRENT.md](HANDBOOK_CURRENT.md)
- Current state register: [PROJECT_STATE_REGISTER.md](PROJECT_STATE_REGISTER.md)
- Roadmap: [roadmap/PLATFORM_EXPANSION_ROADMAP.md](roadmap/PLATFORM_EXPANSION_ROADMAP.md)
- Scientific benchmark and gate: [SCIENTIFIC_VALIDATION_BENCHMARK.md](SCIENTIFIC_VALIDATION_BENCHMARK.md)
- Feature provenance: [FEATURE_PROVENANCE_CONTRACT.md](FEATURE_PROVENANCE_CONTRACT.md)
