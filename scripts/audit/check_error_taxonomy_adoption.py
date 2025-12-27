#!/usr/bin/env python3
"""
Error Taxonomy Adoption Audit

Scans src/ for legacy error patterns that should be migrated to the new taxonomy:
- raise Exception(...) or raise RuntimeError(...)
- except Exception: (catch-all)

Usage:
    python scripts/audit/check_error_taxonomy_adoption.py

Exit Codes:
    0 - No violations found
    2 - Violations found (needs attention)
"""

import sys
from pathlib import Path
from typing import List, Tuple

# ============================================================================
# ALLOWLIST: Files/patterns to skip (false positives, intentional usage)
# ============================================================================
ALLOWLIST = {
    # Example: "src/core/errors.py",  # Base error classes
    # Example: "src/legacy/old_module.py",  # Scheduled for removal
}

# ============================================================================
# Configuration
# ============================================================================
SRC_ROOT = Path(__file__).parent.parent.parent / "src"
EXCLUDE_DIRS = {"__pycache__", ".venv", "tests", "docs", ".git"}

# Patterns to detect
PATTERNS = {
    "raise_exception": "raise Exception(",
    "raise_runtime": "raise RuntimeError(",
    "catch_all": "except Exception:",
}


# ============================================================================
# Core Logic
# ============================================================================
def should_skip(file_path: Path) -> bool:
    """Check if file should be skipped (allowlist or excluded dir)."""
    # Check allowlist
    relative_path = file_path.relative_to(Path.cwd())
    if str(relative_path) in ALLOWLIST:
        return True

    # Check excluded directories
    for part in file_path.parts:
        if part in EXCLUDE_DIRS:
            return True

    return False


def scan_file(file_path: Path) -> List[Tuple[int, str, str]]:
    """
    Scan a single file for error pattern violations.

    Returns:
        List of (line_number, pattern_type, line_content)
    """
    violations = []

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            for line_num, line in enumerate(f, start=1):
                line_stripped = line.strip()

                # Skip comments and empty lines
                if not line_stripped or line_stripped.startswith("#"):
                    continue

                # Check each pattern
                for pattern_name, pattern_text in PATTERNS.items():
                    if pattern_text in line:
                        violations.append((line_num, pattern_name, line_stripped))

    except (UnicodeDecodeError, PermissionError) as e:
        print(f"⚠️  Warning: Could not read {file_path}: {e}", file=sys.stderr)

    return violations


def scan_directory(root_dir: Path) -> dict:
    """
    Recursively scan directory for Python files with violations.

    Returns:
        Dict mapping file paths to list of violations
    """
    results = {}

    for py_file in root_dir.rglob("*.py"):
        if should_skip(py_file):
            continue

        violations = scan_file(py_file)
        if violations:
            results[py_file] = violations

    return results


def format_report(results: dict) -> str:
    """Format scan results into readable report."""
    if not results:
        return "✅ No error taxonomy violations found!"

    lines = []
    lines.append("=" * 80)
    lines.append("ERROR TAXONOMY ADOPTION AUDIT")
    lines.append("=" * 80)
    lines.append("")

    total_violations = sum(len(v) for v in results.values())
    lines.append(f"Found {total_violations} violation(s) in {len(results)} file(s)")
    lines.append("")

    # Group by pattern type
    pattern_counts = {}
    for violations in results.values():
        for _, pattern_type, _ in violations:
            pattern_counts[pattern_type] = pattern_counts.get(pattern_type, 0) + 1

    lines.append("Violations by type:")
    for pattern_name, count in sorted(pattern_counts.items()):
        lines.append(f"  - {pattern_name}: {count}")
    lines.append("")
    lines.append("-" * 80)
    lines.append("")

    # Detail each file
    for file_path in sorted(results.keys()):
        violations = results[file_path]
        relative_path = file_path.relative_to(Path.cwd())

        lines.append(f"📄 {relative_path}")
        lines.append("")

        for line_num, pattern_type, line_content in violations:
            # Truncate long lines
            if len(line_content) > 80:
                line_content = line_content[:77] + "..."

            lines.append(f"  Line {line_num:4d} [{pattern_type}]")
            lines.append(f"    {line_content}")
            lines.append("")

        lines.append("")

    lines.append("-" * 80)
    lines.append("")
    lines.append("Recommendations:")
    lines.append("")
    lines.append("1. raise Exception(...) → Use specific error from src.core.errors")
    lines.append("   Example: raise DataContractError('message', hint='...', context={...})")
    lines.append("")
    lines.append("2. except Exception: → Catch specific exceptions")
    lines.append("   Example: except (DataContractError, ConfigError) as e:")
    lines.append("")
    lines.append("3. If intentional, add to ALLOWLIST in this script")
    lines.append("")
    lines.append("See docs/ERROR_HANDLING_GUIDE.md for full migration guide.")
    lines.append("")
    lines.append("=" * 80)

    return "\n".join(lines)


def main() -> int:
    """Main entry point."""
    print("🔍 Scanning for error taxonomy violations...")
    print(f"   Root: {SRC_ROOT}")
    print(f"   Excluding: {', '.join(sorted(EXCLUDE_DIRS))}")
    print("")

    if not SRC_ROOT.exists():
        print(f"❌ Error: Source directory not found: {SRC_ROOT}", file=sys.stderr)
        return 1

    results = scan_directory(SRC_ROOT)
    report = format_report(results)

    print(report)

    # Exit code: 0 if clean, 2 if violations found
    return 2 if results else 0


if __name__ == "__main__":
    sys.exit(main())
