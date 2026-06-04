"""Static contract for Gap-2↔Gap-3 command dependency drift guard v0.

Reads repo markdown/source only. Never executes scheduler/runtime via subprocess,
never reads external archive paths as pass/fail SSOT, and never treats dry-run
command text as scheduler execute authorization.
"""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SECTION5_DOC = (
    ROOT / "docs" / "ops" / "planning" / "SECTION5_PREFLIGHT_GAP_OWNER_MAP_CONTRACT_V0.md"
)
GAP2_TESTS = ROOT / "tests" / "ops" / "test_gap2_canonical_job_set_contract_v0.py"
GAP2_BOUNDARY_TESTS = (
    ROOT / "tests" / "ops" / "test_gap2_job_set_boundary_drift_guard_contract_v0.py"
)
GAP3_TESTS = ROOT / "tests" / "ops" / "test_gap3_execute_command_contract_v0.py"
HARDENING_OWNER = ROOT / "tests" / "ops" / "test_scheduler_dry_run_hardening_source_contract_v0.py"
FINAL_MACHINE_LINES_HEADER = "## Final Machine Lines"
GAP2_SECTION_HEADER = "## Gap 2 Canonical Job Set Contract v0"
GAP3_SECTION_HEADER = "## Gap 3 Execute Command Contract v0"
GAP7_SECTION_HEADER = "## Gap 7 Risk Boundary Criteria Contract v0"
GAP2_GOVERNED_REFLECTION_HEADER = (
    "## Gap 2 Governed Canonical Job Set Scoped Criteria Acceptance Reflection v0"
)
GAP3_GOVERNED_REFLECTION_HEADER = (
    "## Gap 3 Governed Tier-2 Command Scoped Criteria Acceptance Reflection v0"
)
GAP2_ACCEPTED_FINAL_LINE_REFLECTION_HEADER = (
    "## Gap 2 Governed Canonical Job Set Accepted Scoped-Criteria Final-Line Reflection v0"
)
GAP3_ACCEPTED_FINAL_LINE_REFLECTION_HEADER = (
    "## Gap 3 Governed Tier-2 Command Accepted Scoped-Criteria Final-Line Reflection v0"
)
GAP5_GOVERNED_REFLECTION_HEADER = "## Gap 5 Governed Stop Proof Acceptance Reflection v0"
_MARKER_TRUE = "=true"

CANONICAL_BOUNDED_DRY_RUN_COMMAND = (
    "uv run python scripts/run_scheduler.py --config config/scheduler/jobs.toml "
    "--dry-run --once --verbose"
)
CANONICAL_BOUNDED_DRY_RUN_COMMAND_TIER2 = (
    "uv run python scripts/run_scheduler.py --config config/scheduler/jobs.toml "
    "--dry-run --once --verbose --include-tags paper_shadow_247,preflight,readonly"
)
BOUNDED_PATH_B_CANDIDATE_SCOPE = "PAPER_PLUS_BOUNDED_SHADOW_NON_24_7"
BOUNDED_PAPER_JOBS = (
    "paper_shadow_247_paper_only_preflight_status_v0",
    "paper_shadow_247_paper_only_runtime_min_v0",
    "paper_shadow_247_paper_only_runtime_high_vol_no_trade_v0",
)
BOUNDED_SHADOW_JOB = "p7_shadow_high_vol_no_trade_runner_manual_v0"
EXCLUDED_PLACEHOLDER = "shadow_247_futures_prestart_evidence_drycheck_placeholder_v0"

DEPENDENCY_REQUIRED_FINAL_LINES = (
    "PREFLIGHT_REMAINS_BLOCKED=true",
    "READY_FOR_OPERATOR_ARMING=false",
    "PATH_B_LIFT_DISCUSSION_READY=false",
    "ALL_GAPS_CLOSED=false",
    "GAP2_CANONICAL_JOB_SET_VERIFIED=false",
    "GAP2_JOB_SET_ENABLED=false",
    "GAP3_EXECUTE_COMMAND_VERIFIED=false",
    "GAP3_SCHEDULER_EXECUTION_AUTHORIZED=false",
    "GAP6_DRY_RUN_PROOF_ACCEPTED=true",
    "GAP6_DRY_RUN_RC0_OBSERVED=true",
)

