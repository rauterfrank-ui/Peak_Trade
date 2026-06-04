from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
DOC = ROOT / "docs" / "ops" / "planning" / "SECTION5_PREFLIGHT_GAP_OWNER_MAP_CONTRACT_V0.md"


def test_section5_owner_map_contract_exists_and_is_non_authorizing():
    text = DOC.read_text(encoding="utf-8")

    required = [
        "SECTION5_OWNER_MAP_CONTRACT_V0=true",
        "SECTION5_GAP_CLOSURE_EXECUTED=false",
        "ALL_GAPS_CLOSED=false",
        "PATH_B_LIFT_DISCUSSION_READY=false",
        "PREFLIGHT_REMAINS_BLOCKED=true",
        "READY_FOR_OPERATOR_ARMING=false",
        "RUNTIME_APPROVED=false",
        "PREFLIGHT_LIFT_EXECUTED=false",
    ]

    for marker in required:
        assert marker in text


def test_section5_owner_map_contract_covers_all_gap_targets():
    text = DOC.read_text(encoding="utf-8")

    required_gaps = [
        "Execute entrypoint",
        "Canonical job set",
        "Execute command contracts",
        "Output/evidence paths",
        "Risk boundaries",
        "Primary-evidence enforcement",
        "§2a.1 prerequisites",
        "Stop/rehearsal and dry-run proof",
    ]

    for gap in required_gaps:
        assert gap in text


def test_section5_owner_map_contract_reuse_first_and_no_parallel_docs():
    text = DOC.read_text(encoding="utf-8")

    required = [
        "reuse-first",
        "Canonical owner to reuse first",
        "Prefer extending existing canonical owners over adding parallel documents",
        "Do not lift preflight",
        "Do not mark `READY_FOR_OPERATOR_ARMING=true`",
        "Do not approve runtime",
    ]

    for marker in required:
        assert marker in text


def _gap2a1_section(text: str) -> str:
    return text.split("## §2a.1 Primary Evidence Enforcement Contract v0", 1)[1].split(
        "## Gap 1 Execute Entrypoint Contract v0", 1
    )[0]


def test_section5_gap2a1_pe3_run_type_applicability_contract_v0() -> None:
    text = DOC.read_text(encoding="utf-8")
    section = _gap2a1_section(text)
    for token in (
        "PE3_RUN_TYPE_APPLICABILITY_CONTRACT_V0=true",
        "PE3_RUN_TYPE_MATRIX_DOCS_ANCHOR_V0=true",
        "SLICE_PE2_COMPLETE=true",
        "SLICE_PE3_DOCS_TESTS_ONLY=true",
        "PRIMARY_EVIDENCE_REQUIRED_FOR_RUN_COMPLETION=true",
        "RUN_COMPLETION_INVALID_WITHOUT_DURABLE_PRIMARY_EVIDENCE=true",
    ):
        assert token in section
    assert "PE2_RUN_TYPE_GUARD_MATRIX" in section
    assert "test_run_primary_evidence_retention_hard_gate_v0.py" in section
    assert "PAPER_SHADOW_247_PREFLIGHT_CONTRACT_V0.md" in section
    for run_type in ("Paper", "Shadow", "Testnet", "Live/Canary", "Scheduler", "Supervisor"):
        assert run_type in section
    assert "/tmp`-only insufficient" in section or "/tmp`-only is insufficient" in section
    assert "MANIFEST.sha256" in section
    assert "READY_FOR_OPERATOR_ARMING=false" in section
    assert "GAP2A1_PRIMARY_EVIDENCE_ENFORCED=false" in section
    collapsed = section.replace("**", "")
    assert "does not enable default enforcement" in collapsed.lower()


def _gap4_section(text: str) -> str:
    return text.split("## Gap 4 Output/Evidence Paths Contract v0", 1)[1].split(
        "## Gap 6 Dry-Run Proof Criteria Contract v0", 1
    )[0]


