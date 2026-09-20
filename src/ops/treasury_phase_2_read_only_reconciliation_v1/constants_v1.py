"""Treasury Phase-2 read-only reconciliation foundation. No network. No mutation."""

from __future__ import annotations

CAPABILITY_ID = "TREASURY_PHASE_2_READ_ONLY_RECONCILIATION_FOUNDATION_V1"
PACKAGE_MARKER = "TREASURY_PHASE_2_READ_ONLY_RECONCILIATION_FOUNDATION_V1=true"
OWNER = "ops.treasury_phase_2_read_only_reconciliation_v1"
SCHEMA_VERSION = "treasury_phase_2_read_only_reconciliation.v1"
CONTRACT_VERSION = "v1"
JOIN_SEAM_ID = "TREASURY_PHASE_2_READ_ONLY_RECONCILIATION_TO_CAPITAL_ADMISSION_V1"

CAPITAL_ADMISSION_AUTHORITY = "capital_admission_contract_v1"
RUNTIME_AUTHORIZATION_EFFECT = "NONE"
NETWORK_ALLOWED = False
TREASURY_MUTATION_AUTHORIZED = False
RISK_ADMISSIBLE_MINT_AUTHORIZED = False

TREASURY_PHASE_2_STATUS = "READ_ONLY_FOUNDATION_BOUND"
TREASURY_PHASE_2_READ_ONLY_RECONCILIATION = True
TRANSFER_RECONCILIATION_READ_ONLY_FOUNDATION = True

SECOND_CAPITAL_AUTHORITY_ADDED = False

FORBIDDEN_IMPORT_MARKERS: tuple[str, ...] = (
    "requests",
    "urllib.request",
    "http.client",
    "LiveCanaryHttpClientV1",
    "construct_live_execution_port_v1",
)
