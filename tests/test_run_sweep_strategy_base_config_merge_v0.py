# -*- coding: utf-8 -*-
"""Tests for run_sweep_strategy.py [base_config] + [grid] TOML merge (v0)."""

from __future__ import annotations

from pathlib import Path

import pytest


class TestLoadParameterGridBaseConfigMerge:
    """load_parameter_grid merges [base_config] into sweep dimensions."""

    def test_base_config_and_grid_merged(self, tmp_path: Path) -> None:
        path = tmp_path / "merge.toml"
        path.write_text(
            """
[base_config]
components = ["breakout", "rsi_reversion"]
base_weights = { breakout = 0.6, rsi_reversion = 0.4 }
regime_strategy = "vol_regime_filter"

[grid]
neutral_scale = [0.4, 0.5]
risk_on_scale = [1.0]
""",
            encoding="utf-8",
        )
        from scripts.run_sweep_strategy import expand_parameter_grid, load_parameter_grid

        grid = load_parameter_grid(str(path))
        assert grid["components"] == [["breakout", "rsi_reversion"]]
        assert grid["regime_strategy"] == ["vol_regime_filter"]
        assert grid["neutral_scale"] == [0.4, 0.5]
        combos = expand_parameter_grid(grid)
        assert len(combos) == 2
        for c in combos:
            assert c["components"] == ["breakout", "rsi_reversion"]
            assert c["regime_strategy"] == "vol_regime_filter"

    def test_grid_overrides_base_config_on_collision(self, tmp_path: Path) -> None:
        path = tmp_path / "override.toml"
        path.write_text(
            """
[base_config]
overlap = 1
only_base = true

[grid]
overlap = [2, 3]
""",
            encoding="utf-8",
        )
        from scripts.run_sweep_strategy import expand_parameter_grid, load_parameter_grid

        grid = load_parameter_grid(str(path))
        assert grid["overlap"] == [2, 3]
        assert grid["only_base"] == [True]
        combos = expand_parameter_grid(grid)
        assert len(combos) == 2
        assert combos[0]["overlap"] == 2
        assert combos[1]["overlap"] == 3

    def test_grid_only_toml_unchanged_semantics(self, tmp_path: Path) -> None:
        path = tmp_path / "grid_only.toml"
        path.write_text(
            """
[grid]
a = [1, 2]
b = [10]
""",
            encoding="utf-8",
        )
        from scripts.run_sweep_strategy import expand_parameter_grid, load_parameter_grid

        grid = load_parameter_grid(str(path))
        assert sorted(grid.keys()) == ["a", "b"]
        assert expand_parameter_grid(grid) == [
            {"a": 1, "b": 10},
            {"a": 2, "b": 10},
        ]

    def test_top_level_toml_keys_without_grid_section(self, tmp_path: Path) -> None:
        path = tmp_path / "top_level.toml"
        path.write_text(
            """
x = [1, 2]
y = [3]
""",
            encoding="utf-8",
        )
        from scripts.run_sweep_strategy import expand_parameter_grid, load_parameter_grid

        grid = load_parameter_grid(str(path))
        assert expand_parameter_grid(grid) == [{"x": 1, "y": 3}, {"x": 2, "y": 3}]

    def test_regime_aware_portfolio_dry_run_lists_components(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        path = tmp_path / "regime_smoke.toml"
        path.write_text(
            """
[base_config]
components = ["breakout", "rsi_reversion"]
base_weights = { breakout = 0.6, rsi_reversion = 0.4 }
regime_strategy = "vol_regime_filter"

[grid]
neutral_scale = [0.4, 0.5]
risk_on_scale = [1.0]
risk_off_scale = [0.0]
mode = ["scale"]
signal_threshold = [0.25]
vol_metric = ["atr"]
low_vol_threshold = [0.5]
high_vol_threshold = [1.5]
""",
            encoding="utf-8",
        )
        from scripts.run_sweep_strategy import main

        rc = main(
            [
                "--strategy",
                "regime_aware_portfolio",
                "--grid",
                str(path),
                "--dry-run",
            ]
        )
        assert rc == 0
        out = capsys.readouterr().out
        assert "'components'" in out or "components" in out
