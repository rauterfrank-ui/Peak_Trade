"""Closure proof for governed F1/M9 scoped Owner Apply execution continuation v1."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Final

from src.governance.governed_f1_m9_scoped_owner_apply_execution_real_mechanical_continuation_v1 import (
    DECISION_CONFIG,
    OWNER_WP_DECISION_CONFIG,
    WORKPACKAGE_ID,
    prove_continuation_authority_invariants_v1,
    prove_continuation_decision_files_v1,
)
from src.governance.real_p4_to_f1_m9_apply_lineage_join_v1 import (
    JOIN_STATUS_NOT_CANONICAL,
)

_REPO_ROOT = Path(__file__).resolve().parents[2]


def prove_governed_f1_m9_scoped_owner_apply_execution_v1(*, repo_root: Path | None = None) -> bool:
    root = repo_root or _REPO_ROOT
    if not prove_continuation_decision_files_v1(repo_root=root):
        return False
    decision = json.loads((root / DECISION_CONFIG).read_text(encoding="utf-8"))
    if decision.get("workpackage_id") != WORKPACKAGE_ID:
        return False
    if decision.get("real_p4_to_f1_m9_join_status") != JOIN_STATUS_NOT_CANONICAL:
        return False
    if decision.get("runtime_apply_started") is not False:
        return False
    return prove_continuation_authority_invariants_v1()


__all__ = ["prove_governed_f1_m9_scoped_owner_apply_execution_v1"]
