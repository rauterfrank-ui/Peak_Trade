"""Single Future Canonical Runtime Deterministic Offline Evidence V1 (Capability 5.1).

Proves the Cap 4.1-closed single-future call graph under deterministic offline
market-data replay without activating runtime, consuming authorization, or
starting a network trading session.
"""

from __future__ import annotations

from src.ops.single_future_canonical_runtime_deterministic_offline_evidence_v1.constants_v1 import (
    CANONICAL_RUNTIME_ENTRYPOINT_STATUS,
    CAPABILITY_ID,
    OWNER,
    PACKAGE_MARKER,
    RUNTIME_ACTIVATED,
    SCHEMA_VERSION,
)
from src.ops.single_future_canonical_runtime_deterministic_offline_evidence_v1.evidence_gate_v1 import (
    run_single_future_canonical_runtime_deterministic_offline_evidence_v1,
)
from src.ops.single_future_canonical_runtime_deterministic_offline_evidence_v1.models_v1 import (
    OfflineEvidenceGateResultV1,
)

__all__ = [
    "CANONICAL_RUNTIME_ENTRYPOINT_STATUS",
    "CAPABILITY_ID",
    "OWNER",
    "PACKAGE_MARKER",
    "RUNTIME_ACTIVATED",
    "SCHEMA_VERSION",
    "OfflineEvidenceGateResultV1",
    "run_single_future_canonical_runtime_deterministic_offline_evidence_v1",
]
