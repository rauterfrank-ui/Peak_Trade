"""Public OKX trades allowlist + open-candle trade reducer contracts."""

from __future__ import annotations

from datetime import datetime

import pytest

from src.ops.okx_public_market_data_client_v1 import (
    ALLOWED_PATHS,
    OkxPublicMarketDataClientError,
    OkxPublicMarketDataClientV1,
)
from src.ops.okx_selected_instrument_ohlcv_readmodel_v1 import (
    OKX_TRADES_PATH,
    OhlcvBarV1,
    OkxPublicTradeV1,
    apply_okx_public_trades_to_open_candle_v1,
    merge_open_tip_cumulative_interval_volume_v1,
    parse_okx_public_trades_v1,
    reduce_okx_ohlcv_bars_v1,
)


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


def test_public_trades_path_allowed_private_paths_rejected() -> None:
    assert OKX_TRADES_PATH in ALLOWED_PATHS
    client = OkxPublicMarketDataClientV1(
        fetcher=lambda url, timeout: (200, b'{"code":"0","msg":"","data":[]}')
    )
    env = client.get_json(OKX_TRADES_PATH, {"instId": "SATS-USDT-SWAP", "limit": "5"})
    assert env.request_path == OKX_TRADES_PATH
    assert env.provider_code == "0"

    forbidden = [
        "/api/v5/account/balance",
        "/api/v5/trade/order",
        "/api/v5/trade/orders-pending",
        "/api/v5/account/positions",
        "/api/v5/account/set-leverage",
        "/api/v5/users/subaccount/list",
    ]
    for path in forbidden:
        with pytest.raises(OkxPublicMarketDataClientError, match="PATH_NOT_ALLOWED"):
            client.get_json(path, {})


def test_same_bucket_trade_revises_final_candle_and_dedupes() -> None:
    t0 = "2026-07-25T00:00:00Z"
    bars = [_bar(ts=t0, o="100", h="102", l="99", c="101", v="10", confirm=False)]
    seed_trade = _trade(trade_id="t0", px="101", sz="1", ts_ms=_ms("2026-07-25T00:05:00Z"))
    bars_s, kind_s, applied_s, meta_s = apply_okx_public_trades_to_open_candle_v1(
        bars, [seed_trade], previously_applied_trade_ids=None
    )
    assert kind_s == "NO_OP"
    assert meta_s["seeded"] is True
    assert applied_s == ["t0"]
    assert bars_s[0].close == "101"
    assert bars_s[0].volume == "10"

    t1 = _trade(trade_id="t1", px="103", sz="2", ts_ms=_ms("2026-07-25T00:10:00Z"))
    t2 = _trade(trade_id="t2", px="98", sz="3", ts_ms=_ms("2026-07-25T00:12:00Z"))
    bars_r, kind_r, applied_r, meta_r = apply_okx_public_trades_to_open_candle_v1(
        bars_s, [seed_trade, t1, t2], previously_applied_trade_ids=applied_s
    )
    assert kind_r == "SAME_TIMESTAMP_REVISION"
    assert meta_r["new_trade_count"] == 2
    assert len(bars_r) == 1
    assert bars_r[0].open == "100"
    assert bars_r[0].high == "103"
    assert bars_r[0].low == "98"
    assert bars_r[0].close == "98"
    assert bars_r[0].volume == "15"  # 10 + 2 + 3
    assert set(applied_r) == {"t0", "t1", "t2"}

    # Duplicate trade IDs must not double-count volume.
    bars_d, kind_d, applied_d, meta_d = apply_okx_public_trades_to_open_candle_v1(
        bars_r, [seed_trade, t1, t2], previously_applied_trade_ids=applied_r
    )
    assert kind_d == "NO_OP"
    assert meta_d["duplicate_trade_count"] == 3
    assert bars_d[0].volume == "15"
    assert applied_d == applied_r


