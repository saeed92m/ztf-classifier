"""Tests for the documented-criterion reconstruction.

Every fixture is written at the byte offsets the CDS ReadMes specify, so the
tests exercise the real layout rather than a convenient one. All fixtures are
synthetic: this suite proves the code does what it says, and says nothing about
the real catalogues, which were not reachable.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

from scripts.reconstruct_cpvs_from_photometry import (
    MAG_TO_FLUX_SNR_FACTOR,
    PHOTOMETRY_FIXED_WIDTH,
    TABLE2_FIXED_WIDTH,
    TABLE4_FIXED_WIDTH,
    DetectionRule,
    build_report,
    compare_sets,
    main,
    null_exclusion_sequences,
    qualifying_sequences,
    read_table2,
    read_table4,
)


def _put(chars: list[str], slice_: slice, text: str) -> None:
    for offset, character in enumerate(text):
        index = slice_.start + offset
        if index >= len(chars):
            raise ValueError(f"text {text!r} overflows slice {slice_}")
        chars[index] = character


def table2_line(
    name: str,
    seq: int,
    *,
    gmag: str = "18.500",
    rmag: str = "18.000",
    per_g: str = "1.2345678",
    per_r: str = "1.2345670",
) -> str:
    """One CDS table2.dat row (Lrecl 228) with values at documented columns."""
    chars = [" "] * 228
    _put(chars, TABLE2_FIXED_WIDTH["name"], f"{name:<22}")
    _put(chars, TABLE2_FIXED_WIDTH["seq"], f"{seq:>6}")
    _put(chars, TABLE2_FIXED_WIDTH["per"], f"{1.2345678:>11}")
    _put(chars, TABLE2_FIXED_WIDTH["gmag"], f"{gmag:>6}")
    _put(chars, TABLE2_FIXED_WIDTH["rmag"], f"{rmag:>6}")
    _put(chars, TABLE2_FIXED_WIDTH["per_g"], f"{per_g:>13}")
    _put(chars, TABLE2_FIXED_WIDTH["per_r"], f"{per_r:>13}")
    return "".join(chars)


def table4_line(name: str, object_id: int, klass: str = "EW") -> str:
    """One CDS table4.dat row (Lrecl 63)."""
    chars = [" "] * 63
    _put(chars, TABLE4_FIXED_WIDTH["name"], f"{name:<22}")
    _put(chars, TABLE4_FIXED_WIDTH["id"], f"{object_id:>6}")
    chars[30:35] = list(f"{klass:<5}")
    chars[36:45] = list(f"{123.45678:>9}")
    chars[46:55] = list(f"{45.67890:>9}")
    chars[56:63] = list(f"{0.12345:>7}")
    return "".join(chars)


def photometry_line(
    seq: int,
    magnitude: float,
    magnitude_error: float,
    *,
    flag: int = 0,
    mjd: float = 58200.1234567,
) -> str:
    """One CDS ztf2[gr].dat row (Lrecl 75)."""
    chars = [" "] * 75
    _put(chars, PHOTOMETRY_FIXED_WIDTH["seq"], f"{seq:>6}")
    _put(chars, PHOTOMETRY_FIXED_WIDTH["mjd"], f"{mjd:>13.7f}")
    _put(chars, PHOTOMETRY_FIXED_WIDTH["mag"], f"{magnitude:>10.7f}")
    _put(chars, PHOTOMETRY_FIXED_WIDTH["e_mag"], f"{magnitude_error:>14.7E}")
    _put(chars, PHOTOMETRY_FIXED_WIDTH["flag"], f"{flag:>4}")
    return "".join(chars)


def write(path: Path, lines: list[str]) -> Path:
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


# ---------------------------------------------------------------------------
# Parsing: the null sentinel must stay distinct from a real zero.
# ---------------------------------------------------------------------------


def test_nullable_zero_sentinel_parses_as_missing(tmp_path: Path):
    path = write(
        tmp_path / "table2.dat",
        [
            table2_line("ZTFJ000000.00+000000.0", 1, gmag=" 0.000", rmag="18.000"),
            table2_line("ZTFJ000001.00+000000.0", 2, gmag="18.500", rmag="18.000"),
        ],
    )
    rows = read_table2(path)
    assert rows[1]["gmag"] is None, "?=0 must be None, not 0.0"
    assert rows[2]["gmag"] == pytest.approx(18.5)


def test_table2_parses_seq_and_name_from_documented_columns(tmp_path: Path):
    path = write(
        tmp_path / "table2.dat",
        [table2_line("ZTFJ000000.19+320847.2", 3)],
    )
    rows = read_table2(path)
    assert set(rows) == {3}
    assert rows[3]["name"] == "ZTFJ000000.19+320847.2"


def test_table2_rejects_duplicate_seq(tmp_path: Path):
    path = write(
        tmp_path / "table2.dat",
        [
            table2_line("ZTFJ000000.00+000000.0", 5),
            table2_line("ZTFJ000001.00+000000.0", 5),
        ],
    )
    with pytest.raises(ValueError, match="duplicate Seq"):
        read_table2(path)


def test_table2_rejects_shifted_layout(tmp_path: Path):
    path = write(tmp_path / "table2.dat", ["x" * 228])
    with pytest.raises(ValueError, match="Seq is not an integer"):
        read_table2(path)


def test_table4_parses_name_and_id(tmp_path: Path):
    path = write(
        tmp_path / "table4.dat",
        [table4_line("ZTFJ000000.00+000000.0", 414363)],
    )
    name_to_id, ids = read_table4(path)
    assert name_to_id == {"ZTFJ000000.00+000000.0": 414363}
    assert ids == {414363}


# ---------------------------------------------------------------------------
# The two SNR definitions. This is the scientific heart of the ambiguity.
# ---------------------------------------------------------------------------


def test_inverse_error_snr_is_independent_of_magnitude():
    """f/sigma_f = 1.0857/sigma_m, so the SNR must not depend on the magnitude."""
    rule = DetectionRule(snr_method="inverse_error")
    faint = rule.signal_to_noise(20.0, 0.2)
    bright = rule.signal_to_noise(12.0, 0.2)
    assert faint == pytest.approx(bright)
    assert faint == pytest.approx(MAG_TO_FLUX_SNR_FACTOR / 0.2)


def test_magnitude_over_error_snr_scales_with_magnitude():
    """The shortcut does depend on magnitude, which is why it is not equivalent."""
    rule = DetectionRule(snr_method="magnitude_over_error")
    assert rule.signal_to_noise(20.0, 0.2) == pytest.approx(100.0)
    assert rule.signal_to_noise(12.0, 0.2) == pytest.approx(60.0)


def test_the_two_definitions_disagree_decisively_on_the_sigma_cut():
    """With m/sigma_m almost every detection clears 2.5 sigma.

    e_mag would have to exceed m/2.5 - about 7 mag at r=18 - for the shortcut to
    reject anything. The two readings are therefore not interchangeable, and a
    comparison that does not state which was used is not reproducible.
    """
    inverse = DetectionRule(snr_method="inverse_error")
    shortcut = DetectionRule(snr_method="magnitude_over_error")

    # A genuinely marginal detection: 1.5 sigma in the flux sense.
    assert inverse.signal_to_noise(18.0, MAG_TO_FLUX_SNR_FACTOR / 1.5) < 2.5
    assert shortcut.signal_to_noise(18.0, MAG_TO_FLUX_SNR_FACTOR / 1.5) > 2.5


def test_unknown_snr_method_is_rejected():
    with pytest.raises(ValueError, match="unknown snr_method"):
        DetectionRule(snr_method="guess").signal_to_noise(18.0, 0.1)


# ---------------------------------------------------------------------------
# Detection counting.
# ---------------------------------------------------------------------------


def test_qualifying_sequences_applies_the_sigma_threshold(tmp_path: Path):
    rule = DetectionRule(snr_method="inverse_error")
    # e_mag = 0.1 -> SNR 10.86 (passes 2.5 and 3.0)
    # e_mag = 0.5 -> SNR 2.17 (fails 2.5)
    path = write(
        tmp_path / "ztf2g.dat",
        [
            photometry_line(1, 18.0, 0.1),
            photometry_line(2, 18.0, 0.5),
        ],
    )
    assert qualifying_sequences(path, rule, 2.5) == {1}


def test_qualifying_sequences_needs_only_one_detection(tmp_path: Path):
    rule = DetectionRule(snr_method="inverse_error")
    path = write(
        tmp_path / "ztf2g.dat",
        [
            photometry_line(7, 18.0, 2.0),  # fails
            photometry_line(7, 18.0, 0.1),  # passes -> sequence qualifies
            photometry_line(8, 18.0, 2.0),  # fails
        ],
    )
    assert qualifying_sequences(path, rule, 2.5) == {7}


def test_flag_policy_changes_the_selection(tmp_path: Path):
    path = write(tmp_path / "ztf2g.dat", [photometry_line(9, 18.0, 0.1, flag=32)])
    permissive = DetectionRule(require_flag_zero=False)
    strict = DetectionRule(require_flag_zero=True)
    assert qualifying_sequences(path, permissive, 2.5) == {9}
    assert qualifying_sequences(path, strict, 2.5) == set()


def test_null_exclusion_requires_all_four_fields(tmp_path: Path):
    path = write(
        tmp_path / "table2.dat",
        [
            # complete
            table2_line("ZTFJ000000.00+000000.0", 1),
            # missing rmag
            table2_line("ZTFJ000001.00+000000.0", 2, rmag=" 0.000"),
            # missing Per-r
            table2_line("ZTFJ000002.00+000000.0", 3, per_r=" 0.0000000"),
        ],
    )
    rows = read_table2(path)
    assert null_exclusion_sequences(rows) == {1}


# ---------------------------------------------------------------------------
# Set comparison must be object level, not count level.
# ---------------------------------------------------------------------------


def test_compare_sets_detects_equal_counts_with_different_sets():
    table2 = {
        1: {"name": "A", "gmag": 18.0, "rmag": 18.0, "per_g": 1.0, "per_r": 1.0},
        2: {"name": "B", "gmag": 18.0, "rmag": 18.0, "per_g": 1.0, "per_r": 1.0},
    }
    reference = {1, 2}
    # Same cardinality, different membership.
    produced = {1, 3}
    report = compare_sets({"route": produced}, reference, table2)
    route = report["routes"]["route"]
    assert route["size"] == len(reference)
    assert route["exact_set_equality"] is False
    assert route["produced_only"] == 1
    assert route["reference_only"] == 1
    assert route["produced_only_objects"][0]["seq"] == 3


# ---------------------------------------------------------------------------
# End to end.
# ---------------------------------------------------------------------------


def _build_fixture(tmp_path: Path) -> dict[str, Path]:
    table2 = write(
        tmp_path / "table2.dat",
        [
            table2_line("ZTFJ000000.00+000000.0", 1),
            table2_line("ZTFJ000001.00+000000.0", 2),
            table2_line("ZTFJ000004.00+000000.0", 5, gmag=" 0.000"),
        ],
    )
    table4 = write(
        tmp_path / "table4.dat",
        [
            table4_line("ZTFJ000000.00+000000.0", 1),
            table4_line("ZTFJ000001.00+000000.0", 2),
        ],
    )
    # Both published objects pass the 2.5 sigma g cut; the third object's g
    # magnitude is null in table2 but its photometry is present and significant,
    # so the two routes must disagree on it and the report must show that.
    ztf2g = write(
        tmp_path / "ztf2g.dat",
        [
            photometry_line(1, 18.0, 0.1),
            photometry_line(2, 18.0, 0.1),
            photometry_line(5, 18.0, 0.1),
        ],
    )
    ztf2r = write(
        tmp_path / "ztf2r.dat",
        [
            photometry_line(1, 18.0, 0.1),
            photometry_line(2, 18.0, 0.1),
            photometry_line(5, 18.0, 0.1),
        ],
    )
    return {"table2": table2, "table4": table4, "ztf2g": ztf2g, "ztf2r": ztf2r}


def test_end_to_end_report_records_hashes_and_every_route(tmp_path: Path):
    paths = _build_fixture(tmp_path)
    manifest = build_report(
        table2_path=paths["table2"],
        table4_path=paths["table4"],
        ztf2g_path=paths["ztf2g"],
        ztf2r_path=paths["ztf2r"],
        output_dir=tmp_path / "out",
        rules=[DetectionRule(snr_method="inverse_error", require_flag_zero=False)],
    )

    for name in ("table2", "table4", "ztf2g", "ztf2r"):
        assert len(manifest["inputs"][name]["sha256"]) == 64
        assert manifest["inputs"][name]["bytes"] > 0

    assert manifest["table2_rows"] == 3
    assert manifest["table4_rows"] == 2

    comparison = manifest["comparison"]
    # The published membership resolves to seq 1 and 2 by name.
    assert comparison["reference_size"] == 2
    assert comparison["published_id_vs_name_join"] == "AGREE"

    # The null-exclusion route excludes seq 5, whose gmag is the null sentinel.
    assert comparison["routes"]["null_exclusion"]["exact_set_equality"] is True

    # The documented photometric route includes seq 5, so it must disagree.
    key = "documented_rule[inverse_error,flagFalse]"
    assert comparison["routes"][key]["exact_set_equality"] is False
    assert comparison["routes"][key]["produced_only"] == 1
    assert comparison["routes"][key]["produced_only_objects"][0]["seq"] == 5


def test_report_never_claims_resolution(tmp_path: Path):
    paths = _build_fixture(tmp_path)
    manifest = build_report(
        table2_path=paths["table2"],
        table4_path=paths["table4"],
        ztf2g_path=paths["ztf2g"],
        ztf2r_path=paths["ztf2r"],
        output_dir=tmp_path / "out",
        rules=[DetectionRule()],
    )
    assert manifest["status"] == "UNRESOLVED"
    assert manifest["validated_on_real_data"] is False
    assert "not treated as" in manifest["note"]


def test_unmapped_published_name_is_refused(tmp_path: Path):
    paths = _build_fixture(tmp_path)
    write(
        paths["table4"],
        [table4_line("ZTFJ999999.00+000000.0", 1)],
    )
    with pytest.raises(ValueError, match="absent from table2"):
        build_report(
            table2_path=paths["table2"],
            table4_path=paths["table4"],
            ztf2g_path=paths["ztf2g"],
            ztf2r_path=paths["ztf2r"],
            output_dir=tmp_path / "out",
            rules=[DetectionRule()],
        )


def test_cli_reports_failure_without_writing_a_report(tmp_path: Path):
    paths = _build_fixture(tmp_path)
    output = tmp_path / "out"
    # Non-existent photometry file must be a refusal, not an empty result.
    code = main(
        [
            "--table2",
            str(paths["table2"]),
            "--table4",
            str(paths["table4"]),
            "--ztf2g",
            str(tmp_path / "missing.dat"),
            "--ztf2r",
            str(paths["ztf2r"]),
            "--output-dir",
            str(output),
        ]
    )
    assert code == 1
    assert not (output / "cpvs_documented_rule_report.json").exists()


def test_module_docstring_documents_the_unresolved_parts():
    """The unknowns must stay documented, not silently defaulted."""
    from scripts import reconstruct_cpvs_from_photometry as module

    docstring = module.__doc__ or ""
    assert "snr_method" in docstring
    assert "require_flag_zero" in docstring
    assert "not" in docstring.lower()


def test_cli_is_runnable_as_a_script(tmp_path: Path):
    paths = _build_fixture(tmp_path)
    completed = subprocess.run(
        [
            sys.executable,
            "scripts/reconstruct_cpvs_from_photometry.py",
            "--table2",
            str(paths["table2"]),
            "--table4",
            str(paths["table4"]),
            "--ztf2g",
            str(paths["ztf2g"]),
            "--ztf2r",
            str(paths["ztf2r"]),
            "--output-dir",
            str(tmp_path / "out"),
        ],
        capture_output=True,
        text=True,
        check=False,
        cwd=Path(__file__).resolve().parents[1],
    )
    assert completed.returncode == 0, completed.stderr
    report = json.loads(
        (tmp_path / "out" / "cpvs_documented_rule_report.json").read_text()
    )
    assert report["validated_on_real_data"] is False
    assert len(report["comparison"]["detection_runs"]) == 3


# ---------------------------------------------------------------------------
# Publisher checksums: a wrong download must abort, not be analysed.
# ---------------------------------------------------------------------------


def _write_manifest(tmp_path: Path, md5_by_input: dict[str, str | None]) -> Path:
    entries = []
    for label in ("table2", "table4", "ztf2g", "ztf2r"):
        entries.append(
            {
                "id": label,
                "md5_published_by_publisher": md5_by_input.get(label),
            }
        )
    manifest = tmp_path / "manifest.json"
    manifest.write_text(json.dumps({"inputs": entries}), encoding="utf-8")
    return manifest


def test_publisher_checksum_match_is_reported(tmp_path: Path):
    from scripts.reconstruct_cpvs_from_photometry import (
        md5_file,
        verify_publisher_checksums,
    )

    paths = _build_fixture(tmp_path)
    md5s = {label: md5_file(path) for label, path in paths.items()}
    manifest = _write_manifest(tmp_path, md5s)
    results = verify_publisher_checksums(paths, manifest)
    assert [r["verdict"] for r in results] == ["MATCH"] * 4


def test_publisher_checksum_mismatch_aborts(tmp_path: Path):
    from scripts.reconstruct_cpvs_from_photometry import verify_publisher_checksums

    paths = _build_fixture(tmp_path)
    manifest = _write_manifest(
        tmp_path,
        {
            "table2": "0" * 32,
            "table4": None,
            "ztf2g": None,
            "ztf2r": None,
        },
    )
    with pytest.raises(ValueError, match="publisher checksums"):
        verify_publisher_checksums(paths, manifest)


def test_missing_publisher_checksum_is_not_a_pass(tmp_path: Path):
    """table4.dat has no publisher md5; that must read as unverifiable."""
    from scripts.reconstruct_cpvs_from_photometry import (
        md5_file,
        verify_publisher_checksums,
    )

    paths = _build_fixture(tmp_path)
    md5s = {label: md5_file(path) for label, path in paths.items()}
    md5s["table4"] = None
    manifest = _write_manifest(tmp_path, md5s)
    results = verify_publisher_checksums(paths, manifest)
    by_input = {r["input"]: r["verdict"] for r in results}
    assert by_input["table4"] == "NO_PUBLISHER_CHECKSUM"
    assert by_input["table2"] == "MATCH"


def test_report_records_both_digests(tmp_path: Path):
    paths = _build_fixture(tmp_path)
    manifest = build_report(
        table2_path=paths["table2"],
        table4_path=paths["table4"],
        ztf2g_path=paths["ztf2g"],
        ztf2r_path=paths["ztf2r"],
        output_dir=tmp_path / "out",
        rules=[DetectionRule()],
    )
    for name in ("table2", "table4", "ztf2g", "ztf2r"):
        assert len(manifest["inputs"][name]["sha256"]) == 64
        assert len(manifest["inputs"][name]["md5"]) == 32


def test_committed_acquisition_manifest_matches_the_repo_convention():
    """The acquisition manifest must declare the four required inputs."""
    repo = Path(__file__).resolve().parents[1]
    manifest = json.loads(
        (repo / "configs/cpvs/cpvs_input_acquisition.json").read_text(encoding="utf-8")
    )
    ids = [entry["id"] for entry in manifest["inputs"]]
    assert ids == ["table2", "table4", "ztf2g", "ztf2r"]
    assert manifest["status"] == "BLOCKED"
    assert manifest["never_run"]  # the limitation must stay stated


# ---------------------------------------------------------------------------
# The status document's epistemic labels are a reviewable claim.
#
# An earlier revision of this document labelled the table4.ID = table2.Seq
# relation and the four-way partition VERIFIED FACT. Both were withdrawn as
# overclaims. These tests keep the withdrawal from silently regressing, because
# a document that quietly re-promotes a hypothesis is worse than no document.
# ---------------------------------------------------------------------------


def _status_doc() -> str:
    repo = Path(__file__).resolve().parents[1]
    return (repo / "docs/CPVS_RESOLUTION_STATUS_2026-10-25.md").read_text(
        encoding="utf-8"
    )


def test_status_doc_does_not_call_the_id_seq_relation_verified():
    text = _status_doc()
    assert "CORROBORATING, NOT PROVEN" in text
    # The only place the two may appear together is the retraction itself.
    for line in text.splitlines():
        if "table4.ID" in line and "table2.Seq" in line and "VERIFIED" in line:
            assert "was labelled" in line, line
            assert "withdrawn" in line or "now" in line, line


def test_status_doc_states_the_gate_is_unresolved():
    text = _status_doc()
    assert "Status: UNRESOLVED" in text
    assert "scientific gate stays closed" in text.lower()


def test_status_doc_does_not_present_a_count_match_as_the_cause():
    text = _status_doc()
    assert "count match is not an explanation" in text.lower()
    assert "candidate mechanism" in text.lower()


def test_status_doc_records_the_access_limitation():
    text = _status_doc()
    assert "not reachable from" in text
    assert "HTTP `000`" in text


def test_harness_defaults_to_unresolved_even_on_perfect_agreement(tmp_path: Path):
    """A perfect match must still not flip the status to resolved.

    Resolution requires the real data and a human decision; the script's job is
    to report, not to bless.
    """
    table2 = write(
        tmp_path / "table2.dat",
        [
            table2_line("ZTFJ000000.00+000000.0", 1),
            table2_line("ZTFJ000001.00+000000.0", 2),
        ],
    )
    table4 = write(
        tmp_path / "table4.dat",
        [
            table4_line("ZTFJ000000.00+000000.0", 1),
            table4_line("ZTFJ000001.00+000000.0", 2),
        ],
    )
    photo = [photometry_line(1, 18.0, 0.1), photometry_line(2, 18.0, 0.1)]
    ztf2g = write(tmp_path / "ztf2g.dat", photo)
    ztf2r = write(tmp_path / "ztf2r.dat", photo)

    manifest = build_report(
        table2_path=table2,
        table4_path=table4,
        ztf2g_path=ztf2g,
        ztf2r_path=ztf2r,
        output_dir=tmp_path / "out",
        rules=[DetectionRule()],
    )
    # Every route agrees perfectly...
    routes = manifest["comparison"]["routes"]
    assert all(route["exact_set_equality"] for route in routes.values())
    # ...and the status is still UNRESOLVED.
    assert manifest["status"] == "UNRESOLVED"
