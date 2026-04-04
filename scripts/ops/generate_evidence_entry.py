#!/usr/bin/env python3
"""
Peak_Trade – Evidence Entry Generator (v0.3)

Purpose: Generate evidence entry files from command-line arguments.
Owner: ops
Status: Operational

Usage:
    python scripts/ops/generate_evidence_entry.py \\
        --tag PHASE1 \\
        --category "Test/Refactor" \\
        --title "Phase 1 Baseline Tests" \\
        [--id EV-20260107-PHASE1] \\
        [--date 2026-01-07] \\
        [--out-dir docs/ops/evidence]

Exit Codes:
    0 = Success
    1 = Invalid arguments / file already exists
"""

from __future__ import annotations

import argparse
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional, Sequence

# Schema: Valid categories (case-insensitive, normalized to Title Case)
# Draft slot text in generated Markdown (local operator workflow; not live secrets).
# Avoids literal TBD/XXX tokens so repo placeholder inventory stays triage-friendly.
_DRAFT = "[draft — replace]"

VALID_CATEGORIES = {
    "ci/workflow",
    "drill/operator",
    "test/refactor",
    "incident/rca",
    "config snapshot",
}


def normalize_category(category: str) -> str:
    """Normalize category to Title Case."""
    normalized = category.lower().strip()
    if normalized not in VALID_CATEGORIES:
        raise ValueError(
            f"Invalid category: {category}. Valid: {', '.join(sorted(VALID_CATEGORIES))}"
        )
    # Return title case for display
    return category.strip().title()


def generate_evidence_id(tag: str, date_str: str) -> str:
    """Generate Evidence ID: EV-YYYYMMDD-<TAG>."""
    date_part = date_str.replace("-", "")
    tag_upper = tag.upper().replace("_", "-")
    return f"EV-{date_part}-{tag_upper}"


def generate_template(
    evidence_id: str,
    date: str,
    category: str,
    title: str,
    owner: str = "ops",
) -> str:
    """Generate evidence entry content from template."""
    return f"""# Evidence Entry: {title}

**Evidence ID:** {evidence_id}
**Date:** {date}
**Category:** {category}
**Owner:** {owner}
**Status:** DRAFT

---

## Scope
[1–2 sentences: What system/component/process does this evidence cover?]

---

## Claims
[What does this evidence demonstrate? Be specific and factual.]
- Claim 1: {_DRAFT}
- Claim 2: {_DRAFT}

---

## Evidence / Source Links
- Primary source: {_DRAFT}
- CI run / commit: {_DRAFT}

---

## Verification Steps
[How can someone verify this evidence?]
1. Step 1: {_DRAFT}
2. Step 2: {_DRAFT}
3. Expected result: {_DRAFT}

---

## Risk Notes
[Optional: Any caveats, limitations, or risk context]
- {_DRAFT}

---

## Related PRs / Commits
- PR #<pr-number> — {_DRAFT}
- Commit: {_DRAFT}

---

## Owner / Responsibility
**Owner:** {owner}
**Contact:** {_DRAFT}

---

**Entry Created:** {date}
**Last Updated:** {date}
**Template Version:** v0.3
"""


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        description="Generate evidence entry file",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Generate with auto-ID
  python scripts/ops/generate_evidence_entry.py \\
      --tag PHASE1 \\
      --category "Test/Refactor" \\
      --title "Phase 1 Baseline Tests"

  # Generate with explicit ID
  python scripts/ops/generate_evidence_entry.py \\
      --id EV-20260107-CUSTOM \\
      --category "CI/Workflow" \\
      --title "Custom CI Run"
        """,
    )

    parser.add_argument(
        "--id",
        type=str,
        help="Evidence ID (format: EV-YYYYMMDD-<TAG>). If omitted, auto-generated from --tag and --date.",
    )
    parser.add_argument(
        "--tag",
        type=str,
        help="Tag for auto-generating ID (required if --id not provided). Example: PHASE1, PR518",
    )
    parser.add_argument(
        "--date",
        type=str,
        default=datetime.now().strftime("%Y-%m-%d"),
        help="Evidence date (YYYY-MM-DD). Default: today.",
    )
    parser.add_argument(
        "--category",
        type=str,
        required=True,
        help="Evidence category (CI/Workflow, Drill/Operator, Test/Refactor, Incident/RCA, Config Snapshot)",
    )
    parser.add_argument(
        "--title",
        type=str,
        required=True,
        help="Short title for the evidence entry",
    )
    parser.add_argument(
        "--owner",
        type=str,
        default="ops",
        help="Owner (username/team/role). Default: ops",
    )
    parser.add_argument(
        "--out-dir",
        type=str,
        default="docs/ops/evidence",
        help="Output directory. Default: docs/ops/evidence",
    )

    args = parser.parse_args(argv)

    # Validate inputs
    try:
        # Validate date format
        datetime.strptime(args.date, "%Y-%m-%d")
    except ValueError:
        print(f"❌ Error: Invalid date format: {args.date} (expected YYYY-MM-DD)", file=sys.stderr)
        return 1

    # Validate category
    try:
        category_normalized = normalize_category(args.category)
    except ValueError as e:
        print(f"❌ Error: {e}", file=sys.stderr)
        return 1

    # Generate or validate Evidence ID
    if args.id:
        evidence_id = args.id
        # Validate ID format
        if not evidence_id.startswith("EV-"):
            print(f"❌ Error: Evidence ID must start with 'EV-': {evidence_id}", file=sys.stderr)
            return 1
    else:
        if not args.tag or not args.tag.strip():
            print(
                "❌ Error: Either --id or a non-empty --tag must be provided",
                file=sys.stderr,
            )
            return 1
        evidence_id = generate_evidence_id(args.tag.strip(), args.date)

    # Prepare output path
    out_dir = Path(args.out_dir)
    if out_dir.exists() and out_dir.is_file():
        print(
            f"❌ Error: --out-dir must be a directory, not a file: {out_dir}",
            file=sys.stderr,
        )
        return 1
    out_dir.mkdir(parents=True, exist_ok=True)

    out_file = out_dir / f"{evidence_id}.md"

    # Prevent overwrite
    if out_file.exists():
        print(f"❌ Error: File already exists: {out_file}", file=sys.stderr)
        print("   Use a different --id or --tag to avoid collision.", file=sys.stderr)
        return 1

    # Generate content
    content = generate_template(
        evidence_id=evidence_id,
        date=args.date,
        category=category_normalized,
        title=args.title,
        owner=args.owner,
    )

    # Write file
    out_file.write_text(content, encoding="utf-8")

    # Success message
    print(f"✅ Evidence entry created: {out_file}")
    print(f"   Evidence ID: {evidence_id}")
    print(f"   Category: {category_normalized}")
    print(f"   Date: {args.date}")
    print()
    print("Next steps:")
    print(f"  1. Edit {out_file} to fill in draft placeholders")
    print(f"  2. Add entry to docs/ops/EVIDENCE_INDEX.md (table + category section)")
    print(f"  3. Run: python scripts/ops/validate_evidence_index.py")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
