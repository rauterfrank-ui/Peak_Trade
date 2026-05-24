# tests/trading/master_v2/test_offline_governance_tick_harness_v0.py
"""
Offline Governance-Tick Harness v0 — tests-first, I/O-free, non-authorizing.

Fixture-driven single-tick evaluation using pure ``transition_state`` semantics from
``double_play_state`` only. Does not implement protected runtime, production harness,
scheduler, broker, exchange, or readiness promotion.
"""

from __future__ import annotations

import ast
from dataclasses import dataclass
from pathlib import Path
from typing import FrozenSet, Tuple

from trading.master_v2.double_play_state import (
    DynamicScopeRules,
    RuntimeEnvelope,
    RuntimeScopeState,
    ScopeEvent,
    SideState,
    StaticHardLimits,
    transition_state,
)

HARNESS_LAYER_VERSION = "v0"
CONFIRMED_SCOPE_EVENTS: FrozenSet[ScopeEvent] = frozenset(
    {
        ScopeEvent.DOWNSCOPE_CONFIRMED,
        ScopeEvent.UPSCOPE_CONFIRMED,
        ScopeEvent.KILL_ALL_REQUIRED,
        ScopeEvent.CHOP_DETECTED,
        ScopeEvent.SCOPE_UNKNOWN,
        ScopeEvent.NOOP,
    }
)
CANDIDATE_SCOPE_EVENTS: FrozenSet[ScopeEvent] = frozenset(
    {
        ScopeEvent.DOWNSCOPE_CANDIDATE,
        ScopeEvent.UPSCOPE_CANDIDATE,
    }
)

_GOOD_LIMITS = StaticHardLimits(
    max_notional=1.0,
    max_leverage=1.0,
    max_switches_per_window=100,
    min_band_width=1.0,
    max_band_width=100.0,
)
_GOOD_ENVELOPE = RuntimeEnvelope(static=_GOOD_LIMITS, live_authorization=False)
_GOOD_RULES = DynamicScopeRules(
    min_band_width=1.0,
    max_band_width=50.0,
    min_switch_cooldown_ticks=0,
    max_switches_per_window=1_000_000,
    volatility_estimate=0.1,
)
_EMPTY_SCOPE_STATE = RuntimeScopeState()


@dataclass(frozen=True)
class OfflineGovernanceTickInputV0:
    side_state: SideState
    scope_event: ScopeEvent | None
    scope_state: RuntimeScopeState = _EMPTY_SCOPE_STATE
    now_tick: int = 0
    kill_switch_veto: bool = False
    execution_gate_open: bool = False
    evidence_authorizes_runtime: bool = False
    ai_authorizes_execution: bool = False
    dashboard_authorizes_trades: bool = False
    paper_authorized: bool = False
    shadow_authorized: bool = False
    testnet_authorized: bool = False
    live_authorized_label: bool = False
    universe_selector_consulted: bool = False
    strategy_suitability_consulted: bool = False


@dataclass(frozen=True)
class OfflineGovernanceTickResultV0:
    layer_version: str
    tick_ok: bool
    blocked_reason: str | None
    side_state_before: SideState
    side_state_after: SideState
    transition_allowed: bool
    transition_reason_code: str | None
    compliance_labels: Tuple[str, ...]
    recommended_side: str
    live_authorization: bool
    order_authorization: bool
    broker_exchange_authority: bool
    runtime_start_authorized: bool
    scheduler_start_authorized: bool
    stage_active: str
    protected_runtime_implemented: bool
    production_harness_implemented: bool


