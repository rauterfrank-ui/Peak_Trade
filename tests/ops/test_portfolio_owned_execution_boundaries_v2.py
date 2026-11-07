"""Original writers, synthetic failure boundaries and exact readback; no network."""

from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace
import json
from threading import Barrier

import pytest

from src.ops.full_core_live_path_composition_root_v1 import (
    envelope_bound_external_effect_send_seam_v1 as seam,
    external_effect_permit_durable_consume_v1 as consume,
)
from src.ops.full_core_live_path_composition_root_v1.full_core_exchange_reconciliation_v1 import (
    PortfolioExecutionReconciliationIdentityV2,
    parse_exchange_reconciliation_identity_v1,
)
from src.ops.portfolio_capital_reservation_budget_v1.durable_store_v1 import DurableBudgetStoreError
from tests.ops.test_n1_original_plan_origin_v1 import seed_with_origin, Owner, BoundInstrumentV1
from tests.ops.test_n1_original_reservation_host_handoff_v1 import (
    synthetic_ports_and_isolation as synthetic_ports_and_isolation,
)
from tests.ops.test_full_core_current_productive_envelope_bound_single_use_external_effect_send_seam_v1 import (
    _handle,
    _permit,
)


@pytest.mark.parametrize("environment", ["SHADOW", "PAPER_EXCHANGE", "TESTNET"])
def test_actual_venue_consumer_denies_the_original_non_live_plan(
    tmp_path, monkeypatch, environment
):
    from tests.ops.test_prepost_original_budget_context_v1 import execute, caller

    host, rid, _, envelope, intent, plan = seed_with_origin(tmp_path, monkeypatch, origin=None)
    try:
        host.owner.bind_execution_plan_v1(
            rid,
            envelope,
            canonical_intent=intent,
            venue_plan=replace(plan, environment=environment),
        )
        context = host.owner.execution_plan_context_v1(rid, envelope)
        sequence = host.owner._store.sequence
        with pytest.raises(
            caller.CurrentProductiveActualVenuePostError, match="ENVIRONMENT_MISMATCH"
        ):
            execute(
                dict(
                    envelope=envelope,
                    portfolio_budget_owner=host.owner,
                    portfolio_reservation_id=rid,
                    execution_plan_context=context,
                ),
                tmp_path,
                port=object(),
            )
        assert host.owner._store.sequence == sequence
        assert host.owner.execution_links_v1()[rid]["identity"] is None
        assert not consume.durable_consume_path_v1(tmp_path / "send").exists()
    finally:
        host.close()


def test_k1_transport_checks_the_exact_durable_permit_before_any_key_lookup(tmp_path, monkeypatch):
    from src.ops.full_core_live_path_composition_root_v1 import (
        current_productive_one_shot_fresh_envelope_permit_mint_durable_consume_and_post_join_v1 as lower,
    )

    host, rid, _, envelope, _, _ = seed_with_origin(tmp_path, monkeypatch)
    permit = _permit(envelope)
    try:
        context = host.owner.execution_plan_context_v1(rid, envelope)
        identity = host.owner.begin_execution_submit_v2(rid, envelope, context, permit)
        consume.persist_external_effect_durable_consume_v1(
            store_root=tmp_path / "send",
            permit=permit,
            envelope=envelope,
            durable_state="SENT_INITIATED",
            post_count=1,
            outcome="SYNTHETIC_UNCERTAINTY",
            execution_identity=identity,
        )
        probe = lower.OneShotJoinProbeV1()
        transport = lower._DurableConsumeThenK1HttpTransportV1(
            envelope=envelope,
            store_root=tmp_path / "send",
            k1_backend=object(),
            opener_factory=None,
            probe=probe,
            send_handle=_handle(),
        )
        with pytest.raises(
            lower.FullCoreProductiveHttpPostError, match="DURABLE_PERMIT_ID_MISMATCH"
        ):
            transport.post_trade_order(
                payload={},
                permit_id="foreign-permit",
                envelope_id=envelope.envelope_id,
                envelope_digest=envelope.envelope_digest,
                one_shot_real_post=True,
            )
        assert not probe.events
    finally:
        host.close()


