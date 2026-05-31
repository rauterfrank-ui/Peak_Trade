"""Static source contract tests for scheduler dry-run hardening v0 (offline)."""

from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
RUN_SCHEDULER = REPO_ROOT / "scripts" / "run_scheduler.py"
SECTION5_DOC = (
    REPO_ROOT / "docs" / "ops" / "planning" / "SECTION5_PREFLIGHT_GAP_OWNER_MAP_CONTRACT_V0.md"
)
DOCS_TRUTH_MAP = REPO_ROOT / "docs" / "ops" / "registry" / "DOCS_TRUTH_MAP.md"
GAP3_TESTS = REPO_ROOT / "tests" / "ops" / "test_gap3_execute_command_contract_v0.py"
GAP6_TESTS = REPO_ROOT / "tests" / "ops" / "test_gap6_dry_run_proof_criteria_contract_v0.py"
GAP6_DRIFT_GUARD_TESTS = (
    REPO_ROOT / "tests" / "ops" / "test_gap6_external_repo_drift_guard_contract_v0.py"
)
GAP1_TESTS = REPO_ROOT / "tests" / "ops" / "test_gap1_execute_entrypoint_contract_v0.py"
GAP1_DRIFT_GUARD_TESTS = (
    REPO_ROOT / "tests" / "ops" / "test_gap1_execute_entrypoint_drift_guard_contract_v0.py"
)
GAP2_TESTS = REPO_ROOT / "tests" / "ops" / "test_gap2_canonical_job_set_contract_v0.py"
GAP2_BOUNDARY_TESTS = (
    REPO_ROOT / "tests" / "ops" / "test_gap2_job_set_boundary_drift_guard_contract_v0.py"
)
GAP2_GAP3_DEPENDENCY_TESTS = (
    REPO_ROOT / "tests" / "ops" / "test_gap2_gap3_command_dependency_contract_v0.py"
)
GAP4_TESTS = REPO_ROOT / "tests" / "ops" / "test_gap4_output_evidence_paths_contract_v0.py"
GAP4_DRIFT_GUARD_TESTS = (
    REPO_ROOT / "tests" / "ops" / "test_gap4_output_evidence_paths_drift_guard_contract_v0.py"
)
GAP5_TESTS = REPO_ROOT / "tests" / "ops" / "test_gap5_stop_criteria_contract_v0.py"
GAP5_DRIFT_GUARD_TESTS = (
    REPO_ROOT / "tests" / "ops" / "test_gap5_stop_criteria_drift_guard_contract_v0.py"
)
GAP5_GAP4_DEPENDENCY_TESTS = (
    REPO_ROOT / "tests" / "ops" / "test_gap5_gap4_durable_evidence_dependency_contract_v0.py"
)
GAP5_REHEARSAL_CLASSIFICATION_TESTS = (
    REPO_ROOT / "tests" / "ops" / "test_gap5_stop_rehearsal_evidence_classification_contract_v0.py"
)
GAP2A1_TESTS = (
    REPO_ROOT / "tests" / "ops" / "test_gap2a1_primary_evidence_enforcement_contract_v0.py"
)
GAP2A1_DRIFT_GUARD_TESTS = (
    REPO_ROOT
    / "tests"
    / "ops"
    / "test_gap2a1_primary_evidence_enforcement_drift_guard_contract_v0.py"
)
GAP4_GAP2A1_DEPENDENCY_TESTS = (
    REPO_ROOT / "tests" / "ops" / "test_gap4_gap2a1_primary_evidence_dependency_contract_v0.py"
)
GAP7_TESTS = REPO_ROOT / "tests" / "ops" / "test_gap7_risk_boundary_criteria_contract_v0.py"
GAP7_DRIFT_GUARD_TESTS = (
    REPO_ROOT / "tests" / "ops" / "test_gap7_risk_boundary_drift_guard_contract_v0.py"
)
HARD_GATE_TESTS = (
    REPO_ROOT / "tests" / "ops" / "test_run_primary_evidence_retention_hard_gate_v0.py"
)
BOUNDARY_TESTS = REPO_ROOT / "tests" / "ops" / "test_scheduler_boundary_hard_block_contract_v0.py"
REAL_CONFIG_TICK_TESTS = (
    REPO_ROOT / "tests" / "test_scheduler_real_config_single_tick_dry_run_contract_v0.py"
)
JOB_CONFIG_TESTS = (
    REPO_ROOT / "tests" / "ops" / "test_paper_shadow_247_runtime_scheduler_job_config_v0.py"
)
SNAPSHOT_TESTS = REPO_ROOT / "tests" / "ops" / "test_snapshot_operator_stop_signals.py"

