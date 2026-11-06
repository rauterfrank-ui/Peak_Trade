"""PT1M OHLCV live-repaint contracts for the dashboard readmodel path."""

from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from src.ops.okx_public_market_data_client_v1 import OkxPublicCaptureEnvelopeV1
from src.ops.okx_selected_instrument_ohlcv_readmodel_v1 import (
    DEFAULT_BAR,
    DEFAULT_DASHBOARD_OHLCV_POLL_INTERVAL_SECONDS,
    OPEN_CANDLE_LIVE_SOURCE_PT1M_V1,
    OhlcvBarV1,
    OkxOhlcvReadmodelError,
    OkxPublicTradeV1,
    apply_okx_public_trades_to_open_candle_v1,
    materialize_selected_okx_ohlcv_readmodel_v1,
    normalize_dashboard_ohlcv_interval_v1,
    parse_okx_history_candles,
    reduce_okx_ohlcv_bars_v1,
)
from src.webui.market_dashboard_landscape_v2.presenter import OHLCV_POLL_INTERVAL_SECONDS

INSTRUMENT = "ETH-USDT-SWAP"


def _ms(iso: str) -> str:
    dt = datetime.fromisoformat(iso.replace("Z", "+00:00"))
    return str(int(dt.timestamp() * 1000))


def _bar(
    *,
    ts: str,
    o: str,
    h: str,
    l: str,
    c: str,
    v: str,
    confirm: bool = False,
) -> OhlcvBarV1:
    return OhlcvBarV1(
        ts=ts,
        open=o,
        high=h,
        low=l,
        close=c,
        volume=v,
        volume_ccy=None,
        confirm=confirm,
        provider_ts_ms="0",
    )


def _trade(
    *,
    trade_id: str,
    px: str,
    sz: str,
    ts_ms: str,
    side: str = "buy",
) -> OkxPublicTradeV1:
    from src.ops.okx_captured_at_freshness_policy_v1 import provider_ms_to_utc_iso

    ts = provider_ms_to_utc_iso(ts_ms)
    assert ts is not None
    return OkxPublicTradeV1(
        trade_id=trade_id,
        price=px,
        size=sz,
        side=side,
        ts=ts,
        provider_ts_ms=ts_ms,
    )


