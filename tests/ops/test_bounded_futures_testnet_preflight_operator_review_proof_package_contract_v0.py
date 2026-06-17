"""Static + offline bounded Futures Testnet preflight operator-review proof package (v0, PE-20).

Docs/tests-only. No runtime, network, credentials, or Testnet start.
"""

from __future__ import annotations

import json
import shutil
import subprocess
from dataclasses import replace
from pathlib import Path

import pytest

from src.ops.bounded_futures_testnet_preflight_operator_review_proof_package_contract_v0 import (
    ARTIFACT_EVIDENCE_CHAIN_BINDING,
    ARTIFACT_OPERATOR_DECISION_RECORD,
    ARTIFACT_OPERATOR_REVIEW_INPUT,
    ARTIFACT_OPERATOR_REVIEW_PROOF,
    ARTIFACT_PACKAGE_METADATA,
    ARTIFACT_PACKAGE_SUMMARY,
    ARTIFACT_SAFETY_SNAPSHOT,
    ARTIFACT_SOURCE_STATE_BINDING,
    CONTRACT_VERSION as PE20_CONTRACT_VERSION,
    DECISION_APPROVE_FOR_SEPARATE_NEXT_PHASE_REVIEW,
    DECISION_REJECT,
    DECISION_REQUEST_CHANGES,
    EXPECTED_OPERATOR_NAME,
    PACKAGE_MARKER,
    PACKAGE_STATUS_PERSISTED_VERIFIED,
    PACKAGE_STATUS_REJECTED,
    OperatorReviewProofPackageInput,
    build_proof_package_plan,
    compute_package_digest,
    compute_package_id,
    evaluate_proof_package_result,
    explicit_contract_proof_kwargs,
    persist_operator_review_proof_package,
    validate_package_input_mapping,
)
from src.ops.bounded_futures_testnet_preflight_operator_review_reproducibility_contract_v0 import (
    DECISION_APPROVE_FOR_SEPARATE_NEXT_PHASE_REVIEW as PE19_APPROVE,
    REASON_CHANGES_REQUIRED,
    REASON_EVIDENCE_COMPLETE,
    REASON_EVIDENCE_INCOMPLETE,
    compute_decision_record_digest,
    compute_review_input_digest,
    default_minimal_decision_record,
    default_minimal_operator_review_input,
    evaluate_operator_review,
    serialize_decision_record_canonical,
    serialize_review_input_canonical,
)
from src.ops.bounded_futures_testnet_preflight_packet_archive_contract_v0 import (
    PACKAGE_MARKER as PE16_PACKAGE_MARKER,
    PreflightPacketArchiveInput,
    build_archive_plan,
    compute_archive_identity,
    persist_preflight_packet_archive,
)
from src.ops.bounded_futures_testnet_preflight_packet_builder_contract_v0 import (
    PACKAGE_MARKER as PE14_PACKAGE_MARKER,
    build_preflight_packet,
    compute_input_capture_digest,
    default_minimal_builder_input,
    serialize_input_capture_canonical,
)
from src.ops.bounded_futures_testnet_preflight_packet_completeness_truth_contract_v0 import (
    COMPLETENESS_CONTRACT_VERSION,
    OPERATOR_REVIEW_PROOF_PACKAGE_CONTRACT_VERSION,
    PACKAGE_MARKER as PE17_PACKAGE_MARKER,
    ExplicitContractProof,
    PreflightCompletenessTruthInput,
    evaluate_glb016_internal_truth,
)
from src.ops.bounded_futures_testnet_preflight_packet_contract_v0 import (
    CONTRACT_VERSION,
    FOLLOWUP_RUN_GATE,
    compute_packet_digest,
)
from src.ops.bounded_futures_testnet_preflight_packet_replay_contract_v0 import (
    ARTIFACT_CANONICAL_INPUT_CAPTURE,
    ARTIFACT_PACKET_PAYLOAD,
    HASH_ALGORITHM,
    PACKAGE_MARKER as PE15_PACKAGE_MARKER,
    build_replay_manifest,
    compute_replay_manifest_digest,
    replay_preflight_packet_offline,
    serialize_packet_canonical,
)
from src.ops.bounded_futures_testnet_preflight_source_state_capture_contract_v0 import (
    CAPTURE_VALID,
    PACKAGE_MARKER as PE18_PACKAGE_MARKER,
    capture_preflight_source_state,
    default_minimal_source_state_capture_input,
    explicit_contract_proof_kwargs as pe18_explicit_contract_proof_kwargs,
)
from scripts.ops.primary_evidence_retention_v0 import MANIFEST_FILENAME, verify_manifest_sha256

