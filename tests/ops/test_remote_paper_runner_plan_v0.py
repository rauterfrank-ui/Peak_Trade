"""Unit and static tests for remote_paper_runner_plan_v0 (OP-REMOTE-PAPER-RUNNER-IMPL-V0 Stufe 2)."""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
CLI = REPO_ROOT / "scripts/ops/remote_paper_runner_plan_v0.py"
OPS_DIR = REPO_ROOT / "scripts/ops"
FIXTURES = REPO_ROOT / "tests/fixtures/ops"

PREFLIGHT = FIXTURES / "preflight_remote_paper_planning_pass_v0.json"
PACKET = FIXTURES / "remote_paper_approval_command_packet_v0.json"
INVENTORY = FIXTURES / "remote_host_inventory_planning_v0.json"
SAFETY = FIXTURES / "remote_cost_kill_orphan_safety_v0.json"
REGISTRY = FIXTURES / "registry_remote_paper_planning_row_v0.json"
ASSEMBLY = FIXTURES / "remote_paper_packet_assembly_validator_planning_v0.json"

FORBIDDEN_SUBSTRINGS = (
    "subprocess",
    "Popen",
    "os.system",
    "socket",
    "requests",
    "urllib",
    "boto3",
    "botocore",
    "paramiko",
    "fabric",
    "rclone",
    "aws ",
    "aws_cli",
    "ssh ",
    "systemctl",
    "docker",
    "podman",
    "curl",
    "wget",
    "httpx",
    "aiohttp",
)

FORBIDDEN_IMPORT_MARKERS = (
    "durable_closeout_copy_verify",
    "preflight_remote_runtime_runner",
    "market_dashboard",
    "notion",
    "from src.execution",
    "import execution",
)


def _load_cli():
    spec = importlib.util.spec_from_file_location("remote_paper_runner_plan_v0", CLI)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


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


def test_planning_valid_aligned_fixtures(cli, capsys):
    rc = cli.main(_pass_args())
    captured = capsys.readouterr()
    assert rc == 0
    assert "REMOTE_PAPER_RUNNER_STATUS=planning_valid" in captured.out
    assert "REMOTE_PAPER_RUNNER_START_PERMITTED=false" in captured.out
    assert "REMOTE_PAPER_RUNNER_PLANNING_VALID_NON_AUTHORIZING=true" in captured.out


def test_planning_valid_with_optional_assembly(cli, capsys):
    rc = cli.main(
        _pass_args(extra=["--assembly-validator-json", str(ASSEMBLY)]),
    )
    captured = capsys.readouterr()
    assert rc == 0
    assert "REMOTE_PAPER_RUNNER_STATUS=planning_valid" in captured.out


def test_blocked_missing_max_runtime_seconds(cli, tmp_path):
    safety = json.loads(SAFETY.read_text(encoding="utf-8"))
    del safety["max_runtime_seconds"]
    safety_path = tmp_path / "safety.json"
    safety_path.write_text(json.dumps(safety), encoding="utf-8")
    rc = cli.main(_pass_args(safety=safety_path))
    assert rc == 2


def test_blocked_max_runtime_seconds_zero(cli, tmp_path):
    safety = json.loads(SAFETY.read_text(encoding="utf-8"))
    safety["max_runtime_seconds"] = 0
    safety_path = tmp_path / "safety.json"
    safety_path.write_text(json.dumps(safety), encoding="utf-8")
    rc = cli.main(_pass_args(safety=safety_path))
    assert rc == 2


def test_blocked_missing_expected_cost_ceiling(cli, tmp_path):
    safety = json.loads(SAFETY.read_text(encoding="utf-8"))
    del safety["expected_cost_ceiling"]
    safety_path = tmp_path / "safety.json"
    safety_path.write_text(json.dumps(safety), encoding="utf-8")
    rc = cli.main(_pass_args(safety=safety_path))
    assert rc == 2


def test_blocked_live_authority(cli, tmp_path):
    safety = json.loads(SAFETY.read_text(encoding="utf-8"))
    safety["live_authority"] = True
    safety_path = tmp_path / "safety.json"
    safety_path.write_text(json.dumps(safety), encoding="utf-8")
    rc = cli.main(_pass_args(safety=safety_path))
    assert rc == 2


def test_blocked_testnet_authority(cli, tmp_path):
    safety = json.loads(SAFETY.read_text(encoding="utf-8"))
    safety["testnet_authority"] = True
    safety_path = tmp_path / "safety.json"
    safety_path.write_text(json.dumps(safety), encoding="utf-8")
    rc = cli.main(_pass_args(safety=safety_path))
    assert rc == 2


def test_blocked_broker_credentials(cli, tmp_path):
    inventory = json.loads(INVENTORY.read_text(encoding="utf-8"))
    inventory["broker_credentials_present"] = True
    inventory_path = tmp_path / "inventory.json"
    inventory_path.write_text(json.dumps(inventory), encoding="utf-8")
    rc = cli.main(_pass_args(inventory=inventory_path))
    assert rc == 2


