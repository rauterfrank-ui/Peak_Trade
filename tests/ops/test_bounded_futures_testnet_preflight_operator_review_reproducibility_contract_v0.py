"""Static + offline bounded Futures Testnet preflight operator-review reproducibility (v0, PE-19).

Docs/tests-only. No runtime, network, credentials, or Testnet start.
"""

from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
from dataclasses import replace
from pathlib import Path

import pytest

from src.ops.bounded_futures_testnet_preflight_operator_review_reproducibility_contract_v0 import (
    CONTRACT_VERSION as PE19_CONTRACT_VERSION,
    DECISION_APPROVE_FOR_SEPARATE_NEXT_PHASE_REVIEW,
    DECISION_REJECT,
    DECISION_REQUEST_CHANGES,
    EXPECTED_OPERATOR_NAME,
    PACKAGE_MARKER,
    REASON_CHANGES_REQUIRED,
    REASON_DIGEST_MISMATCH,
    REASON_EVIDENCE_COMPLETE,
    REASON_EVIDENCE_INCOMPLETE,
    REASON_POLICY_BLOCKED,
    REVIEW_INPUT_REJECTED,
    REVIEW_INPUT_VALID,
    REVIEW_PROOF_VALID,
    REVIEW_PROOF_REJECTED,
    compute_decision_record_digest,
    compute_review_input_digest,
    default_minimal_decision_record,
    default_minimal_operator_review_input,
    evaluate_operator_review,
    explicit_contract_proof_kwargs,
    serialize_decision_record_canonical,
    serialize_review_input_canonical,
    validate_decision_record,
    validate_review_input,
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
    OPERATOR_REVIEW_CONTRACT_VERSION,
    PACKAGE_MARKER as PE17_PACKAGE_MARKER,
    SOURCE_STATE_CAPTURE_CONTRACT_VERSION,
    TRUTH_READY_FOR_SEPARATE_OPERATOR_REVIEW,
    TRUTH_STATIC_CHAIN_ADDITIONAL_OPEN,
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
    compute_source_state_digest,
    default_minimal_source_state_capture_input,
    explicit_contract_proof_kwargs as pe18_explicit_contract_proof_kwargs,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
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
PE18_MODULE = (
    REPO_ROOT
    / "src"
    / "ops"
    / "bounded_futures_testnet_preflight_source_state_capture_contract_v0.py"
)
PE13_MODULE = REPO_ROOT / "src" / "ops" / "bounded_futures_testnet_preflight_packet_contract_v0.py"
PE14_MODULE = (
    REPO_ROOT / "src" / "ops" / "bounded_futures_testnet_preflight_packet_builder_contract_v0.py"
)
PE15_MODULE = (
    REPO_ROOT / "src" / "ops" / "bounded_futures_testnet_preflight_packet_replay_contract_v0.py"
)
PE16_MODULE = (
    REPO_ROOT / "src" / "ops" / "bounded_futures_testnet_preflight_packet_archive_contract_v0.py"
)
SECTION5_GAP_OWNER_MAP = (
    REPO_ROOT / "docs" / "ops" / "planning" / "SECTION5_PREFLIGHT_GAP_OWNER_MAP_CONTRACT_V0.md"
)
CI_AUDIT = REPO_ROOT / "docs" / "ops" / "CI_AUDIT_KNOWN_ISSUES.md"

TEST_PACKAGE_MARKER = (
    "BOUNDED_FUTURES_TESTNET_PREFLIGHT_OPERATOR_REVIEW_REPRODUCIBILITY_GUARD_V0=true"
)
_CLASS4_SCOPED_EXCEPTION_MARKER = "BOUNDED_FUTURES_TESTNET_PREFLIGHT_OPERATOR_REVIEW_REPRODUCIBILITY_GUARD_CLASS4_SCOPED_EXCEPTION_V0=true"
GENERIC_FUTURES_INSTRUMENT = "PF_ETHUSD"
VALID_COMMIT_SHA = "abcdef0123456789abcdef0123456789abcdef01"
DEFAULT_MACHINE_SUMMARY = "VERDICT=PLANNED\nFUTURES_ONLY=true\nPREFLIGHT_REMAINS_BLOCKED=true\n"
DEFAULT_RECOMMENDED_NEXT_STEP = "# Recommended next step\n\nNon-authorizing review only.\n"


def _durable_root(tmp_path: Path) -> Path:
    path = REPO_ROOT / "tests" / ".pytest_archive_roots" / f"pe19_{tmp_path.name}"
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
        "capture_input": capture_input,
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


def _valid_review_proof(
    durable_archive_root: Path, *, decision: str = DECISION_APPROVE_FOR_SEPARATE_NEXT_PHASE_REVIEW
):
    review_input = _minimal_review_input(durable_archive_root)
    input_digest = compute_review_input_digest(review_input)
    reason = (
        REASON_EVIDENCE_COMPLETE
        if decision == DECISION_APPROVE_FOR_SEPARATE_NEXT_PHASE_REVIEW
        else REASON_EVIDENCE_INCOMPLETE
        if decision == DECISION_REJECT
        else REASON_CHANGES_REQUIRED
    )
    decision_record = default_minimal_decision_record(
        source_revision=VALID_COMMIT_SHA,
        review_input_digest=input_digest,
        decision=decision,
        reason_code=reason,
    )
    return evaluate_operator_review(
        review_input,
        decision_record,
        review_input_digest=input_digest,
        decision_record_digest=compute_decision_record_digest(decision_record),
    )


def test_package_marker_present() -> None:
    text = Path(__file__).read_text(encoding="utf-8")
    assert TEST_PACKAGE_MARKER in text
    assert _CLASS4_SCOPED_EXCEPTION_MARKER in text
    assert PACKAGE_MARKER in PE19_MODULE.read_text(encoding="utf-8")


def test_valid_review_input_passes(durable_archive_root: Path) -> None:
    review_input = _minimal_review_input(durable_archive_root)
    assert validate_review_input(review_input) == []


def test_review_input_serialization_deterministic(durable_archive_root: Path) -> None:
    review_input = _minimal_review_input(durable_archive_root)
    first = serialize_review_input_canonical(review_input)
    second = serialize_review_input_canonical(review_input)
    assert first == second
    assert len(compute_review_input_digest(review_input)) == 64


def test_review_input_mapping_order_irrelevant(durable_archive_root: Path) -> None:
    review_input = _minimal_review_input(durable_archive_root)
    mapping = {
        "review_contract_version": PE19_CONTRACT_VERSION,
        "review_input_schema_version": "bounded_futures_testnet_preflight_operator_review_input.serialization.v0",
        "source_revision": review_input.source_revision,
        "repository_identity": review_input.repository_identity,
        "contract_versions": {
            "pe19_operator_review": PE19_CONTRACT_VERSION,
            "pe12_lifecycle": review_input.contract_versions.pe12_lifecycle,
            "pe13_packet": review_input.contract_versions.pe13_packet,
            "pe14_builder": review_input.contract_versions.pe14_builder,
            "pe15_replay": review_input.contract_versions.pe15_replay,
            "pe16_archive": review_input.contract_versions.pe16_archive,
            "pe17_completeness_truth": review_input.contract_versions.pe17_completeness_truth,
            "pe18_source_state_capture": review_input.contract_versions.pe18_source_state_capture,
        },
        "evidence_chain": {
            "manifest_verify_rc": 0,
            "archive_manifest_digest": review_input.evidence_chain.archive_manifest_digest,
            "archive_identity": review_input.evidence_chain.archive_identity,
            "completeness_truth_identity": review_input.evidence_chain.completeness_truth_identity,
            "input_capture_digest": review_input.evidence_chain.input_capture_digest,
            "packet_digest": review_input.evidence_chain.packet_digest,
            "replay_manifest_digest": review_input.evidence_chain.replay_manifest_digest,
            "source_state_digest": review_input.evidence_chain.source_state_digest,
        },
        "reviewed_scope": review_input.reviewed_scope,
        "safety_snapshot": {
            "credentials_allowed": False,
            "execution_authorized": False,
            "followup_run_gate": FOLLOWUP_RUN_GATE,
            "live_authorized": False,
            "network_allowed": False,
            "operator_go_present": False,
            "orders_allowed": False,
            "preflight_remains_blocked": True,
            "ready_for_operator_arming": False,
            "scheduler_runtime_allowed": False,
        },
        "futures_only": True,
        "environment": "testnet",
        "non_authorizing": True,
    }
    canonical = json.dumps(mapping, sort_keys=True, separators=(",", ":"))
    assert canonical == serialize_review_input_canonical(review_input)


def test_review_input_relevant_change_alters_digest(durable_archive_root: Path) -> None:
    review_input = _minimal_review_input(durable_archive_root)
    original = compute_review_input_digest(review_input)
    mutated = replace(
        review_input,
        evidence_chain=replace(review_input.evidence_chain, packet_digest="f" * 64),
    )
    assert compute_review_input_digest(mutated) != original


def test_review_input_manifest_verify_rc_nonzero_fail_closed(durable_archive_root: Path) -> None:
    review_input = replace(
        _minimal_review_input(durable_archive_root),
        evidence_chain=replace(
            _minimal_review_input(durable_archive_root).evidence_chain,
            manifest_verify_rc=1,
        ),
    )
    assert validate_review_input(review_input)
    proof = evaluate_operator_review(
        review_input,
        default_minimal_decision_record(
            source_revision=VALID_COMMIT_SHA,
            review_input_digest="a" * 64,
        ),
    )
    assert proof["review_valid"] is False


def test_review_input_missing_pe_binding_fail_closed(durable_archive_root: Path) -> None:
    review_input = replace(
        _minimal_review_input(durable_archive_root),
        evidence_chain=replace(
            _minimal_review_input(durable_archive_root).evidence_chain,
            source_state_digest="",
        ),
    )
    assert validate_review_input(review_input)


def test_decision_approve_valid(durable_archive_root: Path) -> None:
    proof = _valid_review_proof(durable_archive_root)
    assert proof["review_proof_status"] == REVIEW_PROOF_VALID
    assert proof["decision"] == DECISION_APPROVE_FOR_SEPARATE_NEXT_PHASE_REVIEW
    assert proof["review_reproducible"] is True
    assert proof["ready_for_operator_arming"] is False
    assert proof["execution_authorized"] is False
    assert proof["live_authorized"] is False


def test_decision_reject_valid(durable_archive_root: Path) -> None:
    proof = _valid_review_proof(durable_archive_root, decision=DECISION_REJECT)
    assert proof["review_valid"] is True
    assert proof["decision"] == DECISION_REJECT
    assert proof["ready_for_operator_arming"] is False


def test_decision_request_changes_valid(durable_archive_root: Path) -> None:
    proof = _valid_review_proof(durable_archive_root, decision=DECISION_REQUEST_CHANGES)
    assert proof["review_valid"] is True
    assert proof["decision"] == DECISION_REQUEST_CHANGES


def test_no_default_approve(durable_archive_root: Path) -> None:
    review_input = _minimal_review_input(durable_archive_root)
    bad_record = default_minimal_decision_record(
        source_revision=VALID_COMMIT_SHA,
        review_input_digest=compute_review_input_digest(review_input),
        decision="",
        reason_code=REASON_EVIDENCE_COMPLETE,
    )
    assert validate_decision_record(bad_record, review_input=review_input)


def test_unknown_decision_fail_closed(durable_archive_root: Path) -> None:
    review_input = _minimal_review_input(durable_archive_root)
    bad_record = default_minimal_decision_record(
        source_revision=VALID_COMMIT_SHA,
        review_input_digest=compute_review_input_digest(review_input),
        decision="execute",
        reason_code=REASON_POLICY_BLOCKED,
    )
    assert validate_decision_record(bad_record, review_input=review_input)


def test_authority_decision_fail_closed(durable_archive_root: Path) -> None:
    review_input = _minimal_review_input(durable_archive_root)
    bad_record = default_minimal_decision_record(
        source_revision=VALID_COMMIT_SHA,
        review_input_digest=compute_review_input_digest(review_input),
        decision="live",
        reason_code=REASON_POLICY_BLOCKED,
    )
    assert validate_decision_record(bad_record, review_input=review_input)


def test_missing_operator_fail_closed(durable_archive_root: Path) -> None:
    review_input = _minimal_review_input(durable_archive_root)
    bad_record = default_minimal_decision_record(
        source_revision=VALID_COMMIT_SHA,
        review_input_digest=compute_review_input_digest(review_input),
        operator_name="",
    )
    assert validate_decision_record(bad_record, review_input=review_input)


def test_wrong_operator_fail_closed(durable_archive_root: Path) -> None:
    review_input = _minimal_review_input(durable_archive_root)
    bad_record = default_minimal_decision_record(
        source_revision=VALID_COMMIT_SHA,
        review_input_digest=compute_review_input_digest(review_input),
        operator_name="Other Operator",
    )
    assert validate_decision_record(bad_record, review_input=review_input)
    assert EXPECTED_OPERATOR_NAME == "Frank Rauter"


def test_inconsistent_reason_code_fail_closed(durable_archive_root: Path) -> None:
    review_input = _minimal_review_input(durable_archive_root)
    bad_record = default_minimal_decision_record(
        source_revision=VALID_COMMIT_SHA,
        review_input_digest=compute_review_input_digest(review_input),
        decision=DECISION_REJECT,
        reason_code=REASON_EVIDENCE_COMPLETE,
    )
    assert validate_decision_record(bad_record, review_input=review_input)


def test_decision_digest_changes_with_decision(durable_archive_root: Path) -> None:
    review_input = _minimal_review_input(durable_archive_root)
    digest_value = compute_review_input_digest(review_input)
    approve = default_minimal_decision_record(
        source_revision=VALID_COMMIT_SHA,
        review_input_digest=digest_value,
        decision=DECISION_APPROVE_FOR_SEPARATE_NEXT_PHASE_REVIEW,
        reason_code=REASON_EVIDENCE_COMPLETE,
    )
    reject = default_minimal_decision_record(
        source_revision=VALID_COMMIT_SHA,
        review_input_digest=digest_value,
        decision=DECISION_REJECT,
        reason_code=REASON_EVIDENCE_INCOMPLETE,
    )
    assert compute_decision_record_digest(approve) != compute_decision_record_digest(reject)


def test_decision_digest_changes_with_operator(durable_archive_root: Path) -> None:
    review_input = _minimal_review_input(durable_archive_root)
    digest_value = compute_review_input_digest(review_input)
    first = default_minimal_decision_record(
        source_revision=VALID_COMMIT_SHA,
        review_input_digest=digest_value,
        operator_name=EXPECTED_OPERATOR_NAME,
    )
    second = replace(first, operator_name="Frank Rauter ")
    assert compute_decision_record_digest(first) != compute_decision_record_digest(second)


def test_review_proof_digest_mismatch_fail_closed(durable_archive_root: Path) -> None:
    review_input = _minimal_review_input(durable_archive_root)
    input_digest = compute_review_input_digest(review_input)
    decision_record = default_minimal_decision_record(
        source_revision=VALID_COMMIT_SHA,
        review_input_digest=input_digest,
    )
    proof = evaluate_operator_review(
        review_input,
        decision_record,
        review_input_digest="0" * 64,
        decision_record_digest=compute_decision_record_digest(decision_record),
    )
    assert proof["review_valid"] is False
    assert proof["review_input_digest_matches"] is False


def test_review_proof_source_revision_mismatch_fail_closed(durable_archive_root: Path) -> None:
    review_input = _minimal_review_input(durable_archive_root)
    input_digest = compute_review_input_digest(review_input)
    decision_record = default_minimal_decision_record(
        source_revision="fedcba9876543210fedcba9876543210fedcba98",
        review_input_digest=input_digest,
    )
    proof = evaluate_operator_review(
        review_input,
        decision_record,
        review_input_digest=input_digest,
        decision_record_digest=compute_decision_record_digest(decision_record),
    )
    assert proof["review_valid"] is False


def test_boolean_true_without_contract_proof_not_accepted(durable_archive_root: Path) -> None:
    chain = _chain_artifacts(durable_archive_root)
    capture_result = chain["capture_result"]
    evaluation_input = PreflightCompletenessTruthInput(
        packet=chain["packet"],
        builder_input=chain["inputs"],
        replay_manifest=chain["manifest"],
        replay_artifacts=chain["artifacts"],
        replay_result=chain["replay_result"],
        archive_result=chain["archive_result"],
        source_state_capture_proof=ExplicitContractProof(
            **pe18_explicit_contract_proof_kwargs(capture_result)
        ),
        source_state_capture_result=capture_result,
        operator_review_result={"review_valid": True},
    )
    truth = evaluate_glb016_internal_truth(evaluation_input)
    assert truth["operator_review_valid"] is False


def test_pe17_approve_proof_enables_glb016_full(durable_archive_root: Path) -> None:
    chain = _chain_artifacts(durable_archive_root)
    review_proof = _valid_review_proof(durable_archive_root)
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
        operator_review_proof=ExplicitContractProof(**explicit_contract_proof_kwargs(review_proof)),
        operator_review_result=review_proof,
    )
    truth = evaluate_glb016_internal_truth(evaluation_input)
    assert truth["truth_status"] == TRUTH_READY_FOR_SEPARATE_OPERATOR_REVIEW
    assert truth["operator_review_valid"] is True
    assert truth["glb016_full_preflight_reproducibility_satisfied"] is True
    assert truth["ready_for_operator_arming"] is False
    assert truth["execution_authorized"] is False
    assert truth["live_authorized"] is False


