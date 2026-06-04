"""Static contract for Gap-2 bounded job-set boundary drift guard v0.

Reads repo markdown/TOML/source only. Never executes scheduler/runtime, never reads
external archive paths as pass/fail SSOT, and never treats bounded Path-B inventory as
canonical job-set verification or enablement.
"""

from __future__ import annotations

from pathlib import Path

try:
    import tomllib
except ImportError:
    import tomli as tomllib  # type: ignore[no-redef,import-not-found]

ROOT = Path(__file__).resolve().parents[2]
SECTION5_DOC = (
    ROOT / "docs" / "ops" / "planning" / "SECTION5_PREFLIGHT_GAP_OWNER_MAP_CONTRACT_V0.md"
)
PREFLIGHT_TOML = ROOT / "config" / "ops" / "paper_shadow_247_preflight.toml"
JOBS_TOML = ROOT / "config" / "scheduler" / "jobs.toml"
PREFLIGHT_REPORTER = ROOT / "scripts" / "ops" / "report_paper_shadow_247_preflight_status.py"
GAP2_TESTS = ROOT / "tests" / "ops" / "test_gap2_canonical_job_set_contract_v0.py"
JOB_CONFIG_TESTS = (
    ROOT / "tests" / "ops" / "test_paper_shadow_247_runtime_scheduler_job_config_v0.py"
)
HARDENING_OWNER = ROOT / "tests" / "ops" / "test_scheduler_dry_run_hardening_source_contract_v0.py"
FINAL_MACHINE_LINES_HEADER = "## Final Machine Lines"
GAP2_SECTION_HEADER = "## Gap 2 Canonical Job Set Contract v0"
_MARKER_TRUE = "=true"

BOUNDED_PATH_B_CANDIDATE_SCOPE = "PAPER_PLUS_BOUNDED_SHADOW_NON_24_7"
BOUNDED_PAPER_JOBS = (
    "paper_shadow_247_paper_only_preflight_status_v0",
    "paper_shadow_247_paper_only_runtime_min_v0",
    "paper_shadow_247_paper_only_runtime_high_vol_no_trade_v0",
)
BOUNDED_SHADOW_JOB = "p7_shadow_high_vol_no_trade_runner_manual_v0"
EXCLUDED_PLACEHOLDER = "shadow_247_futures_prestart_evidence_drycheck_placeholder_v0"
PREFLIGHT_STATUS_JOB = "paper_shadow_247_paper_only_preflight_status_v0"
BOUNDED_RUNTIME_PAPER_JOBS = (
    "paper_shadow_247_paper_only_runtime_min_v0",
    "paper_shadow_247_paper_only_runtime_high_vol_no_trade_v0",
)

BOUNDARY_REQUIRED_FINAL_LINES = (
    "PREFLIGHT_REMAINS_BLOCKED=true",
    "READY_FOR_OPERATOR_ARMING=false",
    "PATH_B_LIFT_DISCUSSION_READY=false",
    "ALL_GAPS_CLOSED=false",
    "GAP2_CANONICAL_JOB_SET_VERIFIED=false",
    "GAP2_ACCEPTED_SCOPED_CRITERIA=true",
    "GAP2_CANONICAL_JOB_SET_DRY_RUN_OBSERVED=true",
    "GAP2_JOB_SET_ENABLED=false",
    "GAP2_JOBS_TOML_CHANGED=false",
    "GAP6_DRY_RUN_PROOF_ACCEPTED=true",
)

BOUNDARY_FORBIDDEN_REPO_TOKENS = (
    "GAP2_CANONICAL_JOB_SET_VERIFIED=true",
    "GAP2_JOB_SET_ENABLED=true",
    "GAP2_JOBS_TOML_CHANGED=true",
    "GAP3_EXECUTE_COMMAND_VERIFIED=true",
    "SHADOW_24_7_AUTHORIZED=true",
    "PATH_B_LIFT_DISCUSSION_READY=true",
    "ALL_GAPS_CLOSED=true",
    "READY_FOR_OPERATOR_ARMING=true",
    "PREFLIGHT_REMAINS_BLOCKED=false",
)


