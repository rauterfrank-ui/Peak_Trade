import subprocess
from pathlib import Path


def test_run_end_to_end_verification_syntax():
    p = Path("scripts/ops/run_end_to_end_verification.sh")
    assert p.exists()
    subprocess.run(["bash", "-n", str(p)], check=True)
