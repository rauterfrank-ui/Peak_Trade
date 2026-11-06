"""Canonical I04/I05/I55 alt-data consumer boundary v1 (EG-ALT-CONSUMER).

Read-only forensic matrix and fail-closed verifier. Not a consumer wiring
layer. Not a second feature, suitability, selection, or regime/meta owner.
"""

from __future__ import annotations

from src.features.canonical_alt_data_consumer_boundary_v1.constants_v1 import (
    CAPABILITY_ID,
    CONTRACT_VERSION,
    PACKAGE_MARKER,
    REMEDIATION_ID,
    TARGET_BINDING,
)
from src.features.canonical_alt_data_consumer_boundary_v1.matrix_v1 import (
    CONSUMER_MATRIX,
    require_consumer,
    require_producer,
    require_row,
    require_schema,
)
from src.features.canonical_alt_data_consumer_boundary_v1.models_v1 import (
    AltDataConsumerBoundaryError,
    PathClass,
)
from src.features.canonical_alt_data_consumer_boundary_v1.verifier_v1 import (
    evaluate_eg_alt_consumer_v1,
)

__all__ = [
    "CAPABILITY_ID",
    "CONSUMER_MATRIX",
    "CONTRACT_VERSION",
    "PACKAGE_MARKER",
    "PathClass",
    "REMEDIATION_ID",
    "TARGET_BINDING",
    "AltDataConsumerBoundaryError",
    "evaluate_eg_alt_consumer_v1",
    "require_consumer",
    "require_producer",
    "require_row",
    "require_schema",
]
