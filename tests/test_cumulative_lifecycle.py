from ztf_classifier.lifecycle import assert_valid_cycle_record, validate_cycle_record


def valid_record():
    return {
        "stage_id": "test-stage",
        "objective": "preserve cumulative evidence",
        "previous_knowledge_consumed": ["AD-CI-004"],
        "baseline": {"revision": "test"},
        "expected_improvement": ["correctness"],
        "measurement": {
            "metrics": {
                "correctness": {
                    "before": 0.9,
                    "after": 0.95,
                    "status": "MEASURED",
                }
            }
        },
        "validation": {"evidence": ["unit-test"], "scientific_gate_affected": False},
        "failure_analysis": {"status": "no-new-failure", "root_causes": []},
        "knowledge_extraction": {
            "status": "VERIFIED",
            "findings": ["contract is executable"],
        },
        "regression": {"status": "PASS", "open_blockers": []},
        "decision": "ACCEPT",
        "knowledge_carried_forward": ["AD-CI-004"],
    }


def test_valid_cycle_record_passes():
    assert validate_cycle_record(valid_record()) == []
    assert_valid_cycle_record(valid_record())


def test_cycle_requires_knowledge_extraction():
    record = valid_record()
    record["knowledge_extraction"]["status"] = "UNKNOWN"
    errors = validate_cycle_record(record)
    assert "knowledge_extraction.status must use an allowed knowledge status" in errors


def test_cycle_requires_measurement_evidence_shape():
    record = valid_record()
    record["measurement"]["metrics"]["runtime"] = {"before": 10}
    assert any("runtime needs before/after" in error for error in validate_cycle_record(record))


def test_scientific_cycle_requires_validation_evidence_or_blocker():
    record = valid_record()
    record["validation"] = {"scientific_gate_affected": True}
    errors = validate_cycle_record(record)
    assert any("scientific-gate changes require validation evidence" in error for error in errors)


def test_accepted_cycle_cannot_hide_regression():
    record = valid_record()
    record["regression"] = {"status": "BLOCKED", "open_blockers": ["benchmark"}
    errors = validate_cycle_record(record)
    assert any("ACCEPT decisions require" in error for error in errors)


def test_scientific_blocker_is_explicitly_allowed():
    record = valid_record()
    record["validation"] = {
        "scientific_gate_affected": True,
        "status": "BLOCKED",
        "blocker": "immutable source evidence unavailable",
    }
    record["regression"] = {
        "status": "BLOCKED",
        "open_blockers": ["scientific-gate"],
    }
    record["decision"] = "BLOCKED"
    assert validate_cycle_record(record) == []
