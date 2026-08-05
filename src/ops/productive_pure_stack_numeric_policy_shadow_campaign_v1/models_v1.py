"""Immutable models for Stage-2 numeric policy shadow campaign v1."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any, Mapping, Optional, Sequence, Tuple


class CampaignStateV1(str, Enum):
    DECLARED = "DECLARED"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETE = "COMPLETE"
    REJECTED = "REJECTED"


class ShadowAvailabilityV1(str, Enum):
    AVAILABLE = "AVAILABLE"
    UNAVAILABLE = "UNAVAILABLE"
    REJECTED = "REJECTED"


class ShadowProducerKindV1(str, Enum):
    STAGE1_FORMULA_SHADOW = "STAGE1_FORMULA_SHADOW"
    SEQUENCE_METRICS_SHADOW = "SEQUENCE_METRICS_SHADOW"
    SURVIVAL_ENVELOPE_ASSEMBLER_SHADOW = "SURVIVAL_ENVELOPE_ASSEMBLER_SHADOW"
    FRESHNESS_AGE_COLLECTOR_SHADOW = "FRESHNESS_AGE_COLLECTOR_SHADOW"


@dataclass(frozen=True)
class FinalizedBarV1:
    """Point-in-time finalized PT1M bar. Event-time only; no wallclock market surrogate."""

    instrument_id: str
    event_time_epoch_s: int
    open: float
    high: float
    low: float
    close: float
    mark_price: float
    volume: float
    finalized: bool
    dataset_id: str
    source_id: str


@dataclass(frozen=True)
class ShadowFormulaObservationV1:
    formula_id: str
    status: ShadowAvailabilityV1
    value: Optional[float]
    unit: str
    provisional: bool
    productive_activation: bool
    rejection_reason: Optional[str]
    input_digest: str
    observation_event_time_epoch_s: Optional[int]
    notes: Tuple[str, ...] = ()


@dataclass(frozen=True)
class ShadowSequenceMetricsObservationV1:
    definition_id: str
    status: ShadowAvailabilityV1
    provisional: bool
    productive_activation: bool
    path_survival_ratio: Optional[float]
    early_loss_toxicity: Optional[float]
    margin_buffer_at_risk_99: Optional[float]
    sequence_fragility_index: Optional[float]
    liquidation_near_miss_rate: Optional[float]
    governance_breach_frequency: Optional[float]
    chop_switch_survival_score: Optional[float]
    rejection_reason: Optional[str]
    input_digest: str
    notes: Tuple[str, ...] = ()


@dataclass(frozen=True)
class FreshnessAgeObservationV1:
    instrument_id: str
    status: ShadowAvailabilityV1
    age_seconds: Optional[int]
    bar_event_time_epoch_s: Optional[int]
    as_of_event_time_epoch_s: Optional[int]
    provisional: bool
    productive_activation: bool
    rejection_reason: Optional[str]
    input_digest: str
    notes: Tuple[str, ...] = ()


@dataclass(frozen=True)
class ReproducibilityRecordV1:
    git_sha: str
    config_digest: str
    stage1_manifest_digest: str
    calibration_protocol_digest: str
    dataset_id: str
    instrument_id: str
    scenario_id: str
    seed: int
    event_time_epoch_s: int
    wall_time_utc: str
    sole_trading_authority: str
    observation_pack_digest: Optional[str] = None


@dataclass(frozen=True)
class EmptyCapableManifestV1:
    status: str  # EMPTY_SCAFFOLD | DECLARED | COMPLETE
    populated: bool
    entries: Tuple[Mapping[str, Any], ...] = ()
    digest: Optional[str] = None
    notes: Optional[str] = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "populated": self.populated,
            "entries": [dict(e) for e in self.entries],
            "digest": self.digest,
            "notes": self.notes,
        }


@dataclass(frozen=True)
class ShadowCampaignRequestV1:
    campaign_id: str
    origin_main_sha: str
    repo_root: str
    output_root: str
    reproducibility: ReproducibilityRecordV1
    observation_bars: Tuple[FinalizedBarV1, ...] = ()
    best_bid: Optional[float] = None
    best_ask: Optional[float] = None
    recent_abs_log_return: Optional[float] = None
    fee_bps: Optional[float] = None
    slippage_bps: Optional[float] = None
    path_above_barrier: Optional[Tuple[bool, ...]] = None
    sequence_metric_inputs: Optional[Mapping[str, Optional[float]]] = None
    layer_metric_inputs: Optional[Mapping[str, Optional[float]]] = None
    dataset_manifest: EmptyCapableManifestV1 = field(
        default_factory=lambda: EmptyCapableManifestV1(
            status="EMPTY_SCAFFOLD",
            populated=False,
            notes="Shadow campaign declared; dataset not populated",
        )
    )
    train_calibration_validation_partition_manifest: EmptyCapableManifestV1 = field(
        default_factory=lambda: EmptyCapableManifestV1(
            status="EMPTY_SCAFFOLD",
            populated=False,
            notes="Train/calibration/validation partitions not populated",
        )
    )
    walk_forward_manifest: EmptyCapableManifestV1 = field(
        default_factory=lambda: EmptyCapableManifestV1(
            status="EMPTY_SCAFFOLD",
            populated=False,
            notes="Walk-forward folds not populated",
        )
    )
    bootstrap_monte_carlo_manifest: EmptyCapableManifestV1 = field(
        default_factory=lambda: EmptyCapableManifestV1(
            status="EMPTY_SCAFFOLD",
            populated=False,
            notes="Bootstrap/Monte-Carlo not populated",
        )
    )
    stress_pack_manifest: EmptyCapableManifestV1 = field(
        default_factory=lambda: EmptyCapableManifestV1(
            status="EMPTY_SCAFFOLD",
            populated=False,
            notes="Stress packs not populated",
        )
    )
    force_reject_reasons: Tuple[str, ...] = ()
    allow_overwrite: bool = False


@dataclass(frozen=True)
class ShadowCampaignResultV1:
    campaign_id: str
    campaign_state: CampaignStateV1
    pack_campaign_status: str
    evidence_complete: bool
    owner_ratified: bool
    productive_numeric_values_set: int
    input_authority: bool
    runtime_implemented: bool
    productive_activation: bool
    sole_trading_authority: str
    output_dir: str
    evidence_pack_path: str
    pack_digest: str
    rejection_reasons: Tuple[str, ...]
    token_count: int
    shadow_observations: Mapping[str, Any] = field(default_factory=dict)
    data_collection_groups_only: Mapping[str, Sequence[str]] = field(default_factory=dict)
    mechanical_couplings: Mapping[str, str] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["campaign_state"] = self.campaign_state.value
        return payload
