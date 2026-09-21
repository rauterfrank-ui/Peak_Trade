"""Canonical operator bookmark contract for Landscape Dashboard V2 persistent local host."""

from __future__ import annotations

CAPABILITY_ID = "LANDSCAPE_DASHBOARD_PERSISTENT_LOCAL_HOST_V1"

DASHBOARD_BIND_ADDRESS = "127.0.0.1"
DASHBOARD_EXPOSURE = "LOOPBACK_ONLY"
LANDSCAPE_DASHBOARD_FIXED_PORT = 8765
CANONICAL_MARKET_PATH = "/market"
CANONICAL_HEALTH_PATH = "/api/health"

CANONICAL_BOOKMARK_URL = (
    f"http://{DASHBOARD_BIND_ADDRESS}:{LANDSCAPE_DASHBOARD_FIXED_PORT}{CANONICAL_MARKET_PATH}"
)

LAUNCHAGENT_LABEL = "com.peaktrade.landscape-dashboard-persistent-v1"
CONTROLLER_SCRIPT_REL = "scripts/webui/landscape_dashboard_persistent_local_host.sh"
ASGI_TARGET = "src.webui.app:app"

# Repo-wide port census (2026-09-21): 8765 is not bound by docker/workflow defaults.
# 8000 = review harness / legacy local_market_dashboard default; keep separate.
PORT_CONFLICT_STATUS = "NO_KNOWN_REPO_DEFAULT_CONFLICT_ON_8765"

SUPERVISION_METHOD = "macos_launchagent_keepalive"
RESTART_ON_FAILURE = True
