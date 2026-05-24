"""Contract tests for scoped governance_outroot_clearance_v0 preflight binding v0."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

from scripts.ops.paper_shadow_247_governance_outroot_clearance_v0 import (
    build_governance_outroot_clearance_v0,
)
from scripts.ops.report_paper_shadow_247_preflight_status import (
    build_paper_shadow_247_preflight_status,
)
from tests.ops.test_report_paper_shadow_247_preflight_status_cli_v0 import (
    _assert_hold_context_v0,
    _materialize_minimal_preflight_repo,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT = REPO_ROOT / "scripts" / "ops" / "report_paper_shadow_247_preflight_status.py"
FIXTURES = REPO_ROOT / "tests" / "fixtures" / "ops" / "governance_outroot_clearance_v0"
RUN_ID = "daemon_paper_24h_test_fixture_v0"


def _substitute(text: str, *, outroot: Path, paper_staging: Path, shadow_staging: Path) -> str:
    return (
        text.replace("__RUN_ID__", RUN_ID)
        .replace("__OUTROOT__", str(outroot))
        .replace("__PAPER_STAGING__", str(paper_staging))
        .replace("__SHADOW_STAGING__", str(shadow_staging))
    )


def _write_fixture(
    name: str, dest: Path, *, outroot: Path, paper_staging: Path, shadow_staging: Path
) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(
        _substitute(
            (FIXTURES / name).read_text(encoding="utf-8"),
            outroot=outroot,
            paper_staging=paper_staging,
            shadow_staging=shadow_staging,
        ),
        encoding="utf-8",
    )


def _staging_paths(tmp_path: Path) -> tuple[Path, Path]:
    paper = Path(f"/tmp/peak_trade_{RUN_ID}_paper_staging_fixture")
    shadow = Path(f"/tmp/peak_trade_{RUN_ID}_shadow_staging_fixture")
    paper.mkdir(parents=True, exist_ok=True)
    shadow.mkdir(parents=True, exist_ok=True)
    return paper, shadow


def _materialize_valid_outroot(
    tmp_path: Path,
    *,
    include_governance_preflight: bool = True,
    include_governance_closeout: bool = True,
    include_paper_binding: bool = True,
    include_shadow_binding: bool = True,
    include_bridge_closeout: bool = True,
    run_id_in_record: str | None = None,
    scope_in_record: str | None = None,
    paper_staging: Path | None = None,
    shadow_staging: Path | None = None,
    create_staging_dirs: bool = True,
) -> tuple[Path, Path, Path]:
    outroot = tmp_path / "outroot"
    if paper_staging is None or shadow_staging is None:
        default_paper, default_shadow = _staging_paths(tmp_path)
        paper = paper_staging if paper_staging is not None else default_paper
        shadow = shadow_staging if shadow_staging is not None else default_shadow
    else:
        paper = paper_staging
        shadow = shadow_staging
    if create_staging_dirs:
        paper.mkdir(parents=True, exist_ok=True)
        shadow.mkdir(parents=True, exist_ok=True)

    gov_name = "GOVERNANCE_HOLD_CLEARANCE_OPERATOR_RECORD_V0.md"
    gov_text = _substitute(
        (FIXTURES / gov_name).read_text(encoding="utf-8"),
        outroot=outroot,
        paper_staging=paper,
        shadow_staging=shadow,
    )
    if run_id_in_record is not None:
        gov_text = gov_text.replace(f"RUN_ID={RUN_ID}", f"RUN_ID={run_id_in_record}")
    if scope_in_record is not None:
        gov_text = gov_text.replace(
            "HOLD_CLEARANCE_SCOPE=bounded_24h_daemon_paper_shadow_dry_run_only",
            f"HOLD_CLEARANCE_SCOPE={scope_in_record}",
        )

    if include_governance_preflight:
        preflight = outroot / "preflight" / gov_name
        preflight.parent.mkdir(parents=True, exist_ok=True)
        preflight.write_text(gov_text, encoding="utf-8")
    if include_governance_closeout:
        closeout = (
            outroot / "closeout" / "GOVERNANCE_HOLD_CLEARANCE_OPERATOR_RECORD_ARCHIVE_ONLY_V0.md"
        )
        closeout.parent.mkdir(parents=True, exist_ok=True)
        closeout.write_text(gov_text, encoding="utf-8")
    if include_paper_binding:
        _write_fixture(
            "PAPER_STAGING_BINDING_V0.md",
            outroot / "staging" / "PAPER_STAGING_BINDING_V0.md",
            outroot=outroot,
            paper_staging=paper,
            shadow_staging=shadow,
        )
    if include_shadow_binding:
        _write_fixture(
            "SHADOW_STAGING_BINDING_V0.md",
            outroot / "staging" / "SHADOW_STAGING_BINDING_V0.md",
            outroot=outroot,
            paper_staging=paper,
            shadow_staging=shadow,
        )
    if include_bridge_closeout:
        _write_fixture(
            "TMP_STAGING_DURABLE_OUTROOT_BRIDGE_MATERIALIZATION_ARCHIVE_ONLY_V0.md",
            outroot
            / "closeout"
            / "TMP_STAGING_DURABLE_OUTROOT_BRIDGE_MATERIALIZATION_ARCHIVE_ONLY_V0.md",
            outroot=outroot,
            paper_staging=paper,
            shadow_staging=shadow,
        )
    return outroot, paper, shadow


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
    assert "governance_outroot_clearance_v0" not in payload


def test_governance_outroot_clearance_valid_for_complete_outroot(tmp_path: Path) -> None:
    _materialize_minimal_preflight_repo(tmp_path, include_scheduler_jobs=True)
    outroot, paper, shadow = _materialize_valid_outroot(tmp_path)
    payload = build_paper_shadow_247_preflight_status(
        tmp_path,
        durable_run_outroot=outroot,
        expected_run_id=RUN_ID,
    )
    ctx = payload["governance_outroot_clearance_v0"]
    assert isinstance(ctx, dict)
    assert ctx["valid"] is True
    assert ctx["non_authorizing"] is True
    assert ctx["permits_scheduler_runtime_paper_testnet_live"] is False
    assert ctx["paper_staging_root"] == str(paper)
    assert ctx["shadow_staging_root"] == str(shadow)
    _assert_conservative_preflight(payload)


def test_governance_outroot_clearance_module_fail_closed_wrong_run_id(tmp_path: Path) -> None:
    outroot, _, _ = _materialize_valid_outroot(tmp_path)
    ctx = build_governance_outroot_clearance_v0(outroot, expected_run_id="wrong_run_id")
    assert ctx["valid"] is False
    assert any("RUN_ID_mismatch" in issue for issue in ctx["validation_issues"])


def test_governance_outroot_clearance_fail_closed_missing_governance_record(tmp_path: Path) -> None:
    _materialize_valid_outroot(tmp_path, include_governance_preflight=False)
    outroot = tmp_path / "outroot"
    ctx = build_governance_outroot_clearance_v0(outroot, expected_run_id=RUN_ID)
    assert ctx["valid"] is False
    assert any("missing_allowlisted_file" in issue for issue in ctx["validation_issues"])


def test_governance_outroot_clearance_fail_closed_wrong_scope(tmp_path: Path) -> None:
    outroot, _, _ = _materialize_valid_outroot(tmp_path, scope_in_record="wrong_scope")
    ctx = build_governance_outroot_clearance_v0(outroot, expected_run_id=RUN_ID)
    assert ctx["valid"] is False
    assert any("HOLD_CLEARANCE_SCOPE_invalid" in issue for issue in ctx["validation_issues"])


def test_governance_outroot_clearance_fail_closed_missing_staging_binding(tmp_path: Path) -> None:
    outroot, _, _ = _materialize_valid_outroot(tmp_path, include_paper_binding=False)
    ctx = build_governance_outroot_clearance_v0(outroot, expected_run_id=RUN_ID)
    assert ctx["valid"] is False
    assert any("paper_staging_binding" in issue for issue in ctx["validation_issues"])


def test_governance_outroot_clearance_fail_closed_missing_bridge_closeout(tmp_path: Path) -> None:
    outroot, _, _ = _materialize_valid_outroot(tmp_path, include_bridge_closeout=False)
    ctx = build_governance_outroot_clearance_v0(outroot, expected_run_id=RUN_ID)
    assert ctx["valid"] is False
    assert any("bridge_closeout" in issue for issue in ctx["validation_issues"])


def test_governance_outroot_clearance_fail_closed_arbitrary_directory(tmp_path: Path) -> None:
    arbitrary = tmp_path / "not_an_outroot"
    arbitrary.mkdir()
    ctx = build_governance_outroot_clearance_v0(arbitrary, expected_run_id=RUN_ID)
    assert ctx["valid"] is False
    assert ctx["validation_issues"]


def test_governance_outroot_clearance_fail_closed_missing_staging_root_on_disk(
    tmp_path: Path,
) -> None:
    missing_paper = Path(f"/tmp/peak_trade_{RUN_ID}_missing_paper_fixture")
    missing_shadow = Path(f"/tmp/peak_trade_{RUN_ID}_missing_shadow_fixture")
    outroot, _, _ = _materialize_valid_outroot(
        tmp_path,
        paper_staging=missing_paper,
        shadow_staging=missing_shadow,
        create_staging_dirs=False,
    )
    ctx = build_governance_outroot_clearance_v0(outroot, expected_run_id=RUN_ID)
    assert ctx["valid"] is False
    assert any("STAGING_ROOT_not_on_disk" in issue for issue in ctx["validation_issues"])


def test_expected_run_id_required_with_durable_run_outroot(tmp_path: Path) -> None:
    _materialize_minimal_preflight_repo(tmp_path, include_scheduler_jobs=True)
    outroot, _, _ = _materialize_valid_outroot(tmp_path)
    with pytest.raises(ValueError, match="expected_run_id is required"):
        build_paper_shadow_247_preflight_status(tmp_path, durable_run_outroot=outroot)


def test_cli_requires_both_durable_run_outroot_and_expected_run_id(tmp_path: Path) -> None:
    proc = subprocess.run(
        [sys.executable, str(SCRIPT), "--json", "--durable-run-outroot", str(tmp_path)],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == 2
    assert "must be supplied together" in proc.stderr


def test_cli_json_propagates_governance_outroot_clearance_v0(tmp_path: Path) -> None:
    outroot, _, _ = _materialize_valid_outroot(tmp_path)
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
    _assert_conservative_preflight(payload)
