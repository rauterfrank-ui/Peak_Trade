"""Contract tests for Control Plane hook dry-run summary CLI stub v0."""

from __future__ import annotations

import ast
import json
from pathlib import Path

import pytest

from scripts.ops import plan_control_plane_offline_chain_durable_attachment_v0 as planner_mod
from scripts.ops import run_autonomous_ops_control_plane_offline_chain_v0 as chain_mod
from scripts.ops import summarize_control_plane_automation_hook_dry_run_v0 as summary_mod
from tests.ops.test_control_plane_first_automation_hook_dry_run_contract_v0 import (
    STATUS_READY_FOR_CP_HOOK_DRY_RUN,
    ControlPlaneAutomationHookDryRunInputs,
    build_control_plane_automation_hook_dry_run_summary as contract_build_summary,
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
SUMMARY_SCRIPT = REPO_ROOT / "scripts/ops/summarize_control_plane_automation_hook_dry_run_v0.py"
THIS_MODULE = Path(__file__)

HOOK_MACHINE_LINE_ASSERTIONS: tuple[str, ...] = (
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
    "KRAKEN_TESTNET_CRON_REARMED=false",
    "AI_PAID_VARS_REARMED=false",
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
    'add_argument("--copy"',
    'add_argument("--verify"',
    'add_argument("--retention"',
    'add_argument("--closeout"',
    'add_argument("--projection"',
    'add_argument("--notion-sync"',
    'add_argument("--upload"',
    'add_argument("--s3"',
    'add_argument("--ssh"',
    'add_argument("--start"',
    "durable_closeout_copy_verify_v0.main(",
    "build_post_closeout_projection_payload_v0.main(",
    "notion_post_closeout_sync_dry_run_v0.main(",
    "primary_evidence_retention_v0.main(",
    "write_manifest_sha256(",
)


def _this_module_source() -> str:
    return THIS_MODULE.read_text(encoding="utf-8")


def _summary_script_source() -> str:
    return SUMMARY_SCRIPT.read_text(encoding="utf-8")


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


def _run_summary(chain_root: Path, attachment_plan: Path, outdir: Path) -> dict:
    assert (
        summary_mod.main(
            [
                "--chain-root",
                str(chain_root),
                "--attachment-plan",
                str(attachment_plan),
                "--outdir",
                str(outdir),
            ]
        )
        == 0
    )
    return json.loads(
        (outdir / summary_mod.SUMMARY_JSON_FILENAME).read_text(encoding="utf-8"),
    )


def _assert_summary_artifacts_exist(outdir: Path) -> None:
    assert (outdir / summary_mod.SUMMARY_JSON_FILENAME).is_file()
    assert (outdir / summary_mod.SUMMARY_MACHINE_LINES_FILENAME).is_file()
    assert (outdir / summary_mod.SUMMARY_MD_FILENAME).is_file()


def _assert_machine_lines_safety(machine_lines: dict[str, str]) -> None:
    for assertion in HOOK_MACHINE_LINE_ASSERTIONS:
        key, _, value = assertion.partition("=")
        assert machine_lines[key] == value, f"expected {assertion}"


def _contract_inputs_from_planner_plan(
    *,
    chain_root: Path,
    plan: dict,
) -> ControlPlaneAutomationHookDryRunInputs:
    offline_chain_complete = len(plan.get("missing_chain_rel_paths") or []) == 0
    return ControlPlaneAutomationHookDryRunInputs(
        offline_chain_complete=offline_chain_complete,
        attachment_e2e_complete=True,
        attachment_status=str(plan["status"]),
        pointer_only=bool(plan["pointer_only"]),
        target_archive_root=Path(plan["target_archive_root"]),
    )


def _assert_parity_with_contract_helper(
    summary: dict,
    *,
    chain_root: Path,
    plan: dict,
) -> None:
    inp = _contract_inputs_from_planner_plan(chain_root=chain_root, plan=plan)
    expected_status, _, expected_blockers = contract_build_summary(inp)
    assert summary["status"] == expected_status
    assert summary["blockers"] == expected_blockers


def test_summary_ready_case_writes_artifacts_and_matches_contract_v0(tmp_path: Path) -> None:
    chain_dir = tmp_path / "chain"
    planner_dir = tmp_path / "planner"
    summary_dir = tmp_path / "summary_ready"
    assert _run_offline_chain(LEGAL_FIXTURE, chain_dir) == 0
    plan = _run_planner(chain_dir, SYNTHETIC_DURABLE_ARCHIVE_ROOT, planner_dir)
    plan_path = planner_dir / planner_mod.PLAN_JSON_FILENAME

    summary = _run_summary(chain_dir, plan_path, summary_dir)
    _assert_summary_artifacts_exist(summary_dir)
    assert summary["status"] == STATUS_READY_FOR_CP_HOOK_DRY_RUN
    assert summary["attachment_plan_status"] == STATUS_READY_FOR_DURABLE_ATTACHMENT_PLANNING
    assert summary["hook_implemented"] is False
    assert summary["hook_dry_run_only"] is True
    assert summary["full_post_closeout_automation_implemented"] is False
    assert summary["schema_version"] == summary_mod.SCHEMA_VERSION
    _assert_machine_lines_safety(summary["machine_lines"])
    _assert_parity_with_contract_helper(summary, chain_root=chain_dir, plan=plan)

    text1 = (summary_dir / summary_mod.SUMMARY_JSON_FILENAME).read_text(encoding="utf-8")
    assert _run_summary(chain_dir, plan_path, summary_dir) is not None
    text2 = (summary_dir / summary_mod.SUMMARY_JSON_FILENAME).read_text(encoding="utf-8")
    assert text1 == text2


def test_summary_blocked_missing_chain_artifact_not_ready_v0(tmp_path: Path) -> None:
    chain_dir = tmp_path / "chain_partial"
    planner_dir = tmp_path / "planner_blocked"
    summary_dir = tmp_path / "summary_blocked"
    assert _run_offline_chain(LEGAL_FIXTURE, chain_dir) == 0
    removed_rel = REQUIRED_CHAIN_REL_PATHS_V0[0]
    (chain_dir / removed_rel).unlink()

    plan = _run_planner(chain_dir, SYNTHETIC_DURABLE_ARCHIVE_ROOT, planner_dir)
    assert plan["status"] == STATUS_BLOCKED_MISSING_REQUIRED_CHAIN_ARTIFACT
    plan_path = planner_dir / planner_mod.PLAN_JSON_FILENAME

    summary = _run_summary(chain_dir, plan_path, summary_dir)
    _assert_summary_artifacts_exist(summary_dir)
    assert summary["status"] != STATUS_READY_FOR_CP_HOOK_DRY_RUN
    _assert_machine_lines_safety(summary["machine_lines"])
    _assert_parity_with_contract_helper(summary, chain_root=chain_dir, plan=plan)


def test_summary_blocked_tmp_target_archive_not_ready_v0(tmp_path: Path) -> None:
    chain_dir = tmp_path / "chain"
    planner_dir = tmp_path / "planner_tmp"
    summary_dir = tmp_path / "summary_tmp"
    assert _run_offline_chain(LEGAL_FIXTURE, chain_dir) == 0
    tmp_archive = Path("/tmp/control_plane_hook_dry_run_summary_cli_contract_v0")

    plan = _run_planner(chain_dir, tmp_archive, planner_dir)
    assert plan["status"] == STATUS_BLOCKED_TARGET_ARCHIVE_ROOT_UNDER_TMP
    plan_path = planner_dir / planner_mod.PLAN_JSON_FILENAME

    summary = _run_summary(chain_dir, plan_path, summary_dir)
    _assert_summary_artifacts_exist(summary_dir)
    assert summary["status"] != STATUS_READY_FOR_CP_HOOK_DRY_RUN
    _assert_machine_lines_safety(summary["machine_lines"])
    _assert_parity_with_contract_helper(summary, chain_root=chain_dir, plan=plan)


@pytest.mark.parametrize("owner_rel", summary_mod.OWNER_REFERENCES_V0)
def test_summary_owner_references_exist_v0(owner_rel: str) -> None:
    assert (REPO_ROOT / owner_rel).is_file(), f"missing owner reference: {owner_rel!r}"


def test_summary_script_has_no_forbidden_cli_flags_v0() -> None:
    source = _summary_script_source()
    for flag in summary_mod.FORBIDDEN_CLI_FLAGS:
        assert f'add_argument("{flag}"' not in source
        assert f"add_argument('{flag}'" not in source

    for flag in CHARTER_NON_EXECUTING_EXTRA_FLAGS_V0:
        assert f'add_argument("{flag}"' not in source
        assert f"add_argument('{flag}'" not in source

    assert "workflow_dispatch" not in source


def test_docs_truth_map_records_summary_forbidden_cli_flags_chronicle_v0() -> None:
    docs_truth_map = DOCS_TRUTH_MAP.read_text(encoding="utf-8")

    assert "test_summarize_control_plane_automation_hook_dry_run_contract_v0.py" in docs_truth_map
    assert "#3808" in docs_truth_map
    assert "Control-Plane summary forbidden CLI flags lock" in docs_truth_map
    assert "--run" in docs_truth_map
    assert "--live" in docs_truth_map
    assert "--dispatch" in docs_truth_map
    assert "workflow_dispatch" in docs_truth_map
    assert "STOP_IDLE" in docs_truth_map


def test_docs_truth_map_records_pr3810_offline_stub_symmetry_chronicle_v0() -> None:
    docs_truth_map = DOCS_TRUTH_MAP.read_text(encoding="utf-8")

    assert "#3810" in docs_truth_map
    assert "Control-Plane offline stub symmetry package" in docs_truth_map
    assert "test_summarize_control_plane_automation_hook_dry_run_contract_v0.py" in docs_truth_map
    assert (
        "test_plan_control_plane_offline_chain_durable_attachment_contract_v0.py" in docs_truth_map
    )


def test_docs_truth_map_records_pr3812_summary_docs_pointer_lock_chronicle_v0() -> None:
    docs_truth_map = DOCS_TRUTH_MAP.read_text(encoding="utf-8")

    assert "#3812" in docs_truth_map
    assert "Summary DOCS #3810 pointer lock" in docs_truth_map
    assert "test_summarize_control_plane_automation_hook_dry_run_contract_v0.py" in docs_truth_map


def test_summary_script_has_no_runtime_or_invocation_patterns_v0() -> None:
    for pattern in _FORBIDDEN_SOURCE_PATTERNS:
        assert pattern not in _summary_script_source(), (
            f"forbidden pattern in summary script: {pattern!r}"
        )


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


def test_summary_machine_lines_include_required_keys_v0(tmp_path: Path) -> None:
    chain_dir = tmp_path / "chain"
    planner_dir = tmp_path / "planner"
    summary_dir = tmp_path / "summary_ml"
    assert _run_offline_chain(LEGAL_FIXTURE, chain_dir) == 0
    plan = _run_planner(chain_dir, SYNTHETIC_DURABLE_ARCHIVE_ROOT, planner_dir)
    plan_path = planner_dir / planner_mod.PLAN_JSON_FILENAME
    summary = _run_summary(chain_dir, plan_path, summary_dir)
    for key in summary_mod.SUMMARY_MACHINE_LINE_KEYS:
        assert key in summary["machine_lines"]
    ml_text = (summary_dir / summary_mod.SUMMARY_MACHINE_LINES_FILENAME).read_text(
        encoding="utf-8",
    )
    assert "CONTROL_PLANE_HOOK_DRY_RUN_SUMMARY_CLI_STUB_V0=true" in ml_text
    assert "HOOK_IMPLEMENTED=false" in ml_text
    assert plan["status"] == STATUS_READY_FOR_DURABLE_ATTACHMENT_PLANNING


def test_summary_script_forbidden_flags_match_planner_posture_v0() -> None:
    assert summary_mod.FORBIDDEN_CLI_FLAGS == planner_mod.FORBIDDEN_CLI_FLAGS


def _write_minimal_valid_attachment_plan(path: Path) -> None:
    path.write_text(
        json.dumps(
            {
                "schema_version": planner_mod.SCHEMA_VERSION,
                "status": STATUS_READY_FOR_DURABLE_ATTACHMENT_PLANNING,
                "pointer_only": True,
                "target_archive_root": str(SYNTHETIC_DURABLE_ARCHIVE_ROOT),
                "hook_implemented": False,
                "full_post_closeout_automation_implemented": False,
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )


def test_summary_exits_2_on_malformed_attachment_plan_json(tmp_path: Path) -> None:
    chain_dir = tmp_path / "chain"
    summary_dir = tmp_path / "summary_malformed"
    assert _run_offline_chain(LEGAL_FIXTURE, chain_dir) == 0
    plan_path = tmp_path / "malformed_plan.json"
    plan_path.write_text("{not-json\n", encoding="utf-8")
    rc = summary_mod.main(
        [
            "--chain-root",
            str(chain_dir),
            "--attachment-plan",
            str(plan_path),
            "--outdir",
            str(summary_dir),
        ]
    )
    assert rc == 2
    assert not (summary_dir / summary_mod.SUMMARY_JSON_FILENAME).exists()


@pytest.mark.parametrize(
    ("plan_body", "expected_substring"),
    [
        (
            {
                "status": STATUS_READY_FOR_DURABLE_ATTACHMENT_PLANNING,
                "pointer_only": True,
                "target_archive_root": str(SYNTHETIC_DURABLE_ARCHIVE_ROOT),
                "hook_implemented": False,
                "full_post_closeout_automation_implemented": False,
            },
            "missing keys",
        ),
        (
            {
                "schema_version": "wrong_schema_v0",
                "status": STATUS_READY_FOR_DURABLE_ATTACHMENT_PLANNING,
                "pointer_only": True,
                "target_archive_root": str(SYNTHETIC_DURABLE_ARCHIVE_ROOT),
                "hook_implemented": False,
                "full_post_closeout_automation_implemented": False,
            },
            "unsupported attachment plan schema",
        ),
        (
            {
                "schema_version": planner_mod.SCHEMA_VERSION,
                "status": STATUS_READY_FOR_DURABLE_ATTACHMENT_PLANNING,
                "pointer_only": True,
                "target_archive_root": str(SYNTHETIC_DURABLE_ARCHIVE_ROOT),
                "hook_implemented": True,
                "full_post_closeout_automation_implemented": False,
            },
            "hook_implemented must remain false",
        ),
        (
            {
                "schema_version": planner_mod.SCHEMA_VERSION,
                "status": STATUS_READY_FOR_DURABLE_ATTACHMENT_PLANNING,
                "pointer_only": True,
                "target_archive_root": str(SYNTHETIC_DURABLE_ARCHIVE_ROOT),
                "hook_implemented": False,
                "full_post_closeout_automation_implemented": True,
            },
            "full_post_closeout_automation_implemented must remain false",
        ),
    ],
)
def test_summary_exits_2_on_hostile_attachment_plan(
    tmp_path: Path,
    plan_body: dict,
    expected_substring: str,
) -> None:
    chain_dir = tmp_path / "chain"
    summary_dir = tmp_path / "summary_hostile"
    assert _run_offline_chain(LEGAL_FIXTURE, chain_dir) == 0
    plan_path = tmp_path / "hostile_plan.json"
    plan_path.write_text(json.dumps(plan_body, indent=2) + "\n", encoding="utf-8")
    rc = summary_mod.main(
        [
            "--chain-root",
            str(chain_dir),
            "--attachment-plan",
            str(plan_path),
            "--outdir",
            str(summary_dir),
        ]
    )
    assert rc == 2
    assert not (summary_dir / summary_mod.SUMMARY_JSON_FILENAME).exists()


def test_summary_blocked_operational_path_still_exits_zero_and_non_authorizing(
    tmp_path: Path,
) -> None:
    chain_dir = tmp_path / "chain_partial"
    summary_dir = tmp_path / "summary_operational_blocked"
    assert _run_offline_chain(LEGAL_FIXTURE, chain_dir) == 0
    (chain_dir / REQUIRED_CHAIN_REL_PATHS_V0[0]).unlink()
    plan_path = tmp_path / "valid_blocked_plan.json"
    _write_minimal_valid_attachment_plan(plan_path)
    plan_path.write_text(
        json.dumps(
            {
                **json.loads(plan_path.read_text(encoding="utf-8")),
                "status": STATUS_BLOCKED_MISSING_REQUIRED_CHAIN_ARTIFACT,
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    rc = summary_mod.main(
        [
            "--chain-root",
            str(chain_dir),
            "--attachment-plan",
            str(plan_path),
            "--outdir",
            str(summary_dir),
        ]
    )
    assert rc == 0
    summary = json.loads(
        (summary_dir / summary_mod.SUMMARY_JSON_FILENAME).read_text(encoding="utf-8"),
    )
    assert summary["status"] != STATUS_READY_FOR_CP_HOOK_DRY_RUN
    assert summary["hook_implemented"] is False
    assert summary["machine_lines"]["HOOK_IMPLEMENTED"] == "false"
