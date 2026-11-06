"""Contract characterization for Paper/Shadow 24/7 preflight v0 (read-only, no runtime)."""

from __future__ import annotations

import json
import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
CONTRACT = REPO_ROOT / "docs" / "ops" / "runbooks" / "PAPER_SHADOW_247_PREFLIGHT_CONTRACT_V0.md"
CHARTER = REPO_ROOT / "docs" / "ops" / "runbooks" / "SHADOW_247_GOVERNANCE_CHARTER_V0.md"
CHARTER_NAME = "SHADOW_247_GOVERNANCE_CHARTER_V0.md"
SCHEDULER_DAEMON = REPO_ROOT / "docs" / "SCHEDULER_DAEMON.md"
JOBS_TOML = REPO_ROOT / "config" / "scheduler" / "jobs.toml"


def _read_contract() -> str:
    return CONTRACT.read_text(encoding="utf-8")


def _extract_json_example(markdown: str) -> dict[str, object]:
    match = re.search(r"```json\n(.*?)\n```", markdown, re.DOTALL)
    assert match is not None
    return json.loads(match.group(1))


def test_paper_shadow_247_contract_links_governance_charter_without_overriding_blocked_v0() -> None:
    text = _read_contract()
    assert CHARTER.is_file()
    assert f"]({CHARTER_NAME})" in text
    assert "Shadow-247 governance charter" in text
    assert "**STOP_IDLE**" in text
    assert "**does not** override this document" in text
    assert "**BLOCKED** status" in text
    assert "governance-only" in text
    assert "runtime approval" in text


def test_paper_shadow_247_contract_links_charter_24h_evidence_semantics_without_changing_blocked_v0() -> (
    None
):
    """Regression anchor for PR #3562 — preflight navigation to charter 24h tier only."""
    text = _read_contract()
    assert CHARTER.is_file()
    assert "24h bounded Shadow dry-run candidate" in text
    assert CHARTER_NAME in text
    assert "Status and scope" in text
    assert "**documentary**" in text
    assert "**non-authorizing**" in text
    assert "**does not** change this contract" in text
    assert "**BLOCKED** status" in text
    assert "assists navigation only" in text


def test_paper_shadow_247_contract_is_blocked_and_non_authorizing() -> None:
    text = _read_contract()

    assert "Current status: **BLOCKED**." in text
    assert "**STOP — do not activate Paper/Shadow 24/7.**" in text
    assert "are **not** trading authority" in text
    assert "must not be interpreted as daemon activation" in text
    assert "does **not** start a daemon" in text


def test_paper_shadow_247_contract_defines_dry_run_only_command() -> None:
    text = _read_contract()

    expected_cmd = (
        "python3 scripts/run_scheduler.py --config config/scheduler/jobs.toml "
        "--dry-run --once --verbose"
    )
    assert expected_cmd in text
    assert "planning and diagnostics" in text
    assert "must not be interpreted as daemon activation" in text


def test_paper_shadow_247_contract_example_report_is_blocked_json() -> None:
    payload = _extract_json_example(_read_contract())

    assert payload["schema_version"] == "paper_shadow_247_preflight_contract.v0"
    assert payload["status"] == "BLOCKED"
    assert payload["canonical_candidate_jobs"] == []
    assert payload["candidate_commands"] == []
    assert payload["output_paths"] == []
    assert payload["stop_commands"] == []
    assert payload["emergency_stop_commands"] == []
    assert payload["activation_authorized"] is False
    rf = payload["risk_flags"]
    assert rf == {
        "live": False,
        "testnet": False,
        "broker": False,
        "exchange": False,
        "orders": False,
    }
    reasons = payload["status_reasons"]
    assert isinstance(reasons, list)
    assert "paper_shadow_247_owner_entrypoint_missing" in reasons
    assert "paper_shadow_247_canonical_job_set_missing" in reasons


def test_paper_shadow_247_contract_includes_post_pr3376_readiness_closeout() -> None:
    text = _read_contract()

    assert "## Post-PR3376 operator readiness closeout v0" in text
    assert "ops-paper-shadow-247-readiness" in text
    assert "#3371" in text and "#3376" in text
    assert "does **not** authorize scheduler execution" in text
    assert "scripts/ops/report_paper_shadow_247_preflight_status.py" in text
    assert "scripts/ops/snapshot_operator_stop_signals.py" in text


