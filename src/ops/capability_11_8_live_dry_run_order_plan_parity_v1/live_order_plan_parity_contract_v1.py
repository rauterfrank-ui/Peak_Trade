"""Live order-plan parity contracts (§11.19 Cap 11.8) — fixture parity, no submit."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from src.ops.capability_11_8_live_dry_run_order_plan_parity_v1.constants_v1 import (
    CONTRACT_VERSION,
    LIVE_ORDER_PLAN_PARITY_ACTIVATED,
    LIVE_ORDER_PLAN_PARITY_CONTRACT_ACTIVATED,
    LIVE_ORDER_PLAN_PARITY_CONTRACT_BOUND,
    LIVE_ORDER_PLAN_PARITY_OWNER,
    NO_AUTOMATIC_STAGE_PROMOTION,
    OWNER,
    OWNER_GO_REQUIRED_FOR_STAGE_PROMOTION,
)
from src.ops.capability_11_8_live_dry_run_order_plan_parity_v1.live_dry_run_order_plan_contract_v1 import (
    LiveDryRunOrderPlanRecordV1,
    build_live_dry_run_order_plan_record_v1,
)


class LiveOrderPlanParityError(RuntimeError):
    """Fail-closed Live order-plan parity violation."""


@dataclass(frozen=True)
class LiveOrderPlanParityRecordV1:
    order_plan_id: str
    client_order_id: str
    canonical_order_plan_digest: str
    dry_run_serialization_digest: str
    parity_pass: bool
    divergence_reason: str | None
    submitted: bool = False
    network_effect: str = "NONE"
    source: str = "FIXTURE_ONLY"
    contract_version: str = CONTRACT_VERSION
    owner: str = LIVE_ORDER_PLAN_PARITY_OWNER


def build_live_order_plan_parity_record_v1(
    *,
    plan: LiveDryRunOrderPlanRecordV1,
    expected_canonical_digest: str | None = None,
    expected_dry_run_digest: str | None = None,
) -> LiveOrderPlanParityRecordV1:
    if plan.source != "FIXTURE_ONLY":
        raise LiveOrderPlanParityError(
            f"NON_FIXTURE_PARITY_SOURCE_FORBIDDEN_IN_CAPABILITY_11_8:{plan.source}"
        )
    if plan.submitted is True:
        raise LiveOrderPlanParityError(
            f"SUBMITTED_PLAN_PARITY_FORBIDDEN_IN_CAPABILITY_11_8:{plan.client_order_id}"
        )
    if plan.execution_mode != "LIVE_DRY_RUN":
        raise LiveOrderPlanParityError(f"PARITY_EXECUTION_MODE_FORBIDDEN:{plan.execution_mode}")

    expected_canonical = expected_canonical_digest or plan.canonical_order_plan_digest
    expected_dry_run = expected_dry_run_digest or plan.dry_run_serialization_digest
    canonical_match = plan.canonical_order_plan_digest == expected_canonical
    dry_run_match = plan.dry_run_serialization_digest == expected_dry_run
    payload_flags_ok = (
        plan.venue_native_dry_run_payload.get("dry_run") is True
        and plan.venue_native_dry_run_payload.get("submit") is False
    )
    parity_pass = canonical_match and dry_run_match and payload_flags_ok and not plan.submitted
    divergence_reason = None
    if not parity_pass:
        if not canonical_match:
            divergence_reason = "CANONICAL_ORDER_PLAN_DIGEST_MISMATCH"
        elif not dry_run_match:
            divergence_reason = "DRY_RUN_SERIALIZATION_DIGEST_MISMATCH"
        elif not payload_flags_ok:
            divergence_reason = "DRY_RUN_PAYLOAD_FLAGS_INVALID"
        else:
            divergence_reason = "PARITY_FAILED"
    return LiveOrderPlanParityRecordV1(
        order_plan_id=plan.order_plan_id,
        client_order_id=plan.client_order_id,
        canonical_order_plan_digest=plan.canonical_order_plan_digest,
        dry_run_serialization_digest=plan.dry_run_serialization_digest,
        parity_pass=parity_pass,
        divergence_reason=divergence_reason,
        submitted=False,
    )


def refuse_live_order_plan_parity_activation_v1(*, claimed_action: str) -> dict[str, Any]:
    raise LiveOrderPlanParityError(
        f"LIVE_ORDER_PLAN_PARITY_ACTIVATION_FORBIDDEN_IN_CAPABILITY_11_8:{claimed_action}"
    )


def refuse_automatic_stage_promotion_v1(*, claimed_target_stage: str) -> dict[str, Any]:
    raise LiveOrderPlanParityError(
        f"AUTOMATIC_STAGE_PROMOTION_FORBIDDEN_IN_CAPABILITY_11_8:{claimed_target_stage}"
    )


def prove_live_order_plan_parity_contract_v1() -> dict[str, Any]:
    plan = build_live_dry_run_order_plan_record_v1(
        intent_id="intent-parity-demo",
        order_plan_id="plan-parity-demo",
        client_order_id="pt-coid-parity-demo",
        instrument_id="BTC-USDT-SWAP",
        side="BUY",
        order_type="LIMIT",
        quantity="1",
    )
    match_record = build_live_order_plan_parity_record_v1(plan=plan)

    mismatch = build_live_order_plan_parity_record_v1(
        plan=plan,
        expected_canonical_digest="0" * 64,
    )

    activation_blocked = False
    try:
        refuse_live_order_plan_parity_activation_v1(claimed_action="activate_parity")
    except LiveOrderPlanParityError as exc:
        activation_blocked = "ACTIVATION_FORBIDDEN" in str(exc)

    promotion_blocked = False
    try:
        refuse_automatic_stage_promotion_v1(claimed_target_stage="LIVE_CANARY_MINIMUM_EXPOSURE")
    except LiveOrderPlanParityError as exc:
        promotion_blocked = "AUTOMATIC_STAGE_PROMOTION_FORBIDDEN" in str(exc)

    ok = all(
        [
            match_record.parity_pass is True,
            match_record.divergence_reason is None,
            match_record.submitted is False,
            match_record.network_effect == "NONE",
            match_record.source == "FIXTURE_ONLY",
            mismatch.parity_pass is False,
            mismatch.divergence_reason == "CANONICAL_ORDER_PLAN_DIGEST_MISMATCH",
            activation_blocked,
            promotion_blocked,
            LIVE_ORDER_PLAN_PARITY_CONTRACT_BOUND is True,
            LIVE_ORDER_PLAN_PARITY_CONTRACT_ACTIVATED is False,
            LIVE_ORDER_PLAN_PARITY_ACTIVATED is False,
            NO_AUTOMATIC_STAGE_PROMOTION is True,
            OWNER_GO_REQUIRED_FOR_STAGE_PROMOTION is True,
            match_record.owner == OWNER,
        ]
    )
    return {
        "ok": ok,
        "LIVE_ORDER_PLAN_PARITY_CONTRACT_BOUND": True,
        "LIVE_ORDER_PLAN_PARITY_CONTRACT_ACTIVATED": False,
        "LIVE_ORDER_PLAN_PARITY_ACTIVATED": False,
        "NO_AUTOMATIC_STAGE_PROMOTION": True,
        "OWNER_GO_REQUIRED_FOR_STAGE_PROMOTION": True,
        "parity_pass_sample": match_record.parity_pass,
        "parity_mismatch_reason": mismatch.divergence_reason,
        "activation_blocked": activation_blocked,
        "automatic_promotion_blocked": promotion_blocked,
        "OWNER": LIVE_ORDER_PLAN_PARITY_OWNER,
    }
