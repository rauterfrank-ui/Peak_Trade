# tests/trading/master_v2/test_canonical_scope_initialization_v1.py
from __future__ import annotations

import ast
from dataclasses import replace
from pathlib import Path

import pytest

from trading.master_v2.canonical_market_context_v1 import (
    FEATURE_CONTRACT_VERSION,
    BarFinalityStatus,
    CanonicalMarketContextV1,
    ClockTrustStatus,
    DataIntegrityStatus,
    WarmupStatus,
    with_computed_input_digest,
)
from trading.master_v2.canonical_scope_initialization_v1 import (
    CANONICAL_SCOPE_INITIALIZATION_LAYER_VERSION,
    SCOPE_INITIALIZATION_POLICY_VERSION,
    CanonicalScopeBlockReason,
    CanonicalScopeInitializationPolicyV1,
    CanonicalScopeInitializationResultV1,
    CanonicalScopeSnapshotV1,
    CanonicalScopeLifecycleState,
    ScopeInitializationPrerequisitesV1,
    ScopeReinitializationGuardV1,
    clamp_scope_band,
    classify_scope_lifecycle_state,
    compute_canonical_scope_semantic_digest,
    initialize_canonical_scope,
    serialize_canonical_scope_canonical,
    validate_scope_initialization_policy,
    with_computed_semantic_digest,
)
from trading.master_v2.double_play_futures_input import FuturesMarketType


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


def _policy(**overrides: object) -> CanonicalScopeInitializationPolicyV1:
    base: dict = {
        "min_scope_band": 50.0,
        "max_scope_band": 500.0,
        "policy_version": SCOPE_INITIALIZATION_POLICY_VERSION,
    }
    base.update(overrides)
    return CanonicalScopeInitializationPolicyV1(**base)


def _prerequisites(**overrides: object) -> ScopeInitializationPrerequisitesV1:
    base: dict = {
        "required_window_complete": True,
        "instrument_metadata_valid": True,
        "finalized_market_context": True,
    }
    base.update(overrides)
    return ScopeInitializationPrerequisitesV1(**base)


def _initialize(**kwargs: object) -> CanonicalScopeInitializationResultV1:
    ctx = kwargs.pop("market_context", _context())
    policy = kwargs.pop("policy", _policy())
    prereq = kwargs.pop("prerequisites", _prerequisites())
    return initialize_canonical_scope(ctx, policy, prereq, **kwargs)


def test_layer_version_and_policy_constants() -> None:
    assert CANONICAL_SCOPE_INITIALIZATION_LAYER_VERSION == "v1"
    assert SCOPE_INITIALIZATION_POLICY_VERSION == "canonical_scope_initialization_policy_v1"


def test_successful_initialization_from_valid_finalized_futures_context() -> None:
    result = _initialize()
    assert result.lifecycle_state is CanonicalScopeLifecycleState.SCOPE_VALID
    assert result.scope is not None
    assert not result.block_reasons
    assert result.scope.instrument_id == "inst-eth-usdt-perp"
    assert result.scope.initialized_at_trading_epoch == 42
    assert result.scope.source_market_context_id == "ctx-eth-perp-epoch42-ev1"
    assert len(result.scope.source_input_digest) == 64


def test_reference_price_bound_to_mark_price() -> None:
    result = _initialize(market_context=_context(mark_price=4200.0))
    assert result.scope is not None
    assert result.scope.reference_price == 4200.0
    assert result.scope.trailing_anchor == 4200.0


def test_volatility_distance_computed_correctly() -> None:
    result = _initialize(
        market_context=_context(mark_price=1000.0, volatility_estimate=0.25),
        policy=_policy(min_scope_band=10.0, max_scope_band=10_000.0),
    )
    assert result.scope is not None
    assert result.scope.initial_volatility_distance == pytest.approx(250.0)


def test_scope_band_clamped_to_minimum() -> None:
    result = _initialize(
        market_context=_context(mark_price=100.0, volatility_estimate=0.01),
        policy=_policy(min_scope_band=50.0, max_scope_band=500.0),
    )
    assert result.scope is not None
    assert result.scope.initial_volatility_distance == pytest.approx(1.0)
    assert result.scope.scope_band == 50.0


def test_scope_band_clamped_to_maximum() -> None:
    result = _initialize(
        market_context=_context(mark_price=10_000.0, volatility_estimate=0.5),
        policy=_policy(min_scope_band=50.0, max_scope_band=200.0),
    )
    assert result.scope is not None
    assert result.scope.initial_volatility_distance == pytest.approx(5000.0)
    assert result.scope.scope_band == 200.0


