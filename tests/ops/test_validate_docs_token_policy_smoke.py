"""Smoke tests for scripts/ops/validate_docs_token_policy.py (NO-LIVE)."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
_SCRIPT = ROOT / "scripts" / "ops" / "validate_docs_token_policy.py"


def test_validate_docs_token_policy_help_contains_no_live() -> None:
    p = subprocess.run(
        [sys.executable, str(_SCRIPT), "--help"],
        cwd=str(ROOT),
        capture_output=True,
        text=True,
    )
    assert p.returncode == 0, p.stderr
    out = p.stdout.replace("\n", "")
    assert "NO-LIVE" in out
    assert "&#47;" in p.stdout


def test_validate_docs_token_policy_main_returns_2_outside_git_repo(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    sys.path.insert(0, str(ROOT / "scripts" / "ops"))
    import validate_docs_token_policy as m  # noqa: E402

    def fake_check_output(cmd: list[str], **kwargs: object) -> str:
        if cmd[:3] == ["git", "rev-parse", "--show-toplevel"]:
            raise subprocess.CalledProcessError(1, cmd)
        raise AssertionError(f"unexpected subprocess call: {cmd!r}")

    monkeypatch.setattr(m.subprocess, "check_output", fake_check_output)
    assert m.main(["--all"]) == 2
