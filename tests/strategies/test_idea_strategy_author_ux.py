"""Smoke tests for strategy-ideas sandbox (E8 author UX)."""

from __future__ import annotations

import importlib.util
from pathlib import Path

import pandas as pd
import pytest

from src.strategies.ideas.template_example import IdeaExampleStrategy


def _load_new_idea_script():
    root = Path(__file__).resolve().parents[2]
    path = root / "scripts" / "new_idea_strategy.py"
    spec = importlib.util.spec_from_file_location("new_idea_strategy", path)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_idea_example_strategy_flat_signals() -> None:
    s = IdeaExampleStrategy(param1=5, param2=0.01)
    df = pd.DataFrame({"close": range(100, 120)}, index=pd.date_range("2024-01-01", periods=20, freq="h"))
    out = s.generate_signals(df)
    assert isinstance(out, pd.Series)
    assert len(out) == len(df)
    assert (out == 0).all()
    assert out.dtype == int


def test_idea_example_strategy_missing_column_raises() -> None:
    s = IdeaExampleStrategy(param1=3, param2=0.01, price_col="close")
    df = pd.DataFrame({"open": [1, 2, 3]})
    with pytest.raises(ValueError, match="close"):
        s.generate_signals(df)


def test_idea_example_validate_calls_internal() -> None:
    s = IdeaExampleStrategy(param1=10, param2=0.02)
    s.validate()


def test_new_idea_strategy_helpers() -> None:
    mod = _load_new_idea_script()
    assert mod.snake_to_camel("rsi_keltner") == "RsiKeltner"
    assert mod.sanitize_name("  My_Strategy  ") == "my_strategy"
    with pytest.raises(ValueError):
        mod.sanitize_name("bad-name")
