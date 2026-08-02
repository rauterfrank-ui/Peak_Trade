"""Single Selected Future Runtime Binding V1 (Capability 2.4).

Consumes Cap 2.3 persisted selection as the sole productive instrument authority
for the canonical analytical runtime host. Does not mutate Master V2 / Double Play,
activation, live/testnet/paper, or authorization.
"""

from __future__ import annotations

from src.ops.single_selected_future_runtime_binding_v1.binding_gate_v1 import (
    run_single_selected_future_runtime_binding_gate_v1,
)
from src.ops.single_selected_future_runtime_binding_v1.constants_v1 import (
    CAPABILITY_ID,
    OWNER,
    PACKAGE_MARKER,
    SCHEMA_VERSION,
    SELECTED_FUTURE_COUNT,
)
from src.ops.single_selected_future_runtime_binding_v1.models_v1 import (
    BoundInstrumentV1,
    RuntimeBindingGateResultV1,
)

__all__ = [
    "CAPABILITY_ID",
    "OWNER",
    "PACKAGE_MARKER",
    "SCHEMA_VERSION",
    "SELECTED_FUTURE_COUNT",
    "BoundInstrumentV1",
    "RuntimeBindingGateResultV1",
    "run_single_selected_future_runtime_binding_gate_v1",
]
