"""Discoverable contract registry for DDO v0 schemas and enumerations.

Runtime code outside this package must not redefine these record semantics.
This registry is not a trading/promotion/runtime authority.
"""

from __future__ import annotations

from types import MappingProxyType
from typing import Any, Final, Mapping

from src.learning.deterministic_decision_outcome_v0.authority_v0 import (
    AUTHORITY_CLASS,
    LEARNING_PRODUCTIVE_AUTHORITY,
    PROMOTION_AUTHORITY_EFFECT,
    RUNTIME_EFFECT,
)
from src.learning.deterministic_decision_outcome_v0.common_v0 import (
    SCHEMA_NAME_DECISION_EVENT,
    SCHEMA_NAME_INCIDENT_RECORD,
    SCHEMA_NAME_LEDGER_ENVELOPE,
    SCHEMA_NAME_OUTCOME_RECORD,
    SCHEMA_NAME_OUTCOME_REF,
    SCHEMA_VERSION_DECISION_EVENT_V0,
    SCHEMA_VERSION_INCIDENT_RECORD_V0,
    SCHEMA_VERSION_LEDGER_ENVELOPE_V0,
    SCHEMA_VERSION_OUTCOME_RECORD_V0,
    SCHEMA_VERSION_OUTCOME_REF_V0,
    FieldSpecV0,
)
from src.learning.deterministic_decision_outcome_v0.decision_event_v0 import (
    DECISION_EVENT_FIELD_SPECS_V0,
)
from src.learning.deterministic_decision_outcome_v0.enums_v0 import (
    COUNTERFACTUAL_ADMISSIBILITY_V0,
    DECISION_RESULT_V0,
    DECISION_TYPE_V0,
    ENUM_COMPATIBILITY_POLICY_V0,
    INCIDENT_CLASS_V0,
    KILL_SWITCH_CORRECTNESS_V0,
    KILL_SWITCH_TIMING_LABEL_V0,
    OPEN_UNBOUND_ENUMS_V0,
    OUTCOME_LINK_STATUS_V0,
    OUTCOME_ROOT_CAUSE_V0,
    SCHEMA_VERSION_COMPATIBILITY_POLICY_V0,
    STALE_ROOT_CAUSE_V0,
)
from src.learning.deterministic_decision_outcome_v0.errors_v0 import (
    DdoUnsupportedSchemaVersionError,
    DdoValidationError,
)
from src.learning.deterministic_decision_outcome_v0.incident_record_v0 import (
    INCIDENT_RECORD_FIELD_SPECS_V0,
)
from src.learning.deterministic_decision_outcome_v0.outcome_v0 import (
    OUTCOME_RECORD_FIELD_SPECS_V0,
    OUTCOME_REF_FIELD_SPECS_V0,
)
from src.learning.deterministic_decision_outcome_v0.reason_codes_v0 import (
    BLUEPRINT_HARD_BLOCK_CODES_V0,
    BLUEPRINT_HARD_BLOCK_TAXONOMY_ID,
    BLUEPRINT_REASON_CODES_V0,
    BLUEPRINT_REASON_TAXONOMY_ID,
    EXISTING_OPAQUE_TAXONOMY_ID,
    EXISTING_SOURCE_TAXONOMY_REFS_V0,
)
from src.learning.deterministic_decision_outcome_v0.serialization_v0 import (
    ADAPTER_DEVIATION_ALLOW_NAN_FALSE,
    CANONICAL_JSON_ALGORITHM_EQUIVALENT_TO,
    CANONICAL_JSON_ALGORITHM_ID,
    CONTENT_HASH_ALGORITHM_ID,
    LEARNING_LOOP_ENSURE_ASCII_FALSE_DIALECT_IMPORTED,
)

