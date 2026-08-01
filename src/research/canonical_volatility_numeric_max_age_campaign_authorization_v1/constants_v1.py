"""Constants for productive max-age campaign authorization capability v1.

Capability only: defines schema, bindings, TTL, single-use consumption, and
revocation. Does not issue a productive authorization, start a session, open
network, write evidence, select a threshold, or enable enforcement.
"""

from __future__ import annotations

from research.canonical_volatility_max_age_productive_research_evidence_accumulation_v1.constants_v1 import (
    CAPABILITY_VERSION as PRODUCTIVE_ACCUMULATION_CONTRACT_VERSION,
    DEFAULT_JOIN_LEDGER_RELATIVE_PATH,
    DEFAULT_PRODUCTIVE_LEDGER_RELATIVE_PATH,
    DEFAULT_QUARANTINE_LEDGER_RELATIVE_PATH,
    SESSION_PREREGISTRATION_ARTIFACT_REL_PATH,
)
from research.canonical_volatility_max_age_productive_research_evidence_accumulation_v1.session_campaign_preregistration_v1 import (
    CANONICAL_INSTRUMENT_ID,
    PUBLIC_MD_ALLOWED_ENDPOINTS,
    PUBLIC_MD_ALLOWED_METHOD,
    PUBLIC_MD_HOST,
    PUBLIC_MD_VENUE,
)
from trading.master_v2.canonical_volatility_numeric_max_age_parameter_research_design_and_evidence_accumulation_contract_v1 import (
    CAPABILITY_ID as PRODUCTIVE_DESIGN_ID,
)

PACKAGE_MARKER = (
    "MASTER_V2_CANONICAL_VOLATILITY_NUMERIC_MAX_AGE_PRODUCTIVE_"
    "EVIDENCE_CAMPAIGN_AUTHORIZATION_V1=true"
)

CAPABILITY_ID = (
    "MASTER_V2_CANONICAL_VOLATILITY_NUMERIC_MAX_AGE_PRODUCTIVE_EVIDENCE_CAMPAIGN_AUTHORIZATION_V1"
)
REVIEW_MODE_ID = (
    "MASTER_V2_CANONICAL_VOLATILITY_NUMERIC_MAX_AGE_PRODUCTIVE_"
    "EVIDENCE_CAMPAIGN_AUTHORIZATION_CAPABILITY_V1"
)

SCHEMA_NAME = "canonical_volatility_numeric_max_age_productive_evidence_campaign_authorization"
SCHEMA_VERSION = f"{SCHEMA_NAME}/v1"

AUTHORIZATION_SCOPE = (
    "canonical_volatility_numeric_max_age_productive_evidence_campaign_execution_v1"
)

CAMPAIGN_AUTHORIZATION_TTL_SECONDS = 86400
AUTHORIZATION_SINGLE_USE_PER_SESSION = True
AUTHORIZATION_MAXIMUM_TOTAL_CONSUMPTIONS = 2
MAXIMUM_SESSION_COUNT = 2

BOUND_CAMPAIGN_ID = "cv_maxage_productive_evidence_campaign_v1_4b3bdcecab2c0bfe"
BOUND_SESSION_IDS: tuple[str, ...] = (
    "cv_maxage_productive_evidence_campaign_v1_4b3bdcecab2c0bfe_s01_8a97f48c839c",
    "cv_maxage_productive_evidence_campaign_v1_4b3bdcecab2c0bfe_s02_c02312c99747",
)
BOUND_PREREGISTRATION_DIGEST = "1cfc1698796b1b931077cd692c7b0e97bc401f626d7e7b17bba1a777b62a252f"
BOUND_PREREGISTRATION_ARTIFACT_PATH = SESSION_PREREGISTRATION_ARTIFACT_REL_PATH

BOUND_PRODUCTIVE_DESIGN_ID = PRODUCTIVE_DESIGN_ID
BOUND_PRODUCTIVE_ACCUMULATION_CONTRACT_VERSION = PRODUCTIVE_ACCUMULATION_CONTRACT_VERSION

