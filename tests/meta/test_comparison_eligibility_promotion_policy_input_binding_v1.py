"""Contract tests for comparison eligibility promotion policy input binding v1."""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

pytest_plugins = [
    "tests.meta.comparison_ssot_v1_fixtures",
    "tests.meta.comparison_completion_research_validity_binding_v1_fixtures",
    "tests.meta.comparison_completion_promotion_input_binding_v1_fixtures",
    "tests.meta.comparison_promotion_candidate_identity_binding_v1_fixtures",
    "tests.meta.comparison_promotion_candidate_eligibility_evidence_v1_fixtures",
    "tests.meta.comparison_promotion_candidate_model_parameter_identity_binding_v1_fixtures",
    "tests.meta.comparison_config_patch_manifest_cross_domain_lineage_binding_v1_fixtures",
    "tests.meta.comparison_promotion_candidate_input_v1_fixtures",
    "tests.meta.comparison_eligibility_promotion_policy_input_binding_v1_fixtures",
]

from scripts.ops.primary_evidence_retention_v0 import verify_manifest_sha256
from src.meta.learning_loop.comparison_eligibility_promotion_policy_input_binding_v1 import (
    ARTIFACT_REL,
    AUTHORITY_LEVEL,
    CONTRACT_NAME,
    CONTRACT_VERSION,
    EVIDENCE_LEVEL,
    MANIFEST_FILENAME,
    POLICY_INPUT_BINDING_AUTHORITY_INVARIANTS,
    PRODUCER_VERSION,
    SELF_VERIFICATION_REL,
    ComparisonEligibilityPromotionPolicyInputBindingError,
    ComparisonEligibilityPromotionPolicyInputBindingInputs,
    VerifiedCandidateInputBundle,
    build_comparison_eligibility_promotion_policy_input_binding_v1,
    produce_comparison_eligibility_promotion_policy_input_binding_v1,
    reverify_comparison_eligibility_promotion_policy_input_binding_v1,
    serialize_comparison_eligibility_promotion_policy_input_binding_v1,
    verify_binding_inputs,
    verify_candidate_input_bundle,
)
from src.meta.learning_loop.comparison_promotion_candidate_input_v1 import (
    ARTIFACT_REL as STEP3_ARTIFACT_REL,
)
from src.meta.learning_loop.comparison_ssot_v1.io import read_manifest
from src.meta.learning_loop.contract_safety_v1 import deterministic_json_dumps
from tests.meta.comparison_eligibility_promotion_policy_input_binding_v1_fixtures import (
    produce_policy_input_binding_fixture,
)
from tests.meta.comparison_promotion_candidate_input_v1_fixtures import (
    produce_candidate_input_fixture,
)


@pytest.fixture(autouse=True)
def _allow_tmp_output(monkeypatch: pytest.MonkeyPatch) -> None:
    targets = (
        "src.meta.learning_loop.comparison_eligibility_promotion_policy_input_binding_v1.is_under_tmp",
        "src.meta.learning_loop.comparison_promotion_candidate_input_v1.is_under_tmp",
        "src.meta.learning_loop.comparison_config_patch_manifest_cross_domain_lineage_binding_v1.is_under_tmp",
        "src.meta.learning_loop.comparison_promotion_candidate_model_parameter_identity_binding_v1.is_under_tmp",
        "src.meta.learning_loop.comparison_promotion_candidate_eligibility_evidence_v1.is_under_tmp",
        "src.meta.learning_loop.comparison_promotion_candidate_identity_binding_v1.is_under_tmp",
        "src.meta.learning_loop.comparison_completion_promotion_input_binding_v1.is_under_tmp",
        "src.meta.learning_loop.comparison_completion_research_validity_binding_v1.is_under_tmp",
        "src.meta.learning_loop.comparison_completion_evidence_v1.is_under_tmp",
        "src.meta.learning_loop.research_validity_evidence_v1.is_under_tmp",
        "src.meta.learning_loop.comparison_checkpoint_v1.is_under_tmp",
        "src.meta.learning_loop.comparison_common_durable_evidence_binding_v1.is_under_tmp",
        "src.meta.learning_loop.comparison_metric_input_durable_evidence_binding_v1.is_under_tmp",
        "src.meta.learning_loop.comparison_ssot_definition_durable_evidence_binding_v1.is_under_tmp",
        "src.meta.learning_loop.comparison_ssot_result_durable_evidence_binding_v1.is_under_tmp",
        "src.experiments.experiment_identity_manifest_v1.is_under_tmp",
    )
    for target in targets:
        monkeypatch.setattr(target, lambda _path: False)