class _FakeOkxClient:
    def __init__(
        self,
        *,
        captured_at: str,
        close_px: str = "1874.50",
        mark_px: str | None = None,
        high_px: str | None = None,
        low_px: str | None = None,
        open_px: str | None = None,
        volume: str = "10",
        trades: list[dict[str, str]] | None = None,
    ) -> None:
        self.captured_at = captured_at
        self.close_px = close_px
        self.open_px = open_px if open_px is not None else close_px
        self.high_px = high_px if high_px is not None else close_px
        self.low_px = low_px if low_px is not None else close_px
        self.volume = volume
        self.mark_px = mark_px if mark_px is not None else close_px
        self.trades = list(trades or [])
        self.paths: list[str] = []
        self.candle_bars: list[str] = []

    def get_json(self, path: str, params: dict[str, str]) -> OkxPublicCaptureEnvelopeV1:
        self.paths.append(path)
        if path == "/api/v5/public/mark-price":
            body = json.dumps(
                {
                    "code": "0",
                    "msg": "",
                    "data": [
                        {
                            "instId": INSTRUMENT,
                            "instType": "SWAP",
                            "markPx": self.mark_px,
                            "ts": "1784934000123",
                        }
                    ],
                }
            )
            return OkxPublicCaptureEnvelopeV1(
                request_url=f"https://www.okx.com{path}?instId={INSTRUMENT}",
                request_path=path,
                query_parameters=dict(params),
                http_status=200,
                provider_code="0",
                provider_message="",
                capture_started_at=self.captured_at,
                response_received_at=self.captured_at,
                captured_at=self.captured_at,
                effective_at=self.captured_at,
                provider_timestamp=None,
                raw_payload_digest="b" * 64,
                byte_size=len(body.encode("utf-8")),
                raw_body_utf8=body,
            )
        if path == "/api/v5/market/trades":
            body = json.dumps({"code": "0", "msg": "", "data": self.trades})
            return OkxPublicCaptureEnvelopeV1(
                request_url=f"https://www.okx.com{path}?instId={INSTRUMENT}",
                request_path=path,
                query_parameters=dict(params),
                http_status=200,
                provider_code="0",
                provider_message="",
                capture_started_at=self.captured_at,
                response_received_at=self.captured_at,
                captured_at=self.captured_at,
                effective_at=self.captured_at,
                provider_timestamp=None,
                raw_payload_digest="c" * 64,
                byte_size=len(body.encode("utf-8")),
                raw_body_utf8=body,
            )
        assert path == "/api/v5/market/candles"
        okx_bar = str(params.get("bar") or "")
        self.candle_bars.append(okx_bar)
        assert okx_bar in {"1m", "1H"}
        start = datetime(2026, 7, 20, 18, 0, 0, tzinfo=timezone.utc)
        step = timedelta(minutes=1) if okx_bar == "1m" else timedelta(hours=1)
        rows: list[list[str]] = []
        for i in range(100):
            ts = start + (step * i)
            ms = str(int(ts.timestamp() * 1000))
            confirm = "0" if i == 99 else "1"
            if i == 99:
                rows.append(
                    [
                        ms,
                        self.open_px,
                        self.high_px,
                        self.low_px,
                        self.close_px,
                        self.volume,
                        self.volume,
                        self.volume,
                        confirm,
                    ]
                )
            else:
                close = "1870.00"
                rows.append([ms, close, close, close, close, "10", "10", "10", confirm])
        body = json.dumps({"code": "0", "msg": "", "data": rows})
        return OkxPublicCaptureEnvelopeV1(
            request_url=f"https://www.okx.com{path}?instId={INSTRUMENT}&bar={okx_bar}",
            request_path=path,
            query_parameters=dict(params),
            http_status=200,
            provider_code="0",
            provider_message="",
            capture_started_at=self.captured_at,
            response_received_at=self.captured_at,
            captured_at=self.captured_at,
            effective_at=self.captured_at,
            provider_timestamp=None,
            raw_payload_digest="a" * 64,
            byte_size=len(body.encode("utf-8")),
            raw_body_utf8=body,
        )


def test_interval_allowlist_accepts_pt1m_and_pt1h_rejects_unknown() -> None:
    assert normalize_dashboard_ohlcv_interval_v1("PT1M") == ("1m", "PT1M", 60)
    assert normalize_dashboard_ohlcv_interval_v1("1m") == ("1m", "PT1M", 60)
    assert normalize_dashboard_ohlcv_interval_v1("PT1H") == ("1H", "PT1H", 3600)
    assert normalize_dashboard_ohlcv_interval_v1("1H") == ("1H", "PT1H", 3600)
    with pytest.raises(OkxOhlcvReadmodelError, match="UNSUPPORTED_BAR_INTERVAL"):
        normalize_dashboard_ohlcv_interval_v1("PT5S")
    with pytest.raises(OkxOhlcvReadmodelError, match="UNSUPPORTED_BAR_INTERVAL"):
        normalize_dashboard_ohlcv_interval_v1("PT1S")
    with pytest.raises(OkxOhlcvReadmodelError, match="UNSUPPORTED_BAR_INTERVAL"):
        normalize_dashboard_ohlcv_interval_v1("5m")
    assert DEFAULT_BAR == "PT1M"


def test_pt1m_bucket_boundaries_are_exact_utc_minutes() -> None:
    from src.ops.okx_selected_instrument_ohlcv_readmodel_v1 import _bucket_start_utc

    bucket = _bucket_start_utc("2026-07-25T12:34:56.789Z", interval_seconds=60)
    assert bucket.isoformat().replace("+00:00", "Z") == "2026-07-25T12:34:00Z"
    assert bucket.second == 0
    assert bucket.microsecond == 0
    hour = _bucket_start_utc("2026-07-25T12:34:56Z", interval_seconds=3600)
    assert hour.isoformat().replace("+00:00", "Z") == "2026-07-25T12:00:00Z"