REPO_ROOT = Path(__file__).resolve().parents[2]
PE20_MODULE = (
    REPO_ROOT
    / "src"
    / "ops"
    / "bounded_futures_testnet_preflight_operator_review_proof_package_contract_v0.py"
)
PE19_MODULE = (
    REPO_ROOT
    / "src"
    / "ops"
    / "bounded_futures_testnet_preflight_operator_review_reproducibility_contract_v0.py"
)
PE17_MODULE = (
    REPO_ROOT
    / "src"
    / "ops"
    / "bounded_futures_testnet_preflight_packet_completeness_truth_contract_v0.py"
)
SECTION5_GAP_OWNER_MAP = (
    REPO_ROOT / "docs" / "ops" / "planning" / "SECTION5_PREFLIGHT_GAP_OWNER_MAP_CONTRACT_V0.md"
)
CI_AUDIT = REPO_ROOT / "docs" / "ops" / "CI_AUDIT_KNOWN_ISSUES.md"

TEST_PACKAGE_MARKER = (
    "BOUNDED_FUTURES_TESTNET_PREFLIGHT_OPERATOR_REVIEW_PROOF_PACKAGE_GUARD_V0=true"
)
_CLASS4_SCOPED_EXCEPTION_MARKER = "BOUNDED_FUTURES_TESTNET_PREFLIGHT_OPERATOR_REVIEW_PROOF_PACKAGE_GUARD_CLASS4_SCOPED_EXCEPTION_V0=true"
GENERIC_FUTURES_INSTRUMENT = "PF_ETHUSD"
VALID_COMMIT_SHA = "abcdef0123456789abcdef0123456789abcdef01"
DEFAULT_PACKAGE_SUMMARY = (
    "# Package summary\n\nNon-authorizing durable operator-review proof package.\n"
)
DEFAULT_MACHINE_SUMMARY = "VERDICT=PLANNED\nFUTURES_ONLY=true\nPREFLIGHT_REMAINS_BLOCKED=true\n"
DEFAULT_RECOMMENDED_NEXT_STEP = "# Recommended next step\n\nNon-authorizing review only.\n"


def _durable_root(tmp_path: Path) -> Path:
    path = REPO_ROOT / "tests" / ".pytest_archive_roots" / f"pe20_{tmp_path.name}"
    path.mkdir(parents=True, exist_ok=True)
    return path


@pytest.fixture
def durable_archive_root(tmp_path: Path) -> Path:
    root = _durable_root(tmp_path)
    yield root
    if root.exists():
        shutil.rmtree(root, ignore_errors=True)


