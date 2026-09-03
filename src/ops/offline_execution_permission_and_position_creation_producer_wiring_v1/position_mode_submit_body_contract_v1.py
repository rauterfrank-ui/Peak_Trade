"""Route-C position-mode / posSide submit-body contract.

Committed repository evidence does not prove whether an OKX net-mode entry
body must omit posSide, emit posSide=net, or use another token. This module
persists that gap as UNPROVEN and refuses submission-ready bodies. It does
not manufacture posSide=net.
"""

from __future__ import annotations

from typing import Any, Mapping

from src.ops.offline_execution_permission_and_position_creation_producer_wiring_v1.route_c_submit_composition_constants_v1 import (
    POSITION_MODE_FAIL_CLOSED,
    POSITION_MODE_SUBMIT_BODY_SEMANTICS,
)

FORBIDDEN_MANUFACTURED_POSSIDE_VALUES: frozenset[str] = frozenset(
    {"net", "long", "short", "NET", "LONG", "SHORT"}
)


class PositionModeSubmitBodyContractError(RuntimeError):
    """Fail-closed unresolved position-mode submit-body semantics."""


def evaluate_position_mode_submit_body_v1(
    *,
    venue_native_body: Mapping[str, Any] | None,
    pos_mode: str,
) -> tuple[str, tuple[str, ...], bool]:
    """Return (semantics, reasons, submission_ready_allowed).

    submission_ready_allowed is always False while semantics remain UNPROVEN.
    """
    del pos_mode
    reasons: list[str] = []
    if POSITION_MODE_SUBMIT_BODY_SEMANTICS != "UNPROVEN":
        raise PositionModeSubmitBodyContractError("POSITION_MODE_SEMANTICS_DRIFT")
    if not POSITION_MODE_FAIL_CLOSED:
        raise PositionModeSubmitBodyContractError("POSITION_MODE_FAIL_CLOSED_REQUIRED")
    reasons.append("POSITION_MODE_SUBMIT_BODY_SEMANTICS_UNPROVEN")
    body = {} if venue_native_body is None else dict(venue_native_body)
    raw_pos_side = body.get("posSide")
    if raw_pos_side is not None:
        token = str(raw_pos_side).strip()
        if token in FORBIDDEN_MANUFACTURED_POSSIDE_VALUES or token:
            reasons.append("POSSIDE_EMITTED_WHILE_SEMANTICS_UNPROVEN")
            if token.lower() == "net":
                reasons.append("POSSIDE_NET_MANUFACTURED_FORBIDDEN")
    return (
        POSITION_MODE_SUBMIT_BODY_SEMANTICS,
        tuple(dict.fromkeys(reasons)),
        False,
    )
