"""Bounded Futures Testnet preflight packet offline replay + manifest verification (v0, PE-15).

Deterministic, offline replay of a canonically produced PE-13/PE-14 preflight packet.
Verifies canonical serialization, packet digest, and manifest bindings. Does not authorize
network, credentials, orders, runtime, scheduler, or live execution.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict
from typing import Any

from src.ops.bounded_futures_testnet_preflight_packet_builder_contract_v0 import (
    BUILDER_VERSION,
    PreflightPacketBuilderInput,
    build_preflight_packet,
    compute_input_capture_digest,
    parse_builder_input_from_mapping,
    serialize_input_capture_canonical,
    validate_builder_inputs,
)
from src.ops.bounded_futures_testnet_preflight_packet_contract_v0 import (
    CONTRACT_VERSION,
    ENVIRONMENT_TESTNET,
    FOLLOWUP_RUN_GATE,
    BoundedFuturesTestnetPreflightPacket,
    compute_packet_digest,
    serialize_packet_canonical,
    validate_preflight_packet,
)

PACKAGE_MARKER = "BOUNDED_FUTURES_TESTNET_PREFLIGHT_PACKET_REPLAY_CONTRACT_V0=true"
REPLAY_CONTRACT_VERSION = "bounded_futures_testnet_preflight_packet_replay.v0"
MANIFEST_VERSION = "bounded_futures_testnet_preflight_packet_replay_manifest.v0"
HASH_ALGORITHM = "sha256"

ARTIFACT_CANONICAL_INPUT_CAPTURE = "canonical_input_capture"
ARTIFACT_PACKET_PAYLOAD = "packet_payload"
DEFAULT_ARTIFACT_IDS = (ARTIFACT_CANONICAL_INPUT_CAPTURE, ARTIFACT_PACKET_PAYLOAD)

_MANIFEST_TOP_LEVEL_KEYS = frozenset(
    {
        "manifest_version",
        "packet_contract_version",
        "builder_version",
        "replay_contract_version",
        "source_revision",
        "canonical_input_capture_digest",
        "packet_digest",
        "artifact_ids",
        "hash_algorithm",
        "futures_only",
        "environment",
        "non_authorizing",
        "replay_policy",
    }
)

_REPLAY_POLICY_KEYS = frozenset(
    {
        "offline_only",
        "network_allowed",
        "credentials_allowed",
        "runtime_allowed",
        "scheduler_allowed",
        "orders_allowed",
        "execution_authorized",
        "live_authorized",
        "followup_run_gate",
    }
)

_DEFAULT_REPLAY_POLICY: dict[str, Any] = {
    "offline_only": True,
    "network_allowed": False,
    "credentials_allowed": False,
    "runtime_allowed": False,
    "scheduler_allowed": False,
    "orders_allowed": False,
    "execution_authorized": False,
    "live_authorized": False,
    "followup_run_gate": FOLLOWUP_RUN_GATE,
}


def _reject_unknown_keys(data: dict[str, Any], allowed: frozenset[str], prefix: str) -> list[str]:
    unknown = sorted(set(data) - allowed)
    if unknown:
        return [f"{prefix}: unknown field(s) {unknown!r}"]
    return []


def serialize_replay_manifest_canonical(manifest: dict[str, Any]) -> str:
    """Deterministic JSON serialization of replay manifest (sorted keys)."""
    return json.dumps(manifest, sort_keys=True, separators=(",", ":"))


def compute_replay_manifest_digest(manifest: dict[str, Any]) -> str:
    """SHA-256 digest over canonical replay manifest serialization."""
    return hashlib.sha256(serialize_replay_manifest_canonical(manifest).encode("utf-8")).hexdigest()


def default_replay_policy() -> dict[str, Any]:
    """Safe blocked replay policy defaults."""
    return dict(_DEFAULT_REPLAY_POLICY)


def build_replay_manifest(
    *,
    source_revision: str,
    canonical_input_capture_digest: str,
    packet_digest: str,
    artifact_ids: tuple[str, ...] = DEFAULT_ARTIFACT_IDS,
    replay_policy: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Build deterministic replay manifest binding capture and packet digests."""
    policy = replay_policy if replay_policy is not None else default_replay_policy()
    return {
        "manifest_version": MANIFEST_VERSION,
        "packet_contract_version": CONTRACT_VERSION,
        "builder_version": BUILDER_VERSION,
        "replay_contract_version": REPLAY_CONTRACT_VERSION,
        "source_revision": source_revision,
        "canonical_input_capture_digest": canonical_input_capture_digest,
        "packet_digest": packet_digest,
        "artifact_ids": list(artifact_ids),
        "hash_algorithm": HASH_ALGORITHM,
        "futures_only": True,
        "environment": ENVIRONMENT_TESTNET,
        "non_authorizing": True,
        "replay_policy": policy,
    }


