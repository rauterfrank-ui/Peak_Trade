"""Canonical durable ledger path resolution for F1/M9 scoped Owner Apply (paths only)."""

from __future__ import annotations

from pathlib import Path
from typing import Final

from src.governance.f1_m9_productive_apply_execution_boundary_v1 import (
    load_execution_boundary_decision_v1,
)
from src.governance.f1_m9_productive_apply_ledger_v1 import F1M9ProductiveApplyLedgerPathsV1

SCHEMA_VERSION: Final[str] = "f1_m9_productive_apply_durable_ledger_paths/v1"


class F1M9DurableLedgerPathsError(ValueError):
    """Fail-closed durable ledger path resolution error."""


def resolve_canonical_f1_m9_productive_apply_ledger_paths_v1(
    *,
    repo_root: Path | None = None,
) -> F1M9ProductiveApplyLedgerPathsV1:
    root = repo_root or Path(__file__).resolve().parents[2]
    decision = load_execution_boundary_decision_v1(repo_root=root)
    if decision.get("durable_ledger_paths_defined") is not True:
        raise F1M9DurableLedgerPathsError("DURABLE_LEDGER_PATHS_NOT_DEFINED")
    apply_rel = decision.get("durable_apply_ledger_path")
    rev_rel = decision.get("durable_revocation_ledger_path")
    if not isinstance(apply_rel, str) or not apply_rel.strip():
        raise F1M9DurableLedgerPathsError("DURABLE_APPLY_LEDGER_PATH_MISSING")
    if not isinstance(rev_rel, str) or not rev_rel.strip():
        raise F1M9DurableLedgerPathsError("DURABLE_REVOCATION_LEDGER_PATH_MISSING")
    apply_path = (root / apply_rel).resolve()
    rev_path = (root / rev_rel).resolve()
    try:
        apply_path.relative_to(root.resolve())
        rev_path.relative_to(root.resolve())
    except ValueError as exc:
        raise F1M9DurableLedgerPathsError("DURABLE_LEDGER_PATH_OUTSIDE_REPO") from exc
    return F1M9ProductiveApplyLedgerPathsV1(
        apply_ledger_path=apply_path,
        revocation_ledger_path=rev_path,
    )


__all__ = [
    "F1M9DurableLedgerPathsError",
    "SCHEMA_VERSION",
    "resolve_canonical_f1_m9_productive_apply_ledger_paths_v1",
]
