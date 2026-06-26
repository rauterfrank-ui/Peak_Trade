"""Offline OKX Europe adapter lifecycle contract tests (v0, Package E / INV-033 E2)."""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path

import pytest

from src.ops.bounded_futures_testnet_venue_binding_v0 import (
    DEMO_REFERENCE_INSTRUMENT_ID,
    OKX_EUROPE_ADAPTER_LIFECYCLE_CONTRACT_VERSION,
    PRODUCTION_INSTRUMENT_ID,
    REGULATORY_MAX_RETAIL_LEVERAGE,
    VENUE_OKX_EUROPE,
    VENUE_REPORTED_LEVERAGE_CAPABILITY,
    default_okx_europe_xperp_production_binding,
    offline_adapter_capability_descriptor,
)
from src.ops.okx_europe_adapter_lifecycle_contract_v0 import (
    AUTOMATIC_INSTRUMENT_ROLLOVER_ALLOWED,
    AUTOMATIC_ORDER_RESEND_ALLOWED,
    AuthCapabilityKind,
    CancelStateContract,
    ClientOrderIdContract,
    CONTRACT_VERSION,
    DurableEvidenceRecord,
    NormalizedFill,
    NormalizedOrderState,
    NormalizedPosition,
    PACKAGE_MARKER,
    ReconciliationResult,
    ReconciliationTrigger,
    RUNTIME_GO_READY,
    SettlementState,
    allows_automatic_order_resend,
    assert_contract_inert,
    build_client_order_id,
    cancel_ack_implies_canceled_confirmed,
    default_auth_capability,
    default_xperp_demo_position,
    evaluate_offline_contract_invariants,
    get_reconciliation_policy,
    normalize_okx_order_state,
    reject_secret_payload,
    validate_auth_capability,
    validate_cancel_state,
    validate_client_order_id_contract,
    validate_durable_evidence,
    validate_fill,
    validate_order_state_transition,
    validate_position,
    validate_reconciliation_policy,
)

TEST_PACKAGE_MARKER = "OKX_EUROPE_ADAPTER_LIFECYCLE_CONTRACT_TEST_GUARD_V0=true"
REPO_ROOT = Path(__file__).resolve().parents[2]
CONTRACT_MODULE = REPO_ROOT / "src" / "ops" / "okx_europe_adapter_lifecycle_contract_v0.py"


def _client_order_id(**overrides: object) -> ClientOrderIdContract:
    base = ClientOrderIdContract(
        client_order_id=build_client_order_id(
            run_id="a" * 40,
            session_id="sess-001",
            intent_id="b" * 40,
            environment="testnet",
            instrument_id=DEMO_REFERENCE_INSTRUMENT_ID,
        ),
        run_id="a" * 40,
        session_id="sess-001",
        intent_id="b" * 40,
        venue=VENUE_OKX_EUROPE,
        environment="testnet",
        instrument_id=DEMO_REFERENCE_INSTRUMENT_ID,
        uniqueness_scope="session_intent",
        maximum_length=32,
        allowed_character_contract="alphanumeric_case_sensitive",
        deterministic_derivation=True,
        reusable_after_terminal_state=False,
        resend_allowed=False,
        reconciliation_required_before_resend=True,
    )
    return replace(base, **overrides)  # type: ignore[arg-type]


def _fill(**overrides: object) -> NormalizedFill:
    base = NormalizedFill(
        exchange_fill_id="trade-1",
        exchange_order_id="ord-1",
        client_order_id="ptokxetest00000001",
        instrument_id=DEMO_REFERENCE_INSTRUMENT_ID,
        fill_timestamp="1700000000000",
        fill_price=2500.0,
        fill_size=1.0,
        fee=-0.01,
        fee_asset="USD",
        liquidity_role="T",
        cumulative_filled_size=1.0,
        remaining_size=0.0,
        normalized_order_state_after_fill=NormalizedOrderState.FILLED,
    )
    return replace(base, **overrides)  # type: ignore[arg-type]


