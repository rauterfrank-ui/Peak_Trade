from pathlib import Path
import subprocess

SCRIPT = Path("scripts/ops/build_pilot_ready_snapshot.sh")


def test_script_exists():
    assert SCRIPT.exists(), f"missing script: {SCRIPT}"


def test_bash_syntax_ok():
    result = subprocess.run(
        ["bash", "-n", str(SCRIPT)],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr
