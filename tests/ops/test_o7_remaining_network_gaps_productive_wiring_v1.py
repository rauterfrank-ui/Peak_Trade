"""Focused tests for O7 remaining-network-gap productive wiring."""

from __future__ import annotations

import json
import time
import urllib.error
import urllib.request
from pathlib import Path

import pytest

from src.ops.canonical_local_launcher_and_process_supervision_v1.constants_v1 import (
    MODE_DASHBOARD_ONLY,
)
from src.ops.canonical_local_launcher_and_process_supervision_v1.lifecycle_v1 import (
    CanonicalLocalLauncherV1,
    LauncherPathsV1,
)
from src.ops.canonical_public_md_and_ohlcv_transport_reconciliation_v1.constants_v1 import (
    INTERVAL_PT1H,
)
from src.ops.canonical_public_md_and_ohlcv_transport_reconciliation_v1.pso_to_o4_o5_live_bridge_v1 import (
    PsoToO4O5LiveBridgeV1,
)
from src.ops.canonical_read_model_and_market_dashboard_rebuild_v1.constants_v1 import (
    CONNECTION_DISCONNECTED,
    CONNECTION_STALE,
    NON_HEALTHY_RENDER_STATES,
)
from src.ops.canonical_read_model_and_market_dashboard_rebuild_v1.durable_read_model_store_v1 import (
    load_durable_read_model_v1,
)
from src.ops.okx_native_instrument_and_mark_price_runtime_binding_fail_closed_v1.normalized_market_data_v1 import (
    NormalizedPublicMarketDataV1,
)


def _md(
    *, mark: float, event_ts: float, receive_ts: float | None = None
) -> NormalizedPublicMarketDataV1:
    recv = float(event_ts if receive_ts is None else receive_ts)
    return NormalizedPublicMarketDataV1(
        canonical_instrument_id="ETH-USDT-SWAP",
        venue_instrument_id="ETH-USDT-SWAP",
        venue="okx",
        mark_px=mark,
        event_ts_unix=event_ts,
        receive_ts_unix=recv,
        mark_price_endpoint="/api/v5/public/mark-price",
        mark_price_field="markPx",
        mapping_digest="wiring-test-digest",
        mapping_version="v1",
    )


