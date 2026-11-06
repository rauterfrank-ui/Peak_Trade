"""Closure proof for Productive Activation boundary forensic review v1."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Final

from src.governance.productive_activation_boundary_forensic_review_v1 import (
    DECISION_CONFIG,
    OWNER_WP_DECISION_CONFIG,
    WORKPACKAGE_ID,
    prove_productive_activation_boundary_forensic_review_v1,
)

SCHEMA_VERSION: Final[str] = "governed_productive_activation_boundary_forensic_review_closure_v1"


def prove_governed_productive_activation_boundary_forensic_review_v1(
    *, repo_root: Path | None = None
) -> bool:
    root = repo_root or Path(__file__).resolve().parents[2]
    proof = prove_productive_activation_boundary_forensic_review_v1(repo_root=root)
    if proof.ok is not True:
        return False
    paths = (
        DECISION_CONFIG,
        OWNER_WP_DECISION_CONFIG,
        "src/governance/productive_activation_boundary_forensic_review_v1/proof_v1.py",
        "tests/governance/test_productive_activation_boundary_forensic_review_v1.py",
    )
    if not all((root / rel).is_file() for rel in paths):
        return False
    decision = json.loads((root / DECISION_CONFIG).read_text(encoding="utf-8"))
    owner = json.loads((root / OWNER_WP_DECISION_CONFIG).read_text(encoding="utf-8"))
    if decision.get("workpackage_id") != WORKPACKAGE_ID:
        return False
    if owner.get("productive_activation_boundary_forensic_review_authorized") is not True:
        return False
    if decision.get("productive_activation_authorized") is not False:
        return False
    if decision.get("forensic_review_complete") is not True:
        return False
    if decision.get("consumer_reachability_implies_productive_activation") is not False:
        return False
    return True


__all__ = [
    "SCHEMA_VERSION",
    "prove_governed_productive_activation_boundary_forensic_review_v1",
]
