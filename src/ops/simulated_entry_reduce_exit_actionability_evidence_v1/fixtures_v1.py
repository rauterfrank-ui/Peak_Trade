"""Deterministic market fixtures for Cap 7.1 (observations/prices/time/order only)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Sequence

from src.ops.exit_policy_producer_binding_v1.constants_v1 import (
    CANONICAL_TIME_EXIT_MAX_HOLD_SECONDS,
    FROZEN_ADVERSE_EXIT_DISTANCE,
)
from src.ops.simulated_entry_reduce_exit_actionability_evidence_v1.constants_v1 import (
    FEATURE_WARMUP_SEED_LONG,
    FEATURE_WARMUP_SEED_SHORT,
)
from src.ops.stateful_confirmation_and_c1_productive_binding_v1.host_binding_v1 import (
    ObservationCycleKindV1,
)


@dataclass(frozen=True)
class FixtureTickV1:
    mid_price: float
    event_ts_unix: float
    kind: ObservationCycleKindV1 = ObservationCycleKindV1.MARKET_SAMPLE
    note: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "mid_price": float(self.mid_price),
            "event_ts_unix": float(self.event_ts_unix),
            "kind": self.kind.value,
            "note": self.note,
        }


def _ts(i: int, base: float = 1_700_000_000.0, step: float = 1.0) -> float:
    return float(base + i * step)


def long_lifecycle_fixture_v1() -> tuple[tuple[float, ...], tuple[FixtureTickV1, ...]]:
    """flat → confirm → long entry → profit exit ladder → flat."""
    seed = FEATURE_WARMUP_SEED_LONG
    ticks: list[FixtureTickV1] = []
    px = seed[-1]
    # confirmation + entry
    for i in range(3):
        px = px * 1.02
        ticks.append(FixtureTickV1(mid_price=px, event_ts_unix=_ts(i), note="bull_confirm_entry"))
    # hold then profit protection path
    for i in range(3, 7):
        px = px * 1.02
        ticks.append(FixtureTickV1(mid_price=px, event_ts_unix=_ts(i), note="profit_exit_path"))
    return seed, tuple(ticks)


def short_lifecycle_fixture_v1() -> tuple[tuple[float, ...], tuple[FixtureTickV1, ...]]:
    """flat → confirm → short entry → adverse exit → flat (prices below default stop 3400)."""
    seed = FEATURE_WARMUP_SEED_SHORT
    ticks: list[FixtureTickV1] = []
    px = seed[-1]
    for i in range(3):
        px = px * 0.985
        ticks.append(FixtureTickV1(mid_price=px, event_ts_unix=_ts(i), note="bear_confirm_entry"))
    # adverse up through entry + adverse distance
    entry_approx = ticks[1].mid_price
    ticks.append(
        FixtureTickV1(
            mid_price=float(entry_approx + FROZEN_ADVERSE_EXIT_DISTANCE + 20.0),
            event_ts_unix=_ts(3),
            note="adverse_exit_short",
        )
    )
    return seed, tuple(ticks)


def partial_reduce_fixture_v1() -> tuple[tuple[float, ...], tuple[FixtureTickV1, ...]]:
    """open long → partial profit reduces → restart boundary later → final exit."""
    return long_lifecycle_fixture_v1()


def adverse_exit_fixture_v1() -> tuple[tuple[float, ...], tuple[FixtureTickV1, ...]]:
    seed = FEATURE_WARMUP_SEED_LONG
    ticks: list[FixtureTickV1] = []
    px = seed[-1]
    for i in range(3):
        px = px * 1.02
        ticks.append(FixtureTickV1(mid_price=px, event_ts_unix=_ts(i), note="entry"))
    entry = ticks[1].mid_price
    ticks.append(
        FixtureTickV1(
            mid_price=float(entry - FROZEN_ADVERSE_EXIT_DISTANCE - 5.0),
            event_ts_unix=_ts(3),
            note="adverse_exit",
        )
    )
    return seed, tuple(ticks)


def profit_exit_fixture_v1() -> tuple[tuple[float, ...], tuple[FixtureTickV1, ...]]:
    return long_lifecycle_fixture_v1()


def time_exit_fixture_v1() -> tuple[tuple[float, ...], tuple[FixtureTickV1, ...]]:
    seed = FEATURE_WARMUP_SEED_LONG
    ticks: list[FixtureTickV1] = []
    px = seed[-1]
    for i in range(3):
        px = px * 1.02
        ticks.append(FixtureTickV1(mid_price=px, event_ts_unix=_ts(i), note="entry"))
    hold = ticks[-1].mid_price
    ticks.append(
        FixtureTickV1(
            mid_price=hold,
            event_ts_unix=_ts(2) + float(CANONICAL_TIME_EXIT_MAX_HOLD_SECONDS),
            note="time_exit",
        )
    )
    return seed, tuple(ticks)


def duplicate_observation_fixture_v1() -> tuple[tuple[float, ...], tuple[FixtureTickV1, ...]]:
    seed = FEATURE_WARMUP_SEED_LONG
    ticks = [
        FixtureTickV1(mid_price=3572.04, event_ts_unix=_ts(0), note="distinct"),
        FixtureTickV1(
            mid_price=3572.04,
            event_ts_unix=_ts(0),
            kind=ObservationCycleKindV1.DUPLICATE_SAMPLE,
            note="duplicate",
        ),
        FixtureTickV1(mid_price=3643.48, event_ts_unix=_ts(1), note="next_distinct"),
    ]
    return seed, tuple(ticks)


def lifecycle_fixture_catalog_v1() -> dict[str, Any]:
    catalog = {
        "long": long_lifecycle_fixture_v1(),
        "short": short_lifecycle_fixture_v1(),
        "partial_reduce": partial_reduce_fixture_v1(),
        "adverse": adverse_exit_fixture_v1(),
        "profit": profit_exit_fixture_v1(),
        "time": time_exit_fixture_v1(),
        "duplicate": duplicate_observation_fixture_v1(),
    }
    out: dict[str, Any] = {
        "fixture_control_surface": ["market_obs", "prices", "event_time", "order"]
    }
    for name, (seed, ticks) in catalog.items():
        out[name] = {
            "feature_warmup_seed": list(seed),
            "ticks": [t.to_dict() for t in ticks],
        }
    out["forbidden_controls"] = [
        "forced_intent",
        "direct_fill_injection",
        "master_v2_bypass",
        "risk_bypass",
        "safety_bypass",
        "exit_policy_bypass",
    ]
    return out


def ticks_from_mids(
    mids: Sequence[float], *, base_ts: float = 1_700_000_000.0
) -> tuple[FixtureTickV1, ...]:
    return tuple(
        FixtureTickV1(mid_price=float(m), event_ts_unix=_ts(i, base=base_ts))
        for i, m in enumerate(mids)
    )
