"""Fail-safe passive accumulation at the existing bridge evidence seam."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping

from research.canonical_volatility_max_age_productive_research_evidence_accumulation_v1.runtime_v1 import (
    ProductiveEvidenceAccumulationStateV1,
    accumulate_productive_research_evidence_from_cycle_v1,
)
from research.m9_s1_durable_market_session_evidence_accumulation_v1.constants_v1 import (
    COUNTERFACTUAL_ONLY,
    ENFORCEMENT_ENABLED,
    EXTERNAL_EFFECT_AUTHORIZED,
    NUMERIC_MAX_AGE_DECIDED,
    OBSERVATION_ONLY,
    PRODUCTIVE_PARAMETER_MUTATED,
)
from research.m9_s1_durable_market_session_evidence_accumulation_v1.models_v1 import (
    ObservationSourceClassV1,
)
from research.m9_s1_durable_market_session_evidence_accumulation_v1.observation_v1 import (
    build_observation_from_bridge_cycle_v1,
)
from research.m9_s1_durable_market_session_evidence_accumulation_v1.observation_ledger_v1 import (
    append_m9_s1_observation_v1,
)


def passive_accumulate_from_bridge_cycle_v1(
    cycle: Mapping[str, Any],
    *,
    state: ProductiveEvidenceAccumulationStateV1,
    source_class: str | ObservationSourceClassV1,
    m9_s1_observation_ledger_path: Path | None = None,
    project_to_join_ledger: bool = True,
) -> dict[str, Any]:
    """Delegate to productive accumulation; M9-S1 observation append never mutates trading."""
    accumulation = accumulate_productive_research_evidence_from_cycle_v1(
        cycle,
        state=state,
        project_to_join_ledger=project_to_join_ledger,
    )
    out = dict(accumulation)
    out["m9_s1_observation_only"] = OBSERVATION_ONLY
    out["m9_s1_counterfactual_only"] = COUNTERFACTUAL_ONLY
    out["numeric_max_age_decided"] = NUMERIC_MAX_AGE_DECIDED
    out["enforcement_enabled"] = ENFORCEMENT_ENABLED
    out["productive_parameter_mutated"] = PRODUCTIVE_PARAMETER_MUTATED
    out["external_effect_authorized"] = EXTERNAL_EFFECT_AUTHORIZED
    out["trading_behavior_mutated"] = False
    out["presence_gate_semantics_unchanged"] = True
    out["alpha_gate_semantics_unchanged"] = True

    if m9_s1_observation_ledger_path is None:
        out["m9_s1_observation_append"] = {"action": "SKIPPED_NO_LEDGER_PATH"}
        return out

    try:
        observation = build_observation_from_bridge_cycle_v1(
            cycle,
            source_class=source_class,
            repository_sha=state.repository_sha,
            accumulation_result=accumulation,
        )
        append_result = append_m9_s1_observation_v1(
            ledger_path=m9_s1_observation_ledger_path,
            observation=observation,
        )
        out["m9_s1_observation_append"] = append_result
        out["m9_s1_observation"] = observation.to_dict()
    except Exception as exc:  # noqa: BLE001 — passive boundary must not propagate
        out["m9_s1_observation_append"] = {
            "action": "OBSERVATION_LEDGER_WRITE_FAILURE",
            "error": str(exc),
            "error_type": type(exc).__name__,
        }
    return out
