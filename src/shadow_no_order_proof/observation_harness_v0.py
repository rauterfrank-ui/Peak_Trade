# Shadow Observation Harness v0 — declarative evidence only (no runtime entrypoint).
# Core helpers: dataclasses + stdlib hashing/json (no network, no wall-clock reads).
# Bounded filesystem output exists only in write_shadow_observation_local_evidence_v0.

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass, fields, is_dataclass
from pathlib import Path
from typing import Any, Mapping, Optional, Sequence, Union, cast

from src.shadow_no_order_proof.bounded_adapter_v0 import (
    BoundedShadowAdapterPlan,
    build_bounded_shadow_adapter_plan_v0,
)

OBSERVATION_EVIDENCE_SCHEMA_V0 = "shadow_observation_evidence_record.v0"
OBSERVATION_BATCH_SUMMARY_SCHEMA_V0 = "shadow_observation_batch_summary.v0"
TIMED_OBSERVATION_SUMMARY_SCHEMA_V0 = "shadow_observation_timed_summary.v0"
LOCAL_OBSERVATION_RUN_RESULT_SCHEMA_V0 = "shadow_observation_local_run_result.v0"
LOCAL_OBSERVATION_EVIDENCE_OUTPUT_SCHEMA_V0 = "shadow_observation_local_evidence_manifest.v0"

_LOCAL_RUN_RESULT_BASENAME = "local_run_result.json"
_MANIFEST_BASENAME = "manifest.json"
_MANIFEST_SHA256_BASENAME = "MANIFEST.sha256"

_SAFE_RUN_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,254}$")


@dataclass(frozen=True)
class ShadowObservationInputSnapshot:
    """Caller-supplied observation inputs — no broker/exchange/client fields."""

    symbol: str
    observed_at_utc: str
    source: str
    payload: Mapping[str, object]


@dataclass(frozen=True)
class ShadowObservationEvidenceRecord:
    """Deterministic evidence bridge: snapshot + bounded adapter plan (metadata only)."""

    evidence_version: str
    adapter_kind: str
    source: str
    observed_at_utc: str
    evidence_id: str
    evidence_hash: str
    proof_version: str
    allowed_actions: tuple[str, ...]
    evidence_required: bool
    proven_shadow_no_order_entrypoint_found: bool
    executable_command_created: bool
    shadow_mode_allowed: bool
    order_submission_allowed: bool
    broker_allowed: bool
    exchange_allowed: bool
    runtime_allowed: bool
    scheduler_allowed: bool
    live_allowed: bool
    testnet_allowed: bool
    paper_allowed: bool
    broker_touched: bool
    exchange_touched: bool
    credentials_touched: bool
    order_intent_created: bool
    runtime_started: bool
    scheduler_started: bool


@dataclass(frozen=True)
class ShadowObservationBatchSummary:
    """Deterministic aggregate over ordered evidence records (metadata only)."""

    batch_version: str
    record_count: int
    evidence_ids: tuple[str, ...]
    batch_hash: str
    all_no_order: bool
    all_broker_touched_false: bool
    all_exchange_touched_false: bool
    all_credentials_touched_false: bool
    all_order_intent_created_false: bool
    all_runtime_started_false: bool
    all_scheduler_started_false: bool
    all_shadow_mode_allowed_false: bool
    proven_shadow_no_order_entrypoint_found: bool
    executable_command_created: bool


@dataclass(frozen=True)
class ShadowObservationTimedSummary:
    """Deterministic summary: batch evidence + caller-provided cadence metadata (no wall-clock)."""

    timed_version: str
    batch_version: str
    record_count: int
    evidence_ids: tuple[str, ...]
    batch_hash: str
    timed_hash: str
    started_at_utc: str
    ended_at_utc: str
    cadence_seconds: int
    max_observations: int
    observed_at_utc_values: tuple[str, ...]
    cadence_source: str
    all_no_order: bool
    all_broker_touched_false: bool
    all_exchange_touched_false: bool
    all_credentials_touched_false: bool
    all_order_intent_created_false: bool
    all_runtime_started_false: bool
    all_scheduler_started_false: bool
    all_shadow_mode_allowed_false: bool
    proven_shadow_no_order_entrypoint_found: bool
    executable_command_created: bool


