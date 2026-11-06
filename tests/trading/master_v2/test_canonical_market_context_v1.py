# tests/trading/master_v2/test_canonical_market_context_v1.py
from __future__ import annotations

import ast
import copy
from pathlib import Path

import pytest

from trading.master_v2.canonical_market_context_v1 import (
    CANONICAL_MARKET_CONTEXT_LAYER_VERSION,
    FEATURE_CONTRACT_VERSION,
    PRIMARY_DECISION_PRICE,
    BarFinalityStatus,
    CanonicalMarketContextBindingOutcome,
    CanonicalMarketContextBindingStateV1,
    CanonicalMarketContextBlockReason,
    CanonicalMarketContextV1,
    ClockTrustStatus,
    DataIntegrityStatus,
    WarmupStatus,
    bind_canonical_market_context_event,
    canonical_market_type_allowed,
    compute_canonical_market_context_input_digest,
    evaluate_canonical_market_context_eligibility,
    futures_market_type_to_canonical,
    serialize_canonical_market_context_canonical,
    validate_canonical_market_context_fields,
    validate_futures_input_snapshot_binding,
    with_computed_input_digest,
)
from trading.master_v2.double_play_futures_input import (
    FuturesCandidateSnapshot,
    FuturesDerivativesProfile,
    FuturesFreshnessState,
    FuturesInputSnapshot,
    FuturesInstrumentMetadataStatus,
    FuturesLiquidityProfile,
    FuturesMarketDataProvenanceStatus,
    FuturesMarketType,
    FuturesOpportunityProfile,
    FuturesRankingSnapshot,
    FuturesVolatilityProfile,
)


def _features(**kwargs: float) -> dict[str, float]:
    return dict(kwargs)


def _context(**overrides: object) -> CanonicalMarketContextV1:
    base: dict = {
        "context_id": "ctx-eth-perp-epoch42-ev1",
        "instrument_id": "inst-eth-usdt-perp",
        "market_type": FuturesMarketType.PERPETUAL,
        "trading_epoch": 42,
        "market_event_time": "2026-06-30T12:00:00+00:00",
        "decision_time": "2026-06-30T12:00:01+00:00",
        "bar_interval": "1m",
        "bar_finality_status": BarFinalityStatus.FINALIZED,
        "mark_price": 3500.0,
        "index_price": 3499.5,
        "best_bid": 3499.8,
        "best_ask": 3500.2,
        "spread": 0.4,
        "volume": 1_250_000.0,
        "open_interest": 85_000_000.0,
        "funding_rate": 0.00012,
        "volatility_estimate": 0.38,
        "trend_feature_set": _features(slope=0.02, strength=0.71),
        "momentum_feature_set": _features(rsi=55.0, roc=0.015),
        "liquidity_feature_set": _features(depth_score=0.88),
        "market_structure_feature_set": _features(range_ratio=0.42),
        "data_integrity_status": DataIntegrityStatus.TRUSTED,
        "clock_trust_status": ClockTrustStatus.TRUSTED,
        "warmup_status": WarmupStatus.WARMUP_COMPLETE,
        "feature_contract_version": FEATURE_CONTRACT_VERSION,
        "input_digest": "",
    }
    base.update(overrides)
    return CanonicalMarketContextV1(**base)


