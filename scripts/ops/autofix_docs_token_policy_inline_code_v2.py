#!/usr/bin/env python3
"""
Conservative auto-fixer for Docs Token Policy Gate violations.

Strategy:
- Only rewrites *inline code spans* (single backticks) in Markdown.
- Escapes "/" -> "&#47;" inside inline code when the span looks like:
  (a) COMMAND: starts with known command verbs OR contains spaces and a known command token
  (b) HTTP ENDPOINT: starts with HTTP verb + space + "/" (e.g., "GET /ops/ci-health")
- Skips:
  - URLs containing "://"
  - already-escaped spans containing "&#47;"
  - fenced code blocks (``` ... ```) entirely (no changes there)

Usage:
  python scripts/ops/autofix_docs_token_policy_inline_code_v2.py --dry-run <file1> <file2> ...
  python scripts/ops/autofix_docs_token_policy_inline_code_v2.py --write   <file1> <file2> ...
"""

from __future__ import annotations

import argparse
import re
from pathlib import Path
from typing import Iterable, Tuple

INLINE_CODE_RE = re.compile(r"(?<!`)`([^`\n]+)`(?!`)")  # single-backtick spans, no newlines
FENCED_BLOCK_RE = re.compile(r"```.*?```", re.DOTALL)

HTTP_VERBS = ("GET", "POST", "PUT", "PATCH", "DELETE", "HEAD", "OPTIONS")

# common CLI tokens that often include "/" and should NOT be treated as repo paths in docs gate
COMMAND_HINTS = (
    "pytest",
    "uv ",
    "uvx ",
    "python ",
    "python3 ",
    "pip ",
    "git ",
    "gh ",
    "curl ",
    "make ",
    "bash ",
    "zsh ",
)


def looks_like_url(s: str) -> bool:
    return "://" in s


def looks_like_http_endpoint(s: str) -> bool:
    # e.g. "GET /ops/ci-health", "POST /api/v1/foo"
    parts = s.strip().split(None, 1)
    if len(parts) != 2:
        return False
    verb, rest = parts
    return verb in HTTP_VERBS and rest.startswith("/")


def looks_like_command(s: str) -> bool:
    st = s.strip()
    if looks_like_url(st):
        return False
    # strong: starts with a command verb
    for hint in COMMAND_HINTS:
        if st.startswith(hint):
            return True
    # weak: has spaces and contains a command token
    if " " in st:
        for hint in ("pytest", "uv", "python", "git", "gh", "curl", "make", "bash", "zsh"):
            if re.search(rf"(^|\s){re.escape(hint)}(\s|$)", st):
                return True
    return False


def escape_slashes(s: str) -> str:
    # idempotent: do not re-escape
    if "&#47;" in s:
        return s
    return s.replace("/", "&#47;")


def rewrite_inline_code(md: str) -> Tuple[str, int]:
    # protect fenced blocks from any modifications
    fenced_blocks: list[str] = []

    def _fence_repl(m: re.Match) -> str:
        fenced_blocks.append(m.group(0))
        return f"__FENCED_BLOCK_{len(fenced_blocks)-1}__"

    protected = FENCED_BLOCK_RE.sub(_fence_repl, md)

    changes = 0

    def _inline_repl(m: re.Match) -> str:
        nonlocal changes
        inner = m.group(1)

        # skip URLs and already-escaped
        if looks_like_url(inner) or "&#47;" in inner:
            return m.group(0)

        if looks_like_http_endpoint(inner) or looks_like_command(inner):
            if "/" in inner:
                changes += 1
                return f"`{escape_slashes(inner)}`"
        return m.group(0)

    rewritten = INLINE_CODE_RE.sub(_inline_repl, protected)

    # restore fenced blocks
    for i, block in enumerate(fenced_blocks):
        rewritten = rewritten.replace(f"__FENCED_BLOCK_{i}__", block)

    return rewritten, changes


def iter_files(paths: Iterable[str]) -> list[Path]:
    out: list[Path] = []
    for p in paths:
        path = Path(p)
        if not path.exists() or not path.is_file():
            raise FileNotFoundError(f"File not found: {p}")
        out.append(path)
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    mode = ap.add_mutually_exclusive_group(required=True)
    mode.add_argument("--dry-run", action="store_true")
    mode.add_argument("--write", action="store_true")
    ap.add_argument("files", nargs="+")
    args = ap.parse_args()

    files = iter_files(args.files)
    total_changes = 0

    for f in files:
        original = f.read_text(encoding="utf-8")
        rewritten, changes = rewrite_inline_code(original)
        total_changes += changes

        if args.dry_run:
            print(f"[DRY-RUN] {f}: {changes} inline-code span(s) rewritten")
        else:
            if rewritten != original:
                f.write_text(rewritten, encoding="utf-8")
            print(f"[WRITE]   {f}: {changes} inline-code span(s) rewritten")

    print(f"TOTAL rewritten spans: {total_changes}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
