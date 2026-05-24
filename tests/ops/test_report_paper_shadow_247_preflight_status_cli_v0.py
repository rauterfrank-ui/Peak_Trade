"""CLI tests for the Paper/Shadow 24/7 preflight status reporter (read-only)."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

from scripts.ops.report_paper_shadow_247_preflight_status import (
    build_paper_shadow_247_preflight_status,
)

try:
    import tomllib
except ImportError:
    import tomli as tomllib


REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT = REPO_ROOT / "scripts" / "ops" / "report_paper_shadow_247_preflight_status.py"
PREFLIGHT_CONFIG = REPO_ROOT / "config" / "ops" / "paper_shadow_247_preflight.toml"
SCHEDULER_CONFIG_REL = "config/scheduler/jobs.toml"


def _materialize_minimal_preflight_repo(root: Path, *, include_scheduler_jobs: bool) -> None:
    """Tiny repo layout for offline contract tests (no real Peak_Trade checkout)."""

    contract = root / "docs" / "ops" / "runbooks" / "PAPER_SHADOW_247_PREFLIGHT_CONTRACT_V0.md"
    contract.parent.mkdir(parents=True, exist_ok=True)
    contract.write_text(
        "\n".join(
            [
                "# Minimal contract fixture for offline tests",
                "",
                "Current status: **BLOCKED**.",
                "",
                "STOP — do not activate Paper/Shadow 24/7 until operators explicitly lift the block.",
                "",
                "Non-authority: this document is not trading authority.",
                "",
            ]
        ),
        encoding="utf-8",
    )
    sched_doc = root / "docs" / "SCHEDULER_DAEMON.md"
    sched_doc.parent.mkdir(parents=True, exist_ok=True)
    sched_doc.write_text(
        "Preflight: PAPER_SHADOW_247_PREFLIGHT_CONTRACT_V0.md\n",
        encoding="utf-8",
    )
    meta = root / "config" / "ops" / "paper_shadow_247_preflight.toml"
    meta.parent.mkdir(parents=True, exist_ok=True)
    meta.write_text(
        "\n".join(
            [
                'schema_version = "paper_shadow_247_preflight.v0"',
                'canonical_owner = "ops-test-offline-min"',
                "",
                "paper_jobs = [",
                '  "paper_shadow_247_paper_only_preflight_status_v0",',
                "]",
                "",
                "shadow_jobs = [",
                '  "p7_shadow_high_vol_no_trade_runner_manual_v0",',
                "]",
                "",
                "output_paths = [",
                '  "out/paper_shadow_247/paper",',
                "]",
                "",
                'stop_command = "echo stop"',
                'emergency_stop_command = "echo emergency"',
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    if include_scheduler_jobs:
        jobs = root / "config" / "scheduler" / "jobs.toml"
        jobs.parent.mkdir(parents=True, exist_ok=True)
        jobs.write_text(
            "\n".join(
                [
                    "[[job]]",
                    'name = "paper_shadow_247_paper_only_preflight_status_v0"',
                    "enabled = true",
                    'schedule_type = "once"',
                    'command = "python"',
                    "paper_only = true",
                    "dry_run_visible = true",
                    "testnet_authorized = false",
                    "live_authorized = false",
                    "broker_authorized = false",
                    "exchange_authorized = false",
                    "order_submission_authorized = false",
                    "",
                ]
            ),
            encoding="utf-8",
        )


def _tree_snapshot(root: Path) -> set[str]:
    return {str(p.relative_to(root)) for p in root.rglob("*")}


def _assert_command_inventory_shape(payload: dict[str, object]) -> None:
    meta = tomllib.loads(PREFLIGHT_CONFIG.read_text(encoding="utf-8"))
    paper = [str(x) for x in meta["paper_jobs"]]
    shadow = [str(x) for x in meta["shadow_jobs"]]
    commands = payload["commands"]
    assert isinstance(commands, list)
    assert len(commands) == len(paper) + len(shadow)
    assert [c["name"] for c in commands] == paper + shadow
    assert [c["source"] for c in commands] == ["paper"] * len(paper) + ["shadow"] * len(shadow)

    by_name = {str(c["name"]): c for c in commands}
    preflight = by_name["paper_shadow_247_paper_only_preflight_status_v0"]
    assert preflight["found"] is True
    assert preflight["enabled"] is True
    assert preflight["command"] == "python"
    safety_pf = preflight["safety_classification"]
    assert isinstance(safety_pf, dict)
    assert safety_pf["paper_only"] is True
    assert safety_pf["dry_run_visible"] is True
    assert safety_pf["paper_runtime_job"] is None
    assert safety_pf["enabled"] is True
    assert safety_pf["disabled_by_default"] is False
    assert safety_pf["authorization_flags"] == {
        "testnet_authorized": False,
        "live_authorized": False,
        "broker_authorized": False,
        "exchange_authorized": False,
        "order_submission_authorized": False,
    }
    assert safety_pf["non_authorizing"] is True
    args_pf = preflight["args"]
    assert isinstance(args_pf, dict)
    assert args_pf["script"] == "scripts/ops/report_paper_shadow_247_preflight_status.py"

    min_job = by_name["paper_shadow_247_paper_only_runtime_min_v0"]
    assert min_job["found"] is True
    assert min_job["enabled"] is False
    assert min_job["command"] == "python"
    assert min_job["timeout_seconds"] == 600
    safety_min = min_job["safety_classification"]
    assert isinstance(safety_min, dict)
    assert safety_min["paper_only"] is True
    assert safety_min["dry_run_visible"] is True
    assert safety_min["paper_runtime_job"] is True
    assert safety_min["enabled"] is False
    assert safety_min["disabled_by_default"] is True
    assert safety_min["authorization_flags"] == {
        "testnet_authorized": False,
        "live_authorized": False,
        "broker_authorized": False,
        "exchange_authorized": False,
        "order_submission_authorized": False,
    }
    assert safety_min["non_authorizing"] is True
    args_min = min_job["args"]
    assert isinstance(args_min, dict)
    assert args_min["script"] == "scripts/aiops/run_paper_trading_session.py"
    assert args_min["spec"] == "tests/fixtures/p7/paper_run_min_v0.json"
    assert args_min["outdir"] == "out/paper_shadow_247/runtime/min/__DRY_RUN_PLACEHOLDER__"

    high_job = by_name["paper_shadow_247_paper_only_runtime_high_vol_no_trade_v0"]
    assert high_job["found"] is True
    assert high_job["enabled"] is False
    assert high_job["command"] == "python"
    assert high_job["timeout_seconds"] == 600
    safety_high = high_job["safety_classification"]
    assert isinstance(safety_high, dict)
    assert safety_high["paper_only"] is True
    assert safety_high["dry_run_visible"] is True
    assert safety_high["paper_runtime_job"] is True
    assert safety_high["enabled"] is False
    assert safety_high["disabled_by_default"] is True
    assert safety_high["authorization_flags"] == {
        "testnet_authorized": False,
        "live_authorized": False,
        "broker_authorized": False,
        "exchange_authorized": False,
        "order_submission_authorized": False,
    }
    assert safety_high["non_authorizing"] is True
    args_high = high_job["args"]
    assert isinstance(args_high, dict)
    assert args_high["script"] == "scripts/aiops/run_paper_trading_session.py"
    assert args_high["spec"] == "tests/fixtures/p7/paper_run_high_vol_no_trade_v0.json"
    assert (
        args_high["outdir"]
        == "out/paper_shadow_247/runtime/high_vol_no_trade/__DRY_RUN_PLACEHOLDER__"
    )

    assert not any(str(c["name"]).startswith("paper_runner_") for c in commands)
    for name in paper:
        assert by_name[name]["found"] is True, name
    shadow_entry = by_name["p7_shadow_high_vol_no_trade_runner_manual_v0"]
    assert shadow_entry["source"] == "shadow"
    assert shadow_entry["found"] is False
    assert "safety_classification" not in shadow_entry


def _assert_hold_context_v0(payload: dict[str, object]) -> None:
    hc = payload["hold_context_v0"]
    assert isinstance(hc, dict)
    assert hc["schema_version"] == "unknown_hold_context.v0"
    assert hc["current_state"] == "HOLD_NO_PAPER_RUN"
    assert hc["operator_classification"] == "unknown"
    assert hc["go_live_next_step"] == "blocked"
    assert hc["non_authorizing"] is True
    assert isinstance(hc.get("reason"), str) and "unknown" in hc["reason"].lower()
    refs = hc["canonical_doc_refs"]
    assert refs == [
        "docs/ops/runbooks/incident_stop_freeze_rollback.md",
        "docs/SCHEDULER_DAEMON.md",
        "docs/ops/runbooks/PAPER_SHADOW_247_PREFLIGHT_CONTRACT_V0.md",
    ]
    prog = hc["progression_authorization"]
    assert isinstance(prog, dict)
    for key in (
        "activation_authorized",
        "daemon_activation_authorized",
        "scheduler_execution_authorized",
        "paper_runtime_authorized",
        "shadow_runtime_authorized",
        "testnet_authorized",
        "live_authorized",
        "broker_authorized",
        "exchange_authorized",
        "order_submission_authorized",
    ):
        assert prog[key] is False


def _assert_operator_moment_snapshot_v0(payload: dict[str, object]) -> None:
    moment = payload["operator_moment_snapshot_v0"]
    assert isinstance(moment, dict)
    assert moment["schema_version"] == "paper_shadow_247_operator_moment_snapshot.v0"
    assert moment["non_authorizing"] is True
    assert moment["does_not_activate_runtime"] is True
    mirror = moment["mirror_top_level"]
    assert isinstance(mirror, dict)
    assert mirror["status"] == "BLOCKED"
    assert mirror["activation_authorized"] is False
    assert mirror["daemon_activation_authorized"] is False
    assert mirror["paper_runtime_authorized"] is False
    assert mirror["shadow_runtime_authorized"] is False
    assert mirror["testnet_authorized"] is False
    assert mirror["live_authorized"] is False
    assert mirror["broker_authorized"] is False
    assert mirror["exchange_authorized"] is False
    assert mirror["order_submission_authorized"] is False
    assert mirror["scheduler_execution_authorized"] is False
    assert mirror["dry_run_only"] is True
    assert moment["dry_activation_readiness_ready"] is False
    assert moment["hold_context_v0"] == payload["hold_context_v0"]
    _assert_hold_context_v0(payload)
    summary = moment["command_inventory_summary"]
    assert isinstance(summary, dict)
    commands = payload["commands"]
    assert isinstance(commands, list)
    assert summary["commands_total"] == len(commands)
    assert summary["found_true"] + summary["found_false"] == summary["commands_total"]
    assert (
        summary["enabled_true"] + summary["enabled_false"] + summary["enabled_unset"]
        == summary["commands_total"]
    )
    assert summary["paper_runtime_jobs_scheduled_disabled"] == 2
    stop = moment["stop_signal_snapshot"]
    assert isinstance(stop, dict)
    assert stop["contract"] == "operator_stop_signal_snapshot_v1"
    assert isinstance(stop.get("summary"), str)


def _run_json() -> dict[str, object]:
    result = subprocess.run(
        [sys.executable, str(SCRIPT), "--json", "--repo-root", str(REPO_ROOT)],
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    assert result.returncode == 0
    assert result.stderr == ""
    return json.loads(result.stdout)


def test_build_paper_shadow_247_preflight_status_is_blocked_and_non_authorizing() -> None:
    payload = build_paper_shadow_247_preflight_status(REPO_ROOT)

    assert payload["contract"] == "paper_shadow_247_preflight_status_v0"
    assert payload["schema_version"] == 0
    assert payload["status"] == "BLOCKED"
    assert payload["activation_authorized"] is False
    assert payload["daemon_activation_authorized"] is False
    assert payload["paper_runtime_authorized"] is False
    assert payload["shadow_runtime_authorized"] is False
    assert payload["testnet_authorized"] is False
    assert payload["live_authorized"] is False
    assert payload["broker_authorized"] is False
    assert payload["exchange_authorized"] is False
    assert payload["order_submission_authorized"] is False
    assert payload["scheduler_execution_authorized"] is False
    assert payload["dry_run_only"] is True
    assert payload["canonical_owner"] == "ops-paper-shadow-247-readiness"
    assert payload["paper_jobs"]
    assert payload["shadow_jobs"]
    _assert_command_inventory_shape(payload)
    assert payload["output_paths"]
    assert isinstance(payload["stop_command"], str)
    assert payload["stop_command"]
    assert isinstance(payload["emergency_stop_command"], str)
    assert payload["emergency_stop_command"]
    assert payload["risk_flags"] == {
        "live": False,
        "testnet": False,
        "broker": False,
        "exchange": False,
        "orders": False,
        "network": False,
    }
    assert payload["blockers"] == []
    assert payload["status_reasons"] == []
    assert "operator_moment_snapshot_v0" in payload["notes"]
    assert "unknown_hold_context_v0" in payload["notes"]
    _assert_operator_moment_snapshot_v0(payload)


def test_build_paper_shadow_247_preflight_status_reuses_existing_contract_surfaces() -> None:
    payload = build_paper_shadow_247_preflight_status(REPO_ROOT)

    assert all(payload["required_files"].values())
    assert payload["contract_markers"]["contract_doc_exists"] is True
    assert payload["contract_markers"]["contract_states_blocked"] is True
    assert payload["contract_markers"]["contract_mentions_stop"] is True
    assert payload["contract_markers"]["contract_non_authority"] is True
    assert payload["contract_markers"]["scheduler_doc_links_contract"] is True
    assert payload["contract_markers"]["scheduler_config_has_direct_247_job"] is True


def test_cli_json_output_is_json_native_and_does_not_execute_scheduler() -> None:
    payload = _run_json()

    assert payload["status"] == "BLOCKED"
    assert payload["activation_authorized"] is False
    assert payload["dry_run_command"].endswith("--dry-run --once --verbose")
    assert "does_not_run_scheduler" in payload["notes"]
    assert "does_not_start_daemon" in payload["notes"]
    assert "scheduler_command_inventory_v0" in payload["notes"]
    assert "scheduler_command_safety_classification_v0" in payload["notes"]
    assert "operator_moment_snapshot_v0" in payload["notes"]
    assert "unknown_hold_context_v0" in payload["notes"]
    _assert_command_inventory_shape(payload)
    _assert_operator_moment_snapshot_v0(payload)


def test_unknown_hold_context_v0_is_present_in_build_and_cli_json() -> None:
    built = build_paper_shadow_247_preflight_status(REPO_ROOT)
    _assert_hold_context_v0(built)

    cli_payload = _run_json()
    _assert_hold_context_v0(cli_payload)
    assert cli_payload["hold_context_v0"] == built["hold_context_v0"]
    assert all(
        cli_payload["hold_context_v0"]["progression_authorization"][k] is False
        for k in cli_payload["hold_context_v0"]["progression_authorization"]
    )


def test_operator_decision_context_v0_absent_without_decision_record() -> None:
    payload = build_paper_shadow_247_preflight_status(REPO_ROOT)
    assert "operator_decision_context_v0" not in payload
    moment = payload["operator_moment_snapshot_v0"]["stop_signal_snapshot"]
    assert "operator_decision_context_v0" not in moment


def test_build_paper_shadow_247_preflight_status_operator_decision_context_v0_when_record_provided(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    for key in ("PT_INCIDENT_STOP", "PT_FORCE_NO_TRADE", "PT_ENABLED", "PT_ARMED"):
        monkeypatch.delenv(key, raising=False)
    _materialize_minimal_preflight_repo(tmp_path, include_scheduler_jobs=True)
    decision = tmp_path / "op_decision.md"
    decision.write_text(
        "\n".join(
            [
                "OPERATOR_CLASSIFICATION=stale_closed",
                "CURRENT_STATE=HOLD_NO_PAPER_RUN_PENDING_RERUN",
                "GO_LIVE_NEXT_STEP=read_only_snapshot_and_preflight_rerun",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    payload = build_paper_shadow_247_preflight_status(
        tmp_path,
        operator_decision_record=decision,
    )
    ctx = payload["operator_decision_context_v0"]
    assert ctx["schema_version"] == "operator_decision_context.v0"
    assert ctx["operator_classification"] == "stale_closed"
    assert ctx["non_authorizing"] is True
    assert ctx["permits_scheduler_runtime_paper_testnet_live"] is False
    assert "operator_decision_context_v0" in payload["notes"]

    _assert_hold_context_v0(payload)
    assert payload["status"] == "BLOCKED"
    assert payload["activation_authorized"] is False

    stop = payload["operator_moment_snapshot_v0"]["stop_signal_snapshot"]
    assert stop["operator_decision_context_v0"] == ctx


def test_build_paper_shadow_247_preflight_status_invalid_operator_record_raises(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    for key in ("PT_INCIDENT_STOP", "PT_FORCE_NO_TRADE", "PT_ENABLED", "PT_ARMED"):
        monkeypatch.delenv(key, raising=False)
    _materialize_minimal_preflight_repo(tmp_path, include_scheduler_jobs=True)
    missing = tmp_path / "missing.md"
    with pytest.raises(ValueError, match="not a file"):
        build_paper_shadow_247_preflight_status(tmp_path, operator_decision_record=missing)


def test_preflight_cli_operator_decision_record_propagates_to_json(tmp_path: Path) -> None:
    decision = tmp_path / "decision.md"
    decision.write_text("OPERATOR_CLASSIFICATION=stale_closed\n", encoding="utf-8")
    result = subprocess.run(
        [
            sys.executable,
            str(SCRIPT),
            "--json",
            "--repo-root",
            str(REPO_ROOT),
            "--operator-decision-record",
            str(decision),
        ],
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    assert result.returncode == 0
    assert result.stderr == ""
    payload = json.loads(result.stdout)
    assert payload["operator_decision_context_v0"]["operator_classification"] == "stale_closed"
    stop = payload["operator_moment_snapshot_v0"]["stop_signal_snapshot"]
    assert stop["operator_decision_context_v0"]["operator_classification"] == "stale_closed"
    _assert_hold_context_v0(payload)


def test_preflight_cli_operator_decision_record_missing_file_exits_2(tmp_path: Path) -> None:
    missing = tmp_path / "missing.md"
    result = subprocess.run(
        [
            sys.executable,
            str(SCRIPT),
            "--repo-root",
            str(REPO_ROOT),
            "--operator-decision-record",
            str(missing),
        ],
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    assert result.returncode == 2
    assert "ERR:" in result.stderr
    result = subprocess.run(
        [sys.executable, str(SCRIPT), "--repo-root", str(REPO_ROOT)],
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0
    assert result.stderr == ""
    assert result.stdout.splitlines() == [
        "status=BLOCKED",
        "activation_authorized=false",
        "dry_run_only=true",
        "hold_current_state=HOLD_NO_PAPER_RUN",
        "hold_operator_classification=unknown",
        "hold_go_live_next_step=blocked",
        "hold_non_authorizing=true",
        "hold_daemon_activation_authorized=false",
        "hold_scheduler_activation_authorized=false",
        "hold_paper_validation_authorized=false",
        "hold_testnet_authorized=false",
        "hold_live_authorized=false",
    ]


def test_paper_shadow_247_preflight_paper_jobs_align_with_scheduler_inventory() -> None:
    """P7 paper_runner_* contract fixtures must not be canonical scheduler job expectations."""

    meta = tomllib.loads(PREFLIGHT_CONFIG.read_text(encoding="utf-8"))
    paper_jobs = [str(x) for x in meta["paper_jobs"]]
    assert paper_jobs == [
        "paper_shadow_247_paper_only_runtime_min_v0",
        "paper_shadow_247_paper_only_runtime_high_vol_no_trade_v0",
        "paper_shadow_247_paper_only_preflight_status_v0",
    ]
    assert not any(name.startswith("paper_runner_") for name in paper_jobs)

    payload = _run_json()
    by_name = {str(c["name"]): c for c in payload["commands"]}
    for name in paper_jobs:
        assert by_name[name]["found"] is True, name


def test_paper_shadow_247_preflight_metadata_config_is_materialized() -> None:
    config_path = REPO_ROOT / "config" / "ops" / "paper_shadow_247_preflight.toml"

    assert config_path.exists()
    text = config_path.read_text(encoding="utf-8")

    assert 'schema_version = "paper_shadow_247_preflight.v0"' in text
    assert "canonical_owner" in text
    assert "paper_jobs" in text
    assert "shadow_jobs" in text
    assert "output_paths" in text
    assert "stop_command" in text
    assert "emergency_stop_command" in text
    assert "activation_authorized = false" in text
    assert "daemon_activation_authorized = false" in text
    assert "scheduler_execution_authorized = false" in text


def test_paper_shadow_247_preflight_metadata_removes_missing_field_blockers() -> None:
    payload = _run_json()

    assert payload["status"] == "BLOCKED"
    assert payload["activation_authorized"] is False
    assert payload["daemon_activation_authorized"] is False
    assert payload["scheduler_execution_authorized"] is False
    assert payload["paper_runtime_authorized"] is False
    assert payload["shadow_runtime_authorized"] is False

    assert payload["canonical_owner"] == "ops-paper-shadow-247-readiness"
    assert payload["paper_jobs"]
    assert payload["shadow_jobs"]
    assert payload["output_paths"]
    assert payload["stop_command"]
    assert payload["emergency_stop_command"]

    status_reasons = set(payload.get("status_reasons", []))
    blockers = set(payload.get("blockers", []))

    for removed in (
        "canonical_owner_missing",
        "paper_shadow_job_set_missing",
        "output_paths_missing",
        "stop_commands_missing",
    ):
        assert removed not in status_reasons
        assert removed not in blockers

    for key in (
        "testnet_authorized",
        "live_authorized",
        "broker_authorized",
        "exchange_authorized",
        "order_submission_authorized",
    ):
        assert payload[key] is False


def test_paper_shadow_247_preflight_reports_dry_activation_readiness_without_authorization() -> (
    None
):
    payload = _run_json()
    readiness = payload["dry_activation_readiness"]

    assert readiness["schema_version"] == "paper_shadow_247_dry_activation_readiness.v0"
    assert readiness["ready"] is False
    assert readiness["mode"] == "paper_only_dry_activation_readiness"
    assert readiness["dry_run_only"] is True
    assert readiness["decision"] == "BLOCKED_NON_AUTHORIZING_READINESS_ONLY"

    assert readiness["operator_command"] == payload["dry_run_command"]
    assert readiness["stop_command"] == payload["stop_command"]
    assert readiness["emergency_stop_command"] == payload["emergency_stop_command"]

    assert readiness["checks"] == {
        "metadata_ready": True,
        "authorization_flags_false": True,
        "stop_controls_declared": True,
        "output_paths_declared": True,
        "paper_jobs_declared": True,
        "shadow_jobs_declared": True,
    }

    for key in (
        "activation_authorized",
        "daemon_activation_authorized",
        "scheduler_execution_authorized",
        "paper_runtime_authorized",
        "shadow_runtime_authorized",
        "testnet_authorized",
        "live_authorized",
        "broker_authorized",
        "exchange_authorized",
        "order_submission_authorized",
    ):
        assert payload[key] is False


def test_build_preflight_on_minimal_tmp_repo_is_deterministic_and_writes_no_files(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Reporter is read-only: same tmp tree before/after, stable sorted JSON across builds."""

    for key in ("PT_INCIDENT_STOP", "PT_FORCE_NO_TRADE", "PT_ENABLED", "PT_ARMED"):
        monkeypatch.delenv(key, raising=False)
    _materialize_minimal_preflight_repo(tmp_path, include_scheduler_jobs=True)
    before = _tree_snapshot(tmp_path)
    payload_a = build_paper_shadow_247_preflight_status(tmp_path)
    mid = _tree_snapshot(tmp_path)
    payload_b = build_paper_shadow_247_preflight_status(tmp_path)
    after = _tree_snapshot(tmp_path)

    assert before == mid == after
    stable_a = json.dumps(payload_a, sort_keys=True)
    stable_b = json.dumps(payload_b, sort_keys=True)
    assert stable_a == stable_b
    assert payload_a["status"] == "BLOCKED"
    assert payload_a["activation_authorized"] is False
    assert payload_a["required_files"][SCHEDULER_CONFIG_REL] is True
    commands = payload_a["commands"]
    assert isinstance(commands, list)
    assert any(
        c.get("name") == "paper_shadow_247_paper_only_preflight_status_v0"
        and c.get("found") is True
        for c in commands
    )


def test_build_preflight_missing_scheduler_jobs_toml_marks_config_absent_and_non_authorizing(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """If jobs.toml is absent the inventory is explicit: no scheduler jobs resolved, still blocked."""

    for key in ("PT_INCIDENT_STOP", "PT_FORCE_NO_TRADE", "PT_ENABLED", "PT_ARMED"):
        monkeypatch.delenv(key, raising=False)
    _materialize_minimal_preflight_repo(tmp_path, include_scheduler_jobs=False)
    before = _tree_snapshot(tmp_path)
    payload = build_paper_shadow_247_preflight_status(tmp_path)
    assert _tree_snapshot(tmp_path) == before

    assert payload["required_files"][SCHEDULER_CONFIG_REL] is False
    assert payload["contract_markers"]["scheduler_config_has_direct_247_job"] is False
    assert payload["status"] == "BLOCKED"
    assert payload["activation_authorized"] is False
    assert payload["scheduler_execution_authorized"] is False
    for c in payload["commands"]:
        assert c["found"] is False
