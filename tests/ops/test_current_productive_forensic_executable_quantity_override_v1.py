"""Forensic executable quantity override (default OFF). No POST."""

from __future__ import annotations

import json
from decimal import Decimal
from pathlib import Path

import pytest

from src.governance.capital_risk_sizing_v1 import (
    AUTHORITY_EFFECT_NONE,
    REASON_BELOW_MIN_QUANTITY,
    RUNTIME_EFFECT_NONE,
    CapitalRiskSizingDecisionV1,
    CapitalRiskSizingOutcome,
    EnvelopeStatus,
    InstrumentQuantityConstraintsV1,
    PreSizingRiskAssessmentV1,
    PreSizingRiskStatus,
    ScopeCapitalEnvelopeV1,
)
from src.ops.full_core_live_path_composition_root_v1.current_productive_forensic_executable_quantity_override_v1 import (
    PROVENANCE_CURRENT_DERIVED_MIN_VENUE,
    PROVENANCE_EXPLICIT_FORENSIC_INPUT,
    REASON_FORENSIC_EXECUTABLE_QUANTITY_OVERRIDE,
    active_forensic_executable_quantity_override_session_v1,
    bind_forensic_executable_quantity_override_session_v1,
    build_forensic_executable_quantity_override_session_v1,
    derive_forensic_executable_quantity_v1,
    forensic_override_guards_satisfied_v1,
    maybe_apply_forensic_executable_quantity_override_after_live_29p_v1,
    reset_forensic_executable_quantity_override_session_v1,
)
from src.ops.full_core_live_path_composition_root_v1.current_productive_synthetic_enter_forensic_v1 import (
    SyntheticEnterForensicSessionV1,
    bind_synthetic_enter_forensic_session_v1,
    reset_synthetic_enter_forensic_session_v1,
)
from src.ops.full_core_live_path_composition_root_v1.productive_golden_happy_vector_forensic_observability_v1 import (
    GoldenHappyVectorForensicObservabilitySessionV1,
    bind_golden_happy_vector_forensic_observability_session_v1,
    reset_golden_happy_vector_forensic_observability_session_v1,
)
from tests.ops.test_full_core_current_productive_enter_live_29p_join_v1 import (
    _enter_replay,
)
from tests.ops.test_full_core_current_productive_host_enter_29p_invalid_stop_price_repair_v1 import (
    _host_enter_cycle,
)


def _constraints(
    instrument_id: str = "okx_eea:linear_perpetual:GEN:USDT:USDT:gen-usdt-swap",
) -> InstrumentQuantityConstraintsV1:
    return InstrumentQuantityConstraintsV1(
        instrument_id=instrument_id,
        market_type="futures",
        contract_kind="LINEAR",
        contract_multiplier=Decimal("1"),
        lot_size=Decimal("0.01"),
        minimum_quantity=Decimal("0.01"),
        maximum_quantity=None,
        minimum_notional=Decimal("5"),
        tick_size=Decimal("0.01"),
        instrument_metadata_version="test_metadata_v1",
    )


def _blocked_decision(*, instrument_id: str) -> CapitalRiskSizingDecisionV1:
    pre = PreSizingRiskAssessmentV1(
        decision_id="decision-test",
        side="SHORT",
        reference_price=Decimal("100"),
        stop_or_risk_distance=Decimal("1"),
        maximum_loss_budget=Decimal("10"),
        capital_cap_quantity=Decimal("1"),
        loss_budget_quantity=Decimal("0.05"),
        exposure_cap_quantity=Decimal("1"),
        candidate_quantity_upper_bound=Decimal("0.05"),
        status=PreSizingRiskStatus.PASS,
        reason_codes=(),
        input_digest="digest",
    )
    envelope = ScopeCapitalEnvelopeV1(
        decision_id="decision-test",
        instrument_id=instrument_id,
        policy_version="capital_risk_sizing_policy_v1",
        total_capital_limit=Decimal("10"),
        per_order_cap=Decimal("10"),
        available_capital=Decimal("10"),
        remaining_capital=Decimal("10"),
        already_committed_capital=Decimal("0"),
        daily_loss_state={
            "consumed_usd": "0",
            "limit_usd": "10",
            "remaining_usd": "10",
        },
        position_slot_state={"max_positions": "1", "open_count": "0"},
        reason_codes=(),
        status=EnvelopeStatus.PASS,
        input_digest="digest",
    )
    return CapitalRiskSizingDecisionV1(
        outcome=CapitalRiskSizingOutcome.BLOCKED,
        final_quantity=Decimal("0"),
        selected_side="SHORT",
        scope_capital_envelope=envelope,
        pre_sizing_risk=pre,
        canonical_position_sizing=None,
        post_sizing_risk=None,
        quantity_provenance=None,
        reason_codes=(REASON_BELOW_MIN_QUANTITY,),
        authority_effect=AUTHORITY_EFFECT_NONE,
        runtime_effect=RUNTIME_EFFECT_NONE,
        adapter_compatible=False,
    )


