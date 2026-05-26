"""Static contract tests for Remote Paper Validator CLI Planning v0 (§6a.0.6)."""

from __future__ import annotations

import json
import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
TAXONOMY_SPEC = REPO_ROOT / "docs/ops/specs/RUNTIME_LANE_TAXONOMY_AUTHORITY_LEVELS_CONTRACT_V0.md"
PREFLIGHT = REPO_ROOT / "docs/ops/runbooks/PAPER_SHADOW_247_PREFLIGHT_CONTRACT_V0.md"
DOCS_TRUTH_MAP = REPO_ROOT / "docs/ops/registry/DOCS_TRUTH_MAP.md"
FIXTURE = REPO_ROOT / "tests/fixtures/ops/remote_paper_validator_cli_planning_v0.json"
ASSEMBLY_FIXTURE = (
    REPO_ROOT / "tests/fixtures/ops/remote_paper_packet_assembly_validator_planning_v0.json"
)

CLI_CONTRACT_MARKERS = (
    "REMOTE_PAPER_VALIDATOR_CLI_PLANNING_CONTRACT_V0=true",
    "REMOTE_PAPER_VALIDATOR_CLI_PLANNING_ONLY=true",
    "REMOTE_PAPER_VALIDATOR_CLI_IMPLEMENTED=false",
    "REMOTE_PAPER_VALIDATOR_CLI_DO_NOT_RUN=true",
    "REMOTE_PAPER_VALIDATOR_CLI_NO_RUNTIME=true",
    "REMOTE_PAPER_VALIDATOR_CLI_NO_NETWORK=true",
    "REMOTE_PAPER_VALIDATOR_CLI_NO_AWS=true",
    "REMOTE_PAPER_VALIDATOR_CLI_NO_SSH=true",
    "REMOTE_PAPER_VALIDATOR_CLI_NO_SYSTEMD=true",
    "REMOTE_PAPER_VALIDATOR_CLI_NO_ARCHIVE_WALKER=true",
    "REMOTE_PAPER_VALIDATOR_CLI_NO_ARCHIVE_MUTATION=true",
    "REMOTE_PAPER_VALIDATOR_CLI_NO_DRY_COMMAND_TEMPLATE=true",
    "REMOTE_PAPER_VALIDATOR_CLI_NO_REMOTE_RUNNER=true",
    "REMOTE_PAPER_VALIDATOR_CLI_READY_FOR_IMPLEMENTATION=false",
    "REMOTE_PAPER_VALIDATOR_CLI_OUTPUT_STATUS_ENUM_PASS_BLOCKED_INVALID=true",
    "REMOTE_PAPER_VALIDATOR_CLI_PASS_DOES_NOT_AUTHORIZE_RUNTIME=true",
    "REMOTE_PAPER_VALIDATOR_CLI_PASS_DOES_NOT_AUTHORIZE_REMOTE_RUNNER=true",
    "REMOTE_PAPER_VALIDATOR_CLI_PASS_DOES_NOT_AUTHORIZE_LIVE=true",
    "REMOTE_PAPER_VALIDATOR_CLI_PASS_DOES_NOT_AUTHORIZE_TESTNET=true",
    "REMOTE_PAPER_VALIDATOR_CLI_IMPLEMENTATION_REQUIRES_OPERATOR_CHARTER=true",
)

IMPLEMENTED_CLI = REPO_ROOT / "scripts" / "ops" / "validate_remote_paper_packet_v0.py"

FORBIDDEN_DUPLICATE_SPEC_FRAGMENTS = (
    "REMOTE_PAPER_VALIDATOR_CLI_PLANNING_CONTRACT_V0.md",
    "REMOTE_PAPER_VALIDATOR_CLI_V0.md",
)

FORBIDDEN_FIXTURE_PATTERNS = (
    re.compile(r"\b\d{1,3}(?:\.\d{1,3}){3}\b"),
    re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
    re.compile(r"\barn:aws:", re.I),
    re.compile(r"\bi-[0-9a-f]{8,17}\b", re.I),
    re.compile(r"s3://", re.I),
    re.compile(r"-----BEGIN (?:RSA |OPENSSH )?PRIVATE KEY-----"),
)


def _section_6a06() -> str:
    text = TAXONOMY_SPEC.read_text(encoding="utf-8")
    return text.split("#### 6a.0.6 Remote paper validator CLI planning contract v0", 1)[1].split(
        "### S3 / Object Storage", 1
    )[0]


