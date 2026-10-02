"""Forensic-only executable quantity override after real LIVE-29P sizing (default OFF).

RUNTIME_AUTHORIZATION_EFFECT=NONE — no POST, no policy forgery, no external effects.
Real sizing evidence is preserved separately from downstream forensic rebound.
"""

from __future__ import annotations

import json
from contextvars import ContextVar
from contextvars import Token as _CtxReset
from dataclasses import dataclass, replace
from datetime import datetime, timezone
from decimal import ROUND_CEILING, Decimal, InvalidOperation
from pathlib import Path
from typing import Any, Mapping, Optional

from src.governance.capital_risk_sizing_v1 import (
    AUTHORITY_EFFECT_NONE,
    REASON_PASS,
    RUNTIME_EFFECT_NONE,
    CanonicalPositionSizingV1,
    CapitalRiskSizingDecisionV1,
    CapitalRiskSizingOutcome,
    CapitalRiskSizingPolicyV1,
    FinalQuantityStatus,
    InstrumentQuantityConstraintsV1,
    PostSizingRiskAssessmentV1,
    PostSizingRiskStatus,
    QuantityProvenanceV1,
    QuantityStatus,
    _floor_to_lot,
    _linear_projected_notional,
    _linear_projected_stop_loss,
    _policy_digest,
    _sha256_hex,
    _contract_ref,
    IMPLEMENTATION_DIGEST,
)
from trading.master_v2.integrated_offline_trading_logic_replay_v1 import (
    IntegratedOfflineReplayResultV1,
)

OWNER = (
    "full_core_live_path_composition_root_v1."
    "current_productive_forensic_executable_quantity_override_v1"
)

REASON_FORENSIC_EXECUTABLE_QUANTITY_OVERRIDE = "FORENSIC_EXECUTABLE_QUANTITY_OVERRIDE"
PROVENANCE_FORENSIC_OVERRIDE = "FORENSIC_EXECUTABLE_QUANTITY_OVERRIDE_V1"
PROVENANCE_CURRENT_DERIVED_MIN_VENUE = "CURRENT_CONTRACT_MIN_VENUE_QUANTITY_DERIVED"
PROVENANCE_EXPLICIT_FORENSIC_INPUT = "EXPLICIT_FORENSIC_INPUT"

SUMMARY_FILENAME = "forensic_executable_quantity_override_summary_v1.json"
LEDGER_FILENAME = "forensic_executable_quantity_override_v1.jsonl"

_session_var: ContextVar["ForensicExecutableQuantityOverrideSessionV1 | None"] = ContextVar(
    "forensic_executable_quantity_override_session_v1", default=None
)


@dataclass
class ForensicExecutableQuantityOverrideSessionV1:
    enabled: bool
    explicit_forensic_quantity: Decimal | None
    product_evidence_root: Path
    continuous_run_id: str
    require_ghv_pre_external_runtime_flight_recorder_v1: bool


@dataclass(frozen=True)
class ForensicExecutableQuantityOverrideResultV1:
    replay: IntegratedOfflineReplayResultV1
    sizing_decision: CapitalRiskSizingDecisionV1
    sizing_outcome: str
    override_used: bool
    forensic_quantity: Decimal | None
    quantity_provenance_mode: str


def bind_forensic_executable_quantity_override_session_v1(
    session: ForensicExecutableQuantityOverrideSessionV1 | None,
) -> _CtxReset:
    return _session_var.set(session)


def reset_forensic_executable_quantity_override_session_v1(ctx_reset_handle: _CtxReset) -> None:
    _session_var.reset(ctx_reset_handle)


def active_forensic_executable_quantity_override_session_v1() -> (
    ForensicExecutableQuantityOverrideSessionV1 | None
):
    session = _session_var.get()
    if session is None or not session.enabled:
        return None
    return session


def _utc_now_iso_v1() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ")


def _atomic_append_jsonl_v1(*, path: Path, record: Mapping[str, Any]) -> None:
    line = json.dumps(dict(record), sort_keys=True, ensure_ascii=True) + "\n"
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(line)


def _parse_explicit_quantity_v1(raw: str | None) -> Decimal | None:
    if raw is None or not str(raw).strip():
        return None
    try:
        value = Decimal(str(raw).strip())
    except (InvalidOperation, ValueError):
        return None
    if not value.is_finite() or value <= 0:
        return None
    return value


