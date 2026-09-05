"""LIVE_ACCOUNT_BOUND seam and remaining Full-Core admission closeout.

Injected GET doubles only. No productive venue GET. No POST. No arming.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from src.ops.full_core_live_path_composition_root_v1.constants_v1 import (
    FULL_CORE_OFFLINE_E2E_EVIDENCE_CLASS,
    FULL_CORE_OFFLINE_E2E_PROVEN,
    FULL_CORE_SYSTEM_E2E_PROVEN,
    LIVE_ACCOUNT_BOUND_IMPLEMENTED,
    LIVE_ARMED,
    LIVE_ENABLED,
    OWNER_ONE_SHOT_PERMIT_TOKEN,
    WIRE_SEND_PERMITTED,
)
from src.ops.full_core_live_path_composition_root_v1.execution_admission_contract_v1 import (
    ADMISSION_CONTEXT_LIVE,
    CAPITAL_RISK_MODE_LIVE_ACCOUNT_BOUND,
    CAPITAL_RISK_MODE_OFFLINE_ALGEBRA,
    DurableKillSwitchEvidenceStatusV1,
    FreshPretradeGetStatusV1,
    LiveAccountBoundStatusV1,
    OwnerOneShotPermitStatusV1,
    PRETRADE_SOURCE_FRESH_GET,
    PretradeFreshnessStatusV1,
    evaluate_execution_admission_v1,
)
from src.ops.full_core_live_path_composition_root_v1.fresh_pretrade_runtime_get_v1 import (
    ENDPOINT_ACCOUNT_BALANCE,
    ENDPOINT_ACCOUNT_CONFIG,
    ENDPOINT_ACCOUNT_LEVERAGE_INFO,
    ENDPOINT_ACCOUNT_MAX_SIZE,
    ENDPOINT_ACCOUNT_POSITIONS,
    ENDPOINT_PUBLIC_INSTRUMENTS,
    ENDPOINT_PUBLIC_PRICE_LIMIT,
    TRANSPORT_CLASS_INJECTED_TEST_DOUBLE,
    collect_fresh_pretrade_runtime_get_v1,
)
from src.ops.full_core_live_path_composition_root_v1.live_account_bound_v1 import (
    JOIN_SEAM_ID,
    evaluate_live_account_bound_v1,
    join_live_account_bound_into_admission_inputs_v1,
)
from src.ops.full_core_live_path_composition_root_v1.live_admission_gap_dag_v1 import (
    EARLIEST_UNRESOLVED_FULL_CORE_DEPENDENCY,
    FRESH_EXTERNAL_EVIDENCE_REQUIRED_FOR_NEXT_SLICE,
    gap_node_v1,
)
from src.risk_layer.kill_switch.persistence import StatePersistence
from src.risk_layer.kill_switch.state import KillSwitchState
from tests.ops.test_full_core_execution_admission_contract_v1 import _live_inputs
from tests.ops.test_full_core_fresh_pretrade_runtime_get_seam_v1 import (
    InjectedFreshGetTransportV1,
)
from tests.ops.test_full_core_live_path_composition_root_v1 import _run
from tests.trading.master_v2.test_integrated_offline_trading_logic_replay_v1 import (
    _INSTRUMENT,
)
from tests.trading.master_v2.test_master_v2_integrated_replay_safety_before_intent_restore_contract_v1 import (
    _confirmed_replay_input,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
RUNBOOK = REPO_ROOT / "docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md"
SPEC_PATH = REPO_ROOT / "docs/ops/specs/FULL_CORE_REMAINING_ADMISSION_CHAIN_CLOSEOUT_V1.md"

_TEST_UID = "full-core-test-account-uid-1"
_TEST_INST = "SUI-USD_UM_XPERP-310404"
_TEST_TD = "cross"


def _identity_payloads(
    *,
    instrument_id: str = _TEST_INST,
    uid: str = _TEST_UID,
    td_mode: str = _TEST_TD,
    extra_uid: str | None = None,
):
    inst_row = {"instId": instrument_id, "tdMode": td_mode, "mgnMode": td_mode}
    config_rows = [{"uid": uid}]
    if extra_uid is not None:
        config_rows.append({"uid": extra_uid})
    return {
        ENDPOINT_PUBLIC_INSTRUMENTS: {"code": "0", "data": [dict(inst_row)]},
        ENDPOINT_PUBLIC_PRICE_LIMIT: {"code": "0", "data": [{"instId": instrument_id}]},
        ENDPOINT_ACCOUNT_MAX_SIZE: {"code": "0", "data": [dict(inst_row)]},
        ENDPOINT_ACCOUNT_LEVERAGE_INFO: {"code": "0", "data": [dict(inst_row)]},
        ENDPOINT_ACCOUNT_CONFIG: {"code": "0", "data": config_rows},
        ENDPOINT_ACCOUNT_POSITIONS: {"code": "0", "data": [{"mgnMode": td_mode}]},
        ENDPOINT_ACCOUNT_BALANCE: {"code": "0", "data": [{"ccy": "USDC"}]},
    }


def _bound_transport(**overrides):
    payloads = overrides.pop("payloads", None)
    if payloads is None:
        payloads = _identity_payloads()
    return InjectedFreshGetTransportV1(payloads=payloads, **overrides)


def _collect_get(*, instrument_id=_TEST_INST, td_mode=_TEST_TD, **overrides):
    payload = {
        "pretrade_decision_id": "decision-1",
        "instrument_id": instrument_id,
        "td_mode": td_mode,
        "limit_px": "1.23",
        "transport": _bound_transport(),
        "require_collection": True,
    }
    payload.update(overrides)
    return collect_fresh_pretrade_runtime_get_v1(**payload)


def _evaluate_bound(*, get_evidence=None, **overrides):
    evidence = get_evidence if get_evidence is not None else _collect_get()
    payload = {
        "get_evidence": evidence,
        "expected_account_identity": _TEST_UID,
        "expected_instrument_id": _TEST_INST,
        "expected_td_mode": _TEST_TD,
    }
    payload.update(overrides)
    return evaluate_live_account_bound_v1(**payload)


_DEFAULT_TRANSPORT = object()


def _join_live(*, transport=_DEFAULT_TRANSPORT, expected_account_identity=_TEST_UID, **kwargs):
    payload = {
        "plan_identity": "plan-1",
        "venue_plan_identity": "venue-1",
        "instrument_identity_ok": True,
        "pretrade_admissible": True,
        "pretrade_source_kind": PRETRADE_SOURCE_FRESH_GET,
        "pretrade_freshness_status": PretradeFreshnessStatusV1.LIVE_FRESH.value,
        "capital_risk_mode": CAPITAL_RISK_MODE_OFFLINE_ALGEBRA,
        "owner_go": OWNER_ONE_SHOT_PERMIT_TOKEN,
        "admission_context": ADMISSION_CONTEXT_LIVE,
        "provenance_refs": (),
        "transport": _bound_transport() if transport is _DEFAULT_TRANSPORT else transport,
        "pretrade_decision_id": "decision-1",
        "instrument_id": _TEST_INST,
        "td_mode": _TEST_TD,
        "limit_px": "1.23",
        "expected_account_identity": expected_account_identity,
    }
    payload.update(kwargs)
    return join_live_account_bound_into_admission_inputs_v1(**payload)


def _bind_state_path(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    path = tmp_path / "kill_switch_state.json"
    monkeypatch.setenv("PEAK_KILL_SWITCH_STATE_PATH", str(path))
    monkeypatch.delenv("PEAKTRADE_KILL_SWITCH_STATE_PATH", raising=False)
    monkeypatch.delenv("PEAK_KILL_SWITCH", raising=False)
    return path


def test_flags_and_standing_gates_remain_false() -> None:
    assert LIVE_ACCOUNT_BOUND_IMPLEMENTED is True
    assert LIVE_ENABLED is False
    assert LIVE_ARMED is False
    assert WIRE_SEND_PERMITTED is False
    assert FULL_CORE_OFFLINE_E2E_PROVEN is True
    assert FULL_CORE_SYSTEM_E2E_PROVEN is False
    assert FULL_CORE_OFFLINE_E2E_EVIDENCE_CLASS == "INJECTED_NON_PRODUCTIVE"
    assert EARLIEST_UNRESOLVED_FULL_CORE_DEPENDENCY == ("STEP_29P_EQUITY_DIMENSION_BINDING_MISSING")
    assert FRESH_EXTERNAL_EVIDENCE_REQUIRED_FOR_NEXT_SLICE is False
    node = gap_node_v1("LIVE_ACCOUNT_BOUND")
    assert node.implementation_status == "JOINED_TYPED_EVIDENCE_FAIL_CLOSED"
    assert node.wiring_authorized is True
    assert node.standing_live_gates_would_change is False
    live_enabled = gap_node_v1("LIVE_ENABLED")
    assert live_enabled.implementation_status == (
        "STANDING_ADMISSION_SEAM_IMPLEMENTED_DEFAULT_FALSE"
    )
    assert live_enabled.standing_live_gates_would_change is False


def test_complete_binding_evidence_component_pass() -> None:
    evidence = _evaluate_bound()
    assert evidence.evidence_status == LiveAccountBoundStatusV1.TRUSTED_PRESENT.value
    assert evidence.capital_risk_mode == CAPITAL_RISK_MODE_LIVE_ACCOUNT_BOUND
    assert evidence.observed_account_identity == _TEST_UID
    assert evidence.live_enabled is False
    assert evidence.wire_send_permitted is False
    assert "LIVE_ACCOUNT_BOUND_TRUSTED_PRESENT" in evidence.reason_codes


def test_missing_expected_identity_deny() -> None:
    evidence = _evaluate_bound(expected_account_identity="")
    assert evidence.evidence_status == LiveAccountBoundStatusV1.MISSING.value
    assert "LIVE_ACCOUNT_BOUND_EXPECTED_IDENTITY_MISSING" in evidence.reason_codes
    assert "FRESH_GET_ALONE_NOT_ACCOUNT_BOUND" in evidence.reason_codes


def test_fresh_get_success_alone_does_not_prove_bound() -> None:
    get_evidence = _collect_get(transport=InjectedFreshGetTransportV1())
    assert get_evidence.evidence_status == FreshPretradeGetStatusV1.TRUSTED_PRESENT.value
    evidence = _evaluate_bound(get_evidence=get_evidence)
    assert evidence.evidence_status == LiveAccountBoundStatusV1.MISSING.value
    assert "LIVE_ACCOUNT_BOUND_ACCOUNT_UID_MISSING" in evidence.reason_codes
    assert evidence.capital_risk_mode == CAPITAL_RISK_MODE_OFFLINE_ALGEBRA


def test_malformed_uid_deny() -> None:
    payloads = _identity_payloads()
    payloads[ENDPOINT_ACCOUNT_CONFIG] = {"code": "0", "data": [{"uid": 123}]}
    evidence = _evaluate_bound(
        get_evidence=_collect_get(transport=_bound_transport(payloads=payloads))
    )
    assert evidence.evidence_status == LiveAccountBoundStatusV1.MALFORMED.value
    assert "LIVE_ACCOUNT_BOUND_MALFORMED" in evidence.reason_codes


def test_mismatch_wrong_account_deny() -> None:
    evidence = _evaluate_bound(expected_account_identity="other-account")
    assert evidence.evidence_status == LiveAccountBoundStatusV1.MISMATCH.value
    assert "LIVE_ACCOUNT_BOUND_WRONG_ACCOUNT" in evidence.reason_codes


def test_wrong_instrument_deny() -> None:
    payloads = _identity_payloads(instrument_id="BTC-USDT-SWAP")
    evidence = _evaluate_bound(
        get_evidence=_collect_get(transport=_bound_transport(payloads=payloads))
    )
    assert evidence.evidence_status == LiveAccountBoundStatusV1.MISMATCH.value
    assert "LIVE_ACCOUNT_BOUND_WRONG_INSTRUMENT" in evidence.reason_codes


def test_wrong_context_td_mode_deny() -> None:
    payloads = _identity_payloads(td_mode="isolated")
    evidence = _evaluate_bound(
        get_evidence=_collect_get(transport=_bound_transport(payloads=payloads))
    )
    assert evidence.evidence_status == LiveAccountBoundStatusV1.MISMATCH.value
    assert "LIVE_ACCOUNT_BOUND_WRONG_CONTEXT" in evidence.reason_codes


def test_contradictory_duplicate_account_deny() -> None:
    payloads = _identity_payloads(extra_uid="second-account")
    evidence = _evaluate_bound(
        get_evidence=_collect_get(transport=_bound_transport(payloads=payloads))
    )
    assert evidence.evidence_status == LiveAccountBoundStatusV1.CONTRADICTORY.value
    assert "LIVE_ACCOUNT_BOUND_DUPLICATE_AMBIGUOUS_ACCOUNT" in evidence.reason_codes


def test_stale_historical_and_fixture_deny() -> None:
    evidence = _evaluate_bound(
        get_evidence=_collect_get(pretrade_decision_id="HISTORICAL_Z2V_PACK")
    )
    assert evidence.evidence_status == LiveAccountBoundStatusV1.STALE.value
    assert "LIVE_ACCOUNT_BOUND_FIXTURE_REPLAY_NOT_PRODUCTIVE" in evidence.reason_codes
    replay = _evaluate_bound(
        get_evidence=_collect_get(transport=_bound_transport(historical_reuse=True))
    )
    assert replay.evidence_status == LiveAccountBoundStatusV1.STALE.value


def test_string_passthrough_live_account_bound_is_not_authority() -> None:
    decision = evaluate_execution_admission_v1(
        _live_inputs(
            capital_risk_mode=CAPITAL_RISK_MODE_LIVE_ACCOUNT_BOUND,
            live_account_bound_status=LiveAccountBoundStatusV1.MISSING.value,
        )
    )
    assert decision.admitted is False
    assert "LIVE_ACCOUNT_BOUND_STRING_PASSTHROUGH_NOT_AUTHORITY" in decision.reason_codes
    assert "LIVE_ACCOUNT_BOUND_CONTRADICTORY" in decision.reason_codes


def test_join_complete_bound_still_cannot_admit(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    path = _bind_state_path(tmp_path, monkeypatch)
    StatePersistence(str(path)).save(KillSwitchState.ACTIVE)
    inputs = _join_live(state_path=str(path))
    assert inputs.live_account_bound_status == LiveAccountBoundStatusV1.TRUSTED_PRESENT.value
    assert inputs.capital_risk_mode == CAPITAL_RISK_MODE_LIVE_ACCOUNT_BOUND
    assert inputs.fresh_pretrade_get_status == FreshPretradeGetStatusV1.TRUSTED_PRESENT.value
    assert inputs.live_enabled is False
    decision = evaluate_execution_admission_v1(inputs)
    assert decision.admitted is False
    assert "LIVE_ENABLED_FALSE" in decision.reason_codes
    assert "LIVE_ARMED_FALSE" in decision.reason_codes
    assert "WIRE_SEND_NOT_PERMITTED" in decision.reason_codes
    assert "LIVE_ACCOUNT_BOUND_MISSING" not in decision.reason_codes


def test_owner_permit_absent_overall_deny(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    path = _bind_state_path(tmp_path, monkeypatch)
    StatePersistence(str(path)).save(KillSwitchState.ACTIVE)
    inputs = _join_live(owner_go=None, state_path=str(path))
    decision = evaluate_execution_admission_v1(inputs)
    assert decision.admitted is False
    assert "OWNER_ONE_SHOT_PERMIT_MISSING" in decision.reason_codes
    assert inputs.live_account_bound_status == LiveAccountBoundStatusV1.TRUSTED_PRESENT.value


def test_filegate_deny_overall_deny(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    path = _bind_state_path(tmp_path, monkeypatch)
    StatePersistence(str(path)).save(KillSwitchState.KILLED)
    inputs = _join_live(state_path=str(path))
    decision = evaluate_execution_admission_v1(inputs)
    assert decision.admitted is False
    assert "DURABLE_FILEGATE_BLOCKS_TRADING" in decision.reason_codes
    assert inputs.live_account_bound_status == LiveAccountBoundStatusV1.TRUSTED_PRESENT.value


def test_fresh_get_deny_overall_deny(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    path = _bind_state_path(tmp_path, monkeypatch)
    StatePersistence(str(path)).save(KillSwitchState.ACTIVE)
    inputs = _join_live(transport=None, state_path=str(path))
    decision = evaluate_execution_admission_v1(inputs)
    assert decision.admitted is False
    assert "FRESH_PRETRADE_GET_MISSING" in decision.reason_codes
    assert inputs.live_account_bound_status == LiveAccountBoundStatusV1.MISSING.value


def test_account_bound_deny_does_not_override_other_gates(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    path = _bind_state_path(tmp_path, monkeypatch)
    StatePersistence(str(path)).save(KillSwitchState.ACTIVE)
    inputs = _join_live(expected_account_identity="other-account", state_path=str(path))
    decision = evaluate_execution_admission_v1(inputs)
    assert decision.admitted is False
    assert inputs.live_account_bound_status == LiveAccountBoundStatusV1.MISMATCH.value
    assert "LIVE_ACCOUNT_BOUND_MISMATCH" in decision.reason_codes
    assert inputs.owner_one_shot_permit_status == OwnerOneShotPermitStatusV1.TRUSTED_PRESENT.value
    assert inputs.durable_kill_switch_evidence_status == (
        DurableKillSwitchEvidenceStatusV1.TRUSTED_PRESENT.value
    )


def test_one_valid_gate_cannot_override_another() -> None:
    decision = evaluate_execution_admission_v1(
        _live_inputs(
            pretrade_source_kind=PRETRADE_SOURCE_FRESH_GET,
            pretrade_freshness_status=PretradeFreshnessStatusV1.LIVE_FRESH.value,
            capital_risk_mode=CAPITAL_RISK_MODE_LIVE_ACCOUNT_BOUND,
            durable_kill_switch_evidence_status=(
                DurableKillSwitchEvidenceStatusV1.TRUSTED_PRESENT.value
            ),
            durable_kill_switch_blocked=False,
            owner_authorization_present=True,
            owner_one_shot_permit_status=OwnerOneShotPermitStatusV1.TRUSTED_PRESENT.value,
            fresh_pretrade_get_status=FreshPretradeGetStatusV1.TRUSTED_PRESENT.value,
            live_account_bound_status=LiveAccountBoundStatusV1.TRUSTED_PRESENT.value,
            live_enabled=False,
            live_armed=False,
            wire_send_permitted=False,
        )
    )
    assert decision.admitted is False
    assert "LIVE_ENABLED_FALSE" in decision.reason_codes
    assert "LIVE_ARMED_FALSE" in decision.reason_codes
    assert "WIRE_SEND_NOT_PERMITTED" in decision.reason_codes


def test_offline_injected_full_core_path_halts_before_wire_and_does_not_post(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    path = _bind_state_path(tmp_path, monkeypatch)
    StatePersistence(str(path)).save(KillSwitchState.ACTIVE)
    transport = _bound_transport(payloads=_identity_payloads(instrument_id=_INSTRUMENT))
    result, _ = _run(
        monkeypatch,
        _confirmed_replay_input(side="LONG"),
        mode="LIVE",
        fresh_pretrade_get_transport=transport,
        expected_account_identity=_TEST_UID,
    )
    assert result.boundary is not None
    assert result.boundary.halt_before_wire is True
    assert result.boundary.admission is not None
    assert result.boundary.admission.admitted is False
    assert result.wire_send_occurred is False
    assert result.boundary.canary_http_invoked is False
    assert result.boundary.live_execution_port_constructed is False
    assert "HARD_STOP_BEFORE_WIRE" in result.reason_codes
    assert "LIVE_ENABLED_FALSE" in result.reason_codes
    assert "WIRE_SEND_NOT_PERMITTED" in result.reason_codes
    admission = result.boundary.admission
    assert "LIVE_ACCOUNT_BOUND_MISSING" not in admission.reason_codes
    assert JOIN_SEAM_ID
    assert result.full_core_system_e2e_proven is False
    assert result.current_live_core_path_proven is False


def test_runbook_and_spec_bind_closeout_without_live_arming() -> None:
    runbook = RUNBOOK.read_text(encoding="utf-8")
    spec = SPEC_PATH.read_text(encoding="utf-8")
    start = runbook.index("11.2.1.M FULL_CORE_REMAINING_ADMISSION_CHAIN_CLOSEOUT")
    section = runbook[start : runbook.index("## 11.3 Autonomy state model", start)]
    assert "LIVE_ACCOUNT_BOUND_IMPLEMENTED=true" in section
    assert "FULL_CORE_OFFLINE_E2E_PROVEN=true" in section
    assert "FULL_CORE_SYSTEM_E2E_PROVEN=false" in section
    assert "CURRENT_LIVE_CORE_PATH_PROVEN=false" in section
    assert "LIVE_ENABLED=false" in section
    assert "LIVE_ARMED=false" in section
    assert "WIRE_SEND_PERMITTED=false" in section
    assert "POST_PERFORMED=false" in section
    assert "LIVE_ACCOUNT_BOUND_ALONE_CAN_ADMIT=false" in section
    assert "EARLIEST_UNRESOLVED_FULL_CORE_DEPENDENCY=LIVE_ENABLED" in section
    assert "docs_token:" in spec
    assert "DOCS_TOKEN_FULL_CORE_REMAINING_ADMISSION_CHAIN_CLOSEOUT_V1" in spec
    prior = runbook[runbook.index("11.2.1.L FULL_CORE_FRESH_PRETRADE_RUNTIME_GET_SEAM") : start]
    assert "FRESH_PRETRADE_RUNTIME_GET_IMPLEMENTED=true" in prior
    assert "LIVE_ACCOUNT_BOUND_IMPLEMENTED=false" in prior
    assert "EARLIEST_UNRESOLVED_FULL_CORE_DEPENDENCY=LIVE_ACCOUNT_BOUND_IMPLEMENTED" in prior
