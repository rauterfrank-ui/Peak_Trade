#!/usr/bin/env python3
"""READ-ONLY post-#5337 zero-trade audit probe (evidence-only; no productive mutation)."""

from __future__ import annotations

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
from src.backtest.mv2_research_wiring_v1 import (  # noqa: E402
    MV2_REQUIRED_INSTRUMENT_ID,
    run_mv2_research_backtest_wiring_v1,
)
from src.research.final_research_fleet_v0_versioned_binding_manifest_contract_v0 import (  # noqa: E402
    CANONICAL_INSTRUMENT_ID,
)
from src.research.mv2_zero_trade_per_bar_decision_outcome_diagnostic_v1 import (  # noqa: E402
    aggregate_entry_bar_diagnostics_v1,
    build_observational_snapshot_from_replay_v1,
    classify_entry_bar_snapshot_v1,
    is_strategy_entry_raw_signal_v1,
)
from src.strategies.bollinger import BollingerBandsStrategy  # noqa: E402

EVIDENCE = Path(__file__).resolve().parent
SOURCE = Path(
    "/Users/frnkhrz/Documents/Peak_Trade_runtime_evidence_archive_20260520T161443Z/"
    "research/full_canonical_system_economic_evidence_generation_v1_offline_execution_v0_20260716T015033Z"
)
CONFIG = _REPO / "config/research/mv2_zero_trade_per_bar_decision_outcome_diagnostic_v1.json"


def _load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _bars_path(member_id: str) -> Path:
    scratch = SOURCE / "scratch"
    primary = scratch / member_id.replace(":", "_") / "bars.parquet"
    if primary.is_file():
        return primary
    alt = scratch / "datasets" / member_id.replace(":", "_") / "bars.parquet"
    if alt.is_file():
        return alt
    raise FileNotFoundError(member_id)


def _count_raw_signals(bars: pd.DataFrame, strategy_params: dict[str, Any]) -> Counter:
    strategy = BollingerBandsStrategy(
        bb_period=int(strategy_params.get("bb_period", 20)),
        bb_std=float(strategy_params.get("bb_std", 2.0)),
        entry_threshold=float(strategy_params.get("entry_threshold", 0.95)),
        exit_threshold=float(strategy_params.get("exit_threshold", 0.5)),
    )
    signals = strategy.generate_signals(bars)
    c: Counter = Counter()
    for v in signals.fillna(0).astype(int).tolist():
        c[int(v)] += 1
    return c


