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

THIS_MODULE = Path(__file__)

LEGAL_FIXTURE = FIXTURE_DIR / "legal_ready_for_operator_token_path_v0.json"
FORBIDDEN_FIXTURE = FIXTURE_DIR / "forbidden_stop_idle_to_running_v0.json"
FAIL_CLOSED_FIXTURE = FIXTURE_DIR / "fail_closed_missing_evidence_v0.json"

EXPECTED_ALL_FIXTURE_STEMS: tuple[str, ...] = (
    "legal_ready_for_operator_token_path_v0",
    "forbidden_stop_idle_to_running_v0",
    "forbidden_preflight_blocked_to_running_v0",
    "forbidden_preflight_pass_to_running_without_operator_token_v0",
    "forbidden_running_to_evidence_verified_without_closeout_v0",
    "fail_closed_missing_evidence_v0",
)

CHAIN_NO_AUTHORITY_JSON_KEYS: tuple[str, ...] = (
    "full_post_closeout_automation_implemented",
    "closeout_invoked",
    "projection_invoked",
    "notion_sync_invoked",
    "durable_copy_invoked",
    "primary_evidence_retention_invoked",
    "runtime_started",
    "scheduler_started",
    "supervisor_started",
    "daemon_started",
    "paper_shadow_testnet_live_started",
    "aws_remote_touched",
    "s3_upload_required",
    "ssh_required",
    "network_required",
    "live_authority_changed",
    "master_v2_double_play_touched",
)

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

_FORBIDDEN_ORCHESTRATOR_SOURCE_PATTERNS: tuple[str, ...] = (
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


def _this_module_source() -> str:
    return THIS_MODULE.read_text(encoding="utf-8")


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


def _all_fixture_paths() -> list[Path]:
    paths = sorted(FIXTURE_DIR.glob("*.json"))
    assert paths, f"no fixtures under {FIXTURE_DIR}"
    return paths


def _load_fixture_meta(fixture_path: Path) -> dict:
    return json.loads(fixture_path.read_text(encoding="utf-8"))


def _assert_status_mapping(chain: dict, *, expected_forbidden: bool) -> None:
    if expected_forbidden:
        assert chain["plan_status"] == "blocked"
        assert chain["readiness_status"] == "blocked"
    else:
        assert chain["plan_status"] == "plan_only"
        assert chain["readiness_status"] == "ready_for_projection_planning"


def _assert_chain_no_authority_flags(chain: dict) -> None:
    for key in CHAIN_NO_AUTHORITY_JSON_KEYS:
        assert chain[key] is False, f"expected {key}=false, got {chain[key]!r}"


def _assert_chain_machine_lines_no_authority(outdir: Path) -> None:
    text = (outdir / chain_mod.CHAIN_MACHINE_LINES_FILENAME).read_text(encoding="utf-8")
    for assertion in REQUIRED_CHAIN_MACHINE_LINE_ASSERTIONS:
        assert assertion in text
    lines = _parse_machine_lines(text)
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        assert "=" in stripped, f"machine line must be KEY=value: {stripped!r}"
    assert lines["FULL_POST_CLOSEOUT_AUTOMATION_IMPLEMENTED"] == "false"


def test_fixture_directory_covers_all_six_cases_v0() -> None:
    stems = {path.stem for path in _all_fixture_paths()}
    assert stems == set(EXPECTED_ALL_FIXTURE_STEMS)


@pytest.mark.parametrize("fixture_path", _all_fixture_paths(), ids=lambda p: p.stem)
def test_all_fixtures_offline_chain_smoke_v0(tmp_path: Path, fixture_path: Path) -> None:
    meta = _load_fixture_meta(fixture_path)
    outdir = tmp_path / fixture_path.stem
    assert _run_chain(fixture_path, outdir) == 0
    _assert_chain_artifacts(outdir)
    chain = _load_chain(outdir)
    _assert_status_mapping(chain, expected_forbidden=meta["expected_forbidden"])
    _assert_chain_no_authority_flags(chain)
    _assert_chain_machine_lines_no_authority(outdir)


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
    for pattern in _FORBIDDEN_ORCHESTRATOR_SOURCE_PATTERNS:
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


def test_contract_module_imports_are_stdlib_and_scripts_ops_only_v0() -> None:
    allowed_roots = frozenset({"__future__", "ast", "json", "pathlib", "pytest", "scripts"})
    tree = ast.parse(_this_module_source())
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom):
            assert node.module is not None
            root = node.module.split(".")[0]
            assert root in allowed_roots, f"unexpected import from: {node.module!r}"
        elif isinstance(node, ast.Import):
            for alias in node.names:
                root = alias.name.split(".")[0]
                assert root in allowed_roots, f"unexpected import: {alias.name!r}"


def test_contract_module_has_no_runtime_or_invocation_patterns_v0() -> None:
    in_forbidden_tuple = False
    for line in _this_module_source().splitlines():
        if "_FORBIDDEN_ORCHESTRATOR_SOURCE_PATTERNS" in line:
            in_forbidden_tuple = True
            continue
        if in_forbidden_tuple:
            if line.strip().startswith(")"):
                in_forbidden_tuple = False
            continue
        stripped = line.strip()
        if stripped.startswith("assert ") and " not in " in stripped:
            continue
        for pattern in _FORBIDDEN_ORCHESTRATOR_SOURCE_PATTERNS:
            assert pattern not in line, (
                f"forbidden pattern in contract test source: {pattern!r} line={line!r}"
            )