def test_section5_gap4_pe5_dependency_guard_v0() -> None:
    text = DOC.read_text(encoding="utf-8")
    gap4 = _gap4_section(text)
    gap2a1 = _gap2a1_section(text)
    for token in (
        "PE5_GAP4_GAP2A1_DEPENDENCY_GUARD_V0=true",
        "GAP4_OUTPUT_EVIDENCE_DEPENDS_ON_GAP2A1_PRIMARY_EVIDENCE_V0=true",
        "GAP4_COMPLETION_INVALID_WITHOUT_DURABLE_PRIMARY_EVIDENCE=true",
        "GAP4_COMPLETION_INVALID_WITHOUT_MANIFEST_VERIFY=true",
        "SLICE_PE5_TESTS_ONLY=true",
    ):
        assert token in gap4
    for token in (
        "PE5_GAP4_GAP2A1_DEPENDENCY_GUARD_V0=true",
        "GAP4_OUTPUT_EVIDENCE_DEPENDS_ON_GAP2A1_PRIMARY_EVIDENCE_V0=true",
    ):
        assert token in gap2a1
    assert "test_gap4_gap2a1_primary_evidence_dependency_contract_v0.py" in gap4
    assert "GAP4_OUTPUT_EVIDENCE_PATHS_VERIFIED=false" in gap4
    assert "READY_FOR_OPERATOR_ARMING=false" in gap4


def test_section5_eer1_readiness_review_index_crosslink_v0() -> None:
    text = DOC.read_text(encoding="utf-8")
    ci_audit = (ROOT / "docs" / "ops" / "CI_AUDIT_KNOWN_ISSUES.md").read_text(encoding="utf-8")
    gap2a1 = _gap2a1_section(text)
    for token in (
        "EVIDENCE_DURABLE_ENFORCEMENT_READINESS_REVIEW_RC_V0_STARTED=true",
        "EER1_READINESS_REVIEW_INDEX_COMPLETE=true",
        "PRIMARY_EVIDENCE_RUN_COMPLETION_CONTRACT_RC_V0_STATUS=CORE_COMPLETE_AFTER_PE6",
        "CYBERSECURITY_DEFENSIVE_VISIBILITY_CV3_PLUS_RC_V0_STATUS=CORE_COMPLETE_AFTER_CV3C",
        "GAP2A1_PRIMARY_EVIDENCE_ENFORCED=false",
        "ENFORCEMENT_ACTIVATED=false",
        "PREFLIGHT_REMAINS_BLOCKED=true",
        "READY_FOR_OPERATOR_ARMING=false",
    ):
        assert token in gap2a1
        assert token in ci_audit
    assert "Evidence Durable Enforcement Readiness Review RC v0" in ci_audit
    assert "Evidence Durable Enforcement Readiness Review index (EER1 guard)" in gap2a1
    assert "planning/docs/tests readiness review only" in gap2a1.lower()
    assert "PAPER_SHADOW_247_PREFLIGHT_CONTRACT_V0.md" in gap2a1
    assert "MANIFEST" in gap2a1 or "manifest" in gap2a1.lower()
    gap2a1_lines = {line.strip() for line in gap2a1.splitlines()}
    assert "GAP2A1_PRIMARY_EVIDENCE_ENFORCED=true" not in gap2a1_lines
    assert "READY_FOR_OPERATOR_ARMING=true" not in gap2a1_lines


PREFLIGHT_SYNTHESIS_DOCS_BLOCK_REFLECTION_HEADER = "## Preflight Synthesis Docs Block Reflection v0"
FINAL_MACHINE_LINES_HEADER = "## Final Machine Lines"


def _preflight_synthesis_reflection_section(text: str) -> str:
    return text.split(PREFLIGHT_SYNTHESIS_DOCS_BLOCK_REFLECTION_HEADER, 1)[1].split(
        FINAL_MACHINE_LINES_HEADER, 1
    )[0]


def _final_machine_lines(text: str) -> str:
    return text.split(FINAL_MACHINE_LINES_HEADER, 1)[1]


