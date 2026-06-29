# tests/trading/master_v2/test_deterministic_scope_event_generator_v1.py
from __future__ import annotations

import ast
from dataclasses import replace
from pathlib import Path

import pytest

from trading.master_v2.canonical_market_context_v1 import (
    BarFinalityStatus,
    ClockTrustStatus,
    DataIntegrityStatus,
)
from trading.master_v2.canonical_scope_initialization_v1 import (
    CanonicalScopeLifecycleState,
    CanonicalScopeSnapshotV1,
    SCOPE_INITIALIZATION_POLICY_VERSION,
    with_computed_semantic_digest,
)
from trading.master_v2.deterministic_scope_event_generator_v1 import (
    CHOP_POLICY_STATUS,
    DETERMINISTIC_SCOPE_EVENT_GENERATOR_LAYER_VERSION,
    SCOPE_EVENT_GENERATOR_POLICY_VERSION,
    CanonicalScopeEventType,
    ScopeCandidateKind,
    ScopeConfirmationStateV1,
    ScopeCooldownStateV1,
    ScopeDirectionState,
    ScopeEventBlockReason,
    ScopeEventGeneratorInputV1,
    ScopeEventGeneratorPolicyV1,
    compute_evaluated_thresholds,
    compute_scope_event_semantic_digest,
    generate_deterministic_scope_event,
    mirror_price_for_short,
    serialize_scope_event_evidence_canonical,
    validate_scope_event_generator_policy,
    with_computed_scope_event_digest,
)


def _scope(**overrides: object) -> CanonicalScopeSnapshotV1:
    base: dict = {
        "scope_id": "scope-inst-eth-usdt-perp-epoch42-ctx1",
        "instrument_id": "inst-eth-usdt-perp",
        "initialized_at_trading_epoch": 42,
        "source_market_context_id": "ctx-eth-perp-epoch42-ev1",
        "source_input_digest": "a" * 64,
        "lifecycle_state": CanonicalScopeLifecycleState.SCOPE_VALID,
        "reference_price": 3500.0,
        "volatility_estimate": 0.38,
        "initial_volatility_distance": 1330.0,
        "scope_band": 500.0,
        "neutral_upper_boundary": 4000.0,
        "neutral_lower_boundary": 3000.0,
        "trailing_anchor": 3500.0,
        "min_scope_band": 50.0,
        "max_scope_band": 500.0,
        "policy_version": SCOPE_INITIALIZATION_POLICY_VERSION,
        "semantic_digest": "",
        "reason_codes": (),
    }
    base.update(overrides)
    scope = CanonicalScopeSnapshotV1(**base)
    return with_computed_semantic_digest(scope)


def _policy(**overrides: object) -> ScopeEventGeneratorPolicyV1:
    base: dict = {
        "hard_max_scope_distance": 1000.0,
        "hard_max_adverse_distance": 500.0,
        "hard_max_reversal_distance": 800.0,
        "policy_version": SCOPE_EVENT_GENERATOR_POLICY_VERSION,
    }
    base.update(overrides)
    return ScopeEventGeneratorPolicyV1(**base)


def _confirmation(**overrides: object) -> ScopeConfirmationStateV1:
    base: dict = {
        "candidate_kind": None,
        "candidate_count": 0,
        "last_evaluated_trading_epoch": -1,
    }
    base.update(overrides)
    return ScopeConfirmationStateV1(**base)


def _cooldown(**overrides: object) -> ScopeCooldownStateV1:
    base: dict = {
        "active": False,
        "remaining_epochs": 0,
        "policy_version": SCOPE_EVENT_GENERATOR_POLICY_VERSION,
    }
    base.update(overrides)
    return ScopeCooldownStateV1(**base)


