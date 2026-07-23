"""Unit/contract tests for CS open-gap pressure fade v1 score and selection."""

from __future__ import annotations

import json
import math
import re
from pathlib import Path

import pytest

from src.research.cross_sectional_open_gap_pressure_fade_v1_hypothesis_preregistration_v1 import (
    compute_contract_digest,
)
from src.research.cross_sectional_open_gap_pressure_fade_v1_score_v1 import (
    DEFAULT_LOOKBACK_N,
    DEFAULT_REBALANCE_INTERVAL_BARS,
    DEFAULT_SIGNAL_LAG_BARS,
    POLARITY,
    SCORE_FORMULA_VERSION,
    VOL_NORMALIZATION,
    compute_bar_open_gap_v1,
    compute_instrument_score_v1,
    compute_negated_mean_open_gap_v1,
    is_eligible_universe_instrument_v1,
    rank_scores_deterministic_v1,
    validate_lookback_n,
    validate_rebalance_interval_bars,
)
from src.research.cross_sectional_open_gap_pressure_fade_v1_selection_v1 import (
    DIRECTIONAL_FORM,
    SELECTION_MODE,
    TIE_BREAK_POLICY,
    RankIntentSideV1,
    resolve_symmetric_top1_sign_v1,
    select_single_top1_rank_intent_v1,
)
from src.research.cross_sectional_open_gap_pressure_fade_v1_strategy_implementation_binding_v1 import (
    load_and_validate_repo_binding,
)

REPO = Path(__file__).resolve().parents[2]
CONTRACT = (
    REPO
    / "config/research/cross_sectional_open_gap_pressure_fade_v1_preregistered_economic_hypothesis_measurement_contract_v1.json"
)
BINDING = (
    REPO
    / "config/research/cross_sectional_open_gap_pressure_fade_v1_strategy_implementation_binding_v1.json"
)
IMPL_PROD_FILES = (
    REPO / "src/research/cross_sectional_open_gap_pressure_fade_v1_score_v1.py",
    REPO / "src/research/cross_sectional_open_gap_pressure_fade_v1_selection_v1.py",
    REPO
    / "src/research/cross_sectional_open_gap_pressure_fade_v1_strategy_implementation_binding_v1.py",
    BINDING,
    REPO
    / "docs/governance/CROSS_SECTIONAL_OPEN_GAP_PRESSURE_FADE_V1_STRATEGY_IMPLEMENTATION_ONLY_V1.md",
)

# Contaminated CLV formula/digest residue must not appear in Open-Gap surfaces.
_CLV_FORMULA_RESIDUE_RE = re.compile(
    r"(?:compute_bar_clv|mean_clv|close_location_value|"
    r"mean_intrabar_close_location|"
    r"DEFAULT_LOOKBACK_N\s*=\s*36|"
    r"DEFAULT_REBALANCE_INTERVAL_BARS\s*=\s*6|"
    r"\"lookback_n\":\s*36|"
    r"\"rebalance_interval_bars\":\s*6)",
    re.IGNORECASE,
)
_CLV_DIGEST = "5ad3210f8b02151122aff1846f08003fcdf62f662be372a425184a4b76734cb4"


def _constant_open_close(
    *,
    n: int,
    open_value: float,
    close_value: float,
) -> dict[str, tuple[float, ...]]:
    return {
        "open": tuple(open_value for _ in range(n)),
        "close": tuple(close_value for _ in range(n)),
    }


def _gap_up_panel(
    n: int = 80, base: float = 100.0, gap_ratio: float = 1.01
) -> dict[str, tuple[float, ...]]:
    """Every open gaps up vs prior close; closes flat at base."""
    closes = tuple(base for _ in range(n))
    opens = tuple(base * gap_ratio for _ in range(n))
    return {"open": opens, "close": closes}


def _gap_down_panel(
    n: int = 80, base: float = 100.0, gap_ratio: float = 0.99
) -> dict[str, tuple[float, ...]]:
    """Every open gaps down vs prior close; closes flat at base."""
    closes = tuple(base for _ in range(n))
    opens = tuple(base * gap_ratio for _ in range(n))
    return {"open": opens, "close": closes}


