import json
from types import SimpleNamespace
from decimal import Decimal

import pytest

from scripts.ops import up_paper_measurement_v1 as study
from src.ops.exit_policy_producer_binding_v1.models_v1 import canonical_digest_v1


def args(tmp_path, slot=None):
    return SimpleNamespace(
        parent=tmp_path.resolve(),
        session="up_next",
        seconds=3600,
        slot_config=slot,
        research_input=None,
    )


def test_plan_with_missing_originals_creates_nothing(tmp_path, monkeypatch):
    before = list(tmp_path.iterdir())
    monkeypatch.setattr(study.subprocess, "Popen", lambda *a, **kw: pytest.fail("spawn"))
    assert study.prepare(args(tmp_path), now=1)["parallel_commands"] is None
    with pytest.raises(ValueError, match="AWAITING"):
        study.start_prepared(args(tmp_path))
    assert list(tmp_path.iterdir()) == before


def test_bound_plan_selects_same_session_and_preserves_driver_gates(tmp_path, monkeypatch):
    slot = tmp_path / "slot.json"
    slot.write_text(json.dumps(dict(session_id="up_next", paper_cap24={"root": "original-cap24"})))

    def preparation(a, *, current_at):
        assert current_at == 123 and a.slot_config == slot
        return dict(identity=dict(session="up_next"))

    monkeypatch.setattr(study, "preparation", preparation)
    a = args(tmp_path, slot)
    assert study.prepare(a, now=123)["status"] == "AWAITING_GVEF_RESEARCH_INPUT"
    a.research_input = slot
    monkeypatch.setattr(
        study, "verified_input", lambda *_: (SimpleNamespace(model_dump=lambda **_: {}), "digest")
    )
    plan = study.prepare(a, now=123)
    assert plan["session_started"] is False and plan["recorder_seconds"] == 3660
    cmds = plan["parallel_commands"]
    assert cmds["paper"][-4:] == [
        "--card-cap24-evidence-root",
        "original-cap24",
        "--duration-seconds",
        "3600",
    ]
    assert str(slot) in cmds["recorder"] and str(slot) in cmds["paper"]
    assert cmds["paper_environment"][study.CONFIRMATION_DIR].endswith(
        "up_next-measurement/confirmations"
    )
    a.session = "historical"
    with pytest.raises(ValueError, match="foreign session"):
        study.prepare(a, now=123)
    a.session = "up_next"
    (tmp_path / "up_next-paper").mkdir()
    with pytest.raises(ValueError, match="NEW_ISOLATED"):
        study.prepare(a, now=123)


def sample():
    identity = dict(session="s", lane="LANE_2", native_id="UP", binding_digest="b")
    plan = dict(cycle_id="s:occupied:10000:LANE_2", source_hashes={"mark": "h"})
    result = dict(decision_id="d", fill=dict(fill_id="f", event_time_unix=10.12))
    row = dict(
        schema="up_paper_confirmed.v1",
        **identity,
        cycle_id=plan["cycle_id"],
        decision_id="d",
        fill_id="f",
        result_digest=canonical_digest_v1(result),
        execution_mark_sha256="h",
        confirmed_ns=10_300_000_000,
        confirmed_mono_ns=500_000_000,
        clock_host="fixture",
    )
    return row, dict(
        result=result, plan=plan, identity=identity, signal_ms=10000, execution_ms=10100
    )


def test_confirmation_threshold_and_distinct_signal_execution_marks():
    row, kw = sample()
    r = study.confirmed_timing(row, **kw)
    assert r["within_300ms_from_signal"] and r["signal_mark_to_confirmation_ms"] == 300
    assert r["execution_mark_to_confirmation_ms"] == 200
    r = study.confirmed_timing(dict(row, confirmed_ns=row["confirmed_ns"] + 1), **kw)
    assert not r["within_300ms_from_signal"] and r["within_300ms_from_execution"]


@pytest.mark.parametrize(
    "field,value",
    [
        ("fill_id", "foreign"),
        ("decision_id", "wrong"),
        ("result_digest", "wrong"),
        ("binding_digest", "other"),
        ("confirmed_ns", 10_110_000_000),
    ],
)
def test_foreign_or_pre_fill_confirmation_rejected(field, value):
    row, kw = sample()
    with pytest.raises(ValueError):
        study.confirmed_timing(dict(row, **{field: value}), **kw)


def test_local_ws_metric_needs_same_host_causal_exact_mark_and_excludes_corrections():
    row, kw = sample()
    r = study.confirmed_timing(row, **kw)
    before = (Decimal("1"), row["confirmed_ns"] - 1, row["confirmed_mono_ns"] - 1_000_000)
    after = (Decimal("2"), row["confirmed_ns"] + 1, row["confirmed_mono_ns"] + 1)
    assert (
        study.matched_ws_ms(
            [before, after],
            {"clock_host": "fixture", "from_ns": 0, "until_ns": row["confirmed_ns"]},
            r,
            "1",
        )
        == 1
    )
    assert study.matched_ws_ms([before], {"clock_host": "other"}, r, "1") is None
    assert (
        study.matched_ws_ms(
            [after],
            {"clock_host": "fixture", "from_ns": 0, "until_ns": row["confirmed_ns"]},
            r,
            "2",
        )
        is None
    )
    assert (
        study.matched_ws_ms(
            [before],
            {"clock_host": "fixture", "from_ns": 0, "until_ns": row["confirmed_ns"]},
            r,
            "0.9",
        )
        is None
    )
    assert (
        study.matched_ws_ms(
            [before, (Decimal("2"), *before[1:])],
            {"clock_host": "fixture", "from_ns": 0, "until_ns": row["confirmed_ns"]},
            r,
            "1",
        )
        is None
    )