def test_pe17_reject_proof_glb016_full_false(durable_archive_root: Path) -> None:
    chain = _chain_artifacts(durable_archive_root)
    review_proof = _valid_review_proof(durable_archive_root, decision=DECISION_REJECT)
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
        operator_review_proof=ExplicitContractProof(**explicit_contract_proof_kwargs(review_proof)),
        operator_review_result=review_proof,
    )
    truth = evaluate_glb016_internal_truth(evaluation_input)
    assert truth["operator_review_valid"] is True
    assert truth["glb016_full_preflight_reproducibility_satisfied"] is False


def test_pe17_request_changes_glb016_full_false(durable_archive_root: Path) -> None:
    chain = _chain_artifacts(durable_archive_root)
    review_proof = _valid_review_proof(durable_archive_root, decision=DECISION_REQUEST_CHANGES)
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
        operator_review_proof=ExplicitContractProof(**explicit_contract_proof_kwargs(review_proof)),
        operator_review_result=review_proof,
    )
    truth = evaluate_glb016_internal_truth(evaluation_input)
    assert truth["glb016_full_preflight_reproducibility_satisfied"] is False


def test_pe17_invalid_proof_glb016_full_false(durable_archive_root: Path) -> None:
    chain = _chain_artifacts(durable_archive_root)
    review_proof = _valid_review_proof(durable_archive_root)
    review_proof = dict(review_proof)
    review_proof["review_valid"] = False
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
            contract_version=OPERATOR_REVIEW_CONTRACT_VERSION,
            validation_pass=True,
            contract_marker=PACKAGE_MARKER,
        ),
        operator_review_result=review_proof,
    )
    truth = evaluate_glb016_internal_truth(evaluation_input)
    assert truth["operator_review_valid"] is False
    assert truth["glb016_full_preflight_reproducibility_satisfied"] is False


