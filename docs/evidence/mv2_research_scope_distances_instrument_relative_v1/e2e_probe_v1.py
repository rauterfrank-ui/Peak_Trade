#!/usr/bin/env python3
"""Evidence-only before/after probe for mark-relative research scope distances."""

from __future__ import annotations

import csv
import json
import math
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
from src.backtest.mv2_research_wiring_v1 import (  # noqa: E402
    compute_mv2_research_scope_distances_absolute_from_mark_v1,
    run_mv2_research_backtest_wiring_v1,
)
from src.research.final_research_fleet_v0_versioned_binding_manifest_contract_v0 import (  # noqa: E402
    CANONICAL_INSTRUMENT_ID,
)
from trading.master_v2.deterministic_scope_event_generator_v1 import (  # noqa: E402
    ScopeDirectionState,
    compute_evaluated_thresholds,
)

EVIDENCE = Path(__file__).resolve().parent
SOURCE = Path(
    "/Users/frnkhrz/Documents/Peak_Trade_runtime_evidence_archive_20260520T161443Z/"
    "research/full_canonical_system_economic_evidence_generation_v1_offline_execution_v0_20260716T015033Z"
)
MID = "okx:linear_perpetual:1INCH:USDT:USDT:perp"


def _load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> int:
    if not SOURCE.is_dir():
        summary = {"ok": False, "reason": "archive_missing", "source": str(SOURCE)}
        (EVIDENCE / "probe_summary.json").write_text(
            json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )
        print(json.dumps(summary, indent=2))
        return 2

    cfg = _load(SOURCE / "runtime_evaluation_config.json")
    bars = pd.read_parquet(SOURCE / "scratch" / MID.replace(":", "_") / "bars.parquet")
    profile = DatasetProfileBindingV1(
        dataset_profile=DatasetProfileV1.ECONOMIC_RESEARCH_V1,
        execution_cost_binding=ExecutionCostBindingV1(
            spread_model_version="research_conservative_bps_v1",
            execution_price_observation_source="MODELLED_NOT_OBSERVED",
            conservative_half_spread_bps=5.0,
        ),
        l1_observation_status=L1ObservationStatusV1.EXECUTION_MODEL_BOUND_NOT_OBSERVED,
    )

    event_counts: Counter[str] = Counter()
    counts: Counter[str] = Counter()
    samples: list[dict[str, Any]] = []
    prior_mark: float | None = None

    def hook(**kwargs: Any) -> None:
        nonlocal prior_mark
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
        binding = getattr(se, "semantic_binding", None)
        current_price = float(getattr(binding, "current_price", 0.0) or 0.0)
        trailing = float(getattr(binding, "trailing_anchor", 0.0) or 0.0)
        up_d = float(getattr(binding, "up_distance", 0.0) or 0.0)
        adverse_d = float(getattr(binding, "adverse_exit_distance", 0.0) or 0.0)
        reversal_d = float(getattr(binding, "reversal_distance", 0.0) or 0.0)
        thr = compute_evaluated_thresholds(
            direction=ScopeDirectionState.LONG,
            trailing_anchor=trailing,
            up_distance=up_d,
            adverse_exit_distance=adverse_d,
            reversal_distance=reversal_d,
        )
        bull = current_price >= thr.up_candidate_threshold
        bear = current_price <= thr.downscope_candidate_threshold
        if bull:
            counts["bull_candidate"] += 1
        if bear:
            counts["bear_candidate"] += 1
        if not bull and not bear:
            counts["threshold_miss"] += 1
        if up_d in (120.0, 60.0) or math.isclose(up_d, 120.0):
            counts["legacy_absolute_distance_seen"] += 1

        inter_switch = getattr(inter, "state_switch", None)
        side_before = getattr(inter_switch, "previous_side_state", None) or getattr(
            inter_switch, "side_state", None
        )
        side_after = getattr(inter_switch, "next_side_state", None)
        composition = getattr(inter, "composition_result", None)
        comp_side = getattr(getattr(composition, "selected_side", None), "value", None) or getattr(
            composition, "selected_side", None
        )

        if len(samples) < 12 and (
            bull or bear or (prior_mark is not None and current_price < prior_mark)
        ):
            rel = compute_mv2_research_scope_distances_absolute_from_mark_v1(current_price)
            pp = kwargs.get("price_path")
            samples.append(
                {
                    "instrument": MID,
                    "timestamp": str(kwargs.get("bar_timestamp")),
                    "mark": current_price,
                    "prior_mark": prior_mark,
                    "price_path": repr(tuple(float(x) for x in pp) if pp else None),
                    "up_distance_bps": 100.0,
                    "adverse_to_up_ratio": 0.5,
                    "reversal_to_up_ratio": 0.75,
                    "abs_up_distance": up_d,
                    "abs_adverse_exit_distance": adverse_d,
                    "abs_reversal_distance": reversal_d,
                    "helper_up_distance": rel.up_distance,
                    "bull_candidate": bull,
                    "bear_candidate": bear,
                    "scope_event": event_type,
                    "side_before": side_before,
                    "side_after": side_after,
                    "composition_selected_side": comp_side,
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
        observational_panel_member_instrument_id=MID,
    )
    trades = 0
    if result.backtest_result.trades is not None:
        trades = len(result.backtest_result.trades)

    summary = {
        "ok": True,
        "member": MID,
        "before_noop_count": 2893,
        "before_threshold_miss_count": 2893,
        "before_bull_candidate_count": 0,
        "before_bear_candidate_count": 0,
        "after_event_counts": dict(sorted(event_counts.items())),
        "after_noop_count": int(event_counts.get("noop", 0)),
        "after_threshold_miss_count": int(counts.get("threshold_miss", 0)),
        "after_bull_candidate_count": int(counts.get("bull_candidate", 0)),
        "after_bear_candidate_count": int(counts.get("bear_candidate", 0)),
        "after_bull_event_count": int(
            event_counts.get("upscope_candidate", 0) + event_counts.get("upscope_confirmed", 0)
        ),
        "after_bear_event_count": int(
            event_counts.get("downscope_candidate", 0) + event_counts.get("downscope_confirmed", 0)
        ),
        "legacy_absolute_distance_seen": int(counts.get("legacy_absolute_distance_seen", 0)),
        "trades_opened": trades,
        "hooked_bars": sum(event_counts.values()),
    }
    (EVIDENCE / "probe_summary.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    if samples:
        with (EVIDENCE / "representative_bars.csv").open("w", encoding="utf-8", newline="") as fh:
            writer = csv.DictWriter(fh, fieldnames=list(samples[0].keys()))
            writer.writeheader()
            writer.writerows(samples)
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
