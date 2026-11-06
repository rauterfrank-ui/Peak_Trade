"""Contract tests for ai_promotion_assessment_v1."""

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
    "tests.meta.ai_promotion_assessment_v1_fixtures",
]

from scripts.ops.primary_evidence_retention_v0 import verify_manifest_sha256
from src.meta.learning_loop.ai_promotion_assessment_v1 import (
    ARTIFACT_REL,
    AUTHORITY_LEVEL,
    CONTRACT_NAME,
    CONTRACT_VERSION,
    DETERMINISTIC_RULE_SET_VERSION,
    EVIDENCE_LEVEL,
    MANIFEST_FILENAME,
    AI_PROMOTION_ASSESSMENT_AUTHORITY_INVARIANTS,
    PRODUCER_VERSION,
    SELF_VERIFICATION_REL,
    AiPromotionAssessmentError,
    AiPromotionAssessmentInputs,
    VerifiedPolicyDecisionBundle,
    build_ai_promotion_assessment_v1,
    produce_ai_promotion_assessment_v1,
    reverify_ai_promotion_assessment_v1,
    serialize_ai_promotion_assessment_v1,
    verify_assessment_inputs,
    verify_policy_decision_bundle,
)
from src.meta.learning_loop.comparison_promotion_policy_decision_v1 import (
    ARTIFACT_REL as POLICY_DECISION_ARTIFACT_REL,
)
from src.meta.learning_loop.comparison_ssot_v1.io import read_manifest
from src.meta.learning_loop.contract_safety_v1 import deterministic_json_dumps
from tests.meta.ai_promotion_assessment_v1_fixtures import (
    produce_ai_promotion_assessment_fixture,
)
from tests.meta.comparison_promotion_policy_decision_v1_fixtures import (
    produce_policy_decision_fixture,
)