def validate_replay_manifest(manifest: dict[str, Any] | None) -> list[str]:
    """Fail-closed manifest schema validation."""
    if manifest is None:
        return ["manifest required"]
    if not isinstance(manifest, dict):
        return ["manifest must be a mapping"]

    fail_reasons = _reject_unknown_keys(manifest, _MANIFEST_TOP_LEVEL_KEYS, "manifest")

    for field_name in (
        "manifest_version",
        "packet_contract_version",
        "builder_version",
        "replay_contract_version",
        "source_revision",
        "canonical_input_capture_digest",
        "packet_digest",
        "artifact_ids",
        "hash_algorithm",
        "futures_only",
        "environment",
        "non_authorizing",
        "replay_policy",
    ):
        if field_name not in manifest:
            fail_reasons.append(f"manifest missing required field {field_name!r}")

    if fail_reasons:
        return fail_reasons

    if manifest["manifest_version"] != MANIFEST_VERSION:
        fail_reasons.append(f"manifest_version must be {MANIFEST_VERSION!r}")
    if manifest["packet_contract_version"] != CONTRACT_VERSION:
        fail_reasons.append(f"packet_contract_version must be {CONTRACT_VERSION!r}")
    if manifest["builder_version"] != BUILDER_VERSION:
        fail_reasons.append(f"builder_version must be {BUILDER_VERSION!r}")
    if manifest["replay_contract_version"] != REPLAY_CONTRACT_VERSION:
        fail_reasons.append(f"replay_contract_version must be {REPLAY_CONTRACT_VERSION!r}")
    if not manifest["source_revision"]:
        fail_reasons.append("source_revision required")
    if not manifest["canonical_input_capture_digest"]:
        fail_reasons.append("canonical_input_capture_digest required")
    if not manifest["packet_digest"]:
        fail_reasons.append("packet_digest required")
    if manifest["hash_algorithm"] != HASH_ALGORITHM:
        fail_reasons.append(f"hash_algorithm must be {HASH_ALGORITHM!r}")
    if manifest["futures_only"] is not True:
        fail_reasons.append("futures_only must be true")
    if manifest["environment"] != ENVIRONMENT_TESTNET:
        fail_reasons.append(f"environment must be {ENVIRONMENT_TESTNET!r}")
    if manifest["non_authorizing"] is not True:
        fail_reasons.append("non_authorizing must be true")

    artifact_ids = manifest["artifact_ids"]
    if not isinstance(artifact_ids, list) or not artifact_ids:
        fail_reasons.append("artifact_ids must be a non-empty list")
    elif sorted(artifact_ids) != sorted(DEFAULT_ARTIFACT_IDS):
        fail_reasons.append(f"artifact_ids must bind {list(DEFAULT_ARTIFACT_IDS)!r}")

    replay_policy = manifest["replay_policy"]
    if not isinstance(replay_policy, dict):
        fail_reasons.append("replay_policy must be a mapping")
    else:
        fail_reasons.extend(
            _reject_unknown_keys(replay_policy, _REPLAY_POLICY_KEYS, "replay_policy")
        )
        if replay_policy.get("offline_only") is not True:
            fail_reasons.append("replay_policy.offline_only must be true")
        for flag_name in (
            "network_allowed",
            "credentials_allowed",
            "runtime_allowed",
            "scheduler_allowed",
            "orders_allowed",
            "execution_authorized",
            "live_authorized",
        ):
            if replay_policy.get(flag_name) is True:
                fail_reasons.append(f"replay_policy.{flag_name} must be false")
        if replay_policy.get("followup_run_gate") != FOLLOWUP_RUN_GATE:
            fail_reasons.append(f"replay_policy.followup_run_gate must be {FOLLOWUP_RUN_GATE!r}")

    return fail_reasons


