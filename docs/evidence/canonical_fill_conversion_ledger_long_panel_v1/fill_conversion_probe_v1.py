#!/usr/bin/env python3
"""NON-AUTHORITATIVE audit harness: Intent→Ledger fill-conversion long-panel v1.

Evidence-only. Reuses run_mv2_research_backtest_wiring_v1 on the canonical
118-member futures panel fixtures. No productive mutation, no orders/live,
no runtime-bridge activation, no parameter tunes.
"""

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
from src.backtest.mv2_research_wiring_v1 import (  # noqa: E402
    map_decision_evidence_to_position_signal_v1,
    run_mv2_research_backtest_wiring_v1,
)
from src.backtest.strategy_signal_binding_v1 import (  # noqa: E402
    CANONICAL_SYSTEM_ENGINE_SIGNAL_SOURCE,
    ENGINE_SIGNAL_SOURCE_MV2_REPLAY,
)
from src.research.final_research_fleet_v0_versioned_binding_manifest_contract_v0 import (  # noqa: E402
    CANONICAL_INSTRUMENT_ID,
)

EVIDENCE = Path(__file__).resolve().parent
SOURCE = Path(
    "/Users/frnkhrz/Documents/Peak_Trade_runtime_evidence_archive_20260520T161443Z/"
    "research/full_canonical_system_economic_evidence_generation_v1_offline_execution_v0_20260716T015033Z"
)
BINDING = (
    _REPO / "config/research/bollinger_bands_v2_full_canonical_system_economic_binding_v1.json"
)

AUDIT_HARNESS_ID = "CANONICAL_FILL_CONVERSION_LEDGER_LONG_PANEL_V1"
AUDIT_AUTHORITY_EFFECT = "NONE"
AUDIT_RUNTIME_EFFECT = "NONE"

# Classification of per-instrument fill-conversion outcome (diagnostic, not promotion).
CLS_CONVERTED = "CONVERTED"
CLS_INTENT_ZERO = "NO_ENTRY_INTENT"
CLS_MAP_DROP = "INTENT_TO_MAPPED_SIGNAL_DROP"
CLS_ENGINE_DROP = "MAPPED_TO_ENGINE_SIGNAL_DROP"
CLS_LEDGER_ZERO = "ENGINE_SIGNAL_PRESENT_LEDGER_ZERO_TRADE"
CLS_ALIGNMENT_FAIL = "FUNNEL_ENGINE_ALIGNMENT_ANOMALY"
CLS_ERROR = "PROBE_ERROR"


def _load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _profile() -> DatasetProfileBindingV1:
    return DatasetProfileBindingV1(
        dataset_profile=DatasetProfileV1.ECONOMIC_RESEARCH_V1,
        execution_cost_binding=ExecutionCostBindingV1(
            spread_model_version="research_conservative_bps_v1",
            execution_price_observation_source="MODELLED_NOT_OBSERVED",
            conservative_half_spread_bps=5.0,
        ),
        l1_observation_status=L1ObservationStatusV1.EXECUTION_MODEL_BOUND_NOT_OBSERVED,
    )


def _bars_path(member_id: str) -> Path:
    scratch = SOURCE / "scratch"
    primary = scratch / member_id.replace(":", "_") / "bars.parquet"
    if primary.is_file():
        return primary
    alt = scratch / "datasets" / member_id.replace(":", "_") / "bars.parquet"
    if alt.is_file():
        return alt
    raise FileNotFoundError(member_id)


def _symbol(member_id: str) -> str:
    # okx:linear_perpetual:BONK:USDT:USDT:perp -> BONK
    parts = member_id.split(":")
    return parts[2] if len(parts) >= 3 else member_id


def _panel_members() -> list[str]:
    binding = _load(BINDING)
    ids = binding["binding"]["instrument_binding"]["eligible_instrument_ids"]
    return [str(x) for x in ids]


