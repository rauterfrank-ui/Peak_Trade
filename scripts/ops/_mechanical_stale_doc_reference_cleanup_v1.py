#!/usr/bin/env python3
"""One-shot mechanical stale doc reference cleanup for convergence cut PR."""

from __future__ import annotations

import re
import subprocess
import sys
from collections import defaultdict
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from src.ops.docs_reference_targets_common import (
    BARE_RE,
    IGNORE_MARKER,
    extract_targets_from_line,
    inline_code_spans,
    normalize_target,
    range_overlaps,
    resolve_target,
)


def _md_files(root: Path) -> list[Path]:
    out = subprocess.check_output(["git", "ls-files", "docs"], cwd=root, text=True)
    return [root / p for p in out.splitlines() if p.endswith(".md")]


def _missing_refs(root: Path, md_files: list[Path]) -> list[tuple[Path, int, str]]:
    missing: list[tuple[Path, int, str]] = []
    for f in md_files:
        if not f.exists():
            continue
        lines = f.read_text(encoding="utf-8", errors="replace").splitlines()
        in_code = False
        for i, line in enumerate(lines, start=1):
            if line.strip().startswith("```"):
                in_code = not in_code
                continue
            if in_code or IGNORE_MARKER in line:
                continue
            for t in extract_targets_from_line(line):
                resolved = resolve_target(t, f, root)
                if resolved is None or not resolved.is_file():
                    missing.append((f, i, t))
    return missing


def _clean_line(line: str, bad_targets: set[str]) -> str:
    new = line

    def link_repl2(m: re.Match[str]) -> str:
        label = m.group(1)
        raw = m.group(2)
        t = normalize_target(raw)
        if t in bad_targets:
            return label
        return m.group(0)

    new = re.sub(r"\[([^\]]*)\]\(([^)]+)\)", link_repl2, new)

    def code_repl(m: re.Match[str]) -> str:
        t = normalize_target(m.group(1))
        if t in bad_targets:
            return ""
        return m.group(0)

    new = re.sub(r"`([^`]+)`", code_repl, new)

    ic_spans = inline_code_spans(new)
    parts: list[str] = []
    last = 0
    for m in BARE_RE.finditer(new):
        if range_overlaps(m.start(), m.end(), ic_spans):
            continue
        t = normalize_target(m.group(0))
        if t in bad_targets:
            parts.append(new[last : m.start()])
            last = m.end()
    if parts:
        new = "".join(parts) + new[last:]

    return re.sub(r"  +", " ", new).rstrip()


def main() -> int:
    root = Path(".").resolve()
    md_files = _md_files(root)
    line_edits = 0
    for _round in range(12):
        miss = _missing_refs(root, md_files)
        if not miss:
            print(f"REMAINING_MISSING=0 ROUNDS={_round} LINE_EDITS={line_edits}")
            return 0
        by_file_line: dict[tuple[Path, int], set[str]] = defaultdict(set)
        for f, ln, t in miss:
            by_file_line[(f, ln)].add(t)
        for (f, ln), targets in by_file_line.items():
            lines = f.read_text(encoding="utf-8", errors="replace").splitlines()
            idx = ln - 1
            old = lines[idx]
            new = _clean_line(old, targets)
            if new != old:
                lines[idx] = new
                f.write_text("\n".join(lines) + "\n", encoding="utf-8")
                line_edits += 1
    remaining = len(_missing_refs(root, md_files))
    print(f"REMAINING_MISSING={remaining} LINE_EDITS={line_edits}")
    return 1 if remaining else 0


if __name__ == "__main__":
    raise SystemExit(main())
