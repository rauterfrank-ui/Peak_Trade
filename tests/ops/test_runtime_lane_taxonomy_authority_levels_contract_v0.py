"""Static contract tests for Runtime Lane Taxonomy + Authority Levels Contract v0."""

from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
CANONICAL_OWNER = (
    REPO_ROOT / "docs" / "ops" / "specs" / "RUNTIME_LANE_TAXONOMY_AUTHORITY_LEVELS_CONTRACT_V0.md"
)
PREFLIGHT_OWNER = (
    REPO_ROOT / "docs" / "ops" / "runbooks" / "PAPER_SHADOW_247_PREFLIGHT_CONTRACT_V0.md"
)
DOCS_TRUTH_MAP = REPO_ROOT / "docs" / "ops" / "registry" / "DOCS_TRUTH_MAP.md"

REQUIRED_LANE_IDS = (
    "paper",
    "shadow",
    "testnet",
    "scheduler",
    "canary",
    "live_canary",
    "live_production",
    "dashboard",
    "ai_orchestrator",
    "notion",
    "docs",
)

REQUIRED_AUTHORITY_LEVELS = (
    "evidence_only",
    "planning_only",
    "review_input_only",
    "bounded_runtime_candidate",
    "scoped_runtime_exception",
    "operator_decision_required",
    "go_no_go_route_selected",
    "go_decision_granted",
    "live_authority_forbidden",
    "live_authority_requires_separate_record",
)

FORBIDDEN_PROMOTION_LITERALS = (
    "FORBIDDEN_PROMOTION_PAPER_TO_SHADOW_TESTNET_LIVE",
    "FORBIDDEN_PROMOTION_SHADOW_TO_TESTNET_LIVE",
    "FORBIDDEN_PROMOTION_TESTNET_PASS_TO_LIVE_BROKER_EXCHANGE",
    "FORBIDDEN_PROMOTION_SCHEDULER_EVIDENCE_TO_LIVE",
    "FORBIDDEN_PROMOTION_CANARY_DOCS_TO_LIVE",
    "FORBIDDEN_PROMOTION_DASHBOARD_NOTION_DOCS_AI_TO_APPROVAL",
    "FORBIDDEN_PROMOTION_SECRET_PRESENCE_TO_CREDENTIAL_VALIDITY",
    "FORBIDDEN_PROMOTION_GO_NO_GO_TEMPLATE_TO_GO_DECISION",
)

REGISTRY_FIELD_NAMES = (
    "lane_id",
    "lane_kind",
    "evidence_role",
    "runtime_allowed_by_default",
    "requires_approval_record",
    "review_required",
    "manifest_required",
    "durable_retention_required",
    "notion_link_allowed",
    "can_clear_hold",
    "can_clear_glb",
    "can_authorize_live",
    "can_touch_broker_exchange",
    "protected_master_v2_boundary",
)

UNSAFE_AUTHORIZATION_LITERALS = (
    "LIVE_ALLOWED=true",
    "BROKER_EXCHANGE_ALLOWED=true",
    "HOLD_NO_PAPER_RUN_CLEARED=true",
    "GLB_014_CLEARED=true",
    "GLB_015_CLEARED=true",
)

FORBIDDEN_DUPLICATE_SPEC_PATHS = (
    "docs/ops/runbooks/RUNTIME_LANE_TAXONOMY",
    "docs/ops/specs/LANE_TAXONOMY_AUTHORITY",
    "docs/ops/registry/LANE_REGISTRY",
)


def _spec_text() -> str:
    return CANONICAL_OWNER.read_text(encoding="utf-8")


def _preflight_text() -> str:
    return PREFLIGHT_OWNER.read_text(encoding="utf-8")


def test_canonical_owner_exists() -> None:
    assert CANONICAL_OWNER.is_file()


def test_spec_title_present() -> None:
    assert "# Runtime Lane Taxonomy + Authority Levels Contract v0" in _spec_text()


def test_required_machine_markers_present() -> None:
    text = _spec_text()
    for marker in (
        "RUNTIME_LANE_TAXONOMY_AUTHORITY_LEVELS_CONTRACT_V0=true",
        "GENERIC_EVIDENCE_REGISTRY_V1_DEFERRED=true",
        "EVIDENCE_DOES_NOT_AUTHORIZE_RUNTIME=true",
        "TESTNET_PASS_DOES_NOT_AUTHORIZE_LIVE=true",
        "SCHEDULER_BOUNDARY_GAP_ACKNOWLEDGED=true",
        "MASTER_V2_DOUBLE_PLAY_BOUNDARY_PRESERVED=true",
    ):
        assert marker in text


def test_all_normative_lane_ids_present() -> None:
    text = _spec_text()
    for lane_id in REQUIRED_LANE_IDS:
        assert f"`{lane_id}`" in text, f"missing lane_id {lane_id!r}"


def test_all_authority_levels_present() -> None:
    text = _spec_text()
    for level in REQUIRED_AUTHORITY_LEVELS:
        assert f"`{level}`" in text, f"missing authority level {level!r}"


def test_all_forbidden_promotion_literals_present() -> None:
    text = _spec_text()
    for literal in FORBIDDEN_PROMOTION_LITERALS:
        assert literal in text


def test_registry_field_names_present() -> None:
    text = _spec_text()
    assert "REGISTRY_V1_LANE_FIELD_SCHEMA_DEFINED=true" in text
    for field in REGISTRY_FIELD_NAMES:
        assert f"`{field}`" in text or f"- `{field}`" in text or field in text


def test_scheduler_gap_acknowledged() -> None:
    text = _spec_text()
    assert "SCHEDULER_BOUNDARY_VERIFIED=false" in text
    assert "hard process-side block" in text.lower() or "process-side block" in text.lower()
    assert "Scheduler guard implementation is out of scope" in text


def test_generic_registry_v1_deferred() -> None:
    text = _spec_text()
    assert "GENERIC_EVIDENCE_REGISTRY_V1_DEFERRED=true" in text
    assert "Registry v1" in text or "registry v1" in text


def test_paper_shadow_testnet_separation_stated() -> None:
    text = _spec_text()
    assert "Paper / Shadow / Testnet hard separation" in text
    assert "runs&#47;paper" in text
    assert "runs&#47;shadow" in text
    assert "runs&#47;testnet" in text


def test_testnet_pass_does_not_authorize_live() -> None:
    text = _spec_text()
    assert "TESTNET_PASS_DOES_NOT_AUTHORIZE_LIVE=true" in text
    assert "FORBIDDEN_PROMOTION_TESTNET_PASS_TO_LIVE_BROKER_EXCHANGE" in text


def test_dashboard_notion_docs_ai_not_approval_authority() -> None:
    text = _spec_text()
    assert "FORBIDDEN_PROMOTION_DASHBOARD_NOTION_DOCS_AI_TO_APPROVAL" in text
    for lane in ("dashboard", "notion", "docs", "ai_orchestrator"):
        assert f"`{lane}`" in text


def test_master_v2_double_play_boundary_preserved() -> None:
    text = _spec_text()
    assert "MASTER_V2_DOUBLE_PLAY_BOUNDARY_PRESERVED=true" in text
    assert "Master V2 / Double Play" in text
    assert "protected" in text.lower()


def test_spec_crosslinks_preflight_retention_owner() -> None:
    text = _spec_text()
    assert "PAPER_SHADOW_247_PREFLIGHT_CONTRACT_V0.md" in text
    assert "§2a" in text
    assert "§2b" in text


def test_preflight_crosslinks_taxonomy_spec() -> None:
    text = _preflight_text()
    assert "RUNTIME_LANE_TAXONOMY_AUTHORITY_LEVELS_CONTRACT_V0.md" in text


def test_docs_truth_map_lists_taxonomy_spec() -> None:
    text = DOCS_TRUTH_MAP.read_text(encoding="utf-8")
    assert "RUNTIME_LANE_TAXONOMY_AUTHORITY_LEVELS_CONTRACT_V0.md" in text


def test_spec_does_not_contain_unsafe_authorization_literals() -> None:
    text = _spec_text()
    for literal in UNSAFE_AUTHORIZATION_LITERALS:
        assert literal not in text


def test_no_duplicate_docs_surface_paths_introduced() -> None:
    specs_dir = REPO_ROOT / "docs" / "ops" / "specs"
    runbooks_dir = REPO_ROOT / "docs" / "ops" / "runbooks"
    for fragment in FORBIDDEN_DUPLICATE_SPEC_PATHS:
        assert not (specs_dir / fragment).exists()
        assert not (runbooks_dir / fragment).exists()
    taxonomy_specs = list(specs_dir.glob("*LANE_TAXONOMY*"))
    assert taxonomy_specs == [CANONICAL_OWNER]


def test_readiness_tooling_referenced_non_authorizing() -> None:
    text = _spec_text()
    assert "Readiness Evidence Ledger v0" in text
    assert "Readiness Gate Snapshot v0" in text
    assert "non-authorizing" in text.lower()
