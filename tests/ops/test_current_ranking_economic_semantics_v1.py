"""Current relative movement ranking is not an absolute profit/survival claim."""

from decimal import Decimal
from datetime import datetime, timezone

import pytest

from src.ops.mf_membership_context_artifact_contract_v1 import (
    build_membership_context_artifact_v1,
    read_membership_context_artifact_v1,
    write_membership_context_artifact_v1,
)
from src.ops.mf_membership_selector_and_rotation_runtime_contract_v1 import (
    STATUS_CHANGED,
    STATUS_UNCHANGED_REPLAY,
    run_isolated_selector_cycle_v1,
)
from src.ops.peak_trade_ranking_feature_production_v1.pure_compute_v1 import (
    population_sigma_log_returns_v1,
    pt1m_mid_relative_range_v1,
)
from src.ops.peak_trade_economic_ranking_runtime_v1.synthesize_ready_features_v1 import (
    synthesize_ready_feature_production_snapshot_v1,
)
from src.ops.productive_futures_ranking_producer_v1.producer_v1 import (
    produce_productive_futures_ranking_v1,
    run_productive_futures_ranking_producer_v1,
)
from src.ops.productive_futures_ranking_producer_v1.models_v1 import (
    compute_ranking_snapshot_id_v1,
)
from src.ops.productive_futures_ranking_producer_v1.persistence_v1 import (
    load_and_validate_ranking_snapshot_v1,
)
from tests.ops.test_peak_trade_economic_ranking_runtime_v1 import (
    _universe,
    _perp,
    _cid,
    REPO_SHA,
    OBSERVED_UNIX,
)
from tests.test_mf_membership_selector_and_rotation_runtime_contract_v1 import _provenance


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
    assert weakened.ranking_snapshot_id != original.ranking_snapshot_id
    assert not weakened.alpha_allowed and not weakened.selection_authority_created


@pytest.mark.parametrize("all_flat", [False, True], ids=["one-instrument-stalls", "all-stall"])
def test_measured_motion_reaches_original_rotation_with_holding_and_cold_read(tmp_path, all_flat):
    """Pure mark metrics → original Cap22 → durable original MF selector.

    Explicit synthetic closed mark windows; this proves the connected numerical
    and membership behavior, not public-fact admission, venue custody or a host.
    """
    bases = ("ETH", "SOL", "ADA", "AVAX", "BCH", "DOT")
    universe = _universe([_perp(f"{base}-USDT-SWAP", base=base, ctValCcy=base) for base in bases])
    ids = [_cid(universe, f"{base}-USDT-SWAP") for base in bases]

    def ranking(magnitudes, observation):
        # Alternating marks have both nonzero return dispersion and amplitude.
        # Zero magnitude represents a truly motionless, otherwise valid window.
        windows = {
            cid: tuple(str(Decimal(100) + Decimal(m) * (i % 2)) for i in range(61))
            for cid, m in zip(ids, magnitudes)
        }
        volatility = {
            cid: float(population_sigma_log_returns_v1(window)) for cid, window in windows.items()
        }
        amplitude = {
            cid: float(pt1m_mid_relative_range_v1(window)) for cid, window in windows.items()
        }
        for cid, magnitude in zip(ids, magnitudes):
            if magnitude == 0:
                assert volatility[cid] == amplitude[cid] == 0.0
        features = synthesize_ready_feature_production_snapshot_v1(
            universe,
            volatility_by_id=volatility,
            amplitude_by_id=amplitude,
            collection_cycle_id=f"synthetic-mark-window-{observation}",
            observed_at_event_time=datetime.fromtimestamp(
                OBSERVED_UNIX + observation, tz=timezone.utc
            ).isoformat(),
        )
        produced = produce_productive_futures_ranking_v1(
            universe_snapshot=universe,
            feature_production_snapshot=features,
            repository_sha=REPO_SHA,
            producer_observed_at_unix=OBSERVED_UNIX + observation,
        )
        assert produced.ok, produced.failure_codes
        assert produced.snapshot.eligible_candidate_count == 6
        return produced.snapshot.to_dict()

    def cycle(prior, snapshot):
        # Same selector called by current_productive_post_close_feedback_v1;
        # the original writer/readback maintains its own observation history.
        return run_isolated_selector_cycle_v1(
            snapshot=snapshot,
            cap22_provenance=_provenance(snapshot),
            prior=prior,
            store_root=tmp_path,
            persist=True,
        )

    first = ranking((6, 5, 4, 3, 2, 1), 0)
    assert [row["canonical_instrument_id"] for row in first["ranked_candidates"]] == ids
    initial = write_membership_context_artifact_v1(
        build_membership_context_artifact_v1(
            ordered_instrument_ids=ids[:5],
            cap22_provenance=_provenance(first),
            bootstrap=True,
            prior_membership_reference=None,
        ),
        store_root=tmp_path,
    )
    changed = ranking((0, 0, 0, 0, 0, 0) if all_flat else (0, 5, 4, 3, 2, 1), 60)
    protected = cycle(initial, changed)
    assert set(protected.ordered_membership) == set(ids[:5])
    assert protected.rotation_delta["exited"] == protected.rotation_delta["entered"] == []
    readback = read_membership_context_artifact_v1(
        protected.persisted_artifact.instance_id, store_root=tmp_path
    )
    replay = cycle(readback, changed)
    assert replay.decision_status == STATUS_UNCHANGED_REPLAY
    assert replay.persisted_artifact is None
    eligible_after_hold = ranking((0, 0, 0, 0, 0, 0) if all_flat else (0, 5, 4, 3, 2, 1), 120)
    rotated = cycle(readback, eligible_after_hold)
    assert rotated.decision_status == STATUS_CHANGED
    assert rotated.holding_ages[ids[0]] == 2
    if all_flat:
        # A relative rank still exists, using native-ID tie-breaks. Rotation
        # may change tied members; that proves no absolute cost gate here.
        assert all(row["total_score"] == 0.5 for row in eligible_after_hold["ranked_candidates"])
        expected = tuple(
            row["canonical_instrument_id"] for row in eligible_after_hold["ranked_candidates"][:5]
        )
        assert rotated.ordered_membership == expected
    else:
        assert rotated.rotation_delta["exited"] == [ids[0]]
        assert rotated.rotation_delta["entered"] == [ids[5]]
        assert rotated.ordered_membership == tuple(ids[1:])
    assert (
        read_membership_context_artifact_v1(
            rotated.persisted_artifact.instance_id, store_root=tmp_path
        ).ordered_instrument_ids
        == rotated.ordered_membership
    )