@pytest.mark.parametrize(
    "phase", ["before_commit", "lost_ack", "readback", "between_barriers", "after_permit"]
)
def test_original_failure_boundaries_retain_hold_and_forbid_blind_retry(
    tmp_path, monkeypatch, phase
):
    host, rid, _legacy, envelope, _intent, _plan = seed_with_origin(tmp_path, monkeypatch)
    snapshot = host.owner.risk_snapshot_v1()["state"]
    context = host.owner.execution_plan_context_v1(rid, envelope)
    sequence = host.owner._store.sequence
    held = host.owner.active_sum_v1()
    calls = []

    class Transport:
        def post_trade_order(self, **kwargs):
            calls.append(kwargs)
            raise AssertionError("An unproven barrier must not reach transport")

    args = dict(
        envelope=envelope,
        permit=_permit(envelope),
        store_root=tmp_path / "send",
        transport=Transport(),
        handle=_handle(),
        portfolio_budget_owner=host.owner,
        portfolio_reservation_id=rid,
        execution_plan_context=context,
    )
    save = host.owner._store.save
    read = host.owner._store.read_revision_v1

    def bad_save(payload):
        if phase == "lost_ack":
            save(payload)
        raise DurableBudgetStoreError("SYNTHETIC_COMMIT_ACK_UNPROVEN")

    def bad_read(seq, checksum=None):
        if seq == sequence + 1:
            raise DurableBudgetStoreError("SYNTHETIC_COMMIT_READBACK_UNPROVEN")
        return read(seq, checksum)

    def bad_permit(**kwargs):
        raise consume.FullCoreExternalEffectDurableConsumeError("SYNTHETIC_SECOND_BARRIER_FAILED")

    def bad_owner_readback(*args):
        raise ValueError("SYNTHETIC_OWNER_READBACK_FAILED")

    try:
        with monkeypatch.context() as patch:
            if phase in {"before_commit", "lost_ack"}:
                patch.setattr(host.owner._store, "save", bad_save)
            elif phase == "readback":
                patch.setattr(host.owner._store, "read_revision_v1", bad_read)
            elif phase == "between_barriers":
                patch.setattr(seam, "persist_external_effect_durable_consume_v1", bad_permit)
            else:
                patch.setattr(
                    host.owner, "inspect_started_execution_attempt_v2", bad_owner_readback
                )
            with pytest.raises(
                ValueError
                if phase != "between_barriers"
                else seam.FullCoreEnvelopeBoundSendSeamError
            ):
                seam.attempt_envelope_bound_external_effect_send_v1(**args)
        assert not calls
        assert host.owner.active_sum_v1() == held > 0
        state = consume.load_external_effect_durable_consume_v1(store_root=args["store_root"])
        assert state["durable_consumed"] is (phase == "after_permit")
        actual_sequence = host.owner._store.sequence
        with pytest.raises(
            (ValueError, seam.FullCoreEnvelopeBoundSendSeamError),
            match="FENCED|CONSUMED_PERMIT|REPLAY_OR_UNBOUND",
        ):
            seam.attempt_envelope_bound_external_effect_send_v1(**args)
        assert host.owner._store.sequence == actual_sequence and not calls
    finally:
        host.close()
    restored = Owner(
        durable_root=context.root,
        durable_account_identity=snapshot["account_identity"],
        durable_mode="recover",
        durable_lane_bindings={
            lane: BoundInstrumentV1(**row["bound"])
            for lane, row in snapshot["lane_bindings"].items()
        },
    )
    try:
        link = restored.execution_links_v1()[rid]
        assert restored.active_sum_v1() == held
        assert restored.budget_state_v1().recovery_required
        if phase == "before_commit":
            assert link["phase"] == "PLAN_BOUND" and link["identity"] is None
        else:
            identity = parse_exchange_reconciliation_identity_v1(link["identity"])
            assert type(identity) is PortfolioExecutionReconciliationIdentityV2
            assert identity.budget_source_sequence == sequence
            assert identity.budget_submit_sequence == sequence + 1
    finally:
        restored.close()


def test_second_barrier_must_read_back_the_same_actual_attempt_before_transport(
    tmp_path, monkeypatch
):
    host, rid, _, envelope, _, _ = seed_with_origin(tmp_path, monkeypatch)
    permit = _permit(envelope)
    context = host.owner.execution_plan_context_v1(rid, envelope)
    persist = seam.persist_external_effect_durable_consume_v1

    def corrupt_after_commit(**kwargs):
        record = persist(**kwargs)
        other = replace(kwargs["execution_identity"], submit_attempt_id="f" * 32)
        record["execution_identity"] = other.to_dict()
        record["execution_identity_digest"] = other.identity_digest()
        consume.durable_consume_path_v1(kwargs["store_root"]).write_text(json.dumps(record))
        return record

    class Forbidden:
        def post_trade_order(self, **kwargs):
            raise AssertionError("Foreign attempt must not reach transport")

    monkeypatch.setattr(seam, "persist_external_effect_durable_consume_v1", corrupt_after_commit)
    try:
        with pytest.raises(
            seam.FullCoreEnvelopeBoundSendSeamError, match="PERMIT_READBACK_UNPROVEN"
        ):
            seam.attempt_envelope_bound_external_effect_send_v1(
                envelope=envelope,
                permit=permit,
                store_root=tmp_path / "send",
                transport=Forbidden(),
                handle=_handle(),
                portfolio_budget_owner=host.owner,
                portfolio_reservation_id=rid,
                execution_plan_context=context,
            )
        assert host.owner.active_sum_v1() > 0
        assert consume.load_external_effect_durable_consume_v1(store_root=tmp_path / "send")[
            "durable_consumed"
        ]
    finally:
        host.close()