def test_section_6a06_present_with_markers() -> None:
    text = TAXONOMY_SPEC.read_text(encoding="utf-8")
    assert "#### 6a.0.6 Remote paper validator CLI planning contract v0" in text
    for marker in CLI_CONTRACT_MARKERS:
        assert marker in text


def test_top_level_taxonomy_markers_include_cli_planning_contract() -> None:
    text = TAXONOMY_SPEC.read_text(encoding="utf-8")
    assert "REMOTE_PAPER_VALIDATOR_CLI_PLANNING_CONTRACT_V0=true" in text.split("## 2.", 1)[0]


def test_planning_only_not_implemented_do_not_run() -> None:
    section = _section_6a06()
    assert "REMOTE_PAPER_VALIDATOR_CLI_PLANNING_ONLY=true" in section
    assert "REMOTE_PAPER_VALIDATOR_CLI_IMPLEMENTED=false" in section
    assert "REMOTE_PAPER_VALIDATOR_CLI_DO_NOT_RUN=true" in section
    assert "ship validator CLI source" in section
    assert "does **not**" in section or "not** ship" in section


def test_no_runtime_network_aws_ssh_systemd_archive() -> None:
    section = _section_6a06()
    assert "REMOTE_PAPER_VALIDATOR_CLI_NO_RUNTIME=true" in section
    assert "REMOTE_PAPER_VALIDATOR_CLI_NO_NETWORK=true" in section
    assert "REMOTE_PAPER_VALIDATOR_CLI_NO_AWS=true" in section
    assert "REMOTE_PAPER_VALIDATOR_CLI_NO_SSH=true" in section
    assert "REMOTE_PAPER_VALIDATOR_CLI_NO_SYSTEMD=true" in section
    assert "REMOTE_PAPER_VALIDATOR_CLI_NO_ARCHIVE_WALKER=true" in section
    assert "REMOTE_PAPER_VALIDATOR_CLI_NO_ARCHIVE_MUTATION=true" in section


def test_no_dry_command_template_or_remote_runner() -> None:
    section = _section_6a06()
    assert "REMOTE_PAPER_VALIDATOR_CLI_NO_DRY_COMMAND_TEMPLATE=true" in section
    assert "REMOTE_PAPER_VALIDATOR_CLI_NO_REMOTE_RUNNER=true" in section
    assert "no shell command emission" in section.lower()


def test_future_cli_input_shape_local_json_only() -> None:
    section = _section_6a06()
    assert "--preflight-json" in section
    assert "--approval-packet" in section
    assert "--host-inventory" in section
    assert "--cost-kill-orphan-safety" in section
    assert "--registry-json" in section
    assert "no automatic discovery" in section.lower()
    assert "Docker" in section


def test_future_cli_validations_documented() -> None:
    section = _section_6a06()
    assert "remote_run_id" in section
    assert "`paper` only" in section or "**`paper` only**" in section
    assert "paper_only" in section
    assert "remote_runtime` is not a lane" in section or "not a lane" in section
    assert "daemon_paper_24h" in section
    assert "BLOCKED" in section
    assert "DO_NOT_RUN" in section
    assert "§2b.1" in section
    assert "§2b.2" in section


def test_future_output_status_enum_and_pass_non_authorizing() -> None:
    section = _section_6a06()
    assert "REMOTE_PAPER_VALIDATOR_CLI_OUTPUT_STATUS_ENUM_PASS_BLOCKED_INVALID=true" in section
    assert "`PASS`" in section and "`BLOCKED`" in section and "`INVALID`" in section
    assert "REMOTE_PAPER_VALIDATOR_CLI_PASS_DOES_NOT_AUTHORIZE_RUNTIME=true" in section
    assert "REMOTE_PAPER_VALIDATOR_CLI_PASS_DOES_NOT_AUTHORIZE_REMOTE_RUNNER=true" in section
    assert "REMOTE_PAPER_VALIDATOR_CLI_PASS_DOES_NOT_AUTHORIZE_LIVE=true" in section
    assert "REMOTE_PAPER_VALIDATOR_CLI_PASS_DOES_NOT_AUTHORIZE_TESTNET=true" in section


