import subprocess
from pathlib import Path

def test_rotate_launchd_logs_syntax():
    p = Path("scripts/ops/rotate_launchd_logs.sh")
    assert p.exists()
    subprocess.run(["bash", "-n", str(p)], check=True)
