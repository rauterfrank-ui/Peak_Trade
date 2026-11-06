import subprocess
from pathlib import Path


def test_operator_all_syntax():
    p = Path("scripts/ops/operator_all.sh")
    assert p.exists()
    subprocess.run(["bash", "-n", str(p)], check=True)
