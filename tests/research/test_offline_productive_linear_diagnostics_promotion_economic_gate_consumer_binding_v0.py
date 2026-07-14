from __future__ import annotations

import json
import subprocess
import sys
from dataclasses import replace
from pathlib import Path

import pytest

from research.linear_evidence.import_boundary import scan_file_import_boundary
from research.linear_evidence.offline_productive_linear_diagnostics_economic_evidence_consumer_binding_v0 import (
    AUTHORITY_EFFECT,
    CONSUMER_BINDING_OWNER,
    EconomicEvidenceAdmissibility,
    LinearDiagnosticsEconomicEvidenceConsumerBindingV0,
    materialize_linear_diagnostics_economic_evidence_consumer_binding_v0,
)
from research.linear_evidence.offline_productive_linear_diagnostics_promotion_economic_gate_consumer_binding_v0 import (
    BLOCKING_REASON_BLOCKED_SOURCE_DIAGNOSTICS_PRESENT,
    BLOCKING_REASON_BLOCK_DRIFT_EXCEEDS_POLICY,
    BLOCKING_REASON_LINEAR_DIAGNOSTICS_INCONSISTENT,
    BLOCKING_REASON_RANK_DEFICIENT_BLOCKED,
    CANONICAL_PROMOTION_GATE_OWNER,
    PROMOTION_CONSUMER_BINDING_OWNER,
    PromotionEconomicGateConsumerBindingError,
    build_promotion_gate_input_from_linear_diagnostics_consumer_binding_v0,
    default_promotion_consumer_binding_context_v0,
    evaluate_promotion_economic_gate_from_linear_diagnostics_consumer_binding_v0,
    materialize_promotion_economic_gate_consumer_binding_v0,
)
from research.linear_evidence.offline_productive_linear_diagnostics_support_bundle_v0 import (
    DEFAULT_COST_DIAGNOSTICS_BUNDLE,
    DEFAULT_FACTOR_EXPOSURE_BUNDLE,
    DEFAULT_PARAMETER_SENSITIVITY_BUNDLE,
    DEFAULT_ROLLING_LINEAR_DRIFT_BUNDLE,
    DEFAULT_SIGNAL_ORTHOGONALITY_BUNDLE,
    DEFAULT_SOURCE_BUNDLE_SPECS,
    SupportAggregateStatus,
)
from scripts.ops.primary_evidence_retention_v0 import verify_manifest_sha256
from src.governance.economic_diagnostic_optimization_boundary_v0 import build_boundary_report
from src.governance.promotion_loop import promotion_economic_gate_v1 as gate

REPO_ROOT = Path(__file__).resolve().parents[2]
OWNER = REPO_ROOT / (
    "src/research/linear_evidence/"
    "offline_productive_linear_diagnostics_promotion_economic_gate_consumer_binding_v0.py"
)
MATERIALIZER = REPO_ROOT / (
    "scripts/ops/materialize_offline_productive_linear_diagnostics_"
    "promotion_economic_gate_consumer_binding_v0.py"
)
SOURCE_CLOSEOUT = Path(
    "/Users/frnkhrz/Documents/Peak_Trade_runtime_evidence_archive_20260520T161443Z/"
    "research/pr5186_merge_closeout_offline_productive_linear_diagnostics_"
    "economic_evidence_consumer_binding_v0_20260714T231652Z"
)

PRODUCTIVE_BUNDLES = {
    "cost_diagnostics": DEFAULT_COST_DIAGNOSTICS_BUNDLE,
    "signal_orthogonality": DEFAULT_SIGNAL_ORTHOGONALITY_BUNDLE,
    "factor_exposure": DEFAULT_FACTOR_EXPOSURE_BUNDLE,
    "parameter_sensitivity": DEFAULT_PARAMETER_SENSITIVITY_BUNDLE,
    "rolling_linear_drift": DEFAULT_ROLLING_LINEAR_DRIFT_BUNDLE,
}


def _archive_available() -> bool:
    return all(path.is_dir() for path in PRODUCTIVE_BUNDLES.values())


