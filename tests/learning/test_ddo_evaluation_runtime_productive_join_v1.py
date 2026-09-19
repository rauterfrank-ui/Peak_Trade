"""WP_DDO_EVALUATION_RUNTIME_TO_NEXT_HARD_BLOCKER_V1 runtime join tests."""

from __future__ import annotations

import ast
from pathlib import Path
from typing import Any

import pytest

from src.governance.live_mode_gate import ExecutionEnvironment
from src.learning.deterministic_decision_outcome_v0.authority_v0 import (
    LEARNING_PRODUCTIVE_AUTHORITY,
    PROMOTION_AUTHORITY_ACTIVATION,
    SECOND_EXECUTION_AUTHORITY_CREATED,
    SECOND_TRADING_AUTHORITY_CREATED,
    EVALUATION_RUNTIME_WIRING,
)
from src.learning.deterministic_decision_outcome_v0.capture_v0 import (
    bind_capture_session_v0,
    reset_capture_session_v0,
    DdoCaptureBindingV0,
)
from src.learning.deterministic_decision_outcome_v0.decision_event_v0 import (
    build_decision_event_v0,
)
from src.learning.deterministic_decision_outcome_v0.enums_v0 import UNKNOWN
from src.learning.deterministic_decision_outcome_v0.errors_v0 import DdoValidationError
from src.learning.deterministic_decision_outcome_v0.evaluation_runtime_productive_host_v1 import (
    EXTERNAL_EFFECT_AUTHORIZED,
    produce_n_bars_evaluation_runtime_bundle_v1,
)
from src.learning.deterministic_decision_outcome_v0.real_outcome_horizon_productive_host_v1 import (
    produce_real_outcome_horizon_evaluation_observation_v1,
)
from src.ops.capability_11_2_credential_authorization_and_account_identity_boundary_v1.account_identity_boundary_v1 import (
    build_account_identity_record_v1,
)
from src.ops.wallclock_full_canonical_decision_to_simulated_economics_runtime_bridge_v1.decision_economics_cycle_bridge_v1 import (
    run_bridge_cycles_from_mids_v1,
)
from src.ops.wallclock_full_canonical_decision_to_simulated_economics_runtime_bridge_v1.ddo_n_bars_evaluation_runtime_host_binding_v1 import (
    invoke_productive_n_bars_evaluation_runtime_v1,
)
from tests.learning.test_ddo_o4_n_bars_productive_chain_v1 import (
    _decision,
    _identity,
    _snapshot,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
BRIDGE = (
    REPO_ROOT
    / "src/ops/wallclock_full_canonical_decision_to_simulated_economics_runtime_bridge_v1"
    / "decision_economics_cycle_bridge_v1.py"
)
EVAL_BINDING = (
    REPO_ROOT
    / "src/ops/wallclock_full_canonical_decision_to_simulated_economics_runtime_bridge_v1"
    / "ddo_n_bars_evaluation_runtime_host_binding_v1.py"
)


def _session(tmp_path: Path) -> DdoCaptureBindingV0:
    return DdoCaptureBindingV0(enabled=True, ledger_path=tmp_path / "ddo.jsonl")


def test_evaluation_runtime_wiring_unlocked() -> None:
    assert EVALUATION_RUNTIME_WIRING is True
    assert EXTERNAL_EFFECT_AUTHORIZED is False


def test_productive_runtime_real_path(tmp_path: Path) -> None:
    decision = build_decision_event_v0(_decision())
    snap = _snapshot()
    binding = _session(tmp_path)
    capture_session_handle = bind_capture_session_v0(binding)
    try:
        horizon = produce_real_outcome_horizon_evaluation_observation_v1(
            decision, snap, economic_score="LABEL_RT"
        )
        first = produce_n_bars_evaluation_runtime_bundle_v1(horizon, decision, identity=_identity())
        second = produce_n_bars_evaluation_runtime_bundle_v1(
            horizon, decision, identity=_identity()
        )
    finally:
        reset_capture_session_v0(capture_session_handle)
    assert horizon["ok"] is True
    assert first == second
    assert first["runtime_wiring"] is True
    assert first["actual_outcome_ref"] == horizon["evaluation_observation"]["actual_outcome_ref"]
    assert first["hindsight_leakage"] is False


def test_unknown_gap_horizon_fail_closed_runtime() -> None:
    from tests.learning.test_ddo_o4_n_bars_productive_chain_v1 import _o4_bar

    decision = build_decision_event_v0(_decision())
    bars = [
        _o4_bar(
            open_iso="2026-09-01T12:00:00Z", close_iso="2026-09-01T13:00:00Z", close_price=100.0
        ),
        _o4_bar(
            open_iso="2026-09-01T14:00:00Z", close_iso="2026-09-01T15:00:00Z", close_price=101.0
        ),
    ]
    snap = _snapshot(o4_bars=bars)
    horizon = produce_real_outcome_horizon_evaluation_observation_v1(
        decision, snap, outcome_scalar_kind="LOG_RETURN"
    )
    bundle = produce_n_bars_evaluation_runtime_bundle_v1(horizon, decision, identity=_identity())
    assert horizon["ok"] is False
    assert bundle["actual_outcome_ref"] == UNKNOWN


def test_tampered_decision_ref_rejected_at_runtime() -> None:
    decision = build_decision_event_v0(_decision())
    horizon = produce_real_outcome_horizon_evaluation_observation_v1(decision, _snapshot())
    bad_decision = build_decision_event_v0(_decision(record_id="dec-other"))
    with pytest.raises(DdoValidationError, match="EVALUATION_RUNTIME_DECISION_REF_MISMATCH"):
        produce_n_bars_evaluation_runtime_bundle_v1(horizon, bad_decision, identity=_identity())


def test_missing_horizon_observation_rejected() -> None:
    decision = build_decision_event_v0(_decision())
    with pytest.raises(DdoValidationError, match="EVALUATION_RUNTIME_HORIZON_OBSERVATION_MISSING"):
        produce_n_bars_evaluation_runtime_bundle_v1({"ok": True}, decision, identity=_identity())


def test_bridge_single_evaluation_join_site() -> None:
    bridge_source = BRIDGE.read_text(encoding="utf-8")
    assert bridge_source.count("invoke_productive_n_bars_evaluation_runtime_v1(") == 1
    binding_source = EVAL_BINDING.read_text(encoding="utf-8")
    assert binding_source.count("produce_n_bars_evaluation_runtime_bundle_v1(") == 1
    tree = ast.parse(binding_source)
    assert (
        sum(
            1
            for node in ast.walk(tree)
            if isinstance(node, ast.FunctionDef) and node.name.startswith("invoke_productive")
        )
        == 1
    )


def test_full_productive_in_process_chain(tmp_path: Path) -> None:
    decision = build_decision_event_v0(_decision())
    account = build_account_identity_record_v1(
        account_identity="acct-eval-runtime",
        venue="OKX",
        credential_ref_id="cred-eval-runtime",
        account_scope="trading-only",
        expected_uid="acct-eval-runtime",
    )
    state, _ = run_bridge_cycles_from_mids_v1(
        [3500.0],
        session_id="eval-runtime-session",
        require_selection_binding=False,
        ddo_durable_evidence_runtime_state_root=tmp_path,
        ddo_evidence_environment=ExecutionEnvironment.DEV,
        ddo_account_identity_record=account,
        ddo_n_bars_horizon_decision_event=decision,
        ddo_o4_n_bars_bar_evidence_snapshot=_snapshot(),
        ddo_n_bars_evaluation_identity=_identity(),
    )
    horizon = state.last_ddo_n_bars_horizon_observation
    runtime = state.last_ddo_n_bars_evaluation_runtime
    assert horizon is not None and horizon.get("ok") is True
    assert runtime is not None and runtime.get("ok") is True
    assert runtime["runtime_wiring"] is True
    assert runtime["external_effect_authorized"] is False
    assert runtime["actual_outcome_ref"] == horizon["evaluation_observation"]["actual_outcome_ref"]


def test_evaluation_skipped_when_horizon_upstream_missing() -> None:
    class _State:
        last_ddo_n_bars_evaluation_runtime = None

    out = invoke_productive_n_bars_evaluation_runtime_v1(
        _State(),
        decision_event=None,
        identity=None,
        horizon_result=None,
    )
    assert out["skipped"] is True


def test_no_authority_escalation() -> None:
    assert LEARNING_PRODUCTIVE_AUTHORITY == "NONE"
    assert PROMOTION_AUTHORITY_ACTIVATION is False
    assert SECOND_TRADING_AUTHORITY_CREATED is False
    assert SECOND_EXECUTION_AUTHORITY_CREATED is False
