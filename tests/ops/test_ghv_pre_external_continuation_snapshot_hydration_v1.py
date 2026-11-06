"""Continuation snapshot hydration contracts (replay typing, not Product success)."""

from __future__ import annotations

import json
from dataclasses import replace
from decimal import Decimal
from pathlib import Path

import pytest

from src.governance.capital_risk_sizing_v1 import (
    CapitalRiskSizingDecisionV1,
    CapitalRiskSizingOutcome,
    EnvelopeStatus,
    PreSizingRiskAssessmentV1,
    PreSizingRiskStatus,
    ScopeCapitalEnvelopeV1,
)
from src.ops.full_core_live_path_composition_root_v1.composition_root_v1 import (
    compose_core_live_execution_intent_v1,
)
from src.ops.full_core_live_path_composition_root_v1.constants_v1 import MODE_LIVE
from src.ops.full_core_live_path_composition_root_v1.ghv_pre_external_continuation_snapshot_hydration_v1 import (
    capital_risk_sizing_decision_from_snapshot_dict_v1,
    hydrate_continuation_critical_intermediate_v1,
)
from src.ops.full_core_live_path_composition_root_v1.ghv_pre_external_runtime_flight_recorder_v1 import (
    _jsonable,
    load_replay_from_continuation_snapshot_v1,
)
from src.ops.full_core_live_path_composition_root_v1.ghv_pre_external_continuation_harness_v1 import (
    run_ghv_pre_external_continuation_harness_v1,
)
from tests.ops.test_full_core_current_productive_enter_live_29p_join_v1 import EPOCH
from tests.ops.test_ghv_observe_shaped_venue_plan_object_identity_v1 import (
    _genuine_observe_shaped_s7_replay_v1,
)

REAL_SNAPSHOT = Path(
    "evidence/ops/combined_ghv_whole_cycle_canary_measurement_v1/20261002T074052Z/"
    "ghv_pre_external_continuation_snapshot_v1"
)


def _sample_blocked_sizing_dict() -> dict:
    return {
        "adapter_compatible": False,
        "authority_effect": "NONE",
        "canonical_position_sizing": None,
        "final_quantity": "0",
        "outcome": "BLOCKED",
        "post_sizing_risk": None,
        "pre_sizing_risk": {
            "candidate_quantity_upper_bound": "0.00279309536824239125",
            "capital_cap_quantity": "3.887397868117454766875434934",
            "decision_id": "decision-test",
            "exposure_cap_quantity": "3.887397868117454766875434934",
            "input_digest": "abc",
            "loss_budget_quantity": "0.00279309536824239125",
            "maximum_loss_budget": "2.234476294593913",
            "reason_codes": [],
            "reference_price": "0.05748",
            "side": "SHORT",
            "status": "PASS",
            "stop_or_risk_distance": "80.00000",
        },
        "quantity_provenance": None,
        "reason_codes": ["ROUNDED_DOWN", "BELOW_MIN_QUANTITY"],
        "runtime_effect": "NONE",
        "scope_capital_envelope": {
            "already_committed_capital": "0",
            "available_capital": "2.234476294593913",
            "daily_loss_state": {"consumed_usd": "0", "limit_usd": "1", "remaining_usd": "1"},
            "decision_id": "decision-test",
            "input_digest": "abc",
            "instrument_id": "okx_eea:linear_perpetual:SAND:USDT:USDT:sand-usdt-swap",
            "per_order_cap": "2.234476294593913",
            "policy_version": "capital_risk_sizing_policy_v1",
            "position_slot_state": {"max_positions": "1", "open_count": "0"},
            "reason_codes": [],
            "remaining_capital": "2.234476294593913",
            "status": "PASS",
            "total_capital_limit": "2.234476294593913",
        },
        "selected_side": "SHORT",
    }


def test_capital_risk_sizing_roundtrip_jsonable() -> None:
    raw = _sample_blocked_sizing_dict()
    restored = capital_risk_sizing_decision_from_snapshot_dict_v1(raw)
    assert isinstance(restored.outcome, CapitalRiskSizingOutcome)
    assert restored.outcome is CapitalRiskSizingOutcome.BLOCKED
    assert restored.final_quantity == Decimal("0")
    assert restored.pre_sizing_risk.status is PreSizingRiskStatus.PASS
    assert restored.scope_capital_envelope.status is EnvelopeStatus.PASS
    reserialized = _jsonable(restored)
    again = capital_risk_sizing_decision_from_snapshot_dict_v1(reserialized)
    assert again.outcome is restored.outcome
    assert again.reason_codes == restored.reason_codes