def test_pe_chain_reused_not_duplicated() -> None:
    pe19_text = PE19_MODULE.read_text(encoding="utf-8")
    assert "class BoundedFuturesTestnetPreflightPacket" not in pe19_text
    assert PE14_PACKAGE_MARKER in PE14_MODULE.read_text(encoding="utf-8")
    assert PE15_PACKAGE_MARKER in PE15_MODULE.read_text(encoding="utf-8")
    assert PE16_PACKAGE_MARKER in PE16_MODULE.read_text(encoding="utf-8")
    assert PE17_PACKAGE_MARKER in PE17_MODULE.read_text(encoding="utf-8")
    assert PE18_PACKAGE_MARKER in PE18_MODULE.read_text(encoding="utf-8")
    assert CONTRACT_VERSION in PE13_MODULE.read_text(encoding="utf-8")


def test_no_git_subprocess_or_environment_read(monkeypatch: pytest.MonkeyPatch) -> None:
    def _forbidden(*args, **kwargs):
        raise AssertionError("subprocess invocation forbidden")

    monkeypatch.setattr(subprocess, "run", _forbidden)
    monkeypatch.setattr(subprocess, "Popen", _forbidden)
    review_input = default_minimal_operator_review_input(
        source_revision=VALID_COMMIT_SHA,
        packet_digest="a" * 64,
        input_capture_digest="b" * 64,
        replay_manifest_digest="c" * 64,
        archive_identity="archive-id-pe19",
        archive_manifest_digest="d" * 64,
        completeness_truth_identity=COMPLETENESS_CONTRACT_VERSION,
        source_state_digest="e" * 64,
    )
    assert validate_review_input(review_input) == []


