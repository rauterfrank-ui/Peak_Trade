"""Contract tests for handoff_trust_policy_v1."""

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
    "tests.meta.handoff_trust_policy_v1_fixtures",
]

from scripts.ops.primary_evidence_retention_v0 import verify_manifest_sha256
from src.meta.learning_loop.comparison_ssot_v1.io import read_manifest
from src.meta.learning_loop.contract_safety_v1 import deterministic_json_dumps
from src.meta.learning_loop.handoff_trust_policy_v1 import (
    ARTIFACT_REL,
    AUTHORITY_LEVEL,
    CONTRACT_NAME,
    CONTRACT_VERSION,
    DETERMINISTIC_RULE_SET_VERSION,
    EVIDENCE_LEVEL,
    HANDOFF_TRUST_POLICY_AUTHORITY_INVARIANTS,
    MANIFEST_FILENAME,
    PRODUCER_VERSION,
    SELF_VERIFICATION_REL,
    HandoffTrustPolicyError,
    HandoffTrustPolicyInputs,
    VerifiedVersionedArtifactBundle,
    build_handoff_trust_policy_v1,
    produce_handoff_trust_policy_v1,
    reverify_handoff_trust_policy_v1,
    serialize_handoff_trust_policy_v1,
    verify_trust_policy_inputs,
    verify_versioned_artifact_bundle,
    _resolve_consumer_contract,
)
from src.meta.learning_loop.versioned_strategy_model_parameter_artifact_v1 import (
    ARTIFACT_REL as VERSIONED_ARTIFACT_REL,
)
from tests.meta.handoff_trust_policy_v1_fixtures import (
    embedded_consumer_contract_payload,
    produce_handoff_trust_policy_fixture,
    write_consumer_contract_file,
)


