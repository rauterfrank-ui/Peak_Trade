"""Retained Mark inputs keep their historical serialization and current guards."""

from copy import deepcopy

import pytest

from src.ops.integrated_paper_shadow_observation_wallclock_session_execution_v1.bundle_verifier_v1 import (
    _typed_cycle_market_time,
)
from src.ops.wallclock_full_canonical_decision_to_simulated_economics_runtime_bridge_hardening_v2.market_data_price_basis_v2 import (
    build_explicit_mid_price_basis_v2,
)

REVISIONS = (
    "755d4d5a3f6f2756885bd00f14b5758e76e18442",
    "05243d30437dbaeb5e62ce8c9b0e453cec801ab9",
)


def _recorded_mark(label="last"):
    # Shape and values from the retained 14-Nov first cycle. No original file is
    # needed or rewritten by this offline contract test.
    event, received, decided = 1794676457.283, 1794676457.3027918, 1794676457.429805
    instrument = "ETH-USD_UM_XPERP-310404"
    basis = build_explicit_mid_price_basis_v2(
        mid_price=1815.2,
        event_ts_unix=event,
        receive_ts_unix=received,
        price_field=label,
    )
    session = dict(
        session_id="retained-i17",
        canonical_instrument_id=instrument,
        venue_instrument_id=instrument,
        mapping_digest="mapping",
        mark_price_field="markPx",
        mark_price_endpoint="/api/v5/public/mark-price",
    )
    mark = dict(
        **{k: session[k] for k in session if k != "session_id"},
        event_ts_unix=event,
        receive_ts_unix=received,
        mark_receive_ts_unix=received,
        mid_price=1815.2,
        mark_px=1815.2,
    )
    cycle = dict(
        session_id=session["session_id"],
        instrument_id=instrument,
        market_data_reference=basis.market_data_reference,
        price_basis=basis.to_dict(),
        shadow_decision_timing=dict(
            mark_event_ts_unix=event,
            mark_receive_ts_unix=received,
            decision_input_available_ts_unix=decided,
            decision_cycle_ts_unix=decided,
        ),
    )
    return cycle, mark, session, decided


@pytest.mark.parametrize("revision", REVISIONS)
def test_recorded_mark_readback_preserves_original_bytes_and_meaning(revision):
    cycle, mark, session, decided = _recorded_mark()
    originals = deepcopy((cycle, mark, session))
    assert _typed_cycle_market_time(cycle, mark, session, repository_sha=revision) == decided
    assert (cycle, mark, session) == originals
    assert mark["mark_price_field"] == "markPx"
    assert cycle["price_basis"]["price_field"] == "last"


@pytest.mark.parametrize("revision", (None, "a" * 40))
def test_current_or_unknown_producer_cannot_use_recorded_label(revision):
    cycle, mark, session, _ = _recorded_mark()
    with pytest.raises(ValueError, match="DDO_MARKET_PRICE_REFERENCE_MISMATCH"):
        _typed_cycle_market_time(cycle, mark, session, repository_sha=revision)


@pytest.mark.parametrize("revision", (None, "a" * 40))
def test_current_explicit_mark_remains_unchanged(revision):
    cycle, mark, session, decided = _recorded_mark("markPx")
    assert _typed_cycle_market_time(cycle, mark, session, repository_sha=revision) == decided


@pytest.mark.parametrize("revision", REVISIONS)
@pytest.mark.parametrize(
    "fault",
    (
        "actual_last",
        "endpoint",
        "price",
        "ref",
        "bid",
        "clock",
        "quote",
        "session_source",
        "instrument",
        "lane",
        "assignment",
        "relabelled",
    ),
)
def test_recorded_serializer_cannot_hide_changed_inputs_or_new_slot_scope(revision, fault):
    cycle, mark, session, _ = _recorded_mark()
    if fault == "actual_last":
        mark["mark_price_field"] = "last"
    elif fault == "endpoint":
        mark["mark_price_endpoint"] = "/api/v5/market/ticker"
    elif fault == "price":
        mark["mid_price"] += 1
    elif fault == "ref":
        cycle["market_data_reference"] = "a" * 64
    elif fault == "bid":
        cycle["price_basis"]["best_bid"] -= 1
    elif fault == "clock":
        cycle["shadow_decision_timing"]["mark_receive_ts_unix"] += 1
    elif fault == "quote":
        mark["price_basis_quote"] = {}
    elif fault == "session_source":
        session["mark_price_field"] = "last"
    elif fault == "instrument":
        session["canonical_instrument_id"] = "other"
    elif fault == "lane":
        session["lane_id"] = "LANE_1"
    elif fault == "assignment":
        session["n5_assignment"] = {"selection_id": "not-a-legacy-capture"}
    else:
        cycle["price_basis"]["price_field"] = "markPx"
    with pytest.raises(ValueError, match="DDO_MARKET_"):
        _typed_cycle_market_time(cycle, mark, session, repository_sha=revision)
