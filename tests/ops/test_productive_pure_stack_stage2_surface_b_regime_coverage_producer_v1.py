"""Dedicated Surface-B regime-coverage producer contract tests."""

from __future__ import annotations

import pytest

from src.ops.productive_pure_stack_stage2_surface_b_regime_coverage_producer_v1.constants_v1 import (
    AUTHORIZE_DETAIL_FIELD_VALUES,
    TAXONOMY_SINK_LABELS,
    VERSIONED_PRODUCER_ID,
)
from src.ops.productive_pure_stack_stage2_surface_b_regime_coverage_producer_v1.determinism_contract_v1 import (
    assert_deterministic_reproduction_v1,
)
from src.ops.productive_pure_stack_stage2_surface_b_regime_coverage_producer_v1.models_v1 import (
    RegimeCoverageBarInputV1,
    RegimeCoverageProducerErrorV1,
)
from src.ops.productive_pure_stack_stage2_surface_b_regime_coverage_producer_v1.producer_v1 import (
    produce_regime_coverage_labels_v1,
)
from src.ops.productive_pure_stack_stage2_surface_b_regime_coverage_producer_v1.reproducibility_contract_v1 import (
    reproducibility_record_v1,
)


def _bar(et: int, *, instrument_id: str = "ETH-USDT-SWAP") -> RegimeCoverageBarInputV1:
    return RegimeCoverageBarInputV1(
        instrument_id=instrument_id,
        event_time_epoch_s=et,
        open=100.0,
        high=101.0,
        low=99.0,
        close=100.5,
        mark_price=100.4,
        volume=12.0,
        finalized=True,
    )


def test_producer_emits_missing_when_thresholds_unset_v1() -> None:
    t0 = 1_700_000_040  # aligned PT1M bucket open
    bars = (_bar(t0), _bar(t0 + 60))
    result = produce_regime_coverage_labels_v1(
        instrument_id="ETH-USDT-SWAP",
        as_of_event_time_epoch_s=t0 + 60,
        bars=bars,
    )
    assert result.versioned_producer_id == VERSIONED_PRODUCER_ID
    assert result.coverage_counts is None
    assert result.regime_coverage_instance is None
    assert result.productive_emission is False
    assert tuple(result.taxonomy_sink_labels) == TAXONOMY_SINK_LABELS
    assert {o.label for o in result.observations} == {"missing"}
    assert all(
        o.reason == "OWNER_NUMERIC_THRESHOLD_AND_LOOKBACK_UNSET" for o in result.observations
    )
    record = reproducibility_record_v1(result)
    assert record["coverage_counts"] is None
    assert record["input_authority"] is False


def test_producer_rejects_lookahead_v1() -> None:
    t0 = 1_700_000_040
    bars = (_bar(t0), _bar(t0 + 120))
    with pytest.raises(RegimeCoverageProducerErrorV1, match="LOOKAHEAD_FORBIDDEN"):
        produce_regime_coverage_labels_v1(
            instrument_id="ETH-USDT-SWAP",
            as_of_event_time_epoch_s=t0 + 60,
            bars=bars,
        )


def test_producer_rejects_unfinalized_and_multi_instrument_v1() -> None:
    t0 = 1_700_000_040
    bad = RegimeCoverageBarInputV1(
        instrument_id="ETH-USDT-SWAP",
        event_time_epoch_s=t0,
        open=100.0,
        high=101.0,
        low=99.0,
        close=100.5,
        mark_price=100.4,
        volume=12.0,
        finalized=False,
    )
    with pytest.raises(RegimeCoverageProducerErrorV1, match="UNFINALIZED_BAR_FORBIDDEN"):
        produce_regime_coverage_labels_v1(
            instrument_id="ETH-USDT-SWAP",
            as_of_event_time_epoch_s=t0,
            bars=(bad,),
        )
    with pytest.raises(RegimeCoverageProducerErrorV1, match="MULTI_INSTRUMENT_FORBIDDEN"):
        produce_regime_coverage_labels_v1(
            instrument_id="ETH-USDT-SWAP",
            as_of_event_time_epoch_s=t0,
            bars=(_bar(t0, instrument_id="OTHER"),),
        )


def test_producer_deterministic_digest_v1() -> None:
    t0 = 1_700_000_040
    bars = (_bar(t0), _bar(t0 + 60), _bar(t0 + 120))
    result = assert_deterministic_reproduction_v1(
        instrument_id="ETH-USDT-SWAP",
        as_of_event_time_epoch_s=t0 + 120,
        bars=bars,
    )
    assert len(result.producer_digest) == 64


def test_authorize_detail_field_values_bound_v1() -> None:
    assert AUTHORIZE_DETAIL_FIELD_VALUES["canonical_producer_name"]
    assert AUTHORIZE_DETAIL_FIELD_VALUES["versioned_producer_id"] == VERSIONED_PRODUCER_ID
    assert "low|mid|high|unknown|missing" in AUTHORIZE_DETAIL_FIELD_VALUES["taxonomy_binding"]
    assert AUTHORIZE_DETAIL_FIELD_VALUES["threshold_authority_ref"].endswith("UNSET_V1")
    assert AUTHORIZE_DETAIL_FIELD_VALUES["lookback_window_authority_ref"].endswith("UNSET_V1")