def _probe_member(
    *,
    bars: pd.DataFrame,
    cfg: dict[str, Any],
    member_id: str,
    profile: DatasetProfileBindingV1,
) -> dict[str, Any]:
    raw_counts = _count_raw_signals(
        bars, dict(cfg.get("economic_evaluation_v1", {}).get("strategy_params", {}))
    )
    entry_records = []
    all_bar_rows: list[dict[str, Any]] = []
    counters = {
        "raw_entry_hook": 0,
        "agreement_entry": 0,
        "entry_side_none": 0,
        "entry_side_long": 0,
        "entry_side_short": 0,
        "price_path_flat": 0,
        "price_path_up": 0,
        "price_path_down": 0,
        "price_path_missing": 0,
        "side_state": Counter(),
        "next_side_state": Counter(),
        "composition_status": Counter(),
        "composition_selected_side": Counter(),
        "decision_outcome": Counter(),
        "mapped_signal": Counter(),
        "da_bull": Counter(),
        "da_bear": Counter(),
        "suit_bull": Counter(),
        "suit_bear": Counter(),
        "trade_like_enter": 0,
    }

    def _hook(**kwargs: Any) -> None:
        raw = int(kwargs["raw_strategy_signal"])
        material = kwargs.get("agreement_material")
        intermediate = kwargs.get("intermediate")
        price_path = kwargs.get("price_path")
        row: dict[str, Any] = {
            "epoch": int(kwargs["trading_epoch"]),
            "raw": raw,
            "context_id": str(kwargs.get("context_id") or ""),
            "replay_input_built": bool(kwargs["replay_input_built"]),
            "decision_authority_reached": bool(kwargs["decision_authority_reached"]),
            "mapped": int(kwargs["mapped_position_signal"]),
            "decision": kwargs.get("decision_outcome"),
        }
        if material is not None:
            row["event_kind"] = getattr(
                getattr(material, "event_kind", None), "value", material.event_kind
            )
            entry_side = getattr(material, "entry_side", None)
            row["entry_side"] = getattr(entry_side, "value", entry_side)
            row["cycle"] = int(getattr(material, "cycle_signal_value", 0) or 0)
            if str(row["event_kind"]) == "ENTRY":
                counters["agreement_entry"] += 1
            if str(row.get("entry_side")) == "NONE":
                counters["entry_side_none"] += 1
            elif str(row.get("entry_side")) == "LONG":
                counters["entry_side_long"] += 1
            elif str(row.get("entry_side")) == "SHORT":
                counters["entry_side_short"] += 1
        if price_path is None:
            counters["price_path_missing"] += 1
            row["price_path_class"] = "missing"
        else:
            path = tuple(float(x) for x in price_path)
            row["price_path"] = path
            if len(path) < 2 or path[0] == path[-1]:
                counters["price_path_flat"] += 1
                row["price_path_class"] = "flat"
            elif path[-1] > path[0]:
                counters["price_path_up"] += 1
                row["price_path_class"] = "up"
            else:
                counters["price_path_down"] += 1
                row["price_path_class"] = "down"
        if intermediate is not None:
            switch = getattr(intermediate, "state_switch", None)
            if switch is not None:
                nxt = str(getattr(switch, "next_side_state", ""))
                counters["next_side_state"][nxt] += 1
                row["next_side_state"] = nxt
            comp = getattr(intermediate, "composition_result", None)
            if comp is not None:
                status = str(
                    getattr(
                        getattr(comp, "composition_status", None), "value", comp.composition_status
                    )
                )
                side = str(
                    getattr(getattr(comp, "selected_side", None), "value", comp.selected_side)
                )
                counters["composition_status"][status] += 1
                counters["composition_selected_side"][side] += 1
                row["composition_status"] = status
                row["composition_selected_side"] = side
            for key, attr in (
                ("da_bull", "bull_assessment"),
                ("da_bear", "bear_assessment"),
                ("suit_bull", "bull_suitability"),
                ("suit_bear", "bear_suitability"),
            ):
                obj = getattr(intermediate, attr, None)
                st = str(
                    getattr(getattr(obj, "status", None), "value", getattr(obj, "status", None))
                )
                counters[key][st] += 1
                row[key] = st
        decision = kwargs.get("decision_outcome")
        counters["decision_outcome"][str(decision)] += 1
        counters["mapped_signal"][int(kwargs["mapped_position_signal"])] += 1
        if decision in {"enter_long", "enter_short"}:
            counters["trade_like_enter"] += 1
        all_bar_rows.append(row)

        if not is_strategy_entry_raw_signal_v1(raw):
            return
        counters["raw_entry_hook"] += 1
        snap = build_observational_snapshot_from_replay_v1(
            trading_epoch=int(kwargs["trading_epoch"]),
            bar_timestamp=str(kwargs["bar_timestamp"]),
            instrument_id=str(kwargs["instrument_id"]),
            panel_member_instrument_id=str(kwargs["panel_member_instrument_id"]),
            raw_strategy_signal=raw,
            warmup_status=str(kwargs["warmup_status"]),
            warmup_skipped=bool(kwargs["warmup_skipped"]),
            context_id=str(kwargs["context_id"]),
            context_input_digest=str(kwargs["context_input_digest"]),
            agreement_material=material,
            intermediate=intermediate,
            decision_outcome=kwargs.get("decision_outcome"),
            evidence_reason_codes=tuple(kwargs.get("evidence_reason_codes") or ()),
            mapped_position_signal=int(kwargs["mapped_position_signal"]),
            price_path=kwargs.get("price_path"),
            regime_id=kwargs.get("regime_id"),
            eligible_strategy_count=kwargs.get("eligible_strategy_count"),
            regime_wildcard_matched=kwargs.get("regime_wildcard_matched"),
            fail_reasons=tuple(kwargs.get("fail_reasons") or ()),
            replay_input_built=bool(kwargs["replay_input_built"]),
            decision_authority_reached=bool(kwargs["decision_authority_reached"]),
        )
        entry_records.append(classify_entry_bar_snapshot_v1(snap))

    result = run_mv2_research_backtest_wiring_v1(
        bars,
        strategy_id=str(cfg["economic_evaluation_v1"]["strategy_id"]),
        cfg=cfg,
        instrument_id=CANONICAL_INSTRUMENT_ID,
        profile_binding=profile,
        observational_bar_hook=_hook,
        observational_panel_member_instrument_id=member_id,
    )
    trade_count = int(getattr(getattr(result, "stats", None), "trades", 0) or 0)
    if hasattr(result, "trades"):
        try:
            trade_count = max(trade_count, int(len(result.trades)))
        except Exception:  # noqa: BLE001
            pass
    # BacktestResult often exposes n_trades / trade_count variants
    for attr in ("n_trades", "trade_count", "num_trades"):
        if hasattr(result, attr):
            try:
                trade_count = max(trade_count, int(getattr(result, attr) or 0))
            except Exception:  # noqa: BLE001
                pass
    if hasattr(result, "to_dict"):
        try:
            d = result.to_dict()
            for key in ("trades", "n_trades", "trade_count"):
                if key in d and d[key] is not None:
                    if isinstance(d[key], list):
                        trade_count = max(trade_count, len(d[key]))
                    else:
                        trade_count = max(trade_count, int(d[key]))
        except Exception:  # noqa: BLE001
            pass

    agg = aggregate_entry_bar_diagnostics_v1(
        entry_records, expected_entry_count=int(raw_counts.get(1, 0))
    )
    agg_dict = agg.to_dict()
    agg_dict.pop("records", None)

    # First value-loss on ENTRY bars in epoch order
    first_loss = None
    for rec in entry_records:
        if rec.first_failed_stage != "none":
            first_loss = {
                "panel_member": member_id,
                "bar_index": rec.bar_index,
                "bar_timestamp": rec.bar_timestamp,
                "first_failed_stage": rec.first_failed_stage,
                "taxonomy_outcome": rec.taxonomy_outcome,
                "explicit_block_reason": rec.explicit_block_reason,
                "price_path": list(rec.price_path) if rec.price_path else None,
                "composition_outcome": rec.composition_outcome,
                "directional_agreement_outcome": rec.directional_agreement_outcome,
                "suitability_outcome": rec.suitability_outcome,
                "final_decision_outcome": rec.final_decision_outcome,
                "mapped_position_signal": rec.mapped_position_signal,
                "entry_side_on_material": "NONE",  # Bollinger OBL_B07
            }
            break

    return {
        "member_id": member_id,
        "raw_signal_counts": dict(sorted((str(k), v) for k, v in raw_counts.items())),
        "hook_counters": {
            k: (dict(v) if isinstance(v, Counter) else v) for k, v in counters.items()
        },
        "entry_aggregate": agg_dict,
        "trade_count_observed": trade_count,
        "first_entry_value_loss": first_loss,
        "canonical_wiring_instrument_id": MV2_REQUIRED_INSTRUMENT_ID,
        "entry_record_count": len(entry_records),
        "all_bar_count_hooked": len(all_bar_rows),
    }


