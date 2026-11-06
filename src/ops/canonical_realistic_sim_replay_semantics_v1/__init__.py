"""R5 realistic sim/replay semantics v1.

Additive forensic overlay. Reuses I67 paper-sim, I79 replay-pack, Cap7
simulated execution, and Cap5.1 offline MD replay. Not a second execution,
order, promotion, or I17 shadow authority.
"""

from __future__ import annotations

from src.ops.canonical_realistic_sim_replay_semantics_v1.constants_v1 import (
    CAPABILITY_ID,
    CONTRACT_VERSION,
    I67_ROLE,
    I79_ROLE,
    PACKAGE_MARKER,
    REMEDIATION_ID,
)
from src.ops.canonical_realistic_sim_replay_semantics_v1.matrix_v1 import (
    MODE_CLASS_ROWS,
    SEMANTICS_MATRIX,
    require_dimension,
)
from src.ops.canonical_realistic_sim_replay_semantics_v1.models_v1 import (
    ModeClass,
    RealisticSimReplaySemanticsError,
)
from src.ops.canonical_realistic_sim_replay_semantics_v1.verifier_v1 import (
    evaluate_r5_realistic_sim_replay_v1,
    reject_equivalence_claim_v1,
)

__all__ = [
    "CAPABILITY_ID",
    "CONTRACT_VERSION",
    "I67_ROLE",
    "I79_ROLE",
    "MODE_CLASS_ROWS",
    "ModeClass",
    "PACKAGE_MARKER",
    "REMEDIATION_ID",
    "RealisticSimReplaySemanticsError",
    "SEMANTICS_MATRIX",
    "evaluate_r5_realistic_sim_replay_v1",
    "reject_equivalence_claim_v1",
    "require_dimension",
]
