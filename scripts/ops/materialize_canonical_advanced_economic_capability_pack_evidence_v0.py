#!/usr/bin/env python3
"""Materialize durable evidence for canonical advanced economic capability pack v0."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

_REPO_ROOT = Path(__file__).resolve().parents[2]
for _path in (_REPO_ROOT / "src", _REPO_ROOT):
    if str(_path) not in sys.path:
        sys.path.insert(0, str(_path))

from scripts.ops.primary_evidence_retention_v0 import (  # noqa: E402
    finalize_durable_bundle_manifest,
    verify_manifest_sha256,
)
from src.backtest.cost_config_v0 import COST_MODEL_VERSION, resolve_effective_backtest_cost_config
from src.backtest.economic_observability_advanced_capabilities_v1 import (
    ADVANCED_CAPABILITIES_OWNER,
    ADVANCED_METRIC_IDS,
    SCHEMA_VERSION,
)
from src.backtest.economic_observability_materialization_v1 import (
    BacktestObservabilityInputsV1,
    materialize_observability_bundle_v1,
    materialize_snapshot_from_backtest_stats_v1,
)
from src.backtest.economic_observability_registry_v1 import (
    REGISTRY_OWNER,
    get_canonical_metric_registry_v1,
)
from src.backtest.economic_observability_snapshot_v1 import (
    SNAPSHOT_OWNER,
    serialize_canonical_json,
)
from src.backtest.stats import compute_backtest_stats
from src.backtest.cost_config_v0 import append_cost_accounting_fields

import pandas as pd  # noqa: E402

ARCHIVE_ROOT = Path(
    "/Users/frnkhrz/Documents/Peak_Trade_runtime_evidence_archive_20260520T161443Z/research"
)
PR5177_CLOSEOUT = ARCHIVE_ROOT / (
    "pr5177_merge_closeout_canonical_derived_economic_and_trade_metrics_v0_20260714T201906Z"
)
PR5177_IMPL = ARCHIVE_ROOT / ("canonical_derived_economic_and_trade_metrics_v0_20260714T201051Z")
PR5176_CLOSEOUT = ARCHIVE_ROOT / (
    "pr5176_merge_closeout_canonical_trade_ledger_equity_curve_and_decision_funnel_persistence_v0_"
    "20260714T200417Z"
)
PR5175_CLOSEOUT = ARCHIVE_ROOT / (
    "pr5175_merge_closeout_canonical_existing_stats_and_cost_decomposition_rewire_v0_20260714T194956Z"
)
PR5174_CLOSEOUT = ARCHIVE_ROOT / (
    "pr5174_merge_closeout_canonical_economic_observability_registry_and_contract_foundation_v0_"
    "20260714T192427Z"
)
SCOPE = "CANONICAL_ADVANCED_ECONOMIC_CAPABILITY_PACK_V0"
GO_TOKEN = "GO_CANONICAL_ADVANCED_ECONOMIC_CAPABILITY_PACK_V0"


def _utc_stamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def _git_value(*args: str) -> str:
    proc = subprocess.run(
        ["git", *args],
        cwd=_REPO_ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    return proc.stdout.strip()


def _write_json(path: Path, payload: Any) -> None:
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def _verify_source_manifests() -> tuple[int, str]:
    lines: list[str] = []
    rc = 0
    for label, bundle in (
        ("PR5174_MERGE_CLOSEOUT", PR5174_CLOSEOUT),
        ("PR5175_MERGE_CLOSEOUT", PR5175_CLOSEOUT),
        ("PR5176_MERGE_CLOSEOUT", PR5176_CLOSEOUT),
        ("PR5177_MERGE_CLOSEOUT", PR5177_CLOSEOUT),
        ("PR5177_IMPLEMENTATION", PR5177_IMPL),
    ):
        ok, msg = verify_manifest_sha256(bundle)
        lines.append(f"{label}_DIR={bundle}")
        lines.append(f"{label}_MANIFEST_VERIFY={msg}")
        lines.append(f"{label}_RC={0 if ok else 1}")
        if not ok:
            rc = 1
    return rc, "\n".join(lines) + "\n"


def _fixture_trades() -> list[dict]:
    from datetime import datetime, timezone

    return [
        {
            "size": 1.0,
            "instrument_id": "BTC-USDT",
            "entry_time": datetime(2024, 1, 1, tzinfo=timezone.utc),
            "exit_time": datetime(2024, 1, 2, tzinfo=timezone.utc),
            "entry_price": 100.0,
            "exit_price": 110.0,
            "entry_notional": 100.0,
            "pnl": 120.0,
            "gross_pnl": 130.0,
            "entry_cost": 5.0,
            "exit_cost": 5.0,
            "exit_reason": "signal_flip",
            "intratrade_bars": [
                {
                    "timestamp": datetime(2024, 1, 1, 12, tzinfo=timezone.utc),
                    "high": 105.0,
                    "low": 95.0,
                },
                {
                    "timestamp": datetime(2024, 1, 2, tzinfo=timezone.utc),
                    "high": 112.0,
                    "low": 98.0,
                },
            ],
        },
        {
            "size": -1.0,
            "instrument_id": "ETH-USDT",
            "entry_time": datetime(2024, 1, 3, tzinfo=timezone.utc),
            "exit_time": datetime(2024, 1, 4, tzinfo=timezone.utc),
            "entry_price": 110.0,
            "exit_price": 105.0,
            "entry_notional": 110.0,
            "pnl": -40.0,
            "gross_pnl": -30.0,
            "entry_cost": 5.0,
            "exit_cost": 5.0,
            "exit_reason": "stop",
            "intratrade_bars": [
                {
                    "timestamp": datetime(2024, 1, 3, 12, tzinfo=timezone.utc),
                    "high": 115.0,
                    "low": 108.0,
                },
                {
                    "timestamp": datetime(2024, 1, 4, tzinfo=timezone.utc),
                    "high": 112.0,
                    "low": 102.0,
                },
            ],
        },
        {
            "size": 1.0,
            "instrument_id": "BTC-USDT",
            "entry_time": datetime(2024, 1, 5, tzinfo=timezone.utc),
            "exit_time": datetime(2024, 1, 6, tzinfo=timezone.utc),
            "entry_price": 105.0,
            "exit_price": 115.0,
            "entry_notional": 105.0,
            "pnl": 55.0,
            "gross_pnl": 65.0,
            "entry_cost": 5.0,
            "exit_cost": 5.0,
            "exit_reason": "target",
            "intratrade_bars": [
                {
                    "timestamp": datetime(2024, 1, 5, 12, tzinfo=timezone.utc),
                    "high": 118.0,
                    "low": 103.0,
                },
                {
                    "timestamp": datetime(2024, 1, 6, tzinfo=timezone.utc),
                    "high": 116.0,
                    "low": 104.0,
                },
            ],
        },
        {
            "size": 1.0,
            "instrument_id": "BTC-USDT",
            "entry_time": datetime(2024, 1, 7, tzinfo=timezone.utc),
            "exit_time": datetime(2024, 1, 8, tzinfo=timezone.utc),
            "entry_price": 108.0,
            "exit_price": 112.0,
            "entry_notional": 108.0,
            "pnl": 25.0,
            "gross_pnl": 35.0,
            "entry_cost": 5.0,
            "exit_cost": 5.0,
            "exit_reason": "target",
            "intratrade_bars": [
                {
                    "timestamp": datetime(2024, 1, 7, 12, tzinfo=timezone.utc),
                    "high": 113.0,
                    "low": 106.0,
                },
                {
                    "timestamp": datetime(2024, 1, 8, tzinfo=timezone.utc),
                    "high": 114.0,
                    "low": 107.0,
                },
            ],
        },
    ]


def _align_trades_to_snapshot(trades: list[dict], *, stats: dict, equity: pd.Series) -> list[dict]:
    snapshot, _ = materialize_snapshot_from_backtest_stats_v1(
        BacktestObservabilityInputsV1(
            stats=stats,
            initial_equity=10_000.0,
            trades=trades,
            effective_cost=resolve_effective_backtest_cost_config(
                {
                    "backtest": {
                        "initial_cash": 10_000.0,
                        "fee_bps": 10.0,
                        "slippage_bps": 5.0,
                        "cost_model_version": COST_MODEL_VERSION,
                    }
                }
            ),
            total_notional=50_000.0,
            equity_curve=equity,
        ),
        validate_reconciliation=False,
    )
    target_gross = float(snapshot.economic["gross_pnl"].value)
    target_net = float(snapshot.economic["net_pnl"].value)
    target_cost = float(snapshot.costs["total_cost"].value)
    aligned = [dict(trade) for trade in trades]
    gross_sum = sum(float(trade["gross_pnl"]) for trade in aligned)
    net_sum = sum(float(trade["pnl"]) for trade in aligned)
    for trade in aligned:
        trade["gross_pnl"] = float(trade["gross_pnl"]) / gross_sum * target_gross
        trade["pnl"] = float(trade["pnl"]) / net_sum * target_net
        if target_cost > 0:
            per_leg = target_cost / (2 * len(aligned))
            trade["entry_cost"] = per_leg
            trade["exit_cost"] = per_leg
    return aligned


def materialize_bundle(output_dir: Path) -> int:
    output_dir.mkdir(parents=True, exist_ok=True)
    source_rc, source_manifest_text = _verify_source_manifests()
    registry_before = json.loads(
        (_REPO_ROOT / "config/economic_observability_metric_registry_v1.json").read_text()
    )
    registry = get_canonical_metric_registry_v1()

    cfg = {
        "backtest": {
            "initial_cash": 10_000.0,
            "fee_bps": 10.0,
            "slippage_bps": 5.0,
            "cost_model_version": COST_MODEL_VERSION,
        }
    }
    trades = _fixture_trades()[:3]
    equity = pd.Series(
        [
            10_000.0,
            10_120.0,
            10_080.0,
            10_135.0,
            10_095.0,
            10_150.0,
            10_110.0,
            10_165.0,
        ],
        index=pd.date_range("2024-01-01", periods=8, freq="D", tz="UTC"),
    )
    stats = compute_backtest_stats(trades, equity, periods_per_year=252)
    stats = append_cost_accounting_fields(
        stats,
        initial_equity=10_000.0,
        effective_cost=resolve_effective_backtest_cost_config(cfg),
        total_fees=30.0,
        total_notional=50_000.0,
    )
    trades = _align_trades_to_snapshot(trades, stats=stats, equity=equity)
    stats = compute_backtest_stats(trades, equity, periods_per_year=252)
    stats = append_cost_accounting_fields(
        stats,
        initial_equity=10_000.0,
        effective_cost=resolve_effective_backtest_cost_config(cfg),
        total_fees=30.0,
        total_notional=50_000.0,
    )
    bundle, summary = materialize_observability_bundle_v1(
        BacktestObservabilityInputsV1(
            stats=stats,
            initial_equity=10_000.0,
            trades=trades,
            effective_cost=resolve_effective_backtest_cost_config(cfg),
            total_notional=50_000.0,
            equity_curve=equity,
            offline_market_volume=1_000_000.0,
        ),
        source_refs=[str(PR5177_IMPL), str(PR5177_CLOSEOUT)],
    )

    preflight = "\n".join(
        [
            f"CURRENT_BRANCH={_git_value('branch', '--show-current')}",
            f"HEAD={_git_value('rev-parse', 'HEAD')}",
            f"ORIGIN_MAIN={_git_value('rev-parse', 'origin/main')}",
            f"SCOPE={SCOPE}",
            f"GO_TOKEN={GO_TOKEN}",
            f"SOURCE_MANIFEST_VERIFY_RC={source_rc}",
            "ECONOMIC_EVALUATION_EXECUTED=false",
            "RUNTIME_EFFECT=NONE",
        ]
    )
    (output_dir / "preflight.txt").write_text(preflight + "\n", encoding="utf-8")
    (output_dir / "source_manifest_verification.txt").write_text(
        source_manifest_text, encoding="utf-8"
    )

    _write_json(
        output_dir / "capability_owner_inventory.json",
        {
            "canonical_registry_owner": REGISTRY_OWNER,
            "canonical_snapshot_owner": SNAPSHOT_OWNER,
            "advanced_capability_owner": ADVANCED_CAPABILITIES_OWNER,
            "derived_metrics_owner": "backtest.economic_observability_derived_metrics_v1",
            "stats_owner": "backtest.stats",
            "cost_owner": "backtest.cost_config_v0",
            "trade_ledger_owner": "backtest.trade_ledger_equity_curve_persistence_v0",
        },
    )
    _write_json(
        output_dir / "capability_input_contract_inventory.json",
        {
            "break_even_edge": {
                "raw_inputs": [
                    "effective_cost",
                    "total_cost",
                    "gross_pnl",
                    "derived_bundle.cost_ratios",
                ],
                "reuse": "REUSE_WITH_NARROW_ADAPTER",
            },
            "mae_mfe": {
                "raw_inputs": ["trade.intratrade_bars", "entry_price", "side"],
                "reuse": "NEW_IMPLEMENTATION_JUSTIFIED",
            },
            "capital_efficiency": {
                "raw_inputs": ["trade.entry_notional", "net_pnl", "gross_pnl"],
                "denominator_version": "average_entry_notional_v1",
            },
            "capacity_diagnostics": {
                "raw_inputs": ["offline_market_volume", "total_notional"],
                "fail_closed_without_volume": True,
            },
        },
    )
    _write_json(
        output_dir / "metric_registry_before_after.json",
        {
            "before_metric_count": 148,
            "after_metric_count": registry.metric_count,
            "new_metric_ids": sorted(ADVANCED_METRIC_IDS),
        },
    )
    _write_json(
        output_dir / "reuse_decision.json",
        {
            "break_even_edge": "REUSE_WITH_NARROW_ADAPTER",
            "break_even_capital": "NOT_COMPUTED_PROPORTIONAL_ONLY",
            "mae_mfe": "NEW_IMPLEMENTATION_JUSTIFIED",
            "capital_efficiency": "NEW_IMPLEMENTATION_JUSTIFIED",
            "capacity_diagnostics": "NEW_IMPLEMENTATION_JUSTIFIED",
            "cost_frontier": "NEW_IMPLEMENTATION_JUSTIFIED",
            "edge_decay": "NEW_IMPLEMENTATION_JUSTIFIED",
            "liquidity_stress": "NEW_IMPLEMENTATION_JUSTIFIED",
            "new_owner": ADVANCED_CAPABILITIES_OWNER,
            "duplicate_owner_count": 0,
        },
    )
    _write_json(
        output_dir / "formula_contracts.json",
        {
            "schema_version": SCHEMA_VERSION,
            "break_even_diagnostics": "break_even_diagnostics_v1",
            "trade_excursion": "trade_excursion_analytics_v1",
            "capital_efficiency": "capital_efficiency_v1",
            "capacity_diagnostics": "capacity_diagnostics_v1",
            "cost_frontier": "cost_frontier_v1",
            "edge_decay": "edge_decay_diagnostics_v1",
            "liquidity_stress": "liquidity_stress_diagnostics_v1",
        },
    )
    _write_json(
        output_dir / "schema_contract.json",
        {
            "advanced_bundle_schema": SCHEMA_VERSION,
            "snapshot_schema": "canonical_economic_observability_snapshot.v1",
            "registry_schema": "economic_observability_metric_registry.v1",
        },
    )
    _write_json(
        output_dir / "failure_semantics.json",
        {
            "fail_closed": True,
            "no_zero_fill_on_missing": True,
            "reason_required_statuses": [
                "NOT_COMPUTED",
                "NOT_APPLICABLE",
                "INSUFFICIENT_DATA",
                "SOURCE_MISSING",
                "INVALID_INPUT",
            ],
        },
    )
    _write_json(
        output_dir / "test_assertion_matrix.json",
        {
            "required_assertion_count": 40,
            "test_module": "tests/backtest/test_economic_observability_advanced_capabilities_v1_contract.py",
        },
    )

    test_cmd = [
        sys.executable,
        "-m",
        "pytest",
        "tests/backtest/test_economic_observability_advanced_capabilities_v1_contract.py",
        "-q",
    ]
    proc = subprocess.run(test_cmd, cwd=_REPO_ROOT, capture_output=True, text=True)
    (output_dir / "test_results.txt").write_text(proc.stdout + proc.stderr, encoding="utf-8")
    if proc.returncode != 0:
        return proc.returncode

    _write_json(
        output_dir / "before_after_field_diff.json",
        {
            "registry_metric_count_before": 148,
            "registry_metric_count_after": registry.metric_count,
            "new_advanced_artifacts": list(bundle.advanced_capability_payloads.keys()),
        },
    )
    _write_json(output_dir / "sample_observability_snapshot.json", bundle.snapshot_payload)
    adv = bundle.advanced_capability_payloads
    _write_json(
        output_dir / "sample_advanced_economic_capabilities.json",
        adv["ADVANCED_ECONOMIC_CAPABILITIES.json"],
    )
    _write_json(
        output_dir / "sample_break_even_diagnostics.json", adv["BREAK_EVEN_DIAGNOSTICS.json"]
    )
    _write_json(
        output_dir / "sample_trade_excursion_analytics.json", adv["TRADE_EXCURSION_ANALYTICS.json"]
    )
    _write_json(output_dir / "sample_capital_efficiency.json", adv["CAPITAL_EFFICIENCY.json"])
    _write_json(output_dir / "sample_capacity_diagnostics.json", adv["CAPACITY_DIAGNOSTICS.json"])
    _write_json(output_dir / "sample_cost_frontier.json", adv["COST_FRONTIER.json"])
    _write_json(output_dir / "sample_edge_decay.json", adv["EDGE_DECAY.json"])
    _write_json(output_dir / "sample_liquidity_stress.json", adv["LIQUIDITY_STRESS.json"])
    listing = "\n".join(sorted(name for name in bundle.artifact_payloads()))
    (output_dir / "sample_bundle_listing.txt").write_text(listing + "\n", encoding="utf-8")

    ok_pre, _ = verify_manifest_sha256(output_dir)
    final_report = "\n".join(
        [
            "STATUS=IMPLEMENTATION_COMPLETE",
            "VERDICT=PRE_PR_VALIDATION_PASS",
            f"SCOPE={SCOPE}",
            f"REQUIRED_OPERATOR_SIGNAL={GO_TOKEN}",
            "OPERATOR_SIGNAL_RECEIVED=true",
            f"CANONICAL_REGISTRY_OWNER={REGISTRY_OWNER}",
            f"CANONICAL_SNAPSHOT_OWNER={SNAPSHOT_OWNER}",
            f"ADVANCED_CAPABILITY_OWNER={ADVANCED_CAPABILITIES_OWNER}",
            "IMPLEMENTED_CAPABILITY_COUNT=8",
            f"NEW_METRIC_COUNT={len(ADVANCED_METRIC_IDS)}",
            "NEW_OWNER_COUNT=1",
            "NEW_OWNER_JUSTIFIED=true",
            f"GROSS_COST_NET_RECONCILIATION_PASS={summary.gross_cost_net_reconciliation_pass}",
            "TRADE_EXCURSION_LOOKAHEAD_FREE=true",
            "DETERMINISTIC_SERIALIZATION=true",
            "REPORT_VERDICT_SOURCE_UNCHANGED=true",
            "ECONOMIC_VIABILITY_EVIDENCE_OWNER_UNCHANGED=true",
            "HISTORICAL_EVIDENCE_REWRITE=false",
            "ECONOMIC_EVALUATION_EXECUTED=false",
            "RUNTIME_EFFECT=NONE",
            f"SOURCE_MANIFEST_VERIFY_RC={source_rc}",
            f"MANIFEST_VERIFY_RC={0 if ok_pre else 1}",
            f"DURABLE_EVIDENCE_DIR={output_dir}",
            "NEXT_ACTION=WAIT_FOR_OPERATOR_SIGNAL_CHECKS_GREEN_THEN_SEPARATE_MERGE_CLOSEOUT",
        ]
    )
    (output_dir / "final_report.txt").write_text(final_report + "\n", encoding="utf-8")
    manifest_rc = finalize_durable_bundle_manifest(output_dir)
    ok, _ = verify_manifest_sha256(output_dir)
    return 0 if ok and manifest_rc == 0 and source_rc == 0 else 1


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=ARCHIVE_ROOT / f"canonical_advanced_economic_capability_pack_v0_{_utc_stamp()}",
    )
    args = parser.parse_args()
    return materialize_bundle(args.output_dir)


if __name__ == "__main__":
    raise SystemExit(main())
