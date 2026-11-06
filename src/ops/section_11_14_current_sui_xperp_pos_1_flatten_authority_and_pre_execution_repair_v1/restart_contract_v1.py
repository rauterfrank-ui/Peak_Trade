"""Static flatten restart/durability contract. Host-crash remains UNPROVEN."""

from __future__ import annotations

from typing import Any, Mapping

from src.ops.section_11_14_current_sui_xperp_pos_1_flatten_authority_and_pre_execution_repair_v1.constants_v1 import (
    DURABLE_STATE_COMPLETED,
    DURABLE_STATE_INCOMPLETE,
    DURABLE_STATE_NONE,
    HOST_CRASH_DURABILITY,
    LIVE_RESTART_RECONSTRUCTED,
    RESTART_DEFAULT_ACTION,
    RETRY_ALLOWED,
    STATIC_RESTART_PATH_READY_DEFAULT,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.constants_v1 import (
    CANARY_AUTHORIZED,
    LIVE_ARMED,
    LIVE_ENABLED,
    POST_ALLOWED,
)


class FlattenRestartContractError(RuntimeError):
    """Fail-closed flatten restart-contract violation."""


def static_restart_contract_v1() -> dict[str, Any]:
    return {
        "STATIC_RESTART_PATH_READY": STATIC_RESTART_PATH_READY_DEFAULT,
        "HOST_CRASH_DURABILITY": HOST_CRASH_DURABILITY,
        "LIVE_RESTART_RECONSTRUCTED": LIVE_RESTART_RECONSTRUCTED,
        "RESTART_DEFAULT_ACTION": RESTART_DEFAULT_ACTION,
        "RETRY_ALLOWED": RETRY_ALLOWED,
        "AUTOMATIC_RETRY_AFTER_CRASH": False,
        "COMPLETED_STATE_CANNOT_RESUBMIT": True,
        "INCOMPLETE_STATE_FAIL_CLOSED_NO_SUBMIT": True,
        "NONE_STATE_FAIL_CLOSED_NO_SUBMIT": True,
    }


def reconstruct_flatten_durable_state_v1(record: Mapping[str, Any] | None) -> dict[str, Any]:
    if LIVE_ENABLED or LIVE_ARMED or CANARY_AUTHORIZED or POST_ALLOWED:
        raise FlattenRestartContractError("STANDING_LIVE_FLAG_MUST_REMAIN_FALSE")
    if record is None:
        return {
            "state": DURABLE_STATE_NONE,
            "action": RESTART_DEFAULT_ACTION,
            "resubmit_allowed": False,
            "reason": "NO_DURABLE_RECORD",
        }
    state = str(record.get("durable_state") or DURABLE_STATE_NONE).strip()
    if state == DURABLE_STATE_COMPLETED:
        return {
            "state": DURABLE_STATE_COMPLETED,
            "action": RESTART_DEFAULT_ACTION,
            "resubmit_allowed": False,
            "reason": "COMPLETED_FLATTEN_CANNOT_RESUBMIT",
            "action_identity": str(record.get("action_identity") or ""),
            "instrument_id": str(record.get("instrument_id") or ""),
            "client_order_id": str(record.get("client_order_id") or ""),
            "ack_id": str(record.get("ack_id") or ""),
            "fill_id": str(record.get("fill_id") or ""),
        }
    if state == DURABLE_STATE_INCOMPLETE:
        return {
            "state": DURABLE_STATE_INCOMPLETE,
            "action": RESTART_DEFAULT_ACTION,
            "resubmit_allowed": False,
            "reason": "INCOMPLETE_STATE_FAIL_CLOSED_NO_AUTOMATIC_RETRY",
            "new_explicit_authority_required": True,
        }
    return {
        "state": DURABLE_STATE_NONE,
        "action": RESTART_DEFAULT_ACTION,
        "resubmit_allowed": False,
        "reason": "UNKNOWN_OR_NONE_DEFAULT_NO_SUBMIT",
    }


def assert_restart_does_not_submit_v1(decision: Mapping[str, Any]) -> None:
    if str(decision.get("action") or "") != RESTART_DEFAULT_ACTION:
        raise FlattenRestartContractError("RESTART_MUST_DEFAULT_NO_SUBMIT")
    if decision.get("resubmit_allowed") is True:
        raise FlattenRestartContractError("RESTART_RESUBMIT_FORBIDDEN")