def _durable_evidence(**overrides: object) -> DurableEvidenceRecord:
    base = DurableEvidenceRecord(
        run_id="run-001",
        session_id="sess-001",
        intent_id="intent-001",
        client_order_id="ptokxetest00000001",
        exchange_order_id=None,
        instrument_id=DEMO_REFERENCE_INSTRUMENT_ID,
        environment="testnet",
        venue=VENUE_OKX_EUROPE,
        regulatory_entity="OKX Europe Markets Limited",
        request_timestamp="2026-06-26T22:00:00Z",
        exchange_timestamp=None,
        receive_timestamp="2026-06-26T22:00:01Z",
        order_state_before=NormalizedOrderState.REQUEST_SENT.value,
        order_state_after=NormalizedOrderState.UNKNOWN_REMOTE_STATE.value,
        position_state_before=None,
        position_state_after=None,
        reconciliation_reason="ORDER_REQUEST_TIMEOUT",
        reconciliation_result=ReconciliationResult.AMBIGUOUS,
        source_endpoint="/api/v5/trade/order",
        source_channel="rest",
        retry_count=1,
        rate_limit_state="ok",
        credential_scope_used="readonly_private",
        secret_redaction_proven=True,
        production_demo_separation_proven=True,
        runtime_go_token=None,
        operator_identity="Frank Rauter",
    )
    return replace(base, **overrides)  # type: ignore[arg-type]


def test_package_marker_present() -> None:
    assert TEST_PACKAGE_MARKER in Path(__file__).read_text(encoding="utf-8")
    assert PACKAGE_MARKER in CONTRACT_MODULE.read_text(encoding="utf-8")


def test_global_inert_flags() -> None:
    assert RUNTIME_GO_READY is False
    assert AUTOMATIC_ORDER_RESEND_ALLOWED is False
    assert AUTOMATIC_INSTRUMENT_ROLLOVER_ALLOWED is False
    assert_contract_inert()
    result = evaluate_offline_contract_invariants()
    assert result["contract_pass"] is True


def test_venue_binding_lifecycle_hook() -> None:
    binding = default_okx_europe_xperp_production_binding()
    descriptor = offline_adapter_capability_descriptor(binding)
    assert descriptor["okx_europe_adapter_lifecycle_contract_version"] == (
        OKX_EUROPE_ADAPTER_LIFECYCLE_CONTRACT_VERSION
    )
    assert CONTRACT_VERSION == "okx_europe_adapter_lifecycle.v0"


# --- AUTH POSITIVE ---


def test_public_capability_without_credentials() -> None:
    cap = default_auth_capability(AuthCapabilityKind.PUBLIC_CAPABILITY)
    assert validate_auth_capability(cap) == []
    assert cap.authentication_required is False
    assert cap.order_authority is False


def test_readonly_private_without_order_authority() -> None:
    cap = default_auth_capability(AuthCapabilityKind.READONLY_PRIVATE_CAPABILITY)
    assert validate_auth_capability(cap) == []
    assert cap.account_read_authority is True
    assert cap.order_authority is False


def test_trade_capability_runtime_inert() -> None:
    cap = default_auth_capability(AuthCapabilityKind.TRADE_CAPABILITY)
    assert validate_auth_capability(cap) == []
    assert cap.order_authority is True
    assert cap.runtime_go_required is False


def test_auth_uses_reference_semantics_not_values() -> None:
    cap = default_auth_capability(AuthCapabilityKind.TRADE_CAPABILITY)
    assert cap.api_key_reference_required is True
    assert cap.secret_reference_required is True
    assert cap.passphrase_reference_required is True


def test_secret_redaction_invariant() -> None:
    assert reject_secret_payload({"api_key": "x"}) != []
    assert reject_secret_payload({"run_id": "ok"}) == []


# --- AUTH NEGATIVE ---


def test_readonly_with_order_authority_fails() -> None:
    cap = replace(
        default_auth_capability(AuthCapabilityKind.READONLY_PRIVATE_CAPABILITY),
        order_authority=True,
    )
    assert any("order authority" in r for r in validate_auth_capability(cap))