PACKAGE_MARKER = "SCHEDULER_DRY_RUN_HARDENING_SOURCE_CONTRACT_V0=true"
_MARKER_TRUE = "=true"

OWNER_REFERENCES_V0 = (
    "tests/ops/test_gap1_execute_entrypoint_contract_v0.py",
    "tests/ops/test_gap1_execute_entrypoint_drift_guard_contract_v0.py",
    "tests/ops/test_gap2_canonical_job_set_contract_v0.py",
    "tests/ops/test_gap2_job_set_boundary_drift_guard_contract_v0.py",
    "tests/ops/test_gap2_gap3_command_dependency_contract_v0.py",
    "tests/ops/test_gap3_execute_command_contract_v0.py",
    "tests/ops/test_gap4_output_evidence_paths_contract_v0.py",
    "tests/ops/test_gap4_output_evidence_paths_drift_guard_contract_v0.py",
    "tests/ops/test_gap5_stop_criteria_contract_v0.py",
    "tests/ops/test_gap5_stop_criteria_drift_guard_contract_v0.py",
    "tests/ops/test_gap5_gap4_durable_evidence_dependency_contract_v0.py",
    "tests/ops/test_gap5_stop_rehearsal_evidence_classification_contract_v0.py",
    "tests/ops/test_gap2a1_primary_evidence_enforcement_contract_v0.py",
    "tests/ops/test_gap2a1_primary_evidence_enforcement_drift_guard_contract_v0.py",
    "tests/ops/test_gap4_gap2a1_primary_evidence_dependency_contract_v0.py",
    "tests/ops/test_gap7_risk_boundary_criteria_contract_v0.py",
    "tests/ops/test_gap7_risk_boundary_drift_guard_contract_v0.py",
    "tests/ops/test_gap6_dry_run_proof_criteria_contract_v0.py",
    "tests/ops/test_gap6_external_repo_drift_guard_contract_v0.py",
    "tests/ops/test_run_primary_evidence_retention_hard_gate_v0.py",
    "tests/ops/test_snapshot_operator_stop_signals.py",
    "tests/ops/test_scheduler_boundary_hard_block_contract_v0.py",
    "tests/test_scheduler_real_config_single_tick_dry_run_contract_v0.py",
    "tests/ops/test_paper_shadow_247_runtime_scheduler_job_config_v0.py",
    "scripts/run_scheduler.py",
    "docs/ops/planning/SECTION5_PREFLIGHT_GAP_OWNER_MAP_CONTRACT_V0.md",
)


def _run_scheduler_source() -> str:
    return RUN_SCHEDULER.read_text(encoding="utf-8")


def _this_module_source() -> str:
    return Path(__file__).read_text(encoding="utf-8")


def test_scheduler_dry_run_hardening_source_contract_marker_present_v0() -> None:
    assert PACKAGE_MARKER in _this_module_source()


def test_run_scheduler_argparse_dry_run_flag_anchored_v0() -> None:
    source = _run_scheduler_source()
    assert 'parser.add_argument("--dry-run"' in source
    assert "dry_run=args.dry_run" in source


def test_run_scheduler_argparse_once_flag_anchored_v0() -> None:
    source = _run_scheduler_source()
    assert '"--once", action="store_true"' in source
    assert "once=args.once" in source


