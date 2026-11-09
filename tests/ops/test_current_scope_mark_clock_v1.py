"""Source/receive/evaluation clocks at the actual original Scope consumer."""

from copy import deepcopy
from dataclasses import replace
from datetime import datetime, timezone
import hashlib
import json

import pytest

from src.ops.full_core_live_path_composition_root_v1 import (
    current_core_entry_assessment_frame_v1 as frames,
)
from src.ops.full_core_live_path_composition_root_v1.current_productive_canonical_price_provenance_v1 import (
    ProductiveCanonicalPriceProvenanceError,
    build_cmc_mark_provenance_from_okx_mark_price_payload_v1,
)
from tests.ops import (
    test_full_core_current_productive_oneshot_sidestate_confirmation_cursor_join_v1 as core,
)


def iso(value):
    return datetime.fromtimestamp(value, timezone.utc).isoformat()


def provenance(
    *, native="ETH-USDT-SWAP", mark=100.0, index=99.5, event=1_700_000_100.0, captured=None
):
    return build_cmc_mark_provenance_from_okx_mark_price_payload_v1(
        mark_price_payload=dict(
            code="0",
            data=[
                dict(instId=native, markPx=str(mark), idxPx=str(index), ts=str(int(event * 1000)))
            ],
        ),
        venue_native_id=native,
        mark_acquired_at_utc=iso(event if captured is None else captured),
    )


def source_cycles(monkeypatch, *, age=0, fault=None):
    original = core.run_current_productive_master_v2_runtime_cycle_v1

    def run(**kwargs):
        now = kwargs["observed_unix"]
        source = provenance(
            native=kwargs["bound_instrument"].venue_native_id,
            mark=kwargs["mark_px"],
            index=kwargs["index_px"],
            event=now - age,
        )
        if fault == "missing-receive":
            raw = json.loads(source.mark_clock_json)
            raw["captured_at_utc"] = ""
            source = replace(source, mark_clock_json=json.dumps(raw))
        elif fault == "missing-source":
            source = replace(source, mark_clock_json="null")
        kwargs["canonical_price_provenance"] = source
        return original(**kwargs)

    monkeypatch.setattr(core, "run_current_productive_master_v2_runtime_cycle_v1", run)


@pytest.mark.parametrize("age", [0, 5])
def test_existing_mark_freshness_boundary_reaches_original_gge_and_original_cursor(
    monkeypatch, age
):
    source_cycles(monkeypatch, age=age)
    result = core._cycle(cycle_id="source-clock-positive", mark_px=100)
    assert result.replay is not None and result.replay.replay_pass
    context = result.replay.intermediate.market_context
    assert context.mark_price == 100
    assert (
        datetime.fromisoformat(context.market_event_time.replace("Z", "+00:00")).timestamp()
        == 1_700_000_100.0 - age
    )
    assert "-mark-" in context.context_id
    frame = result.outgoing_cursor.entry_assessment_frame
    assert frame["schema"] == frames.PRICE_BOUND_SCHEMA
    assert (
        json.loads(frame["scope_price_source"]["mark_clock_json"])["payload"]["data"][0]["markPx"]
        == "100.0"
    )
    bodies = frames.read_current_core_entry_assessment_frame_v1(result.outgoing_cursor)
    assert bodies["parent"]["market_context_ref"] == context.context_id
    assert result.outgoing_cursor.runtime_scope_state.current_hysteresis_band == pytest.approx(
        context.volatility_estimate * context.mark_price
    )


@pytest.mark.parametrize(
    "age,fault", [(5.001, None), (-0.001, None), (0, "missing-receive"), (0, "missing-source")]
)
def test_stale_future_or_unbound_mark_never_advances_original_scope_or_confirmation(
    monkeypatch, age, fault
):
    origin = core._cycle(cycle_id="clock-origin", mark_px=100)
    source_cycles(monkeypatch, age=age, fault=fault)
    cursor = origin.outgoing_cursor.to_dict()
    before = deepcopy(cursor)
    result = core._cycle(cycle_id="clock-reject", mark_px=105, incoming_cursor=cursor)
    assert result.replay is None and result.outgoing_cursor is None
    assert "CURRENT_SCOPE_MARK_CLOCK_INVALID" in result.input_blocker
    assert cursor == before


def test_fresh_cmc_price_changes_original_gge_distance_without_parameter_change(monkeypatch):
    source_cycles(monkeypatch)
    first = core._cycle(cycle_id="fresh-100", mark_px=100)
    second = core._cycle(cycle_id="fresh-200", mark_px=200)
    assert first.replay.replay_pass and second.replay.replay_pass
    a, b = first.outgoing_cursor.runtime_scope_state, second.outgoing_cursor.runtime_scope_state
    assert b.current_hysteresis_band == pytest.approx(a.current_hysteresis_band * 2)
    assert (
        first.outgoing_cursor.entry_assessment_frame["scope_price_source"]
        != second.outgoing_cursor.entry_assessment_frame["scope_price_source"]
    )


@pytest.mark.parametrize(
    "fault",
    [
        "receive-future",
        "receive-old",
        "stale-venue-new-receive",
        "missing-venue",
        "wrong-payload-price",
        "digest-tampered",
        "duplicate-native",
    ],
)
def test_source_clock_cannot_be_refreshed_by_a_label_or_receive_time(fault):
    now = 1_700_000_100.0
    source = provenance(event=now)
    raw = json.loads(source.mark_clock_json)
    if fault == "receive-future":
        raw["captured_at_utc"] = iso(now + 1)
    elif fault == "receive-old":
        raw["captured_at_utc"] = iso(now - 6)
    elif fault == "stale-venue-new-receive":
        raw["payload"]["data"][0]["ts"] = str(int((now - 6) * 1000))
    elif fault == "missing-venue":
        raw["payload"]["data"][0].pop("ts")
    elif fault == "wrong-payload-price":
        raw["payload"]["data"][0]["markPx"] = "101"
    elif fault == "duplicate-native":
        raw["payload"]["data"].append(deepcopy(raw["payload"]["data"][0]))
    if fault != "digest-tampered":
        raw["payload_sha256"] = hashlib.sha256(
            json.dumps(raw["payload"], sort_keys=True, separators=(",", ":")).encode()
        ).hexdigest()
    else:
        raw["payload_sha256"] = "0" * 64
    with pytest.raises(
        ProductiveCanonicalPriceProvenanceError, match="CURRENT_SCOPE_MARK_CLOCK_INVALID"
    ):
        replace(source, mark_clock_json=json.dumps(raw)).validate_against_cycle_inputs_v1(
            mark_px=100, index_px=99.5, venue_native_id="ETH-USDT-SWAP", observed_unix=now
        )


def test_original_cursor_frame_rejects_rehashed_scope_source_substitution(monkeypatch):
    source_cycles(monkeypatch)
    result = core._cycle(cycle_id="source-substitution", mark_px=100)
    cursor = result.outgoing_cursor
    frame = deepcopy(cursor.entry_assessment_frame)
    source = frame["scope_price_source"]
    raw = json.loads(source["mark_clock_json"])
    raw["captured_at_utc"] = iso(1_700_000_099.0)
    source["mark_clock_json"] = json.dumps(raw)
    frame["digest"] = frames._digest({k: v for k, v in frame.items() if k != "digest"})
    with pytest.raises(ValueError, match="CURRENT_CORE_SCOPE_MARK_SOURCE_BINDING_INVALID"):
        frames.read_current_core_entry_assessment_frame_v1(
            replace(cursor, entry_assessment_frame=frame)
        )
