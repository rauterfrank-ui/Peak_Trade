"""Static contract tests for Remote Paper Approval/Command Packet v0 (taxonomy §6a.0.2)."""

from __future__ import annotations

import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
TAXONOMY_SPEC = (
    REPO_ROOT / "docs" / "ops" / "specs" / "RUNTIME_LANE_TAXONOMY_AUTHORITY_LEVELS_CONTRACT_V0.md"
)
PREFLIGHT = REPO_ROOT / "docs" / "ops" / "runbooks" / "PAPER_SHADOW_247_PREFLIGHT_CONTRACT_V0.md"
DOCS_TRUTH_MAP = REPO_ROOT / "docs" / "ops" / "registry" / "DOCS_TRUTH_MAP.md"
FIXTURE = REPO_ROOT / "tests" / "fixtures" / "ops" / "remote_paper_approval_command_packet_v0.json"

PACKET_CONTRACT_MARKERS = (
    "REMOTE_PAPER_APPROVAL_COMMAND_PACKET_CONTRACT_V0=true",
    "REMOTE_PAPER_APPROVAL_COMMAND_PACKET_DOCS_TESTS_ONLY=true",
    "REMOTE_PAPER_PACKET_NON_EXECUTABLE=true",
    "REMOTE_PAPER_PACKET_DO_NOT_RUN=true",
    "REMOTE_PAPER_PACKET_RUNNER_IMPLEMENTED=false",
    "REMOTE_PAPER_PACKET_APPROVE_REMOTE_RUNNER_START_NOW=false",
    "REMOTE_PAPER_PACKET_LANE_ID_REQUIRED=paper",
    "REMOTE_PAPER_PACKET_REMOTE_RUNTIME_BACKEND_NOT_LANE=true",
    "REMOTE_PAPER_PACKET_LANE_ID_REMOTE_RUNTIME_FORBIDDEN=true",
    "REMOTE_PAPER_PACKET_LANE_ID_DAEMON_PAPER_24H_NOT_LANE=true",
    "REMOTE_PAPER_PACKET_SHADOW_DEFAULT_FORBIDDEN=true",
    "REMOTE_PAPER_PACKET_TESTNET_FORBIDDEN=true",
    "REMOTE_PAPER_PACKET_LIVE_FORBIDDEN=true",
    "REMOTE_PAPER_PACKET_BROKER_CREDENTIALS_FORBIDDEN=true",
    "REMOTE_PAPER_PACKET_AWS_RCLONE_NETWORK_EXECUTION_FORBIDDEN=true",
    "REMOTE_PAPER_PACKET_SSH_SYSTEMD_GHA_RUNNER_FORBIDDEN=true",
    "REMOTE_PAPER_PACKET_REQUIRES_PREFLIGHT_JSON=true",
    "REMOTE_PAPER_PACKET_REQUIRES_SCHEDULER_GUARD=true",
    "REMOTE_PAPER_PACKET_REQUIRES_HOLD_BINDING=true",
    "REMOTE_PAPER_PACKET_REQUIRES_BOUNDED_ADAPTER_APPROVAL=true",
    "REMOTE_PAPER_PACKET_REQUIRES_REGISTRY_V1=true",
    "REMOTE_PAPER_PACKET_REQUIRES_PRIMARY_EVIDENCE_RETENTION=true",
    "REMOTE_PAPER_PACKET_REQUIRES_MANDATORY_DURABLE_CLOSEOUT=true",
    "REMOTE_PAPER_PACKET_S3_PREFIX_PLAN_OPTIONAL_NON_EXECUTING=true",
    "REMOTE_PAPER_PACKET_NOTION_PROJECTION_ONLY=true",
    "REMOTE_PAPER_PACKET_MARKET_DASHBOARD_PROJECTION_ONLY=true",
    "REMOTE_PAPER_PACKET_READY_FOR_START=false",
)

FORBIDDEN_DUPLICATE_SPEC_FRAGMENTS = (
    "REMOTE_PAPER_APPROVAL_COMMAND_PACKET_CONTRACT_V0.md",
    "REMOTE_PAPER_COMMAND_PACKET_V0.md",
)