def _input(**overrides: object) -> ScopeEventGeneratorInputV1:
    scope = overrides.pop("current_scope", _scope())
    base: dict = {
        "instrument_id": scope.instrument_id,
        "trading_epoch": 43,
        "market_context_id": "ctx-eth-perp-epoch43-ev1",
        "market_context_digest": "b" * 64,
        "current_scope": scope,
        "current_direction_state": ScopeDirectionState.LONG,
        "reference_price": 3500.0,
        "current_price": 3500.0,
        "trailing_anchor": 3500.0,
        "up_distance": 100.0,
        "adverse_exit_distance": 80.0,
        "reversal_distance": 120.0,
        "confirmation_epochs": 2,
        "confirmation_state": _confirmation(last_evaluated_trading_epoch=42),
        "cooldown_state": _cooldown(),
        "cooldown_remaining_epochs": 0,
        "data_integrity_status": DataIntegrityStatus.TRUSTED,
        "clock_trust_status": ClockTrustStatus.TRUSTED,
        "bar_finality_status": BarFinalityStatus.FINALIZED,
        "policy_version": SCOPE_EVENT_GENERATOR_POLICY_VERSION,
    }
    base.update(overrides)
    return ScopeEventGeneratorInputV1(**base)


def _generate(**kwargs: object):
    inp = kwargs.pop("inp", _input(**{k: v for k, v in kwargs.items() if k != "policy"}))
    policy = kwargs.pop("policy", _policy())
    return generate_deterministic_scope_event(inp, policy)


def test_layer_version_and_chop_policy_status() -> None:
    assert DETERMINISTIC_SCOPE_EVENT_GENERATOR_LAYER_VERSION == "v1"
    assert CHOP_POLICY_STATUS == "NOT_BOUND"


def test_long_upscope_candidate_first_epoch() -> None:
    evidence = _generate(current_price=3605.0)
    assert evidence.event_type is CanonicalScopeEventType.UPSCOPE_CANDIDATE
    assert evidence.candidate_count_after == 1
    assert evidence.next_confirmation_state.candidate_kind is ScopeCandidateKind.UPSCOPE


def test_long_upscope_confirmation_after_consecutive_epochs() -> None:
    first = _generate(
        trading_epoch=43,
        current_price=3605.0,
        confirmation_state=_confirmation(last_evaluated_trading_epoch=42),
    )
    assert first.event_type is CanonicalScopeEventType.UPSCOPE_CANDIDATE
    second = _generate(
        trading_epoch=44,
        current_price=3610.0,
        confirmation_state=first.next_confirmation_state,
    )
    assert second.event_type is CanonicalScopeEventType.UPSCOPE_CONFIRMED
    assert second.next_scope_effective_epoch == 45


def test_short_upscope_candidate_mirrored_structure() -> None:
    anchor = 3500.0
    up_distance = 100.0
    long_price = anchor + up_distance + 5.0
    short_price = mirror_price_for_short(long_price, anchor)
    evidence = _generate(
        current_direction_state=ScopeDirectionState.SHORT,
        current_price=short_price,
        trailing_anchor=anchor,
    )
    assert evidence.event_type is CanonicalScopeEventType.UPSCOPE_CANDIDATE


def test_long_downscope_candidate() -> None:
    evidence = _generate(
        up_distance=50.0,
        adverse_exit_distance=80.0,
        reversal_distance=120.0,
        current_price=3440.0,
    )
    assert evidence.event_type is CanonicalScopeEventType.DOWNSCOPE_CANDIDATE
    assert ScopeCandidateKind.DOWNSCOPE.value in evidence.matched_conditions


def test_long_downscope_confirmation() -> None:
    distances = {
        "up_distance": 50.0,
        "adverse_exit_distance": 80.0,
        "reversal_distance": 120.0,
    }
    first = _generate(
        trading_epoch=43,
        current_price=3440.0,
        confirmation_state=_confirmation(last_evaluated_trading_epoch=42),
        **distances,
    )
    second = _generate(
        trading_epoch=44,
        current_price=3435.0,
        confirmation_state=first.next_confirmation_state,
        **distances,
    )
    assert second.event_type is CanonicalScopeEventType.DOWNSCOPE_CONFIRMED


def test_long_adverse_exit_candidate() -> None:
    evidence = _generate(current_price=3410.0)
    assert evidence.event_type is CanonicalScopeEventType.ADVERSE_EXIT_CANDIDATE


