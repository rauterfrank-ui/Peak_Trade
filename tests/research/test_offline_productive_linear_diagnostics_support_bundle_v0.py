from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

from research.linear_evidence.import_boundary import scan_file_import_boundary
from research.linear_evidence.offline_productive_linear_diagnostics_support_bundle_v0 import (
    AUTHORITY_EFFECT,
    DEFAULT_COST_DIAGNOSTICS_BUNDLE,
    DEFAULT_FACTOR_EXPOSURE_BUNDLE,
    DEFAULT_PARAMETER_SENSITIVITY_BUNDLE,
    DEFAULT_ROLLING_LINEAR_DRIFT_BUNDLE,
    DEFAULT_SIGNAL_ORTHOGONALITY_BUNDLE,
    DEFAULT_SOURCE_BUNDLE_SPECS,
    DIAGNOSTIC_CLASS_ORDER,
    EVIDENCE_TYPE,
    SCHEMA_VERSION,
    EconomicViabilitySupportStatus,
    SourceBundleSpecV0,
    SupportAggregateStatus,
    SupportBundleValidationError,
    bind_source_diagnostic_v0,
    build_authority_boundary_v0,
    build_productive_linear_diagnostics_support_bundle_artifacts_v0,
    classify_support_aggregate_status,
    validate_support_bundle_artifacts_v0,
    verify_bundle_manifest,
)
from scripts.ops.primary_evidence_retention_v0 import verify_manifest_sha256
from src.governance.economic_diagnostic_optimization_boundary_v0 import build_boundary_report

