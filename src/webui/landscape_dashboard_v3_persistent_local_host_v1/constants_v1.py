"""Landscape V3 persistent local host operator contract (acceptance: no autostart)."""

from __future__ import annotations

CAPABILITY_ID = "LANDSCAPE_DASHBOARD_V3_PERSISTENT_LOCAL_HOST_V1"

DASHBOARD_BIND_ADDRESS = "127.0.0.1"
DASHBOARD_EXPOSURE = "LOOPBACK_ONLY"
LANDSCAPE_DASHBOARD_FIXED_PORT = 8765
CANONICAL_MARKET_PATH = "/market/v3"
CANONICAL_HEALTH_PATH = "/api/health"

CANONICAL_BOOKMARK_URL = (
    f"http://{DASHBOARD_BIND_ADDRESS}:{LANDSCAPE_DASHBOARD_FIXED_PORT}{CANONICAL_MARKET_PATH}"
)

LAUNCHAGENT_LABEL = "com.peaktrade.landscape-dashboard-v3-persistent-v1"
CONTROLLER_SCRIPT_REL = "scripts/webui/landscape_v3_dashboard_persistent_local_host.sh"
ASGI_TARGET = "src.webui.app:app"

PERMANENT_AUTOSTART_ENABLED = False
PORT_CONFLICT_STATUS = "NO_KNOWN_REPO_DEFAULT_CONFLICT_ON_8765"

SUPERVISION_METHOD = "macos_launchagent_manual_start"
RESTART_ON_FAILURE = True
