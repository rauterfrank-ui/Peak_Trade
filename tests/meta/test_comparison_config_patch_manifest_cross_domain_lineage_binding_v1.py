"""Contract tests for comparison config patch manifest cross-domain lineage binding v1."""

from __future__ import annotations

import ast
import hashlib
import json
import shutil
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
]

from scripts.ops.primary_evidence_retention_v0 import verify_manifest_sha256, write_manifest_sha256
from src.meta.learning_loop.comparison_config_patch_manifest_cross_domain_lineage_binding_v1 import (
    ARTIFACT_REL,
    AUTHORITY_LEVEL,
    CONFIG_PATCH_CONTRACT_NAME,
    CONFIG_PATCH_CONTRACT_VERSION,
    CONTRACT_NAME,
    CONTRACT_VERSION,
    CROSS_DOMAIN_BINDING_AUTHORITY_INVARIANTS,
    EVIDENCE_LEVEL,
    MANIFEST_FILENAME,
    PRODUCER_VERSION,
    SELF_VERIFICATION_REL,
    ComparisonConfigPatchManifestCrossDomainLineageBindingError,
    ComparisonConfigPatchManifestCrossDomainLineageBindingInputs,
    VerifiedModelParameterIdentityBindingBundle,
    build_comparison_config_patch_manifest_cross_domain_lineage_binding_v1,
    produce_comparison_config_patch_manifest_cross_domain_lineage_binding_v1,
    reverify_comparison_config_patch_manifest_cross_domain_lineage_binding_v1,
    serialize_comparison_config_patch_manifest_cross_domain_lineage_binding_v1,
    verify_binding_inputs,
    verify_config_patch_manifest_input,
    verify_model_parameter_identity_binding_bundle,
)
from src.meta.learning_loop.comparison_promotion_candidate_model_parameter_identity_binding_v1 import (
    ARTIFACT_REL as STEP1_ARTIFACT_REL,
)
from src.meta.learning_loop.comparison_ssot_v1.io import read_manifest
from src.meta.learning_loop.config_patch_manifest_v1 import (
    load_config_patch_manifest_v1_from_json_path,
)
from src.meta.learning_loop.contract_safety_v1 import (
    compute_content_sha256,
    deterministic_json_dumps,
)
from tests.meta.comparison_config_patch_manifest_cross_domain_lineage_binding_v1_fixtures import (
    CANDIDATE_LINEAGE_MANIFEST_ID,
    produce_cross_domain_lineage_binding_fixture,
    produce_model_parameter_identity_binding_bundle,
    write_matching_config_patch_manifest,
)


