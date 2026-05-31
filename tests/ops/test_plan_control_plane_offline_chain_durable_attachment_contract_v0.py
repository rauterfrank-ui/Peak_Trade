"""Contract tests for Control Plane durable attachment planner CLI stub v0."""

from __future__ import annotations

import ast
import json
from pathlib import Path

import pytest

from scripts.ops import plan_control_plane_offline_chain_durable_attachment_v0 as planner_mod
from scripts.ops import run_autonomous_ops_control_plane_offline_chain_v0 as chain_mod
from tests.ops.test_control_plane_offline_chain_durable_evidence_attachment_contracts_v0 import (
    CONTROL_PLANE_OFFLINE_CHAIN_DURABLE_ATTACHMENT_SCHEMA_VERSION_V0,
    LEGAL_FIXTURE,
    REQUIRED_CHAIN_REL_PATHS_V0,
    STATUS_BLOCKED_MISSING_REQUIRED_CHAIN_ARTIFACT,
    STATUS_BLOCKED_TARGET_ARCHIVE_ROOT_UNDER_TMP,
    STATUS_READY_FOR_DURABLE_ATTACHMENT_PLANNING,
    SYNTHETIC_DURABLE_ARCHIVE_ROOT,
    _evaluate_attachment_plan,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
PLANNER_SCRIPT = REPO_ROOT / "scripts/ops/plan_control_plane_offline_chain_durable_attachment_v0.py"
THIS_MODULE = Path(__file__)

NON_AUTHORITY_JSON_KEYS: tuple[str, ...] = (
    "pointer_only",
    "durable_copy_invoked",
    "primary_evidence_retention_invoked",
    "manifest_write_invoked",
    "copy_verify_invoked",
    "closeout_invoked",
    "projection_invoked",
    "notion_sync_invoked",
    "hook_implemented",
    "full_post_closeout_automation_implemented",
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

DOCS_TRUTH_MAP = REPO_ROOT / "docs" / "ops" / "registry" / "DOCS_TRUTH_MAP.md"

CHARTER_NON_EXECUTING_EXTRA_FLAGS_V0: tuple[str, ...] = (
    "--run",
    "--live",
    "--dispatch",
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
    "durable_closeout_copy_verify_v0.main(",
    "build_post_closeout_projection_payload_v0.main(",
    "notion_post_closeout_sync_dry_run_v0.main(",
    "primary_evidence_retention_v0.main(",
    "write_manifest_sha256(",
)


def _this_module_source() -> str:
    return THIS_MODULE.read_text(encoding="utf-8")


def _planner_script_source() -> str:
    return PLANNER_SCRIPT.read_text(encoding="utf-8")


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


def _assert_plan_artifacts_exist(outdir: Path) -> None:
    assert (outdir / planner_mod.PLAN_JSON_FILENAME).is_file()
    assert (outdir / planner_mod.PLAN_MACHINE_LINES_FILENAME).is_file()
    assert (outdir / planner_mod.PLAN_MD_FILENAME).is_file()


def _assert_non_authority_flags_false(plan: dict) -> None:
    assert plan["pointer_only"] is True
    for key in NON_AUTHORITY_JSON_KEYS:
        if key == "pointer_only":
            continue
        assert plan[key] is False, f"expected {key}=false, got {plan[key]!r}"


def _assert_parity_with_test_helper(
    plan: dict,
    *,
    expected_status: str,
    source_chain_root: Path,
    target_archive_root: Path,
) -> None:
    helper_status, helper_plan = _evaluate_attachment_plan(
        source_chain_root=source_chain_root,
        target_archive_root=target_archive_root,
    )
    assert plan["status"] == helper_status == expected_status
    assert helper_status == expected_status
    assert plan["schema_version"] == helper_plan.schema_version
    assert (
        plan["schema_version"] == CONTROL_PLANE_OFFLINE_CHAIN_DURABLE_ATTACHMENT_SCHEMA_VERSION_V0
    )
    assert plan["pointer_only"] == helper_plan.pointer_only is True
    assert plan["target_archive_root_policy"] == helper_plan.target_archive_root_policy
    assert tuple(plan["required_chain_rel_paths"]) == helper_plan.required_chain_rel_paths
    assert plan["durable_copy_invoked"] == helper_plan.durable_copy_invoked is False
    assert plan["copy_verify_invoked"] == helper_plan.copy_verify_invoked is False


def test_planner_ready_case_matches_helper_and_writes_artifacts(tmp_path: Path) -> None:
    chain_dir = tmp_path / "chain"
    plan_dir = tmp_path / "plan_ready"
    assert _run_offline_chain(LEGAL_FIXTURE, chain_dir) == 0
    plan = _run_planner(chain_dir, SYNTHETIC_DURABLE_ARCHIVE_ROOT, plan_dir)
    _assert_plan_artifacts_exist(plan_dir)
    assert plan["status"] == STATUS_READY_FOR_DURABLE_ATTACHMENT_PLANNING
    assert plan["missing_chain_rel_paths"] == []
    _assert_non_authority_flags_false(plan)
    _assert_parity_with_test_helper(
        plan,
        expected_status=STATUS_READY_FOR_DURABLE_ATTACHMENT_PLANNING,
        source_chain_root=chain_dir,
        target_archive_root=SYNTHETIC_DURABLE_ARCHIVE_ROOT,
    )
    text1 = (plan_dir / planner_mod.PLAN_JSON_FILENAME).read_text(encoding="utf-8")
    assert _run_planner(chain_dir, SYNTHETIC_DURABLE_ARCHIVE_ROOT, plan_dir) is not None
    text2 = (plan_dir / planner_mod.PLAN_JSON_FILENAME).read_text(encoding="utf-8")
    assert text1 == text2


def test_planner_blocked_missing_chain_artifact_matches_helper(tmp_path: Path) -> None:
    chain_dir = tmp_path / "chain_empty"
    chain_dir.mkdir()
    plan_dir = tmp_path / "plan_missing"
    plan = _run_planner(chain_dir, SYNTHETIC_DURABLE_ARCHIVE_ROOT, plan_dir)
    _assert_plan_artifacts_exist(plan_dir)
    assert plan["status"] == STATUS_BLOCKED_MISSING_REQUIRED_CHAIN_ARTIFACT
    assert len(plan["missing_chain_rel_paths"]) > 0
    assert plan["missing_chain_rel_paths"][0] == REQUIRED_CHAIN_REL_PATHS_V0[0]
    _assert_non_authority_flags_false(plan)
    _assert_parity_with_test_helper(
        plan,
        expected_status=STATUS_BLOCKED_MISSING_REQUIRED_CHAIN_ARTIFACT,
        source_chain_root=chain_dir,
        target_archive_root=SYNTHETIC_DURABLE_ARCHIVE_ROOT,
    )


def test_planner_blocked_target_archive_under_tmp_matches_helper(tmp_path: Path) -> None:
    chain_dir = tmp_path / "chain"
    plan_dir = tmp_path / "plan_tmp"
    assert _run_offline_chain(LEGAL_FIXTURE, chain_dir) == 0
    tmp_archive = Path("/tmp/control_plane_durable_attachment_planner_contract_v0")
    plan = _run_planner(chain_dir, tmp_archive, plan_dir)
    _assert_plan_artifacts_exist(plan_dir)
    assert plan["status"] == STATUS_BLOCKED_TARGET_ARCHIVE_ROOT_UNDER_TMP
    assert plan["missing_chain_rel_paths"] == []
    _assert_non_authority_flags_false(plan)
    _assert_parity_with_test_helper(
        plan,
        expected_status=STATUS_BLOCKED_TARGET_ARCHIVE_ROOT_UNDER_TMP,
        source_chain_root=chain_dir,
        target_archive_root=tmp_archive,
    )


def test_planner_blocked_after_removing_chain_artifact(tmp_path: Path) -> None:
    chain_dir = tmp_path / "chain"
    plan_dir = tmp_path / "plan_partial"
    assert _run_offline_chain(LEGAL_FIXTURE, chain_dir) == 0
    removed_rel = REQUIRED_CHAIN_REL_PATHS_V0[0]
    (chain_dir / removed_rel).unlink()
    plan = _run_planner(chain_dir, SYNTHETIC_DURABLE_ARCHIVE_ROOT, plan_dir)
    assert plan["status"] == STATUS_BLOCKED_MISSING_REQUIRED_CHAIN_ARTIFACT
    assert removed_rel in plan["missing_chain_rel_paths"]
    _assert_parity_with_test_helper(
        plan,
        expected_status=STATUS_BLOCKED_MISSING_REQUIRED_CHAIN_ARTIFACT,
        source_chain_root=chain_dir,
        target_archive_root=SYNTHETIC_DURABLE_ARCHIVE_ROOT,
    )


@pytest.mark.parametrize("owner_rel", planner_mod.OWNER_REFERENCES_V0)
def test_owner_references_exist_v0(owner_rel: str) -> None:
    assert (REPO_ROOT / owner_rel).is_file(), f"missing owner reference: {owner_rel!r}"


def test_machine_lines_include_required_keys_v0(tmp_path: Path) -> None:
    chain_dir = tmp_path / "chain"
    plan_dir = tmp_path / "plan_ml"
    assert _run_offline_chain(LEGAL_FIXTURE, chain_dir) == 0
    plan = _run_planner(chain_dir, SYNTHETIC_DURABLE_ARCHIVE_ROOT, plan_dir)
    for key in planner_mod.PLAN_MACHINE_LINE_KEYS:
        assert key in plan["machine_lines"]
    ml_text = (plan_dir / planner_mod.PLAN_MACHINE_LINES_FILENAME).read_text(encoding="utf-8")
    assert "CONTROL_PLANE_DURABLE_ATTACHMENT_PLANNER_CLI_STUB_V0=true" in ml_text
    assert "HOOK_IMPLEMENTED=false" in ml_text
    assert "FULL_POST_CLOSEOUT_AUTOMATION_IMPLEMENTED=false" in ml_text


def test_cli_parser_has_no_forbidden_flags_v0() -> None:
    source = _planner_script_source()
    for flag in planner_mod.FORBIDDEN_CLI_FLAGS:
        assert f'add_argument("{flag}"' not in source
        assert f"add_argument('{flag}'" not in source

    for flag in CHARTER_NON_EXECUTING_EXTRA_FLAGS_V0:
        assert f'add_argument("{flag}"' not in source
        assert f"add_argument('{flag}'" not in source

    assert "workflow_dispatch" not in source


def test_docs_truth_map_records_pr3810_offline_stub_symmetry_chronicle_v0() -> None:
    docs_truth_map = DOCS_TRUTH_MAP.read_text(encoding="utf-8")

    assert "#3810" in docs_truth_map
    assert "Control-Plane offline stub symmetry package" in docs_truth_map
    assert (
        "test_plan_control_plane_offline_chain_durable_attachment_contract_v0.py" in docs_truth_map
    )
    assert "test_summarize_control_plane_automation_hook_dry_run_contract_v0.py" in docs_truth_map


def test_planner_script_has_no_runtime_or_invocation_patterns_v0() -> None:
    source = _planner_script_source()
    for pattern in _FORBIDDEN_SOURCE_PATTERNS:
        assert pattern not in source, f"forbidden pattern in planner script: {pattern!r}"


def test_contract_module_has_no_runtime_or_invocation_patterns_v0() -> None:
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


def test_contract_module_imports_are_stdlib_scripts_ops_tests_ops_only_v0() -> None:
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


def test_planner_exits_2_on_malformed_chain_json_artifact(tmp_path: Path) -> None:
    chain_dir = tmp_path / "chain"
    plan_dir = tmp_path / "plan_malformed"
    assert _run_offline_chain(LEGAL_FIXTURE, chain_dir) == 0
    malformed_rel = "CONTROL_PLANE_OFFLINE_CHAIN_V0.json"
    (chain_dir / malformed_rel).write_text("{not-json\n", encoding="utf-8")
    rc = planner_mod.main(
        [
            "--chain-root",
            str(chain_dir),
            "--target-archive-root",
            str(SYNTHETIC_DURABLE_ARCHIVE_ROOT),
            "--outdir",
            str(plan_dir),
        ]
    )
    assert rc == 2
    assert not (plan_dir / planner_mod.PLAN_JSON_FILENAME).exists()
