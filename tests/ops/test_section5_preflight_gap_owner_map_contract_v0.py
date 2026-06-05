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
PREFLIGHT_LIFT_CLASS4_REFLECTION_HEADER = (
    "## Preflight Lift Explicit Operator Authorization CLASS_4 Reflection v0"
)
ALL_GAPS_CLOSED_FINAL_REFLECTION_HEADER = (
    "## Section-5 ALL_GAPS_CLOSED Final Reflection After Preflight Lift v0"
)
OPERATOR_ARMING_CLASS4_REFLECTION_HEADER = (
    "## Operator Arming Explicit Authorization CLASS_4 Reflection v0"
)
NEXT_EXECUTE_CLASS4_REFLECTION_HEADER = (
    "## NEXT_EXECUTE Explicit Authorization CLASS_4 Reflection v0"
)
BOUNDED_EXECUTE_RUN_CLASS4_REFLECTION_HEADER = (
    "## BOUNDED_EXECUTE_RUN Explicit Authorization CLASS_4 Reflection v0"
)
T3_BOUNDED_EXECUTE_RUN_ATTEMPT_CLASS4_REFLECTION_HEADER = (
    "## T3_BOUNDED_EXECUTE_RUN_ATTEMPT Explicit Authorization CLASS_4 Reflection v0"
)
T3_RUN_ATTEMPT_EXECUTE_CLASS4_REFLECTION_HEADER = (
    "## T3_RUN_ATTEMPT_EXECUTE Explicit Authorization CLASS_4 Reflection v0"
)
T3_PLAN_ONLY_CLOSEOUT_CLASS4_REFLECTION_HEADER = (
    "## T3 Plan-only Closeout CLASS_4 Reflection v0"
)
TIER_C_SHADOW_CROSSLINK_HEADER = "## Tier-C + Shadow durable evidence archive crosslink v0"
FINAL_MACHINE_LINES_HEADER = "## Final Machine Lines"


def _preflight_synthesis_reflection_section(text: str) -> str:
    return text.split(PREFLIGHT_SYNTHESIS_DOCS_BLOCK_REFLECTION_HEADER, 1)[1].split(
        PREFLIGHT_LIFT_CLASS4_REFLECTION_HEADER, 1
    )[0]


def _preflight_lift_class4_reflection_section(text: str) -> str:
    return text.split(PREFLIGHT_LIFT_CLASS4_REFLECTION_HEADER, 1)[1].split(
        ALL_GAPS_CLOSED_FINAL_REFLECTION_HEADER, 1
    )[0]


def _all_gaps_closed_final_reflection_section(text: str) -> str:
    return text.split(ALL_GAPS_CLOSED_FINAL_REFLECTION_HEADER, 1)[1].split(
        OPERATOR_ARMING_CLASS4_REFLECTION_HEADER, 1
    )[0]


def _operator_arming_class4_reflection_section(text: str) -> str:
    return text.split(OPERATOR_ARMING_CLASS4_REFLECTION_HEADER, 1)[1].split(
        NEXT_EXECUTE_CLASS4_REFLECTION_HEADER, 1
    )[0]


def _next_execute_class4_reflection_section(text: str) -> str:
    return text.split(NEXT_EXECUTE_CLASS4_REFLECTION_HEADER, 1)[1].split(
        BOUNDED_EXECUTE_RUN_CLASS4_REFLECTION_HEADER, 1
    )[0]


def _bounded_execute_run_class4_reflection_section(text: str) -> str:
    return text.split(BOUNDED_EXECUTE_RUN_CLASS4_REFLECTION_HEADER, 1)[1].split(
        T3_BOUNDED_EXECUTE_RUN_ATTEMPT_CLASS4_REFLECTION_HEADER, 1
    )[0]


def _t3_bounded_execute_run_attempt_class4_reflection_section(text: str) -> str:
    return text.split(T3_BOUNDED_EXECUTE_RUN_ATTEMPT_CLASS4_REFLECTION_HEADER, 1)[1].split(
        T3_RUN_ATTEMPT_EXECUTE_CLASS4_REFLECTION_HEADER, 1
    )[0]


def _t3_run_attempt_execute_class4_reflection_section(text: str) -> str:
    return text.split(T3_RUN_ATTEMPT_EXECUTE_CLASS4_REFLECTION_HEADER, 1)[1].split(
        T3_PLAN_ONLY_CLOSEOUT_CLASS4_REFLECTION_HEADER, 1
    )[0]


def _t3_plan_only_closeout_class4_reflection_section(text: str) -> str:
    return text.split(T3_PLAN_ONLY_CLOSEOUT_CLASS4_REFLECTION_HEADER, 1)[1].split(
        TIER_C_SHADOW_CROSSLINK_HEADER, 1
    )[0]


def _final_machine_lines(text: str) -> str:
    return text.split(FINAL_MACHINE_LINES_HEADER, 1)[1]


