"""Static contract for Gap-1 execute entrypoint drift guard v0.

Reads repo markdown/source only. Never executes scheduler/runtime/stop/evidence helpers,
never reads external archive paths as pass/fail SSOT, and never treats entrypoint contract
presence, dry-run boundary markers, CLI parseability, or preflight readiness as repo
``GAP1_RUNTIME_APPROVED`` or scheduler execution authorization.
"""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SECTION5_DOC = (
    ROOT / "docs" / "ops" / "planning" / "SECTION5_PREFLIGHT_GAP_OWNER_MAP_CONTRACT_V0.md"
)
PREFLIGHT_CONTRACT = (
    ROOT / "docs" / "ops" / "runbooks" / "PAPER_SHADOW_247_PREFLIGHT_CONTRACT_V0.md"
)
RUN_SCHEDULER = ROOT / "scripts" / "run_scheduler.py"
GAP1_CONTRACT = ROOT / "tests" / "ops" / "test_gap1_execute_entrypoint_contract_v0.py"
HARDENING_OWNER = ROOT / "tests" / "ops" / "test_scheduler_dry_run_hardening_source_contract_v0.py"
FINAL_MACHINE_LINES_HEADER = "## Final Machine Lines"
GAP1_SECTION_HEADER = "## Gap 1 Execute Entrypoint Contract v0"
GAP1_RC0_OBSERVED_REFLECTION_HEADER = (
    "## Gap 1 Governed Execute Entrypoint Observed Evidence Reflection v0"
)
GAP4_GOVERNED_REFLECTION_HEADER = "## Gap 4 Governed Output Evidence Acceptance Reflection v0"
CANONICAL_BOUNDED_DRY_RUN_COMMAND_TIER2 = (
    "uv run python scripts/run_scheduler.py --config config/scheduler/jobs.toml "
    "--dry-run --once --verbose --include-tags paper_shadow_247,preflight,readonly"
)
_MARKER_TRUE = "=true"

GAP1_EXECUTE_ENTRYPOINT_PLANNED = True
GAP1_EXECUTE_ENTRYPOINT_VERIFIED = False
GAP1_RUNTIME_APPROVED = False
GAP1_SCHEDULER_EXECUTION_AUTHORIZED = False
GAP1_EXECUTE_ENTRYPOINT_DEFAULT_ON = False
GAP1_ENTRYPOINT_DRY_RUN_ONLY = True
ENTRYPOINT_CRITERIA_NOT_RUNTIME_APPROVAL = True
DRY_RUN_BOUNDARY_NOT_EXECUTION_AUTHORIZATION = True
PREFLIGHT_READINESS_NOT_SCHEDULER_EXECUTE = True
EVIDENCE_EQUALS_APPROVAL = False
CRITERIA_COMPLETE_EQUALS_GAP_CLOSED = False
FUTURE_EXECUTION_REQUIRES_EXPLICIT_OPT_IN_GO = True

DRIFT_GUARD_REQUIRED_FINAL_LINES = (
    "PREFLIGHT_REMAINS_BLOCKED=true",
    "READY_FOR_OPERATOR_ARMING=false",
    "PATH_B_LIFT_DISCUSSION_READY=false",
    "ALL_GAPS_CLOSED=false",
    "GAP1_EXECUTE_ENTRYPOINT_VERIFIED=false",
    "GAP1_RUNTIME_APPROVED=false",
    "GAP1_SCHEDULER_EXECUTION_AUTHORIZED=false",
    "GAP1_EXECUTE_ENTRYPOINT_DEFAULT_ON=false",
    "GAP2A1_PRIMARY_EVIDENCE_ENFORCED=false",
    "GAP4_OUTPUT_EVIDENCE_PATHS_VERIFIED=false",
    "GAP5_STOP_REHEARSAL_EXECUTED=false",
    "GAP5_STOP_PROOF_ACCEPTED=false",
    "GAP6_DRY_RUN_PROOF_ACCEPTED=false",
)

