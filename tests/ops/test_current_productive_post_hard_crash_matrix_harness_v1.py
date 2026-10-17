"""Hard-crash matrix harness for CURRENT productive Enter-POST (subprocess, offline)."""

from __future__ import annotations

import re
import socket
from pathlib import Path
from typing import Any

import pytest

from tests.ops._current_productive_post_hard_crash_harness_v1 import (
    CrashPointV1,
    RestartEvaluationReplayProbeError,
    assert_second_new_risk_admission_blocked_v1,
    bootstrap_unknown_post_store_v1,
    evaluate_restart_after_crash_v1,
    expected_crash_exit_v1,
    read_json_file_v1,
    run_adversarial_reconciliation_v1,
    spawn_hard_crash_child_v1,
    write_parent_mock_exchange_acceptance_stub_v1,
)
import tests.ops._current_productive_post_hard_crash_harness_v1 as hard_crash_harness_v1
from tests.ops._pilot_guard_enter_post_test_helpers_v1 import PILOT_TEST_INST
from tests.ops.test_current_productive_one_shot_fresh_envelope_permit_mint_durable_consume_and_post_join_v1 import (
    _new_risk_envelope,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.current_productive_unknown_post_attempt_read_only_reconciliation_v1 import (
    CONFIRMED_ACCEPTED_WORKING,
    CONFIRMED_REJECTED,
    STILL_UNKNOWN,
)


from tests.ops._post_path_safety_fixtures_v1 import activate_isolated_kill_switch_state_v1


@pytest.fixture(autouse=True)
def _active_kill_switch_state(
    monkeypatch: pytest.MonkeyPatch, tmp_path_factory: pytest.TempPathFactory
) -> None:
    activate_isolated_kill_switch_state_v1(
        monkeypatch, tmp_path_factory.mktemp("kill_switch_active")
    )


@pytest.fixture(autouse=True)
def _forbid_real_sockets(monkeypatch: pytest.MonkeyPatch) -> None:
    def _boom(*_args: Any, **_kwargs: Any) -> None:
        raise AssertionError("NETWORK_FORBIDDEN")

    monkeypatch.setattr(socket, "create_connection", _boom)
    monkeypatch.setattr(socket.socket, "connect", _boom)


def _run_crash_and_evaluate(tmp_path: Path, point: CrashPointV1, **extra: Any) -> tuple[Any, Any]:
    store = tmp_path / "store"
    child = spawn_hard_crash_child_v1(
        store_root=store,
        crash_point=point,
        extra=extra or None,
    )
    assert child.timed_out is False, child.stderr
    assert child.exit_code == expected_crash_exit_v1(point), (
        f"stderr={child.stderr!r} stdout={child.stdout!r}"
    )
    restart = evaluate_restart_after_crash_v1(store_root=store, crash_point=point)
    return child, restart


def test_c6_atomicity_single_write_no_split_sent_initiated() -> None:
    src = Path(
        "src/ops/full_core_live_path_composition_root_v1/external_effect_permit_durable_consume_v1.py"
    ).read_text(encoding="utf-8")
    fn = src.split("def persist_external_effect_durable_consume_v1", 1)[1].split(
        "def finalize_external_effect_durable_consume_v1", 1
    )[0]
    assert '"durable_state": durable_state' in fn
    persist_body = fn.split("\ndef ", 1)[0]
    assert persist_body.count("_atomic_write_state_v1(") == 1
    assert "with exclusive_store_root_lock_v1(root):" in persist_body
    assert persist_body.index("with exclusive_store_root_lock_v1(root):") < persist_body.index(
        "_atomic_write_state_v1("
    )
    assert "SENT_INITIATED" not in persist_body
    assert ".replace(path)" not in src


@pytest.mark.parametrize(
    "point,expect_correlation,expect_durable,expect_second_block",
    [
        (CrashPointV1.C1, False, False, False),
        (CrashPointV1.C2, False, False, False),
        (CrashPointV1.C3, True, False, False),
        (CrashPointV1.C4, True, False, False),
    ],
)
def test_early_crash_points_fail_closed_without_permit_replay(
    tmp_path: Path,
    point: CrashPointV1,
    expect_correlation: bool,
    expect_durable: bool,
    expect_second_block: bool,
) -> None:
    _, restart = _run_crash_and_evaluate(tmp_path, point)
    assert restart.correlation_present is expect_correlation
    assert restart.durable_consumed is expect_durable
    assert restart.mock_post_attempts_after_restart == 0
    if expect_second_block:
        assert restart.second_admission_blocked is True


def test_c6_crash_before_replace_leaves_no_durable_consume(tmp_path: Path) -> None:
    _, restart = _run_crash_and_evaluate(tmp_path, CrashPointV1.C6)
    assert restart.durable_consumed is False
    assert "DURABLE_CONSUME_TMP_PRESENT" in restart.notes or not restart.durable_consumed
    assert restart.mock_post_attempts_after_restart == 0


def test_c9_http200_crash_after_mapper_path_ack_before_lifecycle_join(
    tmp_path: Path,
) -> None:
    store = tmp_path / "store"
    accept_path = store / "mock_exchange_accept_v1.json"
    write_parent_mock_exchange_acceptance_stub_v1(accept_path)
    child = spawn_hard_crash_child_v1(
        store_root=store,
        crash_point=CrashPointV1.C9_HTTP200,
        extra={"mock_accept_evidence_path": str(accept_path)},
    )
    assert child.timed_out is False, child.stderr
    assert child.exit_code == expected_crash_exit_v1(CrashPointV1.C9_HTTP200)
    evidence = read_json_file_v1(accept_path)
    assert evidence.get("phase") == "CHILD_POST_TRANSPORT_PRE_LIFECYCLE_JOIN"
    assert evidence.get("classification") == "ACKNOWLEDGED"
    assert int(evidence.get("http_status") or 0) == 200
    assert (
        evidence.get("parent_stub") is True
        or evidence.get("schema") == "mock_exchange_acceptance_external_v1"
    )
    restart = evaluate_restart_after_crash_v1(store_root=store, crash_point=CrashPointV1.C9_HTTP200)
    assert restart.durable_consumed is True
    assert restart.durable_state == "SENT_INITIATED"
    assert restart.second_admission_blocked is True
    assert restart.mock_post_attempts_after_restart == 0


def test_c9_crash_after_transport_post_before_seam_return_preserves_fail_closed(
    tmp_path: Path,
) -> None:
    store = tmp_path / "store"
    accept_path = store / "mock_exchange_accept_v1.json"
    child = spawn_hard_crash_child_v1(
        store_root=store,
        crash_point=CrashPointV1.C9,
        extra={"mock_accept_evidence_path": str(accept_path)},
    )
    assert child.timed_out is False
    assert child.exit_code == expected_crash_exit_v1(CrashPointV1.C9)
    assert accept_path.is_file()
    restart = evaluate_restart_after_crash_v1(store_root=store, crash_point=CrashPointV1.C9)
    assert restart.durable_consumed is True
    assert restart.durable_state == "SENT_INITIATED"
    assert restart.second_admission_blocked is True
    assert "NO_NEW_ENTRY_WHILE" in restart.second_admission_reason
    assert restart.mock_post_attempts_after_restart == 0


def test_c10_crash_before_submit_boundary_mark(tmp_path: Path) -> None:
    _, restart = _run_crash_and_evaluate(tmp_path, CrashPointV1.C10)
    assert restart.durable_consumed is True
    assert restart.durable_state == "SENT_INITIATED"
    assert restart.second_admission_blocked is True
    assert restart.mock_post_attempts_after_restart == 0


def test_c11_crash_during_reconciliation_does_not_enable_replay(tmp_path: Path) -> None:
    _, restart = _run_crash_and_evaluate(tmp_path, CrashPointV1.C11)
    assert restart.durable_consumed is True
    assert restart.mock_post_attempts_after_restart == 0


def test_c12_crash_during_atomic_recovery_write_fail_closed(tmp_path: Path) -> None:
    _, restart = _run_crash_and_evaluate(tmp_path, CrashPointV1.C12)
    assert restart.durable_consumed is True
    assert restart.second_admission_blocked is True
    assert restart.mock_post_attempts_after_restart == 0


def test_c3_crash_after_seal_before_mint(tmp_path: Path) -> None:
    _, restart = _run_crash_and_evaluate(tmp_path, CrashPointV1.C3)
    assert restart.correlation_present is True
    assert restart.durable_consumed is False
    assert restart.mock_post_attempts_after_restart == 0


def test_c2_crash_after_reservation_before_correlation(tmp_path: Path) -> None:
    store = tmp_path / "store"
    _, restart = _run_crash_and_evaluate(store, CrashPointV1.C2)
    assert restart.correlation_present is False
    assert restart.guard_state == "RESERVED_PRE_POST"
    assert restart.mock_post_attempts_after_restart == 0


def test_c1_crash_before_atomic_reservation(tmp_path: Path) -> None:
    store = tmp_path / "store"
    _, restart = _run_crash_and_evaluate(store, CrashPointV1.C1)
    assert restart.correlation_present is False
    assert restart.guard_state is None
    assert restart.mock_post_attempts_after_restart == 0


def test_child_runner_is_test_only_entrypoint() -> None:
    runner = Path("tests/ops/_current_productive_post_hard_crash_child_runner_v1.py").read_text(
        encoding="utf-8"
    )
    assert "os._exit" in runner
    assert "eea.okx.com" not in runner
    assert not re.search(r"REAL_KEYCHAIN_ACCESS_AUTHORIZED\s*=\s*True", runner)


@pytest.mark.parametrize(
    "scenario,expected_recon,expect_external",
    [
        ("GET_TECHNICAL_ERROR", STILL_UNKNOWN, "false"),
        ("EMPTY_ORDER_RESPONSE", STILL_UNKNOWN, "false"),
        ("BUSINESS_NEGATIVE", CONFIRMED_REJECTED, "false"),
        ("ORDER_WITHOUT_POSITION", CONFIRMED_ACCEPTED_WORKING, "true"),
        ("CONTRADICTORY_EVIDENCE", STILL_UNKNOWN, "false"),
        ("POSITIVE_ORDER_EVIDENCE", CONFIRMED_ACCEPTED_WORKING, "true"),
    ],
)
def test_c11_adversarial_read_only_reconciliation_variants(
    tmp_path: Path,
    scenario: str,
    expected_recon: str,
    expect_external: str,
) -> None:
    store, env = bootstrap_unknown_post_store_v1(tmp_path)
    recon = run_adversarial_reconciliation_v1(
        scenario=scenario,
        client_order_id=str(env.client_order_id),
        instrument_id=PILOT_TEST_INST,
    )
    assert recon.reconciliation_result == expected_recon
    assert recon.external_effect_confirmed == expect_external
    reason = assert_second_new_risk_admission_blocked_v1(store_root=store)
    assert reason
    assert "NO_NEW_ENTRY_WHILE" in reason or "ADMISSION" in reason.upper()


def test_restart_reuses_same_envelope_identity(tmp_path: Path) -> None:
    env = _new_risk_envelope()
    store = tmp_path / "store"
    spawn_hard_crash_child_v1(store_root=store, crash_point=CrashPointV1.C6)
    restart = evaluate_restart_after_crash_v1(
        store_root=store,
        crash_point=CrashPointV1.C6,
        first_envelope=env,
    )
    assert restart.replay_attempt_executed is True
    assert restart.mock_post_attempts_after_restart == 0
    assert "REPLAY_ATTEMPT_EXECUTED" in restart.notes


def test_c9_restart_same_envelope_replay_blocked_before_mock_transport(tmp_path: Path) -> None:
    store = tmp_path / "store"
    env = _new_risk_envelope()
    spawn_hard_crash_child_v1(store_root=store, crash_point=CrashPointV1.C9)
    restart = evaluate_restart_after_crash_v1(
        store_root=store,
        crash_point=CrashPointV1.C9,
        first_envelope=env,
    )
    assert restart.durable_consumed is True
    assert restart.replay_attempt_executed is True
    assert restart.mock_post_attempts_after_restart == 0


def test_evaluate_restart_negative_control_rejects_stubbed_replay_probe(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    store = tmp_path / "store"
    spawn_hard_crash_child_v1(store_root=store, crash_point=CrashPointV1.C9)

    def _stub_replay(**_kwargs: Any) -> tuple[int, bool, str]:
        return (0, False, "STUB")

    monkeypatch.setattr(
        hard_crash_harness_v1,
        "_attempt_same_envelope_controlled_replay_v1",
        _stub_replay,
    )
    with pytest.raises(RestartEvaluationReplayProbeError, match="NOT_EXECUTED"):
        evaluate_restart_after_crash_v1(store_root=store, crash_point=CrashPointV1.C9)


def test_evaluate_restart_negative_control_rejects_fabricated_mock_post_count(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    store = tmp_path / "store"
    spawn_hard_crash_child_v1(store_root=store, crash_point=CrashPointV1.C9)

    def _stub_replay(**_kwargs: Any) -> tuple[int, bool, str]:
        return (1, True, "STUB")

    monkeypatch.setattr(
        hard_crash_harness_v1,
        "_attempt_same_envelope_controlled_replay_v1",
        _stub_replay,
    )
    with pytest.raises(RestartEvaluationReplayProbeError, match="UNEXPECTED_MOCK_POST"):
        evaluate_restart_after_crash_v1(store_root=store, crash_point=CrashPointV1.C9)
