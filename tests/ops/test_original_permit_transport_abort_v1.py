"""Original transport closure to original budget; synthetic ports only."""

from dataclasses import replace
import json

import pytest

from tests.ops.test_n1_original_plan_origin_v1 import seed_with_origin
from tests.ops.test_n1_original_reservation_host_handoff_v1 import (
    synthetic_ports_and_isolation as synthetic_ports_and_isolation,
)
from tests.ops.test_current_post_original_safety_veto_v1 import active_source
from tests.ops.test_prepost_original_budget_context_v1 import (
    AccountPort,
    _clean_post_integrity,
    caller,
)
from tests.ops.test_current_productive_actual_venue_post_with_fresh_envelope_bound_single_use_permit_v1 import (
    _FakeKeychainBackend,
)
from tests.ops.test_portfolio_execution_recovery_v1 import ReadPort, _bound
from src.risk_layer.kill_switch.state import KillSwitchState
from src.ops.full_core_live_path_composition_root_v1.full_core_exchange_reconciliation_v1 import (
    parse_exchange_reconciliation_identity_v1,
)
from src.ops.full_core_live_path_composition_root_v1.external_effect_permit_durable_consume_v1 import (
    load_external_effect_durable_consume_v1,
)


class EmptyReadPort(ReadPort):
    def get(self, *, endpoint, **kwargs):
        result = super().get(endpoint=endpoint, **kwargs)
        return (
            result
            if endpoint.endswith("/config")
            else replace(result, payload={"code": "0", "data": []})
        )


def stopped_attempt(tmp_path, monkeypatch, phase):
    _, writer = active_source(tmp_path, monkeypatch)
    host, rid, _, envelope, _, _ = seed_with_origin(tmp_path, monkeypatch)
    args = dict(
        envelope=envelope,
        portfolio_budget_owner=host.owner,
        portfolio_reservation_id=rid,
        execution_plan_context=host.owner.execution_plan_context_v1(rid, envelope),
    )
    calls = []
    if phase == "boundary_write":
        from src.ops.full_core_live_path_composition_root_v1 import (
            external_effect_permit_durable_consume_v1 as store,
        )

        original_write = store._write_record_v1

        def fail_after_boundary(path, record):
            original_write(path, record)
            if record.get("transport_attempt", {}).get("phase") == "MAY_HAVE_SENT":
                raise OSError("Synthetic acknowledged-write failure")

        monkeypatch.setattr(store, "_write_record_v1", fail_after_boundary)

    class Backend(_FakeKeychainBackend):
        def copy_matching_generic_password_value_data_v1(self, **kwargs):
            if phase == "during_k1":
                writer.save(KillSwitchState.KILLED)
            return super().copy_matching_generic_password_value_data_v1(**kwargs)

    class Opener:
        def open(self, *_a, **_kw):
            calls.append("possible_socket")
            if phase == "forged_after_boundary":
                from src.ops.full_core_live_path_composition_root_v1.full_core_productive_http_post_transport_v1 import (
                    FullCoreCurrentPostSafetyVetoError,
                )

                raise FullCoreCurrentPostSafetyVetoError("POST_SAFETY_FORGED_AFTER_BOUNDARY")
            if phase == "after_boundary":
                raise TimeoutError("Synthetic socket uncertainty")
            raise AssertionError("Veto must precede socket")

    def factory():
        if phase == "opener_factory":
            writer.save(KillSwitchState.KILLED)
        return Opener()

    def command():
        return caller.execute_current_productive_actual_venue_post_with_fresh_envelope_bound_single_use_permit_v1(
            **args,
            owner_go=caller.OWNER_GO,
            baseline_origin_main_sha=caller.EXPECTED_BASELINE_ORIGIN_MAIN_SHA,
            store_root=tmp_path / "send",
            evidence_root=tmp_path / "evidence",
            perform_real_venue_post=True,
            k1_backend=Backend(),
            opener_factory=factory,
            read_only_get_transport=AccountPort(args),
            execution_integrity_backend=_clean_post_integrity(),
        )

    if phase in {"after_boundary", "boundary_write"}:
        result = command()
        assert result.post_outcome == "UNKNOWN_EXTERNAL_EFFECT_POSSIBLE"
    else:
        with pytest.raises(caller.CurrentProductiveActualVenuePostError, match="POST_SAFETY"):
            command()
    return host, rid, envelope, calls