@pytest.fixture(autouse=True)
def _allow_tmp_output(monkeypatch: pytest.MonkeyPatch) -> None:
    targets = (
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


def _durable_output(tmp_path: Path, name: str = "cross_domain_out") -> Path:
    root = tmp_path / "evidence_root"
    root.mkdir(exist_ok=True)
    return root / name


def _inputs(
    step1_dir: Path, config_patch_path: Path
) -> ComparisonConfigPatchManifestCrossDomainLineageBindingInputs:
    return ComparisonConfigPatchManifestCrossDomainLineageBindingInputs(
        model_parameter_identity_binding_bundle_dir=step1_dir,
        config_patch_manifest_path=config_patch_path,
    )


def test_contract_constants() -> None:
    assert CONTRACT_NAME == "comparison_config_patch_manifest_cross_domain_lineage_binding_v1"
    assert CONTRACT_VERSION == "v1"
    assert EVIDENCE_LEVEL == "LEVEL_3"
    assert AUTHORITY_LEVEL == "NON_AUTHORITIZING_EVIDENCE_ONLY"
    assert CONFIG_PATCH_CONTRACT_NAME == "config_patch_manifest_v1"
    assert CONFIG_PATCH_CONTRACT_VERSION == "v1"


def test_happy_path_pass(tmp_path, ssot_durable_output_dir) -> None:
    fixture = produce_cross_domain_lineage_binding_fixture(tmp_path, ssot_durable_output_dir)
    assert fixture.cross_domain_binding_bundle_dir is not None
    payload = read_manifest(fixture.cross_domain_binding_bundle_dir / ARTIFACT_REL)
    assert payload["cross_domain_lineage_binding_status"] == "PASS"
    assert payload["candidate_identity_status"] == "BOUND"
    assert payload["model_identity_status"] == "BOUND"
    assert payload["parameter_set_identity_status"] == "BOUND"
    assert payload["config_patch_manifest_identity_status"] == "BOUND"
    assert payload["cross_domain_lineage_status"] == "BOUND"
    assert payload["candidate_selection_status"] == "NOT_SELECTED"
    assert payload["winner_selection_status"] == "NOT_SELECTED"
    assert payload["candidate_acceptance_status"] == "NOT_ACCEPTED"
    assert payload["configpatch_created"] is False
    assert payload["configpatch_modified"] is False
    assert payload["configpatch_applied"] is False
    assert payload["configpatch_accepted"] is False
    assert payload["promotion_candidate_constructed"] is False
    assert payload["operational_filter_executed"] is False
    assert payload["promotion_policy_executed"] is False
    assert (
        "CONFIG_PATCH_MANIFEST_CROSS_DOMAIN_LINEAGE_BINDING_COMPLETE"
        in payload["cross_domain_lineage_binding_reason_codes"]
    )


def test_required_non_authorizing_flags(tmp_path, ssot_durable_output_dir) -> None:
    fixture = produce_cross_domain_lineage_binding_fixture(tmp_path, ssot_durable_output_dir)
    payload = read_manifest(fixture.cross_domain_binding_bundle_dir / ARTIFACT_REL)
    assert payload["binding_does_not_select_candidate"] is True
    assert payload["binding_does_not_accept_configpatch"] is True
    assert payload["binding_does_not_create_configpatch"] is True
    assert payload["binding_does_not_modify_configpatch"] is True
    assert payload["binding_does_not_apply_configpatch"] is True
    assert payload["binding_does_not_construct_promotion_candidate"] is True
    assert payload["binding_does_not_execute_policy"] is True
    assert (
        payload["cross_domain_binding_authority_invariants"]
        == CROSS_DOMAIN_BINDING_AUTHORITY_INVARIANTS
    )


def test_determinism(tmp_path, ssot_durable_output_dir) -> None:
    fixture = produce_cross_domain_lineage_binding_fixture(
        tmp_path, ssot_durable_output_dir, produce_output=False
    )
    out_a = _durable_output(tmp_path, "a")
    out_b = _durable_output(tmp_path, "b")
    inputs = _inputs(
        fixture.model_parameter_identity_binding_bundle_dir,
        fixture.config_patch_manifest_path,
    )
    produce_comparison_config_patch_manifest_cross_domain_lineage_binding_v1(
        inputs=inputs, output_dir=out_a
    )
    produce_comparison_config_patch_manifest_cross_domain_lineage_binding_v1(
        inputs=inputs, output_dir=out_b
    )
    assert (out_a / ARTIFACT_REL).read_text() == (out_b / ARTIFACT_REL).read_text()


def test_self_verification_and_manifest(tmp_path, ssot_durable_output_dir) -> None:
    fixture = produce_cross_domain_lineage_binding_fixture(tmp_path, ssot_durable_output_dir)
    out = fixture.cross_domain_binding_bundle_dir
    assert out is not None
    ok, msg = verify_manifest_sha256(out)
    assert ok, msg
    self_payload = read_manifest(out / SELF_VERIFICATION_REL)
    assert self_payload["overall_status"] == "PASS"
    reverify_comparison_config_patch_manifest_cross_domain_lineage_binding_v1(output_dir=out)


def test_missing_step1_bundle(tmp_path, ssot_durable_output_dir) -> None:
    fixture = produce_cross_domain_lineage_binding_fixture(
        tmp_path, ssot_durable_output_dir, produce_output=False
    )
    with pytest.raises(ComparisonConfigPatchManifestCrossDomainLineageBindingError):
        verify_model_parameter_identity_binding_bundle(tmp_path / "missing")


def test_missing_config_patch_manifest(tmp_path, ssot_durable_output_dir) -> None:
    step1 = produce_model_parameter_identity_binding_bundle(tmp_path, ssot_durable_output_dir)
    with pytest.raises(ComparisonConfigPatchManifestCrossDomainLineageBindingError):
        verify_config_patch_manifest_input(tmp_path / "missing.json")


def test_invalid_step1_manifest(tmp_path, ssot_durable_output_dir) -> None:
    fixture = produce_cross_domain_lineage_binding_fixture(
        tmp_path, ssot_durable_output_dir, produce_output=False
    )
    step1_dir = fixture.model_parameter_identity_binding_bundle_dir
    (step1_dir / "MANIFEST.sha256").write_text("invalid", encoding="utf-8")
    with pytest.raises(ComparisonConfigPatchManifestCrossDomainLineageBindingError):
        verify_model_parameter_identity_binding_bundle(step1_dir)


def test_invalid_config_patch_manifest(tmp_path, ssot_durable_output_dir) -> None:
    bad_path = ssot_durable_output_dir / "bad_config_patch.json"
    bad_path.write_text("{}", encoding="utf-8")
    with pytest.raises(ComparisonConfigPatchManifestCrossDomainLineageBindingError):
        verify_config_patch_manifest_input(bad_path)


def test_step1_self_verification_manipulation(tmp_path, ssot_durable_output_dir) -> None:
    fixture = produce_cross_domain_lineage_binding_fixture(
        tmp_path, ssot_durable_output_dir, produce_output=False
    )
    self_path = fixture.model_parameter_identity_binding_bundle_dir / "SELF_VERIFICATION.json"
    payload = read_manifest(self_path)
    payload["overall_status"] = "FAIL"
    self_path.write_text(deterministic_json_dumps(payload), encoding="utf-8")
    with pytest.raises(ComparisonConfigPatchManifestCrossDomainLineageBindingError):
        verify_model_parameter_identity_binding_bundle(
            fixture.model_parameter_identity_binding_bundle_dir
        )


def test_config_patch_digest_manipulation(tmp_path, ssot_durable_output_dir) -> None:
    fixture = produce_cross_domain_lineage_binding_fixture(
        tmp_path, ssot_durable_output_dir, produce_output=False
    )
    raw = json.loads(fixture.config_patch_manifest_path.read_text(encoding="utf-8"))
    raw["integrity"] = {"content_sha256": "0" * 64}
    fixture.config_patch_manifest_path.write_text(deterministic_json_dumps(raw), encoding="utf-8")
    with pytest.raises(ComparisonConfigPatchManifestCrossDomainLineageBindingError):
        verify_config_patch_manifest_input(fixture.config_patch_manifest_path)


def test_lineage_manifest_ref_mismatch_fail(tmp_path, ssot_durable_output_dir) -> None:
    fixture = produce_cross_domain_lineage_binding_fixture(
        tmp_path, ssot_durable_output_dir, produce_output=False
    )
    mismatch_path = write_matching_config_patch_manifest(
        ssot_durable_output_dir / "mismatch_config_patch.json",
        lineage_manifest_ref="99999999-9999-4999-8999-999999999999",
    )
    step1 = verify_model_parameter_identity_binding_bundle(
        fixture.model_parameter_identity_binding_bundle_dir
    )
    config_patch = verify_config_patch_manifest_input(mismatch_path)
    payload = build_comparison_config_patch_manifest_cross_domain_lineage_binding_v1(
        model_parameter_binding=step1,
        config_patch=config_patch,
    )
    assert payload["cross_domain_lineage_binding_status"] == "FAIL"
    assert "LINEAGE_MANIFEST_REF_MISMATCH" in payload["cross_domain_lineage_binding_reason_codes"]


def test_upstream_incomplete_propagation(tmp_path, ssot_durable_output_dir) -> None:
    fixture = produce_cross_domain_lineage_binding_fixture(
        tmp_path,
        ssot_durable_output_dir,
        all_domains_pass=False,
        produce_output=False,
    )
    step1 = verify_model_parameter_identity_binding_bundle(
        fixture.model_parameter_identity_binding_bundle_dir
    )
    config_patch = verify_config_patch_manifest_input(fixture.config_patch_manifest_path)
    payload = build_comparison_config_patch_manifest_cross_domain_lineage_binding_v1(
        model_parameter_binding=step1,
        config_patch=config_patch,
    )
    assert payload["cross_domain_lineage_binding_status"] in {"INCOMPLETE", "FAIL", "NOT_EVALUABLE"}


def test_candidate_digest_manipulation_fail(tmp_path, ssot_durable_output_dir) -> None:
    fixture = produce_cross_domain_lineage_binding_fixture(
        tmp_path, ssot_durable_output_dir, produce_output=False
    )
    step1 = verify_model_parameter_identity_binding_bundle(
        fixture.model_parameter_identity_binding_bundle_dir
    )
    config_patch = verify_config_patch_manifest_input(fixture.config_patch_manifest_path)
    tampered = dict(step1.evidence_payload)
    tampered["candidate_identity_digest"] = "0" * 64
    tampered_bundle = VerifiedModelParameterIdentityBindingBundle(
        bundle_dir=step1.bundle_dir,
        contract_name=step1.contract_name,
        contract_version=step1.contract_version,
        producer_version=step1.producer_version,
        artifact_ref=step1.artifact_ref,
        artifact_digest=step1.artifact_digest,
        manifest_digest=step1.manifest_digest,
        evidence_payload=tampered,
    )
    payload = build_comparison_config_patch_manifest_cross_domain_lineage_binding_v1(
        model_parameter_binding=tampered_bundle,
        config_patch=config_patch,
    )
    assert payload["cross_domain_lineage_binding_status"] == "FAIL"
    assert "CANDIDATE_DIGEST_MISMATCH" in payload["cross_domain_lineage_binding_reason_codes"]


def test_output_existing_dir_fail(tmp_path, ssot_durable_output_dir) -> None:
    fixture = produce_cross_domain_lineage_binding_fixture(
        tmp_path, ssot_durable_output_dir, produce_output=False
    )
    out = _durable_output(tmp_path)
    out.mkdir()
    with pytest.raises(ComparisonConfigPatchManifestCrossDomainLineageBindingError):
        produce_comparison_config_patch_manifest_cross_domain_lineage_binding_v1(
            inputs=_inputs(
                fixture.model_parameter_identity_binding_bundle_dir,
                fixture.config_patch_manifest_path,
            ),
            output_dir=out,
        )


def test_reverify_after_tamper(tmp_path, ssot_durable_output_dir) -> None:
    fixture = produce_cross_domain_lineage_binding_fixture(tmp_path, ssot_durable_output_dir)
    out = fixture.cross_domain_binding_bundle_dir
    assert out is not None
    artifact = read_manifest(out / ARTIFACT_REL)
    artifact["candidate_identity_ref"] = "tampered"
    (out / ARTIFACT_REL).write_text(deterministic_json_dumps(artifact), encoding="utf-8")
    with pytest.raises(ComparisonConfigPatchManifestCrossDomainLineageBindingError):
        reverify_comparison_config_patch_manifest_cross_domain_lineage_binding_v1(output_dir=out)


def test_input_artifact_refs_exactly_two(tmp_path, ssot_durable_output_dir) -> None:
    fixture = produce_cross_domain_lineage_binding_fixture(tmp_path, ssot_durable_output_dir)
    payload = read_manifest(fixture.cross_domain_binding_bundle_dir / ARTIFACT_REL)
    assert len(payload["input_artifact_refs"]) == 2


def test_reason_codes_sorted(tmp_path, ssot_durable_output_dir) -> None:
    fixture = produce_cross_domain_lineage_binding_fixture(tmp_path, ssot_durable_output_dir)
    payload = read_manifest(fixture.cross_domain_binding_bundle_dir / ARTIFACT_REL)
    codes = payload["cross_domain_lineage_binding_reason_codes"]
    assert codes == sorted(codes)


def test_no_forbidden_runtime_imports() -> None:
    module_path = Path(
        "src/meta/learning_loop/comparison_config_patch_manifest_cross_domain_lineage_binding_v1.py"
    )
    tree = ast.parse(module_path.read_text(encoding="utf-8"))
    forbidden = {
        "build_promotion_candidates_from_patches",
        "filter_candidates_for_live",
    }
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom):
            for alias in node.names:
                assert alias.name not in forbidden
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            assert node.func.id not in forbidden


