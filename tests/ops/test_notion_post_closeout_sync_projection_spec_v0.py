"""Static contract tests for Notion post-closeout sync projection spec v0 (taxonomy §6a.1)."""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import pytest

from tests.fixtures.ops.generic_evidence_run_registry_v1 import projection_consumer_v0 as pc

REPO_ROOT = Path(__file__).resolve().parents[2]
TAXONOMY_SPEC = (
    REPO_ROOT / "docs" / "ops" / "specs" / "RUNTIME_LANE_TAXONOMY_AUTHORITY_LEVELS_CONTRACT_V0.md"
)
REGISTRY_SCRIPT = REPO_ROOT / "scripts" / "ops" / "build_generic_evidence_run_registry_v1.py"
DOCS_TRUTH_MAP = REPO_ROOT / "docs" / "ops" / "registry" / "DOCS_TRUTH_MAP.md"
REMOTE_RUNTIME_TESTS = (
    REPO_ROOT / "tests" / "ops" / "test_remote_runtime_host_metadata_contract_v0.py"
)
SECTION_6A_POPULATION_TESTS = (
    REPO_ROOT / "tests" / "ops" / "test_registry_v1_section_6a_field_population_v0.py"
)
PROJECTION_FIXTURE_TESTS = (
    REPO_ROOT / "tests" / "ops" / "test_registry_v1_projection_consumer_smoke_fixtures_v0.py"
)

NOTION_SPEC_MARKERS = (
    "NOTION_POST_CLOSEOUT_SYNC_PROJECTION_SPEC_V0=true",
    "NOTION_PROJECTION_NON_AUTHORIZING=true",
    "NOTION_WRITE_DEFAULT=false",
    "NOTION_SYNC_REQUIRES_OPERATOR_TOKEN=true",
    "NOTION_AUTHORITY=false",
    "NOTION_DESTRUCTIVE_OPS=false",
    "RUNTIME_AUTHORITY=false",
    "SCHEDULER_CLEARANCE_AUTHORITY=false",
    "LIVE_AUTHORITY=false",
    "TESTNET_AUTHORITY=false",
    "BROKER_AUTHORITY=false",
    "DOUBLE_PLAY_AUTHORITY=false",
    "REGISTRY_V1_IS_SOLE_NOTION_PROJECTION_FEED=true",
    "NOTION_PROJECTION_DEFAULT=disabled",
)

NOTION_PROJECTION_STATES = ("disabled", "post_closeout_sync", "verified_evidence_index")

FORBIDDEN_TRUTH_LAYER_PHRASES = (
    "notion is canonical",
    "notion approves",
    "notion grants approval",
    "notion authorizes live",
    "notion truth layer is canonical",
)

ALLOWED_PROJECTION_FIELDS = pc.ALLOWED_PROJECTION_FIELDS
RUN_PROJECTION_FIELDS = pc.RUN_PROJECTION_FIELDS


def _section_6a1() -> str:
    text = TAXONOMY_SPEC.read_text(encoding="utf-8")
    return text.split("### 6a.1 Notion post-closeout sync projection contract v0", 1)[1].split(
        "### 6a.2 Market Dashboard read-only run projection contract v0", 1
    )[0]


def _load_registry():
    spec = importlib.util.spec_from_file_location(
        "build_generic_evidence_run_registry_v1_notion_spec",
        REGISTRY_SCRIPT,
    )
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture
def mod():
    return _load_registry()


def test_taxonomy_section_6a1_present() -> None:
    text = TAXONOMY_SPEC.read_text(encoding="utf-8")
    assert "### 6a.1 Notion post-closeout sync projection contract v0" in text
    for marker in NOTION_SPEC_MARKERS:
        assert marker in text


def test_notion_projection_states_documented() -> None:
    section = _section_6a1()
    for state in NOTION_PROJECTION_STATES:
        assert f"`{state}`" in section


def test_default_notion_projection_disabled() -> None:
    section = _section_6a1()
    assert "NOTION_PROJECTION_DEFAULT=disabled" in section
    assert "notion_projection=disabled" in section
    mod = _load_registry()
    assert mod.REMOTE_RUNTIME_HOST_METADATA_V0_DEFAULTS["notion_projection"] == "disabled"


