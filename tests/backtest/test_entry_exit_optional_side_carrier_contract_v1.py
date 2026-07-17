"""OBL_B05 ENTRY_EXIT optional explicit side-carrier contract v1."""

from __future__ import annotations

from dataclasses import replace

import pytest

from src.backtest.mv2_research_wiring_v1 import (
    MV2_AGREEMENT_BOUND_RELATIVE_IMPULSE_V1,
    project_mv2_agreement_bound_price_path_v1,
    resolve_agreement_bound_directional_cycle_v1,
)
from src.backtest.strategy_signal_suitability_agreement_adapter_v1 import (
    normalize_strategy_signal_to_suitability_agreement_material_v1,
)
from trading.master_v2.directional_assessment_v1 import (
    DirectionalAssessmentSide,
    compute_signal_strength,
)
from trading.master_v2.strategy_suitability_agreement_material_v1 import (
    StrategyAgreementEventKindV1,
    StrategyEntrySideCarrierV1,
    StrategySideAgreementV1,
    StrategySignalEncodingClassV1,
    StrategySuitabilityAgreementErrorV1,
    StrategySuitabilityAgreementMaterialV1,
    compute_strategy_suitability_agreement_material_digest_v1,
    deserialize_strategy_suitability_agreement_material_v1,
    serialize_strategy_suitability_agreement_material_v1,
)
from tests.backtest.test_strategy_signal_suitability_agreement_adapter_v1 import (
    _binding,
    _provenance,
)

_DIGEST = "a" * 64
_PANEL_ENTRY_BASELINE = 185
_FIRST_FALSE_PREDICATE_ID = "FF_DA_FLAT_PATH_ENTRY_EXIT_NO_SIDE_CARRIER_V1"


def _material(
    *,
    encoding: StrategySignalEncodingClassV1,
    cycle: int,
    side: StrategySideAgreementV1 = StrategySideAgreementV1.NEUTRAL,
    event: StrategyAgreementEventKindV1 | None = None,
    entry_side: StrategyEntrySideCarrierV1 = StrategyEntrySideCarrierV1.NONE,
    strategy_id: str = "bollinger_bands",
) -> StrategySuitabilityAgreementMaterialV1:
    digest = compute_strategy_suitability_agreement_material_digest_v1(
        encoding_class=encoding,
        configured_strategy_id=strategy_id,
        executed_strategy_id=strategy_id,
        strategy_version="v1",
        strategy_params_digest=_DIGEST,
        strategy_signal_digest=_DIGEST,
        instrument_id="okx:linear_perpetual:1INCH:USDT:USDT:perp",
        trading_epoch=10,
        cycle_signal_value=cycle,
        side_agreement=side,
        filter_pass=None,
        event_kind=event,
        entry_side=entry_side,
    )
    return StrategySuitabilityAgreementMaterialV1(
        encoding_class=encoding,
        configured_strategy_id=strategy_id,
        executed_strategy_id=strategy_id,
        strategy_version="v1",
        strategy_params_digest=_DIGEST,
        strategy_signal_digest=_DIGEST,
        instrument_id="okx:linear_perpetual:1INCH:USDT:USDT:perp",
        trading_epoch=10,
        cycle_signal_value=cycle,  # type: ignore[arg-type]
        side_agreement=side,
        filter_pass=None,
        event_kind=event,
        material_digest=digest,
        entry_side=entry_side,
    )


def test_legacy_entry_exit_without_field_remains_flat_fail_closed() -> None:
    material = _material(
        encoding=StrategySignalEncodingClassV1.ENTRY_EXIT_EVENT_V1,
        cycle=1,
        side=StrategySideAgreementV1.NEUTRAL,
        event=StrategyAgreementEventKindV1.ENTRY,
        entry_side=StrategyEntrySideCarrierV1.NONE,
    )
    assert material.entry_side is StrategyEntrySideCarrierV1.NONE
    assert resolve_agreement_bound_directional_cycle_v1(material) is None
    assert project_mv2_agreement_bound_price_path_v1(mark_price=100.0, material=material) == (
        100.0,
        100.0,
    )


