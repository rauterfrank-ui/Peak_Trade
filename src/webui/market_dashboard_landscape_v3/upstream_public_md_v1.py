"""Optional background EEA public-MD observation for Landscape V3 (host-independent)."""

from __future__ import annotations

import os
import threading
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Callable, Mapping, Optional

from src.ops.peak_trade_public_market_data_runtime_v1.constants_v1 import (
    EEA_REST_HOST,
    MARK_HISTORY_CANDLES_PATH,
)
from src.ops.peak_trade_public_market_data_runtime_v1.rest_recovery_v1 import (
    assert_eea_rest_host_v1,
    bootstrap_rest_snapshot_v1,
)
from src.ops.peak_trade_public_market_data_runtime_v1.ws_transport_v1 import PublicWsTransportV1
from src.ops.peak_trade_public_market_data_runtime_v1.ws_network_connector_v1 import (
    OkxEeaPublicWsNetworkConnectorV1,
    create_ratified_eea_public_ws_network_connector_v1,
)
from src.webui.market_dashboard_landscape_v3.candle_chart_v1 import (
    pt1m_rows_from_rest_history,
    ticker_to_open_mark_v1,
)
from src.webui.market_dashboard_landscape_v3.constants_v1 import DEFAULT_VENUE_NATIVE_ID
from src.webui.market_dashboard_landscape_v3.presentation_adapter_v1 import (
    LandscapeV3PresentationAdapterV1,
)
from src.webui.market_dashboard_landscape_v3.stream_hub_v1 import LandscapeV3StreamHubV1


RestFetch = Callable[[str, Mapping[str, str]], Mapping[str, Any]]


