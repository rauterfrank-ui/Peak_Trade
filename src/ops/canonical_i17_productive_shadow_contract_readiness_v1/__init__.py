"""R4 I17 PRODUCTIVE_SHADOW contract/evidence readiness v1.

Additive, fail-closed, non-activating. Reuses existing I17 owners.
Does not execute productive shadow, network, orders, or promotion.
"""

from __future__ import annotations

from src.ops.canonical_i17_productive_shadow_contract_readiness_v1.constants_v1 import (
    CANONICAL_SHADOW_CONTRACT_OWNER,
    CANONICAL_SHADOW_EVIDENCE_OWNER,
    CANONICAL_SHADOW_IDENTITY_BINDING,
    CANONICAL_SHADOW_RUNNER_OWNER,
    CAPABILITY_ID,
    CONTRACT_VERSION,
    PACKAGE_MARKER,
    REMEDIATION_ID,
)
from src.ops.canonical_i17_productive_shadow_contract_readiness_v1.models_v1 import (
    I17ShadowContractReadinessError,
    ShadowMode,
)
from src.ops.canonical_i17_productive_shadow_contract_readiness_v1.preflight_v1 import (
    run_shadow_readiness_preflight_v1,
)
from src.ops.canonical_i17_productive_shadow_contract_readiness_v1.verifier_v1 import (
    evaluate_r4_i17_shadow_contract_readiness_v1,
)

__all__ = [
    "CANONICAL_SHADOW_CONTRACT_OWNER",
    "CANONICAL_SHADOW_EVIDENCE_OWNER",
    "CANONICAL_SHADOW_IDENTITY_BINDING",
    "CANONICAL_SHADOW_RUNNER_OWNER",
    "CAPABILITY_ID",
    "CONTRACT_VERSION",
    "I17ShadowContractReadinessError",
    "PACKAGE_MARKER",
    "REMEDIATION_ID",
    "ShadowMode",
    "evaluate_r4_i17_shadow_contract_readiness_v1",
    "run_shadow_readiness_preflight_v1",
]
