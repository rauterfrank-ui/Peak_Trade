"""Bounded Futures Testnet preflight packet durable archive wiring (v0, PE-16).

Deterministic, offline archive plan and local persistence for verified PE-13/PE-14/PE-15
preflight packet evidence. Reuses primary evidence manifest helpers and upstream packet
contracts. Does not authorize network, credentials, orders, runtime, scheduler, or live
execution.
"""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from scripts.ops.primary_evidence_retention_v0 import (
    MANIFEST_FILENAME,
    is_under_tmp,
    require_durable_archive_root,
    verify_manifest_sha256,
    write_manifest_sha256,
)
from src.ops.bounded_futures_testnet_preflight_packet_builder_contract_v0 import (
    BUILDER_VERSION,
    PreflightPacketBuilderInput,
    compute_input_capture_digest,
    serialize_input_capture_canonical,
)
from src.ops.bounded_futures_testnet_preflight_packet_contract_v0 import (
    CONTRACT_VERSION,
    ENVIRONMENT_TESTNET,
    FOLLOWUP_RUN_GATE,
    BoundedFuturesTestnetPreflightPacket,
    compute_packet_digest,
    serialize_packet_canonical,
)
from src.ops.bounded_futures_testnet_preflight_packet_replay_contract_v0 import (
    HASH_ALGORITHM,
    REPLAY_CONTRACT_VERSION,
    compute_replay_manifest_digest,
    replay_preflight_packet_offline,
    serialize_replay_manifest_canonical,
)

PACKAGE_MARKER = "BOUNDED_FUTURES_TESTNET_PREFLIGHT_PACKET_ARCHIVE_CONTRACT_V0=true"
ARCHIVE_CONTRACT_VERSION = "bounded_futures_testnet_preflight_packet_archive.v0"
ARCHIVE_RELATIVE_PREFIX = "bounded_futures_testnet_preflight_packet"

ARTIFACT_CANONICAL_INPUT_CAPTURE = "canonical_input_capture.json"
ARTIFACT_PREFLIGHT_PACKET = "preflight_packet.json"
ARTIFACT_REPLAY_MANIFEST = "replay_manifest.json"
ARTIFACT_REPLAY_RESULT = "replay_result.json"
ARTIFACT_MACHINE_SUMMARY = "MACHINE_SUMMARY.env"
ARTIFACT_RECOMMENDED_NEXT_STEP = "RECOMMENDED_NEXT_STEP.md"

REQUIRED_ARTIFACT_FILENAMES: tuple[str, ...] = (
    ARTIFACT_CANONICAL_INPUT_CAPTURE,
    ARTIFACT_PREFLIGHT_PACKET,
    ARTIFACT_REPLAY_MANIFEST,
    ARTIFACT_REPLAY_RESULT,
    ARTIFACT_MACHINE_SUMMARY,
    ARTIFACT_RECOMMENDED_NEXT_STEP,
    MANIFEST_FILENAME,
)

_ARCHIVE_INPUT_KEYS = frozenset(
    {
        "archive_root",
        "builder_input",
        "packet",
        "replay_manifest",
        "replay_artifacts",
        "expected_packet_digest",
        "machine_summary_env",
        "recommended_next_step_md",
        "archive_contract_version",
        "hash_algorithm",
        "futures_only",
        "environment",
    }
)


@dataclass(frozen=True)
class PreflightPacketArchiveInput:
    archive_root: Path
    builder_input: PreflightPacketBuilderInput
    packet: BoundedFuturesTestnetPreflightPacket
    replay_manifest: dict[str, Any]
    replay_artifacts: dict[str, str]
    expected_packet_digest: str
    machine_summary_env: str
    recommended_next_step_md: str
    archive_contract_version: str = ARCHIVE_CONTRACT_VERSION
    hash_algorithm: str = HASH_ALGORITHM
    futures_only: bool = True
    environment: str = ENVIRONMENT_TESTNET


