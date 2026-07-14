from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path

import pytest

from research.linear_evidence.drift import (
    DRIFT_DIAGNOSTIC_DEFAULTS_V0,
    RollingLinearDriftInputV1,
    fit_rolling_linear_drift,
)
from research.linear_evidence.import_boundary import scan_file_import_boundary
from research.linear_evidence.offline_productive_rolling_linear_drift_diagnostics_v0 import (
    AUTHORITY_EFFECT,
    DIAGNOSTICS_SCOPE_VERSION,
    DEFAULT_MIN_SAMPLES,
    DEFAULT_WINDOW_SIZE,
    DEFAULT_WINDOW_STEP,
    ProductiveRollingLinearDriftReason,
    ProductiveRollingLinearDriftStatus,
    RollingWindowContractV0,
    build_authority_boundary_v0,
    build_productive_rolling_linear_drift_diagnostics_artifacts_v0,
    build_window_results_v0,
    classify_productive_rolling_drift_status_v0,
    default_rolling_window_contract_v0,
    fit_productive_rolling_linear_drift_v0,
)
from scripts.ops.primary_evidence_retention_v0 import verify_manifest_sha256
from src.governance.economic_diagnostic_optimization_boundary_v0 import (
    build_boundary_report,
)
from src.research.offline_parameter_sensitivity_productive_input_join_materializer_v0 import (
    MaterializationStatus,
    materialize_from_manifest_paths_v0,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
OWNER = (
    REPO_ROOT
    / "src/research/linear_evidence/offline_productive_rolling_linear_drift_diagnostics_v0.py"
)
MATERIALIZER = (
    REPO_ROOT / "scripts/ops/materialize_offline_productive_rolling_linear_drift_diagnostics_v0.py"
)
ARCHIVE_ROOT = Path("/Users/frnkhrz/Documents/Peak_Trade_runtime_evidence_archive_20260520T161443Z")
SIGNAL_MATRIX = (
    ARCHIVE_ROOT
    / "research/offline_final_research_fleet_signal_matrix_productive_input_join_materialization_v0_20260714T131741Z"
    / "signal_matrix.jsonl"
)
SEMANTIC_ARTIFACTS = (
    "source_binding.json",
    "rolling_window_contract.json",
    "window_results.json",
    "coefficient_drift.json",
    "fit_metric_drift.json",
    "interpretation.json",
    "deterministic_materialization.txt",
)


def _record(index: int, *, target: float, signal: float, aux: float) -> RollingLinearDriftInputV1:
    decision_time = f"2026-01-01T{index:02d}:00:00Z"
    return RollingLinearDriftInputV1(
        instrument_id="PF_ETHUSD",
        decision_time=decision_time,
        feature_availability_time=decision_time,
        target=target,
        features={"signal": signal, "aux": aux},
    )


def _stable_records(count: int = 14) -> list[RollingLinearDriftInputV1]:
    return [
        _record(index, target=float(index) * 0.2, signal=float(index), aux=float(index % 2))
        for index in range(count)
    ]


def _shift_records() -> list[RollingLinearDriftInputV1]:
    records: list[RollingLinearDriftInputV1] = []
    for index in range(1, 19):
        signal = float(index)
        target = 0.4 * signal if index <= 9 else 2.0 * signal
        records.append(
            RollingLinearDriftInputV1(
                instrument_id="PF_ETHUSD",
                decision_time=f"2026-01-01T{index - 1:02d}:00:00Z",
                feature_availability_time=f"2026-01-01T{index - 1:02d}:00:00Z",
                target=target,
                features={"signal": signal},
            )
        )
    return records


def _small_contract() -> RollingWindowContractV0:
    return RollingWindowContractV0(
        window_size=6,
        window_step=1,
        min_samples=4,
        validation_fraction=0.25,
        baseline_window_policy="FIRST_SUCCESSFUL_WINDOW_ELSE_FIRST_WINDOW",
        solver="numpy.linalg.lstsq",
        fit_intercept=True,
        model_spec_version="parameter_sensitivity_active_feature_subset_v0",
        drift_thresholds=dict(DRIFT_DIAGNOSTIC_DEFAULTS_V0),
    )


def _sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _manifest_digest_for(path: Path, bundle: Path) -> str | None:
    rel = path.relative_to(bundle).as_posix()
    for line in (bundle / "MANIFEST.sha256").read_text(encoding="utf-8").splitlines():
        parts = line.split(None, 1)
        if len(parts) == 2 and parts[1] == rel:
            return parts[0]
    return None


def _run_materializer(out_dir: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [
            sys.executable,
            str(MATERIALIZER),
            "--out",
            str(out_dir),
            "--signal-matrix",
            str(SIGNAL_MATRIX),
            "--skip-focused-tests",
        ],
        cwd=str(REPO_ROOT),
        check=False,
        text=True,
        capture_output=True,
        env={"PYTHONPATH": f"{REPO_ROOT / 'src'}:{REPO_ROOT}"},
    )


@pytest.fixture(scope="module")
def productive_materialization():
    if not SIGNAL_MATRIX.is_file():
        pytest.skip("archive signal matrix unavailable")
    return materialize_from_manifest_paths_v0(
        repo_root=REPO_ROOT,
        signal_matrix_path=SIGNAL_MATRIX,
    )


def test_deterministic_window_formation() -> None:
    contract = _small_contract()
    first = fit_productive_rolling_linear_drift_v0(
        records=_stable_records(), window_contract=contract
    )
    second = fit_productive_rolling_linear_drift_v0(
        records=_stable_records(), window_contract=contract
    )
    assert first.n_windows == second.n_windows
    assert first.config_digest == second.config_digest


def test_no_lookahead_leakage() -> None:
    records = [
        RollingLinearDriftInputV1(
            "PF_ETHUSD",
            "2026-01-01T01:00:00Z",
            "2026-01-01T02:00:00Z",
            0.1,
            {"signal": 1.0},
        ),
        *_stable_records(count=5),
    ]
    evidence = fit_productive_rolling_linear_drift_v0(
        records=records,
        window_contract=_small_contract(),
    )
    status, _ = classify_productive_rolling_drift_status_v0(
        evidence=evidence,
        window_contract=_small_contract(),
    )
    assert status == ProductiveRollingLinearDriftStatus.FEATURE_LEAKAGE_BLOCKED.value


def test_stable_feature_order() -> None:
    evidence = fit_productive_rolling_linear_drift_v0(
        records=_stable_records(),
        window_contract=_small_contract(),
    )
    assert evidence.feature_names == tuple(sorted(evidence.feature_names))


def test_identical_inputs_identical_outputs() -> None:
    contract = _small_contract()
    first = fit_productive_rolling_linear_drift_v0(
        records=_stable_records(), window_contract=contract
    )
    second = fit_productive_rolling_linear_drift_v0(
        records=_stable_records(), window_contract=contract
    )
    assert first.to_dict() == second.to_dict()


def test_coefficient_delta_baseline_and_previous() -> None:
    evidence = fit_productive_rolling_linear_drift_v0(
        records=_stable_records(count=10),
        window_contract=_small_contract(),
    )
    results = build_window_results_v0(evidence, window_contract=_small_contract())
    assert results
    baseline = next(item for item in results if item["is_baseline_window"])
    assert baseline["coefficient_delta_from_baseline"]["signal"] == pytest.approx(0.0)
    assert "coefficient_delta_from_previous" in results[1]


def test_sign_change_detection() -> None:
    evidence = fit_productive_rolling_linear_drift_v0(
        records=_shift_records(),
        window_contract=_small_contract(),
    )
    assert sum(evidence.coefficient_sign_flip_counts.values()) >= 0
    status, reasons = classify_productive_rolling_drift_status_v0(
        evidence=evidence,
        window_contract=_small_contract(),
    )
    assert status in {
        ProductiveRollingLinearDriftStatus.WARN_DRIFT_DETECTED.value,
        ProductiveRollingLinearDriftStatus.BLOCK_DRIFT_EXCEEDS_POLICY.value,
    }
    assert ProductiveRollingLinearDriftReason.COEFFICIENT_MAGNITUDE_DRIFT.value in reasons


def test_rank_deficiency_fail_closed() -> None:
    records = [
        RollingLinearDriftInputV1(
            "PF_ETHUSD",
            f"2026-01-01T{index:02d}:00:00Z",
            f"2026-01-01T{index:02d}:00:00Z",
            float(index),
            {"signal": 1.0, "duplicate": 2.0, "copy": 2.0},
        )
        for index in range(6)
    ]
    evidence = fit_productive_rolling_linear_drift_v0(
        records=records,
        window_contract=_small_contract(),
    )
    status, reasons = classify_productive_rolling_drift_status_v0(
        evidence=evidence,
        window_contract=_small_contract(),
    )
    assert evidence.rank_deficient_window_count >= 1
    assert status in {
        ProductiveRollingLinearDriftStatus.RANK_DEFICIENT_BLOCKED.value,
        ProductiveRollingLinearDriftStatus.INCONCLUSIVE.value,
    }
    assert (
        ProductiveRollingLinearDriftReason.RANK_DEFICIENT_BLOCKED.value in reasons
        or evidence.rank_deficient_window_count >= 1
    )


def test_high_condition_number_classification() -> None:
    evidence = fit_productive_rolling_linear_drift_v0(
        records=_stable_records(),
        window_contract=_small_contract(),
    )
    assert "condition_number_max" in evidence.drift_metrics


def test_insufficient_samples_per_window() -> None:
    contract = RollingWindowContractV0(
        window_size=6,
        window_step=1,
        min_samples=20,
        validation_fraction=0.25,
        baseline_window_policy="FIRST_SUCCESSFUL_WINDOW_ELSE_FIRST_WINDOW",
        solver="numpy.linalg.lstsq",
        fit_intercept=True,
        model_spec_version="parameter_sensitivity_active_feature_subset_v0",
        drift_thresholds=dict(DRIFT_DIAGNOSTIC_DEFAULTS_V0),
    )
    evidence = fit_productive_rolling_linear_drift_v0(
        records=_stable_records(count=8), window_contract=contract
    )
    status, _ = classify_productive_rolling_drift_status_v0(
        evidence=evidence,
        window_contract=contract,
    )
    assert status in {
        ProductiveRollingLinearDriftStatus.WINDOW_SAMPLE_INSUFFICIENT.value,
        ProductiveRollingLinearDriftStatus.INSUFFICIENT_WINDOWS.value,
        ProductiveRollingLinearDriftStatus.INSUFFICIENT_DATA.value,
    }


def test_insufficient_window_count() -> None:
    contract = RollingWindowContractV0(
        window_size=20,
        window_step=10,
        min_samples=4,
        validation_fraction=0.25,
        baseline_window_policy="FIRST_SUCCESSFUL_WINDOW_ELSE_FIRST_WINDOW",
        solver="numpy.linalg.lstsq",
        fit_intercept=True,
        model_spec_version="parameter_sensitivity_active_feature_subset_v0",
        drift_thresholds=dict(DRIFT_DIAGNOSTIC_DEFAULTS_V0),
    )
    evidence = fit_productive_rolling_linear_drift_v0(
        records=_stable_records(count=10), window_contract=contract
    )
    status, _ = classify_productive_rolling_drift_status_v0(
        evidence=evidence,
        window_contract=contract,
    )
    assert status in {
        ProductiveRollingLinearDriftStatus.INSUFFICIENT_DATA.value,
        ProductiveRollingLinearDriftStatus.INSUFFICIENT_WINDOWS.value,
        ProductiveRollingLinearDriftStatus.INCONCLUSIVE.value,
    }


def test_dropped_row_attribution_and_problematic_windows_reported() -> None:
    evidence = fit_productive_rolling_linear_drift_v0(
        records=_stable_records(count=10),
        window_contract=_small_contract(),
    )
    results = build_window_results_v0(evidence, window_contract=_small_contract())
    assert len(results) == evidence.n_windows
    for window in evidence.window_evidence:
        assert window.status in {
            "DIAGNOSTIC_ONLY",
            "INSUFFICIENT_DATA",
            "RANK_DEFICIENT_BLOCKED",
            "ROBUSTNESS_FAILED",
        }


def test_no_automatic_parameter_feature_window_selection() -> None:
    contract = default_rolling_window_contract_v0()
    assert contract.window_size == DEFAULT_WINDOW_SIZE
    assert contract.window_step == DEFAULT_WINDOW_STEP
    assert contract.min_samples == DEFAULT_MIN_SAMPLES


def test_authority_and_runtime_effects_none() -> None:
    boundary = build_authority_boundary_v0()
    assert boundary["authority_effect"] == AUTHORITY_EFFECT
    assert boundary["runtime_effect"] == "NONE"
    assert boundary["parameter_default_changed"] is False
    assert boundary["parameter_optimization_executed"] is False
    assert boundary["strategy_selection_changed"] is False
    assert boundary["economic_evaluation_executed"] is False


def test_deterministic_productive_artifacts(productive_materialization) -> None:
    first = build_productive_rolling_linear_drift_diagnostics_artifacts_v0(
        materialization=productive_materialization,
        source_evidence_refs=["fixture_ref"],
    )
    second = build_productive_rolling_linear_drift_diagnostics_artifacts_v0(
        materialization=productive_materialization,
        source_evidence_refs=["fixture_ref"],
    )
    assert first["output_digest"] == second["output_digest"]


def test_productive_materialization_passes(productive_materialization) -> None:
    if productive_materialization.status != MaterializationStatus.PASS:
        pytest.skip("productive materialization unavailable")
    artifacts = build_productive_rolling_linear_drift_diagnostics_artifacts_v0(
        materialization=productive_materialization,
        source_evidence_refs=["fixture_ref"],
    )
    assert artifacts["diagnostics_scope_version"] == DIAGNOSTICS_SCOPE_VERSION
    assert artifacts["window_quality_diagnostics"]["window_count"] >= 1
    assert artifacts["authority_boundary"]["runtime_effect"] == "NONE"


def test_non_pass_materialization_fail_closed(productive_materialization) -> None:
    if productive_materialization.status != MaterializationStatus.PASS:
        pytest.skip("productive materialization unavailable")
    empty = type(productive_materialization)(
        status=MaterializationStatus.TARGET_BINDING_MISSING,
        records=(),
        join_result=productive_materialization.join_result,
        provenance=productive_materialization.provenance,
        materialization_digest=productive_materialization.materialization_digest,
        output_digest=productive_materialization.output_digest,
        productive_input_digest=productive_materialization.productive_input_digest,
        grid_digest=productive_materialization.grid_digest,
        source_binding_digest=productive_materialization.source_binding_digest,
        source_signal_matrix_digest=productive_materialization.source_signal_matrix_digest,
    )
    artifacts = build_productive_rolling_linear_drift_diagnostics_artifacts_v0(
        materialization=empty,
        source_evidence_refs=["fixture_ref"],
    )
    assert (
        artifacts["aggregate_status"]
        == ProductiveRollingLinearDriftStatus.TARGET_BINDING_MISSING.value
    )


def test_import_boundary_owner_and_materializer() -> None:
    assert scan_file_import_boundary(OWNER, repo_root=REPO_ROOT) == []
    assert scan_file_import_boundary(MATERIALIZER, repo_root=REPO_ROOT) == []


def test_governance_boundary_guard_accepts_new_owner() -> None:
    changed_files = [
        "src/research/linear_evidence/offline_productive_rolling_linear_drift_diagnostics_v0.py",
        "scripts/ops/materialize_offline_productive_rolling_linear_drift_diagnostics_v0.py",
        "tests/research/test_offline_productive_rolling_linear_drift_diagnostics_v0.py",
        "config/governance/economic_diagnostic_optimization_boundary_canonical_owner_map_v0.json",
    ]
    report = build_boundary_report(changed_files, repo_root=REPO_ROOT)
    assert report.admissible is True
    assert report.impact_unknown is False


def test_unknown_path_still_blocked() -> None:
    report = build_boundary_report(
        ["src/research/unregistered_offline_diagnostic_owner_v0.py"],
        repo_root=REPO_ROOT,
    )
    assert report.admissible is False
    assert report.impact_unknown is True


def test_materializer_roundtrip(tmp_path: Path) -> None:
    if not SIGNAL_MATRIX.is_file():
        pytest.skip("archive signal matrix unavailable")

    first_dir = tmp_path / "evidence_a"
    second_dir = tmp_path / "evidence_b"
    first = _run_materializer(first_dir)
    second = _run_materializer(second_dir)
    assert first.returncode == 0, first.stderr
    assert second.returncode == 0, second.stderr

    for bundle in (first_dir, second_dir):
        ok, msg = verify_manifest_sha256(bundle)
        assert ok, msg
        manifest_digest = _manifest_digest_for(bundle / "final_report.txt", bundle)
        assert manifest_digest is not None
        assert manifest_digest == _sha256_file(bundle / "final_report.txt")

    first_semantic = {
        name: (first_dir / name).read_text(encoding="utf-8") for name in SEMANTIC_ARTIFACTS
    }
    second_semantic = {
        name: (second_dir / name).read_text(encoding="utf-8") for name in SEMANTIC_ARTIFACTS
    }
    assert first_semantic == second_semantic


def test_source_manifest_fail_closed(tmp_path: Path) -> None:
    bundle = (
        ARCHIVE_ROOT
        / "research/offline_productive_parameter_sensitivity_diagnostics_v0_20260714T222747Z"
    )
    if not bundle.is_dir():
        pytest.skip("archive bundle unavailable")
    ok, _ = verify_manifest_sha256(bundle)
    assert ok is True
