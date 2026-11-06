"""Session-scoped CanonicalPublicMdBarProducer for DDO N_BARS (observation-only).

Feeds authoritative O4 bars from accepted C1 host observations. No O5/dashboard
side effects. Does not alter cycle decisions.
"""

from __future__ import annotations

from typing import Any, Final

from src.learning.deterministic_decision_outcome_v0.capture_v0 import DdoCaptureBindingV0
from src.ops.canonical_public_md_and_ohlcv_transport_reconciliation_v1.canonical_bar_producer_v1 import (
    CanonicalPublicMdBarProducerV1,
)
from src.ops.canonical_public_md_and_ohlcv_transport_reconciliation_v1.constants_v1 import (
    BAR_STATE_IN_PROGRESS,
)
from src.ops.canonical_public_md_and_ohlcv_transport_reconciliation_v1.bar_state_contract_v1 import (
    BarStateContractErrorV1,
)
from src.ops.okx_native_instrument_and_mark_price_runtime_binding_fail_closed_v1.normalized_market_data_v1 import (
    NormalizedPublicMarketDataV1,
)
from src.trading.market_state.distinct_market_observation_acceptor_v1 import (
    ObservationAcceptanceResultV1,
    ObservationClassification,
)

BINDING_ID: Final[str] = (
    "peak_trade.ops.wallclock_bridge.ddo_o4_canonical_bar_producer_session_binding_v1"
)
DEFAULT_DDO_O4_CONFIG_DIGEST: Final[str] = "ddo_o4_wallclock_bridge_session_v1"
EXTERNAL_EFFECT_AUTHORIZED: Final[bool] = False


def _capture_enabled(state: Any) -> bool:
    binding = getattr(state, "ddo_capture_binding", None)
    return isinstance(binding, DdoCaptureBindingV0) and binding.enabled


def ensure_ddo_o4_canonical_bar_producer_v1(
    state: Any,
    *,
    session_id: str,
    repository_sha: str,
    config_digest: str | None = None,
) -> CanonicalPublicMdBarProducerV1 | None:
    """Lazy-init producer when DDO capture is enabled."""
    if not _capture_enabled(state):
        return None
    existing = getattr(state, "ddo_canonical_public_md_bar_producer", None)
    if isinstance(existing, CanonicalPublicMdBarProducerV1):
        return existing
    digest = (
        config_digest
        or getattr(state, "ddo_o4_config_digest", None)
        or DEFAULT_DDO_O4_CONFIG_DIGEST
    )
    producer = CanonicalPublicMdBarProducerV1(
        session_id=session_id,
        repository_sha=repository_sha,
        config_digest=str(digest),
    )
    state.ddo_canonical_public_md_bar_producer = producer
    return producer


def _normalized_from_acceptance_v1(
    result: ObservationAcceptanceResultV1,
    *,
    receive_ts_unix: float,
) -> NormalizedPublicMarketDataV1 | None:
    ident = result.observation_identity
    if ident is None:
        return None
    return NormalizedPublicMarketDataV1(
        canonical_instrument_id=str(ident.canonical_instrument_id),
        venue_instrument_id=str(ident.venue_instrument_id),
        venue=str(ident.venue),
        mark_px=float(ident.mark_price),
        event_ts_unix=float(ident.venue_event_time),
        receive_ts_unix=float(receive_ts_unix),
        mark_price_endpoint="/wallclock/host_observation_acceptance",
        mark_price_field="mark_price",
        mapping_digest=DEFAULT_DDO_O4_CONFIG_DIGEST,
        mapping_version="v1",
    )


def _finalize_due_bars_v1(producer: CanonicalPublicMdBarProducerV1, event_ts_unix: float) -> None:
    for env in list(producer.list_envelopes()):
        if str(env.get("finalization_state") or "") != BAR_STATE_IN_PROGRESS:
            continue
        if float(event_ts_unix) >= float(env["bar_close_time"]):
            try:
                producer.finalize_bar(
                    canonical_instrument_id=str(env["canonical_instrument_id"]),
                    bar_open_time=float(env["bar_open_time"]),
                )
            except (BarStateContractErrorV1, ValueError):
                pass


def maybe_ingest_accepted_observation_into_ddo_o4_producer_v1(
    state: Any,
    observation_acceptance_result: ObservationAcceptanceResultV1 | None,
    *,
    session_id: str,
    repository_sha: str,
    receive_ts_unix: float,
    runtime_cycle_index: int,
) -> dict[str, Any] | None:
    """Ingest one accepted host observation into the session O4 producer."""
    if observation_acceptance_result is None or observation_acceptance_result.fail_closed:
        return None
    if observation_acceptance_result.classification not in {
        ObservationClassification.DISTINCT,
        ObservationClassification.DUPLICATE,
        ObservationClassification.TRANSPORT_ONLY_DUPLICATE,
    }:
        return None
    producer = ensure_ddo_o4_canonical_bar_producer_v1(
        state,
        session_id=session_id,
        repository_sha=repository_sha,
    )
    if producer is None:
        return None
    data = _normalized_from_acceptance_v1(
        observation_acceptance_result, receive_ts_unix=receive_ts_unix
    )
    if data is None:
        return None
    ingest = producer.ingest_normalized_event(
        data,
        runtime_cycle_index=runtime_cycle_index,
    )
    _finalize_due_bars_v1(producer, float(data.event_ts_unix))
    return {
        "ok": True,
        "binding_id": BINDING_ID,
        "ingest": ingest,
        "external_effect_authorized": EXTERNAL_EFFECT_AUTHORIZED,
    }
