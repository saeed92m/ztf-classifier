# CIN LC-01 Controlled Pilot Protocol v0.1

**Status:** Protocol proposal; not executed  
**Source:** ZTF-CIN-ARCH-001 v1.0.0  
**Tracking:** [Issue #251](https://github.com/saeed92m/ztf-classifier/issues/251)

## 1. Research question

Do independent human assessments of ZTF light-curve morphology add measurable information beyond the existing machine-learning workflow for a declared sample population and task definition?

The pilot evaluates the usefulness and reliability of the annotation process. It does not claim new discoveries, model improvement or general performance across all ZTF objects.

## 2. Task scope

Initial task: LC-01 — Light Curve Assessment.

Initial response vocabulary, to be finalized and versioned: apparently regular; periodic-like; irregular; transient-like; sudden brightening; sudden dimming; complex/mixed behavior; uncertain / cannot determine.

This is an annotation vocabulary, not an astrophysical class taxonomy. The interface must allow abstention and optional confidence.

## 3. Sampling design

The sample should contain separate, documented streams:

1. Representative random sample from the eligible population.
2. Deliberately selected unusual/novel candidates.
3. Model-uncertain candidates.
4. Human–AI disagreement candidates, only after blind assessments are protected.
5. Independently validated control examples.

Maintain sampling probabilities and stream labels. Do not combine targeted and probability samples when estimating population-level metrics. Select a fixed sample size only after eligible population, expected effect, adjudication capacity and statistical power are assessed.

Every sample must have a pinned source manifest, selection seed/policy, inclusion/exclusion log and source-data checksum.

## 4. Presentation and blinding

- Hide model predictions and scores from ordinary participants where practical.
- Hide previous participants' answers.
- Randomize task order.
- Record UI and presentation version.
- Present enough context to interpret the light curve, including filter, time axis, units and quality caveats.
- Do not display image-artifact judgments in an LC-only task.
- Preserve missing data and quality flags; do not silently impute for display.
- Record when a task is not interpretable.

## 5. Independent controls and adjudication

Control examples require documented independent reference evidence and expert adjudication. ALeRCE reference labels alone must not be described as independent astrophysical ground truth.

The adjudication protocol must specify reviewer qualifications, evidence available, independent review, conflict handling and rationale. Expert decisions are stored separately from community responses.

## 6. Assignment policy

Each eligible task receives repeated independent assessments. The number of assignments is determined by pilot design and resource limits, not by a universal fixed-vote rule.

Prevent one contributor from dominating a task. Preserve contributor pseudonym, assignment policy, presentation version and timestamp. Do not reveal model output or earlier responses to ordinary contributors where practical.

## 7. Metrics

Annotation quality: agreement with independently adjudicated controls; per-category precision/recall where valid; inter-annotator agreement with uncertainty intervals; abstention rate and abstention correctness; confidence calibration; ambiguity and expert escalation rates.

Bias and robustness: differences by task stream; effects of presentation version/order; contributor experience effects; correlated errors and repeated-participant effects; coverage across source properties and morphology; selection bias between random and targeted samples.

Operational: task completion and abandonment; median completion time (descriptive only); ingestion failures and duplicate retries; end-to-end provenance completeness; cost per valid annotation.

Product activity metrics must not be interpreted as scientific quality.

## 8. Analysis plan

- Freeze task definition and policy versions before collection.
- Preserve raw responses.
- Exclude invalid submissions only through a documented, versioned QC rule.
- Report raw and QC-filtered results.
- Report disagreement distributions, not only majority labels.
- Evaluate task-specific reliability.
- Separate random-sample estimates from targeted-candidate analyses.
- Compare human assessments with model outputs without assuming either is correct.
- Do not train or update the production model during the pilot.
- If a later model experiment is proposed, create a separate dataset release and leakage-safe object-level split; exclude protected benchmark contamination.

## 9. Data governance

Before recruiting participants, approve privacy notice, consent, contributor pseudonymization, retention/deletion process, source-data licensing, derived asset rights, annotation license, attribution policy, security controls and incident process.

Do not collect unrelated browsing telemetry, device fingerprints or unnecessary personal data.

## 10. Stopping and acceptance criteria

The pilot may be declared operationally complete only when a task can be generated from a pinned sample; multiple independent assignments can be completed; contributions are validated and stored immutably; retries are idempotent; each contribution is traceable to source data and task version; consensus/disagreement can be reconstructed; expert adjudication can be recorded separately; and the dataset manifest can be reproduced.

Scientific usefulness is a separate gate. It requires predeclared thresholds justified by pilot design, independent reference evaluation, bias analysis and evidence that human assessments add information for the declared use case.

## 11. Open decisions before execution

- eligible source and release;
- photometry/visualization quality requirements;
- source identity and AOIC integration status;
- control sample and independent adjudication protocol;
- assignment count and sample size;
- contributor eligibility and consent;
- task duration and stopping rule;
- primary/secondary scientific metrics;
- retention and licensing.

**No pilot execution is claimed by this protocol.**
