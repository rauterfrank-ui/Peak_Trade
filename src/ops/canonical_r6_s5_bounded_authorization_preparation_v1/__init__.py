"""R6 S5 bounded-authorization preparation v1.

Preparation-only overlay. Does not grant Multi-Future authorization,
mutate G13, ratify N>1, or start S6.
"""

from __future__ import annotations

from src.ops.canonical_r6_s5_bounded_authorization_preparation_v1.constants_v1 import (
    CAPABILITY_ID,
    CONTRACT_VERSION,
    MULTI_FUTURE_RUNTIME_AUTHORIZED,
    MULTI_FUTURE_RUNTIME_IMPLEMENTED,
    PACKAGE_MARKER,
    PREPARATION_IS_NOT_AUTHORIZATION,
    REMEDIATION_ID,
    S5_AUTHORIZATION_GRANTED,
    S5_PREPARED,
)
from src.ops.canonical_r6_s5_bounded_authorization_preparation_v1.producer_v1 import (
    produce_bounded_authorization_preparation_v1,
)
from src.ops.canonical_r6_s5_bounded_authorization_preparation_v1.verifier_v1 import (
    evaluate_r6_s5_bounded_authorization_preparation_v1,
)

__all__ = [
    "CAPABILITY_ID",
    "CONTRACT_VERSION",
    "MULTI_FUTURE_RUNTIME_AUTHORIZED",
    "MULTI_FUTURE_RUNTIME_IMPLEMENTED",
    "PACKAGE_MARKER",
    "PREPARATION_IS_NOT_AUTHORIZATION",
    "REMEDIATION_ID",
    "S5_AUTHORIZATION_GRANTED",
    "S5_PREPARED",
    "evaluate_r6_s5_bounded_authorization_preparation_v1",
    "produce_bounded_authorization_preparation_v1",
]
