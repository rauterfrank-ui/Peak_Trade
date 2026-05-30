"""Control Plane first automation hook dry-run contract v0 (tests-only).

Defines CP-specific dry-run readiness for a future offline automation hook adapter.
Binds offline chain completion + pointer-only attachment E2E preconditions without
implementing hooks, CLIs, full automation, or any invoke/start/network/live behavior.
"""

from __future__ import annotations

import ast
from dataclasses import dataclass, replace
from pathlib import Path

import pytest

from scripts.ops import run_autonomous_ops_control_plane_offline_chain_v0 as chain_mod
from scripts.ops.primary_evidence_retention_v0 import is_under_tmp
from tests.ops.test_closeout_to_projection_chain_automation_contract_v0 import (
    build_post_closeout_hook_contract_summary,
)
from tests.ops.test_control_plane_offline_chain_attachment_e2e_contract_v0 import (
    EXPECTED_ALL_FIXTURE_FILES,
)
from tests.ops.test_control_plane_offline_chain_durable_evidence_attachment_contracts_v0 import (
    REQUIRED_CHAIN_REL_PATHS_V0,
    STATUS_BLOCKED_MISSING_REQUIRED_CHAIN_ARTIFACT,
    STATUS_BLOCKED_TARGET_ARCHIVE_ROOT_UNDER_TMP,
    STATUS_READY_FOR_DURABLE_ATTACHMENT_PLANNING,
    SYNTHETIC_DURABLE_ARCHIVE_ROOT,
    _chain_rel_paths_present,
    _evaluate_attachment_plan,
)
from tests.ops.test_control_plane_post_closeout_automation_readiness_contracts_v0 import (
    REQUIRED_BLOCKERS_BEFORE_FULL_AUTOMATION_V0,
)
from tests.ops.test_post_closeout_automation_hook_owner_precheck_v0 import (
    CANONICAL_HOOK_ATTACH_OWNERS,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
THIS_MODULE = Path(__file__)
FIXTURE_DIR = REPO_ROOT / "tests/fixtures/ops/control_plane_transition_v0"

STATUS_READY_FOR_CP_HOOK_DRY_RUN = "ready_for_control_plane_hook_dry_run"
STATUS_BLOCKED_OFFLINE_CHAIN_INCOMPLETE = "blocked_offline_chain_incomplete"
STATUS_BLOCKED_ATTACHMENT_NOT_READY = "blocked_attachment_not_ready"
STATUS_BLOCKED_POINTER_ONLY_REQUIRED = "blocked_pointer_only_required"
STATUS_BLOCKED_TARGET_ARCHIVE_UNDER_TMP = "blocked_target_archive_under_tmp"
STATUS_BLOCKED_HOOK_IMPLEMENTED = "blocked_hook_implemented"
STATUS_BLOCKED_FULL_AUTOMATION_CLAIMED = "blocked_full_automation_claimed"
STATUS_BLOCKED_INVOKE_OR_START_FLAG = "blocked_invoke_or_start_flag"

RUNTIME_GENERIC_HOOK_ATTACH_OWNER_IDS_V0: tuple[str, ...] = tuple(CANONICAL_HOOK_ATTACH_OWNERS)

DOCS_TRUTH_MAP = REPO_ROOT / "docs" / "ops" / "registry" / "DOCS_TRUTH_MAP.md"

CP_HOOK_DRY_RUN_OWNER_REFERENCES_V0: tuple[str, ...] = (
    "scripts/ops/summarize_control_plane_automation_hook_dry_run_v0.py",
    "tests/ops/test_summarize_control_plane_automation_hook_dry_run_contract_v0.py",
    "tests/ops/test_control_plane_planner_and_hook_summary_cli_e2e_contract_v0.py",
    "tests/ops/test_control_plane_offline_chain_attachment_e2e_contract_v0.py",
    "tests/ops/test_control_plane_offline_chain_durable_evidence_attachment_contracts_v0.py",
    "tests/ops/test_control_plane_post_closeout_automation_readiness_contracts_v0.py",
    "tests/ops/test_post_closeout_automation_hook_owner_precheck_v0.py",
    "tests/ops/test_post_closeout_hook_attach_readiness_bridge_v0.py",
    "tests/ops/test_closeout_to_projection_chain_automation_contract_v0.py",
)

CONTROL_PLANE_AUTOMATION_HOOK_DRY_RUN_MACHINE_LINES_V0: dict[str, str] = {
    "CONTROL_PLANE_AUTOMATION_HOOK_DRY_RUN_V0": "true",
    "HOOK_IMPLEMENTED": "false",
    "HOOK_DRY_RUN_ONLY": "true",
    "FULL_POST_CLOSEOUT_AUTOMATION_IMPLEMENTED": "false",
    "OFFLINE_CHAIN_COMPLETE_REQUIRED": "true",
    "ATTACHMENT_E2E_COMPLETE_REQUIRED": "true",
    "POINTER_ONLY_DURABLE_ATTACHMENT_REQUIRED": "true",
    "CLOSEOUT_INVOKED": "false",
    "PROJECTION_INVOKED": "false",
    "NOTION_SYNC_INVOKED": "false",
    "DURABLE_COPY_INVOKED": "false",
    "PRIMARY_EVIDENCE_RETENTION_INVOKED": "false",
    "MANIFEST_WRITE_INVOKED": "false",
    "COPY_VERIFY_INVOKED": "false",
    "RUNTIME_STARTED": "false",
    "SCHEDULER_STARTED": "false",
    "SUPERVISOR_STARTED": "false",
    "DAEMON_STARTED": "false",
    "PAPER_SHADOW_TESTNET_LIVE_STARTED": "false",
    "AWS_REMOTE_TOUCHED": "false",
    "S3_UPLOAD_REQUIRED": "false",
    "SSH_REQUIRED": "false",
    "NETWORK_REQUIRED": "false",
    "LIVE_AUTHORITY_CHANGED": "false",
    "MASTER_V2_DOUBLE_PLAY_TOUCHED": "false",
}

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
    "durable_closeout_copy_verify_v0.main(",
    "build_post_closeout_projection_payload_v0.main(",
    "notion_post_closeout_sync_dry_run_v0.main(",
    "primary_evidence_retention_v0.main(",
    "write_manifest_sha256(",
)


