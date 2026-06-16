"""Contract tests for control plane plan → post-closeout readiness bridge v0."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from scripts.ops import bridge_control_plane_plan_to_post_closeout_readiness_v0 as bridge_mod
from scripts.ops import build_autonomous_ops_control_plane_plan_v0 as plan_mod

REPO_ROOT = Path(__file__).resolve().parents[2]
FIXTURE_DIR = REPO_ROOT / "tests/fixtures/ops/control_plane_transition_v0"
BRIDGE_SCRIPT = REPO_ROOT / "scripts/ops/bridge_control_plane_plan_to_post_closeout_readiness_v0.py"

LEGAL_FIXTURE = FIXTURE_DIR / "legal_ready_for_operator_token_path_v0.json"
FORBIDDEN_FIXTURE = FIXTURE_DIR / "forbidden_stop_idle_to_running_v0.json"

OWNER_PATHS = (
    REPO_ROOT / "tests/ops/test_closeout_to_projection_chain_automation_contract_v0.py",
    REPO_ROOT / "scripts/ops/build_post_closeout_projection_payload_v0.py",
    REPO_ROOT / "scripts/ops/notion_post_closeout_sync_dry_run_v0.py",
    REPO_ROOT / "scripts/ops/durable_closeout_copy_verify_v0.py",
)

REQUIRED_MACHINE_LINE_ASSERTIONS = (
    "PLANNING_ONLY=true",
    "CLOSEOUT_INVOKE_AUTHORIZED=false",
    "PROJECTION_INVOKE_AUTHORIZED=false",
    "NOTION_SYNC_AUTHORIZED=false",
    "DURABLE_COPY_AUTHORIZED=false",
    "PRIMARY_EVIDENCE_RETENTION_INVOKE_AUTHORIZED=false",
    "RUNTIME_START_REQUIRED=false",
    "SCHEDULER_START_REQUIRED=false",
    "SUPERVISOR_START_REQUIRED=false",
    "DAEMON_START_REQUIRED=false",
    "PAPER_SHADOW_TESTNET_LIVE_START_REQUIRED=false",
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
    "durable_closeout_copy_verify_v0.main(",
    "build_post_closeout_projection_payload_v0.main(",
    "notion_post_closeout_sync_dry_run_v0.main(",
)


def _parse_machine_lines(text: str) -> dict[str, str]:
    out: dict[str, str] = {}
    for raw in text.splitlines():
        line = raw.strip()
        if "=" in line:
            key, _, value = line.partition("=")
            out[key.strip()] = value.strip()
    return out


def _make_plan(tmp_path: Path, fixture: Path) -> Path:
    plan_dir = tmp_path / "plan"
    plan_dir.mkdir()
    rc = plan_mod.main(["--fixture", str(fixture), "--outdir", str(plan_dir)])
    assert rc == 0
    return plan_dir / plan_mod.PLAN_JSON_FILENAME


def _run_bridge(plan_json: Path, outdir: Path) -> int:
    return bridge_mod.main(["--plan", str(plan_json), "--outdir", str(outdir)])


@pytest.fixture
def bridge_out_dir(tmp_path: Path) -> Path:
    out = tmp_path / "readiness"
    out.mkdir()
    return out


def test_plan_only_source_produces_ready_for_projection_planning(
    tmp_path: Path, bridge_out_dir: Path
) -> None:
    plan_json = _make_plan(tmp_path, LEGAL_FIXTURE)
    assert _run_bridge(plan_json, bridge_out_dir) == 0
    readiness = json.loads(
        (bridge_out_dir / bridge_mod.READINESS_JSON_FILENAME).read_text(encoding="utf-8")
    )
    assert readiness["schema_version"] == bridge_mod.SCHEMA_VERSION
    assert readiness["control_plane_plan_status"] == "plan_only"
    assert (
        readiness["machine_lines"]["CONTROL_PLANE_POST_CLOSEOUT_READINESS_STATUS"]
        == "ready_for_projection_planning"
    )
    assert readiness["readiness"]["can_prepare_post_closeout_projection_payload"] is True
    assert readiness["closeout_invoke_authorized"] is False
    assert readiness["projection_invoke_authorized"] is False
    assert readiness["notion_sync_authorized"] is False
    assert readiness["durable_copy_authorized"] is False


def test_blocked_source_remains_blocked(tmp_path: Path, bridge_out_dir: Path) -> None:
    plan_json = _make_plan(tmp_path, FORBIDDEN_FIXTURE)
    assert _run_bridge(plan_json, bridge_out_dir) == 0
    readiness = json.loads(
        (bridge_out_dir / bridge_mod.READINESS_JSON_FILENAME).read_text(encoding="utf-8")
    )
    assert readiness["control_plane_plan_status"] == "blocked"
    assert readiness["machine_lines"]["CONTROL_PLANE_POST_CLOSEOUT_READINESS_STATUS"] == "blocked"
    assert readiness["readiness"]["can_prepare_post_closeout_projection_payload"] is False
    assert readiness["closeout_invoke_authorized"] is False
    assert readiness["projection_invoke_authorized"] is False


def test_machine_lines_file_contains_required_flags(tmp_path: Path, bridge_out_dir: Path) -> None:
    plan_json = _make_plan(tmp_path, LEGAL_FIXTURE)
    assert _run_bridge(plan_json, bridge_out_dir) == 0
    text = (bridge_out_dir / bridge_mod.READINESS_MACHINE_LINES_FILENAME).read_text(
        encoding="utf-8"
    )
    for assertion in REQUIRED_MACHINE_LINE_ASSERTIONS:
        assert assertion in text
    lines = _parse_machine_lines(text)
    assert lines["PLANNING_ONLY"] == "true"
    assert lines["CLOSEOUT_INVOKE_AUTHORIZED"] == "false"


def test_owner_pointers_reference_existing_canonical_files(
    tmp_path: Path, bridge_out_dir: Path
) -> None:
    plan_json = _make_plan(tmp_path, LEGAL_FIXTURE)
    assert _run_bridge(plan_json, bridge_out_dir) == 0
    readiness = json.loads(
        (bridge_out_dir / bridge_mod.READINESS_JSON_FILENAME).read_text(encoding="utf-8")
    )
    owners = readiness["owners"]
    for path in OWNER_PATHS:
        assert path.is_file()
        assert path.name in owners.values() or str(path.relative_to(REPO_ROOT)) in owners.values()


def test_bridge_script_source_has_no_dangerous_imports_or_invocations() -> None:
    source = BRIDGE_SCRIPT.read_text(encoding="utf-8")
    for pattern in FORBIDDEN_SOURCE_PATTERNS:
        assert pattern not in source, f"forbidden pattern in bridge source: {pattern!r}"


def test_readiness_json_is_deterministic(tmp_path: Path, bridge_out_dir: Path) -> None:
    plan_json = _make_plan(tmp_path, LEGAL_FIXTURE)
    assert _run_bridge(plan_json, bridge_out_dir) == 0
    text1 = (bridge_out_dir / bridge_mod.READINESS_JSON_FILENAME).read_text(encoding="utf-8")
    assert _run_bridge(plan_json, bridge_out_dir) == 0
    text2 = (bridge_out_dir / bridge_mod.READINESS_JSON_FILENAME).read_text(encoding="utf-8")
    assert text1 == text2
