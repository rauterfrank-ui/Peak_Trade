"""Contract tests for offline Autonomous Ops Control Plane plan generator v0."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from scripts.ops import build_autonomous_ops_control_plane_plan_v0 as plan_mod

REPO_ROOT = Path(__file__).resolve().parents[2]
FIXTURE_DIR = REPO_ROOT / "tests/fixtures/ops/control_plane_transition_v0"
SCRIPT = REPO_ROOT / "scripts/ops/build_autonomous_ops_control_plane_plan_v0.py"

LEGAL_FIXTURE = FIXTURE_DIR / "legal_ready_for_operator_token_path_v0.json"
FORBIDDEN_FIXTURE = FIXTURE_DIR / "forbidden_stop_idle_to_running_v0.json"
FAIL_CLOSED_FIXTURE = FIXTURE_DIR / "fail_closed_missing_evidence_v0.json"

REQUIRED_MACHINE_LINE_ASSERTIONS = (
    "START_RUNTIME_NOW=false",
    "START_SCHEDULER_NOW=false",
    "START_SUPERVISOR_NOW=false",
    "START_DAEMON_NOW=false",
    "START_PAPER_SHADOW_TESTNET_LIVE_NOW=false",
    "AWS_REMOTE_REQUIRED=false",
    "S3_UPLOAD_REQUIRED=false",
    "SSH_REQUIRED=false",
    "NETWORK_REQUIRED=false",
    "LIVE_AUTHORITY_CHANGED=false",
    "MASTER_V2_DOUBLE_PLAY_TOUCHED=false",
)

FORBIDDEN_SOURCE_PATTERNS = (
    "import subprocess",
    "from subprocess",
    "subprocess.run",
    "subprocess.Popen",
    "os.system",
    "import boto3",
    "import paramiko",
    "import requests",
    "import urllib",
    "import socket",
    "run_scheduler",
    'add_argument("--execute"',
    "add_argument('--execute'",
)


def _parse_machine_lines(text: str) -> dict[str, str]:
    out: dict[str, str] = {}
    for raw in text.splitlines():
        line = raw.strip()
        if "=" in line:
            key, _, value = line.partition("=")
            out[key.strip()] = value.strip()
    return out


def _run_cli(fixture: Path, outdir: Path) -> int:
    return plan_mod.main(["--fixture", str(fixture), "--outdir", str(outdir)])


@pytest.fixture
def plan_out_dir(tmp_path: Path) -> Path:
    out = tmp_path / "plan_out"
    out.mkdir()
    return out


def test_legal_fixture_produces_plan_only_and_no_starts(plan_out_dir: Path) -> None:
    rc = _run_cli(LEGAL_FIXTURE, plan_out_dir)
    assert rc == 0
    plan = json.loads((plan_out_dir / plan_mod.PLAN_JSON_FILENAME).read_text(encoding="utf-8"))
    assert plan["schema_version"] == plan_mod.SCHEMA_VERSION
    assert plan["decision"]["status"] == "plan_only"
    assert plan["decision"]["execute_authorized"] is False
    lines = _parse_machine_lines(
        (plan_out_dir / plan_mod.PLAN_MACHINE_LINES_FILENAME).read_text(encoding="utf-8")
    )
    assert lines["CONTROL_PLANE_PLAN_STATUS"] == "plan_only"
    for key in (
        "START_RUNTIME_NOW",
        "START_SCHEDULER_NOW",
        "START_PAPER_SHADOW_TESTNET_LIVE_NOW",
    ):
        assert lines[key] == "false"


def test_forbidden_fixture_produces_blocked_and_no_starts(plan_out_dir: Path) -> None:
    rc = _run_cli(FORBIDDEN_FIXTURE, plan_out_dir)
    assert rc == 0
    plan = json.loads((plan_out_dir / plan_mod.PLAN_JSON_FILENAME).read_text(encoding="utf-8"))
    assert plan["decision"]["status"] == "blocked"
    assert plan["expected_forbidden"] is True
    lines = _parse_machine_lines(
        (plan_out_dir / plan_mod.PLAN_MACHINE_LINES_FILENAME).read_text(encoding="utf-8")
    )
    assert lines["CONTROL_PLANE_PLAN_STATUS"] == "blocked"
    for assertion in REQUIRED_MACHINE_LINE_ASSERTIONS:
        key = assertion.split("=", 1)[0]
        assert lines[key] == "false"


def test_fail_closed_fixture_does_not_authorize_runtime_or_network(plan_out_dir: Path) -> None:
    rc = _run_cli(FAIL_CLOSED_FIXTURE, plan_out_dir)
    assert rc == 0
    plan = json.loads((plan_out_dir / plan_mod.PLAN_JSON_FILENAME).read_text(encoding="utf-8"))
    assert plan["target_state"] == "FAILED_CLOSED"
    decision = plan["decision"]
    assert decision["runtime_start_authorized"] is False
    assert decision["network_required"] is False
    assert decision["live_authority_changed"] is False
    lines = _parse_machine_lines(
        (plan_out_dir / plan_mod.PLAN_MACHINE_LINES_FILENAME).read_text(encoding="utf-8")
    )
    assert lines["NETWORK_REQUIRED"] == "false"
    assert lines["LIVE_AUTHORITY_CHANGED"] == "false"


def test_json_output_is_deterministic_for_legal_fixture(plan_out_dir: Path) -> None:
    rc1 = _run_cli(LEGAL_FIXTURE, plan_out_dir)
    text1 = (plan_out_dir / plan_mod.PLAN_JSON_FILENAME).read_text(encoding="utf-8")
    rc2 = _run_cli(LEGAL_FIXTURE, plan_out_dir)
    text2 = (plan_out_dir / plan_mod.PLAN_JSON_FILENAME).read_text(encoding="utf-8")
    assert rc1 == rc2 == 0
    assert text1 == text2
    payload = json.loads(text1)
    assert payload["schema_version"] == "control_plane_plan_v0"
    assert payload["machine_lines"]["OFFLINE_CONTROL_PLANE_PLAN_GENERATOR_V0"] == "true"


def test_machine_lines_file_contains_required_flags(plan_out_dir: Path) -> None:
    assert _run_cli(LEGAL_FIXTURE, plan_out_dir) == 0
    text = (plan_out_dir / plan_mod.PLAN_MACHINE_LINES_FILENAME).read_text(encoding="utf-8")
    for assertion in REQUIRED_MACHINE_LINE_ASSERTIONS:
        assert assertion in text


def test_script_source_has_no_dangerous_imports_or_execute_flag() -> None:
    source = SCRIPT.read_text(encoding="utf-8")
    for pattern in FORBIDDEN_SOURCE_PATTERNS:
        assert pattern not in source, f"forbidden pattern in planner source: {pattern!r}"


def test_planner_script_and_contract_module_exist_v0() -> None:
    assert SCRIPT.is_file()
    assert Path(__file__).resolve().is_file()
