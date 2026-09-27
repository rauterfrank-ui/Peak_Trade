"""Standing External Effect Lift policy v1 tests."""

from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest

from src.governance.external_effect_authorization_policy_v1 import (
    standing_external_effect_authorization_policy_authorized_v1,
)
from src.governance.governed_current_productive_chain_pre_external_to_external_effect_boundary_closure_v1 import (
    CANONICAL_EXTERNAL_EFFECT_BOUNDARY,
    prove_governed_current_productive_chain_pre_external_to_external_effect_boundary_v1,
)
from src.governance.governed_standing_external_effect_lift_policy_closure_v1 import (
    prove_governed_standing_external_effect_lift_policy_v1,
)
from src.governance.standing_external_effect_lift_gate_binding_v1 import (
    evaluate_lift_bound_external_effect_gate_v1,
)
from src.governance.standing_external_effect_lift_policy_v1 import (
    BASELINE_ORIGIN_MAIN_SHA,
    DECISION_CONFIG,
    OWNER_GO_DECISION_CONFIG,
    POLICY_RECORD_CONFIG,
    STATUS_LIFT_GRANTED,
    STATUS_POLICY_VALID,
    canonical_policy_record_body_v1,
    evaluate_standing_external_effect_lift_admission_v1,
    governed_standing_external_effect_authorized_v1,
    prove_import_time_standing_constant_unchanged_v1,
    prove_lift_does_not_authorize_permit_mint_v1,
    prove_lift_does_not_authorize_real_venue_post_v1,
    standing_external_effect_lift_granted_v1,
    validate_standing_external_effect_lift_policy_record_v1,
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
    evaluate_external_effect_v1,
    invoke_external_effect_v1,
)

REPO_ROOT = Path(__file__).resolve().parents[2]


def test_baseline_and_import_time_standing() -> None:
    assert BASELINE_ORIGIN_MAIN_SHA == "2309dbd5b04a2fc2b41d88d9905d96671e51b1e3"
    assert prove_import_time_standing_constant_unchanged_v1()
    assert EXTERNAL_EFFECT_AUTHORIZED is False
    assert POST_ALLOWED is False
    assert REAL_VENUE_POST_ALLOWED is False


def test_lift_policy_record_valid() -> None:
    result = validate_standing_external_effect_lift_policy_record_v1(repo_root=REPO_ROOT)
    assert result.lift_policy_authorized is True, result.reason_codes
    assert result.policy_status == STATUS_POLICY_VALID
    assert standing_external_effect_lift_granted_v1(repo_root=REPO_ROOT)


def test_positive_lift_admission_and_gate_standing() -> None:
    assert standing_external_effect_authorization_policy_authorized_v1(repo_root=REPO_ROOT)
    admission = evaluate_standing_external_effect_lift_admission_v1(repo_root=REPO_ROOT)
    assert admission.admission_status == STATUS_LIFT_GRANTED
    assert admission.standing_external_effect_lift_granted is True
    assert admission.governed_standing_external_effect_authorized is True
    assert admission.gate_decision is not None
    assert admission.gate_decision.external_effect_authorized is True
    assert admission.gate_decision.fail_closed is False
    assert admission.post_allowed is False
    assert admission.permit_mint_authorized is False
    assert governed_standing_external_effect_authorized_v1(repo_root=REPO_ROOT) is True


def test_gate_binding_lift_vs_import_standing() -> None:
    bound = evaluate_lift_bound_external_effect_gate_v1(repo_root=REPO_ROOT)
    assert bound.lift_admission_granted is True
    assert bound.policy_bound_admission_granted is True
    assert bound.gate_decision_at_lift_standing.external_effect_authorized is True
    assert bound.gate_decision_at_import_standing.external_effect_authorized is False
    assert bound.governed_standing_external_effect_authorized is True


def test_default_gate_and_invoke_remain_fail_closed_for_sink() -> None:
    assert evaluate_external_effect_v1().external_effect_authorized is False
    with pytest.raises(FullCoreExternalEffectNotAuthorizedError):
        invoke_external_effect_v1(attempt_post=True)


def test_authority_separation_proofs() -> None:
    assert prove_lift_does_not_authorize_permit_mint_v1()
    assert prove_lift_does_not_authorize_real_venue_post_v1()
    assert AUTONOMY_CAN_MINT_PERMIT is False
    assert AUTONOMY_CAN_POST is False


def test_closure_and_chain() -> None:
    assert prove_governed_standing_external_effect_lift_policy_v1(repo_root=REPO_ROOT)
    assert prove_governed_current_productive_chain_pre_external_to_external_effect_boundary_v1(
        repo_root=REPO_ROOT
    )


def test_decision_records() -> None:
    owner = json.loads((REPO_ROOT / OWNER_GO_DECISION_CONFIG).read_text(encoding="utf-8"))
    assert owner["standing_external_effect_lift_owner_go"] is True
    assert owner["import_time_external_effect_authorized"] is False
    assert owner["next_genuine_blocker"] == "EXTERNAL_EFFECT_PERMIT_MINT_OWNER_GO"
    decision = json.loads((REPO_ROOT / DECISION_CONFIG).read_text(encoding="utf-8"))
    assert decision["governed_standing_external_effect_authorized"] is True
    assert decision["lift_implies_permit_mint"] is False
    assert decision["post_allowed"] is False


def test_canonical_boundary_constant_updated() -> None:
    assert CANONICAL_EXTERNAL_EFFECT_BOUNDARY == (
        "STANDING_LIFT_GOVERNED_PERMIT_MINT_POLICY_BOUND_CREDENTIAL_POST_FAIL_CLOSED"
    )


def test_lift_record_digest_mismatch_fail_closed(tmp_path: Path) -> None:
    for rel in (
        POLICY_RECORD_CONFIG,
        OWNER_GO_DECISION_CONFIG,
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

    result = validate_standing_external_effect_lift_policy_record_v1(repo_root=tmp_path)
    assert result.lift_policy_authorized is False
    assert "POLICY_RECORD_DIGEST_MISMATCH" in result.reason_codes


def test_owner_go_missing_fail_closed(tmp_path: Path) -> None:
    for rel in (
        POLICY_RECORD_CONFIG,
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
        json.dumps({"standing_external_effect_lift_owner_go": False}) + "\n",
        encoding="utf-8",
    )

    result = validate_standing_external_effect_lift_policy_record_v1(repo_root=tmp_path)
    assert result.lift_policy_authorized is False
    assert "OWNER_GO_DECISION_NOT_CONSUMED" in result.reason_codes


def test_canonical_body_stable() -> None:
    record = json.loads((REPO_ROOT / POLICY_RECORD_CONFIG).read_text(encoding="utf-8"))
    body = canonical_policy_record_body_v1(record)
    mutated = copy.deepcopy(record)
    mutated["semantic_definition"] = "tampered"
    assert canonical_policy_record_body_v1(mutated) != body
