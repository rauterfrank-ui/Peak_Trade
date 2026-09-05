"""Full-Core Execution Admission contract: fail-closed; FILEGATE join is typed evidence only."""

from __future__ import annotations

from decimal import Decimal
from pathlib import Path

import pytest

from src.ops.full_core_live_path_composition_root_v1.constants_v1 import (
    LIVE_ARMED,
    LIVE_ENABLED,
    MODE_LIVE,
    MODE_TEST,
    WIRE_SEND_PERMITTED,
)
from src.ops.full_core_live_path_composition_root_v1.execution_admission_contract_v1 import (
    ADMISSION_CONTEXT_LIVE,
    ADMISSION_CONTEXT_OFFLINE_FULL_CORE_PROOF,
    CAPITAL_RISK_MODE_LIVE_ACCOUNT_BOUND,
    CAPITAL_RISK_MODE_OFFLINE_ALGEBRA,
    DurableKillSwitchEvidenceStatusV1,
    ExecutionAdmissionInputsV1,
    PRETRADE_SOURCE_FRESH_GET,
    PRETRADE_SOURCE_FROZEN_OFFLINE,
    PretradeFreshnessStatusV1,
    default_untrusted_filegate_inputs_v1,
    evaluate_execution_admission_v1,
)
from src.ops.full_core_live_path_composition_root_v1.models_v1 import FrozenPretradeEvidenceV1
from tests.ops.test_full_core_live_path_composition_root_v1 import _run
from tests.trading.master_v2.test_master_v2_integrated_replay_safety_before_intent_restore_contract_v1 import (
    _confirmed_replay_input,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
MASTER_V2 = REPO_ROOT / "src/trading/master_v2"


def _live_inputs(**overrides) -> ExecutionAdmissionInputsV1:
    payload = {
        "plan_identity": "plan-1",
        "venue_plan_identity": "venue-1",
        "instrument_identity_ok": True,
        "pretrade_admissible": True,
        "pretrade_source_kind": PRETRADE_SOURCE_FROZEN_OFFLINE,
        "pretrade_freshness_status": PretradeFreshnessStatusV1.FROZEN_OFFLINE.value,
        "capital_risk_mode": CAPITAL_RISK_MODE_OFFLINE_ALGEBRA,
        "durable_kill_switch_evidence_status": (
            DurableKillSwitchEvidenceStatusV1.UNKNOWN_BLOCKED.value
        ),
        "durable_kill_switch_blocked": None,
        "live_enabled": False,
        "live_armed": False,
        "wire_send_permitted": False,
        "owner_authorization_present": True,
        "admission_context": ADMISSION_CONTEXT_LIVE,
        "provenance_refs": (),
    }
    payload.update(overrides)
    return ExecutionAdmissionInputsV1(**payload)


def test_standing_live_flags_remain_false() -> None:
    assert LIVE_ENABLED is False
    assert LIVE_ARMED is False
    assert WIRE_SEND_PERMITTED is False
    assert MODE_TEST == "TEST"


def test_missing_filegate_evidence_is_not_admitted() -> None:
    decision = evaluate_execution_admission_v1(_live_inputs())
    assert decision.admitted is False
    assert decision.fail_closed is True
    assert "DURABLE_FILEGATE_EVIDENCE_MISSING" in decision.reason_codes
    assert decision.runtime_authority_effect == "NONE"


def test_offline_algebra_live_admission_denied() -> None:
    decision = evaluate_execution_admission_v1(_live_inputs())
    assert decision.admitted is False
    assert "OFFLINE_ALGEBRA_LIVE_ADMISSION_DENIED" in decision.reason_codes
    assert "OFFLINE_ALGEBRA_NOT_LIVE_CAPITAL_AUTHORITY" in decision.reason_codes


def test_frozen_pretrade_live_admission_denied() -> None:
    decision = evaluate_execution_admission_v1(_live_inputs())
    assert decision.admitted is False
    assert "FROZEN_PRETRADE_LIVE_ADMISSION_DENIED" in decision.reason_codes
    assert "FROZEN_OFFLINE_PRETRADE_NOT_LIVE_FRESH" in decision.reason_codes


def test_instrument_identity_mismatch_not_admitted() -> None:
    decision = evaluate_execution_admission_v1(_live_inputs(instrument_identity_ok=False))
    assert decision.admitted is False
    assert "INSTRUMENT_IDENTITY_MISMATCH" in decision.reason_codes


def test_missing_owner_authorization_not_admitted() -> None:
    decision = evaluate_execution_admission_v1(_live_inputs(owner_authorization_present=False))
    assert decision.admitted is False
    assert "MISSING_OWNER_AUTHORIZATION" in decision.reason_codes


def test_missing_pretrade_freshness_not_admitted() -> None:
    decision = evaluate_execution_admission_v1(
        _live_inputs(pretrade_freshness_status=PretradeFreshnessStatusV1.MISSING.value)
    )
    assert decision.admitted is False
    assert "PRETRADE_FRESHNESS_MISSING" in decision.reason_codes
    assert "FROZEN_PRETRADE_LIVE_ADMISSION_DENIED" in decision.reason_codes


def test_fresh_get_source_is_not_implemented() -> None:
    decision = evaluate_execution_admission_v1(
        _live_inputs(
            pretrade_source_kind=PRETRADE_SOURCE_FRESH_GET,
            pretrade_freshness_status=PretradeFreshnessStatusV1.LIVE_FRESH.value,
            capital_risk_mode=CAPITAL_RISK_MODE_LIVE_ACCOUNT_BOUND,
        )
    )
    assert decision.admitted is False
    assert "FRESH_PRETRADE_GET_NOT_IMPLEMENTED" in decision.reason_codes


def test_default_full_core_caller_injects_unknown_blocked() -> None:
    inputs = default_untrusted_filegate_inputs_v1(
        plan_identity="p",
        venue_plan_identity="v",
        instrument_identity_ok=True,
        pretrade_admissible=True,
        pretrade_source_kind=PRETRADE_SOURCE_FROZEN_OFFLINE,
        pretrade_freshness_status=PretradeFreshnessStatusV1.FROZEN_OFFLINE.value,
        capital_risk_mode=CAPITAL_RISK_MODE_OFFLINE_ALGEBRA,
        owner_authorization_present=True,
        admission_context=ADMISSION_CONTEXT_OFFLINE_FULL_CORE_PROOF,
    )
    assert inputs.durable_kill_switch_evidence_status == (
        DurableKillSwitchEvidenceStatusV1.UNKNOWN_BLOCKED.value
    )
    assert inputs.durable_kill_switch_blocked is None
    decision = evaluate_execution_admission_v1(inputs)
    assert decision.admitted is False


def test_full_core_offline_path_halts_when_filegate_evidence_is_missing(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path,
) -> None:
    missing = tmp_path / "absent_kill_switch.json"
    monkeypatch.setenv("PEAK_KILL_SWITCH_STATE_PATH", str(missing))
    monkeypatch.delenv("PEAKTRADE_KILL_SWITCH_STATE_PATH", raising=False)
    monkeypatch.delenv("PEAK_KILL_SWITCH", raising=False)
    result, replay = _run(monkeypatch, _confirmed_replay_input(side="LONG"))
    assert replay.capital_risk_mode == CAPITAL_RISK_MODE_OFFLINE_ALGEBRA
    assert result.boundary is not None
    assert result.boundary.halt_before_wire is True
    assert result.boundary.admission is not None
    assert result.boundary.admission.admitted is False
    assert "DURABLE_FILEGATE_EVIDENCE_MISSING" in result.reason_codes
    assert result.wire_send_occurred is False
    assert "HARD_STOP_BEFORE_WIRE" in result.reason_codes


def test_full_core_live_mode_denies_frozen_and_offline_algebra(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    result, _ = _run(
        monkeypatch,
        _confirmed_replay_input(side="LONG"),
        mode=MODE_LIVE,
    )
    assert result.boundary is not None
    assert result.boundary.admission is not None
    assert result.boundary.admission.admitted is False
    assert "FROZEN_PRETRADE_LIVE_ADMISSION_DENIED" in result.reason_codes
    assert "OFFLINE_ALGEBRA_LIVE_ADMISSION_DENIED" in result.reason_codes
    assert result.wire_send_occurred is False


def test_frozen_pretrade_default_is_never_live_fresh() -> None:
    frozen = FrozenPretradeEvidenceV1(
        max_available=Decimal("10"),
        max_size=Decimal("10"),
        available_margin_ok=True,
        price_band_ok=True,
        instrument_state_ok=True,
        account_mode_ok=True,
        pos_mode_ok=True,
        margin_mode_ok=True,
        leverage_ok=True,
    )
    assert frozen.source_kind == "FROZEN_OFFLINE_PRETRADE_EVIDENCE"
    assert frozen.freshness_status == "FROZEN_OFFLINE"
    assert frozen.freshness_status != "LIVE_FRESH"


def test_master_v2_does_not_import_durable_filegate_runtime_reader() -> None:
    for path in MASTER_V2.rglob("*.py"):
        text = path.read_text(encoding="utf-8")
        assert "kill_switch_should_block_trading(" not in text
        assert "import StatePersistence" not in text
        assert "from src.ops.gates.risk_gate" not in text


def test_construct_live_execution_port_remains_forbidden_on_halt(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    result, _ = _run(
        monkeypatch,
        _confirmed_replay_input(side="LONG"),
        attempt_construct_live_port=True,
    )
    assert result.boundary is not None
    assert result.boundary.live_execution_port_constructed is False
    assert "LIVE_EXECUTION_PORT_CONSTRUCTION_FORBIDDEN" in result.reason_codes
