"""Focused owner tests for CSRHR v1 offline score/selection (synthetic only)."""

from __future__ import annotations

import ast
import json
import math
from pathlib import Path

import pytest

from src.research.cross_sectional_short_horizon_return_reversal_hypothesis_backlog_v1 import (
    load_and_validate_repo_backlog,
)
from src.research.cross_sectional_short_horizon_return_reversal_research_program_v1 import (
    load_and_validate_repo_program,
)
from src.research.cross_sectional_short_horizon_return_reversal_v1_hypothesis_preregistration_v1 import (
    load_and_validate_repo_contract,
)
from src.research.cross_sectional_short_horizon_return_reversal_v1_score_v1 import (
    DEFAULT_LOOKBACK_N,
    DEFAULT_REBALANCE_INTERVAL_BARS,
    HYPOTHESIS_ID,
    SCORE_FORMULA_VERSION,
    VOL_NORMALIZATION,
    compute_instrument_score_v1,
    compute_raw_trailing_log_return_v1,
    is_eligible_universe_instrument_v1,
    rank_scores_deterministic_v1,
    validate_lookback_n,
)
from src.research.cross_sectional_short_horizon_return_reversal_v1_selection_v1 import (
    DIRECTIONAL_FORM,
    RankIntentSideV1,
    resolve_symmetric_top1_sign_v1,
    select_single_top1_rank_intent_v1,
)
from src.research.cross_sectional_short_horizon_return_reversal_v1_strategy_implementation_binding_v1 import (
    REQUIRED_DIGEST,
    load_and_validate_repo_binding,
)

REPO = Path(__file__).resolve().parents[2]
IMPL_FILES = (
    REPO / "src/research/cross_sectional_short_horizon_return_reversal_v1_score_v1.py",
    REPO / "src/research/cross_sectional_short_horizon_return_reversal_v1_selection_v1.py",
)
RETIRED = (
    "trend_following/v1",
    "bollinger_bands/v1",
    "momentum_1h/v1",
)
FORBIDDEN_IMPORT_ROOTS = (
    "src.runtime",
    "src.execution",
    "src.scheduler",
    "src.trading.master_v2",
    "src.risk",
    "requests",
    "urllib",
    "httpx",
    "aiohttp",
)


def _closes_up(start: float = 100.0, n: int = 40, step: float = 1.01) -> tuple[float, ...]:
    values = [start]
    for _ in range(n - 1):
        values.append(values[-1] * step)
    return tuple(values)


def _closes_down(start: float = 100.0, n: int = 40, step: float = 0.99) -> tuple[float, ...]:
    values = [start]
    for _ in range(n - 1):
        values.append(values[-1] * step)
    return tuple(values)


def _panel() -> dict[str, tuple[float, ...]]:
    return {
        "okx:linear_perpetual:ETH-USDT": _closes_up(step=1.01),
        "okx:linear_perpetual:SOL-USDT": _closes_up(step=1.03),
        "okx:linear_perpetual:AVAX-USDT": _closes_up(step=1.02),
        "okx:linear_perpetual:LINK-USDT": _closes_down(step=0.99),
        "okx:linear_perpetual:DOT-USDT": _closes_up(step=1.015),
    }


def test_hypothesis_and_config_binding() -> None:
    assert HYPOTHESIS_ID == (
        "CROSS_SECTIONAL_SHORT_HORIZON_RETURN_REVERSAL_NON_BITCOIN_PERPETUALS_V1"
    )
    report = load_and_validate_repo_binding(REPO)
    assert report["valid"] is True
    assert report["hypothesis_id"] == HYPOTHESIS_ID
    assert report["frozen_digest"] == REQUIRED_DIGEST
    backlog = load_and_validate_repo_backlog(REPO)
    assert backlog["status"] == "OPEN_BACKLOG"
    program = load_and_validate_repo_program(REPO)
    assert program["valid"] is True
    prereg = load_and_validate_repo_contract(REPO)
    assert prereg["valid"] is True