def test_short_adverse_exit_candidate_mirrored() -> None:
    anchor = 3500.0
    long_adverse_price = anchor - 80.0 - 5.0
    short_price = mirror_price_for_short(long_adverse_price, anchor)
    evidence = _generate(
        current_direction_state=ScopeDirectionState.SHORT,
        current_price=short_price,
        trailing_anchor=anchor,
    )
    assert evidence.event_type is CanonicalScopeEventType.ADVERSE_EXIT_CANDIDATE


def test_event_precedence_block_before_candidate() -> None:
    evidence = _generate(
        current_price=3605.0,
        up_distance=0.0,
    )
    assert evidence.event_type is CanonicalScopeEventType.SCOPE_BLOCKED
    assert ScopeEventBlockReason.POLICY_UP_DISTANCE_INVALID.value in evidence.blocked_reasons


def test_event_precedence_adverse_before_favorable_candidate() -> None:
    evidence = _generate(current_price=3390.0)
    assert evidence.event_type is CanonicalScopeEventType.ADVERSE_EXIT_CANDIDATE
    assert ScopeCandidateKind.ADVERSE_EXIT.value in evidence.matched_conditions


def test_candidate_count_starts_at_one() -> None:
    evidence = _generate(current_price=3605.0)
    assert evidence.candidate_count_before == 0
    assert evidence.candidate_count_after == 1


def test_candidate_count_increments_only_on_consecutive_epoch() -> None:
    first = _generate(
        trading_epoch=43,
        current_price=3605.0,
        confirmation_state=_confirmation(last_evaluated_trading_epoch=42),
    )
    second = _generate(
        trading_epoch=44,
        current_price=3610.0,
        confirmation_state=first.next_confirmation_state,
    )
    assert second.candidate_count_after == 2


def test_candidate_reset_when_condition_no_longer_true() -> None:
    first = _generate(
        trading_epoch=43,
        current_price=3605.0,
        confirmation_state=_confirmation(last_evaluated_trading_epoch=42),
    )
    second = _generate(
        trading_epoch=44,
        current_price=3500.0,
        confirmation_state=first.next_confirmation_state,
    )
    assert second.event_type is CanonicalScopeEventType.NOOP
    assert second.next_confirmation_state.candidate_count == 0
    assert second.next_confirmation_state.candidate_kind is None


def test_candidate_reset_on_opposite_signal() -> None:
    upscope = _generate(
        trading_epoch=43,
        current_price=3605.0,
        confirmation_state=_confirmation(last_evaluated_trading_epoch=42),
    )
    downscope = _generate(
        trading_epoch=44,
        current_price=3390.0,
        confirmation_state=upscope.next_confirmation_state,
    )
    assert downscope.next_confirmation_state.candidate_kind is ScopeCandidateKind.ADVERSE_EXIT
    assert downscope.next_confirmation_state.candidate_count == 1


def test_duplicate_epoch_is_idempotent() -> None:
    frozen = ScopeConfirmationStateV1(
        candidate_kind=ScopeCandidateKind.UPSCOPE,
        candidate_count=1,
        last_evaluated_trading_epoch=43,
    )
    inp = _input(
        trading_epoch=43,
        current_price=3605.0,
        confirmation_state=frozen,
    )
    policy = _policy()
    first = generate_deterministic_scope_event(inp, policy)
    second = generate_deterministic_scope_event(inp, policy)
    assert second.candidate_count_after == first.candidate_count_after
    assert second.semantic_digest == first.semantic_digest


def test_out_of_order_epoch_fail_closed() -> None:
    evidence = _generate(
        trading_epoch=41,
        confirmation_state=_confirmation(last_evaluated_trading_epoch=43),
    )
    assert evidence.event_type is CanonicalScopeEventType.SCOPE_BLOCKED
    assert ScopeEventBlockReason.TRADING_EPOCH_OUT_OF_ORDER.value in evidence.blocked_reasons


