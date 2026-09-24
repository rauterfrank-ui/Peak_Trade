"""Join projection extensions for research stratification v2."""

from __future__ import annotations

from typing import Any, Mapping

from research.canonical_volatility_max_age_productive_research_evidence_accumulation_v1.models_v1 import (
    ProductiveResearchEvidenceRecordV1,
)
from research.canonical_volatility_max_age_productive_research_evidence_accumulation_v1.research_stratification_v2.constants_v2 import (
    EVIDENCE_SCHEMA_VERSION_V2,
)
from research.canonical_volatility_max_age_productive_research_evidence_accumulation_v1.join_projection_v1 import (
    project_productive_evidence_to_research_join_v1,
)


def project_productive_evidence_to_research_join_v2(
    record: ProductiveResearchEvidenceRecordV1,
) -> tuple[Any, dict[str, Any]]:
    """Project v2 join with stratification key separate from legacy regime_label."""
    base = project_productive_evidence_to_research_join_v1(record)
    payload = record.to_dict()
    if payload.get("evidence_schema_version") != EVIDENCE_SCHEMA_VERSION_V2:
        raise ValueError("join_v2_requires_evidence_schema_v2")
    stratification_key = str(payload.get("stratification_key_v2") or "")
    extension = {
        "research_stratification_version": payload.get("research_stratification_version"),
        "stratification_key_v2": stratification_key,
        "market_state_stratum_v2": payload.get("market_state_stratum_v2"),
        "volatility_regime_stratum_v2": payload.get("volatility_regime_stratum_v2"),
        "legacy_regime_label_v1": payload.get("legacy_regime_label_v1")
        or payload.get("regime_label"),
        "join_regime_id_v2": stratification_key,
    }
    base_payload = base.to_dict()
    if base_payload.get("regime_id") == record.regime_label:
        # Preserve v1 join field for loader compatibility; v2 consumers use join_regime_id_v2.
        base_payload["research_stratification_v2"] = extension
    return base, extension


def assert_join_v2_bijection_fields_v2(
    record: ProductiveResearchEvidenceRecordV1,
    extension: Mapping[str, Any],
) -> dict[str, bool]:
    payload = record.to_dict()
    return {
        "stratification_key_present": bool(extension.get("stratification_key_v2")),
        "legacy_regime_label_preserved": bool(payload.get("regime_label")),
        "join_regime_id_v2_differs_from_legacy_when_classified": (
            extension.get("join_regime_id_v2") != payload.get("regime_label")
            or not payload.get("stratification_ok")
        ),
    }
