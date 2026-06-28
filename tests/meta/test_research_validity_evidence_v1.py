"""Contract tests for learning loop research validity evidence v1."""

from __future__ import annotations

import ast
import json
import shutil
import uuid
from copy import deepcopy
from pathlib import Path

import pytest

pytest_plugins = ["tests.meta.comparison_ssot_v1_fixtures"]

from scripts.ops.primary_evidence_retention_v0 import verify_manifest_sha256, write_manifest_sha256
from src.experiments.experiment_identity_manifest_v1 import (
    ARTIFACT_FILENAME as EXPERIMENT_IDENTITY_REL,
)
from src.meta.learning_loop.comparison_ssot_v1.io import read_manifest
from src.meta.learning_loop.contract_safety_v1 import (
    compute_content_sha256,
    deterministic_json_dumps,
)
from src.meta.learning_loop.research_validity_evidence_v1 import (
    ARTIFACT_REL,
    CONTRACT_NAME,
    CONTRACT_VERSION,
    EVIDENCE_LEVEL,
    INPUT_ARTIFACT_FILENAME,
    PRODUCER_VERSION,
    RESEARCH_VALIDITY_AUTHORITY_INVARIANTS,
    SELF_VERIFICATION_REL,
    InputArtifactKind,
    ResearchValidityEvidenceError,
    ResearchValidityProducerInputs,
    build_research_validity_evidence_v1,
    produce_research_validity_evidence_v1,
    reverify_research_validity_evidence_v1,
    serialize_research_validity_evidence_v1,
    verify_all_producer_inputs,
)
from tests.meta.research_validity_evidence_v1_fixtures import (
    produce_experiment_identity_bundle,
    produce_full_research_validity_inputs,
    produce_research_input_bundle,
)


