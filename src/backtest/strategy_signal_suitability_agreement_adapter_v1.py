# src/backtest/strategy_signal_suitability_agreement_adapter_v1.py
"""
Thin adapter: StrategySignalBindingResultV1 → StrategySuitabilityAgreementMaterialV1.

Family-scoped normalization only. No position, exit, reversal, sizing, or order authority.
"""

from __future__ import annotations

from typing import Any, Mapping, Optional

from src.backtest.strategy_signal_binding_v1 import (
    COMPOSITE_STRATEGY_ID,
    StrategyExecutionStatus,
    StrategySignalBindingResultV1,
    StrategySignalProvenanceV1,
)
from src.strategies.bollinger_event_semantic_contract_v1 import (
    BOLLINGER_STRATEGY_ID,
    BollingerSignalEventV1,
    classify_bollinger_raw_signal_event_v1,
)
from trading.master_v2.strategy_suitability_agreement_material_v1 import (
    StrategyAgreementEventKindV1,
    StrategyEntrySideCarrierV1,
    StrategySideAgreementV1,
    StrategySignalEncodingClassV1,
    StrategySuitabilityAgreementErrorV1,
    StrategySuitabilityAgreementMaterialV1,
    compute_strategy_suitability_agreement_material_digest_v1,
)

STRATEGY_SIGNAL_SUITABILITY_AGREEMENT_ADAPTER_OWNER = (
    "backtest.strategy_signal_suitability_agreement_adapter_v1"
)

_POSITIONAL_LS_OWNERS = frozenset(
    {
        "breakout_donchian",
        "rsi_reversion",
        "vol_breakout",
        "breakout",
        "mean_reversion_channel",
    }
)
_POSITIONAL_LONG01_OWNERS = frozenset(
    {
        "ma_crossover",
        "ehlers_cycle_filter",
        "bouchaud_microstructure",
        "el_karoui_vol_model",
        "armstrong_cycle",
    }
)
_ENTRY_EXIT_EVENT_OWNERS = frozenset(
    {
        "macd",
        "momentum_1h",
        "bollinger_bands",
        "trend_following",
        "mean_reversion",
        "my_strategy",
        "ecm_cycle",
    }
)
_FILTER_MASK01_OWNERS = frozenset(
    {
        "vol_regime_filter",
        "vol_regime_overlay",
    }
)
_UNKNOWN_OR_STUB_OWNERS = frozenset(
    {
        "meta_labeling",
    }
)

# Explicit producer-scoped side ratification (OBL_B05).
# Only trend_following is ratified: productive +1 ENTRY = LONG.
# No heuristic name/sign/class derivation for other ENTRY_EXIT owners.
_TREND_FOLLOWING_ENTRY_SIDE_RATIFIED_OWNER = "trend_following"

# OBL_B07: bollinger_bands is EVENT_ONLY — events without direction/side.
_BOLLINGER_EVENT_ONLY_OWNER = BOLLINGER_STRATEGY_ID


def resolve_strategy_signal_encoding_class_v1(
    executed_strategy_id: str,
    *,
    effective_strategy_params: Optional[Mapping[str, Any]] = None,
) -> StrategySignalEncodingClassV1:
    """Reuse-first encoding-class resolution from ratified family owners."""
    strategy_id = str(executed_strategy_id).strip()
    if not strategy_id:
        raise StrategySuitabilityAgreementErrorV1("strategy_identity_mismatch")
    if strategy_id in _UNKNOWN_OR_STUB_OWNERS:
        return StrategySignalEncodingClassV1.UNKNOWN_OR_STUB_V1
    if strategy_id in _FILTER_MASK01_OWNERS:
        return StrategySignalEncodingClassV1.FILTER_MASK01_V1
    if strategy_id in _ENTRY_EXIT_EVENT_OWNERS:
        return StrategySignalEncodingClassV1.ENTRY_EXIT_EVENT_V1
    if strategy_id in _POSITIONAL_LONG01_OWNERS:
        return StrategySignalEncodingClassV1.POSITIONAL_LONG01_STATE_V1
    if strategy_id in _POSITIONAL_LS_OWNERS:
        return StrategySignalEncodingClassV1.POSITIONAL_LS_STATE_V1
    if strategy_id == COMPOSITE_STRATEGY_ID:
        params = effective_strategy_params or {}
        signal_owner = str(params.get("signal_strategy_id", "")).strip()
        filter_owner = str(params.get("filter_strategy_id", "")).strip()
        if filter_owner and not signal_owner:
            return resolve_strategy_signal_encoding_class_v1(filter_owner)
        if signal_owner:
            return resolve_strategy_signal_encoding_class_v1(signal_owner)
        raise StrategySuitabilityAgreementErrorV1("encoding_class_unknown")
    raise StrategySuitabilityAgreementErrorV1("encoding_class_unknown")


