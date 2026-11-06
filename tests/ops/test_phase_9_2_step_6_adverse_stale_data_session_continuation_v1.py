"""Tests for PHASE_9_2_STEP_6_ADVERSE_STALE_DATA_SESSION_CONTINUATION_V1."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from src.ops.integrated_paper_shadow_observation_wallclock_session_execution_v1.heartbeat_staleness_v1 import (
    StalenessTrackerV1,
)
from src.ops.integrated_paper_shadow_observation_wallclock_session_execution_v1.killstate_runtime_v1 import (
    KILLSTATE_TRIGGERS,
)
from src.ops.phase_9_2_step_6_adverse_stale_data_session_continuation_v1.constants_v1 import (
    ADVERSE_STALE_DATA_LADDER_STEP_CLOSED,
    CORE_LOGIC_CHANGE,
    DIRECT_FILL_INJECTION_ALLOWED,
    FORCED_INTENT_ALLOWED,
    NETWORK_SESSION_ALLOWED,
    NEXT_OPEN_PHASE_9_2_STEP,
    NO_PARALLEL_KILLSTATE_MODEL,
    NO_PARALLEL_STALENESS_MODEL,
    PHASE_9_2_STEP_6_STATUS,
    PRODUCTIVE_NETWORK_SESSION_EXECUTION_AUTHORIZED,
    TARGET_SESSION_ID,
)
from src.ops.phase_9_2_step_6_adverse_stale_data_session_continuation_v1.evidence_v1 import (
    materialize_capability_evidence_v1,
)
from src.ops.phase_9_2_step_6_adverse_stale_data_session_continuation_v1.fault_path_v1 import (
    prove_governed_adverse_stale_fault_path_offline_v1,
)
from src.ops.phase_9_2_step_6_adverse_stale_data_session_continuation_v1.governed_injected_stale_data_fault_v1 import (
    GovernedInjectedStaleDataControlV1,
    GovernedStaleDataFaultControlError,
    apply_stale_classification_cycle_v1,
    build_disabled_stale_data_fault_schedule_v1,
    build_receive_lag_schedule_v1,
)
from src.ops.phase_9_2_step_6_adverse_stale_data_session_continuation_v1.network_boundary_v1 import (
    prove_public_md_network_boundary_v1,
)
from src.ops.phase_9_2_step_6_adverse_stale_data_session_continuation_v1.parity_v1 import (
    assert_no_parallel_productive_authority_v1,
    prove_phase92_step6_adverse_stale_continuation_parity_v1,
)
from src.ops.phase_9_2_step_6_adverse_stale_data_session_continuation_v1.productive_executor_v1 import (
    exact_productive_caller_path_v1,
    evaluate_step6_binding_gate_v1,
    run_step6_productive_executor_wiring_v1,
)
from src.ops.phase_9_2_step_6_adverse_stale_data_session_continuation_v1.session_contract_v1 import (
    load_and_validate_session_contract_v1,
)
from src.ops.phase_9_2_step_6_adverse_stale_data_session_continuation_v1.session_evidence_schema_v1 import (
    build_session_evidence_template_v1,
)
from src.ops.phase_9_2_step_6_adverse_stale_data_session_continuation_v1.verifier_v1 import (
    verify_binding_manifest_v1,
    verify_productive_session_evidence_v1,
)
from src.ops.single_future_stateful_no_order_runtime_activation_v1.config_v1 import (
    load_activation_config_v1,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
CLI = REPO_ROOT / "scripts/ops/run_phase_9_2_step_6_adverse_stale_data_session_continuation_v1.py"


def _sha() -> str:
    return subprocess.check_output(
        ["git", "rev-parse", "HEAD"], cwd=str(REPO_ROOT), text=True
    ).strip()


def _cfg() -> str:
    return str(
        load_activation_config_v1(
            config_path=REPO_ROOT
            / "config/runtime/single_future_stateful_no_order_runtime_activation_v1.json"
        ).config_digest
    )


def test_parity_and_no_parallel_models() -> None:
    parity = prove_phase92_step6_adverse_stale_continuation_parity_v1()
    authority = assert_no_parallel_productive_authority_v1()
    assert parity["ok"] is True
    assert CORE_LOGIC_CHANGE is False
    assert NETWORK_SESSION_ALLOWED is False
    assert PRODUCTIVE_NETWORK_SESSION_EXECUTION_AUTHORIZED is False
    assert PHASE_9_2_STEP_6_STATUS == "OPEN"
    assert NEXT_OPEN_PHASE_9_2_STEP == "6_ADVERSE_STALE_DATA_SESSION"
    assert ADVERSE_STALE_DATA_LADDER_STEP_CLOSED is False
    assert NO_PARALLEL_STALENESS_MODEL is True
    assert NO_PARALLEL_KILLSTATE_MODEL is True
    assert authority["ok"] is True
    assert authority["parallel_productive_authority_detected"] is False


def test_session_contract_validation() -> None:
    contract = load_and_validate_session_contract_v1(repo_root=REPO_ROOT)
    assert contract["session_id"] == TARGET_SESSION_ID
    assert contract["session_ladder_step"] == "ADVERSE_STALE_DATA_SESSION"
    assert contract["network_session_authorized"] is False
    assert contract["fault_session_execution_authorized"] is False
    assert contract["fault_injection"]["fabricated_observation_allowed"] is False
    assert "RECEIVE_LAG" in contract["fault_injection"]["allowed_kinds"]


def test_stale_data_classifier_reuse() -> None:
    tracker = StalenessTrackerV1(max_stale_seconds=5.0, consecutive_stale_budget=3)
    status, kill = tracker.observe(receive_ts=0.0, wall_now=10.0, mono_ts=1.0)
    assert status in {"warn", "kill"}
    assert kill in {None, "STALE_DATA"}


def test_adverse_stale_killstate_path() -> None:
    proof = prove_governed_adverse_stale_fault_path_offline_v1()
    assert proof["ok"] is True
    assert proof["cases"]["stale_killstate_path"]["ok"] is True
    assert "STALE_DATA" in KILLSTATE_TRIGGERS


def test_stale_observation_does_not_advance_confirmation() -> None:
    tracker = StalenessTrackerV1(max_stale_seconds=5.0, consecutive_stale_budget=3)
    control = GovernedInjectedStaleDataControlV1(schedule=build_receive_lag_schedule_v1())
    wall = 1000.0
    receive = control.resolve_receive_ts_v1(wall_now=wall, natural_receive_ts=wall)
    result = apply_stale_classification_cycle_v1(
        tracker=tracker,
        receive_ts=receive,
        wall_now=wall,
        mono_ts=1.0,
        confirmation_advance_on_stale=False,
    )
    assert result["STALE_CONDITION_OBSERVED"] is True
    assert result["STALE_CONFIRMATION_ADVANCE"] is False
    assert result["confirmation_advance_delta"] == 0
    try:
        apply_stale_classification_cycle_v1(
            tracker=StalenessTrackerV1(max_stale_seconds=5.0, consecutive_stale_budget=3),
            receive_ts=0.0,
            wall_now=10.0,
            mono_ts=1.0,
            confirmation_advance_on_stale=True,
        )
        raise AssertionError("expected stale confirmation advance rejection")
    except GovernedStaleDataFaultControlError:
        pass


def test_duplicate_observation_does_not_advance_confirmation() -> None:
    cases = prove_governed_adverse_stale_fault_path_offline_v1()["cases"]
    dup = cases["duplicate_no_confirmation_advance"]
    assert dup["ok"] is True
    assert dup["DUPLICATE_CONFIRMATION_ADVANCE"] is False
    assert dup["confirmation_advance_count"] == dup["distinct_observation_count"]


def test_no_fabricated_observation() -> None:
    control = GovernedInjectedStaleDataControlV1(schedule=build_receive_lag_schedule_v1())
    control.resolve_receive_ts_v1(wall_now=50.0, natural_receive_ts=50.0)
    control.assert_no_decision_injection_v1()
    assert control.telemetry.fabricated_observation_count == 0
    assert FORCED_INTENT_ALLOWED is False
    assert DIRECT_FILL_INJECTION_ALLOWED is False


def test_bounded_retry_backoff_and_zero_interval_forbidden() -> None:
    cases = prove_governed_adverse_stale_fault_path_offline_v1()["cases"]
    pacing = cases["bounded_retry_backoff_no_zero_interval"]
    assert pacing["ok"] is True
    assert pacing["zero_rejected"] is True
    assert float(pacing["minimum_interval_seconds"]) > 0
    assert float(pacing["backoff_initial_seconds"]) > 0


def test_private_endpoint_and_credential_and_order_negatives() -> None:
    boundary = prove_public_md_network_boundary_v1()
    assert boundary["ok"] is True
    assert boundary["PRIVATE_ENDPOINT_REACHED"] is False
    assert boundary["EXCHANGE_CREDENTIAL_PATH_REACHED"] is False
    assert boundary["ORDER_SIDE_EFFECT_OCCURRED"] is False


def test_no_decision_fill_injection() -> None:
    cases = prove_governed_adverse_stale_fault_path_offline_v1()["cases"]
    assert cases["no_decision_fill_injection"]["ok"] is True
    disabled = GovernedInjectedStaleDataControlV1(
        schedule=build_disabled_stale_data_fault_schedule_v1()
    )
    assert disabled.schedule.enabled is False


def test_executor_wiring_and_exact_productive_caller() -> None:
    gate = evaluate_step6_binding_gate_v1(request_real_network=True, owner_go=True)
    assert gate["ok"] is False
    assert "REAL_NETWORK_SESSION_FORBIDDEN_IN_THIS_CAPABILITY" in gate["blockers"]

    result = run_step6_productive_executor_wiring_v1(
        repository_sha=_sha(),
        config_digest=_cfg(),
        request_real_network=False,
        owner_go=True,
    )
    assert result.ok is True
    assert result.network_session_started is False
    assert result.authorization_consumed is False
    assert result.confirm_token_consumed is False
    assert result.claims["RUNTIME_REACHABLE"] is True
    assert result.claims["PRODUCTIVE_CALLER_ADDED"] is True
    caller = exact_productive_caller_path_v1()
    assert any("run_phase_9_2_step_6" in p for p in caller)
    assert any("productive_executor_v1" in p for p in caller)
    assert any("StalenessTrackerV1" in p for p in caller)


def test_verifier_positive_and_negative_fixtures(tmp_path: Path) -> None:
    summary = materialize_capability_evidence_v1(
        repository_sha=_sha(),
        evidence_root=tmp_path,
        repo_root=REPO_ROOT,
    )
    assert summary["ok"] is True
    positive = json.loads(
        (tmp_path / "fixtures" / "productive_session_positive_fixture_v1.json").read_text(
            encoding="utf-8"
        )
    )
    negative = json.loads(
        (tmp_path / "fixtures" / "productive_session_negative_fixture_v1.json").read_text(
            encoding="utf-8"
        )
    )
    assert verify_productive_session_evidence_v1(positive)["ok"] is True
    assert verify_productive_session_evidence_v1(negative)["ok"] is False

    manifest = json.loads(
        (tmp_path / "adverse_stale_data_session_continuation_manifest_v1.json").read_text(
            encoding="utf-8"
        )
    )
    assert verify_binding_manifest_v1(manifest)["ok"] is True
    assert manifest["claims"]["PHASE_9_2_STEP_6_STATUS"] == "OPEN"


def test_session_evidence_template_schema() -> None:
    template = build_session_evidence_template_v1(repository_sha=_sha(), config_digest=_cfg())
    assert template["fabricated_observation_count"] == 0
    assert template["private_endpoint_reachable"] is False
    assert template["claims"]["ADVERSE_STALE_DATA_LADDER_STEP_CLOSED"] is False


def test_cli_preflight_refuses_real_network() -> None:
    proc = subprocess.run(
        [sys.executable, str(CLI), "preflight", "--request-real-network", "--json"],
        cwd=str(REPO_ROOT),
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == 2
    payload = json.loads(proc.stdout)
    assert payload["ok"] is False
    assert "REAL_NETWORK_SESSION_FORBIDDEN_IN_THIS_CAPABILITY_CLI" in payload["blockers"]


def test_cli_wire_executor_ok() -> None:
    proc = subprocess.run(
        [sys.executable, str(CLI), "wire-executor", "--json"],
        cwd=str(REPO_ROOT),
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == 0
    payload = json.loads(proc.stdout)
    assert payload["ok"] is True
    assert payload["network_session_started"] is False
