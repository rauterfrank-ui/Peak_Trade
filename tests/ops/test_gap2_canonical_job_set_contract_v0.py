from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
DOC = ROOT / "docs" / "ops" / "planning" / "SECTION5_PREFLIGHT_GAP_OWNER_MAP_CONTRACT_V0.md"
CI_AUDIT_RECIPROCAL_OWNER = ROOT / "docs" / "ops" / "CI_AUDIT_KNOWN_ISSUES.md"
GAP2_SECTION_HEADER = "## Gap 2 Canonical Job Set Contract v0"
GAP2_CRITERIA_SSOT_REFLECTION_HEADER = (
    "## Gap 2 Criteria-SSOT Repo-Internal Write/Lift Applied Reflection v0"
)
GAP2A1_SECTION_HEADER = "## §2a.1 Primary Evidence Enforcement Contract v0"
GAP2_PARALLEL_MARKERS = (
    "GAP2_CANONICAL_JOB_SET_CONTRACT_V0=true",
    "Gap 2 Canonical Job Set Contract v0",
)
HARDENING_OWNER = ROOT / "tests" / "ops" / "test_scheduler_dry_run_hardening_source_contract_v0.py"
HARDENING_MARKER = "SCHEDULER_DRY_RUN_HARDENING_SOURCE_CONTRACT_V0=true"
JOB_CONFIG_OWNER = (
    ROOT / "tests" / "ops" / "test_paper_shadow_247_runtime_scheduler_job_config_v0.py"
)
_MARKER_TRUE = "=true"


def _gap2_section(text: str) -> str:
    return text.split(GAP2_SECTION_HEADER, 1)[1].split(GAP2_CRITERIA_SSOT_REFLECTION_HEADER, 1)[0]


def test_gap2_canonical_job_set_contract_is_present_and_non_authorizing():
    section = _gap2_section(DOC.read_text(encoding="utf-8"))

    required = [
        "GAP2_CANONICAL_JOB_SET_CONTRACT_V0=true",
        "GAP2_CRITERIA_ONLY=true",
        "GAP2_CANONICAL_JOB_SET_VERIFIED=false",
        "GAP2_JOB_SET_ENABLED=false",
        "GAP2_JOBS_TOML_CHANGED=false",
        "GAP2_SCHEDULER_EXECUTION_AUTHORIZED=false",
        "GAP2_RUNTIME_APPROVED=false",
        "GAP2_JOB_SET_DEFAULT_ON=false",
        "PATH_B_LIFT_DISCUSSION_READY=false",
        "PREFLIGHT_REMAINS_BLOCKED=true",
    ]

    for marker in required:
        assert marker in section


def test_gap2_canonical_job_set_contract_is_criteria_only_not_verified_or_enabled():
    section = _gap2_section(DOC.read_text(encoding="utf-8"))

    required_language = [
        "docs/tests-only criteria contract",
        "prepares future canonical job-set boundary criteria only",
        "`config/scheduler/jobs.toml` is referenced as a boundary surface only",
        "does not modify `config/scheduler/jobs.toml`",
        "does not enable any scheduler job",
        "does not verify or activate a canonical job set",
        "does not execute `scripts/run_scheduler.py`",
        "does not authorize scheduler execution",
        "does not approve runtime execution",
        "criteria-only",
        "not verified",
        "not job-enabled",
        "not scheduler-authorized",
        "not runtime-approved",
    ]

    for phrase in required_language:
        assert phrase in section


def test_gap2_canonical_job_set_contract_reuses_existing_surfaces():
    section = _gap2_section(DOC.read_text(encoding="utf-8"))

    required_surfaces = [
        "scripts/run_scheduler.py",
        "config/scheduler/jobs.toml",
        "test_paper_shadow_247_runtime_scheduler_job_config_v0.py",
        "test_paper_shadow_247_preflight_contract_v0.py",
        "test_scheduler_boundary_hard_block_contract_v0.py",
        "primary_evidence_retention_v0.py",
        "durable_closeout_copy_verify_v0.py",
    ]

    for surface in required_surfaces:
        assert surface in section


