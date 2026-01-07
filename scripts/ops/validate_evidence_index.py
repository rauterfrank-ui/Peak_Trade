#!/usr/bin/env python3
"""
Peak_Trade – Evidence Index Validator (v0.2)

Purpose: Validate EVIDENCE_INDEX.md structure and references.
Owner: ops
Status: Operational

Usage:
    python scripts/ops/validate_evidence_index.py [--index-path docs/ops/EVIDENCE_INDEX.md]

Exit Codes:
    0 = Validation passed
    2 = Validation errors found
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

# Schema: Valid categories (case-insensitive)
VALID_CATEGORIES = {
    "ci/workflow",
    "ci / workflow",
    "drill/operator",
    "drill / operator",
    "test/refactor",
    "test / refactor",
    "incident/rca",
    "incident / rca",
    "config snapshot",
}

# Evidence ID pattern: EV-YYYYMMDD-<TAG>
EVIDENCE_ID_PATTERN = re.compile(r"^EV-\d{8}-[A-Z0-9\-]{2,20}$")

# Date pattern: YYYY-MM-DD
DATE_PATTERN = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def validate_evidence_id(evidence_id: str) -> list:
    """Validate Evidence ID format."""
    errors = []
    if not EVIDENCE_ID_PATTERN.match(evidence_id):
        errors.append(
            f"Invalid Evidence ID format: {evidence_id} "
            f"(expected: EV-YYYYMMDD-<TAG>, TAG=2-20 uppercase alphanumeric/hyphens)"
        )
    return errors


def validate_date(date_str: str) -> list:
    """Validate date format."""
    errors = []
    if not DATE_PATTERN.match(date_str):
        errors.append(f"Invalid date format: {date_str} (expected: YYYY-MM-DD)")
    return errors


def validate_category(category: str) -> list:
    """Validate category against schema."""
    errors = []
    normalized = category.lower().strip()
    if normalized not in VALID_CATEGORIES:
        errors.append(
            f"Invalid category: '{category}' "
            f"(valid: CI/Workflow, Drill/Operator, Test/Refactor, Incident/RCA, Config Snapshot)"
        )
    return errors


def extract_file_path_from_markdown_link(link: str) -> str | None:
    """Extract file path from markdown link [text](path)."""
    match = re.search(r"\[.*?\]\(([^)]+)\)", link)
    if match:
        path = match.group(1)
        # Skip URLs (http://, https://, mailto:)
        if not path.startswith(("http://", "https://", "mailto:", "#")):
            return path
    return None


def validate_index_file(index_path: Path, repo_root: Path) -> tuple:
    """
    Validate EVIDENCE_INDEX.md structure.

    Returns:
        (error_count, error_messages)
    """
    errors = []

    if not index_path.exists():
        errors.append(f"Evidence Index not found: {index_path}")
        return len(errors), errors

    content = index_path.read_text(encoding="utf-8")
    lines = content.splitlines()

    # Find table start (line with "| Evidence ID |")
    table_start_idx = None
    for i, line in enumerate(lines):
        if line.strip().startswith("| Evidence ID |"):
            table_start_idx = i
            break

    if table_start_idx is None:
        errors.append("Evidence Index table not found (missing '| Evidence ID |' header)")
        return len(errors), errors

    # Parse table rows (skip header and separator)
    table_rows = []
    for i in range(table_start_idx + 2, len(lines)):
        line = lines[i].strip()
        if not line.startswith("|"):
            break  # End of table
        table_rows.append(line)

    if not table_rows:
        errors.append("Evidence Index table is empty (no entries found)")
        return len(errors), errors

    # Track unique IDs
    seen_ids = set()

    # Validate each row
    for row_idx, row in enumerate(table_rows, start=1):
        cells = [cell.strip() for cell in row.split("|")[1:-1]]  # Remove leading/trailing empty cells

        if len(cells) < 7:
            errors.append(f"Row {row_idx}: Incomplete row (expected 7 columns, got {len(cells)})")
            continue

        evidence_id = cells[0].strip()
        date = cells[1].strip()
        owner = cells[2].strip()
        source_link = cells[3].strip()
        claim = cells[4].strip()
        verification = cells[5].strip()
        notes = cells[6].strip()

        # Validate Evidence ID
        errors.extend([f"Row {row_idx}: {err}" for err in validate_evidence_id(evidence_id)])

        # Check ID uniqueness
        if evidence_id in seen_ids:
            errors.append(f"Row {row_idx}: Duplicate Evidence ID: {evidence_id}")
        seen_ids.add(evidence_id)

        # Validate Date
        errors.extend([f"Row {row_idx}: {err}" for err in validate_date(date)])

        # Validate mandatory fields (non-empty)
        if not owner:
            errors.append(f"Row {row_idx} ({evidence_id}): Owner field is empty")
        if not source_link:
            errors.append(f"Row {row_idx} ({evidence_id}): Source Link field is empty")
        if not claim:
            errors.append(f"Row {row_idx} ({evidence_id}): Claim field is empty")
        if not verification:
            errors.append(f"Row {row_idx} ({evidence_id}): Verification field is empty")

        # Validate file paths (best effort)
        file_path = extract_file_path_from_markdown_link(source_link)
        if file_path:
            # Resolve relative to docs/ops/
            full_path = (repo_root / "docs" / "ops" / file_path).resolve()
            if not full_path.exists():
                errors.append(
                    f"Row {row_idx} ({evidence_id}): Referenced file not found: {file_path}"
                )

    # Validate category sections (optional: check if category sections exist)
    category_section_found = False
    for line in lines:
        if line.startswith("### ") and any(cat in line.lower() for cat in VALID_CATEGORIES):
            category_section_found = True
            break

    if not category_section_found:
        errors.append("Warning: No category sections found (e.g., '### CI / Workflow Evidence')")

    return len(errors), errors


def main():
    parser = argparse.ArgumentParser(
        description="Validate Evidence Index structure and references",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    parser.add_argument(
        "--index-path",
        type=str,
        default="docs/ops/EVIDENCE_INDEX.md",
        help="Path to EVIDENCE_INDEX.md (relative to repo root). Default: docs/ops/EVIDENCE_INDEX.md",
    )

    args = parser.parse_args()

    # Determine repo root (assume script is in scripts/ops/)
    script_path = Path(__file__).resolve()
    repo_root = script_path.parent.parent.parent

    index_path = repo_root / args.index_path

    print(f"🔍 Validating Evidence Index: {index_path}")
    print(f"   Repo root: {repo_root}")
    print()

    error_count, errors = validate_index_file(index_path, repo_root)

    if error_count == 0:
        print("✅ Validation passed: Evidence Index is valid")
        sys.exit(0)
    else:
        print(f"❌ Validation failed: {error_count} error(s) found")
        print()
        for error in errors:
            print(f"  - {error}")
        sys.exit(2)


if __name__ == "__main__":
    main()