@dataclass(frozen=True)
class ShadowObservationLocalRunResult:
    """Pure composition of batch + timed summaries with an explicit run boundary hash (no runtime)."""

    run_version: str
    run_id: str
    source: str
    cadence_source: str
    started_at_utc: str
    ended_at_utc: str
    cadence_seconds: int
    max_observations: int
    record_count: int
    evidence_ids: tuple[str, ...]
    batch_hash: str
    timed_hash: str
    run_hash: str
    records: tuple[ShadowObservationEvidenceRecord, ...]
    batch_summary: ShadowObservationBatchSummary
    timed_summary: ShadowObservationTimedSummary
    all_no_order: bool
    all_broker_touched_false: bool
    all_exchange_touched_false: bool
    all_credentials_touched_false: bool
    all_order_intent_created_false: bool
    all_runtime_started_false: bool
    all_scheduler_started_false: bool
    all_shadow_mode_allowed_false: bool
    proven_shadow_no_order_entrypoint_found: bool
    executable_command_created: bool
    local_observation_run_approved: bool
    shadow_mode_allowed: bool
    runtime_allowed: bool
    scheduler_allowed: bool
    order_submission_allowed: bool


@dataclass(frozen=True)
class ShadowObservationLocalEvidenceBundleV0:
    """Deterministic JSON payloads for a local run evidence folder (no filesystem access)."""

    local_run_result_json_bytes: bytes
    manifest_json_bytes: bytes


@dataclass(frozen=True)
class ShadowObservationEvidenceOutputReceipt:
    """Receipt for a bounded write under caller-provided output_dir/run_id (not an approval)."""

    output_root: str
    run_id: str
    local_run_result_path: str
    manifest_path: str
    manifest_sha256_path: str
    local_run_result_sha256: str
    manifest_sha256: str
    manifest_body_sha256_hex: str
    local_observation_evidence_output_approved: bool
    local_observation_run_approved: bool
    proven_shadow_no_order_entrypoint_found: bool
    executable_command_created: bool
    shadow_mode_allowed: bool
    runtime_allowed: bool
    scheduler_allowed: bool
    order_submission_allowed: bool


def _record_satisfies_no_order_invariants(rec: ShadowObservationEvidenceRecord) -> bool:
    if rec.allowed_actions:
        return False
    flags = (
        rec.broker_touched,
        rec.exchange_touched,
        rec.credentials_touched,
        rec.order_intent_created,
        rec.order_submission_allowed,
        rec.runtime_started,
        rec.scheduler_started,
        rec.shadow_mode_allowed,
        rec.live_allowed,
        rec.testnet_allowed,
        rec.paper_allowed,
        rec.broker_allowed,
        rec.exchange_allowed,
        rec.runtime_allowed,
        rec.scheduler_allowed,
        rec.proven_shadow_no_order_entrypoint_found,
        rec.executable_command_created,
    )
    return not any(flags)