def _final_machine_lines(text: str) -> str:
    return text.split(FINAL_MACHINE_LINES_HEADER, 1)[1]


def _gap2_section(text: str) -> str:
    return text.split(GAP2_SECTION_HEADER, 1)[1].split(FINAL_MACHINE_LINES_HEADER, 1)[0]


def _section5_text() -> str:
    return SECTION5_DOC.read_text(encoding="utf-8")


def _preflight_payload() -> dict:
    return tomllib.loads(PREFLIGHT_TOML.read_text(encoding="utf-8"))


def _jobs() -> list[dict]:
    payload = tomllib.loads(JOBS_TOML.read_text(encoding="utf-8"))
    return payload.get("job", [])


def _job_by_name(name: str) -> dict:
    return next(job for job in _jobs() if job.get("name") == name)


def test_gap2_job_set_boundary_module_scope_constant_v0() -> None:
    assert BOUNDED_PATH_B_CANDIDATE_SCOPE == "PAPER_PLUS_BOUNDED_SHADOW_NON_24_7"
    assert EXCLUDED_PLACEHOLDER == "shadow_247_futures_prestart_evidence_drycheck_placeholder_v0"


def test_gap2_job_set_boundary_final_machine_lines_remain_blocked_v0() -> None:
    block = _final_machine_lines(_section5_text())
    for marker in BOUNDARY_REQUIRED_FINAL_LINES:
        assert marker in block


def test_gap2_job_set_boundary_forbids_lift_and_verified_tokens_v0() -> None:
    block = _final_machine_lines(_section5_text())
    lines = {line.strip() for line in block.splitlines()}
    for token in BOUNDARY_FORBIDDEN_REPO_TOKENS:
        assert token not in lines


def test_gap2_job_set_boundary_gap2_section_remains_criteria_only_v0() -> None:
    section = _gap2_section(_section5_text())
    assert "GAP2_CRITERIA_ONLY=true" in section
    assert "does not verify or activate a canonical job set" in section
    assert "does not enable any scheduler job" in section
    lines = {line.strip() for line in section.splitlines()}
    assert "GAP2_CANONICAL_JOB_SET_VERIFIED=true" not in lines
    assert "GAP2_JOB_SET_ENABLED=true" not in lines


def test_gap2_job_set_boundary_preflight_toml_bounded_inventory_only_v0() -> None:
    payload = _preflight_payload()
    paper_jobs = payload["paper_jobs"]
    shadow_jobs = payload["shadow_jobs"]

    assert set(paper_jobs) == set(BOUNDED_PAPER_JOBS)
    assert shadow_jobs == [BOUNDED_SHADOW_JOB]

    for key in (
        "activation_authorized",
        "daemon_activation_authorized",
        "scheduler_execution_authorized",
        "paper_runtime_authorized",
        "shadow_runtime_authorized",
    ):
        assert payload[key] is False, key


def test_gap2_job_set_boundary_excluded_placeholder_not_in_preflight_lists_v0() -> None:
    payload = _preflight_payload()
    assert EXCLUDED_PLACEHOLDER not in payload["paper_jobs"]
    assert EXCLUDED_PLACEHOLDER not in payload["shadow_jobs"]


def test_gap2_job_set_boundary_jobs_toml_runtime_disabled_reporter_readonly_v0() -> None:
    reporter = _job_by_name(PREFLIGHT_STATUS_JOB)
    assert reporter["enabled"] is True
    assert reporter["args"]["script"] == "scripts/ops/report_paper_shadow_247_preflight_status.py"
    assert "readonly" in reporter.get("tags", [])

    for name in BOUNDED_RUNTIME_PAPER_JOBS:
        job = _job_by_name(name)
        assert job["enabled"] is False
        assert "disabled_by_default" in job.get("tags", [])

    shadow = _job_by_name(BOUNDED_SHADOW_JOB)
    assert shadow["enabled"] is False
    assert shadow["args"]["dry_run"] is True


