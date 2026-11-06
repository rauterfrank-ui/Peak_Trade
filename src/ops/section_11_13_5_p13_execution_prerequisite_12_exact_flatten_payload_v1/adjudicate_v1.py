"""Offline EXECUTION_PREREQUISITE_12 adjudication. No GET. No POST."""

from __future__ import annotations

from typing import Any, Mapping

from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.prerequisite_08_fresh_position_observation_v1 import (
    adjudicate_prerequisite_08_window_v1,
)
from src.ops.section_11_13_5_p08_nonzero_position_adjudication_persist_close_v1.captured_payload_v1 import (
    AUTHORIZED_TARGET_ROW,
    captured_envelope_v1,
)
from src.ops.section_11_13_5_p13_execution_prerequisite_12_exact_flatten_payload_v1.constants_v1 import (
    CASE_VALUE,
    CLORDID_SOURCE_CLASS_VALUE,
    CONFLICT_COUNT,
    CONTRACT_BOUNDARY_VALUE,
    EARLIEST_UNRESOLVED_DEPENDENCY,
    EXECUTION_PREREQUISITE_11_POSITION_SIDE_POSSIDE,
    EXECUTION_PREREQUISITE_12_EXACT_FLATTEN_PAYLOAD_FROM_OBSERVED_POSITION,
    EXPECTED_ORIGIN_MAIN_SHA,
    EXACT_PAYLOAD_ALLOWED_KEYS,
    FLATTEN_ORDER_SIDE_RULE,
    LAST_CANONICALLY_CLOSED_STEP,
    NEXT_AUTHORITY_BOUNDARY,
    OFFLINE_CONTRACT_PROOF_PX_CLASS,
    OWNER_GO,
    P08_CLOSED,
    P10_CLOSED,
    P11_CLOSED,
    P11_POS_TO_SZ_CLOSED,
    P12_EXACT_FLATTEN_PAYLOAD_CLOSED_VALUE,
    P12_EXACT_FLATTEN_PAYLOAD_PROVEN_VALUE,
    P12_TEXT_REWRITTEN,
    P13_DOES_NOT_AUTHORIZE_FLATTEN,
    P13_DOES_NOT_GRANT_EXECUTION_READINESS,
    POS_TO_SZ_UNIT_IDENTITY,
    PREDECESSOR_SLICE,
    PRIOR_OWNER_GO,
    PRIVATE_AUTH_USED,
    PUBLIC_SPEC_RETRIEVAL_PERFORMED,
    PX_SOURCE_CLASS_VALUE,
    REDUCE_ONLY_JSON_BOOLEAN_REQUIRED_VALUE,
    REDUCE_ONLY_WIRE_TYPE_STATUS_VALUE,
    REQUEST_POS_SIDE,
    RUNTIME_GET_PERFORMED,
    RUNTIME_GET_REQUIRED,
    SEND_TIME_PAYLOAD_INSTANCE_MINTED_VALUE,
    SEND_TIME_PX_MINTED_VALUE,
    SZ_UNIT_VALUE,
    TARGET_INSTRUMENT_ID,
    TARGET_POSITION_NONZERO_PROVEN,
    TARGET_POSITION_QTY_NUMERIC,
    TARGET_POSITION_QTY_UNIT,
    THIS_SLICE,
    VENUE_NATIVE_ORD_TYPE_VALUE,
    VENUE_NATIVE_TD_MODE_VALUE,
    WORKPACKAGE_ID,
)
from src.ops.section_11_13_5_p13_execution_prerequisite_12_exact_flatten_payload_v1.contract_v1 import (
    EXACT_FLATTEN_PAYLOAD_ALLOWED_KEYS,
    ExactFlattenPayloadError,
)
from src.ops.section_11_13_5_p13_execution_prerequisite_12_exact_flatten_payload_v1.lineage_v1 import (
    exact_flatten_payload_lineage_v1,
    lineage_census_summary_v1,
)
from src.ops.section_11_13_5_p13_execution_prerequisite_12_exact_flatten_payload_v1.payload_builder_v1 import (
    build_exact_flatten_payload_from_observed_position_v1,
    offline_contract_proof_price_permit_v1,
)


