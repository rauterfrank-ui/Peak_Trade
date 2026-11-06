"""Live canary minimum-exposure contracts (§11.19 Cap 11.9 / §11.13).

Fixture-only. No Live canary activation, network, or order submit.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from src.ops.capability_11_9_live_canary_order_execution_v1.constants_v1 import (
    AUTOMATIC_HALT_ALLOWED,
    AUTOMATIC_STAGE_DEMOTION_ALLOWED,
    CANARY_ROLLBACK_CONTRACT_REQUIRED,
    CONTRACT_VERSION,
    LIVE_CANARY_MINIMUM_EXPOSURE_ACTIVATED,
    LIVE_CANARY_MINIMUM_EXPOSURE_CONTRACT_ACTIVATED,
    LIVE_CANARY_MINIMUM_EXPOSURE_CONTRACT_BOUND,
    LIVE_CANARY_MINIMUM_EXPOSURE_OWNER,
    LIVE_PROGRESSION_STAGES_FORBIDDEN,
    LIVE_PROGRESSION_STAGES_IN_SCOPE,
    MINIMUM_RATIFIED_NOTIONAL_ONLY,
    NO_AUTOMATIC_STAGE_PROMOTION,
    OWNER,
    OWNER_GO_REQUIRED_FOR_STAGE_PROMOTION,
    POSITION_COUNT_LIMIT,
)


class LiveCanaryMinimumExposureError(RuntimeError):
    """Fail-closed Live canary minimum-exposure violation."""


@dataclass(frozen=True)
class LiveCanaryMinimumExposureRecordV1:
    """Fixture-only Live canary minimum-exposure bound record."""

    stage: str
    max_notional: str
    position_count_limit: int
    order_count_limit: int
    duration_bound_seconds: int
    loss_budget: str
    rollback_contract_id: str
    minimum_ratified_notional_only: bool
    source: str = "FIXTURE_ONLY"
    network_effect: str = "NONE"
    activated: bool = False
    contract_version: str = CONTRACT_VERSION
    owner: str = LIVE_CANARY_MINIMUM_EXPOSURE_OWNER


def build_live_canary_minimum_exposure_record_v1(
    *,
    stage: str = "LIVE_CANARY_MINIMUM_EXPOSURE",
    max_notional: str = "1",
    position_count_limit: int = POSITION_COUNT_LIMIT,
    order_count_limit: int = 1,
    duration_bound_seconds: int = 3600,
    loss_budget: str = "0",
    rollback_contract_id: str = "canary-rollback-fixture-v1",
    source: str = "FIXTURE_ONLY",
) -> LiveCanaryMinimumExposureRecordV1:
    if stage in LIVE_PROGRESSION_STAGES_FORBIDDEN:
        raise LiveCanaryMinimumExposureError(
            f"CAPABILITY_11_10_SURFACE_FORBIDDEN_IN_CAPABILITY_11_9:{stage}"
        )
    if stage not in LIVE_PROGRESSION_STAGES_IN_SCOPE:
        raise LiveCanaryMinimumExposureError(f"UNKNOWN_LIVE_CANARY_STAGE:{stage}")
    if source != "FIXTURE_ONLY":
        raise LiveCanaryMinimumExposureError(
            f"NON_FIXTURE_LIVE_CANARY_SOURCE_FORBIDDEN_IN_CAPABILITY_11_9:{source}"
        )
    if position_count_limit != POSITION_COUNT_LIMIT:
        raise LiveCanaryMinimumExposureError(
            f"LIVE_CANARY_POSITION_COUNT_LIMIT_FORBIDDEN:{position_count_limit}"
        )
    if not max_notional or max_notional == "0":
        raise LiveCanaryMinimumExposureError("LIVE_CANARY_MAX_NOTIONAL_INVALID")
    if not rollback_contract_id:
        raise LiveCanaryMinimumExposureError("LIVE_CANARY_ROLLBACK_CONTRACT_REQUIRED")
    if order_count_limit < 1:
        raise LiveCanaryMinimumExposureError("LIVE_CANARY_ORDER_COUNT_LIMIT_INVALID")
    if duration_bound_seconds < 1:
        raise LiveCanaryMinimumExposureError("LIVE_CANARY_DURATION_BOUND_INVALID")

    return LiveCanaryMinimumExposureRecordV1(
        stage=stage,
        max_notional=max_notional,
        position_count_limit=position_count_limit,
        order_count_limit=order_count_limit,
        duration_bound_seconds=duration_bound_seconds,
        loss_budget=loss_budget,
        rollback_contract_id=rollback_contract_id,
        minimum_ratified_notional_only=MINIMUM_RATIFIED_NOTIONAL_ONLY,
        source=source,
        network_effect="NONE",
        activated=False,
    )


def refuse_live_canary_minimum_exposure_activation_v1(*, claimed_action: str) -> dict[str, Any]:
    raise LiveCanaryMinimumExposureError(
        f"LIVE_CANARY_MINIMUM_EXPOSURE_ACTIVATION_FORBIDDEN_IN_CAPABILITY_11_9:{claimed_action}"
    )


def refuse_automatic_stage_promotion_v1(*, claimed_target_stage: str) -> dict[str, Any]:
    raise LiveCanaryMinimumExposureError(
        f"AUTOMATIC_STAGE_PROMOTION_FORBIDDEN_IN_CAPABILITY_11_9:{claimed_target_stage}"
    )


def refuse_cap_11_10_live_bounded_v1(*, claimed_surface: str) -> dict[str, Any]:
    raise LiveCanaryMinimumExposureError(
        f"CAPABILITY_11_10_SURFACE_FORBIDDEN_IN_CAPABILITY_11_9:{claimed_surface}"
    )


def prove_live_canary_minimum_exposure_contract_v1() -> dict[str, Any]:
    record = build_live_canary_minimum_exposure_record_v1()

    non_fixture_blocked = False
    try:
        build_live_canary_minimum_exposure_record_v1(source="LIVE_NETWORK")
    except LiveCanaryMinimumExposureError as exc:
        non_fixture_blocked = "NON_FIXTURE" in str(exc)

    bounded_stage_blocked = False
    try:
        build_live_canary_minimum_exposure_record_v1(stage="LIVE_BOUNDED_SINGLE_FUTURE")
    except LiveCanaryMinimumExposureError as exc:
        bounded_stage_blocked = "CAPABILITY_11_10_SURFACE_FORBIDDEN" in str(exc)

    position_limit_blocked = False
    try:
        build_live_canary_minimum_exposure_record_v1(position_count_limit=2)
    except LiveCanaryMinimumExposureError as exc:
        position_limit_blocked = "POSITION_COUNT_LIMIT_FORBIDDEN" in str(exc)

    activation_blocked = False
    try:
        refuse_live_canary_minimum_exposure_activation_v1(claimed_action="activate_canary")
    except LiveCanaryMinimumExposureError as exc:
        activation_blocked = "ACTIVATION_FORBIDDEN" in str(exc)

    promotion_blocked = False
    try:
        refuse_automatic_stage_promotion_v1(claimed_target_stage="LIVE_BOUNDED_SINGLE_FUTURE")
    except LiveCanaryMinimumExposureError as exc:
        promotion_blocked = "AUTOMATIC_STAGE_PROMOTION_FORBIDDEN" in str(exc)

    cap_11_10_blocked = False
    try:
        refuse_cap_11_10_live_bounded_v1(claimed_surface="LIVE_BOUNDED_SINGLE_FUTURE")
    except LiveCanaryMinimumExposureError as exc:
        cap_11_10_blocked = "CAPABILITY_11_10_SURFACE_FORBIDDEN" in str(exc)

    ok = all(
        [
            record.source == "FIXTURE_ONLY",
            record.activated is False,
            record.network_effect == "NONE",
            record.stage == "LIVE_CANARY_MINIMUM_EXPOSURE",
            record.position_count_limit == 1,
            record.minimum_ratified_notional_only is True,
            non_fixture_blocked,
            bounded_stage_blocked,
            position_limit_blocked,
            activation_blocked,
            promotion_blocked,
            cap_11_10_blocked,
            LIVE_CANARY_MINIMUM_EXPOSURE_CONTRACT_BOUND is True,
            LIVE_CANARY_MINIMUM_EXPOSURE_CONTRACT_ACTIVATED is False,
            LIVE_CANARY_MINIMUM_EXPOSURE_ACTIVATED is False,
            MINIMUM_RATIFIED_NOTIONAL_ONLY is True,
            NO_AUTOMATIC_STAGE_PROMOTION is True,
            OWNER_GO_REQUIRED_FOR_STAGE_PROMOTION is True,
            AUTOMATIC_STAGE_DEMOTION_ALLOWED is True,
            AUTOMATIC_HALT_ALLOWED is True,
            CANARY_ROLLBACK_CONTRACT_REQUIRED is True,
            record.owner == OWNER,
        ]
    )
    return {
        "ok": ok,
        "LIVE_CANARY_MINIMUM_EXPOSURE_CONTRACT_BOUND": True,
        "LIVE_CANARY_MINIMUM_EXPOSURE_CONTRACT_ACTIVATED": False,
        "LIVE_CANARY_MINIMUM_EXPOSURE_ACTIVATED": False,
        "MINIMUM_RATIFIED_NOTIONAL_ONLY": True,
        "POSITION_COUNT_LIMIT": POSITION_COUNT_LIMIT,
        "NO_AUTOMATIC_STAGE_PROMOTION": True,
        "OWNER_GO_REQUIRED_FOR_STAGE_PROMOTION": True,
        "AUTOMATIC_STAGE_DEMOTION_ALLOWED": True,
        "AUTOMATIC_HALT_ALLOWED": True,
        "CANARY_ROLLBACK_CONTRACT_REQUIRED": True,
        "stages_in_scope": list(LIVE_PROGRESSION_STAGES_IN_SCOPE),
        "stages_forbidden": list(LIVE_PROGRESSION_STAGES_FORBIDDEN),
        "non_fixture_blocked": non_fixture_blocked,
        "bounded_stage_blocked": bounded_stage_blocked,
        "position_limit_blocked": position_limit_blocked,
        "activation_blocked": activation_blocked,
        "automatic_promotion_blocked": promotion_blocked,
        "cap_11_10_surface_blocked": cap_11_10_blocked,
        "sample_max_notional": record.max_notional,
        "sample_rollback_contract_id": record.rollback_contract_id,
        "OWNER": LIVE_CANARY_MINIMUM_EXPOSURE_OWNER,
    }