def forensic_override_guards_satisfied_v1(
    *,
    require_flight_recorder: bool,
    ghv_pre_external_runtime_flight_recorder_enabled: bool,
) -> tuple[bool, tuple[str, ...]]:
    from src.ops.full_core_live_path_composition_root_v1.current_productive_synthetic_enter_forensic_v1 import (
        active_synthetic_enter_forensic_session_v1,
    )
    from src.ops.full_core_live_path_composition_root_v1.productive_golden_happy_vector_forensic_observability_v1 import (
        active_forensic_observability_session_v1,
    )

    reasons: list[str] = []
    if active_synthetic_enter_forensic_session_v1() is None:
        reasons.append("SYNTHETIC_ENTER_FORENSIC_SESSION_REQUIRED")
    if active_forensic_observability_session_v1() is None:
        reasons.append("GHV_FORENSIC_OBSERVABILITY_SESSION_REQUIRED")
    if require_flight_recorder and not ghv_pre_external_runtime_flight_recorder_enabled:
        reasons.append("GHV_PRE_EXTERNAL_RUNTIME_FLIGHT_RECORDER_REQUIRED")
    return (len(reasons) == 0, tuple(reasons))


def derive_forensic_executable_quantity_v1(
    *,
    constraints: InstrumentQuantityConstraintsV1,
    reference_price: Decimal,
    candidate_quantity_upper_bound: Decimal,
    explicit_forensic_quantity: Decimal | None,
) -> tuple[Decimal | None, str]:
    """Smallest venue-valid quantity within real pre-sizing upper bound."""
    lot = constraints.lot_size
    if lot <= 0:
        return None, PROVENANCE_CURRENT_DERIVED_MIN_VENUE
    max_q = candidate_quantity_upper_bound
    if max_q <= 0:
        return None, PROVENANCE_CURRENT_DERIVED_MIN_VENUE

    if explicit_forensic_quantity is not None:
        q = _floor_to_lot(explicit_forensic_quantity, lot)
        if q <= 0:
            q = lot
        mode = PROVENANCE_EXPLICIT_FORENSIC_INPUT
    else:
        q = constraints.minimum_quantity
        if q <= 0:
            q = lot
        q = _floor_to_lot(q, lot)
        if q < constraints.minimum_quantity:
            q = _floor_to_lot(constraints.minimum_quantity, lot)
            if q < constraints.minimum_quantity:
                q = constraints.minimum_quantity
        mode = PROVENANCE_CURRENT_DERIVED_MIN_VENUE

    multiplier = constraints.contract_multiplier
    if constraints.minimum_notional is not None and reference_price > 0:
        notional = _linear_projected_notional(reference_price, multiplier, q)
        if notional < constraints.minimum_notional:
            need = constraints.minimum_notional / (reference_price * multiplier)
            steps = (need / lot).quantize(Decimal("1"), rounding=ROUND_CEILING)
            q_candidate = steps * lot
            if q_candidate > q:
                q = q_candidate

    if q > max_q:
        return None, mode
    if q < constraints.minimum_quantity:
        return None, mode
    if constraints.maximum_quantity is not None and q > constraints.maximum_quantity:
        return None, mode
    return q, mode


def _real_sizing_is_executable_v1(decision: CapitalRiskSizingDecisionV1) -> bool:
    if decision.outcome is CapitalRiskSizingOutcome.PASS and decision.final_quantity > 0:
        return True
    return False


