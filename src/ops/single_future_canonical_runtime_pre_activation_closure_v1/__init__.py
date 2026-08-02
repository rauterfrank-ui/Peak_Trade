"""Single Future Canonical Runtime Pre-Activation Closure V1 (Capability 4.1).

Closes the full single-future productive call graph to READY_FOR_ACTIVATION without
activating runtime, consuming authorization, or starting a network trading session.
Reuses Cap 2.4 productive host + Cap 1.1–3.1 owners; does not create a second host.
"""

from __future__ import annotations

from src.ops.single_future_canonical_runtime_pre_activation_closure_v1.constants_v1 import (
    CANONICAL_RUNTIME_ENTRYPOINT_STATUS,
    CAPABILITY_ID,
    OWNER,
    PACKAGE_MARKER,
    RUNTIME_ACTIVATED,
    SCHEMA_VERSION,
)
from src.ops.single_future_canonical_runtime_pre_activation_closure_v1.models_v1 import (
    PreActivationGateResultV1,
)
from src.ops.single_future_canonical_runtime_pre_activation_closure_v1.pre_activation_gate_v1 import (
    run_single_future_canonical_runtime_pre_activation_closure_v1,
)

__all__ = [
    "CANONICAL_RUNTIME_ENTRYPOINT_STATUS",
    "CAPABILITY_ID",
    "OWNER",
    "PACKAGE_MARKER",
    "RUNTIME_ACTIVATED",
    "SCHEMA_VERSION",
    "PreActivationGateResultV1",
    "run_single_future_canonical_runtime_pre_activation_closure_v1",
]
