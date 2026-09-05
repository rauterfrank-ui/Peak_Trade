"""Full-Core LIVE_ENABLED standing admission seam. Offline. No wire. No port."""

from __future__ import annotations

from pathlib import Path

from src.ops.full_core_live_path_composition_root_v1.canary_isolation_v1 import (
    refuse_canary_plan_as_full_core_e2e_v1,
)
from src.ops.full_core_live_path_composition_root_v1.constants_v1 import (
    LIVE_ARMED,
    LIVE_ENABLED,
    LIVE_ENABLED_DOES_NOT_IMPLY_LIVE_ARMED,
    LIVE_ENABLED_DOES_NOT_IMPLY_PORT_CONSTRUCTION,
    LIVE_ENABLED_DOES_NOT_IMPLY_WIRE_SEND,
    LIVE_ENABLED_FALSE_REMAINS_FAIL_CLOSED,
    LIVE_ENABLED_STANDING_ADMISSION_SEAM_IMPLEMENTED,
    LIVE_ENABLED_TRUE_IS_NOT_AUTOMATIC_ADMISSION,
    OWNER_ONE_SHOT_PERMIT_TOKEN,
    WIRE_SEND_PERMITTED,
)
from src.ops.full_core_live_path_composition_root_v1.execution_admission_contract_v1 import (
    ADMISSION_CONTEXT_LIVE,
    ADMISSION_CONTEXT_OFFLINE_FULL_CORE_PROOF,
    CAPITAL_AUTHORITY_OBSERVED_NOT_RISK_ADMISSIBLE,
    CAPITAL_RISK_MODE_LIVE_ACCOUNT_BOUND,
    DurableKillSwitchEvidenceStatusV1,
    FreshPretradeGetStatusV1,
    LiveAccountBoundStatusV1,
    OwnerOneShotPermitStatusV1,
    PRETRADE_SOURCE_FRESH_GET,
    PretradeFreshnessStatusV1,
    CapitalAdmissionStatusV1,
    evaluate_execution_admission_v1,
)
from src.ops.full_core_live_path_composition_root_v1.live_admission_gap_dag_v1 import (
    CANONICAL_ORDER_HOST_JOIN_VS_LIVE_ARMED_VS_LIVE_EXECUTION_PORT,
    EARLIEST_UNRESOLVED_FULL_CORE_DEPENDENCY,
    HOST_JOIN_NOT_IN_LIVE_ADMISSION_GAP_DAG,
    LIVE_EXECUTION_PORT_CONSTRUCTION_FORBIDDEN,
    gap_node_v1,
    live_admission_gap_dag_v1,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.constants_v1 import (
    DEFAULT_INSTRUMENT_ID,
    DEFAULT_SIDE,
    LIVE_CANARY_MINIMUM_EXPOSURE_AUTHORIZED_DEFAULT,
)
from tests.ops.test_full_core_execution_admission_contract_v1 import _live_inputs
from tests.ops.test_full_core_live_path_composition_root_v1 import _run
from tests.trading.master_v2.test_master_v2_integrated_replay_safety_before_intent_restore_contract_v1 import (
    _confirmed_replay_input,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
RUNBOOK = REPO_ROOT / "docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md"
SPEC_PATH = REPO_ROOT / "docs/ops/specs/FULL_CORE_LIVE_ENABLED_STANDING_ADMISSION_SEAM_V1.md"

_LIVE_ENABLED_DENY_REASONS = frozenset(
    {
        "LIVE_ENABLED_FALSE",
        "STANDING_OR_INPUT_LIVE_ENABLED",
        "STANDING_LIVE_ENABLED_TRUE",
    }
)


def _all_modelable_live_gates_true(**overrides):
    payload = {
        "live_enabled": True,
        "live_armed": True,
        "wire_send_permitted": True,
        "instrument_identity_ok": True,
        "pretrade_admissible": True,
        "pretrade_source_kind": PRETRADE_SOURCE_FRESH_GET,
        "pretrade_freshness_status": PretradeFreshnessStatusV1.LIVE_FRESH.value,
        "capital_risk_mode": CAPITAL_RISK_MODE_LIVE_ACCOUNT_BOUND,
        "durable_kill_switch_evidence_status": (
            DurableKillSwitchEvidenceStatusV1.TRUSTED_PRESENT.value
        ),
        "durable_kill_switch_blocked": False,
        "owner_authorization_present": True,
        "owner_one_shot_permit_status": OwnerOneShotPermitStatusV1.TRUSTED_PRESENT.value,
        "admission_context": ADMISSION_CONTEXT_LIVE,
        "fresh_pretrade_get_status": FreshPretradeGetStatusV1.TRUSTED_PRESENT.value,
        "live_account_bound_status": LiveAccountBoundStatusV1.TRUSTED_PRESENT.value,
        "capital_admission_status": CapitalAdmissionStatusV1.TRUSTED_PRESENT.value,
        "capital_authority_class": CAPITAL_AUTHORITY_OBSERVED_NOT_RISK_ADMISSIBLE,
    }
    payload.update(overrides)
    return _live_inputs(**payload)


def test_standing_live_enabled_default_and_seam_flags() -> None:
    assert LIVE_ENABLED is False
    assert LIVE_ARMED is False
    assert WIRE_SEND_PERMITTED is False
    assert LIVE_ENABLED_STANDING_ADMISSION_SEAM_IMPLEMENTED is True
    assert LIVE_ENABLED_TRUE_IS_NOT_AUTOMATIC_ADMISSION is True
    assert LIVE_ENABLED_FALSE_REMAINS_FAIL_CLOSED is True
    assert LIVE_ENABLED_DOES_NOT_IMPLY_LIVE_ARMED is True
    assert LIVE_ENABLED_DOES_NOT_IMPLY_WIRE_SEND is True
    assert LIVE_ENABLED_DOES_NOT_IMPLY_PORT_CONSTRUCTION is True
    node = gap_node_v1("LIVE_ENABLED")
    assert node.implementation_status == "STANDING_ADMISSION_SEAM_IMPLEMENTED_DEFAULT_FALSE"
    assert node.wiring_authorized is True
    assert node.standing_live_gates_would_change is False
    assert EARLIEST_UNRESOLVED_FULL_CORE_DEPENDENCY == ("STEP_29P_EQUITY_DIMENSION_BINDING_MISSING")
    assert HOST_JOIN_NOT_IN_LIVE_ADMISSION_GAP_DAG is True
    assert LIVE_EXECUTION_PORT_CONSTRUCTION_FORBIDDEN is True
    assert CANONICAL_ORDER_HOST_JOIN_VS_LIVE_ARMED_VS_LIVE_EXECUTION_PORT == (
        "STANDING_GATES_BEFORE_CONSTRUCTION_CAP72_HOST_REMAINS_SIMULATED"
    )
    dag = live_admission_gap_dag_v1()
    assert dag["LIVE_ENABLED"] is False
    assert dag["LIVE_ENABLED_STANDING_ADMISSION_SEAM_IMPLEMENTED"] is True
    assert dag["EARLIEST_UNRESOLVED_FULL_CORE_DEPENDENCY"] == (
        "STEP_29P_EQUITY_DIMENSION_BINDING_MISSING"
    )


def test_case1_live_enabled_false_denies_with_named_reason() -> None:
    decision = evaluate_execution_admission_v1(_live_inputs(live_enabled=False))
    assert decision.admitted is False
    assert decision.fail_closed is True
    assert "LIVE_ENABLED_FALSE" in decision.reason_codes
    assert "STANDING_OR_INPUT_LIVE_ENABLED" not in decision.reason_codes


def test_case2_live_enabled_true_alone_is_not_deny_reason() -> None:
    decision = evaluate_execution_admission_v1(
        _live_inputs(live_enabled=True, live_armed=False, wire_send_permitted=False)
    )
    assert decision.admitted is False
    assert not _LIVE_ENABLED_DENY_REASONS.intersection(decision.reason_codes)
    assert "LIVE_ARMED_FALSE" in decision.reason_codes
    assert "WIRE_SEND_NOT_PERMITTED" in decision.reason_codes


def test_case3_wire_permission_blocks_when_enabled_and_armed() -> None:
    decision = evaluate_execution_admission_v1(
        _live_inputs(live_enabled=True, live_armed=True, wire_send_permitted=False)
    )
    assert decision.admitted is False
    assert not _LIVE_ENABLED_DENY_REASONS.intersection(decision.reason_codes)
    assert "LIVE_ARMED_FALSE" not in decision.reason_codes
    assert "STANDING_OR_INPUT_LIVE_ARMED" not in decision.reason_codes
    assert "WIRE_SEND_NOT_PERMITTED" in decision.reason_codes


def test_case4_all_modelable_booleans_true_still_halt_on_unresolved_dependency() -> None:
    decision = evaluate_execution_admission_v1(_all_modelable_live_gates_true())
    assert decision.admitted is False
    assert not _LIVE_ENABLED_DENY_REASONS.intersection(decision.reason_codes)
    assert "STANDING_OR_INPUT_LIVE_ARMED" not in decision.reason_codes
    assert "STANDING_OR_INPUT_WIRE_SEND_PERMITTED" not in decision.reason_codes
    assert "LIVE_VENUE_CAPITAL_NOT_ADMITTED_TO_STEP_29P" in decision.reason_codes
    assert "OBSERVED_CAPITAL_NOT_RISK_ADMISSIBLE" in decision.reason_codes


def test_case4_offline_context_with_all_booleans_true_still_not_admitted() -> None:
    decision = evaluate_execution_admission_v1(
        _all_modelable_live_gates_true(admission_context=ADMISSION_CONTEXT_OFFLINE_FULL_CORE_PROOF)
    )
    assert decision.admitted is False
    assert not _LIVE_ENABLED_DENY_REASONS.intersection(decision.reason_codes)
    assert "OFFLINE_FULL_CORE_PROOF_NOT_LIVE_ADMISSION" in decision.reason_codes


def test_case5_canary_surface_unchanged_by_full_core_live_enabled_true() -> None:
    decision = evaluate_execution_admission_v1(_live_inputs(live_enabled=True))
    assert decision.admitted is False
    assert LIVE_ENABLED is False
    assert LIVE_CANARY_MINIMUM_EXPOSURE_AUTHORIZED_DEFAULT is False
    canary = refuse_canary_plan_as_full_core_e2e_v1(
        {"instrument_id": DEFAULT_INSTRUMENT_ID, "side": DEFAULT_SIDE}
    )
    assert canary["admissible_as_full_core_e2e"] is False
    assert canary["CANARY_PATH_IS_PARALLEL_PRODUCTIVE_LIVE_AUTHORITY"] is False


def test_case6_offline_composition_still_halts_without_port_or_wire(monkeypatch) -> None:
    result, _ = _run(
        monkeypatch,
        _confirmed_replay_input(side="LONG"),
        attempt_construct_live_port=True,
        attempt_wire_send=True,
    )
    assert result.boundary is not None
    assert result.boundary.admission is not None
    assert result.boundary.admission.admitted is False
    assert "LIVE_ENABLED_FALSE" in result.boundary.admission.reason_codes
    assert result.boundary.live_execution_port_constructed is False
    assert result.wire_send_occurred is False
    assert result.boundary.canary_http_invoked is False
    assert result.boundary.halt_before_wire is True
    assert OWNER_ONE_SHOT_PERMIT_TOKEN == "OWNER_GO_FULL_CORE_LIVE_PATH_OFFLINE_V1"


def test_runbook_and_spec_bind_standing_seam_without_arming_or_wire() -> None:
    runbook = RUNBOOK.read_text(encoding="utf-8")
    spec = SPEC_PATH.read_text(encoding="utf-8")
    start = runbook.index("11.2.1.O FULL_CORE_LIVE_ENABLED_STANDING_ADMISSION_SEAM")
    section = runbook[
        start : runbook.index("11.2.1.P FULL_CORE_LIVE_ADMISSION_TO_PRE_WIRE_BOUNDARY", start)
    ]
    assert "LIVE_ENABLED_STANDING_ADMISSION_SEAM_IMPLEMENTED=true" in section
    assert "LIVE_ENABLED_DEFAULT=false" in section
    assert "LIVE_ENABLED_TRUE_IS_NOT_AUTOMATIC_ADMISSION=true" in section
    assert "LIVE_ENABLED_FALSE_REMAINS_FAIL_CLOSED=true" in section
    assert "LIVE_ENABLED_DOES_NOT_IMPLY_LIVE_ARMED=true" in section
    assert "LIVE_ENABLED_DOES_NOT_IMPLY_WIRE_SEND=true" in section
    assert "LIVE_ENABLED_DOES_NOT_IMPLY_PORT_CONSTRUCTION=true" in section
    assert "PRODUCTIVE_WIRE_SEND_REACHABLE=false" in section
    assert "EARLIEST_UNRESOLVED_FULL_CORE_DEPENDENCY=LIVE_ARMED" in section
    assert "OPEN_CONTRADICTION_NOT_NORMALIZED" in section
    assert "LIVE_ENABLED=false" in section
    assert "LIVE_ARMED=false" in section
    assert "WIRE_SEND_PERMITTED=false" in section
    assert "docs_token:" in spec
    assert "DOCS_TOKEN_FULL_CORE_LIVE_ENABLED_STANDING_ADMISSION_SEAM_V1" in spec
