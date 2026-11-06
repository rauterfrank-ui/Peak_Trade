"""Real-P4 to F1/M9 apply join fail-closed tests."""

from __future__ import annotations

from pathlib import Path

from src.governance.governed_runtime_apply_materialization_record_v1 import (
    RuntimeApplyMaterializationDecisionStateV1,
    build_materialization_record_body_v1,
    compute_lineage_chain_digest_v1,
)
from src.governance.real_p4_to_f1_m9_apply_lineage_join_v1 import (
    JOIN_STATUS_NOT_CANONICAL,
    evaluate_real_p4_to_f1_m9_apply_join_v1,
)
from tests.governance.test_f1_m9_scoped_owner_apply_authority_v1 import (
    _build_chain_artifacts,
)

REPO_ROOT = Path(__file__).resolve().parents[2]


def _sample_p4_record() -> dict:
    p4 = "a" * 64
    p3 = "b" * 64
    adj = "c" * 64
    env = "d" * 64
    lineage = compute_lineage_chain_digest_v1(
        lineage_chain=(
            f"optimization_envelope://{env}",
            f"adjudicator_a_opt://{adj}",
            f"p3_binding://{p3}",
            f"p4_l6_seam://{p4}",
        )
    )
    body = build_materialization_record_body_v1(
        decision_state=RuntimeApplyMaterializationDecisionStateV1.MATERIALIZATION_AUTHORIZED,
        p4_l6_seam_result_digest=p4,
        p3_binding_result_digest=p3,
        component_a_adjudication_digest=adj,
        optimization_envelope_content_hash=env,
        lineage_chain_digest=lineage,
        reason_codes=("TEST",),
        real_runtime_materialization_performed=True,
    )
    return dict(body)


def test_join_not_canonical_without_configuration(tmp_path: Path) -> None:
    result = evaluate_real_p4_to_f1_m9_apply_join_v1(
        materialization_record=_sample_p4_record(),
        configuration=None,
    )
    assert result.join_permitted is False
    assert result.join_status == JOIN_STATUS_NOT_CANONICAL
    assert result.lineage_join_valid is False


def test_join_denied_with_f1_configuration(tmp_path: Path) -> None:
    artifacts = _build_chain_artifacts(tmp_path)
    result = evaluate_real_p4_to_f1_m9_apply_join_v1(
        materialization_record=_sample_p4_record(),
        configuration=artifacts["configuration"],
    )
    assert result.join_permitted is False
    assert "CROSS_PLANE" in " ".join(result.reason_codes)
