"""Unbound Owner Productive Wire-Send authority schema.

Schema only. Does not mint. Does not verify an issued artifact as accepted.
Does not arm a session. Does not set network_session_authorized. Does not
POST. Does not call inner.send. Does not consume durable state.

OWNER_NETWORK_SESSION_AUTHORITY_V1 is a required predecessor name, not a
substitute for this contract. ConstructiveProductiveFlattenSubmitAdapterV1
remains NO_SEND.
"""

from __future__ import annotations

from typing import Any

from src.ops.section_11_14_current_sui_xperp_pos_1_flatten_authority_and_pre_execution_repair_v1.constants_v1 import (
    AUTHORITY_TYPE_OWNER_FLATTEN_ISSUANCE,
    AUTHORITY_TYPE_OWNER_NETWORK_SESSION,
    BOUND_FROZEN_ENVELOPE_ID,
    BOUND_ORIGIN_MAIN_SHA,
    FLATTEN_SECTION,
    INSTRUMENT_ID,
    NETWORK_SESSION_CANNOT_AUTHORIZE_WIRE_SEND_IN_THIS_REPAIR,
    PRODUCTIVE_TRANSPORT_BIND_KIND_NO_SEND,
    SESSION_ARMING_STANDING,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.constants_v1 import (
    CANARY_AUTHORIZED,
    LIVE_ARMED,
    LIVE_ENABLED,
    POST_ALLOWED,
)

PRODUCTIVE_WIRE_SEND_SCHEMA_VERSION = "owner_productive_wire_send_authority.v1"
AUTHORITY_TYPE_OWNER_PRODUCTIVE_WIRE_SEND = "OWNER_PRODUCTIVE_WIRE_SEND_AUTHORITY_V1"
AUTHORITY_SOURCE_CANONICAL_OWNER_PRODUCTIVE_WIRE_SEND = (
    "CANONICAL_OWNER_PRODUCTIVE_WIRE_SEND_ISSUANCE"
)
PRODUCTIVE_WIRE_SEND_ACTION = "AUTHORIZE_PRODUCTIVE_WIRE_SEND"
PRODUCTIVE_WIRE_SEND_PURPOSE_EXPECTED = "SECTION_11_14_PRODUCTIVE_WIRE_SEND"
PRODUCTIVE_WIRE_SEND_CONFIRM_TOKEN_EXPECTED = "I_AUTHORIZE_SECTION_11_14_PRODUCTIVE_WIRE_SEND"
PRODUCER_IMPLEMENTED = False
ORCHESTRATOR_IMPLEMENTED = True
SEND_CAPABLE_BIND_IMPLEMENTED = True
SEND_ADAPTER_IMPLEMENTED = True
EVALUATOR_IMPLEMENTED = True
PROPOSED_ORCHESTRATOR_SYMBOL = "ProductiveWireSendOrchestratorV1"
PROPOSED_SEND_CAPABLE_BIND_SYMBOL = "ProductiveTransportBindSendCapableV1"
PROPOSED_SEND_CAPABLE_ADAPTER_SYMBOL = "ProductiveFlattenSubmitSendAdapterV1"
PRODUCTIVE_WIRE_SEND_AUTHORITY_ID_FIELDS: tuple[str, ...] = (
    "schema_version",
    "authority_type",
    "section",
    "purpose",
    "action",
    "origin_main_sha",
    "exact_envelope_id",
    "instrument_id",
    "single_use",
)
PRODUCTIVE_WIRE_SEND_INPUT_REQUIRED_FIELDS: tuple[str, ...] = (
    "schema_version",
    "authority_type",
    "authority_source",
    "issued_at",
    "section",
    "purpose",
    "action",
    "origin_main_sha",
    "exact_envelope_id",
    "instrument_id",
    "confirm_token",
    "single_use",
    "consumed",
    "retry_allowed",
    "second_submit_allowed",
    "network_session_grant_cannot_authorize_this",
    "flatten_grant_cannot_authorize_this",
    "live_flags_cannot_authorize_this",
    "session_arming_cannot_authorize_this",
)
FORBIDDEN_IMPLICIT_TRANSITIONS: tuple[str, ...] = (
    "network_session_authorized=true",
    "SESSION_ARMING",
    "LIVE_ENABLED=true",
    "LIVE_ARMED=true",
    "POST_ALLOWED=true",
    "CANARY_AUTHORIZED=true",
    "GET",
    "POST",
    "inner.send",
    "durable_consume",
    "position_mutation",
)
REQUIRED_PREDECESSOR_AUTHORITY_TYPES: tuple[str, ...] = (
    AUTHORITY_TYPE_OWNER_FLATTEN_ISSUANCE,
    AUTHORITY_TYPE_OWNER_NETWORK_SESSION,
)
CONSUME_POINT = "AFTER_POSITIVELY_ADJUDICATED_SUCCESSFUL_SEND_SEMANTICS"
EXPIRY_SEMANTICS = "NONE_DEFINED_IN_SIBLING_11_14_AUTHORITIES"
PRODUCER_SYMBOL_ABSENT = "issue_owner_productive_wire_send_authority_v1"


def productive_wire_send_owner_contract_schema_v1() -> dict[str, Any]:
    """Unbound schema. Mechanism expected-values are not issued authority."""
    return {
        "kind": AUTHORITY_TYPE_OWNER_PRODUCTIVE_WIRE_SEND,
        "ISSUED": False,
        "PRESENT": False,
        "ACCEPTED": False,
        "CONSUMED": False,
        "PRODUCER_IMPLEMENTED": PRODUCER_IMPLEMENTED,
        "ORCHESTRATOR_IMPLEMENTED": ORCHESTRATOR_IMPLEMENTED,
        "SEND_CAPABLE_BIND_IMPLEMENTED": SEND_CAPABLE_BIND_IMPLEMENTED,
        "SEND_ADAPTER_IMPLEMENTED": SEND_ADAPTER_IMPLEMENTED,
        "EVALUATOR_IMPLEMENTED": EVALUATOR_IMPLEMENTED,
        "schema_version": PRODUCTIVE_WIRE_SEND_SCHEMA_VERSION,
        "authority_source_expected": AUTHORITY_SOURCE_CANONICAL_OWNER_PRODUCTIVE_WIRE_SEND,
        "action": PRODUCTIVE_WIRE_SEND_ACTION,
        "purpose_expected": PRODUCTIVE_WIRE_SEND_PURPOSE_EXPECTED,
        "confirm_token_expected": PRODUCTIVE_WIRE_SEND_CONFIRM_TOKEN_EXPECTED,
        "section": FLATTEN_SECTION,
        "bound_origin_main_sha_expected": BOUND_ORIGIN_MAIN_SHA,
        "bound_instrument_id_expected": INSTRUMENT_ID,
        "bound_exact_envelope_id_expected": BOUND_FROZEN_ENVELOPE_ID,
        "single_use_required": True,
        "retry_allowed": False,
        "second_submit_allowed": False,
        "authority_id_fields": list(PRODUCTIVE_WIRE_SEND_AUTHORITY_ID_FIELDS),
        "required_fields": list(PRODUCTIVE_WIRE_SEND_INPUT_REQUIRED_FIELDS),
        "required_predecessor_authority_types": list(REQUIRED_PREDECESSOR_AUTHORITY_TYPES),
        "consume_point": CONSUME_POINT,
        "expiry_semantics": EXPIRY_SEMANTICS,
        "forbidden_implicit_transitions": list(FORBIDDEN_IMPLICIT_TRANSITIONS),
        "proposed_orchestrator_symbol": PROPOSED_ORCHESTRATOR_SYMBOL,
        "proposed_send_capable_bind_symbol": PROPOSED_SEND_CAPABLE_BIND_SYMBOL,
        "proposed_send_capable_adapter_symbol": PROPOSED_SEND_CAPABLE_ADAPTER_SYMBOL,
        "existing_no_send_bind_kind": PRODUCTIVE_TRANSPORT_BIND_KIND_NO_SEND,
        "network_session_cannot_authorize_wire_send": (
            NETWORK_SESSION_CANNOT_AUTHORIZE_WIRE_SEND_IN_THIS_REPAIR is True
        ),
        "session_arming_standing": bool(SESSION_ARMING_STANDING),
        "standing_live_enabled": bool(LIVE_ENABLED),
        "standing_live_armed": bool(LIVE_ARMED),
        "standing_canary_authorized": bool(CANARY_AUTHORIZED),
        "standing_post_allowed": bool(POST_ALLOWED),
        "MECHANISM_EXPECTED_VALUES_ARE_NOT_ISSUED_AUTHORITY": True,
        "EVALUATOR_IS_NOT_ISSUER": True,
        "CHAT_IS_NOT_AUTHORITY": True,
        "ENV_IS_NOT_AUTHORITY": True,
        "CLI_FLAG_IS_NOT_AUTHORITY": True,
        "ISSUING_MUST_NOT_ARM_OR_SEND": True,
        "NO_SEND_ADAPTER_SEMANTICS_UNCHANGED": True,
    }
