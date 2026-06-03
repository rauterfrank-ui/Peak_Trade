"""Static contract tests for primary evidence retention invariant v0 (offline, no runtime)."""

from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
CANONICAL_OWNER = (
    REPO_ROOT / "docs" / "ops" / "runbooks" / "PAPER_SHADOW_247_PREFLIGHT_CONTRACT_V0.md"
)
PAPER_ADAPTER = REPO_ROOT / "scripts" / "ops" / "run_paper_only_bounded_observation_adapter_v0.py"
SHADOW_ADAPTER = REPO_ROOT / "scripts" / "ops" / "run_shadow_bounded_observation_adapter_v0.py"
TESTNET_ADAPTER = REPO_ROOT / "scripts" / "ops" / "run_testnet_bounded_observation_adapter_v0.py"
SHARED_HELPER = REPO_ROOT / "scripts" / "ops" / "primary_evidence_retention_v0.py"
P79_SHELL = REPO_ROOT / "scripts" / "ops" / "p79_supervisor_health_gate_v1.sh"
P79_VERIFY = REPO_ROOT / "scripts" / "ops" / "p79_supervisor_evidence_manifest_verify_v0.py"
P101_SCRIPT = REPO_ROOT / "scripts" / "ops" / "p101_stop_playbook_v1.sh"
P93_SCRIPT = REPO_ROOT / "scripts" / "ops" / "p93_online_readiness_status_dashboard_v1.sh"
P91_SCRIPT = REPO_ROOT / "scripts" / "ops" / "p91_audit_snapshot_runner_v1.sh"
PACK_SCRIPT = REPO_ROOT / "scripts" / "ops" / "pack_online_readiness_supervisor_evidence_v0.py"
SHADOW_REVIEW = REPO_ROOT / "scripts" / "ops" / "review_shadow_bounded_observation_evidence_v0.py"
TESTNET_REVIEW = REPO_ROOT / "scripts" / "ops" / "review_testnet_bounded_observation_evidence_v0.py"
HARD_GATE_CONTRACT_TESTS = (
    REPO_ROOT / "tests" / "ops" / "test_run_primary_evidence_retention_hard_gate_v0.py"
)
BOUNDED_REVIEW_CONTRACT_TESTS = (
    REPO_ROOT
    / "tests"
    / "ops"
    / "test_bounded_observation_review_durable_primary_evidence_contract_v0.py"
)
SCHEDULER_COMPLETION_CONTRACT_TESTS = (
    REPO_ROOT / "tests" / "ops" / "test_scheduler_completion_primary_evidence_closeout_v0.py"
)
RUN_SCHEDULER = REPO_ROOT / "scripts" / "run_scheduler.py"
MANDATORY_CLOSEOUT_WIRING_TOKEN = "DURABLE_PRIMARY_EVIDENCE_MANDATORY_CLOSEOUT_WIRING_V0=true"
ARTIFACT_RETENTION_CROSSLINK_TESTS = (
    REPO_ROOT
    / "tests"
    / "ci"
    / "test_cybersecurity_visibility_repo_static_histogram_artifact_retention_or_evidence_gap_crosslink_v0.py"
)
RECIPROCAL_CROSSLINK_MARKER = "CYBERSECURITY_VISIBILITY_ARTIFACT_RETENTION_DURABLE_PRIMARY_EVIDENCE_RECIPROCAL_CROSSLINK_V0=true"
PE6_CYBER_ER_CROSSLINK_MARKERS: tuple[str, ...] = (
    "PE6_CYBER_ER_ARTIFACT_RETENTION_CROSSLINK_V0=true",
    "CYBER_VISIBILITY_ARTIFACTS_RETENTION_LINKED_TO_PRIMARY_EVIDENCE_V0=true",
    "ER_ARTIFACT_RETENTION_LINKED_TO_CYBER_VISIBILITY_V0=true",
)
_MARKER_TRUE = "=true"
ER_RELEASE_RC_INDEX_HEADING = "### Evidence Durable Closeout Retention RC v0 — index v0"
ER_RELEASE_RC_BLOCK_ANCHOR = "EVIDENCE_DURABLE_CLOSEOUT_RETENTION_RC_V0=true"
ER_PLANNING_BUNDLE_PATH = (
    "/Users/frnkhrz/Documents/Peak_Trade_runtime_evidence_archive_20260520T161443Z/"
    "planning/evidence_durable_closeout_retention_rc_v0_planning_20260602T180921Z/"
)
MANDATORY_CLOSEOUT_CONTRACT_TESTS = (
    REPO_ROOT / "tests" / "ops" / "test_mandatory_durable_closeout_contract_v0.py"
)
DURABLE_CLOSEOUT_VERIFY_TESTS = (
    REPO_ROOT / "tests" / "ops" / "test_durable_closeout_copy_verify_v0.py"
)
THIS_MODULE = Path(__file__).name