DEPENDENCY_FORBIDDEN_REPO_TOKENS = (
    "GAP2_CANONICAL_JOB_SET_VERIFIED=true",
    "GAP2_JOB_SET_ENABLED=true",
    "GAP3_EXECUTE_COMMAND_VERIFIED=true",
    "GAP3_SCHEDULER_EXECUTION_AUTHORIZED=true",
    "GAP6_DRY_RUN_PROOF_VERIFIED=true",
    "SHADOW_24_7_AUTHORIZED=true",
    "PATH_B_LIFT_DISCUSSION_READY=true",
    "ALL_GAPS_CLOSED=true",
    "READY_FOR_OPERATOR_ARMING=true",
    "PREFLIGHT_REMAINS_BLOCKED=false",
)

GAP2_BEFORE_GAP3_DEPENDENCY = "Gap 2 job-set boundary, Gap 3 command text"


def _final_machine_lines(text: str) -> str:
    return text.split(FINAL_MACHINE_LINES_HEADER, 1)[1]


def _gap2_section(text: str) -> str:
    return text.split(GAP2_SECTION_HEADER, 1)[1].split(FINAL_MACHINE_LINES_HEADER, 1)[0]


def _gap2_criteria_section(text: str) -> str:
    return _gap2_section(text)


def _gap3_section(text: str) -> str:
    return text.split(GAP3_SECTION_HEADER, 1)[1].split(
        "## Gap 4 Output/Evidence Paths Contract v0", 1
    )[0]


def _gap7_section(text: str) -> str:
    return text.split(GAP7_SECTION_HEADER, 1)[1].split(GAP2_GOVERNED_REFLECTION_HEADER, 1)[0]


def _gap2_governed_reflection_section(text: str) -> str:
    return text.split(GAP2_GOVERNED_REFLECTION_HEADER, 1)[1].split(
        GAP3_GOVERNED_REFLECTION_HEADER, 1
    )[0]


def _gap3_governed_reflection_section(text: str) -> str:
    return text.split(GAP3_GOVERNED_REFLECTION_HEADER, 1)[1].split(
        GAP2_ACCEPTED_FINAL_LINE_REFLECTION_HEADER, 1
    )[0]


def _gap2_accepted_final_line_reflection_section(text: str) -> str:
    return text.split(GAP2_ACCEPTED_FINAL_LINE_REFLECTION_HEADER, 1)[1].split(
        GAP3_ACCEPTED_FINAL_LINE_REFLECTION_HEADER, 1
    )[0]


def _gap3_accepted_final_line_reflection_section(text: str) -> str:
    return text.split(GAP3_ACCEPTED_FINAL_LINE_REFLECTION_HEADER, 1)[1].split(
        GAP5_GOVERNED_REFLECTION_HEADER, 1
    )[0]


def _section5_text() -> str:
    return SECTION5_DOC.read_text(encoding="utf-8")


def test_gap2_gap3_dependency_module_constants_v0() -> None:
    assert BOUNDED_PATH_B_CANDIDATE_SCOPE == "PAPER_PLUS_BOUNDED_SHADOW_NON_24_7"
    assert "--dry-run --once --verbose" in CANONICAL_BOUNDED_DRY_RUN_COMMAND


def test_gap2_gap3_dependency_final_machine_lines_remain_blocked_v0() -> None:
    block = _final_machine_lines(_section5_text())
    for marker in DEPENDENCY_REQUIRED_FINAL_LINES:
        assert marker in block


def test_gap2_gap3_dependency_forbids_lift_and_verified_tokens_v0() -> None:
    block = _final_machine_lines(_section5_text())
    lines = {line.strip() for line in block.splitlines()}
    for token in DEPENDENCY_FORBIDDEN_REPO_TOKENS:
        assert token not in lines


def test_gap2_gap3_dependency_gap7_chain_orders_job_set_before_command_v0() -> None:
    section = _gap7_section(_section5_text())
    assert GAP2_BEFORE_GAP3_DEPENDENCY in section
    assert "Gap 2 remains the canonical job-set criteria contract" in section
    assert "Gap 3 remains the canonical command-text contract" in section


def test_gap2_gap3_dependency_gap2_section_references_gap3_command_contract_v0() -> None:
    section = _gap2_section(_section5_text())
    assert "Gap 3 remains the canonical command-text contract" in section
    assert "GAP2_CANONICAL_JOB_SET_VERIFIED=false" in section
    assert "GAP2_JOB_SET_ENABLED=false" in section
    lines = {line.strip() for line in section.splitlines()}
    assert "GAP2_CANONICAL_JOB_SET_VERIFIED=true" not in lines


