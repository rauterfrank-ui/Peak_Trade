"""Durable custody and recovery of an already-governed IsolatedLaneTopologyV1.

Owns only checkpoint write, integrity validation, and exact recovery.
Does not map lanes, select, rank, bind, trade, or join a productive host.
"""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import tempfile
import uuid
from pathlib import Path
from typing import Any, Mapping, NoReturn, Optional

from src.ops.current_mf_n5_durable_lane_assignment_persistence_v1.constants_v1 import (
    CAP23_CHANGE_REQUIRED,
    CAP24_CHANGE_REQUIRED,
    CHECKPOINT_DIRNAME,
    CHECKPOINT_FILENAME,
    COMMIT_MARKER_FILENAME,
    CONTRACT_ID,
    CROSS_UNIVERSE_CANDIDATE_BORROWING,
    CROSS_UNIVERSE_FALLBACK,
    CROSS_UNIVERSE_PIN,
    CROSS_UNIVERSE_REPLACEMENT,
    CROSS_UNIVERSE_RERANKING,
    CROSS_UNIVERSE_SELECTION,
    DOUBLE_PLAY_CHANGE_REQUIRED,
    FIVE_LANE_CONTINUOUS_HOST_JOIN,
    FIVE_LANE_RUNTIME_CREATED,
    INSTRUMENT_ID_ALONE_SUFFICIENT,
    LANE_MAPPING_OWNER,
    MANIFEST_FILENAME,
    MASTER_V2_CHANGE_REQUIRED,
    MAX_POSITIONS_EFFECTIVE,
    MF_PRODUCTIVE_JOIN,
    MULTI_UNIVERSE_MERGE,
    OWNER,
    PERSISTENCE_CAP23_SELECTION_AUTHORITY,
    PERSISTENCE_CAP24_BINDING_AUTHORITY,
    PERSISTENCE_EXECUTION_AUTHORITY,
    PERSISTENCE_LANE_MAPPING_AUTHORITY,
    PERSISTENCE_MEMBERSHIP_AUTHORITY,
    PERSISTENCE_RANKING_AUTHORITY,
    PERSISTENCE_TRADING_AUTHORITY,
    RECOVERY_MODE_BOOTSTRAP,
    RECOVERY_MODE_RESTART,
    RECOVERY_MODES,
    SCHEMA_VERSION,
    STAGING_DIRNAME_PREFIX,
    TOPOLOGY_CONTRACT_ID,
    TOPOLOGY_SCHEMA_VERSION,
    UNIVERSE_ISOLATION_ENFORCED,
)
from src.ops.current_mf_n5_durable_lane_assignment_persistence_v1.single_writer_v1 import (
    DuplicateLaneAssignmentWriterError,
    DurableLaneAssignmentSingleWriterV1,
)
from src.ops.current_mf_n5_isolated_lane_instance_topology_v1.topology_v1 import (
    IsolatedLaneTopologyError,
    IsolatedLaneTopologyV1,
    isolated_lane_topology_from_dict,
)
from src.ops.single_selected_future_policy_v1.governed_pin_v1 import lane_state_root_key

FAILURE_MISSING_RESTART = "LANE_ASSIGNMENT_MISSING_RESTART_CHECKPOINT"
FAILURE_CORRUPT = "LANE_ASSIGNMENT_CORRUPT_CHECKPOINT"
FAILURE_UNSUPPORTED_SCHEMA = "LANE_ASSIGNMENT_UNSUPPORTED_SCHEMA"
FAILURE_INTEGRITY = "LANE_ASSIGNMENT_INTEGRITY_MISMATCH"
FAILURE_MALFORMED = "LANE_ASSIGNMENT_MALFORMED_PAYLOAD"
FAILURE_BOOTSTRAP_WITH_PRIOR = "LANE_ASSIGNMENT_BOOTSTRAP_WITH_PRIOR_COMMIT"
FAILURE_CROSS_UNIVERSE = "LANE_ASSIGNMENT_CROSS_UNIVERSE_FORBIDDEN"
FAILURE_PROVENANCE = "LANE_ASSIGNMENT_PROVENANCE_MISMATCH"
FAILURE_STATE_ROOT = "LANE_ASSIGNMENT_STATE_ROOT_MISMATCH"
FAILURE_PARTIAL_WRITE = "LANE_ASSIGNMENT_PARTIAL_WRITE"
FAILURE_INVALID_RECOVERY_MODE = "LANE_ASSIGNMENT_INVALID_RECOVERY_MODE"
FAILURE_AUTHORITY = "LANE_ASSIGNMENT_AUTHORITY_CLAIM_FORBIDDEN"


