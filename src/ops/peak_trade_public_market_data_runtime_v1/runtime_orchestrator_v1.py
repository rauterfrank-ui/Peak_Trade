"""Bootstrap, observe, recover, persist, and publish public market data runtime."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Mapping, Optional

from src.ops.peak_trade_public_market_data_runtime_v1.consumer_adapters_v1 import (
    finalized_facts_to_raw_mark_candles_v1,
    landscape_readmodel_from_live_facts_v1,
    o4_n_bars_envelope_from_historical_facts_v1,
    ranking_b05_adapter_from_finalized_pt1m_marks_v1,
    research_optimizer_historical_adapter_v1,
)
from src.ops.peak_trade_public_market_data_runtime_v1.durable_store_v1 import (
    append_fact_v1,
    default_store_paths_v1,
)
from src.ops.peak_trade_public_market_data_runtime_v1.event_pipeline_v1 import (
    EventSequenceStateV1,
    process_public_events_v1,
)
from src.ops.peak_trade_public_market_data_runtime_v1.freshness_v1 import (
    classify_live_best_bid_ask_freshness_v1,
    classify_live_mark_price_freshness_v1,
)
from src.ops.peak_trade_public_market_data_runtime_v1.historical_query_v1 import (
    query_historical_facts_v1,
)
from src.ops.peak_trade_public_market_data_runtime_v1.o4_pt1h_bar_fact_v1 import (
    load_finalized_pt1h_o4_bar_elements_v1,
)
from src.ops.peak_trade_public_market_data_runtime_v1.rest_recovery_v1 import (
    bootstrap_rest_snapshot_v1,
    recover_pt1m_gaps_via_rest_v1,
)
from src.ops.peak_trade_public_market_data_runtime_v1.ws_transport_v1 import PublicWsTransportV1


@dataclass
class PublicMarketDataRuntimeV1:
    store_root: Path
    venue_native_id: str
    canonical_instrument_id: str
    ws_transport: Optional[PublicWsTransportV1] = None
    rest_fetch_json: Optional[Callable[[str, Mapping[str, str]], Mapping[str, Any]]] = None
    event_state: EventSequenceStateV1 = field(default_factory=EventSequenceStateV1)
    lifecycle_events: list[dict[str, Any]] = field(default_factory=list)

    def bootstrap(self, *, captured_at: str) -> dict[str, Any]:
        if self.rest_fetch_json is None:
            raise RuntimeError("REST_FETCH_UNBOUND")
        snap = bootstrap_rest_snapshot_v1(self.rest_fetch_json, self.venue_native_id)
        self.lifecycle_events.append({"phase": "bootstrap", "host": snap["host"]})
        return snap

    def run_observation_cycle(self) -> list[Mapping[str, Any]]:
        if self.ws_transport is None:
            return []
        msgs = self.ws_transport.poll_messages()
        envelopes, self.event_state, gaps = process_public_events_v1(
            events=msgs, state=self.event_state
        )
        if gaps and self.rest_fetch_json is not None:
            inst_ref = {
                "canonical_instrument_id": self.canonical_instrument_id,
                "venue_native_id": self.venue_native_id,
                "venue": "okx_eea",
                "instrument_type": "SWAP",
                "settlement_asset": "USDT",
                "mapping_provenance_digest": "runtime_v1",
            }
            recovery = recover_pt1m_gaps_via_rest_v1(
                fetch_json=self.rest_fetch_json,
                venue_native_id=self.venue_native_id,
                instrument_ref_dict=inst_ref,
                missing_interval_starts_ms=gaps,
                captured_at="2026-09-26T00:00:00Z",
            )
            paths = default_store_paths_v1(self.store_root)
            for bar in recovery.recovered_bars:
                append_fact_v1(paths, bar.to_dict())
            self.lifecycle_events.append(
                {"phase": "rest_gap_recovery", "gaps": recovery.gaps_detected}
            )
        return [e.payload for e in envelopes]

    def persist_finalized_mark_fact(self, fact_payload: Mapping[str, Any]) -> str:
        paths = default_store_paths_v1(self.store_root)
        record = append_fact_v1(paths, fact_payload)
        return record.fact_digest

    def publish_consumer_surfaces(
        self,
        *,
        mark_age_seconds: float,
        bba_age_seconds: float,
        captured_at: str,
    ) -> dict[str, Any]:
        mark_fresh = classify_live_mark_price_freshness_v1(age_seconds=mark_age_seconds)
        bba_fresh = classify_live_best_bid_ask_freshness_v1(age_seconds=bba_age_seconds)
        hist = query_historical_facts_v1(self.store_root)
        raw_marks = finalized_facts_to_raw_mark_candles_v1(
            hist.facts, venue_native_id=self.venue_native_id, captured_at=captured_at
        )
        ranking = ranking_b05_adapter_from_finalized_pt1m_marks_v1(raw_marks)
        landscape = landscape_readmodel_from_live_facts_v1(
            mark_px="100.0",
            live_mark_captured_at=captured_at,
            ohlcv_freshness_state="fresh" if mark_fresh.publishable else "stale",
        )
        pt1h_bars = load_finalized_pt1h_o4_bar_elements_v1(self.store_root)
        o4 = o4_n_bars_envelope_from_historical_facts_v1(pt1h_bars)
        research = research_optimizer_historical_adapter_v1(
            {"facts": hist.facts, "live_ws_required": hist.live_ws_required}
        )
        return {
            "mark_freshness": mark_fresh,
            "bba_freshness": bba_fresh,
            "landscape": landscape,
            "ranking_b05": ranking,
            "o4_n_bars": o4,
            "research_optimizer": research,
        }

    def restart_replay(self) -> dict[str, Any]:
        hist = query_historical_facts_v1(self.store_root)
        return {
            "restarted": True,
            "fact_count": len(hist.facts),
            "live_ws_required": hist.live_ws_required,
        }
