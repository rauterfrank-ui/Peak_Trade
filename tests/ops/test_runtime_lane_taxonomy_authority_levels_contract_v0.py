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
P91_SCRIPT = REPO_ROOT / "scripts" / "ops" / "p91_audit_snapshot_runner_v1.sh"
WRAPPER_SCRIPT = REPO_ROOT / "scripts" / "ops" / "run_online_readiness_post_stop_pack_v0.sh"
MARKET_DASHBOARD_SPEC = (
    REPO_ROOT / "docs" / "ops" / "specs" / "FUTURES_READ_ONLY_MARKET_DASHBOARD_CONTRACT_V0.md"
)
MARKET_SURFACE_V0 = REPO_ROOT / "docs" / "webui" / "MARKET_SURFACE_V0.md"
READINESS_LEDGER_SCRIPT = REPO_ROOT / "scripts" / "ops" / "build_readiness_evidence_ledger_v0.py"
READINESS_MIRROR_SCRIPT = (
    REPO_ROOT / "scripts" / "ops" / "report_readiness_ledger_preflight_mirror_v0.py"
)
READINESS_GATE_SNAPSHOT_SCRIPT = (
    REPO_ROOT / "scripts" / "ops" / "report_readiness_gate_snapshot_v0.py"
)
PAPER_BOUNDED_ADAPTER_SCRIPT = (
    REPO_ROOT / "scripts" / "ops" / "run_paper_only_bounded_observation_adapter_v0.py"
)
SHADOW_BOUNDED_ADAPTER_SCRIPT = (
    REPO_ROOT / "scripts" / "ops" / "run_shadow_bounded_observation_adapter_v0.py"
)
TESTNET_BOUNDED_ADAPTER_SCRIPT = (
    REPO_ROOT / "scripts" / "ops" / "run_testnet_bounded_observation_adapter_v0.py"
)
SHADOW_BOUNDED_REVIEW_SCRIPT = (
    REPO_ROOT / "scripts" / "ops" / "review_shadow_bounded_observation_evidence_v0.py"
)
TESTNET_BOUNDED_REVIEW_SCRIPT = (
    REPO_ROOT / "scripts" / "ops" / "review_testnet_bounded_observation_evidence_v0.py"
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
    "AUTONOMY_STAGE_AUTHORITY_CROSSWALK",
)

REQUIRED_AUTONOMY_STAGES = tuple(str(i) for i in range(8))

AUTONOMY_CROSSWALK_MARKERS = (
    "AUTONOMY_STAGE_AUTHORITY_CROSSWALK_V0=true",
    "AUTONOMY_STAGE_COUNT=8",
    "AI_L6_EXEC_FORBIDDEN=true",
    "SIGNAL_NOT_TRADE=true",
    "STRATEGY_NOT_AUTHORITY=true",
    "AI_NOT_AUTHORITY=true",
    "DASHBOARD_NOT_APPROVAL=true",
    "KILLSWITCH_SAFETY_VETO_DOMINATES=true",
    "GO_DECISION_REQUIRES_EXTERNAL_RECORD=true",
    "OPERATOR_ONLY_PERMANENT_GATES_DEFINED=true",
)

MASTER_V2_ROADMAP = REPO_ROOT / "docs" / "ops" / "specs" / "MASTER_V2_GO_LIVE_ROADMAP_V0.md"


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
        "REMOTE_RUNTIME_HOST_METADATA_CONTRACT_V0=true",
        "REMOTE_RUNTIME_IS_BACKEND_NOT_LANE=true",
        *AUTONOMY_CROSSWALK_MARKERS,
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
    assert "§2b.3" in text


def test_spec_section_6a08_1_preflight_2b3_closeout_validation_crosslink_v0() -> None:
    text = _spec_text()
    section_start = text.index("#### 6a.0.8.1 Post-Closeout Automation Hook Owner Precheck v0")
    section_end = text.index(
        "### 6a.0.9 Shared Projection Payload Builder Planning Contract v0 (planning-only)",
        section_start,
    )
    section = text[section_start:section_end]
    assert "TAXONOMY_PREFLIGHT_2B3_CLOSEOUT_VALIDATION_CROSSLINK_V0=true" in section
    assert "§2b.3" in section
    assert "#4128" in section
    assert "BLOCKER_HINT" in section
    assert "--durable-closeout-force" in section
    assert "AUTHORITATIVE_STATUS_HIERARCHY_V0=true" in section
    assert "MACHINE_SUMMARY.env" in section
    assert "PREFLIGHT_REMAINS_BLOCKED=true" in section


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


