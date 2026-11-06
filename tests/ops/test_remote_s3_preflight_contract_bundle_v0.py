"""Integrative offline contract bundle: remote runtime preflight, packet validator, S3 export preflight.

Reuses canonical owners (no parallel scripts):
- scripts/ops/preflight_remote_runtime_runner_v0.py
- scripts/ops/validate_remote_paper_packet_v0.py
- scripts/ops/preflight_s3_finalized_evidence_export_v0.py
- scripts/ops/primary_evidence_retention_v0.py
- tests/fixtures/ops/* (existing remote paper planning fixtures)
"""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path
from typing import Any

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
FIXTURES = REPO_ROOT / "tests" / "fixtures" / "ops"
REMOTE_PREFLIGHT_SCRIPT = REPO_ROOT / "scripts" / "ops" / "preflight_remote_runtime_runner_v0.py"
S3_PREFLIGHT_SCRIPT = REPO_ROOT / "scripts" / "ops" / "preflight_s3_finalized_evidence_export_v0.py"
VALIDATOR_CLI = REPO_ROOT / "scripts" / "ops" / "validate_remote_paper_packet_v0.py"
FORBIDDEN_PARALLEL_SCRIPT = REPO_ROOT / "scripts/ops/post_closeout_chain_execute_v0.py"

RUN_ID = "remote_paper_planning_run_20260526T120000Z"
LANE_ID = "paper"

CANONICAL_OWNERS: dict[str, Path] = {
    "preflight_remote_runtime_runner_v0": REMOTE_PREFLIGHT_SCRIPT,
    "validate_remote_paper_packet_v0": VALIDATOR_CLI,
    "preflight_s3_finalized_evidence_export_v0": S3_PREFLIGHT_SCRIPT,
    "primary_evidence_retention_v0": REPO_ROOT
    / "scripts"
    / "ops"
    / "primary_evidence_retention_v0.py",
    "durable_closeout_copy_verify_v0": REPO_ROOT
    / "scripts"
    / "ops"
    / "durable_closeout_copy_verify_v0.py",
}

EXISTING_FIXTURES = {
    "preflight": FIXTURES / "preflight_remote_paper_planning_pass_v0.json",
    "packet": FIXTURES / "remote_paper_approval_command_packet_v0.json",
    "inventory": FIXTURES / "remote_host_inventory_planning_v0.json",
    "safety": FIXTURES / "remote_cost_kill_orphan_safety_v0.json",
    "registry": FIXTURES / "registry_remote_paper_planning_row_v0.json",
}

REMOTE_BOUNDARY_BOOLS_FALSE = (
    "runner_implemented",
    "runtime_commands_called",
    "aws_cli_called",
    "rclone_called",
    "network_called",
    "s3_upload_called",
    "s3_download_called",
    "process_control_called",
    "mutation_called",
    "live_authority",
    "testnet_authority",
)

S3_BOUNDARY_BOOLS_FALSE = (
    "network_actions_called",
    "aws_cli_called",
    "rclone_called",
    "upload_called",
    "download_called",
    "mutation_called",
    "live_authority",
    "testnet_authority",
)


def _import_script(path: Path, module_name: str):
    spec = importlib.util.spec_from_file_location(module_name, path)
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


def _patch_not_tmp(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "scripts.ops.primary_evidence_retention_v0.is_under_tmp",
        lambda _path: False,
    )
    import scripts.ops.preflight_s3_finalized_evidence_export_v0 as s3_mod

    monkeypatch.setattr(s3_mod, "is_under_tmp", lambda _path: False)


def _write_eligible_durable_root(root: Path) -> None:
    from scripts.ops.primary_evidence_retention_v0 import write_manifest_sha256

    root.mkdir(parents=True, exist_ok=True)
    (root / "scheduler_completion_closeout_v0.json").write_text("{}", encoding="utf-8")
    (root / "evidence.txt").write_text("finalized", encoding="utf-8")
    write_manifest_sha256(root)


