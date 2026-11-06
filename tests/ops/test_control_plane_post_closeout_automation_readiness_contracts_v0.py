"""Control Plane post-closeout automation readiness contracts v0 (tests-only, static/offline).

Defines the readiness gate before any future Full Post-Closeout Automation phases 2–9.
Does not invoke closeout, projection, Notion, durable copy, retention, runtime, or network.
Does not duplicate chain execution behavior from test_closeout_to_projection_chain_automation_contract_v0.
"""

from __future__ import annotations

import ast
import json
from pathlib import Path

import pytest

from scripts.ops import bridge_control_plane_plan_to_post_closeout_readiness_v0 as bridge_mod
from scripts.ops import build_autonomous_ops_control_plane_plan_v0 as plan_mod

REPO_ROOT = Path(__file__).resolve().parents[2]
THIS_MODULE = Path(__file__).name

BRIDGE_SCRIPT = REPO_ROOT / "scripts/ops/bridge_control_plane_plan_to_post_closeout_readiness_v0.py"
BRIDGE_TEST = (
    REPO_ROOT / "tests/ops/test_control_plane_plan_output_closeout_projection_bridge_contract_v0.py"
)
CHAIN_TEST = REPO_ROOT / "tests/ops/test_closeout_to_projection_chain_automation_contract_v0.py"
PROJECTION_BUILDER = REPO_ROOT / "scripts/ops/build_post_closeout_projection_payload_v0.py"
NOTION_DRY_RUN = REPO_ROOT / "scripts/ops/notion_post_closeout_sync_dry_run_v0.py"
DURABLE_COPY_VERIFY = REPO_ROOT / "scripts/ops/durable_closeout_copy_verify_v0.py"
PRIMARY_EVIDENCE_RETENTION = REPO_ROOT / "scripts/ops/primary_evidence_retention_v0.py"

LEGAL_FIXTURE = (
    REPO_ROOT
    / "tests/fixtures/ops/control_plane_transition_v0/legal_ready_for_operator_token_path_v0.json"
)
FORBIDDEN_FIXTURE = (
    REPO_ROOT
    / "tests/fixtures/ops/control_plane_transition_v0/forbidden_stop_idle_to_running_v0.json"
)

CONTROL_PLANE_POST_CLOSEOUT_AUTOMATION_PHASES_V0: tuple[str, ...] = (
    "phase_2_plan_output_available",
    "phase_3_post_closeout_readiness_available",
    "phase_4_projection_payload_contract_available",
    "phase_5_notion_sync_dry_run_available",
    "phase_6_durable_copy_verify_available",
    "phase_7_market_dashboard_out_of_scope",
    "phase_8_operator_review_required",
    "phase_9_full_automation_not_implemented",
)

REQUIRED_BLOCKERS_BEFORE_FULL_AUTOMATION_V0: frozenset[str] = frozenset(
    {
        "FULL_POST_CLOSEOUT_AUTOMATION_IMPLEMENTED=false",
        "CLOSEOUT_INVOKED=false",
        "PROJECTION_INVOKED=false",
        "NOTION_SYNC_INVOKED=false",
        "DURABLE_COPY_INVOKED=false",
        "PRIMARY_EVIDENCE_RETENTION_INVOKED=false",
        "MARKET_DASHBOARD_OUT_OF_SCOPE=true",
        "OPERATOR_REVIEW_REQUIRED=true",
    }
)

BRIDGE_NON_AUTHORITY_MARKERS: tuple[str, ...] = (
    "CLOSEOUT_INVOKE_AUTHORIZED",
    "PROJECTION_INVOKE_AUTHORIZED",
    "NOTION_SYNC_AUTHORIZED",
    "DURABLE_COPY_AUTHORIZED",
    "PRIMARY_EVIDENCE_RETENTION_INVOKE_AUTHORIZED",
)

CHAIN_VOCABULARY_MARKERS: tuple[str, ...] = (
    "build_post_closeout_automation_readiness_summary",
    "PostCloseoutAutomationReadinessInputs",
    "build_post_closeout_hook_contract_summary",
    "projection_payload_missing",
    "closeout_manifest_verify_not_ok",
)

_FORBIDDEN_SOURCE_PATTERNS: tuple[str, ...] = (
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


def _read(path: Path) -> str:
    assert path.is_file(), f"missing canonical owner: {path}"
    return path.read_text(encoding="utf-8")


def _this_module_source() -> str:
    return Path(__file__).read_text(encoding="utf-8")


def _make_plan_and_bridge(tmp_path: Path, fixture: Path) -> dict:
    plan_dir = tmp_path / "plan"
    readiness_dir = tmp_path / "readiness"
    plan_dir.mkdir()
    readiness_dir.mkdir()
    assert plan_mod.main(["--fixture", str(fixture), "--outdir", str(plan_dir)]) == 0
    plan_json = plan_dir / plan_mod.PLAN_JSON_FILENAME
    assert bridge_mod.main(["--plan", str(plan_json), "--outdir", str(readiness_dir)]) == 0
    return json.loads(
        (readiness_dir / bridge_mod.READINESS_JSON_FILENAME).read_text(encoding="utf-8")
    )


def test_automation_phases_v0_frozen_shape() -> None:
    assert len(CONTROL_PLANE_POST_CLOSEOUT_AUTOMATION_PHASES_V0) == 8
    assert len(set(CONTROL_PLANE_POST_CLOSEOUT_AUTOMATION_PHASES_V0)) == 8
    assert CONTROL_PLANE_POST_CLOSEOUT_AUTOMATION_PHASES_V0[0].startswith("phase_2_")
    assert CONTROL_PLANE_POST_CLOSEOUT_AUTOMATION_PHASES_V0[-1] == (
        "phase_9_full_automation_not_implemented"
    )


def test_phase_seven_is_planning_gap_not_market_dashboard_touch() -> None:
    assert (
        "phase_7_market_dashboard_out_of_scope" in CONTROL_PLANE_POST_CLOSEOUT_AUTOMATION_PHASES_V0
    )
    assert "MARKET_DASHBOARD_OUT_OF_SCOPE=true" in REQUIRED_BLOCKERS_BEFORE_FULL_AUTOMATION_V0
    tree = ast.parse(_this_module_source())
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom):
            assert node.module is not None
            assert "market_surface" not in node.module
            assert "webui" not in node.module


