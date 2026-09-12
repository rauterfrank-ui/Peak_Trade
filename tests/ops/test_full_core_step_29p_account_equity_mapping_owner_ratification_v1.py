"""STEP-29P equity-mapping Owner ratification. Mapping unproven. No value binding."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from src.ops.capability_11_1_execution_domain_and_order_lifecycle_contracts_v1.execution_ports_v1 import (
    ExecutionPortConstructionForbiddenError,
    bind_simulated_execution_port_v1,
    construct_live_execution_port_v1,
)
from src.ops.full_core_live_path_composition_root_v1.constants_v1 import (
    ACCOUNT_EQUITY_AUTHORITY_OWNER,
    ACCOUNT_EQUITY_AUTHORITY_OWNER_CANDIDATE,
    CAP_7_2_HOST_JOIN_TO_LIVE_EXECUTION_PORT,
    IMPLEMENTATION_OF_VALUE_BINDING,
    LIVE_ACCOUNT_BOUND_JOIN_EXECUTED_THIS_SLICE,
    LIVE_ARMED,
    LIVE_ENABLED,
    MAPPING_PROVEN,
    RISK_ADMISSIBLE_DOES_NOT_IMPLY_LIVE_ARMED,
    RISK_ADMISSIBLE_DOES_NOT_IMPLY_LIVE_ENABLED,
    RISK_ADMISSIBLE_DOES_NOT_IMPLY_PORT_CONSTRUCTION,
    RISK_ADMISSIBLE_DOES_NOT_IMPLY_WIRE_SEND,
    RISK_SIZING_OWNER,
    RUNNING_EQUITY_SOURCE_FIELD_OR_DERIVATION,
    RUNNING_EQUITY_SOURCE_OBJECT,
    RUNNING_EQUITY_SOURCE_SEMANTICS,
    SELECTION_OWNER,
    WIRE_SEND_PERMITTED,
)
from src.ops.full_core_live_path_composition_root_v1.live_admission_gap_dag_v1 import (
    EARLIEST_UNRESOLVED_FULL_CORE_DEPENDENCY,
    FRESH_EXTERNAL_EVIDENCE_REQUIRED_FOR_NEXT_SLICE,
    MAX_SAFE_REPO_INTERNAL_NEXT_SLICE,
    NEXT_STEP_REQUIRES_OWNER_GO,
    live_admission_gap_dag_v1,
)
from src.ops.full_core_live_path_composition_root_v1.step_29p_capital_risk_admissibility_v1 import (
    evaluate_step_29p_capital_risk_admissibility_v1,
)
from src.ops.single_future_stateful_no_order_runtime_activation_v1.simulated_execution_port_v1 import (
    SimulatedExecutionPortV1,
)
from tests.ops.test_full_core_step_29p_risk_admissibility_pre_construction_v1 import (
    _capital,
    _complete_claim,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
RUNBOOK = REPO_ROOT / "docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md"
SPEC_PATH = (
    REPO_ROOT / "docs/ops/specs/FULL_CORE_STEP_29P_ACCOUNT_EQUITY_MAPPING_OWNER_RATIFICATION_V1.md"
)
Q_SPEC_PATH = (
    REPO_ROOT / "docs/ops/specs/FULL_CORE_STEP_29P_RISK_ADMISSIBILITY_PRE_CONSTRUCTION_V1.md"
)
GET_PACK_SUMMARY = (
    REPO_ROOT
    / "evidence/ops/full_core_step_29p_fresh_venue_evidence_v1/20260905T212436Z/SUMMARY.json"
)
PACKAGE_DIR = REPO_ROOT / "src/ops/full_core_live_path_composition_root_v1"
_FORBIDDEN_AUTHORITY_LEAK_TOKENS = (
    "src.learning",
    "src.ranking",
    "economic_md",
    "observe_after_producer_v0",
)
_FORBIDDEN_EQUITY_FIELDS = (
    "details.availEq",
    "availEq",
    "totalEq",
    "eq",
    "adjEq",
    "availBal",
    "cashBal",
    "details.totalEq",
)


def test_mapping_unproven_and_value_binding_not_implemented() -> None:
    assert ACCOUNT_EQUITY_AUTHORITY_OWNER == "UNRESOLVED"
    assert ACCOUNT_EQUITY_AUTHORITY_OWNER_CANDIDATE == "UNRESOLVED"
    assert RUNNING_EQUITY_SOURCE_OBJECT == "NONE"
    assert RUNNING_EQUITY_SOURCE_FIELD_OR_DERIVATION == "NONE"
    assert RUNNING_EQUITY_SOURCE_SEMANTICS == "UNBOUND"
    assert MAPPING_PROVEN is False
    assert IMPLEMENTATION_OF_VALUE_BINDING is False
    assert LIVE_ACCOUNT_BOUND_JOIN_EXECUTED_THIS_SLICE is False
    assert RISK_SIZING_OWNER == "STEP_29P"
    assert LIVE_ENABLED is False
    assert LIVE_ARMED is False
    assert WIRE_SEND_PERMITTED is False
    assert RISK_ADMISSIBLE_DOES_NOT_IMPLY_LIVE_ENABLED is True
    assert RISK_ADMISSIBLE_DOES_NOT_IMPLY_LIVE_ARMED is True
    assert RISK_ADMISSIBLE_DOES_NOT_IMPLY_WIRE_SEND is True
    assert RISK_ADMISSIBLE_DOES_NOT_IMPLY_PORT_CONSTRUCTION is True
    assert EARLIEST_UNRESOLVED_FULL_CORE_DEPENDENCY == (
        "ACCOUNT_EQUITY_SOURCE_SEMANTIC_MAPPING_OWNER_RATIFICATION_REQUIRED"
    )
    assert MAX_SAFE_REPO_INTERNAL_NEXT_SLICE == (
        "NO_FURTHER_REPO_INTERNAL_SLICE_EQUITY_SOURCE_MAPPING_OWNER_RATIFICATION_REQUIRED"
    )
    assert FRESH_EXTERNAL_EVIDENCE_REQUIRED_FOR_NEXT_SLICE is False
    assert NEXT_STEP_REQUIRES_OWNER_GO is True
    dag = live_admission_gap_dag_v1()
    assert dag["MAPPING_PROVEN"] is False
    assert dag["IMPLEMENTATION_OF_VALUE_BINDING"] is False
    assert dag["ACCOUNT_EQUITY_AUTHORITY_OWNER"] == "UNRESOLVED"
    assert dag["EARLIEST_UNRESOLVED_FULL_CORE_DEPENDENCY"] == (
        EARLIEST_UNRESOLVED_FULL_CORE_DEPENDENCY
    )


def test_forbidden_raw_venue_fields_remain_hard_deny() -> None:
    capital = _capital()
    for field in _FORBIDDEN_EQUITY_FIELDS:
        result = evaluate_step_29p_capital_risk_admissibility_v1(
            capital=capital,
            claim=_complete_claim(typed_account_equity_source_field=field),
        )
        assert result.risk_admissible is False, field
        assert "CAPITAL_ADMISSION_OPTIMISTIC_FIELD_FALLBACK" in result.reason_codes
        assert result.equity_dimension_bound is False
        assert result.live_enabled is False
        assert result.live_armed is False
        assert result.wire_send_permitted is False


def test_injected_and_offline_equity_are_not_live_capital_authority() -> None:
    capital = _capital()
    injected = evaluate_step_29p_capital_risk_admissibility_v1(
        capital=capital, claim=_complete_claim()
    )
    assert injected.risk_admissible is True
    assert injected.live_enabled is False
    assert injected.live_armed is False
    assert injected.wire_send_permitted is False
    assert injected.port_constructed is False
    assert MAPPING_PROVEN is False
    assert IMPLEMENTATION_OF_VALUE_BINDING is False
    assert LIVE_ENABLED is False
    assert LIVE_ARMED is False
    assert WIRE_SEND_PERMITTED is False
    adapter = (
        REPO_ROOT / "src/trading/master_v2/capital_risk_sizing_offline_replay_binding_adapter_v0.py"
    ).read_text(encoding="utf-8")
    assert '_DEFAULT_ACCOUNT_EQUITY = Decimal("10000")' in adapter
    assert RUNNING_EQUITY_SOURCE_OBJECT != "OFFLINE_ALGEBRA"
    assert RUNNING_EQUITY_SOURCE_SEMANTICS != "LIVE_CAPITAL_AUTHORITY"


def test_existing_get_pack_does_not_become_risk_admissible() -> None:
    payload = json.loads(GET_PACK_SUMMARY.read_text(encoding="utf-8"))
    assert payload["STEP_29P_RISK_ADMISSIBLE"] is False
    assert payload["PERSIST_CLASSES"]["STEP_29P_RISK_ADMISSIBLE"] is False
    assert payload["PERSIST_CLASSES"]["PORT_CONSTRUCTED"] is False
    missing = set(payload["MISSING_REQUIRED_EVIDENCE"])
    assert "STEP_29P_EQUITY_DIMENSION_UNBOUND" in missing
    assert "STEP_29P_TYPED_ACCOUNT_EQUITY_MISSING" in missing


def test_live_account_bound_join_not_executed_and_does_not_mint_equity() -> None:
    assert LIVE_ACCOUNT_BOUND_JOIN_EXECUTED_THIS_SLICE is False
    producer = (
        REPO_ROOT / "src/ops/full_core_step_29p_fresh_venue_evidence_v1/execute_v1.py"
    ).read_text(encoding="utf-8")
    assert "live_account_bound_status=LiveAccountBoundStatusV1.MISSING.value" in producer
    assert 'equity_dimension=""' in producer
    assert 'typed_account_equity_raw=""' in producer


def test_authority_firewall_learning_ranking_and_cap23() -> None:
    assert SELECTION_OWNER == "CAPABILITY_2_3_SINGLE_SELECTED_FUTURE_POLICY_V1"
    assert RISK_SIZING_OWNER == "STEP_29P"
    leaks: list[str] = []
    for path in sorted(PACKAGE_DIR.glob("*.py")):
        text = path.read_text(encoding="utf-8")
        for token in _FORBIDDEN_AUTHORITY_LEAK_TOKENS:
            if token in text:
                leaks.append(f"{path.name}:{token}")
    assert leaks == []


def test_risk_admissible_does_not_construct_or_arm() -> None:
    with pytest.raises(ExecutionPortConstructionForbiddenError) as raised:
        construct_live_execution_port_v1()
    assert "LIVE_EXECUTION_PORT_CONSTRUCTION_FORBIDDEN_IN_CAPABILITY_11_1" in str(raised.value)
    port = bind_simulated_execution_port_v1()
    assert isinstance(port, SimulatedExecutionPortV1)
    assert CAP_7_2_HOST_JOIN_TO_LIVE_EXECUTION_PORT is False
    assert LIVE_ENABLED is False
    assert LIVE_ARMED is False
    assert WIRE_SEND_PERMITTED is False


def test_runbook_r_consumes_go_without_rewriting_q() -> None:
    runbook = RUNBOOK.read_text(encoding="utf-8")
    spec = SPEC_PATH.read_text(encoding="utf-8")
    q_spec = Q_SPEC_PATH.read_text(encoding="utf-8")
    q_start = runbook.index("11.2.1.Q FULL_CORE_STEP_29P_RISK_ADMISSIBILITY_PRE_CONSTRUCTION")
    r_start = runbook.index("11.2.1.R FULL_CORE_STEP_29P_ACCOUNT_EQUITY_MAPPING_OWNER_RATIFICATION")
    q_section = runbook[q_start:r_start]
    r_section = runbook[r_start : runbook.index("## 11.3 Autonomy state model", r_start)]
    assert "OWNER_GO=FULL_CORE_STEP_29P_ACCOUNT_EQUITY_AUTHORITY_BINDING_V1" in r_section
    assert "OWNER_GO_STATUS=CONSUMED" in r_section
    assert "MAPPING_PROVEN=false" in r_section
    assert "IMPLEMENTATION_OF_VALUE_BINDING=false" in r_section
    assert "ACCOUNT_EQUITY_AUTHORITY_OWNER=UNRESOLVED" in r_section
    assert "RUNNING_EQUITY_SOURCE_OBJECT=NONE" in r_section
    assert "STEP_29P_RISK_ADMISSIBLE=false" in r_section
    assert "LIVE_ACCOUNT_BOUND_JOIN_EXECUTED_THIS_SLICE=false" in r_section
    assert (
        "EARLIEST_UNRESOLVED_FULL_CORE_DEPENDENCY="
        "ACCOUNT_EQUITY_SOURCE_SEMANTIC_MAPPING_OWNER_RATIFICATION_REQUIRED" in r_section
    )
    assert "LIVE_ENABLED=false" in r_section
    assert "LIVE_ARMED=false" in r_section
    assert "WIRE_SEND_PERMITTED=false" in r_section
    assert "CONSTRUCT_LIVE_EXECUTION_PORT_V1=FORBIDDEN_IN_CAP_11_1" in r_section
    assert "CAP_11_1_CONSTRUCTION_POLICY_LIFT_AUTHORIZED=false" in r_section
    assert (
        "EARLIEST_UNRESOLVED_FULL_CORE_DEPENDENCY=STEP_29P_EQUITY_DIMENSION_BINDING_MISSING"
        in q_section
    )
    assert "THIS_SLICE=11.2.1.Q.FULL_CORE_STEP_29P_RISK_ADMISSIBILITY_PRE_CONSTRUCTION" in q_section
    assert "DOCS_TOKEN_FULL_CORE_STEP_29P_ACCOUNT_EQUITY_MAPPING_OWNER_RATIFICATION_V1" in spec
    assert "MAPPING_PROVEN=false" in spec
    assert "IMPLEMENTATION_OF_VALUE_BINDING=false" in spec
    assert (
        "EARLIEST_UNRESOLVED_FULL_CORE_DEPENDENCY=STEP_29P_EQUITY_DIMENSION_BINDING_MISSING"
        in q_spec
    )
    assert "THIS_SLICE=11.2.1.R" not in q_section
