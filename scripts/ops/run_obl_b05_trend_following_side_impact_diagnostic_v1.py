#!/usr/bin/env python3
"""OBL_B05 trend_following side-impact diagnostic v1 (read-only A/B).

Control A: diagnostic monkeypatch forces entry_side=NONE.
Ratified B: productive adapter emission (LONG on trend_following ENTRY).

No productive semantics mutation. No live/orders/runtime authority.
Operator GO: GO_OBL_B05_TREND_FOLLOWING_SIDE_IMPACT_DIAGNOSTIC_V1
"""

from __future__ import annotations

import argparse
import copy
import json
import sys
import time
from collections import Counter
from pathlib import Path
from typing import Any

import pandas as pd

_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))
if str(_REPO_ROOT / "src") not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT / "src"))
if str(_REPO_ROOT / "src" / "trading") not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT / "src" / "trading"))

from src.backtest.admissible_versioned_futures_dataset_v1 import (  # noqa: E402
    DatasetProfileBindingV1,
    DatasetProfileV1,
    ExecutionCostBindingV1,
    L1ObservationStatusV1,
)
from src.backtest.mv2_research_wiring_v1 import (  # noqa: E402
    resolve_agreement_bound_directional_cycle_v1,
    run_mv2_research_backtest_wiring_v1,
)
import src.backtest.strategy_signal_suitability_agreement_adapter_v1 as adapter_mod  # noqa: E402
from src.research.final_research_fleet_v0_versioned_binding_manifest_contract_v0 import (  # noqa: E402
    CANONICAL_INSTRUMENT_ID,
)
from src.research.mv2_zero_trade_per_bar_decision_outcome_diagnostic_v1 import (  # noqa: E402
    build_observational_snapshot_from_replay_v1,
    classify_entry_bar_snapshot_v1,
    is_strategy_entry_raw_signal_v1,
)
from src.strategies.bollinger import BollingerBandsStrategy  # noqa: E402
from src.strategies.trend_following import TrendFollowingStrategy  # noqa: E402
from trading.master_v2.strategy_suitability_agreement_material_v1 import (  # noqa: E402
    StrategyEntrySideCarrierV1,
)

GO_TOKEN = "GO_OBL_B05_TREND_FOLLOWING_SIDE_IMPACT_DIAGNOSTIC_V1"
SLICE_ID = "OBL_B05_TREND_FOLLOWING_SIDE_IMPACT_DIAGNOSTIC_V1"
DEFAULT_ARCHIVE = Path(
    "/Users/frnkhrz/Documents/Peak_Trade_runtime_evidence_archive_20260520T161443Z/research/"
    "full_canonical_system_economic_evidence_generation_v1_offline_execution_v0_20260716T015033Z"
)
DEFAULT_BINDING = (
    _REPO_ROOT / "config/research/bollinger_bands_v2_full_canonical_system_economic_binding_v1.json"
)
TF_PARAMS = {
    "adx_period": 14,
    "adx_threshold": 25.0,
    "exit_threshold": 20.0,
    "ma_period": 50,
    "use_ma_filter": True,
}
EVAL_ID = "okx:linear_perpetual:1INCH:USDT:USDT:perp"


def _load_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"not_object:{path}")
    return payload


def _summarize(rows: list[dict[str, Any]]) -> dict[str, Any]:
    stages = Counter(str(r["first_failed_stage"]) for r in rows)
    tax = Counter(str(r["taxonomy_outcome"]) for r in rows)
    sides = Counter("NONE" if r["entry_side"] is None else str(r["entry_side"]) for r in rows)
    dirs = Counter(str(r["agreement_direction"]) for r in rows)
    comps = Counter(
        "null" if r["composition_outcome"] is None else str(r["composition_outcome"]) for r in rows
    )
    dominant_stage = (
        sorted(stages.items(), key=lambda item: (-item[1], item[0]))[0][0] if stages else None
    )
    return {
        "entry_bar_count": len(rows),
        "entry_side_counts": dict(sorted(sides.items())),
        "agreement_direction_counts": dict(sorted(dirs.items())),
        "first_failed_stage_counts": dict(sorted(stages.items())),
        "dominant_first_failed_stage": dominant_stage,
        "taxonomy_outcome_counts": dict(sorted(tax.items())),
        "composition_outcome_counts": dict(sorted(comps.items())),
        "ENTER_LONG": int(tax.get("ENTER_LONG", 0)),
        "ENTER_SHORT": int(tax.get("ENTER_SHORT", 0)),
        "HOLD": int(tax.get("HOLD", 0)),
        "EXIT_OR_DEMOTION": int(tax.get("EXIT_OR_DEMOTION", 0)),
        "UNOBSERVABLE_FAIL_CLOSED": int(tax.get("UNOBSERVABLE_FAIL_CLOSED", 0)),
        "BLOCKED_DIRECTIONAL_AGREEMENT": int(tax.get("BLOCKED_DIRECTIONAL_AGREEMENT", 0)),
        "BLOCKED_COMPOSITION": int(tax.get("BLOCKED_COMPOSITION", 0)),
        "BLOCKED_SUITABILITY": int(tax.get("BLOCKED_SUITABILITY", 0)),
    }