DRIFT_GUARD_FORBIDDEN_GAP1_REPO_TOKENS = (
    "GAP1_EXECUTE_ENTRYPOINT_RC0_OBSERVED=true",
    "GAP1_EXECUTE_ENTRYPOINT_RC0_OBSERVED_EXTERNAL=true",
    "GAP1_EXECUTE_ENTRYPOINT_VERIFIED=true",
    "GAP1_RUNTIME_APPROVED=true",
    "GAP1_SCHEDULER_EXECUTION_AUTHORIZED=true",
    "GAP1_EXECUTE_ENTRYPOINT_DEFAULT_ON=true",
    "GAP1_ENTRYPOINT_DRY_RUN_ONLY=false",
    "ENTRYPOINT_PRESENT_IMPLIES_RUNTIME_APPROVED=true",
    "DRY_RUN_BOUNDARY_IMPLIES_EXECUTION_AUTHORIZED=true",
    "CONTRACT_PRESENT_IMPLIES_VERIFIED=true",
    "PREFLIGHT_MARKER_IMPLIES_RUNTIME_APPROVED=true",
    "GAP6_DRY_RUN_PROOF_ACCEPTED=true",
    "GAP7_RISK_BOUNDARY_VERIFIED=true",
    "GAP2A1_PRIMARY_EVIDENCE_ENFORCED=true",
    "WORKSHEET_COMPLETE=true",
    "PATH_B_LIFT_DISCUSSION_READY=true",
    "ALL_GAPS_CLOSED=true",
    "READY_FOR_OPERATOR_ARMING=true",
    "PREFLIGHT_REMAINS_BLOCKED=false",
    "SHADOW_24_7_AUTHORIZED=true",
)

EXTERNAL_CONFLATION_FORBIDDEN_REPO_TOKENS = (
    "ENTRYPOINT_PRESENT_IMPLIES_RUNTIME_APPROVED=true",
    "DRY_RUN_BOUNDARY_IMPLIES_EXECUTION_AUTHORIZED=true",
    "CONTRACT_PRESENT_IMPLIES_VERIFIED=true",
    "PREFLIGHT_MARKER_IMPLIES_RUNTIME_APPROVED=true",
)

CONFLATION_SAMPLE_LINES_MUST_NOT_LIFT_RUNTIME_APPROVAL = (
    "ENTRYPOINT_CLI_PARSEABLE=true",
    "DRY_RUN_BOUNDARY_SATISFIED=true",
    "PREFLIGHT_STATUS_OBSERVED=true",
    "GAP1_RUNTIME_APPROVED=true",
    "GAP1_SCHEDULER_EXECUTION_AUTHORIZED=true",
    "scheduler_execution_authorized=true",
)


def _final_machine_lines(text: str) -> str:
    return text.split(FINAL_MACHINE_LINES_HEADER, 1)[1]


def _gap1_section(text: str) -> str:
    return text.split(GAP1_SECTION_HEADER, 1)[1].split("## Gap 3 Execute Command Contract v0", 1)[0]


def _gap1_rc0_observed_reflection_section(text: str) -> str:
    return text.split(GAP1_RC0_OBSERVED_REFLECTION_HEADER, 1)[1].split(
        GAP4_GOVERNED_REFLECTION_HEADER, 1
    )[0]


def _section5_text() -> str:
    return SECTION5_DOC.read_text(encoding="utf-8")


def _run_scheduler_source() -> str:
    return RUN_SCHEDULER.read_text(encoding="utf-8")


def test_gap1_drift_guard_module_constants_v0() -> None:
    assert GAP1_EXECUTE_ENTRYPOINT_PLANNED is True
    assert GAP1_EXECUTE_ENTRYPOINT_VERIFIED is False
    assert GAP1_RUNTIME_APPROVED is False
    assert GAP1_SCHEDULER_EXECUTION_AUTHORIZED is False
    assert GAP1_EXECUTE_ENTRYPOINT_DEFAULT_ON is False
    assert GAP1_ENTRYPOINT_DRY_RUN_ONLY is True
    assert ENTRYPOINT_CRITERIA_NOT_RUNTIME_APPROVAL is True
    assert DRY_RUN_BOUNDARY_NOT_EXECUTION_AUTHORIZATION is True
    assert PREFLIGHT_READINESS_NOT_SCHEDULER_EXECUTE is True


def test_gap1_drift_guard_final_machine_lines_remain_blocked_v0() -> None:
    block = _final_machine_lines(_section5_text())
    for marker in DRIFT_GUARD_REQUIRED_FINAL_LINES:
        assert marker in block


def test_gap1_drift_guard_forbids_lift_tokens_in_final_lines_v0() -> None:
    block = _final_machine_lines(_section5_text())
    lines = {line.strip() for line in block.splitlines()}
    for token in DRIFT_GUARD_FORBIDDEN_GAP1_REPO_TOKENS:
        assert token not in lines