ER_RELEASE_RC_EXPECTED: dict[str, str] = {
    "EVIDENCE_DURABLE_CLOSEOUT_RETENTION_RC_V0": "true",
    "SLICE_ER1_COMPLETE": "true",
    "SLICE_ER2_COMPLETE": "true",
    "SLICE_ER3_DEFERRED": "true",
    "RETENTION_ENFORCEMENT_ACTIVATED": "false",
    "CLOSEOUT_ENFORCEMENT_ACTIVATED": "false",
    "PRE_FLIGHT_BLOCKED_LIFTED": "false",
    "PREFLIGHT_REMAINS_BLOCKED": "true",
    "READY_FOR_OPERATOR_ARMING": "false",
    "READY_FOR_START": "false",
    "NO_PREFLIGHT_LIFT": "true",
    "NO_ENFORCEMENT_ACTIVATION": "true",
    "NO_RUNTIME": "true",
    "NO_PAPER_SHADOW_TESTNET_LIVE": "true",
    "NO_AWS_S3_RCLONE": "true",
    "NOTION_WRITES": "false",
    "WORKFLOW_DISPATCH_EXECUTED": "false",
    "NO_TRADING_AUTHORITY_CHANGE": "true",
    "MASTER_V2_LOGIC_CHANGED": "false",
    "PARALLEL_EVIDENCE_INDEX_CREATED": "false",
    "REUSE_BEFORE_NEW_PASS": "true",
    "STOP_IDLE_VALID": "true",
}


def _owner_text() -> str:
    return CANONICAL_OWNER.read_text(encoding="utf-8")


def _section_2a1() -> str:
    return _owner_text().split("## 2a.1", 1)[1].split("## 2b.", 1)[0]


def _er_release_rc_index_section(text: str) -> str:
    start = text.find(ER_RELEASE_RC_INDEX_HEADING)
    assert start != -1, "missing Evidence Durable Closeout Retention RC v0 index section"
    end = text.find("## 2b.2 Closeout Enforcement Planning Contract v0", start)
    assert end != -1
    return text[start:end]


def _machine_line_values_from_anchor(text: str, anchor: str) -> dict[str, str]:
    idx = text.find(anchor)
    assert idx != -1, f"missing anchor {anchor}"
    fence_start = text.rfind("```", 0, idx)
    fence_end = text.find("```", idx)
    assert fence_start != -1 and fence_end != -1
    inner = text[fence_start + 3 : fence_end]
    if inner.startswith("text\n"):
        inner = inner[5:]
    values: dict[str, str] = {}
    for line in inner.splitlines():
        stripped = line.strip()
        if "=" in stripped:
            key, value = stripped.split("=", 1)
            values[key.strip()] = value.strip()
    return values


def _adapter_text() -> str:
    return PAPER_ADAPTER.read_text(encoding="utf-8")


def _p101_text() -> str:
    return P101_SCRIPT.read_text(encoding="utf-8")


def _p93_text() -> str:
    return P93_SCRIPT.read_text(encoding="utf-8")


def _p91_text() -> str:
    return P91_SCRIPT.read_text(encoding="utf-8")


def test_canonical_owner_exists() -> None:
    assert CANONICAL_OWNER.is_file()


def test_canonical_owner_declares_primary_evidence_required_for_every_run() -> None:
    text = _owner_text()
    assert "PRIMARY_EVIDENCE_REQUIRED_FOR_EVERY_RUN=true" in text
    assert "## 2a. Primary evidence retention invariant v0" in text


def test_canonical_owner_applies_to_all_run_types() -> None:
    text = _owner_text()
    for run_type in (
        "Paper",
        "Shadow",
        "Testnet",
        "Live/Canary",
        "Scheduler",
        "Supervisor",
        "Daemon",
        "Smoke",
        "bounded trial",
        "runtime adapter",
    ):
        assert run_type in text


def test_canonical_owner_requires_durable_archive_outside_tmp() -> None:
    text = _owner_text()
    assert "durable archive outside `/tmp`" in text
    assert "archive verification passes" in text


def test_canonical_owner_requires_manifest_and_sha256_verification() -> None:
    text = _owner_text()
    assert "MANIFEST.sha256" in text
    assert "shasum -a 256 -c" in text
    assert "RC=0" in text


def test_canonical_owner_requires_closeout_and_postrun_review() -> None:
    text = _owner_text()
    assert "closeout present" in text
    assert "postrun/review present" in text
    assert "REVIEW_RESULT.json" in text


def test_canonical_owner_rejects_non_primary_evidence_sources() -> None:
    text = _owner_text()
    forbidden = (
        "/tmp`-only artifacts",
        "transcript-only evidence",
        "Notion pointer-only evidence",
        "chat-summary-only evidence",
        "unverified archive copies",
    )
    for phrase in forbidden:
        assert phrase in text


def test_canonical_owner_forbids_gate_clearance_from_documentary_only() -> None:
    text = _owner_text()
    assert "No gate clearance" in text
    assert "degraded or documentary evidence alone" in text


def test_canonical_owner_no_automatic_24h_72h_rerun_after_paper120() -> None:
    text = _owner_text()
    assert "automatic **24h** or **72h** rerun requirement" in text
    assert "Paper120" in text


def test_canonical_owner_run_not_complete_until_archive_verification() -> None:
    text = _owner_text()
    assert "A run is **not complete** until **archive verification passes**" in text


def test_paper_adapter_plan_only_default_and_execute_gated() -> None:
    text = _adapter_text()
    assert "plan-only default" in text
    assert "--plan-only" in text or '"plan-only"' in text
    assert "--execute" in text
    assert "requires --approval-record" in text or "execute requires --approval-record" in text


