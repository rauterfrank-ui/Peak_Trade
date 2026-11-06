"""Contract tests for comparison completion promotion input binding v1."""

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
]

from scripts.ops.primary_evidence_retention_v0 import verify_manifest_sha256, write_manifest_sha256
from src.meta.learning_loop.comparison_completion_promotion_input_binding_v1 import (
    ARTIFACT_REL,
    AUTHORITY_LEVEL,
    CONTRACT_NAME,
    CONTRACT_VERSION,
    EVIDENCE_LEVEL,
    PRODUCER_VERSION,
    PROMOTION_INPUT_AUTHORITY_INVARIANTS,
    SELF_VERIFICATION_REL,
    ComparisonCompletionPromotionInputBindingError,
    ComparisonCompletionPromotionInputBindingInputs,
    build_comparison_completion_promotion_input_binding_v1,
    produce_comparison_completion_promotion_input_binding_v1,
    reverify_comparison_completion_promotion_input_binding_v1,
    serialize_comparison_completion_promotion_input_binding_v1,
    verify_binding_inputs,
    verify_upstream_binding_bundle,
)
from src.meta.learning_loop.comparison_completion_promotion_input_binding_v1 import (
    _derive_promotion_input_binding_status,
)
from src.meta.learning_loop.comparison_completion_research_validity_binding_v1 import (
    ARTIFACT_REL as UPSTREAM_ARTIFACT_REL,
    ComparisonCompletionResearchValidityBindingInputs,
    produce_comparison_completion_research_validity_binding_v1,
)
from src.meta.learning_loop.comparison_ssot_v1.io import read_manifest
from tests.meta.comparison_completion_promotion_input_binding_v1_fixtures import (
    produce_upstream_binding_bundle,
)


