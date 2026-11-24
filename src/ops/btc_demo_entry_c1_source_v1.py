"""Historical opening-G17 source for the original first-fill C1 publication.

This re-proves the original recorded opening window. It never restores or
supplies a current volatility forecast and never modifies its live checkpoint.
"""

import json

from src.ops.full_core_live_path_composition_root_v1.current_productive_sidestate_confirmation_cursor_v1 import (
    current_productive_cursor_digest_v1,
    load_current_productive_sidestate_confirmation_cursor_v1,
)
from src.ops.full_core_live_path_composition_root_v1.natural_enter_cross_session_outcome_closure_v1.retention_v1 import (
    immutable_json_v1,
)
from src.ops.portfolio_capital_reservation_budget_v1.durable_store_v1 import digest
from trading.master_v2.canonical_volatility_runtime_mark_history_v1 import (
    CanonicalVolatilityRuntimeMarkHistoryHostV1,
)
from trading.master_v2.canonical_volatility_typed_runtime_producer_scaffold_v1 import (
    CanonicalVolatilityTypedRuntimeProducerScaffoldV1,
)


def retain_original_entry_g17_for_c1_v1(runtime, reservation_id):
    raw = load_current_productive_sidestate_confirmation_cursor_v1(runtime.cursor)
    source = runtime.owner.execution_links_v1()[reservation_id]["plan_origin"]["core_cursor_source"]
    if current_productive_cursor_digest_v1(raw) != source["source_cursor_digest"]:
        raise ValueError("BTC_DEMO_ENTRY_C1_ORIGINAL_CURSOR_CHANGED")
    packet = dict(
        schema="btc_demo_original_entry_g17_c1_source.v1",
        reservation_id=reservation_id,
        core_cursor_source=source,
        original_cursor=raw,
        g17_history=runtime.first.g17.history.to_persistence_dict_v1(),
        purpose="HISTORICAL_FIRST_FILL_C1_PUBLICATION_ONLY",
    )
    packet["record_digest"] = digest(packet)
    immutable_json_v1(runtime.root / "original-entry-g17-c1.json", packet)


def read_original_entry_g17_for_c1_v1(runtime, reservation_id):
    packet = json.loads((runtime.root / "original-entry-g17-c1.json").read_bytes())
    body = {k: v for k, v in packet.items() if k != "record_digest"}
    source = runtime.owner.execution_links_v1()[reservation_id]["plan_origin"]["core_cursor_source"]
    if (
        packet["record_digest"] != digest(body)
        or packet["reservation_id"] != reservation_id
        or packet["core_cursor_source"] != source
        or current_productive_cursor_digest_v1(packet["original_cursor"])
        != source["source_cursor_digest"]
    ):
        raise ValueError("BTC_DEMO_ENTRY_C1_ORIGINAL_SOURCE_UNPROVEN")
    history = CanonicalVolatilityRuntimeMarkHistoryHostV1.from_persistence_dict_v1(
        packet["g17_history"]
    )
    producer = CanonicalVolatilityTypedRuntimeProducerScaffoldV1.create(
        venue=history.venue,
        canonical_instrument_id=history.canonical_instrument_id,
        venue_instrument_id=history.venue_instrument_id,
    )
    for row in history.trailing_window_records_v1(count=len(packet["g17_history"]["records"])):
        producer.ingest_finalized_pt1m_mark_sample_v1(
            venue=row.venue,
            canonical_instrument_id=row.canonical_instrument_id,
            venue_instrument_id=row.venue_instrument_id,
            event_time_unix_seconds=row.event_time.unix_seconds,
            mark_price=row.mark_price,
            is_final=row.is_final,
        )
    market = json.loads(
        packet["original_cursor"]["entry_assessment_frame"]["market_context"]["canonical"]
    )
    expected = market["canonical_volatility_estimate"]
    port = producer.output_port_v1()
    if (
        producer.history.history_digest != history.history_digest
        or port.estimate is None
        or port.estimate.source_digest != expected["source_digest"]
        or port.as_of_event_time.isoformat() != expected["as_of_event_time"]
    ):
        raise ValueError("BTC_DEMO_ENTRY_C1_HISTORICAL_G17_MISMATCH")
    return producer
