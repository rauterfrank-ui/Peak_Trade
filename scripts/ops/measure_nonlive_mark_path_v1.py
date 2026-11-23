"""Public mark-price reference and offline comparison with non-live decision timings.

Set PEAK_TRADE_NONLIVE_TIMING_DIR on a non-live host to retain its consumer
measurements. Set PEAK_TRADE_NONLIVE_TIMING_STAGES=1 for detailed diagnostic
profiling; its overhead changes elapsed times. On the same machine, 'reference' records independent public
pushes for the bound contract. 'compare' joins the two recordings offline.
Local processing uses monotonic time. Event-to-receipt ages also include any
offset between the exchange and the host's wall clock.
"""

import argparse
import json
import math
import platform
import sys
import time
from bisect import bisect_right
from collections import defaultdict
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path
from statistics import median

REPO = Path(__file__).resolve().parents[2]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from src.ops.peak_trade_public_market_data_runtime_v1.event_pipeline_v1 import (
    EventSequenceStateV1,
    process_public_events_v1,
)
from src.ops.peak_trade_public_market_data_runtime_v1.ws_binding_v1 import (
    load_ratified_eea_public_ws_binding_v1,
)
from src.ops.peak_trade_public_market_data_runtime_v1.ws_channel_normalizers_v1 import (
    normalize_ticker_row_to_mark_price_fact_v1,
)


def reference_identity(args):
    if args.demo_bound:
        from src.ops.btc_demo_lane3_v2 import _LANE, _NATIVE
        from src.ops.full_core_live_path_composition_root_v1.current_productive_future_identity_semantics_v1 import (
            resolve_selected_future_market_type_v1,
        )
        from src.ops.single_selected_future_runtime_binding_v1.models_v1 import BoundInstrumentV1

        bound = BoundInstrumentV1(**json.loads(args.demo_bound.read_bytes()))
        if (
            bound.venue_native_id != _NATIVE
            or not bound.instrument_id.startswith("okx_eea:")
            or not args.demo_session
        ):
            raise ValueError("original BTC Demo binding and session required")
        resolve_selected_future_market_type_v1(
            instrument_id=bound.instrument_id, venue_native_id=_NATIVE
        )
        return dict(
            mode="TESTNET",
            lane=_LANE,
            session=args.demo_session,
            native_id=_NATIVE,
            canonical_id=bound.instrument_id,
            binding_digest=bound.selection_integrity_digest,
            instrument_type="FUTURES",
            settlement_asset=bound.instrument_id.split(":")[4],
        )
    from src.ops.ranked_slot_run_source_v1 import read_ranked_run_slot_v1

    config = json.loads(args.slot_config.read_bytes())
    slot = read_ranked_run_slot_v1(config)
    mode = {"PAPER_EXCHANGE": "PAPER", "SHADOW": "SHADOW"}[config["surface"]]
    return dict(
        mode=mode,
        lane=slot.lane_id,
        session=config["session_id"],
        native_id=slot.instrument.venue_native_inst_id,
        canonical_id=slot.instrument.canonical_instrument_id,
        binding_digest=slot.selection.integrity_digest,
        instrument_type=slot.instrument.instrument_type,
        settlement_asset=slot.instrument.settlement_currency,
    )