def _durable_output(tmp_path: Path, name: str = "policy_input_binding_out") -> Path:
    root = tmp_path / "evidence_root"
    root.mkdir(exist_ok=True)
    return root / name


def _inputs(step3_dir: Path) -> ComparisonEligibilityPromotionPolicyInputBindingInputs:
    return ComparisonEligibilityPromotionPolicyInputBindingInputs(
        candidate_input_bundle_dir=step3_dir,
    )


def test_contract_constants() -> None:
    assert CONTRACT_NAME == "comparison_eligibility_promotion_policy_input_binding_v1"
    assert CONTRACT_VERSION == "v1"
    assert EVIDENCE_LEVEL == "LEVEL_3"
    assert AUTHORITY_LEVEL == "NON_AUTHORITIZING_EVIDENCE_ONLY"
    assert ARTIFACT_REL == "comparison_eligibility_promotion_policy_input_binding_v1.json"


def test_happy_path_pass(tmp_path, ssot_durable_output_dir) -> None:
    fixture = produce_policy_input_binding_fixture(tmp_path, ssot_durable_output_dir)
    assert fixture.policy_input_binding_bundle_dir is not None
    payload = read_manifest(fixture.policy_input_binding_bundle_dir / ARTIFACT_REL)
    assert payload["eligibility_policy_input_binding_status"] == "PASS"
    assert payload["candidate_input_bound_status"] == "BOUND"
    assert payload["candidate_identity_bound_status"] == "BOUND"
    assert payload["eligibility_evidence_bound_status"] == "VERIFIED"
    assert payload["cross_domain_lineage_bound_status"] == "BOUND"
    assert payload["config_patch_manifest_bound_status"] == "BOUND"
    assert payload["eligibility_policy_input_bound_status"] == "BOUND"
    assert payload["candidate_selection_status"] == "NOT_SELECTED"
    assert payload["promotion_candidate_constructed"] is False
    assert payload["eligibility_recomputed"] is False
    assert payload["promotion_policy_executed"] is False
    assert (
        "COMPARISON_ELIGIBILITY_PROMOTION_POLICY_INPUT_BINDING_COMPLETE"
        in payload["eligibility_policy_input_binding_reason_codes"]
    )


def test_required_non_authorizing_flags(tmp_path, ssot_durable_output_dir) -> None:
    fixture = produce_policy_input_binding_fixture(tmp_path, ssot_durable_output_dir)
    payload = read_manifest(fixture.policy_input_binding_bundle_dir / ARTIFACT_REL)
    assert payload["policy_input_binding_does_not_select"] is True
    assert payload["policy_input_binding_does_not_recompute_eligibility"] is True
    assert payload["configpatch_created"] is False
    assert payload["configpatch_accepted"] is False
    assert payload["candidate_selected"] is False
    assert payload["runtime_authorized"] is False
    assert payload["live_authorized"] is False
    assert payload["orders_allowed"] is False
    assert (
        payload["policy_input_binding_authority_invariants"]
        == POLICY_INPUT_BINDING_AUTHORITY_INVARIANTS
    )


