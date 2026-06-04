from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
DOC = ROOT / "docs" / "ops" / "planning" / "SECTION5_PREFLIGHT_GAP_OWNER_MAP_CONTRACT_V0.md"
PREFLIGHT = ROOT / "docs" / "ops" / "runbooks" / "PAPER_SHADOW_247_PREFLIGHT_CONTRACT_V0.md"
HARD_GATE_TESTS = ROOT / "tests" / "ops" / "test_run_primary_evidence_retention_hard_gate_v0.py"
BOUNDED_REVIEW_TESTS = (
    ROOT
    / "tests"
    / "ops"
    / "test_bounded_observation_review_durable_primary_evidence_contract_v0.py"
)


def test_gap2a1_primary_evidence_enforcement_contract_is_present_and_non_authorizing():
    text = DOC.read_text(encoding="utf-8")

    required = [
        "GAP2A1_PRIMARY_EVIDENCE_ENFORCEMENT_CONTRACT_V0=true",
        "GAP2A1_PRIMARY_EVIDENCE_ENFORCED=false",
        "GAP2A1_ENFORCEMENT_DEFAULT_ON=false",
        "GAP2A1_ENFORCEMENT_OPT_IN_ONLY=true",
        "PATH_B_LIFT_DISCUSSION_READY=false",
        "PREFLIGHT_REMAINS_BLOCKED=true",
        "READY_FOR_OPERATOR_ARMING=false",
        "RUNTIME_APPROVED=false",
    ]

    for marker in required:
        assert marker in text


def test_gap2a1_primary_evidence_enforcement_contract_reuses_existing_surfaces():
    text = DOC.read_text(encoding="utf-8")

    required_surfaces = [
        "scripts/ops/primary_evidence_retention_v0.py",
        "scripts/ops/durable_closeout_copy_verify_v0.py",
        "scripts/run_scheduler.py",
        "tests/ops/test_run_primary_evidence_retention_hard_gate_v0.py",
    ]

    for surface in required_surfaces:
        assert surface in text


def test_gap2a1_crosslinks_pe2_run_type_primary_evidence_guard_matrix_v0():
    text = HARD_GATE_TESTS.read_text(encoding="utf-8")
    assert "PE2_RUN_TYPE_GUARD_MATRIX" in text
    assert "test_pe2_run_type_primary_evidence_guard_matrix_row_v0" in text
    assert "paper" in text and "supervisor" in text


def test_gap2a1_pe3_docs_backed_run_type_applicability_crosslink_v0():
    section5 = DOC.read_text(encoding="utf-8")
    preflight = PREFLIGHT.read_text(encoding="utf-8")
    for token in (
        "PE3_RUN_TYPE_APPLICABILITY_CONTRACT_V0=true",
        "PRIMARY_EVIDENCE_REQUIRED_FOR_RUN_COMPLETION=true",
        "RUN_COMPLETION_INVALID_WITHOUT_DURABLE_PRIMARY_EVIDENCE=true",
    ):
        assert token in section5
        assert token in preflight
    assert "PE2_RUN_TYPE_GUARD_MATRIX" in preflight
    assert "PE3_RUN_TYPE_MATRIX_DOCS_ANCHOR_V0=true" in section5


def test_gap2a1_pe4_bounded_observation_mandatory_closeout_wiring_crosslink_v0():
    section5 = DOC.read_text(encoding="utf-8")
    preflight = PREFLIGHT.read_text(encoding="utf-8")
    bounded = BOUNDED_REVIEW_TESTS.read_text(encoding="utf-8")
    gap2a1 = section5.split("## §2a.1 Primary Evidence Enforcement Contract v0", 1)[1].split(
        "## Gap 1 Execute Entrypoint Contract v0", 1
    )[0]
    section_2a1 = preflight.split("## 2a.1", 1)[1].split("## 2b.", 1)[0]
    for token in (
        "PE4_BOUNDED_OBSERVATION_MANDATORY_CLOSEOUT_WIRING_GUARD_V0=true",
        "MANDATORY_DURABLE_CLOSEOUT_REQUIRED=true",
    ):
        assert token in gap2a1
        assert token in section_2a1
    assert "DURABLE_PRIMARY_EVIDENCE_MANDATORY_CLOSEOUT_WIRING_V0=true" in section_2a1
    assert "PE4_BOUNDED_CLOSEOUT_LANE_MATRIX" in gap2a1 or "bounded_observation_review" in gap2a1
    assert "PE4_BOUNDED_CLOSEOUT_LANE_MATRIX" in bounded
    assert BOUNDED_REVIEW_TESTS.name in gap2a1