def test_section5_preflight_synthesis_docs_block_reflection_non_authorizing_v0() -> None:
    text = DOC.read_text(encoding="utf-8")
    synthesis = _preflight_synthesis_reflection_section(text)
    block = _final_machine_lines(text)

    assert "PREFLIGHT_SYNTHESIS_GOVERNED_REFLECTION_V0=true" in synthesis
    assert "PREFLIGHT_SYNTHESIS_DOCS_BLOCKED=true" in synthesis
    assert "ACCEPTED_MODE=SECTION5_FINALS_CONSOLIDATED_PREFLIGHT_REMAINS_BLOCKED" in synthesis
    assert "EXTERNAL_GAP2A1_TIER0_ACCEPTANCE_POINTER=" in synthesis
    assert "gap2a1_tier0_closure_operator_acceptance_external_only_v0_20260603T164021Z" in synthesis
    assert "INPUT_GAP4_CLOSEOUT_POINTER=" in synthesis
    assert (
        "pr3968_gap4_output_evidence_paths_final_line_reflection_post_merge_closeout_v0"
        in synthesis
    )
    assert (
        "OPERATOR_GO=GO_PREFLIGHT_SYNTHESIS_DOCS_BLOCK_REPO_REFLECTION_DOCS_TESTS_V0" in synthesis
    )
    assert "NO_RUNTIME_AUTHORITY=true" in synthesis
    assert "does not set `PREFLIGHT_REMAINS_BLOCKED=false`" in synthesis
    assert "does not set `ALL_GAPS_CLOSED=true`" in synthesis
    assert "does not set `READY_FOR_OPERATOR_ARMING=true`" in synthesis
    assert "does not set `GAP2A1_PRIMARY_EVIDENCE_ENFORCED=true`" in synthesis
    assert "Evidence synthesis is not runtime authorization" in synthesis

    assert "GAP4_OUTPUT_EVIDENCE_PATHS_VERIFIED=true" in synthesis
    assert "GAP5_STOP_PROOF_ACCEPTED=true" in synthesis
    assert "GAP7_RISK_BOUNDARY_VERIFIED=true" in synthesis
    assert "GAP2A1_TIER0_OPERATOR_ACCEPTED=true" in synthesis
    assert "GAP2A1_PRIMARY_EVIDENCE_ENFORCED=false" in synthesis
    assert "GAP2A1_TIER1_ENFORCEMENT_LIFTED=false" in synthesis
    assert "FULL_SCOPE_GAP4_VERIFIED=false" in synthesis
    assert "PREFLIGHT_REMAINS_BLOCKED=true" in synthesis
    assert "ALL_GAPS_CLOSED=false" in synthesis
    assert "READY_FOR_OPERATOR_ARMING=false" in synthesis

    assert "PREFLIGHT_SYNTHESIS_DOCS_BLOCKED=true" in block
    assert "GAP2A1_TIER0_OPERATOR_ACCEPTED=true" in block
    assert "GAP2A1_TIER1_ENFORCEMENT_LIFTED=false" in block
    assert "GAP2A1_PRIMARY_EVIDENCE_ENFORCED=false" in block
    assert "GAP4_OUTPUT_EVIDENCE_PATHS_VERIFIED=true" in block
    assert "GAP5_STOP_PROOF_ACCEPTED=true" in block
    assert "GAP7_RISK_BOUNDARY_VERIFIED=true" in block
    assert "PREFLIGHT_REMAINS_BLOCKED=true" in block
    assert "ALL_GAPS_CLOSED=false" in block
    assert "READY_FOR_OPERATOR_ARMING=false" in block
    assert "PREFLIGHT_LIFT_EXECUTED=false" in block
    assert "ACTUAL_PREFLIGHT_LIFT_EXECUTED=false" in block

    synthesis_lines = {line.strip() for line in synthesis.splitlines()}
    block_lines = {line.strip() for line in block.splitlines()}
    assert "PREFLIGHT_SYNTHESIS_DOCS_BLOCKED=true" in synthesis_lines
    assert "PREFLIGHT_SYNTHESIS_DOCS_BLOCKED=true" in block_lines
    assert "GAP2A1_TIER0_OPERATOR_ACCEPTED=true" in synthesis_lines
    assert "GAP2A1_TIER0_OPERATOR_ACCEPTED=true" in block_lines
    assert "FULL_SCOPE_GAP4_VERIFIED=true" not in block_lines
    assert "GAP2A1_PRIMARY_EVIDENCE_ENFORCED=true" not in block_lines
    assert "GAP2A1_TIER1_ENFORCEMENT_LIFTED=true" not in block_lines
    assert "PREFLIGHT_REMAINS_BLOCKED=false" not in block_lines
    assert "ALL_GAPS_CLOSED=true" not in block_lines
    assert "READY_FOR_OPERATOR_ARMING=true" not in block_lines


