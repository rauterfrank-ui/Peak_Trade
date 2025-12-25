#!/usr/bin/env python3
from __future__ import annotations

import argparse
import os
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence, Tuple


@dataclass(frozen=True)
class BrokenLink:
    src_file: str
    link: str
    reason: str


LINK_RE = re.compile(r"(?<!\!)\[[^\]]*\]\(([^)]+)\)")  # ignore images ![alt](...)
CODE_FENCE_RE = re.compile(r"^```")
HEADING_RE = re.compile(r"^(#{1,6})\s+(.*)$")


def _strip_code_fences(md: str) -> str:
    """Remove fenced code blocks to avoid matching links inside code."""
    out: List[str] = []
    in_fence = False
    for line in md.splitlines():
        if CODE_FENCE_RE.match(line.strip()):
            in_fence = not in_fence
            continue
        if not in_fence:
            out.append(line)
    return "\n".join(out)


def _github_slugify(text: str) -> str:
    """
    Approximate GitHub anchor slug rules for headings.
    - lower
    - remove punctuation (keep spaces and hyphens)
    - collapse whitespace to '-'
    - collapse multiple '-' to one
    - strip leading/trailing '-'
    """
    s = text.strip().lower()
    # remove inline markdown formatting characters
    s = re.sub(r"[`*_~]+", "", s)
    # remove punctuation except spaces/hyphens
    s = re.sub(r"[^a-z0-9\s\-]", "", s)
    s = re.sub(r"\s+", "-", s)
    s = re.sub(r"-{2,}", "-", s)
    s = s.strip("-")
    return s


def _collect_anchors(md: str) -> Dict[str, int]:
    """
    Collect possible anchors from headings, including GitHub's duplicate suffixing:
    first occurrence: slug
    second occurrence: slug-1
    third: slug-2, ...
    """
    counts: Dict[str, int] = {}
    anchors: Dict[str, int] = {}

    for line in md.splitlines():
        m = HEADING_RE.match(line.strip())
        if not m:
            continue
        heading_text = m.group(2).strip()
        slug = _github_slugify(heading_text)
        if not slug:
            continue

        n = counts.get(slug, 0)
        counts[slug] = n + 1

        anchored = slug if n == 0 else f"{slug}-{n}"
        anchors[anchored] = 1

    return anchors


def _parse_link_target(raw: str) -> str:
    """
    Strip surrounding <...> and optional title part:
      [x](path "title")
    Keep only 'path'.
    """
    raw = raw.strip()
    if raw.startswith("<") and raw.endswith(">"):
        raw = raw[1:-1].strip()

    # Split on whitespace to drop optional title.
    # This is a pragmatic approach; it matches typical Markdown link syntax.
    parts = raw.split()
    return parts[0].strip()


def _is_external(target: str) -> bool:
    t = target.lower()
    return (
        t.startswith("http://")
        or t.startswith("https://")
        or t.startswith("mailto:")
        or t.startswith("tel:")
    )


def _iter_markdown_files(root: Path, paths: Sequence[str]) -> Iterable[Path]:
    for p in paths:
        pp = (root / p).resolve()
        if pp.is_dir():
            yield from pp.rglob("*.md")
        elif pp.is_file() and pp.suffix.lower() == ".md":
            yield pp


def _read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


def check_links(root: Path, paths: Sequence[str]) -> List[BrokenLink]:
    broken: List[BrokenLink] = []

    md_files = sorted({p for p in _iter_markdown_files(root, paths)})

    # cache anchors per file
    anchor_cache: Dict[Path, Dict[str, int]] = {}

    for src in md_files:
        src_rel = str(src.relative_to(root))
        content = _strip_code_fences(_read_text(src))
        src_dir = src.parent

        # anchors in src file
        anchor_cache[src] = _collect_anchors(content)

        for m in LINK_RE.finditer(content):
            raw_target = _parse_link_target(m.group(1))
            if not raw_target:
                continue

            if _is_external(raw_target):
                continue

            # ignore pure queries like ?x=y (rare) and empty
            if raw_target.startswith("?"):
                continue

            # Split path + anchor
            if "#" in raw_target:
                path_part, anchor_part = raw_target.split("#", 1)
            else:
                path_part, anchor_part = raw_target, ""

            # In-page anchor only
            if path_part == "" and anchor_part:
                if anchor_part not in anchor_cache[src]:
                    broken.append(BrokenLink(src_rel, raw_target, f"anchor '#{anchor_part}' not found in {src_rel}"))
                continue

            # If path is empty and no anchor -> ignore (edge)
            if path_part == "" and not anchor_part:
                continue

            # Resolve referenced file
            ref_path = (src_dir / path_part).resolve()

            # Allow links to directories? (rare) -> treat as broken
            if not ref_path.exists():
                broken.append(BrokenLink(src_rel, raw_target, f"target file does not exist: {path_part}"))
                continue

            # If it's a directory, broken (we expect a file)
            if ref_path.is_dir():
                broken.append(BrokenLink(src_rel, raw_target, f"target is a directory, expected file: {path_part}"))
                continue

            # If anchor present, validate anchors in referenced file (only for .md)
            if anchor_part:
                if ref_path.suffix.lower() != ".md":
                    broken.append(BrokenLink(src_rel, raw_target, f"anchor used but target is not .md: {path_part}"))
                    continue

                if ref_path not in anchor_cache:
                    anchor_cache[ref_path] = _collect_anchors(_strip_code_fences(_read_text(ref_path)))

                if anchor_part not in anchor_cache[ref_path]:
                    ref_rel = str(ref_path.relative_to(root))
                    broken.append(BrokenLink(src_rel, raw_target, f"anchor '#{anchor_part}' not found in {ref_rel}"))

    return broken


def main() -> int:
    ap = argparse.ArgumentParser(description="Check internal markdown links (files + #anchors).")
    ap.add_argument("--root", default=".", help="Repository root (default: .)")
    ap.add_argument(
        "--paths",
        nargs="+",
        default=["README.md", "docs/ops", "docs/PEAK_TRADE_STATUS_OVERVIEW.md"],
        help="Files/directories to scan (default: README.md docs/ops docs/PEAK_TRADE_STATUS_OVERVIEW.md)",
    )
    args = ap.parse_args()

    root = Path(args.root).resolve()
    broken = check_links(root=root, paths=args.paths)

    if not broken:
        print("✅ Markdown link check: OK (no broken internal links found)")
        return 0

    print("❌ Markdown link check: BROKEN LINKS FOUND")
    for b in broken:
        print(f"- {b.src_file}: ({b.link}) -> {b.reason}")
    print(f"Total broken links: {len(broken)}")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