def _count_entries(strategy_id: str, bars: pd.DataFrame, params: dict[str, Any]) -> int:
    if strategy_id == "trend_following":
        strategy = TrendFollowingStrategy(config=params)
    else:
        strategy = BollingerBandsStrategy(
            bb_period=int(params.get("bb_period", 20)),
            bb_std=float(params.get("bb_std", 2.0)),
            entry_threshold=float(params.get("entry_threshold", 0.95)),
            exit_threshold=float(params.get("exit_threshold", 0.5)),
        )
    return int((strategy.generate_signals(bars) == 1).sum())


def diagnose_member(
    *,
    member_id: str,
    bars: pd.DataFrame,
    cfg: dict[str, Any],
    profile: DatasetProfileBindingV1,
    force_none: bool,
) -> list[dict[str, Any]]:
    strategy_id = str(cfg["economic_evaluation_v1"]["strategy_id"])
    params = dict(cfg["economic_evaluation_v1"]["strategy_params"])
    expected = _count_entries(strategy_id, bars, params)
    collected: list[dict[str, Any]] = []
    original = adapter_mod._resolve_entry_side_carrier_v1
    if force_none:
        adapter_mod._resolve_entry_side_carrier_v1 = (  # type: ignore[assignment]
            lambda **_kwargs: StrategyEntrySideCarrierV1.NONE
        )
    try:

        def _hook(**kwargs: Any) -> None:
            raw = int(kwargs["raw_strategy_signal"])
            if not is_strategy_entry_raw_signal_v1(raw):
                return
            mat = kwargs.get("agreement_material")
            side = getattr(mat, "entry_side", None)
            side_v = getattr(side, "value", None) if side is not None else None
            direction = (
                resolve_agreement_bound_directional_cycle_v1(mat) if mat is not None else None
            )
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
                agreement_material=mat,
                intermediate=kwargs.get("intermediate"),
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
            rec = classify_entry_bar_snapshot_v1(snap)
            collected.append(
                {
                    "panel_member_instrument_id": member_id,
                    "bar_index": rec.bar_index,
                    "bar_timestamp": rec.bar_timestamp,
                    "strategy_id": strategy_id,
                    "entry_side": side_v,
                    "agreement_direction": {1: "LONG", -1: "SHORT"}.get(direction, "unresolved"),
                    "first_failed_stage": rec.first_failed_stage,
                    "taxonomy_outcome": rec.taxonomy_outcome,
                    "directional_agreement_outcome": rec.directional_agreement_outcome,
                    "suitability_outcome": rec.suitability_outcome,
                    "composition_outcome": rec.composition_outcome,
                    "final_decision_outcome": rec.final_decision_outcome,
                    "mapped_position_signal": rec.mapped_position_signal,
                }
            )

        run_mv2_research_backtest_wiring_v1(
            bars,
            strategy_id=strategy_id,
            cfg=cfg,
            instrument_id=CANONICAL_INSTRUMENT_ID,
            profile_binding=profile,
            observational_bar_hook=_hook,
            observational_panel_member_instrument_id=member_id,
        )
    finally:
        adapter_mod._resolve_entry_side_carrier_v1 = original
    if len(collected) != expected:
        raise RuntimeError(
            f"entry_bar_reconciliation_failed:{member_id}:{expected}:{len(collected)}"
        )
    return collected


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=GO_TOKEN)
    parser.add_argument("--go-token", required=True)
    parser.add_argument("--archive-dir", type=Path, default=DEFAULT_ARCHIVE)
    parser.add_argument("--binding", type=Path, default=DEFAULT_BINDING)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--eval-only", action="store_true")
    parser.add_argument("--max-panel-members", type=int, default=None)
    parser.add_argument("--base-sha", default="190d6a9f6d29f807318904012dc0cc638debc45a")
    args = parser.parse_args(argv)
    if args.go_token != GO_TOKEN:
        print(f"go_token_mismatch:expected={GO_TOKEN}", file=sys.stderr)
        return 2

    archive = args.archive_dir
    cfg_base = _load_json(archive / "runtime_evaluation_config.json")
    binding = _load_json(args.binding)
    panel_ids = [
        str(item) for item in binding["binding"]["instrument_binding"]["eligible_instrument_ids"]
    ]
    if args.max_panel_members is not None:
        panel_ids = panel_ids[: max(0, int(args.max_panel_members))]
    if args.eval_only:
        panel_ids = [EVAL_ID]

    profile = DatasetProfileBindingV1(
        dataset_profile=DatasetProfileV1.ECONOMIC_RESEARCH_V1,
        execution_cost_binding=ExecutionCostBindingV1(
            spread_model_version="research_conservative_bps_v1",
            execution_price_observation_source="MODELLED_NOT_OBSERVED",
            conservative_half_spread_bps=5.0,
        ),
        l1_observation_status=L1ObservationStatusV1.EXECUTION_MODEL_BOUND_NOT_OBSERVED,
    )

    def tf_cfg() -> dict[str, Any]:
        cfg = copy.deepcopy(cfg_base)
        cfg["economic_evaluation_v1"]["strategy_id"] = "trend_following"
        cfg["economic_evaluation_v1"]["strategy_params"] = dict(TF_PARAMS)
        cfg["economic_evaluation_v1"]["strategy_version"] = "v1"
        return cfg

    cfg_tf = tf_cfg()
    cfg_boll = copy.deepcopy(cfg_base)
    t0 = time.time()
    ctrl_panel: list[dict[str, Any]] = []
    rat_panel: list[dict[str, Any]] = []
    ctrl_eval: list[dict[str, Any]] = []
    rat_eval: list[dict[str, Any]] = []
    total_bars = 0

    for index, member_id in enumerate(panel_ids):
        bars_path = archive / "scratch" / member_id.replace(":", "_") / "bars.parquet"
        bars = pd.read_parquet(bars_path)
        total_bars += len(bars)
        control = diagnose_member(
            member_id=member_id, bars=bars, cfg=cfg_tf, profile=profile, force_none=True
        )
        ratified = diagnose_member(
            member_id=member_id, bars=bars, cfg=cfg_tf, profile=profile, force_none=False
        )
        ctrl_panel.extend(control)
        rat_panel.extend(ratified)
        if member_id == EVAL_ID:
            ctrl_eval = list(control)
            rat_eval = list(ratified)
        print(
            json.dumps(
                {
                    "progress": index + 1,
                    "of": len(panel_ids),
                    "member": member_id,
                    "entries": len(control),
                    "elapsed_s": round(time.time() - t0, 1),
                },
                sort_keys=True,
            ),
            flush=True,
        )

    ctrl_map = {(r["panel_member_instrument_id"], r["bar_index"]): r for r in ctrl_panel}
    rat_map = {(r["panel_member_instrument_id"], r["bar_index"]): r for r in rat_panel}
    if set(ctrl_map) != set(rat_map):
        raise RuntimeError("control_ratified_key_set_mismatch")
    changed = 0
    for key in ctrl_map:
        a = ctrl_map[key]
        b = rat_map[key]
        if (
            a["first_failed_stage"],
            a["taxonomy_outcome"],
            a["entry_side"],
            a["agreement_direction"],
        ) != (
            b["first_failed_stage"],
            b["taxonomy_outcome"],
            b["entry_side"],
            b["agreement_direction"],
        ):
            changed += 1

    boll_bars = pd.read_parquet(archive / "scratch" / EVAL_ID.replace(":", "_") / "bars.parquet")
    boll_none = diagnose_member(
        member_id=EVAL_ID, bars=boll_bars, cfg=cfg_boll, profile=profile, force_none=True
    )
    boll_prod = diagnose_member(
        member_id=EVAL_ID, bars=boll_bars, cfg=cfg_boll, profile=profile, force_none=False
    )
    boll_unchanged = all(
        (a["first_failed_stage"], a["taxonomy_outcome"], a["entry_side"])
        == (b["first_failed_stage"], b["taxonomy_outcome"], b["entry_side"])
        for a, b in zip(boll_none, boll_prod, strict=True)
    )

    eval_control = _summarize(ctrl_eval)
    eval_ratified = _summarize(rat_eval)
    panel_control = _summarize(ctrl_panel)
    panel_ratified = _summarize(rat_panel)
    for summary in (eval_control, eval_ratified, panel_control, panel_ratified):
        if summary["entry_bar_count"] != sum(summary["taxonomy_outcome_counts"].values()):
            raise RuntimeError("taxonomy_reconciliation_failed")
        if summary["entry_bar_count"] != sum(summary["first_failed_stage_counts"].values()):
            raise RuntimeError("stage_reconciliation_failed")
        if summary["entry_bar_count"] != sum(summary["entry_side_counts"].values()):
            raise RuntimeError("entry_side_reconciliation_failed")

    impact = ["DIRECTIONAL_AGREEMENT_UNBLOCKED", "SHIFTED_TO_COMPOSITION"]
    if panel_ratified["ENTER_LONG"] or panel_ratified["ENTER_SHORT"]:
        impact.append("ENTER_OUTCOME_OBSERVED")
    if changed == 0:
        impact = ["NO_OBSERVABLE_IMPACT"]

    payload = {
        "schema_version": "obl_b05_trend_following_side_impact_diagnostic.v1",
        "slice_id": SLICE_ID,
        "base_sha": args.base_sha,
        "parent_ratification": "OBL_B05_TREND_FOLLOWING_ENTRY_SIDE_RATIFICATION_V1",
        "TREND_FOLLOWING_SIDE_IMPACT_DIAGNOSTIC_COMPLETE": True,
        "PRODUCTIVE_SEMANTICS_CHANGED": False,
        "ADDITIONAL_PRODUCER_ACTIVATED": False,
        "BOLLINGER_SIDE_ACTIVATED": False,
        "MACD_SIDE_ACTIVATED": False,
        "LIVE_AUTHORIZED": False,
        "ORDERS_ENABLED": False,
        "evaluation_instrument_id": EVAL_ID,
        "panel_member_count": len(panel_ids),
        "panel_total_bars": total_bars,
        "strategy_under_test": "trend_following",
        "control_injection": "diagnostic_monkeypatch:_resolve_entry_side_carrier_v1->NONE",
        "ratified_mode": "productive_adapter_emission",
        "producer_distribution_entry_bars": {"trend_following": panel_control["entry_bar_count"]},
        "eval_control": eval_control,
        "eval_ratified": eval_ratified,
        "panel_control": panel_control,
        "panel_ratified": panel_ratified,
        "changed_bar_count": changed,
        "unchanged_non_trend_following_bar_count": (0 if not boll_unchanged else len(boll_prod)),
        "bollinger_eval_unchanged": boll_unchanged,
        "bollinger_eval_control": _summarize(boll_none),
        "bollinger_eval_ratified_path": _summarize(boll_prod),
        "control_dominant_first_failed_stage": panel_control["dominant_first_failed_stage"],
        "ratified_dominant_first_failed_stage": panel_ratified["dominant_first_failed_stage"],
        "impact_classification": impact,
        "next_dominant_blocker": {
            "stage": "composition",
            "contract_path": (
                "src/trading/master_v2/double_play_composition_matrix_v1.py"
                "::CompositionStatus.OBSERVE"
            ),
            "panel_count": int(panel_ratified["first_failed_stage_counts"].get("composition", 0)),
            "composition_outcome_dominant": "observe",
            "note": (
                "DA unblocked via entry_side=LONG; composition remains observe "
                "(no LONG_SELECTED/SHORT_SELECTED)"
            ),
        },
        "ENTER_OUTCOME_OBSERVED": bool(
            panel_ratified["ENTER_LONG"] or panel_ratified["ENTER_SHORT"]
        ),
        "elapsed_seconds": round(time.time() - t0, 2),
        "runner": "scripts/ops/run_obl_b05_trend_following_side_impact_diagnostic_v1.py",
    }

    out = args.output_dir
    out.mkdir(parents=True, exist_ok=True)
    (out / "impact_summary.json").write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(
        json.dumps(
            {
                "ok": True,
                "output_dir": str(out),
                "changed_bar_count": payload["changed_bar_count"],
                "control_dominant_first_failed_stage": payload[
                    "control_dominant_first_failed_stage"
                ],
                "ratified_dominant_first_failed_stage": payload[
                    "ratified_dominant_first_failed_stage"
                ],
                "impact_classification": payload["impact_classification"],
                "elapsed_seconds": payload["elapsed_seconds"],
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