def _chain_artifacts(
    durable_archive_root: Path,
    *,
    source_revision: str = VALID_COMMIT_SHA,
) -> dict:
    inputs = default_minimal_builder_input(
        source_revision=source_revision,
        instrument=GENERIC_FUTURES_INSTRUMENT,
    )
    build_result = build_preflight_packet(inputs)
    assert build_result["build_pass"]
    packet = build_result["packet"]
    assert packet is not None
    packet_digest = compute_packet_digest(packet)
    capture_digest = compute_input_capture_digest(inputs)
    manifest = build_replay_manifest(
        source_revision=source_revision,
        canonical_input_capture_digest=capture_digest,
        packet_digest=packet_digest,
    )
    manifest_digest = compute_replay_manifest_digest(manifest)
    artifacts = {
        ARTIFACT_CANONICAL_INPUT_CAPTURE: serialize_input_capture_canonical(inputs),
        ARTIFACT_PACKET_PAYLOAD: serialize_packet_canonical(packet),
    }
    replay_result = replay_preflight_packet_offline(
        canonical_input_capture=inputs,
        expected_packet_digest=packet_digest,
        manifest=manifest,
        artifacts=artifacts,
        packet_payload=packet,
    )
    archive_input = PreflightPacketArchiveInput(
        archive_root=durable_archive_root,
        builder_input=inputs,
        packet=packet,
        replay_manifest=manifest,
        replay_artifacts=artifacts,
        expected_packet_digest=packet_digest,
        machine_summary_env=DEFAULT_MACHINE_SUMMARY,
        recommended_next_step_md=DEFAULT_RECOMMENDED_NEXT_STEP,
    )
    archive_plan = build_archive_plan(archive_input)
    archive_result = persist_preflight_packet_archive(archive_input)
    archive_identity = compute_archive_identity(
        source_revision=source_revision,
        packet_digest=packet_digest,
        input_capture_digest=capture_digest,
        manifest_digest=manifest_digest,
    )
    capture_input = default_minimal_source_state_capture_input(
        source_revision=source_revision,
        packet_digest=packet_digest,
        input_capture_digest=capture_digest,
        replay_manifest_digest=manifest_digest,
        archive_identity=archive_identity,
        archive_manifest_digest=archive_plan["manifest_digest"],
        completeness_truth_identity=COMPLETENESS_CONTRACT_VERSION,
    )
    capture_result = capture_preflight_source_state(capture_input)
    assert capture_result["capture_status"] == CAPTURE_VALID
    return {
        "inputs": inputs,
        "packet": packet,
        "packet_digest": packet_digest,
        "capture_digest": capture_digest,
        "manifest_digest": manifest_digest,
        "archive_identity": archive_identity,
        "archive_manifest_digest": archive_plan["manifest_digest"],
        "completeness_truth_identity": COMPLETENESS_CONTRACT_VERSION,
        "source_state_digest": capture_result["source_state_digest"],
        "capture_result": capture_result,
        "replay_result": replay_result,
        "archive_result": archive_result,
        "manifest": manifest,
        "artifacts": artifacts,
    }


def _minimal_review_input(durable_archive_root: Path):
    chain = _chain_artifacts(durable_archive_root)
    return default_minimal_operator_review_input(
        source_revision=VALID_COMMIT_SHA,
        packet_digest=chain["packet_digest"],
        input_capture_digest=chain["capture_digest"],
        replay_manifest_digest=chain["manifest_digest"],
        archive_identity=chain["archive_identity"],
        archive_manifest_digest=chain["archive_manifest_digest"],
        completeness_truth_identity=chain["completeness_truth_identity"],
        source_state_digest=chain["source_state_digest"],
    )


def _valid_package_input(durable_archive_root: Path) -> OperatorReviewProofPackageInput:
    chain = _chain_artifacts(durable_archive_root)
    review_input = _minimal_review_input(durable_archive_root)
    input_digest = compute_review_input_digest(review_input)
    decision_record = default_minimal_decision_record(
        source_revision=VALID_COMMIT_SHA,
        review_input_digest=input_digest,
        decision=DECISION_APPROVE_FOR_SEPARATE_NEXT_PHASE_REVIEW,
        reason_code=REASON_EVIDENCE_COMPLETE,
    )
    return OperatorReviewProofPackageInput(
        archive_root=durable_archive_root,
        review_input=review_input,
        decision_record=decision_record,
        source_state_digest=chain["source_state_digest"],
        package_summary_md=DEFAULT_PACKAGE_SUMMARY,
    )


