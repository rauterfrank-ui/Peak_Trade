"""Static contract tests for Remote Host Inventory Planning Contract v0 (taxonomy §6a.0.3)."""

from __future__ import annotations

import json
import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
TAXONOMY_SPEC = (
    REPO_ROOT / "docs" / "ops" / "specs" / "RUNTIME_LANE_TAXONOMY_AUTHORITY_LEVELS_CONTRACT_V0.md"
)
PREFLIGHT = REPO_ROOT / "docs/ops/runbooks/PAPER_SHADOW_247_PREFLIGHT_CONTRACT_V0.md"
DOCS_TRUTH_MAP = REPO_ROOT / "docs/ops/registry/DOCS_TRUTH_MAP.md"
FIXTURE = REPO_ROOT / "tests/fixtures/ops/remote_host_inventory_planning_v0.json"

INVENTORY_CONTRACT_MARKERS = (
    "REMOTE_HOST_INVENTORY_PLANNING_CONTRACT_V0=true",
    "REMOTE_HOST_INVENTORY_PLANNING_ONLY=true",
    "REMOTE_HOST_INVENTORY_DO_NOT_PROVISION=true",
    "REMOTE_HOST_INVENTORY_DO_NOT_CONNECT=true",
    "REMOTE_HOST_INVENTORY_NO_AWS_CLI=true",
    "REMOTE_HOST_INVENTORY_NO_SSH=true",
    "REMOTE_HOST_INVENTORY_NO_SYSTEMD=true",
    "REMOTE_HOST_INVENTORY_NO_GHA_RUNNER=true",
    "REMOTE_HOST_INVENTORY_NO_NETWORK=true",
    "REMOTE_HOST_INVENTORY_NOT_APPROVAL=true",
    "REMOTE_HOST_INVENTORY_NOT_RUNTIME_START=true",
    "REMOTE_HOST_INVENTORY_NOT_CREDENTIAL_GRANT=true",
    "REMOTE_HOST_INVENTORY_NOT_TESTNET_OR_LIVE_GATE=true",
    "REMOTE_HOST_INVENTORY_REQUIRES_REMOTE_DURABLE_ROOT_CONVENTION=true",
    "REMOTE_HOST_INVENTORY_REQUIRES_COST_CEILING=true",
    "REMOTE_HOST_INVENTORY_REQUIRES_STOP_PROCEDURE=true",
    "REMOTE_HOST_INVENTORY_REQUIRES_ORPHAN_DETECTION=true",
    "REMOTE_HOST_INVENTORY_REQUIRES_TEARDOWN_OWNER=true",
    "REMOTE_HOST_INVENTORY_FORBIDS_REAL_IPS=true",
    "REMOTE_HOST_INVENTORY_FORBIDS_CREDENTIALS=true",
    "REMOTE_HOST_INVENTORY_FORBIDS_ACCOUNT_IDS=true",
)

FORBIDDEN_DUPLICATE_SPEC_FRAGMENTS = (
    "REMOTE_HOST_INVENTORY_PLANNING_CONTRACT_V0.md",
    "REMOTE_HOST_INVENTORY_V0.md",
)

FORBIDDEN_FIXTURE_PATTERNS = (
    re.compile(r"\b\d{1,3}(?:\.\d{1,3}){3}\b"),
    re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
    re.compile(r"\barn:aws:", re.I),
    re.compile(r"\b\d{12}\b"),
    re.compile(r"s3://", re.I),
    re.compile(r"-----BEGIN (?:RSA |OPENSSH )?PRIVATE KEY-----"),
)


def _section_6a03() -> str:
    text = TAXONOMY_SPEC.read_text(encoding="utf-8")
    return text.split("#### 6a.0.3 Remote host inventory planning contract v0", 1)[1].split(
        "### S3 / Object Storage", 1
    )[0]


def test_section_6a03_present_with_markers() -> None:
    text = TAXONOMY_SPEC.read_text(encoding="utf-8")
    assert "#### 6a.0.3 Remote host inventory planning contract v0" in text
    for marker in INVENTORY_CONTRACT_MARKERS:
        assert marker in text


def test_top_level_taxonomy_markers_include_inventory_contract() -> None:
    text = TAXONOMY_SPEC.read_text(encoding="utf-8")
    assert "REMOTE_HOST_INVENTORY_PLANNING_CONTRACT_V0=true" in text.split("## 2.", 1)[0]


def test_planning_only_posture() -> None:
    section = _section_6a03()
    assert "REMOTE_HOST_INVENTORY_PLANNING_ONLY=true" in section
    assert "REMOTE_HOST_INVENTORY_DO_NOT_PROVISION=true" in section
    assert "REMOTE_HOST_INVENTORY_DO_NOT_CONNECT=true" in section
    assert "planning metadata only" in section.lower() or "planning-only" in section.lower()


def test_no_connect_or_provision_implementation() -> None:
    section = _section_6a03()
    assert "REMOTE_HOST_INVENTORY_NO_AWS_CLI=true" in section
    assert "REMOTE_HOST_INVENTORY_NO_SSH=true" in section
    assert "REMOTE_HOST_INVENTORY_NO_SYSTEMD=true" in section
    assert "REMOTE_HOST_INVENTORY_NO_GHA_RUNNER=true" in section
    assert "REMOTE_HOST_INVENTORY_NO_NETWORK=true" in section
    assert "ship inventory CLI" in section


def test_non_authorizing_boundaries() -> None:
    section = _section_6a03()
    assert "REMOTE_HOST_INVENTORY_NOT_APPROVAL=true" in section
    assert "REMOTE_HOST_INVENTORY_NOT_RUNTIME_START=true" in section
    assert "REMOTE_HOST_INVENTORY_NOT_CREDENTIAL_GRANT=true" in section
    assert "REMOTE_HOST_INVENTORY_NOT_TESTNET_OR_LIVE_GATE=true" in section
    assert "BLOCKED" in section


