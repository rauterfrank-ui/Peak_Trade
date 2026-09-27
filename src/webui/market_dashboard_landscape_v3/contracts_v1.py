"""Landscape V3 eight-section presentation taxonomy (display-only)."""

from __future__ import annotations

from typing import Any

SECTION_IDS = (
    "LIVE_MARKET_SYSTEM",
    "MARKET_INTELLIGENCE",
    "REALIZED_BEHAVIOR",
    "LEARNING",
    "OPTIMIZATION",
    "META_LEARNING",
    "MV2_DOUBLE_PLAY_ATTRIBUTION",
    "CLOSED_CYCLE_HEALTH",
)


def empty_section_field_map(section_id: str, fields: tuple[str, ...]) -> dict[str, Any]:
    return {"section_id": section_id, "fields": {name: None for name in fields}}


SECTION_FIELD_NAMES: dict[str, tuple[str, ...]] = {
    "LIVE_MARKET_SYSTEM": (
        "market_facts",
        "selection",
        "account",
        "position",
        "quality",
    ),
    "MARKET_INTELLIGENCE": (
        "context",
        "forecast",
        "uncertainty",
        "coverage",
        "drift",
    ),
    "REALIZED_BEHAVIOR": (
        "n_bars",
        "forward_return",
        "mfe_mae",
        "realized_vol",
        "regime",
    ),
    "LEARNING": (
        "calibration",
        "evidence",
        "context_value",
        "representation",
    ),
    "OPTIMIZATION": (
        "b0_b5",
        "oos",
        "challenger",
        "robustness",
        "failure_memory",
    ),
    "META_LEARNING": (
        "research_choice",
        "representation_feedback",
        "next_research",
    ),
    "MV2_DOUBLE_PLAY_ATTRIBUTION": (
        "decision_t",
        "context_t",
        "outcome_t_plus_n",
        "attribution",
    ),
    "CLOSED_CYCLE_HEALTH": (
        "loop_a",
        "loop_b",
        "loop_c",
        "routing",
        "replay",
    ),
}