def test_package_marker_present() -> None:
    text = Path(__file__).read_text(encoding="utf-8")
    assert TEST_PACKAGE_MARKER in text
    assert _CLASS4_SCOPED_EXCEPTION_MARKER in text
    assert PACKAGE_MARKER in PE20_MODULE.read_text(encoding="utf-8")


def test_valid_approve_package_plan(durable_archive_root: Path) -> None:
    plan = build_proof_package_plan(_valid_package_input(durable_archive_root))
    assert plan["package_status"] == "planned"
    assert plan["package_id"]
    assert plan["package_digest"]
    assert plan["validation_errors"] == []


def test_package_id_and_digest_deterministic(durable_archive_root: Path) -> None:
    package_input = _valid_package_input(durable_archive_root)
    plan_a = build_proof_package_plan(package_input)
    plan_b = build_proof_package_plan(package_input)
    assert plan_a["package_id"] == plan_b["package_id"]
    assert plan_a["package_digest"] == plan_b["package_digest"]


def test_package_mapping_order_irrelevant(durable_archive_root: Path) -> None:
    package_input = _valid_package_input(durable_archive_root)
    review_input = package_input.review_input
    decision_record = package_input.decision_record
    review_proof = evaluate_operator_review(
        review_input,
        decision_record,
        review_input_digest=compute_review_input_digest(review_input),
        decision_record_digest=compute_decision_record_digest(decision_record),
    )
    mapping = {
        "package_contract_version": PE20_CONTRACT_VERSION,
        "package_schema_version": "bounded_futures_testnet_preflight_operator_review_proof_package.serialization.v0",
        "hash_algorithm": HASH_ALGORITHM,
        "operator_review_input": json.loads(serialize_review_input_canonical(review_input)),
        "operator_decision_record": json.loads(
            serialize_decision_record_canonical(decision_record)
        ),
        "operator_review_proof": review_proof,
        "source_state_binding": {
            "package_contract_version": PE20_CONTRACT_VERSION,
            "source_revision": review_input.source_revision,
            "repository_identity": review_input.repository_identity,
            "source_state_digest": package_input.source_state_digest,
            "pe18_source_state_capture_contract_version": "bounded_futures_testnet_preflight_source_state_capture.v0",
        },
        "evidence_chain_binding": {
            "package_contract_version": PE20_CONTRACT_VERSION,
            "source_revision": review_input.source_revision,
            "contract_versions": {
                "pe12_lifecycle": review_input.contract_versions.pe12_lifecycle,
                "pe13_packet": review_input.contract_versions.pe13_packet,
                "pe14_builder": review_input.contract_versions.pe14_builder,
                "pe15_replay": review_input.contract_versions.pe15_replay,
                "pe16_archive": review_input.contract_versions.pe16_archive,
                "pe17_completeness_truth": review_input.contract_versions.pe17_completeness_truth,
                "pe18_source_state_capture": review_input.contract_versions.pe18_source_state_capture,
                "pe19_operator_review": review_input.contract_versions.pe19_operator_review,
            },
            "evidence_chain": {
                "archive_identity": review_input.evidence_chain.archive_identity,
                "archive_manifest_digest": review_input.evidence_chain.archive_manifest_digest,
                "completeness_truth_identity": review_input.evidence_chain.completeness_truth_identity,
                "input_capture_digest": review_input.evidence_chain.input_capture_digest,
                "manifest_verify_rc": 0,
                "packet_digest": review_input.evidence_chain.packet_digest,
                "replay_manifest_digest": review_input.evidence_chain.replay_manifest_digest,
                "source_state_digest": review_input.evidence_chain.source_state_digest,
            },
            "manifest_verify_rc": 0,
        },
        "safety_snapshot": {
            "package_contract_version": PE20_CONTRACT_VERSION,
            "credentials_allowed": False,
            "environment": "testnet",
            "execution_authorized": False,
            "followup_run_gate": FOLLOWUP_RUN_GATE,
            "futures_only": True,
            "live_authorized": False,
            "network_allowed": False,
            "non_authorizing": True,
            "operator_go_present": False,
            "orders_allowed": False,
            "preflight_remains_blocked": True,
            "ready_for_operator_arming": False,
            "scheduler_runtime_allowed": False,
            "zero_order_authorized": False,
        },
        "package_summary_md": DEFAULT_PACKAGE_SUMMARY.rstrip() + "\n",
    }
    canonical = json.dumps(mapping, sort_keys=True, separators=(",", ":"))
    digest_a = compute_package_digest(
        review_input=review_input,
        decision_record=decision_record,
        review_proof=review_proof,
        source_state_digest=package_input.source_state_digest,
        package_summary_md=DEFAULT_PACKAGE_SUMMARY,
    )
    digest_b = hashlib_from_canonical(canonical)
    assert digest_a == digest_b