def test_skipped_epoch_resets_candidate() -> None:
    prior = _generate(
        trading_epoch=43,
        current_price=3605.0,
        confirmation_state=_confirmation(last_evaluated_trading_epoch=42),
    )
    skipped = _generate(
        trading_epoch=45,
        current_price=3605.0,
        confirmation_state=prior.next_confirmation_state,
    )
    assert skipped.next_confirmation_state.candidate_count == 1
    assert skipped.event_type is CanonicalScopeEventType.UPSCOPE_CANDIDATE


def test_confirmation_epochs_zero_invalid() -> None:
    blocks = validate_scope_event_generator_policy(
        _policy(),
        up_distance=100.0,
        adverse_exit_distance=80.0,
        reversal_distance=120.0,
        confirmation_epochs=0,
        policy_version=SCOPE_EVENT_GENERATOR_POLICY_VERSION,
    )
    assert ScopeEventBlockReason.POLICY_CONFIRMATION_EPOCHS_INVALID in blocks


def test_up_distance_zero_invalid() -> None:
    evidence = _generate(up_distance=0.0, current_price=3605.0)
    assert evidence.event_type is CanonicalScopeEventType.SCOPE_BLOCKED


def test_adverse_exit_distance_zero_invalid() -> None:
    evidence = _generate(adverse_exit_distance=0.0, current_price=3410.0)
    assert evidence.event_type is CanonicalScopeEventType.SCOPE_BLOCKED


def test_reversal_distance_zero_invalid() -> None:
    evidence = _generate(reversal_distance=0.0, current_price=3410.0)
    assert evidence.event_type is CanonicalScopeEventType.SCOPE_BLOCKED


def test_adverse_exit_distance_exceeds_reversal_invalid() -> None:
    evidence = _generate(
        adverse_exit_distance=150.0,
        reversal_distance=120.0,
        current_price=3410.0,
    )
    assert ScopeEventBlockReason.POLICY_ADVERSE_EXCEEDS_REVERSAL.value in evidence.blocked_reasons


def test_hard_max_scope_distance_exceeded() -> None:
    evidence = _generate(up_distance=1500.0, current_price=5000.0)
    assert ScopeEventBlockReason.POLICY_HARD_MAX_SCOPE_EXCEEDED.value in evidence.blocked_reasons


def test_unfinalized_bar_blocks() -> None:
    evidence = _generate(bar_finality_status=BarFinalityStatus.UNFINALIZED, current_price=3605.0)
    assert ScopeEventBlockReason.BAR_UNFINALIZED.value in evidence.blocked_reasons


def test_data_integrity_unknown_blocks() -> None:
    evidence = _generate(
        data_integrity_status=DataIntegrityStatus.UNKNOWN,
        current_price=3605.0,
    )
    assert ScopeEventBlockReason.DATA_INTEGRITY_UNKNOWN.value in evidence.blocked_reasons


def test_data_integrity_untrusted_blocks() -> None:
    evidence = _generate(
        data_integrity_status=DataIntegrityStatus.UNTRUSTED,
        current_price=3605.0,
    )
    assert ScopeEventBlockReason.DATA_INTEGRITY_UNTRUSTED.value in evidence.blocked_reasons


def test_clock_trust_unknown_blocks() -> None:
    evidence = _generate(
        clock_trust_status=ClockTrustStatus.UNKNOWN,
        current_price=3605.0,
    )
    assert ScopeEventBlockReason.CLOCK_TRUST_UNKNOWN.value in evidence.blocked_reasons


def test_clock_trust_untrusted_blocks() -> None:
    evidence = _generate(
        clock_trust_status=ClockTrustStatus.UNTRUSTED,
        current_price=3605.0,
    )
    assert ScopeEventBlockReason.CLOCK_TRUST_UNTRUSTED.value in evidence.blocked_reasons


