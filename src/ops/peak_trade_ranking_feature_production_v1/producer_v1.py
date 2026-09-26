"""B05 producer: Cap-2.1 / Input-2 ranking raw-feature production.

Consumes CURRENT Economic-MD Input snapshots, populates B04 raw feature DTOs,
and never ranks, selects, normalizes cross-sectionally, or activates economic rank.
"""

from __future__ import annotations

import ast
from decimal import Decimal
from pathlib import Path
from typing import Any, Mapping, Optional, Sequence

from src.ops.archive_sibling_export_contract_v1.canonical_digest import (
    canonical_digest_v1,
)
from src.ops.economic_md_input_producer_v1.models_v1 import (
    EconomicMdInputSnapshotV1,
    EconomicMdInstrumentRawInputV1,
)
from src.ops.peak_trade_ranking_feature_contract_v1 import (
    INPUT2_MAX_AGE_SECONDS,
    INPUT2_MAX_AGE_SECONDS_RATIFIED,
    Input2FreshnessObservation,
    RankingFeatureValueState,
    RawRankingFeatureValueV1,
    RATIFIED_ECONOMIC_FEATURE_POLICY_IDS,
    RATIFIED_FEATURE_DIRECTIONS,
    RATIFIED_FEATURE_UNITS,
    RATIFIED_RAW_NORMALIZATION,
    build_policy_identity_v1,
    neutral_input2_provenance_v1,
    validate_raw_feature_value_v1,
)
from src.ops.peak_trade_ranking_feature_production_v1.constants_v1 import (
    AUTHORITY_EFFECT,
    B05_IMPLEMENTED,
    BINDING_EFFECT,
    CALL_GRAPH,
    CAP23_SOLE_SELECTION_OWNER,
    CAPABILITY_ID,
    CROSS_UNIVERSE_AUTHORITY,
    ECONOMIC_RANK_ACTIVATED,
    FORBIDDEN_CALL_GRAPH_TARGETS,
    FORBIDDEN_OUTPUT_FIELDS,
    MARK_COUNT,
    MAX_POSITIONS_EFFECTIVE,
    MULTI_FUTURE_RUNTIME_AUTHORIZED,
    OBSERVATION_WINDOW_ID,
    OWNER_GO_THIS_SLICE,
    PRODUCTIVE_ECONOMIC_RANK_ACTIVATION,
    PRODUCTIVE_SELECTION_OWNER,
    PRODUCTION_VERSION,
    RANKING_ACTIVATION,
    RUNTIME_AUTHORIZATION_EFFECT,
    RUNTIME_WIRING_ADDED,
    SCHEMA_VERSION,
    SELECTION_AUTHORITY_CREATED,
)
from src.ops.peak_trade_ranking_feature_production_v1.marks_window_v1 import (
    extract_contiguous_finalized_pt1m_mark_window_v1,
)
from src.ops.peak_trade_ranking_feature_production_v1.models_v1 import (
    InstrumentMarkWindowProvenanceV1,
    InstrumentRawFeatureProductionV1,
    RankingFeatureProductionSnapshotV1,
    compute_production_snapshot_id_v1,
)
from src.ops.peak_trade_ranking_feature_production_v1.pure_compute_v1 import (
    RankingFeaturePureComputeError,
    population_sigma_log_returns_v1,
    pt1m_mid_relative_range_v1,
)
from src.ops.peak_trade_ranking_feature_production_v1.reason_codes_v1 import (
    RankingFeatureProductionReasonCodeV1,
)
from src.ops.peak_trade_ranking_matrix_policy_v1 import (
    AMPLITUDE_POLICY_ID,
    VOLATILITY_POLICY_ID,
)


class RankingFeatureProductionError(ValueError):
    """Fail-closed B05 production error."""

    def __init__(self, code: str, detail: str = "") -> None:
        super().__init__(f"{code}:{detail}" if detail else code)
        self.code = code
        self.detail = detail


