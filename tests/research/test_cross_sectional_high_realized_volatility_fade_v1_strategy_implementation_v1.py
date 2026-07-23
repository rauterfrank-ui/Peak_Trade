"""Focused tests for CSHRVF strategy implementation, exits, ranking, and binding."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from src.research.cross_sectional_high_realized_volatility_fade_v1_exit_state_machine_v1 import (
    CS_VOL_RANK_NORMALIZATION_PERCENTILE_LT_V1,
    EXIT_PRECEDENCE_ASCENDING_WINS_FIRST_V1,
    REGIME_INVALIDATION_CS_RV_RANK_PERCENTILE_LT_V1,
    TIME_EXIT_MAX_BARS_V1,
    TRAILING_STOP_FORBIDDEN_V1,
    CshrvfExitReasonV1,
    entry_exit_reachable_ex_ante_v1,
    evaluate_exit_on_bar_v1,
    open_position_from_fill_v1,
)
from src.research.cross_sectional_high_realized_volatility_fade_v1_strategy_implementation_binding_v1 import (
    REQUIRED_DIGEST,
    load_and_validate_repo_binding,
)
from src.research.cross_sectional_high_realized_volatility_fade_v1_strategy_v1 import (
    BTC_EXCLUDED_V1,
    EXIT_PARAMS_V1,
    EXIT_STATE_MACHINE_IMPLEMENTED_V1,
    HIGH_RANK_MIN_CONSECUTIVE_BARS_V1,
    HIGH_RANK_PERCENTILE_INCLUSIVE_MIN_V1,
    HYPOTHESIS_ID_V1,
    LOW_CROSS_SECTIONAL_VOL_ENTRY_FORBIDDEN_IN_V1,
    NO_CHANNEL_BREAKOUT_REQUIRED_V1,
    PREDECESSOR_STRATEGY_ID_V1,
    PRODUCTIVE_EXIT_PNL_EVALUATOR_REF_V1,
    REARM_RANK_PERCENTILE_STRICTLY_BELOW_V1,
    SPOT_EXCLUDED_V1,
    STRATEGY_IDENTITY_V1,
    VTDC_DEPRESSED_CONTINUATION_ENTRY_FORBIDDEN_V1,
    CshrvfEventV1,
    CshrvfReasonV1,
    generate_cshrvf_events_and_roundtrips_v1,
)
from src.research.cross_sectional_high_realized_volatility_fade_v1_vol_state_v1 import (
    PANEL_MEMBERS_REQUIRED_MIN_V1,
    PERCENTILE_TIE_METHOD_V1,
    RV_PERIOD_V1,
    VOL_ESTIMATOR_FAMILY_V1,
    compute_cross_sectional_rv_level_rank_at_timestamp_v1,
    compute_cross_sectional_rv_rank_wide_panel_v1,
    compute_realized_volatility_24_v1,
    is_bitcoin_instrument_v1,
    is_cshrvf_eligible_instrument_v1,
    is_spot_instrument_v1,
)
import src.research.cross_sectional_high_realized_volatility_fade_v1_strategy_v1 as strat

from src.trading.master_v2.strategy_suitability_agreement_material_v1 import (
    StrategyEntrySideCarrierV1,
)

REPO = Path(__file__).resolve().parents[2]
CONTRACT = (
    REPO
    / "config/research/cross_sectional_high_realized_volatility_fade_v1_preregistered_economic_hypothesis_measurement_contract_v1.json"
)


def _synthetic_frame(n: int = 260, *, uptrend: bool = True) -> pd.DataFrame:
    idx = pd.date_range("2022-01-01", periods=n, freq="h", tz="UTC")
    drift = np.linspace(0, 2.0, n) if uptrend else np.linspace(2.0, 0, n)
    close = pd.Series(100.0, index=idx, dtype=float) + pd.Series(drift, index=idx)
    return pd.DataFrame(
        {"open": close.copy(), "high": close + 1.0, "low": close - 1.0, "close": close}
    )


def test_import_safety_and_binding() -> None:
    report = load_and_validate_repo_binding(REPO)
    assert report["valid"] is True
    assert report["exit_state_machine_implemented"] is True
    assert report["evaluation_authorized"] is False
    assert report["development_evaluation_authorized"] is False
    assert report["frozen_measurement_contract_digest"] == REQUIRED_DIGEST
    assert report["development_run_count"] == 0
    assert STRATEGY_IDENTITY_V1 == "CROSS_SECTIONAL_HIGH_REALIZED_VOLATILITY_FADE_V1"
    assert HYPOTHESIS_ID_V1 == (
        "CROSS_SECTIONAL_HIGH_REALIZED_VOLATILITY_FADE_NON_BITCOIN_PERPETUALS_V1"
    )
    assert PREDECESSOR_STRATEGY_ID_V1 == "VOLATILITY_TERM_STRUCTURE_DEPRESSED_CONTINUATION_V1"
    assert RV_PERIOD_V1 == 24
    assert VOL_ESTIMATOR_FAMILY_V1 == "REALIZED_VOLATILITY_CROSS_SECTIONAL_RANK"
    assert PERCENTILE_TIE_METHOD_V1 == "WEAK_LESS_THAN_OR_EQUAL_EMPIRICAL_CDF"
    assert PANEL_MEMBERS_REQUIRED_MIN_V1 == 10
    assert HIGH_RANK_MIN_CONSECUTIVE_BARS_V1 == 2
    assert HIGH_RANK_PERCENTILE_INCLUSIVE_MIN_V1 == 0.80
    assert REARM_RANK_PERCENTILE_STRICTLY_BELOW_V1 == 0.50
    assert LOW_CROSS_SECTIONAL_VOL_ENTRY_FORBIDDEN_IN_V1 is True
    assert NO_CHANNEL_BREAKOUT_REQUIRED_V1 is True
    assert VTDC_DEPRESSED_CONTINUATION_ENTRY_FORBIDDEN_V1 is True
    assert BTC_EXCLUDED_V1 is True
    assert SPOT_EXCLUDED_V1 is True
    assert EXIT_STATE_MACHINE_IMPLEMENTED_V1 is True
    assert TRAILING_STOP_FORBIDDEN_V1 is True
    assert EXIT_PARAMS_V1["trailing_stop_forbidden"] is True
    assert EXIT_PRECEDENCE_ASCENDING_WINS_FIRST_V1 == (
        "INITIAL_STOP",
        "CROSS_SECTIONAL_VOL_RANK_NORMALIZATION_INVALIDATION",
        "REGIME_INVALIDATION",
        "TIME_EXIT",
        "END_OF_INSTRUMENT_LIQUIDATION",
        "END_OF_PANEL_LIQUIDATION",
    )
    assert CS_VOL_RANK_NORMALIZATION_PERCENTILE_LT_V1 == 0.55
    assert REGIME_INVALIDATION_CS_RV_RANK_PERCENTILE_LT_V1 == 0.40
    assert TIME_EXIT_MAX_BARS_V1 == 48
    assert (REPO / PRODUCTIVE_EXIT_PNL_EVALUATOR_REF_V1).is_file()
    contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
    assert contract["strategy_implementation_present"] is False
    assert contract["development_run_count"] == 0
    assert contract["run_slot_consumed"] is False
    assert contract["contract_digest"] == REQUIRED_DIGEST


def test_realized_volatility_period_and_nan_warmup() -> None:
    idx = pd.date_range("2022-01-01", periods=30, freq="h", tz="UTC")
    close = pd.Series(np.linspace(100.0, 103.0, 30), index=idx, dtype=float)
    rv = compute_realized_volatility_24_v1(close)
    assert rv.isna().sum() == 24  # first return NaN + 23 incomplete windows
    assert np.isfinite(rv.iloc[24:]).all()


def test_cross_sectional_ranking_and_deterministic_tie_breaks() -> None:
    panel = {f"ALT{i}-USDT-SWAP": float(i) for i in range(1, 11)}  # 10 eligible instruments
    ranks = compute_cross_sectional_rv_level_rank_at_timestamp_v1(panel)
    assert ranks["ALT1-USDT-SWAP"] == pytest.approx(0.1)
    assert ranks["ALT10-USDT-SWAP"] == pytest.approx(1.0)
    # Exact ties: both instruments with equal RV share the same WEAK_LEQ rank.
    tied = {f"T{i}-USDT-SWAP": 1.0 for i in range(10)}
    tied_ranks = compute_cross_sectional_rv_level_rank_at_timestamp_v1(tied)
    assert all(v == pytest.approx(1.0) for v in tied_ranks.values())


def test_btc_and_spot_excluded_from_ranking_universe() -> None:
    assert is_bitcoin_instrument_v1("BTC-USDT-SWAP") is True
    assert is_spot_instrument_v1("ETH-USDT") is True
    assert is_cshrvf_eligible_instrument_v1("ETH-USDT-SWAP") is True
    assert is_cshrvf_eligible_instrument_v1("BTC-USDT-SWAP") is False
    assert is_cshrvf_eligible_instrument_v1("ETH-USDT") is False
    panel = {f"ALT{i}-USDT-SWAP": float(i) for i in range(1, 10)}
    panel["BTC-USDT-SWAP"] = 999.0
    panel["ETH-USDT"] = 888.0
    ranks = compute_cross_sectional_rv_level_rank_at_timestamp_v1(panel)
    # Only 9 eligible finite → insufficient cross-section.
    assert ranks["BTC-USDT-SWAP"] is None
    assert ranks["ETH-USDT"] is None
    assert all(ranks[k] is None for k in panel if k.endswith("-SWAP") and not k.startswith("BTC"))


def test_insufficient_cross_section_and_nan_handling() -> None:
    small = {f"ALT{i}-USDT-SWAP": float(i) for i in range(1, 10)}  # 9 < 10
    ranks = compute_cross_sectional_rv_level_rank_at_timestamp_v1(small)
    assert all(v is None for v in ranks.values())
    with_nan = {f"ALT{i}-USDT-SWAP": float(i) for i in range(1, 11)}
    with_nan["ALT5-USDT-SWAP"] = float("nan")
    ranks2 = compute_cross_sectional_rv_level_rank_at_timestamp_v1(with_nan)
    # 9 finite eligible → fail closed.
    assert all(v is None for v in ranks2.values())


def test_pit_same_timestamp_ranking_no_lookahead() -> None:
    idx = pd.date_range("2022-01-01", periods=3, freq="h", tz="UTC")
    cols = [f"ALT{i}-USDT-SWAP" for i in range(1, 11)]
    # t0 values low; t1 values high for ALT10 only — rank at t0 must ignore t1.
    data = pd.DataFrame(1.0, index=idx, columns=cols)
    data.loc[idx[1], "ALT10-USDT-SWAP"] = 100.0
    ranks = compute_cross_sectional_rv_rank_wide_panel_v1(data)
    assert ranks.loc[idx[0], "ALT10-USDT-SWAP"] == pytest.approx(1.0)
    assert ranks.loc[idx[1], "ALT10-USDT-SWAP"] == pytest.approx(1.0)
    # At t0 all equal → all ranks 1.0; changing future bar must not alter t0.
    assert ranks.loc[idx[0]].nunique() == 1


def test_ex_ante_reachability_gate() -> None:
    assert entry_exit_reachable_ex_ante_v1(signal_index=10, series_length=100) is True
    assert entry_exit_reachable_ex_ante_v1(signal_index=10, series_length=59) is False


def test_precedence_initial_stop_beats_normalization_and_regime() -> None:
    pos = open_position_from_fill_v1(
        side="LONG",
        fill_index=0,
        entry_price=100.0,
        atr_at_fill=1.0,
    )
    decision, _ = evaluate_exit_on_bar_v1(
        pos,
        bar_index=1,
        high=101.0,
        low=98.0,
        close=100.5,
        cs_rv_rank=0.20,
        is_last_instrument_bar=False,
        is_last_panel_bar=False,
    )
    assert decision is not None
    assert decision.reason is CshrvfExitReasonV1.INITIAL_STOP


def test_cs_vol_rank_normalization_beats_regime() -> None:
    pos = open_position_from_fill_v1(
        side="LONG",
        fill_index=0,
        entry_price=100.0,
        atr_at_fill=1.0,
    )
    decision, _ = evaluate_exit_on_bar_v1(
        pos,
        bar_index=1,
        high=101.0,
        low=99.5,
        close=100.2,
        cs_rv_rank=0.50,  # <0.55 and not <0.40
        is_last_instrument_bar=False,
        is_last_panel_bar=False,
    )
    assert decision is not None
    assert decision.reason is CshrvfExitReasonV1.CROSS_SECTIONAL_VOL_RANK_NORMALIZATION_INVALIDATION


def test_fade_short_after_positive_short_horizon_return(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    frame = _synthetic_frame(260, uptrend=True)
    ranks = pd.Series(0.60, index=frame.index, dtype=float)
    ranks.iloc[50] = 0.85
    ranks.iloc[51] = 0.90
    monkeypatch.setattr(strat, "compute_atr14_v1", lambda h, l, c: pd.Series(1.0, index=c.index))
    events, roundtrips = generate_cshrvf_events_and_roundtrips_v1(frame, cs_rv_rank=ranks)
    entries = [e for e in events if e.event is CshrvfEventV1.ENTRY_EVENT]
    assert len(entries) == 1
    assert entries[0].entry_side is StrategyEntrySideCarrierV1.SHORT
    assert entries[0].signal_index == 51
    assert entries[0].short_horizon_signed_return is not None
    assert entries[0].short_horizon_signed_return > 0.0
    assert len(roundtrips) >= 1
    assert roundtrips[0].side == "SHORT"
    assert roundtrips[0].fill_index == 52


def test_fade_long_after_negative_short_horizon_return(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    frame = _synthetic_frame(260, uptrend=False)
    ranks = pd.Series(0.60, index=frame.index, dtype=float)
    ranks.iloc[50] = 0.85
    ranks.iloc[51] = 0.90
    monkeypatch.setattr(strat, "compute_atr14_v1", lambda h, l, c: pd.Series(1.0, index=c.index))
    events, roundtrips = generate_cshrvf_events_and_roundtrips_v1(frame, cs_rv_rank=ranks)
    entries = [e for e in events if e.event is CshrvfEventV1.ENTRY_EVENT]
    assert len(entries) == 1
    assert entries[0].entry_side is StrategyEntrySideCarrierV1.LONG
    assert entries[0].short_horizon_signed_return is not None
    assert entries[0].short_horizon_signed_return < 0.0
    assert roundtrips[0].side == "LONG"


def test_neutral_when_not_high_rank(monkeypatch: pytest.MonkeyPatch) -> None:
    frame = _synthetic_frame(220, uptrend=True)
    ranks = pd.Series(0.60, index=frame.index, dtype=float)
    monkeypatch.setattr(strat, "compute_atr14_v1", lambda h, l, c: pd.Series(1.0, index=c.index))
    events, roundtrips = generate_cshrvf_events_and_roundtrips_v1(frame, cs_rv_rank=ranks)
    assert all(e.event is CshrvfEventV1.NONE for e in events)
    assert roundtrips == []


def test_nan_cs_rank_is_warmup_or_insufficient(monkeypatch: pytest.MonkeyPatch) -> None:
    frame = _synthetic_frame(80, uptrend=True)
    ranks = pd.Series(np.nan, index=frame.index, dtype=float)
    monkeypatch.setattr(strat, "compute_atr14_v1", lambda h, l, c: pd.Series(1.0, index=c.index))
    events, roundtrips = generate_cshrvf_events_and_roundtrips_v1(frame, cs_rv_rank=ranks)
    assert roundtrips == []
    assert all(
        e.reason in (CshrvfReasonV1.WARMUP, CshrvfReasonV1.INSUFFICIENT_CROSS_SECTION)
        for e in events
    )


def test_costs_and_execution_pipeline_binding_literals() -> None:
    contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
    costs = contract["costs"]
    assert costs["fee_bps_per_side"] == 10.0
    assert costs["slippage_bps_per_side"] == 5.0
    assert costs["canonical_cost_multiplier"] == 1.0
    exits = contract["exit_semantics"]
    assert exits["productive_exit_pnl_evaluator_ref"] == PRODUCTIVE_EXIT_PNL_EVALUATOR_REF_V1
    assert exits["reuse_canonical_fees_slippage_stop_risk_sizing_execution"] is True
    assert exits["trailing_stop_forbidden"] is True
    assert (
        EXIT_PARAMS_V1["productive_exit_pnl_evaluator_ref"] == PRODUCTIVE_EXIT_PNL_EVALUATOR_REF_V1
    )


def test_governance_registry_and_owner_map_consistency() -> None:
    owners = json.loads(
        (
            REPO
            / "config/governance/economic_diagnostic_optimization_boundary_canonical_owner_map_v0.json"
        ).read_text(encoding="utf-8")
    )["allowed_optimization_surfaces"]
    assert (
        "CROSS_SECTIONAL_HIGH_REALIZED_VOLATILITY_FADE_V1_STRATEGY_IMPLEMENTATION_ONLY_V1" in owners
    )
    program = json.loads(
        (REPO / "config/research/volatility_regime_research_program_v1.json").read_text(
            encoding="utf-8"
        )
    )
    assert program["strategy_implementation_present"] is True
    assert program["development_run_count"] == 0
    assert program["evaluation_authorized"] is False
    backlog = json.loads(
        (REPO / "config/research/volatility_regime_hypothesis_backlog_v1.json").read_text(
            encoding="utf-8"
        )
    )
    hyp = backlog["preregistered_hypotheses"][0]
    assert hyp["implementation_present"] is True
    assert hyp["development_run_count"] == 0
    assert hyp["status"] == "STRATEGY_IMPLEMENTATION_PRESENT_EVALUATION_UNAUTHORIZED"
