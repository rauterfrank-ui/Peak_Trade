"""Diagnostic-only distance-to-actionability capture (no threshold mutation)."""

from __future__ import annotations

from typing import Any, Mapping, Optional

from src.ops.phase_9_2_productive_decision_graph_actionability_forensic_telemetry_v1.models_v1 import (
    DistanceToActionabilityV1,
    optional_float_v1,
)


def capture_distance_to_actionability_v1(
    *,
    confirmation_epochs_required: int | None,
    confirmation_epochs_current: int | None,
    observe_threshold: float | None,
    candidate_threshold: float | None,
    confirm_threshold: float | None,
    actual_directional_measure: float | None,
    scope_boundary: float | None,
    current_price: float | None,
    composition_required_conditions: int | None,
    composition_satisfied_conditions: int | None,
    risk_headroom: float | None,
    safety_state: str | None,
) -> DistanceToActionabilityV1:
    missing: list[str] = []

    def req(name: str, value: Any) -> Any:
        if value is None:
            missing.append(name)
        return value

    epochs_req = req("confirmation_epochs_required", confirmation_epochs_required)
    epochs_cur = req("confirmation_epochs_current", confirmation_epochs_current)
    remaining = None
    if epochs_req is not None and epochs_cur is not None:
        remaining = max(0, int(epochs_req) - int(epochs_cur))
    else:
        missing.append("confirmation_epochs_remaining")

    obs_thr = optional_float_v1(observe_threshold)
    cand_thr = optional_float_v1(candidate_threshold)
    conf_thr = optional_float_v1(confirm_threshold)
    measure = optional_float_v1(actual_directional_measure)
    if obs_thr is None:
        missing.append("observe_threshold")
    if cand_thr is None:
        missing.append("candidate_threshold")
    if conf_thr is None:
        missing.append("confirm_threshold")
    if measure is None:
        missing.append("actual_directional_measure")

    dist_cand = None
    dist_conf = None
    if measure is not None and cand_thr is not None:
        dist_cand = float(cand_thr) - float(measure)
    else:
        missing.append("distance_to_candidate")
    if measure is not None and conf_thr is not None:
        dist_conf = float(conf_thr) - float(measure)
    else:
        missing.append("distance_to_confirm")

    scope_b = optional_float_v1(scope_boundary)
    price = optional_float_v1(current_price)
    dist_scope = None
    if scope_b is not None and price is not None:
        dist_scope = abs(float(scope_b) - float(price))
    else:
        missing.append("distance_to_scope_transition")
        if scope_b is None:
            missing.append("scope_boundary")
        if price is None:
            missing.append("current_price")

    comp_req = composition_required_conditions
    comp_sat = composition_satisfied_conditions
    comp_miss = None
    if comp_req is None:
        missing.append("composition_required_conditions")
    if comp_sat is None:
        missing.append("composition_satisfied_conditions")
    if comp_req is not None and comp_sat is not None:
        comp_miss = max(0, int(comp_req) - int(comp_sat))
    else:
        missing.append("composition_missing_conditions")

    headroom = optional_float_v1(risk_headroom)
    if headroom is None:
        missing.append("risk_headroom")
    if safety_state is None:
        missing.append("safety_state")

    # Deduplicate missing while preserving order.
    seen: set[str] = set()
    uniq_missing: list[str] = []
    for m in missing:
        if m in seen:
            continue
        seen.add(m)
        uniq_missing.append(m)

    return DistanceToActionabilityV1(
        confirmation_epochs_current=None if epochs_cur is None else int(epochs_cur),
        confirmation_epochs_required=None if epochs_req is None else int(epochs_req),
        confirmation_epochs_remaining=remaining,
        observe_threshold=obs_thr,
        candidate_threshold=cand_thr,
        confirm_threshold=conf_thr,
        actual_directional_measure=measure,
        distance_to_candidate=dist_cand,
        distance_to_confirm=dist_conf,
        scope_boundary=scope_b,
        current_price=price,
        distance_to_scope_transition=dist_scope,
        composition_required_conditions=None if comp_req is None else int(comp_req),
        composition_satisfied_conditions=None if comp_sat is None else int(comp_sat),
        composition_missing_conditions=comp_miss,
        risk_headroom=headroom,
        safety_state=safety_state,
        missing_fields=tuple(uniq_missing),
    )


def aggregate_distance_stats_v1(records: list[Mapping[str, Any]]) -> dict[str, Any]:
    if not records:
        return {
            "sample_count": 0,
            "fields_observed": {},
            "diagnostic_only": True,
        }
    field_presence: dict[str, int] = {}
    for rec in records:
        for key, value in rec.items():
            if key in {"missing_fields", "diagnostic_only"}:
                continue
            if value is not None:
                field_presence[key] = field_presence.get(key, 0) + 1
    return {
        "sample_count": len(records),
        "fields_observed": field_presence,
        "diagnostic_only": True,
        "no_threshold_recommendation_in_runtime": True,
    }