def test_gap2_canonical_job_set_contract_references_dependency_chain():
    section = _gap2_section(DOC.read_text(encoding="utf-8"))

    required_chain = [
        "Gap 1 remains the entrypoint boundary",
        "Gap 3 remains the canonical command-text contract",
        "Gap 4 remains the durable output/evidence path contract",
        "Gap 5 remains the stop criteria-only contract",
        "Gap 6 remains the dry-run proof criteria-only contract",
    ]

    for link in required_chain:
        assert link in section


def test_gap2_canonical_job_set_contract_is_not_verified_or_lifted():
    section = _gap2_section(DOC.read_text(encoding="utf-8"))
    lines = {line.strip() for line in section.splitlines()}

    forbidden = [
        "READY_FOR_OPERATOR_ARMING=true",
        "PATH_B_LIFT_DISCUSSION_READY=true",
        "GAP2_CANONICAL_JOB_SET_VERIFIED=true",
        "GAP2_JOB_SET_ENABLED=true",
        "GAP2_JOBS_TOML_CHANGED=true",
        "GAP2_SCHEDULER_EXECUTION_AUTHORIZED=true",
        "GAP2_RUNTIME_APPROVED=true",
        "GAP2_JOB_SET_DEFAULT_ON=true",
    ]

    for marker in forbidden:
        assert marker not in lines


def test_gap2_canonical_job_set_contract_has_no_parallel_doc_surface():
    owner_map = DOC.resolve()
    ci_audit_owner = CI_AUDIT_RECIPROCAL_OWNER.resolve()
    parallel_docs: list[Path] = []

    for path in (ROOT / "docs").rglob("*.md"):
        resolved = path.resolve()
        if resolved == owner_map or resolved == ci_audit_owner:
            continue
        text = path.read_text(encoding="utf-8")
        if any(marker in text for marker in GAP2_PARALLEL_MARKERS):
            parallel_docs.append(path.relative_to(ROOT))

    assert parallel_docs == []


def test_gap2a1_markers_remain_in_section2a1_not_gap2_canonical_job_set():
    text = DOC.read_text(encoding="utf-8")
    gap2_section = _gap2_section(text)
    gap2a1_section = text.split(GAP2A1_SECTION_HEADER, 1)[1].split(
        "## Gap 1 Execute Entrypoint Contract v0", 1
    )[0]

    gap2a1_markers = [
        "GAP2A1_PRIMARY_EVIDENCE_ENFORCEMENT_CONTRACT_V0=true",
        "GAP2A1_PRIMARY_EVIDENCE_ENFORCED=false",
        "GAP2A1_ENFORCEMENT_DEFAULT_ON=false",
        "GAP2A1_ENFORCEMENT_OPT_IN_ONLY=true",
    ]

    for marker in gap2a1_markers:
        assert marker in gap2a1_section
        assert marker not in gap2_section


def test_gap2_owner_crosslinks_scheduler_dry_run_hardening_source_contract_v0():
    assert HARDENING_OWNER.is_file()
    text = HARDENING_OWNER.read_text(encoding="utf-8")
    assert "scripts/run_scheduler.py" in text
    assert "test_gap2_canonical_job_set_contract_v0.py" in text
    assert HARDENING_MARKER in text
    lines = {line.strip() for line in text.splitlines()}
    assert ("GAP2_CANONICAL_JOB_SET_VERIFIED" + _MARKER_TRUE) not in lines


def test_gap2_owner_crosslinks_paper_shadow_runtime_scheduler_job_config_v0():
    section = _gap2_section(DOC.read_text(encoding="utf-8"))
    assert JOB_CONFIG_OWNER.is_file()
    assert "test_paper_shadow_247_runtime_scheduler_job_config_v0.py" in section
    hardening_text = HARDENING_OWNER.read_text(encoding="utf-8")
    assert "test_paper_shadow_247_runtime_scheduler_job_config_v0.py" in hardening_text


def test_gap2_owner_crosslinks_gap6_external_repo_drift_guard_contract_v0():
    drift_guard = ROOT / "tests" / "ops" / "test_gap6_external_repo_drift_guard_contract_v0.py"
    assert drift_guard.is_file()
    text = drift_guard.read_text(encoding="utf-8")
    assert "GAP2_CANONICAL_JOB_SET_VERIFIED=true" in text
    assert "GAP2_JOB_SET_ENABLED=false" in text