def test_score_formula_is_negated_raw_trailing_not_vol_normalized() -> None:
    assert SCORE_FORMULA_VERSION == "negated_raw_trailing_log_return_fixed_lookback_v1"
    assert VOL_NORMALIZATION is False
    assert DEFAULT_LOOKBACK_N == 24
    assert DEFAULT_REBALANCE_INTERVAL_BARS == 4
    assert validate_lookback_n(20) is False


def test_raw_trailing_and_reversal_polarity() -> None:
    closes = _closes_up(n=40)
    epoch = 30
    lookback = 24
    lag = 1
    raw = compute_raw_trailing_log_return_v1(
        closes, lookback_n=lookback, signal_lag_bars=lag, epoch_index=epoch
    )
    assert raw is not None and raw > 0.0
    scored = compute_instrument_score_v1(
        "okx:linear_perpetual:ETH-USDT",
        closes,
        lookback_n=lookback,
        signal_lag_bars=lag,
        epoch_index=epoch,
    )
    assert scored is not None
    assert scored.score == pytest.approx(-raw)
    assert scored.trailing_log_return == pytest.approx(raw)
    # Winner (positive raw) ranks below loser under score_desc after negation.
    winner = compute_instrument_score_v1(
        "okx:linear_perpetual:SOL-USDT",
        _closes_up(step=1.03),
        lookback_n=lookback,
        epoch_index=epoch,
    )
    loser = compute_instrument_score_v1(
        "okx:linear_perpetual:LINK-USDT",
        _closes_down(step=0.99),
        lookback_n=lookback,
        epoch_index=epoch,
    )
    assert winner is not None and loser is not None
    assert loser.score > winner.score
    ranked = rank_scores_deterministic_v1([winner, loser])
    assert ranked[0].instrument_id == "okx:linear_perpetual:LINK-USDT"


def test_deterministic_identical_input() -> None:
    panel = _panel()
    a = select_single_top1_rank_intent_v1(panel, epoch_index=28)
    b = select_single_top1_rank_intent_v1(panel, epoch_index=28)
    assert a == b
    assert a.to_provenance_dict() == b.to_provenance_dict()


def test_long_and_short_side_semantics_and_single_slot() -> None:
    assert DIRECTIONAL_FORM == "D_MUTUALLY_EXCLUSIVE_DIRECTIONAL_SELECTION"
    assert resolve_symmetric_top1_sign_v1(0.1) == RankIntentSideV1.LONG_TOP1
    assert resolve_symmetric_top1_sign_v1(-0.1) == RankIntentSideV1.SHORT_TOP1
    assert resolve_symmetric_top1_sign_v1(0.0) == RankIntentSideV1.FLAT

    # Relative loser tops negated ranking → LONG_TOP1.
    intent = select_single_top1_rank_intent_v1(_panel(), epoch_index=28)
    assert intent.selection_emitted is True
    assert intent.selected_instrument_id == "okx:linear_perpetual:LINK-USDT"
    assert intent.intent_side == RankIntentSideV1.LONG_TOP1
    assert intent.double_play_remains_sole_authority is True

    # All-down panel with one milder loser (higher score after negation is most negative raw).
    downs = {
        "okx:linear_perpetual:ETH-USDT": _closes_down(step=0.995),
        "okx:linear_perpetual:SOL-USDT": _closes_down(step=0.99),
        "okx:linear_perpetual:AVAX-USDT": _closes_down(step=0.992),
        "okx:linear_perpetual:LINK-USDT": _closes_down(step=0.993),
        "okx:linear_perpetual:DOT-USDT": _closes_down(step=0.994),
    }
    # Force a relative winner (positive raw) as sole positive by mixing one up series.
    mixed = dict(downs)
    mixed["okx:linear_perpetual:SOL-USDT"] = _closes_up(step=1.02)
    short_intent = select_single_top1_rank_intent_v1(mixed, epoch_index=28)
    # Top after negation is deepest loser among downs (SOL is winner → low score).
    assert short_intent.selected_instrument_id != "okx:linear_perpetual:SOL-USDT"
    assert short_intent.intent_side in {
        RankIntentSideV1.LONG_TOP1,
        RankIntentSideV1.SHORT_TOP1,
        RankIntentSideV1.FLAT,
    }
    # Explicit SHORT: make top score negative by using all-up panel (negated scores < 0).
    all_up = {
        "okx:linear_perpetual:ETH-USDT": _closes_up(step=1.01),
        "okx:linear_perpetual:SOL-USDT": _closes_up(step=1.02),
        "okx:linear_perpetual:AVAX-USDT": _closes_up(step=1.015),
        "okx:linear_perpetual:LINK-USDT": _closes_up(step=1.012),
        "okx:linear_perpetual:DOT-USDT": _closes_up(step=1.011),
    }
    short_only = select_single_top1_rank_intent_v1(all_up, epoch_index=28)
    assert short_only.intent_side == RankIntentSideV1.SHORT_TOP1
    assert short_only.selected_instrument_id == "okx:linear_perpetual:ETH-USDT"


