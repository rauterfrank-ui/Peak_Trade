"""Deposit/capital-increase → Treasury Phase-2 venue observation binding. GET read-only only."""

from __future__ import annotations

CAPABILITY_ID = "TREASURY_PHASE_2_READ_ONLY_VENUE_OBSERVATION_BINDING_V1"
PACKAGE_MARKER = "TREASURY_PHASE_2_READ_ONLY_VENUE_OBSERVATION_BINDING_V1=true"
OWNER = "ops.treasury_phase_2_read_only_venue_observation_binding_v1"
SCHEMA_VERSION = "treasury_phase_2_read_only_venue_observation_binding.v1"
CONTRACT_VERSION = "v1"

EDGE_SEAM_ID = "DEPOSIT_CAPITAL_INCREASE_TO_TREASURY_PHASE_2_VENUE_OBSERVATION_V1"
TREASURY_PHASE_2_OWNER = "ops.treasury_phase_2_read_only_reconciliation_v1"
FUNDING_BALANCE_READ_OWNER = "ops.offline_funding_balance_read_producer_v1"

RUNTIME_AUTHORIZATION_EFFECT = "NONE"
NETWORK_EXECUTION_AUTHORIZED = False
TREASURY_MUTATION_AUTHORIZED = False
EXTERNAL_EFFECT_AUTHORIZED = False
AVAILABLE_FOR_SIZING_MINT_AUTHORIZED = False

FUNDING_BALANCE_IS_NOT_DEPOSIT_HISTORY = True
OBSERVED_BALANCE_ALONE_CONFIRMS_DEPOSIT = False
TREASURY_CAPITAL_CCY = "USDC"
VENUE_BALANCE_FIELD = "funding_availBal_usdc"
