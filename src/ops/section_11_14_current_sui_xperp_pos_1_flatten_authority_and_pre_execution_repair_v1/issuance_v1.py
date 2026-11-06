"""Canonical Owner Flatten issuance producer. Does not evaluate. Does not POST.

The producer is the only mint path for issued=true. It accepts a fully
explicit input mapping and never fills missing fields, never reads env,
never parses chat, and never treats CLI flags as authority.
"""

from __future__ import annotations

import hashlib
import json
from typing import Any, Mapping

from src.ops.section_11_14_current_sui_xperp_pos_1_flatten_authority_and_pre_execution_repair_v1.constants_v1 import (
    AUTHORITY_ID_FIELDS,
    AUTHORITY_SOURCE_CANONICAL_OWNER_ISSUANCE,
    AUTHORITY_TYPE_OWNER_FLATTEN_ISSUANCE,
    BOUND_FROZEN_ENVELOPE_ID,
    BOUND_ORIGIN_MAIN_SHA,
    CAPTURE_REQUIRED,
    FLATTEN_ACTION,
    FLATTEN_CONFIRM_TOKEN_EXPECTED,
    FLATTEN_PURPOSE_EXPECTED,
    FLATTEN_SECTION,
    FORBIDDEN_AUTHORITY_SOURCES,
    INSTRUMENT_ID,
    ISSUANCE_SCHEMA_VERSION,
    MARGIN_MODE,
    ORDER_QTY_UNIT,
    ORDER_SIDE_FOR_POSITIVE_POS,
    ORDER_TYPE,
    POS_SIDE_OBSERVED,
    POST_SUBMIT_POSITION_RECON_REQUIRED,
    PRE_SUBMIT_FRESH_GET_REQUIRED,
    REDUCE_ONLY_REQUIRED,
    RETRY_ALLOWED,
    SECOND_SUBMIT_ALLOWED,
    SINGLE_USE_REQUIRED,
    VENUE_REDUCE_ONLY_NO_FLIP_OWNER_ACK,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.constants_v1 import (
    CANARY_AUTHORIZED,
    LIVE_ARMED,
    LIVE_ENABLED,
    POST_ALLOWED,
)

ISSUANCE_INPUT_REQUIRED_FIELDS: tuple[str, ...] = (
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
    "expected_signed_position",
    "pos_side",
    "margin_mode",
    "order_side",
    "order_qty",
    "order_qty_unit",
    "reduce_only",
    "order_type",
    "pre_submit_fresh_get_required",
    "post_submit_position_recon_required",
    "capture_required",
    "venue_reduce_only_no_flip_acknowledgement",
    "confirm_token",
    "single_use",
    "consumed",
    "retry_allowed",
    "second_submit_allowed",
)


class FlattenOwnerIssuanceError(RuntimeError):
    """Fail-closed Owner issuance producer violation."""


def _qty_or_pos_ok(raw: Any) -> bool:
    return raw == 1 or raw == "1"


def _canonical_qty(raw: Any) -> str:
    if not _qty_or_pos_ok(raw):
        raise FlattenOwnerIssuanceError("ISSUANCE_QTY_OR_POS_NOT_CANONICAL_1")
    return "1"


def flatten_authority_id_v1(payload: Mapping[str, Any]) -> str:
    """Deterministic SHA-256 over AUTHORITY_ID_FIELDS canonical JSON."""
    missing = [name for name in AUTHORITY_ID_FIELDS if name not in payload]
    if missing:
        raise FlattenOwnerIssuanceError("AUTHORITY_ID_FIELDS_MISSING:" + ",".join(missing))
    material = {name: payload[name] for name in AUTHORITY_ID_FIELDS}
    encoded = json.dumps(material, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def _bind_reasons(explicit: Mapping[str, Any]) -> list[str]:
    reasons: list[str] = []
    if str(explicit.get("schema_version") or "") != ISSUANCE_SCHEMA_VERSION:
        reasons.append("ISSUANCE_SCHEMA_VERSION_MISMATCH")
    if str(explicit.get("authority_type") or "") != AUTHORITY_TYPE_OWNER_FLATTEN_ISSUANCE:
        reasons.append("ISSUANCE_AUTHORITY_TYPE_MISMATCH")
    source = str(explicit.get("authority_source") or "").strip()
    if source != AUTHORITY_SOURCE_CANONICAL_OWNER_ISSUANCE:
        reasons.append("ISSUANCE_AUTHORITY_SOURCE_NOT_CANONICAL")
    if source in FORBIDDEN_AUTHORITY_SOURCES:
        reasons.append("ISSUANCE_AUTHORITY_SOURCE_FORBIDDEN")
    if not str(explicit.get("issued_at") or "").strip():
        reasons.append("ISSUANCE_ISSUED_AT_REQUIRED")
    if str(explicit.get("section") or "") != FLATTEN_SECTION:
        reasons.append("ISSUANCE_SECTION_MISMATCH")
    if str(explicit.get("purpose") or "") != FLATTEN_PURPOSE_EXPECTED:
        reasons.append("ISSUANCE_PURPOSE_MISMATCH")
    if str(explicit.get("action") or "") != FLATTEN_ACTION:
        reasons.append("ISSUANCE_ACTION_MISMATCH")
    if str(explicit.get("origin_main_sha") or "").strip().lower() != BOUND_ORIGIN_MAIN_SHA:
        reasons.append("ISSUANCE_SHA_MISMATCH")
    if str(explicit.get("exact_envelope_id") or "") != BOUND_FROZEN_ENVELOPE_ID:
        reasons.append("ISSUANCE_ENVELOPE_MISMATCH")
    if str(explicit.get("instrument_id") or "") != INSTRUMENT_ID:
        reasons.append("ISSUANCE_INSTRUMENT_MISMATCH")
    if not _qty_or_pos_ok(explicit.get("expected_signed_position")):
        reasons.append("ISSUANCE_POSITION_MISMATCH")
    if str(explicit.get("pos_side") or "") != POS_SIDE_OBSERVED:
        reasons.append("ISSUANCE_POS_SIDE_MISMATCH")
    if str(explicit.get("margin_mode") or "") != MARGIN_MODE:
        reasons.append("ISSUANCE_MARGIN_MODE_MISMATCH")
    if str(explicit.get("order_side") or "").strip().upper() != ORDER_SIDE_FOR_POSITIVE_POS:
        reasons.append("ISSUANCE_SIDE_MISMATCH")
    if not _qty_or_pos_ok(explicit.get("order_qty")):
        reasons.append("ISSUANCE_QTY_MISMATCH")
    if str(explicit.get("order_qty_unit") or "") != ORDER_QTY_UNIT:
        reasons.append("ISSUANCE_QTY_UNIT_MISMATCH")
    if explicit.get("reduce_only") is not True:
        reasons.append("ISSUANCE_REDUCE_ONLY_REQUIRED")
    if str(explicit.get("order_type") or "").strip().upper() != ORDER_TYPE:
        reasons.append("ISSUANCE_ORDER_TYPE_MISMATCH")
    if explicit.get("pre_submit_fresh_get_required") is not True:
        reasons.append("ISSUANCE_PRE_SUBMIT_GET_REQUIRED")
    if explicit.get("post_submit_position_recon_required") is not True:
        reasons.append("ISSUANCE_POST_RECON_REQUIRED")
    if explicit.get("capture_required") is not True:
        reasons.append("ISSUANCE_CAPTURE_REQUIRED")
    if explicit.get("venue_reduce_only_no_flip_acknowledgement") is not True:
        reasons.append("ISSUANCE_VENUE_NO_FLIP_ACK_REQUIRED")
    if str(explicit.get("confirm_token") or "") != FLATTEN_CONFIRM_TOKEN_EXPECTED:
        reasons.append("ISSUANCE_CONFIRM_TOKEN_MISMATCH")
    if explicit.get("single_use") is not True:
        reasons.append("ISSUANCE_SINGLE_USE_REQUIRED")
    if explicit.get("consumed") is not False:
        reasons.append("ISSUANCE_CONSUMED_MUST_BE_FALSE")
    if explicit.get("retry_allowed") is not False:
        reasons.append("ISSUANCE_RETRY_MUST_BE_FALSE")
    if explicit.get("second_submit_allowed") is not False:
        reasons.append("ISSUANCE_SECOND_SUBMIT_MUST_BE_FALSE")
    if PRE_SUBMIT_FRESH_GET_REQUIRED is not True or POST_SUBMIT_POSITION_RECON_REQUIRED is not True:
        reasons.append("ISSUANCE_STANDING_CAPTURE_CONTRACT_DRIFT")
    if CAPTURE_REQUIRED is not True or REDUCE_ONLY_REQUIRED is not True:
        reasons.append("ISSUANCE_STANDING_REDUCE_ONLY_CONTRACT_DRIFT")
    if SINGLE_USE_REQUIRED is not True:
        reasons.append("ISSUANCE_STANDING_SINGLE_USE_DRIFT")
    if RETRY_ALLOWED is True or SECOND_SUBMIT_ALLOWED is True:
        reasons.append("ISSUANCE_STANDING_RETRY_DRIFT")
    if VENUE_REDUCE_ONLY_NO_FLIP_OWNER_ACK is not True:
        reasons.append("ISSUANCE_OWNER_ACK_CONSTANT_DRIFT")
    return reasons


def issue_owner_flatten_authority_v1(*, explicit: Mapping[str, Any] | None) -> dict[str, Any]:
    """Mint issued=true only from a fully explicit canonical Owner input."""
    if LIVE_ENABLED or LIVE_ARMED or CANARY_AUTHORIZED or POST_ALLOWED:
        raise FlattenOwnerIssuanceError("STANDING_LIVE_FLAG_MUST_REMAIN_FALSE")
    reasons: list[str] = []
    if explicit is None:
        return {
            "issued": False,
            "reasons": ["ISSUANCE_EXPLICIT_INPUT_MISSING"],
            "artifact": None,
            "EVALUATOR_IS_NOT_ISSUER": True,
            "CHAT_IS_NOT_AUTHORITY": True,
            "ENV_IS_NOT_AUTHORITY": True,
            "CLI_FLAG_IS_NOT_AUTHORITY": True,
        }
    if "issued" in explicit:
        reasons.append("ISSUANCE_INPUT_MUST_NOT_SELF_ATTEST_ISSUED")
    missing = [name for name in ISSUANCE_INPUT_REQUIRED_FIELDS if name not in explicit]
    if missing:
        reasons.append("ISSUANCE_FIELDS_MISSING:" + ",".join(missing))
    reasons.extend(_bind_reasons(explicit))
    if reasons:
        return {
            "issued": False,
            "reasons": reasons,
            "artifact": None,
            "EVALUATOR_IS_NOT_ISSUER": True,
            "CHAT_IS_NOT_AUTHORITY": True,
            "ENV_IS_NOT_AUTHORITY": True,
            "CLI_FLAG_IS_NOT_AUTHORITY": True,
        }
    expected_pos = _canonical_qty(explicit.get("expected_signed_position"))
    order_qty = _canonical_qty(explicit.get("order_qty"))
    artifact: dict[str, Any] = {
        "schema_version": str(explicit["schema_version"]),
        "authority_type": str(explicit["authority_type"]),
        "authority_source": str(explicit["authority_source"]),
        "issued": True,
        "issued_at": str(explicit["issued_at"]),
        "section": str(explicit["section"]),
        "purpose": str(explicit["purpose"]),
        "action": str(explicit["action"]),
        "origin_main_sha": str(explicit["origin_main_sha"]).strip().lower(),
        "exact_envelope_id": str(explicit["exact_envelope_id"]),
        "instrument_id": str(explicit["instrument_id"]),
        "expected_signed_position": expected_pos,
        "pos_side": str(explicit["pos_side"]),
        "margin_mode": str(explicit["margin_mode"]),
        "order_side": str(explicit["order_side"]).strip().upper(),
        "order_qty": order_qty,
        "order_qty_unit": str(explicit["order_qty_unit"]),
        "reduce_only": True,
        "order_type": str(explicit["order_type"]).strip().upper(),
        "pre_submit_fresh_get_required": True,
        "post_submit_position_recon_required": True,
        "capture_required": True,
        "venue_reduce_only_no_flip_acknowledgement": True,
        "confirm_token": str(explicit["confirm_token"]),
        "single_use": True,
        "consumed": False,
        "retry_allowed": False,
        "second_submit_allowed": False,
        "CHAT_IS_NOT_AUTHORITY": True,
        "ENV_IS_NOT_AUTHORITY": True,
        "CLI_FLAG_IS_NOT_AUTHORITY": True,
        "EVALUATOR_IS_NOT_ISSUER": True,
        "AUTHORITY_IS_SINGLE_USE": True,
    }
    artifact["authority_id"] = flatten_authority_id_v1(artifact)
    return {
        "issued": True,
        "reasons": [],
        "artifact": artifact,
        "EVALUATOR_IS_NOT_ISSUER": True,
        "CHAT_IS_NOT_AUTHORITY": True,
        "ENV_IS_NOT_AUTHORITY": True,
        "CLI_FLAG_IS_NOT_AUTHORITY": True,
    }


def current_section_11_14_issuance_explicit_v1(*, issued_at: str) -> dict[str, Any]:
    """Fully explicit current-bind input. Not itself an issued artifact."""
    return {
        "schema_version": ISSUANCE_SCHEMA_VERSION,
        "authority_type": AUTHORITY_TYPE_OWNER_FLATTEN_ISSUANCE,
        "authority_source": AUTHORITY_SOURCE_CANONICAL_OWNER_ISSUANCE,
        "issued_at": str(issued_at),
        "section": FLATTEN_SECTION,
        "purpose": FLATTEN_PURPOSE_EXPECTED,
        "action": FLATTEN_ACTION,
        "origin_main_sha": BOUND_ORIGIN_MAIN_SHA,
        "exact_envelope_id": BOUND_FROZEN_ENVELOPE_ID,
        "instrument_id": INSTRUMENT_ID,
        "expected_signed_position": "1",
        "pos_side": POS_SIDE_OBSERVED,
        "margin_mode": MARGIN_MODE,
        "order_side": ORDER_SIDE_FOR_POSITIVE_POS,
        "order_qty": "1",
        "order_qty_unit": ORDER_QTY_UNIT,
        "reduce_only": True,
        "order_type": ORDER_TYPE,
        "pre_submit_fresh_get_required": True,
        "post_submit_position_recon_required": True,
        "capture_required": True,
        "venue_reduce_only_no_flip_acknowledgement": True,
        "confirm_token": FLATTEN_CONFIRM_TOKEN_EXPECTED,
        "single_use": True,
        "consumed": False,
        "retry_allowed": False,
        "second_submit_allowed": False,
    }
