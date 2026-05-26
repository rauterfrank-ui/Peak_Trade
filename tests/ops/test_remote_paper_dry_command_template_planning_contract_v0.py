"""Static contract tests for Remote Paper Dry Command Template Planning v0 (§6a.0.7)."""

from __future__ import annotations

import json
import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
TAXONOMY_SPEC = REPO_ROOT / "docs/ops/specs/RUNTIME_LANE_TAXONOMY_AUTHORITY_LEVELS_CONTRACT_V0.md"
PREFLIGHT = REPO_ROOT / "docs/ops/runbooks/PAPER_SHADOW_247_PREFLIGHT_CONTRACT_V0.md"
DOCS_TRUTH_MAP = REPO_ROOT / "docs/ops/registry/DOCS_TRUTH_MAP.md"
FIXTURE = REPO_ROOT / "tests/fixtures/ops/remote_paper_dry_command_template_planning_v0.json"
APPROVAL_PACKET_FIXTURE = (
    REPO_ROOT / "tests/fixtures/ops/remote_paper_approval_command_packet_v0.json"
)
VALIDATOR_CLI_FIXTURE = REPO_ROOT / "tests/fixtures/ops/remote_paper_validator_cli_planning_v0.json"
ASSEMBLY_FIXTURE = (
    REPO_ROOT / "tests/fixtures/ops/remote_paper_packet_assembly_validator_planning_v0.json"
)

TEMPLATE_CONTRACT_MARKERS = (
    "REMOTE_PAPER_DRY_COMMAND_TEMPLATE_PLANNING_CONTRACT_V0=true",
    "REMOTE_PAPER_DRY_COMMAND_TEMPLATE_PLANNING_CONTRACT_DOCS_TESTS_ONLY=true",
    "DRY_COMMAND_TEMPLATE_PLANNING_ONLY=true",
    "DRY_COMMAND_TEMPLATE_DO_NOT_RUN=true",
    "DRY_COMMAND_TEMPLATE_NON_EXECUTABLE=true",
    "DRY_COMMAND_TEMPLATE_EXECUTION_PERMITTED=false",
    "DRY_COMMAND_TEMPLATE_READY_FOR_START=false",
    "DRY_COMMAND_TEMPLATE_PLANNING_ARTIFACT_PRESENT=true",
    "DRY_COMMAND_TEMPLATE_NOT_IN_APPROVAL_PACKET=true",
    "DRY_COMMAND_TEMPLATE_NOT_EMITTED_BY_VALIDATOR_CLI=true",
    "DRY_COMMAND_TEMPLATE_PREFLIGHT_BLOCKED_UNCHANGED=true",
    "DRY_COMMAND_TEMPLATE_NO_RUNTIME=true",
    "DRY_COMMAND_TEMPLATE_NO_NETWORK=true",
    "DRY_COMMAND_TEMPLATE_NO_AWS=true",
    "DRY_COMMAND_TEMPLATE_NO_SSH=true",
    "DRY_COMMAND_TEMPLATE_NO_SYSTEMD=true",
    "DRY_COMMAND_TEMPLATE_NO_GHA_RUNNER=true",
    "DRY_COMMAND_TEMPLATE_NO_RCLONE=true",
    "DRY_COMMAND_TEMPLATE_NO_DOCKER=true",
    "DRY_COMMAND_TEMPLATE_NO_PROCESS_CONTROL=true",
    "DRY_COMMAND_TEMPLATE_NO_REMOTE_RUNNER=true",
    "DRY_COMMAND_TEMPLATE_NO_VALIDATOR_CLI_IMPLEMENTATION=true",
    "DRY_COMMAND_TEMPLATE_NO_CLOSEOUT_HELPER_IMPLEMENTATION=true",
)

FORBIDDEN_DUPLICATE_SPEC_FRAGMENTS = (
    "REMOTE_PAPER_DRY_COMMAND_TEMPLATE_V0.md",
    "REMOTE_PAPER_DRY_COMMAND_TEMPLATE_PLANNING_CONTRACT_V0.md",
)

FORBIDDEN_FIXTURE_SUBSTRINGS = (
    "aws ",
    "aws-cli",
    "arn:aws:",
    "ssh ",
    "scp ",
    "systemctl",
    "rclone",
    "curl ",
    "wget ",
    "docker",
    "podman",
    "gh runner",
    "launchctl",
    "#!/",
    "#!/bin",
    "chmod +x",
    "s3://",
    "AKIA",
)

FORBIDDEN_FIXTURE_PATTERNS = (
    re.compile(r"\b\d{1,3}(?:\.\d{1,3}){3}\b"),
    re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
    re.compile(r"\barn:aws:", re.I),
    re.compile(r"s3://", re.I),
)


def _section_6a07() -> str:
    text = TAXONOMY_SPEC.read_text(encoding="utf-8")
    return text.split(
        "#### 6a.0.7 Remote paper dry command template planning contract v0 (planning-only)",
        1,
    )[1].split("### S3 / Object Storage", 1)[0]


def test_section_6a07_present_with_markers() -> None:
    text = TAXONOMY_SPEC.read_text(encoding="utf-8")
    assert "#### 6a.0.7 Remote paper dry command template planning contract v0" in text
    for marker in TEMPLATE_CONTRACT_MARKERS:
        assert marker in text


def test_top_level_taxonomy_markers_include_dry_command_template_contract() -> None:
    text = TAXONOMY_SPEC.read_text(encoding="utf-8")
    assert (
        "REMOTE_PAPER_DRY_COMMAND_TEMPLATE_PLANNING_CONTRACT_V0=true" in text.split("## 2.", 1)[0]
    )


