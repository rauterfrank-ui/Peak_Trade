"""Contract tests for Package H offline backtest→VaR suite wiring v1."""

from __future__ import annotations

import ast
import json
import shutil
from pathlib import Path
from unittest.mock import patch

import numpy as np
import pandas as pd
import pytest

from src.risk.validation.suite_runner import VaRBacktestSuiteResult
from src.risk.validation.var_suite_backtest_wiring_v1 import (
    SUITE_REPORT_JSON,
    SUITE_REPORT_MD,
    VarSuiteBacktestWiringError,
    load_returns_from_run_dir,
    resolve_backtest_returns,
    run_backtest_var_suite_wiring_v1,
)
from src.risk.validation.var_suite_adapter import run_rolling_historical_var_backtest_suite


def _write_equity_csv(run_dir: Path, *, periods: int = 20) -> None:
    rng = np.random.default_rng(42)
    equity = 100.0 + np.cumsum(rng.normal(0.0, 0.5, size=periods))
    df = pd.DataFrame(
        {
            "date": pd.date_range("2024-01-01", periods=periods, freq="D", tz="UTC"),
            "equity": equity,
        }
    )
    df.to_csv(run_dir / "run_equity.csv", index=False)


def _write_strategy_manifest(manifest_path: Path, strategy_id: str, rel_run_dir: str) -> None:
    manifest_path.write_text(
        f'[strategy_returns]\n{strategy_id} = "{rel_run_dir}"\n',
        encoding="utf-8",
    )


def _sample_suite_result() -> VaRBacktestSuiteResult:
    return VaRBacktestSuiteResult(
        observations=12,
        breaches=1,
        confidence_level=0.95,
        kupiec_pof_result="PASS",
        kupiec_pof_pvalue=0.5,
        basel_traffic_light="GREEN",
        christoffersen_ind_result="PASS",
        christoffersen_ind_pvalue=0.5,
        christoffersen_cc_result="PASS",
        christoffersen_cc_pvalue=0.5,
    )


class TestReturnsLoaderReuse:
    def test_load_returns_from_run_dir_uses_equity_loader(self, tmp_path: Path) -> None:
        run_dir = tmp_path / "run"
        run_dir.mkdir()
        _write_equity_csv(run_dir)
        returns = load_returns_from_run_dir(run_dir)
        assert isinstance(returns, pd.Series)
        assert len(returns) >= 2
        assert np.isfinite(returns.to_numpy(dtype=float)).all()

    def test_missing_run_dir_fail_closed(self, tmp_path: Path) -> None:
        with pytest.raises(VarSuiteBacktestWiringError, match="run_dir not found"):
            load_returns_from_run_dir(tmp_path / "missing")

    def test_empty_run_dir_fail_closed(self, tmp_path: Path) -> None:
        run_dir = tmp_path / "empty"
        run_dir.mkdir()
        with pytest.raises(VarSuiteBacktestWiringError, match="equity load failed"):
            load_returns_from_run_dir(run_dir)


class TestInputContract:
    def test_mutually_exclusive_inputs_fail_closed(self, tmp_path: Path) -> None:
        with pytest.raises(VarSuiteBacktestWiringError, match="mutually exclusive"):
            resolve_backtest_returns(
                run_dir=tmp_path,
                strategy_returns_manifest=tmp_path / "m.toml",
                strategy_id="s1",
            )

    def test_missing_input_fail_closed(self) -> None:
        with pytest.raises(VarSuiteBacktestWiringError, match="exactly one input"):
            resolve_backtest_returns(run_dir=None, strategy_returns_manifest=None, strategy_id=None)

    def test_manifest_requires_strategy_id(self, tmp_path: Path) -> None:
        manifest = tmp_path / "m.toml"
        manifest.write_text("[strategy_returns]\n", encoding="utf-8")
        with pytest.raises(VarSuiteBacktestWiringError, match="strategy_id required"):
            resolve_backtest_returns(
                run_dir=None,
                strategy_returns_manifest=manifest,
                strategy_id=None,
            )

    def test_manifest_loader_path(self, tmp_path: Path) -> None:
        run_dir = tmp_path / "runs" / "r1"
        run_dir.mkdir(parents=True)
        _write_equity_csv(run_dir)
        manifest = tmp_path / "strategy_returns.toml"
        manifest.write_text('[strategy_returns]\ndemo = "runs/r1"\n', encoding="utf-8")
        returns = resolve_backtest_returns(
            run_dir=None,
            strategy_returns_manifest=manifest,
            strategy_id="demo",
            manifest_base_dir=tmp_path,
        )
        assert len(returns) >= 2


