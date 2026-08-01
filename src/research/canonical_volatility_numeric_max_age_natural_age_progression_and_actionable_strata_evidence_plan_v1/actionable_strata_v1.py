"""Actionable alpha strata projection — transport only, no second authority."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping, Optional, Sequence

from research.canonical_volatility_numeric_max_age_natural_age_progression_and_actionable_strata_evidence_plan_v1.constants_v1 import (
    RESEARCH_AGE_GRID_SECONDS,
)
from research.canonical_volatility_numeric_max_age_natural_age_progression_and_actionable_strata_evidence_plan_v1.lifecycle_contract_v1 import (
    NaturalAgeLifecycleObservationV1,
)


def assign_age_bucket_v1(
    age_seconds: Optional[float],
    *,
    grid_seconds: Sequence[int] = RESEARCH_AGE_GRID_SECONDS,
) -> str:
    if age_seconds is None:
        return "AGE_NOT_EVALUABLE"
    age = float(age_seconds)
    if age < 0:
        return "AGE_NEGATIVE_NOT_EVALUABLE"
    for boundary in sorted(int(x) for x in grid_seconds):
        if age <= float(boundary):
            return f"AGE_LE_{boundary}_S"
    return f"AGE_GT_{max(int(x) for x in grid_seconds)}_S"


def _as_bool(value: Any) -> Optional[bool]:
    if value is None:
        return None
    if isinstance(value, bool):
        return value
    return None


def _text(value: Any, default: str = "") -> str:
    if value is None:
        return default
    text = str(value).strip()
    return text if text else default


@dataclass(frozen=True)
class ActionableAlphaStrataEvidenceV1:
    """Strata fields projected from existing productive outputs + lifecycle."""

    age_bucket: str
    estimate_reused: bool
    reuse_count: int
    distinct_observations_since_recompute: int
    market_regime_state: str
    directional_bull_state: str
    directional_bear_state: str
    composition_outcome: str
    selected_side: str
    decision_outcome: str
    entry_opportunity: bool
    position_state: str
    trading_permission_state: str
    data_trust_state: str
    safety_state: str
    risk_action_available: bool
    exit_action_available: bool
    reconciliation_action_available: bool
    already_blocked_for_non_age_reason: bool
    second_decision_authority: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "age_bucket": self.age_bucket,
            "already_blocked_for_non_age_reason": self.already_blocked_for_non_age_reason,
            "composition_outcome": self.composition_outcome,
            "data_trust_state": self.data_trust_state,
            "decision_outcome": self.decision_outcome,
            "directional_bear_state": self.directional_bear_state,
            "directional_bull_state": self.directional_bull_state,
            "distinct_observations_since_recompute": self.distinct_observations_since_recompute,
            "entry_opportunity": self.entry_opportunity,
            "estimate_reused": self.estimate_reused,
            "exit_action_available": self.exit_action_available,
            "market_regime_state": self.market_regime_state,
            "position_state": self.position_state,
            "reconciliation_action_available": self.reconciliation_action_available,
            "reuse_count": self.reuse_count,
            "risk_action_available": self.risk_action_available,
            "safety_state": self.safety_state,
            "second_decision_authority": self.second_decision_authority,
            "selected_side": self.selected_side,
            "trading_permission_state": self.trading_permission_state,
        }


def project_actionable_alpha_strata_v1(
    *,
    productive_cycle: Mapping[str, Any] | None = None,
    productive_record: Mapping[str, Any] | None = None,
    lifecycle_observation: NaturalAgeLifecycleObservationV1 | Mapping[str, Any] | None = None,
) -> ActionableAlphaStrataEvidenceV1:
    """Project strata exclusively from existing productive / lifecycle outputs."""
    cycle = dict(productive_cycle or {})
    record = dict(productive_record or {})
    if isinstance(lifecycle_observation, NaturalAgeLifecycleObservationV1):
        life = lifecycle_observation.to_dict()
    else:
        life = dict(lifecycle_observation or {})

    age = life.get("age_seconds")
    if age is None:
        age = record.get("age_seconds", record.get("estimate_age_seconds"))
    age_bucket = assign_age_bucket_v1(None if age is None else float(age))

    estimate_reused = bool(life.get("estimate_reused", record.get("estimate_reused", False)))
    reuse_count = int(life.get("reuse_count", record.get("reuse_count", 0)) or 0)
    distinct_since = int(
        life.get(
            "distinct_observations_since_recompute",
            record.get("distinct_observations_since_recompute", 0),
        )
        or 0
    )

    feature_regime = dict(cycle.get("feature_regime") or {})
    market_regime = _text(
        record.get("regime_label")
        or feature_regime.get("regime_label")
        or cycle.get("regime_id")
        or "UNKNOWN"
    )

    bull = dict(cycle.get("bull_state") or cycle.get("directional_bull") or {})
    bear = dict(cycle.get("bear_state") or cycle.get("directional_bear") or {})
    composition = dict(cycle.get("composition_outcome") or cycle.get("double_play") or {})

    selected_side = _text(
        record.get("selected_side") or cycle.get("selected_side") or "none",
        default="none",
    ).lower()
    decision_outcome = _text(
        record.get("decision_outcome") or cycle.get("decision_outcome") or "unknown",
        default="unknown",
    ).lower()

    entry_opportunity = decision_outcome == "entry" and selected_side in {
        "long",
        "short",
        "both",
        "both_confirmed",
    }

    already_blocked = decision_outcome in {"blocked", "block"} or selected_side in {
        "none",
        "no_selection",
        "",
    }

    # Preserve availability flags from productive outputs when present; default
    # fail-open for exit/risk/safety observability transport (not enforcement).
    risk_available = _as_bool(cycle.get("risk_action_available"))
    if risk_available is None:
        risk_available = _as_bool(record.get("risk_action_available"))
    if risk_available is None:
        risk_available = True

    exit_available = _as_bool(cycle.get("exit_action_available"))
    if exit_available is None:
        exit_available = _as_bool(record.get("exit_path_preservation"))
    if exit_available is None:
        exit_available = True

    recon_available = _as_bool(cycle.get("reconciliation_action_available"))
    if recon_available is None:
        recon_available = _as_bool(record.get("reconciliation_action_available"))
    if recon_available is None:
        recon_available = True

    return ActionableAlphaStrataEvidenceV1(
        age_bucket=age_bucket,
        estimate_reused=estimate_reused,
        reuse_count=reuse_count,
        distinct_observations_since_recompute=distinct_since,
        market_regime_state=market_regime,
        directional_bull_state=_text(
            bull.get("state") or cycle.get("directional_bull_state") or "UNKNOWN"
        ),
        directional_bear_state=_text(
            bear.get("state") or cycle.get("directional_bear_state") or "UNKNOWN"
        ),
        composition_outcome=_text(
            composition.get("outcome")
            or cycle.get("composition_outcome")
            or record.get("composition_outcome")
            or "UNKNOWN"
        ),
        selected_side=selected_side,
        decision_outcome=decision_outcome,
        entry_opportunity=bool(entry_opportunity),
        position_state=_text(cycle.get("position_state") or record.get("position_state") or "FLAT"),
        trading_permission_state=_text(
            cycle.get("trading_permission_state")
            or record.get("trading_permission_state")
            or "UNKNOWN"
        ),
        data_trust_state=_text(
            record.get("data_trust_state") or cycle.get("data_trust_state") or "UNKNOWN"
        ),
        safety_state=_text(cycle.get("safety_state") or record.get("safety_state") or "UNKNOWN"),
        risk_action_available=bool(risk_available),
        exit_action_available=bool(exit_available),
        reconciliation_action_available=bool(recon_available),
        already_blocked_for_non_age_reason=bool(already_blocked),
        second_decision_authority=False,
    )
