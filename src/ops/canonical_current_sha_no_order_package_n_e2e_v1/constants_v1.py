"""Constants for the current-SHA no-order Package-N wiring orchestrator.

Non-activating. Does not authorize Live, Testnet, orders, credentials, or
COMPLETE_CURRENT_SYSTEM_E2E_PROVEN.
"""

from __future__ import annotations

from src.ops.bounded_futures_testnet_venue_binding_v0 import PRODUCTION_INSTRUMENT_ID

CONTRACT_ID = "canonical_current_sha_no_order_package_n_e2e_v1"
CAPABILITY_ID = "CANONICAL_CURRENT_SHA_NO_ORDER_PACKAGE_N_E2E_V1"
EVIDENCE_DIRNAME = "canonical_current_sha_no_order_package_n_e2e_v1"
OUT_OPS_PREFIX = "out/ops"
CONFIG_RELPATH = "config/ops/canonical_current_sha_no_order_e2e_experiment_identity_v1.json"
CAMPAIGN_ID = "canonical_current_sha_no_order_package_n_e2e_v1"
EXPECTED_ORIGIN_MAIN_SHA = "9f09d6d18484e35e788f5e4eaada2c598926b77f"
I65_RUN_TYPE = "offline_no_order_lifecycle"
DETERMINISTIC_TS_MS = 1_700_000_000_000
COMPLETE_CURRENT_SYSTEM_E2E_PROVEN = False
RUNTIME_AUTHORITY_IMPACT = "NONE"

FORBIDDEN_GENERATE_SCRIPTS = (
    "scripts/ops/generate_capability_7_1_evidence_v1.py",
    "scripts/ops/generate_capability_7_2_evidence_v1.py",
)

RUN_ID_PATTERN = r"^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$"