@pytest.fixture(autouse=True)
def _allow_tmp_output(monkeypatch: pytest.MonkeyPatch) -> None:
    targets = (
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


def _durable_output(tmp_path: Path, name: str = "validity_out") -> Path:
    root = tmp_path / "evidence_root"
    root.mkdir(exist_ok=True)
    return root / name


def _rewrite_input_artifact(bundle_dir: Path, mutator) -> None:
    path = bundle_dir / INPUT_ARTIFACT_FILENAME
    payload = read_manifest(path)
    mutator(payload)
    body = {key: value for key, value in payload.items() if key != "integrity"}
    payload["integrity"] = {"content_sha256": compute_content_sha256(body)}
    path.write_text(deterministic_json_dumps(payload), encoding="utf-8")
    write_manifest_sha256(bundle_dir)


def test_happy_path_produce_and_reverify(tmp_path, ssot_durable_output_dir) -> None:
    inputs = produce_full_research_validity_inputs(
        tmp_path, ssot_durable_output_dir, all_domains_pass=True
    )
    out = _durable_output(tmp_path)
    result = produce_research_validity_evidence_v1(inputs=inputs, output_dir=out)
    assert result.research_validity_status == "PASS"
    assert (out / ARTIFACT_REL).is_file()
    ok, _ = verify_manifest_sha256(out)
    assert ok is True
    reverify_research_validity_evidence_v1(output_dir=out)


def test_deterministic_output(tmp_path, ssot_durable_output_dir) -> None:
    inputs = produce_full_research_validity_inputs(
        tmp_path, ssot_durable_output_dir, all_domains_pass=True
    )
    out_a = _durable_output(tmp_path, "det_a")
    out_b = _durable_output(tmp_path, "det_b")
    produce_research_validity_evidence_v1(inputs=inputs, output_dir=out_a)
    produce_research_validity_evidence_v1(inputs=inputs, output_dir=out_b)
    assert (out_a / ARTIFACT_REL).read_text(encoding="utf-8") == (out_b / ARTIFACT_REL).read_text(
        encoding="utf-8"
    )


def test_not_evaluable_upstream_status(tmp_path, ssot_durable_output_dir) -> None:
    inputs = produce_full_research_validity_inputs(
        tmp_path, ssot_durable_output_dir, all_domains_pass=False
    )
    out = _durable_output(tmp_path, "not_eval")
    result = produce_research_validity_evidence_v1(inputs=inputs, output_dir=out)
    assert result.research_validity_status == "NOT_EVALUABLE"
    evidence = read_manifest(out / ARTIFACT_REL)
    assert evidence["extended_hardening_complete"] is False


def test_missing_checkpoint_bundle(tmp_path, ssot_durable_output_dir) -> None:
    inputs = produce_full_research_validity_inputs(
        tmp_path, ssot_durable_output_dir, all_domains_pass=True
    )
    missing = tmp_path / "missing_checkpoint"
    bad_inputs = ResearchValidityProducerInputs(
        checkpoint_bundle_dir=missing,
        experiment_identity_bundle_dir=inputs.experiment_identity_bundle_dir,
        dataset_identity_bundle_dir=inputs.dataset_identity_bundle_dir,
        partition_evidence_bundle_dir=inputs.partition_evidence_bundle_dir,
        selection_procedure_bundle_dir=inputs.selection_procedure_bundle_dir,
        walk_forward_result_bundle_dir=inputs.walk_forward_result_bundle_dir,
        cost_stress_result_bundle_dir=inputs.cost_stress_result_bundle_dir,
        slippage_stress_result_bundle_dir=inputs.slippage_stress_result_bundle_dir,
        funding_stress_result_bundle_dir=inputs.funding_stress_result_bundle_dir,
        parameter_stability_result_bundle_dir=inputs.parameter_stability_result_bundle_dir,
        regime_breakdown_bundle_dir=inputs.regime_breakdown_bundle_dir,
        overfitting_risk_result_bundle_dir=inputs.overfitting_risk_result_bundle_dir,
    )
    with pytest.raises(ResearchValidityEvidenceError):
        verify_all_producer_inputs(bad_inputs)


def test_experiment_identity_digest_mismatch(tmp_path, ssot_durable_output_dir) -> None:
    inputs = produce_full_research_validity_inputs(
        tmp_path, ssot_durable_output_dir, all_domains_pass=True
    )
    manifest_path = inputs.experiment_identity_bundle_dir / EXPERIMENT_IDENTITY_REL
    payload = read_manifest(manifest_path)
    payload["experiment_identity_id"] = "f" * 64
    manifest_path.write_text(json.dumps(payload), encoding="utf-8")
    write_manifest_sha256(inputs.experiment_identity_bundle_dir)
    with pytest.raises(ResearchValidityEvidenceError, match="experiment_identity_id mismatch"):
        verify_all_producer_inputs(inputs)


def test_dataset_experiment_lineage_mismatch(tmp_path, ssot_durable_output_dir) -> None:
    inputs = produce_full_research_validity_inputs(
        tmp_path, ssot_durable_output_dir, all_domains_pass=True
    )

    def _mutate(payload: dict) -> None:
        payload["experiment_identity_id"] = "a" * 64

    _rewrite_input_artifact(inputs.dataset_identity_bundle_dir, _mutate)
    with pytest.raises(ResearchValidityEvidenceError, match="experiment_identity_id mismatch"):
        verify_all_producer_inputs(inputs)


def test_trial_count_mismatch(tmp_path, ssot_durable_output_dir) -> None:
    inputs = produce_full_research_validity_inputs(
        tmp_path, ssot_durable_output_dir, all_domains_pass=True
    )

    def _mutate(payload: dict) -> None:
        payload["number_of_trials"] = 99

    _rewrite_input_artifact(inputs.selection_procedure_bundle_dir, _mutate)
    with pytest.raises(ResearchValidityEvidenceError, match="number_of_trials mismatch"):
        verify_all_producer_inputs(inputs)


def test_manipulated_checkpoint_manifest(tmp_path, ssot_durable_output_dir) -> None:
    inputs = produce_full_research_validity_inputs(
        tmp_path, ssot_durable_output_dir, all_domains_pass=True
    )
    manifest_path = inputs.checkpoint_bundle_dir / "MANIFEST.sha256"
    manifest_path.write_text("deadbeef\n", encoding="utf-8")
    with pytest.raises(ResearchValidityEvidenceError, match="MANIFEST.sha256"):
        verify_all_producer_inputs(inputs)


def test_forbidden_capability_on_serialized_evidence(tmp_path, ssot_durable_output_dir) -> None:
    inputs = produce_full_research_validity_inputs(
        tmp_path, ssot_durable_output_dir, all_domains_pass=True
    )
    verified = verify_all_producer_inputs(inputs)
    evidence = build_research_validity_evidence_v1(inputs=inputs, verified=verified)
    evidence["capabilities"] = ["CAN_PROMOTE_ARTIFACT"]
    with pytest.raises(ResearchValidityEvidenceError, match="forbidden capability"):
        serialize_research_validity_evidence_v1(evidence)


def test_non_authorizing_flags_required(tmp_path, ssot_durable_output_dir) -> None:
    inputs = produce_full_research_validity_inputs(
        tmp_path, ssot_durable_output_dir, all_domains_pass=True
    )
    verified = verify_all_producer_inputs(inputs)
    evidence = build_research_validity_evidence_v1(inputs=inputs, verified=verified)
    evidence["research_validity_does_not_select"] = False
    with pytest.raises(ResearchValidityEvidenceError, match="research_validity_does_not_select"):
        serialize_research_validity_evidence_v1(evidence)


def test_tampered_output_after_produce(tmp_path, ssot_durable_output_dir) -> None:
    inputs = produce_full_research_validity_inputs(
        tmp_path, ssot_durable_output_dir, all_domains_pass=True
    )
    out = _durable_output(tmp_path, "tamper")
    produce_research_validity_evidence_v1(inputs=inputs, output_dir=out)
    evidence = read_manifest(out / ARTIFACT_REL)
    evidence["is_research_validity_evidence"] = False
    (out / ARTIFACT_REL).write_text(json.dumps(evidence), encoding="utf-8")
    with pytest.raises(ResearchValidityEvidenceError):
        reverify_research_validity_evidence_v1(output_dir=out)


def test_existing_output_fail_closed(tmp_path, ssot_durable_output_dir) -> None:
    inputs = produce_full_research_validity_inputs(
        tmp_path, ssot_durable_output_dir, all_domains_pass=True
    )
    out = _durable_output(tmp_path, "exists")
    out.mkdir()
    with pytest.raises(ResearchValidityEvidenceError, match="already exists"):
        produce_research_validity_evidence_v1(inputs=inputs, output_dir=out)


def test_inputs_not_mutated(tmp_path, ssot_durable_output_dir) -> None:
    inputs = produce_full_research_validity_inputs(
        tmp_path, ssot_durable_output_dir, all_domains_pass=True
    )
    before = {
        rel.as_posix(): rel.read_bytes()
        for bundle in (
            inputs.checkpoint_bundle_dir,
            inputs.experiment_identity_bundle_dir,
            inputs.dataset_identity_bundle_dir,
        )
        for rel in bundle.rglob("*")
        if rel.is_file() and not rel.is_symlink()
    }
    out = _durable_output(tmp_path, "nomut")
    produce_research_validity_evidence_v1(inputs=inputs, output_dir=out)
    after = {
        rel.as_posix(): rel.read_bytes()
        for bundle in (
            inputs.checkpoint_bundle_dir,
            inputs.experiment_identity_bundle_dir,
            inputs.dataset_identity_bundle_dir,
        )
        for rel in bundle.rglob("*")
        if rel.is_file() and not rel.is_symlink()
    }
    assert before == after


def test_ast_no_forbidden_runtime_imports() -> None:
    module_path = (
        Path(__file__).resolve().parents[2]
        / "src/meta/learning_loop/research_validity_evidence_v1.py"
    )
    tree = ast.parse(module_path.read_text(encoding="utf-8"))
    modules: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            modules.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            modules.add(node.module)
    forbidden = {"src.execution", "src.risk", "mlflow"}
    assert not modules & forbidden


def test_contract_constants() -> None:
    assert CONTRACT_NAME == "research_validity_evidence_v1"
    assert CONTRACT_VERSION == "v1"
    assert EVIDENCE_LEVEL == "LEVEL_3"
    assert PRODUCER_VERSION == "research_validity_evidence_v1"


def test_wrong_input_artifact_kind(tmp_path, ssot_durable_output_dir) -> None:
    inputs = produce_full_research_validity_inputs(
        tmp_path, ssot_durable_output_dir, all_domains_pass=True
    )
    bad = ssot_durable_output_dir / "bad_wf"
    shutil.copytree(inputs.walk_forward_result_bundle_dir, bad)
    payload = read_manifest(bad / INPUT_ARTIFACT_FILENAME)
    payload["artifact_kind"] = InputArtifactKind.COST_STRESS_RESULT.value
    (bad / INPUT_ARTIFACT_FILENAME).write_text(json.dumps(payload), encoding="utf-8")
    write_manifest_sha256(bad)
    bad_inputs = ResearchValidityProducerInputs(
        checkpoint_bundle_dir=inputs.checkpoint_bundle_dir,
        experiment_identity_bundle_dir=inputs.experiment_identity_bundle_dir,
        dataset_identity_bundle_dir=inputs.dataset_identity_bundle_dir,
        partition_evidence_bundle_dir=inputs.partition_evidence_bundle_dir,
        selection_procedure_bundle_dir=inputs.selection_procedure_bundle_dir,
        walk_forward_result_bundle_dir=bad,
        cost_stress_result_bundle_dir=inputs.cost_stress_result_bundle_dir,
        slippage_stress_result_bundle_dir=inputs.slippage_stress_result_bundle_dir,
        funding_stress_result_bundle_dir=inputs.funding_stress_result_bundle_dir,
        parameter_stability_result_bundle_dir=inputs.parameter_stability_result_bundle_dir,
        regime_breakdown_bundle_dir=inputs.regime_breakdown_bundle_dir,
        overfitting_risk_result_bundle_dir=inputs.overfitting_risk_result_bundle_dir,
    )
    with pytest.raises(ResearchValidityEvidenceError, match="artifact_kind"):
        verify_all_producer_inputs(bad_inputs)


def test_deterministic_input_artifact_ref_order(tmp_path, ssot_durable_output_dir) -> None:
    inputs = produce_full_research_validity_inputs(
        tmp_path, ssot_durable_output_dir, all_domains_pass=True
    )
    verified = verify_all_producer_inputs(inputs)
    evidence_a = build_research_validity_evidence_v1(inputs=inputs, verified=verified)
    evidence_b = build_research_validity_evidence_v1(inputs=inputs, verified=verified)
    assert evidence_a["input_artifact_refs"] == evidence_b["input_artifact_refs"]
    types = [item["artifact_type"] for item in evidence_a["input_artifact_refs"]]
    assert types == sorted(types)


@pytest.mark.parametrize(
    "missing_field",
    [
        "dataset_identity_bundle_dir",
        "partition_evidence_bundle_dir",
        "selection_procedure_bundle_dir",
        "walk_forward_result_bundle_dir",
    ],
)
def test_missing_required_input_bundle_rejected(
    tmp_path, ssot_durable_output_dir, missing_field: str
) -> None:
    inputs = produce_full_research_validity_inputs(
        tmp_path, ssot_durable_output_dir, all_domains_pass=True
    )
    missing_path = tmp_path / f"missing_{missing_field}"
    replacement = {missing_field: missing_path}
    bad_inputs = ResearchValidityProducerInputs(
        checkpoint_bundle_dir=inputs.checkpoint_bundle_dir,
        experiment_identity_bundle_dir=inputs.experiment_identity_bundle_dir,
        dataset_identity_bundle_dir=replacement.get(
            "dataset_identity_bundle_dir", inputs.dataset_identity_bundle_dir
        ),
        partition_evidence_bundle_dir=replacement.get(
            "partition_evidence_bundle_dir", inputs.partition_evidence_bundle_dir
        ),
        selection_procedure_bundle_dir=replacement.get(
            "selection_procedure_bundle_dir", inputs.selection_procedure_bundle_dir
        ),
        walk_forward_result_bundle_dir=replacement.get(
            "walk_forward_result_bundle_dir", inputs.walk_forward_result_bundle_dir
        ),
        cost_stress_result_bundle_dir=inputs.cost_stress_result_bundle_dir,
        slippage_stress_result_bundle_dir=inputs.slippage_stress_result_bundle_dir,
        funding_stress_result_bundle_dir=inputs.funding_stress_result_bundle_dir,
        parameter_stability_result_bundle_dir=inputs.parameter_stability_result_bundle_dir,
        regime_breakdown_bundle_dir=inputs.regime_breakdown_bundle_dir,
        overfitting_risk_result_bundle_dir=inputs.overfitting_risk_result_bundle_dir,
    )
    with pytest.raises(ResearchValidityEvidenceError):
        verify_all_producer_inputs(bad_inputs)


def test_authority_invariants_present(tmp_path, ssot_durable_output_dir) -> None:
    inputs = produce_full_research_validity_inputs(
        tmp_path, ssot_durable_output_dir, all_domains_pass=True
    )
    out = _durable_output(tmp_path, "inv")
    produce_research_validity_evidence_v1(inputs=inputs, output_dir=out)
    evidence = read_manifest(out / ARTIFACT_REL)
    assert (
        evidence["research_validity_authority_invariants"] == RESEARCH_VALIDITY_AUTHORITY_INVARIANTS
    )
