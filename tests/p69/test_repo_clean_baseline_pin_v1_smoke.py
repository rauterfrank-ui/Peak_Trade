import subprocess
from pathlib import Path


def test_repo_clean_baseline_pin_script_exists_and_parses() -> None:
    p = Path("scripts/ops/repo_clean_baseline_pin_v1.sh")
    assert p.exists()
    assert p.stat().st_mode & 0o111
    subprocess.check_call(["bash", "-n", str(p)])
