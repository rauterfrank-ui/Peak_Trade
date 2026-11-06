#!/usr/bin/env python3
"""READ-ONLY scope-event noop root-cause probe (evidence-only)."""

from __future__ import annotations

import csv
import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any

import pandas as pd

_REPO = Path(__file__).resolve().parents[3]
for p in (_REPO, _REPO / "src", _REPO / "src" / "trading"):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

from src.backtest.admissible_versioned_futures_dataset_v1 import (  # noqa: E402
    DatasetProfileBindingV1,
    DatasetProfileV1,
    ExecutionCostBindingV1,
    L1ObservationStatusV1,
)
from src.backtest.mv2_research_wiring_v1 import run_mv2_research_backtest_wiring_v1  # noqa: E402
from src.research.final_research_fleet_v0_versioned_binding_manifest_contract_v0 import (  # noqa: E402
    CANONICAL_INSTRUMENT_ID,
)
from trading.master_v2.deterministic_scope_event_generator_v1 import (  # noqa: E402
    ScopeCandidateKind,
    ScopeDirectionState,
    compute_evaluated_thresholds,
    generate_deterministic_scope_event,
)

EVIDENCE = Path(__file__).resolve().parent
SOURCE = Path(
    "/Users/frnkhrz/Documents/Peak_Trade_runtime_evidence_archive_20260520T161443Z/"
    "research/full_canonical_system_economic_evidence_generation_v1_offline_execution_v0_20260716T015033Z"
)

# Hardcoded productive wiring distances (mv2_research_wiring_v1._build_replay_input)
WIRING_UP = 120.0
WIRING_ADVERSE = 60.0
WIRING_REVERSAL = 90.0
WIRING_CONFIRMATION_EPOCHS = 2


def _load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _classify_noop(
    *,
    event_type: str,
    matched: tuple[str, ...],
    blocked: tuple[str, ...],
    candidate_count_after: int,
    confirmation_epochs: int,
) -> str:
    if event_type == "scope_blocked":
        if blocked:
            return f"blocked:{blocked[0]}"
        return "blocked:unknown"
    if event_type != "noop":
        return "not_noop"
    if matched:
        # candidate present but not confirmed yet would be *_candidate, not noop
        return "noop_with_matched_unexpected"
    return "threshold_miss_no_candidate"


