"""Contract tests for scripts/ci/check_docs_diff_guard_section.py (git output mocked)."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

_REPO_ROOT = Path(__file__).resolve().parent.parent.parent
_CI_SCRIPTS = _REPO_ROOT / "scripts" / "ci"
if str(_CI_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_CI_SCRIPTS))

import check_docs_diff_guard_section as guard  # noqa: E402


def _fake_sh_factory(merge_base: str, diff_names: list[str]):
    def fake_sh(*args: str) -> str:
        if args == ("git", "merge-base", "HEAD", "origin/main"):
            return merge_base
        if (
            args[:3] == ("git", "diff", "--name-only")
            and len(args) == 4
            and args[3].endswith("..HEAD")
        ):
            return "\n".join(diff_names) + ("\n" if diff_names else "")
        raise AssertionError(f"unexpected sh call: {args!r}")

    return fake_sh


def test_workflow_invokes_policy_script() -> None:
    text = (_REPO_ROOT / ".github/workflows/docs_diff_guard_policy_gate.yml").read_text(
        encoding="utf-8"
    )
    assert "Docs Diff Guard Policy Gate" in text
    assert "python3 scripts/ci/check_docs_diff_guard_section.py" in text


def test_merge_base_failure_skips_with_zero(capsys: pytest.CaptureFixture[str]) -> None:
    def boom(*_args: str) -> str:
        raise subprocess.CalledProcessError(1, "git")

    with patch.object(guard, "sh", side_effect=boom):
        assert guard.main() == 0
    err = capsys.readouterr().out
    assert "merge-base" in err.lower() or "Skipping" in err


def test_not_triggered_no_relevant_changes_zero(capsys: pytest.CaptureFixture[str]) -> None:
    fake = _fake_sh_factory("abc123", ["README.md", "src/foo.py"])
    with patch.object(guard, "sh", fake):
        assert guard.main() == 0
    assert "not applicable" in capsys.readouterr().out.lower()


def test_triggered_happy_path_marker_present(tmp_path: Path) -> None:
    doc = tmp_path / "doc.md"
    doc.write_text(f"# Title\n\nSome text.\n\n{guard.MARKER}\n", encoding="utf-8")
    fake = _fake_sh_factory("abc123", ["docs/ops/README.md"])
    with patch.object(guard, "sh", fake):
        with patch.object(guard, "REQUIRED_DOCS", [doc]):
            assert guard.main() == 0


def test_triggered_missing_marker_fails_with_context(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    doc = tmp_path / "bad.md"
    doc.write_text("# No marker here\n", encoding="utf-8")
    fake = _fake_sh_factory("abc123", ["docs/ops/touched.md"])
    with patch.object(guard, "sh", fake):
        with patch.object(guard, "REQUIRED_DOCS", [doc]):
            assert guard.main() == 1
    out = capsys.readouterr().out
    assert guard.MARKER in out
    assert str(doc) in out or "bad.md" in out
    assert "insert_docs_diff_guard_section.py" in out


def test_triggered_required_doc_path_missing_skipped_not_failed(tmp_path: Path) -> None:
    """If a listed path does not exist, script skips it; none checked => OK."""
    missing = tmp_path / "does_not_exist.md"
    fake = _fake_sh_factory("abc123", ["docs/ops/x.md"])
    with patch.object(guard, "sh", fake):
        with patch.object(guard, "REQUIRED_DOCS", [missing]):
            assert guard.main() == 0