def test_next_bucket_trade_appends_exactly_one_candle() -> None:
    t0 = "2026-07-25T00:00:00Z"
    t1 = "2026-07-25T01:00:00Z"
    bars = [_bar(ts=t0, o="100", h="102", l="99", c="101", v="10", confirm=False)]
    _, _, applied, _ = apply_okx_public_trades_to_open_candle_v1(
        bars,
        [_trade(trade_id="seed", px="101", sz="1", ts_ms=_ms("2026-07-25T00:05:00Z"))],
        previously_applied_trade_ids=None,
    )
    nxt = _trade(trade_id="n1", px="110", sz="4", ts_ms=_ms("2026-07-25T01:00:05Z"))
    bars_n, kind_n, applied_n, meta_n = apply_okx_public_trades_to_open_candle_v1(
        bars, [nxt], previously_applied_trade_ids=applied
    )
    assert kind_n == "NEW_INTERVAL_APPEND"
    assert meta_n["new_trade_count"] == 1
    assert len(bars_n) == 2
    assert bars_n[0].ts == t0
    assert bars_n[0].confirm is True
    assert bars_n[0].close == "101"
    assert bars_n[1].ts == t1
    assert bars_n[1].open == "110"
    assert bars_n[1].close == "110"
    assert bars_n[1].volume == "4"
    assert "n1" in applied_n


def test_old_trade_before_tip_is_ignored() -> None:
    t0 = "2026-07-25T01:00:00Z"
    bars = [_bar(ts=t0, o="100", h="100", l="100", c="100", v="1", confirm=False)]
    _, _, applied, _ = apply_okx_public_trades_to_open_candle_v1(
        bars, [], previously_applied_trade_ids=[]
    )
    old = _trade(trade_id="old", px="90", sz="9", ts_ms=_ms("2026-07-25T00:30:00Z"))
    bars_o, kind_o, _, meta_o = apply_okx_public_trades_to_open_candle_v1(
        bars, [old], previously_applied_trade_ids=applied
    )
    assert kind_o == "NO_OP"
    assert meta_o["old_trade_count"] == 1
    assert bars_o[0].close == "100"
    assert bars_o[0].volume == "1"


def test_candle_reducer_same_timestamp_numeric_contract() -> None:
    """Deterministic A/B contract: same-ts OHLCV change vs identical NO_OP."""
    t0 = "2026-07-25T00:00:00Z"
    existing = [_bar(ts=t0, o="100", h="102", l="99", c="101", v="10", confirm=False)]
    incoming = [_bar(ts=t0, o="100", h="103", l="98", c="102", v="12", confirm=False)]
    bars, kind = reduce_okx_ohlcv_bars_v1(existing, incoming)
    assert kind == "SAME_TIMESTAMP_REVISION"
    assert kind != "NO_OP"
    assert len(bars) == 1
    assert bars[0].high == "103"
    assert bars[0].low == "98"
    assert bars[0].close == "102"
    assert bars[0].volume == "12"
    bars_n, kind_n = reduce_okx_ohlcv_bars_v1(bars, incoming)
    assert kind_n == "NO_OP"


def test_candle_window_churn_does_not_regress_cumulative_open_volume() -> None:
    """MODEL_A: lower OKX tip volume after prior trade accumulation must not regress."""
    t0 = "2026-07-25T00:00:00Z"
    prior = [_bar(ts=t0, o="100", h="105", l="99", c="104", v="1000", confirm=False)]
    # AUTHENTIC_FULL_REPLACE-style tip with lower candle volume / narrower range.
    incoming = [
        _bar(ts="2026-07-24T23:00:00Z", o="90", h="91", l="89", c="90", v="10", confirm=True),
        _bar(ts=t0, o="100", h="103", l="100", c="102", v="900", confirm=False),
    ]
    reduced, kind = reduce_okx_ohlcv_bars_v1(prior, incoming)
    assert kind == "AUTHENTIC_FULL_REPLACE"
    merged, meta = merge_open_tip_cumulative_interval_volume_v1(prior, reduced)
    assert meta["volume_semantic_model"] == "MODEL_A_CUMULATIVE_INTERVAL_VOLUME"
    assert meta["open_tip_volume_preserved"] is True
    assert merged[-1].ts == t0
    assert merged[-1].open == "100"
    assert merged[-1].volume == "1000"
    assert merged[-1].high == "105"
    assert merged[-1].low == "99"
    assert merged[-1].close == "102"
    # Closed prefix from incoming remains; prior sealed history not invented.
    assert merged[0].confirm is True
    assert merged[0].ts == "2026-07-24T23:00:00Z"


