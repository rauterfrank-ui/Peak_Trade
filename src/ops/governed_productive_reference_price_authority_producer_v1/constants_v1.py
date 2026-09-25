"""Governed reference-price authority-owner slot.

Owner assignment plus typed price-semantics class ratification for the
Full-Core track. No governed authority mint at runtime. Observation
transport (G17 mark sample) remains not authority until a separate
implementation WP closes the producer chain.
"""

from __future__ import annotations

CAPABILITY_ID = "GOVERNED_PRODUCTIVE_REFERENCE_PRICE_AUTHORITY_PRODUCER_V1"
PACKAGE_MARKER = "GOVERNED_PRODUCTIVE_REFERENCE_PRICE_AUTHORITY_PRODUCER_V1=true"
OWNER = "ops.governed_productive_reference_price_authority_producer_v1"
SCHEMA_VERSION = "governed_productive_reference_price_authority_producer.v1"
CONTRACT_VERSION = "v1"

REFERENCE_PRICE_AUTHORITY_OWNER = "ops.governed_productive_reference_price_authority_producer_v1"
REFERENCE_PRICE_AUTHORITY_OWNER_CLASS = "GOVERNED_PRODUCTIVE_REFERENCE_PRICE_AUTHORITY_PRODUCER"
PRICE_SEMANTICS_CLASS_RATIFIED = "mark_price"
DIMENSION_ID = "INSTRUMENT_VENUE_TIME_BOUND_CONVERSION_REFERENCE_PRICE"
UNIT_CLASS = "PRICE_QUOTE_PER_INSTRUMENT_UNIT"
SCOPE_TRACK = "FULL_CORE"

OWNER_ASSIGNMENT_RATIFIED = True
SLOT_KIND = "EMPTY_GOVERNED_AUTHORITY_OWNER_SLOT"
SLOT_IS_EMPTY = True
PRODUCER_IMPLEMENTATION_PRESENT = False
GOVERNED_PRODUCER_CREATED = False
OBSERVATION_IS_NOT_AUTHORITY = True
MAPPING_IS_NOT_OWNER_CLOSURE = True
RATIFICATION_IS_NOT_IMPLEMENTATION = True
INDEX_PX_IS_NOT_MARK_PRICE_SYNONYM = True
CANDLE_CLOSE_IS_NOT_REFERENCE_PRICE_AUTHORITY = True

FULL_CORE_CRS_REFERENCE_PRICE_SOURCE_MODULE = (
    "src/ops/full_core_live_path_composition_root_v1/current_productive_enter_live_29p_join_v1.py"
)
FULL_CORE_CRS_REFERENCE_PRICE_SOURCE_FIELD = "replay.intermediate.market_context.mark_price"
