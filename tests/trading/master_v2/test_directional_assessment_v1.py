# tests/trading/master_v2/test_directional_assessment_v1.py
from __future__ import annotations

import ast
import inspect
from dataclasses import fields, replace
from pathlib import Path

import pytest

from trading.master_v2.canonical_market_context_v1 import (
    BarFinalityStatus,
    ClockTrustStatus,
    DataIntegrityStatus,
)
from trading.master_v2.deterministic_scope_event_generator_v1 import mirror_price_for_short
from trading.master_v2.directional_assessment_v1 import (
    DIRECTIONAL_ASSESSMENT_LAYER_VERSION,
    DIRECTIONAL_ASSESSMENT_POLICY_VERSION,
    DirectionalAssessmentHardBlockReason,
    DirectionalAssessmentInputV1,
    DirectionalAssessmentPolicyV1,
    DirectionalAssessmentSide,
    DirectionalAssessmentStatus,
    DirectionalAssessmentV1,
    DirectionalConfirmationStateV1,
    ScopeEventRefV1,
    compute_directional_assessment_semantic_digest,
    compute_directional_confidence,
    compute_signal_strength,
    evaluate_directional_assessment_v1,
    mirror_price_path_for_short,
    normalize_bull_bear_side,
    serialize_directional_assessment_canonical,
    validate_directional_assessment_policy,
    with_computed_directional_assessment_digest,
)


def _scope_ref(**overrides: object) -> ScopeEventRefV1:
    base: dict = {
        "scope_event_id": "scope-event-inst-eth-usdt-perp-epoch42-upscope_candidate",
        "semantic_digest": "a" * 64,
        "event_type": "upscope_candidate",
        "trading_epoch": 42,
    }
    base.update(overrides)
    return ScopeEventRefV1(**base)


def _confirmation(**overrides: object) -> DirectionalConfirmationStateV1:
    base: dict = {
        "candidate_count": 0,
        "last_evaluated_trading_epoch": -1,
        "last_signal_strength": 0.0,
    }
    base.update(overrides)
    return DirectionalConfirmationStateV1(**base)


def _policy(**overrides: object) -> DirectionalAssessmentPolicyV1:
    base: dict = {
        "observe_signal_threshold": 0.001,
        "candidate_signal_threshold": 0.005,
        "confirmation_signal_threshold": 0.01,
        "confirmation_epochs": 2,
        "validity_epochs": 3,
        "policy_version": DIRECTIONAL_ASSESSMENT_POLICY_VERSION,
    }
    base.update(overrides)
    return DirectionalAssessmentPolicyV1(**base)


def _input(**overrides: object) -> DirectionalAssessmentInputV1:
    base: dict = {
        "instrument_id": "inst-eth-usdt-perp",
        "trading_epoch": 43,
        "side": DirectionalAssessmentSide.LONG,
        "price_path": (3500.0, 3540.0),
        "reference_price": 3500.0,
        "feature_refs": ("feat-momentum-v1", "feat-trend-v1"),
        "scope_event_ref": _scope_ref(),
        "survival_preconditions": ("survival_precondition_ref_only",),
        "confirmation_state": _confirmation(last_evaluated_trading_epoch=42),
        "data_integrity_status": DataIntegrityStatus.TRUSTED,
        "clock_trust_status": ClockTrustStatus.TRUSTED,
        "bar_finality_status": BarFinalityStatus.FINALIZED,
        "trusted_data": True,
        "input_complete": True,
        "explicit_hard_block_reasons": (),
        "policy_version": DIRECTIONAL_ASSESSMENT_POLICY_VERSION,
    }
    base.update(overrides)
    return DirectionalAssessmentInputV1(**base)


def _evaluate(**kwargs: object) -> DirectionalAssessmentV1:
    inp = kwargs.pop("inp", _input(**{k: v for k, v in kwargs.items() if k != "policy"}))
    policy = kwargs.pop("policy", _policy())
    return evaluate_directional_assessment_v1(inp, policy)


