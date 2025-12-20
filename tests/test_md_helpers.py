"""Tests for markdown helper utilities (src.utils.md_helpers)."""

from __future__ import annotations

import pathlib

import pytest

from src.utils.md_helpers import ensure_section_insert_at_top, pick_first_existing


class TestPickFirstExisting:
    """Tests for pick_first_existing() function."""

    def test_returns_first_when_exists(self, tmp_path: pathlib.Path) -> None:
        """When candidate[0] exists, return candidate[0]."""
        file1 = tmp_path / "first.txt"
        file2 = tmp_path / "second.txt"
        file1.write_text("content")

        result = pick_first_existing([file1, file2])

        assert result == file1

    def test_returns_second_when_first_missing(self, tmp_path: pathlib.Path) -> None:
        """When candidate[0] doesn't exist but candidate[1] does, return candidate[1]."""
        file1 = tmp_path / "missing.txt"
        file2 = tmp_path / "existing.txt"
        file2.write_text("content")

        result = pick_first_existing([file1, file2])

        assert result == file2

    def test_returns_first_as_fallback_when_none_exist(
        self, tmp_path: pathlib.Path
    ) -> None:
        """When no candidates exist, return candidate[0] as fallback."""
        file1 = tmp_path / "missing1.txt"
        file2 = tmp_path / "missing2.txt"

        result = pick_first_existing([file1, file2])

        assert result == file1
        # Verify it was not created
        assert not result.exists()

    def test_works_with_single_candidate(self, tmp_path: pathlib.Path) -> None:
        """Works correctly with a single candidate."""
        file1 = tmp_path / "single.txt"
        file1.write_text("content")

        result = pick_first_existing([file1])

        assert result == file1

    def test_checks_in_order(self, tmp_path: pathlib.Path) -> None:
        """Checks candidates in order, returns first existing."""
        file1 = tmp_path / "first.txt"
        file2 = tmp_path / "second.txt"
        file3 = tmp_path / "third.txt"

        # Only second exists
        file2.write_text("content")

        result = pick_first_existing([file1, file2, file3])

        assert result == file2