@pytest.fixture()
def launcher_env(tmp_path: Path, repo_root: Path):
    state_root = tmp_path / "state"
    log_root = tmp_path / "logs"
    evidence_root = tmp_path / "evidence"
    cfg = tmp_path / "config.json"
    cfg.write_text(
        json.dumps({"mode": "dashboard-only", "o7_wiring": True}, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    paths = LauncherPathsV1(
        repository_root=repo_root,
        state_root=state_root,
        log_root=log_root,
        evidence_root=evidence_root,
    )
    return CanonicalLocalLauncherV1(paths), cfg, state_root


@pytest.fixture()
def repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _http_get(url: str) -> tuple[int, dict]:
    req = urllib.request.Request(url, headers={"Accept": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=2.0) as resp:
            body = json.loads(resp.read().decode("utf-8"))
            return int(resp.status), body
    except urllib.error.HTTPError as exc:
        body = json.loads(exc.read().decode("utf-8"))
        return int(exc.code), body


def test_pso_to_o4_to_o5_bridge_and_dedup(tmp_path: Path) -> None:
    bridge = PsoToO4O5LiveBridgeV1(
        session_id="bridge-sess",
        repository_sha="abc123",
        config_digest="cfgdigest",
        state_root=tmp_path,
        interval=INTERVAL_PT1H,
    )
    t0 = 1_700_000_000.0
    r1 = bridge.ingest_normalized_event(_md(mark=100.0, event_ts=t0, receive_ts=t0 + 0.01))
    assert r1["accepted"] is True
    assert r1["advance"] is True
    assert r1["timestamp_chain"]["market_event_time"] == t0
    assert r1["timestamp_chain"]["ingestion_time"] == t0 + 0.01
    assert r1["timestamp_chain"]["bar_projection_time"] is not None
    assert r1["timestamp_chain"]["read_model_commit_time"] is not None
    assert r1["timestamp_chain"]["http_response_observed_time"] is None

    # Exact duplicate identity must not advance authoritative bar state.
    r_dup = bridge.ingest_normalized_event(_md(mark=100.0, event_ts=t0, receive_ts=t0 + 0.01))
    assert r_dup["advance"] is False

    r2 = bridge.ingest_normalized_event(_md(mark=101.0, event_ts=t0 + 10.0, receive_ts=t0 + 10.05))
    assert r2["accepted"] is True
    loaded = load_durable_read_model_v1(tmp_path)
    assert loaded is not None
    assert loaded["interval"] == INTERVAL_PT1H
    assert int(loaded["bar_count"] or 0) >= 1
    assert loaded["trading_authority"] is False

    # Crossing bar close must finalize once; second finalize blocked.
    close_ts = float(bridge.producer.list_envelopes()[0]["bar_close_time"])
    r_fin = bridge.ingest_normalized_event(
        _md(mark=102.0, event_ts=close_ts, receive_ts=close_ts + 0.01)
    )
    assert r_fin["accepted"] is True
    finalized = [
        e
        for e in bridge.producer.list_envelopes()
        if str(e.get("finalization_state")) == "FINALIZED_BAR"
    ]
    assert len(finalized) >= 1
    # Attempting finalize again must not raise / duplicate.
    again = bridge.producer.list_envelopes()[0]
    from src.ops.canonical_public_md_and_ohlcv_transport_reconciliation_v1.bar_state_contract_v1 import (
        BarStateContractErrorV1,
    )

    with pytest.raises(BarStateContractErrorV1):
        bridge.producer.finalize_bar(
            canonical_instrument_id=str(again["canonical_instrument_id"]),
            bar_open_time=float(again["bar_open_time"]),
        )


def test_dashboard_http_start_routes_restart_and_stale(launcher_env) -> None:
    launcher, cfg, state_root = launcher_env
    bridge = PsoToO4O5LiveBridgeV1(
        session_id="http-sess-source",
        repository_sha="deadbeef" * 5,
        config_digest="cfg",
        state_root=state_root,
    )
    t0 = 1_700_100_000.0
    bridge.ingest_normalized_event(_md(mark=200.0, event_ts=t0, receive_ts=t0 + 0.02))

    started = launcher.start(
        mode=MODE_DASHBOARD_ONLY,
        session_id="http-sess",
        config_path=cfg,
        repository_sha="deadbeef" * 5,
    )
    assert started["ok"] is True
    status = launcher.status("http-sess")
    assert status["process_alive"] is True
    assert status["http_host"] == "127.0.0.1"
    assert int(status["http_port"] or 0) > 0
    base = status["http_base_url"]
    assert base.startswith("http://127.0.0.1:")

    code_m, market = _http_get(f"{base}/market")
    assert code_m == 200
    assert market["trading_authority"] is False
    assert market["write_methods"] == []
    assert "timestamp_chain" in market["read_model"]
    assert market["read_model"]["timestamp_chain"]["http_response_observed_time"] is not None

    code_o, ohlcv = _http_get(f"{base}/api/market/landscape/ohlcv")
    assert code_o == 200
    assert ohlcv["parallel_ohlcv_producer"] is False
    assert ohlcv["independent_authoritative_recompute"] is False
    assert ohlcv["trading_authority"] is False

    code_h, health = _http_get(f"{base}/health")
    assert code_h in {200, 503}
    assert health["trading_authority"] is False

    # Dashboard restart without mutating PSO/runtime (bridge remains in-process here).
    scaffold_pid = int(started["session"]["process_identity"]["pid"])
    restarted = launcher.restart("http-sess")
    assert restarted["ok"] is True
    status2 = launcher.status("http-sess")
    assert status2["process_alive"] is True
    assert int(status2["process_identity"]["pid"]) != scaffold_pid
    base2 = status2["http_base_url"]
    assert base2 and base2 != base
    # Wait briefly for uvicorn accept after restart.
    deadline = time.time() + 5.0
    last_err = None
    market2 = None
    code_m2 = None
    while time.time() < deadline:
        try:
            code_m2, market2 = _http_get(f"{base2}/market")
            break
        except Exception as exc:  # noqa: BLE001
            last_err = exc
            time.sleep(0.1)
    assert market2 is not None, last_err
    assert code_m2 == 200
    assert market2["read_model"]["bar_count"] == market["read_model"]["bar_count"]

    # Stale / disconnected visibility — never green.
    bridge.mark_stale_and_commit(projection_time_unix=time.time())
    code_s, body_s = _http_get(f"{base2}/health")
    assert code_s == 503
    assert body_s["connection_state"] in NON_HEALTHY_RENDER_STATES
    assert body_s["connection_state"] == CONNECTION_STALE
    assert body_s["status"] == "unhealthy"

    bridge.mark_disconnected_and_commit(projection_time_unix=time.time())
    code_d, body_d = _http_get(f"{base2}/api/market/landscape/ohlcv")
    assert body_d["connection_state"] == CONNECTION_DISCONNECTED
    assert body_d["may_render_healthy"] is False

    stop = launcher.stop("http-sess", graceful_timeout_seconds=3.0)
    assert stop["ok"] is True
    assert stop["stopped"] is True


def test_no_order_credential_live_paths_in_http_surface(launcher_env) -> None:
    launcher, cfg, state_root = launcher_env
    bridge = PsoToO4O5LiveBridgeV1(
        session_id="safety-sess",
        repository_sha="deadbeef" * 5,
        config_digest="cfg",
        state_root=state_root,
    )
    bridge.ingest_normalized_event(_md(mark=1.0, event_ts=1_700_200_000.0))
    launcher.start(
        mode=MODE_DASHBOARD_ONLY,
        session_id="safety-http",
        config_path=cfg,
        repository_sha="deadbeef" * 5,
    )
    base = launcher.status("safety-http")["http_base_url"]
    _, market = _http_get(f"{base}/market")
    blob = json.dumps(market)
    for forbidden in (
        "orders_authorized",
        "live_trading",
        "testnet",
        "api_key",
        "submit_order",
        "exchange_credential",
    ):
        assert forbidden not in blob.lower()
    launcher.stop("safety-http")
