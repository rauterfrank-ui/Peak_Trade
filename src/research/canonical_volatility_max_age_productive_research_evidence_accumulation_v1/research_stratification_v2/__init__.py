"""Research-only max-age stratification v2 (decoupled from bridge feature_regime)."""

from research.canonical_volatility_max_age_productive_research_evidence_accumulation_v1.research_stratification_v2.admission_v2 import (
    evaluate_v2_campaign_admission_v2,
)
from research.canonical_volatility_max_age_productive_research_evidence_accumulation_v1.research_stratification_v2.compute_v2 import (
    compute_research_stratification_v2,
)
from research.canonical_volatility_max_age_productive_research_evidence_accumulation_v1.research_stratification_v2.constants_v2 import (
    RESEARCH_STRATIFICATION_CONTRACT_VERSION,
)

__all__ = [
    "RESEARCH_STRATIFICATION_CONTRACT_VERSION",
    "compute_research_stratification_v2",
    "evaluate_v2_campaign_admission_v2",
]
