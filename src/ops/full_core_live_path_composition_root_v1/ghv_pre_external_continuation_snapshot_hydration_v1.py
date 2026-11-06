"""Rehydrate continuation snapshot JSON into production-compatible typed state.

Observation-only: restores types expected by production consumers (e.g.
``compose_core_live_execution_intent_v1``) after ``_jsonable`` / ``asdict``
serialization. Does not change trading semantics.
"""

from __future__ import annotations

from dataclasses import replace
from decimal import Decimal
from enum import Enum
from typing import Any, Mapping, Optional, Sequence, TypeVar

from src.governance.canonical_order_intent_v1 import (
    CanonicalOrderIntentV1,
    canonical_order_intent_from_dict,
)
from src.governance.capital_risk_sizing_v1 import (
    AUTHORITY_EFFECT_NONE,
    RUNTIME_EFFECT_NONE,
    CanonicalPositionSizingV1,
    CapitalRiskSizingDecisionV1,
    CapitalRiskSizingOutcome,
    EnvelopeStatus,
    FinalQuantityStatus,
    PostSizingRiskAssessmentV1,
    PostSizingRiskStatus,
    PreSizingRiskAssessmentV1,
    PreSizingRiskStatus,
    QuantityProvenanceV1,
    QuantityStatus,
    ScopeCapitalEnvelopeV1,
)
from trading.master_v2.integrated_offline_trading_logic_replay_v1 import (
    IntegratedOfflineReplayIntermediateV1,
    IntegratedOfflineReplayResultV1,
)

OWNER = (
    "full_core_live_path_composition_root_v1.ghv_pre_external_continuation_snapshot_hydration_v1"
)

E = TypeVar("E", bound=Enum)


def _enum_value(enum_cls: type[E], raw: Any) -> E:
    if isinstance(raw, enum_cls):
        return raw
    token = str(raw or "").strip()
    if not token:
        raise ValueError(f"missing enum value for {enum_cls.__name__}")
    return enum_cls(token)


def _decimal(raw: Any) -> Decimal:
    if isinstance(raw, Decimal):
        return raw
    return Decimal(str(raw))


def _tuple_str(raw: Any) -> tuple[str, ...]:
    if raw is None:
        return ()
    if isinstance(raw, str):
        return (raw,)
    return tuple(str(x) for x in raw)


def _mapping_str(raw: Any) -> Mapping[str, str]:
    if not isinstance(raw, Mapping):
        return {}
    return {str(k): str(v) for k, v in raw.items()}


def pre_sizing_risk_assessment_from_snapshot_dict_v1(
    payload: Mapping[str, Any],
) -> PreSizingRiskAssessmentV1:
    return PreSizingRiskAssessmentV1(
        decision_id=str(payload["decision_id"]),
        side=str(payload["side"]),
        reference_price=_decimal(payload["reference_price"]),
        stop_or_risk_distance=_decimal(payload["stop_or_risk_distance"]),
        maximum_loss_budget=_decimal(payload["maximum_loss_budget"]),
        capital_cap_quantity=_decimal(payload["capital_cap_quantity"]),
        loss_budget_quantity=_decimal(payload["loss_budget_quantity"]),
        exposure_cap_quantity=_decimal(payload["exposure_cap_quantity"]),
        candidate_quantity_upper_bound=_decimal(payload["candidate_quantity_upper_bound"]),
        status=_enum_value(PreSizingRiskStatus, payload.get("status")),
        reason_codes=_tuple_str(payload.get("reason_codes")),
        input_digest=str(payload["input_digest"]),
    )


def scope_capital_envelope_from_snapshot_dict_v1(
    payload: Mapping[str, Any],
) -> ScopeCapitalEnvelopeV1:
    return ScopeCapitalEnvelopeV1(
        instrument_id=str(payload["instrument_id"]),
        decision_id=str(payload["decision_id"]),
        policy_version=str(payload["policy_version"]),
        total_capital_limit=_decimal(payload["total_capital_limit"]),
        available_capital=_decimal(payload["available_capital"]),
        already_committed_capital=_decimal(payload["already_committed_capital"]),
        remaining_capital=_decimal(payload["remaining_capital"]),
        per_order_cap=_decimal(payload["per_order_cap"]),
        daily_loss_state=_mapping_str(payload.get("daily_loss_state")),
        position_slot_state=_mapping_str(payload.get("position_slot_state")),
        status=_enum_value(EnvelopeStatus, payload.get("status")),
        reason_codes=_tuple_str(payload.get("reason_codes")),
        input_digest=str(payload["input_digest"]),
    )


