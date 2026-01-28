from __future__ import annotations

from pathlib import Path

import pandas as pd

from src.backtest.result import BacktestResult
from src.backtest.reporting import save_full_report


def test_save_full_report_no_plots_html_has_no_png_refs(tmp_path: Path) -> None:
    idx = pd.date_range("2024-01-01", periods=10, freq="1h")
    equity = pd.Series(
        [100.0, 101.0, 100.5, 102.0, 103.0, 104.0, 103.5, 105.0, 106.0, 107.0],
        index=idx,
    )
    drawdown = (equity / equity.cummax()) - 1.0

    result = BacktestResult(equity_curve=equity, drawdown=drawdown)
    run_name = "x"

    save_full_report(
        result=result,
        output_dir=tmp_path,
        run_name=run_name,
        save_plots_flag=False,
        save_html_flag=True,
    )

    # Contract: --no-plots must not write PNG artifacts.
    assert not (tmp_path / f"{run_name}_equity.png").exists()
    assert not (tmp_path / f"{run_name}_drawdown.png").exists()

    # HTML stays usable and must not reference missing PNGs.
    html = tmp_path / f"{run_name}_report.html"
    assert html.exists()
    content = html.read_text(encoding="utf-8")
    assert f"{run_name}_equity.png" not in content
    assert f"{run_name}_drawdown.png" not in content
    assert "Charts disabled (--no-plots)." in content
