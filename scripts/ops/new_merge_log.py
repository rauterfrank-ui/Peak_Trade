#!/usr/bin/env python3
"""
Generator für Merge Logs mit GitHub CLI Integration.

Nutzt `gh pr view` um PR-Metadaten automatisch zu holen und generiert
gate-safe Merge Logs nach MERGE_LOGS_STYLE_GUIDE.md.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any


def check_gh_available() -> bool:
    """Prüft ob gh CLI verfügbar ist."""
    try:
        result = subprocess.run(
            ["gh", "--version"],
            capture_output=True,
            text=True,
            check=False,
            timeout=5,
        )
        return result.returncode == 0
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False


def fetch_pr_metadata(pr_number: int) -> dict[str, Any] | None:
    """
    Holt PR-Metadaten via gh CLI.

    Args:
        pr_number: PR Nummer

    Returns:
        Dict mit PR-Metadaten oder None bei Fehler
    """
    try:
        result = subprocess.run(
            [
                "gh",
                "pr",
                "view",
                str(pr_number),
                "--json",
                "title,url,mergedAt,mergeCommit,baseRefName,headRefName,state",
            ],
            capture_output=True,
            text=True,
            check=False,
            timeout=10,
        )

        if result.returncode != 0:
            print(f"[error] gh pr view failed: {result.stderr}", file=sys.stderr)
            return None

        data = json.loads(result.stdout)
        return data

    except (subprocess.TimeoutExpired, json.JSONDecodeError, FileNotFoundError) as exc:
        print(f"[error] Failed to fetch PR metadata: {exc}", file=sys.stderr)
        return None


def generate_merge_log_content(
    pr_number: int,
    title: str,
    pr_url: str,
    merged_at: str | None = None,
    merge_commit: str | None = None,
    head_ref: str | None = None,
) -> str:
    """
    Generiert Merge Log Content nach Style Guide.

    Args:
        pr_number: PR Nummer
        title: PR Titel
        pr_url: PR URL
        merged_at: Merge Timestamp (optional)
        merge_commit: Merge Commit SHA (optional)
        head_ref: Branch Name (optional)

    Returns:
        Merge Log Content als String
    """
    # Parse merged_at timestamp
    date_str = "YYYY-MM-DD"
    if merged_at:
        try:
            dt = datetime.fromisoformat(merged_at.replace("Z", "+00:00"))
            date_str = dt.strftime("%Y-%m-%d")
        except (ValueError, AttributeError):
            date_str = "YYYY-MM-DD"

    # De-pathify branch name if present
    branch_display = ""
    if head_ref:
        # Escape forward slashes in branch names
        branch_safe = head_ref.replace("/", "&#47;")
        branch_display = f"**Branch:** `{branch_safe}` → deleted\n"

    commit_display = ""
    if merge_commit:
        commit_display = f"**Merge Commit:** `{merge_commit}`\n"

    template = f"""# PR #{pr_number} — {title}

## Summary
[Brief description of what was changed]

## Why
[Motivation: why was this change needed?]

## Changes
- [List of changes]
- [Bullet points preferred]

## Verification
- [How was this verified?]
- [CI checks, manual tests, etc.]

## Risk
[Risk assessment: Minimal/Low/Medium/High + rationale]

## Operator How-To
- [Guidance for operators]
- [How to use/apply these changes]

## References
- PR: {pr_url}
{commit_display}
---

## Extended

**PR:** {pr_url}
**Merged:** {date_str}
{commit_display}{branch_display}
**Change Type:** [e.g., docs-only, feature, bugfix]

### Detailed Context

[Optional: Add detailed technical notes, full file lists, merge strategy details, etc.]

### Files Changed

```
[List changed files if relevant]
```

### CI Checks
- ✅ [Check name]: SUCCESS
- [Add relevant checks]

### Related Documentation

- [Add links to related docs, PRs, issues]

---

