"""Contract tests for comparison promotion candidate input v1."""

from __future__ import annotations

import ast
import json
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
]

from scripts.ops.primary_evidence_retention_v0 import verify_manifest_sha256
from src.meta.learning_loop.comparison_config_patch_manifest_cross_domain_lineage_binding_v1 import (
    ARTIFACT_REL as STEP2_ARTIFACT_REL,
)
from src.meta.learning_loop.comparison_promotion_candidate_input_v1 import (
    ARTIFACT_REL,
    AUTHORITY_LEVEL,
    CANDIDATE_INPUT_AUTHORITY_INVARIANTS,
    CONTRACT_NAME,
    CONTRACT_VERSION,
    EVIDENCE_LEVEL,
    MANIFEST_FILENAME,
    PRODUCER_VERSION,
    SELF_VERIFICATION_REL,
    ComparisonPromotionCandidateInputError,
    ComparisonPromotionCandidateInputInputs,
    VerifiedCrossDomainLineageBindingBundle,
    build_comparison_promotion_candidate_input_v1,
    produce_comparison_promotion_candidate_input_v1,
    reverify_comparison_promotion_candidate_input_v1,
    serialize_comparison_promotion_candidate_input_v1,
    verify_binding_inputs,
    verify_cross_domain_lineage_binding_bundle,
)
from src.meta.learning_loop.comparison_ssot_v1.io import read_manifest
from src.meta.learning_loop.contract_safety_v1 import deterministic_json_dumps
from tests.meta.comparison_config_patch_manifest_cross_domain_lineage_binding_v1_fixtures import (
    produce_cross_domain_lineage_binding_fixture,
)
from tests.meta.comparison_promotion_candidate_input_v1_fixtures import (
    produce_candidate_input_fixture,
)


