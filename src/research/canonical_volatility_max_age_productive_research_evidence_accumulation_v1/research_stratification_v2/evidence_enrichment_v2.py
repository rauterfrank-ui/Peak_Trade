"""Attach v2 stratification fields to productive evidence (v1 legacy regime preserved)."""

from __future__ import annotations

from typing import Any, Mapping

from research.canonical_volatility_max_age_productive_research_evidence_accumulation_v1.models_v1 import (
    ProductiveResearchEvidenceRecordV1,
)
from research.canonical_volatility_max_age_productive_research_evidence_accumulation_v1.validation_v1 import (
    attach_validation_v1,
    finalize_record_digest_v1,
    productive_record_from_mapping_v1,
)
from research.canonical_volatility_max_age_productive_research_evidence_accumulation_v1.research_stratification_v2.compute_v2 import (
    cmc_from_cycle_binding_v2,
    compute_research_stratification_v2,
)
from research.canonical_volatility_max_age_productive_research_evidence_accumulation_v1.research_stratification_v2.constants_v2 import (
    EVIDENCE_SCHEMA_VERSION_V2,
)
from research.canonical_volatility_max_age_productive_research_evidence_accumulation_v1.research_stratification_v2.mark_path_v2 import (
    ResearchObservationMarkPathStateV2,
    extract_cycle_mark_price_v2,
)
from research.canonical_volatility_max_age_productive_research_evidence_accumulation_v1.research_stratification_v2.models_v2 import (
    ResearchStratificationBindingV2,
)
from research.canonical_volatility_max_age_productive_research_evidence_accumulation_v1.research_stratification_v2.parameter_authority_v2 import (
    build_production_parameter_authority_surface_v2,
)


def enrich_productive_record_with_stratification_v2(
    record: ProductiveResearchEvidenceRecordV1,
    *,
    cycle: Mapping[str, Any],
    binding: ResearchStratificationBindingV2,
    mark_path_state: ResearchObservationMarkPathStateV2,
) -> ProductiveResearchEvidenceRecordV1:
    if not binding.enabled:
        return record
    mark = extract_cycle_mark_price_v2(dict(cycle))
    if mark is not None:
        mark_path_state.append_mark(mark)
    cmc = cmc_from_cycle_binding_v2(cycle)
    params = (
        tuple(binding.parameter_entries_override)
        if binding.parameter_entries_override is not None
        else build_production_parameter_authority_surface_v2()
    )
    strat = compute_research_stratification_v2(
        cmc=cmc,
        mark_prices=mark_path_state.mark_prices,
        parameter_entries=params,
        expected_parameter_digest=binding.research_stratification_parameter_digest,
        legacy_regime_label_v1=record.regime_label,
    )
    payload = record.to_dict()
    payload["evidence_schema_version"] = EVIDENCE_SCHEMA_VERSION_V2
    payload.update(strat.to_evidence_fields_v2())
    payload["legacy_regime_label_v1"] = record.regime_label
    payload["legacy_regime_label_is_v1"] = True
    payload["record_digest"] = finalize_record_digest_v1(payload)
    enriched = productive_record_from_mapping_v1(payload)
    return attach_validation_v1(enriched)
