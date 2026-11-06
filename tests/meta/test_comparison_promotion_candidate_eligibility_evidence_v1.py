"""Contract tests for comparison promotion candidate eligibility evidence v1."""

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
    "tests.meta.comparison_promotion_candidate_eligibility_evidence_v1_fixtures",
]

from scripts.ops.primary_evidence_retention_v0 import verify_manifest_sha256, write_manifest_sha256
from src.meta.learning_loop.comparison_promotion_candidate_eligibility_evidence_v1 import (
    ARTIFACT_REL,
    AUTHORITY_LEVEL,
    CONTRACT_NAME,
    CONTRACT_VERSION,
    ELIGIBILITY_EVIDENCE_AUTHORITY_INVARIANTS,
    EVIDENCE_LEVEL,
    PRODUCER_VERSION,
    SELF_VERIFICATION_REL,
    ComparisonPromotionCandidateEligibilityEvidenceError,
    ComparisonPromotionCandidateEligibilityEvidenceInputs,
    build_comparison_promotion_candidate_eligibility_evidence_v1,
    produce_comparison_promotion_candidate_eligibility_evidence_v1,
    reverify_comparison_promotion_candidate_eligibility_evidence_v1,
    serialize_comparison_promotion_candidate_eligibility_evidence_v1,
    verify_eligibility_inputs,
)
from src.meta.learning_loop.comparison_promotion_candidate_identity_binding_v1 import (
    ARTIFACT_REL as IDENTITY_ARTIFACT_REL,
)
from src.meta.learning_loop.comparison_ssot_v1.io import read_manifest
from tests.meta.comparison_promotion_candidate_eligibility_evidence_v1_fixtures import (
    produce_candidate_identity_binding_bundle,
)


