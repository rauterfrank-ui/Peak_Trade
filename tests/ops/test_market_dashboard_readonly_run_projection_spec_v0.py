"""Static contract tests for Market Dashboard read-only run projection spec v0 (taxonomy §6a.2)."""

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
MARKET_SURFACE = REPO_ROOT / "docs" / "webui" / "MARKET_SURFACE_V0.md"
FUTURES_DASHBOARD_SPEC = (
    REPO_ROOT / "docs" / "ops" / "specs" / "FUTURES_READ_ONLY_MARKET_DASHBOARD_CONTRACT_V0.md"
)
REGISTRY_SCRIPT = REPO_ROOT / "scripts" / "ops" / "build_generic_evidence_run_registry_v1.py"
DOCS_TRUTH_MAP = REPO_ROOT / "docs" / "ops" / "registry" / "DOCS_TRUTH_MAP.md"
REMOTE_RUNTIME_TESTS = (
    REPO_ROOT / "tests" / "ops" / "test_remote_runtime_host_metadata_contract_v0.py"
)
SECTION_6A_POPULATION_TESTS = (
    REPO_ROOT / "tests" / "ops" / "test_registry_v1_section_6a_field_population_v0.py"
)
NOTION_SPEC_TESTS = (
    REPO_ROOT / "tests" / "ops" / "test_notion_post_closeout_sync_projection_spec_v0.py"
)
PROJECTION_FIXTURE_TESTS = (
    REPO_ROOT / "tests" / "ops" / "test_registry_v1_projection_consumer_smoke_fixtures_v0.py"
)
MARKET_DASHBOARD_READONLY_TESTS = (
    REPO_ROOT / "tests" / "webui" / "test_market_dashboard_readonly_structure_contract_v0.py"
)

DASHBOARD_SPEC_MARKERS = (
    "MARKET_DASHBOARD_READONLY_RUN_PROJECTION_SPEC_V0=true",
    "MARKET_DASHBOARD_PROJECTION_READONLY=true",
    "MARKET_DASHBOARD_WRITE_DEFAULT=false",
    "MARKET_DASHBOARD_AUTHORITY=false",
    "MARKET_DASHBOARD_RUNTIME_ACTIONS=false",
    "MARKET_DASHBOARD_POLLING_ACTIVE_RUNTIME=false",
    "MARKET_DASHBOARD_START_STOP_BUTTONS=false",
    "MARKET_DASHBOARD_DOUBLE_PLAY_AUTHORITY=false",
    "MARKET_DASHBOARD_DOUBLE_PLAY_TOUCHED=false",
    "RUNTIME_AUTHORITY=false",
    "SCHEDULER_CLEARANCE_AUTHORITY=false",
    "LIVE_AUTHORITY=false",
    "TESTNET_AUTHORITY=false",
    "BROKER_AUTHORITY=false",
    "DOUBLE_PLAY_AUTHORITY=false",
    "REGISTRY_V1_IS_SOLE_DASHBOARD_PROJECTION_FEED=true",
    "MARKET_DASHBOARD_PROJECTION_DEFAULT=disabled",
)

DASHBOARD_PROJECTION_STATES = ("disabled", "read_only_run_status", "read_only_evidence_status")

FORBIDDEN_TRUTH_LAYER_PHRASES = (
    "dashboard is canonical",
    "dashboard approves",
    "dashboard grants approval",
    "dashboard authorizes live",
    "dashboard truth layer is canonical",
)

ALLOWED_PROJECTION_FIELDS = pc.ALLOWED_PROJECTION_FIELDS
RUN_PROJECTION_FIELDS = pc.RUN_PROJECTION_FIELDS


def _section_6a2() -> str:
    text = TAXONOMY_SPEC.read_text(encoding="utf-8")
    return text.split("### 6a.2 Market Dashboard read-only run projection contract v0", 1)[1].split(
        "### v0 authority posture", 1
    )[0]


