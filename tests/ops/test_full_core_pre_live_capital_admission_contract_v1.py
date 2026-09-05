"""Pre-Live Capital Admission contract. Injected only. No venue GET. No POST."""

from __future__ import annotations

from pathlib import Path

import pytest

from src.ops.full_core_live_path_composition_root_v1.capital_admission_v1 import (
    JOIN_SEAM_ID,
    CapitalAdmissionClaimV1,
    evaluate_capital_admission_v1,
    join_capital_admission_into_admission_inputs_v1,
    live_venue_capital_may_bind_step_29p_v1,
)
from src.ops.full_core_live_path_composition_root_v1.constants_v1 import (
    CAPITAL_ADMISSION_IMPLEMENTED,
    FULL_CORE_OFFLINE_E2E_PROVEN,
    FULL_CORE_SYSTEM_E2E_PROVEN,
    LIVE_ARMED,
    LIVE_ENABLED,
    OWNER_ONE_SHOT_PERMIT_TOKEN,
    WIRE_SEND_PERMITTED,
)
from src.ops.full_core_live_path_composition_root_v1.execution_admission_contract_v1 import (
    ADMISSION_CONTEXT_LIVE,
    ADMISSION_CONTEXT_OFFLINE_FULL_CORE_PROOF,
    CAPITAL_AUTHORITY_NONE,
    CAPITAL_AUTHORITY_OBSERVED_NOT_RISK_ADMISSIBLE,
    CAPITAL_AUTHORITY_RISK_ADMISSIBLE,
    CAPITAL_RISK_MODE_LIVE_ACCOUNT_BOUND,
    CAPITAL_RISK_MODE_OFFLINE_ALGEBRA,
    CAPITAL_SOURCE_OBSERVED_VENUE,
    CapitalAdmissionStatusV1,
    DurableKillSwitchEvidenceStatusV1,
    FreshPretradeGetStatusV1,
    LiveAccountBoundStatusV1,
    OwnerOneShotPermitStatusV1,
    PRETRADE_SOURCE_FRESH_GET,
    PretradeFreshnessStatusV1,
    evaluate_execution_admission_v1,
)
from src.ops.full_core_live_path_composition_root_v1.live_admission_gap_dag_v1 import (
    EARLIEST_UNRESOLVED_FULL_CORE_DEPENDENCY,
    gap_node_v1,
)
from src.risk_layer.kill_switch.persistence import StatePersistence
from src.risk_layer.kill_switch.state import KillSwitchState
from src.trading.master_v2.capital_risk_sizing_offline_replay_binding_adapter_v0 import (
    CAPITAL_RISK_MODE_OFFLINE_ALGEBRA as REPLAY_OFFLINE_ALGEBRA,
    default_offline_replay_capital_context_v0,
)
from tests.ops.test_full_core_execution_admission_contract_v1 import _live_inputs
from tests.ops.test_full_core_live_account_bound_and_remaining_closeout_v1 import (
    _TEST_INST,
    _TEST_TD,
    _TEST_UID,
    _bind_state_path,
    _bound_transport,
    _identity_payloads,
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
SPEC_PATH = REPO_ROOT / "docs/ops/specs/PRE_LIVE_CAPITAL_ADMISSION_CONTRACT_V1.md"


def _claim(**overrides) -> CapitalAdmissionClaimV1:
    payload = {
        "source_class": CAPITAL_SOURCE_OBSERVED_VENUE,
        "account_identity": _TEST_UID,
        "instrument_id": _TEST_INST,
        "observed_capital_raw": "100",
        "observed_field_name": "details.availEq",
        "claimed_risk_admissible_capital": "",
        "claimed_source_field": "",
        "previously_admitted_risk_capital": "",
        "evidence_class": "LIVE_TYPED",
        "evidence_id": "capital-claim-1",
    }
    payload.update(overrides)
    return CapitalAdmissionClaimV1(**payload)


_UNSET = object()


def _evaluate(*, claim=_UNSET, **overrides):
    payload = {
        "claim": _claim() if claim is _UNSET else claim,
        "expected_account_identity": _TEST_UID,
        "expected_instrument_id": _TEST_INST,
        "admission_context": ADMISSION_CONTEXT_LIVE,
    }
    payload.update(overrides)
    return evaluate_capital_admission_v1(**payload)


_DEFAULT_TRANSPORT = object()


def _join(*, transport=_DEFAULT_TRANSPORT, claim=_DEFAULT_TRANSPORT, **kwargs):
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
        "expected_account_identity": _TEST_UID,
        "capital_admission_claim": _claim() if claim is _DEFAULT_TRANSPORT else claim,
    }
    payload.update(kwargs)
    return join_capital_admission_into_admission_inputs_v1(**payload)


