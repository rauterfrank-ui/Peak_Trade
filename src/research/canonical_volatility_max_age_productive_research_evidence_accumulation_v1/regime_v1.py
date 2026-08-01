"""Research-only regime metadata mapping (non-authority)."""

from __future__ import annotations

from typing import Any, Mapping, Optional

from research.canonical_volatility_max_age_productive_research_evidence_accumulation_v1.constants_v1 import (
    REGIME_LABEL_IS_RESEARCH_METADATA_ONLY,
    REGIME_LABEL_MUTATES_ALPHA,
    REGIME_LABEL_MUTATES_POLICY,
    REGIME_LABEL_MUTATES_POSITION,
)
from research.canonical_volatility_max_age_productive_research_evidence_accumulation_v1.models_v1 import (
    ResearchRegimeLabelV1,
    optional_text,
)


def map_typed_feature_regime_to_research_label_v1(
    feature_regime: Mapping[str, Any] | None,
) -> tuple[str, str, str]:
    """Map existing typed feature-regime inputs to research metadata labels.

    Never invents directional/volatility labels without typed evidence.
    Returns ``(regime_label, regime_source, regime_confidence)``.
    """
    _ = (
        REGIME_LABEL_IS_RESEARCH_METADATA_ONLY,
        REGIME_LABEL_MUTATES_ALPHA,
        REGIME_LABEL_MUTATES_POLICY,
        REGIME_LABEL_MUTATES_POSITION,
    )
    if not feature_regime:
        return (
            ResearchRegimeLabelV1.INSUFFICIENT_DATA.value,
            "ABSENT_FEATURE_REGIME",
            "UNKNOWN",
        )

    regime_id = optional_text(feature_regime.get("regime_id"))
    source = optional_text(feature_regime.get("regime_state_source")) or "TYPED_FEATURE_REGIME"
    blockers = feature_regime.get("blockers") or ()
    warmup_complete = feature_regime.get("warmup_complete")
    ok = feature_regime.get("ok")

    if regime_id in (None, "insufficient_history") or warmup_complete is False or ok is False:
        return (
            ResearchRegimeLabelV1.INSUFFICIENT_DATA.value,
            source,
            "UNKNOWN",
        )

    trend = dict(feature_regime.get("trend_features") or {})
    slope = trend.get("slope")
    strength = trend.get("strength")
    vol = feature_regime.get("volatility_estimate")
    structure = dict(feature_regime.get("market_structure_features") or {})
    range_ratio = structure.get("range_ratio")

    # Explicit stress/gap only when typed blockers declare it.
    blocker_text = " ".join(str(b) for b in blockers).upper()
    if "STRESS" in blocker_text or "GAP" in blocker_text:
        return (
            ResearchRegimeLabelV1.STRESS_OR_GAP.value,
            source,
            "UNKNOWN",
        )

    if regime_id == "trending":
        if isinstance(slope, (int, float)):
            if float(slope) > 0:
                return (
                    ResearchRegimeLabelV1.UP_DIRECTIONAL.value,
                    source,
                    "UNKNOWN",
                )
            if float(slope) < 0:
                return (
                    ResearchRegimeLabelV1.DOWN_DIRECTIONAL.value,
                    source,
                    "UNKNOWN",
                )
        return (
            ResearchRegimeLabelV1.UNCLASSIFIED.value,
            source,
            "UNKNOWN",
        )

    if regime_id == "ranging":
        return (
            ResearchRegimeLabelV1.CHOP_OR_RANGE.value,
            source,
            "UNKNOWN",
        )

    if regime_id == "volatile":
        # Without a typed low-vol comparator, only HIGH_VOLATILITY is admissible.
        if isinstance(vol, (int, float)) and float(vol) > 0:
            return (
                ResearchRegimeLabelV1.HIGH_VOLATILITY.value,
                source,
                "UNKNOWN",
            )
        return (
            ResearchRegimeLabelV1.UNCLASSIFIED.value,
            source,
            "UNKNOWN",
        )

    # Optional typed low-vol annotation — only if explicitly present.
    explicit_label = optional_text(feature_regime.get("research_regime_label"))
    if explicit_label in {r.value for r in ResearchRegimeLabelV1}:
        confidence = optional_text(feature_regime.get("regime_confidence")) or "UNKNOWN"
        return explicit_label, source, confidence

    # Do not invent LOW_VOLATILITY from range_ratio alone.
    _ = (strength, range_ratio)
    return (
        ResearchRegimeLabelV1.UNCLASSIFIED.value,
        source,
        "UNKNOWN",
    )


def regime_authority_flags_v1() -> dict[str, bool]:
    return {
        "regime_label_is_research_metadata_only": REGIME_LABEL_IS_RESEARCH_METADATA_ONLY,
        "regime_label_mutates_alpha": REGIME_LABEL_MUTATES_ALPHA,
        "regime_label_mutates_policy": REGIME_LABEL_MUTATES_POLICY,
        "regime_label_mutates_position": REGIME_LABEL_MUTATES_POSITION,
    }