def test_implementation_requires_operator_charter() -> None:
    section = _section_6a06()
    assert "REMOTE_PAPER_VALIDATOR_CLI_IMPLEMENTATION_REQUIRES_OPERATOR_CHARTER=true" in section
    assert "REMOTE_PAPER_VALIDATOR_CLI_READY_FOR_IMPLEMENTATION=false" in section


def test_binds_existing_contracts() -> None:
    section = _section_6a06()
    assert "§2a" in section
    assert "§2b.1" in section
    assert "§2b.2" in section
    assert "§6a.0.5" in section
    assert "§6a.3" in section


def test_section_ordering_6a06_after_6a05_before_s3() -> None:
    text = TAXONOMY_SPEC.read_text(encoding="utf-8")
    assert text.index(
        "#### 6a.0.5 Remote paper packet assembly validator planning contract v0"
    ) < text.index("#### 6a.0.6 Remote paper validator CLI planning contract v0")
    assert text.index("#### 6a.0.6 Remote paper validator CLI planning contract v0") < text.index(
        "### S3 / Object Storage"
    )


def test_preflight_crosslinks_section_6a06() -> None:
    text = PREFLIGHT.read_text(encoding="utf-8")
    assert "§6a.0.6 Remote paper validator CLI planning contract v0" in text
    assert "REMOTE_PAPER_VALIDATOR_CLI_IMPLEMENTED=false" in text


def test_docs_truth_map_lists_section_6a06() -> None:
    text = DOCS_TRUTH_MAP.read_text(encoding="utf-8")
    assert "§6a.0.6" in text
    assert "Remote paper validator CLI planning contract v0" in text


def test_cli_fixture_exists_and_is_planning_only() -> None:
    assert FIXTURE.is_file()
    payload = json.loads(FIXTURE.read_text(encoding="utf-8"))
    assert payload["planning_only"] is True
    assert payload["implemented"] is False
    assert payload["do_not_run"] is True
    assert payload["no_archive_walker"] is True
    assert payload["no_dry_command_template"] is True
    assert payload["no_remote_runner"] is True
    assert payload["ready_for_implementation"] is False
    assert payload["future_output_shape"]["emit_command_template"] is False
    assert payload["authority_flags"]["runtime_authorized"] is False
    assert payload["authority_flags"]["remote_runner_authorized"] is False


def test_cli_fixture_referenced_repo_paths_exist() -> None:
    payload = json.loads(FIXTURE.read_text(encoding="utf-8"))
    for key, rel in payload["input_paths"].items():
        if rel is None:
            continue
        path = REPO_ROOT / rel
        assert path.is_file(), f"{key}: {rel}"


def test_cli_fixture_has_no_obvious_secret_or_ip_fields() -> None:
    raw = FIXTURE.read_text(encoding="utf-8")
    for pattern in FORBIDDEN_FIXTURE_PATTERNS:
        assert pattern.search(raw) is None, f"forbidden pattern matched: {pattern.pattern}"


def test_taxonomy_links_cli_fixture() -> None:
    section = _section_6a06()
    assert "remote_paper_validator_cli_planning_v0.json" in section


def test_validator_cli_implementation_singleton() -> None:
    """OP-REMOTE-PAPER-VALIDATOR-CLI-IMPL-V0 allows exactly one offline CLI entrypoint."""
    assert IMPLEMENTED_CLI.is_file()
    ops = REPO_ROOT / "scripts" / "ops"
    matches = [
        path
        for path in ops.glob("*.py")
        if path.name.startswith("validate_remote_paper") and path.resolve() != IMPLEMENTED_CLI.resolve()
    ]
    assert matches == [], f"duplicate validator CLI scripts: {matches}"


def test_no_duplicate_cli_spec_introduced() -> None:
    specs_dir = REPO_ROOT / "docs/ops/specs"
    runbooks_dir = REPO_ROOT / "docs/ops/runbooks"
    for fragment in FORBIDDEN_DUPLICATE_SPEC_FRAGMENTS:
        if fragment.endswith(".md"):
            assert list(specs_dir.glob(f"*{fragment}*")) == []
            assert list(runbooks_dir.glob(f"*{fragment}*")) == []
    for fragment in FORBIDDEN_DUPLICATE_SPEC_FRAGMENTS:
        assert fragment.endswith(".md")


def test_assembly_fixture_still_present() -> None:
    assert ASSEMBLY_FIXTURE.is_file()
