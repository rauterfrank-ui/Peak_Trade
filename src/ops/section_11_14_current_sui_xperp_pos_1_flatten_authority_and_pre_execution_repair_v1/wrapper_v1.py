"""Current-SHA §11.14 flatten execution wrapper. Fail-closed. No live POST in this repair."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping, Protocol

from src.ops.section_11_14_current_sui_xperp_pos_1_flatten_authority_and_pre_execution_repair_v1.capture_wiring_v1 import (
    capture_readiness_v1,
)
from src.ops.section_11_14_current_sui_xperp_pos_1_flatten_authority_and_pre_execution_repair_v1.constants_v1 import (
    CLOSE_POSITION_ENDPOINT,
    FLATTEN_ACTION,
    FLATTEN_HTTP_ENDPOINT,
    FLATTEN_HTTP_METHOD,
    HISTORICAL_PRODUCTIVE_FLATTEN_SHA,
    INSTRUMENT_ID,
    RETRY_ALLOWED,
    SECOND_SUBMIT_ALLOWED,
    SESSION_ARMING_STANDING,
)
from src.ops.section_11_14_current_sui_xperp_pos_1_flatten_authority_and_pre_execution_repair_v1.contract_v1 import (
    evaluate_flatten_go_candidate_v1,
    reject_entry_go_on_flatten_path_v1,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.constants_v1 import (
    CANARY_AUTHORIZED,
    LIVE_ARMED,
    LIVE_ENABLED,
    POST_ALLOWED,
)


class FlattenWrapperError(RuntimeError):
    """Fail-closed current-SHA flatten wrapper violation."""


class FlattenSubmitTransportV1(Protocol):
    def post(self, *, endpoint: str, body: Mapping[str, Any]) -> Mapping[str, Any]:
        """One POST. Tests bind fake transports only."""


@dataclass
class RecordingFakeFlattenSubmitTransportV1:
    calls: list[dict[str, Any]] = field(default_factory=list)

    def post(self, *, endpoint: str, body: Mapping[str, Any]) -> Mapping[str, Any]:
        path = str(endpoint or "").split("?", 1)[0]
        if path == CLOSE_POSITION_ENDPOINT:
            raise FlattenWrapperError("CLOSE_POSITION_ENDPOINT_REJECTED")
        if path != FLATTEN_HTTP_ENDPOINT:
            raise FlattenWrapperError(f"UNEXPECTED_POST_ENDPOINT:{endpoint}")
        self.calls.append({"method": "POST", "endpoint": endpoint, "body": dict(body)})
        return {"code": "0", "data": [{"ordId": "FAKE", "sCode": "0"}]}


def _sha_ok(raw: Any) -> bool:
    text = str(raw or "").strip().lower()
    return len(text) == 40 and all(ch in "0123456789abcdef" for ch in text)


def evaluate_current_sha_flatten_wrapper_v1(
    *,
    origin_main_sha: str,
    flatten_go_candidate: Mapping[str, Any] | None,
    envelope: Mapping[str, Any] | None,
    session_armed: bool = SESSION_ARMING_STANDING,
    capture_wired: bool = False,
    retry: bool = False,
    second_submit: bool = False,
    durable_consumed: bool = False,
    transport: FlattenSubmitTransportV1 | None = None,
    entry_owner_go: str | None = None,
    entry_purpose: str | None = None,
) -> dict[str, Any]:
    """Structurally exist the flatten submit path. Default is deny / no POST."""
    reasons: list[str] = []
    post_count = 0
    if LIVE_ENABLED or LIVE_ARMED or CANARY_AUTHORIZED or POST_ALLOWED:
        reasons.append("STANDING_LIVE_FLAGS_MUST_REMAIN_FALSE")
    sha = str(origin_main_sha or "").strip().lower()
    if not _sha_ok(sha):
        reasons.append("ORIGIN_MAIN_SHA_REQUIRED")
    if sha == HISTORICAL_PRODUCTIVE_FLATTEN_SHA:
        reasons.append("HISTORICAL_WRAPPER_SHA_MUST_NOT_BE_UNFROZEN")
    entry_reasons = reject_entry_go_on_flatten_path_v1(
        owner_go=entry_owner_go, purpose=entry_purpose
    )
    reasons.extend(entry_reasons)
    if retry is True or RETRY_ALLOWED is True:
        reasons.append("RETRY_FORBIDDEN")
    if second_submit is True or SECOND_SUBMIT_ALLOWED is True:
        reasons.append("SECOND_SUBMIT_FORBIDDEN")
    if durable_consumed is True:
        reasons.append("CONSUMED_STATE_CANNOT_RESUBMIT")
    if session_armed is not True:
        reasons.append("SESSION_NOT_ARMED")
    capture = capture_readiness_v1(wiring_bound=capture_wired)
    if capture.get("ready") is not True:
        reasons.append("CAPTURE_NOT_READY")
    if envelope is None:
        reasons.append("CURRENT_SELL_ENVELOPE_MISSING")
        envelope_id = ""
        instrument = ""
        side = ""
        qty = ""
        signed_pos = ""
    else:
        if str(envelope.get("KIND") or "") != "SECTION_11_14_FLATTEN_SELL_ENVELOPE_V1":
            reasons.append("ENVELOPE_KIND_NOT_FLATTEN_SELL")
        envelope_id = str(envelope.get("FLATTEN_ENVELOPE_ID") or "")
        instrument = str(envelope.get("INSTRUMENT_ID") or "")
        side = str(envelope.get("SIDE") or "")
        qty = str(envelope.get("QTY") or "")
        signed_pos = str(envelope.get("SIGNED_POS") or "")
        if instrument != INSTRUMENT_ID:
            reasons.append("WRAPPER_INSTRUMENT_MISMATCH")
        if str(envelope.get("ORIGIN_MAIN_SHA") or "").strip().lower() != sha:
            reasons.append("ENVELOPE_SHA_MISMATCH")
        if not envelope_id:
            reasons.append("ENVELOPE_ID_MISSING")
    verdict = evaluate_flatten_go_candidate_v1(
        candidate=flatten_go_candidate,
        origin_main_sha=sha,
        instrument_id=instrument or INSTRUMENT_ID,
        expected_signed_position=signed_pos or "1",
        order_side=side or "SELL",
        order_qty=qty or "1",
        exact_envelope_id=envelope_id,
        entry_path=False,
    )
    if verdict.get("accepted") is not True:
        reasons.extend(str(item) for item in (verdict.get("reasons") or []))
    if reasons:
        return {
            "accepted": False,
            "reasons": reasons,
            "POST_PERFORMED": False,
            "POST_COUNT": 0,
            "WIRE_SEND_EXECUTED": False,
            "FLATTEN_EXECUTED": False,
            "OWNER_TOKEN_CONSUMED": False,
            "TRANSPORT_BOUND": transport is not None,
            "STRUCTURAL_ENDPOINT": FLATTEN_HTTP_ENDPOINT,
            "STRUCTURAL_METHOD": FLATTEN_HTTP_METHOD,
            "ACTION": FLATTEN_ACTION,
        }
    if transport is None:
        return {
            "accepted": False,
            "reasons": ["PRODUCTIVE_TRANSPORT_NOT_BOUND"],
            "POST_PERFORMED": False,
            "POST_COUNT": 0,
            "WIRE_SEND_EXECUTED": False,
            "FLATTEN_EXECUTED": False,
            "OWNER_TOKEN_CONSUMED": False,
            "STRUCTURAL_ENDPOINT": FLATTEN_HTTP_ENDPOINT,
            "STRUCTURAL_METHOD": FLATTEN_HTTP_METHOD,
            "NOTE": "Gates passed structurally; live transport remains unbound in this repair.",
        }
    body = dict((envelope or {}).get("VENUE_NATIVE_BODY_PREVIEW") or {})
    if not body:
        raise FlattenWrapperError("VENUE_NATIVE_BODY_MISSING")
    transport.post(endpoint=FLATTEN_HTTP_ENDPOINT, body=body)
    post_count = 1
    return {
        "accepted": True,
        "reasons": [],
        "POST_PERFORMED": True,
        "POST_COUNT": post_count,
        "WIRE_SEND_EXECUTED": False,
        "FLATTEN_EXECUTED": False,
        "OWNER_TOKEN_CONSUMED": False,
        "FAKE_TRANSPORT_ONLY": True,
        "STRUCTURAL_ENDPOINT": FLATTEN_HTTP_ENDPOINT,
        "STRUCTURAL_METHOD": FLATTEN_HTTP_METHOD,
    }


def reject_close_position_endpoint_v1(endpoint: str) -> None:
    path = str(endpoint or "").split("?", 1)[0]
    if path == CLOSE_POSITION_ENDPOINT or path.endswith("/trade/close-position"):
        raise FlattenWrapperError("CLOSE_POSITION_ENDPOINT_REJECTED")
