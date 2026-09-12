"""Running-equity authority architecture ratification. No source. No producer."""

from __future__ import annotations

from pathlib import Path

import pytest

from src.ops.capability_11_1_execution_domain_and_order_lifecycle_contracts_v1.execution_ports_v1 import (
    ExecutionPortConstructionForbiddenError,
    bind_simulated_execution_port_v1,
    construct_live_execution_port_v1,
)
from src.ops.full_core_live_path_composition_root_v1.constants_v1 import (
    ACCOUNT_EQUITY_AUTHORITY_OWNER,
    ADJUDICATION_RESULT,
    ARCHITECTURE_RATIFIED,
    C01_C16_REMAIN_REJECTED,
    FUTURE_ACCOUNT_EQUITY_AUTHORITY_OWNER_CLASS,
    FUTURE_GOVERNED_SOURCE_OBJECT_CLASS,
    FUTURE_PRODUCER_CLASS,
    GOVERNED_PRODUCER_CREATED,
    GOVERNED_PRODUCTIVE_SOURCE_PRESENT,
    IMPLEMENTATION_OF_VALUE_BINDING,
    LIVE_ARMED,
    LIVE_ENABLED,
    LIVE_ACCOUNT_BOUND_IDENTITY_IS_NOT_CAPITAL_AUTHORITY,
    LIVE_ACCOUNT_BOUND_JOIN_EXECUTED_THIS_SLICE,
    LIVE_ACCOUNT_BOUND_JOIN_PRESENT,
    MAPPING_PROVEN,
    OBSERVATION_IS_NOT_AUTHORITY,
    RAW_VENUE_FIELD_AUTHORITY_FORBIDDEN,
    RUNNING_EQUITY_SOURCE_OBJECT,
    RUNTIME_VALUE_BINDING_PRESENT,
    SAMPLE_PROVENANCE_REQUIRED_FIELDS,
    SEMANTIC_REQUIREMENTS_COMPLETE,
    SOURCE_SELECTED,
    STEP_29P_IS_NOT_EQUITY_AUTHORITY_OWNER,
    WIRE_SEND_PERMITTED,
)
from src.ops.full_core_live_path_composition_root_v1.live_admission_gap_dag_v1 import (
    EARLIEST_UNRESOLVED_FULL_CORE_DEPENDENCY,
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
    REPO_ROOT / "docs/ops/specs/FULL_CORE_RUNNING_EQUITY_AUTHORITY_ARCHITECTURE_RATIFICATION_V1.md"
)
S_HEADING = "11.2.1.S FULL_CORE_STEP_29P_ACCOUNT_EQUITY_SOURCE_SEMANTIC_MAPPING_RATIFICATION"
T_HEADING = "11.2.1.T FULL_CORE_RUNNING_EQUITY_POLICY_SEMANTICS_RATIFICATION"
U_HEADING = "11.2.1.U FULL_CORE_RUNNING_EQUITY_AUTHORITY_ARCHITECTURE_RATIFICATION"
_FORBIDDEN_EQUITY_FIELDS = (
    "details.availEq",
    "availEq",
    "totalEq",
    "eq",
    "adjEq",
    "availBal",
    "cashBal",
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
_REQUIRED_PROVENANCE = (
    "dimension_id",
    "bound_account_identity",
    "bound_venue_identity",
    "bound_td_mode",
    "settlement_currency",
    "value",
    "value_semantics",
    "producer_identity",
    "authority_contract_ref",
    "source_revision_or_digest",
    "input_set_digest",
    "decision_epoch",
    "observed_at/as_of",
    "freshness_max_age",
    "freshness_policy_status",
    "restart_reconciliation_status",
    "component_completeness",
    "component_provenance",
    "inclusion_vector",
    "component_term_vector",
    "double_count_guards",
    "currency_conversion_status",
    "witness_reconciliation_status",
    "policy_version",
    "semantic_digest",
    "sample_id",
    "observation_vs_authority_class",
)


def _u_section() -> str:
    runbook = RUNBOOK.read_text(encoding="utf-8")
    u_start = runbook.index(U_HEADING)
    return runbook[u_start : runbook.index("## 11.3 Autonomy state model", u_start)]


def test_architecture_classes_ratified_without_runtime_assignment() -> None:
    assert ARCHITECTURE_RATIFIED is True
    assert FUTURE_ACCOUNT_EQUITY_AUTHORITY_OWNER_CLASS == (
        "GOVERNED_PRODUCTIVE_ACCOUNT_EQUITY_AUTHORITY_PRODUCER"
    )
    assert FUTURE_GOVERNED_SOURCE_OBJECT_CLASS == "GOVERNED_RUNNING_ACCOUNT_EQUITY_SAMPLE_V1"
    assert FUTURE_PRODUCER_CLASS == ("COMPOSITIONAL_RECONSTRUCTION_WITH_WITNESS_RECONCILIATION_V1")
    assert ACCOUNT_EQUITY_AUTHORITY_OWNER == "UNRESOLVED"
    assert RUNNING_EQUITY_SOURCE_OBJECT == "NONE"
    assert SOURCE_SELECTED is False
    assert GOVERNED_PRODUCTIVE_SOURCE_PRESENT is False
    assert GOVERNED_PRODUCER_CREATED is False
    dag = live_admission_gap_dag_v1()
    assert dag["ARCHITECTURE_RATIFIED"] is True
    assert dag["FUTURE_ACCOUNT_EQUITY_AUTHORITY_OWNER_CLASS"] == (
        FUTURE_ACCOUNT_EQUITY_AUTHORITY_OWNER_CLASS
    )
    assert dag["ACCOUNT_EQUITY_AUTHORITY_OWNER"] == "UNRESOLVED"
    assert dag["SOURCE_SELECTED"] is False


def test_firewall_observation_identity_and_consumer_remain_separated() -> None:
    assert OBSERVATION_IS_NOT_AUTHORITY is True
    assert RAW_VENUE_FIELD_AUTHORITY_FORBIDDEN is True
    assert STEP_29P_IS_NOT_EQUITY_AUTHORITY_OWNER is True
    assert LIVE_ACCOUNT_BOUND_IDENTITY_IS_NOT_CAPITAL_AUTHORITY is True
    assert C01_C16_REMAIN_REJECTED is True
    assert ADJUDICATION_RESULT == "NO_CANONICALLY_VALID_MAPPING_AVAILABLE"
    assert MAPPING_PROVEN is False
    assert IMPLEMENTATION_OF_VALUE_BINDING is False
    assert RUNTIME_VALUE_BINDING_PRESENT is False
    assert LIVE_ACCOUNT_BOUND_JOIN_PRESENT is False
    assert LIVE_ACCOUNT_BOUND_JOIN_EXECUTED_THIS_SLICE is False
    assert EARLIEST_UNRESOLVED_FULL_CORE_DEPENDENCY == (
        "NO_CANONICALLY_VALID_ACCOUNT_EQUITY_SOURCE_MAPPING"
    )
    dag = live_admission_gap_dag_v1()
    assert dag["OBSERVATION_IS_NOT_AUTHORITY"] is True
    assert dag["RAW_VENUE_FIELD_AUTHORITY_FORBIDDEN"] is True
    assert dag["STEP_29P_IS_NOT_EQUITY_AUTHORITY_OWNER"] is True
    assert dag["LIVE_ACCOUNT_BOUND_IDENTITY_IS_NOT_CAPITAL_AUTHORITY"] is True
    assert dag["LIVE_ACCOUNT_BOUND_JOIN_PRESENT"] is False
    assert dag["MAPPING_PROVEN"] is False
    assert dag["EARLIEST_UNRESOLVED_FULL_CORE_DEPENDENCY"] == (
        EARLIEST_UNRESOLVED_FULL_CORE_DEPENDENCY
    )


def test_c01_c16_remain_rejected_and_forbidden_fields_deny() -> None:
    runbook = RUNBOOK.read_text(encoding="utf-8")
    s_start = runbook.index(S_HEADING)
    t_start = runbook.index(T_HEADING)
    s_section = runbook[s_start:t_start]
    for candidate_id in _CANDIDATE_IDS:
        assert candidate_id in s_section, candidate_id
    assert "ADJUDICATION_RESULT=NO_CANONICALLY_VALID_MAPPING_AVAILABLE" in s_section
    assert "C01_C16_REMAIN_REJECTED=true" in _u_section()
    capital = _capital()
    for field in _FORBIDDEN_EQUITY_FIELDS:
        result = evaluate_step_29p_capital_risk_admissibility_v1(
            capital=capital,
            claim=_complete_claim(typed_account_equity_source_field=field),
        )
        assert result.risk_admissible is False


def test_step_29p_risk_admissible_and_live_gates_remain_false() -> None:
    u_section = _u_section()
    assert "STEP_29P_RISK_ADMISSIBLE=false" in u_section
    assert LIVE_ENABLED is False
    assert LIVE_ARMED is False
    assert WIRE_SEND_PERMITTED is False


def test_cap11_1_and_cap72_unchanged() -> None:
    with pytest.raises(ExecutionPortConstructionForbiddenError) as raised:
        construct_live_execution_port_v1()
    assert "LIVE_EXECUTION_PORT_CONSTRUCTION_FORBIDDEN_IN_CAPABILITY_11_1" in str(raised.value)
    port = bind_simulated_execution_port_v1()
    assert isinstance(port, SimulatedExecutionPortV1)


def test_sample_provenance_model_is_bound_without_implementation() -> None:
    assert SAMPLE_PROVENANCE_REQUIRED_FIELDS == _REQUIRED_PROVENANCE
    u_section = _u_section()
    for field in _REQUIRED_PROVENANCE:
        assert field in u_section, field


def test_runbook_u_consumes_go_without_rewriting_s_or_t() -> None:
    runbook = RUNBOOK.read_text(encoding="utf-8")
    spec = SPEC_PATH.read_text(encoding="utf-8")
    s_start = runbook.index(S_HEADING)
    t_start = runbook.index(T_HEADING)
    u_start = runbook.index(U_HEADING)
    s_section = runbook[s_start:t_start]
    t_section = runbook[t_start:u_start]
    u_section = _u_section()
    assert "SEMANTIC_REQUIREMENTS_COMPLETE=false" in s_section
    assert "SEMANTIC_REQUIREMENTS_COMPLETE=true" in t_section
    assert "P01_STATUS=DECIDED" in t_section
    assert "U09_STATUS=DECIDED" in t_section
    assert (
        "OWNER_GO=OWNER_GO_PEAK_TRADE_FULL_CORE_RUNNING_EQUITY_AUTHORITY_ARCHITECTURE_RATIFICATION_V1"
        in u_section
    )
    assert "OWNER_GO_STATUS=CONSUMED" in u_section
    assert "ARCHITECTURE_RATIFIED=true" in u_section
    assert (
        "FUTURE_ACCOUNT_EQUITY_AUTHORITY_OWNER_CLASS="
        "GOVERNED_PRODUCTIVE_ACCOUNT_EQUITY_AUTHORITY_PRODUCER" in u_section
    )
    assert (
        "FUTURE_GOVERNED_SOURCE_OBJECT_CLASS=GOVERNED_RUNNING_ACCOUNT_EQUITY_SAMPLE_V1" in u_section
    )
    assert (
        "FUTURE_PRODUCER_CLASS="
        "COMPOSITIONAL_RECONSTRUCTION_WITH_WITNESS_RECONCILIATION_V1" in u_section
    )
    assert "STEP_29P_IS_NOT_EQUITY_AUTHORITY_OWNER=true" in u_section
    assert "LIVE_ACCOUNT_BOUND_IDENTITY_IS_NOT_CAPITAL_AUTHORITY=true" in u_section
    assert "RAW_VENUE_FIELD_AUTHORITY_FORBIDDEN=true" in u_section
    assert "OBSERVATION_IS_NOT_AUTHORITY=true" in u_section
    assert "SOURCE_SELECTED=false" in u_section
    assert "MAPPING_PROVEN=false" in u_section
    assert "RUNTIME_VALUE_BINDING_PRESENT=false" in u_section
    assert "ACCOUNT_EQUITY_AUTHORITY_OWNER=UNRESOLVED" in u_section
    assert "RUNNING_EQUITY_SOURCE_OBJECT=NONE" in u_section
    assert "GOVERNED_PRODUCTIVE_SOURCE_PRESENT=false" in u_section
    assert "GOVERNED_PRODUCER_CREATED=false" in u_section
    assert "LIVE_ACCOUNT_BOUND_JOIN_PRESENT=false" in u_section
    assert "STEP_29P_RISK_ADMISSIBLE=false" in u_section
    assert "LIVE_ENABLED=false" in u_section
    assert "LIVE_ARMED=false" in u_section
    assert "WIRE_SEND_PERMITTED=false" in u_section
    assert "THIS_SLICE=11.2.1.U" not in t_section
    assert "THIS_SLICE=11.2.1.U" not in s_section
    assert SEMANTIC_REQUIREMENTS_COMPLETE is True
    assert "DOCS_TOKEN_FULL_CORE_RUNNING_EQUITY_AUTHORITY_ARCHITECTURE_RATIFICATION_V1" in spec
    assert "ARCHITECTURE_RATIFIED=true" in spec
    assert "SOURCE_SELECTED=false" in spec
    assert "MAPPING_PROVEN=false" in spec