@pytest.fixture(autouse=True)
def _allow_tmp_output(monkeypatch: pytest.MonkeyPatch) -> None:
    targets = (
        "src.meta.learning_loop.ai_promotion_assessment_v1.is_under_tmp",
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


def _durable_output(tmp_path: Path, name: str = "ai_assessment_out") -> Path:
    root = tmp_path / "evidence_root"
    root.mkdir(exist_ok=True)
    return root / name


def _inputs(policy_decision_dir: Path) -> AiPromotionAssessmentInputs:
    return AiPromotionAssessmentInputs(policy_decision_bundle_dir=policy_decision_dir)


def test_contract_constants() -> None:
    assert CONTRACT_NAME == "ai_promotion_assessment_v1"
    assert CONTRACT_VERSION == "v1"
    assert EVIDENCE_LEVEL == "LEVEL_3"
    assert AUTHORITY_LEVEL == "NON_AUTHORITIZING_EVIDENCE_ONLY"
    assert ARTIFACT_REL == "ai_promotion_assessment_v1.json"
    assert DETERMINISTIC_RULE_SET_VERSION == "ai_promotion_assessment_rules_v1"


def test_happy_path_supports_decision(tmp_path, ssot_durable_output_dir) -> None:
    fixture = produce_ai_promotion_assessment_fixture(tmp_path, ssot_durable_output_dir)
    assert fixture.ai_promotion_assessment_bundle_dir is not None
    payload = read_manifest(fixture.ai_promotion_assessment_bundle_dir / ARTIFACT_REL)
    assert payload["assessment_result"] == "SUPPORTS_DECISION"
    assert payload["assessment_confidence_class"] == "HIGH"
    assert payload["ai_promotion_assessment_complete"] is True
    assert payload["policy_decision_bound"] is True
    assert payload["promotion_policy_input_evidence_bound"] is True
    assert payload["cross_domain_lineage_bound"] is True
    assert payload["external_model_called"] is False
    assert payload["network_side_effect_created"] is False
    assert payload["nondeterministic_inference_used"] is False
    assert payload["policy_decision_overridden"] is False
    assert payload["promotion_authorized"] is False
    assert payload["promotion_decision_created"] is False


def test_required_non_authorizing_flags(tmp_path, ssot_durable_output_dir) -> None:
    fixture = produce_ai_promotion_assessment_fixture(tmp_path, ssot_durable_output_dir)
    payload = read_manifest(fixture.ai_promotion_assessment_bundle_dir / ARTIFACT_REL)
    assert payload["assessment_does_not_override_policy_decision"] is True
    assert payload["configpatch_created"] is False
    assert payload["candidate_selected"] is False
    assert payload["live_authorized"] is False
    assert payload["orders_allowed"] is False
    assert payload["runtime_authorized"] is False
    assert payload["scheduler_runtime_allowed"] is False
    assert payload["promotion_consumers_changed"] is False
    assert (
        payload["assessment_authority_invariants"] == AI_PROMOTION_ASSESSMENT_AUTHORITY_INVARIANTS
    )


def test_determinism(tmp_path, ssot_durable_output_dir) -> None:
    decision = produce_policy_decision_fixture(tmp_path, ssot_durable_output_dir)
    assert decision.promotion_policy_decision_bundle_dir is not None
    out_a = _durable_output(tmp_path, "a")
    out_b = _durable_output(tmp_path, "b")
    inputs = _inputs(decision.promotion_policy_decision_bundle_dir)
    produce_ai_promotion_assessment_v1(inputs=inputs, output_dir=out_a)
    produce_ai_promotion_assessment_v1(inputs=inputs, output_dir=out_b)
    assert (out_a / ARTIFACT_REL).read_text() == (out_b / ARTIFACT_REL).read_text()


def test_self_verification_and_manifest(tmp_path, ssot_durable_output_dir) -> None:
    fixture = produce_ai_promotion_assessment_fixture(tmp_path, ssot_durable_output_dir)
    out = fixture.ai_promotion_assessment_bundle_dir
    assert out is not None
    ok, msg = verify_manifest_sha256(out)
    assert ok, msg
    self_payload = read_manifest(out / SELF_VERIFICATION_REL)
    assert self_payload["overall_status"] == "PASS"
    reverify_ai_promotion_assessment_v1(output_dir=out)


def test_missing_policy_decision_bundle(tmp_path) -> None:
    with pytest.raises(AiPromotionAssessmentError):
        verify_policy_decision_bundle(tmp_path / "missing")


def test_invalid_policy_decision_manifest(tmp_path, ssot_durable_output_dir) -> None:
    decision = produce_policy_decision_fixture(tmp_path, ssot_durable_output_dir)
    assert decision.promotion_policy_decision_bundle_dir is not None
    decision_dir = decision.promotion_policy_decision_bundle_dir
    (decision_dir / "MANIFEST.sha256").write_text("invalid", encoding="utf-8")
    with pytest.raises(AiPromotionAssessmentError):
        verify_policy_decision_bundle(decision_dir)


def test_policy_decision_self_verification_manipulation(tmp_path, ssot_durable_output_dir) -> None:
    decision = produce_policy_decision_fixture(tmp_path, ssot_durable_output_dir)
    assert decision.promotion_policy_decision_bundle_dir is not None
    decision_dir = decision.promotion_policy_decision_bundle_dir
    self_path = decision_dir / "SELF_VERIFICATION.json"
    payload = read_manifest(self_path)
    payload["overall_status"] = "FAIL"
    self_path.write_text(deterministic_json_dumps(payload), encoding="utf-8")
    with pytest.raises(AiPromotionAssessmentError):
        verify_policy_decision_bundle(decision_dir)


def test_policy_decision_contract_version_mismatch(tmp_path, ssot_durable_output_dir) -> None:
    decision = produce_policy_decision_fixture(tmp_path, ssot_durable_output_dir)
    assert decision.promotion_policy_decision_bundle_dir is not None
    artifact_path = decision.promotion_policy_decision_bundle_dir / POLICY_DECISION_ARTIFACT_REL
    payload = read_manifest(artifact_path)
    payload["contract_version"] = "v99"
    artifact_path.write_text(deterministic_json_dumps(payload), encoding="utf-8")
    with pytest.raises(AiPromotionAssessmentError):
        verify_policy_decision_bundle(decision.promotion_policy_decision_bundle_dir)


def test_policy_decision_digest_mismatch_on_reverify(tmp_path, ssot_durable_output_dir) -> None:
    fixture = produce_ai_promotion_assessment_fixture(tmp_path, ssot_durable_output_dir)
    out = fixture.ai_promotion_assessment_bundle_dir
    assert out is not None
    artifact = read_manifest(out / ARTIFACT_REL)
    artifact["policy_decision_digest"] = "0" * 64
    (out / ARTIFACT_REL).write_text(deterministic_json_dumps(artifact), encoding="utf-8")
    with pytest.raises(AiPromotionAssessmentError):
        reverify_ai_promotion_assessment_v1(output_dir=out)


def test_upstream_reject_supports_decision(tmp_path, ssot_durable_output_dir) -> None:
    decision = produce_policy_decision_fixture(tmp_path, ssot_durable_output_dir)
    assert decision.promotion_policy_decision_bundle_dir is not None
    bundle = verify_policy_decision_bundle(decision.promotion_policy_decision_bundle_dir)
    tampered = dict(bundle.decision_payload)
    tampered["decision_status"] = "FAIL"
    tampered["decision_outcome"] = "REJECT"
    tampered_bundle = VerifiedPolicyDecisionBundle(
        bundle_dir=bundle.bundle_dir,
        contract_name=bundle.contract_name,
        contract_version=bundle.contract_version,
        producer_version=bundle.producer_version,
        artifact_ref=bundle.artifact_ref,
        artifact_digest=bundle.artifact_digest,
        manifest_digest=bundle.manifest_digest,
        decision_payload=tampered,
    )
    payload = build_ai_promotion_assessment_v1(policy_decision=tampered_bundle)
    assert payload["assessment_result"] == "SUPPORTS_DECISION"
    assert payload["assessment_confidence_class"] == "MEDIUM"


def test_upstream_defer_abstains(tmp_path, ssot_durable_output_dir) -> None:
    decision = produce_policy_decision_fixture(tmp_path, ssot_durable_output_dir)
    assert decision.promotion_policy_decision_bundle_dir is not None
    bundle = verify_policy_decision_bundle(decision.promotion_policy_decision_bundle_dir)
    tampered = dict(bundle.decision_payload)
    tampered["decision_status"] = "INCOMPLETE"
    tampered["decision_outcome"] = "DEFER_INSUFFICIENT_EVIDENCE"
    tampered_bundle = VerifiedPolicyDecisionBundle(
        bundle_dir=bundle.bundle_dir,
        contract_name=bundle.contract_name,
        contract_version=bundle.contract_version,
        producer_version=bundle.producer_version,
        artifact_ref=bundle.artifact_ref,
        artifact_digest=bundle.artifact_digest,
        manifest_digest=bundle.manifest_digest,
        decision_payload=tampered,
    )
    payload = build_ai_promotion_assessment_v1(policy_decision=tampered_bundle)
    assert payload["assessment_result"] == "ABSTAINS"
    assert payload["ai_promotion_assessment_complete"] is False


def test_contradiction_abstains(tmp_path, ssot_durable_output_dir) -> None:
    decision = produce_policy_decision_fixture(tmp_path, ssot_durable_output_dir)
    assert decision.promotion_policy_decision_bundle_dir is not None
    bundle = verify_policy_decision_bundle(decision.promotion_policy_decision_bundle_dir)
    tampered = dict(bundle.decision_payload)
    tampered["decision_status"] = "PASS"
    tampered["decision_outcome"] = "APPROVE"
    tampered["policy_input_evidence_bound_status"] = "NOT_BOUND"
    tampered_bundle = VerifiedPolicyDecisionBundle(
        bundle_dir=bundle.bundle_dir,
        contract_name=bundle.contract_name,
        contract_version=bundle.contract_version,
        producer_version=bundle.producer_version,
        artifact_ref=bundle.artifact_ref,
        artifact_digest=bundle.artifact_digest,
        manifest_digest=bundle.manifest_digest,
        decision_payload=tampered,
    )
    payload = build_ai_promotion_assessment_v1(policy_decision=tampered_bundle)
    assert payload["assessment_result"] == "ABSTAINS"
    assert payload["contradictions"]


def test_promotion_authorized_in_decision_abstains(tmp_path, ssot_durable_output_dir) -> None:
    decision = produce_policy_decision_fixture(tmp_path, ssot_durable_output_dir)
    assert decision.promotion_policy_decision_bundle_dir is not None
    bundle = verify_policy_decision_bundle(decision.promotion_policy_decision_bundle_dir)
    tampered = dict(bundle.decision_payload)
    tampered["promotion_authorized"] = True
    tampered_bundle = VerifiedPolicyDecisionBundle(
        bundle_dir=bundle.bundle_dir,
        contract_name=bundle.contract_name,
        contract_version=bundle.contract_version,
        producer_version=bundle.producer_version,
        artifact_ref=bundle.artifact_ref,
        artifact_digest=bundle.artifact_digest,
        manifest_digest=bundle.manifest_digest,
        decision_payload=tampered,
    )
    payload = build_ai_promotion_assessment_v1(policy_decision=tampered_bundle)
    assert payload["assessment_result"] == "ABSTAINS"


def test_runtime_authorized_flag_rejected_on_serialize(tmp_path, ssot_durable_output_dir) -> None:
    fixture = produce_ai_promotion_assessment_fixture(tmp_path, ssot_durable_output_dir)
    payload = read_manifest(fixture.ai_promotion_assessment_bundle_dir / ARTIFACT_REL)
    payload["runtime_authorized"] = True
    with pytest.raises(AiPromotionAssessmentError):
        serialize_ai_promotion_assessment_v1(payload)


def test_promotion_authorized_flag_rejected_on_serialize(tmp_path, ssot_durable_output_dir) -> None:
    fixture = produce_ai_promotion_assessment_fixture(tmp_path, ssot_durable_output_dir)
    payload = read_manifest(fixture.ai_promotion_assessment_bundle_dir / ARTIFACT_REL)
    payload["promotion_authorized"] = True
    with pytest.raises(AiPromotionAssessmentError):
        serialize_ai_promotion_assessment_v1(payload)


def test_external_model_called_rejected_on_serialize(tmp_path, ssot_durable_output_dir) -> None:
    fixture = produce_ai_promotion_assessment_fixture(tmp_path, ssot_durable_output_dir)
    payload = read_manifest(fixture.ai_promotion_assessment_bundle_dir / ARTIFACT_REL)
    payload["external_model_called"] = True
    with pytest.raises(AiPromotionAssessmentError):
        serialize_ai_promotion_assessment_v1(payload)


def test_network_side_effect_rejected_on_serialize(tmp_path, ssot_durable_output_dir) -> None:
    fixture = produce_ai_promotion_assessment_fixture(tmp_path, ssot_durable_output_dir)
    payload = read_manifest(fixture.ai_promotion_assessment_bundle_dir / ARTIFACT_REL)
    payload["network_side_effect_created"] = True
    with pytest.raises(AiPromotionAssessmentError):
        serialize_ai_promotion_assessment_v1(payload)


def test_nondeterministic_inference_rejected_on_serialize(
    tmp_path, ssot_durable_output_dir
) -> None:
    fixture = produce_ai_promotion_assessment_fixture(tmp_path, ssot_durable_output_dir)
    payload = read_manifest(fixture.ai_promotion_assessment_bundle_dir / ARTIFACT_REL)
    payload["nondeterministic_inference_used"] = True
    with pytest.raises(AiPromotionAssessmentError):
        serialize_ai_promotion_assessment_v1(payload)


def test_policy_decision_overridden_rejected_on_serialize(
    tmp_path, ssot_durable_output_dir
) -> None:
    fixture = produce_ai_promotion_assessment_fixture(tmp_path, ssot_durable_output_dir)
    payload = read_manifest(fixture.ai_promotion_assessment_bundle_dir / ARTIFACT_REL)
    payload["policy_decision_overridden"] = True
    with pytest.raises(AiPromotionAssessmentError):
        serialize_ai_promotion_assessment_v1(payload)


def test_configpatch_created_rejected_on_serialize(tmp_path, ssot_durable_output_dir) -> None:
    fixture = produce_ai_promotion_assessment_fixture(tmp_path, ssot_durable_output_dir)
    payload = read_manifest(fixture.ai_promotion_assessment_bundle_dir / ARTIFACT_REL)
    payload["configpatch_created"] = True
    with pytest.raises(AiPromotionAssessmentError):
        serialize_ai_promotion_assessment_v1(payload)


def test_candidate_selected_rejected_on_serialize(tmp_path, ssot_durable_output_dir) -> None:
    fixture = produce_ai_promotion_assessment_fixture(tmp_path, ssot_durable_output_dir)
    payload = read_manifest(fixture.ai_promotion_assessment_bundle_dir / ARTIFACT_REL)
    payload["candidate_selected"] = True
    with pytest.raises(AiPromotionAssessmentError):
        serialize_ai_promotion_assessment_v1(payload)


def test_promotion_candidate_constructed_rejected_on_serialize(
    tmp_path, ssot_durable_output_dir
) -> None:
    fixture = produce_ai_promotion_assessment_fixture(tmp_path, ssot_durable_output_dir)
    payload = read_manifest(fixture.ai_promotion_assessment_bundle_dir / ARTIFACT_REL)
    payload["promotion_candidate_constructed"] = True
    with pytest.raises(AiPromotionAssessmentError):
        serialize_ai_promotion_assessment_v1(payload)


def test_safety_flags_mutated_rejected_on_serialize(tmp_path, ssot_durable_output_dir) -> None:
    fixture = produce_ai_promotion_assessment_fixture(tmp_path, ssot_durable_output_dir)
    payload = read_manifest(fixture.ai_promotion_assessment_bundle_dir / ARTIFACT_REL)
    payload["safety_flags_mutated"] = True
    with pytest.raises(AiPromotionAssessmentError):
        serialize_ai_promotion_assessment_v1(payload)


def test_promotion_consumers_changed_rejected_on_serialize(
    tmp_path, ssot_durable_output_dir
) -> None:
    fixture = produce_ai_promotion_assessment_fixture(tmp_path, ssot_durable_output_dir)
    payload = read_manifest(fixture.ai_promotion_assessment_bundle_dir / ARTIFACT_REL)
    payload["promotion_consumers_changed"] = True
    with pytest.raises(AiPromotionAssessmentError):
        serialize_ai_promotion_assessment_v1(payload)


def test_live_authorized_rejected_on_serialize(tmp_path, ssot_durable_output_dir) -> None:
    fixture = produce_ai_promotion_assessment_fixture(tmp_path, ssot_durable_output_dir)
    payload = read_manifest(fixture.ai_promotion_assessment_bundle_dir / ARTIFACT_REL)
    payload["live_authorized"] = True
    with pytest.raises(AiPromotionAssessmentError):
        serialize_ai_promotion_assessment_v1(payload)


def test_orders_allowed_rejected_on_serialize(tmp_path, ssot_durable_output_dir) -> None:
    fixture = produce_ai_promotion_assessment_fixture(tmp_path, ssot_durable_output_dir)
    payload = read_manifest(fixture.ai_promotion_assessment_bundle_dir / ARTIFACT_REL)
    payload["orders_allowed"] = True
    with pytest.raises(AiPromotionAssessmentError):
        serialize_ai_promotion_assessment_v1(payload)


def test_scheduler_runtime_allowed_rejected_on_serialize(tmp_path, ssot_durable_output_dir) -> None:
    fixture = produce_ai_promotion_assessment_fixture(tmp_path, ssot_durable_output_dir)
    payload = read_manifest(fixture.ai_promotion_assessment_bundle_dir / ARTIFACT_REL)
    payload["scheduler_runtime_allowed"] = True
    with pytest.raises(AiPromotionAssessmentError):
        serialize_ai_promotion_assessment_v1(payload)


def test_unknown_assessment_result_rejected_on_serialize(tmp_path, ssot_durable_output_dir) -> None:
    fixture = produce_ai_promotion_assessment_fixture(tmp_path, ssot_durable_output_dir)
    payload = read_manifest(fixture.ai_promotion_assessment_bundle_dir / ARTIFACT_REL)
    payload["assessment_result"] = "FREE_TEXT_DECISION"
    with pytest.raises(AiPromotionAssessmentError):
        serialize_ai_promotion_assessment_v1(payload)


def test_manipulated_rule_set_version_rejected_on_serialize(
    tmp_path, ssot_durable_output_dir
) -> None:
    fixture = produce_ai_promotion_assessment_fixture(tmp_path, ssot_durable_output_dir)
    payload = read_manifest(fixture.ai_promotion_assessment_bundle_dir / ARTIFACT_REL)
    payload["deterministic_rule_set_version"] = "tampered_rules_v99"
    with pytest.raises(AiPromotionAssessmentError):
        serialize_ai_promotion_assessment_v1(payload)


def test_forbidden_key_rejected_on_serialize(tmp_path, ssot_durable_output_dir) -> None:
    fixture = produce_ai_promotion_assessment_fixture(tmp_path, ssot_durable_output_dir)
    payload = read_manifest(fixture.ai_promotion_assessment_bundle_dir / ARTIFACT_REL)
    payload["promotion"] = True
    with pytest.raises(AiPromotionAssessmentError):
        serialize_ai_promotion_assessment_v1(payload)


def test_input_artifact_refs_exactly_one(tmp_path, ssot_durable_output_dir) -> None:
    fixture = produce_ai_promotion_assessment_fixture(tmp_path, ssot_durable_output_dir)
    payload = read_manifest(fixture.ai_promotion_assessment_bundle_dir / ARTIFACT_REL)
    assert len(payload["input_artifact_refs"]) == 1


def test_reason_codes_sorted(tmp_path, ssot_durable_output_dir) -> None:
    fixture = produce_ai_promotion_assessment_fixture(tmp_path, ssot_durable_output_dir)
    payload = read_manifest(fixture.ai_promotion_assessment_bundle_dir / ARTIFACT_REL)
    codes = payload["assessment_reason_codes"]
    assert codes == sorted(codes)


def test_output_existing_dir_fail(tmp_path, ssot_durable_output_dir) -> None:
    decision = produce_policy_decision_fixture(tmp_path, ssot_durable_output_dir)
    assert decision.promotion_policy_decision_bundle_dir is not None
    out = _durable_output(tmp_path)
    out.mkdir()
    with pytest.raises(AiPromotionAssessmentError):
        produce_ai_promotion_assessment_v1(
            inputs=_inputs(decision.promotion_policy_decision_bundle_dir),
            output_dir=out,
        )


def test_reverify_after_tamper(tmp_path, ssot_durable_output_dir) -> None:
    fixture = produce_ai_promotion_assessment_fixture(tmp_path, ssot_durable_output_dir)
    out = fixture.ai_promotion_assessment_bundle_dir
    assert out is not None
    artifact = read_manifest(out / ARTIFACT_REL)
    artifact["candidate_identity_ref"] = "tampered"
    (out / ARTIFACT_REL).write_text(deterministic_json_dumps(artifact), encoding="utf-8")
    with pytest.raises(AiPromotionAssessmentError):
        reverify_ai_promotion_assessment_v1(output_dir=out)


def test_no_forbidden_runtime_imports() -> None:
    module_path = Path("src/meta/learning_loop/ai_promotion_assessment_v1.py")
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


def test_transitive_refs_present(tmp_path, ssot_durable_output_dir) -> None:
    fixture = produce_ai_promotion_assessment_fixture(tmp_path, ssot_durable_output_dir)
    payload = read_manifest(fixture.ai_promotion_assessment_bundle_dir / ARTIFACT_REL)
    assert payload["eligibility_evidence_ref"]
    assert payload["eligibility_evidence_digest"]
    assert payload["policy_input_binding_bundle_ref"]
    assert payload["model_identity_ref"]
    assert payload["parameter_set_identity_ref"]
    assert payload["policy_decision_digest"]
    assert payload["policy_decision_ref"]


def test_verify_assessment_inputs(tmp_path, ssot_durable_output_dir) -> None:
    decision = produce_policy_decision_fixture(tmp_path, ssot_durable_output_dir)
    assert decision.promotion_policy_decision_bundle_dir is not None
    bundle = verify_assessment_inputs(_inputs(decision.promotion_policy_decision_bundle_dir))
    assert isinstance(bundle, VerifiedPolicyDecisionBundle)


def test_copy_inputs_no_mutation(tmp_path, ssot_durable_output_dir) -> None:
    decision = produce_policy_decision_fixture(tmp_path, ssot_durable_output_dir)
    assert decision.promotion_policy_decision_bundle_dir is not None
    before = (
        decision.promotion_policy_decision_bundle_dir / POLICY_DECISION_ARTIFACT_REL
    ).read_bytes()
    out = _durable_output(tmp_path)
    produce_ai_promotion_assessment_v1(
        inputs=_inputs(decision.promotion_policy_decision_bundle_dir),
        output_dir=out,
    )
    assert (
        decision.promotion_policy_decision_bundle_dir / POLICY_DECISION_ARTIFACT_REL
    ).read_bytes() == before


def test_producer_version_constant() -> None:
    assert PRODUCER_VERSION == "ai_promotion_assessment_v1"


def test_manifest_files_present(tmp_path, ssot_durable_output_dir) -> None:
    fixture = produce_ai_promotion_assessment_fixture(tmp_path, ssot_durable_output_dir)
    out = fixture.ai_promotion_assessment_bundle_dir
    assert out is not None
    assert (out / ARTIFACT_REL).is_file()
    assert (out / SELF_VERIFICATION_REL).is_file()
    assert (out / MANIFEST_FILENAME).is_file()


def test_assessment_id_equals_output_digest(tmp_path, ssot_durable_output_dir) -> None:
    fixture = produce_ai_promotion_assessment_fixture(tmp_path, ssot_durable_output_dir)
    payload = read_manifest(fixture.ai_promotion_assessment_bundle_dir / ARTIFACT_REL)
    assert payload["assessment_id"] == payload["output_digest"]
    assert payload["artifact_id"] == payload["output_digest"]