def test_gap2_owner_crosslinks_job_set_boundary_drift_guard_contract_v0():
    boundary_guard = (
        ROOT / "tests" / "ops" / "test_gap2_job_set_boundary_drift_guard_contract_v0.py"
    )
    assert boundary_guard.is_file()
    text = boundary_guard.read_text(encoding="utf-8")
    assert "BOUNDED_PATH_B_CANDIDATE_SCOPE" in text
    assert "PAPER_PLUS_BOUNDED_SHADOW_NON_24_7" in text
    assert "GAP2_CANONICAL_JOB_SET_VERIFIED=true" in text
    assert "GAP2_JOB_SET_ENABLED=false" in text
    assert "test_gap2_canonical_job_set_contract_v0.py" in text


def test_gap2_owner_crosslinks_gap2_gap3_command_dependency_contract_v0():
    dependency_guard = ROOT / "tests" / "ops" / "test_gap2_gap3_command_dependency_contract_v0.py"
    assert dependency_guard.is_file()
    text = dependency_guard.read_text(encoding="utf-8")
    assert "CANONICAL_BOUNDED_DRY_RUN_COMMAND" in text
    assert "GAP2_CANONICAL_JOB_SET_VERIFIED=false" in text
    assert "test_gap2_canonical_job_set_contract_v0.py" in text


GAP2_DRY_RUN_OBSERVED_EVIDENCE_HEADER = (
    "## Gap 2 Governed Canonical Job Set Dry-Run Observed Evidence Reflection v0"
)
GAP2_DRY_RUN_OBSERVED_FINAL_LINE_HEADER = (
    "## Gap 2 Governed Canonical Job Set Dry-Run Observed Final-Line Reflection v0"
)
GAP2_VERIFIED_FINAL_LINE_HEADER = (
    "## Gap 2 Governed Canonical Job Set Verified Final-Line Reflection v0"
)
FINAL_MACHINE_LINES_HEADER = "## Final Machine Lines"


def _final_machine_lines(text: str) -> str:
    return text.split(FINAL_MACHINE_LINES_HEADER, 1)[1]


def _gap2_dry_run_observed_evidence_section(text: str) -> str:
    return text.split(GAP2_DRY_RUN_OBSERVED_EVIDENCE_HEADER, 1)[1].split(
        GAP2_DRY_RUN_OBSERVED_FINAL_LINE_HEADER, 1
    )[0]


def _gap2_dry_run_observed_final_line_section(text: str) -> str:
    return text.split(GAP2_DRY_RUN_OBSERVED_FINAL_LINE_HEADER, 1)[1].split(
        GAP2_VERIFIED_FINAL_LINE_HEADER, 1
    )[0]


def _gap2_verified_final_line_section(text: str) -> str:
    return text.split(GAP2_VERIFIED_FINAL_LINE_HEADER, 1)[1].split(
        "## Gap 3 Governed Tier-2 Command Accepted Scoped-Criteria Final-Line Reflection v0", 1
    )[0]


def test_gap2_dry_run_observed_evidence_reflection_non_authorizing_v0() -> None:
    text = DOC.read_text(encoding="utf-8")
    section = _gap2_dry_run_observed_evidence_section(text)
    block = _final_machine_lines(text)

    assert "GAP2_CANONICAL_JOB_SET_DRY_RUN_OBSERVED_GOVERNED_REFLECTION_V0=true" in section
    assert "GAP2_CANONICAL_JOB_SET_VERIFIED=false" in section
    assert "GAP3_EXECUTE_COMMAND_DRY_RUN_RC0_OBSERVED=true" in section
    assert "GAP3_EXECUTE_COMMAND_VERIFIED=false" in section
    assert "does not modify Final Machine Lines" in section
    assert "GAP2_CANONICAL_JOB_SET_DRY_RUN_OBSERVED=true" in block
    assert "GAP2_CANONICAL_JOB_SET_VERIFIED=true" in block
    section_lines = {line.strip() for line in section.splitlines()}
    block_lines = {line.strip() for line in block.splitlines()}
    assert "GAP2_CANONICAL_JOB_SET_VERIFIED=true" not in section_lines


