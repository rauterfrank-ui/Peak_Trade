"""Checkout-independent credential access policy v1 tests."""

from __future__ import annotations

import copy
import json
from pathlib import Path

from src.governance.checkout_independent_credential_access_gate_binding_v1 import (
    evaluate_credential_access_bound_checkout_independent_capability_seam_v1,
)
from src.governance.checkout_independent_credential_access_policy_v1 import (
    BASELINE_ORIGIN_MAIN_SHA,
    DECISION_CONFIG,
    OWNER_GO_DECISION_CONFIG,
    POLICY_RECORD_CONFIG,
    STATUS_ADMISSION_GRANTED,
    STATUS_POLICY_VALID,
    canonical_policy_record_body_v1,
    checkout_independent_credential_access_policy_granted_v1,
    evaluate_checkout_independent_credential_access_admission_v1,
    governed_credential_access_authorized_v1,
    prove_credential_access_does_not_activate_productive_provider_v1,
    prove_credential_access_does_not_authorize_post_v1,
    prove_credential_access_does_not_perform_permit_mint_v1,
    prove_credential_access_does_not_perform_real_secret_load_v1,
    prove_real_keychain_standing_pins_unchanged_v1,
    validate_checkout_independent_credential_access_policy_record_v1,
)
from src.governance.external_effect_permit_mint_policy_v1 import (
    governed_permit_mint_authorized_v1,
)
from src.governance.governed_checkout_independent_credential_access_policy_closure_v1 import (
    prove_governed_checkout_independent_credential_access_policy_v1,
)
from src.governance.governed_current_productive_chain_pre_external_to_external_effect_boundary_closure_v1 import (
    CANONICAL_EXTERNAL_EFFECT_BOUNDARY,
    prove_governed_current_productive_chain_pre_external_to_external_effect_boundary_v1,
)
from src.ops.full_core_live_path_composition_root_v1.constants_v1 import (
    POST_ALLOWED,
    REAL_VENUE_POST_ALLOWED,
)
from src.ops.full_core_live_path_composition_root_v1.current_productive_governed_cycle_orchestrator_v1 import (
    AUTONOMY_CAN_MINT_PERMIT,
    AUTONOMY_CAN_POST,
)

REPO_ROOT = Path(__file__).resolve().parents[2]


def test_baseline_and_secret_safety_proofs() -> None:
    assert BASELINE_ORIGIN_MAIN_SHA == "e92e5cb088f0e1dbdb83d37f40b9e90293cca127"
    assert prove_credential_access_does_not_perform_real_secret_load_v1()
    assert prove_real_keychain_standing_pins_unchanged_v1()
    assert prove_credential_access_does_not_activate_productive_provider_v1()
    assert POST_ALLOWED is False
    assert REAL_VENUE_POST_ALLOWED is False


def test_credential_access_policy_record_valid() -> None:
    result = validate_checkout_independent_credential_access_policy_record_v1(repo_root=REPO_ROOT)
    assert result.credential_access_policy_authorized is True, result.reason_codes
    assert result.policy_status == STATUS_POLICY_VALID
    assert checkout_independent_credential_access_policy_granted_v1(repo_root=REPO_ROOT)


def test_positive_credential_access_admission() -> None:
    assert governed_permit_mint_authorized_v1(repo_root=REPO_ROOT)
    admission = evaluate_checkout_independent_credential_access_admission_v1(repo_root=REPO_ROOT)
    assert admission.admission_status == STATUS_ADMISSION_GRANTED
    assert admission.credential_access_policy_granted is True
    assert admission.governed_credential_access_authorized is True
    assert admission.credential_access_authorized is True
    assert admission.real_secret_load_performed is False
    assert admission.real_credential_access_performed is False
    assert admission.credential_access_performed is False
    assert admission.post_allowed is False
    assert governed_credential_access_authorized_v1(repo_root=REPO_ROOT) is True


def test_credential_access_gate_binding() -> None:
    bound = evaluate_credential_access_bound_checkout_independent_capability_seam_v1(
        repo_root=REPO_ROOT
    )
    assert bound.credential_access_admission_granted is True
    assert bound.permit_mint_bound_admission_granted is True
    assert bound.real_secret_load_performed is False
    assert bound.post_allowed is False


def test_authority_separation_proofs() -> None:
    assert prove_credential_access_does_not_authorize_post_v1()
    assert prove_credential_access_does_not_perform_permit_mint_v1()
    assert AUTONOMY_CAN_MINT_PERMIT is False
    assert AUTONOMY_CAN_POST is False


