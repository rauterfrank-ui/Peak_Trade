"""Hermetic tests for Stage-1 shadow formula producers."""

from __future__ import annotations

import math

from trading.master_v2.fps_atr_or_range_wilder_atr_finalized_ohlcv_v1 import (
    FORMULA_ID as ATR_ID,
    PRODUCTIVE_ACTIVATION as ATR_PA,
    compute_fps_atr_or_range_wilder_atr_finalized_ohlcv_v1,
)
from trading.master_v2.fps_opportunity_score_fee_slippage_breakeven_movement_v1 import (
    FORMULA_ID as OPP_ID,
    PRODUCTIVE_ACTIVATION as OPP_PA,
    compute_fps_opportunity_score_fee_slippage_breakeven_movement_v1,
)
from trading.master_v2.fps_realized_volatility_population_stdev_mark_log_returns_v1 import (
    FORMULA_ID as RV_ID,
    PRODUCTIVE_ACTIVATION as RV_PA,
    compute_fps_realized_volatility_population_stdev_mark_log_returns_v1,
)
from trading.master_v2.fps_sequence_path_survival_ratio_prearm_path_fraction_v1 import (
    FORMULA_ID as PATH_ID,
    PRODUCTIVE_ACTIVATION as PATH_PA,
    compute_fps_sequence_path_survival_ratio_prearm_path_fraction_v1,
)
from trading.master_v2.shadow_futures_input_freshness_age_collector_v1 import (
    PRODUCTIVE_ACTIVATION as AGE_PA,
    collect_shadow_futures_input_freshness_age_v1,
)
from trading.master_v2.shadow_sequence_survival_metrics_producer_v1 import (
    PRODUCTIVE_ACTIVATION as SEQ_PA,
    produce_shadow_sequence_survival_metrics_v1,
)
from trading.master_v2.shadow_survival_envelope_assembler_v1 import (
    PRODUCTIVE_ACTIVATION as ENV_PA,
    assemble_shadow_survival_envelope_v1,
)

from src.ops.productive_pure_stack_numeric_policy_shadow_campaign_v1.models_v1 import (
    FinalizedBarV1,
    ShadowAvailabilityV1,
)


def _bars(
    n: int, *, finalized: bool = True, start: int = 1_700_000_000
) -> tuple[FinalizedBarV1, ...]:
    out: list[FinalizedBarV1] = []
    for i in range(n):
        price = 100.0 + 0.01 * i
        out.append(
            FinalizedBarV1(
                instrument_id="TEST-INST",
                event_time_epoch_s=start + i * 60,
                open=price,
                high=price + 0.2,
                low=price - 0.2,
                close=price,
                mark_price=price,
                volume=1.0,
                finalized=finalized,
                dataset_id="d1",
                source_id="s1",
            )
        )
    return tuple(out)


def test_formula_ids_and_shadow_flags() -> None:
    assert RV_ID == "fps_realized_volatility.population_stdev_mark_log_returns.v1"
    assert ATR_ID == "fps_atr_or_range.wilder_atr_finalized_ohlcv.v1"
    assert OPP_ID == "fps_opportunity_score.fee_slippage_breakeven_movement.v1"
    assert PATH_ID == "fps_sequence_path_survival_ratio.prearm_path_fraction.v1"
    assert RV_PA is False and ATR_PA is False and OPP_PA is False and PATH_PA is False
    assert SEQ_PA is False and ENV_PA is False and AGE_PA is False


def test_realized_vol_available_and_deterministic() -> None:
    bars = _bars(61)
    a = compute_fps_realized_volatility_population_stdev_mark_log_returns_v1(bars)
    b = compute_fps_realized_volatility_population_stdev_mark_log_returns_v1(bars)
    assert a.status is ShadowAvailabilityV1.AVAILABLE
    assert a.value is not None and a.value >= 0.0
    assert a.input_digest == b.input_digest
    assert a.value == b.value
    assert a.productive_activation is False
    assert a.provisional is True


def test_realized_vol_rejects_non_finalized_and_lookahead() -> None:
    assert (
        compute_fps_realized_volatility_population_stdev_mark_log_returns_v1(
            _bars(61, finalized=False)
        ).status
        is ShadowAvailabilityV1.REJECTED
    )
    bars = list(_bars(61))
    bars[10] = FinalizedBarV1(
        **{**bars[10].__dict__, "event_time_epoch_s": bars[9].event_time_epoch_s - 1}
    )
    assert (
        compute_fps_realized_volatility_population_stdev_mark_log_returns_v1(bars).status
        is ShadowAvailabilityV1.REJECTED
    )


def test_atr_warmup_and_missing() -> None:
    assert (
        compute_fps_atr_or_range_wilder_atr_finalized_ohlcv_v1(_bars(5)).status
        is ShadowAvailabilityV1.UNAVAILABLE
    )
    obs = compute_fps_atr_or_range_wilder_atr_finalized_ohlcv_v1(_bars(15))
    assert obs.status is ShadowAvailabilityV1.AVAILABLE
    assert obs.value is not None and obs.value > 0.0


def test_opportunity_missing_never_defaults_to_zero() -> None:
    obs = compute_fps_opportunity_score_fee_slippage_breakeven_movement_v1(
        recent_abs_log_return=None,
        fee_bps=1.0,
        slippage_bps=1.0,
    )
    assert obs.status is ShadowAvailabilityV1.UNAVAILABLE
    assert obs.value is None

    ok = compute_fps_opportunity_score_fee_slippage_breakeven_movement_v1(
        recent_abs_log_return=0.01,
        fee_bps=2.0,
        slippage_bps=2.0,
    )
    assert ok.status is ShadowAvailabilityV1.AVAILABLE
    assert ok.value is not None
    assert 0.0 <= ok.value <= 1.0
    assert not math.isnan(ok.value)


def test_path_survival_fraction() -> None:
    obs = compute_fps_sequence_path_survival_ratio_prearm_path_fraction_v1(
        (True, True, False, True)
    )
    assert obs.status is ShadowAvailabilityV1.AVAILABLE
    assert obs.value == 0.75
    missing = compute_fps_sequence_path_survival_ratio_prearm_path_fraction_v1(None)
    assert missing.status is ShadowAvailabilityV1.UNAVAILABLE
    assert missing.value is None


def test_sequence_metrics_producer_partial_unavailable() -> None:
    partial = produce_shadow_sequence_survival_metrics_v1(
        explicit_metrics={"early_loss_toxicity": 0.1}
    )
    assert partial.status is ShadowAvailabilityV1.UNAVAILABLE
    assert partial.productive_activation is False


def test_envelope_assembler_rejects_limits_binding() -> None:
    assembled = assemble_shadow_survival_envelope_v1(limits={"min_path_survival_ratio": 0.5})
    assert assembled.status is ShadowAvailabilityV1.REJECTED
    assert assembled.envelope is None
    assert assembled.productive_activation is False


def test_freshness_age_event_time_only() -> None:
    bar = _bars(1)[0]
    ok = collect_shadow_futures_input_freshness_age_v1(
        bar=bar,
        as_of_event_time_epoch_s=bar.event_time_epoch_s + 120,
    )
    assert ok.status is ShadowAvailabilityV1.AVAILABLE
    assert ok.age_seconds == 120
    bad = collect_shadow_futures_input_freshness_age_v1(
        bar=bar,
        as_of_event_time_epoch_s=bar.event_time_epoch_s - 1,
    )
    assert bad.status is ShadowAvailabilityV1.REJECTED
    assert bad.age_seconds is None