def _extract_cycle_signal_value(
    binding: StrategySignalBindingResultV1,
    *,
    trading_epoch: int,
) -> int:
    signals = binding.signals
    if signals is None or len(signals) == 0:
        raise StrategySuitabilityAgreementErrorV1("missing_cycle_signal")
    if trading_epoch < 0 or trading_epoch >= len(signals):
        raise StrategySuitabilityAgreementErrorV1("missing_cycle_signal")
    raw = signals.iloc[trading_epoch]
    try:
        value = int(raw)
    except (TypeError, ValueError) as exc:
        raise StrategySuitabilityAgreementErrorV1("missing_cycle_signal") from exc
    if value not in (-1, 0, 1):
        raise StrategySuitabilityAgreementErrorV1("missing_cycle_signal")
    return value


def _intrinsic_side_agreement_and_aux(
    encoding_class: StrategySignalEncodingClassV1,
    cycle_signal_value: int,
) -> tuple[StrategySideAgreementV1, Optional[bool], Optional[StrategyAgreementEventKindV1]]:
    if encoding_class is StrategySignalEncodingClassV1.UNKNOWN_OR_STUB_V1:
        raise StrategySuitabilityAgreementErrorV1("stub_or_unknown_strategy_semantics")
    if encoding_class is StrategySignalEncodingClassV1.FILTER_MASK01_V1:
        if cycle_signal_value not in (0, 1):
            raise StrategySuitabilityAgreementErrorV1("cross_family_coercion_attempted")
        return StrategySideAgreementV1.NOT_APPLICABLE, bool(cycle_signal_value == 1), None
    if encoding_class is StrategySignalEncodingClassV1.ENTRY_EXIT_EVENT_V1:
        if cycle_signal_value == 1:
            return StrategySideAgreementV1.NEUTRAL, None, StrategyAgreementEventKindV1.ENTRY
        if cycle_signal_value == -1:
            return StrategySideAgreementV1.NOT_APPLICABLE, None, StrategyAgreementEventKindV1.EXIT
        return StrategySideAgreementV1.NEUTRAL, None, StrategyAgreementEventKindV1.NONE
    if encoding_class is StrategySignalEncodingClassV1.POSITIONAL_LONG01_STATE_V1:
        if cycle_signal_value == -1:
            raise StrategySuitabilityAgreementErrorV1("cross_family_coercion_attempted")
        if cycle_signal_value == 0:
            return StrategySideAgreementV1.NEUTRAL, None, None
        return StrategySideAgreementV1.NEUTRAL, None, None
    if encoding_class is StrategySignalEncodingClassV1.POSITIONAL_LS_STATE_V1:
        if cycle_signal_value == 0:
            return StrategySideAgreementV1.NEUTRAL, None, None
        return StrategySideAgreementV1.NEUTRAL, None, None
    raise StrategySuitabilityAgreementErrorV1("encoding_class_unknown")


