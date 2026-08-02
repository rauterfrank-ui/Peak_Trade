"""DTOs for Cap 2.4 single selected future runtime binding."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from typing import Any, Mapping, Optional

from src.ops.single_selected_future_runtime_binding_v1.constants_v1 import (
    ALLOWLIST_SELECTION_AUTHORITY,
    AUTHORITY_OWNER,
    CAPABILITY_ID,
    CORE_LOGIC_CHANGE,
    DASHBOARD_AUTHORITY_EFFECT,
    DASHBOARD_ROLE,
    DIRECT_INSTRUMENT_OVERRIDE_ALLOWED,
    LIVE_AUTHORIZED,
    LIVE_PATH_CHANGED,
    MAX_POSITIONS_EFFECTIVE,
    MULTI_FUTURE_RUNTIME_AUTHORIZED,
    ORDERS_AUTHORIZED,
    OWNER,
    PRODUCER_VERSION,
    RUNTIME_ACTIVATION_ALLOWED,
    SCHEMA_VERSION,
    SELECTED_FUTURE_COUNT,
    SELECTION_AUTHORITY_OWNER,
    SELECTION_CONSUMER_IDENTITY,
    SELECTION_SINGLE_WRITER,
    SINGLE_SELECTED_FUTURE,
)


def canonical_json_dumps(payload: Mapping[str, Any] | list[Any] | Any) -> str:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def sha256_hex(payload: str | bytes) -> str:
    if isinstance(payload, str):
        payload = payload.encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


@dataclass(frozen=True)
class BoundInstrumentV1:
    instrument_id: str
    venue_native_id: str
    ranking_snapshot_id: str
    ranking_integrity_digest: str
    universe_snapshot_id: str
    selection_id: str
    selection_integrity_digest: str
    selection_state: str
    selected_future_count: int = SELECTED_FUTURE_COUNT
    max_positions_effective: int = MAX_POSITIONS_EFFECTIVE

    def to_dict(self) -> dict[str, Any]:
        return {
            "instrument_id": self.instrument_id,
            "venue_native_id": self.venue_native_id,
            "ranking_snapshot_id": self.ranking_snapshot_id,
            "ranking_integrity_digest": self.ranking_integrity_digest,
            "universe_snapshot_id": self.universe_snapshot_id,
            "selection_id": self.selection_id,
            "selection_integrity_digest": self.selection_integrity_digest,
            "selection_state": self.selection_state,
            "selected_future_count": int(self.selected_future_count),
            "max_positions_effective": int(self.max_positions_effective),
        }


@dataclass(frozen=True)
class RuntimeBindingEvidenceV1:
    capability_id: str
    schema_version: str
    producer_version: str
    owner: str
    ok: bool
    alpha_enabled: bool
    new_alpha_allowed: bool
    exit_risk_safety_preserved: bool
    hard_stop: bool
    selection_state: str
    instrument_id: str
    venue_native_id: str
    selection_id: str
    selection_integrity_digest: str
    ranking_snapshot_id: str
    ranking_integrity_digest: str
    universe_snapshot_id: str
    repository_sha: str
    config_digest: str
    reconciliation_before_alpha: bool
    reconciliation_alpha_enabled: bool
    reason_codes: tuple[str, ...]
    failure_codes: tuple[str, ...]
    call_graph: tuple[str, ...]
    authority: Mapping[str, Any] = field(default_factory=dict)
    notes: tuple[str, ...] = ()
    bound: Optional[Mapping[str, Any]] = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "capability_id": self.capability_id,
            "schema_version": self.schema_version,
            "producer_version": self.producer_version,
            "owner": self.owner,
            "ok": self.ok,
            "alpha_enabled": self.alpha_enabled,
            "new_alpha_allowed": self.new_alpha_allowed,
            "exit_risk_safety_preserved": self.exit_risk_safety_preserved,
            "hard_stop": self.hard_stop,
            "selection_state": self.selection_state,
            "instrument_id": self.instrument_id,
            "venue_native_id": self.venue_native_id,
            "selection_id": self.selection_id,
            "selection_integrity_digest": self.selection_integrity_digest,
            "ranking_snapshot_id": self.ranking_snapshot_id,
            "ranking_integrity_digest": self.ranking_integrity_digest,
            "universe_snapshot_id": self.universe_snapshot_id,
            "repository_sha": self.repository_sha,
            "config_digest": self.config_digest,
            "reconciliation_before_alpha": self.reconciliation_before_alpha,
            "reconciliation_alpha_enabled": self.reconciliation_alpha_enabled,
            "reason_codes": list(self.reason_codes),
            "failure_codes": list(self.failure_codes),
            "call_graph": list(self.call_graph),
            "authority": dict(self.authority),
            "notes": list(self.notes),
            "bound": None if self.bound is None else dict(self.bound),
        }


@dataclass(frozen=True)
class RuntimeBindingGateResultV1:
    ok: bool
    alpha_enabled: bool
    new_alpha_allowed: bool
    exit_risk_safety_preserved: bool
    hard_stop: bool
    selection_state: str
    bound: Optional[BoundInstrumentV1]
    evidence: RuntimeBindingEvidenceV1
    blockers: tuple[str, ...] = ()
    reconciliation_result: Optional[Mapping[str, Any]] = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "ok": self.ok,
            "alpha_enabled": self.alpha_enabled,
            "new_alpha_allowed": self.new_alpha_allowed,
            "exit_risk_safety_preserved": self.exit_risk_safety_preserved,
            "hard_stop": self.hard_stop,
            "selection_state": self.selection_state,
            "bound": None if self.bound is None else self.bound.to_dict(),
            "evidence": self.evidence.to_dict(),
            "blockers": list(self.blockers),
            "reconciliation_result": (
                None if self.reconciliation_result is None else dict(self.reconciliation_result)
            ),
        }


def authority_block() -> dict[str, Any]:
    return {
        "AUTHORITY_OWNER": AUTHORITY_OWNER,
        "OWNER": OWNER,
        "SELECTION_AUTHORITY_OWNER": SELECTION_AUTHORITY_OWNER,
        "SELECTION_SINGLE_WRITER": SELECTION_SINGLE_WRITER,
        "SELECTION_CONSUMER_IDENTITY": SELECTION_CONSUMER_IDENTITY,
        "SELECTED_FUTURE_COUNT": SELECTED_FUTURE_COUNT,
        "MAX_POSITIONS_EFFECTIVE": MAX_POSITIONS_EFFECTIVE,
        "MULTI_FUTURE_RUNTIME_AUTHORIZED": MULTI_FUTURE_RUNTIME_AUTHORIZED,
        "SINGLE_SELECTED_FUTURE": SINGLE_SELECTED_FUTURE,
        "DASHBOARD_AUTHORITY_EFFECT": DASHBOARD_AUTHORITY_EFFECT,
        "DASHBOARD_ROLE": DASHBOARD_ROLE,
        "ALLOWLIST_SELECTION_AUTHORITY": ALLOWLIST_SELECTION_AUTHORITY,
        "DIRECT_INSTRUMENT_OVERRIDE_ALLOWED": DIRECT_INSTRUMENT_OVERRIDE_ALLOWED,
        "CORE_LOGIC_CHANGE": CORE_LOGIC_CHANGE,
        "LIVE_PATH_CHANGED": LIVE_PATH_CHANGED,
        "RUNTIME_ACTIVATION_ALLOWED": RUNTIME_ACTIVATION_ALLOWED,
        "LIVE_AUTHORIZED": LIVE_AUTHORIZED,
        "ORDERS_AUTHORIZED": ORDERS_AUTHORIZED,
        "SCHEMA_VERSION": SCHEMA_VERSION,
        "PRODUCER_VERSION": PRODUCER_VERSION,
        "CAPABILITY_ID": CAPABILITY_ID,
    }


def compute_config_digest_v1(*, repository_sha: str) -> str:
    payload = {
        "capability_id": CAPABILITY_ID,
        "schema_version": SCHEMA_VERSION,
        "producer_version": PRODUCER_VERSION,
        "selected_future_count": SELECTED_FUTURE_COUNT,
        "max_positions_effective": MAX_POSITIONS_EFFECTIVE,
        "multi_future_runtime_authorized": MULTI_FUTURE_RUNTIME_AUTHORIZED,
        "dashboard_authority_effect": DASHBOARD_AUTHORITY_EFFECT,
        "allowlist_selection_authority": ALLOWLIST_SELECTION_AUTHORITY,
        "direct_instrument_override_allowed": DIRECT_INSTRUMENT_OVERRIDE_ALLOWED,
        "core_logic_change": CORE_LOGIC_CHANGE,
        "runtime_activation_allowed": RUNTIME_ACTIVATION_ALLOWED,
        "repository_sha": repository_sha,
    }
    return sha256_hex(canonical_json_dumps(payload))
