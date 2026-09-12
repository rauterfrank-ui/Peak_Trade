"""Governed account-equity authority-owner slot.

Owner assignment plus typed sample schema and typed venue-witness
observation contract. No producer implementation. No runtime source
object. No mapping. No value binding. No Live-account-bound join.
No wire.
"""

from __future__ import annotations

CAPABILITY_ID = "GOVERNED_PRODUCTIVE_ACCOUNT_EQUITY_AUTHORITY_PRODUCER_V1"
PACKAGE_MARKER = "GOVERNED_PRODUCTIVE_ACCOUNT_EQUITY_AUTHORITY_PRODUCER_V1=true"
OWNER = "ops.governed_productive_account_equity_authority_producer_v1"
SCHEMA_VERSION = "governed_productive_account_equity_authority_producer.v1"
CONTRACT_VERSION = "v1"

ACCOUNT_EQUITY_AUTHORITY_OWNER = "ops.governed_productive_account_equity_authority_producer_v1"
ACCOUNT_EQUITY_AUTHORITY_OWNER_CLASS = "GOVERNED_PRODUCTIVE_ACCOUNT_EQUITY_AUTHORITY_PRODUCER"
OWNER_ASSIGNMENT_RATIFIED = True
SLOT_KIND = "EMPTY_GOVERNED_AUTHORITY_OWNER_SLOT"
SLOT_IS_EMPTY = True
C01_C16_NOT_ELEVATED = True
STEP_29P_IS_NOT_EQUITY_AUTHORITY_OWNER = True
PRODUCER_IMPLEMENTATION_PRESENT = False
GOVERNED_PRODUCER_CREATED = False
GOVERNED_PRODUCTIVE_SOURCE_PRESENT = False
SOURCE_OBJECT_PRESENT = False
SOURCE_OBJECT_PRESENT_SEMANTICS = "RUNTIME_SAMPLE_INSTANCE_NOT_SCHEMA_DEFINITION"
SOURCE_SELECTED = False
GOVERNED_RUNNING_ACCOUNT_EQUITY_SAMPLE_SCHEMA_PRESENT = True
VENUE_WITNESS_SCHEMA_PRESENT = True
VENUE_WITNESS_RUNTIME_INSTANCE_PRESENT = False
VENUE_WITNESS_SELECTED = False
WITNESS_CONTRACT_MISSING_CLOSED = True
OBSERVATION_AUTHORITY_EFFECT = "NONE"
EQUITY_DIMENSION_BOUND = False
MAPPED_TO_RUNNING_ACCOUNT_EQUITY_AVAILABLE_FOR_SIZING = False
RAW_TO_WITNESS_PROVEN = False
RUNTIME_VALUE_PRESENT = False
SAMPLE_PRESENT = False
LIVE_ACCOUNT_BOUND_JOIN_PRESENT = False
CORE_LOGIC_CHANGE = False
RUNTIME_AUTHORIZATION_EFFECT = "NONE"
NUMERIC_EQUITY_TTL_SECONDS = 5
SAMPLE_PROVENANCE_REQUIRED_FIELDS: tuple[str, ...] = (
    "dimension_id",
    "bound_account_identity",
    "bound_venue_identity",
    "bound_td_mode",
    "settlement_currency",
    "value",
    "value_semantics",
    "producer_identity",
    "authority_contract_ref",
    "source_revision_or_digest",
    "input_set_digest",
    "decision_epoch",
    "observed_at/as_of",
    "freshness_max_age",
    "freshness_policy_status",
    "restart_reconciliation_status",
    "component_completeness",
    "component_provenance",
    "inclusion_vector",
    "component_term_vector",
    "double_count_guards",
    "currency_conversion_status",
    "witness_reconciliation_status",
    "policy_version",
    "semantic_digest",
    "sample_id",
    "observation_vs_authority_class",
)
WITNESS_PROVENANCE_REQUIRED_FIELDS: tuple[str, ...] = (
    "witness_id",
    "bound_account_identity",
    "bound_venue_identity",
    "rest_host",
    "bound_td_mode",
    "account_mode",
    "currency_domain",
    "endpoint",
    "method",
    "request_identity",
    "decision_epoch",
    "observed_at/as_of",
    "response_received_at",
    "provider_timestamp",
    "raw_field_path",
    "observation_semantic_class",
    "raw_value_representation",
    "presence_state",
    "raw_payload_state",
    "payload_digest",
    "raw_payload",
    "request_provenance",
    "response_provenance",
    "observation_vs_authority_class",
    "observation_authority_effect",
    "equity_dimension_bound_status",
    "mapping_status",
    "freshness_evidence_status",
    "clock_source_status",
    "provenance_digest",
)
