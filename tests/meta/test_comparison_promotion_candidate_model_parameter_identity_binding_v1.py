"""Contract tests for comparison promotion candidate model/parameter identity binding v1."""

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
]

from scripts.ops.primary_evidence_retention_v0 import verify_manifest_sha256, write_manifest_sha256
from src.experiments.experiment_identity_manifest_v1 import (
    ARTIFACT_FILENAME as EXPERIMENT_IDENTITY_ARTIFACT,
    compute_experiment_identity_id,
)
from src.meta.learning_loop.comparison_promotion_candidate_eligibility_evidence_v1 import (
    ARTIFACT_REL as ELIGIBILITY_ARTIFACT_REL,
)
from src.meta.learning_loop.comparison_promotion_candidate_model_parameter_identity_binding_v1 import (
    ARTIFACT_REL,
    AUTHORITY_LEVEL,
    CONTRACT_NAME,
    CONTRACT_VERSION,
    EVIDENCE_LEVEL,
    MODEL_PARAMETER_BINDING_AUTHORITY_INVARIANTS,
    PRODUCER_VERSION,
    SELF_VERIFICATION_REL,
    ComparisonPromotionCandidateModelParameterIdentityBindingError,
    ComparisonPromotionCandidateModelParameterIdentityBindingInputs,
    VerifiedEligibilityEvidenceBundle,
    build_comparison_promotion_candidate_model_parameter_identity_binding_v1,
    produce_comparison_promotion_candidate_model_parameter_identity_binding_v1,
    reverify_comparison_promotion_candidate_model_parameter_identity_binding_v1,
    serialize_comparison_promotion_candidate_model_parameter_identity_binding_v1,
    verify_binding_inputs,
    verify_eligibility_evidence_bundle,
)
from src.meta.learning_loop.comparison_ssot_v1.io import read_manifest
from src.meta.learning_loop.contract_safety_v1 import (
    compute_content_sha256,
    deterministic_json_dumps,
)
from tests.meta.comparison_promotion_candidate_model_parameter_identity_binding_v1_fixtures import (
    produce_eligibility_evidence_bundle,
)


