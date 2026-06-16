"""Unit and static tests for validate_remote_paper_packet_v0 (OP-REMOTE-PAPER-VALIDATOR-CLI-IMPL-V0)."""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
CLI = REPO_ROOT / "scripts/ops/validate_remote_paper_packet_v0.py"
FIXTURES = REPO_ROOT / "tests/fixtures/ops"

PREFLIGHT = FIXTURES / "preflight_remote_paper_planning_pass_v0.json"
PACKET = FIXTURES / "remote_paper_approval_command_packet_v0.json"
INVENTORY = FIXTURES / "remote_host_inventory_planning_v0.json"
SAFETY = FIXTURES / "remote_cost_kill_orphan_safety_v0.json"
REGISTRY = FIXTURES / "registry_remote_paper_planning_row_v0.json"
ASSEMBLY = FIXTURES / "remote_paper_packet_assembly_validator_planning_v0.json"
VALIDATOR_PLANNING = FIXTURES / "remote_paper_validator_cli_planning_v0.json"
DRY_TEMPLATE_PLANNING = FIXTURES / "remote_paper_dry_command_template_planning_v0.json"

FORBIDDEN_SUBSTRINGS = (
    "aws ",
    "boto3",
    "rclone",
    "ssh ",
    "systemctl",
    "docker",
    "subprocess",
    "requests",
    "urllib",
    "socket",
    "Popen",
    "os.system",
)

FORBIDDEN_IMPORT_MARKERS = (
    "durable_closeout_copy_verify",
    "preflight_remote_runtime_runner",
    "market_dashboard",
    "notion",
    "scheduler",
    "from src.execution",
    "import execution",
)


def _load_cli():
    spec = importlib.util.spec_from_file_location("validate_remote_paper_packet_v0", CLI)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _cli_logic_source_text() -> str:
    text = CLI.read_text(encoding="utf-8")
    start = text.find("def load_json")
    end = text.find("def emit_machine_lines")
    if start != -1 and end != -1 and end > start:
        return text[start:end]
    return text


def _pass_args(
    *,
    preflight: Path = PREFLIGHT,
    packet: Path = PACKET,
    inventory: Path = INVENTORY,
    safety: Path = SAFETY,
    registry: Path = REGISTRY,
    extra: list[str] | None = None,
) -> list[str]:
    args = [
        "--preflight-json",
        str(preflight),
        "--approval-packet-json",
        str(packet),
        "--host-inventory-json",
        str(inventory),
        "--cost-kill-orphan-json",
        str(safety),
        "--registry-json",
        str(registry),
    ]
    if extra:
        args.extend(extra)
    return args


def _has_forbidden_command_template_key(value: object, *, parent_key: str | None = None) -> bool:
    if isinstance(value, dict):
        for key, child in value.items():
            if key == "command_template" and parent_key != "authority":
                return True
            if _has_forbidden_command_template_key(child, parent_key=key):
                return True
        return False
    if isinstance(value, list):
        return any(
            _has_forbidden_command_template_key(item, parent_key=parent_key) for item in value
        )
    return False


@pytest.fixture(scope="module")
def cli():
    return _load_cli()


def test_pass_consistent_fixture_set(cli, capsys):
    rc = cli.main(_pass_args())
    captured = capsys.readouterr()
    assert rc == 0
    assert "REMOTE_PAPER_VALIDATOR_CLI_STATUS=PASS" in captured.out
    assert "REMOTE_PAPER_VALIDATOR_CLI_PREFLIGHT_BLOCKED_LIFTED=false" in captured.out
    assert "REMOTE_PAPER_VALIDATOR_CLI_READY_FOR_START=false" in captured.out


def test_blocked_lane_not_paper(cli, tmp_path):
    packet = json.loads(PACKET.read_text(encoding="utf-8"))
    packet["lane_id"] = "shadow"
    packet_path = tmp_path / "packet.json"
    packet_path.write_text(json.dumps(packet), encoding="utf-8")
    rc = cli.main(_pass_args(packet=packet_path))
    assert rc == 2


def test_blocked_live_authority(cli, tmp_path):
    safety = json.loads(SAFETY.read_text(encoding="utf-8"))
    safety["live_authority"] = True
    safety_path = tmp_path / "safety.json"
    safety_path.write_text(json.dumps(safety), encoding="utf-8")
    rc = cli.main(_pass_args(safety=safety_path))
    assert rc == 2