def test_1_contract_schema_complete() -> None:
    names = {f.name for f in fields(DirectionalAssessmentV1)}
    required = {
        "assessment_id",
        "side",
        "instrument_id",
        "trading_epoch",
        "status",
        "signal_strength",
        "confidence",
        "feature_refs",
        "scope_event_ref",
        "survival_preconditions",
        "hard_block_reasons",
        "reason_codes",
        "valid_until_epoch",
        "semantic_digest",
    }
    assert required.issubset(names)


def test_2_status_enum_exhaustiveness() -> None:
    assert {s.value for s in DirectionalAssessmentStatus} == {
        "invalid",
        "blocked",
        "observe",
        "candidate",
        "confirmed",
    }


def test_3_deterministic_serialization() -> None:
    assessment = _evaluate()
    first = serialize_directional_assessment_canonical(assessment)
    second = serialize_directional_assessment_canonical(assessment)
    assert first == second
    assert json_loads_safe(first) == json_loads_safe(second)


def json_loads_safe(text: str) -> dict:
    import json

    return json.loads(text)


def test_4_stable_semantic_digest() -> None:
    assessment = _evaluate()
    recomputed = compute_directional_assessment_semantic_digest(assessment)
    assert assessment.semantic_digest == recomputed


def test_5_digest_changes_on_semantic_input_change() -> None:
    first = _evaluate(price_path=(3500.0, 3540.0))
    second = _evaluate(price_path=(3500.0, 3550.0))
    assert first.semantic_digest != second.semantic_digest


def test_6_identical_inputs_identical_assessment() -> None:
    inp = _input()
    policy = _policy()
    assert evaluate_directional_assessment_v1(inp, policy) == evaluate_directional_assessment_v1(
        inp, policy
    )


def test_7_bull_bear_mirror_structural_outcome() -> None:
    anchor = 4000.0
    long_path = (anchor, anchor + 50.0)
    short_path = mirror_price_path_for_short(long_path, anchor)
    long_result = _evaluate(
        side=DirectionalAssessmentSide.LONG,
        price_path=long_path,
        reference_price=anchor,
    )
    short_result = _evaluate(
        side=DirectionalAssessmentSide.SHORT,
        price_path=short_path,
        reference_price=anchor,
    )
    assert long_result.status is DirectionalAssessmentStatus.CANDIDATE
    assert short_result.status is DirectionalAssessmentStatus.CANDIDATE
    assert long_result.signal_strength == pytest.approx(short_result.signal_strength)
    assert long_result.confidence == pytest.approx(short_result.confidence)


def test_8_bull_bear_same_contract_type() -> None:
    long_result = _evaluate(side=DirectionalAssessmentSide.LONG)
    short_result = _evaluate(
        side=DirectionalAssessmentSide.SHORT,
        price_path=mirror_price_path_for_short((3500.0, 3540.0), 3500.0),
    )
    assert type(long_result) is DirectionalAssessmentV1
    assert type(short_result) is DirectionalAssessmentV1
    assert normalize_bull_bear_side("bull") is DirectionalAssessmentSide.LONG
    assert normalize_bull_bear_side("bear") is DirectionalAssessmentSide.SHORT


def test_9_untrusted_input_no_candidate_or_confirmed() -> None:
    assessment = _evaluate(trusted_data=False)
    assert assessment.status not in {
        DirectionalAssessmentStatus.CANDIDATE,
        DirectionalAssessmentStatus.CONFIRMED,
    }


def test_10_incomplete_input_invalid_or_blocked() -> None:
    assessment = _evaluate(input_complete=False)
    assert assessment.status in {
        DirectionalAssessmentStatus.INVALID,
        DirectionalAssessmentStatus.BLOCKED,
    }


def test_11_hard_block_reasons_force_fail_closed_status() -> None:
    assessment = _evaluate(
        explicit_hard_block_reasons=(DirectionalAssessmentHardBlockReason.EXPLICIT_HARD_BLOCK,),
        price_path=(3500.0, 3600.0),
    )
    assert assessment.status is DirectionalAssessmentStatus.BLOCKED
    assert (
        DirectionalAssessmentHardBlockReason.EXPLICIT_HARD_BLOCK.value
        in assessment.hard_block_reasons
    )


