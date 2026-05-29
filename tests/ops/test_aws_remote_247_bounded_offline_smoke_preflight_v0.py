"""Offline bounded AWS Remote 247 smoke preflight (fixture CLI; no network/AWS/SSH)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from scripts.ops import aws_remote_247_bounded_offline_smoke_preflight_v0 as smoke_mod
from scripts.ops.aws_remote_247_bounded_offline_smoke_preflight_v0 import DirectPacketInput

REPO_ROOT = Path(__file__).resolve().parents[2]
FIXTURE = (
    REPO_ROOT
    / "tests"
    / "fixtures"
    / "ops"
    / "aws_remote_247_bounded_offline_smoke_fixture_v0.json"
)
SCRIPT = REPO_ROOT / "scripts" / "ops" / "aws_remote_247_bounded_offline_smoke_preflight_v0.py"
BUNDLE_TEST = REPO_ROOT / "tests" / "ops" / "test_remote_s3_preflight_contract_bundle_v0.py"
FORBIDDEN_PARALLEL_SCRIPT = REPO_ROOT / "scripts/ops/post_closeout_chain_execute_v0.py"
REQUIRED_SCOPE = smoke_mod.REQUIRED_APPROVED_SCOPE

FORBIDDEN_IMPORTS = (
    "boto3",
    "paramiko",
    "requests",
    "urllib",
    "socket",
)

DURABLE_OUT_ROOT = (
    REPO_ROOT / "tests" / ".pytest_archive_roots" / "aws_remote_247_smoke_preflight_runs"
)


def _require_durable_archive_root_test(path: Path) -> tuple[bool, str]:
    if not path.exists():
        return False, f"archive root missing: {path}"
    return True, ""


def _patch_not_tmp(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(smoke_mod, "is_under_tmp", lambda _path: False)
    import scripts.ops.preflight_s3_finalized_evidence_export_v0 as s3_mod
    import scripts.ops.primary_evidence_retention_v0 as retention_mod

    monkeypatch.setattr(s3_mod, "is_under_tmp", lambda _path: False)
    monkeypatch.setattr(retention_mod, "is_under_tmp", lambda _path: False)
    monkeypatch.setattr(s3_mod, "require_durable_archive_root", _require_durable_archive_root_test)
    monkeypatch.setattr(
        retention_mod, "require_durable_archive_root", _require_durable_archive_root_test
    )


@pytest.fixture
def durable_out_dir(tmp_path: Path) -> Path:
    """Durable output outside /tmp for Linux CI (pytest tmp_path lives under /tmp)."""
    out = DURABLE_OUT_ROOT / tmp_path.name
    out.mkdir(parents=True, exist_ok=True)
    return out


def _parse_machine_lines(text: str) -> dict[str, str]:
    out: dict[str, str] = {}
    for raw in text.splitlines():
        line = raw.strip()
        if "=" in line:
            key, _, value = line.partition("=")
            out[key.strip()] = value.strip()
    return out


def test_script_source_has_no_forbidden_network_imports() -> None:
    source = SCRIPT.read_text(encoding="utf-8")
    for name in FORBIDDEN_IMPORTS:
        assert f"import {name}" not in source
        assert f"from {name}" not in source


def test_no_parallel_daemon_runner_or_runbook_surfaces() -> None:
    assert not FORBIDDEN_PARALLEL_SCRIPT.exists()
    ops_scripts = REPO_ROOT / "scripts" / "ops"
    runbooks = REPO_ROOT / "docs" / "ops" / "runbooks"
    assert list(ops_scripts.glob("aws_remote_247_daemon*.py")) == []
    assert list(runbooks.glob("AWS_REMOTE_247_DAEMON*.md")) == []


def test_happy_path_all_gates_true_and_safety_lines_false(
    durable_out_dir: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _patch_not_tmp(monkeypatch)
    out = durable_out_dir
    gates, report = smoke_mod.run_bounded_offline_smoke_preflight(
        fixture_path=FIXTURE,
        durable_output_dir=out,
        approved_scope_name=REQUIRED_SCOPE,
        offline=True,
        no_network=True,
    )
    assert gates.all_pass, report
    assert report["status"] == "pass"
    manifest_ok, _ = smoke_mod._write_durable_evidence(out, gates, report)
    assert manifest_ok
    lines = _parse_machine_lines(
        (out / smoke_mod.MACHINE_LINES_FILENAME).read_text(encoding="utf-8")
    )
    for gate in (
        "G1_OPERATOR_SCOPE_VERIFIED",
        "G2_OFFLINE_INVENTORY_VERIFIED",
        "G3_CREDENTIAL_BOUNDARY_VERIFIED",
        "G4_REMOTE_S3_DRY_RUN_CONTRACT_VERIFIED",
        "G5_DURABLE_EVIDENCE_DESTINATION_VERIFIED",
        "G6_FAIL_CLOSED_CLOSEOUT_VERIFIED",
    ):
        assert lines[gate] == "true"
    for key, value in smoke_mod.SAFETY_MACHINE_LINES.items():
        assert lines[key] == value


def test_wrong_approved_scope_fails_closed(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    _patch_not_tmp(monkeypatch)
    gates, report = smoke_mod.run_bounded_offline_smoke_preflight(
        fixture_path=FIXTURE,
        durable_output_dir=tmp_path / "out",
        approved_scope_name="wrong_scope",
        offline=True,
        no_network=True,
    )
    assert not gates.g1
    assert report["status"] == "blocked"


def test_missing_fixture_fails_closed(tmp_path: Path) -> None:
    gates, report = smoke_mod.run_bounded_offline_smoke_preflight(
        fixture_path=tmp_path / "missing.json",
        durable_output_dir=tmp_path / "out",
        approved_scope_name=REQUIRED_SCOPE,
        offline=True,
        no_network=True,
    )
    assert not gates.all_pass
    assert "fixture_missing" in report["reasons"]


def test_durable_output_under_tmp_rejected(tmp_path: Path) -> None:
    rc = smoke_mod.main(
        [
            "--fixture",
            str(FIXTURE),
            "--durable-output-dir",
            "/tmp/aws_remote_247_smoke",
            "--approved-scope-name",
            REQUIRED_SCOPE,
            "--offline",
            "--no-network",
        ]
    )
    assert rc == 2


def test_offline_and_no_network_flags_required(tmp_path: Path) -> None:
    gates, report = smoke_mod.run_bounded_offline_smoke_preflight(
        fixture_path=FIXTURE,
        durable_output_dir=tmp_path / "out",
        approved_scope_name=REQUIRED_SCOPE,
        offline=False,
        no_network=True,
    )
    assert not gates.all_pass
    assert "offline_flag_required" in report["reasons"]
    gates2, report2 = smoke_mod.run_bounded_offline_smoke_preflight(
        fixture_path=FIXTURE,
        durable_output_dir=tmp_path / "out2",
        approved_scope_name=REQUIRED_SCOPE,
        offline=True,
        no_network=False,
    )
    assert not gates2.all_pass
    assert "no_network_flag_required" in report2["reasons"]


def test_cli_main_exit_zero_on_happy_path(
    durable_out_dir: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _patch_not_tmp(monkeypatch)
    out = durable_out_dir / "cli_out"
    rc = smoke_mod.main(
        [
            "--fixture",
            str(FIXTURE),
            "--durable-output-dir",
            str(out),
            "--approved-scope-name",
            REQUIRED_SCOPE,
            "--offline",
            "--no-network",
        ]
    )
    assert rc == 0
    assert (out / "MANIFEST.sha256").is_file()
    assert (
        (out / "MANIFEST_VERIFY.log").read_text(encoding="utf-8").startswith("MANIFEST_VERIFY_RC=0")
    )


def test_pr3752_bundle_aws_remote_crosslinks_still_present() -> None:
    text = BUNDLE_TEST.read_text(encoding="utf-8")
    assert "test_aws_remote_247_governance_docs_preserve_blocked_stop_idle_posture" in text
    assert "runner_implemented" in text


def test_canonical_fixture_exists() -> None:
    assert FIXTURE.is_file()
    payload = json.loads(FIXTURE.read_text(encoding="utf-8"))
    assert payload["approved_scope_name"] == REQUIRED_SCOPE


FIXTURES_OPS = REPO_ROOT / "tests" / "fixtures" / "ops"

# Repo-tracked canonical fixtures (CI-portable); derived-style filenames in tmp_path only.
_DERIVED_PACKET_SOURCES: dict[str, tuple[Path, str]] = {
    "approval": (
        FIXTURES_OPS / "remote_paper_approval_command_packet_v0.json",
        "derived_remote_paper_approval_packet_v1_DO_NOT_RUN.json",
    ),
    "inventory": (
        FIXTURES_OPS / "remote_host_inventory_planning_v0.json",
        "derived_remote_host_inventory_v1_DO_NOT_RUN.json",
    ),
    "safety": (
        FIXTURES_OPS / "remote_cost_kill_orphan_safety_v0.json",
        "derived_remote_cost_kill_orphan_safety_v1_DO_NOT_RUN.json",
    ),
    "preflight": (
        FIXTURES_OPS / "preflight_remote_paper_planning_pass_v0.json",
        "derived_preflight_remote_runtime_runner_v1_DO_NOT_RUN.json",
    ),
    "registry": (
        FIXTURES_OPS / "registry_remote_paper_planning_row_v0.json",
        "derived_registry_v1_DO_NOT_RUN.json",
    ),
}


def _copy_derived_packet_triplet(target_dir: Path) -> DirectPacketInput:
    paths: dict[str, Path] = {}
    for key, (source, dest_name) in _DERIVED_PACKET_SOURCES.items():
        dest = target_dir / dest_name
        payload = json.loads(source.read_text(encoding="utf-8"))
        if key == "approval":
            gate = payload.setdefault("planning_gate", {})
            gate.setdefault("hold_no_paper_run", True)
            gate.setdefault("run_start_allowed", False)
            gate.setdefault("aws_remote_execution_allowed", False)
        dest.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
        paths[key] = dest
    return DirectPacketInput(
        approval_packet=paths["approval"],
        host_inventory=paths["inventory"],
        cost_kill_orphan_safety=paths["safety"],
        remote_runtime_preflight=paths["preflight"],
        registry=paths["registry"],
    )


def test_direct_derived_packet_triplet_passes_offline_non_authorizing(
    durable_out_dir: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _patch_not_tmp(monkeypatch)
    packet_dir = tmp_path / "derived_packet"
    packet_dir.mkdir()
    direct = _copy_derived_packet_triplet(packet_dir)
    out = durable_out_dir / "direct_out"
    gates, report = smoke_mod.run_bounded_offline_smoke_preflight(
        fixture_path=None,
        durable_output_dir=out,
        approved_scope_name=REQUIRED_SCOPE,
        offline=True,
        no_network=True,
        direct_packet=direct,
    )
    assert gates.all_pass, report
    assert report["input_mode"] == "direct_derived_packet"
    manifest_ok, _ = smoke_mod._write_durable_evidence(out, gates, report)
    assert manifest_ok
    lines = _parse_machine_lines(
        (out / smoke_mod.MACHINE_LINES_FILENAME).read_text(encoding="utf-8")
    )
    for key, value in smoke_mod.DIRECT_INPUT_MACHINE_LINES.items():
        assert lines[key] == value


@pytest.mark.parametrize(
    "mutator,expected_reason",
    [
        (lambda d: d.approval_packet.unlink(), "approval_packet_missing"),
        (lambda d: d.host_inventory.unlink(), "host_inventory_missing"),
    ],
)
def test_direct_input_missing_required_file_fails_closed(
    tmp_path: Path,
    mutator,
    expected_reason: str,
) -> None:
    packet_dir = tmp_path / "derived_packet"
    packet_dir.mkdir()
    direct = _copy_derived_packet_triplet(packet_dir)
    mutator(direct)
    gates, report = smoke_mod.run_bounded_offline_smoke_preflight(
        fixture_path=None,
        durable_output_dir=tmp_path / "out",
        approved_scope_name=REQUIRED_SCOPE,
        offline=True,
        no_network=True,
        direct_packet=direct,
    )
    assert not gates.all_pass
    assert expected_reason in report["reasons"]


def test_direct_input_do_not_run_false_fails_closed(tmp_path: Path) -> None:
    packet_dir = tmp_path / "derived_packet"
    packet_dir.mkdir()
    direct = _copy_derived_packet_triplet(packet_dir)
    approval = json.loads(direct.approval_packet.read_text(encoding="utf-8"))
    approval["do_not_run"] = False
    direct.approval_packet.write_text(json.dumps(approval, indent=2) + "\n", encoding="utf-8")
    gates, report = smoke_mod.run_bounded_offline_smoke_preflight(
        fixture_path=None,
        durable_output_dir=tmp_path / "out",
        approved_scope_name=REQUIRED_SCOPE,
        offline=True,
        no_network=True,
        direct_packet=direct,
    )
    assert not gates.all_pass
    assert any("do_not_run_required" in reason for reason in report["reasons"])


def test_direct_input_hold_no_paper_run_false_fails_closed(tmp_path: Path) -> None:
    packet_dir = tmp_path / "derived_packet"
    packet_dir.mkdir()
    direct = _copy_derived_packet_triplet(packet_dir)
    approval = json.loads(direct.approval_packet.read_text(encoding="utf-8"))
    approval["planning_gate"]["hold_no_paper_run"] = False
    direct.approval_packet.write_text(json.dumps(approval, indent=2) + "\n", encoding="utf-8")
    gates, report = smoke_mod.run_bounded_offline_smoke_preflight(
        fixture_path=None,
        durable_output_dir=tmp_path / "out",
        approved_scope_name=REQUIRED_SCOPE,
        offline=True,
        no_network=True,
        direct_packet=direct,
    )
    assert not gates.all_pass
    assert "approval:hold_no_paper_run_required" in report["reasons"]


@pytest.mark.parametrize(
    "field,payload_key",
    [
        ("live_authority", "safety"),
        ("testnet_authority", "safety"),
        ("network_called", "safety"),
        ("aws_cli_called", "safety"),
    ],
)
def test_direct_input_forbidden_authority_true_fails_closed(
    tmp_path: Path, field: str, payload_key: str
) -> None:
    packet_dir = tmp_path / "derived_packet"
    packet_dir.mkdir()
    direct = _copy_derived_packet_triplet(packet_dir)
    path = direct.cost_kill_orphan_safety
    payload = json.loads(path.read_text(encoding="utf-8"))
    payload[field] = True
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    gates, report = smoke_mod.run_bounded_offline_smoke_preflight(
        fixture_path=None,
        durable_output_dir=tmp_path / "out",
        approved_scope_name=REQUIRED_SCOPE,
        offline=True,
        no_network=True,
        direct_packet=direct,
    )
    assert not gates.all_pass
    assert any(field in reason for reason in report["reasons"])


def test_direct_input_cli_main_exit_zero(
    durable_out_dir: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _patch_not_tmp(monkeypatch)
    packet_dir = tmp_path / "derived_packet"
    packet_dir.mkdir()
    direct = _copy_derived_packet_triplet(packet_dir)
    out = durable_out_dir / "direct_cli_out"
    rc = smoke_mod.main(
        [
            "--approval-packet",
            str(direct.approval_packet),
            "--host-inventory",
            str(direct.host_inventory),
            "--cost-kill-orphan-safety",
            str(direct.cost_kill_orphan_safety),
            "--remote-runtime-preflight",
            str(direct.remote_runtime_preflight),
            "--registry",
            str(direct.registry),
            "--durable-output-dir",
            str(out),
            "--approved-scope-name",
            REQUIRED_SCOPE,
            "--offline",
            "--no-network",
        ]
    )
    assert rc == 0
    lines = _parse_machine_lines(
        (out / smoke_mod.MACHINE_LINES_FILENAME).read_text(encoding="utf-8")
    )
    assert lines["DERIVED_PACKET_DIRECT_INPUT_USED"] == "true"
    assert lines["EVIDENCE_ONLY_WRAPPER_REQUIRED"] == "false"
