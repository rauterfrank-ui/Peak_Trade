"""Legacy O4 snapshot materialization from CanonicalPublicMdBarProducerV1.

Non-productive path for tests and parity proofs. Productive wallclock hosts must
use ``maybe_materialize_ddo_o4_n_bars_snapshot_from_public_plane_convergence_v1``.
"""

from __future__ import annotations

from typing import Any, Final, Mapping

from src.learning.deterministic_decision_outcome_v0.errors_v0 import DdoValidationError
from src.ops.canonical_public_md_and_ohlcv_transport_reconciliation_v1.canonical_bar_producer_v1 import (
    CanonicalPublicMdBarProducerV1,
)
from src.ops.canonical_public_md_and_ohlcv_transport_reconciliation_v1.constants_v1 import (
    BAR_STATE_CORRECTED,
    BAR_STATE_FINALIZED,
)
from src.ops.peak_trade_public_market_data_runtime_v1.o4_pt1h_bar_fact_v1 import (
    canonical_bar_envelope_to_o4_bar_element_v1,
)
from src.ops.wallclock_full_canonical_decision_to_simulated_economics_runtime_bridge_v1.ddo_o4_n_bars_snapshot_materialization_v1 import (
    build_o4_n_bars_bar_evidence_snapshot_v1,
)

BINDING_ID: Final[str] = (
    "peak_trade.ops.wallclock_bridge.ddo_o4_n_bars_snapshot_from_canonical_bar_producer_v1"
)
EXTERNAL_EFFECT_AUTHORIZED: Final[bool] = False
_LEGACY_NON_PRODUCTIVE_O4_SNAPSHOT_PATH: Final[bool] = True

_FINALIZED_STATES: Final[frozenset[str]] = frozenset({BAR_STATE_FINALIZED, BAR_STATE_CORRECTED})


def materialize_o4_n_bars_bar_evidence_snapshot_v1(
    *,
    decision_event_ref: str,
    producer: CanonicalPublicMdBarProducerV1,
    n_bars: int,
    decision_event: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Build a validated O4 snapshot from the producer's finalized bar chain tail."""
    finalized = [
        canonical_bar_envelope_to_o4_bar_element_v1(item)
        for item in producer.list_envelopes()
        if str(item.get("finalization_state")) in _FINALIZED_STATES
    ]
    return build_o4_n_bars_bar_evidence_snapshot_v1(
        decision_event_ref=decision_event_ref,
        o4_bars=finalized,
        n_bars=n_bars,
        decision_event=decision_event,
        o4_interval_id=producer.interval,
    )


def maybe_materialize_ddo_o4_n_bars_snapshot_from_canonical_producer_v1(
    state: Any,
    *,
    decision_event_ref: str | None,
    n_bars: int | None = None,
) -> dict[str, Any] | None:
    """Deprecated productive entry — retained for explicit legacy/test callers only."""
    if getattr(state, "ddo_o4_n_bars_bar_evidence_snapshot_locked", False):
        return None
    if not decision_event_ref:
        return None
    producer = getattr(state, "ddo_canonical_public_md_bar_producer", None)
    if not isinstance(producer, CanonicalPublicMdBarProducerV1):
        return None
    count = n_bars if n_bars is not None else int(getattr(state, "ddo_n_bars_horizon_n_bars", 2))
    decision_event = getattr(state, "ddo_n_bars_horizon_decision_event", None)
    try:
        snapshot = materialize_o4_n_bars_bar_evidence_snapshot_v1(
            decision_event_ref=decision_event_ref,
            producer=producer,
            n_bars=count,
            decision_event=decision_event if isinstance(decision_event, Mapping) else None,
        )
    except DdoValidationError as exc:
        return {
            "ok": False,
            "binding_id": BINDING_ID,
            "reason": str(exc),
            "legacy_non_productive_path": _LEGACY_NON_PRODUCTIVE_O4_SNAPSHOT_PATH,
            "external_effect_authorized": EXTERNAL_EFFECT_AUTHORIZED,
        }
    state.ddo_o4_n_bars_bar_evidence_snapshot = snapshot
    return {
        "ok": True,
        "binding_id": BINDING_ID,
        "n_bars": count,
        "decision_event_ref": decision_event_ref,
        "legacy_non_productive_path": _LEGACY_NON_PRODUCTIVE_O4_SNAPSHOT_PATH,
        "external_effect_authorized": EXTERNAL_EFFECT_AUTHORIZED,
    }
