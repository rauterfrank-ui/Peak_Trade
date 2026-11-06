"""Static §11.14 flatten capture wiring. No capture execution in this repair."""

from __future__ import annotations

from typing import Any, Mapping

from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.pre_restart_handoff_capture_hook_v1 import (
    run_capture_hook_after_bound_fill_before_restart_v1,
)
from src.ops.section_11_14_current_sui_xperp_pos_1_flatten_authority_and_pre_execution_repair_v1.constants_v1 import (
    ACK_CAPTURE_KIND,
    CAPTURE_STAGE_ORDER,
    HANDOFF_HOOK_FORBIDS_ACK_CAPTURE,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.constants_v1 import (
    CANARY_AUTHORIZED,
    LIVE_ARMED,
    LIVE_ENABLED,
    POST_ALLOWED,
)


class FlattenCaptureWiringError(RuntimeError):
    """Fail-closed flatten capture-wiring violation."""


ACK_ARTIFACT_KIND = ACK_CAPTURE_KIND
HANDOFF_HOOK_KIND = "PRE_RESTART_HANDOFF_AFTER_BOUND_FILL"
HISTORICAL_FILL_REUSE_FORBIDDEN = True


def flatten_capture_stage_contract_v1() -> dict[str, Any]:
    return {
        "CAPTURE_STAGE_ORDER": list(CAPTURE_STAGE_ORDER),
        "ACK_CAPTURE_KIND": ACK_ARTIFACT_KIND,
        "HANDOFF_HOOK_KIND": HANDOFF_HOOK_KIND,
        "HANDOFF_HOOK_FORBIDS_ACK_CAPTURE": HANDOFF_HOOK_FORBIDS_ACK_CAPTURE,
        "HANDOFF_HOOK_SYMBOL": run_capture_hook_after_bound_fill_before_restart_v1.__name__,
        "CAPTURE_EXECUTED": False,
        "RETROACTIVE_BACKFILL_FORBIDDEN": True,
        "HISTORICAL_FILL_REUSE_FORBIDDEN": HISTORICAL_FILL_REUSE_FORBIDDEN,
        "ACK_AND_FILL_IDENTITIES_MUST_REMAIN_DISTINCT": True,
        "HANDOFF_COMMIT_BEFORE_REQUIRED_CAPTURE_FORBIDDEN": True,
        "STANDING_LIVE_ENABLED": bool(LIVE_ENABLED),
        "STANDING_LIVE_ARMED": bool(LIVE_ARMED),
        "STANDING_CANARY_AUTHORIZED": bool(CANARY_AUTHORIZED),
        "STANDING_POST_ALLOWED": bool(POST_ALLOWED),
    }


def assert_capture_stage_order_v1(observed: tuple[str, ...] | list[str]) -> None:
    if tuple(observed) != CAPTURE_STAGE_ORDER:
        raise FlattenCaptureWiringError("CAPTURE_STAGE_ORDER_MISMATCH")


def record_flatten_capture_stage_v1(
    *,
    durable: Mapping[str, Any],
    stage: str,
    artifact: Mapping[str, Any],
    execute: bool = False,
) -> dict[str, Any]:
    """Record one fake-path stage. execute=True is forbidden in this repair."""
    if execute is True:
        raise FlattenCaptureWiringError("CAPTURE_EXECUTION_FORBIDDEN_IN_THIS_REPAIR")
    if LIVE_ENABLED or LIVE_ARMED or CANARY_AUTHORIZED or POST_ALLOWED:
        raise FlattenCaptureWiringError("STANDING_LIVE_FLAG_MUST_REMAIN_FALSE")
    recorded = list(durable.get("recorded_stages") or [])
    expected_next = (
        CAPTURE_STAGE_ORDER[len(recorded)] if len(recorded) < len(CAPTURE_STAGE_ORDER) else None
    )
    if stage != expected_next:
        raise FlattenCaptureWiringError(
            f"CAPTURE_STAGE_OUT_OF_ORDER:got={stage}:expected={expected_next}"
        )
    if stage == "HANDOFF_COMMIT":
        required = {
            "PRE_ACTION_STATE_CAPTURE",
            "SUBMIT_INTENT_CAPTURE",
            "ACK_CAPTURE",
            "BOUND_FILL_CAPTURE",
            "FEE_CAPTURE",
            "POST_ACTION_POSITION_CAPTURE",
        }
        if not required.issubset(set(recorded)):
            raise FlattenCaptureWiringError("HANDOFF_COMMIT_BEFORE_REQUIRED_CAPTURE")
    if stage == "ACK_CAPTURE":
        kind = str(artifact.get("kind") or "")
        if kind != ACK_ARTIFACT_KIND:
            raise FlattenCaptureWiringError("ACK_CAPTURE_MUST_USE_DISTINCT_ARTIFACT_KIND")
        if str(artifact.get("handoff_hook_reused") or "") in {"true", "True"}:
            raise FlattenCaptureWiringError("ACK_MUST_NOT_REUSE_HANDOFF_HOOK")
    if stage == "BOUND_FILL_CAPTURE":
        fill_id = str(artifact.get("fill_id") or "").strip()
        ack_id = str(artifact.get("ack_id") or "").strip()
        if not fill_id or not ack_id:
            raise FlattenCaptureWiringError("ACK_AND_FILL_IDENTITIES_REQUIRED")
        if fill_id == ack_id:
            raise FlattenCaptureWiringError("ACK_AND_FILL_IDENTITIES_MUST_REMAIN_DISTINCT")
        if bool(artifact.get("historical_reuse")):
            raise FlattenCaptureWiringError("HISTORICAL_FILL_REUSE_FORBIDDEN")
    next_recorded = [*recorded, stage]
    out = dict(durable)
    out["recorded_stages"] = next_recorded
    out["last_artifact"] = dict(artifact)
    out["complete"] = tuple(next_recorded) == CAPTURE_STAGE_ORDER
    out["CAPTURE_EXECUTED"] = False
    return out


def capture_readiness_v1(*, wiring_bound: bool) -> dict[str, Any]:
    if wiring_bound is not True:
        return {"ready": False, "reason": "CAPTURE_WIRING_NOT_BOUND"}
    return {
        "ready": True,
        "reason": "STATIC_CAPTURE_WIRING_BOUND_NOT_EXECUTED",
        "CAPTURE_EXECUTED": False,
        "contract": flatten_capture_stage_contract_v1(),
    }
