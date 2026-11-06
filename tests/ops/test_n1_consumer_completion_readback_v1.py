"""Lost handoff ACK: original consumer readback, actual Core counts and fencing."""

from dataclasses import replace
from decimal import Decimal
import hashlib
import json
from pathlib import Path
import subprocess

import pytest

from src.ops.current_mf_n5_full_autonomy_occupied_lane_mv2_dp_decision_state_addressing_join_v1 import (
    addressing_join_v1 as addressing,
)
from src.ops.current_mf_n5_full_autonomy_occupied_lane_n1_host_join_readiness_v1 import (
    consumer_completion_v1 as completion,
)
from src.ops.current_mf_n5_full_autonomy_productive_runtime_orchestrator_v1 import (
    PostCloseContinuationError,
    PostCloseContinuationReplayV1,
    run_productive_full_autonomy_n5_runtime_orchestrator_v1 as run,
)
from src.ops.current_mf_n5_full_autonomy_productive_runtime_orchestrator_v1 import (
    post_close_continuation_v1 as continuation,
)
from src.ops.portfolio_capital_reservation_budget_v1.contract_v1 import (
    PortfolioCapitalReservationBudgetOwnerV1,
)
from src.ops.portfolio_capital_reservation_budget_v1.recovery_v1 import (
    reconcile_durable_budget_startup_v1,
)
from src.ops.single_selected_future_runtime_binding_v1.models_v1 import BoundInstrumentV1
from tests.ops import test_productive_n1_post_close_continuation_v1 as inputs


def _count_actual_core(monkeypatch):
    calls = []
    original = addressing.run_current_productive_master_v2_runtime_cycle_v1

    def observed(**kwargs):
        calls.append(kwargs["cycle_id"])
        return original(**kwargs)

    monkeypatch.setattr(addressing, "run_current_productive_master_v2_runtime_cycle_v1", observed)
    return calls


@pytest.fixture
def lost_ack(tmp_path, monkeypatch):
    args, owner, writer, _ = inputs._fixture(tmp_path, monkeypatch)
    calls = _count_actual_core(monkeypatch)

    def interrupted(*args, **kwargs):
        raise OSError("lost handoff ACK")

    monkeypatch.setattr(continuation, "acknowledge_post_close_consumer_v1", interrupted)
    try:
        with pytest.raises(OSError, match="lost handoff ACK"):
            run(**args)
        handoff = next(writer.state_root.glob("post_close/*.json"))
        record = json.loads(handoff.read_text())
        assert record["phase"] == "CONSUMING"
        output = next(args["topology_state_root_base"].glob("**/n1_consumer_completions_v1/*.json"))
        assert calls[-1] == "after-close:LANE_1:LANE_1"
        yield args, owner, writer, calls, handoff, output
    finally:
        owner.close()
        writer.release()


@pytest.fixture
def pending_publication(tmp_path, monkeypatch):
    args, owner, writer, _ = inputs._fixture(tmp_path, monkeypatch)
    calls = _count_actual_core(monkeypatch)
    original_link = completion.os.link
    fail_once = True

    def interrupted(source, destination, *args, **kwargs):
        nonlocal fail_once
        if (
            fail_once
            and Path(destination).parent.name == completion.DIRECTORY
            and not str(destination).endswith(".pending.json")
        ):
            fail_once = False
            raise OSError("original output prepared; final publication interrupted")
        return original_link(source, destination, *args, **kwargs)

    monkeypatch.setattr(completion.os, "link", interrupted)
    try:
        with pytest.raises(OSError, match="final publication interrupted"):
            run(**args)
        handoff = next(writer.state_root.glob("post_close/*.json"))
        pending = next(args["topology_state_root_base"].glob("**/*.pending.json"))
        assert json.loads(handoff.read_text())["phase"] == "CONSUMING"
        assert calls[-1] == "after-close:LANE_1:LANE_1"
        yield args, owner, writer, calls, handoff, pending
    finally:
        owner.close()
        writer.release()


def test_prepared_original_output_automatically_restores_publication_and_ack(pending_publication):
    args, owner, _writer, calls, _handoff, pending = pending_publication
    before = list(calls), owner.budget_state_v1()
    original = json.loads(pending.read_text())
    replay = run(**args)
    assert isinstance(replay, PostCloseContinuationReplayV1)
    assert replay.receipt["phase"] == "ACKED"
    assert replay.receipt["consumer_completion_digest"] == original["content_digest"]
    assert (calls, owner.budget_state_v1()) == before
    final = pending.with_name(pending.name.replace(".pending.json", ".json"))
    assert json.loads(final.read_text()) == original and not pending.exists()
    assert run(**args).receipt == replay.receipt
    assert calls == before[0]


