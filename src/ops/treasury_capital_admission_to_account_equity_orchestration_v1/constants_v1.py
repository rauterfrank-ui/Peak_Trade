"""E4: Treasury/Capital-Admission → Account-Equity-Orchestrierung binding constants."""

from __future__ import annotations

CAPABILITY_ID = "TREASURY_CAPITAL_ADMISSION_TO_ACCOUNT_EQUITY_ORCHESTRATION_V1"
PACKAGE_MARKER = "TREASURY_CAPITAL_ADMISSION_TO_ACCOUNT_EQUITY_ORCHESTRATION_V1=true"
OWNER = "ops.treasury_capital_admission_to_account_equity_orchestration_v1"
SCHEMA_VERSION = "treasury_capital_admission_to_account_equity_orchestration.v1"
CONTRACT_VERSION = "v1"

EDGE_SEAM_ID = "TREASURY_CAPITAL_ADMISSION_TO_ACCOUNT_EQUITY_ORCHESTRATION_V1"
CAPITAL_ADMISSION_AUTHORITY = "capital_admission_contract_v1"
ACCOUNT_EQUITY_AUTHORITY = "ops.governed_productive_account_equity_authority_producer_v1"

RUNTIME_AUTHORIZATION_EFFECT = "NONE"
NETWORK_ALLOWED = False
TREASURY_MUTATION_AUTHORIZED = False
EXTERNAL_EFFECT_AUTHORIZED = False
STEP_29P_MINT_AUTHORIZED = False
AVAILABLE_FOR_SIZING_MINT_AUTHORIZED = False
SECOND_ACCOUNT_EQUITY_AUTHORITY_ADDED = False
PARALLEL_ACCOUNT_EQUITY_AUTHORITY_ADDED = False

FORBIDDEN_IMPORT_MARKERS: tuple[str, ...] = (
    "urllib.request",
    "requests",
    "produce_current_productive_29p_risk_capital_v1",
    "evaluate_step_29p_capital_risk_admissibility_v1",
    "PortfolioCapitalReservationBudgetOwnerV1",
)