def test_flags_and_standing_gates_remain_false() -> None:
    assert CAPITAL_ADMISSION_IMPLEMENTED is True
    assert LIVE_ENABLED is False
    assert LIVE_ARMED is False
    assert WIRE_SEND_PERMITTED is False
    assert FULL_CORE_OFFLINE_E2E_PROVEN is True
    assert FULL_CORE_SYSTEM_E2E_PROVEN is False
    assert EARLIEST_UNRESOLVED_FULL_CORE_DEPENDENCY == (
        "LIVE_VENUE_CAPITAL_NOT_ADMITTED_TO_STEP_29P"
    )
    node = gap_node_v1("CAPITAL_ADMISSION")
    assert node.implementation_status == "JOINED_TYPED_EVIDENCE_FAIL_CLOSED"
    assert node.wiring_authorized is True
    assert node.standing_live_gates_would_change is False
    assert node.consumer.startswith("evaluate_execution_admission_v1")


def test_valid_typed_capital_evidence_component_may_pass() -> None:
    evidence = _evaluate()
    assert evidence.evidence_status == CapitalAdmissionStatusV1.TRUSTED_PRESENT.value
    assert evidence.capital_authority_class == CAPITAL_AUTHORITY_OBSERVED_NOT_RISK_ADMISSIBLE
    assert evidence.risk_admissible is False
    assert evidence.live_enabled is False
    assert evidence.wire_send_permitted is False
    assert live_venue_capital_may_bind_step_29p_v1(evidence) is False
    assert "CAPITAL_ADMISSION_TRUSTED_PRESENT" in evidence.reason_codes
    assert "OBSERVED_CAPITAL_NOT_RISK_ADMISSIBLE" in evidence.reason_codes


def test_missing_claim_deny() -> None:
    evidence = _evaluate(claim=None)
    assert evidence.evidence_status == CapitalAdmissionStatusV1.MISSING.value
    assert "CAPITAL_ADMISSION_MISSING" in evidence.reason_codes
    assert "FRESH_GET_ALONE_NOT_CAPITAL_AUTHORITY" in evidence.reason_codes
    assert "LIVE_ACCOUNT_BOUND_ALONE_NOT_CAPITAL_AUTHORITY" in evidence.reason_codes


def test_malformed_observed_deny() -> None:
    evidence = _evaluate(claim=_claim(observed_capital_raw="not-a-number"))
    assert evidence.evidence_status == CapitalAdmissionStatusV1.MALFORMED.value
    assert "CAPITAL_ADMISSION_MALFORMED" in evidence.reason_codes


def test_stale_historical_fixture_replay_deny() -> None:
    historical = _evaluate(claim=_claim(evidence_class="HISTORICAL", evidence_id="pack-1"))
    assert historical.evidence_status == CapitalAdmissionStatusV1.STALE.value
    assert "CAPITAL_ADMISSION_HISTORICAL_NOT_PRODUCTIVE" in historical.reason_codes
    fixture = _evaluate(claim=_claim(source_class="FIXTURE", evidence_class="FIXTURE"))
    assert fixture.evidence_status == CapitalAdmissionStatusV1.STALE.value
    assert "CAPITAL_ADMISSION_FIXTURE_NOT_PRODUCTIVE" in fixture.reason_codes
    replay = _evaluate(claim=_claim(source_class="REPLAY", evidence_class="REPLAY"))
    assert replay.evidence_status == CapitalAdmissionStatusV1.STALE.value
    assert "CAPITAL_ADMISSION_REPLAY_NOT_PRODUCTIVE" in replay.reason_codes


def test_offline_algebra_not_live_capital() -> None:
    evidence = _evaluate(
        claim=_claim(source_class="OFFLINE_ALGEBRA", evidence_class="OFFLINE_ALGEBRA")
    )
    assert evidence.evidence_status == CapitalAdmissionStatusV1.STALE.value
    assert "OFFLINE_ALGEBRA_NOT_LIVE_CAPITAL_AUTHORITY" in evidence.reason_codes
    assert live_venue_capital_may_bind_step_29p_v1(evidence) is False