class TestAdapterDelegation:
    def test_wiring_calls_existing_adapter(self, tmp_path: Path) -> None:
        run_dir = tmp_path / "run"
        run_dir.mkdir()
        _write_equity_csv(run_dir)
        out = tmp_path / "out"
        expected = _sample_suite_result()

        with patch(
            "src.risk.validation.var_suite_backtest_wiring_v1.run_rolling_historical_var_backtest_suite",
            return_value=expected,
        ) as mocked:
            result = run_backtest_var_suite_wiring_v1(run_dir=run_dir, output_dir=out, window=5)

        mocked.assert_called_once()
        call_kwargs = mocked.call_args.kwargs
        assert call_kwargs["window"] == 5
        assert call_kwargs["confidence_level"] == 0.95
        assert isinstance(mocked.call_args.args[0], pd.Series)
        assert result.suite_result is expected

    def test_end_to_end_uses_real_adapter(self, tmp_path: Path) -> None:
        run_dir = tmp_path / "run"
        run_dir.mkdir()
        _write_equity_csv(run_dir, periods=30)
        out = tmp_path / "out"
        result = run_backtest_var_suite_wiring_v1(run_dir=run_dir, output_dir=out, window=5)
        assert result.suite_result.observations >= 2
        assert result.suite_result.overall_result in {"PASS", "FAIL"}


class TestDeterminism:
    def test_identical_inputs_identical_report_bytes(self, tmp_path: Path) -> None:
        run_dir = tmp_path / "run"
        run_dir.mkdir()
        _write_equity_csv(run_dir, periods=30)

        out1 = tmp_path / "out1"
        out2 = tmp_path / "out2"
        run_backtest_var_suite_wiring_v1(run_dir=run_dir, output_dir=out1, window=5)
        run_backtest_var_suite_wiring_v1(run_dir=run_dir, output_dir=out2, window=5)

        json1 = (out1 / SUITE_REPORT_JSON).read_text(encoding="utf-8")
        json2 = (out2 / SUITE_REPORT_JSON).read_text(encoding="utf-8")
        md1 = (out1 / SUITE_REPORT_MD).read_text(encoding="utf-8")
        md2 = (out2 / SUITE_REPORT_MD).read_text(encoding="utf-8")
        assert json1 == json2
        assert md1 == md2