def _run_materializer(out_dir: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [
            sys.executable,
            str(MATERIALIZER),
            "--out",
            str(out_dir),
            "--skip-focused-tests",
        ],
        cwd=str(REPO_ROOT),
        check=False,
        text=True,
        capture_output=True,
        env={"PYTHONPATH": f"{REPO_ROOT / 'src'}:{REPO_ROOT}"},
    )


@pytest.fixture(scope="module")
def consumer_binding():
    if not _archive_available():
        pytest.skip("productive archive bundles unavailable")
    _, binding = materialize_linear_diagnostics_economic_evidence_consumer_binding_v0(
        source_specs=DEFAULT_SOURCE_BUNDLE_SPECS,
        verify_fn=verify_manifest_sha256,
        repo_root=REPO_ROOT,
    )
    return binding


@pytest.fixture(scope="module")
def promotion_binding(consumer_binding):
    return evaluate_promotion_economic_gate_from_linear_diagnostics_consumer_binding_v0(
        consumer_binding=consumer_binding,
    )


def test_canonical_promotion_gate_owner_reused() -> None:
    assert CANONICAL_PROMOTION_GATE_OWNER == gate.PROMOTION_ECONOMIC_GATE_POLICY_OWNER


def test_pr5186_consumer_input_promotion_blocked(promotion_binding) -> None:
    assert promotion_binding.promotion_economic_gate_status == "BLOCKED"
    assert promotion_binding.promotion_candidate_eligible is False
    assert promotion_binding.evidence_admissible is False
    assert promotion_binding.economic_evaluation_executed is False
    assert promotion_binding.economic_validity_pass_created is False
    assert promotion_binding.promotion_pass_created is False


def test_blocked_source_diagnostics_present_remains_blocking(promotion_binding) -> None:
    assert (
        promotion_binding.economic_evidence_admissibility
        == EconomicEvidenceAdmissibility.BLOCKED_SOURCE_DIAGNOSTICS_PRESENT.value
    )
    assert BLOCKING_REASON_BLOCKED_SOURCE_DIAGNOSTICS_PRESENT in promotion_binding.blocking_reason
    assert gate.REASON_ECONOMIC_EVIDENCE_INADMISSIBLE in promotion_binding.gate_result.reason_codes


def test_rank_deficient_blocked_remains_blocking(promotion_binding) -> None:
    assert promotion_binding.cost_diagnostics_status == "RANK_DEFICIENT_BLOCKED"
    assert promotion_binding.factor_exposure_status == "RANK_DEFICIENT_BLOCKED"
    assert BLOCKING_REASON_RANK_DEFICIENT_BLOCKED in promotion_binding.blocking_reason


def test_block_drift_exceeds_policy_remains_blocking(promotion_binding) -> None:
    assert promotion_binding.rolling_linear_drift_status == "BLOCK_DRIFT_EXCEEDS_POLICY"
    assert BLOCKING_REASON_BLOCK_DRIFT_EXCEEDS_POLICY in promotion_binding.blocking_reason


def test_signal_orthogonality_ok_alone_does_not_pass(promotion_binding) -> None:
    assert promotion_binding.signal_orthogonality_status == "OK"
    assert promotion_binding.promotion_candidate_eligible is False
    assert promotion_binding.gate_result.economic_validity_pass is False


def test_robust_region_observed_alone_does_not_pass(promotion_binding) -> None:
    assert promotion_binding.parameter_sensitivity_status == "ROBUST_REGION_OBSERVED"
    assert promotion_binding.promotion_candidate_eligible is False
    assert promotion_binding.gate_result.robustness_pass is False