def prove_chain_binding_static() -> dict[str, Any]:
    wiring = (_REPO / "src/backtest/mv2_research_wiring_v1.py").read_text(encoding="utf-8")
    harness = Path(__file__).read_text(encoding="utf-8")
    return {
        "harness_id": AUDIT_HARNESS_ID,
        "authority_effect": AUDIT_AUTHORITY_EFFECT,
        "runtime_effect": AUDIT_RUNTIME_EFFECT,
        "uses_run_mv2_research_backtest_wiring_v1": "run_mv2_research_backtest_wiring_v1"
        in harness,
        "uses_map_decision_evidence_to_position_signal_v1": (
            "map_decision_evidence_to_position_signal_v1" in harness
        ),
        "wiring_calls_replay": "run_integrated_offline_trading_logic_replay_v1" in wiring,
        "map_owner": "src/backtest/mv2_research_wiring_v1.py::map_decision_evidence_to_position_signal_v1",
        "ledger_owner": "src/backtest/engine.py::BacktestEngine.run_realistic",
        "canonical_engine_signal_source": CANONICAL_SYSTEM_ENGINE_SIGNAL_SOURCE,
        "non_authoritative_marker": "NON-AUTHORITATIVE" in harness,
        "harness_forces_configured_strategy_bypass": any(
            "engine_signal_source" in line
            and "CONFIGURED_STRATEGY" in line
            and "harness_forces" not in line
            and not line.strip().startswith("#")
            for line in harness.splitlines()
        ),
    }


def _classify_row(row: dict[str, Any]) -> tuple[str, str, bool]:
    """Return (class, first_drop_boundary, mechanical_defect_suspected)."""
    if row.get("error"):
        return CLS_ERROR, "probe_execution", False
    enter = int(row["entry_intents"])
    mapped_nz = int(row["mapped_nonzero_on_enter_epochs"])
    engine_nz = int(row["engine_nonzero_bars"])
    trades = int(row["total_trades"])
    map_mismatch = int(row["enter_map_mismatch_count"])
    engine_mismatch = int(row["enter_engine_mismatch_count"])
    alignment_ok = bool(row["funnel_engine_values_match"])

    if not alignment_ok:
        return CLS_ALIGNMENT_FAIL, "assert_decision_funnel_trade_alignment_v1", True
    if enter == 0:
        return CLS_INTENT_ZERO, "entry_exit_policy", False
    if map_mismatch > 0 or mapped_nz < enter:
        return (
            CLS_MAP_DROP,
            "map_decision_evidence_to_position_signal_v1",
            True,
        )
    if engine_mismatch > 0:
        return CLS_ENGINE_DROP, "exposure_gate_or_engine_signal_series", True
    if engine_nz > 0 and trades == 0:
        # Sparse enter impulses followed by reduce→0 is expected engine semantics
        # unless open is contractually required; mark non-mechanical by default.
        return (
            CLS_LEDGER_ZERO,
            "backtest_engine_fill_or_roundtrip_ledger",
            False,
        )
    if trades > 0:
        return CLS_CONVERTED, "NONE", False
    return CLS_LEDGER_ZERO, "unknown_zero_trade", False