def test_score_formula_and_frozen_parameters() -> None:
    assert SCORE_FORMULA_VERSION == "negated_mean_open_gap_fixed_lookback_v1"
    assert POLARITY == "OPEN_GAP_PRESSURE_FADE_NEGATED_MEAN_GAP"
    assert VOL_NORMALIZATION is False
    assert DEFAULT_LOOKBACK_N == 30
    assert DEFAULT_REBALANCE_INTERVAL_BARS == 5
    assert DEFAULT_SIGNAL_LAG_BARS == 1
    assert SELECTION_MODE == "single_top1_by_score_desc"
    assert TIE_BREAK_POLICY == "score_desc_then_instrument_id_asc"
    assert DIRECTIONAL_FORM == "D_MUTUALLY_EXCLUSIVE_DIRECTIONAL_SELECTION"
    assert validate_lookback_n(30) is True
    assert validate_lookback_n(36) is False
    assert validate_rebalance_interval_bars(5) is True
    assert validate_rebalance_interval_bars(6) is False


def test_gap_up_yields_positive_gap_negative_score_and_short_intent() -> None:
    open_b = 110.0
    close_prev = 100.0
    gap = compute_bar_open_gap_v1(open_b=open_b, close_prev=close_prev)
    assert gap is not None
    assert gap > 0.0
    assert gap == pytest.approx(math.log(open_b / close_prev))

    panel = _gap_up_panel(n=80, gap_ratio=1.02)
    epoch = 40
    components = compute_negated_mean_open_gap_v1(
        panel["open"],
        panel["close"],
        lookback_n=30,
        signal_lag_bars=1,
        epoch_index=epoch,
    )
    assert components is not None
    score, mean_gap = components
    assert mean_gap > 0.0
    assert score < 0.0
    assert score == pytest.approx(-mean_gap)
    assert resolve_symmetric_top1_sign_v1(score) == RankIntentSideV1.SHORT_TOP1


def test_gap_down_yields_negative_gap_positive_score_and_long_intent() -> None:
    open_b = 90.0
    close_prev = 100.0
    gap = compute_bar_open_gap_v1(open_b=open_b, close_prev=close_prev)
    assert gap is not None
    assert gap < 0.0

    panel = _gap_down_panel(n=80, gap_ratio=0.98)
    epoch = 40
    components = compute_negated_mean_open_gap_v1(
        panel["open"],
        panel["close"],
        lookback_n=30,
        signal_lag_bars=1,
        epoch_index=epoch,
    )
    assert components is not None
    score, mean_gap = components
    assert mean_gap < 0.0
    assert score > 0.0
    assert resolve_symmetric_top1_sign_v1(score) == RankIntentSideV1.LONG_TOP1


def test_fade_direction_is_not_inverted() -> None:
    """Gap-down fades LONG; gap-up fades SHORT (not inverted continuation)."""
    assert resolve_symmetric_top1_sign_v1(0.05) == RankIntentSideV1.LONG_TOP1
    assert resolve_symmetric_top1_sign_v1(-0.05) == RankIntentSideV1.SHORT_TOP1

    gap_down = compute_bar_open_gap_v1(open_b=95.0, close_prev=100.0)
    gap_up = compute_bar_open_gap_v1(open_b=105.0, close_prev=100.0)
    assert gap_down is not None and gap_up is not None
    assert -gap_down > 0.0
    assert -gap_up < 0.0


def test_prior_close_not_current_close() -> None:
    """Score must use close[b-1], not close[b], as the gap denominator."""
    n = 80
    gap_correct = compute_bar_open_gap_v1(open_b=110.0, close_prev=100.0)
    gap_wrong_current = compute_bar_open_gap_v1(open_b=110.0, close_prev=200.0)
    assert gap_correct is not None and gap_wrong_current is not None
    assert gap_correct > 0.0
    assert gap_wrong_current < 0.0

    opens = [100.0] * n
    closes = [100.0] * n
    opens[35] = 110.0
    closes[35] = 50.0  # current close bait; must not be used as prior
    result = compute_negated_mean_open_gap_v1(
        tuple(opens),
        tuple(closes),
        lookback_n=30,
        signal_lag_bars=1,
        epoch_index=36,
    )
    assert result is not None
    score, mean_gap = result
    expected_mean = math.log(110.0 / 100.0) / 30.0
    assert mean_gap == pytest.approx(expected_mean)
    assert score == pytest.approx(-expected_mean)
    assert score < 0.0