def test_step1_regression_still_passes(tmp_path, ssot_durable_output_dir) -> None:
    step1 = produce_model_parameter_identity_binding_bundle(tmp_path, ssot_durable_output_dir)
    payload = read_manifest(step1 / STEP1_ARTIFACT_REL)
    assert payload["model_parameter_identity_binding_status"] == "PASS"


def test_config_patch_manifest_regression_load(tmp_path, ssot_durable_output_dir) -> None:
    fixture = produce_cross_domain_lineage_binding_fixture(
        tmp_path, ssot_durable_output_dir, produce_output=False
    )
    manifest = load_config_patch_manifest_v1_from_json_path(fixture.config_patch_manifest_path)
    assert manifest.lineage_manifest_ref == CANDIDATE_LINEAGE_MANIFEST_ID


def test_produce_with_matching_lineage(tmp_path, ssot_durable_output_dir) -> None:
    fixture = produce_cross_domain_lineage_binding_fixture(
        tmp_path, ssot_durable_output_dir, produce_output=False
    )
    out = _durable_output(tmp_path)
    result = produce_comparison_config_patch_manifest_cross_domain_lineage_binding_v1(
        inputs=_inputs(
            fixture.model_parameter_identity_binding_bundle_dir,
            fixture.config_patch_manifest_path,
        ),
        output_dir=out,
    )
    assert result.cross_domain_lineage_binding_status == "PASS"
    assert (out / MANIFEST_FILENAME).is_file()