def test_gap2_gap3_dependency_gap3_cannot_verify_while_gap2_unverified_v0() -> None:
    text = _section5_text()
    gap2 = _gap2_section(text)
    gap3 = _gap3_section(text)
    block = _final_machine_lines(text)

    assert "GAP2_CANONICAL_JOB_SET_VERIFIED=false" in gap2
    assert "GAP2_JOB_SET_ENABLED=false" in gap2
    assert "GAP3_EXECUTE_COMMAND_VERIFIED=false" in gap3
    assert "GAP3_EXECUTE_COMMAND_VERIFIED=false" in block
    assert "GAP2_CANONICAL_JOB_SET_VERIFIED=false" in block
    assert "GAP2_JOB_SET_ENABLED=false" in block


def test_gap2_gap3_dependency_gap3_command_is_dry_run_planning_only_v0() -> None:
    section = _gap3_section(_section5_text())
    assert CANONICAL_BOUNDED_DRY_RUN_COMMAND in section
    assert "docs/tests-only command contract" in section
    assert "not verified, and not execution-authorized" in section
    assert "GAP3_EXECUTE_COMMAND_DRY_RUN_ONLY=true" in section
    assert "documentation/planning text only" in section
    assert "does not execute the scheduler" in section
    lines = {line.strip() for line in section.splitlines()}
    assert ("GAP3_EXECUTE_COMMAND_VERIFIED" + _MARKER_TRUE) not in lines
    assert "GAP3_SCHEDULER_EXECUTION_AUTHORIZED=true" not in lines


def test_gap2_gap3_dependency_dry_run_command_not_execute_authorization_v0() -> None:
    section = _gap3_section(_section5_text())
    assert "does not authorize scheduler execution" in section
    assert "GAP3_SCHEDULER_EXECUTION_AUTHORIZED=false" in section
    assert CANONICAL_BOUNDED_DRY_RUN_COMMAND in section


def test_gap2_gap3_dependency_shadow_24_7_not_authorized_in_repo_ssot_v0() -> None:
    text = _section5_text()
    assert "SHADOW_24_7_AUTHORIZED=true" not in text
    block = _final_machine_lines(text)
    assert "SHADOW_24_7_AUTHORIZED=true" not in block


def test_gap2_gap3_dependency_gap6_tokens_untouched_v0() -> None:
    block = _final_machine_lines(_section5_text())
    assert "GAP6_DRY_RUN_PROOF_ACCEPTED=true" in block
    assert "GAP6_DRY_RUN_RC0_OBSERVED=true" in block
    assert "GAP6_DRY_RUN_PROOF_VERIFIED=false" in block


def test_gap2_gap3_dependency_criteria_complete_does_not_close_gaps_v0() -> None:
    text = _section5_text()
    assert "SECTION5_OWNER_MAP_CONTRACT_V0_COMPLETE=true" in text
    assert "ALL_GAPS_CLOSED=false" in text
    assert "GAP3_EXECUTE_COMMAND_CONTRACT_V0=true" in text


def test_gap2_gap3_dependency_evidence_not_approval_language_v0() -> None:
    section = _gap3_section(_section5_text())
    assert "contract-only" in section
    assert "not execution-authorized" in section
    assert "does not lift preflight" in section


def test_gap2_gap3_dependency_module_is_static_no_subprocess_v0() -> None:
    assert HARDENING_OWNER.is_file()
    hardening = HARDENING_OWNER.read_text(encoding="utf-8")
    assert "subprocess" not in hardening.lower() or "import subprocess" not in hardening


def test_gap2_gap3_dependency_owner_crosslinks_gap3_execute_command_v0() -> None:
    assert GAP3_TESTS.is_file()
    text = GAP3_TESTS.read_text(encoding="utf-8")
    assert "test_gap2_gap3_command_dependency_contract_v0.py" in text


def test_gap2_gap3_dependency_owner_crosslinks_gap2_canonical_v0() -> None:
    assert GAP2_TESTS.is_file()
    text = GAP2_TESTS.read_text(encoding="utf-8")
    assert "test_gap2_gap3_command_dependency_contract_v0.py" in text


def test_gap2_gap3_dependency_owner_crosslinks_gap2_boundary_guard_v0() -> None:
    assert GAP2_BOUNDARY_TESTS.is_file()
    text = GAP2_BOUNDARY_TESTS.read_text(encoding="utf-8")
    assert "test_gap2_gap3_command_dependency_contract_v0.py" in text
    assert BOUNDED_PATH_B_CANDIDATE_SCOPE in text


