import json
from types import SimpleNamespace

import pytest

from scripts.ops import measure_nonlive_mark_path_v1 as measurement


IDENTITY = dict(
    mode="PAPER",
    session="up-paper",
    lane="LANE_2",
    native_id="UP-USD_UM_XPERP-310919",
    canonical_id="bound-up",
    binding_digest="e" * 64,
    instrument_type="FUTURES",
    settlement_asset="USD",
)


def test_reference_preserves_push_order_and_never_submits(monkeypatch):
    sub = {"channel": "mark-price", "instId": IDENTITY["native_id"]}
    row = {"instType": "FUTURES", "instId": sub["instId"], "ts": "1700000000000", "markPx": "0.25"}
    messages = iter(
        [
            {"event": "notice", "code": "64010"},
            {"event": "subscribe", "arg": sub},
            {"arg": sub, "data": [row, row, {**row, "markPx": "0.24"}]},
        ]
    )
    times = iter([0, 0, 0, 0, 2])
    monkeypatch.setattr(
        measurement,
        "time",
        SimpleNamespace(
            monotonic=lambda: next(times),
            time_ns=lambda: 1700000000046000000,
            perf_counter_ns=lambda: 42,
        ),
    )
    sent, saved = [], []
    ws = SimpleNamespace(
        send=sent.append, recv=lambda: json.dumps(next(messages)), settimeout=lambda _: None
    )
    measurement.capture(ws, IDENTITY, 1, saved.append)
    assert [json.loads(s) for s in sent] == [{"op": "subscribe", "args": [sub]}]
    assert saved[0]["kind"] == "endpoint_notice"
    assert [(r["duplicate"], r["corrected"]) for r in saved[1:]] == [
        (False, False),
        (True, False),
        (False, True),
    ]
    assert all(r["received_mono_ns"] == 42 for r in saved[1:])


def test_compare_only_uses_available_reference_for_the_matching_consumer(tmp_path):
    base = 1700000000000000000

    def push(event, receive, price):
        return dict(
            kind="mark",
            event_ms=base // 1000000 + event,
            received_ns=base + receive * 1000000,
            received_mono_ns=receive * 1000000,
            mark_px=price,
            out_of_order=False,
            duplicate=False,
        )

    def call(name, start, end, **kw):
        return dict(
            stage=name,
            cycle_id="original",
            start_mono_ns=start * 1000000,
            end_mono_ns=end * 1000000,
            duration_ns=(end - start) * 1000000,
            returned=True,
            **kw,
        )

    ref = tmp_path / "reference.jsonl"
    records = [
        dict(kind="start", schema="nonlive_mark_reference.v1", clock_host="one", **IDENTITY),
        push(100, 120, ".24"),
        push(200, 220, ".25"),
        push(300, 325, ".26"),
        dict(kind="end", complete=True),
    ]
    ref.write_text("".join(json.dumps(r) + "\n" for r in records))
    consumer = tmp_path / "consumer"
    consumer.mkdir()
    row = dict(
        **IDENTITY,
        schema="nonlive_mark_timing.v1",
        clock_host="one",
        profile_status="ACTIVE",
        paper_episode_id="original-simulated-fill",
        host_start_unix_ns=base,
        host_start_mono_ns=0,
        receipt_unix_ns=base + 140000000,
        event_ms=base // 1000000 + 100,
        mark_px=".24",
        calls=[
            call("double_play_scope_l6_l10", 240, 248),
            call("double_play_l10", 245, 246, switch_condition_met=True),
        ],
    )
    for i, value in enumerate(
        [
            row,
            {**row, "session": "other"},
            {**row, "canonical_id": "another-contract"},
            {**row, "calls": []},
            {**row, "calls": [call("paper_reversal_publication", 460, 480)]},
        ]
    ):
        (consumer / f"{i}.json").write_text(json.dumps(value))
    result = measurement.compare(ref, tmp_path)
    assert result["host_observations"] == 3
    assert (
        result["scope_starts_in_reference_window"]
        == result["scope_starts_with_newer_reference"]
        == 1
    )
    assert result["durations"]["reference_minus_consumed_event_time"]["median_ms"] == 100
    assert result["durations"]["l10_switch_to_paper_publication"]["median_ms"] == 234
    assert result["paired_l10_decisions"] == result["paired_l10_decisions_within_300ms"] == 1
    assert result["durations"]["paired_event_to_l10_decision"]["median_ms"] == 146
    assert result["paired_l10_decisions_with_newer_reference"] == 1
    # A returned L10 hold counts. A decision outside the reference window does not.
    extra = {
        **row,
        "event_ms": base // 1000000,
        "calls": [
            call("double_play_l10", 300, 310, switch_condition_met=False),
            call("double_play_l10", 350, 351, switch_condition_met=True),
        ],
    }
    (consumer / "holds.json").write_text(json.dumps(extra))
    (consumer / "entry.json").write_text(json.dumps({**extra, "paper_episode_id": None}))
    paired = measurement.compare(ref, tmp_path)
    assert paired["paired_l10_decisions"] == 2
    assert paired["paired_l10_decisions_within_300ms"] == 1
    assert paired["durations"]["paired_event_to_l10_hold"]["median_ms"] == 310
    assert paired["durations"]["paired_l10_decision_interval"]["median_ms"] == 64
    records[0]["clock_host"] = "another-host"
    ref.write_text("".join(json.dumps(r) + "\n" for r in records))
    assert measurement.compare(ref, tmp_path)["scope_starts_in_reference_window"] == 0
    assert measurement.compare(ref, tmp_path)["paired_l10_decisions"] == 0


def test_foreign_subscription_is_rejected():
    ws = SimpleNamespace(
        send=lambda _: None,
        settimeout=lambda _: None,
        recv=lambda: json.dumps(
            {"event": "subscribe", "arg": {"channel": "mark-price", "instId": "another"}}
        ),
    )
    with pytest.raises(ValueError, match="unexpected OKX subscription"):
        measurement.capture(ws, IDENTITY, 1, lambda _: None)


def test_baseline_clock_records_host_without_installing_profiler(tmp_path, monkeypatch):
    from src.ops import nonlive_mark_timing_v1 as timing

    monkeypatch.setenv("PEAK_TRADE_NONLIVE_TIMING_DIR", str(tmp_path))
    monkeypatch.delenv("PEAK_TRADE_NONLIVE_TIMING_STAGES", raising=False)
    monkeypatch.setattr(timing.sys, "setprofile", lambda _: pytest.fail("unexpected profiler"))
    with timing.observe_nonlive_mark_v1(
        mode="PAPER",
        session="s",
        lane="LANE_2",
        native="bound-up",
        canonical="bound-canonical",
        event_ms=1000,
        price=0.1,
        receipt=1.01,
    ):
        pass
    (path,) = (tmp_path / "consumer").glob("*.json")
    trace = json.loads(path.read_bytes())
    assert trace["profile_status"] == "HOST_ONLY" and trace["calls"] == []
    assert trace["host_end_mono_ns"] >= trace["host_start_mono_ns"]
