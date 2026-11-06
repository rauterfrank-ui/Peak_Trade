"""Constants for preregistered productive session runner capability v1.

Capability only: defines the fail-closed runner contract and CLI mode.
Does not start a productive session, consume authorization, or open network
during capability merge. Operator execution requires a separate GO.
"""

from __future__ import annotations

from research.canonical_volatility_max_age_productive_research_evidence_accumulation_v1.constants_v1 import (
    DEFAULT_JOIN_LEDGER_RELATIVE_PATH,
    DEFAULT_PRODUCTIVE_BRIDGE_CANONICAL_INSTRUMENT_ID,
    DEFAULT_PRODUCTIVE_BRIDGE_VENUE,
    DEFAULT_PRODUCTIVE_BRIDGE_VENUE_INSTRUMENT_ID,
    DEFAULT_PRODUCTIVE_LEDGER_RELATIVE_PATH,
    DEFAULT_QUARANTINE_LEDGER_RELATIVE_PATH,
    SESSION_PREREGISTRATION_CAPABILITY_ID,
)
from research.canonical_volatility_max_age_productive_research_evidence_accumulation_v1.session_campaign_preregistration_v1 import (
    PUBLIC_MD_HOST,
    PUBLIC_MD_VENUE,
    PUBLIC_MD_VENUE_SCOPE,
)
from research.canonical_volatility_numeric_max_age_campaign_authorization_v1.constants_v1 import (
    ABANDONED_CAMPAIGN_ID,
    ABANDONED_SESSION_IDS,
    BOUND_PUBLIC_MD_ENDPOINT_ALLOWLIST,
    BOUND_PUBLIC_MD_HOST,
    BOUND_PUBLIC_MD_METHOD_ALLOWLIST,
    BOUND_PUBLIC_MD_VENUE,
)
from research.canonical_volatility_numeric_max_age_productive_campaign_r1_recovery_active_binding_v1.constants_v1 import (
    R1_MATERIALIZED_REPOSITORY_SHA,
    R1_PREREGISTRATION_REL_PATH,
)
from research.canonical_volatility_numeric_max_age_productive_campaign_r1_recovery_active_binding_v1.identity_v1 import (
    derive_r1_campaign_identity_v1,
)
from research.canonical_volatility_numeric_max_age_productive_campaign_r1_recovery_active_binding_v1.preregistration_v1 import (
    build_r1_active_preregistration_payload_v1,
)

PACKAGE_MARKER = (
    "MASTER_V2_CANONICAL_VOLATILITY_NUMERIC_MAX_AGE_PREREGISTERED_PRODUCTIVE_SESSION_RUNNER_V1=true"
)

CAPABILITY_ID = (
    "MASTER_V2_CANONICAL_VOLATILITY_NUMERIC_MAX_AGE_PREREGISTERED_PRODUCTIVE_SESSION_RUNNER_V1"
)
REVIEW_MODE_ID = (
    "MASTER_V2_CANONICAL_VOLATILITY_NUMERIC_MAX_AGE_PREREGISTERED_"
    "PRODUCTIVE_SESSION_RUNNER_CAPABILITY_V1"
)

CLI_MODE = "productive-preregistered-session-run"
PRODUCTIVE_BRIDGE_ACCUMULATE_CLI_MODE = "productive-bridge-accumulate"

# Active identity mirrors governed R1 binding for the materialized repository SHA.
# Runtime still loads/verifies the sole ACTIVE binding file (fail closed on drift).
_R1_IDENTITY = derive_r1_campaign_identity_v1(repository_sha=R1_MATERIALIZED_REPOSITORY_SHA)
_R1_PREREG = build_r1_active_preregistration_payload_v1(
    repository_sha=R1_MATERIALIZED_REPOSITORY_SHA
)

BOUND_PREREGISTRATION_ID = SESSION_PREREGISTRATION_CAPABILITY_ID
BOUND_PREREGISTRATION_DIGEST_V1 = str(_R1_PREREG["preregistration_digest"])
BOUND_PREREGISTRATION_ARTIFACT_PATH = R1_PREREGISTRATION_REL_PATH
BOUND_CAMPAIGN_ID_V1 = str(_R1_IDENTITY["campaign_id"])
BOUND_SESSION_IDS_V1: tuple[str, ...] = (
    str(_R1_IDENTITY["session_01_id"]),
    str(_R1_IDENTITY["session_02_id"]),
)
SESSION_01_ID = BOUND_SESSION_IDS_V1[0]
SESSION_02_ID = BOUND_SESSION_IDS_V1[1]

