"""Closure proof for governed runtime apply materialization v1."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Final

from src.governance.governed_p4_l6_seam_to_runtime_apply_materialization_real_mechanical_continuation_v1 import (
    DECISION_CONFIG,
    WORKPACKAGE_ID,
    prove_continuation_authority_invariants_v1,
    prove_continuation_decision_files_v1,
)
from src.governance.governed_runtime_apply_materialization_v1 import (
    NORMATIVE_SPEC,
    OWNER_WP_DECISION_CONFIG,
    RUNTIME_APPLY_STARTED,
    prove_negative_runtime_apply_materialization_safety_invariants_v1,
)

_REPO_ROOT = Path(__file__).resolve().parents[2]


def prove_governed_runtime_apply_materialization_v1(*, repo_root: Path | None = None) -> bool:
    root = repo_root or _REPO_ROOT
    if not prove_continuation_decision_files_v1(repo_root=root):
        return False
    decision = json.loads((root / DECISION_CONFIG).read_text(encoding="utf-8"))
    owner = json.loads((root / OWNER_WP_DECISION_CONFIG).read_text(encoding="utf-8"))
    if decision.get("workpackage_id") != WORKPACKAGE_ID:
        return False
    if owner.get("runtime_apply_wp_authorized") is not True:
        return False
    if decision.get("runtime_apply_started") is not False:
        return False
    if RUNTIME_APPLY_STARTED is not False:
        return False
    required = (
        NORMATIVE_SPEC,
        DECISION_CONFIG,
        OWNER_WP_DECISION_CONFIG,
        "src/governance/governed_runtime_apply_materialization_v1.py",
        "src/governance/governed_runtime_apply_materialization_record_v1.py",
        "tests/governance/test_governed_runtime_apply_materialization_v1.py",
    )
    if not all((root / rel).is_file() for rel in required):
        return False
    return (
        prove_negative_runtime_apply_materialization_safety_invariants_v1()
        and prove_continuation_authority_invariants_v1()
    )


__all__ = ["prove_governed_runtime_apply_materialization_v1"]