@pytest.fixture(autouse=True)
def _allow_tmp_output(monkeypatch: pytest.MonkeyPatch) -> None:
    targets = (
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


def _durable_output(tmp_path: Path, name: str = "promotion_input_out") -> Path:
    root = tmp_path / "evidence_root"
    root.mkdir(exist_ok=True)
    return root / name


def _inputs(upstream) -> ComparisonCompletionPromotionInputBindingInputs:
    return ComparisonCompletionPromotionInputBindingInputs(
        completion_validity_binding_bundle_dir=upstream.completion_validity_binding_bundle_dir,
    )


def test_happy_path_pass(tmp_path, ssot_durable_output_dir) -> None:
    upstream = produce_upstream_binding_bundle(tmp_path, ssot_durable_output_dir)
    out = _durable_output(tmp_path)
    result = produce_comparison_completion_promotion_input_binding_v1(
        inputs=_inputs(upstream), output_dir=out
    )
    assert result.promotion_input_binding_status == "PASS"
    assert result.shared_lineage_status == "PASS"
    assert (out / ARTIFACT_REL).is_file()
    ok, _ = verify_manifest_sha256(out)
    assert ok is True
    reverify_comparison_completion_promotion_input_binding_v1(output_dir=out)


def test_deterministic_output_and_manifest(tmp_path, ssot_durable_output_dir) -> None:
    upstream = produce_upstream_binding_bundle(tmp_path, ssot_durable_output_dir)
    out_a = _durable_output(tmp_path, "det_a")
    out_b = _durable_output(tmp_path, "det_b")
    produce_comparison_completion_promotion_input_binding_v1(
        inputs=_inputs(upstream), output_dir=out_a
    )
    produce_comparison_completion_promotion_input_binding_v1(
        inputs=_inputs(upstream), output_dir=out_b
    )
    assert (out_a / ARTIFACT_REL).read_text(encoding="utf-8") == (out_b / ARTIFACT_REL).read_text(
        encoding="utf-8"
    )
    assert (out_a / "MANIFEST.sha256").read_text(encoding="utf-8") == (
        out_b / "MANIFEST.sha256"
    ).read_text(encoding="utf-8")


def test_required_contract_fields(tmp_path, ssot_durable_output_dir) -> None:
    upstream = produce_upstream_binding_bundle(tmp_path, ssot_durable_output_dir)
    out = _durable_output(tmp_path, "fields")
    produce_comparison_completion_promotion_input_binding_v1(
        inputs=_inputs(upstream), output_dir=out
    )
    evidence = read_manifest(out / ARTIFACT_REL)
    assert evidence["contract_name"] == CONTRACT_NAME
    assert evidence["contract_version"] == CONTRACT_VERSION
    assert evidence["producer_version"] == PRODUCER_VERSION
    assert evidence["evidence_level"] == EVIDENCE_LEVEL
    assert evidence["authority_level"] == AUTHORITY_LEVEL
    assert evidence["is_comparison_completion_promotion_input_binding"] is True
    assert evidence["capabilities"] == []
    assert evidence["candidate_identity_status"] == "NOT_BOUND"
    assert evidence["winner_selection_status"] == "NOT_SELECTED"


def test_non_authorizing_flags(tmp_path, ssot_durable_output_dir) -> None:
    upstream = produce_upstream_binding_bundle(tmp_path, ssot_durable_output_dir)
    out = _durable_output(tmp_path, "flags")
    produce_comparison_completion_promotion_input_binding_v1(
        inputs=_inputs(upstream), output_dir=out
    )
    evidence = read_manifest(out / ARTIFACT_REL)
    assert evidence["promotion_input_does_not_select"] is True
    assert evidence["promotion_input_does_not_choose_winner"] is True
    assert evidence["promotion_input_does_not_create_configpatch"] is True
    assert evidence["promotion_input_does_not_execute_eligibility"] is True
    assert evidence["promotion_input_does_not_execute_policy"] is True
    assert evidence["promotion_input_does_not_authorize_promotion"] is True


def test_self_verification_pass(tmp_path, ssot_durable_output_dir) -> None:
    upstream = produce_upstream_binding_bundle(tmp_path, ssot_durable_output_dir)
    out = _durable_output(tmp_path, "self")
    produce_comparison_completion_promotion_input_binding_v1(
        inputs=_inputs(upstream), output_dir=out
    )
    self_payload = read_manifest(out / SELF_VERIFICATION_REL)
    assert self_payload["overall_status"] == "PASS"


def test_upstream_not_evaluable_propagates(tmp_path, ssot_durable_output_dir) -> None:
    upstream = produce_upstream_binding_bundle(
        tmp_path, ssot_durable_output_dir, all_domains_pass=False
    )
    out = _durable_output(tmp_path, "not_eval")
    result = produce_comparison_completion_promotion_input_binding_v1(
        inputs=_inputs(upstream), output_dir=out
    )
    assert result.promotion_input_binding_status == "NOT_EVALUABLE"
    evidence = read_manifest(out / ARTIFACT_REL)
    assert evidence["upstream_binding_status"] == "NOT_EVALUABLE"


def test_promotion_input_authority_invariants(tmp_path, ssot_durable_output_dir) -> None:
    upstream = produce_upstream_binding_bundle(tmp_path, ssot_durable_output_dir)
    out = _durable_output(tmp_path, "inv")
    produce_comparison_completion_promotion_input_binding_v1(
        inputs=_inputs(upstream), output_dir=out
    )
    evidence = read_manifest(out / ARTIFACT_REL)
    assert evidence["promotion_input_authority_invariants"] == PROMOTION_INPUT_AUTHORITY_INVARIANTS


def test_exactly_one_direct_input_ref(tmp_path, ssot_durable_output_dir) -> None:
    upstream = produce_upstream_binding_bundle(tmp_path, ssot_durable_output_dir)
    out = _durable_output(tmp_path, "one_input")
    produce_comparison_completion_promotion_input_binding_v1(
        inputs=_inputs(upstream), output_dir=out
    )
    evidence = read_manifest(out / ARTIFACT_REL)
    assert len(evidence["input_artifact_refs"]) == 1


def test_transitive_lineage_fields(tmp_path, ssot_durable_output_dir) -> None:
    upstream = produce_upstream_binding_bundle(tmp_path, ssot_durable_output_dir)
    out = _durable_output(tmp_path, "lineage")
    produce_comparison_completion_promotion_input_binding_v1(
        inputs=_inputs(upstream), output_dir=out
    )
    evidence = read_manifest(out / ARTIFACT_REL)
    assert evidence["comparison_completion_ref"]
    assert evidence["research_validity_ref"]
    assert evidence["comparison_checkpoint_ref"]
    assert evidence["experiment_identity_ref"]
    assert evidence["dataset_identity_ref"]
    assert evidence["completion_validity_binding_digest"]


def test_upstream_bundle_missing(tmp_path) -> None:
    out = _durable_output(tmp_path)
    inputs = ComparisonCompletionPromotionInputBindingInputs(
        completion_validity_binding_bundle_dir=tmp_path / "missing",
    )
    with pytest.raises(ComparisonCompletionPromotionInputBindingError, match="must be a directory"):
        produce_comparison_completion_promotion_input_binding_v1(inputs=inputs, output_dir=out)


def test_wrong_artifact_type(tmp_path, ssot_durable_output_dir) -> None:
    upstream = produce_upstream_binding_bundle(tmp_path, ssot_durable_output_dir)
    bad_dir = ssot_durable_output_dir / "wrong_type"
    shutil.copytree(upstream.completion_validity_binding_bundle_dir, bad_dir)
    evidence = read_manifest(bad_dir / UPSTREAM_ARTIFACT_REL)
    evidence["contract_name"] = "wrong_contract_v99"
    (bad_dir / UPSTREAM_ARTIFACT_REL).write_text(json.dumps(evidence), encoding="utf-8")
    write_manifest_sha256(bad_dir)
    out = _durable_output(tmp_path)
    with pytest.raises(ComparisonCompletionPromotionInputBindingError, match="contract_name"):
        produce_comparison_completion_promotion_input_binding_v1(
            inputs=ComparisonCompletionPromotionInputBindingInputs(
                completion_validity_binding_bundle_dir=bad_dir,
            ),
            output_dir=out,
        )


def test_manifest_missing(tmp_path, ssot_durable_output_dir) -> None:
    upstream = produce_upstream_binding_bundle(tmp_path, ssot_durable_output_dir)
    bad_dir = ssot_durable_output_dir / "no_manifest"
    shutil.copytree(upstream.completion_validity_binding_bundle_dir, bad_dir)
    (bad_dir / "MANIFEST.sha256").unlink()
    out = _durable_output(tmp_path)
    with pytest.raises(ComparisonCompletionPromotionInputBindingError):
        produce_comparison_completion_promotion_input_binding_v1(
            inputs=ComparisonCompletionPromotionInputBindingInputs(
                completion_validity_binding_bundle_dir=bad_dir,
            ),
            output_dir=out,
        )


def test_manifest_tampered(tmp_path, ssot_durable_output_dir) -> None:
    upstream = produce_upstream_binding_bundle(tmp_path, ssot_durable_output_dir)
    bad_dir = ssot_durable_output_dir / "tampered_manifest"
    shutil.copytree(upstream.completion_validity_binding_bundle_dir, bad_dir)
    (bad_dir / "MANIFEST.sha256").write_text("deadbeef\n", encoding="utf-8")
    out = _durable_output(tmp_path)
    with pytest.raises(ComparisonCompletionPromotionInputBindingError):
        produce_comparison_completion_promotion_input_binding_v1(
            inputs=ComparisonCompletionPromotionInputBindingInputs(
                completion_validity_binding_bundle_dir=bad_dir,
            ),
            output_dir=out,
        )


def test_self_verification_not_pass(tmp_path, ssot_durable_output_dir) -> None:
    upstream = produce_upstream_binding_bundle(tmp_path, ssot_durable_output_dir)
    bad_dir = ssot_durable_output_dir / "bad_self"
    shutil.copytree(upstream.completion_validity_binding_bundle_dir, bad_dir)
    self_payload = read_manifest(bad_dir / "SELF_VERIFICATION.json")
    self_payload["overall_status"] = "FAIL"
    (bad_dir / "SELF_VERIFICATION.json").write_text(json.dumps(self_payload), encoding="utf-8")
    write_manifest_sha256(bad_dir)
    out = _durable_output(tmp_path)
    with pytest.raises(ComparisonCompletionPromotionInputBindingError, match="overall_status"):
        produce_comparison_completion_promotion_input_binding_v1(
            inputs=ComparisonCompletionPromotionInputBindingInputs(
                completion_validity_binding_bundle_dir=bad_dir,
            ),
            output_dir=out,
        )


def test_wrong_evidence_level_upstream(tmp_path, ssot_durable_output_dir) -> None:
    upstream = produce_upstream_binding_bundle(tmp_path, ssot_durable_output_dir)
    bad_dir = ssot_durable_output_dir / "bad_level"
    shutil.copytree(upstream.completion_validity_binding_bundle_dir, bad_dir)
    evidence = read_manifest(bad_dir / UPSTREAM_ARTIFACT_REL)
    evidence["evidence_level"] = "LEVEL_9"
    (bad_dir / UPSTREAM_ARTIFACT_REL).write_text(json.dumps(evidence), encoding="utf-8")
    write_manifest_sha256(bad_dir)
    out = _durable_output(tmp_path)
    with pytest.raises(ComparisonCompletionPromotionInputBindingError, match="evidence_level"):
        produce_comparison_completion_promotion_input_binding_v1(
            inputs=ComparisonCompletionPromotionInputBindingInputs(
                completion_validity_binding_bundle_dir=bad_dir,
            ),
            output_dir=out,
        )


def test_upstream_binding_fail_status_propagation() -> None:
    status, reasons = _derive_promotion_input_binding_status(
        upstream_binding_status="FAIL",
        shared_lineage_status="PASS",
    )
    assert status == "FAIL"
    assert "UPSTREAM_BINDING_FAIL" in reasons


def test_tampered_upstream_binding_status_fail_closed(tmp_path, ssot_durable_output_dir) -> None:
    matched = produce_upstream_binding_bundle(tmp_path, ssot_durable_output_dir)
    bad_dir = ssot_durable_output_dir / "upstream_fail"
    shutil.copytree(matched.completion_validity_binding_bundle_dir, bad_dir)
    evidence = read_manifest(bad_dir / UPSTREAM_ARTIFACT_REL)
    evidence["binding_status"] = "FAIL"
    evidence["binding_reason_codes"] = ["FORCED_FAIL"]
    (bad_dir / UPSTREAM_ARTIFACT_REL).write_text(json.dumps(evidence), encoding="utf-8")
    write_manifest_sha256(bad_dir)
    out = _durable_output(tmp_path)
    with pytest.raises(ComparisonCompletionPromotionInputBindingError, match="integrity mismatch"):
        produce_comparison_completion_promotion_input_binding_v1(
            inputs=ComparisonCompletionPromotionInputBindingInputs(
                completion_validity_binding_bundle_dir=bad_dir,
            ),
            output_dir=out,
        )


def test_digest_mismatch_on_replay(tmp_path, ssot_durable_output_dir) -> None:
    upstream = produce_upstream_binding_bundle(tmp_path, ssot_durable_output_dir)
    out = _durable_output(tmp_path, "digest")
    produce_comparison_completion_promotion_input_binding_v1(
        inputs=_inputs(upstream), output_dir=out
    )
    evidence = read_manifest(out / ARTIFACT_REL)
    evidence["completion_validity_binding_digest"] = "0" * 64
    (out / ARTIFACT_REL).write_text(json.dumps(evidence), encoding="utf-8")
    with pytest.raises(ComparisonCompletionPromotionInputBindingError):
        reverify_comparison_completion_promotion_input_binding_v1(output_dir=out)


def test_forbidden_capability_in_output_serialization() -> None:
    evidence = {
        "contract_name": CONTRACT_NAME,
        "contract_version": CONTRACT_VERSION,
        "producer_version": PRODUCER_VERSION,
        "evidence_level": EVIDENCE_LEVEL,
        "is_comparison_completion_promotion_input_binding": True,
        "evidence_does_not_authorize_promotion": True,
        "evidence_does_not_authorize_runtime": True,
        "promotion_input_does_not_select": True,
        "promotion_input_does_not_accept": True,
        "promotion_input_does_not_choose_winner": True,
        "promotion_input_does_not_authorize_promotion": True,
        "promotion_input_does_not_execute_eligibility": True,
        "promotion_input_does_not_execute_policy": True,
        "promotion_input_does_not_create_configpatch": True,
        "promotion_input_does_not_modify_config": True,
        "promotion_input_does_not_deploy": True,
        "promotion_input_does_not_activate": True,
        "promotion_input_does_not_create_order_intent": True,
        "promotion_input_does_not_modify_trading_logic": True,
        "promotion_input_does_not_authorize_runtime": True,
        "capabilities": ["CAN_PROMOTE_ARTIFACT"],
        "promotion_input_binding_status": "PASS",
    }
    with pytest.raises(
        ComparisonCompletionPromotionInputBindingError, match="forbidden capability"
    ):
        serialize_comparison_completion_promotion_input_binding_v1(evidence)


def test_forbidden_winner_key_on_serialization() -> None:
    evidence = {
        "contract_name": CONTRACT_NAME,
        "contract_version": CONTRACT_VERSION,
        "producer_version": PRODUCER_VERSION,
        "evidence_level": EVIDENCE_LEVEL,
        "is_comparison_completion_promotion_input_binding": True,
        "evidence_does_not_authorize_promotion": True,
        "evidence_does_not_authorize_runtime": True,
        "promotion_input_does_not_select": True,
        "promotion_input_does_not_accept": True,
        "promotion_input_does_not_choose_winner": True,
        "promotion_input_does_not_authorize_promotion": True,
        "promotion_input_does_not_execute_eligibility": True,
        "promotion_input_does_not_execute_policy": True,
        "promotion_input_does_not_create_configpatch": True,
        "promotion_input_does_not_modify_config": True,
        "promotion_input_does_not_deploy": True,
        "promotion_input_does_not_activate": True,
        "promotion_input_does_not_create_order_intent": True,
        "promotion_input_does_not_modify_trading_logic": True,
        "promotion_input_does_not_authorize_runtime": True,
        "capabilities": [],
        "promotion_input_binding_status": "PASS",
        "winner": "bad",
    }
    with pytest.raises(ComparisonCompletionPromotionInputBindingError, match="forbidden key"):
        serialize_comparison_completion_promotion_input_binding_v1(evidence)


def test_forbidden_configpatch_key_on_serialization() -> None:
    evidence = {
        "contract_name": CONTRACT_NAME,
        "contract_version": CONTRACT_VERSION,
        "producer_version": PRODUCER_VERSION,
        "evidence_level": EVIDENCE_LEVEL,
        "is_comparison_completion_promotion_input_binding": True,
        "evidence_does_not_authorize_promotion": True,
        "evidence_does_not_authorize_runtime": True,
        "promotion_input_does_not_select": True,
        "promotion_input_does_not_accept": True,
        "promotion_input_does_not_choose_winner": True,
        "promotion_input_does_not_authorize_promotion": True,
        "promotion_input_does_not_execute_eligibility": True,
        "promotion_input_does_not_execute_policy": True,
        "promotion_input_does_not_create_configpatch": True,
        "promotion_input_does_not_modify_config": True,
        "promotion_input_does_not_deploy": True,
        "promotion_input_does_not_activate": True,
        "promotion_input_does_not_create_order_intent": True,
        "promotion_input_does_not_modify_trading_logic": True,
        "promotion_input_does_not_authorize_runtime": True,
        "capabilities": [],
        "promotion_input_binding_status": "PASS",
        "config_patch_manifest": {},
    }
    with pytest.raises(ComparisonCompletionPromotionInputBindingError, match="forbidden key"):
        serialize_comparison_completion_promotion_input_binding_v1(evidence)


def test_manipulated_non_authority_flags(tmp_path, ssot_durable_output_dir) -> None:
    upstream = produce_upstream_binding_bundle(tmp_path, ssot_durable_output_dir)
    out = _durable_output(tmp_path, "tamper_flags")
    produce_comparison_completion_promotion_input_binding_v1(
        inputs=_inputs(upstream), output_dir=out
    )
    evidence = read_manifest(out / ARTIFACT_REL)
    evidence["promotion_input_does_not_select"] = False
    (out / ARTIFACT_REL).write_text(json.dumps(evidence), encoding="utf-8")
    with pytest.raises(ComparisonCompletionPromotionInputBindingError):
        reverify_comparison_completion_promotion_input_binding_v1(output_dir=out)


def test_output_manipulation(tmp_path, ssot_durable_output_dir) -> None:
    upstream = produce_upstream_binding_bundle(tmp_path, ssot_durable_output_dir)
    out = _durable_output(tmp_path, "tamper")
    produce_comparison_completion_promotion_input_binding_v1(
        inputs=_inputs(upstream), output_dir=out
    )
    evidence = read_manifest(out / ARTIFACT_REL)
    evidence["is_comparison_completion_promotion_input_binding"] = False
    (out / ARTIFACT_REL).write_text(json.dumps(evidence), encoding="utf-8")
    with pytest.raises(ComparisonCompletionPromotionInputBindingError):
        reverify_comparison_completion_promotion_input_binding_v1(output_dir=out)


def test_existing_output_fail_closed(tmp_path, ssot_durable_output_dir) -> None:
    upstream = produce_upstream_binding_bundle(tmp_path, ssot_durable_output_dir)
    out = _durable_output(tmp_path, "exists")
    out.mkdir()
    with pytest.raises(ComparisonCompletionPromotionInputBindingError, match="already exists"):
        produce_comparison_completion_promotion_input_binding_v1(
            inputs=_inputs(upstream), output_dir=out
        )


def test_upstream_not_mutated(tmp_path, ssot_durable_output_dir) -> None:
    upstream = produce_upstream_binding_bundle(tmp_path, ssot_durable_output_dir)
    before = {
        rel.as_posix(): rel.read_bytes()
        for rel in upstream.completion_validity_binding_bundle_dir.rglob("*")
        if rel.is_file() and not rel.is_symlink()
    }
    out = _durable_output(tmp_path, "nomut")
    produce_comparison_completion_promotion_input_binding_v1(
        inputs=_inputs(upstream), output_dir=out
    )
    after = {
        rel.as_posix(): rel.read_bytes()
        for rel in upstream.completion_validity_binding_bundle_dir.rglob("*")
        if rel.is_file() and not rel.is_symlink()
    }
    assert before == after


def test_ast_no_forbidden_runtime_imports() -> None:
    module_path = (
        Path(__file__).resolve().parents[2]
        / "src/meta/learning_loop/comparison_completion_promotion_input_binding_v1.py"
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


def test_regression_upstream_binding_contract_unchanged() -> None:
    from src.meta.learning_loop import comparison_completion_research_validity_binding_v1 as mod

    assert mod.CONTRACT_NAME == "comparison_completion_research_validity_binding_v1"
    assert mod.CONTRACT_VERSION == "v1"


def test_missing_experiment_identity_upstream(tmp_path, ssot_durable_output_dir) -> None:
    upstream = produce_upstream_binding_bundle(tmp_path, ssot_durable_output_dir)
    bad_dir = ssot_durable_output_dir / "no_experiment"
    shutil.copytree(upstream.completion_validity_binding_bundle_dir, bad_dir)
    evidence = read_manifest(bad_dir / UPSTREAM_ARTIFACT_REL)
    evidence["experiment_identity_ref"] = ""
    (bad_dir / UPSTREAM_ARTIFACT_REL).write_text(json.dumps(evidence), encoding="utf-8")
    write_manifest_sha256(bad_dir)
    out = _durable_output(tmp_path)
    with pytest.raises(ComparisonCompletionPromotionInputBindingError, match="integrity mismatch"):
        produce_comparison_completion_promotion_input_binding_v1(
            inputs=ComparisonCompletionPromotionInputBindingInputs(
                completion_validity_binding_bundle_dir=bad_dir,
            ),
            output_dir=out,
        )


def test_build_and_verify_inputs(tmp_path, ssot_durable_output_dir) -> None:
    upstream_bundle = produce_upstream_binding_bundle(tmp_path, ssot_durable_output_dir)
    inputs = _inputs(upstream_bundle)
    verified = verify_binding_inputs(inputs)
    evidence = build_comparison_completion_promotion_input_binding_v1(upstream=verified)
    assert evidence["promotion_input_binding_status"] == "PASS"
    assert verified.contract_name == "comparison_completion_research_validity_binding_v1"


def test_eligible_for_live_forbidden_key() -> None:
    evidence = {
        "contract_name": CONTRACT_NAME,
        "contract_version": CONTRACT_VERSION,
        "producer_version": PRODUCER_VERSION,
        "evidence_level": EVIDENCE_LEVEL,
        "is_comparison_completion_promotion_input_binding": True,
        "evidence_does_not_authorize_promotion": True,
        "evidence_does_not_authorize_runtime": True,
        "promotion_input_does_not_select": True,
        "promotion_input_does_not_accept": True,
        "promotion_input_does_not_choose_winner": True,
        "promotion_input_does_not_authorize_promotion": True,
        "promotion_input_does_not_execute_eligibility": True,
        "promotion_input_does_not_execute_policy": True,
        "promotion_input_does_not_create_configpatch": True,
        "promotion_input_does_not_modify_config": True,
        "promotion_input_does_not_deploy": True,
        "promotion_input_does_not_activate": True,
        "promotion_input_does_not_create_order_intent": True,
        "promotion_input_does_not_modify_trading_logic": True,
        "promotion_input_does_not_authorize_runtime": True,
        "capabilities": [],
        "promotion_input_binding_status": "PASS",
        "eligible_for_live": True,
    }
    with pytest.raises(ComparisonCompletionPromotionInputBindingError, match="forbidden key"):
        serialize_comparison_completion_promotion_input_binding_v1(evidence)
