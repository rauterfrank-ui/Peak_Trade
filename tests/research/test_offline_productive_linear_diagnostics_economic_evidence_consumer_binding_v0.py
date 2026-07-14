from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

from research.linear_evidence.import_boundary import scan_file_import_boundary
from research.linear_evidence.offline_productive_linear_diagnostics_economic_evidence_consumer_binding_v0 import (
    AUTHORITY_EFFECT,
    CONSUMER_BINDING_OWNER,
    EconomicEvidenceAdmissibility,
    LinearDiagnosticsConsumerBindingError,
    apply_linear_diagnostics_refs_to_economic_viability_evidence_v0,
    bind_linear_diagnostics_economic_evidence_consumer_v0,
    derive_linear_diagnostics_reason_codes_v0,
    materialize_linear_diagnostics_economic_evidence_consumer_binding_v0,
)
from research.linear_evidence.offline_productive_linear_diagnostics_support_bundle_v0 import (
    DEFAULT_COST_DIAGNOSTICS_BUNDLE,
    DEFAULT_FACTOR_EXPOSURE_BUNDLE,
    DEFAULT_PARAMETER_SENSITIVITY_BUNDLE,
    DEFAULT_ROLLING_LINEAR_DRIFT_BUNDLE,
    DEFAULT_SIGNAL_ORTHOGONALITY_BUNDLE,
    DEFAULT_SOURCE_BUNDLE_SPECS,
    EconomicViabilitySupportStatus,
    SourceBundleSpecV0,
    SupportAggregateStatus,
    build_productive_linear_diagnostics_support_bundle_artifacts_v0,
)
from scripts.ops.primary_evidence_retention_v0 import verify_manifest_sha256
from src.backtest.economic_viability_evidence_v1 import (
    EconomicViabilityEvidenceV1,
    EconomicViabilityStatus,
    MetricFieldV1,
    MetricSemantic,
)
from src.governance.economic_diagnostic_optimization_boundary_v0 import build_boundary_report

REPO_ROOT = Path(__file__).resolve().parents[2]
OWNER = REPO_ROOT / (
    "src/research/linear_evidence/"
    "offline_productive_linear_diagnostics_economic_evidence_consumer_binding_v0.py"
)
MATERIALIZER = REPO_ROOT / (
    "scripts/ops/materialize_offline_productive_linear_diagnostics_"
    "economic_evidence_consumer_binding_v0.py"
)

PRODUCTIVE_BUNDLES = {
    "cost_diagnostics": DEFAULT_COST_DIAGNOSTICS_BUNDLE,
    "signal_orthogonality": DEFAULT_SIGNAL_ORTHOGONALITY_BUNDLE,
    "factor_exposure": DEFAULT_FACTOR_EXPOSURE_BUNDLE,
    "parameter_sensitivity": DEFAULT_PARAMETER_SENSITIVITY_BUNDLE,
    "rolling_linear_drift": DEFAULT_ROLLING_LINEAR_DRIFT_BUNDLE,
}

SOURCE_CLOSEOUT = Path(
    "/Users/frnkhrz/Documents/Peak_Trade_runtime_evidence_archive_20260520T161443Z/"
    "research/pr5185_merge_closeout_offline_productive_linear_diagnostics_support_bundle_v0_"
    "20260714T230433Z"
)


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
def support_bundle():
    if not _archive_available():
        pytest.skip("productive archive bundles unavailable")
    return build_productive_linear_diagnostics_support_bundle_artifacts_v0(
        source_specs=DEFAULT_SOURCE_BUNDLE_SPECS,
        verify_fn=verify_manifest_sha256,
        repo_root=REPO_ROOT,
    )


def test_all_five_manifest_verified_references_accepted(consumer_binding) -> None:
    assert consumer_binding.linear_diagnostics_referenced is True
    assert consumer_binding.linear_diagnostic_class_count == 5
    assert consumer_binding.cost_model_calibration_ref == str(DEFAULT_COST_DIAGNOSTICS_BUNDLE)
    assert consumer_binding.signal_orthogonality_ref == str(DEFAULT_SIGNAL_ORTHOGONALITY_BUNDLE)
    assert consumer_binding.factor_exposure_ref == str(DEFAULT_FACTOR_EXPOSURE_BUNDLE)
    assert consumer_binding.parameter_sensitivity_ref == str(DEFAULT_PARAMETER_SENSITIVITY_BUNDLE)
    assert consumer_binding.rolling_linear_drift_ref == str(DEFAULT_ROLLING_LINEAR_DRIFT_BUNDLE)


