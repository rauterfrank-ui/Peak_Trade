"""Independent, versioned candidate reviews through the original pure Master V2."""

from dataclasses import asdict, replace
from datetime import datetime
from itertools import permutations
from hashlib import sha256
import json
from urllib.parse import urlencode

import pytest

from src.ops.current_mf_n5_full_autonomy_productive_runtime_orchestrator_v1.offline_candidate_cards_v1 import (
    review_offline_instrument_candidate_cards_v1,
    bind_archived_candidate_captures_v1,
)
from src.ops.full_core_live_path_composition_root_v1.fresh_pretrade_runtime_get_v1 import (
    FreshPretradeGetTransportResultV1,
)
from src.ops.master_v2_double_play_instrument_cards_v1 import OfflineInstrumentCandidateCardV1
from src.ops.full_core_live_path_composition_root_v1.current_productive_canonical_price_provenance_v1 import (
    build_explicit_test_fixture_price_provenance_v1,
)
from src.ops.single_selected_future_runtime_binding_v1.models_v1 import BoundInstrumentV1
from src.ops.current_mf_n5_isolated_lane_instance_topology_v1.topology_v1 import IsolatedLaneSlotV1
from src.ops.current_mf_n5_instrument_runtime_identity_closure_v1.models_v1 import (
    OccupiedLaneRuntimeInstrumentIdentityV1,
)
from trading.master_v2.canonical_market_context_v1 import with_computed_input_digest
from trading.market_state.distinct_market_observation_acceptor_v1 import (
    ObservationCandidateV1,
    commit_observation_acceptance_v1,
    evaluate_distinct_market_observation_v1,
    initial_observation_acceptance_state_v1,
)
from trading.market_state.observation_identity_v1 import InstrumentObservationKeyV1
from trading.master_v2.directional_assessment_confirmation_integration_v1 import (
    initial_directional_confirmation_side_state_carrier_v1,
)
from tests.trading.master_v2.test_integrated_offline_trading_logic_replay_v1 import (
    _market_context,
    _replay_input,
)


def _card(base="ETH", *, source_mode="OFFLINE_FIXTURE", second=1, mark=3500.0, confirmed=False):
    native = f"{base}-USDT-SWAP"
    instrument = f"okx:linear_perpetual:{base}:USDT:USDT:perp"
    context = _market_context(
        instrument_id=instrument,
        context_id=f"{base}-version-{second}",
        decision_time=f"2026-06-30T12:00:{second:02d}+00:00",
        mark_price=mark,
        index_price=mark - 0.5,
        best_bid=mark - 0.2,
        best_ask=mark + 0.2,
    )
    decision_unix = datetime.fromisoformat(context.decision_time).timestamp()
    last_open_ms = int((decision_unix - second - 60) * 1000)
    candles = {
        "code": "0",
        "data": [
            [
                str(last_open_ms - (99 - i) * 60_000),
                str(mark + i),
                str(mark + i + 1),
                str(mark + i - 1),
                str(mark + i),
                "10",
                "10",
                "35000",
                "1",
            ]
            for i in range(100)
        ],
    }
    rows = {
        "/api/v5/market/ticker": {
            "bidPx": str(context.best_bid),
            "askPx": str(context.best_ask),
            "vol24h": str(context.volume),
        },
        "/api/v5/public/open-interest": {"oi": str(context.open_interest)},
        "/api/v5/public/funding-rate": {"fundingRate": str(context.funding_rate)},
    }
    captures = {
        path: {
            "request_path": path,
            "native_id": native,
            "request_query": {"instId": native},
            "get_performed": True,
            "auth_required": False,
            "http_status": 200,
            "captured_at_utc": context.decision_time,
            "payload": {
                "code": "0",
                "data": [{**row, "instId": native, "ts": str(int(decision_unix * 1000))}],
            },
        }
        for path, row in rows.items()
    }
    captures["/api/v5/market/candles"] = {
        **captures["/api/v5/market/ticker"],
        "request_path": "/api/v5/market/candles",
        "request_query": {"instId": native, "bar": "1m"},
        "payload": candles,
    }
    closes = tuple(float(row[4]) for row in candles["data"])
    confirmation = {}
    if confirmed:
        key = InstrumentObservationKeyV1(
            venue="okx_eea", canonical_instrument_id=instrument, venue_instrument_id=native
        )
        state = initial_observation_acceptance_state_v1(bound_instrument_key=key)
        for offset, price in ((-1, mark - 1), (0, mark)):
            acceptance = evaluate_distinct_market_observation_v1(
                state,
                ObservationCandidateV1(
                    venue=key.venue,
                    canonical_instrument_id=instrument,
                    venue_instrument_id=native,
                    venue_event_time=decision_unix + offset,
                    mark_price=price,
                ),
            )
            state = commit_observation_acceptance_v1(current_state=state, result=acceptance)
        base_input = _replay_input()
        confirmation = dict(
            policies=replace(
                base_input.policies,
                directional=replace(base_input.policies.directional, confirmation_epochs=1),
            ),
            directional_confirmation_progress=initial_directional_confirmation_side_state_carrier_v1(
                session_id=base, venue="okx_eea", instrument=key
            ),
            observation_acceptance_result=acceptance,
            confirmation_progress_session_id=base,
            confirmation_progress_venue="okx_eea",
            confirmation_progress_instrument=key,
        )
    return OfflineInstrumentCandidateCardV1(
        source_mode=source_mode,
        binding=BoundInstrumentV1(
            instrument_id=instrument,
            venue_native_id=native,
            ranking_snapshot_id="ranking",
            ranking_integrity_digest="a" * 64,
            universe_snapshot_id="universe",
            selection_id="selection",
            selection_integrity_digest="b" * 64,
            selection_state="SELECTED",
        ),
        replay_input=_replay_input(
            instrument_id=instrument,
            canonical_market_context=context,
            price_path=closes,
            current_price=closes[-1],
            **confirmation,
        ),
        price_provenance=build_explicit_test_fixture_price_provenance_v1(
            venue_native_id=native,
            mark_px=mark,
            index_px=mark - 0.5,
        ),
        market_captures=captures,
    )


