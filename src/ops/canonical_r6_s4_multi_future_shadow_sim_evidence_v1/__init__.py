"""R6 S4 multi-future shadow/sim evidence v1.

Evidence-only overlay over the unauthorized S3 architecture.
Does not authorize Multi-Future runtime, mutate G13, or start S5.
"""

from __future__ import annotations

from src.ops.canonical_r6_s4_multi_future_shadow_sim_evidence_v1.constants_v1 import (
    CAPABILITY_ID,
    CONTRACT_VERSION,
    MULTI_FUTURE_RUNTIME_AUTHORIZED,
    MULTI_FUTURE_RUNTIME_IMPLEMENTED,
    PACKAGE_MARKER,
    REMEDIATION_ID,
    S4_AUTHORIZED,
    S4_EVIDENCE_PREPARED,
)
from src.ops.canonical_r6_s4_multi_future_shadow_sim_evidence_v1.producer_v1 import (
    produce_shadow_sim_evidence_v1,
)
from src.ops.canonical_r6_s4_multi_future_shadow_sim_evidence_v1.verifier_v1 import (
    evaluate_r6_s4_multi_future_shadow_sim_evidence_v1,
)

__all__ = [
    "CAPABILITY_ID",
    "CONTRACT_VERSION",
    "MULTI_FUTURE_RUNTIME_AUTHORIZED",
    "MULTI_FUTURE_RUNTIME_IMPLEMENTED",
    "PACKAGE_MARKER",
    "REMEDIATION_ID",
    "S4_AUTHORIZED",
    "S4_EVIDENCE_PREPARED",
    "evaluate_r6_s4_multi_future_shadow_sim_evidence_v1",
    "produce_shadow_sim_evidence_v1",
]
