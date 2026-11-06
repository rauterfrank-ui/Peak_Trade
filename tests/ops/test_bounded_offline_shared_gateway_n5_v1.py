"""Actual five-instrument facts→B05→Cap22→Cap23/24→N5; no synthesized feature scores."""

import pytest

from src.ops.economic_md_input_producer_v1.purpose_gateway_v1 import PurposeBoundEconomicMdGatewayV1
from src.ops.economic_md_input_producer_v1.producer_v1 import produce_economic_md_input_snapshot_v1
from src.ops.peak_trade_ranking_feature_production_v1.producer_v1 import (
    produce_ranking_feature_production_snapshot_v1,
)
from tests.ops.test_bounded_offline_all_purpose_consumers_v1 import _profiles


def test_one_gateway_preserves_all_five_original_numeric_feature_and_n5_results(
    tmp_path, monkeypatch
):
    from tests.ops import (
        test_current_mf_n5_boundary_occupied_lane_cap24_n1_bind_join_v1 as fixtures,
    )
    from tests.ops.test_current_mf_n5_full_autonomy_productive_runtime_orchestrator_v1 import (
        _run_orchestrator,
    )

    observations = []

    def from_facts(universe):
        routes = {}
        now_ms = int(fixtures.OBSERVED_UNIX * 1000)
        for instrument in universe["instruments"]:
            if not instrument["eligibility"]:
                continue
            native = instrument["venue_native_inst_id"]
            routes[native] = _profiles(
                tmp_path / "public-store",
                canonical=instrument["canonical_instrument_id"],
                native=native,
                now_ms=now_ms,
                last_ms=now_ms // 60000 * 60000,
            )
        gateway = PurposeBoundEconomicMdGatewayV1(routes, now_ms)
        with pytest.raises(ValueError, match="INSTRUMENT_UNBOUND"):
            gateway.collect_instrument_raw_input_v1(venue_native_id="FOREIGN-USDT-SWAP")
        original_digest = gateway.profile_digest_v1()
        routes.clear()
        assert gateway.profile_digest_v1() == original_digest
        economic = produce_economic_md_input_snapshot_v1(
            universe_snapshot=universe,
            public_md_source=gateway,
            collection_started_at_unix=fixtures.OBSERVED_UNIX - 1,
            collection_completed_at_unix=fixtures.OBSERVED_UNIX,
        )
        assert not economic.snapshot.failure_codes, economic.snapshot.failure_codes
        features = produce_ranking_feature_production_snapshot_v1(
            economic.snapshot, observed_age_seconds=0
        )
        assert features.instrument_count_feature_ready == 5
        observations.append((gateway, economic.snapshot, features))
        return features

    monkeypatch.setattr(fixtures, "synthesize_ready_feature_production_snapshot_v1", from_facts)
    natives = ["SOL-USDT-SWAP", "ETH-USDT-SWAP", "ADA-USDT-SWAP", "LINK-USDT-SWAP", "APT-USDT-SWAP"]
    result = _run_orchestrator(
        tmp_path, instrument_rows=natives, target_cardinality=5, include_host_completion_rollup=True
    )
    assert len(observations) == 1 and len(result.lane_rollups) == 5
    assert len({r.cursor_store_root for r in result.lane_rollups}) == 5
    assert result.completion_result.productive_runtime_cardinality == "5_JOINED"
    assert not result.external_effect_authorized and not result.post_allowed
    assert all(not r.permit_created and r.post_count == 0 for r in result.lane_rollups)