def test_readiness_tooling_taxonomy_cross_ref_aligned() -> None:
    assert READINESS_LEDGER_SCRIPT.is_file()
    assert READINESS_MIRROR_SCRIPT.is_file()
    assert READINESS_GATE_SNAPSHOT_SCRIPT.is_file()
    text = _spec_text()
    for marker in (
        "READINESS_LEDGER_REVIEW_INPUT_ONLY=true",
        "READINESS_MIRROR_NON_AUTHORIZING=true",
        "GATE_SNAPSHOT_NO_APPROVAL_AUTHORITY=true",
        "READINESS_AGGREGATE_NO_LIVE_BROKER_EXCHANGE_AUTHORITY=true",
    ):
        assert marker in text
    assert "build_readiness_evidence_ledger_v0.py" in text
    assert "report_readiness_ledger_preflight_mirror_v0.py" in text
    assert "report_readiness_gate_snapshot_v0.py" in text
    assert "Readiness Ledger Preflight Mirror v0" in text
    assert "review input only" in text.lower() or "review_input_only" in text
    assert "READINESS_EVIDENCE_LEDGER_PASS_BLOCKED_SAFE" in text
    assert "READINESS_GATE_SNAPSHOT_PASS_BLOCKED_SAFE" in text
    assert "non-authorizing" in text.lower()
    assert "does not" in text.lower() or "do not" in text.lower()
    assert "Live" in text or "live" in text.lower()
    assert "broker" in text.lower()
    assert "SCHEDULER_BOUNDARY_HARD_BLOCK_CONTRACT_V0.md" in text
    assert "PAPER_SHADOW_247_PREFLIGHT_CONTRACT_V0.md" in text
    assert "operator" in text.lower()
    assert "FORBIDDEN_PROMOTION" in text


def test_readiness_script_taxonomy_reciprocal_pointer_aligned() -> None:
    taxonomy_ref = "RUNTIME_LANE_TAXONOMY_AUTHORITY_LEVELS_CONTRACT_V0.md"
    for script in (
        READINESS_LEDGER_SCRIPT,
        READINESS_MIRROR_SCRIPT,
        READINESS_GATE_SNAPSHOT_SCRIPT,
    ):
        assert script.is_file()
        text = script.read_text(encoding="utf-8")
        assert taxonomy_ref in text
        assert "§10" in text or "section 10" in text.lower()
        assert "review-input-only" in text.lower() or "review input only" in text.lower()
        assert "non-authorizing" in text.lower()
        assert "broker" in text.lower() or "exchange" in text.lower()
        assert "live" in text.lower()
        assert "preflight" in text.lower()
        assert "scheduler" in text.lower() or "operator" in text.lower()
        assert "does not override" in text.lower() or "do not override" in text.lower()


def test_readiness_ledger_bounded_observation_adapter_cross_ref_aligned() -> None:
    assert READINESS_LEDGER_SCRIPT.is_file()
    text = READINESS_LEDGER_SCRIPT.read_text(encoding="utf-8")
    assert "RUNTIME_LANE_TAXONOMY_AUTHORITY_LEVELS_CONTRACT_V0.md" in text
    assert "§10" in text or "section 10" in text.lower()
    assert "bounded observation" in text.lower()
    assert "run_paper_only_bounded_observation_adapter_v0.py" in text or (
        "shadow_bounded_observation_" in text and "testnet_bounded_observation_" in text
    )
    assert "shadow_bounded_observation_" in text
    assert "testnet_bounded_observation_" in text
    assert "review-input-only" in text.lower() or "review input only" in text.lower()
    assert "non-authorizing" in text.lower()
    assert "broker" in text.lower() or "exchange" in text.lower()
    assert "live" in text.lower()
    assert "preflight" in text.lower()
    assert "scheduler" in text.lower() or "operator" in text.lower()
    assert "does not override" in text.lower() or "do not override" in text.lower()
    assert "--execute" in text or "adapter" in text.lower()
    assert "stage-3" in text.lower() or "stage 3" in text.lower()