def test_first_trade_sets_open_high_low_close_and_further_trades_revise() -> None:
    t0 = "2026-07-25T12:34:00Z"
    # Empty tip geometry seeded by first trade in a fresh append path is covered by
    # minute-append; here revise an open tip that already has candle bootstrap open.
    bars = [_bar(ts=t0, o="100", h="100", l="100", c="100", v="1", confirm=False)]
    seed = _trade(trade_id="s0", px="100", sz="1", ts_ms=_ms("2026-07-25T12:34:01Z"))
    _, _, applied, _ = apply_okx_public_trades_to_open_candle_v1(
        bars, [seed], previously_applied_trade_ids=None, interval_seconds=60
    )
    t1 = _trade(trade_id="t1", px="103", sz="2", ts_ms=_ms("2026-07-25T12:34:10Z"))
    t2 = _trade(trade_id="t2", px="98", sz="3", ts_ms=_ms("2026-07-25T12:34:20Z"))
    revised, kind, applied2, meta = apply_okx_public_trades_to_open_candle_v1(
        bars, [seed, t1, t2], previously_applied_trade_ids=applied, interval_seconds=60
    )
    assert kind == "SAME_TIMESTAMP_REVISION"
    assert meta["new_trade_count"] == 2
    assert revised[0].open == "100"
    assert revised[0].high == "103"
    assert revised[0].low == "98"
    assert revised[0].close == "98"
    assert revised[0].volume == "6"  # 1 + 2 + 3
    assert set(applied2) == {"s0", "t1", "t2"}


def test_open_preserved_within_same_pt1m_candle() -> None:
    t0 = "2026-07-25T12:34:00Z"
    bars = [_bar(ts=t0, o="100", h="101", l="99", c="100.5", v="5", confirm=False)]
    _, _, applied, _ = apply_okx_public_trades_to_open_candle_v1(
        bars, [], previously_applied_trade_ids=[], interval_seconds=60
    )
    trade = _trade(trade_id="x1", px="110", sz="1", ts_ms=_ms("2026-07-25T12:34:40Z"))
    revised, kind, _, _ = apply_okx_public_trades_to_open_candle_v1(
        bars, [trade], previously_applied_trade_ids=applied, interval_seconds=60
    )
    assert kind == "SAME_TIMESTAMP_REVISION"
    assert revised[0].open == "100"
    assert revised[0].high == "110"
    assert revised[0].close == "110"


def test_minute_rollover_seals_and_appends_exactly_one_candle() -> None:
    t0 = "2026-07-25T12:34:00Z"
    t1 = "2026-07-25T12:35:00Z"
    bars = [_bar(ts=t0, o="100", h="102", l="99", c="101", v="10", confirm=False)]
    _, _, applied, _ = apply_okx_public_trades_to_open_candle_v1(
        bars,
        [_trade(trade_id="seed", px="101", sz="1", ts_ms=_ms("2026-07-25T12:34:05Z"))],
        previously_applied_trade_ids=None,
        interval_seconds=60,
    )
    nxt = _trade(trade_id="n1", px="110", sz="4", ts_ms=_ms("2026-07-25T12:35:01Z"))
    bars_n, kind_n, _, meta_n = apply_okx_public_trades_to_open_candle_v1(
        bars, [nxt], previously_applied_trade_ids=applied, interval_seconds=60
    )
    assert kind_n == "NEW_INTERVAL_APPEND"
    assert meta_n["new_trade_count"] == 1
    assert len(bars_n) == 2
    assert bars_n[0].ts == t0
    assert bars_n[0].confirm is True
    assert bars_n[1].ts == t1
    assert bars_n[1].open == "110"
    assert bars_n[1].high == "110"
    assert bars_n[1].low == "110"
    assert bars_n[1].close == "110"
    assert bars_n[1].volume == "4"
    assert bars_n[1].confirm is False


def test_duplicate_trades_are_not_double_counted() -> None:
    t0 = "2026-07-25T12:34:00Z"
    bars = [_bar(ts=t0, o="100", h="100", l="100", c="100", v="10", confirm=False)]
    t1 = _trade(trade_id="dup", px="101", sz="2", ts_ms=_ms("2026-07-25T12:34:10Z"))
    # Empty list (not None) = post-bootstrap apply mode.
    bars_r, kind_r, applied_r, _ = apply_okx_public_trades_to_open_candle_v1(
        bars, [t1], previously_applied_trade_ids=[], interval_seconds=60
    )
    assert kind_r == "SAME_TIMESTAMP_REVISION"
    assert bars_r[0].volume == "12"
    bars_d, kind_d, _, meta_d = apply_okx_public_trades_to_open_candle_v1(
        bars_r, [t1], previously_applied_trade_ids=applied_r, interval_seconds=60
    )
    assert kind_d == "NO_OP"
    assert meta_d["duplicate_trade_count"] == 1
    assert bars_d[0].volume == "12"