def test_scheduler_daemon_links_to_paper_shadow_247_contract() -> None:
    scheduler_text = SCHEDULER_DAEMON.read_text(encoding="utf-8")
    assert "PAPER_SHADOW_247_PREFLIGHT_CONTRACT_V0.md" in scheduler_text


def test_scheduler_config_exposes_read_only_paper_shadow_247_preflight_job_only() -> None:
    jobs_text = JOBS_TOML.read_text(encoding="utf-8")

    assert "paper_shadow_247_paper_only_preflight_status_v0" in jobs_text
    assert "report_paper_shadow_247_preflight_status.py" in jobs_text
    assert "paper_only = true" in jobs_text.lower()
    assert "dry_run_visible = true" in jobs_text.lower()

    lowered = jobs_text.lower()
    assert "run_shadow_paper_session" not in lowered


def _section_2a1(text: str) -> str:
    return text.split("## 2a.1", 1)[1].split("## 2b.", 1)[0]


def _section_2a(text: str) -> str:
    return text.split("## 2a. Primary evidence retention invariant v0", 1)[1].split("## 2a.1", 1)[0]


def test_preflight_section_2a_hold_binding_profiles_reciprocal_crosslink_v1() -> None:
    text = _read_contract()
    section = _section_2a(text)
    assert "gap4_req_a_paper_bounded_v0" in section
    assert "paper_l2_120min_hold_binding_v0" in section
    assert "§10a" in section
    assert "§10b" in section
    assert "7200" in section
    assert "300–900s" in section or "300-900s" in section
    assert "test_gap4_req_a_300s_hold_binding_profile_contract_v0.py" in section
    assert "test_paper_l2_120min_hold_binding_profile_contract_v0.py" in section
    collapsed = section.replace("**", "")
    assert "does not authorize execute or preflight lift" in collapsed.lower()


def test_preflight_section_2a1_pe3_run_type_applicability_contract_v0() -> None:
    text = _read_contract()
    section = _section_2a1(text)
    for token in (
        "PE3_RUN_TYPE_APPLICABILITY_CONTRACT_V0=true",
        "PE3_RUN_TYPE_MATRIX_DOCS_ANCHOR_V0=true",
        "SLICE_PE2_COMPLETE=true",
        "SLICE_PE3_DOCS_TESTS_ONLY=true",
        "PRIMARY_EVIDENCE_REQUIRED_FOR_RUN_COMPLETION=true",
        "RUN_COMPLETION_INVALID_WITHOUT_DURABLE_PRIMARY_EVIDENCE=true",
        "PREFLIGHT_REMAINS_BLOCKED=true",
        "READY_FOR_OPERATOR_ARMING=false",
        "GAP2A1_PRIMARY_EVIDENCE_ENFORCED=false",
    ):
        assert token in section
    for run_type in (
        "Paper",
        "Shadow",
        "Testnet",
        "Live/Canary",
        "bounded trial",
        "Scheduler",
        "Supervisor",
    ):
        assert run_type in section
    assert "PE2_RUN_TYPE_GUARD_MATRIX" in section
    assert "/tmp`-only is insufficient" in section or "`/tmp`-only is insufficient" in section
    assert "MANIFEST.sha256" in section
    collapsed = section.replace("**", "")
    assert "Does not activate enforcement" in collapsed
    assert "READY_FOR_OPERATOR_ARMING=false" in section
    assert "set `READY_FOR_OPERATOR_ARMING=true`." in section
    assert "does not** set `READY_FOR_OPERATOR_ARMING=true`" in section


def test_preflight_section_2a1_run_completion_requires_durable_primary_evidence_v0() -> None:
    section = _section_2a1(_read_contract())
    assert "RUN_INCOMPLETE_WITHOUT_PRIMARY_EVIDENCE=true" in section
    assert "TMP_ONLY_EVIDENCE_INVALID=true" in section
    assert "MANIFEST_VERIFY_REQUIRED=true" in section
    assert "FUTURE_RUNS_REQUIRE_DURABLE_ARCHIVE_ROOT=true" in section
    assert "incomplete and invalid" in section


def _section_2b2_eer1(text: str) -> str:
    return text.split(
        "### Evidence Durable Enforcement Readiness Review RC v0 — EER1 crosslink v0", 1
    )[1].split("## 3. Non-authority", 1)[0]