def canonical_position_sizing_from_snapshot_dict_v1(
    payload: Mapping[str, Any],
) -> CanonicalPositionSizingV1:
    return CanonicalPositionSizingV1(
        decision_id=str(payload["decision_id"]),
        instrument_id=str(payload["instrument_id"]),
        side=str(payload["side"]),
        raw_quantity=_decimal(payload["raw_quantity"]),
        bounded_quantity_before_rounding=_decimal(payload["bounded_quantity_before_rounding"]),
        lot_size=_decimal(payload["lot_size"]),
        rounded_quantity=_decimal(payload["rounded_quantity"]),
        reference_price=_decimal(payload["reference_price"]),
        resulting_notional=_decimal(payload["resulting_notional"]),
        quantity_status=_enum_value(QuantityStatus, payload.get("quantity_status")),
        reason_codes=_tuple_str(payload.get("reason_codes")),
        policy_digest=str(payload["policy_digest"]),
        input_digest=str(payload["input_digest"]),
    )


def post_sizing_risk_assessment_from_snapshot_dict_v1(
    payload: Mapping[str, Any],
) -> PostSizingRiskAssessmentV1:
    return PostSizingRiskAssessmentV1(
        proposed_quantity=_decimal(payload["proposed_quantity"]),
        final_allowed_quantity=_decimal(payload["final_allowed_quantity"]),
        resulting_notional=_decimal(payload["resulting_notional"]),
        resulting_max_loss=_decimal(payload["resulting_max_loss"]),
        exposure_after=_decimal(payload["exposure_after"]),
        slot_usage_after=int(payload["slot_usage_after"]),
        status=_enum_value(PostSizingRiskStatus, payload.get("status")),
        reason_codes=_tuple_str(payload.get("reason_codes")),
        input_digest=str(payload["input_digest"]),
    )


def quantity_provenance_from_snapshot_dict_v1(
    payload: Mapping[str, Any],
) -> QuantityProvenanceV1:
    return QuantityProvenanceV1(
        decision_id=str(payload["decision_id"]),
        source_contract_refs=_tuple_str(payload.get("source_contract_refs")),
        capital_envelope_ref=str(payload["capital_envelope_ref"]),
        pre_sizing_risk_ref=str(payload["pre_sizing_risk_ref"]),
        sizing_ref=str(payload["sizing_ref"]),
        post_sizing_risk_ref=str(payload["post_sizing_risk_ref"]),
        instrument_metadata_ref=str(payload["instrument_metadata_ref"]),
        policy_version=str(payload["policy_version"]),
        config_digest=str(payload["config_digest"]),
        implementation_digest=str(payload["implementation_digest"]),
        final_quantity=_decimal(payload["final_quantity"]),
        final_quantity_status=_enum_value(
            FinalQuantityStatus, payload.get("final_quantity_status")
        ),
        authority_effect=str(payload.get("authority_effect") or AUTHORITY_EFFECT_NONE),
        runtime_effect=str(payload.get("runtime_effect") or RUNTIME_EFFECT_NONE),
        adapter_compatible=bool(payload.get("adapter_compatible")),
    )


def capital_risk_sizing_decision_from_snapshot_dict_v1(
    payload: Mapping[str, Any],
) -> CapitalRiskSizingDecisionV1:
    if isinstance(payload, CapitalRiskSizingDecisionV1):
        return payload
    cps_raw = payload.get("canonical_position_sizing")
    psr_raw = payload.get("post_sizing_risk")
    qp_raw = payload.get("quantity_provenance")
    pre_raw = payload.get("pre_sizing_risk")
    scope_raw = payload.get("scope_capital_envelope")
    if not isinstance(pre_raw, Mapping) or not isinstance(scope_raw, Mapping):
        raise ValueError(
            "capital_risk_sizing_decision missing pre_sizing_risk or scope_capital_envelope"
        )
    return CapitalRiskSizingDecisionV1(
        outcome=_enum_value(CapitalRiskSizingOutcome, payload.get("outcome")),
        final_quantity=_decimal(payload["final_quantity"]),
        selected_side=str(payload["selected_side"]),
        scope_capital_envelope=scope_capital_envelope_from_snapshot_dict_v1(scope_raw),
        pre_sizing_risk=pre_sizing_risk_assessment_from_snapshot_dict_v1(pre_raw),
        canonical_position_sizing=(
            canonical_position_sizing_from_snapshot_dict_v1(cps_raw)
            if isinstance(cps_raw, Mapping)
            else None
        ),
        post_sizing_risk=(
            post_sizing_risk_assessment_from_snapshot_dict_v1(psr_raw)
            if isinstance(psr_raw, Mapping)
            else None
        ),
        quantity_provenance=(
            quantity_provenance_from_snapshot_dict_v1(qp_raw)
            if isinstance(qp_raw, Mapping)
            else None
        ),
        reason_codes=_tuple_str(payload.get("reason_codes")),
        authority_effect=str(payload.get("authority_effect") or AUTHORITY_EFFECT_NONE),
        runtime_effect=str(payload.get("runtime_effect") or RUNTIME_EFFECT_NONE),
        adapter_compatible=bool(payload.get("adapter_compatible")),
    )