class DurableLaneAssignmentPersistenceError(ValueError):
    def __init__(self, code: str, detail: str = "") -> None:
        super().__init__(f"{code}:{detail}" if detail else code)
        self.failure_code = code
        self.detail = detail


def _fail(code: str, detail: str = "") -> NoReturn:
    raise DurableLaneAssignmentPersistenceError(code, detail)


def canonical_json_dumps(payload: Mapping[str, Any] | list[Any] | Any) -> str:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def sha256_hex(payload: str | bytes) -> str:
    if isinstance(payload, str):
        payload = payload.encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _atomic_write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_name = tempfile.mkstemp(prefix=path.name + ".", dir=str(path.parent))
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            fh.write(text)
            fh.flush()
            os.fsync(fh.fileno())
        os.replace(tmp_name, path)
    finally:
        if os.path.exists(tmp_name):
            os.unlink(tmp_name)


def checkpoint_root_for(topology_state_root_base: Path | str) -> Path:
    return Path(lane_state_root_key(topology_state_root_base)) / CHECKPOINT_DIRNAME


def topology_integrity_digest_v1(topology_payload: Mapping[str, Any]) -> str:
    return sha256_hex(canonical_json_dumps(dict(topology_payload)))


def write_manifest(root: Path, relative_files: tuple[str, ...]) -> str:
    lines: list[str] = []
    for rel in sorted(relative_files):
        digest = sha256_hex((root / rel).read_bytes())
        lines.append(f"{digest}  {rel}")
    body = "\n".join(lines) + "\n"
    _atomic_write_text(root / MANIFEST_FILENAME, body)
    return sha256_hex(body)


def verify_manifest(root: Path) -> dict[str, Any]:
    manifest = Path(root) / MANIFEST_FILENAME
    if not manifest.is_file():
        _fail(FAILURE_CORRUPT, "MANIFEST_MISSING")
    errors: list[str] = []
    for line in manifest.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            digest, rel = line.split(None, 1)
        except ValueError:
            errors.append("MANIFEST_LINE_MALFORMED")
            continue
        path = Path(root) / rel
        if not path.is_file():
            errors.append(f"MISSING:{rel}")
            continue
        actual = sha256_hex(path.read_bytes())
        if actual != digest:
            errors.append(f"DIGEST_MISMATCH:{rel}")
    if errors:
        _fail(FAILURE_INTEGRITY, ";".join(errors))
    return {"ok": True, "manifest_path": str(manifest)}


def checkpoint_path(root: Path) -> Path:
    return Path(root) / CHECKPOINT_FILENAME


def commit_marker_path(root: Path) -> Path:
    return Path(root) / COMMIT_MARKER_FILENAME


def prior_durable_lane_assignment_commit_exists(topology_state_root_base: Path | str) -> bool:
    root = checkpoint_root_for(topology_state_root_base)
    return commit_marker_path(root).is_file() or checkpoint_path(root).is_file()


def _assert_custody_only() -> None:
    if (
        PERSISTENCE_RANKING_AUTHORITY
        or PERSISTENCE_MEMBERSHIP_AUTHORITY
        or PERSISTENCE_LANE_MAPPING_AUTHORITY
        or PERSISTENCE_CAP23_SELECTION_AUTHORITY
        or PERSISTENCE_CAP24_BINDING_AUTHORITY
        or PERSISTENCE_TRADING_AUTHORITY
        or PERSISTENCE_EXECUTION_AUTHORITY
        or CAP23_CHANGE_REQUIRED
        or CAP24_CHANGE_REQUIRED
        or MASTER_V2_CHANGE_REQUIRED
        or DOUBLE_PLAY_CHANGE_REQUIRED
        or MF_PRODUCTIVE_JOIN
        or FIVE_LANE_RUNTIME_CREATED
        or FIVE_LANE_CONTINUOUS_HOST_JOIN
        or not UNIVERSE_ISOLATION_ENFORCED
    ):
        _fail(FAILURE_AUTHORITY, OWNER)
    if (
        CROSS_UNIVERSE_SELECTION
        or CROSS_UNIVERSE_PIN
        or CROSS_UNIVERSE_REPLACEMENT
        or CROSS_UNIVERSE_FALLBACK
        or CROSS_UNIVERSE_CANDIDATE_BORROWING
        or CROSS_UNIVERSE_RERANKING
        or MULTI_UNIVERSE_MERGE
        or INSTRUMENT_ID_ALONE_SUFFICIENT
    ):
        _fail(FAILURE_CROSS_UNIVERSE, "constant_violation")


