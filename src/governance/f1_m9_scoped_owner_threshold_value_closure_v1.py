"""F1/M9 scoped Owner Threshold Value authority closure v1 (composition proof)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Final

from src.governance.f1_m9_scoped_owner_apply_closure_v1 import (
    prove_f1_m9_scoped_owner_apply_authority_v1,
)
from src.governance.f1_m9_scoped_owner_threshold_value_authority_v1 import (
    CONCRETE_THRESHOLD_VALUE_AUTHORIZED,
    DECISION_CONFIG,
    OWNER_POLICY_DECISION_CONFIG,
    RUNTIME_THRESHOLD_VALUE_AUTHORITY,
    WORKPACKAGE_ID,
)
from src.trading.master_v2.canonical_volatility_numeric_max_age_policy_contract_and_non_enforcing_telemetry_v1 import (
    ENFORCEMENT_ENABLED,
    NUMERIC_MAX_AGE_DECIDED,
)

SCHEMA_VERSION: Final[str] = "f1_m9_scoped_owner_threshold_value_closure_v1"


def prove_f1_m9_scoped_owner_threshold_value_authority_v1(*, repo_root: Path | None = None) -> bool:
    root = repo_root or Path(__file__).resolve().parents[2]
    required = (
        root / DECISION_CONFIG,
        root / OWNER_POLICY_DECISION_CONFIG,
        root / "src/governance/f1_m9_scoped_owner_threshold_value_authority_v1.py",
        root / "src/governance/f1_m9_owner_threshold_value_authorization_record_v1.py",
        root / "src/governance/f1_m9_threshold_value_authorization_ledger_v1.py",
        root / "tests/governance/test_f1_m9_scoped_owner_threshold_value_authority_v1.py",
    )
    if not all(path.is_file() for path in required):
        return False
    if not prove_f1_m9_scoped_owner_apply_authority_v1(repo_root=root):
        return False
    decision = json.loads((root / DECISION_CONFIG).read_text(encoding="utf-8"))
    owner_policy = json.loads((root / OWNER_POLICY_DECISION_CONFIG).read_text(encoding="utf-8"))
    if not decision.get("f1_m9_threshold_value_authority_implemented"):
        return False
    if decision.get("runtime_threshold_authority_value") != RUNTIME_THRESHOLD_VALUE_AUTHORITY:
        return False
    if owner_policy.get("owner_threshold_policy") != (
        "DEDICATED_DIGEST_SEALED_THRESHOLD_VALUE_AUTHORIZATION_RECORD_SEPARATE_FROM_F1_APPLY"
    ):
        return False
    if int(decision.get("productive_numeric_values_set_current", -1)) != 0:
        return False
    if decision.get("numeric_max_age_decided_current") is not False:
        return False
    if decision.get("concrete_threshold_value_authorized") is not False:
        return False
    if CONCRETE_THRESHOLD_VALUE_AUTHORIZED is not False:
        return False
    if ENFORCEMENT_ENABLED is not False or NUMERIC_MAX_AGE_DECIDED is not False:
        return False
    return True


__all__ = [
    "SCHEMA_VERSION",
    "WORKPACKAGE_ID",
    "prove_f1_m9_scoped_owner_threshold_value_authority_v1",
]
