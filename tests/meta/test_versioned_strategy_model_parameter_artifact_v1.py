"""Contract tests for versioned_strategy_model_parameter_artifact_v1."""

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
    "tests.meta.versioned_strategy_model_parameter_artifact_v1_fixtures",
]

from scripts.ops.primary_evidence_retention_v0 import verify_manifest_sha256
from src.meta.learning_loop.comparison_promotion_candidate_identity_binding_v1 import (
    ARTIFACT_REL as CANDIDATE_IDENTITY_ARTIFACT_REL,
)
from src.meta.learning_loop.comparison_promotion_candidate_model_parameter_identity_binding_v1 import (
    ARTIFACT_REL as MODEL_PARAMETER_ARTIFACT_REL,
)
from src.meta.learning_loop.comparison_ssot_v1.io import read_manifest
from src.meta.learning_loop.contract_safety_v1 import deterministic_json_dumps
from src.meta.learning_loop.versioned_strategy_model_parameter_artifact_v1 import (
    ARTIFACT_REL,
    ARTIFACT_SCHEMA_VERSION,
    AUTHORITY_LEVEL,
    CONTRACT_NAME,
    CONTRACT_VERSION,
    CREATION_CONTRACT_VERSION,
    EVIDENCE_LEVEL,
    MANIFEST_FILENAME,
    PRODUCER_VERSION,
    SELF_VERIFICATION_REL,
    VERSIONED_ARTIFACT_AUTHORITY_INVARIANTS,
    VersionedStrategyModelParameterArtifactError,
    VersionedStrategyModelParameterArtifactInputs,
    build_versioned_strategy_model_parameter_artifact_v1,
    produce_versioned_strategy_model_parameter_artifact_v1,
    reverify_versioned_strategy_model_parameter_artifact_v1,
    serialize_versioned_strategy_model_parameter_artifact_v1,
    verify_artifact_inputs,
    verify_candidate_identity_binding_bundle,
    verify_model_parameter_identity_binding_bundle,
)
from tests.meta.versioned_strategy_model_parameter_artifact_v1_fixtures import (
    produce_versioned_artifact_fixture,
    produce_versioned_artifact_input_bundles,
)


@pytest.fixture(autouse=True)
def _allow_tmp_output(monkeypatch: pytest.MonkeyPatch) -> None:
    targets = (
        "src.meta.learning_loop.versioned_strategy_model_parameter_artifact_v1.is_under_tmp",
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
        "src.experiments.experiment_identity_manifest_v1.is_under_tmp",
    )
    for target in targets:
        monkeypatch.setattr(target, lambda _path: False)


def _durable_output(tmp_path: Path, name: str = "versioned_artifact_out") -> Path:
    root = tmp_path / "evidence_root"
    root.mkdir(exist_ok=True)
    return root / name


def test_contract_constants() -> None:
    assert CONTRACT_NAME == "versioned_strategy_model_parameter_artifact_v1"
    assert CONTRACT_VERSION == "v1"
    assert ARTIFACT_SCHEMA_VERSION == "v1"
    assert CREATION_CONTRACT_VERSION == "versioned_strategy_model_parameter_artifact_v1"
    assert EVIDENCE_LEVEL == "LEVEL_3"
    assert AUTHORITY_LEVEL == "NON_AUTHORITIZING"
    assert ARTIFACT_REL == "versioned_strategy_model_parameter_artifact_v1.json"


def test_happy_path(tmp_path, ssot_durable_output_dir) -> None:
    fixture = produce_versioned_artifact_fixture(tmp_path, ssot_durable_output_dir)
    assert fixture.versioned_artifact_bundle_dir is not None
    payload = read_manifest(fixture.versioned_artifact_bundle_dir / ARTIFACT_REL)
    assert payload["versioned_artifact_binding_status"] == "PASS"
    assert payload["versioned_strategy_model_parameter_artifact_complete"] is True
    assert payload["strategy_identity_bound"] is True
    assert payload["model_identity_bound"] is True
    assert payload["parameter_set_identity_bound"] is True
    assert payload["cross_domain_lineage_bound"] is True
    assert payload["artifact_offline_only"] is True
    assert payload["artifact_immutable"] is True