@dataclass(frozen=True)
class ControlPlaneAutomationHookDryRunInputs:
    """Synthetic CP automation hook dry-run readiness (tests only; not production API)."""

    offline_chain_complete: bool = False
    attachment_e2e_complete: bool = False
    attachment_status: str = STATUS_BLOCKED_MISSING_REQUIRED_CHAIN_ARTIFACT
    pointer_only: bool = False
    target_archive_root: Path | None = None
    hook_implemented: bool = False
    full_post_closeout_automation_implemented: bool = False
    closeout_invoked: bool = False
    projection_invoked: bool = False
    notion_sync_invoked: bool = False
    durable_copy_invoked: bool = False
    primary_evidence_retention_invoked: bool = False
    manifest_write_invoked: bool = False
    copy_verify_invoked: bool = False
    runtime_started: bool = False
    scheduler_started: bool = False
    supervisor_started: bool = False
    daemon_started: bool = False
    paper_shadow_testnet_live_started: bool = False
    aws_remote_touched: bool = False
    network_required: bool = False
    live_authority_changed: bool = False
    master_v2_double_play_touched: bool = False
    replaces_generic_hook_owners: bool = False


def build_control_plane_automation_hook_dry_run_summary(
    inp: ControlPlaneAutomationHookDryRunInputs,
) -> tuple[str, dict[str, str], list[str]]:
    """Return (status, machine_lines, blockers) for CP hook dry-run readiness (tests only)."""
    blockers: list[str] = []
    machine_lines = dict(CONTROL_PLANE_AUTOMATION_HOOK_DRY_RUN_MACHINE_LINES_V0)

    if not inp.offline_chain_complete:
        blockers.append("offline_chain_complete_required")
    if not inp.attachment_e2e_complete:
        blockers.append("attachment_e2e_complete_required")
    if inp.attachment_status != STATUS_READY_FOR_DURABLE_ATTACHMENT_PLANNING:
        blockers.append("attachment_status_not_ready_for_durable_attachment_planning")
    if not inp.pointer_only:
        blockers.append("pointer_only_durable_attachment_required")
    if inp.target_archive_root is None:
        blockers.append("target_archive_root_missing")
    elif is_under_tmp(inp.target_archive_root):
        blockers.append("target_archive_root_under_tmp")
    if inp.hook_implemented:
        blockers.append("hook_implemented_must_remain_false")
    if inp.full_post_closeout_automation_implemented:
        blockers.append("full_post_closeout_automation_must_remain_false")
    if inp.replaces_generic_hook_owners:
        blockers.append("must_not_replace_generic_post_closeout_hook_owners")

    invoke_flags = (
        ("closeout_invoked", inp.closeout_invoked),
        ("projection_invoked", inp.projection_invoked),
        ("notion_sync_invoked", inp.notion_sync_invoked),
        ("durable_copy_invoked", inp.durable_copy_invoked),
        ("primary_evidence_retention_invoked", inp.primary_evidence_retention_invoked),
        ("manifest_write_invoked", inp.manifest_write_invoked),
        ("copy_verify_invoked", inp.copy_verify_invoked),
        ("runtime_started", inp.runtime_started),
        ("scheduler_started", inp.scheduler_started),
        ("supervisor_started", inp.supervisor_started),
        ("daemon_started", inp.daemon_started),
        ("paper_shadow_testnet_live_started", inp.paper_shadow_testnet_live_started),
        ("aws_remote_touched", inp.aws_remote_touched),
        ("network_required", inp.network_required),
        ("live_authority_changed", inp.live_authority_changed),
        ("master_v2_double_play_touched", inp.master_v2_double_play_touched),
    )
    for name, value in invoke_flags:
        if value:
            blockers.append(f"forbidden_invoke_or_start:{name}")

    if blockers:
        if "offline_chain_complete_required" in blockers:
            status = STATUS_BLOCKED_OFFLINE_CHAIN_INCOMPLETE
        elif "attachment_e2e_complete_required" in blockers or (
            "attachment_status_not_ready_for_durable_attachment_planning" in blockers
        ):
            status = STATUS_BLOCKED_ATTACHMENT_NOT_READY
        elif "pointer_only_durable_attachment_required" in blockers:
            status = STATUS_BLOCKED_POINTER_ONLY_REQUIRED
        elif "target_archive_root_under_tmp" in blockers:
            status = STATUS_BLOCKED_TARGET_ARCHIVE_UNDER_TMP
        elif "hook_implemented_must_remain_false" in blockers:
            status = STATUS_BLOCKED_HOOK_IMPLEMENTED
        elif "full_post_closeout_automation_must_remain_false" in blockers:
            status = STATUS_BLOCKED_FULL_AUTOMATION_CLAIMED
        elif any(b.startswith("forbidden_invoke_or_start:") for b in blockers):
            status = STATUS_BLOCKED_INVOKE_OR_START_FLAG
        else:
            status = STATUS_BLOCKED_ATTACHMENT_NOT_READY
        machine_lines["CONTROL_PLANE_HOOK_DRY_RUN_STATUS"] = status
        return status, machine_lines, blockers

    machine_lines["CONTROL_PLANE_HOOK_DRY_RUN_STATUS"] = STATUS_READY_FOR_CP_HOOK_DRY_RUN
    return STATUS_READY_FOR_CP_HOOK_DRY_RUN, machine_lines, []