@pytest.fixture(autouse=True)
def _allow_tmp_output(monkeypatch: pytest.MonkeyPatch) -> None:
    targets = (
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


def _durable_output(tmp_path: Path, name: str = "model_parameter_identity_binding_out") -> Path:
    root = tmp_path / "evidence_root"
    root.mkdir(exist_ok=True)
    return root / name


def _inputs(
    eligibility_bundle_dir: Path,
) -> ComparisonPromotionCandidateModelParameterIdentityBindingInputs:
    return ComparisonPromotionCandidateModelParameterIdentityBindingInputs(
        eligibility_evidence_bundle_dir=eligibility_bundle_dir,
    )


def _rewrite_experiment_manifest(experiment_dir: Path, mutator) -> str:
    path = experiment_dir / EXPERIMENT_IDENTITY_ARTIFACT
    payload = read_manifest(path)
    mutator(payload)
    identity_config = payload["identity_config"]
    payload["experiment_identity_id"] = compute_experiment_identity_id(identity_config)
    body = {key: value for key, value in payload.items() if key != "integrity"}
    payload["integrity"] = {"content_sha256": compute_content_sha256(body)}
    path.write_text(deterministic_json_dumps(payload), encoding="utf-8")
    write_manifest_sha256(experiment_dir)
    return payload["integrity"]["content_sha256"]


def _rewrite_eligibility_artifact(eligibility_dir: Path, mutator) -> None:
    path = eligibility_dir / ELIGIBILITY_ARTIFACT_REL
    payload = read_manifest(path)
    mutator(payload)
    canonical = {
        key: value for key, value in payload.items() if key not in {"integrity", "manifest_digest"}
    }
    from src.meta.learning_loop.comparison_promotion_candidate_eligibility_evidence_v1 import (
        serialize_comparison_promotion_candidate_eligibility_evidence_v1,
    )

    manifest_digest = hashlib.sha256(
        serialize_comparison_promotion_candidate_eligibility_evidence_v1(canonical).encode("utf-8")
    ).hexdigest()
    payload["manifest_digest"] = manifest_digest
    excluded = frozenset(
        {"output_digest", "manifest_digest", "integrity", "created_at", "artifact_id"}
    )
    digest_body = {key: payload[key] for key in sorted(payload) if key not in excluded}
    payload["output_digest"] = compute_content_sha256(digest_body)
    payload["artifact_id"] = payload["output_digest"]
    integrity_body = {
        key: value for key, value in payload.items() if key not in {"integrity", "manifest_digest"}
    }
    payload["integrity"] = {"content_sha256": compute_content_sha256(integrity_body)}
    path.write_text(
        serialize_comparison_promotion_candidate_eligibility_evidence_v1(payload),
        encoding="utf-8",
    )
    write_manifest_sha256(eligibility_dir)


def _verified_with_status(
    eligibility_dir: Path, *, candidate_eligibility_status: str
) -> VerifiedEligibilityEvidenceBundle:
    verified = verify_eligibility_evidence_bundle(eligibility_dir)
    evidence = dict(verified.evidence_payload)
    evidence["candidate_eligibility_status"] = candidate_eligibility_status
    return VerifiedEligibilityEvidenceBundle(
        bundle_dir=verified.bundle_dir,
        contract_name=verified.contract_name,
        contract_version=verified.contract_version,
        producer_version=verified.producer_version,
        artifact_ref=verified.artifact_ref,
        artifact_digest=verified.artifact_digest,
        manifest_digest=verified.manifest_digest,
        evidence_level=verified.evidence_level,
        parent_artifact_refs=verified.parent_artifact_refs,
        evidence_payload=evidence,
    )


def test_happy_path_metric_input_candidate(tmp_path, ssot_durable_output_dir) -> None:
    eligibility = produce_eligibility_evidence_bundle(tmp_path, ssot_durable_output_dir)
    out = _durable_output(tmp_path)
    result = produce_comparison_promotion_candidate_model_parameter_identity_binding_v1(
        inputs=_inputs(eligibility.eligibility_evidence_bundle_dir),
        output_dir=out,
    )
    assert result.model_parameter_identity_binding_status == "PASS"
    assert result.model_identity_status == "BOUND"
    assert result.parameter_set_identity_status == "BOUND"
    assert result.model_identity_ref
    assert result.parameter_set_identity_ref
    assert (out / ARTIFACT_REL).is_file()
    ok, _ = verify_manifest_sha256(out)
    assert ok is True
    reverify_comparison_promotion_candidate_model_parameter_identity_binding_v1(output_dir=out)


def test_happy_path_candidate_lineage(tmp_path, ssot_durable_output_dir) -> None:
    eligibility = produce_eligibility_evidence_bundle(
        tmp_path, ssot_durable_output_dir, use_candidate_lineage=True
    )
    out = _durable_output(tmp_path, "lineage_binding")
    result = produce_comparison_promotion_candidate_model_parameter_identity_binding_v1(
        inputs=_inputs(eligibility.eligibility_evidence_bundle_dir),
        output_dir=out,
    )
    assert result.model_parameter_identity_binding_status == "PASS"
    evidence = read_manifest(out / ARTIFACT_REL)
    assert evidence["candidate_identity_source_type"] == "candidate_lineage_manifest_v1"
    assert evidence["model_identity_ref"]
    assert evidence["parameter_set_identity_ref"]


def test_deterministic_output_and_manifest(tmp_path, ssot_durable_output_dir) -> None:
    eligibility = produce_eligibility_evidence_bundle(tmp_path, ssot_durable_output_dir)
    out_a = _durable_output(tmp_path, "det_a")
    out_b = _durable_output(tmp_path, "det_b")
    produce_comparison_promotion_candidate_model_parameter_identity_binding_v1(
        inputs=_inputs(eligibility.eligibility_evidence_bundle_dir), output_dir=out_a
    )
    produce_comparison_promotion_candidate_model_parameter_identity_binding_v1(
        inputs=_inputs(eligibility.eligibility_evidence_bundle_dir), output_dir=out_b
    )
    assert (out_a / ARTIFACT_REL).read_text(encoding="utf-8") == (out_b / ARTIFACT_REL).read_text(
        encoding="utf-8"
    )


def test_required_contract_fields(tmp_path, ssot_durable_output_dir) -> None:
    eligibility = produce_eligibility_evidence_bundle(tmp_path, ssot_durable_output_dir)
    out = _durable_output(tmp_path, "fields")
    produce_comparison_promotion_candidate_model_parameter_identity_binding_v1(
        inputs=_inputs(eligibility.eligibility_evidence_bundle_dir), output_dir=out
    )
    evidence = read_manifest(out / ARTIFACT_REL)
    assert evidence["contract_name"] == CONTRACT_NAME
    assert evidence["contract_version"] == CONTRACT_VERSION
    assert evidence["producer_version"] == PRODUCER_VERSION
    assert evidence["evidence_level"] == EVIDENCE_LEVEL
    assert evidence["authority_level"] == AUTHORITY_LEVEL
    assert evidence["is_comparison_promotion_candidate_model_parameter_identity_binding"] is True
    assert evidence["candidate_selection_status"] == "NOT_SELECTED"
    assert evidence["winner_selection_status"] == "NOT_SELECTED"
    assert evidence["candidate_acceptance_status"] == "NOT_ACCEPTED"
    assert evidence["promotion_candidate_constructed"] is False
    assert evidence["operational_filter_executed"] is False
    assert evidence["promotion_policy_executed"] is False
    assert evidence["configpatch_created"] is False
    assert len(evidence["input_artifact_refs"]) == 1


def test_non_authorizing_flags(tmp_path, ssot_durable_output_dir) -> None:
    eligibility = produce_eligibility_evidence_bundle(tmp_path, ssot_durable_output_dir)
    out = _durable_output(tmp_path, "flags")
    produce_comparison_promotion_candidate_model_parameter_identity_binding_v1(
        inputs=_inputs(eligibility.eligibility_evidence_bundle_dir), output_dir=out
    )
    evidence = read_manifest(out / ARTIFACT_REL)
    assert evidence["binding_does_not_select_candidate"] is True
    assert evidence["binding_does_not_construct_promotion_candidate"] is True
    assert evidence["binding_does_not_execute_operational_filter"] is True
    assert evidence["binding_does_not_create_configpatch"] is True
    assert evidence["model_parameter_binding_authority_invariants"] == (
        MODEL_PARAMETER_BINDING_AUTHORITY_INVARIANTS
    )


def test_self_verification_pass(tmp_path, ssot_durable_output_dir) -> None:
    eligibility = produce_eligibility_evidence_bundle(tmp_path, ssot_durable_output_dir)
    out = _durable_output(tmp_path, "self")
    produce_comparison_promotion_candidate_model_parameter_identity_binding_v1(
        inputs=_inputs(eligibility.eligibility_evidence_bundle_dir), output_dir=out
    )
    self_payload = read_manifest(out / SELF_VERIFICATION_REL)
    assert self_payload["overall_status"] == "PASS"


def test_pass_reason_codes(tmp_path, ssot_durable_output_dir) -> None:
    eligibility = produce_eligibility_evidence_bundle(tmp_path, ssot_durable_output_dir)
    out = _durable_output(tmp_path, "reason")
    produce_comparison_promotion_candidate_model_parameter_identity_binding_v1(
        inputs=_inputs(eligibility.eligibility_evidence_bundle_dir), output_dir=out
    )
    evidence = read_manifest(out / ARTIFACT_REL)
    assert (
        "MODEL_PARAMETER_IDENTITY_BINDING_COMPLETE"
        in evidence["model_parameter_identity_binding_reason_codes"]
    )
    assert evidence["model_parameter_identity_binding_reason_codes"] == sorted(
        evidence["model_parameter_identity_binding_reason_codes"]
    )


def test_upstream_not_evaluable_propagates(tmp_path, ssot_durable_output_dir) -> None:
    eligibility = produce_eligibility_evidence_bundle(
        tmp_path, ssot_durable_output_dir, all_domains_pass=False
    )
    out = _durable_output(tmp_path, "not_eval")
    result = produce_comparison_promotion_candidate_model_parameter_identity_binding_v1(
        inputs=_inputs(eligibility.eligibility_evidence_bundle_dir), output_dir=out
    )
    assert result.model_parameter_identity_binding_status == "NOT_EVALUABLE"
    evidence = read_manifest(out / ARTIFACT_REL)
    assert (
        "NOT_EVALUABLE_INSUFFICIENT_EVIDENCE"
        in evidence["model_parameter_identity_binding_reason_codes"]
    )


def test_upstream_incomplete_propagates(tmp_path, ssot_durable_output_dir) -> None:
    eligibility = produce_eligibility_evidence_bundle(tmp_path, ssot_durable_output_dir)
    verified = _verified_with_status(
        eligibility.eligibility_evidence_bundle_dir, candidate_eligibility_status="INCOMPLETE"
    )
    evidence = build_comparison_promotion_candidate_model_parameter_identity_binding_v1(
        eligibility=verified,
    )
    assert evidence["model_parameter_identity_binding_status"] == "INCOMPLETE"
    assert (
        "UPSTREAM_ELIGIBILITY_INCOMPLETE"
        in evidence["model_parameter_identity_binding_reason_codes"]
    )


def test_upstream_fail_propagates(tmp_path, ssot_durable_output_dir) -> None:
    eligibility = produce_eligibility_evidence_bundle(tmp_path, ssot_durable_output_dir)
    verified = _verified_with_status(
        eligibility.eligibility_evidence_bundle_dir, candidate_eligibility_status="FAIL"
    )
    evidence = build_comparison_promotion_candidate_model_parameter_identity_binding_v1(
        eligibility=verified,
    )
    assert evidence["model_parameter_identity_binding_status"] == "FAIL"
    assert "UPSTREAM_ELIGIBILITY_FAIL" in evidence["model_parameter_identity_binding_reason_codes"]


def test_input_bundle_missing(tmp_path) -> None:
    out = _durable_output(tmp_path)
    inputs = ComparisonPromotionCandidateModelParameterIdentityBindingInputs(
        eligibility_evidence_bundle_dir=tmp_path / "missing",
    )
    with pytest.raises(
        ComparisonPromotionCandidateModelParameterIdentityBindingError, match="must be a directory"
    ):
        produce_comparison_promotion_candidate_model_parameter_identity_binding_v1(
            inputs=inputs, output_dir=out
        )


def test_manifest_manipulated(tmp_path, ssot_durable_output_dir) -> None:
    eligibility = produce_eligibility_evidence_bundle(tmp_path, ssot_durable_output_dir)
    bad_dir = ssot_durable_output_dir / "bad_eligibility"
    shutil.copytree(eligibility.eligibility_evidence_bundle_dir, bad_dir)
    (bad_dir / "MANIFEST.sha256").write_text("deadbeef\n", encoding="utf-8")
    out = _durable_output(tmp_path)
    with pytest.raises(
        ComparisonPromotionCandidateModelParameterIdentityBindingError, match="MANIFEST"
    ):
        produce_comparison_promotion_candidate_model_parameter_identity_binding_v1(
            inputs=_inputs(bad_dir), output_dir=out
        )


def test_missing_model_identity(tmp_path, ssot_durable_output_dir) -> None:
    eligibility = produce_eligibility_evidence_bundle(tmp_path, ssot_durable_output_dir)
    verified = verify_eligibility_evidence_bundle(eligibility.eligibility_evidence_bundle_dir)
    evidence = read_manifest(eligibility.eligibility_evidence_bundle_dir / ELIGIBILITY_ARTIFACT_REL)
    bad_experiment = ssot_durable_output_dir / "bad_experiment_model"
    shutil.copytree(Path(evidence["experiment_identity_ref"]), bad_experiment)

    def _strip_strategy_name(payload: dict) -> None:
        payload["identity_config"]["strategy_name"] = ""

    new_digest = _rewrite_experiment_manifest(bad_experiment, _strip_strategy_name)
    modified = VerifiedEligibilityEvidenceBundle(
        bundle_dir=verified.bundle_dir,
        contract_name=verified.contract_name,
        contract_version=verified.contract_version,
        producer_version=verified.producer_version,
        artifact_ref=verified.artifact_ref,
        artifact_digest=verified.artifact_digest,
        manifest_digest=verified.manifest_digest,
        evidence_level=verified.evidence_level,
        parent_artifact_refs=verified.parent_artifact_refs,
        evidence_payload={
            **verified.evidence_payload,
            "experiment_identity_ref": bad_experiment.as_posix(),
            "experiment_identity_digest": new_digest,
        },
    )
    binding = build_comparison_promotion_candidate_model_parameter_identity_binding_v1(
        eligibility=modified
    )
    assert binding["model_parameter_identity_binding_status"] == "FAIL"
    assert "MODEL_IDENTITY_MISSING" in binding["model_parameter_identity_binding_reason_codes"]


def test_missing_parameter_set(tmp_path, ssot_durable_output_dir) -> None:
    eligibility = produce_eligibility_evidence_bundle(tmp_path, ssot_durable_output_dir)
    verified = verify_eligibility_evidence_bundle(eligibility.eligibility_evidence_bundle_dir)
    evidence = read_manifest(eligibility.eligibility_evidence_bundle_dir / ELIGIBILITY_ARTIFACT_REL)
    bad_experiment = ssot_durable_output_dir / "bad_experiment_params"
    shutil.copytree(Path(evidence["experiment_identity_ref"]), bad_experiment)

    def _clear_parameter_set(payload: dict) -> None:
        payload["identity_config"]["param_sweeps"] = []
        payload["identity_config"]["base_params"] = {}

    new_digest = _rewrite_experiment_manifest(bad_experiment, _clear_parameter_set)
    modified = VerifiedEligibilityEvidenceBundle(
        bundle_dir=verified.bundle_dir,
        contract_name=verified.contract_name,
        contract_version=verified.contract_version,
        producer_version=verified.producer_version,
        artifact_ref=verified.artifact_ref,
        artifact_digest=verified.artifact_digest,
        manifest_digest=verified.manifest_digest,
        evidence_level=verified.evidence_level,
        parent_artifact_refs=verified.parent_artifact_refs,
        evidence_payload={
            **verified.evidence_payload,
            "experiment_identity_ref": bad_experiment.as_posix(),
            "experiment_identity_digest": new_digest,
        },
    )
    binding = build_comparison_promotion_candidate_model_parameter_identity_binding_v1(
        eligibility=modified
    )
    assert binding["model_parameter_identity_binding_status"] == "FAIL"
    assert (
        "PARAMETER_SET_IDENTITY_MISSING" in binding["model_parameter_identity_binding_reason_codes"]
    )


def test_experiment_digest_mismatch(tmp_path, ssot_durable_output_dir) -> None:
    eligibility = produce_eligibility_evidence_bundle(tmp_path, ssot_durable_output_dir)
    evidence = read_manifest(eligibility.eligibility_evidence_bundle_dir / ELIGIBILITY_ARTIFACT_REL)
    experiment_dir = Path(evidence["experiment_identity_ref"])

    def _mutate_without_sync(payload: dict) -> None:
        payload["identity_config"]["strategy_name"] = "mutated_strategy"

    _rewrite_experiment_manifest(experiment_dir, _mutate_without_sync)

    out = _durable_output(tmp_path, "digest_mismatch")
    result = produce_comparison_promotion_candidate_model_parameter_identity_binding_v1(
        inputs=_inputs(eligibility.eligibility_evidence_bundle_dir), output_dir=out
    )
    assert result.model_parameter_identity_binding_status == "FAIL"
    binding = read_manifest(out / ARTIFACT_REL)
    assert (
        "EXPERIMENT_IDENTITY_DIGEST_MISMATCH"
        in binding["model_parameter_identity_binding_reason_codes"]
    )


def test_candidate_selection_detected_on_output_serialization() -> None:
    evidence = _minimal_evidence_payload()
    evidence["candidate_selection_status"] = "SELECTED"
    with pytest.raises(
        ComparisonPromotionCandidateModelParameterIdentityBindingError,
        match="candidate_selection_status",
    ):
        serialize_comparison_promotion_candidate_model_parameter_identity_binding_v1(evidence)


def test_winner_selection_detected_on_output_serialization() -> None:
    evidence = _minimal_evidence_payload()
    evidence["winner_selection_status"] = "WINNER"
    with pytest.raises(
        ComparisonPromotionCandidateModelParameterIdentityBindingError,
        match="winner_selection_status",
    ):
        serialize_comparison_promotion_candidate_model_parameter_identity_binding_v1(evidence)


def test_candidate_acceptance_detected_on_output_serialization() -> None:
    evidence = _minimal_evidence_payload()
    evidence["candidate_acceptance_status"] = "ACCEPTED"
    with pytest.raises(
        ComparisonPromotionCandidateModelParameterIdentityBindingError,
        match="candidate_acceptance_status",
    ):
        serialize_comparison_promotion_candidate_model_parameter_identity_binding_v1(evidence)


def test_forbidden_capability_in_output_serialization() -> None:
    evidence = _minimal_evidence_payload()
    evidence["capabilities"] = ["CAN_PROMOTE_ARTIFACT"]
    with pytest.raises(
        ComparisonPromotionCandidateModelParameterIdentityBindingError, match="forbidden capability"
    ):
        serialize_comparison_promotion_candidate_model_parameter_identity_binding_v1(evidence)


def test_forbidden_filter_candidates_for_live_key_on_serialization() -> None:
    evidence = _minimal_evidence_payload()
    evidence["filter_candidates_for_live"] = True
    with pytest.raises(
        ComparisonPromotionCandidateModelParameterIdentityBindingError, match="forbidden index key"
    ):
        serialize_comparison_promotion_candidate_model_parameter_identity_binding_v1(evidence)


def test_promotion_candidate_constructed_flag_rejected() -> None:
    evidence = _minimal_evidence_payload()
    evidence["promotion_candidate_constructed"] = True
    with pytest.raises(
        ComparisonPromotionCandidateModelParameterIdentityBindingError,
        match="promotion_candidate_constructed",
    ):
        serialize_comparison_promotion_candidate_model_parameter_identity_binding_v1(evidence)


def test_unsorted_reason_codes_rejected() -> None:
    evidence = _minimal_evidence_payload()
    evidence["model_parameter_identity_binding_reason_codes"] = ["Z_CODE", "A_CODE"]
    with pytest.raises(
        ComparisonPromotionCandidateModelParameterIdentityBindingError,
        match="sorted deterministically",
    ):
        serialize_comparison_promotion_candidate_model_parameter_identity_binding_v1(evidence)


def test_existing_output_fail_closed(tmp_path, ssot_durable_output_dir) -> None:
    eligibility = produce_eligibility_evidence_bundle(tmp_path, ssot_durable_output_dir)
    out = _durable_output(tmp_path, "exists")
    out.mkdir()
    with pytest.raises(
        ComparisonPromotionCandidateModelParameterIdentityBindingError, match="already exists"
    ):
        produce_comparison_promotion_candidate_model_parameter_identity_binding_v1(
            inputs=_inputs(eligibility.eligibility_evidence_bundle_dir), output_dir=out
        )


def test_upstream_not_mutated(tmp_path, ssot_durable_output_dir) -> None:
    eligibility = produce_eligibility_evidence_bundle(tmp_path, ssot_durable_output_dir)
    before = {
        rel.as_posix(): rel.read_bytes()
        for rel in eligibility.eligibility_evidence_bundle_dir.rglob("*")
        if rel.is_file() and not rel.is_symlink()
    }
    out = _durable_output(tmp_path, "nomut")
    produce_comparison_promotion_candidate_model_parameter_identity_binding_v1(
        inputs=_inputs(eligibility.eligibility_evidence_bundle_dir), output_dir=out
    )
    after = {
        rel.as_posix(): rel.read_bytes()
        for rel in eligibility.eligibility_evidence_bundle_dir.rglob("*")
        if rel.is_file() and not rel.is_symlink()
    }
    assert before == after


def test_ast_no_forbidden_runtime_imports() -> None:
    module_path = (
        Path(__file__).resolve().parents[2]
        / "src/meta/learning_loop/comparison_promotion_candidate_model_parameter_identity_binding_v1.py"
    )
    tree = ast.parse(module_path.read_text(encoding="utf-8"))
    modules: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            modules.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            modules.add(node.module)
    forbidden = {
        "src.execution",
        "src.risk",
        "src.governance.promotion_loop.engine",
        "src.governance.promotion_loop.safety",
        "src.governance.promotion_loop.policy",
    }
    assert not modules & forbidden


def test_ast_no_filter_candidates_for_live_call() -> None:
    module_path = (
        Path(__file__).resolve().parents[2]
        / "src/meta/learning_loop/comparison_promotion_candidate_model_parameter_identity_binding_v1.py"
    )
    tree = ast.parse(module_path.read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module:
            assert node.module != "src.governance.promotion_loop.engine"
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            assert node.func.id != "filter_candidates_for_live"


def test_regression_eligibility_and_identity_binding_importable() -> None:
    from src.meta.learning_loop import (
        comparison_promotion_candidate_eligibility_evidence_v1 as eligibility_mod,
        comparison_promotion_candidate_identity_binding_v1 as identity_mod,
    )

    assert eligibility_mod.CONTRACT_NAME == "comparison_promotion_candidate_eligibility_evidence_v1"
    assert identity_mod.CONTRACT_NAME == "comparison_promotion_candidate_identity_binding_v1"


def test_build_and_verify_inputs(tmp_path, ssot_durable_output_dir) -> None:
    eligibility = produce_eligibility_evidence_bundle(tmp_path, ssot_durable_output_dir)
    verified = verify_binding_inputs(_inputs(eligibility.eligibility_evidence_bundle_dir))
    evidence = build_comparison_promotion_candidate_model_parameter_identity_binding_v1(
        eligibility=verified,
    )
    assert evidence["model_parameter_identity_binding_status"] == "PASS"


def test_digest_mismatch_on_replay(tmp_path, ssot_durable_output_dir) -> None:
    eligibility = produce_eligibility_evidence_bundle(tmp_path, ssot_durable_output_dir)
    out = _durable_output(tmp_path, "digest")
    produce_comparison_promotion_candidate_model_parameter_identity_binding_v1(
        inputs=_inputs(eligibility.eligibility_evidence_bundle_dir), output_dir=out
    )
    evidence = read_manifest(out / ARTIFACT_REL)
    evidence["eligibility_evidence_digest"] = "0" * 64
    (out / ARTIFACT_REL).write_text(json.dumps(evidence), encoding="utf-8")
    with pytest.raises(ComparisonPromotionCandidateModelParameterIdentityBindingError):
        reverify_comparison_promotion_candidate_model_parameter_identity_binding_v1(output_dir=out)


def _minimal_evidence_payload() -> dict:
    return {
        "contract_name": CONTRACT_NAME,
        "contract_version": CONTRACT_VERSION,
        "producer_version": PRODUCER_VERSION,
        "evidence_level": EVIDENCE_LEVEL,
        "authority_level": AUTHORITY_LEVEL,
        "is_comparison_promotion_candidate_model_parameter_identity_binding": True,
        "evidence_does_not_authorize_promotion": True,
        "evidence_does_not_authorize_runtime": True,
        "binding_does_not_select_candidate": True,
        "binding_does_not_choose_winner": True,
        "binding_does_not_accept_candidate": True,
        "binding_does_not_construct_promotion_candidate": True,
        "binding_does_not_execute_operational_filter": True,
        "binding_does_not_execute_policy": True,
        "binding_does_not_create_configpatch": True,
        "binding_does_not_modify_config": True,
        "binding_does_not_authorize_promotion": True,
        "binding_does_not_authorize_runtime": True,
        "binding_does_not_authorize_live": True,
        "binding_does_not_deploy": True,
        "binding_does_not_activate": True,
        "binding_does_not_create_order_intent": True,
        "binding_does_not_modify_trading_logic": True,
        "capabilities": [],
        "model_parameter_identity_binding_status": "PASS",
        "model_parameter_identity_binding_reason_codes": [
            "MODEL_PARAMETER_IDENTITY_BINDING_COMPLETE"
        ],
        "candidate_selection_status": "NOT_SELECTED",
        "winner_selection_status": "NOT_SELECTED",
        "candidate_acceptance_status": "NOT_ACCEPTED",
        "promotion_candidate_constructed": False,
        "operational_filter_executed": False,
        "promotion_policy_executed": False,
        "configpatch_created": False,
    }