def test_bounded_observation_adapters_taxonomy_cross_ref_aligned() -> None:
    text = _spec_text()
    for marker in (
        "BOUNDED_OBSERVATION_ADAPTERS_TAXONOMY_INDEXED=true",
        "BOUNDED_OBSERVATION_ADAPTERS_REVIEW_INPUT_ONLY=true",
        "BOUNDED_OBSERVATION_ADAPTERS_STAGE3_EXECUTE_GATED=true",
        "BOUNDED_OBSERVATION_ADAPTERS_NO_LIVE_BROKER_EXCHANGE_AUTHORITY=true",
    ):
        assert marker in text
    assert "run_paper_only_bounded_observation_adapter_v0.py" in text
    assert "run_shadow_bounded_observation_adapter_v0.py" in text
    assert "run_testnet_bounded_observation_adapter_v0.py" in text
    assert "plan-only default" in text.lower() or "plan-only" in text.lower()
    assert "Stage-3" in text or "stage-3" in text.lower()
    assert "review input only" in text.lower() or "review_input_only" in text
    assert "non-authorizing" in text.lower()
    assert "broker" in text.lower()
    assert "Live" in text or "live" in text.lower()
    assert "SCHEDULER_BOUNDARY_HARD_BLOCK_CONTRACT_V0.md" in text
    assert "PAPER_SHADOW_247_PREFLIGHT_CONTRACT_V0.md" in text
    assert "operator" in text.lower()
    assert "Master V2" in text or "Double Play" in text
    assert "FORBIDDEN_PROMOTION" in text


def test_bounded_observation_adapter_taxonomy_reciprocal_pointer_aligned() -> None:
    taxonomy_ref = "RUNTIME_LANE_TAXONOMY_AUTHORITY_LEVELS_CONTRACT_V0.md"
    for script in (
        PAPER_BOUNDED_ADAPTER_SCRIPT,
        SHADOW_BOUNDED_ADAPTER_SCRIPT,
        TESTNET_BOUNDED_ADAPTER_SCRIPT,
    ):
        assert script.is_file()
        text = script.read_text(encoding="utf-8")
        assert taxonomy_ref in text
        assert "§10" in text or "section 10" in text.lower()
        assert "review-input-only" in text.lower() or "review input only" in text.lower()
        assert "non-authorizing" in text.lower()
        assert "broker" in text.lower() or "exchange" in text.lower()
        assert "live" in text.lower()
        assert "preflight" in text.lower()
        assert "scheduler" in text.lower() or "operator" in text.lower()
        assert "does not override" in text.lower() or "do not override" in text.lower()


def test_bounded_observation_review_scripts_taxonomy_cross_ref_aligned() -> None:
    text = _spec_text()
    for marker in (
        "BOUNDED_OBSERVATION_REVIEW_SCRIPTS_TAXONOMY_INDEXED=true",
        "BOUNDED_OBSERVATION_REVIEW_SCRIPTS_REVIEW_INPUT_ONLY=true",
        "BOUNDED_OBSERVATION_REVIEW_SCRIPTS_NO_EXECUTE_AUTHORITY=true",
        "BOUNDED_OBSERVATION_REVIEW_SCRIPTS_NO_LIVE_BROKER_EXCHANGE_AUTHORITY=true",
    ):
        assert marker in text
    assert "review_shadow_bounded_observation_evidence_v0.py" in text
    assert "review_testnet_bounded_observation_evidence_v0.py" in text
    assert "review input only" in text.lower() or "review_input_only" in text
    assert "non-authorizing" in text.lower() or "non-executing" in text.lower()
    assert "does not execute adapters" in text.lower() or "does not execute adapter" in text.lower()
    assert "broker" in text.lower()
    assert "Live" in text or "live" in text.lower()
    assert "SCHEDULER_BOUNDARY_HARD_BLOCK_CONTRACT_V0.md" in text or "scheduler" in text.lower()
    assert "PAPER_SHADOW_247_PREFLIGHT_CONTRACT_V0.md" in text or "preflight" in text.lower()
    assert "operator" in text.lower()
    assert "FORBIDDEN_PROMOTION" in text
    assert "run_shadow_bounded_observation_adapter_v0.py" in text
    assert "run_testnet_bounded_observation_adapter_v0.py" in text


def test_bounded_observation_review_script_taxonomy_reciprocal_pointer_aligned() -> None:
    taxonomy_ref = "RUNTIME_LANE_TAXONOMY_AUTHORITY_LEVELS_CONTRACT_V0.md"
    for script in (SHADOW_BOUNDED_REVIEW_SCRIPT, TESTNET_BOUNDED_REVIEW_SCRIPT):
        assert script.is_file()
        text = script.read_text(encoding="utf-8")
        assert taxonomy_ref in text
        assert "§10" in text or "section 10" in text.lower()
        assert "review-input-only" in text.lower() or "review input only" in text.lower()
        assert "non-authorizing" in text.lower()
        assert "broker" in text.lower() or "exchange" in text.lower()
        assert "live" in text.lower()
        assert "preflight" in text.lower()
        assert "scheduler" in text.lower() or "operator" in text.lower()
        assert "does not execute" in text.lower()
        assert "does not override" in text.lower() or "do not override" in text.lower()


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


