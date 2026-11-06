# src/trading/master_v2/double_play_suitability.py
"""
Pure Master V2 Double Play strategy suitability projection (metadata only).

No I/O, no strategy execution, no registry, no exchange, no live authority.
See docs/ops/specs/MASTER_V2_DOUBLE_PLAY_STRATEGY_SUITABILITY_PROJECTION_CONTRACT_V0.md
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

DOUBLE_PLAY_SUITABILITY_LAYER_VERSION = "v0"


class SuitabilityClass(str, Enum):
    LONG_ONLY_CANDIDATE = "long_only_candidate"
    SHORT_ONLY_CANDIDATE = "short_only_candidate"
    BOTH_SIDES_CANDIDATE = "both_sides_candidate"
    NEUTRAL_RANGE_CANDIDATE = "neutral_range_candidate"
    DISABLED_FOR_CANDIDATE = "disabled_for_candidate"
    UNKNOWN_SUITABILITY = "unknown_suitability"


class SideCompatibility(str, Enum):
    LONG_BULL = "long_bull"
    SHORT_BEAR = "short_bear"
    BOTH = "both"
    NEUTRAL_RANGE = "neutral_range"
    UNKNOWN = "unknown"


class SuitabilityBlockReason(str, Enum):
    """Model-level block codes; not execution or registry authority."""

    STRATEGY_DISABLED = "strategy_disabled"
    METADATA_BLOCKER = "metadata_blocker"
    INSTRUMENT_INTELLIGENCE_INCOMPLETE = "instrument_intelligence_incomplete"
    SURVIVAL_ENVELOPE_BLOCKED = "survival_envelope_blocked"
    INSUFFICIENT_EXPLICIT_EVIDENCE = "insufficient_explicit_evidence"
    DECLARED_SIDE_INCOMPLETE = "declared_side_incomplete"


@dataclass(frozen=True)
class StrategyMetadata:
    """Opaque strategy identity and non-authoritative display/context fields."""

    strategy_id: str
    strategy_family: str | None
    declared_side: SideCompatibility
    explicit_side_evidence: bool
    registry_label: str | None = None
    name_surface: str | None = None
    ecm_or_armstrong_surface: str | None = None
    dashboard_label: str | None = None
    ai_summary: str | None = None
    disabled: bool = False
    blockers: tuple[SuitabilityBlockReason, ...] = ()


@dataclass(frozen=True)
class InstrumentIntelligenceSummary:
    """Presence flags for required Instrument Intelligence dimensions."""

    volatility_profile_present: bool
    liquidity_profile_present: bool
    spread_profile_present: bool
    funding_profile_present: bool
    freshness_profile_present: bool
    risk_warnings_present: bool = False
    missing_data_warnings_present: bool = False


@dataclass(frozen=True)
class SuitabilityProjectionInput:
    strategy: StrategyMetadata
    instrument: InstrumentIntelligenceSummary | None
    survival_envelope_allows: bool
    survival_block_reasons: tuple[str, ...] = ()


@dataclass(frozen=True)
class StrategySuitabilityProjection:
    strategy_id: str
    strategy_family: str | None
    suitability_class: SuitabilityClass
    side_compatibility: SideCompatibility
    eligible_for_long_bull_pool: bool
    eligible_for_short_bear_pool: bool
    eligible_for_neutral_pool: bool
    block_reasons: tuple[SuitabilityBlockReason, ...]
    missing_inputs: tuple[str, ...]
    reason: str
    is_signal: bool = False
    is_authority: bool = False
    live_authorization: bool = False


@dataclass(frozen=True)
class SuitabilityProjectionDecision:
    projection: StrategySuitabilityProjection
    can_enter_any_candidate_pool: bool
    can_enter_long_bull_pool: bool
    can_enter_short_bear_pool: bool
    can_enter_neutral_pool: bool
    live_authorization: bool = False


def metadata_has_authoritative_side_evidence(meta: StrategyMetadata) -> bool:
    """
    True when explicit_side_evidence is set and declared_side is not UNKNOWN
    in a way that can support directional or neutral range classification
    (still not trading authority).
    """

    if not meta.explicit_side_evidence:
        return False
    return meta.declared_side != SideCompatibility.UNKNOWN


def instrument_intelligence_complete(
    inst: InstrumentIntelligenceSummary | None,
) -> bool:
    if inst is None:
        return False
    return all(
        (
            inst.volatility_profile_present,
            inst.liquidity_profile_present,
            inst.spread_profile_present,
            inst.funding_profile_present,
            inst.freshness_profile_present,
        )
    )


def survival_allows_projection(inp: SuitabilityProjectionInput) -> bool:
    return bool(inp.survival_envelope_allows)


def _pool_flags_for_class(
    cls: SuitabilityClass,
) -> tuple[bool, bool, bool]:
    """(long_bull, short_bear, neutral) eligibility from suitability class only."""

    if cls == SuitabilityClass.LONG_ONLY_CANDIDATE:
        return (True, False, False)
    if cls == SuitabilityClass.SHORT_ONLY_CANDIDATE:
        return (False, True, False)
    if cls == SuitabilityClass.BOTH_SIDES_CANDIDATE:
        return (True, True, False)
    if cls == SuitabilityClass.NEUTRAL_RANGE_CANDIDATE:
        return (False, False, True)
    return (False, False, False)


def _classify_from_declared_and_evidence(
    meta: StrategyMetadata,
) -> tuple[SuitabilityClass, SideCompatibility, str] | None:
    """
    Returns (class, side_compatibility, reason) or None if caller should emit UNKNOWN
    (after gates, or immediately for inconsistent metadata).
    """

    d = meta.declared_side
    ex = meta.explicit_side_evidence

    if d == SideCompatibility.UNKNOWN and not ex:
        return None

    if d == SideCompatibility.LONG_BULL and ex:
        return (
            SuitabilityClass.LONG_ONLY_CANDIDATE,
            SideCompatibility.LONG_BULL,
            "Long/Bull only candidate with explicit side evidence.",
        )
    if d == SideCompatibility.SHORT_BEAR and ex:
        return (
            SuitabilityClass.SHORT_ONLY_CANDIDATE,
            SideCompatibility.SHORT_BEAR,
            "Short/Bear only candidate with explicit side evidence.",
        )
    if d == SideCompatibility.BOTH and ex:
        return (
            SuitabilityClass.BOTH_SIDES_CANDIDATE,
            SideCompatibility.BOTH,
            "Both-side candidate with explicit both-side evidence.",
        )
    if d == SideCompatibility.BOTH and not ex:
        return (
            SuitabilityClass.UNKNOWN_SUITABILITY,
            SideCompatibility.UNKNOWN,
            "Both-side metadata requires explicit both-side evidence; fail closed.",
        )
    if d == SideCompatibility.NEUTRAL_RANGE and ex:
        return (
            SuitabilityClass.NEUTRAL_RANGE_CANDIDATE,
            SideCompatibility.NEUTRAL_RANGE,
            "Neutral/range candidate with explicit context evidence.",
        )
    if d in (SideCompatibility.LONG_BULL, SideCompatibility.SHORT_BEAR) and not ex:
        return (
            SuitabilityClass.UNKNOWN_SUITABILITY,
            SideCompatibility.UNKNOWN,
            "Directional declared side without explicit side evidence; fail closed.",
        )
    if d == SideCompatibility.NEUTRAL_RANGE and not ex:
        return (
            SuitabilityClass.UNKNOWN_SUITABILITY,
            SideCompatibility.UNKNOWN,
            "Neutral/range without explicit context evidence; fail closed.",
        )
    if d == SideCompatibility.UNKNOWN and ex:
        return (
            SuitabilityClass.UNKNOWN_SUITABILITY,
            SideCompatibility.UNKNOWN,
            "Declared side unknown even with explicit flag; cannot classify.",
        )
    return None


def project_strategy_suitability(
    inp: SuitabilityProjectionInput,
) -> SuitabilityProjectionDecision:
    """
    Fail-closed suitability projection. ``live_authorization`` is always false.
    Not a signal; not Master V2, Testnet, or Live authority.
    """

    meta = inp.strategy
    miss: list[str] = []
    br: list[SuitabilityBlockReason] = list(meta.blockers)

    if meta.disabled:
        br.append(SuitabilityBlockReason.STRATEGY_DISABLED)
        p = _unknown_projection(
            meta,
            SuitabilityClass.DISABLED_FOR_CANDIDATE,
            SideCompatibility.UNKNOWN,
            tuple(dict.fromkeys(br)),
            ("strategy.disabled",),
            "Strategy marked disabled; no candidate pools.",
        )
        return _decision_from_projection(p, allow_any=False)

    if meta.blockers:
        br2 = list(dict.fromkeys(list(meta.blockers) + [SuitabilityBlockReason.METADATA_BLOCKER]))
        p = _unknown_projection(
            meta,
            SuitabilityClass.DISABLED_FOR_CANDIDATE,
            SideCompatibility.UNKNOWN,
            tuple(br2),
            (f"metadata_blockers={len(meta.blockers)}",),
            "Metadata-reported blockers; disabled for candidate class.",
        )
        return _decision_from_projection(p, allow_any=False)

    if not instrument_intelligence_complete(inp.instrument):
        br.append(SuitabilityBlockReason.INSTRUMENT_INTELLIGENCE_INCOMPLETE)
        miss.append("instrument_intelligence")
        p = _unknown_projection(
            meta,
            SuitabilityClass.UNKNOWN_SUITABILITY,
            SideCompatibility.UNKNOWN,
            tuple(dict.fromkeys(br)),
            tuple(miss) if miss else ("instrument_intelligence",),
            "Instrument Intelligence incomplete or missing; unknown suitability (fail closed).",
        )
        return _decision_from_projection(p, allow_any=False)

    if not survival_allows_projection(inp):
        br.append(SuitabilityBlockReason.SURVIVAL_ENVELOPE_BLOCKED)
        for r in inp.survival_block_reasons:
            miss.append(f"survival:{r}")
        p = _unknown_projection(
            meta,
            SuitabilityClass.UNKNOWN_SUITABILITY,
            SideCompatibility.UNKNOWN,
            tuple(dict.fromkeys(br)),
            tuple(miss) if miss else ("survival_envelope",),
            "Survival envelope blocks suitability projection consumption; no pools.",
        )
        return _decision_from_projection(p, allow_any=False)

    if not meta.explicit_side_evidence and meta.declared_side == SideCompatibility.UNKNOWN:
        br.append(SuitabilityBlockReason.INSUFFICIENT_EXPLICIT_EVIDENCE)
        p = _unknown_projection(
            meta,
            SuitabilityClass.UNKNOWN_SUITABILITY,
            SideCompatibility.UNKNOWN,
            tuple(dict.fromkeys(br)),
            ("explicit_side_evidence,declared_side",),
            "Registry, name, ECM/Armstrong, dashboard, or AI text alone cannot grant "
            "suitability; unknown (fail closed).",
        )
        return _decision_from_projection(p, allow_any=False)

    classified = _classify_from_declared_and_evidence(meta)
    if classified is None:
        br.append(SuitabilityBlockReason.DECLARED_SIDE_INCOMPLETE)
        p = _unknown_projection(
            meta,
            SuitabilityClass.UNKNOWN_SUITABILITY,
            SideCompatibility.UNKNOWN,
            tuple(dict.fromkeys(br)),
            ("declared_side",),
            "Could not classify from declared side and evidence.",
        )
        return _decision_from_projection(p, allow_any=False)
    scls, sside, sreason = classified
    if scls == SuitabilityClass.UNKNOWN_SUITABILITY:
        br.append(SuitabilityBlockReason.INSUFFICIENT_EXPLICIT_EVIDENCE)
        p = _unknown_projection(
            meta,
            scls,
            sside,
            tuple(dict.fromkeys(br)),
            ("side_evidence",),
            sreason,
        )
        return _decision_from_projection(p, allow_any=False)

    lg, sg, ng = _pool_flags_for_class(scls)
    block_t = tuple(dict.fromkeys(br)) if br else ()
    p = StrategySuitabilityProjection(
        strategy_id=meta.strategy_id,
        strategy_family=meta.strategy_family,
        suitability_class=scls,
        side_compatibility=sside,
        eligible_for_long_bull_pool=lg,
        eligible_for_short_bear_pool=sg,
        eligible_for_neutral_pool=ng,
        block_reasons=block_t,
        missing_inputs=(),
        reason=sreason,
        is_signal=False,
        is_authority=False,
        live_authorization=False,
    )
    return _decision_from_projection(
        p,
        allow_any=lg or sg or ng,
    )


def _unknown_projection(
    meta: StrategyMetadata,
    suitability_class: SuitabilityClass,
    side: SideCompatibility,
    block_reasons: tuple[SuitabilityBlockReason, ...],
    missing: tuple[str, ...],
    reason: str,
) -> StrategySuitabilityProjection:
    return StrategySuitabilityProjection(
        strategy_id=meta.strategy_id,
        strategy_family=meta.strategy_family,
        suitability_class=suitability_class,
        side_compatibility=side,
        eligible_for_long_bull_pool=False,
        eligible_for_short_bear_pool=False,
        eligible_for_neutral_pool=False,
        block_reasons=block_reasons,
        missing_inputs=missing,
        reason=reason,
        is_signal=False,
        is_authority=False,
        live_authorization=False,
    )


def _decision_from_projection(
    p: StrategySuitabilityProjection,
    *,
    allow_any: bool,
) -> SuitabilityProjectionDecision:
    return SuitabilityProjectionDecision(
        projection=p,
        can_enter_any_candidate_pool=bool(allow_any),
        can_enter_long_bull_pool=p.eligible_for_long_bull_pool,
        can_enter_short_bear_pool=p.eligible_for_short_bear_pool,
        can_enter_neutral_pool=p.eligible_for_neutral_pool,
        live_authorization=False,
    )