def test_determinism(tmp_path, ssot_durable_output_dir) -> None:
    candidate_input = produce_candidate_input_fixture(tmp_path, ssot_durable_output_dir)
    assert candidate_input.candidate_input_bundle_dir is not None
    out_a = _durable_output(tmp_path, "a")
    out_b = _durable_output(tmp_path, "b")
    inputs = _inputs(candidate_input.candidate_input_bundle_dir)
    produce_comparison_eligibility_promotion_policy_input_binding_v1(
        inputs=inputs, output_dir=out_a
    )
    produce_comparison_eligibility_promotion_policy_input_binding_v1(
        inputs=inputs, output_dir=out_b
    )
    assert (out_a / ARTIFACT_REL).read_text() == (out_b / ARTIFACT_REL).read_text()


def test_self_verification_and_manifest(tmp_path, ssot_durable_output_dir) -> None:
    fixture = produce_policy_input_binding_fixture(tmp_path, ssot_durable_output_dir)
    out = fixture.policy_input_binding_bundle_dir
    assert out is not None
    ok, msg = verify_manifest_sha256(out)
    assert ok, msg
    self_payload = read_manifest(out / SELF_VERIFICATION_REL)
    assert self_payload["overall_status"] == "PASS"
    reverify_comparison_eligibility_promotion_policy_input_binding_v1(output_dir=out)


def test_missing_step3_bundle(tmp_path) -> None:
    with pytest.raises(ComparisonEligibilityPromotionPolicyInputBindingError):
        verify_candidate_input_bundle(tmp_path / "missing")


def test_invalid_step3_manifest(tmp_path, ssot_durable_output_dir) -> None:
    candidate_input = produce_candidate_input_fixture(tmp_path, ssot_durable_output_dir)
    assert candidate_input.candidate_input_bundle_dir is not None
    step3_dir = candidate_input.candidate_input_bundle_dir
    (step3_dir / "MANIFEST.sha256").write_text("invalid", encoding="utf-8")
    with pytest.raises(ComparisonEligibilityPromotionPolicyInputBindingError):
        verify_candidate_input_bundle(step3_dir)


def test_step3_self_verification_manipulation(tmp_path, ssot_durable_output_dir) -> None:
    candidate_input = produce_candidate_input_fixture(tmp_path, ssot_durable_output_dir)
    assert candidate_input.candidate_input_bundle_dir is not None
    step3_dir = candidate_input.candidate_input_bundle_dir
    self_path = step3_dir / "SELF_VERIFICATION.json"
    payload = read_manifest(self_path)
    payload["overall_status"] = "FAIL"
    self_path.write_text(deterministic_json_dumps(payload), encoding="utf-8")
    with pytest.raises(ComparisonEligibilityPromotionPolicyInputBindingError):
        verify_candidate_input_bundle(step3_dir)


def test_step3_contract_version_mismatch(tmp_path, ssot_durable_output_dir) -> None:
    candidate_input = produce_candidate_input_fixture(tmp_path, ssot_durable_output_dir)
    assert candidate_input.candidate_input_bundle_dir is not None
    artifact_path = candidate_input.candidate_input_bundle_dir / STEP3_ARTIFACT_REL
    payload = read_manifest(artifact_path)
    payload["contract_version"] = "v99"
    artifact_path.write_text(deterministic_json_dumps(payload), encoding="utf-8")
    with pytest.raises(ComparisonEligibilityPromotionPolicyInputBindingError):
        verify_candidate_input_bundle(candidate_input.candidate_input_bundle_dir)


def test_eligibility_evidence_digest_mismatch_fail(tmp_path, ssot_durable_output_dir) -> None:
    candidate_input = produce_candidate_input_fixture(tmp_path, ssot_durable_output_dir)
    assert candidate_input.candidate_input_bundle_dir is not None
    step3 = verify_candidate_input_bundle(candidate_input.candidate_input_bundle_dir)
    tampered = dict(step3.evidence_payload)
    tampered["eligibility_evidence_digest"] = "0" * 64
    tampered_bundle = VerifiedCandidateInputBundle(
        bundle_dir=step3.bundle_dir,
        contract_name=step3.contract_name,
        contract_version=step3.contract_version,
        producer_version=step3.producer_version,
        artifact_ref=step3.artifact_ref,
        artifact_digest=step3.artifact_digest,
        manifest_digest=step3.manifest_digest,
        evidence_payload=tampered,
    )
    payload = build_comparison_eligibility_promotion_policy_input_binding_v1(
        candidate_input=tampered_bundle
    )
    assert payload["eligibility_policy_input_binding_status"] == "FAIL"
    assert (
        "ELIGIBILITY_EVIDENCE_DIGEST_MISMATCH"
        in payload["eligibility_policy_input_binding_reason_codes"]
    )


