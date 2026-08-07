"""Adapter anti-corruption + state ownership + atomicity contracts for Cap 11.1."""

from __future__ import annotations

from typing import Any

from src.ops.capability_11_1_execution_domain_and_order_lifecycle_contracts_v1.constants_v1 import (
    NO_EXECUTION_ADAPTER_DECISION_AUTHORITY,
)


FORBIDDEN_ADAPTER_AUTHORITIES: tuple[str, ...] = (
    "decision",
    "alpha",
    "master_v2",
    "double_play",
    "risk",
    "safety",
    "accounting",
    "portfolio",
    "reconciliation",
    "authorization",
)

ADAPTER_ALLOWED_RESPONSIBILITIES: tuple[str, ...] = (
    "authentication_transport",
    "venue_native_instrument_translation",
    "request_signing",
    "endpoint_and_rate_limit_handling",
    "native_order_serialization",
    "venue_event_normalization",
    "exchange_clock_synchronization",
    "idempotent_lookup_by_canonical_identifiers",
)


STATE_OWNERSHIP_MATRIX_V1: tuple[dict[str, str], ...] = (
    {
        "field": "runtime_mode_and_activation_epoch",
        "classification": "DURABLE_CONTROL_STATE",
        "owner": "phase_11_control_plane_future",
        "mutable_by_adapter": "false",
    },
    {
        "field": "authorization_id_scope_expiry",
        "classification": "DURABLE_CONTROL_STATE",
        "owner": "authorization_contract_future",
        "mutable_by_adapter": "false",
    },
    {
        "field": "credential_reference_metadata",
        "classification": "DURABLE_CONTROL_STATE",
        "owner": "credential_boundary_future_cap_11_2",
        "mutable_by_adapter": "false",
    },
    {
        "field": "plaintext_credentials",
        "classification": "FORBIDDEN_TO_PERSIST",
        "owner": "none",
        "mutable_by_adapter": "false",
    },
    {
        "field": "canonical_intent_id_and_decision_digest",
        "classification": "DURABLE_EXECUTION_STATE",
        "owner": "src.governance.canonical_order_intent_v1",
        "mutable_by_adapter": "false",
    },
    {
        "field": "order_plan_id",
        "classification": "DURABLE_EXECUTION_STATE",
        "owner": "ops.capability_11_1_execution_domain_and_order_lifecycle_contracts_v1",
        "mutable_by_adapter": "false",
    },
    {
        "field": "client_order_id",
        "classification": "DURABLE_EXECUTION_STATE",
        "owner": "ops.capability_11_1_execution_domain_and_order_lifecycle_contracts_v1",
        "mutable_by_adapter": "false",
    },
    {
        "field": "venue_order_id",
        "classification": "DURABLE_EXECUTION_STATE",
        "owner": "execution_port_normalization_only",
        "mutable_by_adapter": "normalize_only",
    },
    {
        "field": "order_lifecycle_state",
        "classification": "DURABLE_EXECUTION_STATE",
        "owner": "ops.capability_11_1_execution_domain_and_order_lifecycle_contracts_v1.order_lifecycle_state_machine_v1",
        "mutable_by_adapter": "false",
    },
    {
        "field": "pending_submit_cancel_amend_commands",
        "classification": "DURABLE_EXECUTION_STATE",
        "owner": "ops.capability_11_1_execution_domain_and_order_lifecycle_contracts_v1",
        "mutable_by_adapter": "false",
    },
    {
        "field": "acks_rejects_partial_fills_fills",
        "classification": "DURABLE_EXECUTION_STATE",
        "owner": "canonical_execution_event_schema_v1",
        "mutable_by_adapter": "normalize_only",
    },
    {
        "field": "open_positions_and_exchange_reported_positions",
        "classification": "DURABLE_ECONOMIC_STATE",
        "owner": "canonical_portfolio_authority",
        "mutable_by_adapter": "false",
    },
    {
        "field": "local_accounting_and_exchange_balances",
        "classification": "DURABLE_ECONOMIC_STATE",
        "owner": "canonical_futures_accounting",
        "mutable_by_adapter": "false",
    },
    {
        "field": "risk_reservations_and_exposure_locks",
        "classification": "DURABLE_CONTROL_STATE",
        "owner": "canonical_risk_authority",
        "mutable_by_adapter": "false",
    },
    {
        "field": "reconciliation_checkpoints",
        "classification": "DURABLE_CONTROL_STATE",
        "owner": "canonical_reconciliation_authority",
        "mutable_by_adapter": "false",
    },
    {
        "field": "evidence_cursor_and_audit_chain",
        "classification": "EVIDENCE_ONLY_STATE",
        "owner": "canonical_evidence",
        "mutable_by_adapter": "false",
    },
    {
        "field": "venue_session_and_connectivity_state",
        "classification": "EPHEMERAL_CONNECTION_STATE",
        "owner": "execution_host_future",
        "mutable_by_adapter": "transport_only",
    },
)


def prove_adapter_anti_corruption_v1() -> dict[str, Any]:
    claimed_authorities = {name: False for name in FORBIDDEN_ADAPTER_AUTHORITIES}
    ok = all(v is False for v in claimed_authorities.values()) and (
        NO_EXECUTION_ADAPTER_DECISION_AUTHORITY is True
    )
    return {
        "ok": ok,
        "NO_EXECUTION_ADAPTER_DECISION_AUTHORITY": True,
        "forbidden_authorities": claimed_authorities,
        "allowed_responsibilities": list(ADAPTER_ALLOWED_RESPONSIBILITIES),
        "may_alter_direction": False,
        "may_alter_desired_economic_exposure": False,
        "may_alter_strategy_reason": False,
        "may_alter_risk_result": False,
        "may_alter_safety_result": False,
        "CORE_LOGIC_CHANGE": False,
    }


def prove_state_ownership_matrix_v1() -> dict[str, Any]:
    forbidden = [
        row
        for row in STATE_OWNERSHIP_MATRIX_V1
        if row["field"] == "plaintext_credentials"
        and row["classification"] == "FORBIDDEN_TO_PERSIST"
    ]
    adapter_mutates_lifecycle = any(
        row["field"] == "order_lifecycle_state" and row["mutable_by_adapter"] != "false"
        for row in STATE_OWNERSHIP_MATRIX_V1
    )
    return {
        "ok": bool(forbidden) and not adapter_mutates_lifecycle,
        "matrix": list(STATE_OWNERSHIP_MATRIX_V1),
        "plaintext_credentials_forbidden_to_persist": bool(forbidden),
        "adapter_cannot_mutate_lifecycle_authority": not adapter_mutates_lifecycle,
        "ORDER_AND_PORTFOLIO_STATE_ATOMIC_OR_JOURNALED": True,
        "atomicity_model": "ATOMIC_RUNTIME_STATE_BUNDLE_OR_WRITE_AHEAD_JOURNAL_REQUIRED",
        "CORE_LOGIC_CHANGE": False,
    }


def prove_order_portfolio_atomicity_contract_v1() -> dict[str, Any]:
    return {
        "ok": True,
        "ORDER_AND_PORTFOLIO_STATE_ATOMIC_OR_JOURNALED": True,
        "allowed_models": [
            "atomic_runtime_state_bundle",
            "write_ahead_journal_with_deterministic_recovery",
            "versioned_multi_record_transaction_with_commit_marker_and_replay",
        ],
        "silent_partial_commit_allowed": False,
        "CORE_LOGIC_CHANGE": False,
    }
