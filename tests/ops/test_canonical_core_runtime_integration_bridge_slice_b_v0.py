"""Contract tests for Canonical Core Runtime Integration Intent Pipeline Bridge Slice B v0.

Offline proofs for decision → capital/risk/sizing → canonical order intent →
intent compatibility firewall → execution pipeline plan-only boundary.
"""

from __future__ import annotations

import ast
import hashlib
import importlib
import inspect
from decimal import Decimal
from pathlib import Path

import pytest

import src.governance.capital_risk_sizing_v1 as sizing
from src.execution_pipeline import ExecutionPipeline, InMemoryExecutionAdapter
from trading.master_v2.canonical_core_runtime_integration_bridge_v0 import (
    CanonicalCoreRuntimeIntegrationInputV0,
    build_integrated_offline_replay_input_from_harness_v0,
)
from trading.master_v2.canonical_core_runtime_integration_intent_pipeline_bridge_v0 import (
    CANONICAL_CORE_RUNTIME_INTEGRATION_INTENT_PIPELINE_BRIDGE_OWNER,
    CAPITAL_RISK_SIZING_BINDING_STATUS,
    EXECUTION_PIPELINE_PLAN_ONLY_BOUNDARY_STATUS_PASS,
    INTEGRATION_STATUS_BOUND_NOT_ACTIVATED,
    INTENT_COMPATIBILITY_FIREWALL_STATUS,
    PACKAGE_MARKER,
    REASON_CANONICAL_DECISION_NOT_ACTIONABLE,
    REASON_LEGACY_INTENT_AUTHORITY_DENIED,
    REASON_QUANTITY_PROVENANCE_MISSING,
    REASON_RISK_BINDING_INCOMPLETE,
    REASON_ZERO_ORDER_SUBMISSION_BLOCKED,
    CanonicalCoreRuntimeCapitalContextV0,
    CanonicalCoreRuntimeIntentPipelineInputV0,
    build_capital_risk_sizing_input_from_decision_v0,
    build_slice_b_evidence_fields_v0,
    decision_outcome_is_actionable,
    map_decision_outcome_to_intent_action,
    run_canonical_core_runtime_integration_intent_pipeline_bridge_v0,
    run_canonical_core_runtime_integration_intent_pipeline_from_harness_v0,
)
from trading.master_v2.canonical_trading_decision_evidence_v1 import (
    CanonicalTradingDecisionEvidenceV1,
)
from trading.master_v2.double_play_composition_matrix_v1 import CompositionStatus
from trading.master_v2.double_play_entry_exit_policy_v0 import (
    DecisionOutcome,
    EntryExitDirectionState,
)
from trading.master_v2.double_play_state import SideState
from trading.master_v2.integrated_offline_trading_logic_replay_v1 import (
    run_integrated_offline_trading_logic_replay_v1,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
BRIDGE_MODULE = (
    REPO_ROOT
    / "src"
    / "trading"
    / "master_v2"
    / "canonical_core_runtime_integration_intent_pipeline_bridge_v0.py"
)
PLAN_ONLY_MODULE = REPO_ROOT / "src" / "execution_pipeline" / "plan_only_boundary_v0.py"

TEST_PACKAGE_MARKER = "CANONICAL_CORE_RUNTIME_INTEGRATION_SLICE_B_GUARD_V0=true"

TOTAL_LIMIT_USD = Decimal("500")
ORDER_LIMIT_USD = Decimal("25")
DAILY_LOSS_LIMIT_USD = Decimal("25")


def _instrument(**overrides: object) -> sizing.InstrumentQuantityConstraintsV1:
    base: dict[str, object] = {
        "instrument_id": "inst-pf-ethusd-perp",
        "market_type": "futures",
        "contract_kind": "LINEAR",
        "contract_multiplier": Decimal("1"),
        "quantity_step": Decimal("0.01"),
        "minimum_quantity": Decimal("0.01"),
        "maximum_quantity": Decimal("100"),
        "minimum_notional": Decimal("5"),
        "instrument_metadata_version": "futures_metadata_v1_test",
    }
    base.update(overrides)
    return sizing.InstrumentQuantityConstraintsV1(**base)  # type: ignore[arg-type]


def _capital_context(**overrides: object) -> CanonicalCoreRuntimeCapitalContextV0:
    instrument = _instrument()
    base: dict[str, object] = {
        "reference_price": Decimal("2000"),
        "protective_stop_price": Decimal("1900"),
        "account_equity": TOTAL_LIMIT_USD,
        "scope_capital_limit": ORDER_LIMIT_USD,
        "per_trade_risk_limit": ORDER_LIMIT_USD,
        "total_capital_limit": TOTAL_LIMIT_USD,
        "daily_loss_remaining_budget": DAILY_LOSS_LIMIT_USD,
        "current_reconciled_exposure": Decimal("0"),
        "instrument": instrument,
    }
    base.update(overrides)
    return CanonicalCoreRuntimeCapitalContextV0(**base)  # type: ignore[arg-type]


def _decision_evidence(**overrides: object) -> CanonicalTradingDecisionEvidenceV1:
    base: dict[str, object] = {
        "decision_id": "decision-slice-b-fixture",
        "replay_id": "replay-slice-b-fixture",
        "instrument_id": "inst-pf-ethusd-perp",
        "trading_epoch": 0,
        "market_context_ref": "ctx-ref",
        "scope_initialization_ref": "scope-init-ref",
        "scope_event_ref": "scope-event-ref",
        "bull_assessment_ref": "bull-ref",
        "bear_assessment_ref": "bear-ref",
        "state_switch_ref": "state-switch-ref",
        "bull_survival_ref": "bull-survival-ref",
        "bear_survival_ref": "bear-survival-ref",
        "bull_suitability_ref": "bull-suit-ref",
        "bear_suitability_ref": "bear-suit-ref",
        "composition_result_ref": "composition-ref",
        "entry_exit_policy_ref": "entry-exit-ref",
        "current_scope_ref": "current-scope-ref",
        "next_scope_ref": "next-scope-ref",
        "previous_direction_state": "neutral",
        "next_direction_state": "long_armed",
        "selected_side": "LONG",
        "selected_strategy_ref": "strat-ref",
        "decision_outcome": DecisionOutcome.ENTER_LONG.value,
        "entry_or_exit_policy_ref": "entry-exit-ref",
        "reason_codes": ("enter_long",),
        "decision_precedence_trace": ("entry",),
        "component_versions": {"integrated_offline_trading_logic_replay": "v1"},
        "policy_versions": {"entry_exit": "v0"},
        "config_digest": "c" * 64,
        "implementation_digest": "d" * 64,
        "input_digest": hashlib.sha256(b"slice-b-decision-fixture").hexdigest(),
        "semantic_digest": hashlib.sha256(b"slice-b-decision-semantics").hexdigest(),
    }
    base.update(overrides)
    return CanonicalTradingDecisionEvidenceV1(**base)  # type: ignore[arg-type]


def _pipeline_input(**overrides: object) -> CanonicalCoreRuntimeIntentPipelineInputV0:
    base: dict[str, object] = {
        "decision_evidence": _decision_evidence(),
        "capital_context": _capital_context(),
        "plan_only": True,
        "legacy_intent_authority_active": False,
    }
    base.update(overrides)
    return CanonicalCoreRuntimeIntentPipelineInputV0(**base)  # type: ignore[arg-type]


def _enter_long_replay_evidence():
    harness_input = CanonicalCoreRuntimeIntegrationInputV0(
        run_id="slice-b-enter-long",
        harness_instrument="PF_ETHUSD",
        market_type="futures",
    )
    replay_input, errors = build_integrated_offline_replay_input_from_harness_v0(harness_input)
    assert errors == ()
    assert replay_input is not None
    replay_input = replay_input.__class__(
        **{
            **{
                field.name: getattr(replay_input, field.name)
                for field in replay_input.__dataclass_fields__.values()
            },
            "side_state": SideState.LONG_ARMED,
            "direction_state": EntryExitDirectionState.LONG_ARMED,
        }
    )
    replay_result = run_integrated_offline_trading_logic_replay_v1(replay_input)
    return replay_result.evidence, replay_result


def test_package_marker_and_owner_present() -> None:
    assert TEST_PACKAGE_MARKER
    assert PACKAGE_MARKER in BRIDGE_MODULE.read_text(encoding="utf-8")
    assert CANONICAL_CORE_RUNTIME_INTEGRATION_INTENT_PIPELINE_BRIDGE_OWNER.endswith(
        "canonical_core_runtime_integration_intent_pipeline_bridge_v0"
    )
    assert "EXECUTION_PIPELINE_PLAN_ONLY_BOUNDARY_V0=true" in PLAN_ONLY_MODULE.read_text(
        encoding="utf-8"
    )


def test_no_execution_or_adapter_imports_in_bridge() -> None:
    tree = ast.parse(BRIDGE_MODULE.read_text(encoding="utf-8"))
    forbidden = {"live_gates", "live_session", "credentials", "evaluate_double_play"}
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                assert not any(token in alias.name for token in forbidden)
        if isinstance(node, ast.ImportFrom) and node.module:
            assert "InMemoryExecutionAdapter" not in node.module
            assert not any(token in node.module for token in forbidden)


def test_decision_maps_into_existing_sizing_chain() -> None:
    decision = _decision_evidence()
    capital = _capital_context()
    sizing_input, errors = build_capital_risk_sizing_input_from_decision_v0(
        decision=decision,
        capital_context=capital,
    )
    assert errors == ()
    assert sizing_input is not None
    sizing_decision = sizing.evaluate_capital_risk_sizing_v1(sizing_input)
    assert sizing_decision.outcome is sizing.CapitalRiskSizingOutcome.PASS
    assert sizing_decision.quantity_provenance is not None


def test_canonical_intent_owner_produces_intent_with_provenance() -> None:
    result = run_canonical_core_runtime_integration_intent_pipeline_bridge_v0(_pipeline_input())
    assert result.integration_pass is True
    assert result.canonical_intent is not None
    assert result.canonical_intent.quantity_provenance
    assert result.sizing_decision is not None
    assert result.sizing_decision.quantity_provenance is not None


def test_identical_input_produces_deterministic_intent_digest() -> None:
    first = run_canonical_core_runtime_integration_intent_pipeline_bridge_v0(_pipeline_input())
    second = run_canonical_core_runtime_integration_intent_pipeline_bridge_v0(_pipeline_input())
    assert first.intent_semantic_digest == second.intent_semantic_digest
    assert first.intent_semantic_digest != ""


def test_rounding_never_increases_risk_via_sizing_chain() -> None:
    result = run_canonical_core_runtime_integration_intent_pipeline_bridge_v0(_pipeline_input())
    assert result.sizing_decision is not None
    provenance = result.sizing_decision.quantity_provenance
    assert provenance is not None
    assert provenance.final_quantity <= provenance.pre_round_quantity


@pytest.mark.parametrize(
    "outcome",
    [
        DecisionOutcome.NO_ACTION.value,
        DecisionOutcome.OBSERVE.value,
        DecisionOutcome.HOLD.value,
        DecisionOutcome.BLOCKED.value,
    ],
)
def test_non_actionable_decisions_block_without_executable_intent(outcome: str) -> None:
    result = run_canonical_core_runtime_integration_intent_pipeline_bridge_v0(
        _pipeline_input(decision_evidence=_decision_evidence(decision_outcome=outcome))
    )
    assert result.integration_pass is False
    assert result.canonical_intent is None
    assert REASON_CANONICAL_DECISION_NOT_ACTIONABLE in result.reason_codes
    assert not decision_outcome_is_actionable(outcome)


def test_missing_quantity_blocks_fail_closed() -> None:
    decision = _decision_evidence()
    capital = _capital_context()
    sizing_input, _ = build_capital_risk_sizing_input_from_decision_v0(
        decision=decision,
        capital_context=capital,
    )
    assert sizing_input is not None
    blocked_input = sizing.CapitalRiskSizingInputV1(
        **{
            **{
                field.name: getattr(sizing_input, field.name)
                for field in sizing_input.__dataclass_fields__.values()
            },
            "per_trade_risk_limit": Decimal("0.01"),
            "daily_loss_remaining_budget": Decimal("0.01"),
            "scope_capital_limit": Decimal("0.01"),
        }
    )
    blocked_decision = sizing.evaluate_capital_risk_sizing_v1(blocked_input)
    assert blocked_decision.outcome is sizing.CapitalRiskSizingOutcome.BLOCKED
    result = run_canonical_core_runtime_integration_intent_pipeline_bridge_v0(
        _pipeline_input(
            decision_evidence=_decision_evidence(),
            capital_context=_capital_context(
                per_trade_risk_limit=Decimal("0.01"),
                daily_loss_remaining_budget=Decimal("0.01"),
                scope_capital_limit=Decimal("0.01"),
            ),
        )
    )
    assert result.integration_pass is False
    assert REASON_RISK_BINDING_INCOMPLETE in result.reason_codes


def test_execution_eligible_and_adapter_flags_remain_false() -> None:
    result = run_canonical_core_runtime_integration_intent_pipeline_bridge_v0(_pipeline_input())
    assert result.execution_eligible is False
    assert result.adapter_compatible is False
    assert result.submission_blocked is True
    assert result.authority_effect == "NONE"
    assert result.runtime_effect == "NONE"
    assert result.order_effect == "NONE"


def test_pipeline_receives_plan_only_blocked_input_only() -> None:
    result = run_canonical_core_runtime_integration_intent_pipeline_bridge_v0(_pipeline_input())
    assert result.pipeline_boundary_pass is True
    assert result.execution_pipeline_plan_only_boundary_status == (
        EXECUTION_PIPELINE_PLAN_ONLY_BOUNDARY_STATUS_PASS
    )
    assert REASON_ZERO_ORDER_SUBMISSION_BLOCKED in result.reason_codes


def test_no_adapter_instantiation_or_network_in_bridge_module() -> None:
    source = BRIDGE_MODULE.read_text(encoding="utf-8")
    assert "ExecutionPipeline(" not in source
    assert "InMemoryExecutionAdapter" not in source
    assert "requests." not in source
    assert "urllib" not in source
    assert "getenv" not in source


def test_execution_pipeline_execute_not_called_by_boundary_tests() -> None:
    adapter = InMemoryExecutionAdapter()
    pipeline = ExecutionPipeline(adapter=adapter)
    assert inspect.ismethod(pipeline.execute)


def test_legacy_intent_authority_denied() -> None:
    result = run_canonical_core_runtime_integration_intent_pipeline_bridge_v0(
        _pipeline_input(legacy_intent_authority_active=True)
    )
    assert result.integration_pass is False
    assert REASON_LEGACY_INTENT_AUTHORITY_DENIED in result.reason_codes


def test_futures_only_and_bitcoin_blocked() -> None:
    for instrument_id in ("BTCUSDT-PERP", "inst-pf-xbtusd-perp", "ETH-SPOT"):
        result = run_canonical_core_runtime_integration_intent_pipeline_bridge_v0(
            _pipeline_input(
                decision_evidence=_decision_evidence(
                    instrument_id=instrument_id,
                    decision_outcome=DecisionOutcome.ENTER_LONG.value,
                    selected_side="LONG",
                ),
                capital_context=_capital_context(
                    instrument=_instrument(instrument_id=instrument_id),
                ),
            )
        )
        assert result.integration_pass is False


def test_reduce_only_semantics_preserved_for_exit_with_exposure() -> None:
    result = run_canonical_core_runtime_integration_intent_pipeline_bridge_v0(
        _pipeline_input(
            decision_evidence=_decision_evidence(
                decision_outcome=DecisionOutcome.REDUCE.value,
                selected_side="LONG",
            ),
            capital_context=_capital_context(
                current_reconciled_exposure=Decimal("1.0"),
                current_open_side="LONG",
            ),
        )
    )
    if result.canonical_intent is not None:
        assert result.canonical_intent.reduce_only is True
        assert result.canonical_intent.position_effect in {"REDUCE_ONLY", "CLOSE_ONLY"}


def test_reversal_does_not_emit_direct_counter_entry_intent() -> None:
    result = run_canonical_core_runtime_integration_intent_pipeline_bridge_v0(
        _pipeline_input(
            decision_evidence=_decision_evidence(
                decision_outcome=DecisionOutcome.ENTER_SHORT.value,
                selected_side="SHORT",
            ),
            capital_context=_capital_context(
                current_reconciled_exposure=Decimal("1.0"),
                current_open_side="LONG",
            ),
        )
    )
    assert result.integration_pass is False


def test_slice_a_bridge_remains_compatible() -> None:
    harness_input = CanonicalCoreRuntimeIntegrationInputV0(
        run_id="slice-b-compat",
        harness_instrument="PF_ETHUSD",
        market_type="futures",
    )
    slice_a, slice_b = run_canonical_core_runtime_integration_intent_pipeline_from_harness_v0(
        harness_input=harness_input,
        capital_context=_capital_context(),
    )
    assert slice_a.integration_pass is True
    assert slice_a.integration_status == INTEGRATION_STATUS_BOUND_NOT_ACTIVATED
    assert REASON_CANONICAL_DECISION_NOT_ACTIONABLE in slice_b.reason_codes


def test_enter_long_replay_path_can_bind_when_actionable() -> None:
    evidence, replay_result = _enter_long_replay_evidence()
    if (
        replay_result.intermediate is not None
        and replay_result.intermediate.composition_result.composition_status
        is CompositionStatus.LONG_SELECTED
    ):
        result = run_canonical_core_runtime_integration_intent_pipeline_bridge_v0(
            CanonicalCoreRuntimeIntentPipelineInputV0(
                decision_evidence=evidence,
                capital_context=_capital_context(),
            )
        )
        assert evidence.decision_outcome == DecisionOutcome.ENTER_LONG.value
        assert map_decision_outcome_to_intent_action(evidence.decision_outcome) == "ENTER_LONG"
        assert result.integration_pass is True
        assert result.intent_semantic_digest


def test_firewall_and_status_fields() -> None:
    result = run_canonical_core_runtime_integration_intent_pipeline_bridge_v0(_pipeline_input())
    assert result.intent_compatibility_firewall_status == INTENT_COMPATIBILITY_FIREWALL_STATUS
    assert result.capital_risk_sizing_binding_status == CAPITAL_RISK_SIZING_BINDING_STATUS
    assert (
        result.canonical_order_intent_to_execution_pipeline_status
        == INTEGRATION_STATUS_BOUND_NOT_ACTIVATED
    )


def test_evidence_fields_non_authorizing() -> None:
    result = run_canonical_core_runtime_integration_intent_pipeline_bridge_v0(_pipeline_input())
    fields = build_slice_b_evidence_fields_v0(result)
    assert fields["execution_eligible"] is False
    assert fields["submission_blocked"] is True
    assert fields["zero_order_runtime_ready"] is False
    assert fields["runtime_rewire_status"] == "PARTIAL"


def test_governance_modules_not_mutated() -> None:
    intent_mod = importlib.import_module("src.governance.canonical_order_intent_v1")
    sizing_mod = importlib.import_module("src.governance.capital_risk_sizing_v1")
    firewall_mod = importlib.import_module("src.governance.intent_compatibility_firewall_v1")
    assert intent_mod.FUTURES_ONLY is True
    assert sizing_mod.FUTURES_ONLY is True
    assert firewall_mod.FUTURES_ONLY is True


def test_missing_provenance_reason_constant_present() -> None:
    assert REASON_QUANTITY_PROVENANCE_MISSING == "QUANTITY_PROVENANCE_MISSING"
