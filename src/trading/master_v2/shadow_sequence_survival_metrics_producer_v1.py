"""Shadow SequenceSurvivalMetrics producer (provisional / non-authority).

DEFINITION_SET=fps_sequence_metric_set.double_play_survival_envelope_v0_fields.v1
PRODUCTIVE_ACTIVATION=false
Does not map SurvivalResultV1. Does not invent missing metrics.
"""

from __future__ import annotations

from typing import Mapping, Optional

from trading.master_v2.fps_sequence_path_survival_ratio_prearm_path_fraction_v1 import (
    FORMULA_ID as PATH_SURVIVAL_FORMULA_ID,
    compute_fps_sequence_path_survival_ratio_prearm_path_fraction_v1,
)
from trading.master_v2.double_play_survival import SequenceSurvivalMetrics

from src.ops.productive_pure_stack_numeric_policy_shadow_campaign_v1.models_v1 import (
    ShadowAvailabilityV1,
    ShadowSequenceMetricsObservationV1,
)
from src.ops.productive_pure_stack_numeric_policy_shadow_campaign_v1.reproducibility_v1 import (
    digest_mapping,
)

DEFINITION_ID = "fps_sequence_metric_set.double_play_survival_envelope_v0_fields.v1"
PRODUCTIVE_ACTIVATION = False
PROVISIONAL = True

_METRIC_KEYS = (
    "path_survival_ratio",
    "early_loss_toxicity",
    "margin_buffer_at_risk_99",
    "sequence_fragility_index",
    "liquidation_near_miss_rate",
    "governance_breach_frequency",
    "chop_switch_survival_score",
)


def produce_shadow_sequence_survival_metrics_v1(
    *,
    path_above_barrier: tuple[bool, ...] | None = None,
    explicit_metrics: Mapping[str, Optional[float]] | None = None,
    event_time_epoch_s: int | None = None,
) -> ShadowSequenceMetricsObservationV1:
    """Assemble shadow metrics. Missing fields remain None → UNAVAILABLE (no defaults)."""
    explicit = dict(explicit_metrics or {})
    digest = digest_mapping(
        {
            "definition_id": DEFINITION_ID,
            "path_above_barrier": None
            if path_above_barrier is None
            else [bool(x) for x in path_above_barrier],
            "explicit_metrics": {k: explicit.get(k) for k in _METRIC_KEYS},
            "event_time_epoch_s": event_time_epoch_s,
            "productive_activation": PRODUCTIVE_ACTIVATION,
        }
    )

    path_obs = compute_fps_sequence_path_survival_ratio_prearm_path_fraction_v1(
        path_above_barrier,
        event_time_epoch_s=event_time_epoch_s,
    )
    values: dict[str, Optional[float]] = {k: explicit.get(k) for k in _METRIC_KEYS}
    if values["path_survival_ratio"] is None and path_obs.status is ShadowAvailabilityV1.AVAILABLE:
        values["path_survival_ratio"] = path_obs.value

    if any(k for k in explicit if k not in _METRIC_KEYS):
        return ShadowSequenceMetricsObservationV1(
            definition_id=DEFINITION_ID,
            status=ShadowAvailabilityV1.REJECTED,
            provisional=PROVISIONAL,
            productive_activation=PRODUCTIVE_ACTIVATION,
            path_survival_ratio=None,
            early_loss_toxicity=None,
            margin_buffer_at_risk_99=None,
            sequence_fragility_index=None,
            liquidation_near_miss_rate=None,
            governance_breach_frequency=None,
            chop_switch_survival_score=None,
            rejection_reason="reject_unknown_metric_keys",
            input_digest=digest,
            notes=("shadow_only", "provisional", PATH_SURVIVAL_FORMULA_ID),
        )

    if all(values[k] is None for k in _METRIC_KEYS):
        return ShadowSequenceMetricsObservationV1(
            definition_id=DEFINITION_ID,
            status=ShadowAvailabilityV1.UNAVAILABLE,
            provisional=PROVISIONAL,
            productive_activation=PRODUCTIVE_ACTIVATION,
            path_survival_ratio=None,
            early_loss_toxicity=None,
            margin_buffer_at_risk_99=None,
            sequence_fragility_index=None,
            liquidation_near_miss_rate=None,
            governance_breach_frequency=None,
            chop_switch_survival_score=None,
            rejection_reason="unavailable_all_metrics_missing",
            input_digest=digest,
            notes=("shadow_only", "provisional", "no_defaults"),
        )

    return ShadowSequenceMetricsObservationV1(
        definition_id=DEFINITION_ID,
        status=ShadowAvailabilityV1.AVAILABLE
        if all(values[k] is not None for k in _METRIC_KEYS)
        else ShadowAvailabilityV1.UNAVAILABLE,
        provisional=PROVISIONAL,
        productive_activation=PRODUCTIVE_ACTIVATION,
        path_survival_ratio=values["path_survival_ratio"],
        early_loss_toxicity=values["early_loss_toxicity"],
        margin_buffer_at_risk_99=values["margin_buffer_at_risk_99"],
        sequence_fragility_index=values["sequence_fragility_index"],
        liquidation_near_miss_rate=values["liquidation_near_miss_rate"],
        governance_breach_frequency=values["governance_breach_frequency"],
        chop_switch_survival_score=values["chop_switch_survival_score"],
        rejection_reason=None
        if all(values[k] is not None for k in _METRIC_KEYS)
        else "unavailable_partial_metrics",
        input_digest=digest,
        notes=(
            "shadow_only",
            "provisional_formula",
            "not_survival_result_v1",
            "not_input_authority",
        ),
    )


def to_sequence_survival_metrics_dto(
    obs: ShadowSequenceMetricsObservationV1,
) -> SequenceSurvivalMetrics:
    """DTO projection for shadow assembly only — never confers authority."""
    return SequenceSurvivalMetrics(
        path_survival_ratio=obs.path_survival_ratio,
        early_loss_toxicity=obs.early_loss_toxicity,
        margin_buffer_at_risk_99=obs.margin_buffer_at_risk_99,
        sequence_fragility_index=obs.sequence_fragility_index,
        liquidation_near_miss_rate=obs.liquidation_near_miss_rate,
        governance_breach_frequency=obs.governance_breach_frequency,
        chop_switch_survival_score=obs.chop_switch_survival_score,
    )