def test_section5_preflight_synthesis_docs_block_reflection_non_authorizing_v0() -> None:
    text = DOC.read_text(encoding="utf-8")
    synthesis = _preflight_synthesis_reflection_section(text)
    block = _final_machine_lines(text)

    assert "PREFLIGHT_SYNTHESIS_GOVERNED_REFLECTION_V0=true" in synthesis
    assert "PREFLIGHT_SYNTHESIS_VERIFIED_BAR_CHAIN_CONSOLIDATION_V0=true" in synthesis
    assert "PREFLIGHT_SYNTHESIS_DOCS_BLOCKED=true" in synthesis
    assert "ACCEPTED_MODE=SECTION5_FINALS_CONSOLIDATED_PREFLIGHT_REMAINS_BLOCKED" in synthesis
    assert "SECTION5_VERIFIED_BAR_CHAIN_GAPS_1_2_3_6_COMPLETE=true" in synthesis
    assert "GOVERNED_SYNTHESIS_BASIS=GAP1_GAP2_GAP3_GAP6_VERIFIED_BAR_FINALS" in synthesis
    assert "EXTERNAL_GAP2A1_TIER0_ACCEPTANCE_POINTER=" in synthesis
    assert "gap2a1_tier0_closure_operator_acceptance_external_only_v0_20260603T164021Z" in synthesis
    assert "INPUT_RANKING_POINTER=" in synthesis
    assert (
        "repo_wide_next_safe_slice_ranking_after_gap1_verified_bar_closeout_no_run_v0_20260604T214105Z"
        in synthesis
    )
    assert "INPUT_GAP1_CLOSEOUT_POINTER=" in synthesis
    assert "gap1_verified_bar_contract_post_merge_closeout_no_run_v0_20260604T213857Z" in synthesis
    assert "INPUT_GAP2_CLOSEOUT_POINTER=" in synthesis
    assert "gap2_verified_bar_contract_post_merge_closeout_no_run_v0_20260604T205001Z" in synthesis
    assert "INPUT_GAP3_CLOSEOUT_POINTER=" in synthesis
    assert "gap3_verified_bar_contract_post_merge_closeout_no_run_v0_20260604T210936Z" in synthesis
    assert "INPUT_GAP6_CLOSEOUT_POINTER=" in synthesis
    assert "gap6_verified_bar_contract_post_merge_closeout_no_run_v0_20260604T212643Z" in synthesis
    assert "INPUT_GAP4_CLOSEOUT_POINTER=" in synthesis
    assert (
        "pr3968_gap4_output_evidence_paths_final_line_reflection_post_merge_closeout_v0"
        in synthesis
    )
    assert "INPUT_GAP5_CLOSEOUT_POINTER=" in synthesis
    assert (
        "gap5_stop_rehearsal_verified_bar_reflection_post_merge_closeout_no_run_v0_20260604T220658Z"
        in synthesis
    )
    assert (
        "pr3967_gap5_stop_proof_final_line_reflection_post_merge_closeout_v0_20260603T162700Z"
        not in synthesis
    )
    assert (
        "OPERATOR_GO=GO_SECTION5_PREFLIGHT_SYNTHESIS_GAP5_REHEARSAL_VERIFIED_BAR_CLOSEOUT_SYNC_DOCS_TESTS_V0"
        in synthesis
    )
    assert "NO_RUNTIME_AUTHORITY=true" in synthesis
    assert "### Why ALL_GAPS_CLOSED remains false" in synthesis
    assert "does not set `PREFLIGHT_REMAINS_BLOCKED=false`" in synthesis
    assert "does not set `ALL_GAPS_CLOSED=true`" in synthesis
    assert "does not set `READY_FOR_OPERATOR_ARMING=true`" in synthesis
    assert "does not set `NEXT_EXECUTE_ALLOWED=true`" in synthesis
    assert "repo-lift tokens in Final Machine Lines do not authorize runtime execute" in synthesis
    assert "Gap-5 criteria block remains `GAP5_STOP_REHEARSAL_EXECUTED=false`" in synthesis
    assert "Evidence synthesis is not runtime authorization" in synthesis

    assert "GAP1_EXECUTE_ENTRYPOINT_VERIFIED=true" in synthesis
    assert "GAP1_VERIFIED_BAR_TIER=T1_PLUS_T2_ENTRYPOINT_BOUNDARY" in synthesis
    assert "GAP2_CANONICAL_JOB_SET_VERIFIED=true" in synthesis
    assert "GAP3_EXECUTE_COMMAND_VERIFIED=true" in synthesis
    assert "GAP6_DRY_RUN_PROOF_VERIFIED=true" in synthesis
    assert "GAP6_VERIFIED_BAR_TIER=T1_PLUS_T2_DRY_RUN_PROOF" in synthesis
    assert "GAP4_OUTPUT_EVIDENCE_PATHS_VERIFIED=true" in synthesis
    assert "GAP5_STOP_PROOF_ACCEPTED=true" in synthesis
    assert "GAP5_STOP_REHEARSAL_EXECUTED=true" in synthesis
    assert "GAP5_STOP_REHEARSAL_EXECUTED_SOURCE=external_archive_bundle_t2" in synthesis
    assert (
        "GAP5_VERIFIED_BAR_TIER=T0_CHARTER_PRECHECK_PLUS_T1_READONLY_SIGNAL_PLUS_T2_ISOLATED_REHEARSAL"
        in synthesis
    )
    assert "GAP7_RISK_BOUNDARY_VERIFIED=true" in synthesis
    assert "GAP2A1_TIER0_OPERATOR_ACCEPTED=true" in synthesis
    assert "GAP2A1_PRIMARY_EVIDENCE_ENFORCED=true" in synthesis
    assert "GAP2A1_TIER1_ENFORCEMENT_LIFTED_REPO=true" in synthesis
    assert "SECTION5_GAP2A1_REPO_LIFTED=true" in synthesis
    assert "GAP2A1_TIER1_ENFORCEMENT_LIFTED=true" in synthesis
    assert "TIER1_CANONICAL_TAG_BOUNDED_ENFORCE_OBSERVED=true" in synthesis
    assert (
        "PRIMARY_EVIDENCE_ENFORCED_SCOPE=canonical_tag_local_readonly_preflight_once" in synthesis
    )
    assert "FULL_SCOPE_GAP4_VERIFIED=true" in synthesis
    assert "FULL_SCOPE_GAP4_POLICY_SPLIT_RESOLVED=true" in synthesis
    assert "CLASS_4 policy propagation complete" in synthesis
    assert "PREFLIGHT_REMAINS_BLOCKED=true" in synthesis
    assert "ALL_GAPS_CLOSED=false" in synthesis
    assert "NEXT_EXECUTE_ALLOWED=false" in synthesis
    assert "READY_FOR_OPERATOR_ARMING=false" in synthesis
    assert "FUTURES_EXECUTE_AUTHORIZED=false" in synthesis

    assert "PREFLIGHT_SYNTHESIS_DOCS_BLOCKED=true" in block
    assert "GAP1_EXECUTE_ENTRYPOINT_VERIFIED=true" in block
    assert "GAP2_CANONICAL_JOB_SET_VERIFIED=true" in block
    assert "GAP3_EXECUTE_COMMAND_VERIFIED=true" in block
    assert "GAP6_DRY_RUN_PROOF_VERIFIED=true" in block
    assert "GAP2A1_TIER0_OPERATOR_ACCEPTED=true" in block
    assert "GAP2A1_TIER1_ENFORCEMENT_LIFTED=true" in block
    assert "GAP2A1_PRIMARY_EVIDENCE_ENFORCED=true" in block
    assert "GAP2A1_TIER1_ENFORCEMENT_LIFTED_REPO=true" in block
    assert "SECTION5_GAP2A1_REPO_LIFTED=true" in block
    assert "GAP4_OUTPUT_EVIDENCE_PATHS_VERIFIED=true" in block
    assert "FULL_SCOPE_GAP4_VERIFIED=true" in block
    assert "FULL_SCOPE_GAP4_POLICY_SPLIT_RESOLVED=true" in block
    assert "GAP5_STOP_PROOF_ACCEPTED=true" in block
    assert "GAP5_STOP_REHEARSAL_EXECUTED=true" in block
    assert (
        "GAP5_VERIFIED_BAR_TIER=T0_CHARTER_PRECHECK_PLUS_T1_READONLY_SIGNAL_PLUS_T2_ISOLATED_REHEARSAL"
        in block
    )
    assert "GAP7_RISK_BOUNDARY_VERIFIED=true" in block
    assert "PREFLIGHT_REMAINS_BLOCKED=false" in block
    assert "PREFLIGHT_LIFTED_BY_CLASS4_POLICY=true" in block
    assert "ALL_GAPS_CLOSED=true" in block
    assert "NEXT_EXECUTE_ALLOWED=true" in block
    assert "EXECUTE_IS_NOT_RUNTIME_START=true" in block
    assert "READY_FOR_OPERATOR_ARMING=true" in block
    assert "ARMING_NOT_EXECUTE=true" in block
    assert "PREFLIGHT_LIFT_EXECUTED=false" in block
    assert "ACTUAL_PREFLIGHT_LIFT_EXECUTED=false" in block

    synthesis_lines = {line.strip() for line in synthesis.splitlines()}
    block_lines = {line.strip() for line in block.splitlines()}
    assert "PREFLIGHT_SYNTHESIS_DOCS_BLOCKED=true" in synthesis_lines
    assert "PREFLIGHT_SYNTHESIS_DOCS_BLOCKED=true" in block_lines
    assert "SECTION5_VERIFIED_BAR_CHAIN_GAPS_1_2_3_6_COMPLETE=true" in synthesis_lines
    assert "SECTION5_VERIFIED_BAR_CHAIN_GAPS_1_2_3_6_COMPLETE=true" not in block_lines
    assert "GAP1_EXECUTE_ENTRYPOINT_VERIFIED=true" in synthesis_lines
    assert "GAP1_EXECUTE_ENTRYPOINT_VERIFIED=true" in block_lines
    assert "GAP2_CANONICAL_JOB_SET_VERIFIED=true" in synthesis_lines
    assert "GAP2_CANONICAL_JOB_SET_VERIFIED=true" in block_lines
    assert "GAP3_EXECUTE_COMMAND_VERIFIED=true" in synthesis_lines
    assert "GAP3_EXECUTE_COMMAND_VERIFIED=true" in block_lines
    assert "GAP6_DRY_RUN_PROOF_VERIFIED=true" in synthesis_lines
    assert "GAP6_DRY_RUN_PROOF_VERIFIED=true" in block_lines
    assert "GAP2A1_TIER0_OPERATOR_ACCEPTED=true" in synthesis_lines
    assert "GAP2A1_TIER0_OPERATOR_ACCEPTED=true" in block_lines
    assert "FULL_SCOPE_GAP4_VERIFIED=true" in block_lines
    assert "FULL_SCOPE_GAP4_POLICY_SPLIT_RESOLVED=true" in block_lines
    assert "GAP2A1_PRIMARY_EVIDENCE_ENFORCED=true" in block_lines
    assert "GAP2A1_TIER1_ENFORCEMENT_LIFTED_REPO=true" in block_lines
    assert "GAP5_STOP_REHEARSAL_EXECUTED=true" in block_lines
    assert "PREFLIGHT_REMAINS_BLOCKED=false" in block_lines
    assert "PREFLIGHT_LIFTED_BY_CLASS4_POLICY=true" in block_lines
    assert "ALL_GAPS_CLOSED=true" in block_lines
    assert "ALL_GAPS_CLOSED_CLASS4_GOVERNED_REFLECTION_V0=true" in block_lines
    assert "READY_FOR_OPERATOR_ARMING=true" in block_lines
    assert "ARMING_NOT_EXECUTE=true" in block_lines
    assert "NEXT_EXECUTE_ALLOWED=true" in block_lines
    assert "EXECUTE_IS_NOT_RUNTIME_START=true" in block_lines