def test_cycle_signal_plus_one_alone_does_not_create_direction() -> None:
    material = _material(
        encoding=StrategySignalEncodingClassV1.ENTRY_EXIT_EVENT_V1,
        cycle=1,
        event=StrategyAgreementEventKindV1.ENTRY,
        entry_side=StrategyEntrySideCarrierV1.NONE,
    )
    assert material.cycle_signal_value == 1
    assert resolve_agreement_bound_directional_cycle_v1(material) is None


def test_explicit_long_relative_positive_projection() -> None:
    material = _material(
        encoding=StrategySignalEncodingClassV1.ENTRY_EXIT_EVENT_V1,
        cycle=1,
        event=StrategyAgreementEventKindV1.ENTRY,
        entry_side=StrategyEntrySideCarrierV1.LONG,
    )
    assert resolve_agreement_bound_directional_cycle_v1(material) == 1
    path = project_mv2_agreement_bound_price_path_v1(mark_price=100.0, material=material)
    assert path == (100.0, 100.0 * (1.0 + MV2_AGREEMENT_BOUND_RELATIVE_IMPULSE_V1))
    bull = compute_signal_strength(
        price_path=path, side=DirectionalAssessmentSide.LONG, reference_price=100.0
    )
    bear = compute_signal_strength(
        price_path=path, side=DirectionalAssessmentSide.SHORT, reference_price=100.0
    )
    assert bull > 0.0
    assert bear < 0.0


def test_explicit_short_relative_negative_projection() -> None:
    material = _material(
        encoding=StrategySignalEncodingClassV1.ENTRY_EXIT_EVENT_V1,
        cycle=1,
        event=StrategyAgreementEventKindV1.ENTRY,
        entry_side=StrategyEntrySideCarrierV1.SHORT,
    )
    assert resolve_agreement_bound_directional_cycle_v1(material) == -1
    path = project_mv2_agreement_bound_price_path_v1(mark_price=100.0, material=material)
    assert path == (100.0, 100.0 * (1.0 - MV2_AGREEMENT_BOUND_RELATIVE_IMPULSE_V1))
    bull = compute_signal_strength(
        price_path=path, side=DirectionalAssessmentSide.LONG, reference_price=100.0
    )
    bear = compute_signal_strength(
        price_path=path, side=DirectionalAssessmentSide.SHORT, reference_price=100.0
    )
    assert bear > 0.0
    assert bull < 0.0


def test_no_bull_bear_mirroring_shared_path_semantics() -> None:
    long_mat = _material(
        encoding=StrategySignalEncodingClassV1.ENTRY_EXIT_EVENT_V1,
        cycle=1,
        event=StrategyAgreementEventKindV1.ENTRY,
        entry_side=StrategyEntrySideCarrierV1.LONG,
    )
    short_mat = _material(
        encoding=StrategySignalEncodingClassV1.ENTRY_EXIT_EVENT_V1,
        cycle=1,
        event=StrategyAgreementEventKindV1.ENTRY,
        entry_side=StrategyEntrySideCarrierV1.SHORT,
    )
    long_path = project_mv2_agreement_bound_price_path_v1(mark_price=100.0, material=long_mat)
    short_path = project_mv2_agreement_bound_price_path_v1(mark_price=100.0, material=short_mat)
    assert long_path != short_path
    assert long_path[0] == short_path[0] == 100.0
    # Shared long-convention path; orientation via compute_signal_strength, not mirror.


