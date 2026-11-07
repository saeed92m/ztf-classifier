# Zubercal DR20 ambiguity-preserving adapter v1

## Status

Implementation proposal in Draft PR #277. The adapter is a supplementary data-access path. It is not an approved astrophysical cross-match or model-input source.

## Request contract

`ZubercalDR20Request` accepts:
- A positive ZTF OID for provenance only.
- The DR24 source RA and Dec.
- A cone radius in the range `(0, 1.2]` arcsec.

The adapter queries the public LSDB HATS endpoint:

`https://data.lsdb.io/hats/ztf_dr20/zubercal/`

## Response contract

The response preserves:
- Raw Zubercal rows.
- PS1 candidate IDs.
- Per-candidate row count and bands.
- Minimum and maximum angular separation.
- Per-row separation annotations, separate from raw rows.
- Source release, query center, radius, row count and payload SHA-256.

Match state:
- `NO_PS1_MATCH`
- `SINGLE_PS1_ID`
- `AMBIGUOUS_MULTIPLE_PS1_IDS`

The response always sets `crossmatch_decision=NOT_SELECTED`. The adapter does not select the nearest PS1 ID.

## Unit and time semantics

- `objectid` is a PS1 ID, not a ZTF OID.
- `mjd` is MJD(TDB).
- Raw `magerr` is stored in units of 1e-4 mag. The derived value is `magerr_raw / 10000`.
- `flag` and `info` are Zubercal flags. They are not DR24 `catflags`.
- No time conversion, magnitude correction, epoch filtering or feature generation is performed.

## Bounded live evidence

The independent bounded Zubercal probe [workflow 42350687356](https://github.com/saeed92m/ztf-classifier/actions/runs/42350687356) returned 123 rows in g/r for ZTF OID `264114400013085` and two candidate PS1 IDs:
- `82251425938786635`
- `82251425941826616`

The match state was `AMBIGUOUS_MULTIPLE_PS1_IDS`. The adapter's own live parity workflow repeats this query and checks that it preserves both candidates and all raw rows.

## Limitations

- The catalog contains PS1-matched sources only. It does not cover every ZTF transient.
- One 1.2-arcsecond query can return multiple PS1 IDs. The observed probe demonstrates this.
- The adapter does not prove which PS1 object is the correct physical counterpart.
- No DR24/Zubercal photometric parity or v0.2 feature mapping is claimed.