def test_out_of_order_trades_are_processed_deterministically() -> None:
    t0 = "2026-07-25T12:34:00Z"
    bars = [_bar(ts=t0, o="100", h="100", l="100", c="100", v="1", confirm=False)]
    later = _trade(trade_id="2", px="105", sz="1", ts_ms=_ms("2026-07-25T12:34:40Z"))
    earlier = _trade(trade_id="1", px="95", sz="1", ts_ms=_ms("2026-07-25T12:34:10Z"))
    # Input deliberately reverse chronological; apply path expects pre-sorted trades
    # (materializer sorts via parse_okx_public_trades_v1).
    ordered = sorted([later, earlier], key=lambda t: (int(t.provider_ts_ms), t.trade_id))
    revised, kind, _, _ = apply_okx_public_trades_to_open_candle_v1(
        bars, ordered, previously_applied_trade_ids=[], interval_seconds=60
    )
    assert kind == "SAME_TIMESTAMP_REVISION"
    assert revised[0].open == "100"
    assert revised[0].high == "105"
    assert revised[0].low == "95"
    # Close follows last applied in deterministic sort order (later trade).
    assert revised[0].close == "105"
    assert revised[0].volume == "3"


def test_empty_trade_seconds_do_not_invent_candles() -> None:
    t0 = "2026-07-25T12:34:00Z"
    bars = [_bar(ts=t0, o="100", h="100", l="100", c="100", v="1", confirm=False)]
    out, kind, applied, meta = apply_okx_public_trades_to_open_candle_v1(
        bars, [], previously_applied_trade_ids=[], interval_seconds=60
    )
    assert kind == "NO_OP"
    assert len(out) == 1
    assert out[0].ts == t0
    assert applied == []
    assert meta["new_trade_count"] == 0


def test_pt1h_path_remains_backward_compatible() -> None:
    t0 = "2026-07-25T00:00:00Z"
    t1 = "2026-07-25T01:00:00Z"
    bars = [_bar(ts=t0, o="100", h="102", l="99", c="101", v="10", confirm=False)]
    _, _, applied, _ = apply_okx_public_trades_to_open_candle_v1(
        bars,
        [_trade(trade_id="seed", px="101", sz="1", ts_ms=_ms("2026-07-25T00:05:00Z"))],
        previously_applied_trade_ids=None,
        interval_seconds=3600,
    )
    nxt = _trade(trade_id="n1", px="110", sz="4", ts_ms=_ms("2026-07-25T01:00:05Z"))
    bars_n, kind_n, _, _ = apply_okx_public_trades_to_open_candle_v1(
        bars, [nxt], previously_applied_trade_ids=applied, interval_seconds=3600
    )
    assert kind_n == "NEW_INTERVAL_APPEND"
    assert bars_n[1].ts == t1
    reduced, kind = reduce_okx_ohlcv_bars_v1(
        bars,
        [
            _bar(ts=t0, o="100", h="102", l="99", c="101", v="10", confirm=True),
            _bar(ts=t1, o="110", h="110", l="110", c="110", v="4", confirm=False),
        ],
        interval_seconds=3600,
    )
    assert kind == "NEW_INTERVAL_APPEND"
    assert len(reduced) == 2


