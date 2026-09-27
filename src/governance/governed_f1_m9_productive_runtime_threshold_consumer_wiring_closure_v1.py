"""Closure proof for F1/M9 productive runtime threshold consumer wiring v1."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Final

from src.governance.f1_m9_productive_runtime_threshold_consumer_wiring_v1 import (
    DECISION_CONFIG,
    OWNER_WP_DECISION_CONFIG,
    PRODUCTIVE_ACTIVATION_AUTHORIZED,
    RATIFIED_THRESHOLD_NUMERIC_MAX_AGE_SECONDS,
    REAL_P4_TO_F1_M9_JOIN_STATUS,
    WORKPACKAGE_ID,
    consumer_wiring_authorized_v1,
)
from src.governance.governed_f1_m9_scoped_owner_productive_runtime_apply_start_closure_v1 import (
    prove_governed_f1_m9_scoped_owner_productive_runtime_apply_start_v1,
)
from src.ops.productive_pure_stack_numeric_policy_shadow_campaign_v1.constants_v1 import (
    PRODUCTIVE_NUMERIC_VALUES_SET,
)
from src.trading.master_v2.canonical_volatility_numeric_max_age_policy_contract_and_non_enforcing_telemetry_v1 import (
    ENFORCEMENT_ENABLED,
    NUMERIC_MAX_AGE_DECIDED,
)

SCHEMA_VERSION: Final[str] = (
    "governed_f1_m9_productive_runtime_threshold_consumer_wiring_closure_v1"
)


def prove_governed_f1_m9_productive_runtime_threshold_consumer_wiring_v1(
    *, repo_root: Path | None = None
) -> bool:
    root = repo_root or Path(__file__).resolve().parents[2]
    if not prove_governed_f1_m9_scoped_owner_productive_runtime_apply_start_v1(repo_root=root):
        return False
    if not consumer_wiring_authorized_v1(repo_root=root):
        return False
    paths = (
        DECISION_CONFIG,
        OWNER_WP_DECISION_CONFIG,
        "src/governance/f1_m9_productive_runtime_threshold_consumer_wiring_v1.py",
        "tests/governance/test_governed_f1_m9_productive_runtime_threshold_consumer_wiring_real_mechanical_continuation_v1.py",
    )
    if not all((root / rel).is_file() for rel in paths):
        return False
    decision = json.loads((root / DECISION_CONFIG).read_text(encoding="utf-8"))
    owner = json.loads((root / OWNER_WP_DECISION_CONFIG).read_text(encoding="utf-8"))
    if decision.get("workpackage_id") != WORKPACKAGE_ID:
        return False
    if owner.get("f1_m9_productive_runtime_threshold_consumer_wiring_authorized") is not True:
        return False
    if decision.get("productive_activation_authorized") is not False:
        return False
    if decision.get("real_p4_to_f1_m9_join_status") != REAL_P4_TO_F1_M9_JOIN_STATUS:
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
    bound_threshold = str(decision.get("owner_threshold_record_digest_bound") or "")
    if len(bound_threshold) != 64:
        return False
    return True


__all__ = [
    "SCHEMA_VERSION",
    "prove_governed_f1_m9_productive_runtime_threshold_consumer_wiring_v1",
]
