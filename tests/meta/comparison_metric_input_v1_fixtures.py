"""Shared fixtures for comparison_metric_input_v1 tests."""

from __future__ import annotations

import json
import shutil
import uuid
from pathlib import Path
from typing import Any

import pandas as pd
import pytest

from src.experiments.base import ExperimentConfig, ParamSweep
from src.experiments.experiment_identity_manifest_v1 import produce_experiment_identity_manifest_v1
from src.experiments.tracking.run_summary import RunSummary
from src.governance.promotion_loop.candidate_lineage_manifest_v1 import lineage_ref_to_mapping
from src.governance.promotion_loop.backtest_lineage_ref_producer_v1 import (
    RUN_SUMMARY_REL_PATH,
    build_backtest_lineage_ref_from_run_summary,
)
from src.governance.promotion_loop.experiment_lineage_ref_producer_v1 import (
    produce_experiment_lineage_ref_v1,
)
from src.governance.promotion_loop.var_suite_lineage_ref_producer_v1 import (
    produce_var_suite_lineage_ref_v1,
)
from src.risk.validation.var_suite_backtest_wiring_v1 import SUITE_REPORT_JSON

REPO_ROOT = Path(__file__).resolve().parents[2]
_DURABLE_OUTPUT_ROOT = REPO_ROOT / ".comparison_metric_input_pytest_outputs"

FIXED_STARTED = "2025-01-15T10:00:00+00:00"
FIXED_FINISHED = "2025-01-20T10:00:00+00:00"
RUN_ID = "cmp-metric-run-001"
SYMBOLS = ["ETH/USDT:USDT"]

GOLDEN_METRICS = {
    "sharpe": 7.463815111313766,
    "volatility": 0.22422070129952124,
    "total_return": 0.04,
    "max_drawdown": 0.014563106796116505,
    "profit_factor": 4.0,
    "trade_count": 4,
}
GOLDEN_EQUITY_SERIES_DIGEST = "8369d37532c0c0984f8e692f172892c0f6cd7ffe47a85ee6ecbf012a7dc7f53a"
GOLDEN_TRADE_LEDGER_DIGEST = "2b326c7d1f5bd78ec890458eb89cadc0633e4dbfd38d0a740d23c8dea0cd5c6b"
GOLDEN_SOURCE_DIGEST = "ecd909cabf20131fa39d6ce1aa03d73f29bbd1a77795a2c2fe2fcb4c16c5a547"


@pytest.fixture(autouse=True)
def _allow_tmp_output(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "src.meta.learning_loop.comparison_metric_input_v1.io.is_under_tmp",
        lambda _path: False,
    )


@pytest.fixture
def durable_output_dir() -> Path:
    _DURABLE_OUTPUT_ROOT.mkdir(exist_ok=True)
    path = _DURABLE_OUTPUT_ROOT / uuid.uuid4().hex
    path.mkdir(parents=True, exist_ok=True)
    yield path
    if path.exists():
        shutil.rmtree(path, ignore_errors=True)
    for staging in _DURABLE_OUTPUT_ROOT.glob(".comparison_metric_input_staging_*"):
        shutil.rmtree(staging, ignore_errors=True)
    for staging in _DURABLE_OUTPUT_ROOT.glob(".experiment_identity_staging_*"):
        shutil.rmtree(staging, ignore_errors=True)


def comparison_source_ref(ref_mapping: dict[str, Any]) -> dict[str, str]:
    return {
        "owner_domain": str(ref_mapping["owner_domain"]),
        "ref_type": str(ref_mapping["ref_type"]).upper(),
        "ref_id": str(ref_mapping["ref_id"]),
        "digest": str(ref_mapping["digest"]),
    }


