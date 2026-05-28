"""Contract tests for offline Autonomous Ops Control Plane chain orchestrator stub v0."""

from __future__ import annotations

import ast
import json
from pathlib import Path

import pytest

from scripts.ops import run_autonomous_ops_control_plane_offline_chain_v0 as chain_mod

REPO_ROOT = Path(__file__).resolve().parents[2]
FIXTURE_DIR = REPO_ROOT / "tests/fixtures/ops/control_plane_transition_v0"
ORCHESTRATOR_SCRIPT = REPO_ROOT / "scripts/ops/run_autonomous_ops_control_plane_offline_chain_v0.py"

LEGAL_FIXTURE = FIXTURE_DIR / "legal_ready_for_operator_token_path_v0.json"
FORBIDDEN_FIXTURE = FIXTURE_DIR / "forbidden_stop_idle_to_running_v0.json"
FAIL_CLOSED_FIXTURE = FIXTURE_DIR / "fail_closed_missing_evidence_v0.json"

REQUIRED_CHAIN_MACHINE_LINE_ASSERTIONS = (
    "CONTROL_PLANE_OFFLINE_CHAIN_V0=true",
    "PLANNING_ONLY=true",
    "NON_AUTHORIZING=true",
    "FULL_POST_CLOSEOUT_AUTOMATION_IMPLEMENTED=false",
    "CLOSEOUT_INVOKED=false",
    "PROJECTION_INVOKED=false",
    "NOTION_SYNC_INVOKED=false",
    "DURABLE_COPY_INVOKED=false",
    "PRIMARY_EVIDENCE_RETENTION_INVOKED=false",
    "RUNTIME_STARTED=false",
    "SCHEDULER_STARTED=false",
    "SUPERVISOR_STARTED=false",
    "DAEMON_STARTED=false",
    "PAPER_SHADOW_TESTNET_LIVE_STARTED=false",
    "AWS_REMOTE_TOUCHED=false",
    "S3_UPLOAD_REQUIRED=false",
    "SSH_REQUIRED=false",
    "NETWORK_REQUIRED=false",
    "LIVE_AUTHORITY_CHANGED=false",
    "MASTER_V2_DOUBLE_PLAY_TOUCHED=false",
)

FORBIDDEN_CLI_FLAGS = ("--execute", "--run", "--start", "--closeout", "--sync", "--upload")

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
    "primary_evidence_retention_v0.main(",
)


def _parse_machine_lines(text: str) -> dict[str, str]:
    out: dict[str, str] = {}
    for raw in text.splitlines():
        line = raw.strip()
        if "=" in line:
            key, _, value = line.partition("=")
            out[key.strip()] = value.strip()
    return out


def _run_chain(fixture: Path, outdir: Path) -> int:
    return chain_mod.main(["--fixture", str(fixture), "--outdir", str(outdir)])


def _assert_chain_artifacts(outdir: Path) -> None:
    assert (outdir / "plan" / "CONTROL_PLANE_PLAN_V0.json").is_file()
    assert (outdir / "plan" / "CONTROL_PLANE_PLAN_MACHINE_LINES.txt").is_file()
    assert (outdir / "plan" / "CONTROL_PLANE_PLAN_V0.md").is_file()
    assert (outdir / "readiness" / "CONTROL_PLANE_POST_CLOSEOUT_READINESS_V0.json").is_file()
    assert (
        outdir / "readiness" / "CONTROL_PLANE_POST_CLOSEOUT_READINESS_MACHINE_LINES.txt"
    ).is_file()
    assert (outdir / "readiness" / "CONTROL_PLANE_POST_CLOSEOUT_READINESS_V0.md").is_file()
    assert (outdir / chain_mod.CHAIN_JSON_FILENAME).is_file()
    assert (outdir / chain_mod.CHAIN_MACHINE_LINES_FILENAME).is_file()
    assert (outdir / chain_mod.CHAIN_MD_FILENAME).is_file()


def _load_chain(outdir: Path) -> dict:
    return json.loads((outdir / chain_mod.CHAIN_JSON_FILENAME).read_text(encoding="utf-8"))