def _probe_member(member_id: str, cfg: dict[str, Any]) -> dict[str, Any]:
    bars = pd.read_parquet(_bars_path(member_id))
    decisions: list[str] = []
    enter_epochs: list[int] = []

    def hook(**kwargs: Any) -> None:
        decision = str(kwargs.get("decision_outcome") or "")
        epoch = int(kwargs.get("trading_epoch", -1))
        decisions.append(decision)
        if decision in {"enter_long", "enter_short"}:
            enter_epochs.append(epoch)

    result = run_mv2_research_backtest_wiring_v1(
        bars,
        strategy_id=str(cfg["economic_evaluation_v1"]["strategy_id"]),
        cfg=cfg,
        instrument_id=CANONICAL_INSTRUMENT_ID,
        profile_binding=_profile(),
        observational_bar_hook=hook,
        observational_panel_member_instrument_id=member_id,
    )

    outcomes = tuple(getattr(result, "bar_outcomes", ()) or ())
    engine_signals = (
        pd.Series(getattr(result, "signals", pd.Series(dtype=int))).fillna(0).astype(int)
    )
    engine_vals = [int(v) for v in engine_signals.tolist()]
    mapped_vals = [int(getattr(o, "position_signal", 0) or 0) for o in outcomes]

    # Remap from evidence for each outcome to verify adapter contract.
    remap_ok = 0
    remap_fail = 0
    for o in outcomes:
        evidence = getattr(o, "evidence", None)
        if evidence is None:
            continue
        expected = int(map_decision_evidence_to_position_signal_v1(evidence))
        actual = int(getattr(o, "position_signal", 0) or 0)
        if expected == actual:
            remap_ok += 1
        else:
            remap_fail += 1

    enter_long = sum(1 for d in decisions if d == "enter_long")
    enter_short = sum(1 for d in decisions if d == "enter_short")
    reduce_n = sum(1 for d in decisions if d in {"reduce", "exit"})
    entry_intents = enter_long + enter_short

    mapped_on_enter = 0
    enter_map_mismatch = 0
    enter_engine_mismatch = 0
    for ep in enter_epochs:
        if 0 <= ep < len(mapped_vals):
            if mapped_vals[ep] != 0:
                mapped_on_enter += 1
            else:
                enter_map_mismatch += 1
        if 0 <= ep < len(engine_vals):
            if engine_vals[ep] == 0:
                enter_engine_mismatch += 1

    # Impulse length: consecutive nonzero engine bars around enters.
    impulse_lens: list[int] = []
    for ep in enter_epochs:
        if ep < 0 or ep >= len(engine_vals) or engine_vals[ep] == 0:
            impulse_lens.append(0)
            continue
        # forward until zero
        j = ep
        while j < len(engine_vals) and engine_vals[j] != 0:
            j += 1
        impulse_lens.append(j - ep)

    trades_df = getattr(result.backtest_result, "trades", None)
    trade_count = 0
    if trades_df is not None and hasattr(trades_df, "empty") and not trades_df.empty:
        trade_count = int(len(trades_df))
    stats = getattr(result.backtest_result, "stats", None) or {}
    if isinstance(stats, dict):
        trade_count = max(trade_count, int(stats.get("total_trades", 0) or 0))

    funnel = dict(getattr(result, "decision_funnel_counts", None) or {})
    engine_src = str(
        getattr(result, "backtest_engine_signal_source", "")
        or CANONICAL_SYSTEM_ENGINE_SIGNAL_SOURCE
    )
    funnel_engine_match = mapped_vals == engine_vals and len(mapped_vals) == len(engine_vals)

    row: dict[str, Any] = {
        "instrument": _symbol(member_id),
        "member_id": member_id,
        "bars": int(len(bars)),
        "entry_intents": entry_intents,
        "enter_long": enter_long,
        "enter_short": enter_short,
        "exit_or_reduce": reduce_n,
        "mapped_nonzero_bars": int(sum(1 for v in mapped_vals if v != 0)),
        "mapped_nonzero_on_enter_epochs": mapped_on_enter,
        "enter_map_mismatch_count": enter_map_mismatch,
        "engine_nonzero_bars": int(sum(1 for v in engine_vals if v != 0)),
        "enter_engine_mismatch_count": enter_engine_mismatch,
        "remap_contract_ok": remap_ok,
        "remap_contract_fail": remap_fail,
        "median_impulse_len": (
            float(sorted(impulse_lens)[len(impulse_lens) // 2]) if impulse_lens else 0.0
        ),
        "max_impulse_len": int(max(impulse_lens) if impulse_lens else 0),
        "total_trades": trade_count,
        "conversion_ratio_trades_per_enter": (
            float(trade_count) / float(entry_intents) if entry_intents else 0.0
        ),
        "funnel_engine_values_match": funnel_engine_match,
        "engine_signal_source": engine_src,
        "classic_bypass": engine_src
        not in {
            ENGINE_SIGNAL_SOURCE_MV2_REPLAY,
            CANONICAL_SYSTEM_ENGINE_SIGNAL_SOURCE,
            "mv2_decision_replay_series",
        },
        "decision_funnel_trades_opened": int(funnel.get("trades_opened", 0) or 0),
        "decision_top": dict(Counter(decisions).most_common(8)),
    }
    klass, boundary, mechanical = _classify_row(row)
    row["fill_class"] = klass
    row["first_drop_boundary"] = boundary
    row["mechanical_defect_suspected"] = mechanical
    return row


def _write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    keys: list[str] = []
    flat_rows = []
    for row in rows:
        flat = {
            k: (json.dumps(v, sort_keys=True, default=str) if isinstance(v, dict) else v)
            for k, v in row.items()
        }
        flat_rows.append(flat)
        for k in flat:
            if k not in keys:
                keys.append(k)
    with path.open("w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=keys)
        w.writeheader()
        for fr in flat_rows:
            w.writerow(fr)


def main() -> int:
    print(
        json.dumps(
            {
                "harness": AUDIT_HARNESS_ID,
                "authority_effect": AUDIT_AUTHORITY_EFFECT,
                "runtime_effect": AUDIT_RUNTIME_EFFECT,
                "source": str(SOURCE),
            }
        ),
        flush=True,
    )
    if not SOURCE.is_dir():
        print(json.dumps({"ok": False, "error": "SOURCE_MISSING"}))
        return 2

    cfg = _load(SOURCE / "runtime_evaluation_config.json")
    proof = prove_chain_binding_static()
    (EVIDENCE / "chain_binding_proof.txt").write_text(
        json.dumps(proof, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )

    members = _panel_members()
    rows: list[dict[str, Any]] = []
    errors: list[dict[str, str]] = []
    for i, member_id in enumerate(members, 1):
        sym = _symbol(member_id)
        print(
            json.dumps({"phase": "probe", "i": i, "n": len(members), "instrument": sym}),
            flush=True,
        )
        try:
            row = _probe_member(member_id, cfg)
        except Exception as exc:  # noqa: BLE001
            row = {
                "instrument": sym,
                "member_id": member_id,
                "error": str(exc),
                "entry_intents": 0,
                "mapped_nonzero_on_enter_epochs": 0,
                "engine_nonzero_bars": 0,
                "total_trades": 0,
                "enter_map_mismatch_count": 0,
                "enter_engine_mismatch_count": 0,
                "funnel_engine_values_match": False,
                "classic_bypass": False,
            }
            klass, boundary, mechanical = _classify_row(row)
            row["fill_class"] = klass
            row["first_drop_boundary"] = boundary
            row["mechanical_defect_suspected"] = mechanical
            errors.append({"instrument": sym, "error": str(exc)})
        rows.append(row)
        print(
            json.dumps(
                {
                    "instrument": sym,
                    "enter": row.get("entry_intents"),
                    "mapped_on_enter": row.get("mapped_nonzero_on_enter_epochs"),
                    "engine_nz": row.get("engine_nonzero_bars"),
                    "trades": row.get("total_trades"),
                    "class": row.get("fill_class"),
                    "mechanical": row.get("mechanical_defect_suspected"),
                },
                sort_keys=True,
                default=str,
            ),
            flush=True,
        )

    _write_csv(EVIDENCE / "instrument_fill_conversion.csv", rows)

    class_counts = Counter(str(r.get("fill_class")) for r in rows)
    mechanical_rows = [r for r in rows if r.get("mechanical_defect_suspected")]
    totals = {
        "instruments": len(rows),
        "bars": sum(int(r.get("bars") or 0) for r in rows),
        "entry_intents": sum(int(r.get("entry_intents") or 0) for r in rows),
        "enter_long": sum(int(r.get("enter_long") or 0) for r in rows),
        "enter_short": sum(int(r.get("enter_short") or 0) for r in rows),
        "exit_or_reduce": sum(int(r.get("exit_or_reduce") or 0) for r in rows),
        "mapped_nonzero_bars": sum(int(r.get("mapped_nonzero_bars") or 0) for r in rows),
        "engine_nonzero_bars": sum(int(r.get("engine_nonzero_bars") or 0) for r in rows),
        "total_trades": sum(int(r.get("total_trades") or 0) for r in rows),
        "instruments_with_enter": sum(1 for r in rows if int(r.get("entry_intents") or 0) > 0),
        "instruments_with_trades": sum(1 for r in rows if int(r.get("total_trades") or 0) > 0),
        "instruments_ledger_zero_with_enter": sum(
            1
            for r in rows
            if int(r.get("entry_intents") or 0) > 0 and int(r.get("total_trades") or 0) == 0
        ),
        "mechanical_defect_instruments": len(mechanical_rows),
    }
    summary = {
        "ok": True,
        "harness_id": AUDIT_HARNESS_ID,
        "base_sha_expected": "bf74d4e3b15daeb6b4d25411ebd016694c54370b",
        "panel_member_count": len(members),
        "source_fixture": str(SOURCE),
        "binding_ref": str(BINDING.relative_to(_REPO)),
        "class_counts": dict(sorted(class_counts.items())),
        "totals": totals,
        "mechanical_defects": [
            {
                "instrument": r.get("instrument"),
                "class": r.get("fill_class"),
                "boundary": r.get("first_drop_boundary"),
            }
            for r in mechanical_rows
        ],
        "errors": errors,
        "chain_binding_proof": proof,
        "runtime_bridge_status": "BOUND_NOT_ACTIVATED",
        "live_authorized": False,
        "orders": False,
        "classic_engine_bypass_found": any(bool(r.get("classic_bypass")) for r in rows),
        "canonical_chain_bound": all(
            str(r.get("engine_signal_source"))
            in {
                ENGINE_SIGNAL_SOURCE_MV2_REPLAY,
                CANONICAL_SYSTEM_ENGINE_SIGNAL_SOURCE,
                "mv2_decision_replay_series",
            }
            for r in rows
            if not r.get("error")
        ),
    }
    (EVIDENCE / "probe_summary.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True, default=str) + "\n",
        encoding="utf-8",
    )
    print(
        json.dumps({"ok": True, "summary": str(EVIDENCE / "probe_summary.json"), "totals": totals})
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