def test_non_dry_run_path_remains_guarded_before_loop_v0() -> None:
    source = _run_scheduler_source()
    guard_block = source.split("if not args.dry_run:", 1)[1]
    assert "assert_scheduler_start_authorized" in guard_block
    guard_idx = source.index("if not args.dry_run:")
    auth_idx = source.index("assert_scheduler_start_authorized", guard_idx)
    loop_idx = source.index("return run_scheduler_loop", auth_idx)
    assert auth_idx < loop_idx


def test_dry_run_output_banner_contract_anchored_v0() -> None:
    source = _run_scheduler_source()
    assert "DRY-RUN: Keine echte Ausführung" in source
    assert "Mode: {'ONCE' if once else 'CONTINUOUS'}" in source
    assert "SCHEDULER BEENDET" in source
    assert "Iterationen:" in source


def test_primary_evidence_enforce_incompatible_with_dry_run_v0() -> None:
    source = _run_scheduler_source()
    assert "primary_evidence_enforce and dry_run" in source
    assert "incompatible with --dry-run" in source
    assert "validate_scheduler_evidence_cli" in source


def test_tmp_evidence_boundary_uses_existing_is_under_tmp_helper_v0() -> None:
    source = _run_scheduler_source()
    assert "from scripts.ops.primary_evidence_retention_v0 import is_under_tmp" in source
    assert "is_under_tmp(evidence_dir)" in source
    assert "is_under_tmp(durable_closeout_dest_dir)" in source


def test_hardening_module_does_not_claim_verified_or_scheduler_authorized_v0() -> None:
    lines = {line.strip() for line in _this_module_source().splitlines()}
    forbidden = (
        "GAP1_EXECUTE_ENTRYPOINT_VERIFIED" + _MARKER_TRUE,
        "GAP2_CANONICAL_JOB_SET_VERIFIED" + _MARKER_TRUE,
        "GAP3_EXECUTE_COMMAND_VERIFIED" + _MARKER_TRUE,
        "GAP4_OUTPUT_EVIDENCE_PATHS_VERIFIED" + _MARKER_TRUE,
        "GAP4_OUTPUT_EVIDENCE_DEFAULT_ON" + _MARKER_TRUE,
        "GAP5_TYPE2_WAIVER_GRANTED" + _MARKER_TRUE,
        "GAP5_STOP_REHEARSAL_EXECUTED" + _MARKER_TRUE,
        "GAP5_STOP_PROOF_ACCEPTED" + _MARKER_TRUE,
        "GAP5_RUNTIME_STOP_AUTHORITY_CHANGED" + _MARKER_TRUE,
        "GAP5_SCHEDULER_EXECUTION_AUTHORIZED" + _MARKER_TRUE,
        "GAP5_STOP_CRITERIA_DEFAULT_ON" + _MARKER_TRUE,
        "GAP7_RISK_BOUNDARY_VERIFIED" + _MARKER_TRUE,
        "GAP7_RISK_KILLSWITCH_AUTHORITY_CHANGED" + _MARKER_TRUE,
        "GAP7_RISK_KILLSWITCH_RUNTIME_CHANGED" + _MARKER_TRUE,
        "GAP7_MASTER_V2_DOUBLE_PLAY_CHANGED" + _MARKER_TRUE,
        "GAP7_BULL_BEAR_SCOPE_CAPITAL_CHANGED" + _MARKER_TRUE,
        "GAP7_EXECUTION_LIVE_GATES_CHANGED" + _MARKER_TRUE,
        "GAP7_SCHEDULER_EXECUTION_AUTHORIZED" + _MARKER_TRUE,
        "GAP7_RUNTIME_APPROVED" + _MARKER_TRUE,
        "GAP7_RISK_BOUNDARY_DEFAULT_ON" + _MARKER_TRUE,
        "GAP6_DRY_RUN_RC0_OBSERVED" + _MARKER_TRUE,
        "GAP6_DRY_RUN_PROOF_VERIFIED" + _MARKER_TRUE,
        "SCHEDULER_EXECUTION_AUTHORIZED" + _MARKER_TRUE,
        "PREFLIGHT_LIFT_GRANTED" + _MARKER_TRUE,
        "READY_FOR_OPERATOR_ARMING" + _MARKER_TRUE,
    )
    for marker in forbidden:
        assert marker not in lines


