# CPVS VizieR separator-row parser failure — 2026-11-04

## Finding

A fresh source-backed CPVS run on 2026-11-02 re-derived 741,786 candidates from the archived g/r photometry. The expected published membership count is 730,184. The 11,602-object difference remains.

The same run did not complete the independent published-membership audit. The VizieR mirror requests timed out. The fallback table parser then interpreted a dashed separator row (----------------------) as a published ZTF name and failed the Table 2 name-to-Seq crosswalk. The selection diagnostic failed on the same separator value.

Evidence:
- Full source-backed run: https://github.com/saeed92m/ztf-classifier/actions/runs/41417144949
- Job: 125183681255
- Parent SHA-256: 0f3ca5d4e71f674c38b3c08553c12cca0c32d2d31f776166ab29ce80a75cf138
- Parent evidence SHA-256: a7d8c6327aba75c07e091906854a632c640a4a40955d47b00d0957a39722c4a7
- The derivation reported 741,786 candidates against an expected 730,184 and removed zero candidates through its finite/nonzero magnitude guard.

## Change in this branch

The shared read_vizier() parser now rejects rows where every non-empty field consists only of hyphens. Both the four-field audit and diagnose_cpvs_selection.py use this parser.

Regression tests cover:
1. A VizieR Table 4 header, dashed separator row, and one valid data row.
2. The Table 4 ZTF-name to Table 2 Seq membership crosswalk with a separator row.

## Scientific boundary

This is a parser repair. It does not change:
- CPVS SNR thresholds or selection logic;
- the four-field metadata diagnostic;
- the published reference definition;
- v0.2.0 features, model, benchmark, or class order;
- any scientific acceptance criterion.

A passing parser test does not prove exact CPVS membership. The next step, after ordinary CI passes, is to run the crosswalk against the retained 6.9 MB frozen membership artifact. Do not repeat the multi-gigabyte source acquisition until this bounded check passes. A separate explicit source-backed run is required to validate the corrected acquisition path.

## Current disposition

- Parser root cause: identified.
- Parser repair: implemented in this branch.
- Regression tests: added; execution pending.
- Full CPVS reconstruction: unresolved.
- Production selector changes: none.
