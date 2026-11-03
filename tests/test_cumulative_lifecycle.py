from ztf_classifier.lifecycle import (
    _main,
    assert_valid_cycle_record,
    validate_cycle_file,
    validate_cycle_record,
)


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
    assert any(
        "runtime needs before/after" in error for error in validate_cycle_record(record)
    )


def test_scientific_cycle_requires_validation_evidence_or_blocker():
    record = valid_record()
    record["validation"] = {"scientific_gate_affected": True}
    errors = validate_cycle_record(record)
    assert any(
        "scientific-gate changes require validation evidence" in error
        for error in errors
    )


def test_accepted_cycle_cannot_hide_regression():
    record = valid_record()
    record["regression"] = {"status": "BLOCKED", "open_blockers": ["benchmark"]}
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



def test_partial_recovery_evidence_is_valid_when_limited_claims_are_explicit():
    record = valid_record()
    record["measurement"]["metrics"]["reliability"] = {
        "before": "No source-backed recovery availability measurement.",
        "after": "One 100-target run completed; repeatability and photometry quality remain unmeasured.",
        "status": "PARTIALLY_MEASURED",
        "reason": "Single-run evidence is partial.",
    }
    record["regression"] = {
        "status": "NOT_VERIFIED",
        "open_blockers": ["Repeatability remains untested."],
    }
    record["decision"] = "REVISE"
    assert validate_cycle_record(record) == []


def test_cycle_file_error_identifies_the_invalid_record_path(tmp_path):
    import json

    record = valid_record()
    record["regression"] = {"status": "PARTIALLY_VERIFIED", "open_blockers": ["pending"]}
    path = tmp_path / "broken-cycle.json"
    path.write_text(json.dumps(record), encoding="utf-8")

    try:
        validate_cycle_file(path)
    except ValueError as exc:
        assert "broken-cycle.json" in str(exc)
        assert "regression.status must be an allowed status" in str(exc)
    else:
        raise AssertionError("invalid lifecycle record unexpectedly passed")



def test_lifecycle_cli_reports_all_invalid_files(tmp_path, monkeypatch, capsys):
    import json

    invalid = valid_record()
    invalid["regression"] = {
        "status": "PARTIALLY_VERIFIED",
        "open_blockers": ["pending"],
    }
    first = tmp_path / "first.json"
    second = tmp_path / "second.json"
    first.write_text(json.dumps(invalid), encoding="utf-8")
    second.write_text(json.dumps(invalid), encoding="utf-8")

    monkeypatch.setattr(
        "sys.argv",
        ["ztf-lifecycle", "validate", str(first), str(second)],
    )

    assert _main() == 1
    output = capsys.readouterr().out
    assert str(first) in output
    assert str(second) in output
    assert output.count("FAIL ") == 2
