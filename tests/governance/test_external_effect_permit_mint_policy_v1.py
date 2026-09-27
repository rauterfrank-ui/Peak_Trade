"""External Effect Permit Mint policy v1 tests."""

from __future__ import annotations

import copy
import json
from pathlib import Path

from src.governance.external_effect_permit_mint_gate_binding_v1 import (
    evaluate_permit_mint_bound_external_effect_permit_seam_v1,
)
from src.governance.external_effect_permit_mint_policy_v1 import (
    BASELINE_ORIGIN_MAIN_SHA,
    DECISION_CONFIG,
    OWNER_GO_DECISION_CONFIG,
    POLICY_RECORD_CONFIG,
    STATUS_MINT_ADMISSION_GRANTED,
    STATUS_POLICY_VALID,
    canonical_policy_record_body_v1,
    evaluate_external_effect_permit_mint_admission_v1,
    external_effect_permit_mint_policy_granted_v1,
    governed_permit_mint_authorized_v1,
    prove_import_time_autonomy_can_mint_permit_unchanged_v1,
    prove_permit_mint_does_not_authorize_credential_access_v1,
    prove_permit_mint_does_not_authorize_real_venue_post_v1,
    prove_permit_mint_does_not_perform_runtime_mint_v1,
    validate_external_effect_permit_mint_policy_record_v1,
)
from src.governance.governed_current_productive_chain_pre_external_to_external_effect_boundary_closure_v1 import (
    CANONICAL_EXTERNAL_EFFECT_BOUNDARY,
    prove_governed_current_productive_chain_pre_external_to_external_effect_boundary_v1,
)
from src.governance.governed_external_effect_permit_mint_policy_closure_v1 import (
    prove_governed_external_effect_permit_mint_policy_v1,
)
from src.governance.standing_external_effect_lift_policy_v1 import (
    governed_standing_external_effect_authorized_v1,
)
from src.ops.full_core_live_path_composition_root_v1.constants_v1 import (
    EXTERNAL_EFFECT_AUTHORIZED,
    POST_ALLOWED,
    REAL_VENUE_POST_ALLOWED,
)
from src.ops.full_core_live_path_composition_root_v1.current_productive_governed_cycle_orchestrator_v1 import (
    AUTONOMY_CAN_MINT_PERMIT,
    AUTONOMY_CAN_POST,
)

REPO_ROOT = Path(__file__).resolve().parents[2]


def test_baseline_and_import_time_guards() -> None:
    assert BASELINE_ORIGIN_MAIN_SHA == "03727c3cd09504beeedf4839b40dab3a26234331"
    assert prove_import_time_autonomy_can_mint_permit_unchanged_v1()
    assert EXTERNAL_EFFECT_AUTHORIZED is False
    assert POST_ALLOWED is False
    assert REAL_VENUE_POST_ALLOWED is False


def test_permit_mint_policy_record_valid() -> None:
    result = validate_external_effect_permit_mint_policy_record_v1(repo_root=REPO_ROOT)
    assert result.permit_policy_authorized is True, result.reason_codes
    assert result.policy_status == STATUS_POLICY_VALID
    assert external_effect_permit_mint_policy_granted_v1(repo_root=REPO_ROOT)


def test_positive_permit_mint_admission() -> None:
    assert governed_standing_external_effect_authorized_v1(repo_root=REPO_ROOT)
    admission = evaluate_external_effect_permit_mint_admission_v1(repo_root=REPO_ROOT)
    assert admission.admission_status == STATUS_MINT_ADMISSION_GRANTED
    assert admission.permit_mint_policy_granted is True
    assert admission.governed_permit_mint_authorized is True
    assert admission.permit_mint_authorized is True
    assert admission.permit_mint_performed is False
    assert admission.credential_access_authorized is False
    assert admission.post_allowed is False
    assert governed_permit_mint_authorized_v1(repo_root=REPO_ROOT) is True


def test_permit_mint_gate_binding() -> None:
    bound = evaluate_permit_mint_bound_external_effect_permit_seam_v1(repo_root=REPO_ROOT)
    assert bound.permit_mint_admission_granted is True
    assert bound.lift_bound_admission_granted is True
    assert bound.governed_permit_mint_authorized is True
    assert bound.permit_mint_performed is False
    assert bound.credential_access_authorized is False


def test_authority_separation_proofs() -> None:
    assert prove_permit_mint_does_not_perform_runtime_mint_v1()
    assert prove_permit_mint_does_not_authorize_credential_access_v1()
    assert prove_permit_mint_does_not_authorize_real_venue_post_v1()
    assert AUTONOMY_CAN_MINT_PERMIT is False
    assert AUTONOMY_CAN_POST is False


def test_closure_and_chain() -> None:
    assert prove_governed_external_effect_permit_mint_policy_v1(repo_root=REPO_ROOT)
    assert prove_governed_current_productive_chain_pre_external_to_external_effect_boundary_v1(
        repo_root=REPO_ROOT
    )


def test_decision_records() -> None:
    owner = json.loads((REPO_ROOT / OWNER_GO_DECISION_CONFIG).read_text(encoding="utf-8"))
    assert owner["external_effect_permit_mint_owner_go"] is True
    assert owner["permit_mint_performed"] is False
    assert owner["next_genuine_blocker"] == "CHECKOUT_INDEPENDENT_CREDENTIAL_ACCESS_OWNER_GO"
    decision = json.loads((REPO_ROOT / DECISION_CONFIG).read_text(encoding="utf-8"))
    assert decision["governed_permit_mint_authorized"] is True
    assert decision["mint_implies_credential_access"] is False
    assert decision["post_allowed"] is False


def test_canonical_boundary_constant_updated() -> None:
    assert CANONICAL_EXTERNAL_EFFECT_BOUNDARY == (
        "CREDENTIAL_MATERIAL_LOAD_GOVERNED_K1_SIGNING_POST_FAIL_CLOSED"
    )


def test_permit_mint_record_digest_mismatch_fail_closed(tmp_path: Path) -> None:
    for rel in (
        POLICY_RECORD_CONFIG,
        OWNER_GO_DECISION_CONFIG,
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

    result = validate_external_effect_permit_mint_policy_record_v1(repo_root=tmp_path)
    assert result.permit_policy_authorized is False
    assert "POLICY_RECORD_DIGEST_MISMATCH" in result.reason_codes


def test_owner_go_missing_fail_closed(tmp_path: Path) -> None:
    for rel in (
        POLICY_RECORD_CONFIG,
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
        json.dumps({"external_effect_permit_mint_owner_go": False}) + "\n",
        encoding="utf-8",
    )

    result = validate_external_effect_permit_mint_policy_record_v1(repo_root=tmp_path)
    assert result.permit_policy_authorized is False
    assert "OWNER_GO_DECISION_NOT_CONSUMED" in result.reason_codes


def test_canonical_body_stable() -> None:
    record = json.loads((REPO_ROOT / POLICY_RECORD_CONFIG).read_text(encoding="utf-8"))
    body = canonical_policy_record_body_v1(record)
    mutated = copy.deepcopy(record)
    mutated["semantic_definition"] = "tampered"
    assert canonical_policy_record_body_v1(mutated) != body