def test_candidate_identity_mismatch_fail(tmp_path, ssot_durable_output_dir) -> None:
    candidate_input = produce_candidate_input_fixture(tmp_path, ssot_durable_output_dir)
    assert candidate_input.candidate_input_bundle_dir is not None
    step3 = verify_candidate_input_bundle(candidate_input.candidate_input_bundle_dir)
    tampered = dict(step3.evidence_payload)
    tampered["candidate_identity_status"] = "NOT_BOUND"
    tampered_bundle = VerifiedCandidateInputBundle(
        bundle_dir=step3.bundle_dir,
        contract_name=step3.contract_name,
        contract_version=step3.contract_version,
        producer_version=step3.producer_version,
        artifact_ref=step3.artifact_ref,
        artifact_digest=step3.artifact_digest,
        manifest_digest=step3.manifest_digest,
        evidence_payload=tampered,
    )
    payload = build_comparison_eligibility_promotion_policy_input_binding_v1(
        candidate_input=tampered_bundle
    )
    assert payload["eligibility_policy_input_binding_status"] == "FAIL"
    assert "CANDIDATE_LINEAGE_MISMATCH" in payload["eligibility_policy_input_binding_reason_codes"]


def test_cross_domain_lineage_mismatch_fail(tmp_path, ssot_durable_output_dir) -> None:
    candidate_input = produce_candidate_input_fixture(tmp_path, ssot_durable_output_dir)
    assert candidate_input.candidate_input_bundle_dir is not None
    step3 = verify_candidate_input_bundle(candidate_input.candidate_input_bundle_dir)
    tampered = dict(step3.evidence_payload)
    tampered["cross_domain_lineage_status"] = "NOT_BOUND"
    tampered_bundle = VerifiedCandidateInputBundle(
        bundle_dir=step3.bundle_dir,
        contract_name=step3.contract_name,
        contract_version=step3.contract_version,
        producer_version=step3.producer_version,
        artifact_ref=step3.artifact_ref,
        artifact_digest=step3.artifact_digest,
        manifest_digest=step3.manifest_digest,
        evidence_payload=tampered,
    )
    payload = build_comparison_eligibility_promotion_policy_input_binding_v1(
        candidate_input=tampered_bundle
    )
    assert payload["eligibility_policy_input_binding_status"] == "FAIL"
    assert (
        "CROSS_DOMAIN_LINEAGE_NOT_BOUND" in payload["eligibility_policy_input_binding_reason_codes"]
    )


def test_config_patch_manifest_mismatch_fail(tmp_path, ssot_durable_output_dir) -> None:
    candidate_input = produce_candidate_input_fixture(tmp_path, ssot_durable_output_dir)
    assert candidate_input.candidate_input_bundle_dir is not None
    step3 = verify_candidate_input_bundle(candidate_input.candidate_input_bundle_dir)
    tampered = dict(step3.evidence_payload)
    tampered["config_patch_manifest_identity_status"] = "NOT_BOUND"
    tampered_bundle = VerifiedCandidateInputBundle(
        bundle_dir=step3.bundle_dir,
        contract_name=step3.contract_name,
        contract_version=step3.contract_version,
        producer_version=step3.producer_version,
        artifact_ref=step3.artifact_ref,
        artifact_digest=step3.artifact_digest,
        manifest_digest=step3.manifest_digest,
        evidence_payload=tampered,
    )
    payload = build_comparison_eligibility_promotion_policy_input_binding_v1(
        candidate_input=tampered_bundle
    )
    assert payload["eligibility_policy_input_binding_status"] == "FAIL"
    assert (
        "CONFIG_PATCH_LINEAGE_MISMATCH" in payload["eligibility_policy_input_binding_reason_codes"]
    )