def _reject_unknown_keys(data: dict[str, Any], allowed: frozenset[str], prefix: str) -> list[str]:
    unknown = sorted(set(data) - allowed)
    if unknown:
        return [f"{prefix}: unknown field(s) {unknown!r}"]
    return []


def _atomic_write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temp_path = tempfile.mkstemp(
        dir=path.parent,
        prefix=f".tmp_{path.name}_",
    )
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temp_path, path)
    except Exception:
        if os.path.exists(temp_path):
            os.unlink(temp_path)
        raise


def _resolve_under_root(root: Path, relative_path: str) -> tuple[Path | None, list[str]]:
    errors: list[str] = []
    if not relative_path:
        errors.append("archive_relative_path required")
        return None, errors
    if relative_path.startswith("/"):
        errors.append("archive_relative_path must be relative")
        return None, errors
    if ".." in Path(relative_path).parts:
        errors.append("archive_relative_path must not contain '..'")
        return None, errors
    try:
        root_resolved = root.resolve()
        candidate = (root / relative_path).resolve()
        if candidate != root_resolved and root_resolved not in candidate.parents:
            errors.append("archive destination escapes archive_root")
            return None, errors
        return candidate, errors
    except OSError as exc:
        errors.append(f"archive path resolution failed: {exc}")
        return None, errors


def validate_archive_destination(archive_root: Path) -> list[str]:
    """Fail closed when archive root is missing or under /tmp."""
    errors: list[str] = []
    if is_under_tmp(archive_root):
        errors.append("archive_root must be outside /tmp")
    ok, msg = require_durable_archive_root(archive_root)
    if not ok:
        errors.append(msg)
    return errors