def test_gap2_gap3_dependency_owner_crosslinks_hardening_source_contract_v0() -> None:
    assert HARDENING_OWNER.is_file()
    text = HARDENING_OWNER.read_text(encoding="utf-8")
    assert "test_gap2_gap3_command_dependency_contract_v0.py" in text


def test_gap2_governed_reflection_scoped_acceptance_v0() -> None:
    text = _section5_text()
    reflection = _gap2_governed_reflection_section(text)
    criteria = _gap2_criteria_section(text)
    block = _final_machine_lines(text)

    assert "GAP2_CANONICAL_JOB_SET_GOVERNED_REFLECTION_V0=true" in reflection
    assert "GAP2_ACCEPTED_SCOPED_CRITERIA=true" in reflection
    assert f"ACCEPTED_MODE={BOUNDED_PATH_B_CANDIDATE_SCOPE}" in reflection
    assert "NO_REPO_FLAG_LIFT_FROM_EXTERNAL_ACCEPTANCE=true" in reflection
    assert "EXTERNAL_ACCEPTANCE_RECORD_POINTER=" in reflection
    assert "GOVERNED_REPO_REFLECTION_CHARTER_POINTER=" in reflection
    assert "EXECUTED=false" in reflection
    for job in BOUNDED_PAPER_JOBS:
        assert job in reflection
    assert BOUNDED_SHADOW_JOB in reflection
    assert EXCLUDED_PLACEHOLDER in reflection
    assert "Evidence acceptance is not runtime authorization" in reflection
    assert "does not modify Final Machine Lines" in reflection
    assert "GAP2_CANONICAL_JOB_SET_VERIFIED=false" in criteria
    assert "GAP2_CANONICAL_JOB_SET_VERIFIED=false" in block
    reflection_lines = {line.strip() for line in reflection.splitlines()}
    assert "GAP2_CANONICAL_JOB_SET_VERIFIED=true" not in reflection_lines
    assert "GAP2_ACCEPTED_SCOPED_CRITERIA=true" not in criteria


def test_gap2_accepted_scoped_criteria_final_line_governed_reflection_v0() -> None:
    text = _section5_text()
    reflection = _gap2_accepted_final_line_reflection_section(text)
    acceptance = _gap2_governed_reflection_section(text)
    criteria = _gap2_criteria_section(text)
    block = _final_machine_lines(text)

    assert "GAP2_ACCEPTED_SCOPED_CRITERIA_FINAL_LINE_GOVERNED_REFLECTION_V0=true" in reflection
    assert "GAP2_ACCEPTED_SCOPED_CRITERIA=true" in reflection
    assert "ACCEPTED_NOT_VERIFIED_SEMANTIC_PRESERVED=true" in reflection
    assert "GOVERNED_ACCEPTANCE_BASIS=GAP2_ACCEPTED_SCOPED_CRITERIA=true" in reflection
    assert (
        "OPERATOR_GO=GO_PREPARE_SECTION5_GAP2_GAP3_ACCEPTED_SCOPED_CRITERIA_FINAL_LINE_REPO_REFLECTION_DOCS_TESTS_V0"
        in reflection
    )
    assert "does not set `GAP2_CANONICAL_JOB_SET_VERIFIED=true`" in reflection
    assert "does not modify `config/scheduler/jobs.toml`" in reflection
    assert "NO_RUNTIME_AUTHORITY=true" in reflection
    assert "GAP2_ACCEPTED_SCOPED_CRITERIA=true" in acceptance
    assert "GAP2_CANONICAL_JOB_SET_VERIFIED=false" in criteria
    assert "GAP2_ACCEPTED_SCOPED_CRITERIA=true" not in criteria
    assert "GAP2_ACCEPTED_SCOPED_CRITERIA=true" in block
    assert "GAP2_CANONICAL_JOB_SET_VERIFIED=false" in block
    criteria_lines = {line.strip() for line in criteria.splitlines()}
    block_lines = {line.strip() for line in block.splitlines()}
    assert "GAP2_ACCEPTED_SCOPED_CRITERIA=true" not in criteria_lines
    assert "GAP2_ACCEPTED_SCOPED_CRITERIA=true" in block_lines


