"""Typed OWNER_ONE_SHOT permit seam for Full-Core admission. Offline. No venue GET."""

from __future__ import annotations

from pathlib import Path

import pytest

from src.ops.full_core_live_path_composition_root_v1.constants_v1 import (
    LIVE_ARMED,
    LIVE_ENABLED,
    OWNER_ONE_SHOT_PERMIT_TOKEN,
    OWNER_ONE_SHOT_TYPED_LIVE_EXECUTION_PERMIT_IMPLEMENTED,
    WIRE_SEND_PERMITTED,
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
    FRESH_EXTERNAL_EVIDENCE_REQUIRED_FOR_NEXT_SLICE,
    gap_node_v1,
)
from src.ops.full_core_live_path_composition_root_v1.owner_one_shot_permit_v1 import (
    CONSUMPTION_SEMANTICS,
    JOIN_SEAM_ID,
    REPLAY_PROTECTION_PRESENT,
    REUSE_SEMANTICS,
    evaluate_owner_one_shot_permit_v1,
    join_owner_one_shot_permit_into_admission_inputs_v1,
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
SPEC_PATH = REPO_ROOT / "docs/ops/specs/FULL_CORE_OWNER_ONE_SHOT_TYPED_PERMIT_SEAM_V1.md"


def _bind_state_path(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    path = tmp_path / "kill_switch_state.json"
    monkeypatch.setenv("PEAK_KILL_SWITCH_STATE_PATH", str(path))
    monkeypatch.delenv("PEAKTRADE_KILL_SWITCH_STATE_PATH", raising=False)
    monkeypatch.delenv("PEAK_KILL_SWITCH", raising=False)
    return path


def _join_inputs(*, owner_go, state_path=None):
    return join_owner_one_shot_permit_into_admission_inputs_v1(
        plan_identity="plan-1",
        venue_plan_identity="venue-1",
        instrument_identity_ok=True,
        pretrade_admissible=True,
        pretrade_source_kind=PRETRADE_SOURCE_FROZEN_OFFLINE,
        pretrade_freshness_status=PretradeFreshnessStatusV1.FROZEN_OFFLINE.value,
        capital_risk_mode=CAPITAL_RISK_MODE_OFFLINE_ALGEBRA,
        owner_go=owner_go,
        admission_context=ADMISSION_CONTEXT_OFFLINE_FULL_CORE_PROOF,
        provenance_refs=(),
        state_path=state_path,
    )


def test_permit_flag_and_standing_gates_remain_false() -> None:
    assert OWNER_ONE_SHOT_TYPED_LIVE_EXECUTION_PERMIT_IMPLEMENTED is True
    assert LIVE_ENABLED is False
    assert LIVE_ARMED is False
    assert WIRE_SEND_PERMITTED is False
    assert EARLIEST_UNRESOLVED_FULL_CORE_DEPENDENCY == ("LIVE_ACCOUNT_BOUND_IMPLEMENTED")
    assert FRESH_EXTERNAL_EVIDENCE_REQUIRED_FOR_NEXT_SLICE is True
    node = gap_node_v1("OWNER_ONE_SHOT_EXECUTION_PERMIT")
    assert node.implementation_status == "JOINED_TYPED_EVIDENCE_FAIL_CLOSED"
    assert node.wiring_authorized is True
    assert node.standing_live_gates_would_change is False
    assert CONSUMPTION_SEMANTICS == "NOT_IN_EXISTING_FULL_CORE_CONTRACT"
    assert REUSE_SEMANTICS == "NOT_IN_EXISTING_FULL_CORE_CONTRACT"
    assert REPLAY_PROTECTION_PRESENT is False


def test_valid_owner_one_shot_emits_typed_permit_and_does_not_admit() -> None:
    evidence = evaluate_owner_one_shot_permit_v1(owner_go=OWNER_ONE_SHOT_PERMIT_TOKEN)
    assert evidence.evidence_status == OwnerOneShotPermitStatusV1.TRUSTED_PRESENT.value
    presented = evidence.presented_token
    assert presented == OWNER_ONE_SHOT_PERMIT_TOKEN
    assert evidence.consumed is False
    assert evidence.live_enabled is False
    assert evidence.live_armed is False
    assert evidence.wire_send_permitted is False
    inputs = _join_inputs(owner_go=OWNER_ONE_SHOT_PERMIT_TOKEN)
    assert inputs.owner_one_shot_permit_status == (OwnerOneShotPermitStatusV1.TRUSTED_PRESENT.value)
    assert inputs.owner_authorization_present is True
    assert inputs.live_enabled is False
    assert inputs.live_armed is False
    assert inputs.wire_send_permitted is False
    decision = evaluate_execution_admission_v1(inputs)
    assert decision.admitted is False
    assert "MISSING_OWNER_AUTHORIZATION" not in decision.reason_codes
    assert "OWNER_ONE_SHOT_PERMIT_MISSING" not in decision.reason_codes
    assert "LIVE_ENABLED_FALSE" in decision.reason_codes
    assert "WIRE_SEND_NOT_PERMITTED" in decision.reason_codes


def test_missing_permit_fail_closed() -> None:
    for presented in (None, ""):
        evidence = evaluate_owner_one_shot_permit_v1(owner_go=presented)
        assert evidence.evidence_status == OwnerOneShotPermitStatusV1.MISSING.value
        inputs = _join_inputs(owner_go=presented)
        decision = evaluate_execution_admission_v1(inputs)
        assert decision.admitted is False
        assert "OWNER_ONE_SHOT_PERMIT_MISSING" in decision.reason_codes
        assert "MISSING_OWNER_AUTHORIZATION" in decision.reason_codes
        assert inputs.live_enabled is False
        assert inputs.wire_send_permitted is False


def test_malformed_permit_fail_closed() -> None:
    for presented in (True, 1, b"OWNER_GO_FULL_CORE_LIVE_PATH_OFFLINE_V1", "  TOKEN  "):
        evidence = evaluate_owner_one_shot_permit_v1(owner_go=presented)
        assert evidence.evidence_status == OwnerOneShotPermitStatusV1.MALFORMED.value
        inputs = _join_inputs(owner_go=presented)
        decision = evaluate_execution_admission_v1(inputs)
        assert decision.admitted is False
        assert "OWNER_ONE_SHOT_PERMIT_MALFORMED" in decision.reason_codes
        assert inputs.owner_authorization_present is False


def test_whitespace_around_valid_token_is_malformed_not_normalized() -> None:
    padded = f" {OWNER_ONE_SHOT_PERMIT_TOKEN} "
    evidence = evaluate_owner_one_shot_permit_v1(owner_go=padded)
    assert evidence.evidence_status == OwnerOneShotPermitStatusV1.MALFORMED.value
    assert evidence.presented_token == padded


def test_case_variant_is_mismatch_not_normalized() -> None:
    lowered = OWNER_ONE_SHOT_PERMIT_TOKEN.lower()
    evidence = evaluate_owner_one_shot_permit_v1(owner_go=lowered)
    assert evidence.evidence_status == OwnerOneShotPermitStatusV1.MISMATCH.value
    assert evidence.presented_token == lowered


def test_wrong_token_mismatch_fail_closed() -> None:
    evidence = evaluate_owner_one_shot_permit_v1(owner_go="OWNER_GO_LIVE_CANARY_MINIMUM_EXPOSURE")
    assert evidence.evidence_status == OwnerOneShotPermitStatusV1.MISMATCH.value
    inputs = _join_inputs(owner_go="OWNER_GO_LIVE_CANARY_MINIMUM_EXPOSURE")
    decision = evaluate_execution_admission_v1(inputs)
    assert decision.admitted is False
    assert "OWNER_ONE_SHOT_PERMIT_MISMATCH" in decision.reason_codes
    assert "MISSING_OWNER_AUTHORIZATION" in decision.reason_codes


def test_contradictory_bool_and_status_fail_closed() -> None:
    decision = evaluate_execution_admission_v1(
        _live_inputs(
            owner_authorization_present=True,
            owner_one_shot_permit_status=OwnerOneShotPermitStatusV1.MISSING.value,
        )
    )
    assert decision.admitted is False
    assert "OWNER_ONE_SHOT_PERMIT_CONTRADICTORY" in decision.reason_codes
    inverted = evaluate_execution_admission_v1(
        _live_inputs(
            owner_authorization_present=False,
            owner_one_shot_permit_status=OwnerOneShotPermitStatusV1.TRUSTED_PRESENT.value,
        )
    )
    assert inverted.admitted is False
    assert "OWNER_ONE_SHOT_PERMIT_CONTRADICTORY" in inverted.reason_codes


def test_valid_permit_does_not_set_live_enabled_or_armed() -> None:
    evidence = evaluate_owner_one_shot_permit_v1(owner_go=OWNER_ONE_SHOT_PERMIT_TOKEN)
    inputs = _join_inputs(owner_go=OWNER_ONE_SHOT_PERMIT_TOKEN)
    assert evidence.live_enabled is False
    assert evidence.live_armed is False
    assert inputs.live_enabled is False
    assert inputs.live_armed is False
    assert LIVE_ENABLED is False
    assert LIVE_ARMED is False


def test_permit_cannot_override_filegate_block(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _path = _bind_state_path(tmp_path, monkeypatch)
    StatePersistence(str(_path)).save(KillSwitchState.KILLED)
    inputs = _join_inputs(owner_go=OWNER_ONE_SHOT_PERMIT_TOKEN)
    assert inputs.owner_one_shot_permit_status == (OwnerOneShotPermitStatusV1.TRUSTED_PRESENT.value)
    assert inputs.durable_kill_switch_blocked is True
    decision = evaluate_execution_admission_v1(inputs)
    assert decision.admitted is False
    assert "DURABLE_FILEGATE_BLOCKS_TRADING" in decision.reason_codes


def test_trusted_filegate_plus_valid_permit_still_cannot_wire_send(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    path = _bind_state_path(tmp_path, monkeypatch)
    StatePersistence(str(path)).save(KillSwitchState.ACTIVE)
    inputs = _join_inputs(owner_go=OWNER_ONE_SHOT_PERMIT_TOKEN)
    assert inputs.durable_kill_switch_evidence_status == (
        DurableKillSwitchEvidenceStatusV1.TRUSTED_PRESENT.value
    )
    assert inputs.durable_kill_switch_blocked is False
    assert inputs.owner_authorization_present is True
    decision = evaluate_execution_admission_v1(inputs)
    assert decision.admitted is False
    assert "WIRE_SEND_NOT_PERMITTED" in decision.reason_codes
    assert "LIVE_ENABLED_FALSE" in decision.reason_codes
    assert "LIVE_ARMED_FALSE" in decision.reason_codes
    assert inputs.wire_send_permitted is False
    assert WIRE_SEND_PERMITTED is False


def test_full_core_path_valid_permit_still_halts_before_wire(
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
    assert "MISSING_OWNER_AUTHORIZATION" not in result.reason_codes
    assert "OWNER_ONE_SHOT_PERMIT_MISSING" not in result.reason_codes
    assert "LIVE_ENABLED_FALSE" in result.reason_codes
    assert JOIN_SEAM_ID
    assert result.boundary.live_execution_port_constructed is False


def test_runbook_and_spec_bind_permit_without_live_arming() -> None:
    runbook = RUNBOOK.read_text(encoding="utf-8")
    spec = SPEC_PATH.read_text(encoding="utf-8")
    start = runbook.index("11.2.1.K FULL_CORE_OWNER_ONE_SHOT_TYPED_PERMIT_SEAM")
    section = runbook[start : runbook.index("## 11.3 Autonomy state model", start)]
    assert "OWNER_ONE_SHOT_TYPED_LIVE_EXECUTION_PERMIT_IMPLEMENTED=true" in section
    assert "LIVE_ENABLED=false" in section
    assert "LIVE_ARMED=false" in section
    assert "WIRE_SEND_PERMITTED=false" in section
    assert "GET_PERFORMED=false" in section
    assert "POST_PERFORMED=false" in section
    assert "FULL_CORE_SYSTEM_E2E_PROVEN=false" in section
    assert "CURRENT_LIVE_CORE_PATH_PROVEN=false" in section
    assert "VALID_PERMIT_ALONE_CAN_ADMIT=false" in section
    assert "FILEGATE_CAN_BE_OVERRIDDEN_BY_PERMIT=false" in section
    assert (
        "EARLIEST_UNRESOLVED_FULL_CORE_DEPENDENCY=FRESH_PRETRADE_RUNTIME_GET_IMPLEMENTED" in section
    )
    assert "docs_token:" in spec
    assert "DOCS_TOKEN_FULL_CORE_OWNER_ONE_SHOT_TYPED_PERMIT_SEAM_V1" in spec
    prior = runbook[runbook.index("11.2.1.J FULL_CORE_DURABLE_FILEGATE_JOIN_SEAM") : start]
    assert "DURABLE_FILEGATE_RUNTIME_JOIN_IMPLEMENTED=true" in prior
    assert (
        "EARLIEST_UNRESOLVED_FULL_CORE_DEPENDENCY=OWNER_ONE_SHOT_TYPED_LIVE_EXECUTION_PERMIT"
        in prior
    )
