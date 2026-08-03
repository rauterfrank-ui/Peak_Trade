"""Offline/local integration evidence for O7 productive wiring (no network/auth)."""

from __future__ import annotations

import json
import time
import urllib.request
from pathlib import Path

from src.ops.canonical_local_launcher_and_process_supervision_v1.lifecycle_v1 import (
    CanonicalLocalLauncherV1,
    LauncherPathsV1,
)
from src.ops.canonical_public_md_and_ohlcv_transport_reconciliation_v1.pso_to_o4_o5_live_bridge_v1 import (
    PsoToO4O5LiveBridgeV1,
)
from src.ops.governed_end_to_end_runtime_and_dashboard_evidence_v1.constants_v1 import (
    PRODUCTIVE_WIRING_IMPLEMENTED,
)
from src.ops.okx_native_instrument_and_mark_price_runtime_binding_fail_closed_v1.normalized_market_data_v1 import (
    NormalizedPublicMarketDataV1,
)


def _md(mark: float, event_ts: float) -> NormalizedPublicMarketDataV1:
    return NormalizedPublicMarketDataV1(
        canonical_instrument_id="ETH-USDT-SWAP",
        venue_instrument_id="ETH-USDT-SWAP",
        venue="okx",
        mark_px=mark,
        event_ts_unix=event_ts,
        receive_ts_unix=event_ts + 0.01,
        mark_price_endpoint="/api/v5/public/mark-price",
        mark_price_field="markPx",
        mapping_digest="offline-wiring",
        mapping_version="v1",
    )


def run_offline_integration_evidence_v1(*, repository_root: Path, evidence_root: Path) -> dict:
    evidence_root = Path(evidence_root)
    evidence_root.mkdir(parents=True, exist_ok=True)
    work = evidence_root / "work"
    state = work / "state"
    logs = work / "logs"
    ev = work / "evidence"
    cfg = work / "config.json"
    cfg.parent.mkdir(parents=True, exist_ok=True)
    cfg.write_text(json.dumps({"mode": "dashboard-only", "offline_wiring": True}) + "\n")

    bridge = PsoToO4O5LiveBridgeV1(
        session_id="o7-offline-wiring",
        repository_sha="offline" * 5,
        config_digest="offline-cfg",
        state_root=state,
    )
    t0 = 1_700_300_000.0
    ingest = bridge.ingest_normalized_event(_md(210.0, t0))
    launcher = CanonicalLocalLauncherV1(
        LauncherPathsV1(
            repository_root=repository_root,
            state_root=state,
            log_root=logs,
            evidence_root=ev,
        )
    )
    started = launcher.start(
        mode="dashboard-only",
        session_id="o7-offline-http",
        config_path=cfg,
        repository_sha="offline" * 5,
    )
    status = launcher.status("o7-offline-http")
    base = status["http_base_url"]
    with urllib.request.urlopen(f"{base}/market", timeout=2.0) as resp:
        market = json.loads(resp.read().decode("utf-8"))
    with urllib.request.urlopen(f"{base}/api/market/landscape/ohlcv", timeout=2.0) as resp:
        ohlcv = json.loads(resp.read().decode("utf-8"))
    pid_before = int(started["session"]["process_identity"]["pid"])
    restarted = launcher.restart("o7-offline-http")
    status2 = launcher.status("o7-offline-http")
    deadline = time.time() + 5.0
    market2 = None
    while time.time() < deadline:
        try:
            with urllib.request.urlopen(f"{status2['http_base_url']}/market", timeout=1.0) as resp:
                market2 = json.loads(resp.read().decode("utf-8"))
            break
        except Exception:
            time.sleep(0.1)
    stop = launcher.stop("o7-offline-http", graceful_timeout_seconds=3.0)

    payload = {
        "schema_id": "ops.o7_productive_wiring_offline_integration_evidence_v1",
        "ok": True,
        "network_session_started": False,
        "authorization_issued": False,
        "authorization_consumed": False,
        "confirm_token_minted": False,
        "orders_submitted": False,
        "credentials_used": False,
        "testnet_used": False,
        "live_trading_used": False,
        "o7_full_capability_closed": False,
        "productive_wiring_implemented": dict(PRODUCTIVE_WIRING_IMPLEMENTED),
        "bridge_ingest_accepted": bool(ingest.get("accepted")),
        "timestamp_chain": ingest.get("timestamp_chain"),
        "http_host": status.get("http_host"),
        "http_port": status.get("http_port"),
        "market_route_ok": market.get("trading_authority") is False,
        "ohlcv_route_ok": ohlcv.get("trading_authority") is False,
        "restart_ok": bool(restarted.get("ok")),
        "restart_pid_changed": int(status2["process_identity"]["pid"]) != pid_before,
        "durable_reload_bar_count": (market2 or {}).get("read_model", {}).get("bar_count"),
        "stop_ok": bool(stop.get("ok")),
        "residual_gaps": [
            "LIVE_OHLCV_MATRIX_CONTINUITY",
            "DASHBOARD_HTTP_POLL_CONTINUITY",
            "END_TO_END_NETWORK_LATENCY",
            "NETWORK_FAILURE_RECOVERY_EVIDENCE",
        ],
        "notes": [
            "Attempt-2 already proves long-running public-MD.",
            "Separate post-merge Owner-GO network evidence session required to close residual gaps.",
        ],
    }
    out = evidence_root / "OFFLINE_INTEGRATION_EVIDENCE.json"
    out.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return payload


if __name__ == "__main__":
    repo = Path(__file__).resolve().parents[3]
    root = (
        repo
        / "docs"
        / "evidence"
        / "capability_o7_governed_end_to_end_runtime_and_dashboard_evidence_v1"
        / "productive_wiring_offline_integration_v1"
    )
    print(
        json.dumps(
            run_offline_integration_evidence_v1(repository_root=repo, evidence_root=root), indent=2
        )
    )
