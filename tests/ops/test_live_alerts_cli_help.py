import subprocess
import sys
from pathlib import Path


def test_live_alerts_cli_help_subprocess_smoke():
    root = Path(__file__).resolve().parents[2]
    script = root / "scripts" / "live_alerts_cli.py"

    result = subprocess.run(
        [sys.executable, str(script), "--help"],
        cwd=root,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    combined_output = result.stdout + result.stderr
    assert "usage:" in combined_output.lower()
    assert "live" in combined_output.lower()
    assert "alert" in combined_output.lower()