def authority_block_v1() -> dict[str, Any]:
    return {
        "AUTHORITY_EFFECT": AUTHORITY_EFFECT,
        "B05_IMPLEMENTED": B05_IMPLEMENTED,
        "BINDING_EFFECT": BINDING_EFFECT,
        "CAP23_SOLE_SELECTION_OWNER": CAP23_SOLE_SELECTION_OWNER,
        "CROSS_UNIVERSE_AUTHORITY": CROSS_UNIVERSE_AUTHORITY,
        "ECONOMIC_RANK_ACTIVATED": ECONOMIC_RANK_ACTIVATED,
        "INPUT2_MAX_AGE_SECONDS": INPUT2_MAX_AGE_SECONDS,
        "INPUT2_MAX_AGE_SECONDS_RATIFIED": INPUT2_MAX_AGE_SECONDS_RATIFIED,
        "MAX_POSITIONS_EFFECTIVE": MAX_POSITIONS_EFFECTIVE,
        "MULTI_FUTURE_RUNTIME_AUTHORIZED": MULTI_FUTURE_RUNTIME_AUTHORIZED,
        "PRODUCTIVE_ECONOMIC_RANK_ACTIVATION": PRODUCTIVE_ECONOMIC_RANK_ACTIVATION,
        "PRODUCTIVE_SELECTION_OWNER": PRODUCTIVE_SELECTION_OWNER,
        "RANKING_ACTIVATION": RANKING_ACTIVATION,
        "RUNTIME_AUTHORIZATION_EFFECT": RUNTIME_AUTHORIZATION_EFFECT,
        "RUNTIME_WIRING_ADDED": RUNTIME_WIRING_ADDED,
        "SELECTION_AUTHORITY_CREATED": SELECTION_AUTHORITY_CREATED,
    }


def classify_peak_trade_ranking_feature_production_v1() -> dict[str, Any]:
    return {
        **authority_block_v1(),
        "b05_implemented": B05_IMPLEMENTED,
        "capability_id": CAPABILITY_ID,
        "canonical_economic_md_producer": ("src.ops.economic_md_input_producer_v1"),
        "owner_go_this_slice": OWNER_GO_THIS_SLICE,
        "production_version": PRODUCTION_VERSION,
        "ratified_economic_feature_policy_ids": list(RATIFIED_ECONOMIC_FEATURE_POLICY_IDS),
        "schema_version": SCHEMA_VERSION,
    }


def _state_for_reason(code: RankingFeatureProductionReasonCodeV1) -> RankingFeatureValueState:
    if code == RankingFeatureProductionReasonCodeV1.MISSING_MARK_PRICE:
        return RankingFeatureValueState.MISSING
    if code == RankingFeatureProductionReasonCodeV1.INSUFFICIENT_PT1M_MARK_WARMUP:
        return RankingFeatureValueState.INCOMPLETE_WARMUP
    return RankingFeatureValueState.INVALID


def _non_ready_feature(
    feature_policy_id: str,
    *,
    state: RankingFeatureValueState,
    reason_code: str,
) -> RawRankingFeatureValueV1:
    return RawRankingFeatureValueV1(
        feature_policy_id=feature_policy_id,
        state=state,
        raw_value=None,
        units=RATIFIED_FEATURE_UNITS[feature_policy_id],
        direction=RATIFIED_FEATURE_DIRECTIONS[feature_policy_id],
        observation_window_id=OBSERVATION_WINDOW_ID,
        raw_feature_normalization=RATIFIED_RAW_NORMALIZATION[feature_policy_id],
        reason_code=reason_code,
    )


def _ready_feature(feature_policy_id: str, value: Decimal) -> RawRankingFeatureValueV1:
    as_float = float(value)
    if as_float != as_float or as_float in (float("inf"), float("-inf")):
        raise RankingFeatureProductionError("NON_FINITE_FEATURE_VALUE", feature_policy_id)
    return RawRankingFeatureValueV1(
        feature_policy_id=feature_policy_id,
        state=RankingFeatureValueState.READY,
        raw_value=as_float,
        units=RATIFIED_FEATURE_UNITS[feature_policy_id],
        direction=RATIFIED_FEATURE_DIRECTIONS[feature_policy_id],
        observation_window_id=OBSERVATION_WINDOW_ID,
        raw_feature_normalization=RATIFIED_RAW_NORMALIZATION[feature_policy_id],
        reason_code=None,
    )


def _pair_from_reason(
    code: RankingFeatureProductionReasonCodeV1,
) -> tuple[RawRankingFeatureValueV1, RawRankingFeatureValueV1]:
    state = _state_for_reason(code)
    reason = code.value
    return (
        _non_ready_feature(VOLATILITY_POLICY_ID, state=state, reason_code=reason),
        _non_ready_feature(AMPLITUDE_POLICY_ID, state=state, reason_code=reason),
    )


def compute_b03_ratified_raw_features_pure_v1(
    mark_px: tuple[str, ...],
) -> tuple[RawRankingFeatureValueV1, RawRankingFeatureValueV1]:
    """Shared pure seam for research/backtest/shadow/productive parity (B09)."""
    try:
        vol = population_sigma_log_returns_v1(mark_px)
        amp = pt1m_mid_relative_range_v1(mark_px)
    except RankingFeaturePureComputeError as exc:
        return _pair_from_reason(exc.reason_code)
    except Exception:
        return _pair_from_reason(RankingFeatureProductionReasonCodeV1.COMPUTE_ERROR)
    return (
        _ready_feature(VOLATILITY_POLICY_ID, vol),
        _ready_feature(AMPLITUDE_POLICY_ID, amp),
    )