def test_gap2_job_set_boundary_placeholder_excluded_from_bounded_candidate_v0() -> None:
    payload = _preflight_payload()
    placeholder_job = _job_by_name(EXCLUDED_PLACEHOLDER)
    assert EXCLUDED_PLACEHOLDER not in payload["paper_jobs"]
    assert EXCLUDED_PLACEHOLDER not in payload["shadow_jobs"]
    assert placeholder_job["enabled"] is False
    assert placeholder_job.get("shadow_247_futures_placeholder") is True


def test_gap2_job_set_boundary_shadow_24_7_not_authorized_in_repo_ssot_v0() -> None:
    text = _section5_text()
    assert "SHADOW_24_7_AUTHORIZED=true" not in text
    block = _final_machine_lines(text)
    assert "SHADOW_24_7_AUTHORIZED=true" not in block


def test_gap2_job_set_boundary_gap6_tokens_untouched_by_gap2_slice_v0() -> None:
    block = _final_machine_lines(_section5_text())
    assert "GAP6_DRY_RUN_PROOF_ACCEPTED=true" in block
    assert "GAP6_DRY_RUN_RC0_OBSERVED=true" in block
    assert "GAP6_DRY_RUN_PROOF_VERIFIED=false" in block


def test_gap2_job_set_boundary_criteria_complete_does_not_close_gaps_v0() -> None:
    text = _section5_text()
    assert "SECTION5_OWNER_MAP_CONTRACT_V0_COMPLETE=true" in text
    assert "ALL_GAPS_CLOSED=false" in text
    assert "GAP2_CRITERIA_ONLY=true" in text


def test_gap2_job_set_boundary_evidence_not_approval_language_v0() -> None:
    section = _gap2_section(_section5_text())
    assert "criteria-only" in section
    assert "not verified" in section
    assert "not job-enabled" in section


def test_gap2_job_set_boundary_config_surfaces_exist_read_only_v0() -> None:
    assert JOBS_TOML.is_file()
    assert PREFLIGHT_TOML.is_file()
    assert PREFLIGHT_REPORTER.is_file()
    reporter = _job_by_name(PREFLIGHT_STATUS_JOB)
    assert reporter["args"]["script"] == "scripts/ops/report_paper_shadow_247_preflight_status.py"


def test_gap2_job_set_boundary_owner_crosslinks_gap2_canonical_contract_v0() -> None:
    assert GAP2_TESTS.is_file()
    text = GAP2_TESTS.read_text(encoding="utf-8")
    assert "test_gap2_job_set_boundary_drift_guard_contract_v0.py" in text


def test_gap2_job_set_boundary_owner_crosslinks_job_config_contract_v0() -> None:
    assert JOB_CONFIG_TESTS.is_file()
    text = JOB_CONFIG_TESTS.read_text(encoding="utf-8")
    assert "test_gap2_job_set_boundary_drift_guard_contract_v0.py" in text


def test_gap2_job_set_boundary_owner_crosslinks_hardening_source_contract_v0() -> None:
    assert HARDENING_OWNER.is_file()
    text = HARDENING_OWNER.read_text(encoding="utf-8")
    assert "test_gap2_job_set_boundary_drift_guard_contract_v0.py" in text


def test_gap2_job_set_boundary_owner_crosslinks_gap2_gap3_command_dependency_v0() -> None:
    dependency_guard = ROOT / "tests" / "ops" / "test_gap2_gap3_command_dependency_contract_v0.py"
    assert dependency_guard.is_file()
    text = dependency_guard.read_text(encoding="utf-8")
    assert BOUNDED_PATH_B_CANDIDATE_SCOPE in text
    assert "GAP3_EXECUTE_COMMAND_VERIFIED=false" in text
    assert "test_gap2_job_set_boundary_drift_guard_contract_v0.py" in text