@pytest.mark.parametrize("good", [True, False])
def test_ready_requires_the_bound_connection_and_both_streams(tmp_path, good):
    from tests.ops.test_up_paper_ws_depth_v1 import PLAN, ACK, START, mark, book

    now = study.time.time_ns()
    ts = now // study.MS
    path = tmp_path / "public.jsonl"
    rows = [dict(kind="start", source="public_websocket", **PLAN)]
    messages = [m for _, m in ACK] + [mark(ts - START)]
    if good:
        messages.append(book(ts - START, 10, -1))
    for n, msg in enumerate(messages, 1):
        rows.append(dict(kind="frame", raw=json.dumps(msg), received_ns=now, frame=n))
    rows.append(dict(kind="end"))
    path.write_text("".join(json.dumps(r) + "\n" for r in rows))
    proc = SimpleNamespace(poll=lambda: None)
    if good:
        study.await_public_pair(
            proc, path, PLAN, Decimal(".01"), Decimal("1"), study.time.monotonic() + 2
        )
    else:
        with pytest.raises(ValueError, match="fresh jointly"):
            study.await_public_pair(
                proc, path, PLAN, Decimal(".01"), Decimal("1"), study.time.monotonic() + 2
            )


def test_research_worker_covers_producer_and_uses_actual_final_window(tmp_path, monkeypatch):
    from scripts.ops import nonlive_gvef_companion_v1 as companion

    log = []
    monkeypatch.setattr(
        companion, "_tick", lambda c, o, phase: log.append((phase, c.slot.starts_at.timestamp()))
    )
    identity = dict(
        session="test",
        lane="LANE_2",
        canonical_id="UP",
        native_id="UP-FUT",
        occupancy_digest="c" * 64,
    )
    packet = dict(
        identity=identity,
        paper_root=str(tmp_path / "paper" / "test"),
        evidence_root=str(tmp_path / "measure"),
        paper_seconds=3600,
        gvef={"research": {"input": dict(template="/t", bars="/b", config="/c")}},
    )
    root = tmp_path / "paper" / "test"
    root.mkdir(parents=True)
    (root / "window.json").write_text(json.dumps(dict(started_at=42, duration_seconds=3600)))
    packet["gvef"]["research"]["digest"] = "original"
    monkeypatch.setattr(study, "research_digest", lambda *_: "original")
    campaign = study.paper_campaign(packet, 38)
    assert campaign.slot.n5_selection_digest == identity["occupancy_digest"]
    assert not campaign.state.is_relative_to(campaign.paper_runs)
    with companion.paired_gvef(
        campaign, tmp_path / "worker", final_campaign=lambda: study.closed_paper_campaign(packet)
    ):
        log.append(("paper", 40))
    assert log == [("start", 38), ("paper", 40), ("closeout", 42)]
    with pytest.raises(ValueError, match="abort"):
        with companion.paired_gvef(campaign, tmp_path / "failed"):
            raise ValueError("abort")
    assert log[-1] == ("start", 38)


def test_shadow_gvef_requires_original_decision_session_and_lane(tmp_path, monkeypatch):
    from datetime import datetime, timedelta, timezone
    from scripts.ops import run_i17_shadow_learning_companion_v1 as shadow
    from scripts.ops import nonlive_gvef_companion_v1 as companion
    from scripts.ops import run_recurrent_offline_research_v1 as research

    inst = shadow.require_i17_shadow_instrument_v1(["UP-USDT-SWAP"])
    now = datetime.now(timezone.utc) - timedelta(minutes=1)
    run = tmp_path / "follow" / "run"
    evidence = tmp_path / "shadow" / "s" / "evidence"
    path = tmp_path / "campaign.json"
    slot = dict(
        surface="SHADOW",
        session_id="s",
        lane_id="LANE_1",
        instrument_id=inst.canonical_id,
        venue_native_id=inst.native_id,
        n5_selection_digest="d" * 64,
        starts_at=now.isoformat(),
        ends_at=(now + timedelta(hours=2)).isoformat(),
    )
    campaign = dict(
        state=str(tmp_path / "state"),
        paper_runs=str(tmp_path / "paper"),
        shadow_follow_ups=str(run.parent),
        shadow_runs=str(tmp_path / "shadow"),
        research_inputs={inst.canonical_id: [dict(template="/t", bars="/b", config="/c")]},
        jobs_per_tick=1,
        history_jobs=4,
        retry_seconds=300,
        slot=slot,
    )

    def call():
        path.write_text(json.dumps(campaign))
        return shadow.shadow_gvef(
            path,
            run,
            evidence,
            SimpleNamespace(instrument_allowlist=[inst.native_id], session_id="s"),
            SimpleNamespace(selection=SimpleNamespace(integrity_digest="d" * 64)),
        )

    monkeypatch.setattr(
        research,
        "_input_bundle",
        lambda _: (
            dict(instrument_id=inst.canonical_id, observed_surface="SHADOW"),
            None,
            None,
            None,
        ),
    )
    monkeypatch.setattr(companion, "research_digest", lambda *_: "original")
    monkeypatch.setattr(
        companion, "paired_gvef", lambda c, p, **kw: (kw["final_campaign"]().slot.session_id, p)
    )
    assert call() == ("s", run / "gvef")
    slot["lane_id"] = "LANE_4"
    with pytest.raises(ValueError, match="SESSION_SCOPE"):
        call()
    slot["lane_id"] = "LANE_1"
    slot["session_id"] = "foreign"
    with pytest.raises(ValueError, match="SESSION_SCOPE"):
        call()
