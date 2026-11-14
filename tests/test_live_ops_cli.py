"""The retired CSV operator routes refuse work before opening input or output."""

from pathlib import Path
import subprocess

import pytest

ROOT = Path(__file__).resolve().parents[1]
PT = ROOT / "scripts/pt"

RETIRED = (
    ("generate_forward_signals", "--strategy", "ma_crossover"),
    ("run_forward_signals", "--strategy", "ma_crossover"),
    ("live_ops", "portfolio", "--json"),
    ("run_autonomous_workflow", "--once", "--dry-run"),
    ("generate_operator_meta_report", "--output", "would-write.html"),
    ("preview_live_orders", "--signals", "missing.csv"),
    ("check_live_risk_limits", "--orders", "missing.csv"),
    ("paper_trade_from_orders", "--orders", "missing.csv"),
)


@pytest.mark.parametrize(("entrypoint", "arg", "value"), RETIRED)
def test_retired_operator_help_and_invocation(tmp_path, entrypoint, arg, value):
    script = ROOT / f"scripts/{entrypoint}.py"
    help_result = subprocess.run(
        [PT, script, "--help"], cwd=tmp_path, capture_output=True, text=True
    )
    assert help_result.returncode == 0, help_result.stderr
    assert "Retired entrypoint" in help_result.stdout
    result = subprocess.run([PT, script, arg, value], cwd=tmp_path, capture_output=True, text=True)
    assert result.returncode == 2
    assert f"{entrypoint.upper()}_RETIRED" in result.stderr
    assert not list(tmp_path.iterdir())


@pytest.mark.parametrize("command", ("pipeline", "report"))
def test_retired_live_ops_wrappers_write_no_report(tmp_path, command):
    cfg = tmp_path / "config.toml"
    cfg.write_text("")
    output = tmp_path / "reports"
    args = (
        [ROOT / "scripts/pipeline_cli.py", "live_ops", "--", "health", "--json"]
        if command == "pipeline"
        else [
            ROOT / "scripts/generate_live_status_report.py",
            "--config",
            cfg,
            "--output-dir",
            output,
        ]
    )
    result = subprocess.run([PT, *args], cwd=tmp_path, capture_output=True, text=True)
    assert result.returncode != 0
    assert "LIVE_OPS_RETIRED" in result.stderr
    assert not output.exists()
