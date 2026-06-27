"""Producer tests for Package J offline VAR_SUITE LineageRef production."""

from __future__ import annotations

import hashlib
import json
import os
import stat
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from src.governance.promotion_loop.candidate_lineage_manifest_v1 import (
    CandidateType,
    LineageRefType,
    LineageRelation,
    build_candidate_lineage_manifest_v1_from_producer_input,
    lineage_ref_to_mapping,
    serialize_candidate_lineage_manifest_v1,
    validate_candidate_lineage_manifest_v1,
)
from src.governance.promotion_loop.var_suite_lineage_ref_producer_v1 import (
    SUITE_REPORT_JSON,
    VAR_SUITE_LINEAGE_REF_REQUIRED,
    VAR_SUITE_OWNER_DOMAIN,
    VarSuiteLineageRefProducerError,
    build_var_suite_lineage_ref_from_report_dir,
    compute_var_suite_lineage_ref_digest,
    produce_var_suite_lineage_ref_v1,
    produce_var_suite_lineage_ref_v1_to_path,
    serialize_var_suite_lineage_ref_v1,
    write_var_suite_lineage_ref_v1_atomic,
)
from src.risk.validation.var_suite_backtest_wiring_v1 import SUITE_REPORT_JSON as WIRING_JSON

LINEAGE_ID = "11111111-1111-4111-8111-111111111111"
CONTRACT_REF = "22222222-2222-4222-8222-222222222222"
REPORT_DIR_NAME = "suite-run-001"


def _minimal_suite_report_data(*, overall_result: str = "PASS") -> dict:
    return {"overall_result": overall_result}


def _full_suite_report_data(*, overall_result: str = "PASS") -> dict:
    return {
        "overall_result": overall_result,
        "observations": 250,
        "breaches": 3,
        "confidence_level": 0.95,
        "kupiec_pof_result": "PASS",
        "kupiec_pof_pvalue": 0.78,
        "basel_traffic_light": "GREEN",
        "christoffersen_ind_result": "PASS",
        "christoffersen_ind_pvalue": 0.88,
        "christoffersen_cc_result": "PASS",
        "christoffersen_cc_pvalue": 0.92,
    }


def _write_report_dir(
    tmp_path: Path,
    data: dict,
    *,
    report_dir_name: str = REPORT_DIR_NAME,
    indent: int | None = 2,
) -> Path:
    report_dir = tmp_path / report_dir_name
    report_dir.mkdir()
    report_path = report_dir / SUITE_REPORT_JSON
    if indent is None:
        report_path.write_bytes(json.dumps(data, separators=(",", ":")).encode("utf-8"))
    else:
        report_path.write_text(json.dumps(data, indent=indent), encoding="utf-8")
    return report_dir


def test_minimal_report_dir_produces_valid_var_suite_ref(tmp_path: Path) -> None:
    report_dir = _write_report_dir(tmp_path, _minimal_suite_report_data())
    result = produce_var_suite_lineage_ref_v1(report_dir=report_dir)
    ref = result.ref
    assert ref.ref_type == LineageRefType.VAR_SUITE
    assert ref.ref_id == REPORT_DIR_NAME
    assert ref.relation == LineageRelation.VALIDATES
    assert ref.owner_domain == VAR_SUITE_OWNER_DOMAIN
    assert ref.required is VAR_SUITE_LINEAGE_REF_REQUIRED
    assert ref.artifact_path == SUITE_REPORT_JSON
    report_bytes = result.suite_report_path.read_bytes()
    assert ref.digest == compute_var_suite_lineage_ref_digest(report_bytes)


def test_full_report_dir_produces_valid_var_suite_ref(tmp_path: Path) -> None:
    report_dir = _write_report_dir(tmp_path, _full_suite_report_data())
    result = produce_var_suite_lineage_ref_v1(report_dir=report_dir)
    assert result.ref.ref_id == REPORT_DIR_NAME
    payload = json.loads(serialize_var_suite_lineage_ref_v1(result.ref))
    assert "observations" not in payload
    assert "breaches" not in payload
    assert "overall_result" not in payload
    assert "kupiec_pof_pvalue" not in payload


def test_ref_id_equals_report_dir_name(tmp_path: Path) -> None:
    explicit_name = "canonical-suite-run-42"
    report_dir = _write_report_dir(
        tmp_path,
        _minimal_suite_report_data(),
        report_dir_name=explicit_name,
    )
    result = produce_var_suite_lineage_ref_v1(report_dir=report_dir)
    assert result.ref.ref_id == explicit_name


