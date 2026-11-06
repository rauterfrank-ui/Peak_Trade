"""E1 units control at the original numeric feature and ranking consumers."""

from dataclasses import replace

import pytest

from src.ops.economic_md_input_producer_v1.producer_v1 import produce_economic_md_input_snapshot_v1
from src.ops.economic_md_input_producer_v1.purpose_gateway_v1 import PurposeBoundEconomicMdGatewayV1
from src.ops.peak_trade_ranking_feature_production_v1.producer_v1 import (
    produce_ranking_feature_production_snapshot_v1,
    validate_ranking_feature_production_snapshot_v1,
)
from src.ops.productive_futures_ranking_producer_v1.producer_v1 import (
    produce_productive_futures_ranking_v1,
)
from tests.ops import test_current_mf_n5_boundary_occupied_lane_cap24_n1_bind_join_v1 as fixtures
from tests.ops.test_bounded_offline_all_purpose_consumers_v1 import _profiles


def test_rehashed_annualized_sigma_is_rejected_by_actual_ranker(tmp_path):
    rows = fixtures._five_rows()
    universe = fixtures.produce_governed_futures_universe_v1(
        source_payload=fixtures._payload(rows),
        mark_price_payload=fixtures._marks(*(r["instId"] for r in rows)),
        repository_sha=fixtures.REPO_SHA,
        producer_observed_at_unix=fixtures.OBSERVED_UNIX,
        source_event_time=fixtures.SOURCE_EVENT,
    ).snapshot.to_dict()
    now = int(fixtures.OBSERVED_UNIX * 1000)
    sources = {
        row["venue_native_inst_id"]: _profiles(
            tmp_path / "facts",
            canonical=row["canonical_instrument_id"],
            native=row["venue_native_inst_id"],
            now_ms=now,
            last_ms=now // 60000 * 60000,
        )
        for row in universe["instruments"]
        if row["eligibility"]
    }
    economic = produce_economic_md_input_snapshot_v1(
        universe_snapshot=universe,
        public_md_source=PurposeBoundEconomicMdGatewayV1(sources, now),
        collection_started_at_unix=fixtures.OBSERVED_UNIX - 1,
        collection_completed_at_unix=fixtures.OBSERVED_UNIX,
    )
    features = produce_ranking_feature_production_snapshot_v1(economic.snapshot)

    def rank(snapshot):
        return produce_productive_futures_ranking_v1(
            universe_snapshot=universe,
            feature_production_snapshot=snapshot,
            repository_sha=fixtures.REPO_SHA,
            producer_observed_at_unix=fixtures.OBSERVED_UNIX,
        )

    assert not rank(features).failure_codes
    row = features.instruments[0]
    sigma = row.raw_features[0]
    annualized = replace(sigma, raw_value=sigma.raw_value * 725, units="ANNUALIZED_SIGMA")
    changed = replace(row, raw_features=(annualized, *row.raw_features[1:]))
    bad = replace(
        features, instruments=(changed, *features.instruments[1:])
    ).with_production_digest()
    assert bad.production_digest == bad.compute_production_digest()
    with pytest.raises(ValueError, match="FEATURE_UNITS_MISMATCH"):
        validate_ranking_feature_production_snapshot_v1(bad)
    rejected = rank(bad)
    assert rejected.failure_codes == ("ECONOMIC_FEATURE_PRODUCTION_SNAPSHOT_INVALID",)
    assert not rejected.snapshot.ranked_candidates
