"""Governed instrument-metadata authority-owner slot + producer identity.

Owner assignment for Full-Core C2 INSTRUMENT_QUANTITY_METADATA. Observation
from GET /api/v5/public/instruments remains not authority until consumer bind
closes the chain under a separate implementation slice.
"""

from __future__ import annotations

CAPABILITY_ID = "GOVERNED_PRODUCTIVE_INSTRUMENT_METADATA_AUTHORITY_PRODUCER_V1"
PACKAGE_MARKER = "GOVERNED_PRODUCTIVE_INSTRUMENT_METADATA_AUTHORITY_PRODUCER_V1=true"
OWNER = "ops.governed_productive_instrument_metadata_authority_producer_v1"
SCHEMA_VERSION = "governed_productive_instrument_metadata_authority_producer.v1"
CONTRACT_VERSION = "v1"

INSTRUMENT_METADATA_AUTHORITY_OWNER = (
    "ops.governed_productive_instrument_metadata_authority_producer_v1"
)
INSTRUMENT_METADATA_AUTHORITY_OWNER_CLASS = (
    "GOVERNED_PRODUCTIVE_INSTRUMENT_METADATA_AUTHORITY_PRODUCER"
)
DIMENSION_ID = "COMPLETE_INSTRUMENT_QUANTITY_CONSTRAINT_METADATA"
UNIT_CLASS = "INSTRUMENT_CONSTRAINT_BUNDLE"
SCOPE_TRACK = "FULL_CORE"
VENUE_BINDING_RATIFIED = "OKX_EEA"
QUANTITY_UNIT_SEMANTICS_RATIFIED = "CONTRACTS_SZ_LOT_STEP"

OWNER_ASSIGNMENT_RATIFIED = True
SLOT_KIND = "GOVERNED_PRODUCTIVE_INSTRUMENT_METADATA_AUTHORITY_PRODUCER"
SLOT_IS_EMPTY = False
PRODUCER_IMPLEMENTATION_PRESENT = True
GOVERNED_PRODUCER_CREATED = True
OBSERVATION_IS_NOT_AUTHORITY = True
MAPPING_IS_NOT_OWNER_CLOSURE = True
RATIFICATION_IS_NOT_CHAIN_CLOSURE = True
SELECTION_AUTHORITY_REMAINS_CAP24 = True

FULL_CORE_INSTRUMENT_METADATA_OBSERVATION_TRANSPORT = (
    "src/ops/full_core_live_path_composition_root_v1/fresh_pretrade_runtime_get_v1.py"
)
FULL_CORE_INSTRUMENT_METADATA_OBSERVATION_ENDPOINT = "/api/v5/public/instruments"
FULL_CORE_INSTRUMENT_METADATA_CRS_CONSUMER_REBIND = (
    "src/ops/full_core_live_path_composition_root_v1/"
    "current_productive_mv2_capital_context_rebind_v1.py"
)
