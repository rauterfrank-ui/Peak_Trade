"""Smoke tests for scripts/ops/autofix_docs_token_policy_inline_code.py (NO-LIVE)."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
_SCRIPT = ROOT / "scripts" / "ops" / "autofix_docs_token_policy_inline_code.py"


def test_autofix_docs_token_policy_help_docstring_mentions_no_live() -> None:
    """Module docstring is printed on empty invocation; must mention NO-LIVE."""
    sys.path.insert(0, str(ROOT / "scripts" / "ops"))
    import autofix_docs_token_policy_inline_code as m  # noqa: E402

    code = m.main([])
    assert code == 1
    # docstring is printed to stdout by main([]); re-import fresh would not capture.
    # Assert NO-LIVE is in module doc:
    assert "NO-LIVE" in m.__doc__


def test_autofix_docs_token_policy_main_returns_1_missing_file(tmp_path: Path) -> None:
    sys.path.insert(0, str(ROOT / "scripts" / "ops"))
    import autofix_docs_token_policy_inline_code as m  # noqa: E402

    code = m.main([str(tmp_path / "nope.md")])
    assert code == 1


def test_autofix_docs_token_policy_main_returns_0_clean_md(tmp_path: Path) -> None:
    f = tmp_path / "clean.md"
    f.write_text("# Title\n\nNo inline slashes here.\n", encoding="utf-8")
    sys.path.insert(0, str(ROOT / "scripts" / "ops"))
    import autofix_docs_token_policy_inline_code as m  # noqa: E402

    code = m.main([str(f)])
    assert code == 0


def test_autofix_docs_token_policy_subprocess_help_via_doc() -> None:
    """Running with no args exits 1; stderr empty; doc printed to stdout."""
    p = subprocess.run(
        [sys.executable, str(_SCRIPT)],
        cwd=str(ROOT),
        capture_output=True,
        text=True,
    )
    assert p.returncode == 1
    assert "NO-LIVE" in p.stdout
