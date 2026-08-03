"""Continuous read-only OKX OHLCV refresh contracts for Market Landscape V2."""

from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

import pytest
from fastapi.testclient import TestClient

from scripts.ops.primary_evidence_retention_v0 import (
    write_manifest_sha256 as _write_manifest_sha256,
)
from src.ops.okx_public_market_data_client_v1 import OkxPublicCaptureEnvelopeV1
from src.ops.okx_selected_instrument_ohlcv_readmodel_v1 import (
    DEFAULT_DASHBOARD_OHLCV_POLL_INTERVAL_SECONDS,
    OhlcvBarV1,
    OkxOhlcvReadmodelError,
    materialize_selected_okx_ohlcv_readmodel_v1,
    reduce_okx_ohlcv_bars_v1,
    refresh_selected_okx_ohlcv_readmodel_from_archive_v1,
)
from src.webui.app import create_app
from src.webui.market_dashboard_landscape_shell_router_v2 import (
    build_ohlcv_poll_response_v1,
)
from src.webui.workflow_dashboard_archive_root_v1 import ENV_ARCHIVE_ROOT

REPO = Path(__file__).resolve().parents[2]
INSTRUMENT = "SATS-USDT-SWAP"


def _iso(dt: datetime) -> str:
    return dt.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


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


class _FakeOkxClient:
    def __init__(
        self,
        *,
        captured_at: str,
        close_px: str = "0.000000009176",
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
        self.calls = 0
        self.paths: list[str] = []

    def get_json(self, path: str, params: dict[str, str]) -> OkxPublicCaptureEnvelopeV1:
        self.calls += 1
        self.paths.append(path)
        if path == "/api/v5/public/mark-price":
            assert params["instId"] == INSTRUMENT
            assert params["instType"] == "SWAP"
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
            assert params["instId"] == INSTRUMENT
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
        assert params["instId"] == INSTRUMENT
        start = datetime(2026, 7, 20, 18, 0, 0, tzinfo=timezone.utc)
        rows: list[list[str]] = []
        for i in range(100):
            ts = start + timedelta(hours=i)
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
                close = "0.000000009200"
                rows.append([ms, close, close, close, close, "10", "10", "10", confirm])
        body = json.dumps({"code": "0", "msg": "", "data": rows})
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
            raw_payload_digest="a" * 64,
            byte_size=len(body.encode("utf-8")),
            raw_body_utf8=body,
        )


class _FailingOkxClient:
    calls = 0

    def get_json(self, path: str, params: dict[str, str]) -> OkxPublicCaptureEnvelopeV1:
        self.calls += 1
        raise RuntimeError("PROVIDER_DOWN")


