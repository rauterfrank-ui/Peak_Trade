"""Surface-B Owner/STA regime-coverage producer decision surface v1.

INPUT_AUTHORITY=false
RUNTIME_IMPLEMENTED=false
RAW_INPUT_PACK_CREATED=false
CAMPAIGN_STARTED=false
PRODUCTIVE_NUMERIC_VALUES_SET=0
REGIME_COVERAGE_STATUS=SEMANTICALLY_UNRESOLVED
EXISTING_PRODUCERS_ELEVATED=false
DASHBOARD_AUTHORITY_EFFECT=NONE
"""

from __future__ import annotations

from src.ops.productive_pure_stack_stage2_surface_b_owner_sta_regime_coverage_producer_decision_v1.constants_v1 import (
    CAPABILITY_SCOPE,
    DECISION_ID,
    PACKAGE_MARKER,
)
from src.ops.productive_pure_stack_stage2_surface_b_owner_sta_regime_coverage_producer_decision_v1.validator_v1 import (
    RegimeCoverageProducerDecisionErrorV1,
    load_canonical_regime_coverage_producer_decisions_manifest_v1,
    validate_regime_coverage_owner_choice_v1,
    validate_regime_coverage_producer_manifest_v1,
)

__all__ = [
    "CAPABILITY_SCOPE",
    "DECISION_ID",
    "PACKAGE_MARKER",
    "RegimeCoverageProducerDecisionErrorV1",
    "load_canonical_regime_coverage_producer_decisions_manifest_v1",
    "validate_regime_coverage_owner_choice_v1",
    "validate_regime_coverage_producer_manifest_v1",
]