def test_scope_band_unchanged_within_bounds() -> None:
    result = _initialize(
        market_context=_context(mark_price=1000.0, volatility_estimate=0.1),
        policy=_policy(min_scope_band=50.0, max_scope_band=500.0),
    )
    assert result.scope is not None
    assert result.scope.scope_band == pytest.approx(100.0)


def test_neutral_boundaries_and_trailing_anchor() -> None:
    result = _initialize(
        market_context=_context(mark_price=2000.0, volatility_estimate=0.05),
        policy=_policy(min_scope_band=10.0, max_scope_band=500.0),
    )
    assert result.scope is not None
    band = result.scope.scope_band
    assert result.scope.neutral_upper_boundary == pytest.approx(2000.0 + band)
    assert result.scope.neutral_lower_boundary == pytest.approx(2000.0 - band)
    assert result.scope.trailing_anchor == 2000.0


def test_clamp_scope_band_unit_cases() -> None:
    assert clamp_scope_band(5.0, 50.0, 500.0) == 50.0
    assert clamp_scope_band(900.0, 50.0, 500.0) == 500.0
    assert clamp_scope_band(120.0, 50.0, 500.0) == 120.0


def test_deterministic_scope_output() -> None:
    a = _initialize()
    b = _initialize()
    assert a.scope is not None and b.scope is not None
    assert a.scope == b.scope


def test_deterministic_semantic_digest() -> None:
    result = _initialize()
    assert result.scope is not None
    d1 = compute_canonical_scope_semantic_digest(result.scope)
    d2 = compute_canonical_scope_semantic_digest(result.scope)
    assert d1 == d2
    assert d1 == result.scope.semantic_digest


def test_semantic_digest_changes_on_decision_relevant_field() -> None:
    base = _initialize()
    changed = _initialize(market_context=_context(volatility_estimate=0.39))
    assert base.scope is not None and changed.scope is not None
    assert base.scope.semantic_digest != changed.scope.semantic_digest


def test_reason_code_order_does_not_affect_semantic_digest() -> None:
    result = _initialize()
    assert result.scope is not None
    scope_a = result.scope
    scope_b = replace(scope_a, reason_codes=("a", "b"))
    scope_c = replace(scope_a, reason_codes=("b", "a"))
    assert scope_b.reason_codes != scope_c.reason_codes
    assert compute_canonical_scope_semantic_digest(
        scope_b
    ) == compute_canonical_scope_semantic_digest(scope_c)


def test_warmup_required_yields_warming_up() -> None:
    result = _initialize(market_context=_context(warmup_status=WarmupStatus.WARMUP_REQUIRED))
    assert result.scope is None
    assert result.lifecycle_state is CanonicalScopeLifecycleState.SCOPE_WARMING_UP
    assert CanonicalScopeBlockReason.WARMUP_INCOMPLETE in result.block_reasons


def test_warmup_invalid_yields_invalid() -> None:
    result = _initialize(market_context=_context(warmup_status=WarmupStatus.WARMUP_INVALID))
    assert result.lifecycle_state is CanonicalScopeLifecycleState.SCOPE_INVALID
    assert CanonicalScopeBlockReason.WARMUP_INVALID in result.block_reasons


def test_unfinalized_bar_blocked() -> None:
    result = _initialize(market_context=_context(bar_finality_status=BarFinalityStatus.UNFINALIZED))
    assert result.scope is None
    assert CanonicalScopeBlockReason.BAR_UNFINALIZED in result.block_reasons


def test_data_integrity_untrusted_blocked() -> None:
    result = _initialize(
        market_context=_context(data_integrity_status=DataIntegrityStatus.UNTRUSTED)
    )
    assert result.scope is None
    assert CanonicalScopeBlockReason.DATA_INTEGRITY_UNTRUSTED in result.block_reasons


def test_data_integrity_unknown_blocked() -> None:
    result = _initialize(market_context=_context(data_integrity_status=DataIntegrityStatus.UNKNOWN))
    assert CanonicalScopeBlockReason.DATA_INTEGRITY_UNKNOWN in result.block_reasons


def test_clock_trust_untrusted_blocked() -> None:
    result = _initialize(market_context=_context(clock_trust_status=ClockTrustStatus.UNTRUSTED))
    assert CanonicalScopeBlockReason.CLOCK_TRUST_UNTRUSTED in result.block_reasons