def test_paper_adapter_archive_root_must_be_outside_tmp() -> None:
    text = _adapter_text()
    assert "archive root must be outside /tmp" in text


def test_canonical_owner_references_paper_adapter_implementation() -> None:
    text = _owner_text()
    assert "run_paper_only_bounded_observation_adapter_v0.py" in text
    assert "primary_evidence_retention_v0.py" in text
    assert "plan-only default" in text
    assert "archive root outside `/tmp`" in text


def test_shared_helper_module_exists() -> None:
    assert SHARED_HELPER.is_file()
    text = SHARED_HELPER.read_text(encoding="utf-8")
    assert "def write_manifest_sha256" in text
    assert "def verify_manifest_sha256" in text
    assert "def finalize_primary_evidence_root" in text


def test_canonical_owner_references_scheduler_completion_opt_in() -> None:
    text = _owner_text()
    assert "run_scheduler.py" in text
    assert "primary-evidence-enforce" in text or "primary_evidence_enforce" in text
    assert "scheduler_completion_closeout_v0" in text


def test_canonical_owner_references_supervisor_pack_closeout() -> None:
    text = _owner_text()
    assert "pack_online_readiness_supervisor_evidence_v0.py" in text
    assert "supervisor_session_closeout_v0" in text


def test_canonical_owner_references_p79_archive_manifest_gate() -> None:
    text = _owner_text()
    assert "p79_supervisor_health_gate_v1.sh" in text
    assert "ARCHIVE_ROOT" in text
    assert "verify_manifest_sha256" in text
    assert "supervisor_session_closeout_v0" in text
    assert "MANIFEST.sha256" in text
    assert "non-authorizing" in text
    assert "does not start/stop supervisor" in text


def test_canonical_owner_references_p101_post_stop_operator_hints() -> None:
    text = _owner_text()
    assert "p101_stop_playbook_v1.sh" in text
    assert "P101_POST_STOP_PRIMARY_EVIDENCE_OPERATOR_HINTS" in text
    assert "run_online_readiness_post_stop_pack_v0.sh" in text
    assert "--p79-archive-verify" in text
    assert "does not execute wrapper" in text.lower() or "does not execute pack" in text.lower()
    assert "operator must" in text.lower()
    assert "non-authorizing" in text
    assert "In-process online-daemon automatic pack remains unimplemented" in text


def test_canonical_owner_references_p91_post_stop_operator_hints() -> None:
    text = _owner_text()
    assert "p91_audit_snapshot_runner_v1.sh" in text
    assert "P93 status dashboard" in text or "p93" in text.lower()
    assert "run_online_readiness_post_stop_pack_v0.sh" in text
    assert "--p79-archive-verify" in text
    assert "does not execute wrapper" in text.lower() or "non-executing" in text.lower()
    assert "operator must" in text.lower()
    assert "non-authorizing" in text
    assert "In-process online-daemon automatic pack remains unimplemented" in text


def test_canonical_owner_references_post_stop_pack_wrapper() -> None:
    text = _owner_text()
    assert "run_online_readiness_post_stop_pack_v0.sh" in text
    assert "pack_online_readiness_supervisor_evidence_v0.py" in text
    assert "operator-invoked" in text.lower()
    assert "--p79-archive-verify" in text
    assert "does not start/stop supervisor" in text
    assert "launchctl" in text.lower()
    assert "non-authorizing" in text
    assert "In-process online-daemon automatic pack remains unimplemented" in text


def test_p79_archive_root_mode_in_health_gate_shell() -> None:
    assert P79_SHELL.is_file()
    text = P79_SHELL.read_text(encoding="utf-8")
    assert "ARCHIVE_ROOT" in text
    assert "mutually exclusive" in text
    assert "p79_supervisor_evidence_manifest_verify_v0.py" in text
    assert "evidence_non_authorizing" in text


def test_p79_verifier_reuses_shared_manifest_helper() -> None:
    assert P79_VERIFY.is_file()
    text = P79_VERIFY.read_text(encoding="utf-8")
    assert "verify_manifest_sha256" in text
    assert "primary_evidence_retention_v0" in text
    assert "def verify_manifest_sha256" not in text
    assert "subprocess" not in text
    assert "launchctl " not in text


def test_p79_verifier_checks_closeout_and_manifest_non_authorizing() -> None:
    text = P79_VERIFY.read_text(encoding="utf-8")
    assert "CLOSEOUT_FILENAME" in text or "supervisor_session_closeout_v0" in text
    assert "MANIFEST_FILENAME" in text or "MANIFEST.sha256" in text
    assert "evidence_non_authorizing" in text
    assert "LIVE_ALLOWED" not in text
    assert "BROKER_EXCHANGE_ALLOWED" not in text


def test_p101_stop_playbook_post_stop_hint_references_wrapper_and_optional_p79() -> None:
    assert P101_SCRIPT.is_file()
    text = _p101_text()
    assert "run_online_readiness_post_stop_pack_v0.sh" in text
    assert "--p79-archive-verify" in text
    assert "P101_POST_STOP_PRIMARY_EVIDENCE_OPERATOR_HINTS.txt" in text
    assert "--primary-evidence-enforce" in text


