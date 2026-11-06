"""
Shared reference-target extraction for docs reference targets tooling.

Must stay aligned with scripts/ops/verify_docs_reference_targets.sh (embedded Python)
and scripts/ops/collect_docs_reference_targets_fullscan.py.
"""

from __future__ import annotations

import html
import re
from pathlib import Path

# Inline ignore marker (same line skips all reference extraction)
IGNORE_MARKER = "<!-- pt:ref-target-ignore -->"

# Patterns:
#  - Markdown links: [text](relative/path.ext)
#  - Inline code blocks: `relative/path.ext`
#  - Bare paths: config/.../x.toml (etc.)
LINK_RE = re.compile(r"\[[^\]]*\]\(([^)]+)\)")
CODE_RE = re.compile(r"`([^`]+)`")
BARE_RE = re.compile(
    r"(?<![\w/.\-])"
    r"(?:(?:config|docs|src|scripts|\.github)/[A-Za-z0-9_\-./]+?\.(?:toml|md|py|yml|yaml|sh|json|txt))"
    r"(?![\w/.\-])"
)


def is_url(s: str) -> bool:
    s2 = s.strip()
    return (
        s2.startswith("http://")
        or s2.startswith("https://")
        or s2.startswith("mailto:")
        or "://" in s2
    )


def normalize_target(raw: str) -> str | None:
    t = raw.strip()

    # strip leading/trailing punctuation that commonly wraps paths
    t = t.strip().lstrip("(<\"'").rstrip(")>\"'.,;:]")

    # Decode HTML entities (e.g. &#47; from docs token policy) before treating # as anchor.
    t = html.unescape(t)

    # ignore anchors-only
    if t.startswith("#"):
        return None

    # ignore URLs
    if is_url(t):
        return None

    # strip anchor fragments: file.md#section
    if "#" in t:
        t = t.split("#", 1)[0].strip()

    # strip query parameters: file.md?plain=1
    if "?" in t:
        t = t.split("?", 1)[0].strip()

    # ignore empty
    if not t:
        return None

    # ignore wildcards and globs (*, ?, [, ], <>)
    if any(c in t for c in ("*", "?", "[", "]", "<", ">")):
        return None

    # ignore if it looks like a command (space-separated)
    if " " in t:
        return None

    # ignore directory-only references (trailing slash)
    if t.endswith("/"):
        return None

    # check if this is a relative path
    is_relative = t.startswith("./") or t.startswith("../")

    # normalize leading / for absolute repo paths
    if t.startswith("/"):
        t = t[1:]

    # quick filter: we only validate repo-ish paths or relative paths
    roots = ("config/", "docs/", "src/", "scripts/", ".github/")
    if not is_relative and not t.startswith(roots):
        return None

    return t


def inline_code_spans(line: str) -> list[tuple[int, int]]:
    """Half-open [start, end) ranges for each `...` inline code span (incl. backticks)."""
    return [(m.start(), m.end()) for m in CODE_RE.finditer(line)]


def range_overlaps(a0: int, a1: int, spans: list[tuple[int, int]]) -> bool:
    """True if [a0, a1) overlaps any span in spans."""
    for s, e in spans:
        if a0 < e and a1 > s:
            return True
    return False


def safe_is_within(p: Path, root: Path) -> bool:
    try:
        rp = p.resolve()
        return str(rp).startswith(str(root))
    except Exception:
        return False


def resolve_target(target: str, doc_file: Path, repo_root: Path) -> Path | None:
    """Resolve a target path to an absolute path within repo_root, or None if outside."""
    if target.startswith("./") or target.startswith("../"):
        doc_dir = doc_file.parent
        resolved = (doc_dir / target).resolve()
    else:
        resolved = (repo_root / target).resolve()

    if not safe_is_within(resolved, repo_root):
        return None

    return resolved


def extract_targets_from_line(line: str) -> list[str]:
    """Extract normalized repo path targets from one markdown line (not inside code fences)."""
    out: list[str] = []
    for raw in LINK_RE.findall(line):
        t = normalize_target(raw)
        if t:
            out.append(t)
    for raw in CODE_RE.findall(line):
        t = normalize_target(raw)
        if t:
            out.append(t)
    ic_spans = inline_code_spans(line)
    for m in BARE_RE.finditer(line):
        if range_overlaps(m.start(), m.end(), ic_spans):
            continue
        raw = m.group(0)
        t = normalize_target(raw)
        if t:
            out.append(t)
    return out


def extract_references_from_markdown_file(file_path: Path) -> list[tuple[int, str, str]]:
    """
    Extract references from a markdown file (same rules as verify script).

    Returns:
        List of (line_number, target, link_text). link_text is always "" (parity with gate).
    """
    refs: list[tuple[int, str, str]] = []

    try:
        lines = file_path.read_text(encoding="utf-8", errors="replace").splitlines()
    except Exception:
        return refs

    in_code_block = False

    for i, line in enumerate(lines, start=1):
        if line.strip().startswith("```"):
            in_code_block = not in_code_block
            continue

        if in_code_block or IGNORE_MARKER in line:
            continue

        for t in extract_targets_from_line(line):
            refs.append((i, t, ""))

    return refs
