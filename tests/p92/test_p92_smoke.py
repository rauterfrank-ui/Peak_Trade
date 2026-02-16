from pathlib import Path
import os
import subprocess


def test_p92_retention_smoke(tmp_path: Path):
    ops = tmp_path / "ops"
    ops.mkdir()
    # create 5 fake snapshot dirs
    for ts in [
        "20260216T000000Z",
        "20260216T000500Z",
        "20260216T001000Z",
        "20260216T001500Z",
        "20260216T002000Z",
    ]:
        (ops / f"p91_shadow_soak_audit_snapshot_{ts}").mkdir()
    env = {
        **os.environ,
        "KEEP_N": "2",
        "OPS_DIR": str(ops),
    }
    root = Path(__file__).resolve().parents[2]
    subprocess.check_call(
        ["bash", "scripts/ops/p92_p91_audit_snapshot_retention_v1.sh"],
        cwd=root,
        env=env,
    )
    remain = sorted([p.name for p in ops.iterdir() if p.is_dir()])
    assert remain == [
        "p91_shadow_soak_audit_snapshot_20260216T001500Z",
        "p91_shadow_soak_audit_snapshot_20260216T002000Z",
    ]