def test_preflight_section_2b2_eer1_readiness_review_index_v0() -> None:
    text = _read_contract()
    ci_audit = (REPO_ROOT / "docs" / "ops" / "CI_AUDIT_KNOWN_ISSUES.md").read_text(encoding="utf-8")
    section = _section_2b2_eer1(text)
    for token in (
        "EVIDENCE_DURABLE_ENFORCEMENT_READINESS_REVIEW_RC_V0_STARTED=true",
        "EER1_READINESS_REVIEW_INDEX_COMPLETE=true",
        "PRIMARY_EVIDENCE_RUN_COMPLETION_CONTRACT_RC_V0_STATUS=CORE_COMPLETE_AFTER_PE6",
        "CYBERSECURITY_DEFENSIVE_VISIBILITY_CV3_PLUS_RC_V0_STATUS=CORE_COMPLETE_AFTER_CV3",
        "CLOSEOUT_ENFORCEMENT_PLANNING_ONLY=true",
        "CLOSEOUT_ENFORCEMENT_ACTIVATED=false",
        "GAP2A1_PRIMARY_EVIDENCE_ENFORCED=false",
        "RETENTION_ENFORCEMENT_ACTIVATED=false",
        "ENFORCEMENT_ACTIVATED=false",
        "MANIFEST_VERIFY_REQUIRED=true",
        "PREFLIGHT_REMAINS_BLOCKED=true",
        "READY_FOR_OPERATOR_ARMING=false",
    ):
        assert token in section
    for token in (
        "EVIDENCE_DURABLE_ENFORCEMENT_READINESS_REVIEW_RC_V0_STARTED=true",
        "EER1_READINESS_REVIEW_INDEX_COMPLETE=true",
        "PRIMARY_EVIDENCE_RUN_COMPLETION_CONTRACT_RC_V0_STATUS=CORE_COMPLETE_AFTER_PE6",
        "CYBERSECURITY_DEFENSIVE_VISIBILITY_CV3_PLUS_RC_V0_STATUS=CORE_COMPLETE_AFTER_CV3",
        "GAP2A1_PRIMARY_EVIDENCE_ENFORCED=false",
        "ENFORCEMENT_ACTIVATED=false",
        "PREFLIGHT_REMAINS_BLOCKED=true",
        "READY_FOR_OPERATOR_ARMING=false",
    ):
        assert token in ci_audit
    assert "SECTION5_PREFLIGHT_GAP_OWNER_MAP_CONTRACT_V0.md" in text or "§2a.1" in section
    assert "test_paper_shadow_247_preflight_contract_v0.py" in section
    assert "Evidence Durable Enforcement Readiness Review RC v0" in ci_audit
    collapsed = section.replace("**", "")
    assert "does not activate enforcement" in collapsed.lower()
    section_lines = {line.strip() for line in section.splitlines()}
    assert "GAP2A1_PRIMARY_EVIDENCE_ENFORCED=true" not in section_lines
    assert "READY_FOR_OPERATOR_ARMING=true" not in section_lines


def _section_2b3(text: str | None = None) -> str:
    body = text if text is not None else _read_contract()
    return body.split("## 2b.3 Durable closeout adapter validation operator SSOT v0", 1)[1].split(
        "## 2c. Preflight Gate Repo-Internal Write/Lift Applied Reflection v0", 1
    )[0]


