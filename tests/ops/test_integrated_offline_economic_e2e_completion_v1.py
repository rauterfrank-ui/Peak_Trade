"""End-to-end productive offline economic completion tests."""

from __future__ import annotations

from pathlib import Path

from src.ops.integrated_offline_economic_evidence_v1.integrated_offline_economic_validity_adjudication_v1 import (
    evaluate_integrated_offline_economic_validity_v1,
)
from src.ops.integrated_offline_economic_evidence_v1.integrated_verifier_v1 import (
    verify_integrated_offline_economic_evidence_v1,
)
from src.ops.integrated_offline_economic_evidence_v1.productive_offline_economic_completion_v1 import (
    produce_productive_offline_economic_completion_bundle_v1,
)

REPO_ROOT = Path(__file__).resolve().parents[2]


def test_productive_offline_economic_e2e_completion(tmp_path: Path) -> None:
    rel = "evidence/ops/integrated_offline_economic_evidence_v1/e2e_test_bundle_v1"
    produced = produce_productive_offline_economic_completion_bundle_v1(
        repo_root=REPO_ROOT,
        evidence_relpath=rel,
    )
    assert produced.md_bridge_verified is True
    assert produced.productive_decision_equivalence_verified is True
    assert produced.comparison_rows > 0
    assert not produced.blockers

    verified = verify_integrated_offline_economic_evidence_v1(
        repo_root=REPO_ROOT,
        evidence_root=REPO_ROOT / rel,
        expected_proven_source_sha=produced.proven_source_sha,
    )
    assert verified.canonical_identity_verified is True
    assert verified.verified is True
    assert verified.offline_economic_evidence_complete is True

    adjudicated = evaluate_integrated_offline_economic_validity_v1(
        repo_root=REPO_ROOT,
        evidence_root=REPO_ROOT / rel,
        expected_proven_source_sha=produced.proven_source_sha,
        verification=verified,
    )
    assert adjudicated.economic_validity_evaluated is True
    assert adjudicated.walk_forward_monte_carlo_stress_requirements_met is True
    assert adjudicated.operator_ratification_required is True
    if produced.trade_count == 0:
        assert adjudicated.economic_validity_pass is False
        assert "ECONOMIC_ZERO_OR_INSUFFICIENT_TRADES" in adjudicated.failure_reasons
