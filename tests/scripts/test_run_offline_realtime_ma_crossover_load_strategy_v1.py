"""
run_offline_realtime_ma_crossover: canonical load_strategy() migration (offline, fail-closed).
"""

from __future__ import annotations

import ast
import importlib
import subprocess
import sys
from pathlib import Path
from unittest.mock import patch

import numpy as np
import pandas as pd
import pytest

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

TARGET_SCRIPT = project_root / "scripts/run_offline_realtime_ma_crossover.py"
MA_CROSSOVER_KEY = "ma_crossover"


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
    module = importlib.import_module("scripts.run_offline_realtime_ma_crossover")
    with patch.object(module, "main") as main_mock:
        importlib.reload(module)
    main_mock.assert_not_called()


def test_source_has_no_direct_ma_crossover_class_import() -> None:
    tree = ast.parse(_read_source())
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module == "src.strategies.ma_crossover":
            pytest.fail("direct ma_crossover module import remains")
    assert "MACrossoverStrategy" not in _read_source()


def test_source_uses_load_strategy_and_registry_key() -> None:
    source = _read_source()
    assert "load_strategy" in source
    assert MA_CROSSOVER_KEY in source
    assert "MA_CROSSOVER_STRATEGY_KEY" in source


def test_load_strategy_ma_crossover_matches_direct_oop_instance() -> None:
    from src.strategies import load_strategy
    from src.strategies.ma_crossover import MACrossoverStrategy

    df = _sample_ohlcv()
    params = {"fast_window": 10, "slow_window": 30, "price_col": "close"}
    canonical = load_strategy(MA_CROSSOVER_KEY)(df, params)
    legacy = MACrossoverStrategy(fast_window=10, slow_window=30).generate_signals(df)
    pd.testing.assert_series_equal(canonical, legacy)


def test_unknown_strategy_fails_closed() -> None:
    from src.strategies import load_strategy

    with pytest.raises(ValueError, match="Unbekannte Strategie"):
        load_strategy("definitely_not_a_strategy_xyz")


def test_cli_help_smoke_no_runner_execution() -> None:
    result = subprocess.run(
        [sys.executable, str(TARGET_SCRIPT), "--help"],
        cwd=project_root,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0
    assert "fast-window" in result.stdout


def test_import_smoke_no_main_execution() -> None:
    result = subprocess.run(
        [sys.executable, "-c", "import scripts.run_offline_realtime_ma_crossover"],
        cwd=project_root,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr
