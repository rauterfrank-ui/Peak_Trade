"""Static contract tests for Runtime Lane Taxonomy + Authority Levels Contract v0."""

from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
CANONICAL_OWNER = (
    REPO_ROOT / "docs" / "ops" / "specs" / "RUNTIME_LANE_TAXONOMY_AUTHORITY_LEVELS_CONTRACT_V0.md"
)
GENERIC_EVIDENCE_REGISTRY_V1 = (
    REPO_ROOT / "scripts" / "ops" / "build_generic_evidence_run_registry_v1.py"
)
SCHEDULER_BOUNDARY_GUARD = REPO_ROOT / "scripts" / "ops" / "scheduler_start_boundary_guard_v0.py"
P67_SCHEDULER_CLI = REPO_ROOT / "src" / "ops" / "p67" / "shadow_session_scheduler_cli_v1.py"
SCHEDULER_LAUNCHER = REPO_ROOT / "scripts" / "run_scheduler.py"
SUPERVISOR_PACK_SCRIPT = (
    REPO_ROOT / "scripts" / "ops" / "pack_online_readiness_supervisor_evidence_v0.py"
)
PRIMARY_EVIDENCE_HELPER = REPO_ROOT / "scripts" / "ops" / "primary_evidence_retention_v0.py"
P79_SHELL = REPO_ROOT / "scripts" / "ops" / "p79_supervisor_health_gate_v1.sh"
P79_VERIFY = REPO_ROOT / "scripts" / "ops" / "p79_supervisor_evidence_manifest_verify_v0.py"
P101_SCRIPT = REPO_ROOT / "scripts" / "ops" / "p101_stop_playbook_v1.sh"
P93_SCRIPT = REPO_ROOT / "scripts" / "ops" / "p93_online_readiness_status_dashboard_v1.sh"
WRAPPER_SCRIPT = REPO_ROOT / "scripts" / "ops" / "run_online_readiness_post_stop_pack_v0.sh"
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
        "GENERIC_EVIDENCE_REGISTRY_V1_IMPLEMENTED=true",
        "GENERIC_EVIDENCE_REGISTRY_V1_DEFERRED=false",
        "EVIDENCE_DOES_NOT_AUTHORIZE_RUNTIME=true",
        "TESTNET_PASS_DOES_NOT_AUTHORIZE_LIVE=true",
        "SCHEDULER_BOUNDARY_LAUNCHER_GUARDED=true",
        "P67_CLI_SCHEDULER_BOUNDARY_GUARDED=true",
        "SCHEDULER_LIBRARY_BYPASS_RESIDUAL=true",
        "SCHEDULER_COMPLETION_PRIMARY_EVIDENCE_CLOSEOUT_OPT_IN=true",
        "SUPERVISOR_EVIDENCE_PACK_CLOSEOUT_OPT_IN=true",
        "PRIMARY_EVIDENCE_SHARED_HELPER_REUSED=true",
        "P79_SUPERVISOR_ARCHIVE_ROOT_MODE_IMPLEMENTED=true",
        "P79_SUPERVISOR_PRIMARY_EVIDENCE_MANIFEST_VERIFY=true",
        "P79_SUPERVISOR_RUNTIME_TICK_MODE_PRESERVED=true",
        "P79_SUPERVISOR_GATE_NON_AUTHORIZING=true",
        "P101_POST_STOP_PRIMARY_EVIDENCE_HINTS_IMPLEMENTED=true",
        "P101_POST_STOP_PACK_HINT_REFERENCED=true",
        "P101_POST_STOP_P79_ARCHIVE_VERIFY_HINT_REFERENCED=true",
        "P101_POST_STOP_HINT_ONLY=true",
        "P101_POST_STOP_PACK_NOT_EXECUTED=true",
        "P101_POST_STOP_P79_VERIFY_NOT_EXECUTED=true",
        "P101_POST_STOP_OPERATOR_EXPLICIT_REQUIRED=true",
        "P101_POST_STOP_EVIDENCE_NON_AUTHORIZING=true",
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


def test_generic_registry_v1_implemented_not_deferred() -> None:
    assert GENERIC_EVIDENCE_REGISTRY_V1.is_file()
    text = _spec_text()
    assert "GENERIC_EVIDENCE_REGISTRY_V1_IMPLEMENTED=true" in text
    assert "GENERIC_EVIDENCE_REGISTRY_V1_DEFERRED=false" in text
    assert "build_generic_evidence_run_registry_v1.py" in text
    assert "Registry v1" in text or "registry v1" in text


def test_scheduler_boundary_markers_aligned_with_main() -> None:
    assert SCHEDULER_BOUNDARY_GUARD.is_file()
    assert P67_SCHEDULER_CLI.is_file()
    text = _spec_text()
    assert "SCHEDULER_BOUNDARY_LAUNCHER_GUARDED=true" in text
    assert "P67_CLI_SCHEDULER_BOUNDARY_GUARDED=true" in text
    assert "scheduler_start_boundary_guard_v0.py" in text
    assert "run_scheduler.py" in text
    assert "shadow_session_scheduler_cli_v1.py" in text
    assert "SCHEDULER_BOUNDARY_HARD_BLOCK_CONTRACT_V0.md" in text


def test_scheduler_library_bypass_residual_preserved() -> None:
    text = _spec_text()
    assert "SCHEDULER_LIBRARY_BYPASS_RESIDUAL=true" in text
    assert "P67_LIBRARY_SCHEDULER_BOUNDARY_OPT_IN_IMPLEMENTED=true" in text
    assert "scheduler_boundary_enforce" in text
    assert "run_shadow_session_scheduler_v1()" in text
    assert "bypass" in text.lower()
    assert "P72" in text


def test_non_authorizing_language_preserved() -> None:
    text = _spec_text()
    assert "EVIDENCE_DOES_NOT_AUTHORIZE_RUNTIME=true" in text
    assert "TESTNET_PASS_DOES_NOT_AUTHORIZE_LIVE=true" in text
    assert "non-authorizing" in text.lower()
    assert "does not grant gate clearance" in text.lower() or "does not clear" in text.lower()


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


def test_scheduler_completion_closeout_marker_aligned() -> None:
    assert SCHEDULER_LAUNCHER.is_file()
    text = _spec_text()
    assert "SCHEDULER_COMPLETION_PRIMARY_EVIDENCE_CLOSEOUT_OPT_IN=true" in text
    assert "scheduler_completion_closeout_v0.json" in text
    assert "--evidence-dir" in text or "evidence-dir" in text
    assert "primary-evidence-enforce" in text or "primary_evidence_enforce" in text
    assert "finalize_primary_evidence_root" in text
    assert "default off" in text.lower()


def test_supervisor_evidence_pack_closeout_marker_aligned() -> None:
    assert SUPERVISOR_PACK_SCRIPT.is_file()
    text = _spec_text()
    assert "SUPERVISOR_EVIDENCE_PACK_CLOSEOUT_OPT_IN=true" in text
    assert "pack_online_readiness_supervisor_evidence_v0.py" in text
    assert "supervisor_session_closeout_v0.json" in text
    assert "operator-invoked after STOP" in text.lower() or "after STOP" in text
    assert "launchctl" in text.lower()
    assert "start/stop supervisor" in text.lower()
    assert "**not**" in text or "does not start" in text.lower()


def test_primary_evidence_shared_helper_referenced() -> None:
    assert PRIMARY_EVIDENCE_HELPER.is_file()
    text = _spec_text()
    assert "PRIMARY_EVIDENCE_SHARED_HELPER_REUSED=true" in text
    assert "primary_evidence_retention_v0.py" in text
    assert "finalize_primary_evidence_root" in text


def test_opt_in_default_off_preserved() -> None:
    text = _spec_text()
    assert "default off" in text.lower()
    assert "opt-in" in text.lower()
    assert (
        "Mandatory §2a primary-evidence enforcement beyond canonical owner opt-in closeouts" in text
    )


def test_primary_evidence_closeout_residual_risks_preserved() -> None:
    text = _spec_text()
    assert "SCHEDULER_LIBRARY_BYPASS_RESIDUAL=true" in text
    assert "In-process online daemon automatic session closeout pack is **not implemented**" in text
    assert "Live-pilot" in text or "live-pilot" in text
    assert "non-authorizing" in text.lower()


def test_p79_archive_manifest_gate_marker_aligned() -> None:
    assert P79_SHELL.is_file()
    assert P79_VERIFY.is_file()
    text = _spec_text()
    assert "P79_SUPERVISOR_ARCHIVE_ROOT_MODE_IMPLEMENTED=true" in text
    assert "P79_SUPERVISOR_PRIMARY_EVIDENCE_MANIFEST_VERIFY=true" in text
    assert "P79_SUPERVISOR_RUNTIME_TICK_MODE_PRESERVED=true" in text
    assert "P79_SUPERVISOR_GATE_NON_AUTHORIZING=true" in text
    assert "ARCHIVE_ROOT" in text
    assert "p79_supervisor_evidence_manifest_verify_v0.py" in text
    assert "verify_manifest_sha256" in text
    assert "supervisor_session_closeout_v0.json" in text
    assert "MANIFEST.sha256" in text
    assert "runtime tick" in text.lower() or "Runtime tick" in text
    assert "launchctl" in text.lower()
    assert "does not clear HOLD" in text or "non-authorizing" in text.lower()


def test_p101_post_stop_hint_marker_aligned() -> None:
    assert P101_SCRIPT.is_file()
    text = _spec_text()
    for marker in (
        "P101_POST_STOP_PRIMARY_EVIDENCE_HINTS_IMPLEMENTED=true",
        "P101_POST_STOP_PACK_HINT_REFERENCED=true",
        "P101_POST_STOP_P79_ARCHIVE_VERIFY_HINT_REFERENCED=true",
        "P101_POST_STOP_HINT_ONLY=true",
        "P101_POST_STOP_PACK_NOT_EXECUTED=true",
        "P101_POST_STOP_P79_VERIFY_NOT_EXECUTED=true",
        "P101_POST_STOP_OPERATOR_EXPLICIT_REQUIRED=true",
        "P101_POST_STOP_EVIDENCE_NON_AUTHORIZING=true",
    ):
        assert marker in text
    assert "p101_stop_playbook_v1.sh" in text
    assert "P101_POST_STOP_PRIMARY_EVIDENCE_OPERATOR_HINTS.txt" in text
    assert "run_online_readiness_post_stop_pack_v0.sh" in text
    assert "--p79-archive-verify" in text
    assert "does not** execute wrapper" in text or "does not execute wrapper" in text.lower()
    assert "operator must run" in text.lower() or "explicitly after STOP" in text
    assert "non-authorizing" in text.lower()
    assert "p91" in text
    assert "SCHEDULER_LIBRARY_BYPASS_RESIDUAL=true" in text


def test_p93_post_stop_wrapper_hint_marker_aligned() -> None:
    assert P93_SCRIPT.is_file()
    text = _spec_text()
    for marker in (
        "P93_POST_STOP_WRAPPER_HINTS_IMPLEMENTED=true",
        "P93_POST_STOP_WRAPPER_REFERENCED=true",
        "P93_POST_STOP_P79_ARCHIVE_VERIFY_HINT_REFERENCED=true",
        "P93_POST_STOP_HINT_ONLY=true",
        "P93_POST_STOP_WRAPPER_NOT_EXECUTED=true",
        "P93_POST_STOP_PACK_NOT_EXECUTED=true",
        "P93_POST_STOP_P79_VERIFY_NOT_EXECUTED=true",
        "P93_POST_STOP_OPERATOR_EXPLICIT_REQUIRED=true",
        "P93_POST_STOP_EVIDENCE_NON_AUTHORIZING=true",
    ):
        assert marker in text
    assert "p93_online_readiness_status_dashboard_v1.sh" in text
    assert "P93_POST_STOP_PRIMARY_EVIDENCE_OPERATOR_HINTS.txt" in text
    assert "run_online_readiness_post_stop_pack_v0.sh" in text
    assert "--p79-archive-verify" in text
    assert "does not** execute wrapper" in text or "does not execute wrapper" in text.lower()
    assert "operator must run" in text.lower() or "explicitly after STOP" in text
    assert "non-authorizing" in text.lower()
    assert "In-process online daemon automatic session closeout pack is **not implemented**" in text
    assert "p91" in text
    assert "SCHEDULER_LIBRARY_BYPASS_RESIDUAL=true" in text


def test_post_stop_pack_wrapper_marker_aligned() -> None:
    assert WRAPPER_SCRIPT.is_file()
    text = _spec_text()
    preflight = _preflight_text()
    for marker in (
        "ONLINE_DAEMON_POST_STOP_PACK_WRAPPER_IMPLEMENTED=true",
        "ONLINE_DAEMON_POST_STOP_WRAPPER_OPERATOR_INVOKED=true",
        "ONLINE_DAEMON_POST_STOP_WRAPPER_NO_LAUNCHCTL=true",
        "ONLINE_DAEMON_POST_STOP_WRAPPER_NON_AUTHORIZING=true",
    ):
        assert marker in text
    assert "run_online_readiness_post_stop_pack_v0.sh" in text
    assert "pack_online_readiness_supervisor_evidence_v0.py" in text
    assert "--p79-archive-verify" in text
    assert "operator-invoked" in text.lower()
    assert "launchctl" in text.lower()
    assert "In-process online daemon automatic session closeout pack is **not implemented**" in text
    assert "run_online_readiness_post_stop_pack_v0.sh" in preflight
    assert "operator-invoked" in preflight.lower()
    assert "non-authorizing" in preflight.lower()
