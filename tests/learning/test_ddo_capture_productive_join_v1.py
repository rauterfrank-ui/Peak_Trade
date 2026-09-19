"""WP_DDO_CAPTURE_PRODUCTIVE_JOIN_TO_NEXT_HARD_BLOCKER_V1 capture/host join tests."""

from __future__ import annotations

import ast
from pathlib import Path
from typing import Any

import pytest

from src.governance.live_mode_gate import ExecutionEnvironment
from src.learning.deterministic_decision_outcome_v0.authority_v0 import (
    LEARNING_PRODUCTIVE_AUTHORITY,
    SECOND_EXECUTION_AUTHORITY_CREATED,
    SECOND_TRADING_AUTHORITY_CREATED,
)
from src.learning.deterministic_decision_outcome_v0.capture_v0 import (
    BLOCKED_CAPTURE_SEAMS_V0,
    IMPLEMENTED_CAPTURE_SEAMS_V0,
    SEAM_REAL_OUTCOME_HORIZON,
    DdoCaptureBindingV0,
    bind_capture_session_v0,
    observe_producer_result_v0,
    reset_capture_session_v0,
)
from src.learning.deterministic_decision_outcome_v0.decision_event_v0 import (
    build_decision_event_v0,
)
from src.learning.deterministic_decision_outcome_v0.enums_v0 import UNKNOWN
from src.learning.deterministic_decision_outcome_v0.errors_v0 import DdoValidationError
from src.learning.deterministic_decision_outcome_v0.evaluation_engine_v0 import (
    EVALUATION_RUNTIME_WIRING,
    evaluate_offline_bundle_v0,
)
from src.learning.deterministic_decision_outcome_v0.ledger_v0 import AppendOnlyDdoLedgerV0
from src.learning.deterministic_decision_outcome_v0.real_outcome_horizon_contracts_v1 import (
    REAL_OUTCOME_HORIZON_ENGINE_WIRED,
)
from src.learning.deterministic_decision_outcome_v0.real_outcome_horizon_productive_host_v1 import (
    EXTERNAL_EFFECT_AUTHORIZED,
    produce_real_outcome_horizon_evaluation_observation_v1,
)
from src.ops.capability_11_2_credential_authorization_and_account_identity_boundary_v1.account_identity_boundary_v1 import (
    build_account_identity_record_v1,
)
from src.ops.wallclock_full_canonical_decision_to_simulated_economics_runtime_bridge_v1.decision_economics_cycle_bridge_v1 import (
    run_bridge_cycles_from_mids_v1,
)
from src.ops.wallclock_full_canonical_decision_to_simulated_economics_runtime_bridge_v1.ddo_n_bars_horizon_observation_host_binding_v1 import (
    invoke_productive_n_bars_horizon_observation_v1,
)
from tests.learning.test_ddo_o4_n_bars_productive_chain_v1 import (
    _decision,
    _identity,
    _snapshot,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
HOST_BINDING = (
    REPO_ROOT
    / "src/ops/wallclock_full_canonical_decision_to_simulated_economics_runtime_bridge_v1"
    / "ddo_n_bars_horizon_observation_host_binding_v1.py"
)
BRIDGE = (
    REPO_ROOT
    / "src/ops/wallclock_full_canonical_decision_to_simulated_economics_runtime_bridge_v1"
    / "decision_economics_cycle_bridge_v1.py"
)


def _session(tmp_path: Path) -> DdoCaptureBindingV0:
    return DdoCaptureBindingV0(enabled=True, ledger_path=tmp_path / "ddo.jsonl")


def test_capture_unlock_and_wired_flags() -> None:
    assert REAL_OUTCOME_HORIZON_ENGINE_WIRED is True
    assert SEAM_REAL_OUTCOME_HORIZON in IMPLEMENTED_CAPTURE_SEAMS_V0
    assert SEAM_REAL_OUTCOME_HORIZON not in BLOCKED_CAPTURE_SEAMS_V0
    assert EXTERNAL_EFFECT_AUTHORIZED is False


def test_productive_real_happy_path_single_capture(tmp_path: Path) -> None:
    decision = build_decision_event_v0(_decision())
    snap = _snapshot()
    binding = _session(tmp_path)
    capture_session_handle = bind_capture_session_v0(binding)
    try:
        first = produce_real_outcome_horizon_evaluation_observation_v1(
            decision, snap, economic_score="LABEL_1"
        )
        second = produce_real_outcome_horizon_evaluation_observation_v1(
            decision, snap, economic_score="LABEL_1"
        )
    finally:
        reset_capture_session_v0(capture_session_handle)
    assert first == second
    assert first["ok"] is True
    horizon_records = [
        r
        for r in binding.captured_records
        if r.get("schema_name") == "real_outcome_horizon_observation_capture"
    ]
    decision_records = [
        r for r in binding.captured_records if r.get("schema_name") == "decision_event"
    ]
    assert len(horizon_records) == 1
    assert len(decision_records) == 1
    obs = first["evaluation_observation"]
    bundle = evaluate_offline_bundle_v0(decision, obs, identity=_identity())
    assert bundle["outcome_record"]["actual_outcome_ref"] == obs["actual_outcome_ref"]
    assert obs["actual_outcome_ref"].startswith("ddo.outcome.")
    assert bundle["hindsight_leakage"] is False


def test_missing_upstream_evidence_skips_fail_closed() -> None:
    class _State:
        last_ddo_n_bars_horizon_observation = None

    state = _State()
    out = invoke_productive_n_bars_horizon_observation_v1(
        state,
        decision_event=None,
        o4_snapshot=None,
        event_ts_unix=1_700_000_000.0,
    )
    assert out["skipped"] is True
    assert out["reason"] == "HORIZON_UPSTREAM_EVIDENCE_MISSING"


def test_gap_horizon_fail_closed_unknown_outcome(tmp_path: Path) -> None:
    decision = build_decision_event_v0(_decision())
    bars = [
        {
            "canonical_instrument_id": "ETH-USD-SWAP-CANON",
            "venue_instrument_id": "ETH-USD-SWAP",
            "venue": "okx_eea",
            "interval": "PT1H",
            "bar_open_time": 1_756_732_800.0,
            "bar_close_time": 1_756_736_400.0,
            "finalization_state": "FINALIZED",
            "quality_state": "FINALIZED",
            "last_observation_identity": {
                "venue": "okx_eea",
                "canonical_instrument_id": "ETH-USD-SWAP-CANON",
                "venue_instrument_id": "ETH-USD-SWAP",
                "venue_event_time": 1_756_736_400.0,
                "mark_price": 100.0,
            },
            "session_id": "o4-session-1",
            "repository_sha": "abc12345deadbeef",
            "config_digest": "cfgdigest001",
            "close": 100.0,
            "revision": 0,
        },
        {
            "canonical_instrument_id": "ETH-USD-SWAP-CANON",
            "venue_instrument_id": "ETH-USD-SWAP",
            "venue": "okx_eea",
            "interval": "PT1H",
            "bar_open_time": 1_756_740_000.0,
            "bar_close_time": 1_756_743_600.0,
            "finalization_state": "FINALIZED",
            "quality_state": "FINALIZED",
            "last_observation_identity": {
                "venue": "okx_eea",
                "canonical_instrument_id": "ETH-USD-SWAP-CANON",
                "venue_instrument_id": "ETH-USD-SWAP",
                "venue_event_time": 1_756_743_600.0,
                "mark_price": 101.0,
            },
            "session_id": "o4-session-1",
            "repository_sha": "abc12345deadbeef",
            "config_digest": "cfgdigest001",
            "close": 101.0,
            "revision": 0,
        },
    ]
    snap = _snapshot(o4_bars=bars)
    binding = _session(tmp_path)
    capture_session_handle = bind_capture_session_v0(binding)
    try:
        result = produce_real_outcome_horizon_evaluation_observation_v1(
            decision, snap, outcome_scalar_kind="LOG_RETURN"
        )
    finally:
        reset_capture_session_v0(capture_session_handle)
    assert result["ok"] is False
    obs = result["evaluation_observation"]
    bundle = evaluate_offline_bundle_v0(decision, obs, identity=_identity())
    assert bundle["outcome_record"]["actual_outcome_ref"] == UNKNOWN


def test_wrong_seam_rejected_for_horizon_payload(tmp_path: Path) -> None:
    binding = _session(tmp_path)
    with pytest.raises(KeyError):
        observe_producer_result_v0(
            binding,
            seam_id="real_outcome_horizon_engine.invalid",
            result={"ok": True, "evaluation_observation": {}},
            event_time_utc="2026-09-01T14:00:00Z",
        )


def test_horizon_capture_requires_evaluation_observation(tmp_path: Path) -> None:
    binding = _session(tmp_path)
    with pytest.raises(ValueError, match="HORIZON_EVALUATION_OBSERVATION_MISSING"):
        observe_producer_result_v0(
            binding,
            seam_id=SEAM_REAL_OUTCOME_HORIZON,
            result={"ok": True, "hard_stop": False},
            event_time_utc="2026-09-01T14:00:00Z",
        )


def test_bridge_single_host_join_site() -> None:
    source = BRIDGE.read_text(encoding="utf-8")
    assert source.count("invoke_productive_n_bars_horizon_observation_v1(") == 1
    binding_source = HOST_BINDING.read_text(encoding="utf-8")
    assert "produce_real_outcome_horizon_evaluation_observation_v1" in binding_source
    tree = ast.parse(binding_source)
    decorator_hits = 0
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name.startswith("invoke_productive"):
            decorator_hits += 1
    assert decorator_hits == 1


def test_bridge_productive_chain_reaches_horizon_capture(tmp_path: Path) -> None:
    decision = build_decision_event_v0(_decision())
    account = build_account_identity_record_v1(
        account_identity="acct-horizon-join",
        venue="OKX",
        credential_ref_id="cred-horizon-join",
        account_scope="trading-only",
        expected_uid="acct-horizon-join",
    )
    state, _cycles = run_bridge_cycles_from_mids_v1(
        [3500.0],
        session_id="horizon-join-session",
        require_selection_binding=False,
        ddo_durable_evidence_runtime_state_root=tmp_path,
        ddo_evidence_environment=ExecutionEnvironment.DEV,
        ddo_account_identity_record=account,
        ddo_n_bars_horizon_decision_event=decision,
        ddo_o4_n_bars_bar_evidence_snapshot=_snapshot(),
        ddo_n_bars_economic_score="LABEL_BRIDGE",
    )
    horizon = state.last_ddo_n_bars_horizon_observation
    assert horizon is not None
    assert horizon.get("skipped") is not True
    assert horizon["ok"] is True
    assert horizon["external_effect_authorized"] is False
    ledger_path = state.ddo_capture_binding.ledger_path
    assert ledger_path is not None
    records = AppendOnlyDdoLedgerV0(ledger_path).read_all()
    horizon_caps = [
        r for r in records if r.get("schema_name") == "real_outcome_horizon_observation_capture"
    ]
    assert len(horizon_caps) == 1


def test_no_trading_authority_escalation_markers() -> None:
    assert LEARNING_PRODUCTIVE_AUTHORITY == "NONE"
    assert SECOND_TRADING_AUTHORITY_CREATED is False
    assert SECOND_EXECUTION_AUTHORITY_CREATED is False


def test_tampered_decision_ref_rejected() -> None:
    decision = build_decision_event_v0(_decision(record_id="dec-other"))
    with pytest.raises(DdoValidationError, match="DECISION_EVENT_REF_MISMATCH"):
        produce_real_outcome_horizon_evaluation_observation_v1(decision, _snapshot())
