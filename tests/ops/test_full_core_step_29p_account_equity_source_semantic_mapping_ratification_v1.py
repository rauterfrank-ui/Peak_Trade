"""STEP-29P equity source-semantic mapping ratification. No canonical mapping."""

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
    ADJUDICATION_RESULT,
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
    SOURCE_CANDIDATE_COUNT,
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
    REPO_ROOT
    / "docs/ops/specs/FULL_CORE_STEP_29P_ACCOUNT_EQUITY_SOURCE_SEMANTIC_MAPPING_RATIFICATION_V1.md"
)
R_SPEC_PATH = (
    REPO_ROOT / "docs/ops/specs/FULL_CORE_STEP_29P_ACCOUNT_EQUITY_MAPPING_OWNER_RATIFICATION_V1.md"
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
_CANDIDATE_IDS = (
    "C01_Q_GET_PACK_DETAILS_AVAILEQ",
    "C02_FORBIDDEN_RAW_VENUE_EQ_FIELDS",
    "C03_CAPITAL_ADMISSION_ENVELOPE",
    "C04_CRS_ACCOUNT_EQUITY_CONSUMER",
    "C05_OFFLINE_REPLAY_DEFAULT_10000",
    "C06_INJECTED_RUNNING_ACCOUNT_EQUITY",
    "C07_FUNDING_ACCOUNT_BALANCE_OBSERVATION",
    "C08_TREASURY_OBSERVED_OR_RECONCILED_CAPITAL",
    "C09_CAP11_3_FIXTURE_PRIVATE_ACCOUNT_STATE",
    "C10_LEDGER_SNAPSHOT_EQUITY_BY_CCY",
    "C11_CAP31_PRODUCTIVE_FUTURES_ACCOUNTING",
    "C12_S1114_LIVE_ACCOUNTING_RECONSTRUCTED",
    "C13_BACKTEST_STATE_FILE_ACCOUNT_EQUITY",
    "C14_START_BALANCE",
    "C15_LIVE_ACCOUNT_BOUND_IDENTITY",
    "C16_RESTART_RECONSTRUCTION_ACCOUNTING",
)
_OPEN_SEMANTIC_REQUIREMENTS = (
    "ACCOUNT_MODE=OPEN",
    "REALIZED_UNREALIZED_TREATMENT=OPEN",
    "OPEN_POSITION_TREATMENT=OPEN",
    "PENDING_ORDER_RESERVATIONS=OPEN",
    "LIABILITIES_BORROWINGS=OPEN",
    "FEES=OPEN",
    "HAIRCUTS_RESERVE_DEPLETION=FROZEN_PENDING_OWNER_POLICY",
    "RESTART_RECONCILIATION_FOR_THIS_DIMENSION=OPEN",
    "MULTI_CURRENCY_CONVERSION=OPEN",
)


def test_adjudication_no_canonically_valid_mapping() -> None:
    assert ADJUDICATION_RESULT == "NO_CANONICALLY_VALID_MAPPING_AVAILABLE"
    assert SOURCE_CANDIDATE_COUNT == 16
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
        "NO_CANONICALLY_VALID_ACCOUNT_EQUITY_SOURCE_MAPPING"
    )
    assert MAX_SAFE_REPO_INTERNAL_NEXT_SLICE == (
        "NO_FURTHER_REPO_INTERNAL_SLICE_NO_CANONICALLY_VALID_EQUITY_MAPPING"
    )
    assert FRESH_EXTERNAL_EVIDENCE_REQUIRED_FOR_NEXT_SLICE is False
    assert NEXT_STEP_REQUIRES_OWNER_GO is True
    dag = live_admission_gap_dag_v1()
    assert dag["ADJUDICATION_RESULT"] == "NO_CANONICALLY_VALID_MAPPING_AVAILABLE"
    assert dag["SOURCE_CANDIDATE_COUNT"] == 16
    assert dag["MAPPING_PROVEN"] is False
    assert dag["IMPLEMENTATION_OF_VALUE_BINDING"] is False
    assert dag["ACCOUNT_EQUITY_AUTHORITY_OWNER"] == "UNRESOLVED"
    assert dag["EARLIEST_UNRESOLVED_FULL_CORE_DEPENDENCY"] == (
        EARLIEST_UNRESOLVED_FULL_CORE_DEPENDENCY
    )