def test_positional_ls_and_long01_unchanged() -> None:
    ls_long = _material(
        encoding=StrategySignalEncodingClassV1.POSITIONAL_LS_STATE_V1,
        cycle=1,
        strategy_id="rsi_reversion",
    )
    ls_short = _material(
        encoding=StrategySignalEncodingClassV1.POSITIONAL_LS_STATE_V1,
        cycle=-1,
        strategy_id="rsi_reversion",
    )
    long01 = _material(
        encoding=StrategySignalEncodingClassV1.POSITIONAL_LONG01_STATE_V1,
        cycle=1,
        strategy_id="ma_crossover",
    )
    long01_flat = _material(
        encoding=StrategySignalEncodingClassV1.POSITIONAL_LONG01_STATE_V1,
        cycle=0,
        strategy_id="ma_crossover",
    )
    assert resolve_agreement_bound_directional_cycle_v1(ls_long) == 1
    assert resolve_agreement_bound_directional_cycle_v1(ls_short) == -1
    assert resolve_agreement_bound_directional_cycle_v1(long01) == 1
    assert resolve_agreement_bound_directional_cycle_v1(long01_flat) is None
    assert ls_long.entry_side is StrategyEntrySideCarrierV1.NONE
    assert long01.entry_side is StrategyEntrySideCarrierV1.NONE


def test_exit_does_not_invent_side_even_if_carrier_absent() -> None:
    material = _material(
        encoding=StrategySignalEncodingClassV1.ENTRY_EXIT_EVENT_V1,
        cycle=-1,
        side=StrategySideAgreementV1.NOT_APPLICABLE,
        event=StrategyAgreementEventKindV1.EXIT,
        entry_side=StrategyEntrySideCarrierV1.NONE,
    )
    assert resolve_agreement_bound_directional_cycle_v1(material) is None
    assert project_mv2_agreement_bound_price_path_v1(mark_price=50.0, material=material) == (
        50.0,
        50.0,
    )


def test_exit_with_explicit_side_rejected_by_schema() -> None:
    with pytest.raises(StrategySuitabilityAgreementErrorV1, match="entry_side_event_kind_mismatch"):
        _material(
            encoding=StrategySignalEncodingClassV1.ENTRY_EXIT_EVENT_V1,
            cycle=-1,
            side=StrategySideAgreementV1.NOT_APPLICABLE,
            event=StrategyAgreementEventKindV1.EXIT,
            entry_side=StrategyEntrySideCarrierV1.LONG,
        )


def test_serialization_roundtrip_preserves_entry_side() -> None:
    material = _material(
        encoding=StrategySignalEncodingClassV1.ENTRY_EXIT_EVENT_V1,
        cycle=1,
        event=StrategyAgreementEventKindV1.ENTRY,
        entry_side=StrategyEntrySideCarrierV1.SHORT,
    )
    payload = serialize_strategy_suitability_agreement_material_v1(material)
    assert payload["entry_side"] == "SHORT"
    restored = deserialize_strategy_suitability_agreement_material_v1(payload)
    assert restored.entry_side is StrategyEntrySideCarrierV1.SHORT
    assert restored.material_digest == material.material_digest
    assert resolve_agreement_bound_directional_cycle_v1(restored) == -1


def test_legacy_payload_missing_entry_side_deserializes_to_none() -> None:
    material = _material(
        encoding=StrategySignalEncodingClassV1.ENTRY_EXIT_EVENT_V1,
        cycle=1,
        event=StrategyAgreementEventKindV1.ENTRY,
        entry_side=StrategyEntrySideCarrierV1.NONE,
    )
    payload = serialize_strategy_suitability_agreement_material_v1(material)
    del payload["entry_side"]
    restored = deserialize_strategy_suitability_agreement_material_v1(payload)
    assert restored.entry_side is StrategyEntrySideCarrierV1.NONE
    assert resolve_agreement_bound_directional_cycle_v1(restored) is None


def test_invalid_entry_side_fail_closed() -> None:
    material = _material(
        encoding=StrategySignalEncodingClassV1.ENTRY_EXIT_EVENT_V1,
        cycle=1,
        event=StrategyAgreementEventKindV1.ENTRY,
        entry_side=StrategyEntrySideCarrierV1.NONE,
    )
    payload = serialize_strategy_suitability_agreement_material_v1(material)
    payload["entry_side"] = "BULL"
    with pytest.raises(StrategySuitabilityAgreementErrorV1, match="material_deserialize"):
        deserialize_strategy_suitability_agreement_material_v1(payload)


