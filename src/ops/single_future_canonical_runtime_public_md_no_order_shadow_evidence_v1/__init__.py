"""Single Future Canonical Runtime Public-MD No-Order Shadow Evidence V1 (Capability 5.2).

Captures public market data, consumes Cap-5.2 authorization once, and proves the
Cap 4.1/5.1-closed single-future call graph under a no-order shadow path without
activating runtime or enabling live/testnet/paper order execution.
"""

from __future__ import annotations

from src.ops.single_future_canonical_runtime_public_md_no_order_shadow_evidence_v1.constants_v1 import (
    CANONICAL_RUNTIME_ENTRYPOINT_STATUS,
    CAPABILITY_ID,
    OWNER,
    PACKAGE_MARKER,
    RUNTIME_ACTIVATED,
    SCHEMA_VERSION,
)
from src.ops.single_future_canonical_runtime_public_md_no_order_shadow_evidence_v1.evidence_gate_v1 import (
    run_single_future_canonical_runtime_public_md_no_order_shadow_evidence_v1,
)
from src.ops.single_future_canonical_runtime_public_md_no_order_shadow_evidence_v1.models_v1 import (
    PublicMdShadowGateResultV1,
)

__all__ = [
    "CANONICAL_RUNTIME_ENTRYPOINT_STATUS",
    "CAPABILITY_ID",
    "OWNER",
    "PACKAGE_MARKER",
    "RUNTIME_ACTIVATED",
    "SCHEMA_VERSION",
    "PublicMdShadowGateResultV1",
    "run_single_future_canonical_runtime_public_md_no_order_shadow_evidence_v1",
]
