"""S06 C4 selected_side ownership conformance.

BOUNDED_WORKPACKAGE=
MASTER_V2_DOUBLE_PLAY_BOUNDED_BEHAVIORAL_CONFORMANCE_VECTOR_SET_FROM_PROVEN_CELLS_ONLY_V1
SLICE=S06_C4_SELECTED_SIDE_OWNERSHIP
C4_BINDING_OWNER=post_confirmation_survival_suitability_composition_binding_v1
SURVIVAL_OWNER=evaluate_survival_assessment_v1
SUITABILITY_OWNER=evaluate_suitability_binding_v1
COMPOSITION_OWNER=evaluate_double_play_composition_matrix_v1
REPLAY_CONSUMER=run_integrated_offline_trading_logic_replay_v1

Additive behavioral assertions only. No trading-semantics mutation.
Composition selected_side is CompositionSelectedSide, not SideState.
C3 confirmation, Survival, Suitability, Composition selected_side, Scope CHOP,
and SideState remain distinct. S07 transition semantics are out of this slice.

Epistemic:
- CANONICAL_AUTHORITY: C4 binding constants; Composition matrix selected_side;
  Sole-Authority row "Composition selected_side"
- FORENSIC_RAW_EVIDENCE: Replay assigns composition_result from
  evaluate_double_play_composition_matrix_v1; transition_state side_state=
  inp.side_state
- ALREADY_ADJUDICATED: S05 C3 CONFIRMED is not Scope CONFIRMED
- Not claimed: SideState ownership; Scope-CHOP SSOT; Survival/Suitability
  semantics change; compose_double_play_decision as productive C4 owner;
  clock unification; call-order as new ownership

Path is tests/trading/ not tests/trading/master_v2/: the Economic Guard treats
tests/trading/master_v2/test_* as forbidden MASTER_V2 mutation surface.
Owner fixtures are reused via import of existing owner test helpers.
"""

from __future__ import annotations

import ast
from dataclasses import fields
from pathlib import Path

from trading.market_state.directional_confirmation_progress_v1 import ConfirmationSideV1
from trading.market_state.observation_identity_v1 import MarketObservationEpoch
from trading.master_v2.directional_assessment_confirmation_integration_v1 import (
    initial_directional_confirmation_side_state_carrier_v1,
    non_advancing_observation_acceptance_result_v1,
)
from trading.master_v2.directional_assessment_v1 import (
    DirectionalAssessmentSide,
    DirectionalAssessmentStatus,
)
from trading.master_v2.double_play_composition_matrix_v1 import (
    COMPOSITION_BOTH_SIDES_CONFIRMED_ROLE,
    COMPOSITION_CHOP_STATUS,
    CompositionChopGuardStatus,
    CompositionConflictStatus,
    CompositionSelectedSide,
    CompositionStatus,
)
from trading.master_v2.double_play_state import SideState
from trading.master_v2.post_confirmation_survival_suitability_composition_binding_v1 import (
    COMPOSITION_REMAINS_SOLE_CONFIRMED_ADMISSIBILITY_GATE,
    SURVIVAL_CONFIRMED_EARLY_GATE,
    SUITABILITY_CONFIRMED_EARLY_GATE,
    assert_post_c3_downstream_confirmation_non_authority_v1,
    assert_productive_c4_modules_confirmation_non_authority_v1,
    collect_forbidden_downstream_confirmation_calls_v1,
    collect_forbidden_scenario_legacy_imports_v1,
)
from trading.master_v2.suitability_binding_v1 import (
    SuitabilityBindingStatus,
    SuitabilityResultV1,
)
from trading.master_v2.survival_assessment_v1 import (
    SurvivalAssessmentStatus,
    SurvivalResultV1,
)

from tests.trading.master_v2.test_double_play_composition_matrix_v1 import (
    _evaluate,
    _side_bundle,
)
from tests.trading.master_v2.test_integrated_offline_trading_logic_replay_v1 import _run
from tests.trading.master_v2.test_post_confirmation_survival_suitability_composition_binding_v1 import (
    _carrier_from_sides,
    _confirmed_side_state,
    _distinct_acceptor,
    _key,
    _policies_confirm_once,
    _session,
)

