"""Static + offline bounded Futures Testnet preflight completeness/truth (v0, PE-17).

Docs/tests-only. No runtime, network, credentials, or Testnet start.
"""

from __future__ import annotations

import hashlib
import shutil
from dataclasses import replace
from pathlib import Path
from typing import Any

import pytest

from src.ops.bounded_futures_testnet_preflight_packet_archive_contract_v0 import (
    PACKAGE_MARKER as PE16_PACKAGE_MARKER,
    PreflightPacketArchiveInput,
    build_archive_plan,
    compute_archive_identity,
    persist_preflight_packet_archive,
)
from src.ops.bounded_futures_testnet_preflight_packet_builder_contract_v0 import (
    BUILDER_VERSION,
    PACKAGE_MARKER as PE14_PACKAGE_MARKER,
    PreflightPacketBuilderInput,
    build_preflight_packet,
    compute_input_capture_digest,
    default_minimal_builder_input,
    serialize_input_capture_canonical,
)
from src.ops.bounded_futures_testnet_preflight_packet_completeness_truth_contract_v0 import (
    COMPLETENESS_COMPLETE,
    COMPLETENESS_CONTRACT_VERSION,
    COMPLETENESS_INCOMPLETE,
    COMPLETENESS_REJECTED,
    OPERATOR_REVIEW_CONTRACT_VERSION,
    PACKAGE_MARKER,
    SOURCE_STATE_CAPTURE_CONTRACT_VERSION,
    TRUTH_BLOCKED_INCOMPLETE,
    TRUTH_READY_FOR_SEPARATE_OPERATOR_REVIEW,
    TRUTH_STATIC_CHAIN_ADDITIONAL_OPEN,
    ExplicitContractProof,
    PreflightCompletenessTruthInput,
    evaluate_glb016_internal_truth,
    evaluate_preflight_completeness_and_truth,
    evaluate_preflight_packet_completeness,
)
from src.ops.bounded_futures_testnet_preflight_packet_contract_v0 import (
    CONTRACT_VERSION,
    FOLLOWUP_RUN_GATE,
    BoundedFuturesTestnetPreflightPacket,
    compute_packet_digest,
    serialize_packet_canonical,
)
from src.ops.bounded_futures_testnet_preflight_packet_replay_contract_v0 import (
    ARTIFACT_CANONICAL_INPUT_CAPTURE,
    ARTIFACT_PACKET_PAYLOAD,
    PACKAGE_MARKER as PE15_PACKAGE_MARKER,
    build_replay_manifest,
    compute_replay_manifest_digest,
    replay_preflight_packet_offline,
    serialize_replay_manifest_canonical,
)
from src.ops.bounded_futures_testnet_preflight_source_state_capture_contract_v0 import (
    PACKAGE_MARKER as PE18_SOURCE_MARKER,
    capture_preflight_source_state,
    default_minimal_source_state_capture_input,
    explicit_contract_proof_kwargs as pe18_explicit_contract_proof_kwargs,
)
from src.ops.bounded_futures_testnet_preflight_operator_review_reproducibility_contract_v0 import (
    evaluate_operator_review,
    explicit_contract_proof_kwargs as pe19_explicit_contract_proof_kwargs,
    default_minimal_decision_record,
    default_minimal_operator_review_input,
    compute_review_input_digest,
    compute_decision_record_digest,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
PE17_MODULE = (
    REPO_ROOT
    / "src"
    / "ops"
    / "bounded_futures_testnet_preflight_packet_completeness_truth_contract_v0.py"
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

TEST_PACKAGE_MARKER = "BOUNDED_FUTURES_TESTNET_PREFLIGHT_PACKET_COMPLETENESS_TRUTH_GUARD_V0=true"
_CLASS4_SCOPED_EXCEPTION_MARKER = "BOUNDED_FUTURES_TESTNET_PREFLIGHT_PACKET_COMPLETENESS_TRUTH_GUARD_CLASS4_SCOPED_EXCEPTION_V0=true"
GENERIC_FUTURES_INSTRUMENT = "PF_ETHUSD"
VALID_COMMIT_SHA = "abcdef0123456789abcdef0123456789abcdef01"
DEFAULT_MACHINE_SUMMARY = (
    "VERDICT=PLANNED\n"
    "FUTURES_ONLY=true\n"
    "PREFLIGHT_REMAINS_BLOCKED=true\n"
    "EXECUTION_AUTHORIZED=false\n"
    "LIVE_AUTHORIZED=false\n"
)
DEFAULT_RECOMMENDED_NEXT_STEP = (
    "# Recommended next step\n\n"
    "Non-authorizing completeness/truth evaluation only. "
    "Operator input required in a new chat before any run.\n"
)


def _durable_root(tmp_path: Path) -> Path:
    path = REPO_ROOT / "tests" / ".pytest_archive_roots" / f"pe17_{tmp_path.name}"
    path.mkdir(parents=True, exist_ok=True)
    return path


def _pe18_pe19_proofs(
    durable_archive_root: Path,
) -> tuple[dict[str, Any], dict[str, Any], ExplicitContractProof, ExplicitContractProof]:
    chain_input = _build_full_chain(durable_archive_root)
    assert chain_input.packet is not None
    assert chain_input.builder_input is not None
    assert chain_input.archive_result is not None
    source_revision = chain_input.builder_input.source_build.source_revision
    packet_digest = compute_packet_digest(chain_input.packet)
    capture_digest = compute_input_capture_digest(chain_input.builder_input)
    manifest_digest = compute_replay_manifest_digest(chain_input.replay_manifest or {})
    archive_input = PreflightPacketArchiveInput(
        archive_root=durable_archive_root,
        builder_input=chain_input.builder_input,
        packet=chain_input.packet,
        replay_manifest=chain_input.replay_manifest,
        replay_artifacts=chain_input.replay_artifacts,
        expected_packet_digest=packet_digest,
        machine_summary_env=DEFAULT_MACHINE_SUMMARY,
        recommended_next_step_md=DEFAULT_RECOMMENDED_NEXT_STEP,
    )
    archive_plan = build_archive_plan(archive_input)
    archive_identity = compute_archive_identity(
        source_revision=source_revision,
        packet_digest=packet_digest,
        input_capture_digest=capture_digest,
        manifest_digest=manifest_digest,
    )
    archive_manifest_digest = archive_plan["manifest_digest"]
    capture_input = default_minimal_source_state_capture_input(
        source_revision=source_revision,
        packet_digest=packet_digest,
        input_capture_digest=capture_digest,
        replay_manifest_digest=manifest_digest,
        archive_identity=archive_identity,
        archive_manifest_digest=archive_manifest_digest,
        completeness_truth_identity=COMPLETENESS_CONTRACT_VERSION,
    )
    capture_result = capture_preflight_source_state(capture_input)
    review_input = default_minimal_operator_review_input(
        source_revision=source_revision,
        packet_digest=packet_digest,
        input_capture_digest=capture_digest,
        replay_manifest_digest=manifest_digest,
        archive_identity=archive_identity,
        archive_manifest_digest=archive_manifest_digest,
        completeness_truth_identity=COMPLETENESS_CONTRACT_VERSION,
        source_state_digest=str(capture_result.get("source_state_digest")),
    )
    review_input_digest = compute_review_input_digest(review_input)
    decision_record = default_minimal_decision_record(
        source_revision=source_revision,
        review_input_digest=review_input_digest,
    )
    review_proof = evaluate_operator_review(
        review_input,
        decision_record,
        review_input_digest=review_input_digest,
        decision_record_digest=compute_decision_record_digest(decision_record),
    )
    return (
        capture_result,
        review_proof,
        ExplicitContractProof(**pe18_explicit_contract_proof_kwargs(capture_result)),
        ExplicitContractProof(**pe19_explicit_contract_proof_kwargs(review_proof)),
    )


@pytest.fixture
def durable_archive_root(tmp_path: Path) -> Path:
    root = _durable_root(tmp_path)
    yield root
    if root.exists():
        shutil.rmtree(root, ignore_errors=True)


def _minimal_input() -> PreflightPacketBuilderInput:
    return default_minimal_builder_input(
        source_revision=VALID_COMMIT_SHA,
        instrument=GENERIC_FUTURES_INSTRUMENT,
    )


def _build_full_chain(
    durable_archive_root: Path,
) -> PreflightCompletenessTruthInput:
    inputs = _minimal_input()
    build_result = build_preflight_packet(inputs)
    assert build_result["build_pass"]
    packet = build_result["packet"]
    assert packet is not None
    packet_digest = compute_packet_digest(packet)
    capture_digest = compute_input_capture_digest(inputs)
    manifest = build_replay_manifest(
        source_revision=inputs.source_build.source_revision,
        canonical_input_capture_digest=capture_digest,
        packet_digest=packet_digest,
    )
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
    archive_result = persist_preflight_packet_archive(archive_input)
    assert archive_result["archive_status"] == "persisted_verified"
    return PreflightCompletenessTruthInput(
        packet=packet,
        builder_input=inputs,
        replay_manifest=manifest,
        replay_artifacts=artifacts,
        replay_result=replay_result,
        archive_result=archive_result,
    )


def test_package_marker_present() -> None:
    text = Path(__file__).read_text(encoding="utf-8")
    assert TEST_PACKAGE_MARKER in text
    assert _CLASS4_SCOPED_EXCEPTION_MARKER in text
    assert PACKAGE_MARKER in PE17_MODULE.read_text(encoding="utf-8")


def test_complete_chain_complete_for_internal_static_truth(durable_archive_root: Path) -> None:
    result = evaluate_preflight_packet_completeness(_build_full_chain(durable_archive_root))
    assert result["completeness_status"] == COMPLETENESS_COMPLETE
    assert result["packet_complete"] is True
    assert result["input_capture_complete"] is True
    assert result["builder_alignment_complete"] is True
    assert result["replay_complete"] is True
    assert result["archive_complete"] is True
    assert result["digest_chain_complete"] is True
    assert result["lifecycle_gates_complete"] is True
    assert result["evidence_requirements_complete"] is True
    assert result["validation_errors"] == []
    assert result["non_authorizing"] is True
    assert result["execution_authorized"] is False
    assert result["live_authorized"] is False


def test_completeness_deterministic(durable_archive_root: Path) -> None:
    evaluation_input = _build_full_chain(durable_archive_root)
    first = evaluate_preflight_packet_completeness(evaluation_input)
    second = evaluate_preflight_packet_completeness(evaluation_input)
    assert first == second


def test_missing_requirements_and_validation_errors_stable_order(
    durable_archive_root: Path,
) -> None:
    evaluation_input = _build_full_chain(durable_archive_root)
    evaluation_input = PreflightCompletenessTruthInput(
        packet=None,
        builder_input=evaluation_input.builder_input,
        replay_manifest=evaluation_input.replay_manifest,
        replay_artifacts=evaluation_input.replay_artifacts,
        replay_result=evaluation_input.replay_result,
        archive_result=evaluation_input.archive_result,
    )
    first = evaluate_preflight_packet_completeness(evaluation_input)
    second = evaluate_preflight_packet_completeness(evaluation_input)
    assert first["missing_requirements"] == second["missing_requirements"]
    assert first["validation_errors"] == second["validation_errors"]


def test_pe13_pe14_pe15_pe16_types_reused_not_duplicated() -> None:
    pe17_text = PE17_MODULE.read_text(encoding="utf-8")
    assert "class BoundedFuturesTestnetPreflightPacket" not in pe17_text
    assert "class PreflightPacketBuilderInput" not in pe17_text
    assert PE14_PACKAGE_MARKER in PE14_MODULE.read_text(encoding="utf-8")
    assert PE15_PACKAGE_MARKER in PE15_MODULE.read_text(encoding="utf-8")
    assert PE16_PACKAGE_MARKER in PE16_MODULE.read_text(encoding="utf-8")
    assert "validate_preflight_packet" in pe17_text
    assert "build_preflight_packet" in pe17_text
    assert "replay_preflight_packet_offline" in pe17_text


@pytest.mark.parametrize(
    "mutator,expected_status",
    [
        (lambda inp: replace(inp, packet=None), COMPLETENESS_INCOMPLETE),
        (lambda inp: replace(inp, builder_input=None), COMPLETENESS_INCOMPLETE),
        (lambda inp: replace(inp, replay_result=None), COMPLETENESS_INCOMPLETE),
        (lambda inp: replace(inp, archive_result=None), COMPLETENESS_INCOMPLETE),
    ],
)
def test_missing_component_incomplete(
    durable_archive_root: Path,
    mutator,
    expected_status: str,
) -> None:
    evaluation_input = mutator(_build_full_chain(durable_archive_root))
    result = evaluate_preflight_packet_completeness(evaluation_input)
    assert result["completeness_status"] == expected_status
    assert result["missing_requirements"]


def test_replay_rejected_incomplete(durable_archive_root: Path) -> None:
    evaluation_input = _build_full_chain(durable_archive_root)
    bad_replay = dict(evaluation_input.replay_result or {})
    bad_replay["replay_status"] = "rejected"
    evaluation_input = replace(evaluation_input, replay_result=bad_replay)
    result = evaluate_preflight_packet_completeness(evaluation_input)
    assert result["completeness_status"] in (COMPLETENESS_INCOMPLETE, COMPLETENESS_REJECTED)
    assert not result["replay_complete"]


def test_archive_not_verified_incomplete(durable_archive_root: Path) -> None:
    evaluation_input = _build_full_chain(durable_archive_root)
    bad_archive = dict(evaluation_input.archive_result or {})
    bad_archive["archive_status"] = "rejected"
    evaluation_input = replace(evaluation_input, archive_result=bad_archive)
    result = evaluate_preflight_packet_completeness(evaluation_input)
    assert result["completeness_status"] in (COMPLETENESS_INCOMPLETE, COMPLETENESS_REJECTED)
    assert not result["archive_complete"]


def test_digest_mismatch_rejected(durable_archive_root: Path) -> None:
    evaluation_input = _build_full_chain(durable_archive_root)
    bad_manifest = dict(evaluation_input.replay_manifest or {})
    bad_manifest["packet_digest"] = "0" * 64
    evaluation_input = replace(evaluation_input, replay_manifest=bad_manifest)
    result = evaluate_preflight_packet_completeness(evaluation_input)
    assert result["completeness_status"] == COMPLETENESS_REJECTED
    assert any("digest" in error for error in result["validation_errors"])


def test_source_revision_mismatch_rejected(durable_archive_root: Path) -> None:
    evaluation_input = _build_full_chain(durable_archive_root)
    assert evaluation_input.builder_input is not None
    bad_input = replace(
        evaluation_input.builder_input,
        source_build=replace(
            evaluation_input.builder_input.source_build,
            source_revision="other-revision",
        ),
    )
    evaluation_input = replace(evaluation_input, builder_input=bad_input)
    result = evaluate_preflight_packet_completeness(evaluation_input)
    assert result["completeness_status"] == COMPLETENESS_REJECTED


def test_version_mismatch_rejected(durable_archive_root: Path) -> None:
    evaluation_input = _build_full_chain(durable_archive_root)
    bad_manifest = dict(evaluation_input.replay_manifest or {})
    bad_manifest["builder_version"] = "wrong.version"
    evaluation_input = replace(evaluation_input, replay_manifest=bad_manifest)
    result = evaluate_preflight_packet_completeness(evaluation_input)
    assert result["completeness_status"] == COMPLETENESS_REJECTED


def test_algorithm_mismatch_rejected(durable_archive_root: Path) -> None:
    evaluation_input = _build_full_chain(durable_archive_root)
    bad_manifest = dict(evaluation_input.replay_manifest or {})
    bad_manifest["hash_algorithm"] = "md5"
    evaluation_input = replace(evaluation_input, replay_manifest=bad_manifest)
    result = evaluate_preflight_packet_completeness(evaluation_input)
    assert result["completeness_status"] == COMPLETENESS_REJECTED


def test_manifest_verify_rc_nonzero_rejected(durable_archive_root: Path) -> None:
    evaluation_input = _build_full_chain(durable_archive_root)
    bad_archive = dict(evaluation_input.archive_result or {})
    bad_archive["manifest_verify_rc"] = 1
    evaluation_input = replace(evaluation_input, archive_result=bad_archive)
    result = evaluate_preflight_packet_completeness(evaluation_input)
    assert result["completeness_status"] == COMPLETENESS_REJECTED


def test_tmp_evidence_rejected(durable_archive_root: Path) -> None:
    evaluation_input = _build_full_chain(durable_archive_root)
    assert evaluation_input.packet is not None
    bad_packet = replace(
        evaluation_input.packet,
        evidence=replace(
            evaluation_input.packet.evidence,
            durable_archive_target="/tmp/evidence",
            tmp_only_evidence=True,
        ),
    )
    evaluation_input = replace(evaluation_input, packet=bad_packet)
    result = evaluate_preflight_packet_completeness(evaluation_input)
    assert result["completeness_status"] == COMPLETENESS_REJECTED


def test_authority_flag_true_rejected(durable_archive_root: Path) -> None:
    evaluation_input = _build_full_chain(durable_archive_root)
    assert evaluation_input.packet is not None
    bad_packet = replace(
        evaluation_input.packet,
        authority_gates=replace(
            evaluation_input.packet.authority_gates,
            execution_authorized=True,
        ),
    )
    evaluation_input = replace(evaluation_input, packet=bad_packet)
    result = evaluate_preflight_packet_completeness(evaluation_input)
    assert result["completeness_status"] == COMPLETENESS_REJECTED


def test_wrong_market_type_rejected(durable_archive_root: Path) -> None:
    evaluation_input = _build_full_chain(durable_archive_root)
    assert evaluation_input.packet is not None
    bad_packet = replace(
        evaluation_input.packet,
        instrument_scope=replace(
            evaluation_input.packet.instrument_scope,
            market_type="spot",
        ),
    )
    evaluation_input = replace(evaluation_input, packet=bad_packet)
    result = evaluate_preflight_packet_completeness(evaluation_input)
    assert result["completeness_status"] == COMPLETENESS_REJECTED


def test_wrong_environment_rejected(durable_archive_root: Path) -> None:
    evaluation_input = _build_full_chain(durable_archive_root)
    assert evaluation_input.packet is not None
    bad_packet = replace(evaluation_input.packet, environment="live")
    evaluation_input = replace(evaluation_input, packet=bad_packet)
    result = evaluate_preflight_packet_completeness(evaluation_input)
    assert result["completeness_status"] == COMPLETENESS_REJECTED


def test_later_lifecycle_phase_rejected(durable_archive_root: Path) -> None:
    evaluation_input = _build_full_chain(durable_archive_root)
    assert evaluation_input.packet is not None
    bad_packet = replace(
        evaluation_input.packet,
        pe12_binding=replace(
            evaluation_input.packet.pe12_binding,
            current_phase="zero_order",
        ),
    )
    evaluation_input = replace(evaluation_input, packet=bad_packet)
    result = evaluate_preflight_packet_completeness(evaluation_input)
    assert result["completeness_status"] == COMPLETENESS_REJECTED


def test_evidence_binding_missing_incomplete(durable_archive_root: Path) -> None:
    evaluation_input = _build_full_chain(durable_archive_root)
    assert evaluation_input.packet is not None
    bad_packet = replace(
        evaluation_input.packet,
        evidence=replace(
            evaluation_input.packet.evidence,
            eer1_required=False,
        ),
    )
    evaluation_input = replace(evaluation_input, packet=bad_packet)
    result = evaluate_preflight_packet_completeness(evaluation_input)
    assert result["completeness_status"] in (COMPLETENESS_INCOMPLETE, COMPLETENESS_REJECTED)


def test_truth_static_chain_additional_requirements_open(durable_archive_root: Path) -> None:
    evaluation_input = _build_full_chain(durable_archive_root)
    truth = evaluate_glb016_internal_truth(evaluation_input)
    assert truth["truth_status"] == TRUTH_STATIC_CHAIN_ADDITIONAL_OPEN
    assert truth["internal_static_chain_complete"] is True
    assert truth["source_state_capture_valid"] is False
    assert truth["operator_review_valid"] is False
    assert truth["glb016_full_preflight_reproducibility_satisfied"] is False
    assert truth["ready_for_operator_arming"] is False
    assert truth["execution_authorized"] is False
    assert truth["live_authorized"] is False


def test_source_state_true_without_valid_proof_not_accepted(durable_archive_root: Path) -> None:
    evaluation_input = _build_full_chain(durable_archive_root)
    evaluation_input = replace(
        evaluation_input,
        source_state_capture_proof=ExplicitContractProof(
            contract_version=SOURCE_STATE_CAPTURE_CONTRACT_VERSION,
            validation_pass=False,
        ),
    )
    truth = evaluate_glb016_internal_truth(evaluation_input)
    assert truth["source_state_capture_present"] is True
    assert truth["source_state_capture_valid"] is False
    assert truth["truth_status"] == TRUTH_STATIC_CHAIN_ADDITIONAL_OPEN


def test_operator_review_true_without_valid_proof_not_accepted(
    durable_archive_root: Path,
) -> None:
    evaluation_input = _build_full_chain(durable_archive_root)
    evaluation_input = replace(
        evaluation_input,
        operator_review_proof=ExplicitContractProof(
            contract_version=OPERATOR_REVIEW_CONTRACT_VERSION,
            validation_pass=False,
        ),
    )
    truth = evaluate_glb016_internal_truth(evaluation_input)
    assert truth["operator_review_reproducible"] is True
    assert truth["operator_review_valid"] is False
    assert truth["truth_status"] == TRUTH_STATIC_CHAIN_ADDITIONAL_OPEN


def test_both_requirements_valid_explicit_ready_for_separate_operator_review(
    durable_archive_root: Path,
) -> None:
    evaluation_input = _build_full_chain(durable_archive_root)
    capture_result, review_proof, source_proof, operator_proof = _pe18_pe19_proofs(
        durable_archive_root
    )
    evaluation_input = replace(
        evaluation_input,
        source_state_capture_proof=source_proof,
        source_state_capture_result=capture_result,
        operator_review_proof=operator_proof,
        operator_review_result=review_proof,
    )
    truth = evaluate_glb016_internal_truth(evaluation_input)
    assert truth["truth_status"] == TRUTH_READY_FOR_SEPARATE_OPERATOR_REVIEW
    assert truth["glb016_full_preflight_reproducibility_satisfied"] is True
    assert truth["ready_for_operator_arming"] is False
    assert truth["execution_authorized"] is False
    assert truth["live_authorized"] is False


def test_incomplete_chain_truth_blocked(durable_archive_root: Path) -> None:
    evaluation_input = _build_full_chain(durable_archive_root)
    evaluation_input = replace(evaluation_input, archive_result=None)
    truth = evaluate_glb016_internal_truth(evaluation_input)
    assert truth["truth_status"] == TRUTH_BLOCKED_INCOMPLETE
    assert truth["internal_static_chain_complete"] is False


def test_truth_deterministic(durable_archive_root: Path) -> None:
    evaluation_input = _build_full_chain(durable_archive_root)
    first = evaluate_glb016_internal_truth(evaluation_input)
    second = evaluate_glb016_internal_truth(evaluation_input)
    assert first == second


def test_combined_evaluation_wrapper(durable_archive_root: Path) -> None:
    combined = evaluate_preflight_completeness_and_truth(_build_full_chain(durable_archive_root))
    assert combined["completeness"]["completeness_status"] == COMPLETENESS_COMPLETE
    assert combined["truth"]["truth_status"] == TRUTH_STATIC_CHAIN_ADDITIONAL_OPEN
    assert combined["non_authorizing"] is True


def test_manifest_digest_stable_binding() -> None:
    inputs = _minimal_input()
    build_result = build_preflight_packet(inputs)
    packet = build_result["packet"]
    assert packet is not None
    packet_digest = compute_packet_digest(packet)
    manifest = build_replay_manifest(
        source_revision=inputs.source_build.source_revision,
        canonical_input_capture_digest=compute_input_capture_digest(inputs),
        packet_digest=packet_digest,
    )
    digest = hashlib.sha256(
        serialize_replay_manifest_canonical(manifest).encode("utf-8")
    ).hexdigest()
    assert len(digest) == 64
    assert CONTRACT_VERSION in PE13_MODULE.read_text(encoding="utf-8")
    assert BUILDER_VERSION in PE14_MODULE.read_text(encoding="utf-8")
    assert "followup_run_gate" in PE17_MODULE.read_text(encoding="utf-8")


def test_section5_pe17_crosslink_present() -> None:
    section5 = SECTION5_GAP_OWNER_MAP.read_text(encoding="utf-8")
    assert "bounded_futures_testnet_preflight_packet_completeness_truth_contract_v0" in section5
    assert "PE-17 guard" in section5


def test_ci_audit_pe17_crosslink_present() -> None:
    ci_audit = CI_AUDIT.read_text(encoding="utf-8")
    assert "PE-17 Bounded Futures Testnet preflight packet completeness" in ci_audit
    assert "bounded_futures_testnet_preflight_packet_completeness_truth_contract_v0" in ci_audit