def _this_module_source() -> str:
    return THIS_MODULE.read_text(encoding="utf-8")


def _run_offline_chain(fixture: Path, outdir: Path) -> int:
    return chain_mod.main(["--fixture", str(fixture), "--outdir", str(outdir)])


def _synthetic_ready_inputs_from_chain(
    tmp_path: Path, fixture: Path
) -> ControlPlaneAutomationHookDryRunInputs:
    outdir = tmp_path / fixture.stem
    assert _run_offline_chain(fixture, outdir) == 0
    present, _ = _chain_rel_paths_present(outdir, REQUIRED_CHAIN_REL_PATHS_V0)
    assert present
    attachment_status, plan = _evaluate_attachment_plan(
        source_chain_root=outdir,
        target_archive_root=SYNTHETIC_DURABLE_ARCHIVE_ROOT,
    )
    return ControlPlaneAutomationHookDryRunInputs(
        offline_chain_complete=True,
        attachment_e2e_complete=True,
        attachment_status=attachment_status,
        pointer_only=plan.pointer_only,
        target_archive_root=SYNTHETIC_DURABLE_ARCHIVE_ROOT,
    )


def test_frozen_dry_run_machine_lines_v0() -> None:
    assert CONTROL_PLANE_AUTOMATION_HOOK_DRY_RUN_MACHINE_LINES_V0["HOOK_IMPLEMENTED"] == "false"
    assert CONTROL_PLANE_AUTOMATION_HOOK_DRY_RUN_MACHINE_LINES_V0["HOOK_DRY_RUN_ONLY"] == "true"
    assert (
        CONTROL_PLANE_AUTOMATION_HOOK_DRY_RUN_MACHINE_LINES_V0[
            "FULL_POST_CLOSEOUT_AUTOMATION_IMPLEMENTED"
        ]
        == "false"
    )
    assert (
        CONTROL_PLANE_AUTOMATION_HOOK_DRY_RUN_MACHINE_LINES_V0["OFFLINE_CHAIN_COMPLETE_REQUIRED"]
        == "true"
    )
    assert (
        CONTROL_PLANE_AUTOMATION_HOOK_DRY_RUN_MACHINE_LINES_V0["ATTACHMENT_E2E_COMPLETE_REQUIRED"]
        == "true"
    )
    true_required = {
        "OFFLINE_CHAIN_COMPLETE_REQUIRED",
        "ATTACHMENT_E2E_COMPLETE_REQUIRED",
        "POINTER_ONLY_DURABLE_ATTACHMENT_REQUIRED",
    }
    for key, value in CONTROL_PLANE_AUTOMATION_HOOK_DRY_RUN_MACHINE_LINES_V0.items():
        if key in true_required:
            assert value == "true", key
        elif key not in (
            "CONTROL_PLANE_AUTOMATION_HOOK_DRY_RUN_V0",
            "HOOK_DRY_RUN_ONLY",
        ):
            assert value == "false", key


