"""Contract tests for comparison promotion candidate identity binding v1."""

from __future__ import annotations

import ast
import json
import shutil
from pathlib import Path

import pytest

pytest_plugins = [
    "tests.meta.comparison_ssot_v1_fixtures",
    "tests.meta.comparison_completion_research_validity_binding_v1_fixtures",
    "tests.meta.comparison_completion_promotion_input_binding_v1_fixtures",
    "tests.meta.comparison_promotion_candidate_identity_binding_v1_fixtures",
]

from scripts.ops.primary_evidence_retention_v0 import verify_manifest_sha256, write_manifest_sha256
from src.meta.learning_loop.comparison_completion_promotion_input_binding_v1 import (
    ARTIFACT_REL as PROMOTION_INPUT_ARTIFACT_REL,
)
from src.meta.learning_loop.comparison_promotion_candidate_identity_binding_v1 import (
    ARTIFACT_REL,
    AUTHORITY_LEVEL,
    CONTRACT_NAME,
    CONTRACT_VERSION,
    EVIDENCE_LEVEL,
    PRODUCER_VERSION,
    CANDIDATE_IDENTITY_BINDING_AUTHORITY_INVARIANTS,
    SELF_VERIFICATION_REL,
    ComparisonPromotionCandidateIdentityBindingError,
    ComparisonPromotionCandidateIdentityBindingInputs,
    build_comparison_promotion_candidate_identity_binding_v1,
    produce_comparison_promotion_candidate_identity_binding_v1,
    reverify_comparison_promotion_candidate_identity_binding_v1,
    serialize_comparison_promotion_candidate_identity_binding_v1,
    verify_binding_inputs,
)
from src.meta.learning_loop.comparison_ssot_v1.io import read_manifest
from tests.meta.comparison_promotion_candidate_identity_binding_v1_fixtures import (
    CANDIDATE_LINEAGE_ARTIFACT_REL,
    FIXED_NOW,
    produce_candidate_lineage_candidate_bundle,
    produce_metric_input_candidate_bundle,
    produce_promotion_input_binding_bundle,
)


