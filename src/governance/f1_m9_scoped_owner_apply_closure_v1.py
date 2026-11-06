"""F1/M9 scoped Owner Apply closure v1 (composition proof)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Final

from src.governance.f1_m9_scoped_owner_apply_authority_v1 import (
    DECISION_CONFIG,
    OWNER_POLICY_DECISION_CONFIG,
    RUNTIME_APPLY_AUTHORITY_VALUE,
    WORKPACKAGE_ID,
)
from src.governance.governed_productive_configuration_v1 import runtime_apply_possible_v1
from src.governance.v32_d29_f1_m9_per_ingress_productive_authorization_apply_closure_v1 import (
    prove_v32_d29_f1_m9_per_ingress_productive_authorization_apply_max_build_v1,
)

SCHEMA_VERSION: Final[str] = "f1_m9_scoped_owner_apply_closure_v1"


def prove_f1_m9_scoped_owner_apply_authority_v1(*, repo_root: Path | None = None) -> bool:
    root = repo_root or Path(__file__).resolve().parents[2]
    required = (
        root / DECISION_CONFIG,
        root / OWNER_POLICY_DECISION_CONFIG,
        root / "src/governance/f1_m9_scoped_owner_apply_authority_v1.py",
        root / "src/governance/f1_m9_owner_apply_authorization_record_v1.py",
        root / "src/governance/f1_m9_productive_apply_ledger_v1.py",
        root / "tests/governance/test_f1_m9_scoped_owner_apply_authority_v1.py",
    )
    if not all(path.is_file() for path in required):
        return False
    if not prove_v32_d29_f1_m9_per_ingress_productive_authorization_apply_max_build_v1(
        repo_root=root
    ):
        return False
    decision = json.loads((root / DECISION_CONFIG).read_text(encoding="utf-8"))
    owner_policy = json.loads((root / OWNER_POLICY_DECISION_CONFIG).read_text(encoding="utf-8"))
    if not decision.get("f1_m9_apply_implemented"):
        return False
    if decision.get("runtime_apply_authority_value") != RUNTIME_APPLY_AUTHORITY_VALUE:
        return False
    if owner_policy.get("owner_apply_policy") != "SCOPED_APPLY_WITH_DEDICATED_RECORD":
        return False
    if int(decision.get("productive_numeric_values_set_current", -1)) != 0:
        return False
    if decision.get("global_optimization_join_authorized"):
        return False
    if runtime_apply_possible_v1() is not False:
        return False
    return True


__all__ = [
    "SCHEMA_VERSION",
    "WORKPACKAGE_ID",
    "prove_f1_m9_scoped_owner_apply_authority_v1",
]
