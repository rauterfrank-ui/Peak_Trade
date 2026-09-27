"""Closure proof for actual-venue POST admission policy v1."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Final

from src.governance.current_productive_actual_venue_post_admission_policy_v1 import (
    DECISION_CONFIG,
    OWNER_GO_DECISION_CONFIG,
    WORKPACKAGE_ID,
    validate_actual_venue_post_admission_policy_v1,
)

SCHEMA_VERSION: Final[str] = "governed_current_productive_actual_venue_post_admission_closure_v1"


def prove_governed_current_productive_actual_venue_post_admission_v1(
    *, repo_root: Path | None = None
) -> bool:
    root = repo_root or Path(__file__).resolve().parents[2]
    policy = validate_actual_venue_post_admission_policy_v1(repo_root=root)
    if policy.policy_valid is not True:
        return False
    paths = (
        OWNER_GO_DECISION_CONFIG,
        DECISION_CONFIG,
        "src/governance/current_productive_real_venue_post_admission_v1.py",
        "src/governance/current_productive_actual_venue_post_admission_policy_v1.py",
        "src/ops/full_core_live_path_composition_root_v1/"
        "current_productive_actual_venue_post_owner_go_durable_consume_v1.py",
        "src/ops/governed_productive_account_equity_authority_producer_v1/"
        "current_productive_actual_venue_post_with_fresh_envelope_bound_single_use_permit_v1.py",
        "tests/ops/test_current_productive_actual_venue_post_with_fresh_envelope_bound_single_use_permit_v1.py",
    )
    if not all((root / rel).is_file() for rel in paths):
        return False
    owner = json.loads((root / OWNER_GO_DECISION_CONFIG).read_text(encoding="utf-8"))
    return owner.get("workpackage_id") == WORKPACKAGE_ID and owner.get("owner_go") is True


__all__ = [
    "SCHEMA_VERSION",
    "prove_governed_current_productive_actual_venue_post_admission_v1",
]
