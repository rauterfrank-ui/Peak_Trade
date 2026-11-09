"""Current relative movement ranking is not an absolute profit/survival claim."""

import pytest

from src.ops.peak_trade_economic_ranking_runtime_v1.synthesize_ready_features_v1 import (
    synthesize_ready_feature_production_snapshot_v1,
)
from src.ops.productive_futures_ranking_producer_v1.producer_v1 import (
    produce_productive_futures_ranking_v1,
)
from tests.ops.test_peak_trade_economic_ranking_runtime_v1 import (
    _universe,
    _perp,
    _cid,
    REPO_SHA,
    OBSERVED_UNIX,
)


@pytest.mark.parametrize("scale", [0.1, 0.001, 0.000001])
def test_uniformly_weaker_mark_movement_keeps_relative_order_without_proving_cost_cover(scale):
    universe = _universe(
        [_perp(), _perp("SOL-USDT-SWAP", base="SOL"), _perp("ADA-USDT-SWAP", base="ADA")]
    )
    ids = [_cid(universe, native) for native in ("ETH-USDT-SWAP", "SOL-USDT-SWAP", "ADA-USDT-SWAP")]

    def rank(factor):
        # Explicit synthetic, already admissible raw feature inputs. Ratified
        # percentiles and actual Cap22 producer do all scoring; no new policy.
        features = synthesize_ready_feature_production_snapshot_v1(
            universe,
            volatility_by_id={cid: factor * value for cid, value in zip(ids, (0.03, 0.02, 0.01))},
            amplitude_by_id={cid: factor * value for cid, value in zip(ids, (0.08, 0.04, 0.02))},
        )
        result = produce_productive_futures_ranking_v1(
            universe_snapshot=universe,
            feature_production_snapshot=features,
            repository_sha=REPO_SHA,
            producer_observed_at_unix=OBSERVED_UNIX,
        )
        assert result.snapshot.eligible_candidate_count == 3
        return result.snapshot

    original, weakened = rank(1.0), rank(scale)

    def projected(snapshot):
        return [
            (row.canonical_instrument_id, row.rank, row.total_score)
            for row in snapshot.ranked_candidates
        ]

    assert projected(weakened) == projected(original)
    assert [row.canonical_instrument_id for row in weakened.ranked_candidates] == ids
    # Different source inputs remain different evidence despite equal order.
    assert weakened.integrity_digest != original.integrity_digest
    assert not weakened.alpha_allowed and not weakened.selection_authority_created
