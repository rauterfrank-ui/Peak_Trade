import subprocess
from pathlib import Path


def test_bash_syntax():
    p = Path("scripts/ops/run_live_pilot_session.sh")
    assert p.exists()
    subprocess.run(["bash", "-n", str(p)], check=True)
