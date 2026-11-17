"""Fresh rankings renew selection validity and preserve original selection provenance."""

from dataclasses import replace
from datetime import datetime, timezone

import pytest

from src.ops.productive_futures_ranking_producer_v1.models_v1 import (
    ProductiveFuturesRankingSnapshotV1,
)
from src.ops.single_selected_future_policy_v1.selection_v1 import (
    produce_single_selected_future_v1,
)
from tests.ops import test_single_selected_future_policy_v1 as inputs


T0 = 1_700_000_100.0


def _rfc(seconds):
    return datetime.fromtimestamp(seconds, timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _ranking_at(
    monkeypatch,
    seconds,
    order=("ETH-USDT-SWAP", "SOL-USDT-SWAP"),
    instruments=("ETH-USDT-SWAP", "SOL-USDT-SWAP"),
):
    monkeypatch.setattr(inputs, "OBSERVED_UNIX", seconds)
    monkeypatch.setattr(inputs, "SOURCE_EVENT", str(int(seconds * 1000)))
    ranking = inputs._ranking(
        [
            inputs._perp(native, base=native.split("-")[0], ct_val_ccy=native.split("-")[0])
            for native in instruments
        ]
    )
    return inputs._with_authoritative_rank_order(ranking, list(order))


def _produce(ranking, *, now, previous=None, **kwargs):
    return produce_single_selected_future_v1(
        ranking_snapshot=ranking,
        repository_sha=inputs.REPO_SHA,
        producer_observed_at_unix=now,
        previous_selection=previous,
        **kwargs,
    )


def test_fresh_keep_renews_validity_from_ranking_and_preserves_selection_origin(monkeypatch):
    old = _produce(_ranking_at(monkeypatch, T0), now=T0).selection
    fresh = _ranking_at(monkeypatch, T0 + 7200)
    result = _produce(fresh, now=T0 + 7201, previous=old)
    selection = result.selection

    assert result.ok and not result.hard_stop
    assert selection.instrument_id == old.instrument_id
    assert selection.selected_at_event_time == old.selected_at_event_time == _rfc(T0)
    assert selection.valid_from == old.valid_from
    assert selection.valid_until == _rfc(T0 + 7200 + 3600)
    assert old.valid_until == _rfc(T0 + 3600)
    assert selection.ranking_snapshot_id == fresh["ranking_snapshot_id"]
    assert selection.ranking_integrity_digest == fresh["integrity_digest"]
    assert selection.previous_selection_id == old.selection_id
    assert selection.selection_id != old.selection_id
    assert selection.integrity_digest == selection.compute_integrity_digest()
    assert not selection.alpha_allowed and not selection.multi_future_runtime_authorized


@pytest.mark.parametrize("validity", [3600, 1800])
def test_brev_mmt_flat_selection_has_no_wait_and_keeps_receipt_horizon(monkeypatch, validity):
    brev, mmt = "BREV-USDT-SWAP", "MMT-USDT-SWAP"
    old_ranking = _ranking_at(monkeypatch, T0, order=(brev, mmt), instruments=(brev, mmt))
    old = _produce(old_ranking, now=T0, selection_validity_seconds=validity).selection
    assert old.venue_native_id == brev
    fresh = _ranking_at(monkeypatch, T0 + 60, order=(mmt, brev), instruments=(brev, mmt))
    flat = _produce(fresh, now=T0 + 61, previous=old, selection_validity_seconds=validity).selection
    assert flat.venue_native_id == mmt
    assert flat.reason_codes == ("SELECTION_REFRESHED",)
    assert flat.selected_at_event_time == _rfc(T0 + 60)
    assert flat.valid_until == _rfc(T0 + 60 + validity)

    held = _produce(
        fresh,
        now=T0 + 61,
        previous=old,
        selection_validity_seconds=validity,
        open_position_instrument_id=old.instrument_id,
    ).selection
    assert held.venue_native_id == brev
    assert held.state == "REPLACEMENT_PENDING"
    assert held.replacement_venue_native_id == mmt
    assert held.valid_until == flat.valid_until


def test_hysteresis_retention_still_renews_from_fresh_evidence(monkeypatch):
    old = _produce(_ranking_at(monkeypatch, T0), now=T0).selection
    result = _produce(
        _ranking_at(monkeypatch, T0 + 7200, ("SOL-USDT-SWAP", "ETH-USDT-SWAP")),
        now=T0 + 7201,
        previous=old,
        hysteresis_rank_improvement=2,
    )
    assert result.selection.instrument_id == old.instrument_id
    assert "HYSTERESIS_BLOCKS_CHURN" in result.selection.reason_codes
    assert result.selection.selected_at_event_time == old.selected_at_event_time
    assert result.selection.valid_until == _rfc(T0 + 7200 + 3600)


@pytest.mark.parametrize("problem", ["stale", "future", "digest"])
def test_unusable_ranking_cannot_renew_a_kept_selection(monkeypatch, problem):
    old = _produce(_ranking_at(monkeypatch, T0), now=T0).selection
    fresh = _ranking_at(monkeypatch, T0 + 7200)
    now = T0 + 7201
    expected = "RANKING_SNAPSHOT_INVALID"
    if problem == "stale":
        now = T0 + 7501
        expected = "RANKING_SNAPSHOT_STALE"
    elif problem == "future":
        fresh = (
            replace(
                ProductiveFuturesRankingSnapshotV1.from_dict(fresh),
                event_time=_rfc(now + 1),
            )
            .with_integrity_digest()
            .to_dict()
        )
    else:
        fresh["integrity_digest"] = "0" * 64
        expected = "RANKING_DIGEST_MISMATCH"
    result = _produce(fresh, now=now, previous=old, max_ranking_age_seconds=300)
    assert not result.ok and result.hard_stop
    assert result.selection.state == "NO_SELECTION"
    assert expected in result.failure_codes
    assert not result.selection.instrument_id
    assert result.alpha_blocked


def test_reobserving_one_ranking_cannot_extend_its_validity(monkeypatch):
    old = _produce(_ranking_at(monkeypatch, T0), now=T0).selection
    fresh = _ranking_at(monkeypatch, T0 + 7200)
    first = _produce(fresh, now=T0 + 7201, previous=old).selection
    retry = _produce(fresh, now=T0 + 7301, previous=old).selection
    assert retry.valid_until == first.valid_until == _rfc(T0 + 7200 + 3600)
    assert retry.selection_id == first.selection_id
    assert retry.integrity_digest == first.integrity_digest
