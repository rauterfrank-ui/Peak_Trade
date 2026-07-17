#!/usr/bin/env python3
"""OBL_B05 Bollinger long-semantic decision + quantitative baseline v1.

Read-only / semantics-free:
- Decision C (CONTRACT_REMAINS_AMBIGUOUS) — no productive entry_side activation.
- Quantitative Bollinger ENTRY/EXIT baseline on canonical panel archive.
- SHORT reference via positional mean_reversion_channel on identical bars/scope.

Operator GO: GO_OBL_B05_BOLLINGER_LONG_SEMANTIC_DECISION_AND_QUANTITATIVE_BASELINE_V1
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
from src.research.final_research_fleet_v0_versioned_binding_manifest_contract_v0 import (  # noqa: E402
    CANONICAL_INSTRUMENT_ID,
)
from src.research.mv2_zero_trade_per_bar_decision_outcome_diagnostic_v1 import (  # noqa: E402
    build_observational_snapshot_from_replay_v1,
    classify_entry_bar_snapshot_v1,
    is_strategy_entry_raw_signal_v1,
)
from src.strategies.bollinger import BollingerBandsStrategy  # noqa: E402
from src.strategies.rsi_reversion import RsiReversionStrategy  # noqa: E402

GO_TOKEN = "GO_OBL_B05_BOLLINGER_LONG_SEMANTIC_DECISION_AND_QUANTITATIVE_BASELINE_V1"
SLICE_ID = "OBL_B05_BOLLINGER_LONG_SEMANTIC_DECISION_AND_QUANTITATIVE_BASELINE_V1"
DEFAULT_ARCHIVE = Path(
    "/Users/frnkhrz/Documents/Peak_Trade_runtime_evidence_archive_20260520T161443Z/research/"
    "full_canonical_system_economic_evidence_generation_v1_offline_execution_v0_20260716T015033Z"
)
DEFAULT_BINDING = (
    _REPO_ROOT / "config/research/bollinger_bands_v2_full_canonical_system_economic_binding_v1.json"
)
EVAL_ID = "okx:linear_perpetual:1INCH:USDT:USDT:perp"
# POSITIONAL_LS SHORT reference (same panel bars; documented strategy overlay).
SHORT_REF_STRATEGY_ID = "rsi_reversion"
SHORT_REF_PARAMS = {
    "rsi_window": 14,
    "lower": 30.0,
    "upper": 70.0,
}


def _load_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"not_object:{path}")
    return payload


def _summarize_entry_rows(rows: list[dict[str, Any]]) -> dict[str, Any]:
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
        "BLOCKED_WARMUP": int(tax.get("BLOCKED_WARMUP", 0)),
    }


def _event_counts_from_signals(signals: pd.Series) -> dict[str, int]:
    values = signals.fillna(0).astype(int)
    return {
        "total_bars": int(len(values)),
        "entry_plus_one": int((values == 1).sum()),
        "exit_minus_one": int((values == -1).sum()),
        "neutral_zero": int((values == 0).sum()),
    }


def _bollinger_signals(bars: pd.DataFrame, params: dict[str, Any]) -> pd.Series:
    strategy = BollingerBandsStrategy(
        bb_period=int(params.get("bb_period", 20)),
        bb_std=float(params.get("bb_std", 2.0)),
        entry_threshold=float(params.get("entry_threshold", 0.95)),
        exit_threshold=float(params.get("exit_threshold", 0.5)),
    )
    return strategy.generate_signals(bars)


def _short_ref_signals(bars: pd.DataFrame, params: dict[str, Any]) -> pd.Series:
    strategy = RsiReversionStrategy(
        rsi_window=int(params.get("rsi_window", 14)),
        lower=float(params.get("lower", 30.0)),
        upper=float(params.get("upper", 70.0)),
    )
    return strategy.generate_signals(bars)


def diagnose_raw_ones(
    *,
    member_id: str,
    bars: pd.DataFrame,
    cfg: dict[str, Any],
    profile: DatasetProfileBindingV1,
) -> list[dict[str, Any]]:
    """Collect MV2 taxonomy for raw strategy signal == +1 (ENTRY or positional long)."""
    strategy_id = str(cfg["economic_evaluation_v1"]["strategy_id"])
    params = dict(cfg["economic_evaluation_v1"]["strategy_params"])
    if strategy_id == "bollinger_bands":
        expected = int((_bollinger_signals(bars, params) == 1).sum())
    elif strategy_id == SHORT_REF_STRATEGY_ID:
        expected = int((_short_ref_signals(bars, params) == 1).sum())
    else:
        raise ValueError(f"unsupported_strategy:{strategy_id}")
    collected: list[dict[str, Any]] = []

    def _hook(**kwargs: Any) -> None:
        raw = int(kwargs["raw_strategy_signal"])
        if not is_strategy_entry_raw_signal_v1(raw):
            return
        mat = kwargs.get("agreement_material")
        side = getattr(mat, "entry_side", None)
        side_v = getattr(side, "value", None) if side is not None else None
        event_kind = getattr(getattr(mat, "event_kind", None), "value", None)
        direction = resolve_agreement_bound_directional_cycle_v1(mat) if mat is not None else None
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
                "raw_signal": raw,
                "event_kind": event_kind,
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
    if len(collected) != expected:
        raise RuntimeError(
            f"entry_bar_reconciliation_failed:{member_id}:{strategy_id}:{expected}:{len(collected)}"
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
    parser.add_argument("--base-sha", default="8ed59484959504e7d477dc9e8d4adedd2ec022b0")
    args = parser.parse_args(argv)
    if args.go_token != GO_TOKEN:
        print(f"go_token_mismatch:expected={GO_TOKEN}", file=sys.stderr)
        return 2

    archive = args.archive_dir
    cfg_boll = _load_json(archive / "runtime_evaluation_config.json")
    if str(cfg_boll["economic_evaluation_v1"]["strategy_id"]) != "bollinger_bands":
        raise RuntimeError("archive_strategy_not_bollinger_bands")
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

    cfg_short = copy.deepcopy(cfg_boll)
    cfg_short["economic_evaluation_v1"]["strategy_id"] = SHORT_REF_STRATEGY_ID
    cfg_short["economic_evaluation_v1"]["strategy_params"] = dict(SHORT_REF_PARAMS)
    cfg_short["economic_evaluation_v1"]["strategy_version"] = "v1"

    t0 = time.time()
    boll_params = dict(cfg_boll["economic_evaluation_v1"]["strategy_params"])
    event_panel = Counter()
    short_event_panel = Counter()
    boll_entry_rows: list[dict[str, Any]] = []
    short_long_entry_rows: list[dict[str, Any]] = []
    boll_eval_rows: list[dict[str, Any]] = []
    short_eval_long_rows: list[dict[str, Any]] = []
    total_bars = 0
    short_minus_one_panel = 0
    short_minus_one_eval = 0

    for index, member_id in enumerate(panel_ids):
        bars_path = archive / "scratch" / member_id.replace(":", "_") / "bars.parquet"
        bars = pd.read_parquet(bars_path)
        total_bars += len(bars)

        boll_sig = _bollinger_signals(bars, boll_params)
        boll_ev = _event_counts_from_signals(boll_sig)
        for key in ("total_bars", "entry_plus_one", "exit_minus_one", "neutral_zero"):
            event_panel[key] += boll_ev[key]

        short_sig = _short_ref_signals(bars, SHORT_REF_PARAMS)
        short_ev = _event_counts_from_signals(short_sig)
        for key in ("total_bars", "entry_plus_one", "exit_minus_one", "neutral_zero"):
            short_event_panel[key] += short_ev[key]
        short_minus_one_panel += int(short_ev["exit_minus_one"])
        # For POSITIONAL_LS, -1 is SHORT entry (not EXIT). Track explicitly.
        if member_id == EVAL_ID:
            short_minus_one_eval = int(short_ev["exit_minus_one"])

        boll_rows = diagnose_raw_ones(member_id=member_id, bars=bars, cfg=cfg_boll, profile=profile)
        short_rows = diagnose_raw_ones(
            member_id=member_id, bars=bars, cfg=cfg_short, profile=profile
        )
        boll_entry_rows.extend(boll_rows)
        short_long_entry_rows.extend(short_rows)
        if member_id == EVAL_ID:
            boll_eval_rows = list(boll_rows)
            short_eval_long_rows = list(short_rows)

        print(
            json.dumps(
                {
                    "progress": index + 1,
                    "of": len(panel_ids),
                    "member": member_id,
                    "bollinger_entry": len(boll_rows),
                    "bollinger_exit": boll_ev["exit_minus_one"],
                    "rsi_plus_one": len(short_rows),
                    "rsi_minus_one_short": short_ev["exit_minus_one"],
                    "elapsed_s": round(time.time() - t0, 1),
                },
                sort_keys=True,
            ),
            flush=True,
        )

    boll_panel_summary = _summarize_entry_rows(boll_entry_rows)
    boll_eval_summary = _summarize_entry_rows(boll_eval_rows)
    short_plus_panel = _summarize_entry_rows(short_long_entry_rows)
    short_plus_eval = _summarize_entry_rows(short_eval_long_rows)

    for summary in (boll_panel_summary, boll_eval_summary, short_plus_panel, short_plus_eval):
        if summary["entry_bar_count"] != sum(summary["taxonomy_outcome_counts"].values()):
            raise RuntimeError("taxonomy_reconciliation_failed")
        if summary["entry_bar_count"] != sum(summary["first_failed_stage_counts"].values()):
            raise RuntimeError("stage_reconciliation_failed")
        if summary["entry_bar_count"] != sum(summary["entry_side_counts"].values()):
            raise RuntimeError("entry_side_reconciliation_failed")

    if event_panel["entry_plus_one"] != boll_panel_summary["entry_bar_count"]:
        raise RuntimeError("bollinger_entry_event_vs_mv2_mismatch")
    if event_panel["total_bars"] != total_bars:
        raise RuntimeError("total_bars_mismatch")

    # Invariants for decision C / bollinger
    if boll_panel_summary["entry_side_counts"].get("LONG", 0) != 0:
        raise RuntimeError("bollinger_long_side_unexpected")
    if boll_panel_summary["entry_side_counts"].get("SHORT", 0) != 0:
        raise RuntimeError("bollinger_short_side_unexpected")
    if boll_panel_summary["agreement_direction_counts"].get("SHORT", 0) != 0:
        raise RuntimeError("bollinger_agreement_short_unexpected")

    payload = {
        "schema_version": "obl_b05_bollinger_long_semantic_decision.v1",
        "slice_id": SLICE_ID,
        "base_sha": args.base_sha,
        "parent_decision": "OBL_B05_ENTRY_EXIT_PRODUCER_SIDE_AUTHORITY_DECISION_V1",
        "BOLLINGER_LONG_SEMANTIC_DECISION_COMPLETE": True,
        "BOLLINGER_DECISION": "CONTRACT_REMAINS_AMBIGUOUS",
        "BOLLINGER_QUANTITATIVE_BASELINE_COMPLETE": True,
        "BOLLINGER_SIDE_ACTIVATED": False,
        "BOLLINGER_SHORT_EMISSION": False,
        "OTHER_PRODUCER_SIDE_EMISSION_CHANGED": False,
        "PRODUCTIVE_SEMANTICS_CHANGED": False,
        "LIVE_AUTHORIZED": False,
        "ORDERS_ENABLED": False,
        "evaluation_instrument_id": EVAL_ID,
        "panel_member_count": len(panel_ids),
        "panel_total_bars": total_bars,
        "archive_dir": str(archive),
        "binding": str(args.binding.relative_to(_REPO_ROOT)),
        "scope_note": (
            "Identical durable full-canonical panel scratch + bollinger runtime config; "
            "SHORT reference overlays rsi_reversion POSITIONAL_LS on same bars "
            "(documented strategy-id difference; -1 is SHORT entry there, EXIT for bollinger)."
        ),
        "unresolved_contradictions": [
            "CP02_class_doc_1_long_vs_method_return_1_entry",
            "CP01_base_strategy_abc_long_short_vs_entry_exit",
            "CP03_registry_supported_sides_long_short_vs_long_only_code",
            "decision_d_entry_never_implies_long",
            "adapter_keeps_bollinger_entry_side_none",
            "parent_ssot_blocked_ambiguity",
        ],
        "decision_evidence": {
            "parent_bollinger_entry_side_decision": "BLOCKED_AMBIGUITY",
            "productive_minus_one_meaning": "EXIT_EVENT",
            "productive_plus_one_meaning": "ENTRY_EVENT",
            "short_entry_condition_present": False,
            "canonical_side_authority_present": False,
            "variant_a_rejected_reason": (
                "productive code/tests/owner contract not consistently long-only "
                "(class doc vs method return vs Decision D vs adapter NONE)"
            ),
            "variant_b_rejected_reason": (
                "producer package not ratified as EVENT_ONLY_NO_SIDE_AUTHORITY; "
                "parent audit class remains AMBIGUOUS_OR_CONTRADICTORY"
            ),
        },
        "bollinger_event_baseline_panel": dict(sorted(event_panel.items())),
        "bollinger_event_baseline_eval": _event_counts_from_signals(
            _bollinger_signals(
                pd.read_parquet(archive / "scratch" / EVAL_ID.replace(":", "_") / "bars.parquet"),
                boll_params,
            )
        )
        if EVAL_ID in panel_ids
        else None,
        "bollinger_eval_entry_mv2": boll_eval_summary,
        "bollinger_panel_entry_mv2": boll_panel_summary,
        "short_reference": {
            "producer_id": SHORT_REF_STRATEGY_ID,
            "encoding": "POSITIONAL_LS_STATE_V1",
            "params": dict(SHORT_REF_PARAMS),
            "minus_one_meaning": "SHORT_ENTRY_POSITIONAL",
            "plus_one_meaning": "LONG_ENTRY_POSITIONAL",
            "scope": "same_panel_bars_identical_archive_strategy_overlay",
            "panel_event_counts": {
                **dict(sorted(short_event_panel.items())),
                "short_entry_minus_one": short_minus_one_panel,
                "note": (
                    "exit_minus_one key reused from event counter helper; "
                    "for rsi_reversion it counts positional SHORT entries (raw==-1)"
                ),
            },
            "eval_short_entry_minus_one": short_minus_one_eval,
            "panel_short_entry_minus_one": short_minus_one_panel,
            "panel_long_plus_one_mv2": short_plus_panel,
            "eval_long_plus_one_mv2": short_plus_eval,
        },
        "comparison_table": {
            "scope": "identical_panel_member_set_and_bars; strategy differs by design",
            "bollinger_entry_plus_one": event_panel["entry_plus_one"],
            "bollinger_exit_minus_one": event_panel["exit_minus_one"],
            "bollinger_side_resolved": 0,
            "bollinger_entry_side_long": 0,
            "bollinger_entry_side_short": 0,
            "bollinger_entry_side_none": boll_panel_summary["entry_side_counts"].get("NONE", 0),
            "bollinger_agreement_pass": 0,
            "bollinger_agreement_block": boll_panel_summary["BLOCKED_DIRECTIONAL_AGREEMENT"],
            "bollinger_composition_observe_or_block": boll_panel_summary["BLOCKED_COMPOSITION"],
            "bollinger_ENTER_LONG": boll_panel_summary["ENTER_LONG"],
            "bollinger_ENTER_SHORT": boll_panel_summary["ENTER_SHORT"],
            "bollinger_HOLD": boll_panel_summary["HOLD"],
            "bollinger_dominant_first_failed_stage": boll_panel_summary[
                "dominant_first_failed_stage"
            ],
            "short_reference_entry_count": short_minus_one_panel,
            "short_reference_long_plus_one_count": short_event_panel["entry_plus_one"],
            "short_reference_dominant_note": (
                "rsi_reversion -1 is positional SHORT; Bollinger -1 is EXIT (never SHORT). "
                "Bollinger ENTRY remains side-unresolved (NONE) under decision C."
            ),
        },
        "control_dominant_first_failed_stage": boll_panel_summary["dominant_first_failed_stage"],
        "ratified_dominant_first_failed_stage": boll_panel_summary["dominant_first_failed_stage"],
        "changed_bar_count": 0,
        "next_dominant_blocker": {
            "stage": boll_panel_summary["dominant_first_failed_stage"],
            "contract_path": (
                "trading.master_v2 / resolve_agreement_bound_directional_cycle_v1 "
                "(ENTRY_EXIT entry_side=NONE → no directional cycle)"
            ),
            "panel_count": int(
                boll_panel_summary["first_failed_stage_counts"].get(
                    str(boll_panel_summary["dominant_first_failed_stage"]), 0
                )
            ),
            "note": "No side ratification in this slice; DA remains fail-closed for Bollinger ENTRY.",
        },
        "macd_side_activated": False,
        "elapsed_seconds": round(time.time() - t0, 2),
        "runner": "scripts/ops/run_obl_b05_bollinger_long_semantic_decision_baseline_v1.py",
    }

    out = args.output_dir
    out.mkdir(parents=True, exist_ok=True)
    (out / "baseline_summary.json").write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(
        json.dumps(
            {
                "ok": True,
                "output_dir": str(out),
                "BOLLINGER_DECISION": payload["BOLLINGER_DECISION"],
                "panel_entry": event_panel["entry_plus_one"],
                "panel_exit": event_panel["exit_minus_one"],
                "short_reference_entry_count": short_minus_one_panel,
                "dominant_stage": boll_panel_summary["dominant_first_failed_stage"],
                "elapsed_seconds": payload["elapsed_seconds"],
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