def test_section5_preflight_lift_class4_reflection_non_authorizing_v0() -> None:
    text = DOC.read_text(encoding="utf-8")
    reflection = _preflight_lift_class4_reflection_section(text)
    synthesis = _preflight_synthesis_reflection_section(text)
    block = _final_machine_lines(text)

    for token in (
        "PREFLIGHT_LIFT_CLASS4_GOVERNED_REFLECTION_V0=true",
        "PREFLIGHT_LIFTED_BY_CLASS4_POLICY=true",
        "ACCEPTED_MODE=PREFLIGHT_LIFT_EXPLICIT_OPERATOR_AUTHORIZATION_CLASS4_DOCS_TESTS_ONLY",
        "OPERATOR_GO=GO_PREFLIGHT_LIFT_EXPLICIT_OPERATOR_AUTHORIZATION_CLASS4_DOCS_TESTS_V0",
        "CLASS4_OPERATOR_GO_ACCEPTED=true",
        "G1_OPERATOR_DECISION_RECORD_FULFILLED=true",
        "POLICY_LIFT_NOT_OPERATIONAL_AUTHORIZATION=true",
        "PREFLIGHT_LIFT_DOES_NOT_CLOSE_ALL_GAPS=true",
        "PREFLIGHT_LIFT_NOT_ARMING=true",
        "PREFLIGHT_LIFT_NOT_EXECUTE=true",
        "PREFLIGHT_LIFT_NOT_LIVE=true",
        "PREFLIGHT_LIFT_NOT_FUTURES_AUTHORITY=true",
        "PREFLIGHT_REMAINS_BLOCKED=false",
        "ALL_GAPS_CLOSED=false",
        "READY_FOR_OPERATOR_ARMING=false",
        "NEXT_EXECUTE_ALLOWED=false",
        "PREFLIGHT_LIFT_EXECUTED=false",
        "ACTUAL_PREFLIGHT_LIFT_EXECUTED=false",
    ):
        assert token in reflection

    assert "Preflight lift ≠ operator arming ≠ execute ≠ live ≠ futures authority" in reflection
    assert "does not set `ALL_GAPS_CLOSED=true`" in reflection
    assert "does not set `READY_FOR_OPERATOR_ARMING=true`" in reflection
    assert "PREFLIGHT_REMAINS_BLOCKED=true" in synthesis
    assert "does not set `PREFLIGHT_REMAINS_BLOCKED=false`" in synthesis
    block_lines = {line.strip() for line in block.splitlines()}
    assert "PREFLIGHT_REMAINS_BLOCKED=false" in block_lines
    assert "PREFLIGHT_LIFTED_BY_CLASS4_POLICY=true" in block_lines
    assert "G1_OPERATOR_DECISION_RECORD_FULFILLED=true" in block_lines
    assert "ALL_GAPS_CLOSED=true" in block_lines
    assert "READY_FOR_OPERATOR_ARMING=true" in block_lines
    assert "NEXT_EXECUTE_ALLOWED=true" in block_lines
    assert "EXECUTE_IS_NOT_RUNTIME_START=true" in block_lines
    assert "PREFLIGHT_LIFT_EXECUTED=true" not in block_lines


def test_section5_all_gaps_closed_final_reflection_after_preflight_lift_non_authorizing_v0() -> (
    None
):
    text = DOC.read_text(encoding="utf-8")
    reflection = _all_gaps_closed_final_reflection_section(text)
    preflight_lift = _preflight_lift_class4_reflection_section(text)
    block = _final_machine_lines(text)

    for token in (
        "ALL_GAPS_CLOSED_CLASS4_GOVERNED_REFLECTION_V0=true",
        "ALL_GAPS_CLOSED=true",
        "ACCEPTED_MODE=SECTION5_ALL_GAPS_CLOSED_FINAL_REFLECTION_DOCS_TESTS_ONLY",
        "OPERATOR_GO=GO_SECTION5_ALL_GAPS_CLOSED_FINAL_REFLECTION_AFTER_PREFLIGHT_LIFT_DOCS_TESTS_V0",
        "CLASS4_OPERATOR_GO_ACCEPTED=true",
        "ALL_SECTION5_GAP_FINAL_TOKENS_TRUE=true",
        "GUARD_GAP_CLOSURE_NOT_AUTHORITY_LIFT=true",
        "ALL_GAPS_CLOSURE_NOT_ARMING=true",
        "ALL_GAPS_CLOSURE_NOT_EXECUTE=true",
        "ALL_GAPS_CLOSURE_NOT_LIVE=true",
        "ALL_GAPS_CLOSURE_NOT_FUTURES_AUTHORITY=true",
        "PREFLIGHT_REMAINS_BLOCKED=false",
        "PREFLIGHT_LIFTED_BY_CLASS4_POLICY=true",
        "READY_FOR_OPERATOR_ARMING=false",
        "NEXT_EXECUTE_ALLOWED=false",
        "SECTION5_GAP_CLOSURE_EXECUTED=false",
    ):
        assert token in reflection

    assert (
        "ALL_GAPS_CLOSED=true ≠ READY_FOR_OPERATOR_ARMING=true ≠ NEXT_EXECUTE_ALLOWED=true"
        in reflection
    )
    assert (
        "does not set `READY_FOR_OPERATOR_ARMING=true` or `NEXT_EXECUTE_ALLOWED=true`" in reflection
    )
    assert "does not set `SECTION5_GAP_CLOSURE_EXECUTED=true`" in reflection
    assert "PREFLIGHT_LIFT_DOES_NOT_CLOSE_ALL_GAPS=true" in preflight_lift
    block_lines = {line.strip() for line in block.splitlines()}
    assert "ALL_GAPS_CLOSED=true" in block_lines
    assert "ALL_GAPS_CLOSED_CLASS4_GOVERNED_REFLECTION_V0=true" in block_lines
    assert "READY_FOR_OPERATOR_ARMING=true" in block_lines
    assert "NEXT_EXECUTE_ALLOWED=true" in block_lines
    assert "EXECUTE_IS_NOT_RUNTIME_START=true" in block_lines
    assert "FUTURES_EXECUTE_AUTHORIZED=true" not in block_lines


def test_section5_operator_arming_explicit_authorization_class4_non_authorizing_v0() -> None:
    text = DOC.read_text(encoding="utf-8")
    reflection = _operator_arming_class4_reflection_section(text)
    all_gaps = _all_gaps_closed_final_reflection_section(text)
    block = _final_machine_lines(text)

    for token in (
        "READY_FOR_OPERATOR_ARMING_CLASS4_GOVERNED_REFLECTION_V0=true",
        "READY_FOR_OPERATOR_ARMING=true",
        "ACCEPTED_MODE=OPERATOR_ARMING_EXPLICIT_AUTHORIZATION_CLASS4_DOCS_TESTS_ONLY",
        "OPERATOR_GO=GO_OPERATOR_ARMING_EXPLICIT_AUTHORIZATION_CLASS4_DOCS_TESTS_V0",
        "CLASS4_OPERATOR_GO_ACCEPTED=true",
        "OPERATOR_ARMING_DECISION_RECORD_REFLECTED=true",
        "GUARD_ARMING_NOT_AUTHORITY_LIFT=true",
        "ARMING_NOT_EXECUTE=true",
        "ARMING_NOT_RUNTIME=true",
        "ARMING_NOT_LIVE=true",
        "ARMING_NOT_FUTURES_AUTHORITY=true",
        "ARMING_NOT_ORDERS=true",
        "ALL_GAPS_CLOSED=true",
        "PREFLIGHT_REMAINS_BLOCKED=false",
        "PREFLIGHT_LIFTED_BY_CLASS4_POLICY=true",
        "NEXT_EXECUTE_ALLOWED=false",
        "RUNTIME_APPROVED=false",
        "FUTURES_EXECUTE_AUTHORIZED=false",
    ):
        assert token in reflection

    assert "READY_FOR_OPERATOR_ARMING=true ≠ NEXT_EXECUTE_ALLOWED=true" in reflection
    assert "does not set `NEXT_EXECUTE_ALLOWED=true`" in reflection
    assert "READY_FOR_OPERATOR_ARMING=false" in all_gaps
    block_lines = {line.strip() for line in block.splitlines()}
    assert "READY_FOR_OPERATOR_ARMING=true" in block_lines
    assert "READY_FOR_OPERATOR_ARMING_CLASS4_GOVERNED_REFLECTION_V0=true" in block_lines
    assert "ARMING_NOT_EXECUTE=true" in block_lines
    assert "NEXT_EXECUTE_ALLOWED=true" in block_lines
    assert "EXECUTE_IS_NOT_RUNTIME_START=true" in block_lines
    assert "FUTURES_EXECUTE_AUTHORIZED=true" not in block_lines


def test_section5_next_execute_explicit_authorization_class4_non_authorizing_v0() -> None:
    text = DOC.read_text(encoding="utf-8")
    reflection = _next_execute_class4_reflection_section(text)
    arming = _operator_arming_class4_reflection_section(text)
    block = _final_machine_lines(text)

    for token in (
        "NEXT_EXECUTE_CLASS4_GOVERNED_REFLECTION_V0=true",
        "NEXT_EXECUTE_ALLOWED=true",
        "ACCEPTED_MODE=NEXT_EXECUTE_EXPLICIT_AUTHORIZATION_CLASS4_DOCS_TESTS_ONLY",
        "OPERATOR_GO=GO_NEXT_EXECUTE_EXPLICIT_AUTHORIZATION_CLASS4_DOCS_TESTS_V0",
        "CLASS4_OPERATOR_GO_ACCEPTED=true",
        "NEXT_EXECUTE_OPERATOR_DECISION_RECORD_REFLECTED=true",
        "GUARD_EXECUTE_NOT_AUTHORITY_LIFT=true",
        "EXECUTE_IS_NOT_RUNTIME_START=true",
        "EXECUTE_NOT_RUNTIME=true",
        "EXECUTE_NOT_LIVE=true",
        "EXECUTE_NOT_FUTURES_AUTHORITY=true",
        "EXECUTE_NOT_ORDERS=true",
        "READY_FOR_OPERATOR_ARMING=true",
        "ARMING_NOT_EXECUTE=true",
        "ALL_GAPS_CLOSED=true",
        "PREFLIGHT_REMAINS_BLOCKED=false",
        "PREFLIGHT_LIFTED_BY_CLASS4_POLICY=true",
        "BOUNDED_EXECUTE_RUN_AUTHORIZED=false",
        "RUNTIME_APPROVED=false",
        "FUTURES_EXECUTE_AUTHORIZED=false",
    ):
        assert token in reflection

    assert "NEXT_EXECUTE_ALLOWED=true ≠ Runtime start" in reflection
    assert "does not set `RUNTIME_APPROVED=true`" in reflection
    assert "NEXT_EXECUTE_ALLOWED=false" in arming
    block_lines = {line.strip() for line in block.splitlines()}
    assert "NEXT_EXECUTE_ALLOWED=true" in block_lines
    assert "NEXT_EXECUTE_CLASS4_GOVERNED_REFLECTION_V0=true" in block_lines
    assert "EXECUTE_IS_NOT_RUNTIME_START=true" in block_lines
    assert "ARMING_NOT_EXECUTE=true" in block_lines
    assert "BOUNDED_EXECUTE_RUN_AUTHORIZED=true" in block_lines
    assert "BOUNDED_EXECUTE_RUN_IS_NOT_LIVE=true" in block_lines
    assert "T3_BOUNDED_EXECUTE_RUN_ATTEMPT_AUTHORIZED=true" in block_lines
    assert "CONCRETE_RUN_AUTHORIZED=false" in block_lines
    assert "FUTURES_EXECUTE_AUTHORIZED=true" not in block_lines


