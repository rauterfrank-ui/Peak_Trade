"""Unit/contract tests for CS path-efficiency continuation v1 score/selection."""

from __future__ import annotations

from pathlib import Path

import pytest

from src.research.cross_sectional_path_efficiency_continuation_v1_score_v1 import (
    DEFAULT_LOOKBACK_N,
    DEFAULT_REBALANCE_INTERVAL_BARS,
    DEFAULT_SIGNAL_LAG_BARS,
    POLARITY,
    SCORE_FORMULA_VERSION,
    VOL_NORMALIZATION,
    compute_instrument_score_v1,
    compute_net_and_path_sum_v1,
    compute_path_efficiency_score_components_v1,
    is_eligible_universe_instrument_v1,
    rank_scores_deterministic_v1,
    validate_lookback_n,
)
from src.research.cross_sectional_path_efficiency_continuation_v1_selection_v1 import (
    DIRECTIONAL_FORM,
    SELECTION_MODE,
    TIE_BREAK_POLICY,
    RankIntentSideV1,
    resolve_symmetric_top1_sign_v1,
    select_single_top1_rank_intent_v1,
)
from src.research.cross_sectional_path_efficiency_continuation_v1_strategy_implementation_binding_v1 import (
    REQUIRED_DIGEST,
    load_and_validate_repo_binding,
)

REPO = Path(__file__).resolve().parents[2]
CSRHR_BACKLOG = (
    REPO
    / "config/research/cross_sectional_short_horizon_return_reversal_hypothesis_backlog_v1.json"
)
PROGRAM = (
    REPO / "config/research/cross_sectional_path_efficiency_continuation_research_program_v1.json"
)
CONTRACT = (
    REPO
    / "config/research/cross_sectional_path_efficiency_continuation_v1_preregistered_economic_hypothesis_measurement_contract_v1.json"
)


def _closes_smooth_up(start: float = 100.0, n: int = 80, step: float = 1.01) -> tuple[float, ...]:
    values = [start]
    for _ in range(n - 1):
        values.append(values[-1] * step)
    return tuple(values)


def _closes_choppy(start: float = 100.0, n: int = 80, amp: float = 0.05) -> tuple[float, ...]:
    """Alternating up/down path with small net move (low path efficiency)."""
    values = [start]
    for i in range(n - 1):
        factor = 1.0 + amp if i % 2 == 0 else 1.0 - amp
        values.append(values[-1] * factor)
    return tuple(values)


def _closes_flat(start: float = 100.0, n: int = 80) -> tuple[float, ...]:
    return tuple(start for _ in range(n))


