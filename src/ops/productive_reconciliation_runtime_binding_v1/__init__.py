"""Productive Reconciliation Runtime Binding V1 (Capability 1.1).

Binds reconciliation as a mandatory startup gate before the first decision
cycle of the canonical analytical runtime host. Does not mutate Master V2 /
Double Play trading logic, activation, live/testnet/paper, or authorization.
"""

from __future__ import annotations

from src.ops.productive_reconciliation_runtime_binding_v1.constants_v1 import (
    CAPABILITY_ID,
    OWNER,
    PACKAGE_MARKER,
    PRODUCTIVE_RECONCILIATION_BOUND,
    SCHEMA_VERSION,
)
from src.ops.productive_reconciliation_runtime_binding_v1.models_v1 import (
    PortfolioTruthSnapshotV1,
    PositionTruthV1,
    ProductiveReconciliationGateResultV1,
)
from src.ops.productive_reconciliation_runtime_binding_v1.startup_gate_v1 import (
    run_productive_reconciliation_startup_gate_v1,
)
from src.ops.productive_reconciliation_runtime_binding_v1.taxonomy_v1 import (
    ProductiveReconciliationClass,
)

__all__ = [
    "CAPABILITY_ID",
    "OWNER",
    "PACKAGE_MARKER",
    "PRODUCTIVE_RECONCILIATION_BOUND",
    "SCHEMA_VERSION",
    "PortfolioTruthSnapshotV1",
    "PositionTruthV1",
    "ProductiveReconciliationClass",
    "ProductiveReconciliationGateResultV1",
    "run_productive_reconciliation_startup_gate_v1",
]
