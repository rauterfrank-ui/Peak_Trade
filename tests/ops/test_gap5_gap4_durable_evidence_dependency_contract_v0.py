"""Static contract for Gap-5↔Gap-4 durable evidence dependency v0.

Reads repo markdown/source only. Never executes stop/scheduler/runtime/evidence helpers,
never copies/moves/archives evidence, never reads external archive paths as pass/fail SSOT,
and never treats planning/drift guards as verified durable chains or stop proof acceptance.
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
GAP4_DRIFT_GUARD = (
    ROOT / "tests" / "ops" / "test_gap4_output_evidence_paths_drift_guard_contract_v0.py"
)
GAP5_DRIFT_GUARD = ROOT / "tests" / "ops" / "test_gap5_stop_criteria_drift_guard_contract_v0.py"
HARDENING_OWNER = ROOT / "tests" / "ops" / "test_scheduler_dry_run_hardening_source_contract_v0.py"
FINAL_MACHINE_LINES_HEADER = "## Final Machine Lines"
GAP4_SECTION_HEADER = "## Gap 4 Output/Evidence Paths Contract v0"
GAP5_SECTION_HEADER = "## Gap 5 Stop Criteria Contract v0"
GAP2A1_SECTION_HEADER = "## §2a.1 Primary Evidence Enforcement Contract v0"
_MARKER_TRUE = "=true"

GAP5_STOP_PROOF_REQUIRES_DURABLE_GAP4_CHAIN = True
GAP4_DURABLE_CHAIN_IS_FUTURE_REQUIREMENT = True
TMP_CANNOT_SATISFY_DURABLE_PROOF_CHAIN = True
EVIDENCE_EQUALS_APPROVAL = False
CRITERIA_COMPLETE_EQUALS_GAP_CLOSED = False

DURABLE_EVIDENCE_SURFACES = (
    "primary_evidence_retention_v0.py",
    "durable_closeout_copy_verify_v0.py",
)

DEPENDENCY_REQUIRED_FINAL_LINES = (
    "PREFLIGHT_REMAINS_BLOCKED=true",
    "READY_FOR_OPERATOR_ARMING=false",
    "PATH_B_LIFT_DISCUSSION_READY=false",
    "ALL_GAPS_CLOSED=false",
    "GAP4_OUTPUT_EVIDENCE_PATHS_VERIFIED=true",
    "GAP4_OUTPUT_EVIDENCE_DEFAULT_ON=false",
    "GAP2A1_PRIMARY_EVIDENCE_ENFORCED=false",
    "GAP5_STOP_REHEARSAL_EXECUTED=false",
    "GAP5_STOP_PROOF_ACCEPTED=true",
    "GAP5_TYPE2_WAIVER_GRANTED=false",
    "GAP6_DRY_RUN_PROOF_ACCEPTED=false",
)

DEPENDENCY_FORBIDDEN_REPO_TOKENS = (
    "GAP5_STOP_CRITERIA_VERIFIED=true",
    "GAP5_STOP_REHEARSAL_EXECUTED=true",
    "GAP5_TYPE2_WAIVER_GRANTED=true",
    "GAP2A1_PRIMARY_EVIDENCE_ENFORCED=true",
    "GAP6_DRY_RUN_PROOF_ACCEPTED=true",
    "WORKSHEET_COMPLETE=true",
    "PATH_B_LIFT_DISCUSSION_READY=true",
    "ALL_GAPS_CLOSED=true",
    "READY_FOR_OPERATOR_ARMING=true",
    "PREFLIGHT_REMAINS_BLOCKED=false",
)


def _final_machine_lines(text: str) -> str:
    return text.split(FINAL_MACHINE_LINES_HEADER, 1)[1]


def _gap4_section(text: str) -> str:
    return text.split(GAP4_SECTION_HEADER, 1)[1].split(
        "## Gap 6 Dry-Run Proof Criteria Contract v0", 1
    )[0]


def _gap5_section(text: str) -> str:
    return text.split(GAP5_SECTION_HEADER, 1)[1].split("## Gap 2 Canonical Job Set Contract v0", 1)[
        0
    ]


def _gap2a1_section(text: str) -> str:
    return text.split(GAP2A1_SECTION_HEADER, 1)[1].split(
        "## Gap 1 Execute Entrypoint Contract v0", 1
    )[0]


def _section5_text() -> str:
    return SECTION5_DOC.read_text(encoding="utf-8")


def test_gap5_gap4_durable_evidence_dependency_module_constants_v0() -> None:
    assert GAP5_STOP_PROOF_REQUIRES_DURABLE_GAP4_CHAIN is True
    assert GAP4_DURABLE_CHAIN_IS_FUTURE_REQUIREMENT is True
    assert TMP_CANNOT_SATISFY_DURABLE_PROOF_CHAIN is True
    assert EVIDENCE_EQUALS_APPROVAL is False
    assert CRITERIA_COMPLETE_EQUALS_GAP_CLOSED is False


def test_gap5_gap4_durable_evidence_dependency_final_machine_lines_remain_blocked_v0() -> None:
    block = _final_machine_lines(_section5_text())
    for marker in DEPENDENCY_REQUIRED_FINAL_LINES:
        assert marker in block


def test_gap5_gap4_durable_evidence_dependency_forbids_lift_and_verified_tokens_v0() -> None:
    block = _final_machine_lines(_section5_text())
    lines = {line.strip() for line in block.splitlines()}
    for token in DEPENDENCY_FORBIDDEN_REPO_TOKENS:
        assert token not in lines


def test_gap5_gap4_durable_evidence_dependency_gap5_requires_durable_gap4_chain_v0() -> None:
    section = _gap5_section(_section5_text())
    assert "linked through Gap 4" in section
    assert "archived outside `/tmp`" in section
    assert "manifest-verified" in section
    assert "does not accept or verify stop proof" in section
    for surface in DURABLE_EVIDENCE_SURFACES:
        assert surface in section


def test_gap5_gap4_durable_evidence_dependency_gap4_planning_not_verified_chain_v0() -> None:
    section = _gap4_section(_section5_text())
    assert "GAP4_OUTPUT_EVIDENCE_PATHS_VERIFIED=false" in section
    assert "contract-only, not verified" in section
    assert "archived outside `/tmp`" in section
    assert "checksummed, verified" in section
    lines = {line.strip() for line in section.splitlines()}
    assert "GAP4_OUTPUT_EVIDENCE_PATHS_VERIFIED=true" not in lines


def test_gap5_gap4_durable_evidence_dependency_gap5_cannot_prove_while_gap4_unverified_v0() -> None:
    text = _section5_text()
    gap4 = _gap4_section(text)
    gap5 = _gap5_section(text)
    block = _final_machine_lines(text)

    assert "GAP4_OUTPUT_EVIDENCE_PATHS_VERIFIED=false" in gap4
    assert "GAP5_STOP_PROOF_ACCEPTED=false" in gap5
    assert "GAP5_STOP_REHEARSAL_EXECUTED=false" in gap5
    assert "GAP4_OUTPUT_EVIDENCE_PATHS_VERIFIED=true" in block
    assert "GAP5_STOP_PROOF_ACCEPTED=true" in block
    assert "GAP5_STOP_CRITERIA_VERIFIED=true" not in text


def test_gap5_gap4_durable_evidence_dependency_gap2a1_remains_not_enforced_v0() -> None:
    section = _gap2a1_section(_section5_text())
    block = _final_machine_lines(_section5_text())
    assert "GAP2A1_PRIMARY_EVIDENCE_ENFORCED=false" in section
    assert "GAP2A1_ENFORCEMENT_OPT_IN_ONLY=true" in section
    assert "GAP2A1_PRIMARY_EVIDENCE_ENFORCED=false" in block


def test_gap5_gap4_durable_evidence_dependency_tmp_not_canonical_proof_ready_v0() -> None:
    gap4 = _gap4_section(_section5_text())
    gap5 = _gap5_section(_section5_text())
    hardening = HARDENING_OWNER.read_text(encoding="utf-8")
    assert "archived outside `/tmp`" in gap4
    assert "archived outside `/tmp`" in gap5
    assert "from scripts.ops.primary_evidence_retention_v0 import is_under_tmp" in hardening


def test_gap5_gap4_durable_evidence_dependency_future_manifest_requirement_not_executed_v0() -> (
    None
):
    gap4 = _gap4_section(_section5_text())
    gap5 = _gap5_section(_section5_text())
    assert "checksummed, verified" in gap4
    assert "manifest-verified" in gap5
    assert GAP4_DURABLE_CHAIN_IS_FUTURE_REQUIREMENT is True


def test_gap5_gap4_durable_evidence_dependency_stop_proof_not_from_planning_only_v0() -> None:
    gap5 = _gap5_section(_section5_text())
    block = _final_machine_lines(_section5_text())
    assert "criteria-only" in gap5
    assert "not proof-accepted" in gap5
    assert "GAP5_STOP_PROOF_ACCEPTED=true" in block
    preflight = PREFLIGHT_CONTRACT.read_text(encoding="utf-8")
    assert "Evidence ≠ approval" in preflight


def test_gap5_gap4_durable_evidence_dependency_drift_guards_are_not_proof_or_chain_v0() -> None:
    assert GAP4_DRIFT_GUARD.is_file()
    assert GAP5_DRIFT_GUARD.is_file()
    gap4_text = GAP4_DRIFT_GUARD.read_text(encoding="utf-8")
    gap5_text = GAP5_DRIFT_GUARD.read_text(encoding="utf-8")
    assert "GAP4_OUTPUT_EVIDENCE_PATHS_VERIFIED=false" in gap4_text
    assert "GAP5_STOP_PROOF_ACCEPTED=false" in gap5_text
    assert "DRIFT_GUARD_FORBIDDEN_GAP4_REPO_TOKENS" in gap4_text
    assert "DRIFT_GUARD_FORBIDDEN_GAP5_REPO_TOKENS" in gap5_text


def test_gap5_gap4_durable_evidence_dependency_gap6_tokens_untouched_v0() -> None:
    block = _final_machine_lines(_section5_text())
    assert "GAP6_DRY_RUN_PROOF_ACCEPTED=false" in block
    assert "GAP6_DRY_RUN_RC0_OBSERVED=true" in block
    assert "GAP6_DRY_RUN_PROOF_VERIFIED=false" in block


def test_gap5_gap4_durable_evidence_dependency_criteria_complete_does_not_close_gaps_v0() -> None:
    text = _section5_text()
    assert "SECTION5_OWNER_MAP_CONTRACT_V0_COMPLETE=true" in text
    assert "ALL_GAPS_CLOSED=false" in text
    assert "GAP4_OUTPUT_EVIDENCE_PATHS_CONTRACT_V0=true" in text
    assert "GAP5_STOP_CRITERIA_CONTRACT_V0=true" in text


def test_gap5_gap4_durable_evidence_dependency_evidence_not_approval_language_v0() -> None:
    gap4 = _gap4_section(_section5_text())
    gap5 = _gap5_section(_section5_text())
    assert "contract-only" in gap4
    assert "criteria-only" in gap5
    assert "does not lift preflight" in gap4
    assert "does not accept or verify stop proof" in gap5


def test_gap5_gap4_durable_evidence_dependency_module_is_static_no_subprocess_v0() -> None:
    import ast

    tree = ast.parse(Path(__file__).read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                assert alias.name != "subprocess"
        elif isinstance(node, ast.ImportFrom):
            assert node.module != "subprocess"


def test_gap5_gap4_durable_evidence_dependency_owner_crosslinks_gap4_drift_guard_v0() -> None:
    assert GAP4_DRIFT_GUARD.is_file()
    text = GAP4_DRIFT_GUARD.read_text(encoding="utf-8")
    assert "test_gap5_gap4_durable_evidence_dependency_contract_v0.py" in text


def test_gap5_gap4_durable_evidence_dependency_owner_crosslinks_gap5_drift_guard_v0() -> None:
    assert GAP5_DRIFT_GUARD.is_file()
    text = GAP5_DRIFT_GUARD.read_text(encoding="utf-8")
    assert "test_gap5_gap4_durable_evidence_dependency_contract_v0.py" in text


def test_gap5_gap4_durable_evidence_dependency_owner_crosslinks_hardening_source_contract_v0() -> (
    None
):
    assert HARDENING_OWNER.is_file()
    text = HARDENING_OWNER.read_text(encoding="utf-8")
    assert "test_gap5_gap4_durable_evidence_dependency_contract_v0.py" in text
    lines = {line.strip() for line in text.splitlines()}
    assert ("GAP5_STOP_PROOF_ACCEPTED" + _MARKER_TRUE) not in lines
    assert ("GAP4_OUTPUT_EVIDENCE_PATHS_VERIFIED" + _MARKER_TRUE) not in lines


def test_gap5_gap4_durable_evidence_dependency_owner_crosslinks_rehearsal_classification_v0() -> (
    None
):
    classification = (
        ROOT / "tests" / "ops" / "test_gap5_stop_rehearsal_evidence_classification_contract_v0.py"
    )
    assert classification.is_file()
    text = classification.read_text(encoding="utf-8")
    assert "test_gap5_gap4_durable_evidence_dependency_contract_v0.py" in text
    assert "GAP5_STOP_PROOF_ACCEPTED=false" in text


def test_gap5_gap4_durable_evidence_dependency_owner_crosslinks_gap2a1_drift_guard_v0() -> None:
    drift_guard = (
        ROOT
        / "tests"
        / "ops"
        / "test_gap2a1_primary_evidence_enforcement_drift_guard_contract_v0.py"
    )
    assert drift_guard.is_file()
    text = drift_guard.read_text(encoding="utf-8")
    assert "test_gap5_gap4_durable_evidence_dependency_contract_v0.py" in text
    assert "GAP2A1_PRIMARY_EVIDENCE_ENFORCED=false" in text
