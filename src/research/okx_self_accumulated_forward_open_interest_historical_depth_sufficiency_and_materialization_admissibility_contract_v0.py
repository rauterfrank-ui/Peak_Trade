"""Self-accumulated forward OI historical depth sufficiency and materialization admissibility v0.

Offline-only fail-closed contract bridging self-accumulated archive accrual to panel
materialization admissibility. Reuses archive, integrity audit, coverage/freshness, and
PIT semantics owners. Does NOT treat the fixed-2024 public-fetch horizon as the
self-accumulated admissibility target. Research-only; no runtime authority.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Mapping, Sequence

from src.research.cross_sectional_open_interest_delta_rank_v0_capability_gap_registration_and_scope_parking_v0 import (
    RESEARCH_SCOPE,
)
from src.research.cross_sectional_open_interest_delta_rank_v0_pit_semantics_contract_v0 import (
    BAR_INTERVAL,
    LOOKBACK_K,
    SIGNAL_LAG_BARS,
    STALE_THRESHOLD_BARS,
)
from src.research.okx_self_accumulated_forward_open_interest_archive_integrity_audit_v0 import (
    MIN_OBSERVATIONS_FOR_SUFFICIENT_DATA,
    ArchiveIntegrityAuditStatus,
    audit_archive_snapshot_v0,
)
from src.research.okx_self_accumulated_forward_open_interest_archive_v0 import (
    BAR_INTERVAL_MS,
    ForwardOpenInterestObservationV0,
    GapStalenessStatus,
    InstrumentArchiveStateV0,
    assess_gap_and_staleness_v0,
    load_effective_archive_states_from_snapshot_v0,
    observation_from_row_dict_v0,
    serialize_canonical_json,
)
from src.research.okx_self_accumulated_forward_open_interest_coverage_freshness_report_v0 import (
    FreshnessStatus,
    generate_coverage_freshness_report_v0,
)
from src.research.pit_okx_pt1h_panel_ohlcv_dataset_v1 import (
    PanelValidationErrorCode,
    validate_panel_series_v1,
)

PACKAGE_MARKER = (
    "OKX_SELF_ACCUMULATED_FORWARD_OPEN_INTEREST_HISTORICAL_DEPTH_SUFFICIENCY_"
    "AND_MATERIALIZATION_ADMISSIBILITY_CONTRACT_V0=true"
)
MODULE_VERSION = (
    "okx_self_accumulated_forward_open_interest_historical_depth_sufficiency_"
    "and_materialization_admissibility.v0"
)
CONFIRM_GO = (
    "GO_OKX_SELF_ACCUMULATED_FORWARD_OPEN_INTEREST_HISTORICAL_DEPTH_SUFFICIENCY_"
    "AND_MATERIALIZATION_ADMISSIBILITY_CONTRACT_V0"
)
CONFIG_REL_PATH = (
    "config/research/"
    "okx_self_accumulated_forward_open_interest_historical_depth_sufficiency_"
    "and_materialization_admissibility_contract_v0.json"
)

AUTHORITY_EFFECT = "NONE"
RUNTIME_EFFECT = "NONE"

BRIDGE_KIND = "SELF_ACCUMULATED_FORWARD_ACCRUAL_BRIDGE_V0"
BRIDGE_MODE = "ARCHIVE_ACCRUAL_TAIL_CONTIGUOUS_V0"
EXCLUDED_HORIZON_OWNER = "okx_historical_open_interest_public_fetch_v0"
EXCLUDED_HORIZON_SYMBOLS = ("START_INCLUSIVE_UTC", "END_EXCLUSIVE_UTC")
MATERIALIZER_OWNER = (
    "cross_sectional_open_interest_delta_rank_v0_bound_panel_dataset_materialization_v0"
)

MATERIALIZATION_STATUS_DEFERRED = "DEFERRED_INSUFFICIENT_HISTORY"
MATERIALIZATION_STATUS_READY = "READY_FOR_SELF_ACCUMULATED_PANEL_MATERIALIZATION"

NEXT_CANONICAL_SCOPE_AFTER_SUFFICIENCY = (
    "CORE_SYSTEM_DEVELOPMENT_SELF_ACCUMULATED_OI_BOUND_PANEL_DATASET_MATERIALIZATION_V0"
)
COLLECTION_CONTINUE_SCOPE = (
    "CORE_SYSTEM_DEVELOPMENT_CONTINUE_LIVE_OI_SELF_ACCUMULATED_FORWARD_COLLECTION_V0"
)

# Explicit versioned policy inputs with fail-closed safe defaults.
# required_contiguous_bars derived from existing PIT semantics (lookback + lag + 1 decision bar).
REQUIRED_CONTIGUOUS_BARS = LOOKBACK_K + SIGNAL_LAG_BARS + 1
# For PT1H contiguous bars, earliest-to-latest span hours = bar_count - 1.
REQUIRED_HISTORY_DURATION_HOURS = max(REQUIRED_CONTIGUOUS_BARS - 1, 1)
MINIMUM_INSTRUMENT_COUNT = 5
MAXIMUM_ALLOWED_GAP_BARS = 0
MINIMUM_OBSERVATIONS_PER_INSTRUMENT = MIN_OBSERVATIONS_FOR_SUFFICIENT_DATA
REQUIRED_OBSERVATION_COUNT = REQUIRED_CONTIGUOUS_BARS * MINIMUM_INSTRUMENT_COUNT


class AdmissibilityReason(str, Enum):
    ARCHIVE_INTEGRITY_FAIL = "ARCHIVE_INTEGRITY_FAIL"
    INSUFFICIENT_OBSERVATION_COUNT = "INSUFFICIENT_OBSERVATION_COUNT"
    INSUFFICIENT_CONTIGUOUS_TAIL_BARS = "INSUFFICIENT_CONTIGUOUS_TAIL_BARS"
    INSUFFICIENT_HISTORY_DURATION = "INSUFFICIENT_HISTORY_DURATION"
    INSUFFICIENT_INSTRUMENT_COUNT = "INSUFFICIENT_INSTRUMENT_COUNT"
    GAP_EXCEEDS_MAXIMUM_ALLOWED = "GAP_EXCEEDS_MAXIMUM_ALLOWED"
    STALE_FRESHNESS = "STALE_FRESHNESS"
    PER_INSTRUMENT_OBSERVATION_COUNT_BELOW_MINIMUM = (
        "PER_INSTRUMENT_OBSERVATION_COUNT_BELOW_MINIMUM"
    )
    HISTORICAL_DEPTH_INSUFFICIENT = "HISTORICAL_DEPTH_INSUFFICIENT"
    FIXED_2024_PUBLIC_FETCH_HORIZON_NOT_APPLICABLE = (
        "FIXED_2024_PUBLIC_FETCH_HORIZON_NOT_APPLICABLE"
    )
    SELF_ACCUMULATED_BRIDGE_SATISFIED = "SELF_ACCUMULATED_BRIDGE_SATISFIED"


@dataclass(frozen=True)
class SufficiencyPolicyV0:
    required_contiguous_bars: int
    required_history_duration_hours: int
    minimum_instrument_count: int
    maximum_allowed_gap_bars: int
    minimum_observations_per_instrument: int
    required_observation_count: int


@dataclass(frozen=True)
class InstrumentContinuityMetricsV0:
    instrument_id: str
    observation_count: int
    contiguous_tail_bars: int
    max_internal_gap_bars: int
    effective_history_duration_hours: float


@dataclass(frozen=True)
class MaterializationAdmissibilityAssessmentV0:
    schema_version: str
    archive_root: str
    as_of_utc: str
    policy: SufficiencyPolicyV0
    required_observation_count: int
    required_history_duration_hours: int
    required_contiguous_bars: int
    minimum_instrument_count: int
    maximum_allowed_gap_bars: int
    current_observation_count: int
    current_effective_history_duration_hours: float
    current_contiguous_tail_bars: int
    current_instrument_count: int
    historical_depth_sufficient: bool
    continuity_sufficient: bool
    instrument_coverage_sufficient: bool
    sample_sufficiency_met: bool
    dataset_materialization_allowed: bool
    materialization_status: str
    collection_continue_required: bool
    collection_termination_condition: bool
    earliest_possible_materialization_utc: str | None
    next_canonical_scope: str | None
    bridge_kind: str
    bridge_mode: str
    excluded_horizon_owner: str
    materializer_owner: str
    reason_codes: tuple[str, ...]
    per_instrument_metrics: tuple[InstrumentContinuityMetricsV0, ...]
    authority_effect: str = AUTHORITY_EFFECT
    runtime_effect: str = RUNTIME_EFFECT


def default_sufficiency_policy_v0() -> SufficiencyPolicyV0:
    return SufficiencyPolicyV0(
        required_contiguous_bars=REQUIRED_CONTIGUOUS_BARS,
        required_history_duration_hours=REQUIRED_HISTORY_DURATION_HOURS,
        minimum_instrument_count=MINIMUM_INSTRUMENT_COUNT,
        maximum_allowed_gap_bars=MAXIMUM_ALLOWED_GAP_BARS,
        minimum_observations_per_instrument=MINIMUM_OBSERVATIONS_PER_INSTRUMENT,
        required_observation_count=REQUIRED_OBSERVATION_COUNT,
    )


def build_bridge_contract_v0() -> dict[str, Any]:
    return {
        "schema_version": MODULE_VERSION,
        "bridge_kind": BRIDGE_KIND,
        "bridge_mode": BRIDGE_MODE,
        "research_scope": RESEARCH_SCOPE,
        "excluded_horizon_owner": EXCLUDED_HORIZON_OWNER,
        "excluded_horizon_symbols": list(EXCLUDED_HORIZON_SYMBOLS),
        "excluded_horizon_note": (
            "Fixed 2024 public-fetch START_INCLUSIVE_UTC/END_EXCLUSIVE_UTC horizon is "
            "explicitly NOT the self-accumulated forward accrual admissibility target."
        ),
        "materializer_owner": MATERIALIZER_OWNER,
        "materializer_entry_point": (
            "scripts/ops/materialize_cross_sectional_open_interest_delta_rank_v0_"
            "bound_panel_open_interest_dataset_v0.py"
        ),
        "self_accumulated_admissibility_target": "ARCHIVE_ACCRUAL_TAIL_CONTIGUOUS_V0",
        "historical_backfill_allowed": False,
        "authority_effect": AUTHORITY_EFFECT,
        "runtime_effect": RUNTIME_EFFECT,
    }


def build_sufficiency_policy_config_v0() -> dict[str, Any]:
    policy = default_sufficiency_policy_v0()
    return {
        "schema_version": MODULE_VERSION,
        "policy_version": "v0",
        "research_scope": RESEARCH_SCOPE,
        "required_contiguous_bars": policy.required_contiguous_bars,
        "required_history_duration_hours": policy.required_history_duration_hours,
        "minimum_instrument_count": policy.minimum_instrument_count,
        "maximum_allowed_gap_bars": policy.maximum_allowed_gap_bars,
        "minimum_observations_per_instrument": policy.minimum_observations_per_instrument,
        "required_observation_count": policy.required_observation_count,
        "derivation_notes": {
            "required_contiguous_bars": "LOOKBACK_K + SIGNAL_LAG_BARS + 1 from PIT semantics owner",
            "minimum_instrument_count": "validate_panel_series_v1 default min_instruments=5",
            "maximum_allowed_gap_bars": "fail-closed safe default 0; gaps are never silently ignored",
            "required_observation_count": "required_contiguous_bars * minimum_instrument_count",
            "required_history_duration_hours": "max(required_contiguous_bars - 1, 1) span hours for PT1H bars",
        },
        "pit_semantics_refs": {
            "lookback_k": LOOKBACK_K,
            "signal_lag_bars": SIGNAL_LAG_BARS,
            "bar_interval": BAR_INTERVAL,
            "stale_threshold_bars": STALE_THRESHOLD_BARS,
        },
        "authority_effect": AUTHORITY_EFFECT,
        "runtime_effect": RUNTIME_EFFECT,
    }


def build_gap_and_continuity_contract_v0() -> dict[str, Any]:
    return {
        "schema_version": MODULE_VERSION,
        "gap_detection_owner": "okx_self_accumulated_forward_open_interest_archive_v0",
        "gap_detection_function": "assess_gap_and_staleness_v0",
        "gap_rule": "delta_ms > BAR_INTERVAL_MS => GapStalenessStatus.GAP",
        "maximum_allowed_gap_bars": MAXIMUM_ALLOWED_GAP_BARS,
        "continuity_sufficient_rule": (
            "all instruments: max_internal_gap_bars <= maximum_allowed_gap_bars AND "
            "contiguous_tail_bars >= required_contiguous_bars"
        ),
        "historical_backfill_allowed": False,
        "gap_repair_via_backfill_allowed": False,
        "silent_gap_ignore_allowed": False,
        "authority_effect": AUTHORITY_EFFECT,
        "runtime_effect": RUNTIME_EFFECT,
    }


def build_collection_termination_contract_v0() -> dict[str, Any]:
    return {
        "schema_version": MODULE_VERSION,
        "collection_continue_scope": COLLECTION_CONTINUE_SCOPE,
        "collection_termination_condition": (
            "historical_depth_sufficient AND dataset_materialization_allowed AND "
            f"materialization_status == {MATERIALIZATION_STATUS_READY!r}"
        ),
        "collection_continue_required_rule": "NOT collection_termination_condition",
        "next_canonical_scope_after_sufficiency": NEXT_CANONICAL_SCOPE_AFTER_SUFFICIENCY,
        "next_canonical_scope_rule": (
            "set only when collection_termination_condition is True; otherwise None"
        ),
        "authority_effect": AUTHORITY_EFFECT,
        "runtime_effect": RUNTIME_EFFECT,
    }


def compute_implementation_digest_v0() -> str:
    return hashlib.sha256(
        serialize_canonical_json(
            {
                "module": MODULE_VERSION,
                "confirm_go": CONFIRM_GO,
                "bridge_kind": BRIDGE_KIND,
                "policy": build_sufficiency_policy_config_v0(),
                "bridge": build_bridge_contract_v0(),
            }
        ).encode("utf-8")
    ).hexdigest()


def build_contract_config_v0() -> dict[str, Any]:
    return {
        "schema_version": MODULE_VERSION,
        "go_token": CONFIRM_GO,
        "research_scope": RESEARCH_SCOPE,
        "bridge_contract": build_bridge_contract_v0(),
        "sufficiency_policy": build_sufficiency_policy_config_v0(),
        "gap_and_continuity_contract": build_gap_and_continuity_contract_v0(),
        "collection_termination_contract": build_collection_termination_contract_v0(),
        "default_enabled": False,
        "operator_go_required": True,
        "offline_only": True,
        "no_network_collection": True,
        "no_dataset_materialization": True,
        "no_economic_evaluation": True,
        "authority_effect": AUTHORITY_EFFECT,
        "runtime_effect": RUNTIME_EFFECT,
        "implementation_digest": compute_implementation_digest_v0(),
    }


def _parse_utc_ms(value: str) -> int:
    dt = datetime.strptime(value, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
    return int(dt.timestamp() * 1000)


def _format_utc_ms(ms: int) -> str:
    return datetime.fromtimestamp(ms / 1000, tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _gap_bars_between(prior_ms: int, current_ms: int) -> int:
    delta_ms = current_ms - prior_ms
    if delta_ms <= BAR_INTERVAL_MS:
        return 0
    return (delta_ms // BAR_INTERVAL_MS) - 1


def compute_contiguous_tail_bars(
    observations: Sequence[ForwardOpenInterestObservationV0],
) -> int:
    if not observations:
        return 0
    sorted_obs = sorted(observations, key=lambda o: o.venue_timestamp_ms)
    tail = 1
    for index in range(len(sorted_obs) - 2, -1, -1):
        if (
            _gap_bars_between(
                sorted_obs[index].venue_timestamp_ms,
                sorted_obs[index + 1].venue_timestamp_ms,
            )
            == 0
        ):
            tail += 1
        else:
            break
    return tail


def compute_max_internal_gap_bars(
    observations: Sequence[ForwardOpenInterestObservationV0],
) -> int:
    if len(observations) < 2:
        return 0
    sorted_obs = sorted(observations, key=lambda o: o.venue_timestamp_ms)
    max_gap = 0
    for index in range(1, len(sorted_obs)):
        max_gap = max(
            max_gap,
            _gap_bars_between(
                sorted_obs[index - 1].venue_timestamp_ms,
                sorted_obs[index].venue_timestamp_ms,
            ),
        )
    return max_gap


def compute_instrument_continuity_metrics_v0(
    state: InstrumentArchiveStateV0,
) -> InstrumentContinuityMetricsV0:
    observations = tuple(state.observations)
    if not observations:
        return InstrumentContinuityMetricsV0(
            instrument_id=state.instrument_id,
            observation_count=0,
            contiguous_tail_bars=0,
            max_internal_gap_bars=0,
            effective_history_duration_hours=0.0,
        )
    sorted_obs = sorted(observations, key=lambda o: o.venue_timestamp_ms)
    earliest_ms = sorted_obs[0].venue_timestamp_ms
    latest_ms = sorted_obs[-1].venue_timestamp_ms
    return InstrumentContinuityMetricsV0(
        instrument_id=state.instrument_id,
        observation_count=len(sorted_obs),
        contiguous_tail_bars=compute_contiguous_tail_bars(sorted_obs),
        max_internal_gap_bars=compute_max_internal_gap_bars(sorted_obs),
        effective_history_duration_hours=(latest_ms - earliest_ms) / 3_600_000,
    )


def _load_archive_states_v0(snapshot_dir: Path) -> list[InstrumentArchiveStateV0]:
    return load_effective_archive_states_from_snapshot_v0(snapshot_dir)


def _aggregate_archive_metrics(
    metrics: Sequence[InstrumentContinuityMetricsV0],
) -> tuple[int, float, int]:
    if not metrics:
        return 0, 0.0, 0
    total_obs = sum(item.observation_count for item in metrics)
    min_tail = min(item.contiguous_tail_bars for item in metrics)
    max_duration = max(item.effective_history_duration_hours for item in metrics)
    return total_obs, max_duration, min_tail


def _continuity_sufficient(
    metrics: Sequence[InstrumentContinuityMetricsV0],
    *,
    policy: SufficiencyPolicyV0,
) -> bool:
    if not metrics:
        return False
    return all(
        item.max_internal_gap_bars <= policy.maximum_allowed_gap_bars
        and item.contiguous_tail_bars >= policy.required_contiguous_bars
        for item in metrics
    )


def _instrument_coverage_sufficient(
    metrics: Sequence[InstrumentContinuityMetricsV0],
    *,
    policy: SufficiencyPolicyV0,
) -> bool:
    return len(metrics) >= policy.minimum_instrument_count


def _sample_sufficiency_met(
    metrics: Sequence[InstrumentContinuityMetricsV0],
    *,
    policy: SufficiencyPolicyV0,
) -> bool:
    if not metrics:
        return False
    if sum(item.observation_count for item in metrics) < policy.required_observation_count:
        return False
    return all(
        item.observation_count >= policy.minimum_observations_per_instrument for item in metrics
    )


def _historical_depth_sufficient(
    *,
    continuity_sufficient: bool,
    instrument_coverage_sufficient: bool,
    sample_sufficiency_met: bool,
    current_effective_history_duration_hours: float,
    current_contiguous_tail_bars: int,
    policy: SufficiencyPolicyV0,
) -> bool:
    return (
        continuity_sufficient
        and instrument_coverage_sufficient
        and sample_sufficiency_met
        and current_effective_history_duration_hours >= policy.required_history_duration_hours
        and current_contiguous_tail_bars >= policy.required_contiguous_bars
    )


def assess_materialization_admissibility_from_states_v0(
    *,
    states: Sequence[InstrumentArchiveStateV0],
    archive_root: str,
    as_of_utc: str,
    integrity_status: ArchiveIntegrityAuditStatus,
    freshness_status: str,
    policy: SufficiencyPolicyV0 | None = None,
) -> MaterializationAdmissibilityAssessmentV0:
    """Deterministic fail-closed admissibility assessment from loaded archive states."""
    policy = policy or default_sufficiency_policy_v0()
    per_instrument = tuple(compute_instrument_continuity_metrics_v0(state) for state in states)
    (
        current_observation_count,
        current_effective_history_duration_hours,
        current_contiguous_tail_bars,
    ) = _aggregate_archive_metrics(per_instrument)
    current_instrument_count = len(per_instrument)

    continuity_sufficient = _continuity_sufficient(per_instrument, policy=policy)
    instrument_coverage_sufficient = _instrument_coverage_sufficient(per_instrument, policy=policy)
    sample_sufficiency_met = _sample_sufficiency_met(per_instrument, policy=policy)

    historical_depth_sufficient = _historical_depth_sufficient(
        continuity_sufficient=continuity_sufficient,
        instrument_coverage_sufficient=instrument_coverage_sufficient,
        sample_sufficiency_met=sample_sufficiency_met,
        current_effective_history_duration_hours=current_effective_history_duration_hours,
        current_contiguous_tail_bars=current_contiguous_tail_bars,
        policy=policy,
    )

    reason_codes: list[str] = [
        AdmissibilityReason.FIXED_2024_PUBLIC_FETCH_HORIZON_NOT_APPLICABLE.value
    ]
    if integrity_status is not ArchiveIntegrityAuditStatus.PASS:
        reason_codes.append(AdmissibilityReason.ARCHIVE_INTEGRITY_FAIL.value)
    if current_observation_count < policy.required_observation_count:
        reason_codes.append(AdmissibilityReason.INSUFFICIENT_OBSERVATION_COUNT.value)
    if current_contiguous_tail_bars < policy.required_contiguous_bars:
        reason_codes.append(AdmissibilityReason.INSUFFICIENT_CONTIGUOUS_TAIL_BARS.value)
    if current_effective_history_duration_hours < policy.required_history_duration_hours:
        reason_codes.append(AdmissibilityReason.INSUFFICIENT_HISTORY_DURATION.value)
    if current_instrument_count < policy.minimum_instrument_count:
        reason_codes.append(AdmissibilityReason.INSUFFICIENT_INSTRUMENT_COUNT.value)
    if not continuity_sufficient:
        if any(
            item.max_internal_gap_bars > policy.maximum_allowed_gap_bars for item in per_instrument
        ):
            reason_codes.append(AdmissibilityReason.GAP_EXCEEDS_MAXIMUM_ALLOWED.value)
        else:
            reason_codes.append(AdmissibilityReason.INSUFFICIENT_CONTIGUOUS_TAIL_BARS.value)
    if any(
        item.observation_count < policy.minimum_observations_per_instrument
        for item in per_instrument
    ):
        reason_codes.append(
            AdmissibilityReason.PER_INSTRUMENT_OBSERVATION_COUNT_BELOW_MINIMUM.value
        )
    if freshness_status == FreshnessStatus.STALE.value:
        reason_codes.append(AdmissibilityReason.STALE_FRESHNESS.value)
    if not historical_depth_sufficient:
        reason_codes.append(AdmissibilityReason.HISTORICAL_DEPTH_INSUFFICIENT.value)

    dataset_materialization_allowed = (
        historical_depth_sufficient
        and integrity_status is ArchiveIntegrityAuditStatus.PASS
        and freshness_status != FreshnessStatus.STALE.value
    )
    materialization_status = (
        MATERIALIZATION_STATUS_READY
        if dataset_materialization_allowed
        else MATERIALIZATION_STATUS_DEFERRED
    )
    collection_termination_condition = dataset_materialization_allowed
    collection_continue_required = not collection_termination_condition
    next_canonical_scope = (
        NEXT_CANONICAL_SCOPE_AFTER_SUFFICIENCY if collection_termination_condition else None
    )
    earliest_possible_materialization_utc: str | None = None
    if per_instrument and all(
        item.contiguous_tail_bars >= policy.required_contiguous_bars for item in per_instrument
    ):
        latest_ms = max(
            sorted(state.observations, key=lambda o: o.venue_timestamp_ms)[-1].venue_timestamp_ms
            for state in states
            if state.observations
        )
        earliest_needed_ms = latest_ms - (policy.required_contiguous_bars - 1) * BAR_INTERVAL_MS
        earliest_possible_materialization_utc = _format_utc_ms(earliest_needed_ms)

    if dataset_materialization_allowed:
        reason_codes.append(AdmissibilityReason.SELF_ACCUMULATED_BRIDGE_SATISFIED.value)

    return MaterializationAdmissibilityAssessmentV0(
        schema_version=MODULE_VERSION,
        archive_root=archive_root,
        as_of_utc=as_of_utc,
        policy=policy,
        required_observation_count=policy.required_observation_count,
        required_history_duration_hours=policy.required_history_duration_hours,
        required_contiguous_bars=policy.required_contiguous_bars,
        minimum_instrument_count=policy.minimum_instrument_count,
        maximum_allowed_gap_bars=policy.maximum_allowed_gap_bars,
        current_observation_count=current_observation_count,
        current_effective_history_duration_hours=current_effective_history_duration_hours,
        current_contiguous_tail_bars=current_contiguous_tail_bars,
        current_instrument_count=current_instrument_count,
        historical_depth_sufficient=historical_depth_sufficient,
        continuity_sufficient=continuity_sufficient,
        instrument_coverage_sufficient=instrument_coverage_sufficient,
        sample_sufficiency_met=sample_sufficiency_met,
        dataset_materialization_allowed=dataset_materialization_allowed,
        materialization_status=materialization_status,
        collection_continue_required=collection_continue_required,
        collection_termination_condition=collection_termination_condition,
        earliest_possible_materialization_utc=earliest_possible_materialization_utc,
        next_canonical_scope=next_canonical_scope,
        bridge_kind=BRIDGE_KIND,
        bridge_mode=BRIDGE_MODE,
        excluded_horizon_owner=EXCLUDED_HORIZON_OWNER,
        materializer_owner=MATERIALIZER_OWNER,
        reason_codes=tuple(dict.fromkeys(reason_codes)),
        per_instrument_metrics=per_instrument,
    )


def assess_materialization_admissibility_v0(
    *,
    archive_root: Path,
    as_of_utc: str,
    policy: SufficiencyPolicyV0 | None = None,
) -> MaterializationAdmissibilityAssessmentV0:
    """Offline assessment over one archive snapshot directory."""
    audit = audit_archive_snapshot_v0(snapshot_dir=archive_root)
    coverage = generate_coverage_freshness_report_v0(
        archive_root=archive_root,
        as_of_utc=as_of_utc,
    )
    states = _load_archive_states_v0(archive_root)
    return assess_materialization_admissibility_from_states_v0(
        states=states,
        archive_root=str(archive_root),
        as_of_utc=as_of_utc,
        integrity_status=audit.status,
        freshness_status=coverage.freshness_status,
        policy=policy,
    )


def assessment_to_dict_v0(
    assessment: MaterializationAdmissibilityAssessmentV0,
) -> dict[str, Any]:
    return {
        "schema_version": assessment.schema_version,
        "archive_root": assessment.archive_root,
        "as_of_utc": assessment.as_of_utc,
        "required_observation_count": assessment.required_observation_count,
        "required_history_duration_hours": assessment.required_history_duration_hours,
        "required_contiguous_bars": assessment.required_contiguous_bars,
        "minimum_instrument_count": assessment.minimum_instrument_count,
        "maximum_allowed_gap_bars": assessment.maximum_allowed_gap_bars,
        "current_observation_count": assessment.current_observation_count,
        "current_effective_history_duration_hours": assessment.current_effective_history_duration_hours,
        "current_contiguous_tail_bars": assessment.current_contiguous_tail_bars,
        "current_instrument_count": assessment.current_instrument_count,
        "historical_depth_sufficient": assessment.historical_depth_sufficient,
        "continuity_sufficient": assessment.continuity_sufficient,
        "instrument_coverage_sufficient": assessment.instrument_coverage_sufficient,
        "sample_sufficiency_met": assessment.sample_sufficiency_met,
        "dataset_materialization_allowed": assessment.dataset_materialization_allowed,
        "materialization_status": assessment.materialization_status,
        "collection_continue_required": assessment.collection_continue_required,
        "collection_termination_condition": assessment.collection_termination_condition,
        "earliest_possible_materialization_utc": assessment.earliest_possible_materialization_utc,
        "next_canonical_scope": assessment.next_canonical_scope,
        "bridge_kind": assessment.bridge_kind,
        "bridge_mode": assessment.bridge_mode,
        "excluded_horizon_owner": assessment.excluded_horizon_owner,
        "materializer_owner": assessment.materializer_owner,
        "reason_codes": list(assessment.reason_codes),
        "per_instrument_metrics": [
            {
                "instrument_id": item.instrument_id,
                "observation_count": item.observation_count,
                "contiguous_tail_bars": item.contiguous_tail_bars,
                "max_internal_gap_bars": item.max_internal_gap_bars,
                "effective_history_duration_hours": item.effective_history_duration_hours,
            }
            for item in assessment.per_instrument_metrics
        ],
        "authority_effect": assessment.authority_effect,
        "runtime_effect": assessment.runtime_effect,
    }


def panel_minimum_instrument_gate_unchanged_v0(
    instrument_ids: Sequence[str],
) -> bool:
    """Reuse canonical panel validator minimum instrument gate without mutating it."""
    if len(instrument_ids) < MINIMUM_INSTRUMENT_COUNT:
        return False

    class _StubSeries:
        def __init__(self, instrument_id: str) -> None:
            self.instrument_id = instrument_id
            self.bars = ()

    result = validate_panel_series_v1([_StubSeries(i) for i in instrument_ids])
    return PanelValidationErrorCode.INSUFFICIENT_INSTRUMENTS.value not in result.error_codes


def assess_gap_for_observation_pair_v0(
    current: ForwardOpenInterestObservationV0,
    prior: ForwardOpenInterestObservationV0 | None,
) -> GapStalenessStatus:
    return assess_gap_and_staleness_v0(current, prior=prior).status