def test_upstream_fail_propagation(tmp_path, ssot_durable_output_dir) -> None:
    candidate_input = produce_candidate_input_fixture(tmp_path, ssot_durable_output_dir)
    assert candidate_input.candidate_input_bundle_dir is not None
    step3 = verify_candidate_input_bundle(candidate_input.candidate_input_bundle_dir)
    tampered = dict(step3.evidence_payload)
    tampered["candidate_input_status"] = "FAIL"
    tampered_bundle = VerifiedCandidateInputBundle(
        bundle_dir=step3.bundle_dir,
        contract_name=step3.contract_name,
        contract_version=step3.contract_version,
        producer_version=step3.producer_version,
        artifact_ref=step3.artifact_ref,
        artifact_digest=step3.artifact_digest,
        manifest_digest=step3.manifest_digest,
        evidence_payload=tampered,
    )
    payload = build_comparison_eligibility_promotion_policy_input_binding_v1(
        candidate_input=tampered_bundle
    )
    assert payload["eligibility_policy_input_binding_status"] == "FAIL"
    assert (
        "UPSTREAM_CANDIDATE_INPUT_FAIL" in payload["eligibility_policy_input_binding_reason_codes"]
    )


def test_candidate_selection_detected_fail(tmp_path, ssot_durable_output_dir) -> None:
    candidate_input = produce_candidate_input_fixture(tmp_path, ssot_durable_output_dir)
    assert candidate_input.candidate_input_bundle_dir is not None
    step3 = verify_candidate_input_bundle(candidate_input.candidate_input_bundle_dir)
    tampered = dict(step3.evidence_payload)
    tampered["candidate_selection_status"] = "SELECTED"
    tampered_bundle = VerifiedCandidateInputBundle(
        bundle_dir=step3.bundle_dir,
        contract_name=step3.contract_name,
        contract_version=step3.contract_version,
        producer_version=step3.producer_version,
        artifact_ref=step3.artifact_ref,
        artifact_digest=step3.artifact_digest,
        manifest_digest=step3.manifest_digest,
        evidence_payload=tampered,
    )
    payload = build_comparison_eligibility_promotion_policy_input_binding_v1(
        candidate_input=tampered_bundle
    )
    assert payload["eligibility_policy_input_binding_status"] == "FAIL"
    assert (
        "CANDIDATE_SELECTION_DETECTED" in payload["eligibility_policy_input_binding_reason_codes"]
    )


def test_promotion_candidate_construction_detected_fail(tmp_path, ssot_durable_output_dir) -> None:
    candidate_input = produce_candidate_input_fixture(tmp_path, ssot_durable_output_dir)
    assert candidate_input.candidate_input_bundle_dir is not None
    step3 = verify_candidate_input_bundle(candidate_input.candidate_input_bundle_dir)
    tampered = dict(step3.evidence_payload)
    tampered["promotion_candidate_constructed"] = True
    tampered_bundle = VerifiedCandidateInputBundle(
        bundle_dir=step3.bundle_dir,
        contract_name=step3.contract_name,
        contract_version=step3.contract_version,
        producer_version=step3.producer_version,
        artifact_ref=step3.artifact_ref,
        artifact_digest=step3.artifact_digest,
        manifest_digest=step3.manifest_digest,
        evidence_payload=tampered,
    )
    payload = build_comparison_eligibility_promotion_policy_input_binding_v1(
        candidate_input=tampered_bundle
    )
    assert payload["eligibility_policy_input_binding_status"] == "FAIL"
    assert (
        "PROMOTION_CANDIDATE_CONSTRUCTION_DETECTED"
        in payload["eligibility_policy_input_binding_reason_codes"]
    )


