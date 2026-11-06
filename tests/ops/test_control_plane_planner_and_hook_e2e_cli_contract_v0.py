"""Control Plane planner CLI → hook dry-run summary E2E contract v0 (tests-only).

Proves: fixture → offline chain → attachment planner CLI → plan JSON → hook dry-run summary
without hook CLI, full automation, copy, verify, retention, closeout, projection, Notion,
runtime, network, or cost re-arm.
"""

from __future__ import annotations

import ast
import json
from pathlib import Path

import pytest

from scripts.ops import plan_control_plane_offline_chain_durable_attachment_v0 as planner_mod
from scripts.ops import run_autonomous_ops_control_plane_offline_chain_v0 as chain_mod
from tests.ops.test_control_plane_first_automation_hook_dry_run_contract_v0 import (
    CONTROL_PLANE_AUTOMATION_HOOK_DRY_RUN_MACHINE_LINES_V0,
    STATUS_READY_FOR_CP_HOOK_DRY_RUN,
    ControlPlaneAutomationHookDryRunInputs,
    build_control_plane_automation_hook_dry_run_summary,
)
from tests.ops.test_control_plane_offline_chain_durable_evidence_attachment_contracts_v0 import (
    LEGAL_FIXTURE,
    REQUIRED_CHAIN_REL_PATHS_V0,
    STATUS_BLOCKED_MISSING_REQUIRED_CHAIN_ARTIFACT,
    STATUS_BLOCKED_TARGET_ARCHIVE_ROOT_UNDER_TMP,
    STATUS_READY_FOR_DURABLE_ATTACHMENT_PLANNING,
    SYNTHETIC_DURABLE_ARCHIVE_ROOT,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
THIS_MODULE = Path(__file__)

E2E_OWNER_REFERENCES_V0: tuple[str, ...] = (
    "scripts/ops/run_autonomous_ops_control_plane_offline_chain_v0.py",
    "scripts/ops/plan_control_plane_offline_chain_durable_attachment_v0.py",
    "tests/ops/test_control_plane_first_automation_hook_dry_run_contract_v0.py",
    "tests/ops/test_plan_control_plane_offline_chain_durable_attachment_contract_v0.py",
    "tests/ops/test_control_plane_offline_chain_attachment_e2e_contract_v0.py",
    "tests/ops/test_control_plane_offline_chain_durable_evidence_attachment_contracts_v0.py",
)

HOOK_MACHINE_LINE_ASSERTIONS_READY: tuple[str, ...] = (
    "HOOK_IMPLEMENTED=false",
    "HOOK_DRY_RUN_ONLY=true",
    "FULL_POST_CLOSEOUT_AUTOMATION_IMPLEMENTED=false",
    "DURABLE_COPY_INVOKED=false",
    "PRIMARY_EVIDENCE_RETENTION_INVOKED=false",
    "MANIFEST_WRITE_INVOKED=false",
    "COPY_VERIFY_INVOKED=false",
    "CLOSEOUT_INVOKED=false",
    "PROJECTION_INVOKED=false",
    "NOTION_SYNC_INVOKED=false",
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
    "launchctl",
    'add_argument("--execute"',
    "add_argument('--execute'",
    'add_argument("--copy"',
    'add_argument("--verify"',
    'add_argument("--retention"',
    'add_argument("--closeout"',
    'add_argument("--projection"',
    'add_argument("--notion-sync"',
    "durable_closeout_copy_verify_v0.main(",
    "build_post_closeout_projection_payload_v0.main(",
    "notion_post_closeout_sync_dry_run_v0.main(",
    "primary_evidence_retention_v0.main(",
    "write_manifest_sha256(",
    "KRAKEN_TESTNET_CRON_ENABLED =",
    "PT_AI_MODELS_ENABLED =",
    "PEAK_TRADE_RUN_PAID_PROMPTFOO_EVALS =",
)


def _this_module_source() -> str:
    return THIS_MODULE.read_text(encoding="utf-8")


def _run_offline_chain(fixture: Path, outdir: Path) -> int:
    return chain_mod.main(["--fixture", str(fixture), "--outdir", str(outdir)])


def _run_planner(chain_root: Path, target_archive_root: Path, outdir: Path) -> dict:
    assert (
        planner_mod.main(
            [
                "--chain-root",
                str(chain_root),
                "--target-archive-root",
                str(target_archive_root),
                "--outdir",
                str(outdir),
            ]
        )
        == 0
    )
    return json.loads(
        (outdir / planner_mod.PLAN_JSON_FILENAME).read_text(encoding="utf-8"),
    )


def _assert_planner_output_files_exist(outdir: Path) -> None:
    assert (outdir / planner_mod.PLAN_JSON_FILENAME).is_file()
    assert (outdir / planner_mod.PLAN_MACHINE_LINES_FILENAME).is_file()
    assert (outdir / planner_mod.PLAN_MD_FILENAME).is_file()


def _hook_inputs_from_planner_plan(
    *,
    chain_root: Path,
    plan: dict,
    attachment_e2e_complete: bool,
) -> ControlPlaneAutomationHookDryRunInputs:
    offline_chain_complete = len(plan.get("missing_chain_rel_paths") or []) == 0
    return ControlPlaneAutomationHookDryRunInputs(
        offline_chain_complete=offline_chain_complete,
        attachment_e2e_complete=attachment_e2e_complete,
        attachment_status=str(plan["status"]),
        pointer_only=bool(plan["pointer_only"]),
        target_archive_root=Path(plan["target_archive_root"]),
    )


def _assert_hook_summary_not_ready(hook_status: str, blockers: list[str]) -> None:
    assert hook_status != STATUS_READY_FOR_CP_HOOK_DRY_RUN
    assert blockers


def _assert_hook_machine_lines_safety(machine_lines: dict[str, str]) -> None:
    for assertion in HOOK_MACHINE_LINE_ASSERTIONS_READY:
        key, _, value = assertion.partition("=")
        assert machine_lines[key] == value, f"expected {assertion}"
    assert machine_lines["POINTER_ONLY_DURABLE_ATTACHMENT_REQUIRED"] == "true"


def test_ready_e2e_chain_planner_cli_to_hook_dry_run_summary_v0(tmp_path: Path) -> None:
    chain_dir = tmp_path / "chain"
    planner_dir = tmp_path / "planner"
    assert _run_offline_chain(LEGAL_FIXTURE, chain_dir) == 0
    plan = _run_planner(chain_dir, SYNTHETIC_DURABLE_ARCHIVE_ROOT, planner_dir)
    _assert_planner_output_files_exist(planner_dir)

    assert plan["status"] == STATUS_READY_FOR_DURABLE_ATTACHMENT_PLANNING
    assert plan["pointer_only"] is True
    assert plan["durable_attachment_contract_mode"] == planner_mod.DURABLE_ATTACHMENT_CONTRACT_MODE
    assert plan["missing_chain_rel_paths"] == []
    assert plan["hook_implemented"] is False
    assert plan["full_post_closeout_automation_implemented"] is False

    hook_status, hook_machine_lines, blockers = build_control_plane_automation_hook_dry_run_summary(
        _hook_inputs_from_planner_plan(
            chain_root=chain_dir,
            plan=plan,
            attachment_e2e_complete=True,
        )
    )
    assert hook_status == STATUS_READY_FOR_CP_HOOK_DRY_RUN
    assert blockers == []
    _assert_hook_machine_lines_safety(hook_machine_lines)

    planner_ml = (planner_dir / planner_mod.PLAN_MACHINE_LINES_FILENAME).read_text(
        encoding="utf-8",
    )
    assert "CONTROL_PLANE_DURABLE_ATTACHMENT_PLANNER_CLI_STUB_V0=true" in planner_ml
    assert "DURABLE_COPY_INVOKED=false" in planner_ml
    assert "HOOK_IMPLEMENTED=false" in planner_ml


def test_blocked_missing_chain_artifact_planner_and_hook_not_ready_v0(tmp_path: Path) -> None:
    chain_dir = tmp_path / "chain_partial"
    planner_dir = tmp_path / "planner_blocked"
    assert _run_offline_chain(LEGAL_FIXTURE, chain_dir) == 0
    removed_rel = REQUIRED_CHAIN_REL_PATHS_V0[0]
    (chain_dir / removed_rel).unlink()

    plan = _run_planner(chain_dir, SYNTHETIC_DURABLE_ARCHIVE_ROOT, planner_dir)
    _assert_planner_output_files_exist(planner_dir)
    assert plan["status"] == STATUS_BLOCKED_MISSING_REQUIRED_CHAIN_ARTIFACT
    assert removed_rel in plan["missing_chain_rel_paths"]

    hook_status, hook_machine_lines, blockers = build_control_plane_automation_hook_dry_run_summary(
        _hook_inputs_from_planner_plan(
            chain_root=chain_dir,
            plan=plan,
            attachment_e2e_complete=True,
        )
    )
    _assert_hook_summary_not_ready(hook_status, blockers)
    assert "offline_chain_complete_required" in blockers or (
        "attachment_status_not_ready_for_durable_attachment_planning" in blockers
    )
    assert hook_machine_lines["HOOK_IMPLEMENTED"] == "false"
    assert hook_machine_lines["FULL_POST_CLOSEOUT_AUTOMATION_IMPLEMENTED"] == "false"


def test_blocked_tmp_target_archive_planner_and_hook_not_ready_v0(tmp_path: Path) -> None:
    chain_dir = tmp_path / "chain"
    planner_dir = tmp_path / "planner_tmp"
    assert _run_offline_chain(LEGAL_FIXTURE, chain_dir) == 0
    tmp_archive = Path("/tmp/control_plane_planner_hook_e2e_cli_contract_v0")

    plan = _run_planner(chain_dir, tmp_archive, planner_dir)
    _assert_planner_output_files_exist(planner_dir)
    assert plan["status"] == STATUS_BLOCKED_TARGET_ARCHIVE_ROOT_UNDER_TMP

    hook_status, hook_machine_lines, blockers = build_control_plane_automation_hook_dry_run_summary(
        _hook_inputs_from_planner_plan(
            chain_root=chain_dir,
            plan=plan,
            attachment_e2e_complete=True,
        )
    )
    _assert_hook_summary_not_ready(hook_status, blockers)
    assert "attachment_status_not_ready_for_durable_attachment_planning" in blockers or (
        "target_archive_root_under_tmp" in blockers
    )
    assert hook_machine_lines["DURABLE_COPY_INVOKED"] == "false"
    assert hook_machine_lines["NETWORK_REQUIRED"] == "false"


@pytest.mark.parametrize("owner_rel", E2E_OWNER_REFERENCES_V0)
def test_e2e_owner_references_exist_v0(owner_rel: str) -> None:
    assert (REPO_ROOT / owner_rel).is_file(), f"missing owner reference: {owner_rel!r}"


def test_frozen_hook_dry_run_machine_lines_include_required_keys_v0() -> None:
    assert CONTROL_PLANE_AUTOMATION_HOOK_DRY_RUN_MACHINE_LINES_V0["HOOK_IMPLEMENTED"] == "false"
    assert CONTROL_PLANE_AUTOMATION_HOOK_DRY_RUN_MACHINE_LINES_V0["HOOK_DRY_RUN_ONLY"] == "true"
    assert (
        CONTROL_PLANE_AUTOMATION_HOOK_DRY_RUN_MACHINE_LINES_V0[
            "FULL_POST_CLOSEOUT_AUTOMATION_IMPLEMENTED"
        ]
        == "false"
    )


def test_module_imports_are_stdlib_scripts_ops_tests_ops_only_v0() -> None:
    allowed_roots = frozenset(
        {"__future__", "ast", "json", "pathlib", "pytest", "scripts", "tests"}
    )
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


def test_module_has_no_runtime_invocation_or_cost_rearm_patterns_v0() -> None:
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
                f"forbidden pattern in e2e contract test source: {pattern!r} line={line!r}"
            )


def test_cost_rearm_flags_documented_as_false_in_ready_e2e_v0(tmp_path: Path) -> None:
    """Cost re-arm vars are not set; planner contract mode remains pointer-only."""
    chain_dir = tmp_path / "chain_cost"
    planner_dir = tmp_path / "planner_cost"
    assert _run_offline_chain(LEGAL_FIXTURE, chain_dir) == 0
    plan = _run_planner(chain_dir, SYNTHETIC_DURABLE_ARCHIVE_ROOT, planner_dir)
    hook_status, _, _ = build_control_plane_automation_hook_dry_run_summary(
        _hook_inputs_from_planner_plan(
            chain_root=chain_dir,
            plan=plan,
            attachment_e2e_complete=True,
        )
    )
    assert hook_status == STATUS_READY_FOR_CP_HOOK_DRY_RUN
    assert plan["durable_attachment_contract_mode"] == planner_mod.DURABLE_ATTACHMENT_CONTRACT_MODE