def evaluate_offline_governance_tick_v0(
    tick_input: OfflineGovernanceTickInputV0,
) -> OfflineGovernanceTickResultV0:
    """Single offline governance tick — compliance labels only; never authorizes runtime."""
    if tick_input.kill_switch_veto:
        return OfflineGovernanceTickResultV0(
            layer_version=HARNESS_LAYER_VERSION,
            tick_ok=False,
            blocked_reason="KILL_SWITCH_VETO",
            side_state_before=tick_input.side_state,
            side_state_after=SideState.KILL_ALL,
            transition_allowed=False,
            transition_reason_code="KILL_SWITCH_VETO",
            compliance_labels=("kill_switch_superior", "fail_closed"),
            recommended_side="neutral",
            live_authorization=False,
            order_authorization=False,
            broker_exchange_authority=False,
            runtime_start_authorized=False,
            scheduler_start_authorized=False,
            stage_active="STAGE_0_STOP",
            protected_runtime_implemented=False,
            production_harness_implemented=False,
        )

    if tick_input.scope_event is None:
        return _blocked_result(
            tick_input,
            blocked_reason="MISSING_SCOPE_EVENT",
            labels=("fail_closed", "missing_confirmed_scope_event"),
        )

    if tick_input.scope_event in CANDIDATE_SCOPE_EVENTS:
        return _blocked_result(
            tick_input,
            blocked_reason="CANDIDATE_SCOPE_EVENT_NOT_AUTHORIZED",
            labels=("fail_closed", "candidate_not_confirmed"),
        )

    if tick_input.scope_event not in CONFIRMED_SCOPE_EVENTS:
        return _blocked_result(
            tick_input,
            blocked_reason="UNCONFIRMED_SCOPE_EVENT",
            labels=("fail_closed", "unconfirmed_scope_event"),
        )

    side_after, _, decision = transition_state(
        side_state=tick_input.side_state,
        event=tick_input.scope_event,
        scope_state=tick_input.scope_state,
        rules=_GOOD_RULES,
        envelope=_GOOD_ENVELOPE,
        now_tick=tick_input.now_tick,
    )

    labels: list[str] = ["pure_transition_evaluated"]
    if decision.allowed:
        labels.append("transition_compliance_visible")
    else:
        labels.append("transition_blocked_visible")

    if tick_input.execution_gate_open:
        labels.append("execution_gate_open_label_only")
    else:
        labels.append("execution_gate_closed")

    labels.extend(
        [
            "evidence_informational_only",
            "ai_informational_only",
            "dashboard_informational_only",
            "paper_blocked",
            "shadow_blocked",
            "testnet_blocked",
            "live_blocked",
        ]
    )

    return OfflineGovernanceTickResultV0(
        layer_version=HARNESS_LAYER_VERSION,
        tick_ok=decision.allowed,
        blocked_reason=None if decision.allowed else decision.reason_code,
        side_state_before=tick_input.side_state,
        side_state_after=side_after,
        transition_allowed=decision.allowed,
        transition_reason_code=decision.reason_code,
        compliance_labels=tuple(labels),
        recommended_side=_recommended_side_label(side_after),
        live_authorization=False,
        order_authorization=False,
        broker_exchange_authority=False,
        runtime_start_authorized=False,
        scheduler_start_authorized=False,
        stage_active="STAGE_0_STOP",
        protected_runtime_implemented=False,
        production_harness_implemented=False,
    )


def _blocked_result(
    tick_input: OfflineGovernanceTickInputV0,
    *,
    blocked_reason: str,
    labels: Tuple[str, ...],
) -> OfflineGovernanceTickResultV0:
    return OfflineGovernanceTickResultV0(
        layer_version=HARNESS_LAYER_VERSION,
        tick_ok=False,
        blocked_reason=blocked_reason,
        side_state_before=tick_input.side_state,
        side_state_after=tick_input.side_state,
        transition_allowed=False,
        transition_reason_code=blocked_reason,
        compliance_labels=labels,
        recommended_side=_recommended_side_label(tick_input.side_state),
        live_authorization=False,
        order_authorization=False,
        broker_exchange_authority=False,
        runtime_start_authorized=False,
        scheduler_start_authorized=False,
        stage_active="STAGE_0_STOP",
        protected_runtime_implemented=False,
        production_harness_implemented=False,
    )


