# -*- coding: utf-8 -*-
"""Tests for opt-in --diagnostics-dir on scripts/run_sweep_strategy.py (v0)."""

from __future__ import annotations

import json
from pathlib import Path


class TestSweepDiagnosticsExport:
    """Research-only JSON per combination when --diagnostics-dir is set."""

    def test_no_diagnostics_when_flag_omitted(self, tmp_path: Path) -> None:
        diag = tmp_path / "nodiag"
        diag.mkdir()
        from scripts.run_sweep_strategy import main

        rc = main(
            [
                "--strategy",
                "ma_crossover",
                "--param",
                "fast_window=5",
                "--param",
                "slow_window=10",
                "--bars",
                "35",
                "--no-registry",
                "--max-runs",
                "1",
            ]
        )
        assert rc == 0
        assert list(diag.glob("*.json")) == []

    def test_diagnostics_written_with_flag(self, tmp_path: Path) -> None:
        diag = tmp_path / "diag"
        from scripts.run_sweep_strategy import main

        rc = main(
            [
                "--strategy",
                "ma_crossover",
                "--param",
                "fast_window=5",
                "--param",
                "slow_window=10",
                "--bars",
                "35",
                "--no-registry",
                "--max-runs",
                "1",
                "--diagnostics-dir",
                str(diag),
            ]
        )
        assert rc == 0
        p = diag / "combo_0001.json"
        assert p.is_file()
        payload = json.loads(p.read_text(encoding="utf-8"))
        assert payload["combo_index"] == 1
        assert payload["success"] is True
        assert payload["error"] is None
        assert payload["params"]["fast_window"] == 5
        assert payload["params"]["slow_window"] == 10
        assert isinstance(payload["stats"], dict)
        assert "total_trades" in payload["stats"] or "sharpe" in payload["stats"]
        bd = payload["backtest_diagnostics"]
        assert isinstance(bd, dict)
        assert "equity_curve" in bd or "trades" in bd

    def test_multiple_combos_deterministic_names(self, tmp_path: Path) -> None:
        diag = tmp_path / "diag2"
        from scripts.run_sweep_strategy import main

        rc = main(
            [
                "--strategy",
                "ma_crossover",
                "--param",
                "fast_window=5,6",
                "--param",
                "slow_window=10",
                "--bars",
                "30",
                "--no-registry",
                "--max-runs",
                "2",
                "--diagnostics-dir",
                str(diag),
            ]
        )
        assert rc == 0
        assert (diag / "combo_0001.json").is_file()
        assert (diag / "combo_0002.json").is_file()
