"""Bounded Futures Testnet preflight packet completeness + internal truth (v0, PE-17).

Deterministic, offline evaluation of PE-13 through PE-16 artifact completeness and
non-authorizing GLB-016 internal static-truth status. Consumes upstream contract
results only; does not authorize network, credentials, orders, runtime, scheduler,
or live execution.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from src.ops.bounded_futures_testnet_adapter_lifecycle_contract_v0 import (
    PHASE_STATIC_PREFLIGHT,
    PHASE_ZERO_ORDER,
    PREFLIGHT_REMAINS_BLOCKED,
    READY_FOR_OPERATOR_ARMING,
)
from src.ops.bounded_futures_testnet_preflight_packet_builder_contract_v0 import (
    BUILDER_VERSION,
    PreflightPacketBuilderInput,
    build_preflight_packet,
    compute_input_capture_digest,
    validate_builder_inputs,
)
from src.ops.bounded_futures_testnet_preflight_packet_contract_v0 import (
    CONTRACT_VERSION,
    ENVIRONMENT_TESTNET,
    FOLLOWUP_RUN_GATE,
    PRIMARY_EVIDENCE_OWNER,
    BoundedFuturesTestnetPreflightPacket,
    compute_packet_digest,
    validate_preflight_packet,
)
from src.ops.bounded_futures_testnet_preflight_packet_replay_contract_v0 import (
    HASH_ALGORITHM,
    REPLAY_CONTRACT_VERSION,
    replay_preflight_packet_offline,
    validate_replay_manifest,
)

PACKAGE_MARKER = "BOUNDED_FUTURES_TESTNET_PREFLIGHT_PACKET_COMPLETENESS_TRUTH_CONTRACT_V0=true"
COMPLETENESS_CONTRACT_VERSION = "bounded_futures_testnet_preflight_packet_completeness_truth.v0"

SOURCE_STATE_CAPTURE_CONTRACT_VERSION = "bounded_futures_testnet_preflight_source_state_capture.v0"
OPERATOR_REVIEW_CONTRACT_VERSION = (
    "bounded_futures_testnet_preflight_operator_review_reproducibility.v0"
)

COMPLETENESS_COMPLETE = "complete_for_internal_static_truth"
COMPLETENESS_INCOMPLETE = "incomplete"
COMPLETENESS_REJECTED = "rejected"

TRUTH_BLOCKED_INCOMPLETE = "blocked_incomplete"
TRUTH_STATIC_CHAIN_ADDITIONAL_OPEN = "static_chain_complete_additional_requirements_open"
TRUTH_READY_FOR_SEPARATE_OPERATOR_REVIEW = "ready_for_separate_operator_review"

_HARD_REJECTION_SUBSTRINGS = (
    "mismatch",
    "must be false",
    "must be true",
    "rejected",
    "invalid",
    "authority",
    "operator_go",
    "manifest_verify_rc",
    "/tmp",
    "unknown field",
    "algorithm",
    "collision",
    "traversal",
    "escapes",
)


@dataclass(frozen=True)
class ExplicitContractProof:
    contract_version: str
    validation_pass: bool
    contract_marker: str | None = None


@dataclass(frozen=True)
class PreflightCompletenessTruthInput:
    packet: BoundedFuturesTestnetPreflightPacket | None = None
    builder_input: PreflightPacketBuilderInput | None = None
    replay_manifest: dict[str, Any] | None = None
    replay_artifacts: dict[str, str] | None = None
    replay_result: dict[str, Any] | None = None
    archive_result: dict[str, Any] | None = None
    source_state_capture_proof: ExplicitContractProof | None = None
    operator_review_proof: ExplicitContractProof | None = None


def _sorted_unique(items: list[str]) -> list[str]:
    return sorted(dict.fromkeys(items))


def _is_hard_rejection(error: str) -> bool:
    lowered = error.lower()
    return any(fragment in lowered for fragment in _HARD_REJECTION_SUBSTRINGS)


def _proof_valid(
    proof: ExplicitContractProof | None,
    *,
    expected_contract_version: str,
    expected_marker: str | None = None,
) -> bool:
    if proof is None:
        return False
    if not proof.validation_pass:
        return False
    if proof.contract_version != expected_contract_version:
        return False
    if expected_marker is not None and proof.contract_marker != expected_marker:
        return False
    return True


def _evaluate_packet_contract(
    packet: BoundedFuturesTestnetPreflightPacket | None,
) -> tuple[bool, list[str], list[str]]:
    errors: list[str] = []
    if packet is None:
        return False, ["packet_contract: packet required"], []

    validation = validate_preflight_packet(packet)
    if not validation["validation_pass"]:
        errors.extend(f"packet_contract: {reason}" for reason in validation["fail_reasons"])
    if packet.contract_version != CONTRACT_VERSION:
        errors.append(f"packet_contract: contract_version must be {CONTRACT_VERSION!r}")
    if not packet.futures_only:
        errors.append("packet_contract: futures_only must be true")
    if packet.environment != ENVIRONMENT_TESTNET:
        errors.append(f"packet_contract: environment must be {ENVIRONMENT_TESTNET!r}")
    if not packet.non_authorizing:
        errors.append("packet_contract: non_authorizing must be true")

    gates = packet.authority_gates
    for flag_name, flag_value in (
        ("credentials_allowed", gates.credentials_allowed),
        ("network_allowed", gates.network_allowed),
        ("orders_allowed", gates.orders_allowed),
        ("runtime_allowed", gates.runtime_allowed),
        ("scheduler_allowed", gates.scheduler_allowed),
        ("execution_authorized", gates.execution_authorized),
        ("live_authorized", gates.live_authorized),
    ):
        if flag_value:
            errors.append(f"packet_contract: {flag_name} must be false")
    if gates.operator_go_present:
        errors.append("packet_contract: operator_go_present must be false")
    if gates.followup_run_gate != FOLLOWUP_RUN_GATE:
        errors.append(f"packet_contract: followup_run_gate must be {FOLLOWUP_RUN_GATE!r}")

    digest = compute_packet_digest(packet)
    if not digest or len(digest) != 64:
        errors.append("packet_contract: packet digest invalid")

    complete = not errors
    missing = [] if complete else ["packet_contract"]
    validation_errors = errors if complete or _is_hard_rejection(" ".join(errors)) else errors
    return complete, missing, validation_errors


def _evaluate_input_capture(
    builder_input: PreflightPacketBuilderInput | None,
    packet: BoundedFuturesTestnetPreflightPacket | None,
) -> tuple[bool, list[str], list[str]]:
    errors: list[str] = []
    if builder_input is None:
        return False, ["input_capture: canonical input capture required"], []

    input_errors = validate_builder_inputs(builder_input)
    errors.extend(f"input_capture: {reason}" for reason in input_errors)
    if builder_input.source_build.builder_version != BUILDER_VERSION:
        errors.append(f"input_capture: builder_version must be {BUILDER_VERSION!r}")
    if builder_input.source_build.contract_version != CONTRACT_VERSION:
        errors.append(f"input_capture: contract_version must be {CONTRACT_VERSION!r}")

    capture_digest = compute_input_capture_digest(builder_input)
    if not capture_digest or len(capture_digest) != 64:
        errors.append("input_capture: capture digest invalid")

    if packet is not None and packet.source_revision != builder_input.source_build.source_revision:
        errors.append("input_capture: source_revision binding mismatch with packet")

    complete = not errors
    missing = [] if complete else ["input_capture"]
    return complete, missing, errors


def _evaluate_builder_alignment(
    builder_input: PreflightPacketBuilderInput | None,
    packet: BoundedFuturesTestnetPreflightPacket | None,
) -> tuple[bool, list[str], list[str]]:
    errors: list[str] = []
    if builder_input is None or packet is None:
        return False, ["builder_alignment: builder input and packet required"], []

    build_result = build_preflight_packet(builder_input)
    if not build_result["build_pass"]:
        errors.extend(
            f"builder_alignment: {reason}" for reason in build_result.get("fail_reasons", [])
        )
    rebuilt_packet = build_result.get("packet")
    if rebuilt_packet is None:
        errors.append("builder_alignment: deterministic build produced no packet")
    else:
        rebuilt_digest = compute_packet_digest(rebuilt_packet)
        packet_digest = compute_packet_digest(packet)
        if rebuilt_digest != packet_digest:
            errors.append("builder_alignment: rebuilt packet_digest mismatch")
        if rebuilt_packet.source_revision != packet.source_revision:
            errors.append("builder_alignment: source_revision mismatch")

    complete = not errors
    missing = [] if complete else ["builder_alignment"]
    return complete, missing, errors


def _evaluate_replay(
    *,
    builder_input: PreflightPacketBuilderInput | None,
    packet: BoundedFuturesTestnetPreflightPacket | None,
    replay_manifest: dict[str, Any] | None,
    replay_artifacts: dict[str, str] | None,
    replay_result: dict[str, Any] | None,
) -> tuple[bool, list[str], list[str]]:
    errors: list[str] = []
    if replay_result is None:
        return False, ["replay: replay result required"], []

    if replay_result.get("replay_status") != "verified":
        errors.append("replay: replay_status must be verified")
    if replay_result.get("manifest_valid") is not True:
        errors.append("replay: manifest_valid must be true")
    if replay_result.get("non_authorizing") is not True:
        errors.append("replay: non_authorizing must be true")
    for flag in ("execution_authorized", "live_authorized"):
        if replay_result.get(flag) is True:
            errors.append(f"replay: {flag} must be false")

    if replay_manifest is not None:
        errors.extend(f"replay: {reason}" for reason in validate_replay_manifest(replay_manifest))

    if builder_input is not None and packet is not None:
        expected_digest = compute_packet_digest(packet)
        recomputed = replay_preflight_packet_offline(
            canonical_input_capture=builder_input,
            expected_packet_digest=expected_digest,
            manifest=replay_manifest,
            artifacts=replay_artifacts,
            packet_payload=packet,
        )
        if recomputed["replay_status"] != "verified":
            errors.extend(f"replay: {reason}" for reason in recomputed["validation_errors"])

    complete = not errors
    missing = [] if complete else ["replay"]
    return complete, missing, errors


def _evaluate_archive(
    archive_result: dict[str, Any] | None,
) -> tuple[bool, list[str], list[str]]:
    errors: list[str] = []
    if archive_result is None:
        return False, ["archive: archive result required"], []

    if archive_result.get("archive_status") != "persisted_verified":
        errors.append("archive: archive_status must be persisted_verified")
    if archive_result.get("durable_destination_valid") is not True:
        errors.append("archive: durable_destination_valid must be true")
    if archive_result.get("required_artifacts_present") is not True:
        errors.append("archive: required_artifacts_present must be true")
    if archive_result.get("manifest_written") is not True:
        errors.append("archive: manifest_written must be true")
    if archive_result.get("manifest_verify_rc") != 0:
        errors.append("archive: manifest_verify_rc must be 0")
    if archive_result.get("replay_verified") is not True:
        errors.append("archive: replay_verified must be true")
    if archive_result.get("packet_digest_matches") is not True:
        errors.append("archive: packet_digest_matches must be true")
    if archive_result.get("input_capture_digest_matches") is not True:
        errors.append("archive: input_capture_digest_matches must be true")
    if archive_result.get("collision_detected") is True:
        errors.append("archive: collision_detected must be false")
    if archive_result.get("non_authorizing") is not True:
        errors.append("archive: non_authorizing must be true")
    for flag in ("execution_authorized", "live_authorized"):
        if archive_result.get(flag) is True:
            errors.append(f"archive: {flag} must be false")

    archive_errors = archive_result.get("validation_errors") or []
    if archive_errors:
        errors.extend(f"archive: {reason}" for reason in archive_errors)

    complete = not errors
    missing = [] if complete else ["archive"]
    return complete, missing, errors


def _evaluate_digest_chain(
    *,
    builder_input: PreflightPacketBuilderInput | None,
    packet: BoundedFuturesTestnetPreflightPacket | None,
    replay_manifest: dict[str, Any] | None,
    archive_result: dict[str, Any] | None,
) -> tuple[bool, list[str], list[str]]:
    errors: list[str] = []
    if builder_input is None or packet is None or replay_manifest is None:
        return False, ["digest_chain: packet, capture, and replay manifest required"], []

    capture_digest = compute_input_capture_digest(builder_input)
    packet_digest = compute_packet_digest(packet)
    if replay_manifest.get("canonical_input_capture_digest") != capture_digest:
        errors.append("digest_chain: capture digest mismatch in replay manifest")
    if replay_manifest.get("packet_digest") != packet_digest:
        errors.append("digest_chain: packet digest mismatch in replay manifest")
    if replay_manifest.get("hash_algorithm") != HASH_ALGORITHM:
        errors.append(f"digest_chain: hash_algorithm must be {HASH_ALGORITHM!r}")
    if replay_manifest.get("source_revision") != builder_input.source_build.source_revision:
        errors.append("digest_chain: source_revision mismatch")
    for version_field, expected in (
        ("packet_contract_version", CONTRACT_VERSION),
        ("builder_version", BUILDER_VERSION),
        ("replay_contract_version", REPLAY_CONTRACT_VERSION),
    ):
        if replay_manifest.get(version_field) != expected:
            errors.append(f"digest_chain: {version_field} mismatch")

    if archive_result is not None:
        if archive_result.get("packet_digest_matches") is False:
            errors.append("digest_chain: archive packet_digest_matches false")
        if archive_result.get("input_capture_digest_matches") is False:
            errors.append("digest_chain: archive input_capture_digest_matches false")

    complete = not errors
    missing = [] if complete else ["digest_chain"]
    return complete, missing, errors


def _evaluate_lifecycle_gates(
    packet: BoundedFuturesTestnetPreflightPacket | None,
) -> tuple[bool, list[str], list[str]]:
    errors: list[str] = []
    if packet is None:
        return False, ["lifecycle_gates: packet required"], []

    pe12 = packet.pe12_binding
    if pe12.current_phase != PHASE_STATIC_PREFLIGHT:
        errors.append(f"lifecycle_gates: current_phase must be {PHASE_STATIC_PREFLIGHT!r}")
    if pe12.allowed_next_phase != PHASE_ZERO_ORDER:
        errors.append(f"lifecycle_gates: allowed_next_phase must be {PHASE_ZERO_ORDER!r}")
    for phase_name, blocked_flag in (
        ("zero_order", pe12.zero_order_blocked),
        ("private_readonly", pe12.private_readonly_blocked),
        ("validate_only", pe12.validate_only_blocked),
        ("tiny_order", pe12.tiny_order_blocked),
    ):
        if not blocked_flag:
            errors.append(f"lifecycle_gates: {phase_name} must remain blocked")

    gates = packet.authority_gates
    if gates.operator_go_present:
        errors.append("lifecycle_gates: operator_go_present must be false")
    if gates.followup_run_gate != FOLLOWUP_RUN_GATE:
        errors.append(f"lifecycle_gates: followup_run_gate must be {FOLLOWUP_RUN_GATE!r}")

    if PREFLIGHT_REMAINS_BLOCKED is not True:
        errors.append("lifecycle_gates: PREFLIGHT_REMAINS_BLOCKED must be true")
    if READY_FOR_OPERATOR_ARMING is not False:
        errors.append("lifecycle_gates: READY_FOR_OPERATOR_ARMING must be false")

    complete = not errors
    missing = [] if complete else ["lifecycle_gates"]
    return complete, missing, errors


def _evaluate_evidence_requirements(
    packet: BoundedFuturesTestnetPreflightPacket | None,
    archive_result: dict[str, Any] | None,
) -> tuple[bool, list[str], list[str]]:
    errors: list[str] = []
    if packet is None:
        return False, ["evidence_requirements: packet required"], []

    evidence = packet.evidence
    if evidence.primary_evidence_owner != PRIMARY_EVIDENCE_OWNER:
        errors.append("evidence_requirements: primary_evidence_owner mismatch")
    if not evidence.durable_archive_target or evidence.durable_archive_target.startswith("/tmp"):
        errors.append("evidence_requirements: durable_archive_target invalid")
    if not evidence.manifest_required:
        errors.append("evidence_requirements: manifest_required must be true")
    if not evidence.manifest_verify_rc_zero:
        errors.append("evidence_requirements: manifest_verify_rc_zero must be true")
    if not evidence.reconciliation_required:
        errors.append("evidence_requirements: reconciliation_required must be true")
    if not evidence.eer1_required:
        errors.append("evidence_requirements: eer1_required must be true")
    if not evidence.post_run_review_required:
        errors.append("evidence_requirements: post_run_review_required must be true")
    if evidence.tmp_only_evidence:
        errors.append("evidence_requirements: tmp_only_evidence must be false")

    if archive_result is None:
        errors.append("evidence_requirements: durable archive wiring result required")
    elif archive_result.get("archive_status") != "persisted_verified":
        errors.append("evidence_requirements: archive must be persisted_verified")

    complete = not errors
    missing = [] if complete else ["evidence_requirements"]
    return complete, missing, errors


def evaluate_preflight_packet_completeness(
    evaluation_input: PreflightCompletenessTruthInput,
) -> dict[str, Any]:
    """Evaluate PE-13..PE-16 completeness; never grants execution or live authority."""
    packet = evaluation_input.packet
    builder_input = evaluation_input.builder_input
    replay_manifest = evaluation_input.replay_manifest
    replay_artifacts = evaluation_input.replay_artifacts
    replay_result = evaluation_input.replay_result
    archive_result = evaluation_input.archive_result

    missing_requirements: list[str] = []
    validation_errors: list[str] = []

    sections: list[tuple[str, bool, list[str], list[str]]] = [
        ("packet", *_evaluate_packet_contract(packet)),
        ("input_capture", *_evaluate_input_capture(builder_input, packet)),
        ("builder_alignment", *_evaluate_builder_alignment(builder_input, packet)),
        (
            "replay",
            *_evaluate_replay(
                builder_input=builder_input,
                packet=packet,
                replay_manifest=replay_manifest,
                replay_artifacts=replay_artifacts,
                replay_result=replay_result,
            ),
        ),
        ("archive", *_evaluate_archive(archive_result)),
        (
            "digest_chain",
            *_evaluate_digest_chain(
                builder_input=builder_input,
                packet=packet,
                replay_manifest=replay_manifest,
                archive_result=archive_result,
            ),
        ),
        ("lifecycle_gates", *_evaluate_lifecycle_gates(packet)),
        ("evidence_requirements", *_evaluate_evidence_requirements(packet, archive_result)),
    ]

    flags = {
        "packet_complete": False,
        "input_capture_complete": False,
        "builder_alignment_complete": False,
        "replay_complete": False,
        "archive_complete": False,
        "digest_chain_complete": False,
        "lifecycle_gates_complete": False,
        "evidence_requirements_complete": False,
    }
    for name, complete, missing, errors in sections:
        flags[f"{name}_complete"] = complete
        missing_requirements.extend(missing)
        validation_errors.extend(errors)

    missing_requirements = _sorted_unique(missing_requirements)
    validation_errors = _sorted_unique(validation_errors)

    all_complete = all(complete for _, complete, _, _ in sections)
    has_hard_rejection = any(_is_hard_rejection(error) for error in validation_errors)

    if all_complete and not validation_errors:
        completeness_status = COMPLETENESS_COMPLETE
    elif has_hard_rejection:
        completeness_status = COMPLETENESS_REJECTED
    else:
        completeness_status = COMPLETENESS_INCOMPLETE

    return {
        "completeness_contract_version": COMPLETENESS_CONTRACT_VERSION,
        "completeness_status": completeness_status,
        **flags,
        "missing_requirements": missing_requirements,
        "validation_errors": validation_errors,
        "non_authorizing": True,
        "execution_authorized": False,
        "live_authorized": False,
        "followup_run_gate": FOLLOWUP_RUN_GATE,
    }


def evaluate_glb016_internal_truth(
    evaluation_input: PreflightCompletenessTruthInput,
    completeness_result: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Evaluate non-authorizing GLB-016 internal static-truth status."""
    completeness = completeness_result or evaluate_preflight_packet_completeness(evaluation_input)
    validation_errors: list[str] = []
    blocking_requirements: list[str] = []

    internal_static_chain_complete = completeness["completeness_status"] == COMPLETENESS_COMPLETE

    source_proof = evaluation_input.source_state_capture_proof
    operator_proof = evaluation_input.operator_review_proof

    source_state_capture_present = source_proof is not None
    source_state_capture_valid = _proof_valid(
        source_proof,
        expected_contract_version=SOURCE_STATE_CAPTURE_CONTRACT_VERSION,
        expected_marker="BOUNDED_FUTURES_TESTNET_PREFLIGHT_SOURCE_STATE_CAPTURE_CONTRACT_V0=true",
    )
    operator_review_reproducible = operator_proof is not None
    operator_review_valid = _proof_valid(
        operator_proof,
        expected_contract_version=OPERATOR_REVIEW_CONTRACT_VERSION,
        expected_marker=(
            "BOUNDED_FUTURES_TESTNET_PREFLIGHT_OPERATOR_REVIEW_REPRODUCIBILITY_CONTRACT_V0=true"
        ),
    )

    if source_state_capture_present and not source_state_capture_valid:
        validation_errors.append(
            "source_state_capture: present without valid explicit contract proof"
        )
    if operator_review_reproducible and not operator_review_valid:
        validation_errors.append(
            "operator_review: reproducible claim without valid explicit contract proof"
        )

    if completeness["completeness_status"] in (COMPLETENESS_INCOMPLETE, COMPLETENESS_REJECTED):
        truth_status = TRUTH_BLOCKED_INCOMPLETE
        blocking_requirements.append("pe13_pe16_internal_chain_incomplete")
        blocking_requirements.extend(completeness["missing_requirements"])
    elif not source_state_capture_valid or not operator_review_valid:
        truth_status = TRUTH_STATIC_CHAIN_ADDITIONAL_OPEN
        if not source_state_capture_valid:
            blocking_requirements.append("canonical_source_state_capture")
        if not operator_review_valid:
            blocking_requirements.append("reproducible_operator_review_semantics")
    else:
        truth_status = TRUTH_READY_FOR_SEPARATE_OPERATOR_REVIEW

    glb016_full = (
        internal_static_chain_complete and source_state_capture_valid and operator_review_valid
    )

    return {
        "truth_contract_version": COMPLETENESS_CONTRACT_VERSION,
        "truth_status": truth_status,
        "internal_static_chain_complete": internal_static_chain_complete,
        "packet_completeness_present": internal_static_chain_complete,
        "source_state_capture_present": source_state_capture_present,
        "source_state_capture_valid": source_state_capture_valid,
        "operator_review_reproducible": operator_review_reproducible,
        "operator_review_valid": operator_review_valid,
        "glb016_full_preflight_reproducibility_satisfied": glb016_full,
        "blocking_requirements": _sorted_unique(blocking_requirements),
        "validation_errors": _sorted_unique(validation_errors),
        "non_authorizing": True,
        "ready_for_operator_arming": False,
        "execution_authorized": False,
        "live_authorized": False,
        "followup_run_gate": FOLLOWUP_RUN_GATE,
    }


def evaluate_preflight_completeness_and_truth(
    evaluation_input: PreflightCompletenessTruthInput,
) -> dict[str, Any]:
    """Combined completeness and internal truth evaluation."""
    completeness = evaluate_preflight_packet_completeness(evaluation_input)
    truth = evaluate_glb016_internal_truth(evaluation_input, completeness)
    return {
        "completeness": completeness,
        "truth": truth,
        "non_authorizing": True,
        "execution_authorized": False,
        "live_authorized": False,
        "followup_run_gate": FOLLOWUP_RUN_GATE,
    }