def test_default_off_no_session_leaves_sizing_unchanged() -> None:
    assert active_forensic_executable_quantity_override_session_v1() is None
    _, cycle_b, _ = _host_enter_cycle()
    replay = _enter_replay(cycle_b)
    blocked = _blocked_decision(instrument_id=str(replay.evidence.instrument_id))
    out = maybe_apply_forensic_executable_quantity_override_after_live_29p_v1(
        rebound_replay=replay,
        sizing_decision=blocked,
        constraints=_constraints(str(replay.evidence.instrument_id)),
        live_ctx=object(),
        cycle_index=1,
    )
    assert out.override_used is False
    assert out.sizing_decision.outcome is CapitalRiskSizingOutcome.BLOCKED


def test_guard_rejects_override_without_synthetic_and_ghv_sessions(tmp_path: Path) -> None:
    session = build_forensic_executable_quantity_override_session_v1(
        enabled=True,
        explicit_forensic_quantity="0.01",
        product_evidence_root=tmp_path,
        continuous_run_id="run-guard",
        require_ghv_pre_external_runtime_flight_recorder_v1=False,
    )
    reset = bind_forensic_executable_quantity_override_session_v1(session)
    try:
        ok, reasons = forensic_override_guards_satisfied_v1(
            require_flight_recorder=False,
            ghv_pre_external_runtime_flight_recorder_enabled=False,
        )
        assert ok is False
        assert "SYNTHETIC_ENTER_FORENSIC_SESSION_REQUIRED" in reasons
        _, cycle_b, _ = _host_enter_cycle()
        replay = _enter_replay(cycle_b)
        blocked = _blocked_decision(instrument_id=str(replay.evidence.instrument_id))
        out = maybe_apply_forensic_executable_quantity_override_after_live_29p_v1(
            rebound_replay=replay,
            sizing_decision=blocked,
            constraints=_constraints(str(replay.evidence.instrument_id)),
            live_ctx=object(),
            cycle_index=1,
        )
        assert out.override_used is False
    finally:
        reset_forensic_executable_quantity_override_session_v1(reset)


