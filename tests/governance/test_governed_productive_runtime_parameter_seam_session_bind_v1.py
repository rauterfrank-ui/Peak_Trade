"""Tests for governed productive runtime parameter seam session bind v1."""

from __future__ import annotations

from pathlib import Path

from src.governance.governed_productive_runtime_parameter_seam_join_v1 import (
    resolve_governed_runtime_seam_for_presence_gate_v1,
)
from src.governance.governed_productive_runtime_parameter_seam_session_bind_v1 import (
    STATUS_BOUND,
    STATUS_DENIED,
    bind_governed_authorized_productive_parameter_seam_to_hardened_bridge_session_v1,
    optimization_can_bind_session_seam_directly_v1,
    read_session_bound_seam_for_runtime_transport_v1,
)
from src.ops.wallclock_full_canonical_decision_to_simulated_economics_runtime_bridge_hardening_v2.hardening_cycle_bridge_v2 import (
    HardenedBridgeSessionStateV2,
    run_hardened_bridge_cycle_v2,
)
from src.trading.master_v2.double_play_runtime_typed_volatility_presence_gate_v1 import (
    evaluate_double_play_runtime_typed_volatility_presence_gate_v1,
)
from src.trading.master_v2.canonical_volatility_numeric_max_age_policy_contract_and_non_enforcing_telemetry_v1 import (
    ENFORCEMENT_ENABLED,
    NUMERIC_MAX_AGE_DECIDED,
    THRESHOLD_STATUS_RATIFIED_NUMERIC,
    THRESHOLD_STATUS_UNRESOLVED,
)
from tests.governance.test_governed_productive_runtime_parameter_seam_join_v1 import (
    _valid_seam_record,
)
from tests.trading.master_v2.test_canonical_volatility_productive_runtime_cmc_typed_binding_v1 import (
    T0,
    _price_at,
    _sample,
)
from tests.trading.master_v2.test_double_play_runtime_typed_volatility_presence_gate_v1 import (
    _context,
    _valid_estimate,
)
from trading.master_v2.canonical_market_context_v1 import with_computed_input_digest
from trading.master_v2.canonical_volatility_binding_and_provenance_transport_v1 import (
    bind_typed_canonical_volatility_estimate_into_market_context_v1,
    evaluate_typed_volatility_binding_eligibility_v1,
)


def test_valid_seam_session_bind_reaches_bridge_presence_gate(tmp_path: Path) -> None:
    seam_record = _valid_seam_record(tmp_path)
    state = HardenedBridgeSessionStateV2()
    state.typed_volatility_persistence_path = tmp_path / "hist.json"
    state, bind = bind_governed_authorized_productive_parameter_seam_to_hardened_bridge_session_v1(
        state,
        seam_record,
        session_id="seam-session-bind-e2e",
    )
    assert bind.bind_status == STATUS_BOUND
    assert state.governed_authorized_productive_parameter_seam_record is not None
    assert read_session_bound_seam_for_runtime_transport_v1(state) is not None

    transport = resolve_governed_runtime_seam_for_presence_gate_v1(
        state.governed_authorized_productive_parameter_seam_record
    )
    estimate = _valid_estimate()
    ctx = bind_typed_canonical_volatility_estimate_into_market_context_v1(
        with_computed_input_digest(_context(volatility_estimate=0.0)),
        estimate,
    )
    elig = evaluate_typed_volatility_binding_eligibility_v1(ctx)
    gate = evaluate_double_play_runtime_typed_volatility_presence_gate_v1(
        ctx,
        eligibility=elig,
        authorized_productive_parameter_seam=transport.seam_for_consumer,
    )
    assert gate.max_age_policy_evidence is not None
    assert gate.max_age_policy_evidence.threshold_status == THRESHOLD_STATUS_UNRESOLVED
    assert gate.max_age_policy_evidence.enforcement_applied is False
    assert (
        state.governed_authorized_productive_parameter_seam_record["seam_digest"]
        == bind.seam_digest
    )


def test_bridge_cycle_research_join_epistemic_lane_with_ratified_seam_telemetry(
    tmp_path: Path,
) -> None:
    """Gate stays UNRESOLVED without threshold auth; research join stays UNRESOLVED."""
    seam_record = _valid_seam_record(tmp_path)
    state = HardenedBridgeSessionStateV2()
    state.typed_volatility_persistence_path = tmp_path / "hist.json"
    state, _ = bind_governed_authorized_productive_parameter_seam_to_hardened_bridge_session_v1(
        state,
        seam_record,
        session_id="seam-research-join-reconciled",
    )
    last = None
    for i in range(61):
        last = run_hardened_bridge_cycle_v2(
            state,
            mid_price=_price_at(i),
            event_ts_unix=T0 + float(i),
            session_id="seam-research-join-reconciled",
            finalized_pt1m_mark_sample=_sample(i),
        )
    assert last is not None
    gate = last["double_play_typed_volatility_presence_gate"]
    assert gate["max_age_policy_evidence"]["threshold_status"] == THRESHOLD_STATUS_UNRESOLVED
    join = last["canonical_volatility_max_age_research_evidence_join"]
    assert join["threshold_status"] == THRESHOLD_STATUS_UNRESOLVED
    assert join["enforcement_applied"] is False


