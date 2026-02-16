import os
from pathlib import Path

import pytest
import subprocess

SUP_BASE = Path("out/ops/online_readiness_supervisor")
HAS_SUPERVISOR = SUP_BASE.exists() and bool(list(SUP_BASE.glob("run_*")))


@pytest.mark.skipif(not HAS_SUPERVISOR, reason="supervisor run_* not present")
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
