"""Static contract for Gap-2a.1 primary-evidence enforcement drift guard v0.

Reads repo markdown/source only. Never executes scheduler/runtime/retention helpers,
never copies/moves/archives evidence, never reads external archive or tier-plan paths as
pass/fail SSOT, and never treats external evidence presence, manifest verification, or
tier-plan completion as repo ``GAP2A1_PRIMARY_EVIDENCE_ENFORCED``.
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
GAP2A1_CONTRACT = ROOT / "tests" / "ops" / "test_gap2a1_primary_evidence_enforcement_contract_v0.py"
GAP4_DRIFT_GUARD = (
    ROOT / "tests" / "ops" / "test_gap4_output_evidence_paths_drift_guard_contract_v0.py"
)
GAP5_GAP4_DEPENDENCY = (
    ROOT / "tests" / "ops" / "test_gap5_gap4_durable_evidence_dependency_contract_v0.py"
)
HARDENING_OWNER = ROOT / "tests" / "ops" / "test_scheduler_dry_run_hardening_source_contract_v0.py"
FINAL_MACHINE_LINES_HEADER = "## Final Machine Lines"
GAP2A1_SECTION_HEADER = "## §2a.1 Primary Evidence Enforcement Contract v0"
_MARKER_TRUE = "=true"

GAP2A1_ENFORCEMENT_PLANNED = True
GAP2A1_ENFORCEMENT_OPT_IN_ONLY = True
GAP2A1_ENFORCEMENT_DEFAULT_ON = False
GAP2A1_PRIMARY_EVIDENCE_ENFORCED = False
EXTERNAL_TIER_PLAN_NOT_REPO_SSOT = True
EXTERNAL_MANIFEST_VERIFY_NOT_ENFORCEMENT = True
DURABLE_ARCHIVE_EXISTENCE_NOT_ENFORCEMENT = True
EVIDENCE_EQUALS_APPROVAL = False
CRITERIA_COMPLETE_EQUALS_GAP_CLOSED = False
FUTURE_ENFORCEMENT_REQUIRES_EXPLICIT_OPT_IN_GO = True

DRIFT_GUARD_REQUIRED_FINAL_LINES = (
    "PREFLIGHT_REMAINS_BLOCKED=true",
    "READY_FOR_OPERATOR_ARMING=false",
    "PATH_B_LIFT_DISCUSSION_READY=false",
    "ALL_GAPS_CLOSED=false",
    "GAP2A1_PRIMARY_EVIDENCE_ENFORCED=false",
    "GAP2A1_ENFORCEMENT_DEFAULT_ON=false",
    "GAP4_OUTPUT_EVIDENCE_PATHS_VERIFIED=false",
    "GAP5_STOP_REHEARSAL_EXECUTED=false",
    "GAP5_STOP_PROOF_ACCEPTED=true",
    "GAP6_DRY_RUN_PROOF_ACCEPTED=false",
)

DRIFT_GUARD_FORBIDDEN_GAP2A1_REPO_TOKENS = (
    "GAP2A1_PRIMARY_EVIDENCE_ENFORCED=true",
    "GAP2A1_ENFORCEMENT_DEFAULT_ON=true",
    "GAP2A1_ENFORCEMENT_ACCEPTED=true",
    "GAP2A1_TIER_COMPLETE=true",
    "GAP2A1_TIER_5_SATISFIED=true",
    "EXTERNAL_TIER_PLAN_COMPLETE=true",
    "EXTERNAL_MANIFEST_VERIFY_RC0_IMPLIES_ENFORCED=true",
    "DURABLE_ARCHIVE_EXISTS_IMPLIES_ENFORCED=true",
    "EVIDENCE_PRESENCE_IMPLIES_ENFORCED=true",
    "GAP4_OUTPUT_EVIDENCE_PATHS_VERIFIED=true",
    "GAP6_DRY_RUN_PROOF_ACCEPTED=true",
    "WORKSHEET_COMPLETE=true",
    "PATH_B_LIFT_DISCUSSION_READY=true",
    "ALL_GAPS_CLOSED=true",
    "READY_FOR_OPERATOR_ARMING=true",
    "PREFLIGHT_REMAINS_BLOCKED=false",
    "SHADOW_24_7_AUTHORIZED=true",
)

EXTERNAL_CONFLATION_FORBIDDEN_REPO_TOKENS = (
    "GAP2A1_ENFORCEMENT_ACCEPTED=true",
    "GAP2A1_TIER_COMPLETE=true",
    "GAP2A1_TIER_5_SATISFIED=true",
    "EXTERNAL_TIER_PLAN_COMPLETE=true",
    "EXTERNAL_MANIFEST_VERIFY_RC0_IMPLIES_ENFORCED=true",
    "DURABLE_ARCHIVE_EXISTS_IMPLIES_ENFORCED=true",
    "EVIDENCE_PRESENCE_IMPLIES_ENFORCED=true",
    "EXTERNAL_GAP2A1_PRIMARY_EVIDENCE_ENFORCED=true",
)


def _final_machine_lines(text: str) -> str:
    return text.split(FINAL_MACHINE_LINES_HEADER, 1)[1]


def _gap2a1_section(text: str) -> str:
    return text.split(GAP2A1_SECTION_HEADER, 1)[1].split(
        "## Gap 1 Execute Entrypoint Contract v0", 1
    )[0]


def _section5_text() -> str:
    return SECTION5_DOC.read_text(encoding="utf-8")


def test_gap2a1_drift_guard_module_constants_v0() -> None:
    assert GAP2A1_ENFORCEMENT_PLANNED is True
    assert GAP2A1_ENFORCEMENT_OPT_IN_ONLY is True
    assert GAP2A1_ENFORCEMENT_DEFAULT_ON is False
    assert GAP2A1_PRIMARY_EVIDENCE_ENFORCED is False
    assert EXTERNAL_TIER_PLAN_NOT_REPO_SSOT is True
    assert EXTERNAL_MANIFEST_VERIFY_NOT_ENFORCEMENT is True
    assert DURABLE_ARCHIVE_EXISTENCE_NOT_ENFORCEMENT is True
    assert EVIDENCE_EQUALS_APPROVAL is False
    assert CRITERIA_COMPLETE_EQUALS_GAP_CLOSED is False
    assert FUTURE_ENFORCEMENT_REQUIRES_EXPLICIT_OPT_IN_GO is True


def test_gap2a1_drift_guard_final_machine_lines_remain_blocked_v0() -> None:
    block = _final_machine_lines(_section5_text())
    for marker in DRIFT_GUARD_REQUIRED_FINAL_LINES:
        assert marker in block


def test_gap2a1_drift_guard_forbids_lift_tokens_in_final_lines_v0() -> None:
    block = _final_machine_lines(_section5_text())
    lines = {line.strip() for line in block.splitlines()}
    for token in DRIFT_GUARD_FORBIDDEN_GAP2A1_REPO_TOKENS:
        assert token not in lines


def test_gap2a1_drift_guard_gap2a1_section_preserves_opt_in_not_enforced_v0() -> None:
    section = _gap2a1_section(_section5_text())
    lines = {line.strip() for line in section.splitlines()}
    assert "GAP2A1_PRIMARY_EVIDENCE_ENFORCED=false" in section
    assert "GAP2A1_ENFORCEMENT_DEFAULT_ON=false" in section
    assert "GAP2A1_ENFORCEMENT_OPT_IN_ONLY=true" in section
    assert "opt-in only" in section
    assert "intentionally non-authorizing" in section
    for token in (
        "GAP2A1_PRIMARY_EVIDENCE_ENFORCED=true",
        "GAP2A1_ENFORCEMENT_DEFAULT_ON=true",
    ):
        assert token not in lines


def test_gap2a1_drift_guard_repo_ssot_forbids_external_enforcement_tokens_v0() -> None:
    text = _section5_text()
    for token in EXTERNAL_CONFLATION_FORBIDDEN_REPO_TOKENS:
        assert token not in text


def test_gap2a1_drift_guard_preflight_evidence_not_approval_v0() -> None:
    text = PREFLIGHT_CONTRACT.read_text(encoding="utf-8")
    assert "Current status: **BLOCKED**." in text
    assert "Evidence ≠ approval" in text


def test_gap2a1_drift_guard_gap4_verified_not_enforcement_v0() -> None:
    assert GAP4_DRIFT_GUARD.is_file()
    text = GAP4_DRIFT_GUARD.read_text(encoding="utf-8")
    assert "GAP4_OUTPUT_EVIDENCE_PATHS_VERIFIED=false" in text
    assert "GAP2A1_PRIMARY_EVIDENCE_ENFORCED=false" in text
    assert "GAP4_OUTPUT_EVIDENCE_PATHS_VERIFIED = False" in text
    block = _final_machine_lines(_section5_text())
    assert "GAP4_OUTPUT_EVIDENCE_PATHS_VERIFIED=false" in block
    assert "GAP2A1_PRIMARY_EVIDENCE_ENFORCED=false" in block


def test_gap2a1_drift_guard_gap5_gap6_orthogonal_v0() -> None:
    block = _final_machine_lines(_section5_text())
    assert "GAP5_STOP_REHEARSAL_EXECUTED=false" in block
    assert "GAP5_STOP_PROOF_ACCEPTED=true" in block
    assert "GAP6_DRY_RUN_PROOF_ACCEPTED=false" in block
    assert "GAP6_DRY_RUN_RC0_OBSERVED=false" in block
    assert "GAP6_DRY_RUN_PROOF_VERIFIED=false" in block


def _module_preamble() -> str:
    return Path(__file__).read_text(encoding="utf-8").split("\ndef test_", 1)[0]


def test_gap2a1_drift_guard_tier_plan_not_repo_ssot_v0() -> None:
    preamble = _module_preamble()
    assert "Peak_Trade_runtime_evidence_archive" not in preamble
    assert "external_gap2a1_primary_evidence_enforcement_tier_plan" not in preamble
    assert EXTERNAL_TIER_PLAN_NOT_REPO_SSOT is True
    assert EXTERNAL_MANIFEST_VERIFY_NOT_ENFORCEMENT is True


def test_gap2a1_drift_guard_criteria_complete_does_not_close_gaps_v0() -> None:
    text = _section5_text()
    assert "SECTION5_OWNER_MAP_CONTRACT_V0_COMPLETE=true" in text
    assert "ALL_GAPS_CLOSED=false" in text
    assert "GAP2A1_PRIMARY_EVIDENCE_ENFORCEMENT_CONTRACT_V0=true" in text
    assert "GAP2A1_PRIMARY_EVIDENCE_ENFORCED=false" in text


def test_gap2a1_drift_guard_external_signals_not_enforcement_language_v0() -> None:
    section = _gap2a1_section(_section5_text())
    assert "does not enable default enforcement" in section
    assert "Evidence ≠ approval" not in section
    preflight = PREFLIGHT_CONTRACT.read_text(encoding="utf-8")
    assert "RUN_INCOMPLETE_WITHOUT_PRIMARY_EVIDENCE=true" in preflight
    assert "EVIDENCE_DOES_NOT_AUTHORIZE_RUNTIME=true" in preflight


def test_gap2a1_drift_guard_module_is_static_no_subprocess_v0() -> None:
    import ast

    tree = ast.parse(Path(__file__).read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                assert alias.name != "subprocess"
        elif isinstance(node, ast.ImportFrom):
            assert node.module != "subprocess"


def test_gap2a1_drift_guard_owner_crosslinks_contract_tests_v0() -> None:
    assert GAP2A1_CONTRACT.is_file()
    text = GAP2A1_CONTRACT.read_text(encoding="utf-8")
    assert "GAP2A1_PRIMARY_EVIDENCE_ENFORCED=false" in text


def test_gap2a1_drift_guard_owner_crosslinks_gap4_drift_guard_v0() -> None:
    assert GAP4_DRIFT_GUARD.is_file()
    text = GAP4_DRIFT_GUARD.read_text(encoding="utf-8")
    assert "test_gap2a1_primary_evidence_enforcement_drift_guard_contract_v0.py" in text


def test_gap2a1_drift_guard_owner_crosslinks_gap5_gap4_dependency_v0() -> None:
    assert GAP5_GAP4_DEPENDENCY.is_file()
    text = GAP5_GAP4_DEPENDENCY.read_text(encoding="utf-8")
    assert "test_gap2a1_primary_evidence_enforcement_drift_guard_contract_v0.py" in text
    assert "GAP2A1_PRIMARY_EVIDENCE_ENFORCED=false" in text


def test_gap2a1_drift_guard_owner_crosslinks_hardening_source_contract_v0() -> None:
    assert HARDENING_OWNER.is_file()
    text = HARDENING_OWNER.read_text(encoding="utf-8")
    assert "test_gap2a1_primary_evidence_enforcement_drift_guard_contract_v0.py" in text
    lines = {line.strip() for line in text.splitlines()}
    assert ("GAP2A1_PRIMARY_EVIDENCE_ENFORCED" + _MARKER_TRUE) not in lines
    assert ("GAP2A1_ENFORCEMENT_DEFAULT_ON" + _MARKER_TRUE) not in lines


def test_gap2a1_drift_guard_owner_crosslinks_gap4_gap2a1_dependency_v0() -> None:
    dependency = (
        ROOT / "tests" / "ops" / "test_gap4_gap2a1_primary_evidence_dependency_contract_v0.py"
    )
    assert dependency.is_file()
    text = dependency.read_text(encoding="utf-8")
    assert "test_gap2a1_primary_evidence_enforcement_drift_guard_contract_v0.py" in text
    assert "GAP2A1_PRIMARY_EVIDENCE_ENFORCED=false" in text
