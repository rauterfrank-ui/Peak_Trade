"""PRE_EXTERNAL terminal isolation — LIVE remains terminal; SHADOW may continue explicitly."""

from __future__ import annotations

from src.ops.canonical_shadow_runtime_enablement_v1.constants_v1 import (
    EXECUTION_LANE_LIVE,
    EXECUTION_LANE_SHADOW,
    EXECUTION_LANE_TESTNET,
    LIVE_PRE_EXTERNAL_TERMINAL,
    SHADOW_PRE_EXTERNAL_CONTINUATION,
)
from src.ops.full_core_live_path_composition_root_v1.current_productive_governed_cycle_orchestrator_v1 import (
    DISPOSITION_PRE_EXTERNAL_EFFECT,
)

PRE_EXTERNAL_TERMINAL_DISPOSITION = DISPOSITION_PRE_EXTERNAL_EFFECT


class PreExternalLaneIsolationError(ValueError):
    """Fail-closed lane violation."""


def assert_pre_external_disposition_v1(*, disposition: str) -> None:
    if str(disposition) != PRE_EXTERNAL_TERMINAL_DISPOSITION:
        raise PreExternalLaneIsolationError(
            f"expected_pre_external_disposition:{PRE_EXTERNAL_TERMINAL_DISPOSITION!r};"
            f"got={disposition!r}"
        )


def resolve_post_pre_external_continuation_v1(
    *,
    execution_lane: str,
    pre_external_reached: bool,
) -> str:
    if not pre_external_reached:
        raise PreExternalLaneIsolationError("pre_external_not_reached")
    lane = str(execution_lane or "").strip().upper()
    if lane == EXECUTION_LANE_LIVE:
        if LIVE_PRE_EXTERNAL_TERMINAL is not True:
            raise PreExternalLaneIsolationError("live_pre_external_terminal_invariant_violated")
        return "TERMINAL_PRE_EXTERNAL"
    if lane == EXECUTION_LANE_TESTNET:
        raise PreExternalLaneIsolationError("testnet_post_pre_external_forbidden_in_shadow_wp")
    if lane == EXECUTION_LANE_SHADOW:
        return SHADOW_PRE_EXTERNAL_CONTINUATION
    raise PreExternalLaneIsolationError(f"unknown_execution_lane:{lane!r}")
