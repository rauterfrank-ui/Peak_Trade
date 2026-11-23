import json
from types import SimpleNamespace
from decimal import Decimal

import pytest

from scripts.ops import up_paper_measurement_v1 as study
from src.ops.exit_policy_producer_binding_v1.models_v1 import canonical_digest_v1


def args(tmp_path, slot=None):
    return SimpleNamespace(
        parent=tmp_path.resolve(), session="up_next", seconds=3600, slot_config=slot
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
    (tmp_path / "up_next-inputs").mkdir()
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