def produce_raw_ranking_features_for_instrument_v1(
    instrument: EconomicMdInstrumentRawInputV1,
) -> InstrumentRawFeatureProductionV1:
    extraction = extract_contiguous_finalized_pt1m_mark_window_v1(instrument.finalized_pt1m_marks)
    if not extraction.ok or extraction.window is None:
        reason = extraction.reason_code or RankingFeatureProductionReasonCodeV1.MISSING_MARK_PRICE
        raw = _pair_from_reason(reason)
        for row in raw:
            validate_raw_feature_value_v1(row)
        return InstrumentRawFeatureProductionV1(
            canonical_instrument_id=instrument.canonical_instrument_id,
            venue_native_id=instrument.venue_native_id,
            raw_features=raw,
            feature_production_ready=False,
            mark_window_provenance=None,
            exclusion_reason_codes=(reason.value,),
            economic_md_raw_input_digest=instrument.raw_input_digest,
        )

    window = extraction.window
    raw = compute_b03_ratified_raw_features_pure_v1(window.mark_px)
    for row in raw:
        validate_raw_feature_value_v1(row)
    ready = all(row.state == RankingFeatureValueState.READY for row in raw)
    exclusion: tuple[str, ...] = ()
    if not ready:
        exclusion = tuple(sorted({str(row.reason_code) for row in raw if row.reason_code}))
    provenance = InstrumentMarkWindowProvenanceV1(
        observation_window_id=OBSERVATION_WINDOW_ID,
        as_of_event_time=window.as_of_event_time,
        source_class=window.source_class,
        source_endpoint=window.source_endpoint,
        mark_count=MARK_COUNT,
        event_timestamps=window.event_timestamps,
    )
    return InstrumentRawFeatureProductionV1(
        canonical_instrument_id=instrument.canonical_instrument_id,
        venue_native_id=instrument.venue_native_id,
        raw_features=raw,
        feature_production_ready=ready,
        mark_window_provenance=provenance if ready else provenance,
        exclusion_reason_codes=exclusion,
        economic_md_raw_input_digest=instrument.raw_input_digest,
    )


def build_input2_provenance_from_snapshot_v1(
    snapshot: EconomicMdInputSnapshotV1,
    *,
    observed_age_seconds: Optional[float] = None,
) -> Any:
    freshness = Input2FreshnessObservation.NOT_OBSERVED
    if observed_age_seconds is not None:
        freshness = Input2FreshnessObservation.AGE_OBSERVED
    return neutral_input2_provenance_v1(
        economic_input_snapshot_id=snapshot.economic_input_snapshot_id,
        economic_input_snapshot_digest=snapshot.payload_digest,
        collection_cycle_id=snapshot.collection_cycle_identity,
        observed_at_event_time=snapshot.collection_completed_at,
        observed_age_seconds=observed_age_seconds,
        freshness_observation=freshness,
    )


def _instrument_feature_digest(row: InstrumentRawFeatureProductionV1) -> str:
    return canonical_digest_v1(row.to_dict())


def produce_ranking_feature_production_snapshot_v1(
    economic_md_snapshot: EconomicMdInputSnapshotV1,
    *,
    observed_age_seconds: Optional[float] = None,
) -> RankingFeatureProductionSnapshotV1:
    if economic_md_snapshot.payload_digest != economic_md_snapshot.compute_payload_digest():
        raise RankingFeatureProductionError("CORRUPT_ECONOMIC_MD_SNAPSHOT_DIGEST")

    produced: list[InstrumentRawFeatureProductionV1] = []
    for instrument in economic_md_snapshot.instruments:
        produced.append(produce_raw_ranking_features_for_instrument_v1(instrument))

    ordered = tuple(sorted(produced, key=lambda row: row.canonical_instrument_id))
    feature_digests = [_instrument_feature_digest(row) for row in ordered]
    production_snapshot_id = compute_production_snapshot_id_v1(
        economic_input_snapshot_id=economic_md_snapshot.economic_input_snapshot_id,
        economic_input_snapshot_digest=economic_md_snapshot.payload_digest,
        instrument_feature_digests=feature_digests,
    )
    ready_count = sum(1 for row in ordered if row.feature_production_ready)
    snapshot = RankingFeatureProductionSnapshotV1(
        schema_version=SCHEMA_VERSION,
        production_version=PRODUCTION_VERSION,
        capability_id=CAPABILITY_ID,
        production_snapshot_id=production_snapshot_id,
        policy_identity=build_policy_identity_v1(),
        input2_provenance=build_input2_provenance_from_snapshot_v1(
            economic_md_snapshot,
            observed_age_seconds=observed_age_seconds,
        ),
        instruments=ordered,
        instrument_count_requested=len(ordered),
        instrument_count_feature_ready=ready_count,
        production_digest="",
        authority=authority_block_v1(),
        call_graph=CALL_GRAPH,
    )
    return snapshot.with_production_digest()


