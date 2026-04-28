"""
CLI: --experiments-dir / --sweeps-output-dir für MC- und Stress-Runner.

Read-only Bezugspfad-Anpassung; keine Produktions-Evidence durch diese Tests allein.
"""

from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import scripts.run_monte_carlo_robustness as mc_script
import scripts.run_stress_tests as stress_script


def test_monte_carlo_passes_custom_experiments_and_sweeps_dirs(monkeypatch, tmp_path) -> None:
    monkeypatch.chdir(tmp_path)

    captured = {}

    def _fake_loader(*args, **kwargs):  # type: ignore[no-untyped-def]
        captured["kwargs"] = kwargs
        return [{"config_id": "only", "rank": 1}]

    with patch.object(mc_script, "load_top_n_configs_for_sweep", side_effect=_fake_loader):
        with patch.object(mc_script, "load_returns_for_config", return_value=_series()):
            with patch.object(mc_script, "run_monte_carlo_from_returns") as mc_run:
                with patch.object(mc_script, "build_monte_carlo_report"):
                    mc_run.return_value = MagicMock()
                    parser = mc_script.build_parser()
                    args = parser.parse_args(
                        [
                            "--sweep-name",
                            "smoke_sweep",
                            "--top-n",
                            "1",
                            "--num-runs",
                            "5",
                            "--format",
                            "md",
                            "--experiments-dir",
                            str(tmp_path / "exp"),
                            "--sweeps-output-dir",
                            str(tmp_path / "swp"),
                            "--use-dummy-data",
                            "--output-dir",
                            str(tmp_path / "out"),
                        ]
                    )
                    rc = mc_script.run_from_args(args)

    assert rc == 0
    assert captured["kwargs"]["experiments_dir"] == tmp_path / "exp"
    assert captured["kwargs"]["output_path"] == tmp_path / "swp"


def test_stress_passes_custom_experiments_and_sweeps_dirs(monkeypatch, tmp_path) -> None:
    monkeypatch.chdir(tmp_path)

    captured = {}

    def _fake_loader(*args, **kwargs):  # type: ignore[no-untyped-def]
        captured["kwargs"] = kwargs
        return [{"config_id": "only", "rank": 1}]

    with patch.object(stress_script, "load_top_n_configs_for_sweep", side_effect=_fake_loader):
        with patch.object(stress_script, "load_returns_for_top_config") as lr:
            lr.return_value = _series()
            with patch.object(stress_script, "run_stress_test_suite") as suite_run:
                with patch.object(stress_script, "build_stress_test_report") as brep:
                    suite_run.return_value = MagicMock()
                    brep.return_value = {}
                    parser = stress_script.build_parser()
                    args = parser.parse_args(
                        [
                            "--sweep-name",
                            "smoke_sweep",
                            "--config",
                            "config/config.toml",
                            "--top-n",
                            "1",
                            "--scenarios",
                            "single_crash_bar",
                            "--format",
                            "md",
                            "--experiments-dir",
                            str(tmp_path / "exp2"),
                            "--sweeps-output-dir",
                            str(tmp_path / "swp2"),
                            "--output-dir",
                            str(tmp_path / "stre"),
                            "--use-dummy-data",
                        ]
                    )
                    rc = stress_script.run_from_args(args)

    assert rc == 0
    assert captured["kwargs"]["experiments_dir"] == tmp_path / "exp2"
    assert captured["kwargs"]["output_path"] == tmp_path / "swp2"
    lr_kwargs = lr.call_args[1]
    assert lr_kwargs["experiments_dir"] == tmp_path / "exp2"


def _series():  # type: ignore[no-untyped-def]
    import pandas as pd

    return pd.Series([0.01, -0.005, 0.002])