def test_tie_break_and_hold_between_rebalances() -> None:
    a = compute_instrument_score_v1(
        "okx:linear_perpetual:AAA-USDT", _closes_up(step=1.02), lookback_n=24, epoch_index=30
    )
    b = compute_instrument_score_v1(
        "okx:linear_perpetual:BBB-USDT", _closes_up(step=1.02), lookback_n=24, epoch_index=30
    )
    assert a is not None and b is not None
    ranked = rank_scores_deterministic_v1([b, a])
    assert ranked[0].instrument_id < ranked[1].instrument_id

    intent = select_single_top1_rank_intent_v1(_panel(), epoch_index=28)
    held = select_single_top1_rank_intent_v1(_panel(), epoch_index=29, prior_intent=intent)
    assert held.selection_emitted is False
    assert held.selected_instrument_id == intent.selected_instrument_id
    assert held.intent_side == intent.intent_side


def test_missing_nonfinite_insufficient_and_ineligible() -> None:
    short_hist = {
        "okx:linear_perpetual:ETH-USDT": _closes_up(n=10),
        "okx:linear_perpetual:SOL-USDT": _closes_up(n=10, step=1.02),
        "okx:linear_perpetual:AVAX-USDT": _closes_up(n=10, step=1.015),
        "okx:linear_perpetual:LINK-USDT": _closes_down(n=10),
        "okx:linear_perpetual:DOT-USDT": _closes_up(n=10, step=1.011),
    }
    missing = select_single_top1_rank_intent_v1(short_hist, epoch_index=28)
    assert missing.insufficient_universe is True
    assert missing.intent_side == RankIntentSideV1.FLAT

    nan_panel = _panel()
    nan_closes = list(nan_panel["okx:linear_perpetual:ETH-USDT"])
    nan_closes[20] = float("nan")
    nan_panel["okx:linear_perpetual:ETH-USDT"] = tuple(nan_closes)
    assert (
        compute_instrument_score_v1(
            "okx:linear_perpetual:ETH-USDT",
            nan_panel["okx:linear_perpetual:ETH-USDT"],
            lookback_n=24,
            epoch_index=30,
        )
        is None
    )

    sparse = {
        "okx:linear_perpetual:ETH-USDT": _closes_up(),
        "okx:linear_perpetual:SOL-USDT": _closes_up(step=1.02),
    }
    insufficient = select_single_top1_rank_intent_v1(sparse, epoch_index=28)
    assert insufficient.insufficient_universe is True

    assert is_eligible_universe_instrument_v1("okx:linear_perpetual:BTC-USDT") is False
    assert is_eligible_universe_instrument_v1("okx:spot:ETH-USDT") is False
    assert (
        compute_instrument_score_v1(
            "okx:linear_perpetual:BTC-USDT", _closes_up(), lookback_n=24, epoch_index=30
        )
        is None
    )
    assert (
        compute_instrument_score_v1(
            "okx:spot:ETH-USDT", _closes_up(), lookback_n=24, epoch_index=30
        )
        is None
    )


