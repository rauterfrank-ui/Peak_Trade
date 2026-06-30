"""Deterministic adapter from canonical strategy registry snapshot to SuitabilityStrategyRegistryV1."""

from __future__ import annotations

from typing import Optional, Sequence, Tuple

from src.trading.master_v2.directional_assessment_v1 import DirectionalAssessmentSide
from src.trading.master_v2.suitability_binding_v1 import (
    SuitabilityStrategyEntryV1,
    SuitabilityStrategyRegistryV1,
)

from .registry import StrategyRegistryEntryV1, StrategyRegistrySnapshotV1


def _default_priority_rank(strategy_id: str) -> int:
    return sum(ord(c) for c in strategy_id) % 10_000


def canonical_entry_to_suitability_entry(
    entry: StrategyRegistryEntryV1,
    *,
    priority_rank: Optional[int] = None,
    supported_regime_ids: Optional[Sequence[str]] = None,
) -> SuitabilityStrategyEntryV1:
    sides: Tuple[DirectionalAssessmentSide, ...] = ()
    if "long" in entry.supported_sides and "short" in entry.supported_sides:
        sides = (DirectionalAssessmentSide.LONG, DirectionalAssessmentSide.SHORT)
    elif "long" in entry.supported_sides:
        sides = (DirectionalAssessmentSide.LONG,)
    elif "short" in entry.supported_sides:
        sides = (DirectionalAssessmentSide.SHORT,)

    regimes = tuple(supported_regime_ids or entry.supported_regimes or ("*",))
    rank = priority_rank if priority_rank is not None else _default_priority_rank(entry.strategy_id)
    disabled = entry.deprecation_status.value in {"DEPRECATED_STRATEGY", "REMOVED"}

    return SuitabilityStrategyEntryV1(
        strategy_id=entry.strategy_id,
        supported_regime_ids=regimes,
        supported_sides=sides,
        priority_rank=rank,
        disabled=disabled,
    )


def build_suitability_registry_from_snapshot(
    snapshot: StrategyRegistrySnapshotV1,
    *,
    priority_ranks: Optional[dict[str, int]] = None,
    regime_overrides: Optional[dict[str, Sequence[str]]] = None,
) -> SuitabilityStrategyRegistryV1:
    ranks = priority_ranks or {}
    regimes = regime_overrides or {}
    entries = tuple(
        canonical_entry_to_suitability_entry(
            entry,
            priority_rank=ranks.get(entry.strategy_id),
            supported_regime_ids=regimes.get(entry.strategy_id),
        )
        for entry in sorted(snapshot.entries, key=lambda e: e.strategy_id)
    )
    return SuitabilityStrategyRegistryV1(entries=entries)
