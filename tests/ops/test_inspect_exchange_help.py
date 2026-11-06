import subprocess
import sys
from pathlib import Path


def test_inspect_exchange_help_subprocess_smoke():
    root = Path(__file__).resolve().parents[2]
    script = root / "scripts" / "inspect_exchange.py"

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
    assert "exchange" in combined_output.lower()
    assert "inspect" in combined_output.lower()
