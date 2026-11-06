"""STEP29P consolidation contract: reuse-first owner binding and bypass guards."""

from __future__ import annotations

from decimal import Decimal
from pathlib import Path

import src.governance.capital_risk_sizing_v1 as sizing
from trading.master_v2.canonical_trading_decision_evidence_v1 import (
    CanonicalTradingDecisionEvidenceV1,
)

CANONICAL_OWNER = "src.governance.capital_risk_sizing_v1"
REPO_ROOT = Path(__file__).resolve().parents[2]


def test_consolidation_canonical_owner_is_single_ssot() -> None:
    assert sizing.CONTRACT_NAME == "capital_risk_sizing_v1"
    assert sizing.PACKAGE_MARKER == "CAPITAL_RISK_SIZING_V1=true"
    assert f"{sizing.__name__}" == "src.governance.capital_risk_sizing_v1"


def test_consolidation_quantity_chain_contract_names() -> None:
    schema = sizing.capital_risk_sizing_schema_v1()
    assert schema["quantity_chain"] == [
        "CanonicalTradingDecisionEvidenceV1",
        "ScopeCapitalEnvelopeV1",
        "PreSizingRiskAssessmentV1",
        "CanonicalPositionSizingV1",
        "PostSizingRiskAssessmentV1",
        "QuantityProvenanceV1",
    ]


def test_consolidation_bypass_scan_export() -> None:
    scan = sizing.export_bypass_scan_v1(repo_root=REPO_ROOT)
    assert scan["CANONICAL_OWNER"] == CANONICAL_OWNER
    assert scan["DIRECT_DECISION_TO_QUANTITY_PATH_BLOCKED"] is True
    assert scan["DIRECT_SIGNAL_TO_QUANTITY_PATH_BLOCKED"] is True
    assert scan["IMPLICIT_DEFAULT_QUANTITY_BLOCKED"] is True
    assert scan["RISK_INCREASING_ROUNDING_BLOCKED"] is True
    assert scan["QUANTITY_WITHOUT_PROVENANCE_BLOCKED"] is True
    assert scan["DIRECT_QUANTITY_TO_ADAPTER_PATH_BLOCKED"] is True
    assert scan["AUTHORITY_EFFECT"] == "NONE"
    assert scan["RUNTIME_EFFECT"] == "NONE"
    assert scan["ADAPTER_COMPATIBLE"] is False


def test_consolidation_legacy_position_sizer_classified_deprecate() -> None:
    scan = sizing.export_bypass_scan_v1(repo_root=REPO_ROOT)
    assert scan["LEGACY_POSITION_SIZER_CLASSIFICATION"] == "DEPRECATE_LEGACY_PATH"
    assert scan["LEGACY_POSITION_SIZER_PRESENT"] is True


def test_consolidation_policy_limits_not_hardcoded_in_module_source() -> None:
    source = (REPO_ROOT / "src" / "governance" / "capital_risk_sizing_v1.py").read_text(
        encoding="utf-8"
    )
    assert 'TOTAL_LIMIT_USD = Decimal("500")' not in source
    assert 'ORDER_LIMIT_USD = Decimal("25")' not in source


def test_consolidation_end_to_end_chain_from_decision_evidence() -> None:
    policy = sizing.CapitalRiskSizingPolicyV1(
        policy_version="capital_risk_sizing_policy_v1",
        total_capital_limit_usd=Decimal("500"),
        order_limit_usd=Decimal("25"),
        daily_loss_limit_usd=Decimal("25"),
        max_positions=1,
    )
    instrument = sizing.InstrumentQuantityConstraintsV1(
        instrument_id="ETH-USD-PERP",
        market_type="futures",
        contract_kind="LINEAR",
        contract_multiplier=Decimal("1"),
        lot_size=Decimal("0.01"),
        minimum_quantity=Decimal("0.01"),
        maximum_quantity=Decimal("100"),
        minimum_notional=Decimal("5"),
        tick_size=Decimal("0.01"),
        instrument_metadata_version="futures_metadata_v1_test",
    )
    evidence = CanonicalTradingDecisionEvidenceV1(
        decision_id="decision-consolidation",
        replay_id="replay-consolidation",
        instrument_id="ETH-USD-PERP",
        trading_epoch=1,
        market_context_ref="ctx",
        scope_initialization_ref="init",
        scope_event_ref="evt",
        bull_assessment_ref="bull",
        bear_assessment_ref="bear",
        state_switch_ref="sw",
        bull_survival_ref="bs",
        bear_survival_ref="brs",
        bull_suitability_ref="bsu",
        bear_suitability_ref="brsu",
        composition_result_ref="comp",
        entry_exit_policy_ref="eep",
        current_scope_ref="cs",
        next_scope_ref="ns",
        previous_direction_state="neutral",
        next_direction_state="long_active",
        selected_side="LONG",
        selected_strategy_ref="strat",
        decision_outcome="enter_long",
        entry_or_exit_policy_ref="eep",
        reason_codes=(),
        decision_precedence_trace=(),
        component_versions={},
        policy_versions={"capital_risk_sizing_policy_v1": "v1"},
        config_digest="cfg",
        implementation_digest=sizing.IMPLEMENTATION_DIGEST,
        input_digest="b" * 64,
        semantic_digest="",
    )
    context = sizing.CapitalRiskSizingContextV1(
        reference_price=Decimal("2000"),
        protective_stop_price=Decimal("1900"),
        stop_distance=None,
        account_equity=Decimal("500"),
        already_committed_capital=Decimal("0"),
        daily_loss_consumed=Decimal("0"),
        current_reconciled_exposure=Decimal("0"),
        reconciled_open_position_quantity=Decimal("0"),
        current_open_positions_count=0,
        current_open_side=None,
        reconciliation_status="RECONCILED",
        configured_quantity_cap=None,
        leverage_ceiling=Decimal("5"),
        instrument=instrument,
        config_digest="cfg",
    )
    result = sizing.evaluate_quantity_chain_v1(evidence, context, policy)
    assert result.outcome is sizing.CapitalRiskSizingOutcome.PASS
    assert result.quantity_provenance is not None
    assert result.quantity_provenance.adapter_compatible is False
    assert result.scope_capital_envelope.policy_version == policy.policy_version