def main() -> int:
    config = _load(CONFIG)
    cfg = _load(SOURCE / "runtime_evaluation_config.json")
    eval_id = str(config["evaluation_instrument_id"])
    max_members = int(sys.argv[1]) if len(sys.argv) > 1 else 8

    binding = _load(_REPO / str(config["binding_ref"]))
    eligible = (
        binding.get("binding", {}).get("instrument_binding", {}).get("eligible_instrument_ids")
        or []
    )
    panel_ids = [str(x) for x in eligible][:max_members]
    if eval_id not in panel_ids:
        panel_ids = [eval_id] + panel_ids
        panel_ids = list(dict.fromkeys(panel_ids))[:max_members]

    profile = DatasetProfileBindingV1(
        dataset_profile=DatasetProfileV1.ECONOMIC_RESEARCH_V1,
        execution_cost_binding=ExecutionCostBindingV1(
            spread_model_version="research_conservative_bps_v1",
            execution_price_observation_source="MODELLED_NOT_OBSERVED",
            conservative_half_spread_bps=5.0,
        ),
        l1_observation_status=L1ObservationStatusV1.EXECUTION_MODEL_BOUND_NOT_OBSERVED,
    )

    member_results = []
    global_first_loss = None
    stage_counts: Counter = Counter()
    composition_side: Counter = Counter()
    next_side: Counter = Counter()
    decision_counts: Counter = Counter()
    raw_total: Counter = Counter()
    trade_total = 0

    for mid in panel_ids:
        bars = pd.read_parquet(_bars_path(mid))
        result = _probe_member(bars=bars, cfg=cfg, member_id=mid, profile=profile)
        member_results.append(result)
        for k, v in result["raw_signal_counts"].items():
            raw_total[k] += int(v)
        trade_total += int(result["trade_count_observed"])
        for stage, n in result["entry_aggregate"].get("first_failed_stage_counts", {}).items():
            stage_counts[stage] += int(n)
        hc = result["hook_counters"]
        for k, v in hc.get("composition_selected_side", {}).items():
            composition_side[k] += int(v)
        for k, v in hc.get("next_side_state", {}).items():
            next_side[k] += int(v)
        for k, v in hc.get("decision_outcome", {}).items():
            decision_counts[k] += int(v)
        if global_first_loss is None and result["first_entry_value_loss"] is not None:
            global_first_loss = result["first_entry_value_loss"]
        print(
            json.dumps(
                {
                    "member": mid,
                    "raw_entry": result["raw_signal_counts"].get("1", 0),
                    "dominant_stage": result["entry_aggregate"].get("dominant_first_failed_stage"),
                    "trade_count": result["trade_count_observed"],
                },
                sort_keys=True,
            ),
            flush=True,
        )

    summary = {
        "base_sha_expected": "a55c4000f33269a98107fd1294b1c9ba82433cad",
        "panel_members_probed": panel_ids,
        "raw_signal_counts_total": dict(sorted(raw_total.items())),
        "raw_signal_nonzero": any(int(k) != 0 and int(v) > 0 for k, v in raw_total.items()),
        "first_failed_stage_counts": dict(sorted(stage_counts.items())),
        "dominant_first_failed_stage": (
            stage_counts.most_common(1)[0][0] if stage_counts else None
        ),
        "composition_selected_side_counts": dict(sorted(composition_side.items())),
        "next_side_state_counts": dict(sorted(next_side.items())),
        "decision_outcome_counts": dict(sorted(decision_counts.items())),
        "trade_count_total_observed": trade_total,
        "global_first_entry_value_loss": global_first_loss,
        "members": member_results,
    }
    (EVIDENCE / "probe_summary.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps({"ok": True, "summary_path": str(EVIDENCE / "probe_summary.json")}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
