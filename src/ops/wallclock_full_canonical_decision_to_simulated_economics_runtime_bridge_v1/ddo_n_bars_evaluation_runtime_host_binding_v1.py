"""Productive bridge binding for REAL N_BARS evaluation runtime."""

from __future__ import annotations

from typing import Any, Final, Mapping

from src.learning.deterministic_decision_outcome_v0.evaluation_runtime_productive_host_v1 import (
    EXTERNAL_EFFECT_AUTHORIZED,
    derive_productive_n_bars_evaluation_identity_v1,
    produce_n_bars_evaluation_runtime_bundle_v1,
)
from src.learning.deterministic_decision_outcome_v0.real_outcome_horizon_contracts_v1 import (
    EVALUATION_RUNTIME_WIRING,
)

BINDING_ID: Final[str] = (
    "peak_trade.ops.wallclock_bridge.ddo_n_bars_evaluation_runtime_host_binding_v1"
)


def invoke_productive_n_bars_evaluation_runtime_v1(
    state: Any,
    *,
    decision_event: Mapping[str, Any] | None,
    identity: Mapping[str, Any] | None,
    horizon_result: Mapping[str, Any] | None,
    correlation_id: str | None = None,
) -> dict[str, Any]:
    """Fail-closed evaluation join; consumes horizon output only."""
    if not EVALUATION_RUNTIME_WIRING:
        return {
            "ok": True,
            "skipped": True,
            "reason": "EVALUATION_RUNTIME_NOT_WIRED",
            "external_effect_authorized": EXTERNAL_EFFECT_AUTHORIZED,
        }
    if decision_event is None or horizon_result is None:
        return {
            "ok": True,
            "skipped": True,
            "reason": "EVALUATION_UPSTREAM_EVIDENCE_MISSING",
            "external_effect_authorized": EXTERNAL_EFFECT_AUTHORIZED,
        }
    if horizon_result.get("skipped") is True:
        return {
            "ok": True,
            "skipped": True,
            "reason": "EVALUATION_UPSTREAM_HORIZON_SKIPPED",
            "external_effect_authorized": EXTERNAL_EFFECT_AUTHORIZED,
        }
    observation = horizon_result.get("evaluation_observation")
    if not isinstance(observation, Mapping):
        return {
            "ok": True,
            "skipped": True,
            "reason": "EVALUATION_HORIZON_OBSERVATION_MISSING",
            "external_effect_authorized": EXTERNAL_EFFECT_AUTHORIZED,
        }
    resolved_identity = identity
    if resolved_identity is None:
        corr = correlation_id or f"ddo.eval.{getattr(state, 'cycle_index', 0)}"
        resolved_identity = derive_productive_n_bars_evaluation_identity_v1(
            decision_record_id=str(decision_event["record_id"]),
            evaluation_time_utc=str(observation["evaluation_time_utc"]),
            correlation_id=corr,
        )
    result = produce_n_bars_evaluation_runtime_bundle_v1(
        horizon_result,
        decision_event,
        resolved_identity,
    )
    payload = dict(result)
    payload["binding_id"] = BINDING_ID
    payload["external_effect_authorized"] = EXTERNAL_EFFECT_AUTHORIZED
    state.last_ddo_n_bars_evaluation_runtime = payload
    return payload