@pytest.mark.parametrize("owner_rel", CP_HOOK_DRY_RUN_OWNER_REFERENCES_V0)
def test_cp_hook_dry_run_owner_references_exist_v0(owner_rel: str) -> None:
    assert (REPO_ROOT / owner_rel).is_file(), f"missing owner reference: {owner_rel!r}"


def test_docs_truth_map_records_control_plane_hook_dry_run_crosslink_chronicle_v0() -> None:
    docs_truth_map = DOCS_TRUTH_MAP.read_text(encoding="utf-8")

    assert "test_control_plane_first_automation_hook_dry_run_contract_v0.py" in docs_truth_map
    assert "#3802" in docs_truth_map
    assert "Control-Plane Hook Dry-Run Reciprocal Owner Crosslink v0" in docs_truth_map
    assert "FULL_POST_CLOSEOUT_AUTOMATION_IMPLEMENTED=false" in docs_truth_map
    assert "PREFLIGHT_REMAINS_BLOCKED=true" in docs_truth_map
    assert "STOP_IDLE_PRESERVED=true" in docs_truth_map


def test_automation_readiness_still_blocks_full_automation_v0() -> None:
    assert (
        "FULL_POST_CLOSEOUT_AUTOMATION_IMPLEMENTED=false"
        in REQUIRED_BLOCKERS_BEFORE_FULL_AUTOMATION_V0
    )


def test_generic_hook_contract_summary_exported_not_duplicated_v0() -> None:
    assert callable(build_post_closeout_hook_contract_summary)
    tree = ast.parse(_this_module_source())
    defined = {node.name for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)}
    assert "build_control_plane_automation_hook_dry_run_summary" in defined
    assert "build_post_closeout_hook_contract_summary" not in defined


def test_runtime_hook_attach_owners_referenced_not_replaced_v0() -> None:
    assert len(RUNTIME_GENERIC_HOOK_ATTACH_OWNER_IDS_V0) == 4
    assert "scheduler_completion" in RUNTIME_GENERIC_HOOK_ATTACH_OWNER_IDS_V0
    assert "must_not_replace_generic_post_closeout_hook_owners" in _this_module_source()


def test_attachment_e2e_module_covers_all_six_fixtures_v0() -> None:
    assert len(EXPECTED_ALL_FIXTURE_FILES) == 6


@pytest.mark.parametrize(
    "fixture_name",
    EXPECTED_ALL_FIXTURE_FILES,
    ids=lambda n: n.removesuffix(".json"),
)
def test_all_fixtures_ready_for_cp_hook_dry_run_v0(tmp_path: Path, fixture_name: str) -> None:
    fixture = FIXTURE_DIR / fixture_name
    inp = _synthetic_ready_inputs_from_chain(tmp_path, fixture)
    status, machine_lines, blockers = build_control_plane_automation_hook_dry_run_summary(inp)
    assert status == STATUS_READY_FOR_CP_HOOK_DRY_RUN
    assert blockers == []
    assert machine_lines["HOOK_IMPLEMENTED"] == "false"
    assert machine_lines["FULL_POST_CLOSEOUT_AUTOMATION_IMPLEMENTED"] == "false"