def test_section5_bounded_execute_run_explicit_authorization_class4_non_authorizing_v0() -> None:
    text = DOC.read_text(encoding="utf-8")
    reflection = _bounded_execute_run_class4_reflection_section(text)
    next_execute = _next_execute_class4_reflection_section(text)
    block = _final_machine_lines(text)

    for token in (
        "BOUNDED_EXECUTE_RUN_CLASS4_GOVERNED_REFLECTION_V0=true",
        "BOUNDED_EXECUTE_RUN_AUTHORIZED=true",
        "ACCEPTED_MODE=BOUNDED_EXECUTE_RUN_EXPLICIT_AUTHORIZATION_CLASS4_DOCS_TESTS_ONLY",
        "OPERATOR_GO=GO_BOUNDED_EXECUTE_RUN_EXPLICIT_AUTHORIZATION_CLASS4_DOCS_TESTS_V0",
        "CLASS4_OPERATOR_GO_ACCEPTED=true",
        "BOUNDED_EXECUTE_RUN_OPERATOR_DECISION_RECORD_REFLECTED=true",
        "GUARD_BOUNDED_RUN_NOT_AUTHORITY_LIFT=true",
        "BOUNDED_EXECUTE_RUN_IS_NOT_RUNTIME_START=true",
        "BOUNDED_EXECUTE_RUN_NOT_RUNTIME=true",
        "BOUNDED_EXECUTE_RUN_IS_NOT_LIVE=true",
        "BOUNDED_EXECUTE_RUN_NOT_FUTURES_AUTHORITY=true",
        "BOUNDED_EXECUTE_RUN_NOT_ORDERS=true",
        "READY_FOR_OPERATOR_ARMING=true",
        "ARMING_NOT_EXECUTE=true",
        "NEXT_EXECUTE_ALLOWED=true",
        "EXECUTE_IS_NOT_RUNTIME_START=true",
        "ALL_GAPS_CLOSED=true",
        "PREFLIGHT_REMAINS_BLOCKED=false",
        "PREFLIGHT_LIFTED_BY_CLASS4_POLICY=true",
        "T3_BOUNDED_EXECUTE_RUN_ATTEMPT_AUTHORIZED=false",
        "RUNTIME_APPROVED=false",
        "FUTURES_EXECUTE_AUTHORIZED=false",
    ):
        assert token in reflection

    assert "BOUNDED_EXECUTE_RUN_AUTHORIZED=true ≠ Runtime start" in reflection
    assert "does not set `RUNTIME_APPROVED=true`" in reflection
    assert "BOUNDED_EXECUTE_RUN_AUTHORIZED=false" in next_execute
    block_lines = {line.strip() for line in block.splitlines()}
    assert "BOUNDED_EXECUTE_RUN_AUTHORIZED=true" in block_lines
    assert "BOUNDED_EXECUTE_RUN_CLASS4_GOVERNED_REFLECTION_V0=true" in block_lines
    assert "BOUNDED_EXECUTE_RUN_IS_NOT_RUNTIME_START=true" in block_lines
    assert "BOUNDED_EXECUTE_RUN_IS_NOT_LIVE=true" in block_lines
    assert "ARMING_NOT_EXECUTE=true" in block_lines
    assert "NEXT_EXECUTE_ALLOWED=true" in block_lines
    assert "T3_BOUNDED_EXECUTE_RUN_ATTEMPT_AUTHORIZED=true" in block_lines
    assert "CONCRETE_RUN_AUTHORIZED=false" in block_lines
    assert "FUTURES_EXECUTE_AUTHORIZED=true" not in block_lines


def test_section5_t3_bounded_execute_run_attempt_explicit_authorization_class4_non_authorizing_v0() -> (
    None
):
    text = DOC.read_text(encoding="utf-8")
    reflection = _t3_bounded_execute_run_attempt_class4_reflection_section(text)
    bounded_run = _bounded_execute_run_class4_reflection_section(text)
    block = _final_machine_lines(text)

    for token in (
        "T3_BOUNDED_EXECUTE_RUN_ATTEMPT_CLASS4_GOVERNED_REFLECTION_V0=true",
        "T3_BOUNDED_EXECUTE_RUN_ATTEMPT_AUTHORIZED=true",
        "ACCEPTED_MODE=T3_BOUNDED_EXECUTE_RUN_ATTEMPT_EXPLICIT_AUTHORIZATION_CLASS4_DOCS_TESTS_ONLY",
        "OPERATOR_GO=GO_T3_BOUNDED_EXECUTE_RUN_ATTEMPT_DOCS_TESTS_POLICY_REFLECTION_V0",
        "CLASS4_OPERATOR_GO_ACCEPTED=true",
        "T3_BOUNDED_EXECUTE_RUN_ATTEMPT_OPERATOR_DECISION_RECORD_REFLECTED=true",
        "GUARD_T3_ATTEMPT_NOT_AUTHORITY_LIFT=true",
        "T3_BOUNDED_EXECUTE_RUN_ATTEMPT_IS_NOT_RUNTIME_START=true",
        "T3_BOUNDED_EXECUTE_RUN_ATTEMPT_NOT_RUNTIME=true",
        "T3_BOUNDED_EXECUTE_RUN_ATTEMPT_IS_NOT_LIVE=true",
        "T3_BOUNDED_EXECUTE_RUN_ATTEMPT_NOT_FUTURES_AUTHORITY=true",
        "T3_BOUNDED_EXECUTE_RUN_ATTEMPT_NOT_ORDERS=true",
        "CONCRETE_RUN_AUTHORIZED=false",
        "T3_CONCRETE_RUN_GO_REQUIRED=true",
        "T3_RUN_ATTEMPT_EXECUTE_ALLOWED_NOW=false",
        "READY_FOR_OPERATOR_ARMING=true",
        "ARMING_NOT_EXECUTE=true",
        "NEXT_EXECUTE_ALLOWED=true",
        "EXECUTE_IS_NOT_RUNTIME_START=true",
        "BOUNDED_EXECUTE_RUN_AUTHORIZED=true",
        "ALL_GAPS_CLOSED=true",
        "PREFLIGHT_REMAINS_BLOCKED=false",
        "PREFLIGHT_LIFTED_BY_CLASS4_POLICY=true",
        "RUNTIME_APPROVED=false",
        "RUNTIME_STARTED=false",
        "SCHEDULER_STARTED=false",
        "ORDERS_ATTEMPTED=false",
        "PRIVATE_API_USED=false",
        "CREDENTIALS_READ=false",
        "ENV_FILE_OPENED=false",
        "FUTURES_EXECUTE_AUTHORIZED=false",
    ):
        assert token in reflection

    assert "T3_BOUNDED_EXECUTE_RUN_ATTEMPT_AUTHORIZED=true ≠ Runtime start" in reflection
    assert "does not set `RUNTIME_APPROVED=true`" in reflection
    assert "T3_BOUNDED_EXECUTE_RUN_ATTEMPT_AUTHORIZED=false" in bounded_run
    block_lines = {line.strip() for line in block.splitlines()}
    assert "T3_BOUNDED_EXECUTE_RUN_ATTEMPT_AUTHORIZED=true" in block_lines
    assert "T3_BOUNDED_EXECUTE_RUN_ATTEMPT_CLASS4_GOVERNED_REFLECTION_V0=true" in block_lines
    assert "T3_BOUNDED_EXECUTE_RUN_ATTEMPT_IS_NOT_RUNTIME_START=true" in block_lines
    assert "T3_BOUNDED_EXECUTE_RUN_ATTEMPT_IS_NOT_LIVE=true" in block_lines
    assert "CONCRETE_RUN_AUTHORIZED=false" in block_lines
    assert "T3_CONCRETE_RUN_GO_REQUIRED=true" in block_lines
    assert "T3_RUN_ATTEMPT_EXECUTE_ALLOWED_NOW=false" in block_lines
    assert "FUTURES_EXECUTE_AUTHORIZED=true" not in block_lines