def hashlib_from_canonical(canonical: str) -> str:
    import hashlib

    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def test_relevant_change_alters_package_id_and_digest(durable_archive_root: Path) -> None:
    package_input = _valid_package_input(durable_archive_root)
    plan = build_proof_package_plan(package_input)
    mutated_input = replace(
        package_input,
        review_input=replace(
            package_input.review_input,
            evidence_chain=replace(
                package_input.review_input.evidence_chain,
                packet_digest="f" * 64,
            ),
        ),
    )
    mutated_plan = build_proof_package_plan(mutated_input)
    assert mutated_plan["package_id"] != plan["package_id"]
    assert mutated_plan["package_digest"] != plan["package_digest"]


def test_unknown_package_input_fields_fail_closed() -> None:
    assert validate_package_input_mapping({"archive_root": "/x", "extra": True})


def test_reject_decision_fail_closed(durable_archive_root: Path) -> None:
    package_input = _valid_package_input(durable_archive_root)
    review_input = package_input.review_input
    input_digest = compute_review_input_digest(review_input)
    reject_input = replace(
        package_input,
        decision_record=default_minimal_decision_record(
            source_revision=VALID_COMMIT_SHA,
            review_input_digest=input_digest,
            decision=DECISION_REJECT,
            reason_code=REASON_EVIDENCE_INCOMPLETE,
        ),
    )
    plan = build_proof_package_plan(reject_input)
    assert plan["package_status"] == PACKAGE_STATUS_REJECTED


def test_request_changes_fail_closed(durable_archive_root: Path) -> None:
    package_input = _valid_package_input(durable_archive_root)
    review_input = package_input.review_input
    input_digest = compute_review_input_digest(review_input)
    changes_input = replace(
        package_input,
        decision_record=default_minimal_decision_record(
            source_revision=VALID_COMMIT_SHA,
            review_input_digest=input_digest,
            decision=DECISION_REQUEST_CHANGES,
            reason_code=REASON_CHANGES_REQUIRED,
        ),
    )
    plan = build_proof_package_plan(changes_input)
    assert plan["package_status"] == PACKAGE_STATUS_REJECTED


def test_wrong_operator_fail_closed(durable_archive_root: Path) -> None:
    package_input = _valid_package_input(durable_archive_root)
    review_input = package_input.review_input
    input_digest = compute_review_input_digest(review_input)
    bad_input = replace(
        package_input,
        decision_record=default_minimal_decision_record(
            source_revision=VALID_COMMIT_SHA,
            review_input_digest=input_digest,
            operator_name="Other Operator",
        ),
    )
    plan = build_proof_package_plan(bad_input)
    assert plan["package_status"] == PACKAGE_STATUS_REJECTED
    assert EXPECTED_OPERATOR_NAME == "Frank Rauter"


