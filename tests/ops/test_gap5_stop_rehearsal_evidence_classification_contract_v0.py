"""Static contract for Gap-5 stop-rehearsal evidence classification v0.

Reads repo markdown/source only. Never executes stop/scheduler/runtime, never copies/moves/archives
evidence, never reads external archive paths as pass/fail SSOT, and never treats external rehearsal
records as repo ``GAP5_STOP_REHEARSAL_EXECUTED`` or ``GAP5_STOP_PROOF_ACCEPTED``.
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
GAP5_DRIFT_GUARD = ROOT / "tests" / "ops" / "test_gap5_stop_criteria_drift_guard_contract_v0.py"
GAP5_GAP4_DEPENDENCY = (
    ROOT / "tests" / "ops" / "test_gap5_gap4_durable_evidence_dependency_contract_v0.py"
)
HARDENING_OWNER = ROOT / "tests" / "ops" / "test_scheduler_dry_run_hardening_source_contract_v0.py"
FINAL_MACHINE_LINES_HEADER = "## Final Machine Lines"
GAP5_SECTION_HEADER = "## Gap 5 Stop Criteria Contract v0"
GAP5_GOVERNED_REFLECTION_HEADER = "## Gap 5 Governed Stop Proof Acceptance Reflection v0"
_MARKER_TRUE = "=true"

EXTERNAL_REHEARSAL_RECORD_NOT_REPO_SSOT = True
REHEARSAL_EXECUTED_EXTERNAL_NOT_GAP5_STOP_REHEARSAL_EXECUTED = True
STOP_PROOF_OBSERVED_EXTERNAL_NOT_GAP5_STOP_PROOF_ACCEPTED = True
EVIDENCE_EQUALS_APPROVAL = False
CRITERIA_COMPLETE_EQUALS_GAP_CLOSED = False
FUTURE_REHEARSAL_ACCEPTANCE_REQUIRES_GOVERNED_REPO_PROCESS = True

CLASSIFICATION_REQUIRED_FINAL_LINES = (
    "PREFLIGHT_LIFTED_BY_CLASS4_POLICY=true",
    "READY_FOR_OPERATOR_ARMING=true",
    "ARMING_NOT_EXECUTE=true",
    "PATH_B_LIFT_DISCUSSION_READY=false",
    "ALL_GAPS_CLOSED=true",
    "GAP5_STOP_REHEARSAL_EXECUTED=true",
    "GAP5_STOP_PROOF_ACCEPTED=true",
    "GAP5_TYPE2_WAIVER_GRANTED=false",
    "GAP4_OUTPUT_EVIDENCE_PATHS_VERIFIED=true",
    "GAP2A1_PRIMARY_EVIDENCE_ENFORCED=true",
    "GAP6_DRY_RUN_PROOF_ACCEPTED=true",
)

CLASSIFICATION_FORBIDDEN_REPO_TOKENS = (
    "GAP5_STOP_CRITERIA_VERIFIED=true",
    "REHEARSAL_EXECUTED=true",
    "REHEARSAL_OBSERVED=true",
    "STOP_PROOF_OBSERVED=true",
    "GAP5_STOP_REHEARSAL_EXECUTED_EXTERNAL=true",
    "GAP5_STOP_PROOF_ACCEPTED_EXTERNAL=true",
    "EXTERNAL_REHEARSAL_EVIDENCE_ACCEPTED=true",
    "WORKSHEET_COMPLETE=true",
    "PATH_B_LIFT_DISCUSSION_READY=true",
    "SHADOW_24_7_AUTHORIZED=true",
)


def _final_machine_lines(text: str) -> str:
    return text.split(FINAL_MACHINE_LINES_HEADER, 1)[1]


def _gap5_section(text: str) -> str:
    return text.split(GAP5_SECTION_HEADER, 1)[1].split("## Gap 2 Canonical Job Set Contract v0", 1)[
        0
    ]


def _gap5_governed_reflection_section(text: str) -> str:
    return text.split(GAP5_GOVERNED_REFLECTION_HEADER, 1)[1].split(FINAL_MACHINE_LINES_HEADER, 1)[0]


def _section5_text() -> str:
    return SECTION5_DOC.read_text(encoding="utf-8")


def test_gap5_rehearsal_classification_module_constants_v0() -> None:
    assert EXTERNAL_REHEARSAL_RECORD_NOT_REPO_SSOT is True
    assert REHEARSAL_EXECUTED_EXTERNAL_NOT_GAP5_STOP_REHEARSAL_EXECUTED is True
    assert STOP_PROOF_OBSERVED_EXTERNAL_NOT_GAP5_STOP_PROOF_ACCEPTED is True
    assert EVIDENCE_EQUALS_APPROVAL is False
    assert CRITERIA_COMPLETE_EQUALS_GAP_CLOSED is False
    assert FUTURE_REHEARSAL_ACCEPTANCE_REQUIRES_GOVERNED_REPO_PROCESS is True


def test_gap5_rehearsal_classification_final_machine_lines_remain_blocked_v0() -> None:
    block = _final_machine_lines(_section5_text())
    for marker in CLASSIFICATION_REQUIRED_FINAL_LINES:
        assert marker in block


def test_gap5_rehearsal_classification_forbids_lift_and_external_tokens_v0() -> None:
    block = _final_machine_lines(_section5_text())
    lines = {line.strip() for line in block.splitlines()}
    for token in CLASSIFICATION_FORBIDDEN_REPO_TOKENS:
        assert token not in lines


def test_gap5_rehearsal_classification_repo_ssot_forbids_external_rehearsal_tokens_v0() -> None:
    lines = {line.strip() for line in _section5_text().splitlines()}
    external_tokens = (
        "REHEARSAL_EXECUTED=true",
        "REHEARSAL_OBSERVED=true",
        "STOP_PROOF_OBSERVED=true",
        "GAP5_STOP_REHEARSAL_EXECUTED_EXTERNAL=true",
        "GAP5_STOP_PROOF_ACCEPTED_EXTERNAL=true",
        "EXTERNAL_REHEARSAL_EVIDENCE_ACCEPTED=true",
    )
    for token in external_tokens:
        assert token not in lines


def test_gap5_rehearsal_classification_gap5_section_preserves_not_rehearsed_not_proof_v0() -> None:
    section = _gap5_section(_section5_text())
    assert "GAP5_STOP_REHEARSAL_EXECUTED=false" in section
    assert "GAP5_STOP_PROOF_ACCEPTED=false" in section
    assert "does not execute or claim a stop-tool rehearsal" in section
    assert "does not accept or verify stop proof" in section
    assert "criteria-only" in section
    assert "not rehearsal-executed" in section
    assert "not proof-accepted" in section
    lines = {line.strip() for line in section.splitlines()}
    for token in CLASSIFICATION_FORBIDDEN_REPO_TOKENS:
        assert token not in lines


def test_gap5_rehearsal_classification_preflight_evidence_not_approval_v0() -> None:
    text = PREFLIGHT_CONTRACT.read_text(encoding="utf-8")
    assert "Current status: **BLOCKED**." in text
    assert "Evidence ≠ approval" in text


def test_gap5_rehearsal_classification_drift_guard_is_not_rehearsal_executed_v0() -> None:
    assert GAP5_DRIFT_GUARD.is_file()
    text = GAP5_DRIFT_GUARD.read_text(encoding="utf-8")
    assert "GAP5_STOP_REHEARSAL_EXECUTED=true" in text
    assert "DRIFT_GUARD_FORBIDDEN_GAP5_REPO_TOKENS" in text
    assert "GAP5_STOP_PROOF_ACCEPTED=false" in text
    assert "never treats external F5 approval or planning" in text
    assert "charters as repo Gap-5 rehearsal execution or proof acceptance" in text


def test_gap5_rehearsal_classification_dependency_is_not_proof_acceptance_v0() -> None:
    assert GAP5_GAP4_DEPENDENCY.is_file()
    text = GAP5_GAP4_DEPENDENCY.read_text(encoding="utf-8")
    assert "GAP5_STOP_PROOF_REQUIRES_DURABLE_GAP4_CHAIN" in text
    assert "GAP4_DURABLE_CHAIN_IS_FUTURE_REQUIREMENT" in text
    assert "GAP5_STOP_PROOF_ACCEPTED=false" in text
    assert (
        "never treats planning/drift guards as verified durable chains or stop proof acceptance"
        in text
    )


def test_gap5_rehearsal_classification_gap4_gap6_tokens_untouched_v0() -> None:
    block = _final_machine_lines(_section5_text())
    assert "GAP4_OUTPUT_EVIDENCE_PATHS_VERIFIED=true" in block
    assert "GAP6_DRY_RUN_PROOF_ACCEPTED=true" in block
    assert "GAP6_DRY_RUN_RC0_OBSERVED=true" in block
    assert "GAP6_DRY_RUN_PROOF_VERIFIED=true" in block


def test_gap5_rehearsal_classification_criteria_complete_does_not_close_gaps_v0() -> None:
    text = _section5_text()
    assert "SECTION5_OWNER_MAP_CONTRACT_V0_COMPLETE=true" in text
    assert "ALL_GAPS_CLOSED=false" in text
    assert "GAP5_STOP_CRITERIA_CONTRACT_V0=true" in text
    assert "GAP5_STOP_PROOF_ACCEPTED=false" in _gap5_section(text)
    assert "GAP5_STOP_PROOF_ACCEPTED=true" in _final_machine_lines(text)


def test_gap5_rehearsal_classification_module_is_static_no_subprocess_v0() -> None:
    import ast

    tree = ast.parse(Path(__file__).read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                assert alias.name != "subprocess"
        elif isinstance(node, ast.ImportFrom):
            assert node.module != "subprocess"


def test_gap5_rehearsal_classification_owner_crosslinks_drift_guard_v0() -> None:
    assert GAP5_DRIFT_GUARD.is_file()
    text = GAP5_DRIFT_GUARD.read_text(encoding="utf-8")
    assert "test_gap5_stop_rehearsal_evidence_classification_contract_v0.py" in text


def test_gap5_rehearsal_classification_owner_crosslinks_dependency_v0() -> None:
    assert GAP5_GAP4_DEPENDENCY.is_file()
    text = GAP5_GAP4_DEPENDENCY.read_text(encoding="utf-8")
    assert "test_gap5_stop_rehearsal_evidence_classification_contract_v0.py" in text


def test_gap5_rehearsal_classification_owner_crosslinks_hardening_source_contract_v0() -> None:
    assert HARDENING_OWNER.is_file()
    text = HARDENING_OWNER.read_text(encoding="utf-8")
    assert "test_gap5_stop_rehearsal_evidence_classification_contract_v0.py" in text
    lines = {line.strip() for line in text.splitlines()}
    assert ("GAP5_STOP_REHEARSAL_EXECUTED" + _MARKER_TRUE) not in lines
    assert ("GAP5_STOP_PROOF_ACCEPTED" + _MARKER_TRUE) not in lines


def test_gap5_rehearsal_classification_verified_final_line_scoped_repo_token_v0() -> None:
    text = _section5_text()
    reflection = text.split(
        "## Gap 5 Governed Stop Rehearsal Verified Final-Line Reflection v0", 1
    )[1].split("## Gap 6 Governed Dry-Run Proof Acceptance Reflection v0", 1)[0]
    criteria = _gap5_section(text)
    block = _final_machine_lines(text)

    assert "GAP5_STOP_REHEARSAL_VERIFIED_FINAL_LINE_GOVERNED_REFLECTION_V0=true" in reflection
    assert "GAP5_STOP_REHEARSAL_EXECUTED=true" in reflection
    assert "GAP5_STOP_REHEARSAL_EXECUTED=false" in criteria
    assert "GAP5_STOP_REHEARSAL_EXECUTED=true" in block
    assert "STOP_REHEARSAL_EXECUTED_EXTERNAL_BUNDLE=true" in reflection
    assert "GAP5_STOP_REHEARSAL_EXECUTED_EXTERNAL=true" not in text


def test_gap5_rehearsal_classification_governed_reflection_allows_scoped_repo_token_v0() -> None:
    text = _section5_text()
    reflection = _gap5_governed_reflection_section(text)
    criteria = _gap5_section(text)
    block = _final_machine_lines(text)

    assert "GAP5_STOP_PROOF_ACCEPTED=true" in reflection
    assert "GAP5_STOP_PROOF_ACCEPTED=false" in criteria
    assert "GAP5_STOP_PROOF_ACCEPTED=true" in block
    assert "GAP5_STOP_PROOF_ACCEPTED_EXTERNAL=true" not in text
    assert "does not adopt external-only acceptance tokens as repo SSOT" in reflection
    assert FUTURE_REHEARSAL_ACCEPTANCE_REQUIRES_GOVERNED_REPO_PROCESS is True
    assert STOP_PROOF_OBSERVED_EXTERNAL_NOT_GAP5_STOP_PROOF_ACCEPTED is True
