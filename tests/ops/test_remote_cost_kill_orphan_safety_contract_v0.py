"""Static contract tests for Remote Cost/Kill/Orphan Safety Contract v0 (taxonomy §6a.0.4)."""

from __future__ import annotations

import json
import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
TAXONOMY_SPEC = REPO_ROOT / "docs/ops/specs/RUNTIME_LANE_TAXONOMY_AUTHORITY_LEVELS_CONTRACT_V0.md"
PREFLIGHT = REPO_ROOT / "docs/ops/runbooks/PAPER_SHADOW_247_PREFLIGHT_CONTRACT_V0.md"
DOCS_TRUTH_MAP = REPO_ROOT / "docs/ops/registry/DOCS_TRUTH_MAP.md"
FIXTURE = REPO_ROOT / "tests/fixtures/ops/remote_cost_kill_orphan_safety_v0.json"

SAFETY_CONTRACT_MARKERS = (
    "REMOTE_COST_KILL_ORPHAN_SAFETY_CONTRACT_V0=true",
    "REMOTE_COST_KILL_ORPHAN_PLANNING_ONLY=true",
    "REMOTE_COST_KILL_ORPHAN_DO_NOT_PROVISION=true",
    "REMOTE_COST_KILL_ORPHAN_DO_NOT_CONNECT=true",
    "REMOTE_COST_KILL_ORPHAN_DO_NOT_KILL_PROCESS=true",
    "REMOTE_COST_KILL_ORPHAN_DO_NOT_TERMINATE_HOST=true",
    "REMOTE_COST_KILL_ORPHAN_NO_AWS_CLI=true",
    "REMOTE_COST_KILL_ORPHAN_NO_SSH=true",
    "REMOTE_COST_KILL_ORPHAN_NO_SYSTEMD=true",
    "REMOTE_COST_KILL_ORPHAN_NO_GHA_RUNNER=true",
    "REMOTE_COST_KILL_ORPHAN_NO_NETWORK=true",
    "REMOTE_COST_KILL_ORPHAN_NOT_APPROVAL=true",
    "REMOTE_COST_KILL_ORPHAN_NOT_RUNTIME_START=true",
    "REMOTE_COST_KILL_ORPHAN_NOT_HOST_TERMINATION=true",
    "REMOTE_COST_KILL_ORPHAN_NOT_CREDENTIAL_GRANT=true",
    "REMOTE_COST_KILL_ORPHAN_NOT_TESTNET_OR_LIVE_GATE=true",
    "REMOTE_COST_KILL_ORPHAN_REQUIRES_COST_CEILING=true",
    "REMOTE_COST_KILL_ORPHAN_REQUIRES_MAX_INSTANCE_LIFETIME=true",
    "REMOTE_COST_KILL_ORPHAN_REQUIRES_MAX_RUNTIME_SECONDS=true",
    "REMOTE_COST_KILL_ORPHAN_REQUIRES_STOP_PROCEDURE=true",
    "REMOTE_COST_KILL_ORPHAN_REQUIRES_KILL_PROCEDURE=true",
    "REMOTE_COST_KILL_ORPHAN_REQUIRES_ORPHAN_DETECTION=true",
    "REMOTE_COST_KILL_ORPHAN_REQUIRES_TEARDOWN_OWNER=true",
    "REMOTE_COST_KILL_ORPHAN_REQUIRES_DURABLE_CLOSEOUT=true",
    "REMOTE_COST_KILL_ORPHAN_FORBIDS_REAL_IPS=true",
    "REMOTE_COST_KILL_ORPHAN_FORBIDS_CREDENTIALS=true",
    "REMOTE_COST_KILL_ORPHAN_FORBIDS_ACCOUNT_IDS=true",
    "REMOTE_COST_KILL_ORPHAN_FORBIDS_INSTANCE_IDS=true",
)

FORBIDDEN_DUPLICATE_SPEC_FRAGMENTS = (
    "REMOTE_COST_KILL_ORPHAN_SAFETY_CONTRACT_V0.md",
    "REMOTE_COST_KILL_ORPHAN_V0.md",
)

