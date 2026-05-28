"""Control Plane offline chain durable-evidence attachment contracts v0 (tests-only).

Models pointer-only attachment planning for offline chain outputs into durable evidence
archives later. Does not invoke copy, verify, manifest write, closeout, projection,
Notion, retention, runtime, or network.
"""

from __future__ import annotations

import ast
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

import pytest

from scripts.ops import run_autonomous_ops_control_plane_offline_chain_v0 as chain_mod
from scripts.ops.primary_evidence_retention_v0 import is_under_tmp

REPO_ROOT = Path(__file__).resolve().parents[2]
THIS_MODULE = Path(__file__)
FIXTURE_DIR = REPO_ROOT / "tests/fixtures/ops/control_plane_transition_v0"
LEGAL_FIXTURE = FIXTURE_DIR / "legal_ready_for_operator_token_path_v0.json"

CONTROL_PLANE_OFFLINE_CHAIN_DURABLE_ATTACHMENT_SCHEMA_VERSION_V0 = (
    "control_plane_offline_chain_durable_attachment_v0"
)

REQUIRED_CHAIN_REL_PATHS_V0: tuple[str, ...] = (
    "plan/CONTROL_PLANE_PLAN_V0.json",
    "plan/CONTROL_PLANE_PLAN_MACHINE_LINES.txt",
    "plan/CONTROL_PLANE_PLAN_V0.md",
    "readiness/CONTROL_PLANE_POST_CLOSEOUT_READINESS_V0.json",
    "readiness/CONTROL_PLANE_POST_CLOSEOUT_READINESS_MACHINE_LINES.txt",
    "readiness/CONTROL_PLANE_POST_CLOSEOUT_READINESS_V0.md",
    "CONTROL_PLANE_OFFLINE_CHAIN_V0.json",
    "CONTROL_PLANE_OFFLINE_CHAIN_MACHINE_LINES.txt",
    "CONTROL_PLANE_OFFLINE_CHAIN_V0.md",
)

ATTACHMENT_OWNER_REFERENCES_V0: tuple[str, ...] = (
    "scripts/ops/primary_evidence_retention_v0.py",
    "scripts/ops/durable_closeout_copy_verify_v0.py",
    "scripts/ops/run_autonomous_ops_control_plane_offline_chain_v0.py",
    "tests/ops/test_autonomous_ops_control_plane_offline_orchestrator_contract_v0.py",
)

STATUS_READY_FOR_DURABLE_ATTACHMENT_PLANNING = "ready_for_durable_attachment_planning"
STATUS_BLOCKED_MISSING_REQUIRED_CHAIN_ARTIFACT = "blocked_missing_required_chain_artifact"
STATUS_BLOCKED_TARGET_ARCHIVE_ROOT_UNDER_TMP = "blocked_target_archive_root_under_tmp"

SYNTHETIC_DURABLE_ARCHIVE_ROOT = Path(
    "/Users/frnkhrz/Documents/Peak_Trade_runtime_evidence_archive_20260520T161443Z"
    "/closeout/control_plane_offline_chain_durable_attachment_contracts_v0_synthetic"
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
    "write_manifest_sha256(",
)


@dataclass(frozen=True)
class ControlPlaneOfflineChainDurableAttachmentPlanV0:
    schema_version: str
    source_chain_root: str
    target_archive_root: str
    required_chain_rel_paths: tuple[str, ...]
    target_archive_root_policy: str
    pointer_only: bool
    durable_copy_invoked: bool
    primary_evidence_retention_invoked: bool
    manifest_write_invoked: bool
    copy_verify_invoked: bool
    runtime_started: bool
    scheduler_started: bool
    aws_remote_touched: bool
    network_required: bool
    live_authority_changed: bool
    master_v2_double_play_touched: bool


def _this_module_source() -> str:
    return THIS_MODULE.read_text(encoding="utf-8")


def _run_offline_chain(fixture: Path, outdir: Path) -> int:
    return chain_mod.main(["--fixture", str(fixture), "--outdir", str(outdir)])


def _chain_rel_paths_present(
    chain_root: Path, rel_paths: tuple[str, ...]
) -> tuple[bool, str | None]:
    for rel in rel_paths:
        if not (chain_root / rel).is_file():
            return False, rel
    return True, None


def _evaluate_attachment_plan(
    *,
    source_chain_root: Path,
    target_archive_root: Path,
    required_chain_rel_paths: tuple[str, ...] = REQUIRED_CHAIN_REL_PATHS_V0,
) -> tuple[str, ControlPlaneOfflineChainDurableAttachmentPlanV0]:
    present, _missing = _chain_rel_paths_present(source_chain_root, required_chain_rel_paths)

    if not present:
        status = STATUS_BLOCKED_MISSING_REQUIRED_CHAIN_ARTIFACT
    elif is_under_tmp(target_archive_root):
        status = STATUS_BLOCKED_TARGET_ARCHIVE_ROOT_UNDER_TMP
    else:
        status = STATUS_READY_FOR_DURABLE_ATTACHMENT_PLANNING

    plan = ControlPlaneOfflineChainDurableAttachmentPlanV0(
        schema_version=CONTROL_PLANE_OFFLINE_CHAIN_DURABLE_ATTACHMENT_SCHEMA_VERSION_V0,
        source_chain_root=str(source_chain_root),
        target_archive_root=str(target_archive_root),
        required_chain_rel_paths=required_chain_rel_paths,
        target_archive_root_policy="must_be_outside_tmp",
        pointer_only=True,
        durable_copy_invoked=False,
        primary_evidence_retention_invoked=False,
        manifest_write_invoked=False,
        copy_verify_invoked=False,
        runtime_started=False,
        scheduler_started=False,
        aws_remote_touched=False,
        network_required=False,
        live_authority_changed=False,
        master_v2_double_play_touched=False,
    )
    return status, plan