def test_promotion_policy_executed_detected_fail(tmp_path, ssot_durable_output_dir) -> None:
    candidate_input = produce_candidate_input_fixture(tmp_path, ssot_durable_output_dir)
    assert candidate_input.candidate_input_bundle_dir is not None
    step3 = verify_candidate_input_bundle(candidate_input.candidate_input_bundle_dir)
    tampered = dict(step3.evidence_payload)
    tampered["promotion_policy_executed"] = True
    tampered_bundle = VerifiedCandidateInputBundle(
        bundle_dir=step3.bundle_dir,
        contract_name=step3.contract_name,
        contract_version=step3.contract_version,
        producer_version=step3.producer_version,
        artifact_ref=step3.artifact_ref,
        artifact_digest=step3.artifact_digest,
        manifest_digest=step3.manifest_digest,
        evidence_payload=tampered,
    )
    payload = build_comparison_eligibility_promotion_policy_input_binding_v1(
        candidate_input=tampered_bundle
    )
    assert payload["eligibility_policy_input_binding_status"] == "FAIL"
    assert "PROMOTION_POLICY_DETECTED" in payload["eligibility_policy_input_binding_reason_codes"]


def test_configpatch_acceptance_detected_fail(tmp_path, ssot_durable_output_dir) -> None:
    candidate_input = produce_candidate_input_fixture(tmp_path, ssot_durable_output_dir)
    assert candidate_input.candidate_input_bundle_dir is not None
    step3 = verify_candidate_input_bundle(candidate_input.candidate_input_bundle_dir)
    tampered = dict(step3.evidence_payload)
    tampered["config_patch_acceptance_status"] = "ACCEPTED"
    tampered_bundle = VerifiedCandidateInputBundle(
        bundle_dir=step3.bundle_dir,
        contract_name=step3.contract_name,
        contract_version=step3.contract_version,
        producer_version=step3.producer_version,
        artifact_ref=step3.artifact_ref,
        artifact_digest=step3.artifact_digest,
        manifest_digest=step3.manifest_digest,
        evidence_payload=tampered,
    )
    payload = build_comparison_eligibility_promotion_policy_input_binding_v1(
        candidate_input=tampered_bundle
    )
    assert payload["eligibility_policy_input_binding_status"] == "FAIL"
    assert (
        "CONFIG_PATCH_ACCEPTANCE_DETECTED"
        in payload["eligibility_policy_input_binding_reason_codes"]
    )


def test_runtime_authorized_flag_rejected_on_serialize(tmp_path, ssot_durable_output_dir) -> None:
    fixture = produce_policy_input_binding_fixture(tmp_path, ssot_durable_output_dir)
    payload = read_manifest(fixture.policy_input_binding_bundle_dir / ARTIFACT_REL)
    payload["runtime_authorized"] = True
    with pytest.raises(ComparisonEligibilityPromotionPolicyInputBindingError):
        serialize_comparison_eligibility_promotion_policy_input_binding_v1(payload)


def test_live_authorized_flag_rejected_on_serialize(tmp_path, ssot_durable_output_dir) -> None:
    fixture = produce_policy_input_binding_fixture(tmp_path, ssot_durable_output_dir)
    payload = read_manifest(fixture.policy_input_binding_bundle_dir / ARTIFACT_REL)
    payload["live_authorized"] = True
    with pytest.raises(ComparisonEligibilityPromotionPolicyInputBindingError):
        serialize_comparison_eligibility_promotion_policy_input_binding_v1(payload)


def test_orders_allowed_flag_rejected_on_serialize(tmp_path, ssot_durable_output_dir) -> None:
    fixture = produce_policy_input_binding_fixture(tmp_path, ssot_durable_output_dir)
    payload = read_manifest(fixture.policy_input_binding_bundle_dir / ARTIFACT_REL)
    payload["orders_allowed"] = True
    with pytest.raises(ComparisonEligibilityPromotionPolicyInputBindingError):
        serialize_comparison_eligibility_promotion_policy_input_binding_v1(payload)


