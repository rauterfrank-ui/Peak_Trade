"""Bounded self-learning readback through the original DDO and O4 consumers."""

from __future__ import annotations

import json
import math
import subprocess
from pathlib import Path

import pytest

from src.learning.deterministic_decision_outcome_v0 import (
    offline_learning_follow_up_v1 as follow_up,
)
from src.learning.deterministic_decision_outcome_v0.capture_v0 import (
    SEAM_DOUBLE_PLAY_ENTRY_EXIT,
    DdoCaptureBindingV0,
    observe_producer_result_v0,
)
from src.learning.deterministic_decision_outcome_v0.errors_v0 import DdoValidationError
from src.learning.deterministic_decision_outcome_v0.ledger_v0 import AppendOnlyDdoLedgerV0
from tests.learning.test_ddo_double_play_producer_input_evidence_capture_v1 import (
    DoublePlayEntryExitPolicyV0,
    _enter_input,
    _hold_input,
    evaluate_double_play_entry_exit_policy_v0,
)
from tests.learning.test_ddo_o4_n_bars_productive_chain_v1 import _o4_bar, _snapshot

REPO = Path(__file__).resolve().parents[2]
SCOPE = {
    "session_id": "offline-sl-fixture",
    "account_scope": "offline-fixture",
    "code_sha": "1" * 64,
    "config_hash": "2" * 64,
    "instrument_id": "inst-eth-usdt-perp",
    "native_instrument_id": "ETH-USDT-SWAP",
    "venue": "okx_eea",
    "n_bars": 2,
}


def _time(hour, minute=0):
    return f"2026-09-01T{hour:02d}:{minute:02d}:00Z"


def _capture(ledger_path, decision_input, *, event_time):
    policy = DoublePlayEntryExitPolicyV0()
    result = evaluate_double_play_entry_exit_policy_v0(decision_input, policy)
    binding = DdoCaptureBindingV0(
        enabled=True, ledger_path=ledger_path, capture_scope_config_hash=SCOPE["config_hash"]
    )
    capture = observe_producer_result_v0(
        binding,
        seam_id=SEAM_DOUBLE_PLAY_ENTRY_EXIT,
        result=result,
        args=(decision_input, policy),
        event_time_utc=event_time,
        cycle_id="offline-ddo:" + event_time,
        correlation_id="offline-correlation",
        repository_sha=SCOPE["code_sha"],
    )
    assert capture["durable_ok"] is True
    return capture["record_id"]


def _request(*refs, at):
    return {"scope": SCOPE, "candidate_decision_refs": list(refs), "planned_at_utc": at}


def _source(ref, start_hour, first, last, *, known_at=None):
    bars = []
    for hour, price in ((start_hour, first), (start_hour + 1, last)):
        bar = _o4_bar(open_iso=_time(hour), close_iso=_time(hour + 1), close_price=price)
        bar.update(
            canonical_instrument_id=SCOPE["instrument_id"],
            venue_instrument_id=SCOPE["native_instrument_id"],
            repository_sha=SCOPE["code_sha"],
            config_digest=SCOPE["config_hash"],
        )
        bar["last_observation_identity"].update(
            canonical_instrument_id=SCOPE["instrument_id"],
            venue_instrument_id=SCOPE["native_instrument_id"],
        )
        bars.append(bar)
    return {
        "known_at_utc": known_at or _time(start_hour + 2, 1),
        "snapshot": _snapshot(
            decision_event_ref=ref, horizon_start_time_utc=_time(start_hour), o4_bars=bars
        ),
    }


def _cli(root, cycle, action, *, packet=None, digest=None):
    args = [str(REPO / "scripts/pt"), "scripts/ops/run_offline_ddo_learning_follow_up_v1.py"]
    args.extend(("--root", str(root), "--cycle", cycle, action))
    if packet is not None:
        path = root / f"{cycle}-{action}-input.json"
        path.write_text(json.dumps(packet))
        args.extend(("--request" if action == "plan" else "--source", str(path)))
    if digest is not None:
        args.extend(("--plan-digest", digest))
    proc = subprocess.run(args, cwd=REPO, capture_output=True, text=True)
    assert proc.returncode == 0, proc.stderr
    return json.loads(proc.stdout)


@pytest.fixture
def offline_workspace(tmp_path):
    root = tmp_path.resolve()
    path = follow_up.offline_learning_ledger_path_v1(root, SCOPE["account_scope"])
    initial_ref = _capture(path, _hold_input(), event_time=_time(12))
    return root, path, initial_ref


