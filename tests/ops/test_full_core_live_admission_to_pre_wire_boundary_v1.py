"""Full-Core LIVE_ARMED standing seam and pre-wire admission closure. Offline."""

from __future__ import annotations

from pathlib import Path

from src.ops.full_core_live_path_composition_root_v1.canary_isolation_v1 import (
    refuse_canary_plan_as_full_core_e2e_v1,
)
from src.ops.full_core_live_path_composition_root_v1.constants_v1 import (
    CAP_7_2_HOST_JOIN_TO_LIVE_EXECUTION_PORT,
    FULL_CORE_HOST_STANDING_PREDICATE_JOIN_IMPLEMENTED,
    LIVE_ARMED,
    LIVE_ARMED_DOES_NOT_IMPLY_PORT_CONSTRUCTION,
    LIVE_ARMED_DOES_NOT_IMPLY_RISK_ADMISSIBLE,
    LIVE_ARMED_DOES_NOT_IMPLY_WIRE_SEND,
    LIVE_ARMED_FALSE_REMAINS_FAIL_CLOSED,
    LIVE_ARMED_STANDING_ADMISSION_SEAM_IMPLEMENTED,
    LIVE_ARMED_TRUE_IS_NOT_AUTOMATIC_ADMISSION,
    LIVE_ENABLED,
    LIVE_EXECUTION_PORT_CONSTRUCTIBLE,
    LIVE_EXECUTION_PORT_CONSTRUCTION_ADMISSION_CONTRACT_IMPLEMENTED,
    OWNER_ONE_SHOT_PERMIT_TOKEN,
    PRODUCTIVE_WIRE_SEND_REACHABLE,
    WIRE_SEND_PERMITTED,
    WIRE_SEND_PERMITTED_FALSE_REMAINS_FAIL_CLOSED,
    WIRE_SEND_PERMITTED_STANDING_ADMISSION_SEAM_IMPLEMENTED,
    WIRE_SEND_PERMITTED_TRUE_IS_NOT_AUTOMATIC_SEND,
)
from src.ops.full_core_live_path_composition_root_v1.execution_admission_contract_v1 import (
    ADMISSION_CONTEXT_OFFLINE_FULL_CORE_PROOF,
    evaluate_execution_admission_v1,
)
from src.ops.full_core_live_path_composition_root_v1.live_admission_gap_dag_v1 import (
    CANONICAL_ORDER_HOST_JOIN_VS_LIVE_ARMED_VS_LIVE_EXECUTION_PORT,
    EARLIEST_UNRESOLVED_FULL_CORE_DEPENDENCY,
    LIVE_EXECUTION_PORT_CONSTRUCTION_FORBIDDEN,
    MAX_SAFE_REPO_INTERNAL_NEXT_SLICE,
    gap_node_v1,
    live_admission_gap_dag_v1,
)
from src.ops.full_core_live_path_composition_root_v1.live_execution_port_construction_admission_v1 import (
    CAP_11_1_CONSTRUCTION_FORBIDDEN_REASON,
    evaluate_live_execution_port_construction_admission_v1,
    prove_live_execution_port_not_constructible_v1,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.constants_v1 import (
    DEFAULT_INSTRUMENT_ID,
    DEFAULT_SIDE,
    LIVE_CANARY_MINIMUM_EXPOSURE_AUTHORIZED_DEFAULT,
)
from tests.ops.test_full_core_execution_admission_contract_v1 import _live_inputs
from tests.ops.test_full_core_live_enabled_standing_admission_seam_v1 import (
    _all_modelable_live_gates_true,
)
from tests.ops.test_full_core_live_path_composition_root_v1 import _run
from tests.trading.master_v2.test_master_v2_integrated_replay_safety_before_intent_restore_contract_v1 import (
    _confirmed_replay_input,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
RUNBOOK = REPO_ROOT / "docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md"
SPEC_PATH = REPO_ROOT / "docs/ops/specs/FULL_CORE_LIVE_ADMISSION_TO_PRE_WIRE_BOUNDARY_V1.md"

_ARMED_DENY = frozenset(
    {"LIVE_ARMED_FALSE", "STANDING_OR_INPUT_LIVE_ARMED", "STANDING_LIVE_ARMED_TRUE"}
)
_ENABLED_DENY = frozenset(
    {"LIVE_ENABLED_FALSE", "STANDING_OR_INPUT_LIVE_ENABLED", "STANDING_LIVE_ENABLED_TRUE"}
)


def test_standing_defaults_and_pre_wire_flags() -> None:
    assert LIVE_ENABLED is False
    assert LIVE_ARMED is False
    assert WIRE_SEND_PERMITTED is False
    assert LIVE_ARMED_STANDING_ADMISSION_SEAM_IMPLEMENTED is True
    assert LIVE_ARMED_TRUE_IS_NOT_AUTOMATIC_ADMISSION is True
    assert LIVE_ARMED_FALSE_REMAINS_FAIL_CLOSED is True
    assert LIVE_ARMED_DOES_NOT_IMPLY_RISK_ADMISSIBLE is True
    assert LIVE_ARMED_DOES_NOT_IMPLY_WIRE_SEND is True
    assert LIVE_ARMED_DOES_NOT_IMPLY_PORT_CONSTRUCTION is True
    assert WIRE_SEND_PERMITTED_STANDING_ADMISSION_SEAM_IMPLEMENTED is True
    assert WIRE_SEND_PERMITTED_TRUE_IS_NOT_AUTOMATIC_SEND is True
    assert WIRE_SEND_PERMITTED_FALSE_REMAINS_FAIL_CLOSED is True
    assert FULL_CORE_HOST_STANDING_PREDICATE_JOIN_IMPLEMENTED is True
    assert CAP_7_2_HOST_JOIN_TO_LIVE_EXECUTION_PORT is False
    assert LIVE_EXECUTION_PORT_CONSTRUCTION_ADMISSION_CONTRACT_IMPLEMENTED is True
    assert LIVE_EXECUTION_PORT_CONSTRUCTIBLE is False
    assert PRODUCTIVE_WIRE_SEND_REACHABLE is False
    assert LIVE_EXECUTION_PORT_CONSTRUCTION_FORBIDDEN is True
    armed = gap_node_v1("LIVE_ARMED")
    assert armed.implementation_status == "STANDING_ADMISSION_SEAM_IMPLEMENTED_DEFAULT_FALSE"
    assert armed.wiring_authorized is True
    assert armed.standing_live_gates_would_change is False
    send = gap_node_v1("WIRE_SEND_PERMITTED")
    assert send.implementation_status == "STANDING_ADMISSION_SEAM_IMPLEMENTED_DEFAULT_FALSE"
    assert EARLIEST_UNRESOLVED_FULL_CORE_DEPENDENCY == (
        "LIVE_VENUE_CAPITAL_NOT_ADMITTED_TO_STEP_29P"
    )
    assert MAX_SAFE_REPO_INTERNAL_NEXT_SLICE == (
        "NO_FURTHER_REPO_INTERNAL_SLICE_PRE_WIRE_BOUNDARY_REACHED"
    )
    assert CANONICAL_ORDER_HOST_JOIN_VS_LIVE_ARMED_VS_LIVE_EXECUTION_PORT == (
        "STANDING_GATES_BEFORE_CONSTRUCTION_CAP72_HOST_REMAINS_SIMULATED"
    )
    dag = live_admission_gap_dag_v1()
    assert dag["LIVE_ARMED"] is False
    assert dag["LIVE_ARMED_STANDING_ADMISSION_SEAM_IMPLEMENTED"] is True
    assert dag["PRODUCTIVE_WIRE_SEND_REACHABLE"] is False


def test_enabled_armed_matrix_false_false() -> None:
    decision = evaluate_execution_admission_v1(
        _live_inputs(live_enabled=False, live_armed=False, wire_send_permitted=False)
    )
    assert decision.admitted is False
    assert "LIVE_ENABLED_FALSE" in decision.reason_codes
    assert "LIVE_ARMED_FALSE" in decision.reason_codes
    assert "STANDING_OR_INPUT_LIVE_ARMED" not in decision.reason_codes


def test_enabled_armed_matrix_true_false() -> None:
    decision = evaluate_execution_admission_v1(
        _live_inputs(live_enabled=True, live_armed=False, wire_send_permitted=False)
    )
    assert decision.admitted is False
    assert not _ENABLED_DENY.intersection(decision.reason_codes)
    assert "LIVE_ARMED_FALSE" in decision.reason_codes


def test_enabled_armed_matrix_false_true() -> None:
    decision = evaluate_execution_admission_v1(
        _live_inputs(live_enabled=False, live_armed=True, wire_send_permitted=False)
    )
    assert decision.admitted is False
    assert "LIVE_ENABLED_FALSE" in decision.reason_codes
    assert not _ARMED_DENY.intersection(decision.reason_codes)


def test_enabled_armed_matrix_true_true_still_not_admitted() -> None:
    decision = evaluate_execution_admission_v1(
        _live_inputs(live_enabled=True, live_armed=True, wire_send_permitted=False)
    )
    assert decision.admitted is False
    assert not _ENABLED_DENY.intersection(decision.reason_codes)
    assert not _ARMED_DENY.intersection(decision.reason_codes)
    assert "WIRE_SEND_NOT_PERMITTED" in decision.reason_codes


def test_armed_true_does_not_imply_risk_port_or_wire() -> None:
    decision = evaluate_execution_admission_v1(_all_modelable_live_gates_true())
    assert decision.admitted is False
    assert "OBSERVED_CAPITAL_NOT_RISK_ADMISSIBLE" in decision.reason_codes
    assert "LIVE_VENUE_CAPITAL_NOT_ADMITTED_TO_STEP_29P" in decision.reason_codes
    construction = evaluate_live_execution_port_construction_admission_v1(
        admission=decision,
        live_enabled=True,
        live_armed=True,
        wire_send_permitted=True,
    )
    assert construction.constructible is False
    assert construction.constructed is False
    assert CAP_11_1_CONSTRUCTION_FORBIDDEN_REASON in construction.reason_codes
    assert PRODUCTIVE_WIRE_SEND_REACHABLE is False


def test_full_conjunction_still_halts_at_external_boundary() -> None:
    live = evaluate_execution_admission_v1(_all_modelable_live_gates_true())
    assert live.admitted is False
    assert "LIVE_VENUE_CAPITAL_NOT_ADMITTED_TO_STEP_29P" in live.reason_codes
    offline = evaluate_execution_admission_v1(
        _all_modelable_live_gates_true(admission_context=ADMISSION_CONTEXT_OFFLINE_FULL_CORE_PROOF)
    )
    assert offline.admitted is False
    assert "OFFLINE_FULL_CORE_PROOF_NOT_LIVE_ADMISSION" in offline.reason_codes


def test_construction_admission_never_constructs_with_productive_resources() -> None:
    proof = prove_live_execution_port_not_constructible_v1()
    assert proof["ok"] is True
    denied = evaluate_live_execution_port_construction_admission_v1(
        live_enabled=True,
        live_armed=True,
        wire_send_permitted=True,
        attempt_with_credentials=True,
        attempt_network_session=True,
    )
    assert denied.constructible is False
    assert denied.constructed is False
    assert denied.productive_resources_requested is True
    assert "PRODUCTIVE_CONSTRUCTION_RESOURCES_FORBIDDEN" in denied.reason_codes
    assert CAP_11_1_CONSTRUCTION_FORBIDDEN_REASON in denied.reason_codes


def test_host_composition_uses_admission_authority_and_does_not_construct(monkeypatch) -> None:
    result, _ = _run(
        monkeypatch,
        _confirmed_replay_input(side="LONG"),
        attempt_construct_live_port=True,
        attempt_wire_send=True,
    )
    assert result.intent is not None
    assert result.intent.live_enabled is False
    assert result.intent.live_armed is False
    assert result.intent.wire_send_permitted is False
    assert result.intent.execution_eligible is False
    assert result.intent.submission_authorized is False
    assert result.boundary is not None
    assert result.boundary.admission is not None
    assert result.boundary.admission.admitted is False
    assert result.boundary.live_execution_port_constructed is False
    assert result.wire_send_occurred is False
    assert result.boundary.canary_http_invoked is False
    assert result.boundary.halt_before_wire is True
    assert "STANDING_LIVE_GATE_TRUE" not in result.reason_codes
    assert CAP_11_1_CONSTRUCTION_FORBIDDEN_REASON in result.reason_codes
    assert OWNER_ONE_SHOT_PERMIT_TOKEN == "OWNER_GO_FULL_CORE_LIVE_PATH_OFFLINE_V1"


def test_canary_cannot_bypass_full_core_armed_seam() -> None:
    decision = evaluate_execution_admission_v1(_live_inputs(live_armed=True, live_enabled=True))
    assert decision.admitted is False
    assert LIVE_ARMED is False
    assert LIVE_CANARY_MINIMUM_EXPOSURE_AUTHORIZED_DEFAULT is False
    canary = refuse_canary_plan_as_full_core_e2e_v1(
        {"instrument_id": DEFAULT_INSTRUMENT_ID, "side": DEFAULT_SIDE}
    )
    assert canary["admissible_as_full_core_e2e"] is False
    assert canary["CANARY_PATH_IS_PARALLEL_PRODUCTIVE_LIVE_AUTHORITY"] is False


def test_runbook_and_spec_bind_pre_wire_boundary_without_arming_or_wire() -> None:
    runbook = RUNBOOK.read_text(encoding="utf-8")
    spec = SPEC_PATH.read_text(encoding="utf-8")
    start = runbook.index("11.2.1.P FULL_CORE_LIVE_ADMISSION_TO_PRE_WIRE_BOUNDARY")
    section = runbook[start : runbook.index("## 11.3 Autonomy state model", start)]
    assert "LIVE_ARMED_STANDING_ADMISSION_SEAM_IMPLEMENTED=true" in section
    assert "LIVE_ARMED_DEFAULT=false" in section
    assert "LIVE_ARMED_TRUE_IS_NOT_AUTOMATIC_ADMISSION=true" in section
    assert "WIRE_SEND_PERMITTED_STANDING_ADMISSION_SEAM_IMPLEMENTED=true" in section
    assert "FULL_CORE_HOST_STANDING_PREDICATE_JOIN_IMPLEMENTED=true" in section
    assert "CAP_7_2_HOST_JOIN_TO_LIVE_EXECUTION_PORT=false" in section
    assert "LIVE_EXECUTION_PORT_CONSTRUCTION_ADMISSION_CONTRACT_IMPLEMENTED=true" in section
    assert "LIVE_EXECUTION_PORT_CONSTRUCTIBLE=false" in section
    assert "PRODUCTIVE_WIRE_SEND_REACHABLE=false" in section
    assert "IMPLEMENTED=true" in section
    assert "DEFAULT=false" in section
    assert (
        "STRUCTURALLY_REACHABLE=false" in section
        or "PRODUCTIVE_WIRE_SEND_REACHABLE=false" in section
    )
    assert "RUNTIME_SATISFIED=false" in section
    assert "AUTHORIZED=false" in section
    assert "EXECUTED=false" in section
    assert (
        "EARLIEST_UNRESOLVED_FULL_CORE_DEPENDENCY=LIVE_VENUE_CAPITAL_NOT_ADMITTED_TO_STEP_29P"
        in section
    )
    assert "LIVE_ENABLED=false" in section
    assert "LIVE_ARMED=false" in section
    assert "WIRE_SEND_PERMITTED=false" in section
    assert "docs_token:" in spec
    assert "DOCS_TOKEN_FULL_CORE_LIVE_ADMISSION_TO_PRE_WIRE_BOUNDARY_V1" in spec