def test_gap2a1_pe5_gap4_output_evidence_dependency_crosslink_v0() -> None:
    section5 = DOC.read_text(encoding="utf-8")
    preflight = PREFLIGHT.read_text(encoding="utf-8")
    gap2a1 = section5.split("## §2a.1 Primary Evidence Enforcement Contract v0", 1)[1].split(
        "## Gap 1 Execute Entrypoint Contract v0", 1
    )[0]
    gap4 = section5.split("## Gap 4 Output/Evidence Paths Contract v0", 1)[1].split(
        "## Gap 6 Dry-Run Proof Criteria Contract v0", 1
    )[0]
    section_2a1 = preflight.split("## 2a.1", 1)[1].split("## 2b.", 1)[0]
    for token in (
        "PE5_GAP4_GAP2A1_DEPENDENCY_GUARD_V0=true",
        "GAP4_OUTPUT_EVIDENCE_DEPENDS_ON_GAP2A1_PRIMARY_EVIDENCE_V0=true",
    ):
        assert token in gap2a1
        assert token in gap4
        assert token in section_2a1
    assert "test_gap4_gap2a1_primary_evidence_dependency_contract_v0.py" in gap2a1
    assert "Gap4 ↔ Gap2a.1 dependency" in gap2a1


def test_gap2a1_pe6_cyber_er_artifact_retention_crosslink_v0() -> None:
    section5 = DOC.read_text(encoding="utf-8")
    preflight = PREFLIGHT.read_text(encoding="utf-8")
    ci_audit = (ROOT / "docs" / "ops" / "CI_AUDIT_KNOWN_ISSUES.md").read_text(encoding="utf-8")
    gap2a1 = section5.split("## §2a.1 Primary Evidence Enforcement Contract v0", 1)[1].split(
        "## Gap 1 Execute Entrypoint Contract v0", 1
    )[0]
    er_index = preflight.split("### Evidence Durable Closeout Retention RC v0", 1)[1].split(
        "## 2b.", 1
    )[0]
    cyber_crosslink = (
        ROOT
        / "tests"
        / "ci"
        / "test_cybersecurity_visibility_repo_static_histogram_artifact_retention_or_evidence_gap_crosslink_v0.py"
    )
    for token in (
        "PE6_CYBER_ER_ARTIFACT_RETENTION_CROSSLINK_V0=true",
        "CYBER_VISIBILITY_ARTIFACTS_RETENTION_LINKED_TO_PRIMARY_EVIDENCE_V0=true",
        "ER_ARTIFACT_RETENTION_LINKED_TO_CYBER_VISIBILITY_V0=true",
    ):
        assert token in gap2a1
        assert token in ci_audit
        assert token in er_index
    assert "Cyber ↔ ER artifact-retention crosslink" in gap2a1
    assert cyber_crosslink.name in gap2a1
    assert cyber_crosslink.is_file()
    assert "INPUT_JSONL_PROVIDED=false" in ci_audit
    assert "defensive/derived/static" in ci_audit.lower()
    collapsed = gap2a1.replace("**", "")
    assert "does not activate enforcement" in collapsed.lower()


def test_gap2a1_primary_evidence_enforcement_contract_is_not_default_on():
    text = DOC.read_text(encoding="utf-8")
    section = text.split("## §2a.1 Primary Evidence Enforcement Contract v0", 1)[1].split(
        "## Gap 1 Execute Entrypoint Contract v0", 1
    )[0]
    lines = {line.strip() for line in section.splitlines()}

    forbidden = [
        "GAP2A1_PRIMARY_EVIDENCE_ENFORCED=true",
        "GAP2A1_ENFORCEMENT_DEFAULT_ON=true",
        "GAP2A1_TIER1_ENFORCEMENT_LIFTED=true",
    ]

    for marker in forbidden:
        assert marker not in lines


