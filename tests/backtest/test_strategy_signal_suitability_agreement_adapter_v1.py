# tests/backtest/test_strategy_signal_suitability_agreement_adapter_v1.py
"""Focused adapter tests for family-scoped suitability agreement normalization."""

from __future__ import annotations

import pandas as pd
import pytest

from src.backtest.strategy_signal_binding_v1 import (
    AllFlatSignalReason,
    SignalAlignmentStatus,
    SignalContractStatus,
    StrategyExecutionStatus,
    StrategySignalBindingResultV1,
    StrategySignalProvenanceV1,
)
from src.backtest.strategy_signal_suitability_agreement_adapter_v1 import (
    normalize_strategy_signal_to_suitability_agreement_material_v1,
    resolve_strategy_signal_encoding_class_v1,
)
from trading.master_v2.strategy_suitability_agreement_material_v1 import (
    StrategyAgreementEventKindV1,
    StrategySignalEncodingClassV1,
    StrategySuitabilityAgreementErrorV1,
)

_DIGEST_A = "a" * 64
_DIGEST_B = "b" * 64


def _provenance(**overrides: object) -> StrategySignalProvenanceV1:
    base = {
        "configured_strategy_id": "rsi_reversion",
        "executed_strategy_id": "rsi_reversion",
        "strategy_version": "v1",
        "strategy_owner": "strategies.rsi_reversion",
        "configured_strategy_params": {},
        "effective_strategy_params": {},
        "strategy_params_digest": _DIGEST_A,
        "strategy_execution_status": StrategyExecutionStatus.EXECUTED,
        "strategy_signal_source": "canonical_strategy_signal_series",
        "strategy_signal_digest": _DIGEST_B,
        "strategy_signal_count": 3,
        "strategy_nonzero_signal_count": 2,
        "strategy_signal_transition_count": 1,
        "engine_signal_source": "configured_strategy_signal",
        "engine_signal_digest": _DIGEST_B,
        "engine_input_nonzero_signal_count": 2,
        "signal_alignment_status": SignalAlignmentStatus.ALIGNED,
        "signal_contract_status": SignalContractStatus.PASS,
        "all_flat_signal_reason": AllFlatSignalReason.NONE,
    }
    base.update(overrides)
    return StrategySignalProvenanceV1(**base)


def _binding(
    values: list[int],
    *,
    provenance: StrategySignalProvenanceV1 | None = None,
) -> StrategySignalBindingResultV1:
    return StrategySignalBindingResultV1(
        signals=pd.Series(values, dtype=int),
        provenance=provenance or _provenance(),
    )


def test_positional_ls_encoding_and_material_digest_differs_by_cycle_value() -> None:
    m_long = normalize_strategy_signal_to_suitability_agreement_material_v1(
        _binding([1, 0, -1]),
        instrument_id="inst-eth-usdt-perp",
        trading_epoch=0,
    )
    m_short = normalize_strategy_signal_to_suitability_agreement_material_v1(
        _binding([1, 0, -1]),
        instrument_id="inst-eth-usdt-perp",
        trading_epoch=2,
    )
    assert m_long.encoding_class is StrategySignalEncodingClassV1.POSITIONAL_LS_STATE_V1
    assert m_long.cycle_signal_value == 1
    assert m_short.cycle_signal_value == -1
    assert m_long.material_digest != m_short.material_digest


def test_entry_exit_minus_one_is_exit_not_short() -> None:
    material = normalize_strategy_signal_to_suitability_agreement_material_v1(
        _binding(
            [1, -1, 0],
            provenance=_provenance(
                configured_strategy_id="macd",
                executed_strategy_id="macd",
            ),
        ),
        instrument_id="inst-eth-usdt-perp",
        trading_epoch=1,
    )
    assert material.encoding_class is StrategySignalEncodingClassV1.ENTRY_EXIT_EVENT_V1
    assert material.event_kind is StrategyAgreementEventKindV1.EXIT
    assert material.cycle_signal_value == -1


def test_filter_mask_values() -> None:
    blocked = normalize_strategy_signal_to_suitability_agreement_material_v1(
        _binding(
            [0, 1],
            provenance=_provenance(
                configured_strategy_id="vol_regime_filter",
                executed_strategy_id="vol_regime_filter",
            ),
        ),
        instrument_id="inst-eth-usdt-perp",
        trading_epoch=0,
    )
    allowed = normalize_strategy_signal_to_suitability_agreement_material_v1(
        _binding(
            [0, 1],
            provenance=_provenance(
                configured_strategy_id="vol_regime_filter",
                executed_strategy_id="vol_regime_filter",
            ),
        ),
        instrument_id="inst-eth-usdt-perp",
        trading_epoch=1,
    )
    assert blocked.filter_pass is False
    assert allowed.filter_pass is True


def test_positional_long01_negative_fail_closed() -> None:
    with pytest.raises(StrategySuitabilityAgreementErrorV1, match="cross_family_coercion"):
        normalize_strategy_signal_to_suitability_agreement_material_v1(
            _binding(
                [-1],
                provenance=_provenance(
                    configured_strategy_id="ma_crossover",
                    executed_strategy_id="ma_crossover",
                ),
            ),
            instrument_id="inst-eth-usdt-perp",
            trading_epoch=0,
        )


def test_unknown_stub_fail_closed() -> None:
    assert (
        resolve_strategy_signal_encoding_class_v1("meta_labeling")
        is StrategySignalEncodingClassV1.UNKNOWN_OR_STUB_V1
    )
    with pytest.raises(StrategySuitabilityAgreementErrorV1, match="stub_or_unknown"):
        normalize_strategy_signal_to_suitability_agreement_material_v1(
            _binding(
                [1],
                provenance=_provenance(
                    configured_strategy_id="meta_labeling",
                    executed_strategy_id="meta_labeling",
                ),
            ),
            instrument_id="inst-eth-usdt-perp",
            trading_epoch=0,
        )


def test_identity_and_digest_mismatches_fail_closed() -> None:
    binding = _binding([1])
    with pytest.raises(StrategySuitabilityAgreementErrorV1, match="strategy_identity_mismatch"):
        normalize_strategy_signal_to_suitability_agreement_material_v1(
            binding,
            instrument_id="inst-eth-usdt-perp",
            trading_epoch=0,
            expected_configured_strategy_id="other",
        )
    with pytest.raises(StrategySuitabilityAgreementErrorV1, match="strategy_version_mismatch"):
        normalize_strategy_signal_to_suitability_agreement_material_v1(
            binding,
            instrument_id="inst-eth-usdt-perp",
            trading_epoch=0,
            expected_strategy_version="v999",
        )
    with pytest.raises(
        StrategySuitabilityAgreementErrorV1, match="strategy_params_digest_mismatch"
    ):
        normalize_strategy_signal_to_suitability_agreement_material_v1(
            binding,
            instrument_id="inst-eth-usdt-perp",
            trading_epoch=0,
            expected_strategy_params_digest="c" * 64,
        )
    with pytest.raises(
        StrategySuitabilityAgreementErrorV1, match="strategy_signal_digest_mismatch"
    ):
        normalize_strategy_signal_to_suitability_agreement_material_v1(
            binding,
            instrument_id="inst-eth-usdt-perp",
            trading_epoch=0,
            expected_strategy_signal_digest="c" * 64,
        )
    with pytest.raises(StrategySuitabilityAgreementErrorV1, match="missing_cycle_signal"):
        normalize_strategy_signal_to_suitability_agreement_material_v1(
            binding,
            instrument_id="inst-eth-usdt-perp",
            trading_epoch=9,
        )
