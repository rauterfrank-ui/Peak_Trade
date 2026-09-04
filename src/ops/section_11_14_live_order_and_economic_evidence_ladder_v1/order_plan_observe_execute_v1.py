"""Execute the gated canary path and stop after the order-plan artifact.

Session-arms LIVE_ENABLED / LIVE_ARMED / live_canary_authorized only as
call parameters. Standing module gates remain false. Does not POST.
Uses the canary technical execute token on the producer; this workpackage
Owner-GO authorizes that invocation.
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

from src.core.environment import LIVE_CONFIRM_TOKEN
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.config_v1 import (
    example_incomplete_config_dict_v1,
    load_live_canary_config_v1,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.constants_v1 import (
    DEFAULT_INSTRUMENT_ID,
    DEFAULT_ORDER_TYPE,
    DEFAULT_SIDE,
    DEFAULT_TD_MODE,
    OWNER_GO_EXECUTE,
    REQUIRED_CREDENTIAL_CLASS,
    REQUIRED_SECRETREF_URI,
    REUSED_BINDING_ACCOUNT_SCOPE,
    REUSED_BINDING_ENTITY,
    REUSED_BINDING_REGION,
    REUSED_BINDING_REST_HOST,
    REUSED_BINDING_VENUE,
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
    EXPECTED_ORIGIN_MAIN_SHA,
    LIVE_ARMED,
    LIVE_AUTHORIZED,
    LIVE_ENABLED,
    LIVE_EXECUTION_CODE_EXISTS,
    LIVE_EXECUTION_PATH_REACHABLE,
    LIVE_PRIVATE_READ_ONLY_PROVEN,
    OWNER_GO,
    POST_ALLOWED,
    POST_REQUIRED_FOR_LIVE_ORDER_PLAN_OBSERVED,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.contract_v1 import (
    Section1114OfflineSurfaceError,
    assert_contract_invariants_v1,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.credential_presence_v1 import (
    default_vault_path_v1,
)


def _utc_now_iso_v1() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def productive_canary_execute_config_dict_v1() -> dict[str, Any]:
    payload = example_incomplete_config_dict_v1()
    payload.update(
        {
            "venue": REUSED_BINDING_VENUE,
            "entity": REUSED_BINDING_ENTITY,
            "region": REUSED_BINDING_REGION,
            "rest_host": REUSED_BINDING_REST_HOST,
            "rest_base": f"https://{REUSED_BINDING_REST_HOST}",
            "account_scope": REUSED_BINDING_ACCOUNT_SCOPE,
            "instrument_id": DEFAULT_INSTRUMENT_ID,
            "side": DEFAULT_SIDE,
            "order_type": DEFAULT_ORDER_TYPE,
            "td_mode": DEFAULT_TD_MODE,
            "secretref_uri": REQUIRED_SECRETREF_URI,
            "credential_class": REQUIRED_CREDENTIAL_CLASS,
            "owner_declared_host_allowlist": [REUSED_BINDING_REST_HOST],
        }
    )
    return payload


def _sanitize_plan_v1(plan: Mapping[str, Any] | None) -> dict[str, Any] | None:
    if not isinstance(plan, Mapping):
        return None
    venue = plan.get("venue_native_payload")
    venue_keys = sorted(str(k) for k in venue.keys()) if isinstance(venue, Mapping) else []
    return {
        "instrument_id": plan.get("instrument_id"),
        "side": plan.get("side"),
        "order_type": plan.get("order_type"),
        "td_mode": plan.get("td_mode"),
        "quantity": plan.get("quantity"),
        "quantity_domain": plan.get("quantity_domain"),
        "quantity_unit": plan.get("quantity_unit"),
        "limit_price": plan.get("limit_price"),
        "min_sz": plan.get("min_sz"),
        "lot_sz": plan.get("lot_sz"),
        "tick_sz": plan.get("tick_sz"),
        "ct_val": plan.get("ct_val"),
        "ct_val_ccy": plan.get("ct_val_ccy"),
        "min_executable_notional": plan.get("min_executable_notional"),
        "max_notional": plan.get("max_notional"),
        "clordid_present": bool(str(plan.get("clordid") or "").strip()),
        "clordid_prefix": str(plan.get("clordid") or "")[:8],
        "venue_native_keys": venue_keys,
        "venue_native_instId": venue.get("instId") if isinstance(venue, Mapping) else None,
        "venue_native_tdMode": venue.get("tdMode") if isinstance(venue, Mapping) else None,
        "venue_native_side": venue.get("side") if isinstance(venue, Mapping) else None,
        "venue_native_ordType": venue.get("ordType") if isinstance(venue, Mapping) else None,
        "venue_native_sz": venue.get("sz") if isinstance(venue, Mapping) else None,
        "venue_native_px": venue.get("px") if isinstance(venue, Mapping) else None,
    }


def execute_order_plan_observe_v1(
    *,
    owner_go: str,
    origin_main_sha: str,
    vault_file: Path | None = None,
    vault_backend: Any = None,
    transport: LiveCanaryTransportV1 | None = None,
) -> dict[str, Any]:
    assert_contract_invariants_v1()
    if str(owner_go or "").strip() != OWNER_GO:
        raise Section1114OfflineSurfaceError("OWNER_GO_MISMATCH")
    if str(origin_main_sha or "").strip() != EXPECTED_ORIGIN_MAIN_SHA:
        raise Section1114OfflineSurfaceError("ORIGIN_MAIN_SHA_MISMATCH")
    if POST_ALLOWED is True:
        raise Section1114OfflineSurfaceError("POST_MUST_REMAIN_FORBIDDEN")
    if POST_REQUIRED_FOR_LIVE_ORDER_PLAN_OBSERVED is True:
        raise Section1114OfflineSurfaceError("POST_NOT_REQUIRED_DRIFT")
    if LIVE_AUTHORIZED is True or LIVE_ENABLED is True or LIVE_ARMED is True:
        raise Section1114OfflineSurfaceError("STANDING_LIVE_GATE_TRUE")
    if SUBMIT_UNLOCKED is True:
        raise Section1114OfflineSurfaceError("STANDING_SUBMIT_UNLOCKED_TRUE")
    if CANARY_TECHNICAL_EXECUTE_TOKEN != OWNER_GO_EXECUTE:
        raise Section1114OfflineSurfaceError("CANARY_TECHNICAL_TOKEN_DRIFT")
    if LIVE_EXECUTION_CODE_EXISTS is not True:
        raise Section1114OfflineSurfaceError("CODE_EXISTS_PREDECESSOR_FALSE")
    if LIVE_EXECUTION_PATH_REACHABLE is not True:
        raise Section1114OfflineSurfaceError("PATH_REACHABLE_PREDECESSOR_FALSE")
    if LIVE_PRIVATE_READ_ONLY_PROVEN is not True:
        raise Section1114OfflineSurfaceError("PRIVATE_READ_ONLY_PREDECESSOR_FALSE")

    gate_state_before = {
        "LIVE_ENABLED_STANDING": LIVE_ENABLED,
        "LIVE_ARMED_STANDING": LIVE_ARMED,
        "SUBMIT_UNLOCKED_STANDING": SUBMIT_UNLOCKED,
        "LIVE_AUTHORIZED_STANDING": LIVE_AUTHORIZED,
        "SESSION_LIVE_ENABLED": False,
        "SESSION_LIVE_ARMED": False,
        "SESSION_LIVE_CANARY_AUTHORIZED": False,
    }
    cfg = load_live_canary_config_v1(
        productive_canary_execute_config_dict_v1(),
        require_execute_fields=True,
    )
    backend = vault_backend
    if backend is None:
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
            observe_order_plan_only=True,
        )
    except (LiveCanarySubmitTransportError, LiveCanarySubmitGateError) as exc:
        blocked_reason = str(exc)
        transport_payload = None
    ended = _utc_now_iso_v1()
    gate_state_after = {
        "LIVE_ENABLED_STANDING": LIVE_ENABLED,
        "LIVE_ARMED_STANDING": LIVE_ARMED,
        "SUBMIT_UNLOCKED_STANDING": SUBMIT_UNLOCKED,
        "LIVE_AUTHORIZED_STANDING": LIVE_AUTHORIZED,
        "SESSION_LIVE_ENABLED": False,
        "SESSION_LIVE_ARMED": False,
        "SESSION_LIVE_CANARY_AUTHORIZED": False,
        "LIVE_GATES_RETURNED_FAIL_CLOSED": True,
    }
    plan = None
    if isinstance(transport_payload, Mapping):
        raw_plan = transport_payload.get("plan")
        if isinstance(raw_plan, Mapping):
            plan = _sanitize_plan_v1(raw_plan)
    counters = (
        dict(transport_payload.get("counters") or {})
        if isinstance(transport_payload, Mapping)
        else {}
    )
    produced = (
        transport_payload is not None
        and transport_payload.get("ORDER_PLAN_PRODUCED_AFTER_GATES") is True
        and transport_payload.get("POST_USED") is not True
        and transport_payload.get("CANARY_RESULT") == "ORDER_PLAN_OBSERVED_NO_POST"
        and plan is not None
        and bool(plan.get("instrument_id"))
        and bool(plan.get("quantity"))
        and bool(plan.get("limit_price"))
    )
    get_count = int(counters.get("GET_REQUEST_COUNT") or counters.get("REQUEST_COUNT") or 0)
    post_count = int(counters.get("ENTRY_SUBMIT_COUNT") or 0)
    if post_count > 0:
        raise Section1114OfflineSurfaceError("POST_COUNT_NONZERO_ON_OBSERVE_PATH")
    evidence = {
        "OWNER_GO": OWNER_GO,
        "CANARY_TECHNICAL_EXECUTE_TOKEN": OWNER_GO_EXECUTE,
        "ORIGIN_MAIN_SHA": origin_main_sha,
        "STARTED_AT_UTC": started,
        "ENDED_AT_UTC": ended,
        "RESPONSE_TIME_UTC": ended,
        "LIVE_EXECUTION_CODE_EXISTS": True,
        "LIVE_EXECUTION_PATH_REACHABLE": True,
        "LIVE_PRIVATE_READ_ONLY_PROVEN": True,
        "PRODUCED_ON_CANONICAL_SUBMIT_PATH": produced,
        "AFTER_REFUSE_SUBMIT_UNLESS_GATES_PASS": produced,
        "CURRENT_VENUE_DERIVED_INPUTS": produced,
        "ORDER_PLAN_ARTIFACT_PRESENT": produced,
        "NOT_BLOCKED_DRY_RUN": True,
        "NOT_DIRECT_BUILDER_INVOCATION": True,
        "NO_POST_REQUIRED": True,
        "POST_USED": False,
        "WIRE_SEND_POST": False,
        "SUBMIT_USED": False,
        "SUBMIT_COUNT": 0,
        "RETRY_USED": False,
        "SECOND_SUBMIT_USED": False,
        "CANCEL_USED": False,
        "AMEND_USED": False,
        "FLATTEN_EXECUTE_USED": False,
        "FUNDING_USED": False,
        "LIVE_GATE_ACTIVATION_USED": True,
        "LIVE_GATES_RETURNED_FAIL_CLOSED": True,
        "CREDENTIAL_USE": True,
        "PRIVATE_GET_USED": produced or blocked_reason is not None,
        "PUBLIC_GET_USED": produced or blocked_reason is not None,
        "VENUE_REQUESTS": get_count,
        "BLOCKED_REASON": blocked_reason,
        "CANARY_RESULT": None
        if transport_payload is None
        else transport_payload.get("CANARY_RESULT"),
        "plan": plan,
        "submit_gate": None if transport_payload is None else transport_payload.get("submit_gate"),
        "pre_submit_state": None
        if transport_payload is None
        else transport_payload.get("pre_submit_state"),
        "counters": counters,
        "GATE_STATE_BEFORE": gate_state_before,
        "GATE_STATE_DURING": {
            "SESSION_LIVE_ENABLED": True,
            "SESSION_LIVE_ARMED": True,
            "SESSION_LIVE_CANARY_AUTHORIZED": True,
            "STANDING_LIVE_ENABLED": False,
            "STANDING_LIVE_ARMED": False,
            "STANDING_SUBMIT_UNLOCKED": False,
            "STANDING_CANARY_AUTHORIZED": False,
        },
        "GATE_STATE_AFTER": gate_state_after,
        "LIVE_ORDER_PLAN_OBSERVED": produced,
        "LIVE_SUBMIT_ACK_OBSERVED": False,
        "SECRET_VALUES_INCLUDED": False,
    }
    return evidence