def test_trade_runtime_go_fails() -> None:
    cap = replace(
        default_auth_capability(AuthCapabilityKind.TRADE_CAPABILITY), runtime_go_required=True
    )
    assert any("runtime_go_required" in r for r in validate_auth_capability(cap))


def test_public_with_auth_required_fails() -> None:
    cap = replace(
        default_auth_capability(AuthCapabilityKind.PUBLIC_CAPABILITY), authentication_required=True
    )
    assert validate_auth_capability(cap)


# --- CLIENT ORDER ID POSITIVE ---


def test_valid_deterministic_client_order_id() -> None:
    cid = build_client_order_id(
        run_id="abc123def456" * 3 + "abcd",
        session_id="s1",
        intent_id="fed987654321" * 3 + "fed9",
        environment="testnet",
        instrument_id=DEMO_REFERENCE_INSTRUMENT_ID,
    )
    contract = _client_order_id(client_order_id=cid)
    assert validate_client_order_id_contract(contract) == []
    assert len(cid) <= 32


def test_production_demo_namespace_separated() -> None:
    demo = _client_order_id(environment="testnet", instrument_id=DEMO_REFERENCE_INSTRUMENT_ID)
    assert validate_client_order_id_contract(demo) == []
    prod = _client_order_id(environment="production", instrument_id=PRODUCTION_INSTRUMENT_ID)
    assert validate_client_order_id_contract(prod) == []


def test_reconciliation_before_resend_required() -> None:
    contract = _client_order_id(resend_allowed=True, reconciliation_required_before_resend=True)
    assert validate_client_order_id_contract(contract) == []


# --- CLIENT ORDER ID NEGATIVE ---


def test_client_order_id_too_long() -> None:
    contract = _client_order_id(client_order_id="x" * 33, maximum_length=32)
    assert any("maximum_length" in r for r in validate_client_order_id_contract(contract))


def test_client_order_id_invalid_chars() -> None:
    contract = _client_order_id(client_order_id="bad-id-with-dashes!!")
    assert any("allowed_character" in r for r in validate_client_order_id_contract(contract))


def test_missing_intent_id() -> None:
    contract = _client_order_id(intent_id="")
    assert any("intent_id" in r for r in validate_client_order_id_contract(contract))


def test_demo_instrument_in_production_env_fails() -> None:
    contract = _client_order_id(
        environment="production", instrument_id=DEMO_REFERENCE_INSTRUMENT_ID
    )
    assert validate_client_order_id_contract(contract)


def test_resend_without_reconciliation_fails() -> None:
    contract = _client_order_id(resend_allowed=True, reconciliation_required_before_resend=False)
    assert validate_client_order_id_contract(contract)


def test_unknown_remote_state_blocks_auto_resend() -> None:
    assert allows_automatic_order_resend(NormalizedOrderState.UNKNOWN_REMOTE_STATE) is False


# --- ORDER POSITIVE ---


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("live", NormalizedOrderState.LIVE),
        ("partially_filled", NormalizedOrderState.PARTIALLY_FILLED),
        ("filled", NormalizedOrderState.FILLED),
        ("canceled", NormalizedOrderState.CANCELED),
        ("mmp_canceled", NormalizedOrderState.CANCELED),
    ],
)
def test_okx_states_normalize(raw: str, expected: NormalizedOrderState) -> None:
    assert normalize_okx_order_state(raw) == expected


def test_valid_order_transitions() -> None:
    assert (
        validate_order_state_transition(
            NormalizedOrderState.REQUEST_SENT, NormalizedOrderState.UNKNOWN_REMOTE_STATE
        )
        == []
    )
    assert (
        validate_order_state_transition(
            NormalizedOrderState.CANCEL_PENDING, NormalizedOrderState.PARTIALLY_FILLED
        )
        == []
    )


def test_partial_fill_during_cancel_pending() -> None:
    assert (
        validate_order_state_transition(
            NormalizedOrderState.CANCEL_PENDING, NormalizedOrderState.PARTIALLY_FILLED
        )
        == []
    )


