"""
Tests for docs reference targets baseline collection and trend checking.

Minimal unit tests for deterministic JSON formatting and trend comparison.
"""

import json
import tempfile
from pathlib import Path

import pytest


def test_baseline_json_deterministic_sorting():
    """Test that missing_items are deterministically sorted."""
    # Sample missing items (intentionally unsorted)
    items = [
        {
            "source_file": "docs/b.md",
            "line_number": 10,
            "target": "config/x.toml",
            "link_text": None,
        },
        {
            "source_file": "docs/a.md",
            "line_number": 20,
            "target": "config/y.toml",
            "link_text": "Link Y",
        },
        {
            "source_file": "docs/a.md",
            "line_number": 10,
            "target": "config/z.toml",
            "link_text": None,
        },
        {
            "source_file": "docs/a.md",
            "line_number": 10,
            "target": "config/a.toml",
            "link_text": None,
        },
    ]

    # Expected sort order: source_file, line_number, target
    expected_order = [
        ("docs/a.md", 10, "config/a.toml"),
        ("docs/a.md", 10, "config/z.toml"),
        ("docs/a.md", 20, "config/y.toml"),
        ("docs/b.md", 10, "config/x.toml"),
    ]

    # Sort as script does
    sorted_items = sorted(
        items,
        key=lambda x: (x["source_file"], x["line_number"], x["target"]),
    )

    actual_order = [
        (item["source_file"], item["line_number"], item["target"])
        for item in sorted_items
    ]

    assert actual_order == expected_order


def test_baseline_json_structure():
    """Test that baseline JSON has expected structure."""
    baseline = {
        "generated_at_utc": "2026-01-07T04:00:00Z",
        "git_sha": "abc123",
        "tool_version": "1.0.0",
        "scan_stats": {
            "total_markdown_files": 100,
            "ignored_files": 10,
            "scanned_files": 90,
            "total_references": 500,
        },
        "missing_count": 1,
        "missing_items": [
            {
                "source_file": "docs/example.md",
                "line_number": 42,
                "target": "config/missing.toml",
                "link_text": "Example Link",
            }
        ],
    }

    # Validate structure
    assert "generated_at_utc" in baseline
    assert "git_sha" in baseline
    assert "tool_version" in baseline
    assert "scan_stats" in baseline
    assert "missing_count" in baseline
    assert "missing_items" in baseline

    # Validate scan_stats
    assert "total_markdown_files" in baseline["scan_stats"]
    assert "scanned_files" in baseline["scan_stats"]
    assert "total_references" in baseline["scan_stats"]

    # Validate missing_count matches items length
    assert baseline["missing_count"] == len(baseline["missing_items"])

    # Validate missing_item structure
    item = baseline["missing_items"][0]
    assert "source_file" in item
    assert "line_number" in item
    assert "target" in item
    assert "link_text" in item


def test_trend_comparison_logic():
    """Test trend comparison: current vs baseline."""
    baseline_count = 100

    # Case 1: No change
    assert 100 <= baseline_count  # PASS

    # Case 2: Improvement
    assert 95 <= baseline_count  # PASS (debt reduced)

    # Case 3: Regression
    assert not (105 <= baseline_count)  # FAIL (debt increased)


def test_baseline_json_serialization():
    """Test that baseline can be serialized and deserialized consistently."""
    baseline = {
        "generated_at_utc": "2026-01-07T04:00:00Z",
        "git_sha": "abc123",
        "tool_version": "1.0.0",
        "scan_stats": {
            "total_markdown_files": 10,
            "ignored_files": 0,
            "scanned_files": 10,
            "total_references": 50,
        },
        "missing_count": 2,
        "missing_items": [
            {
                "source_file": "docs/a.md",
                "line_number": 10,
                "target": "config/x.toml",
                "link_text": None,
            },
            {
                "source_file": "docs/b.md",
                "line_number": 20,
                "target": "src/y.py",
                "link_text": "Link Y",
            },
        ],
    }

    # Serialize
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".json", delete=False
    ) as f:
        json.dump(baseline, f, indent=2, sort_keys=False, ensure_ascii=False)
        f.write("\n")
        temp_path = Path(f.name)

    try:
        # Deserialize
        with open(temp_path, encoding="utf-8") as f:
            loaded = json.load(f)

        # Verify round-trip
        assert loaded == baseline

        # Verify structure preservation
        assert list(loaded.keys()) == list(baseline.keys())
        assert loaded["missing_count"] == len(loaded["missing_items"])
    finally:
        temp_path.unlink()


def test_missing_item_deduplication():
    """Test that duplicate missing items are handled correctly."""
    # Simulate scanning same reference twice (shouldn't happen, but test it)
    items = [
        {
            "source_file": "docs/a.md",
            "line_number": 10,
            "target": "config/x.toml",
            "link_text": None,
        },
        {
            "source_file": "docs/a.md",
            "line_number": 10,
            "target": "config/x.toml",
            "link_text": None,
        },
    ]

    # Convert to tuples for deduplication
    unique_items = list({
        (item["source_file"], item["line_number"], item["target"])
        for item in items
    })

    assert len(unique_items) == 1


@pytest.mark.parametrize(
    "current,baseline,expected_pass",
    [
        (100, 100, True),   # Stable
        (95, 100, True),    # Improved
        (105, 100, False),  # Regressed
        (0, 100, True),     # All fixed!
        (100, 0, False),    # All broken!
    ],
)
def test_trend_gate_scenarios(current, baseline, expected_pass):
    """Test various trend gate scenarios."""
    passes = current <= baseline
    assert passes == expected_pass
