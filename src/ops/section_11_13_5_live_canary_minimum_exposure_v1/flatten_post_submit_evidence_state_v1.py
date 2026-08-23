"""Offline post-submit flatten evidence-state classifier.

Classifies caller-supplied HTTP/snapshot evidence only. Never GETs, never
POSTs, never enables live wire, and never claims LIVE_FLATTEN_PROVABILITY
or productive venue proof. Fixture satisfaction is contract behavior only.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from typing import Any, Mapping

from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.constants_v1 import (
    DEFAULT_INSTRUMENT_ID,
    LIVE_AUTHORIZED,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.flatten_limit_price_contract_v1 import (
    LIVE_FLATTEN_PROVABILITY_STATUS,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.flatten_post_action_proof_contract_v1 import (
    evaluate_canary_flatten_post_action_proof_contract_v1,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.flatten_submit_transport_v1 import (
    DEDICATED_FLATTEN_TRANSPORT_LIVE_WIRE_ENABLED,
)

STATE_NOT_SUBMITTED = "NOT_SUBMITTED"
STATE_SUBMITTED_UNACKNOWLEDGED = "SUBMITTED_UNACKNOWLEDGED"
STATE_ACKNOWLEDGED = "ACKNOWLEDGED"
STATE_FILLED = "FILLED"
STATE_POSITION_CLOSED_PROVEN = "POSITION_CLOSED_PROVEN"
STATE_POSITION_REMAINS = "POSITION_REMAINS"
STATE_UNKNOWN_FAIL_CLOSED = "UNKNOWN_FAIL_CLOSED"

_ACK_OK_CODES = frozenset({"0"})


class LiveCanaryFlattenPostSubmitEvidenceError(RuntimeError):
    """Fail-closed post-submit evidence-state violation."""


@dataclass(frozen=True)
class CanaryFlattenPostSubmitEvidenceStateV1:
    """Injected-evidence classification. Not productive venue proof."""

    evidence_state: str
    submit_attempted: bool
    send_attempted: bool
    acknowledged: bool
    filled_claimed: bool
    position_closed_contract: bool
    productive_venue_proof: bool
    live_flatten_provability: str
    live_wire_enabled: bool
    live_authorized: bool
    actual_post: bool
    blocking_reasons: tuple[str, ...]
    audit_class: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "evidence_state": self.evidence_state,
            "submit_attempted": self.submit_attempted,
            "send_attempted": self.send_attempted,
            "acknowledged": self.acknowledged,
            "filled_claimed": self.filled_claimed,
            "position_closed_contract": self.position_closed_contract,
            "productive_venue_proof": self.productive_venue_proof,
            "live_flatten_provability": self.live_flatten_provability,
            "live_wire_enabled": self.live_wire_enabled,
            "live_authorized": self.live_authorized,
            "actual_post": self.actual_post,
            "blocking_reasons": list(self.blocking_reasons),
            "audit_class": self.audit_class,
        }


def _result(
    *,
    evidence_state: str,
    submit_attempted: bool,
    send_attempted: bool,
    acknowledged: bool,
    filled_claimed: bool,
    position_closed_contract: bool,
    actual_post: bool,
    blocking_reasons: tuple[str, ...],
    audit_class: str,
) -> CanaryFlattenPostSubmitEvidenceStateV1:
    if LIVE_AUTHORIZED or DEDICATED_FLATTEN_TRANSPORT_LIVE_WIRE_ENABLED:
        raise LiveCanaryFlattenPostSubmitEvidenceError("LIVE_WIRE_MUST_REMAIN_DISABLED")
    return CanaryFlattenPostSubmitEvidenceStateV1(
        evidence_state=evidence_state,
        submit_attempted=submit_attempted,
        send_attempted=send_attempted,
        acknowledged=acknowledged,
        filled_claimed=filled_claimed,
        position_closed_contract=position_closed_contract,
        productive_venue_proof=False,
        live_flatten_provability=LIVE_FLATTEN_PROVABILITY_STATUS,
        live_wire_enabled=False,
        live_authorized=False,
        actual_post=actual_post,
        blocking_reasons=blocking_reasons,
        audit_class=audit_class,
    )


def _dec(raw: Any) -> Decimal | None:
    if raw is None or str(raw).strip() == "":
        return None
    try:
        return Decimal(str(raw).strip())
    except (InvalidOperation, TypeError, ValueError):
        return None


def _parse_ack(response_body: Mapping[str, Any] | None) -> tuple[bool, bool, tuple[str, ...]]:
    """Return (acknowledged, filled_claimed, reasons). Conservative: no invented fills."""
    if response_body is None:
        return False, False, ("RESPONSE_BODY_MISSING",)
    if not isinstance(response_body, Mapping):
        return False, False, ("RESPONSE_BODY_NOT_MAPPING",)
    if str(response_body.get("code") or "") not in _ACK_OK_CODES:
        return False, False, ("EXCHANGE_CODE_NOT_OK",)
    data = response_body.get("data")
    if data is None:
        data = []
    if not isinstance(data, list) or len(data) != 1:
        return False, False, ("ACK_DATA_AMBIGUOUS",)
    row = data[0]
    if not isinstance(row, Mapping):
        return False, False, ("ACK_ROW_NOT_MAPPING",)
    scode = str(row.get("sCode") or row.get("s_code") or "")
    if scode not in _ACK_OK_CODES:
        return False, False, ("SCODE_NOT_OK",)
    fill = _dec(row.get("accFillSz") if row.get("accFillSz") is not None else row.get("fillSz"))
    sz = _dec(row.get("sz"))
    filled = fill is not None and sz is not None and fill == sz and fill > 0
    return True, filled, ()


def evaluate_canary_flatten_post_submit_evidence_state_v1(
    *,
    submit_attempted: bool,
    send_attempted: bool = False,
    http_status: int | None = None,
    response_body: Mapping[str, Any] | None = None,
    transport_error: str | None = None,
    pre_positions_payload: Mapping[str, Any] | None = None,
    post_positions_payload: Mapping[str, Any] | None = None,
    post_pending_orders_payload: Mapping[str, Any] | None = None,
    instrument_id: str = DEFAULT_INSTRUMENT_ID,
    requested_qty: str | None = None,
) -> CanaryFlattenPostSubmitEvidenceStateV1:
    """Classify injected flatten evidence. Never a venue-proof upgrade."""
    del requested_qty  # sizing authority stays on the construction path
    target = str(instrument_id or "").strip()
    if not target or target != DEFAULT_INSTRUMENT_ID:
        return _result(
            evidence_state=STATE_UNKNOWN_FAIL_CLOSED,
            submit_attempted=bool(submit_attempted),
            send_attempted=bool(send_attempted),
            acknowledged=False,
            filled_claimed=False,
            position_closed_contract=False,
            actual_post=False,
            blocking_reasons=("INSTRUMENT_BINDING_MISMATCH",),
            audit_class="unknown_fail_closed",
        )

    if not submit_attempted and not send_attempted:
        return _result(
            evidence_state=STATE_NOT_SUBMITTED,
            submit_attempted=False,
            send_attempted=False,
            acknowledged=False,
            filled_claimed=False,
            position_closed_contract=False,
            actual_post=False,
            blocking_reasons=("NO_POST_ATTEMPTED",),
            audit_class="offline_intent_construction",
        )

    if send_attempted and not submit_attempted:
        return _result(
            evidence_state=STATE_UNKNOWN_FAIL_CLOSED,
            submit_attempted=False,
            send_attempted=True,
            acknowledged=False,
            filled_claimed=False,
            position_closed_contract=False,
            actual_post=False,
            blocking_reasons=("SEND_WITHOUT_SUBMIT_ATTEMPT",),
            audit_class="unknown_fail_closed",
        )

    err = str(transport_error or "").strip()
    if err in {"UNKNOWN_FLATTEN_SUBMIT_TIMEOUT", "UNKNOWN_FLATTEN_SUBMIT_NETWORK", "TIMEOUT"}:
        return _result(
            evidence_state=STATE_SUBMITTED_UNACKNOWLEDGED,
            submit_attempted=True,
            send_attempted=True,
            acknowledged=False,
            filled_claimed=False,
            position_closed_contract=False,
            actual_post=True,
            blocking_reasons=(err,),
            audit_class="submitted_unacknowledged",
        )
    if err == "UNKNOWN_FLATTEN_SUBMIT_NO_BLIND_RETRY":
        return _result(
            evidence_state=STATE_UNKNOWN_FAIL_CLOSED,
            submit_attempted=True,
            send_attempted=True,
            acknowledged=False,
            filled_claimed=False,
            position_closed_contract=False,
            actual_post=True,
            blocking_reasons=(err, "NO_RETRY"),
            audit_class="unknown_fail_closed",
        )
    if err == "DUPLICATE_FLATTEN_SUBMIT_FORBIDDEN":
        return _result(
            evidence_state=STATE_UNKNOWN_FAIL_CLOSED,
            submit_attempted=True,
            send_attempted=bool(send_attempted),
            acknowledged=False,
            filled_claimed=False,
            position_closed_contract=False,
            actual_post=False,
            blocking_reasons=(err, "NO_RETRY"),
            audit_class="unknown_fail_closed",
        )

    if http_status is None and response_body is None:
        return _result(
            evidence_state=STATE_SUBMITTED_UNACKNOWLEDGED,
            submit_attempted=True,
            send_attempted=True,
            acknowledged=False,
            filled_claimed=False,
            position_closed_contract=False,
            actual_post=True,
            blocking_reasons=("NO_PARSEABLE_ACK",),
            audit_class="submitted_unacknowledged",
        )

    if http_status is not None and int(http_status) != 200:
        return _result(
            evidence_state=STATE_UNKNOWN_FAIL_CLOSED,
            submit_attempted=True,
            send_attempted=True,
            acknowledged=False,
            filled_claimed=False,
            position_closed_contract=False,
            actual_post=True,
            blocking_reasons=(f"HTTP_STATUS_{http_status}",),
            audit_class="unknown_fail_closed",
        )

    acknowledged, filled_claimed, ack_reasons = _parse_ack(response_body)
    if not acknowledged:
        return _result(
            evidence_state=STATE_UNKNOWN_FAIL_CLOSED,
            submit_attempted=True,
            send_attempted=True,
            acknowledged=False,
            filled_claimed=False,
            position_closed_contract=False,
            actual_post=True,
            blocking_reasons=ack_reasons or ("ACK_UNPROVEN",),
            audit_class="unknown_fail_closed",
        )

    if (
        pre_positions_payload is None
        or post_positions_payload is None
        or post_pending_orders_payload is None
    ):
        state = STATE_FILLED if filled_claimed else STATE_ACKNOWLEDGED
        return _result(
            evidence_state=state,
            submit_attempted=True,
            send_attempted=True,
            acknowledged=True,
            filled_claimed=filled_claimed,
            position_closed_contract=False,
            actual_post=True,
            blocking_reasons=("POST_POSITION_SNAPSHOTS_NOT_SUPPLIED",),
            audit_class="venue_acknowledgement",
        )

    post_action = evaluate_canary_flatten_post_action_proof_contract_v1(
        pre_positions_payload=pre_positions_payload,
        post_positions_payload=post_positions_payload,
        post_pending_orders_payload=post_pending_orders_payload,
        instrument_id=target,
    )
    if post_action.already_flat_noop:
        return _result(
            evidence_state=STATE_UNKNOWN_FAIL_CLOSED,
            submit_attempted=True,
            send_attempted=True,
            acknowledged=True,
            filled_claimed=filled_claimed,
            position_closed_contract=False,
            actual_post=True,
            blocking_reasons=("ALREADY_FLAT_AFTER_CLAIMED_SUBMIT",),
            audit_class="unknown_fail_closed",
        )
    if post_action.offline_contract_satisfied:
        return _result(
            evidence_state=STATE_POSITION_CLOSED_PROVEN,
            submit_attempted=True,
            send_attempted=True,
            acknowledged=True,
            filled_claimed=filled_claimed,
            position_closed_contract=True,
            actual_post=True,
            blocking_reasons=(
                "INJECTED_SNAPSHOT_CONTRACT_ONLY",
                "PRODUCTIVE_VENUE_PROOF_FALSE",
            ),
            audit_class="fill_position_closure_contract_not_venue_proof",
        )
    if not post_action.post_pos_zero:
        return _result(
            evidence_state=STATE_POSITION_REMAINS,
            submit_attempted=True,
            send_attempted=True,
            acknowledged=True,
            filled_claimed=filled_claimed,
            position_closed_contract=False,
            actual_post=True,
            blocking_reasons=tuple(post_action.blocking_reasons) or ("POST_NOT_FLAT",),
            audit_class="position_remains",
        )
    state = STATE_FILLED if filled_claimed else STATE_ACKNOWLEDGED
    return _result(
        evidence_state=state,
        submit_attempted=True,
        send_attempted=True,
        acknowledged=True,
        filled_claimed=filled_claimed,
        position_closed_contract=False,
        actual_post=True,
        blocking_reasons=tuple(post_action.blocking_reasons) or ("POST_ACTION_NOT_CLOSED",),
        audit_class="venue_acknowledgement",
    )