def _resolve_builder_input(
    canonical_input_capture: dict[str, Any] | PreflightPacketBuilderInput,
) -> tuple[PreflightPacketBuilderInput | None, list[str]]:
    if isinstance(canonical_input_capture, PreflightPacketBuilderInput):
        return canonical_input_capture, []
    if not isinstance(canonical_input_capture, dict):
        return None, ["canonical_input_capture must be a mapping or PreflightPacketBuilderInput"]
    parsed, errors = parse_builder_input_from_mapping(canonical_input_capture)
    return parsed, errors


def replay_preflight_packet_offline(
    *,
    canonical_input_capture: dict[str, Any] | PreflightPacketBuilderInput,
    expected_packet_digest: str,
    manifest: dict[str, Any] | None,
    artifacts: dict[str, str] | None = None,
    packet_payload: BoundedFuturesTestnetPreflightPacket | None = None,
) -> dict[str, Any]:
    """Offline replay verification; never grants execution or live authority."""
    validation_errors: list[str] = []

    manifest_errors = validate_replay_manifest(manifest)
    manifest_valid = not manifest_errors
    validation_errors.extend(manifest_errors)

    if manifest is None:
        return _replay_result(
            replay_status="rejected",
            manifest_valid=False,
            validation_errors=validation_errors,
        )

    builder_input, parse_errors = _resolve_builder_input(canonical_input_capture)
    validation_errors.extend(parse_errors)
    if builder_input is None:
        return _replay_result(
            replay_status="rejected",
            manifest_valid=manifest_valid,
            validation_errors=validation_errors,
        )

    builder_input_errors = validate_builder_inputs(builder_input)
    validation_errors.extend(builder_input_errors)

    computed_capture_digest = compute_input_capture_digest(builder_input)
    input_capture_digest_matches = (
        computed_capture_digest == manifest["canonical_input_capture_digest"]
    )
    if not input_capture_digest_matches:
        validation_errors.append("canonical_input_capture_digest mismatch")

    build_result = build_preflight_packet(builder_input)
    if not build_result["build_pass"]:
        validation_errors.extend(build_result["fail_reasons"])
    rebuilt_packet = build_result.get("packet")
    computed_packet_digest: str | None = None
    if rebuilt_packet is not None:
        computed_packet_digest = compute_packet_digest(rebuilt_packet)
        packet_validation = validate_preflight_packet(rebuilt_packet)
        if not packet_validation["validation_pass"]:
            validation_errors.extend(packet_validation["fail_reasons"])

    packet_digest_matches = False
    if computed_packet_digest is not None:
        packet_digest_matches = (
            computed_packet_digest == expected_packet_digest
            and computed_packet_digest == manifest["packet_digest"]
        )
        if computed_packet_digest != expected_packet_digest:
            validation_errors.append("expected_packet_digest mismatch")
        if computed_packet_digest != manifest["packet_digest"]:
            validation_errors.append("manifest packet_digest mismatch")

    source_revision_matches = (
        builder_input.source_build.source_revision == manifest["source_revision"]
    )
    if not source_revision_matches:
        validation_errors.append("source_revision mismatch")

    contract_versions_match = (
        manifest["packet_contract_version"] == CONTRACT_VERSION
        and manifest["builder_version"] == BUILDER_VERSION
        and manifest["replay_contract_version"] == REPLAY_CONTRACT_VERSION
    )
    if not contract_versions_match:
        validation_errors.append("contract version binding mismatch")

    algorithm_matches = manifest["hash_algorithm"] == HASH_ALGORITHM
    if not algorithm_matches:
        validation_errors.append("hash_algorithm mismatch")

    artifacts_complete = True
    if artifacts is None:
        artifacts_complete = False
        validation_errors.append("artifacts required")
    else:
        for artifact_id in manifest.get("artifact_ids", []):
            if artifact_id not in artifacts:
                artifacts_complete = False
                validation_errors.append(f"missing artifact binding: {artifact_id!r}")
        if artifacts_complete and rebuilt_packet is not None:
            expected_capture = serialize_input_capture_canonical(builder_input)
            expected_packet = serialize_packet_canonical(rebuilt_packet)
            if artifacts.get(ARTIFACT_CANONICAL_INPUT_CAPTURE) != expected_capture:
                artifacts_complete = False
                validation_errors.append(f"{ARTIFACT_CANONICAL_INPUT_CAPTURE} artifact mismatch")
            if artifacts.get(ARTIFACT_PACKET_PAYLOAD) != expected_packet:
                artifacts_complete = False
                validation_errors.append(f"{ARTIFACT_PACKET_PAYLOAD} artifact mismatch")

    if packet_payload is not None and rebuilt_packet is not None:
        if serialize_packet_canonical(packet_payload) != serialize_packet_canonical(rebuilt_packet):
            validation_errors.append("provided packet_payload does not match rebuilt packet")

    verified = (
        manifest_valid
        and input_capture_digest_matches
        and packet_digest_matches
        and source_revision_matches
        and contract_versions_match
        and algorithm_matches
        and artifacts_complete
        and not validation_errors
    )

    return _replay_result(
        replay_status="verified" if verified else "rejected",
        manifest_valid=manifest_valid,
        input_capture_digest_matches=input_capture_digest_matches,
        packet_digest_matches=packet_digest_matches,
        source_revision_matches=source_revision_matches,
        contract_versions_match=contract_versions_match,
        algorithm_matches=algorithm_matches,
        artifacts_complete=artifacts_complete,
        validation_errors=validation_errors,
        computed_capture_digest=computed_capture_digest,
        computed_packet_digest=computed_packet_digest,
        rebuilt_packet=rebuilt_packet,
    )