def test_concurrent_budget_attempt_creation_has_one_original_winner(tmp_path, monkeypatch):
    host, rid, _, envelope, _, _ = seed_with_origin(tmp_path, monkeypatch)
    context = host.owner.execution_plan_context_v1(rid, envelope)
    permit, barrier = _permit(envelope), Barrier(2)
    sequence = host.owner._store.sequence

    def attempt():
        barrier.wait(timeout=10)
        try:
            return host.owner.begin_execution_submit_v2(rid, envelope, context, permit)
        except ValueError as exc:
            assert "REPLAY_OR_UNBOUND" in str(exc)
            return None

    try:
        with ThreadPoolExecutor(max_workers=2) as pool:
            futures = [pool.submit(attempt) for _ in range(2)]
            result = [f.result(timeout=15) for f in futures]
        winner = [r for r in result if r is not None]
        assert len(winner) == 1
        assert host.owner._store.sequence == sequence + 1
        assert host.owner.execution_links_v1()[rid]["identity"] == winner[0].to_dict()
    finally:
        host.close()


def test_concurrent_permit_consumers_cannot_overwrite_the_original_attempt(tmp_path, monkeypatch):
    host, rid, _, envelope, _, _ = seed_with_origin(tmp_path, monkeypatch)
    permit = _permit(envelope)
    context = host.owner.execution_plan_context_v1(rid, envelope)
    identity = host.owner.begin_execution_submit_v2(rid, envelope, context, permit)
    barrier = Barrier(2)

    def attempt():
        barrier.wait(timeout=10)
        try:
            return consume.persist_external_effect_durable_consume_v1(
                store_root=tmp_path / "send",
                permit=permit,
                envelope=envelope,
                durable_state="SENT_INITIATED",
                post_count=1,
                outcome="SYNTHETIC_UNCERTAINTY",
                execution_identity=identity,
            )
        except consume.FullCoreExternalEffectDurableConsumeError as exc:
            assert str(exc) in {"CONSUMED_PERMIT", "DURABLE_CONSUME_WRITER_BUSY"}
            return None

    try:
        with ThreadPoolExecutor(max_workers=2) as pool:
            futures = [pool.submit(attempt) for _ in range(2)]
            results = [f.result(timeout=15) for f in futures]
        assert sum(r is not None for r in results) == 1
        record = consume.load_external_effect_durable_consume_v1(store_root=tmp_path / "send")[
            "record"
        ]
        assert record["execution_identity"] == identity.to_dict()
    finally:
        host.close()


@pytest.mark.parametrize("fault", ["both", "foreign_account", "fenced_during_gets", "not_admitted"])
def test_original_plan_context_does_not_bypass_current_context_or_account_checks(
    tmp_path, monkeypatch, fault
):
    from tests.ops.test_prepost_original_budget_context_v1 import execute, AccountPort, caller

    host, rid, legacy, envelope, _, _ = seed_with_origin(tmp_path, monkeypatch)
    context = host.owner.execution_plan_context_v1(rid, envelope)
    args = dict(
        envelope=envelope,
        portfolio_budget_owner=host.owner,
        portfolio_reservation_id=rid,
        execution_plan_context=context,
    )
    sequence = host.owner._store.sequence
    if fault == "both":
        args["execution_identity"] = legacy
    if fault == "not_admitted":
        host.owner._admitted = False  # Negative fault only; never grant authority.
    port = AccountPort(
        args,
        uid="foreign" if fault == "foreign_account" else None,
        after_last=host.owner.restart_fail_closed_v1 if fault == "fenced_during_gets" else None,
    )
    try:
        with pytest.raises((caller.CurrentProductiveActualVenuePostError, ValueError)):
            execute(args, tmp_path, port=port)
        assert not consume.durable_consume_path_v1(tmp_path / "send").exists()
        assert host.owner.execution_links_v1()[rid]["identity"] is None
        if fault != "fenced_during_gets":
            assert host.owner._store.sequence == sequence
        assert host.owner.active_sum_v1() > 0
        assert len(port.requests) == (
            10 if fault in {"foreign_account", "fenced_during_gets"} else 0
        )
    finally:
        host.close()