def test_missing_linear_diagnostics_no_implicit_pass() -> None:
    broken = LinearDiagnosticsEconomicEvidenceConsumerBindingV0(
        schema_version="offline_productive_linear_diagnostics_economic_evidence_consumer_binding.v0",
        owner=CONSUMER_BINDING_OWNER,
        economic_viability_evidence_consumer_target="target",
        linear_diagnostics_referenced=False,
        linear_diagnostic_class_count=0,
        cost_model_calibration_ref="",
        signal_orthogonality_ref="",
        factor_exposure_ref="",
        parameter_sensitivity_ref="",
        rolling_linear_drift_ref="",
        cost_diagnostics_status="",
        signal_orthogonality_status="",
        factor_exposure_status="",
        parameter_sensitivity_status="",
        rolling_linear_drift_status="",
        aggregate_status=SupportAggregateStatus.INSUFFICIENT_OR_UNVERIFIED_SOURCE_EVIDENCE.value,
        aggregate_reason_codes=("INSUFFICIENT_SOURCE",),
        economic_viability_support_status="INSUFFICIENT_SOURCE_BINDING",
        linear_diagnostics_status=SupportAggregateStatus.INSUFFICIENT_OR_UNVERIFIED_SOURCE_EVIDENCE.value,
        linear_diagnostics_reason_codes=("INSUFFICIENT_SOURCE",),
        economic_evidence_admissibility=(
            EconomicEvidenceAdmissibility.INSUFFICIENT_OR_UNVERIFIED_SOURCE_EVIDENCE.value
        ),
        support_bundle_output_digest="0" * 64,
        economic_pass_authority=False,
        promotion_pass_authority=False,
        strategy_selection_authority=False,
        runtime_effect=AUTHORITY_EFFECT,
        authority_effect=AUTHORITY_EFFECT,
    )
    ctx = default_promotion_consumer_binding_context_v0(broken)
    gate_input = build_promotion_gate_input_from_linear_diagnostics_consumer_binding_v0(
        ctx=ctx,
        consumer_binding=broken,
    )
    result = evaluate_promotion_economic_gate_from_linear_diagnostics_consumer_binding_v0(
        consumer_binding=broken,
        ctx=ctx,
    )
    assert gate_input.evidence_admissible is False
    assert result.promotion_candidate_eligible is False
    assert result.promotion_economic_gate_status in {"BLOCKED", "INELIGIBLE"}


def test_unknown_status_no_implicit_pass(consumer_binding) -> None:
    mutated = replace(consumer_binding, parameter_sensitivity_status="MAYBE_UNKNOWN")
    ctx = default_promotion_consumer_binding_context_v0(mutated)
    result = evaluate_promotion_economic_gate_from_linear_diagnostics_consumer_binding_v0(
        consumer_binding=mutated,
        ctx=ctx,
    )
    assert result.promotion_candidate_eligible is False
    assert any(
        code.startswith(gate.REASON_REQUIRED_STATUS_UNKNOWN)
        for code in result.gate_result.reason_codes
    )


def test_inconsistent_aggregate_rejected(consumer_binding) -> None:
    inconsistent = replace(
        consumer_binding,
        aggregate_status=SupportAggregateStatus.BLOCK_SUPPORT_EVIDENCE.value,
        economic_evidence_admissibility=(
            EconomicEvidenceAdmissibility.DIAGNOSTIC_SUPPORT_REFERENCE_READY.value
        ),
    )
    ctx = default_promotion_consumer_binding_context_v0(inconsistent)
    with pytest.raises(PromotionEconomicGateConsumerBindingError, match="INCONSISTENT"):
        build_promotion_gate_input_from_linear_diagnostics_consumer_binding_v0(
            ctx=ctx,
            consumer_binding=inconsistent,
        )


def test_inadmissible_economic_evidence_not_promotion_candidate(promotion_binding) -> None:
    assert promotion_binding.evidence_admissible is False
    assert promotion_binding.promotion_candidate_eligible is False
    assert promotion_binding.gate_result.eligible_for_promotion_candidate is False


def test_linear_diagnostics_alone_no_promotion_pass(promotion_binding) -> None:
    assert promotion_binding.promotion_pass_created is False
    assert promotion_binding.gate_result.promotion_eligible is False
    assert promotion_binding.gate_result.shadow_candidate_eligible is False
    assert promotion_binding.gate_result.paper_candidate_eligible is False
    assert promotion_binding.gate_result.testnet_candidate_eligible is False


