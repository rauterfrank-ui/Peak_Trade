"""Running-equity policy semantics ratification. No source. No mapping."""

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
    C01_C16_REMAIN_REJECTED,
    DECIDED_RUNNING_EQUITY_POLICY_IDS,
    DOUBLE_COUNT_CONTROL_U02_U03_MTM_ONCE,
    DOUBLE_COUNT_CONTROL_U04_HOLD_ONCE,
    DOUBLE_COUNT_CONTROL_U05_LIABILITY_ONCE,
    DOUBLE_COUNT_CONTROL_U06_FEE_ONCE,
    GOVERNED_PRODUCER_CREATED,
    IMPLEMENTATION_OF_VALUE_BINDING,
    LIVE_ARMED,
    LIVE_ENABLED,
    LIVE_ACCOUNT_BOUND_JOIN_EXECUTED_THIS_SLICE,
    MAPPING_PROVEN,
    NUMERIC_EQUITY_TTL_SECONDS,
    P01_HAIRCUTS_RESERVE_DEPLETION,
    P01_MAY_INCREASE_EQUITY,
    P01_STATUS,
    P01_ZERO_ONLY_BY_EXPLICIT_POLICY,
    POLICY_SEMANTICS_COMPLETE,
    RUNNING_EQUITY_POLICY_SEMANTICS_RATIFIED,
    RUNNING_EQUITY_SOURCE_OBJECT,
    SEMANTIC_REQUIREMENTS_COMPLETE,
    U01_ACCOUNT_MODE_ROLE,
    U01_STATUS,
    U02_STATUS,
    U03_STATUS,
    U04_STATUS,
    U05_STATUS,
    U06_STATUS,
    U07_RESTART_RECONCILIATION,
    U07_STATUS,
    U08_MULTI_CURRENCY_CONVERSION,
    U08_STATUS,
    U09_COPIES_AVAILABLE_MARGIN_TS_AGE_BOUND,
    U09_FRESHNESS_CLASS,
    U09_SAME_PRETRADE_EPOCH_REQUIRED,
    U09_STATUS,
    USD_EQUALS_USDC,
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
    REPO_ROOT / "docs/ops/specs/FULL_CORE_RUNNING_EQUITY_POLICY_SEMANTICS_RATIFICATION_V1.md"
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


def _t_section() -> str:
    runbook = RUNBOOK.read_text(encoding="utf-8")
    t_start = runbook.index(T_HEADING)
    return runbook[t_start : runbook.index(U_HEADING, t_start)]


def test_all_ten_policies_decided() -> None:
    assert DECIDED_RUNNING_EQUITY_POLICY_IDS == (
        "P01",
        "U01",
        "U02",
        "U03",
        "U04",
        "U05",
        "U06",
        "U07",
        "U08",
        "U09",
    )
    assert P01_STATUS == "DECIDED"
    assert U01_STATUS == "DECIDED"
    assert U02_STATUS == "DECIDED"
    assert U03_STATUS == "DECIDED"
    assert U04_STATUS == "DECIDED"
    assert U05_STATUS == "DECIDED"
    assert U06_STATUS == "DECIDED"
    assert U07_STATUS == "DECIDED"
    assert U08_STATUS == "DECIDED"
    assert U09_STATUS == "DECIDED"
    assert RUNNING_EQUITY_POLICY_SEMANTICS_RATIFIED is True
    assert SEMANTIC_REQUIREMENTS_COMPLETE is True
    assert POLICY_SEMANTICS_COMPLETE is True
    dag = live_admission_gap_dag_v1()
    assert dag["P01_STATUS"] == "DECIDED"
    assert dag["U09_STATUS"] == "DECIDED"
    assert dag["SEMANTIC_REQUIREMENTS_COMPLETE"] is True
    assert dag["POLICY_SEMANTICS_COMPLETE"] is True