def _batch_summary_fingerprint_bytes(*, evidence_ids: tuple[str, ...]) -> bytes:
    body: dict[str, object] = {
        "schema": OBSERVATION_BATCH_SUMMARY_SCHEMA_V0,
        "evidence_ids": list(evidence_ids),
    }
    return json.dumps(body, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode(
        "utf-8"
    )


def _timed_summary_fingerprint_bytes(
    *,
    batch_hash: str,
    evidence_ids: tuple[str, ...],
    started_at_utc: str,
    ended_at_utc: str,
    cadence_seconds: int,
    max_observations: int,
    cadence_source: str,
    observed_at_utc_values: tuple[str, ...],
) -> bytes:
    body: dict[str, object] = {
        "schema": TIMED_OBSERVATION_SUMMARY_SCHEMA_V0,
        "batch_hash": batch_hash,
        "evidence_ids": list(evidence_ids),
        "cadence_seconds": cadence_seconds,
        "cadence_source": cadence_source,
        "ended_at_utc": ended_at_utc,
        "max_observations": max_observations,
        "observed_at_utc_values": list(observed_at_utc_values),
        "started_at_utc": started_at_utc,
    }
    return json.dumps(body, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode(
        "utf-8"
    )


def _local_run_fingerprint_bytes(
    *,
    timed_hash: str,
    batch_hash: str,
    evidence_ids: tuple[str, ...],
    run_id: str,
    source: str,
    cadence_source: str,
    started_at_utc: str,
    ended_at_utc: str,
    cadence_seconds: int,
    max_observations: int,
) -> bytes:
    body: dict[str, object] = {
        "schema": LOCAL_OBSERVATION_RUN_RESULT_SCHEMA_V0,
        "batch_hash": batch_hash,
        "cadence_seconds": cadence_seconds,
        "cadence_source": cadence_source,
        "ended_at_utc": ended_at_utc,
        "evidence_ids": list(evidence_ids),
        "max_observations": max_observations,
        "run_id": run_id,
        "source": source,
        "started_at_utc": started_at_utc,
        "timed_hash": timed_hash,
    }
    return json.dumps(body, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode(
        "utf-8"
    )


def _canonical_json_primitive(obj: object) -> object:
    """Normalize nested structures for deterministic JSON (sorted dict keys, tuples as lists)."""
    if obj is None or isinstance(obj, (bool, int, float, str)):
        return obj
    if isinstance(obj, Mapping):
        mapping = cast(Mapping[str, Any], obj)
        return {k: _canonical_json_primitive(mapping[k]) for k in sorted(mapping)}
    if isinstance(obj, (list, tuple)):
        return [_canonical_json_primitive(x) for x in obj]
    raise TypeError(f"Unsupported payload type for canonical JSON: {type(obj)!r}")


def _observation_value_to_json_obj(obj: object) -> object:
    """Turn observation harness dataclasses/mappings into JSON-compatible trees."""
    if is_dataclass(obj) and not isinstance(obj, type):
        dc_any = cast(Any, obj)
        return {
            f.name: _observation_value_to_json_obj(getattr(dc_any, f.name)) for f in fields(dc_any)
        }
    if isinstance(obj, Mapping):
        mapping = cast(Mapping[str, Any], obj)
        return {k: _observation_value_to_json_obj(mapping[k]) for k in sorted(mapping)}
    if isinstance(obj, (list, tuple)):
        seq = cast(Sequence[object], obj)
        return [_observation_value_to_json_obj(x) for x in seq]
    if obj is None or isinstance(obj, (bool, int, float, str)):
        return obj
    raise TypeError(f"Unsupported observation export type: {type(obj)!r}")


def _require_safe_run_id(run_id: str) -> None:
    if run_id != run_id.strip() or not run_id:
        raise ValueError("run_id must be a non-empty trimmed string")
    if ".." in run_id:
        raise ValueError("run_id must not contain '..'")
    if _SAFE_RUN_ID_RE.match(run_id) is None:
        raise ValueError("run_id has unsafe characters")


def _dump_canonical_json_bytes(payload: Mapping[str, object]) -> bytes:
    return json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")


def build_shadow_observation_local_evidence_bundle_v0(
    result: ShadowObservationLocalRunResult,
) -> ShadowObservationLocalEvidenceBundleV0:
    """Serialize a local run result + deterministic manifest bytes (pure; no filesystem)."""
    body_obj = _observation_value_to_json_obj(result)
    body = cast(Mapping[str, object], body_obj)
    payload_bytes = _dump_canonical_json_bytes(body)
    payload_sha256 = hashlib.sha256(payload_bytes).hexdigest()
    manifest_body: dict[str, object] = {
        "schema": LOCAL_OBSERVATION_EVIDENCE_OUTPUT_SCHEMA_V0,
        "created_by": "shadow_observation_harness_v0",
        "run_id": result.run_id,
        "run_hash": result.run_hash,
        "files": [
            {
                "path": _LOCAL_RUN_RESULT_BASENAME,
                "sha256": payload_sha256,
                "bytes": len(payload_bytes),
            }
        ],
    }
    manifest_bytes = _dump_canonical_json_bytes(manifest_body)
    return ShadowObservationLocalEvidenceBundleV0(
        local_run_result_json_bytes=payload_bytes,
        manifest_json_bytes=manifest_bytes,
    )


def write_shadow_observation_local_evidence_v0(
    result: ShadowObservationLocalRunResult,
    *,
    output_dir: Union[str, Path],
    overwrite: bool = False,
) -> ShadowObservationEvidenceOutputReceipt:
    """Write bounded evidence files under output_dir/run_id (caller-owned paths only)."""
    _require_safe_run_id(result.run_id)
    base = Path(output_dir).expanduser().resolve()
    base.mkdir(parents=True, exist_ok=True)
    dest = (base / result.run_id).resolve()
    if not dest.is_relative_to(base):
        raise ValueError("run_id resolves outside output_dir")
    dest.mkdir(parents=True, exist_ok=True)

    bundle = build_shadow_observation_local_evidence_bundle_v0(result)
    payload_bytes = bundle.local_run_result_json_bytes
    manifest_bytes = bundle.manifest_json_bytes
    manifest_body_hex = hashlib.sha256(manifest_bytes).hexdigest()
    digest_bytes = f"{manifest_body_hex}\n".encode("utf-8")

    p_payload = dest / _LOCAL_RUN_RESULT_BASENAME
    p_manifest = dest / _MANIFEST_BASENAME
    p_digest = dest / _MANIFEST_SHA256_BASENAME

    targets = (p_payload, p_manifest, p_digest)
    if not overwrite:
        for p in targets:
            if p.exists():
                raise FileExistsError(str(p))
    else:
        for p in targets:
            if p.exists():
                p.unlink()

    p_payload.write_bytes(payload_bytes)
    p_manifest.write_bytes(manifest_bytes)
    p_digest.write_bytes(digest_bytes)

    payload_written_hash = hashlib.sha256(p_payload.read_bytes()).hexdigest()
    manifest_written_hash = hashlib.sha256(p_manifest.read_bytes()).hexdigest()

    return ShadowObservationEvidenceOutputReceipt(
        output_root=str(dest),
        run_id=result.run_id,
        local_run_result_path=str(p_payload),
        manifest_path=str(p_manifest),
        manifest_sha256_path=str(p_digest),
        local_run_result_sha256=payload_written_hash,
        manifest_sha256=manifest_written_hash,
        manifest_body_sha256_hex=manifest_body_hex,
        local_observation_evidence_output_approved=False,
        local_observation_run_approved=result.local_observation_run_approved,
        proven_shadow_no_order_entrypoint_found=result.proven_shadow_no_order_entrypoint_found,
        executable_command_created=result.executable_command_created,
        shadow_mode_allowed=result.shadow_mode_allowed,
        runtime_allowed=result.runtime_allowed,
        scheduler_allowed=result.scheduler_allowed,
        order_submission_allowed=result.order_submission_allowed,
    )


def _fingerprint_bytes(
    *, snapshot: ShadowObservationInputSnapshot, plan: BoundedShadowAdapterPlan
) -> bytes:
    """Stable UTF-8 bytes for hashing; no wall-clock inputs."""
    body: dict[str, object] = {
        "schema": OBSERVATION_EVIDENCE_SCHEMA_V0,
        "snapshot": {
            "symbol": snapshot.symbol,
            "observed_at_utc": snapshot.observed_at_utc,
            "source": snapshot.source,
            "payload": _canonical_json_primitive(dict(snapshot.payload)),
        },
        "plan": {
            "adapter_kind": plan.adapter_kind,
            "source": plan.source,
            "proof_version": plan.proof_version,
            "allowed_actions": list(plan.allowed_actions),
            "forbidden_actions": list(plan.forbidden_actions),
            "evidence_required": plan.evidence_required,
            "proven_shadow_no_order_entrypoint_found": plan.proven_shadow_no_order_entrypoint_found,
            "executable_command_created": plan.executable_command_created,
            "not_executable_declaration": plan.not_executable_declaration,
            "not_approved_declaration": plan.not_approved_declaration,
            "shadow_mode_allowed": plan.shadow_mode_allowed,
            "order_submission_allowed": plan.order_submission_allowed,
            "broker_allowed": plan.broker_allowed,
            "exchange_allowed": plan.exchange_allowed,
            "runtime_allowed": plan.runtime_allowed,
            "scheduler_allowed": plan.scheduler_allowed,
            "live_allowed": plan.live_allowed,
            "testnet_allowed": plan.testnet_allowed,
            "paper_allowed": plan.paper_allowed,
        },
    }
    return json.dumps(body, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode(
        "utf-8"
    )


def build_shadow_observation_evidence_record_v0(
    *,
    snapshot: ShadowObservationInputSnapshot,
    plan: Optional[BoundedShadowAdapterPlan] = None,
) -> ShadowObservationEvidenceRecord:
    """Combine a snapshot with a bounded adapter plan into a deterministic evidence record."""
    resolved = (
        plan if plan is not None else build_bounded_shadow_adapter_plan_v0(source=snapshot.source)
    )
    raw = _fingerprint_bytes(snapshot=snapshot, plan=resolved)
    digest = hashlib.sha256(raw).hexdigest()
    return ShadowObservationEvidenceRecord(
        evidence_version=OBSERVATION_EVIDENCE_SCHEMA_V0,
        adapter_kind=resolved.adapter_kind,
        source=snapshot.source,
        observed_at_utc=snapshot.observed_at_utc,
        evidence_id=digest,
        evidence_hash=digest,
        proof_version=resolved.proof_version,
        allowed_actions=resolved.allowed_actions,
        evidence_required=resolved.evidence_required,
        proven_shadow_no_order_entrypoint_found=resolved.proven_shadow_no_order_entrypoint_found,
        executable_command_created=resolved.executable_command_created,
        shadow_mode_allowed=resolved.shadow_mode_allowed,
        order_submission_allowed=resolved.order_submission_allowed,
        broker_allowed=resolved.broker_allowed,
        exchange_allowed=resolved.exchange_allowed,
        runtime_allowed=resolved.runtime_allowed,
        scheduler_allowed=resolved.scheduler_allowed,
        live_allowed=resolved.live_allowed,
        testnet_allowed=resolved.testnet_allowed,
        paper_allowed=resolved.paper_allowed,
        broker_touched=False,
        exchange_touched=False,
        credentials_touched=False,
        order_intent_created=False,
        runtime_started=False,
        scheduler_started=False,
    )


def run_shadow_observation_one_shot_v0(
    snapshot: ShadowObservationInputSnapshot,
) -> ShadowObservationEvidenceRecord:
    """One in-memory snapshot → one evidence record; bounded plan from `snapshot.source` only."""
    return build_shadow_observation_evidence_record_v0(snapshot=snapshot, plan=None)


def run_shadow_observation_batch_v0(
    snapshots: Sequence[ShadowObservationInputSnapshot],
) -> tuple[ShadowObservationEvidenceRecord, ...]:
    """Ordered snapshots → ordered evidence records; one one-shot evaluation per snapshot."""
    return tuple(run_shadow_observation_one_shot_v0(s) for s in snapshots)


def build_shadow_observation_batch_summary_v0(
    records: Sequence[ShadowObservationEvidenceRecord],
) -> ShadowObservationBatchSummary:
    """Derive a deterministic batch summary and hash from an ordered evidence sequence."""
    ordered = tuple(records)
    evidence_ids = tuple(r.evidence_id for r in ordered)
    raw = _batch_summary_fingerprint_bytes(evidence_ids=evidence_ids)
    batch_hash = hashlib.sha256(raw).hexdigest()

    if not ordered:
        return ShadowObservationBatchSummary(
            batch_version=OBSERVATION_BATCH_SUMMARY_SCHEMA_V0,
            record_count=0,
            evidence_ids=evidence_ids,
            batch_hash=batch_hash,
            all_no_order=True,
            all_broker_touched_false=True,
            all_exchange_touched_false=True,
            all_credentials_touched_false=True,
            all_order_intent_created_false=True,
            all_runtime_started_false=True,
            all_scheduler_started_false=True,
            all_shadow_mode_allowed_false=True,
            proven_shadow_no_order_entrypoint_found=False,
            executable_command_created=False,
        )

    return ShadowObservationBatchSummary(
        batch_version=OBSERVATION_BATCH_SUMMARY_SCHEMA_V0,
        record_count=len(ordered),
        evidence_ids=evidence_ids,
        batch_hash=batch_hash,
        all_no_order=all(_record_satisfies_no_order_invariants(r) for r in ordered),
        all_broker_touched_false=all(not r.broker_touched for r in ordered),
        all_exchange_touched_false=all(not r.exchange_touched for r in ordered),
        all_credentials_touched_false=all(not r.credentials_touched for r in ordered),
        all_order_intent_created_false=all(not r.order_intent_created for r in ordered),
        all_runtime_started_false=all(not r.runtime_started for r in ordered),
        all_scheduler_started_false=all(not r.scheduler_started for r in ordered),
        all_shadow_mode_allowed_false=all(not r.shadow_mode_allowed for r in ordered),
        proven_shadow_no_order_entrypoint_found=False,
        executable_command_created=False,
    )


def build_shadow_observation_timed_summary_v0(
    records: Sequence[ShadowObservationEvidenceRecord],
    *,
    started_at_utc: str,
    ended_at_utc: str,
    cadence_seconds: int,
    max_observations: int,
    cadence_source: str = "caller_provided",
) -> ShadowObservationTimedSummary:
    """Batch summary plus caller-supplied timing metadata → deterministic timed hash; no I/O or clocks."""
    if cadence_seconds < 0:
        raise ValueError("cadence_seconds must be >= 0")
    if max_observations < 0:
        raise ValueError("max_observations must be >= 0")
    ordered = tuple(records)
    batch = build_shadow_observation_batch_summary_v0(ordered)
    observed_at_utc_values = tuple(rec.observed_at_utc for rec in ordered)
    raw = _timed_summary_fingerprint_bytes(
        batch_hash=batch.batch_hash,
        evidence_ids=batch.evidence_ids,
        started_at_utc=started_at_utc,
        ended_at_utc=ended_at_utc,
        cadence_seconds=cadence_seconds,
        max_observations=max_observations,
        cadence_source=cadence_source,
        observed_at_utc_values=observed_at_utc_values,
    )
    timed_hash = hashlib.sha256(raw).hexdigest()
    return ShadowObservationTimedSummary(
        timed_version=TIMED_OBSERVATION_SUMMARY_SCHEMA_V0,
        batch_version=batch.batch_version,
        record_count=batch.record_count,
        evidence_ids=batch.evidence_ids,
        batch_hash=batch.batch_hash,
        timed_hash=timed_hash,
        started_at_utc=started_at_utc,
        ended_at_utc=ended_at_utc,
        cadence_seconds=cadence_seconds,
        max_observations=max_observations,
        observed_at_utc_values=observed_at_utc_values,
        cadence_source=cadence_source,
        all_no_order=batch.all_no_order,
        all_broker_touched_false=batch.all_broker_touched_false,
        all_exchange_touched_false=batch.all_exchange_touched_false,
        all_credentials_touched_false=batch.all_credentials_touched_false,
        all_order_intent_created_false=batch.all_order_intent_created_false,
        all_runtime_started_false=batch.all_runtime_started_false,
        all_scheduler_started_false=batch.all_scheduler_started_false,
        all_shadow_mode_allowed_false=batch.all_shadow_mode_allowed_false,
        proven_shadow_no_order_entrypoint_found=False,
        executable_command_created=False,
    )


def run_shadow_observation_local_v0(
    snapshots: Sequence[ShadowObservationInputSnapshot],
    *,
    started_at_utc: str,
    ended_at_utc: str,
    cadence_seconds: int,
    max_observations: int,
    run_id: str,
    source: str = "caller_provided",
    cadence_source: str = "caller_provided",
) -> ShadowObservationLocalRunResult:
    """Finite caller snapshots + metadata → records, batch summary, timed summary, deterministic run hash."""
    ordered_snaps = tuple(snapshots)
    if len(ordered_snaps) > max_observations:
        raise ValueError("snapshot count exceeds max_observations")
    records = run_shadow_observation_batch_v0(ordered_snaps)
    batch_summary = build_shadow_observation_batch_summary_v0(records)
    timed_summary = build_shadow_observation_timed_summary_v0(
        records,
        started_at_utc=started_at_utc,
        ended_at_utc=ended_at_utc,
        cadence_seconds=cadence_seconds,
        max_observations=max_observations,
        cadence_source=cadence_source,
    )
    raw = _local_run_fingerprint_bytes(
        timed_hash=timed_summary.timed_hash,
        batch_hash=batch_summary.batch_hash,
        evidence_ids=batch_summary.evidence_ids,
        run_id=run_id,
        source=source,
        cadence_source=cadence_source,
        started_at_utc=started_at_utc,
        ended_at_utc=ended_at_utc,
        cadence_seconds=cadence_seconds,
        max_observations=max_observations,
    )
    run_hash = hashlib.sha256(raw).hexdigest()
    return ShadowObservationLocalRunResult(
        run_version=LOCAL_OBSERVATION_RUN_RESULT_SCHEMA_V0,
        run_id=run_id,
        source=source,
        cadence_source=cadence_source,
        started_at_utc=started_at_utc,
        ended_at_utc=ended_at_utc,
        cadence_seconds=cadence_seconds,
        max_observations=max_observations,
        record_count=batch_summary.record_count,
        evidence_ids=batch_summary.evidence_ids,
        batch_hash=batch_summary.batch_hash,
        timed_hash=timed_summary.timed_hash,
        run_hash=run_hash,
        records=records,
        batch_summary=batch_summary,
        timed_summary=timed_summary,
        all_no_order=batch_summary.all_no_order,
        all_broker_touched_false=batch_summary.all_broker_touched_false,
        all_exchange_touched_false=batch_summary.all_exchange_touched_false,
        all_credentials_touched_false=batch_summary.all_credentials_touched_false,
        all_order_intent_created_false=batch_summary.all_order_intent_created_false,
        all_runtime_started_false=batch_summary.all_runtime_started_false,
        all_scheduler_started_false=batch_summary.all_scheduler_started_false,
        all_shadow_mode_allowed_false=batch_summary.all_shadow_mode_allowed_false,
        proven_shadow_no_order_entrypoint_found=False,
        executable_command_created=False,
        local_observation_run_approved=False,
        shadow_mode_allowed=False,
        runtime_allowed=False,
        scheduler_allowed=False,
        order_submission_allowed=False,
    )