def capture(socket, identity, seconds, emit, *, timeout_error=TimeoutError):
    binding = load_ratified_eea_public_ws_binding_v1()
    subscription = dict(channel=binding.public_channel_mark_price, instId=identity["native_id"])
    ref = dict(
        venue="okx_eea",
        canonical_instrument_id=identity["canonical_id"],
        venue_native_id=identity["native_id"],
        instrument_type=identity["instrument_type"],
        settlement_asset=identity["settlement_asset"],
        mapping_provenance_digest=identity["binding_digest"],
    )
    state = EventSequenceStateV1()
    deadline = time.monotonic() + seconds
    acknowledged = False
    socket.send(json.dumps(dict(op="subscribe", args=[subscription])))
    while (remaining := deadline - time.monotonic()) > 0:
        socket.settimeout(min(15, remaining))
        try:
            raw = socket.recv()
        except timeout_error:
            if time.monotonic() >= deadline:
                break
            raise ValueError("public mark reference timed out")
        received_ns = time.time_ns()
        received_mono_ns = time.perf_counter_ns()
        message = json.loads(raw)
        if message.get("event") == "notice" and message.get("code") == "64010":
            emit(dict(kind="endpoint_notice", received_ns=received_ns, message=message))
            continue
        if message.get("event") == "error":
            emit(dict(kind="exchange_error", code=message.get("code"), message=message.get("msg")))
            raise ValueError(f"OKX {message.get('code')}: {message.get('msg')}")
        arg = message.get("arg") or {}
        if any(arg.get(k) != v for k, v in subscription.items()):
            emit(dict(kind="unexpected_message", received_ns=received_ns, message=message))
            raise ValueError("unexpected OKX subscription or connection event")
        if message.get("event") == "subscribe":
            acknowledged = True
            continue
        if not acknowledged or "event" in message or not message.get("data"):
            raise ValueError("missing confirmed mark-price subscription or data")
        envelopes, _, _ = process_public_events_v1(events=[message], state=state)
        if len(envelopes) != len(message["data"]):
            raise ValueError("invalid mark-price rows")
        # One local receipt per transport message, including multi-row pushes.
        captured = datetime.fromtimestamp(received_ns / 1e9, timezone.utc).isoformat()
        for item in envelopes:
            row = item.payload["data"][0]
            if row.get("instType") != ref["instrument_type"]:
                raise ValueError("mark instrument type mismatch")
            fact = normalize_ticker_row_to_mark_price_fact_v1(
                row,
                instrument_ref=ref,
                captured_at=captured,
                session_id=identity["session"],
                duplicate=item.duplicate,
                corrected=item.corrected,
                out_of_order=item.out_of_order,
            )
            emit(
                dict(
                    kind="mark",
                    event_ms=item.event_ts_ms,
                    received_ns=received_ns,
                    received_mono_ns=received_mono_ns,
                    mark_px=fact.mark_px,
                    raw_row=row,
                    duplicate=item.duplicate,
                    corrected=item.corrected,
                    out_of_order=item.out_of_order,
                )
            )
    if not acknowledged:
        raise ValueError("public mark subscription unconfirmed")


def record(args):
    from websocket import WebSocketTimeoutException, create_connection
    from src.ops.canonical_runtime_environment_contract_v1.preflight_v1 import (
        assert_http_client_proxy_env_clean_v1,
    )

    if not 0 < args.seconds <= 7200:
        raise ValueError("measurement duration must be within two hours")
    identity = reference_identity(args)
    assert_http_client_proxy_env_clean_v1()
    url = load_ratified_eea_public_ws_binding_v1().ws_base_url
    with args.output.open("x", encoding="utf-8", buffering=1) as handle:

        def emit(row):
            handle.write(json.dumps(row, allow_nan=False) + "\n")

        emit(
            dict(
                kind="start",
                schema="nonlive_mark_reference.v1",
                endpoint=url,
                clock_host=platform.node(),
                **identity,
            )
        )
        socket = create_connection(url, timeout=10, redirect_limit=0, suppress_origin=True)
        try:
            if socket.getstatus() != 101:
                raise ValueError("unexpected public websocket handshake")
            capture(socket, identity, args.seconds, emit, timeout_error=WebSocketTimeoutException)
            emit(dict(kind="end", complete=True))
        finally:
            socket.close()


def distribution(values):
    if not values:
        return {"n": 0}
    ordered = sorted(values)
    return dict(
        n=len(values),
        median_ms=median(ordered),
        p95_ms=ordered[math.ceil(0.95 * len(values)) - 1],
        maximum_ms=ordered[-1],
    )