@pytest.mark.parametrize("phase", ["during_k1", "opener_factory"])
def test_original_abort_is_durable_consumed_and_reaches_budget_with_fresh_empty_reads(
    tmp_path, monkeypatch, phase
):
    host, rid, envelope, calls = stopped_attempt(tmp_path, monkeypatch, phase)
    try:
        link = host.owner.execution_links_v1()[rid]
        record = load_external_effect_durable_consume_v1(store_root=tmp_path / "send")["record"]
        assert calls == []
        assert record["durable_state"] == "ABORTED_BEFORE_TRANSPORT"
        assert record["consumed"] is True
        assert record["retry_allowed"] is record["resubmit_allowed"] is False
        assert link["transport_store_root"] == str((tmp_path / "send").resolve())
        held = host.owner.active_sum_v1()
        assert held > 0
        identity = parse_exchange_reconciliation_identity_v1(link["identity"])
        host.reconciliation_transport = EmptyReadPort(identity)
        context = host.observe_v1({"LANE_1": _bound()})
        proof = context.execution_reconciliation[rid]
        assert proof["matched"] and proof["reservation_released"]
        assert proof["decision"]["order_state"] == "never_submitted"
        assert proof["local_submit_outcome"] == "NOT_SUBMITTED"
        assert host.owner.active_sum_v1() == 0
        assert host.owner.budget_state_v1().recovery_required
        assert host.owner.execution_links_v1()[rid]["envelope"] == envelope.to_runtime_json_v1()
    finally:
        host.close()


@pytest.mark.parametrize("phase", ["after_boundary", "forged_after_boundary"])
def test_possible_transport_never_becomes_abort_even_with_typed_veto_text(
    tmp_path, monkeypatch, phase
):
    host, rid, _, calls = stopped_attempt(tmp_path, monkeypatch, phase)
    try:
        assert calls == ["possible_socket"]
        record = load_external_effect_durable_consume_v1(store_root=tmp_path / "send")["record"]
        assert record["durable_state"] == "SENT_INITIATED"
        assert record["transport_attempt"]["phase"] == "MAY_HAVE_SENT"
        identity = parse_exchange_reconciliation_identity_v1(
            host.owner.execution_links_v1()[rid]["identity"]
        )
        held = host.owner.active_sum_v1()
        host.reconciliation_transport = EmptyReadPort(identity)
        context = host.observe_v1({"LANE_1": _bound()})
        proof = context.execution_reconciliation[rid]
        assert not proof["matched"] and not proof["reservation_released"]
        assert proof["local_submit_outcome"] == "TRANSPORT_UNKNOWN"
        assert proof["local_submit_evidence"] is None
        assert host.owner.active_sum_v1() == held > 0
    finally:
        host.close()