def test_verify_binding_inputs(tmp_path, ssot_durable_output_dir) -> None:
    fixture = produce_cross_domain_lineage_binding_fixture(
        tmp_path, ssot_durable_output_dir, produce_output=False
    )
    step1, config_patch = verify_binding_inputs(
        _inputs(
            fixture.model_parameter_identity_binding_bundle_dir,
            fixture.config_patch_manifest_path,
        )
    )
    assert isinstance(step1, VerifiedModelParameterIdentityBindingBundle)
    assert config_patch.manifest_id


def test_serialization_forbidden_key(tmp_path, ssot_durable_output_dir) -> None:
    fixture = produce_cross_domain_lineage_binding_fixture(tmp_path, ssot_durable_output_dir)
    payload = read_manifest(fixture.cross_domain_binding_bundle_dir / ARTIFACT_REL)
    payload["promotion"] = True
    with pytest.raises(ComparisonConfigPatchManifestCrossDomainLineageBindingError):
        serialize_comparison_config_patch_manifest_cross_domain_lineage_binding_v1(payload)


def test_copy_inputs_no_mutation(tmp_path, ssot_durable_output_dir) -> None:
    fixture = produce_cross_domain_lineage_binding_fixture(
        tmp_path, ssot_durable_output_dir, produce_output=False
    )
    step1_before = (
        fixture.model_parameter_identity_binding_bundle_dir / STEP1_ARTIFACT_REL
    ).read_bytes()
    config_before = fixture.config_patch_manifest_path.read_bytes()
    out = _durable_output(tmp_path)
    produce_comparison_config_patch_manifest_cross_domain_lineage_binding_v1(
        inputs=_inputs(
            fixture.model_parameter_identity_binding_bundle_dir,
            fixture.config_patch_manifest_path,
        ),
        output_dir=out,
    )
    assert (
        fixture.model_parameter_identity_binding_bundle_dir / STEP1_ARTIFACT_REL
    ).read_bytes() == step1_before
    assert fixture.config_patch_manifest_path.read_bytes() == config_before