def test_p101_stop_playbook_post_stop_hint_markers_non_authorizing() -> None:
    text = _p101_text()
    for marker in (
        "HINT_ONLY=true",
        "WRAPPER_REFERENCED=true",
        "WRAPPER_NOT_EXECUTED_BY_P101=true",
        "PACK_NOT_EXECUTED_BY_P101=true",
        "P79_ARCHIVE_VERIFY_NOT_EXECUTED_BY_P101=true",
        "OPERATOR_MUST_RUN_EXPLICITLY=true",
        "EVIDENCE_NON_AUTHORIZING=true",
    ):
        assert marker in text


def test_p101_stop_playbook_does_not_auto_execute_wrapper_pack_or_p79_archive_verify() -> None:
    lines = _p101_text().splitlines()
    wrapper_offenders = [
        line
        for line in lines
        if "run_online_readiness_post_stop_pack_v0.sh" in line
        and not line.strip().startswith("#")
        and not line.strip().startswith("echo")
    ]
    assert wrapper_offenders == []
    pack_offenders = [
        line
        for line in lines
        if "pack_online_readiness_supervisor_evidence_v0.py" in line
        and not line.strip().startswith("#")
        and not line.strip().startswith("echo")
    ]
    assert pack_offenders == []
    p79_offenders = [
        line
        for line in lines
        if "p79_supervisor_health_gate_v1.sh" in line
        and "ARCHIVE_ROOT" in line
        and not line.strip().startswith("echo")
    ]
    assert p79_offenders == []


def test_p101_stop_playbook_no_new_launchctl_or_supervisor_start() -> None:
    text = _p101_text()
    assert "launchctl bootstrap" not in text
    assert "launchctl kickstart" not in text
    assert "online_readiness_supervisor_v1.sh start" not in text
    assert "online_readiness_daemon_v1.sh" not in text


def test_p93_status_dashboard_post_stop_hint_references_wrapper_and_optional_p79() -> None:
    assert P93_SCRIPT.is_file()
    text = _p93_text()
    assert "run_online_readiness_post_stop_pack_v0.sh" in text
    assert "--p79-archive-verify" in text
    assert "P93_POST_STOP_PRIMARY_EVIDENCE_OPERATOR_HINTS.txt" in text
    assert "--primary-evidence-enforce" in text


def test_p93_status_dashboard_post_stop_hint_markers_non_authorizing() -> None:
    text = _p93_text()
    for marker in (
        "HINT_ONLY=true",
        "WRAPPER_REFERENCED=true",
        "WRAPPER_NOT_EXECUTED_BY_P93=true",
        "PACK_NOT_EXECUTED_BY_P93=true",
        "P79_ARCHIVE_VERIFY_NOT_EXECUTED_BY_P93=true",
        "OPERATOR_MUST_RUN_EXPLICITLY=true",
        "EVIDENCE_NON_AUTHORIZING=true",
    ):
        assert marker in text


def test_p93_status_dashboard_does_not_auto_execute_wrapper_pack_or_p79_archive_verify() -> None:
    lines = _p93_text().splitlines()
    wrapper_offenders = [
        line
        for line in lines
        if "run_online_readiness_post_stop_pack_v0.sh" in line
        and not line.strip().startswith("#")
        and not line.strip().startswith("echo")
    ]
    assert wrapper_offenders == []
    pack_offenders = [
        line
        for line in lines
        if "pack_online_readiness_supervisor_evidence_v0.py" in line
        and not line.strip().startswith("#")
        and not line.strip().startswith("echo")
    ]
    assert pack_offenders == []
    p79_offenders = [
        line
        for line in lines
        if "p79_supervisor_health_gate_v1.sh" in line
        and "ARCHIVE_ROOT" in line
        and not line.strip().startswith("echo")
    ]
    assert p79_offenders == []


def test_p93_status_dashboard_no_new_launchctl_or_supervisor_start() -> None:
    text = _p93_text()
    assert "launchctl bootstrap" not in text
    assert "launchctl kickstart" not in text
    assert "online_readiness_supervisor_v1.sh start" not in text
    assert "online_readiness_daemon_v1.sh" not in text


def test_p91_audit_snapshot_post_stop_hint_references_wrapper_and_optional_p79() -> None:
    assert P91_SCRIPT.is_file()
    text = _p91_text()
    assert "run_online_readiness_post_stop_pack_v0.sh" in text
    assert "--p79-archive-verify" in text
    assert "P91_POST_STOP_PRIMARY_EVIDENCE_OPERATOR_HINTS.txt" in text
    assert "--primary-evidence-enforce" in text


def test_p91_audit_snapshot_post_stop_hint_markers_non_authorizing() -> None:
    text = _p91_text()
    for marker in (
        "HINT_ONLY=true",
        "WRAPPER_REFERENCED=true",
        "WRAPPER_NOT_EXECUTED_BY_P91=true",
        "PACK_NOT_EXECUTED_BY_P91=true",
        "P79_ARCHIVE_VERIFY_NOT_EXECUTED_BY_P91=true",
        "OPERATOR_MUST_RUN_EXPLICITLY=true",
        "EVIDENCE_NON_AUTHORIZING=true",
        "P91_AUDIT_SNAPSHOT_NOT_POST_STOP_AUTHORITY=true",
    ):
        assert marker in text