def test_gap1_drift_guard_gap1_section_preserves_dry_run_not_approved_v0() -> None:
    section = _gap1_section(_section5_text())
    lines = {line.strip() for line in section.splitlines()}
    assert "GAP1_EXECUTE_ENTRYPOINT_VERIFIED=false" in section
    assert "GAP1_RUNTIME_APPROVED=false" in section
    assert "GAP1_SCHEDULER_EXECUTION_AUTHORIZED=false" in section
    assert "GAP1_EXECUTE_ENTRYPOINT_DEFAULT_ON=false" in section
    assert "GAP1_ENTRYPOINT_DRY_RUN_ONLY=true" in section
    for token in (
        "GAP1_EXECUTE_ENTRYPOINT_VERIFIED=true",
        "GAP1_RUNTIME_APPROVED=true",
        "GAP1_SCHEDULER_EXECUTION_AUTHORIZED=true",
    ):
        assert token not in lines


def test_gap1_drift_guard_repo_ssot_forbids_runtime_lift_tokens_v0() -> None:
    text = _section5_text()
    for token in EXTERNAL_CONFLATION_FORBIDDEN_REPO_TOKENS:
        assert token not in text


def test_gap1_drift_guard_preflight_remains_blocked_v0() -> None:
    text = PREFLIGHT_CONTRACT.read_text(encoding="utf-8")
    assert "Current status: **BLOCKED**." in text
    assert "Evidence ≠ approval" in text
    assert PREFLIGHT_READINESS_NOT_SCHEDULER_EXECUTE is True


def test_gap1_drift_guard_run_scheduler_static_dry_run_boundary_v0() -> None:
    source = _run_scheduler_source()
    assert 'parser.add_argument("--dry-run"' in source
    assert "if not args.dry_run:" in source
    assert "assert_scheduler_start_authorized" in source
    hardening = HARDENING_OWNER.read_text(encoding="utf-8")
    assert "test_run_scheduler_argparse_dry_run_flag_anchored_v0" in hardening


def test_gap1_drift_guard_entrypoint_not_execution_authorization_v0() -> None:
    block = _final_machine_lines(_section5_text())
    section = _gap1_section(_section5_text())
    assert ENTRYPOINT_CRITERIA_NOT_RUNTIME_APPROVAL is True
    assert "GAP1_RUNTIME_APPROVED=false" in section
    assert "GAP1_SCHEDULER_EXECUTION_AUTHORIZED=false" in section
    assert "GAP1_RUNTIME_APPROVED=false" in block
    assert "GAP1_SCHEDULER_EXECUTION_AUTHORIZED=false" in block
    lines = {line.strip() for line in block.splitlines()}
    assert "GAP1_RUNTIME_APPROVED=true" not in lines
    assert "GAP1_SCHEDULER_EXECUTION_AUTHORIZED=true" not in lines


def test_gap1_drift_guard_sample_conflation_lines_not_final_line_lifts_v0() -> None:
    block = _final_machine_lines(_section5_text())
    lines = {line.strip() for line in block.splitlines()}
    for sample in CONFLATION_SAMPLE_LINES_MUST_NOT_LIFT_RUNTIME_APPROVAL:
        assert sample not in lines


def test_gap1_drift_guard_gap6_gap7_gap2a1_orthogonal_v0() -> None:
    block = _final_machine_lines(_section5_text())
    assert "GAP6_DRY_RUN_PROOF_ACCEPTED=false" in block
    assert "GAP6_DRY_RUN_RC0_OBSERVED=false" in block
    assert "GAP7_RISK_BOUNDARY_VERIFIED=false" in block
    assert "GAP2A1_PRIMARY_EVIDENCE_ENFORCED=false" in block


def test_gap1_drift_guard_criteria_complete_does_not_close_gaps_v0() -> None:
    text = _section5_text()
    assert "SECTION5_OWNER_MAP_CONTRACT_V0_COMPLETE=true" in text
    assert "ALL_GAPS_CLOSED=false" in text
    assert "GAP1_EXECUTE_ENTRYPOINT_CONTRACT_V0=true" in text
    assert "GAP1_RUNTIME_APPROVED=false" in text


