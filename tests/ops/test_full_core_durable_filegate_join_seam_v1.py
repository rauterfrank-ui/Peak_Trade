"""Durable FILEGATE join seam for Full-Core admission. Offline. No venue GET."""

from __future__ import annotations

import json
from datetime import datetime, timedelta
from pathlib import Path

import pytest

from src.ops.full_core_live_path_composition_root_v1.constants_v1 import (
    DURABLE_FILEGATE_RUNTIME_JOIN_IMPLEMENTED,
    LIVE_ARMED,
    LIVE_ENABLED,
    WIRE_SEND_PERMITTED,
)
from src.ops.full_core_live_path_composition_root_v1.durable_filegate_join_v1 import (
    JOIN_SEAM_ID,
    join_durable_filegate_into_admission_inputs_v1,
    read_durable_filegate_join_evidence_v1,
)
from src.ops.full_core_live_path_composition_root_v1.execution_admission_contract_v1 import (
    ADMISSION_CONTEXT_OFFLINE_FULL_CORE_PROOF,
    CAPITAL_RISK_MODE_OFFLINE_ALGEBRA,
    DurableKillSwitchEvidenceStatusV1,
    OwnerOneShotPermitStatusV1,
    PRETRADE_SOURCE_FROZEN_OFFLINE,
    PretradeFreshnessStatusV1,
    evaluate_execution_admission_v1,
)
from src.ops.full_core_live_path_composition_root_v1.live_admission_gap_dag_v1 import (
    EARLIEST_UNRESOLVED_FULL_CORE_DEPENDENCY,
    gap_node_v1,
)
from src.risk_layer.kill_switch.persistence import StatePersistence
from src.risk_layer.kill_switch.state import KillSwitchState
from tests.ops.test_full_core_execution_admission_contract_v1 import _live_inputs
from tests.ops.test_full_core_live_path_composition_root_v1 import _run
from tests.trading.master_v2.test_master_v2_integrated_replay_safety_before_intent_restore_contract_v1 import (
    _confirmed_replay_input,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
RUNBOOK = REPO_ROOT / "docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md"
SPEC_PATH = REPO_ROOT / "docs/ops/specs/FULL_CORE_DURABLE_FILEGATE_JOIN_SEAM_V1.md"


def _bind_state_path(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    path = tmp_path / "kill_switch_state.json"
    monkeypatch.setenv("PEAK_KILL_SWITCH_STATE_PATH", str(path))
    monkeypatch.delenv("PEAKTRADE_KILL_SWITCH_STATE_PATH", raising=False)
    monkeypatch.delenv("PEAK_KILL_SWITCH", raising=False)
    return path


def _join_inputs(**overrides):
    payload = {
        "plan_identity": "plan-1",
        "venue_plan_identity": "venue-1",
        "instrument_identity_ok": True,
        "pretrade_admissible": True,
        "pretrade_source_kind": PRETRADE_SOURCE_FROZEN_OFFLINE,
        "pretrade_freshness_status": PretradeFreshnessStatusV1.FROZEN_OFFLINE.value,
        "capital_risk_mode": CAPITAL_RISK_MODE_OFFLINE_ALGEBRA,
        "owner_authorization_present": True,
        "owner_one_shot_permit_status": OwnerOneShotPermitStatusV1.TRUSTED_PRESENT.value,
        "admission_context": ADMISSION_CONTEXT_OFFLINE_FULL_CORE_PROOF,
        "provenance_refs": (),
    }
    payload.update(overrides)
    return join_durable_filegate_into_admission_inputs_v1(**payload)


def test_join_flag_and_standing_gates_remain_false() -> None:
    assert DURABLE_FILEGATE_RUNTIME_JOIN_IMPLEMENTED is True
    assert LIVE_ENABLED is False
    assert LIVE_ARMED is False
    assert WIRE_SEND_PERMITTED is False
    assert EARLIEST_UNRESOLVED_FULL_CORE_DEPENDENCY == ("FRESH_PRETRADE_RUNTIME_GET_IMPLEMENTED")
    node = gap_node_v1("DURABLE_FILEGATE_RUNTIME_JOIN")
    assert node.implementation_status == "JOINED_TYPED_EVIDENCE_FAIL_CLOSED"
    assert node.wiring_authorized is True
    assert node.standing_live_gates_would_change is False


def test_valid_active_filegate_is_trusted_but_does_not_admit(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    path = _bind_state_path(tmp_path, monkeypatch)
    StatePersistence(str(path)).save(KillSwitchState.ACTIVE)
    evidence = read_durable_filegate_join_evidence_v1()
    assert evidence.evidence_status == DurableKillSwitchEvidenceStatusV1.TRUSTED_PRESENT.value
    assert evidence.blocked is False
    assert evidence.state_name == "ACTIVE"
    assert evidence.env_overlay_used_as_durable_evidence is False
    inputs = _join_inputs()
    assert inputs.durable_kill_switch_evidence_status == (
        DurableKillSwitchEvidenceStatusV1.TRUSTED_PRESENT.value
    )
    assert inputs.durable_kill_switch_blocked is False
    assert inputs.live_enabled is False
    assert inputs.live_armed is False
    assert inputs.wire_send_permitted is False
    decision = evaluate_execution_admission_v1(inputs)
    assert decision.admitted is False
    assert "DURABLE_FILEGATE_EVIDENCE_MISSING" not in decision.reason_codes
    assert "LIVE_ENABLED_FALSE" in decision.reason_codes
    assert "WIRE_SEND_NOT_PERMITTED" in decision.reason_codes


def test_valid_killed_filegate_is_trusted_and_blocks(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    path = _bind_state_path(tmp_path, monkeypatch)
    StatePersistence(str(path)).save(
        KillSwitchState.KILLED, killed_at=datetime.utcnow(), trigger_reason="join-test"
    )
    evidence = read_durable_filegate_join_evidence_v1()
    assert evidence.evidence_status == DurableKillSwitchEvidenceStatusV1.TRUSTED_PRESENT.value
    assert evidence.blocked is True
    decision = evaluate_execution_admission_v1(_join_inputs())
    assert decision.admitted is False
    assert "DURABLE_FILEGATE_BLOCKS_TRADING" in decision.reason_codes
    assert "DURABLE_KILL_SWITCH_BLOCKED_OR_UNTRUSTED" in decision.reason_codes


def test_missing_filegate_fail_closed(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    path = _bind_state_path(tmp_path, monkeypatch)
    assert path.exists() is False
    evidence = read_durable_filegate_join_evidence_v1()
    assert evidence.evidence_status == DurableKillSwitchEvidenceStatusV1.MISSING.value
    assert evidence.blocked is None
    decision = evaluate_execution_admission_v1(_join_inputs())
    assert decision.admitted is False
    assert "DURABLE_FILEGATE_EVIDENCE_MISSING" in decision.reason_codes


def test_malformed_filegate_fail_closed(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    path = _bind_state_path(tmp_path, monkeypatch)
    path.write_text("{not-json", encoding="utf-8")
    evidence = read_durable_filegate_join_evidence_v1()
    assert evidence.evidence_status == DurableKillSwitchEvidenceStatusV1.UNKNOWN_BLOCKED.value
    assert evidence.blocked is None
    decision = evaluate_execution_admission_v1(_join_inputs())
    assert decision.admitted is False
    assert "DURABLE_FILEGATE_UNKNOWN_BLOCKED" in decision.reason_codes


def test_invalid_enum_filegate_fail_closed(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    path = _bind_state_path(tmp_path, monkeypatch)
    path.write_text(json.dumps({"state": "NOPE"}), encoding="utf-8")
    evidence = read_durable_filegate_join_evidence_v1()
    assert evidence.evidence_status == DurableKillSwitchEvidenceStatusV1.UNKNOWN_BLOCKED.value
    decision = evaluate_execution_admission_v1(_join_inputs())
    assert decision.admitted is False
    assert "DURABLE_FILEGATE_UNKNOWN_BLOCKED" in decision.reason_codes


def test_contradictory_filegate_fail_closed(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    path = _bind_state_path(tmp_path, monkeypatch)
    path.write_text(
        json.dumps({"state": "ACTIVE", "status": "KILLED", "kill_switch": True}),
        encoding="utf-8",
    )
    evidence = read_durable_filegate_join_evidence_v1()
    assert evidence.evidence_status == DurableKillSwitchEvidenceStatusV1.CONTRADICTORY.value
    assert evidence.contradictory is True
    decision = evaluate_execution_admission_v1(_join_inputs())
    assert decision.admitted is False
    assert "DURABLE_FILEGATE_CONTRADICTORY" in decision.reason_codes


def test_peak_kill_switch_overlay_is_not_durable_evidence(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("PEAK_KILL_SWITCH_STATE_PATH", raising=False)
    monkeypatch.delenv("PEAKTRADE_KILL_SWITCH_STATE_PATH", raising=False)
    monkeypatch.setenv("PEAK_KILL_SWITCH", "1")
    evidence = read_durable_filegate_join_evidence_v1(state_path=str(tmp_path / "absent.json"))
    assert evidence.evidence_status == DurableKillSwitchEvidenceStatusV1.MISSING.value
    assert evidence.env_overlay_used_as_durable_evidence is False
    inputs = _join_inputs(state_path=str(tmp_path / "absent.json"))
    decision = evaluate_execution_admission_v1(inputs)
    assert decision.admitted is False
    assert "DURABLE_FILEGATE_EVIDENCE_MISSING" in decision.reason_codes
    assert inputs.durable_kill_switch_blocked is None


def test_saved_at_age_is_not_a_filegate_freshness_contract(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    path = _bind_state_path(tmp_path, monkeypatch)
    old = (datetime.utcnow() - timedelta(days=400)).isoformat()
    path.write_text(
        json.dumps({"state": "ACTIVE", "saved_at": old, "version": "1.0"}),
        encoding="utf-8",
    )
    evidence = read_durable_filegate_join_evidence_v1()
    assert evidence.evidence_status == DurableKillSwitchEvidenceStatusV1.TRUSTED_PRESENT.value
    assert evidence.blocked is False


def test_join_does_not_change_hardcoded_untrusted_injector() -> None:
    inputs = _live_inputs()
    assert inputs.durable_kill_switch_evidence_status == (
        DurableKillSwitchEvidenceStatusV1.UNKNOWN_BLOCKED.value
    )
    decision = evaluate_execution_admission_v1(inputs)
    assert decision.admitted is False


def test_full_core_path_join_trusted_active_still_halts_before_wire(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    path = _bind_state_path(tmp_path, monkeypatch)
    StatePersistence(str(path)).save(KillSwitchState.ACTIVE)
    result, _ = _run(monkeypatch, _confirmed_replay_input(side="LONG"))
    assert result.boundary is not None
    assert result.boundary.halt_before_wire is True
    assert result.boundary.admission is not None
    assert result.boundary.admission.admitted is False
    assert result.wire_send_occurred is False
    assert "HARD_STOP_BEFORE_WIRE" in result.reason_codes
    assert "LIVE_ENABLED_FALSE" in result.reason_codes
    assert "DURABLE_FILEGATE_EVIDENCE_MISSING" not in result.reason_codes
    assert JOIN_SEAM_ID
    assert result.boundary.live_execution_port_constructed is False


def test_runbook_and_spec_bind_join_without_live_arming() -> None:
    runbook = RUNBOOK.read_text(encoding="utf-8")
    spec = SPEC_PATH.read_text(encoding="utf-8")
    start = runbook.index("11.2.1.J FULL_CORE_DURABLE_FILEGATE_JOIN_SEAM")
    section = runbook[
        start : runbook.index("11.2.1.K FULL_CORE_OWNER_ONE_SHOT_TYPED_PERMIT_SEAM", start)
    ]
    assert "DURABLE_FILEGATE_RUNTIME_JOIN_IMPLEMENTED=true" in section
    assert "LIVE_ENABLED=false" in section
    assert "LIVE_ARMED=false" in section
    assert "WIRE_SEND_PERMITTED=false" in section
    assert "GET_PERFORMED=false" in section
    assert "POST_PERFORMED=false" in section
    assert "FULL_CORE_SYSTEM_E2E_PROVEN=false" in section
    assert "CURRENT_LIVE_CORE_PATH_PROVEN=false" in section
    assert (
        "EARLIEST_UNRESOLVED_FULL_CORE_DEPENDENCY=OWNER_ONE_SHOT_TYPED_LIVE_EXECUTION_PERMIT"
        in section
    )
    assert "docs_token:" in spec
    assert "DOCS_TOKEN_FULL_CORE_DURABLE_FILEGATE_JOIN_SEAM_V1" in spec
    identity = runbook[
        runbook.index("11.2.1.I FULL_CORE_LIVE_PATH_IDENTITY_AND_ADMISSION_GAP") : start
    ]
    assert "DURABLE_FILEGATE_RUNTIME_JOIN_IMPLEMENTED=false" in identity
    assert "FUTURE_PRODUCTIVE_LIVE_EXECUTION_PATH=FULL_CORE_LIVE_PATH" in identity
