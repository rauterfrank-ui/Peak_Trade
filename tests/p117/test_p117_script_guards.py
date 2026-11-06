"""P117 script guards — run without supervisor."""

import subprocess
from pathlib import Path


def test_p117_script_exists_and_executable():
    p = Path("scripts/ops/p117_run_p116_exec_evidence_guarded_v1.sh")
    assert p.exists()
    assert p.stat().st_mode & 0o111


def test_p117_script_skips_when_disabled():
    root = Path(__file__).resolve().parents[2]
    rc = subprocess.run(
        ["bash", str(root / "scripts/ops/p117_run_p116_exec_evidence_guarded_v1.sh")],
        env={"MODE": "shadow", "DRY_RUN": "YES", "P117_ENABLE_EXEC_EVI": "NO"},
        cwd=str(root),
        capture_output=True,
        text=True,
    )
    assert rc.returncode == 0
    assert "P117_SKIP" in (rc.stdout + rc.stderr)


def test_p117_script_guard_rejects_dry_run_no():
    root = Path(__file__).resolve().parents[2]
    rc = subprocess.run(
        ["bash", str(root / "scripts/ops/p117_run_p116_exec_evidence_guarded_v1.sh")],
        env={"MODE": "shadow", "DRY_RUN": "NO", "P117_ENABLE_EXEC_EVI": "YES"},
        cwd=str(root),
        capture_output=True,
        text=True,
    )
    assert rc.returncode == 3
    assert "dry_run_must_be_yes" in (rc.stdout + rc.stderr)
