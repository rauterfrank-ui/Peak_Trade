"""URI decoding finds original documents without weakening repository containment."""

from pathlib import Path

import pytest

from scripts.ops.collect_docs_reference_targets_fullscan import scan_docs
from src.ops.docs_reference_targets_common import (
    extract_targets_from_line,
    resolve_target,
    safe_is_within,
)


@pytest.mark.parametrize(
    ("literal", "actual"),
    [
        ("docs/SL%20OPT.json", "docs/SL OPT.json"),
        ("docs/Original%20Blueprint.pdf", "docs/Original Blueprint.pdf"),
        ("docs/%C3%9Cbersicht.md", "docs/Übersicht.md"),
        ("docs/literal%2520name.md", "docs/literal%20name.md"),
        ("docs/item%23identity.md", "docs/item#identity.md"),
        ("docs/plain.md", "docs/plain.md"),
    ],
)
def test_uri_targets_resolve_to_exact_existing_identity(tmp_path, literal, actual):
    file = tmp_path / actual
    file.parent.mkdir(parents=True, exist_ok=True)
    file.write_text("original\n")
    resolved = resolve_target(literal, tmp_path / "docs/index.md", tmp_path)
    assert resolved == file
    assert resolved.read_text() == "original\n"


def test_relative_base_is_selected_after_decoding(tmp_path):
    target = tmp_path / "docs/Source Note.md"
    target.parent.mkdir()
    target.write_text("source\n")
    assert (
        resolve_target("%2E%2E/Source%20Note.md", tmp_path / "docs/nested/index.md", tmp_path)
        == target
    )


def test_encoded_fragment_character_is_not_mistaken_for_heading(tmp_path):
    path = tmp_path / "docs/item#identity.md"
    path.parent.mkdir()
    path.write_text("original\n")
    targets = extract_targets_from_line("[record](./item%23identity.md#section)")
    assert targets == ["./item%23identity.md"]
    assert resolve_target(targets[0], tmp_path / "docs/index.md", tmp_path) == path


@pytest.mark.parametrize(
    "target", ["../repo-sibling/private.md", "%2E%2E/repo-sibling/private.md", "%00", "docs/%FF.md"]
)
def test_invalid_or_outside_targets_fail_closed(tmp_path, target):
    root = tmp_path / "repo"
    root.mkdir()
    sibling = tmp_path / "repo-sibling"
    sibling.mkdir()
    (sibling / "private.md").write_text("outside\n")
    assert resolve_target(target, root / "index.md", root) is None


def test_sibling_with_same_name_prefix_is_outside(tmp_path):
    root = tmp_path / "repo"
    root.mkdir()
    sibling = tmp_path / "repo-copy"
    sibling.mkdir()
    assert not safe_is_within(sibling, root)
    assert safe_is_within(root / "nested/file.md", root)


def test_symlink_cannot_escape_repository_after_decode(tmp_path):
    root = tmp_path / "repo"
    root.mkdir()
    outside = tmp_path / "repo-sibling"
    outside.mkdir()
    (outside / "Source Note.md").write_text("outside\n")
    (root / "alias").symlink_to(outside, target_is_directory=True)
    assert resolve_target("alias/Source%20Note.md", root / "index.md", root) is None


def test_double_encoding_is_decoded_exactly_once(tmp_path):
    path = tmp_path / "docs/literal%20name.md"
    path.parent.mkdir()
    path.write_text("percent identity\n")
    (path.parent / "literal name.md").write_text("different identity\n")
    assert resolve_target("docs/literal%2520name.md", path.parent / "index.md", tmp_path) == path


def test_full_scan_counts_only_missing_sources_and_keeps_all_references(tmp_path):
    docs = tmp_path / "docs"
    docs.mkdir()
    (docs / "SL OPT.json").write_text("{}\n")
    (docs / "Original Blueprint.pdf").write_bytes(b"test source")
    (docs / "index.md").write_text(
        "[learning](./SL%20OPT.json)\n"
        "[blueprint](./Original%20Blueprint.pdf)\n"
        "[missing](./missing.json)\n"
    )
    result = scan_docs(tmp_path)
    assert result["tool_version"] == "1.1.0"
    assert result["scan_stats"]["total_references"] == 3
    assert result["missing_count"] == 1
    assert result["missing_items"][0]["target"] == "./missing.json"
