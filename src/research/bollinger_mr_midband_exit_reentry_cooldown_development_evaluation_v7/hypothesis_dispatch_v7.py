"""Hypothesis-ID dispatch for V7 reentry-cooldown evaluation surfaces."""

from __future__ import annotations

from typing import Any, Mapping

from src.research.bollinger_mr_midband_exit_reentry_cooldown_development_evaluation_v7.constants_v7 import (
    CLI_REL_PATH,
    HYPOTHESIS_ID,
    OWNER_SURFACE,
)

HYPOTHESIS_DISPATCH_V7: dict[str, dict[str, str]] = {
    HYPOTHESIS_ID: {
        "cli": CLI_REL_PATH,
        "runner": (
            "src.research.bollinger_mr_midband_exit_reentry_cooldown_development_evaluation_v7"
            ".panel_runner_v7:run_development_evaluation"
        ),
        "owner_surface": OWNER_SURFACE,
        "preflight": (
            "src.research.bollinger_mr_midband_exit_reentry_cooldown_development_evaluation_v7"
            ".measurement_validity_preflight_v7:run_measurement_validity_preflight"
        ),
        "decision": (
            "src.research.bollinger_mr_midband_exit_reentry_cooldown_development_evaluation_v7"
            ".decision_v7:decide_development_evaluation_v7"
        ),
    }
}


class HypothesisDispatchError(ValueError):
    """Unknown or unbound hypothesis id for V7 dispatch."""


def resolve_v7_dispatch(hypothesis_id: str) -> dict[str, str]:
    entry = HYPOTHESIS_DISPATCH_V7.get(hypothesis_id)
    if entry is None:
        raise HypothesisDispatchError(f"HYPOTHESIS_ID_NOT_BOUND:{hypothesis_id}")
    return dict(entry)


def dispatch_table_snapshot() -> Mapping[str, Any]:
    return {
        "schema_version": "bollinger_mr_v7_hypothesis_dispatch.v1",
        "entries": dict(HYPOTHESIS_DISPATCH_V7),
    }


__all__ = [
    "HYPOTHESIS_DISPATCH_V7",
    "HypothesisDispatchError",
    "dispatch_table_snapshot",
    "resolve_v7_dispatch",
]
