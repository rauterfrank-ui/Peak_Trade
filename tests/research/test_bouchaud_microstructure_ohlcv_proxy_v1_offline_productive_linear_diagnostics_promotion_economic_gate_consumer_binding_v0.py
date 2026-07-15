"""Contract tests for Bouchaud OHLCV proxy v1 promotion economic gate consumer binding v0."""

from __future__ import annotations

import importlib.util
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
    LinearDiagnosticsConsumerBindingError,
    bind_linear_diagnostics_economic_evidence_consumer_v0,
)
from research.linear_evidence.offline_productive_linear_diagnostics_promotion_economic_gate_consumer_binding_v0 import (
    BLOCKING_REASON_BLOCKED_SOURCE_DIAGNOSTICS_PRESENT,
    CANONICAL_PROMOTION_GATE_OWNER,
    PROMOTION_CONSUMER_BINDING_OWNER,
    PromotionEconomicGateConsumerBindingError,
    build_promotion_gate_input_from_linear_diagnostics_consumer_binding_v0,
    evaluate_promotion_economic_gate_from_linear_diagnostics_consumer_binding_v0,
)
from research.linear_evidence.offline_productive_linear_diagnostics_support_bundle_v0 import (
    SupportAggregateStatus,
)
from scripts.ops.primary_evidence_retention_v0 import verify_manifest_sha256
from src.governance.economic_diagnostic_optimization_boundary_v0 import build_boundary_report
from src.governance.promotion_loop import promotion_economic_gate_v1 as gate
from src.research.bouchaud_microstructure_ohlcv_proxy_v1_offline_productive_linear_diagnostics_execution_and_support_evidence_v0 import (
    CANONICAL_FEATURE_DIGEST,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
MATERIALIZER = REPO_ROOT / (
    "scripts/ops/"
    "materialize_bouchaud_microstructure_ohlcv_proxy_v1_offline_productive_linear_diagnostics_"
    "promotion_economic_gate_consumer_binding_v0.py"
)
GENERIC_PROMOTION_OWNER = REPO_ROOT / (
    "src/research/linear_evidence/"
    "offline_productive_linear_diagnostics_promotion_economic_gate_consumer_binding_v0.py"
)
PR5192_IMPLEMENTATION_DIR = Path(
    "/Users/frnkhrz/Documents/Peak_Trade_runtime_evidence_archive_20260520T161443Z/research/"
    "bouchaud_microstructure_ohlcv_proxy_v1_offline_productive_linear_diagnostics_"
    "economic_evidence_consumer_binding_v0_20260715T011845Z"
)
PR5192_CLOSEOUT_DIR = Path(
    "/Users/frnkhrz/Documents/Peak_Trade_runtime_evidence_archive_20260520T161443Z/research/"
    "pr5192_merge_closeout_bouchaud_offline_productive_linear_diagnostics_"
    "economic_evidence_consumer_binding_v0_20260715T011845Z"
)
PR5191_IMPLEMENTATION_DIR = Path(
    "/Users/frnkhrz/Documents/Peak_Trade_runtime_evidence_archive_20260520T161443Z/research/"
    "bouchaud_microstructure_ohlcv_proxy_v1_offline_productive_linear_diagnostics_"
    "execution_and_support_evidence_v0_20260715T004424Z"
)
PR5187_CLOSEOUT_DIR = Path(
    "/Users/frnkhrz/Documents/Peak_Trade_runtime_evidence_archive_20260520T161443Z/research/"
    "pr5187_merge_closeout_offline_productive_linear_diagnostics_"
    "promotion_economic_gate_consumer_binding_v0_20260714T233336Z"
)
PRODUCTIVE_SUPPORT_BUNDLE_ARTIFACT = "productive_support_bundle.json"

FORBIDDEN_RUNTIME_IMPORT_PREFIXES = (
    "src.execution",
    "src.scheduler",
    "src.broker",
    "src.orders",
)


def _load_materializer_module():
    spec = importlib.util.spec_from_file_location("bouchaud_promotion_materializer", MATERIALIZER)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules["bouchaud_promotion_materializer"] = module
    spec.loader.exec_module(module)
    return module


def _archive_available() -> bool:
    return (
        PR5192_IMPLEMENTATION_DIR.is_dir()
        and PR5191_IMPLEMENTATION_DIR.is_dir()
        and (PR5191_IMPLEMENTATION_DIR / PRODUCTIVE_SUPPORT_BUNDLE_ARTIFACT).is_file()
        and PR5192_CLOSEOUT_DIR.is_dir()
    )


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
def materializer_module():
    return _load_materializer_module()


@pytest.fixture(scope="module")
def promotion_binding(materializer_module):
    if not _archive_available():
        pytest.skip("PR5192 archive evidence unavailable")
    ok, _ = verify_manifest_sha256(PR5192_IMPLEMENTATION_DIR)
    assert ok
    _, _, promotion = materializer_module.bind_bouchaud_promotion_economic_gate_consumer_v0(
        pr5191_implementation_dir=PR5191_IMPLEMENTATION_DIR,
        pr5192_implementation_dir=PR5192_IMPLEMENTATION_DIR,
        expected_feature_digest=CANONICAL_FEATURE_DIGEST,
        verify_fn=verify_manifest_sha256,
    )
    return promotion


@pytest.fixture(scope="module")
def consumer_binding(materializer_module):
    if not _archive_available():
        pytest.skip("PR5192 archive evidence unavailable")
    _, consumer, _ = materializer_module.bind_bouchaud_promotion_economic_gate_consumer_v0(
        pr5191_implementation_dir=PR5191_IMPLEMENTATION_DIR,
        pr5192_implementation_dir=PR5192_IMPLEMENTATION_DIR,
        expected_feature_digest=CANONICAL_FEATURE_DIGEST,
        verify_fn=verify_manifest_sha256,
    )
    return consumer


def test_generic_promotion_consumer_owner_reused() -> None:
    assert CANONICAL_PROMOTION_GATE_OWNER == gate.PROMOTION_ECONOMIC_GATE_POLICY_OWNER


def test_real_generic_promotion_consumer_path_invoked(promotion_binding) -> None:
    assert promotion_binding.owner == PROMOTION_CONSUMER_BINDING_OWNER
    assert (
        promotion_binding.canonical_promotion_gate_owner
        == gate.PROMOTION_ECONOMIC_GATE_POLICY_OWNER
    )
    assert promotion_binding.gate_result.gate_policy_id == gate.PROMOTION_ECONOMIC_GATE_POLICY_ID
    assert promotion_binding.economic_evidence_consumer_source.endswith(
        "offline_productive_linear_diagnostics_economic_evidence_consumer_binding_v0"
    )


def test_valid_bouchaud_support_bundle_accepted(promotion_binding, consumer_binding) -> None:
    assert consumer_binding.linear_diagnostics_referenced is True
    assert consumer_binding.linear_diagnostic_class_count == 5
    assert consumer_binding.owner == CONSUMER_BINDING_OWNER
    assert promotion_binding.promotion_economic_gate_status == "BLOCKED"
    assert promotion_binding.promotion_candidate_eligible is False


def test_blocked_source_diagnostics_present_remains_blocking(promotion_binding) -> None:
    assert (
        promotion_binding.economic_evidence_admissibility
        == EconomicEvidenceAdmissibility.BLOCKED_SOURCE_DIAGNOSTICS_PRESENT.value
    )
    assert BLOCKING_REASON_BLOCKED_SOURCE_DIAGNOSTICS_PRESENT in promotion_binding.blocking_reason
    assert gate.REASON_ECONOMIC_EVIDENCE_INADMISSIBLE in promotion_binding.gate_result.reason_codes


def test_wrong_feature_digest_rejected(materializer_module) -> None:
    if not _archive_available():
        pytest.skip("PR5192 archive evidence unavailable")
    with pytest.raises(
        materializer_module.BouchaudPromotionConsumerBindingValidationError,
        match="FEATURE_DIGEST_MISMATCH",
    ):
        materializer_module.bind_bouchaud_promotion_economic_gate_consumer_v0(
            pr5191_implementation_dir=PR5191_IMPLEMENTATION_DIR,
            pr5192_implementation_dir=PR5192_IMPLEMENTATION_DIR,
            expected_feature_digest="0" * 64,
            verify_fn=verify_manifest_sha256,
        )


def test_missing_support_bundle_rejected(materializer_module, tmp_path: Path) -> None:
    missing_dir = tmp_path / "missing_support"
    missing_dir.mkdir()
    with pytest.raises(
        materializer_module.BouchaudPromotionConsumerBindingValidationError,
        match="MISSING_FEATURE_MATRIX_BINDING|MISSING_PRODUCTIVE_SUPPORT_BUNDLE",
    ):
        materializer_module.bind_bouchaud_promotion_economic_gate_consumer_v0(
            pr5191_implementation_dir=missing_dir,
            pr5192_implementation_dir=PR5192_IMPLEMENTATION_DIR,
            expected_feature_digest=CANONICAL_FEATURE_DIGEST,
            verify_fn=verify_manifest_sha256,
        )


def test_missing_pr5192_implementation_rejected(materializer_module, tmp_path: Path) -> None:
    if not _archive_available():
        pytest.skip("PR5192 archive evidence unavailable")
    missing_dir = tmp_path / "missing_pr5192"
    with pytest.raises(
        materializer_module.BouchaudPromotionConsumerBindingValidationError,
        match="MISSING_PR5192_IMPLEMENTATION_DIR",
    ):
        materializer_module.bind_bouchaud_promotion_economic_gate_consumer_v0(
            pr5191_implementation_dir=PR5191_IMPLEMENTATION_DIR,
            pr5192_implementation_dir=missing_dir,
            expected_feature_digest=CANONICAL_FEATURE_DIGEST,
            verify_fn=verify_manifest_sha256,
        )


def test_missing_linear_diagnostics_reference_fail_closed(materializer_module) -> None:
    if not _archive_available():
        pytest.skip("PR5192 archive evidence unavailable")
    economic_materializer = materializer_module._load_economic_consumer_materializer()
    support_bundle = economic_materializer.load_referenced_productive_support_bundle_v0(
        PR5191_IMPLEMENTATION_DIR
    )
    broken = dict(support_bundle)
    broken["cost_diagnostics_ref"] = ""
    with pytest.raises(LinearDiagnosticsConsumerBindingError, match="MISSING_DIAGNOSTIC_REF"):
        bind_linear_diagnostics_economic_evidence_consumer_v0(
            support_bundle=broken,
            verify_fn=verify_manifest_sha256,
        )


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
    materializer_module = _load_materializer_module()
    ctx_obj = materializer_module.default_bouchaud_promotion_consumer_binding_context_v0(
        broken,
        feature_digest=CANONICAL_FEATURE_DIGEST,
    )
    result = evaluate_promotion_economic_gate_from_linear_diagnostics_consumer_binding_v0(
        consumer_binding=broken,
        ctx=ctx_obj,
    )
    assert result.promotion_candidate_eligible is False
    assert result.promotion_economic_gate_status in {"BLOCKED", "INELIGIBLE"}


def test_linear_evidence_alone_no_promotion_pass(promotion_binding) -> None:
    assert promotion_binding.promotion_pass_created is False
    assert promotion_binding.economic_evaluation_executed is False
    assert promotion_binding.economic_validity_pass_created is False
    assert promotion_binding.gate_result.promotion_eligible is False
    assert promotion_binding.gate_result.shadow_candidate_eligible is False


def test_inconsistent_aggregate_rejected(consumer_binding) -> None:
    inconsistent = replace(
        consumer_binding,
        aggregate_status=SupportAggregateStatus.BLOCK_SUPPORT_EVIDENCE.value,
        economic_evidence_admissibility=(
            EconomicEvidenceAdmissibility.DIAGNOSTIC_SUPPORT_REFERENCE_READY.value
        ),
    )
    materializer_module = _load_materializer_module()
    ctx = materializer_module.default_bouchaud_promotion_consumer_binding_context_v0(
        inconsistent,
        feature_digest=CANONICAL_FEATURE_DIGEST,
    )
    with pytest.raises(PromotionEconomicGateConsumerBindingError, match="INCONSISTENT"):
        build_promotion_gate_input_from_linear_diagnostics_consumer_binding_v0(
            ctx=ctx,
            consumer_binding=inconsistent,
        )


def test_repeated_materialization_deterministic(promotion_binding, materializer_module) -> None:
    if not _archive_available():
        pytest.skip("PR5192 archive evidence unavailable")
    _, _, second = materializer_module.bind_bouchaud_promotion_economic_gate_consumer_v0(
        pr5191_implementation_dir=PR5191_IMPLEMENTATION_DIR,
        pr5192_implementation_dir=PR5192_IMPLEMENTATION_DIR,
        expected_feature_digest=CANONICAL_FEATURE_DIGEST,
        verify_fn=verify_manifest_sha256,
    )
    assert second.to_dict() == promotion_binding.to_dict()


def test_second_materialization_diff_empty(promotion_binding, materializer_module) -> None:
    if not _archive_available():
        pytest.skip("PR5192 archive evidence unavailable")
    first_payload = json.dumps(promotion_binding.to_dict(), sort_keys=True, separators=(",", ":"))
    _, _, second = materializer_module.bind_bouchaud_promotion_economic_gate_consumer_v0(
        pr5191_implementation_dir=PR5191_IMPLEMENTATION_DIR,
        pr5192_implementation_dir=PR5192_IMPLEMENTATION_DIR,
        expected_feature_digest=CANONICAL_FEATURE_DIGEST,
        verify_fn=verify_manifest_sha256,
    )
    second_payload = json.dumps(second.to_dict(), sort_keys=True, separators=(",", ":"))
    assert first_payload == second_payload


def test_authority_and_runtime_effects_none(promotion_binding) -> None:
    assert promotion_binding.runtime_effect == AUTHORITY_EFFECT == "NONE"
    assert promotion_binding.authority_effect == "NONE"
    assert promotion_binding.gate_result.authority_effect == gate.AUTHORITY_EFFECT_NONE
    assert promotion_binding.gate_result.runtime_effect == gate.RUNTIME_EFFECT_NONE


def test_no_runtime_import_boundary_violation() -> None:
    assert scan_file_import_boundary(MATERIALIZER, repo_root=REPO_ROOT) == []
    source = MATERIALIZER.read_text(encoding="utf-8")
    for prefix in FORBIDDEN_RUNTIME_IMPORT_PREFIXES:
        assert prefix not in source
    assert "src.execution" not in source


def test_generic_promotion_owner_unchanged() -> None:
    source = GENERIC_PROMOTION_OWNER.read_text(encoding="utf-8")
    assert "bouchaud" not in source.lower()


def test_governance_boundary_admissible() -> None:
    report = build_boundary_report(
        [
            str(MATERIALIZER.relative_to(REPO_ROOT)),
            str(Path(__file__).relative_to(REPO_ROOT)),
            "config/governance/economic_diagnostic_optimization_boundary_canonical_owner_map_v0.json",
        ],
        repo_root=REPO_ROOT,
    )
    assert report.admissible is True
    assert report.impact_unknown is False


def test_pr5192_and_pr5187_source_manifests_verified() -> None:
    if not _archive_available():
        pytest.skip("PR5192 archive evidence unavailable")
    ok, _ = verify_manifest_sha256(PR5192_IMPLEMENTATION_DIR)
    assert ok
    ok_closeout, _ = verify_manifest_sha256(PR5192_CLOSEOUT_DIR)
    assert ok_closeout
    if PR5187_CLOSEOUT_DIR.is_dir():
        ok_5187, _ = verify_manifest_sha256(PR5187_CLOSEOUT_DIR)
        assert ok_5187


def test_materializer_roundtrip_manifest_verified(tmp_path: Path) -> None:
    if not _archive_available():
        pytest.skip("PR5192 archive evidence unavailable")
    first_dir = tmp_path / "evidence_a"
    second_dir = tmp_path / "evidence_b"
    first = _run_materializer(first_dir)
    second = _run_materializer(second_dir)
    assert first.returncode == 0, first.stdout + first.stderr
    assert second.returncode == 0, second.stdout + second.stderr

    for bundle in (first_dir, second_dir):
        ok, _ = verify_manifest_sha256(bundle)
        assert ok

    contract_a = json.loads((first_dir / "consumer_contract.json").read_text(encoding="utf-8"))
    contract_b = json.loads((second_dir / "consumer_contract.json").read_text(encoding="utf-8"))
    assert contract_a == contract_b
    assert contract_a["promotion_economic_gate_status"] == "BLOCKED"
    assert contract_a["promotion_candidate_eligible"] is False
    assert contract_a["bouchaud_feature_digest"] == CANONICAL_FEATURE_DIGEST
    final_report = (first_dir / "final_report.txt").read_text(encoding="utf-8")
    assert "PROMOTION_PASS_CREATED=false" in final_report
    assert "ECONOMIC_EVALUATION_EXECUTED=false" in final_report
    assert "RUNTIME_EFFECT=NONE" in final_report