def test_12_reason_codes_nonempty_for_nontrivial_result() -> None:
    for status in (
        DirectionalAssessmentStatus.CANDIDATE,
        DirectionalAssessmentStatus.CONFIRMED,
        DirectionalAssessmentStatus.BLOCKED,
        DirectionalAssessmentStatus.INVALID,
    ):
        if status is DirectionalAssessmentStatus.CANDIDATE:
            result = _evaluate(price_path=(3500.0, 3540.0))
        elif status is DirectionalAssessmentStatus.CONFIRMED:
            first = _evaluate(
                trading_epoch=43,
                price_path=(3500.0, 3540.0),
                confirmation_state=_confirmation(last_evaluated_trading_epoch=42),
            )
            result = _evaluate(
                trading_epoch=44,
                price_path=(3500.0, 3550.0),
                confirmation_state=DirectionalConfirmationStateV1(
                    candidate_count=1,
                    last_evaluated_trading_epoch=43,
                    last_signal_strength=first.signal_strength,
                ),
                scope_event_ref=_scope_ref(trading_epoch=43),
            )
        elif status is DirectionalAssessmentStatus.BLOCKED:
            result = _evaluate(trusted_data=False)
        else:
            result = _evaluate(price_path=(3500.0,))
        assert result.status is status
        assert result.reason_codes


def test_13_stale_trading_epoch_blocked_or_invalid() -> None:
    assessment = _evaluate(
        trading_epoch=40,
        confirmation_state=_confirmation(last_evaluated_trading_epoch=43),
        scope_event_ref=_scope_ref(trading_epoch=39),
    )
    assert assessment.status in {
        DirectionalAssessmentStatus.BLOCKED,
        DirectionalAssessmentStatus.INVALID,
    }
    assert (
        DirectionalAssessmentHardBlockReason.TRADING_EPOCH_OUT_OF_ORDER.value
        in assessment.hard_block_reasons
    )


def test_14_scope_event_ref_immutable() -> None:
    scope_ref = _scope_ref()
    assessment = _evaluate(scope_event_ref=scope_ref)
    assert assessment.scope_event_ref is scope_ref
    assert assessment.scope_event_ref.semantic_digest == scope_ref.semantic_digest


def test_15_no_runtime_adapter_order_imports_or_side_effects() -> None:
    root = Path(__file__).resolve().parent.parent.parent.parent / "src" / "trading" / "master_v2"
    path = root / "directional_assessment_v1.py"
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
        "execution",
        "risk",
    }
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for n in node.names:
                assert n.name.split(".")[0] not in bad_roots
        if isinstance(node, ast.ImportFrom) and node.module:
            assert node.module.split(".")[0] not in bad_roots
    source = inspect.getsource(evaluate_directional_assessment_v1)
    assert "open(" not in source
    assert "requests." not in source


def test_16_futures_only_spot_instrument_rejected() -> None:
    assessment = _evaluate(instrument_id="inst-spot-eth-usdt")
    assert (
        DirectionalAssessmentHardBlockReason.INSTRUMENT_KIND_FORBIDDEN.value
        in assessment.hard_block_reasons
    )


def test_17_no_bitcoin_semantics_in_output() -> None:
    assessment = _evaluate(instrument_id="inst-sol-usdt-perp")
    serialized = serialize_directional_assessment_canonical(assessment).lower()
    assert "btc" not in serialized
    assert "bitcoin" not in serialized
    assert "xbt" not in serialized


def test_18_long_short_symmetry_thresholds() -> None:
    anchor = 100.0
    policy = _policy(
        observe_signal_threshold=0.001,
        candidate_signal_threshold=0.01,
        confirmation_signal_threshold=0.02,
        confirmation_epochs=2,
    )
    long_strength = compute_signal_strength(
        price_path=(anchor, anchor * 1.02),
        side=DirectionalAssessmentSide.LONG,
        reference_price=anchor,
    )
    short_strength = compute_signal_strength(
        price_path=mirror_price_path_for_short((anchor, anchor * 1.02), anchor),
        side=DirectionalAssessmentSide.SHORT,
        reference_price=anchor,
    )
    assert long_strength == pytest.approx(short_strength)
    long_conf = compute_directional_confidence(long_strength, policy.confirmation_signal_threshold)
    short_conf = compute_directional_confidence(
        short_strength, policy.confirmation_signal_threshold
    )
    assert long_conf == pytest.approx(short_conf)