def _closes_with_nan(n: int = 80) -> tuple[float, ...]:
    values = list(_closes_smooth_up(n=n))
    values[n // 2] = float("nan")
    return tuple(values)


def test_score_formula_and_frozen_parameters() -> None:
    assert (
        SCORE_FORMULA_VERSION == "path_efficiency_ratio_times_sign_net_log_return_fixed_lookback_v1"
    )
    assert POLARITY == "PATH_EFFICIENCY_CONTINUATION_ER_TIMES_SIGN"
    assert VOL_NORMALIZATION is False
    assert DEFAULT_LOOKBACK_N == 48
    assert DEFAULT_REBALANCE_INTERVAL_BARS == 8
    assert DEFAULT_SIGNAL_LAG_BARS == 1
    assert SELECTION_MODE == "single_top1_by_score_desc"
    assert TIE_BREAK_POLICY == "score_desc_then_instrument_id_asc"
    assert DIRECTIONAL_FORM == "D_MUTUALLY_EXCLUSIVE_DIRECTIONAL_SELECTION"


def test_path_efficiency_computation_and_continuation_score() -> None:
    closes = _closes_smooth_up(n=80, step=1.01)
    epoch = 60
    lookback = 48
    lag = 1
    components = compute_path_efficiency_score_components_v1(
        closes, lookback_n=lookback, signal_lag_bars=lag, epoch_index=epoch
    )
    assert components is not None
    score, er, net, path_sum = components
    assert path_sum > 0.0
    assert net > 0.0
    assert er == pytest.approx(abs(net) / path_sum)
    assert score == pytest.approx(er)  # positive continuation
    # Smooth monotonic path → ER near 1.0
    assert er == pytest.approx(1.0, abs=1e-12)

    net_path = compute_net_and_path_sum_v1(
        closes, lookback_n=lookback, signal_lag_bars=lag, epoch_index=epoch
    )
    assert net_path is not None
    assert net_path[0] == pytest.approx(net)
    assert net_path[1] == pytest.approx(path_sum)


def test_choppy_path_has_lower_efficiency_than_smooth() -> None:
    smooth = _closes_smooth_up(n=80, step=1.005)
    choppy = _closes_choppy(n=80, amp=0.03)
    epoch = 60
    s = compute_path_efficiency_score_components_v1(
        smooth, lookback_n=48, signal_lag_bars=1, epoch_index=epoch
    )
    c = compute_path_efficiency_score_components_v1(
        choppy, lookback_n=48, signal_lag_bars=1, epoch_index=epoch
    )
    assert s is not None and c is not None
    assert abs(s[1]) > abs(c[1])


def test_universe_binding_non_bitcoin_perpetual_usdt() -> None:
    assert is_eligible_universe_instrument_v1("okx:linear_perpetual:ETH-USDT") is True
    assert is_eligible_universe_instrument_v1("okx:linear_perpetual:BTC-USDT") is False
    assert is_eligible_universe_instrument_v1("okx:spot:ETH-USDT") is False
    assert is_eligible_universe_instrument_v1("okx:linear_perpetual:ETH-USD") is False
    assert (
        compute_instrument_score_v1(
            "okx:linear_perpetual:BTC-USDT",
            _closes_smooth_up(),
            lookback_n=48,
            epoch_index=60,
        )
        is None
    )


def test_pit_safety_insufficient_history_and_lookahead_window() -> None:
    closes = _closes_smooth_up(n=40)
    # Need lookback + lag bars of history; epoch 40 with lookback 48 is insufficient.
    assert (
        compute_path_efficiency_score_components_v1(
            closes, lookback_n=48, signal_lag_bars=1, epoch_index=39
        )
        is None
    )
    # At epoch e, only closes through e-lag are used (no current-bar lookahead).
    long = _closes_smooth_up(n=80)
    epoch = 60
    lag = 1
    components = compute_path_efficiency_score_components_v1(
        long, lookback_n=48, signal_lag_bars=lag, epoch_index=epoch
    )
    assert components is not None
    # Mutating future closes beyond lag must not change score.
    mutated = list(long)
    mutated[epoch] = mutated[epoch] * 10.0
    components2 = compute_path_efficiency_score_components_v1(
        mutated, lookback_n=48, signal_lag_bars=lag, epoch_index=epoch
    )
    assert components2 is not None
    assert components2[0] == pytest.approx(components[0])


def test_nan_inf_zero_division_and_flat_path_ineligible() -> None:
    assert (
        compute_path_efficiency_score_components_v1(
            _closes_flat(), lookback_n=48, signal_lag_bars=1, epoch_index=60
        )
        is None
    )
    assert (
        compute_path_efficiency_score_components_v1(
            _closes_with_nan(), lookback_n=48, signal_lag_bars=1, epoch_index=60
        )
        is None
    )
    # Zero then rebound that yields path_sum>0 but net!=0 is fine; Inf closes fail.
    inf_closes = list(_closes_smooth_up())
    inf_closes[30] = float("inf")
    assert (
        compute_path_efficiency_score_components_v1(
            inf_closes, lookback_n=48, signal_lag_bars=1, epoch_index=60
        )
        is None
    )


def test_deterministic_tie_break_instrument_id_asc() -> None:
    # Two instruments with identical smooth paths → equal scores; tie-break by id asc.
    a = compute_instrument_score_v1(
        "okx:linear_perpetual:AAA-USDT",
        _closes_smooth_up(step=1.01),
        lookback_n=48,
        epoch_index=60,
    )
    b = compute_instrument_score_v1(
        "okx:linear_perpetual:BBB-USDT",
        _closes_smooth_up(step=1.01),
        lookback_n=48,
        epoch_index=60,
    )
    assert a is not None and b is not None
    assert a.score == pytest.approx(b.score)
    ranked = rank_scores_deterministic_v1([b, a])
    assert ranked[0].instrument_id == "okx:linear_perpetual:AAA-USDT"
    assert ranked[1].instrument_id == "okx:linear_perpetual:BBB-USDT"


def test_directional_form_d_symmetric_top1_sign() -> None:
    assert resolve_symmetric_top1_sign_v1(0.5) == RankIntentSideV1.LONG_TOP1
    assert resolve_symmetric_top1_sign_v1(-0.5) == RankIntentSideV1.SHORT_TOP1
    assert resolve_symmetric_top1_sign_v1(0.0) == RankIntentSideV1.FLAT
    assert resolve_symmetric_top1_sign_v1(float("nan")) == RankIntentSideV1.FLAT


def test_continuation_selection_prefers_higher_path_efficiency() -> None:
    closes = {
        "okx:linear_perpetual:ETH-USDT": _closes_choppy(amp=0.04),
        "okx:linear_perpetual:SOL-USDT": _closes_smooth_up(step=1.008),
        "okx:linear_perpetual:AVAX-USDT": _closes_choppy(amp=0.03),
        "okx:linear_perpetual:LINK-USDT": _closes_choppy(amp=0.05),
        "okx:linear_perpetual:DOT-USDT": _closes_choppy(amp=0.02),
    }
    intent = select_single_top1_rank_intent_v1(closes, epoch_index=56)
    assert intent.selection_emitted is True
    assert intent.insufficient_universe is False
    assert intent.selected_instrument_id == "okx:linear_perpetual:SOL-USDT"
    assert intent.intent_side == RankIntentSideV1.LONG_TOP1
    assert intent.double_play_remains_sole_authority is True

    held = select_single_top1_rank_intent_v1(closes, epoch_index=57, prior_intent=intent)
    assert held.selection_emitted is False
    assert held.selected_instrument_id == intent.selected_instrument_id


def test_short_top1_when_top_score_negative() -> None:
    # All-down cross-section: score=ER*sign is negative; score_desc picks algebraically
    # largest (least negative) top1 → SHORT_TOP1 under symmetric_top1_sign.
    down_smooth = _closes_smooth_up(start=200.0, step=0.992)  # ER~1 → score~-1
    down_choppy = []
    px = 200.0
    for i in range(80):
        down_choppy.append(px)
        px *= 0.995 if i % 2 == 0 else 0.999  # lower ER → score closer to 0
    closes = {
        "okx:linear_perpetual:ETH-USDT": tuple(down_smooth),
        "okx:linear_perpetual:SOL-USDT": tuple(down_choppy),
        "okx:linear_perpetual:AVAX-USDT": tuple(down_choppy),
        "okx:linear_perpetual:LINK-USDT": tuple(down_choppy),
        "okx:linear_perpetual:DOT-USDT": tuple(down_choppy),
    }
    intent = select_single_top1_rank_intent_v1(closes, epoch_index=56)
    assert intent.selection_emitted is True
    assert intent.intent_side == RankIntentSideV1.SHORT_TOP1
    assert intent.top_score is not None and intent.top_score < 0.0
    # Choppy downs outrank smooth down under score_desc (e.g. -0.2 > -1.0).
    assert intent.selected_instrument_id != "okx:linear_perpetual:ETH-USDT"
    assert intent.selected_instrument_id is not None


def test_insufficient_universe_and_frozen_param_fail_closed() -> None:
    closes = {
        "okx:linear_perpetual:ETH-USDT": _closes_smooth_up(),
        "okx:linear_perpetual:SOL-USDT": _closes_smooth_up(step=1.02),
    }
    intent = select_single_top1_rank_intent_v1(closes, epoch_index=56)
    assert intent.insufficient_universe is True
    assert intent.intent_side == RankIntentSideV1.FLAT
    assert validate_lookback_n(24) is False
    with pytest.raises(ValueError, match="LOOKBACK_N_NOT_FROZEN_PARAMETER"):
        select_single_top1_rank_intent_v1(closes, epoch_index=56, lookback_n=24)


def test_empty_cross_section_fail_closed() -> None:
    intent = select_single_top1_rank_intent_v1({}, epoch_index=56)
    assert intent.insufficient_universe is True
    assert intent.selected_instrument_id is None
    assert intent.intent_side == RankIntentSideV1.FLAT


def test_implementation_binding_guards_and_csrhr_unchanged() -> None:
    import json

    report = load_and_validate_repo_binding(REPO)
    assert report["valid"] is True
    assert report["strategy_implementation_present"] is True
    assert report["evaluation_authorized"] is False
    assert report["development_run_count"] == 0
    assert report["holdout_authorized"] is False
    assert report["frozen_digest"] == REQUIRED_DIGEST
    assert report["csrhr_unchanged"] is True

    csrhr = json.loads(CSRHR_BACKLOG.read_text(encoding="utf-8"))
    assert csrhr["status"] == "OPEN_BACKLOG"
    assert csrhr["development_run_count"] == 0

    program = json.loads(PROGRAM.read_text(encoding="utf-8"))
    assert program["development_run_count"] == 0
    assert program["evaluation_authorized"] is False
    assert program["strategy_implementation_present"] is False

    contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
    assert contract["development_run_count"] == 0
    assert contract["evaluation_authorized"] is False
    assert contract["strategy_implementation_present"] is False
    assert contract["contract_digest"] == REQUIRED_DIGEST


def test_evaluation_path_not_imported_or_callable_in_impl_modules() -> None:
    score_src = (
        REPO / "src/research/cross_sectional_path_efficiency_continuation_v1_score_v1.py"
    ).read_text(encoding="utf-8")
    selection_src = (
        REPO / "src/research/cross_sectional_path_efficiency_continuation_v1_selection_v1.py"
    ).read_text(encoding="utf-8")
    binding_src = (
        REPO
        / "src/research/cross_sectional_path_efficiency_continuation_v1_strategy_implementation_binding_v1.py"
    ).read_text(encoding="utf-8")
    forbidden_snippets = (
        "run_evaluate_cross_sectional_path_efficiency",
        "development_evaluation_v1",
        "evaluate_path_v1",
        "from src.research.cross_sectional_path_efficiency_continuation_v1_development_evaluation",
        "importlib.import_module",
    )
    for src in (score_src, selection_src, binding_src):
        for snippet in forbidden_snippets:
            assert snippet not in src
        assert "runner_start" not in score_src
        assert "runner_start" not in selection_src
