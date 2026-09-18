"""S05 C1/C3 vs Scope confirmation-clock separation conformance.

BOUNDED_WORKPACKAGE=
MASTER_V2_DOUBLE_PLAY_BOUNDED_BEHAVIORAL_CONFORMANCE_VECTOR_SET_FROM_PROVEN_CELLS_ONLY_V1
SLICE=S05_C1_C3_VS_SCOPE_CONFIRMATION_CLOCK
C1_OWNER=DistinctMarketObservationAcceptorV1
C2_OWNER=evaluate_confirmation_progress_v1
C3_OWNER=evaluate_directional_assessment_with_confirmation_progress_v1
SCOPE_CLOCK_OWNER=generate_deterministic_scope_event
REPLAY_CONSUMER=run_integrated_offline_trading_logic_replay_v1

Additive behavioral assertions only. No trading-semantics mutation.
"Confirmation clock" is TEST terminology only; not a production type.
C1 MarketObservationEpoch is not ScopeConfirmationState.trading_epoch.
C2/C3 ConfirmationProgressStateV1 is not ScopeConfirmationStateV1.
Composition last_evaluated_trading_epoch is out of this slice.
FILEGATE / execution / Live / S06 / S07 are out of this slice.

Epistemic:
- CANONICAL_AUTHORITY: C1 acceptor; C2 progress evaluator; C3 carrier/status map;
  Scope generator confirmation cursor
- FORENSIC_RAW_EVIDENCE: Replay binds Scope threshold to inp.confirmation_epochs
  and C2/C3 threshold to inp.policies.directional.confirmation_epochs
- ALREADY_ADJUDICATED: S04 C3 CONFIRMED is not Scope CONFIRMED
- Not claimed: clock unification; numeric identity of confirmation_epochs
  fixtures; selected_side; transition_state; compose_double_play_decision as owner

Path is tests/trading/ not tests/trading/master_v2/: the Economic Guard treats
tests/trading/master_v2/test_* as forbidden MASTER_V2 mutation surface.
Owner fixtures are reused via import of existing owner test helpers.
"""

from __future__ import annotations

import ast
from dataclasses import replace
from pathlib import Path

from trading.market_state.directional_confirmation_progress_v1 import (
    ConfirmationAssessmentSignalV1,
    ConfirmationAssessmentStateV1,
    ConfirmationProgressInputV1,
    ConfirmationProgressReasonCodeV1,
    ConfirmationSideV1,
    evaluate_confirmation_progress_v1,
    initial_confirmation_progress_state_v1,
)
from trading.market_state.distinct_market_observation_acceptor_v1 import (
    DistinctMarketObservationAcceptorV1,
    ObservationClassification,
)
from trading.market_state.observation_identity_v1 import MarketObservationEpoch
from trading.master_v2.deterministic_scope_event_generator_v1 import (
    CanonicalScopeEventType,
    ScopeCandidateKind,
    ScopeConfirmationStateV1,
)
from trading.master_v2.directional_assessment_confirmation_integration_v1 import (
    LEGACY_DIRECTIONAL_CONFIRMATION_STATE_AUTHORITY,
    LEGACY_TRADING_EPOCH_COUNTER_CONFIRMATION_AUTHORITY,
    assert_c3_confirmation_authority_exclusive_v1,
)
from trading.master_v2.directional_assessment_v1 import DirectionalAssessmentStatus
from trading.master_v2.integrated_offline_trading_logic_replay_v1 import (
    run_integrated_offline_trading_logic_replay_v1,
)

from tests.trading.market_state.test_distinct_market_observation_acceptor_v1 import (
    _candidate,
    _key,
)
from tests.trading.master_v2.test_deterministic_scope_event_generator_v1 import (
    _generate,
)
from tests.trading.master_v2.test_integrated_offline_trading_logic_replay_v1 import (
    _EPOCH,
    _INSTRUMENT,
    _default_policies,
    _replay_input,
)