def _section_6a02() -> str:
    text = TAXONOMY_SPEC.read_text(encoding="utf-8")
    return text.split("#### 6a.0.2 Remote paper approval/command packet contract v0", 1)[1].split(
        "### S3 / Object Storage", 1
    )[0]


def test_section_6a02_present_with_markers() -> None:
    text = TAXONOMY_SPEC.read_text(encoding="utf-8")
    assert "#### 6a.0.2 Remote paper approval/command packet contract v0" in text
    for marker in PACKET_CONTRACT_MARKERS:
        assert marker in text


def test_top_level_taxonomy_markers_include_packet_contract() -> None:
    text = TAXONOMY_SPEC.read_text(encoding="utf-8")
    assert "REMOTE_PAPER_APPROVAL_COMMAND_PACKET_CONTRACT_V0=true" in text.split("## 2.", 1)[0]


def test_paper_only_and_backend_not_lane() -> None:
    section = _section_6a02()
    assert "REMOTE_PAPER_PACKET_LANE_ID_REQUIRED=paper" in section
    assert "REMOTE_PAPER_PACKET_REMOTE_RUNTIME_BACKEND_NOT_LANE=true" in section
    assert "lane_id=remote_runtime" in section
    assert "lane_id=daemon_paper_24h" in section


def test_non_executable_posture() -> None:
    section = _section_6a02()
    assert "REMOTE_PAPER_PACKET_NON_EXECUTABLE=true" in section
    assert "REMOTE_PAPER_PACKET_DO_NOT_RUN=true" in section
    assert "REMOTE_PAPER_PACKET_RUNNER_IMPLEMENTED=false" in section
    assert "REMOTE_PAPER_PACKET_APPROVE_REMOTE_RUNNER_START_NOW=false" in section
    assert "ship packet assembly CLI" in section
    assert "dry command template" in section.lower()


def test_required_input_pointers_documented() -> None:
    section = _section_6a02()
    assert "preflight_remote_runtime_runner_v0.py" in section
    assert "scheduler_start_boundary_guard_v0.py" in section
    assert "paper_shadow_247_scheduler_hold_runtime_binding_v0.py" in section
    assert "run_paper_only_bounded_observation_adapter_v0.py" in section
    assert "build_generic_evidence_run_registry_v1.py" in section
    assert "primary_evidence_retention_v0.py" in section
    assert "§2b.1" in section or "2b.1" in section
    assert "preflight_s3_finalized_evidence_export_v0.py" in section


def test_not_new_approval_authority() -> None:
    section = _section_6a02()
    assert "REMOTE_PAPER_PACKET_NOT_NEW_APPROVAL_AUTHORITY=true" in section
    assert "extends" in section.lower()
    assert "not** a new approval authority" in section or "not a new approval authority" in section


def test_output_machine_lines_documented() -> None:
    section = _section_6a02()
    assert "prepared_not_executable" in section
    assert "REMOTE_PAPER_PACKET_READY_FOR_IMPLEMENTATION_REVIEW" in section
    assert "REMOTE_PAPER_PACKET_READY_FOR_START" in section
    assert "REMOTE_PAPER_PACKET_OPERATOR_APPROVAL_REQUIRED" in section
    for line in (
        "REMOTE_PAPER_PACKET_RUNTIME_COMMANDS_CALLED",
        "REMOTE_PAPER_PACKET_AWS_CLI_CALLED",
        "REMOTE_PAPER_PACKET_NETWORK_CALLED",
        "REMOTE_PAPER_PACKET_SSH_CALLED",
        "REMOTE_PAPER_PACKET_SYSTEMD_CALLED",
        "REMOTE_PAPER_PACKET_S3_UPLOAD_CALLED",
        "REMOTE_PAPER_PACKET_S3_DOWNLOAD_CALLED",
    ):
        assert line in section