def test_normal_executable_sizing_skips_override(tmp_path: Path) -> None:
    syn_reset = bind_synthetic_enter_forensic_session_v1(
        SyntheticEnterForensicSessionV1(
            enabled=True,
            synthetic_side="enter_short",
            inject_cycle_index=1,
            product_evidence_root=tmp_path,
            continuous_run_id="run-skip",
        )
    )
    ghv_reset = bind_golden_happy_vector_forensic_observability_session_v1(
        GoldenHappyVectorForensicObservabilitySessionV1(
            enabled=True,
            product_evidence_root=tmp_path,
            run_id="run-skip",
            continuous_run_id="run-skip",
            repository_sha="abc",
        )
    )
    fq_reset = bind_forensic_executable_quantity_override_session_v1(
        build_forensic_executable_quantity_override_session_v1(
            enabled=True,
            explicit_forensic_quantity=None,
            product_evidence_root=tmp_path,
            continuous_run_id="run-skip",
            require_ghv_pre_external_runtime_flight_recorder_v1=False,
        )
    )
    try:
        _, cycle_b, _ = _host_enter_cycle()
        replay = _enter_replay(cycle_b)
        blocked = _blocked_decision(instrument_id=str(replay.evidence.instrument_id))
        pass_decision = CapitalRiskSizingDecisionV1(
            outcome=CapitalRiskSizingOutcome.PASS,
            final_quantity=Decimal("0.04"),
            selected_side=blocked.selected_side,
            scope_capital_envelope=blocked.scope_capital_envelope,
            pre_sizing_risk=blocked.pre_sizing_risk,
            canonical_position_sizing=None,
            post_sizing_risk=None,
            quantity_provenance=None,
            reason_codes=("PASS",),
            authority_effect=AUTHORITY_EFFECT_NONE,
            runtime_effect=RUNTIME_EFFECT_NONE,
            adapter_compatible=True,
        )
        out = maybe_apply_forensic_executable_quantity_override_after_live_29p_v1(
            rebound_replay=replay,
            sizing_decision=pass_decision,
            constraints=_constraints(str(replay.evidence.instrument_id)),
            live_ctx=object(),
            cycle_index=1,
        )
        assert out.override_used is False
        summary = json.loads(
            (tmp_path / "forensic_executable_quantity_override_summary_v1.json").read_text()
        )
        assert summary["FORENSIC_EXECUTABLE_QUANTITY_OVERRIDE_USED"] is False
    finally:
        reset_forensic_executable_quantity_override_session_v1(fq_reset)
        reset_golden_happy_vector_forensic_observability_session_v1(ghv_reset)
        reset_synthetic_enter_forensic_session_v1(syn_reset)


def test_blocked_sizing_applies_explicit_forensic_quantity_downstream(tmp_path: Path) -> None:
    syn_reset = bind_synthetic_enter_forensic_session_v1(
        SyntheticEnterForensicSessionV1(
            enabled=True,
            synthetic_side="enter_short",
            inject_cycle_index=1,
            product_evidence_root=tmp_path,
            continuous_run_id="run-apply",
        )
    )
    ghv_reset = bind_golden_happy_vector_forensic_observability_session_v1(
        GoldenHappyVectorForensicObservabilitySessionV1(
            enabled=True,
            product_evidence_root=tmp_path,
            run_id="run-apply",
            continuous_run_id="run-apply",
            repository_sha="abc",
        )
    )
    fq_reset = bind_forensic_executable_quantity_override_session_v1(
        build_forensic_executable_quantity_override_session_v1(
            enabled=True,
            explicit_forensic_quantity="0.05",
            product_evidence_root=tmp_path,
            continuous_run_id="run-apply",
            require_ghv_pre_external_runtime_flight_recorder_v1=False,
        )
    )
    try:
        from src.ops.full_core_live_path_composition_root_v1.current_productive_mv2_capital_context_rebind_v1 import (
            build_current_productive_live_account_capital_context_v1,
        )

        _, cycle_b, _ = _host_enter_cycle()
        replay = _enter_replay(cycle_b)
        constraints = _constraints(str(replay.evidence.instrument_id))
        live_ctx = build_current_productive_live_account_capital_context_v1(
            instrument_id=str(replay.evidence.instrument_id),
            typed_account_equity=Decimal("1000"),
            reference_price=Decimal("100"),
            protective_stop_price=Decimal("99"),
            instrument_constraints=constraints,
        )
        blocked = _blocked_decision(instrument_id=str(replay.evidence.instrument_id))
        out = maybe_apply_forensic_executable_quantity_override_after_live_29p_v1(
            rebound_replay=replay,
            sizing_decision=blocked,
            constraints=constraints,
            live_ctx=live_ctx,
            cycle_index=1,
        )
        assert out.override_used is True
        assert out.forensic_quantity == Decimal("0.05")
        assert out.sizing_decision.outcome is CapitalRiskSizingOutcome.PASS
        assert out.sizing_decision.final_quantity == Decimal("0.05")
        assert REASON_FORENSIC_EXECUTABLE_QUANTITY_OVERRIDE in out.sizing_decision.reason_codes
        summary = json.loads(
            (tmp_path / "forensic_executable_quantity_override_summary_v1.json").read_text()
        )
        assert summary["REAL_SIZING_OUTCOME_BEFORE_OVERRIDE"] == "BLOCKED"
        assert summary["REAL_FINAL_QUANTITY_BEFORE_OVERRIDE"] == "0"
        assert summary["FORENSIC_EXECUTABLE_QUANTITY_OVERRIDE_USED"] is True
        assert summary["DOWNSTREAM_QUANTITY_CONSUMED"] == "0.05"
    finally:
        reset_forensic_executable_quantity_override_session_v1(fq_reset)
        reset_golden_happy_vector_forensic_observability_session_v1(ghv_reset)
        reset_synthetic_enter_forensic_session_v1(syn_reset)


