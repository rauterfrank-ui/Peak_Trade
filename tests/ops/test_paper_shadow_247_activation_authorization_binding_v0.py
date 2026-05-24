"""Contract tests for scoped activation_authorization_v0 preflight binding v0."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

from scripts.ops.paper_shadow_247_activation_authorization_v0 import (
    build_activation_authorization_v0,
)
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
GOV_FIXTURES = REPO_ROOT / "tests" / "fixtures" / "ops" / "governance_outroot_clearance_v0"
ACT_FIXTURES = REPO_ROOT / "tests" / "fixtures" / "ops" / "activation_authorization_v0"
RUN_ID = "daemon_paper_24h_test_fixture_v0"


def _substitute_gov(text: str, *, outroot: Path, paper_staging: Path, shadow_staging: Path) -> str:
    return (
        text.replace("__RUN_ID__", RUN_ID)
        .replace("__OUTROOT__", str(outroot))
        .replace("__PAPER_STAGING__", str(paper_staging))
        .replace("__SHADOW_STAGING__", str(shadow_staging))
    )


def _substitute_act(text: str) -> str:
    return text.replace("__RUN_ID__", RUN_ID)


def _staging_paths() -> tuple[Path, Path]:
    paper = Path(f"/tmp/peak_trade_{RUN_ID}_paper_staging_fixture")
    shadow = Path(f"/tmp/peak_trade_{RUN_ID}_shadow_staging_fixture")
    paper.mkdir(parents=True, exist_ok=True)
    shadow.mkdir(parents=True, exist_ok=True)
    return paper, shadow


def _write_gov_fixture(
    name: str, dest: Path, *, outroot: Path, paper_staging: Path, shadow_staging: Path
) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(
        _substitute_gov(
            (GOV_FIXTURES / name).read_text(encoding="utf-8"),
            outroot=outroot,
            paper_staging=paper_staging,
            shadow_staging=shadow_staging,
        ),
        encoding="utf-8",
    )


def _materialize_valid_outroot(
    tmp_path: Path,
    *,
    include_governance: bool = True,
    include_activation_preflight: bool = True,
    include_activation_closeout: bool = True,
    run_id_in_record: str | None = None,
    scope_in_record: str | None = None,
    paper_lane: str | None = None,
    shadow_lane: str | None = None,
    scheduler_lane: str | None = None,
    create_staging_dirs: bool = True,
) -> Path:
    outroot = tmp_path / "outroot"
    paper, shadow = _staging_paths()
    if create_staging_dirs:
        paper.mkdir(parents=True, exist_ok=True)
        shadow.mkdir(parents=True, exist_ok=True)

    if include_governance:
        _write_gov_fixture(
            "GOVERNANCE_HOLD_CLEARANCE_OPERATOR_RECORD_V0.md",
            outroot / "preflight" / "GOVERNANCE_HOLD_CLEARANCE_OPERATOR_RECORD_V0.md",
            outroot=outroot,
            paper_staging=paper,
            shadow_staging=shadow,
        )
        _write_gov_fixture(
            "GOVERNANCE_HOLD_CLEARANCE_OPERATOR_RECORD_V0.md",
            outroot / "closeout" / "GOVERNANCE_HOLD_CLEARANCE_OPERATOR_RECORD_ARCHIVE_ONLY_V0.md",
            outroot=outroot,
            paper_staging=paper,
            shadow_staging=shadow,
        )
        _write_gov_fixture(
            "PAPER_STAGING_BINDING_V0.md",
            outroot / "staging" / "PAPER_STAGING_BINDING_V0.md",
            outroot=outroot,
            paper_staging=paper,
            shadow_staging=shadow,
        )
        _write_gov_fixture(
            "SHADOW_STAGING_BINDING_V0.md",
            outroot / "staging" / "SHADOW_STAGING_BINDING_V0.md",
            outroot=outroot,
            paper_staging=paper,
            shadow_staging=shadow,
        )
        _write_gov_fixture(
            "TMP_STAGING_DURABLE_OUTROOT_BRIDGE_MATERIALIZATION_ARCHIVE_ONLY_V0.md",
            outroot
            / "closeout"
            / "TMP_STAGING_DURABLE_OUTROOT_BRIDGE_MATERIALIZATION_ARCHIVE_ONLY_V0.md",
            outroot=outroot,
            paper_staging=paper,
            shadow_staging=shadow,
        )

    act_text = _substitute_act(
        (ACT_FIXTURES / "ACTIVATION_AUTHORIZATION_OPERATOR_RECORD_V0.md").read_text(
            encoding="utf-8"
        )
    )
    if run_id_in_record is not None:
        act_text = act_text.replace(f"RUN_ID={RUN_ID}", f"RUN_ID={run_id_in_record}")
    if scope_in_record is not None:
        act_text = act_text.replace(
            "AUTHORIZATION_SCOPE=bounded_24h_daemon_paper_shadow_dry_run_only",
            f"AUTHORIZATION_SCOPE={scope_in_record}",
        )
    if paper_lane is not None:
        act_text = act_text.replace(
            "PAPER_LANE_ACTIVATION_AUTHORIZED=true_FOR_RUN_ID_ONLY",
            f"PAPER_LANE_ACTIVATION_AUTHORIZED={paper_lane}",
        )
    if shadow_lane is not None:
        act_text = act_text.replace(
            "SHADOW_LANE_ACTIVATION_AUTHORIZED=true_FOR_RUN_ID_ONLY",
            f"SHADOW_LANE_ACTIVATION_AUTHORIZED={shadow_lane}",
        )
    if scheduler_lane is not None:
        act_text = act_text.replace(
            "SCHEDULER_ACTIVATION_AUTHORIZED=true_FOR_RUN_ID_ONLY",
            f"SCHEDULER_ACTIVATION_AUTHORIZED={scheduler_lane}",
        )

    if include_activation_preflight:
        path = outroot / "preflight" / "ACTIVATION_AUTHORIZATION_OPERATOR_RECORD_V0.md"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(act_text, encoding="utf-8")
    if include_activation_closeout:
        path = outroot / "closeout" / "ACTIVATION_AUTHORIZATION_OPERATOR_RECORD_ARCHIVE_ONLY_V0.md"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(act_text, encoding="utf-8")

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
    assert "activation_authorization_v0" not in payload


def test_activation_authorization_valid_with_governance_prerequisite(tmp_path: Path) -> None:
    _materialize_minimal_preflight_repo(tmp_path, include_scheduler_jobs=True)
    outroot = _materialize_valid_outroot(tmp_path)
    payload = build_paper_shadow_247_preflight_status(
        tmp_path,
        durable_run_outroot=outroot,
        expected_run_id=RUN_ID,
    )
    gov = payload["governance_outroot_clearance_v0"]
    act = payload["activation_authorization_v0"]
    assert isinstance(gov, dict) and gov["valid"] is True
    assert isinstance(act, dict) and act["valid"] is True
    assert act["governance_outroot_clearance_valid"] is True
    assert act["paper_lane_activation_authorized"] is True
    assert act["shadow_lane_activation_authorized"] is True
    assert act["scheduler_activation_authorized"] is True
    _assert_conservative_preflight(payload)


def test_activation_authorization_fail_closed_when_governance_invalid(tmp_path: Path) -> None:
    outroot = _materialize_valid_outroot(tmp_path, include_governance=False)
    gov = build_governance_outroot_clearance_v0(outroot, expected_run_id=RUN_ID)
    act = build_activation_authorization_v0(
        outroot,
        expected_run_id=RUN_ID,
        governance_outroot_clearance_v0=gov,
    )
    assert gov["valid"] is False
    assert act["valid"] is False
    assert "governance_outroot_clearance_not_valid" in act["validation_issues"]


def test_activation_authorization_fail_closed_wrong_run_id(tmp_path: Path) -> None:
    outroot = _materialize_valid_outroot(tmp_path)
    gov = build_governance_outroot_clearance_v0(outroot, expected_run_id=RUN_ID)
    act = build_activation_authorization_v0(
        outroot,
        expected_run_id="wrong_run_id",
        governance_outroot_clearance_v0=gov,
    )
    assert act["valid"] is False
    assert any("RUN_ID_mismatch" in issue for issue in act["validation_issues"])


def test_activation_authorization_fail_closed_missing_activation_record(tmp_path: Path) -> None:
    outroot = _materialize_valid_outroot(tmp_path, include_activation_preflight=False)
    gov = build_governance_outroot_clearance_v0(outroot, expected_run_id=RUN_ID)
    act = build_activation_authorization_v0(
        outroot,
        expected_run_id=RUN_ID,
        governance_outroot_clearance_v0=gov,
    )
    assert act["valid"] is False
    assert any("missing_allowlisted_file" in issue for issue in act["validation_issues"])


def test_activation_authorization_fail_closed_missing_activation_closeout(tmp_path: Path) -> None:
    outroot = _materialize_valid_outroot(tmp_path, include_activation_closeout=False)
    gov = build_governance_outroot_clearance_v0(outroot, expected_run_id=RUN_ID)
    act = build_activation_authorization_v0(
        outroot,
        expected_run_id=RUN_ID,
        governance_outroot_clearance_v0=gov,
    )
    assert act["valid"] is False


def test_activation_authorization_fail_closed_wrong_scope(tmp_path: Path) -> None:
    outroot = _materialize_valid_outroot(tmp_path, scope_in_record="wrong_scope")
    gov = build_governance_outroot_clearance_v0(outroot, expected_run_id=RUN_ID)
    act = build_activation_authorization_v0(
        outroot,
        expected_run_id=RUN_ID,
        governance_outroot_clearance_v0=gov,
    )
    assert act["valid"] is False
    assert any("AUTHORIZATION_SCOPE_invalid" in issue for issue in act["validation_issues"])


def test_activation_authorization_fail_closed_missing_paper_lane(tmp_path: Path) -> None:
    outroot = _materialize_valid_outroot(tmp_path, paper_lane="false")
    gov = build_governance_outroot_clearance_v0(outroot, expected_run_id=RUN_ID)
    act = build_activation_authorization_v0(
        outroot,
        expected_run_id=RUN_ID,
        governance_outroot_clearance_v0=gov,
    )
    assert act["valid"] is False
    assert any(
        "PAPER_LANE_ACTIVATION_AUTHORIZED_invalid" in issue for issue in act["validation_issues"]
    )


def test_activation_authorization_fail_closed_missing_shadow_lane(tmp_path: Path) -> None:
    outroot = _materialize_valid_outroot(tmp_path, shadow_lane="false")
    gov = build_governance_outroot_clearance_v0(outroot, expected_run_id=RUN_ID)
    act = build_activation_authorization_v0(
        outroot,
        expected_run_id=RUN_ID,
        governance_outroot_clearance_v0=gov,
    )
    assert act["valid"] is False


def test_activation_authorization_fail_closed_missing_scheduler_authorization(
    tmp_path: Path,
) -> None:
    outroot = _materialize_valid_outroot(tmp_path, scheduler_lane="false")
    gov = build_governance_outroot_clearance_v0(outroot, expected_run_id=RUN_ID)
    act = build_activation_authorization_v0(
        outroot,
        expected_run_id=RUN_ID,
        governance_outroot_clearance_v0=gov,
    )
    assert act["valid"] is False


def test_activation_authorization_fail_closed_arbitrary_directory(tmp_path: Path) -> None:
    arbitrary = tmp_path / "not_an_outroot"
    arbitrary.mkdir()
    act = build_activation_authorization_v0(
        arbitrary,
        expected_run_id=RUN_ID,
        governance_outroot_clearance_v0={"valid": True},
    )
    assert act["valid"] is False


def test_cli_json_propagates_activation_authorization_v0(tmp_path: Path) -> None:
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
    _assert_conservative_preflight(payload)