def test_closure_and_chain() -> None:
    assert prove_governed_checkout_independent_credential_access_policy_v1(repo_root=REPO_ROOT)
    assert prove_governed_current_productive_chain_pre_external_to_external_effect_boundary_v1(
        repo_root=REPO_ROOT
    )


def test_decision_records() -> None:
    owner = json.loads((REPO_ROOT / OWNER_GO_DECISION_CONFIG).read_text(encoding="utf-8"))
    assert owner["checkout_independent_credential_access_owner_go"] is True
    assert owner["real_secret_load_performed"] is False
    assert (
        owner["next_genuine_blocker"] == "REAL_KEYCHAIN_ACCESS_OR_CREDENTIAL_MATERIAL_LOAD_OWNER_GO"
    )
    decision = json.loads((REPO_ROOT / DECISION_CONFIG).read_text(encoding="utf-8"))
    assert decision["governed_credential_access_authorized"] is True
    assert decision["access_implies_real_secret_load"] is False
    assert decision["post_allowed"] is False


def test_canonical_boundary_constant_updated() -> None:
    assert CANONICAL_EXTERNAL_EFFECT_BOUNDARY == (
        "K1_OPAQUE_SIGNING_PRE_POST_ENVELOPE_VALIDATED_REAL_VENUE_POST_ADMISSION_FAIL_CLOSED"
    )


def test_record_digest_mismatch_fail_closed(tmp_path: Path) -> None:
    for rel in (
        POLICY_RECORD_CONFIG,
        OWNER_GO_DECISION_CONFIG,
        "config/governance/external_effect_permit_mint_policy_v1_record.json",
        "config/governance/external_effect_permit_mint_owner_go_v1_decision.json",
        "config/governance/standing_external_effect_lift_policy_v1_record.json",
        "config/governance/standing_external_effect_lift_owner_go_v1_decision.json",
        "config/governance/external_effect_authorization_policy_v1_record.json",
        "config/governance/external_effect_authorization_policy_owner_go_v1_decision.json",
    ):
        src = REPO_ROOT / rel
        dst = tmp_path / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        dst.write_text(src.read_text(encoding="utf-8"), encoding="utf-8")

    record = json.loads((tmp_path / POLICY_RECORD_CONFIG).read_text(encoding="utf-8"))
    record["policy_record_digest"] = "0" * 64
    (tmp_path / POLICY_RECORD_CONFIG).write_text(json.dumps(record, indent=2) + "\n")

    result = validate_checkout_independent_credential_access_policy_record_v1(repo_root=tmp_path)
    assert result.credential_access_policy_authorized is False
    assert "POLICY_RECORD_DIGEST_MISMATCH" in result.reason_codes


def test_owner_go_missing_fail_closed(tmp_path: Path) -> None:
    for rel in (
        POLICY_RECORD_CONFIG,
        "config/governance/external_effect_permit_mint_policy_v1_record.json",
        "config/governance/external_effect_permit_mint_owner_go_v1_decision.json",
        "config/governance/standing_external_effect_lift_policy_v1_record.json",
        "config/governance/standing_external_effect_lift_owner_go_v1_decision.json",
        "config/governance/external_effect_authorization_policy_v1_record.json",
        "config/governance/external_effect_authorization_policy_owner_go_v1_decision.json",
    ):
        src = REPO_ROOT / rel
        dst = tmp_path / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        dst.write_text(src.read_text(encoding="utf-8"), encoding="utf-8")

    owner_path = tmp_path / OWNER_GO_DECISION_CONFIG
    owner_path.parent.mkdir(parents=True, exist_ok=True)
    owner_path.write_text(
        json.dumps({"checkout_independent_credential_access_owner_go": False}) + "\n",
        encoding="utf-8",
    )

    result = validate_checkout_independent_credential_access_policy_record_v1(repo_root=tmp_path)
    assert result.credential_access_policy_authorized is False
    assert "OWNER_GO_DECISION_NOT_CONSUMED" in result.reason_codes


def test_canonical_body_stable() -> None:
    record = json.loads((REPO_ROOT / POLICY_RECORD_CONFIG).read_text(encoding="utf-8"))
    body = canonical_policy_record_body_v1(record)
    mutated = copy.deepcopy(record)
    mutated["semantic_definition"] = "tampered"
    assert canonical_policy_record_body_v1(mutated) != body