FORBIDDEN_FIXTURE_PATTERNS = (
    re.compile(r"\b\d{1,3}(?:\.\d{1,3}){3}\b"),
    re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
    re.compile(r"\barn:aws:", re.I),
    re.compile(r"\bi-[0-9a-f]{8,17}\b", re.I),
    re.compile(r"\b\d{12}\b"),
    re.compile(r"s3://", re.I),
    re.compile(r"-----BEGIN (?:RSA |OPENSSH )?PRIVATE KEY-----"),
)


def _section_6a04() -> str:
    text = TAXONOMY_SPEC.read_text(encoding="utf-8")
    return text.split("#### 6a.0.4 Remote cost/kill/orphan safety contract v0", 1)[1].split(
        "### S3 / Object Storage", 1
    )[0]


def test_section_6a04_present_with_markers() -> None:
    text = TAXONOMY_SPEC.read_text(encoding="utf-8")
    assert "#### 6a.0.4 Remote cost/kill/orphan safety contract v0" in text
    for marker in SAFETY_CONTRACT_MARKERS:
        assert marker in text


def test_top_level_taxonomy_markers_include_safety_contract() -> None:
    text = TAXONOMY_SPEC.read_text(encoding="utf-8")
    assert "REMOTE_COST_KILL_ORPHAN_SAFETY_CONTRACT_V0=true" in text.split("## 2.", 1)[0]


def test_planning_only_no_kill_or_terminate() -> None:
    section = _section_6a04()
    assert "REMOTE_COST_KILL_ORPHAN_PLANNING_ONLY=true" in section
    assert "REMOTE_COST_KILL_ORPHAN_DO_NOT_KILL_PROCESS=true" in section
    assert "REMOTE_COST_KILL_ORPHAN_DO_NOT_TERMINATE_HOST=true" in section
    assert "REMOTE_COST_KILL_ORPHAN_NOT_HOST_TERMINATION=true" in section


def test_no_connect_provision_or_process_control() -> None:
    section = _section_6a04()
    assert "REMOTE_COST_KILL_ORPHAN_DO_NOT_PROVISION=true" in section
    assert "REMOTE_COST_KILL_ORPHAN_DO_NOT_CONNECT=true" in section
    assert "REMOTE_COST_KILL_ORPHAN_NO_AWS_CLI=true" in section
    assert "REMOTE_COST_KILL_ORPHAN_NO_SSH=true" in section
    assert "process control" in section.lower()


def test_non_authorizing_boundaries() -> None:
    section = _section_6a04()
    assert "REMOTE_COST_KILL_ORPHAN_NOT_APPROVAL=true" in section
    assert "REMOTE_COST_KILL_ORPHAN_NOT_RUNTIME_START=true" in section
    assert "REMOTE_COST_KILL_ORPHAN_NOT_CREDENTIAL_GRANT=true" in section
    assert "REMOTE_COST_KILL_ORPHAN_NOT_TESTNET_OR_LIVE_GATE=true" in section


def test_required_safety_fields_documented() -> None:
    section = _section_6a04()
    for field in (
        "remote_host_id",
        "remote_run_id",
        "runtime_backend",
        "expected_cost_ceiling",
        "max_instance_lifetime_seconds",
        "max_runtime_seconds",
        "stop_procedure_ref",
        "kill_procedure_ref",
        "orphan_detection_ref",
        "teardown_owner",
        "cost_owner",
        "incident_owner",
        "evidence_owner",
        "closeout_owner",
        "orphan_check_required",
        "teardown_required",
        "stop_procedure_required",
        "cost_ceiling_required",
        "durable_closeout_required",
        "manifest_verify_required",
    ):
        assert field in section


def test_implementation_charter_blocked_without_safety() -> None:
    section = _section_6a04()
    assert "REMOTE_COST_KILL_ORPHAN_IMPLEMENTATION_CHARTER_BLOCKED_WITHOUT_SAFETY=true" in section
    assert "implementation charter" in section.lower()


