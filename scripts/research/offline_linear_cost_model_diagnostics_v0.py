from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

_SCRIPT_ROOT = Path(__file__).resolve()
for parent in [_SCRIPT_ROOT, *_SCRIPT_ROOT.parents]:
    if (parent / "src").is_dir() and (parent / ".git").exists():
        repo_s = str(parent)
        if repo_s not in sys.path:
            sys.path.insert(0, repo_s)
        break

import numpy as np

from src.research.linear_evidence.contracts import to_jsonable
from src.research.linear_evidence.cost_model import build_cost_model_calibration_evidence
from src.research.linear_evidence.feature_matrix import build_feature_matrix_binding
from src.research.linear_evidence.fitters import fit_ols_lstsq


FIXTURE_ROWS = [
    {
        "decision_time": "2026-01-01T00:00:00Z",
        "spread_bps": 4.0,
        "volatility_estimate": 0.010,
        "order_notional_to_depth": 0.10,
        "funding_rate_abs": 0.0001,
        "liquidity_score": 0.90,
        "realized_slippage_bps": 5.2,
    },
    {
        "decision_time": "2026-01-01T01:00:00Z",
        "spread_bps": 4.5,
        "volatility_estimate": 0.011,
        "order_notional_to_depth": 0.12,
        "funding_rate_abs": 0.0001,
        "liquidity_score": 0.88,
        "realized_slippage_bps": 5.8,
    },
    {
        "decision_time": "2026-01-01T02:00:00Z",
        "spread_bps": 5.0,
        "volatility_estimate": 0.014,
        "order_notional_to_depth": 0.16,
        "funding_rate_abs": 0.0002,
        "liquidity_score": 0.80,
        "realized_slippage_bps": 7.0,
    },
    {
        "decision_time": "2026-01-01T03:00:00Z",
        "spread_bps": 5.5,
        "volatility_estimate": 0.015,
        "order_notional_to_depth": 0.20,
        "funding_rate_abs": 0.0002,
        "liquidity_score": 0.76,
        "realized_slippage_bps": 7.8,
    },
    {
        "decision_time": "2026-01-01T04:00:00Z",
        "spread_bps": 6.0,
        "volatility_estimate": 0.018,
        "order_notional_to_depth": 0.22,
        "funding_rate_abs": 0.0003,
        "liquidity_score": 0.70,
        "realized_slippage_bps": 9.1,
    },
    {
        "decision_time": "2026-01-01T05:00:00Z",
        "spread_bps": 6.5,
        "volatility_estimate": 0.020,
        "order_notional_to_depth": 0.24,
        "funding_rate_abs": 0.0003,
        "liquidity_score": 0.66,
        "realized_slippage_bps": 10.0,
    },
    {
        "decision_time": "2026-01-01T06:00:00Z",
        "spread_bps": 7.2,
        "volatility_estimate": 0.023,
        "order_notional_to_depth": 0.27,
        "funding_rate_abs": 0.0004,
        "liquidity_score": 0.60,
        "realized_slippage_bps": 11.8,
    },
    {
        "decision_time": "2026-01-01T07:00:00Z",
        "spread_bps": 8.0,
        "volatility_estimate": 0.026,
        "order_notional_to_depth": 0.30,
        "funding_rate_abs": 0.0005,
        "liquidity_score": 0.55,
        "realized_slippage_bps": 13.0,
    },
]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", required=True)
    args = parser.parse_args()

    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)

    feature_names = (
        "spread_bps",
        "volatility_estimate",
        "order_notional_to_depth",
        "funding_rate_abs",
        "liquidity_score",
    )
    x, y, binding = build_feature_matrix_binding(
        FIXTURE_ROWS,
        feature_names=feature_names,
        target_name="realized_slippage_bps",
    )
    model = fit_ols_lstsq(x, y, binding)
    design_all = np.column_stack([np.ones(x.shape[0]), x])
    coeff_values = np.asarray(list(model.coefficients.values()), dtype=float)
    predicted = design_all @ coeff_values
    calibration = build_cost_model_calibration_evidence(
        model, observed_target_bps=y, predicted_target_bps=predicted
    )

    report = {
        "verdict": "OFFLINE_LINEAR_COST_MODEL_DIAGNOSTICS_V0_PASS_OR_FAIL_CLOSED",
        "offline_only": True,
        "runtime_authority": False,
        "order_authority": False,
        "promotion_pass_authority": False,
        "backtest_cost_default_change": False,
        "calibration": to_jsonable(calibration),
    }
    (out / "offline_linear_cost_model_diagnostics_v0.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print("VERDICT=OFFLINE_LINEAR_COST_MODEL_DIAGNOSTICS_V0_PASS_OR_FAIL_CLOSED")
    print(f"REPORT={out / 'offline_linear_cost_model_diagnostics_v0.json'}")
    print(f"STATUS={calibration.status}")
    print("OFFLINE_ONLY=true")
    print("RUNTIME_AUTHORITY=false")
    print("ORDER_AUTHORITY=false")
    print("PROMOTION_PASS_AUTHORITY=false")
    print("BACKTEST_COST_DEFAULT_CHANGE=false")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