def test_expired_distinct_from_canceled_mapping() -> None:
    assert NormalizedOrderState.EXPIRED != NormalizedOrderState.CANCELED
    assert (
        validate_order_state_transition(NormalizedOrderState.LIVE, NormalizedOrderState.EXPIRED)
        == []
    )


# --- ORDER NEGATIVE ---


def test_unknown_okx_state_fail_closed() -> None:
    assert normalize_okx_order_state("working") == NormalizedOrderState.UNKNOWN_REMOTE_STATE
    assert normalize_okx_order_state("") == NormalizedOrderState.UNKNOWN_REMOTE_STATE


def test_invalid_transition_rejected() -> None:
    assert validate_order_state_transition(
        NormalizedOrderState.REQUEST_SENT, NormalizedOrderState.LIVE
    )


def test_timeout_not_auto_live() -> None:
    assert validate_order_state_transition(
        NormalizedOrderState.REQUEST_SENT, NormalizedOrderState.LIVE
    )


def test_filled_not_canceled() -> None:
    assert validate_order_state_transition(
        NormalizedOrderState.FILLED, NormalizedOrderState.CANCELED
    )


def test_unknown_cannot_spawn_new_intent() -> None:
    assert validate_order_state_transition(
        NormalizedOrderState.UNKNOWN_REMOTE_STATE, NormalizedOrderState.REQUEST_PREPARED
    )


# --- CANCEL ---


def test_cancel_ack_not_canceled_confirmed() -> None:
    cancel = CancelStateContract(
        cancel_requested=True,
        cancel_acknowledged=True,
        canceled_confirmed=False,
        cancel_by_exchange_order_id="ord-1",
        cancel_by_client_order_id=None,
        order_state_before_cancel=NormalizedOrderState.LIVE,
        order_state_after_cancel=NormalizedOrderState.CANCEL_PENDING,
        concurrent_fill_detected=False,
        reconciliation_required=True,
        final_state_confirmed=False,
    )
    assert validate_cancel_state(cancel) == []
    assert cancel_ack_implies_canceled_confirmed(cancel) is False


def test_cancel_ack_as_terminal_fails() -> None:
    cancel = CancelStateContract(
        cancel_requested=True,
        cancel_acknowledged=True,
        canceled_confirmed=False,
        cancel_by_client_order_id="cl-1",
        cancel_by_exchange_order_id=None,
        order_state_before_cancel=NormalizedOrderState.LIVE,
        order_state_after_cancel=NormalizedOrderState.CANCELED,
        concurrent_fill_detected=False,
        reconciliation_required=True,
        final_state_confirmed=True,
    )
    assert validate_cancel_state(cancel)
    assert cancel_ack_implies_canceled_confirmed(cancel) is True


# --- FILL POSITIVE ---


def test_consistent_full_fill() -> None:
    assert validate_fill(_fill()) == []


def test_partial_fill_accumulation() -> None:
    fill = _fill(
        fill_size=0.5,
        cumulative_filled_size=1.5,
        remaining_size=0.5,
        normalized_order_state_after_fill=NormalizedOrderState.PARTIALLY_FILLED,
    )
    assert validate_fill(fill) == []


# --- FILL NEGATIVE ---


def test_negative_fill_size() -> None:
    assert any("negative" in r for r in validate_fill(_fill(fill_size=-1.0)))


def test_decreasing_cumulative_fill() -> None:
    fill = _fill(cumulative_filled_size=0.5, fill_size=1.0)
    assert validate_fill(fill)


def test_filled_with_remaining() -> None:
    fill = _fill(remaining_size=1.0, normalized_order_state_after_fill=NormalizedOrderState.FILLED)
    assert validate_fill(fill)


# --- POSITION POSITIVE ---


def test_eth_xperp_position_passes() -> None:
    pos = default_xperp_demo_position(environment="testnet")
    assert validate_position(pos, environment="testnet") == []
    assert pos.effective_operational_leverage_cap == REGULATORY_MAX_RETAIL_LEVERAGE


def test_leverage_cap_stays_ten() -> None:
    pos = default_xperp_demo_position()
    assert pos.leverage_reported == VENUE_REPORTED_LEVERAGE_CAPABILITY
    assert pos.effective_operational_leverage_cap == 10.0


