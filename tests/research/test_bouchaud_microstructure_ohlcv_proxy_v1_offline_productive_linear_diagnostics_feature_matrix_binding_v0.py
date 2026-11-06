"""Contract tests for Bouchaud OHLCV proxy v1 offline productive linear diagnostics feature matrix binding v0."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pandas as pd
import pytest

from research.linear_evidence.import_boundary import scan_file_import_boundary
from research.linear_evidence.offline_productive_linear_diagnostics_support_bundle_v0 import (
    DEFAULT_COST_DIAGNOSTICS_BUNDLE,
    DEFAULT_FACTOR_EXPOSURE_BUNDLE,
    DEFAULT_PARAMETER_SENSITIVITY_BUNDLE,
    DEFAULT_ROLLING_LINEAR_DRIFT_BUNDLE,
    DEFAULT_SIGNAL_ORTHOGONALITY_BUNDLE,
    DEFAULT_SOURCE_BUNDLE_SPECS,
    DIAGNOSTIC_CLASS_ORDER,
)
from scripts.ops.primary_evidence_retention_v0 import verify_manifest_sha256
from src.research.bouchaud_microstructure_ohlcv_proxy_v1_offline_productive_linear_diagnostics_feature_matrix_binding_v0 import (
    BINDING_ID,
    BINDING_OWNER,
    CANONICAL_OWNER,
    EVIDENCE_TYPE,
    FEATURE_MATRIX_OWNER,
    FeatureMatrixBindingStatus,
    FeatureMatrixBindingValidationError,
    bind_bouchaud_feature_matrix_to_linear_diagnostics_v0,
    materialize_bouchaud_feature_matrix_linear_diagnostics_binding_v0,
)
from src.research.bouchaud_microstructure_ohlcv_proxy_v1_research_generation_preparation_v0 import (
    FEATURE_NAMES,
    TARGET_NAME,
    build_target_binding,
    load_fixture_bars_v0,
    materialize_and_validate_feature_matrix_v0,
    validate_no_lookahead_contract_v0,
)
from src.research.linear_evidence.offline_productive_linear_diagnostics_support_bundle_v0 import (
    build_productive_linear_diagnostics_support_bundle_artifacts_v0,
)
from src.governance.economic_diagnostic_optimization_boundary_v0 import build_boundary_report

REPO_ROOT = Path(__file__).resolve().parents[2]
OWNER = REPO_ROOT / (
    "src/research/"
    "bouchaud_microstructure_ohlcv_proxy_v1_offline_productive_linear_diagnostics_"
    "feature_matrix_binding_v0.py"
)
MATERIALIZER = REPO_ROOT / (
    "scripts/ops/"
    "materialize_bouchaud_microstructure_ohlcv_proxy_v1_offline_productive_linear_diagnostics_"
    "feature_matrix_binding_v0.py"
)
FIXTURE_PATH = (
    REPO_ROOT
    / "tests/fixtures/bouchaud_microstructure_ohlcv_proxy_v1_research_generation_preparation_v0/"
    "truth_pack_bars.json"
)

PRODUCTIVE_BUNDLES = {
    "cost_diagnostics": DEFAULT_COST_DIAGNOSTICS_BUNDLE,
    "signal_orthogonality": DEFAULT_SIGNAL_ORTHOGONALITY_BUNDLE,
    "factor_exposure": DEFAULT_FACTOR_EXPOSURE_BUNDLE,
    "parameter_sensitivity": DEFAULT_PARAMETER_SENSITIVITY_BUNDLE,
    "rolling_linear_drift": DEFAULT_ROLLING_LINEAR_DRIFT_BUNDLE,
}

FORBIDDEN_RUNTIME_IMPORT_PREFIXES = (
    "src.execution",
    "src.scheduler",
    "src.broker",
    "src.orders",
)


def _archive_available() -> bool:
    return all(path.is_dir() for path in PRODUCTIVE_BUNDLES.values())


def _fixture_rows_and_binding():
    payload = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))
    bars = pd.DataFrame(payload["bars"])
    rows, binding, digest = materialize_and_validate_feature_matrix_v0(bars)
    assert digest == payload["expected_feature_digest"]
    return rows, binding, digest


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
def fixture_binding():
    return _fixture_rows_and_binding()


@pytest.fixture(scope="module")
def productive_support_bundle():
    if not _archive_available():
        pytest.skip("productive archive bundles unavailable")
    return build_productive_linear_diagnostics_support_bundle_artifacts_v0(
        source_specs=DEFAULT_SOURCE_BUNDLE_SPECS,
        verify_fn=verify_manifest_sha256,
        repo_root=REPO_ROOT,
    )


@pytest.fixture(scope="module")
def bound_artifacts(fixture_binding, productive_support_bundle):
    rows, binding, digest = fixture_binding
    payload, result = materialize_bouchaud_feature_matrix_linear_diagnostics_binding_v0(
        rows=rows,
        binding=binding,
        feature_digest=digest,
        source_specs=DEFAULT_SOURCE_BUNDLE_SPECS,
        verify_fn=verify_manifest_sha256,
        repo_root=REPO_ROOT,
    )
    return payload, result


def test_fixture_feature_digest_deterministic(fixture_binding) -> None:
    _, binding, digest = fixture_binding
    assert binding.feature_names == FEATURE_NAMES
    assert binding.target_name == TARGET_NAME
    assert binding.feature_matrix_digest == digest
    assert len(digest) == 64


def test_feature_matrix_binding_contract_preserved(bound_artifacts, fixture_binding) -> None:
    payload, result = bound_artifacts
    _, binding, digest = fixture_binding
    assert payload["feature_digest"] == digest
    assert payload["feature_matrix_binding"]["feature_matrix_digest"] == digest
    assert result.feature_digest_identity_preserved is True
    assert result.feature_matrix_owner == FEATURE_MATRIX_OWNER


def test_all_five_diagnostic_classes_consume_matrix(bound_artifacts) -> None:
    _, result = bound_artifacts
    assert len(result.diagnostic_consumption_bindings) == 5
    classes = {item.diagnostic_class for item in result.diagnostic_consumption_bindings}
    assert classes == set(DIAGNOSTIC_CLASS_ORDER)
    for item in result.diagnostic_consumption_bindings:
        assert item.consumption_status == FeatureMatrixBindingStatus.BOUND.value
        assert item.canonical_feature_digest == result.feature_digest
        assert item.feature_digest_preserved is True


def test_support_bundle_chain_bound(bound_artifacts, productive_support_bundle) -> None:
    payload, result = bound_artifacts
    assert result.linear_diagnostics_chain_bound is True
    assert payload["support_bundle_output_digest"] == productive_support_bundle["output_digest"]
    assert (
        payload["support_bundle_aggregate_status"] == productive_support_bundle["aggregate_status"]
    )


def test_binding_status_bound(bound_artifacts) -> None:
    _, result = bound_artifacts
    assert result.binding_status == FeatureMatrixBindingStatus.BOUND.value
    assert result.economic_evaluation_executed is False
    assert result.runtime_effect == "NONE"
    assert result.authority_effect == "NONE"


def test_missing_target_binding_fail_closed(fixture_binding, productive_support_bundle) -> None:
    rows, binding, digest = fixture_binding
    bad_target = dict(build_target_binding())
    bad_target["target_name"] = "wrong_target"
    with pytest.raises(FeatureMatrixBindingValidationError, match="TARGET_BINDING_NAME_MISMATCH"):
        bind_bouchaud_feature_matrix_to_linear_diagnostics_v0(
            rows=rows,
            binding=binding,
            feature_digest=digest,
            support_bundle=productive_support_bundle,
            target_binding=bad_target,
        )


def test_feature_digest_mismatch_fail_closed(fixture_binding, productive_support_bundle) -> None:
    rows, binding, digest = fixture_binding
    with pytest.raises(
        FeatureMatrixBindingValidationError, match="FEATURE_DIGEST_IDENTITY_MISMATCH"
    ):
        bind_bouchaud_feature_matrix_to_linear_diagnostics_v0(
            rows=rows,
            binding=binding,
            feature_digest="0" * 64,
            support_bundle=productive_support_bundle,
        )


def test_materialization_deterministic(fixture_binding) -> None:
    if not _archive_available():
        pytest.skip("productive archive bundles unavailable")
    rows, binding, digest = fixture_binding
    first, _ = materialize_bouchaud_feature_matrix_linear_diagnostics_binding_v0(
        rows=rows,
        binding=binding,
        feature_digest=digest,
        source_specs=DEFAULT_SOURCE_BUNDLE_SPECS,
        verify_fn=verify_manifest_sha256,
        repo_root=REPO_ROOT,
    )
    second, _ = materialize_bouchaud_feature_matrix_linear_diagnostics_binding_v0(
        rows=rows,
        binding=binding,
        feature_digest=digest,
        source_specs=DEFAULT_SOURCE_BUNDLE_SPECS,
        verify_fn=verify_manifest_sha256,
        repo_root=REPO_ROOT,
    )
    assert first["output_digest"] == second["output_digest"]


def test_no_runtime_import_boundary_violation() -> None:
    assert scan_file_import_boundary(OWNER, repo_root=REPO_ROOT) == []
    assert scan_file_import_boundary(MATERIALIZER, repo_root=REPO_ROOT) == []
    source = OWNER.read_text(encoding="utf-8")
    for prefix in FORBIDDEN_RUNTIME_IMPORT_PREFIXES:
        assert prefix not in source


def test_governance_boundary_admissible() -> None:
    report = build_boundary_report(
        [
            str(OWNER.relative_to(REPO_ROOT)),
            str(MATERIALIZER.relative_to(REPO_ROOT)),
            str(Path(__file__).relative_to(REPO_ROOT)),
            "config/governance/economic_diagnostic_optimization_boundary_canonical_owner_map_v0.json",
        ],
        repo_root=REPO_ROOT,
    )
    assert report.admissible is True
    assert report.impact_unknown is False


def test_materializer_roundtrip_manifest_verified(tmp_path) -> None:
    if not _archive_available():
        pytest.skip("productive archive bundles unavailable")
    out_dir = tmp_path / "binding_bundle"
    proc = _run_materializer(out_dir)
    assert proc.returncode == 0, proc.stdout + proc.stderr
    ok, _ = verify_manifest_sha256(out_dir)
    assert ok
    contract = json.loads((out_dir / "binding_contract.json").read_text(encoding="utf-8"))
    assert contract["binding_id"] == BINDING_ID
    assert contract["evidence_type"] == EVIDENCE_TYPE
    assert contract["owner"] == BINDING_OWNER
    final_report = (out_dir / "final_report.txt").read_text(encoding="utf-8")
    assert "MANIFEST_VERIFY_RC=0" in final_report
    assert "ALL_GREEN=True" in final_report