def _futures_snapshot(**overrides: object) -> FuturesInputSnapshot:
    candidate = FuturesCandidateSnapshot(
        candidate_id="c-eth-1",
        instrument_id="inst-eth-usdt-perp",
        symbol="ETH-USDT-PERP",
        market_type=FuturesMarketType.PERPETUAL,
        exchange="example",
        base_currency="ETH",
        quote_currency="USDT",
        live_authorization=False,
    )
    parts: dict = {
        "candidate": candidate,
        "ranking": FuturesRankingSnapshot(
            source_universe_size=100,
            selected_top_n=20,
            rank=2,
            score=0.87,
            score_components_complete=True,
            is_top_n_member=True,
        ),
        "instrument": FuturesInstrumentMetadataStatus(
            complete=True,
            contract_size_known=True,
            tick_size_known=True,
            step_size_known=True,
            min_qty_known=True,
            min_notional_known=True,
            margin_asset_known=True,
            settlement_asset_known=True,
            leverage_bounds_known=True,
            missing_fields=(),
        ),
        "provenance": FuturesMarketDataProvenanceStatus(
            complete=True,
            freshness_state=FuturesFreshnessState.FRESH,
            dataset_id="ds-eth-1",
            source="fixture",
            mark_available=True,
            index_available=True,
            last_available=True,
            ohlcv_available=True,
            funding_available=True,
            open_interest_available=True,
            missing_fields=(),
        ),
        "volatility": FuturesVolatilityProfile(
            realized_volatility=0.38,
            atr_or_rolling_range=45.0,
            volatility_regime="medium",
            dynamic_scope_usable=True,
        ),
        "liquidity": FuturesLiquidityProfile(
            spread_bps=1.1,
            average_spread_bps=1.3,
            volume=1_250_000.0,
            quote_volume=4_375_000_000.0,
            liquidity_regime="deep",
            spread_quality="tight",
        ),
        "derivatives": FuturesDerivativesProfile(
            funding_available=True,
            funding_rate=0.00012,
            funding_regime="neutral",
            open_interest_available=True,
            open_interest=85_000_000.0,
            open_interest_regime="high",
        ),
        "opportunity": FuturesOpportunityProfile(
            opportunity_score=0.72,
            inactivity_score=0.08,
            movement_above_fee_slippage_breakeven=True,
            chop_risk="low",
            candidate_is_inactive=False,
        ),
    }
    parts.update(overrides)
    return FuturesInputSnapshot(**parts)


def test_layer_version_and_primary_decision_price_constants() -> None:
    assert CANONICAL_MARKET_CONTEXT_LAYER_VERSION == "v1"
    assert PRIMARY_DECISION_PRICE == "VENUE_MARK_PRICE"


def test_complete_valid_futures_context_forms_and_passes_validation() -> None:
    ctx = _context()
    blocks = validate_canonical_market_context_fields(ctx)
    assert not blocks
    bound = with_computed_input_digest(ctx)
    assert len(bound.input_digest) == 64
    elig = evaluate_canonical_market_context_eligibility(bound)
    assert elig.trading_decision_allowed
    assert elig.scope_confirmation_allowed
    assert elig.new_directional_exposure_allowed
    assert not elig.observation_and_reconciliation_only
    assert elig.primary_decision_price == ctx.mark_price
    assert elig.decision_price_source == PRIMARY_DECISION_PRICE
    assert not elig.execution_eligible
    assert not elig.is_authority


def test_input_digest_is_deterministic() -> None:
    ctx = _context()
    d1 = compute_canonical_market_context_input_digest(ctx)
    d2 = compute_canonical_market_context_input_digest(ctx)
    assert d1 == d2
    assert d1 == with_computed_input_digest(ctx).input_digest


def test_identical_inputs_yield_identical_digest() -> None:
    a = compute_canonical_market_context_input_digest(_context())
    b = compute_canonical_market_context_input_digest(_context())
    assert a == b


def test_feature_dictionary_order_does_not_affect_digest() -> None:
    ctx_a = _context(trend_feature_set={"b": 2.0, "a": 1.0})
    ctx_b = _context(trend_feature_set={"a": 1.0, "b": 2.0})
    assert compute_canonical_market_context_input_digest(
        ctx_a
    ) == compute_canonical_market_context_input_digest(ctx_b)


def test_decision_relevant_field_change_changes_digest() -> None:
    base = compute_canonical_market_context_input_digest(_context())
    changed = compute_canonical_market_context_input_digest(_context(mark_price=3501.0))
    assert base != changed


def test_duplicate_event_is_idempotent() -> None:
    ctx = _context()
    state = CanonicalMarketContextBindingStateV1()
    first = bind_canonical_market_context_event(ctx, state)
    assert first.eligibility.binding_outcome is CanonicalMarketContextBindingOutcome.ACCEPTED
    second = bind_canonical_market_context_event(ctx, first.next_state)
    assert (
        second.eligibility.binding_outcome
        is CanonicalMarketContextBindingOutcome.DUPLICATE_IDEMPOTENT
    )
    assert second.next_state == first.next_state


