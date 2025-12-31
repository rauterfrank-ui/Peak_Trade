#!/usr/bin/env python3
"""
Hygiene-Check für Merge Logs.

Prüft auf:
- Verbotene lokale Pfade (/Users/, /home/, C:\, ~/)
- Unicode-Probleme (Control chars, Bidi, Zero-Width, BOM, Surrogates)

Usage:
    python check_merge_log_hygiene.py docs/ops/PR_*.md
    python check_merge_log_hygiene.py docs/ops/PR_450_MERGE_LOG.md
"""

from __future__ import annotations

import argparse
import sys
import unicodedata
from pathlib import Path


class Finding:
    """Represents a hygiene finding."""

    def __init__(
        self,
        file_path: Path,
        line: int,
        column: int,
        category: str,
        message: str,
        char: str | None = None,
    ):
        self.file_path = file_path
        self.line = line
        self.column = column
        self.category = category
        self.message = message
        self.char = char

    def __str__(self) -> str:
        loc = f"{self.file_path}:{self.line}:{self.column}"
        char_info = ""
        if self.char:
            code_point = f"U+{ord(self.char):04X}"
            char_info = f" [{code_point}]"
        return f"{loc} {self.category}: {self.message}{char_info}"


def check_forbidden_local_paths(
    file_path: Path,
    content: str,
) -> list[Finding]:
    """
    Prüft auf verbotene lokale Pfade.

    Args:
        file_path: Pfad zur Datei
        content: Dateiinhalt

    Returns:
        Liste von Findings
    """
    findings = []
    forbidden_patterns = [
        "/Users/",
        "/home/",
        "C:\\",
        "~/",
    ]

    lines = content.split("\n")
    for line_num, line in enumerate(lines, start=1):
        for pattern in forbidden_patterns:
            if pattern in line:
                col = line.find(pattern) + 1
                findings.append(
                    Finding(
                        file_path=file_path,
                        line=line_num,
                        column=col,
                        category="forbidden-path",
                        message=f"Contains forbidden local path pattern: {pattern}",
                    )
                )

    return findings


def check_unicode_hygiene(
    file_path: Path,
    content: str,
) -> list[Finding]:
    """
    Prüft Unicode-Hygiene.

    Erkennt:
    - Control chars (Cc) außer \\n, \\t, \\r
    - Format chars (Cf) - Bidi, Zero-Width, etc.
    - Surrogates (Cs)
    - BOM (U+FEFF)

    Args:
        file_path: Pfad zur Datei
        content: Dateiinhalt

    Returns:
        Liste von Findings
    """
    findings = []
    allowed_control = {"\n", "\t", "\r"}

    lines = content.split("\n")
    for line_num, line in enumerate(lines, start=1):
        for col, char in enumerate(line, start=1):
            category = unicodedata.category(char)
            char_name = unicodedata.name(char, "UNKNOWN")

            # Control characters (except allowed ones)
            if category == "Cc" and char not in allowed_control:
                findings.append(
                    Finding(
                        file_path=file_path,
                        line=line_num,
                        column=col,
                        category="control-char",
                        message=f"Control character: {char_name}",
                        char=char,
                    )
                )

            # Format characters (Bidi, Zero-Width, etc.)
            elif category == "Cf":
                findings.append(
                    Finding(
                        file_path=file_path,
                        line=line_num,
                        column=col,
                        category="format-char",
                        message=f"Format character: {char_name}",
                        char=char,
                    )
                )

            # Surrogates
            elif category == "Cs":
                findings.append(
                    Finding(
                        file_path=file_path,
                        line=line_num,
                        column=col,
                        category="surrogate",
                        message=f"Surrogate character: {char_name}",
                        char=char,
                    )
                )

    # Check for BOM at start of file
    if content and ord(content[0]) == 0xFEFF:
        findings.append(
            Finding(
                file_path=file_path,
                line=1,
                column=1,
                category="bom",
                message="File starts with BOM (Byte Order Mark)",
                char=content[0],
            )
        )

    return findings


def check_file(file_path: Path) -> list[Finding]:
    """
    Führt alle Checks auf einer Datei aus.

    Args:
        file_path: Pfad zur Datei

    Returns:
        Liste von Findings
    """
    try:
        content = file_path.read_text(encoding="utf-8", errors="replace")
    except OSError as exc:
        return [
            Finding(
                file_path=file_path,
                line=0,
                column=0,
                category="read-error",
                message=f"Failed to read file: {exc}",
            )
        ]

    findings = []
    findings.extend(check_forbidden_local_paths(file_path, content))
    findings.extend(check_unicode_hygiene(file_path, content))

    return findings


def main() -> int:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Check merge logs for hygiene issues",
        epilog="Example: python check_merge_log_hygiene.py docs/ops/PR_*.md",
    )
    parser.add_argument(
        "files",
        nargs="+",
        type=Path,
        help="Files or glob patterns to check",
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Verbose output",
    )

    args = parser.parse_args()

    # Expand globs and collect files
    files_to_check: list[Path] = []
    for pattern in args.files:
        if "*" in str(pattern) or "?" in str(pattern):
            # Glob pattern
            parent = pattern.parent if pattern.parent.exists() else Path(".")
            pattern_str = pattern.name
            matched = list(parent.glob(pattern_str))
            files_to_check.extend(matched)
        else:
            # Regular file
            if pattern.exists():
                files_to_check.append(pattern)
            else:
                print(
                    f"[warning] File not found: {pattern}",
                    file=sys.stderr,
                )

    if not files_to_check:
        print("[error] No files to check", file=sys.stderr)
        return 1

    # Check all files
    all_findings: list[Finding] = []
    for file_path in files_to_check:
        if args.verbose:
            print(f"[check] {file_path}")

        findings = check_file(file_path)
        all_findings.extend(findings)

    # Report findings
    if not all_findings:
        print(f"✅ All checks passed ({len(files_to_check)} files)")
        return 0

    # Group by category
    by_category: dict[str, list[Finding]] = {}
    for finding in all_findings:
        if finding.category not in by_category:
            by_category[finding.category] = []
        by_category[finding.category].append(finding)

    # Print summary
    print(f"\n❌ Found {len(all_findings)} issue(s) in {len(files_to_check)} file(s):\n")

    for category, findings in sorted(by_category.items()):
        print(f"\n{category.upper()} ({len(findings)}):")
        for finding in findings:
            print(f"  {finding}")

    print("\nPlease fix these issues before committing.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