PE11_BOUNDED_FUTURES_REACHABILITY_REFLECTION_HEADER = (
    "## PE-11 Governed Bounded Futures Reachability Reflection v0"
)


def _pe11_reflection_section(text: str) -> str:
    return text.split(PE11_BOUNDED_FUTURES_REACHABILITY_REFLECTION_HEADER, 1)[1].split(
        "## Preflight Synthesis Docs Block Reflection v0", 1
    )[0]


def test_section5_pe11_bounded_futures_reachability_reflection_non_authorizing_v0() -> None:
    text = DOC.read_text(encoding="utf-8")
    pe11 = _pe11_reflection_section(text)
    block = _final_machine_lines(text)

    for token in (
        "PE11_BOUNDED_FUTURES_REACHABILITY_GOVERNED_REFLECTION_V0=true",
        "ZERO_ORDER_PUBLIC_FUTURES_REACHABILITY_PROVEN=true",
        "CREDENTIAL_PRESENCE_PRESENT_REFLECTED=true",
        "PRIVATE_READONLY_WIRE_REACHABILITY_PROVEN=true",
        "REACHABILITY_PROVEN_NOT_ORDER_AUTHORIZED=true",
        "ARCHIVE_HARNESS_SCRIPT_EXECUTE_AUTHORIZED_NOW=false",
        "FUTURES_EXECUTE_AUTHORIZED=false",
        "FUTURES_PRIVATE_API_AUTHORIZED=false",
        "FUTURES_VALIDATE_ONLY_AUTHORIZED=false",
        "FUTURES_SESSION_AUTHORIZED_NOW=false",
        "NEXT_EXECUTE_ALLOWED=false",
        "PREFLIGHT_REMAINS_BLOCKED=true",
        "ALL_GAPS_CLOSED=false",
        "READY_FOR_OPERATOR_ARMING=false",
    ):
        assert token in pe11

    assert "bounded_futures_private_readonly_contract_v0.py" in text
    assert "kraken_futures_demo_credential_presence_contract_v0.py" in text
    assert "private_readonly_final_retry_Frank_Rauter_20260604T183718Z" in pe11
    assert "futures_network_reachability_post_run_evidence_review_v0_20260604T154641Z" in pe11
    assert "Reachability proven ≠ authorization" in pe11 or "Reachability proven" in pe11
    assert "does not set `PREFLIGHT_REMAINS_BLOCKED=false`" in pe11
    assert "does not set `ALL_GAPS_CLOSED=true`" in pe11
    assert "does not set `FUTURES_EXECUTE_AUTHORIZED=true`" in pe11
    assert "Evidence reflection is not runtime authorization" in pe11

    for token in (
        "PE11_BOUNDED_FUTURES_REACHABILITY_GOVERNED_REFLECTION_V0=true",
        "ZERO_ORDER_PUBLIC_FUTURES_REACHABILITY_PROVEN=true",
        "PRIVATE_READONLY_WIRE_REACHABILITY_PROVEN=true",
        "REACHABILITY_PROVEN_NOT_ORDER_AUTHORIZED=true",
        "FUTURES_EXECUTE_AUTHORIZED=false",
        "ARCHIVE_HARNESS_SCRIPT_EXECUTE_AUTHORIZED_NOW=false",
    ):
        assert token in block

    pe11_lines = {line.strip() for line in pe11.splitlines()}
    block_lines = {line.strip() for line in block.splitlines()}
    assert "FUTURES_EXECUTE_AUTHORIZED=true" not in pe11_lines
    assert "ARCHIVE_HARNESS_SCRIPT_EXECUTE_AUTHORIZED_NOW=true" not in block_lines
    assert "ALL_GAPS_CLOSED=true" not in block_lines
    assert "READY_FOR_OPERATOR_ARMING=true" not in block_lines