def test_overlapping_trade_batches_do_not_double_count_or_regress_volume() -> None:
    t0 = "2026-07-25T00:00:00Z"
    bars = [_bar(ts=t0, o="100", h="100", l="100", c="100", v="10", confirm=False)]
    batch1 = [
        _trade(trade_id="a", px="101", sz="1", ts_ms=_ms("2026-07-25T00:01:00Z")),
        _trade(trade_id="b", px="102", sz="2", ts_ms=_ms("2026-07-25T00:02:00Z")),
    ]
    # First observation seeds IDs already priced into the candle tip (no double-count).
    bars_s, kind_s, applied, meta_s = apply_okx_public_trades_to_open_candle_v1(
        bars, batch1, previously_applied_trade_ids=None
    )
    assert kind_s == "NO_OP"
    assert meta_s["seeded"] is True
    assert bars_s[0].volume == "10"
    # Re-apply same batch after seed: duplicates only.
    bars_d, kind_d, applied_d, meta_d = apply_okx_public_trades_to_open_candle_v1(
        bars_s, batch1, previously_applied_trade_ids=applied
    )
    assert kind_d == "NO_OP"
    assert meta_d["duplicate_trade_count"] == 2
    assert bars_d[0].volume == "10"
    # Later poll returns truncated window (trade "a" gone) plus one new trade.
    batch2 = [
        _trade(trade_id="b", px="102", sz="2", ts_ms=_ms("2026-07-25T00:02:00Z")),
        _trade(trade_id="c", px="103", sz="3", ts_ms=_ms("2026-07-25T00:03:00Z")),
    ]
    bars3, kind3, applied3, meta3 = apply_okx_public_trades_to_open_candle_v1(
        bars_d, batch2, previously_applied_trade_ids=applied_d
    )
    assert kind3 == "SAME_TIMESTAMP_REVISION"
    assert meta3["duplicate_trade_count"] == 1
    assert meta3["new_trade_count"] == 1
    assert bars3[0].volume == "13"  # 10 + 3; missing "a" from window does not regress
    assert set(applied3) >= {"a", "b", "c"}
    # Cumulative merge against a lower candle tip preserves volume.
    lower_candle = [_bar(ts=t0, o="100", h="103", l="100", c="103", v="12", confirm=False)]
    merged, meta = merge_open_tip_cumulative_interval_volume_v1(bars3, lower_candle)
    assert merged[0].volume == "13"
    assert meta["open_tip_volume_preserved"] is True


def test_parse_okx_public_trades_newest_first_input() -> None:
    rows = [
        {
            "instId": "SATS-USDT-SWAP",
            "tradeId": "2",
            "px": "0.000000009200",
            "sz": "3",
            "side": "sell",
            "ts": _ms("2026-07-25T00:10:00Z"),
        },
        {
            "instId": "SATS-USDT-SWAP",
            "tradeId": "1",
            "px": "0.000000009100",
            "sz": "1",
            "side": "buy",
            "ts": _ms("2026-07-25T00:00:00Z"),
        },
    ]
    parsed = parse_okx_public_trades_v1(rows)
    assert [t.trade_id for t in parsed] == ["1", "2"]