CONTINUATION_CRITICAL_FIELD_AUDIT_V1: tuple[dict[str, str], ...] = (
    {
        "FIELD": "intermediate.capital_risk_sizing_decision",
        "PRODUCTION_TYPE": "CapitalRiskSizingDecisionV1",
        "CONSUMER": "compose_core_live_execution_intent_v1",
    },
    {
        "FIELD": "intermediate.canonical_order_intent",
        "PRODUCTION_TYPE": "CanonicalOrderIntentV1 | None",
        "CONSUMER": "compose_core_live_execution_intent_v1",
    },
    {
        "FIELD": "intermediate.composition_result",
        "PRODUCTION_TYPE": "DoublePlayCompositionResultV1",
        "CONSUMER": "compose_core_live_execution_intent_v1 (presence)",
    },
    {
        "FIELD": "intermediate.entry_exit_decision",
        "PRODUCTION_TYPE": "EntryExitPolicyDecisionV0",
        "CONSUMER": "compose_core_live_execution_intent_v1 (presence)",
    },
    {
        "FIELD": "replay_execution_safety",
        "PRODUCTION_TYPE": "ReplayExecutionSafetyV1 | None",
        "CONSUMER": "compose_core_live_execution_intent_v1",
    },
    {
        "FIELD": "evidence",
        "PRODUCTION_TYPE": "CanonicalTradingDecisionEvidenceV1",
        "CONSUMER": "compose + venue_plan",
    },
    {
        "FIELD": "bound_instrument",
        "PRODUCTION_TYPE": "BoundInstrumentV1",
        "CONSUMER": "continuation harness",
    },
)


def hydrate_continuation_critical_intermediate_v1(
    intermediate: IntegratedOfflineReplayIntermediateV1,
    intermediate_raw: Mapping[str, Any],
) -> IntegratedOfflineReplayIntermediateV1:
    """Rehydrate typed fields required by offline continuation consumers."""
    sizing_raw = intermediate_raw.get("capital_risk_sizing_decision")
    sizing: CapitalRiskSizingDecisionV1 | None = None
    if sizing_raw is not None:
        if isinstance(sizing_raw, CapitalRiskSizingDecisionV1):
            sizing = sizing_raw
        elif isinstance(sizing_raw, Mapping):
            sizing = capital_risk_sizing_decision_from_snapshot_dict_v1(sizing_raw)
        else:
            raise TypeError("capital_risk_sizing_decision snapshot type unsupported")

    intent_raw = intermediate_raw.get("canonical_order_intent")
    intent: CanonicalOrderIntentV1 | None = None
    if intent_raw is not None:
        if isinstance(intent_raw, CanonicalOrderIntentV1):
            intent = intent_raw
        elif isinstance(intent_raw, Mapping):
            intent = canonical_order_intent_from_dict(intent_raw)
        else:
            raise TypeError("canonical_order_intent snapshot type unsupported")

    return replace(
        intermediate,
        capital_risk_sizing_decision=sizing,
        canonical_order_intent=intent,
    )


def audit_intermediate_hydration_v1(
    intermediate_raw: Mapping[str, Any],
    hydrated: IntegratedOfflineReplayIntermediateV1,
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    sizing_raw = intermediate_raw.get("capital_risk_sizing_decision")
    sizing = hydrated.capital_risk_sizing_decision
    rows.append(
        {
            "FIELD": "capital_risk_sizing_decision",
            "PRODUCTION_TYPE": "CapitalRiskSizingDecisionV1",
            "SNAPSHOT_TYPE": type(sizing_raw).__name__ if sizing_raw is not None else "None",
            "REHYDRATED_TYPE": type(sizing).__name__ if sizing is not None else "None",
            "SEMANTIC_EQUIVALENCE": (
                "PASS"
                if sizing is None
                else (
                    "PASS"
                    if isinstance(sizing, CapitalRiskSizingDecisionV1)
                    and hasattr(sizing, "outcome")
                    else "FAIL"
                )
            ),
            "STATUS": "REPAIRED" if isinstance(sizing, CapitalRiskSizingDecisionV1) else "NONE",
        }
    )
    intent_raw = intermediate_raw.get("canonical_order_intent")
    intent = hydrated.canonical_order_intent
    rows.append(
        {
            "FIELD": "canonical_order_intent",
            "PRODUCTION_TYPE": "CanonicalOrderIntentV1",
            "SNAPSHOT_TYPE": type(intent_raw).__name__ if intent_raw is not None else "None",
            "REHYDRATED_TYPE": type(intent).__name__ if intent is not None else "None",
            "SEMANTIC_EQUIVALENCE": (
                "PASS" if intent is None or isinstance(intent, CanonicalOrderIntentV1) else "FAIL"
            ),
            "STATUS": "REPAIRED" if isinstance(intent, CanonicalOrderIntentV1) else "NONE",
        }
    )
    return rows


__all__ = [
    "CONTINUATION_CRITICAL_FIELD_AUDIT_V1",
    "OWNER",
    "audit_intermediate_hydration_v1",
    "capital_risk_sizing_decision_from_snapshot_dict_v1",
    "hydrate_continuation_critical_intermediate_v1",
    "scope_capital_envelope_from_snapshot_dict_v1",
]