_REPO_ROOT = Path(__file__).resolve().parents[2]
_REPLAY_SOURCE = _REPO_ROOT / "src/trading/master_v2/integrated_offline_trading_logic_replay_v1.py"
_C3_SOURCE = (
    _REPO_ROOT / "src/trading/master_v2/directional_assessment_confirmation_integration_v1.py"
)
_GENERATOR_SOURCE = _REPO_ROOT / "src/trading/master_v2/deterministic_scope_event_generator_v1.py"
_COMPOSE_ORACLE = "compose_double_play_decision"
_LEGACY_DA = "evaluate_directional_assessment_v1"
_SCOPE_CONFIRMED = frozenset(
    {
        CanonicalScopeEventType.UPSCOPE_CONFIRMED,
        CanonicalScopeEventType.DOWNSCOPE_CONFIRMED,
    }
)


def _imported_names(tree: ast.AST) -> list[str]:
    names: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            names.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            names.append(node.module)
            names.extend(f"{node.module}.{alias.name}" for alias in node.names)
    return names


def _call_name(node: ast.Call) -> str | None:
    func = node.func
    if isinstance(func, ast.Name):
        return func.id
    if isinstance(func, ast.Attribute):
        return func.attr
    return None


def _ordered_calls(tree: ast.AST) -> list[ast.Call]:
    calls = [node for node in ast.walk(tree) if isinstance(node, ast.Call)]
    return sorted(calls, key=lambda node: (node.lineno, node.col_offset))


def _attr_path(node: ast.AST) -> str:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        return f"{_attr_path(node.value)}.{node.attr}"
    if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "int":
        if node.args:
            return f"int({_attr_path(node.args[0])})"
    return ""


def _constructor_kw(tree: ast.AST, ctor: str, keyword: str) -> list[str]:
    values: list[str] = []
    for call in _ordered_calls(tree):
        if _call_name(call) != ctor:
            continue
        for kw in call.keywords:
            if kw.arg == keyword:
                values.append(_attr_path(kw.value))
    return values


def _c2_consume(acceptor, *, prior=None, instrument=None):
    key = instrument or _key()
    state = prior or initial_confirmation_progress_state_v1(
        session_id="sess-s05-clock",
        venue=key.venue,
        instrument=key,
        side=ConfirmationSideV1.LONG,
        initial_market_observation_epoch=MarketObservationEpoch(value=0),
    )
    return evaluate_confirmation_progress_v1(
        ConfirmationProgressInputV1(
            prior_state=state,
            observation_acceptance_result=acceptor,
            session_id=state.session_id,
            venue=state.venue,
            instrument=state.instrument,
            side=state.side,
            assessment_signal=ConfirmationAssessmentSignalV1.CANDIDATE,
            confirmation_threshold=2,
        )
    )


def _replay_c2_cursor(result) -> tuple[int, int, int, int]:
    carrier = result.intermediate.directional_confirmation_progress_after
    bull = carrier.bull_confirmation_state
    bear = carrier.bear_confirmation_state
    return (
        bull.latest_accepted_market_observation_epoch.value,
        bull.distinct_confirmation_observation_count,
        bear.latest_accepted_market_observation_epoch.value,
        bear.distinct_confirmation_observation_count,
    )


def _empty_scope_confirmation() -> ScopeConfirmationStateV1:
    return ScopeConfirmationStateV1(
        candidate_kind=None,
        candidate_count=0,
        last_evaluated_trading_epoch=_EPOCH - 1,
    )


def _replay_instrument_key():
    return _key(venue="offline_replay", canonical=_INSTRUMENT, venue_inst=_INSTRUMENT)


