"""Shared F1/M9 durable ledger + seam materialization for CURRENT productive ops tests."""

from __future__ import annotations

from pathlib import Path

from src.governance.f1_m9_productive_apply_ledger_v1 import (
    F1M9ProductiveApplyLedgerPathsV1,
    initialize_empty_revocation_ledger_v1,
)
from src.governance.f1_m9_threshold_value_authorization_ledger_v1 import (
    F1M9ThresholdValueAuthorizationLedgerPathsV1,
    initialize_empty_threshold_revocation_ledger_v1,
)
from src.governance.governed_f1_m9_scoped_owner_productive_runtime_apply_start_real_mechanical_continuation_v1 import (
    GovernedF1M9RuntimeApplyStartRequestV1,
    run_governed_f1_m9_scoped_owner_productive_runtime_apply_start_continuation_v1,
)

REPO_ROOT = Path(__file__).resolve().parents[2]


def f1_m9_apply_ledger_paths_v1(tmp_path: Path) -> F1M9ProductiveApplyLedgerPathsV1:
    rev = tmp_path / "apply_revocation.jsonl"
    initialize_empty_revocation_ledger_v1(rev)
    return F1M9ProductiveApplyLedgerPathsV1(
        apply_ledger_path=tmp_path / "apply_ledger.jsonl",
        revocation_ledger_path=rev,
    )


def f1_m9_threshold_ledger_paths_v1(tmp_path: Path) -> F1M9ThresholdValueAuthorizationLedgerPathsV1:
    rev = tmp_path / "threshold_revocation.jsonl"
    initialize_empty_threshold_revocation_ledger_v1(rev)
    return F1M9ThresholdValueAuthorizationLedgerPathsV1(
        threshold_ledger_path=tmp_path / "threshold_ledger.jsonl",
        threshold_revocation_ledger_path=rev,
    )


def materialize_f1_m9_runtime_applied_seam_ledgers_v1(tmp_path: Path) -> dict[str, object]:
    """Run canonical apply-start once; return ledger paths and bound seam record."""
    apply_paths = f1_m9_apply_ledger_paths_v1(tmp_path)
    threshold_paths = f1_m9_threshold_ledger_paths_v1(tmp_path)
    result = run_governed_f1_m9_scoped_owner_productive_runtime_apply_start_continuation_v1(
        GovernedF1M9RuntimeApplyStartRequestV1(
            apply_ledger_paths=apply_paths,
            threshold_ledger_paths=threshold_paths,
            repo_root=REPO_ROOT,
        )
    )
    assert result.status == "CONTINUATION_COMPLETE", result.blocking_reasons
    assert result.bound_seam_record is not None
    return {
        "apply_ledger_paths": apply_paths,
        "threshold_ledger_paths": threshold_paths,
        "bound_seam_record": dict(result.bound_seam_record),
    }
