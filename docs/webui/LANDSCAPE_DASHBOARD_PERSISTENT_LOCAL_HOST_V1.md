# Landscape Dashboard V2 — persistent local loopback host

`CAPABILITY_ID=LANDSCAPE_DASHBOARD_PERSISTENT_LOCAL_HOST_V1`  
`ATLAS_AUTHORITY=NONE` — operator convenience only; not trading authority.

## Canonical bookmark

```text
http://127.0.0.1:8765/market
```

Loopback-only (`127.0.0.1`). No `0.0.0.0`, no LAN/public exposure.

## Controller

```bash
./scripts/webui/landscape_dashboard_persistent_local_host.sh install
./scripts/webui/landscape_dashboard_persistent_local_host.sh enable
./scripts/webui/landscape_dashboard_persistent_local_host.sh start
./scripts/webui/landscape_dashboard_persistent_local_host.sh status
./scripts/webui/landscape_dashboard_persistent_local_host.sh restart
./scripts/webui/landscape_dashboard_persistent_local_host.sh stop
./scripts/webui/landscape_dashboard_persistent_local_host.sh disable
./scripts/webui/landscape_dashboard_persistent_local_host.sh open
```

Uses macOS user LaunchAgent (`KeepAlive`) with foreground `uvicorn src.webui.app:app`.
Survives Cursor and Terminal closure. Does not require Full-Core, OKX, or a trading session
for HTTP availability; stale/missing read models remain fail-closed in the UI.

Machine-readable contract: `src/webui/landscape_dashboard_persistent_local_host_v1/constants_v1.py`.