def test_uses_suite_report_json_file(tmp_path: Path) -> None:
    report_dir = _write_report_dir(tmp_path, _minimal_suite_report_data())
    result = produce_var_suite_lineage_ref_v1(report_dir=report_dir)
    assert result.suite_report_path.name == WIRING_JSON
    assert result.suite_report_path == report_dir / SUITE_REPORT_JSON


def test_deterministic_digest_and_relative_artifact_path(tmp_path: Path) -> None:
    report_dir = _write_report_dir(tmp_path, _full_suite_report_data())
    first = produce_var_suite_lineage_ref_v1(report_dir=report_dir)
    second = produce_var_suite_lineage_ref_v1(report_dir=report_dir)
    assert first.ref.digest == second.ref.digest
    assert first.ref.artifact_path == SUITE_REPORT_JSON
    assert not first.ref.artifact_path.startswith("/")


def test_byte_identical_canonical_json_output(tmp_path: Path) -> None:
    report_dir = _write_report_dir(tmp_path, _minimal_suite_report_data())
    result = produce_var_suite_lineage_ref_v1(report_dir=report_dir)
    first = serialize_var_suite_lineage_ref_v1(result.ref)
    second = serialize_var_suite_lineage_ref_v1(result.ref)
    assert first == second
    assert json.loads(first) == json.loads(second)


def test_candidate_lineage_manifest_v1_accepts_producer_output(tmp_path: Path) -> None:
    report_dir = _write_report_dir(tmp_path, _minimal_suite_report_data())
    ref = produce_var_suite_lineage_ref_v1(report_dir=report_dir).ref
    fixed_now = datetime(2026, 6, 27, 18, 0, 0, tzinfo=timezone.utc)
    manifest = build_candidate_lineage_manifest_v1_from_producer_input(
        {
            "lineage_manifest_id": LINEAGE_ID,
            "candidate_id": "candidate-package-j-001",
            "candidate_type": CandidateType.CONFIG_PATCH_BUNDLE.value,
            "candidate_contract_ref": CONTRACT_REF,
            "refs": [lineage_ref_to_mapping(ref)],
            "created_at": fixed_now.isoformat(),
        },
        created_at=fixed_now,
    )
    payload = json.loads(serialize_candidate_lineage_manifest_v1(manifest))
    valid, phase, errors, _ = validate_candidate_lineage_manifest_v1(payload)
    assert valid is True, (phase, errors)
    assert payload["refs"][0]["ref_id"] == REPORT_DIR_NAME
    assert payload["refs"][0]["ref_type"] == LineageRefType.VAR_SUITE.value


def test_missing_report_dir_fails_closed(tmp_path: Path) -> None:
    with pytest.raises(VarSuiteLineageRefProducerError, match="report_dir not found"):
        produce_var_suite_lineage_ref_v1(report_dir=tmp_path / "missing")


def test_report_path_is_file_not_directory(tmp_path: Path) -> None:
    file_path = tmp_path / "not-a-dir"
    file_path.write_text("x", encoding="utf-8")
    with pytest.raises(VarSuiteLineageRefProducerError, match="not a directory"):
        produce_var_suite_lineage_ref_v1(report_dir=file_path)


def test_missing_suite_report_json_fails_closed(tmp_path: Path) -> None:
    report_dir = tmp_path / "empty-report"
    report_dir.mkdir()
    with pytest.raises(VarSuiteLineageRefProducerError, match="suite_report.json not found"):
        produce_var_suite_lineage_ref_v1(report_dir=report_dir)


def test_suite_report_is_directory_fails_closed(tmp_path: Path) -> None:
    report_dir = tmp_path / "bad-report"
    report_dir.mkdir()
    (report_dir / SUITE_REPORT_JSON).mkdir()
    with pytest.raises(VarSuiteLineageRefProducerError, match="is a directory"):
        produce_var_suite_lineage_ref_v1(report_dir=report_dir)


def test_invalid_json_fails_closed(tmp_path: Path) -> None:
    report_dir = tmp_path / "bad-json-report"
    report_dir.mkdir()
    (report_dir / SUITE_REPORT_JSON).write_text("{not-json", encoding="utf-8")
    with pytest.raises(VarSuiteLineageRefProducerError, match="invalid suite_report.json"):
        produce_var_suite_lineage_ref_v1(report_dir=report_dir)