def test_section5_pe19_crosslink_present() -> None:
    section5 = SECTION5_GAP_OWNER_MAP.read_text(encoding="utf-8")
    assert (
        "bounded_futures_testnet_preflight_operator_review_reproducibility_contract_v0" in section5
    )
    assert "PE-19 guard" in section5


def test_ci_audit_pe19_crosslink_present() -> None:
    ci_audit = CI_AUDIT.read_text(encoding="utf-8")
    assert "PE-19 Bounded Futures Testnet preflight operator-review reproducibility" in ci_audit
    assert (
        "bounded_futures_testnet_preflight_operator_review_reproducibility_contract_v0" in ci_audit
    )


def test_explicit_contract_proof_version_matches_pe17(durable_archive_root: Path) -> None:
    review_proof = _valid_review_proof(durable_archive_root)
    proof = ExplicitContractProof(**explicit_contract_proof_kwargs(review_proof))
    assert proof.contract_version == OPERATOR_REVIEW_CONTRACT_VERSION
    assert proof.contract_version == PE19_CONTRACT_VERSION
    assert proof.contract_marker == PACKAGE_MARKER
    assert FOLLOWUP_RUN_GATE == "OPERATOR_INPUT_REQUIRED_IN_NEW_CHAT_NO_AUTO_GO"
    assert HASH_ALGORITHM == "sha256"