def test_digest_mismatch_fail_closed(durable_archive_root: Path) -> None:
    package_input = _valid_package_input(durable_archive_root)
    review_input = package_input.review_input
    input_digest = compute_review_input_digest(review_input)
    bad_input = replace(
        package_input,
        decision_record=default_minimal_decision_record(
            source_revision=VALID_COMMIT_SHA,
            review_input_digest="0" * 64,
        ),
    )
    plan = build_proof_package_plan(bad_input)
    assert plan["package_status"] == PACKAGE_STATUS_REJECTED


def test_manifest_verify_rc_nonzero_fail_closed(durable_archive_root: Path) -> None:
    package_input = _valid_package_input(durable_archive_root)
    review_input = replace(
        package_input.review_input,
        evidence_chain=replace(
            package_input.review_input.evidence_chain,
            manifest_verify_rc=1,
        ),
    )
    bad_input = replace(package_input, review_input=review_input)
    plan = build_proof_package_plan(bad_input)
    assert plan["package_status"] == PACKAGE_STATUS_REJECTED


def test_source_state_digest_mismatch_fail_closed(durable_archive_root: Path) -> None:
    package_input = _valid_package_input(durable_archive_root)
    bad_input = replace(package_input, source_state_digest="0" * 64)
    plan = build_proof_package_plan(bad_input)
    assert plan["package_status"] == PACKAGE_STATUS_REJECTED


def test_persist_writes_required_artifacts(durable_archive_root: Path) -> None:
    result = persist_operator_review_proof_package(_valid_package_input(durable_archive_root))
    assert result["package_status"] == PACKAGE_STATUS_PERSISTED_VERIFIED
    assert result["required_artifacts_present"] is True
    assert result["manifest_written"] is True
    assert result["manifest_verify_rc"] == 0
    destination = durable_archive_root / result["package_relative_path"]
    for artifact in (
        ARTIFACT_OPERATOR_REVIEW_INPUT,
        ARTIFACT_OPERATOR_DECISION_RECORD,
        ARTIFACT_OPERATOR_REVIEW_PROOF,
        ARTIFACT_SOURCE_STATE_BINDING,
        ARTIFACT_EVIDENCE_CHAIN_BINDING,
        ARTIFACT_SAFETY_SNAPSHOT,
        ARTIFACT_PACKAGE_METADATA,
        ARTIFACT_PACKAGE_SUMMARY,
        MANIFEST_FILENAME,
    ):
        assert (destination / artifact).is_file()


def test_persist_idempotent(durable_archive_root: Path) -> None:
    package_input = _valid_package_input(durable_archive_root)
    first = persist_operator_review_proof_package(package_input)
    second = persist_operator_review_proof_package(package_input)
    assert first["package_status"] == PACKAGE_STATUS_PERSISTED_VERIFIED
    assert second["package_status"] == PACKAGE_STATUS_PERSISTED_VERIFIED
    assert first["package_id"] == second["package_id"]


def test_collision_with_differing_content_fail_closed(durable_archive_root: Path) -> None:
    package_input = _valid_package_input(durable_archive_root)
    first = persist_operator_review_proof_package(package_input)
    mutated = replace(package_input, package_summary_md="# Different summary\n")
    second = persist_operator_review_proof_package(mutated)
    assert first["package_status"] == PACKAGE_STATUS_PERSISTED_VERIFIED
    assert second["package_status"] == PACKAGE_STATUS_REJECTED
    assert second["collision_detected"] is True


def test_tmp_archive_root_rejected(tmp_path: Path) -> None:
    package_input = replace(_valid_package_input(tmp_path), archive_root=Path("/tmp/pe20_test"))
    result = persist_operator_review_proof_package(package_input)
    assert result["package_status"] == PACKAGE_STATUS_REJECTED


def test_path_traversal_rejected(durable_archive_root: Path) -> None:
    from src.ops.bounded_futures_testnet_preflight_operator_review_proof_package_contract_v0 import (
        _resolve_under_root,
    )

    destination, errors = _resolve_under_root(durable_archive_root, "../escape")
    assert destination is None
    assert errors