def test_p91_audit_snapshot_does_not_auto_execute_wrapper_pack_or_p79_archive_verify() -> None:
    lines = _p91_text().splitlines()
    wrapper_offenders = [
        line
        for line in lines
        if "run_online_readiness_post_stop_pack_v0.sh" in line
        and not line.strip().startswith("#")
        and not line.strip().startswith("echo")
    ]
    assert wrapper_offenders == []
    pack_offenders = [
        line
        for line in lines
        if "pack_online_readiness_supervisor_evidence_v0.py" in line
        and not line.strip().startswith("#")
        and not line.strip().startswith("echo")
    ]
    assert pack_offenders == []
    p79_offenders = [
        line
        for line in lines
        if "p79_supervisor_health_gate_v1.sh" in line
        and "ARCHIVE_ROOT" in line
        and not line.strip().startswith("echo")
    ]
    assert p79_offenders == []


def test_p91_audit_snapshot_no_new_launchctl_or_supervisor_start() -> None:
    text = _p91_text()
    assert "launchctl bootstrap" not in text
    assert "launchctl kickstart" not in text
    assert "online_readiness_supervisor_v1.sh start" not in text
    assert "online_readiness_daemon_v1.sh" not in text


def test_canonical_owner_references_p67_p72_opt_in_enforce() -> None:
    text = _owner_text()
    assert "primary_evidence_enforce=True" in text
    assert "finalize_primary_evidence_root" in text


def test_bounded_adapters_import_shared_helper_not_duplicate_verify() -> None:
    for path in (PAPER_ADAPTER, SHADOW_ADAPTER, TESTNET_ADAPTER):
        text = path.read_text(encoding="utf-8")
        assert "primary_evidence_retention_v0" in text
        assert "def verify_manifest_sha256" not in text


def test_section_2a1_contains_mandatory_closeout_wiring_token() -> None:
    text = _owner_text()
    section = _section_2a1()
    assert "## 2a. Primary evidence retention invariant v0" in text
    assert "## 2a.1 Future-run primary evidence hard gate v0" in text
    assert text.index("## 2a.") < text.index("## 2a.1") < text.index("## 2b.")
    assert MANDATORY_CLOSEOUT_WIRING_TOKEN in section


def test_invariant_owner_crosslinks_mandatory_wiring_with_bounded_review_durable_run_root() -> None:
    section = _section_2a1()
    for review_path in (SHADOW_REVIEW, TESTNET_REVIEW):
        text = review_path.read_text(encoding="utf-8")
        assert review_path.name in section
        assert "--durable-run-root" in text
        assert "validate_durable_primary_evidence_root" in text
        assert "default=None" in text
    assert MANDATORY_CLOSEOUT_WIRING_TOKEN in section


def test_invariant_owner_crosslinks_bounded_adapters_with_mandatory_wiring_review_owners() -> None:
    section = _section_2a1()
    for adapter_path, review_name in (
        (SHADOW_ADAPTER, SHADOW_REVIEW.name),
        (TESTNET_ADAPTER, TESTNET_REVIEW.name),
    ):
        adapter_text = adapter_path.read_text(encoding="utf-8")
        assert review_name in adapter_text
        assert review_name in section
        assert "primary_evidence_retention_v0" in adapter_text
    assert MANDATORY_CLOSEOUT_WIRING_TOKEN in section


def test_invariant_owner_preserves_durable_run_root_default_off_on_adapter_execute() -> None:
    for adapter_path in (SHADOW_ADAPTER, TESTNET_ADAPTER):
        text = adapter_path.read_text(encoding="utf-8")
        assert "--durable-run-root" not in text
        assert "durable_run_root" not in text
        review_cmd_region = text.split("review_cmd =", 1)[1].split("]", 1)[0]
        assert "--staging-root" in review_cmd_region
        assert "--durable-run-root" not in review_cmd_region
    section = _section_2a1()
    collapsed = section.replace("**", "").lower()
    assert "default off" in collapsed or "opt-in (default off)" in collapsed


def test_invariant_owner_mandatory_wiring_chain_preserves_non_authorizing_boundary() -> None:
    invariant_section = _owner_text().split("## 2a.1", 1)[0]
    mandatory_section = _section_2a1()
    for section in (invariant_section, mandatory_section):
        collapsed = section.replace("**", "").lower()
        assert "non-authorizing" in collapsed or "evidence ≠ approval" in section
        assert "blocked" in collapsed
    assert "EVIDENCE_DOES_NOT_AUTHORIZE_RUNTIME=true" in mandatory_section
    assert HARD_GATE_CONTRACT_TESTS.name in Path(__file__).read_text(encoding="utf-8")


def test_invariant_owner_crosslinks_bounded_review_contract_module() -> None:
    invariant_text = Path(__file__).read_text(encoding="utf-8")
    bounded_text = BOUNDED_REVIEW_CONTRACT_TESTS.read_text(encoding="utf-8")
    assert BOUNDED_REVIEW_CONTRACT_TESTS.name in invariant_text
    assert MANDATORY_CLOSEOUT_WIRING_TOKEN in bounded_text
    assert MANDATORY_CLOSEOUT_WIRING_TOKEN in invariant_text
    for review_path in (SHADOW_REVIEW, TESTNET_REVIEW):
        review_text = review_path.read_text(encoding="utf-8")
        assert review_path.name in bounded_text or review_path.name in invariant_text
        assert "--durable-run-root" in review_text
        assert "validate_durable_primary_evidence_root" in review_text


