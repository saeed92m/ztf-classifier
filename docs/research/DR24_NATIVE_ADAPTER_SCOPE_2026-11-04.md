# DR24 Native Adapter — Current Scope

This branch adds a bounded, provenance-preserving native DR24 Lightcurves backend. It preserves HMJD, native magnitude values, magnitude errors, color coefficients, raw catflags, OID/filter/field/readout metadata, and deterministic payload hashes. It rejects broad scans without the objectid index, duplicate OIDs, unexpected OIDs, and malformed payload schemas.

**Scientific limitation:** this backend does not yet normalize DR24 measurements for the frozen v0.2.0 feature pipeline. HMJD is not MJD. The project has not approved a time conversion, a DR24-to-ALeRCE photometric mapping, a catflags production mask, or a general cross-OID identity rule. The backend therefore exposes raw source-native records only. It does not run inference and does not silently fall back to ALeRCE.

The next acceptance gates are: approve and validate time semantics; define photometry/color handling; define versioned quality policy; define OID grouping; then add normalized observations and an end-to-end 30–50-object test. No model, feature schema, class order, benchmark, or release artifact is changed.


## Source semantics checked against DR24 documentation

The source definitions below are documented in the official ZTF DR24 release notes and the IRSA HATS/LSDB tutorial. They define the native data contract. They do not, by themselves, approve a project-specific normalization or selection policy.

- **Time:** `hmjd` is heliocentric-based Modified Julian Date, derived as `HJD - 2400000.5`. It refers to the exposure midpoint and is stored as double precision truncated to five decimal places. It must not be silently relabeled as geocentric MJD.
- **Magnitude:** `mag` is calibrated in the native ZTF system with zero AB color (`g-r=0`) assumed. The release notes state that no color correction is applied.
- **Uncertainty:** `magerr` is the reported 1-sigma magnitude uncertainty. It excludes the usually small calibration-zeropoint uncertainty and possible systematics relative to external catalogs.
- **Color term:** `clrcoeff` is the linear color coefficient. Applying it requires the source color in the relevant AB system. A color value or transformation must not be invented when it is absent.
- **Quality:** `catflags` is bit-encoded. Bit 15 (decimal 32768) marks cloud- and/or moon-affected epochs. The release notes recommend excluding these epochs for ordinary use; other bits encode source-level issues. The raw adapter preserves all bits and applies no mask. A project mask must be versioned and validated before inference.
- **Object identity:** The IRSA HATS tutorial defines one Lightcurves row per ZTF object. A ZTF object ID is defined per filter, field, and quadrant. One astrophysical source can therefore have up to three OIDs (g/r/i), and more when it lies near field or quadrant boundaries. `objectid` is not a guaranteed astrophysical-source identifier.
- **Filter identity:** `filterid` maps 1 to g, 2 to r, and 3 to i. `fieldid` and `rcid` retain survey partition/readout provenance. The raw adapter preserves each OID separately and does not cross-match or group OIDs.

### Scientific implications

1. Preserve `hmjd` as a named, heliocentric time coordinate in the raw record. A conversion or alignment to another time coordinate requires an explicit, tested policy.
2. Keep raw `mag`, `magerr`, and `clrcoeff` together. Any color-corrected magnitude is a derived value and needs a separate field, formula, color source, and provenance.
3. Do not treat `catflags == 0` as equivalent to the documented cloud/moon exclusion. The release notes distinguish bit 15 from other source-level bits.
4. Keep g/r/i OIDs separate. A multi-band astrophysical object requires an explicit identity/cross-match contract (the planned AOIC layer); positional proximity alone must not silently merge OIDs.
5. Negative `magerr` values are documented as failed/non-converged PSF-fit estimates and must be identified in downstream quality diagnostics. The raw adapter preserves them.

### Primary sources

- ZTF Collaboration, **Public Data Release 24**, Sections 9, 10 (Cautionary Notes 12, 15, 18), and 12.c (DR24 Parquet field definitions): https://irsa.ipac.caltech.edu/data/ZTF/docs/releases/dr24/ztf_release_notes_dr24.pdf
- IRSA, **Access ZTF DR24 Light Curves from HATS Catalog** (one row per ZTF OID, per-filter/field/quadrant identity, indexed `objectid` lookup, and multi-OID physical-source caveat): https://caltech-ipac.github.io/irsa-tutorials/ztf-lightcurves/
- IRSA Cloud Data Access, ZTF DR24 HATS S3 prefixes: https://irsa.ipac.caltech.edu/cloud_access/

These sources establish the meaning of source fields. They do not establish equivalence with ALeRCE photometry or authorize reuse of the frozen v0.2.0 feature transformations.
