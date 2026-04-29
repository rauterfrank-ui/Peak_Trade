"""CLI contract tests for scripts/ops/check_repo_truth_claims.py (subprocess, isolated fixtures)."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
_SCRIPT = ROOT / "scripts" / "ops" / "check_repo_truth_claims.py"


def _run(
    tmp_path: Path,
    *,
    cfg: Path | None,
    extra_args: list[str] | None = None,
) -> subprocess.CompletedProcess[str]:
    cmd = [
        sys.executable,
        str(_SCRIPT),
        "--repo-root",
        str(tmp_path),
    ]
    if cfg is not None:
        cmd.extend(["--config", str(cfg)])
    if extra_args:
        cmd.extend(extra_args)
    return subprocess.run(
        cmd,
        cwd=str(ROOT),
        capture_output=True,
        text=True,
        check=False,
    )


def test_cli_missing_config_returns_2(tmp_path: Path) -> None:
    missing = tmp_path / "nope.yaml"
    p = _run(tmp_path, cfg=missing)
    assert p.returncode == 2
    assert "ERR: config not found" in p.stderr
    assert missing.as_posix() in p.stderr or str(missing.resolve()) in p.stderr


def test_cli_invalid_yaml_root_returns_2(tmp_path: Path) -> None:
    cfg = tmp_path / "bad.yaml"
    cfg.write_text("not a mapping", encoding="utf-8")
    p = _run(tmp_path, cfg=cfg)
    assert p.returncode == 2
    assert "ERR: failed to load claims:" in p.stderr


def test_cli_no_claims_key_passes_zero_checks(tmp_path: Path) -> None:
    cfg = tmp_path / "empty.yaml"
    cfg.write_text("version: 1\n", encoding="utf-8")
    p = _run(tmp_path, cfg=cfg)
    assert p.returncode == 0
    assert "repo_truth_claims: OK (0 check(s))." in p.stdout


def test_cli_path_exists_pass_routes_pass_to_stdout(tmp_path: Path) -> None:
    (tmp_path / "marker.txt").write_text("x", encoding="utf-8")
    cfg = tmp_path / "c.yaml"
    cfg.write_text(
        "version: 1\nclaims:\n  - id: m1\n    check: path_exists\n    path: marker.txt\n",
        encoding="utf-8",
    )
    p = _run(tmp_path, cfg=cfg)
    assert p.returncode == 0
    assert "[PASS] m1:" in p.stdout
    assert "repo_truth_claims: OK (1 check(s))." in p.stdout


def test_cli_missing_path_returns_1_and_stderr(tmp_path: Path) -> None:
    cfg = tmp_path / "c.yaml"
    cfg.write_text(
        "version: 1\nclaims:\n  - id: miss\n    check: path_exists\n    path: nope.txt\n",
        encoding="utf-8",
    )
    p = _run(tmp_path, cfg=cfg)
    assert p.returncode == 1
    assert "[FAIL] miss:" in p.stderr
    assert "repo_truth_claims: FAIL" in p.stderr


def test_cli_unknown_check_kind_returns_2(tmp_path: Path) -> None:
    cfg = tmp_path / "c.yaml"
    cfg.write_text(
        "version: 1\nclaims:\n  - id: u1\n    check: future_magic\n    path: x\n",
        encoding="utf-8",
    )
    p = _run(tmp_path, cfg=cfg)
    assert p.returncode == 2
    assert "[UNKNOWN] u1:" in p.stderr
    assert "repo_truth_claims: UNKNOWN" in p.stderr