def test_same_epoch_and_numeric_ttl() -> None:
    assert U09_FRESHNESS_CLASS == "FRESH_GET_PER_PRETRADE_DECISION"
    assert U09_SAME_PRETRADE_EPOCH_REQUIRED is True
    assert NUMERIC_EQUITY_TTL_SECONDS == 5
    assert U09_COPIES_AVAILABLE_MARGIN_TS_AGE_BOUND is False
    dag = live_admission_gap_dag_v1()
    assert dag["U09_SAME_PRETRADE_EPOCH_REQUIRED"] is True
    assert dag["NUMERIC_EQUITY_TTL_SECONDS"] == 5


def test_usd_is_not_usdc_and_reduction_only() -> None:
    assert USD_EQUALS_USDC is False
    assert P01_MAY_INCREASE_EQUITY is False
    assert P01_ZERO_ONLY_BY_EXPLICIT_POLICY is True
    assert P01_HAIRCUTS_RESERVE_DEPLETION == "REDUCTION_ONLY_UNSPECIFIED_FAIL_CLOSED"
    assert U08_MULTI_CURRENCY_CONVERSION == (
        "USDC_NATIVE_OR_OWNER_RATIFIED_CONTRACT_ELSE_FAIL_CLOSED"
    )
    dag = live_admission_gap_dag_v1()
    assert dag["USD_EQUALS_USDC"] is False
    assert dag["P01_MAY_INCREASE_EQUITY"] is False


def test_double_count_and_restart_guards() -> None:
    assert DOUBLE_COUNT_CONTROL_U02_U03_MTM_ONCE is True
    assert DOUBLE_COUNT_CONTROL_U04_HOLD_ONCE is True
    assert DOUBLE_COUNT_CONTROL_U05_LIABILITY_ONCE is True
    assert DOUBLE_COUNT_CONTROL_U06_FEE_ONCE is True
    assert U07_RESTART_RECONCILIATION == "FAIL_CLOSED_UNTIL_FRESH_SAME_EPOCH_RECONCILED"
    assert U01_ACCOUNT_MODE_ROLE == "ELIGIBILITY_CONTEXT_NOT_NUMERIC_EQUITY_TERM"


def test_mapping_owner_source_and_live_gates_unchanged() -> None:
    assert MAPPING_PROVEN is False
    assert IMPLEMENTATION_OF_VALUE_BINDING is False
    assert ACCOUNT_EQUITY_AUTHORITY_OWNER == (
        "ops.governed_productive_account_equity_authority_producer_v1"
    )
    assert RUNNING_EQUITY_SOURCE_OBJECT == "NONE"
    assert LIVE_ACCOUNT_BOUND_JOIN_EXECUTED_THIS_SLICE is False
    assert GOVERNED_PRODUCER_CREATED is False
    assert C01_C16_REMAIN_REJECTED is True
    assert ADJUDICATION_RESULT == "NO_CANONICALLY_VALID_MAPPING_AVAILABLE"
    assert EARLIEST_UNRESOLVED_FULL_CORE_DEPENDENCY == (
        "NO_CANONICALLY_VALID_ACCOUNT_EQUITY_SOURCE_MAPPING"
    )
    assert LIVE_ENABLED is False
    assert LIVE_ARMED is False
    assert WIRE_SEND_PERMITTED is False
    dag = live_admission_gap_dag_v1()
    assert dag["MAPPING_PROVEN"] is False
    assert dag["ACCOUNT_EQUITY_AUTHORITY_OWNER"] == ACCOUNT_EQUITY_AUTHORITY_OWNER
    assert dag["C01_C16_REMAIN_REJECTED"] is True
    assert dag["EARLIEST_UNRESOLVED_FULL_CORE_DEPENDENCY"] == (
        EARLIEST_UNRESOLVED_FULL_CORE_DEPENDENCY
    )