def test_section5_t3_run_attempt_execute_explicit_authorization_class4_non_authorizing_v0() -> None:
    text = DOC.read_text(encoding="utf-8")
    reflection = _t3_run_attempt_execute_class4_reflection_section(text)
    t3_policy = _t3_bounded_execute_run_attempt_class4_reflection_section(text)
    block = _final_machine_lines(text)

    for token in (
        "T3_RUN_ATTEMPT_EXECUTE_CLASS4_GOVERNED_REFLECTION_V0=true",
        "T3_RUN_ATTEMPT_EXECUTE_AUTHORIZED=true",
        "ACCEPTED_MODE=T3_RUN_ATTEMPT_EXECUTE_EXPLICIT_AUTHORIZATION_CLASS4_DOCS_TESTS_ONLY",
        "OPERATOR_GO=GO_T3_RUN_ATTEMPT_EXECUTE_DOCS_TESTS_POLICY_REFLECTION_V0",
        "CLASS4_OPERATOR_GO_ACCEPTED=true",
        "T3_RUN_ATTEMPT_EXECUTE_OPERATOR_DECISION_RECORD_REFLECTED=true",
        "GUARD_T3_EXECUTE_NOT_AUTHORITY_LIFT=true",
        "T3_RUN_ATTEMPT_EXECUTE_IS_NOT_RUNTIME_START=true",
        "T3_RUN_ATTEMPT_EXECUTE_NOT_RUNTIME=true",
        "T3_RUN_ATTEMPT_EXECUTE_IS_NOT_LIVE=true",
        "T3_RUN_ATTEMPT_EXECUTE_NOT_FUTURES_AUTHORITY=true",
        "T3_RUN_ATTEMPT_EXECUTE_NOT_ORDERS=true",
        "CONCRETE_RUN_AUTHORIZED=false",
        "T3_CONCRETE_RUN_GO_REQUIRED=true",
        "T3_RUN_ATTEMPT_READINESS_PREFLIGHT_REQUIRED=true",
        "T3_RUN_ATTEMPT_EXECUTE_ALLOWED_NOW=false",
        "T3_BOUNDED_EXECUTE_RUN_ATTEMPT_AUTHORIZED=true",
        "T3_BOUNDED_EXECUTE_RUN_ATTEMPT_OPERATOR_DECISION_RECORD_REFLECTED=true",
        "ALL_GAPS_CLOSED=true",
        "PREFLIGHT_REMAINS_BLOCKED=false",
        "PREFLIGHT_LIFTED_BY_CLASS4_POLICY=true",
        "RUNTIME_APPROVED=false",
        "RUNTIME_STARTED=false",
        "SCHEDULER_STARTED=false",
        "ORDERS_ATTEMPTED=false",
        "PRIVATE_API_USED=false",
        "CREDENTIALS_READ=false",
        "ENV_FILE_OPENED=false",
        "FUTURES_EXECUTE_AUTHORIZED=false",
        "FUTURES_PRIVATE_API_AUTHORIZED=false",
        "FUTURES_VALIDATE_ONLY_AUTHORIZED=false",
        "FUTURES_SESSION_AUTHORIZED_NOW=false",
    ):
        assert token in reflection

    assert "T3_RUN_ATTEMPT_EXECUTE_AUTHORIZED=true ≠ Runtime start" in reflection
    assert "does not set `RUNTIME_APPROVED=true`" in reflection
    assert "T3_RUN_ATTEMPT_EXECUTE_AUTHORIZED=false" not in t3_policy
    block_lines = {line.strip() for line in block.splitlines()}
    assert "T3_RUN_ATTEMPT_EXECUTE_AUTHORIZED=true" in block_lines
    assert "T3_RUN_ATTEMPT_EXECUTE_CLASS4_GOVERNED_REFLECTION_V0=true" in block_lines
    assert "T3_RUN_ATTEMPT_EXECUTE_OPERATOR_DECISION_RECORD_REFLECTED=true" in block_lines
    assert "T3_RUN_ATTEMPT_EXECUTE_IS_NOT_RUNTIME_START=true" in block_lines
    assert "T3_RUN_ATTEMPT_EXECUTE_IS_NOT_LIVE=true" in block_lines
    assert "T3_RUN_ATTEMPT_READINESS_PREFLIGHT_REQUIRED=true" in block_lines
    assert "CONCRETE_RUN_AUTHORIZED=false" in block_lines
    assert "T3_CONCRETE_RUN_GO_REQUIRED=true" in block_lines
    assert "T3_RUN_ATTEMPT_EXECUTE_ALLOWED_NOW=false" in block_lines
    assert "FUTURES_EXECUTE_AUTHORIZED=true" not in block_lines


def test_section5_t3_plan_only_closeout_class4_non_authorizing_v0() -> None:
    text = DOC.read_text(encoding="utf-8")
    reflection = _t3_plan_only_closeout_class4_reflection_section(text)
    execute_policy = _t3_run_attempt_execute_class4_reflection_section(text)
    block = _final_machine_lines(text)

    for token in (
        "T3_PLAN_ONLY_CLOSEOUT_CLASS4_GOVERNED_REFLECTION_V0=true",
        "T3_PLAN_ONLY_EXECUTE_CLOSEOUT_REFLECTED=true",
        "T3_BOUNDED_EXECUTE_RUN_ATTEMPT_PLAN_ONLY_COMPLETED=true",
        "PLAN_ONLY_EXECUTE_RC=0",
        "T3_PLAN_ONLY_EXECUTE_CLOSEOUT_PASSED=true",
        "ACCEPTED_MODE=T3_PLAN_ONLY_CLOSEOUT_DOCS_TESTS_ONLY",
        "OPERATOR_GO=GO_T3_PLAN_ONLY_CLOSEOUT_DOCS_TESTS_POLICY_REFLECTION_V0",
        "CLASS4_OPERATOR_GO_ACCEPTED=true",
        "GUARD_T3_PLAN_ONLY_NOT_AUTHORITY_LIFT=true",
        "T3_PLAN_ONLY_EXECUTE_IS_NOT_RUNTIME_START=true",
        "T3_PLAN_ONLY_EXECUTE_IS_NOT_LIVE=true",
        "T3_PLAN_ONLY_EXECUTE_NOT_RUNTIME=true",
        "T3_PLAN_ONLY_EXECUTE_NOT_ORDERS=true",
        "CONCRETE_RUN_AUTHORIZED=false",
        "T3_RUN_ATTEMPT_EXECUTE_ALLOWED_NOW=false",
        "NEXT_RUNTIME_STAGE_REQUIRES_SEPARATE_CHARTER=true",
        "RUNTIME_STARTED=false",
        "SCHEDULER_STARTED=false",
        "ORDERS_ATTEMPTED=false",
        "PRIVATE_API_USED=false",
        "CREDENTIALS_READ=false",
        "ENV_FILE_OPENED=false",
        "FUTURES_EXECUTE_AUTHORIZED=false",
        "FUTURES_PRIVATE_API_AUTHORIZED=false",
        "FUTURES_VALIDATE_ONLY_AUTHORIZED=false",
        "FUTURES_SESSION_AUTHORIZED_NOW=false",
    ):
        assert token in reflection

    assert "INPUT_T3_PLAN_ONLY_CLOSEOUT_POINTER=" in reflection
    assert "INPUT_T3_PLAN_ONLY_EVIDENCE_RUN_ROOT_POINTER=" in reflection
    assert "T3_PLAN_ONLY_EXECUTE_CLOSEOUT_REFLECTED=true ≠ Runtime start" in reflection
    assert "does not set `T3_RUN_ATTEMPT_EXECUTE_ALLOWED_NOW=true`" in reflection
    assert "T3_PLAN_ONLY_EXECUTE_CLOSEOUT_REFLECTED=true" not in execute_policy
    block_lines = {line.strip() for line in block.splitlines()}
    assert "T3_PLAN_ONLY_EXECUTE_CLOSEOUT_REFLECTED=true" in block_lines
    assert "T3_BOUNDED_EXECUTE_RUN_ATTEMPT_PLAN_ONLY_COMPLETED=true" in block_lines
    assert "T3_PLAN_ONLY_EXECUTE_CLOSEOUT_PASSED=true" in block_lines
    assert "NEXT_RUNTIME_STAGE_REQUIRES_SEPARATE_CHARTER=true" in block_lines
    assert "T3_RUN_ATTEMPT_EXECUTE_ALLOWED_NOW=false" in block_lines
    assert "CONCRETE_RUN_AUTHORIZED=false" in block_lines
    assert "FUTURES_EXECUTE_AUTHORIZED=true" not in block_lines


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
    assert "ALL_GAPS_CLOSED=true" in block_lines
    assert "READY_FOR_OPERATOR_ARMING=true" in block_lines


