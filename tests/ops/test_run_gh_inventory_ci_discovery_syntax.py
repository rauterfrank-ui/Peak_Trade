import subprocess
from pathlib import Path


def test_bash_syntax():
    p = Path("scripts/ops/run_gh_inventory_ci_discovery.sh")
    assert p.exists()
    subprocess.run(["bash", "-n", str(p)], check=True)
