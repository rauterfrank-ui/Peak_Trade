"""Standing constants for Treasury PDF current-head rebind census.

No network. No mutation. PDF is never authority.
"""

from __future__ import annotations

CAPABILITY_ID = "TREASURY_PDF_CURRENT_HEAD_REBIND_AND_CENSUS_V1"
PACKAGE_MARKER = "TREASURY_PDF_CURRENT_HEAD_REBIND_AND_CENSUS_V1=true"
OWNER = "ops.treasury_pdf_current_head_rebind_and_census_v1"
SCHEMA_VERSION = "treasury_pdf_current_head_rebind_and_census.v1"
CONTRACT_VERSION = "v1"

WP_ID = "TREASURY_PDF_CURRENT_HEAD_REBIND_AND_CENSUS_V1"
OWNER_GO = WP_ID
ALLOWED_OWNER_GOS = frozenset({OWNER_GO, f"OWNER_GO_{OWNER_GO}", "OWNER_GO=true"})

EXPECTED_ORIGIN_MAIN_SHA = "402dbee646c85400c525acd14bc38f4c16e0a17f"
CANONICAL_PACK_RELPATH = "evidence/ops/treasury_pdf_current_head_rebind_and_census_v1"
CANONICAL_PACK_AS_OF_FOLDER = "2026-09-21T010000Z"
SCHEMA_CLASS = "TREASURY_PDF_CURRENT_HEAD_REBIND_AND_CENSUS_V1"
AUTHORITY_EFFECT = "NONE"
PDF_AUTHORITY = "NONE"
ATLAS_AUTHORITY = "NONE"

NETWORK_ALLOWED = False
EXTERNAL_EFFECT_AUTHORIZED = False
TREASURY_MUTATION_AUTHORIZED = False

CURRENT_CANONICAL_TREASURY_AUTHORITY = (
    "docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md#CURRENT-Treasury-Phase-Bindings"
)

EARLIEST_REAL_TREASURY_BLOCKER = (
    "E4_TREASURY_CAPITAL_ADMISSION_TO_ACCOUNT_EQUITY_ORCHESTRATION_PRODUCTIVE_HOST_JOIN_NOT_WIRED"
)
BLOCKER_CLASS = "PRODUCTIVE_HOST_JOIN_AND_ORCHESTRATION"
MISSING_FACT_OR_AUTHORITY = (
    "Governed productive host wiring for E4 treasury capital admission → account-equity "
    "orchestration join; offline joins proven after productive read-only venue observation; "
    "no sizing or STEP-29P mint authorized."
)

FULL_CORE_P1_STATUS = "CLOSED"
FULL_CORE_P1_PR_BUDGET_SLOT = "1_OF_2"
FULL_CORE_P2_P3_ON_CURRENT_HEAD = "NOT_CANONICALLY_DEFINED"

TRUE_TOKEN = "true"
FALSE_TOKEN = "false"