def test_blocked_when_offline_chain_incomplete_v0() -> None:
    inp = ControlPlaneAutomationHookDryRunInputs(
        offline_chain_complete=False,
        attachment_e2e_complete=True,
        attachment_status=STATUS_READY_FOR_DURABLE_ATTACHMENT_PLANNING,
        pointer_only=True,
        target_archive_root=SYNTHETIC_DURABLE_ARCHIVE_ROOT,
    )
    status, _, blockers = build_control_plane_automation_hook_dry_run_summary(inp)
    assert status == STATUS_BLOCKED_OFFLINE_CHAIN_INCOMPLETE
    assert "offline_chain_complete_required" in blockers


def test_blocked_when_attachment_status_not_ready_v0(tmp_path: Path) -> None:
    fixture = FIXTURE_DIR / EXPECTED_ALL_FIXTURE_FILES[0]
    outdir = tmp_path / "chain_partial"
    assert _run_offline_chain(fixture, outdir) == 0
    (outdir / REQUIRED_CHAIN_REL_PATHS_V0[0]).unlink()
    attachment_status, _ = _evaluate_attachment_plan(
        source_chain_root=outdir,
        target_archive_root=SYNTHETIC_DURABLE_ARCHIVE_ROOT,
    )
    inp = ControlPlaneAutomationHookDryRunInputs(
        offline_chain_complete=False,
        attachment_e2e_complete=True,
        attachment_status=attachment_status,
        pointer_only=True,
        target_archive_root=SYNTHETIC_DURABLE_ARCHIVE_ROOT,
    )
    status, _, blockers = build_control_plane_automation_hook_dry_run_summary(inp)
    assert status == STATUS_BLOCKED_OFFLINE_CHAIN_INCOMPLETE
    assert "offline_chain_complete_required" in blockers


def test_blocked_when_pointer_only_false_v0() -> None:
    inp = ControlPlaneAutomationHookDryRunInputs(
        offline_chain_complete=True,
        attachment_e2e_complete=True,
        attachment_status=STATUS_READY_FOR_DURABLE_ATTACHMENT_PLANNING,
        pointer_only=False,
        target_archive_root=SYNTHETIC_DURABLE_ARCHIVE_ROOT,
    )
    status, _, blockers = build_control_plane_automation_hook_dry_run_summary(inp)
    assert status == STATUS_BLOCKED_POINTER_ONLY_REQUIRED
    assert "pointer_only_durable_attachment_required" in blockers


def test_blocked_when_target_archive_under_tmp_v0(tmp_path: Path) -> None:
    fixture = FIXTURE_DIR / EXPECTED_ALL_FIXTURE_FILES[0]
    inp = _synthetic_ready_inputs_from_chain(tmp_path, fixture)
    inp = replace(inp, target_archive_root=Path("/tmp/cp_hook_dry_run_contract_v0"))
    status, _, blockers = build_control_plane_automation_hook_dry_run_summary(inp)
    assert status == STATUS_BLOCKED_TARGET_ARCHIVE_UNDER_TMP
    assert "target_archive_root_under_tmp" in blockers


def test_blocked_when_hook_implemented_true_v0() -> None:
    inp = ControlPlaneAutomationHookDryRunInputs(
        offline_chain_complete=True,
        attachment_e2e_complete=True,
        attachment_status=STATUS_READY_FOR_DURABLE_ATTACHMENT_PLANNING,
        pointer_only=True,
        target_archive_root=SYNTHETIC_DURABLE_ARCHIVE_ROOT,
        hook_implemented=True,
    )
    status, machine_lines, blockers = build_control_plane_automation_hook_dry_run_summary(inp)
    assert status == STATUS_BLOCKED_HOOK_IMPLEMENTED
    assert "hook_implemented_must_remain_false" in blockers
    assert machine_lines["HOOK_IMPLEMENTED"] == "false"