@pytest.fixture(autouse=True)
def _allow_tmp_output(monkeypatch: pytest.MonkeyPatch) -> None:
    targets = (
        "src.meta.learning_loop.handoff_trust_policy_v1.is_under_tmp",
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


def _durable_output(tmp_path: Path, name: str = "handoff_trust_out") -> Path:
    root = tmp_path / "evidence_root"
    root.mkdir(exist_ok=True)
    return root / name


def _inputs(versioned_dir: Path, consumer: Path | None = None) -> HandoffTrustPolicyInputs:
    return HandoffTrustPolicyInputs(
        versioned_artifact_bundle_dir=versioned_dir,
        consumer_contract_ref=consumer,
    )


def test_contract_constants() -> None:
    assert CONTRACT_NAME == "handoff_trust_policy_v1"
    assert CONTRACT_VERSION == "v1"
    assert EVIDENCE_LEVEL == "LEVEL_3"
    assert AUTHORITY_LEVEL == "NON_AUTHORITIZING"
    assert ARTIFACT_REL == "handoff_trust_policy_v1.json"
    assert DETERMINISTIC_RULE_SET_VERSION == "handoff_trust_policy_rules_v1"


def test_happy_path_allow_offline_handoff(tmp_path, ssot_durable_output_dir) -> None:
    fixture = produce_handoff_trust_policy_fixture(tmp_path, ssot_durable_output_dir)
    assert fixture.handoff_trust_policy_bundle_dir is not None
    payload = read_manifest(fixture.handoff_trust_policy_bundle_dir / ARTIFACT_REL)
    assert payload["trust_result"] == "ALLOW_OFFLINE_HANDOFF"
    assert payload["compatibility_result"] == "COMPATIBLE"
    assert payload["handoff_trust_policy_complete"] is True
    assert payload["versioned_artifact_bound"] is True
    assert payload["producer_contract_bound"] is True
    assert payload["cross_domain_lineage_bound"] is True
    assert payload["handoff_executed"] is False
    assert payload["consumer_invoked"] is False
    assert payload["consumer_mutated"] is False


def test_required_non_authorizing_flags(tmp_path, ssot_durable_output_dir) -> None:
    fixture = produce_handoff_trust_policy_fixture(tmp_path, ssot_durable_output_dir)
    payload = read_manifest(fixture.handoff_trust_policy_bundle_dir / ARTIFACT_REL)
    assert payload["promotion_authorized"] is False
    assert payload["promotion_candidate_constructed"] is False
    assert payload["configpatch_created"] is False
    assert payload["configpatch_modified"] is False
    assert payload["configpatch_applied"] is False
    assert payload["configpatch_accepted"] is False
    assert payload["runtime_configuration_created"] is False
    assert payload["runtime_authorized"] is False
    assert payload["live_authorized"] is False
    assert payload["orders_allowed"] is False
    assert payload["scheduler_runtime_allowed"] is False
    assert payload["files_transferred"] is False
    assert payload["network_side_effect_created"] is False
    assert (
        payload["handoff_trust_policy_authority_invariants"]
        == HANDOFF_TRUST_POLICY_AUTHORITY_INVARIANTS
    )


def test_determinism(tmp_path, ssot_durable_output_dir) -> None:
    versioned = produce_handoff_trust_policy_fixture(
        tmp_path, ssot_durable_output_dir, produce_output=False
    )
    out_a = _durable_output(tmp_path, "a")
    out_b = _durable_output(tmp_path, "b")
    inputs = _inputs(versioned.versioned_artifact_bundle_dir)
    produce_handoff_trust_policy_v1(inputs=inputs, output_dir=out_a)
    produce_handoff_trust_policy_v1(inputs=inputs, output_dir=out_b)
    assert (out_a / ARTIFACT_REL).read_text() == (out_b / ARTIFACT_REL).read_text()


def test_self_verification_and_manifest(tmp_path, ssot_durable_output_dir) -> None:
    fixture = produce_handoff_trust_policy_fixture(tmp_path, ssot_durable_output_dir)
    out = fixture.handoff_trust_policy_bundle_dir
    assert out is not None
    ok, msg = verify_manifest_sha256(out)
    assert ok, msg
    self_payload = read_manifest(out / SELF_VERIFICATION_REL)
    assert self_payload["overall_status"] == "PASS"
    reverify_handoff_trust_policy_v1(output_dir=out)


def test_explicit_consumer_contract_file(tmp_path, ssot_durable_output_dir) -> None:
    fixture = produce_handoff_trust_policy_fixture(
        tmp_path,
        ssot_durable_output_dir,
        include_consumer_contract_file=True,
    )
    payload = read_manifest(fixture.handoff_trust_policy_bundle_dir / ARTIFACT_REL)
    assert payload["trust_result"] == "ALLOW_OFFLINE_HANDOFF"
    assert payload["consumer_contract_ref"] == fixture.consumer_contract_path.parent.as_posix()


def test_missing_versioned_artifact_bundle(tmp_path) -> None:
    with pytest.raises(HandoffTrustPolicyError):
        verify_versioned_artifact_bundle(tmp_path / "missing")


def test_invalid_versioned_artifact_manifest(tmp_path, ssot_durable_output_dir) -> None:
    fixture = produce_handoff_trust_policy_fixture(
        tmp_path, ssot_durable_output_dir, produce_output=False
    )
    versioned_dir = fixture.versioned_artifact_bundle_dir
    (versioned_dir / "MANIFEST.sha256").write_text("invalid", encoding="utf-8")
    with pytest.raises(HandoffTrustPolicyError):
        verify_versioned_artifact_bundle(versioned_dir)


def test_versioned_artifact_self_verification_manipulation(
    tmp_path, ssot_durable_output_dir
) -> None:
    fixture = produce_handoff_trust_policy_fixture(
        tmp_path, ssot_durable_output_dir, produce_output=False
    )
    versioned_dir = fixture.versioned_artifact_bundle_dir
    self_path = versioned_dir / "SELF_VERIFICATION.json"
    payload = read_manifest(self_path)
    payload["overall_status"] = "FAIL"
    self_path.write_text(deterministic_json_dumps(payload), encoding="utf-8")
    with pytest.raises(HandoffTrustPolicyError):
        verify_versioned_artifact_bundle(versioned_dir)


def test_versioned_artifact_contract_version_mismatch(tmp_path, ssot_durable_output_dir) -> None:
    fixture = produce_handoff_trust_policy_fixture(
        tmp_path, ssot_durable_output_dir, produce_output=False
    )
    artifact_path = fixture.versioned_artifact_bundle_dir / VERSIONED_ARTIFACT_REL
    payload = read_manifest(artifact_path)
    payload["contract_version"] = "v99"
    artifact_path.write_text(deterministic_json_dumps(payload), encoding="utf-8")
    with pytest.raises(HandoffTrustPolicyError):
        verify_versioned_artifact_bundle(fixture.versioned_artifact_bundle_dir)


def test_versioned_artifact_digest_mismatch_on_reverify(tmp_path, ssot_durable_output_dir) -> None:
    fixture = produce_handoff_trust_policy_fixture(tmp_path, ssot_durable_output_dir)
    out = fixture.handoff_trust_policy_bundle_dir
    artifact = read_manifest(out / ARTIFACT_REL)
    artifact["artifact_digest"] = "0" * 64
    (out / ARTIFACT_REL).write_text(deterministic_json_dumps(artifact), encoding="utf-8")
    with pytest.raises(HandoffTrustPolicyError):
        reverify_handoff_trust_policy_v1(output_dir=out)


def test_strategy_lineage_mismatch_denies(tmp_path, ssot_durable_output_dir) -> None:
    fixture = produce_handoff_trust_policy_fixture(
        tmp_path, ssot_durable_output_dir, produce_output=False
    )
    versioned = verify_versioned_artifact_bundle(fixture.versioned_artifact_bundle_dir)
    tampered = dict(versioned.artifact_payload)
    tampered["strategy_identity_digest"] = "1" * 64
    versioned = VerifiedVersionedArtifactBundle(
        **{**versioned.__dict__, "artifact_payload": tampered}
    )
    consumer = _resolve_consumer_contract(None)
    policy = build_handoff_trust_policy_v1(versioned_artifact=versioned, consumer=consumer)
    assert policy["trust_result"] == "DENY_HANDOFF"


def test_producer_contract_mismatch_denies(tmp_path, ssot_durable_output_dir) -> None:
    fixture = produce_handoff_trust_policy_fixture(
        tmp_path, ssot_durable_output_dir, produce_output=False
    )
    versioned = verify_versioned_artifact_bundle(fixture.versioned_artifact_bundle_dir)
    tampered = dict(versioned.artifact_payload)
    tampered["contract_name"] = "wrong_producer"
    versioned = VerifiedVersionedArtifactBundle(
        **{**versioned.__dict__, "artifact_payload": tampered}
    )
    consumer = _resolve_consumer_contract(None)
    policy = build_handoff_trust_policy_v1(versioned_artifact=versioned, consumer=consumer)
    assert policy["trust_result"] == "DENY_HANDOFF"
    assert policy["compatibility_result"] == "INCOMPATIBLE"


def test_consumer_contract_mismatch_rejected(tmp_path, ssot_durable_output_dir) -> None:
    fixture = produce_handoff_trust_policy_fixture(
        tmp_path, ssot_durable_output_dir, produce_output=False
    )
    bad_consumer = write_consumer_contract_file(
        _durable_output(tmp_path, "consumer") / "bad_consumer.json"
    )
    payload = embedded_consumer_contract_payload()
    payload["contract_version"] = "v99"
    bad_consumer.write_text(deterministic_json_dumps(payload), encoding="utf-8")
    with pytest.raises(HandoffTrustPolicyError):
        verify_trust_policy_inputs(
            HandoffTrustPolicyInputs(
                versioned_artifact_bundle_dir=fixture.versioned_artifact_bundle_dir,
                consumer_contract_ref=bad_consumer,
            )
        )


def test_incompatible_schema_version_denies(tmp_path, ssot_durable_output_dir) -> None:
    fixture = produce_handoff_trust_policy_fixture(
        tmp_path, ssot_durable_output_dir, produce_output=False
    )
    versioned = verify_versioned_artifact_bundle(fixture.versioned_artifact_bundle_dir)
    tampered = dict(versioned.artifact_payload)
    tampered["artifact_schema_version"] = "v99"
    versioned = VerifiedVersionedArtifactBundle(
        **{**versioned.__dict__, "artifact_payload": tampered}
    )
    consumer = _resolve_consumer_contract(None)
    policy = build_handoff_trust_policy_v1(versioned_artifact=versioned, consumer=consumer)
    assert policy["trust_result"] == "DENY_HANDOFF"


def test_revoked_trust_denies(tmp_path, ssot_durable_output_dir) -> None:
    fixture = produce_handoff_trust_policy_fixture(
        tmp_path, ssot_durable_output_dir, produce_output=False
    )
    versioned = verify_versioned_artifact_bundle(fixture.versioned_artifact_bundle_dir)
    tampered = dict(versioned.artifact_payload)
    tampered["revocation_state"] = "REVOKED"
    versioned = VerifiedVersionedArtifactBundle(
        **{**versioned.__dict__, "artifact_payload": tampered}
    )
    consumer = _resolve_consumer_contract(None)
    policy = build_handoff_trust_policy_v1(versioned_artifact=versioned, consumer=consumer)
    assert policy["trust_result"] == "DENY_HANDOFF"


def test_unknown_revocation_abstains(tmp_path, ssot_durable_output_dir) -> None:
    fixture = produce_handoff_trust_policy_fixture(
        tmp_path, ssot_durable_output_dir, produce_output=False
    )
    versioned = verify_versioned_artifact_bundle(fixture.versioned_artifact_bundle_dir)
    tampered = dict(versioned.artifact_payload)
    tampered["revocation_state"] = "UNKNOWN"
    versioned = VerifiedVersionedArtifactBundle(
        **{**versioned.__dict__, "artifact_payload": tampered}
    )
    consumer = _resolve_consumer_contract(None)
    policy = build_handoff_trust_policy_v1(versioned_artifact=versioned, consumer=consumer)
    assert policy["trust_result"] == "ABSTAIN"


def test_promotion_authorized_in_artifact_denies(tmp_path, ssot_durable_output_dir) -> None:
    fixture = produce_handoff_trust_policy_fixture(
        tmp_path, ssot_durable_output_dir, produce_output=False
    )
    versioned = verify_versioned_artifact_bundle(fixture.versioned_artifact_bundle_dir)
    tampered = dict(versioned.artifact_payload)
    tampered["promotion_authorized"] = True
    versioned = VerifiedVersionedArtifactBundle(
        **{**versioned.__dict__, "artifact_payload": tampered}
    )
    consumer = _resolve_consumer_contract(None)
    policy = build_handoff_trust_policy_v1(versioned_artifact=versioned, consumer=consumer)
    assert policy["trust_result"] == "DENY_HANDOFF"


def test_handoff_executed_flag_rejected_on_serialize(tmp_path, ssot_durable_output_dir) -> None:
    fixture = produce_handoff_trust_policy_fixture(tmp_path, ssot_durable_output_dir)
    payload = read_manifest(fixture.handoff_trust_policy_bundle_dir / ARTIFACT_REL)
    payload["handoff_executed"] = True
    with pytest.raises(HandoffTrustPolicyError):
        serialize_handoff_trust_policy_v1(payload)


def test_consumer_invoked_flag_rejected_on_serialize(tmp_path, ssot_durable_output_dir) -> None:
    fixture = produce_handoff_trust_policy_fixture(tmp_path, ssot_durable_output_dir)
    payload = read_manifest(fixture.handoff_trust_policy_bundle_dir / ARTIFACT_REL)
    payload["consumer_invoked"] = True
    with pytest.raises(HandoffTrustPolicyError):
        serialize_handoff_trust_policy_v1(payload)


def test_runtime_authorized_flag_rejected_on_serialize(tmp_path, ssot_durable_output_dir) -> None:
    fixture = produce_handoff_trust_policy_fixture(tmp_path, ssot_durable_output_dir)
    payload = read_manifest(fixture.handoff_trust_policy_bundle_dir / ARTIFACT_REL)
    payload["runtime_authorized"] = True
    with pytest.raises(HandoffTrustPolicyError):
        serialize_handoff_trust_policy_v1(payload)


def test_forbidden_key_rejected_on_serialize(tmp_path, ssot_durable_output_dir) -> None:
    fixture = produce_handoff_trust_policy_fixture(tmp_path, ssot_durable_output_dir)
    payload = read_manifest(fixture.handoff_trust_policy_bundle_dir / ARTIFACT_REL)
    payload["promotion"] = True
    with pytest.raises(HandoffTrustPolicyError):
        serialize_handoff_trust_policy_v1(payload)


def test_output_existing_dir_fail(tmp_path, ssot_durable_output_dir) -> None:
    versioned = produce_handoff_trust_policy_fixture(
        tmp_path, ssot_durable_output_dir, produce_output=False
    )
    out = _durable_output(tmp_path)
    out.mkdir()
    with pytest.raises(HandoffTrustPolicyError):
        produce_handoff_trust_policy_v1(
            inputs=_inputs(versioned.versioned_artifact_bundle_dir),
            output_dir=out,
        )


def test_reverify_after_tamper(tmp_path, ssot_durable_output_dir) -> None:
    fixture = produce_handoff_trust_policy_fixture(tmp_path, ssot_durable_output_dir)
    out = fixture.handoff_trust_policy_bundle_dir
    artifact = read_manifest(out / ARTIFACT_REL)
    artifact["trust_result"] = "DENY_HANDOFF"
    (out / ARTIFACT_REL).write_text(deterministic_json_dumps(artifact), encoding="utf-8")
    with pytest.raises(HandoffTrustPolicyError):
        reverify_handoff_trust_policy_v1(output_dir=out)


def test_manifest_self_hashing_not_allowed(tmp_path, ssot_durable_output_dir) -> None:
    fixture = produce_handoff_trust_policy_fixture(tmp_path, ssot_durable_output_dir)
    out = fixture.handoff_trust_policy_bundle_dir
    manifest_path = out / MANIFEST_FILENAME
    lines = manifest_path.read_text(encoding="utf-8").splitlines()
    manifest_path.write_text(
        "\n".join(lines + [f"{manifest_path.name}  deadbeef"]), encoding="utf-8"
    )
    ok, _ = verify_manifest_sha256(out)
    assert ok is False


def test_verify_trust_policy_inputs(tmp_path, ssot_durable_output_dir) -> None:
    versioned = produce_handoff_trust_policy_fixture(
        tmp_path, ssot_durable_output_dir, produce_output=False
    )
    artifact_bundle, consumer = verify_trust_policy_inputs(
        _inputs(versioned.versioned_artifact_bundle_dir)
    )
    assert artifact_bundle.bundle_dir.is_dir()
    assert consumer.contract_id


def test_copy_inputs_no_mutation(tmp_path, ssot_durable_output_dir) -> None:
    versioned = produce_handoff_trust_policy_fixture(
        tmp_path, ssot_durable_output_dir, produce_output=False
    )
    before = (versioned.versioned_artifact_bundle_dir / VERSIONED_ARTIFACT_REL).read_bytes()
    out = _durable_output(tmp_path)
    produce_handoff_trust_policy_v1(
        inputs=_inputs(versioned.versioned_artifact_bundle_dir),
        output_dir=out,
    )
    assert (versioned.versioned_artifact_bundle_dir / VERSIONED_ARTIFACT_REL).read_bytes() == before


def test_no_forbidden_runtime_imports() -> None:
    module_path = Path("src/meta/learning_loop/handoff_trust_policy_v1.py")
    tree = ast.parse(module_path.read_text(encoding="utf-8"))
    forbidden = {
        "src.governance.promotion_loop.engine",
        "src.governance.promotion_loop.policy",
        "src.governance.promotion_loop.safety",
    }
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module in forbidden:
            pytest.fail(f"forbidden import: {node.module}")
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name in forbidden:
                    pytest.fail(f"forbidden import: {alias.name}")