**Status:** ✅ Merged
**Impact:** [Describe impact on operators/system]
"""

    return template


def write_merge_log(
    output_path: Path,
    content: str,
    overwrite: bool = False,
) -> bool:
    """
    Schreibt Merge Log Datei.

    Args:
        output_path: Zieldatei
        content: Merge Log Content
        overwrite: Erlaube Überschreiben (default: False)

    Returns:
        True bei Erfolg, False bei Fehler
    """
    if output_path.exists() and not overwrite:
        print(
            f"[error] File already exists: {output_path}\nUse --overwrite to replace existing file",
            file=sys.stderr,
        )
        return False

    try:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(content, encoding="utf-8")
        print(f"[created] {output_path}")
        return True
    except OSError as exc:
        print(f"[error] Failed to write file: {exc}", file=sys.stderr)
        return False


def update_readme(
    readme_path: Path,
    pr_number: int,
    title: str,
    date_str: str,
    merge_log_filename: str,
) -> bool:
    """
    Aktualisiert docs/ops/README.md mit neuem Merge Log Link.

    Args:
        readme_path: Pfad zur README
        pr_number: PR Nummer
        title: PR Titel
        date_str: Merge Datum
        merge_log_filename: Dateiname des Merge Logs

    Returns:
        True bei Erfolg, False bei Fehler
    """
    if not readme_path.exists():
        print(f"[warning] README not found: {readme_path}", file=sys.stderr)
        return False

    try:
        text = readme_path.read_text(encoding="utf-8")

        # Check if already present
        signature = f"PR #{pr_number}"
        if f"PR_{pr_number}_MERGE_LOG.md" in text or signature in text:
            print(f"[skip] PR #{pr_number} already in README")
            return True

        # Find "Verified Merge Logs" or "Merge Logs" section
        target_sections = ["## Verified Merge Logs", "## Merge Logs"]
        section_found = None
        for section in target_sections:
            if section in text:
                section_found = section
                break

        if not section_found:
            print(
                f"[warning] No merge logs section found in README",
                file=sys.stderr,
            )
            return False

        # Create entry
        entry = f"- **PR #{pr_number} ({title})** → `{merge_log_filename}`\n"

        # Insert at top of section (after header)
        before, after = text.split(section_found, 1)

        # Find insertion point (after header and intro text)
        lines = after.split("\n")
        insert_idx = 0

        for i, line in enumerate(lines):
            if line.startswith("-") or line.startswith("**"):
                # First list item found
                insert_idx = i
                break
            elif line.strip() and not line.startswith("#"):
                # Intro text, skip
                continue
            elif i > 0 and line.strip() == "":
                # Empty line after intro
                insert_idx = i + 1

        # Insert entry
        lines.insert(insert_idx, entry)
        new_text = before + section_found + "\n".join(lines)

        readme_path.write_text(new_text, encoding="utf-8")
        print(f"[updated] {readme_path}")
        return True

    except (OSError, ValueError) as exc:
        print(f"[error] Failed to update README: {exc}", file=sys.stderr)
        return False


def main() -> int:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Generate gate-safe merge logs with GitHub CLI integration",
        epilog="Example: python new_merge_log.py --pr 450",
    )
    parser.add_argument(
        "--pr",
        type=int,
        required=True,
        help="PR number",
    )
    parser.add_argument(
        "--out",
        type=Path,
        help="Output path (default: docs/ops/PR_<NUM>_MERGE_LOG.md)",
    )
    parser.add_argument(
        "--update-readme",
        action="store_true",
        default=True,
        help="Update docs/ops/README.md (default: true)",
    )
    parser.add_argument(
        "--no-update-readme",
        dest="update_readme",
        action="store_false",
        help="Do not update README",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Overwrite existing file",
    )
    parser.add_argument(
        "--fallback",
        action="store_true",
        help="Use fallback mode (template with placeholders)",
    )

    args = parser.parse_args()

    # Determine repo root
    repo_root = Path(__file__).resolve().parents[2]

    # Determine output path
    if args.out:
        output_path = args.out
    else:
        output_path = repo_root / "docs" / "ops" / f"PR_{args.pr}_MERGE_LOG.md"

    # Check gh availability
    if not args.fallback and not check_gh_available():
        print(
            "[warning] gh CLI not available or not authenticated\n"
            "Install: https://cli.github.com/\n"
            "Authenticate: gh auth login\n"
            "Using fallback mode...\n",
            file=sys.stderr,
        )
        args.fallback = True

    # Fetch PR metadata (if not fallback)
    pr_data = None
    if not args.fallback:
        print(f"[fetch] PR #{args.pr} metadata via gh CLI...")
        pr_data = fetch_pr_metadata(args.pr)

        if not pr_data:
            print(
                f"[error] Failed to fetch PR #{args.pr} metadata\n"
                "Retrying with --fallback flag...\n",
                file=sys.stderr,
            )
            args.fallback = True

    # Generate content
    if args.fallback or not pr_data:
        # Fallback mode: template with placeholders
        content = generate_merge_log_content(
            pr_number=args.pr,
            title="[TODO: Add PR title]",
            pr_url=f"https://github.com/OWNER/REPO/pull/{args.pr}",
            merged_at=None,
            merge_commit=None,
            head_ref=None,
        )
        print("[fallback] Generated template with placeholders")
        print("Please fill in the TODO sections manually")
    else:
        # Use fetched data
        title = pr_data.get("title", "[TODO: Add PR title]")
        pr_url = pr_data.get("url", f"https://github.com/OWNER/REPO/pull/{args.pr}")
        merged_at = pr_data.get("mergedAt")
        merge_commit_data = pr_data.get("mergeCommit", {})
        merge_commit = merge_commit_data.get("oid") if merge_commit_data else None
        head_ref = pr_data.get("headRefName")

        content = generate_merge_log_content(
            pr_number=args.pr,
            title=title,
            pr_url=pr_url,
            merged_at=merged_at,
            merge_commit=merge_commit,
            head_ref=head_ref,
        )
        print(f"[generated] Merge log for PR #{args.pr}: {title}")

    # Write merge log
    if not write_merge_log(output_path, content, overwrite=args.overwrite):
        return 1

    # Update README (if requested)
    if args.update_readme and not args.fallback:
        readme_path = repo_root / "docs" / "ops" / "README.md"
        date_str = "YYYY-MM-DD"
        if pr_data and pr_data.get("mergedAt"):
            try:
                dt = datetime.fromisoformat(pr_data["mergedAt"].replace("Z", "+00:00"))
                date_str = dt.strftime("%Y-%m-%d")
            except (ValueError, AttributeError):
                pass

        title = pr_data.get("title", "TODO") if pr_data else "TODO"
        update_readme(
            readme_path,
            args.pr,
            title,
            date_str,
            output_path.name,
        )

    print(f"\n✅ Merge log created: {output_path}")
    if not args.fallback:
        print("✅ Ready for review and commit")
    else:
        print("⚠️  Fallback mode: Please fill in placeholder sections")

    return 0


if __name__ == "__main__":
    sys.exit(main())