def _build_forensic_pass_sizing_decision_v1(
    *,
    real_decision: CapitalRiskSizingDecisionV1,
    constraints: InstrumentQuantityConstraintsV1,
    forensic_quantity: Decimal,
    reference_price: Decimal,
    risk_distance: Decimal,
    policy_version: str,
    config_digest: str,
    decision_id: str,
) -> CapitalRiskSizingDecisionV1 | None:
    pre = real_decision.pre_sizing_risk
    envelope = real_decision.scope_capital_envelope
    multiplier = constraints.contract_multiplier
    rounded = forensic_quantity
    resulting_notional = _linear_projected_notional(reference_price, multiplier, rounded)
    if (
        constraints.minimum_notional is not None
        and resulting_notional < constraints.minimum_notional
    ):
        return None
    if constraints.maximum_quantity is not None and rounded > constraints.maximum_quantity:
        return None

    max_loss_budget = pre.maximum_loss_budget
    resulting_max_loss = _linear_projected_stop_loss(risk_distance, multiplier, rounded)
    if resulting_max_loss > max_loss_budget:
        return None
    if resulting_notional > envelope.per_order_cap:
        return None

    daily_loss = envelope.daily_loss_state
    daily_limit = daily_loss.get("limit_usd") if isinstance(daily_loss, Mapping) else None
    slot_state = envelope.position_slot_state
    max_positions_raw = slot_state.get("max_positions") if isinstance(slot_state, Mapping) else "1"
    policy = CapitalRiskSizingPolicyV1(
        policy_version=policy_version,
        total_capital_limit_usd=envelope.total_capital_limit,
        order_limit_usd=envelope.per_order_cap,
        daily_loss_limit_usd=Decimal(str(daily_limit or envelope.total_capital_limit)),
        max_positions=int(max_positions_raw or 1),
    )
    pol_digest = _policy_digest(policy)

    canonical_sizing = CanonicalPositionSizingV1(
        decision_id=decision_id,
        instrument_id=str(envelope.instrument_id),
        side=pre.side,
        raw_quantity=rounded,
        bounded_quantity_before_rounding=rounded,
        lot_size=constraints.lot_size,
        rounded_quantity=rounded,
        reference_price=reference_price,
        resulting_notional=resulting_notional,
        quantity_status=QuantityStatus.PASS,
        reason_codes=(REASON_FORENSIC_EXECUTABLE_QUANTITY_OVERRIDE, REASON_PASS),
        policy_digest=pol_digest,
        input_digest=pre.input_digest,
    )

    post_sizing = PostSizingRiskAssessmentV1(
        proposed_quantity=rounded,
        final_allowed_quantity=rounded,
        resulting_notional=resulting_notional,
        resulting_max_loss=resulting_max_loss,
        exposure_after=resulting_notional,
        slot_usage_after=int(
            (
                envelope.position_slot_state.get("open_count")
                if isinstance(envelope.position_slot_state, Mapping)
                else 0
            )
            or 0
        ),
        status=PostSizingRiskStatus.PASS,
        reason_codes=(REASON_FORENSIC_EXECUTABLE_QUANTITY_OVERRIDE, REASON_PASS),
        input_digest=pre.input_digest,
    )

    quantity_provenance = QuantityProvenanceV1(
        decision_id=decision_id,
        source_contract_refs=(
            "CanonicalTradingDecisionEvidenceV1",
            PROVENANCE_FORENSIC_OVERRIDE,
        ),
        capital_envelope_ref=_contract_ref(
            "ScopeCapitalEnvelopeV1", _sha256_hex({"decision_id": decision_id})
        ),
        pre_sizing_risk_ref=_contract_ref(
            "PreSizingRiskAssessmentV1",
            _sha256_hex({"bound": str(pre.candidate_quantity_upper_bound)}),
        ),
        sizing_ref=_contract_ref("CanonicalPositionSizingV1", pol_digest),
        post_sizing_risk_ref=_contract_ref(
            "PostSizingRiskAssessmentV1", _sha256_hex({"qty": str(rounded)})
        ),
        instrument_metadata_ref=str(constraints.instrument_metadata_version),
        policy_version=policy_version,
        config_digest=config_digest,
        implementation_digest=IMPLEMENTATION_DIGEST,
        final_quantity=rounded,
        final_quantity_status=FinalQuantityStatus.PASS,
        authority_effect=AUTHORITY_EFFECT_NONE,
        runtime_effect=RUNTIME_EFFECT_NONE,
        adapter_compatible=True,
    )

    return CapitalRiskSizingDecisionV1(
        outcome=CapitalRiskSizingOutcome.PASS,
        final_quantity=rounded,
        selected_side=real_decision.selected_side,
        scope_capital_envelope=envelope,
        pre_sizing_risk=pre,
        canonical_position_sizing=canonical_sizing,
        post_sizing_risk=post_sizing,
        quantity_provenance=quantity_provenance,
        reason_codes=(REASON_FORENSIC_EXECUTABLE_QUANTITY_OVERRIDE, REASON_PASS),
        authority_effect=AUTHORITY_EFFECT_NONE,
        runtime_effect=RUNTIME_EFFECT_NONE,
        adapter_compatible=True,
    )


