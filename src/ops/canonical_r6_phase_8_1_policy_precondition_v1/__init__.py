"""R6 Phase-8.1 policy precondition v1.

Read-only forensic overlay. Does not implement Multi-Future runtime,
change G13, or claim SINGLE_FUTURE_LIVE_PROOF.
"""

from __future__ import annotations

from src.ops.canonical_r6_phase_8_1_policy_precondition_v1.checklist_v1 import (
    S1_CHECKLIST,
    require_item,
)
from src.ops.canonical_r6_phase_8_1_policy_precondition_v1.constants_v1 import (
    CAPABILITY_ID,
    CONTRACT_VERSION,
    PACKAGE_MARKER,
    REMEDIATION_ID,
)
from src.ops.canonical_r6_phase_8_1_policy_precondition_v1.models_v1 import (
    PolicyItemStatus,
    R6Phase81PolicyError,
)
from src.ops.canonical_r6_phase_8_1_policy_precondition_v1.verifier_v1 import (
    evaluate_r6_phase_8_1_policy_precondition_v1,
)

__all__ = [
    "CAPABILITY_ID",
    "CONTRACT_VERSION",
    "PACKAGE_MARKER",
    "PolicyItemStatus",
    "R6Phase81PolicyError",
    "REMEDIATION_ID",
    "S1_CHECKLIST",
    "evaluate_r6_phase_8_1_policy_precondition_v1",
    "require_item",
]