BOUND_PUBLIC_MD_VENUE = PUBLIC_MD_VENUE
BOUND_PUBLIC_MD_HOST = PUBLIC_MD_HOST
BOUND_PUBLIC_MD_ENDPOINT_ALLOWLIST: tuple[str, ...] = tuple(PUBLIC_MD_ALLOWED_ENDPOINTS)
BOUND_PUBLIC_MD_METHOD_ALLOWLIST: tuple[str, ...] = (PUBLIC_MD_ALLOWED_METHOD,)
BOUND_INSTRUMENT_ALLOWLIST: tuple[str, ...] = (CANONICAL_INSTRUMENT_ID,)

BOUND_DURABLE_LEDGER_PATH = DEFAULT_PRODUCTIVE_LEDGER_RELATIVE_PATH
BOUND_JOIN_PATH = DEFAULT_JOIN_LEDGER_RELATIVE_PATH
BOUND_QUARANTINE_PATH = DEFAULT_QUARANTINE_LEDGER_RELATIVE_PATH

# Planned authorization ledger paths (typed here; not materialized by this capability).
_AUTHORIZATION_DIR = (
    "docs/evidence/canonical_volatility_max_age_productive_research_evidence_ledger_v1/"
    f"campaigns/{BOUND_CAMPAIGN_ID}/authorization"
)
BOUND_REVOCATION_LEDGER_PATH = f"{_AUTHORIZATION_DIR}/revocation_ledger.jsonl"
BOUND_CONSUMPTION_LEDGER_PATH = f"{_AUTHORIZATION_DIR}/consumption_ledger.jsonl"

UNKNOWN_FIELD_POLICY = "REJECT_UNKNOWN_FIELDS"
ORDERS_TECHNICALLY_EXCLUDED = True
PRIVATE_ENDPOINTS_EXCLUDED = True
CREDENTIALS_REQUIRED = False
NETWORK_SIDE_EFFECTS_ON_CAPABILITY = False
PRODUCTIVE_ISSUANCE_IN_THIS_CAPABILITY = False

SPEC_REL_PATH = (
    "docs/ops/specs/"
    "MASTER_V2_CANONICAL_VOLATILITY_NUMERIC_MAX_AGE_PRODUCTIVE_"
    "EVIDENCE_CAMPAIGN_AUTHORIZATION_V1.md"
)
CLI_REL_PATH = (
    "scripts/ops/run_canonical_volatility_max_age_productive_research_evidence_accumulation_v1.py"
)

RENDER_CLI_MODE = "render-campaign-authorization"
VERIFY_CLI_MODE = "verify-campaign-authorization"
REVOKE_CLI_MODE = "revoke-campaign-authorization"
CONSUME_CLI_MODE = "consume-campaign-authorization"

REQUIRED_ARTIFACT_FIELDS: tuple[str, ...] = (
    "schema_version",
    "authorization_id",
    "authorization_scope",
    "issued_at",
    "earliest_start",
    "expires_at",
    "single_use",
    "repository_sha",
    "campaign_id",
    "session_ids",
    "maximum_session_count",
    "preregistration_artifact_path",
    "preregistration_digest",
    "productive_design_id",
    "productive_accumulation_contract_version",
    "public_md_venue",
    "public_md_host",
    "public_md_endpoint_allowlist",
    "public_md_method_allowlist",
    "instrument_allowlist",
    "durable_ledger_path",
    "join_path",
    "quarantine_path",
    "revocation_ledger_path",
    "consumption_ledger_path",
    "campaign_authorization_ttl_seconds",
    "authorization_single_use_per_session",
    "authorization_maximum_total_consumptions",
    "artifact_digest",
)

REVOCATION_REQUIRED_FIELDS: tuple[str, ...] = (
    "authorization_id",
    "authorization_digest",
    "revoked_at",
    "reason",
    "operator_reference",
    "revocation_record_digest",
)

CONSUMPTION_REQUIRED_FIELDS: tuple[str, ...] = (
    "authorization_id",
    "authorization_digest",
    "session_id",
    "consumed_at",
    "consumption_index",
    "repository_sha",
    "campaign_id",
    "consumption_record_digest",
)
