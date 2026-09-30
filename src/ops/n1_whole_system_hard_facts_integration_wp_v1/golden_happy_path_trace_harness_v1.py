"""RW-E22: golden vector vs runtime trace with first-divergence reporting."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping, Sequence


GOLDEN_TRACE_KEYS: tuple[str, ...] = (
    "RUN_ID",
    "instrument",
    "instrument_epoch",
    "ranking_snapshot",
    "membership_artifact",
    "lane_id",
    "cap23_selection",
    "cap24_binding",
    "observation_epoch",
    "confirmation_epoch",
    "g17",
    "feature_regime",
    "cmc",
    "dynamic_scope",
    "mv2_double_play",
    "qualification",
    "side_state",
    "entry_exit_policy",
    "quantity",
    "reservation",
    "final_order_envelope",
    "pre_external",
)


@dataclass
class GoldenHappyPathTraceResultV1:
    ok: bool
    vector_name: str
    expected: dict[str, Any]
    actual: dict[str, Any]
    first_divergence_key: str = ""
    first_divergence_detail: str = ""
    contiguous_confirmation: bool = False


@dataclass
class GoldenHarnessAggregateV1:
    natural_long: GoldenHappyPathTraceResultV1
    natural_short: GoldenHappyPathTraceResultV1
    hold: GoldenHappyPathTraceResultV1
    negative_vectors: list[GoldenHappyPathTraceResultV1] = field(default_factory=list)


def build_expected_golden_vector_v1(
    *,
    run_id: str,
    instrument: str,
    side: str,
) -> dict[str, Any]:
    terminal = "PRE_EXTERNAL" if side in {"LONG", "SHORT"} else "HOLD"
    return {
        "RUN_ID": run_id,
        "instrument": instrument,
        "side": side,
        "pre_external": side in {"LONG", "SHORT"},
        "terminal": terminal,
        "synthetic_b05_rejected": True,
    }


def diff_golden_vs_actual_v1(
    *,
    expected: Mapping[str, Any],
    actual: Mapping[str, Any],
    vector_name: str,
    keys: Sequence[str] | None = None,
) -> GoldenHappyPathTraceResultV1:
    compare_keys = keys or GOLDEN_TRACE_KEYS
    first_key = ""
    first_detail = ""
    for key in compare_keys:
        if key not in expected and key not in actual:
            continue
        exp = expected.get(key)
        act = actual.get(key)
        if exp != act:
            first_key = key
            first_detail = f"expected={exp!r} actual={act!r}"
            break
    ok = first_key == ""
    return GoldenHappyPathTraceResultV1(
        ok=ok,
        vector_name=vector_name,
        expected=dict(expected),
        actual=dict(actual),
        first_divergence_key=first_key,
        first_divergence_detail=first_detail,
        contiguous_confirmation=actual.get("contiguous_confirmation") is True
        or expected.get("contiguous_confirmation") is True,
    )


def prove_natural_long_short_hold_vectors_v1(
    *,
    run_id: str,
    instrument: str,
    long_actual: Mapping[str, Any],
    short_actual: Mapping[str, Any],
    hold_actual: Mapping[str, Any],
) -> GoldenHarnessAggregateV1:
    long_exp = build_expected_golden_vector_v1(run_id=run_id, instrument=instrument, side="LONG")
    short_exp = build_expected_golden_vector_v1(run_id=run_id, instrument=instrument, side="SHORT")
    hold_exp = build_expected_golden_vector_v1(run_id=run_id, instrument=instrument, side="HOLD")
    return GoldenHarnessAggregateV1(
        natural_long=diff_golden_vs_actual_v1(
            expected=long_exp,
            actual=long_actual,
            vector_name="NATURAL_LONG",
            keys=tuple(long_exp.keys()),
        ),
        natural_short=diff_golden_vs_actual_v1(
            expected=short_exp,
            actual=short_actual,
            vector_name="NATURAL_SHORT",
            keys=tuple(short_exp.keys()),
        ),
        hold=diff_golden_vs_actual_v1(
            expected=hold_exp,
            actual=hold_actual,
            vector_name="HOLD",
            keys=tuple(hold_exp.keys()),
        ),
    )


def negative_failure_vector_v1(
    *,
    name: str,
    expected_block: str,
    actual: Mapping[str, Any],
) -> GoldenHappyPathTraceResultV1:
    blocked_at = str(actual.get("first_block") or actual.get("failure_code") or "")
    ok = blocked_at == expected_block or expected_block in blocked_at
    return GoldenHappyPathTraceResultV1(
        ok=ok,
        vector_name=name,
        expected={"first_block": expected_block},
        actual=dict(actual),
        first_divergence_key="first_block" if not ok else "",
        first_divergence_detail="" if ok else f"expected={expected_block} got={blocked_at}",
    )
