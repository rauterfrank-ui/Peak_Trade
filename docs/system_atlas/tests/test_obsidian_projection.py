"""Obsidian source links and preservation boundaries, without writing a vault."""

import json
from pathlib import Path
from runpy import run_path

import pytest

ROOT = Path(__file__).resolve().parents[3]
N = run_path(str(ROOT / "docs/system_atlas/obsidian_projection.py"))


def test_repo_relative_links_resolve_to_source_or_current_vault_note():
    source = ROOT / "docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md"
    text = "[Core](../../../src/trading/master_v2/golden_geometry_engine_v1.py) [Map](../../governance/PEAK_TRADE_MAP_OF_TRUTH.md)"
    result = N["mirror_links"](text, source)
    assert (ROOT / "src/trading/master_v2/golden_geometry_engine_v1.py").as_uri() in result
    assert "[[00 Systemindex/Aktueller Repo-Stand/Map of Truth|Map]]" in result
    assert "../../../" not in result


def test_removed_repo_map_does_not_become_a_phantom_vault_note():
    rel = "docs/governance/feature_state_map_v1.md"
    text = "[[" + str(ROOT / rel) + "|Vorheriger Quellpfad]]"
    result, count = N["normalize_repo_wikilinks"](text, {rel})
    assert count == 1
    assert "Aktueller Atlas" in result
    assert "[[" + str(ROOT) not in result
    assert rel in result


def test_refresh_keeps_detailed_body_and_replaces_only_its_own_block():
    original = (
        "---\nstand: 2026-11-05\n---\n\n# Core\n\n## Zustandsdetails\nOriginaler Feldvertrag.\n"
    )
    block = "\n<!-- current-repo-projection:start -->\nAktueller Quellenstand.\n<!-- current-repo-projection:end -->\n"
    once = N["insert_current_block"](original, block)
    twice = N["insert_current_block"](once, block)
    assert once == twice
    assert "## Zustandsdetails\nOriginaler Feldvertrag." in twice
    assert "stand: 2026-11-05" in twice
    assert twice.count("<!-- current-repo-projection:start -->") == 1


def test_repository_cannot_be_used_as_a_vault():
    with pytest.raises(ValueError, match="EXISTING_EXTERNAL_VAULT_REQUIRED"):
        N["build"](ROOT)


def test_canvas_json_reformatting_is_reported_without_losing_value_binding():
    obj = {"nodes": [{"id": "title", "x": 0, "text": "Original"}], "edges": []}
    raw = json.dumps(obj, indent=2).encode()
    item = {
        "path": "Systemkarte.canvas",
        "sha256": N["digest"](raw),
        "json_sha256": N["json_content_digest"](raw),
    }
    assert N["verify_generated_file"](raw, item) is False
    reformatted = json.dumps(obj, sort_keys=True, separators=(",", ":")).encode()
    assert N["verify_generated_file"](reformatted, item) is True
    obj["nodes"][0]["x"] = 1
    with pytest.raises(ValueError, match="PROJECTION_CONTENT_CHANGED"):
        N["verify_generated_file"](json.dumps(obj).encode(), item)


def test_markdown_remains_byte_bound_even_if_json_digest_were_present():
    item = {
        "path": "Start.md",
        "sha256": N["digest"](b"Original"),
        "json_sha256": N["json_content_digest"](b"{}"),
    }
    with pytest.raises(ValueError, match="PROJECTION_CONTENT_CHANGED"):
        N["verify_generated_file"](b"{}", item)