def _require_mapping(payload: Any, *, code: str, detail: str) -> Mapping[str, Any]:
    if not isinstance(payload, Mapping):
        _fail(code, detail)
    return payload


def _validate_produced_topology(topology: IsolatedLaneTopologyV1) -> IsolatedLaneTopologyV1:
    if topology.owner != LANE_MAPPING_OWNER:
        _fail(FAILURE_AUTHORITY, topology.owner)
    if topology.contract_id != TOPOLOGY_CONTRACT_ID:
        _fail(FAILURE_UNSUPPORTED_SCHEMA, topology.contract_id)
    if topology.schema_version != TOPOLOGY_SCHEMA_VERSION:
        _fail(FAILURE_UNSUPPORTED_SCHEMA, topology.schema_version)
    if int(topology.max_positions_effective) != MAX_POSITIONS_EFFECTIVE:
        _fail(FAILURE_CORRUPT, "max_positions_effective")
    if topology.mf_productive_join or topology.five_lane_runtime_created:
        _fail(FAILURE_AUTHORITY, "productive_join")
    try:
        restored = isolated_lane_topology_from_dict(topology.to_dict())
    except IsolatedLaneTopologyError as exc:
        raise DurableLaneAssignmentPersistenceError(exc.failure_code, exc.detail) from exc
    if restored.to_dict() != topology.to_dict():
        _fail(FAILURE_CORRUPT, "topology_round_trip")
    return restored


def _envelope_for(topology: IsolatedLaneTopologyV1) -> dict[str, Any]:
    topology_payload = topology.to_dict()
    return {
        "contract_id": CONTRACT_ID,
        "integrity_digest": topology_integrity_digest_v1(topology_payload),
        "lane_mapping_owner": LANE_MAPPING_OWNER,
        "owner": OWNER,
        "schema_version": SCHEMA_VERSION,
        "topology": topology_payload,
    }


def _marker_for(envelope: Mapping[str, Any], topology: IsolatedLaneTopologyV1) -> dict[str, Any]:
    return {
        "integrity_digest": str(envelope["integrity_digest"]),
        "ranking_integrity_digest": topology.ranking_integrity_digest,
        "ranking_snapshot_id": topology.ranking_snapshot_id,
        "schema_version": SCHEMA_VERSION,
        "topology_state_root_base": topology.topology_state_root_base,
        "universe_snapshot_id": topology.universe_snapshot_id,
    }


def _load_json_object(path: Path, *, missing_code: str) -> Mapping[str, Any]:
    if not path.is_file():
        _fail(missing_code, path.name)
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:  # noqa: BLE001
        _fail(FAILURE_MALFORMED, f"{path.name}:{exc}")
    return _require_mapping(payload, code=FAILURE_MALFORMED, detail=path.name)


