"""Identity and hard invariants for wallclock MD-observe capability v1."""

from __future__ import annotations

CAPABILITY_ID = "INTEGRATED_PAPER_SHADOW_OBSERVATION_WALLCLOCK_SESSION_EXECUTION_CAPABILITY_V1"
PACKAGE_MARKER = (
    "INTEGRATED_PAPER_SHADOW_OBSERVATION_WALLCLOCK_SESSION_EXECUTION_CAPABILITY_V1=true"
)
PRODUCER_FAMILY = "ops.integrated_paper_shadow_observation_wallclock_session_execution_v1"
SCHEMA_VERSION = "v1"
CONTRACT_CONFIG_SCHEMA_VERSION = (
    "integrated_paper_shadow_observation_wallclock_session_execution.v1"
)
EVIDENCE_SCHEMA_ID = "ops.integrated_paper_shadow_observation_wallclock_evidence_v1"
EVIDENCE_SCHEMA_VERSION = "v1"

AUTHORITY_EFFECT_NONE = "NONE"
ACTIVATION_EFFECT_NONE = "NONE"
RUNTIME_EFFECT_NONE = "NONE"
ORDER_EFFECT_NONE = "NONE"
ECONOMIC_GATE_EFFECT_NONE = "NONE"

REQUIRED_MODE = "observation"
VENUE_OKX = "OKX"
MARKET_TYPE_FUTURES = "FUTURES"
CANONICAL_INSTRUMENT_ID = "ETH-USD_UM_XPERP-310404"
CANONICAL_HOST = "eea.okx.com"
TRANSPORT_REST_POLL_V1 = "rest_poll_v1"

NETWORK_SCOPE = "okx_eea_futures_public_md_observe_v1"
SESSION_EXECUTION_SCOPE = "paper_shadow_observation_wallclock_v1"

DEFAULT_MAX_SESSION_DURATION_SECONDS = 21600
DEFAULT_POLL_INTERVAL_SECONDS = 2.0
DEFAULT_HEARTBEAT_INTERVAL_SECONDS = 5.0
DEFAULT_HEARTBEAT_LOSS_SECONDS = 15.0
DEFAULT_MAX_STALE_SECONDS = 5.0
DEFAULT_MAX_GAP_SECONDS = 10.0
DEFAULT_MAX_CLOCK_SKEW_SECONDS = 30.0
DEFAULT_MAX_CLOCK_DRIFT_SECONDS = 30.0
DEFAULT_CONSECUTIVE_STALE_BUDGET = 3
DEFAULT_MAX_RECONNECT_ATTEMPTS = 10
DEFAULT_MAX_RECONNECT_WINDOW_SECONDS = 120.0
DEFAULT_PER_REQUEST_MAX_RETRIES = 2
DEFAULT_SESSION_HTTP_429_BUDGET = 20
DEFAULT_MIN_QUALITY_WINDOW_SECONDS = 300
DEFAULT_SHUTDOWN_GRACE_SECONDS = 30.0

ALLOWED_PATHS = frozenset(
    {
        "/api/v5/public/time",
        "/api/v5/public/instruments",
        "/api/v5/market/ticker",
        "/api/v5/market/tickers",
        "/api/v5/public/mark-price",
    }
)
ALLOWED_METHODS = frozenset({"GET"})
ALLOWED_HEADERS = frozenset({"accept", "user-agent"})
USER_AGENT = (
    "PeakTradePaperShadowWallclockObserve/1.0 "
    "(+read-only; no-credentials; no-orders; eea-public-md)"
)

FORBIDDEN_IMPORT_PREFIXES: tuple[str, ...] = (
    "src.orders",
    "src.broker",
    "src.live",
    "src.execution.live",
)

CONFIG_RELPATH = (
    "config/ops/integrated_paper_shadow_observation_wallclock_session_execution_v1.toml"
)
CONTRACT_DOC_RELPATH = (
    "docs/ops/runbooks/INTEGRATED_PAPER_SHADOW_OBSERVATION_WALLCLOCK_"
    "SESSION_EXECUTION_CAPABILITY_V1.md"
)
CLI_RELPATH = "scripts/ops/run_integrated_paper_shadow_observation_wallclock_session_v1.py"

EXECUTION_CLASS_ANALYTICAL = "ANALYTICAL_SIMULATION_NOT_PAPER_EXECUTION"

CONFIRM_TOKEN_ENV = "PEAK_TRADE_PSO_WALLCLOCK_CONFIRM_TOKEN"