def _bollinger_event_only_side_agreement_and_aux(
    cycle_signal_value: int,
) -> tuple[StrategySideAgreementV1, Optional[bool], Optional[StrategyAgreementEventKindV1]]:
    """OBL_B07 Bollinger EVENT_ONLY: map raw signal via Bollinger contract only.

    Direction and entry_side stay NONE (enforced by carrier resolver). Classic
    engine LONG reinterpretation is explicitly non-canonical here.
    """
    event = classify_bollinger_raw_signal_event_v1(cycle_signal_value)
    if event is BollingerSignalEventV1.UNKNOWN_FAIL_CLOSED:
        raise StrategySuitabilityAgreementErrorV1("bollinger_raw_signal_invalid")
    if event is BollingerSignalEventV1.ENTRY_EVENT:
        return StrategySideAgreementV1.NEUTRAL, None, StrategyAgreementEventKindV1.ENTRY
    if event is BollingerSignalEventV1.EXIT_EVENT:
        return StrategySideAgreementV1.NOT_APPLICABLE, None, StrategyAgreementEventKindV1.EXIT
    return StrategySideAgreementV1.NEUTRAL, None, StrategyAgreementEventKindV1.NONE


def _resolve_entry_side_carrier_v1(
    *,
    executed_strategy_id: str,
    encoding_class: StrategySignalEncodingClassV1,
    event_kind: Optional[StrategyAgreementEventKindV1],
    cycle_signal_value: int,
) -> StrategyEntrySideCarrierV1:
    """Resolve optional ENTRY_EXIT ``entry_side`` (fail-closed, producer-explicit).

    Productive ``trend_following`` contract (``src/strategies/trend_following.py``):
    - ``+1`` / ENTRY = LONG entry (ADX strong and +DI > -DI; optional MA filter)
    - ``-1`` / EXIT = exit event (ADX weak or -DI > +DI) — never SHORT
    - ``0`` / NONE = no change / flat

    ``bollinger_bands`` is OBL_B07 EVENT_ONLY: events without side (always NONE).
    No SHORT-entry condition exists in the productive Bollinger producer. Other
    ENTRY_EXIT owners remain ``NONE`` until a separate ratification GO.
    """
    if encoding_class is not StrategySignalEncodingClassV1.ENTRY_EXIT_EVENT_V1:
        return StrategyEntrySideCarrierV1.NONE
    if executed_strategy_id == _BOLLINGER_EVENT_ONLY_OWNER:
        return StrategyEntrySideCarrierV1.NONE
    if executed_strategy_id != _TREND_FOLLOWING_ENTRY_SIDE_RATIFIED_OWNER:
        return StrategyEntrySideCarrierV1.NONE
    if event_kind is StrategyAgreementEventKindV1.ENTRY and cycle_signal_value == 1:
        return StrategyEntrySideCarrierV1.LONG
    return StrategyEntrySideCarrierV1.NONE