GAP6_ACCEPTED_FINAL_LINE_REFLECTION_HEADER = (
    "## Gap 6 Governed Dry-Run Proof Accepted Final-Line Reflection v0"
)


def _gap6_accepted_final_line_reflection_section(text: str) -> str:
    return text.split(GAP6_ACCEPTED_FINAL_LINE_REFLECTION_HEADER, 1)[1].split(
        "## Gap 6 Governed Bounded Dry-Run RC0 Observed Evidence Reflection v0", 1
    )[0]


def test_section5_gap6_dry_run_proof_accepted_final_line_reflection_non_authorizing_v0() -> None:
    text = DOC.read_text(encoding="utf-8")
    section = _gap6_accepted_final_line_reflection_section(text)
    block = _final_machine_lines(text)

    for token in (
        "GAP6_DRY_RUN_PROOF_ACCEPTED_FINAL_LINE_GOVERNED_REFLECTION_V0=true",
        "ACCEPTED_NOT_VERIFIED_NOT_OBSERVED_SEMANTIC_PRESERVED=true",
        "GAP6_DRY_RUN_PROOF_VERIFIED=false",
        "PREFLIGHT_REMAINS_BLOCKED=true",
        "ALL_GAPS_CLOSED=false",
    ):
        assert token in section

    assert "GAP6_DRY_RUN_PROOF_ACCEPTED=true" in block
    assert "GAP6_DRY_RUN_PROOF_VERIFIED=true" in block
    assert "GAP6_DRY_RUN_RC0_OBSERVED=true" in block
    block_lines = {line.strip() for line in block.splitlines()}
    assert "GAP6_DRY_RUN_PROOF_VERIFIED=true" in block_lines
    assert "READY_FOR_OPERATOR_ARMING=true" in block_lines


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
    assert "GAP6_DRY_RUN_PROOF_VERIFIED=true" in block
    assert "GAP1_EXECUTE_ENTRYPOINT_VERIFIED=true" in block
    block_lines = {line.strip() for line in block.splitlines()}
    assert "GAP6_DRY_RUN_PROOF_VERIFIED=true" in block_lines
    assert "GAP1_EXECUTE_ENTRYPOINT_VERIFIED=true" in block_lines
    assert "READY_FOR_OPERATOR_ARMING=true" in block_lines


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
    assert "GAP2_CANONICAL_JOB_SET_DRY_RUN_OBSERVED=true" in block
    assert "GAP2_CANONICAL_JOB_SET_VERIFIED=true" in block
    assert "GAP3_EXECUTE_COMMAND_DRY_RUN_RC0_OBSERVED=true" in block
    assert "GAP3_EXECUTE_COMMAND_VERIFIED=true" in block
    block_lines = {line.strip() for line in block.splitlines()}
    assert "GAP2_CANONICAL_JOB_SET_VERIFIED=true" in block_lines
    assert "GAP3_EXECUTE_COMMAND_VERIFIED=true" in block_lines
    assert "READY_FOR_OPERATOR_ARMING=true" in block_lines


GAP2_DRY_RUN_OBSERVED_FINAL_LINE_REFLECTION_HEADER = (
    "## Gap 2 Governed Canonical Job Set Dry-Run Observed Final-Line Reflection v0"
)
GAP2_VERIFIED_FINAL_LINE_REFLECTION_HEADER = (
    "## Gap 2 Governed Canonical Job Set Verified Final-Line Reflection v0"
)
GAP3_ACCEPTED_SCOPED_CRITERIA_FINAL_LINE_REFLECTION_HEADER = (
    "## Gap 3 Governed Tier-2 Command Accepted Scoped-Criteria Final-Line Reflection v0"
)
GAP3_DRY_RUN_RC0_OBSERVED_FINAL_LINE_REFLECTION_HEADER = (
    "## Gap 3 Governed Tier-2 Command Dry-Run RC0 Observed Final-Line Reflection v0"
)
GAP3_VERIFIED_FINAL_LINE_REFLECTION_HEADER = (
    "## Gap 3 Governed Execute Command Verified Final-Line Reflection v0"
)


def _gap2_dry_run_observed_final_line_reflection_section(text: str) -> str:
    return text.split(GAP2_DRY_RUN_OBSERVED_FINAL_LINE_REFLECTION_HEADER, 1)[1].split(
        GAP2_VERIFIED_FINAL_LINE_REFLECTION_HEADER, 1
    )[0]


def _gap2_verified_final_line_reflection_section(text: str) -> str:
    return text.split(GAP2_VERIFIED_FINAL_LINE_REFLECTION_HEADER, 1)[1].split(
        GAP3_ACCEPTED_SCOPED_CRITERIA_FINAL_LINE_REFLECTION_HEADER, 1
    )[0]


def test_section5_gap2_dry_run_observed_final_line_reflection_non_authorizing_v0() -> None:
    text = DOC.read_text(encoding="utf-8")
    section = _gap2_dry_run_observed_final_line_reflection_section(text)
    block = _final_machine_lines(text)

    for token in (
        "GAP2_CANONICAL_JOB_SET_DRY_RUN_OBSERVED_FINAL_LINE_GOVERNED_REFLECTION_V0=true",
        "OBSERVED_NOT_VERIFIED_SEMANTIC_PRESERVED=true",
        "GAP2_CANONICAL_JOB_SET_VERIFIED=false",
        "GAP2_ACCEPTED_SCOPED_CRITERIA=true",
        "PREFLIGHT_REMAINS_BLOCKED=true",
        "ALL_GAPS_CLOSED=false",
    ):
        assert token in section

    assert "GAP2_CANONICAL_JOB_SET_DRY_RUN_OBSERVED=true" in block
    assert "GAP2_ACCEPTED_SCOPED_CRITERIA=true" in block
    assert "GAP2_CANONICAL_JOB_SET_VERIFIED=true" in block
    block_lines = {line.strip() for line in block.splitlines()}
    assert "GAP2_CANONICAL_JOB_SET_VERIFIED=true" in block_lines
    assert "READY_FOR_OPERATOR_ARMING=true" in block_lines


def test_section5_gap2_verified_final_line_reflection_non_authorizing_v0() -> None:
    text = DOC.read_text(encoding="utf-8")
    section = _gap2_verified_final_line_reflection_section(text)
    block = _final_machine_lines(text)
    gap2 = text.split("## Gap 2 Canonical Job Set Contract v0", 1)[1].split(
        "## Final Machine Lines", 1
    )[0]

    for token in (
        "GAP2_CANONICAL_JOB_SET_VERIFIED_FINAL_LINE_GOVERNED_REFLECTION_V0=true",
        "VERIFIED_BAR_TIER=T1_PLUS_T2_BOUNDARY_INVENTORY",
        "T1_STATIC_READONLY_SUFFICIENT_FOR_VERIFIED=false",
        "T2_DRY_RUN_FULL_INVENTORY_SUFFICIENT_FOR_VERIFIED=true",
        "T3_BOUNDED_EXECUTE_REQUIRED_FOR_VERIFIED=false",
        "GAP2_VERIFIED_REQUIRES_RUNTIME_EXECUTE=false",
        "VERIFIED_NOT_OBSERVED_SEMANTIC_PRESERVED=true",
        "GAP2_CANONICAL_JOB_SET_DRY_RUN_OBSERVED=true",
        "GAP2_ACCEPTED_SCOPED_CRITERIA=true",
        "GAP3_EXECUTE_COMMAND_VERIFIED=false",
        "PREFLIGHT_REMAINS_BLOCKED=true",
        "ALL_GAPS_CLOSED=false",
    ):
        assert token in section

    assert "GAP2_CANONICAL_JOB_SET_VERIFIED=true" in block
    assert "VERIFIED_BAR_TIER=T1_PLUS_T2_BOUNDARY_INVENTORY" in block
    assert "GAP2_CANONICAL_JOB_SET_VERIFIED=false" in gap2
    assert "GAP3_EXECUTE_COMMAND_VERIFIED=true" in block
    block_lines = {line.strip() for line in block.splitlines()}
    assert "GAP2_CANONICAL_JOB_SET_VERIFIED=true" in block_lines
    assert "GAP3_EXECUTE_COMMAND_VERIFIED=true" in block_lines
    assert "READY_FOR_OPERATOR_ARMING=true" in block_lines


def _gap3_dry_run_rc0_observed_final_line_reflection_section(text: str) -> str:
    return text.split(GAP3_DRY_RUN_RC0_OBSERVED_FINAL_LINE_REFLECTION_HEADER, 1)[1].split(
        GAP3_VERIFIED_FINAL_LINE_REFLECTION_HEADER, 1
    )[0]


def _gap3_verified_final_line_reflection_section(text: str) -> str:
    return text.split(GAP3_VERIFIED_FINAL_LINE_REFLECTION_HEADER, 1)[1].split(
        "## Gap 5 Governed Stop Proof Acceptance Reflection v0", 1
    )[0]


