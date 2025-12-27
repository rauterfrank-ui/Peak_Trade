#!/usr/bin/env python3
from __future__ import annotations
import argparse
import re
from pathlib import Path


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("pr_num", type=int)
    ap.add_argument("merge_log_path")
    ap.add_argument("--readme", required=True)
    args = ap.parse_args()

    readme = Path(args.readme)
    text = readme.read_text(encoding="utf-8")

    pr = args.pr_num
    entry = f"- PR #{pr} – Merge Log: `{args.merge_log_path}`\n"

    header = "## Merge Logs (Ops)"
    if header not in text:
        # Append section deterministically
        if not text.endswith("\n"):
            text += "\n"
        text += f"\n{header}\n\n{entry}"
        readme.write_text(text, encoding="utf-8")
        return 0

    # Split into lines for controlled insertion
    lines = text.splitlines(keepends=True)
    # Find header line index
    h_idx = next(i for i, l in enumerate(lines) if l.strip() == header)

    # Define section range: from header to next '## ' or EOF
    sec_start = h_idx + 1
    sec_end = len(lines)
    for i in range(sec_start, len(lines)):
        if lines[i].startswith("## ") and i != h_idx:
            sec_end = i
            break

    section = "".join(lines[sec_start:sec_end])

    # Remove existing entry for PR (any variant)
    pr_re = re.compile(rf"^- PR #{pr}\s+–\s+Merge Log:\s+`[^`]+`\s*$", re.MULTILINE)
    section_new = pr_re.sub("", section).strip("\n")

    # Ensure exactly one blank line after header
    prefix = "".join(lines[:sec_start])
    suffix = "".join(lines[sec_end:])

    # Rebuild section with entry appended at end (keeps bullets grouped)
    if section_new.strip():
        if not section_new.endswith("\n"):
            section_new += "\n"
        section_new += entry
    else:
        section_new = "\n" + entry

    # Normalize: collapse >2 blank lines inside this section
    section_new = re.sub(r"\n{3,}", "\n\n", section_new)

    new_text = prefix + section_new + suffix
    readme.write_text(new_text, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