def test_invariant_owner_crosslinks_scheduler_completion_contract_module() -> None:
    invariant_text = Path(__file__).read_text(encoding="utf-8")
    scheduler_text = SCHEDULER_COMPLETION_CONTRACT_TESTS.read_text(encoding="utf-8")
    assert SCHEDULER_COMPLETION_CONTRACT_TESTS.name in invariant_text
    assert Path(__file__).name in scheduler_text
    assert MANDATORY_CLOSEOUT_WIRING_TOKEN in invariant_text
    assert MANDATORY_CLOSEOUT_WIRING_TOKEN in scheduler_text
    assert HARD_GATE_CONTRACT_TESTS.name in scheduler_text


def test_invariant_scheduler_reciprocal_chain_shares_mandatory_wiring_with_preflight_2a1() -> None:
    section = _section_2a1()
    scheduler_text = SCHEDULER_COMPLETION_CONTRACT_TESTS.read_text(encoding="utf-8")
    hard_gate_text = HARD_GATE_CONTRACT_TESTS.read_text(encoding="utf-8")
    assert MANDATORY_CLOSEOUT_WIRING_TOKEN in section
    assert MANDATORY_CLOSEOUT_WIRING_TOKEN in scheduler_text
    assert MANDATORY_CLOSEOUT_WIRING_TOKEN in hard_gate_text
    assert HARD_GATE_CONTRACT_TESTS.name in Path(__file__).read_text(encoding="utf-8")
    assert "§2a.1" in section or "2a.1" in section


def test_invariant_scheduler_reciprocal_chain_preserves_non_authorizing_evidence_boundary() -> None:
    scheduler_text = RUN_SCHEDULER.read_text(encoding="utf-8")
    scheduler_owner_text = SCHEDULER_COMPLETION_CONTRACT_TESTS.read_text(encoding="utf-8")
    section = _section_2a1().replace("**", "").lower()
    assert "evidence_non_authorizing" in scheduler_text
    assert "non-authorizing" in section or "does not authorize runtime" in section
    assert (
        "non-authorizing" in scheduler_owner_text.lower()
        or "evidence_non_authorizing" in scheduler_owner_text
    )
    assert "finalize_primary_evidence_root" in SHARED_HELPER.read_text(encoding="utf-8")


def test_invariant_scheduler_reciprocal_chain_confirms_no_scheduler_start_implied() -> None:
    scheduler_script = RUN_SCHEDULER.read_text(encoding="utf-8")
    scheduler_owner_text = SCHEDULER_COMPLETION_CONTRACT_TESTS.read_text(encoding="utf-8").lower()
    preflight_text = _owner_text().lower()
    assert "assert_scheduler_start_authorized" in scheduler_script
    assert "SCHEDULER_START_BLOCKED_EXIT" in scheduler_script
    assert "test_non_dry_run_blocked_under_hold_still_exits_2" in scheduler_owner_text
    assert (
        "start boundary guard unchanged" in preflight_text or "scheduler boundary" in preflight_text
    )


def test_invariant_scheduler_reciprocal_chain_preserves_durable_run_root_and_adapter_default_off() -> (
    None
):
    scheduler_owner_text = SCHEDULER_COMPLETION_CONTRACT_TESTS.read_text(encoding="utf-8")
    section = _section_2a1().replace("**", "").lower()
    for adapter_path in (SHADOW_ADAPTER, TESTNET_ADAPTER):
        text = adapter_path.read_text(encoding="utf-8")
        assert "--durable-run-root" not in text
        assert "durable_run_root" not in text
    for review_path in (SHADOW_REVIEW, TESTNET_REVIEW):
        text = review_path.read_text(encoding="utf-8")
        assert "--durable-run-root" in text
        assert "default=None" in text
    assert "default off" in section or "opt-in" in section
    assert (
        "primary-evidence-enforce" in scheduler_owner_text
        or "primary_evidence_enforce" in scheduler_owner_text
    )


def test_paper_adapter_verifies_manifest_after_archive_copy() -> None:
    text = PAPER_ADAPTER.read_text(encoding="utf-8")
    execute = text.split("def execute_plan", 1)[1].split("\ndef build_arg_parser", 1)[0]
    assert "verify_manifest_sha256(archive_dest)" in execute
    assert execute.index("verify_manifest_sha256(archive_dest)") > execute.rindex("shutil.copy")
    assert "MANIFEST_VERIFY_RC=0" in execute


def test_verify_manifest_sha256_fails_closed_on_missing(tmp_path) -> None:
    import sys

    sys.path.insert(0, str(REPO_ROOT))
    from scripts.ops.primary_evidence_retention_v0 import verify_manifest_sha256

    ok, reason = verify_manifest_sha256(tmp_path)
    assert ok is False
    assert reason == "MANIFEST.sha256 missing"


def test_verify_manifest_sha256_detects_checksum_mismatch(tmp_path) -> None:
    import sys

    sys.path.insert(0, str(REPO_ROOT))
    from scripts.ops.primary_evidence_retention_v0 import (
        verify_manifest_sha256,
        write_manifest_sha256,
    )

    data = tmp_path / "data.txt"
    data.write_text("hello", encoding="utf-8")
    write_manifest_sha256(tmp_path)
    data.write_text("tampered", encoding="utf-8")
    ok, reason = verify_manifest_sha256(tmp_path)
    assert ok is False
    assert "checksum mismatch" in reason