def test_invalid_root_structure_fails_closed(tmp_path: Path) -> None:
    report_dir = tmp_path / "array-root"
    report_dir.mkdir()
    (report_dir / SUITE_REPORT_JSON).write_text("[]", encoding="utf-8")
    with pytest.raises(VarSuiteLineageRefProducerError, match="root must be a JSON object"):
        produce_var_suite_lineage_ref_v1(report_dir=report_dir)


def test_missing_overall_result_fails_closed(tmp_path: Path) -> None:
    report_dir = _write_report_dir(tmp_path, {"observations": 10})
    with pytest.raises(VarSuiteLineageRefProducerError, match="missing overall_result"):
        produce_var_suite_lineage_ref_v1(report_dir=report_dir)


@pytest.mark.parametrize("overall_result", ["PASS", "FAIL", "WARN", "UNKNOWN", ""])
def test_overall_result_values_structurally_accepted_not_interpreted(
    tmp_path: Path, overall_result: str
) -> None:
    report_dir = _write_report_dir(tmp_path, {"overall_result": overall_result})
    result = produce_var_suite_lineage_ref_v1(report_dir=report_dir)
    assert result.ref.ref_id == REPORT_DIR_NAME


def test_unsafe_ref_id_dot_fails_closed() -> None:
    report_dir = MagicMock(spec=Path)
    report_dir.name = "."
    with pytest.raises(VarSuiteLineageRefProducerError, match="ref_id is unsafe"):
        build_var_suite_lineage_ref_from_report_dir(
            report_dir,
            report_bytes=b'{"overall_result":"PASS"}',
        )


def test_report_dir_symlink_fails_closed(tmp_path: Path) -> None:
    real_dir = _write_report_dir(
        tmp_path, _minimal_suite_report_data(), report_dir_name="real-report"
    )
    link = tmp_path / "linked-report"
    link.symlink_to(real_dir, target_is_directory=True)
    with pytest.raises(VarSuiteLineageRefProducerError, match="must not be a symlink"):
        produce_var_suite_lineage_ref_v1(report_dir=link)


def test_suite_report_symlink_fails_closed(tmp_path: Path) -> None:
    report_dir = tmp_path / "report-with-link"
    report_dir.mkdir()
    external = tmp_path / "external_report.json"
    external.write_text(json.dumps(_minimal_suite_report_data()), encoding="utf-8")
    (report_dir / SUITE_REPORT_JSON).symlink_to(external)
    with pytest.raises(VarSuiteLineageRefProducerError, match="must not be a symlink"):
        produce_var_suite_lineage_ref_v1(report_dir=report_dir)


def test_mtime_does_not_change_digest(tmp_path: Path) -> None:
    report_dir = _write_report_dir(tmp_path, _minimal_suite_report_data())
    first = produce_var_suite_lineage_ref_v1(report_dir=report_dir).ref.digest
    report_path = report_dir / SUITE_REPORT_JSON
    old = report_path.stat().st_mtime
    os.utime(report_path, (old + 3600, old + 3600))
    second = produce_var_suite_lineage_ref_v1(report_dir=report_dir).ref.digest
    assert first == second


def test_byte_change_changes_digest(tmp_path: Path) -> None:
    report_dir = _write_report_dir(tmp_path, _minimal_suite_report_data())
    first = produce_var_suite_lineage_ref_v1(report_dir=report_dir).ref.digest
    report_path = report_dir / SUITE_REPORT_JSON
    report_path.write_text(
        json.dumps({"overall_result": "PASS", "extra": 1}, indent=2),
        encoding="utf-8",
    )
    second = produce_var_suite_lineage_ref_v1(report_dir=report_dir).ref.digest
    assert first != second


def test_suite_report_file_not_modified(tmp_path: Path) -> None:
    report_dir = _write_report_dir(tmp_path, _minimal_suite_report_data())
    report_path = report_dir / SUITE_REPORT_JSON
    before = report_path.read_bytes()
    produce_var_suite_lineage_ref_v1(report_dir=report_dir)
    assert report_path.read_bytes() == before


def test_digest_matches_sha256_of_exact_file_bytes(tmp_path: Path) -> None:
    report_dir = _write_report_dir(tmp_path, _full_suite_report_data(), indent=None)
    report_bytes = (report_dir / SUITE_REPORT_JSON).read_bytes()
    ref = build_var_suite_lineage_ref_from_report_dir(report_dir, report_bytes=report_bytes)
    assert ref.digest == hashlib.sha256(report_bytes).hexdigest()


