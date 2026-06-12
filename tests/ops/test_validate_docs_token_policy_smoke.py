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


RUNBOOK_DOCS_TOKEN_POLICY = ROOT / "docs" / "ops" / "runbooks" / "RUNBOOK_DOCS_TOKEN_POLICY_GATE.md"
GATES_OVERVIEW = ROOT / "docs" / "ops" / "GATES_OVERVIEW.md"
CI_AUDIT = ROOT / "docs" / "ops" / "CI_AUDIT_KNOWN_ISSUES.md"


def test_docs_token_policy_runbook_documents_standard_check_for_docs_prs() -> None:
    doc = RUNBOOK_DOCS_TOKEN_POLICY.read_text(encoding="utf-8")
    assert "Standard local checks for docs / docs+tests PRs" in doc
    assert "preflight_docs_token_policy_changed.sh" in doc
    assert "docs-token-policy-gate" in doc
    assert "required standard check" in doc.lower()


def test_gates_overview_documents_mandatory_docs_token_preflight() -> None:
    doc = GATES_OVERVIEW.read_text(encoding="utf-8")
    assert "Docs / docs+tests PR — mandatory local preflight" in doc
    assert "preflight_docs_token_policy_changed.sh" in doc
    assert "docs-token-policy-gate" in doc


def test_ci_audit_documents_docs_token_policy_standard_check_integration() -> None:
    doc = CI_AUDIT.read_text(encoding="utf-8")
    assert "Docs Token Policy Guard standard check integration" in doc
    assert "DOCS_TOKEN_POLICY_GUARD_STANDARD_CHECK_INTEGRATION_V1=true" in doc
    assert "GO_DOCS_TOKEN_POLICY_GUARD_STANDARD_CHECK_INTEGRATION_NARROW_FIX_NO_RUN_V1" in doc


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