REPO_ROOT = Path(__file__).resolve().parents[2]
OWNER = REPO_ROOT / (
    "src/research/linear_evidence/offline_productive_linear_diagnostics_support_bundle_v0.py"
)
MATERIALIZER = (
    REPO_ROOT / "scripts/ops/materialize_offline_productive_linear_diagnostics_support_bundle_v0.py"
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
def productive_artifacts():
    if not _archive_available():
        pytest.skip("productive archive bundles unavailable")
    artifacts = build_productive_linear_diagnostics_support_bundle_artifacts_v0(
        source_specs=DEFAULT_SOURCE_BUNDLE_SPECS,
        verify_fn=verify_manifest_sha256,
        repo_root=REPO_ROOT,
    )
    validate_support_bundle_artifacts_v0(artifacts)
    return artifacts


def test_all_five_source_classes_canonically_bound(productive_artifacts) -> None:
    assert productive_artifacts["diagnostic_class_present_count"] == 5
    assert productive_artifacts["diagnostic_class_count"] == 5
    ref_fields = {
        "cost_diagnostics": "cost_diagnostics_ref",
        "signal_orthogonality": "signal_orthogonality_ref",
        "factor_exposure": "factor_exposure_ref",
        "parameter_sensitivity": "parameter_sensitivity_ref",
        "rolling_linear_drift": "rolling_linear_drift_ref",
    }
    for diagnostic_class in DIAGNOSTIC_CLASS_ORDER:
        assert diagnostic_class in productive_artifacts["source_statuses"]
        assert diagnostic_class in productive_artifacts["source_reason_codes"]
        assert productive_artifacts["source_manifest_digests"][diagnostic_class]
        assert productive_artifacts[ref_fields[diagnostic_class]]


def test_productive_bundle_refs_present(productive_artifacts) -> None:
    assert productive_artifacts["cost_diagnostics_ref"] == str(DEFAULT_COST_DIAGNOSTICS_BUNDLE)
    assert productive_artifacts["signal_orthogonality_ref"] == str(
        DEFAULT_SIGNAL_ORTHOGONALITY_BUNDLE
    )
    assert productive_artifacts["factor_exposure_ref"] == str(DEFAULT_FACTOR_EXPOSURE_BUNDLE)
    assert productive_artifacts["parameter_sensitivity_ref"] == str(
        DEFAULT_PARAMETER_SENSITIVITY_BUNDLE
    )
    assert productive_artifacts["rolling_linear_drift_ref"] == str(
        DEFAULT_ROLLING_LINEAR_DRIFT_BUNDLE
    )


def test_source_manifests_verified_before_materialization() -> None:
    if not _archive_available():
        pytest.skip("productive archive bundles unavailable")
    for bundle in PRODUCTIVE_BUNDLES.values():
        assert verify_bundle_manifest(bundle, verify_fn=verify_manifest_sha256) == 0


def test_missing_source_evidence_fail_closed(tmp_path: Path) -> None:
    missing_spec = SourceBundleSpecV0(
        diagnostic_class="cost_diagnostics",
        evidence_type="offline_linear_cost_model_diagnostics.v0",
        bundle_path=tmp_path / "missing_bundle",
        status_artifact="reason_codes.json",
    )
    with pytest.raises(SupportBundleValidationError, match="SOURCE_BUNDLE_MISSING"):
        bind_source_diagnostic_v0(missing_spec, verify_fn=verify_manifest_sha256)


def test_manifest_error_fail_closed(tmp_path: Path) -> None:
    bundle = tmp_path / "bad_bundle"
    bundle.mkdir()
    (bundle / "MANIFEST.sha256").write_text("deadbeef  missing.txt\n", encoding="utf-8")
    spec = SourceBundleSpecV0(
        diagnostic_class="cost_diagnostics",
        evidence_type="offline_linear_cost_model_diagnostics.v0",
        bundle_path=bundle,
        status_artifact="reason_codes.json",
    )

    def _fail_verify(_: Path) -> tuple[bool, str]:
        return False, "MANIFEST_MISMATCH"

    with pytest.raises(SupportBundleValidationError, match="SOURCE_MANIFEST_VERIFY_FAILED"):
        bind_source_diagnostic_v0(spec, verify_fn=_fail_verify)


def test_source_status_and_reason_codes_preserved(productive_artifacts) -> None:
    assert productive_artifacts["source_statuses"]["cost_diagnostics"] == "RANK_DEFICIENT_BLOCKED"
    assert (
        "RANK_DEFICIENT_FEATURE_MATRIX"
        in productive_artifacts["source_reason_codes"]["cost_diagnostics"]
    )
    assert productive_artifacts["source_statuses"]["signal_orthogonality"] == "OK"
    assert productive_artifacts["source_statuses"]["factor_exposure"] == "RANK_DEFICIENT_BLOCKED"
    assert (
        productive_artifacts["source_statuses"]["parameter_sensitivity"] == "ROBUST_REGION_OBSERVED"
    )
    assert (
        productive_artifacts["source_statuses"]["rolling_linear_drift"]
        == "BLOCK_DRIFT_EXCEEDS_POLICY"
    )
    assert (
        "COEFFICIENT_MAGNITUDE_DRIFT"
        in productive_artifacts["source_reason_codes"]["rolling_linear_drift"]
    )


def test_blocking_rolling_drift_remains_blockering_in_aggregate(productive_artifacts) -> None:
    assert (
        productive_artifacts["aggregate_status"]
        == SupportAggregateStatus.BLOCK_SUPPORT_EVIDENCE.value
    )
    assert any(
        code.startswith("BLOCKED_SOURCE:rolling_linear_drift:")
        for code in productive_artifacts["aggregate_reason_codes"]
    )
    assert (
        productive_artifacts["economic_viability_support_status"]
        == EconomicViabilitySupportStatus.BLOCKED_SOURCE_DIAGNOSTICS_PRESENT.value
    )


def test_aggregate_semantics_deterministic(productive_artifacts) -> None:
    second = build_productive_linear_diagnostics_support_bundle_artifacts_v0(
        source_specs=DEFAULT_SOURCE_BUNDLE_SPECS,
        verify_fn=verify_manifest_sha256,
        repo_root=REPO_ROOT,
    )
    assert second["aggregate_status"] == productive_artifacts["aggregate_status"]
    assert second["aggregate_reason_codes"] == productive_artifacts["aggregate_reason_codes"]


def test_stable_sorting_and_serialization(productive_artifacts) -> None:
    serialized = json.dumps(productive_artifacts, sort_keys=True, separators=(",", ":"))
    roundtrip = json.loads(serialized)
    assert roundtrip["source_evidence_refs"] == productive_artifacts["source_evidence_refs"]
    assert roundtrip["aggregate_reason_codes"] == productive_artifacts["aggregate_reason_codes"]


def test_materializer_to_validator_roundtrip(productive_artifacts) -> None:
    validate_support_bundle_artifacts_v0(productive_artifacts)


def test_repeated_materialization_byte_identical(productive_artifacts) -> None:
    second = build_productive_linear_diagnostics_support_bundle_artifacts_v0(
        source_specs=DEFAULT_SOURCE_BUNDLE_SPECS,
        verify_fn=verify_manifest_sha256,
        repo_root=REPO_ROOT,
    )
    assert second["output_digest"] == productive_artifacts["output_digest"]


def test_no_economic_evaluation_or_authority(productive_artifacts) -> None:
    boundary = productive_artifacts["authority_boundary"]
    assert boundary["economic_evaluation_executed"] is False
    assert boundary["economic_validity_pass_created"] is False
    assert boundary["promotion_pass_created"] is False
    assert boundary["parameter_optimization_executed"] is False
    assert boundary["parameter_default_changed"] is False
    assert boundary["strategy_selection_changed"] is False
    assert productive_artifacts["economic_pass_authority"] is False
    assert productive_artifacts["promotion_pass_authority"] is False
    assert productive_artifacts["strategy_selection_authority"] is False


def test_runtime_and_authority_effects_none() -> None:
    boundary = build_authority_boundary_v0()
    assert boundary["runtime_effect"] == AUTHORITY_EFFECT == "NONE"
    assert boundary["authority_effect"] == "NONE"


def test_import_boundary_owner_and_materializer() -> None:
    assert scan_file_import_boundary(OWNER, repo_root=REPO_ROOT) == []
    assert scan_file_import_boundary(MATERIALIZER, repo_root=REPO_ROOT) == []


def test_governance_boundary_guard_accepts_new_owner() -> None:
    changed_files = [
        "src/research/linear_evidence/offline_productive_linear_diagnostics_support_bundle_v0.py",
        "scripts/ops/materialize_offline_productive_linear_diagnostics_support_bundle_v0.py",
        "tests/research/test_offline_productive_linear_diagnostics_support_bundle_v0.py",
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


def test_contract_metadata_bound(productive_artifacts) -> None:
    assert productive_artifacts["schema_version"] == SCHEMA_VERSION
    assert productive_artifacts["evidence_type"] == EVIDENCE_TYPE
    assert productive_artifacts["runtime_effect"] == "NONE"
    assert productive_artifacts["authority_effect"] == "NONE"


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

    digest_a = (first_dir / "deterministic_materialization.txt").read_text(encoding="utf-8")
    digest_b = (second_dir / "deterministic_materialization.txt").read_text(encoding="utf-8")
    assert "SECOND_MATERIALIZATION_DIFF_EMPTY=True" in digest_a
    assert digest_a == digest_b

    payload_a = json.loads(
        (first_dir / "linear_diagnostics_support_bundle.json").read_text(encoding="utf-8")
    )
    payload_b = json.loads(
        (second_dir / "linear_diagnostics_support_bundle.json").read_text(encoding="utf-8")
    )
    assert payload_a["output_digest"] == payload_b["output_digest"]
    assert payload_a["aggregate_status"] == SupportAggregateStatus.BLOCK_SUPPORT_EVIDENCE.value


def test_insufficient_binding_aggregate_fail_closed() -> None:
    aggregate_status, reason_codes = classify_support_aggregate_status([])
    assert (
        aggregate_status == SupportAggregateStatus.INSUFFICIENT_OR_UNVERIFIED_SOURCE_EVIDENCE.value
    )
    assert "NO_SOURCE_BINDINGS" in reason_codes