def test_preflight_section_2b3_durable_closeout_adapter_validation_ssot_v0() -> None:
    text = _read_contract()
    assert "## 2b.3 Durable closeout adapter validation operator SSOT v0" in text
    section = _section_2b3(text)
    for token in (
        "PREFLIGHT_DURABLE_CLOSEOUT_ADAPTER_VALIDATION_SSOT_V0=true",
        "PREFLIGHT_DURABLE_CLOSEOUT_ADAPTER_VALIDATION_DOCS_TESTS_ONLY=true",
        "DURABLE_CLOSEOUT_IDENTICAL_SOURCE_DEST_REJECTED=true",
        "DURABLE_CLOSEOUT_ADAPTER_PRE_INVOKE_VALIDATION=true",
        "BOUNDED_ADAPTER_OBSERVATION_CLOSEOUT_DECOUPLED=true",
        "DURABLE_CLOSEOUT_FORCE_REQUIRES_DISTINCT_PATHS=true",
        "BLOCKER_HINT_MACHINE_READABLE=true",
        "AUTHORITATIVE_STATUS_HIERARCHY_V0=true",
        "HISTORICAL_PRE_RECOVERY_FAIL_NOT_CURRENT_STATUS=true",
        "PREFLIGHT_REMAINS_BLOCKED=true",
        "PRE_FLIGHT_BLOCKED_LIFTED=false",
    ):
        assert token in section
    assert "#4127" in section
    assert "#4128" in section
    assert "durable_closeout_copy_verify_v0.py" in section
    assert "run_paper_only_bounded_observation_adapter_v0.py" in section
    assert "run_scheduler.py" in section
    assert "pack_online_readiness_supervisor_evidence_v0.py" in section
    assert "validate_durable_closeout_invoke_paths" in section
    assert "SCHEDULER_SUPERVISOR_DURABLE_CLOSEOUT_PRE_INVOKE_VALIDATION=true" in section
    assert "test_durable_closeout_copy_verify_v0.py" in section
    assert "test_bounded_adapter_invoke_durable_closeout_v0.py" in section
    assert "test_scheduler_durable_closeout_hook_pass_through_v0.py" in section
    assert "test_supervisor_pack_durable_closeout_hook_pass_through_v0.py" in section
    assert "POST_INVOKE_RESULT_CLASSIFICATION_MATRIX_GUARD_V0=true" in section
    assert "ALL_FIVE_ATTACH_HOOK_SURFACES_RESULT_CLASSIFICATION_COVERED=true" in section
    assert "VALIDATE_CLI_ARGS_CROSS_SURFACE_PARITY_MATRIX_GUARD_V0=true" in section
    assert "ALL_BOUNDED_ADAPTER_ATTACH_SURFACES_CLI_ARGS_MATRIX_COVERED=true" in section
    assert "DEST_MANIFEST_VERIFY_RC_CROSS_SURFACE_PARITY_MATRIX_GUARD_V0=true" in section
    assert "ALL_FIVE_ATTACH_HOOK_SURFACES_DEST_MANIFEST_VERIFY_RC_COVERED=true" in section
    assert "HOOK_ATTACH_AFTER_MANIFEST_VERIFY_RC_ZERO_ONLY_GUARDED=true" in section


def test_preflight_section_2b3_durable_closeout_force_and_blocker_hints_v0() -> None:
    section = _section_2b3()
    assert "--durable-closeout-force" in section
    assert "BLOCKER_HINT" in section
    assert "durable_closeout_identical_source_dest" in section
    assert "durable_closeout_dest_non_empty_without_force" in section
    assert "BOUNDED_ADAPTER_DURABLE_CLOSEOUT_BLOCKER_HINT" in section
    assert "SCHEDULER_DURABLE_CLOSEOUT_BLOCKER_HINT" in section
    assert "SUPERVISOR_PACK_DURABLE_CLOSEOUT_BLOCKER_HINT" in section
    assert "snapshot source" in section.lower() or "snapshot-source" in section.lower()


def test_preflight_section_2b3_authoritative_hierarchy_and_non_authorizing_v0() -> None:
    text = _read_contract()
    section = _section_2b3(text)
    assert "MACHINE_SUMMARY.env" in section
    assert "MANIFEST_VERIFY_RC=0" in section
    assert "RUN_CLOSEOUT.md" in section
    assert "RESULT_SUMMARY.env" in section
    assert "historical" in section.lower() or "pre-recovery" in section.lower()
    assert "does **not** lift Preflight **BLOCKED**" in section or (
        "Preflight remains **BLOCKED**" in section
    )
    collapsed = section.replace("**", "")
    assert "Evidence ≠ approval" in collapsed or "Evidence != approval" in collapsed
    assert text.index("## 2b.2 Closeout Enforcement Planning Contract v0") < text.index(
        "## 2b.3 Durable closeout adapter validation operator SSOT v0"
    )


def test_preflight_section_2b3_adjacent_section_ordering_v0() -> None:
    text = _read_contract()
    assert text.index("## 2b.2 Closeout Enforcement Planning Contract v0") < text.index(
        "## 2b.3 Durable closeout adapter validation operator SSOT v0"
    )
    assert text.index("## 2b.3 Durable closeout adapter validation operator SSOT v0") < text.index(
        "## 2c. Preflight Gate Repo-Internal Write/Lift Applied Reflection v0"
    )


def test_preflight_section_2b3_crosslinks_taxonomy_6a08_1_v0() -> None:
    section = _section_2b3()
    assert "RUNTIME_LANE_TAXONOMY_AUTHORITY_LEVELS_CONTRACT_V0.md" in section
    assert "§6a.0.8.1" in section
    assert "non-authorizing" in section.lower()