def normalize_strategy_signal_to_suitability_agreement_material_v1(
    binding: StrategySignalBindingResultV1,
    *,
    instrument_id: str,
    trading_epoch: int,
    expected_configured_strategy_id: Optional[str] = None,
    expected_executed_strategy_id: Optional[str] = None,
    expected_strategy_version: Optional[str] = None,
    expected_strategy_params_digest: Optional[str] = None,
    expected_strategy_signal_digest: Optional[str] = None,
) -> StrategySuitabilityAgreementMaterialV1:
    """Normalize a bound strategy signal cycle into master_v2 agreement material."""
    if not isinstance(binding, StrategySignalBindingResultV1):
        raise StrategySuitabilityAgreementErrorV1("stub_or_unknown_strategy_semantics")
    provenance: StrategySignalProvenanceV1 = binding.provenance
    if provenance.strategy_execution_status is not StrategyExecutionStatus.EXECUTED:
        raise StrategySuitabilityAgreementErrorV1("stub_or_unknown_strategy_semantics")

    configured_id = provenance.configured_strategy_id
    executed_id = provenance.executed_strategy_id
    strategy_version = provenance.strategy_version
    params_digest = provenance.strategy_params_digest
    signal_digest = provenance.strategy_signal_digest

    if (
        expected_configured_strategy_id is not None
        and configured_id != expected_configured_strategy_id
    ):
        raise StrategySuitabilityAgreementErrorV1("strategy_identity_mismatch")
    if expected_executed_strategy_id is not None and executed_id != expected_executed_strategy_id:
        raise StrategySuitabilityAgreementErrorV1("strategy_identity_mismatch")
    if expected_strategy_version is not None and strategy_version != expected_strategy_version:
        raise StrategySuitabilityAgreementErrorV1("strategy_version_mismatch")
    if (
        expected_strategy_params_digest is not None
        and params_digest != expected_strategy_params_digest
    ):
        raise StrategySuitabilityAgreementErrorV1("strategy_params_digest_mismatch")
    if (
        expected_strategy_signal_digest is not None
        and signal_digest != expected_strategy_signal_digest
    ):
        raise StrategySuitabilityAgreementErrorV1("strategy_signal_digest_mismatch")
    if not instrument_id:
        raise StrategySuitabilityAgreementErrorV1("instrument_mismatch")

    encoding_class = resolve_strategy_signal_encoding_class_v1(
        executed_id,
        effective_strategy_params=provenance.effective_strategy_params,
    )
    if encoding_class is StrategySignalEncodingClassV1.UNKNOWN_OR_STUB_V1:
        raise StrategySuitabilityAgreementErrorV1("stub_or_unknown_strategy_semantics")

    cycle_signal_value = _extract_cycle_signal_value(binding, trading_epoch=trading_epoch)
    if executed_id == _BOLLINGER_EVENT_ONLY_OWNER:
        # OBL_B07: Bollinger EVENT_ONLY contract is the event authority.
        # Does not invent LONG/SHORT or classic-engine direction.
        side_agreement, filter_pass, event_kind = _bollinger_event_only_side_agreement_and_aux(
            cycle_signal_value
        )
    else:
        side_agreement, filter_pass, event_kind = _intrinsic_side_agreement_and_aux(
            encoding_class, cycle_signal_value
        )
    # Explicit producer-scoped carrier only (trend_following LONG on ENTRY).
    # Bollinger EVENT_ONLY and generic +1 never invent side authority.
    entry_side = _resolve_entry_side_carrier_v1(
        executed_strategy_id=executed_id,
        encoding_class=encoding_class,
        event_kind=event_kind,
        cycle_signal_value=cycle_signal_value,
    )
    if (
        executed_id == _BOLLINGER_EVENT_ONLY_OWNER
        and entry_side is not StrategyEntrySideCarrierV1.NONE
    ):
        raise StrategySuitabilityAgreementErrorV1("bollinger_entry_side_must_be_none")
    material_digest = compute_strategy_suitability_agreement_material_digest_v1(
        encoding_class=encoding_class,
        configured_strategy_id=configured_id,
        executed_strategy_id=executed_id,
        strategy_version=strategy_version,
        strategy_params_digest=params_digest,
        strategy_signal_digest=signal_digest,
        instrument_id=instrument_id,
        trading_epoch=trading_epoch,
        cycle_signal_value=cycle_signal_value,
        side_agreement=side_agreement,
        filter_pass=filter_pass,
        event_kind=event_kind,
        entry_side=entry_side,
    )
    return StrategySuitabilityAgreementMaterialV1(
        encoding_class=encoding_class,
        configured_strategy_id=configured_id,
        executed_strategy_id=executed_id,
        strategy_version=strategy_version,
        strategy_params_digest=params_digest,
        strategy_signal_digest=signal_digest,
        instrument_id=instrument_id,
        trading_epoch=trading_epoch,
        cycle_signal_value=cycle_signal_value,  # type: ignore[arg-type]
        side_agreement=side_agreement,
        filter_pass=filter_pass,
        event_kind=event_kind,
        material_digest=material_digest,
        entry_side=entry_side,
    )


__all__ = [
    "STRATEGY_SIGNAL_SUITABILITY_AGREEMENT_ADAPTER_OWNER",
    "normalize_strategy_signal_to_suitability_agreement_material_v1",
    "resolve_strategy_signal_encoding_class_v1",
]