def test_required_inventory_fields_documented() -> None:
    section = _section_6a03()
    for field in (
        "remote_host_id",
        "runtime_backend",
        "host_owner",
        "operator_owner",
        "environment_class",
        "remote_durable_root_convention",
        "log_root_convention",
        "closeout_root_convention",
        "registry_v1_pointer",
        "credential_boundary",
        "secrets_present",
        "broker_credentials_present",
        "exchange_credentials_present",
        "paper_only",
        "max_instance_lifetime_required",
        "max_runtime_seconds_required",
        "cost_ceiling_required",
        "stop_procedure_required",
        "orphan_detection_required",
        "teardown_owner_required",
    ):
        assert field in section
    assert "planning_only" in section


def test_safety_requirements_documented() -> None:
    section = _section_6a03()
    assert "REMOTE_HOST_INVENTORY_REQUIRES_COST_CEILING=true" in section
    assert "REMOTE_HOST_INVENTORY_REQUIRES_STOP_PROCEDURE=true" in section
    assert "REMOTE_HOST_INVENTORY_REQUIRES_ORPHAN_DETECTION=true" in section
    assert "REMOTE_HOST_INVENTORY_REQUIRES_TEARDOWN_OWNER=true" in section
    assert "REMOTE_HOST_INVENTORY_REQUIRES_REMOTE_DURABLE_ROOT_CONVENTION=true" in section


def test_forbidden_content_documented() -> None:
    section = _section_6a03()
    assert "REMOTE_HOST_INVENTORY_FORBIDS_REAL_IPS=true" in section
    assert "REMOTE_HOST_INVENTORY_FORBIDS_CREDENTIALS=true" in section
    assert "REMOTE_HOST_INVENTORY_FORBIDS_ACCOUNT_IDS=true" in section
    assert "SSH usernames" in section or "ssh usernames" in section.lower()


def test_contract_bindings_reuse_existing_owners() -> None:
    section = _section_6a03()
    assert "§6a.0 Remote Runtime Command Contract" in section
    assert "§6a.0.1" in section
    assert "§6a.0.2" in section
    assert "primary_evidence_retention_v0.py" in section
    assert "§2b.1" in section or "2b.1" in section
    assert "build_generic_evidence_run_registry_v1.py" in section
    assert "preflight_s3_finalized_evidence_export_v0.py" in section
    assert "RUNBOOK_OPERATOR_CREDENTIAL_BOUNDARIES_PLANNING_FIRST_V0.md" in section


def test_section_ordering_6a03_before_s3_subsection() -> None:
    text = TAXONOMY_SPEC.read_text(encoding="utf-8")
    assert text.index("#### 6a.0.3 Remote host inventory planning contract v0") < text.index(
        "### S3 / Object Storage"
    )
    assert text.index("#### 6a.0.2 Remote paper approval/command packet contract v0") < text.index(
        "#### 6a.0.3 Remote host inventory planning contract v0"
    )


def test_preflight_crosslinks_section_6a03() -> None:
    text = PREFLIGHT.read_text(encoding="utf-8")
    assert "§6a.0.3 Remote host inventory planning contract v0" in text
    assert "REMOTE_HOST_INVENTORY_PLANNING_ONLY=true" in text


def test_docs_truth_map_lists_section_6a03() -> None:
    text = DOCS_TRUTH_MAP.read_text(encoding="utf-8")
    assert "§6a.0.3" in text
    assert "Remote host inventory planning contract v0" in text


def test_fixture_exists_and_is_planning_only() -> None:
    assert FIXTURE.is_file()
    payload = json.loads(FIXTURE.read_text(encoding="utf-8"))
    assert payload["planning_only"] is True
    assert payload["do_not_provision"] is True
    assert payload["do_not_connect"] is True
    assert payload["network_called"] is False
    assert payload["aws_cli_called"] is False
    assert payload["ssh_called"] is False
    assert payload["systemd_called"] is False
    assert payload["gha_runner_implemented"] is False
    assert payload["broker_credentials_present"] is False
    assert payload["exchange_credentials_present"] is False
    assert payload["live_authority"] is False
    assert payload["testnet_authority"] is False
    assert payload["environment_class"] == "planning_only"
    output = payload["output_machine_lines"]
    assert output["REMOTE_HOST_INVENTORY_READY_FOR_IMPLEMENTATION_CHARTER"] is False
    assert output["REMOTE_HOST_INVENTORY_PROVISIONED"] is False
    assert output["REMOTE_HOST_INVENTORY_CONNECTED"] is False


def test_fixture_has_no_obvious_secret_account_or_ip_fields() -> None:
    raw = FIXTURE.read_text(encoding="utf-8")
    for pattern in FORBIDDEN_FIXTURE_PATTERNS:
        assert pattern.search(raw) is None, f"forbidden pattern matched: {pattern.pattern}"


def test_taxonomy_links_fixture() -> None:
    section = _section_6a03()
    assert "remote_host_inventory_planning_v0.json" in section


def test_no_duplicate_inventory_spec_introduced() -> None:
    specs_dir = REPO_ROOT / "docs/ops/specs"
    runbooks_dir = REPO_ROOT / "docs/ops/runbooks"
    for fragment in FORBIDDEN_DUPLICATE_SPEC_FRAGMENTS:
        assert list(specs_dir.glob(f"*{fragment}*")) == []
        assert list(runbooks_dir.glob(f"*{fragment}*")) == []
