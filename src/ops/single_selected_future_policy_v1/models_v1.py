"""Versioned DTOs for single selected future persistence (Capability 2.3)."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from typing import Any, Mapping, Optional, Sequence

from src.ops.single_selected_future_policy_v1.constants_v1 import (
    ALPHA_ALLOWED_DEFAULT,
    CAPABILITY_ID,
    DEFAULT_HYSTERESIS_RANK_IMPROVEMENT,
    DEFAULT_MAX_RANKING_AGE_SECONDS,
    DEFAULT_MIN_DATA_QUALITY_STATUS,
    DEFAULT_MIN_HISTORY_SAMPLES,
    DEFAULT_MIN_HOLDING_PERIOD_SECONDS,
    DEFAULT_REFRESH_CADENCE_SECONDS,
    MAX_POSITIONS_EFFECTIVE,
    OWNER,
    PRODUCER_VERSION,
    SCHEMA_VERSION,
    SELECTED_FUTURE_COUNT,
    SELECTION_POLICY_ID,
    SELECTION_POLICY_PROVENANCE,
    SELECTION_POLICY_VERSION,
    SINGLE_SELECTED_FUTURE,
    STATE_NO_SELECTION,
    VENUE,
)


def canonical_json_dumps(payload: Mapping[str, Any] | list[Any] | Any) -> str:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def sha256_hex(payload: str | bytes) -> str:
    if isinstance(payload, str):
        payload = payload.encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


@dataclass(frozen=True)
class SingleSelectedFutureSelectionV1:
    """Deterministic, versioned single-future selection DTO."""

    schema_version: str
    capability_id: str
    producer_version: str
    selection_id: str
    instrument_id: str
    venue_native_id: str
    ranking_snapshot_id: str
    ranking_integrity_digest: str
    ranking_event_time: str
    selected_at_event_time: str
    selected_at_wall_time: str
    valid_from: str
    valid_until: str
    policy_version: str
    policy_id: str
    config_digest: str
    repository_sha: str
    reason_codes: tuple[str, ...]
    state: str
    integrity_digest: str
    previous_state: str = STATE_NO_SELECTION
    previous_selection_id: str = ""
    previous_instrument_id: str = ""
    replacement_instrument_id: str = ""
    replacement_venue_native_id: str = ""
    selected_rank: int = 0
    selected_future_count: int = SELECTED_FUTURE_COUNT
    max_positions_effective: int = MAX_POSITIONS_EFFECTIVE
    single_selected_future: bool = SINGLE_SELECTED_FUTURE
    multi_future_runtime_authorized: bool = False
    alpha_allowed: bool = False
    alpha_authority_for_replacement: bool = False
    open_position_present: bool = False
    open_position_instrument_id: str = ""
    dashboard_input_used: bool = False
    allowlist_input_used: bool = False
    manual_override_used: bool = False
    selection_input_digest: str = ""
    policy_provenance: str = SELECTION_POLICY_PROVENANCE
    authority: Mapping[str, Any] = field(default_factory=dict)
    call_graph: tuple[str, ...] = ()
    failure_codes: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "capability_id": self.capability_id,
            "producer_version": self.producer_version,
            "selection_id": self.selection_id,
            "instrument_id": self.instrument_id,
            "venue_native_id": self.venue_native_id,
            "ranking_snapshot_id": self.ranking_snapshot_id,
            "ranking_integrity_digest": self.ranking_integrity_digest,
            "ranking_event_time": self.ranking_event_time,
            "selected_at_event_time": self.selected_at_event_time,
            "selected_at_wall_time": self.selected_at_wall_time,
            "valid_from": self.valid_from,
            "valid_until": self.valid_until,
            "policy_version": self.policy_version,
            "policy_id": self.policy_id,
            "policy_provenance": self.policy_provenance,
            "config_digest": self.config_digest,
            "repository_sha": self.repository_sha,
            "reason_codes": list(self.reason_codes),
            "state": self.state,
            "integrity_digest": self.integrity_digest,
            "previous_state": self.previous_state,
            "previous_selection_id": self.previous_selection_id,
            "previous_instrument_id": self.previous_instrument_id,
            "replacement_instrument_id": self.replacement_instrument_id,
            "replacement_venue_native_id": self.replacement_venue_native_id,
            "selected_rank": int(self.selected_rank),
            "selected_future_count": int(self.selected_future_count),
            "max_positions_effective": int(self.max_positions_effective),
            "single_selected_future": bool(self.single_selected_future),
            "multi_future_runtime_authorized": bool(self.multi_future_runtime_authorized),
            "alpha_allowed": bool(self.alpha_allowed),
            "alpha_authority_for_replacement": bool(self.alpha_authority_for_replacement),
            "open_position_present": bool(self.open_position_present),
            "open_position_instrument_id": self.open_position_instrument_id,
            "dashboard_input_used": bool(self.dashboard_input_used),
            "allowlist_input_used": bool(self.allowlist_input_used),
            "manual_override_used": bool(self.manual_override_used),
            "selection_input_digest": self.selection_input_digest,
            "authority": dict(self.authority),
            "call_graph": list(self.call_graph),
            "failure_codes": list(self.failure_codes),
        }

    def deterministic_payload_for_digest(self) -> dict[str, Any]:
        """Digest payload excludes wall-clock selection time."""
        payload = self.to_dict()
        payload.pop("integrity_digest", None)
        payload.pop("selected_at_wall_time", None)
        return payload

    def compute_integrity_digest(self) -> str:
        return sha256_hex(canonical_json_dumps(self.deterministic_payload_for_digest()))

    def with_integrity_digest(self) -> "SingleSelectedFutureSelectionV1":
        digest = self.compute_integrity_digest()
        return SingleSelectedFutureSelectionV1(
            schema_version=self.schema_version,
            capability_id=self.capability_id,
            producer_version=self.producer_version,
            selection_id=self.selection_id,
            instrument_id=self.instrument_id,
            venue_native_id=self.venue_native_id,
            ranking_snapshot_id=self.ranking_snapshot_id,
            ranking_integrity_digest=self.ranking_integrity_digest,
            ranking_event_time=self.ranking_event_time,
            selected_at_event_time=self.selected_at_event_time,
            selected_at_wall_time=self.selected_at_wall_time,
            valid_from=self.valid_from,
            valid_until=self.valid_until,
            policy_version=self.policy_version,
            policy_id=self.policy_id,
            config_digest=self.config_digest,
            repository_sha=self.repository_sha,
            reason_codes=self.reason_codes,
            state=self.state,
            integrity_digest=digest,
            previous_state=self.previous_state,
            previous_selection_id=self.previous_selection_id,
            previous_instrument_id=self.previous_instrument_id,
            replacement_instrument_id=self.replacement_instrument_id,
            replacement_venue_native_id=self.replacement_venue_native_id,
            selected_rank=self.selected_rank,
            selected_future_count=self.selected_future_count,
            max_positions_effective=self.max_positions_effective,
            single_selected_future=self.single_selected_future,
            multi_future_runtime_authorized=self.multi_future_runtime_authorized,
            alpha_allowed=self.alpha_allowed,
            alpha_authority_for_replacement=self.alpha_authority_for_replacement,
            open_position_present=self.open_position_present,
            open_position_instrument_id=self.open_position_instrument_id,
            dashboard_input_used=self.dashboard_input_used,
            allowlist_input_used=self.allowlist_input_used,
            manual_override_used=self.manual_override_used,
            selection_input_digest=self.selection_input_digest,
            policy_provenance=self.policy_provenance,
            authority=dict(self.authority),
            call_graph=self.call_graph,
            failure_codes=self.failure_codes,
        )

    @staticmethod
    def from_dict(payload: Mapping[str, Any]) -> "SingleSelectedFutureSelectionV1":
        return SingleSelectedFutureSelectionV1(
            schema_version=str(payload.get("schema_version") or ""),
            capability_id=str(payload.get("capability_id") or ""),
            producer_version=str(payload.get("producer_version") or ""),
            selection_id=str(payload.get("selection_id") or ""),
            instrument_id=str(payload.get("instrument_id") or ""),
            venue_native_id=str(payload.get("venue_native_id") or ""),
            ranking_snapshot_id=str(payload.get("ranking_snapshot_id") or ""),
            ranking_integrity_digest=str(payload.get("ranking_integrity_digest") or ""),
            ranking_event_time=str(payload.get("ranking_event_time") or ""),
            selected_at_event_time=str(payload.get("selected_at_event_time") or ""),
            selected_at_wall_time=str(payload.get("selected_at_wall_time") or ""),
            valid_from=str(payload.get("valid_from") or ""),
            valid_until=str(payload.get("valid_until") or ""),
            policy_version=str(payload.get("policy_version") or ""),
            policy_id=str(payload.get("policy_id") or ""),
            config_digest=str(payload.get("config_digest") or ""),
            repository_sha=str(payload.get("repository_sha") or ""),
            reason_codes=tuple(str(x) for x in (payload.get("reason_codes") or ())),
            state=str(payload.get("state") or STATE_NO_SELECTION),
            integrity_digest=str(payload.get("integrity_digest") or ""),
            previous_state=str(payload.get("previous_state") or STATE_NO_SELECTION),
            previous_selection_id=str(payload.get("previous_selection_id") or ""),
            previous_instrument_id=str(payload.get("previous_instrument_id") or ""),
            replacement_instrument_id=str(payload.get("replacement_instrument_id") or ""),
            replacement_venue_native_id=str(payload.get("replacement_venue_native_id") or ""),
            selected_rank=int(payload.get("selected_rank") or 0),
            selected_future_count=int(
                payload.get("selected_future_count") or SELECTED_FUTURE_COUNT
            ),
            max_positions_effective=int(
                payload.get("max_positions_effective") or MAX_POSITIONS_EFFECTIVE
            ),
            single_selected_future=bool(
                payload.get("single_selected_future", SINGLE_SELECTED_FUTURE)
            ),
            multi_future_runtime_authorized=bool(
                payload.get("multi_future_runtime_authorized", False)
            ),
            alpha_allowed=bool(payload.get("alpha_allowed", False)),
            alpha_authority_for_replacement=bool(
                payload.get("alpha_authority_for_replacement", False)
            ),
            open_position_present=bool(payload.get("open_position_present", False)),
            open_position_instrument_id=str(payload.get("open_position_instrument_id") or ""),
            dashboard_input_used=bool(payload.get("dashboard_input_used", False)),
            allowlist_input_used=bool(payload.get("allowlist_input_used", False)),
            manual_override_used=bool(payload.get("manual_override_used", False)),
            selection_input_digest=str(payload.get("selection_input_digest") or ""),
            policy_provenance=str(payload.get("policy_provenance") or SELECTION_POLICY_PROVENANCE),
            authority=dict(payload.get("authority") or {}),
            call_graph=tuple(str(x) for x in (payload.get("call_graph") or ())),
            failure_codes=tuple(str(x) for x in (payload.get("failure_codes") or ())),
        )


@dataclass(frozen=True)
class SelectionProduceResultV1:
    selection: SingleSelectedFutureSelectionV1
    ok: bool
    hard_stop: bool
    failure_codes: tuple[str, ...]
    alpha_blocked: bool = True


def authority_block() -> dict[str, Any]:
    return {
        "SELECTION_AUTHORITY_OWNER_SINGLE": True,
        "AUTHORITY_OWNER": CAPABILITY_ID,
        "OWNER": OWNER,
        "DASHBOARD_AUTHORITY": False,
        "DASHBOARD_ROLE": "READ_ONLY_CONSUMER",
        "SELECTION_AUTHORITY_ADDED": True,
        "SINGLE_SELECTED_FUTURE": True,
        "SELECTED_FUTURE_COUNT": SELECTED_FUTURE_COUNT,
        "MAX_POSITIONS_EFFECTIVE": MAX_POSITIONS_EFFECTIVE,
        "MULTI_FUTURE_RUNTIME_AUTHORIZED": False,
        "ALPHA_AUTHORITY_ADDED": False,
        "EXECUTION_AUTHORITY_ADDED": False,
        "TOP_N_ACTIVE_SET_AUTHORITY": False,
        "ALLOWLIST_SELECTION_AUTHORITY": False,
        "LEGACY_PARALLEL_AUTHORITY_ABSENT": True,
        "ALPHA_ALLOWED": ALPHA_ALLOWED_DEFAULT,
        "VENUE": VENUE,
        "SCHEMA_VERSION": SCHEMA_VERSION,
        "PRODUCER_VERSION": PRODUCER_VERSION,
        "SELECTION_POLICY_ID": SELECTION_POLICY_ID,
        "SELECTION_POLICY_VERSION": SELECTION_POLICY_VERSION,
        "MANUAL_OVERRIDE_ALLOWED": False,
        "CORE_LOGIC_CHANGE": False,
        "RUNTIME_ACTIVATION_ALLOWED": False,
    }


def compute_config_digest_v1(
    *,
    repository_sha: str,
    max_ranking_age_seconds: float = DEFAULT_MAX_RANKING_AGE_SECONDS,
    refresh_cadence_seconds: float = DEFAULT_REFRESH_CADENCE_SECONDS,
    min_holding_period_seconds: float = DEFAULT_MIN_HOLDING_PERIOD_SECONDS,
    hysteresis_rank_improvement: int = DEFAULT_HYSTERESIS_RANK_IMPROVEMENT,
    min_history_samples: int = DEFAULT_MIN_HISTORY_SAMPLES,
    min_data_quality_status: str = DEFAULT_MIN_DATA_QUALITY_STATUS,
    venue: str = VENUE,
) -> str:
    payload = {
        "capability_id": CAPABILITY_ID,
        "schema_version": SCHEMA_VERSION,
        "producer_version": PRODUCER_VERSION,
        "selection_policy_id": SELECTION_POLICY_ID,
        "selection_policy_version": SELECTION_POLICY_VERSION,
        "venue": venue,
        "max_ranking_age_seconds": float(max_ranking_age_seconds),
        "refresh_cadence_seconds": float(refresh_cadence_seconds),
        "min_holding_period_seconds": float(min_holding_period_seconds),
        "hysteresis_rank_improvement": int(hysteresis_rank_improvement),
        "min_history_samples": int(min_history_samples),
        "min_data_quality_status": str(min_data_quality_status),
        "selected_future_count": SELECTED_FUTURE_COUNT,
        "max_positions_effective": MAX_POSITIONS_EFFECTIVE,
        "single_selected_future": True,
        "multi_future_runtime_authorized": False,
        "dashboard_authority": False,
        "manual_override_allowed": False,
        "alpha_allowed": ALPHA_ALLOWED_DEFAULT,
        "repository_sha": repository_sha,
    }
    return sha256_hex(canonical_json_dumps(payload))


def compute_selection_id_v1(
    *,
    ranking_snapshot_id: str,
    ranking_integrity_digest: str,
    instrument_id: str,
    config_digest: str,
    repository_sha: str,
    state: str,
) -> str:
    material = "|".join(
        [
            CAPABILITY_ID,
            SELECTION_POLICY_ID,
            SELECTION_POLICY_VERSION,
            PRODUCER_VERSION,
            ranking_snapshot_id,
            ranking_integrity_digest,
            instrument_id or "NONE",
            state,
            config_digest,
            repository_sha,
        ]
    )
    return f"ssf_{sha256_hex(material)[:24]}"


def compute_selection_input_digest_v1(
    *,
    ranking_snapshot_id: str,
    ranking_integrity_digest: str,
    ranking_event_time: str,
    config_digest: str,
    open_position_instrument_id: str,
    instrument_status_overlay: Mapping[str, Any] | None,
) -> str:
    payload = {
        "ranking_snapshot_id": ranking_snapshot_id,
        "ranking_integrity_digest": ranking_integrity_digest,
        "ranking_event_time": ranking_event_time,
        "config_digest": config_digest,
        "open_position_instrument_id": open_position_instrument_id or "",
        "instrument_status_overlay": dict(instrument_status_overlay or {}),
    }
    return sha256_hex(canonical_json_dumps(payload))