def _decode_checkpoint(
    envelope: Mapping[str, Any],
    *,
    expected_topology_state_root_base: Path | str,
    expected_universe_snapshot_id: str | None,
    expected_ranking_snapshot_id: str | None,
    expected_ranking_integrity_digest: str | None,
) -> IsolatedLaneTopologyV1:
    schema_version = str(envelope.get("schema_version") or "").strip()
    if schema_version != SCHEMA_VERSION:
        _fail(FAILURE_UNSUPPORTED_SCHEMA, schema_version or "missing")
    if str(envelope.get("contract_id") or "").strip() != CONTRACT_ID:
        _fail(FAILURE_UNSUPPORTED_SCHEMA, str(envelope.get("contract_id") or ""))
    if str(envelope.get("owner") or "").strip() != OWNER:
        _fail(FAILURE_AUTHORITY, str(envelope.get("owner") or ""))
    if str(envelope.get("lane_mapping_owner") or "").strip() != LANE_MAPPING_OWNER:
        _fail(FAILURE_AUTHORITY, str(envelope.get("lane_mapping_owner") or ""))
    topology_payload = _require_mapping(
        envelope.get("topology"), code=FAILURE_MALFORMED, detail="topology"
    )
    stored_digest = str(envelope.get("integrity_digest") or "").strip()
    recomputed = topology_integrity_digest_v1(topology_payload)
    if not stored_digest or stored_digest != recomputed:
        _fail(FAILURE_INTEGRITY, "topology")
    try:
        topology = isolated_lane_topology_from_dict(topology_payload)
    except IsolatedLaneTopologyError as exc:
        raise DurableLaneAssignmentPersistenceError(exc.failure_code, exc.detail) from exc
    _validate_produced_topology(topology)
    expected_base = lane_state_root_key(expected_topology_state_root_base)
    if topology.topology_state_root_base != expected_base:
        _fail(FAILURE_STATE_ROOT, "topology_state_root_base")
    if (
        expected_universe_snapshot_id is not None
        and topology.universe_snapshot_id != expected_universe_snapshot_id
    ):
        _fail(FAILURE_CROSS_UNIVERSE, "universe_snapshot_id")
    if (
        expected_ranking_snapshot_id is not None
        and topology.ranking_snapshot_id != expected_ranking_snapshot_id
    ):
        _fail(FAILURE_PROVENANCE, "ranking_snapshot_id")
    if (
        expected_ranking_integrity_digest is not None
        and topology.ranking_integrity_digest != expected_ranking_integrity_digest
    ):
        _fail(FAILURE_PROVENANCE, "ranking_integrity_digest")
    return topology


def persist_durable_lane_assignment_v1(
    *,
    topology: IsolatedLaneTopologyV1,
    writer: DurableLaneAssignmentSingleWriterV1,
    simulate_partial_write: bool = False,
    simulate_write_failure: bool = False,
    simulate_crash_after_checkpoint_before_marker: bool = False,
) -> dict[str, Any]:
    """Record an already-governed topology. Does not compute the next topology."""
    _assert_custody_only()
    try:
        writer.assert_held()
    except DuplicateLaneAssignmentWriterError as exc:
        raise DurableLaneAssignmentPersistenceError(exc.failure_code, str(exc)) from exc
    if simulate_write_failure:
        _fail(FAILURE_PARTIAL_WRITE, "SIMULATED_WRITE_FAILURE")
    validated = _validate_produced_topology(topology)
    root = checkpoint_root_for(validated.topology_state_root_base)
    expected_writer_root = Path(lane_state_root_key(writer.state_root))
    if Path(lane_state_root_key(root)) != expected_writer_root:
        _fail(FAILURE_STATE_ROOT, "writer_state_root")
    root.mkdir(parents=True, exist_ok=True)
    envelope = _envelope_for(validated)
    marker = _marker_for(envelope, validated)
    staging = root / f"{STAGING_DIRNAME_PREFIX}{uuid.uuid4().hex}"
    staging.mkdir(parents=True, exist_ok=False)
    try:
        checkpoint_text = json.dumps(envelope, sort_keys=True, indent=2) + "\n"
        marker_text = json.dumps(marker, sort_keys=True, indent=2) + "\n"
        (staging / CHECKPOINT_FILENAME).write_text(checkpoint_text, encoding="utf-8")
        if simulate_crash_after_checkpoint_before_marker:
            _atomic_write_text(root / CHECKPOINT_FILENAME, checkpoint_text)
            _fail(FAILURE_PARTIAL_WRITE, "SIMULATED_CHECKPOINT_WITHOUT_MARKER")
        (staging / COMMIT_MARKER_FILENAME).write_text(marker_text, encoding="utf-8")
        write_manifest(staging, (CHECKPOINT_FILENAME, COMMIT_MARKER_FILENAME))
        if simulate_partial_write:
            _atomic_write_text(root / CHECKPOINT_FILENAME, checkpoint_text)
            _fail(FAILURE_PARTIAL_WRITE, "SIMULATED_PARTIAL")
        for name in (CHECKPOINT_FILENAME, COMMIT_MARKER_FILENAME, MANIFEST_FILENAME):
            _atomic_write_text(root / name, (staging / name).read_text(encoding="utf-8"))
        verify_manifest(root)
        recovered = recover_durable_lane_assignment_v1(
            topology_state_root_base=validated.topology_state_root_base,
            recovery_mode=RECOVERY_MODE_RESTART,
            expected_universe_snapshot_id=validated.universe_snapshot_id,
            expected_ranking_snapshot_id=validated.ranking_snapshot_id,
            expected_ranking_integrity_digest=validated.ranking_integrity_digest,
        )
        if recovered is None or recovered.to_dict() != validated.to_dict():
            _fail(FAILURE_CORRUPT, "POST_LOAD")
        return {
            "checkpoint_path": str(checkpoint_path(root)),
            "integrity_digest": envelope["integrity_digest"],
            "ok": True,
            "topology_state_root_base": validated.topology_state_root_base,
        }
    finally:
        if staging.exists():
            shutil.rmtree(staging, ignore_errors=True)