def test_forbidden_content_documented() -> None:
    section = _section_6a04()
    assert "REMOTE_COST_KILL_ORPHAN_FORBIDS_REAL_IPS=true" in section
    assert "REMOTE_COST_KILL_ORPHAN_FORBIDS_CREDENTIALS=true" in section
    assert "REMOTE_COST_KILL_ORPHAN_FORBIDS_ACCOUNT_IDS=true" in section
    assert "REMOTE_COST_KILL_ORPHAN_FORBIDS_INSTANCE_IDS=true" in section


def test_contract_bindings_reuse_existing_owners() -> None:
    section = _section_6a04()
    assert "§6a.0 Remote Runtime Command Contract" in section
    assert "§6a.0.1" in section
    assert "§6a.0.2" in section
    assert "§6a.0.3" in section
    assert "primary_evidence_retention_v0.py" in section
    assert "§2b.1" in section or "2b.1" in section
    assert "build_generic_evidence_run_registry_v1.py" in section


def test_section_ordering_6a04_before_s3_subsection() -> None:
    text = TAXONOMY_SPEC.read_text(encoding="utf-8")
    assert text.index("#### 6a.0.4 Remote cost/kill/orphan safety contract v0") < text.index(
        "### S3 / Object Storage"
    )
    assert text.index("#### 6a.0.3 Remote host inventory planning contract v0") < text.index(
        "#### 6a.0.4 Remote cost/kill/orphan safety contract v0"
    )


def test_preflight_crosslinks_section_6a04() -> None:
    text = PREFLIGHT.read_text(encoding="utf-8")
    assert "§6a.0.4 Remote cost/kill/orphan safety contract v0" in text
    assert "REMOTE_COST_KILL_ORPHAN_PLANNING_ONLY=true" in text


def test_docs_truth_map_lists_section_6a04() -> None:
    text = DOCS_TRUTH_MAP.read_text(encoding="utf-8")
    assert "§6a.0.4" in text
    assert "Remote cost/kill/orphan safety contract v0" in text


def test_fixture_exists_and_is_planning_only() -> None:
    assert FIXTURE.is_file()
    payload = json.loads(FIXTURE.read_text(encoding="utf-8"))
    assert payload["planning_only"] is True
    assert payload["do_not_provision"] is True
    assert payload["do_not_connect"] is True
    assert payload["do_not_kill_process"] is True
    assert payload["do_not_terminate_host"] is True
    assert payload["network_called"] is False
    assert payload["aws_cli_called"] is False
    assert payload["ssh_called"] is False
    assert payload["systemd_called"] is False
    assert payload["process_control_called"] is False
    assert payload["host_termination_called"] is False
    assert payload["gha_runner_implemented"] is False
    assert payload["broker_credentials_present"] is False
    assert payload["exchange_credentials_present"] is False
    assert payload["live_authority"] is False
    assert payload["testnet_authority"] is False
    output = payload["output_machine_lines"]
    assert output["REMOTE_COST_KILL_ORPHAN_READY_FOR_IMPLEMENTATION_CHARTER"] is False
    assert output["REMOTE_COST_KILL_ORPHAN_PROCESS_KILLED"] is False
    assert output["REMOTE_COST_KILL_ORPHAN_HOST_TERMINATED"] is False


def test_fixture_has_no_obvious_secret_account_ip_or_instance_fields() -> None:
    raw = FIXTURE.read_text(encoding="utf-8")
    for pattern in FORBIDDEN_FIXTURE_PATTERNS:
        assert pattern.search(raw) is None, f"forbidden pattern matched: {pattern.pattern}"


def test_taxonomy_links_fixture() -> None:
    section = _section_6a04()
    assert "remote_cost_kill_orphan_safety_v0.json" in section


def test_no_duplicate_safety_spec_introduced() -> None:
    specs_dir = REPO_ROOT / "docs/ops/specs"
    runbooks_dir = REPO_ROOT / "docs/ops/runbooks"
    for fragment in FORBIDDEN_DUPLICATE_SPEC_FRAGMENTS:
        assert list(specs_dir.glob(f"*{fragment}*")) == []
        assert list(runbooks_dir.glob(f"*{fragment}*")) == []
