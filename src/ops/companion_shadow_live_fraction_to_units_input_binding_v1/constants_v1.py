"""Companion Shadow/Live Fraction→Units input read-binding constants v1.

Read-only consumption of existing Q0 / reference-price / instrument-metadata
governed producers. Does not mint capital, price, or metadata authority.
Does not wire shadow_session or live_session.

RUNTIME_AUTHORIZATION_EFFECT=NONE
"""

from __future__ import annotations

PACKAGE_MARKER = "COMPANION_SHADOW_LIVE_FRACTION_TO_UNITS_INPUT_BINDING_V1=true"
BINDING_ID = "COMPANION_SHADOW_LIVE_FRACTION_TO_UNITS_INPUT_BINDING_V1"
CONTRACT_ID = "COMPANION_FRACTION_TO_UNITS_CONTRACT_V1"
OWNER_GO = "OWNER_GO_C2_COMPANION_CONVERSION_DEPENDENCY_CLOSURE_V1"
SCOPE_TRACK = "COMPANION_SHADOW_LIVE_READ_BINDING"

ACCOUNT_EQUITY_AUTHORITY_OWNER = "ops.governed_productive_account_equity_authority_producer_v1"
REFERENCE_PRICE_AUTHORITY_OWNER = "ops.governed_productive_reference_price_authority_producer_v1"
INSTRUMENT_METADATA_AUTHORITY_OWNER = (
    "ops.governed_productive_instrument_metadata_authority_producer_v1"
)

EQUITY_DIMENSION_ID = "RUNNING_ACCOUNT_EQUITY_AVAILABLE_FOR_SIZING"
REFERENCE_PRICE_SEMANTICS_CLASS = "mark_price"
INPUT_UNIT = "FRACTION_DECIMAL_0_1"
OUTPUT_UNIT = "QUANTITY_BASE_UNITS"
POSITION_FRACTION_SEMANTICS = "FRACTION_OF_RUNNING_ACCOUNT_EQUITY_AVAILABLE_FOR_SIZING"

LEVERAGE_ROLE = "NONE_IN_CONVERSION"
ROUNDING_OWNER = "COMPANION_CONTRACT_PRE_NORMALIZATION_ONLY"
LOT_STEP_NORMALIZATION_OWNER = "src.governance.capital_risk_sizing_v1._floor_to_lot"
VENUE_NORMALIZATION_OWNER_FULL_CORE = (
    "src.ops.full_core_live_path_composition_root_v1.venue_translation_v1"
)
VENUE_NORMALIZATION_OWNER_COMPANION = "NONE_AT_SIGNAL_TO_ORDERS_HANDOFF"

C2_AUTHORITY_ADDED = False
RUNTIME_CONVERSION_IMPLEMENTED = False
