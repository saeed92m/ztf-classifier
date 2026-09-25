# ZTF Classifier — Data Card

## Dataset identity
- Benchmark: benchmark_v0.2
- Objects: 150
- Classes: 15
- Objects per class: 10
- Feature schema: v0.2, 42 frozen features
- Source: targeted ZTF light curves acquired through the ALeRCE interface
- Labels: ALeRCE reference/weak labels

## Intended use
The benchmark is intended for reproducible software validation, model-development regression tests, and controlled scientific experiments.

It must not be presented as a representative sample of the full ZTF population.

## Composition
The benchmark contains the 15 frozen classes used by the v0.2 scientific baseline: SNIa, SNIbc, SNII, SLSN, QSO, AGN, Blazar, CV/Nova, YSO, LPV, E, DSCT, RRL, CEP, and Periodic-Other.

## Collection and provenance
The project uses targeted/lazy acquisition rather than requiring the complete ZTF data release in Git. Acquisition metadata, source schema information, and reproducibility manifests are retained with derived artifacts where available.

## Quality and known limitations
- ALeRCE labels are not independent astrophysical ground truth.
- The benchmark is intentionally small and balanced.
- Missing observations, photometric quality, source-system differences, and class-definition ambiguity can affect downstream performance.
- Temporal and population-level generalization require larger independent validation datasets.

## Governance
Raw/source data and derived analysis products must remain distinguishable. Future external-source ingestion must preserve source provenance, licensing, attribution, and terms-of-use metadata.

## Versioning
This card describes benchmark_v0.2 and the immutable scientific baseline v0.2.0. Changes to scientific composition require a separately versioned dataset contract.
