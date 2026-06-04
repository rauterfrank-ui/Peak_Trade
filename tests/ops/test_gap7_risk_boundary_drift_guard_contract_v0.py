"""Static contract for Gap-7 risk-boundary drift guard v0.

Reads repo markdown/source only. Never executes scheduler/runtime/stop/risk helpers,
never reads external archive paths as pass/fail SSOT, and never treats KillSwitch runbook
presence, external checklist completion, scheduler boundary markers, preflight markers, or
dashboard/strategy readiness labels as repo ``GAP7_RISK_BOUNDARY_VERIFIED`` or authority lift.
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
KILL_SWITCH_RUNBOOK = ROOT / "docs" / "risk" / "KILL_SWITCH_RUNBOOK.md"
GAP7_CRITERIA_TESTS = ROOT / "tests" / "ops" / "test_gap7_risk_boundary_criteria_contract_v0.py"
HARDENING_OWNER = ROOT / "tests" / "ops" / "test_scheduler_dry_run_hardening_source_contract_v0.py"
BOUNDARY_OWNER = ROOT / "tests" / "ops" / "test_scheduler_boundary_hard_block_contract_v0.py"
FINAL_MACHINE_LINES_HEADER = "## Final Machine Lines"
GAP7_SECTION_HEADER = "## Gap 7 Risk Boundary Criteria Contract v0"
GAP7_GOVERNED_REFLECTION_HEADER = "## Gap 7 Governed Risk Boundary Acceptance Reflection v0"
GAP7_VERIFIED_FINAL_LINE_REFLECTION_HEADER = (
    "## Gap 7 Governed Risk Boundary Verified Final-Line Reflection v0"
)
GAP4_VERIFIED_FINAL_LINE_REFLECTION_HEADER = (
    "## Gap 4 Governed Output Evidence Paths Verified Final-Line Reflection v0"
)
GAP5_GOVERNED_REFLECTION_HEADER = "## Gap 5 Governed Stop Proof Acceptance Reflection v0"
_MARKER_TRUE = "=true"

GAP7_RISK_BOUNDARY_PLANNED = True
GAP7_RISK_BOUNDARY_VERIFIED = False
GAP7_RISK_KILLSWITCH_AUTHORITY_CHANGED = False
GAP7_RISK_KILLSWITCH_RUNTIME_CHANGED = False
GAP7_EXECUTION_LIVE_GATES_CHANGED = False
GAP7_RISK_BOUNDARY_DEFAULT_ON = False
EXTERNAL_GAP7_CHECKLIST_NOT_REPO_SSOT = True
KILLSWITCH_DOC_NOT_AUTHORITY_CHANGE = True
RISK_VISIBILITY_NOT_VERIFICATION = True
LIVE_GATE_CRITERIA_NOT_AUTHORIZATION = True
DASHBOARD_READINESS_NOT_TRADE_AUTHORITY = True
AI_READINESS_NOT_LIVE_AUTHORITY = True
STRATEGY_READINESS_NOT_LIVE_AUTHORITY = True
EVIDENCE_EQUALS_APPROVAL = False
CRITERIA_COMPLETE_EQUALS_GAP_CLOSED = False
FUTURE_VERIFICATION_REQUIRES_EXPLICIT_OPERATOR_GO = True

DRIFT_GUARD_REQUIRED_FINAL_LINES = (
    "PREFLIGHT_LIFTED_BY_CLASS4_POLICY=true",
    "READY_FOR_OPERATOR_ARMING=false",
    "PATH_B_LIFT_DISCUSSION_READY=false",
    "ALL_GAPS_CLOSED=true",
    "GAP7_RISK_BOUNDARY_VERIFIED=true",
    "GAP7_RISK_KILLSWITCH_AUTHORITY_CHANGED=false",
    "GAP7_RISK_KILLSWITCH_RUNTIME_CHANGED=false",
    "GAP7_MASTER_V2_DOUBLE_PLAY_CHANGED=false",
    "GAP7_BULL_BEAR_SCOPE_CAPITAL_CHANGED=false",
    "GAP7_EXECUTION_LIVE_GATES_CHANGED=false",
    "GAP7_SCHEDULER_EXECUTION_AUTHORIZED=false",
    "GAP7_RUNTIME_APPROVED=false",
    "GAP7_RISK_BOUNDARY_DEFAULT_ON=false",
    "GAP5_STOP_REHEARSAL_EXECUTED=true",
    "GAP5_STOP_PROOF_ACCEPTED=true",
    "GAP6_DRY_RUN_PROOF_ACCEPTED=true",
    "GAP2A1_PRIMARY_EVIDENCE_ENFORCED=true",
    "GAP4_OUTPUT_EVIDENCE_PATHS_VERIFIED=true",
)

DRIFT_GUARD_FORBIDDEN_GAP7_REPO_TOKENS = (
    "GAP7_RISK_KILLSWITCH_AUTHORITY_CHANGED=true",
    "GAP7_RISK_KILLSWITCH_RUNTIME_CHANGED=true",
    "GAP7_MASTER_V2_DOUBLE_PLAY_CHANGED=true",
    "GAP7_BULL_BEAR_SCOPE_CAPITAL_CHANGED=true",
    "GAP7_EXECUTION_LIVE_GATES_CHANGED=true",
    "GAP7_SCHEDULER_EXECUTION_AUTHORIZED=true",
    "GAP7_RUNTIME_APPROVED=true",
    "GAP7_RISK_BOUNDARY_DEFAULT_ON=true",
    "READY_FOR_OPERATOR_ARMING=true",
    "PATH_B_LIFT_DISCUSSION_READY=true",
    "SHADOW_24_7_AUTHORIZED=true",
    "WORKSHEET_COMPLETE=true",
)

EXTERNAL_CONFLATION_FORBIDDEN_REPO_TOKENS = (
    "RISK_VISIBILITY_IMPLIES_VERIFIED=true",
    "KILLSWITCH_DOC_IMPLIES_AUTHORITY_CHANGED=true",
    "KILLSWITCH_RUNBOOK_IMPLIES_VERIFIED=true",
    "LIVE_GATE_CRITERIA_IMPLIES_AUTHORIZATION=true",
    "SCHEDULER_BOUNDARY_IMPLIES_RISK_VERIFIED=true",
    "PREFLIGHT_MARKER_IMPLIES_RISK_VERIFIED=true",
    "DASHBOARD_READINESS_IMPLIES_TRADE_AUTHORITY=true",
    "STRATEGY_READINESS_IMPLIES_LIVE_AUTHORITY=true",
    "AI_READINESS_IMPLIES_LIVE_AUTHORITY=true",
    "EXTERNAL_GAP7_CHECKLIST_COMPLETE_IMPLIES_VERIFIED=true",
    "EXTERNAL_RISK_REVIEW_IMPLIES_GAP7_VERIFIED=true",
    "GAP7_CRITERIA_COMPLETE_IMPLIES_VERIFIED=true",
)

CONFLATION_SAMPLE_LINES_MUST_NOT_LIFT_GAP7_VERIFIED = (
    "EXTERNAL_GAP7_CHECKLIST_COMPLETE=true",
    "RISK_BOUNDARY_CRITERIA_SATISFIED=true",
    "KILLSWITCH_RUNBOOK_PRESENT=true",
    "LIVE_GATE_CRITERIA_DOCUMENTED=true",
    "DASHBOARD_READINESS_OBSERVED=true",
    "AI_READINESS_OBSERVED=true",
    "STRATEGY_READINESS_OBSERVED=true",
    "SCHEDULER_BOUNDARY_MARKER_PRESENT=true",
    "PREFLIGHT_STATUS_OBSERVED=true",
    "MANIFEST_VERIFY_RC=0",
)


def _final_machine_lines(text: str) -> str:
    return text.split(FINAL_MACHINE_LINES_HEADER, 1)[1]


def _gap7_criteria_section(text: str) -> str:
    return text.split(GAP7_SECTION_HEADER, 1)[1].split(GAP5_GOVERNED_REFLECTION_HEADER, 1)[0]


def _gap7_governed_reflection_section(text: str) -> str:
    return text.split(GAP7_GOVERNED_REFLECTION_HEADER, 1)[1].split(
        GAP7_VERIFIED_FINAL_LINE_REFLECTION_HEADER, 1
    )[0]


def _gap7_verified_final_line_reflection_section(text: str) -> str:
    return text.split(GAP7_VERIFIED_FINAL_LINE_REFLECTION_HEADER, 1)[1].split(
        GAP4_VERIFIED_FINAL_LINE_REFLECTION_HEADER, 1
    )[0]


def _gap7_section(text: str) -> str:
    return _gap7_criteria_section(text)


def _section5_text() -> str:
    return SECTION5_DOC.read_text(encoding="utf-8")


def _module_preamble() -> str:
    return Path(__file__).read_text(encoding="utf-8").split("\ndef test_", 1)[0]


def test_gap7_drift_guard_module_constants_v0() -> None:
    assert GAP7_RISK_BOUNDARY_PLANNED is True
    assert GAP7_RISK_BOUNDARY_VERIFIED is False
    assert GAP7_RISK_KILLSWITCH_AUTHORITY_CHANGED is False
    assert GAP7_RISK_KILLSWITCH_RUNTIME_CHANGED is False
    assert GAP7_EXECUTION_LIVE_GATES_CHANGED is False
    assert GAP7_RISK_BOUNDARY_DEFAULT_ON is False
    assert EXTERNAL_GAP7_CHECKLIST_NOT_REPO_SSOT is True
    assert KILLSWITCH_DOC_NOT_AUTHORITY_CHANGE is True
    assert RISK_VISIBILITY_NOT_VERIFICATION is True
    assert LIVE_GATE_CRITERIA_NOT_AUTHORIZATION is True
    assert DASHBOARD_READINESS_NOT_TRADE_AUTHORITY is True
    assert AI_READINESS_NOT_LIVE_AUTHORITY is True
    assert STRATEGY_READINESS_NOT_LIVE_AUTHORITY is True
    assert EVIDENCE_EQUALS_APPROVAL is False
    assert CRITERIA_COMPLETE_EQUALS_GAP_CLOSED is False
    assert FUTURE_VERIFICATION_REQUIRES_EXPLICIT_OPERATOR_GO is True


def test_gap7_drift_guard_final_machine_lines_remain_blocked_v0() -> None:
    block = _final_machine_lines(_section5_text())
    for marker in DRIFT_GUARD_REQUIRED_FINAL_LINES:
        assert marker in block


def test_gap7_drift_guard_forbids_lift_tokens_in_final_lines_v0() -> None:
    block = _final_machine_lines(_section5_text())
    lines = {line.strip() for line in block.splitlines()}
    for token in DRIFT_GUARD_FORBIDDEN_GAP7_REPO_TOKENS:
        assert token not in lines


def test_gap7_drift_guard_gap7_section_preserves_criteria_only_v0() -> None:
    section = _gap7_section(_section5_text())
    lines = {line.strip() for line in section.splitlines()}
    assert "GAP7_RISK_BOUNDARY_CRITERIA_CONTRACT_V0=true" in section
    assert "GAP7_CRITERIA_ONLY=true" in section
    assert "GAP7_RISK_BOUNDARY_VERIFIED=false" in section
    assert "docs/tests-only criteria contract" in section
    assert "does not verify or activate Risk Boundaries" in section
    assert "does not change Risk/KillSwitch authority" in section
    assert "criteria-only" in section
    assert "not verified" in section
    for token in (
        "GAP7_RISK_BOUNDARY_VERIFIED=true",
        "GAP7_RISK_KILLSWITCH_AUTHORITY_CHANGED=true",
        "GAP7_EXECUTION_LIVE_GATES_CHANGED=true",
    ):
        assert token not in lines


def test_gap7_drift_guard_repo_ssot_forbids_conflation_tokens_v0() -> None:
    text = _section5_text()
    for token in EXTERNAL_CONFLATION_FORBIDDEN_REPO_TOKENS:
        assert token not in text


def test_gap7_drift_guard_preflight_remains_blocked_v0() -> None:
    text = PREFLIGHT_CONTRACT.read_text(encoding="utf-8")
    assert "Current status: **BLOCKED**." in text
    assert "Evidence ≠ approval" in text
    assert EVIDENCE_EQUALS_APPROVAL is False


def test_gap7_drift_guard_killswitch_doc_not_authority_change_v0() -> None:
    assert KILL_SWITCH_RUNBOOK.is_file()
    section = _gap7_section(_section5_text())
    assert "docs/risk/KILL_SWITCH_RUNBOOK.md" in section
    assert KILLSWITCH_DOC_NOT_AUTHORITY_CHANGE is True
    assert GAP7_RISK_KILLSWITCH_AUTHORITY_CHANGED is False
    block = _final_machine_lines(_section5_text())
    assert "GAP7_RISK_KILLSWITCH_AUTHORITY_CHANGED=false" in block
    assert "GAP7_RISK_KILLSWITCH_RUNTIME_CHANGED=false" in block


def test_gap7_drift_guard_risk_visibility_not_verification_v0() -> None:
    block = _final_machine_lines(_section5_text())
    section = _gap7_section(_section5_text())
    assert RISK_VISIBILITY_NOT_VERIFICATION is True
    assert "GAP7_RISK_BOUNDARY_VERIFIED=false" in section
    assert "GAP7_RISK_BOUNDARY_VERIFIED=true" in block
    lines = {line.strip() for line in block.splitlines()}
    assert "GAP7_RISK_BOUNDARY_VERIFIED=false" not in lines


def test_gap7_drift_guard_live_gate_criteria_not_authorization_v0() -> None:
    block = _final_machine_lines(_section5_text())
    section = _gap7_section(_section5_text())
    assert LIVE_GATE_CRITERIA_NOT_AUTHORIZATION is True
    assert "does not change execution/live gates" in section
    assert "GAP7_EXECUTION_LIVE_GATES_CHANGED=false" in section
    assert "GAP7_EXECUTION_LIVE_GATES_CHANGED=false" in block


def test_gap7_drift_guard_sample_conflation_lines_not_final_line_lifts_v0() -> None:
    block = _final_machine_lines(_section5_text())
    lines = {line.strip() for line in block.splitlines()}
    for sample in CONFLATION_SAMPLE_LINES_MUST_NOT_LIFT_GAP7_VERIFIED:
        assert sample not in lines


def test_gap7_drift_guard_gap6_gap2a1_orthogonal_v0() -> None:
    block = _final_machine_lines(_section5_text())
    assert "GAP6_DRY_RUN_PROOF_ACCEPTED=true" in block
    assert "GAP6_DRY_RUN_RC0_OBSERVED=true" in block
    assert "GAP6_DRY_RUN_PROOF_VERIFIED=true" in block
    assert "GAP2A1_PRIMARY_EVIDENCE_ENFORCED=true" in block
    assert "GAP2A1_ENFORCEMENT_DEFAULT_ON=false" in block
    assert "GAP7_RISK_BOUNDARY_VERIFIED=true" in block


def test_gap7_drift_guard_gap5_stop_orthogonal_v0() -> None:
    block = _final_machine_lines(_section5_text())
    assert "GAP5_STOP_REHEARSAL_EXECUTED=true" in block
    assert "GAP5_STOP_PROOF_ACCEPTED=true" in block
    assert "GAP7_RISK_BOUNDARY_VERIFIED=true" in block


def test_gap7_drift_guard_criteria_complete_does_not_close_gaps_v0() -> None:
    text = _section5_text()
    assert "SECTION5_OWNER_MAP_CONTRACT_V0_COMPLETE=true" in text
    assert "ALL_GAPS_CLOSED=false" in text
    assert "GAP7_RISK_BOUNDARY_CRITERIA_CONTRACT_V0=true" in text
    assert "GAP7_RISK_BOUNDARY_VERIFIED=false" in _gap7_criteria_section(text)
    assert "GAP7_RISK_BOUNDARY_VERIFIED=true" in _final_machine_lines(text)


def test_gap7_drift_guard_external_checklist_not_repo_ssot_v0() -> None:
    preamble = _module_preamble()
    assert "Peak_Trade_runtime_evidence_archive" not in preamble
    assert "external_gap7_risk_boundary_checklist" not in preamble
    assert EXTERNAL_GAP7_CHECKLIST_NOT_REPO_SSOT is True


def test_gap7_drift_guard_module_is_static_no_subprocess_v0() -> None:
    import ast

    tree = ast.parse(Path(__file__).read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                assert alias.name != "subprocess"
        elif isinstance(node, ast.ImportFrom):
            assert node.module != "subprocess"


def test_gap7_drift_guard_owner_crosslinks_criteria_tests_v0() -> None:
    assert GAP7_CRITERIA_TESTS.is_file()
    text = GAP7_CRITERIA_TESTS.read_text(encoding="utf-8")
    assert "test_gap7_risk_boundary_drift_guard_contract_v0.py" in text
    assert "GAP7_RISK_BOUNDARY_VERIFIED=false" in text


def test_gap7_drift_guard_owner_crosslinks_hardening_source_contract_v0() -> None:
    assert HARDENING_OWNER.is_file()
    text = HARDENING_OWNER.read_text(encoding="utf-8")
    assert "test_gap7_risk_boundary_drift_guard_contract_v0.py" in text
    lines = {line.strip() for line in text.splitlines()}
    assert ("GAP7_RISK_BOUNDARY_VERIFIED" + _MARKER_TRUE) not in lines
    assert ("GAP7_RISK_KILLSWITCH_AUTHORITY_CHANGED" + _MARKER_TRUE) not in lines
    assert ("GAP7_EXECUTION_LIVE_GATES_CHANGED" + _MARKER_TRUE) not in lines


def test_gap7_drift_guard_owner_crosslinks_boundary_contract_v0() -> None:
    assert BOUNDARY_OWNER.is_file()
    section = _gap7_section(_section5_text())
    assert "test_scheduler_boundary_hard_block_contract_v0.py" in section


def test_gap7_drift_guard_repo_ssot_forbids_external_gap7_acceptance_token_v0() -> None:
    text = _section5_text()
    assert "GAP7_RISK_BOUNDARY_ACCEPTED_EXTERNAL=true" not in text
    assert "GAP7_RISK_BOUNDARY_VERIFIED=false" in text


def test_gap7_drift_guard_governed_reflection_scoped_acceptance_v0() -> None:
    text = _section5_text()
    reflection = _gap7_governed_reflection_section(text)
    criteria = _gap7_criteria_section(text)
    block = _final_machine_lines(text)

    assert "GAP7_RISK_BOUNDARY_GOVERNED_REFLECTION_V0=true" in reflection
    assert "GAP7_RISK_BOUNDARY_ACCEPTED=true" in reflection
    assert (
        "ACCEPTED_MODE=GAP7_RISK_BOUNDARY_SCOPED_EXTERNAL_CHECKLIST_WALKTHROUGH_ACCEPTANCE"
        in reflection
    )
    assert "NO_REPO_FLAG_LIFT_FROM_EXTERNAL_ACCEPTANCE=true" in reflection
    assert "EXTERNAL_ACCEPTANCE_RECORD_POINTER=" in reflection
    assert "GOVERNED_REPO_REFLECTION_CHARTER_POINTER=" in reflection
    assert "GAP7_RISK_BOUNDARY_ACCEPTED_EXTERNAL=true" not in text
    assert "does not verify Gap-7 risk boundaries in criteria or Final Machine Lines" in reflection
    assert "does not change Risk/KillSwitch authority or runtime behavior" in reflection
    assert "does not change execution/live gates" in reflection
    assert "does not authorize scheduler execution" in reflection
    assert "does not enable operator arming" in reflection
    assert "does not open Path-B lift discussion" in reflection
    assert "does not start or authorize Runtime, Paper, Shadow, Testnet, or Live" in reflection
    assert (
        "does not modify existing Gap-7 criteria/final machine-line verification status"
        in reflection
    )
    assert "Evidence acceptance is not runtime authorization" in reflection
    assert "GAP7_RISK_BOUNDARY_VERIFIED=false" in criteria
    assert "criteria-only" in criteria
    assert "not verified" in criteria
    assert "GAP7_RISK_BOUNDARY_VERIFIED=true" in block
    assert "GAP4_OUTPUT_EVIDENCE_PATHS_VERIFIED=true" in block
    assert "GAP2A1_PRIMARY_EVIDENCE_ENFORCED=true" in block
    assert "READY_FOR_OPERATOR_ARMING=false" in block
    assert "PATH_B_LIFT_DISCUSSION_READY=false" in block
    assert "PREFLIGHT_REMAINS_BLOCKED=false" in block
    reflection_lines = {line.strip() for line in reflection.splitlines()}
    criteria_lines = {line.strip() for line in criteria.splitlines()}
    block_lines = {line.strip() for line in block.splitlines()}
    assert "GAP7_RISK_BOUNDARY_ACCEPTED=true" in reflection_lines
    assert "GAP7_RISK_BOUNDARY_ACCEPTED=true" not in criteria_lines
    assert "GAP7_RISK_BOUNDARY_ACCEPTED=true" not in block_lines
    assert "GAP7_RISK_BOUNDARY_VERIFIED=true" in block_lines
    assert "GAP7_RISK_BOUNDARY_VERIFIED=true" not in criteria_lines


def test_gap7_verified_final_line_governed_reflection_scoped_verification_v0() -> None:
    text = _section5_text()
    reflection = _gap7_verified_final_line_reflection_section(text)
    acceptance = _gap7_governed_reflection_section(text)
    criteria = _gap7_criteria_section(text)
    block = _final_machine_lines(text)

    assert "GAP7_RISK_BOUNDARY_VERIFIED_FINAL_LINE_GOVERNED_REFLECTION_V0=true" in reflection
    assert "GAP7_RISK_BOUNDARY_VERIFIED=true" in reflection
    assert (
        "ACCEPTED_MODE=GAP7_RISK_BOUNDARY_SCOPED_EXTERNAL_CHECKLIST_WALKTHROUGH_FINAL_LINE_VERIFIED"
        in reflection
    )
    assert "GOVERNED_ACCEPTANCE_BASIS=GAP7_RISK_BOUNDARY_ACCEPTED=true" in reflection
    assert "EXTERNAL_ACCEPTANCE_RECORD_POINTER=" in reflection
    assert (
        "gap7_risk_boundary_operator_walkthrough_external_acceptance_record_v0_20260531T202750Z"
        in reflection
    )
    assert "INPUT_STRATEGY_POINTER=" in reflection
    assert "section5_remaining_gaps_closure_strategy_no_lift_v0_20260603T160500Z" in reflection
    assert (
        "OPERATOR_GO=GO_GAP7_RISK_BOUNDARY_VERIFIED_FINAL_LINE_REPO_REFLECTION_DOCS_TESTS_V0"
        in reflection
    )
    assert "NO_RUNTIME_AUTHORITY=true" in reflection
    assert "NO_REPO_FLAG_LIFT_FROM_EXTERNAL_ACCEPTANCE=true" in reflection
    assert "does not modify Gap-7 criteria block verification posture" in reflection
    assert "does not change Risk/KillSwitch authority or runtime behavior" in reflection
    assert "does not authorize scheduler execution" in reflection
    assert "does not enable operator arming" in reflection
    assert "does not set `ALL_GAPS_CLOSED=true`" in reflection
    assert "does not lift preflight" in reflection
    assert "Evidence verification is not runtime authorization" in reflection
    assert "GAP7_RISK_BOUNDARY_ACCEPTED=true" in acceptance
    assert "GAP7_RISK_BOUNDARY_VERIFIED=false" in criteria
    assert "GAP7_RISK_BOUNDARY_VERIFIED=true" in block
    assert "ALL_GAPS_CLOSED=true" in block
    assert "READY_FOR_OPERATOR_ARMING=false" in block
    assert "PREFLIGHT_REMAINS_BLOCKED=false" in block
    reflection_lines = {line.strip() for line in reflection.splitlines()}
    criteria_lines = {line.strip() for line in criteria.splitlines()}
    block_lines = {line.strip() for line in block.splitlines()}
    assert "GAP7_RISK_BOUNDARY_VERIFIED=true" in reflection_lines
    assert "GAP7_RISK_BOUNDARY_VERIFIED=true" in block_lines
    assert "GAP7_RISK_BOUNDARY_VERIFIED=true" not in criteria_lines
    assert "GAP7_RISK_BOUNDARY_VERIFIED=false" not in block_lines
