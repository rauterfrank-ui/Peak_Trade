"""
run_backtest.py: canonical load_strategy() migration (offline, fail-closed).
"""

from __future__ import annotations

import ast
import importlib
import inspect
import subprocess
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import numpy as np
import pandas as pd
import pytest

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

import scripts.run_backtest as run_backtest_script

TARGET_SCRIPT = project_root / "scripts/run_backtest.py"
MA_CROSSOVER_KEY = "ma_crossover"
MOMENTUM_KEY = "momentum_1h"
RSI_REVERSION_KEY = "rsi_reversion"
EL_KAROUI_ALIAS_KEY = "el_karoui_vol_v1"

FORBIDDEN_IMPORTS = ("create_strategy_from_config",)


def _read_source() -> str:
    return TARGET_SCRIPT.read_text(encoding="utf-8")


def _sample_ohlcv(n: int = 80) -> pd.DataFrame:
    np.random.seed(42)
    index = pd.date_range("2024-01-01", periods=n, freq="h")
    close = 100.0 + np.cumsum(np.random.randn(n))
    return pd.DataFrame(
        {
            "open": close * 0.999,
            "high": close * 1.002,
            "low": close * 0.998,
            "close": close,
            "volume": np.full(n, 1000.0),
        },
        index=index,
    )


def test_module_imports_without_main_side_effects() -> None:
    with patch.object(run_backtest_script, "main") as main_mock:
        importlib.reload(run_backtest_script)
    main_mock.assert_not_called()


def test_source_has_no_create_strategy_from_config() -> None:
    tree = ast.parse(_read_source())
    imported = {
        alias.name
        for node in tree.body
        if isinstance(node, ast.ImportFrom) and node.module
        for alias in node.names
    }
    assert "create_strategy_from_config" not in imported


def test_source_uses_load_strategy() -> None:
    assert "load_strategy" in _read_source()


def test_source_has_no_parallel_strategy_registry_assignment() -> None:
    tree = ast.parse(_read_source())
    assigned_names = {
        node.targets[0].id
        for node in tree.body
        if isinstance(node, ast.Assign)
        and len(node.targets) == 1
        and isinstance(node.targets[0], ast.Name)
    }
    assert "STRATEGY_REGISTRY" not in assigned_names


def test_build_strategy_params_includes_stop_pct_default_for_registry_key() -> None:
    from src.core.peak_config import PeakConfig

    raw = {"environment": {"mode": "backtest"}, "strategy": {}}
    cfg = PeakConfig(raw=raw)
    params = run_backtest_script._build_strategy_params_from_config(cfg, MA_CROSSOVER_KEY)
    assert params["stop_pct"] == 0.02
    assert "fast_window" not in params


def test_build_strategy_params_source_uses_load_strategy_for_registry_path() -> None:
    source = inspect.getsource(run_backtest_script._build_strategy_params_from_config)
    assert "load_strategy" in source
    assert "spec.cls.from_config" not in source


def test_resolve_strategy_signal_fn_source_uses_load_strategy_only() -> None:
    source = inspect.getsource(run_backtest_script._resolve_strategy_signal_fn)
    assert "load_strategy" in source
    assert "spec.cls.from_config" not in source
    assert "generate_signals(df" not in source


def test_build_strategy_params_calls_load_strategy_for_alias_key() -> None:
    from src.core.peak_config import PeakConfig

    raw = {
        "environment": {"mode": "backtest"},
        "research": {"allow_r_and_d_strategies": True},
        "strategy": {"el_karoui_vol_model": {}},
    }
    cfg = PeakConfig(raw=raw)

    with patch.object(run_backtest_script, "load_strategy") as load_mock:
        load_mock.return_value = MagicMock()
        params = run_backtest_script._build_strategy_params_from_config(cfg, EL_KAROUI_ALIAS_KEY)

    load_mock.assert_called_once_with("el_karoui_vol_model")
    assert params["stop_pct"] == 0.02


def test_resolve_strategy_signal_fn_calls_load_strategy_for_alias_key() -> None:
    with patch.object(run_backtest_script, "load_strategy") as load_mock:
        load_mock.return_value = MagicMock()
        run_backtest_script._resolve_strategy_signal_fn(EL_KAROUI_ALIAS_KEY)

    load_mock.assert_called_once_with("el_karoui_vol_model")