def test_signal_lag_prevents_lookahead() -> None:
    n = 80
    # Persistent gap-up so score is non-zero / eligible.
    closes = [100.0] * n
    opens = [101.0] * n
    epoch = 40
    baseline = compute_negated_mean_open_gap_v1(
        tuple(opens),
        tuple(closes),
        lookback_n=30,
        signal_lag_bars=1,
        epoch_index=epoch,
    )
    opens2 = list(opens)
    closes2 = list(closes)
    # Mutate only the current epoch bar (lookahead bait); lag=1 must ignore it.
    opens2[40] = 999.0
    closes2[40] = 1.0
    lagged = compute_negated_mean_open_gap_v1(
        tuple(opens2),
        tuple(closes2),
        lookback_n=30,
        signal_lag_bars=1,
        epoch_index=epoch,
    )
    assert baseline is not None and lagged is not None
    assert baseline[0] == pytest.approx(lagged[0])
    no_lag = compute_negated_mean_open_gap_v1(
        tuple(opens2),
        tuple(closes2),
        lookback_n=30,
        signal_lag_bars=0,
        epoch_index=epoch,
    )
    assert no_lag is not None
    assert no_lag[0] != pytest.approx(lagged[0])


def test_lookback_is_exactly_30() -> None:
    assert DEFAULT_LOOKBACK_N == 30
    panel = _gap_up_panel(n=80, gap_ratio=1.01)
    epoch = 50
    ok = compute_negated_mean_open_gap_v1(
        panel["open"],
        panel["close"],
        lookback_n=30,
        signal_lag_bars=1,
        epoch_index=epoch,
    )
    assert ok is not None
    too_early = compute_negated_mean_open_gap_v1(
        panel["open"],
        panel["close"],
        lookback_n=30,
        signal_lag_bars=1,
        epoch_index=30,
    )
    assert too_early is None
    with pytest.raises(ValueError, match="LOOKBACK_N_NOT_FROZEN_PARAMETER"):
        select_single_top1_rank_intent_v1(
            {"okx:linear_perpetual:ETH-USDT": panel},
            epoch_index=40,
            lookback_n=29,
        )


def test_rebalance_is_exactly_5() -> None:
    assert DEFAULT_REBALANCE_INTERVAL_BARS == 5
    panel = {
        f"okx:linear_perpetual:A{i}-USDT": _gap_down_panel(n=80, gap_ratio=0.99 - i * 0.001)
        for i in range(5)
    }
    intent = select_single_top1_rank_intent_v1(panel, epoch_index=40)
    assert intent.selection_emitted is True
    assert intent.rebalance_interval_bars == 5
    held = select_single_top1_rank_intent_v1(panel, epoch_index=41, prior_intent=intent)
    assert held.selection_emitted is False
    assert held.selected_instrument_id == intent.selected_instrument_id
    with pytest.raises(ValueError, match="REBALANCE_INTERVAL_NOT_FROZEN_PARAMETER"):
        select_single_top1_rank_intent_v1(panel, epoch_index=40, rebalance_interval_bars=6)


def test_score_zero_is_ineligible() -> None:
    panel = _constant_open_close(n=80, open_value=100.0, close_value=100.0)
    assert (
        compute_negated_mean_open_gap_v1(
            panel["open"],
            panel["close"],
            lookback_n=30,
            signal_lag_bars=1,
            epoch_index=40,
        )
        is None
    )
    assert (
        compute_instrument_score_v1(
            "okx:linear_perpetual:ETH-USDT",
            panel["open"],
            panel["close"],
            epoch_index=40,
        )
        is None
    )
    assert resolve_symmetric_top1_sign_v1(0.0) == RankIntentSideV1.FLAT


def test_insufficient_eligible_universe_yields_no_selection() -> None:
    panel = {
        "okx:linear_perpetual:ETH-USDT": _gap_down_panel(),
        "okx:linear_perpetual:SOL-USDT": _gap_up_panel(),
        "okx:linear_perpetual:AVAX-USDT": _gap_down_panel(gap_ratio=0.98),
        "okx:linear_perpetual:LINK-USDT": _gap_up_panel(gap_ratio=1.03),
    }
    intent = select_single_top1_rank_intent_v1(panel, epoch_index=40)
    assert intent.eligible_member_count < 5
    assert intent.insufficient_universe is True
    assert intent.selected_instrument_id is None
    assert intent.intent_side == RankIntentSideV1.FLAT