def test_source_statuses_preserved(consumer_binding) -> None:
    assert consumer_binding.cost_diagnostics_status == "RANK_DEFICIENT_BLOCKED"
    assert consumer_binding.signal_orthogonality_status == "OK"
    assert consumer_binding.factor_exposure_status == "RANK_DEFICIENT_BLOCKED"
    assert consumer_binding.parameter_sensitivity_status == "ROBUST_REGION_OBSERVED"
    assert consumer_binding.rolling_linear_drift_status == "BLOCK_DRIFT_EXCEEDS_POLICY"


def test_aggregate_deterministically_reconstructed(consumer_binding) -> None:
    assert consumer_binding.aggregate_status == SupportAggregateStatus.BLOCK_SUPPORT_EVIDENCE.value
    assert (
        consumer_binding.economic_viability_support_status
        == EconomicViabilitySupportStatus.BLOCKED_SOURCE_DIAGNOSTICS_PRESENT.value
    )
    assert (
        consumer_binding.linear_diagnostics_status
        == SupportAggregateStatus.BLOCK_SUPPORT_EVIDENCE.value
    )


def test_blocking_source_statuses_remain_blocking(consumer_binding) -> None:
    assert "COST_DIAGNOSTICS_RANK_DEFICIENT" in consumer_binding.linear_diagnostics_reason_codes
    assert "FACTOR_EXPOSURE_RANK_DEFICIENT" in consumer_binding.linear_diagnostics_reason_codes
    assert "ROLLING_LINEAR_DRIFT_EXCEEDS_POLICY" in consumer_binding.linear_diagnostics_reason_codes
    assert (
        consumer_binding.economic_evidence_admissibility
        == EconomicEvidenceAdmissibility.BLOCKED_SOURCE_DIAGNOSTICS_PRESENT.value
    )


def test_signal_orthogonality_ok_does_not_clear_blockers(consumer_binding) -> None:
    assert consumer_binding.signal_orthogonality_status == "OK"
    assert consumer_binding.aggregate_status == SupportAggregateStatus.BLOCK_SUPPORT_EVIDENCE.value
    assert (
        consumer_binding.economic_evidence_admissibility
        == EconomicEvidenceAdmissibility.BLOCKED_SOURCE_DIAGNOSTICS_PRESENT.value
    )


def test_parameter_sensitivity_robust_region_does_not_create_economic_pass(
    consumer_binding,
) -> None:
    assert consumer_binding.parameter_sensitivity_status == "ROBUST_REGION_OBSERVED"
    assert consumer_binding.economic_pass_authority is False
    assert (
        consumer_binding.economic_evidence_admissibility
        != EconomicEvidenceAdmissibility.DIAGNOSTIC_SUPPORT_REFERENCE_READY.value
    )


def test_linear_diagnostics_alone_cannot_set_economically_viable_offline(consumer_binding) -> None:
    assert consumer_binding.economic_pass_authority is False
    assert consumer_binding.promotion_pass_authority is False
    assert consumer_binding.strategy_selection_authority is False


def test_missing_reference_blocked(support_bundle) -> None:
    broken = dict(support_bundle)
    broken["cost_diagnostics_ref"] = ""
    with pytest.raises(LinearDiagnosticsConsumerBindingError, match="MISSING_DIAGNOSTIC_REF"):
        bind_linear_diagnostics_economic_evidence_consumer_v0(
            support_bundle=broken,
            verify_fn=verify_manifest_sha256,
        )


def test_source_manifest_rc_not_zero_blocked(support_bundle) -> None:
    def _fail_verify(_: Path) -> tuple[bool, str]:
        return False, "MANIFEST_MISMATCH"

    with pytest.raises(
        LinearDiagnosticsConsumerBindingError, match="SOURCE_MANIFEST_VERIFY_FAILED"
    ):
        bind_linear_diagnostics_economic_evidence_consumer_v0(
            support_bundle=support_bundle,
            verify_fn=_fail_verify,
        )