@pytest.fixture(autouse=True)
def _allow_tmp_output(monkeypatch: pytest.MonkeyPatch) -> None:
    targets = (
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


def _durable_output(tmp_path: Path, name: str = "candidate_input_out") -> Path:
    root = tmp_path / "evidence_root"
    root.mkdir(exist_ok=True)
    return root / name


def _inputs(step2_dir: Path) -> ComparisonPromotionCandidateInputInputs:
    return ComparisonPromotionCandidateInputInputs(
        cross_domain_lineage_binding_bundle_dir=step2_dir,
    )


def test_contract_constants() -> None:
    assert CONTRACT_NAME == "comparison_promotion_candidate_input_v1"
    assert CONTRACT_VERSION == "v1"
    assert EVIDENCE_LEVEL == "LEVEL_3"
    assert AUTHORITY_LEVEL == "NON_AUTHORITIZING_EVIDENCE_ONLY"
    assert ARTIFACT_REL == "comparison_promotion_candidate_input_v1.json"


def test_happy_path_pass(tmp_path, ssot_durable_output_dir) -> None:
    fixture = produce_candidate_input_fixture(tmp_path, ssot_durable_output_dir)
    assert fixture.candidate_input_bundle_dir is not None
    payload = read_manifest(fixture.candidate_input_bundle_dir / ARTIFACT_REL)
    assert payload["candidate_input_status"] == "PASS"
    assert payload["candidate_identity_status"] == "BOUND"
    assert payload["model_identity_status"] == "BOUND"
    assert payload["parameter_set_identity_status"] == "BOUND"
    assert payload["config_patch_manifest_identity_status"] == "BOUND"
    assert payload["eligibility_evidence_status"] == "VERIFIED"
    assert payload["cross_domain_lineage_status"] == "BOUND"
    assert payload["candidate_selection_status"] == "NOT_SELECTED"
    assert payload["winner_selection_status"] == "NOT_SELECTED"
    assert payload["candidate_acceptance_status"] == "NOT_ACCEPTED"
    assert payload["config_patch_acceptance_status"] == "NOT_ACCEPTED"
    assert payload["promotion_candidate_constructed"] is False
    assert payload["configpatch_created"] is False
    assert payload["configpatch_modified"] is False
    assert payload["configpatch_applied"] is False
    assert (
        "COMPARISON_PROMOTION_CANDIDATE_INPUT_COMPLETE" in payload["candidate_input_reason_codes"]
    )


def test_required_non_authorizing_flags(tmp_path, ssot_durable_output_dir) -> None:
    fixture = produce_candidate_input_fixture(tmp_path, ssot_durable_output_dir)
    payload = read_manifest(fixture.candidate_input_bundle_dir / ARTIFACT_REL)
    assert payload["candidate_input_does_not_select"] is True
    assert payload["candidate_input_does_not_accept_configpatch"] is True
    assert payload["candidate_input_does_not_create_configpatch"] is True
    assert payload["candidate_input_does_not_construct_promotion_candidate"] is True
    assert payload["candidate_input_does_not_execute_policy"] is True
    assert payload["candidate_input_authority_invariants"] == CANDIDATE_INPUT_AUTHORITY_INVARIANTS


def test_determinism(tmp_path, ssot_durable_output_dir) -> None:
    cross_domain = produce_cross_domain_lineage_binding_fixture(tmp_path, ssot_durable_output_dir)
    assert cross_domain.cross_domain_binding_bundle_dir is not None
    out_a = _durable_output(tmp_path, "a")
    out_b = _durable_output(tmp_path, "b")
    inputs = _inputs(cross_domain.cross_domain_binding_bundle_dir)
    produce_comparison_promotion_candidate_input_v1(inputs=inputs, output_dir=out_a)
    produce_comparison_promotion_candidate_input_v1(inputs=inputs, output_dir=out_b)
    assert (out_a / ARTIFACT_REL).read_text() == (out_b / ARTIFACT_REL).read_text()


def test_self_verification_and_manifest(tmp_path, ssot_durable_output_dir) -> None:
    fixture = produce_candidate_input_fixture(tmp_path, ssot_durable_output_dir)
    out = fixture.candidate_input_bundle_dir
    assert out is not None
    ok, msg = verify_manifest_sha256(out)
    assert ok, msg
    self_payload = read_manifest(out / SELF_VERIFICATION_REL)
    assert self_payload["overall_status"] == "PASS"
    reverify_comparison_promotion_candidate_input_v1(output_dir=out)


def test_missing_step2_bundle(tmp_path) -> None:
    with pytest.raises(ComparisonPromotionCandidateInputError):
        verify_cross_domain_lineage_binding_bundle(tmp_path / "missing")


def test_invalid_step2_manifest(tmp_path, ssot_durable_output_dir) -> None:
    cross_domain = produce_cross_domain_lineage_binding_fixture(tmp_path, ssot_durable_output_dir)
    assert cross_domain.cross_domain_binding_bundle_dir is not None
    step2_dir = cross_domain.cross_domain_binding_bundle_dir
    (step2_dir / "MANIFEST.sha256").write_text("invalid", encoding="utf-8")
    with pytest.raises(ComparisonPromotionCandidateInputError):
        verify_cross_domain_lineage_binding_bundle(step2_dir)


def test_step2_self_verification_manipulation(tmp_path, ssot_durable_output_dir) -> None:
    cross_domain = produce_cross_domain_lineage_binding_fixture(tmp_path, ssot_durable_output_dir)
    assert cross_domain.cross_domain_binding_bundle_dir is not None
    step2_dir = cross_domain.cross_domain_binding_bundle_dir
    self_path = step2_dir / "SELF_VERIFICATION.json"
    payload = read_manifest(self_path)
    payload["overall_status"] = "FAIL"
    self_path.write_text(deterministic_json_dumps(payload), encoding="utf-8")
    with pytest.raises(ComparisonPromotionCandidateInputError):
        verify_cross_domain_lineage_binding_bundle(step2_dir)


def test_candidate_digest_manipulation_fail(tmp_path, ssot_durable_output_dir) -> None:
    cross_domain = produce_cross_domain_lineage_binding_fixture(tmp_path, ssot_durable_output_dir)
    assert cross_domain.cross_domain_binding_bundle_dir is not None
    step2 = verify_cross_domain_lineage_binding_bundle(cross_domain.cross_domain_binding_bundle_dir)
    tampered = dict(step2.evidence_payload)
    tampered["candidate_identity_digest"] = "0" * 64
    tampered_bundle = VerifiedCrossDomainLineageBindingBundle(
        bundle_dir=step2.bundle_dir,
        contract_name=step2.contract_name,
        contract_version=step2.contract_version,
        producer_version=step2.producer_version,
        artifact_ref=step2.artifact_ref,
        artifact_digest=step2.artifact_digest,
        manifest_digest=step2.manifest_digest,
        evidence_payload=tampered,
    )
    payload = build_comparison_promotion_candidate_input_v1(cross_domain_binding=tampered_bundle)
    assert payload["candidate_input_status"] == "FAIL"
    assert "CANDIDATE_DIGEST_MISMATCH" in payload["candidate_input_reason_codes"]


def test_model_digest_manipulation_fail(tmp_path, ssot_durable_output_dir) -> None:
    cross_domain = produce_cross_domain_lineage_binding_fixture(tmp_path, ssot_durable_output_dir)
    assert cross_domain.cross_domain_binding_bundle_dir is not None
    step2 = verify_cross_domain_lineage_binding_bundle(cross_domain.cross_domain_binding_bundle_dir)
    tampered = dict(step2.evidence_payload)
    tampered["model_identity_digest"] = "0" * 64
    tampered_bundle = VerifiedCrossDomainLineageBindingBundle(
        bundle_dir=step2.bundle_dir,
        contract_name=step2.contract_name,
        contract_version=step2.contract_version,
        producer_version=step2.producer_version,
        artifact_ref=step2.artifact_ref,
        artifact_digest=step2.artifact_digest,
        manifest_digest=step2.manifest_digest,
        evidence_payload=tampered,
    )
    payload = build_comparison_promotion_candidate_input_v1(cross_domain_binding=tampered_bundle)
    assert payload["candidate_input_status"] == "FAIL"
    assert "MODEL_DIGEST_MISMATCH" in payload["candidate_input_reason_codes"]


def test_parameter_set_digest_manipulation_fail(tmp_path, ssot_durable_output_dir) -> None:
    cross_domain = produce_cross_domain_lineage_binding_fixture(tmp_path, ssot_durable_output_dir)
    assert cross_domain.cross_domain_binding_bundle_dir is not None
    step2 = verify_cross_domain_lineage_binding_bundle(cross_domain.cross_domain_binding_bundle_dir)
    tampered = dict(step2.evidence_payload)
    tampered["parameter_set_identity_digest"] = "0" * 64
    tampered_bundle = VerifiedCrossDomainLineageBindingBundle(
        bundle_dir=step2.bundle_dir,
        contract_name=step2.contract_name,
        contract_version=step2.contract_version,
        producer_version=step2.producer_version,
        artifact_ref=step2.artifact_ref,
        artifact_digest=step2.artifact_digest,
        manifest_digest=step2.manifest_digest,
        evidence_payload=tampered,
    )
    payload = build_comparison_promotion_candidate_input_v1(cross_domain_binding=tampered_bundle)
    assert payload["candidate_input_status"] == "FAIL"
    assert "PARAMETER_SET_DIGEST_MISMATCH" in payload["candidate_input_reason_codes"]


def test_config_patch_manifest_digest_manipulation_fail(tmp_path, ssot_durable_output_dir) -> None:
    cross_domain = produce_cross_domain_lineage_binding_fixture(tmp_path, ssot_durable_output_dir)
    assert cross_domain.cross_domain_binding_bundle_dir is not None
    step2 = verify_cross_domain_lineage_binding_bundle(cross_domain.cross_domain_binding_bundle_dir)
    tampered = dict(step2.evidence_payload)
    tampered["config_patch_manifest_digest"] = "0" * 64
    tampered_bundle = VerifiedCrossDomainLineageBindingBundle(
        bundle_dir=step2.bundle_dir,
        contract_name=step2.contract_name,
        contract_version=step2.contract_version,
        producer_version=step2.producer_version,
        artifact_ref=step2.artifact_ref,
        artifact_digest=step2.artifact_digest,
        manifest_digest=step2.manifest_digest,
        evidence_payload=tampered,
    )
    payload = build_comparison_promotion_candidate_input_v1(cross_domain_binding=tampered_bundle)
    assert payload["candidate_input_status"] == "FAIL"
    assert "CONFIG_PATCH_MANIFEST_DIGEST_MISMATCH" in payload["candidate_input_reason_codes"]


def test_upstream_incomplete_propagation(tmp_path, ssot_durable_output_dir) -> None:
    cross_domain = produce_cross_domain_lineage_binding_fixture(
        tmp_path,
        ssot_durable_output_dir,
        all_domains_pass=False,
    )
    assert cross_domain.cross_domain_binding_bundle_dir is not None
    step2 = verify_cross_domain_lineage_binding_bundle(cross_domain.cross_domain_binding_bundle_dir)
    payload = build_comparison_promotion_candidate_input_v1(cross_domain_binding=step2)
    assert payload["candidate_input_status"] in {"INCOMPLETE", "FAIL", "NOT_EVALUABLE"}


def test_upstream_fail_propagation(tmp_path, ssot_durable_output_dir) -> None:
    cross_domain = produce_cross_domain_lineage_binding_fixture(tmp_path, ssot_durable_output_dir)
    assert cross_domain.cross_domain_binding_bundle_dir is not None
    step2 = verify_cross_domain_lineage_binding_bundle(cross_domain.cross_domain_binding_bundle_dir)
    tampered = dict(step2.evidence_payload)
    tampered["cross_domain_lineage_binding_status"] = "FAIL"
    tampered_bundle = VerifiedCrossDomainLineageBindingBundle(
        bundle_dir=step2.bundle_dir,
        contract_name=step2.contract_name,
        contract_version=step2.contract_version,
        producer_version=step2.producer_version,
        artifact_ref=step2.artifact_ref,
        artifact_digest=step2.artifact_digest,
        manifest_digest=step2.manifest_digest,
        evidence_payload=tampered,
    )
    payload = build_comparison_promotion_candidate_input_v1(cross_domain_binding=tampered_bundle)
    assert payload["candidate_input_status"] == "FAIL"
    assert "UPSTREAM_CROSS_DOMAIN_LINEAGE_FAIL" in payload["candidate_input_reason_codes"]


def test_candidate_selection_detected_fail(tmp_path, ssot_durable_output_dir) -> None:
    cross_domain = produce_cross_domain_lineage_binding_fixture(tmp_path, ssot_durable_output_dir)
    assert cross_domain.cross_domain_binding_bundle_dir is not None
    step2 = verify_cross_domain_lineage_binding_bundle(cross_domain.cross_domain_binding_bundle_dir)
    tampered = dict(step2.evidence_payload)
    tampered["candidate_selection_status"] = "SELECTED"
    tampered_bundle = VerifiedCrossDomainLineageBindingBundle(
        bundle_dir=step2.bundle_dir,
        contract_name=step2.contract_name,
        contract_version=step2.contract_version,
        producer_version=step2.producer_version,
        artifact_ref=step2.artifact_ref,
        artifact_digest=step2.artifact_digest,
        manifest_digest=step2.manifest_digest,
        evidence_payload=tampered,
    )
    payload = build_comparison_promotion_candidate_input_v1(cross_domain_binding=tampered_bundle)
    assert payload["candidate_input_status"] == "FAIL"
    assert "CANDIDATE_SELECTION_DETECTED" in payload["candidate_input_reason_codes"]


def test_winner_selection_detected_fail(tmp_path, ssot_durable_output_dir) -> None:
    cross_domain = produce_cross_domain_lineage_binding_fixture(tmp_path, ssot_durable_output_dir)
    assert cross_domain.cross_domain_binding_bundle_dir is not None
    step2 = verify_cross_domain_lineage_binding_bundle(cross_domain.cross_domain_binding_bundle_dir)
    tampered = dict(step2.evidence_payload)
    tampered["winner_selection_status"] = "WINNER"
    tampered_bundle = VerifiedCrossDomainLineageBindingBundle(
        bundle_dir=step2.bundle_dir,
        contract_name=step2.contract_name,
        contract_version=step2.contract_version,
        producer_version=step2.producer_version,
        artifact_ref=step2.artifact_ref,
        artifact_digest=step2.artifact_digest,
        manifest_digest=step2.manifest_digest,
        evidence_payload=tampered,
    )
    payload = build_comparison_promotion_candidate_input_v1(cross_domain_binding=tampered_bundle)
    assert payload["candidate_input_status"] == "FAIL"
    assert "WINNER_SELECTION_DETECTED" in payload["candidate_input_reason_codes"]


def test_candidate_acceptance_detected_fail(tmp_path, ssot_durable_output_dir) -> None:
    cross_domain = produce_cross_domain_lineage_binding_fixture(tmp_path, ssot_durable_output_dir)
    assert cross_domain.cross_domain_binding_bundle_dir is not None
    step2 = verify_cross_domain_lineage_binding_bundle(cross_domain.cross_domain_binding_bundle_dir)
    tampered = dict(step2.evidence_payload)
    tampered["candidate_acceptance_status"] = "ACCEPTED"
    tampered_bundle = VerifiedCrossDomainLineageBindingBundle(
        bundle_dir=step2.bundle_dir,
        contract_name=step2.contract_name,
        contract_version=step2.contract_version,
        producer_version=step2.producer_version,
        artifact_ref=step2.artifact_ref,
        artifact_digest=step2.artifact_digest,
        manifest_digest=step2.manifest_digest,
        evidence_payload=tampered,
    )
    payload = build_comparison_promotion_candidate_input_v1(cross_domain_binding=tampered_bundle)
    assert payload["candidate_input_status"] == "FAIL"
    assert "CANDIDATE_ACCEPTANCE_DETECTED" in payload["candidate_input_reason_codes"]


def test_configpatch_acceptance_detected_fail(tmp_path, ssot_durable_output_dir) -> None:
    cross_domain = produce_cross_domain_lineage_binding_fixture(tmp_path, ssot_durable_output_dir)
    assert cross_domain.cross_domain_binding_bundle_dir is not None
    step2 = verify_cross_domain_lineage_binding_bundle(cross_domain.cross_domain_binding_bundle_dir)
    tampered = dict(step2.evidence_payload)
    tampered["configpatch_accepted"] = True
    tampered_bundle = VerifiedCrossDomainLineageBindingBundle(
        bundle_dir=step2.bundle_dir,
        contract_name=step2.contract_name,
        contract_version=step2.contract_version,
        producer_version=step2.producer_version,
        artifact_ref=step2.artifact_ref,
        artifact_digest=step2.artifact_digest,
        manifest_digest=step2.manifest_digest,
        evidence_payload=tampered,
    )
    payload = build_comparison_promotion_candidate_input_v1(cross_domain_binding=tampered_bundle)
    assert payload["candidate_input_status"] == "FAIL"
    assert "CONFIG_PATCH_ACCEPTANCE_DETECTED" in payload["candidate_input_reason_codes"]


def test_configpatch_creation_detected_fail(tmp_path, ssot_durable_output_dir) -> None:
    cross_domain = produce_cross_domain_lineage_binding_fixture(tmp_path, ssot_durable_output_dir)
    assert cross_domain.cross_domain_binding_bundle_dir is not None
    step2 = verify_cross_domain_lineage_binding_bundle(cross_domain.cross_domain_binding_bundle_dir)
    tampered = dict(step2.evidence_payload)
    tampered["configpatch_created"] = True
    tampered_bundle = VerifiedCrossDomainLineageBindingBundle(
        bundle_dir=step2.bundle_dir,
        contract_name=step2.contract_name,
        contract_version=step2.contract_version,
        producer_version=step2.producer_version,
        artifact_ref=step2.artifact_ref,
        artifact_digest=step2.artifact_digest,
        manifest_digest=step2.manifest_digest,
        evidence_payload=tampered,
    )
    payload = build_comparison_promotion_candidate_input_v1(cross_domain_binding=tampered_bundle)
    assert payload["candidate_input_status"] == "FAIL"
    assert "CONFIGPATCH_CREATION_DETECTED" in payload["candidate_input_reason_codes"]


def test_configpatch_mutation_detected_fail(tmp_path, ssot_durable_output_dir) -> None:
    cross_domain = produce_cross_domain_lineage_binding_fixture(tmp_path, ssot_durable_output_dir)
    assert cross_domain.cross_domain_binding_bundle_dir is not None
    step2 = verify_cross_domain_lineage_binding_bundle(cross_domain.cross_domain_binding_bundle_dir)
    tampered = dict(step2.evidence_payload)
    tampered["configpatch_modified"] = True
    tampered_bundle = VerifiedCrossDomainLineageBindingBundle(
        bundle_dir=step2.bundle_dir,
        contract_name=step2.contract_name,
        contract_version=step2.contract_version,
        producer_version=step2.producer_version,
        artifact_ref=step2.artifact_ref,
        artifact_digest=step2.artifact_digest,
        manifest_digest=step2.manifest_digest,
        evidence_payload=tampered,
    )
    payload = build_comparison_promotion_candidate_input_v1(cross_domain_binding=tampered_bundle)
    assert payload["candidate_input_status"] == "FAIL"
    assert "CONFIGPATCH_MUTATION_DETECTED" in payload["candidate_input_reason_codes"]


def test_configpatch_application_detected_fail(tmp_path, ssot_durable_output_dir) -> None:
    cross_domain = produce_cross_domain_lineage_binding_fixture(tmp_path, ssot_durable_output_dir)
    assert cross_domain.cross_domain_binding_bundle_dir is not None
    step2 = verify_cross_domain_lineage_binding_bundle(cross_domain.cross_domain_binding_bundle_dir)
    tampered = dict(step2.evidence_payload)
    tampered["configpatch_applied"] = True
    tampered_bundle = VerifiedCrossDomainLineageBindingBundle(
        bundle_dir=step2.bundle_dir,
        contract_name=step2.contract_name,
        contract_version=step2.contract_version,
        producer_version=step2.producer_version,
        artifact_ref=step2.artifact_ref,
        artifact_digest=step2.artifact_digest,
        manifest_digest=step2.manifest_digest,
        evidence_payload=tampered,
    )
    payload = build_comparison_promotion_candidate_input_v1(cross_domain_binding=tampered_bundle)
    assert payload["candidate_input_status"] == "FAIL"
    assert "CONFIGPATCH_APPLICATION_DETECTED" in payload["candidate_input_reason_codes"]


def test_promotion_candidate_construction_detected_fail(tmp_path, ssot_durable_output_dir) -> None:
    cross_domain = produce_cross_domain_lineage_binding_fixture(tmp_path, ssot_durable_output_dir)
    assert cross_domain.cross_domain_binding_bundle_dir is not None
    step2 = verify_cross_domain_lineage_binding_bundle(cross_domain.cross_domain_binding_bundle_dir)
    tampered = dict(step2.evidence_payload)
    tampered["promotion_candidate_constructed"] = True
    tampered_bundle = VerifiedCrossDomainLineageBindingBundle(
        bundle_dir=step2.bundle_dir,
        contract_name=step2.contract_name,
        contract_version=step2.contract_version,
        producer_version=step2.producer_version,
        artifact_ref=step2.artifact_ref,
        artifact_digest=step2.artifact_digest,
        manifest_digest=step2.manifest_digest,
        evidence_payload=tampered,
    )
    payload = build_comparison_promotion_candidate_input_v1(cross_domain_binding=tampered_bundle)
    assert payload["candidate_input_status"] == "FAIL"
    assert "PROMOTION_CANDIDATE_CONSTRUCTION_DETECTED" in payload["candidate_input_reason_codes"]


def test_contract_version_mismatch_on_verify(tmp_path, ssot_durable_output_dir) -> None:
    cross_domain = produce_cross_domain_lineage_binding_fixture(tmp_path, ssot_durable_output_dir)
    assert cross_domain.cross_domain_binding_bundle_dir is not None
    artifact_path = cross_domain.cross_domain_binding_bundle_dir / STEP2_ARTIFACT_REL
    payload = read_manifest(artifact_path)
    payload["contract_version"] = "v99"
    artifact_path.write_text(deterministic_json_dumps(payload), encoding="utf-8")
    with pytest.raises(ComparisonPromotionCandidateInputError):
        verify_cross_domain_lineage_binding_bundle(cross_domain.cross_domain_binding_bundle_dir)


def test_input_artifact_refs_exactly_one(tmp_path, ssot_durable_output_dir) -> None:
    fixture = produce_candidate_input_fixture(tmp_path, ssot_durable_output_dir)
    payload = read_manifest(fixture.candidate_input_bundle_dir / ARTIFACT_REL)
    assert len(payload["input_artifact_refs"]) == 1


def test_reason_codes_sorted(tmp_path, ssot_durable_output_dir) -> None:
    fixture = produce_candidate_input_fixture(tmp_path, ssot_durable_output_dir)
    payload = read_manifest(fixture.candidate_input_bundle_dir / ARTIFACT_REL)
    codes = payload["candidate_input_reason_codes"]
    assert codes == sorted(codes)


def test_output_existing_dir_fail(tmp_path, ssot_durable_output_dir) -> None:
    cross_domain = produce_cross_domain_lineage_binding_fixture(tmp_path, ssot_durable_output_dir)
    assert cross_domain.cross_domain_binding_bundle_dir is not None
    out = _durable_output(tmp_path)
    out.mkdir()
    with pytest.raises(ComparisonPromotionCandidateInputError):
        produce_comparison_promotion_candidate_input_v1(
            inputs=_inputs(cross_domain.cross_domain_binding_bundle_dir),
            output_dir=out,
        )


def test_reverify_after_tamper(tmp_path, ssot_durable_output_dir) -> None:
    fixture = produce_candidate_input_fixture(tmp_path, ssot_durable_output_dir)
    out = fixture.candidate_input_bundle_dir
    assert out is not None
    artifact = read_manifest(out / ARTIFACT_REL)
    artifact["candidate_identity_ref"] = "tampered"
    (out / ARTIFACT_REL).write_text(deterministic_json_dumps(artifact), encoding="utf-8")
    with pytest.raises(ComparisonPromotionCandidateInputError):
        reverify_comparison_promotion_candidate_input_v1(output_dir=out)


def test_no_forbidden_runtime_imports() -> None:
    module_path = Path("src/meta/learning_loop/comparison_promotion_candidate_input_v1.py")
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


def test_step2_regression_still_passes(tmp_path, ssot_durable_output_dir) -> None:
    cross_domain = produce_cross_domain_lineage_binding_fixture(tmp_path, ssot_durable_output_dir)
    assert cross_domain.cross_domain_binding_bundle_dir is not None
    payload = read_manifest(cross_domain.cross_domain_binding_bundle_dir / STEP2_ARTIFACT_REL)
    assert payload["cross_domain_lineage_binding_status"] == "PASS"


def test_step1_regression_still_passes(tmp_path, ssot_durable_output_dir) -> None:
    cross_domain = produce_cross_domain_lineage_binding_fixture(tmp_path, ssot_durable_output_dir)
    assert cross_domain.cross_domain_binding_bundle_dir is not None
    step2 = read_manifest(cross_domain.cross_domain_binding_bundle_dir / STEP2_ARTIFACT_REL)
    step1_path = Path(str(step2["model_parameter_identity_binding_bundle_ref"])) / (
        "comparison_promotion_candidate_model_parameter_identity_binding_v1.json"
    )
    step1 = read_manifest(step1_path)
    assert step1["model_parameter_identity_binding_status"] == "PASS"


def test_eligibility_regression_refs_present(tmp_path, ssot_durable_output_dir) -> None:
    fixture = produce_candidate_input_fixture(tmp_path, ssot_durable_output_dir)
    payload = read_manifest(fixture.candidate_input_bundle_dir / ARTIFACT_REL)
    assert payload["eligibility_evidence_ref"]
    assert payload["eligibility_evidence_digest"]
    assert payload["promotion_input_binding_ref"]
    assert payload["promotion_input_binding_digest"]


def test_verify_binding_inputs(tmp_path, ssot_durable_output_dir) -> None:
    cross_domain = produce_cross_domain_lineage_binding_fixture(tmp_path, ssot_durable_output_dir)
    assert cross_domain.cross_domain_binding_bundle_dir is not None
    bundle = verify_binding_inputs(_inputs(cross_domain.cross_domain_binding_bundle_dir))
    assert isinstance(bundle, VerifiedCrossDomainLineageBindingBundle)


def test_serialization_forbidden_key(tmp_path, ssot_durable_output_dir) -> None:
    fixture = produce_candidate_input_fixture(tmp_path, ssot_durable_output_dir)
    payload = read_manifest(fixture.candidate_input_bundle_dir / ARTIFACT_REL)
    payload["promotion"] = True
    with pytest.raises(ComparisonPromotionCandidateInputError):
        serialize_comparison_promotion_candidate_input_v1(payload)


def test_copy_inputs_no_mutation(tmp_path, ssot_durable_output_dir) -> None:
    cross_domain = produce_cross_domain_lineage_binding_fixture(tmp_path, ssot_durable_output_dir)
    assert cross_domain.cross_domain_binding_bundle_dir is not None
    before = (cross_domain.cross_domain_binding_bundle_dir / STEP2_ARTIFACT_REL).read_bytes()
    out = _durable_output(tmp_path)
    produce_comparison_promotion_candidate_input_v1(
        inputs=_inputs(cross_domain.cross_domain_binding_bundle_dir),
        output_dir=out,
    )
    assert (
        cross_domain.cross_domain_binding_bundle_dir / STEP2_ARTIFACT_REL
    ).read_bytes() == before


def test_producer_version_constant() -> None:
    assert PRODUCER_VERSION == "comparison_promotion_candidate_input_v1"


def test_manifest_files_present(tmp_path, ssot_durable_output_dir) -> None:
    fixture = produce_candidate_input_fixture(tmp_path, ssot_durable_output_dir)
    out = fixture.candidate_input_bundle_dir
    assert out is not None
    assert (out / ARTIFACT_REL).is_file()
    assert (out / SELF_VERIFICATION_REL).is_file()
    assert (out / MANIFEST_FILENAME).is_file()