def test_derive_quantity_is_instrument_agnostic() -> None:
    constraints = _constraints("okx_eea:linear_perpetual:AAA:USDT:USDT:aaa-usdt-swap")
    qty, mode = derive_forensic_executable_quantity_v1(
        constraints=constraints,
        reference_price=Decimal("100"),
        candidate_quantity_upper_bound=Decimal("1"),
        explicit_forensic_quantity=None,
    )
    assert qty == Decimal("0.05")
    assert mode == PROVENANCE_CURRENT_DERIVED_MIN_VENUE
    explicit_qty, explicit_mode = derive_forensic_executable_quantity_v1(
        constraints=constraints,
        reference_price=Decimal("100"),
        candidate_quantity_upper_bound=Decimal("1"),
        explicit_forensic_quantity=Decimal("0.07"),
    )
    assert explicit_qty == Decimal("0.07")
    assert explicit_mode == PROVENANCE_EXPLICIT_FORENSIC_INPUT


def test_override_does_not_strip_real_sizing_from_evidence_summary(tmp_path: Path) -> None:
    syn_reset = bind_synthetic_enter_forensic_session_v1(
        SyntheticEnterForensicSessionV1(
            enabled=True,
            synthetic_side="enter_short",
            inject_cycle_index=1,
            product_evidence_root=tmp_path,
            continuous_run_id="run-evidence",
        )
    )
    ghv_reset = bind_golden_happy_vector_forensic_observability_session_v1(
        GoldenHappyVectorForensicObservabilitySessionV1(
            enabled=True,
            product_evidence_root=tmp_path,
            run_id="run-evidence",
            continuous_run_id="run-evidence",
            repository_sha="abc",
        )
    )
    fq_reset = bind_forensic_executable_quantity_override_session_v1(
        build_forensic_executable_quantity_override_session_v1(
            enabled=True,
            explicit_forensic_quantity="0.05",
            product_evidence_root=tmp_path,
            continuous_run_id="run-evidence",
            require_ghv_pre_external_runtime_flight_recorder_v1=False,
        )
    )
    try:
        from src.ops.full_core_live_path_composition_root_v1.current_productive_mv2_capital_context_rebind_v1 import (
            build_current_productive_live_account_capital_context_v1,
        )

        _, cycle_b, _ = _host_enter_cycle()
        replay = _enter_replay(cycle_b)
        constraints = _constraints(str(replay.evidence.instrument_id))
        live_ctx = build_current_productive_live_account_capital_context_v1(
            instrument_id=str(replay.evidence.instrument_id),
            typed_account_equity=Decimal("1000"),
            reference_price=Decimal("100"),
            protective_stop_price=Decimal("99"),
            instrument_constraints=constraints,
        )
        blocked = _blocked_decision(instrument_id=str(replay.evidence.instrument_id))
        maybe_apply_forensic_executable_quantity_override_after_live_29p_v1(
            rebound_replay=replay,
            sizing_decision=blocked,
            constraints=constraints,
            live_ctx=live_ctx,
            cycle_index=1,
        )
        summary = json.loads(
            (tmp_path / "forensic_executable_quantity_override_summary_v1.json").read_text()
        )
        assert summary["REAL_SIZING_OUTCOME_BEFORE_OVERRIDE"] == "BLOCKED"
        assert summary["REAL_FINAL_QUANTITY_BEFORE_OVERRIDE"] == "0"
        assert summary["FORENSIC_EXECUTABLE_QUANTITY"] == "0.05"
    finally:
        reset_forensic_executable_quantity_override_session_v1(fq_reset)
        reset_golden_happy_vector_forensic_observability_session_v1(ghv_reset)
        reset_synthetic_enter_forensic_session_v1(syn_reset)
