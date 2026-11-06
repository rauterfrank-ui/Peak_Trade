"""Contract tests for comparison promotion policy decision v1."""

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
    "tests.meta.comparison_promotion_policy_input_evidence_v1_fixtures",
    "tests.meta.comparison_promotion_policy_decision_v1_fixtures",
]

from scripts.ops.primary_evidence_retention_v0 import verify_manifest_sha256
from src.meta.learning_loop.comparison_promotion_policy_decision_v1 import (
    ARTIFACT_REL,
    AUTHORITY_LEVEL,
    CONTRACT_NAME,
    CONTRACT_VERSION,
    EVIDENCE_LEVEL,
    MANIFEST_FILENAME,
    PROMOTION_POLICY_DECISION_AUTHORITY_INVARIANTS,
    PRODUCER_VERSION,
    SELF_VERIFICATION_REL,
    ComparisonPromotionPolicyDecisionError,
    ComparisonPromotionPolicyDecisionInputs,
    VerifiedPolicyInputEvidenceBundle,
    build_comparison_promotion_policy_decision_v1,
    produce_comparison_promotion_policy_decision_v1,
    reverify_comparison_promotion_policy_decision_v1,
    serialize_comparison_promotion_policy_decision_v1,
    verify_decision_inputs,
    verify_policy_input_evidence_bundle,
)
from src.meta.learning_loop.comparison_promotion_policy_input_evidence_v1 import (
    ARTIFACT_REL as STEP5_ARTIFACT_REL,
)
from src.meta.learning_loop.comparison_ssot_v1.io import read_manifest
from src.meta.learning_loop.contract_safety_v1 import deterministic_json_dumps
from tests.meta.comparison_promotion_policy_decision_v1_fixtures import (
    produce_policy_decision_fixture,
)
from tests.meta.comparison_promotion_policy_input_evidence_v1_fixtures import (
    produce_policy_input_evidence_fixture,
)


