"""Static contract for Gap-6 external↔repo drift guard v0.

Reads repo markdown/TOML/source only. Never executes scheduler/runtime, never reads
external archive paths as pass/fail SSOT, and never treats external F6 evidence as
repo Gap-6 acceptance.
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
GAP6_TESTS = ROOT / "tests" / "ops" / "test_gap6_dry_run_proof_criteria_contract_v0.py"
HARDENING_OWNER = ROOT / "tests" / "ops" / "test_scheduler_dry_run_hardening_source_contract_v0.py"
FINAL_MACHINE_LINES_HEADER = "## Final Machine Lines"
GAP6_SECTION_HEADER = "## Gap 6 Dry-Run Proof Criteria Contract v0"
GAP6_GOVERNED_REFLECTION_HEADER = "## Gap 6 Governed Dry-Run Proof Acceptance Reflection v0"
GAP6_RC0_OBSERVED_REFLECTION_HEADER = (
    "## Gap 6 Governed Bounded Dry-Run RC0 Observed Evidence Reflection v0"
)
GAP4_GOVERNED_REFLECTION_HEADER = "## Gap 4 Governed Output Evidence Acceptance Reflection v0"
_MARKER_TRUE = "=true"

CANONICAL_BOUNDED_DRY_RUN_COMMAND_TIER2 = (
    "uv run python scripts/run_scheduler.py --config config/scheduler/jobs.toml "
    "--dry-run --once --verbose --include-tags paper_shadow_247,preflight,readonly"
)

DRIFT_GUARD_REQUIRED_FINAL_LINES = (
    "PREFLIGHT_REMAINS_BLOCKED=true",
    "READY_FOR_OPERATOR_ARMING=false",
    "PATH_B_LIFT_DISCUSSION_READY=false",
    "ALL_GAPS_CLOSED=false",
    "GAP6_DRY_RUN_RC0_OBSERVED=false",
    "GAP6_DRY_RUN_PROOF_ACCEPTED=false",
    "GAP6_DRY_RUN_PROOF_VERIFIED=false",
    "GAP2_CANONICAL_JOB_SET_VERIFIED=false",
    "GAP2_JOB_SET_ENABLED=false",
    "SECTION5_GAP_CLOSURE_EXECUTED=false",
)

DRIFT_GUARD_FORBIDDEN_REPO_TOKENS = (
    "GAP6_DRY_RUN_RC0_OBSERVED_EXTERNAL=true",
    "GAP6_DRY_RUN_RC0_OBSERVED=true",
    "GAP6_DRY_RUN_PROOF_ACCEPTED=true",
    "GAP6_DRY_RUN_PROOF_VERIFIED=true",
    "WORKSHEET_COMPLETE=true",
    "SHADOW_24_7_AUTHORIZED=true",
    "PATH_B_LIFT_DISCUSSION_READY=true",
    "ALL_GAPS_CLOSED=true",
    "READY_FOR_OPERATOR_ARMING=true",
    "PREFLIGHT_REMAINS_BLOCKED=false",
    "GAP2_CANONICAL_JOB_SET_VERIFIED=true",
    "GAP2_JOB_SET_ENABLED=true",
)


def _final_machine_lines(text: str) -> str:
    return text.split(FINAL_MACHINE_LINES_HEADER, 1)[1]


def _gap6_criteria_section(text: str) -> str:
    return text.split(GAP6_SECTION_HEADER, 1)[1].split("## Gap 5 Stop Criteria Contract v0", 1)[0]


def _gap6_governed_reflection_section(text: str) -> str:
    return text.split(GAP6_GOVERNED_REFLECTION_HEADER, 1)[1].split(
        GAP6_RC0_OBSERVED_REFLECTION_HEADER, 1
    )[0]


def _gap6_rc0_observed_reflection_section(text: str) -> str:
    return text.split(GAP6_RC0_OBSERVED_REFLECTION_HEADER, 1)[1].split(
        GAP4_GOVERNED_REFLECTION_HEADER, 1
    )[0]


def _section5_text() -> str:
    return SECTION5_DOC.read_text(encoding="utf-8")


def test_gap6_external_repo_drift_guard_final_machine_lines_remain_blocked_v0() -> None:
    block = _final_machine_lines(_section5_text())
    for marker in DRIFT_GUARD_REQUIRED_FINAL_LINES:
        assert marker in block


def test_gap6_external_repo_drift_guard_repo_ssot_forbids_external_gap6_observed_token_v0() -> None:
    text = _section5_text()
    assert "GAP6_DRY_RUN_RC0_OBSERVED_EXTERNAL=true" not in text
    assert "GAP6_DRY_RUN_PROOF_ACCEPTED_EXTERNAL=true" not in text
    assert "GAP6_DRY_RUN_RC0_OBSERVED=false" in text


def test_gap6_external_repo_drift_guard_repo_ssot_forbids_lift_and_verified_tokens_v0() -> None:
    block = _final_machine_lines(_section5_text())
    lines = {line.strip() for line in block.splitlines()}
    for token in DRIFT_GUARD_FORBIDDEN_REPO_TOKENS:
        assert token not in lines


def test_gap6_external_repo_drift_guard_criteria_complete_does_not_close_gaps_v0() -> None:
    text = _section5_text()
    assert "SECTION5_OWNER_MAP_CONTRACT_V0=true" in text
    assert "SECTION5_OWNER_MAP_CONTRACT_V0_COMPLETE=true" in text
    assert "ALL_GAPS_CLOSED=false" in text
    assert "GAP6_DRY_RUN_PROOF_CRITERIA_CONTRACT_V0=true" in text
    assert "GAP6_CRITERIA_ONLY=true" in text
    assert "GAP6_DRY_RUN_PROOF_ACCEPTED=false" in text


def test_gap6_external_repo_drift_guard_preflight_contract_remains_blocked_v0() -> None:
    text = PREFLIGHT_CONTRACT.read_text(encoding="utf-8")
    assert "Current status: **BLOCKED**." in text
    assert "Evidence ≠ approval" in text


def test_gap6_external_repo_drift_guard_gap6_section_preserves_evidence_not_approval_v0() -> None:
    gap6_section = _gap6_criteria_section(_section5_text())
    assert "does not claim RC=0 was observed" in gap6_section
    assert "does not accept or verify any proof" in gap6_section
    assert "GAP6_DRY_RUN_PROOF_ACCEPTED=false" in gap6_section
    lines = {line.strip() for line in gap6_section.splitlines()}
    assert "GAP6_DRY_RUN_PROOF_ACCEPTED=true" not in lines


def test_gap6_external_repo_drift_guard_shadow_24_7_not_authorized_in_repo_ssot_v0() -> None:
    text = _section5_text()
    assert "SHADOW_24_7_AUTHORIZED=true" not in text
    block = _final_machine_lines(text)
    assert "SHADOW_24_7_AUTHORIZED=true" not in block


def test_gap6_external_repo_drift_guard_owner_crosslinks_gap6_criteria_tests_v0() -> None:
    assert GAP6_TESTS.is_file()
    text = GAP6_TESTS.read_text(encoding="utf-8")
    assert "test_gap6_external_repo_drift_guard_contract_v0.py" in text


def test_gap6_external_repo_drift_guard_owner_crosslinks_hardening_source_contract_v0() -> None:
    assert HARDENING_OWNER.is_file()
    text = HARDENING_OWNER.read_text(encoding="utf-8")
    assert "test_gap6_external_repo_drift_guard_contract_v0.py" in text
    lines = {line.strip() for line in text.splitlines()}
    assert ("GAP6_DRY_RUN_RC0_OBSERVED" + _MARKER_TRUE) not in lines


def test_gap6_external_repo_drift_guard_governed_reflection_scoped_acceptance_v0() -> None:
    text = _section5_text()
    reflection = _gap6_governed_reflection_section(text)
    criteria = _gap6_criteria_section(text)
    block = _final_machine_lines(text)

    assert "GAP6_DRY_RUN_PROOF_GOVERNED_REFLECTION_V0=true" in reflection
    assert "GAP6_DRY_RUN_PROOF_ACCEPTED=true" in reflection
    assert "ACCEPTED_MODE=BOUNDED_DRY_RUN_PROOF" in reflection
    assert "NO_REPO_FLAG_LIFT_FROM_EXTERNAL_ACCEPTANCE=true" in reflection
    assert "EXTERNAL_ACCEPTANCE_RECORD_POINTER=" in reflection
    assert "GAP6_DRY_RUN_PROOF_ACCEPTED_EXTERNAL=true" not in text
    assert "GAP6_DRY_RUN_RC0_OBSERVED_EXTERNAL=true" not in text
    assert "does not verify Gap-4 output evidence paths" in reflection
    assert "does not verify Gap-7 risk boundaries" in reflection
    assert "does not enforce Gap-2a.1 primary evidence" in reflection
    assert "does not authorize scheduler execution" in reflection
    assert "does not enable operator arming" in reflection
    assert "does not open Path-B lift discussion" in reflection
    assert "does not start or authorize Runtime, Paper, Shadow, Testnet, or Live" in reflection
    assert "does not modify the existing Gap-6 criteria block" in reflection
    assert "does not modify Final Machine Lines" in reflection
    assert "Evidence acceptance is not runtime authorization" in reflection
    assert "GAP6_DRY_RUN_PROOF_ACCEPTED=false" in criteria
    assert "GAP6_DRY_RUN_PROOF_ACCEPTED=false" in block
    assert "GAP6_DRY_RUN_RC0_OBSERVED=false" in block
    assert "GAP4_OUTPUT_EVIDENCE_PATHS_VERIFIED=false" in block
    assert "GAP7_RISK_BOUNDARY_VERIFIED=true" in block
    assert "GAP2A1_PRIMARY_EVIDENCE_ENFORCED=false" in block
    assert "GAP1_SCHEDULER_EXECUTION_AUTHORIZED=false" in block
    assert "GAP3_SCHEDULER_EXECUTION_AUTHORIZED=false" in block
    assert "READY_FOR_OPERATOR_ARMING=false" in block
    assert "PATH_B_LIFT_DISCUSSION_READY=false" in block
    assert "PREFLIGHT_REMAINS_BLOCKED=true" in block


def test_gap6_rc0_observed_governed_reflection_scoped_evidence_v0() -> None:
    text = _section5_text()
    reflection = _gap6_rc0_observed_reflection_section(text)
    criteria = _gap6_criteria_section(text)
    block = _final_machine_lines(text)

    assert "GAP6_BOUNDED_DRY_RUN_RC0_OBSERVED_GOVERNED_REFLECTION_V0=true" in reflection
    assert "GAP6_DRY_RUN_RC0_OBSERVED=true" in reflection
    assert "ACCEPTED_MODE=BOUNDED_TIER2_TAG_FILTERED_DRY_RUN_RC0" in reflection
    assert "EXIT_CODE=0" in reflection
    assert "DRY_RUN_EXECUTED=true" in reflection
    assert "DRY_RUN_ONCE=true" in reflection
    assert "INCLUDE_TAGS=paper_shadow_247,preflight,readonly" in reflection
    assert CANONICAL_BOUNDED_DRY_RUN_COMMAND_TIER2 in reflection
    assert "UNEXPECTED_EXECUTION_OBSERVED=false" in reflection
    assert "LEGACY_JOBS_EXCLUDED=true" in reflection
    assert "CANONICAL_JOB_SCOPE_RESPECTED=true" in reflection
    assert "paper_shadow_247_paper_only_preflight_status_v0" in reflection
    assert "EXTERNAL_EVIDENCE_BUNDLE_POINTER=" in reflection
    assert (
        "gap6_bounded_dry_run_evidence_capture_operator_authorized_v0_20260603T153911Z"
        in reflection
    )
    assert "NO_REPO_FLAG_LIFT_FROM_EXTERNAL_ACCEPTANCE=true" in reflection
    assert "does not modify Final Machine Lines" in reflection
    assert "does not lift preflight" in reflection
    assert "Evidence observation is not runtime authorization" in reflection
    assert "GAP6_DRY_RUN_RC0_OBSERVED=false" in criteria
    assert "GAP6_DRY_RUN_RC0_OBSERVED=false" in block
    assert "ALL_GAPS_CLOSED=false" in block
    assert "READY_FOR_OPERATOR_ARMING=false" in block
    assert "GAP7_RISK_BOUNDARY_VERIFIED=true" in block
    reflection_lines = {line.strip() for line in reflection.splitlines()}
    criteria_lines = {line.strip() for line in criteria.splitlines()}
    block_lines = {line.strip() for line in block.splitlines()}
    assert "GAP6_DRY_RUN_RC0_OBSERVED=true" in reflection_lines
    assert "GAP6_DRY_RUN_RC0_OBSERVED=true" not in criteria_lines
    assert "GAP6_DRY_RUN_RC0_OBSERVED=true" not in block_lines
    assert "GAP6_DRY_RUN_RC0_OBSERVED_EXTERNAL=true" not in text