def test_gap2a1_tier1_activation_contract_present_and_blocked_v0() -> None:
    section5 = DOC.read_text(encoding="utf-8")
    gap2a1 = section5.split("## §2a.1 Primary Evidence Enforcement Contract v0", 1)[1].split(
        "## Gap 1 Execute Entrypoint Contract v0", 1
    )[0]
    final_lines = section5.split("## Final Machine Lines", 1)[1]

    required = (
        "TIER1_PRIMARY_EVIDENCE_ENFORCEMENT_CONTRACT_V0=true",
        "TIER1_PRIMARY_EVIDENCE_ENFORCEMENT_CONTRACTED=true",
        "TIER1_PRIMARY_EVIDENCE_ENFORCEMENT_CHARTERED=true",
        "GAP2A1_TIER1_ENFORCEMENT_LIFTED=false",
        "GAP2A1_PRIMARY_EVIDENCE_ENFORCED=false",
        "PREFLIGHT_REMAINS_BLOCKED=true",
        "ALL_GAPS_CLOSED=false",
        "READY_FOR_OPERATOR_ARMING=false",
        "TIER1_FAIL_CLOSED_ON_MISSING_PRIMARY_EVIDENCE=true",
        "TIER1_NO_RETROACTIVE_ENFORCEMENT=true",
        "TIER1_NO_LEGACY_EVIDENCE_MIGRATION_REQUIRED=true",
        "TIER1_OPT_IN_FLAG_REQUIRED_PER_ENTRYPOINT=true",
        "SLICE_TIER1_DOCS_TESTS_ONLY=true",
        "EXTERNAL_TIER1_CHARTER_POINTER=",
        "PE2_RUN_TYPE_GUARD_MATRIX",
        "fail-closed",
    )
    for token in required:
        assert token in gap2a1

    assert "TIER1_PRIMARY_EVIDENCE_ENFORCEMENT_CONTRACTED=true" in final_lines
    assert "GAP2A1_TIER1_ENFORCEMENT_LIFTED=true" in final_lines
    assert "GAP2A1_PRIMARY_EVIDENCE_ENFORCED=true" in final_lines
    forbidden = (
        "GAP2A1_ENFORCEMENT_DEFAULT_ON=true",
        "PREFLIGHT_REMAINS_BLOCKED=false",
        "ALL_GAPS_CLOSED=true",
        "READY_FOR_OPERATOR_ARMING=true",
    )
    gap2a1_lines = {line.strip() for line in gap2a1.splitlines()}
    for token in forbidden:
        assert token not in gap2a1_lines
    assert "GAP2A1_PRIMARY_EVIDENCE_ENFORCED=true" not in gap2a1_lines


TIER1_ZERO_DISPATCH_MANIFEST_OBSERVED_FINAL_LINE_REFLECTION_HEADER = (
    "## Tier-1 Governed Zero-Dispatch Manifest Observed Final-Line Reflection v0"
)
TIER1_CANONICAL_TAG_BOUNDED_ENFORCE_OBSERVED_FINAL_LINE_REFLECTION_HEADER = (
    "## Tier-1 Governed Canonical-Tag Bounded Enforce Observed Final-Line Reflection v0"
)
GAP2A1_REPO_LIFT_CLASS4_REFLECTION_HEADER = (
    "## Gap-2a.1 Governed Primary Evidence Repo-Lift CLASS_4 Reflection v0"
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
    ].split(GAP2A1_REPO_LIFT_CLASS4_REFLECTION_HEADER, 1)[0]


def test_gap2a1_tier1_zero_dispatch_manifest_observed_final_line_reflection_v0() -> None:
    section5 = DOC.read_text(encoding="utf-8")
    section = _tier1_zero_dispatch_manifest_observed_final_line_reflection_section(section5)
    final_lines = section5.split("## Final Machine Lines", 1)[1]
    gap2a1 = section5.split("## §2a.1 Primary Evidence Enforcement Contract v0", 1)[1].split(
        "## Gap 1 Execute Entrypoint Contract v0", 1
    )[0]

    for token in (
        "TIER1_PRIMARY_EVIDENCE_ENFORCEMENT_ZERO_DISPATCH_OBSERVED=true",
        "TIER1_PRIMARY_EVIDENCE_MANIFEST_CREATED=true",
        "TIER1_PRIMARY_EVIDENCE_MANIFEST_VERIFY_RC=0",
        "PRIMARY_EVIDENCE_ENFORCED_SCOPE=zero_dispatch_local_only",
        "GAP2A1_TIER1_ENFORCEMENT_LIFTED_REPO=false",
        "SECTION5_GAP2A1_REPO_LIFTED=false",
    ):
        assert token in section

    assert "PRIMARY_EVIDENCE_ENFORCED=true" in final_lines
    assert "GAP2A1_PRIMARY_EVIDENCE_ENFORCED=true" in final_lines
    assert "GAP2A1_TIER1_ENFORCEMENT_LIFTED=true" in final_lines
    gap2a1_lines = {line.strip() for line in gap2a1.splitlines()}
    assert "GAP2A1_PRIMARY_EVIDENCE_ENFORCED=true" not in gap2a1_lines
    assert "PRIMARY_EVIDENCE_ENFORCED=true" not in gap2a1_lines