def test_contradictory_risk_admissible_claim_deny() -> None:
    evidence = _evaluate(claim=_claim(claimed_risk_admissible_capital="100"))
    assert evidence.evidence_status == CapitalAdmissionStatusV1.CONTRADICTORY.value
    assert "CAPITAL_ADMISSION_RISK_ADMISSIBLE_POLICY_FROZEN" in evidence.reason_codes
    assert "CAPITAL_INCREASE_NOT_AUTO_ADMITTED" in evidence.reason_codes


def test_wrong_account_and_instrument_deny() -> None:
    wrong_account = _evaluate(claim=_claim(account_identity="other-account"))
    assert wrong_account.evidence_status == CapitalAdmissionStatusV1.WRONG_CONTEXT.value
    assert "CAPITAL_ADMISSION_WRONG_ACCOUNT" in wrong_account.reason_codes
    wrong_inst = _evaluate(claim=_claim(instrument_id="BTC-USDT-SWAP"))
    assert wrong_inst.evidence_status == CapitalAdmissionStatusV1.WRONG_CONTEXT.value
    assert "CAPITAL_ADMISSION_WRONG_INSTRUMENT" in wrong_inst.reason_codes


def test_optimistic_field_fallback_deny() -> None:
    for field in ("totalEq", "eq", "adjEq", "availEq", "availBal", "cashBal"):
        evidence = _evaluate(claim=_claim(claimed_source_field=field))
        assert evidence.evidence_status == CapitalAdmissionStatusV1.CONTRADICTORY.value
        assert "CAPITAL_ADMISSION_OPTIMISTIC_FIELD_FALLBACK" in evidence.reason_codes


def test_balance_increase_does_not_increase_sizing_authority() -> None:
    observed_only = _evaluate(claim=_claim(observed_capital_raw="500"))
    assert observed_only.evidence_status == CapitalAdmissionStatusV1.TRUSTED_PRESENT.value
    assert live_venue_capital_may_bind_step_29p_v1(observed_only) is False
    increase = _evaluate(
        claim=_claim(observed_capital_raw="200", previously_admitted_risk_capital="50")
    )
    assert increase.evidence_status == CapitalAdmissionStatusV1.CONTRADICTORY.value
    assert "CAPITAL_INCREASE_NOT_AUTO_ADMITTED" in increase.reason_codes
    assert live_venue_capital_may_bind_step_29p_v1(increase) is False


def test_capital_decrease_denies_stale_higher_capacity() -> None:
    evidence = _evaluate(
        claim=_claim(observed_capital_raw="40", previously_admitted_risk_capital="100")
    )
    assert evidence.evidence_status == CapitalAdmissionStatusV1.STALE.value
    assert "CAPITAL_DECREASE_STALE_HIGHER_DENIED" in evidence.reason_codes
    assert live_venue_capital_may_bind_step_29p_v1(evidence) is False


