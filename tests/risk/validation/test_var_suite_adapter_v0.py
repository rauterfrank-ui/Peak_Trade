"""Contract tests for offline VaR suite adapter (v0)."""

from __future__ import annotations

import ast
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from src.risk.validation.suite_runner import VaRBacktestSuiteResult, run_var_backtest_suite
from src.risk.validation.var_suite_adapter import (
    AlignedVaRBacktestInputs,
    align_var_backtest_inputs,
    build_rolling_historical_var_forecast,
    normalize_var_sign_to_positive_loss,
    run_rolling_historical_var_backtest_suite,
)


class TestLookAheadFreedom:
    def test_forecast_at_t_unchanged_when_return_at_t_changes(self):
        dates = pd.date_range("2024-01-01", periods=12, freq="D")
        returns = pd.Series(
            [0.01, 0.01, 0.01, -0.02, 0.01, 0.01, 0.01, -0.01, 0.02, 0.01, -0.015, 0.005],
            index=dates,
            dtype=float,
        )
        window = 3
        t = 3

        forecast_before = build_rolling_historical_var_forecast(
            returns, window=window, confidence_level=0.95
        )

        returns_modified = returns.copy()
        returns_modified.iloc[t] = -0.50

        forecast_after = build_rolling_historical_var_forecast(
            returns_modified, window=window, confidence_level=0.95
        )

        assert forecast_before.iloc[t] == forecast_after.iloc[t]
        assert forecast_before.iloc[t + 1] != forecast_after.iloc[t + 1]


class TestRollingWindowSemantics:
    def test_first_valid_forecast_after_required_window(self):
        dates = pd.date_range("2024-01-01", periods=15, freq="D")
        returns = pd.Series([0.01, -0.02, 0.015, -0.01, 0.005] * 3, index=dates)
        window = 5

        forecast = build_rolling_historical_var_forecast(
            returns, window=window, confidence_level=0.95
        )

        assert forecast.iloc[:window].isna().all()
        assert forecast.iloc[window:].notna().all()


class TestSignNormalization:
    def test_negative_var_normalized_to_positive(self):
        idx = pd.date_range("2024-01-01", periods=4, freq="D")
        var_series = pd.Series([-0.03, -0.02, 0.01, -0.005], index=idx)

        normalized = normalize_var_sign_to_positive_loss(var_series)

        pd.testing.assert_series_equal(
            normalized,
            pd.Series([0.03, 0.02, 0.01, 0.005], index=idx),
        )

    def test_positive_var_unchanged(self):
        idx = pd.date_range("2024-01-01", periods=3, freq="D")
        var_series = pd.Series([0.03, 0.02, 0.01], index=idx)

        normalized = normalize_var_sign_to_positive_loss(var_series)

        pd.testing.assert_series_equal(normalized, var_series)


class TestStrictAlignment:
    def test_label_based_intersection_no_position_mismatch(self):
        returns = pd.Series([0.01, -0.03, 0.02, 0.01], index=["a", "b", "c", "d"])
        var_series = pd.Series([0.02, 0.02, 0.02, 0.02], index=["b", "c", "d", "e"])

        aligned = align_var_backtest_inputs(returns, var_series)

        assert isinstance(aligned, AlignedVaRBacktestInputs)
        assert list(aligned.returns.index) == ["b", "c", "d"]
        assert aligned.returns.index.equals(aligned.var_series.index)
        assert len(aligned.returns) == len(aligned.var_series) == 3
        assert aligned.returns.loc["b"] == -0.03
        assert aligned.var_series.loc["b"] == 0.02


class TestFailClosedInputs:
    @pytest.mark.parametrize(
        "returns,var_series,match",
        [
            (
                pd.Series([0.01, np.nan], index=[0, 1]),
                pd.Series([0.02, 0.02], index=[0, 1]),
                "NaN or Inf",
            ),
            (
                pd.Series([0.01, 0.02], index=[0, 0]),
                pd.Series([0.02, 0.02], index=[0, 1]),
                "unique",
            ),
        ],
    )
    def test_invalid_alignment_inputs_rejected(self, returns, var_series, match):
        with pytest.raises(ValueError, match=match):
            align_var_backtest_inputs(returns, var_series)

    def test_inf_var_rejected_by_sign_normalizer(self):
        var_series = pd.Series([0.02, np.inf], index=[0, 1])
        with pytest.raises(ValueError, match="NaN or Inf"):
            normalize_var_sign_to_positive_loss(var_series)

    def test_empty_intersection_rejected(self):
        returns = pd.Series([0.01], index=["a"])
        var_series = pd.Series([0.02], index=["b"])

        with pytest.raises(ValueError, match="no overlapping"):
            align_var_backtest_inputs(returns, var_series)


class TestSuiteIntegration:
    def test_adapter_delegates_to_existing_suite_runner(self):
        dates = pd.date_range("2024-01-01", periods=30, freq="D")
        rng = np.random.default_rng(42)
        returns = pd.Series(rng.normal(0.001, 0.015, size=30), index=dates)

        result = run_rolling_historical_var_backtest_suite(
            returns,
            window=10,
            confidence_level=0.95,
            significance=0.05,
        )

        assert isinstance(result, VaRBacktestSuiteResult)
        assert result.observations > 0
        assert result.kupiec_pof_result in {"PASS", "FAIL"}
        assert result.christoffersen_ind_result in {"PASS", "FAIL"}
        assert result.christoffersen_cc_result in {"PASS", "FAIL"}
        assert 0.0 <= result.kupiec_pof_pvalue <= 1.0
        assert 0.0 <= result.christoffersen_ind_pvalue <= 1.0
        assert 0.0 <= result.christoffersen_cc_pvalue <= 1.0


class TestViolationSemantics:
    def test_negative_return_below_negative_var_is_breach(self):
        idx = pd.date_range("2024-01-01", periods=1, freq="D")
        returns = pd.Series([-0.05], index=idx)
        var_series = pd.Series([0.03], index=idx)

        result = run_var_backtest_suite(returns, var_series, confidence_level=0.95)

        assert result.breaches == 1
        assert returns.iloc[0] < -var_series.iloc[0]


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

    def test_adapter_module_has_no_trading_or_network_imports(self):
        module_path = Path("src/risk/validation/var_suite_adapter.py")
        source = module_path.read_text(encoding="utf-8")
        tree = ast.parse(source)

        imported_modules: set[str] = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imported_modules.add(alias.name)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imported_modules.add(node.module)

        for forbidden in self._FORBIDDEN_IMPORTS:
            assert not any(
                mod == forbidden or mod.startswith(f"{forbidden}.") for mod in imported_modules
            ), f"forbidden import: {forbidden}"