@pytest.fixture(autouse=True)
def _allow_tmp_output(monkeypatch: pytest.MonkeyPatch) -> None:
    targets = (
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


def _durable_output(tmp_path: Path, name: str = "candidate_identity_binding_out") -> Path:
    root = tmp_path / "evidence_root"
    root.mkdir(exist_ok=True)
    return root / name


def _inputs(promotion_input, candidate) -> ComparisonPromotionCandidateIdentityBindingInputs:
    return ComparisonPromotionCandidateIdentityBindingInputs(
        promotion_input_binding_bundle_dir=promotion_input.promotion_input_binding_bundle_dir,
        candidate_identity_bundle_dir=candidate.candidate_identity_bundle_dir,
    )


def test_happy_path_metric_input_candidate(tmp_path, ssot_durable_output_dir) -> None:
    promotion_input = produce_promotion_input_binding_bundle(tmp_path, ssot_durable_output_dir)
    candidate = produce_metric_input_candidate_bundle(
        tmp_path, ssot_durable_output_dir, promotion_input=promotion_input
    )
    out = _durable_output(tmp_path)
    result = produce_comparison_promotion_candidate_identity_binding_v1(
        inputs=_inputs(promotion_input, candidate), output_dir=out
    )
    assert result.candidate_identity_binding_status == "PASS"
    assert result.shared_lineage_status == "PASS"
    assert (out / ARTIFACT_REL).is_file()
    ok, _ = verify_manifest_sha256(out)
    assert ok is True
    reverify_comparison_promotion_candidate_identity_binding_v1(output_dir=out)


def test_happy_path_candidate_lineage(tmp_path, ssot_durable_output_dir) -> None:
    promotion_input = produce_promotion_input_binding_bundle(tmp_path, ssot_durable_output_dir)
    candidate = produce_candidate_lineage_candidate_bundle(
        ssot_durable_output_dir, promotion_input=promotion_input
    )
    out = _durable_output(tmp_path, "lineage_out")
    result = produce_comparison_promotion_candidate_identity_binding_v1(
        inputs=_inputs(promotion_input, candidate), output_dir=out
    )
    assert result.candidate_identity_binding_status == "PASS"
    evidence = read_manifest(out / ARTIFACT_REL)
    assert evidence["candidate_identity_source_type"] == "candidate_lineage_manifest_v1"


def test_deterministic_output_and_manifest(tmp_path, ssot_durable_output_dir) -> None:
    promotion_input = produce_promotion_input_binding_bundle(tmp_path, ssot_durable_output_dir)
    candidate = produce_metric_input_candidate_bundle(
        tmp_path, ssot_durable_output_dir, promotion_input=promotion_input
    )
    out_a = _durable_output(tmp_path, "det_a")
    out_b = _durable_output(tmp_path, "det_b")
    produce_comparison_promotion_candidate_identity_binding_v1(
        inputs=_inputs(promotion_input, candidate), output_dir=out_a
    )
    produce_comparison_promotion_candidate_identity_binding_v1(
        inputs=_inputs(promotion_input, candidate), output_dir=out_b
    )
    assert (out_a / ARTIFACT_REL).read_text(encoding="utf-8") == (out_b / ARTIFACT_REL).read_text(
        encoding="utf-8"
    )


def test_required_contract_fields(tmp_path, ssot_durable_output_dir) -> None:
    promotion_input = produce_promotion_input_binding_bundle(tmp_path, ssot_durable_output_dir)
    candidate = produce_metric_input_candidate_bundle(
        tmp_path, ssot_durable_output_dir, promotion_input=promotion_input
    )
    out = _durable_output(tmp_path, "fields")
    produce_comparison_promotion_candidate_identity_binding_v1(
        inputs=_inputs(promotion_input, candidate), output_dir=out
    )
    evidence = read_manifest(out / ARTIFACT_REL)
    assert evidence["contract_name"] == CONTRACT_NAME
    assert evidence["contract_version"] == CONTRACT_VERSION
    assert evidence["producer_version"] == PRODUCER_VERSION
    assert evidence["evidence_level"] == EVIDENCE_LEVEL
    assert evidence["authority_level"] == AUTHORITY_LEVEL
    assert evidence["is_comparison_promotion_candidate_identity_binding"] is True
    assert evidence["candidate_identity_status"] == "BOUND"
    assert evidence["candidate_selection_status"] == "NOT_SELECTED"
    assert evidence["winner_selection_status"] == "NOT_SELECTED"
    assert len(evidence["input_artifact_refs"]) == 2


def test_non_authorizing_flags(tmp_path, ssot_durable_output_dir) -> None:
    promotion_input = produce_promotion_input_binding_bundle(tmp_path, ssot_durable_output_dir)
    candidate = produce_metric_input_candidate_bundle(
        tmp_path, ssot_durable_output_dir, promotion_input=promotion_input
    )
    out = _durable_output(tmp_path, "flags")
    produce_comparison_promotion_candidate_identity_binding_v1(
        inputs=_inputs(promotion_input, candidate), output_dir=out
    )
    evidence = read_manifest(out / ARTIFACT_REL)
    assert evidence["candidate_identity_binding_does_not_select"] is True
    assert evidence["candidate_identity_binding_does_not_choose_winner"] is True
    assert evidence["candidate_identity_binding_does_not_create_configpatch"] is True


def test_self_verification_pass(tmp_path, ssot_durable_output_dir) -> None:
    promotion_input = produce_promotion_input_binding_bundle(tmp_path, ssot_durable_output_dir)
    candidate = produce_metric_input_candidate_bundle(
        tmp_path, ssot_durable_output_dir, promotion_input=promotion_input
    )
    out = _durable_output(tmp_path, "self")
    produce_comparison_promotion_candidate_identity_binding_v1(
        inputs=_inputs(promotion_input, candidate), output_dir=out
    )
    self_payload = read_manifest(out / SELF_VERIFICATION_REL)
    assert self_payload["overall_status"] == "PASS"


def test_upstream_not_evaluable_propagates(tmp_path, ssot_durable_output_dir) -> None:
    promotion_input = produce_promotion_input_binding_bundle(
        tmp_path, ssot_durable_output_dir, all_domains_pass=False
    )
    candidate = produce_metric_input_candidate_bundle(
        tmp_path, ssot_durable_output_dir, promotion_input=promotion_input
    )
    out = _durable_output(tmp_path, "not_eval")
    result = produce_comparison_promotion_candidate_identity_binding_v1(
        inputs=_inputs(promotion_input, candidate), output_dir=out
    )
    assert result.candidate_identity_binding_status == "NOT_EVALUABLE"


def test_promotion_input_bundle_missing(tmp_path, ssot_durable_output_dir) -> None:
    promotion_input = produce_promotion_input_binding_bundle(tmp_path, ssot_durable_output_dir)
    candidate = produce_metric_input_candidate_bundle(
        tmp_path, ssot_durable_output_dir, promotion_input=promotion_input
    )
    out = _durable_output(tmp_path)
    inputs = ComparisonPromotionCandidateIdentityBindingInputs(
        promotion_input_binding_bundle_dir=tmp_path / "missing",
        candidate_identity_bundle_dir=candidate.candidate_identity_bundle_dir,
    )
    with pytest.raises(
        ComparisonPromotionCandidateIdentityBindingError, match="must be a directory"
    ):
        produce_comparison_promotion_candidate_identity_binding_v1(inputs=inputs, output_dir=out)


def test_candidate_bundle_missing(tmp_path, ssot_durable_output_dir) -> None:
    promotion_input = produce_promotion_input_binding_bundle(tmp_path, ssot_durable_output_dir)
    out = _durable_output(tmp_path)
    inputs = ComparisonPromotionCandidateIdentityBindingInputs(
        promotion_input_binding_bundle_dir=promotion_input.promotion_input_binding_bundle_dir,
        candidate_identity_bundle_dir=tmp_path / "missing",
    )
    with pytest.raises(
        ComparisonPromotionCandidateIdentityBindingError, match="must be a directory"
    ):
        produce_comparison_promotion_candidate_identity_binding_v1(inputs=inputs, output_dir=out)


def test_promotion_input_not_bound_status_fail_closed(tmp_path, ssot_durable_output_dir) -> None:
    promotion_input = produce_promotion_input_binding_bundle(tmp_path, ssot_durable_output_dir)
    candidate = produce_metric_input_candidate_bundle(
        tmp_path, ssot_durable_output_dir, promotion_input=promotion_input
    )
    bad_dir = ssot_durable_output_dir / "bad_promo"
    shutil.copytree(promotion_input.promotion_input_binding_bundle_dir, bad_dir)
    evidence = read_manifest(bad_dir / PROMOTION_INPUT_ARTIFACT_REL)
    evidence["candidate_identity_status"] = "BOUND"
    (bad_dir / PROMOTION_INPUT_ARTIFACT_REL).write_text(json.dumps(evidence), encoding="utf-8")
    write_manifest_sha256(bad_dir)
    out = _durable_output(tmp_path)
    with pytest.raises(ComparisonPromotionCandidateIdentityBindingError, match="NOT_BOUND"):
        produce_comparison_promotion_candidate_identity_binding_v1(
            inputs=ComparisonPromotionCandidateIdentityBindingInputs(
                promotion_input_binding_bundle_dir=bad_dir,
                candidate_identity_bundle_dir=candidate.candidate_identity_bundle_dir,
            ),
            output_dir=out,
        )


def test_lineage_mismatch_candidate_lineage(tmp_path, ssot_durable_output_dir) -> None:
    from src.governance.promotion_loop.candidate_lineage_manifest_v1 import (
        LineageRefType,
        LineageRelation,
        build_candidate_lineage_manifest_v1_from_producer_input,
        serialize_candidate_lineage_manifest_v1,
    )

    promotion_input = produce_promotion_input_binding_bundle(tmp_path, ssot_durable_output_dir)
    bad_candidate = ssot_durable_output_dir / "bad_candidate"
    bad_candidate.mkdir(parents=True, exist_ok=True)
    manifest = build_candidate_lineage_manifest_v1_from_producer_input(
        {
            "lineage_manifest_id": "dddddddd-dddd-4ddd-8ddd-dddddddddddd",
            "candidate_id": "candidate-wrong-lineage-001",
            "candidate_type": "config_patch_bundle",
            "candidate_contract_ref": "eeeeeeee-eeee-4eee-8eee-eeeeeeeeeeee",
            "refs": [
                {
                    "ref_type": LineageRefType.EXPERIMENT.value,
                    "ref_id": "wrong-experiment-id",
                    "relation": LineageRelation.SOURCES.value,
                    "owner_domain": "experiments/base",
                    "required": True,
                }
            ],
            "created_at": FIXED_NOW.isoformat(),
            "created_by": "comparison_promotion_candidate_identity_binding_v1_fixtures",
        },
        created_at=FIXED_NOW,
    )
    artifact_path = bad_candidate / CANDIDATE_LINEAGE_ARTIFACT_REL
    artifact_path.write_text(serialize_candidate_lineage_manifest_v1(manifest), encoding="utf-8")
    write_manifest_sha256(bad_candidate)
    out = _durable_output(tmp_path)
    result = produce_comparison_promotion_candidate_identity_binding_v1(
        inputs=ComparisonPromotionCandidateIdentityBindingInputs(
            promotion_input_binding_bundle_dir=promotion_input.promotion_input_binding_bundle_dir,
            candidate_identity_bundle_dir=bad_candidate,
        ),
        output_dir=out,
    )
    assert result.candidate_identity_binding_status == "FAIL"
    assert result.shared_lineage_status == "FAIL"


def test_forbidden_ranked_input_ids_key_on_serialization() -> None:
    evidence = {
        "contract_name": CONTRACT_NAME,
        "contract_version": CONTRACT_VERSION,
        "producer_version": PRODUCER_VERSION,
        "evidence_level": EVIDENCE_LEVEL,
        "is_comparison_promotion_candidate_identity_binding": True,
        "evidence_does_not_authorize_promotion": True,
        "evidence_does_not_authorize_runtime": True,
        "candidate_identity_binding_does_not_select": True,
        "candidate_identity_binding_does_not_choose_winner": True,
        "candidate_identity_binding_does_not_accept": True,
        "candidate_identity_binding_does_not_execute_eligibility": True,
        "candidate_identity_binding_does_not_execute_policy": True,
        "candidate_identity_binding_does_not_create_configpatch": True,
        "candidate_identity_binding_does_not_modify_config": True,
        "candidate_identity_binding_does_not_deploy": True,
        "candidate_identity_binding_does_not_activate": True,
        "candidate_identity_binding_does_not_create_order_intent": True,
        "candidate_identity_binding_does_not_modify_trading_logic": True,
        "candidate_identity_binding_does_not_authorize_runtime": True,
        "capabilities": [],
        "candidate_identity_binding_status": "PASS",
        "candidate_selection_status": "NOT_SELECTED",
        "winner_selection_status": "NOT_SELECTED",
        "ranked_input_ids": ["x"],
    }
    with pytest.raises(ComparisonPromotionCandidateIdentityBindingError, match="forbidden key"):
        serialize_comparison_promotion_candidate_identity_binding_v1(evidence)


def test_forbidden_capability_in_output_serialization() -> None:
    evidence = {
        "contract_name": CONTRACT_NAME,
        "contract_version": CONTRACT_VERSION,
        "producer_version": PRODUCER_VERSION,
        "evidence_level": EVIDENCE_LEVEL,
        "is_comparison_promotion_candidate_identity_binding": True,
        "evidence_does_not_authorize_promotion": True,
        "evidence_does_not_authorize_runtime": True,
        "candidate_identity_binding_does_not_select": True,
        "candidate_identity_binding_does_not_choose_winner": True,
        "candidate_identity_binding_does_not_accept": True,
        "candidate_identity_binding_does_not_execute_eligibility": True,
        "candidate_identity_binding_does_not_execute_policy": True,
        "candidate_identity_binding_does_not_create_configpatch": True,
        "candidate_identity_binding_does_not_modify_config": True,
        "candidate_identity_binding_does_not_deploy": True,
        "candidate_identity_binding_does_not_activate": True,
        "candidate_identity_binding_does_not_create_order_intent": True,
        "candidate_identity_binding_does_not_modify_trading_logic": True,
        "candidate_identity_binding_does_not_authorize_runtime": True,
        "capabilities": ["CAN_PROMOTE_ARTIFACT"],
        "candidate_identity_binding_status": "PASS",
        "candidate_selection_status": "NOT_SELECTED",
        "winner_selection_status": "NOT_SELECTED",
    }
    with pytest.raises(
        ComparisonPromotionCandidateIdentityBindingError, match="forbidden capability"
    ):
        serialize_comparison_promotion_candidate_identity_binding_v1(evidence)


def test_existing_output_fail_closed(tmp_path, ssot_durable_output_dir) -> None:
    promotion_input = produce_promotion_input_binding_bundle(tmp_path, ssot_durable_output_dir)
    candidate = produce_metric_input_candidate_bundle(
        tmp_path, ssot_durable_output_dir, promotion_input=promotion_input
    )
    out = _durable_output(tmp_path, "exists")
    out.mkdir()
    with pytest.raises(ComparisonPromotionCandidateIdentityBindingError, match="already exists"):
        produce_comparison_promotion_candidate_identity_binding_v1(
            inputs=_inputs(promotion_input, candidate), output_dir=out
        )


def test_upstream_not_mutated(tmp_path, ssot_durable_output_dir) -> None:
    promotion_input = produce_promotion_input_binding_bundle(tmp_path, ssot_durable_output_dir)
    candidate = produce_metric_input_candidate_bundle(
        tmp_path, ssot_durable_output_dir, promotion_input=promotion_input
    )
    promo_before = {
        rel.as_posix(): rel.read_bytes()
        for rel in promotion_input.promotion_input_binding_bundle_dir.rglob("*")
        if rel.is_file() and not rel.is_symlink()
    }
    cand_before = {
        rel.as_posix(): rel.read_bytes()
        for rel in candidate.candidate_identity_bundle_dir.rglob("*")
        if rel.is_file() and not rel.is_symlink()
    }
    out = _durable_output(tmp_path, "nomut")
    produce_comparison_promotion_candidate_identity_binding_v1(
        inputs=_inputs(promotion_input, candidate), output_dir=out
    )
    promo_after = {
        rel.as_posix(): rel.read_bytes()
        for rel in promotion_input.promotion_input_binding_bundle_dir.rglob("*")
        if rel.is_file() and not rel.is_symlink()
    }
    cand_after = {
        rel.as_posix(): rel.read_bytes()
        for rel in candidate.candidate_identity_bundle_dir.rglob("*")
        if rel.is_file() and not rel.is_symlink()
    }
    assert promo_before == promo_after
    assert cand_before == cand_after


def test_ast_no_forbidden_runtime_imports() -> None:
    module_path = (
        Path(__file__).resolve().parents[2]
        / "src/meta/learning_loop/comparison_promotion_candidate_identity_binding_v1.py"
    )
    tree = ast.parse(module_path.read_text(encoding="utf-8"))
    modules: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            modules.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            modules.add(node.module)
    forbidden = {"src.execution", "src.risk", "src.governance.promotion_loop.engine", "mlflow"}
    assert not modules & forbidden


def test_regression_promotion_input_binding_contract_unchanged() -> None:
    from src.meta.learning_loop import comparison_completion_promotion_input_binding_v1 as mod

    assert mod.CONTRACT_NAME == "comparison_completion_promotion_input_binding_v1"
    assert mod.CONTRACT_VERSION == "v1"


def test_build_and_verify_inputs(tmp_path, ssot_durable_output_dir) -> None:
    promotion_input = produce_promotion_input_binding_bundle(tmp_path, ssot_durable_output_dir)
    candidate = produce_metric_input_candidate_bundle(
        tmp_path, ssot_durable_output_dir, promotion_input=promotion_input
    )
    inputs = _inputs(promotion_input, candidate)
    promo_verified, candidate_verified = verify_binding_inputs(inputs)
    evidence = build_comparison_promotion_candidate_identity_binding_v1(
        promotion_input=promo_verified,
        candidate=candidate_verified,
    )
    assert evidence["candidate_identity_binding_status"] == "PASS"
    assert evidence["candidate_identity_binding_authority_invariants"] == (
        CANDIDATE_IDENTITY_BINDING_AUTHORITY_INVARIANTS
    )


def test_digest_mismatch_on_replay(tmp_path, ssot_durable_output_dir) -> None:
    promotion_input = produce_promotion_input_binding_bundle(tmp_path, ssot_durable_output_dir)
    candidate = produce_metric_input_candidate_bundle(
        tmp_path, ssot_durable_output_dir, promotion_input=promotion_input
    )
    out = _durable_output(tmp_path, "digest")
    produce_comparison_promotion_candidate_identity_binding_v1(
        inputs=_inputs(promotion_input, candidate), output_dir=out
    )
    evidence = read_manifest(out / ARTIFACT_REL)
    evidence["promotion_input_binding_digest"] = "0" * 64
    (out / ARTIFACT_REL).write_text(json.dumps(evidence), encoding="utf-8")
    with pytest.raises(ComparisonPromotionCandidateIdentityBindingError):
        reverify_comparison_promotion_candidate_identity_binding_v1(output_dir=out)
