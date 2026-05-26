"""Contract tests for shared Registry v1 projection consumer smoke fixtures v0."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from tests.fixtures.ops.generic_evidence_run_registry_v1 import projection_consumer_v0 as pc
from tests.ops import test_market_dashboard_readonly_run_projection_spec_v0 as dashboard_spec
from tests.ops import test_notion_post_closeout_sync_projection_spec_v0 as notion_spec

REPO_ROOT = pc.REPO_ROOT
TAXONOMY_SPEC = (
    REPO_ROOT / "docs" / "ops" / "specs" / "RUNTIME_LANE_TAXONOMY_AUTHORITY_LEVELS_CONTRACT_V0.md"
)
FIXTURES_README = (
    REPO_ROOT / "tests" / "fixtures" / "ops" / "generic_evidence_run_registry_v1" / "README.md"
)

AUTHORITY_MARKERS = (
    "NOTION_AUTHORITY=false",
    "MARKET_DASHBOARD_AUTHORITY=false",
    "S3_AUTHORITY=false",
    "RUNTIME_AUTHORITY=false",
    "SCHEDULER_CLEARANCE_AUTHORITY=false",
    "LIVE_AUTHORITY=false",
    "TESTNET_AUTHORITY=false",
    "BROKER_AUTHORITY=false",
    "DOUBLE_PLAY_AUTHORITY=false",
)


def _section_6a1() -> str:
    text = TAXONOMY_SPEC.read_text(encoding="utf-8")
    return text.split("### 6a.1 Notion post-closeout sync projection contract v0", 1)[1].split(
        "### 6a.2 Market Dashboard read-only run projection contract v0", 1
    )[0]


def _section_6a2() -> str:
    text = TAXONOMY_SPEC.read_text(encoding="utf-8")
    return text.split("### 6a.2 Market Dashboard read-only run projection contract v0", 1)[1].split(
        "### v0 authority posture", 1
    )[0]


def test_shared_fixture_module_marker() -> None:
    assert pc.REGISTRY_V1_PROJECTION_CONSUMER_SMOKE_FIXTURES_V0 is True


def test_notion_and_dashboard_tests_import_shared_field_constants() -> None:
    assert notion_spec.ALLOWED_PROJECTION_FIELDS is pc.ALLOWED_PROJECTION_FIELDS
    assert notion_spec.RUN_PROJECTION_FIELDS is pc.RUN_PROJECTION_FIELDS
    assert dashboard_spec.ALLOWED_PROJECTION_FIELDS is pc.ALLOWED_PROJECTION_FIELDS
    assert dashboard_spec.RUN_PROJECTION_FIELDS is pc.RUN_PROJECTION_FIELDS


def test_taxonomy_sections_document_shared_projection_fields() -> None:
    for field in pc.ALLOWED_PROJECTION_FIELDS:
        assert field in _section_6a1()
        assert field in _section_6a2()


def test_s3_relevant_fields_subset_of_run_projection_fields() -> None:
    for field in pc.S3_RELEVANT_PROJECTION_FIELDS:
        assert field in pc.RUN_PROJECTION_FIELDS


def test_fixtures_readme_documents_projection_consumer_contract() -> None:
    text = FIXTURES_README.read_text(encoding="utf-8")
    assert "Projection consumer smoke fixtures v0" in text
    assert "REGISTRY_V1_PROJECTION_CONSUMER_SMOKE_FIXTURES_V0=true" in text
    assert "S3_RELEVANT_PROJECTION_FIELDS" in text
    for marker in AUTHORITY_MARKERS:
        assert marker in text
    assert "non-authorizing" in text.lower()


def test_minimal_paper_run_builds_registry_v1_with_projection_fields(tmp_path: Path) -> None:
    archive = tmp_path / "archive"
    pc.write_minimal_paper_run(archive)
    payload = pc.build_registry(archive)
    assert payload["schema"] == "peak_trade.generic_evidence_run_registry.v1"
    for field in pc.TOP_LEVEL_PROJECTION_SUMMARY_FIELDS:
        assert field in payload
    run = payload["runs"][0]
    pc.assert_non_authorizing_run_projection_defaults(run)
    for field in pc.S3_RELEVANT_PROJECTION_FIELDS:
        assert field in run


def test_composition_fixture_includes_record_kind_and_section_6a_fields(tmp_path: Path) -> None:
    archive = tmp_path / "archive"
    run_id = pc.DEFAULT_COMPOSITION_RUN_ID
    pc.write_lane(archive, "paper", run_id)
    pc.write_lane(archive, "shadow", run_id, review="PASS")
    pc.write_composition(archive, run_id)
    payload = pc.build_registry(archive)
    comp = payload["compositions"][0]
    assert comp["record_kind"] == "composition_index"
    for field in pc.SECTION_6A_METADATA_FIELDS:
        assert field in comp
    assert comp["composition_id"] == "daemon_paper_24h"
    assert comp["rollup_manifest_verified"] is True
    for field in pc.ALLOWED_PROJECTION_FIELDS:
        if field in ("lane_id", "review_verdict", "manifest_verified"):
            continue
        assert field in comp


def test_no_registry_v2_or_forbidden_lane_ids(tmp_path: Path) -> None:
    archive = tmp_path / "archive"
    pc.write_minimal_paper_run(archive)
    payload = pc.build_registry(archive)
    assert "generic_evidence_run_registry.v2" not in json.dumps(payload)
    lane_ids = {r["lane_id"] for r in payload["runs"]}
    assert "daemon_paper_24h" not in lane_ids
    assert "remote_runtime" not in lane_ids


def test_section_6a_population_tests_use_shared_archive_helpers() -> None:
    from tests.ops import test_registry_v1_section_6a_field_population_v0 as section_6a

    assert section_6a._write_lane is pc.write_lane
    assert section_6a._write_composition is pc.write_composition