def _write_universe(archive_root: Path, *, symbol: str = INSTRUMENT) -> Path:
    readmodels = archive_root / "readmodels"
    readmodels.mkdir(parents=True, exist_ok=True)
    generated_at = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    universe = {
        "schema_name": "universe_selection_readmodel.v1",
        "schema_version": 1,
        "generated_at": generated_at,
        "source_run_id": "okx_continuous_refresh_v1",
        "source_stage": "paper",
        "non_authorizing": True,
        "fixture_marked": False,
        "universe": [
            {
                "row_id": f"c-{symbol}",
                "symbol": symbol,
                "rank": 1,
                "exchange": "okx",
            }
        ],
        "ranking": [
            {
                "row_id": f"r-c-{symbol}",
                "symbol": symbol,
                "rank": 1,
                "notes": "futures_upstream_adapter_v1",
            }
        ],
        "selected_future": {
            "row_id": f"s-c-{symbol}",
            "symbol": symbol,
            "rank": 1,
            "truth_status": "PERSISTED",
            "selection_reason": "upstream_explicit_selection",
        },
        "market_snapshot": {
            "truth_status": "PERSISTED",
            "source_kind": "futures_upstream_adapter_v1",
            "snapshot_id": f"u2c-{symbol}",
            "exchange": "okx",
            "captured_at": None,
        },
        "evidence": {
            "producer_contract": "universe_selection_producer.v1",
            "storage_target": "readmodels/universe_selection_readmodel.v1.json",
            "links": [],
        },
        "missing_truth": {
            "universe": "PERSISTED",
            "ranking": "PERSISTED",
            "selected_future": "PERSISTED",
            "future_detail": "AVAILABLE",
            "orders_fills_pnl": "NOT_PERSISTED",
        },
    }
    path = readmodels / "universe_selection_readmodel.v1.json"
    path.write_text(json.dumps(universe, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    _write_manifest_sha256(readmodels)
    return path


def test_open_candle_reducer_same_timestamp_revisions_then_append() -> None:
    """Mandatory A/B/C same-ts revisions + D new-interval append at the reduce boundary."""
    t0 = "2026-07-25T00:00:00Z"
    t1 = "2026-07-25T01:00:00Z"
    a = [_bar(ts=t0, o="100", h="100", l="100", c="100", v="1", confirm=False)]
    bars_a, kind_a = reduce_okx_ohlcv_bars_v1(None, a)
    assert kind_a == "BOOTSTRAP"
    assert len(bars_a) == 1
    assert bars_a[0].close == "100"

    b = [_bar(ts=t0, o="100", h="103", l="100", c="103", v="2", confirm=False)]
    bars_b, kind_b = reduce_okx_ohlcv_bars_v1(bars_a, b)
    assert kind_b == "SAME_TIMESTAMP_REVISION"
    assert len(bars_b) == 1
    assert bars_b[0].open == "100"
    assert bars_b[0].high == "103"
    assert bars_b[0].low == "100"
    assert bars_b[0].close == "103"
    assert bars_b[0].volume == "2"

    c = [_bar(ts=t0, o="100", h="103", l="98", c="98", v="3", confirm=False)]
    bars_c, kind_c = reduce_okx_ohlcv_bars_v1(bars_b, c)
    assert kind_c == "SAME_TIMESTAMP_REVISION"
    assert len(bars_c) == 1
    assert bars_c[0].open == "100"
    assert bars_c[0].high == "103"
    assert bars_c[0].low == "98"
    assert bars_c[0].close == "98"
    assert bars_c[0].volume == "3"

    # Identical OHLCV at same timestamp is a no-op (not candle motion).
    bars_noop, kind_noop = reduce_okx_ohlcv_bars_v1(bars_c, c)
    assert kind_noop == "NO_OP"
    assert bars_noop is bars_c or [x.to_json_dict() for x in bars_noop] == [
        x.to_json_dict() for x in bars_c
    ]

    d_prev_sealed = _bar(ts=t0, o="100", h="103", l="98", c="98", v="3", confirm=True)
    d_new = _bar(ts=t1, o="101", h="101", l="101", c="101", v="1", confirm=False)
    bars_d, kind_d = reduce_okx_ohlcv_bars_v1(bars_c, [d_prev_sealed, d_new])
    assert kind_d == "NEW_INTERVAL_APPEND"
    assert len(bars_d) == 2
    assert bars_d[0].ts == t0
    assert bars_d[0].confirm is True
    assert bars_d[0].close == "98"
    assert bars_d[1].ts == t1
    assert bars_d[1].close == "101"

    # Open regression and high/low regressions fail closed.
    with pytest.raises(OkxOhlcvReadmodelError, match="OPEN_REGRESSION"):
        reduce_okx_ohlcv_bars_v1(
            bars_c,
            [_bar(ts=t0, o="99", h="103", l="98", c="98", v="3", confirm=False)],
        )
    with pytest.raises(OkxOhlcvReadmodelError, match="HIGH_REGRESSION"):
        reduce_okx_ohlcv_bars_v1(
            bars_c,
            [_bar(ts=t0, o="100", h="102", l="98", c="98", v="3", confirm=False)],
        )
    with pytest.raises(OkxOhlcvReadmodelError, match="LOW_REGRESSION"):
        reduce_okx_ohlcv_bars_v1(
            bars_c,
            [_bar(ts=t0, o="100", h="103", l="99", c="98", v="3", confirm=False)],
        )


def test_volume_revision_moves_candle_series_digest(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from src.webui.market_dashboard_landscape_v2.presenter import (
        serialize_ohlcv_browser_payload_v1,
    )

    archive = tmp_path / "archive"
    selection = _write_universe(archive)
    monkeypatch.setenv(ENV_ARCHIVE_ROOT, str(archive))
    materialize_selected_okx_ohlcv_readmodel_v1(
        archive_root=archive,
        selected_instrument=INSTRUMENT,
        selected_provider_instrument_id=INSTRUMENT,
        selected_venue="okx",
        selection_bundle_id="bundle-a",
        selection_path=selection,
        client=_FakeOkxClient(  # type: ignore[arg-type]
            captured_at="2026-07-25T00:00:00Z",
            open_px="0.000000009100",
            high_px="0.000000009100",
            low_px="0.000000009100",
            close_px="0.000000009100",
            volume="10",
            mark_px="0.000000009100",
        ),
    )
    path = archive / "readmodels/okx_selected_instrument_ohlcv_readmodel.v1.json"
    first = serialize_ohlcv_browser_payload_v1(json.loads(path.read_text(encoding="utf-8")))
    assert first is not None
    refresh_selected_okx_ohlcv_readmodel_from_archive_v1(
        archive_root=archive,
        client=_FakeOkxClient(  # type: ignore[arg-type]
            captured_at="2026-07-25T00:00:03Z",
            open_px="0.000000009100",
            high_px="0.000000009100",
            low_px="0.000000009100",
            close_px="0.000000009100",
            volume="25",
            mark_px="0.000000009100",
        ),
        force=True,
    )
    second_doc = json.loads(path.read_text(encoding="utf-8"))
    second = serialize_ohlcv_browser_payload_v1(second_doc)
    assert second is not None
    assert first["last_timestamp"] == second["last_timestamp"]
    assert first["bars"][-1]["close"] == second["bars"][-1]["close"]
    assert first["bars"][-1]["volume"] != second["bars"][-1]["volume"]
    assert first["candle_series_digest"] != second["candle_series_digest"]
    assert second_doc.get("ohlcv_revision_kind") == "SAME_TIMESTAMP_REVISION"
    assert second.get("close_source_semantics") == ("okx_market_candles_close_plus_public_trades")
    assert second.get("mark_source_semantics") == ("okx_public_mark_price_markPx_metadata_only")
    assert second.get("open_candle_live_source") == "okx_public_trades_into_pt1h_v1"
    assert second.get("trades_endpoint") == "/api/v5/market/trades"


def test_authentic_okx_maps_and_newer_snapshot_advances(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    archive = tmp_path / "archive"
    selection = _write_universe(archive)
    monkeypatch.setenv(ENV_ARCHIVE_ROOT, str(archive))

    client_a = _FakeOkxClient(
        captured_at="2026-07-25T00:00:00Z",
        open_px="0.000000009100",
        high_px="0.000000009100",
        low_px="0.000000009100",
        close_px="0.000000009100",
    )
    first = materialize_selected_okx_ohlcv_readmodel_v1(
        archive_root=archive,
        selected_instrument=INSTRUMENT,
        selected_provider_instrument_id=INSTRUMENT,
        selected_venue="okx",
        selection_bundle_id="bundle-a",
        selection_path=selection,
        client=client_a,  # type: ignore[arg-type]
    )
    assert first["bar_count"] == 100
    assert first["last_closed_timestamp"] is not None

    client_b = _FakeOkxClient(
        captured_at="2026-07-25T00:05:00Z",
        open_px="0.000000009100",
        high_px="0.000000009500",
        low_px="0.000000009100",
        close_px="0.000000009500",
    )
    second = refresh_selected_okx_ohlcv_readmodel_from_archive_v1(
        archive_root=archive,
        client=client_b,  # type: ignore[arg-type]
        force=True,
    )
    assert second["status"] == "OK"
    assert second["refresh_attempted"] is True
    assert second["captured_at"] == "2026-07-25T00:05:00Z"
    assert second["captured_at"] != first.get("captured_at")
    assert second["ohlcv"]["instrument_id"] == INSTRUMENT
    assert second["ohlcv"]["venue"] == "okx"
    assert second["ohlcv"]["bars"][-1]["close"] == "0.000000009500"
    assert second["ohlcv"]["bars"][-1]["open"] == "0.000000009100"
    assert second["ohlcv"]["live_mark_price"] == "0.000000009500"
    assert second["ohlcv"].get("ohlcv_revision_kind") == "SAME_TIMESTAMP_REVISION"
    assert "/api/v5/market/candles" in client_b.paths
    assert "/api/v5/market/trades" in client_b.paths
    assert "/api/v5/public/mark-price" in client_b.paths
    assert client_b.calls == 3
    assert second["ohlcv"].get("open_candle_live_source") == "okx_public_trades_into_pt1h_v1"
    assert second["ohlcv"].get("trades_endpoint") == "/api/v5/market/trades"


def test_public_trades_revise_open_candle_when_candles_static(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Static candles + new authentic trade IDs must revise tip OHLCV and digest."""
    archive = tmp_path / "archive"
    selection = _write_universe(archive)
    monkeypatch.setenv(ENV_ARCHIVE_ROOT, str(archive))
    tip_ms = "1784926800000"  # FakeOkx open tip 2026-07-24T21:00:00Z
    seed_ms = "1784926900000"
    new_ms = "1784927400000"
    seed_trades = [
        {
            "instId": INSTRUMENT,
            "tradeId": "seed-1",
            "px": "0.000000009100",
            "sz": "1",
            "side": "buy",
            "ts": seed_ms,
        }
    ]
    materialize_selected_okx_ohlcv_readmodel_v1(
        archive_root=archive,
        selected_instrument=INSTRUMENT,
        selected_provider_instrument_id=INSTRUMENT,
        selected_venue="okx",
        selection_bundle_id="bundle-a",
        selection_path=selection,
        client=_FakeOkxClient(  # type: ignore[arg-type]
            captured_at="2026-07-24T21:05:00Z",
            open_px="0.000000009100",
            high_px="0.000000009100",
            low_px="0.000000009100",
            close_px="0.000000009100",
            volume="10",
            trades=seed_trades,
        ),
    )
    path = archive / "readmodels/okx_selected_instrument_ohlcv_readmodel.v1.json"
    first = json.loads(path.read_text(encoding="utf-8"))
    assert first["last_timestamp"].startswith("2026-07-24T21:00:00")
    assert first["applied_trade_ids"] == ["seed-1"]
    assert first["bars"][-1]["close"] == "0.000000009100"
    assert first["bars"][-1]["volume"] == "10"

    new_trades = seed_trades + [
        {
            "instId": INSTRUMENT,
            "tradeId": "new-2",
            "px": "0.000000009250",
            "sz": "5",
            "side": "sell",
            "ts": new_ms,
        }
    ]
    second = refresh_selected_okx_ohlcv_readmodel_from_archive_v1(
        archive_root=archive,
        client=_FakeOkxClient(  # type: ignore[arg-type]
            captured_at="2026-07-24T21:10:00Z",
            open_px="0.000000009100",
            high_px="0.000000009100",
            low_px="0.000000009100",
            close_px="0.000000009100",
            volume="10",
            trades=new_trades,
        ),
        force=True,
    )
    assert second["status"] == "OK"
    tip = second["ohlcv"]["bars"][-1]
    assert tip["ts"].startswith("2026-07-24T21:00:00")
    assert tip["open"] == "0.000000009100"
    assert tip["high"] == "0.000000009250"
    assert tip["low"] == "0.000000009100"
    assert tip["close"] == "0.000000009250"
    assert tip["volume"] == "15"
    assert second["ohlcv"]["ohlcv_revision_kind"] == "SAME_TIMESTAMP_REVISION"
    assert second["ohlcv"]["trade_revision_kind"] == "SAME_TIMESTAMP_REVISION"
    assert second["ohlcv"]["candle_revision_kind"] == "NO_OP"
    assert "new-2" in second["ohlcv"]["applied_trade_ids"]
    assert tip_ms  # tip bucket provenance anchor


def test_provider_failure_does_not_fabricate_or_advance(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    archive = tmp_path / "archive"
    selection = _write_universe(archive)
    monkeypatch.setenv(ENV_ARCHIVE_ROOT, str(archive))
    good = _FakeOkxClient(captured_at="2026-07-25T00:00:00Z")
    materialize_selected_okx_ohlcv_readmodel_v1(
        archive_root=archive,
        selected_instrument=INSTRUMENT,
        selected_provider_instrument_id=INSTRUMENT,
        selected_venue="okx",
        selection_bundle_id="bundle-a",
        selection_path=selection,
        client=good,  # type: ignore[arg-type]
    )
    before = json.loads(
        (archive / "readmodels/okx_selected_instrument_ohlcv_readmodel.v1.json").read_text(
            encoding="utf-8"
        )
    )
    failing = _FailingOkxClient()
    result = refresh_selected_okx_ohlcv_readmodel_from_archive_v1(
        archive_root=archive,
        client=failing,  # type: ignore[arg-type]
        force=True,
    )
    after = json.loads(
        (archive / "readmodels/okx_selected_instrument_ohlcv_readmodel.v1.json").read_text(
            encoding="utf-8"
        )
    )
    assert result["status"] == "REFRESH_FAILED"
    assert result["fabricated"] is False
    assert failing.calls == 1
    assert after["captured_at"] == before["captured_at"]
    assert after["bars"] == before["bars"]


def test_instrument_mismatch_fail_closed(tmp_path: Path) -> None:
    archive = tmp_path / "archive"
    selection = _write_universe(archive, symbol=INSTRUMENT)
    good = _FakeOkxClient(captured_at="2026-07-25T00:00:00Z")
    materialize_selected_okx_ohlcv_readmodel_v1(
        archive_root=archive,
        selected_instrument=INSTRUMENT,
        selected_provider_instrument_id=INSTRUMENT,
        selected_venue="okx",
        selection_bundle_id="bundle-a",
        selection_path=selection,
        client=good,  # type: ignore[arg-type]
    )
    # Corrupt selection identity relative to persisted OHLCV.
    _write_universe(archive, symbol="ETH-USDT-SWAP")
    with pytest.raises(Exception) as excinfo:
        refresh_selected_okx_ohlcv_readmodel_from_archive_v1(
            archive_root=archive,
            client=good,  # type: ignore[arg-type]
            force=True,
        )
    assert "INSTRUMENT_MISMATCH" in str(excinfo.value)


def test_poll_endpoint_readonly_and_advances_without_restart(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    archive = tmp_path / "archive"
    selection = _write_universe(archive)
    monkeypatch.setenv(ENV_ARCHIVE_ROOT, str(archive))
    client_a = _FakeOkxClient(captured_at="2026-07-25T00:00:00Z")
    materialize_selected_okx_ohlcv_readmodel_v1(
        archive_root=archive,
        selected_instrument=INSTRUMENT,
        selected_provider_instrument_id=INSTRUMENT,
        selected_venue="okx",
        selection_bundle_id="bundle-a",
        selection_path=selection,
        client=client_a,  # type: ignore[arg-type]
    )

    app = create_app()
    http = TestClient(app)
    first = http.get("/api/market/landscape/ohlcv")
    assert first.status_code == 200
    body1 = first.json()
    assert body1["schema_name"] == "market_landscape_ohlcv_poll_response.v1"
    assert body1["write_methods"] == []
    assert body1["orders"] is False
    assert body1["runtime_activation"] is False
    assert body1["direct_browser_okx"] is False
    assert body1["selected_instrument_id"] == INSTRUMENT
    assert body1["venue"] == "OKX"
    assert body1["browser_payload"]["bar_count"] == 100
    digest1 = body1["payload_digest"]
    captured1 = body1["captured_at"]

    client_b = _FakeOkxClient(captured_at="2026-07-25T00:10:00Z", close_px="0.000000009999")

    # Inject fake client into poll builder path via monkeypatch of refresh helper.
    def _refresh(**kwargs: Any) -> dict[str, Any]:
        kwargs = dict(kwargs)
        kwargs["client"] = client_b
        kwargs["force"] = True
        return refresh_selected_okx_ohlcv_readmodel_from_archive_v1(**kwargs)

    monkeypatch.setattr(
        "src.webui.market_dashboard_landscape_shell_router_v2.refresh_selected_okx_ohlcv_readmodel_from_archive_v1",
        _refresh,
        raising=False,
    )
    # Patch where the builder imports from.
    import src.ops.okx_selected_instrument_ohlcv_readmodel_v1 as ohlcv_mod

    monkeypatch.setattr(
        ohlcv_mod,
        "refresh_selected_okx_ohlcv_readmodel_from_archive_v1",
        _refresh,
    )

    second = build_ohlcv_poll_response_v1(force_refresh=True, client=client_b)
    assert second["captured_at"] == "2026-07-25T00:10:00Z"
    assert second["captured_at"] != captured1
    assert second["payload_digest"] != digest1
    assert second["browser_payload"]["bars"][-1]["close"] == pytest.approx(9.999e-09)
    assert http.get("/market").status_code == 200


def test_market_page_exposes_poll_contract_and_no_order_controls(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    archive = tmp_path / "archive"
    selection = _write_universe(archive)
    monkeypatch.setenv(ENV_ARCHIVE_ROOT, str(archive))
    client = _FakeOkxClient(captured_at="2026-07-25T00:00:00Z")
    materialize_selected_okx_ohlcv_readmodel_v1(
        archive_root=archive,
        selected_instrument=INSTRUMENT,
        selected_provider_instrument_id=INSTRUMENT,
        selected_venue="okx",
        selection_bundle_id="bundle-a",
        selection_path=selection,
        client=client,  # type: ignore[arg-type]
    )
    app = create_app()
    http = TestClient(app)
    resp = http.get("/market")
    assert resp.status_code == 200
    html = resp.text
    assert 'data-mdl-ohlcv-poll-path="/api/market/landscape/ohlcv"' in html
    assert (
        f'data-mdl-ohlcv-poll-interval-seconds="{DEFAULT_DASHBOARD_OHLCV_POLL_INTERVAL_SECONDS}"'
        in html
    )
    assert 'data-mdl-field="ohlcv_captured_at"' in html
    assert 'data-mdl-field="ohlcv_latest_candle_at"' in html
    assert 'data-mdl-field="ohlcv_open"' in html
    assert 'data-mdl-field="ohlcv_close"' in html
    assert 'data-mdl-field="ohlcv_volume"' in html
    assert 'data-mdl-field="ohlcv_revision"' in html
    assert 'data-mdl-field="ohlcv_live_mark"' in html
    assert "data-mdl-data-connection-state" in html
    assert 'data-mdl-decision-strip="true"' in html
    assert "HEALTHY" in html or "LIVE_DATA" in html or "MISSING_SOURCE" in html or "STALE" in html
    assert "OKX" in html
    assert INSTRUMENT in html
    assert "www.okx.com" not in html
    assert 'method="post"' not in html.lower()
    assert "place order" not in html.lower()
    assert "LIVE_AUTHORIZED" not in html or 'content="false"' in html
    assert "kraken" not in html.lower() or "historical" in html.lower()


def test_open_candle_mark_update_same_timestamp_is_mark_only_not_geometry(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Same candle ts + changed mark ⇒ candle_series_digest stable; mark never mutates close."""
    from src.webui.market_dashboard_landscape_v2.presenter import (
        serialize_ohlcv_browser_payload_v1,
    )

    archive = tmp_path / "archive"
    selection = _write_universe(archive)
    monkeypatch.setenv(ENV_ARCHIVE_ROOT, str(archive))
    first_client = _FakeOkxClient(
        captured_at="2026-07-25T00:00:00Z",
        close_px="0.000000009100",
        mark_px="0.000000009100",
    )
    materialize_selected_okx_ohlcv_readmodel_v1(
        archive_root=archive,
        selected_instrument=INSTRUMENT,
        selected_provider_instrument_id=INSTRUMENT,
        selected_venue="okx",
        selection_bundle_id="bundle-a",
        selection_path=selection,
        client=first_client,  # type: ignore[arg-type]
    )
    path = archive / "readmodels/okx_selected_instrument_ohlcv_readmodel.v1.json"
    first_doc = json.loads(path.read_text(encoding="utf-8"))
    # Honest freshness for connection-state projection (synthetic bars are aged).
    first_doc["freshness_state"] = "fresh"
    first_doc["is_stale"] = False
    path.write_text(json.dumps(first_doc, indent=2) + "\n", encoding="utf-8")
    _write_manifest_sha256(archive / "readmodels")
    first_payload = serialize_ohlcv_browser_payload_v1(first_doc)
    assert first_payload is not None
    ts1 = first_payload["last_timestamp"]
    close1 = first_payload["bars"][-1]["close"]
    display1 = first_payload["bars"][-1]["display_close"]
    chart1 = first_payload["chart_digest"]
    series1 = first_payload["candle_series_digest"]
    meta1 = first_payload["metadata_digest"]
    assert first_payload["bars"][-1]["provisional"] is True
    assert chart1 == series1

    second_client = _FakeOkxClient(
        captured_at="2026-07-25T00:00:03Z",
        close_px="0.000000009100",
        mark_px="0.000000009250",
    )
    refreshed = refresh_selected_okx_ohlcv_readmodel_from_archive_v1(
        archive_root=archive,
        client=second_client,  # type: ignore[arg-type]
        force=True,
    )
    assert refreshed["status"] == "OK"
    second_doc = json.loads(path.read_text(encoding="utf-8"))
    second_doc["freshness_state"] = "fresh"
    second_doc["is_stale"] = False
    path.write_text(json.dumps(second_doc, indent=2) + "\n", encoding="utf-8")
    _write_manifest_sha256(archive / "readmodels")
    second_payload = serialize_ohlcv_browser_payload_v1(second_doc)
    assert second_payload is not None
    ts2 = second_payload["last_timestamp"]
    close2 = second_payload["bars"][-1]["close"]
    display2 = second_payload["bars"][-1]["display_close"]
    chart2 = second_payload["chart_digest"]
    series2 = second_payload["candle_series_digest"]
    meta2 = second_payload["metadata_digest"]
    assert ts1 == ts2
    assert close1 == close2
    assert display1 == display2
    assert display2 == pytest.approx(9.1e-09)
    assert chart1 == chart2
    assert series1 == series2
    assert meta1 != meta2
    assert second_payload["live_mark_price"] == pytest.approx(9.25e-09)
    # Closed bars remain ordered / not duplicated.
    bars = second_payload["bars"]
    assert len(bars) == 100
    assert [b["ts"] for b in bars] == sorted(b["ts"] for b in bars)
    assert len({b["ts"] for b in bars}) == 100
    # Closed candle OHLC unchanged relative to first refresh for early bars.
    assert first_payload["bars"][0]["close"] == bars[0]["close"]
    assert bars[0]["confirm"] is True

    # Poll response connection state with injected skip refresh (no live OKX).
    def _skip(**kwargs: Any) -> dict[str, Any]:
        retained = json.loads(path.read_text(encoding="utf-8"))
        retained["freshness_state"] = "fresh"
        retained["is_stale"] = False
        return {
            "status": "SKIPPED_RECENT",
            "refresh_attempted": False,
            "selected_instrument": INSTRUMENT,
            "selected_venue": "okx",
            "captured_at": retained.get("captured_at"),
            "last_timestamp": retained.get("last_timestamp"),
            "ohlcv": retained,
        }

    import src.ops.okx_selected_instrument_ohlcv_readmodel_v1 as ohlcv_mod

    monkeypatch.setattr(
        ohlcv_mod,
        "refresh_selected_okx_ohlcv_readmodel_from_archive_v1",
        _skip,
    )
    poll = build_ohlcv_poll_response_v1(force_refresh=False)
    assert poll["data_connection_state"] == "HEALTHY"
    assert poll["direct_browser_okx"] is False
    assert poll["orders"] is False


def test_captured_at_only_does_not_change_chart_digest(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from src.webui.market_dashboard_landscape_v2.presenter import (
        serialize_ohlcv_browser_payload_v1,
    )

    archive = tmp_path / "archive"
    selection = _write_universe(archive)
    monkeypatch.setenv(ENV_ARCHIVE_ROOT, str(archive))
    client_a = _FakeOkxClient(
        captured_at="2026-07-25T00:00:00Z",
        close_px="0.000000009100",
        mark_px="0.000000009100",
    )
    materialize_selected_okx_ohlcv_readmodel_v1(
        archive_root=archive,
        selected_instrument=INSTRUMENT,
        selected_provider_instrument_id=INSTRUMENT,
        selected_venue="okx",
        selection_bundle_id="bundle-a",
        selection_path=selection,
        client=client_a,  # type: ignore[arg-type]
    )
    path = archive / "readmodels/okx_selected_instrument_ohlcv_readmodel.v1.json"
    first_payload = serialize_ohlcv_browser_payload_v1(json.loads(path.read_text(encoding="utf-8")))
    client_b = _FakeOkxClient(
        captured_at="2026-07-25T00:00:05Z",
        close_px="0.000000009100",
        mark_px="0.000000009100",
    )
    refresh_selected_okx_ohlcv_readmodel_from_archive_v1(
        archive_root=archive,
        client=client_b,  # type: ignore[arg-type]
        force=True,
    )
    second_doc = json.loads(path.read_text(encoding="utf-8"))
    second_payload = serialize_ohlcv_browser_payload_v1(second_doc)
    assert first_payload is not None and second_payload is not None
    assert first_payload["chart_digest"] == second_payload["chart_digest"]
    assert first_payload["candle_series_digest"] == second_payload["candle_series_digest"]
    assert first_payload["metadata_digest"] != second_payload["metadata_digest"]
    assert first_payload["captured_at"] != second_payload["captured_at"]
    assert first_payload["payload_digest"] != second_payload["payload_digest"]


def test_same_timestamp_ohlc_change_moves_candle_series_digest_only(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Authentic O/H/L/C change at same open-candle ts must move candle_series_digest."""
    from src.webui.market_dashboard_landscape_v2.presenter import (
        serialize_ohlcv_browser_payload_v1,
    )

    archive = tmp_path / "archive"
    selection = _write_universe(archive)
    monkeypatch.setenv(ENV_ARCHIVE_ROOT, str(archive))
    materialize_selected_okx_ohlcv_readmodel_v1(
        archive_root=archive,
        selected_instrument=INSTRUMENT,
        selected_provider_instrument_id=INSTRUMENT,
        selected_venue="okx",
        selection_bundle_id="bundle-a",
        selection_path=selection,
        client=_FakeOkxClient(  # type: ignore[arg-type]
            captured_at="2026-07-25T00:00:00Z",
            open_px="0.000000009100",
            high_px="0.000000009100",
            low_px="0.000000009100",
            close_px="0.000000009100",
            mark_px="0.000000009100",
        ),
    )
    path = archive / "readmodels/okx_selected_instrument_ohlcv_readmodel.v1.json"
    first_payload = serialize_ohlcv_browser_payload_v1(json.loads(path.read_text(encoding="utf-8")))
    assert first_payload is not None
    refresh_selected_okx_ohlcv_readmodel_from_archive_v1(
        archive_root=archive,
        client=_FakeOkxClient(  # type: ignore[arg-type]
            captured_at="2026-07-25T00:00:03Z",
            open_px="0.000000009100",
            high_px="0.000000009220",
            low_px="0.000000009100",
            close_px="0.000000009220",
            mark_px="0.000000009220",
        ),
        force=True,
    )
    second_payload = serialize_ohlcv_browser_payload_v1(
        json.loads(path.read_text(encoding="utf-8"))
    )
    assert second_payload is not None
    assert first_payload["last_timestamp"] == second_payload["last_timestamp"]
    assert first_payload["bars"][-1]["close"] != second_payload["bars"][-1]["close"]
    assert first_payload["candle_series_digest"] != second_payload["candle_series_digest"]
    assert first_payload["chart_digest"] != second_payload["chart_digest"]
    assert second_payload["bars"][-1]["display_close"] == second_payload["bars"][-1]["close"]


def test_js_layout_stability_and_update_classification_contracts() -> None:
    js = (REPO / "static/js/market_dashboard_landscape_v2.js").read_text(encoding="utf-8")
    css = (REPO / "static/css/market_dashboard_landscape_v2.css").read_text(encoding="utf-8")
    html = (REPO / "templates/peak_trade_dashboard/market_landscape_v2.html").read_text(
        encoding="utf-8"
    )
    assert "candle_series_digest" in js
    assert "metadata_digest" in js
    assert "SAME_TIMESTAMP_LAST_CANDLE_CHANGE" in js
    assert "MARK_ONLY" in js
    assert "METADATA_ONLY" in js
    assert "LAST_CANDLE_IN_PLACE" in js
    assert "volume" in js
    assert "data-mdl-chart-candle-volume" in js
    assert 'data-mdl-field="ohlcv_open"' in js or 'data-mdl-field="ohlcv_open"' in html
    assert 'data-mdl-field="ohlcv_close"' in html
    assert 'data-mdl-field="ohlcv_volume"' in html
    assert 'data-mdl-field="ohlcv_revision"' in html
    assert "resolveCssBox" in js
    assert "syncBackingStore" in js
    assert "devicePixelRatio" in js
    # Must not feed stage/clientHeight back into canvas.style.height (growth loop).
    assert "canvas.style.height" not in js
    assert "canvas.style.width" not in js
    assert "stage.scrollHeight" not in js
    assert "stage.clientHeight || 360" not in js
    assert "Math.max(220, stage.clientHeight" not in js
    assert "www.okx.com" not in js
    assert "wss://ws.okx.com" not in js
    assert "kraken" not in js.lower()
    assert "DEGRADED" in js or "RECONNECTING" in js or "DISCONNECTED" in js
    assert "MAX_BACKOFF_SECONDS" in js
    # CSS owns fixed stage/meta bands; chart must not flex-grow the Decision strip away.
    assert "--mdl-stage-height" in css
    assert "max-height: var(--mdl-stage-height)" in css
    assert "--mdl-chart-meta-band" in css
    assert "flex: 0 0 auto" in css
    assert "min(56vh, 580px)" not in css
    assert 'data-mdl-decision-strip="true"' in html
    assert "text-overflow: ellipsis" in css


def test_live_data_requires_fresh_ohlcv_source_not_mark_cosmetics(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from src.webui.market_dashboard_landscape_v2.presenter import (
        _ohlcv_data_connection_state,
        serialize_ohlcv_browser_payload_v1,
    )
    from src.webui.market_dashboard_landscape_v2.availability import Availability

    archive = tmp_path / "archive"
    selection = _write_universe(archive)
    monkeypatch.setenv(ENV_ARCHIVE_ROOT, str(archive))
    materialize_selected_okx_ohlcv_readmodel_v1(
        archive_root=archive,
        selected_instrument=INSTRUMENT,
        selected_provider_instrument_id=INSTRUMENT,
        selected_venue="okx",
        selection_bundle_id="bundle-a",
        selection_path=selection,
        client=_FakeOkxClient(captured_at="2026-07-25T00:00:00Z"),
    )
    path = archive / "readmodels/okx_selected_instrument_ohlcv_readmodel.v1.json"
    doc = json.loads(path.read_text(encoding="utf-8"))
    doc["freshness_state"] = "fresh"
    doc["is_stale"] = False
    payload = serialize_ohlcv_browser_payload_v1(doc)
    assert payload is not None
    assert (
        _ohlcv_data_connection_state(
            browser_payload=payload,
            ohlcv_payload=doc,
            chart_availability=Availability.AVAILABLE,
        )
        == "HEALTHY"
    )
    # Stale OHLCV source must not claim HEALTHY even if captured_at text exists.
    stale = dict(doc)
    stale["freshness_state"] = "stale"
    stale["is_stale"] = True
    assert (
        _ohlcv_data_connection_state(
            browser_payload=payload,
            ohlcv_payload=stale,
            chart_availability=Availability.STALE,
        )
        == "STALE"
    )
    # Missing candle capture clock → not HEALTHY (O5 age/degraded path; never invent healthy).
    no_cap = dict(doc)
    no_cap.pop("candle_captured_at", None)
    no_cap["captured_at"] = None
    no_cap_state = _ohlcv_data_connection_state(
        browser_payload=payload,
        ohlcv_payload=no_cap,
        chart_availability=Availability.AVAILABLE,
    )
    assert no_cap_state != "HEALTHY"
    assert no_cap_state in {"DEGRADED", "STALE", "MISSING_SOURCE"}


def test_js_uses_chart_digest_alias_and_never_okx_host() -> None:
    js = (REPO / "static/js/market_dashboard_landscape_v2.js").read_text(encoding="utf-8")
    assert "chart_digest" in js
    assert "www.okx.com" not in js
    assert "wss://ws.okx.com" not in js
    assert "kraken" not in js.lower()


def test_poll_interval_targets_visible_intrabar_feedback() -> None:
    from src.webui.market_dashboard_landscape_v2.presenter import (
        OHLCV_POLL_INTERVAL_SECONDS,
    )

    assert DEFAULT_DASHBOARD_OHLCV_POLL_INTERVAL_SECONDS <= 5
    assert DEFAULT_DASHBOARD_OHLCV_POLL_INTERVAL_SECONDS >= 1
    assert OHLCV_POLL_INTERVAL_SECONDS == DEFAULT_DASHBOARD_OHLCV_POLL_INTERVAL_SECONDS


def test_ohlcv_refresh_preserves_universe_selection_manifest_binding(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Continuous OHLCV writes must not invalidate universe_selection binding."""
    from datetime import datetime, timezone

    from src.webui.market_dashboard_landscape_producer_binding_v2 import (
        bind_market_universe_slots,
    )

    archive = tmp_path / "archive"
    selection = _write_universe(archive)
    monkeypatch.setenv(ENV_ARCHIVE_ROOT, str(archive))
    materialize_selected_okx_ohlcv_readmodel_v1(
        archive_root=archive,
        selected_instrument=INSTRUMENT,
        selected_provider_instrument_id=INSTRUMENT,
        selected_venue="okx",
        selection_bundle_id="bundle-a",
        selection_path=selection,
        client=_FakeOkxClient(captured_at="2026-07-25T00:00:00Z"),  # type: ignore[arg-type]
    )
    first_slots = bind_market_universe_slots(generated_at=datetime.now(timezone.utc))
    assert first_slots["universe_ranking"].availability.value == "AVAILABLE"
    assert first_slots["universe_ranking"].selected_instrument_id == INSTRUMENT

    refresh_selected_okx_ohlcv_readmodel_from_archive_v1(
        archive_root=archive,
        client=_FakeOkxClient(  # type: ignore[arg-type]
            captured_at="2026-07-25T00:00:03Z",
            close_px="0.000000009200",
        ),
        force=True,
    )
    second_slots = bind_market_universe_slots(generated_at=datetime.now(timezone.utc))
    assert second_slots["universe_ranking"].availability.value == "AVAILABLE"
    assert second_slots["universe_ranking"].selected_instrument_id == INSTRUMENT
    assert second_slots["market_instrument"].instrument_id == INSTRUMENT


def test_stale_and_missing_source_fail_closed(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    archive = tmp_path / "archive"
    monkeypatch.setenv(ENV_ARCHIVE_ROOT, str(archive))
    app = create_app()
    http = TestClient(app)
    missing = http.get("/api/market/landscape/ohlcv")
    assert missing.status_code == 200
    body = missing.json()
    assert body["status"] == "MISSING_SOURCE"
    assert body["availability"] == "MISSING_SOURCE"
    assert body["browser_payload"] is None

    selection = _write_universe(archive)
    old = _FakeOkxClient(captured_at="2026-07-20T00:00:00Z")
    materialize_selected_okx_ohlcv_readmodel_v1(
        archive_root=archive,
        selected_instrument=INSTRUMENT,
        selected_provider_instrument_id=INSTRUMENT,
        selected_venue="okx",
        selection_bundle_id="bundle-a",
        selection_path=selection,
        client=old,  # type: ignore[arg-type]
    )
    # Age the on-disk freshness classification by rewriting stale flags honestly.
    path = archive / "readmodels/okx_selected_instrument_ohlcv_readmodel.v1.json"
    doc = json.loads(path.read_text(encoding="utf-8"))
    doc["freshness_state"] = "stale"
    doc["is_stale"] = True
    doc["stale_reason"] = "ohlcv_latest_candle_exceeds_threshold"
    path.write_text(json.dumps(doc, indent=2) + "\n", encoding="utf-8")
    _write_manifest_sha256(archive / "readmodels")

    def _skip_refresh(**kwargs: Any) -> dict[str, Any]:
        retained = json.loads(path.read_text(encoding="utf-8"))
        return {
            "status": "SKIPPED_RECENT",
            "refresh_attempted": False,
            "selected_instrument": INSTRUMENT,
            "selected_venue": "okx",
            "captured_at": retained.get("captured_at"),
            "last_timestamp": retained.get("last_timestamp"),
            "ohlcv": retained,
        }

    import src.ops.okx_selected_instrument_ohlcv_readmodel_v1 as ohlcv_mod

    monkeypatch.setattr(
        ohlcv_mod,
        "refresh_selected_okx_ohlcv_readmodel_from_archive_v1",
        _skip_refresh,
    )
    poll = build_ohlcv_poll_response_v1(force_refresh=False)
    assert poll["availability"] == "STALE"
    assert poll["is_stale"] is True
    assert poll["browser_payload"] is not None
