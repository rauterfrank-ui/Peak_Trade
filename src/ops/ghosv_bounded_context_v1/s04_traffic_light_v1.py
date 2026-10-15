"""S04 — traffic light aggregation."""

from __future__ import annotations

from typing import Sequence

from src.ops.ghosv_bounded_context_v1.constants_v1 import TRAFFIC_GREEN, TRAFFIC_RED, TRAFFIC_YELLOW
from src.ops.ghosv_bounded_context_v1.types_v1 import GhosvIntegrityFindingV1


def aggregate_traffic_v1(findings: Sequence[GhosvIntegrityFindingV1]) -> str:
    if any(f.traffic == TRAFFIC_RED for f in findings):
        return TRAFFIC_RED
    if any(f.traffic == TRAFFIC_YELLOW for f in findings):
        return TRAFFIC_YELLOW
    if findings and all(f.traffic == TRAFFIC_GREEN for f in findings):
        return TRAFFIC_GREEN
    return TRAFFIC_YELLOW


def aggregate_traffic_by_trade_v1(
    findings: Sequence[GhosvIntegrityFindingV1],
    trade_ids: Sequence[str],
) -> tuple[tuple[str, str], ...]:
    if not trade_ids:
        return (("__global__", aggregate_traffic_v1(findings)),)
    # Per-trade uses global aggregate unless findings carry trade scope (future); v1 uses global.
    overall = aggregate_traffic_v1(findings)
    return tuple((tid, overall) for tid in trade_ids)
