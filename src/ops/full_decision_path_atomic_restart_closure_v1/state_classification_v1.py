"""Persist-vs-rebuild classification matrix for Cap 6.4 (forensic, non-authoritative)."""

from __future__ import annotations

from typing import Any

from src.ops.full_decision_path_atomic_restart_closure_v1.constants_v1 import (
    MEMBER_ACCOUNTING,
    MEMBER_CONFIRMATION,
    MEMBER_DECISION_CONFIG,
    MEMBER_DYNAMIC_SCOPE,
    MEMBER_RECONCILIATION_REF,
    MEMBER_SELECTION_REF,
    MEMBER_VOLATILITY_REF,
    OWNER,
    PREDECESSOR_CAP31,
    PREDECESSOR_CAP61,
    PREDECESSOR_CAP62,
    PREDECESSOR_CAPABILITY,
)


def build_state_root_classification_matrix_v1() -> list[dict[str, Any]]:
    """Classify every required decision-path field exactly once."""
    return [
        {
            "field": "c1_observation_acceptance_state",
            "state_root": MEMBER_CONFIRMATION,
            "owner": PREDECESSOR_CAP61,
            "writer": "ConfirmationStateSingleWriterV1",
            "classification": "PERSIST_DIRECTLY",
            "reason": "epoch/cursor continuity requires durable C1 state",
        },
        {
            "field": "c2_c3_confirmation_side_carrier",
            "state_root": MEMBER_CONFIRMATION,
            "owner": PREDECESSOR_CAP61,
            "writer": "ConfirmationStateSingleWriterV1",
            "classification": "PERSIST_DIRECTLY",
            "reason": "candidate/confirmed continuity across restart",
        },
        {
            "field": "confirmation_session_id",
            "state_root": MEMBER_CONFIRMATION,
            "owner": PREDECESSOR_CAP61,
            "writer": "ConfirmationStateSingleWriterV1",
            "classification": "PERSIST_DIRECTLY",
            "reason": "stable session identity; silent reinit forbidden",
        },
        {
            "field": "runtime_scope_state",
            "state_root": MEMBER_DYNAMIC_SCOPE,
            "owner": PREDECESSOR_CAP62,
            "writer": "DynamicScopeStateSingleWriterV1",
            "classification": "PERSIST_DIRECTLY",
            "reason": "trailing/envelope SSOT restore",
        },
        {
            "field": "canonical_scope_snapshot",
            "state_root": MEMBER_DYNAMIC_SCOPE,
            "owner": PREDECESSOR_CAP62,
            "writer": "DynamicScopeStateSingleWriterV1",
            "classification": "PERSIST_DIRECTLY",
            "reason": "scope continuity; no silent None reset",
        },
        {
            "field": "master_v2_double_play_carrier_required",
            "state_root": MEMBER_DYNAMIC_SCOPE,
            "owner": PREDECESSOR_CAP62,
            "writer": "DynamicScopeStateSingleWriterV1",
            "classification": "PERSIST_DIRECTLY",
            "reason": "only RuntimeScopeState / CanonicalScopeSnapshot; no new MV2 domain",
        },
        {
            "field": "decision_runtime_config_digest",
            "state_root": MEMBER_DECISION_CONFIG,
            "owner": PREDECESSOR_CAPABILITY,
            "writer": "ops.decision_config_ownership_and_consumer_closure_v1",
            "classification": "PERSIST_DIRECTLY",
            "reason": "config digest bind + mismatch fail-closed",
        },
        {
            "field": "portfolio_accounting_state",
            "state_root": MEMBER_ACCOUNTING,
            "owner": PREDECESSOR_CAP31,
            "writer": "ProductiveFuturesAccountingSingleWriterV1",
            "classification": "PERSIST_DIRECTLY",
            "reason": "economic continuity; no portfolio rollback",
        },
        {
            "field": "fill_ledger_idempotency",
            "state_root": MEMBER_ACCOUNTING,
            "owner": PREDECESSOR_CAP31,
            "writer": "ProductiveFuturesAccountingSingleWriterV1",
            "classification": "PERSIST_DIRECTLY",
            "reason": "duplicate fill prevention",
        },
        {
            "field": "selection_state_reference",
            "state_root": MEMBER_SELECTION_REF,
            "owner": "ops.single_selected_future_runtime_binding_v1",
            "writer": "selection_binding_writer",
            "classification": "PERSIST_DIRECTLY",
            "reason": "reference only; Cap 2.4 remains sole selection authority",
        },
        {
            "field": "reconciliation_state_reference",
            "state_root": MEMBER_RECONCILIATION_REF,
            "owner": "ops.productive_reconciliation_startup_gate_v1",
            "writer": "reconciliation_writer",
            "classification": "PERSIST_DIRECTLY",
            "reason": "reconciliation-before-alpha after restart",
        },
        {
            "field": "volatility_state_reference",
            "state_root": MEMBER_VOLATILITY_REF,
            "owner": "typed_volatility_persistence_where_configured",
            "writer": "volatility_writer",
            "classification": "PERSIST_DIRECTLY",
            "reason": "reference digest only; no parallel volatility model",
        },
        {
            "field": "runtime_commit_position",
            "state_root": "decision_path_atomic",
            "owner": OWNER,
            "writer": "DecisionPathAtomicSingleWriterV1",
            "classification": "PERSIST_DIRECTLY",
            "reason": "coordinator commit marker / sequence",
        },
        {
            "field": "pending_evidence_cursor",
            "state_root": "decision_path_atomic",
            "owner": OWNER,
            "writer": "DecisionPathAtomicSingleWriterV1",
            "classification": "PERSIST_DIRECTLY",
            "reason": "evidence durability separate from economic commit",
        },
        {
            "field": "feature_vectors",
            "state_root": "derived",
            "owner": "feature_pipeline",
            "writer": "none",
            "classification": "REBUILD_DETERMINISTICALLY",
            "reason": "rebuilt from persisted mid/price path + observations",
        },
        {
            "field": "regime_derived",
            "state_root": "derived",
            "owner": "regime_pipeline",
            "writer": "none",
            "classification": "REBUILD_DETERMINISTICALLY",
            "reason": "deterministic from features",
        },
        {
            "field": "unrealized_pnl",
            "state_root": "derived",
            "owner": PREDECESSOR_CAP31,
            "writer": "none",
            "classification": "REBUILD_DETERMINISTICALLY",
            "reason": "derived from position + mark",
        },
        {
            "field": "immutable_config_rule_objects",
            "state_root": "derived",
            "owner": PREDECESSOR_CAPABILITY,
            "writer": "none",
            "classification": "REBUILD_DETERMINISTICALLY",
            "reason": "loaded from typed config owner by digest",
        },
        {
            "field": "transport_metadata",
            "state_root": "ephemeral",
            "owner": "market_data_transport",
            "writer": "none",
            "classification": "EPHEMERAL_ONLY",
            "reason": "never distinctness or decision authority",
        },
        {
            "field": "in_memory_cycle_scratch",
            "state_root": "ephemeral",
            "owner": "bridge_session",
            "writer": "none",
            "classification": "EPHEMERAL_ONLY",
            "reason": "host scratch; not restart authority",
        },
        {
            "field": "capability_evidence_artifacts",
            "state_root": "evidence",
            "owner": OWNER,
            "writer": "evidence_materializer",
            "classification": "EVIDENCE_ONLY",
            "reason": "claims/manifests; not trading-state authority",
        },
        {
            "field": "master_v2_full_decision_blob",
            "state_root": "forbidden",
            "owner": "none",
            "writer": "none",
            "classification": "FORBIDDEN_TO_PERSIST",
            "reason": "MASTER_V2_NEW_PERSISTENCE_DOMAIN_MODEL_ALLOWED=false",
        },
        {
            "field": "double_play_parallel_domain",
            "state_root": "forbidden",
            "owner": "none",
            "writer": "none",
            "classification": "FORBIDDEN_TO_PERSIST",
            "reason": "DOUBLE_PLAY_NEW_PERSISTENCE_DOMAIN_MODEL_ALLOWED=false",
        },
        {
            "field": "forced_intent_or_fill_injection",
            "state_root": "forbidden",
            "owner": "none",
            "writer": "none",
            "classification": "FORBIDDEN_TO_PERSIST",
            "reason": "FORCED_INTENT/DIRECT_FILL_INJECTION forbidden",
        },
    ]


def classify_fields_by_bucket_v1() -> dict[str, list[str]]:
    matrix = build_state_root_classification_matrix_v1()
    buckets: dict[str, list[str]] = {
        "PERSIST_DIRECTLY": [],
        "REBUILD_DETERMINISTICALLY": [],
        "EPHEMERAL_ONLY": [],
        "EVIDENCE_ONLY": [],
        "FORBIDDEN_TO_PERSIST": [],
    }
    for row in matrix:
        buckets[str(row["classification"])].append(str(row["field"]))
    return buckets