def test_gap3_governed_reflection_tier2_command_v0() -> None:
    text = _section5_text()
    reflection = _gap3_governed_reflection_section(text)
    criteria = _gap3_section(text)
    block = _final_machine_lines(text)

    assert "GAP3_EXECUTE_COMMAND_GOVERNED_REFLECTION_V0=true" in reflection
    assert "GAP3_ACCEPTED_SCOPED_CRITERIA=true" in reflection
    assert "ACCEPTED_MODE=BOUNDED_DRY_RUN_COMMAND_TIER2" in reflection
    assert CANONICAL_BOUNDED_DRY_RUN_COMMAND in reflection
    assert CANONICAL_BOUNDED_DRY_RUN_COMMAND_TIER2 in reflection
    assert "--include-tags paper_shadow_247,preflight,readonly" in reflection
    assert "does not observe or record `GAP6_DRY_RUN_RC0_OBSERVED=true`" in reflection
    assert "separate operator-authorized bounded execute GO" in reflection
    assert "NO_REPO_FLAG_LIFT_FROM_EXTERNAL_ACCEPTANCE=true" in reflection
    assert "EXECUTED=false" in reflection
    assert "GAP3_EXECUTE_COMMAND_VERIFIED=false" in criteria
    assert "GAP3_EXECUTE_COMMAND_VERIFIED=false" in block
    reflection_lines = {line.strip() for line in reflection.splitlines()}
    assert "GAP3_EXECUTE_COMMAND_VERIFIED=true" not in reflection_lines
    assert "GAP3_ACCEPTED_SCOPED_CRITERIA=true" not in criteria


def test_gap3_accepted_scoped_criteria_final_line_governed_reflection_v0() -> None:
    text = _section5_text()
    reflection = _gap3_accepted_final_line_reflection_section(text)
    acceptance = _gap3_governed_reflection_section(text)
    criteria = _gap3_section(text)
    block = _final_machine_lines(text)

    assert "GAP3_ACCEPTED_SCOPED_CRITERIA_FINAL_LINE_GOVERNED_REFLECTION_V0=true" in reflection
    assert "GAP3_ACCEPTED_SCOPED_CRITERIA=true" in reflection
    assert "ACCEPTED_NOT_VERIFIED_SEMANTIC_PRESERVED=true" in reflection
    assert "GOVERNED_ACCEPTANCE_BASIS=GAP3_ACCEPTED_SCOPED_CRITERIA=true" in reflection
    assert (
        "OPERATOR_GO=GO_PREPARE_SECTION5_GAP2_GAP3_ACCEPTED_SCOPED_CRITERIA_FINAL_LINE_REPO_REFLECTION_DOCS_TESTS_V0"
        in reflection
    )
    assert "does not set `GAP3_EXECUTE_COMMAND_VERIFIED=true`" in reflection
    assert "does not observe or record `GAP6_DRY_RUN_RC0_OBSERVED=true`" in reflection
    assert "NO_RUNTIME_AUTHORITY=true" in reflection
    assert "GAP3_ACCEPTED_SCOPED_CRITERIA=true" in acceptance
    assert "GAP3_EXECUTE_COMMAND_VERIFIED=false" in criteria
    assert "GAP3_ACCEPTED_SCOPED_CRITERIA=true" not in criteria
    assert "GAP3_ACCEPTED_SCOPED_CRITERIA=true" in block
    assert "GAP3_EXECUTE_COMMAND_VERIFIED=false" in block
    criteria_lines = {line.strip() for line in criteria.splitlines()}
    block_lines = {line.strip() for line in block.splitlines()}
    assert "GAP3_ACCEPTED_SCOPED_CRITERIA=true" not in criteria_lines
    assert "GAP3_ACCEPTED_SCOPED_CRITERIA=true" in block_lines


def test_gap2_gap3_reflection_final_lines_no_verified_or_rc0_flip_v0() -> None:
    block = _final_machine_lines(_section5_text())
    lines = {line.strip() for line in block.splitlines()}
    for token in DEPENDENCY_FORBIDDEN_REPO_TOKENS:
        assert token not in lines
    assert "GAP2_ACCEPTED_SCOPED_CRITERIA=true" in block
    assert "GAP3_ACCEPTED_SCOPED_CRITERIA=true" in block
    assert "GAP2_CANONICAL_JOB_SET_VERIFIED=false" in block
    assert "GAP3_EXECUTE_COMMAND_VERIFIED=false" in block
    assert "GAP6_DRY_RUN_RC0_OBSERVED=true" in block
    assert "GAP6_DRY_RUN_PROOF_VERIFIED=false" in block
    assert "PREFLIGHT_REMAINS_BLOCKED=true" in block
    assert "ALL_GAPS_CLOSED=false" in block