def test_p91_post_stop_wrapper_hint_marker_aligned() -> None:
    assert P91_SCRIPT.is_file()
    text = _spec_text()
    for marker in (
        "P91_POST_STOP_WRAPPER_HINTS_IMPLEMENTED=true",
        "P91_POST_STOP_WRAPPER_REFERENCED=true",
        "P91_POST_STOP_P79_ARCHIVE_VERIFY_HINT_REFERENCED=true",
        "P91_POST_STOP_HINT_ONLY=true",
        "P91_POST_STOP_WRAPPER_NOT_EXECUTED=true",
        "P91_POST_STOP_PACK_NOT_EXECUTED=true",
        "P91_POST_STOP_P79_VERIFY_NOT_EXECUTED=true",
        "P91_POST_STOP_OPERATOR_EXPLICIT_REQUIRED=true",
        "P91_POST_STOP_EVIDENCE_NON_AUTHORIZING=true",
    ):
        assert marker in text
    assert "p91_audit_snapshot_runner_v1.sh" in text
    assert "P91_POST_STOP_PRIMARY_EVIDENCE_OPERATOR_HINTS.txt" in text
    assert "run_online_readiness_post_stop_pack_v0.sh" in text
    assert "--p79-archive-verify" in text
    assert "does not** execute wrapper" in text or "does not execute wrapper" in text.lower()
    assert "operator must run" in text.lower() or "explicitly when durable" in text
    assert "non-authorizing" in text.lower()
    assert "No** launchctl" in text or "no launchctl" in text.lower()
    assert "audit/snapshot hygiene" in text.lower() or "audit snapshot" in text.lower()


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
    assert "p91_audit_snapshot_runner_v1.sh" in preflight
    assert "operator-invoked" in preflight.lower()
    assert "non-authorizing" in preflight.lower()


def test_market_dashboard_f5_non_authority_taxonomy_cross_ref_aligned() -> None:
    assert MARKET_DASHBOARD_SPEC.is_file()
    taxonomy = _spec_text()
    market = MARKET_DASHBOARD_SPEC.read_text(encoding="utf-8")
    for marker in (
        "MARKET_DASHBOARD_READ_ONLY_NON_AUTHORITY=true",
        "MARKET_DASHBOARD_NO_APPROVAL_AUTHORITY=true",
        "MARKET_DASHBOARD_NO_LIVE_BROKER_EXCHANGE_AUTHORITY=true",
    ):
        assert marker in taxonomy
    assert "FUTURES_READ_ONLY_MARKET_DASHBOARD_CONTRACT_V0.md" in taxonomy
    assert "`dashboard`" in taxonomy
    assert "review_input_only" in taxonomy
    assert "FORBIDDEN_PROMOTION_DASHBOARD_NOTION_DOCS_AI_TO_APPROVAL" in taxonomy
    assert "RUNTIME_LANE_TAXONOMY_AUTHORITY_LEVELS_CONTRACT_V0.md" in market
    assert "Lane taxonomy cross-reference" in market
    assert "Dashboard ≠ Freigabe" in market or "dashboard" in market.lower()
    assert "non-authorizing" in market.lower()
    assert "does not grant" in market.lower() or "does not permit" in market.lower()
    assert "Master V2" in market
    assert "Double Play" in market
    assert "Live" in market
    assert "broker" in market.lower() or "exchange" in market.lower()
    assert "scheduler" in market.lower() or "runtime" in market.lower()


def test_market_surface_v0_taxonomy_cross_ref_aligned() -> None:
    assert MARKET_SURFACE_V0.is_file()
    assert MARKET_DASHBOARD_SPEC.is_file()
    surface = MARKET_SURFACE_V0.read_text(encoding="utf-8")
    taxonomy = _spec_text()
    assert "RUNTIME_LANE_TAXONOMY_AUTHORITY_LEVELS_CONTRACT_V0.md" in surface
    assert "§7h" in surface or "7h" in surface
    assert "Lane taxonomy cross-reference" in surface
    assert "`dashboard`" in surface
    assert "review_input_only" in surface
    assert "FUTURES_READ_ONLY_MARKET_DASHBOARD_CONTRACT_V0.md" in surface
    assert "double-play" in surface.lower()
    assert "Master V2" in surface
    assert "Double Play" in surface
    assert "non-authorizing" in surface.lower()
    assert "review input only" in surface.lower() or "review_input_only" in surface
    assert "FORBIDDEN_PROMOTION_DASHBOARD_NOTION_DOCS_AI_TO_APPROVAL" in surface
    assert "Live" in surface or "live" in surface.lower()
    assert "broker" in surface.lower() or "exchange" in surface.lower()
    assert "does not" in surface.lower() or "do not" in surface.lower()
    assert "MARKET_SURFACE_V0.md" in taxonomy
    assert "does not replace the F5 contract owner" in taxonomy or "F5 contract owner" in taxonomy