def test_section5_gap1_gap2_and_gap6_remain_unverified_and_non_authorizing_v0() -> None:
    section5 = SECTION5_DOC.read_text(encoding="utf-8")
    assert "GAP1_EXECUTE_ENTRYPOINT_VERIFIED=false" in section5
    assert "GAP1_SCHEDULER_EXECUTION_AUTHORIZED=false" in section5
    assert "GAP1_RUNTIME_APPROVED=false" in section5
    assert "GAP2_CANONICAL_JOB_SET_VERIFIED=false" in section5
    assert "GAP2_JOB_SET_ENABLED=false" in section5
    assert "GAP2_JOBS_TOML_CHANGED=false" in section5
    assert "GAP3_EXECUTE_COMMAND_VERIFIED=false" in section5
    assert "GAP4_OUTPUT_EVIDENCE_PATHS_VERIFIED=false" in section5
    assert "GAP4_OUTPUT_EVIDENCE_DEFAULT_ON=false" in section5
    assert "GAP5_TYPE2_WAIVER_GRANTED=false" in section5
    assert "GAP5_STOP_REHEARSAL_EXECUTED=false" in section5
    assert "GAP5_STOP_PROOF_ACCEPTED=false" in section5
    assert "GAP5_RUNTIME_STOP_AUTHORITY_CHANGED=false" in section5
    assert "GAP5_SCHEDULER_EXECUTION_AUTHORIZED=false" in section5
    assert "GAP5_STOP_CRITERIA_DEFAULT_ON=false" in section5
    assert "GAP7_RISK_BOUNDARY_VERIFIED=false" in section5
    assert "GAP7_RISK_KILLSWITCH_AUTHORITY_CHANGED=false" in section5
    assert "GAP7_RISK_KILLSWITCH_RUNTIME_CHANGED=false" in section5
    assert "GAP7_MASTER_V2_DOUBLE_PLAY_CHANGED=false" in section5
    assert "GAP7_BULL_BEAR_SCOPE_CAPITAL_CHANGED=false" in section5
    assert "GAP7_EXECUTION_LIVE_GATES_CHANGED=false" in section5
    assert "GAP7_SCHEDULER_EXECUTION_AUTHORIZED=false" in section5
    assert "GAP7_RUNTIME_APPROVED=false" in section5
    assert "GAP7_RISK_BOUNDARY_DEFAULT_ON=false" in section5
    assert "GAP6_DRY_RUN_RC0_OBSERVED=false" in section5
    assert "GAP6_DRY_RUN_PROOF_VERIFIED=false" in section5
    assert "PREFLIGHT_REMAINS_BLOCKED=true" in section5


def test_reciprocal_owner_references_exist_v0() -> None:
    for owner_rel in OWNER_REFERENCES_V0:
        assert (REPO_ROOT / owner_rel).is_file(), f"missing owner reference: {owner_rel!r}"


def test_gap1_owner_crosslinks_scheduler_dry_run_hardening_source_contract_v0() -> None:
    text = GAP1_TESTS.read_text(encoding="utf-8")
    assert "test_scheduler_dry_run_hardening_source_contract_v0.py" in text
    assert PACKAGE_MARKER in text