LEDGER_ENVELOPE_FIELD_SPECS_V0: Final[tuple[FieldSpecV0, ...]] = (
    FieldSpecV0("envelope_schema_name", "REQUIRED", "string", True, "Envelope schema name."),
    FieldSpecV0("envelope_schema_version", "REQUIRED", "string", True, "Envelope schema version."),
    FieldSpecV0("sequence", "REQUIRED", "int", False, "Ledger sequence. Not in content identity."),
    FieldSpecV0(
        "prev_ledger_hash",
        "REQUIRED",
        "sha256|GENESIS",
        False,
        "Chain pointer. Not content identity.",
    ),
    FieldSpecV0(
        "ledger_entry_hash",
        "REQUIRED",
        "sha256",
        False,
        "Envelope chain hash. Not content identity.",
    ),
    FieldSpecV0(
        "ingested_at_utc",
        "OPTIONAL",
        "utc_timestamp|null",
        False,
        "Persistence timestamp. Not content identity. Null if not supplied.",
    ),
    FieldSpecV0("record_type", "REQUIRED", "enum:RECORD_TYPE_V0", True, "Record type."),
    FieldSpecV0("schema_name", "REQUIRED", "string", True, "Inner schema name."),
    FieldSpecV0("schema_version", "REQUIRED", "string", True, "Inner schema version."),
    FieldSpecV0("record_id", "REQUIRED", "record_id", True, "Inner record identity."),
    FieldSpecV0("content_hash", "REQUIRED", "sha256", True, "Inner content hash."),
    FieldSpecV0("payload", "REQUIRED", "object", True, "Canonical inner record."),
)


def _specs_as_dicts(specs: tuple[FieldSpecV0, ...]) -> tuple[dict[str, Any], ...]:
    return tuple(
        {
            "name": spec.name,
            "nullability": spec.nullability,
            "value_kind": spec.value_kind,
            "in_content_hash": spec.in_content_hash,
            "notes": spec.notes,
        }
        for spec in specs
    )


