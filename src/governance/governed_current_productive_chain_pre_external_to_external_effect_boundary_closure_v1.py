"""End-to-end closure: governed productive chain → PRE_EXTERNAL → external-effect boundary."""

from __future__ import annotations

from pathlib import Path
from typing import Final

from src.governance.external_effect_boundary_forensic_review_v1.proof_v1 import (
    prove_external_effect_boundary_forensic_review_v1,
)
from src.governance.governed_current_continuous_run_policy_closure_v1 import (
    prove_governed_current_continuous_run_policy_v1,
)
from src.governance.governed_current_productive_activation_policy_closure_v1 import (
    prove_governed_current_productive_activation_policy_v1,
)
from src.governance.governed_external_effect_boundary_forensic_review_closure_v1 import (
    prove_governed_external_effect_boundary_forensic_review_v1,
)
from src.ops.pre_external_to_external_effect_boundary_bounded_wp_v1.proof_v1 import (
    prove_pre_external_to_external_effect_boundary_v1,
)

SCHEMA_VERSION: Final[str] = (
    "governed_current_productive_chain_pre_external_to_external_effect_boundary_closure_v1"
)
BOUNDED_ORCHESTRATION_TERMINAL: Final[str] = "PRE_EXTERNAL_EFFECT_BOUNDARY"
CANONICAL_EXTERNAL_EFFECT_BOUNDARY: Final[str] = (
    "STANDING_EXTERNAL_EFFECT_GATE_AND_ENVELOPE_SEAM_FAIL_CLOSED"
)


def prove_governed_current_productive_chain_pre_external_to_external_effect_boundary_v1(
    *, repo_root: Path | None = None
) -> bool:
    root = repo_root or Path(__file__).resolve().parents[2]
    if not prove_governed_current_productive_activation_policy_v1(repo_root=root):
        return False
    if not prove_governed_current_continuous_run_policy_v1(repo_root=root):
        return False
    pre_external = prove_pre_external_to_external_effect_boundary_v1()
    if pre_external.ok is not True:
        return False
    if not prove_governed_external_effect_boundary_forensic_review_v1(repo_root=root):
        return False
    forensic = prove_external_effect_boundary_forensic_review_v1(repo_root=root)
    return forensic.ok is True


__all__ = [
    "BOUNDED_ORCHESTRATION_TERMINAL",
    "CANONICAL_EXTERNAL_EFFECT_BOUNDARY",
    "SCHEMA_VERSION",
    "prove_governed_current_productive_chain_pre_external_to_external_effect_boundary_v1",
]