def test_gap1_drift_guard_owner_crosslinks_scheduler_dry_run_hardening_source_contract_v0() -> None:
    text = GAP1_DRIFT_GUARD_TESTS.read_text(encoding="utf-8")
    assert "test_scheduler_dry_run_hardening_source_contract_v0.py" in text
    assert "GAP1_RUNTIME_APPROVED=false" in text
    assert "GAP1_SCHEDULER_EXECUTION_AUTHORIZED=false" in text
    assert "GAP1_ENTRYPOINT_DRY_RUN_ONLY=true" in text
    hardening_text = _this_module_source()
    assert "test_gap1_execute_entrypoint_drift_guard_contract_v0.py" in hardening_text
    lines = {line.strip() for line in hardening_text.splitlines()}
    assert ("GAP1_EXECUTE_ENTRYPOINT_VERIFIED" + _MARKER_TRUE) not in lines
    assert ("GAP1_RUNTIME_APPROVED" + _MARKER_TRUE) not in lines
    assert ("GAP1_SCHEDULER_EXECUTION_AUTHORIZED" + _MARKER_TRUE) not in lines


def test_gap2_owner_crosslinks_scheduler_dry_run_hardening_source_contract_v0() -> None:
    text = GAP2_TESTS.read_text(encoding="utf-8")
    assert "test_scheduler_dry_run_hardening_source_contract_v0.py" in text
    assert PACKAGE_MARKER in text


def test_gap2_boundary_owner_crosslinks_scheduler_dry_run_hardening_source_contract_v0() -> None:
    text = GAP2_BOUNDARY_TESTS.read_text(encoding="utf-8")
    assert "test_scheduler_dry_run_hardening_source_contract_v0.py" in text
    assert "GAP2_CANONICAL_JOB_SET_VERIFIED=false" in text
    assert "GAP2_JOB_SET_ENABLED=false" in text
    hardening_text = _this_module_source()
    assert "test_gap2_job_set_boundary_drift_guard_contract_v0.py" in hardening_text
    lines = {line.strip() for line in hardening_text.splitlines()}
    assert ("GAP2_CANONICAL_JOB_SET_VERIFIED" + _MARKER_TRUE) not in lines


def test_gap3_owner_crosslinks_scheduler_dry_run_hardening_source_contract_v0() -> None:
    text = GAP3_TESTS.read_text(encoding="utf-8")
    assert "test_scheduler_dry_run_hardening_source_contract_v0.py" in text
    assert PACKAGE_MARKER in text


def test_gap2_gap3_dependency_owner_crosslinks_scheduler_dry_run_hardening_source_contract_v0() -> (
    None
):
    text = GAP2_GAP3_DEPENDENCY_TESTS.read_text(encoding="utf-8")
    assert "test_scheduler_dry_run_hardening_source_contract_v0.py" in text
    assert "GAP3_EXECUTE_COMMAND_VERIFIED=false" in text
    assert "GAP2_CANONICAL_JOB_SET_VERIFIED=false" in text
    hardening_text = _this_module_source()
    assert "test_gap2_gap3_command_dependency_contract_v0.py" in hardening_text
    lines = {line.strip() for line in hardening_text.splitlines()}
    assert ("GAP3_EXECUTE_COMMAND_VERIFIED" + _MARKER_TRUE) not in lines


def test_gap4_owner_crosslinks_scheduler_dry_run_hardening_source_contract_v0() -> None:
    text = GAP4_TESTS.read_text(encoding="utf-8")
    assert "test_scheduler_dry_run_hardening_source_contract_v0.py" in text
    assert PACKAGE_MARKER in text


def test_gap4_drift_guard_owner_crosslinks_scheduler_dry_run_hardening_source_contract_v0() -> None:
    text = GAP4_DRIFT_GUARD_TESTS.read_text(encoding="utf-8")
    assert "test_scheduler_dry_run_hardening_source_contract_v0.py" in text
    assert "test_gap4_output_evidence_paths_contract_v0.py" in text
    assert "GAP4_OUTPUT_EVIDENCE_PATHS_VERIFIED=false" in text


def test_gap5_owner_crosslinks_scheduler_dry_run_hardening_source_contract_v0() -> None:
    text = GAP5_TESTS.read_text(encoding="utf-8")
    assert "test_scheduler_dry_run_hardening_source_contract_v0.py" in text
    assert PACKAGE_MARKER in text