def test_required_chain_rel_paths_mirror_orchestrator_outputs_v0() -> None:
    orchestrator = REPO_ROOT / "scripts/ops/run_autonomous_ops_control_plane_offline_chain_v0.py"
    text = orchestrator.read_text(encoding="utf-8")
    assert chain_mod.PLAN_SUBDIR == "plan"
    assert chain_mod.READINESS_SUBDIR == "readiness"
    assert chain_mod.CHAIN_JSON_FILENAME in text
    assert chain_mod.CHAIN_MACHINE_LINES_FILENAME in text
    assert chain_mod.CHAIN_MD_FILENAME in text
    assert len(REQUIRED_CHAIN_REL_PATHS_V0) == 9


def test_offline_orchestrator_creates_all_required_chain_rel_paths_v0(tmp_path: Path) -> None:
    outdir = tmp_path / "chain"
    assert _run_offline_chain(LEGAL_FIXTURE, outdir) == 0
    present, missing = _chain_rel_paths_present(outdir, REQUIRED_CHAIN_REL_PATHS_V0)
    assert present, f"missing required chain artifact: {missing!r}"


def test_attachment_plan_ready_for_durable_attachment_planning_v0(tmp_path: Path) -> None:
    outdir = tmp_path / "chain"
    assert _run_offline_chain(LEGAL_FIXTURE, outdir) == 0
    status, plan = _evaluate_attachment_plan(
        source_chain_root=outdir,
        target_archive_root=SYNTHETIC_DURABLE_ARCHIVE_ROOT,
    )
    assert status == STATUS_READY_FOR_DURABLE_ATTACHMENT_PLANNING
    assert plan.schema_version == CONTROL_PLANE_OFFLINE_CHAIN_DURABLE_ATTACHMENT_SCHEMA_VERSION_V0
    assert plan.pointer_only is True
    assert plan.target_archive_root_policy == "must_be_outside_tmp"
    assert plan.durable_copy_invoked is False
    assert plan.primary_evidence_retention_invoked is False
    assert plan.manifest_write_invoked is False
    assert plan.copy_verify_invoked is False
    assert plan.runtime_started is False
    assert plan.scheduler_started is False
    assert plan.aws_remote_touched is False
    assert plan.network_required is False
    assert plan.live_authority_changed is False
    assert plan.master_v2_double_play_touched is False


def test_attachment_plan_blocked_when_required_chain_artifact_missing_v0(tmp_path: Path) -> None:
    outdir = tmp_path / "chain"
    outdir.mkdir()
    status, plan = _evaluate_attachment_plan(
        source_chain_root=outdir,
        target_archive_root=SYNTHETIC_DURABLE_ARCHIVE_ROOT,
    )
    assert status == STATUS_BLOCKED_MISSING_REQUIRED_CHAIN_ARTIFACT
    assert plan.pointer_only is True
    assert plan.durable_copy_invoked is False


def test_attachment_plan_blocked_when_target_archive_root_under_tmp_v0(tmp_path: Path) -> None:
    outdir = tmp_path / "chain"
    assert _run_offline_chain(LEGAL_FIXTURE, outdir) == 0
    tmp_archive = Path("/tmp/control_plane_offline_chain_durable_attachment_contracts_v0")
    status, plan = _evaluate_attachment_plan(
        source_chain_root=outdir,
        target_archive_root=tmp_archive,
    )
    assert status == STATUS_BLOCKED_TARGET_ARCHIVE_ROOT_UNDER_TMP
    assert is_under_tmp(tmp_archive)
    assert plan.durable_copy_invoked is False


def test_documents_style_archive_root_accepted_by_policy_v0() -> None:
    assert not is_under_tmp(SYNTHETIC_DURABLE_ARCHIVE_ROOT)
    assert "Peak_Trade_runtime_evidence_archive" in str(SYNTHETIC_DURABLE_ARCHIVE_ROOT)


@pytest.mark.parametrize("owner_rel", ATTACHMENT_OWNER_REFERENCES_V0)
def test_attachment_owner_references_exist_v0(owner_rel: str) -> None:
    assert (REPO_ROOT / owner_rel).is_file(), f"missing owner reference: {owner_rel!r}"


def test_synthetic_attachment_plan_dict_shape_v0(tmp_path: Path) -> None:
    outdir = tmp_path / "chain"
    assert _run_offline_chain(LEGAL_FIXTURE, outdir) == 0
    _, plan = _evaluate_attachment_plan(
        source_chain_root=outdir,
        target_archive_root=SYNTHETIC_DURABLE_ARCHIVE_ROOT,
    )
    payload: dict[str, Any] = asdict(plan)
    assert (
        payload["schema_version"]
        == CONTROL_PLANE_OFFLINE_CHAIN_DURABLE_ATTACHMENT_SCHEMA_VERSION_V0
    )
    assert payload["required_chain_rel_paths"] == REQUIRED_CHAIN_REL_PATHS_V0
    assert payload["pointer_only"] is True
    for key in (
        "durable_copy_invoked",
        "primary_evidence_retention_invoked",
        "manifest_write_invoked",
        "copy_verify_invoked",
        "runtime_started",
        "scheduler_started",
        "aws_remote_touched",
        "network_required",
        "live_authority_changed",
        "master_v2_double_play_touched",
    ):
        assert payload[key] is False, key


def test_module_imports_are_stdlib_scripts_ops_only_v0() -> None:
    allowed_roots = frozenset(
        {"__future__", "ast", "dataclasses", "pathlib", "typing", "pytest", "scripts"}
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
                f"forbidden pattern in contract test source: {pattern!r} line={line!r}"
            )