def test_build_strategy_params_calls_load_strategy_for_registry_validation() -> None:
    from src.core.peak_config import PeakConfig

    raw = {
        "environment": {"mode": "backtest"},
        "strategy": {
            MA_CROSSOVER_KEY: {"fast_window": 10, "slow_window": 50, "price_col": "close"}
        },
    }
    cfg = PeakConfig(raw=raw)

    with patch.object(run_backtest_script, "load_strategy") as load_mock:
        load_mock.return_value = MagicMock()
        params = run_backtest_script._build_strategy_params_from_config(cfg, MA_CROSSOVER_KEY)

    load_mock.assert_called_once_with(MA_CROSSOVER_KEY)
    assert params["fast_window"] == 10
    assert params["stop_pct"] == 0.02


def test_build_strategy_params_isolated_per_strategy_key() -> None:
    from src.core.peak_config import PeakConfig

    cfg = PeakConfig(
        raw={
            "environment": {"mode": "backtest"},
            "strategy": {
                MA_CROSSOVER_KEY: {"fast_window": 10, "slow_window": 50, "price_col": "close"},
                MOMENTUM_KEY: {
                    "lookback_period": 15,
                    "entry_threshold": 0.02,
                    "exit_threshold": -0.01,
                },
            },
        }
    )
    ma_params = run_backtest_script._build_strategy_params_from_config(cfg, MA_CROSSOVER_KEY)
    mom_params = run_backtest_script._build_strategy_params_from_config(cfg, MOMENTUM_KEY)

    assert "lookback_period" not in ma_params
    assert "fast_window" not in mom_params
    assert ma_params["fast_window"] == 10
    assert mom_params["lookback_period"] == 15


def test_build_strategy_params_unknown_strategy_fails_closed() -> None:
    from src.core.peak_config import PeakConfig

    cfg = PeakConfig(raw={"environment": {"mode": "backtest"}, "strategy": {}})
    with pytest.raises(KeyError):
        run_backtest_script._build_strategy_params_from_config(cfg, "definitely_not_a_strategy_xyz")


def test_build_strategy_params_includes_explicit_section_values() -> None:
    from src.core.peak_config import PeakConfig

    raw = {
        "environment": {"mode": "backtest"},
        "strategy": {
            MA_CROSSOVER_KEY: {
                "fast_window": 10,
                "slow_window": 50,
                "price_col": "close",
                "stop_pct": 0.03,
            },
        },
    }
    cfg = PeakConfig(raw=raw)
    params = run_backtest_script._build_strategy_params_from_config(cfg, MA_CROSSOVER_KEY)
    assert params["fast_window"] == 10
    assert params["slow_window"] == 50
    assert params["stop_pct"] == 0.03


@pytest.mark.parametrize(
    "strategy_key,strategy_section,n_bars",
    [
        (
            MA_CROSSOVER_KEY,
            {MA_CROSSOVER_KEY: {"fast_window": 10, "slow_window": 50, "price_col": "close"}},
            80,
        ),
        (
            MOMENTUM_KEY,
            {
                MOMENTUM_KEY: {
                    "lookback_period": 15,
                    "entry_threshold": 0.02,
                    "exit_threshold": -0.01,
                }
            },
            120,
        ),
        (
            RSI_REVERSION_KEY,
            {RSI_REVERSION_KEY: {"rsi_period": 14, "oversold": 30, "overbought": 70}},
            120,
        ),
    ],
)
def test_signal_equivalence_vs_create_strategy_from_config(
    strategy_key: str,
    strategy_section: dict,
    n_bars: int,
) -> None:
    from src.core.peak_config import PeakConfig
    from src.strategies.registry import create_strategy_from_config

    raw = {"environment": {"mode": "backtest"}, "strategy": strategy_section}
    cfg = PeakConfig(raw=raw)
    df = _sample_ohlcv(n_bars)

    legacy = create_strategy_from_config(strategy_key, cfg).generate_signals(df)
    params = run_backtest_script._build_strategy_params_from_config(cfg, strategy_key)
    canonical = run_backtest_script._resolve_strategy_signal_fn(strategy_key)(df, params)

    pd.testing.assert_series_equal(canonical, legacy)


def test_el_karoui_alias_resolves_via_load_strategy() -> None:
    from src.core.peak_config import PeakConfig
    from src.strategies.registry import create_strategy_from_config

    raw = {
        "environment": {"mode": "backtest"},
        "research": {"allow_r_and_d_strategies": True},
        "strategy": {"el_karoui_vol_model": {}},
    }
    cfg = PeakConfig(raw=raw)
    df = _sample_ohlcv(120)

    legacy = create_strategy_from_config(EL_KAROUI_ALIAS_KEY, cfg).generate_signals(df)
    params = run_backtest_script._build_strategy_params_from_config(cfg, EL_KAROUI_ALIAS_KEY)
    canonical = run_backtest_script._resolve_strategy_signal_fn(EL_KAROUI_ALIAS_KEY)(df, params)

    pd.testing.assert_series_equal(canonical, legacy)