def _injected_c1(
    *, duplicate: bool = False, previous_mark: float | None = None, mark: float = 3500.0
):
    key = _replay_instrument_key()
    state = DistinctMarketObservationAcceptorV1.initial_state(bound_instrument_key=key)
    if previous_mark is None:
        candidate = _candidate(
            venue=key.venue,
            canonical=key.canonical_instrument_id,
            venue_inst=key.venue_instrument_id,
            mark=mark,
        )
        first = DistinctMarketObservationAcceptorV1.evaluate(state, candidate)
        if not duplicate:
            return first
        committed = DistinctMarketObservationAcceptorV1.commit(current_state=state, result=first)
        return DistinctMarketObservationAcceptorV1.evaluate(committed, candidate)
    first_candidate = _candidate(
        venue=key.venue,
        canonical=key.canonical_instrument_id,
        venue_inst=key.venue_instrument_id,
        mark=previous_mark,
        event_time=1_700_000_000.0,
    )
    first = DistinctMarketObservationAcceptorV1.evaluate(state, first_candidate)
    committed = DistinctMarketObservationAcceptorV1.commit(current_state=state, result=first)
    second_candidate = _candidate(
        venue=key.venue,
        canonical=key.canonical_instrument_id,
        venue_inst=key.venue_instrument_id,
        mark=mark,
        event_time=1_700_000_001.0,
    )
    return DistinctMarketObservationAcceptorV1.evaluate(committed, second_candidate)


def test_s05_t01_c1_distinct_may_advance_c2_c3_without_scope_candidate() -> None:
    """S05-T01: C1 DISTINCT may advance C2/C3; Scope count stays 0 without a candidate."""
    first = DistinctMarketObservationAcceptorV1.evaluate(
        DistinctMarketObservationAcceptorV1.initial_state(),
        _candidate(),
    )
    assert first.classification is ObservationClassification.DISTINCT
    progressed = _c2_consume(first)
    assert progressed.confirmation_advanced is True
    assert progressed.state_after.latest_accepted_market_observation_epoch.value == 1
    assert progressed.state_after.distinct_confirmation_observation_count == 1

    idle_scope = _generate(current_price=3500.0)
    assert idle_scope.event_type is CanonicalScopeEventType.NOOP
    assert idle_scope.next_confirmation_state.candidate_count == 0
    assert idle_scope.next_confirmation_state.candidate_kind is None

    injected = run_integrated_offline_trading_logic_replay_v1(
        _replay_input(
            observation_acceptance_result=_injected_c1(previous_mark=3400.0, mark=3500.0),
            scope_confirmation_state=_empty_scope_confirmation(),
        )
    )
    assert injected.intermediate is not None
    cursor = _replay_c2_cursor(injected)
    assert cursor[1] == 1 or cursor[3] == 1
    assert injected.intermediate.scope_event.next_confirmation_state.candidate_count == 0
    assert injected.intermediate.scope_event.event_type not in _SCOPE_CONFIRMED


def test_s05_t02_scope_confirmed_without_c2_count_advancement() -> None:
    """S05-T02: consecutive Scope candidates may CONFIRMED without C2 count advance."""
    first = _generate(current_price=3605.0)
    assert first.event_type is CanonicalScopeEventType.UPSCOPE_CANDIDATE
    second = _generate(
        trading_epoch=44,
        current_price=3610.0,
        confirmation_state=first.next_confirmation_state,
    )
    assert second.event_type is CanonicalScopeEventType.UPSCOPE_CONFIRMED
    idle_c2 = initial_confirmation_progress_state_v1(
        session_id="sess-s05-t02",
        venue="okx_eea",
        instrument=_key(),
        side=ConfirmationSideV1.LONG,
        initial_market_observation_epoch=MarketObservationEpoch(value=0),
    )
    assert idle_c2.distinct_confirmation_observation_count == 0

    result = run_integrated_offline_trading_logic_replay_v1(
        _replay_input(
            current_price=3710.0,
            price_path=(3500.0, 3500.0),
            scope_confirmation_state=ScopeConfirmationStateV1(
                candidate_kind=ScopeCandidateKind.UPSCOPE,
                candidate_count=1,
                last_evaluated_trading_epoch=_EPOCH - 1,
            ),
        )
    )
    assert result.intermediate is not None
    assert result.intermediate.scope_event.event_type is CanonicalScopeEventType.UPSCOPE_CONFIRMED
    assert _replay_c2_cursor(result) == (0, 0, 0, 0)