GAP6_GAP1_FINAL_LINE_REFLECTION_HEADER = (
    "## Gap 6 Governed Dry-Run RC0 Observed Final-Line Reflection v0"
)


def _gap6_gap1_final_line_reflection_section(text: str) -> str:
    return text.split(GAP6_GAP1_FINAL_LINE_REFLECTION_HEADER, 1)[1].split(
        "## Preflight Synthesis Docs Block Reflection v0", 1
    )[0]


def test_section5_gap6_gap1_rc0_observed_final_line_reflection_non_authorizing_v0() -> None:
    text = DOC.read_text(encoding="utf-8")
    section = _gap6_gap1_final_line_reflection_section(text)
    block = _final_machine_lines(text)

    for token in (
        "GAP6_DRY_RUN_RC0_OBSERVED_FINAL_LINE_GOVERNED_REFLECTION_V0=true",
        "GAP1_EXECUTE_ENTRYPOINT_RC0_OBSERVED_FINAL_LINE_GOVERNED_REFLECTION_V0=true",
        "OBSERVED_NOT_VERIFIED_SEMANTIC_PRESERVED=true",
        "PREFLIGHT_REMAINS_BLOCKED=true",
        "ALL_GAPS_CLOSED=false",
    ):
        assert token in section

    assert "GAP6_DRY_RUN_RC0_OBSERVED=true" in block
    assert "GAP1_EXECUTE_ENTRYPOINT_RC0_OBSERVED=true" in block
    assert "GAP6_DRY_RUN_PROOF_VERIFIED=false" in block
    assert "GAP1_EXECUTE_ENTRYPOINT_VERIFIED=false" in block
    block_lines = {line.strip() for line in block.splitlines()}
    assert "GAP6_DRY_RUN_PROOF_VERIFIED=true" not in block_lines
    assert "GAP1_EXECUTE_ENTRYPOINT_VERIFIED=true" not in block_lines
    assert "READY_FOR_OPERATOR_ARMING=true" not in block_lines


GAP2_GAP3_ACCEPTED_FINAL_LINE_REFLECTION_HEADER = (
    "## Gap 2 Governed Canonical Job Set Accepted Scoped-Criteria Final-Line Reflection v0"
)


def _gap2_gap3_accepted_final_line_reflection_section(text: str) -> str:
    return text.split(GAP2_GAP3_ACCEPTED_FINAL_LINE_REFLECTION_HEADER, 1)[1].split(
        "## Gap 5 Governed Stop Proof Acceptance Reflection v0", 1
    )[0]


def test_section5_gap2_gap3_accepted_scoped_criteria_final_line_reflection_non_authorizing_v0() -> (
    None
):
    text = DOC.read_text(encoding="utf-8")
    section = _gap2_gap3_accepted_final_line_reflection_section(text)
    block = _final_machine_lines(text)

    for token in (
        "GAP2_ACCEPTED_SCOPED_CRITERIA_FINAL_LINE_GOVERNED_REFLECTION_V0=true",
        "GAP3_ACCEPTED_SCOPED_CRITERIA_FINAL_LINE_GOVERNED_REFLECTION_V0=true",
        "ACCEPTED_NOT_VERIFIED_SEMANTIC_PRESERVED=true",
        "PREFLIGHT_REMAINS_BLOCKED=true",
        "ALL_GAPS_CLOSED=false",
    ):
        assert token in section

    assert "GAP2_ACCEPTED_SCOPED_CRITERIA=true" in block
    assert "GAP3_ACCEPTED_SCOPED_CRITERIA=true" in block
    assert "GAP2_CANONICAL_JOB_SET_VERIFIED=false" in block
    assert "GAP3_EXECUTE_COMMAND_VERIFIED=false" in block
    block_lines = {line.strip() for line in block.splitlines()}
    assert "GAP2_CANONICAL_JOB_SET_VERIFIED=true" not in block_lines
    assert "GAP3_EXECUTE_COMMAND_VERIFIED=true" not in block_lines
    assert "READY_FOR_OPERATOR_ARMING=true" not in block_lines