def test_recompute_clock_alone_is_not_a_new_economic_ranking_observation():
    universe = _universe([_perp(), _perp("SOL-USDT-SWAP", base="SOL", ctValCcy="SOL")])
    features = synthesize_ready_feature_production_snapshot_v1(universe)
    outputs = [
        produce_productive_futures_ranking_v1(
            universe_snapshot=universe,
            feature_production_snapshot=features,
            repository_sha=REPO_SHA,
            producer_observed_at_unix=OBSERVED_UNIX + delay,
        ).snapshot
        for delay in (0, 30)
    ]
    assert outputs[0].produced_at_wall_time != outputs[1].produced_at_wall_time
    assert outputs[0].ranking_snapshot_id == outputs[1].ranking_snapshot_id
    assert outputs[0].integrity_digest == outputs[1].integrity_digest


def test_legacy_ranking_identity_cold_load_keeps_original_membership_and_bytes(tmp_path):
    bases = ("ETH", "SOL", "ADA", "AVAX", "BCH", "DOT")
    universe = _universe([_perp(f"{base}-USDT-SWAP", base=base, ctValCcy=base) for base in bases])
    features = synthesize_ready_feature_production_snapshot_v1(universe)
    current = produce_productive_futures_ranking_v1(
        universe_snapshot=universe,
        feature_production_snapshot=features,
        repository_sha=REPO_SHA,
        producer_observed_at_unix=OBSERVED_UNIX,
    ).snapshot
    # Exact pre-change identity algorithm, with the unchanged snapshot schema.
    # This is a synthetic compatibility record, not historical venue evidence.
    legacy_id = compute_ranking_snapshot_id_v1(
        universe_snapshot_id=current.universe_snapshot_id,
        universe_source_digest=current.universe_source_digest,
        config_digest=current.config_digest,
        repository_sha=current.repository_sha,
    )
    assert legacy_id != current.ranking_snapshot_id
    persisted = run_productive_futures_ranking_producer_v1(
        state_root=tmp_path / "ranking",
        universe_snapshot=universe,
        feature_production_snapshot=features,
        repository_sha=REPO_SHA,
        producer_observed_at_unix=OBSERVED_UNIX,
        ranking_snapshot_id=legacy_id,
        session_id="synthetic-pre-change-record",
    )
    assert persisted["ok"]
    snapshot = persisted["snapshot"]
    members = [row["canonical_instrument_id"] for row in snapshot["ranked_candidates"][:5]]
    original = write_membership_context_artifact_v1(
        build_membership_context_artifact_v1(
            ordered_instrument_ids=members,
            cap22_provenance=_provenance(snapshot),
            bootstrap=True,
            prior_membership_reference=None,
        ),
        store_root=tmp_path / "membership",
    )
    before = {str(path): path.read_bytes() for path in tmp_path.rglob("*") if path.is_file()}
    loaded = load_and_validate_ranking_snapshot_v1(
        tmp_path / "ranking",
        expected_repository_sha=REPO_SHA,
        expected_config_digest=current.config_digest,
    )
    assert loaded.ok
    assert loaded.snapshot.to_dict() == snapshot
    restored = read_membership_context_artifact_v1(
        original.instance_id, store_root=tmp_path / "membership"
    )
    replay = run_isolated_selector_cycle_v1(
        snapshot=loaded.snapshot.to_dict(),
        cap22_provenance=_provenance(loaded.snapshot.to_dict()),
        prior=restored,
        store_root=tmp_path / "membership",
        persist=True,
    )
    assert restored.to_dict() == original.to_dict()
    assert restored.cap22_provenance.ranking_snapshot_id == legacy_id
    assert replay.decision_status == STATUS_UNCHANGED_REPLAY
    assert replay.ordered_membership == tuple(members)
    assert replay.persisted_artifact is None
    assert before == {
        str(path): path.read_bytes() for path in tmp_path.rglob("*") if path.is_file()
    }
