"""Post-6135 Appendix-A proof-only: Replay vs isolated 29P/Safety/29Q owners.

Semantics-neutral. No runtime mutation. Owner-composed golden vector; no JSON corpus.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from pathlib import Path
from typing import Any, Optional

import pytest

from src.governance.canonical_order_intent_v1 import CanonicalOrderIntentV1, IntentAction
from src.governance.capital_risk_sizing_v1 import CapitalRiskSizingDecisionV1
from trading.master_v2.canonical_order_intent_offline_replay_binding_adapter_v0 import (
    CanonicalOrderIntentOfflineReplayBindingResultV0,
)
from trading.master_v2.capital_risk_sizing_offline_replay_binding_adapter_v0 import (
    CapitalRiskSizingOfflineReplayBindingResultV0,
)
from trading.master_v2.double_play_entry_exit_policy_v0 import DecisionOutcome
from trading.master_v2.integrated_offline_trading_logic_replay_v1 import (
    INTEGRATED_OFFLINE_TRADING_LOGIC_REPLAY_OWNER,
    run_integrated_offline_trading_logic_replay_v1,
)
from trading.master_v2.safety_kernel_offline_replay_binding_adapter_v0 import (
    SafetyKernelOfflineReplayBindingResultV0,
    SafetyKernelOfflineReplayBoundaryV0,
)
from tests.trading.master_v2.test_master_v2_integrated_replay_safety_before_intent_restore_contract_v1 import (
    _confirmed_replay_input,
    _exit_replay_input,
)

REPO_ROOT = Path(__file__).resolve().parents[3]
REPLAY_MODULE = REPO_ROOT / "src/trading/master_v2/integrated_offline_trading_logic_replay_v1.py"
SPEC_PATH = (
    REPO_ROOT
    / "docs/ops/specs/MASTER_V2_INTEGRATED_REPLAY_APPENDIX_A_CORE_LOGIC_PARITY_POST_6135_V1.md"
)
_ENTER_OUTCOMES = frozenset({DecisionOutcome.ENTER_LONG.value, DecisionOutcome.ENTER_SHORT.value})
_ENTER_ACTIONS = frozenset({IntentAction.ENTER_LONG.value, IntentAction.ENTER_SHORT.value})


@dataclass(frozen=True)
class _Capture:
    kwargs: dict[str, Any]
    result: Any


def _sizing_semantic(
    decision: Optional[CapitalRiskSizingDecisionV1],
) -> Optional[dict[str, Any]]:
    if decision is None:
        return None
    outcome = decision.outcome.value if hasattr(decision.outcome, "value") else decision.outcome
    return {
        "outcome": outcome,
        "final_quantity": decision.final_quantity,
        "selected_side": decision.selected_side,
        "reason_codes": tuple(decision.reason_codes),
        "authority_effect": decision.authority_effect,
        "runtime_effect": decision.runtime_effect,
    }


def _safety_semantic(boundary: SafetyKernelOfflineReplayBoundaryV0) -> dict[str, Any]:
    return {
        "hard_block_reasons": tuple(boundary.hard_block_reasons),
        "reason_codes": tuple(boundary.reason_codes),
        "no_permission_issued": boundary.no_permission_issued,
        "no_submission_before_permission": boundary.no_submission_before_permission,
        "safety_boundary_bound": boundary.safety_boundary_bound,
        "runtime_authority_effect": boundary.runtime_authority_effect,
        "order_effect": boundary.order_effect,
        "credential_effect": boundary.credential_effect,
    }


def _intent_semantic(intent: Optional[CanonicalOrderIntentV1]) -> Optional[dict[str, Any]]:
    if intent is None:
        return None
    return {
        "intent_action": intent.intent_action,
        "quantity": intent.quantity,
        "instrument_id": intent.instrument_id,
        "side": intent.side,
        "submission_authorized": intent.submission_authorized,
        "execution_eligible": intent.execution_eligible,
        "authority_effect": intent.authority_effect,
        "runtime_effect": intent.runtime_effect,
        "adapter_compatible": intent.adapter_compatible,
    }


def _instrument_replay_owners(
    monkeypatch: pytest.MonkeyPatch,
    *,
    force_safety_hard_block: bool = False,
) -> tuple[list[str], dict[str, list[_Capture]], dict[str, Any]]:
    import trading.master_v2.canonical_order_intent_offline_replay_binding_adapter_v0 as coi_mod
    import trading.master_v2.capital_risk_sizing_offline_replay_binding_adapter_v0 as crs_mod
    import trading.master_v2.killswitch_boundary_offline_replay_binding_adapter_v0 as ks_mod
    import trading.master_v2.reconciliation_unknown_outcome_offline_replay_binding_adapter_v0 as ruo_mod
    import trading.master_v2.safety_kernel_offline_replay_binding_adapter_v0 as sk_mod

    order: list[str] = []
    captures: dict[str, list[_Capture]] = {
        "29P": [],
        "SAFETY": [],
        "29Q": [],
        "RECON": [],
        "KS": [],
    }
    real_29p = crs_mod.bind_capital_risk_sizing_offline_replay_evidence_v0
    real_safety = sk_mod.bind_safety_kernel_offline_replay_evidence_v0
    real_29q = coi_mod.bind_canonical_order_intent_offline_replay_evidence_v0
    real_recon = ruo_mod.bind_reconciliation_unknown_outcome_offline_replay_evidence_v0
    real_ks = ks_mod.bind_killswitch_boundary_offline_replay_evidence_v0

    def wrap_29p(*args: Any, **kwargs: Any) -> CapitalRiskSizingOfflineReplayBindingResultV0:
        order.append("29P")
        result = real_29p(*args, **kwargs)
        captures["29P"].append(_Capture(kwargs={"args": args, **kwargs}, result=result))
        return result

    def wrap_safety(evidence: Any, *, context: Any) -> SafetyKernelOfflineReplayBindingResultV0:
        order.append("SAFETY")
        ctx = context
        if force_safety_hard_block:
            ctx = replace(context, killswitch_blocked=True, safety_decision_allowed=False)
        result = real_safety(evidence, context=ctx)
        captures["SAFETY"].append(
            _Capture(kwargs={"evidence": evidence, "context": ctx}, result=result)
        )
        return result

    def wrap_29q(*args: Any, **kwargs: Any) -> CanonicalOrderIntentOfflineReplayBindingResultV0:
        order.append("29Q")
        result = real_29q(*args, **kwargs)
        captures["29Q"].append(_Capture(kwargs={"args": args, **kwargs}, result=result))
        return result

    def wrap_recon(*args: Any, **kwargs: Any) -> Any:
        order.append("RECON")
        result = real_recon(*args, **kwargs)
        captures["RECON"].append(_Capture(kwargs={"args": args, **kwargs}, result=result))
        return result

    def wrap_ks(*args: Any, **kwargs: Any) -> Any:
        order.append("KS")
        result = real_ks(*args, **kwargs)
        captures["KS"].append(_Capture(kwargs={"args": args, **kwargs}, result=result))
        return result

    monkeypatch.setattr(crs_mod, "bind_capital_risk_sizing_offline_replay_evidence_v0", wrap_29p)
    monkeypatch.setattr(sk_mod, "bind_safety_kernel_offline_replay_evidence_v0", wrap_safety)
    monkeypatch.setattr(coi_mod, "bind_canonical_order_intent_offline_replay_evidence_v0", wrap_29q)
    monkeypatch.setattr(
        ruo_mod, "bind_reconciliation_unknown_outcome_offline_replay_evidence_v0", wrap_recon
    )
    monkeypatch.setattr(ks_mod, "bind_killswitch_boundary_offline_replay_evidence_v0", wrap_ks)
    reals = {"29P": real_29p, "SAFETY": real_safety, "29Q": real_29q}
    return order, captures, reals


def _independent_29p(
    capture: _Capture, real_29p: Any
) -> CapitalRiskSizingOfflineReplayBindingResultV0:
    args = capture.kwargs["args"]
    kwargs = {k: v for k, v in capture.kwargs.items() if k != "args"}
    return real_29p(*args, **kwargs)


def _independent_safety(
    capture: _Capture, real_safety: Any
) -> SafetyKernelOfflineReplayBindingResultV0:
    return real_safety(capture.kwargs["evidence"], context=capture.kwargs["context"])


def _independent_29q(
    capture: _Capture, real_29q: Any
) -> CanonicalOrderIntentOfflineReplayBindingResultV0:
    args = capture.kwargs["args"]
    kwargs = {k: v for k, v in capture.kwargs.items() if k != "args"}
    return real_29q(*args, **kwargs)


@pytest.mark.parametrize(
    ("case_id", "force_safety_hard_block", "build_input"),
    [
        ("CASE_A_SAFETY_PASS_ENTER", False, lambda: _confirmed_replay_input(side="LONG")),
        ("CASE_B_SAFETY_HARDBLOCK_ENTER", True, lambda: _confirmed_replay_input(side="LONG")),
        ("CASE_C_EXIT_PATH", False, _exit_replay_input),
    ],
)
def test_appendix_a_owner_composed_replay_parity(
    monkeypatch: pytest.MonkeyPatch,
    case_id: str,
    force_safety_hard_block: bool,
    build_input: Any,
) -> None:
    order, captures, reals = _instrument_replay_owners(
        monkeypatch, force_safety_hard_block=force_safety_hard_block
    )
    result = run_integrated_offline_trading_logic_replay_v1(build_input())
    assert result.intermediate is not None

    assert captures["29P"], case_id
    assert captures["SAFETY"], case_id
    assert captures["RECON"], case_id
    assert captures["KS"], case_id
    assert order[0] == "29P"
    assert order[1] == "SAFETY"
    assert "RECON" in order
    assert "KS" in order
    assert order.index("SAFETY") < order.index("RECON")
    assert order.index("RECON") < order.index("KS")

    expected_29p = _independent_29p(captures["29P"][0], reals["29P"])
    expected_safety = _independent_safety(captures["SAFETY"][0], reals["SAFETY"])
    replay_29p = captures["29P"][0].result
    replay_safety = captures["SAFETY"][0].result

    assert _sizing_semantic(replay_29p.sizing_decision) == _sizing_semantic(
        expected_29p.sizing_decision
    )
    assert replay_29p.quantity_status == expected_29p.quantity_status
    assert replay_29p.risk_sizing_effect == expected_29p.risk_sizing_effect
    assert _safety_semantic(replay_safety.boundary) == _safety_semantic(expected_safety.boundary)
    assert replay_safety.safety_boundary_effect == expected_safety.safety_boundary_effect
    assert replay_safety.binding_applied is expected_safety.binding_applied
    assert expected_safety.boundary.no_permission_issued is True
    assert expected_safety.boundary.runtime_authority_effect == "NONE"
    assert expected_safety.boundary.order_effect == "NONE"

    enter_blocked = bool(replay_safety.boundary.hard_block_reasons) and (
        result.evidence.decision_outcome in _ENTER_OUTCOMES
    )

    if case_id == "CASE_B_SAFETY_HARDBLOCK_ENTER":
        assert result.evidence.decision_outcome in _ENTER_OUTCOMES
        assert replay_safety.boundary.hard_block_reasons
        assert "entry_blocked_by_safety_kernel_boundary" in replay_safety.boundary.reason_codes
        assert enter_blocked is True
        assert "29Q" not in order
        assert captures["29Q"] == []
        assert result.intermediate.canonical_order_intent is None
        assert result.evidence.reconciliation_unknown_outcome_ref
        assert result.evidence.killswitch_boundary_ref
        post_29p_evidence = replay_29p.evidence
        isolated_would_be = reals["29Q"](
            post_29p_evidence,
            sizing_decision=replay_29p.sizing_decision,
            capital_context=None,
        )
        if isolated_would_be.canonical_intent is not None:
            assert isolated_would_be.canonical_intent.intent_action in _ENTER_ACTIONS
        expected_29q_semantic = None
    elif case_id == "CASE_C_EXIT_PATH":
        assert result.evidence.decision_outcome == DecisionOutcome.EXIT.value
        assert result.evidence.decision_outcome not in _ENTER_OUTCOMES
        assert "29Q" in order
        assert order.index("SAFETY") < order.index("29Q")
        replay_intent = result.intermediate.canonical_order_intent
        if replay_intent is not None:
            assert replay_intent.intent_action not in _ENTER_ACTIONS
            assert replay_intent.submission_authorized is False
            assert replay_intent.execution_eligible is False
        expected_29q = _independent_29q(captures["29Q"][0], reals["29Q"])
        assert _intent_semantic(captures["29Q"][0].result.canonical_intent) == _intent_semantic(
            expected_29q.canonical_intent
        )
        expected_29q_semantic = _intent_semantic(expected_29q.canonical_intent)
    else:
        assert result.evidence.decision_outcome == DecisionOutcome.ENTER_LONG.value
        assert enter_blocked is False
        assert "29Q" in order
        assert order.index("SAFETY") < order.index("29Q")
        expected_29q = _independent_29q(captures["29Q"][0], reals["29Q"])
        replay_intent = result.intermediate.canonical_order_intent
        assert _intent_semantic(replay_intent) == _intent_semantic(expected_29q.canonical_intent)
        assert _intent_semantic(captures["29Q"][0].result.canonical_intent) == _intent_semantic(
            expected_29q.canonical_intent
        )
        if replay_intent is not None:
            assert replay_intent.intent_action == IntentAction.ENTER_LONG.value
            assert replay_intent.submission_authorized is False
            assert replay_intent.execution_eligible is False
            assert replay_intent.authority_effect == "NONE"
        expected_29q_semantic = _intent_semantic(expected_29q.canonical_intent)

    composed = (
        _sizing_semantic(expected_29p.sizing_decision),
        _safety_semantic(expected_safety.boundary),
        expected_29q_semantic,
    )
    replay_tuple = (
        _sizing_semantic(result.intermediate.capital_risk_sizing_decision),
        _safety_semantic(replay_safety.boundary),
        _intent_semantic(result.intermediate.canonical_order_intent),
    )
    assert replay_tuple == composed


def test_spec_and_negative_contracts_are_proof_only() -> None:
    spec = SPEC_PATH.read_text(encoding="utf-8")
    assert (
        "PROOF_SLICE_ID=MASTER_V2_INTEGRATED_REPLAY_APPENDIX_A_CORE_LOGIC_PARITY_POST_6135_V1"
        in spec
    )
    assert "NORMATIVE_PARITY_SUBJECT=ACTIVE_INTEGRATED_REPLAY_POST_6135" in spec
    assert "BASELINE_ORIGIN_MAIN_SHA=6ad52f7b762da8da12b0d26056e6a9fd3dab4f11" in spec
    assert "CLOSED_WIRING_PR=6135" in spec
    assert "PROOF_ONLY=true" in spec
    assert "RUNTIME_MUTATION=false" in spec
    assert "NEW_GOLDEN_VECTOR_CORPUS=false" in spec
    assert "A07_HISTORICAL_STAGE_CREATED=false" in spec
    assert "A08_HISTORICAL_STAGE_CREATED=false" in spec
    assert "A06_PROMOTED=false" in spec
    assert "XP03_ACTIVATED=false" in spec
    assert "FOUR_WAY_HARNESS_RESCOPED=false" in spec
    assert "CURRENT_6135_GRANT_REUSED_AS_WILDCARD=false" in spec
    source = REPLAY_MODULE.read_text(encoding="utf-8")
    assert "capital_risk_sizing_safety_intent_restore_v1" not in source
    assert "compose_capital_risk_sizing_intent_from_core_evidence_v1" not in source
    assert "run_canonical_core_runtime_integration_intent_pipeline" not in source
    assert "economic_viability_evidence_v1" not in source
    assert INTEGRATED_OFFLINE_TRADING_LOGIC_REPLAY_OWNER.endswith(
        "integrated_offline_trading_logic_replay_v1"
    )