@dataclass
class LandscapeV3UpstreamPublicMdServiceV1:
    hub: LandscapeV3StreamHubV1
    venue_native_id: str = DEFAULT_VENUE_NATIVE_ID
    adapter: LandscapeV3PresentationAdapterV1 = field(
        default_factory=LandscapeV3PresentationAdapterV1
    )
    poll_interval_seconds: float = 1.0
    stale_after_seconds: float = 10.0
    _thread: Optional[threading.Thread] = field(default=None, repr=False)
    _stop: threading.Event = field(default_factory=threading.Event, repr=False)
    _connector: Optional[OkxEeaPublicWsNetworkConnectorV1] = field(default=None, repr=False)
    _transport: Optional[PublicWsTransportV1] = field(default=None, repr=False)
    _rest_fetch: Optional[RestFetch] = field(default=None, repr=False)
    _sequence: int = 0

    @classmethod
    def from_env(cls, hub: LandscapeV3StreamHubV1) -> "LandscapeV3UpstreamPublicMdServiceV1":
        inst = os.environ.get("PEAK_TRADE_LANDSCAPE_V3_INSTRUMENT", DEFAULT_VENUE_NATIVE_ID)
        return cls(hub=hub, venue_native_id=inst)

    def live_enabled(self) -> bool:
        return os.environ.get("PEAK_TRADE_LANDSCAPE_V3_PUBLIC_MD_LIVE", "").strip() in {
            "1",
            "true",
            "TRUE",
        }

    def start_if_enabled(self) -> None:
        if not self.live_enabled():
            self.hub.observation.transport_state = "DISCONNECTED"
            return
        if self._thread is not None and self._thread.is_alive():
            return
        self._stop.clear()
        self._thread = threading.Thread(
            target=self._run_loop, name="landscape-v3-public-md", daemon=True
        )
        self._thread.start()

    def stop(self) -> None:
        self._stop.set()
        if self._transport is not None:
            try:
                self._transport.close()
            except Exception:
                pass
        if self._connector is not None:
            try:
                self._connector.disconnect()
            except Exception:
                pass
        if self._thread is not None:
            self._thread.join(timeout=3.0)

    def inject_rest_fetcher_for_tests(self, fetch: RestFetch) -> None:
        self._rest_fetch = fetch

    def bootstrap_offline(self, fetch: RestFetch) -> None:
        """REST-only bootstrap for tests and degraded shell (no live WS)."""
        assert_eea_rest_host_v1(EEA_REST_HOST)
        obs = self.hub.observation
        obs.rest_host = EEA_REST_HOST
        snap = bootstrap_rest_snapshot_v1(fetch, self.venue_native_id)
        hist = fetch(
            MARK_HISTORY_CANDLES_PATH, {"instId": self.venue_native_id, "bar": "1m", "limit": "120"}
        )
        rows = pt1m_rows_from_rest_history(hist)
        finalized = [r for r in rows if str(r.get("confirm")) == "1"]
        obs.chart.reset_for_instrument(self.venue_native_id)
        obs.chart.bootstrap_from_finalized_rows(finalized)
        mark_data = (snap.get("mark") or {}).get("data") or []
        if mark_data:
            obs.mark_px = str(mark_data[0].get("markPx") or mark_data[0].get("mark_px"))
        obs.mark_captured_at = datetime.now(timezone.utc).isoformat()
        obs.transport_state = "DISCONNECTED"
        obs.freshness_state = "BOOTSTRAP_ONLY"
        obs.provenance = {"transport": "eea_public_rest", "host": EEA_REST_HOST}

    def _run_loop(self) -> None:
        try:
            self._connector = create_ratified_eea_public_ws_network_connector_v1()
            self._transport = PublicWsTransportV1.from_ratified_binding(
                connector=self._connector,
                message_source=self._connector.message_source,
                venue_native_id=self.venue_native_id,
            )
            self._transport.connect_and_subscribe()
            self.hub.observation.transport_state = "CONNECTED"
            if self._rest_fetch is not None:
                self.bootstrap_offline(self._rest_fetch)
            last_msg = time.monotonic()
            while not self._stop.is_set():
                msgs = self._transport.poll_messages()
                now = time.monotonic()
                if msgs:
                    last_msg = now
                    self._handle_ws_messages(msgs)
                if now - last_msg > self.stale_after_seconds:
                    self.hub.observation.transport_state = "STALE"
                    self.hub.observation.freshness_state = "STALE"
                else:
                    self.hub.observation.transport_state = "CONNECTED"
                    self.hub.observation.freshness_state = "LIVE"
                time.sleep(self.poll_interval_seconds)
        except Exception as exc:
            self.hub.observation.transport_state = "DISCONNECTED"
            self.hub.observation.freshness_state = "ERROR"
            self.hub.observation.provenance = {"last_error": str(exc)}
        finally:
            if self._connector is not None:
                self._connector.disconnect()

    def _handle_ws_messages(self, msgs: list[Mapping[str, Any]]) -> None:
        obs = self.hub.observation
        chart_events: list[dict[str, Any]] = []
        for msg in msgs:
            arg = msg.get("arg") if isinstance(msg.get("arg"), dict) else {}
            data = msg.get("data")
            if not isinstance(data, list):
                continue
            channel = str(arg.get("channel") or "")
            if channel == "tickers" and data:
                row = data[0]
                ts_raw = row.get("ts")
                ts_ms = int(str(ts_raw)) if ts_raw is not None else int(time.time() * 1000)
                interval_start = ts_ms - (ts_ms % 60_000)
                mark = ticker_to_open_mark_v1(row, interval_start_ms=interval_start)
                chart_events.extend(obs.chart.apply_live_mark(mark))
                obs.mark_px = str(row.get("last") or row.get("markPx") or obs.mark_px)
                obs.mark_captured_at = datetime.now(timezone.utc).isoformat()
            if channel == "trades" and data:
                row = data[0]
                px = row.get("px")
                ts_raw = row.get("ts")
                if px is not None and ts_raw is not None:
                    ts_ms = int(str(ts_raw))
                    interval_start = ts_ms - (ts_ms % 60_000)
                    chart_events.extend(
                        obs.chart.apply_live_mark(
                            {
                                "interval_start_ms": interval_start,
                                "mark_px": str(px),
                                "confirm": "0",
                            }
                        )
                    )
        if chart_events:
            self._sequence += 1
            obs.sequence_cursor = self._sequence
            payload = self.adapter.build_incremental(
                obs,
                chart_events=chart_events,
            )
            payload["type"] = "incremental"
            payload["stream_schema"] = "market_dashboard_landscape_v3_stream.v1"
            self.hub.publish_from_thread(payload)
