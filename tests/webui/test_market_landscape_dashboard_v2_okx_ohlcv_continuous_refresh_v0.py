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
    materialize_selected_okx_ohlcv_readmodel_v1,
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


class _FakeOkxClient:
    def __init__(self, *, captured_at: str, close_px: str = "0.000000009176") -> None:
        self.captured_at = captured_at
        self.close_px = close_px
        self.calls = 0

    def get_json(self, path: str, params: dict[str, str]) -> OkxPublicCaptureEnvelopeV1:
        assert path == "/api/v5/market/history-candles"
        assert params["instId"] == INSTRUMENT
        self.calls += 1
        start = datetime(2026, 7, 20, 18, 0, 0, tzinfo=timezone.utc)
        rows: list[list[str]] = []
        for i in range(100):
            ts = start + timedelta(hours=i)
            ms = str(int(ts.timestamp() * 1000))
            confirm = "0" if i == 99 else "1"
            close = self.close_px if i == 99 else "0.000000009200"
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
    universe = {
        "schema_name": "universe_selection_readmodel.v1",
        "schema_version": 1,
        "generated_at": "2026-07-24T21:48:23Z",
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


def test_authentic_okx_maps_and_newer_snapshot_advances(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    archive = tmp_path / "archive"
    selection = _write_universe(archive)
    monkeypatch.setenv(ENV_ARCHIVE_ROOT, str(archive))

    client_a = _FakeOkxClient(captured_at="2026-07-25T00:00:00Z", close_px="0.000000009100")
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

    client_b = _FakeOkxClient(captured_at="2026-07-25T00:05:00Z", close_px="0.000000009500")
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
    assert client_b.calls == 1


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
    assert 'data-mdl-field="ohlcv_freshness"' in html
    assert "OKX" in html
    assert INSTRUMENT in html
    assert "www.okx.com" not in html
    assert 'method="post"' not in html.lower()
    assert "place order" not in html.lower()
    assert "LIVE_AUTHORIZED" not in html or 'content="false"' in html
    assert "kraken" not in html.lower() or "historical" in html.lower()


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
