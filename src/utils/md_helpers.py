"""Markdown document manipulation helpers for Peak_Trade ops workflows."""

from __future__ import annotations

import pathlib
import re


def pick_first_existing(candidates: list[pathlib.Path]) -> pathlib.Path:
    """
    Returns the first existing Path from the given list.
    If none exist, returns the first candidate (will be created).

    Args:
        candidates: List of Path objects to check

    Returns:
        First existing path, or first candidate as fallback

    Example:
        >>> paths = [Path("new.md"), Path("existing.md")]
        >>> pick_first_existing(paths)  # returns existing.md if it exists
    """
    for p in candidates:
        if p.exists():
            return p
    # fallback target (will be created)
    return candidates[0]


def ensure_section_insert_at_top(
    path: pathlib.Path,
    section_h2: str,
    entry_md: str,
    signature: str,
) -> None:
    """
    Fügt einen Entry in eine Markdown-Datei unter einem H2-Header ein (an den Anfang der Section).
    Erstellt Datei/Ordner falls nicht vorhanden, verhindert Duplikate via signature.

    Args:
        path: Path to markdown file (will be created if doesn't exist)
        section_h2: H2 section name (without ##)
        entry_md: Markdown text to insert
        signature: Unique signature for duplicate prevention (e.g., "2025-12-20-PR195")

    Behavior:
        - Creates parent directories if needed
        - Creates file with default header if it doesn't exist
        - Creates section if it doesn't exist
        - Inserts entry at the top of the section
        - Skips insertion if signature is already present (duplicate prevention)

    Example:
        >>> ensure_section_insert_at_top(
        ...     path=Path("STATUS.md"),
        ...     section_h2="Recent Updates",
        ...     entry_md="### 2025-12-20 - Update\\n- Details",
        ...     signature="2025-12-20-update"
        ... )
        [insert] entry in STATUS.md
    """
    path.parent.mkdir(parents=True, exist_ok=True)

    if path.exists():
        text = path.read_text(encoding="utf-8")
    else:
        text = "# Peak_Trade Status Overview\n\n"

    if signature in text:
        print(f"[skip] already present in {path}")
        return

    h2 = f"## {section_h2}\n"
    if h2 not in text:
        if not text.endswith("\n"):
            text += "\n"
        text += f"\n{h2}\n"
        text += entry_md + ("" if entry_md.endswith("\n") else "\n")
        path.write_text(text, encoding="utf-8")
        print(f"[add] section + entry in {path}")
        return

    # Insert right after the section header
    before, after = text.split(h2, 1)
    insert = entry_md + ("" if entry_md.endswith("\n") else "\n")
    new_text = before + h2 + "\n" + insert + after.lstrip("\n")
    path.write_text(new_text, encoding="utf-8")
    print(f"[insert] entry in {path}")
