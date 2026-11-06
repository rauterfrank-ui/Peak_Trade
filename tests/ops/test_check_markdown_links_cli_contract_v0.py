"""CLI contract tests for scripts/ops/check_markdown_links.py (v0)."""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts" / "ops" / "check_markdown_links.py"


def _run_cli(root: Path, *paths: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [
            sys.executable,
            str(SCRIPT),
            "--root",
            str(root),
            "--paths",
            *paths,
        ],
        capture_output=True,
        text=True,
        check=False,
    )


def test_cli_exit_0_when_no_broken_internal_links(tmp_path: Path) -> None:
    docs = tmp_path / "docs"
    docs.mkdir(parents=True, exist_ok=True)
    (docs / "guide.md").write_text(
        "# Guide\n\nSee [section](#details).\n\n## Details\n\nBody.\n",
        encoding="utf-8",
    )

    p = _run_cli(tmp_path, "docs/guide.md")

    assert p.returncode == 0
    assert "✅ Markdown link check: OK (no broken internal links found)" in p.stdout
    assert p.stderr == ""


def test_cli_exit_1_when_target_escapes_repository_root(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    docs = repo / "docs"
    docs.mkdir(parents=True, exist_ok=True)
    outside = tmp_path / "outside"
    outside.mkdir(parents=True, exist_ok=True)
    target = outside / "target.md"
    target.write_text("# Outside\n\n", encoding="utf-8")
    (docs / "index.md").write_text(
        "# Index\n\n[escape](../../outside/target.md)\n",
        encoding="utf-8",
    )

    p = _run_cli(repo, "docs/index.md")

    assert p.returncode == 1
    assert "❌ Markdown link check: BROKEN LINKS FOUND" in p.stdout
    assert "target escapes repository root" in p.stdout
    assert re.search(
        r"^- docs/index\.md: \(\.\./\.\./outside/target\.md\) -> target escapes repository root$",
        p.stdout,
        flags=re.MULTILINE,
    )
    assert "Total broken links: 1" in p.stdout
    assert p.stderr == ""

    target.unlink()
    p2 = _run_cli(repo, "docs/index.md")
    assert p2.returncode == 1
    assert "target escapes repository root" in p2.stdout
    assert p2.stderr == ""


def test_cli_exit_1_when_target_file_missing(tmp_path: Path) -> None:
    docs = tmp_path / "docs"
    docs.mkdir(parents=True, exist_ok=True)
    (docs / "broken_file.md").write_text(
        "# Broken\n\nMissing [target](./does-not-exist.md).\n",
        encoding="utf-8",
    )

    p = _run_cli(tmp_path, "docs/broken_file.md")

    assert p.returncode == 1
    assert "❌ Markdown link check: BROKEN LINKS FOUND" in p.stdout
    assert re.search(
        r"^- docs/broken_file\.md: \(\./does-not-exist\.md\) -> target file does not exist: \./does-not-exist\.md$",
        p.stdout,
        flags=re.MULTILINE,
    )
    assert "Total broken links: 1" in p.stdout
    assert p.stderr == ""


def test_cli_exit_1_when_cross_file_anchor_missing(tmp_path: Path) -> None:
    docs = tmp_path / "docs"
    docs.mkdir(parents=True, exist_ok=True)
    (docs / "source.md").write_text(
        "# Source\n\nJump to [missing anchor](target.md#nope).\n",
        encoding="utf-8",
    )
    (docs / "target.md").write_text("# Target\n\nText.\n", encoding="utf-8")

    p = _run_cli(tmp_path, "docs")

    assert p.returncode == 1
    assert "❌ Markdown link check: BROKEN LINKS FOUND" in p.stdout
    assert re.search(
        r"^- docs/source\.md: \(target\.md#nope\) -> anchor '#nope' not found in docs/target\.md$",
        p.stdout,
        flags=re.MULTILINE,
    )
    assert "Total broken links: 1" in p.stdout
    assert p.stderr == ""


def test_cli_ignores_external_and_contact_links(tmp_path: Path) -> None:
    docs = tmp_path / "docs"
    docs.mkdir(parents=True, exist_ok=True)
    (docs / "external_only.md").write_text(
        "# External\n\n"
        "[web](https://example.com)\n"
        "[mail](mailto:ops@example.com)\n"
        "[phone](tel:+490000000)\n",
        encoding="utf-8",
    )

    p = _run_cli(tmp_path, "docs/external_only.md")

    assert p.returncode == 0
    assert "✅ Markdown link check: OK (no broken internal links found)" in p.stdout
    assert p.stderr == ""
