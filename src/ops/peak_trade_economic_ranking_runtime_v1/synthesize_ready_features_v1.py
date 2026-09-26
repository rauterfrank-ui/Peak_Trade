"""Test/offline helper: synthesize READY B05 feature rows for Cap-2.1-eligible instruments.

When all instruments receive identical ready feature values, B03 ordering reduces to the
ratified venue_native_id ASC final fallback — preserving Cap 2.3 consumer test fixtures
that previously depended on structural ties.
"""

from __future__ import annotations

from typing import Any, Mapping

from src.ops.peak_trade_ranking_feature_contract_v1 import (
    RankingFeatureValueState,
    RawRankingFeatureValueV1,
    RATIFIED_FEATURE_DIRECTIONS,
    RATIFIED_FEATURE_UNITS,
    RATIFIED_RAW_NORMALIZATION,
    build_policy_identity_v1,
    neutral_input2_provenance_v1,
)
from src.ops.peak_trade_ranking_feature_production_v1.constants_v1 import (
    CAPABILITY_ID,
    OBSERVATION_WINDOW_ID,
    PRODUCTION_VERSION,
    SCHEMA_VERSION,
)
from src.ops.peak_trade_ranking_feature_production_v1.models_v1 import (
    InstrumentMarkWindowProvenanceV1,
    InstrumentRawFeatureProductionV1,
    RankingFeatureProductionSnapshotV1,
)
from src.ops.peak_trade_ranking_feature_production_v1.producer_v1 import authority_block_v1
from src.ops.peak_trade_ranking_matrix_policy_v1 import AMPLITUDE_POLICY_ID, VOLATILITY_POLICY_ID
from src.ops.productive_futures_ranking_producer_v1.policy_v1 import (
    compute_score_components_v1,
    is_ranking_eligible_v1,
)


def _ready(feature_policy_id: str, value: float) -> RawRankingFeatureValueV1:
    return RawRankingFeatureValueV1(
        feature_policy_id=feature_policy_id,
        state=RankingFeatureValueState.READY,
        raw_value=float(value),
        units=RATIFIED_FEATURE_UNITS[feature_policy_id],
        direction=RATIFIED_FEATURE_DIRECTIONS[feature_policy_id],
        observation_window_id=OBSERVATION_WINDOW_ID,
        raw_feature_normalization=RATIFIED_RAW_NORMALIZATION[feature_policy_id],
        reason_code=None,
    )


def synthesize_ready_feature_production_snapshot_v1(
    universe_snapshot: Mapping[str, Any],
    *,
    volatility_by_id: Mapping[str, float] | None = None,
    amplitude_by_id: Mapping[str, float] | None = None,
    default_volatility: float = 0.01,
    default_amplitude: float = 0.02,
    collection_cycle_id: str = "synth_emd_cycle",
    economic_input_snapshot_id: str = "synth_emd_snap",
    economic_input_snapshot_digest: str = "synth_emd_digest",
    observed_at_event_time: str = "2026-09-26T00:00:00Z",
) -> RankingFeatureProductionSnapshotV1:
    vol_map = dict(volatility_by_id or {})
    amp_map = dict(amplitude_by_id or {})
    instruments: list[InstrumentRawFeatureProductionV1] = []
    for row in universe_snapshot.get("instruments") or ():
        components = compute_score_components_v1(row)
        if not is_ranking_eligible_v1(components):
            continue
        cid = str(row.get("canonical_instrument_id") or "")
        vid = str(row.get("venue_native_inst_id") or row.get("venue_native_id") or "")
        vol = float(vol_map.get(cid, default_volatility))
        amp = float(amp_map.get(cid, default_amplitude))
        instruments.append(
            InstrumentRawFeatureProductionV1(
                canonical_instrument_id=cid,
                venue_native_id=vid,
                raw_features=(_ready(VOLATILITY_POLICY_ID, vol), _ready(AMPLITUDE_POLICY_ID, amp)),
                feature_production_ready=True,
                mark_window_provenance=InstrumentMarkWindowProvenanceV1(
                    observation_window_id=OBSERVATION_WINDOW_ID,
                    as_of_event_time="1700000000000",
                    source_class="SYNTHETIC_TEST_READY_FEATURES",
                    source_endpoint="synthetic",
                    mark_count=61,
                    event_timestamps=tuple(str(1_700_000_000_000 + i * 60_000) for i in range(61)),
                ),
                exclusion_reason_codes=(),
                economic_md_raw_input_digest=f"synth_{cid}",
            )
        )
    ordered = tuple(sorted(instruments, key=lambda r: r.canonical_instrument_id))
    snap = RankingFeatureProductionSnapshotV1(
        schema_version=SCHEMA_VERSION,
        production_version=PRODUCTION_VERSION,
        capability_id=CAPABILITY_ID,
        production_snapshot_id="synth_rfp_1",
        policy_identity=build_policy_identity_v1(),
        input2_provenance=neutral_input2_provenance_v1(
            economic_input_snapshot_id=economic_input_snapshot_id,
            economic_input_snapshot_digest=economic_input_snapshot_digest,
            collection_cycle_id=collection_cycle_id,
            observed_at_event_time=observed_at_event_time,
        ),
        instruments=ordered,
        instrument_count_requested=len(ordered),
        instrument_count_feature_ready=len(ordered),
        production_digest="",
        authority=authority_block_v1(),
        call_graph=("synthesize_ready_feature_production_snapshot_v1",),
    )
    return snap.with_production_digest()