def test_materialize_pt1m_document_reports_interval(
    tmp_path: Path,
) -> None:
    selection = tmp_path / "selection.json"
    selection.write_text("{}", encoding="utf-8")
    client = _FakeOkxClient(captured_at="2026-07-25T12:34:30Z")
    result = materialize_selected_okx_ohlcv_readmodel_v1(
        archive_root=tmp_path,
        selected_instrument=INSTRUMENT,
        selected_provider_instrument_id=INSTRUMENT,
        selected_venue="okx",
        selection_bundle_id="bundle-pt1m",
        selection_path=selection,
        bar="PT1M",
        client=client,  # type: ignore[arg-type]
    )
    assert result["interval"] == "PT1M"
    assert client.candle_bars == ["1m"]
    doc = json.loads(
        (tmp_path / "readmodels" / "okx_selected_instrument_ohlcv_readmodel.v1.json").read_text(
            encoding="utf-8"
        )
    )
    assert doc["interval"] == "PT1M"
    assert doc["provider_bar"] == "1m"
    assert doc["interval_seconds"] == 60
    assert doc["open_candle_live_source"] == OPEN_CANDLE_LIVE_SOURCE_PT1M_V1
    assert doc["bar_count"] == 100
    tip = doc["bars"][-1]
    tip_dt = datetime.fromisoformat(tip["ts"].replace("Z", "+00:00"))
    assert tip_dt.second == 0
    assert tip_dt.microsecond == 0
    # Contiguous PT1M history: last closed precedes open tip by exactly 60s.
    closed = [b for b in doc["bars"] if b["confirm"]]
    assert closed
    last_closed = datetime.fromisoformat(closed[-1]["ts"].replace("Z", "+00:00"))
    assert (tip_dt - last_closed).total_seconds() == 60.0


def test_materialize_pt1h_still_accepted(tmp_path: Path) -> None:
    selection = tmp_path / "selection.json"
    selection.write_text("{}", encoding="utf-8")
    client = _FakeOkxClient(captured_at="2026-07-25T12:00:30Z")
    result = materialize_selected_okx_ohlcv_readmodel_v1(
        archive_root=tmp_path,
        selected_instrument=INSTRUMENT,
        selected_provider_instrument_id=INSTRUMENT,
        selected_venue="okx",
        selection_bundle_id="bundle-pt1h",
        selection_path=selection,
        bar="PT1H",
        client=client,  # type: ignore[arg-type]
    )
    assert result["interval"] == "PT1H"
    assert client.candle_bars == ["1H"]
    doc = json.loads(
        (tmp_path / "readmodels" / "okx_selected_instrument_ohlcv_readmodel.v1.json").read_text(
            encoding="utf-8"
        )
    )
    assert doc["interval"] == "PT1H"
    assert doc["provider_bar"] == "1H"


def test_unknown_bar_rejected_by_materialize(tmp_path: Path) -> None:
    selection = tmp_path / "selection.json"
    selection.write_text("{}", encoding="utf-8")
    with pytest.raises(OkxOhlcvReadmodelError, match="UNSUPPORTED_BAR_INTERVAL"):
        materialize_selected_okx_ohlcv_readmodel_v1(
            archive_root=tmp_path,
            selected_instrument=INSTRUMENT,
            selected_provider_instrument_id=INSTRUMENT,
            selected_venue="okx",
            selection_bundle_id="bundle-bad",
            selection_path=selection,
            bar="PT5S",
            client=_FakeOkxClient(captured_at="2026-07-25T12:00:00Z"),  # type: ignore[arg-type]
        )


def test_frontend_poll_interval_is_one_second() -> None:
    assert DEFAULT_DASHBOARD_OHLCV_POLL_INTERVAL_SECONDS == 1
    assert OHLCV_POLL_INTERVAL_SECONDS == 1
    js = (
        Path(__file__).resolve().parents[2] / "static" / "js" / "market_dashboard_landscape_v2.js"
    ).read_text(encoding="utf-8")
    assert "LAST_CANDLE_IN_PLACE" in js
    assert "SAME_TIMESTAMP_LAST_CANDLE_CHANGE" in js
    assert "NEW_CANDLE_APPEND" in js


def test_parse_pt1m_gap_detection_uses_sixty_second_buckets() -> None:
    rows = [
        ["1700000000000", "1", "2", "0.5", "1.5", "10", "10", "15", "1"],
        ["1700000060000", "1.5", "2.5", "1.0", "2.0", "11", "11", "16", "1"],
        ["1700000180000", "2.0", "3.0", "1.5", "2.5", "12", "12", "17", "1"],  # +2m gap
    ]
    bars, notes = parse_okx_history_candles(rows, interval_seconds=60)
    assert len(bars) == 3
    assert "GAP_COUNT:1" in notes