def test_registry_gates_block_r_and_d_without_flag() -> None:
    from src.core.peak_config import PeakConfig

    raw = {"environment": {"mode": "backtest"}, "strategy": {"ehlers_cycle_filter": {}}}
    cfg = PeakConfig(raw=raw)
    with pytest.raises(ValueError, match="R&D-only"):
        run_backtest_script._validate_strategy_registry_gates("ehlers_cycle_filter", cfg)


def test_main_backtest_path_passes_full_params_to_signal_fn() -> None:
    from src.core.peak_config import PeakConfig

    raw = {
        "environment": {"mode": "backtest"},
        "strategy": {
            MA_CROSSOVER_KEY: {"fast_window": 10, "slow_window": 50, "price_col": "close"}
        },
    }
    cfg = PeakConfig(raw=raw)
    captured: dict[str, object] = {}

    def fake_signal_fn(df, params):
        captured["params"] = dict(params)
        captured["df_len"] = len(df)
        return pd.Series(0, index=df.index)

    mock_result = MagicMock()
    mock_result.stats = {
        "total_return": 0.0,
        "max_drawdown": 0.0,
        "sharpe": 0.0,
        "total_trades": 0,
        "win_rate": 0.0,
        "profit_factor": 0.0,
    }
    mock_result.equity_curve = pd.Series(
        [10000.0, 10000.0], index=pd.date_range("2024-01-01", periods=2, freq="h")
    )

    with (
        patch.object(run_backtest_script, "parse_args") as parse_mock,
        patch.object(run_backtest_script, "load_config", return_value=cfg),
        patch.object(run_backtest_script, "load_ohlcv_data", return_value=_sample_ohlcv()),
        patch.object(
            run_backtest_script, "build_position_sizer_from_config", return_value=MagicMock()
        ),
        patch.object(
            run_backtest_script, "build_risk_manager_from_config", return_value=MagicMock()
        ),
        patch.object(
            run_backtest_script, "_resolve_strategy_signal_fn", return_value=fake_signal_fn
        ),
        patch.object(
            run_backtest_script.BacktestEngine, "run_realistic", return_value=mock_result
        ) as run_mock,
        patch.object(run_backtest_script, "log_backtest_result", return_value="reg-1"),
        patch.object(run_backtest_script, "ensure_run_dir", return_value=Path("/tmp/run")),
        patch.object(
            run_backtest_script, "write_config_snapshot", return_value=Path("/tmp/cfg.json")
        ),
        patch.object(run_backtest_script, "write_stats_json", return_value=Path("/tmp/stats.json")),
        patch.object(run_backtest_script, "write_equity_csv", return_value=Path("/tmp/eq.csv")),
        patch.object(run_backtest_script, "write_trades_parquet_optional", return_value=None),
        patch.object(
            run_backtest_script, "write_report_snippet_md", return_value=Path("/tmp/snippet.md")
        ),
        patch("pathlib.Path.exists", return_value=True),
    ):
        args = MagicMock()
        args.config = "config.toml"
        args.strategy = MA_CROSSOVER_KEY
        args.data_file = None
        args.start_date = None
        args.end_date = None
        args.bars = 80
        args.tag = None
        args.verbose = False
        args.save_report = None
        args.run_id = "test-run"
        args.results_dir = "results"
        args.tracker = "null"
        args.no_report = True
        parse_mock.return_value = args

        rc = run_backtest_script.main()

    assert rc == 0
    run_mock.assert_called_once()
    call_kwargs = run_mock.call_args.kwargs
    assert call_kwargs["strategy_params"]["fast_window"] == 10
    assert call_kwargs["strategy_params"]["slow_window"] == 50
    assert call_kwargs["strategy_params"]["stop_pct"] == 0.02
    call_kwargs["strategy_signal_fn"](call_kwargs["df"], call_kwargs["strategy_params"])
    assert captured["params"]["fast_window"] == 10
    assert captured["params"]["slow_window"] == 50


def test_unknown_strategy_fails_closed_at_gates() -> None:
    from src.core.peak_config import PeakConfig

    cfg = PeakConfig(raw={"environment": {"mode": "backtest"}})
    with pytest.raises(KeyError):
        run_backtest_script._validate_strategy_registry_gates("definitely_not_a_strategy_xyz", cfg)


