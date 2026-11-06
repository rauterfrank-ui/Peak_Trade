from __future__ import annotations

import re
from pathlib import Path


def _read(path: str) -> str:
    return Path(path).read_text(encoding="utf-8")


def test_run_strategy_from_config_has_no_plots_flag_and_wiring() -> None:
    txt = _read("scripts/run_strategy_from_config.py")
    assert "--no-plots" in txt
    assert re.search(r"save_plots_flag\s*=\s*not\s+args\.no_plots", txt)


def test_run_portfolio_backtest_has_no_plots_flag_and_wiring() -> None:
    txt = _read("scripts/run_portfolio_backtest.py")
    assert "--no-plots" in txt
    assert re.search(r"save_plots_flag\s*=\s*not\s+args\.no_plots", txt)
