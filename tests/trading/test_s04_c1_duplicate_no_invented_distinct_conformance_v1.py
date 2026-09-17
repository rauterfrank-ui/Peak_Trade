"""S04 C1 duplicate / no invented DISTINCT conformance.

BOUNDED_WORKPACKAGE=
MASTER_V2_DOUBLE_PLAY_BOUNDED_BEHAVIORAL_CONFORMANCE_VECTOR_SET_FROM_PROVEN_CELLS_ONLY_V1
SLICE=S04_C1_DUPLICATE_NO_INVENTED_DISTINCT
PRIMARY_OWNER=DistinctMarketObservationAcceptorV1
C2_CONSUMER=evaluate_confirmation_progress_v1
REPLAY_BIND=integrated_offline_trading_logic_replay_v1._resolve_c3_confirmation_binding_v1

Additive behavioral assertions only. No trading-semantics mutation.
C1 classification is not C2 progress. C2 progress is not C3 CONFIRMED.
C3 CONFIRMED is not Scope CONFIRMED. Replay is a C1 consumer, not owner.
FILEGATE / execution / Live / S05 / S06 / S07 are out of this slice.

Epistemic:
- CANONICAL_AUTHORITY: DistinctMarketObservationAcceptorV1; C2 non-DISTINCT gate
- FORENSIC_RAW_EVIDENCE: Replay None-bind to non_advancing DUPLICATE placeholder
- ALREADY_ADJUDICATED: V-C1-01 DISTINCT may advance C2; V-C1-02 duplicate no-op
- Not claimed: C3/Scope CONFIRMED clocks; selected_side; transition_state;
  Cap-6.3 distances; compose_double_play_decision as owner

Path is tests/trading/ not tests/trading/master_v2/: the Economic Guard treats
tests/trading/master_v2/test_* as forbidden MASTER_V2 mutation surface.
Owner fixtures are reused via import of existing owner test helpers.
"""

from __future__ import annotations

import ast
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
from trading.master_v2.integrated_offline_trading_logic_replay_v1 import (
    run_integrated_offline_trading_logic_replay_v1,
)

from tests.trading.market_state.test_distinct_market_observation_acceptor_v1 import (
    _candidate,
    _key,
)
from tests.trading.master_v2.test_integrated_offline_trading_logic_replay_v1 import (
    _INSTRUMENT,
    _replay_input,
)

_REPO_ROOT = Path(__file__).resolve().parents[2]
_REPLAY_SOURCE = _REPO_ROOT / "src/trading/master_v2/integrated_offline_trading_logic_replay_v1.py"
_COMPOSE_ORACLE = "compose_double_play_decision"
_NON_ADVANCING = "non_advancing_observation_acceptance_result_v1"
_EVALUATE_C1 = "evaluate_distinct_market_observation_v1"
_ACCEPTOR_CLASS = "DistinctMarketObservationAcceptorV1"


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


def _function_def(tree: ast.AST, name: str) -> ast.FunctionDef:
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name == name:
            return node
    raise AssertionError(f"missing function {name}")


def _defined_function_names(tree: ast.AST) -> set[str]:
    return {
        node.name
        for node in ast.walk(tree)
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
    }


def _defined_class_names(tree: ast.AST) -> set[str]:
    return {node.name for node in ast.walk(tree) if isinstance(node, ast.ClassDef)}


def _name_or_attr(node: ast.AST) -> str:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        return f"{_name_or_attr(node.value)}.{node.attr}"
    return ""


