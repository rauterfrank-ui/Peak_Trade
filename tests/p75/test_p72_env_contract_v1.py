from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path


def _run(cmd: list[str], env: dict[str, str], cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        cmd,
        cwd=str(cwd),
        env={**os.environ, **env},
        text=True,
        capture_output=True,
        check=False,
    )


def _assert_pack_ok(proc: subprocess.CompletedProcess[str]) -> None:
    assert proc.returncode == 0, (
        f"rc={proc.returncode}\nSTDOUT:\n{proc.stdout}\nSTDERR:\n{proc.stderr}"
    )
    assert "P72_SHADOWLOOP_PACK_OK" in proc.stdout, (
        f"missing OK marker\nSTDOUT:\n{proc.stdout}\nSTDERR:\n{proc.stderr}"
    )


def _assert_expected_files(out_dir: Path) -> None:
    # P72 pack should write these (from P71 + P62/P63 chain)
    for name in ("manifest.json", "readiness_report.json", "shadow_plan.json"):
        p = out_dir / name
        assert p.exists(), f"missing {p}"
    # manifest should at least be valid JSON
    json.loads((out_dir / "manifest.json").read_text(encoding="utf-8"))


def test_p72_legacy_env_vars_only(tmp_path: Path) -> None:
    root = Path(__file__).resolve().parents[2]
    out_dir = tmp_path / "p72_legacy_only"
    env = {
        "OUT_DIR": str(out_dir),
        "RUN_ID": "p75_legacy_only",
        "MODE": "shadow",
        "ITERATIONS": "1",
        "INTERVAL": "0",
        "PYTHONPATH": str(root),
    }
    proc = _run(["bash", "scripts/ops/p72_shadowloop_pack_v1.sh"], env=env, cwd=root)
    _assert_pack_ok(proc)
    _assert_expected_files(out_dir)


def test_p72_override_env_vars_only(tmp_path: Path) -> None:
    root = Path(__file__).resolve().parents[2]
    out_dir = tmp_path / "p72_override_only"
    env = {
        "OUT_DIR_OVERRIDE": str(out_dir),
        "RUN_ID_OVERRIDE": "p75_override_only",
        "MODE_OVERRIDE": "shadow",
        "ITERATIONS_OVERRIDE": "1",
        "INTERVAL_OVERRIDE": "0",
        "PYTHONPATH": str(root),
    }
    proc = _run(["bash", "scripts/ops/p72_shadowloop_pack_v1.sh"], env=env, cwd=root)
    _assert_pack_ok(proc)
    _assert_expected_files(out_dir)


def test_p72_override_wins_over_legacy(tmp_path: Path) -> None:
    root = Path(__file__).resolve().parents[2]
    legacy_dir = tmp_path / "p72_legacy_should_not_win"
    override_dir = tmp_path / "p72_override_should_win"
    env = {
        # legacy
        "OUT_DIR": str(legacy_dir),
        "RUN_ID": "p75_legacy",
        "MODE": "shadow",
        "ITERATIONS": "1",
        "INTERVAL": "0",
        # override (should win)
        "OUT_DIR_OVERRIDE": str(override_dir),
        "RUN_ID_OVERRIDE": "p75_override",
        "MODE_OVERRIDE": "shadow",
        "ITERATIONS_OVERRIDE": "1",
        "INTERVAL_OVERRIDE": "0",
        "PYTHONPATH": str(root),
    }
    proc = _run(["bash", "scripts/ops/p72_shadowloop_pack_v1.sh"], env=env, cwd=root)
    _assert_pack_ok(proc)

    # must write to override dir
    _assert_expected_files(override_dir)
    assert not (legacy_dir / "manifest.json").exists(), "legacy OUT_DIR unexpectedly used"
