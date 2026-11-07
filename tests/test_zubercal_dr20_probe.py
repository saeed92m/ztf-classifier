from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path

import pytest

ZUBERCAL_HATS_URL = "https://data.lsdb.io/hats/ztf_dr20/zubercal/"
DR24_OBJECTID = 264114400013085
SEARCH_RADIUS_ARCSEC = 1.2


@pytest.mark.skipif(
    os.getenv("ZTF_ZUBERCAL_PROBE") != "1",
    reason="Set ZTF_ZUBERCAL_PROBE=1 to run the bounded remote Zubercal probe.",
)
def test_bounded_zubercal_dr20_remote_probe(tmp_path: Path) -> None:
    import astropy.units as u
    import lsdb
    import pandas as pd
    from astropy.coordinates import SkyCoord
    from dask.distributed import Client

    from ztf_classifier.io.dr24_lightcurve import (
        DR24LightcurveBackend,
        DR24LightcurveRequest,
    )

    dr24 = DR24LightcurveBackend().acquire(
        DR24LightcurveRequest((DR24_OBJECTID,))
    )
    assert len(dr24.records) == 1
    source = dr24.records[0]
    center = SkyCoord(
        ra=float(source.objra) * u.deg,
        dec=float(source.objdec) * u.deg,
        frame="icrs",
    )
    spatial_filter = lsdb.ConeSearch(
        ra=center.ra.deg,
        dec=center.dec.deg,
        radius_arcsec=SEARCH_RADIUS_ARCSEC,
    )
    catalog = lsdb.open_catalog(
        ZUBERCAL_HATS_URL,
        search_filter=spatial_filter,
        columns=[
            "objectid",
            "mjd",
            "band",
            "mag",
            "magerr",
            "fieldid",
            "rcidin",
            "info",
            "flag",
            "objra",
            "objdec",
        ],
    )
    with Client(n_workers=1, threads_per_worker=1, memory_limit="2GB"):
        frame = catalog.compute()

    required = {
        "objectid",
        "mjd",
        "band",
        "mag",
        "magerr",
        "fieldid",
        "rcidin",
        "info",
        "flag",
        "objra",
        "objdec",
    }
    assert required.issubset(set(frame.columns))
    assert isinstance(frame, pd.DataFrame)

    unique_ids = sorted(int(value) for value in frame["objectid"].dropna().unique())
    bands = sorted(str(value) for value in frame["band"].dropna().unique())
    if not frame.empty:
        assert frame["objectid"].notna().all()
        assert frame["mjd"].notna().all()
        assert frame["mag"].notna().all()
        assert frame["magerr"].notna().all()
        assert set(bands).issubset({"g", "r", "i"})
        assert frame["magerr"].ge(0).all()

    if frame.empty:
        max_sep_arcsec = None
    else:
        coords = SkyCoord(
            ra=frame["objra"].astype(float).to_numpy() * u.deg,
            dec=frame["objdec"].astype(float).to_numpy() * u.deg,
            frame="icrs",
        )
        max_sep_arcsec = float(center.separation(coords).max().arcsec)

    records = frame.to_dict(orient="records")
    canonical = json.dumps(records, sort_keys=True, default=str).encode("utf-8")
    report = {
        "schema_version": "ztf-zubercal-dr20-probe-v1",
        "source": ZUBERCAL_HATS_URL,
        "source_release": "Zubercal DR20",
        "query": {
            "ztf_dr24_objectid": DR24_OBJECTID,
            "center_ra_deg": center.ra.deg,
            "center_dec_deg": center.dec.deg,
            "radius_arcsec": SEARCH_RADIUS_ARCSEC,
        },
        "result": {
            "row_count": len(frame),
            "unique_ps1_objectids": unique_ids,
            "unique_ps1_objectid_count": len(unique_ids),
            "bands": bands,
            "max_detection_separation_arcsec": max_sep_arcsec,
            "match_state": (
                "NO_PS1_MATCH"
                if not unique_ids
                else "SINGLE_PS1_ID"
                if len(unique_ids) == 1
                else "AMBIGUOUS_MULTIPLE_PS1_IDS"
            ),
            "payload_sha256": hashlib.sha256(canonical).hexdigest(),
        },
        "semantics": {
            "objectid": "PS1 object ID; not a ZTF OID",
            "mjd": "MJD(TDB)",
            "magerr_raw_scale": "integer in 1e-4 mag units",
            "magerr_conversion": "magerr_raw / 10000",
            "flag_fields": ["flag", "info"],
            "not_equivalent_to": "DR24 catflags",
        },
        "raw_rows_preserved": True,
    }
    output = Path(os.getenv("ZUBERCAL_PROBE_OUTPUT", tmp_path / "zubercal-probe.json"))
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    assert report["result"]["row_count"] >= 0
