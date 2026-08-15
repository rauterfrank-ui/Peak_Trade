"""Identity and hard invariants for productive issuance + real public MD run v1."""

from __future__ import annotations

CAPABILITY_ID = (
    "INTEGRATED_PAPER_SHADOW_PRODUCTIVE_AUTHORIZATION_ISSUANCE_"
    "AND_REAL_NETWORK_EXECUTION_CAPABILITY_V1"
)
PACKAGE_MARKER = (
    "INTEGRATED_PAPER_SHADOW_PRODUCTIVE_AUTHORIZATION_ISSUANCE_"
    "AND_REAL_NETWORK_EXECUTION_CAPABILITY_V1=true"
)
PRODUCER_FAMILY = (
    "ops.integrated_paper_shadow_productive_authorization_issuance_and_real_network_execution_v1"
)
SCHEMA_VERSION = "v1"
CONTRACT_CONFIG_SCHEMA_VERSION = (
    "integrated_paper_shadow_productive_authorization_issuance_and_real_network_execution.v1"
)
ISSUANCE_MANIFEST_SCHEMA = "ops.integrated_paper_shadow_productive_issuance_manifest_v1"

AUTHORITY_EFFECT_NONE = "NONE"
ACTIVATION_EFFECT_NONE = "NONE"
RUNTIME_EFFECT_NONE = "NONE"
ORDER_EFFECT_NONE = "NONE"
ECONOMIC_GATE_EFFECT_NONE = "NONE"

VENUE_OKX = "OKX"
MARKET_TYPE_FUTURES = "FUTURES"
CANONICAL_INSTRUMENT_ID = "ETH-USD_UM_XPERP-310404"
CANONICAL_HOST = "eea.okx.com"
HOST_ALLOWLIST: tuple[str, ...] = (CANONICAL_HOST,)
NETWORK_SCOPE = "okx_eea_futures_public_md_observe_v1"
SESSION_EXECUTION_SCOPE = "paper_shadow_observation_wallclock_v1"
REQUIRED_MODE = "observation"

# I17 productive duration policy (Owner-GO 2026-08-14).
# Canonical qualification is 2h. 6h remains supported as extended soak and
# does not block the next phase after a successful canonical 2h I17 closeout.
# The 6h ceiling stays so soak sessions can still be planned. Test-only
# --allow-noncanonical-duration never grants order/live/canary authority.
I17_CANONICAL_DURATION_SECONDS = 7200
I17_EXTENDED_SOAK_DURATION_SECONDS = 21600
I17_EXTENDED_SOAK_BLOCKS_NEXT_PHASE = False
CANONICAL_PRODUCTIVE_DURATION_SECONDS = I17_CANONICAL_DURATION_SECONDS
EXTENDED_SOAK_DURATION_SECONDS = I17_EXTENDED_SOAK_DURATION_SECONDS
EXTENDED_SOAK_BLOCKS_NEXT_PHASE = I17_EXTENDED_SOAK_BLOCKS_NEXT_PHASE
DEFAULT_PLANNED_DURATION_SECONDS = I17_CANONICAL_DURATION_SECONDS
DEFAULT_MAX_SESSION_DURATION_SECONDS = I17_EXTENDED_SOAK_DURATION_SECONDS
DURATION_CLASS_CANONICAL_QUALIFICATION = "CANONICAL_QUALIFICATION"
DURATION_CLASS_EXTENDED_SOAK = "EXTENDED_SOAK_NON_BLOCKING"
DURATION_CLASS_NONCANONICAL = "NONCANONICAL_TEST_ONLY"
ALLOWED_PRODUCTIVE_DURATIONS: frozenset[int] = frozenset(
    {
        I17_CANONICAL_DURATION_SECONDS,
        I17_EXTENDED_SOAK_DURATION_SECONDS,
    }
)
PRODUCTIVE_DURATION_BLOCKER = "PRODUCTIVE_DURATION_MUST_BE_CANONICAL_7200_OR_EXTENDED_SOAK_21600"
I17_CANONICAL_QUALITATIVE_ACCEPTANCE_REQUIREMENTS: tuple[str, ...] = (
    "PLANNED_RUNTIME_EQUALS_CANONICAL_7200",
    "NATURAL_TERMINAL_CLOSEOUT",
    "TERMINAL_VERDICT_PRESENT",
    "INTEGRITY_AND_EVIDENCE_SEAL",
    "BUNDLE_VERIFIER_PASS",
    "CONTIGUOUS_MARKET_DATA_SEQUENCES",
    "CONTIGUOUS_HEARTBEATS",
    "CONTIGUOUS_DECISION_CYCLES",
    "NO_UNEXPLAINED_FATAL_TRACEBACK_KILLSTATE",
    "NO_UNALLOWED_STALENESS",
    "RECONNECT_TRANSPORT_PER_EXISTING_CONTRACT",
    "ORDER_EFFECT_NONE",
    "NO_CANARY_ORDER_SUBMIT_EFFECT",
    "NO_SAFETY_AUTHORITY_ESCALATION",
)

DEFAULT_CONFIRM_TOKEN_TTL_SECONDS = 3600
MIN_CONFIRM_TOKEN_TTL_SECONDS = 60
MAX_CONFIRM_TOKEN_TTL_SECONDS = 86400

DEFAULT_CONNECT_TIMEOUT_SECONDS = 5.0
DEFAULT_READ_TIMEOUT_SECONDS = 10.0
DEFAULT_MAX_RESPONSE_BYTES = 1_048_576
DEFAULT_PER_REQUEST_MAX_RETRIES = 2
DEFAULT_SESSION_HTTP_429_BUDGET = 20