def test_out_of_order_event_fail_closed() -> None:
    earlier = _context(
        context_id="ctx-earlier",
        market_event_time="2026-06-30T12:00:00+00:00",
        decision_time="2026-06-30T12:00:01+00:00",
    )
    later = _context(
        context_id="ctx-later",
        market_event_time="2026-06-30T12:01:00+00:00",
        decision_time="2026-06-30T12:01:01+00:00",
    )
    state = CanonicalMarketContextBindingStateV1()
    accepted = bind_canonical_market_context_event(later, state)
    assert accepted.eligibility.binding_outcome is CanonicalMarketContextBindingOutcome.ACCEPTED
    ooo = bind_canonical_market_context_event(earlier, accepted.next_state)
    assert ooo.eligibility.binding_outcome is CanonicalMarketContextBindingOutcome.BLOCKED
    assert (
        CanonicalMarketContextBlockReason.OUT_OF_ORDER_MARKET_EVENT in ooo.eligibility.block_reasons
    )
    assert not ooo.eligibility.trading_decision_allowed


def test_unfinalized_bar_blocks_entry_and_scope_confirmation() -> None:
    ctx = with_computed_input_digest(_context(bar_finality_status=BarFinalityStatus.UNFINALIZED))
    elig = evaluate_canonical_market_context_eligibility(ctx)
    assert not elig.trading_decision_allowed
    assert not elig.scope_confirmation_allowed
    assert CanonicalMarketContextBlockReason.BAR_UNFINALIZED in elig.block_reasons


def test_warmup_required_blocks_directional_exposure() -> None:
    ctx = with_computed_input_digest(_context(warmup_status=WarmupStatus.WARMUP_REQUIRED))
    elig = evaluate_canonical_market_context_eligibility(ctx)
    assert not elig.new_directional_exposure_allowed
    assert not elig.scope_confirmation_allowed
    assert elig.observation_and_reconciliation_only
    assert CanonicalMarketContextBlockReason.WARMUP_REQUIRED in elig.block_reasons


def test_warmup_invalid_blocks() -> None:
    ctx = with_computed_input_digest(_context(warmup_status=WarmupStatus.WARMUP_INVALID))
    elig = evaluate_canonical_market_context_eligibility(ctx)
    assert not elig.new_directional_exposure_allowed
    assert elig.observation_and_reconciliation_only
    assert CanonicalMarketContextBlockReason.WARMUP_INVALID in elig.block_reasons


@pytest.mark.parametrize(
    "status",
    [DataIntegrityStatus.UNTRUSTED, DataIntegrityStatus.UNKNOWN, DataIntegrityStatus.INVALID],
)
def test_data_integrity_untrusted_or_unknown_blocks(status: DataIntegrityStatus) -> None:
    ctx = with_computed_input_digest(_context(data_integrity_status=status))
    elig = evaluate_canonical_market_context_eligibility(ctx)
    assert not elig.trading_decision_allowed
    assert elig.observation_and_reconciliation_only


@pytest.mark.parametrize(
    "status",
    [ClockTrustStatus.UNTRUSTED, ClockTrustStatus.UNKNOWN, ClockTrustStatus.INVALID],
)
def test_clock_trust_untrusted_or_unknown_blocks(status: ClockTrustStatus) -> None:
    ctx = with_computed_input_digest(_context(clock_trust_status=status))
    elig = evaluate_canonical_market_context_eligibility(ctx)
    assert not elig.trading_decision_allowed
    assert elig.observation_and_reconciliation_only


def test_mark_price_is_canonical_decision_price() -> None:
    ctx = with_computed_input_digest(_context(mark_price=4123.45))
    elig = evaluate_canonical_market_context_eligibility(ctx)
    assert elig.primary_decision_price == 4123.45
    serialized = serialize_canonical_market_context_canonical(ctx)
    assert PRIMARY_DECISION_PRICE in serialized


def test_spread_validated_against_bid_ask() -> None:
    blocks = validate_canonical_market_context_fields(_context(spread=9.99))
    assert CanonicalMarketContextBlockReason.SPREAD_INCONSISTENT in blocks