def compute_archive_identity(
    *,
    source_revision: str,
    packet_digest: str,
    input_capture_digest: str,
    manifest_digest: str,
    archive_contract_version: str = ARCHIVE_CONTRACT_VERSION,
    packet_contract_version: str = CONTRACT_VERSION,
    builder_version: str = BUILDER_VERSION,
    replay_contract_version: str = REPLAY_CONTRACT_VERSION,
    futures_only: bool = True,
    environment: str = ENVIRONMENT_TESTNET,
) -> str:
    """Deterministic archive identity from stable non-secret inputs."""
    identity_payload = {
        "archive_contract_version": archive_contract_version,
        "packet_contract_version": packet_contract_version,
        "builder_version": builder_version,
        "replay_contract_version": replay_contract_version,
        "source_revision": source_revision,
        "packet_digest": packet_digest,
        "input_capture_digest": input_capture_digest,
        "manifest_digest": manifest_digest,
        "futures_only": futures_only,
        "environment": environment,
    }
    canonical = json.dumps(identity_payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def compute_archive_relative_path(archive_identity: str) -> str:
    """Deterministic relative archive path under the injected archive root."""
    return f"{ARCHIVE_RELATIVE_PREFIX}/{archive_identity}"


def serialize_replay_result_canonical(replay_result: dict[str, Any]) -> str:
    """Serialize replay result without non-JSON packet objects."""
    payload = {key: value for key, value in replay_result.items() if key != "rebuilt_packet"}
    if replay_result.get("rebuilt_packet") is not None:
        packet = replay_result["rebuilt_packet"]
        payload["rebuilt_packet_digest"] = compute_packet_digest(packet)
    return json.dumps(payload, sort_keys=True, separators=(",", ":"))


def validate_manifest_entries(entries: tuple[str, ...]) -> list[str]:
    """Reject duplicate, absolute, or traversal manifest artifact paths."""
    errors: list[str] = []
    if len(entries) != len(set(entries)):
        errors.append("duplicate artifact filenames in manifest plan")
    for entry in entries:
        if entry.startswith("/"):
            errors.append(f"absolute manifest path rejected: {entry!r}")
        if ".." in Path(entry).parts:
            errors.append(f"path traversal rejected in manifest entry: {entry!r}")
    missing = sorted(set(REQUIRED_ARTIFACT_FILENAMES) - {MANIFEST_FILENAME} - set(entries))
    if missing:
        errors.append(f"missing required artifacts in manifest plan: {missing}")
    return errors


def _validate_archive_input(archive_input: PreflightPacketArchiveInput) -> list[str]:
    errors: list[str] = []
    errors.extend(validate_archive_destination(archive_input.archive_root))
    if archive_input.archive_contract_version != ARCHIVE_CONTRACT_VERSION:
        errors.append(f"archive_contract_version must be {ARCHIVE_CONTRACT_VERSION!r}")
    if archive_input.hash_algorithm != HASH_ALGORITHM:
        errors.append(f"hash_algorithm must be {HASH_ALGORITHM!r}")
    if archive_input.futures_only is not True:
        errors.append("futures_only must be true")
    if archive_input.environment != ENVIRONMENT_TESTNET:
        errors.append(f"environment must be {ENVIRONMENT_TESTNET!r}")
    if not archive_input.machine_summary_env.strip():
        errors.append("machine_summary_env required")
    if not archive_input.recommended_next_step_md.strip():
        errors.append("recommended_next_step_md required")
    if not archive_input.expected_packet_digest:
        errors.append("expected_packet_digest required")

    computed_packet_digest = compute_packet_digest(archive_input.packet)
    computed_capture_digest = compute_input_capture_digest(archive_input.builder_input)
    if computed_packet_digest != archive_input.expected_packet_digest:
        errors.append("packet_digest mismatch")
    manifest_digest = compute_replay_manifest_digest(archive_input.replay_manifest)
    if archive_input.replay_manifest.get("packet_digest") != computed_packet_digest:
        errors.append("replay_manifest packet_digest mismatch")
    if (
        archive_input.replay_manifest.get("canonical_input_capture_digest")
        != computed_capture_digest
    ):
        errors.append("replay_manifest input_capture_digest mismatch")
    if archive_input.replay_manifest.get("source_revision") != (
        archive_input.builder_input.source_build.source_revision
    ):
        errors.append("source_revision mismatch")

    replay_result = replay_preflight_packet_offline(
        canonical_input_capture=archive_input.builder_input,
        expected_packet_digest=archive_input.expected_packet_digest,
        manifest=archive_input.replay_manifest,
        artifacts=archive_input.replay_artifacts,
        packet_payload=archive_input.packet,
    )
    if replay_result["replay_status"] != "verified":
        errors.append("replay not verified")
    if (
        replay_result.get("execution_authorized") is True
        or replay_result.get("live_authorized") is True
    ):
        errors.append("replay result must remain non-authorizing")

    return errors


def build_archive_plan(archive_input: PreflightPacketArchiveInput) -> dict[str, Any]:
    """Build deterministic archive plan without filesystem mutation."""
    validation_errors = _validate_archive_input(archive_input)
    packet_digest = compute_packet_digest(archive_input.packet)
    input_capture_digest = compute_input_capture_digest(archive_input.builder_input)
    manifest_digest = compute_replay_manifest_digest(archive_input.replay_manifest)
    source_revision = archive_input.builder_input.source_build.source_revision
    archive_identity = compute_archive_identity(
        source_revision=source_revision,
        packet_digest=packet_digest,
        input_capture_digest=input_capture_digest,
        manifest_digest=manifest_digest,
        archive_contract_version=archive_input.archive_contract_version,
        futures_only=archive_input.futures_only,
        environment=archive_input.environment,
    )
    archive_relative_path = compute_archive_relative_path(archive_identity)
    manifest_entries = tuple(sorted(set(REQUIRED_ARTIFACT_FILENAMES) - {MANIFEST_FILENAME}))
    manifest_entry_errors = validate_manifest_entries(manifest_entries)
    validation_errors.extend(manifest_entry_errors)
    destination, path_errors = _resolve_under_root(
        archive_input.archive_root,
        archive_relative_path,
    )
    validation_errors.extend(path_errors)

    replay_result = replay_preflight_packet_offline(
        canonical_input_capture=archive_input.builder_input,
        expected_packet_digest=archive_input.expected_packet_digest,
        manifest=archive_input.replay_manifest,
        artifacts=archive_input.replay_artifacts,
        packet_payload=archive_input.packet,
    )
    artifact_contents = {
        ARTIFACT_CANONICAL_INPUT_CAPTURE: serialize_input_capture_canonical(
            archive_input.builder_input
        ),
        ARTIFACT_PREFLIGHT_PACKET: serialize_packet_canonical(archive_input.packet),
        ARTIFACT_REPLAY_MANIFEST: serialize_replay_manifest_canonical(
            archive_input.replay_manifest
        ),
        ARTIFACT_REPLAY_RESULT: serialize_replay_result_canonical(replay_result),
        ARTIFACT_MACHINE_SUMMARY: archive_input.machine_summary_env.rstrip() + "\n",
        ARTIFACT_RECOMMENDED_NEXT_STEP: archive_input.recommended_next_step_md.rstrip() + "\n",
    }

    return {
        "archive_status": "planned" if not validation_errors else "rejected",
        "archive_identity": archive_identity,
        "archive_relative_path": archive_relative_path,
        "archive_destination": str(destination) if destination is not None else "",
        "required_artifacts": list(REQUIRED_ARTIFACT_FILENAMES),
        "manifest_entries": list(manifest_entries),
        "artifact_contents": artifact_contents,
        "packet_digest": packet_digest,
        "input_capture_digest": input_capture_digest,
        "manifest_digest": manifest_digest,
        "replay_verified": replay_result["replay_status"] == "verified",
        "validation_errors": validation_errors,
        "durable_destination_valid": not validation_errors and destination is not None,
        "non_authorizing": True,
        "execution_authorized": False,
        "live_authorized": False,
    }


def _directory_contents_match(root: Path, artifact_contents: dict[str, str]) -> bool:
    if not root.is_dir():
        return False
    for name, expected in artifact_contents.items():
        if name == MANIFEST_FILENAME:
            continue
        path = root / name
        if not path.is_file():
            return False
        if path.read_text(encoding="utf-8") != expected:
            return False
    return True


def _cleanup_directory(path: Path) -> None:
    if path.exists():
        shutil.rmtree(path)


def persist_preflight_packet_archive(
    archive_input: PreflightPacketArchiveInput,
) -> dict[str, Any]:
    """Persist verified preflight packet evidence under the injected archive root."""
    plan = build_archive_plan(archive_input)
    validation_errors = list(plan["validation_errors"])
    archive_root = archive_input.archive_root
    archive_identity = plan["archive_identity"]
    archive_relative_path = plan["archive_relative_path"]
    artifact_contents: dict[str, str] = plan["artifact_contents"]

    destination, path_errors = _resolve_under_root(archive_root, archive_relative_path)
    validation_errors.extend(path_errors)
    if validation_errors or destination is None:
        return _archive_result(
            archive_status="rejected",
            archive_identity=archive_identity,
            archive_relative_path=archive_relative_path,
            validation_errors=validation_errors,
            durable_destination_valid=False,
        )

    collision_detected = False
    if destination.exists():
        if _directory_contents_match(destination, artifact_contents):
            verify_ok, _ = verify_manifest_sha256(destination)
            manifest_verify_rc = 0 if verify_ok else 1
            if manifest_verify_rc != 0:
                validation_errors.append("existing archive manifest verification failed")
                return _archive_result(
                    archive_status="rejected",
                    archive_identity=archive_identity,
                    archive_relative_path=archive_relative_path,
                    validation_errors=validation_errors,
                    collision_detected=True,
                    durable_destination_valid=False,
                )
            return _archive_result(
                archive_status="persisted_verified",
                archive_identity=archive_identity,
                archive_relative_path=archive_relative_path,
                validation_errors=[],
                required_artifacts_present=True,
                manifest_written=True,
                manifest_verify_rc=0,
                packet_digest_matches=True,
                input_capture_digest_matches=True,
                replay_verified=True,
                durable_destination_valid=True,
                collision_detected=False,
            )
        collision_detected = True
        validation_errors.append("archive identity collision with differing content")
        return _archive_result(
            archive_status="rejected",
            archive_identity=archive_identity,
            archive_relative_path=archive_relative_path,
            validation_errors=validation_errors,
            collision_detected=collision_detected,
            durable_destination_valid=False,
        )

    staging = destination.parent / f".staging_{archive_identity}"
    if staging.exists():
        _cleanup_directory(staging)
    staging.mkdir(parents=True, exist_ok=True)

    try:
        for name, content in artifact_contents.items():
            if name == MANIFEST_FILENAME:
                continue
            _atomic_write_text(staging / name, content)
        write_manifest_sha256(staging)
        verify_ok, verify_msg = verify_manifest_sha256(staging)
        manifest_verify_rc = 0 if verify_ok else 1
        if manifest_verify_rc != 0:
            validation_errors.append(f"manifest verification failed: {verify_msg}")
            _cleanup_directory(staging)
            return _archive_result(
                archive_status="rejected",
                archive_identity=archive_identity,
                archive_relative_path=archive_relative_path,
                validation_errors=validation_errors,
                manifest_written=True,
                manifest_verify_rc=manifest_verify_rc,
                durable_destination_valid=False,
            )
        destination.parent.mkdir(parents=True, exist_ok=True)
        staging.rename(destination)
    except OSError as exc:
        _cleanup_directory(staging)
        validation_errors.append(f"persist failed: {exc}")
        return _archive_result(
            archive_status="rejected",
            archive_identity=archive_identity,
            archive_relative_path=archive_relative_path,
            validation_errors=validation_errors,
            durable_destination_valid=False,
        )

    final_verify_ok, final_verify_msg = verify_manifest_sha256(destination)
    manifest_verify_rc = 0 if final_verify_ok else 1
    if manifest_verify_rc != 0:
        validation_errors.append(f"post-write manifest verification failed: {final_verify_msg}")
        return _archive_result(
            archive_status="rejected",
            archive_identity=archive_identity,
            archive_relative_path=archive_relative_path,
            validation_errors=validation_errors,
            manifest_written=True,
            manifest_verify_rc=manifest_verify_rc,
            durable_destination_valid=False,
        )

    return _archive_result(
        archive_status="persisted_verified",
        archive_identity=archive_identity,
        archive_relative_path=archive_relative_path,
        validation_errors=[],
        required_artifacts_present=True,
        manifest_written=True,
        manifest_verify_rc=0,
        packet_digest_matches=True,
        input_capture_digest_matches=True,
        replay_verified=True,
        durable_destination_valid=True,
        collision_detected=False,
    )


def validate_archive_input_mapping(data: dict[str, Any]) -> list[str]:
    """Validate explicit mapping input for unknown top-level keys."""
    return _reject_unknown_keys(data, _ARCHIVE_INPUT_KEYS, "archive_input")


def _archive_result(
    *,
    archive_status: str,
    archive_identity: str,
    archive_relative_path: str,
    validation_errors: list[str],
    required_artifacts_present: bool = False,
    manifest_written: bool = False,
    manifest_verify_rc: int | None = None,
    packet_digest_matches: bool = False,
    input_capture_digest_matches: bool = False,
    replay_verified: bool = False,
    durable_destination_valid: bool = False,
    collision_detected: bool = False,
) -> dict[str, Any]:
    return {
        "archive_status": archive_status,
        "archive_identity": archive_identity,
        "archive_relative_path": archive_relative_path,
        "required_artifacts_present": required_artifacts_present,
        "manifest_written": manifest_written,
        "manifest_verify_rc": manifest_verify_rc,
        "packet_digest_matches": packet_digest_matches,
        "input_capture_digest_matches": input_capture_digest_matches,
        "replay_verified": replay_verified,
        "durable_destination_valid": durable_destination_valid,
        "collision_detected": collision_detected,
        "validation_errors": validation_errors,
        "non_authorizing": True,
        "execution_authorized": False,
        "live_authorized": False,
        "followup_run_gate": FOLLOWUP_RUN_GATE,
    }