def test_required_non_authorizing_flags(tmp_path, ssot_durable_output_dir) -> None:
    fixture = produce_versioned_artifact_fixture(tmp_path, ssot_durable_output_dir)
    payload = read_manifest(fixture.versioned_artifact_bundle_dir / ARTIFACT_REL)
    assert payload["strategy_executed"] is False
    assert payload["model_inference_executed"] is False
    assert payload["parameters_optimized"] is False
    assert payload["promotion_authorized"] is False
    assert payload["configpatch_created"] is False
    assert payload["runtime_authorized"] is False
    assert payload["live_authorized"] is False
    assert payload["orders_allowed"] is False
    assert payload["scheduler_runtime_allowed"] is False
    assert payload["network_side_effect_created"] is False
    assert payload["artifact_authority_invariants"] == VERSIONED_ARTIFACT_AUTHORITY_INVARIANTS


def test_determinism(tmp_path, ssot_durable_output_dir) -> None:
    bundles = produce_versioned_artifact_input_bundles(tmp_path, ssot_durable_output_dir)
    inputs = VersionedStrategyModelParameterArtifactInputs(
        candidate_identity_binding_bundle_dir=bundles.candidate_identity_binding_bundle_dir,
        model_parameter_identity_binding_bundle_dir=bundles.model_parameter_identity_binding_bundle_dir,
    )
    out_a = _durable_output(tmp_path, "a")
    out_b = _durable_output(tmp_path, "b")
    produce_versioned_strategy_model_parameter_artifact_v1(inputs=inputs, output_dir=out_a)
    produce_versioned_strategy_model_parameter_artifact_v1(inputs=inputs, output_dir=out_b)
    assert (out_a / ARTIFACT_REL).read_text() == (out_b / ARTIFACT_REL).read_text()


def test_artifact_id_stability(tmp_path, ssot_durable_output_dir) -> None:
    fixture = produce_versioned_artifact_fixture(tmp_path, ssot_durable_output_dir)
    payload = read_manifest(fixture.versioned_artifact_bundle_dir / ARTIFACT_REL)
    assert payload["artifact_id"] == payload["output_digest"]
    assert len(payload["artifact_id"]) == 64


def test_manifest_and_self_verification(tmp_path, ssot_durable_output_dir) -> None:
    fixture = produce_versioned_artifact_fixture(tmp_path, ssot_durable_output_dir)
    out = fixture.versioned_artifact_bundle_dir
    assert out is not None
    ok, _ = verify_manifest_sha256(out)
    assert ok
    assert (out / SELF_VERIFICATION_REL).is_file()
    self_payload = read_manifest(out / SELF_VERIFICATION_REL)
    assert self_payload["overall_status"] == "PASS"


def test_reverify(tmp_path, ssot_durable_output_dir) -> None:
    fixture = produce_versioned_artifact_fixture(tmp_path, ssot_durable_output_dir)
    reverify_versioned_strategy_model_parameter_artifact_v1(
        output_dir=fixture.versioned_artifact_bundle_dir
    )


def test_with_ai_assessment_provenance(tmp_path, ssot_durable_output_dir) -> None:
    fixture = produce_versioned_artifact_fixture(
        tmp_path, ssot_durable_output_dir, include_ai_assessment=True
    )
    payload = read_manifest(fixture.versioned_artifact_bundle_dir / ARTIFACT_REL)
    assert payload["ai_promotion_assessment_digest"]
    assert len(payload["input_artifact_refs"]) == 3


def test_identity_fields_bound(tmp_path, ssot_durable_output_dir) -> None:
    fixture = produce_versioned_artifact_fixture(tmp_path, ssot_durable_output_dir)
    payload = read_manifest(fixture.versioned_artifact_bundle_dir / ARTIFACT_REL)
    assert payload["strategy_identity_ref"]
    assert payload["strategy_identity_digest"]
    assert payload["strategy_version"]
    assert payload["model_identity_ref"]
    assert payload["model_identity_digest"]
    assert payload["parameter_set_identity_ref"]
    assert payload["parameter_set_identity_digest"]
    assert payload["comparison_definition_id"]


