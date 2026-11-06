"""Closure proof for governed productive configuration apply authority v1."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Final

from src.governance.governed_productive_configuration_apply_authority_v1 import (
    APPLY_AUTHORITY_ID,
    DECISION_CONFIG,
    NORMATIVE_SPEC,
    OWNER_RATIFICATION_CONFIG,
    RUNTIME_APPLY_STARTED,
    WORKPACKAGE_ID,
    prove_negative_apply_authority_safety_invariants_v1,
)

_REPO_ROOT = Path(__file__).resolve().parents[2]


def prove_governed_productive_configuration_apply_authority_v1(
    *, repo_root: Path | None = None
) -> bool:
    root = repo_root or _REPO_ROOT
    required = (
        NORMATIVE_SPEC,
        DECISION_CONFIG,
        OWNER_RATIFICATION_CONFIG,
        "src/governance/governed_productive_configuration_apply_record_v1.py",
        "src/governance/governed_productive_configuration_apply_authority_v1.py",
        "tests/governance/test_governed_productive_configuration_apply_authority_v1.py",
    )
    for rel in required:
        if not (root / rel).is_file():
            return False
    decision = json.loads((root / DECISION_CONFIG).read_text(encoding="utf-8"))
    owner = json.loads((root / OWNER_RATIFICATION_CONFIG).read_text(encoding="utf-8"))
    if decision.get("workpackage_id") != WORKPACKAGE_ID:
        return False
    if decision.get("apply_authority_id") != APPLY_AUTHORITY_ID:
        return False
    if owner.get("ratified_authority_id") != APPLY_AUTHORITY_ID:
        return False
    if decision.get("runtime_apply_started") is not False:
        return False
    if decision.get("real_runtime_materialization_performed") is not False:
        return False
    if RUNTIME_APPLY_STARTED is not False:
        return False
    if not prove_negative_apply_authority_safety_invariants_v1():
        return False
    return True


__all__ = ["prove_governed_productive_configuration_apply_authority_v1"]