def _write_registry(
    path: Path,
    *,
    archive_root: Path,
    run_id: str,
    lane_id: str,
    archive_path: str,
    evidence_transport: str,
) -> None:
    path.write_text(
        json.dumps(
            {
                "schema": "peak_trade.generic_evidence_run_registry.v1",
                "archive_root": str(archive_root.resolve()),
                "runs": [
                    {
                        "run_id": run_id,
                        "lane_id": lane_id,
                        "archive_path": archive_path,
                        "evidence_transport": evidence_transport,
                        "manifest_verified": True,
                    }
                ],
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )


def _remote_preflight_kwargs(**overrides: Any) -> dict[str, Any]:
    base = {
        "dry_run": True,
        "no_network": True,
        "runtime_host": "remote",
        "runtime_backend": "ec2",
        "runtime_mode": "paper_only",
        "lane_id": LANE_ID,
        "remote_run_id": RUN_ID,
        "max_runtime_seconds": 3600,
        "evidence_root_type": "remote_durable",
        "evidence_transport": "local_only",
        "registry_json": None,
        "s3_prefix_plan_json": None,
        "approval_record": None,
        "scheduler_guard_json": None,
    }
    base.update(overrides)
    return base


def _validator_pass_argv(
    *,
    preflight: Path,
    packet: Path,
    registry: Path,
    s3_plan: Path | None = None,
) -> list[str]:
    args = [
        "--preflight-json",
        str(preflight),
        "--approval-packet-json",
        str(packet),
        "--host-inventory-json",
        str(EXISTING_FIXTURES["inventory"]),
        "--cost-kill-orphan-json",
        str(EXISTING_FIXTURES["safety"]),
        "--registry-json",
        str(registry),
    ]
    if s3_plan is not None:
        args.extend(["--s3-prefix-plan-json", str(s3_plan)])
    return args


@pytest.fixture(scope="module")
def remote_preflight_mod():
    return _import_script(REMOTE_PREFLIGHT_SCRIPT, "bundle_preflight_remote_runtime_runner_v0")


@pytest.fixture(scope="module")
def s3_preflight_mod():
    return _import_script(S3_PREFLIGHT_SCRIPT, "bundle_preflight_s3_finalized_evidence_export_v0")


@pytest.fixture(scope="module")
def validator_cli():
    return _import_script(VALIDATOR_CLI, "bundle_validate_remote_paper_packet_v0")


@pytest.fixture
def durable_root(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    _patch_not_tmp(monkeypatch)
    root = tmp_path / "durable_evidence"
    _write_eligible_durable_root(root)
    return root


def test_reuse_drift_guard_canonical_owners_exist() -> None:
    for rel_path in CANONICAL_OWNERS.values():
        assert rel_path.is_file(), f"missing canonical owner: {rel_path}"


def test_forbidden_post_closeout_chain_execute_script_absent() -> None:
    assert not FORBIDDEN_PARALLEL_SCRIPT.exists()


def test_remote_preflight_eligible_planning_only_boundary(
    remote_preflight_mod, tmp_path: Path
) -> None:
    registry_path = tmp_path / "registry.json"
    _write_registry(
        registry_path,
        archive_root=tmp_path / "archive",
        run_id=RUN_ID,
        lane_id=LANE_ID,
        archive_path=f"runs/{LANE_ID}/{RUN_ID}",
        evidence_transport="local_only",
    )
    result = remote_preflight_mod.run_preflight(
        **_remote_preflight_kwargs(registry_json=registry_path)
    )
    assert result["status"] == "eligible"
    assert result["dry_run"] is True
    assert result["no_network"] is True
    for field in REMOTE_BOUNDARY_BOOLS_FALSE:
        assert result[field] is False
    assert result.get("ready_for_start") is not True
    assert str(result.get("status", "")).lower() not in {
        "ready_for_start",
        "ready_for_operator_arming",
        "unblocked",
        "pass",
    }


def test_validate_remote_paper_packet_reuses_existing_fixtures_pass(validator_cli, capsys) -> None:
    rc = validator_cli.main(
        _validator_pass_argv(
            preflight=EXISTING_FIXTURES["preflight"],
            packet=EXISTING_FIXTURES["packet"],
            registry=EXISTING_FIXTURES["registry"],
        )
    )
    captured = capsys.readouterr()
    assert rc == 0
    assert "REMOTE_PAPER_VALIDATOR_CLI_STATUS=PASS" in captured.out
    assert "REMOTE_PAPER_VALIDATOR_CLI_READY_FOR_START=false" in captured.out
    assert "REMOTE_PAPER_VALIDATOR_CLI_PREFLIGHT_BLOCKED_LIFTED=false" in captured.out


def test_s3_preflight_finalized_durable_root_export_prefix_plan(
    s3_preflight_mod, durable_root: Path
) -> None:
    result = s3_preflight_mod.run_preflight(
        durable_root,
        dry_run=True,
        no_network=True,
        run_id=RUN_ID,
        lane_id=LANE_ID,
        export_prefix_plan=True,
    )
    assert result["status"] == "eligible"
    assert result["manifest_verify_rc"] == 0
    for field in S3_BOUNDARY_BOOLS_FALSE:
        assert result[field] is False
    plan = result["export_prefix_plan"]
    assert plan["status"] == "proposed"
    assert plan["run_id"] == RUN_ID
    assert plan["lane_id"] == LANE_ID
    assert plan["upload_called"] is False
    assert plan["network_actions_called"] is False


def test_cross_bundle_s3_transport_registry_remote_preflight_and_validator(
    remote_preflight_mod,
    s3_preflight_mod,
    validator_cli,
    durable_root: Path,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _patch_not_tmp(monkeypatch)
    archive_root = durable_root.parent
    archive_rel = "durable_evidence"
    registry_path = tmp_path / "bundle_registry.json"
    _write_registry(
        registry_path,
        archive_root=archive_root,
        run_id=RUN_ID,
        lane_id=LANE_ID,
        archive_path=archive_rel,
        evidence_transport="s3_export_after_finalize",
    )

    s3_result = s3_preflight_mod.run_preflight(
        durable_root,
        dry_run=True,
        no_network=True,
        registry_json=registry_path,
        run_id=RUN_ID,
        lane_id=LANE_ID,
        export_prefix_plan=True,
    )
    assert s3_result["status"] == "eligible"
    plan_path = tmp_path / "s3_prefix_plan.json"
    plan_path.write_text(json.dumps(s3_result["export_prefix_plan"], indent=2), encoding="utf-8")

    remote_result = remote_preflight_mod.run_preflight(
        **_remote_preflight_kwargs(
            evidence_transport="s3_export_after_finalize_plan",
            registry_json=registry_path,
            s3_prefix_plan_json=plan_path,
        )
    )
    assert remote_result["status"] == "eligible"
    assert remote_result["evidence_transport"] == "s3_export_after_finalize_plan"
    for field in REMOTE_BOUNDARY_BOOLS_FALSE:
        assert remote_result[field] is False

    preflight_path = tmp_path / "remote_preflight.json"
    preflight_path.write_text(json.dumps(remote_result, indent=2), encoding="utf-8")

    packet = json.loads(EXISTING_FIXTURES["packet"].read_text(encoding="utf-8"))
    packet["evidence_transport"] = "s3_export_after_finalize_plan"
    packet["remote_run_id"] = RUN_ID
    packet_path = tmp_path / "packet.json"
    packet_path.write_text(json.dumps(packet, indent=2), encoding="utf-8")

    registry_bundle = json.loads(registry_path.read_text(encoding="utf-8"))
    registry_bundle_path = tmp_path / "registry_bundle.json"
    registry_bundle_path.write_text(json.dumps(registry_bundle, indent=2), encoding="utf-8")

    rc = validator_cli.main(
        _validator_pass_argv(
            preflight=preflight_path,
            packet=packet_path,
            registry=registry_bundle_path,
            s3_plan=plan_path,
        )
    )
    assert rc == 0

    reg_row = registry_bundle["runs"][0]
    assert reg_row["run_id"] == RUN_ID
    assert reg_row["evidence_transport"] == "s3_export_after_finalize"
    assert remote_result["remote_run_id"] == RUN_ID
    assert s3_result["export_prefix_plan"]["run_id"] == RUN_ID
    from scripts.ops.primary_evidence_retention_v0 import is_under_tmp

    assert is_under_tmp(durable_root) is False


# --- AWS Remote 24/7 daemon static contract crosslink v0 (offline; tests-only) ---

AWS_REMOTE_247_DOC_OWNERS: dict[str, Path] = {
    "paper_shadow_247_preflight": REPO_ROOT
    / "docs"
    / "ops"
    / "runbooks"
    / "PAPER_SHADOW_247_PREFLIGHT_CONTRACT_V0.md",
    "shadow_247_governance_charter": REPO_ROOT
    / "docs"
    / "ops"
    / "runbooks"
    / "SHADOW_247_GOVERNANCE_CHARTER_V0.md",
    "runtime_lane_taxonomy": REPO_ROOT
    / "docs"
    / "ops"
    / "specs"
    / "RUNTIME_LANE_TAXONOMY_AUTHORITY_LEVELS_CONTRACT_V0.md",
}

AWS_REMOTE_247_BUNDLE_SELF = Path(__file__).resolve()

AWS_REMOTE_247_FORBIDDEN_SCRIPT_NAMES = "aws_remote_247_daemon*.py"
AWS_REMOTE_247_FORBIDDEN_RUNBOOK_NAMES = "AWS_REMOTE_247_DAEMON*.md"


def test_aws_remote_247_governance_and_retention_doc_owners_exist() -> None:
    for label, path in AWS_REMOTE_247_DOC_OWNERS.items():
        assert path.is_file(), f"missing aws_remote_247 doc owner {label}: {path}"
    for label, path in CANONICAL_OWNERS.items():
        assert path.is_file(), f"missing aws_remote_247 script owner {label}: {path}"
    assert AWS_REMOTE_247_BUNDLE_SELF.is_file()
    assert REMOTE_PREFLIGHT_SCRIPT.is_file()


def test_aws_remote_247_remote_preflight_declares_runner_not_implemented() -> None:
    source = REMOTE_PREFLIGHT_SCRIPT.read_text(encoding="utf-8")
    assert '"runner_implemented": False' in source or "'runner_implemented': False" in source
    assert "daemon_paper_24h" in source
    assert '"remote_runtime"' in source or "'remote_runtime'" in source


def test_aws_remote_247_governance_docs_preserve_blocked_stop_idle_posture() -> None:
    preflight = AWS_REMOTE_247_DOC_OWNERS["paper_shadow_247_preflight"].read_text(encoding="utf-8")
    charter = AWS_REMOTE_247_DOC_OWNERS["shadow_247_governance_charter"].read_text(encoding="utf-8")
    taxonomy = AWS_REMOTE_247_DOC_OWNERS["runtime_lane_taxonomy"].read_text(encoding="utf-8")

    assert "BLOCKED" in preflight
    assert "ready_for_start=false" in preflight.lower()
    assert "STOP_IDLE" in charter
    assert "not_ready" in charter
    assert "Evidence ≠ Approval" in charter or "Evidence" in charter and "Approval" in charter
    assert "FULL_POST_CLOSEOUT_AUTOMATION_IMPLEMENTED=false" in taxonomy
    assert "POST_CLOSEOUT_AUTOMATION_HOOK_IMPLEMENTED=false" in taxonomy
    assert "REMOTE_RUNTIME_IS_BACKEND_NOT_LANE=true" in taxonomy
    assert "runner_implemented=false" in taxonomy.lower()


def test_aws_remote_247_docs_do_not_treat_docs_as_runtime_lane_authority() -> None:
    preflight = AWS_REMOTE_247_DOC_OWNERS["paper_shadow_247_preflight"].read_text(encoding="utf-8")
    taxonomy = AWS_REMOTE_247_DOC_OWNERS["runtime_lane_taxonomy"].read_text(encoding="utf-8")

    assert "does not authorize" in preflight.lower()
    assert "EVIDENCE_DOES_NOT_AUTHORIZE_RUNTIME=true" in taxonomy
    assert (
        "does not grant gate clearance" in taxonomy.lower() or "does not clear" in taxonomy.lower()
    )


def test_aws_remote_247_no_parallel_daemon_runner_or_runbook_surfaces() -> None:
    assert not FORBIDDEN_PARALLEL_SCRIPT.exists()
    ops_scripts = REPO_ROOT / "scripts" / "ops"
    runbooks = REPO_ROOT / "docs" / "ops" / "runbooks"
    assert list(ops_scripts.glob(AWS_REMOTE_247_FORBIDDEN_SCRIPT_NAMES)) == []
    assert list(runbooks.glob(AWS_REMOTE_247_FORBIDDEN_RUNBOOK_NAMES)) == []


def test_aws_remote_247_remote_preflight_forbids_daemon_paper_24h_as_lane(
    remote_preflight_mod,
) -> None:
    forbidden = remote_preflight_mod.FORBIDDEN_LANE_IDS
    assert "daemon_paper_24h" in forbidden
    assert "remote_runtime" in forbidden
    result = remote_preflight_mod.run_preflight(
        **_remote_preflight_kwargs(lane_id="daemon_paper_24h")
    )
    assert result["status"] in {"blocked", "invalid"}
    assert result["runner_implemented"] is False
    assert result["network_called"] is False
    assert result["aws_cli_called"] is False