class TestEnsureSectionInsertAtTop:
    """Tests for ensure_section_insert_at_top() function."""

    def test_creates_file_and_parent_dir_when_missing(
        self, tmp_path: pathlib.Path
    ) -> None:
        """File and parent directories are created when they don't exist."""
        nested_path = tmp_path / "sub" / "deep" / "doc.md"
        entry = "### Entry 1\n- Detail A"
        signature = "sig-001"

        ensure_section_insert_at_top(nested_path, "Updates", entry, signature)

        assert nested_path.exists()
        assert nested_path.parent.exists()

    def test_creates_file_with_section_and_entry_when_new(
        self, tmp_path: pathlib.Path
    ) -> None:
        """When file doesn't exist, creates it with header, section, and entry."""
        doc_path = tmp_path / "doc.md"
        signature = "2025-12-20-PR195"
        entry = f"### 2025-12-20 - PR #195 ({signature})\n- Error taxonomy hardening"

        ensure_section_insert_at_top(doc_path, "Recent Updates", entry, signature)

        content = doc_path.read_text(encoding="utf-8")
        assert "# Peak_Trade Status Overview" in content
        assert "## Recent Updates\n" in content
        assert entry in content
        assert signature in content

    def test_creates_section_when_missing_in_existing_file(
        self, tmp_path: pathlib.Path
    ) -> None:
        """When file exists but section doesn't, section is created and entry inserted."""
        doc_path = tmp_path / "doc.md"
        doc_path.write_text("# My Doc\n\n## Other Section\nSome content\n")

        entry = "### New Entry\n- Detail"
        signature = "sig-new"

        ensure_section_insert_at_top(doc_path, "Updates", entry, signature)

        content = doc_path.read_text(encoding="utf-8")
        assert "## Updates\n" in content
        assert entry in content
        assert "## Other Section" in content  # Original content preserved

    def test_inserts_entry_at_top_of_existing_section(
        self, tmp_path: pathlib.Path
    ) -> None:
        """When section exists, entry is inserted at the top (right after header)."""
        doc_path = tmp_path / "doc.md"
        initial = "# Doc\n\n## Updates\n\n### Old Entry\n- Old detail\n"
        doc_path.write_text(initial)

        entry = "### New Entry\n- New detail"
        signature = "sig-new"

        ensure_section_insert_at_top(doc_path, "Updates", entry, signature)

        content = doc_path.read_text(encoding="utf-8")

        # New entry should appear before old entry
        new_idx = content.index("### New Entry")
        old_idx = content.index("### Old Entry")
        assert new_idx < old_idx

    def test_prevents_duplicate_insertion_via_signature(
        self, tmp_path: pathlib.Path, capsys
    ) -> None:
        """When signature is already present, no insertion happens (duplicate prevention)."""
        doc_path = tmp_path / "doc.md"
        signature = "unique-sig-123"
        entry = f"### Entry 1 ({signature})\n- Detail"

        # First insertion
        ensure_section_insert_at_top(doc_path, "Updates", entry, signature)
        content_after_first = doc_path.read_text(encoding="utf-8")

        # Second insertion with same signature (should be skipped)
        ensure_section_insert_at_top(doc_path, "Updates", entry, signature)
        content_after_second = doc_path.read_text(encoding="utf-8")

        # Content should be identical
        assert content_after_first == content_after_second

        # Check console output
        captured = capsys.readouterr()
        assert "[skip] already present" in captured.out

    def test_handles_entry_with_trailing_newline(self, tmp_path: pathlib.Path) -> None:
        """Entry with trailing newline is handled correctly."""
        doc_path = tmp_path / "doc.md"
        # Pre-create file with existing content to avoid triple newline from header
        doc_path.write_text("# Doc\n\n## Updates\n\nExisting entry\n")
        
        signature = "sig-1"
        entry_with_newline = f"### New Entry ({signature})\n- Detail\n"

        ensure_section_insert_at_top(doc_path, "Updates", entry_with_newline, signature)

        content = doc_path.read_text(encoding="utf-8")

        # Should not have excessive newlines between entries
        assert "\n\n\n\n" not in content

    def test_handles_entry_without_trailing_newline(
        self, tmp_path: pathlib.Path
    ) -> None:
        """Entry without trailing newline gets one added."""
        doc_path = tmp_path / "doc.md"
        entry_no_newline = "### Entry\n- Detail"
        signature = "sig-2"

        ensure_section_insert_at_top(doc_path, "Updates", entry_no_newline, signature)

        content = doc_path.read_text(encoding="utf-8")

        # Should end with single newline
        assert content.endswith("\n")
        assert not content.endswith("\n\n")

    def test_preserves_content_in_other_sections(self, tmp_path: pathlib.Path) -> None:
        """Content in other sections is preserved unchanged."""
        doc_path = tmp_path / "doc.md"
        initial = (
            "# Doc\n\n"
            "## Section A\n"
            "Content A1\n"
            "Content A2\n\n"
            "## Section B\n"
            "Content B1\n"
        )
        doc_path.write_text(initial)

        entry = "### New in A"
        signature = "sig-a"

        ensure_section_insert_at_top(doc_path, "Section A", entry, signature)

        content = doc_path.read_text(encoding="utf-8")

        # Section B should be unchanged
        assert "## Section B\n" in content
        assert "Content B1" in content

        # Section A should have new entry
        assert "### New in A" in content
        assert "Content A1" in content

    def test_works_with_multiple_sections(self, tmp_path: pathlib.Path) -> None:
        """Can insert into different sections in the same file."""
        doc_path = tmp_path / "doc.md"
        doc_path.write_text("# Doc\n\n")

        # Insert into Section A
        ensure_section_insert_at_top(doc_path, "Section A", "Entry A1", "sig-a1")

        # Insert into Section B
        ensure_section_insert_at_top(doc_path, "Section B", "Entry B1", "sig-b1")

        # Insert another into Section A (should be at top)
        ensure_section_insert_at_top(doc_path, "Section A", "Entry A2", "sig-a2")

        content = doc_path.read_text(encoding="utf-8")

        # Both sections exist
        assert "## Section A\n" in content
        assert "## Section B\n" in content

        # Entry A2 appears before Entry A1 (inserted at top)
        a2_idx = content.index("Entry A2")
        a1_idx = content.index("Entry A1")
        assert a2_idx < a1_idx

    def test_console_output_messages(
        self, tmp_path: pathlib.Path, capsys
    ) -> None:
        """Correct console messages are printed for different scenarios."""
        doc_path = tmp_path / "doc.md"

        # Case 1: New file + section
        ensure_section_insert_at_top(doc_path, "Updates", "Entry 1 (sig-1)", "sig-1")
        captured = capsys.readouterr()
        assert "[add] section + entry" in captured.out

        # Case 2: Existing file, new entry in existing section
        ensure_section_insert_at_top(doc_path, "Updates", "Entry 2 (sig-2)", "sig-2")
        captured = capsys.readouterr()
        assert "[insert] entry" in captured.out

        # Case 3: Duplicate (signature exists)
        ensure_section_insert_at_top(doc_path, "Updates", "Entry 2 (sig-2)", "sig-2")
        captured = capsys.readouterr()
        assert "[skip] already present" in captured.out

    def test_signature_can_be_anywhere_in_file(self, tmp_path: pathlib.Path) -> None:
        """Signature detection works regardless of where it appears in file."""
        doc_path = tmp_path / "doc.md"
        doc_path.write_text("# Doc\n\nSome text with unique-marker-xyz embedded\n")

        entry = "### Entry"
        signature = "unique-marker-xyz"

        ensure_section_insert_at_top(doc_path, "Updates", entry, signature)

        # Should skip because signature is already in file
        content = doc_path.read_text(encoding="utf-8")
        assert content.count("unique-marker-xyz") == 1  # Still only once

    def test_real_world_pr_merge_scenario(self, tmp_path: pathlib.Path) -> None:
        """Simulates real-world PR merge log scenario."""
        status_doc = tmp_path / "STATUS.md"

        pr195_entry = (
            "### 2025-12-20 — PR #195 merged (da64f05) — Error Taxonomy Hardening\n"
            "- ✅ README: Error-Handling Quick Usage Guide\n"
            "- ✅ docs/ops: Merge-Logs hinzugefügt\n"
            "- CI: lint ✅ | tests ✅\n"
        )
        signature_195 = "2025-12-20-PR195"

        # First PR
        ensure_section_insert_at_top(
            status_doc, "Recent Merges", pr195_entry, signature_195
        )

        # Simulate another PR
        pr196_entry = (
            "### 2025-12-21 — PR #196 merged (abc1234) — Fix Bug\n"
            "- ✅ Fixed critical bug\n"
        )
        signature_196 = "2025-12-21-PR196"

        ensure_section_insert_at_top(
            status_doc, "Recent Merges", pr196_entry, signature_196
        )

        content = status_doc.read_text(encoding="utf-8")

        # Both PRs present
        assert "PR #195" in content
        assert "PR #196" in content

        # PR #196 appears first (more recent, inserted at top)
        pr196_idx = content.index("PR #196")
        pr195_idx = content.index("PR #195")
        assert pr196_idx < pr195_idx