@pytest.mark.parametrize(
    "fault",
    [
        "missing",
        "malformed",
        "foreign_identity",
        "foreign_permit",
        "no_claim",
        "pre_socket",
        "venue_cancel",
        "stale",
        "pending",
        "position",
    ],
)
def test_negative_or_conflicting_sources_cannot_release_original_hold(tmp_path, monkeypatch, fault):
    from tests.ops.test_portfolio_execution_recovery_v1 import _fetch, ACCOUNT
    from src.ops.full_core_live_path_composition_root_v1 import (
        full_core_exchange_reconciliation_okx_read_only_provider_v1 as provider,
    )

    host, rid, _, _ = stopped_attempt(tmp_path, monkeypatch, "opener_factory")
    try:
        path = tmp_path / "send/full_core_external_effect_permit_consume_v1.json"
        record = json.loads(path.read_text())
        if fault == "missing":
            path.unlink()
        elif fault == "malformed":
            path.write_text("{")
        elif fault in {"foreign_identity", "foreign_permit", "no_claim", "pre_socket"}:
            if fault == "foreign_identity":
                record["execution_identity"]["submit_attempt_id"] = "0" * 32
            elif fault == "foreign_permit":
                record["permit_id"] = "foreign-permit"
            elif fault == "no_claim":
                del record["transport_attempt"]
            else:
                record["durable_state"] = "SENT_INITIATED"
                record["transport_attempt"]["phase"] = "PRE_SOCKET"
                del record["transport_attempt"]["aborted_at_utc"]
                del record["transport_attempt"]["reason_code"]
            path.write_text(json.dumps(record))
        identity = parse_exchange_reconciliation_identity_v1(
            host.owner.execution_links_v1()[rid]["identity"]
        )
        host.reconciliation_transport = (
            ReadPort(identity) if fault == "venue_cancel" else EmptyReadPort(identity)
        )
        if fault == "position":
            host.fetch = _fetch(
                uid=ACCOUNT,
                positions=({"instId": identity.native_id, "posSide": "net", "pos": "1"},),
            )
        if fault in {"stale", "pending"}:
            original = provider.fetch_okx_read_only_reconciliation_snapshot_v1

            def altered(**kwargs):
                snapshot = original(**kwargs)
                return replace(
                    snapshot,
                    **(
                        {"snapshot_freshness_proven": False}
                        if fault == "stale"
                        else {"pending_orders_observation": None}
                    ),
                )

            monkeypatch.setattr(provider, "fetch_okx_read_only_reconciliation_snapshot_v1", altered)
        held = host.owner.active_sum_v1()
        proof = host.observe_v1({"LANE_1": _bound()}).execution_reconciliation[rid]
        assert not proof["reservation_released"]
        assert not proof["matched"]
        assert host.owner.active_sum_v1() == held > 0
        if fault == "venue_cancel":
            assert "LOCAL_NEVER_SUBMITTED_VENUE_CONTRADICTION" in proof["reason_codes"]
    finally:
        host.close()


def test_cold_original_stores_keep_abort_and_release_only_through_original_reconciliation(
    tmp_path, monkeypatch
):
    from tests.ops.test_portfolio_execution_recovery_v1 import _host, _fetch, NOW, ACCOUNT

    host, rid, _, _ = stopped_attempt(tmp_path, monkeypatch, "opener_factory")
    link = host.owner.execution_links_v1()[rid]
    held = host.owner.active_sum_v1()
    from tests.ops.test_original_budget_send_permit_handoff_v1 import cold_owner

    restored = cold_owner(host)
    try:
        assert restored.active_sum_v1() == held > 0
        assert restored.execution_links_v1()[rid] == link
    finally:
        restored.close()
    host = _host(tmp_path, _fetch(uid=ACCOUNT), clock=lambda: NOW, expected_account=ACCOUNT)
    try:
        identity = parse_exchange_reconciliation_identity_v1(link["identity"])
        host.reconciliation_transport = EmptyReadPort(identity)
        proof = host.observe_v1({"LANE_1": _bound()}).execution_reconciliation[rid]
        assert proof["reservation_released"]
        sequence = host.owner._store.sequence
        old_reconciliation = host.owner.execution_links_v1()[rid]["reconciliation"]
        second = host.observe_v1({"LANE_1": _bound()})
        # Original host writes its recovery fence on every observation. It
        # must not reconcile/release the terminal reservation a second time.
        assert host.owner._store.sequence == sequence + 1
        assert second.execution_reconciliation == {}
        assert host.owner.execution_links_v1()[rid]["reconciliation"] == old_reconciliation
        assert host.owner.active_sum_v1() == 0
    finally:
        host.close()


