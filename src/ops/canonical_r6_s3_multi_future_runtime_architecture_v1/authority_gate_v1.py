"""Fail-closed authorization gate for R6 S3.

IMPLEMENTED and AUTHORIZED are independent. AUTHORIZED is never derived
from IMPLEMENTED. Missing/unknown/false authorization fail-closes the
effective runtime to SINGLE_SELECTED_FUTURE with MAX_POSITIONS_EFFECTIVE=1
and no submit unlock.
"""

from __future__ import annotations

from types import MappingProxyType
from typing import Any, Mapping

from src.ops.canonical_r6_s3_multi_future_runtime_architecture_v1.constants_v1 import (
    AUTHORIZED_NOT_DERIVED_FROM_IMPLEMENTED,
    CANARY_AUTHORIZED,
    CURRENT_EFFECTIVE_RUNTIME_MODE,
    IMPLEMENTED_DOES_NOT_IMPLY_AUTHORIZED,
    LIVE_AUTHORIZED,
    MAX_POSITIONS_EFFECTIVE,
    MULTI_FUTURE_RUNTIME_AUTHORIZED,
    MULTI_FUTURE_RUNTIME_IMPLEMENTED,
    SUBMIT_UNLOCKED,
    TESTNET_AUTHORIZED,
)
from src.ops.canonical_r6_s3_multi_future_runtime_architecture_v1.models_v1 import (
    Phase82GraphRequestV1,
    R6S3RuntimeArchitectureError,
)


def _reject(message: str) -> None:
    raise R6S3RuntimeArchitectureError(message)


def resolve_authority_flags_v1(request: Phase82GraphRequestV1) -> Mapping[str, Any]:
    implemented = MULTI_FUTURE_RUNTIME_IMPLEMENTED
    if request.requested_implemented is False:
        implemented = False
    authorized_constant = MULTI_FUTURE_RUNTIME_AUTHORIZED
    requested = request.requested_authorized
    if requested is True:
        _reject("multi_future_runtime_authorized_rejected_g13")
    if requested not in (None, False):
        _reject("multi_future_runtime_authorized_unknown")
    authorized = False
    if authorized_constant is True:
        _reject("package_authorized_flag_must_remain_false")
    if implemented is True and authorized is True:
        _reject("authorized_derived_from_implemented")
    if authorized is not False:
        _reject("authorization_missing_or_unknown")
    return MappingProxyType(
        {
            "implemented": bool(implemented),
            "authorized": False,
            "effective_runtime_mode": CURRENT_EFFECTIVE_RUNTIME_MODE,
            "max_positions_effective": MAX_POSITIONS_EFFECTIVE,
            "submit_unlocked": SUBMIT_UNLOCKED,
            "live_authorized": LIVE_AUTHORIZED,
            "testnet_authorized": TESTNET_AUTHORIZED,
            "canary_authorized": CANARY_AUTHORIZED,
            "implemented_does_not_imply_authorized": IMPLEMENTED_DOES_NOT_IMPLY_AUTHORIZED,
            "authorized_not_derived_from_implemented": AUTHORIZED_NOT_DERIVED_FROM_IMPLEMENTED,
        }
    )