class P13ExactFlattenPayloadAdjudicationError(RuntimeError):
    """Fail-closed EXECUTION_PREREQUISITE_12 adjudication violation."""


def _field_provenance(*, payload: Mapping[str, Any]) -> list[dict[str, str]]:
    body = payload["body"]
    return [
        {
            "FIELD_NAME": "instId",
            "REQUIRED_OR_OPTIONAL": "REQUIRED",
            "SOURCE": "observed_position.instId",
            "SOURCE_CLASS": "OBSERVED_POSITION",
            "TRANSFORMATION": "COPY_OBSERVED_BOUND_INSTRUMENT_ID",
            "UNIT": "NOT_APPLICABLE",
            "VALUE_DOMAIN": TARGET_INSTRUMENT_ID,
            "INSTRUMENT_BOUND": "true",
            "ACCOUNT_BOUND": "true",
            "FRESHNESS_DEPENDENT": "true",
            "CURRENTLY_PROVEN": "true",
            "PROVENANCE": str(body.get("instId")),
            "CONTRADICTIONS": "NONE",
        },
        {
            "FIELD_NAME": "tdMode",
            "REQUIRED_OR_OPTIONAL": "REQUIRED",
            "SOURCE": "standing_canonical_DEFAULT_TD_MODE",
            "SOURCE_CLASS": "STANDING_CONFIGURATION",
            "TRANSFORMATION": "STANDING_CANONICAL_CROSS_NOT_ROW_MGNMODE",
            "UNIT": "NOT_APPLICABLE",
            "VALUE_DOMAIN": VENUE_NATIVE_TD_MODE_VALUE,
            "INSTRUMENT_BOUND": "false",
            "ACCOUNT_BOUND": "true",
            "FRESHNESS_DEPENDENT": "false",
            "CURRENTLY_PROVEN": "true",
            "PROVENANCE": str(body.get("tdMode")),
            "CONTRADICTIONS": "NONE",
        },
        {
            "FIELD_NAME": "side",
            "REQUIRED_OR_OPTIONAL": "REQUIRED",
            "SOURCE": "P11_flatten_order_side_from_signed_pos_v1",
            "SOURCE_CLASS": "DERIVED",
            "TRANSFORMATION": "SELL_IF_SIGNED_POS_GT_0_ELSE_BUY_THEN_MAPPER_LOWER",
            "UNIT": "NOT_APPLICABLE",
            "VALUE_DOMAIN": "buy|sell",
            "INSTRUMENT_BOUND": "true",
            "ACCOUNT_BOUND": "true",
            "FRESHNESS_DEPENDENT": "true",
            "CURRENTLY_PROVEN": "true",
            "PROVENANCE": str(body.get("side")),
            "CONTRADICTIONS": "NONE",
        },
        {
            "FIELD_NAME": "sz",
            "REQUIRED_OR_OPTIONAL": "REQUIRED",
            "SOURCE": "identity_flatten_sz_from_signed_pos_v1",
            "SOURCE_CLASS": "DERIVED",
            "TRANSFORMATION": "IDENTITY_ABS_SIGNED_POS_THEN_FORMAT_F_INTEGRAL_COLLAPSE",
            "UNIT": SZ_UNIT_VALUE,
            "VALUE_DOMAIN": "POSITIVE_NUMBER_OF_CONTRACTS_STRING",
            "INSTRUMENT_BOUND": "true",
            "ACCOUNT_BOUND": "true",
            "FRESHNESS_DEPENDENT": "true",
            "CURRENTLY_PROVEN": "true",
            "PROVENANCE": str(body.get("sz")),
            "CONTRADICTIONS": "NONE",
        },
        {
            "FIELD_NAME": "posSide",
            "REQUIRED_OR_OPTIONAL": "OMITTED",
            "SOURCE": "P11_REQUEST_POS_SIDE_POLICY",
            "SOURCE_CLASS": "OMITTED_REQUEST_FIELD",
            "TRANSFORMATION": "MAPPER_DOES_NOT_EMIT",
            "UNIT": "NOT_APPLICABLE",
            "VALUE_DOMAIN": REQUEST_POS_SIDE,
            "INSTRUMENT_BOUND": "false",
            "ACCOUNT_BOUND": "false",
            "FRESHNESS_DEPENDENT": "false",
            "CURRENTLY_PROVEN": "true",
            "PROVENANCE": REQUEST_POS_SIDE,
            "CONTRADICTIONS": "NONE",
        },
        {
            "FIELD_NAME": "ordType",
            "REQUIRED_OR_OPTIONAL": "REQUIRED",
            "SOURCE": "Z2CB_FLATTEN_ORDER_TYPE",
            "SOURCE_CLASS": "STANDING_CONFIGURATION",
            "TRANSFORMATION": "STANDING_LIMIT_THEN_MAPPER_LOWER",
            "UNIT": "NOT_APPLICABLE",
            "VALUE_DOMAIN": VENUE_NATIVE_ORD_TYPE_VALUE,
            "INSTRUMENT_BOUND": "false",
            "ACCOUNT_BOUND": "false",
            "FRESHNESS_DEPENDENT": "false",
            "CURRENTLY_PROVEN": "true",
            "PROVENANCE": str(body.get("ordType")),
            "CONTRADICTIONS": "NONE",
        },
        {
            "FIELD_NAME": "reduceOnly",
            "REQUIRED_OR_OPTIONAL": "REQUIRED",
            "SOURCE": "Z2CB_FLATTEN_REDUCE_ONLY_SEMANTICS",
            "SOURCE_CLASS": "STANDING_CONFIGURATION",
            "TRANSFORMATION": "JSON_BOOLEAN_TRUE_WIRE_TYPE_UNPROVEN",
            "UNIT": "NOT_APPLICABLE",
            "VALUE_DOMAIN": "JSON_BOOLEAN_TRUE",
            "INSTRUMENT_BOUND": "false",
            "ACCOUNT_BOUND": "false",
            "FRESHNESS_DEPENDENT": "false",
            "CURRENTLY_PROVEN": "true",
            "PROVENANCE": "true",
            "CONTRADICTIONS": "NONE",
        },
        {
            "FIELD_NAME": "px",
            "REQUIRED_OR_OPTIONAL": "REQUIRED",
            "SOURCE": "FlattenPricePermitV1.limit_price",
            "SOURCE_CLASS": PX_SOURCE_CLASS_VALUE,
            "TRANSFORMATION": "COPY_BOUND_PRICE_PERMIT_LIMIT_PRICE",
            "UNIT": "QUOTE_CURRENCY_LIMIT_PRICE",
            "VALUE_DOMAIN": "POSITIVE_TICK_ALIGNED_DECIMAL_STRING",
            "INSTRUMENT_BOUND": "true",
            "ACCOUNT_BOUND": "false",
            "FRESHNESS_DEPENDENT": "true",
            "CURRENTLY_PROVEN": "true",
            "PROVENANCE": OFFLINE_CONTRACT_PROOF_PX_CLASS,
            "CONTRADICTIONS": "NONE",
        },
        {
            "FIELD_NAME": "clOrdId",
            "REQUIRED_OR_OPTIONAL": "REQUIRED",
            "SOURCE": "serialize_canary_flatten_clordid_v1",
            "SOURCE_CLASS": CLORDID_SOURCE_CLASS_VALUE,
            "TRANSFORMATION": "SHA256_OWNER_GO_ORIGIN_MAIN_FLATTEN_THEN_CLIENT_ORDER_ID",
            "UNIT": "NOT_APPLICABLE",
            "VALUE_DOMAIN": "ALPHANUMERIC_CLIENT_ORDER_ID",
            "INSTRUMENT_BOUND": "true",
            "ACCOUNT_BOUND": "false",
            "FRESHNESS_DEPENDENT": "false",
            "CURRENTLY_PROVEN": "true",
            "PROVENANCE": str(body.get("clOrdId")),
            "CONTRADICTIONS": "NONE",
        },
    ]