def raw_claim(tmp_path, *, create_claim=True):
    from tests.ops.test_full_core_current_productive_envelope_bound_single_use_external_effect_send_seam_v1 import (
        _envelope,
        _permit,
    )
    from src.ops.full_core_live_path_composition_root_v1.external_effect_permit_durable_consume_v1 import (
        persist_external_effect_durable_consume_v1,
        claim_original_permit_transport_attempt_v1,
    )

    envelope = _envelope()
    permit = _permit(envelope)
    persist_external_effect_durable_consume_v1(
        store_root=tmp_path,
        permit=permit,
        envelope=envelope,
        durable_state="SENT_INITIATED",
        post_count=1,
        outcome="UNKNOWN",
    )
    args = dict(
        store_root=tmp_path,
        permit_id=permit.permit_id,
        envelope_id=envelope.envelope_id,
        envelope_digest=envelope.envelope_digest,
    )
    return (
        (claim_original_permit_transport_attempt_v1(**args) if create_claim else None),
        args,
        envelope,
    )


@pytest.mark.parametrize("terminal", ["abort", "socket", "crash_gap"])
def test_original_claim_cannot_be_reclaimed_or_reversed_by_a_second_caller(tmp_path, terminal):
    from src.ops.full_core_live_path_composition_root_v1.external_effect_permit_durable_consume_v1 import (
        claim_original_permit_transport_attempt_v1,
        FullCoreExternalEffectDurableConsumeError,
    )

    claim, args, _ = raw_claim(tmp_path)
    if terminal == "abort":
        claim.abort_before_transport_v1(reason_code="POST_SAFETY_SYNTHETIC")
    elif terminal == "socket":
        claim.mark_socket_boundary_v1()
    before = load_external_effect_durable_consume_v1(store_root=tmp_path)
    with pytest.raises(FullCoreExternalEffectDurableConsumeError):
        claim_original_permit_transport_attempt_v1(**args)
    if terminal != "crash_gap":
        with pytest.raises(FullCoreExternalEffectDurableConsumeError):
            claim.mark_socket_boundary_v1()
        with pytest.raises(FullCoreExternalEffectDurableConsumeError):
            claim.abort_before_transport_v1(reason_code="POST_SAFETY_SYNTHETIC")
    assert load_external_effect_durable_consume_v1(store_root=tmp_path) == before


@pytest.mark.parametrize("failure", ["file_sync", "directory_sync", "readback"])
def test_unproven_boundary_write_keeps_consumed_state_without_negative_terminal(
    tmp_path, monkeypatch, failure
):
    from src.ops.full_core_live_path_composition_root_v1 import (
        external_effect_permit_durable_consume_v1 as store,
    )

    claim, _, _ = raw_claim(tmp_path)
    if failure in {"file_sync", "directory_sync"}:
        original = store.os.fsync
        calls = []

        def sync(fd):
            calls.append(fd)
            if len(calls) == (1 if failure == "file_sync" else 2):
                raise OSError("Synthetic sync failure")
            return original(fd)

        monkeypatch.setattr(store.os, "fsync", sync)
    else:
        original = store.json.loads
        calls = []

        def read(*a, **kw):
            value = original(*a, **kw)
            calls.append(value)
            return {} if len(calls) == 2 else value

        monkeypatch.setattr(store.json, "loads", read)
    with pytest.raises((OSError, store.FullCoreExternalEffectDurableConsumeError)):
        claim.mark_socket_boundary_v1()
    record = json.loads((tmp_path / store.DURABLE_CONSUME_FILENAME).read_text())
    assert record["durable_state"] == "SENT_INITIATED"
    assert record["transport_attempt"]["phase"] == (
        "PRE_SOCKET" if failure == "file_sync" else "MAY_HAVE_SENT"
    )


