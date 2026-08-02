"""Productive Futures Accounting Runtime Binding V1 (Capability 3.1).

Binds the canonical futures_accounting kernel after simulated fill generation and
before portfolio/risk state persistence on the Cap 2.4 productive analytical host.
Does not mutate Master V2 / Double Play / Risk / Safety decision logic, activation,
live/testnet/paper orders, or authorization consumption.
"""

from __future__ import annotations

from src.ops.productive_futures_accounting_runtime_binding_v1.bridge_binding_v1 import (
    apply_intended_action_via_canonical_accounting_v1,
    ensure_accounting_session_v1,
)
from src.ops.productive_futures_accounting_runtime_binding_v1.constants_v1 import (
    CAPABILITY_ID,
    FUTURES_ACCOUNTING_RUNTIME_BOUND,
    OWNER,
    PACKAGE_MARKER,
    SCHEMA_VERSION,
)
from src.ops.productive_futures_accounting_runtime_binding_v1.models_v1 import (
    AccountingApplyResultV1,
    ContractMetadataV1,
)

__all__ = [
    "CAPABILITY_ID",
    "FUTURES_ACCOUNTING_RUNTIME_BOUND",
    "OWNER",
    "PACKAGE_MARKER",
    "SCHEMA_VERSION",
    "AccountingApplyResultV1",
    "ContractMetadataV1",
    "apply_intended_action_via_canonical_accounting_v1",
    "ensure_accounting_session_v1",
]