def test_candidate_selected_flag_rejected_on_serialize(tmp_path, ssot_durable_output_dir) -> None:
    fixture = produce_policy_input_binding_fixture(tmp_path, ssot_durable_output_dir)
    payload = read_manifest(fixture.policy_input_binding_bundle_dir / ARTIFACT_REL)
    payload["candidate_selected"] = True
    with pytest.raises(ComparisonEligibilityPromotionPolicyInputBindingError):
        serialize_comparison_eligibility_promotion_policy_input_binding_v1(payload)


def test_promotion_candidate_constructed_flag_rejected_on_serialize(
    tmp_path, ssot_durable_output_dir
) -> None:
    fixture = produce_policy_input_binding_fixture(tmp_path, ssot_durable_output_dir)
    payload = read_manifest(fixture.policy_input_binding_bundle_dir / ARTIFACT_REL)
    payload["promotion_candidate_constructed"] = True
    with pytest.raises(ComparisonEligibilityPromotionPolicyInputBindingError):
        serialize_comparison_eligibility_promotion_policy_input_binding_v1(payload)


def test_promotion_policy_executed_flag_rejected_on_serialize(
    tmp_path, ssot_durable_output_dir
) -> None:
    fixture = produce_policy_input_binding_fixture(tmp_path, ssot_durable_output_dir)
    payload = read_manifest(fixture.policy_input_binding_bundle_dir / ARTIFACT_REL)
    payload["promotion_policy_executed"] = True
    with pytest.raises(ComparisonEligibilityPromotionPolicyInputBindingError):
        serialize_comparison_eligibility_promotion_policy_input_binding_v1(payload)


def test_configpatch_accepted_flag_rejected_on_serialize(tmp_path, ssot_durable_output_dir) -> None:
    fixture = produce_policy_input_binding_fixture(tmp_path, ssot_durable_output_dir)
    payload = read_manifest(fixture.policy_input_binding_bundle_dir / ARTIFACT_REL)
    payload["configpatch_accepted"] = True
    with pytest.raises(ComparisonEligibilityPromotionPolicyInputBindingError):
        serialize_comparison_eligibility_promotion_policy_input_binding_v1(payload)


def test_forbidden_key_rejected_on_serialize(tmp_path, ssot_durable_output_dir) -> None:
    fixture = produce_policy_input_binding_fixture(tmp_path, ssot_durable_output_dir)
    payload = read_manifest(fixture.policy_input_binding_bundle_dir / ARTIFACT_REL)
    payload["promotion"] = True
    with pytest.raises(ComparisonEligibilityPromotionPolicyInputBindingError):
        serialize_comparison_eligibility_promotion_policy_input_binding_v1(payload)


def test_input_artifact_refs_exactly_one(tmp_path, ssot_durable_output_dir) -> None:
    fixture = produce_policy_input_binding_fixture(tmp_path, ssot_durable_output_dir)
    payload = read_manifest(fixture.policy_input_binding_bundle_dir / ARTIFACT_REL)
    assert len(payload["input_artifact_refs"]) == 1


def test_reason_codes_sorted(tmp_path, ssot_durable_output_dir) -> None:
    fixture = produce_policy_input_binding_fixture(tmp_path, ssot_durable_output_dir)
    payload = read_manifest(fixture.policy_input_binding_bundle_dir / ARTIFACT_REL)
    codes = payload["eligibility_policy_input_binding_reason_codes"]
    assert codes == sorted(codes)


def test_output_existing_dir_fail(tmp_path, ssot_durable_output_dir) -> None:
    candidate_input = produce_candidate_input_fixture(tmp_path, ssot_durable_output_dir)
    assert candidate_input.candidate_input_bundle_dir is not None
    out = _durable_output(tmp_path)
    out.mkdir()
    with pytest.raises(ComparisonEligibilityPromotionPolicyInputBindingError):
        produce_comparison_eligibility_promotion_policy_input_binding_v1(
            inputs=_inputs(candidate_input.candidate_input_bundle_dir),
            output_dir=out,
        )