def test_blocked_when_full_automation_claimed_v0() -> None:
    inp = ControlPlaneAutomationHookDryRunInputs(
        offline_chain_complete=True,
        attachment_e2e_complete=True,
        attachment_status=STATUS_READY_FOR_DURABLE_ATTACHMENT_PLANNING,
        pointer_only=True,
        target_archive_root=SYNTHETIC_DURABLE_ARCHIVE_ROOT,
        full_post_closeout_automation_implemented=True,
    )
    status, machine_lines, blockers = build_control_plane_automation_hook_dry_run_summary(inp)
    assert status == STATUS_BLOCKED_FULL_AUTOMATION_CLAIMED
    assert "full_post_closeout_automation_must_remain_false" in blockers
    assert machine_lines["FULL_POST_CLOSEOUT_AUTOMATION_IMPLEMENTED"] == "false"


@pytest.mark.parametrize(
    "field",
    (
        "closeout_invoked",
        "projection_invoked",
        "notion_sync_invoked",
        "durable_copy_invoked",
        "scheduler_started",
        "runtime_started",
        "network_required",
    ),
)
def test_blocked_when_invoke_or_start_flag_set_v0(field: str) -> None:
    base = ControlPlaneAutomationHookDryRunInputs(
        offline_chain_complete=True,
        attachment_e2e_complete=True,
        attachment_status=STATUS_READY_FOR_DURABLE_ATTACHMENT_PLANNING,
        pointer_only=True,
        target_archive_root=SYNTHETIC_DURABLE_ARCHIVE_ROOT,
    )
    inp = replace(base, **{field: True})
    status, _, blockers = build_control_plane_automation_hook_dry_run_summary(inp)
    assert status == STATUS_BLOCKED_INVOKE_OR_START_FLAG
    assert f"forbidden_invoke_or_start:{field}" in blockers


def test_blocked_when_replaces_generic_hook_owners_v0() -> None:
    inp = ControlPlaneAutomationHookDryRunInputs(
        offline_chain_complete=True,
        attachment_e2e_complete=True,
        attachment_status=STATUS_READY_FOR_DURABLE_ATTACHMENT_PLANNING,
        pointer_only=True,
        target_archive_root=SYNTHETIC_DURABLE_ARCHIVE_ROOT,
        replaces_generic_hook_owners=True,
    )
    status, _, blockers = build_control_plane_automation_hook_dry_run_summary(inp)
    assert "must_not_replace_generic_post_closeout_hook_owners" in blockers


def test_blocked_attachment_status_under_tmp_maps_to_attachment_blocker_v0(
    tmp_path: Path,
) -> None:
    fixture = FIXTURE_DIR / EXPECTED_ALL_FIXTURE_FILES[0]
    outdir = tmp_path / "chain"
    assert _run_offline_chain(fixture, outdir) == 0
    tmp_archive = Path("/tmp/cp_hook_dry_run_attachment_tmp")
    attachment_status, plan = _evaluate_attachment_plan(
        source_chain_root=outdir,
        target_archive_root=tmp_archive,
    )
    assert attachment_status == STATUS_BLOCKED_TARGET_ARCHIVE_ROOT_UNDER_TMP
    inp = ControlPlaneAutomationHookDryRunInputs(
        offline_chain_complete=True,
        attachment_e2e_complete=True,
        attachment_status=attachment_status,
        pointer_only=plan.pointer_only,
        target_archive_root=tmp_archive,
    )
    status, _, blockers = build_control_plane_automation_hook_dry_run_summary(inp)
    assert status == STATUS_BLOCKED_ATTACHMENT_NOT_READY
    assert "attachment_status_not_ready_for_durable_attachment_planning" in blockers


def test_module_imports_are_stdlib_scripts_ops_tests_ops_only_v0() -> None:
    allowed_roots = frozenset(
        {"__future__", "ast", "dataclasses", "pathlib", "pytest", "scripts", "tests"}
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
                f"forbidden pattern in cp hook dry-run contract source: {pattern!r} line={line!r}"
            )


def test_hook_dry_run_summary_cli_e2e_reciprocal_owner_crosslink_v0() -> None:
    """The downstream hook-summary E2E terminus must point back to this upstream hook owner."""

    downstream_test = (
        REPO_ROOT / "tests/ops/test_control_plane_planner_and_hook_summary_cli_e2e_contract_v0.py"
    )
    downstream_source = downstream_test.read_text(encoding="utf-8")

    assert "E2E_OWNER_REFERENCES_V0" in downstream_source
    assert (
        "tests/ops/test_control_plane_first_automation_hook_dry_run_contract_v0.py"
        in downstream_source
    )
