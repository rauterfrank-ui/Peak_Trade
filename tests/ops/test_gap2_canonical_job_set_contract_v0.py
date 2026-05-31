from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
DOC = ROOT / "docs" / "ops" / "planning" / "SECTION5_PREFLIGHT_GAP_OWNER_MAP_CONTRACT_V0.md"
GAP2_SECTION_HEADER = "## Gap 2 Canonical Job Set Contract v0"
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
    return text.split(GAP2_SECTION_HEADER, 1)[1].split("## Final Machine Lines", 1)[0]


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
    parallel_docs: list[Path] = []

    for path in (ROOT / "docs").rglob("*.md"):
        if path.resolve() == owner_map:
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
    assert "GAP2_CANONICAL_JOB_SET_VERIFIED=false" in text
    assert "GAP2_JOB_SET_ENABLED=false" in text


def test_gap2_owner_crosslinks_job_set_boundary_drift_guard_contract_v0():
    boundary_guard = (
        ROOT / "tests" / "ops" / "test_gap2_job_set_boundary_drift_guard_contract_v0.py"
    )
    assert boundary_guard.is_file()
    text = boundary_guard.read_text(encoding="utf-8")
    assert "BOUNDED_PATH_B_CANDIDATE_SCOPE" in text
    assert "PAPER_PLUS_BOUNDED_SHADOW_NON_24_7" in text
    assert "GAP2_CANONICAL_JOB_SET_VERIFIED=false" in text
    assert "GAP2_JOB_SET_ENABLED=false" in text
    assert "test_gap2_canonical_job_set_contract_v0.py" in text
