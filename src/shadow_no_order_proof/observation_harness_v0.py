# Shadow Observation Harness v0 — declarative evidence only (no runtime entrypoint).
# Pure: dataclasses + stdlib hashing/json. No I/O, no network, no time lookups.

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Any, Mapping, Optional, cast

from src.shadow_no_order_proof.bounded_adapter_v0 import (
    BoundedShadowAdapterPlan,
    build_bounded_shadow_adapter_plan_v0,
)

OBSERVATION_EVIDENCE_SCHEMA_V0 = "shadow_observation_evidence_record.v0"


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