def test_s05_t03_replay_binds_distinct_confirmation_epoch_fields() -> None:
    """S05-T03: Scope threshold and C2/C3 threshold are distinct field bindings."""
    replay_tree = ast.parse(_REPLAY_SOURCE.read_text(encoding="utf-8"))
    c3_tree = ast.parse(_C3_SOURCE.read_text(encoding="utf-8"))
    scope_kw = _constructor_kw(replay_tree, "ScopeEventGeneratorInputV1", "confirmation_epochs")
    assert "int(inp.confirmation_epochs)" in scope_kw
    c3_threshold = _constructor_kw(c3_tree, "ConfirmationProgressInputV1", "confirmation_threshold")
    assert "int(policy.confirmation_epochs)" in c3_threshold
    c3_policy = _constructor_kw(
        replay_tree,
        "DirectionalAssessmentConfirmationIntegrationInputV1",
        "policy",
    )
    assert "inp.policies.directional" in c3_policy

    fixture = _replay_input()
    assert fixture.confirmation_epochs == fixture.policies.directional.confirmation_epochs
    # Equal numeric fixtures are coincidence, not a proven single threshold.
    assert fixture.confirmation_epochs == 2
    directional_once = replace(fixture.policies.directional, confirmation_epochs=1)
    split = run_integrated_offline_trading_logic_replay_v1(
        _replay_input(
            observation_acceptance_result=_injected_c1(previous_mark=3400.0, mark=3500.0),
            scope_confirmation_state=_empty_scope_confirmation(),
            confirmation_epochs=5,
            policies=replace(fixture.policies, directional=directional_once),
        )
    )
    assert split.intermediate is not None
    assert split.intermediate.bull_assessment.status is DirectionalAssessmentStatus.CONFIRMED
    assert split.intermediate.scope_event.event_type not in _SCOPE_CONFIRMED
    assert split.intermediate.scope_event.next_confirmation_state.candidate_count == 0


def test_s05_t04_c1_duplicate_does_not_compensate_on_scope_cursor() -> None:
    """S05-T04: C1 DUPLICATE → C2 NON_DISTINCT_NOOP; Scope count is not incremented."""
    state = DistinctMarketObservationAcceptorV1.initial_state()
    candidate = _candidate()
    first = DistinctMarketObservationAcceptorV1.evaluate(state, candidate)
    committed = DistinctMarketObservationAcceptorV1.commit(current_state=state, result=first)
    after_distinct = _c2_consume(first)
    duplicate = DistinctMarketObservationAcceptorV1.evaluate(committed, candidate)
    assert duplicate.classification is ObservationClassification.DUPLICATE
    after_duplicate = _c2_consume(duplicate, prior=after_distinct.state_after)
    assert after_duplicate.reason_code is ConfirmationProgressReasonCodeV1.NON_DISTINCT_NOOP
    assert after_duplicate.confirmation_advanced is False
    assert after_duplicate.state_after == after_distinct.state_after

    idle_scope = _generate(current_price=3500.0)
    assert idle_scope.candidate_count_after == 0
    assert idle_scope.candidate_count_after <= idle_scope.candidate_count_before

    result = run_integrated_offline_trading_logic_replay_v1(
        _replay_input(
            observation_acceptance_result=_injected_c1(duplicate=True),
            scope_confirmation_state=_empty_scope_confirmation(),
        )
    )
    assert result.intermediate is not None
    cursor = _replay_c2_cursor(result)
    assert cursor[1] == 0 and cursor[3] == 0
    assert result.intermediate.scope_event.next_confirmation_state.candidate_count == 0
    assert result.intermediate.scope_event.event_type not in _SCOPE_CONFIRMED


