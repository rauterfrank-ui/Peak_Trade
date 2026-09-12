"""Typed Trading-Account venue-witness observation contract. No mapping. No producer."""

from __future__ import annotations

import hashlib
from dataclasses import FrozenInstanceError
from pathlib import Path

import pytest

from src.ops.capability_11_1_execution_domain_and_order_lifecycle_contracts_v1.execution_ports_v1 import (
    ExecutionPortConstructionForbiddenError,
    bind_simulated_execution_port_v1,
    construct_live_execution_port_v1,
)
from src.ops.full_core_live_path_composition_root_v1.constants_v1 import (
    EQUITY_DIMENSION_BOUND,
    GOVERNED_PRODUCER_CREATED,
    GOVERNED_PRODUCTIVE_SOURCE_PRESENT,
    LIVE_ACCOUNT_BOUND_JOIN_PRESENT,
    LIVE_ARMED,
    LIVE_ENABLED,
    MAPPED_TO_RUNNING_ACCOUNT_EQUITY_AVAILABLE_FOR_SIZING,
    MAPPING_PROVEN,
    OBSERVATION_AUTHORITY_EFFECT,
    RAW_TO_WITNESS_PROVEN,
    RUNTIME_VALUE_BINDING_PRESENT,
    SOURCE_OBJECT_PRESENT,
    SOURCE_SELECTED,
    VENUE_WITNESS_RUNTIME_INSTANCE_PRESENT,
    VENUE_WITNESS_SCHEMA_PRESENT,
    VENUE_WITNESS_SELECTED,
    WIRE_SEND_PERMITTED,
    WITNESS_CONTRACT_MISSING_CLOSED,
)
from src.ops.full_core_live_path_composition_root_v1.live_admission_gap_dag_v1 import (
    EARLIEST_DECOMPOSED_CONTRACT_GAP,
    EARLIEST_UNRESOLVED_FULL_CORE_DEPENDENCY,
    live_admission_gap_dag_v1,
)
from src.ops.full_core_live_path_composition_root_v1.step_29p_capital_risk_admissibility_v1 import (
    evaluate_step_29p_capital_risk_admissibility_v1,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.venue_witness_observation_v1 import (
    CANONICAL_OBSERVED_AT_AS_OF,
    CLOCK_SOURCE_STATUS_UNBOUND,
    EQUITY_DIMENSION_BOUND_STATUS_UNBOUND,
    FRESHNESS_EVIDENCE_STATUS,
    MAPPING_STATUS_UNBOUND,
    OBSERVATION_SEMANTIC_CLASS,
    PAYLOAD_DIGEST_ONLY,
    PRESENCE_EMPTY,
    PRESENCE_MALFORMED,
    PRESENCE_MISSING,
    PRESENCE_NONZERO,
    PRESENCE_ZERO,
    RAW_PAYLOAD_RETAINED,
    TradingAccountVenueWitnessObservationV1,
    VenueWitnessObservationContractError,
    attach_venue_witness_provenance_digest_v1,
    build_trading_account_venue_witness_observation_v1,
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
SPEC_PATH = REPO_ROOT / "docs/ops/specs/FULL_CORE_TYPED_VENUE_WITNESS_OBSERVATION_CONTRACT_V1.md"
W_HEADING = "11.2.1.W FULL_CORE_GOVERNED_RUNNING_ACCOUNT_EQUITY_SAMPLE_SCHEMA"
X_HEADING = "11.2.1.X FULL_CORE_TYPED_VENUE_WITNESS_OBSERVATION_CONTRACT"
_SYNTHETIC_PAYLOAD = '{"code":"0","data":[{"details":[{"ccy":"USDC","availEq":"1.25"}]}]}'
_FORBIDDEN_FALLBACK = "totalEq|eq|adjEq|availEq"


def _synthetic_fields(
    *, presence: str = PRESENCE_NONZERO, **overrides: object
) -> dict[str, object]:
    raw_value = "1.25"
    if presence == PRESENCE_MISSING or presence == PRESENCE_EMPTY:
        raw_value = ""
    elif presence == PRESENCE_ZERO:
        raw_value = "0"
    elif presence == PRESENCE_MALFORMED:
        raw_value = "not-a-decimal"
    fields: dict[str, object] = {
        "witness_id": "SYNTHETIC_WITNESS_ID",
        "bound_account_identity": "SYNTHETIC_BOUND_ACCOUNT",
        "bound_venue_identity": "OKX_EEA",
        "rest_host": "eea.okx.com",
        "bound_td_mode": "cross",
        "account_mode": "UNPROVEN",
        "currency_domain": "USDC",
        "endpoint": "/api/v5/account/balance",
        "method": "GET",
        "request_identity": "synthetic-request-id",
        "decision_epoch": "synthetic-decision-epoch",
        CANONICAL_OBSERVED_AT_AS_OF: "2026-09-12T00:00:00Z",
        "response_received_at": "2026-09-12T00:00:01Z",
        "provider_timestamp": "1757696400000",
        "raw_field_path": "details.availEq",
        "observation_semantic_class": OBSERVATION_SEMANTIC_CLASS,
        "raw_value_representation": raw_value,
        "presence_state": presence,
        "raw_payload_state": PAYLOAD_DIGEST_ONLY,
        "payload_digest": "a" * 64,
        "raw_payload": "",
        "request_provenance": "SYNTHETIC_GET_REQUEST",
        "response_provenance": "SYNTHETIC_GET_RESPONSE_DIGEST_ONLY",
        "observation_vs_authority_class": "OBSERVATION",
        "observation_authority_effect": "NONE",
        "equity_dimension_bound_status": EQUITY_DIMENSION_BOUND_STATUS_UNBOUND,
        "mapping_status": MAPPING_STATUS_UNBOUND,
        "freshness_evidence_status": FRESHNESS_EVIDENCE_STATUS,
        "clock_source_status": CLOCK_SOURCE_STATUS_UNBOUND,
    }
    fields.update(overrides)
    return attach_venue_witness_provenance_digest_v1(fields)


def _x_section() -> str:
    runbook = RUNBOOK.read_text(encoding="utf-8")
    x_start = runbook.index(X_HEADING)
    return runbook[x_start : runbook.index("## 11.3 Autonomy state model", x_start)]


def test_valid_synthetic_observation_can_be_constructed() -> None:
    witness = build_trading_account_venue_witness_observation_v1(**_synthetic_fields())
    assert isinstance(witness, TradingAccountVenueWitnessObservationV1)
    assert witness.bound_account_identity == "SYNTHETIC_BOUND_ACCOUNT"
    assert witness.currency_domain == "USDC"
    assert witness.observation_semantic_class == OBSERVATION_SEMANTIC_CLASS
    assert witness.observation_vs_authority_class == "OBSERVATION"
    canonical = witness.to_canonical_dict()
    assert canonical[CANONICAL_OBSERVED_AT_AS_OF] == "2026-09-12T00:00:00Z"
    assert canonical["raw_field_path"] == "details.availEq"
    assert VENUE_WITNESS_SCHEMA_PRESENT is True
    assert VENUE_WITNESS_RUNTIME_INSTANCE_PRESENT is False
    assert VENUE_WITNESS_SELECTED is False


def test_object_is_immutable() -> None:
    witness = build_trading_account_venue_witness_observation_v1(**_synthetic_fields())
    with pytest.raises(FrozenInstanceError):
        witness.presence_state = PRESENCE_ZERO  # type: ignore[misc]


def test_missing_account_identity_fails() -> None:
    fields = _synthetic_fields()
    fields["bound_account_identity"] = ""
    with pytest.raises(VenueWitnessObservationContractError) as raised:
        build_trading_account_venue_witness_observation_v1(**fields)
    assert "bound_account_identity" in str(raised.value)


def test_missing_venue_context_fails() -> None:
    fields = _synthetic_fields()
    fields["bound_venue_identity"] = ""
    with pytest.raises(VenueWitnessObservationContractError) as raised:
        build_trading_account_venue_witness_observation_v1(**fields)
    assert "bound_venue_identity" in str(raised.value)
    fields = _synthetic_fields()
    fields["rest_host"] = ""
    with pytest.raises(VenueWitnessObservationContractError) as raised:
        build_trading_account_venue_witness_observation_v1(**fields)
    assert "rest_host" in str(raised.value)


def test_missing_currency_domain_fails() -> None:
    fields = _synthetic_fields()
    fields["currency_domain"] = ""
    with pytest.raises(VenueWitnessObservationContractError) as raised:
        build_trading_account_venue_witness_observation_v1(**fields)
    assert "currency_domain" in str(raised.value)


def test_usd_is_not_rewritten_to_usdc() -> None:
    witness = build_trading_account_venue_witness_observation_v1(
        **_synthetic_fields(currency_domain="USD")
    )
    assert witness.currency_domain == "USD"
    assert witness.currency_domain != "USDC"


def test_missing_endpoint_and_request_identity_fail() -> None:
    fields = _synthetic_fields()
    fields["endpoint"] = ""
    with pytest.raises(VenueWitnessObservationContractError) as raised:
        build_trading_account_venue_witness_observation_v1(**fields)
    assert "endpoint" in str(raised.value)
    fields = _synthetic_fields()
    fields["request_identity"] = ""
    with pytest.raises(VenueWitnessObservationContractError) as raised:
        build_trading_account_venue_witness_observation_v1(**fields)
    assert "request_identity" in str(raised.value)


def test_missing_observation_timestamp_fails() -> None:
    fields = _synthetic_fields()
    fields[CANONICAL_OBSERVED_AT_AS_OF] = ""
    with pytest.raises(VenueWitnessObservationContractError) as raised:
        build_trading_account_venue_witness_observation_v1(**fields)
    assert "observed_at/as_of" in str(raised.value) or "FIELD_MISSING" in str(raised.value)


def test_missing_is_not_present_zero() -> None:
    missing = build_trading_account_venue_witness_observation_v1(
        **_synthetic_fields(presence=PRESENCE_MISSING)
    )
    zero = build_trading_account_venue_witness_observation_v1(
        **_synthetic_fields(presence=PRESENCE_ZERO)
    )
    assert missing.presence_state == PRESENCE_MISSING
    assert zero.presence_state == PRESENCE_ZERO
    assert missing.raw_value_representation == ""
    assert zero.raw_value_representation == "0"
    assert missing.presence_state != zero.presence_state
    fields = _synthetic_fields(presence=PRESENCE_MISSING)
    fields["raw_value_representation"] = "0"
    with pytest.raises(VenueWitnessObservationContractError) as raised:
        build_trading_account_venue_witness_observation_v1(
            **attach_venue_witness_provenance_digest_v1(fields)
        )
    assert "MISSING_MUST_HAVE_EMPTY_RAW" in str(raised.value)


def test_empty_is_not_present_zero() -> None:
    empty = build_trading_account_venue_witness_observation_v1(
        **_synthetic_fields(presence=PRESENCE_EMPTY)
    )
    zero = build_trading_account_venue_witness_observation_v1(
        **_synthetic_fields(presence=PRESENCE_ZERO)
    )
    assert empty.presence_state == PRESENCE_EMPTY
    assert zero.presence_state == PRESENCE_ZERO
    assert empty.raw_value_representation == ""
    assert empty.presence_state != zero.presence_state


def test_malformed_is_not_present_zero() -> None:
    malformed = build_trading_account_venue_witness_observation_v1(
        **_synthetic_fields(presence=PRESENCE_MALFORMED)
    )
    zero = build_trading_account_venue_witness_observation_v1(
        **_synthetic_fields(presence=PRESENCE_ZERO)
    )
    assert malformed.presence_state == PRESENCE_MALFORMED
    assert malformed.raw_value_representation == "not-a-decimal"
    assert malformed.presence_state != zero.presence_state
    fields = _synthetic_fields(presence=PRESENCE_MALFORMED)
    fields["raw_value_representation"] = "0"
    with pytest.raises(VenueWitnessObservationContractError) as raised:
        build_trading_account_venue_witness_observation_v1(
            **attach_venue_witness_provenance_digest_v1(fields)
        )
    assert "MALFORMED_REQUIRES_NON_DECIMAL_RAW" in str(raised.value)


def test_raw_payload_retained_and_digest_only_are_distinct() -> None:
    digest_only = build_trading_account_venue_witness_observation_v1(**_synthetic_fields())
    retained_fields = _synthetic_fields(
        raw_payload_state=RAW_PAYLOAD_RETAINED,
        raw_payload=_SYNTHETIC_PAYLOAD,
        payload_digest=hashlib.sha256(_SYNTHETIC_PAYLOAD.encode("utf-8")).hexdigest(),
        response_provenance="SYNTHETIC_GET_RESPONSE_RAW_RETAINED",
    )
    retained = build_trading_account_venue_witness_observation_v1(**retained_fields)
    assert digest_only.raw_payload_state == PAYLOAD_DIGEST_ONLY
    assert retained.raw_payload_state == RAW_PAYLOAD_RETAINED
    assert digest_only.raw_payload == ""
    assert retained.raw_payload == _SYNTHETIC_PAYLOAD
    assert digest_only.raw_payload_state != retained.raw_payload_state


def test_digest_only_cannot_claim_raw_payload_retained() -> None:
    fields = _synthetic_fields()
    fields["raw_payload"] = _SYNTHETIC_PAYLOAD
    with pytest.raises(VenueWitnessObservationContractError) as raised:
        build_trading_account_venue_witness_observation_v1(
            **attach_venue_witness_provenance_digest_v1(fields)
        )
    assert "DIGEST_ONLY_CANNOT_CLAIM_RAW_PAYLOAD" in str(raised.value)


def test_forbidden_optimistic_fallback_chain_does_not_exist() -> None:
    fields = _synthetic_fields()
    fields["raw_field_path"] = _FORBIDDEN_FALLBACK
    with pytest.raises(VenueWitnessObservationContractError) as raised:
        build_trading_account_venue_witness_observation_v1(
            **attach_venue_witness_provenance_digest_v1(fields)
        )
    assert "FALLBACK_CHAIN_FORBIDDEN" in str(raised.value)
    inspect_source = (
        REPO_ROOT
        / "src/ops/governed_productive_account_equity_authority_producer_v1"
        / "venue_witness_observation_v1.py"
    ).read_text(encoding="utf-8")
    assert "totalEq or eq or adjEq" not in inspect_source
    assert 'row.get("totalEq") or row.get("eq")' not in inspect_source


def test_raw_field_path_is_preserved_exactly() -> None:
    witness = build_trading_account_venue_witness_observation_v1(
        **_synthetic_fields(raw_field_path="details.availEq")
    )
    assert witness.raw_field_path == "details.availEq"
    assert witness.observation_semantic_class != "details.availEq"
    assert witness.observation_semantic_class == OBSERVATION_SEMANTIC_CLASS


def test_object_authority_class_is_observation_only() -> None:
    witness = build_trading_account_venue_witness_observation_v1(**_synthetic_fields())
    assert witness.observation_vs_authority_class == "OBSERVATION"
    assert witness.observation_authority_effect == "NONE"
    assert OBSERVATION_AUTHORITY_EFFECT == "NONE"
    fields = _synthetic_fields()
    fields["observation_vs_authority_class"] = "AUTHORITY"
    with pytest.raises(VenueWitnessObservationContractError) as raised:
        build_trading_account_venue_witness_observation_v1(
            **attach_venue_witness_provenance_digest_v1(fields)
        )
    assert "AUTHORITY_CLASS_FORBIDDEN" in str(raised.value)


def test_mapping_and_equity_dimension_remain_unbound() -> None:
    witness = build_trading_account_venue_witness_observation_v1(**_synthetic_fields())
    assert witness.mapping_status == MAPPING_STATUS_UNBOUND
    assert witness.equity_dimension_bound_status == EQUITY_DIMENSION_BOUND_STATUS_UNBOUND
    assert EQUITY_DIMENSION_BOUND is False
    assert MAPPED_TO_RUNNING_ACCOUNT_EQUITY_AVAILABLE_FOR_SIZING is False
    fields = _synthetic_fields()
    fields["mapping_status"] = "BOUND"
    with pytest.raises(VenueWitnessObservationContractError) as raised:
        build_trading_account_venue_witness_observation_v1(
            **attach_venue_witness_provenance_digest_v1(fields)
        )
    assert "MAPPING_STATUS_MUST_REMAIN_UNBOUND" in str(raised.value)
    fields = _synthetic_fields()
    fields["observation_semantic_class"] = "RUNNING_ACCOUNT_EQUITY_AVAILABLE_FOR_SIZING"
    with pytest.raises(VenueWitnessObservationContractError) as raised:
        build_trading_account_venue_witness_observation_v1(
            **attach_venue_witness_provenance_digest_v1(fields)
        )
    assert "SEMANTIC_CLASS_NOT_RAW_VENUE_OBSERVATION" in str(raised.value)


def test_schema_creation_does_not_select_source_or_mapping_or_producer() -> None:
    build_trading_account_venue_witness_observation_v1(**_synthetic_fields())
    assert SOURCE_SELECTED is False
    assert MAPPING_PROVEN is False
    assert SOURCE_OBJECT_PRESENT is False
    assert GOVERNED_PRODUCER_CREATED is False
    assert GOVERNED_PRODUCTIVE_SOURCE_PRESENT is False
    assert RUNTIME_VALUE_BINDING_PRESENT is False
    assert LIVE_ACCOUNT_BOUND_JOIN_PRESENT is False
    assert RAW_TO_WITNESS_PROVEN is False
    dag = live_admission_gap_dag_v1()
    assert dag["SOURCE_SELECTED"] is False
    assert dag["MAPPING_PROVEN"] is False
    assert dag["VENUE_WITNESS_SCHEMA_PRESENT"] is True
    assert dag["VENUE_WITNESS_RUNTIME_INSTANCE_PRESENT"] is False
    assert dag["VENUE_WITNESS_SELECTED"] is False
    assert dag["WITNESS_CONTRACT_MISSING_CLOSED"] is True
    assert dag["RAW_TO_WITNESS_PROVEN"] is False
    assert dag["EARLIEST_UNRESOLVED_FULL_CORE_DEPENDENCY"] == (
        "NO_CANONICALLY_VALID_ACCOUNT_EQUITY_SOURCE_MAPPING"
    )
    assert EARLIEST_UNRESOLVED_FULL_CORE_DEPENDENCY == (
        "NO_CANONICALLY_VALID_ACCOUNT_EQUITY_SOURCE_MAPPING"
    )
    assert dag["EARLIEST_DECOMPOSED_CONTRACT_GAP"] == ("INTERNAL_RECONSTRUCTION_CONTRACT_MISSING")
    assert EARLIEST_DECOMPOSED_CONTRACT_GAP == "INTERNAL_RECONSTRUCTION_CONTRACT_MISSING"


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


def test_runbook_x_consumes_go_without_rewriting_w() -> None:
    runbook = RUNBOOK.read_text(encoding="utf-8")
    spec = SPEC_PATH.read_text(encoding="utf-8")
    w_start = runbook.index(W_HEADING)
    x_section = _x_section()
    w_section = runbook[w_start : runbook.index(X_HEADING, w_start)]
    assert "GOVERNED_RUNNING_ACCOUNT_EQUITY_SAMPLE_SCHEMA_PRESENT=true" in w_section
    assert "THIS_SLICE=11.2.1.X" not in w_section
    assert (
        "OWNER_GO=OWNER_GO_PEAK_TRADE_FULL_CORE_TYPED_VENUE_WITNESS_OBSERVATION_CONTRACT_V1"
        in x_section
    )
    assert "OWNER_GO_STATUS=CONSUMED" in x_section
    assert "VENUE_WITNESS_SCHEMA_PRESENT=true" in x_section
    assert "VENUE_WITNESS_RUNTIME_INSTANCE_PRESENT=false" in x_section
    assert "VENUE_WITNESS_SELECTED=false" in x_section
    assert "RAW_TO_WITNESS_PROVEN=false" in x_section
    assert "EQUITY_DIMENSION_BOUND=false" in x_section
    assert "SOURCE_OBJECT_PRESENT=false" in x_section
    assert "SOURCE_SELECTED=false" in x_section
    assert "MAPPING_PROVEN=false" in x_section
    assert "GOVERNED_PRODUCER_CREATED=false" in x_section
    assert "RUNTIME_VALUE_BINDING_PRESENT=false" in x_section
    assert "LIVE_ACCOUNT_BOUND_JOIN_PRESENT=false" in x_section
    assert "STEP_29P_RISK_ADMISSIBLE=false" in x_section
    assert "LIVE_ENABLED=false" in x_section
    assert "LIVE_ARMED=false" in x_section
    assert "WIRE_SEND_PERMITTED=false" in x_section
    assert "WITNESS_CONTRACT_MISSING_CLOSED=true" in x_section
    assert (
        "EARLIEST_UNRESOLVED_FULL_CORE_DEPENDENCY="
        "NO_CANONICALLY_VALID_ACCOUNT_EQUITY_SOURCE_MAPPING" in x_section
    )
    assert "EARLIEST_DECOMPOSED_CONTRACT_GAP=NORMALIZATION_CONTRACT_MISSING" in x_section
    assert "DOCS_TOKEN_FULL_CORE_TYPED_VENUE_WITNESS_OBSERVATION_CONTRACT_V1" in spec
    assert "VENUE_WITNESS_SCHEMA_PRESENT=true" in spec
    assert "SOURCE_SELECTED=false" in spec
    assert "MAPPING_PROVEN=false" in spec
    assert "GOVERNED_PRODUCER_CREATED=false" in spec
    assert WITNESS_CONTRACT_MISSING_CLOSED is True
