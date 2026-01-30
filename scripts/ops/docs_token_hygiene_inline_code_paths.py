#!/usr/bin/env python3
"""
docs token hygiene: normalize slash-containing path/ref tokens inside *inline code* spans only.

- Only touches Markdown inline code (single backticks), NOT fenced code blocks (```).
- Replaces "/" with "&#47;" only when the inline-code token looks like a path/ref
  (heuristic: contains "/" but NOT "://", not URL-ish).
- Dry-run prints a unified diff; --apply writes file after creating a backup under .ops_local/backup_docs/...

Usage:
  python3 scripts/ops/docs_token_hygiene_inline_code_paths.py --path <file.md>
  python3 scripts/ops/docs_token_hygiene_inline_code_paths.py --path <file.md> --apply
"""

from __future__ import annotations

import argparse
import datetime as dt
import difflib
from pathlib import Path


def utc_ts() -> str:
    return dt.datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")


def is_urlish(s: str) -> bool:
    ls = s.lower()
    return (
        "://" in s
        or ls.startswith("http://")
        or ls.startswith("https://")
        or ls.startswith("mailto:")
        or ls.startswith("www.")
    )


def should_encode_inline_code_token(tok: str) -> bool:
    # only encode if it looks like a path/ref and contains at least one '/'
    if "/" not in tok:
        return False
    if "&#47;" in tok:
        return False  # already encoded
    if is_urlish(tok):
        return False
    # avoid touching common things that are not "paths" even if they contain '/'
    # (add more excludes if needed later)
    if tok.strip() in {"/", "//"}:
        return False
    return True


def encode_slashes(tok: str) -> str:
    return tok.replace("/", "&#47;")


def process_markdown(text: str) -> str:
    """
    Process markdown while respecting fenced code blocks.
    Only transforms inline code spans in non-fenced regions.
    """
    out_lines: list[str] = []
    in_fence = False
    fence_delim = ""  # ``` or ~~~

    for line in text.splitlines(keepends=False):
        stripped = line.lstrip()

        # Fence toggling (``` or ~~~), allow indentation
        if stripped.startswith("```") or stripped.startswith("~~~"):
            delim = "```" if stripped.startswith("```") else "~~~"
            if not in_fence:
                in_fence = True
                fence_delim = delim
            else:
                # only close if same delimiter
                if fence_delim == delim:
                    in_fence = False
                    fence_delim = ""
            out_lines.append(line)
            continue

        if in_fence:
            out_lines.append(line)
            continue

        # Outside fences: rewrite inline code spans.
        # Simple state machine: split by backtick while preserving pairs.
        parts = line.split("`")
        if len(parts) < 3:
            out_lines.append(line)
            continue

        # Odd indices are inside inline code spans (best-effort; ignores nested/backtick-escaping edge cases).
        for i in range(1, len(parts), 2):
            tok = parts[i]
            if should_encode_inline_code_token(tok):
                parts[i] = encode_slashes(tok)

        out_lines.append("`".join(parts))

    return "\n".join(out_lines) + ("\n" if text.endswith("\n") else "")


def backup_file(src: Path, repo_root: Path) -> Path:
    rel = src.relative_to(repo_root)
    out = repo_root / ".ops_local" / "backup_docs" / rel.parent / f"{rel.stem}.{utc_ts()}.bak{src.suffix}"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_bytes(src.read_bytes())
    return out


def find_repo_root(start: Path) -> Path:
    cur = start.resolve()
    for _ in range(25):
        if (cur / ".git").exists():
            return cur
        if cur.parent == cur:
            break
        cur = cur.parent
    return start.resolve()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--path", required=True, help="Path to markdown file (repo-relative or absolute).")
    ap.add_argument("--apply", action="store_true", help="Write changes (default: dry-run).")
    args = ap.parse_args()

    p = Path(args.path)
    if not p.is_absolute():
        repo = find_repo_root(Path.cwd())
        p = (repo / p).resolve()
    else:
        repo = find_repo_root(p.parent)

    if not p.exists():
        print(f"ERROR: file not found: {p}")
        return 2

    before = p.read_text(encoding="utf-8")
    after = process_markdown(before)

    if before == after:
        print("SKIP: no changes (idempotent).")
        return 0

    diff = difflib.unified_diff(
        before.splitlines(True),
        after.splitlines(True),
        fromfile=str(p),
        tofile=str(p),
        lineterm="",
    )
    print("== docs token hygiene (inline code paths) ==")
    print("mode:", "APPLY" if args.apply else "DRY-RUN")
    print("file:", p)
    print("".join(diff))

    if args.apply:
        b = backup_file(p, repo)
        print(f"backup: {b}")
        p.write_text(after, encoding="utf-8")
        print("write: OK")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