def test_c01_c16_remain_rejected_in_s_and_forbidden_fields_deny() -> None:
    runbook = RUNBOOK.read_text(encoding="utf-8")
    s_start = runbook.index(S_HEADING)
    t_start = runbook.index(T_HEADING)
    s_section = runbook[s_start:t_start]
    for candidate_id in _CANDIDATE_IDS:
        assert candidate_id in s_section, candidate_id
    assert "ADJUDICATION_RESULT=NO_CANONICALLY_VALID_MAPPING_AVAILABLE" in s_section
    assert "C01_C16_REMAIN_REJECTED=true" in _t_section()
    capital = _capital()
    for field in _FORBIDDEN_EQUITY_FIELDS:
        result = evaluate_step_29p_capital_risk_admissibility_v1(
            capital=capital,
            claim=_complete_claim(typed_account_equity_source_field=field),
        )
        assert result.risk_admissible is False


def test_step_29p_risk_admissible_and_live_gates_remain_false() -> None:
    t_section = _t_section()
    assert "STEP_29P_RISK_ADMISSIBLE=false" in t_section
    assert LIVE_ENABLED is False
    assert LIVE_ARMED is False
    assert WIRE_SEND_PERMITTED is False


def test_cap11_1_and_cap72_unchanged() -> None:
    with pytest.raises(ExecutionPortConstructionForbiddenError) as raised:
        construct_live_execution_port_v1()
    assert "LIVE_EXECUTION_PORT_CONSTRUCTION_FORBIDDEN_IN_CAPABILITY_11_1" in str(raised.value)
    port = bind_simulated_execution_port_v1()
    assert isinstance(port, SimulatedExecutionPortV1)


def test_runbook_t_consumes_go_without_rewriting_s() -> None:
    runbook = RUNBOOK.read_text(encoding="utf-8")
    spec = SPEC_PATH.read_text(encoding="utf-8")
    s_start = runbook.index(S_HEADING)
    t_start = runbook.index(T_HEADING)
    s_section = runbook[s_start:t_start]
    t_section = _t_section()
    assert "SEMANTIC_REQUIREMENTS_COMPLETE=false" in s_section
    assert (
        "OWNER_GO=OWNER_GO_PEAK_TRADE_FULL_CORE_RUNNING_EQUITY_POLICY_SEMANTICS_RATIFICATION_V1"
        in t_section
    )
    assert "OWNER_GO_STATUS=CONSUMED" in t_section
    assert "SEMANTIC_REQUIREMENTS_COMPLETE=true" in t_section
    assert "POLICY_SEMANTICS_COMPLETE=true" in t_section
    assert "P01_STATUS=DECIDED" in t_section
    assert "U09_STATUS=DECIDED" in t_section
    assert "NUMERIC_EQUITY_TTL_SECONDS=5" in t_section
    assert "U09_SAME_PRETRADE_EPOCH_REQUIRED=true" in t_section
    assert "USD_EQUALS_USDC=false" in t_section
    assert "P01_MAY_INCREASE_EQUITY=false" in t_section
    assert "MAPPING_PROVEN=false" in t_section
    assert "ACCOUNT_EQUITY_AUTHORITY_OWNER=UNRESOLVED" in t_section
    assert "RUNNING_EQUITY_SOURCE_OBJECT=NONE" in t_section
    assert "STEP_29P_RISK_ADMISSIBLE=false" in t_section
    assert "LIVE_ENABLED=false" in t_section
    assert "LIVE_ARMED=false" in t_section
    assert "WIRE_SEND_PERMITTED=false" in t_section
    assert "GOVERNED_PRODUCER_CREATED=false" in t_section
    assert "THIS_SLICE=11.2.1.T" not in s_section
    assert "DOCS_TOKEN_FULL_CORE_RUNNING_EQUITY_POLICY_SEMANTICS_RATIFICATION_V1" in spec
    assert "SEMANTIC_REQUIREMENTS_COMPLETE=true" in spec
    assert "MAPPING_PROVEN=false" in spec
