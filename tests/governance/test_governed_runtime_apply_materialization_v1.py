"""Governed runtime apply materialization v1 — ingress, admission, negatives."""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path

import pytest

from src.governance.governed_runtime_apply_materialization_closure_v1 import (
    prove_governed_runtime_apply_materialization_v1,
)
from src.governance.governed_runtime_apply_materialization_record_v1 import (
    RuntimeApplyMaterializationDecisionStateV1,
)
from src.governance.governed_runtime_apply_materialization_v1 import (
    RUNTIME_APPLY_STARTED,
    RuntimeApplyMaterializationCallerClassV1,
    RuntimeApplyMaterializationEvaluateRequestV1,
    RuntimeApplyMaterializationIngressV1,
    evaluate_runtime_apply_materialization_v1,
    materialization_implies_configuration_applied_v1,
    prove_negative_runtime_apply_materialization_safety_invariants_v1,
    seam_bound_implies_productive_activation_v1,
    validate_runtime_apply_materialization_ingress_v1,
)
from src.governance.master_v2_double_play_evidence_input_plane_p4_l6_productive_seam_binding_v1.constants_v1 import (
    SEAM_BIND_DISPOSITION,
)
from src.meta.learning_loop.contract_safety_v1 import is_valid_sha256_hex

REPO_ROOT = Path(__file__).resolve().parents[2]


def _valid_ingress() -> RuntimeApplyMaterializationIngressV1:
    p4 = "a" * 64
    p3 = "b" * 64
    adj = "c" * 64
    env = "d" * 64
    chain = (
        f"optimization_envelope://{env}",
        f"adjudicator_a_opt://{adj}",
        f"p3_binding://{p3}",
        f"p4_l6_seam://{p4}",
    )
    return RuntimeApplyMaterializationIngressV1(
        p4_l6_seam_result_digest=p4,
        p3_binding_result_digest=p3,
        component_a_adjudication_digest=adj,
        optimization_envelope_content_hash=env,
        p4_seam_disposition=SEAM_BIND_DISPOSITION,
        lineage_chain=chain,
        real_upstream_source_used=True,
        ddo_fixture_state_used=False,
    )


def test_closure_proof_passes() -> None:
    assert prove_governed_runtime_apply_materialization_v1(repo_root=REPO_ROOT)


def test_materialization_eligible_and_authorized() -> None:
    ingress = _valid_ingress()
    eligible = evaluate_runtime_apply_materialization_v1(
        RuntimeApplyMaterializationEvaluateRequestV1(
            ingress=ingress,
            request_materialization_authorization=False,
        ),
        repo_root=REPO_ROOT,
    )
    assert (
        eligible.decision_state
        == RuntimeApplyMaterializationDecisionStateV1.MATERIALIZATION_ELIGIBLE
    )
    assert eligible.configuration_materialized is True
    assert eligible.configuration_applied is False
    assert eligible.real_runtime_materialization_performed is True
    rec = eligible.materialization_record
    assert rec is not None
    assert rec.materialization_record["runtime_apply_started"] is False

    authorized = evaluate_runtime_apply_materialization_v1(
        RuntimeApplyMaterializationEvaluateRequestV1(
            ingress=ingress,
            request_materialization_authorization=True,
        ),
        repo_root=REPO_ROOT,
    )
    assert (
        authorized.decision_state
        == RuntimeApplyMaterializationDecisionStateV1.MATERIALIZATION_AUTHORIZED
    )
    assert authorized.runtime_apply_authorization_valid is True


@pytest.mark.parametrize(
    "mutator,expected",
    [
        (lambda i: replace(i, ddo_fixture_state_used=True), "DDO_FIXTURE"),
        (lambda i: replace(i, p4_seam_disposition="SEAM_NO_BIND"), "P4_L6_SEAM_NOT_BOUND"),
        (lambda i: replace(i, p4_l6_seam_result_digest="b" * 64), "P4_L6_SEAM_LINEAGE_MISMATCH"),
    ],
)
def test_ingress_fail_closed(mutator, expected: str) -> None:
    ingress = mutator(_valid_ingress())
    reasons = validate_runtime_apply_materialization_ingress_v1(ingress)
    assert any(expected in r for r in reasons)


def test_forbidden_caller_classes() -> None:
    ingress = _valid_ingress()
    for caller in (
        RuntimeApplyMaterializationCallerClassV1.OPTIMIZATION,
        RuntimeApplyMaterializationCallerClassV1.COMPONENT_B,
    ):
        result = evaluate_runtime_apply_materialization_v1(
            RuntimeApplyMaterializationEvaluateRequestV1(
                ingress=ingress,
                caller_class=caller,
            ),
            repo_root=REPO_ROOT,
        )
        assert (
            result.decision_state
            == RuntimeApplyMaterializationDecisionStateV1.MATERIALIZATION_DENIED
        )


def test_safety_invariants() -> None:
    assert RUNTIME_APPLY_STARTED is False
    assert prove_negative_runtime_apply_materialization_safety_invariants_v1()
    assert seam_bound_implies_productive_activation_v1() is False
    assert materialization_implies_configuration_applied_v1() is False


def test_record_digests_are_sha256() -> None:
    result = evaluate_runtime_apply_materialization_v1(
        RuntimeApplyMaterializationEvaluateRequestV1(ingress=_valid_ingress()),
        repo_root=REPO_ROOT,
    )
    assert result.materialization_record is not None
    digest = result.materialization_record.materialization_record_digest
    assert is_valid_sha256_hex(digest)