def test_fresh_get_valid_but_capital_missing_overall_deny(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    path = _bind_state_path(tmp_path, monkeypatch)
    StatePersistence(str(path)).save(KillSwitchState.ACTIVE)
    inputs = _join(claim=None, state_path=str(path))
    assert inputs.fresh_pretrade_get_status == FreshPretradeGetStatusV1.TRUSTED_PRESENT.value
    assert inputs.live_account_bound_status == LiveAccountBoundStatusV1.TRUSTED_PRESENT.value
    assert inputs.capital_admission_status == CapitalAdmissionStatusV1.MISSING.value
    decision = evaluate_execution_admission_v1(inputs)
    assert decision.admitted is False
    assert "CAPITAL_ADMISSION_MISSING" in decision.reason_codes
    assert "LIVE_ACCOUNT_BOUND_MISSING" not in decision.reason_codes


def test_live_account_bound_valid_but_capital_invalid_overall_deny(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    path = _bind_state_path(tmp_path, monkeypatch)
    StatePersistence(str(path)).save(KillSwitchState.ACTIVE)
    inputs = _join(claim=_claim(account_identity="other-account"), state_path=str(path))
    assert inputs.live_account_bound_status == LiveAccountBoundStatusV1.TRUSTED_PRESENT.value
    assert inputs.capital_admission_status == CapitalAdmissionStatusV1.WRONG_CONTEXT.value
    decision = evaluate_execution_admission_v1(inputs)
    assert decision.admitted is False
    assert "CAPITAL_ADMISSION_WRONG_CONTEXT" in decision.reason_codes


def test_capital_valid_live_enabled_false_overall_deny(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    path = _bind_state_path(tmp_path, monkeypatch)
    StatePersistence(str(path)).save(KillSwitchState.ACTIVE)
    inputs = _join(state_path=str(path))
    assert inputs.capital_admission_status == CapitalAdmissionStatusV1.TRUSTED_PRESENT.value
    assert inputs.live_enabled is False
    decision = evaluate_execution_admission_v1(inputs)
    assert decision.admitted is False
    assert "LIVE_ENABLED_FALSE" in decision.reason_codes
    assert "LIVE_ARMED_FALSE" in decision.reason_codes
    assert "WIRE_SEND_NOT_PERMITTED" in decision.reason_codes


def test_forged_risk_admissible_cannot_override_gates() -> None:
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
            capital_admission_status=CapitalAdmissionStatusV1.TRUSTED_PRESENT.value,
            capital_authority_class=CAPITAL_AUTHORITY_RISK_ADMISSIBLE,
            live_enabled=False,
            live_armed=False,
            wire_send_permitted=False,
        )
    )
    assert decision.admitted is False
    assert "CAPITAL_ADMISSION_RISK_ADMISSIBLE_POLICY_FROZEN" in decision.reason_codes
    assert "LIVE_ENABLED_FALSE" in decision.reason_codes
    assert "CAPITAL_ADMISSION_MISSING" not in decision.reason_codes


def test_offline_algebra_replay_is_not_live_capital() -> None:
    ctx = default_offline_replay_capital_context_v0(instrument_id=_TEST_INST)
    assert ctx.capital_risk_mode == REPLAY_OFFLINE_ALGEBRA
    evidence = evaluate_capital_admission_v1(
        claim=None,
        expected_account_identity=_TEST_UID,
        expected_instrument_id=_TEST_INST,
        admission_context=ADMISSION_CONTEXT_OFFLINE_FULL_CORE_PROOF,
    )
    assert evidence.evidence_status == CapitalAdmissionStatusV1.NOT_REQUIRED_OFFLINE.value
    assert live_venue_capital_may_bind_step_29p_v1(evidence) is False


def test_capital_admission_cannot_override_other_gates(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    path = _bind_state_path(tmp_path, monkeypatch)
    StatePersistence(str(path)).save(KillSwitchState.KILLED)
    inputs = _join(state_path=str(path))
    decision = evaluate_execution_admission_v1(inputs)
    assert decision.admitted is False
    assert inputs.capital_admission_status == CapitalAdmissionStatusV1.TRUSTED_PRESENT.value
    assert "DURABLE_FILEGATE_BLOCKS_TRADING" in decision.reason_codes
    assert "LIVE_ENABLED_FALSE" in decision.reason_codes


def test_offline_injected_path_still_halts_before_wire(
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
    assert "CAPITAL_ADMISSION_MISSING" in result.boundary.admission.reason_codes
    assert "LIVE_VENUE_CAPITAL_NOT_ADMITTED_TO_STEP_29P" in result.boundary.admission.reason_codes
    assert JOIN_SEAM_ID


def test_runbook_and_spec_bind_without_live_arming() -> None:
    runbook = RUNBOOK.read_text(encoding="utf-8")
    spec = SPEC_PATH.read_text(encoding="utf-8")
    start = runbook.index("11.2.1.N PRE_LIVE_CAPITAL_ADMISSION_CONTRACT")
    section = runbook[start : runbook.index("11.2.2 TREASURY_PHASE_1_OFFLINE_CONTRACTS", start)]
    assert "CAPITAL_ADMISSION_IMPLEMENTED=true" in section
    assert "OBSERVED_CAPITAL != RISK_ADMISSIBLE_CAPITAL" in section
    assert "PL_TF_001_STATUS=CLOSED_TYPED_ADMISSION_SEAM" in section
    assert "PL_TF_002_STATUS=FROZEN_PENDING_NETWORK_EVIDENCE" in section
    assert "LIVE_ENABLED=false" in section
    assert "LIVE_ARMED=false" in section
    assert "WIRE_SEND_PERMITTED=false" in section
    assert "TREASURY_MUTATION_REACHABLE_FROM_TRADING=false" in section
    assert "EARLIEST_UNRESOLVED_FULL_CORE_DEPENDENCY=LIVE_ENABLED" in section
    assert "docs_token:" in spec
    assert "DOCS_TOKEN_PRE_LIVE_CAPITAL_ADMISSION_CONTRACT_V1" in spec
    assert CAPITAL_AUTHORITY_NONE == "NONE"