# Env flag is NEVER sufficient alone — only an additional hard gate beside auth.
REAL_NETWORK_ENV = "PEAK_TRADE_PSO_WALLCLOCK_ALLOW_REAL_NETWORK"
CONFIRM_TOKEN_ENV = "PEAK_TRADE_PSO_WALLCLOCK_CONFIRM_TOKEN"

CONFIG_RELPATH = (
    "config/ops/integrated_paper_shadow_productive_authorization_issuance_"
    "and_real_network_execution_v1.toml"
)
CONTRACT_DOC_RELPATH = (
    "docs/ops/runbooks/INTEGRATED_PAPER_SHADOW_PRODUCTIVE_AUTHORIZATION_"
    "ISSUANCE_AND_REAL_NETWORK_EXECUTION_CAPABILITY_V1.md"
)
CLI_RELPATH = (
    "scripts/ops/run_integrated_paper_shadow_productive_authorization_"
    "issuance_and_real_network_v1.py"
)

WALLCLOCK_OWNER = "ops.integrated_paper_shadow_observation_wallclock_session_execution_v1"
GO_PREREG_OWNER = "ops.paper_shadow_observation_operator_go_session_preregistration_v1"
OBSERVATION_OWNER = "ops.integrated_paper_shadow_observation_session_v1"
PIPELINE_OWNER = "ops.integrated_paper_shadow_economic_validity_pipeline_v1"

WALLCLOCK_CONFIG_IDENTITY = (
    "config/ops/integrated_paper_shadow_observation_wallclock_session_execution_v1.toml"
)
WALLCLOCK_CODE_IDENTITY = (
    "src/ops/integrated_paper_shadow_observation_wallclock_session_execution_v1/"
)
PRODUCTIVE_CODE_IDENTITY = (
    "src/ops/integrated_paper_shadow_productive_authorization_issuance_"
    "and_real_network_execution_v1/"
)

STRATEGY_PORTFOLIO_ID = "master_v2_double_play_paper_shadow_observation_portfolio_v1"
STRATEGY_COMPONENT_IDENTITIES: tuple[str, ...] = (
    "trading.master_v2.double_play_entry_exit_policy_v0",
    WALLCLOCK_OWNER,
    PRODUCER_FAMILY,
)

FORBIDDEN_IMPORT_PREFIXES: tuple[str, ...] = (
    "src.orders",
    "src.broker",
    "src.live",
    "src.execution.live",
)

CAPABILITY_SOURCE_RELPATHS: tuple[str, ...] = (
    "src/ops/integrated_paper_shadow_productive_authorization_issuance_"
    "and_real_network_execution_v1/__init__.py",
    "src/ops/integrated_paper_shadow_productive_authorization_issuance_"
    "and_real_network_execution_v1/constants_v1.py",
    "src/ops/integrated_paper_shadow_productive_authorization_issuance_"
    "and_real_network_execution_v1/productive_confirm_token_producer_v1.py",
    "src/ops/integrated_paper_shadow_productive_authorization_issuance_"
    "and_real_network_execution_v1/productive_preregistration_producer_v1.py",
    "src/ops/integrated_paper_shadow_productive_authorization_issuance_"
    "and_real_network_execution_v1/productive_operator_go_producer_v1.py",
    "src/ops/integrated_paper_shadow_productive_authorization_issuance_"
    "and_real_network_execution_v1/productive_authorization_verifier_v1.py",
    "src/ops/integrated_paper_shadow_productive_authorization_issuance_"
    "and_real_network_execution_v1/real_http_fetcher_v1.py",
    "src/ops/integrated_paper_shadow_productive_authorization_issuance_"
    "and_real_network_execution_v1/productive_run_entrypoint_v1.py",
    "src/ops/integrated_paper_shadow_productive_authorization_issuance_"
    "and_real_network_execution_v1/issuance_evidence_v1.py",
)


def classify_productive_planned_duration_v1(duration_seconds: int) -> str:
    duration = int(duration_seconds)
    if duration == I17_CANONICAL_DURATION_SECONDS:
        return DURATION_CLASS_CANONICAL_QUALIFICATION
    if duration == I17_EXTENDED_SOAK_DURATION_SECONDS:
        return DURATION_CLASS_EXTENDED_SOAK
    return DURATION_CLASS_NONCANONICAL


def productive_duration_requires_test_only_flag_v1(duration_seconds: int) -> bool:
    return classify_productive_planned_duration_v1(duration_seconds) == (
        DURATION_CLASS_NONCANONICAL
    )


def duration_next_phase_blockers_v1(
    *,
    canonical_qualification_proven: bool,
    extended_soak_proven: bool = False,
) -> tuple[str, ...]:
    """Duration-only next-phase blockers. Soak absence never blocks while
    I17_EXTENDED_SOAK_BLOCKS_NEXT_PHASE is false. Qualitative evidence remains
    owned by the wallclock bundle verifier.
    """
    blockers: list[str] = []
    if not canonical_qualification_proven:
        blockers.append("I17_CANONICAL_7200S_QUALIFICATION_ABSENT")
    if I17_EXTENDED_SOAK_BLOCKS_NEXT_PHASE and not extended_soak_proven:
        blockers.append("I17_EXTENDED_SOAK_21600S_ABSENT")
    return tuple(blockers)
