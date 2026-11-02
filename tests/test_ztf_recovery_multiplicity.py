from scripts.audit_ztf_recovery_multiplicity import audit_recovery


def test_multi_filter_oids_are_reported_but_not_called_false_positives():
    catalog = [{"external_id": "CSS_A", "ra": "10", "dec": "20"}]
    matches = [
        {"external_id": "CSS_A", "oid": "100", "ra": "10", "dec": "20", "filtercode": "zg"},
        {"external_id": "CSS_A", "oid": "200", "ra": "10", "dec": "20", "filtercode": "zr"},
        {"external_id": "CSS_A", "oid": "300", "ra": "10", "dec": "20", "filtercode": "zi"},
    ]

    rows, summary = audit_recovery(catalog, matches, radii_arcsec=(1.0,))

    assert rows[0]["ztf_oid_count"] == 3
    assert rows[0]["filter_count"] == 3
    assert rows[0]["same_filter_multiple_oids"] is False
    assert summary["radii"]["1.0"]["multi_oid_objects"] == 1
    assert summary["radii"]["1.0"]["multi_filter_objects"] == 1
    assert summary["radii"]["1.0"]["same_filter_multi_oid_objects"] == 0
    assert "not classified as false positives" in summary["interpretation"]


def test_multiple_oids_in_one_filter_are_separately_flagged():
    catalog = [{"external_id": "CSS_B", "ra": "10", "dec": "20"}]
    matches = [
        {"external_id": "CSS_B", "oid": "100", "ra": "10", "dec": "20", "filtercode": "zg"},
        {"external_id": "CSS_B", "oid": "101", "ra": "10.0001", "dec": "20", "filtercode": "zg"},
        {"external_id": "CSS_B", "oid": "200", "ra": "10", "dec": "20", "filtercode": "zr"},
    ]

    rows, summary = audit_recovery(catalog, matches, radii_arcsec=(1.0,))

    assert rows[0]["ztf_oid_count"] == 3
    assert rows[0]["same_filter_multiple_oids"] is True
    assert summary["radii"]["1.0"]["same_filter_multi_oid_objects"] == 1


def test_unmatched_catalog_sources_are_retained_in_denominator():
    catalog = [
        {"external_id": "CSS_A", "ra": "10", "dec": "20"},
        {"external_id": "CSS_B", "ra": "30", "dec": "40"},
    ]
    matches = [
        {"external_id": "CSS_A", "oid": "100", "ra": "10", "dec": "20", "filtercode": "zg"},
    ]

    rows, summary = audit_recovery(catalog, matches, radii_arcsec=(1.0,))

    assert len(rows) == 2
    assert summary["radii"]["1.0"]["catalog_objects"] == 2
    assert summary["radii"]["1.0"]["matched_objects"] == 1
    assert summary["radii"]["1.0"]["unmatched_objects"] == 1


def test_radius_sensitivity_uses_recomputed_angular_separation():
    catalog = [{"external_id": "CSS_A", "ra": "10", "dec": "20"}]
    matches = [
        {"external_id": "CSS_A", "oid": "100", "ra": "10.0002", "dec": "20", "filtercode": "zg"},
    ]

    _, summary = audit_recovery(catalog, matches, radii_arcsec=(1.0, 2.0, 5.0))

    assert summary["radii"]["1.0"]["matched_objects"] == 0
    assert summary["radii"]["2.0"]["matched_objects"] == 1
    assert summary["radii"]["5.0"]["matched_objects"] == 1


def test_duplicate_catalog_ids_fail_closed():
    catalog = [
        {"external_id": "CSS_A", "ra": "10", "dec": "20"},
        {"external_id": "CSS_A", "ra": "10", "dec": "20"},
    ]

    try:
        audit_recovery(catalog, [], radii_arcsec=(1.0,))
    except ValueError as exc:
        assert "duplicate external_id" in str(exc)
    else:
        raise AssertionError("duplicate external IDs must be rejected")


def test_match_rows_for_unknown_catalog_ids_fail_closed():
    catalog = [{"external_id": "CSS_A", "ra": "10", "dec": "20"}]
    matches = [
        {"external_id": "CSS_UNKNOWN", "oid": "100", "ra": "10", "dec": "20", "filtercode": "zg"},
    ]

    try:
        audit_recovery(catalog, matches, radii_arcsec=(1.0,))
    except ValueError as exc:
        assert "unknown external_id" in str(exc)
    else:
        raise AssertionError("unknown external IDs must be rejected")