def _load_registry():
    spec = importlib.util.spec_from_file_location(
        "build_generic_evidence_run_registry_v1_dashboard_spec",
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


def test_taxonomy_section_6a2_present() -> None:
    text = TAXONOMY_SPEC.read_text(encoding="utf-8")
    assert "### 6a.2 Market Dashboard read-only run projection contract v0" in text
    for marker in DASHBOARD_SPEC_MARKERS:
        assert marker in text


def test_market_dashboard_projection_states_documented() -> None:
    section = _section_6a2()
    for state in DASHBOARD_PROJECTION_STATES:
        assert f"`{state}`" in section


def test_default_market_dashboard_projection_disabled() -> None:
    section = _section_6a2()
    assert "MARKET_DASHBOARD_PROJECTION_DEFAULT=disabled" in section
    assert "market_dashboard_projection=disabled" in section
    mod = _load_registry()
    assert mod.REMOTE_RUNTIME_HOST_METADATA_V0_DEFAULTS["market_dashboard_projection"] == "disabled"


def test_registry_v1_is_sole_dashboard_feed() -> None:
    section = _section_6a2()
    assert "REGISTRY_V1_IS_SOLE_DASHBOARD_PROJECTION_FEED=true" in section
    assert "runs[]" in section
    assert "compositions[]" in section
    assert "Do not" in section
    mod = _load_registry()
    assert mod.REGISTRY_V1_IS_SOLE_DASHBOARD_PROJECTION_FEED is True
    assert mod.MARKET_DASHBOARD_READONLY_RUN_PROJECTION_SPEC_V0 is True
    assert mod.SCHEMA == "peak_trade.generic_evidence_run_registry.v1"


def test_allowed_projection_fields_documented() -> None:
    section = _section_6a2()
    for field in ALLOWED_PROJECTION_FIELDS:
        assert field in section


def test_canonical_boundary_copy_present() -> None:
    section = _section_6a2()
    assert "Read-only operational projection" in section
    assert "does not authorize runtime" in section.lower()
    assert "Double Play decisions" in section


def test_forbidden_runtime_actions_and_no_truth_layer_language() -> None:
    section = _section_6a2().lower()
    for marker in (
        "market_dashboard_authority=false",
        "market_dashboard_runtime_actions=false",
        "market_dashboard_polling_active_runtime=false",
        "market_dashboard_start_stop_buttons=false",
        "no parallel dashboard truth layer",
    ):
        assert marker in section
    for phrase in FORBIDDEN_TRUTH_LAYER_PHRASES:
        assert phrase not in section


def test_double_play_protected_untouched() -> None:
    section = _section_6a2()
    assert "MARKET_DASHBOARD_DOUBLE_PLAY_TOUCHED=false" in section
    assert "double-play" in section.lower() or "double_play" in section.lower()
    assert "untouched" in section.lower() or "unchanged" in section.lower()


def test_no_registry_v2_or_new_lane_ids() -> None:
    section = _section_6a2()
    assert "Registry v2" in section or "no Registry v2" in section
    assert "lane_id=daemon_paper_24h" in section
    assert "lane_id=remote_runtime" in section
    assert "generic_evidence_run_registry.v2" not in section


def test_surface_cross_references() -> None:
    section = _section_6a2()
    assert "MARKET_SURFACE_V0.md" in section
    assert "FUTURES_READ_ONLY_MARKET_DASHBOARD_CONTRACT_V0.md" in section
    assert MARKET_SURFACE.is_file()
    assert FUTURES_DASHBOARD_SPEC.is_file()


def test_registry_fixture_supports_projection_field_extraction(mod, tmp_path: Path) -> None:
    archive = tmp_path / "archive"
    pc.write_minimal_paper_run(archive)
    payload = mod.build_registry(mod.BuildContext(archive_root=archive, repo_root=REPO_ROOT))
    run = payload["runs"][0]
    pc.assert_non_authorizing_run_projection_defaults(run)
    assert payload["schema"] == "peak_trade.generic_evidence_run_registry.v1"
    assert "generic_evidence_run_registry.v2" not in json.dumps(payload)


def test_owner_crosslinks() -> None:
    owner_text = Path(__file__).read_text(encoding="utf-8")
    assert REMOTE_RUNTIME_TESTS.name in owner_text
    assert SECTION_6A_POPULATION_TESTS.name in owner_text
    assert NOTION_SPEC_TESTS.name in owner_text
    assert PROJECTION_FIXTURE_TESTS.name in owner_text
    remote_text = REMOTE_RUNTIME_TESTS.read_text(encoding="utf-8")
    assert "MARKET_DASHBOARD_PROJECTION_READONLY=true" in remote_text
    assert MARKET_DASHBOARD_READONLY_TESTS.is_file()


def test_docs_truth_map_references_dashboard_projection_spec() -> None:
    text = DOCS_TRUTH_MAP.read_text(encoding="utf-8")
    assert "MARKET_DASHBOARD_READONLY_RUN_PROJECTION_SPEC_V0" in text or "6a.2" in text
    assert TAXONOMY_SPEC.name in text
