"""Isolated CURRENT permit/send-seam replay proof (offline, no Owner-GO execute path)."""

from __future__ import annotations

import socket
from pathlib import Path
from typing import Any

import pytest

import tests.ops._current_productive_post_hard_crash_harness_v1 as hard_crash_harness_v1
from src.ops.full_core_live_path_composition_root_v1.current_productive_mandatory_new_risk_enter_post_admission_v1 import (
    load_enter_post_lifecycle_correlation_v1,
)
from src.ops.full_core_live_path_composition_root_v1.external_effect_permit_durable_consume_v1 import (
    DURABLE_STATE_SENT_INITIATED,
    load_external_effect_durable_consume_v1,
)
from tests.ops._current_productive_post_hard_crash_harness_v1 import (
    CrashPointV1,
    RestartEvaluationReplayProbeError,
    assert_permit_send_seam_replay_proof_v1,
    attempt_permit_send_seam_same_envelope_replay_v1,
    evaluate_restart_after_crash_v1,
    spawn_hard_crash_child_v1,
)
from tests.ops.test_current_productive_one_shot_fresh_envelope_permit_mint_durable_consume_and_post_join_v1 import (
    _new_risk_envelope,
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


def test_c9_crash_store_seam_rejects_consumed_permit_without_mock_post(
    tmp_path: Path,
) -> None:
    store = tmp_path / "store"
    envelope = _new_risk_envelope()
    spawn_hard_crash_child_v1(store_root=store, crash_point=CrashPointV1.C9)
    correlation = load_enter_post_lifecycle_correlation_v1(store_root=store)
    assert correlation is not None
    assert str(correlation.get("clordid") or "") == str(envelope.client_order_id)

    durable = load_external_effect_durable_consume_v1(store_root=store)
    assert durable.get("durable_consumed") is True
    record = durable.get("record") if isinstance(durable.get("record"), dict) else {}
    assert str(record.get("durable_state") or "") == DURABLE_STATE_SENT_INITIATED

    seam = attempt_permit_send_seam_same_envelope_replay_v1(
        store_root=store,
        envelope=envelope,
    )
    assert seam.owner_go_gate_reached is False
    assert seam.rejection_reason == "CONSUMED_PERMIT"
    assert seam.mock_post_attempts == 0
    assert_permit_send_seam_replay_proof_v1(seam)


def test_evaluate_restart_uses_permit_send_seam_channel_after_consumed_crash(
    tmp_path: Path,
) -> None:
    store = tmp_path / "store"
    envelope = _new_risk_envelope()
    spawn_hard_crash_child_v1(store_root=store, crash_point=CrashPointV1.C9)
    restart = evaluate_restart_after_crash_v1(
        store_root=store,
        crash_point=CrashPointV1.C9,
        first_envelope=envelope,
    )
    assert restart.replay_attempt_executed is True
    assert restart.mock_post_attempts_after_restart == 0
    assert any(n.startswith("REPLAY_CHANNEL=PERMIT_SEND_SEAM:") for n in restart.notes)


def test_negative_control_assert_proof_fails_on_fabricated_zero_count() -> None:
    fake = hard_crash_harness_v1.PermitSendSeamReplayProbeResultV1(
        mock_post_attempts=0,
        rejection_reason="UNEXPECTED_SUCCESS",
        owner_go_gate_reached=False,
        durable_permit_id="p1",
        durable_envelope_id="e1",
    )
    with pytest.raises(RestartEvaluationReplayProbeError, match="SEAM_REPLAY_REJECTION_UNEXPECTED"):
        assert_permit_send_seam_replay_proof_v1(fake)


def test_negative_control_assert_proof_fails_when_mock_post_count_nonzero() -> None:
    fake = hard_crash_harness_v1.PermitSendSeamReplayProbeResultV1(
        mock_post_attempts=1,
        rejection_reason="CONSUMED_PERMIT",
        owner_go_gate_reached=False,
        durable_permit_id="p1",
        durable_envelope_id="e1",
    )
    with pytest.raises(RestartEvaluationReplayProbeError, match="SEAM_REPLAY_MOCK_POST_NONZERO"):
        assert_permit_send_seam_replay_proof_v1(fake)