@pytest.mark.parametrize(
    "lifecycle,reason",
    [
        (
            CanonicalScopeLifecycleState.SCOPE_UNINITIALIZED,
            ScopeEventBlockReason.SCOPE_UNINITIALIZED,
        ),
        (CanonicalScopeLifecycleState.SCOPE_WARMING_UP, ScopeEventBlockReason.SCOPE_WARMING_UP),
        (CanonicalScopeLifecycleState.SCOPE_STALE, ScopeEventBlockReason.SCOPE_STALE),
        (CanonicalScopeLifecycleState.SCOPE_INVALID, ScopeEventBlockReason.SCOPE_INVALID),
    ],
)
def test_non_valid_scope_lifecycle_blocks(lifecycle, reason) -> None:
    scope = _scope(lifecycle_state=lifecycle)
    evidence = _generate(current_scope=scope, current_price=3605.0)
    assert evidence.event_type is CanonicalScopeEventType.SCOPE_BLOCKED
    assert reason.value in evidence.blocked_reasons


def test_scope_valid_allows_evaluation() -> None:
    evidence = _generate(current_price=3605.0)
    assert evidence.event_type is CanonicalScopeEventType.UPSCOPE_CANDIDATE


def test_active_cooldown_prevents_new_confirmation() -> None:
    first = _generate(
        trading_epoch=43,
        current_price=3605.0,
        confirmation_state=_confirmation(last_evaluated_trading_epoch=42),
    )
    blocked = _generate(
        trading_epoch=44,
        current_price=3610.0,
        confirmation_state=first.next_confirmation_state,
        cooldown_state=_cooldown(active=True, remaining_epochs=3),
        cooldown_remaining_epochs=3,
    )
    assert blocked.event_type is CanonicalScopeEventType.SCOPE_BLOCKED
    assert ScopeEventBlockReason.COOLDOWN_ACTIVE.value in blocked.blocked_reasons


def test_active_cooldown_allows_adverse_exit_evidence() -> None:
    evidence = _generate(
        current_price=3410.0,
        cooldown_state=_cooldown(active=True, remaining_epochs=2),
        cooldown_remaining_epochs=2,
    )
    assert evidence.event_type is CanonicalScopeEventType.ADVERSE_EXIT_CANDIDATE


def test_current_scope_remains_unchanged() -> None:
    scope = _scope()
    evidence = _generate(current_scope=scope, current_price=3605.0)
    assert evidence.current_scope_ref is scope
    assert evidence.current_scope_ref.trailing_anchor == scope.trailing_anchor


def test_next_scope_effective_next_epoch_only_on_confirmed() -> None:
    candidate = _generate(
        trading_epoch=43,
        current_price=3605.0,
        confirmation_state=_confirmation(last_evaluated_trading_epoch=42),
    )
    assert candidate.next_scope_effective_epoch is None
    confirmed = _generate(
        trading_epoch=44,
        current_price=3610.0,
        confirmation_state=candidate.next_confirmation_state,
    )
    assert confirmed.next_scope_effective_epoch == 45


def test_no_authority_runtime_order_or_position_effects() -> None:
    evidence = _generate(current_price=3605.0)
    assert evidence.authority_effect == "NONE"
    assert evidence.runtime_effect == "NONE"
    assert evidence.order_effect == "NONE"
    assert evidence.position_effect == "NONE"


def test_deterministic_output() -> None:
    inp = _input(current_price=3605.0)
    policy = _policy()
    a = generate_deterministic_scope_event(inp, policy)
    b = generate_deterministic_scope_event(inp, policy)
    assert a == b


def test_deterministic_digest() -> None:
    evidence = _generate(current_price=3605.0)
    recomputed = compute_scope_event_semantic_digest(evidence)
    assert evidence.semantic_digest == recomputed


def test_semantic_field_change_changes_digest() -> None:
    first = _generate(current_price=3605.0)
    second = _generate(current_price=3606.0)
    assert first.semantic_digest != second.semantic_digest


def test_unordered_blocked_reason_codes_do_not_change_digest() -> None:
    inp = _input(
        bar_finality_status=BarFinalityStatus.UNFINALIZED,
        data_integrity_status=DataIntegrityStatus.UNKNOWN,
        current_price=3605.0,
    )
    evidence = generate_deterministic_scope_event(inp, _policy())
    payload = serialize_scope_event_evidence_canonical(evidence)
    assert '"bar_unfinalized"' in payload
    assert '"data_integrity_unknown"' in payload