@pytest.fixture(autouse=True)
def _allow_tmp_output(monkeypatch: pytest.MonkeyPatch) -> None:
    targets = (
        "src.meta.learning_loop.comparison_promotion_policy_decision_v1.is_under_tmp",
        "src.meta.learning_loop.comparison_promotion_policy_input_evidence_v1.is_under_tmp",
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


def _durable_output(tmp_path: Path, name: str = "policy_decision_out") -> Path:
    root = tmp_path / "evidence_root"
    root.mkdir(exist_ok=True)
    return root / name


def _inputs(step5_dir: Path) -> ComparisonPromotionPolicyDecisionInputs:
    return ComparisonPromotionPolicyDecisionInputs(
        policy_input_evidence_bundle_dir=step5_dir,
    )


def test_contract_constants() -> None:
    assert CONTRACT_NAME == "comparison_promotion_policy_decision_v1"
    assert CONTRACT_VERSION == "v1"
    assert EVIDENCE_LEVEL == "LEVEL_3"
    assert AUTHORITY_LEVEL == "NON_AUTHORITIZING_EVIDENCE_ONLY"
    assert ARTIFACT_REL == "comparison_promotion_policy_decision_v1.json"


def test_happy_path_approve(tmp_path, ssot_durable_output_dir) -> None:
    fixture = produce_policy_decision_fixture(tmp_path, ssot_durable_output_dir)
    assert fixture.promotion_policy_decision_bundle_dir is not None
    payload = read_manifest(fixture.promotion_policy_decision_bundle_dir / ARTIFACT_REL)
    assert payload["decision_status"] == "PASS"
    assert payload["decision_outcome"] == "APPROVE"
    assert payload["policy_input_evidence_bound_status"] == "BOUND"
    assert payload["promotion_decision_complete"] is True
    assert payload["policy_input_evidence_bound"] is True
    assert payload["promotion_decision_created"] is True
    assert payload["promotion_policy_executed"] is False
    assert payload["promotion_authorized"] is False
    assert payload["runtime_authorized"] is False
    assert payload["candidate_selection_status"] == "NOT_SELECTED"
    assert (
        "COMPARISON_PROMOTION_POLICY_DECISION_COMPLETE"
        in payload["promotion_decision_reason_codes"]
    )


def test_required_non_authorizing_flags(tmp_path, ssot_durable_output_dir) -> None:
    fixture = produce_policy_decision_fixture(tmp_path, ssot_durable_output_dir)
    payload = read_manifest(fixture.promotion_policy_decision_bundle_dir / ARTIFACT_REL)
    assert payload["promotion_decision_does_not_select"] is True
    assert payload["promotion_decision_does_not_execute_policy"] is True
    assert payload["configpatch_created"] is False
    assert payload["candidate_selected"] is False
    assert payload["live_authorized"] is False
    assert payload["orders_allowed"] is False
    assert payload["jsonl_side_effect_created"] is False
    assert (
        payload["promotion_decision_authority_invariants"]
        == PROMOTION_POLICY_DECISION_AUTHORITY_INVARIANTS
    )


def test_determinism(tmp_path, ssot_durable_output_dir) -> None:
    evidence = produce_policy_input_evidence_fixture(tmp_path, ssot_durable_output_dir)
    assert evidence.promotion_policy_input_evidence_bundle_dir is not None
    out_a = _durable_output(tmp_path, "a")
    out_b = _durable_output(tmp_path, "b")
    inputs = _inputs(evidence.promotion_policy_input_evidence_bundle_dir)
    produce_comparison_promotion_policy_decision_v1(inputs=inputs, output_dir=out_a)
    produce_comparison_promotion_policy_decision_v1(inputs=inputs, output_dir=out_b)
    assert (out_a / ARTIFACT_REL).read_text() == (out_b / ARTIFACT_REL).read_text()


def test_self_verification_and_manifest(tmp_path, ssot_durable_output_dir) -> None:
    fixture = produce_policy_decision_fixture(tmp_path, ssot_durable_output_dir)
    out = fixture.promotion_policy_decision_bundle_dir
    assert out is not None
    ok, msg = verify_manifest_sha256(out)
    assert ok, msg
    self_payload = read_manifest(out / SELF_VERIFICATION_REL)
    assert self_payload["overall_status"] == "PASS"
    reverify_comparison_promotion_policy_decision_v1(output_dir=out)


def test_missing_step5_bundle(tmp_path) -> None:
    with pytest.raises(ComparisonPromotionPolicyDecisionError):
        verify_policy_input_evidence_bundle(tmp_path / "missing")


def test_invalid_step5_manifest(tmp_path, ssot_durable_output_dir) -> None:
    evidence = produce_policy_input_evidence_fixture(tmp_path, ssot_durable_output_dir)
    assert evidence.promotion_policy_input_evidence_bundle_dir is not None
    step5_dir = evidence.promotion_policy_input_evidence_bundle_dir
    (step5_dir / "MANIFEST.sha256").write_text("invalid", encoding="utf-8")
    with pytest.raises(ComparisonPromotionPolicyDecisionError):
        verify_policy_input_evidence_bundle(step5_dir)


def test_step5_self_verification_manipulation(tmp_path, ssot_durable_output_dir) -> None:
    evidence = produce_policy_input_evidence_fixture(tmp_path, ssot_durable_output_dir)
    assert evidence.promotion_policy_input_evidence_bundle_dir is not None
    step5_dir = evidence.promotion_policy_input_evidence_bundle_dir
    self_path = step5_dir / "SELF_VERIFICATION.json"
    payload = read_manifest(self_path)
    payload["overall_status"] = "FAIL"
    self_path.write_text(deterministic_json_dumps(payload), encoding="utf-8")
    with pytest.raises(ComparisonPromotionPolicyDecisionError):
        verify_policy_input_evidence_bundle(step5_dir)


def test_step5_contract_version_mismatch(tmp_path, ssot_durable_output_dir) -> None:
    evidence = produce_policy_input_evidence_fixture(tmp_path, ssot_durable_output_dir)
    assert evidence.promotion_policy_input_evidence_bundle_dir is not None
    artifact_path = evidence.promotion_policy_input_evidence_bundle_dir / STEP5_ARTIFACT_REL
    payload = read_manifest(artifact_path)
    payload["contract_version"] = "v99"
    artifact_path.write_text(deterministic_json_dumps(payload), encoding="utf-8")
    with pytest.raises(ComparisonPromotionPolicyDecisionError):
        verify_policy_input_evidence_bundle(evidence.promotion_policy_input_evidence_bundle_dir)


def test_upstream_fail_reject(tmp_path, ssot_durable_output_dir) -> None:
    evidence = produce_policy_input_evidence_fixture(tmp_path, ssot_durable_output_dir)
    assert evidence.promotion_policy_input_evidence_bundle_dir is not None
    step5 = verify_policy_input_evidence_bundle(evidence.promotion_policy_input_evidence_bundle_dir)
    tampered = dict(step5.evidence_payload)
    tampered["promotion_policy_input_evidence_status"] = "FAIL"
    tampered_bundle = VerifiedPolicyInputEvidenceBundle(
        bundle_dir=step5.bundle_dir,
        contract_name=step5.contract_name,
        contract_version=step5.contract_version,
        producer_version=step5.producer_version,
        artifact_ref=step5.artifact_ref,
        artifact_digest=step5.artifact_digest,
        manifest_digest=step5.manifest_digest,
        evidence_payload=tampered,
    )
    payload = build_comparison_promotion_policy_decision_v1(policy_input_evidence=tampered_bundle)
    assert payload["decision_status"] == "FAIL"
    assert payload["decision_outcome"] == "REJECT"
    assert "UPSTREAM_POLICY_INPUT_EVIDENCE_FAIL" in payload["promotion_decision_reason_codes"]


def test_upstream_incomplete_defer(tmp_path, ssot_durable_output_dir) -> None:
    evidence = produce_policy_input_evidence_fixture(tmp_path, ssot_durable_output_dir)
    assert evidence.promotion_policy_input_evidence_bundle_dir is not None
    step5 = verify_policy_input_evidence_bundle(evidence.promotion_policy_input_evidence_bundle_dir)
    tampered = dict(step5.evidence_payload)
    tampered["promotion_policy_input_evidence_status"] = "INCOMPLETE"
    tampered_bundle = VerifiedPolicyInputEvidenceBundle(
        bundle_dir=step5.bundle_dir,
        contract_name=step5.contract_name,
        contract_version=step5.contract_version,
        producer_version=step5.producer_version,
        artifact_ref=step5.artifact_ref,
        artifact_digest=step5.artifact_digest,
        manifest_digest=step5.manifest_digest,
        evidence_payload=tampered,
    )
    payload = build_comparison_promotion_policy_decision_v1(policy_input_evidence=tampered_bundle)
    assert payload["decision_status"] == "INCOMPLETE"
    assert payload["decision_outcome"] == "DEFER_INSUFFICIENT_EVIDENCE"
    assert "UPSTREAM_POLICY_INPUT_EVIDENCE_INCOMPLETE" in payload["promotion_decision_reason_codes"]


def test_upstream_not_evaluable_defer(tmp_path, ssot_durable_output_dir) -> None:
    evidence = produce_policy_input_evidence_fixture(tmp_path, ssot_durable_output_dir)
    assert evidence.promotion_policy_input_evidence_bundle_dir is not None
    step5 = verify_policy_input_evidence_bundle(evidence.promotion_policy_input_evidence_bundle_dir)
    tampered = dict(step5.evidence_payload)
    tampered["promotion_policy_input_evidence_status"] = "NOT_EVALUABLE"
    tampered_bundle = VerifiedPolicyInputEvidenceBundle(
        bundle_dir=step5.bundle_dir,
        contract_name=step5.contract_name,
        contract_version=step5.contract_version,
        producer_version=step5.producer_version,
        artifact_ref=step5.artifact_ref,
        artifact_digest=step5.artifact_digest,
        manifest_digest=step5.manifest_digest,
        evidence_payload=tampered,
    )
    payload = build_comparison_promotion_policy_decision_v1(policy_input_evidence=tampered_bundle)
    assert payload["decision_status"] == "NOT_EVALUABLE"
    assert payload["decision_outcome"] == "DEFER_INSUFFICIENT_EVIDENCE"
    assert "NOT_EVALUABLE_INSUFFICIENT_EVIDENCE" in payload["promotion_decision_reason_codes"]


def test_candidate_selection_block_safety(tmp_path, ssot_durable_output_dir) -> None:
    evidence = produce_policy_input_evidence_fixture(tmp_path, ssot_durable_output_dir)
    assert evidence.promotion_policy_input_evidence_bundle_dir is not None
    step5 = verify_policy_input_evidence_bundle(evidence.promotion_policy_input_evidence_bundle_dir)
    tampered = dict(step5.evidence_payload)
    tampered["candidate_selection_status"] = "SELECTED"
    tampered_bundle = VerifiedPolicyInputEvidenceBundle(
        bundle_dir=step5.bundle_dir,
        contract_name=step5.contract_name,
        contract_version=step5.contract_version,
        producer_version=step5.producer_version,
        artifact_ref=step5.artifact_ref,
        artifact_digest=step5.artifact_digest,
        manifest_digest=step5.manifest_digest,
        evidence_payload=tampered,
    )
    payload = build_comparison_promotion_policy_decision_v1(policy_input_evidence=tampered_bundle)
    assert payload["decision_status"] == "FAIL"
    assert payload["decision_outcome"] == "BLOCK_SAFETY"
    assert "CANDIDATE_SELECTION_DETECTED" in payload["promotion_decision_reason_codes"]


def test_promotion_candidate_construction_block_safety(tmp_path, ssot_durable_output_dir) -> None:
    evidence = produce_policy_input_evidence_fixture(tmp_path, ssot_durable_output_dir)
    assert evidence.promotion_policy_input_evidence_bundle_dir is not None
    step5 = verify_policy_input_evidence_bundle(evidence.promotion_policy_input_evidence_bundle_dir)
    tampered = dict(step5.evidence_payload)
    tampered["promotion_candidate_constructed"] = True
    tampered_bundle = VerifiedPolicyInputEvidenceBundle(
        bundle_dir=step5.bundle_dir,
        contract_name=step5.contract_name,
        contract_version=step5.contract_version,
        producer_version=step5.producer_version,
        artifact_ref=step5.artifact_ref,
        artifact_digest=step5.artifact_digest,
        manifest_digest=step5.manifest_digest,
        evidence_payload=tampered,
    )
    payload = build_comparison_promotion_policy_decision_v1(policy_input_evidence=tampered_bundle)
    assert payload["decision_status"] == "FAIL"
    assert payload["decision_outcome"] == "BLOCK_SAFETY"
    assert "PROMOTION_CANDIDATE_CONSTRUCTION_DETECTED" in payload["promotion_decision_reason_codes"]


def test_promotion_policy_executed_block_safety(tmp_path, ssot_durable_output_dir) -> None:
    evidence = produce_policy_input_evidence_fixture(tmp_path, ssot_durable_output_dir)
    assert evidence.promotion_policy_input_evidence_bundle_dir is not None
    step5 = verify_policy_input_evidence_bundle(evidence.promotion_policy_input_evidence_bundle_dir)
    tampered = dict(step5.evidence_payload)
    tampered["promotion_policy_executed"] = True
    tampered_bundle = VerifiedPolicyInputEvidenceBundle(
        bundle_dir=step5.bundle_dir,
        contract_name=step5.contract_name,
        contract_version=step5.contract_version,
        producer_version=step5.producer_version,
        artifact_ref=step5.artifact_ref,
        artifact_digest=step5.artifact_digest,
        manifest_digest=step5.manifest_digest,
        evidence_payload=tampered,
    )
    payload = build_comparison_promotion_policy_decision_v1(policy_input_evidence=tampered_bundle)
    assert payload["decision_status"] == "FAIL"
    assert payload["decision_outcome"] == "BLOCK_SAFETY"
    assert "PROMOTION_POLICY_DETECTED" in payload["promotion_decision_reason_codes"]


def test_promotion_authorized_block_safety(tmp_path, ssot_durable_output_dir) -> None:
    evidence = produce_policy_input_evidence_fixture(tmp_path, ssot_durable_output_dir)
    assert evidence.promotion_policy_input_evidence_bundle_dir is not None
    step5 = verify_policy_input_evidence_bundle(evidence.promotion_policy_input_evidence_bundle_dir)
    tampered = dict(step5.evidence_payload)
    tampered["promotion_authorized"] = True
    tampered_bundle = VerifiedPolicyInputEvidenceBundle(
        bundle_dir=step5.bundle_dir,
        contract_name=step5.contract_name,
        contract_version=step5.contract_version,
        producer_version=step5.producer_version,
        artifact_ref=step5.artifact_ref,
        artifact_digest=step5.artifact_digest,
        manifest_digest=step5.manifest_digest,
        evidence_payload=tampered,
    )
    payload = build_comparison_promotion_policy_decision_v1(policy_input_evidence=tampered_bundle)
    assert payload["decision_status"] == "FAIL"
    assert payload["decision_outcome"] == "BLOCK_SAFETY"
    assert "PROMOTION_AUTHORITY_DETECTED" in payload["promotion_decision_reason_codes"]


def test_runtime_authorized_flag_rejected_on_serialize(tmp_path, ssot_durable_output_dir) -> None:
    fixture = produce_policy_decision_fixture(tmp_path, ssot_durable_output_dir)
    payload = read_manifest(fixture.promotion_policy_decision_bundle_dir / ARTIFACT_REL)
    payload["runtime_authorized"] = True
    with pytest.raises(ComparisonPromotionPolicyDecisionError):
        serialize_comparison_promotion_policy_decision_v1(payload)


def test_promotion_authorized_flag_rejected_on_serialize(tmp_path, ssot_durable_output_dir) -> None:
    fixture = produce_policy_decision_fixture(tmp_path, ssot_durable_output_dir)
    payload = read_manifest(fixture.promotion_policy_decision_bundle_dir / ARTIFACT_REL)
    payload["promotion_authorized"] = True
    with pytest.raises(ComparisonPromotionPolicyDecisionError):
        serialize_comparison_promotion_policy_decision_v1(payload)


def test_promotion_policy_executed_flag_rejected_on_serialize(
    tmp_path, ssot_durable_output_dir
) -> None:
    fixture = produce_policy_decision_fixture(tmp_path, ssot_durable_output_dir)
    payload = read_manifest(fixture.promotion_policy_decision_bundle_dir / ARTIFACT_REL)
    payload["promotion_policy_executed"] = True
    with pytest.raises(ComparisonPromotionPolicyDecisionError):
        serialize_comparison_promotion_policy_decision_v1(payload)


def test_promotion_decision_created_must_be_true_on_serialize(
    tmp_path, ssot_durable_output_dir
) -> None:
    fixture = produce_policy_decision_fixture(tmp_path, ssot_durable_output_dir)
    payload = read_manifest(fixture.promotion_policy_decision_bundle_dir / ARTIFACT_REL)
    payload["promotion_decision_created"] = False
    with pytest.raises(ComparisonPromotionPolicyDecisionError):
        serialize_comparison_promotion_policy_decision_v1(payload)


def test_candidate_selected_flag_rejected_on_serialize(tmp_path, ssot_durable_output_dir) -> None:
    fixture = produce_policy_decision_fixture(tmp_path, ssot_durable_output_dir)
    payload = read_manifest(fixture.promotion_policy_decision_bundle_dir / ARTIFACT_REL)
    payload["candidate_selected"] = True
    with pytest.raises(ComparisonPromotionPolicyDecisionError):
        serialize_comparison_promotion_policy_decision_v1(payload)


def test_forbidden_key_rejected_on_serialize(tmp_path, ssot_durable_output_dir) -> None:
    fixture = produce_policy_decision_fixture(tmp_path, ssot_durable_output_dir)
    payload = read_manifest(fixture.promotion_policy_decision_bundle_dir / ARTIFACT_REL)
    payload["promotion"] = True
    with pytest.raises(ComparisonPromotionPolicyDecisionError):
        serialize_comparison_promotion_policy_decision_v1(payload)


def test_input_artifact_refs_exactly_one(tmp_path, ssot_durable_output_dir) -> None:
    fixture = produce_policy_decision_fixture(tmp_path, ssot_durable_output_dir)
    payload = read_manifest(fixture.promotion_policy_decision_bundle_dir / ARTIFACT_REL)
    assert len(payload["input_artifact_refs"]) == 1


def test_reason_codes_sorted(tmp_path, ssot_durable_output_dir) -> None:
    fixture = produce_policy_decision_fixture(tmp_path, ssot_durable_output_dir)
    payload = read_manifest(fixture.promotion_policy_decision_bundle_dir / ARTIFACT_REL)
    codes = payload["promotion_decision_reason_codes"]
    assert codes == sorted(codes)


def test_output_existing_dir_fail(tmp_path, ssot_durable_output_dir) -> None:
    evidence = produce_policy_input_evidence_fixture(tmp_path, ssot_durable_output_dir)
    assert evidence.promotion_policy_input_evidence_bundle_dir is not None
    out = _durable_output(tmp_path)
    out.mkdir()
    with pytest.raises(ComparisonPromotionPolicyDecisionError):
        produce_comparison_promotion_policy_decision_v1(
            inputs=_inputs(evidence.promotion_policy_input_evidence_bundle_dir),
            output_dir=out,
        )


def test_reverify_after_tamper(tmp_path, ssot_durable_output_dir) -> None:
    fixture = produce_policy_decision_fixture(tmp_path, ssot_durable_output_dir)
    out = fixture.promotion_policy_decision_bundle_dir
    assert out is not None
    artifact = read_manifest(out / ARTIFACT_REL)
    artifact["candidate_identity_ref"] = "tampered"
    (out / ARTIFACT_REL).write_text(deterministic_json_dumps(artifact), encoding="utf-8")
    with pytest.raises(ComparisonPromotionPolicyDecisionError):
        reverify_comparison_promotion_policy_decision_v1(output_dir=out)


def test_no_forbidden_runtime_imports() -> None:
    module_path = Path("src/meta/learning_loop/comparison_promotion_policy_decision_v1.py")
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


def test_step5_regression_still_passes(tmp_path, ssot_durable_output_dir) -> None:
    evidence = produce_policy_input_evidence_fixture(tmp_path, ssot_durable_output_dir)
    assert evidence.promotion_policy_input_evidence_bundle_dir is not None
    payload = read_manifest(
        evidence.promotion_policy_input_evidence_bundle_dir / STEP5_ARTIFACT_REL
    )
    assert payload["promotion_policy_input_evidence_status"] == "PASS"


def test_transitive_refs_present(tmp_path, ssot_durable_output_dir) -> None:
    fixture = produce_policy_decision_fixture(tmp_path, ssot_durable_output_dir)
    payload = read_manifest(fixture.promotion_policy_decision_bundle_dir / ARTIFACT_REL)
    assert payload["eligibility_evidence_ref"]
    assert payload["eligibility_evidence_digest"]
    assert payload["promotion_input_binding_ref"]
    assert payload["policy_input_binding_bundle_ref"]
    assert payload["model_identity_ref"]
    assert payload["parameter_set_identity_ref"]


def test_verify_decision_inputs(tmp_path, ssot_durable_output_dir) -> None:
    evidence = produce_policy_input_evidence_fixture(tmp_path, ssot_durable_output_dir)
    assert evidence.promotion_policy_input_evidence_bundle_dir is not None
    bundle = verify_decision_inputs(_inputs(evidence.promotion_policy_input_evidence_bundle_dir))
    assert isinstance(bundle, VerifiedPolicyInputEvidenceBundle)


def test_copy_inputs_no_mutation(tmp_path, ssot_durable_output_dir) -> None:
    evidence = produce_policy_input_evidence_fixture(tmp_path, ssot_durable_output_dir)
    assert evidence.promotion_policy_input_evidence_bundle_dir is not None
    before = (evidence.promotion_policy_input_evidence_bundle_dir / STEP5_ARTIFACT_REL).read_bytes()
    out = _durable_output(tmp_path)
    produce_comparison_promotion_policy_decision_v1(
        inputs=_inputs(evidence.promotion_policy_input_evidence_bundle_dir),
        output_dir=out,
    )
    assert (
        evidence.promotion_policy_input_evidence_bundle_dir / STEP5_ARTIFACT_REL
    ).read_bytes() == before


def test_producer_version_constant() -> None:
    assert PRODUCER_VERSION == "comparison_promotion_policy_decision_v1"


def test_manifest_files_present(tmp_path, ssot_durable_output_dir) -> None:
    fixture = produce_policy_decision_fixture(tmp_path, ssot_durable_output_dir)
    out = fixture.promotion_policy_decision_bundle_dir
    assert out is not None
    assert (out / ARTIFACT_REL).is_file()
    assert (out / SELF_VERIFICATION_REL).is_file()
    assert (out / MANIFEST_FILENAME).is_file()