def test_five_cards_keep_independent_master_v2_decisions_and_gge_lineage():
    cards = {
        _card(base).binding.instrument_id: _card(base)
        for base in ("ETH", "SOL", "ADA", "LINK", "APT")
    }
    result = review_offline_instrument_candidate_cards_v1(cards)
    assert len(result) == 5
    for instrument, review in result.items():
        assert asdict(cards[instrument])["owner_universe"] == "Master V2 Double Play"
        assert asdict(review)["owner_universe"] == "Master V2 Double Play"
        assert review.status == "NO_ENTRY"
        assert review.decision_outcome == "no_action"
        assert review.gge_input_digest is not None
        assert review.card_digest is not None
        assert (
            review.market_context_digest
            == cards[instrument].replay_input.canonical_market_context.input_digest
        )


def test_formally_valid_unfavorable_and_malformed_cards_never_stop_other_candidates():
    good, unfavorable, malformed = (
        _card("ETH", confirmed=True),
        _card("SOL", confirmed=True),
        _card("ADA"),
    )
    policies = unfavorable.replay_input.policies
    unfavorable = replace(
        unfavorable,
        replay_input=replace(
            unfavorable.replay_input,
            policies=replace(policies, survival=replace(policies.survival, min_net_edge=999.0)),
        ),
    )
    malformed = replace(malformed, market_captures={})
    expected = None
    for order in permutations((good, unfavorable, malformed)):
        result = review_offline_instrument_candidate_cards_v1(
            {card.binding.instrument_id: card for card in order}
        )
        assert result[good.binding.instrument_id].status == "OFFLINE_ENTRY_DECISION"
        assert result[good.binding.instrument_id].decision_outcome == "enter_long"
        assert result[unfavorable.binding.instrument_id].status == "NO_ENTRY"
        assert result[malformed.binding.instrument_id].status == "REJECTED_INPUT"
        if expected is None:
            expected = result
        assert result == expected


@pytest.mark.parametrize("mode", ["PAPER", "SHADOW"])
def test_source_update_changes_the_card_and_rechecks_the_actual_values(mode):
    first = _card(source_mode=mode)
    updated = _card(source_mode=mode, second=2, mark=3501.0, confirmed=True)
    instrument = first.binding.instrument_id
    previous = review_offline_instrument_candidate_cards_v1({instrument: first})[instrument]
    current = review_offline_instrument_candidate_cards_v1({instrument: updated})[instrument]
    assert current.source_mode == mode
    assert current.card_digest != previous.card_digest
    assert current.market_context_digest != previous.market_context_digest
    assert current.gge_input_digest != previous.gge_input_digest
    assert current.decision_time != previous.decision_time
    assert previous.status == "NO_ENTRY"
    assert current.status == "OFFLINE_ENTRY_DECISION"
    assert (
        current == review_offline_instrument_candidate_cards_v1({instrument: updated})[instrument]
    )


