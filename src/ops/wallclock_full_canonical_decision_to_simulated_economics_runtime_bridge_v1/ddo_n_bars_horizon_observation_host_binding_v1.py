"""Productive bridge binding for REAL N_BARS horizon observation capture.

Single join site for the wallclock economics host. Observation-only.
"""

from __future__ import annotations

from typing import Any, Final, Mapping

from src.learning.deterministic_decision_outcome_v0.real_outcome_horizon_contracts_v1 import (
    REAL_OUTCOME_HORIZON_ENGINE_WIRED,
)
from src.learning.deterministic_decision_outcome_v0.real_outcome_horizon_productive_host_v1 import (
    EXTERNAL_EFFECT_AUTHORIZED,
    produce_real_outcome_horizon_evaluation_observation_v1,
)

BINDING_ID: Final[str] = (
    "peak_trade.ops.wallclock_bridge.ddo_n_bars_horizon_observation_host_binding_v1"
)


def invoke_productive_n_bars_horizon_observation_v1(
    state: Any,
    *,
    decision_event: Mapping[str, Any] | None,
    o4_snapshot: Mapping[str, Any] | None,
    event_ts_unix: float,
    outcome_scalar_kind: str = "LOG_RETURN",
    economic_score: str | None = None,
) -> dict[str, Any]:
    """Fail-closed productive join; does not alter bridge cycle decisions."""
    if not REAL_OUTCOME_HORIZON_ENGINE_WIRED:
        return {
            "ok": True,
            "skipped": True,
            "reason": "REAL_OUTCOME_HORIZON_ENGINE_NOT_WIRED",
            "external_effect_authorized": EXTERNAL_EFFECT_AUTHORIZED,
        }
    if decision_event is None or o4_snapshot is None:
        return {
            "ok": True,
            "skipped": True,
            "reason": "HORIZON_UPSTREAM_EVIDENCE_MISSING",
            "external_effect_authorized": EXTERNAL_EFFECT_AUTHORIZED,
        }
    result = produce_real_outcome_horizon_evaluation_observation_v1(
        decision_event,
        o4_snapshot,
        outcome_scalar_kind=outcome_scalar_kind,
        economic_score=economic_score,
        producer_observed_at_unix=float(event_ts_unix),
    )
    payload = dict(result)
    payload["binding_id"] = BINDING_ID
    payload["external_effect_authorized"] = EXTERNAL_EFFECT_AUTHORIZED
    state.last_ddo_n_bars_horizon_observation = payload
    return payload
