"""Closure proof for CURRENT Productive Activation policy v1."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Final

from src.governance.current_productive_activation_policy_v1 import (
    OWNER_GO_DECISION_CONFIG,
    POLICY_RECORD_CONFIG,
    WORKPACKAGE_ID,
    prove_downstream_authorities_independent_v1,
    prove_p5_bind_does_not_imply_productive_activation_v1,
    validate_productive_activation_policy_record_v1,
)
from src.governance.governed_f1_m9_productive_runtime_threshold_consumer_wiring_closure_v1 import (
    prove_governed_f1_m9_productive_runtime_threshold_consumer_wiring_v1,
)
from src.governance.productive_activation_boundary_forensic_review_v1.proof_v1 import (
    prove_productive_activation_boundary_forensic_review_v1,
)

SCHEMA_VERSION: Final[str] = "governed_current_productive_activation_policy_closure_v1"


def prove_governed_current_productive_activation_policy_v1(
    *, repo_root: Path | None = None
) -> bool:
    root = repo_root or Path(__file__).resolve().parents[2]
    policy = validate_productive_activation_policy_record_v1(repo_root=root)
    if policy.policy_authorized is not True:
        return False
    if not prove_downstream_authorities_independent_v1():
        return False
    if not prove_p5_bind_does_not_imply_productive_activation_v1():
        return False
    paths = (
        POLICY_RECORD_CONFIG,
        OWNER_GO_DECISION_CONFIG,
        "src/governance/current_productive_activation_policy_v1.py",
        "tests/governance/test_current_productive_activation_policy_v1.py",
    )
    if not all((root / rel).is_file() for rel in paths):
        return False
    owner = json.loads((root / OWNER_GO_DECISION_CONFIG).read_text(encoding="utf-8"))
    if owner.get("workpackage_id") != WORKPACKAGE_ID:
        return False
    if owner.get("current_productive_activation_policy_owner_go") is not True:
        return False
    if not prove_governed_f1_m9_productive_runtime_threshold_consumer_wiring_v1(repo_root=root):
        return False
    forensic = prove_productive_activation_boundary_forensic_review_v1(repo_root=root)
    return forensic.ok is True


__all__ = [
    "SCHEMA_VERSION",
    "prove_governed_current_productive_activation_policy_v1",
]