def recover_durable_lane_assignment_v1(
    *,
    topology_state_root_base: Path | str,
    recovery_mode: str,
    expected_universe_snapshot_id: str | None = None,
    expected_ranking_snapshot_id: str | None = None,
    expected_ranking_integrity_digest: str | None = None,
) -> Optional[IsolatedLaneTopologyV1]:
    """Recover exact prior topology. Does not run the #6593 mapping transition."""
    _assert_custody_only()
    if recovery_mode not in RECOVERY_MODES:
        _fail(FAILURE_INVALID_RECOVERY_MODE, recovery_mode)
    root = checkpoint_root_for(topology_state_root_base)
    checkpoint = checkpoint_path(root)
    marker = commit_marker_path(root)
    prior_exists = marker.is_file() or checkpoint.is_file()
    if recovery_mode == RECOVERY_MODE_BOOTSTRAP:
        if prior_exists:
            _fail(FAILURE_BOOTSTRAP_WITH_PRIOR, str(root))
        return None
    if not checkpoint.is_file() or not marker.is_file() or not (root / MANIFEST_FILENAME).is_file():
        _fail(FAILURE_MISSING_RESTART, str(root))
    verify_manifest(root)
    envelope = _load_json_object(checkpoint, missing_code=FAILURE_MISSING_RESTART)
    marker_payload = _load_json_object(marker, missing_code=FAILURE_MISSING_RESTART)
    topology = _decode_checkpoint(
        envelope,
        expected_topology_state_root_base=topology_state_root_base,
        expected_universe_snapshot_id=expected_universe_snapshot_id,
        expected_ranking_snapshot_id=expected_ranking_snapshot_id,
        expected_ranking_integrity_digest=expected_ranking_integrity_digest,
    )
    marker_digest = str(marker_payload.get("integrity_digest") or "").strip()
    if marker_digest != str(envelope.get("integrity_digest") or "").strip():
        _fail(FAILURE_INTEGRITY, "commit_marker")
    if str(marker_payload.get("schema_version") or "").strip() != SCHEMA_VERSION:
        _fail(FAILURE_UNSUPPORTED_SCHEMA, str(marker_payload.get("schema_version") or ""))
    if str(marker_payload.get("universe_snapshot_id") or "") != topology.universe_snapshot_id:
        _fail(FAILURE_CROSS_UNIVERSE, "commit_marker_universe")
    if str(marker_payload.get("ranking_snapshot_id") or "") != topology.ranking_snapshot_id:
        _fail(FAILURE_PROVENANCE, "commit_marker_ranking")
    if (
        str(marker_payload.get("ranking_integrity_digest") or "")
        != topology.ranking_integrity_digest
    ):
        _fail(FAILURE_PROVENANCE, "commit_marker_digest")
    if lane_state_root_key(str(marker_payload.get("topology_state_root_base") or "")) != (
        topology.topology_state_root_base
    ):
        _fail(FAILURE_STATE_ROOT, "commit_marker_base")
    return topology