def persist_forensic_executable_quantity_evidence_v1(
    *,
    session: ForensicExecutableQuantityOverrideSessionV1,
    cycle_index: int,
    natural_decision_before_synthetic: str,
    real_sizing_outcome: str,
    real_final_quantity: str,
    override_used: bool,
    forensic_quantity: str,
    quantity_provenance_mode: str,
    downstream_quantity_consumed: str,
    policy_outcome_after_override: str,
    venue_plan_status_after_override: str,
    pre_external_reached: bool,
    post_count: int,
    external_effect_count: int,
) -> None:
    root = Path(session.product_evidence_root)
    record = {
        "schema": "forensic_executable_quantity_override.v1",
        "owner": OWNER,
        "continuous_run_id": session.continuous_run_id,
        "cycle_index": cycle_index,
        "recorded_at": _utc_now_iso_v1(),
        "SYNTHETIC_ENTER_USED": True,
        "NATURAL_DECISION_BEFORE_SYNTHETIC": natural_decision_before_synthetic,
        "REAL_SIZING_OUTCOME_BEFORE_OVERRIDE": real_sizing_outcome,
        "REAL_FINAL_QUANTITY_BEFORE_OVERRIDE": real_final_quantity,
        "FORENSIC_EXECUTABLE_QUANTITY_OVERRIDE_ENABLED": True,
        "FORENSIC_EXECUTABLE_QUANTITY_OVERRIDE_USED": override_used,
        "FORENSIC_EXECUTABLE_QUANTITY": forensic_quantity,
        "FORENSIC_QUANTITY_PROVENANCE": quantity_provenance_mode,
        "DOWNSTREAM_QUANTITY_CONSUMED": downstream_quantity_consumed,
        "POLICY_OUTCOME_AFTER_OVERRIDE": policy_outcome_after_override,
        "VENUE_PLAN_STATUS_AFTER_OVERRIDE": venue_plan_status_after_override,
        "PRE_EXTERNAL_REACHED": pre_external_reached,
        "POST_COUNT": post_count,
        "EXTERNAL_EFFECT_COUNT": external_effect_count,
    }
    _atomic_append_jsonl_v1(path=root / LEDGER_FILENAME, record=record)
    (root / SUMMARY_FILENAME).write_text(
        json.dumps(record, sort_keys=True, indent=2) + "\n",
        encoding="utf-8",
    )