# Tombstone aliases — never active; reactivation fail-closed via R1 gates.
TOMBSTONE_ABANDONED_CAMPAIGN_ID = ABANDONED_CAMPAIGN_ID
TOMBSTONE_ABANDONED_SESSION_IDS: tuple[str, ...] = ABANDONED_SESSION_IDS

BOUND_VENUE = PUBLIC_MD_VENUE
BOUND_VENUE_SCOPE = PUBLIC_MD_VENUE_SCOPE
BOUND_PUBLIC_MD_HOST_V1 = PUBLIC_MD_HOST
BOUND_INSTRUMENT_ID = DEFAULT_PRODUCTIVE_BRIDGE_CANONICAL_INSTRUMENT_ID
BOUND_VENUE_INSTRUMENT_ID = DEFAULT_PRODUCTIVE_BRIDGE_VENUE_INSTRUMENT_ID
BOUND_EVIDENCE_SCOPE = "canonical_volatility_max_age_productive_research_evidence_ledger_v1"

# Bridge sample venue remains the existing productive bridge consumer default.
BRIDGE_SAMPLE_VENUE = DEFAULT_PRODUCTIVE_BRIDGE_VENUE

PUBLIC_MD_ENDPOINT_ALLOWLIST: tuple[str, ...] = BOUND_PUBLIC_MD_ENDPOINT_ALLOWLIST
PUBLIC_MD_METHOD_ALLOWLIST: tuple[str, ...] = BOUND_PUBLIC_MD_METHOD_ALLOWLIST
ASSERT_PUBLIC_MD_VENUE = BOUND_PUBLIC_MD_VENUE
ASSERT_PUBLIC_MD_HOST = BOUND_PUBLIC_MD_HOST

EXPECTED_BRANCH_DEFAULT = "main"

DERIVED_SESSION_ID_MARKERS: tuple[str, ...] = ("-productive-", "*", "?")

PRODUCTIVE_LEDGER_REL_PATH = DEFAULT_PRODUCTIVE_LEDGER_RELATIVE_PATH
JOIN_LEDGER_REL_PATH = DEFAULT_JOIN_LEDGER_RELATIVE_PATH
QUARANTINE_LEDGER_REL_PATH = DEFAULT_QUARANTINE_LEDGER_RELATIVE_PATH

SPEC_REL_PATH = (
    "docs/ops/specs/"
    "MASTER_V2_CANONICAL_VOLATILITY_NUMERIC_MAX_AGE_PREREGISTERED_"
    "PRODUCTIVE_SESSION_RUNNER_V1.md"
)
CLI_REL_PATH = (
    "scripts/ops/run_canonical_volatility_max_age_productive_research_evidence_accumulation_v1.py"
)

ORDERS_TECHNICALLY_EXCLUDED = True
PRIVATE_ENDPOINTS_EXCLUDED = True
CREDENTIALS_REQUIRED = False
WEBSOCKET_ALLOWED = False
SYNTHETIC_OFFLINE_MARK_SOURCE_FORBIDDEN = True
PRODUCTIVE_SESSION_EXECUTION_IN_THIS_CAPABILITY = False

# Public-MD rate-limit / request-budget hardening (ops/transport safety; not alpha).
PUBLIC_MD_RATE_LIMIT_HARDENING_CAPABILITY_ID = (
    "MASTER_V2_CANONICAL_VOLATILITY_NUMERIC_MAX_AGE_PRODUCTIVE_SESSION_"
    "PUBLIC_MD_RATE_LIMIT_AND_REQUEST_BUDGET_HARDENING_V1"
)
PUBLIC_MD_RATE_LIMIT_HARDENING_SPEC_REL_PATH = (
    "docs/ops/specs/"
    "MASTER_V2_CANONICAL_VOLATILITY_NUMERIC_MAX_AGE_PRODUCTIVE_SESSION_"
    "PUBLIC_MD_RATE_LIMIT_AND_REQUEST_BUDGET_HARDENING_V1.md"
)
