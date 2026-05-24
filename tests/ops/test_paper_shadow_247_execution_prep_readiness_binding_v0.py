"""Contract tests for scoped execution_prep_readiness_v0 preflight binding v0."""

from __future__ import annotations

import json
import stat
import subprocess
import sys
from pathlib import Path

from scripts.ops.paper_shadow_247_activation_authorization_v0 import (
    build_activation_authorization_v0,
)
from scripts.ops.paper_shadow_247_execution_prep_readiness_v0 import (
    build_execution_prep_readiness_v0,
)
from scripts.ops.paper_shadow_247_governance_outroot_clearance_v0 import (
    build_governance_outroot_clearance_v0,
)
from scripts.ops.report_paper_shadow_247_preflight_status import (
    build_paper_shadow_247_preflight_status,
)
from tests.ops.test_paper_shadow_247_activation_authorization_binding_v0 import (
    _materialize_valid_outroot as _materialize_activation_outroot,
)
from tests.ops.test_report_paper_shadow_247_preflight_status_cli_v0 import (
    _assert_hold_context_v0,
    _materialize_minimal_preflight_repo,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT = REPO_ROOT / "scripts" / "ops" / "report_paper_shadow_247_preflight_status.py"
EXEC_FIXTURES = REPO_ROOT / "tests" / "fixtures" / "ops" / "execution_prep_readiness_v0"
RUN_ID = "daemon_paper_24h_test_fixture_v0"

NON_EXECUTING_GUARD = """#!/usr/bin/env bash
echo "NON_EXECUTING_ARTIFACT_ONLY"
exit 64
"""

EXECUTING_GUARD = """#!/usr/bin/env bash
echo "EXECUTION_BLOCKED_PRE_START_CHECKS_FAILED"
exit 75
"""


def _substitute_exec(text: str) -> str:
    return text.replace("__RUN_ID__", RUN_ID)


def _write_command_guards(outroot: Path, *, executable: bool = False) -> None:
    commands = outroot / "commands"
    commands.mkdir(parents=True, exist_ok=True)
    for name, body in (
        ("NON_EXECUTING_START_COMMAND_V0.sh", NON_EXECUTING_GUARD),
        ("EXECUTING_START_COMMAND_V0.sh", EXECUTING_GUARD),
    ):
        path = commands / name
        path.write_text(body, encoding="utf-8")
        mode = stat.S_IRUSR | stat.S_IWUSR
        if executable:
            mode |= stat.S_IXUSR
        path.chmod(mode)


def _write_execution_prep_records(
    outroot: Path,
    *,
    include_preflight: bool = True,
    include_closeout: bool = True,
    run_id_in_record: str | None = None,
    scope_in_record: str | None = None,
    authorized: str | None = None,
) -> None:
    text = _substitute_exec(
        (EXEC_FIXTURES / "EXECUTION_PREP_OPERATOR_RECORD_V0.md").read_text(encoding="utf-8")
    )
    if run_id_in_record is not None:
        text = text.replace(f"RUN_ID={RUN_ID}", f"RUN_ID={run_id_in_record}")
    if scope_in_record is not None:
        text = text.replace(
            "EXECUTION_PREP_SCOPE=bounded_24h_daemon_paper_shadow_dry_run_only",
            f"EXECUTION_PREP_SCOPE={scope_in_record}",
        )
    if authorized is not None:
        text = text.replace(
            "EXECUTION_PREP_AUTHORIZED=true_FOR_RUN_ID_ONLY",
            f"EXECUTION_PREP_AUTHORIZED={authorized}",
        )

    if include_preflight:
        path = outroot / "preflight" / "EXECUTION_PREP_OPERATOR_RECORD_V0.md"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
    if include_closeout:
        path = outroot / "closeout" / "EXECUTION_PREP_OPERATOR_RECORD_ARCHIVE_ONLY_V0.md"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")


def _materialize_valid_outroot(
    tmp_path: Path,
    *,
    include_execution_prep_preflight: bool = True,
    include_execution_prep_closeout: bool = True,
    include_command_guards: bool = True,
    command_guards_executable: bool = False,
    run_id_in_record: str | None = None,
    scope_in_record: str | None = None,
    authorized: str | None = None,
    **activation_kwargs: object,
) -> Path:
    outroot = _materialize_activation_outroot(tmp_path, **activation_kwargs)
    _write_execution_prep_records(
        outroot,
        include_preflight=include_execution_prep_preflight,
        include_closeout=include_execution_prep_closeout,
        run_id_in_record=run_id_in_record,
        scope_in_record=scope_in_record,
        authorized=authorized,
    )
    if include_command_guards:
        _write_command_guards(outroot, executable=command_guards_executable)
    return outroot


def _assert_conservative_preflight(payload: dict[str, object]) -> None:
    assert payload["status"] == "BLOCKED"
    assert payload["activation_authorized"] is False
    assert payload["scheduler_execution_authorized"] is False
    assert payload["paper_runtime_authorized"] is False
    assert payload["shadow_runtime_authorized"] is False
    dry = payload["dry_activation_readiness"]
    assert isinstance(dry, dict)
    assert dry["ready"] is False
    _assert_hold_context_v0(payload)


def test_default_preflight_unchanged_without_durable_run_outroot(tmp_path: Path) -> None:
    _materialize_minimal_preflight_repo(tmp_path, include_scheduler_jobs=True)
    payload = build_paper_shadow_247_preflight_status(tmp_path)
    _assert_conservative_preflight(payload)
    assert "execution_prep_readiness_v0" not in payload


def test_execution_prep_readiness_valid_with_prerequisites(tmp_path: Path) -> None:
    _materialize_minimal_preflight_repo(tmp_path, include_scheduler_jobs=True)
    outroot = _materialize_valid_outroot(tmp_path)
    payload = build_paper_shadow_247_preflight_status(
        tmp_path,
        durable_run_outroot=outroot,
        expected_run_id=RUN_ID,
    )
    gov = payload["governance_outroot_clearance_v0"]
    act = payload["activation_authorization_v0"]
    prep = payload["execution_prep_readiness_v0"]
    assert isinstance(gov, dict) and gov["valid"] is True
    assert isinstance(act, dict) and act["valid"] is True
    assert isinstance(prep, dict) and prep["valid"] is True
    assert prep["governance_outroot_clearance_valid"] is True
    assert prep["activation_authorization_valid"] is True
    assert prep["execution_prep_authorized"] is True
    assert prep["execution_prep_scope"] == "bounded_24h_daemon_paper_shadow_dry_run_only"
    assert prep["execution_prep_allowed_next_step"] == "reporter_binding_pr_only"
    assert prep["command_guards_preserved"] is True
    assert prep["no_active_run_snapshot_valid"] is True
    _assert_conservative_preflight(payload)


def test_execution_prep_readiness_fail_closed_when_governance_invalid(tmp_path: Path) -> None:
    outroot = _materialize_valid_outroot(tmp_path, include_governance=False)
    gov = build_governance_outroot_clearance_v0(outroot, expected_run_id=RUN_ID)
    act = build_activation_authorization_v0(
        outroot,
        expected_run_id=RUN_ID,
        governance_outroot_clearance_v0=gov,
    )
    prep = build_execution_prep_readiness_v0(
        outroot,
        expected_run_id=RUN_ID,
        governance_outroot_clearance_v0=gov,
        activation_authorization_v0=act,
    )
    assert gov["valid"] is False
    assert prep["valid"] is False
    assert "governance_outroot_clearance_not_valid" in prep["validation_issues"]


def test_execution_prep_readiness_fail_closed_when_activation_invalid(tmp_path: Path) -> None:
    outroot = _materialize_valid_outroot(
        tmp_path,
        include_activation_preflight=False,
    )
    gov = build_governance_outroot_clearance_v0(outroot, expected_run_id=RUN_ID)
    act = build_activation_authorization_v0(
        outroot,
        expected_run_id=RUN_ID,
        governance_outroot_clearance_v0=gov,
    )
    prep = build_execution_prep_readiness_v0(
        outroot,
        expected_run_id=RUN_ID,
        governance_outroot_clearance_v0=gov,
        activation_authorization_v0=act,
    )
    assert act["valid"] is False
    assert prep["valid"] is False
    assert "activation_authorization_not_valid" in prep["validation_issues"]


def test_execution_prep_readiness_fail_closed_wrong_run_id(tmp_path: Path) -> None:
    outroot = _materialize_valid_outroot(tmp_path)
    gov = build_governance_outroot_clearance_v0(outroot, expected_run_id=RUN_ID)
    act = build_activation_authorization_v0(
        outroot,
        expected_run_id=RUN_ID,
        governance_outroot_clearance_v0=gov,
    )
    prep = build_execution_prep_readiness_v0(
        outroot,
        expected_run_id="wrong_run_id",
        governance_outroot_clearance_v0=gov,
        activation_authorization_v0=act,
    )
    assert prep["valid"] is False
    assert any("RUN_ID_mismatch" in issue for issue in prep["validation_issues"])


def test_execution_prep_readiness_fail_closed_missing_preflight_record(tmp_path: Path) -> None:
    outroot = _materialize_valid_outroot(tmp_path, include_execution_prep_preflight=False)
    gov = build_governance_outroot_clearance_v0(outroot, expected_run_id=RUN_ID)
    act = build_activation_authorization_v0(
        outroot,
        expected_run_id=RUN_ID,
        governance_outroot_clearance_v0=gov,
    )
    prep = build_execution_prep_readiness_v0(
        outroot,
        expected_run_id=RUN_ID,
        governance_outroot_clearance_v0=gov,
        activation_authorization_v0=act,
    )
    assert prep["valid"] is False
    assert any("missing_allowlisted_file" in issue for issue in prep["validation_issues"])


def test_execution_prep_readiness_fail_closed_missing_closeout_record(tmp_path: Path) -> None:
    outroot = _materialize_valid_outroot(tmp_path, include_execution_prep_closeout=False)
    gov = build_governance_outroot_clearance_v0(outroot, expected_run_id=RUN_ID)
    act = build_activation_authorization_v0(
        outroot,
        expected_run_id=RUN_ID,
        governance_outroot_clearance_v0=gov,
    )
    prep = build_execution_prep_readiness_v0(
        outroot,
        expected_run_id=RUN_ID,
        governance_outroot_clearance_v0=gov,
        activation_authorization_v0=act,
    )
    assert prep["valid"] is False


def test_execution_prep_readiness_fail_closed_wrong_scope(tmp_path: Path) -> None:
    outroot = _materialize_valid_outroot(tmp_path, scope_in_record="wrong_scope")
    gov = build_governance_outroot_clearance_v0(outroot, expected_run_id=RUN_ID)
    act = build_activation_authorization_v0(
        outroot,
        expected_run_id=RUN_ID,
        governance_outroot_clearance_v0=gov,
    )
    prep = build_execution_prep_readiness_v0(
        outroot,
        expected_run_id=RUN_ID,
        governance_outroot_clearance_v0=gov,
        activation_authorization_v0=act,
    )
    assert prep["valid"] is False
    assert any("EXECUTION_PREP_SCOPE_invalid" in issue for issue in prep["validation_issues"])


def test_execution_prep_readiness_fail_closed_missing_authorization(tmp_path: Path) -> None:
    outroot = _materialize_valid_outroot(tmp_path, authorized="false")
    gov = build_governance_outroot_clearance_v0(outroot, expected_run_id=RUN_ID)
    act = build_activation_authorization_v0(
        outroot,
        expected_run_id=RUN_ID,
        governance_outroot_clearance_v0=gov,
    )
    prep = build_execution_prep_readiness_v0(
        outroot,
        expected_run_id=RUN_ID,
        governance_outroot_clearance_v0=gov,
        activation_authorization_v0=act,
    )
    assert prep["valid"] is False
    assert any("EXECUTION_PREP_AUTHORIZED_invalid" in issue for issue in prep["validation_issues"])


def test_execution_prep_readiness_fail_closed_missing_command_guards(tmp_path: Path) -> None:
    outroot = _materialize_valid_outroot(tmp_path, include_command_guards=False)
    gov = build_governance_outroot_clearance_v0(outroot, expected_run_id=RUN_ID)
    act = build_activation_authorization_v0(
        outroot,
        expected_run_id=RUN_ID,
        governance_outroot_clearance_v0=gov,
    )
    prep = build_execution_prep_readiness_v0(
        outroot,
        expected_run_id=RUN_ID,
        governance_outroot_clearance_v0=gov,
        activation_authorization_v0=act,
    )
    assert prep["valid"] is False
    assert any("command_guard:missing" in issue for issue in prep["validation_issues"])


def test_execution_prep_readiness_fail_closed_executable_command_guards(tmp_path: Path) -> None:
    outroot = _materialize_valid_outroot(tmp_path, command_guards_executable=True)
    gov = build_governance_outroot_clearance_v0(outroot, expected_run_id=RUN_ID)
    act = build_activation_authorization_v0(
        outroot,
        expected_run_id=RUN_ID,
        governance_outroot_clearance_v0=gov,
    )
    prep = build_execution_prep_readiness_v0(
        outroot,
        expected_run_id=RUN_ID,
        governance_outroot_clearance_v0=gov,
        activation_authorization_v0=act,
    )
    assert prep["valid"] is False
    assert any("command_guard:executable" in issue for issue in prep["validation_issues"])


def test_execution_prep_readiness_fail_closed_arbitrary_directory(tmp_path: Path) -> None:
    arbitrary = tmp_path / "not_an_outroot"
    arbitrary.mkdir()
    prep = build_execution_prep_readiness_v0(
        arbitrary,
        expected_run_id=RUN_ID,
        governance_outroot_clearance_v0={"valid": True},
        activation_authorization_v0={"valid": True},
    )
    assert prep["valid"] is False


def test_cli_json_propagates_execution_prep_readiness_v0(tmp_path: Path) -> None:
    outroot = _materialize_valid_outroot(tmp_path)
    proc = subprocess.run(
        [
            sys.executable,
            str(SCRIPT),
            "--json",
            "--repo-root",
            str(REPO_ROOT),
            "--durable-run-outroot",
            str(outroot),
            "--expected-run-id",
            RUN_ID,
        ],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == 0, proc.stderr
    payload = json.loads(proc.stdout)
    assert payload["governance_outroot_clearance_v0"]["valid"] is True
    assert payload["activation_authorization_v0"]["valid"] is True
    assert payload["execution_prep_readiness_v0"]["valid"] is True
    _assert_conservative_preflight(payload)