@pytest.mark.parametrize(
    "fixture",
    [LEGAL_FIXTURE, FORBIDDEN_FIXTURE, FAIL_CLOSED_FIXTURE],
    ids=lambda p: p.stem,
)
def test_orchestrator_writes_plan_readiness_and_chain_artifacts(
    tmp_path: Path, fixture: Path
) -> None:
    outdir = tmp_path / fixture.stem
    assert _run_chain(fixture, outdir) == 0
    _assert_chain_artifacts(outdir)


def test_legal_fixture_plan_only_and_ready_for_projection_planning(tmp_path: Path) -> None:
    outdir = tmp_path / "legal"
    assert _run_chain(LEGAL_FIXTURE, outdir) == 0
    chain = _load_chain(outdir)
    assert chain["plan_status"] == "plan_only"
    assert chain["readiness_status"] == "ready_for_projection_planning"
    assert chain["full_post_closeout_automation_implemented"] is False
    assert chain["closeout_invoked"] is False
    assert chain["projection_invoked"] is False
    assert chain["runtime_started"] is False
    assert chain["network_required"] is False
    assert chain["live_authority_changed"] is False


def test_forbidden_fixture_blocked_and_non_authorizing(tmp_path: Path) -> None:
    outdir = tmp_path / "forbidden"
    assert _run_chain(FORBIDDEN_FIXTURE, outdir) == 0
    chain = _load_chain(outdir)
    assert chain["plan_status"] == "blocked"
    assert chain["readiness_status"] == "blocked"
    assert chain["full_post_closeout_automation_implemented"] is False
    assert chain["closeout_invoked"] is False
    assert chain["notion_sync_invoked"] is False


def test_fail_closed_fixture_never_authorizes_anything(tmp_path: Path) -> None:
    outdir = tmp_path / "fail_closed"
    assert _run_chain(FAIL_CLOSED_FIXTURE, outdir) == 0
    chain = _load_chain(outdir)
    assert chain["closeout_invoked"] is False
    assert chain["projection_invoked"] is False
    assert chain["durable_copy_invoked"] is False
    assert chain["primary_evidence_retention_invoked"] is False
    assert chain["paper_shadow_testnet_live_started"] is False
    assert chain["live_authority_changed"] is False


def test_chain_machine_lines_are_deterministic_key_value_lines(tmp_path: Path) -> None:
    outdir = tmp_path / "legal"
    assert _run_chain(LEGAL_FIXTURE, outdir) == 0
    text = (outdir / chain_mod.CHAIN_MACHINE_LINES_FILENAME).read_text(encoding="utf-8")
    for assertion in REQUIRED_CHAIN_MACHINE_LINE_ASSERTIONS:
        assert assertion in text
    lines = _parse_machine_lines(text)
    assert lines["FULL_POST_CLOSEOUT_AUTOMATION_IMPLEMENTED"] == "false"


def test_cli_parser_has_no_execute_or_runtime_flags() -> None:
    source = ORCHESTRATOR_SCRIPT.read_text(encoding="utf-8")
    for flag in FORBIDDEN_CLI_FLAGS:
        assert f'"{flag}"' not in source
        assert f"'{flag}'" not in source


def test_orchestrator_source_has_no_dangerous_imports_or_invocations() -> None:
    source = ORCHESTRATOR_SCRIPT.read_text(encoding="utf-8")
    for pattern in FORBIDDEN_SOURCE_PATTERNS:
        assert pattern not in source, f"forbidden pattern in orchestrator source: {pattern!r}"


def test_offline_chain_json_is_deterministic(tmp_path: Path) -> None:
    outdir = tmp_path / "legal"
    assert _run_chain(LEGAL_FIXTURE, outdir) == 0
    text1 = (outdir / chain_mod.CHAIN_JSON_FILENAME).read_text(encoding="utf-8")
    assert _run_chain(LEGAL_FIXTURE, outdir) == 0
    text2 = (outdir / chain_mod.CHAIN_JSON_FILENAME).read_text(encoding="utf-8")
    assert text1 == text2


def test_module_imports_are_scripts_ops_only_v0() -> None:
    allowed_roots = frozenset(
        {"__future__", "argparse", "json", "pathlib", "sys", "typing", "scripts"}
    )
    tree = ast.parse(ORCHESTRATOR_SCRIPT.read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom):
            assert node.module is not None
            root = node.module.split(".")[0]
            assert root in allowed_roots, f"unexpected import from: {node.module!r}"
