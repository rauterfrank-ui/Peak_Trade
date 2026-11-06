"""Campaign admission gates for research stratification v2."""

from __future__ import annotations

from typing import Any, Mapping, Sequence

from research.canonical_volatility_max_age_productive_research_evidence_accumulation_v1.research_stratification_v2.constants_v2 import (
    RESEARCH_STRATIFICATION_CONTRACT_VERSION,
)
from research.canonical_volatility_max_age_productive_research_evidence_accumulation_v1.research_stratification_v2.parameter_authority_v2 import (
    ParameterAuthorityEntryV2,
    build_production_parameter_authority_surface_v2,
    parameter_authority_complete_v2,
    parameter_authority_digest_v2,
)


def evaluate_v2_campaign_admission_v2(
    *,
    research_stratification_contract_version: str,
    research_stratification_parameter_digest: str | None,
    parameter_entries: Sequence[ParameterAuthorityEntryV2] | None = None,
    preregistration_v2_bound: bool = False,
) -> dict[str, Any]:
    entries = (
        tuple(parameter_entries)
        if parameter_entries is not None
        else build_production_parameter_authority_surface_v2()
    )
    digest = parameter_authority_digest_v2(entries)
    blockers: list[str] = []
    if research_stratification_contract_version != RESEARCH_STRATIFICATION_CONTRACT_VERSION:
        blockers.append("STRATIFICATION_CONTRACT_VERSION_MISMATCH")
    if not preregistration_v2_bound:
        blockers.append("PREREGISTRATION_V2_NOT_BOUND")
    if not parameter_authority_complete_v2(entries):
        blockers.append("PARAMETER_AUTHORITY_INCOMPLETE")
    if (
        research_stratification_parameter_digest
        and research_stratification_parameter_digest != digest
    ):
        blockers.append("PARAMETER_DIGEST_MISMATCH")
    admission = not blockers
    return {
        "research_stratification_v2_campaign_admission": admission,
        "parameter_authority_complete": parameter_authority_complete_v2(entries),
        "parameter_digest": digest,
        "admission_blockers": tuple(sorted(set(blockers))),
    }