def test_gap1_drift_guard_module_is_static_no_subprocess_v0() -> None:
    import ast

    tree = ast.parse(Path(__file__).read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                assert alias.name != "subprocess"
        elif isinstance(node, ast.ImportFrom):
            assert node.module != "subprocess"


def test_gap1_drift_guard_owner_crosslinks_contract_tests_v0() -> None:
    assert GAP1_CONTRACT.is_file()
    text = GAP1_CONTRACT.read_text(encoding="utf-8")
    assert "test_gap1_execute_entrypoint_drift_guard_contract_v0.py" in text
    assert "GAP1_RUNTIME_APPROVED=false" in text
    assert "GAP1_SCHEDULER_EXECUTION_AUTHORIZED=false" in text


def test_gap1_drift_guard_owner_crosslinks_hardening_source_contract_v0() -> None:
    assert HARDENING_OWNER.is_file()
    text = HARDENING_OWNER.read_text(encoding="utf-8")
    assert "test_gap1_execute_entrypoint_drift_guard_contract_v0.py" in text
    lines = {line.strip() for line in text.splitlines()}
    assert ("GAP1_EXECUTE_ENTRYPOINT_VERIFIED" + _MARKER_TRUE) not in lines
    assert ("GAP1_RUNTIME_APPROVED" + _MARKER_TRUE) not in lines
    assert ("GAP1_SCHEDULER_EXECUTION_AUTHORIZED" + _MARKER_TRUE) not in lines


def test_gap1_rc0_observed_governed_reflection_scoped_evidence_v0() -> None:
    text = _section5_text()
    reflection = _gap1_rc0_observed_reflection_section(text)
    criteria = _gap1_section(text)
    block = _final_machine_lines(text)

    assert "GAP1_EXECUTE_ENTRYPOINT_OBSERVED_GOVERNED_REFLECTION_V0=true" in reflection
    assert "GAP1_EXECUTE_ENTRYPOINT_RC0_OBSERVED=true" in reflection
    assert "ACCEPTED_MODE=BOUNDED_TIER2_TAG_FILTERED_ENTRYPOINT_DRY_RUN_RC0" in reflection
    assert "ENTRYPOINT=scripts/run_scheduler.py" in reflection
    assert "EXIT_CODE=0" in reflection
    assert "DRY_RUN_OBSERVED=true" in reflection
    assert "DRY_RUN_ONCE=true" in reflection
    assert "INCLUDE_TAGS=paper_shadow_247,preflight,readonly" in reflection
    assert CANONICAL_BOUNDED_DRY_RUN_COMMAND_TIER2 in reflection
    assert "scripts/run_scheduler.py" in reflection
    assert "UNEXPECTED_EXECUTION_OBSERVED=false" in reflection
    assert "GAP6_EVIDENCE_SOURCE=true" in reflection
    assert "EXTERNAL_EVIDENCE_BUNDLE_POINTER=" in reflection
    assert (
        "gap6_bounded_dry_run_evidence_capture_operator_authorized_v0_20260603T153911Z"
        in reflection
    )
    assert "NO_REPO_FLAG_LIFT_FROM_EXTERNAL_ACCEPTANCE=true" in reflection
    assert "does not modify Final Machine Lines" in reflection
    assert "does not lift preflight" in reflection
    assert "Evidence observation is not runtime authorization" in reflection
    assert "GAP1_EXECUTE_ENTRYPOINT_VERIFIED=false" in criteria
    assert "GAP1_EXECUTE_ENTRYPOINT_VERIFIED=false" in block
    assert "ALL_GAPS_CLOSED=false" in block
    assert "READY_FOR_OPERATOR_ARMING=false" in block
    assert "PREFLIGHT_REMAINS_BLOCKED=true" in block
    assert "GAP7_RISK_BOUNDARY_VERIFIED=false" in block
    reflection_lines = {line.strip() for line in reflection.splitlines()}
    criteria_lines = {line.strip() for line in criteria.splitlines()}
    block_lines = {line.strip() for line in block.splitlines()}
    assert "GAP1_EXECUTE_ENTRYPOINT_RC0_OBSERVED=true" in reflection_lines
    assert "GAP1_EXECUTE_ENTRYPOINT_RC0_OBSERVED=true" not in criteria_lines
    assert "GAP1_EXECUTE_ENTRYPOINT_RC0_OBSERVED=true" not in block_lines
    assert "GAP1_EXECUTE_ENTRYPOINT_RC0_OBSERVED_EXTERNAL=true" not in text
    assert "Live/Testnet/Shadow/Paper/Broker/Network/AWS" in reflection
