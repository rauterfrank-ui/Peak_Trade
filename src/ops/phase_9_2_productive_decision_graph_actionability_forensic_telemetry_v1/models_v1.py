"""Models for ProductiveDecisionStageObservationV1 (no decision authority)."""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass, field
from typing import Any, Mapping, Optional


def sha256_hex(payload: str | bytes) -> str:
    if isinstance(payload, str):
        payload = payload.encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def canonical_digest_v1(obj: Any) -> str:
    material = json.dumps(obj, sort_keys=True, separators=(",", ":"), default=str)
    return sha256_hex(material)


def redact_detail_v1(detail: str | None) -> str:
    """Redact potentially sensitive detail while keeping diagnostic class tokens."""
    if detail is None:
        return ""
    text = str(detail)
    # Never persist credential-like substrings.
    lowered = text.lower()
    for token in ("secret", "password", "apikey", "api_key", "token=", "bearer "):
        if token in lowered:
            return "REDACTED_SENSITIVE"
    if len(text) > 512:
        return text[:512] + "...REDACTED_TRUNCATED"
    return text


@dataclass(frozen=True)
class ProductiveDecisionStageObservationV1:
    schema_version: str
    repository_sha: str
    config_digest: str
    runtime_session_id: str
    decision_cycle_id: str
    instrument_id: str
    market_event_time: float | None
    observation_identity: str
    observation_epoch: int | None
    confirmation_session_id: str
    stage: str
    stage_call_order_index: int
    input_state_digest: str
    output_state_digest: str
    evaluated: bool
    passed: bool
    blocked: bool
    not_reached: bool
    not_applicable: bool
    decision: str
    reason_code: str
    reason_detail_redacted: str
    authority_symbol: str
    intended_side: str
    position_state: str
    scope_state: str
    confirmation_phase: str
    entry_actionable: bool
    reduce_actionable: bool
    exit_actionable: bool
    terminal_for_cycle: bool
    terminal_blocking_stage: bool
    producer_version: str = "productive_decision_graph_actionability_forensic_telemetry.v1"
    telemetry_decision_authority: bool = False

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class CycleTerminalRecordV1:
    schema_version: str
    repository_sha: str
    config_digest: str
    runtime_session_id: str
    decision_cycle_id: str
    instrument_id: str
    market_event_time: float | None
    terminal_outcome: str
    primary_reason: str | None
    secondary_reasons: tuple[str, ...] = ()
    terminal_blocking_stage: str | None = None
    terminal_blocking_stage_index: int | None = None
    entry_actionable: bool = False
    reduce_actionable: bool = False
    exit_actionable: bool = False
    intended_side: str = "HOLD"
    decision_outcome: str = ""
    distance_to_actionability: dict[str, Any] = field(default_factory=dict)
    stage_event_count: int = 0
    event_digest: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "repository_sha": self.repository_sha,
            "config_digest": self.config_digest,
            "runtime_session_id": self.runtime_session_id,
            "decision_cycle_id": self.decision_cycle_id,
            "instrument_id": self.instrument_id,
            "market_event_time": self.market_event_time,
            "terminal_outcome": self.terminal_outcome,
            "primary_reason": self.primary_reason,
            "secondary_reasons": list(self.secondary_reasons),
            "terminal_blocking_stage": self.terminal_blocking_stage,
            "terminal_blocking_stage_index": self.terminal_blocking_stage_index,
            "entry_actionable": self.entry_actionable,
            "reduce_actionable": self.reduce_actionable,
            "exit_actionable": self.exit_actionable,
            "intended_side": self.intended_side,
            "decision_outcome": self.decision_outcome,
            "distance_to_actionability": dict(self.distance_to_actionability),
            "stage_event_count": self.stage_event_count,
            "event_digest": self.event_digest,
        }


@dataclass
class DistanceToActionabilityV1:
    confirmation_epochs_current: int | None = None
    confirmation_epochs_required: int | None = None
    confirmation_epochs_remaining: int | None = None
    observe_threshold: float | None = None
    candidate_threshold: float | None = None
    confirm_threshold: float | None = None
    actual_directional_measure: float | None = None
    distance_to_candidate: float | None = None
    distance_to_confirm: float | None = None
    scope_boundary: float | None = None
    current_price: float | None = None
    distance_to_scope_transition: float | None = None
    composition_required_conditions: int | None = None
    composition_satisfied_conditions: int | None = None
    composition_missing_conditions: int | None = None
    risk_headroom: float | None = None
    safety_state: str | None = None
    missing_fields: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["missing_fields"] = list(self.missing_fields)
        d["diagnostic_only"] = True
        return d


def empty_counters_v1(keys: tuple[str, ...]) -> dict[str, int]:
    return {k: 0 for k in keys}


def merge_mapping_int_v1(dst: dict[str, int], src: Mapping[str, int]) -> None:
    for k, v in src.items():
        dst[k] = int(dst.get(k, 0)) + int(v)


def optional_float_v1(value: Any) -> Optional[float]:
    if value is None:
        return None
    try:
        f = float(value)
    except (TypeError, ValueError):
        return None
    if f != f or f in (float("inf"), float("-inf")):
        return None
    return f
