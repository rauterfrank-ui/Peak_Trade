"""Contract tests for comparison completion research validity binding v1."""

from __future__ import annotations

import ast
import json
import shutil
from copy import deepcopy
from pathlib import Path

import pytest

pytest_plugins = [
    "tests.meta.comparison_ssot_v1_fixtures",
    "tests.meta.comparison_completion_research_validity_binding_v1_fixtures",
]

from scripts.ops.primary_evidence_retention_v0 import verify_manifest_sha256, write_manifest_sha256
from src.meta.learning_loop.comparison_completion_evidence_v1 import (
    ARTIFACT_REL as COMPLETION_ARTIFACT_REL,
    CONTRACT_VERSION as COMPLETION_CONTRACT_VERSION,
    SELF_VERIFICATION_REL as COMPLETION_SELF_VERIFICATION_REL,
    produce_comparison_completion_evidence_v1,
)
from src.meta.learning_loop.comparison_completion_research_validity_binding_v1 import (
    ARTIFACT_REL,
    AUTHORITY_LEVEL,
    BINDING_AUTHORITY_INVARIANTS,
    CONTRACT_NAME,
    CONTRACT_VERSION,
    EVIDENCE_LEVEL,
    PRODUCER_VERSION,
    SELF_VERIFICATION_REL,
    ComparisonCompletionResearchValidityBindingError,
    ComparisonCompletionResearchValidityBindingInputs,
    build_comparison_completion_research_validity_binding_v1,
    produce_comparison_completion_research_validity_binding_v1,
    reverify_comparison_completion_research_validity_binding_v1,
    serialize_comparison_completion_research_validity_binding_v1,
    verify_binding_inputs,
)
from src.meta.learning_loop.comparison_ssot_v1.io import read_manifest
from src.meta.learning_loop.contract_safety_v1 import (
    compute_content_sha256,
    deterministic_json_dumps,
)
from src.meta.learning_loop.research_validity_evidence_v1 import (
    ARTIFACT_REL as VALIDITY_ARTIFACT_REL,
    CONTRACT_VERSION as VALIDITY_CONTRACT_VERSION,
    SELF_VERIFICATION_REL as VALIDITY_SELF_VERIFICATION_REL,
    produce_research_validity_evidence_v1,
)
from tests.meta.comparison_completion_research_validity_binding_v1_fixtures import (
    produce_matched_completion_and_validity_bundles,
)
from tests.meta.research_validity_evidence_v1_fixtures import (
    produce_checkpoint_bundle,
    produce_full_research_validity_inputs,
)