def test_f5_contract_market_surface_bidirectional_crossref_v0() -> None:
    """F5 contract and Market Surface v0 cross-reference each other; separation preserved."""
    assert MARKET_DASHBOARD_SPEC.is_file()
    assert MARKET_SURFACE_V0.is_file()
    f5 = MARKET_DASHBOARD_SPEC.read_text(encoding="utf-8")
    surface = MARKET_SURFACE_V0.read_text(encoding="utf-8")
    assert "MARKET_SURFACE_V0.md" in f5
    assert "orthogonal" in f5.lower()
    assert "does not replace" in f5.lower()
    assert "Market-Airport" in f5 or "market-airport" in f5.lower()
    assert "FUTURES_READ_ONLY_MARKET_DASHBOARD_CONTRACT_V0.md" in surface
    assert "replace f5" in surface.lower()
    assert "Guardrails" in surface
    assert "Freigabe" in surface
    assert "AI" in surface and "Authority" in surface


def test_autonomy_stage_authority_crosswalk_section_present() -> None:
    text = _spec_text()
    assert "## 12. Autonomy stage authority crosswalk" in text
    assert "Reuse-before-new" in text
    assert "§12" in text or "section 12" in text.lower()


def test_all_autonomy_stages_0_through_7_present() -> None:
    text = _spec_text()
    for stage in REQUIRED_AUTONOMY_STAGES:
        assert f"| `{stage}` |" in text, f"missing stage {stage!r} in crosswalk table"


def test_autonomy_crosswalk_invariant_literals_present() -> None:
    text = _spec_text()
    for marker in AUTONOMY_CROSSWALK_MARKERS:
        assert marker in text
    assert "L6 EXEC" in text
    assert "go_decision_granted" in text
    assert (
        "Permanently operator-only" in text or "Permanently operator-only or external-gated" in text
    )


def test_autonomy_crosswalk_forbidden_promotions_referenced() -> None:
    text = _spec_text()
    for literal in (
        "FORBIDDEN_PROMOTION_SHADOW_TO_TESTNET_LIVE",
        "FORBIDDEN_PROMOTION_PAPER_TO_SHADOW_TESTNET_LIVE",
        "FORBIDDEN_PROMOTION_TESTNET_PASS_TO_LIVE_BROKER_EXCHANGE",
        "FORBIDDEN_PROMOTION_CANARY_DOCS_TO_LIVE",
        "FORBIDDEN_PROMOTION_GO_NO_GO_TEMPLATE_TO_GO_DECISION",
        "FORBIDDEN_PROMOTION_DASHBOARD_NOTION_DOCS_AI_TO_APPROVAL",
    ):
        assert literal in text


def test_autonomy_crosswalk_canonical_owner_crosslinks() -> None:
    text = _spec_text()
    for owner in (
        "MASTER_V2_GO_LIVE_ROADMAP_V0.md",
        "MASTER_V2_DECISION_AUTHORITY_MAP_V1.md",
        "MASTER_V2_LEARNING_AI_AUTONOMY_INVENTORY_V1.md",
        "AI_AUTONOMY_CONTROL_CENTER.md",
        "CANARY_LIVE_ENTRY_CRITERIA.md",
    ):
        assert owner in text


def test_no_duplicate_autonomy_crosswalk_spec_introduced() -> None:
    specs_dir = REPO_ROOT / "docs" / "ops" / "specs"
    for fragment in FORBIDDEN_DUPLICATE_SPEC_PATHS:
        if fragment.startswith("docs/"):
            continue
        matches = list(specs_dir.glob(f"*{fragment}*"))
        assert matches == [], f"duplicate spec surface: {matches}"


def test_roadmap_crosslinks_taxonomy_section_12() -> None:
    assert MASTER_V2_ROADMAP.is_file()
    roadmap = MASTER_V2_ROADMAP.read_text(encoding="utf-8")
    taxonomy = _spec_text()
    assert "RUNTIME_LANE_TAXONOMY_AUTHORITY_LEVELS_CONTRACT_V0.md" in roadmap
    assert "§12" in roadmap or "Autonomy Stage Authority Crosswalk" in roadmap
    assert "MASTER_V2_GO_LIVE_ROADMAP_V0.md" in taxonomy
    assert "§3.1" in taxonomy
    assert "non-authorizing" in roadmap.lower() or "non-authorizing" in taxonomy.lower()