def test_gap5_drift_guard_owner_crosslinks_scheduler_dry_run_hardening_source_contract_v0() -> None:
    text = GAP5_DRIFT_GUARD_TESTS.read_text(encoding="utf-8")
    assert "test_scheduler_dry_run_hardening_source_contract_v0.py" in text
    assert "test_gap5_stop_criteria_contract_v0.py" in text
    assert "GAP5_STOP_REHEARSAL_EXECUTED=false" in text


def test_gap5_gap4_dependency_owner_crosslinks_scheduler_dry_run_hardening_source_contract_v0() -> (
    None
):
    text = GAP5_GAP4_DEPENDENCY_TESTS.read_text(encoding="utf-8")
    assert "test_scheduler_dry_run_hardening_source_contract_v0.py" in text
    assert "test_gap4_output_evidence_paths_drift_guard_contract_v0.py" in text
    assert "test_gap5_stop_criteria_drift_guard_contract_v0.py" in text
    assert "GAP5_STOP_PROOF_ACCEPTED=false" in text


def test_gap5_rehearsal_classification_owner_crosslinks_scheduler_dry_run_hardening_source_contract_v0() -> (
    None
):
    text = GAP5_REHEARSAL_CLASSIFICATION_TESTS.read_text(encoding="utf-8")
    assert "test_scheduler_dry_run_hardening_source_contract_v0.py" in text
    assert "GAP5_STOP_REHEARSAL_EXECUTED=false" in text
    assert "GAP5_STOP_PROOF_ACCEPTED=false" in text
    hardening_text = _this_module_source()
    assert "test_gap5_stop_rehearsal_evidence_classification_contract_v0.py" in hardening_text
    lines = {line.strip() for line in hardening_text.splitlines()}
    assert ("GAP5_STOP_REHEARSAL_EXECUTED" + _MARKER_TRUE) not in lines
    assert ("GAP5_STOP_PROOF_ACCEPTED" + _MARKER_TRUE) not in lines


def test_gap2a1_drift_guard_owner_crosslinks_scheduler_dry_run_hardening_source_contract_v0() -> (
    None
):
    text = GAP2A1_DRIFT_GUARD_TESTS.read_text(encoding="utf-8")
    assert "test_scheduler_dry_run_hardening_source_contract_v0.py" in text
    assert "GAP2A1_PRIMARY_EVIDENCE_ENFORCED=false" in text
    assert "GAP2A1_ENFORCEMENT_OPT_IN_ONLY=true" in text
    hardening_text = _this_module_source()
    assert "test_gap2a1_primary_evidence_enforcement_drift_guard_contract_v0.py" in hardening_text
    lines = {line.strip() for line in hardening_text.splitlines()}
    assert ("GAP2A1_PRIMARY_EVIDENCE_ENFORCED" + _MARKER_TRUE) not in lines
    assert ("GAP2A1_ENFORCEMENT_DEFAULT_ON" + _MARKER_TRUE) not in lines


def test_gap4_gap2a1_dependency_owner_crosslinks_scheduler_dry_run_hardening_source_contract_v0() -> (
    None
):
    text = GAP4_GAP2A1_DEPENDENCY_TESTS.read_text(encoding="utf-8")
    assert "test_scheduler_dry_run_hardening_source_contract_v0.py" in text
    assert "GAP4_OUTPUT_EVIDENCE_PATHS_VERIFIED=false" in text
    assert "GAP2A1_PRIMARY_EVIDENCE_ENFORCED=false" in text
    hardening_text = _this_module_source()
    assert "test_gap4_gap2a1_primary_evidence_dependency_contract_v0.py" in hardening_text
    lines = {line.strip() for line in hardening_text.splitlines()}
    assert ("GAP4_OUTPUT_EVIDENCE_PATHS_VERIFIED" + _MARKER_TRUE) not in lines
    assert ("GAP2A1_PRIMARY_EVIDENCE_ENFORCED" + _MARKER_TRUE) not in lines