def test_missing_strategy_identity_rejected_on_build(tmp_path, ssot_durable_output_dir) -> None:
    bundles = produce_versioned_artifact_input_bundles(tmp_path, ssot_durable_output_dir)
    candidate = verify_candidate_identity_binding_bundle(
        bundles.candidate_identity_binding_bundle_dir
    )
    model_parameter = verify_model_parameter_identity_binding_bundle(
        bundles.model_parameter_identity_binding_bundle_dir
    )
    tampered = dict(candidate.evidence_payload)
    tampered["strategy_identity_ref"] = ""
    tampered["experiment_identity_digest"] = ""
    candidate = type(candidate)(**{**candidate.__dict__, "evidence_payload": tampered})
    artifact = build_versioned_strategy_model_parameter_artifact_v1(
        candidate=candidate,
        model_parameter=model_parameter,
        ai_assessment=None,
    )
    assert artifact["versioned_artifact_binding_status"] == "FAIL"
    assert "STRATEGY_IDENTITY_MISSING" in artifact["versioned_artifact_binding_reason_codes"]


def test_missing_model_identity_rejected_on_build(tmp_path, ssot_durable_output_dir) -> None:
    bundles = produce_versioned_artifact_input_bundles(tmp_path, ssot_durable_output_dir)
    candidate = verify_candidate_identity_binding_bundle(
        bundles.candidate_identity_binding_bundle_dir
    )
    model_parameter = verify_model_parameter_identity_binding_bundle(
        bundles.model_parameter_identity_binding_bundle_dir
    )
    tampered = dict(model_parameter.evidence_payload)
    tampered["model_identity_ref"] = ""
    model_parameter = type(model_parameter)(
        **{**model_parameter.__dict__, "evidence_payload": tampered}
    )
    artifact = build_versioned_strategy_model_parameter_artifact_v1(
        candidate=candidate,
        model_parameter=model_parameter,
        ai_assessment=None,
    )
    assert artifact["versioned_artifact_binding_status"] == "FAIL"


def test_strategy_digest_mismatch_rejected(tmp_path, ssot_durable_output_dir) -> None:
    bundles = produce_versioned_artifact_input_bundles(tmp_path, ssot_durable_output_dir)
    candidate_path = bundles.candidate_identity_binding_bundle_dir / CANDIDATE_IDENTITY_ARTIFACT_REL
    payload = read_manifest(candidate_path)
    payload["experiment_identity_digest"] = "0" * 64
    candidate_path.write_text(deterministic_json_dumps(payload), encoding="utf-8")
    with pytest.raises(VersionedStrategyModelParameterArtifactError):
        produce_versioned_strategy_model_parameter_artifact_v1(
            inputs=VersionedStrategyModelParameterArtifactInputs(
                candidate_identity_binding_bundle_dir=bundles.candidate_identity_binding_bundle_dir,
                model_parameter_identity_binding_bundle_dir=bundles.model_parameter_identity_binding_bundle_dir,
            ),
            output_dir=_durable_output(tmp_path),
        )


def test_model_digest_mismatch_rejected(tmp_path, ssot_durable_output_dir) -> None:
    bundles = produce_versioned_artifact_input_bundles(tmp_path, ssot_durable_output_dir)
    model_path = bundles.model_parameter_identity_binding_bundle_dir / MODEL_PARAMETER_ARTIFACT_REL
    payload = read_manifest(model_path)
    payload["model_identity_digest"] = "1" * 64
    model_path.write_text(deterministic_json_dumps(payload), encoding="utf-8")
    with pytest.raises(VersionedStrategyModelParameterArtifactError):
        produce_versioned_strategy_model_parameter_artifact_v1(
            inputs=VersionedStrategyModelParameterArtifactInputs(
                candidate_identity_binding_bundle_dir=bundles.candidate_identity_binding_bundle_dir,
                model_parameter_identity_binding_bundle_dir=bundles.model_parameter_identity_binding_bundle_dir,
            ),
            output_dir=_durable_output(tmp_path),
        )