def test_load_strategy_no_network_calls() -> None:
    from src.strategies import load_strategy

    with patch("urllib.request.urlopen") as urlopen:
        load_strategy(MA_CROSSOVER_KEY)
        load_strategy(MOMENTUM_KEY)
    urlopen.assert_not_called()


def test_import_smoke_no_main_execution() -> None:
    result = subprocess.run(
        [sys.executable, "-c", "import scripts.run_backtest"],
        cwd=project_root,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr


def test_cli_help_smoke() -> None:
    result = subprocess.run(
        [sys.executable, str(TARGET_SCRIPT), "--help"],
        cwd=project_root,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    assert "NO-LIVE" in result.stdout


def test_load_ohlcv_data_dummy_semantics_unchanged() -> None:
    df = run_backtest_script.load_ohlcv_data(None, None, None, n_bars=120)
    assert list(df.columns) == ["open", "high", "low", "close", "volume"]
    assert len(df) == 120
    assert isinstance(df.index, pd.DatetimeIndex)


def test_load_ohlcv_data_missing_file_raises(tmp_path) -> None:
    missing = tmp_path / "missing.csv"
    with pytest.raises(FileNotFoundError, match="Datei nicht gefunden"):
        run_backtest_script.load_ohlcv_data(str(missing), None, None, n_bars=10)


def test_load_ohlcv_data_csv_path_uses_csv_loader_chain(tmp_path, monkeypatch) -> None:
    csv_path = tmp_path / "btc_eur_1h.csv"
    csv_path.write_text("timestamp,open,high,low,close,volume\n", encoding="utf-8")
    raw_df = _sample_ohlcv()
    normalized_df = raw_df.copy()
    loader_calls: list[str] = []
    normalize_calls: list[pd.DataFrame] = []

    class FakeCsvLoader:
        def load(self, path: str) -> pd.DataFrame:
            loader_calls.append(path)
            return raw_df

    class FakeNormalizer:
        def normalize(self, df: pd.DataFrame) -> pd.DataFrame:
            normalize_calls.append(df)
            return normalized_df

    monkeypatch.setattr(run_backtest_script, "CsvLoader", FakeCsvLoader)
    monkeypatch.setattr(run_backtest_script, "DataNormalizer", FakeNormalizer)

    result = run_backtest_script.load_ohlcv_data(str(csv_path), None, None, n_bars=10)

    assert loader_calls == [str(csv_path)]
    assert len(normalize_calls) == 1
    assert result is normalized_df


def test_load_ohlcv_data_parquet_uses_read_parquet_and_normalizer(tmp_path, monkeypatch) -> None:
    parquet_path = tmp_path / "btc_eur_1h.parquet"
    parquet_path.write_bytes(b"parquet-placeholder")
    raw_df = _sample_ohlcv().rename_axis("timestamp").reset_index()
    normalized_df = raw_df.set_index("timestamp")
    read_calls: list[str] = []
    normalize_calls: list[pd.DataFrame] = []

    def fake_read_parquet(path, *args, **kwargs):
        read_calls.append(str(path))
        return raw_df.copy()

    class FakeNormalizer:
        def normalize(self, df: pd.DataFrame) -> pd.DataFrame:
            normalize_calls.append(df)
            return normalized_df

    monkeypatch.setattr(run_backtest_script.pd, "read_parquet", fake_read_parquet)
    monkeypatch.setattr(run_backtest_script, "DataNormalizer", FakeNormalizer)

    result = run_backtest_script.load_ohlcv_data(str(parquet_path), None, None, n_bars=10)

    assert read_calls == [str(parquet_path)]
    assert len(normalize_calls) == 1
    assert list(normalize_calls[0].columns) == ["open", "high", "low", "close", "volume"]
    assert isinstance(normalize_calls[0].index, pd.DatetimeIndex)
    assert result is normalized_df


@pytest.mark.parametrize("suffix", [".parquet", ".pq"])
def test_load_ohlcv_data_parquet_suffixes_supported(tmp_path, monkeypatch, suffix) -> None:
    parquet_path = tmp_path / f"btc_eur_1h{suffix}"
    parquet_path.write_bytes(b"parquet-placeholder")
    sample = _sample_ohlcv()

    monkeypatch.setattr(
        run_backtest_script.pd,
        "read_parquet",
        lambda path, *args, **kwargs: sample.copy(),
    )
    monkeypatch.setattr(
        run_backtest_script,
        "DataNormalizer",
        lambda: MagicMock(normalize=lambda df: df),
    )

    result = run_backtest_script.load_ohlcv_data(str(parquet_path), None, None, n_bars=10)
    assert len(result) == len(sample)
