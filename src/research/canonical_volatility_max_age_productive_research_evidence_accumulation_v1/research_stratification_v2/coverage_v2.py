"""Dimension-separated coverage for research stratification v2."""

from __future__ import annotations

from typing import Any, Mapping, Sequence

from research.canonical_volatility_max_age_productive_research_evidence_accumulation_v1.models_v1 import (
    ProductiveResearchEvidenceRecordV1,
    ValidationStatusV1,
)
from research.canonical_volatility_max_age_productive_research_evidence_accumulation_v1.research_stratification_v2.constants_v2 import (
    EVIDENCE_SCHEMA_VERSION_V2,
    FAIL_CLOSED_STRATUM_VALUES,
    RESEARCH_STRATIFICATION_CONTRACT_VERSION,
)
from research.canonical_volatility_max_age_productive_research_evidence_accumulation_v1.validation_v1 import (
    validate_productive_evidence_record_v1,
)


def _stratum_from_record(
    record: ProductiveResearchEvidenceRecordV1 | Mapping[str, Any],
    field: str,
) -> str | None:
    payload = (
        record.to_dict() if isinstance(record, ProductiveResearchEvidenceRecordV1) else dict(record)
    )
    return payload.get(field)  # type: ignore[return-value]


def is_classified_stratum_v2(value: str | None) -> bool:
    if value is None:
        return False
    text = str(value).strip()
    if not text or text in FAIL_CLOSED_STRATUM_VALUES:
        return False
    return True


def evaluate_coverage_readiness_v2_v1(
    *,
    records: Sequence[ProductiveResearchEvidenceRecordV1 | Mapping[str, Any]],
    minimum_market_regimes: int = 2,
    minimum_volatility_regimes: int = 1,
    expected_stratification_contract_version: str = RESEARCH_STRATIFICATION_CONTRACT_VERSION,
    expected_parameter_digest: str | None = None,
) -> dict[str, Any]:
    gaps: list[str] = []
    valid_v2 = []
    saw_v1 = False
    for record in records:
        payload = (
            record.to_dict()
            if isinstance(record, ProductiveResearchEvidenceRecordV1)
            else dict(record)
        )
        schema = str(payload.get("evidence_schema_version") or "")
        if schema != EVIDENCE_SCHEMA_VERSION_V2:
            saw_v1 = True
            continue
        status, _ = validate_productive_evidence_record_v1(record)
        if status != ValidationStatusV1.VALID:
            gaps.append("INVALID_V2_RECORD")
            continue
        if (
            payload.get("research_stratification_version")
            != expected_stratification_contract_version
        ):
            gaps.append("STRATIFICATION_CONTRACT_VERSION_MISMATCH")
            continue
        if (
            expected_parameter_digest
            and payload.get("stratification_parameter_digest") != expected_parameter_digest
        ):
            gaps.append("STRATIFICATION_PARAMETER_DIGEST_MISMATCH")
            continue
        if not payload.get("stratification_input_provenance"):
            gaps.append("MISSING_STRATIFICATION_PROVENANCE")
            continue
        valid_v2.append(payload)

    if saw_v1 and valid_v2:
        gaps.append("MIXED_V1_V2_SCOPE_FORBIDDEN")
    if not valid_v2:
        gaps.append("NO_V2_EVIDENCE_RECORDS")

    market = sorted(
        {
            str(r.get("market_state_stratum_v2"))
            for r in valid_v2
            if is_classified_stratum_v2(r.get("market_state_stratum_v2"))
        }
    )
    vol = sorted(
        {
            str(r.get("volatility_regime_stratum_v2"))
            for r in valid_v2
            if is_classified_stratum_v2(r.get("volatility_regime_stratum_v2"))
        }
    )

    if len(market) < int(minimum_market_regimes):
        gaps.append("MINIMUM_MARKET_REGIMES")
    if len(vol) < int(minimum_volatility_regimes):
        gaps.append("MINIMUM_VOLATILITY_REGIMES")

    ready = not gaps and bool(valid_v2)
    return {
        "coverage_schema_version": "canonical_volatility_max_age_research_stratification_coverage/v2",
        "distinct_market_state_strata": market,
        "distinct_volatility_regime_strata": vol,
        "market_regime_count": len(market),
        "volatility_regime_count": len(vol),
        "valid_v2_evidence_count": len(valid_v2),
        "coverage_gaps": tuple(sorted(set(gaps))),
        "ready_for_research_execution_v2": ready,
        "mixed_v1_v2_coverage_allowed": False,
    }
