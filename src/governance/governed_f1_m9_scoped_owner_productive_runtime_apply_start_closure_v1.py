"""Closure proof for F1/M9 governed productive runtime apply start continuation v1."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Final

from src.governance.governed_f1_m9_scoped_owner_productive_runtime_apply_start_real_mechanical_continuation_v1 import (
    DECISION_CONFIG,
    OWNER_WP_DECISION_CONFIG,
    PRODUCTIVE_ACTIVATION_AUTHORIZED,
    RATIFIED_THRESHOLD_NUMERIC_MAX_AGE_SECONDS,
    WORKPACKAGE_ID,
    prove_continuation_authority_invariants_v1,
    prove_continuation_decision_files_v1,
)
from src.governance.governed_f1_m9_scoped_owner_threshold_value_ratification_closure_v1 import (
    prove_governed_f1_m9_scoped_owner_threshold_value_ratification_v1,
)
from src.ops.productive_pure_stack_numeric_policy_shadow_campaign_v1.constants_v1 import (
    PRODUCTIVE_NUMERIC_VALUES_SET,
)
from src.trading.master_v2.canonical_volatility_numeric_max_age_policy_contract_and_non_enforcing_telemetry_v1 import (
    ENFORCEMENT_ENABLED,
    NUMERIC_MAX_AGE_DECIDED,
)

SCHEMA_VERSION: Final[str] = "governed_f1_m9_scoped_owner_productive_runtime_apply_start_closure_v1"


def prove_governed_f1_m9_scoped_owner_productive_runtime_apply_start_v1(
    *, repo_root: Path | None = None
) -> bool:
    root = repo_root or Path(__file__).resolve().parents[2]
    if not prove_continuation_authority_invariants_v1():
        return False
    if not prove_continuation_decision_files_v1(repo_root=root):
        return False
    if not prove_governed_f1_m9_scoped_owner_threshold_value_ratification_v1(repo_root=root):
        return False
    decision = json.loads((root / DECISION_CONFIG).read_text(encoding="utf-8"))
    owner = json.loads((root / OWNER_WP_DECISION_CONFIG).read_text(encoding="utf-8"))
    if decision.get("workpackage_id") != WORKPACKAGE_ID:
        return False
    if owner.get("governed_productive_runtime_apply_start_authorized") is not True:
        return False
    if decision.get("productive_activation_authorized") is not False:
        return False
    if PRODUCTIVE_ACTIVATION_AUTHORIZED is not False:
        return False
    if PRODUCTIVE_NUMERIC_VALUES_SET != 0:
        return False
    if NUMERIC_MAX_AGE_DECIDED is not False or ENFORCEMENT_ENABLED is not False:
        return False
    if int(decision.get("ratified_threshold_numeric_max_age_seconds", -1)) != (
        RATIFIED_THRESHOLD_NUMERIC_MAX_AGE_SECONDS
    ):
        return False
    bound_apply = str(decision.get("authorized_owner_apply_record_digest_bound") or "")
    bound_threshold = str(decision.get("owner_threshold_record_digest_bound") or "")
    if len(bound_apply) != 64 or len(bound_threshold) != 64:
        return False
    return True


__all__ = [
    "SCHEMA_VERSION",
    "prove_governed_f1_m9_scoped_owner_productive_runtime_apply_start_v1",
]
