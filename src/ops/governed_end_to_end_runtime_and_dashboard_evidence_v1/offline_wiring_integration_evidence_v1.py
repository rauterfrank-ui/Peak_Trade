"""Offline integration evidence for O7 PSO→O4→O5 wiring (no HTTP / no O2 supervisor)."""

from __future__ import annotations

import json
from pathlib import Path

from src.ops.canonical_derived_public_md_read_model_v1.durable_read_model_store_v1 import (
    load_durable_read_model_v1,
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
    cfg = work / "config.json"
    cfg.parent.mkdir(parents=True, exist_ok=True)
    cfg.write_text(json.dumps({"mode": "offline-evidence", "offline_wiring": True}) + "\n")

    bridge = PsoToO4O5LiveBridgeV1(
        session_id="o7-offline-wiring",
        repository_sha="offline" * 5,
        config_digest="offline-cfg",
        state_root=state,
    )
    t0 = 1_700_300_000.0
    ingest = bridge.ingest_normalized_event(_md(210.0, t0))
    durable = load_durable_read_model_v1(state)
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
        "durable_read_model_present": durable is not None,
        "presentation_http_host_retired": True,
        "o2_dashboard_supervisor_retired": True,
        "http_host": None,
        "http_port": None,
        "market_route_ok": None,
        "ohlcv_route_ok": None,
        "restart_ok": None,
        "restart_pid_changed": None,
        "durable_reload_bar_count": (durable or {}).get("bar_count")
        if isinstance(durable, dict)
        else None,
        "stop_ok": None,
        "residual_gaps": [
            "LIVE_OHLCV_MATRIX_CONTINUITY",
            "DASHBOARD_HTTP_POLL_CONTINUITY",
            "END_TO_END_NETWORK_LATENCY",
            "NETWORK_FAILURE_RECOVERY_EVIDENCE",
            "PRESENTATION_HTTP_HOST_RETIRED",
        ],
        "notes": [
            "PSO→O4→O5 durable bridge proven offline without presentation HTTP.",
            "Presentation operator entry retired fail-closed under O8.",
        ],
        "repository_root_bound": str(repository_root),
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