def test_cross_domain_lineage_mismatch_rejected(tmp_path, ssot_durable_output_dir) -> None:
    bundles = produce_versioned_artifact_input_bundles(tmp_path, ssot_durable_output_dir)
    candidate = verify_candidate_identity_binding_bundle(
        bundles.candidate_identity_binding_bundle_dir
    )
    model_parameter = verify_model_parameter_identity_binding_bundle(
        bundles.model_parameter_identity_binding_bundle_dir
    )
    tampered = dict(candidate.evidence_payload)
    tampered["comparison_definition_id"] = "other-comparison-definition-id"
    candidate = type(candidate)(**{**candidate.__dict__, "evidence_payload": tampered})
    artifact = build_versioned_strategy_model_parameter_artifact_v1(
        candidate=candidate,
        model_parameter=model_parameter,
        ai_assessment=None,
    )
    assert artifact["versioned_artifact_binding_status"] == "FAIL"
    assert (
        "COMPARISON_DEFINITION_ID_MISMATCH" in artifact["versioned_artifact_binding_reason_codes"]
    )


def test_promotion_authorized_rejected_on_serialize(tmp_path, ssot_durable_output_dir) -> None:
    fixture = produce_versioned_artifact_fixture(tmp_path, ssot_durable_output_dir)
    payload = read_manifest(fixture.versioned_artifact_bundle_dir / ARTIFACT_REL)
    payload["promotion_authorized"] = True
    with pytest.raises(VersionedStrategyModelParameterArtifactError):
        serialize_versioned_strategy_model_parameter_artifact_v1(payload)


def test_runtime_authorized_rejected_on_serialize(tmp_path, ssot_durable_output_dir) -> None:
    fixture = produce_versioned_artifact_fixture(tmp_path, ssot_durable_output_dir)
    payload = read_manifest(fixture.versioned_artifact_bundle_dir / ARTIFACT_REL)
    payload["runtime_authorized"] = True
    with pytest.raises(VersionedStrategyModelParameterArtifactError):
        serialize_versioned_strategy_model_parameter_artifact_v1(payload)


def test_strategy_executed_rejected_on_serialize(tmp_path, ssot_durable_output_dir) -> None:
    fixture = produce_versioned_artifact_fixture(tmp_path, ssot_durable_output_dir)
    payload = read_manifest(fixture.versioned_artifact_bundle_dir / ARTIFACT_REL)
    payload["strategy_executed"] = True
    with pytest.raises(VersionedStrategyModelParameterArtifactError):
        serialize_versioned_strategy_model_parameter_artifact_v1(payload)


def test_model_inference_executed_rejected_on_serialize(tmp_path, ssot_durable_output_dir) -> None:
    fixture = produce_versioned_artifact_fixture(tmp_path, ssot_durable_output_dir)
    payload = read_manifest(fixture.versioned_artifact_bundle_dir / ARTIFACT_REL)
    payload["model_inference_executed"] = True
    with pytest.raises(VersionedStrategyModelParameterArtifactError):
        serialize_versioned_strategy_model_parameter_artifact_v1(payload)


def test_parameters_optimized_rejected_on_serialize(tmp_path, ssot_durable_output_dir) -> None:
    fixture = produce_versioned_artifact_fixture(tmp_path, ssot_durable_output_dir)
    payload = read_manifest(fixture.versioned_artifact_bundle_dir / ARTIFACT_REL)
    payload["parameters_optimized"] = True
    with pytest.raises(VersionedStrategyModelParameterArtifactError):
        serialize_versioned_strategy_model_parameter_artifact_v1(payload)


def test_configpatch_created_rejected_on_serialize(tmp_path, ssot_durable_output_dir) -> None:
    fixture = produce_versioned_artifact_fixture(tmp_path, ssot_durable_output_dir)
    payload = read_manifest(fixture.versioned_artifact_bundle_dir / ARTIFACT_REL)
    payload["configpatch_created"] = True
    with pytest.raises(VersionedStrategyModelParameterArtifactError):
        serialize_versioned_strategy_model_parameter_artifact_v1(payload)


