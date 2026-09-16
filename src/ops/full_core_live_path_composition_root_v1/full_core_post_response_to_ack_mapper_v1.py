"""Full-Core POST-result → Cap-11.1 post-submit lifecycle join.

Consumes an existing Full-Core POST result (or a typed transport failure) and
joins it onto the already ratified Cap 11.1 lifecycle machine plus Full-Core
recon classes. Venue-event normalization only. One-way downstream of POST.

CURRENT authority used, not redesigned:
- Master Runbook §11.4 SUBMIT_ATTEMPTED → ACKNOWLEDGED | REJECTED | UNKNOWN
- Cap 11.1 order-lifecycle machine and UNKNOWN-submit semantics
- §11.2.1.DM HTTP 200 / code=0 / sCode=0 is submit ACK, not fill
- Ambiguous / malformed / timeout => UNKNOWN fail-closed
- UNKNOWN never blindly resubmits; exchange query is required first
- Fill is never inferred from a submit ACK

Does not import §11.14. Does not promote the historical live-submit ACK
standing field.
Does not mutate Master-V2, Double Play, 29P/29Q, FILEGATE, permit, or
EXTERNAL_EFFECT standing authority. Does not POST.

RUNTIME_AUTHORIZATION_EFFECT=NONE
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping, Optional

from src.ops.capability_11_1_execution_domain_and_order_lifecycle_contracts_v1.order_lifecycle_state_machine_v1 import (
    OrderLifecycleStateMachineV1,
    OrderLifecycleTransitionError,
)
from src.ops.capability_11_1_execution_domain_and_order_lifecycle_contracts_v1.submission_semantics_v1 import (
    UnknownSubmitSemanticsV1,
)
from src.ops.full_core_live_path_composition_root_v1.constants_v1 import (
    POST_SUBMIT_RECON,
    RESTART_RECON,
    UNKNOWN_OUTCOME_RECON,
)
from src.ops.full_core_live_path_composition_root_v1.full_core_productive_http_post_transport_v1 import (
    FullCoreTradeOrderPostResultV1,
)

FULL_CORE_POST_RESPONSE_TO_ACK_MAPPER_IMPLEMENTED = True
FULL_CORE_POST_SUBMIT_LIFECYCLE_JOIN_ACTIVATED = True
MAPPER_OWNER = (
    "ops.full_core_live_path_composition_root_v1.full_core_post_response_to_ack_mapper_v1"
)
LIFECYCLE_OWNER = (
    "ops.capability_11_1_execution_domain_and_order_lifecycle_contracts_v1"
    ".order_lifecycle_state_machine_v1"
)
ACKNOWLEDGED = "ACKNOWLEDGED"
REJECTED = "REJECTED"
UNKNOWN = "UNKNOWN"
SUBMIT_ATTEMPTED = "SUBMIT_ATTEMPTED"

_TIMEOUT_TOKENS = ("TIMEOUT", "TimeoutError", "socket.timeout")
_NETWORK_TOKENS = ("NETWORK", "URLError", "OSError", "UNKNOWN_OUTCOME")


class FullCorePostSubmitJoinError(RuntimeError):
    """Fail-closed post-submit join violation."""


@dataclass(frozen=True)
class FullCorePostSubmitJoinResultV1:
    post_attempted: bool
    typed_outcome: str
    lifecycle_state: str
    recon_class: str
    restart_blocked: bool
    fill_observed: bool
    resubmit_allowed: bool
    blind_retry_forbidden: bool
    exchange_query_before_retry_required: bool
    unknown_requires_exchange_query: bool
    venue_order_id: str
    client_order_id: str
    reason: str
    http_status: int
    ack_is_not_fill: bool
    http_success_is_not_ack: bool
    mapper_owner: str
    lifecycle_owner: str
    section_11_14_promoted: bool
    real_post_count: int


def _nonempty(value: Any) -> bool:
    return bool(str(value or "").strip())


def _data_rows(payload: Any) -> list[Mapping[str, Any]]:
    if not isinstance(payload, Mapping):
        return []
    rows = payload.get("data")
    if not isinstance(rows, list):
        return []
    return [row for row in rows if isinstance(row, Mapping)]


def _error_text(transport_error: str | None) -> str:
    return str(transport_error or "")


def classify_full_core_post_result_v1(
    *,
    result: Optional[FullCoreTradeOrderPostResultV1],
    sent_clordid: str,
    submit_count: int = 1,
    transport_error: str | None = None,
    redirect: bool = False,
) -> dict[str, Any]:
    """Map a POST result to ACKNOWLEDGED | REJECTED | UNKNOWN. Never a fill."""

    err = _error_text(transport_error)
    sent = str(sent_clordid or "").strip()
    post_attempted = bool(result is not None and result.post_attempted is True) or bool(err)
    http_status = int(result.http_status) if result is not None else 0
    payload: Any = result.payload if result is not None else None
    parsed = isinstance(payload, Mapping)
    code = str(payload.get("code") or "") if parsed else ""
    rows = _data_rows(payload) if parsed else []
    data_count = len(rows)
    row = rows[0] if data_count == 1 else {}
    scode = str(row.get("sCode") or "") if row else ""
    ord_id = str(row.get("ordId") or "").strip() if row else ""
    returned = str(row.get("clOrdId") or "").strip() if row else ""
    transport_unknown = bool(result is not None and result.unknown_outcome is True)

    if result is not None and result.post_attempted is not True and not err:
        classification = UNKNOWN
        reason = "REQUEST_NOT_SENT_OR_LOCAL_ERROR_BEFORE_WIRE"
    elif any(token in err for token in _TIMEOUT_TOKENS):
        classification = UNKNOWN
        reason = "TIMEOUT_AFTER_POSSIBLE_SEND"
    elif any(token in err for token in _NETWORK_TOKENS) or transport_unknown:
        classification = UNKNOWN
        reason = "CONNECTION_OR_TRANSPORT_FAILURE_AFTER_SEND_ATTEMPTED"
    elif redirect is True:
        classification = UNKNOWN
        reason = "REDIRECT_IS_UNKNOWN_NOT_ACK"
    elif result is None:
        classification = UNKNOWN
        reason = "POST_RESULT_MISSING"
    elif not parsed:
        classification = UNKNOWN
        reason = "PARSE_FAILURE"
    elif parsed and _nonempty(code) and code != "0":
        classification = REJECTED
        reason = "TOP_LEVEL_CODE_NOT_ZERO"
    elif parsed and code == "0" and data_count == 1 and _nonempty(scode) and scode != "0":
        classification = REJECTED
        reason = "SCODE_NOT_ZERO"
    elif http_status != 200:
        classification = UNKNOWN
        reason = "HTTP_STATUS_NOT_200"
    elif code != "0":
        classification = UNKNOWN
        reason = "TOP_LEVEL_CODE_MISSING_OR_UNCLEAR"
    elif data_count != 1:
        classification = UNKNOWN
        reason = "DATA_CARDINALITY_NOT_EXACTLY_ONE"
    elif scode != "0":
        classification = UNKNOWN
        reason = "SCODE_MISSING_OR_UNCLEAR"
    elif not _nonempty(ord_id):
        classification = UNKNOWN
        reason = "ORDID_MISSING"
    elif not _nonempty(returned):
        classification = UNKNOWN
        reason = "RETURNED_CLORDID_MISSING"
    elif not _nonempty(sent) or returned != sent:
        classification = UNKNOWN
        reason = "CLORDID_IDENTITY_MISMATCH"
    elif int(submit_count) != 1:
        classification = UNKNOWN
        reason = "SUBMIT_COUNT_NOT_ONE"
    else:
        classification = ACKNOWLEDGED
        reason = "SYNCHRONOUS_ACK_NOT_FILL"

    return {
        "classification": classification,
        "reason": reason,
        "post_attempted": bool(post_attempted),
        "http_status": http_status,
        "venue_order_id": ord_id if classification == ACKNOWLEDGED else "",
        "client_order_id": returned if classification == ACKNOWLEDGED else sent,
        "fill_observed": False,
        "http_success_is_not_ack": True,
        "ack_is_not_fill": True,
        "resubmit_allowed": False,
    }


def _advance_cap11_1_from_submit_attempted(target: str) -> tuple[str, bool]:
    machine = OrderLifecycleStateMachineV1(
        current_state=SUBMIT_ATTEMPTED,
        history=[SUBMIT_ATTEMPTED],
    )
    try:
        machine.transition(target)
    except OrderLifecycleTransitionError as exc:
        raise FullCorePostSubmitJoinError(str(exc)) from exc
    restart_blocked = False
    if machine.current_state == UNKNOWN:
        try:
            machine.transition(ACKNOWLEDGED, exchange_query_completed=False)
        except OrderLifecycleTransitionError as exc:
            restart_blocked = exc.code == "UNKNOWN_REQUIRES_EXCHANGE_QUERY_BEFORE_RETRY"
        if restart_blocked is not True:
            raise FullCorePostSubmitJoinError("UNKNOWN_RESTART_GATE_NOT_BOUND")
    return machine.current_state, restart_blocked


def join_full_core_post_result_to_lifecycle_v1(
    *,
    result: Optional[FullCoreTradeOrderPostResultV1],
    sent_clordid: str,
    submit_count: int = 1,
    transport_error: str | None = None,
    redirect: bool = False,
) -> FullCorePostSubmitJoinResultV1:
    """Join POST result → typed outcome → Cap 11.1 + Full-Core recon/restart."""

    classified = classify_full_core_post_result_v1(
        result=result,
        sent_clordid=sent_clordid,
        submit_count=submit_count,
        transport_error=transport_error,
        redirect=redirect,
    )
    outcome = str(classified["classification"])
    lifecycle_state, restart_blocked = _advance_cap11_1_from_submit_attempted(outcome)
    unknown = UnknownSubmitSemanticsV1()
    blind = unknown.evaluate_retry_admissibility(
        exchange_query_completed=False,
        blind_retry=True,
    )
    query_required = unknown.evaluate_retry_admissibility(
        exchange_query_completed=False,
        blind_retry=False,
    )
    if blind["admissible"] is True:
        raise FullCorePostSubmitJoinError("BLIND_RETRY_MUST_REMAIN_FORBIDDEN")
    if outcome == UNKNOWN:
        recon = UNKNOWN_OUTCOME_RECON
        restart_blocked = True
        if query_required["admissible"] is True:
            raise FullCorePostSubmitJoinError("UNKNOWN_MUST_REQUIRE_EXCHANGE_QUERY")
    elif outcome in {ACKNOWLEDGED, REJECTED}:
        recon = POST_SUBMIT_RECON
        restart_blocked = False
    else:
        recon = UNKNOWN_OUTCOME_RECON
        restart_blocked = True
    return FullCorePostSubmitJoinResultV1(
        post_attempted=bool(classified["post_attempted"]),
        typed_outcome=outcome,
        lifecycle_state=lifecycle_state,
        recon_class=recon,
        restart_blocked=bool(restart_blocked),
        fill_observed=False,
        resubmit_allowed=False,
        blind_retry_forbidden=True,
        exchange_query_before_retry_required=bool(outcome == UNKNOWN),
        unknown_requires_exchange_query=bool(outcome == UNKNOWN),
        venue_order_id=str(classified["venue_order_id"]),
        client_order_id=str(classified["client_order_id"]),
        reason=str(classified["reason"]),
        http_status=int(classified["http_status"]),
        ack_is_not_fill=True,
        http_success_is_not_ack=True,
        mapper_owner=MAPPER_OWNER,
        lifecycle_owner=LIFECYCLE_OWNER,
        section_11_14_promoted=False,
        real_post_count=0,
    )


def prove_unknown_blocks_blind_resubmit_v1(
    join: FullCorePostSubmitJoinResultV1,
) -> bool:
    if join.typed_outcome != UNKNOWN:
        return join.resubmit_allowed is False
    if join.resubmit_allowed is True:
        return False
    if join.restart_blocked is not True:
        return False
    if join.recon_class != UNKNOWN_OUTCOME_RECON:
        return False
    unknown = UnknownSubmitSemanticsV1()
    blind = unknown.evaluate_retry_admissibility(
        exchange_query_completed=False,
        blind_retry=True,
    )
    return blind["admissible"] is False and join.recon_class != RESTART_RECON