def test_persistent_storage_error_retains_prepared_output_until_repair(
    pending_publication, monkeypatch
):
    args, owner, _writer, calls, handoff, pending = pending_publication
    before = pending.read_bytes(), handoff.read_bytes(), list(calls), owner.budget_state_v1()
    original_link = completion.os.link

    def still_unavailable(source, destination, *args, **kwargs):
        if Path(destination).parent.name == completion.DIRECTORY:
            raise OSError("storage temporarily unavailable")
        return original_link(source, destination, *args, **kwargs)

    with monkeypatch.context() as fault:
        fault.setattr(completion.os, "link", still_unavailable)
        with pytest.raises(PostCloseContinuationError, match="PUBLICATION_RETRY_REQUIRED"):
            run(**args)
    assert (pending.read_bytes(), handoff.read_bytes(), calls, owner.budget_state_v1()) == before
    assert run(**args).receipt["phase"] == "ACKED"
    assert calls == before[2]


@pytest.mark.parametrize("tamper", ["partial", "generation", "bootstrap", "effect"])
def test_invalid_prepared_output_is_not_automatically_published(pending_publication, tamper):
    args, owner, _writer, calls, handoff, pending = pending_publication
    record = json.loads(pending.read_text())
    if tamper == "partial":
        pending.write_text('{"schema":')
    else:
        if tamper == "generation":
            record["bound_instrument"]["selection_id"] = "foreign"
        elif tamper == "bootstrap":
            record["consumed"]["cycle_id"] = "after-close:LANE_1"
        else:
            record["external_effect_count"] = 1
        body = {k: v for k, v in record.items() if k != "content_digest"}
        record["content_digest"] = hashlib.sha256(
            json.dumps(body, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()
        ).hexdigest()
        pending.write_text(json.dumps(record))
    before = pending.read_bytes(), handoff.read_bytes(), list(calls), owner.budget_state_v1()
    with pytest.raises(PostCloseContinuationError, match="CORE_OUTCOME_UNCERTAIN"):
        run(**args)
    assert (pending.read_bytes(), handoff.read_bytes(), calls, owner.budget_state_v1()) == before


def test_recovery_preserves_original_output_later_hold_and_replay(lost_ack):
    args, owner, _writer, calls, handoff, output = lost_ack
    original_calls = list(calls)
    original_output = output.read_bytes()
    actual = json.loads(original_output)
    later = owner.try_reserve_v1(
        slot_id="LANE_1",
        decision_id="later",
        cycle_id="later",
        observation_id=owner.budget_state_v1().observation_id,
        amount=Decimal("10"),
    )
    assert later.reservation is not None
    budget_before = owner.budget_state_v1()
    replay = run(**args)
    assert isinstance(replay, PostCloseContinuationReplayV1)
    assert replay.receipt["acknowledgement_source"] == "ORIGINAL_N1_CONSUMER_COMPLETION_READBACK"
    assert replay.receipt["consumer_completion_digest"] == actual["content_digest"]
    assert replay.receipt["consumed"] == {"LANE_1": actual["consumed"]}
    assert replay.receipt["terminal_boundary"] == "PRE_EXTERNAL_EFFECT"
    first_ack = handoff.read_bytes()
    assert run(**args).receipt == replay.receipt
    assert handoff.read_bytes() == first_ack and output.read_bytes() == original_output
    assert owner.budget_state_v1() == budget_before and owner.active_sum_v1() == 10
    assert calls == original_calls


@pytest.mark.parametrize(
    "tamper",
    [
        "missing",
        "partial",
        "digest",
        "binding",
        "generation",
        "bootstrap",
        "input",
        "lane",
        "origin",
        "root",
        "producer",
        "failed",
        "permit",
        "post",
        "effect",
    ],
)
def test_unproven_completion_never_acknowledges_or_reexecutes(lost_ack, tamper):
    args, owner, _writer, calls, handoff, output = lost_ack
    record = json.loads(output.read_text())
    if tamper == "missing":
        output.unlink()
    elif tamper == "partial":
        output.write_text('{"schema":')
    else:
        if tamper == "digest":
            record["consumed"]["input_digest"] = "0" * 64
        elif tamper == "binding":
            record["binding_digest"] = "0" * 64
        elif tamper == "generation":
            record["bound_instrument"]["selection_id"] = "foreign-generation"
        elif tamper == "bootstrap":
            record["consumed"]["cycle_id"] = "after-close:LANE_1"
        elif tamper == "input":
            record["consumed"]["input_digest"] = "missing"
        elif tamper == "lane":
            record["lane_id"] = "LANE_2"
        elif tamper == "origin":
            record["origin_main_sha"] = "0" * 40
        elif tamper == "root":
            record["lane_state_root"] += "-foreign"
        elif tamper == "producer":
            record["producer"] = "unrelated-producer"
        elif tamper == "failed":
            record["disposition"] = "FAIL_CLOSED"
        elif tamper == "permit":
            record["permit_created"] = True
        elif tamper == "post":
            record["post_count"] = 1
        elif tamper == "effect":
            record["external_effect_count"] = 1
        if tamper != "digest":
            body = {k: v for k, v in record.items() if k != "content_digest"}
            record["content_digest"] = hashlib.sha256(
                json.dumps(body, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()
            ).hexdigest()
        output.write_text(json.dumps(record))
    before = handoff.read_bytes(), owner.budget_state_v1(), list(calls)
    with pytest.raises(PostCloseContinuationError, match="CORE_OUTCOME_UNCERTAIN"):
        run(**args)
    assert (handoff.read_bytes(), owner.budget_state_v1(), calls) == before


def test_aborted_completion_write_keeps_real_cursor_and_core_outcome_fenced(tmp_path, monkeypatch):
    args, owner, writer, _ = inputs._fixture(tmp_path, monkeypatch)
    calls = _count_actual_core(monkeypatch)
    original_link = completion.os.link

    def interrupted(source, destination, *args, **kwargs):
        if Path(destination).parent.name == completion.DIRECTORY and str(destination).endswith(
            ".pending.json"
        ):
            raise OSError("before durable consumer completion")
        return original_link(source, destination, *args, **kwargs)

    monkeypatch.setattr(completion.os, "link", interrupted)
    try:
        with pytest.raises(OSError, match="before durable"):
            run(**args)
        original_calls = list(calls)
        assert calls[-1] == "after-close:LANE_1:LANE_1"
        assert not list(
            args["topology_state_root_base"].glob("**/n1_consumer_completions_v1/*.json")
        )
        handoff = next(writer.state_root.glob("post_close/*.json"))
        before = handoff.read_bytes()
        with pytest.raises(PostCloseContinuationError, match="CORE_OUTCOME_UNCERTAIN"):
            run(**args)
        assert handoff.read_bytes() == before and calls == original_calls
    finally:
        owner.close()
        writer.release()


@pytest.mark.parametrize("interruption", ["lost_ack", "pending_publication"])
def test_lost_ack_after_owner_reopen_does_not_readmit_account(request, tmp_path, interruption):
    args, owner, writer, calls, _handoff, _output = request.getfixturevalue(interruption)
    previous_calls = list(calls)
    owner.close()
    writer.release()
    context = args["post_close_continuation"]
    restored = PortfolioCapitalReservationBudgetOwnerV1(
        durable_root=tmp_path / "budget",
        durable_account_identity="acct-1",
        durable_mode="recover",
        durable_lane_bindings={"LANE_1": context.request.bound_instrument},
    )
    new_writer = inputs.sources._held_writer(args["topology_state_root_base"])
    args.update(
        portfolio_budget_owner=restored,
        lane_assignment_writer=new_writer,
        post_close_continuation=replace(
            context, request=replace(context.request, budget_owner=restored)
        ),
    )
    try:
        before = restored.budget_state_v1()
        replay = run(**args)
        assert isinstance(replay, PostCloseContinuationReplayV1)
        assert replay.receipt["phase"] == "ACKED"
        assert restored.budget_state_v1() == before and not before.admitted
        assert calls == previous_calls
    finally:
        restored.close()
        new_writer.release()


@pytest.mark.parametrize("fresh", [True, False])
def test_recovered_ack_needs_fresh_original_budget_recovery_for_readiness(
    pending_publication, tmp_path, fresh
):
    args, owner, writer, calls, _handoff, _output = pending_publication
    previous_calls = list(calls)
    owner.close()
    writer.release()
    context = args["post_close_continuation"]
    restored = PortfolioCapitalReservationBudgetOwnerV1(
        durable_root=tmp_path / "budget",
        durable_account_identity="acct-1",
        durable_mode="recover",
        durable_lane_bindings={"LANE_1": context.request.bound_instrument},
    )
    new_writer = inputs.sources._held_writer(args["topology_state_root_base"])
    args.update(
        portfolio_budget_owner=restored,
        lane_assignment_writer=new_writer,
        post_close_continuation=replace(
            context, request=replace(context.request, budget_owner=restored)
        ),
    )
    try:
        replay = run(**args)
        assert replay.receipt["phase"] == "ACKED" and not restored.budget_state_v1().admitted
        bound = BoundInstrumentV1(**replay.receipt["bound_by_lane"]["LANE_1"])
        recovery = reconcile_durable_budget_startup_v1(
            restored,
            output=context.request.capital_handoff.producer_output,
            observed=context.budget_observed,
            lane_bindings={"LANE_1": bound},
            reconciliation_state_root=args["cap24_bind"].reconciliation_state_root,
            session_id="fresh-restart-admission",
            repository_sha=args["repository_sha"],
            now_unix=args["cap24_bind"].now_unix + (0 if fresh else 3600),
            capital_max_age_seconds=context.capital_max_age_seconds,
        )
        assert (recovery.disposition.value == "ADMITTED") is fresh
        assert restored.budget_state_v1().admitted is fresh
        assert calls == previous_calls
        assert restored.active_sum_v1() == 0
    finally:
        restored.close()
        new_writer.release()


@pytest.mark.parametrize("interruption", ["lost_ack", "pending_publication"])
def test_original_completion_readback_in_fresh_process(request, tmp_path, interruption):
    _args, _owner, _writer, calls, _handoff, output = request.getfixturevalue(interruption)
    body = json.loads(output.read_text())
    read_request = tmp_path / "readback.json"
    read_request.write_text(
        json.dumps(
            {
                "lane_state_root": body["lane_state_root"],
                "binding_digest": body["binding_digest"],
                "lane_id": body["lane_id"],
                "bound": body["bound_instrument"],
                "cycle_prefix": body["cycle_prefix"],
                "origin_main_sha": body["origin_main_sha"],
            }
        )
    )
    root = Path(__file__).resolve().parents[2]
    reader = (
        "recover_n1_consumer_completion_v1"
        if interruption == "pending_publication"
        else "read_n1_consumer_completion_v1"
    )
    code = (
        "import json,sys; from src.ops.current_mf_n5_full_autonomy_occupied_lane_n1_host_join_readiness_v1.consumer_completion_v1 "
        f"import {reader}; "
        f"print(json.dumps({reader}(**json.load(open(sys.argv[1])))))"
    )
    result = subprocess.run(
        [str(root / "scripts/pt"), "-c", code, str(read_request)],
        cwd=root,
        capture_output=True,
        text=True,
        check=True,
    )
    assert json.loads(result.stdout.splitlines()[-1]) == body
    assert calls[-1] == "after-close:LANE_1:LANE_1"


def test_original_completion_cannot_be_overwritten_with_different_output(tmp_path, monkeypatch):
    args, owner, writer, _ = inputs._fixture(tmp_path, monkeypatch)
    try:
        result = run(**args)
        receipt = result.post_close_continuation_receipt
        projections = result.readiness_projections
        kwargs = dict(
            binding_digest=receipt["binding_digest"],
            cycle_prefix=args["cycle_id_prefix"],
            origin_main_sha=args["origin_main_sha"],
        )
        path = next(args["topology_state_root_base"].glob("**/n1_consumer_completions_v1/*.json"))
        before = path.read_bytes()
        completion.persist_n1_consumer_completion_v1(projections, **kwargs)
        assert path.read_bytes() == before
        projection = projections["LANE_1"]
        consumer = projection.n1_consumer_result
        invocation = consumer.s7_invocation
        conflicting = replace(
            projection,
            n1_consumer_result=replace(
                consumer,
                s7_invocation=replace(
                    invocation,
                    cycle_result=replace(invocation.cycle_result, input_digest="f" * 64),
                ),
            ),
        )
        with pytest.raises(completion.N1ConsumerCompletionError, match="IMMUTABLE_OUTPUT_CONFLICT"):
            completion.persist_n1_consumer_completion_v1({"LANE_1": conflicting}, **kwargs)
        assert path.read_bytes() == before
    finally:
        owner.close()
        writer.release()