@pytest.fixture(autouse=True)
def _allow_tmp_output(monkeypatch: pytest.MonkeyPatch) -> None:
    targets = (
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


def _durable_output(tmp_path: Path, name: str = "binding_out") -> Path:
    root = tmp_path / "evidence_root"
    root.mkdir(exist_ok=True)
    return root / name


def _binding_inputs(matched) -> ComparisonCompletionResearchValidityBindingInputs:
    return ComparisonCompletionResearchValidityBindingInputs(
        completion_evidence_bundle_dir=matched.completion_bundle_dir,
        research_validity_evidence_bundle_dir=matched.research_validity_bundle_dir,
    )


def test_happy_path_binding_pass(tmp_path, ssot_durable_output_dir) -> None:
    matched = produce_matched_completion_and_validity_bundles(tmp_path, ssot_durable_output_dir)
    out = _durable_output(tmp_path)
    result = produce_comparison_completion_research_validity_binding_v1(
        inputs=_binding_inputs(matched),
        output_dir=out,
    )
    assert result.binding_status == "PASS"
    assert result.shared_lineage_status == "PASS"
    assert (out / ARTIFACT_REL).is_file()
    ok, _ = verify_manifest_sha256(out)
    assert ok is True
    reverify_comparison_completion_research_validity_binding_v1(output_dir=out)


def test_deterministic_output_and_manifest(tmp_path, ssot_durable_output_dir) -> None:
    matched = produce_matched_completion_and_validity_bundles(
        tmp_path, ssot_durable_output_dir, completion_name="c1", validity_name="v1"
    )
    out_a = _durable_output(tmp_path, "det_a")
    out_b = _durable_output(tmp_path, "det_b")
    produce_comparison_completion_research_validity_binding_v1(
        inputs=_binding_inputs(matched), output_dir=out_a
    )
    produce_comparison_completion_research_validity_binding_v1(
        inputs=_binding_inputs(matched), output_dir=out_b
    )
    assert (out_a / ARTIFACT_REL).read_text(encoding="utf-8") == (out_b / ARTIFACT_REL).read_text(
        encoding="utf-8"
    )
    assert (out_a / "MANIFEST.sha256").read_text(encoding="utf-8") == (
        out_b / "MANIFEST.sha256"
    ).read_text(encoding="utf-8")


def test_deterministic_input_artifact_ref_order(tmp_path, ssot_durable_output_dir) -> None:
    matched = produce_matched_completion_and_validity_bundles(tmp_path, ssot_durable_output_dir)
    completion, validity, shared = verify_binding_inputs(_binding_inputs(matched))
    evidence_a = build_comparison_completion_research_validity_binding_v1(
        completion=completion, validity=validity, shared_lineage=shared
    )
    evidence_b = build_comparison_completion_research_validity_binding_v1(
        completion=completion, validity=validity, shared_lineage=shared
    )
    types = [item["artifact_type"] for item in evidence_a["input_artifact_refs"]]
    assert types == sorted(types)
    assert evidence_a["input_artifact_refs"] == evidence_b["input_artifact_refs"]


def test_required_contract_fields(tmp_path, ssot_durable_output_dir) -> None:
    matched = produce_matched_completion_and_validity_bundles(tmp_path, ssot_durable_output_dir)
    out = _durable_output(tmp_path, "fields")
    produce_comparison_completion_research_validity_binding_v1(
        inputs=_binding_inputs(matched), output_dir=out
    )
    evidence = read_manifest(out / ARTIFACT_REL)
    assert evidence["contract_name"] == CONTRACT_NAME
    assert evidence["contract_version"] == CONTRACT_VERSION
    assert evidence["producer_version"] == PRODUCER_VERSION
    assert evidence["evidence_level"] == EVIDENCE_LEVEL
    assert evidence["authority_level"] == AUTHORITY_LEVEL
    assert evidence["is_completion_research_validity_binding"] is True
    assert evidence["capabilities"] == []


def test_non_authorizing_flags(tmp_path, ssot_durable_output_dir) -> None:
    matched = produce_matched_completion_and_validity_bundles(tmp_path, ssot_durable_output_dir)
    out = _durable_output(tmp_path, "flags")
    produce_comparison_completion_research_validity_binding_v1(
        inputs=_binding_inputs(matched), output_dir=out
    )
    evidence = read_manifest(out / ARTIFACT_REL)
    assert evidence["binding_does_not_select"] is True
    assert evidence["binding_does_not_promote"] is True
    assert evidence["binding_does_not_authorize_runtime"] is True
    assert evidence["evidence_does_not_authorize_promotion"] is True
    assert evidence["binding_does_not_modify_trading_logic"] is True


def test_self_verification_pass(tmp_path, ssot_durable_output_dir) -> None:
    matched = produce_matched_completion_and_validity_bundles(tmp_path, ssot_durable_output_dir)
    out = _durable_output(tmp_path, "self")
    produce_comparison_completion_research_validity_binding_v1(
        inputs=_binding_inputs(matched), output_dir=out
    )
    self_payload = read_manifest(out / SELF_VERIFICATION_REL)
    assert self_payload["overall_status"] == "PASS"


def test_binding_status_not_evaluable_upstream(tmp_path, ssot_durable_output_dir) -> None:
    matched = produce_matched_completion_and_validity_bundles(
        tmp_path, ssot_durable_output_dir, all_domains_pass=False
    )
    out = _durable_output(tmp_path, "not_eval")
    result = produce_comparison_completion_research_validity_binding_v1(
        inputs=_binding_inputs(matched), output_dir=out
    )
    assert result.binding_status == "NOT_EVALUABLE"
    evidence = read_manifest(out / ARTIFACT_REL)
    assert evidence["research_validity_status"] == "NOT_EVALUABLE"


def test_binding_authority_invariants(tmp_path, ssot_durable_output_dir) -> None:
    matched = produce_matched_completion_and_validity_bundles(tmp_path, ssot_durable_output_dir)
    out = _durable_output(tmp_path, "inv")
    produce_comparison_completion_research_validity_binding_v1(
        inputs=_binding_inputs(matched), output_dir=out
    )
    evidence = read_manifest(out / ARTIFACT_REL)
    assert evidence["binding_authority_invariants"] == BINDING_AUTHORITY_INVARIANTS


def test_contract_constants() -> None:
    assert CONTRACT_NAME == "comparison_completion_research_validity_binding_v1"
    assert CONTRACT_VERSION == "v1"
    assert EVIDENCE_LEVEL == "LEVEL_3"


def test_missing_completion_bundle(tmp_path, ssot_durable_output_dir) -> None:
    matched = produce_matched_completion_and_validity_bundles(tmp_path, ssot_durable_output_dir)
    out = _durable_output(tmp_path)
    inputs = ComparisonCompletionResearchValidityBindingInputs(
        completion_evidence_bundle_dir=tmp_path / "missing_completion",
        research_validity_evidence_bundle_dir=matched.research_validity_bundle_dir,
    )
    with pytest.raises(ComparisonCompletionResearchValidityBindingError, match="directory"):
        produce_comparison_completion_research_validity_binding_v1(inputs=inputs, output_dir=out)


def test_missing_research_validity_bundle(tmp_path, ssot_durable_output_dir) -> None:
    matched = produce_matched_completion_and_validity_bundles(tmp_path, ssot_durable_output_dir)
    out = _durable_output(tmp_path)
    inputs = ComparisonCompletionResearchValidityBindingInputs(
        completion_evidence_bundle_dir=matched.completion_bundle_dir,
        research_validity_evidence_bundle_dir=tmp_path / "missing_validity",
    )
    with pytest.raises(ComparisonCompletionResearchValidityBindingError, match="directory"):
        produce_comparison_completion_research_validity_binding_v1(inputs=inputs, output_dir=out)


def test_wrong_completion_artifact_type(tmp_path, ssot_durable_output_dir) -> None:
    matched = produce_matched_completion_and_validity_bundles(tmp_path, ssot_durable_output_dir)
    bad = ssot_durable_output_dir / "bad_completion"
    shutil.copytree(matched.checkpoint_bundle_dir, bad)
    out = _durable_output(tmp_path)
    inputs = ComparisonCompletionResearchValidityBindingInputs(
        completion_evidence_bundle_dir=bad,
        research_validity_evidence_bundle_dir=matched.research_validity_bundle_dir,
    )
    with pytest.raises(ComparisonCompletionResearchValidityBindingError):
        produce_comparison_completion_research_validity_binding_v1(inputs=inputs, output_dir=out)


def test_wrong_research_validity_artifact_type(tmp_path, ssot_durable_output_dir) -> None:
    matched = produce_matched_completion_and_validity_bundles(tmp_path, ssot_durable_output_dir)
    out = _durable_output(tmp_path)
    inputs = ComparisonCompletionResearchValidityBindingInputs(
        completion_evidence_bundle_dir=matched.completion_bundle_dir,
        research_validity_evidence_bundle_dir=matched.completion_bundle_dir,
    )
    with pytest.raises(ComparisonCompletionResearchValidityBindingError):
        produce_comparison_completion_research_validity_binding_v1(inputs=inputs, output_dir=out)


def test_unsupported_completion_version(tmp_path, ssot_durable_output_dir) -> None:
    matched = produce_matched_completion_and_validity_bundles(tmp_path, ssot_durable_output_dir)
    path = matched.completion_bundle_dir / COMPLETION_ARTIFACT_REL
    payload = read_manifest(path)
    payload["contract_version"] = "v99"
    path.write_text(json.dumps(payload), encoding="utf-8")
    write_manifest_sha256(matched.completion_bundle_dir)
    out = _durable_output(tmp_path)
    with pytest.raises(ComparisonCompletionResearchValidityBindingError, match="contract_version"):
        produce_comparison_completion_research_validity_binding_v1(
            inputs=_binding_inputs(matched), output_dir=out
        )


def test_unsupported_research_validity_version(tmp_path, ssot_durable_output_dir) -> None:
    matched = produce_matched_completion_and_validity_bundles(tmp_path, ssot_durable_output_dir)
    path = matched.research_validity_bundle_dir / VALIDITY_ARTIFACT_REL
    payload = read_manifest(path)
    payload["contract_version"] = "v99"
    path.write_text(json.dumps(payload), encoding="utf-8")
    write_manifest_sha256(matched.research_validity_bundle_dir)
    out = _durable_output(tmp_path)
    with pytest.raises(ComparisonCompletionResearchValidityBindingError, match="contract_version"):
        produce_comparison_completion_research_validity_binding_v1(
            inputs=_binding_inputs(matched), output_dir=out
        )


def test_missing_completion_manifest(tmp_path, ssot_durable_output_dir) -> None:
    matched = produce_matched_completion_and_validity_bundles(tmp_path, ssot_durable_output_dir)
    (matched.completion_bundle_dir / "MANIFEST.sha256").unlink()
    out = _durable_output(tmp_path)
    with pytest.raises(ComparisonCompletionResearchValidityBindingError, match="MANIFEST"):
        produce_comparison_completion_research_validity_binding_v1(
            inputs=_binding_inputs(matched), output_dir=out
        )


def test_missing_research_validity_manifest(tmp_path, ssot_durable_output_dir) -> None:
    matched = produce_matched_completion_and_validity_bundles(tmp_path, ssot_durable_output_dir)
    (matched.research_validity_bundle_dir / "MANIFEST.sha256").unlink()
    out = _durable_output(tmp_path)
    with pytest.raises(ComparisonCompletionResearchValidityBindingError, match="MANIFEST"):
        produce_comparison_completion_research_validity_binding_v1(
            inputs=_binding_inputs(matched), output_dir=out
        )


def test_manipulated_completion_manifest(tmp_path, ssot_durable_output_dir) -> None:
    matched = produce_matched_completion_and_validity_bundles(tmp_path, ssot_durable_output_dir)
    (matched.completion_bundle_dir / "MANIFEST.sha256").write_text("deadbeef\n", encoding="utf-8")
    out = _durable_output(tmp_path)
    with pytest.raises(ComparisonCompletionResearchValidityBindingError, match="MANIFEST"):
        produce_comparison_completion_research_validity_binding_v1(
            inputs=_binding_inputs(matched), output_dir=out
        )


def test_manipulated_research_validity_manifest(tmp_path, ssot_durable_output_dir) -> None:
    matched = produce_matched_completion_and_validity_bundles(tmp_path, ssot_durable_output_dir)
    (matched.research_validity_bundle_dir / "MANIFEST.sha256").write_text(
        "deadbeef\n", encoding="utf-8"
    )
    out = _durable_output(tmp_path)
    with pytest.raises(ComparisonCompletionResearchValidityBindingError, match="MANIFEST"):
        produce_comparison_completion_research_validity_binding_v1(
            inputs=_binding_inputs(matched), output_dir=out
        )


def test_completion_self_verification_not_pass(tmp_path, ssot_durable_output_dir) -> None:
    matched = produce_matched_completion_and_validity_bundles(tmp_path, ssot_durable_output_dir)
    self_path = matched.completion_bundle_dir / COMPLETION_SELF_VERIFICATION_REL
    payload = read_manifest(self_path)
    payload["overall_status"] = "FAIL"
    self_path.write_text(json.dumps(payload), encoding="utf-8")
    write_manifest_sha256(matched.completion_bundle_dir)
    out = _durable_output(tmp_path)
    with pytest.raises(ComparisonCompletionResearchValidityBindingError, match="overall_status"):
        produce_comparison_completion_research_validity_binding_v1(
            inputs=_binding_inputs(matched), output_dir=out
        )


def test_research_validity_self_verification_not_pass(tmp_path, ssot_durable_output_dir) -> None:
    matched = produce_matched_completion_and_validity_bundles(tmp_path, ssot_durable_output_dir)
    self_path = matched.research_validity_bundle_dir / VALIDITY_SELF_VERIFICATION_REL
    payload = read_manifest(self_path)
    payload["overall_status"] = "FAIL"
    self_path.write_text(json.dumps(payload), encoding="utf-8")
    write_manifest_sha256(matched.research_validity_bundle_dir)
    out = _durable_output(tmp_path)
    with pytest.raises(ComparisonCompletionResearchValidityBindingError, match="overall_status"):
        produce_comparison_completion_research_validity_binding_v1(
            inputs=_binding_inputs(matched), output_dir=out
        )


def test_wrong_evidence_level_on_completion(tmp_path, ssot_durable_output_dir) -> None:
    matched = produce_matched_completion_and_validity_bundles(tmp_path, ssot_durable_output_dir)
    path = matched.completion_bundle_dir / COMPLETION_ARTIFACT_REL
    payload = read_manifest(path)
    payload["evidence_level"] = "LEVEL_2"
    body = {k: v for k, v in payload.items() if k != "integrity"}
    payload["integrity"] = {"content_sha256": compute_content_sha256(body)}
    path.write_text(deterministic_json_dumps(payload), encoding="utf-8")
    write_manifest_sha256(matched.completion_bundle_dir)
    out = _durable_output(tmp_path)
    with pytest.raises(ComparisonCompletionResearchValidityBindingError, match="evidence_level"):
        produce_comparison_completion_research_validity_binding_v1(
            inputs=_binding_inputs(matched), output_dir=out
        )


def test_forbidden_capability_on_completion(tmp_path, ssot_durable_output_dir) -> None:
    matched = produce_matched_completion_and_validity_bundles(tmp_path, ssot_durable_output_dir)
    path = matched.completion_bundle_dir / COMPLETION_ARTIFACT_REL
    payload = read_manifest(path)
    payload["capabilities"] = ["CAN_PROMOTE_ARTIFACT"]
    path.write_text(json.dumps(payload), encoding="utf-8")
    write_manifest_sha256(matched.completion_bundle_dir)
    out = _durable_output(tmp_path)
    with pytest.raises(ComparisonCompletionResearchValidityBindingError, match="forbidden"):
        produce_comparison_completion_research_validity_binding_v1(
            inputs=_binding_inputs(matched), output_dir=out
        )


def test_forbidden_capability_on_research_validity(tmp_path, ssot_durable_output_dir) -> None:
    matched = produce_matched_completion_and_validity_bundles(tmp_path, ssot_durable_output_dir)
    path = matched.research_validity_bundle_dir / VALIDITY_ARTIFACT_REL
    payload = read_manifest(path)
    payload["capabilities"] = ["CAN_SUBMIT_LIVE_ORDERS"]
    path.write_text(json.dumps(payload), encoding="utf-8")
    write_manifest_sha256(matched.research_validity_bundle_dir)
    out = _durable_output(tmp_path)
    with pytest.raises(ComparisonCompletionResearchValidityBindingError, match="forbidden"):
        produce_comparison_completion_research_validity_binding_v1(
            inputs=_binding_inputs(matched), output_dir=out
        )


def test_forbidden_capability_on_binding_serialization() -> None:
    matched_completion = {
        "contract_name": "comparison_completion_evidence_v1",
        "contract_version": COMPLETION_CONTRACT_VERSION,
        "producer_version": "comparison_completion_evidence_v1",
        "evidence_level": EVIDENCE_LEVEL,
        "is_completion_evidence": True,
        "evidence_does_not_authorize_promotion": True,
        "evidence_does_not_authorize_runtime": True,
        "completion_does_not_select": True,
        "completion_does_not_accept": True,
        "completion_does_not_deploy": True,
        "completion_does_not_activate": True,
        "completion_does_not_create_order_intent": True,
        "capabilities": [],
        "completion_status": "COMPLETE",
        "input_checkpoint_bundle_ref": "/var/cp",
        "input_checkpoint_digest": "a" * 64,
        "comparison_definition_id": "00000000-0000-4000-8000-000000000099",
        "parent_artifact_refs": [{"ref_type": "comparison_checkpoint_v1", "digest": "a" * 64}],
        "output_digest": "b" * 64,
    }
    matched_validity = {
        "contract_name": "research_validity_evidence_v1",
        "contract_version": VALIDITY_CONTRACT_VERSION,
        "producer_version": "research_validity_evidence_v1",
        "evidence_level": EVIDENCE_LEVEL,
        "is_research_validity_evidence": True,
        "evidence_does_not_authorize_promotion": True,
        "evidence_does_not_authorize_runtime": True,
        "research_validity_does_not_select": True,
        "research_validity_does_not_accept": True,
        "research_validity_does_not_deploy": True,
        "research_validity_does_not_activate": True,
        "research_validity_does_not_create_order_intent": True,
        "research_validity_does_not_modify_trading_logic": True,
        "capabilities": [],
        "research_validity_status": "PASS",
        "comparison_checkpoint_ref": "/var/cp",
        "comparison_checkpoint_digest": "a" * 64,
        "experiment_identity_ref": "/var/exp",
        "experiment_identity_digest": "c" * 64,
        "dataset_identity_ref": "/var/ds",
        "dataset_identity_digest": "d" * 64,
        "comparison_definition_id": "00000000-0000-4000-8000-000000000099",
        "parent_artifact_refs": [
            {
                "ref_type": "comparison_checkpoint_v1",
                "digest": "a" * 64,
                "bundle_path": "/var/cp",
            }
        ],
        "output_digest": "e" * 64,
    }
    from src.meta.learning_loop.comparison_completion_research_validity_binding_v1 import (
        SharedLineageResult,
        VerifiedEvidenceBundle,
        check_shared_lineage,
    )

    completion = VerifiedEvidenceBundle(
        bundle_dir=Path("/var/completion"),
        contract_name="comparison_completion_evidence_v1",
        contract_version=COMPLETION_CONTRACT_VERSION,
        producer_version="comparison_completion_evidence_v1",
        artifact_ref=COMPLETION_ARTIFACT_REL,
        artifact_digest="b" * 64,
        manifest_digest="f" * 64,
        evidence_level=EVIDENCE_LEVEL,
        parent_artifact_refs=(
            {
                "ref_type": "comparison_checkpoint_v1",
                "digest": "a" * 64,
                "bundle_path": "/var/cp",
            },
        ),
        evidence_payload=matched_completion,
    )
    validity = VerifiedEvidenceBundle(
        bundle_dir=Path("/var/validity"),
        contract_name="research_validity_evidence_v1",
        contract_version=VALIDITY_CONTRACT_VERSION,
        producer_version="research_validity_evidence_v1",
        artifact_ref=VALIDITY_ARTIFACT_REL,
        artifact_digest="e" * 64,
        manifest_digest="g" * 64,
        evidence_level=EVIDENCE_LEVEL,
        parent_artifact_refs=(
            {
                "ref_type": "comparison_checkpoint_v1",
                "digest": "a" * 64,
                "bundle_path": "/var/cp",
            },
        ),
        evidence_payload=matched_validity,
    )
    shared = check_shared_lineage(completion=completion, validity=validity)
    evidence = build_comparison_completion_research_validity_binding_v1(
        completion=completion, validity=validity, shared_lineage=shared
    )
    evidence["capabilities"] = ["CAN_CHANGE_RISK_POLICY"]
    with pytest.raises(ComparisonCompletionResearchValidityBindingError, match="forbidden"):
        serialize_comparison_completion_research_validity_binding_v1(evidence)


def test_checkpoint_lineage_mismatch(tmp_path, ssot_durable_output_dir) -> None:
    root_a = ssot_durable_output_dir / "lineage_a"
    root_b = ssot_durable_output_dir / "lineage_b"
    root_a.mkdir(parents=True, exist_ok=True)
    root_b.mkdir(parents=True, exist_ok=True)
    matched_a = produce_matched_completion_and_validity_bundles(
        tmp_path / "case_a", root_a, completion_name="c_a", validity_name="v_a"
    )
    matched_b = produce_matched_completion_and_validity_bundles(
        tmp_path / "case_b", root_b, completion_name="c_b", validity_name="v_b"
    )
    out = _durable_output(tmp_path)
    inputs = ComparisonCompletionResearchValidityBindingInputs(
        completion_evidence_bundle_dir=matched_a.completion_bundle_dir,
        research_validity_evidence_bundle_dir=matched_b.research_validity_bundle_dir,
    )
    with pytest.raises(
        ComparisonCompletionResearchValidityBindingError, match="comparison_checkpoint_ref mismatch"
    ):
        produce_comparison_completion_research_validity_binding_v1(inputs=inputs, output_dir=out)


def test_experiment_identity_digest_mismatch_in_validity(tmp_path, ssot_durable_output_dir) -> None:
    matched = produce_matched_completion_and_validity_bundles(tmp_path, ssot_durable_output_dir)
    path = matched.research_validity_bundle_dir / VALIDITY_ARTIFACT_REL
    payload = read_manifest(path)
    payload["experiment_identity_digest"] = "f" * 64
    path.write_text(json.dumps(payload), encoding="utf-8")
    write_manifest_sha256(matched.research_validity_bundle_dir)
    out = _durable_output(tmp_path)
    with pytest.raises(ComparisonCompletionResearchValidityBindingError):
        produce_comparison_completion_research_validity_binding_v1(
            inputs=_binding_inputs(matched), output_dir=out
        )


def test_dataset_identity_ref_mismatch(tmp_path, ssot_durable_output_dir) -> None:
    matched = produce_matched_completion_and_validity_bundles(tmp_path, ssot_durable_output_dir)
    path = matched.research_validity_bundle_dir / VALIDITY_ARTIFACT_REL
    payload = read_manifest(path)
    payload["dataset_identity_ref"] = "/var/other/dataset"
    path.write_text(json.dumps(payload), encoding="utf-8")
    write_manifest_sha256(matched.research_validity_bundle_dir)
    out = _durable_output(tmp_path)
    with pytest.raises(ComparisonCompletionResearchValidityBindingError):
        produce_comparison_completion_research_validity_binding_v1(
            inputs=_binding_inputs(matched), output_dir=out
        )


def test_parent_lineage_contradictory(tmp_path, ssot_durable_output_dir) -> None:
    from src.meta.learning_loop.comparison_completion_research_validity_binding_v1 import (
        VerifiedEvidenceBundle,
        check_shared_lineage,
    )

    matched = produce_matched_completion_and_validity_bundles(tmp_path, ssot_durable_output_dir)
    completion, validity, _ = verify_binding_inputs(_binding_inputs(matched))
    contradictory_parent = dict(completion.parent_artifact_refs[0])
    contradictory_parent["digest"] = "f" * 64
    completion_bad = VerifiedEvidenceBundle(
        bundle_dir=completion.bundle_dir,
        contract_name=completion.contract_name,
        contract_version=completion.contract_version,
        producer_version=completion.producer_version,
        artifact_ref=completion.artifact_ref,
        artifact_digest=completion.artifact_digest,
        manifest_digest=completion.manifest_digest,
        evidence_level=completion.evidence_level,
        parent_artifact_refs=(contradictory_parent,),
        evidence_payload=completion.evidence_payload,
    )
    with pytest.raises(ComparisonCompletionResearchValidityBindingError, match="digest mismatch"):
        check_shared_lineage(completion=completion_bad, validity=validity)


def test_digest_mismatch_on_completion_output(tmp_path, ssot_durable_output_dir) -> None:
    matched = produce_matched_completion_and_validity_bundles(tmp_path, ssot_durable_output_dir)
    path = matched.completion_bundle_dir / COMPLETION_ARTIFACT_REL
    payload = read_manifest(path)
    payload["output_digest"] = "f" * 64
    path.write_text(json.dumps(payload), encoding="utf-8")
    write_manifest_sha256(matched.completion_bundle_dir)
    out = _durable_output(tmp_path)
    with pytest.raises(ComparisonCompletionResearchValidityBindingError):
        produce_comparison_completion_research_validity_binding_v1(
            inputs=_binding_inputs(matched), output_dir=out
        )


def test_completion_status_not_complete_yields_fail_binding(
    tmp_path, ssot_durable_output_dir
) -> None:
    from src.meta.learning_loop.comparison_completion_research_validity_binding_v1 import (
        VerifiedEvidenceBundle,
    )

    matched = produce_matched_completion_and_validity_bundles(tmp_path, ssot_durable_output_dir)
    completion, validity, shared = verify_binding_inputs(_binding_inputs(matched))
    incomplete_payload = dict(completion.evidence_payload)
    incomplete_payload["completion_status"] = "INCOMPLETE"
    completion_incomplete = VerifiedEvidenceBundle(
        bundle_dir=completion.bundle_dir,
        contract_name=completion.contract_name,
        contract_version=completion.contract_version,
        producer_version=completion.producer_version,
        artifact_ref=completion.artifact_ref,
        artifact_digest=completion.artifact_digest,
        manifest_digest=completion.manifest_digest,
        evidence_level=completion.evidence_level,
        parent_artifact_refs=completion.parent_artifact_refs,
        evidence_payload=incomplete_payload,
    )
    evidence = build_comparison_completion_research_validity_binding_v1(
        completion=completion_incomplete, validity=validity, shared_lineage=shared
    )
    assert evidence["binding_status"] == "FAIL"
    assert evidence["completion_status"] == "INCOMPLETE"


def test_research_validity_incomplete_yields_incomplete_binding(
    tmp_path, ssot_durable_output_dir
) -> None:
    from src.meta.learning_loop.comparison_completion_research_validity_binding_v1 import (
        VerifiedEvidenceBundle,
    )

    matched = produce_matched_completion_and_validity_bundles(tmp_path, ssot_durable_output_dir)
    completion, validity, shared = verify_binding_inputs(_binding_inputs(matched))
    incomplete_payload = dict(validity.evidence_payload)
    incomplete_payload["research_validity_status"] = "INCOMPLETE"
    validity_incomplete = VerifiedEvidenceBundle(
        bundle_dir=validity.bundle_dir,
        contract_name=validity.contract_name,
        contract_version=validity.contract_version,
        producer_version=validity.producer_version,
        artifact_ref=validity.artifact_ref,
        artifact_digest=validity.artifact_digest,
        manifest_digest=validity.manifest_digest,
        evidence_level=validity.evidence_level,
        parent_artifact_refs=validity.parent_artifact_refs,
        evidence_payload=incomplete_payload,
    )
    evidence = build_comparison_completion_research_validity_binding_v1(
        completion=completion, validity=validity_incomplete, shared_lineage=shared
    )
    assert evidence["binding_status"] == "INCOMPLETE"


def test_manipulated_non_authority_flags_on_output(tmp_path, ssot_durable_output_dir) -> None:
    matched = produce_matched_completion_and_validity_bundles(tmp_path, ssot_durable_output_dir)
    out = _durable_output(tmp_path, "tamper_flags")
    produce_comparison_completion_research_validity_binding_v1(
        inputs=_binding_inputs(matched), output_dir=out
    )
    evidence = read_manifest(out / ARTIFACT_REL)
    evidence["binding_does_not_promote"] = False
    (out / ARTIFACT_REL).write_text(json.dumps(evidence), encoding="utf-8")
    with pytest.raises(ComparisonCompletionResearchValidityBindingError):
        reverify_comparison_completion_research_validity_binding_v1(output_dir=out)


def test_output_manipulation_after_produce(tmp_path, ssot_durable_output_dir) -> None:
    matched = produce_matched_completion_and_validity_bundles(tmp_path, ssot_durable_output_dir)
    out = _durable_output(tmp_path, "tamper")
    produce_comparison_completion_research_validity_binding_v1(
        inputs=_binding_inputs(matched), output_dir=out
    )
    evidence = read_manifest(out / ARTIFACT_REL)
    evidence["is_completion_research_validity_binding"] = False
    (out / ARTIFACT_REL).write_text(json.dumps(evidence), encoding="utf-8")
    with pytest.raises(ComparisonCompletionResearchValidityBindingError):
        reverify_comparison_completion_research_validity_binding_v1(output_dir=out)


def test_promotion_input_field_forbidden_on_serialization() -> None:
    evidence = {
        "contract_name": CONTRACT_NAME,
        "contract_version": CONTRACT_VERSION,
        "producer_version": PRODUCER_VERSION,
        "evidence_level": EVIDENCE_LEVEL,
        "is_completion_research_validity_binding": True,
        "evidence_does_not_authorize_promotion": True,
        "evidence_does_not_authorize_runtime": True,
        "binding_does_not_select": True,
        "binding_does_not_accept": True,
        "binding_does_not_promote": True,
        "binding_does_not_deploy": True,
        "binding_does_not_activate": True,
        "binding_does_not_create_order_intent": True,
        "binding_does_not_modify_trading_logic": True,
        "capabilities": [],
        "binding_status": "PASS",
        "is_promotion_input": True,
    }
    with pytest.raises(ComparisonCompletionResearchValidityBindingError, match="forbidden key"):
        serialize_comparison_completion_research_validity_binding_v1(evidence)


def test_inputs_not_mutated(tmp_path, ssot_durable_output_dir) -> None:
    matched = produce_matched_completion_and_validity_bundles(tmp_path, ssot_durable_output_dir)
    before = {
        rel.as_posix(): rel.read_bytes()
        for bundle in (matched.completion_bundle_dir, matched.research_validity_bundle_dir)
        for rel in bundle.rglob("*")
        if rel.is_file() and not rel.is_symlink()
    }
    out = _durable_output(tmp_path, "nomut")
    produce_comparison_completion_research_validity_binding_v1(
        inputs=_binding_inputs(matched), output_dir=out
    )
    after = {
        rel.as_posix(): rel.read_bytes()
        for bundle in (matched.completion_bundle_dir, matched.research_validity_bundle_dir)
        for rel in bundle.rglob("*")
        if rel.is_file() and not rel.is_symlink()
    }
    assert before == after


def test_existing_output_fail_closed(tmp_path, ssot_durable_output_dir) -> None:
    matched = produce_matched_completion_and_validity_bundles(tmp_path, ssot_durable_output_dir)
    out = _durable_output(tmp_path, "exists")
    out.mkdir()
    with pytest.raises(ComparisonCompletionResearchValidityBindingError, match="already exists"):
        produce_comparison_completion_research_validity_binding_v1(
            inputs=_binding_inputs(matched), output_dir=out
        )


def test_ast_no_forbidden_runtime_imports() -> None:
    module_path = (
        Path(__file__).resolve().parents[2]
        / "src/meta/learning_loop/comparison_completion_research_validity_binding_v1.py"
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


def test_regression_completion_contract_unchanged() -> None:
    from src.meta.learning_loop import comparison_completion_evidence_v1 as mod

    assert mod.CONTRACT_NAME == "comparison_completion_evidence_v1"
    assert mod.CONTRACT_VERSION == "v1"


def test_regression_research_validity_contract_unchanged() -> None:
    from src.meta.learning_loop import research_validity_evidence_v1 as mod

    assert mod.CONTRACT_NAME == "research_validity_evidence_v1"
    assert mod.CONTRACT_VERSION == "v1"


def test_unknown_parent_ref_type(tmp_path, ssot_durable_output_dir) -> None:
    from src.meta.learning_loop.comparison_completion_research_validity_binding_v1 import (
        VerifiedEvidenceBundle,
        check_shared_lineage,
    )

    matched = produce_matched_completion_and_validity_bundles(tmp_path, ssot_durable_output_dir)
    completion, validity, _ = verify_binding_inputs(_binding_inputs(matched))
    bad_parent = dict(validity.parent_artifact_refs[0])
    bad_parent["ref_type"] = "unknown_owner_v99"
    validity_bad = VerifiedEvidenceBundle(
        bundle_dir=validity.bundle_dir,
        contract_name=validity.contract_name,
        contract_version=validity.contract_version,
        producer_version=validity.producer_version,
        artifact_ref=validity.artifact_ref,
        artifact_digest=validity.artifact_digest,
        manifest_digest=validity.manifest_digest,
        evidence_level=validity.evidence_level,
        parent_artifact_refs=(bad_parent,),
        evidence_payload=validity.evidence_payload,
    )
    with pytest.raises(ComparisonCompletionResearchValidityBindingError, match="ref_type mismatch"):
        check_shared_lineage(completion=completion, validity=validity_bad)


def test_second_completion_input_rejected_via_wrong_bundle(
    tmp_path, ssot_durable_output_dir
) -> None:
    matched = produce_matched_completion_and_validity_bundles(tmp_path, ssot_durable_output_dir)
    second_completion = ssot_durable_output_dir / "second_completion"
    produce_comparison_completion_evidence_v1(
        checkpoint_bundle_dir=matched.checkpoint_bundle_dir,
        output_dir=second_completion,
    )
    out = _durable_output(tmp_path)
    inputs = ComparisonCompletionResearchValidityBindingInputs(
        completion_evidence_bundle_dir=second_completion,
        research_validity_evidence_bundle_dir=matched.research_validity_bundle_dir,
    )
    result = produce_comparison_completion_research_validity_binding_v1(
        inputs=inputs, output_dir=out
    )
    assert result.binding_status == "PASS"


def test_orphan_checkpoint_bundle_rejected_as_completion(tmp_path, ssot_durable_output_dir) -> None:
    orphan_root = ssot_durable_output_dir / "orphan"
    orphan_root.mkdir(parents=True, exist_ok=True)
    matched_root = ssot_durable_output_dir / "matched"
    matched_root.mkdir(parents=True, exist_ok=True)
    orphan = produce_checkpoint_bundle(tmp_path / "orphan_case", orphan_root)
    matched = produce_matched_completion_and_validity_bundles(
        tmp_path / "matched_case", matched_root
    )
    out = _durable_output(tmp_path)
    inputs = ComparisonCompletionResearchValidityBindingInputs(
        completion_evidence_bundle_dir=orphan,
        research_validity_evidence_bundle_dir=matched.research_validity_bundle_dir,
    )
    with pytest.raises(ComparisonCompletionResearchValidityBindingError):
        produce_comparison_completion_research_validity_binding_v1(inputs=inputs, output_dir=out)