def maybe_apply_forensic_executable_quantity_override_after_live_29p_v1(
    *,
    rebound_replay: IntegratedOfflineReplayResultV1,
    sizing_decision: CapitalRiskSizingDecisionV1,
    constraints: InstrumentQuantityConstraintsV1,
    live_ctx: Any,
    cycle_index: int,
    ghv_pre_external_runtime_flight_recorder_enabled: bool = False,
) -> ForensicExecutableQuantityOverrideResultV1:
    from src.ops.full_core_live_path_composition_root_v1.current_productive_enter_live_29p_join_v1 import (
        _rebound_replay_with_sizing_decision_v1,
    )

    session = active_forensic_executable_quantity_override_session_v1()
    if session is None:
        return ForensicExecutableQuantityOverrideResultV1(
            replay=rebound_replay,
            sizing_decision=sizing_decision,
            sizing_outcome=str(getattr(sizing_decision.outcome, "value", sizing_decision.outcome)),
            override_used=False,
            forensic_quantity=None,
            quantity_provenance_mode="",
        )

    guards_ok, guard_reasons = forensic_override_guards_satisfied_v1(
        require_flight_recorder=session.require_ghv_pre_external_runtime_flight_recorder_v1,
        ghv_pre_external_runtime_flight_recorder_enabled=(
            ghv_pre_external_runtime_flight_recorder_enabled
        ),
    )
    if not guards_ok:
        record = {
            "schema": "forensic_executable_quantity_override_guard_reject.v1",
            "owner": OWNER,
            "cycle_index": cycle_index,
            "guard_reasons": list(guard_reasons),
            "recorded_at": _utc_now_iso_v1(),
        }
        _atomic_append_jsonl_v1(
            path=Path(session.product_evidence_root) / LEDGER_FILENAME,
            record=record,
        )
        return ForensicExecutableQuantityOverrideResultV1(
            replay=rebound_replay,
            sizing_decision=sizing_decision,
            sizing_outcome=str(getattr(sizing_decision.outcome, "value", sizing_decision.outcome)),
            override_used=False,
            forensic_quantity=None,
            quantity_provenance_mode="",
        )

    real_outcome = str(getattr(sizing_decision.outcome, "value", sizing_decision.outcome))
    real_final = str(sizing_decision.final_quantity)
    if _real_sizing_is_executable_v1(sizing_decision):
        persist_forensic_executable_quantity_evidence_v1(
            session=session,
            cycle_index=cycle_index,
            natural_decision_before_synthetic="",
            real_sizing_outcome=real_outcome,
            real_final_quantity=real_final,
            override_used=False,
            forensic_quantity="",
            quantity_provenance_mode="REAL_SIZING_ALREADY_EXECUTABLE",
            downstream_quantity_consumed=real_final,
            policy_outcome_after_override=real_outcome,
            venue_plan_status_after_override="NOT_REACHED",
            pre_external_reached=False,
            post_count=0,
            external_effect_count=0,
        )
        return ForensicExecutableQuantityOverrideResultV1(
            replay=rebound_replay,
            sizing_decision=sizing_decision,
            sizing_outcome=real_outcome,
            override_used=False,
            forensic_quantity=None,
            quantity_provenance_mode="REAL_SIZING_ALREADY_EXECUTABLE",
        )

    pre = sizing_decision.pre_sizing_risk
    reference_price = pre.reference_price
    risk_distance = pre.stop_or_risk_distance
    forensic_qty, prov_mode = derive_forensic_executable_quantity_v1(
        constraints=constraints,
        reference_price=reference_price,
        candidate_quantity_upper_bound=pre.candidate_quantity_upper_bound,
        explicit_forensic_quantity=session.explicit_forensic_quantity,
    )
    if forensic_qty is None:
        persist_forensic_executable_quantity_evidence_v1(
            session=session,
            cycle_index=cycle_index,
            natural_decision_before_synthetic="",
            real_sizing_outcome=real_outcome,
            real_final_quantity=real_final,
            override_used=False,
            forensic_quantity="",
            quantity_provenance_mode=prov_mode,
            downstream_quantity_consumed="0",
            policy_outcome_after_override=real_outcome,
            venue_plan_status_after_override="NOT_REACHED",
            pre_external_reached=False,
            post_count=0,
            external_effect_count=0,
        )
        return ForensicExecutableQuantityOverrideResultV1(
            replay=rebound_replay,
            sizing_decision=sizing_decision,
            sizing_outcome=real_outcome,
            override_used=False,
            forensic_quantity=None,
            quantity_provenance_mode=prov_mode,
        )

    policy_version = str(sizing_decision.scope_capital_envelope.policy_version)
    prov = sizing_decision.quantity_provenance
    config_digest = str(getattr(live_ctx, "config_digest", "") or "")
    if not config_digest and prov is not None:
        config_digest = str(prov.config_digest or "")
    forensic_decision = _build_forensic_pass_sizing_decision_v1(
        real_decision=sizing_decision,
        constraints=constraints,
        forensic_quantity=forensic_qty,
        reference_price=reference_price,
        risk_distance=risk_distance,
        policy_version=policy_version,
        config_digest=config_digest,
        decision_id=pre.decision_id,
    )
    if forensic_decision is None:
        persist_forensic_executable_quantity_evidence_v1(
            session=session,
            cycle_index=cycle_index,
            natural_decision_before_synthetic="",
            real_sizing_outcome=real_outcome,
            real_final_quantity=real_final,
            override_used=False,
            forensic_quantity=str(forensic_qty),
            quantity_provenance_mode=prov_mode,
            downstream_quantity_consumed="0",
            policy_outcome_after_override=real_outcome,
            venue_plan_status_after_override="NOT_REACHED",
            pre_external_reached=False,
            post_count=0,
            external_effect_count=0,
        )
        return ForensicExecutableQuantityOverrideResultV1(
            replay=rebound_replay,
            sizing_decision=sizing_decision,
            sizing_outcome=real_outcome,
            override_used=False,
            forensic_quantity=forensic_qty,
            quantity_provenance_mode=prov_mode,
        )

    forensic_rebound = _rebound_replay_with_sizing_decision_v1(
        rebound_replay,
        sizing_decision=forensic_decision,
        live_ctx=live_ctx,
    )
    forensic_outcome = str(getattr(forensic_decision.outcome, "value", forensic_decision.outcome))
    persist_forensic_executable_quantity_evidence_v1(
        session=session,
        cycle_index=cycle_index,
        natural_decision_before_synthetic="",
        real_sizing_outcome=real_outcome,
        real_final_quantity=real_final,
        override_used=True,
        forensic_quantity=str(forensic_qty),
        quantity_provenance_mode=prov_mode,
        downstream_quantity_consumed=str(forensic_decision.final_quantity),
        policy_outcome_after_override=forensic_outcome,
        venue_plan_status_after_override="NOT_REACHED",
        pre_external_reached=False,
        post_count=0,
        external_effect_count=0,
    )
    return ForensicExecutableQuantityOverrideResultV1(
        replay=forensic_rebound,
        sizing_decision=forensic_decision,
        sizing_outcome=forensic_outcome,
        override_used=True,
        forensic_quantity=forensic_qty,
        quantity_provenance_mode=prov_mode,
    )