# --- POSITION NEGATIVE ---


def test_swap_forbidden() -> None:
    pos = replace(default_xperp_demo_position(), instrument_type="SWAP")
    assert validate_position(pos, environment="testnet")


def test_classic_perpetual_forbidden() -> None:
    pos = replace(default_xperp_demo_position(), is_classic_perpetual_swap=True)
    assert validate_position(pos, environment="testnet")


def test_missing_expiry_forbidden() -> None:
    pos = replace(default_xperp_demo_position(), has_fixed_expiry=False)
    assert validate_position(pos, environment="testnet")


def test_demo_as_production_instrument_fails() -> None:
    pos = replace(default_xperp_demo_position(), instrument_id=PRODUCTION_INSTRUMENT_ID)
    assert validate_position(pos, environment="testnet")


def test_operational_cap_fifty_fails() -> None:
    pos = replace(default_xperp_demo_position(), effective_operational_leverage_cap=50.0)
    assert validate_position(pos, environment="testnet")


def test_btc_instrument_forbidden() -> None:
    pos = replace(default_xperp_demo_position(), instrument_id="BTC-USD_UM_XPERP-310328")
    assert validate_position(pos, environment="testnet")


# --- RECONCILIATION POSITIVE ---


@pytest.mark.parametrize(
    "trigger",
    [
        ReconciliationTrigger.STARTUP,
        ReconciliationTrigger.ORDER_REQUEST_TIMEOUT,
        ReconciliationTrigger.CANCEL_REQUEST_TIMEOUT,
        ReconciliationTrigger.WEBSOCKET_DISCONNECT,
        ReconciliationTrigger.PROCESS_RESTART,
        ReconciliationTrigger.AWS_TASK_RESTART,
        ReconciliationTrigger.RATE_LIMIT,
        ReconciliationTrigger.PARTIAL_FILL,
        ReconciliationTrigger.INSTRUMENT_EXPIRY,
    ],
)
def test_reconciliation_policies_valid(trigger: ReconciliationTrigger) -> None:
    policy = get_reconciliation_policy(trigger)
    assert validate_reconciliation_policy(policy) == []


def test_unknown_remote_state_no_promotion() -> None:
    policy = get_reconciliation_policy(ReconciliationTrigger.UNKNOWN_REMOTE_STATE)
    assert policy.promotion_allowed is False


# --- RECONCILIATION NEGATIVE ---


def test_unbounded_retry_fails() -> None:
    policy = replace(
        get_reconciliation_policy(ReconciliationTrigger.STARTUP),
        retry_limit=100,
    )
    assert validate_reconciliation_policy(policy)


def test_clock_drift_no_mutating_retry() -> None:
    policy = replace(
        get_reconciliation_policy(ReconciliationTrigger.CLOCK_DRIFT), retry_allowed=True
    )
    assert validate_reconciliation_policy(policy)


def test_restart_missing_durable_ids_fails() -> None:
    policy = replace(
        get_reconciliation_policy(ReconciliationTrigger.PROCESS_RESTART),
        required_identifiers=("clOrdId",),
    )
    assert validate_reconciliation_policy(policy)


def test_instrument_expiry_no_promotion() -> None:
    policy = replace(
        get_reconciliation_policy(ReconciliationTrigger.INSTRUMENT_EXPIRY),
        promotion_allowed=True,
    )
    assert validate_reconciliation_policy(policy)


# --- DURABLE EVIDENCE ---


def test_durable_evidence_passes() -> None:
    assert validate_durable_evidence(_durable_evidence()) == []


def test_durable_evidence_runtime_go_forbidden() -> None:
    rec = _durable_evidence(runtime_go_token="GO_RUNTIME")
    assert validate_durable_evidence(rec)


def test_durable_evidence_separation_required() -> None:
    rec = _durable_evidence(production_demo_separation_proven=False)
    assert validate_durable_evidence(rec)


def test_settlement_state_enum() -> None:
    assert SettlementState.ACTIVE.value == "ACTIVE"
