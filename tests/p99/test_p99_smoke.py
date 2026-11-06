import os
import subprocess
from pathlib import Path

import pytest

SUP_BASE = Path("out/ops/online_readiness_supervisor")
HAS_SUPERVISOR = SUP_BASE.exists() and bool(list(SUP_BASE.glob("run_*")))


def _p95_launchd_ready() -> bool:
    """True if p95 meta gate would pass (launchd jobs present)."""
    try:
        uid = subprocess.run(
            ["id", "-u"], capture_output=True, text=True, check=True
        ).stdout.strip()
        r = subprocess.run(
            ["launchctl", "print", f"gui/{uid}/com.peaktrade.p93-status-dashboard"],
            capture_output=True,
            timeout=2,
        )
        return r.returncode == 0
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False


HAS_P95_READY = _p95_launchd_ready()


@pytest.mark.skipif(
    not HAS_SUPERVISOR or not HAS_P95_READY,
    reason="supervisor run_* not present or p95 launchd jobs missing",
)
def test_p99_cli_creates_evidence(tmp_path: Path) -> None:
    root = subprocess.check_output(["git", "rev-parse", "--show-toplevel"], text=True).strip()
    evi = tmp_path / "evi"
    out_ops = tmp_path / "out_ops"
    out_ops.mkdir()
    env = os.environ.copy()
    env["EVI_OVERRIDE"] = str(evi)
    env["OUT_OPS_OVERRIDE"] = str(out_ops)
    env["TS_OVERRIDE"] = "20990101T000000Z"
    env["DRY_RUN"] = "YES"
    p = subprocess.run(
        ["python3", "-m", "src.ops.p99.ops_loop_cli_v1", "--mode", "shadow"],
        cwd=root,
        env=env,
        text=True,
        capture_output=True,
    )
    assert p.returncode == 0, (p.stdout, p.stderr)
    assert "P99_OK" in p.stdout
    assert (evi / "report.json").exists()
    assert (evi / "SHA256SUMS.txt").exists()
    pin = out_ops / "P99_OPS_LOOP_DONE_20990101T000000Z.txt"
    assert pin.exists()
    assert Path(str(pin) + ".sha256").exists()


def test_p99_cli_help() -> None:
    root = subprocess.check_output(["git", "rev-parse", "--show-toplevel"], text=True).strip()
    p = subprocess.run(
        ["python3", "-m", "src.ops.p99.ops_loop_cli_v1", "--help"],
        cwd=root,
        text=True,
        capture_output=True,
    )
    assert p.returncode == 0
    assert "p99_ops_loop_cli_v1" in p.stdout
