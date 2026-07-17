"""Market Dashboard ReadModel contracts v1 — domain snapshot contracts.

Immutable typed consumer contracts. These store producer results only and never
calculate decisions, authority, risk permission, execution permission, or
promotion eligibility. Missing data must use UnavailableSnapshotV1 — never
zero-value fabrication.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any

from src.webui.market_dashboard_readmodels_v1.provenance import (
    DashboardFreshnessStateV1,
    DashboardSnapshotProvenanceV1,
)
from src.webui.market_dashboard_readmodels_v1.validation import (
    MarketDashboardReadModelContractError,
    normalize_blockers,
    normalize_reason_codes,
    require_aware_datetime,
    require_enum,
    require_finite_number,
    require_non_empty_str,
    require_non_negative_int,
    require_non_negative_number,
    require_optional_finite_number,
    require_optional_non_empty_str,
    require_optional_non_negative_number,
    require_optional_sha256_digest,
    require_schema_id,
    require_schema_version,
)

PACKAGE_ID = "market_dashboard_readmodels.v1"
UNAVAILABLE_SCHEMA_ID = "peak_trade.market_dashboard.unavailable_snapshot.v1"
UNAVAILABLE_SCHEMA_VERSION = 1

MARKET_INSTRUMENT_SCHEMA_ID = "peak_trade.market_dashboard.market_instrument_snapshot.v1"
MARKET_RANKING_SCHEMA_ID = "peak_trade.market_dashboard.market_ranking_snapshot.v1"
CANONICAL_DECISION_SCHEMA_ID = "peak_trade.market_dashboard.canonical_decision_summary.v1"
DOUBLE_PLAY_SCHEMA_ID = "peak_trade.market_dashboard.double_play_decision_snapshot.v1"
SAFETY_AUTHORITY_SCHEMA_ID = "peak_trade.market_dashboard.safety_authority_snapshot.v1"
EXECUTION_STATE_SCHEMA_ID = "peak_trade.market_dashboard.execution_state_snapshot.v1"
ECONOMIC_SUMMARY_SCHEMA_ID = "peak_trade.market_dashboard.economic_summary_snapshot.v1"
DIAGNOSTICS_SUMMARY_SCHEMA_ID = "peak_trade.market_dashboard.diagnostics_summary_snapshot.v1"
FRESHNESS_SCHEMA_ID = "peak_trade.market_dashboard.dashboard_freshness_snapshot.v1"
SCHEMA_VERSION_V1 = 1


class DashboardAvailabilityStateV1(str, Enum):
    """Explicit fail-closed availability semantics."""

    AVAILABLE = "AVAILABLE"
    UNAVAILABLE = "UNAVAILABLE"
    NOT_BOUND = "NOT_BOUND"
    MISSING_SOURCE = "MISSING_SOURCE"
    STALE = "STALE"
    MALFORMED_SOURCE = "MALFORMED_SOURCE"


UNAVAILABLE_ALLOWED_STATES = frozenset(
    {
        DashboardAvailabilityStateV1.UNAVAILABLE,
        DashboardAvailabilityStateV1.NOT_BOUND,
        DashboardAvailabilityStateV1.MISSING_SOURCE,
        DashboardAvailabilityStateV1.STALE,
        DashboardAvailabilityStateV1.MALFORMED_SOURCE,
    }
)


class CanonicalDecisionStatusV1(str, Enum):
    """Producer-supplied decision status; unknown must remain explicit."""

    ALLOW = "ALLOW"
    BLOCK = "BLOCK"
    HOLD = "HOLD"
    UNKNOWN = "UNKNOWN"
    NOT_PROVIDED = "NOT_PROVIDED"


class DecisionDirectionV1(str, Enum):
    LONG = "LONG"
    SHORT = "SHORT"
    FLAT = "FLAT"
    UNKNOWN = "UNKNOWN"
    NOT_PROVIDED = "NOT_PROVIDED"


class EligibilityStatusV1(str, Enum):
    ELIGIBLE = "ELIGIBLE"
    INELIGIBLE = "INELIGIBLE"
    UNKNOWN = "UNKNOWN"
    NOT_PROVIDED = "NOT_PROVIDED"


class AuthorityClassificationV1(str, Enum):
    """Unknown must not collapse to blocked/safe."""

    AUTHORIZED = "AUTHORIZED"
    NOT_AUTHORIZED = "NOT_AUTHORIZED"
    UNKNOWN = "UNKNOWN"
    NOT_PROVIDED = "NOT_PROVIDED"


class TriStateV1(str, Enum):
    """Explicit tri-state for kill-switch / gate / permission fields."""

    TRUE = "TRUE"
    FALSE = "FALSE"
    UNKNOWN = "UNKNOWN"
    NOT_PROVIDED = "NOT_PROVIDED"


class OperatingModeV1(str, Enum):
    OFFLINE = "OFFLINE"
    PAPER = "PAPER"
    SHADOW = "SHADOW"
    TESTNET = "TESTNET"
    LIVE = "LIVE"
    UNKNOWN = "UNKNOWN"
    NOT_PROVIDED = "NOT_PROVIDED"


class EconomicGateStatusV1(str, Enum):
    PASS = "PASS"
    FAIL = "FAIL"
    UNKNOWN = "UNKNOWN"
    NOT_PROVIDED = "NOT_PROVIDED"
    DIAGNOSTIC_ONLY = "DIAGNOSTIC_ONLY"


@dataclass(frozen=True)
class UnavailableSnapshotV1:
    """Explicit unavailable / missing-source representation (never a zero domain result)."""

    schema_id: str
    schema_version: int
    availability_state: DashboardAvailabilityStateV1
    reason_code: str
    detail: str
    expected_source: str
    generated_at: datetime
    source_reference: str | None = None
    provenance: DashboardSnapshotProvenanceV1 | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "schema_id", require_schema_id(self.schema_id))
        object.__setattr__(self, "schema_version", require_schema_version(self.schema_version))
        state = require_enum(
            self.availability_state,
            DashboardAvailabilityStateV1,
            field="availability_state",
        )
        if state == DashboardAvailabilityStateV1.AVAILABLE:
            raise MarketDashboardReadModelContractError(
                "UnavailableSnapshotV1 cannot use AVAILABLE"
            )
        if state not in UNAVAILABLE_ALLOWED_STATES:
            raise MarketDashboardReadModelContractError(
                f"unsupported unavailable availability_state: {state}"
            )
        object.__setattr__(self, "availability_state", state)
        object.__setattr__(
            self, "reason_code", require_non_empty_str(self.reason_code, field="reason_code")
        )
        object.__setattr__(self, "detail", require_non_empty_str(self.detail, field="detail"))
        object.__setattr__(
            self,
            "expected_source",
            require_non_empty_str(self.expected_source, field="expected_source"),
        )
        object.__setattr__(
            self,
            "generated_at",
            require_aware_datetime(self.generated_at, field="generated_at"),
        )
        object.__setattr__(
            self,
            "source_reference",
            require_optional_non_empty_str(self.source_reference, field="source_reference"),
        )
        if self.provenance is not None and not isinstance(
            self.provenance, DashboardSnapshotProvenanceV1
        ):
            raise MarketDashboardReadModelContractError(
                "provenance must be DashboardSnapshotProvenanceV1 when supplied"
            )


def new_unavailable_snapshot_v1(
    *,
    availability_state: DashboardAvailabilityStateV1 | str,
    reason_code: str,
    detail: str,
    expected_source: str,
    generated_at: datetime,
    source_reference: str | None = None,
    provenance: DashboardSnapshotProvenanceV1 | None = None,
) -> UnavailableSnapshotV1:
    return UnavailableSnapshotV1(
        schema_id=UNAVAILABLE_SCHEMA_ID,
        schema_version=UNAVAILABLE_SCHEMA_VERSION,
        availability_state=require_enum(
            availability_state, DashboardAvailabilityStateV1, field="availability_state"
        ),
        reason_code=reason_code,
        detail=detail,
        expected_source=expected_source,
        generated_at=generated_at,
        source_reference=source_reference,
        provenance=provenance,
    )


@dataclass(frozen=True)
class OhlcvBarV1:
    open: float
    high: float
    low: float
    close: float
    volume: float | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "open", require_finite_number(self.open, field="open"))
        object.__setattr__(self, "high", require_finite_number(self.high, field="high"))
        object.__setattr__(self, "low", require_finite_number(self.low, field="low"))
        object.__setattr__(self, "close", require_finite_number(self.close, field="close"))
        object.__setattr__(
            self,
            "volume",
            require_optional_non_negative_number(self.volume, field="volume"),
        )
        if self.high < self.low:
            raise MarketDashboardReadModelContractError("high must be >= low")
        if self.high < self.open or self.high < self.close:
            raise MarketDashboardReadModelContractError("high must be >= open and close")
        if self.low > self.open or self.low > self.close:
            raise MarketDashboardReadModelContractError("low must be <= open and close")


@dataclass(frozen=True)
class MarketInstrumentSnapshotV1:
    schema_id: str
    schema_version: int
    instrument_id: str
    venue: str
    effective_at: datetime
    freshness_state: DashboardFreshnessStateV1
    provenance: DashboardSnapshotProvenanceV1
    mark_price: float | None = None
    last_price: float | None = None
    change_abs: float | None = None
    change_pct: float | None = None
    volume: float | None = None
    ohlcv: OhlcvBarV1 | None = None
    market_series_reference: str | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "schema_id", require_schema_id(self.schema_id))
        object.__setattr__(self, "schema_version", require_schema_version(self.schema_version))
        object.__setattr__(
            self,
            "instrument_id",
            require_non_empty_str(self.instrument_id, field="instrument_id"),
        )
        object.__setattr__(self, "venue", require_non_empty_str(self.venue, field="venue"))
        object.__setattr__(
            self,
            "effective_at",
            require_aware_datetime(self.effective_at, field="effective_at"),
        )
        object.__setattr__(
            self,
            "freshness_state",
            require_enum(self.freshness_state, DashboardFreshnessStateV1, field="freshness_state"),
        )
        if not isinstance(self.provenance, DashboardSnapshotProvenanceV1):
            raise MarketDashboardReadModelContractError("provenance is mandatory")
        object.__setattr__(
            self, "mark_price", require_optional_finite_number(self.mark_price, field="mark_price")
        )
        object.__setattr__(
            self, "last_price", require_optional_finite_number(self.last_price, field="last_price")
        )
        object.__setattr__(
            self,
            "change_abs",
            require_optional_finite_number(self.change_abs, field="change_abs"),
        )
        object.__setattr__(
            self,
            "change_pct",
            require_optional_finite_number(self.change_pct, field="change_pct"),
        )
        object.__setattr__(
            self,
            "volume",
            require_optional_non_negative_number(self.volume, field="volume"),
        )
        if self.ohlcv is not None and not isinstance(self.ohlcv, OhlcvBarV1):
            raise MarketDashboardReadModelContractError("ohlcv must be OhlcvBarV1 when supplied")
        object.__setattr__(
            self,
            "market_series_reference",
            require_optional_non_empty_str(
                self.market_series_reference, field="market_series_reference"
            ),
        )
        if self.mark_price is None and self.last_price is None and self.ohlcv is None:
            raise MarketDashboardReadModelContractError(
                "MarketInstrumentSnapshotV1 requires mark_price, last_price, or ohlcv; "
                "use UnavailableSnapshotV1 when market data is missing"
            )


@dataclass(frozen=True)
class MarketRankingItemV1:
    instrument_id: str
    rank: int
    score: float | None
    eligibility_status: EligibilityStatusV1
    reason_codes: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "instrument_id",
            require_non_empty_str(self.instrument_id, field="instrument_id"),
        )
        if not isinstance(self.rank, int) or isinstance(self.rank, bool) or self.rank < 1:
            raise MarketDashboardReadModelContractError("rank must be an integer >= 1")
        object.__setattr__(self, "score", require_optional_finite_number(self.score, field="score"))
        object.__setattr__(
            self,
            "eligibility_status",
            require_enum(self.eligibility_status, EligibilityStatusV1, field="eligibility_status"),
        )
        object.__setattr__(
            self,
            "reason_codes",
            normalize_reason_codes(self.reason_codes, field="reason_codes"),
        )


@dataclass(frozen=True)
class MarketRankingSnapshotV1:
    schema_id: str
    schema_version: int
    ranked_items: tuple[MarketRankingItemV1, ...]
    selected_instrument_id: str | None
    effective_at: datetime
    provenance: DashboardSnapshotProvenanceV1
    allow_duplicate_ranks: bool = False

    def __post_init__(self) -> None:
        object.__setattr__(self, "schema_id", require_schema_id(self.schema_id))
        object.__setattr__(self, "schema_version", require_schema_version(self.schema_version))
        if not isinstance(self.ranked_items, tuple):
            raise MarketDashboardReadModelContractError("ranked_items must be a tuple")
        for index, item in enumerate(self.ranked_items):
            if not isinstance(item, MarketRankingItemV1):
                raise MarketDashboardReadModelContractError(
                    f"ranked_items[{index}] must be MarketRankingItemV1"
                )
        instrument_ids = [item.instrument_id for item in self.ranked_items]
        if len(set(instrument_ids)) != len(instrument_ids):
            raise MarketDashboardReadModelContractError(
                "ranked_items must have unique instrument_id values"
            )
        ranks = [item.rank for item in self.ranked_items]
        if not self.allow_duplicate_ranks and len(set(ranks)) != len(ranks):
            raise MarketDashboardReadModelContractError(
                "duplicate ranks are not allowed unless allow_duplicate_ranks=True"
            )
        # Deterministic ordering by rank then instrument_id.
        ordered = tuple(sorted(self.ranked_items, key=lambda item: (item.rank, item.instrument_id)))
        object.__setattr__(self, "ranked_items", ordered)
        object.__setattr__(
            self,
            "selected_instrument_id",
            require_optional_non_empty_str(
                self.selected_instrument_id, field="selected_instrument_id"
            ),
        )
        if (
            self.selected_instrument_id is not None
            and self.selected_instrument_id not in instrument_ids
            and instrument_ids
        ):
            raise MarketDashboardReadModelContractError(
                "selected_instrument_id must reference a ranked instrument when ranking is non-empty"
            )
        object.__setattr__(
            self,
            "effective_at",
            require_aware_datetime(self.effective_at, field="effective_at"),
        )
        if not isinstance(self.provenance, DashboardSnapshotProvenanceV1):
            raise MarketDashboardReadModelContractError("provenance is mandatory")


@dataclass(frozen=True)
class CanonicalDecisionSummaryV1:
    """Stores a producer decision result only — does not calculate or infer decisions."""

    schema_id: str
    schema_version: int
    decision_status: CanonicalDecisionStatusV1
    direction: DecisionDirectionV1
    confidence: float | None
    evidence_status: str
    reason_codes: tuple[str, ...]
    blockers: tuple[str, ...]
    evidence_digest: str | None
    evidence_reference: str | None
    effective_at: datetime
    provenance: DashboardSnapshotProvenanceV1

    def __post_init__(self) -> None:
        object.__setattr__(self, "schema_id", require_schema_id(self.schema_id))
        object.__setattr__(self, "schema_version", require_schema_version(self.schema_version))
        object.__setattr__(
            self,
            "decision_status",
            require_enum(self.decision_status, CanonicalDecisionStatusV1, field="decision_status"),
        )
        object.__setattr__(
            self,
            "direction",
            require_enum(self.direction, DecisionDirectionV1, field="direction"),
        )
        object.__setattr__(
            self,
            "confidence",
            require_optional_finite_number(self.confidence, field="confidence"),
        )
        if self.confidence is not None and not (0.0 <= self.confidence <= 1.0):
            raise MarketDashboardReadModelContractError("confidence must be in [0, 1] when set")
        object.__setattr__(
            self,
            "evidence_status",
            require_non_empty_str(self.evidence_status, field="evidence_status"),
        )
        object.__setattr__(
            self,
            "reason_codes",
            normalize_reason_codes(self.reason_codes, field="reason_codes"),
        )
        object.__setattr__(self, "blockers", normalize_blockers(self.blockers, field="blockers"))
        object.__setattr__(
            self,
            "evidence_digest",
            require_optional_sha256_digest(self.evidence_digest, field="evidence_digest"),
        )
        object.__setattr__(
            self,
            "evidence_reference",
            require_optional_non_empty_str(self.evidence_reference, field="evidence_reference"),
        )
        if self.evidence_digest is None and self.evidence_reference is None:
            raise MarketDashboardReadModelContractError(
                "CanonicalDecisionSummaryV1 requires evidence_digest or evidence_reference"
            )
        object.__setattr__(
            self,
            "effective_at",
            require_aware_datetime(self.effective_at, field="effective_at"),
        )
        if not isinstance(self.provenance, DashboardSnapshotProvenanceV1):
            raise MarketDashboardReadModelContractError("provenance is mandatory")


@dataclass(frozen=True)
class SideAssessmentV1:
    status: str
    score: float | None = None
    reason_codes: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "status", require_non_empty_str(self.status, field="status"))
        object.__setattr__(self, "score", require_optional_finite_number(self.score, field="score"))
        object.__setattr__(
            self,
            "reason_codes",
            normalize_reason_codes(self.reason_codes, field="reason_codes"),
        )


@dataclass(frozen=True)
class DoublePlayDecisionSnapshotV1:
    """Producer-projected Double Play result only — no composition/arbitration logic."""

    schema_id: str
    schema_version: int
    bull_assessment: SideAssessmentV1
    bear_assessment: SideAssessmentV1
    composition_result: str
    arbitration_status: str
    blockers: tuple[str, ...]
    evidence_digest: str | None
    evidence_reference: str | None
    effective_at: datetime
    provenance: DashboardSnapshotProvenanceV1

    def __post_init__(self) -> None:
        object.__setattr__(self, "schema_id", require_schema_id(self.schema_id))
        object.__setattr__(self, "schema_version", require_schema_version(self.schema_version))
        if not isinstance(self.bull_assessment, SideAssessmentV1):
            raise MarketDashboardReadModelContractError("bull_assessment must be SideAssessmentV1")
        if not isinstance(self.bear_assessment, SideAssessmentV1):
            raise MarketDashboardReadModelContractError("bear_assessment must be SideAssessmentV1")
        object.__setattr__(
            self,
            "composition_result",
            require_non_empty_str(self.composition_result, field="composition_result"),
        )
        object.__setattr__(
            self,
            "arbitration_status",
            require_non_empty_str(self.arbitration_status, field="arbitration_status"),
        )
        object.__setattr__(self, "blockers", normalize_blockers(self.blockers, field="blockers"))
        object.__setattr__(
            self,
            "evidence_digest",
            require_optional_sha256_digest(self.evidence_digest, field="evidence_digest"),
        )
        object.__setattr__(
            self,
            "evidence_reference",
            require_optional_non_empty_str(self.evidence_reference, field="evidence_reference"),
        )
        if self.evidence_digest is None and self.evidence_reference is None:
            raise MarketDashboardReadModelContractError(
                "DoublePlayDecisionSnapshotV1 requires evidence_digest or evidence_reference"
            )
        object.__setattr__(
            self,
            "effective_at",
            require_aware_datetime(self.effective_at, field="effective_at"),
        )
        if not isinstance(self.provenance, DashboardSnapshotProvenanceV1):
            raise MarketDashboardReadModelContractError("provenance is mandatory")


@dataclass(frozen=True)
class SafetyAuthoritySnapshotV1:
    """Authority/risk/execution permission states as supplied by producers — no derivation."""

    schema_id: str
    schema_version: int
    authority_classification: AuthorityClassificationV1
    kill_switch_state: TriStateV1
    risk_gate_state: TriStateV1
    execution_permission_state: TriStateV1
    fail_closed_reason_codes: tuple[str, ...]
    effective_at: datetime
    provenance: DashboardSnapshotProvenanceV1

    def __post_init__(self) -> None:
        object.__setattr__(self, "schema_id", require_schema_id(self.schema_id))
        object.__setattr__(self, "schema_version", require_schema_version(self.schema_version))
        object.__setattr__(
            self,
            "authority_classification",
            require_enum(
                self.authority_classification,
                AuthorityClassificationV1,
                field="authority_classification",
            ),
        )
        object.__setattr__(
            self,
            "kill_switch_state",
            require_enum(self.kill_switch_state, TriStateV1, field="kill_switch_state"),
        )
        object.__setattr__(
            self,
            "risk_gate_state",
            require_enum(self.risk_gate_state, TriStateV1, field="risk_gate_state"),
        )
        object.__setattr__(
            self,
            "execution_permission_state",
            require_enum(
                self.execution_permission_state,
                TriStateV1,
                field="execution_permission_state",
            ),
        )
        object.__setattr__(
            self,
            "fail_closed_reason_codes",
            normalize_reason_codes(self.fail_closed_reason_codes, field="fail_closed_reason_codes"),
        )
        object.__setattr__(
            self,
            "effective_at",
            require_aware_datetime(self.effective_at, field="effective_at"),
        )
        if not isinstance(self.provenance, DashboardSnapshotProvenanceV1):
            raise MarketDashboardReadModelContractError("provenance is mandatory")


@dataclass(frozen=True)
class ExecutionStateSnapshotV1:
    """Execution/recon state snapshot — no order methods or exchange clients."""

    schema_id: str
    schema_version: int
    operating_mode: OperatingModeV1
    intent_state: str
    fill_state: str
    reconciliation_state: str
    unknown_outcome_state: str
    effective_at: datetime
    provenance: DashboardSnapshotProvenanceV1

    def __post_init__(self) -> None:
        object.__setattr__(self, "schema_id", require_schema_id(self.schema_id))
        object.__setattr__(self, "schema_version", require_schema_version(self.schema_version))
        object.__setattr__(
            self,
            "operating_mode",
            require_enum(self.operating_mode, OperatingModeV1, field="operating_mode"),
        )
        for name in (
            "intent_state",
            "fill_state",
            "reconciliation_state",
            "unknown_outcome_state",
        ):
            object.__setattr__(
                self,
                name,
                require_non_empty_str(getattr(self, name), field=name),
            )
        object.__setattr__(
            self,
            "effective_at",
            require_aware_datetime(self.effective_at, field="effective_at"),
        )
        if not isinstance(self.provenance, DashboardSnapshotProvenanceV1):
            raise MarketDashboardReadModelContractError("provenance is mandatory")


@dataclass(frozen=True)
class EconomicSummarySnapshotV1:
    """Economic metrics as supplied; unavailable metrics remain None (never 0.0 default)."""

    schema_id: str
    schema_version: int
    economic_gate_status: EconomicGateStatusV1
    sample_size: int | None
    evidence_digest: str | None
    evidence_reference: str | None
    effective_at: datetime
    provenance: DashboardSnapshotProvenanceV1
    gross_return: float | None = None
    net_return: float | None = None
    profit_factor: float | None = None
    drawdown: float | None = None
    cost_drag: float | None = None
    expectancy: float | None = None
    authoritative_gate: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "schema_id", require_schema_id(self.schema_id))
        object.__setattr__(self, "schema_version", require_schema_version(self.schema_version))
        object.__setattr__(
            self,
            "economic_gate_status",
            require_enum(
                self.economic_gate_status, EconomicGateStatusV1, field="economic_gate_status"
            ),
        )
        if self.sample_size is None:
            pass
        else:
            object.__setattr__(
                self,
                "sample_size",
                require_non_negative_int(self.sample_size, field="sample_size"),
            )
        for name in (
            "gross_return",
            "net_return",
            "profit_factor",
            "drawdown",
            "cost_drag",
            "expectancy",
        ):
            object.__setattr__(
                self,
                name,
                require_optional_finite_number(getattr(self, name), field=name),
            )
        if self.drawdown is not None and self.drawdown < 0:
            raise MarketDashboardReadModelContractError("drawdown must be >= 0 when set")
        if self.cost_drag is not None and self.cost_drag < 0:
            raise MarketDashboardReadModelContractError("cost_drag must be >= 0 when set")
        object.__setattr__(
            self,
            "evidence_digest",
            require_optional_sha256_digest(self.evidence_digest, field="evidence_digest"),
        )
        object.__setattr__(
            self,
            "evidence_reference",
            require_optional_non_empty_str(self.evidence_reference, field="evidence_reference"),
        )
        if self.evidence_digest is None and self.evidence_reference is None:
            raise MarketDashboardReadModelContractError(
                "EconomicSummarySnapshotV1 requires evidence_digest or evidence_reference"
            )
        if not isinstance(self.authoritative_gate, bool):
            raise MarketDashboardReadModelContractError("authoritative_gate must be bool")
        if (
            self.economic_gate_status == EconomicGateStatusV1.DIAGNOSTIC_ONLY
            and self.authoritative_gate
        ):
            raise MarketDashboardReadModelContractError(
                "DIAGNOSTIC_ONLY economic_gate_status cannot be authoritative"
            )
        object.__setattr__(
            self,
            "effective_at",
            require_aware_datetime(self.effective_at, field="effective_at"),
        )
        if not isinstance(self.provenance, DashboardSnapshotProvenanceV1):
            raise MarketDashboardReadModelContractError("provenance is mandatory")


@dataclass(frozen=True)
class DiagnosticsSummarySnapshotV1:
    """Diagnostic-only snapshot; cannot grant authority or alter decisions/gates."""

    schema_id: str
    schema_version: int
    diagnostic_statuses: tuple[str, ...]
    bundle_digest: str | None
    bundle_reference: str | None
    effective_at: datetime
    provenance: DashboardSnapshotProvenanceV1
    non_authoritative: bool = True
    diagnostic_only: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "schema_id", require_schema_id(self.schema_id))
        object.__setattr__(self, "schema_version", require_schema_version(self.schema_version))
        object.__setattr__(
            self,
            "diagnostic_statuses",
            normalize_reason_codes(self.diagnostic_statuses, field="diagnostic_statuses"),
        )
        object.__setattr__(
            self,
            "bundle_digest",
            require_optional_sha256_digest(self.bundle_digest, field="bundle_digest"),
        )
        object.__setattr__(
            self,
            "bundle_reference",
            require_optional_non_empty_str(self.bundle_reference, field="bundle_reference"),
        )
        if self.bundle_digest is None and self.bundle_reference is None:
            raise MarketDashboardReadModelContractError(
                "DiagnosticsSummarySnapshotV1 requires bundle_digest or bundle_reference"
            )
        if self.non_authoritative is not True:
            raise MarketDashboardReadModelContractError(
                "DiagnosticsSummarySnapshotV1 must set non_authoritative=True"
            )
        if self.diagnostic_only is not True:
            raise MarketDashboardReadModelContractError(
                "DiagnosticsSummarySnapshotV1 must set diagnostic_only=True"
            )
        object.__setattr__(
            self,
            "effective_at",
            require_aware_datetime(self.effective_at, field="effective_at"),
        )
        if not isinstance(self.provenance, DashboardSnapshotProvenanceV1):
            raise MarketDashboardReadModelContractError("provenance is mandatory")


@dataclass(frozen=True)
class SourceFreshnessEntryV1:
    source_key: str
    freshness_state: DashboardFreshnessStateV1
    source_age_seconds: float | None
    missing: bool
    stale: bool

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "source_key", require_non_empty_str(self.source_key, field="source_key")
        )
        object.__setattr__(
            self,
            "freshness_state",
            require_enum(self.freshness_state, DashboardFreshnessStateV1, field="freshness_state"),
        )
        if self.source_age_seconds is not None:
            age = require_non_negative_number(self.source_age_seconds, field="source_age_seconds")
            object.__setattr__(self, "source_age_seconds", age)
        if not isinstance(self.missing, bool) or not isinstance(self.stale, bool):
            raise MarketDashboardReadModelContractError("missing/stale must be bool")
        if self.missing and self.freshness_state not in {
            DashboardFreshnessStateV1.MISSING,
            DashboardFreshnessStateV1.UNKNOWN,
        }:
            raise MarketDashboardReadModelContractError(
                "missing=True requires freshness_state MISSING or UNKNOWN"
            )
        if self.stale and self.freshness_state not in {
            DashboardFreshnessStateV1.STALE,
            DashboardFreshnessStateV1.UNKNOWN,
        }:
            raise MarketDashboardReadModelContractError(
                "stale=True requires freshness_state STALE or UNKNOWN"
            )


@dataclass(frozen=True)
class DashboardFreshnessSnapshotV1:
    schema_id: str
    schema_version: int
    page_generated_at: datetime
    source_entries: tuple[SourceFreshnessEntryV1, ...]
    provenance: DashboardSnapshotProvenanceV1

    def __post_init__(self) -> None:
        object.__setattr__(self, "schema_id", require_schema_id(self.schema_id))
        object.__setattr__(self, "schema_version", require_schema_version(self.schema_version))
        object.__setattr__(
            self,
            "page_generated_at",
            require_aware_datetime(self.page_generated_at, field="page_generated_at"),
        )
        if not isinstance(self.source_entries, tuple):
            raise MarketDashboardReadModelContractError("source_entries must be a tuple")
        for index, entry in enumerate(self.source_entries):
            if not isinstance(entry, SourceFreshnessEntryV1):
                raise MarketDashboardReadModelContractError(
                    f"source_entries[{index}] must be SourceFreshnessEntryV1"
                )
        keys = [entry.source_key for entry in self.source_entries]
        if len(set(keys)) != len(keys):
            raise MarketDashboardReadModelContractError("source_entries keys must be unique")
        ordered = tuple(sorted(self.source_entries, key=lambda entry: entry.source_key))
        object.__setattr__(self, "source_entries", ordered)
        if not isinstance(self.provenance, DashboardSnapshotProvenanceV1):
            raise MarketDashboardReadModelContractError("provenance is mandatory")


# Helpers to construct available snapshots with canonical schema ids.


def new_market_instrument_snapshot_v1(**kwargs: Any) -> MarketInstrumentSnapshotV1:
    return MarketInstrumentSnapshotV1(
        schema_id=MARKET_INSTRUMENT_SCHEMA_ID,
        schema_version=SCHEMA_VERSION_V1,
        **kwargs,
    )


def new_market_ranking_snapshot_v1(**kwargs: Any) -> MarketRankingSnapshotV1:
    return MarketRankingSnapshotV1(
        schema_id=MARKET_RANKING_SCHEMA_ID,
        schema_version=SCHEMA_VERSION_V1,
        **kwargs,
    )


def new_canonical_decision_summary_v1(**kwargs: Any) -> CanonicalDecisionSummaryV1:
    return CanonicalDecisionSummaryV1(
        schema_id=CANONICAL_DECISION_SCHEMA_ID,
        schema_version=SCHEMA_VERSION_V1,
        **kwargs,
    )


def new_double_play_decision_snapshot_v1(**kwargs: Any) -> DoublePlayDecisionSnapshotV1:
    return DoublePlayDecisionSnapshotV1(
        schema_id=DOUBLE_PLAY_SCHEMA_ID,
        schema_version=SCHEMA_VERSION_V1,
        **kwargs,
    )


def new_safety_authority_snapshot_v1(**kwargs: Any) -> SafetyAuthoritySnapshotV1:
    return SafetyAuthoritySnapshotV1(
        schema_id=SAFETY_AUTHORITY_SCHEMA_ID,
        schema_version=SCHEMA_VERSION_V1,
        **kwargs,
    )


def new_execution_state_snapshot_v1(**kwargs: Any) -> ExecutionStateSnapshotV1:
    return ExecutionStateSnapshotV1(
        schema_id=EXECUTION_STATE_SCHEMA_ID,
        schema_version=SCHEMA_VERSION_V1,
        **kwargs,
    )


def new_economic_summary_snapshot_v1(**kwargs: Any) -> EconomicSummarySnapshotV1:
    return EconomicSummarySnapshotV1(
        schema_id=ECONOMIC_SUMMARY_SCHEMA_ID,
        schema_version=SCHEMA_VERSION_V1,
        **kwargs,
    )


def new_diagnostics_summary_snapshot_v1(**kwargs: Any) -> DiagnosticsSummarySnapshotV1:
    return DiagnosticsSummarySnapshotV1(
        schema_id=DIAGNOSTICS_SUMMARY_SCHEMA_ID,
        schema_version=SCHEMA_VERSION_V1,
        **kwargs,
    )


def new_dashboard_freshness_snapshot_v1(**kwargs: Any) -> DashboardFreshnessSnapshotV1:
    return DashboardFreshnessSnapshotV1(
        schema_id=FRESHNESS_SCHEMA_ID,
        schema_version=SCHEMA_VERSION_V1,
        **kwargs,
    )


__all__ = [
    "AuthorityClassificationV1",
    "CANONICAL_DECISION_SCHEMA_ID",
    "CanonicalDecisionStatusV1",
    "CanonicalDecisionSummaryV1",
    "DIAGNOSTICS_SUMMARY_SCHEMA_ID",
    "DOUBLE_PLAY_SCHEMA_ID",
    "DashboardAvailabilityStateV1",
    "DashboardFreshnessSnapshotV1",
    "DecisionDirectionV1",
    "DiagnosticsSummarySnapshotV1",
    "DoublePlayDecisionSnapshotV1",
    "ECONOMIC_SUMMARY_SCHEMA_ID",
    "EXECUTION_STATE_SCHEMA_ID",
    "EconomicGateStatusV1",
    "EconomicSummarySnapshotV1",
    "EligibilityStatusV1",
    "ExecutionStateSnapshotV1",
    "FRESHNESS_SCHEMA_ID",
    "MARKET_INSTRUMENT_SCHEMA_ID",
    "MARKET_RANKING_SCHEMA_ID",
    "MarketInstrumentSnapshotV1",
    "MarketRankingItemV1",
    "MarketRankingSnapshotV1",
    "OhlcvBarV1",
    "OperatingModeV1",
    "PACKAGE_ID",
    "SAFETY_AUTHORITY_SCHEMA_ID",
    "SCHEMA_VERSION_V1",
    "SafetyAuthoritySnapshotV1",
    "SideAssessmentV1",
    "SourceFreshnessEntryV1",
    "TriStateV1",
    "UNAVAILABLE_SCHEMA_ID",
    "UNAVAILABLE_SCHEMA_VERSION",
    "UnavailableSnapshotV1",
    "new_canonical_decision_summary_v1",
    "new_dashboard_freshness_snapshot_v1",
    "new_diagnostics_summary_snapshot_v1",
    "new_double_play_decision_snapshot_v1",
    "new_economic_summary_snapshot_v1",
    "new_execution_state_snapshot_v1",
    "new_market_instrument_snapshot_v1",
    "new_market_ranking_snapshot_v1",
    "new_safety_authority_snapshot_v1",
    "new_unavailable_snapshot_v1",
]