CONTRACT_REGISTRY_V0: Final[Mapping[str, Any]] = MappingProxyType(
    {
        "registry_id": "peak_trade.learning.ddo.contract_registry_v0",
        "registry_version": "contract_registry_v0",
        "authority_class": AUTHORITY_CLASS,
        "runtime_effect": RUNTIME_EFFECT,
        "promotion_authority_effect": PROMOTION_AUTHORITY_EFFECT,
        "learning_productive_authority": LEARNING_PRODUCTIVE_AUTHORITY,
        "enum_compatibility_policy": ENUM_COMPATIBILITY_POLICY_V0,
        "schema_version_compatibility_policy": SCHEMA_VERSION_COMPATIBILITY_POLICY_V0,
        "canonical_json_algorithm_id": CANONICAL_JSON_ALGORITHM_ID,
        "canonical_json_algorithm_equivalent_to": CANONICAL_JSON_ALGORITHM_EQUIVALENT_TO,
        "content_hash_algorithm_id": CONTENT_HASH_ALGORITHM_ID,
        "adapter_deviation_allow_nan_false": ADAPTER_DEVIATION_ALLOW_NAN_FALSE,
        "learning_loop_ensure_ascii_false_dialect_imported": (
            LEARNING_LOOP_ENSURE_ASCII_FALSE_DIALECT_IMPORTED
        ),
        "open_unbound_enums": OPEN_UNBOUND_ENUMS_V0,
        "schemas": MappingProxyType(
            {
                SCHEMA_NAME_DECISION_EVENT: MappingProxyType(
                    {
                        "schema_name": SCHEMA_NAME_DECISION_EVENT,
                        "supported_versions": (SCHEMA_VERSION_DECISION_EVENT_V0,),
                        "current_version": SCHEMA_VERSION_DECISION_EVENT_V0,
                        "fields": _specs_as_dicts(DECISION_EVENT_FIELD_SPECS_V0),
                    }
                ),
                SCHEMA_NAME_INCIDENT_RECORD: MappingProxyType(
                    {
                        "schema_name": SCHEMA_NAME_INCIDENT_RECORD,
                        "supported_versions": (SCHEMA_VERSION_INCIDENT_RECORD_V0,),
                        "current_version": SCHEMA_VERSION_INCIDENT_RECORD_V0,
                        "fields": _specs_as_dicts(INCIDENT_RECORD_FIELD_SPECS_V0),
                    }
                ),
                SCHEMA_NAME_OUTCOME_REF: MappingProxyType(
                    {
                        "schema_name": SCHEMA_NAME_OUTCOME_REF,
                        "supported_versions": (SCHEMA_VERSION_OUTCOME_REF_V0,),
                        "current_version": SCHEMA_VERSION_OUTCOME_REF_V0,
                        "fields": _specs_as_dicts(OUTCOME_REF_FIELD_SPECS_V0),
                    }
                ),
                SCHEMA_NAME_OUTCOME_RECORD: MappingProxyType(
                    {
                        "schema_name": SCHEMA_NAME_OUTCOME_RECORD,
                        "supported_versions": (SCHEMA_VERSION_OUTCOME_RECORD_V0,),
                        "current_version": SCHEMA_VERSION_OUTCOME_RECORD_V0,
                        "fields": _specs_as_dicts(OUTCOME_RECORD_FIELD_SPECS_V0),
                    }
                ),
                SCHEMA_NAME_LEDGER_ENVELOPE: MappingProxyType(
                    {
                        "schema_name": SCHEMA_NAME_LEDGER_ENVELOPE,
                        "supported_versions": (SCHEMA_VERSION_LEDGER_ENVELOPE_V0,),
                        "current_version": SCHEMA_VERSION_LEDGER_ENVELOPE_V0,
                        "fields": _specs_as_dicts(LEDGER_ENVELOPE_FIELD_SPECS_V0),
                    }
                ),
            }
        ),
        "enums": MappingProxyType(
            {
                "DECISION_TYPE_V0": DECISION_TYPE_V0,
                "DECISION_RESULT_V0": DECISION_RESULT_V0,
                "INCIDENT_CLASS_V0": INCIDENT_CLASS_V0,
                "KILL_SWITCH_CORRECTNESS_V0": KILL_SWITCH_CORRECTNESS_V0,
                "KILL_SWITCH_TIMING_LABEL_V0": KILL_SWITCH_TIMING_LABEL_V0,
                "STALE_ROOT_CAUSE_V0": STALE_ROOT_CAUSE_V0,
                "OUTCOME_ROOT_CAUSE_V0": OUTCOME_ROOT_CAUSE_V0,
                "COUNTERFACTUAL_ADMISSIBILITY_V0": COUNTERFACTUAL_ADMISSIBILITY_V0,
                "OUTCOME_LINK_STATUS_V0": OUTCOME_LINK_STATUS_V0,
            }
        ),
        "reason_taxonomies": MappingProxyType(
            {
                BLUEPRINT_REASON_TAXONOMY_ID: BLUEPRINT_REASON_CODES_V0,
                BLUEPRINT_HARD_BLOCK_TAXONOMY_ID: BLUEPRINT_HARD_BLOCK_CODES_V0,
                EXISTING_OPAQUE_TAXONOMY_ID: "OPAQUE_EXACT_STRING_WITH_BOUND_SOURCE_PATH",
            }
        ),
        "existing_source_taxonomy_refs": EXISTING_SOURCE_TAXONOMY_REFS_V0,
        "reserved_lineage_slots_v0_must_be_empty": (
            "attribution_refs",
            "counterfactual_refs",
            "candidate_refs",
        ),
    }
)


def get_schema_contract_v0(schema_name: str, schema_version: str) -> Mapping[str, Any]:
    schemas = CONTRACT_REGISTRY_V0["schemas"]
    if schema_name not in schemas:
        raise DdoValidationError(f"UNKNOWN_SCHEMA_NAME:{schema_name}")
    contract = schemas[schema_name]
    if schema_version not in contract["supported_versions"]:
        raise DdoUnsupportedSchemaVersionError(
            f"UNSUPPORTED_SCHEMA_VERSION:{schema_name}:{schema_version}"
        )
    return contract


def hash_scope_fields_v0(schema_name: str, schema_version: str) -> tuple[str, ...]:
    contract = get_schema_contract_v0(schema_name, schema_version)
    return tuple(field["name"] for field in contract["fields"] if field["in_content_hash"])
