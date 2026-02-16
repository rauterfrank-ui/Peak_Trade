import subprocess
from pathlib import Path


def test_launchd_script_syntax_ok() -> None:
    p = Path("scripts/ops/launchd_online_readiness_supervisor_smoke_v1.sh")
    assert p.exists()
    r = subprocess.run(["bash", "-n", str(p)], check=False, capture_output=True, text=True)
    assert r.returncode == 0, r.stderr


def test_launchd_script_usage_exit_2() -> None:
    p = Path("scripts/ops/launchd_online_readiness_supervisor_smoke_v1.sh")
    r = subprocess.run(["bash", str(p), "nope"], check=False, capture_output=True, text=True)
    assert r.returncode == 2