def test_positional_encoding_rejects_explicit_entry_side() -> None:
    with pytest.raises(StrategySuitabilityAgreementErrorV1, match="entry_side_encoding_mismatch"):
        _material(
            encoding=StrategySignalEncodingClassV1.POSITIONAL_LS_STATE_V1,
            cycle=1,
            strategy_id="rsi_reversion",
            entry_side=StrategyEntrySideCarrierV1.LONG,
        )


def test_adapter_legacy_producers_default_entry_side_none() -> None:
    material = normalize_strategy_signal_to_suitability_agreement_material_v1(
        _binding(
            [1, 0, -1],
            provenance=_provenance(
                configured_strategy_id="bollinger_bands",
                executed_strategy_id="bollinger_bands",
            ),
        ),
        instrument_id="inst-eth-usdt-perp",
        trading_epoch=0,
    )
    assert material.encoding_class is StrategySignalEncodingClassV1.ENTRY_EXIT_EVENT_V1
    assert material.event_kind is StrategyAgreementEventKindV1.ENTRY
    assert material.cycle_signal_value == 1
    assert material.entry_side is StrategyEntrySideCarrierV1.NONE
    assert resolve_agreement_bound_directional_cycle_v1(material) is None


def test_bollinger_panel_baseline_predicate_unchanged_without_carrier() -> None:
    """Contract-universal baseline: 185× FF_DA_FLAT_PATH while Bollinger emits NONE."""
    assert _PANEL_ENTRY_BASELINE == 185
    assert _FIRST_FALSE_PREDICATE_ID == "FF_DA_FLAT_PATH_ENTRY_EXIT_NO_SIDE_CARRIER_V1"
    material = _material(
        encoding=StrategySignalEncodingClassV1.ENTRY_EXIT_EVENT_V1,
        cycle=1,
        event=StrategyAgreementEventKindV1.ENTRY,
        entry_side=StrategyEntrySideCarrierV1.NONE,
        strategy_id="bollinger_bands",
    )
    assert resolve_agreement_bound_directional_cycle_v1(material) is None
    path = project_mv2_agreement_bound_price_path_v1(mark_price=0.25, material=material)
    assert path == (0.25, 0.25)
    strength = compute_signal_strength(
        price_path=path, side=DirectionalAssessmentSide.LONG, reference_price=0.25
    )
    assert strength == pytest.approx(0.0)


def test_digest_changes_when_entry_side_changes() -> None:
    none_mat = _material(
        encoding=StrategySignalEncodingClassV1.ENTRY_EXIT_EVENT_V1,
        cycle=1,
        event=StrategyAgreementEventKindV1.ENTRY,
        entry_side=StrategyEntrySideCarrierV1.NONE,
    )
    long_mat = _material(
        encoding=StrategySignalEncodingClassV1.ENTRY_EXIT_EVENT_V1,
        cycle=1,
        event=StrategyAgreementEventKindV1.ENTRY,
        entry_side=StrategyEntrySideCarrierV1.LONG,
    )
    assert none_mat.material_digest != long_mat.material_digest


def test_replace_missing_attr_defaults_none_on_legacy_shaped_object() -> None:
    """getattr fallback: objects without entry_side remain fail-closed."""
    material = _material(
        encoding=StrategySignalEncodingClassV1.ENTRY_EXIT_EVENT_V1,
        cycle=1,
        event=StrategyAgreementEventKindV1.ENTRY,
        entry_side=StrategyEntrySideCarrierV1.NONE,
    )
    # Simulates a pre-extension consumer that only sees known fields.
    stripped = replace(material)
    assert getattr(stripped, "entry_side") is StrategyEntrySideCarrierV1.NONE