def test_missing_seam_fail_closed() -> None:
    state = HardenedBridgeSessionStateV2()
    _, bind = bind_governed_authorized_productive_parameter_seam_to_hardened_bridge_session_v1(
        state,
        None,
    )
    assert bind.bind_status == STATUS_DENIED
    assert state.governed_authorized_productive_parameter_seam_record is None


def test_stale_digest_rejected(tmp_path: Path) -> None:
    seam_record = _valid_seam_record(tmp_path)
    seam_record["seam_digest"] = "0" * 64
    state = HardenedBridgeSessionStateV2()
    _, bind = bind_governed_authorized_productive_parameter_seam_to_hardened_bridge_session_v1(
        state,
        seam_record,
    )
    assert bind.bind_status == STATUS_DENIED
    assert "SEAM_DIGEST_INVALID" in bind.reason_codes


def test_rebind_different_seam_forbidden(tmp_path: Path) -> None:
    first = _valid_seam_record(tmp_path)
    second = dict(first)
    second["numeric_max_age_seconds"] = float(first["numeric_max_age_seconds"]) + 1.0
    second["authorized_candidate_max_age_seconds"] = second["numeric_max_age_seconds"]
    from src.meta.learning_loop.contract_safety_v1 import compute_content_sha256

    body = {k: v for k, v in second.items() if k != "seam_digest"}
    second["seam_digest"] = compute_content_sha256(body)

    state = HardenedBridgeSessionStateV2()
    state, _ = bind_governed_authorized_productive_parameter_seam_to_hardened_bridge_session_v1(
        state,
        first,
        session_id="s1",
    )
    _, rebind = bind_governed_authorized_productive_parameter_seam_to_hardened_bridge_session_v1(
        state,
        second,
        session_id="s1",
    )
    assert rebind.bind_status == STATUS_DENIED
    assert "SESSION_SEAM_REBIND_FORBIDDEN" in rebind.reason_codes


def test_idempotent_rebind_same_digest(tmp_path: Path) -> None:
    seam_record = _valid_seam_record(tmp_path)
    state = HardenedBridgeSessionStateV2()
    state, first = bind_governed_authorized_productive_parameter_seam_to_hardened_bridge_session_v1(
        state,
        seam_record,
        session_id="s-idem",
    )
    state, second = (
        bind_governed_authorized_productive_parameter_seam_to_hardened_bridge_session_v1(
            state,
            seam_record,
            session_id="s-idem",
        )
    )
    assert first.seam_digest == second.seam_digest
    assert "SESSION_SEAM_ALREADY_BOUND_IDEMPOTENT" in second.reason_codes


def test_session_id_mismatch_rejected(tmp_path: Path) -> None:
    seam_record = _valid_seam_record(tmp_path)
    state = HardenedBridgeSessionStateV2()
    state.session_id = "existing-session"
    _, bind = bind_governed_authorized_productive_parameter_seam_to_hardened_bridge_session_v1(
        state,
        seam_record,
        session_id="other-session",
    )
    assert bind.bind_status == STATUS_DENIED
    assert "SESSION_ID_MISMATCH" in bind.reason_codes


def test_bridge_without_bind_stays_unresolved_presence_age(tmp_path: Path) -> None:
    state = HardenedBridgeSessionStateV2()
    state.typed_volatility_persistence_path = tmp_path / "hist2.json"
    last = run_hardened_bridge_cycle_v2(
        state,
        mid_price=_price_at(0),
        event_ts_unix=T0,
        session_id="no-seam",
        finalized_pt1m_mark_sample=_sample(0),
    )
    gate = last["double_play_typed_volatility_presence_gate"]
    assert gate["max_age_policy_evidence"]["threshold_status"] == THRESHOLD_STATUS_UNRESOLVED


def test_optimization_cannot_bind_session_seam_directly() -> None:
    assert optimization_can_bind_session_seam_directly_v1() is False


def test_authority_invariants() -> None:
    assert NUMERIC_MAX_AGE_DECIDED is False
    assert ENFORCEMENT_ENABLED is False