def test_two_process_cycles_consume_and_advance_the_saved_learning_state(offline_workspace):
    root, path, initial_ref = offline_workspace
    first_plan = _cli(root, "first", "plan", packet=_request(initial_ref, at=_time(12, 5)))
    assert first_plan["plan"]["prior_state_record_ref"] is None
    first = _cli(
        root,
        "first",
        "complete",
        packet=_source(initial_ref, 13, 100, 110),
        digest=first_plan["plan_digest"],
    )
    assert first["learning_state_version"] == 1
    assert first["log_return"] == pytest.approx(math.log(110 / 100))

    earlier = _capture(path, _enter_input(), event_time=_time(15, 30))
    same_class = _capture(path, _hold_input(), event_time=_time(15, 45))
    second_plan = _cli(
        root, "second", "plan", packet=_request(earlier, same_class, at=_time(15, 50))
    )
    plan = second_plan["plan"]
    assert plan["prior_state_record_ref"] == first["learning_state_record_ref"]
    assert plan["prior_state_content_hash"] == first["learning_state_content_hash"]
    assert plan["chronological_first_ref"] == earlier
    assert plan["selected"]["decision_ref"] == same_class
    assert plan["prior_decision_class"] == plan["selected"]["decision_class"] == "hold"

    source = _source(same_class, 16, 110, 99)
    second = _cli(root, "second", "complete", packet=source, digest=second_plan["plan_digest"])
    assert second["learning_state_version"] == 2
    assert second["prior_state_record_ref"] == first["learning_state_record_ref"]
    assert second["log_return"] == pytest.approx(math.log(99 / 110))
    assert second["decision_ref"] == same_class
    assert second["source_profile"] == "SYNTHETIC_OFFLINE"
    assert second["authority"] == "NONE"
    assert _cli(root, "second", "readback", digest=second_plan["plan_digest"]) == second

    saved = path.read_bytes()
    assert (
        _cli(root, "second", "complete", packet=source, digest=second_plan["plan_digest"]) == second
    )
    assert path.read_bytes() == saved
    rows = AppendOnlyDdoLedgerV0(path).read_all()
    assert [
        row["decision_event_ref"] for row in rows if row["schema_name"] == "outcome_record"
    ] == [initial_ref, same_class]


def test_rejects_future_candidates_and_wrong_measurement(offline_workspace):
    root, path, initial_ref = offline_workspace
    with pytest.raises(DdoValidationError, match="CANDIDATE_NOT_PROSPECTIVE"):
        follow_up.prepare_offline_learning_follow_up_v1(
            root, "too-early", _request(initial_ref, at=_time(11, 59))
        )
    plan = follow_up.prepare_offline_learning_follow_up_v1(
        root, "first", _request(initial_ref, at=_time(12, 5))
    )
    saved = path.read_bytes()
    for source, reason in (
        (_source(initial_ref, 14, 100, 110), "MEASUREMENT_SCOPE_MISMATCH"),
        (_source(initial_ref, 13, 100, 110, known_at=_time(14, 59)), "MEASUREMENT_TIME_MISMATCH"),
    ):
        with pytest.raises(DdoValidationError, match=reason):
            follow_up.complete_offline_learning_follow_up_v1(
                root, "first", plan_digest=plan["plan_digest"], source=source
            )
    assert path.read_bytes() == saved


def test_recovery_after_state_append_and_stale_competing_plan(offline_workspace, monkeypatch):
    root, path, initial_ref = offline_workspace
    request = _request(initial_ref, at=_time(12, 5))
    first = follow_up.prepare_offline_learning_follow_up_v1(root, "first", request)
    stale = follow_up.prepare_offline_learning_follow_up_v1(root, "competing", request)
    original_publish = follow_up._publish
    source = _source(initial_ref, 13, 100, 110)

    def fail_after_ingest(target, body):
        if target.name == "result.json":
            raise OSError("injected result publication failure")
        return original_publish(target, body)

    with monkeypatch.context() as patch:
        patch.setattr(follow_up, "_publish", fail_after_ingest)
        with pytest.raises(OSError, match="injected result publication failure"):
            follow_up.complete_offline_learning_follow_up_v1(
                root, "first", plan_digest=first["plan_digest"], source=source
            )
    saved = path.read_bytes()
    with pytest.raises(DdoValidationError, match="LEARNING_STATE_PREDECESSOR_CHANGED"):
        follow_up.complete_offline_learning_follow_up_v1(
            root, "competing", plan_digest=stale["plan_digest"], source=source
        )
    result = follow_up.complete_offline_learning_follow_up_v1(
        root, "first", plan_digest=first["plan_digest"], source=source
    )
    assert result["learning_state_version"] == 1
    assert path.read_bytes() == saved

    receipt = root / "sl-follow-up/first/measurement.json"
    content = json.loads(receipt.read_bytes())
    content["body"]["measurement"]["log_return"] = 999
    receipt.write_text(json.dumps(content))
    with pytest.raises(DdoValidationError, match="RECEIPT_DIGEST"):
        follow_up.read_offline_learning_follow_up_v1(
            root, "first", plan_digest=first["plan_digest"]
        )
