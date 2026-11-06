"""DTOs for Cap 5.1 deterministic offline evidence."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from typing import Any, Mapping, Optional

from src.ops.single_future_canonical_runtime_deterministic_offline_evidence_v1.constants_v1 import (
    CANONICAL_DIGEST_EXCLUDED_KEYS,
    CANONICAL_RUNTIME_ENTRYPOINT_STATUS,
    CAPABILITY_ID,
    OWNER,
    PRODUCER_VERSION,
    RUNTIME_ACTIVATED,
    SCHEMA_VERSION,
)


def canonical_json_dumps(payload: Mapping[str, Any] | list[Any] | Any) -> str:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def sha256_hex(payload: str | bytes) -> str:
    if isinstance(payload, str):
        payload = payload.encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def strip_volatile_for_canonical_digest(payload: Any) -> Any:
    """Recursively drop volatile path/time fields from canonical digest material."""
    if isinstance(payload, Mapping):
        out: dict[str, Any] = {}
        for key, value in payload.items():
            if str(key) in CANONICAL_DIGEST_EXCLUDED_KEYS:
                continue
            out[str(key)] = strip_volatile_for_canonical_digest(value)
        return out
    if isinstance(payload, (list, tuple)):
        return [strip_volatile_for_canonical_digest(x) for x in payload]
    return payload


def canonical_digest_v1(payload: Mapping[str, Any] | list[Any] | Any) -> str:
    return sha256_hex(canonical_json_dumps(strip_volatile_for_canonical_digest(payload)))


@dataclass(frozen=True)
class OfflineEvidenceGateFlagsV1:
    flags: Mapping[str, bool]

    def all_true(self) -> bool:
        return all(bool(v) for v in self.flags.values())

    def false_flags(self) -> tuple[str, ...]:
        return tuple(sorted(k for k, v in self.flags.items() if not bool(v)))

    def to_dict(self) -> dict[str, Any]:
        return {k: bool(v) for k, v in sorted(self.flags.items())}


@dataclass(frozen=True)
class AnalyticalSessionLockV1:
    identity: str
    session_id: str
    lock_path: str
    acquired: bool
    network_session: bool = False
    authorization_consumed: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "identity": self.identity,
            "session_id": self.session_id,
            "lock_path": self.lock_path,
            "acquired": self.acquired,
            "network_session": self.network_session,
            "authorization_consumed": self.authorization_consumed,
        }


@dataclass(frozen=True)
class ReplayTelemetryV1:
    cycle_count: int
    distinct_observation_count: int
    duplicate_observation_count: int
    missing_observation_count: int
    hold_count: int
    entry_count: int
    reduce_count: int
    exit_count: int
    blocked_reason_counts: Mapping[str, int]
    decision_outcomes: tuple[str, ...]
    intended_actions: tuple[Mapping[str, Any], ...]
    simulated_fills: tuple[Mapping[str, Any], ...]
    risk_vetoes: int
    safety_vetoes: int
    typed_volatility_presence_events: int
    numeric_max_age_strata_diagnostic: tuple[Mapping[str, Any], ...]
    total_fees: str
    total_slippage: str
    realized_pnl: str
    unrealized_pnl: str
    max_drawdown: str
    profit_factor: Optional[str]
    turnover: str
    portfolio_state_digest: str
    risk_state_digest: str
    selected_future_identity: Mapping[str, Any]
    native_instrument_binding: Mapping[str, Any]
    reconciliation_result: Mapping[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return {
            "cycle_count": self.cycle_count,
            "distinct_observation_count": self.distinct_observation_count,
            "duplicate_observation_count": self.duplicate_observation_count,
            "missing_observation_count": self.missing_observation_count,
            "hold_count": self.hold_count,
            "entry_count": self.entry_count,
            "reduce_count": self.reduce_count,
            "exit_count": self.exit_count,
            "blocked_reason_counts": dict(sorted(self.blocked_reason_counts.items())),
            "decision_outcomes": list(self.decision_outcomes),
            "intended_actions": [dict(x) for x in self.intended_actions],
            "simulated_fills": [dict(x) for x in self.simulated_fills],
            "risk_vetoes": self.risk_vetoes,
            "safety_vetoes": self.safety_vetoes,
            "typed_volatility_presence_events": self.typed_volatility_presence_events,
            "numeric_max_age_strata_diagnostic": [
                dict(x) for x in self.numeric_max_age_strata_diagnostic
            ],
            "total_fees": self.total_fees,
            "total_slippage": self.total_slippage,
            "realized_pnl": self.realized_pnl,
            "unrealized_pnl": self.unrealized_pnl,
            "max_drawdown": self.max_drawdown,
            "profit_factor": self.profit_factor,
            "turnover": self.turnover,
            "portfolio_state_digest": self.portfolio_state_digest,
            "risk_state_digest": self.risk_state_digest,
            "selected_future_identity": dict(self.selected_future_identity),
            "native_instrument_binding": dict(self.native_instrument_binding),
            "reconciliation_result": dict(self.reconciliation_result),
        }


@dataclass(frozen=True)
class OfflineEvidenceBundleV1:
    capability_id: str
    schema_version: str
    producer_version: str
    owner: str
    ok: bool
    repository_sha: str
    baseline_sha: str
    config_digest: str
    fixture_digest: str
    fixture_version: str
    call_graph_before: tuple[str, ...]
    call_graph_after: tuple[str, ...]
    productive_call_graph_proven: tuple[str, ...]
    gate_flags: Mapping[str, bool]
    telemetry: Mapping[str, Any]
    restart_recovery: Mapping[str, Any]
    failure_injection_results: Mapping[str, Any]
    activation_negative: Mapping[str, Any]
    network_order_negative: Mapping[str, Any]
    legacy_authority_check: Mapping[str, Any]
    independent_run: Mapping[str, Any]
    verifier_result: Mapping[str, Any]
    canonical_outcome_digest: str
    canonical_runtime_entrypoint_status: str = CANONICAL_RUNTIME_ENTRYPOINT_STATUS
    runtime_activated: bool = RUNTIME_ACTIVATED
    notes: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return {
            "capability_id": self.capability_id,
            "schema_version": self.schema_version,
            "producer_version": self.producer_version,
            "owner": self.owner,
            "ok": self.ok,
            "repository_sha": self.repository_sha,
            "baseline_sha": self.baseline_sha,
            "config_digest": self.config_digest,
            "fixture_digest": self.fixture_digest,
            "fixture_version": self.fixture_version,
            "call_graph_before": list(self.call_graph_before),
            "call_graph_after": list(self.call_graph_after),
            "productive_call_graph_proven": list(self.productive_call_graph_proven),
            "gate_flags": dict(sorted(self.gate_flags.items())),
            "telemetry": dict(self.telemetry),
            "restart_recovery": dict(self.restart_recovery),
            "failure_injection_results": dict(self.failure_injection_results),
            "activation_negative": dict(self.activation_negative),
            "network_order_negative": dict(self.network_order_negative),
            "legacy_authority_check": dict(self.legacy_authority_check),
            "independent_run": dict(self.independent_run),
            "verifier_result": dict(self.verifier_result),
            "canonical_outcome_digest": self.canonical_outcome_digest,
            "CANONICAL_RUNTIME_ENTRYPOINT_STATUS": self.canonical_runtime_entrypoint_status,
            "RUNTIME_ACTIVATED": bool(self.runtime_activated),
            "notes": list(self.notes),
        }


@dataclass(frozen=True)
class OfflineEvidenceGateResultV1:
    ok: bool
    ready_for_activation: bool
    runtime_activated: bool
    hard_stop: bool
    status: str
    gate_flags: OfflineEvidenceGateFlagsV1
    evidence: OfflineEvidenceBundleV1
    blockers: tuple[str, ...] = ()
    failure_codes: tuple[str, ...] = ()
    offline_end_to_end: Optional[Mapping[str, Any]] = None
    bridge_cycles: tuple[Mapping[str, Any], ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return {
            "ok": self.ok,
            "ready_for_activation": self.ready_for_activation,
            "runtime_activated": self.runtime_activated,
            "hard_stop": self.hard_stop,
            "CANONICAL_RUNTIME_ENTRYPOINT_STATUS": self.status,
            "gate_flags": self.gate_flags.to_dict(),
            "evidence": self.evidence.to_dict(),
            "blockers": list(self.blockers),
            "failure_codes": list(self.failure_codes),
            "offline_end_to_end": (
                None if self.offline_end_to_end is None else dict(self.offline_end_to_end)
            ),
            "bridge_cycles": [dict(c) for c in self.bridge_cycles],
        }


@dataclass
class MutableGateAccumulatorV1:
    flags: dict[str, bool] = field(default_factory=dict)
    blockers: list[str] = field(default_factory=list)
    failure_codes: list[str] = field(default_factory=list)

    def set_flag(self, name: str, value: bool, *, failure_code: str | None = None) -> None:
        self.flags[name] = bool(value)
        if not value:
            self.blockers.append(name)
            if failure_code:
                self.failure_codes.append(failure_code)


def default_evidence_shell(
    *,
    repository_sha: str,
    baseline_sha: str,
    config_digest: str,
    fixture_digest: str,
    fixture_version: str,
) -> OfflineEvidenceBundleV1:
    return OfflineEvidenceBundleV1(
        capability_id=CAPABILITY_ID,
        schema_version=SCHEMA_VERSION,
        producer_version=PRODUCER_VERSION,
        owner=OWNER,
        ok=False,
        repository_sha=repository_sha,
        baseline_sha=baseline_sha,
        config_digest=config_digest,
        fixture_digest=fixture_digest,
        fixture_version=fixture_version,
        call_graph_before=(),
        call_graph_after=(),
        productive_call_graph_proven=(),
        gate_flags={},
        telemetry={},
        restart_recovery={},
        failure_injection_results={},
        activation_negative={},
        network_order_negative={},
        legacy_authority_check={},
        independent_run={},
        verifier_result={"ok": False},
        canonical_outcome_digest="",
    )
