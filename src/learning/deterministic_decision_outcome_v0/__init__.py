"""Offline Decision-Outcome Learning contract foundation v0.

AUTHORITY_CLASS=OFFLINE_CONFIG_CONTRACT
RUNTIME_EFFECT=NONE
PROMOTION_AUTHORITY_EFFECT=NONE
LEARNING_PRODUCTIVE_AUTHORITY=NONE
"""

from src.learning.deterministic_decision_outcome_v0.authority_v0 import (
    AUTHORITY_CLASS,
    AUTHORITY_OWNER,
    LEARNING_PRODUCTIVE_AUTHORITY,
    PROMOTION_AUTHORITY_EFFECT,
    RUNTIME_EFFECT,
    WORKPACKAGE_ID,
)
from src.learning.deterministic_decision_outcome_v0.contract_registry_v0 import (
    CONTRACT_REGISTRY_V0,
    get_schema_contract_v0,
    hash_scope_fields_v0,
)
from src.learning.deterministic_decision_outcome_v0.decision_event_v0 import (
    build_decision_event_v0,
    validate_decision_event_v0,
)
from src.learning.deterministic_decision_outcome_v0.errors_v0 import (
    DdoDuplicateConflictError,
    DdoError,
    DdoIntegrityError,
    DdoLedgerCorruptionError,
    DdoLineageError,
    DdoMalformedRecordError,
    DdoUnsupportedSchemaVersionError,
    DdoValidationError,
)
from src.learning.deterministic_decision_outcome_v0.incident_record_v0 import (
    build_incident_record_v0,
    validate_incident_record_v0,
)
from src.learning.deterministic_decision_outcome_v0.ledger_v0 import (
    AppendOnlyDdoLedgerV0,
    AppendResultV0,
    validate_canonical_record_v0,
)
from src.learning.deterministic_decision_outcome_v0.outcome_v0 import (
    build_outcome_record_v0,
    validate_outcome_record_v0,
    validate_outcome_ref_v0,
)
from src.learning.deterministic_decision_outcome_v0.serialization_v0 import (
    canonical_json_dumps_v0,
    compute_content_hash_v0,
)

__all__ = [
    "AUTHORITY_CLASS",
    "AUTHORITY_OWNER",
    "AppendOnlyDdoLedgerV0",
    "AppendResultV0",
    "CONTRACT_REGISTRY_V0",
    "DdoDuplicateConflictError",
    "DdoError",
    "DdoIntegrityError",
    "DdoLedgerCorruptionError",
    "DdoLineageError",
    "DdoMalformedRecordError",
    "DdoUnsupportedSchemaVersionError",
    "DdoValidationError",
    "LEARNING_PRODUCTIVE_AUTHORITY",
    "PROMOTION_AUTHORITY_EFFECT",
    "RUNTIME_EFFECT",
    "WORKPACKAGE_ID",
    "build_decision_event_v0",
    "build_incident_record_v0",
    "build_outcome_record_v0",
    "canonical_json_dumps_v0",
    "compute_content_hash_v0",
    "get_schema_contract_v0",
    "hash_scope_fields_v0",
    "validate_canonical_record_v0",
    "validate_decision_event_v0",
    "validate_incident_record_v0",
    "validate_outcome_record_v0",
    "validate_outcome_ref_v0",
]
