"""B07 Future Profile Snapshot builder.

The builder is observational: it reuses current canonical snapshots and never
fetches, ranks, selects, binds, or mutates downstream trading state.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Mapping, Optional

from src.ops.economic_md_input_producer_v1.models_v1 import (
    EconomicMdInputSnapshotV1,
    EconomicMdInstrumentRawInputV1,
)
from src.ops.future_profile_snapshot_v1.constants_v1 import (
    AUTHORITY_ELIGIBILITY_SAFETY,
    AUTHORITY_PROFILE_ONLY,
    AUTHORITY_RANKING_INPUT,
    AUTHORITY_UNCLASSIFIED,
    AVAILABLE,
    CAPABILITY_ID,
    GROUP_ACTIVITY_DEPTH,
    GROUP_IDENTITY_CONTRACT,
    GROUP_MARKET_STATE,
    GROUP_MOVEMENT_ECONOMIC_FEATURES,
    GROUP_PROVENANCE_DATA_QUALITY,
    GROUP_RANKING_CONTEXT,
    MISSING,
    NOT_APPLICABLE,
    PRODUCER_VERSION,
    PROFILE_VERSION,
    SCHEMA_VERSION,
)
from src.ops.future_profile_snapshot_v1.models_v1 import (
    FutureProfileFieldV1,
    FutureProfileInstrumentSnapshotV1,
    FutureProfileSnapshotV1,
    authority_block_v1,
    compute_profile_snapshot_id_v1,
    validate_future_profile_snapshot_v1,
)
from src.ops.governed_futures_universe_producer_v1.models_v1 import (
    GovernedFuturesUniverseSnapshotV1,
    GovernedUniverseInstrumentV1,
)
from src.ops.peak_trade_ranking_feature_production_v1.models_v1 import (
    InstrumentRawFeatureProductionV1,
    RankingFeatureProductionSnapshotV1,
)
from src.ops.productive_futures_ranking_producer_v1.models_v1 import (
    ProductiveFuturesRankingSnapshotV1,
    RankedCandidateV1,
)
from src.ops.single_selected_future_policy_v1.models_v1 import (
    SingleSelectedFutureSelectionV1,
)


def _rfc3339(unix: float) -> str:
    return datetime.fromtimestamp(unix, tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _field(
    *,
    group: str,
    field_id: str,
    authority_class: str,
    value: Any,
    source: str,
    canonical_producer: str,
    unit_or_semantics: str,
    observed_at_event_time: str,
    captured_at: str,
    provenance_ref: Mapping[str, Any],
    missing_reason: str = "",
    valid: bool = True,
) -> FutureProfileFieldV1:
    state = AVAILABLE if value is not None else MISSING
    return FutureProfileFieldV1(
        group=group,
        field_id=field_id,
        authority_class=authority_class,
        availability_state=state,
        value=value,
        source=source,
        canonical_producer=canonical_producer,
        unit_or_semantics=unit_or_semantics,
        observed_at_event_time=observed_at_event_time,
        captured_at=captured_at,
        provenance_ref=dict(provenance_ref),
        missing_reason=missing_reason if state == MISSING else "",
        valid=valid if state == AVAILABLE else False,
    )


def _missing_field(
    *,
    group: str,
    field_id: str,
    authority_class: str,
    source: str,
    canonical_producer: str,
    unit_or_semantics: str,
    observed_at_event_time: str,
    captured_at: str,
    provenance_ref: Mapping[str, Any],
    missing_reason: str,
) -> FutureProfileFieldV1:
    return _field(
        group=group,
        field_id=field_id,
        authority_class=authority_class,
        value=None,
        source=source,
        canonical_producer=canonical_producer,
        unit_or_semantics=unit_or_semantics,
        observed_at_event_time=observed_at_event_time,
        captured_at=captured_at,
        provenance_ref=provenance_ref,
        missing_reason=missing_reason,
        valid=False,
    )


def _ranked_by_id(
    ranking: Optional[ProductiveFuturesRankingSnapshotV1],
) -> dict[str, RankedCandidateV1]:
    if ranking is None:
        return {}
    rows = list(ranking.ranked_candidates) + list(ranking.excluded_candidates)
    return {row.canonical_instrument_id: row for row in rows}


def _features_by_id(
    features: Optional[RankingFeatureProductionSnapshotV1],
) -> dict[str, InstrumentRawFeatureProductionV1]:
    if features is None:
        return {}
    return {row.canonical_instrument_id: row for row in features.instruments}


def _emd_by_id(
    economic_md: Optional[EconomicMdInputSnapshotV1],
) -> dict[str, EconomicMdInstrumentRawInputV1]:
    if economic_md is None:
        return {}
    return {row.canonical_instrument_id: row for row in economic_md.instruments}


def _source_references(
    *,
    universe: GovernedFuturesUniverseSnapshotV1,
    economic_md: Optional[EconomicMdInputSnapshotV1],
    features: Optional[RankingFeatureProductionSnapshotV1],
    ranking: Optional[ProductiveFuturesRankingSnapshotV1],
    selection: Optional[SingleSelectedFutureSelectionV1],
) -> dict[str, Any]:
    refs: dict[str, Any] = {
        "universe_snapshot_id": universe.snapshot_id,
        "universe_payload_digest": universe.payload_digest,
        "universe_source_digest": universe.source_digest,
    }
    if economic_md is not None:
        refs.update(
            {
                "economic_md_input_snapshot_id": economic_md.economic_input_snapshot_id,
                "economic_md_payload_digest": economic_md.payload_digest,
            }
        )
    if features is not None:
        refs.update(
            {
                "feature_production_snapshot_id": features.production_snapshot_id,
                "feature_production_digest": features.production_digest,
            }
        )
    if ranking is not None:
        refs.update(
            {
                "ranking_integrity_digest": ranking.integrity_digest,
                "ranking_snapshot_id": ranking.ranking_snapshot_id,
            }
        )
    if selection is not None:
        refs.update(
            {
                "selection_id": selection.selection_id,
                "selection_integrity_digest": selection.integrity_digest,
            }
        )
    return refs


def _selected_reference(
    selection: Optional[SingleSelectedFutureSelectionV1],
) -> dict[str, Any]:
    if selection is None:
        return {
            "profile_selects_future": False,
            "selection_reference_available": False,
        }
    return {
        "instrument_id": selection.instrument_id,
        "profile_selects_future": False,
        "selection_id": selection.selection_id,
        "selection_reference_available": bool(selection.instrument_id),
        "selection_state": selection.state,
        "selection_owner": selection.capability_id,
        "venue_native_id": selection.venue_native_id,
    }


def _identity_fields(
    *,
    instrument: GovernedUniverseInstrumentV1,
    universe: GovernedFuturesUniverseSnapshotV1,
) -> list[FutureProfileFieldV1]:
    ref = {
        "source_digest": universe.source_digest,
        "snapshot_id": universe.snapshot_id,
    }
    base_kwargs = {
        "source": "cap21_governed_futures_universe_snapshot",
        "canonical_producer": "ops.governed_futures_universe_producer_v1",
        "observed_at_event_time": instrument.source_event_time,
        "captured_at": instrument.producer_observed_at,
        "provenance_ref": ref,
    }
    values = {
        "canonical_instrument_id": instrument.canonical_instrument_id,
        "venue": instrument.venue,
        "venue_native_inst_id": instrument.venue_native_inst_id,
        "instrument_type": instrument.instrument_type,
        "base_currency": instrument.base_currency,
        "quote_currency": instrument.quote_currency,
        "settlement_currency": instrument.settlement_currency,
        "contract_type": instrument.contract_type,
        "perpetual_or_expiry_semantics": instrument.perpetual_or_expiry_semantics,
        "expiry_time": instrument.expiry_time,
        "tick_size": instrument.tick_size,
        "lot_size": instrument.lot_size,
        "minimum_order_size": instrument.minimum_order_size,
        "contract_value": instrument.contract_value,
        "contract_value_currency": instrument.contract_value_currency,
        "trading_status": instrument.trading_status,
        "mark_price_supported": instrument.mark_price_supported,
        "market_data_supported": instrument.market_data_supported,
        "eligibility": instrument.eligibility,
    }
    fields: list[FutureProfileFieldV1] = []
    for field_id, value in values.items():
        if value is None:
            fields.append(
                _missing_field(
                    group=GROUP_IDENTITY_CONTRACT,
                    field_id=field_id,
                    authority_class=AUTHORITY_ELIGIBILITY_SAFETY,
                    unit_or_semantics="cap21_structural_eligibility_or_contract_metadata",
                    missing_reason="NOT_APPLICABLE_FOR_PERPETUAL_CONTRACT",
                    **base_kwargs,
                )
            )
            continue
        fields.append(
            _field(
                group=GROUP_IDENTITY_CONTRACT,
                field_id=field_id,
                authority_class=AUTHORITY_ELIGIBILITY_SAFETY,
                value=value,
                unit_or_semantics="cap21_structural_eligibility_or_contract_metadata",
                **base_kwargs,
            )
        )
    fields.append(
        _field(
            group=GROUP_PROVENANCE_DATA_QUALITY,
            field_id="data_quality_status",
            authority_class=AUTHORITY_ELIGIBILITY_SAFETY,
            value=instrument.data_quality_status,
            unit_or_semantics="cap21_data_quality_status",
            **base_kwargs,
        )
    )
    fields.append(
        _field(
            group=GROUP_PROVENANCE_DATA_QUALITY,
            field_id="exclusion_reason_codes",
            authority_class=AUTHORITY_ELIGIBILITY_SAFETY,
            value=list(instrument.exclusion_reason_codes),
            unit_or_semantics="cap21_fail_closed_exclusion_reasons",
            **base_kwargs,
        )
    )
    return fields


def _economic_md_fields(
    *,
    instrument: GovernedUniverseInstrumentV1,
    row: Optional[EconomicMdInstrumentRawInputV1],
    event_time: str,
    captured_at: str,
    economic_md: Optional[EconomicMdInputSnapshotV1],
) -> list[FutureProfileFieldV1]:
    ref = {
        "economic_md_input_snapshot_id": ""
        if economic_md is None
        else economic_md.economic_input_snapshot_id,
        "economic_md_payload_digest": "" if economic_md is None else economic_md.payload_digest,
    }
    base = {
        "source": "economic_md_input_snapshot",
        "canonical_producer": "ops.economic_md_input_producer_v1",
        "observed_at_event_time": event_time,
        "captured_at": captured_at,
        "provenance_ref": ref,
    }
    if row is None:
        return [
            _missing_field(
                group=GROUP_MARKET_STATE,
                field_id="latest_finalized_mark_price",
                authority_class=AUTHORITY_PROFILE_ONLY,
                unit_or_semantics="venue_native_mark_price",
                missing_reason="OPTIONAL_ECONOMIC_MD_INPUT_NOT_AVAILABLE",
                **base,
            ),
            _missing_field(
                group=GROUP_ACTIVITY_DEPTH,
                field_id="best_bid_price",
                authority_class=AUTHORITY_PROFILE_ONLY,
                unit_or_semantics="same_cycle_ticker_bid_px",
                missing_reason="OPTIONAL_TICKER_NOT_AVAILABLE",
                **base,
            ),
            _missing_field(
                group=GROUP_ACTIVITY_DEPTH,
                field_id="best_ask_price",
                authority_class=AUTHORITY_PROFILE_ONLY,
                unit_or_semantics="same_cycle_ticker_ask_px",
                missing_reason="OPTIONAL_TICKER_NOT_AVAILABLE",
                **base,
            ),
        ]
    latest_mark = row.finalized_pt1m_marks[-1] if row.finalized_pt1m_marks else None
    ticker = row.ticker
    fields = [
        _field(
            group=GROUP_PROVENANCE_DATA_QUALITY,
            field_id="economic_md_raw_input_digest",
            authority_class=AUTHORITY_PROFILE_ONLY,
            value=row.raw_input_digest,
            unit_or_semantics="economic_md_instrument_raw_input_digest",
            **base,
        ),
        _field(
            group=GROUP_PROVENANCE_DATA_QUALITY,
            field_id="economic_md_raw_input_eligible",
            authority_class=AUTHORITY_UNCLASSIFIED,
            value=row.raw_input_eligible,
            unit_or_semantics="economic_md_input_quality_not_promoted_to_selection",
            **base,
        ),
    ]
    if latest_mark is None:
        fields.append(
            _missing_field(
                group=GROUP_MARKET_STATE,
                field_id="latest_finalized_mark_price",
                authority_class=AUTHORITY_PROFILE_ONLY,
                unit_or_semantics="venue_native_mark_price",
                missing_reason="OPTIONAL_FINALIZED_MARK_NOT_AVAILABLE",
                **base,
            )
        )
    else:
        fields.extend(
            [
                _field(
                    group=GROUP_MARKET_STATE,
                    field_id="latest_finalized_mark_price",
                    authority_class=AUTHORITY_PROFILE_ONLY,
                    value=latest_mark.mark_px,
                    unit_or_semantics="venue_native_mark_price",
                    observed_at_event_time=latest_mark.event_timestamp,
                    captured_at=latest_mark.receive_or_capture_timestamp,
                    source=latest_mark.source_class,
                    canonical_producer="ops.economic_md_input_producer_v1",
                    provenance_ref=ref,
                ),
                _field(
                    group=GROUP_MARKET_STATE,
                    field_id="latest_mark_finalization_status",
                    authority_class=AUTHORITY_PROFILE_ONLY,
                    value=latest_mark.finalization_status,
                    unit_or_semantics="finalized_pt1m_mark_status",
                    observed_at_event_time=latest_mark.event_timestamp,
                    captured_at=latest_mark.receive_or_capture_timestamp,
                    source=latest_mark.source_class,
                    canonical_producer="ops.economic_md_input_producer_v1",
                    provenance_ref=ref,
                ),
            ]
        )
    if ticker is None:
        fields.extend(
            [
                _missing_field(
                    group=GROUP_ACTIVITY_DEPTH,
                    field_id="best_bid_price",
                    authority_class=AUTHORITY_PROFILE_ONLY,
                    unit_or_semantics="same_cycle_ticker_bid_px",
                    missing_reason="OPTIONAL_TICKER_NOT_AVAILABLE",
                    **base,
                ),
                _missing_field(
                    group=GROUP_ACTIVITY_DEPTH,
                    field_id="best_ask_price",
                    authority_class=AUTHORITY_PROFILE_ONLY,
                    unit_or_semantics="same_cycle_ticker_ask_px",
                    missing_reason="OPTIONAL_TICKER_NOT_AVAILABLE",
                    **base,
                ),
            ]
        )
    else:
        fields.extend(
            [
                _field(
                    group=GROUP_ACTIVITY_DEPTH,
                    field_id="best_bid_price",
                    authority_class=AUTHORITY_PROFILE_ONLY,
                    value=ticker.bid_px,
                    unit_or_semantics="same_cycle_ticker_bid_px",
                    observed_at_event_time=ticker.ticker_event_timestamp or "",
                    captured_at=ticker.capture_or_receive_timestamp,
                    source=ticker.source_class,
                    canonical_producer="ops.economic_md_input_producer_v1",
                    provenance_ref=ref,
                    missing_reason="OPTIONAL_TICKER_BID_NOT_AVAILABLE",
                ),
                _field(
                    group=GROUP_ACTIVITY_DEPTH,
                    field_id="best_ask_price",
                    authority_class=AUTHORITY_PROFILE_ONLY,
                    value=ticker.ask_px,
                    unit_or_semantics="same_cycle_ticker_ask_px",
                    observed_at_event_time=ticker.ticker_event_timestamp or "",
                    captured_at=ticker.capture_or_receive_timestamp,
                    source=ticker.source_class,
                    canonical_producer="ops.economic_md_input_producer_v1",
                    provenance_ref=ref,
                    missing_reason="OPTIONAL_TICKER_ASK_NOT_AVAILABLE",
                ),
            ]
        )
    unresolved = row.unresolved_validity_dimensions.to_dict()
    for field_id, value in sorted(unresolved.items()):
        fields.append(
            _field(
                group=GROUP_PROVENANCE_DATA_QUALITY,
                field_id=f"unresolved_validity_{field_id}",
                authority_class=AUTHORITY_UNCLASSIFIED,
                value=value,
                unit_or_semantics="unresolved_validity_dimension_not_policy_promoted",
                **base,
            )
        )
    return fields


def _feature_fields(
    *,
    feature_row: Optional[InstrumentRawFeatureProductionV1],
    event_time: str,
    captured_at: str,
    features: Optional[RankingFeatureProductionSnapshotV1],
) -> list[FutureProfileFieldV1]:
    ref = {
        "feature_production_digest": "" if features is None else features.production_digest,
        "feature_production_snapshot_id": ""
        if features is None
        else features.production_snapshot_id,
    }
    base = {
        "source": "b05_ranking_feature_production_snapshot",
        "canonical_producer": "ops.peak_trade_ranking_feature_production_v1",
        "observed_at_event_time": event_time,
        "captured_at": captured_at,
        "provenance_ref": ref,
    }
    if feature_row is None:
        return [
            _missing_field(
                group=GROUP_MOVEMENT_ECONOMIC_FEATURES,
                field_id="b05_raw_features",
                authority_class=AUTHORITY_RANKING_INPUT,
                unit_or_semantics="required_b05_feature_bundle",
                missing_reason="REQUIRED_B05_FEATURE_PRODUCTION_ROW_NOT_AVAILABLE",
                **base,
            )
        ]
    fields = [
        _field(
            group=GROUP_PROVENANCE_DATA_QUALITY,
            field_id="b05_economic_md_raw_input_digest",
            authority_class=AUTHORITY_RANKING_INPUT,
            value=feature_row.economic_md_raw_input_digest,
            unit_or_semantics="source_raw_input_digest_reused",
            **base,
        ),
        _field(
            group=GROUP_PROVENANCE_DATA_QUALITY,
            field_id="b05_feature_production_ready",
            authority_class=AUTHORITY_RANKING_INPUT,
            value=feature_row.feature_production_ready,
            unit_or_semantics="b05_required_feature_readiness",
            **base,
        ),
    ]
    if feature_row.mark_window_provenance is not None:
        mw = feature_row.mark_window_provenance
        fields.extend(
            [
                _field(
                    group=GROUP_PROVENANCE_DATA_QUALITY,
                    field_id="b05_mark_window_id",
                    authority_class=AUTHORITY_RANKING_INPUT,
                    value=mw.observation_window_id,
                    unit_or_semantics="b05_observation_window_id",
                    observed_at_event_time=mw.as_of_event_time,
                    captured_at=captured_at,
                    source=mw.source_class,
                    canonical_producer="ops.peak_trade_ranking_feature_production_v1",
                    provenance_ref=ref,
                ),
                _field(
                    group=GROUP_PROVENANCE_DATA_QUALITY,
                    field_id="b05_mark_count",
                    authority_class=AUTHORITY_RANKING_INPUT,
                    value=mw.mark_count,
                    unit_or_semantics="count_finalized_pt1m_marks",
                    observed_at_event_time=mw.as_of_event_time,
                    captured_at=captured_at,
                    source=mw.source_endpoint,
                    canonical_producer="ops.peak_trade_ranking_feature_production_v1",
                    provenance_ref=ref,
                ),
            ]
        )
    for raw in feature_row.raw_features:
        fields.append(
            _field(
                group=GROUP_MOVEMENT_ECONOMIC_FEATURES,
                field_id=f"b05_raw_feature.{raw.feature_policy_id}",
                authority_class=AUTHORITY_RANKING_INPUT,
                value=raw.raw_value,
                unit_or_semantics=raw.units,
                missing_reason=raw.reason_code or "REQUIRED_RANKING_FEATURE_NOT_READY",
                **base,
            )
        )
        fields.append(
            _field(
                group=GROUP_MOVEMENT_ECONOMIC_FEATURES,
                field_id=f"b05_raw_feature_state.{raw.feature_policy_id}",
                authority_class=AUTHORITY_RANKING_INPUT,
                value=raw.state.value,
                unit_or_semantics=raw.raw_feature_normalization,
                **base,
            )
        )
    return fields


def _ranking_fields(
    *,
    candidate: Optional[RankedCandidateV1],
    event_time: str,
    captured_at: str,
    ranking: Optional[ProductiveFuturesRankingSnapshotV1],
) -> list[FutureProfileFieldV1]:
    ref = {
        "ranking_integrity_digest": "" if ranking is None else ranking.integrity_digest,
        "ranking_snapshot_id": "" if ranking is None else ranking.ranking_snapshot_id,
    }
    base = {
        "source": "b06_productive_futures_ranking_snapshot",
        "canonical_producer": "ops.productive_futures_ranking_producer_v1",
        "observed_at_event_time": event_time,
        "captured_at": captured_at,
        "provenance_ref": ref,
    }
    if candidate is None:
        return [
            _missing_field(
                group=GROUP_RANKING_CONTEXT,
                field_id="rank_position",
                authority_class=AUTHORITY_RANKING_INPUT,
                unit_or_semantics="b06_ranking_position",
                missing_reason="OPTIONAL_RANKING_CONTEXT_NOT_AVAILABLE",
                **base,
            )
        ]
    fields = [
        _field(
            group=GROUP_RANKING_CONTEXT,
            field_id="rank_position",
            authority_class=AUTHORITY_RANKING_INPUT,
            value=candidate.rank,
            unit_or_semantics="b06_rank_position_zero_for_excluded",
            **base,
        ),
        _field(
            group=GROUP_RANKING_CONTEXT,
            field_id="balanced_movement_score",
            authority_class=AUTHORITY_RANKING_INPUT,
            value=candidate.total_score,
            unit_or_semantics="b06_score_reused_not_recomputed",
            **base,
        ),
        _field(
            group=GROUP_RANKING_CONTEXT,
            field_id="ranking_eligibility_status",
            authority_class=AUTHORITY_RANKING_INPUT,
            value=candidate.eligibility_status,
            unit_or_semantics="b06_candidate_eligibility_status",
            **base,
        ),
    ]
    for key, value in sorted(candidate.tie_break_values.items()):
        fields.append(
            _field(
                group=GROUP_RANKING_CONTEXT,
                field_id=f"b06_tie_break.{key}",
                authority_class=AUTHORITY_RANKING_INPUT,
                value=value,
                unit_or_semantics="b06_order_witness_reused",
                **base,
            )
        )
    return fields


def _instrument_profile(
    *,
    instrument: GovernedUniverseInstrumentV1,
    universe: GovernedFuturesUniverseSnapshotV1,
    economic_md_row: Optional[EconomicMdInstrumentRawInputV1],
    feature_row: Optional[InstrumentRawFeatureProductionV1],
    ranking_row: Optional[RankedCandidateV1],
    economic_md: Optional[EconomicMdInputSnapshotV1],
    features: Optional[RankingFeatureProductionSnapshotV1],
    ranking: Optional[ProductiveFuturesRankingSnapshotV1],
) -> FutureProfileInstrumentSnapshotV1:
    event_time = universe.generated_at_event_time
    captured_at = universe.generated_at_wall_time
    fields: list[FutureProfileFieldV1] = []
    fields.extend(_identity_fields(instrument=instrument, universe=universe))
    fields.extend(
        _economic_md_fields(
            instrument=instrument,
            row=economic_md_row,
            event_time=event_time,
            captured_at=captured_at,
            economic_md=economic_md,
        )
    )
    fields.extend(
        _feature_fields(
            feature_row=feature_row,
            event_time=event_time,
            captured_at=captured_at,
            features=features,
        )
    )
    fields.extend(
        _ranking_fields(
            candidate=ranking_row,
            event_time=event_time,
            captured_at=captured_at,
            ranking=ranking,
        )
    )
    ordered = tuple(sorted(fields, key=lambda row: (row.group, row.field_id)))
    return FutureProfileInstrumentSnapshotV1(
        canonical_instrument_id=instrument.canonical_instrument_id,
        venue_native_id=instrument.venue_native_inst_id,
        profile_state="PROFILE_AVAILABLE",
        fields=ordered,
        profile_field_count=len(ordered),
        profile_only_field_count=sum(
            1 for row in ordered if row.authority_class == AUTHORITY_PROFILE_ONLY
        ),
        unclassified_field_count=sum(
            1 for row in ordered if row.authority_class == AUTHORITY_UNCLASSIFIED
        ),
        ranking_input_field_count=sum(
            1 for row in ordered if row.authority_class == AUTHORITY_RANKING_INPUT
        ),
        eligibility_safety_field_count=sum(
            1 for row in ordered if row.authority_class == AUTHORITY_ELIGIBILITY_SAFETY
        ),
    )


def _coerce_universe(
    universe_snapshot: Mapping[str, Any] | GovernedFuturesUniverseSnapshotV1,
) -> GovernedFuturesUniverseSnapshotV1:
    if isinstance(universe_snapshot, GovernedFuturesUniverseSnapshotV1):
        return universe_snapshot
    return GovernedFuturesUniverseSnapshotV1.from_dict(universe_snapshot)


def build_future_profile_snapshot_v1(
    *,
    universe_snapshot: Mapping[str, Any] | GovernedFuturesUniverseSnapshotV1,
    repository_sha: str,
    profile_observed_at_unix: float,
    economic_md_snapshot: Mapping[str, Any] | EconomicMdInputSnapshotV1 | None = None,
    feature_production_snapshot: Mapping[str, Any]
    | RankingFeatureProductionSnapshotV1
    | None = None,
    ranking_snapshot: Mapping[str, Any] | ProductiveFuturesRankingSnapshotV1 | None = None,
    selection: Mapping[str, Any] | SingleSelectedFutureSelectionV1 | None = None,
) -> FutureProfileSnapshotV1:
    universe = _coerce_universe(universe_snapshot)
    economic_md = (
        economic_md_snapshot
        if isinstance(economic_md_snapshot, EconomicMdInputSnapshotV1)
        else EconomicMdInputSnapshotV1.from_dict(economic_md_snapshot)
        if economic_md_snapshot is not None
        else None
    )
    features = (
        feature_production_snapshot
        if isinstance(feature_production_snapshot, RankingFeatureProductionSnapshotV1)
        else RankingFeatureProductionSnapshotV1.from_dict(feature_production_snapshot)
        if feature_production_snapshot is not None
        else None
    )
    ranking = (
        ranking_snapshot
        if isinstance(ranking_snapshot, ProductiveFuturesRankingSnapshotV1)
        else ProductiveFuturesRankingSnapshotV1.from_dict(ranking_snapshot)
        if ranking_snapshot is not None
        else None
    )
    selected = (
        selection
        if isinstance(selection, SingleSelectedFutureSelectionV1)
        else SingleSelectedFutureSelectionV1.from_dict(selection)
        if selection is not None
        else None
    )

    emd_by_id = _emd_by_id(economic_md)
    features_by_id = _features_by_id(features)
    ranking_by_id = _ranked_by_id(ranking)
    instruments = tuple(
        _instrument_profile(
            instrument=instrument,
            universe=universe,
            economic_md_row=emd_by_id.get(instrument.canonical_instrument_id),
            feature_row=features_by_id.get(instrument.canonical_instrument_id),
            ranking_row=ranking_by_id.get(instrument.canonical_instrument_id),
            economic_md=economic_md,
            features=features,
            ranking=ranking,
        )
        for instrument in sorted(universe.instruments, key=lambda row: row.canonical_instrument_id)
    )
    source_refs = _source_references(
        universe=universe,
        economic_md=economic_md,
        features=features,
        ranking=ranking,
        selection=selected,
    )
    profile_id = compute_profile_snapshot_id_v1(
        repository_sha=repository_sha,
        source_references=source_refs,
        instrument_ids=tuple(row.canonical_instrument_id for row in instruments),
    )
    snapshot = FutureProfileSnapshotV1(
        schema_version=SCHEMA_VERSION,
        capability_id=CAPABILITY_ID,
        producer_version=PRODUCER_VERSION,
        profile_version=PROFILE_VERSION,
        profile_snapshot_id=profile_id,
        repository_sha=repository_sha,
        profile_event_time=universe.generated_at_event_time,
        produced_at_wall_time=_rfc3339(profile_observed_at_unix),
        source_references=source_refs,
        instruments=instruments,
        selected_instrument_reference=_selected_reference(selected),
        authority=authority_block_v1(),
    ).with_integrity_digest()
    validate_future_profile_snapshot_v1(snapshot)
    return snapshot


def get_future_profile_for_instrument_v1(
    snapshot: FutureProfileSnapshotV1,
    *,
    canonical_instrument_id: str,
) -> Optional[FutureProfileInstrumentSnapshotV1]:
    for instrument in snapshot.instruments:
        if instrument.canonical_instrument_id == canonical_instrument_id:
            return instrument
    return None


def get_selected_future_profile_v1(
    snapshot: FutureProfileSnapshotV1,
) -> Optional[FutureProfileInstrumentSnapshotV1]:
    selected_id = str(snapshot.selected_instrument_reference.get("instrument_id") or "")
    if not selected_id:
        return None
    return get_future_profile_for_instrument_v1(
        snapshot,
        canonical_instrument_id=selected_id,
    )


def missing_optional_profile_field_v1(field: FutureProfileFieldV1) -> bool:
    return field.authority_class == AUTHORITY_PROFILE_ONLY and field.availability_state in {
        MISSING,
        NOT_APPLICABLE,
    }