def _recommended_side_label(side: SideState) -> str:
    if side in (SideState.LONG_ACTIVE, SideState.LONG_ARMED, SideState.LONG_BLOCKED):
        return "long"
    if side in (SideState.SHORT_ACTIVE, SideState.SHORT_ARMED, SideState.SHORT_BLOCKED):
        return "short"
    if side == SideState.KILL_ALL:
        return "kill_all"
    return "neutral"


def _assert_non_authorizing(result: OfflineGovernanceTickResultV0) -> None:
    assert result.live_authorization is False
    assert result.order_authorization is False
    assert result.broker_exchange_authority is False
    assert result.runtime_start_authorized is False
    assert result.scheduler_start_authorized is False
    assert result.stage_active == "STAGE_0_STOP"
    assert result.protected_runtime_implemented is False
    assert result.production_harness_implemented is False


def test_long_side_confirmed_event_yields_compliance_label_only_no_order() -> None:
    result = evaluate_offline_governance_tick_v0(
        OfflineGovernanceTickInputV0(
            side_state=SideState.NEUTRAL_OBSERVE,
            scope_event=ScopeEvent.UPSCOPE_CONFIRMED,
        )
    )
    _assert_non_authorizing(result)
    assert result.tick_ok is True
    assert result.side_state_after == SideState.LONG_ARMED
    assert result.recommended_side == "long"
    assert "transition_compliance_visible" in result.compliance_labels


def test_short_side_confirmed_event_yields_compliance_label_only_no_order() -> None:
    result = evaluate_offline_governance_tick_v0(
        OfflineGovernanceTickInputV0(
            side_state=SideState.NEUTRAL_OBSERVE,
            scope_event=ScopeEvent.DOWNSCOPE_CONFIRMED,
        )
    )
    _assert_non_authorizing(result)
    assert result.tick_ok is True
    assert result.side_state_after == SideState.SHORT_ARMED
    assert result.recommended_side == "short"


def test_kill_switch_veto_blocks_everything() -> None:
    result = evaluate_offline_governance_tick_v0(
        OfflineGovernanceTickInputV0(
            side_state=SideState.LONG_ACTIVE,
            scope_event=ScopeEvent.UPSCOPE_CONFIRMED,
            kill_switch_veto=True,
        )
    )
    _assert_non_authorizing(result)
    assert result.tick_ok is False
    assert result.blocked_reason == "KILL_SWITCH_VETO"
    assert result.side_state_after == SideState.KILL_ALL
    assert "kill_switch_superior" in result.compliance_labels


def test_missing_scope_event_fails_closed() -> None:
    result = evaluate_offline_governance_tick_v0(
        OfflineGovernanceTickInputV0(
            side_state=SideState.LONG_ACTIVE,
            scope_event=None,
        )
    )
    _assert_non_authorizing(result)
    assert result.tick_ok is False
    assert result.blocked_reason == "MISSING_SCOPE_EVENT"


def test_candidate_scope_event_fails_closed() -> None:
    result = evaluate_offline_governance_tick_v0(
        OfflineGovernanceTickInputV0(
            side_state=SideState.LONG_ACTIVE,
            scope_event=ScopeEvent.DOWNSCOPE_CANDIDATE,
        )
    )
    _assert_non_authorizing(result)
    assert result.tick_ok is False
    assert result.blocked_reason == "CANDIDATE_SCOPE_EVENT_NOT_AUTHORIZED"
    assert result.side_state_after == SideState.LONG_ACTIVE


def test_execution_gate_closed_keeps_live_authorization_false() -> None:
    result = evaluate_offline_governance_tick_v0(
        OfflineGovernanceTickInputV0(
            side_state=SideState.NEUTRAL_OBSERVE,
            scope_event=ScopeEvent.UPSCOPE_CONFIRMED,
            execution_gate_open=False,
        )
    )
    _assert_non_authorizing(result)
    assert "execution_gate_closed" in result.compliance_labels


def test_execution_gate_open_label_does_not_grant_live_authorization() -> None:
    result = evaluate_offline_governance_tick_v0(
        OfflineGovernanceTickInputV0(
            side_state=SideState.NEUTRAL_OBSERVE,
            scope_event=ScopeEvent.UPSCOPE_CONFIRMED,
            execution_gate_open=True,
        )
    )
    _assert_non_authorizing(result)
    assert "execution_gate_open_label_only" in result.compliance_labels