def test_authority_and_runtime_effects_none(promotion_binding) -> None:
    assert promotion_binding.runtime_effect == AUTHORITY_EFFECT == "NONE"
    assert promotion_binding.authority_effect == "NONE"
    assert promotion_binding.gate_result.authority_effect == gate.AUTHORITY_EFFECT_NONE
    assert promotion_binding.gate_result.runtime_effect == gate.RUNTIME_EFFECT_NONE


def test_import_boundary_owner_and_materializer() -> None:
    assert scan_file_import_boundary(OWNER, repo_root=REPO_ROOT) == []
    assert scan_file_import_boundary(MATERIALIZER, repo_root=REPO_ROOT) == []


def test_governance_boundary_guard_accepts_new_owner() -> None:
    changed_files = [
        "src/research/linear_evidence/offline_productive_linear_diagnostics_promotion_economic_gate_consumer_binding_v0.py",
        "scripts/ops/materialize_offline_productive_linear_diagnostics_promotion_economic_gate_consumer_binding_v0.py",
        "tests/research/test_offline_productive_linear_diagnostics_promotion_economic_gate_consumer_binding_v0.py",
        "config/governance/economic_diagnostic_optimization_boundary_canonical_owner_map_v0.json",
    ]
    report = build_boundary_report(changed_files, repo_root=REPO_ROOT)
    assert report.admissible is True
    assert report.impact_unknown is False


def test_repeated_materialization_deterministic(consumer_binding) -> None:
    first = evaluate_promotion_economic_gate_from_linear_diagnostics_consumer_binding_v0(
        consumer_binding=consumer_binding,
    )
    second = evaluate_promotion_economic_gate_from_linear_diagnostics_consumer_binding_v0(
        consumer_binding=consumer_binding,
    )
    assert first.to_dict() == second.to_dict()


def test_source_closeout_manifest_verified() -> None:
    if not SOURCE_CLOSEOUT.is_dir():
        pytest.skip("source closeout unavailable")
    ok, _ = verify_manifest_sha256(SOURCE_CLOSEOUT)
    assert ok


def test_materializer_roundtrip(tmp_path: Path) -> None:
    if not _archive_available():
        pytest.skip("productive archive bundles unavailable")

    first_dir = tmp_path / "evidence_a"
    second_dir = tmp_path / "evidence_b"
    first = _run_materializer(first_dir)
    second = _run_materializer(second_dir)
    assert first.returncode == 0, first.stderr
    assert second.returncode == 0, second.stderr

    for bundle in (first_dir, second_dir):
        ok, _ = verify_manifest_sha256(bundle)
        assert ok

    contract_a = json.loads((first_dir / "consumer_contract.json").read_text(encoding="utf-8"))
    contract_b = json.loads((second_dir / "consumer_contract.json").read_text(encoding="utf-8"))
    assert contract_a == contract_b
    assert contract_a["promotion_economic_gate_status"] == "BLOCKED"
    assert contract_a["promotion_candidate_eligible"] is False


def test_real_productive_materialize_path_not_test_copy() -> None:
    if not _archive_available():
        pytest.skip("productive archive bundles unavailable")
    _, consumer, promotion = materialize_promotion_economic_gate_consumer_binding_v0(
        source_specs=DEFAULT_SOURCE_BUNDLE_SPECS,
        verify_fn=verify_manifest_sha256,
        repo_root=REPO_ROOT,
    )
    assert consumer.linear_diagnostics_referenced is True
    assert promotion.owner == PROMOTION_CONSUMER_BINDING_OWNER
    assert promotion.canonical_promotion_gate_owner == gate.PROMOTION_ECONOMIC_GATE_POLICY_OWNER
    assert promotion.gate_result.gate_policy_id == gate.PROMOTION_ECONOMIC_GATE_POLICY_ID
    assert promotion.promotion_economic_gate_status == "BLOCKED"
