# DR24 Native Adapter — Current Scope

This branch adds a bounded, provenance-preserving native DR24 Lightcurves backend. It preserves HMJD, native magnitude values, magnitude errors, color coefficients, raw catflags, OID/filter/field/readout metadata, and deterministic payload hashes. It rejects broad scans without the objectid index, duplicate OIDs, unexpected OIDs, and malformed payload schemas.

**Scientific limitation:** this backend does not yet normalize DR24 measurements for the frozen v0.2.0 feature pipeline. HMJD is not MJD. The project has not approved a time conversion, a DR24-to-ALeRCE photometric mapping, a catflags production mask, or a general cross-OID identity rule. The backend therefore exposes raw source-native records only. It does not run inference and does not silently fall back to ALeRCE.

The next acceptance gates are: approve and validate time semantics; define photometry/color handling; define versioned quality policy; define OID grouping; then add normalized observations and an end-to-end 30–50-object test. No model, feature schema, class order, benchmark, or release artifact is changed.
