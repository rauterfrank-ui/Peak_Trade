"""Concrete account-equity authority-owner assignment. Empty slot. No producer."""

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
    ACCOUNT_EQUITY_AUTHORITY_OWNER_CANDIDATE,
    ACCOUNT_EQUITY_AUTHORITY_OWNER_CLASS,
    ADJUDICATION_RESULT,
    ARCHITECTURE_RATIFIED,
    C01_C16_REMAIN_REJECTED,
    FUTURE_ACCOUNT_EQUITY_AUTHORITY_OWNER_CLASS,
    FUTURE_GOVERNED_SOURCE_OBJECT_CLASS,
    FUTURE_PRODUCER_CLASS,
    GOVERNED_PRODUCER_CREATED,
    GOVERNED_PRODUCTIVE_SOURCE_PRESENT,
    IMPLEMENTATION_OF_VALUE_BINDING,
    LIVE_ACCOUNT_BOUND_JOIN_PRESENT,
    LIVE_ARMED,
    LIVE_ENABLED,
    MAPPING_PROVEN,
    OWNER_ASSIGNMENT_RATIFIED,
    RUNNING_EQUITY_SOURCE_OBJECT,
    RUNTIME_VALUE_BINDING_PRESENT,
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
from src.ops.governed_productive_account_equity_authority_producer_v1.constants_v1 import (
    C01_C16_NOT_ELEVATED,
    PRODUCER_IMPLEMENTATION_PRESENT,
    SLOT_IS_EMPTY,
    SLOT_KIND,
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
    / "docs/ops/specs/FULL_CORE_ACCOUNT_EQUITY_AUTHORITY_OWNER_CONCRETE_ASSIGNMENT_RATIFICATION_V1.md"
)
SLOT_DIR = REPO_ROOT / "src/ops/governed_productive_account_equity_authority_producer_v1"
ASSIGNED_OWNER = "ops.governed_productive_account_equity_authority_producer_v1"
U_HEADING = "11.2.1.U FULL_CORE_RUNNING_EQUITY_AUTHORITY_ARCHITECTURE_RATIFICATION"
V_HEADING = "11.2.1.V FULL_CORE_ACCOUNT_EQUITY_AUTHORITY_OWNER_CONCRETE_ASSIGNMENT_RATIFICATION"
W_HEADING = "11.2.1.W FULL_CORE_GOVERNED_RUNNING_ACCOUNT_EQUITY_SAMPLE_SCHEMA"
_FORBIDDEN_EQUITY_FIELDS = (
    "details.availEq",
    "availEq",
    "totalEq",
    "eq",
    "adjEq",
    "availBal",
    "cashBal",
)
_CENSUS_IDS = (
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


def _v_section() -> str:
    runbook = RUNBOOK.read_text(encoding="utf-8")
    v_start = runbook.index(V_HEADING)
    return runbook[v_start : runbook.index(W_HEADING, v_start)]


def test_owner_assigned_to_empty_governed_slot_without_source_or_producer() -> None:
    assert OWNER_ASSIGNMENT_RATIFIED is True
    assert ACCOUNT_EQUITY_AUTHORITY_OWNER == ASSIGNED_OWNER
    assert ACCOUNT_EQUITY_AUTHORITY_OWNER != "UNRESOLVED"
    assert ACCOUNT_EQUITY_AUTHORITY_OWNER_CLASS == (
        "GOVERNED_PRODUCTIVE_ACCOUNT_EQUITY_AUTHORITY_PRODUCER"
    )
    assert ACCOUNT_EQUITY_AUTHORITY_OWNER_CLASS == FUTURE_ACCOUNT_EQUITY_AUTHORITY_OWNER_CLASS
    assert ACCOUNT_EQUITY_AUTHORITY_OWNER_CANDIDATE == "UNRESOLVED"
    assert SLOT_KIND == "EMPTY_GOVERNED_AUTHORITY_OWNER_SLOT"
    assert SLOT_IS_EMPTY is True
    assert C01_C16_NOT_ELEVATED is True
    assert PRODUCER_IMPLEMENTATION_PRESENT is False
    assert GOVERNED_PRODUCER_CREATED is False
    assert GOVERNED_PRODUCTIVE_SOURCE_PRESENT is False
    assert RUNNING_EQUITY_SOURCE_OBJECT == "NONE"
    assert SOURCE_SELECTED is False
    assert MAPPING_PROVEN is False
    assert IMPLEMENTATION_OF_VALUE_BINDING is False
    assert RUNTIME_VALUE_BINDING_PRESENT is False
    assert LIVE_ACCOUNT_BOUND_JOIN_PRESENT is False
    assert ARCHITECTURE_RATIFIED is True
    dag = live_admission_gap_dag_v1()
    assert dag["OWNER_ASSIGNMENT_RATIFIED"] is True
    assert dag["ACCOUNT_EQUITY_AUTHORITY_OWNER"] == ASSIGNED_OWNER
    assert dag["ACCOUNT_EQUITY_AUTHORITY_OWNER_CLASS"] == ACCOUNT_EQUITY_AUTHORITY_OWNER_CLASS
    assert dag["SOURCE_SELECTED"] is False
    assert dag["MAPPING_PROVEN"] is False
    assert dag["GOVERNED_PRODUCTIVE_SOURCE_PRESENT"] is False


def test_slot_contains_no_producer_implementation() -> None:
    py_files = sorted(path.name for path in SLOT_DIR.glob("*.py"))
    assert py_files == ["__init__.py", "constants_v1.py", "sample_schema_v1.py"]
    producer_surface = "\n".join(
        path.read_text(encoding="utf-8")
        for path in SLOT_DIR.glob("*.py")
        if path.name != "sample_schema_v1.py"
    )
    for forbidden in (
        "def mint",
        "def produce",
        "def reconstruct",
        "def bind_account_equity",
        "typed_account_equity_raw",
    ):
        assert forbidden not in producer_surface, forbidden
    schema = (SLOT_DIR / "sample_schema_v1.py").read_text(encoding="utf-8")
    assert "def mint" not in schema
    assert "def produce" not in schema
    assert "def reconstruct" not in schema
    assert "def bind_account_equity" not in schema


def test_c01_c16_not_elevated_and_forbidden_fields_deny() -> None:
    assert ACCOUNT_EQUITY_AUTHORITY_OWNER not in _CENSUS_IDS
    assert C01_C16_REMAIN_REJECTED is True
    assert STEP_29P_IS_NOT_EQUITY_AUTHORITY_OWNER is True
    assert ADJUDICATION_RESULT == "NO_CANONICALLY_VALID_MAPPING_AVAILABLE"
    assert EARLIEST_UNRESOLVED_FULL_CORE_DEPENDENCY == (
        "NO_CANONICALLY_VALID_ACCOUNT_EQUITY_SOURCE_MAPPING"
    )
    capital = _capital()
    for field in _FORBIDDEN_EQUITY_FIELDS:
        result = evaluate_step_29p_capital_risk_admissibility_v1(
            capital=capital,
            claim=_complete_claim(typed_account_equity_source_field=field),
        )
        assert result.risk_admissible is False


def test_step_29p_risk_admissible_and_live_gates_remain_false() -> None:
    v_section = _v_section()
    assert "STEP_29P_RISK_ADMISSIBLE=false" in v_section
    assert LIVE_ENABLED is False
    assert LIVE_ARMED is False
    assert WIRE_SEND_PERMITTED is False


def test_cap11_1_and_cap72_unchanged() -> None:
    with pytest.raises(ExecutionPortConstructionForbiddenError) as raised:
        construct_live_execution_port_v1()
    assert "LIVE_EXECUTION_PORT_CONSTRUCTION_FORBIDDEN_IN_CAPABILITY_11_1" in str(raised.value)
    port = bind_simulated_execution_port_v1()
    assert isinstance(port, SimulatedExecutionPortV1)


def test_runbook_v_consumes_go_without_rewriting_u() -> None:
    runbook = RUNBOOK.read_text(encoding="utf-8")
    spec = SPEC_PATH.read_text(encoding="utf-8")
    u_start = runbook.index(U_HEADING)
    v_start = runbook.index(V_HEADING)
    u_section = runbook[u_start:v_start]
    v_section = _v_section()
    assert "ARCHITECTURE_RATIFIED=true" in u_section
    assert "ACCOUNT_EQUITY_AUTHORITY_OWNER=UNRESOLVED" in u_section
    assert "THIS_SLICE=11.2.1.V" not in u_section
    assert (
        "OWNER_GO=OWNER_GO_PEAK_TRADE_FULL_CORE_ACCOUNT_EQUITY_AUTHORITY_OWNER_"
        "CONCRETE_ASSIGNMENT_RATIFICATION_V1" in v_section
    )
    assert "OWNER_GO_STATUS=CONSUMED" in v_section
    assert "OWNER_ASSIGNMENT_RATIFIED=true" in v_section
    assert f"ACCOUNT_EQUITY_AUTHORITY_OWNER={ASSIGNED_OWNER}" in v_section
    assert (
        "ACCOUNT_EQUITY_AUTHORITY_OWNER_CLASS="
        "GOVERNED_PRODUCTIVE_ACCOUNT_EQUITY_AUTHORITY_PRODUCER" in v_section
    )
    assert "SLOT_KIND=EMPTY_GOVERNED_AUTHORITY_OWNER_SLOT" in v_section
    assert "C01_C16_NOT_ELEVATED=true" in v_section
    assert "SOURCE_SELECTED=false" in v_section
    assert "MAPPING_PROVEN=false" in v_section
    assert "RUNTIME_VALUE_BINDING_PRESENT=false" in v_section
    assert "GOVERNED_PRODUCTIVE_SOURCE_PRESENT=false" in v_section
    assert "GOVERNED_PRODUCER_CREATED=false" in v_section
    assert "LIVE_ACCOUNT_BOUND_JOIN_PRESENT=false" in v_section
    assert "STEP_29P_RISK_ADMISSIBLE=false" in v_section
    assert "LIVE_ENABLED=false" in v_section
    assert "LIVE_ARMED=false" in v_section
    assert "WIRE_SEND_PERMITTED=false" in v_section
    assert (
        "EARLIEST_UNRESOLVED_FULL_CORE_DEPENDENCY="
        "NO_CANONICALLY_VALID_ACCOUNT_EQUITY_SOURCE_MAPPING" in v_section
    )
    assert FUTURE_GOVERNED_SOURCE_OBJECT_CLASS == "GOVERNED_RUNNING_ACCOUNT_EQUITY_SAMPLE_V1"
    assert FUTURE_PRODUCER_CLASS == "COMPOSITIONAL_RECONSTRUCTION_WITH_WITNESS_RECONCILIATION_V1"
    assert (
        "DOCS_TOKEN_FULL_CORE_ACCOUNT_EQUITY_AUTHORITY_OWNER_CONCRETE_ASSIGNMENT_RATIFICATION_V1"
        in spec
    )
    assert "OWNER_ASSIGNMENT_RATIFIED=true" in spec
    assert f"ACCOUNT_EQUITY_AUTHORITY_OWNER={ASSIGNED_OWNER}" in spec
    assert "SOURCE_SELECTED=false" in spec
    assert "MAPPING_PROVEN=false" in spec
    assert "GOVERNED_PRODUCER_CREATED=false" in spec
