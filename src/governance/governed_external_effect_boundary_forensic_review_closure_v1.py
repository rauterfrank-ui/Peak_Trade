"""Closure proof for External Effect boundary forensic review v1."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Final

from src.governance.external_effect_boundary_forensic_review_v1.constants_v1 import (
    DECISION_CONFIG,
    OWNER_WP_DECISION_CONFIG,
    WORKPACKAGE_ID,
)
from src.governance.external_effect_boundary_forensic_review_v1.proof_v1 import (
    prove_external_effect_boundary_forensic_review_v1,
)

SCHEMA_VERSION: Final[str] = "governed_external_effect_boundary_forensic_review_closure_v1"


def prove_governed_external_effect_boundary_forensic_review_v1(
    *, repo_root: Path | None = None
) -> bool:
    root = repo_root or Path(__file__).resolve().parents[2]
    proof = prove_external_effect_boundary_forensic_review_v1(repo_root=root)
    if proof.ok is not True:
        return False
    paths = (
        DECISION_CONFIG,
        OWNER_WP_DECISION_CONFIG,
        "src/governance/external_effect_boundary_forensic_review_v1/proof_v1.py",
        "tests/governance/test_external_effect_boundary_forensic_review_v1.py",
    )
    if not all((root / rel).is_file() for rel in paths):
        return False
    owner = json.loads((root / OWNER_WP_DECISION_CONFIG).read_text(encoding="utf-8"))
    if owner.get("workpackage_id") != WORKPACKAGE_ID:
        return False
    if owner.get("external_effect_boundary_forensic_review_owner_go") is not True:
        return False
    return True


__all__ = [
    "SCHEMA_VERSION",
    "prove_governed_external_effect_boundary_forensic_review_v1",
]
