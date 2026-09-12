"""Typed GOVERNED_RUNNING_ACCOUNT_EQUITY_SAMPLE_V1 schema. No producer. No mapping."""

from __future__ import annotations

from decimal import Decimal
from pathlib import Path

import pytest

from src.ops.capability_11_1_execution_domain_and_order_lifecycle_contracts_v1.execution_ports_v1 import (
    ExecutionPortConstructionForbiddenError,
    bind_simulated_execution_port_v1,
    construct_live_execution_port_v1,
)
from src.ops.full_core_live_path_composition_root_v1.constants_v1 import (
    GOVERNED_PRODUCER_CREATED,
    GOVERNED_PRODUCTIVE_SOURCE_PRESENT,
    GOVERNED_RUNNING_ACCOUNT_EQUITY_SAMPLE_SCHEMA_PRESENT,
    LIVE_ACCOUNT_BOUND_JOIN_PRESENT,
    LIVE_ARMED,
    LIVE_ENABLED,
    MAPPING_PROVEN,
    NUMERIC_EQUITY_TTL_SECONDS,
    RUNTIME_VALUE_BINDING_PRESENT,
    SAMPLE_PROVENANCE_REQUIRED_FIELDS,
    SOURCE_OBJECT_PRESENT,
    SOURCE_OBJECT_PRESENT_SEMANTICS,
    SOURCE_SELECTED,
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
    OWNER,
    SAMPLE_PRESENT,
    SAMPLE_PROVENANCE_REQUIRED_FIELDS as OWNER_SLOT_SAMPLE_PROVENANCE_REQUIRED_FIELDS,
    NUMERIC_EQUITY_TTL_SECONDS as OWNER_SLOT_NUMERIC_EQUITY_TTL_SECONDS,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.sample_schema_v1 import (
    CANONICAL_OBSERVED_AT_AS_OF,
    DIMENSION_ID,
    GovernedRunningAccountEquitySampleSchemaError,
    GovernedRunningAccountEquitySampleV1,
    build_governed_running_account_equity_sample_v1,
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
    REPO_ROOT / "docs/ops/specs/FULL_CORE_GOVERNED_RUNNING_ACCOUNT_EQUITY_SAMPLE_SCHEMA_V1.md"
)
V_HEADING = "11.2.1.V FULL_CORE_ACCOUNT_EQUITY_AUTHORITY_OWNER_CONCRETE_ASSIGNMENT_RATIFICATION"
W_HEADING = "11.2.1.W FULL_CORE_GOVERNED_RUNNING_ACCOUNT_EQUITY_SAMPLE_SCHEMA"
X_HEADING = "11.2.1.X FULL_CORE_TYPED_VENUE_WITNESS_OBSERVATION_CONTRACT"
_FORBIDDEN_EQUITY_FIELDS = (
    "details.availEq",
    "availEq",
    "totalEq",
    "eq",
    "adjEq",
    "availBal",
    "cashBal",
    "frozenBal",
    "isoEq",
    "ordFrozen",
    "upl",
    "mgnRatio",
    "Balance.total",
    "LedgerSnapshot.equity_by_ccy",
    "AccountingPortfolioStateV1.equity",
    "FundingAccountBalanceObservationV1",
    "FreshAvailableMarginObservationV1",
    "SimulatedPortfolioStateV1.equity",
    "start_balance",
)


def _synthetic_fields() -> dict[str, object]:
    return {
        "dimension_id": DIMENSION_ID,
        "bound_account_identity": "SYNTHETIC_BOUND_ACCOUNT",
        "bound_venue_identity": "OKX_EEA",
        "bound_td_mode": "cross",
        "settlement_currency": "USDC",
        "value": Decimal("1.25"),
        "value_semantics": "SYNTHETIC_SCHEMA_PROOF_NOT_VENUE_FIELD",
        "producer_identity": OWNER,
        "authority_contract_ref": ("FULL_CORE_GOVERNED_RUNNING_ACCOUNT_EQUITY_SAMPLE_SCHEMA_V1"),
        "source_revision_or_digest": "synthetic-source-digest",
        "input_set_digest": "synthetic-input-digest",
        "decision_epoch": "synthetic-decision-epoch",
        CANONICAL_OBSERVED_AT_AS_OF: "2026-09-12T00:00:00Z",
        "freshness_max_age": str(NUMERIC_EQUITY_TTL_SECONDS),
        "freshness_policy_status": "EXPLICIT_NOT_IMPLIED_FRESH",
        "restart_reconciliation_status": "EXPLICIT_NOT_RECONCILED",
        "component_completeness": "EXPLICIT_SYNTHETIC_COMPLETENESS",
        "component_provenance": "SYNTHETIC_SCHEMA_PROOF",
        "inclusion_vector": "EXPLICIT_SYNTHETIC_INCLUSION",
        "component_term_vector": "EXPLICIT_SYNTHETIC_TERM_VECTOR",
        "double_count_guards": "EXPLICIT_SYNTHETIC_DOUBLE_COUNT_GUARDS",
        "currency_conversion_status": "USDC_NATIVE_NO_CONVERSION",
        "witness_reconciliation_status": "EXPLICIT_NOT_RECONCILED",
        "policy_version": "P01_U01_U09_DECIDED",
        "semantic_digest": "synthetic-semantic-digest",
        "sample_id": "synthetic-sample-id",
        "observation_vs_authority_class": "OBSERVATION",
    }


def _w_section() -> str:
    runbook = RUNBOOK.read_text(encoding="utf-8")
    w_start = runbook.index(W_HEADING)
    return runbook[w_start : runbook.index(X_HEADING, w_start)]


def test_owner_slot_provenance_fields_match_runbook_controlling_tuple() -> None:
    assert OWNER_SLOT_SAMPLE_PROVENANCE_REQUIRED_FIELDS == SAMPLE_PROVENANCE_REQUIRED_FIELDS
    assert OWNER_SLOT_NUMERIC_EQUITY_TTL_SECONDS == NUMERIC_EQUITY_TTL_SECONDS
    assert CANONICAL_OBSERVED_AT_AS_OF in SAMPLE_PROVENANCE_REQUIRED_FIELDS


def test_schema_constructs_with_explicit_synthetic_values_only() -> None:
    sample = build_governed_running_account_equity_sample_v1(**_synthetic_fields())
    assert isinstance(sample, GovernedRunningAccountEquitySampleV1)
    assert sample.dimension_id == DIMENSION_ID
    assert sample.settlement_currency == "USDC"
    assert sample.value == Decimal("1.25")
    canonical = sample.to_canonical_dict()
    assert tuple(canonical) == SAMPLE_PROVENANCE_REQUIRED_FIELDS
    assert canonical[CANONICAL_OBSERVED_AT_AS_OF] == "2026-09-12T00:00:00Z"
    assert GOVERNED_RUNNING_ACCOUNT_EQUITY_SAMPLE_SCHEMA_PRESENT is True
    assert SOURCE_OBJECT_PRESENT is False
    assert SAMPLE_PRESENT is False
    assert SOURCE_OBJECT_PRESENT_SEMANTICS == "RUNTIME_SAMPLE_INSTANCE_NOT_SCHEMA_DEFINITION"


def test_missing_required_provenance_fails() -> None:
    fields = _synthetic_fields()
    fields.pop("sample_id")
    with pytest.raises(GovernedRunningAccountEquitySampleSchemaError) as raised:
        build_governed_running_account_equity_sample_v1(**fields)
    assert "GOVERNED_RUNNING_ACCOUNT_EQUITY_SAMPLE_FIELD_MISSING:sample_id" in str(raised.value)


def test_missing_account_identity_fails() -> None:
    fields = _synthetic_fields()
    fields["bound_account_identity"] = ""
    with pytest.raises(GovernedRunningAccountEquitySampleSchemaError) as raised:
        build_governed_running_account_equity_sample_v1(**fields)
    assert "bound_account_identity" in str(raised.value)


def test_missing_semantic_dimension_fails() -> None:
    fields = _synthetic_fields()
    fields["dimension_id"] = ""
    with pytest.raises(GovernedRunningAccountEquitySampleSchemaError) as raised:
        build_governed_running_account_equity_sample_v1(**fields)
    assert "dimension_id" in str(raised.value)


def test_missing_currency_fails() -> None:
    fields = _synthetic_fields()
    fields["settlement_currency"] = ""
    with pytest.raises(GovernedRunningAccountEquitySampleSchemaError) as raised:
        build_governed_running_account_equity_sample_v1(**fields)
    assert "settlement_currency" in str(raised.value)


def test_usd_is_not_usdc() -> None:
    fields = _synthetic_fields()
    fields["settlement_currency"] = "USD"
    with pytest.raises(GovernedRunningAccountEquitySampleSchemaError) as raised:
        build_governed_running_account_equity_sample_v1(**fields)
    assert "CURRENCY_NOT_USDC" in str(raised.value)


def test_missing_freshness_evidence_fails() -> None:
    fields = _synthetic_fields()
    fields["freshness_max_age"] = ""
    with pytest.raises(GovernedRunningAccountEquitySampleSchemaError) as raised:
        build_governed_running_account_equity_sample_v1(**fields)
    assert "freshness_max_age" in str(raised.value)


def test_missing_reconciliation_provenance_fails() -> None:
    fields = _synthetic_fields()
    fields["witness_reconciliation_status"] = ""
    with pytest.raises(GovernedRunningAccountEquitySampleSchemaError) as raised:
        build_governed_running_account_equity_sample_v1(**fields)
    assert "witness_reconciliation_status" in str(raised.value)


def test_decimal_value_validation_is_deterministic() -> None:
    fields = _synthetic_fields()
    fields["value"] = Decimal("Infinity")
    with pytest.raises(GovernedRunningAccountEquitySampleSchemaError) as raised:
        build_governed_running_account_equity_sample_v1(**fields)
    assert "VALUE_NOT_FINITE" in str(raised.value)
    fields["value"] = "not-a-decimal"
    with pytest.raises(GovernedRunningAccountEquitySampleSchemaError) as raised:
        build_governed_running_account_equity_sample_v1(**fields)
    assert "VALUE_NOT_DECIMAL" in str(raised.value)


def test_raw_forbidden_field_names_cannot_be_fallback_authority() -> None:
    for forbidden in _FORBIDDEN_EQUITY_FIELDS:
        fields = _synthetic_fields()
        fields["value_semantics"] = forbidden
        with pytest.raises(GovernedRunningAccountEquitySampleSchemaError) as raised:
            build_governed_running_account_equity_sample_v1(**fields)
        assert "FORBIDDEN_AUTHORITY_FIELD" in str(raised.value), forbidden
        fields = _synthetic_fields()
        fields["producer_identity"] = forbidden
        with pytest.raises(GovernedRunningAccountEquitySampleSchemaError) as raised:
            build_governed_running_account_equity_sample_v1(**fields)
        assert "FORBIDDEN_AUTHORITY_FIELD" in str(raised.value) or (
            "PRODUCER_IDENTITY_MISMATCH" in str(raised.value)
        ), forbidden


def test_authority_class_cannot_mint_without_producer() -> None:
    fields = _synthetic_fields()
    fields["observation_vs_authority_class"] = "AUTHORITY"
    with pytest.raises(GovernedRunningAccountEquitySampleSchemaError) as raised:
        build_governed_running_account_equity_sample_v1(**fields)
    assert "AUTHORITY_CLASS_FORBIDDEN_UNTIL_PRODUCER_MINT" in str(raised.value)


def test_schema_creation_does_not_select_source_or_mapping_or_producer() -> None:
    build_governed_running_account_equity_sample_v1(**_synthetic_fields())
    assert SOURCE_SELECTED is False
    assert MAPPING_PROVEN is False
    assert GOVERNED_PRODUCER_CREATED is False
    assert GOVERNED_PRODUCTIVE_SOURCE_PRESENT is False
    assert RUNTIME_VALUE_BINDING_PRESENT is False
    assert LIVE_ACCOUNT_BOUND_JOIN_PRESENT is False
    dag = live_admission_gap_dag_v1()
    assert dag["SOURCE_SELECTED"] is False
    assert dag["MAPPING_PROVEN"] is False
    assert dag["GOVERNED_RUNNING_ACCOUNT_EQUITY_SAMPLE_SCHEMA_PRESENT"] is True
    assert dag["SOURCE_OBJECT_PRESENT"] is False
    assert dag["EARLIEST_UNRESOLVED_FULL_CORE_DEPENDENCY"] == (
        "NO_CANONICALLY_VALID_ACCOUNT_EQUITY_SOURCE_MAPPING"
    )
    assert EARLIEST_UNRESOLVED_FULL_CORE_DEPENDENCY == (
        "NO_CANONICALLY_VALID_ACCOUNT_EQUITY_SOURCE_MAPPING"
    )


def test_step_29p_remains_inadmissible_and_live_gates_remain_false() -> None:
    capital = _capital()
    result = evaluate_step_29p_capital_risk_admissibility_v1(
        capital=capital,
        claim=_complete_claim(typed_account_equity_source_field="availEq"),
    )
    assert result.risk_admissible is False
    assert LIVE_ENABLED is False
    assert LIVE_ARMED is False
    assert WIRE_SEND_PERMITTED is False
    with pytest.raises(ExecutionPortConstructionForbiddenError) as raised:
        construct_live_execution_port_v1()
    assert "LIVE_EXECUTION_PORT_CONSTRUCTION_FORBIDDEN_IN_CAPABILITY_11_1" in str(raised.value)
    port = bind_simulated_execution_port_v1()
    assert isinstance(port, SimulatedExecutionPortV1)


def test_runbook_w_consumes_go_without_rewriting_v() -> None:
    runbook = RUNBOOK.read_text(encoding="utf-8")
    spec = SPEC_PATH.read_text(encoding="utf-8")
    v_start = runbook.index(V_HEADING)
    w_section = _w_section()
    v_section = runbook[v_start : runbook.index(W_HEADING, v_start)]
    assert "OWNER_ASSIGNMENT_RATIFIED=true" in v_section
    assert "THIS_SLICE=11.2.1.W" not in v_section
    assert (
        "OWNER_GO=OWNER_GO_PEAK_TRADE_FULL_CORE_GOVERNED_RUNNING_ACCOUNT_EQUITY_SAMPLE_SCHEMA_V1"
        in w_section
    )
    assert "OWNER_GO_STATUS=CONSUMED" in w_section
    assert "GOVERNED_RUNNING_ACCOUNT_EQUITY_SAMPLE_SCHEMA_PRESENT=true" in w_section
    assert "SOURCE_OBJECT_PRESENT=false" in w_section
    assert "SOURCE_SELECTED=false" in w_section
    assert "MAPPING_PROVEN=false" in w_section
    assert "GOVERNED_PRODUCER_CREATED=false" in w_section
    assert "RUNTIME_VALUE_BINDING_PRESENT=false" in w_section
    assert "LIVE_ACCOUNT_BOUND_JOIN_PRESENT=false" in w_section
    assert "STEP_29P_RISK_ADMISSIBLE=false" in w_section
    assert "LIVE_ENABLED=false" in w_section
    assert "LIVE_ARMED=false" in w_section
    assert "WIRE_SEND_PERMITTED=false" in w_section
    assert (
        "EARLIEST_UNRESOLVED_FULL_CORE_DEPENDENCY="
        "NO_CANONICALLY_VALID_ACCOUNT_EQUITY_SOURCE_MAPPING" in w_section
    )
    assert "DOCS_TOKEN_FULL_CORE_GOVERNED_RUNNING_ACCOUNT_EQUITY_SAMPLE_SCHEMA_V1" in spec
    assert "GOVERNED_RUNNING_ACCOUNT_EQUITY_SAMPLE_SCHEMA_PRESENT=true" in spec
    assert "SOURCE_SELECTED=false" in spec
    assert "MAPPING_PROVEN=false" in spec
    assert "GOVERNED_PRODUCER_CREATED=false" in spec
