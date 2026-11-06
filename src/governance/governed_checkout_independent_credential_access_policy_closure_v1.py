"""Closure proof for Checkout-independent credential access policy v1."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Final

from src.governance.checkout_independent_credential_access_policy_v1 import (
    DECISION_CONFIG,
    OWNER_GO_DECISION_CONFIG,
    POLICY_RECORD_CONFIG,
    WORKPACKAGE_ID,
    prove_credential_access_does_not_activate_productive_provider_v1,
    prove_credential_access_does_not_authorize_post_v1,
    prove_credential_access_does_not_perform_permit_mint_v1,
    prove_credential_access_does_not_perform_real_secret_load_v1,
    prove_real_keychain_standing_pins_unchanged_v1,
    validate_checkout_independent_credential_access_policy_record_v1,
)
from src.governance.governed_external_effect_permit_mint_policy_closure_v1 import (
    prove_governed_external_effect_permit_mint_policy_v1,
)

SCHEMA_VERSION: Final[str] = "governed_checkout_independent_credential_access_policy_closure_v1"


def prove_governed_checkout_independent_credential_access_policy_v1(
    *, repo_root: Path | None = None
) -> bool:
    root = repo_root or Path(__file__).resolve().parents[2]
    policy = validate_checkout_independent_credential_access_policy_record_v1(repo_root=root)
    if policy.credential_access_policy_authorized is not True:
        return False
    if not prove_credential_access_does_not_perform_real_secret_load_v1():
        return False
    if not prove_real_keychain_standing_pins_unchanged_v1():
        return False
    if not prove_credential_access_does_not_activate_productive_provider_v1():
        return False
    if not prove_credential_access_does_not_authorize_post_v1():
        return False
    if not prove_credential_access_does_not_perform_permit_mint_v1():
        return False
    paths = (
        POLICY_RECORD_CONFIG,
        OWNER_GO_DECISION_CONFIG,
        DECISION_CONFIG,
        "src/governance/checkout_independent_credential_access_policy_v1.py",
        "src/governance/checkout_independent_credential_access_gate_binding_v1.py",
        "tests/governance/test_checkout_independent_credential_access_policy_v1.py",
    )
    if not all((root / rel).is_file() for rel in paths):
        return False
    owner = json.loads((root / OWNER_GO_DECISION_CONFIG).read_text(encoding="utf-8"))
    if owner.get("workpackage_id") != WORKPACKAGE_ID:
        return False
    if owner.get("checkout_independent_credential_access_owner_go") is not True:
        return False
    decision = json.loads((root / DECISION_CONFIG).read_text(encoding="utf-8"))
    if decision.get("workpackage_id") != WORKPACKAGE_ID:
        return False
    if decision.get("governed_credential_access_authorized") is not True:
        return False
    if decision.get("real_secret_load_performed") is not False:
        return False
    if decision.get("real_credential_access_performed") is not False:
        return False
    if decision.get("post_allowed") is not False:
        return False
    return prove_governed_external_effect_permit_mint_policy_v1(repo_root=root)


__all__ = [
    "SCHEMA_VERSION",
    "prove_governed_checkout_independent_credential_access_policy_v1",
]
