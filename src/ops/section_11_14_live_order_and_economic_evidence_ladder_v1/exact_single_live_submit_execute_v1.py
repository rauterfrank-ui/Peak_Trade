"""Exactly one governed productive Live entry submit for §11.14 ACK.

Session-arms live_enabled / live_armed / live_canary_authorized only as call
parameters. Standing module gates remain false. Reuses
``run_canary_submit_transport_v1`` with ``observe_order_plan_only=False``.
Does not copy the historical 20260904T140500Z order-plan artifact.
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

from src.core.environment import LIVE_CONFIRM_TOKEN
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.config_v1 import (
    load_live_canary_config_v1,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.constants_v1 import (
    LIVE_ARMED as CANARY_LIVE_ARMED,
    LIVE_AUTHORIZED as CANARY_LIVE_AUTHORIZED,
    LIVE_ENABLED as CANARY_LIVE_ENABLED,
    OWNER_GO_EXECUTE,
    SUBMIT_UNLOCKED,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.http_client_v1 import (
    LiveCanaryTransportV1,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.live_credential_ephemeral_v1 import (
    build_file_secretref_vault_backend_v1,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.submit_gates_v1 import (
    LiveCanarySubmitGateError,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.submit_transport_v1 import (
    LiveCanarySubmitTransportError,
    run_canary_submit_transport_v1,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.constants_v1 import (
    CANARY_TECHNICAL_EXECUTE_TOKEN,
    LIVE_ARMED,
    LIVE_AUTHORIZED,
    LIVE_ENABLED,
    LIVE_EXECUTION_CODE_EXISTS,
    LIVE_EXECUTION_PATH_REACHABLE,
    LIVE_ORDER_PLAN_OBSERVED,
    LIVE_PRIVATE_READ_ONLY_PROVEN,
    POST_ALLOWED,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.contract_v1 import (
    Section1114OfflineSurfaceError,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.credential_presence_v1 import (
    default_vault_path_v1,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.order_plan_observe_execute_v1 import (
    productive_canary_execute_config_dict_v1,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.submit_ack_observed_adjudication_v1 import (
    adjudicate_live_submit_ack_observed_v1,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.submit_ack_observed_predicate_v1 import (
    ADMISSIBLE_SOURCE_KIND,
)

THIS_OWNER_GO = "PEAK_TRADE_OWNER_GO_SECTION_11_14_EXACT_SINGLE_LIVE_SUBMIT_POST_V1"
EXPECTED_ORIGIN_MAIN_SHA = "d6d3fa2970aafc9517cff9c0b8c1685dabd9791b"
HISTORICAL_ORDER_PLAN_RUN_ID = "20260904T140500Z"

_PRODUCTIVE_SUBMIT_BUDGET_CONSUMED = False


def _utc_now_iso_v1() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _sanitize_plan_v1(plan: Mapping[str, Any] | None) -> dict[str, Any] | None:
    if not isinstance(plan, Mapping):
        return None
    venue = plan.get("venue_native_payload")
    venue_map = venue if isinstance(venue, Mapping) else {}
    return {
        "instrument_id": plan.get("instrument_id"),
        "side": plan.get("side"),
        "order_type": plan.get("order_type"),
        "td_mode": plan.get("td_mode"),
        "quantity": plan.get("quantity"),
        "quantity_domain": plan.get("quantity_domain"),
        "quantity_unit": plan.get("quantity_unit"),
        "limit_price": plan.get("limit_price"),
        "clordid_present": bool(str(plan.get("clordid") or "").strip()),
        "clordid": str(plan.get("clordid") or ""),
        "venue_native_instId": venue_map.get("instId"),
        "venue_native_tdMode": venue_map.get("tdMode"),
        "venue_native_side": venue_map.get("side"),
        "venue_native_ordType": venue_map.get("ordType"),
        "venue_native_sz": venue_map.get("sz"),
        "venue_native_px": venue_map.get("px"),
    }


def _ack_input_from_transport_v1(
    *,
    payload: Mapping[str, Any] | None,
    send_attempted: bool,
    post_used: bool,
) -> dict[str, Any]:
    payload_map = dict(payload or {})
    http_ev = dict(payload_map.get("http_error_evidence") or {})
    adj = dict(payload_map.get("submit_adjudication_evidence") or {})
    plan = payload_map.get("plan") if isinstance(payload_map.get("plan"), Mapping) else {}
    venue = (
        plan.get("venue_native_payload")
        if isinstance(plan.get("venue_native_payload"), Mapping)
        else {}
    )
    rows = list(http_ev.get("okx_data") or adj.get("okx_data") or [])
    row: Mapping[str, Any] = rows[0] if rows and isinstance(rows[0], Mapping) else {}
    sent = str(plan.get("clordid") or venue.get("clOrdId") or "").strip()
    returned = str(row.get("clOrdId") or "").strip()
    canary_result = str(payload_map.get("CANARY_RESULT") or "")
    recon_match = canary_result in {
        "UNKNOWN_SUBMIT_RESOLVED_PENDING",
        "UNKNOWN_SUBMIT_RESOLVED_HISTORY",
    }
    data_count = http_ev.get("okx_data_count")
    if data_count is None:
        data_count = adj.get("OKX_DATA_COUNT")
    transport_error = str(payload_map.get("error") or "") or None
    counters = dict(payload_map.get("counters") or {})
    entry_count = int(counters.get("ENTRY_SUBMIT_COUNT") or 0)
    return {
        "source_kind": ADMISSIBLE_SOURCE_KIND,
        "POST_USED": post_used,
        "send_attempted": send_attempted,
        "entry_submit_count": entry_count,
        "http_status": http_ev.get("http_status") or payload_map.get("http_status"),
        "okx_code": http_ev.get("okx_code") or adj.get("TOP_LEVEL_OKX_CODE"),
        "json_parse_ok": http_ev.get("json_parse_ok"),
        "redirect_followed": bool(http_ev.get("redirect_followed")),
        "redirectish": bool(http_ev.get("redirect_status"))
        or bool(http_ev.get("redirect_followed")),
        "data_count": data_count,
        "s_code": row.get("sCode"),
        "ord_id": row.get("ordId"),
        "returned_clordid": returned or None,
        "sent_clordid": sent or None,
        "transport_error": transport_error,
        "CURRENT_PRODUCTIVE_POST_OF_FRESH_PLAN": bool(post_used and send_attempted),
        "historical_plan_reused": False,
        "read_only_recon_clordid_match": recon_match,
        "LIVE_FILL_OBSERVED": False,
        "LIVE_SUBMIT_ACK_OBSERVED": False,
    }


def execute_exact_single_live_submit_post_v1(
    *,
    owner_go: str,
    origin_main_sha: str,
    vault_file: Path | None = None,
    vault_backend: Any = None,
    transport: LiveCanaryTransportV1 | None = None,
) -> dict[str, Any]:
    global _PRODUCTIVE_SUBMIT_BUDGET_CONSUMED
    if str(owner_go or "").strip() != THIS_OWNER_GO:
        raise Section1114OfflineSurfaceError("OWNER_GO_MISMATCH")
    if str(origin_main_sha or "").strip() != EXPECTED_ORIGIN_MAIN_SHA:
        raise Section1114OfflineSurfaceError("ORIGIN_MAIN_SHA_MISMATCH")
    if LIVE_AUTHORIZED is True or LIVE_ENABLED is True or LIVE_ARMED is True:
        raise Section1114OfflineSurfaceError("STANDING_LIVE_GATE_TRUE")
    if CANARY_LIVE_AUTHORIZED is True or CANARY_LIVE_ENABLED is True or CANARY_LIVE_ARMED is True:
        raise Section1114OfflineSurfaceError("CANARY_STANDING_LIVE_GATE_TRUE")
    if SUBMIT_UNLOCKED is True:
        raise Section1114OfflineSurfaceError("STANDING_SUBMIT_UNLOCKED_TRUE")
    if POST_ALLOWED is True:
        raise Section1114OfflineSurfaceError("STANDING_POST_ALLOWED_MUST_REMAIN_FALSE")
    if CANARY_TECHNICAL_EXECUTE_TOKEN != OWNER_GO_EXECUTE:
        raise Section1114OfflineSurfaceError("CANARY_TECHNICAL_TOKEN_DRIFT")
    if LIVE_EXECUTION_CODE_EXISTS is not True:
        raise Section1114OfflineSurfaceError("CODE_EXISTS_PREDECESSOR_FALSE")
    if LIVE_EXECUTION_PATH_REACHABLE is not True:
        raise Section1114OfflineSurfaceError("PATH_REACHABLE_PREDECESSOR_FALSE")
    if LIVE_PRIVATE_READ_ONLY_PROVEN is not True:
        raise Section1114OfflineSurfaceError("PRIVATE_READ_ONLY_PREDECESSOR_FALSE")
    if LIVE_ORDER_PLAN_OBSERVED is not True:
        raise Section1114OfflineSurfaceError("ORDER_PLAN_PREDECESSOR_FALSE")
    if _PRODUCTIVE_SUBMIT_BUDGET_CONSUMED:
        raise Section1114OfflineSurfaceError("PRODUCTIVE_SUBMIT_BUDGET_ALREADY_CONSUMED")

    gate_state_before = {
        "LIVE_ENABLED_STANDING": LIVE_ENABLED,
        "LIVE_ARMED_STANDING": LIVE_ARMED,
        "SUBMIT_UNLOCKED_STANDING": SUBMIT_UNLOCKED,
        "LIVE_AUTHORIZED_STANDING": LIVE_AUTHORIZED,
        "POST_ALLOWED_STANDING": POST_ALLOWED,
        "SESSION_LIVE_ENABLED": False,
        "SESSION_LIVE_ARMED": False,
        "SESSION_LIVE_CANARY_AUTHORIZED": False,
    }
    cfg = load_live_canary_config_v1(
        productive_canary_execute_config_dict_v1(),
        require_execute_fields=True,
    )
    backend = vault_backend
    if backend is None and transport is None:
        path = (
            Path(vault_file)
            if vault_file is not None
            else default_vault_path_v1(repo_root=Path(__file__).resolve().parents[3])
        )
        backend = build_file_secretref_vault_backend_v1(vault_file=path)

    started = _utc_now_iso_v1()
    blocked_reason: str | None = None
    transport_payload: dict[str, Any] | None = None
    try:
        transport_payload = run_canary_submit_transport_v1(
            cfg=cfg,
            origin_main_sha=origin_main_sha,
            owner_go=OWNER_GO_EXECUTE,
            live_canary_authorized=True,
            live_enabled=True,
            live_armed=True,
            confirm_token=LIVE_CONFIRM_TOKEN,
            owner_go_consumed=False,
            permission_attestation={"READ": True, "TRADE": True, "WITHDRAW": False},
            transport=transport,
            allow_productive_wire_send=transport is None,
            live_canary_cybersecurity_gate="PASS",
            vault_backend=backend,
            observe_order_plan_only=False,
        )
    except (LiveCanarySubmitTransportError, LiveCanarySubmitGateError) as exc:
        blocked_reason = str(exc)
        transport_payload = None
    ended = _utc_now_iso_v1()

    payload = dict(transport_payload) if isinstance(transport_payload, Mapping) else {}
    counters = dict(payload.get("counters") or {})
    post_count = int(counters.get("ENTRY_SUBMIT_COUNT") or 0)
    unknown = bool(payload.get("UNKNOWN_SUBMIT") is True)
    error_text = str(payload.get("error") or blocked_reason or "")
    send_attempted = bool(
        unknown
        or post_count > 0
        or payload.get("SESSION_ENTRY_SUBMITTED") is True
        or "UNKNOWN_SUBMIT" in error_text
    )
    post_used = bool(
        post_count > 0
        or payload.get("SESSION_ENTRY_SUBMITTED") is True
        or payload.get("mode") == "execute"
        and send_attempted
    )
    if send_attempted:
        _PRODUCTIVE_SUBMIT_BUDGET_CONSUMED = True

    pre_wire_stop = None if send_attempted else blocked_reason
    submit_gate = payload.get("submit_gate")
    gate_map = submit_gate if isinstance(submit_gate, Mapping) else {}
    gate_conjunction_pass = (
        transport_payload is not None
        and blocked_reason is None
        and gate_map.get("SUBMIT_ALLOWED") is True
    )

    ack_input = _ack_input_from_transport_v1(
        payload=payload if payload else None,
        send_attempted=send_attempted,
        post_used=post_used and send_attempted,
    )
    ack = adjudicate_live_submit_ack_observed_v1(submit_ack_evidence=ack_input)
    plan = _sanitize_plan_v1(
        payload.get("plan") if isinstance(payload.get("plan"), Mapping) else None
    )

    return {
        "OWNER_GO": THIS_OWNER_GO,
        "CANARY_TECHNICAL_EXECUTE_TOKEN": OWNER_GO_EXECUTE,
        "ORIGIN_MAIN_SHA": origin_main_sha,
        "STARTED_AT_UTC": started,
        "ENDED_AT_UTC": ended,
        "HISTORICAL_PLAN_REUSED": False,
        "HISTORICAL_ORDER_PLAN_RUN_ID_NOT_LOADED": HISTORICAL_ORDER_PLAN_RUN_ID,
        "FRESH_PLAN_PRODUCED": plan is not None,
        "plan": plan,
        "PRE_WIRE_LOCKS": {
            "DUPLICATE_ENTRY_SUBMIT_FORBIDDEN": True,
            "UNKNOWN_SUBMIT_NO_BLIND_RETRY": True,
            "NEW_CLIENT_ENTRY_SUBMIT_COUNT_START": 0,
            "NEW_CLIENT_SEND_ATTEMPTED_START": False,
        },
        "GATE_STATE_BEFORE": gate_state_before,
        "GATE_STATE_DURING": {
            "SESSION_LIVE_ENABLED": True,
            "SESSION_LIVE_ARMED": True,
            "SESSION_LIVE_CANARY_AUTHORIZED": True,
            "STANDING_LIVE_ENABLED": False,
            "STANDING_LIVE_ARMED": False,
            "STANDING_SUBMIT_UNLOCKED": False,
            "STANDING_POST_ALLOWED": False,
        },
        "GATE_STATE_AFTER": {
            "LIVE_ENABLED_STANDING": LIVE_ENABLED,
            "LIVE_ARMED_STANDING": LIVE_ARMED,
            "SUBMIT_UNLOCKED_STANDING": SUBMIT_UNLOCKED,
            "LIVE_AUTHORIZED_STANDING": LIVE_AUTHORIZED,
            "POST_ALLOWED_STANDING": POST_ALLOWED,
        },
        "CURRENT_GATE_CONJUNCTION_STATUS": (
            "PASS"
            if gate_conjunction_pass and send_attempted
            else (
                "FAIL_CLOSED_BEFORE_WIRE"
                if pre_wire_stop
                else ("PASS" if gate_conjunction_pass else "UNKNOWN")
            )
        ),
        "PRE_WIRE_STOP_REASON": pre_wire_stop,
        "BLOCKED_REASON": blocked_reason,
        "PRODUCTIVE_POST_ATTEMPTED": send_attempted,
        "PRODUCTIVE_POST_ATTEMPT_COUNT": 1 if send_attempted else 0,
        "WIRE_SEND_ATTEMPTED": send_attempted,
        "UNKNOWN_SUBMIT_STATE": unknown or ("UNKNOWN_SUBMIT" in error_text),
        "RETRY_PERFORMED": False,
        "SECOND_SUBMIT_PERFORMED": False,
        "READ_ONLY_RECON_PERFORMED": bool(ack_input.get("read_only_recon_clordid_match"))
        or str(payload.get("CANARY_RESULT") or "").startswith("UNKNOWN_SUBMIT"),
        "CANARY_RESULT": payload.get("CANARY_RESULT"),
        "submit_gate": payload.get("submit_gate"),
        "pre_submit_state": payload.get("pre_submit_state"),
        "counters": counters,
        "http_status": ack_input.get("http_status"),
        "okx_code": ack_input.get("okx_code"),
        "s_code": ack_input.get("s_code"),
        "ord_id": ack_input.get("ord_id"),
        "sent_clordid": ack_input.get("sent_clordid"),
        "returned_clordid": ack_input.get("returned_clordid"),
        "ACK_SOURCE_KIND": ADMISSIBLE_SOURCE_KIND,
        "ack_adjudication": ack,
        "LIVE_SUBMIT_ACK_OBSERVED": ack.get("LIVE_SUBMIT_ACK_OBSERVED") is True,
        "LIVE_FILL_OBSERVED": False,
        "LIVE_FEE_OBSERVED": False,
        "LIVE_POSITION_RECONCILED": False,
        "SECTION_11_14_COMPLETE": False,
        "SECTION_11_14_AUTHORIZED": False,
        "SECRET_VALUES_INCLUDED": False,
        "error": payload.get("error"),
    }