def test_clock_trust_unknown_blocked() -> None:
    result = _initialize(market_context=_context(clock_trust_status=ClockTrustStatus.UNKNOWN))
    assert CanonicalScopeBlockReason.CLOCK_TRUST_UNKNOWN in result.block_reasons


def test_required_window_incomplete_blocked() -> None:
    result = _initialize(prerequisites=_prerequisites(required_window_complete=False))
    assert result.scope is None
    assert CanonicalScopeBlockReason.REQUIRED_WINDOW_INCOMPLETE in result.block_reasons
    assert result.lifecycle_state is CanonicalScopeLifecycleState.SCOPE_WARMING_UP


def test_instrument_metadata_invalid_blocked() -> None:
    result = _initialize(prerequisites=_prerequisites(instrument_metadata_valid=False))
    assert CanonicalScopeBlockReason.INSTRUMENT_METADATA_INVALID in result.block_reasons


def test_market_context_not_finalized_flag_blocked() -> None:
    result = _initialize(prerequisites=_prerequisites(finalized_market_context=False))
    assert CanonicalScopeBlockReason.MARKET_CONTEXT_NOT_FINALIZED in result.block_reasons


def test_mark_price_non_positive_invalid() -> None:
    result = _initialize(market_context=_context(mark_price=0.0))
    assert result.lifecycle_state is CanonicalScopeLifecycleState.SCOPE_INVALID
    assert CanonicalScopeBlockReason.MARK_PRICE_NON_POSITIVE in result.block_reasons


def test_negative_volatility_invalid() -> None:
    result = _initialize(market_context=_context(volatility_estimate=-0.01))
    assert result.lifecycle_state is CanonicalScopeLifecycleState.SCOPE_INVALID
    assert CanonicalScopeBlockReason.VOLATILITY_NEGATIVE in result.block_reasons


def test_min_scope_band_non_positive_invalid() -> None:
    blocks = validate_scope_initialization_policy(_policy(min_scope_band=0.0))
    assert CanonicalScopeBlockReason.MIN_SCOPE_BAND_NON_POSITIVE in blocks
    result = _initialize(policy=_policy(min_scope_band=0.0))
    assert result.lifecycle_state is CanonicalScopeLifecycleState.SCOPE_INVALID


def test_max_scope_band_lt_min_invalid() -> None:
    blocks = validate_scope_initialization_policy(
        _policy(min_scope_band=100.0, max_scope_band=50.0)
    )
    assert CanonicalScopeBlockReason.MAX_SCOPE_BAND_LT_MIN in blocks


def test_no_implicit_policy_defaults_required_explicit_policy() -> None:
    with pytest.raises(TypeError):
        CanonicalScopeInitializationPolicyV1()  # type: ignore[call-arg]


def test_reinitialization_blocked_open_position() -> None:
    first = _initialize()
    assert first.scope is not None
    second = _initialize(
        existing_scope=first.scope,
        reinitialization_guard=ScopeReinitializationGuardV1(has_open_position=True),
    )
    assert CanonicalScopeBlockReason.REINITIALIZATION_OPEN_POSITION in second.block_reasons


def test_reinitialization_blocked_unknown_position() -> None:
    first = _initialize()
    assert first.scope is not None
    second = _initialize(
        existing_scope=first.scope,
        reinitialization_guard=ScopeReinitializationGuardV1(has_unknown_position=True),
    )
    assert CanonicalScopeBlockReason.REINITIALIZATION_UNKNOWN_POSITION in second.block_reasons


def test_reinitialization_blocked_unresolved_increase_order() -> None:
    first = _initialize()
    assert first.scope is not None
    second = _initialize(
        existing_scope=first.scope,
        reinitialization_guard=ScopeReinitializationGuardV1(has_unresolved_increase_order=True),
    )
    assert (
        CanonicalScopeBlockReason.REINITIALIZATION_UNRESOLVED_INCREASE_ORDER in second.block_reasons
    )


def test_reinitialization_blocked_unresolved_reduce_order() -> None:
    first = _initialize()
    assert first.scope is not None
    second = _initialize(
        existing_scope=first.scope,
        reinitialization_guard=ScopeReinitializationGuardV1(has_unresolved_reduce_order=True),
    )
    assert (
        CanonicalScopeBlockReason.REINITIALIZATION_UNRESOLVED_REDUCE_ORDER in second.block_reasons
    )


