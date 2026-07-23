"""Pure field-projection adapters — no decision/risk/sizing recomputation."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Mapping, Sequence

from .availability import Availability
from .contracts import (
    SCHEMA_FAMILY,
    SCHEMA_VERSION,
    CanonicalDecisionSnapshotV1,
    DoublePlaySnapshotV1,
    DynamicScopeSnapshotV1,
    MarketInstrumentSnapshotV1,
    UniverseRankingSnapshotV1,
)
from .provenance import FreshnessV1, SnapshotProvenanceV1


def project_market_instrument_snapshot_v1(
    *,
    instrument_id: str,
    venue: str | None,
    market_type: str | None,
    mark_price: float | None,
    reason_codes: Sequence[str],
    generated_at: datetime,
    effective_at: datetime | None,
    source_reference: str | None,
    evidence_digest: str | None = None,
    git_sha: str | None = None,
    producer_module: str = "trading.master_v2.canonical_market_context_v1",
    source_kind: str = "canonical_market_context",
    availability: Availability = Availability.AVAILABLE,
    max_age_seconds: int | None = None,
    is_stale: bool = False,
    stale_reason: str | None = None,
) -> MarketInstrumentSnapshotV1:
    """Project already-computed market identity fields into a Landscape snapshot.

    Forbidden: inventing instrument/venue/mark_price, fabricating OHLCV, or
    deriving futures/spot eligibility from symbol heuristics.
    market_type and mark_price may remain None when the producer did not supply them.
    generated_at/effective_at must be producer timestamps — never page-assembly time.
    """
    if not instrument_id:
        raise ValueError("instrument_id required for AVAILABLE/STALE projection")
    if availability not in (Availability.AVAILABLE, Availability.STALE):
        raise ValueError("project_market_instrument only emits AVAILABLE or STALE")
    if availability is Availability.AVAILABLE and is_stale:
        raise ValueError("AVAILABLE cannot be stale")
    if availability is Availability.STALE and not is_stale:
        raise ValueError("STALE requires is_stale=True")
    schema_id = f"{SCHEMA_FAMILY}.market_instrument.{SCHEMA_VERSION}"
    provenance = SnapshotProvenanceV1(
        schema_id=schema_id,
        schema_version=SCHEMA_VERSION,
        producer_module=producer_module,
        generated_at=generated_at,
        effective_at=effective_at,
        source_kind=source_kind,
        source_reference=source_reference,
        evidence_digest=evidence_digest,
        git_sha=git_sha,
        availability=availability,
    )
    freshness = FreshnessV1(
        observed_at=generated_at,
        max_age_seconds=max_age_seconds,
        is_stale=is_stale,
        stale_reason=stale_reason,
    )
    return MarketInstrumentSnapshotV1(
        schema_id=schema_id,
        schema_version=SCHEMA_VERSION,
        provenance=provenance,
        freshness=freshness,
        availability=availability,
        instrument_id=instrument_id,
        venue=venue,
        market_type=market_type,
        mark_price=None if mark_price is None else float(mark_price),
        reason_codes=tuple(str(code) for code in reason_codes),
    )


def project_universe_ranking_snapshot_v1(
    *,
    ranking: Sequence[Mapping[str, Any]],
    selected_instrument_id: str | None,
    reason_codes: Sequence[str],
    generated_at: datetime,
    effective_at: datetime | None,
    source_reference: str | None,
    universe: Sequence[Mapping[str, Any]] = (),
    evidence_digest: str | None = None,
    git_sha: str | None = None,
    producer_module: str = ("webui.workflow_dashboard_readmodel_v1.universe_selection_contract_v1"),
    availability: Availability = Availability.AVAILABLE,
    max_age_seconds: int | None = None,
    is_stale: bool = False,
    stale_reason: str | None = None,
) -> UniverseRankingSnapshotV1:
    """Project an existing universe_selection ranking into Landscape form.

    Forbidden: recomputing ranks, inventing selected instruments, or enriching
    rows with decision/risk/sizing semantics.
    generated_at/effective_at must be producer timestamps — never page-assembly time.
    """
    ranking_rows = tuple(dict(row) for row in ranking)
    universe_rows = tuple(dict(row) for row in universe)
    if not ranking_rows and not universe_rows and not selected_instrument_id:
        raise ValueError(
            "ranking, universe, or selected_instrument_id required for AVAILABLE/STALE"
        )
    if availability not in (Availability.AVAILABLE, Availability.STALE):
        raise ValueError("project_universe_ranking only emits AVAILABLE or STALE")
    if availability is Availability.AVAILABLE and is_stale:
        raise ValueError("AVAILABLE cannot be stale")
    if availability is Availability.STALE and not is_stale:
        raise ValueError("STALE requires is_stale=True")
    schema_id = f"{SCHEMA_FAMILY}.universe_ranking.{SCHEMA_VERSION}"
    provenance = SnapshotProvenanceV1(
        schema_id=schema_id,
        schema_version=SCHEMA_VERSION,
        producer_module=producer_module,
        generated_at=generated_at,
        effective_at=effective_at,
        source_kind="universe_selection_readmodel",
        source_reference=source_reference,
        evidence_digest=evidence_digest,
        git_sha=git_sha,
        availability=availability,
    )
    freshness = FreshnessV1(
        observed_at=generated_at,
        max_age_seconds=max_age_seconds,
        is_stale=is_stale,
        stale_reason=stale_reason,
    )
    return UniverseRankingSnapshotV1(
        schema_id=schema_id,
        schema_version=SCHEMA_VERSION,
        provenance=provenance,
        freshness=freshness,
        availability=availability,
        ranking=ranking_rows,
        universe=universe_rows,
        selected_instrument_id=selected_instrument_id,
        reason_codes=tuple(str(code) for code in reason_codes),
    )


def project_dynamic_scope_snapshot_v1(
    *,
    scope_state: str,
    current_scope_ref: str,
    reason_codes: Sequence[str],
    generated_at: datetime,
    effective_at: datetime | None,
    source_reference: str | None,
    next_scope_ref: str | None = None,
    evidence_digest: str | None = None,
    git_sha: str | None = None,
    producer_module: str = "trading.master_v2.canonical_scope_initialization_v1",
    source_kind: str = "canonical_scope_snapshot",
    availability: Availability = Availability.AVAILABLE,
    max_age_seconds: int | None = None,
    is_stale: bool = False,
    stale_reason: str | None = None,
) -> DynamicScopeSnapshotV1:
    """Project already-computed canonical scope lifecycle identity fields.

    Forbidden: inventing lifecycle state/refs, deriving regime/bull-bear/switch,
    calling scope initializers or switch-transition owners, or using page-assembly
    time as producer freshness.
    generated_at/effective_at must be producer timestamps — never page-assembly time.
    """
    if not scope_state:
        raise ValueError("scope_state required for AVAILABLE/STALE projection")
    if not current_scope_ref:
        raise ValueError("current_scope_ref required for AVAILABLE/STALE projection")
    if availability not in (Availability.AVAILABLE, Availability.STALE):
        raise ValueError("project_dynamic_scope only emits AVAILABLE or STALE")
    if availability is Availability.AVAILABLE and is_stale:
        raise ValueError("AVAILABLE cannot be stale")
    if availability is Availability.STALE and not is_stale:
        raise ValueError("STALE requires is_stale=True")
    schema_id = f"{SCHEMA_FAMILY}.dynamic_scope.{SCHEMA_VERSION}"
    provenance = SnapshotProvenanceV1(
        schema_id=schema_id,
        schema_version=SCHEMA_VERSION,
        producer_module=producer_module,
        generated_at=generated_at,
        effective_at=effective_at,
        source_kind=source_kind,
        source_reference=source_reference,
        evidence_digest=evidence_digest,
        git_sha=git_sha,
        availability=availability,
    )
    freshness = FreshnessV1(
        observed_at=generated_at,
        max_age_seconds=max_age_seconds,
        is_stale=is_stale,
        stale_reason=stale_reason,
    )
    return DynamicScopeSnapshotV1(
        schema_id=schema_id,
        schema_version=SCHEMA_VERSION,
        provenance=provenance,
        freshness=freshness,
        availability=availability,
        scope_state=str(scope_state),
        current_scope_ref=str(current_scope_ref),
        next_scope_ref=None if next_scope_ref is None else str(next_scope_ref),
        reason_codes=tuple(str(code) for code in reason_codes),
    )


def project_canonical_decision_snapshot_v1(
    *,
    instrument_id: str,
    decision: str,
    direction: str,
    reason_codes: Sequence[str],
    blockers: Sequence[str],
    decision_id: str | None,
    evidence_schema_version: str,
    evidence_digest: str | None,
    generated_at: datetime,
    effective_at: datetime | None,
    source_reference: str | None,
    git_sha: str | None = None,
    producer_module: str = "trading.master_v2.canonical_trading_decision_evidence_v1",
) -> CanonicalDecisionSnapshotV1:
    """Project already-computed decision evidence fields into a Landscape snapshot.

    Forbidden: inventing decision/direction, synthesizing reason codes, or
    deriving blockers from non-evidence sources.
    """
    if not instrument_id or not decision or not direction:
        raise ValueError("instrument_id, decision, and direction are required for AVAILABLE")
    if not evidence_schema_version:
        raise ValueError("evidence_schema_version required")
    codes = tuple(str(code) for code in reason_codes)
    block = tuple(str(code) for code in blockers)
    schema_id = f"{SCHEMA_FAMILY}.canonical_decision.{SCHEMA_VERSION}"
    provenance = SnapshotProvenanceV1(
        schema_id=schema_id,
        schema_version=SCHEMA_VERSION,
        producer_module=producer_module,
        generated_at=generated_at,
        effective_at=effective_at,
        source_kind="canonical_trading_decision_evidence",
        source_reference=source_reference,
        evidence_digest=evidence_digest,
        git_sha=git_sha,
        availability=Availability.AVAILABLE,
    )
    freshness = FreshnessV1(
        observed_at=generated_at,
        max_age_seconds=None,
        is_stale=False,
        stale_reason=None,
    )
    return CanonicalDecisionSnapshotV1(
        schema_id=schema_id,
        schema_version=SCHEMA_VERSION,
        provenance=provenance,
        freshness=freshness,
        availability=Availability.AVAILABLE,
        instrument_id=instrument_id,
        decision=decision,
        direction=direction,
        reason_codes=codes,
        blockers=block,
        decision_id=decision_id,
        evidence_schema_version=evidence_schema_version,
    )


def project_double_play_snapshot_v1(
    *,
    overall_status: str,
    panel_summaries: Sequence[Mapping[str, Any]],
    blockers: Sequence[str],
    generated_at: datetime,
    source_reference: str | None,
    evidence_digest: str | None = None,
    git_sha: str | None = None,
    producer_module: str = "trading.master_v2.double_play_dashboard_display",
) -> DoublePlaySnapshotV1:
    """Project an existing Double Play display snapshot into Landscape form."""
    if not overall_status:
        raise ValueError("overall_status required for AVAILABLE")
    schema_id = f"{SCHEMA_FAMILY}.double_play.{SCHEMA_VERSION}"
    provenance = SnapshotProvenanceV1(
        schema_id=schema_id,
        schema_version=SCHEMA_VERSION,
        producer_module=producer_module,
        generated_at=generated_at,
        effective_at=generated_at,
        source_kind="double_play_dashboard_display",
        source_reference=source_reference,
        evidence_digest=evidence_digest,
        git_sha=git_sha,
        availability=Availability.AVAILABLE,
    )
    freshness = FreshnessV1(
        observed_at=generated_at,
        max_age_seconds=None,
        is_stale=False,
        stale_reason=None,
    )
    return DoublePlaySnapshotV1(
        schema_id=schema_id,
        schema_version=SCHEMA_VERSION,
        provenance=provenance,
        freshness=freshness,
        availability=Availability.AVAILABLE,
        overall_status=overall_status,
        panel_summaries=tuple(dict(row) for row in panel_summaries),
        blockers=tuple(str(code) for code in blockers),
        display_only=True,
        live_authorization=False,
    )