def test_invalid_bid_ask_time_and_instrument_rejected() -> None:
    assert (
        CanonicalMarketContextBlockReason.BEST_BID_INVALID
        in validate_canonical_market_context_fields(_context(best_bid=-1.0))
    )
    assert (
        CanonicalMarketContextBlockReason.BEST_ASK_INVALID
        in validate_canonical_market_context_fields(_context(best_ask=0.0))
    )
    assert (
        CanonicalMarketContextBlockReason.MARKET_EVENT_TIME_INVALID
        in validate_canonical_market_context_fields(_context(market_event_time="not-a-time"))
    )
    assert (
        CanonicalMarketContextBlockReason.INSTRUMENT_ID_INVALID
        in validate_canonical_market_context_fields(_context(instrument_id=""))
    )


def test_futures_only_enforced_via_market_type() -> None:
    assert canonical_market_type_allowed(FuturesMarketType.PERPETUAL)
    assert not canonical_market_type_allowed(FuturesMarketType.UNKNOWN)
    blocks = validate_canonical_market_context_fields(
        _context(market_type=FuturesMarketType.UNKNOWN)
    )
    assert CanonicalMarketContextBlockReason.INSTRUMENT_KIND_UNKNOWN in blocks


def test_spot_and_synthetic_spot_instrument_id_rejected() -> None:
    for instrument_id in ("inst-spot-eth", "inst-synthetic_spot-eth", "inst-synthetic-spot-eth"):
        blocks = validate_canonical_market_context_fields(_context(instrument_id=instrument_id))
        assert CanonicalMarketContextBlockReason.INSTRUMENT_ID_INVALID in blocks


def test_bitcoin_not_required_in_semantics_generic_instrument_works() -> None:
    ctx = _context(
        instrument_id="inst-sol-usdt-perp",
        context_id="ctx-sol-perp-epoch1-ev1",
    )
    assert not validate_canonical_market_context_fields(ctx)
    digest = compute_canonical_market_context_input_digest(ctx)
    assert "btc" not in digest
    assert "bitcoin" not in serialize_canonical_market_context_canonical(ctx).lower()


def test_futures_input_binding_adapter_consistency() -> None:
    ctx = _context()
    snap = _futures_snapshot()
    assert not validate_futures_input_snapshot_binding(ctx, snap)
    mismatch = validate_futures_input_snapshot_binding(
        ctx,
        _futures_snapshot(
            candidate=FuturesCandidateSnapshot(
                candidate_id="x",
                instrument_id="other",
                symbol="OTHER-PERP",
                market_type=FuturesMarketType.FUTURES,
                exchange="example",
                base_currency="SOL",
                quote_currency="USDT",
            )
        ),
    )
    assert CanonicalMarketContextBlockReason.FUTURES_INPUT_INSTRUMENT_MISMATCH in mismatch


def test_bind_with_futures_input_snapshot_narrow_adapter() -> None:
    ctx = _context()
    snap = _futures_snapshot()
    result = bind_canonical_market_context_event(
        ctx, CanonicalMarketContextBindingStateV1(), futures_input_snapshot=snap
    )
    assert result.eligibility.binding_outcome is CanonicalMarketContextBindingOutcome.ACCEPTED


def test_no_runtime_order_or_execution_side_effects_in_module() -> None:
    root = Path(__file__).resolve().parent.parent.parent.parent / "src" / "trading" / "master_v2"
    path = root / "canonical_market_context_v1.py"
    tree = ast.parse(path.read_text(encoding="utf-8"))
    bad_roots = {
        "ccxt",
        "requests",
        "urllib3",
        "httpx",
        "aiohttp",
        "socket",
        "websockets",
        "boto3",
        "subprocess",
    }
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for n in node.names:
                assert n.name.split(".")[0] not in bad_roots
        if isinstance(node, ast.ImportFrom) and node.module:
            assert node.module.split(".")[0] not in bad_roots


def test_futures_market_type_reuse_bridge() -> None:
    assert futures_market_type_to_canonical(FuturesMarketType.SWAP) is FuturesMarketType.SWAP


def test_existing_double_play_futures_input_regression_still_importable() -> None:
    from trading.master_v2.double_play_futures_input import evaluate_futures_input_snapshot

    d = evaluate_futures_input_snapshot(_futures_snapshot())
    assert d.ready_for_downstream_model_use