def test_reinitialization_blocked_submission_unknown() -> None:
    first = _initialize()
    assert first.scope is not None
    second = _initialize(
        existing_scope=first.scope,
        reinitialization_guard=ScopeReinitializationGuardV1(has_submission_unknown=True),
    )
    assert CanonicalScopeBlockReason.REINITIALIZATION_SUBMISSION_UNKNOWN in second.block_reasons


def test_reinitialization_blocked_not_reconciled() -> None:
    first = _initialize()
    assert first.scope is not None
    second = _initialize(
        existing_scope=first.scope,
        reinitialization_guard=ScopeReinitializationGuardV1(reconciliation_status="PENDING"),
    )
    assert CanonicalScopeBlockReason.REINITIALIZATION_NOT_RECONCILED in second.block_reasons


def test_no_authority_runtime_or_order_effects() -> None:
    result = _initialize()
    assert not result.is_authority
    assert not result.runtime_effect
    assert not result.order_effect
    assert not result.execution_eligible
    assert not result.live_authorization
    assert not result.scope_event_generated


def test_no_scope_event_generated() -> None:
    result = _initialize()
    assert result.scope_event_generated is False


def test_existing_market_context_regression_still_importable() -> None:
    from trading.master_v2.canonical_market_context_v1 import (
        evaluate_canonical_market_context_eligibility,
    )

    ctx = with_computed_input_digest(_context())
    elig = evaluate_canonical_market_context_eligibility(ctx)
    assert elig.trading_decision_allowed


def test_futures_only_spot_instrument_id_rejected() -> None:
    result = _initialize(market_context=_context(instrument_id="inst-spot-eth"))
    assert CanonicalScopeBlockReason.MARKET_CONTEXT_FIELD_INVALID in result.block_reasons


def test_synthetic_spot_instrument_id_rejected() -> None:
    result = _initialize(market_context=_context(instrument_id="inst-synthetic_spot-eth"))
    assert CanonicalScopeBlockReason.MARKET_CONTEXT_FIELD_INVALID in result.block_reasons


def test_no_bitcoin_semantics_in_scope_output() -> None:
    result = _initialize(
        market_context=_context(
            instrument_id="inst-sol-usdt-perp",
            context_id="ctx-sol-perp-epoch1-ev1",
        )
    )
    assert result.scope is not None
    serialized = serialize_canonical_scope_canonical(result.scope).lower()
    assert "btc" not in serialized
    assert "bitcoin" not in serialized
    assert "xbt" not in serialized


def test_classify_scope_lifecycle_state_helpers() -> None:
    assert (
        classify_scope_lifecycle_state((CanonicalScopeBlockReason.WARMUP_INCOMPLETE,))
        is CanonicalScopeLifecycleState.SCOPE_WARMING_UP
    )
    assert (
        classify_scope_lifecycle_state((CanonicalScopeBlockReason.VOLATILITY_NEGATIVE,))
        is CanonicalScopeLifecycleState.SCOPE_INVALID
    )


def test_with_computed_semantic_digest_round_trip() -> None:
    result = _initialize()
    assert result.scope is not None
    bare = CanonicalScopeSnapshotV1(
        scope_id=result.scope.scope_id,
        instrument_id=result.scope.instrument_id,
        initialized_at_trading_epoch=result.scope.initialized_at_trading_epoch,
        source_market_context_id=result.scope.source_market_context_id,
        source_input_digest=result.scope.source_input_digest,
        lifecycle_state=result.scope.lifecycle_state,
        reference_price=result.scope.reference_price,
        volatility_estimate=result.scope.volatility_estimate,
        initial_volatility_distance=result.scope.initial_volatility_distance,
        scope_band=result.scope.scope_band,
        neutral_upper_boundary=result.scope.neutral_upper_boundary,
        neutral_lower_boundary=result.scope.neutral_lower_boundary,
        trailing_anchor=result.scope.trailing_anchor,
        min_scope_band=result.scope.min_scope_band,
        max_scope_band=result.scope.max_scope_band,
        policy_version=result.scope.policy_version,
        semantic_digest="",
        reason_codes=result.scope.reason_codes,
    )
    bound = with_computed_semantic_digest(bare)
    assert bound.semantic_digest == result.scope.semantic_digest


def test_no_runtime_order_or_execution_side_effects_in_module() -> None:
    root = Path(__file__).resolve().parent.parent.parent.parent / "src" / "trading" / "master_v2"
    path = root / "canonical_scope_initialization_v1.py"
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
