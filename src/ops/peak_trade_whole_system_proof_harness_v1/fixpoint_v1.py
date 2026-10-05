"""Fixpoint engine — two consecutive zero-delta passes required."""

from __future__ import annotations

from typing import Any, Callable


def run_fixpoint_v1(
    discover_fn: Callable[[], dict[str, Any]],
    *,
    max_passes: int = 5,
) -> dict[str, Any]:
    passes: list[dict[str, Any]] = []
    prev_key: tuple[int, int, int] | None = None
    consecutive_zero = 0
    for i in range(max_passes):
        snap = discover_fn()
        key = (
            len(snap.get("components", [])),
            len(snap.get("edges", [])),
            len(snap.get("dynamic_bindings", [])),
        )
        delta = (
            0 if prev_key is None else max(0, key[0] - prev_key[0]) + max(0, key[1] - prev_key[1])
        )
        pass_row = {
            "PASS": i + 1,
            "NEW_COMPONENTS": max(0, key[0] - (prev_key[0] if prev_key else 0)),
            "NEW_EDGES": max(0, key[1] - (prev_key[1] if prev_key else 0)),
            "NEW_DYNAMIC_BINDINGS": max(0, key[2] - (prev_key[2] if prev_key else 0)),
            "DELTA": delta,
        }
        passes.append(pass_row)
        if delta == 0 and prev_key is not None:
            consecutive_zero += 1
        else:
            consecutive_zero = 0
        prev_key = key
        if consecutive_zero >= 2:
            break
    return {
        "PASSES": passes,
        "SEMANTIC_FIXPOINT_REACHED": consecutive_zero >= 2,
        "CONSECUTIVE_ZERO_DELTA_PASSES": consecutive_zero,
    }