def test_write_and_verify_manifest_roundtrip(tmp_path) -> None:
    import sys

    sys.path.insert(0, str(REPO_ROOT))
    from scripts.ops.primary_evidence_retention_v0 import (
        verify_manifest_sha256,
        write_manifest_sha256,
    )

    (tmp_path / "nested").mkdir()
    (tmp_path / "nested" / "a.txt").write_text("a", encoding="utf-8")
    (tmp_path / "b.txt").write_text("b", encoding="utf-8")
    write_manifest_sha256(tmp_path)
    ok, reason = verify_manifest_sha256(tmp_path)
    assert ok is True, reason


def test_invariant_owner_crosslinks_cybersecurity_artifact_retention_histogram_v0() -> None:
    ci_audit = (REPO_ROOT / "docs" / "ops" / "CI_AUDIT_KNOWN_ISSUES.md").read_text(encoding="utf-8")
    assert RECIPROCAL_CROSSLINK_MARKER in ci_audit
    assert "artifact_retention_or_evidence_gap" in ci_audit
    assert Path(__file__).name in ci_audit
    assert ARTIFACT_RETENTION_CROSSLINK_TESTS.is_file()

    crosslink_text = ARTIFACT_RETENTION_CROSSLINK_TESTS.read_text(encoding="utf-8")
    assert Path(__file__).name in crosslink_text
    assert RECIPROCAL_CROSSLINK_MARKER in crosslink_text
    assert HARD_GATE_CONTRACT_TESTS.is_file()
    assert Path(__file__).name in HARD_GATE_CONTRACT_TESTS.read_text(encoding="utf-8")

    ci_lines = {line.strip() for line in ci_audit.splitlines()}
    assert ("INPUT_JSONL_PROVIDED" + _MARKER_TRUE) not in ci_lines
    assert ("R001_R002_R007_MAPPING_COMPLETED" + _MARKER_TRUE) not in ci_lines


def test_pe6_invariant_owner_cyber_er_defensive_reciprocal_retention_guard_v0() -> None:
    ci_audit = (REPO_ROOT / "docs" / "ops" / "CI_AUDIT_KNOWN_ISSUES.md").read_text(encoding="utf-8")
    section5 = (
        REPO_ROOT / "docs" / "ops" / "planning" / "SECTION5_PREFLIGHT_GAP_OWNER_MAP_CONTRACT_V0.md"
    ).read_text(encoding="utf-8")
    gap2a1 = section5.split("## §2a.1 Primary Evidence Enforcement Contract v0", 1)[1].split(
        "## Gap 1 Execute Entrypoint Contract v0", 1
    )[0]
    preflight_er = (
        _owner_text()
        .split("### Evidence Durable Closeout Retention RC v0", 1)[1]
        .split("## 2b.", 1)[0]
    )

    for token in PE6_CYBER_ER_CROSSLINK_MARKERS:
        assert token in ci_audit
        assert token in gap2a1
        assert token in preflight_er

    crosslink_text = ARTIFACT_RETENTION_CROSSLINK_TESTS.read_text(encoding="utf-8")
    assert "PE6_CYBER_ER_ARTIFACT_RETENTION_CROSSLINK_V0=true" in crosslink_text
    assert "defensive/derived/static" in ci_audit.lower()
    assert "CYBER_VISIBILITY_ARTIFACTS_DEFENSIVE_DERIVED_STATIC_ONLY=true" in ci_audit
    assert "artifact_retention_or_evidence_gap" in ci_audit
    assert HARD_GATE_CONTRACT_TESTS.is_file()
    assert THIS_MODULE in HARD_GATE_CONTRACT_TESTS.read_text(encoding="utf-8")
    assert "TMP_ONLY_EVIDENCE_INVALID" in _owner_text()
    assert "MANIFEST_VERIFY_REQUIRED" in _owner_text()
    assert "PREFLIGHT_REMAINS_BLOCKED=true" in preflight_er
    assert "READY_FOR_OPERATOR_ARMING=false" in preflight_er

    ci_lines = {line.strip() for line in ci_audit.splitlines()}
    assert ("INPUT_JSONL_PROVIDED" + _MARKER_TRUE) not in ci_lines
    assert ("R001_R002_R007_MAPPING_COMPLETED" + _MARKER_TRUE) not in ci_lines


