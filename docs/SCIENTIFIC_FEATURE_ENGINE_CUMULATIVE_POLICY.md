# Scientific Feature Engine — Cumulative Improvement Policy

The Scientific Feature Engine is a first-class scientific subsystem and follows the cumulative-learning lifecycle.

## Required baseline

For each meaningful feature-engine iteration, record where applicable:

- feature quality and scientific validity;
- determinism;
- runtime and feature-generation time;
- missing-data robustness;
- schema compatibility;
- provenance completeness;
- QC acceptance;
- inference compatibility;
- regression status.

## Feature acceptance

Adding a feature is not itself an improvement. The change must show evidence of scientific or engineering value and must not introduce leakage, nondeterminism, schema incompatibility, or unacceptable performance/resource regressions.

## Knowledge propagation

Feature-engine findings are written to the operational knowledge layer and carried into later model, benchmark, and API stages.

Changes to feature generation trigger the relevant Scientific Validation benchmarks under the permanent product-level gate.
