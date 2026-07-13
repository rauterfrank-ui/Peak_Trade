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
from src.research.offline_linear_cost_diagnostic_row_materializer_v0 import (
    MaterializationStatus,
    TARGET_NAME,
    materialize_offline_linear_cost_diagnostic_rows_v0,
)

AUTHORITY_EFFECT = "NONE"
RUNTIME_EFFECT = "NONE"

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


def _load_jsonl(path: Path) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        payload = json.loads(stripped)
        if isinstance(payload, dict):
            rows.append(payload)
    return rows


def _materializer_rows_to_feature_rows(
    materialized_rows: tuple[dict[str, object], ...],
) -> list[dict[str, object]]:
    feature_rows: list[dict[str, object]] = []
    for row in materialized_rows:
        feature_rows.append(
            {
                "decision_time": row["decision_time"],
                "spread_bps": row["spread_bps"],
                "volatility_estimate": row["volatility_estimate"],
                "order_notional": row["order_notional"],
                "funding_rate_abs": row.get("funding_rate_abs"),
                "liquidity_score": row.get("liquidity_score"),
                TARGET_NAME: row[TARGET_NAME],
            }
        )
    return feature_rows


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", required=True)
    parser.add_argument("--trade-ledger", type=Path, default=None)
    parser.add_argument("--entry-bar-snapshots", type=Path, default=None)
    parser.add_argument(
        "--fixture-scaffold",
        action="store_true",
        help="Scaffolding-only fixture rows; never counted as productive samples.",
    )
    args = parser.parse_args()

    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)

    fixture_scaffold_only = bool(args.fixture_scaffold)
    trade_ledger_rows: list[dict[str, object]] = []
    entry_bar_snapshots: list[dict[str, object]] = []
    if args.trade_ledger is not None:
        trade_ledger_rows = _load_jsonl(args.trade_ledger)
    if args.entry_bar_snapshots is not None:
        entry_bar_snapshots = _load_jsonl(args.entry_bar_snapshots)

    materialization = materialize_offline_linear_cost_diagnostic_rows_v0(
        trade_ledger_rows=trade_ledger_rows,
        entry_bar_reference_snapshots=entry_bar_snapshots,
    )
    productive_rows = _materializer_rows_to_feature_rows(materialization.rows)
    n_productive_samples = len(productive_rows)
    ols_executed = False
    calibration_payload: dict[str, object] | None = None
    min_ols_samples = 5

    if n_productive_samples >= min_ols_samples:
        feature_names = (
            "spread_bps",
            "volatility_estimate",
            "order_notional",
        )
        x, y, binding = build_feature_matrix_binding(
            productive_rows,
            feature_names=feature_names,
            target_name=TARGET_NAME,
        )
        model = fit_ols_lstsq(x, y, binding)
        design_all = np.column_stack([np.ones(x.shape[0]), x])
        coeff_values = np.asarray(list(model.coefficients.values()), dtype=float)
        predicted = design_all @ coeff_values
        calibration_payload = to_jsonable(
            build_cost_model_calibration_evidence(
                model, observed_target_bps=y, predicted_target_bps=predicted
            )
        )
        ols_executed = True
    elif fixture_scaffold_only:
        x, y, binding = build_feature_matrix_binding(
            FIXTURE_ROWS,
            feature_names=(
                "spread_bps",
                "volatility_estimate",
                "order_notional_to_depth",
                "funding_rate_abs",
                "liquidity_score",
            ),
            target_name="realized_slippage_bps",
        )
        model = fit_ols_lstsq(x, y, binding)
        design_all = np.column_stack([np.ones(x.shape[0]), x])
        coeff_values = np.asarray(list(model.coefficients.values()), dtype=float)
        predicted = design_all @ coeff_values
        calibration_payload = to_jsonable(
            build_cost_model_calibration_evidence(
                model, observed_target_bps=y, predicted_target_bps=predicted
            )
        )
        ols_executed = True

    if n_productive_samples == 0 and not fixture_scaffold_only:
        verdict = "OFFLINE_LINEAR_COST_MODEL_DIAGNOSTICS_V0_FAIL_CLOSED"
        status = materialization.status.value
    else:
        verdict = "OFFLINE_LINEAR_COST_MODEL_DIAGNOSTICS_V0_PASS_OR_FAIL_CLOSED"
        status = (
            materialization.status.value
            if n_productive_samples > 0
            else MaterializationStatus.INSUFFICIENT_DATA.value
        )

    report = {
        "verdict": verdict,
        "offline_only": True,
        "runtime_authority": False,
        "order_authority": False,
        "promotion_pass_authority": False,
        "backtest_cost_default_change": False,
        "fixture_scaffold_only": fixture_scaffold_only,
        "n_productive_samples": n_productive_samples,
        "n_fixture_scaffold_rows": len(FIXTURE_ROWS) if fixture_scaffold_only else 0,
        "ols_executed": ols_executed,
        "materialization_status": status,
        "materialization_digest": materialization.materialization_digest,
        "admissible_sample_count": materialization.admissible_count,
        "rejected_row_count": len(materialization.rejected),
        "target_name": TARGET_NAME,
        "calibration": calibration_payload,
    }
    (out / "offline_linear_cost_model_diagnostics_v0.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(f"VERDICT={verdict}")
    print(f"REPORT={out / 'offline_linear_cost_model_diagnostics_v0.json'}")
    print(f"MATERIALIZATION_STATUS={status}")
    print(f"N_PRODUCTIVE_SAMPLES={n_productive_samples}")
    print(f"OLS_EXECUTED={'true' if ols_executed else 'false'}")
    print("OFFLINE_ONLY=true")
    print("RUNTIME_AUTHORITY=false")
    print("ORDER_AUTHORITY=false")
    print("PROMOTION_PASS_AUTHORITY=false")
    print("BACKTEST_COST_DEFAULT_CHANGE=false")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