def test_evidence_durable_closeout_retention_rc_v0_slice_er1_release_index_v0() -> None:
    text = _owner_text()
    collapsed = text.lower()
    section = _er_release_rc_index_section(text)
    release_values = _machine_line_values_from_anchor(text, ER_RELEASE_RC_BLOCK_ANCHOR)

    assert "EVIDENCE_DURABLE_CLOSEOUT_RETENTION_RC_V0" in section
    assert "**CORE COMPLETE**" in section
    assert "SLICE-ER-1" in section
    assert "SLICE-ER-2" in section
    assert "SLICE-ER-3" in section
    assert "complete" in section and "#3906" in section
    assert "complete" in section and "#3907" in section
    assert "**deferred**" in section
    assert "not authorized until merged" not in collapsed
    assert "Release scope (complete)" in section
    assert "docs/tests/tooling-only" in section
    assert (
        "this document (§2a / §2a.1)" in section
        or "§2a primary evidence retention invariant" in section
    )
    assert THIS_MODULE in section
    assert MANDATORY_CLOSEOUT_CONTRACT_TESTS.name in section
    assert DURABLE_CLOSEOUT_VERIFY_TESTS.name in section
    assert ER_PLANNING_BUNDLE_PATH in section
    assert "no parallel" in collapsed
    assert (
        "does **not** authorize future runs" in section
        or "does not authorize future runs" in collapsed
    )
    assert "does **not** claim retention is fully enforced" in section or (
        "does not claim retention is fully enforced" in collapsed
    )
    assert "Canonical remains repo + durable Evidence Archive" in section
    assert "PREFLIGHT_REMAINS_BLOCKED=true" in section
    assert "READY_FOR_OPERATOR_ARMING=false" in section

    for key, expected in ER_RELEASE_RC_EXPECTED.items():
        assert release_values.get(key) == expected, (
            f"release RC index {key}={release_values.get(key)!r} expected {expected!r}"
        )

    assert "non-authorizing" in collapsed or "BLOCKED" in section


def test_evidence_durable_closeout_retention_rc_v0_slice_er2_guard_owner_crosslink_v0() -> None:
    section = _er_release_rc_index_section(_owner_text())

    assert "SLICE-ER-2" in section
    assert (
        "test_*retention*" in section
        or "test_primary_evidence_retention_invariant_contract_v0.py" in section
    )
    assert (
        "test_*closeout*" in section or "test_mandatory_durable_closeout_contract_v0.py" in section
    )
    assert THIS_MODULE in section
    assert MANDATORY_CLOSEOUT_CONTRACT_TESTS.is_file()


EER1_PLANNING_BUNDLE_PATH = (
    "/Users/frnkhrz/Documents/Peak_Trade_runtime_evidence_archive_20260520T161443Z/"
    "planning/next_larger_release_candidate_after_cv3_plus_core_complete_v0_20260603T033708Z/"
)
EER1_CV3_PLUS_CLOSEOUT_PATH = (
    "/Users/frnkhrz/Documents/Peak_Trade_runtime_evidence_archive_20260520T161443Z/"
    "closeout/cybersecurity_defensive_visibility_cv3_plus_rc_v0_core_complete_after_cv3c_v0_20260603T033708Z/"
)
EER1_PE_CLOSEOUT_PATH = (
    "/Users/frnkhrz/Documents/Peak_Trade_runtime_evidence_archive_20260520T161443Z/"
    "closeout/primary_evidence_run_completion_contract_rc_v0_core_complete_after_pe6_v0_20260603T031800Z/"
)
EER1_CI_INDEX_HEADING = "## Evidence Durable Enforcement Readiness Review RC v0 — index v0"
EER1_PREFLIGHT_CROSSLINK_HEADING = (
    "### Evidence Durable Enforcement Readiness Review RC v0 — EER1 crosslink v0"
)


def _eer1_ci_index_section(text: str) -> str:
    return text.split(EER1_CI_INDEX_HEADING, 1)[1].split("## Master V2", 1)[0]


def _eer1_preflight_crosslink_section(text: str) -> str:
    return text.split(EER1_PREFLIGHT_CROSSLINK_HEADING, 1)[1].split("## 3. Non-authority", 1)[0]


def test_eer1_readiness_review_index_v0() -> None:
    owner = _owner_text()
    ci_audit = (REPO_ROOT / "docs" / "ops" / "CI_AUDIT_KNOWN_ISSUES.md").read_text(encoding="utf-8")
    section5 = (
        REPO_ROOT / "docs" / "ops" / "planning" / "SECTION5_PREFLIGHT_GAP_OWNER_MAP_CONTRACT_V0.md"
    ).read_text(encoding="utf-8")
    gap2a1 = section5.split("## §2a.1 Primary Evidence Enforcement Contract v0", 1)[1].split(
        "## Gap 1 Execute Entrypoint Contract v0", 1
    )[0]
    ci_section = _eer1_ci_index_section(ci_audit)
    preflight_eer1 = _eer1_preflight_crosslink_section(owner)

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
        assert token in ci_section
        assert token in gap2a1
        assert token in preflight_eer1
    for token in (
        "RETENTION_ENFORCEMENT_ACTIVATED=false",
        "CLOSEOUT_ENFORCEMENT_ACTIVATED=false",
        "MANIFEST_VERIFY_REQUIRED=true",
    ):
        assert token in ci_section
        assert token in preflight_eer1

    assert EER1_PLANNING_BUNDLE_PATH in ci_section
    assert EER1_CV3_PLUS_CLOSEOUT_PATH in ci_section
    assert EER1_PE_CLOSEOUT_PATH in ci_section
    assert "SECTION5_PREFLIGHT_GAP_OWNER_MAP_CONTRACT_V0.md" in ci_section
    assert "PAPER_SHADOW_247_PREFLIGHT_CONTRACT_V0.md" in ci_section
    assert THIS_MODULE in ci_section
    assert "prerequisite input" in ci_section.lower() or "prerequisite" in ci_section.lower()
    assert "no parallel" in ci_section.lower()
    ci_lines = {line.strip() for line in ci_section.splitlines()}
    assert "GAP2A1_PRIMARY_EVIDENCE_ENFORCED=true" not in ci_lines
    assert "READY_FOR_OPERATOR_ARMING=true" not in ci_lines
