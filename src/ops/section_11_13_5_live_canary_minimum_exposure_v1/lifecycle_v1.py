"""Lifecycle / closeout / unknown-submit contracts for §11.13.5 (gated; not activated)."""

from __future__ import annotations

from typing import Any


class LiveCanaryLifecycleError(RuntimeError):
    """Fail-closed lifecycle contract violation."""


ALLOWED_LIFECYCLE_STATES: tuple[str, ...] = (
    "PRE_SUBMIT_GATED",
    "SUBMIT_PENDING",
    "ACKNOWLEDGED",
    "REJECTED",
    "PARTIAL_FILL",
    "FILLED",
    "CANCEL_PENDING",
    "CANCELED",
    "UNKNOWN_SUBMIT",
    "FLATTEN_PENDING",
    "FLAT",
    "HALTED",
)


def build_lifecycle_and_closeout_contract_v1() -> dict[str, Any]:
    return {
        "DOCUMENT_CLASS": "SECTION_11_13_5_LIFECYCLE_CLOSEOUT_CONTRACT_V1",
        "ACTIVATED": False,
        "allowed_lifecycle_states": list(ALLOWED_LIFECYCLE_STATES),
        "idempotency_policy": "ONE_SHOT_CLORDID_PER_OWNER_GO_BINDING",
        "clordid_prefix": "pt-canary-",
        "ack_handling": "REQUIRE_EXCHANGE_ORDID_OR_EXPLICIT_REJECT_CODE",
        "fill_handling": "RECORD_FILL_THEN_POST_TRADE_RECONCILE",
        "reject_handling": "NO_RETRY_WITHOUT_NEW_OWNER_GO; SEAL_EVIDENCE",
        "unknown_submit_handling": (
            "POLL_ORDERS_PENDING_AND_ORDER_HISTORY_WITHIN_BOUNDED_TIMEOUT;"
            "IF_STILL_UNKNOWN_THEN_HALT_AND_OWNER_REVIEW"
        ),
        "cancel_flatten_closeout": (
            "ON_STOP_OR_KILL: CANCEL_OPEN_CANARY_ORDER_THEN_CLOSE_POSITION_IF_ANY;"
            "REQUIRE_FLAT_BEFORE_PROVEN"
        ),
        "residual_order_detection": "FAIL_IF_OPEN_ORDERS_REMAIN_AFTER_CLOSEOUT",
        "residual_position_detection": "FAIL_IF_POSITION_REMAINS_AFTER_CLOSEOUT",
        "post_trade_reconciliation": (
            "RE-RUN_SECTION_11_5_LAYERS_AFTER_FLAT; DIVERGENCE_BLOCKS_PROVEN"
        ),
        "emergency_kill_switch_interaction": (
            "KILL_SWITCH_OR_HALT_TRIGGERS_IMMEDIATE_CANCEL_FLATTEN_PATH;NO_NEW_ENTRY_WHILE_HALTED"
        ),
        "bounded_timeout_retry_policy": {
            "submit_timeout_seconds": 15.0,
            "unknown_submit_poll_timeout_seconds": 60.0,
            "closeout_timeout_seconds": 120.0,
            "max_retries": 2,
            "retry_backoff_seconds": 0.25,
        },
        "order_count_limit": 1,
        "position_count_limit": 1,
        "direction_semantics": "SINGLE_SIDE_LIMIT_ONLY",
        "order_type_semantics": "LIMIT_ONLY_NO_MARKET",
    }


def refuse_ungated_lifecycle_transition_v1(*, claimed_state: str) -> None:
    raise LiveCanaryLifecycleError(f"UNGATED_LIFECYCLE_TRANSITION_FORBIDDEN:{claimed_state}")