def compare(reference, timing_dir):
    with reference.open() as f:
        header = json.loads(next(f))
        if header.get("schema") != "nonlive_mark_reference.v1" or header["kind"] != "start":
            raise ValueError("invalid reference header")
        records = [json.loads(line) for line in f]
    marks = [
        r for r in records if r["kind"] == "mark" and not (r["out_of_order"] or r["duplicate"])
    ]
    arrivals = [r["received_ns"] for r in marks]
    mono_arrivals = [r["received_mono_ns"] for r in marks]
    if arrivals != sorted(arrivals):
        raise ValueError("local wall clock moved backwards during reference capture")
    if mono_arrivals != sorted(mono_arrivals):
        raise ValueError("invalid monotonic reference chronology")

    def latest_arrived_mark(host, wall, mono):
        if not host or host != header.get("clock_host") or not arrivals:
            return None
        if arrivals[0] <= wall <= arrivals[-1] and mono_arrivals[0] <= mono <= mono_arrivals[-1]:
            return marks[bisect_right(mono_arrivals, mono) - 1]
        return None

    samples = defaultdict(list)
    changed = []
    for previous, current in zip(marks, marks[1:]):
        samples["reference_receive_interval"].append(
            (current["received_mono_ns"] - previous["received_mono_ns"]) / 1e6
        )
        if Decimal(previous["mark_px"]) != Decimal(current["mark_px"]):
            changed.append((current["received_ns"] - current["event_ms"] * 1_000_000) / 1e6)
    samples["reference_changed_mark_event_to_receive"] = changed
    for r in marks:
        samples["reference_event_to_receive"].append(
            (r["received_ns"] - r["event_ms"] * 1_000_000) / 1e6
        )
    count = paired = newer = corrected = over = n_target = 0
    scope_missing = profiler_unavailable = host_only_count = 0
    switches, publications = {}, {}
    decision_times = []
    decisions_with_newer_reference = decisions_with_different_value = 0
    decisions_nonnegative = decisions_within_target = 0
    for path in (timing_dir / "consumer").glob("*.json"):
        row = json.loads(path.read_bytes())
        if row.get("schema") != "nonlive_mark_timing.v1" or any(
            row.get(k) != header[k]
            for k in ("mode", "session", "lane", "native_id", "canonical_id")
        ):
            continue
        count += 1
        samples["rest_event_to_receipt"].append(
            (row["receipt_unix_ns"] - row["event_ms"] * 1_000_000) / 1e6
        )
        status = row["profile_status"]
        host_only_count += int(status == "HOST_ONLY")
        profiler_unavailable += int(status not in {"ACTIVE", "HOST_ONLY"})
        scope_missing += int(
            status == "ACTIVE"
            and not any(
                c.get("returned")
                and c["stage"] in {"double_play_scope_l6_l10", "shadow_scope_event"}
                for c in row["calls"]
            )
        )
        start, mono = row["host_start_unix_ns"], row["host_start_mono_ns"]
        card_start, card_end = (
            row.get("paper_card_start_mono_ns"),
            row.get("paper_card_end_mono_ns"),
        )
        if (
            row["mode"] == "PAPER"
            and card_start is not None
            and card_end is not None
            and card_start <= card_end <= mono
        ):
            samples["paper_card_update"].append((card_end - card_start) / 1e6)
            samples["paper_card_return_to_host_start"].append((mono - card_end) / 1e6)
        if status in {"ACTIVE", "HOST_ONLY"} and row.get("host_end_mono_ns") is not None:
            metric = "host_processing" if status == "HOST_ONLY" else "profiled_host_processing"
            samples[metric].append((row["host_end_mono_ns"] - mono) / 1e6)
        current = latest_arrived_mark(row.get("clock_host"), start, mono)
        if current is not None:
            samples["reference_minus_host_input_event_time"].append(
                current["event_ms"] - row["event_ms"]
            )
        if status != "ACTIVE":
            continue
        master_starts = {
            c["cycle_id"]: c["start_mono_ns"]
            for c in row["calls"]
            if c["stage"] in {"master_v2", "shadow_master_v2_replay"} and c.get("returned")
        }
        for call in row["calls"]:
            if not call.get("returned"):
                continue
            samples[call["stage"]].append(call["duration_ns"] / 1e6)
            if (
                row["mode"] == "PAPER"
                and row.get("paper_episode_id")
                and call["stage"] == "double_play_l10"
                and type(call.get("switch_condition_met")) is bool
            ):
                # L10 has made a decision for both hold and switch. Compare at its return.
                end_mono = call["end_mono_ns"]
                end_wall = start + end_mono - mono
                current = latest_arrived_mark(row.get("clock_host"), end_wall, end_mono)
                if current is not None:
                    age = (end_wall - row["event_ms"] * 1_000_000) / 1e6
                    outcome = "switch" if call["switch_condition_met"] else "hold"
                    samples["paired_event_to_l10_decision"].append(age)
                    samples["paired_event_to_l10_" + outcome].append(age)
                    samples["paired_receipt_to_l10_decision"].append(
                        (end_wall - row["receipt_unix_ns"]) / 1e6
                    )
                    decisions_with_newer_reference += int(current["event_ms"] > row["event_ms"])
                    decisions_with_different_value += int(
                        Decimal(current["mark_px"]) != Decimal(row["mark_px"])
                    )
                    decisions_nonnegative += int(age >= 0)
                    decisions_within_target += int(0 <= age <= 300)
                    decision_times.append(end_mono)
            if call["stage"] == "double_play_l10" and call.get("switch_condition_met"):
                at_signal = start + call["end_mono_ns"] - mono
                samples["rest_event_to_l10_switch"].append(
                    (at_signal - row["event_ms"] * 1_000_000) / 1e6
                )
                samples["rest_receipt_to_l10_switch"].append(
                    (at_signal - row["receipt_unix_ns"]) / 1e6
                )
                switches.setdefault(call["cycle_id"], []).append((row, call))
            if call["stage"] == "paper_reversal_publication":
                publications.setdefault(call["cycle_id"], []).append((row, call))
            if call["stage"] in {"master_v2", "shadow_master_v2_replay"}:
                since_host = call["start_mono_ns"] - mono
                samples["host_start_to_master_v2"].append(since_host / 1e6)
                samples["rest_receipt_to_master_v2"].append(
                    (start + since_host - row["receipt_unix_ns"]) / 1e6
                )
            if call["stage"] not in {"double_play_scope_l6_l10", "shadow_scope_event"}:
                continue
            # Cross-clock ages are apparent ages. Local stage durations use only monotonic time.
            at = start + call["start_mono_ns"] - mono
            parent = master_starts.get(call["cycle_id"])
            if parent is not None and parent <= call["start_mono_ns"]:
                samples["master_v2_start_to_scope_start"].append(
                    (call["start_mono_ns"] - parent) / 1e6
                )
            age_ms = (at - row["event_ms"] * 1_000_000) / 1e6
            samples["rest_event_to_scope_start"].append(age_ms)
            samples["rest_receipt_to_scope_start"].append((at - row["receipt_unix_ns"]) / 1e6)
            current = latest_arrived_mark(row.get("clock_host"), at, call["start_mono_ns"])
            if current is not None:
                paired += 1
                newer += int(current["event_ms"] > row["event_ms"])
                corrected += int(
                    current["event_ms"] == row["event_ms"]
                    and Decimal(current["mark_px"]) != Decimal(row["mark_px"])
                )
                if age_ms >= 0:
                    n_target += 1
                    over += int(age_ms > 300)
                samples["reference_minus_consumed_event_time"].append(
                    current["event_ms"] - row["event_ms"]
                )
    for key in switches.keys() & publications.keys():
        if len(switches[key]) == len(publications[key]) == 1:
            original, switch = switches[key][0]
            publication, booking = publications[key][0]
            host = original.get("clock_host")
            signal, booked = switch["end_mono_ns"], booking["end_mono_ns"]
            if host and host == publication.get("clock_host") and booked >= signal:
                samples["l10_switch_to_paper_publication"].append((booked - signal) / 1e6)
                signal_wall = (
                    original["host_start_unix_ns"] + signal - original["host_start_mono_ns"]
                )
                booked_wall = (
                    publication["host_start_unix_ns"] + booked - publication["host_start_mono_ns"]
                )
                if (
                    booking.get("booking_confirmed") is True
                    and original.get("paper_episode_id")
                    and original["paper_episode_id"] == publication.get("paper_episode_id")
                    and original["event_ms"] * 1_000_000
                    <= original["receipt_unix_ns"]
                    <= signal_wall
                    <= booked_wall
                    and latest_arrived_mark(host, signal_wall, signal) is not None
                    and latest_arrived_mark(host, booked_wall, booked) is not None
                ):
                    age = (signal_wall - original["event_ms"] * 1_000_000 + booked - signal) / 1e6
                    samples["paired_event_to_confirmed_paper_booking"].append(age)
    decision_times.sort()
    samples["paired_l10_decision_interval"] = [
        (end - start) / 1e6 for start, end in zip(decision_times, decision_times[1:])
    ]
    return dict(
        identity={k: header[k] for k in ("session", "lane", "native_id", "mode")},
        reference_complete=bool(records and records[-1].get("complete")),
        reference_push_rows=len(marks),
        changed_marks_above_300ms=sum(a > 300 for a in changed),
        host_observations=count,
        host_only_observations=host_only_count,
        profiled_host_observations_without_scope=scope_missing,
        profiler_unavailable=profiler_unavailable,
        scope_starts_in_reference_window=paired,
        scope_starts_with_different_mark_same_timestamp=corrected,
        scope_starts_with_newer_reference=newer,
        scope_starts_above_300ms=over,
        scope_starts_with_nonnegative_age=n_target,
        paired_l10_decisions=len(decision_times),
        paired_l10_decisions_with_nonnegative_age=decisions_nonnegative,
        paired_l10_decisions_within_300ms=decisions_within_target,
        paired_confirmed_paper_bookings=len(samples["paired_event_to_confirmed_paper_booking"]),
        paired_confirmed_paper_bookings_within_300ms=sum(
            age <= 300 for age in samples["paired_event_to_confirmed_paper_booking"]
        ),
        paired_l10_decisions_with_newer_reference=decisions_with_newer_reference,
        paired_l10_decisions_with_different_reference_price=decisions_with_different_value,
        durations={k: distribution(v) for k, v in samples.items()},
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="action", required=True)
    run = sub.add_parser("reference")
    target = run.add_mutually_exclusive_group(required=True)
    target.add_argument(
        "--slot-config", type=Path, help="Prepared ranked Paper or Shadow slot JSON"
    )
    target.add_argument(
        "--demo-bound", type=Path, help="BoundInstrumentV1 JSON from the BTC Demo lane"
    )
    run.add_argument("--demo-session", help="Original Demo writer_session_id, with --demo-bound")
    run.add_argument("--seconds", type=int, required=True, help="Public observation duration")
    run.add_argument(
        "--output", type=Path, required=True, help="New JSONL file in an existing directory"
    )
    report = sub.add_parser("compare")
    report.add_argument("--reference", required=True, type=Path)
    report.add_argument(
        "--timing-dir", required=True, type=Path, help="Host's PEAK_TRADE_NONLIVE_TIMING_DIR"
    )
    args = parser.parse_args()
    if args.action == "reference":
        record(args)
    else:
        print(json.dumps(compare(args.reference, args.timing_dir), indent=2, allow_nan=False))


if __name__ == "__main__":
    main()
