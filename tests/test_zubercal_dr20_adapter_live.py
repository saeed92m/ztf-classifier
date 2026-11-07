from __future__ import annotations

import json
import os
from pathlib import Path

import pytest

from ztf_classifier.io.zubercal_dr20 import (
    ZubercalDR20Backend,
    ZubercalDR20Request,
)


@pytest.mark.skipif(
    os.getenv("ZTF_ZUBERCAL_ADAPTER_LIVE_TEST") != "1",
    reason="Set ZTF_ZUBERCAL_ADAPTER_LIVE_TEST=1 to run live Zubercal adapter parity.",
)
def test_zubercal_adapter_preserves_observed_ps1_ambiguity(tmp_path: Path) -> None:
    request = ZubercalDR20Request(
        ztf_objectid=264114400013085,
        ra_deg=142.59396362304688,
        dec_deg=-21.453134536743164,
        radius_arcsec=1.2,
    )
    result = ZubercalDR20Backend().acquire(request)
    payload = result.to_dict()

    assert payload["source_release"] == "Zubercal DR20"
    assert payload["match_state"] == "AMBIGUOUS_MULTIPLE_PS1_IDS"
    assert payload["crossmatch_decision"] == "NOT_SELECTED"
    assert payload["provenance"]["row_count"] == 123
    assert payload["provenance"]["candidate_ps1_id_count"] == 2
    assert {
        item["ps1_objectid"] for item in payload["candidate_summary"]
    } == {82251425938786635, 82251425941826616}
    assert {row["band"] for row in payload["raw_rows"]} == {"g", "r"}
    assert all("separation_arcsec" not in row for row in payload["raw_rows"])
    assert len(payload["row_annotations"]) == len(payload["raw_rows"])
    assert len(payload["provenance"]["payload_sha256"]) == 64
    assert payload["semantics"]["objectid"] == "PS1 object ID; not a ZTF OID"

    output = Path(
        os.getenv("ZUBERCAL_ADAPTER_OUTPUT", tmp_path / "zubercal-adapter-live.json")
    )
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
