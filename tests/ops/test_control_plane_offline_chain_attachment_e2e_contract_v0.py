"""Control Plane offline chain → pointer-only durable attachment E2E contract v0 (tests-only).

Proves all six transition fixtures flow: fixture → offline chain outputs → attachment planning
without copy, verify, manifest write, retention, closeout, projection, Notion, runtime, or network.
"""

from __future__ import annotations

import ast
import json
from pathlib import Path

import pytest

from scripts.ops import run_autonomous_ops_control_plane_offline_chain_v0 as chain_mod
from tests.ops.test_control_plane_offline_chain_durable_evidence_attachment_contracts_v0 import (
    CONTROL_PLANE_OFFLINE_CHAIN_DURABLE_ATTACHMENT_SCHEMA_VERSION_V0,
    REQUIRED_CHAIN_REL_PATHS_V0,
    STATUS_BLOCKED_MISSING_REQUIRED_CHAIN_ARTIFACT,
    STATUS_BLOCKED_TARGET_ARCHIVE_ROOT_UNDER_TMP,
    STATUS_READY_FOR_DURABLE_ATTACHMENT_PLANNING,
    SYNTHETIC_DURABLE_ARCHIVE_ROOT,
    ControlPlaneOfflineChainDurableAttachmentPlanV0,
    _chain_rel_paths_present,
    _evaluate_attachment_plan,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
THIS_MODULE = Path(__file__)
FIXTURE_DIR = REPO_ROOT / "tests/fixtures/ops/control_plane_transition_v0"

EXPECTED_ALL_FIXTURE_FILES: tuple[str, ...] = (
    "legal_ready_for_operator_token_path_v0.json",
    "forbidden_stop_idle_to_running_v0.json",
    "forbidden_preflight_blocked_to_running_v0.json",
    "forbidden_preflight_pass_to_running_without_operator_token_v0.json",
    "forbidden_running_to_evidence_verified_without_closeout_v0.json",
    "fail_closed_missing_evidence_v0.json",
)

E2E_ATTACHMENT_OWNER_REFERENCES_V0: tuple[str, ...] = (
    "scripts/ops/primary_evidence_retention_v0.py",
    "scripts/ops/durable_closeout_copy_verify_v0.py",
    "scripts/ops/run_autonomous_ops_control_plane_offline_chain_v0.py",
    "tests/ops/test_control_plane_offline_chain_durable_evidence_attachment_contracts_v0.py",
)

CHAIN_NON_AUTHORITY_JSON_KEYS: tuple[str, ...] = (
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


def _this_module_source() -> str:
    return THIS_MODULE.read_text(encoding="utf-8")


def _run_offline_chain(fixture: Path, outdir: Path) -> int:
    return chain_mod.main(["--fixture", str(fixture), "--outdir", str(outdir)])


def _load_chain(outdir: Path) -> dict:
    return json.loads(
        (outdir / chain_mod.CHAIN_JSON_FILENAME).read_text(encoding="utf-8"),
    )


def _load_fixture_meta(fixture_path: Path) -> dict:
    return json.loads(fixture_path.read_text(encoding="utf-8"))


def _assert_chain_status_mapping(chain: dict, *, expected_forbidden: bool) -> None:
    if expected_forbidden:
        assert chain["plan_status"] == "blocked"
        assert chain["readiness_status"] == "blocked"
    else:
        assert chain["plan_status"] == "plan_only"
        assert chain["readiness_status"] == "ready_for_projection_planning"


def _assert_chain_non_authority_flags(chain: dict) -> None:
    for key in CHAIN_NON_AUTHORITY_JSON_KEYS:
        assert chain[key] is False, f"expected chain {key}=false, got {chain[key]!r}"


def _assert_attachment_plan_non_authority(
    plan: ControlPlaneOfflineChainDurableAttachmentPlanV0,
) -> None:
    assert plan.schema_version == CONTROL_PLANE_OFFLINE_CHAIN_DURABLE_ATTACHMENT_SCHEMA_VERSION_V0
    assert plan.pointer_only is True
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


def _all_fixture_paths() -> list[Path]:
    return [FIXTURE_DIR / name for name in EXPECTED_ALL_FIXTURE_FILES]


def test_fixture_matrix_covers_all_six_explicit_fixtures_v0() -> None:
    paths = _all_fixture_paths()
    assert len(paths) == 6
    stems = {path.stem for path in paths}
    assert stems == {name.removesuffix(".json") for name in EXPECTED_ALL_FIXTURE_FILES}
    for path in paths:
        assert path.is_file(), f"missing fixture: {path}"


@pytest.mark.parametrize("fixture_path", _all_fixture_paths(), ids=lambda p: p.stem)
def test_all_fixtures_chain_to_attachment_e2e_v0(tmp_path: Path, fixture_path: Path) -> None:
    meta = _load_fixture_meta(fixture_path)
    outdir = tmp_path / fixture_path.stem
    assert _run_offline_chain(fixture_path, outdir) == 0

    present, missing = _chain_rel_paths_present(outdir, REQUIRED_CHAIN_REL_PATHS_V0)
    assert present, f"missing required chain artifact: {missing!r}"

    chain = _load_chain(outdir)
    _assert_chain_status_mapping(chain, expected_forbidden=meta["expected_forbidden"])
    _assert_chain_non_authority_flags(chain)

    status, plan = _evaluate_attachment_plan(
        source_chain_root=outdir,
        target_archive_root=SYNTHETIC_DURABLE_ARCHIVE_ROOT,
    )
    assert status == STATUS_READY_FOR_DURABLE_ATTACHMENT_PLANNING
    _assert_attachment_plan_non_authority(plan)
    assert plan.required_chain_rel_paths == REQUIRED_CHAIN_REL_PATHS_V0
    assert "Peak_Trade_runtime_evidence_archive" in plan.target_archive_root


def test_fail_closed_blocked_missing_required_chain_artifact_v0(tmp_path: Path) -> None:
    fixture = FIXTURE_DIR / EXPECTED_ALL_FIXTURE_FILES[0]
    outdir = tmp_path / "chain_partial"
    assert _run_offline_chain(fixture, outdir) == 0
    removed = outdir / REQUIRED_CHAIN_REL_PATHS_V0[0]
    assert removed.is_file()
    removed.unlink()

    status, plan = _evaluate_attachment_plan(
        source_chain_root=outdir,
        target_archive_root=SYNTHETIC_DURABLE_ARCHIVE_ROOT,
    )
    assert status == STATUS_BLOCKED_MISSING_REQUIRED_CHAIN_ARTIFACT
    _assert_attachment_plan_non_authority(plan)


def test_fail_closed_blocked_target_archive_root_under_tmp_v0(tmp_path: Path) -> None:
    fixture = FIXTURE_DIR / EXPECTED_ALL_FIXTURE_FILES[-1]
    outdir = tmp_path / "chain"
    assert _run_offline_chain(fixture, outdir) == 0
    tmp_archive = Path("/tmp/control_plane_offline_chain_attachment_e2e_contract_v0")

    status, plan = _evaluate_attachment_plan(
        source_chain_root=outdir,
        target_archive_root=tmp_archive,
    )
    assert status == STATUS_BLOCKED_TARGET_ARCHIVE_ROOT_UNDER_TMP
    _assert_attachment_plan_non_authority(plan)


@pytest.mark.parametrize("owner_rel", E2E_ATTACHMENT_OWNER_REFERENCES_V0)
def test_e2e_attachment_owner_references_exist_v0(owner_rel: str) -> None:
    assert (REPO_ROOT / owner_rel).is_file(), f"missing owner reference: {owner_rel!r}"


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
                f"forbidden pattern in e2e contract test source: {pattern!r} line={line!r}"
            )