def test_census_candidates_are_existing_and_rejected() -> None:
    runbook = RUNBOOK.read_text(encoding="utf-8")
    s_start = runbook.index(
        "11.2.1.S FULL_CORE_STEP_29P_ACCOUNT_EQUITY_SOURCE_SEMANTIC_MAPPING_RATIFICATION"
    )
    s_section = runbook[
        s_start : runbook.index(
            "11.2.1.T FULL_CORE_RUNNING_EQUITY_POLICY_SEMANTICS_RATIFICATION", s_start
        )
    ]
    assert SOURCE_CANDIDATE_COUNT == len(_CANDIDATE_IDS)
    for candidate_id in _CANDIDATE_IDS:
        assert candidate_id in s_section, candidate_id
    assert "ADJUDICATION_RESULT=NO_CANONICALLY_VALID_MAPPING_AVAILABLE" in s_section
    assert "EXACTLY_ONE_CANONICAL_MAPPING_PROVEN" in s_section
    assert "MULTIPLE_PLAUSIBLE_BUT_OWNER_RATIFICATION_REQUIRED" in s_section
    assert "No best-effort mapping is selected." in s_section
    assert "GOVERNED_PRODUCTIVE_ACCOUNT_EQUITY_AUTHORITY_PRODUCER" in s_section
    assert "productive_producer_present=false" in s_section
    for requirement in _OPEN_SEMANTIC_REQUIREMENTS:
        assert requirement in s_section, requirement
    assert "SEMANTIC_REQUIREMENTS_COMPLETE=false" in s_section


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


def test_runbook_s_consumes_go_without_rewriting_r() -> None:
    runbook = RUNBOOK.read_text(encoding="utf-8")
    spec = SPEC_PATH.read_text(encoding="utf-8")
    r_spec = R_SPEC_PATH.read_text(encoding="utf-8")
    r_start = runbook.index("11.2.1.R FULL_CORE_STEP_29P_ACCOUNT_EQUITY_MAPPING_OWNER_RATIFICATION")
    s_start = runbook.index(
        "11.2.1.S FULL_CORE_STEP_29P_ACCOUNT_EQUITY_SOURCE_SEMANTIC_MAPPING_RATIFICATION"
    )
    r_section = runbook[r_start:s_start]
    s_section = runbook[
        s_start : runbook.index(
            "11.2.1.T FULL_CORE_RUNNING_EQUITY_POLICY_SEMANTICS_RATIFICATION", s_start
        )
    ]
    assert (
        "OWNER_GO=FULL_CORE_STEP_29P_ACCOUNT_EQUITY_SOURCE_SEMANTIC_MAPPING_RATIFICATION_V1"
        in s_section
    )
    assert "OWNER_GO_STATUS=CONSUMED" in s_section
    assert "ADJUDICATION_RESULT=NO_CANONICALLY_VALID_MAPPING_AVAILABLE" in s_section
    assert "MAPPING_PROVEN=false" in s_section
    assert "IMPLEMENTATION_OF_VALUE_BINDING=false" in s_section
    assert "RUNTIME_VALUE_BINDING_IMPLEMENTED=false" in s_section
    assert "ACCOUNT_EQUITY_AUTHORITY_OWNER=UNRESOLVED" in s_section
    assert "RUNNING_EQUITY_SOURCE_OBJECT=NONE" in s_section
    assert "STEP_29P_RISK_ADMISSIBLE=false" in s_section
    assert "LIVE_ACCOUNT_BOUND_JOIN_EXECUTED_THIS_SLICE=false" in s_section
    assert (
        "EARLIEST_UNRESOLVED_FULL_CORE_DEPENDENCY="
        "NO_CANONICALLY_VALID_ACCOUNT_EQUITY_SOURCE_MAPPING" in s_section
    )
    assert "LIVE_ENABLED=false" in s_section
    assert "LIVE_ARMED=false" in s_section
    assert "WIRE_SEND_PERMITTED=false" in s_section
    assert "CONSTRUCT_LIVE_EXECUTION_PORT_V1=FORBIDDEN_IN_CAP_11_1" in s_section
    assert "CAP_11_1_CONSTRUCTION_POLICY_LIFT_AUTHORIZED=false" in s_section
    assert "CAP72_PRODUCTIVE_PORT=SimulatedExecutionPortV1" in s_section
    assert (
        "EARLIEST_UNRESOLVED_FULL_CORE_DEPENDENCY="
        "ACCOUNT_EQUITY_SOURCE_SEMANTIC_MAPPING_OWNER_RATIFICATION_REQUIRED" in r_section
    )
    assert "THIS_SLICE=11.2.1.R.FULL_CORE_STEP_29P_ACCOUNT_EQUITY_MAPPING_OWNER_RATIFICATION" in (
        r_section
    )
    assert "THIS_SLICE=11.2.1.S" not in r_section
    assert (
        "DOCS_TOKEN_FULL_CORE_STEP_29P_ACCOUNT_EQUITY_SOURCE_SEMANTIC_MAPPING_RATIFICATION_V1"
        in spec
    )
    assert "ADJUDICATION_RESULT=NO_CANONICALLY_VALID_MAPPING_AVAILABLE" in spec
    assert "IMPLEMENTATION_OF_VALUE_BINDING=false" in spec
    assert (
        "EARLIEST_UNRESOLVED_FULL_CORE_DEPENDENCY="
        "ACCOUNT_EQUITY_SOURCE_SEMANTIC_MAPPING_OWNER_RATIFICATION_REQUIRED" in r_spec
    )
    assert "THIS_SLICE=11.2.1.S" not in r_section
