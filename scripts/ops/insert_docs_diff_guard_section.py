#!/usr/bin/env python3
"""
Generic markdown section inserter with CLI support (idempotent, reusable).

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

DEFAULT_TARGET_FILES = [
    # Add default files here if needed
    # Path("docs/ops/SOME_DOC.md"),
]


def insert_section_into_file(
    p: Path,
    snippet: str,
    marker: str,
    anchors: list[str],
    dry_run: bool = False,
) -> bool:
    """
    Inserts snippet into markdown file p (idempotent).
    Returns True if inserted/appended, False if already present or file missing.
    """
    if not p.exists():
        print(f"⏭️  Skip (nicht gefunden): {p}")
        return False

    s = p.read_text(encoding="utf-8")
    if marker in s:
        print(f"ℹ️  Skip (bereits vorhanden): {p}")
        return False

    snippet_clean = snippet.strip() + "\n"
    inserted = False

    for a in anchors:
        idx = s.find(a)
        if idx != -1:
            line_end = s.find("\n", idx)
            if line_end == -1:
                line_end = len(s)
            insert_at = line_end + 1

            # ensure blank line separation
            prefix = "\n" if not s[:insert_at].endswith("\n\n") else ""
            suffix = "\n" if not snippet_clean.endswith("\n\n") else ""
            s2 = s[:insert_at] + prefix + snippet_clean + suffix + s[insert_at:]

            if dry_run:
                print(f"🧪 DRY-RUN: would insert into {p} (anchor: {a})")
            else:
                p.write_text(s2, encoding="utf-8")
                print(f"✅ Inserted into: {p} (anchor: {a})")
            inserted = True
            break

    if not inserted:
        if dry_run:
            print(f"🧪 DRY-RUN: would append to end of {p}")
        else:
            p.write_text(s.rstrip() + "\n\n" + snippet_clean, encoding="utf-8")
            print(f"✅ Appended to end: {p}")

    return True


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Insert Docs Diff Guard section into markdown files (idempotent)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--files",
        type=str,
        help="Comma-separated list of files (overrides default TARGET_FILES)",
    )
    parser.add_argument(
        "--anchors",
        type=str,
        help="Comma-separated list of anchor strings (overrides DEFAULT_ANCHORS)",
    )
    parser.add_argument(
        "--print-snippet",
        action="store_true",
        help="Print snippet and exit",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be done without making changes",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    # Print snippet and exit
    if args.print_snippet:
        print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        print("📄 SNIPPET:")
        print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        print(SNIPPET)
        print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        print(f"MARKER: {SECTION_MARKER}")
        print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        return 0

    # Parse files
    if args.files:
        target_files = [Path(f.strip()) for f in args.files.split(",")]
    else:
        target_files = DEFAULT_TARGET_FILES

    if not target_files:
        print("❌ No target files specified. Use --files or set DEFAULT_TARGET_FILES in script.")
        return 1

    # Parse anchors
    anchors = (
        [a.strip() for a in args.anchors.split(",")]
        if args.anchors
        else DEFAULT_ANCHORS
    )

    # Process files
    if args.dry_run:
        print("🧪 DRY-RUN MODE (no changes will be made)")
        print("")

    modified = 0
    for p in target_files:
        if insert_section_into_file(
            p,
            SNIPPET,
            SECTION_MARKER,
            anchors,
            dry_run=args.dry_run,
        ):
            modified += 1

    print(f"\n🎉 Done: {modified} file(s) {'would be ' if args.dry_run else ''}modified.")
    return 0  # Always success (idempotent)


if __name__ == "__main__":
    sys.exit(main())