def test_unknown_diagnostic_class_blocked(support_bundle) -> None:
    with pytest.raises(LinearDiagnosticsConsumerBindingError, match="UNKNOWN_DIAGNOSTIC_CLASS"):
        bind_linear_diagnostics_economic_evidence_consumer_v0(
            support_bundle=support_bundle,
            verify_fn=verify_manifest_sha256,
            expected_source_statuses={"unknown_class": "OK"},
        )


def test_contradictory_source_status_blocked(support_bundle) -> None:
    with pytest.raises(LinearDiagnosticsConsumerBindingError, match="CONTRADICTORY_SOURCE_STATUS"):
        bind_linear_diagnostics_economic_evidence_consumer_v0(
            support_bundle=support_bundle,
            verify_fn=verify_manifest_sha256,
            expected_source_statuses={"cost_diagnostics": "OK"},
        )


def test_repeated_materialization_deterministic(consumer_binding) -> None:
    _, second = materialize_linear_diagnostics_economic_evidence_consumer_binding_v0(
        source_specs=DEFAULT_SOURCE_BUNDLE_SPECS,
        verify_fn=verify_manifest_sha256,
        repo_root=REPO_ROOT,
    )
    assert second.to_dict() == consumer_binding.to_dict()
    assert second.support_bundle_output_digest == consumer_binding.support_bundle_output_digest


def test_second_materialization_no_semantic_diff(consumer_binding) -> None:
    first_payload = json.dumps(consumer_binding.to_dict(), sort_keys=True, separators=(",", ":"))
    _, second = materialize_linear_diagnostics_economic_evidence_consumer_binding_v0(
        source_specs=DEFAULT_SOURCE_BUNDLE_SPECS,
        verify_fn=verify_manifest_sha256,
        repo_root=REPO_ROOT,
    )
    second_payload = json.dumps(second.to_dict(), sort_keys=True, separators=(",", ":"))
    assert first_payload == second_payload


def test_runtime_and_authority_effects_none(consumer_binding) -> None:
    assert consumer_binding.runtime_effect == AUTHORITY_EFFECT == "NONE"
    assert consumer_binding.authority_effect == "NONE"


def test_import_boundary_owner_and_materializer() -> None:
    assert scan_file_import_boundary(OWNER, repo_root=REPO_ROOT) == []
    assert scan_file_import_boundary(MATERIALIZER, repo_root=REPO_ROOT) == []


def test_governance_boundary_guard_accepts_new_owner() -> None:
    changed_files = [
        "src/research/linear_evidence/offline_productive_linear_diagnostics_economic_evidence_consumer_binding_v0.py",
        "scripts/ops/materialize_offline_productive_linear_diagnostics_economic_evidence_consumer_binding_v0.py",
        "tests/research/test_offline_productive_linear_diagnostics_economic_evidence_consumer_binding_v0.py",
        "config/governance/economic_diagnostic_optimization_boundary_canonical_owner_map_v0.json",
    ]
    report = build_boundary_report(changed_files, repo_root=REPO_ROOT)
    assert report.admissible is True
    assert report.impact_unknown is False