def _c2_consume(acceptor, *, prior=None, instrument=None):
    key = instrument or _key()
    state = prior or initial_confirmation_progress_state_v1(
        session_id="sess-s04-c1",
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


def test_s04_t01_v_c1_01_first_candidate_distinct_allows_c2_progress() -> None:
    """S04-T01 / V-C1-01: real C1 DISTINCT epoch 0→1 may advance C2; not CONFIRMED."""
    state = DistinctMarketObservationAcceptorV1.initial_state()
    assert state.market_observation_epoch.value == 0
    assert state.last_accepted_observation_identity is None

    first = DistinctMarketObservationAcceptorV1.evaluate(state, _candidate())
    assert first.classification is ObservationClassification.DISTINCT
    assert first.strategy_advance_allowed is True
    assert first.state_before.market_observation_epoch.value == 0
    assert first.state_after.market_observation_epoch.value == 1
    assert first.state_after.last_accepted_observation_identity is not None

    progressed = _c2_consume(first)
    assert progressed.reason_code is ConfirmationProgressReasonCodeV1.ACCEPTED_DISTINCT_PROGRESS
    assert progressed.confirmation_advanced is True
    assert progressed.state_after.latest_accepted_market_observation_epoch.value == 1
    assert progressed.state_after.distinct_confirmation_observation_count == 1
    assert progressed.state_after.assessment_state is not ConfirmationAssessmentStateV1.CONFIRMED


def test_s04_t02_v_c1_02_duplicate_leaves_c1_and_c2_unchanged() -> None:
    """S04-T02 / V-C1-02: identical candidate is DUPLICATE; C2 NON_DISTINCT_NOOP."""
    state = DistinctMarketObservationAcceptorV1.initial_state()
    candidate = _candidate()
    first = DistinctMarketObservationAcceptorV1.evaluate(state, candidate)
    committed = DistinctMarketObservationAcceptorV1.commit(current_state=state, result=first)
    after_distinct = _c2_consume(first)

    duplicate = DistinctMarketObservationAcceptorV1.evaluate(committed, candidate)
    assert duplicate.classification is ObservationClassification.DUPLICATE
    assert duplicate.strategy_advance_allowed is False
    assert duplicate.state_after == duplicate.state_before
    assert duplicate.state_after.market_observation_epoch.value == 1
    assert duplicate.state_after.market_observation_epoch == committed.market_observation_epoch

    after_duplicate = _c2_consume(duplicate, prior=after_distinct.state_after)
    assert after_duplicate.reason_code is ConfirmationProgressReasonCodeV1.NON_DISTINCT_NOOP
    assert after_duplicate.confirmation_advanced is False
    assert after_duplicate.state_after == after_distinct.state_after
    assert after_duplicate.state_changed is False


def test_s04_t03_replay_default_omitted_acceptor_does_not_advance() -> None:
    """S04-T03: omitted Replay acceptor stays non-advancing DUPLICATE; no C2 advance."""
    inp = _replay_input()
    assert inp.observation_acceptance_result is None
    result = run_integrated_offline_trading_logic_replay_v1(inp)
    assert result.intermediate is not None
    cursor = _replay_c2_cursor(result)
    assert cursor == (0, 0, 0, 0)
    carrier = result.intermediate.directional_confirmation_progress_after
    assert carrier is not None
    assert (
        carrier.bull_confirmation_state.assessment_state
        is not ConfirmationAssessmentStateV1.CONFIRMED
    )
    assert (
        carrier.bear_confirmation_state.assessment_state
        is not ConfirmationAssessmentStateV1.CONFIRMED
    )


def test_s04_t04_replay_consumer_injected_c1_distinct_advances_vs_t03() -> None:
    """S04-T04: injected real C1 DISTINCT advances Replay C2 cursor versus T03."""
    default = run_integrated_offline_trading_logic_replay_v1(_replay_input())
    default_cursor = _replay_c2_cursor(default)

    key = _key(venue="offline_replay", canonical=_INSTRUMENT, venue_inst=_INSTRUMENT)
    c1_state = DistinctMarketObservationAcceptorV1.initial_state(bound_instrument_key=key)
    distinct = DistinctMarketObservationAcceptorV1.evaluate(
        c1_state,
        _candidate(
            venue=key.venue,
            canonical=key.canonical_instrument_id,
            venue_inst=key.venue_instrument_id,
            mark=3500.0,
        ),
    )
    assert distinct.classification is ObservationClassification.DISTINCT
    assert distinct.strategy_advance_allowed is True
    assert distinct.state_after.market_observation_epoch.value == 1

    injected = run_integrated_offline_trading_logic_replay_v1(
        _replay_input(observation_acceptance_result=distinct)
    )
    assert injected.intermediate is not None
    injected_cursor = _replay_c2_cursor(injected)
    assert injected_cursor != default_cursor
    assert injected_cursor[0] == 1 or injected_cursor[2] == 1
    # C2 progress is not a C3/Scope CONFIRMED oracle; do not read selected_side.


def test_s04_t05_v_neg_replay_does_not_invent_distinct() -> None:
    """S04-T05 / V-NEG: Replay has no C1 acceptor; None-bind is non-advancing DUPLICATE."""
    replay_tree = ast.parse(_REPLAY_SOURCE.read_text(encoding="utf-8"))
    imported = _imported_names(replay_tree)
    assert all(not name.endswith(_ACCEPTOR_CLASS) for name in imported)
    assert all(_EVALUATE_C1 not in name for name in imported)
    assert _ACCEPTOR_CLASS not in _defined_class_names(replay_tree)
    assert _EVALUATE_C1 not in _defined_function_names(replay_tree)
    assert all(_call_name(call) != _EVALUATE_C1 for call in _ordered_calls(replay_tree))
    assert all(
        _ACCEPTOR_CLASS not in _name_or_attr(call.func) for call in _ordered_calls(replay_tree)
    )

    bind_fn = _function_def(replay_tree, "_resolve_c3_confirmation_binding_v1")
    none_bind_calls = [
        call for call in _ordered_calls(bind_fn) if _call_name(call) == _NON_ADVANCING
    ]
    assert none_bind_calls
    assert all(_call_name(call) != _EVALUATE_C1 for call in _ordered_calls(bind_fn))

    distinct_constructed = any(
        isinstance(node, ast.Attribute)
        and node.attr == "DISTINCT"
        and _name_or_attr(node.value).endswith("ObservationClassification")
        for node in ast.walk(replay_tree)
    )
    assert distinct_constructed is False

    assert all(_COMPOSE_ORACLE not in name for name in imported)
    assert all(_call_name(call) != _COMPOSE_ORACLE for call in _ordered_calls(replay_tree))
    assert all("src.execution" not in name for name in imported)
    assert all(not name.startswith("src.live") for name in imported)
    this_tree = ast.parse(Path(__file__).read_text(encoding="utf-8"))
    assert all(_COMPOSE_ORACLE not in name for name in _imported_names(this_tree))
    assert all(_call_name(call) != "transition_state" for call in _ordered_calls(this_tree))
    assert all("derive_scope_event_distances_v1" not in name for name in _imported_names(this_tree))
