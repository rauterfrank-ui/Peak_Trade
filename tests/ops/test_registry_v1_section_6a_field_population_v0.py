"""Contract tests for Registry v1 taxonomy §6a field population v0."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from tests.fixtures.ops.generic_evidence_run_registry_v1 import projection_consumer_v0 as pc

ROOT = pc.REPO_ROOT
REGISTRY_SCRIPT = pc.REGISTRY_SCRIPT
TAXONOMY_SPEC = (
    ROOT / "docs" / "ops" / "specs" / "RUNTIME_LANE_TAXONOMY_AUTHORITY_LEVELS_CONTRACT_V0.md"
)

SECTION_6A_FIELDS = pc.SECTION_6A_METADATA_FIELDS
RUN_ID = pc.DEFAULT_COMPOSITION_RUN_ID

_write_lane = pc.write_lane
_write_composition = pc.write_composition


def _load_registry():
    return pc.load_registry_module(module_name="build_generic_evidence_run_registry_v1_section_6a")


def _build(mod, archive: Path) -> dict:
    return mod.build_registry(mod.BuildContext(archive_root=archive, repo_root=ROOT))


@pytest.fixture
def mod():
    return _load_registry()


def test_registry_module_exposes_section_6a_population_marker() -> None:
    mod = _load_registry()
    assert mod.REGISTRY_V1_SECTION_6A_FIELDS_POPULATED is True
    assert mod.SCHEMA == "peak_trade.generic_evidence_run_registry.v1"


def test_taxonomy_documents_section_6a_population() -> None:
    text = TAXONOMY_SPEC.read_text(encoding="utf-8")
    assert "REGISTRY_V1_SECTION_6A_FIELDS_POPULATED=true" in text
    assert "non-authorizing metadata defaults" in text


def test_runs_include_all_section_6a_fields(mod, tmp_path: Path) -> None:
    archive = tmp_path / "archive"
    _write_lane(archive, "paper", "paper_run")
    _write_lane(archive, "shadow", "shadow_run", review="PASS")
    payload = _build(mod, archive)
    for run in payload["runs"]:
        for field in SECTION_6A_FIELDS:
            assert field in run
        assert run["live_authority"] is False
        assert run["testnet_authority"] is False
        assert run["notion_projection"] == "disabled"
        assert run["market_dashboard_projection"] == "disabled"
        assert run["evidence_transport"] == "local_only"


def test_paper_lane_runtime_mode_paper_only(mod, tmp_path: Path) -> None:
    archive = tmp_path / "archive"
    _write_lane(archive, "paper", "paper_run")
    paper = _build(mod, archive)["runs"][0]
    assert paper["lane_id"] == "paper"
    assert paper["runtime_mode"] == "paper_only"
    assert paper["runtime_host"] == "local"
    assert paper["runtime_backend"] == "laptop"


def test_shadow_lane_uses_safe_section_6a_default(mod, tmp_path: Path) -> None:
    archive = tmp_path / "archive"
    _write_lane(archive, "shadow", "shadow_run", review="PASS")
    shadow = _build(mod, archive)["runs"][0]
    assert shadow["lane_id"] == "shadow"
    assert shadow["runtime_mode"] == "paper_only"
    assert shadow["live_authority"] is False


def test_composition_includes_section_6a_fields(mod, tmp_path: Path) -> None:
    archive = tmp_path / "archive"
    _write_lane(archive, "paper", RUN_ID)
    _write_lane(archive, "shadow", RUN_ID, review="PASS")
    _write_composition(archive, RUN_ID)
    payload = _build(mod, archive)
    assert len(payload["compositions"]) == 1
    comp = payload["compositions"][0]
    for field in SECTION_6A_FIELDS:
        assert field in comp
    assert comp["runtime_mode"] == "paper_then_shadow"
    assert comp["composition_index_authority"] is False
    assert comp["notion_projection"] == "disabled"
    assert comp["market_dashboard_projection"] == "disabled"


def test_no_registry_v2_or_new_lane_ids(mod, tmp_path: Path) -> None:
    archive = tmp_path / "archive"
    _write_lane(archive, "paper", RUN_ID)
    _write_composition(archive, RUN_ID)
    payload = _build(mod, archive)
    assert payload["schema"] == "peak_trade.generic_evidence_run_registry.v1"
    assert "generic_evidence_run_registry.v2" not in json.dumps(payload)
    lane_ids = {r["lane_id"] for r in payload["runs"]}
    assert "daemon_paper_24h" not in lane_ids
    assert "remote_runtime" not in lane_ids


def test_manifest_hash_mismatch_still_fail_closed(mod, tmp_path: Path) -> None:
    archive = tmp_path / "archive"
    run_dir = _write_lane(archive, "paper", "paper_run")
    (run_dir / "MANIFEST.sha256").write_text("deadbeef  evidence.txt\n", encoding="utf-8")
    payload = _build(mod, archive)
    assert payload["verdict"] == mod.VERDICT_FAIL_CLOSED
    paper = payload["runs"][0]
    for field in SECTION_6A_FIELDS:
        assert field in paper
    assert any(i["code"] == "MANIFEST_HASH_MISMATCH" for i in payload["issues"])