def test_broker_exchange_authority_always_false() -> None:
    result = evaluate_offline_governance_tick_v0(
        OfflineGovernanceTickInputV0(
            side_state=SideState.NEUTRAL_OBSERVE,
            scope_event=ScopeEvent.DOWNSCOPE_CONFIRMED,
        )
    )
    _assert_non_authorizing(result)
    assert result.broker_exchange_authority is False


def test_evidence_ai_dashboard_informational_only() -> None:
    result = evaluate_offline_governance_tick_v0(
        OfflineGovernanceTickInputV0(
            side_state=SideState.NEUTRAL_OBSERVE,
            scope_event=ScopeEvent.UPSCOPE_CONFIRMED,
            evidence_authorizes_runtime=True,
            ai_authorizes_execution=True,
            dashboard_authorizes_trades=True,
        )
    )
    _assert_non_authorizing(result)
    assert "evidence_informational_only" in result.compliance_labels
    assert "ai_informational_only" in result.compliance_labels
    assert "dashboard_informational_only" in result.compliance_labels


def test_paper_shadow_testnet_live_remain_blocked() -> None:
    result = evaluate_offline_governance_tick_v0(
        OfflineGovernanceTickInputV0(
            side_state=SideState.NEUTRAL_OBSERVE,
            scope_event=ScopeEvent.UPSCOPE_CONFIRMED,
            paper_authorized=True,
            shadow_authorized=True,
            testnet_authorized=True,
            live_authorized_label=True,
        )
    )
    _assert_non_authorizing(result)
    for label in ("paper_blocked", "shadow_blocked", "testnet_blocked", "live_blocked"):
        assert label in result.compliance_labels


def test_universe_selector_and_strategy_suitability_not_consulted() -> None:
    result = evaluate_offline_governance_tick_v0(
        OfflineGovernanceTickInputV0(
            side_state=SideState.NEUTRAL_OBSERVE,
            scope_event=ScopeEvent.UPSCOPE_CONFIRMED,
            universe_selector_consulted=False,
            strategy_suitability_consulted=False,
        )
    )
    _assert_non_authorizing(result)
    assert result.tick_ok is True


def test_pure_transition_decision_never_grants_live_authorization() -> None:
    side, _, decision = transition_state(
        side_state=SideState.NEUTRAL_OBSERVE,
        event=ScopeEvent.UPSCOPE_CONFIRMED,
        scope_state=_EMPTY_SCOPE_STATE,
        rules=_GOOD_RULES,
        envelope=_GOOD_ENVELOPE,
        now_tick=0,
    )
    assert side == SideState.LONG_ARMED
    assert decision.live_authorization_granted is False


def test_harness_avoids_dangerous_imports_by_source_inspection() -> None:
    tree = ast.parse(Path(__file__).read_text(encoding="utf-8"))
    forbidden_roots = {
        "subprocess",
        "socket",
        "requests",
        "urllib",
        "httpx",
        "aiohttp",
        "scheduler",
    }
    forbidden_modules = {
        "trading.master_v2.local_evaluator",
        "ops.p67",
        "ops.p72",
        "ops.p79",
        "webui",
    }
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                root = alias.name.split(".")[0]
                assert root not in forbidden_roots, alias.name
                assert alias.name not in forbidden_modules, alias.name
        if isinstance(node, ast.ImportFrom):
            module = node.module or ""
            root = module.split(".")[0]
            assert root not in forbidden_roots, module
            assert module not in forbidden_modules, module
            assert not module.startswith("ops."), module


def test_harness_imports_only_double_play_state_from_src() -> None:
    tree = ast.parse(Path(__file__).read_text(encoding="utf-8"))
    src_imports: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module and node.module.startswith("trading."):
            src_imports.append(node.module)
    assert src_imports == ["trading.master_v2.double_play_state"]
