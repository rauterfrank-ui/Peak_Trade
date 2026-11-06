import subprocess
from pathlib import Path


def test_pull_latest_prbg_syntax():
    p = Path("scripts/ops/pull_latest_prbg_execution_evidence.sh")
    assert p.exists()
    subprocess.run(["bash", "-n", str(p)], check=True)
