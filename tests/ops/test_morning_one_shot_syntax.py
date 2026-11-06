import subprocess
from pathlib import Path


def test_morning_one_shot_syntax():
    p = Path("scripts/ops/run_morning_one_shot.sh")
    assert p.exists()
    subprocess.run(["bash", "-n", str(p)], check=True)