def test_gap7_owner_crosslinks_scheduler_dry_run_hardening_source_contract_v0() -> None:
    text = GAP7_TESTS.read_text(encoding="utf-8")
    assert "test_scheduler_dry_run_hardening_source_contract_v0.py" in text
    assert PACKAGE_MARKER in text


def test_gap7_drift_guard_owner_crosslinks_scheduler_dry_run_hardening_source_contract_v0() -> None:
    text = GAP7_DRIFT_GUARD_TESTS.read_text(encoding="utf-8")
    assert "test_scheduler_dry_run_hardening_source_contract_v0.py" in text
    assert "test_gap7_risk_boundary_criteria_contract_v0.py" in text
    assert "GAP7_RISK_BOUNDARY_VERIFIED=false" in text
    hardening_text = _this_module_source()
    assert "test_gap7_risk_boundary_drift_guard_contract_v0.py" in hardening_text
    lines = {line.strip() for line in hardening_text.splitlines()}
    assert ("GAP7_RISK_BOUNDARY_VERIFIED" + _MARKER_TRUE) not in lines
    assert ("GAP7_RISK_KILLSWITCH_AUTHORITY_CHANGED" + _MARKER_TRUE) not in lines
    assert ("GAP7_EXECUTION_LIVE_GATES_CHANGED" + _MARKER_TRUE) not in lines


def test_gap6_owner_crosslinks_scheduler_dry_run_hardening_source_contract_v0() -> None:
    text = GAP6_TESTS.read_text(encoding="utf-8")
    assert "test_scheduler_dry_run_hardening_source_contract_v0.py" in text
    assert PACKAGE_MARKER in text


def test_gap6_drift_guard_owner_crosslinks_scheduler_dry_run_hardening_source_contract_v0() -> None:
    text = GAP6_DRIFT_GUARD_TESTS.read_text(encoding="utf-8")
    assert "test_scheduler_dry_run_hardening_source_contract_v0.py" in text
    assert "test_gap6_dry_run_proof_criteria_contract_v0.py" in text
    assert "GAP6_DRY_RUN_RC0_OBSERVED=false" in text


def test_boundary_owner_crosslinks_scheduler_dry_run_hardening_source_contract_v0() -> None:
    text = BOUNDARY_TESTS.read_text(encoding="utf-8")
    assert "test_scheduler_dry_run_hardening_source_contract_v0.py" in text
    assert PACKAGE_MARKER in text


def test_real_config_tick_owner_crosslinked_from_hardening_module_v0() -> None:
    assert "test_scheduler_real_config_single_tick_dry_run_contract_v0.py" in _this_module_source()
    assert REAL_CONFIG_TICK_TESTS.is_file()


def test_job_config_owner_crosslinked_from_hardening_module_v0() -> None:
    assert "test_paper_shadow_247_runtime_scheduler_job_config_v0.py" in _this_module_source()
    assert JOB_CONFIG_TESTS.is_file()


def test_hard_gate_owner_crosslinked_from_hardening_module_v0() -> None:
    assert "test_run_primary_evidence_retention_hard_gate_v0.py" in _this_module_source()
    assert HARD_GATE_TESTS.is_file()


def test_snapshot_owner_crosslinked_from_hardening_module_v0() -> None:
    assert "test_snapshot_operator_stop_signals.py" in _this_module_source()
    assert SNAPSHOT_TESTS.is_file()


def test_docs_truth_map_records_scheduler_dry_run_hardening_chronicle_v0() -> None:
    text = DOCS_TRUTH_MAP.read_text(encoding="utf-8")
    assert "Scheduler dry-run hardening source contract v0" in text
    assert "test_scheduler_dry_run_hardening_source_contract_v0.py" in text
    assert "test_gap3_execute_command_contract_v0.py" in text
    assert "test_gap6_dry_run_proof_criteria_contract_v0.py" in text
    assert "test_scheduler_boundary_hard_block_contract_v0.py" in text
