#!/usr/bin/env python3
"""
Unit tests for TODO board encoding robustness.
Tests read_text_smart() function with various encodings.
"""
import sys
import tempfile
import unicodedata
from pathlib import Path

# Add scripts directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from build_todo_board_html import read_text_smart


def test_read_text_smart_utf16le():
    """Test read_text_smart with UTF-16LE encoded file."""
    # Content with em-dash (U+2014) and German umlaut
    content = "Sortino-Ratio ergänzen — Kurzfristig (1–3 Sessions)"

    with tempfile.NamedTemporaryFile(mode='wb', suffix='.md', delete=False) as f:
        temp_path = Path(f.name)
        # Write as UTF-16LE with BOM
        f.write(b'\xff\xfe')  # BOM for UTF-16LE
        f.write(content.encode('utf-16le'))

    try:
        result = read_text_smart(temp_path)

        # Assert content is correctly decoded
        assert "ergänzen" in result, f"Expected 'ergänzen' in result, got: {result!r}"
        assert "1–3" in result, f"Expected '1–3' in result, got: {result!r}"
        assert "Sortino-Ratio" in result
        assert "Kurzfristig" in result

        # Ensure no BOM, replacement characters or control chars
        assert "\ufeff" not in result, "BOM should be removed"
        assert "\ufffd" not in result, "Found replacement character in result"
        assert "\x13" not in result, "Found DC3 control character in result"

        # Verify no other control characters (except \n and \t)
        for ch in result:
            cat = unicodedata.category(ch)
            if cat == "Cc" and ch not in ("\n", "\t"):
                raise AssertionError(f"Found unwanted control character: {ch!r} (U+{ord(ch):04X})")

        print(f"✅ UTF-16LE test passed: {result!r}")

    finally:
        temp_path.unlink()


def test_read_text_smart_utf16be():
    """Test read_text_smart with UTF-16BE encoded file."""
    content = "Test — with em-dash and ä ö ü"

    with tempfile.NamedTemporaryFile(mode='wb', suffix='.md', delete=False) as f:
        temp_path = Path(f.name)
        # Write as UTF-16BE with BOM
        f.write(b'\xfe\xff')  # BOM for UTF-16BE
        f.write(content.encode('utf-16be'))

    try:
        result = read_text_smart(temp_path)

        assert "em-dash" in result
        assert "ä ö ü" in result
        assert "\ufeff" not in result, "BOM should be removed"
        assert "\ufffd" not in result

        print(f"✅ UTF-16BE test passed: {result!r}")

    finally:
        temp_path.unlink()


def test_read_text_smart_utf8():
    """Test read_text_smart with UTF-8 encoded file (normal case)."""
    content = "Standard UTF-8 — mit Umlauten: äöü ÄÖÜ ß"

    with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8', suffix='.md', delete=False) as f:
        temp_path = Path(f.name)
        f.write(content)

    try:
        result = read_text_smart(temp_path)

        assert result == content
        assert "äöü" in result
        assert "ÄÖÜ" in result

        print(f"✅ UTF-8 test passed: {result!r}")

    finally:
        temp_path.unlink()


def test_read_text_smart_control_char_removal():
    """Test that control characters (except \\n and \\t) are removed."""
    # Create content with DC3 (0x13) and other control chars
    content = "Normal text\nwith newline\tand tab\x13DC3 should be removed\x01SOH too"

    with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8', suffix='.md', delete=False) as f:
        temp_path = Path(f.name)
        f.write(content)

    try:
        result = read_text_smart(temp_path)

        # \n and \t should be preserved
        assert "\n" in result
        assert "\t" in result

        # Control chars should be removed
        assert "\x13" not in result, "DC3 should be removed"
        assert "\x01" not in result, "SOH should be removed"

        # Text should still be there
        assert "Normal text" in result
        assert "DC3 should be removed" in result

        print(f"✅ Control char removal test passed: {result!r}")

    finally:
        temp_path.unlink()


def test_read_text_smart_no_bom_with_nul_bytes():
    """Test heuristic detection of UTF-16LE without BOM (using NUL byte pattern)."""
    content = "ASCII text with — em-dash"

    with tempfile.NamedTemporaryFile(mode='wb', suffix='.md', delete=False) as f:
        temp_path = Path(f.name)
        # Write as UTF-16LE without BOM
        f.write(content.encode('utf-16le'))

    try:
        result = read_text_smart(temp_path)

        # Should detect UTF-16LE via NUL byte heuristic
        assert "ASCII text" in result
        assert "em-dash" in result
        assert "\x00" not in result, "Should not have NUL bytes in decoded text"

        print(f"✅ UTF-16LE (no BOM) heuristic test passed: {result!r}")

    finally:
        temp_path.unlink()


if __name__ == "__main__":
    print("Running TODO board encoding tests...\n")

    test_read_text_smart_utf16le()
    test_read_text_smart_utf16be()
    test_read_text_smart_utf8()
    test_read_text_smart_control_char_removal()
    test_read_text_smart_no_bom_with_nul_bytes()

    print("\n✅ All tests passed!")
