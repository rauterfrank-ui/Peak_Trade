"""Live dry-run order-plan contracts (§11.19 Cap 11.8 / §11.13 LIVE_DRY_RUN_ORDER_PLAN).

Fixture-only. Stops before SUBMIT_PENDING. No network submit.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Any, Mapping

from src.ops.capability_11_8_live_dry_run_order_plan_parity_v1.constants_v1 import (
    CONTRACT_VERSION,
    LIVE_DRY_RUN_ALLOWED_EXECUTION_MODE,
    LIVE_DRY_RUN_FORBIDDEN_LIFECYCLE_STATES,
    LIVE_DRY_RUN_LIFECYCLE_STATES,
    LIVE_DRY_RUN_NETWORK_EFFECT,
    LIVE_DRY_RUN_ORDER_PLAN_ACTIVATED,
    LIVE_DRY_RUN_ORDER_PLAN_CONTRACT_ACTIVATED,
    LIVE_DRY_RUN_ORDER_PLAN_CONTRACT_BOUND,
    LIVE_DRY_RUN_ORDER_PLAN_OWNER,
    LIVE_DRY_RUN_REQUIRED_FIELDS,
    LIVE_ORDER_SUBMIT_PERFORMED_IN_CAPABILITY_11_8,
    LIVE_PROGRESSION_STAGES_FORBIDDEN,
    LIVE_PROGRESSION_STAGES_IN_SCOPE,
    OWNER,
)


class LiveDryRunOrderPlanError(RuntimeError):
    """Fail-closed Live dry-run order-plan violation."""


def _canonical_dumps(payload: Mapping[str, Any]) -> str:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


@dataclass(frozen=True)
class LiveDryRunOrderPlanRecordV1:
    """Fixture-only Live dry-run order-plan record (pre-submit only)."""

    stage: str
    intent_id: str
    order_plan_id: str
    client_order_id: str
    instrument_id: str
    side: str
    order_type: str
    quantity: str
    execution_mode: str
    lifecycle_state: str
    canonical_order_plan_digest: str
    venue_native_dry_run_payload: dict[str, Any]
    dry_run_serialization_digest: str
    source: str = "FIXTURE_ONLY"
    network_effect: str = "NONE"
    submitted: bool = False
    contract_version: str = CONTRACT_VERSION
    owner: str = LIVE_DRY_RUN_ORDER_PLAN_OWNER


def build_live_dry_run_order_plan_record_v1(
    *,
    stage: str = "LIVE_DRY_RUN_ORDER_PLAN",
    intent_id: str,
    order_plan_id: str,
    client_order_id: str,
    instrument_id: str,
    side: str,
    order_type: str,
    quantity: str,
    lifecycle_state: str = "PRE_SUBMIT_VALIDATED",
    execution_mode: str = LIVE_DRY_RUN_ALLOWED_EXECUTION_MODE,
    source: str = "FIXTURE_ONLY",
) -> LiveDryRunOrderPlanRecordV1:
    if stage in LIVE_PROGRESSION_STAGES_FORBIDDEN:
        raise LiveDryRunOrderPlanError(
            f"CAPABILITY_11_9_SURFACE_FORBIDDEN_IN_CAPABILITY_11_8:{stage}"
        )
    if stage not in LIVE_PROGRESSION_STAGES_IN_SCOPE:
        raise LiveDryRunOrderPlanError(f"UNKNOWN_LIVE_DRY_RUN_STAGE:{stage}")
    if source != "FIXTURE_ONLY":
        raise LiveDryRunOrderPlanError(
            f"NON_FIXTURE_LIVE_DRY_RUN_SOURCE_FORBIDDEN_IN_CAPABILITY_11_8:{source}"
        )
    if execution_mode != LIVE_DRY_RUN_ALLOWED_EXECUTION_MODE:
        raise LiveDryRunOrderPlanError(f"LIVE_DRY_RUN_EXECUTION_MODE_FORBIDDEN:{execution_mode}")
    if lifecycle_state in LIVE_DRY_RUN_FORBIDDEN_LIFECYCLE_STATES:
        raise LiveDryRunOrderPlanError(f"LIVE_DRY_RUN_SUBMIT_LIFECYCLE_FORBIDDEN:{lifecycle_state}")
    if lifecycle_state not in LIVE_DRY_RUN_LIFECYCLE_STATES:
        raise LiveDryRunOrderPlanError(f"UNKNOWN_LIVE_DRY_RUN_LIFECYCLE_STATE:{lifecycle_state}")

    fields = {
        "intent_id": intent_id,
        "order_plan_id": order_plan_id,
        "client_order_id": client_order_id,
        "instrument_id": instrument_id,
        "side": side,
        "order_type": order_type,
        "quantity": quantity,
        "execution_mode": execution_mode,
    }
    for key in LIVE_DRY_RUN_REQUIRED_FIELDS:
        if not fields.get(key):
            raise LiveDryRunOrderPlanError(f"LIVE_DRY_RUN_ORDER_PLAN_FIELD_MISSING:{key}")

    canonical_payload = {
        "intent_id": intent_id,
        "order_plan_id": order_plan_id,
        "client_order_id": client_order_id,
        "instrument_id": instrument_id,
        "side": side,
        "order_type": order_type,
        "quantity": quantity,
        "execution_mode": execution_mode,
        "lifecycle_state": lifecycle_state,
        "stage": stage,
    }
    venue_native_dry_run_payload = {
        "clOrdId": client_order_id,
        "instId": instrument_id,
        "side": side.lower(),
        "ordType": order_type.lower(),
        "sz": quantity,
        "tdMode": "cross",
        "dry_run": True,
        "submit": False,
    }
    return LiveDryRunOrderPlanRecordV1(
        stage=stage,
        intent_id=intent_id,
        order_plan_id=order_plan_id,
        client_order_id=client_order_id,
        instrument_id=instrument_id,
        side=side,
        order_type=order_type,
        quantity=quantity,
        execution_mode=execution_mode,
        lifecycle_state=lifecycle_state,
        canonical_order_plan_digest=hashlib.sha256(
            _canonical_dumps(canonical_payload).encode("utf-8")
        ).hexdigest(),
        venue_native_dry_run_payload=venue_native_dry_run_payload,
        dry_run_serialization_digest=hashlib.sha256(
            _canonical_dumps(venue_native_dry_run_payload).encode("utf-8")
        ).hexdigest(),
        source=source,
        network_effect=LIVE_DRY_RUN_NETWORK_EFFECT,
        submitted=False,
    )


def refuse_live_dry_run_order_plan_activation_v1(*, claimed_action: str) -> dict[str, Any]:
    raise LiveDryRunOrderPlanError(
        f"LIVE_DRY_RUN_ORDER_PLAN_ACTIVATION_FORBIDDEN_IN_CAPABILITY_11_8:{claimed_action}"
    )


def refuse_live_dry_run_order_submit_v1(*, client_order_id: str) -> dict[str, Any]:
    raise LiveDryRunOrderPlanError(
        f"LIVE_DRY_RUN_ORDER_SUBMIT_FORBIDDEN_IN_CAPABILITY_11_8:{client_order_id}"
    )


def refuse_live_dry_run_network_session_v1(*, session_id: str) -> dict[str, Any]:
    raise LiveDryRunOrderPlanError(
        f"LIVE_DRY_RUN_NETWORK_SESSION_FORBIDDEN_IN_CAPABILITY_11_8:{session_id}"
    )


def refuse_live_dry_run_credential_access_v1(*, claimed_action: str) -> dict[str, Any]:
    raise LiveDryRunOrderPlanError(
        f"LIVE_DRY_RUN_CREDENTIAL_ACCESS_FORBIDDEN_IN_CAPABILITY_11_8:{claimed_action}"
    )


def refuse_cap_11_9_live_canary_v1(*, claimed_surface: str) -> dict[str, Any]:
    raise LiveDryRunOrderPlanError(
        f"CAPABILITY_11_9_SURFACE_FORBIDDEN_IN_CAPABILITY_11_8:{claimed_surface}"
    )


def prove_live_dry_run_order_plan_contract_v1() -> dict[str, Any]:
    record = build_live_dry_run_order_plan_record_v1(
        intent_id="intent-dryrun-demo",
        order_plan_id="plan-dryrun-demo",
        client_order_id="pt-coid-live-dryrun-demo",
        instrument_id="BTC-USDT-SWAP",
        side="BUY",
        order_type="LIMIT",
        quantity="1",
    )

    non_fixture_blocked = False
    try:
        build_live_dry_run_order_plan_record_v1(
            intent_id="intent-bad",
            order_plan_id="plan-bad",
            client_order_id="pt-coid-bad",
            instrument_id="BTC-USDT-SWAP",
            side="BUY",
            order_type="LIMIT",
            quantity="1",
            source="LIVE_NETWORK",
        )
    except LiveDryRunOrderPlanError as exc:
        non_fixture_blocked = "NON_FIXTURE" in str(exc)

    live_submit_mode_blocked = False
    try:
        build_live_dry_run_order_plan_record_v1(
            intent_id="intent-live",
            order_plan_id="plan-live",
            client_order_id="pt-coid-live",
            instrument_id="BTC-USDT-SWAP",
            side="BUY",
            order_type="LIMIT",
            quantity="1",
            execution_mode="LIVE",
        )
    except LiveDryRunOrderPlanError as exc:
        live_submit_mode_blocked = "EXECUTION_MODE_FORBIDDEN" in str(exc)

    submit_lifecycle_blocked = False
    try:
        build_live_dry_run_order_plan_record_v1(
            intent_id="intent-submit",
            order_plan_id="plan-submit",
            client_order_id="pt-coid-submit",
            instrument_id="BTC-USDT-SWAP",
            side="BUY",
            order_type="LIMIT",
            quantity="1",
            lifecycle_state="SUBMIT_PENDING",
        )
    except LiveDryRunOrderPlanError as exc:
        submit_lifecycle_blocked = "SUBMIT_LIFECYCLE_FORBIDDEN" in str(exc)

    canary_stage_blocked = False
    try:
        build_live_dry_run_order_plan_record_v1(
            stage="LIVE_CANARY_MINIMUM_EXPOSURE",
            intent_id="intent-canary",
            order_plan_id="plan-canary",
            client_order_id="pt-coid-canary",
            instrument_id="BTC-USDT-SWAP",
            side="BUY",
            order_type="LIMIT",
            quantity="1",
        )
    except LiveDryRunOrderPlanError as exc:
        canary_stage_blocked = "CAPABILITY_11_9_SURFACE_FORBIDDEN" in str(exc)

    activation_blocked = False
    try:
        refuse_live_dry_run_order_plan_activation_v1(claimed_action="activate_dry_run")
    except LiveDryRunOrderPlanError as exc:
        activation_blocked = "ACTIVATION_FORBIDDEN" in str(exc)

    submit_blocked = False
    try:
        refuse_live_dry_run_order_submit_v1(client_order_id=record.client_order_id)
    except LiveDryRunOrderPlanError as exc:
        submit_blocked = "ORDER_SUBMIT_FORBIDDEN" in str(exc)

    session_blocked = False
    try:
        refuse_live_dry_run_network_session_v1(session_id="live-dryrun-session")
    except LiveDryRunOrderPlanError as exc:
        session_blocked = "NETWORK_SESSION_FORBIDDEN" in str(exc)

    credential_blocked = False
    try:
        refuse_live_dry_run_credential_access_v1(claimed_action="load_api_key")
    except LiveDryRunOrderPlanError as exc:
        credential_blocked = "CREDENTIAL_ACCESS_FORBIDDEN" in str(exc)

    canary_blocked = False
    try:
        refuse_cap_11_9_live_canary_v1(claimed_surface="LIVE_CANARY_MINIMUM_EXPOSURE")
    except LiveDryRunOrderPlanError as exc:
        canary_blocked = "CAPABILITY_11_9_SURFACE_FORBIDDEN" in str(exc)

    ok = all(
        [
            record.source == "FIXTURE_ONLY",
            record.submitted is False,
            record.network_effect == "NONE",
            record.venue_native_dry_run_payload.get("dry_run") is True,
            record.venue_native_dry_run_payload.get("submit") is False,
            bool(record.canonical_order_plan_digest),
            bool(record.dry_run_serialization_digest),
            non_fixture_blocked,
            live_submit_mode_blocked,
            submit_lifecycle_blocked,
            canary_stage_blocked,
            activation_blocked,
            submit_blocked,
            session_blocked,
            credential_blocked,
            canary_blocked,
            LIVE_DRY_RUN_ORDER_PLAN_CONTRACT_BOUND is True,
            LIVE_DRY_RUN_ORDER_PLAN_CONTRACT_ACTIVATED is False,
            LIVE_DRY_RUN_ORDER_PLAN_ACTIVATED is False,
            LIVE_ORDER_SUBMIT_PERFORMED_IN_CAPABILITY_11_8 is False,
            record.owner == OWNER,
        ]
    )
    return {
        "ok": ok,
        "LIVE_DRY_RUN_ORDER_PLAN_CONTRACT_BOUND": True,
        "LIVE_DRY_RUN_ORDER_PLAN_CONTRACT_ACTIVATED": False,
        "LIVE_DRY_RUN_ORDER_PLAN_ACTIVATED": False,
        "LIVE_DRY_RUN_NETWORK_EFFECT": "NONE",
        "LIVE_ORDER_SUBMIT_PERFORMED_IN_CAPABILITY_11_8": False,
        "stages_in_scope": list(LIVE_PROGRESSION_STAGES_IN_SCOPE),
        "stages_forbidden": list(LIVE_PROGRESSION_STAGES_FORBIDDEN),
        "lifecycle_states": list(LIVE_DRY_RUN_LIFECYCLE_STATES),
        "forbidden_lifecycle_states": list(LIVE_DRY_RUN_FORBIDDEN_LIFECYCLE_STATES),
        "non_fixture_blocked": non_fixture_blocked,
        "live_submit_mode_blocked": live_submit_mode_blocked,
        "submit_lifecycle_blocked": submit_lifecycle_blocked,
        "canary_stage_blocked": canary_stage_blocked,
        "activation_blocked": activation_blocked,
        "submit_blocked": submit_blocked,
        "network_session_blocked": session_blocked,
        "credential_access_blocked": credential_blocked,
        "cap_11_9_surface_blocked": canary_blocked,
        "sample_canonical_digest": record.canonical_order_plan_digest,
        "sample_dry_run_digest": record.dry_run_serialization_digest,
        "OWNER": LIVE_DRY_RUN_ORDER_PLAN_OWNER,
    }
