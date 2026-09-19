"""Productive host binding: evaluation bundle → learning state ingest (non-authorizing)."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Final, Mapping

from src.learning.deterministic_decision_outcome_v0.capture_v0 import DdoCaptureBindingV0
from src.learning.deterministic_decision_outcome_v0.learning_outcome_evidence_ingest_v1 import (
    EXTERNAL_EFFECT_AUTHORIZED,
    derive_learning_state_scope_id_v1,
    ingest_evaluation_bundle_into_learning_state_v1,
)
from src.learning.deterministic_decision_outcome_v0.ledger_v0 import AppendOnlyDdoLedgerV0

BINDING_ID: Final[str] = (
    "peak_trade.ops.wallclock_bridge.ddo_learning_outcome_evidence_ingest_host_binding_v1"
)


def _ledger_from_state(state: Any) -> AppendOnlyDdoLedgerV0 | None:
    binding = getattr(state, "ddo_capture_binding", None)
    if not isinstance(binding, DdoCaptureBindingV0) or not binding.enabled:
        return None
    if binding.ledger_path is None:
        return None
    return AppendOnlyDdoLedgerV0(Path(binding.ledger_path))


def _scope_id_from_state(state: Any, *, session_id: str) -> str:
    account = getattr(state, "ddo_account_identity_record", None)
    account_identity = None
    if account is not None:
        account_identity = str(getattr(account, "account_identity", None) or "")
    return derive_learning_state_scope_id_v1(
        session_id=session_id,
        account_identity=account_identity or None,
    )


def apply_learning_state_feedback_to_next_cycle_v1(state: Any) -> None:
    """Ratified feedback seam: opaque economic score label only."""
    snapshot = getattr(state, "last_ddo_learning_state", None)
    if not isinstance(snapshot, Mapping):
        return
    label = snapshot.get("next_cycle_economic_score_label")
    if not isinstance(label, str) or not label or label == "UNKNOWN":
        return
    state.ddo_n_bars_economic_score = label


def invoke_productive_learning_outcome_evidence_ingest_v1(
    state: Any,
    *,
    evaluation_runtime: Mapping[str, Any] | None,
    session_id: str,
    correlation_id: str | None = None,
    cycle_id: str | None = None,
) -> dict[str, Any]:
    if evaluation_runtime is None or evaluation_runtime.get("ok") is not True:
        return {
            "ok": True,
            "skipped": True,
            "reason": "EVALUATION_RUNTIME_NOT_OK",
            "external_effect_authorized": EXTERNAL_EFFECT_AUTHORIZED,
        }
    bundle_wrapper = evaluation_runtime.get("bundle")
    if not isinstance(bundle_wrapper, Mapping):
        return {
            "ok": True,
            "skipped": True,
            "reason": "EVALUATION_BUNDLE_MISSING",
            "external_effect_authorized": EXTERNAL_EFFECT_AUTHORIZED,
        }
    ledger = _ledger_from_state(state)
    if ledger is None:
        return {
            "ok": True,
            "skipped": True,
            "reason": "LEDGER_NOT_BOUND",
            "external_effect_authorized": EXTERNAL_EFFECT_AUTHORIZED,
        }
    outcome = bundle_wrapper.get("outcome_record")
    attribution = bundle_wrapper.get("attribution_record")
    counterfactual = bundle_wrapper.get("counterfactual_record")
    if not all(isinstance(row, Mapping) for row in (outcome, attribution, counterfactual)):
        return {
            "ok": True,
            "skipped": True,
            "reason": "EVALUATION_BUNDLE_INCOMPLETE",
            "external_effect_authorized": EXTERNAL_EFFECT_AUTHORIZED,
        }
    scope_id = _scope_id_from_state(state, session_id=session_id)
    corr = correlation_id or f"ddo.lingest.{session_id}.fallback"
    if len(corr) < 8:
        corr = f"{corr}.padding00"[:128]
    event_time = str(outcome.get("event_time_utc") or "")
    if not event_time:
        return {
            "ok": True,
            "skipped": True,
            "reason": "OUTCOME_EVENT_TIME_MISSING",
            "external_effect_authorized": EXTERNAL_EFFECT_AUTHORIZED,
        }
    result = ingest_evaluation_bundle_into_learning_state_v1(
        ledger,
        state_scope_id=scope_id,
        outcome=outcome,
        attribution=attribution,
        counterfactual=counterfactual,
        event_time_utc=event_time,
        correlation_id=corr,
        cycle_id=cycle_id,
    )
    payload = dict(result)
    payload["binding_id"] = BINDING_ID
    payload["state_scope_id"] = scope_id
    state.last_ddo_learning_state = payload.get("learning_state_record")
    state.last_ddo_learning_outcome_ingest = payload
    return payload