def test_reverify_after_tamper(tmp_path, ssot_durable_output_dir) -> None:
    fixture = produce_policy_input_binding_fixture(tmp_path, ssot_durable_output_dir)
    out = fixture.policy_input_binding_bundle_dir
    assert out is not None
    artifact = read_manifest(out / ARTIFACT_REL)
    artifact["candidate_identity_ref"] = "tampered"
    (out / ARTIFACT_REL).write_text(deterministic_json_dumps(artifact), encoding="utf-8")
    with pytest.raises(ComparisonEligibilityPromotionPolicyInputBindingError):
        reverify_comparison_eligibility_promotion_policy_input_binding_v1(output_dir=out)


def test_no_forbidden_runtime_imports() -> None:
    module_path = Path(
        "src/meta/learning_loop/comparison_eligibility_promotion_policy_input_binding_v1.py"
    )
    tree = ast.parse(module_path.read_text(encoding="utf-8"))
    forbidden = {
        "build_promotion_candidates_from_patches",
        "filter_candidates_for_live",
        "PromotionCandidate",
    }
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom):
            for alias in node.names:
                assert alias.name not in forbidden
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            assert node.func.id not in forbidden


def test_step3_regression_still_passes(tmp_path, ssot_durable_output_dir) -> None:
    candidate_input = produce_candidate_input_fixture(tmp_path, ssot_durable_output_dir)
    assert candidate_input.candidate_input_bundle_dir is not None
    payload = read_manifest(candidate_input.candidate_input_bundle_dir / STEP3_ARTIFACT_REL)
    assert payload["candidate_input_status"] == "PASS"


def test_eligibility_evidence_refs_present(tmp_path, ssot_durable_output_dir) -> None:
    fixture = produce_policy_input_binding_fixture(tmp_path, ssot_durable_output_dir)
    payload = read_manifest(fixture.policy_input_binding_bundle_dir / ARTIFACT_REL)
    assert payload["eligibility_evidence_ref"]
    assert payload["eligibility_evidence_digest"]
    assert payload["promotion_input_binding_ref"]
    assert payload["promotion_input_binding_digest"]


def test_verify_binding_inputs(tmp_path, ssot_durable_output_dir) -> None:
    candidate_input = produce_candidate_input_fixture(tmp_path, ssot_durable_output_dir)
    assert candidate_input.candidate_input_bundle_dir is not None
    bundle = verify_binding_inputs(_inputs(candidate_input.candidate_input_bundle_dir))
    assert isinstance(bundle, VerifiedCandidateInputBundle)


def test_copy_inputs_no_mutation(tmp_path, ssot_durable_output_dir) -> None:
    candidate_input = produce_candidate_input_fixture(tmp_path, ssot_durable_output_dir)
    assert candidate_input.candidate_input_bundle_dir is not None
    before = (candidate_input.candidate_input_bundle_dir / STEP3_ARTIFACT_REL).read_bytes()
    out = _durable_output(tmp_path)
    produce_comparison_eligibility_promotion_policy_input_binding_v1(
        inputs=_inputs(candidate_input.candidate_input_bundle_dir),
        output_dir=out,
    )
    assert (candidate_input.candidate_input_bundle_dir / STEP3_ARTIFACT_REL).read_bytes() == before


def test_producer_version_constant() -> None:
    assert PRODUCER_VERSION == "comparison_eligibility_promotion_policy_input_binding_v1"


def test_manifest_files_present(tmp_path, ssot_durable_output_dir) -> None:
    fixture = produce_policy_input_binding_fixture(tmp_path, ssot_durable_output_dir)
    out = fixture.policy_input_binding_bundle_dir
    assert out is not None
    assert (out / ARTIFACT_REL).is_file()
    assert (out / SELF_VERIFICATION_REL).is_file()
    assert (out / MANIFEST_FILENAME).is_file()
