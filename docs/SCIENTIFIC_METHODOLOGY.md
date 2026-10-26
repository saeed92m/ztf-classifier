# ZTF Classifier — Scientific Methodology

## Scope

The platform analyzes public ZTF observations with explicit provenance, schema, temporal, leakage, and evidence boundaries.

## Immutable baseline

The v0.2.0 benchmark contains 150 objects across 15 ALeRCE reference classes, 42 frozen features, and an XGBoost baseline model. ALeRCE labels are benchmark/reference labels, not independent astrophysical ground truth.

## Evidence

Benchmark performance, external catalog/reference agreement, source-backed reproduction, OOD behavior, failure analysis, and human/scientific validation are distinct evidence types.

## Diagnostic semantics

Classification uncertainty, calibration, conformal prediction, OOD, and scientific anomaly are separate concepts. A high OOD score is not automatically an astrophysical anomaly.

## CPVS boundary

The immutable published membership reference contains 730,184 objects from a parent table with 781,602 rows. The latest source-backed run [#40397098709](https://github.com/saeed92m/ztf-classifier/actions/runs/40397098709) reports 741,788 candidates, all 730,184 published members present, 11,604 candidate-only objects, and zero published-only IDs. The derivation and independent membership audit did not pass exact reproduction; the workflow correctly retained `UNRESOLVED`. Parent Table 2 SHA-256 is `0f3ca5d4e71f674c38b3c08553c12cca0c32d2d31f776166ab29ce80a75cf138`. The prior run #38121913146 reported 741,786 / 11,602 and is superseded for current reporting; the two-ID shift between runs remains unexplained. The four-field predicate is diagnostic only and does not prove the publisher's historical rule.

### CPVS report crosswalk contract

The published Table 4 has both a ZTF object-name column (`ZTF`) and its own numeric internal `ID`. Membership reporting must join by normalized ZTF object name to the parent Table 2 object-name field (`ID`) and map that name to parent `Seq`/SourceID. Never compare Table 4's numeric `ID` directly with parent `Seq`. For report inputs, the parent metadata export must include `ID,Seq,gmag,rmag,Per-g,Per-r`; an export containing only `Seq` and the four metrics cannot support the official name crosswalk unless a separate verified crosswalk is joined. Record exact query URLs, retrieval timestamps, and hashes.

## Reproducibility

Scientific claims require source identity, retrieval/version information, object identifiers, hashes, schemas, taxonomy, temporal/leakage controls, and retained evidence artifacts.

## CPVS parallel experiment decision

The project compares (A) source-backed reconstruction/Jupyter processing and (B) provenance-rich discrepancy reporting. Neither is preselected. A matching count alone is insufficient; compare identifier integrity, reproducibility, per-object inclusion/exclusion reasons, false inclusion/exclusion against an explicit reference, invalid-value handling, and independent source-backed astronomical inputs. See [the experiment plan](https://github.com/saeed92m/ztf-classifier/blob/experiment/cpvs-jupyter-reconstruction-20261025/docs/experiments/CPVS_PARALLEL_RESOLUTION_EXPERIMENT_PLAN_2026-10-25.md).