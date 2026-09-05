"""Sibling GET-only producer for STEP-29P fresh venue evidence.

Not a Full-Core package. Not a second capital-admission authority.
Does not POST. Does not construct LiveExecutionPort. Does not arm Live.
"""

from __future__ import annotations

from src.ops.full_core_step_29p_fresh_venue_evidence_v1.constants_v1 import (
    AUTHORIZED_HOST,
    OWNER_GO,
    THIS_SLICE,
)
from src.ops.full_core_step_29p_fresh_venue_evidence_v1.requirement_matrix_v1 import (
    FRESH_EVIDENCE_REQUIREMENT_MATRIX,
)

__all__ = (
    "AUTHORIZED_HOST",
    "FRESH_EVIDENCE_REQUIREMENT_MATRIX",
    "OWNER_GO",
    "THIS_SLICE",
)
