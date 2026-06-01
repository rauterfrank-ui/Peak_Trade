"""Static contract for Gap-4↔Gap2a.1 primary evidence dependency v0.

Reads repo markdown/source only. Never executes scheduler/runtime/retention helpers,
never copies/moves/archives evidence, never reads external archive or tier-plan paths as
pass/fail SSOT, and never treats Gap-4 durable path criteria, verified paths, archived
evidence, manifest verification, or closeout presence as repo ``GAP2A1_PRIMARY_EVIDENCE_ENFORCED``.
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
GAP2A1_DRIFT_GUARD = (
    ROOT / "tests" / "ops" / "test_gap2a1_primary_evidence_enforcement_drift_guard_contract_v0.py"
)
HARDENING_OWNER = ROOT / "tests" / "ops" / "test_scheduler_dry_run_hardening_source_contract_v0.py"
FINAL_MACHINE_LINES_HEADER = "## Final Machine Lines"
GAP4_SECTION_HEADER = "## Gap 4 Output/Evidence Paths Contract v0"
GAP4_COMPLETENESS_REFLECTION_HEADER = "## Gap 4 Full-Scope Evidence Completeness Reflection v0"
GAP4_VERIFIED_REFLECTION_HEADER = "## Gap 4 Full-Scope Gap4 Verified Reflection v0"
GAP2A1_SECTION_HEADER = "## §2a.1 Primary Evidence Enforcement Contract v0"
_MARKER_TRUE = "=true"

GAP4_DURABLE_PATH_CRITERIA_PLANNED = True
GAP4_OUTPUT_EVIDENCE_PATHS_VERIFIED = False
GAP2A1_ENFORCEMENT_OPT_IN_ONLY = True
GAP2A1_PRIMARY_EVIDENCE_ENFORCED = False
GAP4_VERIFIED_NOT_IMPLIES_GAP2A1_ENFORCED = True
DURABLE_EVIDENCE_NOT_ENFORCEMENT_OPT_IN = True
MANIFEST_VERIFY_NOT_ENFORCEMENT = True
CLOSEOUT_PRESENCE_NOT_ENFORCEMENT = True
TMP_CANNOT_SATISFY_DURABLE_EVIDENCE_CHAIN = True
EXTERNAL_TIER_PLAN_NOT_REPO_SSOT = True
EVIDENCE_EQUALS_APPROVAL = False
CRITERIA_COMPLETE_EQUALS_GAP_CLOSED = False
FUTURE_GAP2A1_ENFORCEMENT_REQUIRES_EXPLICIT_OPT_IN_GO = True

DURABLE_EVIDENCE_SURFACES = (
    "primary_evidence_retention_v0.py",
    "durable_closeout_copy_verify_v0.py",
)

DEPENDENCY_REQUIRED_FINAL_LINES = (
    "PREFLIGHT_REMAINS_BLOCKED=true",
    "READY_FOR_OPERATOR_ARMING=false",
    "PATH_B_LIFT_DISCUSSION_READY=false",
    "ALL_GAPS_CLOSED=false",
    "GAP4_OUTPUT_EVIDENCE_PATHS_VERIFIED=false",
    "GAP4_OUTPUT_EVIDENCE_DEFAULT_ON=false",
    "GAP4_OUTPUT_EVIDENCE_OPT_IN_ONLY=true",
    "GAP2A1_PRIMARY_EVIDENCE_ENFORCED=false",
    "GAP2A1_ENFORCEMENT_DEFAULT_ON=false",
    "GAP5_STOP_REHEARSAL_EXECUTED=false",
    "GAP5_STOP_PROOF_ACCEPTED=false",
    "GAP6_DRY_RUN_PROOF_ACCEPTED=false",
)

DEPENDENCY_FORBIDDEN_REPO_TOKENS = (
    "GAP4_OUTPUT_EVIDENCE_PATHS_VERIFIED=true",
    "GAP4_OUTPUT_EVIDENCE_DEFAULT_ON=true",
    "GAP2A1_PRIMARY_EVIDENCE_ENFORCED=true",
    "GAP2A1_ENFORCEMENT_DEFAULT_ON=true",
    "GAP4_VERIFIED_IMPLIES_GAP2A1_ENFORCED=true",
    "DURABLE_EVIDENCE_IMPLIES_ENFORCEMENT=true",
    "MANIFEST_VERIFY_RC0_IMPLIES_GAP2A1_ENFORCED=true",
    "CLOSEOUT_EXISTS_IMPLIES_GAP2A1_ENFORCED=true",
    "ARCHIVED_EVIDENCE_IMPLIES_ENFORCEMENT=true",
    "GAP2A1_TIER_COMPLETE=true",
    "GAP2A1_TIER_5_SATISFIED=true",
    "EXTERNAL_TIER_PLAN_COMPLETE=true",
    "GAP5_STOP_PROOF_ACCEPTED=true",
    "GAP6_DRY_RUN_PROOF_ACCEPTED=true",
    "WORKSHEET_COMPLETE=true",
    "PATH_B_LIFT_DISCUSSION_READY=true",
    "ALL_GAPS_CLOSED=true",
    "READY_FOR_OPERATOR_ARMING=true",
    "PREFLIGHT_REMAINS_BLOCKED=false",
    "SHADOW_24_7_AUTHORIZED=true",
)

CONFLATION_SAMPLE_LINES_MUST_NOT_LIFT_ENFORCEMENT = (
    "DURABLE_EVIDENCE_PRESENT=true",
    "DURABLE_EVIDENCE_PATH_VERIFIED=true",
    "ARCHIVED_EVIDENCE_FOUND=true",
    "MANIFEST_VERIFY_RC=0",
    "CLOSEOUT_BUNDLE_PRESENT=true",
    "GAP4_OUTPUT_EVIDENCE_PATHS_VERIFIED=true",
    "EXTERNAL_TIER_PLAN_TIER_5_SATISFIED=true",
)

CONFLATION_SAMPLE_ALLOWED_IN_COMPLETENESS_REFLECTION_ONLY = (
    "GAP4_OUTPUT_EVIDENCE_PATHS_VERIFIED=true",
)


def _final_machine_lines(text: str) -> str:
    return text.split(FINAL_MACHINE_LINES_HEADER, 1)[1]


def _gap4_section(text: str) -> str:
    return text.split(GAP4_SECTION_HEADER, 1)[1].split(
        "## Gap 6 Dry-Run Proof Criteria Contract v0", 1
    )[0]


def _gap2a1_section(text: str) -> str:
    return text.split(GAP2A1_SECTION_HEADER, 1)[1].split(
        "## Gap 1 Execute Entrypoint Contract v0", 1
    )[0]


def _gap4_completeness_reflection_section(text: str) -> str:
    return text.split(GAP4_COMPLETENESS_REFLECTION_HEADER, 1)[1].split(
        GAP4_VERIFIED_REFLECTION_HEADER, 1
    )[0]


def _gap4_verified_reflection_section(text: str) -> str:
    return text.split(GAP4_VERIFIED_REFLECTION_HEADER, 1)[1].split(
        "## Gap 7 Governed Risk Boundary Acceptance Reflection v0", 1
    )[0]


def _section5_text() -> str:
    return SECTION5_DOC.read_text(encoding="utf-8")


def _module_preamble() -> str:
    return Path(__file__).read_text(encoding="utf-8").split("\ndef test_", 1)[0]


def test_gap4_gap2a1_dependency_module_constants_v0() -> None:
    assert GAP4_DURABLE_PATH_CRITERIA_PLANNED is True
    assert GAP4_OUTPUT_EVIDENCE_PATHS_VERIFIED is False
    assert GAP2A1_ENFORCEMENT_OPT_IN_ONLY is True
    assert GAP2A1_PRIMARY_EVIDENCE_ENFORCED is False
    assert GAP4_VERIFIED_NOT_IMPLIES_GAP2A1_ENFORCED is True
    assert DURABLE_EVIDENCE_NOT_ENFORCEMENT_OPT_IN is True
    assert MANIFEST_VERIFY_NOT_ENFORCEMENT is True
    assert CLOSEOUT_PRESENCE_NOT_ENFORCEMENT is True
    assert EXTERNAL_TIER_PLAN_NOT_REPO_SSOT is True


def test_gap4_gap2a1_dependency_final_machine_lines_remain_blocked_v0() -> None:
    block = _final_machine_lines(_section5_text())
    for marker in DEPENDENCY_REQUIRED_FINAL_LINES:
        assert marker in block


def test_gap4_gap2a1_dependency_forbids_lift_and_conflation_tokens_v0() -> None:
    block = _final_machine_lines(_section5_text())
    lines = {line.strip() for line in block.splitlines()}
    for token in DEPENDENCY_FORBIDDEN_REPO_TOKENS:
        assert token not in lines


def test_gap4_gap2a1_dependency_gap4_section_criteria_not_verified_v0() -> None:
    section = _gap4_section(_section5_text())
    assert "GAP4_OUTPUT_EVIDENCE_PATHS_CONTRACT_V0=true" in section
    assert "GAP4_OUTPUT_EVIDENCE_PATHS_VERIFIED=false" in section
    assert "GAP4_OUTPUT_EVIDENCE_DEFAULT_ON=false" in section
    assert "GAP4_OUTPUT_EVIDENCE_OPT_IN_ONLY=true" in section
    assert "contract-only, not verified" in section
    assert "not enforcement-on" in section
    lines = {line.strip() for line in section.splitlines()}
    assert "GAP4_OUTPUT_EVIDENCE_PATHS_VERIFIED=true" not in lines


def test_gap4_gap2a1_dependency_gap2a1_section_opt_in_not_enforced_v0() -> None:
    section = _gap2a1_section(_section5_text())
    assert "GAP2A1_PRIMARY_EVIDENCE_ENFORCED=false" in section
    assert "GAP2A1_ENFORCEMENT_DEFAULT_ON=false" in section
    assert "GAP2A1_ENFORCEMENT_OPT_IN_ONLY=true" in section
    assert "opt-in only" in section
    lines = {line.strip() for line in section.splitlines()}
    assert "GAP2A1_PRIMARY_EVIDENCE_ENFORCED=true" not in lines


def test_gap4_gap2a1_dependency_gap4_verified_not_implies_gap2a1_enforced_v0() -> None:
    block = _final_machine_lines(_section5_text())
    gap4 = _gap4_section(_section5_text())
    gap2a1 = _gap2a1_section(_section5_text())
    assert GAP4_VERIFIED_NOT_IMPLIES_GAP2A1_ENFORCED is True
    assert "GAP4_OUTPUT_EVIDENCE_PATHS_VERIFIED=false" in gap4
    assert "GAP2A1_PRIMARY_EVIDENCE_ENFORCED=false" in gap2a1
    assert "GAP4_OUTPUT_EVIDENCE_PATHS_VERIFIED=false" in block
    assert "GAP2A1_PRIMARY_EVIDENCE_ENFORCED=false" in block
    lines = {line.strip() for line in block.splitlines()}
    assert "GAP4_OUTPUT_EVIDENCE_PATHS_VERIFIED=true" not in lines
    assert "GAP2A1_PRIMARY_EVIDENCE_ENFORCED=true" not in lines


def test_gap4_gap2a1_dependency_durable_evidence_not_enforcement_v0() -> None:
    gap4 = _gap4_section(_section5_text())
    for surface in DURABLE_EVIDENCE_SURFACES:
        assert surface in gap4
    assert DURABLE_EVIDENCE_NOT_ENFORCEMENT_OPT_IN is True
    assert GAP2A1_PRIMARY_EVIDENCE_ENFORCED is False


def test_gap4_gap2a1_dependency_sample_conflation_lines_not_repo_ssot_lifts_v0() -> None:
    text = _section5_text()
    block_lines = {line.strip() for line in _final_machine_lines(text).splitlines()}
    criteria_lines = {line.strip() for line in _gap4_section(text).splitlines()}
    gap2a1_lines = {line.strip() for line in _gap2a1_section(text).splitlines()}
    completeness_lines = {
        line.strip() for line in _gap4_completeness_reflection_section(text).splitlines()
    }
    verified_lines = {line.strip() for line in _gap4_verified_reflection_section(text).splitlines()}
    repo_ssot_lines = block_lines | criteria_lines | gap2a1_lines
    for sample in CONFLATION_SAMPLE_LINES_MUST_NOT_LIFT_ENFORCEMENT:
        assert sample not in block_lines
        if sample in CONFLATION_SAMPLE_ALLOWED_IN_COMPLETENESS_REFLECTION_ONLY:
            assert sample in completeness_lines or sample in verified_lines
            assert sample not in repo_ssot_lines
            continue
        assert sample not in repo_ssot_lines


def test_gap4_gap2a1_dependency_tmp_not_canonical_durable_chain_v0() -> None:
    gap4 = _gap4_section(_section5_text())
    hardening = HARDENING_OWNER.read_text(encoding="utf-8")
    assert TMP_CANNOT_SATISFY_DURABLE_EVIDENCE_CHAIN is True
    assert "archived outside `/tmp`" in gap4
    assert "from scripts.ops.primary_evidence_retention_v0 import is_under_tmp" in hardening


def test_gap4_gap2a1_dependency_manifest_closeout_not_enforcement_v0() -> None:
    gap4 = _gap4_section(_section5_text())
    assert "checksummed, verified" in gap4
    assert MANIFEST_VERIFY_NOT_ENFORCEMENT is True
    assert CLOSEOUT_PRESENCE_NOT_ENFORCEMENT is True
    assert "durable_closeout_copy_verify_v0.py" in gap4


def test_gap4_gap2a1_dependency_tier_plan_not_repo_ssot_v0() -> None:
    preamble = _module_preamble()
    assert "Peak_Trade_runtime_evidence_archive" not in preamble
    assert "external_gap2a1_primary_evidence_enforcement_tier_plan" not in preamble
    section = _gap2a1_section(_section5_text())
    assert "opt-in only" in section
    assert "intentionally non-authorizing" in section


def test_gap4_gap2a1_dependency_gap5_gap6_orthogonal_v0() -> None:
    block = _final_machine_lines(_section5_text())
    assert "GAP5_STOP_REHEARSAL_EXECUTED=false" in block
    assert "GAP5_STOP_PROOF_ACCEPTED=false" in block
    assert "GAP6_DRY_RUN_PROOF_ACCEPTED=false" in block
    assert "GAP6_DRY_RUN_RC0_OBSERVED=false" in block


def test_gap4_gap2a1_dependency_criteria_complete_does_not_close_gaps_v0() -> None:
    text = _section5_text()
    assert "SECTION5_OWNER_MAP_CONTRACT_V0_COMPLETE=true" in text
    assert "ALL_GAPS_CLOSED=false" in text
    assert "GAP4_OUTPUT_EVIDENCE_PATHS_VERIFIED=false" in text
    assert "GAP2A1_PRIMARY_EVIDENCE_ENFORCED=false" in text


def test_gap4_gap2a1_dependency_evidence_not_approval_language_v0() -> None:
    gap4 = _gap4_section(_section5_text())
    preflight = PREFLIGHT_CONTRACT.read_text(encoding="utf-8")
    assert "does not authorize runtime" in gap4
    assert "Evidence ≠ approval" in preflight
    assert EVIDENCE_EQUALS_APPROVAL is False


def test_gap4_gap2a1_dependency_module_is_static_no_subprocess_v0() -> None:
    import ast

    tree = ast.parse(Path(__file__).read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                assert alias.name != "subprocess"
        elif isinstance(node, ast.ImportFrom):
            assert node.module != "subprocess"


def test_gap4_gap2a1_dependency_owner_crosslinks_gap4_drift_guard_v0() -> None:
    assert GAP4_DRIFT_GUARD.is_file()
    text = GAP4_DRIFT_GUARD.read_text(encoding="utf-8")
    assert "test_gap4_gap2a1_primary_evidence_dependency_contract_v0.py" in text
    assert "GAP4_OUTPUT_EVIDENCE_PATHS_VERIFIED=false" in text


def test_gap4_gap2a1_dependency_owner_crosslinks_gap2a1_drift_guard_v0() -> None:
    assert GAP2A1_DRIFT_GUARD.is_file()
    text = GAP2A1_DRIFT_GUARD.read_text(encoding="utf-8")
    assert "test_gap4_gap2a1_primary_evidence_dependency_contract_v0.py" in text
    assert "GAP2A1_PRIMARY_EVIDENCE_ENFORCED=false" in text


def test_gap4_gap2a1_dependency_owner_crosslinks_hardening_source_contract_v0() -> None:
    assert HARDENING_OWNER.is_file()
    text = HARDENING_OWNER.read_text(encoding="utf-8")
    assert "test_gap4_gap2a1_primary_evidence_dependency_contract_v0.py" in text
    lines = {line.strip() for line in text.splitlines()}
    assert ("GAP4_OUTPUT_EVIDENCE_PATHS_VERIFIED" + _MARKER_TRUE) not in lines
    assert ("GAP2A1_PRIMARY_EVIDENCE_ENFORCED" + _MARKER_TRUE) not in lines