def test_hydration_allows_compose_to_read_sizing_outcome(tmp_path: Path) -> None:
    pairs, observe_replay, _ = _genuine_observe_shaped_s7_replay_v1(tmp_path)
    bound = pairs["LANE_1"][1]
    assert observe_replay.intermediate is not None
    sizing = CapitalRiskSizingDecisionV1(
        outcome=CapitalRiskSizingOutcome.BLOCKED,
        final_quantity=Decimal("0"),
        selected_side="SHORT",
        scope_capital_envelope=ScopeCapitalEnvelopeV1(
            instrument_id=str(bound.instrument_id),
            decision_id="d1",
            policy_version="capital_risk_sizing_policy_v1",
            total_capital_limit=Decimal("1"),
            available_capital=Decimal("1"),
            already_committed_capital=Decimal("0"),
            remaining_capital=Decimal("1"),
            per_order_cap=Decimal("1"),
            daily_loss_state={"remaining_usd": "1"},
            position_slot_state={"open_count": "0"},
            status=EnvelopeStatus.PASS,
            reason_codes=(),
            input_digest="dig",
        ),
        pre_sizing_risk=PreSizingRiskAssessmentV1(
            decision_id="d1",
            side="SHORT",
            reference_price=Decimal("1"),
            stop_or_risk_distance=Decimal("1"),
            maximum_loss_budget=Decimal("1"),
            capital_cap_quantity=Decimal("1"),
            loss_budget_quantity=Decimal("1"),
            exposure_cap_quantity=Decimal("1"),
            candidate_quantity_upper_bound=Decimal("1"),
            status=PreSizingRiskStatus.PASS,
            reason_codes=(),
            input_digest="dig",
        ),
        canonical_position_sizing=None,
        post_sizing_risk=None,
        quantity_provenance=None,
        reason_codes=("BELOW_MIN_QUANTITY",),
    )
    from dataclasses import replace as dc_replace

    evidence = dc_replace(
        observe_replay.evidence,
        decision_outcome="enter_short",
        selected_side="short",
    )
    inter = replace(observe_replay.intermediate, capital_risk_sizing_decision=sizing)
    replay = replace(observe_replay, evidence=evidence, intermediate=inter)
    from trading.master_v2.integrated_offline_trading_logic_replay_v1 import (
        IntegratedOfflineReplayIntermediateV1,
    )

    inter_raw = _jsonable(inter)
    assert isinstance(inter_raw["capital_risk_sizing_decision"], dict)
    naive = IntegratedOfflineReplayIntermediateV1(**inter_raw)
    hydrated = hydrate_continuation_critical_intermediate_v1(naive, inter_raw)
    replay_h = replace(replay, intermediate=hydrated)
    status, reasons, _ = compose_core_live_execution_intent_v1(
        replay=replay_h,
        bound_instrument=bound,
        mode=MODE_LIVE,
        composed_epoch=EPOCH,
    )
    assert status.name == "DENY"
    assert any("SIZING_OUTCOME" in r or "29P_DENY" in r for r in reasons)


@pytest.mark.skipif(not REAL_SNAPSHOT.is_dir(), reason="real measurement snapshot absent")
def test_real_combined_measurement_snapshot_load_and_harness() -> None:
    _manifest, replay = load_replay_from_continuation_snapshot_v1(REAL_SNAPSHOT)
    assert replay.intermediate is not None
    sizing = replay.intermediate.capital_risk_sizing_decision
    assert sizing is None or hasattr(sizing, "outcome")
    if sizing is not None:
        assert isinstance(sizing.outcome, CapitalRiskSizingOutcome)
    evidence_root = REAL_SNAPSHOT.parent
    report = run_ghv_pre_external_continuation_harness_v1(
        snapshot_root=REAL_SNAPSHOT,
        output_dir=evidence_root,
    )
    assert report["NO_FAIL_FAST_OBSERVATION"] is True
    assert len(report["stages"]) >= 5
    assert (evidence_root / "ghv_pre_external_runtime_state_graph_v1.json").is_file()
    assert (evidence_root / "ghv_system_wide_canary_events_v1.jsonl").is_file()