def test_notion_and_dashboard_projection_only() -> None:
    section = _section_6a02()
    assert "REMOTE_PAPER_PACKET_NOTION_PROJECTION_ONLY=true" in section
    assert "REMOTE_PAPER_PACKET_MARKET_DASHBOARD_PROJECTION_ONLY=true" in section
    assert "§6a.1" in section
    assert "§6a.2" in section


def test_s3_optional_prefix_plan_non_executing() -> None:
    section = _section_6a02()
    assert "REMOTE_PAPER_PACKET_S3_PREFIX_PLAN_OPTIONAL_NON_EXECUTING=true" in section
    assert (
        "upload does **not** authorize" in section
        or "does not authorize runtime" in section.lower()
    )


def test_section_ordering_6a02_before_s3_subsection() -> None:
    text = TAXONOMY_SPEC.read_text(encoding="utf-8")
    assert text.index("#### 6a.0.2 Remote paper approval/command packet contract v0") < text.index(
        "### S3 / Object Storage"
    )
    assert text.index("#### 6a.0.1 Local remote runner preflight v0") < text.index(
        "#### 6a.0.2 Remote paper approval/command packet contract v0"
    )


def test_preflight_crosslinks_section_6a02() -> None:
    text = PREFLIGHT.read_text(encoding="utf-8")
    assert "§6a.0.2 Remote paper approval/command packet contract v0" in text
    assert "REMOTE_PAPER_PACKET_READY_FOR_START=false" in text


def test_docs_truth_map_lists_section_6a02() -> None:
    text = DOCS_TRUTH_MAP.read_text(encoding="utf-8")
    assert "§6a.0.2" in text
    assert "Remote paper approval/command packet contract v0" in text


def test_fixture_exists_and_is_non_executable() -> None:
    assert FIXTURE.is_file()
    payload = json.loads(FIXTURE.read_text(encoding="utf-8"))
    assert payload["do_not_run"] is True
    assert payload["approve_remote_runner_start_now"] is False
    assert payload["runner_implemented"] is False
    assert payload["lane_id"] == "paper"
    assert payload["runtime_mode"] == "paper_only"
    assert payload["runtime_host"] == "remote"
    output = payload["output_machine_lines"]
    assert output["REMOTE_PAPER_PACKET_READY_FOR_START"] is False
    assert output["REMOTE_PAPER_PACKET_RUNTIME_COMMANDS_CALLED"] is False
    assert output["REMOTE_PAPER_PACKET_AWS_CLI_CALLED"] is False
    assert output["REMOTE_PAPER_PACKET_NETWORK_CALLED"] is False
    assert output["REMOTE_PAPER_PACKET_SSH_CALLED"] is False
    assert output["REMOTE_PAPER_PACKET_SYSTEMD_CALLED"] is False
    assert output["REMOTE_PAPER_PACKET_S3_UPLOAD_CALLED"] is False
    assert output["REMOTE_PAPER_PACKET_S3_DOWNLOAD_CALLED"] is False


def test_fixture_references_canonical_owners() -> None:
    payload = json.loads(FIXTURE.read_text(encoding="utf-8"))
    pointers = payload["input_pointers"]
    assert "preflight_remote_runtime_runner_v0_json" in pointers
    assert "scheduler_guard_snapshot" in pointers
    assert "hold_binding" in pointers
    assert "bounded_adapter_approval_record" in pointers
    assert "registry_v1_row" in pointers
    assert "primary_evidence_retention_contract" in pointers
    assert "mandatory_durable_closeout_contract" in pointers


def test_taxonomy_links_fixture() -> None:
    section = _section_6a02()
    assert "remote_paper_approval_command_packet_v0.json" in section


def test_no_duplicate_packet_spec_introduced() -> None:
    specs_dir = REPO_ROOT / "docs" / "ops" / "specs"
    runbooks_dir = REPO_ROOT / "docs" / "ops" / "runbooks"
    for fragment in FORBIDDEN_DUPLICATE_SPEC_FRAGMENTS:
        assert list(specs_dir.glob(f"*{fragment}*")) == []
        assert list(runbooks_dir.glob(f"*{fragment}*")) == []