def test_static_glb016_satisfied_authority_flags_remain_false(durable_archive_root: Path) -> None:
    result = persist_operator_review_proof_package(_valid_package_input(durable_archive_root))
    evaluation = evaluate_proof_package_result(result)
    assert evaluation["static_glb016_reproducibility_satisfied"] is True
    assert evaluation["preflight_remains_blocked"] is True
    assert evaluation["ready_for_operator_arming"] is False
    assert evaluation["execution_authorized"] is False
    assert evaluation["live_authorized"] is False
    assert evaluation["zero_order_authorized"] is False
    assert evaluation["non_authorizing"] is True


def test_pe17_consumes_valid_package_proof(durable_archive_root: Path) -> None:
    chain = _chain_artifacts(durable_archive_root)
    package_result = persist_operator_review_proof_package(
        _valid_package_input(durable_archive_root)
    )
    package_eval = evaluate_proof_package_result(package_result)
    review_input = _minimal_review_input(durable_archive_root)
    input_digest = compute_review_input_digest(review_input)
    decision_record = default_minimal_decision_record(
        source_revision=VALID_COMMIT_SHA,
        review_input_digest=input_digest,
        decision=PE19_APPROVE,
        reason_code=REASON_EVIDENCE_COMPLETE,
    )
    review_proof = evaluate_operator_review(
        review_input,
        decision_record,
        review_input_digest=input_digest,
        decision_record_digest=compute_decision_record_digest(decision_record),
    )
    evaluation_input = PreflightCompletenessTruthInput(
        packet=chain["packet"],
        builder_input=chain["inputs"],
        replay_manifest=chain["manifest"],
        replay_artifacts=chain["artifacts"],
        replay_result=chain["replay_result"],
        archive_result=chain["archive_result"],
        source_state_capture_proof=ExplicitContractProof(
            **pe18_explicit_contract_proof_kwargs(chain["capture_result"])
        ),
        source_state_capture_result=chain["capture_result"],
        operator_review_proof=ExplicitContractProof(
            contract_version="bounded_futures_testnet_preflight_operator_review_reproducibility.v0",
            validation_pass=True,
            contract_marker="BOUNDED_FUTURES_TESTNET_PREFLIGHT_OPERATOR_REVIEW_REPRODUCIBILITY_CONTRACT_V0=true",
        ),
        operator_review_result=review_proof,
        operator_review_proof_package_proof=ExplicitContractProof(
            **explicit_contract_proof_kwargs(package_eval)
        ),
        operator_review_proof_package_result=package_eval,
    )
    truth = evaluate_glb016_internal_truth(evaluation_input)
    assert truth["operator_review_proof_package_valid"] is True
    assert truth["glb016_full_preflight_reproducibility_satisfied"] is True
    assert truth["ready_for_operator_arming"] is False


