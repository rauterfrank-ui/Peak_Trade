"""Read-only D26 adapter: integrated replay decision evidence → native baseline classification."""

from __future__ import annotations

from typing import Any, Mapping

from src.governance.platform_unified_native_vs_candidate_baseline_evidence_v1 import (
    classify_canonical_trading_decision_evidence_v1,
)
from trading.master_v2.canonical_trading_decision_evidence_v1 import (
    CanonicalTradingDecisionEvidenceV1,
)


def bind_integrated_replay_native_baseline_classification_v1(
    evidence: CanonicalTradingDecisionEvidenceV1,
    *,
    influence_markers: Mapping[str, Any] | None = None,
) -> Mapping[str, Any]:
    record = classify_canonical_trading_decision_evidence_v1(
        evidence,
        influence_markers=influence_markers,
    )
    return record.to_dict()


__all__ = ["bind_integrated_replay_native_baseline_classification_v1"]