def test_gap2a1_tier1_canonical_tag_bounded_enforce_observed_final_line_reflection_v0() -> None:
    section5 = DOC.read_text(encoding="utf-8")
    section = _tier1_canonical_tag_bounded_enforce_observed_final_line_reflection_section(section5)
    final_lines = section5.split("## Final Machine Lines", 1)[1]
    gap2a1 = section5.split("## §2a.1 Primary Evidence Enforcement Contract v0", 1)[1].split(
        "## Gap 1 Execute Entrypoint Contract v0", 1
    )[0]

    for token in (
        "TIER1_CANONICAL_TAG_BOUNDED_ENFORCE_OBSERVED=true",
        "TIER1_CANONICAL_TAG_PRIMARY_EVIDENCE_MANIFEST_CREATED=true",
        "TIER1_CANONICAL_TAG_PRIMARY_EVIDENCE_MANIFEST_VERIFY_RC=0",
        "PRIMARY_EVIDENCE_ENFORCED_SCOPE=canonical_tag_local_readonly_preflight_once",
        "OBSERVED_TAG_MATCH_COUNT=5",
        "OBSERVED_DUE_JOB_COUNT=1",
        "OBSERVED_JOBS_DISPATCHED=1",
        "OBSERVED_JOB_STARTED=paper_shadow_247_paper_only_preflight_status_v0",
        "UNEXPECTED_JOB_STARTED=false",
        "GAP2A1_TIER1_ENFORCEMENT_LIFTED_REPO=false",
        "SECTION5_GAP2A1_REPO_LIFTED=false",
    ):
        assert token in section

    assert "TIER1_CANONICAL_TAG_BOUNDED_ENFORCE_OBSERVED=true" in final_lines
    assert (
        "PRIMARY_EVIDENCE_ENFORCED_SCOPE=canonical_tag_local_readonly_preflight_once" in final_lines
    )
    assert "GAP2A1_PRIMARY_EVIDENCE_ENFORCED=true" in final_lines
    assert "GAP2A1_TIER1_ENFORCEMENT_LIFTED=true" in final_lines
    gap2a1_lines = {line.strip() for line in gap2a1.splitlines()}
    assert "GAP2A1_PRIMARY_EVIDENCE_ENFORCED=true" not in gap2a1_lines
    assert "TIER1_CANONICAL_TAG_BOUNDED_ENFORCE_OBSERVED=true" not in gap2a1_lines


def test_gap2a1_eer1_readiness_review_index_crosslink_v0() -> None:
    section5 = DOC.read_text(encoding="utf-8")
    ci_audit = (ROOT / "docs" / "ops" / "CI_AUDIT_KNOWN_ISSUES.md").read_text(encoding="utf-8")
    preflight = PREFLIGHT.read_text(encoding="utf-8")
    gap2a1 = section5.split("## §2a.1 Primary Evidence Enforcement Contract v0", 1)[1].split(
        "## Gap 1 Execute Entrypoint Contract v0", 1
    )[0]
    eer1_preflight = preflight.split(
        "### Evidence Durable Enforcement Readiness Review RC v0 — EER1 crosslink v0", 1
    )[1].split("## 3. Non-authority", 1)[0]
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
        assert token in eer1_preflight
    assert "Evidence Durable Enforcement Readiness Review index (EER1 guard)" in gap2a1
    assert "MANIFEST" in gap2a1 or "manifest" in gap2a1.lower()
    assert "test_gap2a1_primary_evidence_enforcement_contract_v0.py" not in gap2a1
    assert Path(__file__).name in ci_audit or "gap2a1" in ci_audit.lower()
    gap2a1_lines = {line.strip() for line in gap2a1.splitlines()}
    assert "GAP2A1_PRIMARY_EVIDENCE_ENFORCED=true" not in gap2a1_lines
    assert "READY_FOR_OPERATOR_ARMING=true" not in gap2a1_lines