def test_planning_only_non_executable_do_not_run() -> None:
    section = _section_6a07()
    assert "DRY_COMMAND_TEMPLATE_PLANNING_ONLY=true" in section
    assert "DRY_COMMAND_TEMPLATE_NON_EXECUTABLE=true" in section
    assert "DRY_COMMAND_TEMPLATE_DO_NOT_RUN=true" in section
    assert "**does not** ship runnable templates" in section


def test_execution_and_start_forbidden() -> None:
    section = _section_6a07()
    assert "DRY_COMMAND_TEMPLATE_EXECUTION_PERMITTED=false" in section
    assert "DRY_COMMAND_TEMPLATE_READY_FOR_START=false" in section
    assert "DRY_COMMAND_TEMPLATE_PREFLIGHT_BLOCKED_UNCHANGED=true" in section


def test_not_in_packet_not_emitted_by_validator_cli() -> None:
    section = _section_6a07()
    assert "DRY_COMMAND_TEMPLATE_NOT_IN_APPROVAL_PACKET=true" in section
    assert "DRY_COMMAND_TEMPLATE_NOT_EMITTED_BY_VALIDATOR_CLI=true" in section
    assert "remote_paper_dry_command_template_planning_v0.json" in section


def test_fixture_exists_and_required_fields() -> None:
    assert FIXTURE.is_file()
    payload = json.loads(FIXTURE.read_text(encoding="utf-8"))
    assert payload["schema_version"] == "peak_trade.remote_paper_dry_command_template_planning.v0"
    assert payload["planning_only"] is True
    assert payload["do_not_run"] is True
    assert payload["non_executable"] is True
    assert payload["execution_permitted"] is False
    assert payload["ready_for_start"] is False
    assert payload["command_template_absent_from_approval_packet"] is True
    assert payload["command_template_absent_from_validator_output"] is True
    assert payload["placeholder_only"] is True
    assert payload["boundaries"]["preflight_blocked_lifted"] is False


def test_illustrative_steps_have_no_executable_command_or_authority() -> None:
    payload = json.loads(FIXTURE.read_text(encoding="utf-8"))
    for step in payload["illustrative_steps"]:
        assert step["mode"] == "operator_manual_review_only"
        assert step["executable_command"] is None
        assert step["command_line"] is None
        assert step["starts_runtime"] is False
        assert step["authority"] is False


def test_fixture_forbidden_substrings_absent() -> None:
    raw = FIXTURE.read_text(encoding="utf-8").lower()
    for token in FORBIDDEN_FIXTURE_SUBSTRINGS:
        assert token.lower() not in raw, f"forbidden substring: {token!r}"


def test_fixture_forbidden_patterns_absent() -> None:
    raw = FIXTURE.read_text(encoding="utf-8")
    for pattern in FORBIDDEN_FIXTURE_PATTERNS:
        assert pattern.search(raw) is None, f"forbidden pattern: {pattern.pattern}"


def test_approval_packet_has_no_command_template_field() -> None:
    raw = APPROVAL_PACKET_FIXTURE.read_text(encoding="utf-8")
    assert "command_template" not in raw


def test_validator_cli_fixture_no_template_emission() -> None:
    payload = json.loads(VALIDATOR_CLI_FIXTURE.read_text(encoding="utf-8"))
    assert payload["no_dry_command_template"] is True
    assert payload["future_output_shape"]["emit_command_template"] is False


def test_assembly_fixture_still_blocks_dry_command_template() -> None:
    payload = json.loads(ASSEMBLY_FIXTURE.read_text(encoding="utf-8"))
    assert payload["no_dry_command_template"] is True
    assert payload["ready_for_dry_command_template"] is False


def test_no_duplicate_root_spec_introduced() -> None:
    specs_dir = REPO_ROOT / "docs/ops/specs"
    runbooks_dir = REPO_ROOT / "docs/ops/runbooks"
    for fragment in FORBIDDEN_DUPLICATE_SPEC_FRAGMENTS:
        assert list(specs_dir.glob(f"*{fragment}*")) == []
        assert list(runbooks_dir.glob(f"*{fragment}*")) == []


def test_no_dry_command_template_script_in_ops() -> None:
    ops = REPO_ROOT / "scripts/ops"
    matches = [p for p in ops.glob("*dry*command*template*.py") if p.is_file()]
    assert matches == []


def test_section_ordering_6a07_after_6a06_before_s3() -> None:
    text = TAXONOMY_SPEC.read_text(encoding="utf-8")
    assert text.index("#### 6a.0.6 Remote paper validator CLI planning contract v0") < text.index(
        "#### 6a.0.7 Remote paper dry command template planning contract v0"
    )
    assert text.index(
        "#### 6a.0.7 Remote paper dry command template planning contract v0"
    ) < text.index("### S3 / Object Storage")


def test_preflight_crosslinks_section_6a07() -> None:
    text = PREFLIGHT.read_text(encoding="utf-8")
    assert "§6a.0.7 Remote paper dry command template planning contract v0" in text
    assert "DRY_COMMAND_TEMPLATE_EXECUTION_PERMITTED=false" in text


def test_docs_truth_map_lists_section_6a07() -> None:
    text = DOCS_TRUTH_MAP.read_text(encoding="utf-8")
    assert "§6a.0.7" in text
    assert "dry command template planning contract v0" in text.lower()