@pytest.fixture(autouse=True)
def _allow_tmp_output(monkeypatch: pytest.MonkeyPatch) -> None:
    targets = (
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


def _durable_output(tmp_path: Path, name: str = "eligibility_out") -> Path:
    root = tmp_path / "evidence_root"
    root.mkdir(exist_ok=True)
    return root / name


def _inputs(identity_bundle_dir: Path) -> ComparisonPromotionCandidateEligibilityEvidenceInputs:
    return ComparisonPromotionCandidateEligibilityEvidenceInputs(
        candidate_identity_binding_bundle_dir=identity_bundle_dir,
    )


def test_happy_path_metric_input_candidate(tmp_path, ssot_durable_output_dir) -> None:
    identity = produce_candidate_identity_binding_bundle(tmp_path, ssot_durable_output_dir)
    out = _durable_output(tmp_path)
    result = produce_comparison_promotion_candidate_eligibility_evidence_v1(
        inputs=_inputs(identity.candidate_identity_binding_bundle_dir),
        output_dir=out,
    )
    assert result.candidate_eligibility_status == "PASS"
    assert (out / ARTIFACT_REL).is_file()
    ok, _ = verify_manifest_sha256(out)
    assert ok is True
    reverify_comparison_promotion_candidate_eligibility_evidence_v1(output_dir=out)


def test_happy_path_candidate_lineage(tmp_path, ssot_durable_output_dir) -> None:
    identity = produce_candidate_identity_binding_bundle(
        tmp_path, ssot_durable_output_dir, use_candidate_lineage=True
    )
    out = _durable_output(tmp_path, "lineage_eligibility")
    result = produce_comparison_promotion_candidate_eligibility_evidence_v1(
        inputs=_inputs(identity.candidate_identity_binding_bundle_dir),
        output_dir=out,
    )
    assert result.candidate_eligibility_status == "PASS"
    evidence = read_manifest(out / ARTIFACT_REL)
    assert evidence["candidate_identity_source_type"] == "candidate_lineage_manifest_v1"


def test_deterministic_output_and_manifest(tmp_path, ssot_durable_output_dir) -> None:
    identity = produce_candidate_identity_binding_bundle(tmp_path, ssot_durable_output_dir)
    out_a = _durable_output(tmp_path, "det_a")
    out_b = _durable_output(tmp_path, "det_b")
    produce_comparison_promotion_candidate_eligibility_evidence_v1(
        inputs=_inputs(identity.candidate_identity_binding_bundle_dir), output_dir=out_a
    )
    produce_comparison_promotion_candidate_eligibility_evidence_v1(
        inputs=_inputs(identity.candidate_identity_binding_bundle_dir), output_dir=out_b
    )
    assert (out_a / ARTIFACT_REL).read_text(encoding="utf-8") == (out_b / ARTIFACT_REL).read_text(
        encoding="utf-8"
    )


def test_required_contract_fields(tmp_path, ssot_durable_output_dir) -> None:
    identity = produce_candidate_identity_binding_bundle(tmp_path, ssot_durable_output_dir)
    out = _durable_output(tmp_path, "fields")
    produce_comparison_promotion_candidate_eligibility_evidence_v1(
        inputs=_inputs(identity.candidate_identity_binding_bundle_dir), output_dir=out
    )
    evidence = read_manifest(out / ARTIFACT_REL)
    assert evidence["contract_name"] == CONTRACT_NAME
    assert evidence["contract_version"] == CONTRACT_VERSION
    assert evidence["producer_version"] == PRODUCER_VERSION
    assert evidence["evidence_level"] == EVIDENCE_LEVEL
    assert evidence["authority_level"] == AUTHORITY_LEVEL
    assert evidence["is_comparison_promotion_candidate_eligibility_evidence"] is True
    assert evidence["candidate_selection_status"] == "NOT_SELECTED"
    assert evidence["winner_selection_status"] == "NOT_SELECTED"
    assert evidence["candidate_acceptance_status"] == "NOT_ACCEPTED"
    assert evidence["promotion_candidate_constructed"] is False
    assert evidence["operational_filter_executed"] is False
    assert evidence["promotion_policy_executed"] is False
    assert evidence["configpatch_created"] is False
    assert len(evidence["input_artifact_refs"]) == 1


def test_non_authorizing_flags(tmp_path, ssot_durable_output_dir) -> None:
    identity = produce_candidate_identity_binding_bundle(tmp_path, ssot_durable_output_dir)
    out = _durable_output(tmp_path, "flags")
    produce_comparison_promotion_candidate_eligibility_evidence_v1(
        inputs=_inputs(identity.candidate_identity_binding_bundle_dir), output_dir=out
    )
    evidence = read_manifest(out / ARTIFACT_REL)
    assert evidence["eligibility_evidence_does_not_select"] is True
    assert evidence["eligibility_evidence_does_not_construct_promotion_candidate"] is True
    assert evidence["eligibility_evidence_does_not_execute_operational_filter"] is True
    assert evidence["eligibility_evidence_does_not_create_configpatch"] is True
    assert evidence["eligibility_evidence_authority_invariants"] == (
        ELIGIBILITY_EVIDENCE_AUTHORITY_INVARIANTS
    )


def test_self_verification_pass(tmp_path, ssot_durable_output_dir) -> None:
    identity = produce_candidate_identity_binding_bundle(tmp_path, ssot_durable_output_dir)
    out = _durable_output(tmp_path, "self")
    produce_comparison_promotion_candidate_eligibility_evidence_v1(
        inputs=_inputs(identity.candidate_identity_binding_bundle_dir), output_dir=out
    )
    self_payload = read_manifest(out / SELF_VERIFICATION_REL)
    assert self_payload["overall_status"] == "PASS"


def test_pass_reason_code(tmp_path, ssot_durable_output_dir) -> None:
    identity = produce_candidate_identity_binding_bundle(tmp_path, ssot_durable_output_dir)
    out = _durable_output(tmp_path, "reason")
    produce_comparison_promotion_candidate_eligibility_evidence_v1(
        inputs=_inputs(identity.candidate_identity_binding_bundle_dir), output_dir=out
    )
    evidence = read_manifest(out / ARTIFACT_REL)
    assert evidence["candidate_eligibility_reason_codes"] == ["ELIGIBLE_EVIDENCE_COMPLETE"]
    assert evidence["candidate_eligibility_reason_codes"] == sorted(
        evidence["candidate_eligibility_reason_codes"]
    )


def test_upstream_not_evaluable_propagates(tmp_path, ssot_durable_output_dir) -> None:
    identity = produce_candidate_identity_binding_bundle(
        tmp_path, ssot_durable_output_dir, all_domains_pass=False
    )
    out = _durable_output(tmp_path, "not_eval")
    result = produce_comparison_promotion_candidate_eligibility_evidence_v1(
        inputs=_inputs(identity.candidate_identity_binding_bundle_dir), output_dir=out
    )
    assert result.candidate_eligibility_status == "NOT_EVALUABLE"
    evidence = read_manifest(out / ARTIFACT_REL)
    assert "NOT_EVALUABLE_INSUFFICIENT_EVIDENCE" in evidence["candidate_eligibility_reason_codes"]


def test_input_bundle_missing(tmp_path) -> None:
    out = _durable_output(tmp_path)
    inputs = ComparisonPromotionCandidateEligibilityEvidenceInputs(
        candidate_identity_binding_bundle_dir=tmp_path / "missing",
    )
    with pytest.raises(
        ComparisonPromotionCandidateEligibilityEvidenceError, match="must be a directory"
    ):
        produce_comparison_promotion_candidate_eligibility_evidence_v1(
            inputs=inputs, output_dir=out
        )


def test_manifest_manipulated(tmp_path, ssot_durable_output_dir) -> None:
    identity = produce_candidate_identity_binding_bundle(tmp_path, ssot_durable_output_dir)
    bad_dir = ssot_durable_output_dir / "bad_identity"
    shutil.copytree(identity.candidate_identity_binding_bundle_dir, bad_dir)
    (bad_dir / "MANIFEST.sha256").write_text("deadbeef\n", encoding="utf-8")
    out = _durable_output(tmp_path)
    with pytest.raises(ComparisonPromotionCandidateEligibilityEvidenceError, match="MANIFEST"):
        produce_comparison_promotion_candidate_eligibility_evidence_v1(
            inputs=_inputs(bad_dir), output_dir=out
        )


def test_candidate_identity_not_bound(tmp_path, ssot_durable_output_dir) -> None:
    identity = produce_candidate_identity_binding_bundle(tmp_path, ssot_durable_output_dir)
    bad_dir = ssot_durable_output_dir / "bad_bound"
    shutil.copytree(identity.candidate_identity_binding_bundle_dir, bad_dir)
    evidence = read_manifest(bad_dir / IDENTITY_ARTIFACT_REL)
    evidence["candidate_identity_status"] = "NOT_BOUND"
    (bad_dir / IDENTITY_ARTIFACT_REL).write_text(json.dumps(evidence), encoding="utf-8")
    write_manifest_sha256(bad_dir)
    out = _durable_output(tmp_path)
    with pytest.raises(ComparisonPromotionCandidateEligibilityEvidenceError):
        produce_comparison_promotion_candidate_eligibility_evidence_v1(
            inputs=_inputs(bad_dir), output_dir=out
        )


def test_candidate_selection_detected_on_output_serialization() -> None:
    evidence = _minimal_evidence_payload()
    evidence["candidate_selection_status"] = "SELECTED"
    with pytest.raises(
        ComparisonPromotionCandidateEligibilityEvidenceError,
        match="candidate_selection_status",
    ):
        serialize_comparison_promotion_candidate_eligibility_evidence_v1(evidence)


def test_winner_selection_detected_on_output_serialization() -> None:
    evidence = _minimal_evidence_payload()
    evidence["winner_selection_status"] = "WINNER"
    with pytest.raises(
        ComparisonPromotionCandidateEligibilityEvidenceError,
        match="winner_selection_status",
    ):
        serialize_comparison_promotion_candidate_eligibility_evidence_v1(evidence)


def test_forbidden_capability_in_output_serialization() -> None:
    evidence = _minimal_evidence_payload()
    evidence["capabilities"] = ["CAN_PROMOTE_ARTIFACT"]
    with pytest.raises(
        ComparisonPromotionCandidateEligibilityEvidenceError, match="forbidden capability"
    ):
        serialize_comparison_promotion_candidate_eligibility_evidence_v1(evidence)


def test_forbidden_eligible_for_live_key_on_serialization() -> None:
    evidence = _minimal_evidence_payload()
    evidence["eligible_for_live"] = True
    with pytest.raises(ComparisonPromotionCandidateEligibilityEvidenceError, match="forbidden key"):
        serialize_comparison_promotion_candidate_eligibility_evidence_v1(evidence)


def test_promotion_candidate_constructed_flag_rejected() -> None:
    evidence = _minimal_evidence_payload()
    evidence["promotion_candidate_constructed"] = True
    with pytest.raises(
        ComparisonPromotionCandidateEligibilityEvidenceError,
        match="promotion_candidate_constructed",
    ):
        serialize_comparison_promotion_candidate_eligibility_evidence_v1(evidence)


def test_operational_filter_executed_flag_rejected() -> None:
    evidence = _minimal_evidence_payload()
    evidence["operational_filter_executed"] = True
    with pytest.raises(
        ComparisonPromotionCandidateEligibilityEvidenceError,
        match="operational_filter_executed",
    ):
        serialize_comparison_promotion_candidate_eligibility_evidence_v1(evidence)


def test_unsorted_reason_codes_rejected() -> None:
    evidence = _minimal_evidence_payload()
    evidence["candidate_eligibility_reason_codes"] = ["Z_CODE", "A_CODE"]
    with pytest.raises(
        ComparisonPromotionCandidateEligibilityEvidenceError, match="sorted deterministically"
    ):
        serialize_comparison_promotion_candidate_eligibility_evidence_v1(evidence)


def test_existing_output_fail_closed(tmp_path, ssot_durable_output_dir) -> None:
    identity = produce_candidate_identity_binding_bundle(tmp_path, ssot_durable_output_dir)
    out = _durable_output(tmp_path, "exists")
    out.mkdir()
    with pytest.raises(
        ComparisonPromotionCandidateEligibilityEvidenceError, match="already exists"
    ):
        produce_comparison_promotion_candidate_eligibility_evidence_v1(
            inputs=_inputs(identity.candidate_identity_binding_bundle_dir), output_dir=out
        )


def test_upstream_not_mutated(tmp_path, ssot_durable_output_dir) -> None:
    identity = produce_candidate_identity_binding_bundle(tmp_path, ssot_durable_output_dir)
    before = {
        rel.as_posix(): rel.read_bytes()
        for rel in identity.candidate_identity_binding_bundle_dir.rglob("*")
        if rel.is_file() and not rel.is_symlink()
    }
    out = _durable_output(tmp_path, "nomut")
    produce_comparison_promotion_candidate_eligibility_evidence_v1(
        inputs=_inputs(identity.candidate_identity_binding_bundle_dir), output_dir=out
    )
    after = {
        rel.as_posix(): rel.read_bytes()
        for rel in identity.candidate_identity_binding_bundle_dir.rglob("*")
        if rel.is_file() and not rel.is_symlink()
    }
    assert before == after


def test_ast_no_forbidden_runtime_imports() -> None:
    module_path = (
        Path(__file__).resolve().parents[2]
        / "src/meta/learning_loop/comparison_promotion_candidate_eligibility_evidence_v1.py"
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
        / "src/meta/learning_loop/comparison_promotion_candidate_eligibility_evidence_v1.py"
    )
    tree = ast.parse(module_path.read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module:
            assert node.module != "src.governance.promotion_loop.engine"
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            assert node.func.id != "filter_candidates_for_live"


def test_regression_identity_binding_contract_unchanged() -> None:
    from src.meta.learning_loop import comparison_promotion_candidate_identity_binding_v1 as mod

    assert mod.CONTRACT_NAME == "comparison_promotion_candidate_identity_binding_v1"
    assert mod.CONTRACT_VERSION == "v1"


def test_build_and_verify_inputs(tmp_path, ssot_durable_output_dir) -> None:
    identity = produce_candidate_identity_binding_bundle(tmp_path, ssot_durable_output_dir)
    verified = verify_eligibility_inputs(_inputs(identity.candidate_identity_binding_bundle_dir))
    evidence = build_comparison_promotion_candidate_eligibility_evidence_v1(
        identity_binding=verified,
    )
    assert evidence["candidate_eligibility_status"] == "PASS"


def test_digest_mismatch_on_replay(tmp_path, ssot_durable_output_dir) -> None:
    identity = produce_candidate_identity_binding_bundle(tmp_path, ssot_durable_output_dir)
    out = _durable_output(tmp_path, "digest")
    produce_comparison_promotion_candidate_eligibility_evidence_v1(
        inputs=_inputs(identity.candidate_identity_binding_bundle_dir), output_dir=out
    )
    evidence = read_manifest(out / ARTIFACT_REL)
    evidence["candidate_identity_binding_digest"] = "0" * 64
    (out / ARTIFACT_REL).write_text(json.dumps(evidence), encoding="utf-8")
    with pytest.raises(ComparisonPromotionCandidateEligibilityEvidenceError):
        reverify_comparison_promotion_candidate_eligibility_evidence_v1(output_dir=out)


def _minimal_evidence_payload() -> dict:
    return {
        "contract_name": CONTRACT_NAME,
        "contract_version": CONTRACT_VERSION,
        "producer_version": PRODUCER_VERSION,
        "evidence_level": EVIDENCE_LEVEL,
        "authority_level": AUTHORITY_LEVEL,
        "is_comparison_promotion_candidate_eligibility_evidence": True,
        "evidence_does_not_authorize_promotion": True,
        "evidence_does_not_authorize_runtime": True,
        "eligibility_evidence_does_not_select": True,
        "eligibility_evidence_does_not_choose_winner": True,
        "eligibility_evidence_does_not_accept": True,
        "eligibility_evidence_does_not_construct_promotion_candidate": True,
        "eligibility_evidence_does_not_execute_operational_filter": True,
        "eligibility_evidence_does_not_execute_policy": True,
        "eligibility_evidence_does_not_create_configpatch": True,
        "eligibility_evidence_does_not_modify_config": True,
        "eligibility_evidence_does_not_authorize_promotion": True,
        "eligibility_evidence_does_not_authorize_runtime": True,
        "eligibility_evidence_does_not_authorize_live": True,
        "eligibility_evidence_does_not_deploy": True,
        "eligibility_evidence_does_not_activate": True,
        "eligibility_evidence_does_not_create_order_intent": True,
        "eligibility_evidence_does_not_modify_trading_logic": True,
        "capabilities": [],
        "candidate_eligibility_status": "PASS",
        "candidate_eligibility_reason_codes": ["ELIGIBLE_EVIDENCE_COMPLETE"],
        "candidate_selection_status": "NOT_SELECTED",
        "winner_selection_status": "NOT_SELECTED",
        "candidate_acceptance_status": "NOT_ACCEPTED",
        "promotion_candidate_constructed": False,
        "operational_filter_executed": False,
        "promotion_policy_executed": False,
        "configpatch_created": False,
    }
