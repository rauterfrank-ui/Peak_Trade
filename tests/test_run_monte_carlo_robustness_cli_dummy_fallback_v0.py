"""
CLI: Dummy-Top-N-Fallback für offline Smoke (parity mit run_stress_tests.py).
"""

from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import patch

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import scripts.run_monte_carlo_robustness as mc_script


@patch("scripts.run_monte_carlo_robustness.load_top_n_configs_for_sweep")
def test_mc_dummy_fallback_loader_raises_writes_md(mock_load, tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    mock_load.side_effect = RuntimeError("no sweep results")

    out = tmp_path / "mc_out"
    args = mc_script.build_parser().parse_args(
        [
            "--sweep-name",
            "smoke",
            "--top-n",
            "1",
            "--num-runs",
            "20",
            "--format",
            "md",
            "--output-dir",
            str(out),
            "--use-dummy-data",
            "--dummy-bars",
            "80",
        ]
    )

    rc = mc_script.run_from_args(args)
    assert rc == 0
    md_files = list(out.rglob("*.md"))
    assert md_files, "expected at least one markdown report under output-dir"


@patch("scripts.run_monte_carlo_robustness.load_top_n_configs_for_sweep")
def test_mc_no_dummy_loader_raises_exits_nonzero(mock_load, tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    mock_load.side_effect = RuntimeError("no sweep results")

    args = mc_script.build_parser().parse_args(
        [
            "--sweep-name",
            "smoke",
            "--top-n",
            "1",
            "--num-runs",
            "20",
            "--format",
            "md",
            "--output-dir",
            str(tmp_path / "mc_out"),
            "--dummy-bars",
            "80",
        ]
    )

    rc = mc_script.run_from_args(args)
    assert rc == 1


@patch("scripts.run_monte_carlo_robustness.load_top_n_configs_for_sweep")
def test_mc_dummy_fallback_empty_configs(mock_load, tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    mock_load.return_value = []

    out = tmp_path / "mc_empty"
    args = mc_script.build_parser().parse_args(
        [
            "--sweep-name",
            "smoke",
            "--top-n",
            "2",
            "--num-runs",
            "15",
            "--format",
            "md",
            "--output-dir",
            str(out),
            "--use-dummy-data",
            "--dummy-bars",
            "60",
        ]
    )

    rc = mc_script.run_from_args(args)
    assert rc == 0
    dirs = [p for p in out.iterdir() if p.is_dir()]
    assert {d.name for d in dirs} >= {"dummy_config_1", "dummy_config_2"}


def test_mc_dummy_fallback_no_writes_under_repo_reports(tmp_path, monkeypatch):
    """Outputs only under tmp_path (caller-provided output-dir); repo reports/ untouched."""
    marker = project_root / "reports" / "monte_carlo"
    before = set(marker.rglob("*")) if marker.exists() else set()

    monkeypatch.chdir(tmp_path)
    out = tmp_path / "only_here"

    def _boom(*_a, **_kw):
        raise RuntimeError("no experiments")

    with patch.object(mc_script, "load_top_n_configs_for_sweep", side_effect=_boom):
        args = mc_script.build_parser().parse_args(
            [
                "--sweep-name",
                "smoke",
                "--top-n",
                "1",
                "--num-runs",
                "10",
                "--format",
                "md",
                "--output-dir",
                str(out),
                "--use-dummy-data",
                "--dummy-bars",
                "40",
            ]
        )
        rc = mc_script.run_from_args(args)
    assert rc == 0
    assert out.exists()
    assert list(out.rglob("*.md"))

    after = set(marker.rglob("*")) if marker.exists() else set()
    assert before == after