def refresh_forensic_executable_quantity_run_outcome_v1(
    *,
    session: ForensicExecutableQuantityOverrideSessionV1,
    policy_outcome_after_override: str,
    venue_plan_status_after_override: str,
    pre_external_reached: bool,
    post_count: int,
    external_effect_count: int,
) -> None:
    summary_path = Path(session.product_evidence_root) / SUMMARY_FILENAME
    if not summary_path.is_file():
        return
    payload = json.loads(summary_path.read_text(encoding="utf-8"))
    payload["POLICY_OUTCOME_AFTER_OVERRIDE"] = policy_outcome_after_override
    payload["VENUE_PLAN_STATUS_AFTER_OVERRIDE"] = venue_plan_status_after_override
    payload["PRE_EXTERNAL_REACHED"] = pre_external_reached
    payload["POST_COUNT"] = post_count
    payload["EXTERNAL_EFFECT_COUNT"] = external_effect_count
    summary_path.write_text(json.dumps(payload, sort_keys=True, indent=2) + "\n", encoding="utf-8")


def build_forensic_executable_quantity_override_session_v1(
    *,
    enabled: bool,
    explicit_forensic_quantity: str | None,
    product_evidence_root: Path,
    continuous_run_id: str,
    require_ghv_pre_external_runtime_flight_recorder_v1: bool = True,
) -> ForensicExecutableQuantityOverrideSessionV1:
    return ForensicExecutableQuantityOverrideSessionV1(
        enabled=enabled,
        explicit_forensic_quantity=_parse_explicit_quantity_v1(explicit_forensic_quantity),
        product_evidence_root=Path(product_evidence_root),
        continuous_run_id=str(continuous_run_id),
        require_ghv_pre_external_runtime_flight_recorder_v1=(
            require_ghv_pre_external_runtime_flight_recorder_v1
        ),
    )


__all__ = [
    "ForensicExecutableQuantityOverrideResultV1",
    "ForensicExecutableQuantityOverrideSessionV1",
    "LEDGER_FILENAME",
    "OWNER",
    "PROVENANCE_CURRENT_DERIVED_MIN_VENUE",
    "PROVENANCE_EXPLICIT_FORENSIC_INPUT",
    "PROVENANCE_FORENSIC_OVERRIDE",
    "REASON_FORENSIC_EXECUTABLE_QUANTITY_OVERRIDE",
    "SUMMARY_FILENAME",
    "active_forensic_executable_quantity_override_session_v1",
    "bind_forensic_executable_quantity_override_session_v1",
    "build_forensic_executable_quantity_override_session_v1",
    "derive_forensic_executable_quantity_v1",
    "forensic_override_guards_satisfied_v1",
    "maybe_apply_forensic_executable_quantity_override_after_live_29p_v1",
    "persist_forensic_executable_quantity_evidence_v1",
    "refresh_forensic_executable_quantity_run_outcome_v1",
    "reset_forensic_executable_quantity_override_session_v1",
]
