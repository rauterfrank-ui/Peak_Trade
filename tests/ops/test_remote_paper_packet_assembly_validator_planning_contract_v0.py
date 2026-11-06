"""Static contract tests for Remote Paper Packet Assembly Validator Planning v0 (§6a.0.5)."""

from __future__ import annotations

import json
import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
TAXONOMY_SPEC = REPO_ROOT / "docs/ops/specs/RUNTIME_LANE_TAXONOMY_AUTHORITY_LEVELS_CONTRACT_V0.md"
PREFLIGHT = REPO_ROOT / "docs/ops/runbooks/PAPER_SHADOW_247_PREFLIGHT_CONTRACT_V0.md"
DOCS_TRUTH_MAP = REPO_ROOT / "docs/ops/registry/DOCS_TRUTH_MAP.md"
FIXTURE = (
    REPO_ROOT
    / "tests"
    / "fixtures"
    / "ops"
    / "remote_paper_packet_assembly_validator_planning_v0.json"
)
PACKET_FIXTURE = REPO_ROOT / "tests/fixtures/ops/remote_paper_approval_command_packet_v0.json"
INVENTORY_FIXTURE = REPO_ROOT / "tests/fixtures/ops/remote_host_inventory_planning_v0.json"
SAFETY_FIXTURE = REPO_ROOT / "tests/fixtures/ops/remote_cost_kill_orphan_safety_v0.json"

VALIDATOR_CONTRACT_MARKERS = (
    "REMOTE_PAPER_PACKET_ASSEMBLY_VALIDATOR_PLANNING_CONTRACT_V0=true",
    "REMOTE_PAPER_PACKET_VALIDATOR_PLANNING_ONLY=true",
    "REMOTE_PAPER_PACKET_VALIDATOR_NO_CLI_IMPLEMENTATION=true",
    "REMOTE_PAPER_PACKET_VALIDATOR_DO_NOT_RUN=true",
    "REMOTE_PAPER_PACKET_VALIDATOR_NO_RUNNER_IMPLEMENTATION=true",
    "REMOTE_PAPER_PACKET_VALIDATOR_NO_DRY_COMMAND_TEMPLATE=true",
    "REMOTE_PAPER_PACKET_VALIDATOR_NO_AWS_CLI=true",
    "REMOTE_PAPER_PACKET_VALIDATOR_NO_SSH=true",
    "REMOTE_PAPER_PACKET_VALIDATOR_NO_SYSTEMD=true",
    "REMOTE_PAPER_PACKET_VALIDATOR_NO_GHA_RUNNER=true",
    "REMOTE_PAPER_PACKET_VALIDATOR_NO_NETWORK=true",
    "REMOTE_PAPER_PACKET_VALIDATOR_NO_PROCESS_CONTROL=true",
    "REMOTE_PAPER_PACKET_VALIDATOR_REQUIRES_PREFLIGHT_JSON=true",
    "REMOTE_PAPER_PACKET_VALIDATOR_REQUIRES_APPROVAL_PACKET=true",
    "REMOTE_PAPER_PACKET_VALIDATOR_REQUIRES_HOST_INVENTORY=true",
    "REMOTE_PAPER_PACKET_VALIDATOR_REQUIRES_COST_KILL_ORPHAN_SAFETY=true",
    "REMOTE_PAPER_PACKET_VALIDATOR_REQUIRES_REGISTRY_V1=true",
    "REMOTE_PAPER_PACKET_VALIDATOR_S3_PREFIX_PLAN_OPTIONAL_NON_EXECUTING=true",
    "REMOTE_PAPER_PACKET_VALIDATOR_READY_FOR_IMPLEMENTATION_CHARTER=false",
    "REMOTE_PAPER_PACKET_VALIDATOR_READY_FOR_START=false",
    "REMOTE_PAPER_PACKET_VALIDATOR_READY_FOR_DRY_COMMAND_TEMPLATE=false",
)

