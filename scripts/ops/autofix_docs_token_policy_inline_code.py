#!/usr/bin/env python3
"""
Auto-fix docs token policy violations by encoding forward slashes in inline-code tokens.

Conservative strategy:
- Only modify inline-code tokens (single backticks: `token`)
- Replace / with &#47;
- Preserve URLs (http://, https://)
- Keep fenced code blocks unchanged
- Keep plain text unchanged

Usage:
    python scripts/ops/autofix_docs_token_policy_inline_code.py <file1.md> [file2.md ...] [--write]

    --write: Apply changes (default: dry-run)
"""

import re
import sys
from pathlib import Path


def fix_inline_code_tokens(content: str) -> tuple[str, int]:
    """
    Fix inline-code tokens by encoding forward slashes.

    Returns:
        (fixed_content, num_replacements)
    """
    replacements = 0

    # Pattern: Match inline code tokens (single backticks)
    # Exclude: Already encoded (&#47;), URLs (http://, https://), fenced code blocks

    def replace_slash_in_token(match):
        nonlocal replacements
        token = match.group(1)

        # Skip if already encoded
        if "&#47;" in token:
            return match.group(0)

        # Skip if it's a URL
        if token.startswith("http://") or token.startswith("https://"):
            return match.group(0)

        # Replace / with &#47;
        if "/" in token:
            fixed_token = token.replace("/", "&#47;")
            replacements += 1
            return f"`{fixed_token}`"

        return match.group(0)

    # Match inline code: `token` but not `` or ```
    # Negative lookbehind/lookahead to exclude fenced code blocks
    pattern = r"(?<!`)(`[^`\n]+?`)(?!`)"

    fixed_content = re.sub(pattern, replace_slash_in_token, content)

    return fixed_content, replacements


def process_file(file_path: Path, write: bool = False) -> tuple[int, bool]:
    """
    Process a single Markdown file.

    Returns:
        (num_replacements, success)
    """
    try:
        content = file_path.read_text(encoding="utf-8")
    except Exception as e:
        print(f"❌ Error reading {file_path}: {e}", file=sys.stderr)
        return 0, False

    fixed_content, num_replacements = fix_inline_code_tokens(content)

    if num_replacements == 0:
        print(f"✅ {file_path}: No changes needed")
        return 0, True

    if write:
        try:
            file_path.write_text(fixed_content, encoding="utf-8")
            print(f"✅ {file_path}: Fixed {num_replacements} token(s)")
        except Exception as e:
            print(f"❌ Error writing {file_path}: {e}", file=sys.stderr)
            return 0, False
    else:
        print(f"🔍 {file_path}: Would fix {num_replacements} token(s) (dry-run)")

    return num_replacements, True


def main():
    args = sys.argv[1:]
    write = False

    if "--write" in args:
        write = True
        args.remove("--write")

    if not args:
        print(__doc__)
        sys.exit(1)

    files = [Path(f) for f in args]

    # Validate all files exist
    for f in files:
        if not f.exists():
            print(f"❌ File not found: {f}", file=sys.stderr)
            sys.exit(1)
        if not f.suffix == ".md":
            print(f"⚠️  Warning: {f} is not a Markdown file", file=sys.stderr)

    print(f"{'🔧 WRITE MODE' if write else '🔍 DRY-RUN MODE'}")
    print(f"Processing {len(files)} file(s)...\n")

    total_replacements = 0
    success_count = 0

    for file_path in files:
        num_replacements, success = process_file(file_path, write)
        total_replacements += num_replacements
        if success:
            success_count += 1

    print(f"\n{'=' * 60}")
    print(f"Total replacements: {total_replacements}")
    print(f"Files processed: {success_count}/{len(files)}")

    if not write and total_replacements > 0:
        print(f"\n💡 Run with --write to apply changes")

    sys.exit(0 if success_count == len(files) else 1)


if __name__ == "__main__":
    main()