def validate_ranking_feature_production_snapshot_v1(
    snapshot: RankingFeatureProductionSnapshotV1,
) -> None:
    if snapshot.schema_version != SCHEMA_VERSION:
        raise RankingFeatureProductionError("SCHEMA_VERSION_MISMATCH")
    if snapshot.capability_id != CAPABILITY_ID:
        raise RankingFeatureProductionError("CAPABILITY_ID_MISMATCH")
    if snapshot.production_digest != snapshot.compute_production_digest():
        raise RankingFeatureProductionError("PRODUCTION_DIGEST_MISMATCH")
    if snapshot.input2_provenance.input2_max_age_seconds != INPUT2_MAX_AGE_SECONDS:
        raise RankingFeatureProductionError("INPUT2_MAX_AGE_MUST_REMAIN_UNRATIFIED")
    if snapshot.input2_provenance.input2_max_age_seconds_ratified is not False:
        raise RankingFeatureProductionError("INPUT2_MAX_AGE_RATIFICATION_FORBIDDEN")
    auth = snapshot.authority or authority_block_v1()
    if auth.get("PRODUCTIVE_ECONOMIC_RANK_ACTIVATION"):
        raise RankingFeatureProductionError("PRODUCTIVE_ACTIVATION_FORBIDDEN")
    if auth.get("ECONOMIC_RANK_ACTIVATED"):
        raise RankingFeatureProductionError("ECONOMIC_RANK_ACTIVATED_FORBIDDEN")
    if auth.get("SELECTION_AUTHORITY_CREATED"):
        raise RankingFeatureProductionError("SELECTION_AUTHORITY_FORBIDDEN")
    if auth.get("BINDING_EFFECT"):
        raise RankingFeatureProductionError("BINDING_EFFECT_FORBIDDEN")
    if auth.get("RANKING_ACTIVATION"):
        raise RankingFeatureProductionError("RANKING_ACTIVATION_FORBIDDEN")

    serialized = snapshot.to_dict()
    for forbidden in FORBIDDEN_OUTPUT_FIELDS:
        if forbidden in serialized:
            raise RankingFeatureProductionError("FORBIDDEN_OUTPUT_FIELD", forbidden)
        for instrument in serialized.get("instruments") or []:
            if isinstance(instrument, Mapping) and forbidden in instrument:
                raise RankingFeatureProductionError("FORBIDDEN_OUTPUT_FIELD", forbidden)

    seen: set[str] = set()
    ready = 0
    for instrument in snapshot.instruments:
        if instrument.canonical_instrument_id in seen:
            raise RankingFeatureProductionError("DUPLICATE_INSTRUMENT")
        seen.add(instrument.canonical_instrument_id)
        raw_ids = [row.feature_policy_id for row in instrument.raw_features]
        if tuple(raw_ids) != RATIFIED_ECONOMIC_FEATURE_POLICY_IDS:
            raise RankingFeatureProductionError("RATIFIED_RAW_FEATURE_SET_ORDER_MISMATCH")
        for row in instrument.raw_features:
            validate_raw_feature_value_v1(row)
        if instrument.feature_production_ready:
            if any(row.state != RankingFeatureValueState.READY for row in instrument.raw_features):
                raise RankingFeatureProductionError("READY_FLAG_DRIFT")
            ready += 1
        else:
            if all(row.state == RankingFeatureValueState.READY for row in instrument.raw_features):
                raise RankingFeatureProductionError("NON_READY_FLAG_DRIFT")
    if ready != snapshot.instrument_count_feature_ready:
        raise RankingFeatureProductionError("FEATURE_READY_COUNT_MISMATCH")


def assert_no_forbidden_call_graph_imports_v1(module_paths: Sequence[Path]) -> None:
    for path in module_paths:
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            names: list[str] = []
            if isinstance(node, ast.Import):
                names.extend(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                names.append(node.module)
            for name in names:
                lowered = name.lower()
                for forbidden in FORBIDDEN_CALL_GRAPH_TARGETS:
                    if forbidden.lower() in lowered:
                        raise RankingFeatureProductionError(
                            "FORBIDDEN_IMPORT",
                            f"{path.name}:{forbidden}",
                        )
