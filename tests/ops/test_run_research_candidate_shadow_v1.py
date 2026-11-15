"""Prospective replay must bind both profiles before collecting any scored data."""

from datetime import datetime, timedelta, timezone
import json

import pytest

from scripts.ops import run_research_candidate_shadow_v1 as replay
from src.evaluation.golden_vectors.integration.evaluation_receipt_v1 import (
    EvaluationReceiptArchiveV1,
)
from tests.ops.test_capture_offline_learning_mark_window_v1 import xperp_binding  # noqa: F401


def test_paired_window_registration_finality_and_immutable_readback(
    tmp_path, monkeypatch, xperp_binding
):
    workspace = EvaluationReceiptArchiveV1(tmp_path.resolve() / "out")
    instrument = xperp_binding["native_instrument_id"]
    start = datetime(2026, 11, 15, tzinfo=timezone.utc)
    parent_time = start - timedelta(minutes=15)
    revision = "f" * 40
    pair = {
        "parent_revision": "a" * 40,
        "candidate_known_at_utc": parent_time.isoformat(),
        "parent_data_known_at_utc": (parent_time - timedelta(days=1)).isoformat(),
        "instrument_id": instrument,
        "profiles": {
            "reference": {"parameters": {"fast_window": 10, "slow_window": 30}},
            "candidate": {"parameters": {"fast_window": 10, "slow_window": 40}},
        },
    }
    monkeypatch.setattr(replay, "_pair", lambda *_: pair)
    monkeypatch.setattr(replay, "_require_original_replay_code", lambda *_: None)
    args = dict(
        campaign=tmp_path / "campaign",
        evidence_digest="b" * 64,
        config={},
        binding=xperp_binding,
        start=start.isoformat(),
        hours=2,
        revision=revision,
    )
    with pytest.raises(ValueError, match="FUTURE_GRID_ALIGNED"):
        replay.prepare_v1(workspace, **args, now=start)
    assert not (workspace.root / "plan.json").exists()
    plan = replay.prepare_v1(workspace, **args, now=parent_time)
    assert replay.prepare_v1(workspace, **args, now=start) == plan

    end = start + 2 * replay.HOUR
    grid_start = replay._utc(plan["warmup_start_utc"])
    bar_times = [grid_start + n * replay.HOUR for n in range(replay.LOOKBACK_BARS + 3)]
    original_calls = []
    mark_closes = [100.0 + 0.1 * index * index for index, _ in enumerate(bar_times)]
    drop_mark = True

    def fetch(path, query):
        original_calls.append((path, query))
        if path == replay.ROLE_PATHS["funding"]:
            data = [
                {
                    "instId": instrument,
                    "instType": "FUTURES",
                    "fundingTime": replay._milliseconds(grid_start),
                    "realizedRate": "0.0001",
                }
            ]
        else:
            data = []
            for ts, price in zip(bar_times, mark_closes, strict=True):
                row = [str(replay._milliseconds(ts)), *([str(price)] * 4)]
                if path == replay.ROLE_PATHS["last"]:
                    row += ["12", "1.2", "12"]
                data.append([*row, "1"])
            if drop_mark and path == replay.ROLE_PATHS["mark"]:
                data.pop()
        return json.dumps({"code": "0", "data": data}).encode()

    with pytest.raises(ValueError, match="FORWARD_WINDOW_NOT_CLOSED"):
        replay.observe_v1(workspace, revision=revision, fetch=fetch, clock=lambda: start)
    assert not original_calls
    with pytest.raises(ValueError, match="FORWARD_INCOMPLETE_CANDLE_COVERAGE:mark"):
        replay.observe_v1(workspace, revision=revision, fetch=fetch, clock=lambda: end)
    assert not (workspace.root / "public-input.json").exists()
    drop_mark = False

    measured = []

    def measure(plan, bars, profile):
        assert list(bars.index[-3:].to_pydatetime()) == [start, start + replay.HOUR, end]
        measured.append((profile["parameters"]["slow_window"], tuple(bars["mark_price"])))
        return {"engine_pre_funding_return": 0.0}

    monkeypatch.setattr(replay, "_run_profile", measure)
    result = replay.observe_v1(workspace, revision=revision, fetch=fetch, clock=lambda: end)
    assert {case[0] for case in measured} == {30, 40}
    assert len({case[1] for case in measured}) == 1
    assert result["public_mark_log_return"]["from_close_utc"] == start.isoformat()
    assert result["public_mark_log_return"]["to_close_utc"] == end.isoformat()
    assert result["economic_qualification_status"] == "BLOCKED"
    assert result["reality_gap_status"] == "INCOMPLETE"
    calls = len(original_calls)
    assert replay.observe_v1(workspace, revision=revision, verify=True, fetch=fetch) == result
    assert len(original_calls) == calls