def test_registry_v1_is_sole_notion_feed() -> None:
    section = _section_6a1()
    assert "REGISTRY_V1_IS_SOLE_NOTION_PROJECTION_FEED=true" in section
    assert "Do not" in section and "walk" in section.lower() or "directly" in section.lower()
    assert "runs[]" in section
    assert "compositions[]" in section
    mod = _load_registry()
    assert mod.REGISTRY_V1_IS_SOLE_NOTION_PROJECTION_FEED is True
    assert mod.SCHEMA == "peak_trade.generic_evidence_run_registry.v1"


def test_future_sync_requires_operator_token() -> None:
    section = _section_6a1()
    assert "NOTION_SYNC_REQUIRES_OPERATOR_TOKEN=true" in section
    assert "APPROVE_NOTION_POST_CLOSEOUT_SYNC_NOW=true" in section
    assert "not implemented" in section.lower()


def test_allowed_projection_fields_documented() -> None:
    section = _section_6a1()
    for field in ALLOWED_PROJECTION_FIELDS:
        assert field in section


def test_canonical_boundary_copy_present() -> None:
    section = _section_6a1()
    assert "non-authorizing projection of Peak_Trade repo" in section
    assert "Repo contracts, manifests, closeouts" in section
    assert "do not authorize runtime" in section.lower()


def test_forbidden_authority_and_no_truth_layer_language() -> None:
    section = _section_6a1().lower()
    for marker in (
        "notion_authority=false",
        "notion_write_default=false",
        "no parallel notion truth layer",
    ):
        assert marker in section
    for phrase in FORBIDDEN_TRUTH_LAYER_PHRASES:
        assert phrase not in section


def test_no_registry_v2_or_new_lane_ids() -> None:
    section = _section_6a1()
    assert "Registry v2" in section or "no Registry v2" in section
    assert "lane_id=daemon_paper_24h" in section
    assert "lane_id=remote_runtime" in section
    assert "generic_evidence_run_registry.v2" not in section


def test_registry_fixture_supports_projection_field_extraction(mod, tmp_path: Path) -> None:
    archive = tmp_path / "archive"
    pc.write_minimal_paper_run(archive)
    payload = mod.build_registry(mod.BuildContext(archive_root=archive, repo_root=REPO_ROOT))
    run = payload["runs"][0]
    pc.assert_non_authorizing_run_projection_defaults(run)
    assert payload["schema"] == "peak_trade.generic_evidence_run_registry.v1"
    assert "generic_evidence_run_registry.v2" not in json.dumps(payload)


def test_owner_crosslinks_remote_runtime_and_section_6a_population_tests() -> None:
    owner_text = Path(__file__).read_text(encoding="utf-8")
    assert REMOTE_RUNTIME_TESTS.name in owner_text
    assert SECTION_6A_POPULATION_TESTS.name in owner_text
    assert PROJECTION_FIXTURE_TESTS.name in owner_text
    remote_text = REMOTE_RUNTIME_TESTS.read_text(encoding="utf-8")
    assert "NOTION_PROJECTION_NON_AUTHORIZING=true" in remote_text


def test_docs_truth_map_references_notion_projection_spec() -> None:
    text = DOCS_TRUTH_MAP.read_text(encoding="utf-8")
    assert "NOTION_POST_CLOSEOUT_SYNC_PROJECTION_SPEC_V0" in text or "6a.1" in text
    assert TAXONOMY_SPEC.name in text


def test_post_closeout_charter_binds_notion_default_off_and_no_authority() -> None:
    section = pc.taxonomy_section_6a08()
    for marker in pc.POST_CLOSEOUT_PROJECTION_AUTOMATION_CHARTER_MARKERS:
        assert marker in section
    assert "NOTION_POST_CLOSEOUT_SYNC_V0" in section
    assert "§6a.1" in section
    notion_section = _section_6a1()
    assert "NOTION_WRITE_DEFAULT=false" in notion_section
    assert "after closeout" in notion_section.lower() or "post_closeout_sync" in notion_section
    assert "manifest" in section.lower()


def test_notion_projection_after_closeout_and_manifest_verify_only() -> None:
    section = pc.taxonomy_section_6a08()
    assert "PROJECTION_AFTER_CLOSEOUT_ONLY=true" in section
    assert "PROJECTION_AFTER_MANIFEST_VERIFY_ONLY=true" in section
    assert "NOTION_POST_CLOSEOUT_SYNC_ENABLED=false" in section
    assert "NOTION_IS_PROJECTION_ONLY=true" in section
