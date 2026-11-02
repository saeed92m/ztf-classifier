from scripts.acquire_bts_snapshot import deterministic_sample, parse_bts_csv


def test_bts_csv_parser_handles_leading_blank_and_sexagesimal_coordinates():
    payload = (
        b"\nZTFID,IAUID,RA,Dec,type,peakmag\n"
        b"ZTF18abcde,AT2018abc,21:05:10.27,-09:32:41.6,SN Ia,18.2\n"
    )

    rows = parse_bts_csv(payload)

    assert len(rows) == 1
    assert rows[0]["external_id"] == "ZTF18abcde"
    assert rows[0]["tns_id"] == "AT2018abc"
    assert abs(float(rows[0]["ra"]) - 316.2927916667) < 1e-8
    assert abs(float(rows[0]["dec"]) - (-9.5448888889)) < 1e-8


def test_bts_csv_parser_accepts_decimal_coordinates():
    payload = (
        b"ZTFID,IAUID,RA,Dec,type\n"
        b"ZTF18abcde,AT2018abc,316.25,-9.5,SN Ia\n"
    )

    rows = parse_bts_csv(payload)

    assert rows[0]["ra"] == 316.25
    assert rows[0]["dec"] == -9.5


def test_bts_csv_parser_rejects_duplicate_ztf_ids():
    payload = (
        b"ZTFID,IAUID,RA,Dec,type\n"
        b"ZTF18abcde,AT2018abc,10,20,SN Ia\n"
        b"ZTF18abcde,AT2018abd,10,20,SN Ia\n"
    )

    try:
        parse_bts_csv(payload)
    except ValueError as exc:
        assert "duplicate ZTFID" in str(exc)
    else:
        raise AssertionError("duplicate BTS ZTF IDs must be rejected")


def test_bts_sample_is_deterministic_and_bounded():
    rows = [
        {"external_id": f"ZTF18abcde{i}", "ra": 10.0, "dec": 20.0}
        for i in range(10)
    ]

    first = deterministic_sample(rows, 4)
    second = deterministic_sample(list(reversed(rows)), 4)

    assert [row["external_id"] for row in first] == [
        row["external_id"] for row in second
    ]
    assert len(first) == 4