def test_pe17_invalid_package_proof_glb016_false(durable_archive_root: Path) -> None:
    chain = _chain_artifacts(durable_archive_root)
    package_result = persist_operator_review_proof_package(
        _valid_package_input(durable_archive_root)
    )
    package_eval = evaluate_proof_package_result(package_result)
    package_eval = dict(package_eval)
    package_eval["static_glb016_reproducibility_satisfied"] = False
    review_input = _minimal_review_input(durable_archive_root)
    input_digest = compute_review_input_digest(review_input)
    decision_record = default_minimal_decision_record(
        source_revision=VALID_COMMIT_SHA,
        review_input_digest=input_digest,
    )
    review_proof = evaluate_operator_review(
        review_input,
        decision_record,
        review_input_digest=input_digest,
        decision_record_digest=compute_decision_record_digest(decision_record),
    )
    evaluation_input = PreflightCompletenessTruthInput(
        packet=chain["packet"],
        builder_input=chain["inputs"],
        replay_manifest=chain["manifest"],
        replay_artifacts=chain["artifacts"],
        replay_result=chain["replay_result"],
        archive_result=chain["archive_result"],
        source_state_capture_proof=ExplicitContractProof(
            **pe18_explicit_contract_proof_kwargs(chain["capture_result"])
        ),
        source_state_capture_result=chain["capture_result"],
        operator_review_proof=ExplicitContractProof(
            contract_version="bounded_futures_testnet_preflight_operator_review_reproducibility.v0",
            validation_pass=True,
            contract_marker="BOUNDED_FUTURES_TESTNET_PREFLIGHT_OPERATOR_REVIEW_REPRODUCIBILITY_CONTRACT_V0=true",
        ),
        operator_review_result=review_proof,
        operator_review_proof_package_proof=ExplicitContractProof(
            contract_version=OPERATOR_REVIEW_PROOF_PACKAGE_CONTRACT_VERSION,
            validation_pass=True,
            contract_marker=PACKAGE_MARKER,
        ),
        operator_review_proof_package_result=package_eval,
    )
    truth = evaluate_glb016_internal_truth(evaluation_input)
    assert truth["operator_review_proof_package_valid"] is False
    assert truth["glb016_full_preflight_reproducibility_satisfied"] is False


def test_pe_chain_reused_not_duplicated() -> None:
    pe20_text = PE20_MODULE.read_text(encoding="utf-8")
    assert "class BoundedFuturesTestnetPreflightPacket" not in pe20_text
    assert "evaluate_operator_review" in pe20_text
    assert PE19_MODULE.read_text(encoding="utf-8")
    assert PE16_PACKAGE_MARKER in (
        REPO_ROOT
        / "src"
        / "ops"
        / "bounded_futures_testnet_preflight_packet_archive_contract_v0.py"
    ).read_text(encoding="utf-8")
    assert PE17_PACKAGE_MARKER in PE17_MODULE.read_text(encoding="utf-8")
    assert PE18_PACKAGE_MARKER in (
        REPO_ROOT
        / "src"
        / "ops"
        / "bounded_futures_testnet_preflight_source_state_capture_contract_v0.py"
    ).read_text(encoding="utf-8")
    assert CONTRACT_VERSION in (
        REPO_ROOT / "src" / "ops" / "bounded_futures_testnet_preflight_packet_contract_v0.py"
    ).read_text(encoding="utf-8")


def test_no_git_subprocess_or_environment_read(
    monkeypatch: pytest.MonkeyPatch, durable_archive_root: Path
) -> None:
    def _forbidden(*args, **kwargs):
        raise AssertionError("subprocess invocation forbidden")

    monkeypatch.setattr(subprocess, "run", _forbidden)
    monkeypatch.setattr(subprocess, "Popen", _forbidden)
    plan = build_proof_package_plan(_valid_package_input(durable_archive_root))
    assert plan["package_id"]


def test_section5_pe20_crosslink_present() -> None:
    section5 = SECTION5_GAP_OWNER_MAP.read_text(encoding="utf-8")
    assert "bounded_futures_testnet_preflight_operator_review_proof_package_contract_v0" in section5
    assert "PE-20 guard" in section5


def test_ci_audit_pe20_crosslink_present() -> None:
    ci_audit = CI_AUDIT.read_text(encoding="utf-8")
    assert "PE-20 Bounded Futures Testnet preflight operator-review proof package" in ci_audit
    assert "bounded_futures_testnet_preflight_operator_review_proof_package_contract_v0" in ci_audit


def test_post_write_manifest_verify_rc_zero(durable_archive_root: Path) -> None:
    result = persist_operator_review_proof_package(_valid_package_input(durable_archive_root))
    destination = durable_archive_root / result["package_relative_path"]
    verify_ok, _ = verify_manifest_sha256(destination)
    assert verify_ok
    assert result["manifest_verify_rc"] == 0