def sample_experiment_config(**overrides: Any) -> ExperimentConfig:
    base = ExperimentConfig(
        name="cmp metric test",
        strategy_name="ma_crossover",
        param_sweeps=[ParamSweep(name="fast", values=[10])],
        symbols=SYMBOLS,
        timeframe="1d",
        start_date="2025-01-01",
        end_date="2025-01-20",
        initial_capital=10000.0,
        base_params={"return_basis": "NET_EQUITY_CURVE"},
    )
    for key, value in overrides.items():
        setattr(base, key, value)
    return base


def write_equity_csv(run_dir: Path, values: list[float] | None = None) -> None:
    values = values or [10000.0, 10100.0, 10050.0, 10200.0, 10300.0, 10150.0, 10400.0]
    rows = []
    for idx, equity in enumerate(values):
        rows.append({"timestamp": f"2025-01-{idx + 1:02d}T00:00:00+00:00", "equity": equity})
    pd.DataFrame(rows).to_csv(run_dir / "equity.csv", index=False)


def write_trades_parquet(run_dir: Path, pnls: list[float] | None = None) -> None:
    pnls = pnls or [100.0, -50.0, 75.0, 25.0]
    pd.DataFrame({"pnl": pnls}).to_parquet(run_dir / "trades.parquet", index=False)


def write_config_snapshot(run_dir: Path) -> None:
    payload = {
        "meta": {"data_source": "synthetic_fixture_v1"},
        "params": {
            "symbols": SYMBOLS,
            "timeframe": "1d",
            "initial_capital": 10000.0,
            "return_basis": "NET_EQUITY_CURVE",
            "fee_model": "PROVABLY_ZERO",
            "slippage_model": "PROVABLY_ZERO",
        },
    }
    (run_dir / "config_snapshot.json").write_text(json.dumps(payload), encoding="utf-8")


def write_run_summary(run_dir: Path, *, run_id: str = RUN_ID) -> RunSummary:
    summary = RunSummary(
        run_id=run_id,
        started_at_utc=FIXED_STARTED,
        finished_at_utc=FIXED_FINISHED,
        status="FINISHED",
        params={
            "symbols": SYMBOLS,
            "timeframe": "1d",
            "initial_capital": 10000.0,
        },
    )
    summary.write_json(run_dir / RUN_SUMMARY_REL_PATH)
    return summary


def build_backtest_run_dir(tmp_path: Path, *, run_id: str = RUN_ID) -> tuple[Path, dict[str, str]]:
    run_dir = tmp_path / run_id
    run_dir.mkdir(parents=True)
    summary = write_run_summary(run_dir, run_id=run_id)
    write_config_snapshot(run_dir)
    write_equity_csv(run_dir)
    write_trades_parquet(run_dir)
    ref = build_backtest_lineage_ref_from_run_summary(summary)
    return run_dir, comparison_source_ref(lineage_ref_to_mapping(ref))


def build_experiment_bundle(
    tmp_path: Path,
    completed_run_dir: Path,
) -> tuple[Path, dict[str, str], Path]:
    manifest_dir = _DURABLE_OUTPUT_ROOT / f"identity_{uuid.uuid4().hex}"
    produce_experiment_identity_manifest_v1(
        sample_experiment_config(),
        manifest_dir,
        source_experiment_id="source-exp-001",
    )
    lineage = produce_experiment_lineage_ref_v1(manifest_dir=manifest_dir)
    ref = comparison_source_ref(lineage_ref_to_mapping(lineage.ref))
    return manifest_dir, ref, completed_run_dir


def build_var_suite_bundle(
    tmp_path: Path,
    *,
    companion_run_dir: Path,
    backtest_ref: dict[str, str],
) -> tuple[Path, dict[str, str], dict[str, str]]:
    suite_dir = tmp_path / "suite_run_candidate"
    suite_dir.mkdir()
    report = {"overall_result": "PASS", "checks": []}
    (suite_dir / SUITE_REPORT_JSON).write_text(json.dumps(report), encoding="utf-8")
    var_ref = comparison_source_ref(
        lineage_ref_to_mapping(produce_var_suite_lineage_ref_v1(report_dir=suite_dir).ref)
    )
    return suite_dir, var_ref, backtest_ref