def test_blocked_exchange_credentials(cli, tmp_path):
    safety = json.loads(SAFETY.read_text(encoding="utf-8"))
    safety["exchange_credentials_present"] = True
    safety_path = tmp_path / "safety.json"
    safety_path.write_text(json.dumps(safety), encoding="utf-8")
    rc = cli.main(_pass_args(safety=safety_path))
    assert rc == 2


def test_blocked_lane_not_paper(cli, tmp_path):
    packet = json.loads(PACKET.read_text(encoding="utf-8"))
    packet["lane_id"] = "shadow"
    packet_path = tmp_path / "packet.json"
    packet_path.write_text(json.dumps(packet), encoding="utf-8")
    rc = cli.main(_pass_args(packet=packet_path))
    assert rc == 2


def test_invalid_ready_for_start(cli, tmp_path):
    packet = json.loads(PACKET.read_text(encoding="utf-8"))
    packet["ready_for_start"] = True
    packet_path = tmp_path / "packet.json"
    packet_path.write_text(json.dumps(packet), encoding="utf-8")
    rc = cli.main(_pass_args(packet=packet_path))
    assert rc == 1


def test_invalid_preflight_blocked_lifted(cli, tmp_path):
    preflight = json.loads(PREFLIGHT.read_text(encoding="utf-8"))
    preflight["preflight_blocked_lifted"] = True
    preflight_path = tmp_path / "preflight.json"
    preflight_path.write_text(json.dumps(preflight), encoding="utf-8")
    rc = cli.main(_pass_args(preflight=preflight_path))
    assert rc == 1


def test_invalid_approve_remote_runner_start_now(cli, tmp_path):
    packet = json.loads(PACKET.read_text(encoding="utf-8"))
    packet["approve_remote_runner_start_now"] = True
    packet_path = tmp_path / "packet.json"
    packet_path.write_text(json.dumps(packet), encoding="utf-8")
    rc = cli.main(_pass_args(packet=packet_path))
    assert rc == 1


def test_invalid_command_template(cli, tmp_path):
    packet = json.loads(PACKET.read_text(encoding="utf-8"))
    packet["command_template"] = "echo forbidden"
    packet_path = tmp_path / "packet.json"
    packet_path.write_text(json.dumps(packet), encoding="utf-8")
    rc = cli.main(_pass_args(packet=packet_path))
    assert rc == 1


def test_invalid_secret_pattern_s3(cli, tmp_path):
    packet = json.loads(PACKET.read_text(encoding="utf-8"))
    packet["note"] = "s3://bucket/object"
    packet_path = tmp_path / "packet.json"
    packet_path.write_text(json.dumps(packet), encoding="utf-8")
    rc = cli.main(_pass_args(packet=packet_path))
    assert rc == 1


def test_invalid_missing_file(cli, tmp_path):
    rc = cli.main(_pass_args(preflight=tmp_path / "missing_preflight.json"))
    assert rc == 1


def test_invalid_inventory_charter_ready_flag(cli, tmp_path):
    inventory = json.loads(INVENTORY.read_text(encoding="utf-8"))
    inventory.setdefault("output_machine_lines", {})[
        "REMOTE_HOST_INVENTORY_READY_FOR_IMPLEMENTATION_CHARTER"
    ] = True
    inventory_path = tmp_path / "inventory.json"
    inventory_path.write_text(json.dumps(inventory), encoding="utf-8")
    rc = cli.main(_pass_args(inventory=inventory_path))
    assert rc == 1


def test_json_output_contract(cli, capsys):
    rc = cli.main([*_pass_args(), "--json"])
    captured = capsys.readouterr()
    assert rc == 0
    payload = json.loads(captured.out.strip())
    assert payload["schema_version"] == "peak_trade.remote_paper_runner_plan_result.v0"
    assert payload["status"] == "planning_valid"
    assert payload["preflight_blocked_lifted"] is False
    assert payload["ready_for_start"] is False
    assert payload["remote_runner_start_permitted"] is False
    assert payload["runtime_commands_called"] is False
    assert all(value is False for value in payload["authority"].values())
    assert payload["plan_mode"] == {
        "dry_run": True,
        "no_network": True,
        "no_execute": True,
    }


def test_machine_lines_never_start_permitted(cli, capsys):
    cli.main(_pass_args())
    captured = capsys.readouterr()
    assert "START_PERMITTED=true" not in captured.out


def test_static_forbidden_substrings() -> None:
    text = CLI.read_text(encoding="utf-8")
    for token in FORBIDDEN_SUBSTRINGS:
        assert token not in text, f"forbidden token present: {token}"


def test_static_forbidden_import_markers() -> None:
    text = CLI.read_text(encoding="utf-8")
    for marker in FORBIDDEN_IMPORT_MARKERS:
        assert marker not in text, f"forbidden import marker: {marker}"


def test_singleton_runner_plan_cli() -> None:
    matches = list(OPS_DIR.glob("remote_paper_runner_plan_v0.py"))
    assert matches == [CLI]


def test_reuses_validate_inputs_import() -> None:
    text = CLI.read_text(encoding="utf-8")
    assert "validate_inputs" in text
    assert "subprocess" not in text