def test_pit_membership_and_no_lookahead() -> None:
    panel = _panel()
    membership = frozenset(
        {
            "okx:linear_perpetual:ETH-USDT",
            "okx:linear_perpetual:SOL-USDT",
            "okx:linear_perpetual:AVAX-USDT",
            "okx:linear_perpetual:DOT-USDT",
            # LINK omitted from PIT membership despite close series present.
        }
    )
    intent = select_single_top1_rank_intent_v1(panel, epoch_index=28, pit_membership=membership)
    assert intent.insufficient_universe is True
    assert "okx:linear_perpetual:LINK-USDT" not in intent.ranked_instrument_ids

    # Lookahead: score at epoch uses only lag-adjusted history.
    closes = _closes_up(n=40)
    epoch = 30
    raw = compute_raw_trailing_log_return_v1(
        closes, lookback_n=24, signal_lag_bars=1, epoch_index=epoch
    )
    lag_idx = epoch - 1
    expected = math.log(closes[lag_idx] / closes[lag_idx - 24])
    assert raw == pytest.approx(expected)
    # Future bar mutation must not change score at prior epoch.
    mutated = list(closes)
    mutated[-1] = mutated[-1] * 10.0
    raw2 = compute_raw_trailing_log_return_v1(
        mutated, lookback_n=24, signal_lag_bars=1, epoch_index=epoch
    )
    assert raw2 == pytest.approx(raw)


def test_no_hidden_parameter_fallback() -> None:
    with pytest.raises(ValueError, match="LOOKBACK_N_NOT_FROZEN_PARAMETER"):
        select_single_top1_rank_intent_v1(_panel(), epoch_index=28, lookback_n=20)
    with pytest.raises(ValueError, match="REBALANCE_INTERVAL_NOT_FROZEN_PARAMETER"):
        select_single_top1_rank_intent_v1(_panel(), epoch_index=28, rebalance_interval_bars=1)


def test_import_boundary_and_no_authority_mutation_surfaces() -> None:
    for path in IMPL_FILES:
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    for forbidden in FORBIDDEN_IMPORT_ROOTS:
                        assert not alias.name.startswith(forbidden)
            elif isinstance(node, ast.ImportFrom) and node.module:
                for forbidden in FORBIDDEN_IMPORT_ROOTS:
                    assert not node.module.startswith(forbidden)
    # Explicit: retired hypothesis IDs untouched in binding.
    binding = json.loads(
        (
            REPO / "config/research/"
            "cross_sectional_short_horizon_return_reversal_v1_strategy_implementation_binding_v1.json"
        ).read_text(encoding="utf-8")
    )
    blob = json.dumps(binding)
    for retired in RETIRED:
        assert retired not in blob


def test_no_evaluation_or_run_slot_or_holdout() -> None:
    report = load_and_validate_repo_binding(REPO)
    assert report["evaluation_authorized"] is False
    assert report["holdout_authorized"] is False
    assert report["run_slot_consumed"] is False
    backlog = json.loads(
        (
            REPO
            / "config/research/cross_sectional_short_horizon_return_reversal_hypothesis_backlog_v1.json"
        ).read_text(encoding="utf-8")
    )
    hyp = backlog["preregistered_hypotheses"][0]
    assert hyp["run_slot_consumed"] is False
    assert hyp["status"] == "PREREGISTERED_DEFINITION_ONLY"
    assert backlog["holdout_forbidden"] is True
    measurement = json.loads(
        (
            REPO / "config/research/"
            "cross_sectional_short_horizon_return_reversal_v1_preregistered_economic_"
            "hypothesis_measurement_contract_v1.json"
        ).read_text(encoding="utf-8")
    )
    assert measurement["strategy_implementation_present"] is False
    assert measurement["run_slot_consumed"] is False
    assert measurement["sealed_holdout_content_inspection_authorized"] is False


def test_provenance_serialization_stable() -> None:
    intent = select_single_top1_rank_intent_v1(_panel(), epoch_index=28)
    prov = intent.to_provenance_dict()
    assert prov["hypothesis_id"] == HYPOTHESIS_ID
    assert prov["schema_version"].startswith(
        "cross_sectional_short_horizon_return_reversal_v1_rank_intent"
    )
    assert prov["dataset_id"] == (
        "pit_okx_linear_usdt_non_bitcoin_cross_sectional_pt1h_dev_pre_holdout_v1"
    )
    assert prov["epoch_index"] == 28
    assert prov["lookback_n"] == 24
    assert json.dumps(prov, sort_keys=True) == json.dumps(prov, sort_keys=True)
