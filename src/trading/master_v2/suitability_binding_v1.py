# src/trading/master_v2/suitability_binding_v1.py
"""
Pure Suitability Binding v1: offline strategy suitability contract for STEP 29F Rank-2.

Consumes immutable DirectionalAssessmentV1 and SurvivalResultV1 evidence, explicit regime
binding, and an offline strategy registry snapshot. Produces fachliche suitability evidence
only — no runtime, authority, order, risk, sizing, or double-play composition effects.
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from enum import Enum
from typing import Mapping, Optional, Tuple

from trading.master_v2.directional_assessment_v1 import (
    DirectionalAssessmentSide,
    DirectionalAssessmentV1,
)
from trading.master_v2.survival_assessment_v1 import (
    SurvivalAssessmentStatus,
    SurvivalResultV1,
    directional_assessment_ref_from_assessment,
)
from trading.master_v2.survival_assessment_v1 import (
    DirectionalAssessmentRefV1 as SurvivalDirectionalAssessmentRefV1,
)

SUITABILITY_BINDING_LAYER_VERSION = "v1"
SUITABILITY_RANKING_POLICY_VERSION = "suitability_ranking_policy_v1"

_AUTHORITY_EFFECT_NONE = "NONE"
_RUNTIME_EFFECT_NONE = "NONE"
_ORDER_EFFECT_NONE = "NONE"
_RISK_EFFECT_NONE = "NONE"

_FORBIDDEN_INSTRUMENT_SUBSTRINGS = frozenset({"btc", "xbt", "bitcoin", "spot", "synthetic_spot"})

_UNKNOWN_REGIME_ID = "unknown_regime"


class SuitabilityBindingStatus(str, Enum):
    PASS = "pass"
    FAIL = "fail"
    BLOCKED = "blocked"


class SuitabilityRegimeStatus(str, Enum):
    KNOWN = "known"
    UNKNOWN = "unknown"


class SuitabilityHardBlockReason(str, Enum):
    NO_SUITABLE_STRATEGY = "no_suitable_strategy"
    SURVIVAL_NOT_PASS = "survival_not_pass"
    EXPLICIT_HARD_BLOCK = "explicit_hard_block"


class SuitabilityBlockedReason(str, Enum):
    DIRECTIONAL_ASSESSMENT_REF_MISMATCH = "directional_assessment_ref_mismatch"
    DIRECTIONAL_ASSESSMENT_REF_STALE = "directional_assessment_ref_stale"
    INPUT_INCOMPLETE = "input_incomplete"
    INSTRUMENT_KIND_FORBIDDEN = "instrument_kind_forbidden"
    MISSING_RANKING_POLICY = "missing_ranking_policy"
    MISSING_STRATEGY_REGISTRY = "missing_strategy_registry"
    POLICY_VERSION_INVALID = "policy_version_invalid"
    POLICY_VALIDITY_EPOCHS_INVALID = "policy_validity_epochs_invalid"
    RANKING_POLICY_VERSION_INVALID = "ranking_policy_version_invalid"
    REGIME_UNKNOWN = "regime_unknown"
    SIDE_MISMATCH = "side_mismatch"
    STRATEGY_REGISTRY_EMPTY = "strategy_registry_empty"
    SURVIVAL_RESULT_BLOCKED = "survival_result_blocked"
    SURVIVAL_RESULT_REF_MISMATCH = "survival_result_ref_mismatch"
    SURVIVAL_RESULT_REF_STALE = "survival_result_ref_stale"
    TRADING_EPOCH_OUT_OF_ORDER = "trading_epoch_out_of_order"
    EXPLICIT_BLOCKED = "explicit_blocked"


@dataclass(frozen=True)
class DirectionalAssessmentRefV1:
    """Immutable reference to upstream DirectionalAssessmentV1 evidence."""

    assessment_id: str
    semantic_digest: str
    trading_epoch: int
    side: DirectionalAssessmentSide
    status: str

    def __post_init__(self) -> None:
        if self.semantic_digest and not _valid_sha256_hex(self.semantic_digest):
            msg = "semantic_digest must be empty or a 64-char lowercase sha256 hex"
            raise ValueError(msg)


@dataclass(frozen=True)
class SurvivalResultRefV1:
    """Immutable reference to upstream SurvivalResultV1 evidence."""

    survival_id: str
    semantic_digest: str
    trading_epoch: int
    side: DirectionalAssessmentSide
    status: SurvivalAssessmentStatus

    def __post_init__(self) -> None:
        if self.semantic_digest and not _valid_sha256_hex(self.semantic_digest):
            msg = "semantic_digest must be empty or a 64-char lowercase sha256 hex"
            raise ValueError(msg)


@dataclass(frozen=True)
class SuitabilityStrategyEntryV1:
    """Offline strategy eligibility snapshot; not the runtime strategy registry."""

    strategy_id: str
    supported_regime_ids: Tuple[str, ...]
    supported_sides: Tuple[DirectionalAssessmentSide, ...]
    priority_rank: int
    disabled: bool = False
    confidence_score: Optional[float] = None


@dataclass(frozen=True)
class SuitabilityStrategyRegistryV1:
    """Immutable registry snapshot evaluated in strategy_id order, never list position."""

    entries: Tuple[SuitabilityStrategyEntryV1, ...]


@dataclass(frozen=True)
class SuitabilityRankingPolicyV1:
    """Versioned ranking policy with explicit tie-break on strategy_id."""

    validity_epochs: int
    no_match_status: SuitabilityBindingStatus
    policy_version: str = SUITABILITY_RANKING_POLICY_VERSION
    tie_break_field: str = "strategy_id"


@dataclass(frozen=True)
class SuitabilityBindingInputV1:
    instrument_id: str
    trading_epoch: int
    side: DirectionalAssessmentSide
    directional_assessment: DirectionalAssessmentV1
    survival_result: SurvivalResultV1
    regime_id: str
    regime_status: SuitabilityRegimeStatus
    strategy_registry: Optional[SuitabilityStrategyRegistryV1]
    last_evaluated_trading_epoch: int
    input_complete: bool
    explicit_hard_block_reasons: Tuple[SuitabilityHardBlockReason, ...]
    explicit_blocked_reasons: Tuple[SuitabilityBlockedReason, ...]
    ranking_policy_version: str


@dataclass(frozen=True)
class SuitabilityResultV1:
    suitability_id: str
    instrument_id: str
    side: DirectionalAssessmentSide
    trading_epoch: int
    directional_assessment_ref: DirectionalAssessmentRefV1
    survival_result_ref: SurvivalResultRefV1
    regime_id: str
    regime_status: SuitabilityRegimeStatus
    eligible_strategy_ids: Tuple[str, ...]
    selected_strategy_id: Optional[str]
    ranking_policy_version: str
    tie_break_trace: Tuple[str, ...]
    status: SuitabilityBindingStatus
    hard_block_reasons: Tuple[str, ...]
    reason_codes: Tuple[str, ...]
    valid_until_epoch: int
    semantic_digest: str
    authority_effect: str = _AUTHORITY_EFFECT_NONE
    runtime_effect: str = _RUNTIME_EFFECT_NONE
    order_effect: str = _ORDER_EFFECT_NONE
    risk_effect: str = _RISK_EFFECT_NONE

    def __post_init__(self) -> None:
        if self.semantic_digest and not _valid_sha256_hex(self.semantic_digest):
            msg = "semantic_digest must be empty or a 64-char lowercase sha256 hex"
            raise ValueError(msg)
        if self.valid_until_epoch <= self.trading_epoch:
            msg = "valid_until_epoch must be strictly greater than trading_epoch"
            raise ValueError(msg)
        if self.status in (SuitabilityBindingStatus.FAIL, SuitabilityBindingStatus.BLOCKED):
            if self.selected_strategy_id is not None:
                msg = "selected_strategy_id must be unset for FAIL or BLOCKED"
                raise ValueError(msg)


def _valid_sha256_hex(value: str) -> bool:
    return bool(re.fullmatch(r"[0-9a-f]{64}", value))


def _positive_int(value: object) -> bool:
    return isinstance(value, int) and value > 0


def _instrument_id_allowed(instrument_id: str) -> bool:
    lowered = instrument_id.lower()
    return not any(token in lowered for token in _FORBIDDEN_INSTRUMENT_SUBSTRINGS)


def directional_assessment_ref_from_assessment_v1(
    assessment: DirectionalAssessmentV1,
) -> DirectionalAssessmentRefV1:
    return DirectionalAssessmentRefV1(
        assessment_id=assessment.assessment_id,
        semantic_digest=assessment.semantic_digest,
        trading_epoch=assessment.trading_epoch,
        side=assessment.side,
        status=assessment.status.value,
    )


def survival_result_ref_from_result(result: SurvivalResultV1) -> SurvivalResultRefV1:
    return SurvivalResultRefV1(
        survival_id=result.survival_id,
        semantic_digest=result.semantic_digest,
        trading_epoch=result.trading_epoch,
        side=result.side,
        status=result.status,
    )


def validate_suitability_ranking_policy(
    policy: SuitabilityRankingPolicyV1,
    *,
    ranking_policy_version: str,
) -> Tuple[SuitabilityBlockedReason, ...]:
    blocks: list[SuitabilityBlockedReason] = []
    if not policy.policy_version or policy.policy_version != SUITABILITY_RANKING_POLICY_VERSION:
        blocks.append(SuitabilityBlockedReason.POLICY_VERSION_INVALID)
    if ranking_policy_version != SUITABILITY_RANKING_POLICY_VERSION:
        blocks.append(SuitabilityBlockedReason.RANKING_POLICY_VERSION_INVALID)
    if not _positive_int(policy.validity_epochs):
        blocks.append(SuitabilityBlockedReason.POLICY_VALIDITY_EPOCHS_INVALID)
    if policy.no_match_status not in (
        SuitabilityBindingStatus.FAIL,
        SuitabilityBindingStatus.BLOCKED,
    ):
        blocks.append(SuitabilityBlockedReason.POLICY_VERSION_INVALID)
    if policy.tie_break_field != "strategy_id":
        blocks.append(SuitabilityBlockedReason.POLICY_VERSION_INVALID)
    return tuple(dict.fromkeys(blocks))


def _is_unknown_regime(regime_id: str, regime_status: SuitabilityRegimeStatus) -> bool:
    return (
        regime_status is SuitabilityRegimeStatus.UNKNOWN
        or regime_id.strip().lower() == _UNKNOWN_REGIME_ID
    )


def _strategy_supports_side(
    entry: SuitabilityStrategyEntryV1,
    side: DirectionalAssessmentSide,
) -> bool:
    return side in entry.supported_sides


def _strategy_supports_regime(entry: SuitabilityStrategyEntryV1, regime_id: str) -> bool:
    normalized = regime_id.strip().lower()
    return normalized in {rid.strip().lower() for rid in entry.supported_regime_ids}


def filter_eligible_strategies(
    registry: SuitabilityStrategyRegistryV1,
    *,
    side: DirectionalAssessmentSide,
    regime_id: str,
) -> Tuple[SuitabilityStrategyEntryV1, ...]:
    eligible = [
        entry
        for entry in registry.entries
        if not entry.disabled
        and _strategy_supports_side(entry, side)
        and _strategy_supports_regime(entry, regime_id)
    ]
    return tuple(sorted(eligible, key=lambda e: (e.priority_rank, e.strategy_id)))


def rank_eligible_strategies(
    eligible: Tuple[SuitabilityStrategyEntryV1, ...],
    *,
    policy: SuitabilityRankingPolicyV1,
) -> Tuple[SuitabilityStrategyEntryV1, ...]:
    """Deterministic ranking: priority_rank asc, then strategy_id lexicographic asc."""

    del policy  # version validated separately; criteria are fixed for v1
    return tuple(sorted(eligible, key=lambda e: (e.priority_rank, e.strategy_id)))


def select_strategy_deterministic(
    eligible: Tuple[SuitabilityStrategyEntryV1, ...],
    *,
    policy: SuitabilityRankingPolicyV1,
) -> Tuple[Optional[str], Tuple[str, ...]]:
    ranked = rank_eligible_strategies(eligible, policy=policy)
    if not ranked:
        return None, ("no_eligible_strategies",)
    if len(ranked) == 1:
        return ranked[0].strategy_id, ("single_eligible_strategy",)
    trace = (
        "ranking_policy_version="
        + policy.policy_version
        + ";criteria=priority_rank,strategy_id;order=asc,asc;"
        + f"tie_break={policy.tie_break_field};candidates="
        + ",".join(e.strategy_id for e in ranked)
    )
    return ranked[0].strategy_id, (trace,)


def _derive_suitability_id(
    instrument_id: str,
    trading_epoch: int,
    side: DirectionalAssessmentSide,
    status: SuitabilityBindingStatus,
) -> str:
    return f"suitability-{instrument_id}-epoch{trading_epoch}-{side.value}-{status.value}"


def serialize_suitability_result_canonical(result: SuitabilityResultV1) -> str:
    dref = result.directional_assessment_ref
    sref = result.survival_result_ref
    payload = {
        "authority_effect": result.authority_effect,
        "directional_assessment_digest": dref.semantic_digest,
        "directional_assessment_epoch": dref.trading_epoch,
        "directional_assessment_id": dref.assessment_id,
        "directional_assessment_side": dref.side.value,
        "directional_assessment_status": dref.status,
        "eligible_strategy_ids": list(result.eligible_strategy_ids),
        "hard_block_reasons": sorted(result.hard_block_reasons),
        "instrument_id": result.instrument_id,
        "layer_version": SUITABILITY_BINDING_LAYER_VERSION,
        "order_effect": result.order_effect,
        "ranking_policy_version": result.ranking_policy_version,
        "reason_codes": sorted(result.reason_codes),
        "regime_id": result.regime_id,
        "regime_status": result.regime_status.value,
        "risk_effect": result.risk_effect,
        "runtime_effect": result.runtime_effect,
        "selected_strategy_id": result.selected_strategy_id,
        "side": result.side.value,
        "status": result.status.value,
        "suitability_id": result.suitability_id,
        "survival_result_digest": sref.semantic_digest,
        "survival_result_epoch": sref.trading_epoch,
        "survival_result_id": sref.survival_id,
        "survival_result_side": sref.side.value,
        "survival_result_status": sref.status.value,
        "tie_break_trace": list(result.tie_break_trace),
        "trading_epoch": result.trading_epoch,
        "valid_until_epoch": result.valid_until_epoch,
    }
    return json.dumps(payload, sort_keys=True, separators=(",", ":"))


def compute_suitability_result_semantic_digest(result: SuitabilityResultV1) -> str:
    canonical = serialize_suitability_result_canonical(result)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def with_computed_suitability_result_digest(result: SuitabilityResultV1) -> SuitabilityResultV1:
    digest = compute_suitability_result_semantic_digest(result)
    return SuitabilityResultV1(
        suitability_id=result.suitability_id,
        instrument_id=result.instrument_id,
        side=result.side,
        trading_epoch=result.trading_epoch,
        directional_assessment_ref=result.directional_assessment_ref,
        survival_result_ref=result.survival_result_ref,
        regime_id=result.regime_id,
        regime_status=result.regime_status,
        eligible_strategy_ids=result.eligible_strategy_ids,
        selected_strategy_id=result.selected_strategy_id,
        ranking_policy_version=result.ranking_policy_version,
        tie_break_trace=result.tie_break_trace,
        status=result.status,
        hard_block_reasons=result.hard_block_reasons,
        reason_codes=result.reason_codes,
        valid_until_epoch=result.valid_until_epoch,
        semantic_digest=digest,
        authority_effect=result.authority_effect,
        runtime_effect=result.runtime_effect,
        order_effect=result.order_effect,
        risk_effect=result.risk_effect,
    )


def _resolve_epoch_semantics(
    *,
    trading_epoch: int,
    last_evaluated_trading_epoch: int,
    assessment_epoch: int,
    survival_epoch: int,
) -> Tuple[str, Optional[SuitabilityBlockedReason]]:
    if assessment_epoch > trading_epoch:
        return "stale_assessment_ref", SuitabilityBlockedReason.DIRECTIONAL_ASSESSMENT_REF_STALE
    if survival_epoch > trading_epoch:
        return "stale_survival_ref", SuitabilityBlockedReason.SURVIVAL_RESULT_REF_STALE
    if last_evaluated_trading_epoch < 0:
        return "first", None
    if trading_epoch < last_evaluated_trading_epoch:
        return "out_of_order", SuitabilityBlockedReason.TRADING_EPOCH_OUT_OF_ORDER
    return "ok", None


def _refs_consistent(
    inp: SuitabilityBindingInputV1,
) -> Tuple[Optional[SuitabilityBlockedReason], ...]:
    blocks: list[SuitabilityBlockedReason] = []
    assessment = inp.directional_assessment
    survival = inp.survival_result
    if assessment.instrument_id != inp.instrument_id:
        blocks.append(SuitabilityBlockedReason.DIRECTIONAL_ASSESSMENT_REF_MISMATCH)
    if survival.instrument_id != inp.instrument_id:
        blocks.append(SuitabilityBlockedReason.SURVIVAL_RESULT_REF_MISMATCH)
    if assessment.side != inp.side:
        blocks.append(SuitabilityBlockedReason.SIDE_MISMATCH)
    if survival.side != inp.side:
        blocks.append(SuitabilityBlockedReason.SIDE_MISMATCH)
    if assessment.trading_epoch != survival.trading_epoch:
        blocks.append(SuitabilityBlockedReason.SURVIVAL_RESULT_REF_MISMATCH)
    surv_dref: SurvivalDirectionalAssessmentRefV1 = survival.directional_assessment_ref
    if surv_dref.assessment_id != assessment.assessment_id:
        blocks.append(SuitabilityBlockedReason.SURVIVAL_RESULT_REF_MISMATCH)
    if surv_dref.semantic_digest != assessment.semantic_digest:
        blocks.append(SuitabilityBlockedReason.SURVIVAL_RESULT_REF_MISMATCH)
    return tuple(dict.fromkeys(blocks))


def _finalize_result(
    inp: SuitabilityBindingInputV1,
    policy: SuitabilityRankingPolicyV1,
    *,
    status: SuitabilityBindingStatus,
    eligible_strategy_ids: Tuple[str, ...],
    selected_strategy_id: Optional[str],
    tie_break_trace: Tuple[str, ...],
    hard_block_reasons: Tuple[str, ...],
    reason_codes: Tuple[str, ...],
) -> SuitabilityResultV1:
    valid_until = inp.trading_epoch + policy.validity_epochs
    result = SuitabilityResultV1(
        suitability_id=_derive_suitability_id(
            inp.instrument_id, inp.trading_epoch, inp.side, status
        ),
        instrument_id=inp.instrument_id,
        side=inp.side,
        trading_epoch=inp.trading_epoch,
        directional_assessment_ref=directional_assessment_ref_from_assessment_v1(
            inp.directional_assessment
        ),
        survival_result_ref=survival_result_ref_from_result(inp.survival_result),
        regime_id=inp.regime_id,
        regime_status=inp.regime_status,
        eligible_strategy_ids=eligible_strategy_ids,
        selected_strategy_id=selected_strategy_id,
        ranking_policy_version=policy.policy_version,
        tie_break_trace=tie_break_trace,
        status=status,
        hard_block_reasons=hard_block_reasons,
        reason_codes=reason_codes,
        valid_until_epoch=valid_until,
        semantic_digest="",
    )
    return with_computed_suitability_result_digest(result)


def evaluate_suitability_binding_v1(
    inp: SuitabilityBindingInputV1,
    policy: SuitabilityRankingPolicyV1,
) -> SuitabilityResultV1:
    """
    Deterministic suitability evaluator.

    Fail-closed on incomplete, untrusted, ambiguous, or epoch-invalid inputs.
    Never mutates ``inp.directional_assessment``, ``inp.survival_result``, or upstream evidence.
    """

    def blocked(
        reason: SuitabilityBlockedReason,
        *,
        reason_code: str,
        hard: Tuple[str, ...] = (),
    ) -> SuitabilityResultV1:
        return _finalize_result(
            inp,
            policy,
            status=SuitabilityBindingStatus.BLOCKED,
            eligible_strategy_ids=(),
            selected_strategy_id=None,
            tie_break_trace=(),
            hard_block_reasons=hard,
            reason_codes=(reason_code, reason.value),
        )

    policy_blocks = validate_suitability_ranking_policy(
        policy, ranking_policy_version=inp.ranking_policy_version
    )
    if policy_blocks:
        return blocked(
            SuitabilityBlockedReason.POLICY_VERSION_INVALID,
            reason_code="policy_validation_failed",
        )

    if not _instrument_id_allowed(inp.instrument_id):
        return blocked(
            SuitabilityBlockedReason.INSTRUMENT_KIND_FORBIDDEN,
            reason_code="instrument_gate_failed",
        )

    if not inp.input_complete:
        return blocked(
            SuitabilityBlockedReason.INPUT_INCOMPLETE,
            reason_code="input_gate_failed",
        )

    if inp.explicit_blocked_reasons:
        return _finalize_result(
            inp,
            policy,
            status=SuitabilityBindingStatus.BLOCKED,
            eligible_strategy_ids=(),
            selected_strategy_id=None,
            tie_break_trace=(),
            hard_block_reasons=(),
            reason_codes=("explicit_blocked",)
            + tuple(sorted(r.value for r in inp.explicit_blocked_reasons)),
        )

    ref_blocks = _refs_consistent(inp)
    if ref_blocks:
        return blocked(ref_blocks[0], reason_code="reference_consistency_failed")

    assessment = inp.directional_assessment
    survival = inp.survival_result

    epoch_mode, epoch_block = _resolve_epoch_semantics(
        trading_epoch=inp.trading_epoch,
        last_evaluated_trading_epoch=inp.last_evaluated_trading_epoch,
        assessment_epoch=assessment.trading_epoch,
        survival_epoch=survival.trading_epoch,
    )
    if epoch_block is not None:
        return blocked(epoch_block, reason_code=f"epoch_semantics_failed:{epoch_mode}")

    if survival.status is SurvivalAssessmentStatus.BLOCKED:
        return blocked(
            SuitabilityBlockedReason.SURVIVAL_RESULT_BLOCKED,
            reason_code="survival_gate_blocked",
        )

    if survival.status is not SurvivalAssessmentStatus.PASS:
        hard = (SuitabilityHardBlockReason.SURVIVAL_NOT_PASS.value,)
        if inp.explicit_hard_block_reasons:
            hard = tuple(
                dict.fromkeys(
                    [SuitabilityHardBlockReason.SURVIVAL_NOT_PASS.value]
                    + [r.value for r in inp.explicit_hard_block_reasons]
                )
            )
        status = (
            SuitabilityBindingStatus.FAIL
            if survival.status is SurvivalAssessmentStatus.FAIL
            else SuitabilityBindingStatus.BLOCKED
        )
        return _finalize_result(
            inp,
            policy,
            status=status,
            eligible_strategy_ids=(),
            selected_strategy_id=None,
            tie_break_trace=(),
            hard_block_reasons=hard,
            reason_codes=("survival_not_pass",),
        )

    if _is_unknown_regime(inp.regime_id, inp.regime_status):
        return blocked(
            SuitabilityBlockedReason.REGIME_UNKNOWN,
            reason_code="unknown_regime_blocked",
        )

    if inp.strategy_registry is None:
        return blocked(
            SuitabilityBlockedReason.MISSING_STRATEGY_REGISTRY,
            reason_code="registry_missing",
        )

    if not inp.strategy_registry.entries:
        return blocked(
            SuitabilityBlockedReason.STRATEGY_REGISTRY_EMPTY,
            reason_code="registry_empty",
        )

    eligible_entries = filter_eligible_strategies(
        inp.strategy_registry,
        side=inp.side,
        regime_id=inp.regime_id,
    )
    eligible_ids = tuple(e.strategy_id for e in eligible_entries)

    if not eligible_entries:
        status = policy.no_match_status
        hard: Tuple[str, ...] = ()
        if status is SuitabilityBindingStatus.FAIL:
            hard = (SuitabilityHardBlockReason.NO_SUITABLE_STRATEGY.value,)
        return _finalize_result(
            inp,
            policy,
            status=status,
            eligible_strategy_ids=(),
            selected_strategy_id=None,
            tie_break_trace=("no_eligible_strategies",),
            hard_block_reasons=hard,
            reason_codes=("no_suitable_strategy",),
        )

    if inp.explicit_hard_block_reasons:
        return _finalize_result(
            inp,
            policy,
            status=SuitabilityBindingStatus.FAIL,
            eligible_strategy_ids=eligible_ids,
            selected_strategy_id=None,
            tie_break_trace=(),
            hard_block_reasons=tuple(sorted(r.value for r in inp.explicit_hard_block_reasons)),
            reason_codes=("explicit_hard_block",),
        )

    selected_id, tie_trace = select_strategy_deterministic(eligible_entries, policy=policy)
    assert selected_id is not None
    return _finalize_result(
        inp,
        policy,
        status=SuitabilityBindingStatus.PASS,
        eligible_strategy_ids=eligible_ids,
        selected_strategy_id=selected_id,
        tie_break_trace=tie_trace,
        hard_block_reasons=(),
        reason_codes=("strategy_selected",),
    )


def mirror_suitability_strategy_entry_for_short(
    entry: SuitabilityStrategyEntryV1,
) -> SuitabilityStrategyEntryV1:
    """Structural mirror helper for Long/Short symmetry tests."""
    mirrored_sides = tuple(
        DirectionalAssessmentSide.SHORT
        if s is DirectionalAssessmentSide.LONG
        else DirectionalAssessmentSide.LONG
        for s in entry.supported_sides
    )
    return SuitabilityStrategyEntryV1(
        strategy_id=entry.strategy_id,
        supported_regime_ids=entry.supported_regime_ids,
        supported_sides=mirrored_sides,
        priority_rank=entry.priority_rank,
        disabled=entry.disabled,
        confidence_score=entry.confidence_score,
    )


__all__ = [
    "SUITABILITY_BINDING_LAYER_VERSION",
    "SUITABILITY_RANKING_POLICY_VERSION",
    "DirectionalAssessmentRefV1",
    "SurvivalResultRefV1",
    "SuitabilityBindingInputV1",
    "SuitabilityBindingStatus",
    "SuitabilityBlockedReason",
    "SuitabilityHardBlockReason",
    "SuitabilityRankingPolicyV1",
    "SuitabilityRegimeStatus",
    "SuitabilityResultV1",
    "SuitabilityStrategyEntryV1",
    "SuitabilityStrategyRegistryV1",
    "compute_suitability_result_semantic_digest",
    "directional_assessment_ref_from_assessment_v1",
    "evaluate_suitability_binding_v1",
    "filter_eligible_strategies",
    "mirror_suitability_strategy_entry_for_short",
    "rank_eligible_strategies",
    "select_strategy_deterministic",
    "serialize_suitability_result_canonical",
    "survival_result_ref_from_result",
    "validate_suitability_ranking_policy",
    "with_computed_suitability_result_digest",
]