FORBIDDEN_DUPLICATE_SPEC_FRAGMENTS = (
    "REMOTE_PAPER_PACKET_ASSEMBLY_VALIDATOR_PLANNING_CONTRACT_V0.md",
    "REMOTE_PAPER_PACKET_VALIDATOR_V0.md",
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


def _section_6a05() -> str:
    text = TAXONOMY_SPEC.read_text(encoding="utf-8")
    return text.split(
        "#### 6a.0.5 Remote paper packet assembly validator planning contract v0",
        1,
    )[1].split("### S3 / Object Storage", 1)[0]


def test_section_6a05_present_with_markers() -> None:
    text = TAXONOMY_SPEC.read_text(encoding="utf-8")
    assert "#### 6a.0.5 Remote paper packet assembly validator planning contract v0" in text
    for marker in VALIDATOR_CONTRACT_MARKERS:
        assert marker in text


def test_top_level_taxonomy_markers_include_validator_contract() -> None:
    text = TAXONOMY_SPEC.read_text(encoding="utf-8")
    assert (
        "REMOTE_PAPER_PACKET_ASSEMBLY_VALIDATOR_PLANNING_CONTRACT_V0=true"
        in text.split("## 2.", 1)[0]
    )


def test_planning_only_no_cli_or_runner() -> None:
    section = _section_6a05()
    assert "REMOTE_PAPER_PACKET_VALIDATOR_PLANNING_ONLY=true" in section
    assert "REMOTE_PAPER_PACKET_VALIDATOR_NO_CLI_IMPLEMENTATION=true" in section
    assert "REMOTE_PAPER_PACKET_VALIDATOR_NO_RUNNER_IMPLEMENTATION=true" in section
    assert "assembly-validator CLI" in section
    assert "§6a.0.6 owns the separate offline packet validator CLI" in section


def test_no_dry_command_template_and_blocked_gate() -> None:
    section = _section_6a05()
    assert "REMOTE_PAPER_PACKET_VALIDATOR_NO_DRY_COMMAND_TEMPLATE=true" in section
    assert "REMOTE_PAPER_PACKET_VALIDATOR_READY_FOR_DRY_COMMAND_TEMPLATE=false" in section
    assert "Dry command templates remain **blocked**" in section


def test_non_authorizing_boundaries() -> None:
    section = _section_6a05()
    assert "REMOTE_PAPER_PACKET_VALIDATOR_NOT_APPROVAL=true" in section
    assert "REMOTE_PAPER_PACKET_VALIDATOR_NOT_RUNTIME_START=true" in section
    assert "replace scheduler guard" in section
    assert "HOLD binding" in section
    assert "§2b.1" in section or "2b.1" in section


def test_required_bound_artifacts_documented() -> None:
    section = _section_6a05()
    assert "preflight_remote_runtime_runner_v0.py" in section
    assert "remote_paper_approval_command_packet_v0.json" in section
    assert "remote_host_inventory_planning_v0.json" in section
    assert "remote_cost_kill_orphan_safety_v0.json" in section
    assert "build_generic_evidence_run_registry_v1.py" in section
    assert "preflight_s3_finalized_evidence_export_v0.py" in section


def test_cross_artifact_consistency_fields_documented() -> None:
    section = _section_6a05()
    for field in (
        "remote_run_id",
        "runtime_host",
        "runtime_backend",
        "runtime_mode",
        "lane_id",
        "remote_host_id",
        "max_runtime_seconds",
        "evidence_root_type",
        "evidence_transport",
        "live_authority",
        "testnet_authority",
        "broker_credentials_present",
        "exchange_credentials_present",
    ):
        assert field in section


def test_output_machine_lines_documented() -> None:
    section = _section_6a05()
    assert "planning_valid" in section
    for line in (
        "REMOTE_PAPER_PACKET_VALIDATOR_RUNTIME_COMMANDS_CALLED",
        "REMOTE_PAPER_PACKET_VALIDATOR_AWS_CLI_CALLED",
        "REMOTE_PAPER_PACKET_VALIDATOR_NETWORK_CALLED",
        "REMOTE_PAPER_PACKET_VALIDATOR_SSH_CALLED",
        "REMOTE_PAPER_PACKET_VALIDATOR_SYSTEMD_CALLED",
        "REMOTE_PAPER_PACKET_VALIDATOR_PROCESS_CONTROL_CALLED",
        "REMOTE_PAPER_PACKET_VALIDATOR_HOST_TERMINATION_CALLED",
        "REMOTE_PAPER_PACKET_VALIDATOR_S3_UPLOAD_CALLED",
        "REMOTE_PAPER_PACKET_VALIDATOR_S3_DOWNLOAD_CALLED",
    ):
        assert line in section


def test_section_ordering_6a05_before_s3_subsection() -> None:
    text = TAXONOMY_SPEC.read_text(encoding="utf-8")
    assert text.index(
        "#### 6a.0.5 Remote paper packet assembly validator planning contract v0"
    ) < text.index("### S3 / Object Storage")
    assert text.index("#### 6a.0.4 Remote cost/kill/orphan safety contract v0") < text.index(
        "#### 6a.0.5 Remote paper packet assembly validator planning contract v0"
    )


def test_preflight_crosslinks_section_6a05() -> None:
    text = PREFLIGHT.read_text(encoding="utf-8")
    assert "§6a.0.5 Remote paper packet assembly validator planning contract v0" in text
    assert "REMOTE_PAPER_PACKET_VALIDATOR_READY_FOR_DRY_COMMAND_TEMPLATE=false" in text


def test_docs_truth_map_lists_section_6a05() -> None:
    text = DOCS_TRUTH_MAP.read_text(encoding="utf-8")
    assert "§6a.0.5" in text
    assert "Remote paper packet assembly validator planning contract v0" in text


def test_validator_fixture_exists_and_is_planning_only() -> None:
    assert FIXTURE.is_file()
    payload = json.loads(FIXTURE.read_text(encoding="utf-8"))
    assert payload["planning_only"] is True
    assert payload["do_not_run"] is True
    assert payload["no_cli_implementation"] is True
    assert payload["no_runner_implementation"] is True
    assert payload["no_dry_command_template"] is True
    assert payload["ready_for_implementation_charter"] is False
    assert payload["ready_for_start"] is False
    assert payload["ready_for_dry_command_template"] is False
    assert payload["runtime_commands_called"] is False
    assert payload["aws_cli_called"] is False
    assert payload["network_called"] is False
    assert payload["ssh_called"] is False
    assert payload["systemd_called"] is False
    assert payload["process_control_called"] is False
    assert payload["host_termination_called"] is False
    assert payload["s3_upload_called"] is False
    assert payload["s3_download_called"] is False


def test_validator_fixture_referenced_paths_exist() -> None:
    payload = json.loads(FIXTURE.read_text(encoding="utf-8"))
    for rel in payload["bound_artifacts"].values():
        if rel is None:
            continue
        path = REPO_ROOT / rel
        assert path.is_file(), rel


def test_validator_fixture_has_no_obvious_secret_account_or_ip_fields() -> None:
    raw = FIXTURE.read_text(encoding="utf-8")
    for pattern in FORBIDDEN_FIXTURE_PATTERNS:
        assert pattern.search(raw) is None, f"forbidden pattern matched: {pattern.pattern}"


def test_bound_fixtures_align_with_canonical_cross_artifact_fields() -> None:
    validator = json.loads(FIXTURE.read_text(encoding="utf-8"))
    canonical = validator["canonical_cross_artifact_fields"]
    packet = json.loads(PACKET_FIXTURE.read_text(encoding="utf-8"))
    inventory = json.loads(INVENTORY_FIXTURE.read_text(encoding="utf-8"))
    safety = json.loads(SAFETY_FIXTURE.read_text(encoding="utf-8"))

    assert packet["remote_run_id"] == canonical["remote_run_id"]
    assert safety["remote_run_id"] == canonical["remote_run_id"]
    assert inventory["remote_host_id"] == canonical["remote_host_id"]
    assert safety["remote_host_id"] == canonical["remote_host_id"]
    assert packet["runtime_backend"] == canonical["runtime_backend"]
    assert inventory["runtime_backend"] == canonical["runtime_backend"]
    assert safety["runtime_backend"] == canonical["runtime_backend"]
    assert packet["max_runtime_seconds"] == canonical["max_runtime_seconds"]
    assert safety["max_runtime_seconds"] == canonical["max_runtime_seconds"]
    assert packet["lane_id"] == canonical["lane_id"]
    assert packet["runtime_mode"] == canonical["runtime_mode"]
    assert packet["evidence_root_type"] == canonical["evidence_root_type"]
    assert packet["evidence_transport"] == canonical["evidence_transport"]


def test_taxonomy_links_validator_fixture() -> None:
    section = _section_6a05()
    assert "remote_paper_packet_assembly_validator_planning_v0.json" in section


def test_no_duplicate_validator_spec_introduced() -> None:
    specs_dir = REPO_ROOT / "docs/ops/specs"
    runbooks_dir = REPO_ROOT / "docs/ops/runbooks"
    for fragment in FORBIDDEN_DUPLICATE_SPEC_FRAGMENTS:
        assert list(specs_dir.glob(f"*{fragment}*")) == []
        assert list(runbooks_dir.glob(f"*{fragment}*")) == []
