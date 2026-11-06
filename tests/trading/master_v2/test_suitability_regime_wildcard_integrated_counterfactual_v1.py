# tests/trading/master_v2/test_suitability_regime_wildcard_integrated_counterfactual_v1.py
"""Integrated counterfactual: production registry + ENTRY agreement under trending."""

from __future__ import annotations

from dataclasses import replace

from src.strategies.registry import build_registry_snapshot
from src.strategies.suitability_registry_adapter_v1 import build_suitability_registry_from_snapshot
from tests.trading.master_v2 import test_integrated_offline_trading_logic_replay_v1 as replay_tests
from trading.master_v2.integrated_offline_trading_logic_replay_v1 import (
    run_integrated_offline_trading_logic_replay_v1,
)
from trading.master_v2.suitability_binding_v1 import (
    SuitabilityBindingStatus,
    filter_eligible_strategies,
)
from trading.master_v2.directional_assessment_v1 import DirectionalAssessmentSide
from trading.master_v2.strategy_suitability_agreement_material_v1 import (
    StrategyAgreementEventKindV1,
    StrategySideAgreementV1,
    StrategySignalEncodingClassV1,
    StrategySuitabilityAgreementMaterialV1,
    compute_strategy_suitability_agreement_material_digest_v1,
)


def _entry_material(
    *, instrument_id: str, trading_epoch: int
) -> StrategySuitabilityAgreementMaterialV1:
    encoding = StrategySignalEncodingClassV1.ENTRY_EXIT_EVENT_V1
    digest = compute_strategy_suitability_agreement_material_digest_v1(
        encoding_class=encoding,
        configured_strategy_id="bollinger_bands",
        executed_strategy_id="bollinger_bands",
        strategy_version="v1",
        strategy_params_digest="a" * 64,
        strategy_signal_digest="b" * 64,
        instrument_id=instrument_id,
        trading_epoch=trading_epoch,
        cycle_signal_value=1,
        side_agreement=StrategySideAgreementV1.NEUTRAL,
        filter_pass=None,
        event_kind=StrategyAgreementEventKindV1.ENTRY,
    )
    return StrategySuitabilityAgreementMaterialV1(
        encoding_class=encoding,
        configured_strategy_id="bollinger_bands",
        executed_strategy_id="bollinger_bands",
        strategy_version="v1",
        strategy_params_digest="a" * 64,
        strategy_signal_digest="b" * 64,
        instrument_id=instrument_id,
        trading_epoch=trading_epoch,
        cycle_signal_value=1,
        side_agreement=StrategySideAgreementV1.NEUTRAL,
        filter_pass=None,
        event_kind=StrategyAgreementEventKindV1.ENTRY,
        material_digest=digest,
    )


def test_integrated_production_registry_bull_entry_agreement_not_no_suitable() -> None:
    registry = build_suitability_registry_from_snapshot(build_registry_snapshot())
    eligible = filter_eligible_strategies(
        registry,
        side=DirectionalAssessmentSide.LONG,
        regime_id="trending",
    )
    assert len(eligible) == len(registry.entries)
    assert len(eligible) > 0

    base = replay_tests._replay_input()
    material = _entry_material(
        instrument_id=base.instrument_id,
        trading_epoch=base.trading_epoch,
    )
    inp = replace(
        base,
        strategy_registry=registry,
        regime_id="trending",
        strategy_suitability_agreement_material=material,
    )
    result = run_integrated_offline_trading_logic_replay_v1(inp)
    inter = result.intermediate
    assert inter is not None
    bull = inter.bull_suitability
    assert bull.status is SuitabilityBindingStatus.PASS
    assert "strategy_signal_agreement_agree" in bull.reason_codes
    assert "no_suitable_strategy" not in bull.reason_codes
    assert bull.selected_strategy_id is not None
    assert len(bull.eligible_strategy_ids) > 0