def adjudicate_execution_prerequisite_12_exact_flatten_payload_v1(
    *,
    origin_main_sha: str,
    positions_payload: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    bound_sha = str(origin_main_sha or "").strip()
    if bound_sha != EXPECTED_ORIGIN_MAIN_SHA:
        raise P13ExactFlattenPayloadAdjudicationError("ORIGIN_MAIN_SHA_MISMATCH")
    if AUTHORIZED_TARGET_ROW.get("pos") != "1":
        raise P13ExactFlattenPayloadAdjudicationError("CAPTURED_POS_DRIFT")
    if AUTHORIZED_TARGET_ROW.get("instId") != TARGET_INSTRUMENT_ID:
        raise P13ExactFlattenPayloadAdjudicationError("INSTRUMENT_MISMATCH")
    envelope = captured_envelope_v1() if positions_payload is None else dict(positions_payload)
    window = adjudicate_prerequisite_08_window_v1(
        positions_payload=envelope,
        instrument_id=TARGET_INSTRUMENT_ID,
    )
    if window.get("TARGET_POSITION_QTY_UNIT") != "PROVEN":
        raise P13ExactFlattenPayloadAdjudicationError("PRODUCER_UNIT_NOT_PROVEN")
    if window.get("TARGET_POSITION_QTY_NUMERIC") != "PASS":
        raise P13ExactFlattenPayloadAdjudicationError("QTY_NUMERIC_NOT_PASS")
    signed_raw = window.get("signed_pos")
    if signed_raw is None:
        raise P13ExactFlattenPayloadAdjudicationError("SIGNED_POS_PRODUCER_ABSENT")
    living_earliest = str(window.get("EARLIEST_UNRESOLVED_DEPENDENCY") or "").strip()
    if not living_earliest:
        raise P13ExactFlattenPayloadAdjudicationError("WINDOW_EARLIEST_DEPENDENCY_MISSING")
    if window.get("EXECUTION_PREREQUISITE_12_STATUS") != (
        EXECUTION_PREREQUISITE_12_EXACT_FLATTEN_PAYLOAD_FROM_OBSERVED_POSITION
    ):
        raise P13ExactFlattenPayloadAdjudicationError("WINDOW_PREREQUISITE_12_STATUS_DRIFT")
    try:
        permit = offline_contract_proof_price_permit_v1(
            flatten_side="SELL",
            signed_pos=str(signed_raw),
        )
        payload = build_exact_flatten_payload_from_observed_position_v1(
            positions_payload=envelope,
            price_permit=permit,
            owner_go=OWNER_GO,
            origin_main_sha=bound_sha,
            instrument_id=TARGET_INSTRUMENT_ID,
        )
    except ExactFlattenPayloadError as exc:
        raise P13ExactFlattenPayloadAdjudicationError(str(exc)) from exc
    if payload.body.get("side") != "sell":
        raise P13ExactFlattenPayloadAdjudicationError("P08_LONG_POS_MUST_FLATTEN_SELL")
    if payload.body.get("sz") != "1":
        raise P13ExactFlattenPayloadAdjudicationError("P08_POS_1_MUST_SZ_1")
    if payload.body.get("instId") != TARGET_INSTRUMENT_ID:
        raise P13ExactFlattenPayloadAdjudicationError("INST_ID_DRIFT")
    if payload.body.get("tdMode") != VENUE_NATIVE_TD_MODE_VALUE:
        raise P13ExactFlattenPayloadAdjudicationError("TD_MODE_DRIFT")
    if payload.body.get("ordType") != VENUE_NATIVE_ORD_TYPE_VALUE:
        raise P13ExactFlattenPayloadAdjudicationError("ORD_TYPE_DRIFT")
    if payload.body.get("reduceOnly") is not True:
        raise P13ExactFlattenPayloadAdjudicationError("REDUCE_ONLY_DRIFT")
    if "posSide" in payload.body:
        raise P13ExactFlattenPayloadAdjudicationError("REQUEST_POS_SIDE_PRESENT")
    if set(payload.body) != set(EXACT_FLATTEN_PAYLOAD_ALLOWED_KEYS):
        raise P13ExactFlattenPayloadAdjudicationError("PAYLOAD_KEYSET_DRIFT")
    repeat = build_exact_flatten_payload_from_observed_position_v1(
        positions_payload=envelope,
        price_permit=permit,
        owner_go=OWNER_GO,
        origin_main_sha=bound_sha,
        instrument_id=TARGET_INSTRUMENT_ID,
    )
    if repeat.body_sha256 != payload.body_sha256 or repeat.body != payload.body:
        raise P13ExactFlattenPayloadAdjudicationError("PAYLOAD_NOT_DETERMINISTIC")
    lineage = exact_flatten_payload_lineage_v1()
    census = lineage_census_summary_v1()
    if int(census["SEAM_COUNT"]) != len(lineage):
        raise P13ExactFlattenPayloadAdjudicationError("LINEAGE_CENSUS_DRIFT")
    provenance = _field_provenance(payload=payload.to_dict())
    return {
        "OWNER_GO": OWNER_GO,
        "PRIOR_OWNER_GO": PRIOR_OWNER_GO,
        "THIS_SLICE": THIS_SLICE,
        "PREDECESSOR_SLICE": PREDECESSOR_SLICE,
        "WORKPACKAGE_ID": WORKPACKAGE_ID,
        "BOUND_ORIGIN_MAIN_SHA": bound_sha,
        "TARGET_INSTRUMENT_ID": TARGET_INSTRUMENT_ID,
        "CASE": CASE_VALUE,
        "EXECUTION_PREREQUISITE_12_EXACT_FLATTEN_PAYLOAD_FROM_OBSERVED_POSITION": (
            EXECUTION_PREREQUISITE_12_EXACT_FLATTEN_PAYLOAD_FROM_OBSERVED_POSITION
        ),
        "P12_EXACT_FLATTEN_PAYLOAD_PROVEN": P12_EXACT_FLATTEN_PAYLOAD_PROVEN_VALUE,
        "P12_EXACT_FLATTEN_PAYLOAD_CLOSED": P12_EXACT_FLATTEN_PAYLOAD_CLOSED_VALUE,
        "EXACT_PAYLOAD_FIELDS": list(EXACT_PAYLOAD_ALLOWED_KEYS),
        "VENUE_NATIVE_BODY": payload.body,
        "CANONICAL_JSON": payload.canonical_json,
        "BODY_SHA256": payload.body_sha256,
        "CONTRACT_BOUNDARY": CONTRACT_BOUNDARY_VALUE,
        "INST_ID_PROVENANCE": payload.body["instId"],
        "TD_MODE_PROVENANCE": payload.body["tdMode"],
        "SIDE_PROVENANCE": payload.body["side"],
        "SZ_PROVENANCE": payload.body["sz"],
        "POSSIDE_PROVENANCE": REQUEST_POS_SIDE,
        "ORD_TYPE_PROVENANCE": payload.body["ordType"],
        "REDUCE_ONLY_STATUS": "JSON_BOOLEAN_TRUE_WIRE_TYPE_UNPROVEN",
        "PRICE_FIELD_STATUS": PX_SOURCE_CLASS_VALUE,
        "CLORDID_PROVENANCE": payload.clordid,
        "PX_SOURCE_CLASS": PX_SOURCE_CLASS_VALUE,
        "CLORDID_SOURCE_CLASS": CLORDID_SOURCE_CLASS_VALUE,
        "OFFLINE_PROOF_PX_CLASS": OFFLINE_CONTRACT_PROOF_PX_CLASS,
        "SEND_TIME_PX_MINTED": SEND_TIME_PX_MINTED_VALUE,
        "SEND_TIME_PAYLOAD_INSTANCE_MINTED": SEND_TIME_PAYLOAD_INSTANCE_MINTED_VALUE,
        "FLATTEN_ORDER_SIDE_RULE": FLATTEN_ORDER_SIDE_RULE,
        "FLATTEN_ORDER_SIDE": payload.flatten_side,
        "REQUEST_POS_SIDE": REQUEST_POS_SIDE,
        "signed_pos": payload.signed_pos,
        "SZ_UNIT": SZ_UNIT_VALUE,
        "REDUCE_ONLY_JSON_BOOLEAN_REQUIRED": REDUCE_ONLY_JSON_BOOLEAN_REQUIRED_VALUE,
        "REDUCE_ONLY_WIRE_TYPE_STATUS": REDUCE_ONLY_WIRE_TYPE_STATUS_VALUE,
        "FRESHNESS_STATUS": payload.freshness_status,
        "PAYLOAD_DETERMINISM_STATUS": "PASS",
        "PAYLOAD_TRACEABILITY_STATUS": "PASS",
        "FAIL_CLOSED_STATUS": "PASS",
        "CONFLICT_COUNT": CONFLICT_COUNT,
        "P08_CLOSED": P08_CLOSED,
        "P10_CLOSED": P10_CLOSED,
        "P11_POS_TO_SZ_CLOSED": P11_POS_TO_SZ_CLOSED,
        "P11_CLOSED": P11_CLOSED,
        "P12_TEXT_REWRITTEN": P12_TEXT_REWRITTEN,
        "TARGET_POSITION_NONZERO_PROVEN": TARGET_POSITION_NONZERO_PROVEN,
        "TARGET_POSITION_QTY_NUMERIC": TARGET_POSITION_QTY_NUMERIC,
        "TARGET_POSITION_QTY_UNIT": TARGET_POSITION_QTY_UNIT,
        "POS_TO_SZ_UNIT_IDENTITY": POS_TO_SZ_UNIT_IDENTITY,
        "LAST_CANONICALLY_CLOSED_STEP": LAST_CANONICALLY_CLOSED_STEP,
        "EARLIEST_UNRESOLVED_DEPENDENCY": EARLIEST_UNRESOLVED_DEPENDENCY,
        "NEXT_AUTHORITY_BOUNDARY": NEXT_AUTHORITY_BOUNDARY,
        "EXECUTION_PREREQUISITE_11_POSITION_SIDE_POSSIDE": (
            EXECUTION_PREREQUISITE_11_POSITION_SIDE_POSSIDE
        ),
        "P13_DOES_NOT_GRANT_EXECUTION_READINESS": P13_DOES_NOT_GRANT_EXECUTION_READINESS,
        "P13_DOES_NOT_AUTHORIZE_FLATTEN": P13_DOES_NOT_AUTHORIZE_FLATTEN,
        "RUNTIME_GET_REQUIRED": RUNTIME_GET_REQUIRED,
        "RUNTIME_GET_PERFORMED": RUNTIME_GET_PERFORMED,
        "PRIVATE_AUTH_USED": PRIVATE_AUTH_USED,
        "PUBLIC_SPEC_RETRIEVAL_PERFORMED": PUBLIC_SPEC_RETRIEVAL_PERFORMED,
        "LIVE_EXECUTION": False,
        "CANARY_EXECUTION": False,
        "MERGE_AUTHORIZED_BY_THIS_PERSIST": False,
        "THIS_GO_GET_COUNT": 0,
        "THIS_GO_POST_COUNT": 0,
        "GET_PERFORMED_THIS_PERSIST": False,
        "POST_PERFORMED": False,
        "FIELD_PROVENANCE": provenance,
        "LINEAGE": lineage,
        "CENSUS": census,
        "VENUE_NATIVE_BODY_KEYS": sorted(payload.body.keys()),
    }