_REPO_ROOT = Path(__file__).resolve().parents[2]
_REPLAY_SOURCE = _REPO_ROOT / "src/trading/master_v2/integrated_offline_trading_logic_replay_v1.py"
_C4_SOURCE = (
    _REPO_ROOT
    / "src/trading/master_v2/post_confirmation_survival_suitability_composition_binding_v1.py"
)
_SURVIVAL_SOURCE = _REPO_ROOT / "src/trading/master_v2/survival_assessment_v1.py"
_SUITABILITY_SOURCE = _REPO_ROOT / "src/trading/master_v2/suitability_binding_v1.py"
_COMPOSITION_SOURCE = _REPO_ROOT / "src/trading/master_v2/double_play_composition_matrix_v1.py"
_PRODUCTIVE_C4_MODULES = (
    _REPLAY_SOURCE,
    _SURVIVAL_SOURCE,
    _SUITABILITY_SOURCE,
    _COMPOSITION_SOURCE,
    _REPO_ROOT / "src/backtest/mv2_research_wiring_v1.py",
)
_COMPOSE_ORACLE = "compose_double_play_decision"
_COMPOSITION_OWNER = "evaluate_double_play_composition_matrix_v1"
_FORBIDDEN_SCENARIO_TAILS = frozenset(
    {
        "double_play_survival",
        "double_play_suitability",
        "double_play_composition",
        "survival_suitability_scenario_binding_adapter_v0",
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
    return ""


def _assign_target_names(node: ast.AST) -> list[str]:
    names: list[str] = []
    if isinstance(node, ast.Name):
        names.append(node.id)
    elif isinstance(node, ast.Tuple | ast.List):
        for elt in node.elts:
            names.extend(_assign_target_names(elt))
    return names


def _composition_result_assign_calls(tree: ast.AST) -> list[ast.Call]:
    calls: list[ast.Call] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Assign):
            continue
        if "composition_result" not in {
            name for target in node.targets for name in _assign_target_names(target)
        }:
            continue
        if isinstance(node.value, ast.Call):
            calls.append(node.value)
    return calls


def _kw_path(call: ast.Call, keyword: str) -> str | None:
    for kw in call.keywords:
        if kw.arg == keyword:
            return _attr_path(kw.value)
    return None


def _assigned_frozenset_strings(tree: ast.AST, name: str) -> frozenset[str]:
    values: set[str] = set()
    for node in ast.walk(tree):
        call: ast.AST | None = None
        if isinstance(node, ast.Assign):
            if any(isinstance(target, ast.Name) and target.id == name for target in node.targets):
                call = node.value
        elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
            if node.target.id == name:
                call = node.value
        if not isinstance(call, ast.Call) or _call_name(call) != "frozenset":
            continue
        if not call.args:
            continue
        arg = call.args[0]
        if isinstance(arg, ast.Set | ast.List | ast.Tuple):
            for elt in arg.elts:
                if isinstance(elt, ast.Constant) and isinstance(elt.value, str):
                    values.add(elt.value)
    return frozenset(values)


def test_s06_t01_c4_survival_suitability_are_not_confirmation_authority() -> None:
    """S06-T01: Survival/Suitability add no C1/C2/C3 confirmation authority."""
    assert COMPOSITION_REMAINS_SOLE_CONFIRMED_ADMISSIBILITY_GATE is True
    assert SURVIVAL_CONFIRMED_EARLY_GATE is False
    assert SUITABILITY_CONFIRMED_EARLY_GATE is False
    assert_post_c3_downstream_confirmation_non_authority_v1()
    assert_productive_c4_modules_confirmation_non_authority_v1(repo_root=_REPO_ROOT)

    for path in (_SURVIVAL_SOURCE, _SUITABILITY_SOURCE, _COMPOSITION_SOURCE):
        source = path.read_text(encoding="utf-8")
        assert not collect_forbidden_downstream_confirmation_calls_v1(source), path.name
        assert not collect_forbidden_scenario_legacy_imports_v1(source), path.name

    survival_fields = {f.name for f in fields(SurvivalResultV1)}
    suitability_fields = {f.name for f in fields(SuitabilityResultV1)}
    assert "selected_side" not in survival_fields
    assert "selected_side" not in suitability_fields
    assert "selected_strategy_id" in suitability_fields
    assert "selected_strategy_id" != "selected_side"


def test_s06_t02_one_sided_confirmed_pass_yields_side_only_from_composition() -> None:
    """S06-T02: one-sided C3 CONFIRMED + Survival/Suitability PASS → LONG|SHORT via matrix."""
    bull, bull_s, bull_u = _side_bundle(DirectionalAssessmentSide.LONG)
    bear, bear_s, bear_u = _side_bundle(
        DirectionalAssessmentSide.SHORT,
        assessment_status=DirectionalAssessmentStatus.OBSERVE,
        suitability_status=SuitabilityBindingStatus.BLOCKED,
    )
    assert bull.status is DirectionalAssessmentStatus.CONFIRMED
    assert bull_s.status is SurvivalAssessmentStatus.PASS
    assert bull_u.status is SuitabilityBindingStatus.PASS
    long_result = _evaluate(
        bull_directional_assessment=bull,
        bear_directional_assessment=bear,
        bull_survival_result=bull_s,
        bear_survival_result=bear_s,
        bull_suitability_result=bull_u,
        bear_suitability_result=bear_u,
    )
    assert long_result.selected_side is CompositionSelectedSide.LONG
    assert long_result.composition_status is CompositionStatus.LONG_SELECTED

    bear_ok, bear_s_ok, bear_u_ok = _side_bundle(DirectionalAssessmentSide.SHORT)
    bull_idle, bull_s_idle, bull_u_idle = _side_bundle(
        DirectionalAssessmentSide.LONG,
        assessment_status=DirectionalAssessmentStatus.OBSERVE,
        suitability_status=SuitabilityBindingStatus.BLOCKED,
    )
    short_result = _evaluate(
        bull_directional_assessment=bull_idle,
        bear_directional_assessment=bear_ok,
        bull_survival_result=bull_s_idle,
        bear_survival_result=bear_s_ok,
        bull_suitability_result=bull_u_idle,
        bear_suitability_result=bear_u_ok,
    )
    assert bear_ok.status is DirectionalAssessmentStatus.CONFIRMED
    assert bear_s_ok.status is SurvivalAssessmentStatus.PASS
    assert bear_u_ok.status is SuitabilityBindingStatus.PASS
    assert short_result.selected_side is CompositionSelectedSide.SHORT
    assert short_result.composition_status is CompositionStatus.SHORT_SELECTED

    composition_tree = ast.parse(_COMPOSITION_SOURCE.read_text(encoding="utf-8"))
    owner_calls = {
        _call_name(call)
        for call in _ordered_calls(composition_tree)
        if _call_name(call) == _COMPOSITION_OWNER
    }
    assert _COMPOSITION_OWNER in {
        node.name for node in ast.walk(composition_tree) if isinstance(node, ast.FunctionDef)
    }
    assert not owner_calls  # definition is FunctionDef, not a nested owner call
    survival_tree = ast.parse(_SURVIVAL_SOURCE.read_text(encoding="utf-8"))
    suitability_tree = ast.parse(_SUITABILITY_SOURCE.read_text(encoding="utf-8"))
    assert all(_call_name(call) != _COMPOSITION_OWNER for call in _ordered_calls(survival_tree))
    assert all(_call_name(call) != _COMPOSITION_OWNER for call in _ordered_calls(suitability_tree))

    replay = _run(
        policies=_policies_confirm_once(),
        price_path=(3500.0, 3570.0),
        directional_confirmation_progress=initial_directional_confirmation_side_state_carrier_v1(
            session_id=_session(),
            venue="okx_eea",
            instrument=_key(),
        ),
        observation_acceptance_result=_distinct_acceptor()[0],
        confirmation_progress_session_id=_session(),
        confirmation_progress_venue="okx_eea",
        confirmation_progress_instrument=_key(),
    )
    assert replay.intermediate is not None
    assert replay.intermediate.bull_assessment.status is DirectionalAssessmentStatus.CONFIRMED
    assert replay.intermediate.bull_survival.status is SurvivalAssessmentStatus.PASS
    assert replay.intermediate.bull_suitability.status is SuitabilityBindingStatus.PASS
    assert replay.intermediate.composition_result.selected_side is CompositionSelectedSide.LONG
    assert isinstance(replay.intermediate.composition_result.selected_side, CompositionSelectedSide)


def test_s06_t03_replay_obtains_composition_result_from_matrix_owner() -> None:
    """S06-T03: productive replay composition_result comes from the matrix owner."""
    replay_src = _REPLAY_SOURCE.read_text(encoding="utf-8")
    replay_tree = ast.parse(replay_src)
    composition_assigns = _composition_result_assign_calls(replay_tree)
    assert composition_assigns
    assert all(_call_name(call) == _COMPOSITION_OWNER for call in composition_assigns)
    assert all(_call_name(call) != _COMPOSE_ORACLE for call in _ordered_calls(replay_tree))
    assert f"{_COMPOSE_ORACLE}(" not in replay_src
    assert not collect_forbidden_scenario_legacy_imports_v1(replay_src)
    imported = _imported_names(replay_tree)
    assert any(name.endswith(_COMPOSITION_OWNER) for name in imported)
    assert _COMPOSITION_OWNER in {_call_name(call) for call in _ordered_calls(replay_tree)}

    result = _run()
    assert result.intermediate is not None
    assert result.intermediate.composition_result.selected_side is CompositionSelectedSide.NONE


def test_s06_t04_survival_pass_on_non_confirmed_does_not_select_side() -> None:
    """S06-T04: Survival PASS on CANDIDATE/OBSERVE does not independently select LONG/SHORT."""
    for status in (
        DirectionalAssessmentStatus.CANDIDATE,
        DirectionalAssessmentStatus.OBSERVE,
    ):
        bull, bull_s, bull_u = _side_bundle(
            DirectionalAssessmentSide.LONG,
            assessment_status=status,
        )
        bear, bear_s, bear_u = _side_bundle(
            DirectionalAssessmentSide.SHORT,
            assessment_status=DirectionalAssessmentStatus.INVALID,
        )
        assert bull.status is status
        assert bull_s.status is SurvivalAssessmentStatus.PASS
        assert bull_u.status is SuitabilityBindingStatus.PASS
        result = _evaluate(
            bull_directional_assessment=bull,
            bear_directional_assessment=bear,
            bull_survival_result=bull_s,
            bear_survival_result=bear_s,
            bull_suitability_result=bull_u,
            bear_suitability_result=bear_u,
        )
        assert result.selected_side is CompositionSelectedSide.NONE
        assert result.selected_side is not CompositionSelectedSide.LONG
        assert result.selected_side is not CompositionSelectedSide.SHORT

    replay = _run(
        price_path=(3500.0, 3570.0),
        directional_confirmation_progress=initial_directional_confirmation_side_state_carrier_v1(
            session_id=_session(),
            venue="okx_eea",
            instrument=_key(),
        ),
        observation_acceptance_result=_distinct_acceptor()[0],
        confirmation_progress_session_id=_session(),
        confirmation_progress_venue="okx_eea",
        confirmation_progress_instrument=_key(),
    )
    assert replay.intermediate is not None
    assert replay.intermediate.bull_assessment.status is DirectionalAssessmentStatus.CANDIDATE
    assert replay.intermediate.composition_result.selected_side is CompositionSelectedSide.NONE
    assert "selected_side" not in {f.name for f in fields(SurvivalResultV1)}


def test_s06_t05_both_sides_confirmed_yields_none_not_scope_chop() -> None:
    """S06-T05: BOTH_SIDES_CONFIRMED → selected_side NONE; not Scope-CHOP SSOT."""
    bull, bull_s, bull_u = _side_bundle(DirectionalAssessmentSide.LONG)
    bear, bear_s, bear_u = _side_bundle(DirectionalAssessmentSide.SHORT)
    result = _evaluate(
        bull_directional_assessment=bull,
        bear_directional_assessment=bear,
        bull_survival_result=bull_s,
        bear_survival_result=bear_s,
        bull_suitability_result=bull_u,
        bear_suitability_result=bear_u,
    )
    assert bull.status is DirectionalAssessmentStatus.CONFIRMED
    assert bear.status is DirectionalAssessmentStatus.CONFIRMED
    assert result.selected_side is CompositionSelectedSide.NONE
    assert result.conflict_status is CompositionConflictStatus.BOTH_SIDES_CONFIRMED
    assert COMPOSITION_BOTH_SIDES_CONFIRMED_ROLE == "COMPOSITION_CONFLICT_NOT_SCOPE_CHOP_SSOT"
    assert COMPOSITION_CHOP_STATUS == "CONSUMER_PROJECTION_ONLY"
    assert "composition_conflict_not_scope_chop" in result.reason_codes
    assert result.chop_guard_status is CompositionChopGuardStatus.NONE
    # Historical CompositionStatus.CHOP_GUARD_BLOCK is an entry-gate label, not Scope-CHOP SSOT.
    assert result.composition_status is CompositionStatus.CHOP_GUARD_BLOCK

    replay = _run(
        price_path=(3500.0, 3500.0),
        directional_confirmation_progress=_carrier_from_sides(
            bull=_confirmed_side_state(side=ConfirmationSideV1.LONG),
            bear=_confirmed_side_state(side=ConfirmationSideV1.SHORT),
        ),
        observation_acceptance_result=non_advancing_observation_acceptance_result_v1(
            bound_instrument_key=_key(),
            market_observation_epoch=MarketObservationEpoch(value=1),
        ),
        confirmation_progress_session_id=_session(),
        confirmation_progress_venue="okx_eea",
        confirmation_progress_instrument=_key(),
    )
    assert replay.intermediate is not None
    assert replay.intermediate.bull_assessment.status is DirectionalAssessmentStatus.CONFIRMED
    assert replay.intermediate.bear_assessment.status is DirectionalAssessmentStatus.CONFIRMED
    assert replay.intermediate.composition_result.selected_side is CompositionSelectedSide.NONE
    assert (
        replay.intermediate.composition_result.conflict_status
        is CompositionConflictStatus.BOTH_SIDES_CONFIRMED
    )


def test_s06_t06_selected_side_is_not_sidestate_and_not_transition_arg() -> None:
    """S06-T06: CompositionSelectedSide is not SideState; not passed as side_state=."""
    assert CompositionSelectedSide is not SideState
    assert {member.name for member in CompositionSelectedSide} != {
        member.name for member in SideState
    }
    assert CompositionSelectedSide.LONG not in SideState
    assert CompositionSelectedSide.SHORT not in SideState
    assert CompositionSelectedSide.NONE not in SideState

    replay_tree = ast.parse(_REPLAY_SOURCE.read_text(encoding="utf-8"))
    transition_calls = [
        call for call in _ordered_calls(replay_tree) if _call_name(call) == "transition_state"
    ]
    assert transition_calls
    side_state_args = [_kw_path(call, "side_state") for call in transition_calls]
    assert all(arg == "inp.side_state" for arg in side_state_args)
    assert all(arg is not None and "selected_side" not in arg for arg in side_state_args)
    assert all(
        _kw_path(call, "side_state") != "composition_result.selected_side"
        for call in transition_calls
    )

    this_tree = ast.parse(Path(__file__).read_text(encoding="utf-8"))
    assert all(_call_name(call) != "transition_state" for call in _ordered_calls(this_tree))
    assert not (
        _REPO_ROOT / "tests/trading/test_s07_sidestate_transition_boundary_conformance_v1.py"
    ).exists()


def test_s06_t07_legacy_compose_and_scenario_composition_not_c4_owner() -> None:
    """S06-T07: quarantined compose/scenario composition is not productive C4 selected_side owner."""
    c4_src = _C4_SOURCE.read_text(encoding="utf-8")
    assert "double_play_composition" in c4_src
    assert "_FORBIDDEN_SCENARIO_LEGACY_IMPORT_MODULES" in c4_src
    for path in _PRODUCTIVE_C4_MODULES:
        source = path.read_text(encoding="utf-8")
        legacy = collect_forbidden_scenario_legacy_imports_v1(source)
        assert not legacy, path.name
        tree = ast.parse(source)
        assert all(_call_name(call) != _COMPOSE_ORACLE for call in _ordered_calls(tree))
        assert f"{_COMPOSE_ORACLE}(" not in source

    replay_src = _REPLAY_SOURCE.read_text(encoding="utf-8")
    assert _COMPOSITION_OWNER in replay_src
    assert f"{_COMPOSE_ORACLE}(" not in replay_src

    this_tree = ast.parse(Path(__file__).read_text(encoding="utf-8"))
    assert all(_COMPOSE_ORACLE not in name for name in _imported_names(this_tree))
    assert all("src.execution" not in name for name in _imported_names(this_tree))
    c4_tree = ast.parse(c4_src)
    forbidden_tails = _assigned_frozenset_strings(
        c4_tree, "_FORBIDDEN_SCENARIO_LEGACY_IMPORT_MODULES"
    )
    assert "double_play_composition" in forbidden_tails
    assert forbidden_tails == _FORBIDDEN_SCENARIO_TAILS
