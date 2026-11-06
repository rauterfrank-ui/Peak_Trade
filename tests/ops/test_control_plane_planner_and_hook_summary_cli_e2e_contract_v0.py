"""Control Plane chain → planner CLI → hook summary CLI E2E contract v0 (tests-only).

Proves: LEGAL_FIXTURE → offline chain CLI → durable attachment planner CLI → hook dry-run
summary CLI, with fail-closed blocked paths. Does not invoke runtime, network, copy, verify,
retention, closeout, projection, or Notion.
"""

from __future__ import annotations

import ast
import json
from pathlib import Path

import pytest

from scripts.ops import plan_control_plane_offline_chain_durable_attachment_v0 as planner_mod
from scripts.ops import run_autonomous_ops_control_plane_offline_chain_v0 as chain_mod
from scripts.ops import summarize_control_plane_automation_hook_dry_run_v0 as summary_mod
from scripts.ops import bridge_control_plane_plan_to_post_closeout_readiness_v0 as bridge_mod
from tests.ops.test_control_plane_first_automation_hook_dry_run_contract_v0 import (
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
from tests.ops.test_plan_control_plane_offline_chain_durable_attachment_contract_v0 import (
    NON_AUTHORITY_JSON_KEYS,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
THIS_MODULE = Path(__file__)

E2E_OWNER_REFERENCES_V0: tuple[str, ...] = (
    "scripts/ops/run_autonomous_ops_control_plane_offline_chain_v0.py",
    "scripts/ops/plan_control_plane_offline_chain_durable_attachment_v0.py",
    "scripts/ops/summarize_control_plane_automation_hook_dry_run_v0.py",
    "tests/ops/test_control_plane_first_automation_hook_dry_run_contract_v0.py",
    "tests/ops/test_plan_control_plane_offline_chain_durable_attachment_contract_v0.py",
    "tests/ops/test_control_plane_planner_and_hook_e2e_cli_contract_v0.py",
    "tests/ops/test_summarize_control_plane_automation_hook_dry_run_contract_v0.py",
    "tests/ops/test_control_plane_offline_chain_durable_evidence_attachment_contracts_v0.py",
)

# Planner/summary CLI stubs emit *_STARTED/*_INVOKED keys (not *_REQUIRED from transition fixtures).
E2E_SAFETY_MACHINE_LINE_ASSERTIONS: tuple[str, ...] = (
    "HOOK_IMPLEMENTED=false",
    "FULL_POST_CLOSEOUT_AUTOMATION_IMPLEMENTED=false",
    "RUNTIME_STARTED=false",
    "SCHEDULER_STARTED=false",
    "SUPERVISOR_STARTED=false",
    "DAEMON_STARTED=false",
    "PAPER_SHADOW_TESTNET_LIVE_STARTED=false",
    "AWS_REMOTE_TOUCHED=false",
    "S3_UPLOAD_REQUIRED=false",
    "SSH_REQUIRED=false",
    "NETWORK_REQUIRED=false",
    "CLOSEOUT_INVOKED=false",
    "PROJECTION_INVOKED=false",
    "NOTION_SYNC_INVOKED=false",
    "MASTER_V2_DOUBLE_PLAY_TOUCHED=false",
    "LIVE_AUTHORITY_CHANGED=false",
    "DURABLE_COPY_INVOKED=false",
    "PRIMARY_EVIDENCE_RETENTION_INVOKED=false",
    "MANIFEST_WRITE_INVOKED=false",
    "COPY_VERIFY_INVOKED=false",
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


def _assert_planner_artifacts_exist(outdir: Path) -> None:
    assert (outdir / planner_mod.PLAN_JSON_FILENAME).is_file()
    assert (outdir / planner_mod.PLAN_MACHINE_LINES_FILENAME).is_file()
    assert (outdir / planner_mod.PLAN_MD_FILENAME).is_file()


def _assert_summary_artifacts_exist(outdir: Path) -> None:
    assert (outdir / summary_mod.SUMMARY_JSON_FILENAME).is_file()
    assert (outdir / summary_mod.SUMMARY_MACHINE_LINES_FILENAME).is_file()
    assert (outdir / summary_mod.SUMMARY_MD_FILENAME).is_file()


def _assert_non_authority_plan_json(plan: dict) -> None:
    assert plan["pointer_only"] is True
    for key in NON_AUTHORITY_JSON_KEYS:
        if key == "pointer_only":
            continue
        assert plan[key] is False, f"expected {key}=false, got {plan[key]!r}"


def _assert_safety_machine_lines(
    *,
    plan: dict,
    summary: dict,
    planner_ml_text: str,
    summary_ml_text: str,
) -> None:
    merged = {**plan["machine_lines"], **summary["machine_lines"]}
    for assertion in E2E_SAFETY_MACHINE_LINE_ASSERTIONS:
        key, _, value = assertion.partition("=")
        assert merged[key] == value, f"expected {assertion}"
        assert assertion in planner_ml_text or assertion in summary_ml_text, (
            f"expected {assertion!r} in planner or summary machine-lines file"
        )
    assert summary["machine_lines"]["HOOK_DRY_RUN_ONLY"] == "true"
    assert "HOOK_DRY_RUN_ONLY=true" in summary_ml_text
    assert "CONTROL_PLANE_DURABLE_ATTACHMENT_PLANNER_CLI_STUB_V0=true" in planner_ml_text
    assert "CONTROL_PLANE_HOOK_DRY_RUN_SUMMARY_CLI_STUB_V0=true" in summary_ml_text


def _assert_parity_with_contract_helper(
    summary: dict,
    *,
    chain_root: Path,
    plan: dict,
) -> None:
    inp = summary_mod.hook_inputs_from_attachment_plan(chain_root=chain_root, plan=plan)
    expected_status, _, expected_blockers = contract_build_summary(inp)
    assert summary["status"] == expected_status
    assert summary["blockers"] == expected_blockers


def _assert_no_side_effect_artifacts(root: Path) -> None:
    assert not list(root.rglob("MANIFEST.sha256"))


def test_ready_e2e_chain_planner_summary_cli_v0(tmp_path: Path) -> None:
    chain_dir = tmp_path / "chain"
    planner_dir = tmp_path / "planner"
    summary_dir = tmp_path / "summary"
    assert _run_offline_chain(LEGAL_FIXTURE, chain_dir) == 0

    plan = _run_planner(chain_dir, SYNTHETIC_DURABLE_ARCHIVE_ROOT, planner_dir)
    _assert_planner_artifacts_exist(planner_dir)
    assert plan["status"] == STATUS_READY_FOR_DURABLE_ATTACHMENT_PLANNING
    _assert_non_authority_plan_json(plan)

    plan_path = planner_dir / planner_mod.PLAN_JSON_FILENAME
    summary = _run_summary(chain_dir, plan_path, summary_dir)
    _assert_summary_artifacts_exist(summary_dir)

    assert summary["status"] == summary_mod.STATUS_READY_FOR_CP_HOOK_DRY_RUN
    assert summary["attachment_plan_status"] == STATUS_READY_FOR_DURABLE_ATTACHMENT_PLANNING
    assert summary["hook_implemented"] is False
    assert summary["full_post_closeout_automation_implemented"] is False
    assert summary["blockers"] == []

    planner_ml = (planner_dir / planner_mod.PLAN_MACHINE_LINES_FILENAME).read_text(
        encoding="utf-8",
    )
    summary_ml = (summary_dir / summary_mod.SUMMARY_MACHINE_LINES_FILENAME).read_text(
        encoding="utf-8",
    )
    _assert_safety_machine_lines(
        plan=plan,
        summary=summary,
        planner_ml_text=planner_ml,
        summary_ml_text=summary_ml,
    )
    _assert_parity_with_contract_helper(summary, chain_root=chain_dir, plan=plan)
    _assert_no_side_effect_artifacts(tmp_path)


def test_blocked_missing_chain_artifact_planner_and_summary_not_ready_v0(
    tmp_path: Path,
) -> None:
    chain_dir = tmp_path / "chain_partial"
    planner_dir = tmp_path / "planner_blocked"
    summary_dir = tmp_path / "summary_blocked"
    assert _run_offline_chain(LEGAL_FIXTURE, chain_dir) == 0
    removed_rel = REQUIRED_CHAIN_REL_PATHS_V0[0]
    (chain_dir / removed_rel).unlink()

    plan = _run_planner(chain_dir, SYNTHETIC_DURABLE_ARCHIVE_ROOT, planner_dir)
    _assert_planner_artifacts_exist(planner_dir)
    assert plan["status"] == STATUS_BLOCKED_MISSING_REQUIRED_CHAIN_ARTIFACT
    assert removed_rel in plan["missing_chain_rel_paths"]

    plan_path = planner_dir / planner_mod.PLAN_JSON_FILENAME
    summary = _run_summary(chain_dir, plan_path, summary_dir)
    _assert_summary_artifacts_exist(summary_dir)
    assert summary["status"] != summary_mod.STATUS_READY_FOR_CP_HOOK_DRY_RUN
    assert summary["attachment_plan_status"] == STATUS_BLOCKED_MISSING_REQUIRED_CHAIN_ARTIFACT
    assert summary["blockers"]

    _assert_safety_machine_lines(
        plan=plan,
        summary=summary,
        planner_ml_text=(planner_dir / planner_mod.PLAN_MACHINE_LINES_FILENAME).read_text(
            encoding="utf-8",
        ),
        summary_ml_text=(summary_dir / summary_mod.SUMMARY_MACHINE_LINES_FILENAME).read_text(
            encoding="utf-8",
        ),
    )
    _assert_parity_with_contract_helper(summary, chain_root=chain_dir, plan=plan)
    _assert_no_side_effect_artifacts(tmp_path)


def test_blocked_tmp_target_archive_planner_and_summary_not_ready_v0(tmp_path: Path) -> None:
    chain_dir = tmp_path / "chain"
    planner_dir = tmp_path / "planner_tmp"
    summary_dir = tmp_path / "summary_tmp"
    assert _run_offline_chain(LEGAL_FIXTURE, chain_dir) == 0
    tmp_archive = Path(
        "/tmp/control_plane_planner_hook_summary_cli_e2e_contract_v0",
    )

    plan = _run_planner(chain_dir, tmp_archive, planner_dir)
    _assert_planner_artifacts_exist(planner_dir)
    assert plan["status"] == STATUS_BLOCKED_TARGET_ARCHIVE_ROOT_UNDER_TMP

    plan_path = planner_dir / planner_mod.PLAN_JSON_FILENAME
    summary = _run_summary(chain_dir, plan_path, summary_dir)
    _assert_summary_artifacts_exist(summary_dir)
    assert summary["status"] != summary_mod.STATUS_READY_FOR_CP_HOOK_DRY_RUN
    assert summary["attachment_plan_status"] == STATUS_BLOCKED_TARGET_ARCHIVE_ROOT_UNDER_TMP
    assert summary["blockers"]

    _assert_safety_machine_lines(
        plan=plan,
        summary=summary,
        planner_ml_text=(planner_dir / planner_mod.PLAN_MACHINE_LINES_FILENAME).read_text(
            encoding="utf-8",
        ),
        summary_ml_text=(summary_dir / summary_mod.SUMMARY_MACHINE_LINES_FILENAME).read_text(
            encoding="utf-8",
        ),
    )
    _assert_parity_with_contract_helper(summary, chain_root=chain_dir, plan=plan)
    _assert_no_side_effect_artifacts(tmp_path)


@pytest.mark.parametrize("owner_rel", E2E_OWNER_REFERENCES_V0)
def test_e2e_owner_references_exist_v0(owner_rel: str) -> None:
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


def test_summary_cli_forbidden_flags_match_planner_posture_v0() -> None:
    assert summary_mod.FORBIDDEN_CLI_FLAGS == planner_mod.FORBIDDEN_CLI_FLAGS


def test_bridge_exits_2_on_malformed_plan_json(tmp_path: Path) -> None:
    plan_path = tmp_path / "malformed_plan.json"
    plan_path.write_text("{not-json\n", encoding="utf-8")
    readiness_dir = tmp_path / "readiness"
    rc = bridge_mod.main(["--plan", str(plan_path), "--outdir", str(readiness_dir)])
    assert rc == 2
    assert not (readiness_dir / bridge_mod.READINESS_JSON_FILENAME).exists()


def test_chain_orchestrator_exits_2_on_malformed_fixture_json(tmp_path: Path) -> None:
    fixture_path = tmp_path / "malformed_fixture.json"
    fixture_path.write_text("{not-json\n", encoding="utf-8")
    chain_dir = tmp_path / "chain_malformed"
    rc = chain_mod.main(["--fixture", str(fixture_path), "--outdir", str(chain_dir)])
    assert rc == 2
    assert not (chain_dir / chain_mod.CHAIN_JSON_FILENAME).exists()


def test_e2e_summary_exits_2_on_tampered_attachment_plan_without_side_effects(
    tmp_path: Path,
) -> None:
    chain_dir = tmp_path / "chain"
    planner_dir = tmp_path / "planner"
    summary_dir = tmp_path / "summary_tampered"
    assert _run_offline_chain(LEGAL_FIXTURE, chain_dir) == 0
    plan = _run_planner(chain_dir, SYNTHETIC_DURABLE_ARCHIVE_ROOT, planner_dir)
    plan_path = planner_dir / planner_mod.PLAN_JSON_FILENAME
    tampered = {**plan, "hook_implemented": True}
    plan_path.write_text(json.dumps(tampered, indent=2) + "\n", encoding="utf-8")
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
    _assert_no_side_effect_artifacts(tmp_path)
