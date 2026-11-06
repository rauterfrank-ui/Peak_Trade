"""Reproduce bounded supplier probes via ./scripts/pt - < this file, from repo root.

Synthetic simulator studies only. No new Search-to-execution adapter or policy.
"""

import json
import math
import subprocess
from copy import deepcopy
from pathlib import Path

from src.backtest.mv2_research_wiring_v1 import (
    compute_mv2_backtest_metrics_v1,
    run_mv2_research_backtest_wiring_v1,
)
from src.backtest.parameter_sensitivity_v1 import run_parameter_sensitivity_v1
from src.backtest.strategy_signal_binding_v1 import (
    StrategySignalBindingError,
    execute_configured_strategy_signal_series_v1,
)
from src.meta.learning_loop.contract_safety_v1 import compute_content_sha256
from src.risk.position_sizer import PositionRequest, calc_position_size
from tests.backtest.test_mv2_research_wiring_v1 import _bars, _cfg
from tests.backtest.test_parameter_sensitivity_v1 import _bars as grid_bars
from tests.backtest.test_parameter_sensitivity_v1 import _cfg as grid_cfg

ROOT = Path.cwd()
OUT = ROOT / "docs/ops/evidence/numerical_research_execution_supplier_probe_v1_2026_11_04"


def evidence_json(value):
    # JSON evidence transport only: never turn a supplier NaN into a number.
    if isinstance(value, float) and not math.isfinite(value):
        return {"status": "NON_FINITE_FROM_SUPPLIER", "raw_repr": repr(value)}
    if isinstance(value, dict):
        return {key: evidence_json(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [evidence_json(item) for item in value]
    return value


def dump(name, value):
    (OUT / name).write_text(
        json.dumps(evidence_json(value), indent=2, sort_keys=True, default=str, allow_nan=False)
        + "\n"
    )


def bars(count):
    result = _bars(count)
    prices = [100 + 5 * math.sin(i / 12) + 0.01 * i for i in range(count)]
    for key in ("open", "close", "mark_price", "index_price"):
        result[key] = prices
    result["high"] = [p + 0.5 for p in prices]
    result["low"] = [p - 0.5 for p in prices]
    result["best_bid"] = [p - 0.05 for p in prices]
    result["best_ask"] = [p + 0.05 for p in prices]
    result["bar_interval"] = "1h"
    return result


source_commit = subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip()
control_bars = bars(256)
dump("synthetic_bars.json", json.loads(control_bars.to_json(orient="table", date_format="iso")))
bar_binding = compute_content_sha256(
    json.loads(control_bars.to_json(orient="table", date_format="iso"))
)

# The former Search fixture's short names are not registered engine aliases.
denials = []
for short_names in ({"fast": 10, "slow": 50}, {"fast": 10, "slow": 100}):
    cfg = deepcopy(_cfg())
    cfg["economic_evaluation_v1"]["strategy_params"] = short_names
    try:
        execute_configured_strategy_signal_series_v1(
            control_bars, strategy_id="ma_crossover", cfg=cfg
        )
    except StrategySignalBindingError as exc:
        denials.append({"parameters": short_names, "status": "REJECTED", "reason": str(exc)})
    else:
        raise AssertionError("Unregistered Search-fixture names unexpectedly admitted")
dump("short_name_denials.json", denials)

runs = []
for label, risk in (
    ("original_fixture_sizing", 0.02),
    ("explicit_lower_risk_synthetic_scenario", 0.002),
):
    for slow in (50, 100):
        cfg = deepcopy(_cfg())
        cfg["risk"]["risk_per_trade"] = risk
        cfg["economic_evaluation_v1"]["strategy_params"] = {"fast_window": 10, "slow_window": slow}
        hook_rows = []

        def hook(**row):
            material = row["agreement_material"]
            hook_rows.append(
                {
                    "epoch": row["trading_epoch"],
                    "timestamp": row["bar_timestamp"],
                    "raw_strategy_signal": row["raw_strategy_signal"],
                    "mapped_signal": row["mapped_position_signal"],
                    "agreement_cycle_signal": None
                    if material is None
                    else material.cycle_signal_value,
                    "agreement_params_digest": None
                    if material is None
                    else material.strategy_params_digest,
                    "decision_outcome": row["decision_outcome"],
                    "fail_reasons": list(row["fail_reasons"]),
                }
            )

        result = run_mv2_research_backtest_wiring_v1(
            bars=control_bars, strategy_id="ma_crossover", cfg=cfg, observational_bar_hook=hook
        )
        trades = result.backtest_result.trades
        record = {
            "scenario": label,
            "slow_window": slow,
            "input_cfg": cfg,
            "bar_binding": bar_binding,
            "strategy_provenance": result.strategy_signal_provenance.to_dict(),
            "signal_source": result.backtest_engine_signal_source,
            "engine_signal_digest": result.backtest_engine_signal_digest,
            "mv2_signal_digest": result.mv2_replay_signal_digest,
            "engine_signals": result.signals.tolist(),
            "engine_stats": result.backtest_result.stats,
            "hourly_supplier_metrics": dict(
                compute_mv2_backtest_metrics_v1(result.backtest_result)
            ),
            "cost_binding": result.effective_cost_config.to_dict(),
            "funnel": result.decision_funnel_counts,
            "block_reason_counts": result.block_reason_counts,
            "equity": [
                {"timestamp": str(t), "value": float(v)}
                for t, v in result.backtest_result.equity_curve.items()
            ],
            "trades": [] if trades is None else trades.to_dict(orient="records"),
            "bar_trace": hook_rows,
        }
        assert record["engine_signal_digest"] == record["mv2_signal_digest"]
        assert all(row["raw_strategy_signal"] == row["agreement_cycle_signal"] for row in hook_rows)
        dump(f"{label}_slow{slow}.json", record)
        runs.append(
            {
                "scenario": label,
                "slow_window": slow,
                "raw_nonzero_bars": sum(row["raw_strategy_signal"] != 0 for row in hook_rows),
                "engine_signal_digest": record["engine_signal_digest"],
                "engine_stats": record["engine_stats"],
                "hourly_supplier_metrics": record["hourly_supplier_metrics"],
            }
        )

for pair in (runs[:2], runs[2:]):
    assert pair[0]["engine_signal_digest"] != pair[1]["engine_signal_digest"]
assert all(r["engine_stats"]["total_trades"] == 0 for r in runs[:2])
assert all(r["engine_stats"]["total_trades"] > 0 for r in runs[2:])
assert runs[2]["engine_stats"]["total_return"] != runs[3]["engine_stats"]["total_return"]
size = calc_position_size(
    PositionRequest(equity=10000, entry_price=100, stop_price=98, risk_per_trade=0.02),
    max_position_pct=0.25,
    min_position_value=10,
    min_stop_distance=0.0001,
)
assert size.rejected
dump("original_sizing_rejection.json", vars(size))

# Execute the existing sensitivity owner, not a mocked split evaluator.
small = run_parameter_sensitivity_v1(
    bars=grid_bars(),
    cfg=grid_cfg(),
    strategy_id="ma_crossover",
    strategy_version="v1",
    data_digest=compute_content_sha256(
        json.loads(grid_bars().to_json(orient="table", date_format="iso"))
    ),
)
dump("original_small_grid_result.json", small.to_dict())
assert small.failed_point_count == small.combination_count == 4

long_bars = bars(768)
cfg = deepcopy(_cfg())
cfg["risk"]["risk_per_trade"] = 0.002
cfg["economic_evaluation_v1"]["strategy_params"] = {"fast_window": 10, "slow_window": 50}
cfg["backtest"]["parameter_sensitivity"] = {
    "bind": True,
    "grid_version": "v1",
    "grid": {
        "grid_id": "explicit_native_name_synthetic_probe_v1",
        "parameter_names": ["strategy.fast_window", "strategy.slow_window"],
        "parameter_values": [[10], [50, 100]],
        "search_space_bounds": {
            "strategy.fast_window": {"min": 2, "max": 200},
            "strategy.slow_window": {"min": 3, "max": 500},
        },
        "seed": 12,
    },
}
long = run_parameter_sensitivity_v1(
    bars=long_bars,
    cfg=cfg,
    strategy_id="ma_crossover",
    strategy_version="v1",
    data_digest=compute_content_sha256(
        json.loads(long_bars.to_json(orient="table", date_format="iso"))
    ),
)
dump("native_grid_result.json", long.to_dict())
dump("native_grid_input_cfg.json", cfg)
assert long.failed_point_count == 0
assert all(p.evaluation_status.value == "EVALUATED" for p in long.points)
dump(
    "summary.json",
    {
        "source_commit": source_commit,
        "source_class": "SYNTHETIC_CONTROL_NOT_NATURAL_MARKET",
        "runs": runs,
        "short_names": denials,
        "small_grid": {"pipeline": small.pipeline_status.value, "failed": small.failed_point_count},
        "native_grid": {
            "pipeline": long.pipeline_status.value,
            "failed": long.failed_point_count,
            "evaluated": len(long.points),
        },
        "boundaries": [
            "Separate native-name execution probes, not the prior Search candidate or its canonical experiment identity",
            "Reduced-risk scenario is explicit probe configuration; no live or production policy adoption",
            "Raw engine stats annualize by 365; existing hourly supplier recomputes by 8760",
            "Sensitivity output stores OOS fields and split references, not all computed train/validation metrics",
            "Funding absent; economic interpretation flag remains false; CRS unresolved evidence retained",
            "Different results do not show improvement or natural validity; no direct canonical-core attribution",
        ],
    },
)
print(
    json.dumps(
        {
            "runs": runs,
            "small_grid_failed": small.failed_point_count,
            "native_grid_evaluated": len(long.points),
        },
        default=str,
    )
)