def test_s05_t05_duplicate_scope_trading_epoch_preserves_scope_state() -> None:
    """S05-T05: duplicate Scope trading_epoch freezes ScopeConfirmationState; not C3."""
    first = _generate(current_price=3605.0)
    assert first.event_type is CanonicalScopeEventType.UPSCOPE_CANDIDATE
    duplicate_epoch = _generate(
        trading_epoch=first.trading_epoch,
        current_price=3605.0,
        confirmation_state=first.next_confirmation_state,
    )
    assert duplicate_epoch.next_confirmation_state == first.next_confirmation_state
    assert (
        duplicate_epoch.next_confirmation_state.last_evaluated_trading_epoch == first.trading_epoch
    )

    frozen = ScopeConfirmationStateV1(
        candidate_kind=ScopeCandidateKind.UPSCOPE,
        candidate_count=1,
        last_evaluated_trading_epoch=_EPOCH,
    )
    result = run_integrated_offline_trading_logic_replay_v1(
        _replay_input(
            observation_acceptance_result=_injected_c1(previous_mark=3400.0, mark=3500.0),
            scope_confirmation_state=frozen,
        )
    )
    assert result.intermediate is not None
    assert result.intermediate.scope_event.next_confirmation_state == frozen
    cursor = _replay_c2_cursor(result)
    assert cursor[1] == 1 or cursor[3] == 1
    assert result.intermediate.bull_assessment.status is not None
    assert result.intermediate.scope_event.next_confirmation_state.candidate_count == 1


def test_s05_t06_legacy_da_is_not_productive_c1_c3_or_scope_clock() -> None:
    """S05-T06: legacy DA / DirectionalConfirmationStateV1 is not a productive clock."""
    assert LEGACY_DIRECTIONAL_CONFIRMATION_STATE_AUTHORITY is False
    assert LEGACY_TRADING_EPOCH_COUNTER_CONFIRMATION_AUTHORITY is False
    assert_c3_confirmation_authority_exclusive_v1()

    replay_src = _REPLAY_SOURCE.read_text(encoding="utf-8")
    replay_tree = ast.parse(replay_src)
    assert f"{_LEGACY_DA}(" not in replay_src
    assert all(_call_name(call) != _LEGACY_DA for call in _ordered_calls(replay_tree))
    assert "evaluate_directional_assessment_with_confirmation_progress_v1" in {
        _call_name(call) for call in _ordered_calls(replay_tree)
    }
    assert "LEGACY_NON_AUTHORITY" in replay_src
    assert "never consulted for status" in replay_src

    c3_tree = ast.parse(_C3_SOURCE.read_text(encoding="utf-8"))
    assert all(_call_name(call) != _LEGACY_DA for call in _ordered_calls(c3_tree))
    assert "evaluate_confirmation_progress_v1" in {
        _call_name(call) for call in _ordered_calls(c3_tree)
    }
    generator_tree = ast.parse(_GENERATOR_SOURCE.read_text(encoding="utf-8"))
    imported = _imported_names(generator_tree)
    assert all(
        "directional_assessment_confirmation_integration_v1" not in name for name in imported
    )
    assert all("DirectionalConfirmationStateV1" not in name for name in imported)
    assert all(_call_name(call) != _LEGACY_DA for call in _ordered_calls(generator_tree))


def test_s05_t07_c3_confirmed_alone_does_not_emit_scope_confirmed() -> None:
    """S05-T07: C3 CONFIRMED alone does not emit CanonicalScopeEventType.*_CONFIRMED."""
    policies = replace(
        _default_policies(),
        directional=replace(_default_policies().directional, confirmation_epochs=1),
    )
    result = run_integrated_offline_trading_logic_replay_v1(
        _replay_input(
            observation_acceptance_result=_injected_c1(previous_mark=3400.0, mark=3500.0),
            scope_confirmation_state=_empty_scope_confirmation(),
            policies=policies,
        )
    )
    assert result.intermediate is not None
    assert result.intermediate.bull_assessment.status is DirectionalAssessmentStatus.CONFIRMED
    assert result.intermediate.scope_event.event_type not in _SCOPE_CONFIRMED
    assert result.intermediate.scope_event.next_confirmation_state.candidate_count == 0

    c3_tree = ast.parse(_C3_SOURCE.read_text(encoding="utf-8"))
    assert all(
        _call_name(call) != "generate_deterministic_scope_event" for call in _ordered_calls(c3_tree)
    )
    this_tree = ast.parse(Path(__file__).read_text(encoding="utf-8"))
    assert all(_COMPOSE_ORACLE not in name for name in _imported_names(this_tree))
    assert all(_call_name(call) != "transition_state" for call in _ordered_calls(this_tree))
    assert all("src.execution" not in name for name in _imported_names(this_tree))