@pytest.mark.parametrize(
    "problem", ["foreign", "unbound_value", "future_capture", "digest", "c1_gap", "file_writer"]
)
def test_invalid_card_does_not_contaminate_another_instrument(problem):
    card, other = _card("ETH"), _card("SOL")
    if problem == "foreign":
        card = replace(card, binding=replace(card.binding, venue_native_id="ADA-USDT-SWAP"))
    elif problem == "unbound_value":
        context = with_computed_input_digest(
            replace(card.replay_input.canonical_market_context, volume=999.0)
        )
        card = replace(
            card, replay_input=replace(card.replay_input, canonical_market_context=context)
        )
    elif problem == "future_capture":
        card.market_captures["/api/v5/market/ticker"]["captured_at_utc"] = "2026-06-30T12:00:02Z"
    elif problem == "digest":
        context = replace(card.replay_input.canonical_market_context, input_digest="f" * 64)
        card = replace(
            card, replay_input=replace(card.replay_input, canonical_market_context=context)
        )
    elif problem == "c1_gap":
        card.market_captures["/api/v5/market/candles"]["payload"]["data"].pop(50)
    else:
        card = replace(
            card,
            replay_input=replace(
                card.replay_input,
                regime_bull_bear_switch_evidence_path="/tmp/forbidden-card-writer.json",
            ),
        )
    reviews = review_offline_instrument_candidate_cards_v1(
        {card.binding.instrument_id: card, other.binding.instrument_id: other}
    )
    assert reviews[card.binding.instrument_id].status == "REJECTED_INPUT"
    assert reviews[card.binding.instrument_id].owner_universe == "Master V2 Double Play"
    assert reviews[other.binding.instrument_id].decision_digest is not None


def test_malformed_native_identity_does_not_abort_the_batch():
    good, malformed = _card("ETH"), _card("SOL")
    malformed = replace(malformed, binding=replace(malformed.binding, venue_native_id=[]))
    reviews = review_offline_instrument_candidate_cards_v1(
        {good.binding.instrument_id: good, malformed.binding.instrument_id: malformed}
    )
    assert reviews[malformed.binding.instrument_id].status == "REJECTED_INPUT"
    assert reviews[good.binding.instrument_id].decision_digest is not None


def _with_slot(card, lane):
    return replace(
        card,
        slot_identity=OccupiedLaneRuntimeInstrumentIdentityV1.from_bound(
            lane_id=lane, bound=card.binding
        ),
    )


def _ranked_slot_pairs(bindings):
    return {
        lane: (
            IsolatedLaneSlotV1(
                lane_id=lane,
                occupancy="OCCUPIED",
                canonical_instrument_id=bound.instrument_id,
                lane_state_root=f"/offline/{lane}",
                universe_snapshot_id=bound.universe_snapshot_id,
                ranking_snapshot_id=bound.ranking_snapshot_id,
                ranking_integrity_digest=bound.ranking_integrity_digest,
            ),
            bound,
        )
        for lane, bound in bindings.items()
    }


def test_five_slot_cards_carry_current_instrument_and_generation():
    cards = [
        _with_slot(_card(base), f"LANE_{i + 1}")
        for i, base in enumerate(("ETH", "SOL", "ADA", "LINK", "APT"))
    ]
    bindings = {card.slot_identity.lane_id: card.binding for card in cards}
    reviews = review_offline_instrument_candidate_cards_v1(
        {card.binding.instrument_id: card for card in cards},
        ranked_slot_pairs=_ranked_slot_pairs(bindings),
    )
    for card in cards:
        review = reviews[card.binding.instrument_id]
        assert review.lane_id == card.slot_identity.lane_id
        assert review.instrument_epoch == card.slot_identity.lane_identity.instrument_epoch
        assert review.card_digest is not None