def test_actual_http_does_not_open_after_unproven_boundary_write_despite_zero_counter(
    tmp_path, monkeypatch
):
    host, rid, _, calls = stopped_attempt(tmp_path, monkeypatch, "boundary_write")
    try:
        assert calls == []
        record = load_external_effect_durable_consume_v1(store_root=tmp_path / "send")["record"]
        assert record["transport_attempt"]["phase"] == "MAY_HAVE_SENT"
        identity = parse_exchange_reconciliation_identity_v1(
            host.owner.execution_links_v1()[rid]["identity"]
        )
        host.reconciliation_transport = EmptyReadPort(identity)
        held = host.owner.active_sum_v1()
        proof = host.observe_v1({"LANE_1": _bound()}).execution_reconciliation[rid]
        assert proof["local_submit_evidence"] is None
        assert not proof["reservation_released"]
        assert host.owner.active_sum_v1() == held > 0
    finally:
        host.close()


@pytest.mark.parametrize("entry", ["public", "private"])
def test_actual_http_requires_original_claim_in_addition_to_current_safety(
    tmp_path, monkeypatch, entry
):
    from tests.ops.test_full_core_current_productive_envelope_bound_single_use_external_effect_send_seam_v1 import (
        _envelope,
        _handle,
    )
    from src.ops.full_core_live_path_composition_root_v1.current_productive_post_safety_veto_v1 import (
        resolve_current_post_safety_context_v1,
    )
    from src.ops.full_core_live_path_composition_root_v1.envelope_bound_external_effect_send_seam_v1 import (
        _payload_from_envelope_v1,
    )
    from src.ops.full_core_live_path_composition_root_v1.full_core_productive_http_post_transport_v1 import (
        FullCoreProductiveHttpTradeOrderTransportV1,
        FullCoreProductiveHttpPostError,
    )

    active_source(tmp_path, monkeypatch)
    envelope = _envelope()
    http = FullCoreProductiveHttpTradeOrderTransportV1(
        handle=_handle(),
        signing_handle=object(),
        post_safety_context=resolve_current_post_safety_context_v1(envelope, stage="TEST"),
    )
    with pytest.raises(FullCoreProductiveHttpPostError, match="ORIGINAL_TRANSPORT_CLAIM_REQUIRED"):
        if entry == "private":
            http._perform_http_post_v1(payload=_payload_from_envelope_v1(envelope))
        else:
            http.post_trade_order(
                payload=_payload_from_envelope_v1(envelope),
                permit_id="unproven",
                envelope_id=envelope.envelope_id,
                envelope_digest=envelope.envelope_digest,
                one_shot_real_post=True,
            )
    assert http.post_count == 0


def test_simultaneous_original_transport_claim_has_exactly_one_winner(tmp_path):
    from concurrent.futures import ThreadPoolExecutor
    from src.ops.full_core_live_path_composition_root_v1 import (
        external_effect_permit_durable_consume_v1 as store,
    )

    _, args, _ = raw_claim(tmp_path, create_claim=False)

    def claim_once(_):
        try:
            return store.claim_original_permit_transport_attempt_v1(**args)
        except store.FullCoreExternalEffectDurableConsumeError:
            return None

    with ThreadPoolExecutor(max_workers=2) as pool:
        winners = [value for value in pool.map(claim_once, range(2)) if value is not None]
    assert len(winners) == 1
    assert (
        load_external_effect_durable_consume_v1(store_root=tmp_path)["record"]["transport_attempt"][
            "claim_id"
        ]
        == winners[0].claim_id
    )


def test_transport_root_cannot_be_changed_after_original_submit_commit(tmp_path, monkeypatch):
    host, rid, _, _ = stopped_attempt(tmp_path, monkeypatch, "opener_factory")
    try:
        host.owner._execution_links[rid]["transport_store_root"] = str(
            (tmp_path / "foreign").resolve()
        )
        link = host.owner.execution_links_v1()[rid]
        identity = parse_exchange_reconciliation_identity_v1(link["identity"])
        host.reconciliation_transport = EmptyReadPort(identity)
        held = host.owner.active_sum_v1()
        with pytest.raises(ValueError, match="ORIGINAL_EXECUTION_ATTEMPT_COMMIT_UNPROVEN"):
            host.observe_v1({"LANE_1": _bound()})
        assert host.owner.active_sum_v1() == held > 0
    finally:
        host.close()
