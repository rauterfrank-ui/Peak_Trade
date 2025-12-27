#!/usr/bin/env python3
"""
Unicode/BiDi Security Guard

Scans a file for suspicious Unicode characters that could be used for:
- Text direction manipulation (BiDi attacks)
- Hidden characters (zero-width, format controls)
- Control characters that shouldn't appear in text files

Exits with code 2 if suspicious characters are found, 0 otherwise.

Usage:
    python3 unicode_guard.py <filepath>
"""

import sys
import unicodedata
from pathlib import Path
from typing import List, Tuple


def scan_file(filepath: Path) -> List[Tuple[int, str, str, str]]:
    """
    Scan file for suspicious Unicode characters.

    Returns list of tuples: (char_index, char, unicode_code, unicode_name)
    """
    try:
        content = filepath.read_text(encoding="utf-8", errors="strict")
    except UnicodeDecodeError as e:
        print(f"ERROR: File is not valid UTF-8: {filepath}", file=sys.stderr)
        print(f"  {e}", file=sys.stderr)
        sys.exit(2)
    except FileNotFoundError:
        print(f"ERROR: File not found: {filepath}", file=sys.stderr)
        sys.exit(1)

    suspicious = []

    for i, ch in enumerate(content):
        cat = unicodedata.category(ch)
        cp = ord(ch)

        # Check for format control characters (Unicode category Cf)
        # This includes: BOM, ZWSP, BiDi controls, isolates, etc.
        if cat == "Cf":
            name = unicodedata.name(ch, "UNKNOWN")
            suspicious.append((i, ch, f"U+{cp:04X}", name))
            continue

        # Check for hard control characters (< 32) except newline, tab, carriage return
        if cp < 32 and ch not in ("\n", "\r", "\t"):
            suspicious.append((i, ch, f"U+{cp:04X}", f"CTRL({cp})"))

    return suspicious


def main():
    if len(sys.argv) != 2:
        print("Usage: unicode_guard.py <filepath>", file=sys.stderr)
        sys.exit(1)

    filepath = Path(sys.argv[1])

    suspicious = scan_file(filepath)

    if suspicious:
        print(
            f"ERROR: Found {len(suspicious)} suspicious Unicode character(s) in {filepath}",
            file=sys.stderr,
        )
        print("", file=sys.stderr)

        # Show first 200 occurrences
        for i, ch, code, name in suspicious[:200]:
            # Don't try to print the actual character (may be invisible/control)
            print(f"  idx={i:>6}  {code}  {name}", file=sys.stderr)

        if len(suspicious) > 200:
            print(f"  ... and {len(suspicious) - 200} more", file=sys.stderr)

        print("", file=sys.stderr)
        print("These characters could be used for:", file=sys.stderr)
        print("  - BiDi text direction manipulation attacks", file=sys.stderr)
        print("  - Hidden/invisible text", file=sys.stderr)
        print("  - GitHub security warnings", file=sys.stderr)
        sys.exit(2)

    print(f"✅ No suspicious Unicode characters found in {filepath}")
    sys.exit(0)


if __name__ == "__main__":
    main()