def test_gap2_dry_run_observed_final_line_governed_reflection_v0() -> None:
    text = DOC.read_text(encoding="utf-8")
    section = _gap2_dry_run_observed_final_line_section(text)
    criteria = _gap2_section(text)
    block = _final_machine_lines(text)

    assert (
        "GAP2_CANONICAL_JOB_SET_DRY_RUN_OBSERVED_FINAL_LINE_GOVERNED_REFLECTION_V0=true" in section
    )
    assert "GAP2_CANONICAL_JOB_SET_DRY_RUN_OBSERVED=true" in section
    assert "OBSERVED_NOT_VERIFIED_SEMANTIC_PRESERVED=true" in section
    assert (
        "OPERATOR_GO=GO_PREPARE_SECTION5_GAP2_CANONICAL_JOB_SET_DRY_RUN_OBSERVED_FINAL_LINE_REPO_REFLECTION_DOCS_TESTS_V0"
        in section
    )
    assert "does not set `GAP2_CANONICAL_JOB_SET_VERIFIED=true`" in section
    assert "GAP2_CANONICAL_JOB_SET_VERIFIED=false" in criteria
    assert "GAP2_CANONICAL_JOB_SET_DRY_RUN_OBSERVED=true" in block
    assert "GAP2_ACCEPTED_SCOPED_CRITERIA=true" in block
    assert "GAP2_CANONICAL_JOB_SET_VERIFIED=true" in block
    criteria_lines = {line.strip() for line in criteria.splitlines()}
    block_lines = {line.strip() for line in block.splitlines()}
    assert "GAP2_CANONICAL_JOB_SET_DRY_RUN_OBSERVED=true" not in criteria_lines
    assert "GAP2_CANONICAL_JOB_SET_DRY_RUN_OBSERVED=true" in block_lines
    assert "GAP2_CANONICAL_JOB_SET_VERIFIED=false" in criteria_lines
    assert "GAP2_CANONICAL_JOB_SET_VERIFIED=true" in block_lines


def test_gap2_verified_final_line_governed_reflection_v0() -> None:
    text = DOC.read_text(encoding="utf-8")
    section = _gap2_verified_final_line_section(text)
    criteria = _gap2_section(text)
    block = _final_machine_lines(text)

    assert "GAP2_CANONICAL_JOB_SET_VERIFIED_FINAL_LINE_GOVERNED_REFLECTION_V0=true" in section
    assert "VERIFIED_BAR_TIER=T1_PLUS_T2_BOUNDARY_INVENTORY" in section
    assert "T1_STATIC_READONLY_SUFFICIENT_FOR_VERIFIED=false" in section
    assert "T2_DRY_RUN_FULL_INVENTORY_SUFFICIENT_FOR_VERIFIED=true" in section
    assert "T3_BOUNDED_EXECUTE_REQUIRED_FOR_VERIFIED=false" in section
    assert "VERIFIED_NOT_OBSERVED_SEMANTIC_PRESERVED=true" in section
    assert "TAG_FILTERED_JOBS_IN_PLAN=5" in section
    assert "CANONICAL_JOBS_IN_SCOPE=4" in section
    assert "GAP2_CANONICAL_JOB_SET_DRY_RUN_OBSERVED=true" in section
    assert "does not modify Gap-2 criteria block verification posture" in section
    assert "GAP2_CANONICAL_JOB_SET_VERIFIED=false" in criteria
    assert "GAP2_CANONICAL_JOB_SET_VERIFIED=true" in block
    assert "GAP2_CANONICAL_JOB_SET_DRY_RUN_OBSERVED=true" in block
    assert "GAP2_ACCEPTED_SCOPED_CRITERIA=true" in block
    assert "VERIFIED_BAR_TIER=T1_PLUS_T2_BOUNDARY_INVENTORY" in block
    assert "GAP3_EXECUTE_COMMAND_VERIFIED=true" in block
    criteria_lines = {line.strip() for line in criteria.splitlines()}
    block_lines = {line.strip() for line in block.splitlines()}
    assert "GAP2_CANONICAL_JOB_SET_VERIFIED=false" in criteria_lines
    assert "GAP2_CANONICAL_JOB_SET_VERIFIED=true" in block_lines
    assert "GAP2_JOB_SET_ENABLED=true" not in block_lines
