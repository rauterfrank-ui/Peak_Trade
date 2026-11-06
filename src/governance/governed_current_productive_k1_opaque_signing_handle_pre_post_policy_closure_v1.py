"""Closure proof for K1 opaque signing handle PRE-POST policy v1."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Final

from src.governance.current_productive_k1_opaque_signing_handle_pre_post_policy_v1 import (
    DECISION_CONFIG,
    OWNER_GO_DECISION_CONFIG,
    POLICY_RECORD_CONFIG,
    WORKPACKAGE_ID,
    prove_k1_pre_post_does_not_authorize_post_v1,
    prove_k1_pre_post_does_not_flip_standing_keychain_pins_v1,
    prove_k1_pre_post_policy_does_not_perform_permit_mint_v1,
    validate_k1_opaque_signing_handle_pre_post_policy_record_v1,
)
from src.governance.governed_real_keychain_access_or_credential_material_load_policy_closure_v1 import (
    prove_governed_real_keychain_access_or_credential_material_load_policy_v1,
)

SCHEMA_VERSION: Final[str] = (
    "governed_current_productive_k1_opaque_signing_handle_pre_post_policy_closure_v1"
)


def prove_governed_current_productive_k1_opaque_signing_handle_pre_post_policy_v1(
    *, repo_root: Path | None = None
) -> bool:
    root = repo_root or Path(__file__).resolve().parents[2]
    policy = validate_k1_opaque_signing_handle_pre_post_policy_record_v1(repo_root=root)
    if policy.k1_pre_post_policy_authorized is not True:
        return False
    if not prove_k1_pre_post_does_not_flip_standing_keychain_pins_v1():
        return False
    if not prove_k1_pre_post_does_not_authorize_post_v1():
        return False
    if not prove_k1_pre_post_policy_does_not_perform_permit_mint_v1():
        return False
    paths = (
        POLICY_RECORD_CONFIG,
        OWNER_GO_DECISION_CONFIG,
        DECISION_CONFIG,
        "src/governance/current_productive_k1_opaque_signing_handle_pre_post_policy_v1.py",
        "src/governance/current_productive_k1_opaque_signing_handle_pre_post_gate_binding_v1.py",
        "src/governance/k1_opaque_signing_handle_governed_construction_v1.py",
        "src/governance/current_productive_k1_pre_post_request_envelope_v1.py",
        "tests/governance/test_current_productive_k1_opaque_signing_handle_pre_post_policy_v1.py",
    )
    if not all((root / rel).is_file() for rel in paths):
        return False
    owner = json.loads((root / OWNER_GO_DECISION_CONFIG).read_text(encoding="utf-8"))
    if owner.get("workpackage_id") != WORKPACKAGE_ID:
        return False
    if owner.get("current_productive_k1_opaque_signing_handle_pre_post_owner_go") is not True:
        return False
    decision = json.loads((root / DECISION_CONFIG).read_text(encoding="utf-8"))
    if decision.get("workpackage_id") != WORKPACKAGE_ID:
        return False
    if decision.get("governed_k1_opaque_signing_handle_authorized") is not True:
        return False
    if decision.get("post_allowed") is not False:
        return False
    if decision.get("request_signing_authorized") is not True:
        return False
    return prove_governed_real_keychain_access_or_credential_material_load_policy_v1(repo_root=root)


__all__ = [
    "SCHEMA_VERSION",
    "prove_governed_current_productive_k1_opaque_signing_handle_pre_post_policy_v1",
]
