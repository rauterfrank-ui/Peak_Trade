"""Build archive-sibling Execution/Reconciliation fields from replay commit artifacts only.

Maps already-produced canonical order-intent binding facts on cycle commit:
- ``order_intent_effect`` / ``order_intent_ref`` on finalized decision evidence
- ``canonical_order_intent`` on IntegratedOfflineReplayIntermediateV1 when bound

Does not call build_canonical_order_intent_v1 or recompute reconciliation.
"""

from __future__ import annotations

from typing import Any, Mapping

from src.ops.execution_reconciliation_archive_sibling_exporter_v1.constants_v1 import (
    ERROR_BOUND_OFFLINE_INTENT_MISSING,
    ERROR_DECISION_EVIDENCE_ABSENT,
    ERROR_INTENT_EFFECT_INCOMPLETE,
    ERROR_INTENT_REF_MISMATCH,
    ERROR_REPLAY_COMMIT_INCOMPLETE,
    ERROR_UNBOUND_INTENT_PRESENT,
    ERROR_UNBOUND_REF_PRESENT,
)
from trading.master_v2.canonical_order_intent_offline_replay_binding_adapter_v0 import (
    ORDER_INTENT_EFFECT_BOUND_OFFLINE,
    ORDER_INTENT_EFFECT_NONE,
    compute_order_intent_ref_v0,
)
from src.webui.workflow_dashboard_readmodel_v1.execution_reconciliation_presentation_projection_materializer_v1 import (
    coerce_execution_reconciliation_fields_mapping_v1,
)


def _read_str_field(source: object, key: str) -> str | None:
    if isinstance(source, Mapping):
        raw = source.get(key)
    elif hasattr(source, key):
        raw = getattr(source, key)
    else:
        return None
    if not isinstance(raw, str) or not raw.strip():
        return None
    return raw.strip()


def _read_reason_codes(source: object) -> tuple[str, ...] | None:
    if isinstance(source, Mapping):
        raw = source.get("reason_codes")
    elif hasattr(source, "reason_codes"):
        raw = getattr(source, "reason_codes")
    else:
        return None
    if raw is None:
        return ()
    if not isinstance(raw, (list, tuple)):
        return None
    return tuple(str(code) for code in raw)


def build_execution_reconciliation_sibling_payload_from_replay_commit_v1(
    *,
    replay_intermediate: object | None,
    decision_evidence: object | None,
) -> tuple[dict[str, Any] | None, tuple[str, ...]]:
    """Map replay-attached order-intent binding facts into sibling export shape."""
    if decision_evidence is None:
        return None, (ERROR_DECISION_EVIDENCE_ABSENT,)

    order_intent_effect = _read_str_field(decision_evidence, "order_intent_effect")
    if order_intent_effect is None:
        return None, (ERROR_INTENT_EFFECT_INCOMPLETE,)

    order_intent_ref = _read_str_field(decision_evidence, "order_intent_ref") or ""

    intent = None
    if replay_intermediate is not None and hasattr(replay_intermediate, "canonical_order_intent"):
        intent = getattr(replay_intermediate, "canonical_order_intent", None)

    execution_status = order_intent_effect
    raw_fields: dict[str, Any] = {
        "execution_status": execution_status,
        "schema_version": "v1",
    }

    if order_intent_effect == ORDER_INTENT_EFFECT_BOUND_OFFLINE:
        if intent is None:
            return None, (ERROR_BOUND_OFFLINE_INTENT_MISSING,)
        if not order_intent_ref:
            return None, (ERROR_INTENT_REF_MISMATCH,)
        expected_ref = compute_order_intent_ref_v0(intent)
        if order_intent_ref != expected_ref:
            return None, (ERROR_INTENT_REF_MISMATCH,)
        raw_fields["order_intent_ref"] = order_intent_ref
        raw_fields["reason_codes"] = list(intent.reason_codes)
        raw_fields["evidence_digest"] = intent.semantic_digest
        raw_fields["semantic_digest"] = intent.semantic_digest
    elif order_intent_effect == ORDER_INTENT_EFFECT_NONE:
        if intent is not None:
            return None, (ERROR_UNBOUND_INTENT_PRESENT,)
        if order_intent_ref:
            return None, (ERROR_UNBOUND_REF_PRESENT,)
        reason_codes = _read_reason_codes(decision_evidence)
        if reason_codes is None:
            return None, (ERROR_REPLAY_COMMIT_INCOMPLETE,)
        raw_fields["reason_codes"] = list(reason_codes)
    else:
        return None, (ERROR_INTENT_EFFECT_INCOMPLETE,)

    coerced, errors = coerce_execution_reconciliation_fields_mapping_v1(raw_fields)
    if coerced is None:
        return None, errors
    return dict(coerced), ()