def test_invalid_missing_file(cli, tmp_path):
    rc = cli.main(
        _pass_args(preflight=tmp_path / "missing_preflight.json"),
    )
    assert rc == 1


def test_invalid_malformed_json(cli, tmp_path):
    bad = tmp_path / "bad.json"
    bad.write_text("{not-json", encoding="utf-8")
    rc = cli.main(_pass_args(preflight=bad))
    assert rc == 1


def test_invalid_secret_pattern(cli, tmp_path):
    packet = json.loads(PACKET.read_text(encoding="utf-8"))
    packet["note"] = "s3://bucket/object"
    packet_path = tmp_path / "packet.json"
    packet_path.write_text(json.dumps(packet), encoding="utf-8")
    rc = cli.main(_pass_args(packet=packet_path))
    assert rc == 1


def test_json_output_contract(cli, capsys):
    rc = cli.main([*_pass_args(), "--json"])
    captured = capsys.readouterr()
    assert rc == 0
    payload = json.loads(captured.out.strip())
    assert set(payload.keys()) == {
        "schema_version",
        "status",
        "reasons",
        "checked_artifacts",
        "authority",
        "preflight_blocked_lifted",
        "ready_for_start",
    }
    assert payload["status"] == "PASS"
    assert payload["authority"]["runtime"] is False
    assert payload["authority"]["remote_runner_start"] is False
    assert payload["authority"]["testnet"] is False
    assert payload["authority"]["live"] is False
    assert payload["authority"]["command_template"] is False
    assert payload["preflight_blocked_lifted"] is False
    assert payload["ready_for_start"] is False
    assert not _has_forbidden_command_template_key(payload)


def test_no_command_template_in_output(cli, capsys):
    rc = cli.main([*_pass_args(), "--json"])
    captured = capsys.readouterr()
    assert rc == 0
    assert not _has_forbidden_command_template_key(json.loads(captured.out.strip()))


def test_input_command_template_invalid(cli, tmp_path):
    packet = json.loads(PACKET.read_text(encoding="utf-8"))
    packet["command_template"] = "echo forbidden"
    packet_path = tmp_path / "packet.json"
    packet_path.write_text(json.dumps(packet), encoding="utf-8")
    rc = cli.main(_pass_args(packet=packet_path))
    assert rc == 1


def test_ready_for_start_true_blocked(cli, tmp_path):
    packet = json.loads(PACKET.read_text(encoding="utf-8"))
    packet["ready_for_start"] = True
    packet_path = tmp_path / "packet.json"
    packet_path.write_text(json.dumps(packet), encoding="utf-8")
    rc = cli.main(_pass_args(packet=packet_path))
    assert rc == 2


def test_remote_run_id_mismatch_invalid(cli, tmp_path):
    safety = json.loads(SAFETY.read_text(encoding="utf-8"))
    safety["remote_run_id"] = "other_run_id"
    safety_path = tmp_path / "safety.json"
    safety_path.write_text(json.dumps(safety), encoding="utf-8")
    rc = cli.main(_pass_args(safety=safety_path))
    assert rc == 1


def test_static_forbidden_substrings_absent():
    lower = _cli_logic_source_text().lower()
    for token in FORBIDDEN_SUBSTRINGS:
        assert token.lower() not in lower, f"forbidden token: {token!r}"


def test_static_forbidden_import_markers_absent():
    text = CLI.read_text(encoding="utf-8")
    for marker in FORBIDDEN_IMPORT_MARKERS:
        assert marker not in text


def test_no_file_write_flags():
    text = CLI.read_text(encoding="utf-8")
    assert "--output" not in text
    assert "write_text" not in text
    assert "write_bytes" not in text


def test_adjacent_planning_fixtures_remain_non_authorizing():
    packet = json.loads(PACKET.read_text(encoding="utf-8"))
    assert "command_template" not in packet
    validator_planning = json.loads(VALIDATOR_PLANNING.read_text(encoding="utf-8"))
    assert validator_planning["future_output_shape"]["emit_command_template"] is False
    dry_planning = json.loads(DRY_TEMPLATE_PLANNING.read_text(encoding="utf-8"))
    assert dry_planning["execution_permitted"] is False


def test_blocked_closeout_complete_without_proof(cli, tmp_path):
    closeout = tmp_path / "closeout.json"
    closeout.write_text(
        json.dumps({"closeout_complete": True}),
        encoding="utf-8",
    )
    rc = cli.main(
        [
            *_pass_args(),
            "--closeout-metadata-json",
            str(closeout),
        ]
    )
    assert rc == 2