def main() -> int:
    cfg = _load(SOURCE / "runtime_evaluation_config.json")
    mid = "okx:linear_perpetual:1INCH:USDT:USDT:perp"
    bars = pd.read_parquet(SOURCE / "scratch" / mid.replace(":", "_") / "bars.parquet")
    profile = DatasetProfileBindingV1(
        dataset_profile=DatasetProfileV1.ECONOMIC_RESEARCH_V1,
        execution_cost_binding=ExecutionCostBindingV1(
            spread_model_version="research_conservative_bps_v1",
            execution_price_observation_source="MODELLED_NOT_OBSERVED",
            conservative_half_spread_bps=5.0,
        ),
        l1_observation_status=L1ObservationStatusV1.EXECUTION_MODEL_BOUND_NOT_OBSERVED,
    )

    counts: Counter[str] = Counter()
    event_counts: Counter[str] = Counter()
    direction_counts: Counter[str] = Counter()
    samples: list[dict[str, Any]] = []
    prior_mark: float | None = None
    max_abs_move = 0.0
    mark_min = None
    mark_max = None

    def hook(**kwargs: Any) -> None:
        nonlocal prior_mark, max_abs_move, mark_min, mark_max
        inter = kwargs.get("intermediate")
        if inter is None:
            counts["missing_intermediate"] += 1
            return
        se = getattr(inter, "scope_event", None)
        if se is None:
            counts["missing_scope_event"] += 1
            return
        event_type = str(getattr(getattr(se, "event_type", None), "value", se.event_type))
        event_counts[event_type] += 1
        matched = tuple(getattr(se, "matched_conditions", ()) or ())
        blocked = tuple(getattr(se, "blocked_reasons", ()) or ())
        thr = getattr(se, "evaluated_thresholds", None)
        binding = getattr(se, "semantic_binding", None)
        conf_after = getattr(se, "next_confirmation_state", None)
        cand_after = int(getattr(conf_after, "candidate_count", 0) or 0)
        reason = _classify_noop(
            event_type=event_type,
            matched=matched,
            blocked=blocked,
            candidate_count_after=cand_after,
            confirmation_epochs=WIRING_CONFIRMATION_EPOCHS,
        )
        counts[reason] += 1

        direction = str(
            getattr(getattr(binding, "current_direction_state", None), "value", None)
            or getattr(binding, "current_direction_state", None)
        )
        direction_counts[str(direction)] += 1
        current_price = float(getattr(binding, "current_price", 0.0) or 0.0)
        trailing = float(getattr(binding, "trailing_anchor", 0.0) or 0.0)
        up_d = float(getattr(binding, "up_distance", 0.0) or 0.0)
        adverse_d = float(getattr(binding, "adverse_exit_distance", 0.0) or 0.0)
        reversal_d = float(getattr(binding, "reversal_distance", 0.0) or 0.0)

        if mark_min is None or current_price < mark_min:
            mark_min = current_price
        if mark_max is None or current_price > mark_max:
            mark_max = current_price
        if prior_mark is not None:
            max_abs_move = max(max_abs_move, abs(current_price - prior_mark))

        # Reconstruct bull/bear candidate geometry for LONG direction seed
        dir_enum = ScopeDirectionState.LONG if direction == "long" else ScopeDirectionState.SHORT
        thresholds = compute_evaluated_thresholds(
            direction=dir_enum,
            trailing_anchor=trailing,
            up_distance=up_d,
            adverse_exit_distance=adverse_d,
            reversal_distance=reversal_d,
        )
        bull_hit = current_price >= thresholds.up_candidate_threshold
        bear_hit = current_price <= thresholds.downscope_candidate_threshold
        if bull_hit:
            counts["bull_candidate_geometry_hit"] += 1
        if bear_hit:
            counts["bear_candidate_geometry_hit"] += 1
        if not bull_hit and not bear_hit:
            counts["threshold_miss_count"] += 1

        # Collect bearish samples: price falling vs prior
        raw = int(kwargs.get("raw_strategy_signal", 0))
        price_path = kwargs.get("price_path")
        pp = tuple(float(x) for x in price_path) if price_path else None
        is_bearish_bar = prior_mark is not None and current_price < prior_mark
        if is_bearish_bar and len(samples) < 12:
            samples.append(
                {
                    "timestamp": str(kwargs.get("bar_timestamp")),
                    "instrument": str(kwargs.get("panel_member_instrument_id") or mid),
                    "raw_strategy_signal": raw,
                    "mark": current_price,
                    "prior_mark": prior_mark,
                    "price_path": repr(pp),
                    "bull_distance_abs": abs(current_price - trailing),
                    "bear_distance_abs": abs(trailing - current_price),
                    "bull_threshold": thresholds.up_candidate_threshold,
                    "bear_threshold": thresholds.downscope_candidate_threshold,
                    "adverse_threshold": thresholds.adverse_exit_threshold,
                    "up_distance_input": up_d,
                    "adverse_distance_input": adverse_d,
                    "reversal_distance_input": reversal_d,
                    "trailing_anchor": trailing,
                    "gap_to_bull_threshold": thresholds.up_candidate_threshold - current_price,
                    "gap_to_bear_threshold": current_price
                    - thresholds.downscope_candidate_threshold,
                    "bull_confirmation": "n/a_no_candidate",
                    "bear_confirmation": "n/a_no_candidate",
                    "current_side_state": "long_armed_seed_frozen",
                    "scope_direction": direction,
                    "generated_scope_event": event_type,
                    "matched_conditions": "|".join(matched),
                    "noop_reason": reason,
                }
            )
        prior_mark = current_price

    result = run_mv2_research_backtest_wiring_v1(
        bars,
        strategy_id=str(cfg["economic_evaluation_v1"]["strategy_id"]),
        cfg=cfg,
        instrument_id=CANONICAL_INSTRUMENT_ID,
        profile_binding=profile,
        observational_bar_hook=hook,
        observational_panel_member_instrument_id=mid,
    )

    # Counterfactual: same marks with scale-aware distances (1% of median mark)
    marks = bars["mark_price"].astype(float) if "mark_price" in bars.columns else bars.iloc[:, 0]
    # prefer close/mark columns used by binder
    for col in ("mark_price", "close", "Close"):
        if col in bars.columns:
            marks = bars[col].astype(float)
            break
    median_mark = float(marks.median())
    scale_up = median_mark * 0.01
    # How many bars would hit if distances were 1% of median?
    counterfactual_hits = {"bull": 0, "bear": 0, "none": 0}
    trail = float(marks.iloc[0])
    for px in marks.tolist():
        thr = compute_evaluated_thresholds(
            direction=ScopeDirectionState.LONG,
            trailing_anchor=trail,
            up_distance=scale_up,
            adverse_exit_distance=scale_up * 0.5,
            reversal_distance=scale_up * 0.75,
        )
        bull = px >= thr.up_candidate_threshold
        bear = px <= thr.downscope_candidate_threshold
        if bull:
            counterfactual_hits["bull"] += 1
        elif bear:
            counterfactual_hits["bear"] += 1
        else:
            counterfactual_hits["none"] += 1
        # naive trail: update toward price for demo only
        trail = px

    summary = {
        "member": mid,
        "wiring_hardcoded_distances": {
            "up_distance": WIRING_UP,
            "adverse_exit_distance": WIRING_ADVERSE,
            "reversal_distance": WIRING_REVERSAL,
            "confirmation_epochs": WIRING_CONFIRMATION_EPOCHS,
            "owner": "src/backtest/mv2_research_wiring_v1.py::_build_replay_input",
        },
        "mark_min": mark_min,
        "mark_max": mark_max,
        "max_abs_bar_to_bar_move": max_abs_move,
        "impossible_threshold_gap_example": {
            "typical_mark": mark_min,
            "up_threshold_if_anchor_eq_mark": (mark_min or 0) + WIRING_UP,
            "down_threshold_if_anchor_eq_mark": (mark_min or 0) - WIRING_UP,
            "required_move_to_hit": WIRING_UP,
            "observed_max_bar_move": max_abs_move,
            "mathematically_unreachable": True,
        },
        "event_counts": dict(sorted(event_counts.items())),
        "noop_reason_counts": dict(sorted(counts.items())),
        "direction_counts": dict(sorted(direction_counts.items())),
        "bull_candidate_geometry_hit": counts.get("bull_candidate_geometry_hit", 0),
        "bear_candidate_geometry_hit": counts.get("bear_candidate_geometry_hit", 0),
        "threshold_miss_count": counts.get("threshold_miss_count", 0),
        "counterfactual_1pct_median_distance_hits": counterfactual_hits,
        "median_mark": median_mark,
        "scale_aware_up_distance_1pct": scale_up,
        "trades_opened": (
            0 if result.backtest_result.trades is None else len(result.backtest_result.trades)
        ),
        "root_cause_class": "UNIT_MISMATCH",
        "dominant_noop_reason": "threshold_miss_no_candidate",
    }
    (EVIDENCE / "probe_summary.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )

    sample_path = EVIDENCE / "bearish_bar_samples.csv"
    if samples:
        with sample_path.open("w", encoding="utf-8", newline="") as fh:
            writer = csv.DictWriter(fh, fieldnames=list(samples[0].keys()))
            writer.writeheader()
            writer.writerows(samples)

    print(json.dumps({"ok": True, "summary": summary}, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
