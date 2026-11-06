"""Current §11.14 Flatten-GO contract schema. No token mint. No consumption."""

from __future__ import annotations

from typing import Any, Mapping

from src.ops.section_11_14_current_sui_xperp_pos_1_flatten_authority_and_pre_execution_repair_v1.constants_v1 import (
    AUTHORITY_SOURCE_CANONICAL_OWNER_ISSUANCE,
    AUTHORITY_TYPE_OWNER_FLATTEN_ISSUANCE,
    BOUND_FROZEN_ENVELOPE_ID,
    BOUND_ORIGIN_MAIN_SHA,
    CAPTURE_REQUIRED,
    CONSUMED_ENTRY_OWNER_EXECUTION_GO,
    CONSUMED_GO_CANNOT_BE_REUSED,
    ENTRY_OWNER_GO_CANNOT_AUTHORIZE_FLATTEN,
    ENTRY_PURPOSE_FORBIDDEN,
    FLATTEN_ACTION,
    FLATTEN_CONFIRM_TOKEN_EXPECTED,
    FLATTEN_CONTRACT_KIND,
    FLATTEN_OWNER_GO_CANNOT_AUTHORIZE_ENTRY,
    FLATTEN_PURPOSE_EXPECTED,
    FLATTEN_SECTION,
    FORBIDDEN_AUTHORITY_SOURCES,
    HISTORICAL_G12_FLATTEN_OWNER_GO,
    HISTORICAL_G12_FLATTEN_PURPOSE,
    HISTORICAL_PRODUCTIVE_FLATTEN_OWNER_GO,
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
    REQUEST_POS_SIDE_POLICY,
    RETRY_ALLOWED,
    SECOND_SUBMIT_ALLOWED,
    SINGLE_USE_REQUIRED,
    VENUE_REDUCE_ONLY_NO_FLIP,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.constants_v1 import (
    CANARY_AUTHORIZED,
    LIVE_ARMED,
    LIVE_ENABLED,
    POST_ALLOWED,
)


class FlattenGoContractError(RuntimeError):
    """Fail-closed Flatten-GO contract violation."""


REQUIRED_CANDIDATE_FIELDS: tuple[str, ...] = (
    "action",
    "section",
    "purpose",
    "confirm_token",
    "origin_main_sha",
    "instrument_id",
    "expected_signed_position",
    "pos_side",
    "margin_mode",
    "order_side",
    "order_qty",
    "order_qty_unit",
    "reduce_only",
    "order_type",
    "exact_envelope_id",
    "single_use",
    "retry_allowed",
    "second_submit_allowed",
    "pre_submit_fresh_get_required",
    "post_submit_position_recon_required",
    "capture_required",
    "consumed",
    "venue_reduce_only_no_flip_acknowledgement",
)


def flatten_go_contract_schema_v1() -> dict[str, Any]:
    """Return the unbound schema. This is not an issued Owner GO."""
    return {
        "kind": FLATTEN_CONTRACT_KIND,
        "ISSUED": False,
        "PRESENT": False,
        "action": FLATTEN_ACTION,
        "section": FLATTEN_SECTION,
        "purpose_expected": FLATTEN_PURPOSE_EXPECTED,
        "confirm_token_expected": FLATTEN_CONFIRM_TOKEN_EXPECTED,
        "instrument_id_expected": INSTRUMENT_ID,
        "pos_side_expected": POS_SIDE_OBSERVED,
        "margin_mode_expected": MARGIN_MODE,
        "order_side_for_positive_pos": ORDER_SIDE_FOR_POSITIVE_POS,
        "order_qty_unit": ORDER_QTY_UNIT,
        "reduce_only_required": REDUCE_ONLY_REQUIRED,
        "order_type": ORDER_TYPE,
        "request_pos_side_policy": REQUEST_POS_SIDE_POLICY,
        "single_use_required": SINGLE_USE_REQUIRED,
        "retry_allowed": RETRY_ALLOWED,
        "second_submit_allowed": SECOND_SUBMIT_ALLOWED,
        "pre_submit_fresh_get_required": PRE_SUBMIT_FRESH_GET_REQUIRED,
        "post_submit_position_recon_required": POST_SUBMIT_POSITION_RECON_REQUIRED,
        "capture_required": CAPTURE_REQUIRED,
        "entry_owner_go_cannot_authorize_flatten": ENTRY_OWNER_GO_CANNOT_AUTHORIZE_FLATTEN,
        "flatten_owner_go_cannot_authorize_entry": FLATTEN_OWNER_GO_CANNOT_AUTHORIZE_ENTRY,
        "consumed_go_cannot_be_reused": CONSUMED_GO_CANNOT_BE_REUSED,
        "venue_reduce_only_no_flip": VENUE_REDUCE_ONLY_NO_FLIP,
        "standing_live_enabled": bool(LIVE_ENABLED),
        "standing_live_armed": bool(LIVE_ARMED),
        "standing_canary_authorized": bool(CANARY_AUTHORIZED),
        "standing_post_allowed": bool(POST_ALLOWED),
        "required_candidate_fields": list(REQUIRED_CANDIDATE_FIELDS),
        "MECHANISM_EXPECTED_VALUES_ARE_NOT_ISSUED_AUTHORITY": True,
        "EVALUATOR_IS_NOT_ISSUER": True,
        "CHAT_IS_NOT_AUTHORITY": True,
        "ENV_IS_NOT_AUTHORITY": True,
        "CLI_FLAG_IS_NOT_AUTHORITY": True,
    }


def _sha_ok(raw: Any) -> bool:
    text = str(raw or "").strip().lower()
    return len(text) == 40 and all(ch in "0123456789abcdef" for ch in text)


def verify_owner_flatten_issuance_v1(
    *,
    issuance: Mapping[str, Any] | None,
    origin_main_sha: str,
    instrument_id: str,
    expected_signed_position: str,
    order_side: str,
    order_qty: str,
    exact_envelope_id: str,
    durable_consumed_authority_id: str = "",
) -> dict[str, Any]:
    """Verify an issuance artifact. Does not mint issued=true."""
    from src.ops.section_11_14_current_sui_xperp_pos_1_flatten_authority_and_pre_execution_repair_v1.issuance_v1 import (
        ISSUANCE_INPUT_REQUIRED_FIELDS,
        flatten_authority_id_v1,
    )

    reasons: list[str] = []
    if issuance is None:
        return {
            "accepted": False,
            "issued": False,
            "reasons": ["ISSUANCE_ARTIFACT_MISSING"],
            "authority_id": "",
            "EVALUATOR_IS_NOT_ISSUER": True,
        }
    missing = [
        name
        for name in (*ISSUANCE_INPUT_REQUIRED_FIELDS, "issued", "authority_id")
        if name not in issuance
    ]
    if missing:
        reasons.append("ISSUANCE_FIELDS_MISSING:" + ",".join(missing))
    source = str(issuance.get("authority_source") or "").strip()
    if source != AUTHORITY_SOURCE_CANONICAL_OWNER_ISSUANCE:
        reasons.append("ISSUANCE_AUTHORITY_SOURCE_NOT_CANONICAL")
    if source in FORBIDDEN_AUTHORITY_SOURCES:
        reasons.append("ISSUANCE_AUTHORITY_SOURCE_FORBIDDEN")
    if str(issuance.get("schema_version") or "") != ISSUANCE_SCHEMA_VERSION:
        reasons.append("ISSUANCE_SCHEMA_VERSION_MISMATCH")
    if str(issuance.get("authority_type") or "") != AUTHORITY_TYPE_OWNER_FLATTEN_ISSUANCE:
        reasons.append("ISSUANCE_AUTHORITY_TYPE_MISMATCH")
    if issuance.get("issued") is not True:
        reasons.append("ISSUANCE_ARTIFACT_NOT_ISSUED")
    if str(issuance.get("section") or "") != FLATTEN_SECTION:
        reasons.append("ISSUANCE_SECTION_MISMATCH")
    if str(issuance.get("purpose") or "") != FLATTEN_PURPOSE_EXPECTED:
        reasons.append("ISSUANCE_PURPOSE_MISMATCH")
    if str(issuance.get("action") or "") != FLATTEN_ACTION:
        reasons.append("ISSUANCE_ACTION_MISMATCH")
    bound_sha = str(issuance.get("origin_main_sha") or "").strip().lower()
    expected_sha = str(origin_main_sha or "").strip().lower()
    if not _sha_ok(bound_sha) or not _sha_ok(expected_sha) or bound_sha != expected_sha:
        reasons.append("ISSUANCE_SHA_MISMATCH")
    if bound_sha != BOUND_ORIGIN_MAIN_SHA:
        reasons.append("ISSUANCE_SHA_NOT_CURRENT_BIND")
    if str(issuance.get("instrument_id") or "").strip() != str(instrument_id or "").strip():
        reasons.append("ISSUANCE_INSTRUMENT_MISMATCH")
    if (
        str(issuance.get("expected_signed_position") or "").strip()
        != str(expected_signed_position or "").strip()
    ):
        reasons.append("ISSUANCE_POSITION_MISMATCH")
    if str(issuance.get("pos_side") or "").strip() != POS_SIDE_OBSERVED:
        reasons.append("ISSUANCE_POS_SIDE_MISMATCH")
    if str(issuance.get("margin_mode") or "").strip() != MARGIN_MODE:
        reasons.append("ISSUANCE_MARGIN_MODE_MISMATCH")
    if (
        str(issuance.get("order_side") or "").strip().upper()
        != str(order_side or "").strip().upper()
    ):
        reasons.append("ISSUANCE_SIDE_MISMATCH")
    if str(issuance.get("order_qty") or "").strip() != str(order_qty or "").strip():
        reasons.append("ISSUANCE_QTY_MISMATCH")
    if str(issuance.get("order_qty_unit") or "").strip() != ORDER_QTY_UNIT:
        reasons.append("ISSUANCE_QTY_UNIT_MISMATCH")
    if issuance.get("reduce_only") is not True:
        reasons.append("ISSUANCE_REDUCE_ONLY_REQUIRED")
    if str(issuance.get("order_type") or "").strip().upper() != ORDER_TYPE:
        reasons.append("ISSUANCE_ORDER_TYPE_MISMATCH")
    if str(issuance.get("exact_envelope_id") or "").strip() != str(exact_envelope_id or "").strip():
        reasons.append("ISSUANCE_ENVELOPE_MISMATCH")
    if str(issuance.get("exact_envelope_id") or "") != BOUND_FROZEN_ENVELOPE_ID:
        reasons.append("ISSUANCE_ENVELOPE_NOT_CURRENT_BIND")
    if issuance.get("single_use") is not True:
        reasons.append("ISSUANCE_SINGLE_USE_REQUIRED")
    if issuance.get("retry_allowed") is not False:
        reasons.append("ISSUANCE_RETRY_MUST_BE_FALSE")
    if issuance.get("second_submit_allowed") is not False:
        reasons.append("ISSUANCE_SECOND_SUBMIT_MUST_BE_FALSE")
    if issuance.get("consumed") is True:
        reasons.append("ISSUANCE_CONSUMED")
    if issuance.get("pre_submit_fresh_get_required") is not True:
        reasons.append("ISSUANCE_PRE_SUBMIT_GET_REQUIRED")
    if issuance.get("post_submit_position_recon_required") is not True:
        reasons.append("ISSUANCE_POST_RECON_REQUIRED")
    if issuance.get("capture_required") is not True:
        reasons.append("ISSUANCE_CAPTURE_REQUIRED")
    if issuance.get("venue_reduce_only_no_flip_acknowledgement") is not True:
        reasons.append("ISSUANCE_VENUE_NO_FLIP_ACK_REQUIRED")
    if str(issuance.get("confirm_token") or "") != FLATTEN_CONFIRM_TOKEN_EXPECTED:
        reasons.append("ISSUANCE_CONFIRM_TOKEN_MISMATCH")
    authority_id = ""
    try:
        authority_id = flatten_authority_id_v1(issuance)
    except Exception as exc:  # noqa: BLE001
        reasons.append(f"ISSUANCE_AUTHORITY_ID_UNCOMPUTABLE:{exc}")
    recorded_id = str(issuance.get("authority_id") or "")
    if authority_id and recorded_id and recorded_id != authority_id:
        reasons.append("ISSUANCE_AUTHORITY_ID_MISMATCH")
    consumed_id = str(durable_consumed_authority_id or "").strip()
    if consumed_id and authority_id and consumed_id == authority_id:
        reasons.append("ISSUANCE_DURABLE_CONSUMED")
    runtime_issued = (not reasons) and issuance.get("issued") is True
    return {
        "accepted": not reasons,
        "issued": runtime_issued,
        "reasons": reasons,
        "authority_id": recorded_id or authority_id,
        "authority_source": source,
        "EVALUATOR_IS_NOT_ISSUER": True,
    }


def evaluate_flatten_go_candidate_v1(
    *,
    candidate: Mapping[str, Any] | None,
    origin_main_sha: str,
    instrument_id: str,
    expected_signed_position: str,
    order_side: str,
    order_qty: str,
    exact_envelope_id: str,
    entry_path: bool = False,
    issuance: Mapping[str, Any] | None = None,
    durable_consumed_authority_id: str = "",
) -> dict[str, Any]:
    """Validate a candidate and optionally verify an issuance artifact.

    This function never mints issued=true. Runtime issued is true only when a
    present artifact already carries issued=true and verification passes.
    """
    reasons: list[str] = []
    if LIVE_ENABLED or LIVE_ARMED or CANARY_AUTHORIZED or POST_ALLOWED:
        reasons.append("STANDING_LIVE_FLAGS_MUST_REMAIN_FALSE")
    if entry_path is True:
        reasons.append("FLATTEN_GO_CANNOT_AUTHORIZE_ENTRY")
        return {
            "accepted": False,
            "reasons": reasons,
            "present": candidate is not None,
            "issued": False,
            "EVALUATOR_IS_NOT_ISSUER": True,
        }
    if candidate is None and issuance is None:
        reasons.append("FLATTEN_GO_CANDIDATE_MISSING")
        return {
            "accepted": False,
            "reasons": reasons,
            "present": False,
            "issued": False,
            "EVALUATOR_IS_NOT_ISSUER": True,
        }
    if candidate is None:
        candidate = issuance

    missing = [name for name in REQUIRED_CANDIDATE_FIELDS if name not in candidate]
    if missing:
        reasons.append("FLATTEN_GO_FIELDS_MISSING:" + ",".join(missing))

    purpose = str(candidate.get("purpose") or "").strip()
    confirm = str(candidate.get("confirm_token") or "").strip()
    action = str(candidate.get("action") or "").strip()
    section = str(candidate.get("section") or "").strip()
    supplied_go = str(candidate.get("owner_go") or candidate.get("token_id") or "").strip()

    if action != FLATTEN_ACTION:
        reasons.append("FLATTEN_ACTION_MISMATCH")
    if section != FLATTEN_SECTION:
        reasons.append("FLATTEN_SECTION_MISMATCH")
    if purpose != FLATTEN_PURPOSE_EXPECTED:
        reasons.append("FLATTEN_PURPOSE_MISMATCH")
    if purpose == ENTRY_PURPOSE_FORBIDDEN or ENTRY_PURPOSE_FORBIDDEN in purpose:
        reasons.append("ENTRY_OWNER_GO_CANNOT_AUTHORIZE_FLATTEN")
    if purpose == HISTORICAL_G12_FLATTEN_PURPOSE:
        reasons.append("HISTORICAL_G12_FLATTEN_PURPOSE_FORBIDDEN")
    if confirm != FLATTEN_CONFIRM_TOKEN_EXPECTED:
        reasons.append("FLATTEN_CONFIRM_TOKEN_MISMATCH")
    if supplied_go == CONSUMED_ENTRY_OWNER_EXECUTION_GO:
        reasons.append("CONSUMED_ENTRY_GO_CANNOT_AUTHORIZE_FLATTEN")
    if supplied_go in {
        HISTORICAL_G12_FLATTEN_OWNER_GO,
        HISTORICAL_PRODUCTIVE_FLATTEN_OWNER_GO,
    }:
        reasons.append("HISTORICAL_G12_FLATTEN_GO_FORBIDDEN")
    if bool(candidate.get("consumed")) is True:
        reasons.append("CONSUMED_GO_CANNOT_BE_REUSED")

    bound_sha = str(candidate.get("origin_main_sha") or "").strip().lower()
    expected_sha = str(origin_main_sha or "").strip().lower()
    if not _sha_ok(bound_sha) or not _sha_ok(expected_sha) or bound_sha != expected_sha:
        reasons.append("FLATTEN_GO_SHA_MISMATCH")
    if str(candidate.get("instrument_id") or "").strip() != str(instrument_id or "").strip():
        reasons.append("FLATTEN_GO_INSTRUMENT_MISMATCH")
    if (
        str(candidate.get("expected_signed_position") or "").strip()
        != str(expected_signed_position or "").strip()
    ):
        reasons.append("FLATTEN_GO_POSITION_MISMATCH")
    if str(candidate.get("pos_side") or "").strip() != POS_SIDE_OBSERVED:
        reasons.append("FLATTEN_GO_POS_SIDE_MISMATCH")
    if str(candidate.get("margin_mode") or "").strip() != MARGIN_MODE:
        reasons.append("FLATTEN_GO_MARGIN_MODE_MISMATCH")
    if (
        str(candidate.get("order_side") or "").strip().upper()
        != str(order_side or "").strip().upper()
    ):
        reasons.append("FLATTEN_GO_SIDE_MISMATCH")
    if str(candidate.get("order_qty") or "").strip() != str(order_qty or "").strip():
        reasons.append("FLATTEN_GO_QTY_MISMATCH")
    if str(candidate.get("order_qty_unit") or "").strip() != ORDER_QTY_UNIT:
        reasons.append("FLATTEN_GO_QTY_UNIT_MISMATCH")
    if candidate.get("reduce_only") is not True:
        reasons.append("FLATTEN_GO_REDUCE_ONLY_REQUIRED")
    if str(candidate.get("order_type") or "").strip().upper() != ORDER_TYPE:
        reasons.append("FLATTEN_GO_ORDER_TYPE_MISMATCH")
    if (
        str(candidate.get("exact_envelope_id") or "").strip()
        != str(exact_envelope_id or "").strip()
    ):
        reasons.append("FLATTEN_GO_ENVELOPE_MISMATCH")
    if candidate.get("single_use") is not True:
        reasons.append("FLATTEN_GO_SINGLE_USE_REQUIRED")
    if candidate.get("retry_allowed") is not False:
        reasons.append("FLATTEN_GO_RETRY_MUST_BE_FALSE")
    if candidate.get("second_submit_allowed") is not False:
        reasons.append("FLATTEN_GO_SECOND_SUBMIT_MUST_BE_FALSE")
    if candidate.get("pre_submit_fresh_get_required") is not True:
        reasons.append("FLATTEN_GO_PRE_SUBMIT_GET_REQUIRED")
    if candidate.get("post_submit_position_recon_required") is not True:
        reasons.append("FLATTEN_GO_POST_RECON_REQUIRED")
    if candidate.get("capture_required") is not True:
        reasons.append("FLATTEN_GO_CAPTURE_REQUIRED")
    ack_value = candidate.get("venue_reduce_only_no_flip_acknowledgement")
    if issuance is None:
        ack = str(ack_value or "").strip()
        if ack != VENUE_REDUCE_ONLY_NO_FLIP:
            reasons.append("FLATTEN_GO_VENUE_NO_FLIP_ACK_REQUIRED_UNPROVEN")
    elif ack_value is not True and str(ack_value or "").strip() != VENUE_REDUCE_ONLY_NO_FLIP:
        reasons.append("FLATTEN_GO_VENUE_NO_FLIP_ACK_REQUIRED")

    issuance_verify: dict[str, Any] = {
        "accepted": False,
        "issued": False,
        "reasons": ["ISSUANCE_ARTIFACT_MISSING"],
        "authority_id": "",
        "EVALUATOR_IS_NOT_ISSUER": True,
    }
    if issuance is not None:
        issuance_verify = verify_owner_flatten_issuance_v1(
            issuance=issuance,
            origin_main_sha=origin_main_sha,
            instrument_id=instrument_id,
            expected_signed_position=expected_signed_position,
            order_side=order_side,
            order_qty=order_qty,
            exact_envelope_id=exact_envelope_id,
            durable_consumed_authority_id=durable_consumed_authority_id,
        )
        reasons.extend(str(item) for item in (issuance_verify.get("reasons") or []))
    runtime_issued = issuance is not None and issuance_verify.get("issued") is True
    candidate_accepted = not reasons
    if issuance is not None:
        candidate_accepted = candidate_accepted and issuance_verify.get("accepted") is True
    return {
        "accepted": candidate_accepted,
        "reasons": reasons,
        "present": True,
        "issued": runtime_issued,
        "kind": FLATTEN_CONTRACT_KIND,
        "EVALUATOR_IS_NOT_ISSUER": True,
        "authority_id": issuance_verify.get("authority_id") or "",
        "authority_source": issuance_verify.get("authority_source") or "",
        "issuance_present": issuance is not None,
    }


def reject_entry_go_on_flatten_path_v1(*, owner_go: str | None, purpose: str | None) -> list[str]:
    reasons: list[str] = []
    go = str(owner_go or "").strip()
    purpose_n = str(purpose or "").strip()
    if go == CONSUMED_ENTRY_OWNER_EXECUTION_GO:
        reasons.append("ENTRY_OWNER_GO_CANNOT_AUTHORIZE_FLATTEN")
    if purpose_n == ENTRY_PURPOSE_FORBIDDEN or "EXACT_SINGLE_LIVE_FILL" in purpose_n:
        reasons.append("ENTRY_PURPOSE_CANNOT_AUTHORIZE_FLATTEN")
    return reasons


def reject_flatten_go_on_entry_path_v1(
    *, purpose: str | None, confirm_token: str | None
) -> list[str]:
    reasons: list[str] = []
    if str(purpose or "").strip() == FLATTEN_PURPOSE_EXPECTED:
        reasons.append("FLATTEN_GO_CANNOT_AUTHORIZE_ENTRY")
    if str(confirm_token or "").strip() == FLATTEN_CONFIRM_TOKEN_EXPECTED:
        reasons.append("FLATTEN_CONFIRM_CANNOT_AUTHORIZE_ENTRY")
    return reasons
