"""Negative host admission before financial/DDO handoff; frozen replay stays exact."""

from dataclasses import replace
import hashlib
import json

from src.learning.deterministic_decision_outcome_v0.capture_v0 import (
    DdoCaptureBindingV0,
    bind_capture_session_v0,
    reset_capture_session_v0,
)
from trading.master_v2.double_play_entry_exit_policy_v0 import TradingGate
from trading.master_v2.survival_numeric_admission_v1 import (
    admit_survival_numeric_inputs_v1,
    admit_survival_numeric_policy_v1,
)


def _restricted_input(inp, policy, reasons):
    gate = inp.trading_gate
    if gate not in (TradingGate.BLOCKED, TradingGate.EXIT_ONLY):
        gate = TradingGate.EXIT_ONLY
    material = dict(
        schema="current_numeric_entry_admission.v1",
        input_digest=inp.input_digest,
        reason_codes=sorted(reasons),
        trading_gate=gate.value,
        authority="NONE",
    )
    return replace(
        inp,
        trading_gate=gate,
        policies=replace(inp.policies, survival=policy),
        input_digest=hashlib.sha256(json.dumps(material, sort_keys=True).encode()).hexdigest(),
    )


def prepare_current_productive_numeric_entry_v1(inp, *, replay_runner):
    """Validate actual pure replay inputs before its result can enter finance.

    Valid no-capture calls reuse the pure preview. Invalid inputs restrict the
    original Entry gate; confirmation/store writers run only after the final
    replay. No original Survival outcome is rewritten as a new native outcome.
    """
    policy, reasons = admit_survival_numeric_policy_v1(inp.policies.survival)
    if reasons:
        return _restricted_input(inp, policy, reasons), None, reasons

    # Do not publish optional evidence-only files or DDO from the preview.
    preview_input = replace(inp, regime_bull_bear_switch_evidence_path=None)
    capture_token = bind_capture_session_v0(DdoCaptureBindingV0(enabled=False))
    try:
        preview = replay_runner(preview_input)
    finally:
        reset_capture_session_v0(capture_token)
    if preview.intermediate is None:
        return inp, preview, ()
    from trading.master_v2.integrated_offline_trading_logic_replay_v1 import (
        _survival_input_for_assessment,
    )

    blocked = []
    for side in ("bull", "bear"):
        assessment = getattr(preview.intermediate, side + "_assessment")
        if assessment is None:
            continue
        # This frozen builder is pure. Same input/assessment gives the actual
        # cost/metric fields; there is no proxy or duplicated economic formula.
        admission = admit_survival_numeric_inputs_v1(
            _survival_input_for_assessment(inp, assessment), inp.policies.survival
        )
        blocked.extend(admission.reason_codes)
    reasons = tuple(dict.fromkeys(blocked))
    if reasons:
        return _restricted_input(inp, policy, reasons), None, reasons
    return inp, preview if inp.regime_bull_bear_switch_evidence_path is None else None, ()
