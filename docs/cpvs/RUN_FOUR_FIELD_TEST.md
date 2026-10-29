# CPVS four-field membership audit

## Purpose

This diagnostic tests whether the predicate

`gmag > 0 AND rmag > 0 AND Per-g > 0 AND Per-r > 0`

applied to **all Table 2 parent objects** is extensionally equal to the published Table 4 membership. It is a diagnostic only; it must not silently change the production selection policy.

## Important distinction: 11,602 and 55 are different differences

The retained source-backed historical artifact contains:

- Parent metadata: 781,602 rows; SHA-256 `3675b1274f73fcb15d47e7a780f194ef8fa335cd248c6ff53ea4f01559c86591`
- Reconstructed candidate IDs: 741,786; SHA-256 `699ff34bcf8dd4b5043eed48384973cb5109fd86ca260f831a502097370238df`
- Published membership: 730,184; historical audit reported 730,184 intersection, 11,602 candidate-only and zero published-only.

Independent parsing of those retained parent/candidate files gives:

| Set comparison | Count |
|---|---:|
| Parent objects satisfying all four positive-field conditions (`S4`) | 730,239 |
| `S4 ∩ candidates` | 730,184 |
| Candidate IDs failing at least one of the four conditions | 11,602 |
| `S4 - candidates` (pass all four fields but never entered the candidate set) | 55 |

The sorted 11,602-ID residual SHA-256 is `b891e2ef5a79841f23a7d4c8f5d45087280ba5de515d3f39463d9c1465286643`. The sorted 55-ID list SHA-256 (decimal IDs, one per line, trailing newline) is `9ca933554a7c070f93d6fe36d614549ba8abcbf6aeb5ccd53787600745708941`.

**Do not describe this as “11,602 became 55.”** The 11,602 are candidate objects rejected by the predicate; the 55 are different parent objects that pass the predicate but are absent from the candidate set. Thus the four-field predicate over the *entire parent table* predicts 55 extra objects versus the published set. The raw Table 4 bytes were not bundled in that historical artifact, so a fresh two-table source audit is still required before treating the prediction as independently reverified against current publisher bytes.

## Identifier semantics

- Table 2 `Seq` is the parent catalogue's internal source identifier.
- Table 4's numeric `ID` must **not** be assumed equal to Table 2 `Seq`.
- Map published membership by the exact published ZTF object name (`Table 4.ZTF`) to the corresponding Table 2 object name (`Table 2.ID`), then compare using Table 2 `Seq`.
- The parser accepts the CDS fixed-width tables and VizieR ASU-TSV extracts. It skips metadata and separator rows, validates expected data-row counts, rejects duplicate/ambiguous identifiers, and fails closed on unmappable published names.

## Reproducible local run

The automated workflow downloads only compact columns from the two catalogues, not the multi-gigabyte epoch-photometry archives.

```bash
mkdir -p ~/cpvs-two-table && cd ~/cpvs-two-table

curl --location --fail --show-error --retry 2 \
  'https://vizier.cds.unistra.fr/viz-bin/asu-tsv?-source=J/ApJS/249/18/table2&-out=ID,Seq,gmag,rmag,Per-g,Per-r&-out.max=1000000' \
  -o table2.tsv

curl --location --fail --show-error --retry 2 \
  'https://vizier.cds.unistra.fr/viz-bin/asu-tsv?-source=J/ApJ/932/118/table4&-out=ZTF,ID&-out.max=1000000' \
  -o table4.tsv

python3 /path/to/ztf-classifier/scripts/verify_cpvs_four_field_rule.py --self-test
python3 /path/to/ztf-classifier/scripts/verify_cpvs_four_field_rule.py \
  --table2 table2.tsv --table4 table4.tsv \
  --out cpvs_four_field_report.json --dump-ids
```

Replace `/path/to/ztf-classifier` with the checked-out repository path. The script records source file SHA-256 hashes, validates 781,602 Table 2 rows and 730,184 Table 4 rows, reports both directional set differences, and writes the exact differing IDs.

## Interpretation and acceptance

- `four_field_only > 0`: the four-field predicate is **not** equivalent to published membership across the full parent table.
- `published_only > 0`: the predicate also excludes published members and is insufficient to define membership.
- Both differences zero: extensional equality for the exact hashed inputs only; this still does not prove the authors intended this undocumented rule.

Do not change production selection, thresholds, feature definitions, model artifacts, or the v0.2.0 baseline to force a matching count. Keep Issue #170 open until the raw-source comparison and method provenance are documented. A passing synthetic self-test validates parser logic only, not the scientific hypothesis.
