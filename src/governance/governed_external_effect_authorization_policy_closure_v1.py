"""Closure proof for External Effect authorization policy v1."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Final

from src.governance.external_effect_authorization_policy_v1 import (
    DECISION_CONFIG,
    OWNER_GO_DECISION_CONFIG,
    POLICY_RECORD_CONFIG,
    WORKPACKAGE_ID,
    prove_policy_does_not_authorize_credential_access_v1,
    prove_policy_does_not_authorize_permit_mint_v1,
    prove_policy_does_not_authorize_real_venue_post_v1,
    prove_pre_external_reachability_does_not_imply_external_effect_authorization_v1,
    prove_standing_gate_chain_present_v1,
    validate_external_effect_authorization_policy_record_v1,
)
from src.governance.governed_external_effect_boundary_forensic_review_closure_v1 import (
    prove_governed_external_effect_boundary_forensic_review_v1,
)

SCHEMA_VERSION: Final[str] = "governed_external_effect_authorization_policy_closure_v1"


def prove_governed_external_effect_authorization_policy_v1(
    *, repo_root: Path | None = None
) -> bool:
    root = repo_root or Path(__file__).resolve().parents[2]
    policy = validate_external_effect_authorization_policy_record_v1(repo_root=root)
    if policy.policy_authorized is not True:
        return False
    if not prove_pre_external_reachability_does_not_imply_external_effect_authorization_v1():
        return False
    if not prove_policy_does_not_authorize_permit_mint_v1():
        return False
    if not prove_policy_does_not_authorize_credential_access_v1():
        return False
    if not prove_policy_does_not_authorize_real_venue_post_v1():
        return False
    if not prove_standing_gate_chain_present_v1(repo_root=root):
        return False
    paths = (
        POLICY_RECORD_CONFIG,
        OWNER_GO_DECISION_CONFIG,
        DECISION_CONFIG,
        "src/governance/external_effect_authorization_policy_v1.py",
        "src/governance/external_effect_authorization_policy_gate_binding_v1.py",
        "tests/governance/test_external_effect_authorization_policy_v1.py",
    )
    if not all((root / rel).is_file() for rel in paths):
        return False
    owner = json.loads((root / OWNER_GO_DECISION_CONFIG).read_text(encoding="utf-8"))
    if owner.get("workpackage_id") != WORKPACKAGE_ID:
        return False
    if owner.get("external_effect_authorization_policy_owner_go") is not True:
        return False
    decision = json.loads((root / DECISION_CONFIG).read_text(encoding="utf-8"))
    if decision.get("workpackage_id") != WORKPACKAGE_ID:
        return False
    if decision.get("standing_external_effect_authorized") is not False:
        return False
    return prove_governed_external_effect_boundary_forensic_review_v1(repo_root=root)


__all__ = [
    "SCHEMA_VERSION",
    "prove_governed_external_effect_authorization_policy_v1",
]