def test_apply_refs_to_economic_viability_evidence_preserves_status(consumer_binding) -> None:
    evidence = EconomicViabilityEvidenceV1(
        contract_version="v1",
        owner="backtest.economic_viability_evidence_v1",
        strategy_id="test",
        strategy_version="v0",
        instrument_id_or_universe="ETH-USDT-SWAP",
        canonical_trading_logic_version="v1",
        data_period="p",
        training_period="p",
        validation_period="p",
        out_of_sample_period="p",
        fee_model_version="v0",
        slippage_model_version="v0",
        funding_model_version="v0",
        execution_model_version="v0",
        config_digest="c",
        implementation_digest="i",
        data_digest="d",
        gross_return=MetricFieldV1(semantic=MetricSemantic.NOT_COMPUTED),
        net_return=MetricFieldV1(semantic=MetricSemantic.NOT_COMPUTED),
        net_expectancy=MetricFieldV1(semantic=MetricSemantic.NOT_COMPUTED),
        profit_factor=MetricFieldV1(semantic=MetricSemantic.NOT_COMPUTED),
        sharpe=MetricFieldV1(semantic=MetricSemantic.NOT_COMPUTED),
        sortino=MetricFieldV1(semantic=MetricSemantic.NOT_COMPUTED),
        max_drawdown=MetricFieldV1(semantic=MetricSemantic.NOT_COMPUTED),
        calmar=MetricFieldV1(semantic=MetricSemantic.NOT_COMPUTED),
        trade_count=MetricFieldV1(semantic=MetricSemantic.NOT_COMPUTED),
        turnover=MetricFieldV1(semantic=MetricSemantic.NOT_COMPUTED),
        fee_drag=MetricFieldV1(semantic=MetricSemantic.NOT_COMPUTED),
        funding_drag=MetricFieldV1(semantic=MetricSemantic.NOT_COMPUTED),
        slippage_impact=MetricFieldV1(semantic=MetricSemantic.NOT_COMPUTED),
        tail_loss=MetricFieldV1(semantic=MetricSemantic.NOT_COMPUTED),
        time_in_market=MetricFieldV1(semantic=MetricSemantic.NOT_COMPUTED),
        long_contribution=MetricFieldV1(semantic=MetricSemantic.NOT_COMPUTED),
        short_contribution=MetricFieldV1(semantic=MetricSemantic.NOT_COMPUTED),
        regime_breakdown={},
        portfolio_contribution={},
        walk_forward_results={},
        monte_carlo_results={},
        stress_results={},
        parameter_sensitivity_results={},
        parameter_neighbor_degradation=MetricFieldV1(semantic=MetricSemantic.NOT_COMPUTED),
        single_trade_profit_contribution=MetricFieldV1(semantic=MetricSemantic.NOT_COMPUTED),
        single_regime_profit_contribution=MetricFieldV1(semantic=MetricSemantic.NOT_COMPUTED),
        status=EconomicViabilityStatus.RESEARCH_ONLY,
        reason_codes=("configured_strategy_signal_bound",),
        manifest_digest="m",
        wiring_chain_digest="w",
        randomness_seed=0,
        data_admissibility={},
        cost_binding={},
    )
    bound = apply_linear_diagnostics_refs_to_economic_viability_evidence_v0(
        evidence, consumer_binding
    )
    assert bound.status is EconomicViabilityStatus.RESEARCH_ONLY
    assert bound.factor_exposure_ref == consumer_binding.factor_exposure_ref
    assert "factor_exposure_ref" in bound.to_semantic_dict()


def test_derive_reason_codes_includes_blocking_classes() -> None:
    reason_codes = derive_linear_diagnostics_reason_codes_v0(
        source_statuses={
            "cost_diagnostics": "RANK_DEFICIENT_BLOCKED",
            "factor_exposure": "RANK_DEFICIENT_BLOCKED",
            "rolling_linear_drift": "BLOCK_DRIFT_EXCEEDS_POLICY",
        },
        aggregate_reason_codes=("BLOCKED_SOURCE:cost_diagnostics:RANK_DEFICIENT_BLOCKED",),
    )
    assert "COST_DIAGNOSTICS_RANK_DEFICIENT" in reason_codes
    assert "FACTOR_EXPOSURE_RANK_DEFICIENT" in reason_codes
    assert "ROLLING_LINEAR_DRIFT_EXCEEDS_POLICY" in reason_codes


def test_missing_source_evidence_fail_closed(tmp_path: Path) -> None:
    missing_spec = SourceBundleSpecV0(
        diagnostic_class="cost_diagnostics",
        evidence_type="offline_linear_cost_model_diagnostics.v0",
        bundle_path=tmp_path / "missing_bundle",
        status_artifact="reason_codes.json",
    )
    specs = (missing_spec, *DEFAULT_SOURCE_BUNDLE_SPECS[1:])
    with pytest.raises(Exception, match="SOURCE_BUNDLE_MISSING"):
        materialize_linear_diagnostics_economic_evidence_consumer_binding_v0(
            source_specs=specs,
            verify_fn=verify_manifest_sha256,
            repo_root=REPO_ROOT,
        )


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

    binding_a = json.loads((first_dir / "consumer_contract.json").read_text(encoding="utf-8"))
    binding_b = json.loads((second_dir / "consumer_contract.json").read_text(encoding="utf-8"))
    assert binding_a == binding_b
    assert (
        binding_a["linear_diagnostics_status"]
        == SupportAggregateStatus.BLOCK_SUPPORT_EVIDENCE.value
    )