class TestAtomicPublication:
    def test_publishes_both_reports(self, tmp_path: Path) -> None:
        run_dir = tmp_path / "run"
        run_dir.mkdir()
        _write_equity_csv(run_dir, periods=30)
        out = tmp_path / "out"
        run_backtest_var_suite_wiring_v1(run_dir=run_dir, output_dir=out, window=5)
        assert (out / SUITE_REPORT_JSON).is_file()
        assert (out / SUITE_REPORT_MD).is_file()
        data = json.loads((out / SUITE_REPORT_JSON).read_text(encoding="utf-8"))
        assert "overall_result" in data

    def test_existing_output_dir_fail_closed(self, tmp_path: Path) -> None:
        run_dir = tmp_path / "run"
        run_dir.mkdir()
        _write_equity_csv(run_dir)
        out = tmp_path / "out"
        out.mkdir()
        with pytest.raises(VarSuiteBacktestWiringError, match="already exists"):
            run_backtest_var_suite_wiring_v1(run_dir=run_dir, output_dir=out, window=5)

    def test_adapter_failure_leaves_no_final_output(self, tmp_path: Path) -> None:
        run_dir = tmp_path / "run"
        run_dir.mkdir()
        _write_equity_csv(run_dir)
        out = tmp_path / "out"
        with patch(
            "src.risk.validation.var_suite_backtest_wiring_v1.run_rolling_historical_var_backtest_suite",
            side_effect=ValueError("adapter failed"),
        ):
            with pytest.raises(ValueError, match="adapter failed"):
                run_backtest_var_suite_wiring_v1(run_dir=run_dir, output_dir=out, window=5)
        assert not out.exists()

    def test_publish_failure_cleans_staging(self, tmp_path: Path) -> None:
        run_dir = tmp_path / "run"
        run_dir.mkdir()
        _write_equity_csv(run_dir)
        out = tmp_path / "out"

        with patch(
            "src.risk.validation.var_suite_backtest_wiring_v1._atomic_publish_suite_reports",
            side_effect=VarSuiteBacktestWiringError("publish failed"),
        ):
            with pytest.raises(VarSuiteBacktestWiringError, match="publish failed"):
                run_backtest_var_suite_wiring_v1(run_dir=run_dir, output_dir=out, window=5)
        assert not out.exists()
        assert not any(
            p.name.startswith(".var_suite_backtest_wiring_staging_") for p in tmp_path.iterdir()
        )


class TestInvalidReturns:
    def test_nan_returns_fail_at_adapter(self, tmp_path: Path) -> None:
        run_dir = tmp_path / "run"
        run_dir.mkdir()
        _write_equity_csv(run_dir, periods=30)
        out = tmp_path / "out"
        nan_returns = load_returns_from_run_dir(run_dir)
        nan_returns.iloc[0] = np.nan
        with patch(
            "src.risk.validation.var_suite_backtest_wiring_v1.resolve_backtest_returns",
            return_value=nan_returns,
        ):
            with pytest.raises(ValueError, match="NaN"):
                run_backtest_var_suite_wiring_v1(run_dir=run_dir, output_dir=out, window=5)


class TestAuthorityNeutrality:
    _FORBIDDEN_IMPORTS = (
        "src.execution",
        "src.governance",
        "requests",
        "urllib",
        "httpx",
        "aiohttp",
        "ccxt",
    )

    def test_wiring_module_has_no_trading_or_network_imports(self) -> None:
        module_path = Path("src/risk/validation/var_suite_backtest_wiring_v1.py")
        source = module_path.read_text(encoding="utf-8")
        tree = ast.parse(source)
        imported: set[str] = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imported.add(alias.name)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imported.add(node.module)
        for forbidden in self._FORBIDDEN_IMPORTS:
            assert not any(mod == forbidden or mod.startswith(f"{forbidden}.") for mod in imported)


class TestNoDuplicatedVarCalculation:
    def test_wiring_does_not_import_var_calculation_modules(self) -> None:
        source = Path("src/risk/validation/var_suite_backtest_wiring_v1.py").read_text(
            encoding="utf-8"
        )
        tree = ast.parse(source)
        imported: set[str] = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imported.add(alias.name)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imported.add(node.module)
        assert "src.risk.portfolio_var" not in imported

    def test_real_path_matches_direct_adapter(self, tmp_path: Path) -> None:
        run_dir = tmp_path / "run"
        run_dir.mkdir()
        _write_equity_csv(run_dir, periods=30)
        returns = load_returns_from_run_dir(run_dir)
        direct = run_rolling_historical_var_backtest_suite(returns, window=5)
        out = tmp_path / "out"
        wired = run_backtest_var_suite_wiring_v1(run_dir=run_dir, output_dir=out, window=5)
        assert wired.suite_result.observations == direct.observations
        assert wired.suite_result.breaches == direct.breaches
        assert wired.suite_result.overall_result == direct.overall_result