def test_section5_gap3_dry_run_rc0_observed_final_line_reflection_non_authorizing_v0() -> None:
    text = DOC.read_text(encoding="utf-8")
    section = _gap3_dry_run_rc0_observed_final_line_reflection_section(text)
    block = _final_machine_lines(text)
    gap3 = text.split("## Gap 3 Execute Command Contract v0", 1)[1].split(
        "## Final Machine Lines", 1
    )[0]

    for token in (
        "GAP3_EXECUTE_COMMAND_DRY_RUN_RC0_OBSERVED_FINAL_LINE_GOVERNED_REFLECTION_V0=true",
        "OBSERVED_NOT_VERIFIED_SEMANTIC_PRESERVED=true",
        "GAP3_EXECUTE_COMMAND_VERIFIED=false",
        "PREFLIGHT_REMAINS_BLOCKED=true",
        "ALL_GAPS_CLOSED=false",
    ):
        assert token in section

    assert "GAP3_EXECUTE_COMMAND_DRY_RUN_RC0_OBSERVED=true" in block
    assert "GAP3_EXECUTE_COMMAND_VERIFIED=true" in block
    assert "GAP3_EXECUTE_COMMAND_VERIFIED=false" in gap3
    block_lines = {line.strip() for line in block.splitlines()}
    assert "GAP3_EXECUTE_COMMAND_DRY_RUN_RC0_OBSERVED=true" in block_lines
    assert "READY_FOR_OPERATOR_ARMING=true" in block_lines


def test_section5_gap3_verified_final_line_reflection_non_authorizing_v0() -> None:
    text = DOC.read_text(encoding="utf-8")
    section = _gap3_verified_final_line_reflection_section(text)
    block = _final_machine_lines(text)
    gap3 = text.split("## Gap 3 Execute Command Contract v0", 1)[1].split(
        "## Final Machine Lines", 1
    )[0]

    for token in (
        "GAP3_EXECUTE_COMMAND_VERIFIED_FINAL_LINE_GOVERNED_REFLECTION_V0=true",
        "GAP3_VERIFIED_BAR_TIER=T1_PLUS_T2_COMMAND_BOUNDARY",
        "T1_STATIC_READONLY_SUFFICIENT_FOR_GAP3_VERIFIED=false",
        "T2_DRY_RUN_COMMAND_RC0_SUFFICIENT_FOR_GAP3_VERIFIED=true",
        "T3_BOUNDED_EXECUTE_REQUIRED_FOR_GAP3_VERIFIED=false",
        "GAP3_VERIFIED_REQUIRES_RUNTIME_EXECUTE=false",
        "VERIFIED_NOT_OBSERVED_SEMANTIC_PRESERVED=true",
        "GAP3_EXECUTE_COMMAND_DRY_RUN_RC0_OBSERVED=true",
        "GAP3_ACCEPTED_SCOPED_CRITERIA=true",
        "PREFLIGHT_REMAINS_BLOCKED=true",
        "ALL_GAPS_CLOSED=false",
    ):
        assert token in section

    assert "GAP3_EXECUTE_COMMAND_VERIFIED=true" in block
    assert "GAP3_VERIFIED_BAR_TIER=T1_PLUS_T2_COMMAND_BOUNDARY" in block
    assert "GAP3_EXECUTE_COMMAND_VERIFIED=false" in gap3
    block_lines = {line.strip() for line in block.splitlines()}
    assert "GAP3_EXECUTE_COMMAND_VERIFIED=true" in block_lines
    assert "READY_FOR_OPERATOR_ARMING=true" in block_lines


GAP6_VERIFIED_FINAL_LINE_REFLECTION_HEADER = (
    "## Gap 6 Governed Dry-Run Proof Verified Final-Line Reflection v0"
)


def _gap6_verified_final_line_reflection_section(text: str) -> str:
    return text.split(GAP6_VERIFIED_FINAL_LINE_REFLECTION_HEADER, 1)[1].split(
        "## Gap 1 Governed Execute Entrypoint RC0 Observed Final-Line Reflection v0", 1
    )[0]


def test_section5_gap6_verified_final_line_reflection_non_authorizing_v0() -> None:
    text = DOC.read_text(encoding="utf-8")
    section = _gap6_verified_final_line_reflection_section(text)
    block = _final_machine_lines(text)
    gap6 = text.split("## Gap 6 Dry-Run Proof Criteria Contract v0", 1)[1].split(
        "## Final Machine Lines", 1
    )[0]

    for token in (
        "GAP6_DRY_RUN_PROOF_VERIFIED_FINAL_LINE_GOVERNED_REFLECTION_V0=true",
        "GAP6_VERIFIED_BAR_TIER=T1_PLUS_T2_DRY_RUN_PROOF",
        "T1_STATIC_READONLY_SUFFICIENT_FOR_GAP6_VERIFIED=false",
        "T2_DRY_RUN_PROOF_RC0_SUFFICIENT_FOR_GAP6_VERIFIED=true",
        "T3_BOUNDED_EXECUTE_REQUIRED_FOR_GAP6_VERIFIED=false",
        "GAP6_VERIFIED_REQUIRES_RUNTIME_EXECUTE=false",
        "VERIFIED_NOT_OBSERVED_NOT_ACCEPTED_SEMANTIC_PRESERVED=true",
        "GAP6_DRY_RUN_RC0_OBSERVED=true",
        "GAP6_DRY_RUN_PROOF_ACCEPTED=true",
        "GAP1_EXECUTE_ENTRYPOINT_VERIFIED=false",
        "PREFLIGHT_REMAINS_BLOCKED=true",
        "ALL_GAPS_CLOSED=false",
    ):
        assert token in section

    assert "GAP6_DRY_RUN_PROOF_VERIFIED=true" in block
    assert "GAP6_VERIFIED_BAR_TIER=T1_PLUS_T2_DRY_RUN_PROOF" in block
    assert "GAP6_DRY_RUN_PROOF_VERIFIED=false" in gap6
    block_lines = {line.strip() for line in block.splitlines()}
    assert "GAP6_DRY_RUN_PROOF_VERIFIED=true" in block_lines
    assert "READY_FOR_OPERATOR_ARMING=true" in block_lines


GAP1_VERIFIED_FINAL_LINE_REFLECTION_HEADER = (
    "## Gap 1 Governed Execute Entrypoint Verified Final-Line Reflection v0"
)


def _gap1_verified_final_line_reflection_section(text: str) -> str:
    return text.split(GAP1_VERIFIED_FINAL_LINE_REFLECTION_HEADER, 1)[1].split(
        "## Tier-1 Governed Zero-Dispatch Manifest Observed Final-Line Reflection v0", 1
    )[0]


def test_section5_gap1_verified_final_line_reflection_non_authorizing_v0() -> None:
    text = DOC.read_text(encoding="utf-8")
    section = _gap1_verified_final_line_reflection_section(text)
    block = _final_machine_lines(text)
    gap1 = text.split("## Gap 1 Execute Entrypoint Contract v0", 1)[1].split(
        "## Gap 3 Execute Command Contract v0", 1
    )[0]

    for token in (
        "GAP1_EXECUTE_ENTRYPOINT_VERIFIED_FINAL_LINE_GOVERNED_REFLECTION_V0=true",
        "GAP1_VERIFIED_BAR_TIER=T1_PLUS_T2_ENTRYPOINT_BOUNDARY",
        "T1_STATIC_READONLY_SUFFICIENT_FOR_GAP1_VERIFIED=false",
        "T2_ENTRYPOINT_DRY_RUN_RC0_SUFFICIENT_FOR_GAP1_VERIFIED=true",
        "T3_BOUNDED_EXECUTE_REQUIRED_FOR_GAP1_VERIFIED=false",
        "GAP1_VERIFIED_REQUIRES_RUNTIME_EXECUTE=false",
        "VERIFIED_NOT_OBSERVED_SEMANTIC_PRESERVED=true",
        "GAP1_EXECUTE_ENTRYPOINT_RC0_OBSERVED=true",
        "GAP6_DRY_RUN_PROOF_VERIFIED=true",
        "PREFLIGHT_REMAINS_BLOCKED=true",
        "ALL_GAPS_CLOSED=false",
    ):
        assert token in section

    assert "GAP1_EXECUTE_ENTRYPOINT_VERIFIED=true" in block
    assert "GAP1_VERIFIED_BAR_TIER=T1_PLUS_T2_ENTRYPOINT_BOUNDARY" in block
    assert "GAP1_EXECUTE_ENTRYPOINT_VERIFIED=false" in gap1
    block_lines = {line.strip() for line in block.splitlines()}
    assert "GAP1_EXECUTE_ENTRYPOINT_VERIFIED=true" in block_lines
    assert "READY_FOR_OPERATOR_ARMING=true" in block_lines


GAP5_REHEARSAL_VERIFIED_FINAL_LINE_REFLECTION_HEADER = (
    "## Gap 5 Governed Stop Rehearsal Verified Final-Line Reflection v0"
)


def _gap5_rehearsal_verified_final_line_reflection_section(text: str) -> str:
    return text.split(GAP5_REHEARSAL_VERIFIED_FINAL_LINE_REFLECTION_HEADER, 1)[1].split(
        "## Gap 6 Governed Dry-Run Proof Acceptance Reflection v0", 1
    )[0]