def test_forbidden_key_rejected_on_serialize(tmp_path, ssot_durable_output_dir) -> None:
    fixture = produce_versioned_artifact_fixture(tmp_path, ssot_durable_output_dir)
    payload = read_manifest(fixture.versioned_artifact_bundle_dir / ARTIFACT_REL)
    payload["promotion"] = True
    with pytest.raises(VersionedStrategyModelParameterArtifactError):
        serialize_versioned_strategy_model_parameter_artifact_v1(payload)


def test_output_existing_dir_fail(tmp_path, ssot_durable_output_dir) -> None:
    bundles = produce_versioned_artifact_input_bundles(tmp_path, ssot_durable_output_dir)
    out = _durable_output(tmp_path)
    out.mkdir()
    with pytest.raises(VersionedStrategyModelParameterArtifactError):
        produce_versioned_strategy_model_parameter_artifact_v1(
            inputs=VersionedStrategyModelParameterArtifactInputs(
                candidate_identity_binding_bundle_dir=bundles.candidate_identity_binding_bundle_dir,
                model_parameter_identity_binding_bundle_dir=bundles.model_parameter_identity_binding_bundle_dir,
            ),
            output_dir=out,
        )


def test_reverify_after_tamper(tmp_path, ssot_durable_output_dir) -> None:
    fixture = produce_versioned_artifact_fixture(tmp_path, ssot_durable_output_dir)
    out = fixture.versioned_artifact_bundle_dir
    artifact = read_manifest(out / ARTIFACT_REL)
    artifact["model_identity_ref"] = "tampered"
    (out / ARTIFACT_REL).write_text(deterministic_json_dumps(artifact), encoding="utf-8")
    with pytest.raises(VersionedStrategyModelParameterArtifactError):
        reverify_versioned_strategy_model_parameter_artifact_v1(output_dir=out)


def test_verify_artifact_inputs(tmp_path, ssot_durable_output_dir) -> None:
    bundles = produce_versioned_artifact_input_bundles(tmp_path, ssot_durable_output_dir)
    candidate, model_parameter, ai_assessment = verify_artifact_inputs(
        VersionedStrategyModelParameterArtifactInputs(
            candidate_identity_binding_bundle_dir=bundles.candidate_identity_binding_bundle_dir,
            model_parameter_identity_binding_bundle_dir=bundles.model_parameter_identity_binding_bundle_dir,
        )
    )
    assert candidate.bundle_dir.is_dir()
    assert model_parameter.bundle_dir.is_dir()
    assert ai_assessment is None


def test_copy_inputs_no_mutation(tmp_path, ssot_durable_output_dir) -> None:
    bundles = produce_versioned_artifact_input_bundles(tmp_path, ssot_durable_output_dir)
    before = (
        bundles.candidate_identity_binding_bundle_dir / CANDIDATE_IDENTITY_ARTIFACT_REL
    ).read_bytes()
    out = _durable_output(tmp_path)
    produce_versioned_strategy_model_parameter_artifact_v1(
        inputs=VersionedStrategyModelParameterArtifactInputs(
            candidate_identity_binding_bundle_dir=bundles.candidate_identity_binding_bundle_dir,
            model_parameter_identity_binding_bundle_dir=bundles.model_parameter_identity_binding_bundle_dir,
        ),
        output_dir=out,
    )
    assert (
        bundles.candidate_identity_binding_bundle_dir / CANDIDATE_IDENTITY_ARTIFACT_REL
    ).read_bytes() == before


def test_no_forbidden_runtime_imports() -> None:
    module_path = Path("src/meta/learning_loop/versioned_strategy_model_parameter_artifact_v1.py")
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


def test_manifest_files_present(tmp_path, ssot_durable_output_dir) -> None:
    fixture = produce_versioned_artifact_fixture(tmp_path, ssot_durable_output_dir)
    out = fixture.versioned_artifact_bundle_dir
    assert out is not None
    assert (out / ARTIFACT_REL).is_file()
    assert (out / SELF_VERIFICATION_REL).is_file()
    assert (out / MANIFEST_FILENAME).is_file()


def test_producer_version_constant() -> None:
    assert PRODUCER_VERSION == "versioned_strategy_model_parameter_artifact_v1"
