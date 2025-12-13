from __future__ import annotations

import os
import re
import subprocess
import sys
import urllib.parse
from pathlib import Path


def _git_repo_root() -> Path:
    """Return repo root in a worktree-safe way."""
    try:
        out = subprocess.check_output(["git", "rev-parse", "--show-toplevel"], text=True).strip()
        if out:
            return Path(out)
    except Exception:
        pass
    # Fallback: tests/.. = repo root in standard layout
    return Path(__file__).resolve().parents[1]


def _ensure_board_built(repo_root: Path, html_path: Path) -> None:
    """Build board if it doesn't exist (keeps CI robust for fresh checkouts)."""
    if html_path.exists():
        return
    cmd = [sys.executable, "scripts/build_todo_board_html.py"]
    subprocess.run(cmd, cwd=str(repo_root), check=True)


def _read_html(html_path: Path) -> str:
    return html_path.read_text(encoding="utf-8", errors="replace")


def test_todo_board_html_exists_and_contains_expected_markers() -> None:
    repo_root = _git_repo_root()
    html_path = repo_root / "docs/00_overview/PEAK_TRADE_TODO_BOARD.html"
    _ensure_board_built(repo_root, html_path)

    assert html_path.exists(), f"TODO board HTML missing at: {html_path}"

    text = _read_html(html_path)
    low = text.lower()

    # Minimal sanity markers (avoid fragile exact strings)
    assert "<html" in low or "<!doctype html" in low
    assert "todo" in low, "Expected TODO-related content in HTML"
    assert ("cursor://" in text) or ("__REPO_ROOT__" in text), "Expected cursor links or repo-root placeholder"


def test_no_absolute_repo_root_path_leaks_into_html() -> None:
    repo_root = _git_repo_root()
    html_path = repo_root / "docs/00_overview/PEAK_TRADE_TODO_BOARD.html"
    _ensure_board_built(repo_root, html_path)

    text = _read_html(html_path)

    abs_root = str(repo_root)
    enc_root = urllib.parse.quote(abs_root)

    assert abs_root not in text, f"Absolute repo root leaked into HTML: {abs_root}"
    assert enc_root not in text, f"URL-encoded repo root leaked into HTML: {enc_root}"


def test_cursor_links_use_repo_root_placeholder_and_no_absolute_paths() -> None:
    repo_root = _git_repo_root()
    html_path = repo_root / "docs/00_overview/PEAK_TRADE_TODO_BOARD.html"
    _ensure_board_built(repo_root, html_path)

    text = _read_html(html_path)

    # We expect placeholders to exist if cursor links are present
    if "cursor://" in text:
        assert "__REPO_ROOT__" in text, "cursor:// links present but __REPO_ROOT__ placeholder missing"

    # Hard fails: common absolute-path patterns
    forbidden_patterns = [
        r"cursor://file//Users/",          # macOS absolute
        r"cursor://file///Users/",         # macOS absolute variant
        r"cursor://file//[A-Za-z]:\\",     # Windows drive absolute
        r"cursor://file///[A-Za-z]:\\",    # Windows drive absolute variant
        r"file:///",                       # file URLs should not be emitted into board
        r"/Users/",                        # generic macOS absolute path leak
        r"[A-Za-z]:\\",                    # generic Windows absolute path leak
    ]
    for pat in forbidden_patterns:
        assert re.search(pat, text) is None, f"Forbidden path leak detected: pattern={pat}"


def test_windows_file_urls_not_present_in_html() -> None:
    repo_root = _git_repo_root()
    html_path = repo_root / "docs/00_overview/PEAK_TRADE_TODO_BOARD.html"
    _ensure_board_built(repo_root, html_path)

    text = _read_html(html_path)

    # Specifically guard against Windows file URL variants
    assert "file:///" not in text
    assert "file:\\" not in text
