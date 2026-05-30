"""Control Plane plan generator CLI → bridge CLI → post-closeout readiness E2E v0.

Proves: transition fixture → plan generator CLI → bridge CLI → readiness artifacts,
with fail-closed blocked and malformed-plan paths. Visibility-only; does not invoke
runtime, network, closeout, copy, verify, retention, projection, Notion, or hooks.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from scripts.ops import bridge_control_plane_plan_to_post_closeout_readiness_v0 as bridge_mod
from scripts.ops import build_autonomous_ops_control_plane_plan_v0 as plan_mod
from tests.ops.test_control_plane_plan_output_closeout_projection_bridge_contract_v0 import (
    FORBIDDEN_FIXTURE,
    LEGAL_FIXTURE,
    REQUIRED_MACHINE_LINE_ASSERTIONS,
    _make_plan,
    _run_bridge,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
THIS_MODULE = Path(__file__)

E2E_OWNER_REFERENCES_V0: tuple[str, ...] = (
    "scripts/ops/build_autonomous_ops_control_plane_plan_v0.py",
    "scripts/ops/bridge_control_plane_plan_to_post_closeout_readiness_v0.py",
    "tests/ops/test_control_plane_plan_output_closeout_projection_bridge_contract_v0.py",
    "tests/ops/test_control_plane_post_closeout_automation_readiness_contracts_v0.py",
    "tests/ops/test_control_plane_plan_bridge_readiness_cli_e2e_contract_v0.py",
)

_FORBIDDEN_SIDE_EFFECT_NAMES: tuple[str, ...] = (
    "MANIFEST.sha256",
    "MANIFEST_VERIFY.log",
    "FINAL_MACHINE_LINES.txt",
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


def _assert_readiness_artifacts_exist(readiness_dir: Path) -> None:
    assert (readiness_dir / bridge_mod.READINESS_JSON_FILENAME).is_file()
    assert (readiness_dir / bridge_mod.READINESS_MACHINE_LINES_FILENAME).is_file()
    assert (readiness_dir / bridge_mod.READINESS_MD_FILENAME).is_file()


def _assert_no_side_effect_artifacts(root: Path) -> None:
    for name in _FORBIDDEN_SIDE_EFFECT_NAMES:
        assert not list(root.rglob(name)), f"unexpected side-effect artifact: {name}"


def _assert_non_authorizing_readiness(readiness: dict) -> None:
    assert readiness["planning_only"] is True
    assert readiness["closeout_invoke_authorized"] is False
    assert readiness["projection_invoke_authorized"] is False
    assert readiness["notion_sync_authorized"] is False
    assert readiness["durable_copy_authorized"] is False
    assert readiness["primary_evidence_retention_invoke_authorized"] is False


def test_ready_e2e_plan_generator_cli_to_bridge_readiness_cli_v0(tmp_path: Path) -> None:
    plan_dir = tmp_path / "plan"
    readiness_dir = tmp_path / "readiness"
    plan_dir.mkdir()
    readiness_dir.mkdir()

    assert plan_mod.main(["--fixture", str(LEGAL_FIXTURE), "--outdir", str(plan_dir)]) == 0
    plan_json = plan_dir / plan_mod.PLAN_JSON_FILENAME
    assert plan_json.is_file()

    assert _run_bridge(plan_json, readiness_dir) == 0
    _assert_readiness_artifacts_exist(readiness_dir)

    readiness = json.loads(
        (readiness_dir / bridge_mod.READINESS_JSON_FILENAME).read_text(encoding="utf-8"),
    )
    assert readiness["schema_version"] == bridge_mod.SCHEMA_VERSION
    assert readiness["control_plane_plan_status"] == "plan_only"
    assert (
        readiness["machine_lines"]["CONTROL_PLANE_POST_CLOSEOUT_READINESS_STATUS"]
        == "ready_for_projection_planning"
    )
    assert readiness["readiness"]["can_prepare_post_closeout_projection_payload"] is True
    _assert_non_authorizing_readiness(readiness)

    machine_lines_text = (readiness_dir / bridge_mod.READINESS_MACHINE_LINES_FILENAME).read_text(
        encoding="utf-8"
    )
    for assertion in REQUIRED_MACHINE_LINE_ASSERTIONS:
        assert assertion in machine_lines_text

    md_text = (readiness_dir / bridge_mod.READINESS_MD_FILENAME).read_text(encoding="utf-8")
    assert "planning" in md_text.lower() or "readiness" in md_text.lower()

    _assert_no_side_effect_artifacts(tmp_path)


def test_blocked_forbidden_fixture_bridge_readiness_remains_non_authorizing_v0(
    tmp_path: Path,
) -> None:
    readiness_dir = tmp_path / "readiness_blocked"
    readiness_dir.mkdir()
    plan_json = _make_plan(tmp_path, FORBIDDEN_FIXTURE)

    assert _run_bridge(plan_json, readiness_dir) == 0
    _assert_readiness_artifacts_exist(readiness_dir)

    readiness = json.loads(
        (readiness_dir / bridge_mod.READINESS_JSON_FILENAME).read_text(encoding="utf-8"),
    )
    assert readiness["control_plane_plan_status"] == "blocked"
    assert readiness["machine_lines"]["CONTROL_PLANE_POST_CLOSEOUT_READINESS_STATUS"] == "blocked"
    assert readiness["readiness"]["can_prepare_post_closeout_projection_payload"] is False
    _assert_non_authorizing_readiness(readiness)

    machine_lines_text = (readiness_dir / bridge_mod.READINESS_MACHINE_LINES_FILENAME).read_text(
        encoding="utf-8"
    )
    assert "CLOSEOUT_INVOKE_AUTHORIZED=false" in machine_lines_text
    assert "PROJECTION_INVOKE_AUTHORIZED=false" in machine_lines_text

    _assert_no_side_effect_artifacts(tmp_path)


def test_bridge_exits_2_on_malformed_plan_json_without_readiness_v0(tmp_path: Path) -> None:
    plan_path = tmp_path / "malformed_plan.json"
    plan_path.write_text("{not-json\n", encoding="utf-8")
    readiness_dir = tmp_path / "readiness_malformed"
    readiness_dir.mkdir()

    rc = bridge_mod.main(["--plan", str(plan_path), "--outdir", str(readiness_dir)])
    assert rc == 2
    assert not (readiness_dir / bridge_mod.READINESS_JSON_FILENAME).exists()
    assert not (readiness_dir / bridge_mod.READINESS_MACHINE_LINES_FILENAME).exists()
    assert not (readiness_dir / bridge_mod.READINESS_MD_FILENAME).exists()
    _assert_no_side_effect_artifacts(tmp_path)


@pytest.mark.parametrize("owner_rel", E2E_OWNER_REFERENCES_V0)
def test_e2e_owner_references_exist_v0(owner_rel: str) -> None:
    assert (REPO_ROOT / owner_rel).is_file(), f"missing E2E owner reference: {owner_rel}"


def test_e2e_module_documents_plan_bridge_readiness_path_v0() -> None:
    text = _this_module_source()
    assert "plan generator CLI" in text
    assert "bridge CLI" in text
    assert "post-closeout readiness" in text
    assert "plan→bridge→readiness" in text or "plan generator CLI → bridge CLI" in text


def test_e2e_module_has_no_forbidden_runtime_or_invoke_patterns_v0() -> None:
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
                f"forbidden pattern in E2E contract test source: {pattern!r} line={line!r}"
            )
