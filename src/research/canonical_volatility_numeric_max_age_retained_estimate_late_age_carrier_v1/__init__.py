"""R1 retained-estimate late-age lifecycle carrier — research evidence only.

PRODUCTION_AUTHORITY_EFFECT=NONE. Does not alter MV2+Double-Play trading
authority, mark-history schema, regime pipeline, or M9 enforcement.
"""

from __future__ import annotations

from research.canonical_volatility_numeric_max_age_retained_estimate_late_age_carrier_v1.architecture_guards_v1 import (
    assert_retained_estimate_late_age_architecture_guards_v1,
)
from research.canonical_volatility_numeric_max_age_retained_estimate_late_age_carrier_v1.carrier_v1 import (
    build_retained_estimate_lifecycle_carrier_payload_v1,
    load_retained_estimate_lifecycle_carrier_v1,
    verify_retained_estimate_lifecycle_carrier_binding_v1,
    write_retained_estimate_lifecycle_carrier_once_v1,
)
from research.canonical_volatility_numeric_max_age_retained_estimate_late_age_carrier_v1.constants_v1 import (
    CARRIER_FILENAME,
    PACKAGE_MARKER,
    PRODUCTION_AUTHORITY_EFFECT,
    SCHEMA_VERSION,
)
from research.canonical_volatility_numeric_max_age_retained_estimate_late_age_carrier_v1.hold_v1 import (
    empty_age_bucket_observation_counts_v1,
    prereg_age_grid_coverage_complete_v1,
    record_age_bucket_observation_v1,
)
from research.canonical_volatility_numeric_max_age_retained_estimate_late_age_carrier_v1.models_v1 import (
    RetainedEstimateLateAgeCarrierError,
    RetainedEstimateLifecycleCarrierV1,
    estimate_id_from_source_digest_v1,
)

__all__ = [
    "CARRIER_FILENAME",
    "PACKAGE_MARKER",
    "PRODUCTION_AUTHORITY_EFFECT",
    "SCHEMA_VERSION",
    "RetainedEstimateLateAgeCarrierError",
    "RetainedEstimateLifecycleCarrierV1",
    "assert_retained_estimate_late_age_architecture_guards_v1",
    "build_retained_estimate_lifecycle_carrier_payload_v1",
    "empty_age_bucket_observation_counts_v1",
    "estimate_id_from_source_digest_v1",
    "load_retained_estimate_lifecycle_carrier_v1",
    "prereg_age_grid_coverage_complete_v1",
    "record_age_bucket_observation_v1",
    "verify_retained_estimate_lifecycle_carrier_binding_v1",
    "write_retained_estimate_lifecycle_carrier_once_v1",
]
