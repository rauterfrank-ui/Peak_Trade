"""Productive DDO O4→N_BARS source convergence onto WP-A/WP-C canonical public plane."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Final, Mapping

from src.ops.canonical_public_md_and_ohlcv_transport_reconciliation_v1.canonical_bar_producer_v1 import (
    CanonicalPublicMdBarProducerV1,
)
from src.ops.canonical_public_md_and_ohlcv_transport_reconciliation_v1.constants_v1 import (
    BAR_STATE_CORRECTED,
    BAR_STATE_FINALIZED,
)
from src.ops.market_data_private_state_runtime_convergence_v1.public_handoff_v1 import (
    converged_o4_handoff_v1,
)
from src.ops.peak_trade_public_market_data_runtime_v1.consumer_adapters_v1 import (
    o4_n_bars_envelope_from_historical_facts_v1,
)
from src.ops.peak_trade_public_market_data_runtime_v1.o4_pt1h_bar_fact_v1 import (
    load_finalized_pt1h_o4_bar_elements_v1,
    sync_finalized_envelopes_to_wp_a_store_v1,
)
from src.learning.deterministic_decision_outcome_v0.errors_v0 import DdoValidationError
from src.ops.wallclock_full_canonical_decision_to_simulated_economics_runtime_bridge_v1.ddo_o4_n_bars_snapshot_materialization_v1 import (
    build_o4_n_bars_bar_evidence_snapshot_v1,
)

BINDING_ID: Final[str] = "peak_trade.ops.wallclock_bridge.ddo_o4_n_bars_public_plane_convergence_v1"
EXTERNAL_EFFECT_AUTHORIZED: Final[bool] = False

PRODUCTIVE_DDO_O4_SOURCE_IS_WP_A_WP_C_CANONICAL: Final[bool] = True
COMPETING_PRODUCTIVE_O4_TRUTH: Final[bool] = False
N_BARS_REMAINS_PT1H: Final[bool] = True
DDO_OBSERVATION_ONLY: Final[bool] = True

_FINALIZED_STATES: Final[frozenset[str]] = frozenset({BAR_STATE_FINALIZED, BAR_STATE_CORRECTED})


def default_public_md_store_root_v1(ddo_runtime_state_root: Path) -> Path:
    return ddo_runtime_state_root / "peak_trade_public_market_data_runtime_v1"


def resolve_public_md_store_root_v1(state: Any) -> Path | None:
    explicit = getattr(state, "public_md_store_root", None)
    if explicit:
        return Path(str(explicit))
    ddo_root = getattr(state, "ddo_durable_evidence_runtime_state_root", None)
    if ddo_root:
        return default_public_md_store_root_v1(Path(str(ddo_root)))
    return None


def ensure_public_md_store_root_on_state_v1(state: Any) -> Path | None:
    root = resolve_public_md_store_root_v1(state)
    if root is None:
        return None
    state.public_md_store_root = str(root)
    return root


def sync_session_producer_finalized_bars_to_wp_a_v1(state: Any) -> dict[str, Any] | None:
    """Write finalized session producer bars to WP-A facts (producer is writer only)."""
    store_root = ensure_public_md_store_root_on_state_v1(state)
    if store_root is None:
        return None
    producer = getattr(state, "ddo_canonical_public_md_bar_producer", None)
    if not isinstance(producer, CanonicalPublicMdBarProducerV1):
        return None
    result = sync_finalized_envelopes_to_wp_a_store_v1(
        store_root,
        producer.list_envelopes(),
        finalized_states=_FINALIZED_STATES,
    )
    return {
        "ok": True,
        "binding_id": BINDING_ID,
        "phase": "sync_producer_to_wp_a_facts",
        "external_effect_authorized": EXTERNAL_EFFECT_AUTHORIZED,
        **result,
    }


def build_wp_c_converged_o4_from_store_v1(store_root: Path) -> dict[str, Any]:
    bars = load_finalized_pt1h_o4_bar_elements_v1(store_root)
    wp_a_o4 = o4_n_bars_envelope_from_historical_facts_v1(bars)
    return converged_o4_handoff_v1(wp_a_o4, consumer_id="o4_n_bars_learning")


def materialize_ddo_o4_snapshot_from_converged_public_plane_v1(
    *,
    decision_event_ref: str,
    converged_o4: Mapping[str, Any],
    n_bars: int,
    decision_event: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    payload = converged_o4.get("payload")
    if not isinstance(payload, Mapping):
        raise ValueError("CONVERGED_O4_PAYLOAD_MISSING")
    if payload.get("forward_fill") is True:
        raise ValueError("O4_FORWARD_FILL_FORBIDDEN")
    bars_raw = payload.get("bars")
    if not isinstance(bars_raw, list) or not bars_raw:
        raise ValueError("O4_CANONICAL_BARS_MISSING")
    return build_o4_n_bars_bar_evidence_snapshot_v1(
        decision_event_ref=decision_event_ref,
        o4_bars=bars_raw,
        n_bars=n_bars,
        decision_event=decision_event,
    )


def maybe_materialize_ddo_o4_n_bars_snapshot_from_public_plane_convergence_v1(
    state: Any,
    *,
    decision_event_ref: str | None,
    n_bars: int | None = None,
) -> dict[str, Any] | None:
    """Productive DDO O4 snapshot via WP-A facts → WP-C converged_o4 only."""
    if getattr(state, "ddo_o4_n_bars_bar_evidence_snapshot_locked", False):
        return None
    if not decision_event_ref:
        return None
    store_root = ensure_public_md_store_root_on_state_v1(state)
    if store_root is None:
        return {
            "ok": False,
            "binding_id": BINDING_ID,
            "reason": "PUBLIC_MD_STORE_UNBOUND",
            "external_effect_authorized": EXTERNAL_EFFECT_AUTHORIZED,
        }
    sync_session_producer_finalized_bars_to_wp_a_v1(state)
    try:
        converged = build_wp_c_converged_o4_from_store_v1(store_root)
        count = (
            n_bars if n_bars is not None else int(getattr(state, "ddo_n_bars_horizon_n_bars", 2))
        )
        decision_event = getattr(state, "ddo_n_bars_horizon_decision_event", None)
        snapshot = materialize_ddo_o4_snapshot_from_converged_public_plane_v1(
            decision_event_ref=decision_event_ref,
            converged_o4=converged,
            n_bars=count,
            decision_event=decision_event if isinstance(decision_event, Mapping) else None,
        )
    except (ValueError, TypeError, DdoValidationError) as exc:
        return {
            "ok": False,
            "binding_id": BINDING_ID,
            "reason": str(exc),
            "external_effect_authorized": EXTERNAL_EFFECT_AUTHORIZED,
        }
    state.ddo_o4_n_bars_bar_evidence_snapshot = snapshot
    state.last_ddo_o4_public_plane_convergence = {
        "ok": True,
        "binding_id": BINDING_ID,
        "productive_ddo_o4_source_is_wp_a_wp_c_canonical": PRODUCTIVE_DDO_O4_SOURCE_IS_WP_A_WP_C_CANONICAL,
        "competing_productive_o4_truth": COMPETING_PRODUCTIVE_O4_TRUTH,
        "consumer_id": converged.get("consumer_id"),
        "external_effect_authorized": EXTERNAL_EFFECT_AUTHORIZED,
    }
    return dict(state.last_ddo_o4_public_plane_convergence)