def test_19_no_implicit_strategy_selection() -> None:
    assessment = _evaluate()
    serialized = serialize_directional_assessment_canonical(assessment)
    assert "strategy" not in serialized.lower()
    assert "selected_strategy" not in serialized.lower()


def test_20_step29b_c_d_regression_imports_still_work() -> None:
    from trading.master_v2.canonical_market_context_v1 import CanonicalMarketContextV1
    from trading.master_v2.canonical_scope_initialization_v1 import initialize_canonical_scope
    from trading.master_v2.deterministic_scope_event_generator_v1 import (
        generate_deterministic_scope_event,
    )

    assert CanonicalMarketContextV1 is not None
    assert initialize_canonical_scope is not None
    assert generate_deterministic_scope_event is not None


def test_layer_version_constant() -> None:
    assert DIRECTIONAL_ASSESSMENT_LAYER_VERSION == "v1"


def test_observe_status_below_threshold() -> None:
    assessment = _evaluate(price_path=(3500.0, 3501.0))
    assert assessment.status is DirectionalAssessmentStatus.OBSERVE


def test_candidate_status_on_strong_move() -> None:
    assessment = _evaluate(price_path=(3500.0, 3540.0))
    assert assessment.status is DirectionalAssessmentStatus.CANDIDATE


def test_confirmed_after_consecutive_epochs() -> None:
    first = _evaluate(
        trading_epoch=43,
        price_path=(3500.0, 3540.0),
        confirmation_state=_confirmation(last_evaluated_trading_epoch=42),
    )
    second = _evaluate(
        trading_epoch=44,
        price_path=(3500.0, 3550.0),
        confirmation_state=DirectionalConfirmationStateV1(
            candidate_count=1,
            last_evaluated_trading_epoch=43,
            last_signal_strength=first.signal_strength,
        ),
        scope_event_ref=_scope_ref(trading_epoch=43),
    )
    assert second.status is DirectionalAssessmentStatus.CONFIRMED


def test_valid_until_epoch_explicit_and_bounded() -> None:
    assessment = _evaluate(trading_epoch=43)
    assert assessment.valid_until_epoch == 46


def test_no_authority_runtime_order_or_risk_effects() -> None:
    assessment = _evaluate()
    assert assessment.authority_effect == "NONE"
    assert assessment.runtime_effect == "NONE"
    assert assessment.order_effect == "NONE"
    assert assessment.risk_effect == "NONE"


def test_with_computed_directional_assessment_digest_round_trip() -> None:
    assessment = _evaluate()
    bare = replace(assessment, semantic_digest="")
    bound = with_computed_directional_assessment_digest(bare)
    assert bound.semantic_digest == assessment.semantic_digest


def test_policy_threshold_order_invalid() -> None:
    blocks = validate_directional_assessment_policy(
        _policy(
            observe_signal_threshold=0.02,
            candidate_signal_threshold=0.01,
            confirmation_signal_threshold=0.005,
        ),
        policy_version=DIRECTIONAL_ASSESSMENT_POLICY_VERSION,
    )
    assert DirectionalAssessmentHardBlockReason.POLICY_THRESHOLD_ORDER_INVALID in blocks


def test_scope_event_ref_stale_epoch() -> None:
    assessment = _evaluate(
        trading_epoch=41,
        scope_event_ref=_scope_ref(trading_epoch=42),
    )
    assert assessment.status is DirectionalAssessmentStatus.BLOCKED
    assert (
        DirectionalAssessmentHardBlockReason.SCOPE_EVENT_REF_STALE.value
        in assessment.hard_block_reasons
    )


def test_synthetic_spot_instrument_rejected() -> None:
    assessment = _evaluate(instrument_id="inst-synthetic_spot-eth")
    assert (
        DirectionalAssessmentHardBlockReason.INSTRUMENT_KIND_FORBIDDEN.value
        in assessment.hard_block_reasons
    )


def test_mirror_price_for_short_used_in_path_mirror() -> None:
    anchor = 3500.0
    price = 3600.0
    mirrored = mirror_price_path_for_short((price,), anchor)[0]
    assert mirrored == pytest.approx(mirror_price_for_short(price, anchor))