def test_section5_gap5_rehearsal_verified_final_line_reflection_non_authorizing_v0() -> None:
    text = DOC.read_text(encoding="utf-8")
    section = _gap5_rehearsal_verified_final_line_reflection_section(text)
    block = _final_machine_lines(text)
    gap5 = text.split("## Gap 5 Stop Criteria Contract v0", 1)[1].split(
        "## Gap 2 Canonical Job Set Contract v0", 1
    )[0]

    for token in (
        "GAP5_STOP_REHEARSAL_VERIFIED_FINAL_LINE_GOVERNED_REFLECTION_V0=true",
        "GAP5_VERIFIED_BAR_TIER=T0_CHARTER_PRECHECK_PLUS_T1_READONLY_SIGNAL_PLUS_T2_ISOLATED_REHEARSAL",
        "ISOLATED_REHEARSAL_CONTEXT_USED=true",
        "STOP_REHEARSAL_EXECUTED_EXTERNAL_BUNDLE=true",
        "REAL_PROCESS_SIGNAL_SENT=false",
        "REAL_PROCESS_KILLED=false",
        "EXTERNAL_T2_REHEARSAL_EVIDENCE_POINTER=",
        "gap5_stop_rehearsal_bounded_execute_v0_20260604T215341Z",
        "PREFLIGHT_REMAINS_BLOCKED=true",
        "ALL_GAPS_CLOSED=false",
    ):
        assert token in section

    assert "GAP5_STOP_REHEARSAL_EXECUTED=true" in block
    assert "GAP5_STOP_REHEARSAL_EXECUTED=false" in gap5
    block_lines = {line.strip() for line in block.splitlines()}
    assert "GAP5_STOP_REHEARSAL_EXECUTED=true" in block_lines
    assert "READY_FOR_OPERATOR_ARMING=true" in block_lines


TIER1_ZERO_DISPATCH_MANIFEST_OBSERVED_FINAL_LINE_REFLECTION_HEADER = (
    "## Tier-1 Governed Zero-Dispatch Manifest Observed Final-Line Reflection v0"
)
TIER1_CANONICAL_TAG_BOUNDED_ENFORCE_OBSERVED_FINAL_LINE_REFLECTION_HEADER = (
    "## Tier-1 Governed Canonical-Tag Bounded Enforce Observed Final-Line Reflection v0"
)


def _tier1_zero_dispatch_manifest_observed_final_line_reflection_section(text: str) -> str:
    return text.split(TIER1_ZERO_DISPATCH_MANIFEST_OBSERVED_FINAL_LINE_REFLECTION_HEADER, 1)[
        1
    ].split(TIER1_CANONICAL_TAG_BOUNDED_ENFORCE_OBSERVED_FINAL_LINE_REFLECTION_HEADER, 1)[0]


def _tier1_canonical_tag_bounded_enforce_observed_final_line_reflection_section(
    text: str,
) -> str:
    return text.split(TIER1_CANONICAL_TAG_BOUNDED_ENFORCE_OBSERVED_FINAL_LINE_REFLECTION_HEADER, 1)[
        1
    ].split("## Gap-2a.1 Governed Primary Evidence Repo-Lift CLASS_4 Reflection v0", 1)[0]


def test_section5_tier1_zero_dispatch_manifest_observed_final_line_reflection_v0() -> None:
    text = DOC.read_text(encoding="utf-8")
    section = _tier1_zero_dispatch_manifest_observed_final_line_reflection_section(text)
    block = _final_machine_lines(text)
    gap2a1 = _gap2a1_section(text)

    for token in (
        "TIER1_ZERO_DISPATCH_MANIFEST_OBSERVED_FINAL_LINE_GOVERNED_REFLECTION_V0=true",
        "TIER1_PRIMARY_EVIDENCE_ENFORCEMENT_ZERO_DISPATCH_OBSERVED=true",
        "TIER1_PRIMARY_EVIDENCE_MANIFEST_CREATED=true",
        "TIER1_PRIMARY_EVIDENCE_MANIFEST_VERIFY_RC=0",
        "PRIMARY_EVIDENCE_ENFORCED_SCOPE=zero_dispatch_local_only",
        "OBSERVED_NOT_ENFORCED_REPO_SSOT_SEMANTIC_PRESERVED=true",
        "GAP2A1_TIER1_ENFORCEMENT_LIFTED_REPO=false",
        "SECTION5_GAP2A1_REPO_LIFTED=false",
        "GAP2A1_TIER1_ENFORCEMENT_LIFTED_EXTERNAL_SESSION_ONLY=true",
        "GAP2_CANONICAL_JOB_SET_VERIFIED=false",
        "GAP3_EXECUTE_COMMAND_VERIFIED=false",
        "PREFLIGHT_REMAINS_BLOCKED=true",
        "ALL_GAPS_CLOSED=false",
    ):
        assert token in section

    assert "PRIMARY_EVIDENCE_ENFORCED=true" in block
    assert "PRIMARY_EVIDENCE_ENFORCED_SCOPE=zero_dispatch_local_only" in block
    assert "TIER1_PRIMARY_EVIDENCE_ENFORCEMENT_ZERO_DISPATCH_OBSERVED=true" in block
    assert "GAP2A1_PRIMARY_EVIDENCE_ENFORCED=true" in block
    assert "GAP2A1_TIER1_ENFORCEMENT_LIFTED=true" in block
    gap2a1_lines = {line.strip() for line in gap2a1.splitlines()}
    assert "GAP2A1_PRIMARY_EVIDENCE_ENFORCED=true" not in gap2a1_lines
    block_lines = {line.strip() for line in block.splitlines()}
    assert "GAP2A1_PRIMARY_EVIDENCE_ENFORCED=true" in block_lines
    assert "GAP2A1_TIER1_ENFORCEMENT_LIFTED=true" in block_lines
    assert "READY_FOR_OPERATOR_ARMING=true" in block_lines


def test_section5_tier1_canonical_tag_bounded_enforce_observed_final_line_reflection_v0() -> None:
    text = DOC.read_text(encoding="utf-8")
    section = _tier1_canonical_tag_bounded_enforce_observed_final_line_reflection_section(text)
    block = _final_machine_lines(text)
    gap2a1 = _gap2a1_section(text)
    gap2 = text.split("## Gap 2 Canonical Job Set Contract v0", 1)[1].split(
        "## Final Machine Lines", 1
    )[0]

    for token in (
        "TIER1_CANONICAL_TAG_BOUNDED_ENFORCE_OBSERVED_FINAL_LINE_GOVERNED_REFLECTION_V0=true",
        "TIER1_CANONICAL_TAG_BOUNDED_ENFORCE_OBSERVED=true",
        "TIER1_CANONICAL_TAG_PRIMARY_EVIDENCE_MANIFEST_CREATED=true",
        "TIER1_CANONICAL_TAG_PRIMARY_EVIDENCE_MANIFEST_VERIFY_RC=0",
        "PRIMARY_EVIDENCE_ENFORCED_SCOPE=canonical_tag_local_readonly_preflight_once",
        "OBSERVED_NOT_ENFORCED_REPO_SSOT_SEMANTIC_PRESERVED=true",
        "OBSERVED_JOB_STARTED=paper_shadow_247_paper_only_preflight_status_v0",
        "UNEXPECTED_JOB_STARTED=false",
        "GAP2A1_TIER1_ENFORCEMENT_LIFTED_REPO=false",
        "SECTION5_GAP2A1_REPO_LIFTED=false",
        "GAP2_CANONICAL_JOB_SET_VERIFIED=false",
        "GAP3_EXECUTE_COMMAND_VERIFIED=false",
        "PREFLIGHT_REMAINS_BLOCKED=true",
        "ALL_GAPS_CLOSED=false",
    ):
        assert token in section

    assert "TIER1_CANONICAL_TAG_BOUNDED_ENFORCE_OBSERVED=true" in block
    assert "PRIMARY_EVIDENCE_ENFORCED_SCOPE=canonical_tag_local_readonly_preflight_once" in block
    assert "GAP2A1_PRIMARY_EVIDENCE_ENFORCED=true" in block
    assert "GAP2A1_TIER1_ENFORCEMENT_LIFTED=true" in block
    assert "TIER1_CANONICAL_TAG_BOUNDED_ENFORCE_OBSERVED=true" not in gap2
    gap2a1_lines = {line.strip() for line in gap2a1.splitlines()}
    assert "GAP2A1_PRIMARY_EVIDENCE_ENFORCED=true" not in gap2a1_lines
    assert "TIER1_CANONICAL_TAG_BOUNDED_ENFORCE_OBSERVED=true" not in gap2a1_lines
    block_lines = {line.strip() for line in block.splitlines()}
    assert "GAP2A1_PRIMARY_EVIDENCE_ENFORCED=true" in block_lines
    assert "GAP2A1_TIER1_ENFORCEMENT_LIFTED=true" in block_lines
    assert "READY_FOR_OPERATOR_ARMING=true" in block_lines