def test_long_short_mirror_structural_sequence() -> None:
    anchor = 4000.0
    up_distance = 50.0
    long_price = anchor + up_distance + 1.0
    short_price = mirror_price_for_short(long_price, anchor)
    long_evidence = _generate(
        current_direction_state=ScopeDirectionState.LONG,
        trailing_anchor=anchor,
        reference_price=anchor,
        current_price=long_price,
        up_distance=up_distance,
        adverse_exit_distance=40.0,
        reversal_distance=60.0,
    )
    short_evidence = _generate(
        current_direction_state=ScopeDirectionState.SHORT,
        trailing_anchor=anchor,
        reference_price=anchor,
        current_price=short_price,
        up_distance=up_distance,
        adverse_exit_distance=40.0,
        reversal_distance=60.0,
    )
    assert long_evidence.event_type is CanonicalScopeEventType.UPSCOPE_CANDIDATE
    assert short_evidence.event_type is CanonicalScopeEventType.UPSCOPE_CANDIDATE


def test_compute_evaluated_thresholds_long_and_short() -> None:
    long_t = compute_evaluated_thresholds(
        direction=ScopeDirectionState.LONG,
        trailing_anchor=100.0,
        up_distance=10.0,
        adverse_exit_distance=8.0,
        reversal_distance=12.0,
    )
    short_t = compute_evaluated_thresholds(
        direction=ScopeDirectionState.SHORT,
        trailing_anchor=100.0,
        up_distance=10.0,
        adverse_exit_distance=8.0,
        reversal_distance=12.0,
    )
    assert long_t.up_candidate_threshold == pytest.approx(110.0)
    assert short_t.up_candidate_threshold == pytest.approx(90.0)
    assert long_t.adverse_exit_threshold == pytest.approx(92.0)
    assert short_t.adverse_exit_threshold == pytest.approx(108.0)


def test_futures_only_spot_instrument_rejected() -> None:
    scope = _scope(instrument_id="inst-spot-eth-usdt")
    evidence = _generate(current_scope=scope, current_price=3605.0)
    assert ScopeEventBlockReason.INSTRUMENT_KIND_FORBIDDEN.value in evidence.blocked_reasons


def test_no_bitcoin_semantics_in_output() -> None:
    scope = _scope(
        instrument_id="inst-sol-usdt-perp",
        scope_id="scope-inst-sol-usdt-perp-epoch43-ctx1",
    )
    evidence = _generate(current_scope=scope, current_price=3605.0)
    serialized = serialize_scope_event_evidence_canonical(evidence).lower()
    assert "btc" not in serialized
    assert "bitcoin" not in serialized
    assert "xbt" not in serialized


def test_synthetic_spot_instrument_rejected() -> None:
    scope = _scope(instrument_id="inst-synthetic_spot-eth")
    evidence = _generate(current_scope=scope, current_price=3605.0)
    assert ScopeEventBlockReason.INSTRUMENT_KIND_FORBIDDEN.value in evidence.blocked_reasons


def test_chop_detected_not_emitted_without_bound_policy() -> None:
    evidence = _generate(current_price=3605.0)
    assert evidence.event_type is not CanonicalScopeEventType.CHOP_DETECTED
    assert CHOP_POLICY_STATUS == "NOT_BOUND"


def test_with_computed_scope_event_digest_round_trip() -> None:
    evidence = _generate(current_price=3605.0)
    bare = replace(evidence, semantic_digest="")
    bound = with_computed_scope_event_digest(bare)
    assert bound.semantic_digest == evidence.semantic_digest


def test_no_runtime_order_or_execution_side_effects_in_module() -> None:
    root = Path(__file__).resolve().parent.parent.parent.parent / "src" / "trading" / "master_v2"
    path = root / "deterministic_scope_event_generator_v1.py"
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


def test_step29c_regression_imports_still_work() -> None:
    from trading.master_v2.canonical_scope_initialization_v1 import initialize_canonical_scope

    assert initialize_canonical_scope is not None


def test_step29b_regression_imports_still_work() -> None:
    from trading.master_v2.canonical_market_context_v1 import CanonicalMarketContextV1

    assert CanonicalMarketContextV1 is not None
