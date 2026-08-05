"""Shadow Survival Envelope assembler — observation bundle only.

PRODUCTIVE_ACTIVATION=false
Does not evaluate productive decisions as authority.
Does not map SurvivalResultV1 / SuitabilityResultV1.
Does not invent StateSwitchSurvivalLimits thresholds.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping, Optional

from trading.master_v2.double_play_survival import (
    ArithmeticFingerprint,
    DoublePlaySurvivalEnvelope,
    LayerArithmeticStatus,
    SequenceSurvivalMetrics,
)
from src.ops.productive_pure_stack_numeric_policy_shadow_campaign_v1.shadow_sequence_survival_metrics_producer_v1 import (
    produce_shadow_sequence_survival_metrics_v1,
    to_sequence_survival_metrics_dto,
)

from src.ops.productive_pure_stack_numeric_policy_shadow_campaign_v1.models_v1 import (
    ShadowAvailabilityV1,
)
from src.ops.productive_pure_stack_numeric_policy_shadow_campaign_v1.reproducibility_v1 import (
    digest_mapping,
)

PRODUCTIVE_ACTIVATION = False
ASSEMBLER_ID = "shadow_survival_envelope_assembler.v1"


@dataclass(frozen=True)
class ShadowSurvivalEnvelopeAssemblyV1:
    assembler_id: str
    status: ShadowAvailabilityV1
    provisional: bool
    productive_activation: bool
    envelope: Optional[DoublePlaySurvivalEnvelope]
    rejection_reason: Optional[str]
    input_digest: str
    notes: tuple[str, ...]


def _layer_from_mapping(raw: Mapping[str, Any] | None) -> Optional[LayerArithmeticStatus]:
    if raw is None:
        return None
    required = (
        "max_effective_leverage",
        "min_liquidation_buffer",
        "fee_breakeven_bps",
        "expected_adverse_fill_loss",
        "funding_cost_profile",
        "is_perpetual",
    )
    if any(k not in raw or raw[k] is None for k in required):
        return None
    return LayerArithmeticStatus(
        max_effective_leverage=float(raw["max_effective_leverage"]),
        min_liquidation_buffer=float(raw["min_liquidation_buffer"]),
        fee_breakeven_bps=float(raw["fee_breakeven_bps"]),
        expected_adverse_fill_loss=float(raw["expected_adverse_fill_loss"]),
        funding_cost_profile=str(raw["funding_cost_profile"]),
        is_perpetual=bool(raw["is_perpetual"]),
    )


def assemble_shadow_survival_envelope_v1(
    *,
    fingerprint: Optional[ArithmeticFingerprint] = None,
    long_layer: Optional[Mapping[str, Any]] = None,
    short_layer: Optional[Mapping[str, Any]] = None,
    path_above_barrier: tuple[bool, ...] | None = None,
    sequence_metric_inputs: Mapping[str, Optional[float]] | None = None,
    # Explicitly rejected: limits are Owner Stage-2 tokens and must remain unset here.
    limits: Any = None,
) -> ShadowSurvivalEnvelopeAssemblyV1:
    digest = digest_mapping(
        {
            "assembler_id": ASSEMBLER_ID,
            "fingerprint": None if fingerprint is None else fingerprint.__dict__,
            "long_layer": None if long_layer is None else dict(long_layer),
            "short_layer": None if short_layer is None else dict(short_layer),
            "path_above_barrier": None
            if path_above_barrier is None
            else [bool(x) for x in path_above_barrier],
            "sequence_metric_inputs": dict(sequence_metric_inputs or {}),
            "limits_provided": limits is not None,
            "productive_activation": PRODUCTIVE_ACTIVATION,
        }
    )

    if limits is not None:
        return ShadowSurvivalEnvelopeAssemblyV1(
            assembler_id=ASSEMBLER_ID,
            status=ShadowAvailabilityV1.REJECTED,
            provisional=True,
            productive_activation=PRODUCTIVE_ACTIVATION,
            envelope=None,
            rejection_reason="reject_shadow_assembler_must_not_bind_survival_limits",
            input_digest=digest,
            notes=("shadow_only", "no_productive_limits", "no_numeric_owner_values"),
        )

    seq_obs = produce_shadow_sequence_survival_metrics_v1(
        path_above_barrier=path_above_barrier,
        explicit_metrics=sequence_metric_inputs,
    )
    long_dto = _layer_from_mapping(long_layer)
    short_dto = _layer_from_mapping(short_layer)

    if fingerprint is None or long_dto is None or short_dto is None:
        return ShadowSurvivalEnvelopeAssemblyV1(
            assembler_id=ASSEMBLER_ID,
            status=ShadowAvailabilityV1.UNAVAILABLE,
            provisional=True,
            productive_activation=PRODUCTIVE_ACTIVATION,
            envelope=None,
            rejection_reason="unavailable_incomplete_arithmetic_or_fingerprint",
            input_digest=digest,
            notes=("shadow_only", "provisional", "not_survival_result_v1"),
        )

    # Envelope DTO without limits: construct is intentionally incomplete for evaluate_*.
    # We expose sequence metrics DTO for evidence; envelope field remains None unless
    # callers only need the observation bundle.
    _ = to_sequence_survival_metrics_dto(seq_obs)
    _ = SequenceSurvivalMetrics  # typing anchor for DTO identity

    return ShadowSurvivalEnvelopeAssemblyV1(
        assembler_id=ASSEMBLER_ID,
        status=ShadowAvailabilityV1.AVAILABLE
        if seq_obs.status is ShadowAvailabilityV1.AVAILABLE
        else ShadowAvailabilityV1.UNAVAILABLE,
        provisional=True,
        productive_activation=PRODUCTIVE_ACTIVATION,
        envelope=None,
        rejection_reason=None
        if seq_obs.status is ShadowAvailabilityV1.AVAILABLE
        else (seq_obs.rejection_reason or "unavailable_sequence_metrics"),
        input_digest=digest,
        notes=(
            "shadow_only",
            "provisional_assembler",
            "limits_intentionally_unbound",
            "not_input_authority",
            f"sequence_status={seq_obs.status.value}",
        ),
    )