def test_atomic_writer_success_and_fail_closed_existing(tmp_path: Path) -> None:
    report_dir = _write_report_dir(tmp_path, _minimal_suite_report_data())
    ref = produce_var_suite_lineage_ref_v1(report_dir=report_dir).ref
    output_path = tmp_path / "ref.json"
    write_var_suite_lineage_ref_v1_atomic(ref, output_path)
    assert output_path.is_file()
    with pytest.raises(VarSuiteLineageRefProducerError, match="already exists"):
        write_var_suite_lineage_ref_v1_atomic(ref, output_path)


def test_end_to_end_producer_writes_output(tmp_path: Path) -> None:
    report_dir = _write_report_dir(tmp_path, _minimal_suite_report_data())
    output_path = tmp_path / "out" / "var_suite_ref.json"
    produce_var_suite_lineage_ref_v1_to_path(report_dir=report_dir, output_path=output_path)
    payload = json.loads(output_path.read_text(encoding="utf-8"))
    assert payload["ref_type"] == LineageRefType.VAR_SUITE.value
    assert payload["ref_id"] == REPORT_DIR_NAME


def test_non_writable_output_parent_fails_without_partial_output(tmp_path: Path) -> None:
    report_dir = _write_report_dir(tmp_path, _minimal_suite_report_data())
    readonly_parent = tmp_path / "readonly"
    readonly_parent.mkdir()
    output_path = readonly_parent / "ref.json"
    os.chmod(readonly_parent, stat.S_IRUSR | stat.S_IXUSR)
    try:
        with pytest.raises(OSError):
            produce_var_suite_lineage_ref_v1_to_path(report_dir=report_dir, output_path=output_path)
    finally:
        os.chmod(readonly_parent, stat.S_IRWXU)
    assert not output_path.exists()
    assert not output_path.with_name(output_path.name + ".tmp").exists()


def test_writer_replace_failure_cleans_tmp_and_leaves_existing_output(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    report_dir = _write_report_dir(tmp_path, _minimal_suite_report_data())
    ref = produce_var_suite_lineage_ref_v1(report_dir=report_dir).ref
    output_path = tmp_path / "ref.json"
    output_path.write_text('{"existing": true}', encoding="utf-8")
    original = Path.replace

    def _fail_replace(self, target):  # type: ignore[no-untyped-def]
        if self.name.endswith(".tmp"):
            raise OSError("forced replace failure")
        return original(self, target)

    monkeypatch.setattr(Path, "replace", _fail_replace)
    with pytest.raises(OSError, match="forced replace failure"):
        write_var_suite_lineage_ref_v1_atomic(
            ref,
            output_path,
            fail_closed_if_exists=False,
        )
    assert output_path.read_text(encoding="utf-8") == '{"existing": true}'
    assert list(output_path.parent.glob("*.tmp")) == []


def test_fixture_report_dir_integration(tmp_path: Path) -> None:
    fixture_root = (
        Path(__file__).parent.parent.parent / "fixtures" / "var_suite_reports" / "run_pass_all"
    )
    result = produce_var_suite_lineage_ref_v1(report_dir=fixture_root)
    assert result.ref.ref_id == "run_pass_all"
    assert (
        result.ref.digest
        == hashlib.sha256((fixture_root / SUITE_REPORT_JSON).read_bytes()).hexdigest()
    )


def test_no_var_suite_or_runtime_side_effects(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    report_dir = _write_report_dir(tmp_path, _minimal_suite_report_data())

    def _forbidden(*args, **kwargs):  # type: ignore[no-untyped-def]
        raise AssertionError("VaR suite or runtime invocation forbidden")

    monkeypatch.setattr(
        "src.risk.validation.var_suite_backtest_wiring_v1.run_backtest_var_suite_wiring_v1",
        _forbidden,
    )
    monkeypatch.setattr(
        "src.risk.validation.var_suite_backtest_wiring_v1.resolve_backtest_returns",
        _forbidden,
    )
    produce_var_suite_lineage_ref_v1(report_dir=report_dir)


def test_absolute_path_not_in_serialized_ref(tmp_path: Path) -> None:
    report_dir = _write_report_dir(tmp_path, _minimal_suite_report_data())
    result = produce_var_suite_lineage_ref_v1(report_dir=report_dir)
    serialized = serialize_var_suite_lineage_ref_v1(result.ref)
    assert str(report_dir) not in serialized
    assert "/Users/" not in serialized
