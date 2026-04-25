# src/trading/master_v2/double_play_survival.py
"""
Pure Double Play Survival Envelope model (docs-only target semantics).

Encodes arithmetic completeness, sequence metrics, and fail-closed evaluation per
docs/ops/specs/MASTER_V2_DOUBLE_PLAY_ARITHMETIC_SEQUENCE_SURVIVAL_CONTRACT_V0.md.
No I/O, no exchange, no execution, no risk wiring.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Optional, Tuple

DOUBLE_PLAY_SURVIVAL_LAYER_VERSION = "v0"


class SurvivalBlockReason(str, Enum):
    """Why pre-authorization is blocked (model status only, non-authority)."""

    INCOMPLETE_FINGERPRINT = "incomplete_fingerprint"
    MISSING_FUNDING_FOR_PERP = "missing_funding_for_perpetual"
    MISSING_LIQUIDATION_MODEL = "missing_liquidation_model"
    INCOMPLETE_SEQUENCE_METRICS = "incomplete_sequence_metrics"
    PATH_SURVIVAL_TOO_LOW = "path_survival_too_low"
    EARLY_LOSS_TOO_HIGH = "early_loss_toxicity_too_high"
    MARGIN_BUFFER_AT_RISK_TOO_LOW = "margin_buffer_at_risk_99_too_low"
    SEQUENCE_FRAGILITY_TOO_HIGH = "sequence_fragility_too_high"
    LIQUIDATION_NEAR_MISS_TOO_HIGH = "liquidation_near_miss_too_high"
    GOVERNANCE_BREACH_TOO_HIGH = "governance_breach_frequency_too_high"
    CHOP_SWITCH_SURVIVAL_TOO_LOW = "chop_switch_survival_too_low"
    LONG_LEVERAGE_TOO_HIGH = "long_leverage_too_high"
    SHORT_LEVERAGE_TOO_HIGH = "short_leverage_too_high"
    LONG_LIQUIDATION_BUFFER_TOO_LOW = "long_liquidation_buffer_too_low"
    SHORT_LIQUIDATION_BUFFER_TOO_LOW = "short_liquidation_buffer_too_low"
    LONG_ADVERSE_FILL_LOSS_TOO_HIGH = "long_adverse_fill_loss_too_high"
    SHORT_ADVERSE_FILL_LOSS_TOO_HIGH = "short_adverse_fill_loss_too_high"


class SurvivalEnvelopeStatus(str, Enum):
    """Coarse result of ``evaluate_survival_envelope``."""

    OK = "ok"
    BLOCKED = "blocked"


@dataclass(frozen=True)
class ArithmeticFingerprint:
    """Component completeness for the futures Arithmetic Kernel (contract §6)."""

    contract_spec_complete: bool = False
    fee_model_complete: bool = False
    slippage_model_complete: bool = False
    funding_model_complete: bool = False
    margin_model_complete: bool = False
    liquidation_model_complete: bool = False
    rounding_model_complete: bool = False


@dataclass(frozen=True)
class LayerArithmeticStatus:
    """Per-side arithmetic fingerprint numbers (long/bull or short/bear)."""

    max_effective_leverage: float
    min_liquidation_buffer: float
    fee_breakeven_bps: float
    expected_adverse_fill_loss: float
    funding_cost_profile: str
    is_perpetual: bool


@dataclass(frozen=True)
class SequenceSurvivalMetrics:
    """
    Path / sequence survival inputs (all optional: ``None`` = missing for fail-closed).
    """

    path_survival_ratio: Optional[float] = None
    early_loss_toxicity: Optional[float] = None
    margin_buffer_at_risk_99: Optional[float] = None
    sequence_fragility_index: Optional[float] = None
    liquidation_near_miss_rate: Optional[float] = None
    governance_breach_frequency: Optional[float] = None
    chop_switch_survival_score: Optional[float] = None


@dataclass(frozen=True)
class StateSwitchSurvivalLimits:
    """
    Pre-arm thresholds. ``live_authorization`` must not grant Live; evaluation
    still returns ``live_authorization`` false on the decision.
    """

    min_path_survival_ratio: float
    max_early_loss_toxicity: float
    min_margin_buffer_at_risk_99: float
    max_sequence_fragility_index: float
    max_liquidation_near_miss_rate: float
    max_governance_breach_frequency: float
    min_chop_switch_survival_score: float
    max_effective_leverage: float
    min_liquidation_buffer: float
    max_adverse_fill_loss: float
    live_authorization: bool = False


@dataclass(frozen=True)
class DoublePlaySurvivalEnvelope:
    """Bundle passed to :func:`evaluate_survival_envelope`."""

    fingerprint: ArithmeticFingerprint
    long_layer: LayerArithmeticStatus
    short_layer: LayerArithmeticStatus
    sequence: SequenceSurvivalMetrics
    limits: StateSwitchSurvivalLimits


@dataclass(frozen=True)
class SurvivalEnvelopeDecision:
    """
    Outcome: ``pre_authorization_eligible`` is model-level status only, not execution
    or session permission. ``live_authorization`` is always false.
    """

    status: SurvivalEnvelopeStatus
    pre_authorization_eligible: bool
    block_reasons: Tuple[SurvivalBlockReason, ...]
    live_authorization: bool = False


def core_fingerprint_complete(fp: ArithmeticFingerprint) -> bool:
    """Contract, fee, slippage, margin, rounding (funding/liquidation checked separately)."""

    return all(
        (
            fp.contract_spec_complete,
            fp.fee_model_complete,
            fp.slippage_model_complete,
            fp.margin_model_complete,
            fp.rounding_model_complete,
        )
    )


def arithmetic_complete(fp: ArithmeticFingerprint) -> bool:
    """All seven fields true — used for a fully 'green' fingerprint (e.g. test 15)."""

    return (
        core_fingerprint_complete(fp)
        and fp.funding_model_complete
        and fp.liquidation_model_complete
    )


def layer_arithmetic_complete(
    long_layer: LayerArithmeticStatus,
    short_layer: LayerArithmeticStatus,
) -> bool:
    """Both layers present with finite numeric fields (structural sanity)."""
    for layer in (long_layer, short_layer):
        for x in (
            layer.max_effective_leverage,
            layer.min_liquidation_buffer,
            layer.fee_breakeven_bps,
            layer.expected_adverse_fill_loss,
        ):
            if x != x:  # NaN
                return False
    return True


def sequence_metrics_complete(seq: SequenceSurvivalMetrics) -> bool:
    return all(
        (
            seq.path_survival_ratio is not None,
            seq.early_loss_toxicity is not None,
            seq.margin_buffer_at_risk_99 is not None,
            seq.sequence_fragility_index is not None,
            seq.liquidation_near_miss_rate is not None,
            seq.governance_breach_frequency is not None,
            seq.chop_switch_survival_score is not None,
        )
    )


def evaluate_survival_envelope(
    envelope: DoublePlaySurvivalEnvelope,
) -> SurvivalEnvelopeDecision:
    """
    Fail-closed evaluation. Never authorizes live; never returns live_authorization
    on the decision (always ``False``) even if ``limits.live_authorization`` is true.
    """
    r: list[SurvivalBlockReason] = []
    fp = envelope.fingerprint
    lo = envelope.long_layer
    sh = envelope.short_layer
    seq = envelope.sequence
    lim = envelope.limits

    if (lo.is_perpetual or sh.is_perpetual) and not fp.funding_model_complete:
        r.append(SurvivalBlockReason.MISSING_FUNDING_FOR_PERP)
    if not fp.liquidation_model_complete:
        r.append(SurvivalBlockReason.MISSING_LIQUIDATION_MODEL)
    if not core_fingerprint_complete(fp):
        r.append(SurvivalBlockReason.INCOMPLETE_FINGERPRINT)
    if not sequence_metrics_complete(seq):
        r.append(SurvivalBlockReason.INCOMPLETE_SEQUENCE_METRICS)

    if r:
        return SurvivalEnvelopeDecision(
            status=SurvivalEnvelopeStatus.BLOCKED,
            pre_authorization_eligible=False,
            block_reasons=tuple(r),
            live_authorization=False,
        )

    # Sequence threshold checks (all metrics known)
    assert seq.path_survival_ratio is not None
    if seq.path_survival_ratio < lim.min_path_survival_ratio:
        r.append(SurvivalBlockReason.PATH_SURVIVAL_TOO_LOW)
    assert seq.early_loss_toxicity is not None
    if seq.early_loss_toxicity > lim.max_early_loss_toxicity:
        r.append(SurvivalBlockReason.EARLY_LOSS_TOO_HIGH)
    assert seq.margin_buffer_at_risk_99 is not None
    if seq.margin_buffer_at_risk_99 < lim.min_margin_buffer_at_risk_99:
        r.append(SurvivalBlockReason.MARGIN_BUFFER_AT_RISK_TOO_LOW)
    assert seq.sequence_fragility_index is not None
    if seq.sequence_fragility_index > lim.max_sequence_fragility_index:
        r.append(SurvivalBlockReason.SEQUENCE_FRAGILITY_TOO_HIGH)
    assert seq.liquidation_near_miss_rate is not None
    if seq.liquidation_near_miss_rate > lim.max_liquidation_near_miss_rate:
        r.append(SurvivalBlockReason.LIQUIDATION_NEAR_MISS_TOO_HIGH)
    assert seq.governance_breach_frequency is not None
    if seq.governance_breach_frequency > lim.max_governance_breach_frequency:
        r.append(SurvivalBlockReason.GOVERNANCE_BREACH_TOO_HIGH)
    assert seq.chop_switch_survival_score is not None
    if seq.chop_switch_survival_score < lim.min_chop_switch_survival_score:
        r.append(SurvivalBlockReason.CHOP_SWITCH_SURVIVAL_TOO_LOW)

    # Layer limits
    if lo.max_effective_leverage > lim.max_effective_leverage:
        r.append(SurvivalBlockReason.LONG_LEVERAGE_TOO_HIGH)
    if sh.max_effective_leverage > lim.max_effective_leverage:
        r.append(SurvivalBlockReason.SHORT_LEVERAGE_TOO_HIGH)
    if lo.min_liquidation_buffer < lim.min_liquidation_buffer:
        r.append(SurvivalBlockReason.LONG_LIQUIDATION_BUFFER_TOO_LOW)
    if sh.min_liquidation_buffer < lim.min_liquidation_buffer:
        r.append(SurvivalBlockReason.SHORT_LIQUIDATION_BUFFER_TOO_LOW)
    if lo.expected_adverse_fill_loss > lim.max_adverse_fill_loss:
        r.append(SurvivalBlockReason.LONG_ADVERSE_FILL_LOSS_TOO_HIGH)
    if sh.expected_adverse_fill_loss > lim.max_adverse_fill_loss:
        r.append(SurvivalBlockReason.SHORT_ADVERSE_FILL_LOSS_TOO_HIGH)

    if r:
        return SurvivalEnvelopeDecision(
            status=SurvivalEnvelopeStatus.BLOCKED,
            pre_authorization_eligible=False,
            block_reasons=tuple(r),
            live_authorization=False,
        )

    return SurvivalEnvelopeDecision(
        status=SurvivalEnvelopeStatus.OK,
        pre_authorization_eligible=True,
        block_reasons=(),
        live_authorization=False,
    )
