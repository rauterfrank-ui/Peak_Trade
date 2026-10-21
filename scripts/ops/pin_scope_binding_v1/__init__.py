"""Reusable pin and scope binding. AUTHORITY=NONE. No guardian identity."""

from scripts.ops.pin_scope_binding_v1.bind_v1 import bind_pin_and_scope_v1
from scripts.ops.pin_scope_binding_v1.constants_v1 import (
    AUTHORITY,
    GUARDIAN_IDENTITY,
    STATUS_ACCEPTED,
    STATUS_FORGED_PROVENANCE,
    STATUS_INPUT_SOURCE_STALE,
    STATUS_INVALID_PROVENANCE,
    STATUS_INVALID_SCOPE,
    STATUS_PIN_MISMATCH,
    STATUS_POLICY_CONFLICT,
    STATUS_SCOPE_CONFLICT,
    STATUS_SCOPE_EMPTY,
)

__all__ = [
    "AUTHORITY",
    "GUARDIAN_IDENTITY",
    "STATUS_ACCEPTED",
    "STATUS_FORGED_PROVENANCE",
    "STATUS_INPUT_SOURCE_STALE",
    "STATUS_POLICY_CONFLICT",
    "STATUS_INVALID_PROVENANCE",
    "STATUS_INVALID_SCOPE",
    "STATUS_PIN_MISMATCH",
    "STATUS_SCOPE_CONFLICT",
    "STATUS_SCOPE_EMPTY",
    "bind_pin_and_scope_v1",
]
