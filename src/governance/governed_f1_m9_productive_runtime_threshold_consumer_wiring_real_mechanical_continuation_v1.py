"""Governed F1/M9 productive runtime threshold consumer wiring continuation v1."""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Final, Mapping

from src.governance.f1_m9_productive_apply_ledger_v1 import F1M9ProductiveApplyLedgerPathsV1
from src.governance.f1_m9_productive_runtime_threshold_consumer_wiring_v1 import (
    DECISION_CONFIG,
    OWNER_WP_DECISION_CONFIG,
    WORKPACKAGE_ID,
)
from src.governance.f1_m9_threshold_value_authorization_ledger_v1 import (
    F1M9ThresholdValueAuthorizationLedgerPathsV1,
)
from src.governance.governed_f1_m9_scoped_owner_productive_runtime_apply_start_real_mechanical_continuation_v1 import (
    GovernedF1M9RuntimeApplyStartRequestV1,
    run_governed_f1_m9_scoped_owner_productive_runtime_apply_start_continuation_v1,
)
from src.governance.real_p4_to_f1_m9_apply_lineage_join_v1 import JOIN_STATUS_NOT_CANONICAL

SCHEMA_VERSION: Final[str] = (
    "governed_f1_m9_productive_runtime_threshold_consumer_wiring_real_mechanical_continuation_v1"
)
NORMATIVE_SPEC: Final[str] = (
    "docs/ops/specs/"
    "GOVERNED_F1_M9_PRODUCTIVE_RUNTIME_THRESHOLD_CONSUMER_WIRING_REAL_MECHANICAL_CONTINUATION_V1.md"
)

PRODUCTIVE_ACTIVATION_AUTHORIZED: Final[bool] = False
REAL_P4_TO_F1_M9_JOIN_STATUS: Final[str] = JOIN_STATUS_NOT_CANONICAL

_REPO_ROOT = Path(__file__).resolve().parents[2]


@dataclass(frozen=True, slots=True)
class GovernedF1M9ThresholdConsumerWiringRequestV1:
    apply_ledger_paths: F1M9ProductiveApplyLedgerPathsV1
    threshold_ledger_paths: F1M9ThresholdValueAuthorizationLedgerPathsV1
    repo_root: Path | None = None


@dataclass(frozen=True, slots=True)
class GovernedF1M9ThresholdConsumerWiringResultV1:
    status: str
    blocking_reasons: tuple[str, ...]
    threshold_runtime_consumer_status: str
    bound_seam_record: Mapping[str, Any] | None

    def to_dict(self) -> dict[str, Any]:
        return {
            "blocking_reasons": list(self.blocking_reasons),
            "bound_seam_record_digest": (
                str(self.bound_seam_record.get("seam_digest"))
                if isinstance(self.bound_seam_record, Mapping)
                and self.bound_seam_record.get("seam_digest")
                else None
            ),
            "status": self.status,
            "threshold_runtime_consumer_status": self.threshold_runtime_consumer_status,
        }


def resolve_runtime_applied_seam_for_consumer_wiring_v1(
    request: GovernedF1M9ThresholdConsumerWiringRequestV1,
) -> Mapping[str, Any] | None:
    """Reuse canonical apply-start chain; no parallel seam authority."""
    root = request.repo_root or _REPO_ROOT
    apply_start = run_governed_f1_m9_scoped_owner_productive_runtime_apply_start_continuation_v1(
        GovernedF1M9RuntimeApplyStartRequestV1(
            apply_ledger_paths=request.apply_ledger_paths,
            threshold_ledger_paths=request.threshold_ledger_paths,
            repo_root=root,
            persist_durable_evidence=False,
            evaluation_time_utc=datetime.now(timezone.utc),
        )
    )
    if apply_start.status != "CONTINUATION_COMPLETE":
        return None
    if apply_start.bound_seam_record is None:
        return None
    return dict(apply_start.bound_seam_record)


def run_governed_f1_m9_productive_runtime_threshold_consumer_wiring_continuation_v1(
    request: GovernedF1M9ThresholdConsumerWiringRequestV1,
) -> GovernedF1M9ThresholdConsumerWiringResultV1:
    seam = resolve_runtime_applied_seam_for_consumer_wiring_v1(request)
    if seam is None:
        return GovernedF1M9ThresholdConsumerWiringResultV1(
            status="REJECTED",
            blocking_reasons=("RUNTIME_APPLIED_SEAM_UNAVAILABLE",),
            threshold_runtime_consumer_status="DENIED_FAIL_CLOSED",
            bound_seam_record=None,
        )
    if seam.get("runtime_applied") is not True:
        return GovernedF1M9ThresholdConsumerWiringResultV1(
            status="REJECTED",
            blocking_reasons=("CONFIGURATION_RUNTIME_APPLIED_REQUIRED",),
            threshold_runtime_consumer_status="DENIED_FAIL_CLOSED",
            bound_seam_record=seam,
        )
    return GovernedF1M9ThresholdConsumerWiringResultV1(
        status="CONTINUATION_COMPLETE",
        blocking_reasons=(),
        threshold_runtime_consumer_status="PRESENCE_GATE_TRANSPORT_READY",
        bound_seam_record=seam,
    )


def prove_continuation_decision_files_v1(*, repo_root: Path | None = None) -> bool:
    root = repo_root or _REPO_ROOT
    paths = (
        DECISION_CONFIG,
        OWNER_WP_DECISION_CONFIG,
        NORMATIVE_SPEC,
        "src/governance/f1_m9_productive_runtime_threshold_consumer_wiring_v1.py",
        "tests/governance/test_governed_f1_m9_productive_runtime_threshold_consumer_wiring_real_mechanical_continuation_v1.py",
    )
    if not all((root / rel).is_file() for rel in paths):
        return False
    decision = json.loads((root / DECISION_CONFIG).read_text(encoding="utf-8"))
    return decision.get("workpackage_id") == WORKPACKAGE_ID


__all__ = [
    "DECISION_CONFIG",
    "GovernedF1M9ThresholdConsumerWiringRequestV1",
    "GovernedF1M9ThresholdConsumerWiringResultV1",
    "NORMATIVE_SPEC",
    "OWNER_WP_DECISION_CONFIG",
    "PRODUCTIVE_ACTIVATION_AUTHORIZED",
    "REAL_P4_TO_F1_M9_JOIN_STATUS",
    "SCHEMA_VERSION",
    "WORKPACKAGE_ID",
    "prove_continuation_decision_files_v1",
    "resolve_runtime_applied_seam_for_consumer_wiring_v1",
    "run_governed_f1_m9_productive_runtime_threshold_consumer_wiring_continuation_v1",
]