def _replay_result(
    *,
    replay_status: str,
    manifest_valid: bool,
    validation_errors: list[str],
    input_capture_digest_matches: bool = False,
    packet_digest_matches: bool = False,
    source_revision_matches: bool = False,
    contract_versions_match: bool = False,
    algorithm_matches: bool = False,
    artifacts_complete: bool = False,
    computed_capture_digest: str | None = None,
    computed_packet_digest: str | None = None,
    rebuilt_packet: BoundedFuturesTestnetPreflightPacket | None = None,
) -> dict[str, Any]:
    return {
        "replay_status": replay_status,
        "manifest_valid": manifest_valid,
        "input_capture_digest_matches": input_capture_digest_matches,
        "packet_digest_matches": packet_digest_matches,
        "source_revision_matches": source_revision_matches,
        "contract_versions_match": contract_versions_match,
        "algorithm_matches": algorithm_matches,
        "artifacts_complete": artifacts_complete,
        "validation_errors": validation_errors,
        "non_authorizing": True,
        "execution_authorized": False,
        "live_authorized": False,
        "computed_capture_digest": computed_capture_digest,
        "computed_packet_digest": computed_packet_digest,
        "rebuilt_packet": rebuilt_packet,
    }


def builder_input_to_capture_mapping(inputs: PreflightPacketBuilderInput) -> dict[str, Any]:
    """Expose PE-14 input capture as mapping for artifact binding tests."""
    return asdict(inputs)
