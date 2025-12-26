#!/usr/bin/env python3
"""
Generic markdown section inserter with CLI support and detailed result tracking.

Usage:
  python3 insert_docs_diff_guard_section.py
  python3 insert_docs_diff_guard_section.py --files docs/ops/README.md,docs/ops/TOOLKIT.md
  python3 insert_docs_diff_guard_section.py --print-snippet
  python3 insert_docs_diff_guard_section.py --dry-run
  python3 insert_docs_diff_guard_section.py --anchors "## Quick Start,## Toolkit"
"""

from __future__ import annotations

import argparse
import sys
from dataclasses import dataclass
from pathlib import Path

SECTION_MARKER = "Docs Diff Guard (auto beim Merge)"

SNIPPET = """\
## Docs Diff Guard (auto beim Merge)

Beim `--merge` läuft standardmäßig automatisch ein **Docs Diff Guard**, der große versehentliche Löschungen in `docs/*` erkennt und **den Merge blockiert**.

### Override-Optionen
```bash
# Custom Threshold (z.B. bei beabsichtigter Restrukturierung)
scripts/ops/review_and_merge_pr.sh --pr 123 --merge --docs-guard-threshold 500

# Warn-only (kein Fail, nur Warnung)
scripts/ops/review_and_merge_pr.sh --pr 123 --merge --docs-guard-warn-only

# Guard komplett überspringen (NOT RECOMMENDED)
scripts/ops/review_and_merge_pr.sh --pr 123 --merge --skip-docs-guard
```

**Siehe auch:**
- Vollständige Dokumentation: `docs/ops/README.md` (Abschnitt "Docs Diff Guard")
- PR Management Toolkit: `docs/ops/PR_MANAGEMENT_TOOLKIT.md`
- Standalone Script: `scripts/ops/docs_diff_guard.sh`
- Merge-Log: `docs/ops/PR_311_MERGE_LOG.md`
"""

DEFAULT_ANCHORS = [
    "## 🚀 Quick Start",
    "## Quick Start",
    "review_and_merge_pr.sh",
    "PR Review",
    "PR Management",
    "## Toolkit",
]

DEFAULT_TARGET_FILES: list[Path] = [
    # Add default files here if needed
]


@dataclass
class Result:
    """Result of insert operation."""

    path: Path
    changed: bool
    mode: str  # skipped_not_found, skipped_present, inserted, appended


def _parse_csv_list(csv: str | None) -> list[str]:
    """Parse comma-separated list, returns empty list if None."""
    if not csv:
        return []
    return [x.strip() for x in csv.split(",") if x.strip()]


def insert_into_file(
    p: Path,
    marker: str,
    snippet: str,
    anchors: list[str],
    dry_run: bool = False,
) -> Result:
    """
    Inserts snippet into markdown file p (idempotent).
    Returns Result with detailed operation info.
    """
    if not p.exists():
        print(f"⏭️  Skip (nicht gefunden): {p}")
        return Result(path=p, changed=False, mode="skipped_not_found")

    s = p.read_text(encoding="utf-8")
    if marker in s:
        print(f"ℹ️  Skip (bereits vorhanden): {p}")
        return Result(path=p, changed=False, mode="skipped_present")

    snippet_block = snippet.strip() + "\n"

    for a in anchors:
        idx = s.find(a)
        if idx != -1:
            line_end = s.find("\n", idx)
            if line_end == -1:
                line_end = len(s)
            insert_at = line_end + 1

            # ensure blank line separation around insert
            before = s[:insert_at]
            after = s[insert_at:]
            sep_before = "\n" if not before.endswith("\n\n") else ""
            sep_after = (
                "\n" if not snippet_block.endswith("\n\n") and not after.startswith("\n") else ""
            )
            s2 = before + sep_before + snippet_block + sep_after + after

            if not dry_run:
                p.write_text(s2, encoding="utf-8")
            print(f"✅ Inserted: {p} (anchor: {a}){' [dry-run]' if dry_run else ''}")
            return Result(path=p, changed=True, mode="inserted")

    # Fallback: append at end
    s2 = s.rstrip() + "\n\n" + snippet_block
    if not dry_run:
        p.write_text(s2, encoding="utf-8")
    print(f"✅ Appended:  {p}{' [dry-run]' if dry_run else ''}")
    return Result(path=p, changed=True, mode="appended")


def parse_args() -> argparse.Namespace:
    ap = argparse.ArgumentParser(
        description="Insert Docs Diff Guard section into markdown files (idempotent)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    ap.add_argument(
        "--files",
        type=str,
        help="Comma-separated list of files (overrides default TARGET_FILES)",
    )
    ap.add_argument(
        "--anchors",
        type=str,
        help="Comma-separated list of anchor strings (overrides DEFAULT_ANCHORS)",
    )
    ap.add_argument(
        "--print-snippet",
        action="store_true",
        help="Print snippet and exit",
    )
    ap.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be done without making changes",
    )
    return ap.parse_args()


def main() -> int:
    args = parse_args()

    if args.print_snippet:
        print(SNIPPET.strip())
        return 0

    files = _parse_csv_list(args.files)
    anchors = _parse_csv_list(args.anchors)

    target_paths = [Path(x) for x in files] if files else list(DEFAULT_TARGET_FILES)
    anchor_list = anchors if anchors else list(DEFAULT_ANCHORS)

    if not target_paths:
        print("❌ No target files specified. Use --files or set DEFAULT_TARGET_FILES in script.")
        return 1

    print("🧩 Insert Section")
    print(f"  Marker:   {SECTION_MARKER}")
    print(f"  Targets:  {', '.join(str(p) for p in target_paths)}")
    print(f"  Anchors:  {len(anchor_list)} anchor(s)")
    print(f"  Dry-run:  {bool(args.dry_run)}")
    print("")

    results: list[Result] = []
    for p in target_paths:
        res = insert_into_file(
            p,
            marker=SECTION_MARKER,
            snippet=SNIPPET,
            anchors=anchor_list,
            dry_run=args.dry_run,
        )
        results.append(res)

    # Summary
    changed_count = sum(1 for r in results if r.changed)
    print("")
    print(
        f"🎉 Done: {changed_count}/{len(results)} file(s) {'would be ' if args.dry_run else ''}modified."
    )

    return 0  # Always success (idempotent)


if __name__ == "__main__":
    sys.exit(main())
