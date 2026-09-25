# Scientific Validation Roadmap

Scientific validation is a permanent Product-Level Gate for the final Astronomical Data Analysis & Discovery Platform.

## Stage V0 — Registry foundation

- [x] Versioned Benchmark Registry
- [x] Machine-readable benchmark manifests
- [x] Deterministic table runner
- [x] JSON + Markdown validation reports
- [x] SHA-256 input evidence
- [x] Explicit ground-truth/reference separation
- [x] Release-blocking regression comparison

## Stage V1 — Benchmark adapters

- [ ] StarEmbed ZTF_40k adapter and reproducible subset retrieval
- [ ] ZTF periodic-variable classification release (~730k) adapter
- [ ] historical ZTF periodic-variable catalog (~781k) adapter
- [ ] pinned ZTF DR24 source-backed adapter
- [ ] ALeRCE API/TAP independent-reference adapter

Each adapter must preserve source/version/DOI/retrieval date/object IDs/hashes/schema/taxonomy/split/leakage/preprocessing/provenance.

## Stage V2 — Leakage and scientific integrity

- [ ] object overlap and duplicate-object audits across all benchmark populations
- [ ] target-leakage audit
- [ ] future-data/temporal leakage audit
- [ ] benchmark-trained-artifact audit
- [ ] preprocessing compatibility audit
- [ ] deterministic feature-generation audit
- [ ] schema compatibility audit
- [ ] provenance completeness audit
- [ ] failure-code correctness audit

Any unresolved required check blocks release.

## Stage V3 — Full metric and failure analysis

For applicable benchmarks:

- [ ] accuracy and balanced accuracy
- [ ] macro/weighted precision, recall, F1
- [ ] per-class metrics and confusion matrix
- [ ] log loss and Brier score
- [ ] calibration/reliability diagnostics
- [ ] OOD metrics
- [ ] coverage/rejection
- [ ] false-accept/false-reject analysis
- [ ] QC acceptance rate
- [ ] inference reproducibility
- [ ] resource/latency evidence where relevant

## Stage V4 — Product integration

- [ ] validation service integrated with the application layer
- [ ] Benchmark Registry exposed through scientific operations APIs
- [ ] Scientific Validation Dashboard/Report integrated into Workbench
- [ ] release evidence generated automatically
- [ ] benchmark regression status visible per release
- [ ] out-of-domain scope and known failure cases visible to users

## Stage V5 — CI/release operations

- [x] registry contract validation in ordinary CI
- [ ] scheduled heavy benchmark execution
- [ ] manual release-candidate benchmark execution
- [ ] regression artifacts retained as release evidence
- [ ] release workflow consumes scientific validation status
- [ ] no final release can bypass the scientific gate

## Permanent change-trigger policy

Relevant benchmarks must rerun after changes to:

- feature generation;
- preprocessing;
- model or model artifact;
- inference;
- calibration;
- conformal prediction;
- OOD/anomaly handling;
- normalization;
- scientific API contracts.

Benchmark regressions are release-blocking until reviewed and dispositioned.

## Initial source registry

The permanent source set is:

1. StarEmbed ZTF_40k
2. ZTF periodic-variable classification release (~730k objects)
3. historical ZTF periodic-variable catalog (~781k objects)
4. pinned ZTF DR24 source-backed subset
5. ALeRCE API/TAP as an independent reference system

The benchmark source data remains external to Git; Git stores the contracts, manifests, hashes, configurations, and reports.