def test_top1_and_tie_break_deterministic() -> None:
    shared = _gap_down_panel(n=80, gap_ratio=0.99)
    a = compute_instrument_score_v1(
        "okx:linear_perpetual:AAA-USDT", shared["open"], shared["close"], epoch_index=40
    )
    b = compute_instrument_score_v1(
        "okx:linear_perpetual:BBB-USDT", shared["open"], shared["close"], epoch_index=40
    )
    assert a is not None and b is not None
    assert a.score == pytest.approx(b.score)
    ranked = rank_scores_deterministic_v1([b, a])
    assert ranked[0].instrument_id == "okx:linear_perpetual:AAA-USDT"

    panel = {
        "okx:linear_perpetual:ETH-USDT": _gap_down_panel(gap_ratio=0.99),
        "okx:linear_perpetual:SOL-USDT": _gap_down_panel(gap_ratio=0.95),
        "okx:linear_perpetual:AVAX-USDT": _gap_down_panel(gap_ratio=0.98),
        "okx:linear_perpetual:LINK-USDT": _gap_up_panel(gap_ratio=1.01),
        "okx:linear_perpetual:DOT-USDT": _gap_up_panel(gap_ratio=1.02),
    }
    intent = select_single_top1_rank_intent_v1(panel, epoch_index=40)
    assert intent.insufficient_universe is False
    assert intent.selected_instrument_id == "okx:linear_perpetual:SOL-USDT"
    assert intent.intent_side == RankIntentSideV1.LONG_TOP1
    assert intent.double_play_remains_sole_authority is True
    assert not is_eligible_universe_instrument_v1("okx:linear_perpetual:BTC-USDT")


def test_no_clv_residue_in_open_gap_surfaces() -> None:
    for path in IMPL_PROD_FILES:
        text = path.read_text(encoding="utf-8")
        assert _CLV_FORMULA_RESIDUE_RE.search(text) is None, f"CLV residue in {path}"
        assert _CLV_DIGEST not in text
        assert "DEFAULT_LOOKBACK_N = 36" not in text
        assert "DEFAULT_REBALANCE_INTERVAL_BARS = 6" not in text
        assert '"lookback_n": 36' not in text
        assert '"rebalance_interval_bars": 6' not in text
    score_text = IMPL_PROD_FILES[0].read_text(encoding="utf-8")
    selection_text = IMPL_PROD_FILES[1].read_text(encoding="utf-8")
    for text in (score_text, selection_text):
        assert "intrabar_close_location" not in text
        assert "compute_bar_clv" not in text
        assert "mean_clv" not in text
        assert "from src.research.cross_sectional_intrabar" not in text


def test_implementation_binding_and_counters_unchanged() -> None:
    report = load_and_validate_repo_binding(REPO)
    assert report["valid"] is True
    assert report["strategy_implementation_present"] is True
    assert report["implementation_matches_preregistration"] is True
    assert report["evaluation_authorized"] is False
    assert report["development_evaluation_executed"] is False
    assert report["development_run_count"] == 0
    assert report["run_slot_consumed"] is False
    assert report["holdout_authorized"] is False
    assert report["double_play_remains_sole_authority"] is True

    measurement = json.loads(CONTRACT.read_text(encoding="utf-8"))
    live_digest = compute_contract_digest(measurement)
    assert measurement["contract_digest"] == live_digest
    assert report["frozen_digest"] == live_digest
    assert live_digest == "7f8d361b597825428eecb2f6f791fcef07fe5a0dd92f9613f99b5d15e95b5768"
    assert measurement["development_run_count"] == 0
    assert measurement["run_slot_consumed"] is False
    assert measurement["development_evaluation_executed"] is False
    assert measurement["strategy_implementation_present"] is False

    binding = json.loads(BINDING.read_text(encoding="utf-8"))
    assert binding["development_run_count"] == 0
    assert binding["run_slot_consumed"] is False
    assert binding["development_evaluation_executed"] is False
    assert binding["parameter_defaults"]["lookback_n"] == 30
    assert binding["parameter_defaults"]["rebalance_interval_bars"] == 5
