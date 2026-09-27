"""External Effect authorization policy v1 tests."""

from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest

from src.governance.external_effect_authorization_policy_v1 import (
    BASELINE_ORIGIN_MAIN_SHA,
    DECISION_CONFIG,
    OWNER_GO_DECISION_CONFIG,
    POLICY_RECORD_CONFIG,
    STATUS_ADMISSION_GRANTED,
    STATUS_POLICY_VALID,
    canonical_policy_record_body_v1,
    evaluate_external_effect_policy_admission_v1,
    prove_policy_does_not_authorize_credential_access_v1,
    prove_policy_does_not_authorize_permit_mint_v1,
    prove_policy_does_not_authorize_real_venue_post_v1,
    prove_pre_external_reachability_does_not_imply_external_effect_authorization_v1,
    prove_standing_gate_chain_present_v1,
    standing_external_effect_authorization_policy_authorized_v1,
    validate_external_effect_authorization_policy_record_v1,
)
from src.governance.external_effect_authorization_policy_gate_binding_v1 import (
    evaluate_policy_bound_external_effect_gate_v1,
)
from src.governance.governed_external_effect_authorization_policy_closure_v1 import (
    prove_governed_external_effect_authorization_policy_v1,
)
from src.governance.governed_current_productive_chain_pre_external_to_external_effect_boundary_closure_v1 import (
    prove_governed_current_productive_chain_pre_external_to_external_effect_boundary_v1,
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
from src.ops.full_core_live_path_composition_root_v1.external_effect_gate_v1 import (
    FullCoreExternalEffectNotAuthorizedError,
    invoke_external_effect_v1,
)

REPO_ROOT = Path(__file__).resolve().parents[2]


def test_baseline_and_standing_pins() -> None:
    assert BASELINE_ORIGIN_MAIN_SHA == "b5e0fd94bbf7ba5f1742c98086e548d450ab4d2b"
    assert EXTERNAL_EFFECT_AUTHORIZED is False
    assert POST_ALLOWED is False
    assert REAL_VENUE_POST_ALLOWED is False
    assert AUTONOMY_CAN_MINT_PERMIT is False
    assert AUTONOMY_CAN_POST is False


def test_policy_record_valid_and_standing_authorized() -> None:
    result = validate_external_effect_authorization_policy_record_v1(repo_root=REPO_ROOT)
    assert result.policy_authorized is True, result.reason_codes
    assert result.policy_status == STATUS_POLICY_VALID
    assert standing_external_effect_authorization_policy_authorized_v1(repo_root=REPO_ROOT)


def test_policy_admission_granted_standing_flags_false() -> None:
    admission = evaluate_external_effect_policy_admission_v1(repo_root=REPO_ROOT)
    assert admission.admission_status == STATUS_ADMISSION_GRANTED
    assert admission.policy_admission_granted is True
    assert admission.standing_external_effect_authorized is False
    assert admission.post_allowed is False
    assert admission.real_venue_post_allowed is False
    assert admission.permit_mint_authorized is False
    assert admission.credential_access_performed is False
    assert admission.gate_decision is not None
    assert admission.gate_decision.external_effect_authorized is False
    assert admission.gate_decision.fail_closed is True


def test_gate_binding_matches_admission() -> None:
    bound = evaluate_policy_bound_external_effect_gate_v1(repo_root=REPO_ROOT)
    assert bound.policy_admission_granted is True
    assert bound.gate_decision.external_effect_authorized is False
    assert bound.standing_external_effect_authorized is True
    assert bound.extra.get("governed_standing_lift") == "true"
    assert bound.extra.get("governed_permit_mint") == "true"
    assert bound.extra.get("governed_credential_access") == "true"
    assert bound.permit_mint_authorized is True
    assert bound.credential_access_performed is False


def test_authority_separation_proofs() -> None:
    assert prove_pre_external_reachability_does_not_imply_external_effect_authorization_v1()
    assert prove_policy_does_not_authorize_permit_mint_v1()
    assert prove_policy_does_not_authorize_credential_access_v1()
    assert prove_policy_does_not_authorize_real_venue_post_v1()
    assert prove_standing_gate_chain_present_v1(repo_root=REPO_ROOT)


def test_closure_and_chain() -> None:
    assert prove_governed_external_effect_authorization_policy_v1(repo_root=REPO_ROOT)
    assert prove_governed_current_productive_chain_pre_external_to_external_effect_boundary_v1(
        repo_root=REPO_ROOT
    )


def test_decision_records_fail_closed() -> None:
    owner = json.loads((REPO_ROOT / OWNER_GO_DECISION_CONFIG).read_text(encoding="utf-8"))
    assert owner["external_effect_authorization_policy_owner_go"] is True
    assert owner["standing_external_effect_authorized"] is False
    assert owner["next_genuine_blocker"] == "EXTERNAL_EFFECT_STANDING_LIFT_OWNER_GO"
    decision = json.loads((REPO_ROOT / DECISION_CONFIG).read_text(encoding="utf-8"))
    assert decision["external_effect_authorization_policy_authorized"] is True
    assert decision["standing_external_effect_authorized"] is False
    assert decision["policy_implies_permit_mint"] is False
    assert decision["policy_implies_credential_access"] is False
    assert decision["policy_implies_real_venue_post"] is False


def test_invoke_external_effect_sink_still_fail_closed() -> None:
    assert standing_external_effect_authorization_policy_authorized_v1(repo_root=REPO_ROOT)
    with pytest.raises(FullCoreExternalEffectNotAuthorizedError):
        invoke_external_effect_v1(attempt_post=True)


def test_policy_record_digest_mismatch_fail_closed(tmp_path: Path) -> None:
    for rel in (
        POLICY_RECORD_CONFIG,
        OWNER_GO_DECISION_CONFIG,
        "config/governance/current_productive_activation_policy_v1_record.json",
        "config/governance/current_continuous_run_policy_v1_record.json",
        "config/governance/current_productive_activation_policy_owner_go_v1_decision.json",
        "config/governance/current_continuous_run_policy_owner_go_v1_decision.json",
        "config/governance/external_effect_boundary_forensic_review_v1_decision_v1.json",
    ):
        src = REPO_ROOT / rel
        dst = tmp_path / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        dst.write_text(src.read_text(encoding="utf-8"), encoding="utf-8")

    record = json.loads((tmp_path / POLICY_RECORD_CONFIG).read_text(encoding="utf-8"))
    record["policy_record_digest"] = "0" * 64
    (tmp_path / POLICY_RECORD_CONFIG).write_text(json.dumps(record, indent=2) + "\n")

    result = validate_external_effect_authorization_policy_record_v1(repo_root=tmp_path)
    assert result.policy_authorized is False
    assert "POLICY_RECORD_DIGEST_MISMATCH" in result.reason_codes


def test_owner_go_missing_fail_closed(tmp_path: Path) -> None:
    for rel in (
        POLICY_RECORD_CONFIG,
        "config/governance/current_productive_activation_policy_v1_record.json",
        "config/governance/current_continuous_run_policy_v1_record.json",
        "config/governance/external_effect_boundary_forensic_review_v1_decision_v1.json",
    ):
        src = REPO_ROOT / rel
        dst = tmp_path / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        dst.write_text(src.read_text(encoding="utf-8"), encoding="utf-8")

    owner_path = tmp_path / OWNER_GO_DECISION_CONFIG
    owner_path.parent.mkdir(parents=True, exist_ok=True)
    owner_path.write_text(
        json.dumps({"external_effect_authorization_policy_owner_go": False}) + "\n",
        encoding="utf-8",
    )

    result = validate_external_effect_authorization_policy_record_v1(repo_root=tmp_path)
    assert result.policy_authorized is False
    assert "OWNER_GO_DECISION_NOT_CONSUMED" in result.reason_codes


def test_canonical_body_stable() -> None:
    record = json.loads((REPO_ROOT / POLICY_RECORD_CONFIG).read_text(encoding="utf-8"))
    body = canonical_policy_record_body_v1(record)
    mutated = copy.deepcopy(record)
    mutated["semantic_definition"] = "tampered"
    assert canonical_policy_record_body_v1(mutated) != body