def test_required_blockers_before_full_automation_v0() -> None:
    assert len(REQUIRED_BLOCKERS_BEFORE_FULL_AUTOMATION_V0) == 8
    assert (
        "FULL_POST_CLOSEOUT_AUTOMATION_IMPLEMENTED=false"
        in REQUIRED_BLOCKERS_BEFORE_FULL_AUTOMATION_V0
    )
    assert "OPERATOR_REVIEW_REQUIRED=true" in REQUIRED_BLOCKERS_BEFORE_FULL_AUTOMATION_V0


def test_bridge_owner_and_contract_test_exist_v0() -> None:
    assert BRIDGE_SCRIPT.is_file()
    assert BRIDGE_TEST.is_file()
    assert "CONTROL_PLANE_POST_CLOSEOUT_READINESS_V0" in _read(BRIDGE_SCRIPT)


def test_canonical_closeout_projection_owners_exist_v0() -> None:
    for path in (
        CHAIN_TEST,
        PROJECTION_BUILDER,
        NOTION_DRY_RUN,
        DURABLE_COPY_VERIFY,
        PRIMARY_EVIDENCE_RETENTION,
    ):
        assert path.is_file(), f"missing owner: {path}"


def test_bridge_script_contains_non_authorizing_invoke_flags_v0() -> None:
    text = _read(BRIDGE_SCRIPT)
    for marker in BRIDGE_NON_AUTHORITY_MARKERS:
        assert marker in text
        assert f'"{marker}": "false"' in text or f"{marker}: false" in text


def test_chain_automation_owner_has_readiness_vocabulary_v0() -> None:
    text = _read(CHAIN_TEST)
    for marker in CHAIN_VOCABULARY_MARKERS:
        assert marker in text


def test_chain_owner_execution_not_duplicated_in_this_module_v0() -> None:
    tree = ast.parse(_this_module_source())
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom):
            assert node.module is not None
            assert "test_closeout_to_projection_chain_automation_contract_v0" not in node.module
        if isinstance(node, ast.Call):
            func = node.func
            if isinstance(func, ast.Name):
                assert func.id != "build_post_closeout_automation_readiness_summary"


def test_plan_only_bridge_readiness_does_not_authorize_full_automation(
    tmp_path: Path,
) -> None:
    readiness = _make_plan_and_bridge(tmp_path, LEGAL_FIXTURE)
    assert readiness["planning_only"] is True
    assert readiness["closeout_invoke_authorized"] is False
    assert readiness["projection_invoke_authorized"] is False
    assert readiness["notion_sync_authorized"] is False
    assert readiness["durable_copy_authorized"] is False
    assert readiness["primary_evidence_retention_invoke_authorized"] is False
    assert (
        readiness["machine_lines"]["CONTROL_PLANE_POST_CLOSEOUT_READINESS_STATUS"]
        == "ready_for_projection_planning"
    )
    assert readiness["readiness"]["can_prepare_post_closeout_projection_payload"] is True


def test_blocked_bridge_readiness_remains_blocked_and_non_authorizing(
    tmp_path: Path,
) -> None:
    readiness = _make_plan_and_bridge(tmp_path, FORBIDDEN_FIXTURE)
    assert readiness["control_plane_plan_status"] == "blocked"
    assert readiness["machine_lines"]["CONTROL_PLANE_POST_CLOSEOUT_READINESS_STATUS"] == "blocked"
    assert readiness["readiness"]["can_prepare_post_closeout_projection_payload"] is False
    assert readiness["closeout_invoke_authorized"] is False
    assert readiness["projection_invoke_authorized"] is False


def test_module_imports_are_stdlib_and_existing_ops_only_v0() -> None:
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


def test_module_has_no_runtime_or_invocation_patterns_v0() -> None:
    in_forbidden_tuple = False
    for line in _this_module_source().splitlines():
        if "_FORBIDDEN_SOURCE_PATTERNS" in line:
            in_forbidden_tuple = True
            continue
        if in_forbidden_tuple:
            if line.strip().startswith(")"):
                in_forbidden_tuple = False
            continue
        stripped = line.strip()
        if stripped.startswith("assert ") and " not in " in stripped:
            continue
        for pattern in _FORBIDDEN_SOURCE_PATTERNS:
            assert pattern not in line, (
                f"forbidden pattern in contract test source: {pattern!r} line={line!r}"
            )
