"""Tests for GHOSV Execution bounded offline observer."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from src.ops.full_core_live_path_composition_root_v1.current_productive_governed_cycle_orchestrator_v1 import (
    LEDGER_FILENAME,
)
from src.ops.full_core_live_path_composition_root_v1.current_productive_persisted_reconciliation_disposition_v1 import (
    CONTRACT_ID as G004_CONTRACT_ID,
    attempt_digest_v1,
)
from src.ops.ghosv_bounded_context_v1.constants_v1 import ADAPTER_MODE, SAFETY_ESCALATION_ENABLED
from src.ops.ghosv_bounded_context_v1.execution_bounded_offline_observer_v1 import (
    REPORT_FILENAME,
    OutputPathSafetyError,
    ExecutionOfflineObserverPathsV1,
    assert_output_dir_safe_v1,
    run_execution_bounded_offline_observer_v1,
)
from src.ops.ghosv_bounded_context_v1.execution_offline_consistency_guard_v1 import (
    BoundedInputError,
    MAX_FILE_BYTES,
    run_consistency_guard_v1,
    verify_recon_bundle_v1,
)
from src.ops.productive_reconciliation_runtime_binding_v1.persistence_v1 import write_manifest

REPO = Path(__file__).resolve().parents[2]
CAP11_FIXTURE = (
    REPO
    / "docs/evidence/capability_1_1_productive_reconciliation_runtime_binding_v1/clean_start_match"
)
PRE_EXTERNAL_FIXTURE = (
    REPO
    / "tests/fixtures/current_productive_golden_happy_vector_post_7065_reference_v1/PRE_EXTERNAL_CONVERGENCE_REPORT.json"
)


def _write_cycle_dir(
    tmp_path: Path,
    *,
    ledger: dict,
    transitions: list[dict] | None = None,
    malformed_tail: str | None = None,
) -> Path:
    root = tmp_path / "cycle"
    root.mkdir(parents=True)
    (root / LEDGER_FILENAME).write_text(json.dumps(ledger, indent=2), encoding="utf-8")
    if transitions is not None or malformed_tail is not None:
        lines: list[str] = []
        if transitions:
            lines.extend(json.dumps(row, sort_keys=True) for row in transitions)
        if malformed_tail is not None:
            lines.append(malformed_tail)
        (root / "transitions.jsonl").write_text("\n".join(lines) + "\n", encoding="utf-8")
    return root


def _base_ledger(**extra: object) -> dict:
    payload = {
        "state": "COMPLETED",
        "binding_digest": "digest-a",
        "cycle_owner_go": "OWNER_GO_CURRENT_PRODUCTIVE_GOVERNED_CYCLE_ORCHESTRATOR_V1",
        "native_id": "BTC-USDT-SWAP",
        "POST_COUNT": "0",
        "PERMIT_CREATED": "false",
    }
    payload.update(extra)
    return payload


def _run_observer(tmp_path: Path, **kwargs: object) -> dict:
    out = tmp_path / "observer_out"
    paths = ExecutionOfflineObserverPathsV1(
        trade_id=str(kwargs.get("trade_id", "observer-test")),
        output_dir=out,
        recon_dir=kwargs.get("recon_dir"),
        pre_external_report=kwargs.get("pre_external_report"),
        final_order_envelope=kwargs.get("final_order_envelope"),
        governed_cycle_evidence_dir=kwargs.get("governed_cycle_evidence_dir"),
        g004_post_attempt_store_root=kwargs.get("g004_post_attempt_store_root"),
    )
    return run_execution_bounded_offline_observer_v1(paths)


def test_valid_recon_manifest_cap11_fixture(tmp_path: Path):
    report = _run_observer(tmp_path, recon_dir=CAP11_FIXTURE)
    assert report["observer_run_success"] is True
    assert report["source_consistency"]["recon_manifest_validation"] == "PASS"
    assert report["ghosv_traffic_light"] in {"GREEN", "YELLOW", "RED"}
    assert (tmp_path / "observer_out" / REPORT_FILENAME).is_file()


def test_missing_manifest_fail_closed(tmp_path: Path):
    recon = tmp_path / "recon"
    recon.mkdir()
    (recon / "productive_reconciliation_evidence_v1.json").write_text("{}", encoding="utf-8")
    guard = run_consistency_guard_v1(
        recon_dir=recon,
        pre_external_report=None,
        final_order_envelope=None,
        governed_cycle_evidence_dir=None,
        g004_post_attempt_store_root=None,
    )
    assert guard.recon.consistency == "FAIL"
    assert "MANIFEST_MISSING" in guard.recon.reason_codes


def test_manifest_digest_mismatch(tmp_path: Path):
    recon = tmp_path / "recon_bad"
    recon.mkdir()
    (recon / "productive_portfolio_state_v1.json").write_text(
        '{"positions":[]}\n', encoding="utf-8"
    )
    (recon / "productive_reconciliation_evidence_v1.json").write_text(
        '{"classification":"MATCH"}\n', encoding="utf-8"
    )
    write_manifest(
        recon, ("productive_portfolio_state_v1.json", "productive_reconciliation_evidence_v1.json")
    )
    (recon / "productive_reconciliation_evidence_v1.json").write_text(
        '{"classification":"DRIFT"}\n', encoding="utf-8"
    )
    result = verify_recon_bundle_v1(recon)
    assert result.consistency == "FAIL"
    assert any("DIGEST_MISMATCH" in c for c in result.reason_codes)


def test_ledger_truncated_json(tmp_path: Path):
    cycle = tmp_path / "cycle"
    cycle.mkdir()
    (cycle / LEDGER_FILENAME).write_text('{"state": "COMP', encoding="utf-8")
    guard = run_consistency_guard_v1(
        recon_dir=None,
        pre_external_report=None,
        final_order_envelope=None,
        governed_cycle_evidence_dir=cycle,
        g004_post_attempt_store_root=None,
    )
    assert guard.ledger.consistency == "FAIL"


def test_transitions_truncated_tail(tmp_path: Path):
    root = _write_cycle_dir(
        tmp_path,
        ledger=_base_ledger(),
        transitions=[_base_ledger(state="IN_PROGRESS")],
        malformed_tail='{"state":',
    )
    guard = run_consistency_guard_v1(
        recon_dir=None,
        pre_external_report=None,
        final_order_envelope=None,
        governed_cycle_evidence_dir=root,
        g004_post_attempt_store_root=None,
    )
    assert guard.transitions.consistency == "UNKNOWN"
    assert "MALFORMED_OR_TRUNCATED_JSONL" in guard.transitions.reason_codes


def test_duplicate_transition(tmp_path: Path):
    row = _base_ledger(state="IN_PROGRESS")
    root = _write_cycle_dir(tmp_path, ledger=_base_ledger(), transitions=[row, row])
    guard = run_consistency_guard_v1(
        recon_dir=None,
        pre_external_report=None,
        final_order_envelope=None,
        governed_cycle_evidence_dir=root,
        g004_post_attempt_store_root=None,
    )
    assert "DUPLICATE_ADJACENT_TRANSITION" in guard.transitions.reason_codes


def test_pre_external_without_post_submission_witness(tmp_path: Path):
    if not PRE_EXTERNAL_FIXTURE.is_file():
        pytest.skip("pre external fixture missing")
    report = _run_observer(tmp_path, pre_external_report=PRE_EXTERNAL_FIXTURE)
    assert report["execution_lifecycle_completeness"] == "PRE_EXTERNAL_ONLY"
    assert report["observer_run_success"] is True
    missing = report["missing_evidence_classes"]
    assert "POST_SUBMISSION_WITNESS" in missing
    assert missing.count("POST_SUBMISSION_WITNESS") == 1


def test_explicit_post_count_zero_cycle(tmp_path: Path):
    root = _write_cycle_dir(
        tmp_path,
        ledger=_base_ledger(POST_COUNT="0"),
        transitions=[_base_ledger(state="IN_PROGRESS"), _base_ledger(state="COMPLETED")],
    )
    report = _run_observer(tmp_path, governed_cycle_evidence_dir=root)
    assert report["observer_run_success"] is True
    assert report["execution_lifecycle_completeness"] == "POST_SUBMISSION_WITNESSED"


def test_missing_post_count_unknown(tmp_path: Path):
    ledger = _base_ledger()
    del ledger["POST_COUNT"]
    root = _write_cycle_dir(tmp_path, ledger=ledger)
    report = _run_observer(tmp_path, governed_cycle_evidence_dir=root)
    assert report["observer_run_success"] is True
    assert report["ghosv_traffic_light"] in {"YELLOW", "RED", "UNKNOWN"}


def test_local_cancelled_stop(tmp_path: Path):
    root = _write_cycle_dir(
        tmp_path,
        ledger=_base_ledger(state="CANCELLED_STOP", reason_code="CANCELLED"),
        transitions=[_base_ledger(state="CANCELLED_STOP", reason_code="CANCELLED")],
    )
    report = _run_observer(tmp_path, governed_cycle_evidence_dir=root)
    assert report["observer_run_success"] is True


def test_missing_optional_g004(tmp_path: Path):
    store = tmp_path / "g004_empty"
    store.mkdir()
    report = _run_observer(tmp_path, g004_post_attempt_store_root=store, recon_dir=CAP11_FIXTURE)
    assert report["source_consistency"]["g004_consistency"] == "NOT_APPLICABLE"
    assert report["observer_run_success"] is True


def test_malformed_g004(tmp_path: Path):
    store = tmp_path / "g004_bad"
    store.mkdir()
    (store / "full_core_post_attempt_exchange_reconciliation_disposition_v1.json").write_text(
        "{not-json", encoding="utf-8"
    )
    guard = run_consistency_guard_v1(
        recon_dir=None,
        pre_external_report=None,
        final_order_envelope=None,
        governed_cycle_evidence_dir=None,
        g004_post_attempt_store_root=store,
    )
    assert guard.g004.consistency == "UNKNOWN"


def test_valid_g004_guard_pass_not_partial(tmp_path: Path):
    store = tmp_path / "g004_ok"
    store.mkdir()
    submit_attempt_id = "attempt-1"
    envelope_digest = "env-digest"
    record = {
        "contract_id": G004_CONTRACT_ID,
        "submit_attempt_id": submit_attempt_id,
        "clordid": "cl-1",
        "envelope_digest": envelope_digest,
        "attempt_digest": attempt_digest_v1(
            submit_attempt_id=submit_attempt_id,
            envelope_digest=envelope_digest,
        ),
        "native_id": "BTC-USDT-SWAP",
        "reconciliation_outcome": "CONFIRMED_FILLED",
        "typed_post_submit_outcome": "ACKNOWLEDGED",
        "local_submit_outcome": "SUBMITTED",
        "ack_is_not_fill": True,
    }
    (store / "full_core_post_attempt_exchange_reconciliation_disposition_v1.json").write_text(
        json.dumps(record), encoding="utf-8"
    )
    guard = run_consistency_guard_v1(
        recon_dir=None,
        pre_external_report=None,
        final_order_envelope=None,
        governed_cycle_evidence_dir=None,
        g004_post_attempt_store_root=store,
    )
    assert guard.g004.consistency == "PASS"
    assert guard.evidence_consistency == "PASS"


def test_g004_confirmed_filled_not_standalone_fill(tmp_path: Path):
    store = tmp_path / "g004_ok"
    store.mkdir()
    submit_attempt_id = "attempt-1"
    envelope_digest = "env-digest"
    record = {
        "contract_id": G004_CONTRACT_ID,
        "submit_attempt_id": submit_attempt_id,
        "clordid": "cl-1",
        "envelope_digest": envelope_digest,
        "attempt_digest": attempt_digest_v1(
            submit_attempt_id=submit_attempt_id,
            envelope_digest=envelope_digest,
        ),
        "native_id": "BTC-USDT-SWAP",
        "reconciliation_outcome": "CONFIRMED_FILLED",
        "typed_post_submit_outcome": "ACKNOWLEDGED",
        "local_submit_outcome": "SUBMITTED",
        "ack_is_not_fill": True,
    }
    (store / "full_core_post_attempt_exchange_reconciliation_disposition_v1.json").write_text(
        json.dumps(record), encoding="utf-8"
    )
    report = _run_observer(tmp_path, g004_post_attempt_store_root=store, recon_dir=CAP11_FIXTURE)
    assert report["observer_run_success"] is True
    kinds = report["missing_evidence_classes"]
    assert "FILL" in kinds or "FULL_FILL" in kinds


def test_cross_file_native_id_mismatch(tmp_path: Path):
    if not PRE_EXTERNAL_FIXTURE.is_file():
        pytest.skip("pre external fixture missing")
    root = _write_cycle_dir(tmp_path, ledger=_base_ledger(native_id="ETH-USDT-SWAP"))
    report = _run_observer(
        tmp_path,
        pre_external_report=PRE_EXTERNAL_FIXTURE,
        governed_cycle_evidence_dir=root,
    )
    assert report["source_consistency"]["evidence_consistency"] == "FAIL"


def test_oversized_input(tmp_path: Path):
    huge = tmp_path / "huge.json"
    huge.write_bytes(b"x" * (MAX_FILE_BYTES + 1))
    with pytest.raises(BoundedInputError):
        run_consistency_guard_v1(
            recon_dir=None,
            pre_external_report=huge,
            final_order_envelope=None,
            governed_cycle_evidence_dir=None,
            g004_post_attempt_store_root=None,
        )


def test_output_outside_source_directories(tmp_path: Path):
    recon = tmp_path / "recon"
    recon.mkdir()
    out = tmp_path / "out"
    assert_output_dir_safe_v1(output_dir=out, source_paths=(recon,))
    report = _run_observer(tmp_path, recon_dir=CAP11_FIXTURE)
    out_path = Path(report["report_path"])
    assert CAP11_FIXTURE not in out_path.parents


def test_output_inside_source_rejected(tmp_path: Path):
    with pytest.raises(OutputPathSafetyError):
        assert_output_dir_safe_v1(
            output_dir=CAP11_FIXTURE / "nested", source_paths=(CAP11_FIXTURE,)
        )


def test_source_inside_output_rejected(tmp_path: Path):
    out = tmp_path / "out"
    out.mkdir()
    recon = out / "recon"
    recon.mkdir()
    with pytest.raises(OutputPathSafetyError):
        assert_output_dir_safe_v1(output_dir=out, source_paths=(recon,))


def test_symlink_output_to_source_rejected(tmp_path: Path):
    recon = tmp_path / "recon"
    recon.mkdir()
    alias_out = tmp_path / "alias_out"
    alias_out.symlink_to(recon)
    with pytest.raises(OutputPathSafetyError):
        assert_output_dir_safe_v1(output_dir=alias_out, source_paths=(recon,))


def test_no_productive_source_mutation(tmp_path: Path):
    if not PRE_EXTERNAL_FIXTURE.is_file():
        pytest.skip("pre external fixture missing")
    before = PRE_EXTERNAL_FIXTURE.stat().st_mtime_ns
    _run_observer(tmp_path, pre_external_report=PRE_EXTERNAL_FIXTURE)
    after = PRE_EXTERNAL_FIXTURE.stat().st_mtime_ns
    assert before == after


def test_s06_remains_disabled(tmp_path: Path):
    report = _run_observer(tmp_path, recon_dir=CAP11_FIXTURE)
    safety = report["safety_adapter_status"]
    assert safety["adapter_mode"] == ADAPTER_MODE == "DISABLED"
    assert safety["safety_escalation_enabled"] is False


def test_cli_success_not_green_assessment(tmp_path: Path):
    report = _run_observer(tmp_path, recon_dir=CAP11_FIXTURE)
    assert report["disclaimer"]["cli_exit_not_traffic_green"] is True
    assert report["observer_run_status"] == "OBSERVER_RUN_SUCCESS"


def test_transitions_optional_absent_not_applicable(tmp_path: Path):
    cycle = tmp_path / "cycle"
    cycle.mkdir()
    (cycle / LEDGER_FILENAME).write_text(json.dumps(_base_ledger()), encoding="utf-8")
    guard = run_consistency_guard_v1(
        recon_dir=None,
        pre_external_report=None,
        final_order_envelope=None,
        governed_cycle_evidence_dir=cycle,
        g004_post_attempt_store_root=None,
    )
    assert guard.transitions.consistency == "NOT_APPLICABLE"
    assert guard.transitions.presence == "SOURCE_NOT_PRESENT"


def test_cross_file_evidence_root_prefix_trap(tmp_path: Path):
    evidence_root = tmp_path / "runs" / "abc"
    evidence_root.mkdir(parents=True)
    cycle = tmp_path / "runs" / "abcdef"
    cycle.mkdir(parents=True)
    (cycle / LEDGER_FILENAME).write_text(json.dumps(_base_ledger()), encoding="utf-8")
    pre = tmp_path / "pre.json"
    pre.write_text(
        json.dumps(
            {
                "NATIVE_ID": "BTC-USDT-SWAP",
                "RUN_ID": "run-1",
                "EVIDENCE_ROOT": str(evidence_root),
            }
        ),
        encoding="utf-8",
    )
    guard = run_consistency_guard_v1(
        recon_dir=None,
        pre_external_report=pre,
        final_order_envelope=None,
        governed_cycle_evidence_dir=cycle,
        g004_post_attempt_store_root=None,
    )
    assert "RUN_CYCLE_PATH_NOT_UNDER_EVIDENCE_ROOT" in guard.cross_file.reason_codes


def test_malformed_pre_external_still_writes_report(tmp_path: Path):
    sources = tmp_path / "sources"
    sources.mkdir()
    bad_pre = sources / "pre_bad.json"
    bad_pre.write_text("{not-json", encoding="utf-8")
    report = _run_observer(tmp_path, pre_external_report=bad_pre)
    assert (tmp_path / "observer_out" / REPORT_FILENAME).is_file()
    assert report["observer_run_status"] == "OBSERVER_RUN_FAILED"
    assert report["ghosv_pipeline_error"] is not None
    assert report["ghosv_traffic_light"] == "UNKNOWN"


def test_valid_completed_cycle_guard_pass(tmp_path: Path):
    root = _write_cycle_dir(
        tmp_path,
        ledger=_base_ledger(),
        transitions=[_base_ledger(state="IN_PROGRESS"), _base_ledger(state="COMPLETED")],
    )
    guard = run_consistency_guard_v1(
        recon_dir=None,
        pre_external_report=None,
        final_order_envelope=None,
        governed_cycle_evidence_dir=root,
        g004_post_attempt_store_root=None,
    )
    assert guard.ledger.consistency == "PASS"
    assert guard.transitions.consistency == "PASS"
