"""R6 S3 Phase-8.2 multi-future runtime architecture v1.

Implementation-only overlay behind fail-closed flags.
Does not authorize Multi-Future runtime, mutate G13, or create a
second execution/accounting writer.
"""

from __future__ import annotations

from src.ops.canonical_r6_s3_multi_future_runtime_architecture_v1.constants_v1 import (
    CAPABILITY_ID,
    CONTRACT_VERSION,
    MULTI_FUTURE_RUNTIME_AUTHORIZED,
    MULTI_FUTURE_RUNTIME_IMPLEMENTED,
    PACKAGE_MARKER,
    REMEDIATION_ID,
)
from src.ops.canonical_r6_s3_multi_future_runtime_architecture_v1.models_v1 import (
    InstrumentContextV1,
    Phase82GraphRequestV1,
    RankingCandidateV1,
    R6S3RuntimeArchitectureError,
)
from src.ops.canonical_r6_s3_multi_future_runtime_architecture_v1.orchestrator_v1 import (
    evaluate_phase_82_graph_v1,
)
from src.ops.canonical_r6_s3_multi_future_runtime_architecture_v1.verifier_v1 import (
    evaluate_r6_s3_multi_future_runtime_architecture_v1,
)

__all__ = [
    "CAPABILITY_ID",
    "CONTRACT_VERSION",
    "InstrumentContextV1",
    "MULTI_FUTURE_RUNTIME_AUTHORIZED",
    "MULTI_FUTURE_RUNTIME_IMPLEMENTED",
    "PACKAGE_MARKER",
    "Phase82GraphRequestV1",
    "R6S3RuntimeArchitectureError",
    "RankingCandidateV1",
    "REMEDIATION_ID",
    "evaluate_phase_82_graph_v1",
    "evaluate_r6_s3_multi_future_runtime_architecture_v1",
]
