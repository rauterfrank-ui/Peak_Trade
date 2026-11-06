"""Canonical F1/M9 durable apply bootstrap for CURRENT productive Master-V2 consumers.

Uses the existing governed apply-start continuation only. No second authority,
no synthetic seam, no numeric policy change.

RUNTIME_AUTHORIZATION_EFFECT=NONE
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Final

from src.governance.f1_m9_productive_apply_ledger_v1 import (
    F1M9ProductiveApplyLedgerPathsV1,
    initialize_empty_revocation_ledger_v1,
)
from src.governance.f1_m9_threshold_value_authorization_ledger_v1 import (
    F1M9ThresholdValueAuthorizationLedgerPathsV1,
    initialize_empty_threshold_revocation_ledger_v1,
)

SCHEMA_VERSION: Final[str] = "current_productive_f1_m9_canonical_durable_bootstrap/v1"
BOOTSTRAP_OWNER: Final[str] = (
    "ops.full_core_live_path_composition_root_v1."
    "current_productive_f1_m9_canonical_durable_bootstrap_v1"
)


@dataclass(frozen=True, slots=True)
class CurrentProductiveF1M9DurableBootstrapResultV1:
    status: str
    blocking_reasons: tuple[str, ...]
    apply_start_status: str | None
    seam_available: bool


def _ensure_empty_revocation_ledgers_v1(
    *,
    apply_ledger_paths: F1M9ProductiveApplyLedgerPathsV1,
    threshold_ledger_paths: F1M9ThresholdValueAuthorizationLedgerPathsV1,
) -> None:
    apply_ledger_paths.apply_ledger_path.parent.mkdir(parents=True, exist_ok=True)
    rev = apply_ledger_paths.revocation_ledger_path
    if not rev.is_file():
        initialize_empty_revocation_ledger_v1(rev)
    threshold_rev = threshold_ledger_paths.threshold_revocation_ledger_path
    if not threshold_rev.is_file():
        initialize_empty_threshold_revocation_ledger_v1(threshold_rev)


def ensure_canonical_f1_m9_runtime_applied_seam_materialized_v1(
    *,
    repo_root: Path,
    apply_ledger_paths: F1M9ProductiveApplyLedgerPathsV1,
    threshold_ledger_paths: F1M9ThresholdValueAuthorizationLedgerPathsV1,
) -> CurrentProductiveF1M9DurableBootstrapResultV1:
    """Materialize durable apply/threshold state via canonical apply-start when needed."""
    from src.governance.governed_f1_m9_productive_runtime_threshold_consumer_wiring_real_mechanical_continuation_v1 import (
        GovernedF1M9ThresholdConsumerWiringRequestV1,
        resolve_runtime_applied_seam_for_consumer_wiring_v1,
    )
    from src.governance.governed_f1_m9_scoped_owner_productive_runtime_apply_start_real_mechanical_continuation_v1 import (
        GovernedF1M9RuntimeApplyStartRequestV1,
        run_governed_f1_m9_scoped_owner_productive_runtime_apply_start_continuation_v1,
    )

    request = GovernedF1M9ThresholdConsumerWiringRequestV1(
        apply_ledger_paths=apply_ledger_paths,
        threshold_ledger_paths=threshold_ledger_paths,
        repo_root=repo_root,
    )
    seam = resolve_runtime_applied_seam_for_consumer_wiring_v1(request)
    if seam is not None:
        return CurrentProductiveF1M9DurableBootstrapResultV1(
            status="ALREADY_MATERIALIZED",
            blocking_reasons=(),
            apply_start_status=None,
            seam_available=True,
        )

    _ensure_empty_revocation_ledgers_v1(
        apply_ledger_paths=apply_ledger_paths,
        threshold_ledger_paths=threshold_ledger_paths,
    )
    apply_start = run_governed_f1_m9_scoped_owner_productive_runtime_apply_start_continuation_v1(
        GovernedF1M9RuntimeApplyStartRequestV1(
            apply_ledger_paths=apply_ledger_paths,
            threshold_ledger_paths=threshold_ledger_paths,
            repo_root=repo_root,
            persist_durable_evidence=False,
            evaluation_time_utc=datetime.now(timezone.utc),
        )
    )
    if apply_start.status != "CONTINUATION_COMPLETE":
        return CurrentProductiveF1M9DurableBootstrapResultV1(
            status="REJECTED",
            blocking_reasons=tuple(apply_start.blocking_reasons),
            apply_start_status=apply_start.status,
            seam_available=False,
        )

    seam_after = resolve_runtime_applied_seam_for_consumer_wiring_v1(request)
    if seam_after is None:
        return CurrentProductiveF1M9DurableBootstrapResultV1(
            status="REJECTED",
            blocking_reasons=("RUNTIME_APPLIED_SEAM_UNAVAILABLE_AFTER_APPLY_START",),
            apply_start_status=apply_start.status,
            seam_available=False,
        )
    return CurrentProductiveF1M9DurableBootstrapResultV1(
        status="BOOTSTRAP_COMPLETE",
        blocking_reasons=(),
        apply_start_status=apply_start.status,
        seam_available=True,
    )


__all__ = [
    "BOOTSTRAP_OWNER",
    "CurrentProductiveF1M9DurableBootstrapResultV1",
    "SCHEMA_VERSION",
    "ensure_canonical_f1_m9_runtime_applied_seam_materialized_v1",
]
