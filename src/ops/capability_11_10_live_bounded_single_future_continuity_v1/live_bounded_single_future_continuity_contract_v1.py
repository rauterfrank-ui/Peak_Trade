"""Live bounded single-future continuity contracts (§11.19 Cap 11.10 / §11.13).

Fixture-only. No Live bounded activation, network, or order submit.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from src.ops.capability_11_10_live_bounded_single_future_continuity_v1.constants_v1 import (
    AUTOMATIC_HALT_ALLOWED,
    AUTOMATIC_STAGE_DEMOTION_ALLOWED,
    BOUNDED_CONTINUITY_ROLLBACK_CONTRACT_REQUIRED,
    CONTRACT_VERSION,
    LIVE_BOUNDED_SINGLE_FUTURE_ACTIVATED,
    LIVE_BOUNDED_SINGLE_FUTURE_CONTINUITY_ACTIVATED,
    LIVE_BOUNDED_SINGLE_FUTURE_CONTINUITY_CONTRACT_ACTIVATED,
    LIVE_BOUNDED_SINGLE_FUTURE_CONTINUITY_CONTRACT_BOUND,
    LIVE_BOUNDED_SINGLE_FUTURE_CONTINUITY_OWNER,
    LIVE_PROGRESSION_STAGES_FORBIDDEN,
    LIVE_PROGRESSION_STAGES_IN_SCOPE,
    MINIMUM_RATIFIED_NOTIONAL_ONLY,
    NO_AUTOMATIC_STAGE_PROMOTION,
    OWNER,
    OWNER_GO_REQUIRED_FOR_STAGE_PROMOTION,
    POSITION_COUNT_LIMIT,
    SINGLE_FUTURE_ONLY,
)


class LiveBoundedSingleFutureContinuityError(RuntimeError):
    """Fail-closed Live bounded single-future continuity violation."""


@dataclass(frozen=True)
class LiveBoundedSingleFutureContinuityRecordV1:
    """Fixture-only Live bounded single-future continuity bound record."""

    stage: str
    continuity_session_id: str
    instrument_id: str
    max_notional: str
    position_count_limit: int
    order_count_limit: int
    duration_bound_seconds: int
    loss_budget: str
    rollback_contract_id: str
    minimum_ratified_notional_only: bool
    single_future_only: bool
    source: str = "FIXTURE_ONLY"
    network_effect: str = "NONE"
    activated: bool = False
    contract_version: str = CONTRACT_VERSION
    owner: str = LIVE_BOUNDED_SINGLE_FUTURE_CONTINUITY_OWNER


def build_live_bounded_single_future_continuity_record_v1(
    *,
    stage: str = "LIVE_BOUNDED_SINGLE_FUTURE",
    continuity_session_id: str = "bounded-continuity-fixture-v1",
    instrument_id: str = "BTC-USDT-SWAP",
    max_notional: str = "1",
    position_count_limit: int = POSITION_COUNT_LIMIT,
    order_count_limit: int = 1,
    duration_bound_seconds: int = 86400,
    loss_budget: str = "0",
    rollback_contract_id: str = "bounded-continuity-rollback-fixture-v1",
    source: str = "FIXTURE_ONLY",
) -> LiveBoundedSingleFutureContinuityRecordV1:
    if stage in LIVE_PROGRESSION_STAGES_FORBIDDEN:
        raise LiveBoundedSingleFutureContinuityError(
            f"CAPABILITY_11_11_SURFACE_FORBIDDEN_IN_CAPABILITY_11_10:{stage}"
        )
    if stage not in LIVE_PROGRESSION_STAGES_IN_SCOPE:
        raise LiveBoundedSingleFutureContinuityError(
            f"UNKNOWN_LIVE_BOUNDED_CONTINUITY_STAGE:{stage}"
        )
    if source != "FIXTURE_ONLY":
        raise LiveBoundedSingleFutureContinuityError(
            f"NON_FIXTURE_LIVE_BOUNDED_SOURCE_FORBIDDEN_IN_CAPABILITY_11_10:{source}"
        )
    if position_count_limit != POSITION_COUNT_LIMIT:
        raise LiveBoundedSingleFutureContinuityError(
            f"LIVE_BOUNDED_POSITION_COUNT_LIMIT_FORBIDDEN:{position_count_limit}"
        )
    if not instrument_id:
        raise LiveBoundedSingleFutureContinuityError("LIVE_BOUNDED_INSTRUMENT_ID_REQUIRED")
    if not continuity_session_id:
        raise LiveBoundedSingleFutureContinuityError("LIVE_BOUNDED_CONTINUITY_SESSION_ID_REQUIRED")
    if not max_notional or max_notional == "0":
        raise LiveBoundedSingleFutureContinuityError("LIVE_BOUNDED_MAX_NOTIONAL_INVALID")
    if not rollback_contract_id:
        raise LiveBoundedSingleFutureContinuityError("LIVE_BOUNDED_ROLLBACK_CONTRACT_REQUIRED")
    if order_count_limit < 1:
        raise LiveBoundedSingleFutureContinuityError("LIVE_BOUNDED_ORDER_COUNT_LIMIT_INVALID")
    if duration_bound_seconds < 1:
        raise LiveBoundedSingleFutureContinuityError("LIVE_BOUNDED_DURATION_BOUND_INVALID")

    return LiveBoundedSingleFutureContinuityRecordV1(
        stage=stage,
        continuity_session_id=continuity_session_id,
        instrument_id=instrument_id,
        max_notional=max_notional,
        position_count_limit=position_count_limit,
        order_count_limit=order_count_limit,
        duration_bound_seconds=duration_bound_seconds,
        loss_budget=loss_budget,
        rollback_contract_id=rollback_contract_id,
        minimum_ratified_notional_only=MINIMUM_RATIFIED_NOTIONAL_ONLY,
        single_future_only=SINGLE_FUTURE_ONLY,
        source=source,
        network_effect="NONE",
        activated=False,
    )


def refuse_live_bounded_single_future_activation_v1(*, claimed_action: str) -> dict[str, Any]:
    raise LiveBoundedSingleFutureContinuityError(
        f"LIVE_BOUNDED_SINGLE_FUTURE_ACTIVATION_FORBIDDEN_IN_CAPABILITY_11_10:{claimed_action}"
    )


def refuse_automatic_stage_promotion_v1(*, claimed_target_stage: str) -> dict[str, Any]:
    raise LiveBoundedSingleFutureContinuityError(
        f"AUTOMATIC_STAGE_PROMOTION_FORBIDDEN_IN_CAPABILITY_11_10:{claimed_target_stage}"
    )


def refuse_cap_11_11_live_autonomous_v1(*, claimed_surface: str) -> dict[str, Any]:
    raise LiveBoundedSingleFutureContinuityError(
        f"CAPABILITY_11_11_SURFACE_FORBIDDEN_IN_CAPABILITY_11_10:{claimed_surface}"
    )


def prove_live_bounded_single_future_continuity_contract_v1() -> dict[str, Any]:
    record = build_live_bounded_single_future_continuity_record_v1()

    non_fixture_blocked = False
    try:
        build_live_bounded_single_future_continuity_record_v1(source="LIVE_NETWORK")
    except LiveBoundedSingleFutureContinuityError as exc:
        non_fixture_blocked = "NON_FIXTURE" in str(exc)

    multi_session_blocked = False
    try:
        build_live_bounded_single_future_continuity_record_v1(stage="LIVE_BOUNDED_MULTI_SESSION")
    except LiveBoundedSingleFutureContinuityError as exc:
        multi_session_blocked = "CAPABILITY_11_11_SURFACE_FORBIDDEN" in str(exc)

    position_limit_blocked = False
    try:
        build_live_bounded_single_future_continuity_record_v1(position_count_limit=2)
    except LiveBoundedSingleFutureContinuityError as exc:
        position_limit_blocked = "POSITION_COUNT_LIMIT_FORBIDDEN" in str(exc)

    activation_blocked = False
    try:
        refuse_live_bounded_single_future_activation_v1(claimed_action="activate_bounded")
    except LiveBoundedSingleFutureContinuityError as exc:
        activation_blocked = "ACTIVATION_FORBIDDEN" in str(exc)

    promotion_blocked = False
    try:
        refuse_automatic_stage_promotion_v1(claimed_target_stage="LIVE_BOUNDED_MULTI_SESSION")
    except LiveBoundedSingleFutureContinuityError as exc:
        promotion_blocked = "AUTOMATIC_STAGE_PROMOTION_FORBIDDEN" in str(exc)

    cap_11_11_blocked = False
    try:
        refuse_cap_11_11_live_autonomous_v1(claimed_surface="LIVE_AUTONOMOUS_SINGLE_FUTURE")
    except LiveBoundedSingleFutureContinuityError as exc:
        cap_11_11_blocked = "CAPABILITY_11_11_SURFACE_FORBIDDEN" in str(exc)

    ok = all(
        [
            record.source == "FIXTURE_ONLY",
            record.activated is False,
            record.network_effect == "NONE",
            record.stage == "LIVE_BOUNDED_SINGLE_FUTURE",
            record.position_count_limit == 1,
            record.single_future_only is True,
            record.minimum_ratified_notional_only is True,
            non_fixture_blocked,
            multi_session_blocked,
            position_limit_blocked,
            activation_blocked,
            promotion_blocked,
            cap_11_11_blocked,
            LIVE_BOUNDED_SINGLE_FUTURE_CONTINUITY_CONTRACT_BOUND is True,
            LIVE_BOUNDED_SINGLE_FUTURE_CONTINUITY_CONTRACT_ACTIVATED is False,
            LIVE_BOUNDED_SINGLE_FUTURE_CONTINUITY_ACTIVATED is False,
            LIVE_BOUNDED_SINGLE_FUTURE_ACTIVATED is False,
            MINIMUM_RATIFIED_NOTIONAL_ONLY is True,
            SINGLE_FUTURE_ONLY is True,
            NO_AUTOMATIC_STAGE_PROMOTION is True,
            OWNER_GO_REQUIRED_FOR_STAGE_PROMOTION is True,
            AUTOMATIC_STAGE_DEMOTION_ALLOWED is True,
            AUTOMATIC_HALT_ALLOWED is True,
            BOUNDED_CONTINUITY_ROLLBACK_CONTRACT_REQUIRED is True,
            record.owner == OWNER,
        ]
    )
    return {
        "ok": ok,
        "LIVE_BOUNDED_SINGLE_FUTURE_CONTINUITY_CONTRACT_BOUND": True,
        "LIVE_BOUNDED_SINGLE_FUTURE_CONTINUITY_CONTRACT_ACTIVATED": False,
        "LIVE_BOUNDED_SINGLE_FUTURE_CONTINUITY_ACTIVATED": False,
        "LIVE_BOUNDED_SINGLE_FUTURE_ACTIVATED": False,
        "MINIMUM_RATIFIED_NOTIONAL_ONLY": True,
        "SINGLE_FUTURE_ONLY": True,
        "POSITION_COUNT_LIMIT": POSITION_COUNT_LIMIT,
        "NO_AUTOMATIC_STAGE_PROMOTION": True,
        "OWNER_GO_REQUIRED_FOR_STAGE_PROMOTION": True,
        "AUTOMATIC_STAGE_DEMOTION_ALLOWED": True,
        "AUTOMATIC_HALT_ALLOWED": True,
        "BOUNDED_CONTINUITY_ROLLBACK_CONTRACT_REQUIRED": True,
        "stages_in_scope": list(LIVE_PROGRESSION_STAGES_IN_SCOPE),
        "stages_forbidden": list(LIVE_PROGRESSION_STAGES_FORBIDDEN),
        "non_fixture_blocked": non_fixture_blocked,
        "multi_session_stage_blocked": multi_session_blocked,
        "position_limit_blocked": position_limit_blocked,
        "activation_blocked": activation_blocked,
        "automatic_promotion_blocked": promotion_blocked,
        "cap_11_11_surface_blocked": cap_11_11_blocked,
        "sample_max_notional": record.max_notional,
        "sample_rollback_contract_id": record.rollback_contract_id,
        "sample_continuity_session_id": record.continuity_session_id,
        "OWNER": LIVE_BOUNDED_SINGLE_FUTURE_CONTINUITY_OWNER,
    }