def test_old_slot_card_is_rejected_after_assignment_changes_and_other_card_continues():
    first, other = (
        _with_slot(_card("ETH", confirmed=True), "LANE_1"),
        _with_slot(_card("SOL", confirmed=True), "LANE_2"),
    )
    updated_binding = replace(
        first.binding, selection_id="new-assignment", selection_integrity_digest="c" * 64
    )
    bindings = {"LANE_1": updated_binding, "LANE_2": other.binding}
    cards = {first.binding.instrument_id: first, other.binding.instrument_id: other}
    rejected = review_offline_instrument_candidate_cards_v1(
        cards, ranked_slot_pairs=_ranked_slot_pairs(bindings)
    )
    assert rejected[first.binding.instrument_id].status == "REJECTED_INPUT"
    assert rejected[other.binding.instrument_id].status == "OFFLINE_ENTRY_DECISION"
    updated = _with_slot(replace(first, binding=updated_binding), "LANE_1")
    current = review_offline_instrument_candidate_cards_v1(
        {updated.binding.instrument_id: updated}, ranked_slot_pairs=_ranked_slot_pairs(bindings)
    )[updated.binding.instrument_id]
    assert current.status == "OFFLINE_ENTRY_DECISION"
    assert current.instrument_epoch != first.slot_identity.lane_identity.instrument_epoch


def test_conflicting_slot_cards_are_local_rejections():
    cards = [
        _with_slot(_card("ETH"), "LANE_1"),
        _with_slot(_card("SOL"), "LANE_1"),
        _with_slot(_card("ADA", confirmed=True), "LANE_3"),
    ]
    bindings = {"LANE_1": cards[0].binding, "LANE_3": cards[2].binding}
    reviews = review_offline_instrument_candidate_cards_v1(
        {card.binding.instrument_id: card for card in cards},
        ranked_slot_pairs=_ranked_slot_pairs(bindings),
    )
    assert reviews[cards[0].binding.instrument_id].status == "REJECTED_INPUT"
    assert reviews[cards[1].binding.instrument_id].status == "REJECTED_INPUT"
    assert reviews[cards[2].binding.instrument_id].status == "OFFLINE_ENTRY_DECISION"


@pytest.mark.parametrize(
    "field",
    ["lane_id", "canonical_instrument_id", "ranking_snapshot_id", "ranking_integrity_digest"],
)
def test_card_cannot_reassign_the_ranked_slot(field):
    first, other = _with_slot(_card("ETH"), "LANE_1"), _with_slot(_card("SOL"), "LANE_2")
    pairs = _ranked_slot_pairs({"LANE_1": first.binding, "LANE_2": other.binding})
    slot, bound = pairs["LANE_1"]
    pairs["LANE_1"] = (replace(slot, **{field: "foreign"}), bound)
    result = review_offline_instrument_candidate_cards_v1(
        {first.binding.instrument_id: first, other.binding.instrument_id: other},
        ranked_slot_pairs=pairs,
    )
    assert result[first.binding.instrument_id].status == "REJECTED_INPUT"
    assert result[other.binding.instrument_id].decision_digest is not None


def test_original_get_receipts_supply_card_values_and_reject_modified_archive_bytes():
    card = _card(confirmed=True)
    observations, bodies = {}, {}
    for path, capture in card.market_captures.items():
        body = json.dumps(capture["payload"]).encode()
        bodies[path] = body
        observations[path] = FreshPretradeGetTransportResultV1(
            get_performed=True,
            method="GET",
            endpoint=path + "?" + urlencode(capture["request_query"]),
            http_status=200,
            payload=capture["payload"],
            auth_header_sent=False,
            transport_class="FIXTURE",
            venue_live_contact=True,
            historical_reuse=False,
            error_class="",
            body_sha256=sha256(body).hexdigest(),
            acquired_at_utc=capture["captured_at_utc"],
        )
    archived = bind_archived_candidate_captures_v1(
        card, observations=observations, raw_bodies=bodies
    )
    instrument = card.binding.instrument_id
    review = review_offline_instrument_candidate_cards_v1({instrument: archived})[instrument]
    assert review.status == "OFFLINE_ENTRY_DECISION"
    assert (
        archived.market_captures["/api/v5/market/ticker"]["body_sha256"]
        == sha256(bodies["/api/v5/market/ticker"]).hexdigest()
    )
    with pytest.raises(ValueError, match="candidate_original_capture_mismatch"):
        bind_archived_candidate_captures_v1(
            card, observations=observations, raw_bodies={**bodies, "/api/v5/market/ticker": b"{}"}
        )
    archived.market_captures["/api/v5/market/ticker"]["payload"]["data"][0]["vol24h"] = "999"
    assert (
        review_offline_instrument_candidate_cards_v1({instrument: archived})[instrument].status
        == "REJECTED_INPUT"
    )
