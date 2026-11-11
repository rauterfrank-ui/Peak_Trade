"""Original reconciliation, Safety state and transport veto on isolated fixtures."""

import json
import select
import subprocess
import time
from concurrent.futures import ThreadPoolExecutor
from dataclasses import asdict, replace
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path

import pytest

from src.ops import execution_incident_safety_v1 as incident
from src.ops.execution_ghosv_fill_quantity_v1 import (
    build_offline_execution_fill_quantity_incident_v1,
)
from src.ops.execution_incident_diagnostics_v1 import iter_offline_execution_incident_diagnostics_v1
from src.ops.execution_incident_host_v1 import (
    deliver_host_execution_incident_v1,
    observe_and_deliver_host_execution_incident_v1,
)
from src.ops.full_core_live_path_composition_root_v1.fresh_pretrade_runtime_get_v1 import (
    TRANSPORT_CLASS_INJECTED_TEST_DOUBLE,
)
from src.ops.full_core_live_path_composition_root_v1.full_core_exchange_reconciliation_offline_provider_v1 import (
    OfflineExchangeFixtureV1,
    build_offline_exchange_reconciliation_snapshot_v1,
)
from src.ops.full_core_live_path_composition_root_v1.full_core_exchange_reconciliation_v1 import (
    LocalSubmitOutcome,
    PortfolioExecutionReconciliationIdentityV2,
    REASON_FILL_EXCEEDS_ORDER,
    REASON_NEGATIVE_REMAINING,
    adjudicate_full_core_exchange_reconciliation_v1,
    parse_exchange_reconciliation_identity_v1,
)
from src.ops.full_core_live_path_composition_root_v1.full_core_post_response_to_ack_mapper_v1 import (
    join_full_core_post_result_to_lifecycle_v1,
)
from src.ops.full_core_live_path_composition_root_v1.full_core_post_submit_exchange_reconciliation_lifecycle_join_v1 import (
    FullCorePostSubmitLifecycleReconciliationJoinError,
    run_full_core_post_submit_lifecycle_reconciliation_join_v1,
)
from src.risk_layer.kill_switch.persistence import StatePersistence
from src.risk_layer.kill_switch.state import KillSwitchState
from src.ops.portfolio_capital_reservation_budget_v1.host_v1 import PortfolioBudgetHostV1
from tests.ops.test_current_productive_actual_venue_post_with_fresh_envelope_bound_single_use_permit_v1 import (
    _envelope,
)
from tests.ops.test_full_core_exchange_reconciliation_v1 import _binding, _identity
from tests.ops.test_full_core_current_productive_envelope_bound_single_use_external_effect_send_seam_v1 import (
    _permit,
)
from tests.ops.test_full_core_post_submit_exchange_reconciliation_lifecycle_join_v1 import (
    ORD,
    _ack_post_result,
    _join_kwargs,
    _order_row_join,
)
from tests.ops.test_n1_original_plan_origin_v1 import seed_with_origin
from tests.ops.test_n1_original_reservation_host_handoff_v1 import (
    synthetic_ports_and_isolation as synthetic_ports_and_isolation,
)
from tests.ops.test_prepost_original_budget_context_v1 import caller, execute
from tests.ops import test_portfolio_execution_recovery_v1 as recovery_fixture
from tests.ops.test_portfolio_budget_host_v1 import _fetch

NOW = datetime(2026, 11, 11, 12, tzinfo=timezone.utc)


@pytest.fixture
def scope(tmp_path, monkeypatch):
    root = tmp_path.resolve() / "execution-incident"
    root.mkdir()
    scope = incident.OfflineExecutionIncidentScopeV1(
        root, _identity().account_identity, "synthetic-execution", NOW - timedelta(seconds=10)
    )
    monkeypatch.setenv("PEAK_KILL_SWITCH_STATE_PATH", str(scope.state_path))
    monkeypatch.delenv("PEAKTRADE_KILL_SWITCH_STATE_PATH", raising=False)
    monkeypatch.delenv("PEAK_KILL_SWITCH", raising=False)
    StatePersistence(str(scope.state_path)).save(KillSwitchState.ACTIVE)
    return scope


def snapshot(identity, *, fill_total=None, **fixture_fields):
    order_size = identity.final_quantity
    overfill = str(Decimal(order_size) + 1)
    return build_offline_exchange_reconciliation_snapshot_v1(
        identity=identity,
        fixture=OfflineExchangeFixtureV1(
            order_history={
                "data": [
                    {
                        "instId": identity.native_id,
                        "clOrdId": identity.clordid,
                        "ordId": "original-order",
                        "state": "partially_filled",
                        "sz": order_size,
                        "accFillSz": order_size,
                    }
                ]
            },
            fills={
                "data": [
                    {
                        "instId": identity.native_id,
                        "clOrdId": identity.clordid,
                        "ordId": "original-order",
                        "fillId": "original-fill",
                        "fillSz": fill_total if fill_total is not None else overfill,
                    }
                ]
            },
            **fixture_fields,
        ),
    )


def delivery_args(scope, identity=None, **overrides):
    identity = _identity() if identity is None else identity
    return (
        dict(
            scope=scope,
            session_id=scope.session_id,
            identity=identity,
            snapshot=snapshot(identity),
            local_submit_outcome=LocalSubmitOutcome.TRANSPORT_ACK,
            observed_at=NOW,
            evaluated_at=NOW,
        )
        | overrides
    )


def source_incident(args):
    return build_offline_execution_fill_quantity_incident_v1(
        session_id=args["session_id"],
        observed_at=args["observed_at"],
        identity=args["identity"],
        snapshot=args["snapshot"],
        decision=adjudicate_full_core_exchange_reconciliation_v1(
            identity=args["identity"],
            snapshot=args["snapshot"],
            local_submit_outcome=args["local_submit_outcome"],
        ),
        local_submit_outcome=args["local_submit_outcome"],
    )


def receive(scope, identity=None, **overrides):
    args = delivery_args(scope, identity, **overrides)
    return incident.accept_offline_execution_incident_v1(
        **args, source_incident=source_incident(args)
    )


def test_reconciliation_incident_reaches_original_before_socket_veto_and_cold_read(
    tmp_path, monkeypatch, scope
):
    host, rid, identity, envelope, _, _ = seed_with_origin(tmp_path, monkeypatch)
    scope = replace(scope, account=identity.account_identity)
    original_execute = caller.execute_current_productive_actual_venue_post_with_fresh_envelope_bound_single_use_permit_v1
    calls = []
    receipts = []
    incident_identities = []

    class Opener:
        def open(self, *args, **kwargs):
            calls.append("transport")
            raise AssertionError("the actual pre-socket veto must refuse this attempt")

    def factory():
        calls.append("factory")
        payload = host.owner.execution_links_v1()[rid]["identity"]
        consumed_identity = parse_exchange_reconciliation_identity_v1(payload)
        assert type(consumed_identity) is PortfolioExecutionReconciliationIdentityV2
        offline_identity = replace(consumed_identity, execution_environment="SHADOW")
        incident_identities.append(offline_identity)
        receipts.append(receive(scope, offline_identity))
        return Opener()

    def with_incident(*args, **kwargs):
        kwargs["opener_factory"] = factory
        return original_execute(*args, **kwargs)

    monkeypatch.setattr(
        caller,
        "execute_current_productive_actual_venue_post_with_fresh_envelope_bound_single_use_permit_v1",
        with_incident,
    )
    held_before = host.owner.active_sum_v1()
    try:
        initial = incident.observe_offline_execution_incident_v1(scope=scope, envelope=envelope)
        assert initial["state_name"] == "ACTIVE"
        assert initial["post_safety_veto"] is None
        with pytest.raises(
            caller.CurrentProductiveActualVenuePostError,
            match="POST_SAFETY_DURABLE_VETO:BEFORE_SOCKET:TRUSTED_PRESENT:KILLED",
        ):
            execute(
                {
                    "envelope": envelope,
                    "portfolio_budget_owner": host.owner,
                    "portfolio_reservation_id": rid,
                    "execution_plan_context": host.owner.execution_plan_context_v1(rid, envelope),
                },
                tmp_path,
            )
        assert calls == ["factory"]
        assert host.owner.active_sum_v1() == held_before > 0
        assert host.owner.execution_links_v1()[rid]["identity"] is not None
    finally:
        host.close()

    (receipt,) = receipts
    assert receipt["disposition"] == "KILL_PERSISTED"
    assert receipt["reconciliation_reason"] == REASON_FILL_EXCEEDS_ORDER
    cold_scope = replace(scope)
    state_before = scope.state_path.read_bytes()
    journal_before = scope.journal_path.read_bytes()
    observed = incident.observe_offline_execution_incident_v1(
        scope=cold_scope, envelope=envelope, incident_id=receipt["incident_id"]
    )
    assert observed["state_name"] == "KILLED"
    assert observed["kill_revision"] == receipt["kill_revision"]
    assert observed["correlated_incident_veto"] is True
    assert scope.state_path.read_bytes() == state_before
    assert scope.journal_path.read_bytes() == journal_before
    subprocess_observation = """
import json
import sys
from datetime import datetime
from pathlib import Path
from src.ops.execution_incident_safety_v1 import (
    OfflineExecutionIncidentScopeV1, observe_offline_execution_incident_v1,
)
from src.ops.full_core_live_path_composition_root_v1.final_order_envelope_v1 import (
    FinalOrderEnvelopeV1,
)
args = json.loads(sys.argv[1])
scope = OfflineExecutionIncidentScopeV1(
    Path(args["root"]), args["account"], args["session_id"],
    datetime.fromisoformat(args["started_at"]),
)
print(json.dumps(observe_offline_execution_incident_v1(
    scope=scope, envelope=FinalOrderEnvelopeV1(**args["envelope"]),
    incident_id=args["incident_id"],
)))
"""
    launcher = Path(incident.__file__).resolve().parents[2] / "scripts/pt"
    reopened = subprocess.run(
        [
            str(launcher),
            "-c",
            subprocess_observation,
            json.dumps(
                {
                    **scope.binding(),
                    "envelope": asdict(envelope),
                    "incident_id": receipt["incident_id"],
                }
            ),
        ],
        check=True,
        capture_output=True,
        text=True,
        timeout=15,
    )
    assert json.loads(reopened.stdout.splitlines()[-1]) == observed
    assert scope.state_path.read_bytes() == state_before
    assert scope.journal_path.read_bytes() == journal_before

    # An unrelated later state is independently reported and never attributed
    # to the historical incident. Only the original test owner changes the file.
    StatePersistence(str(scope.state_path)).save(KillSwitchState.ACTIVE)
    observed = incident.observe_offline_execution_incident_v1(
        scope=cold_scope, envelope=envelope, incident_id=receipt["incident_id"]
    )
    assert observed["post_safety_veto"] is None
    assert observed["correlated_incident_veto"] is False
    assert receive(cold_scope, incident_identities[0]) == receipt
    assert StatePersistence(str(scope.state_path)).load()["state"] == "ACTIVE"


@pytest.mark.parametrize(
    "fixture_fields",
    [
        {"fill_total": "10"},
        {"snapshot_freshness_proven": False},
        {"item_freshness_proven": False},
        {"incomplete_pagination": True},
        {"response_status": "500"},
        {"transport_failures": ("TIMEOUT",)},
    ],
)
def test_only_confirmed_original_critical_evidence_can_mutate_state(scope, fixture_fields):
    before = scope.state_path.read_bytes()
    assert receive(scope, snapshot=snapshot(_identity(), **fixture_fields)) is None
    assert scope.state_path.read_bytes() == before
    assert not scope.journal_path.exists()


@pytest.mark.parametrize(
    "fault",
    [
        "different_venue_order",
        "missing_venue_order",
        "missing_native_id",
        "missing_fill_id",
        "fill_only",
    ],
)
def test_quantity_reason_without_exact_order_and_fill_evidence_does_not_escalate(scope, fault):
    identity = replace(_identity(), exchange_ord_id=None)
    evidence = snapshot(identity)
    order, fill = evidence.evidence_items
    payload = dict(fill.payload)
    if fault == "different_venue_order":
        payload["ordId"] = "foreign-venue-order"
    elif fault == "missing_venue_order":
        payload.pop("ordId")
    elif fault == "missing_native_id":
        payload.pop("instId")
    elif fault == "missing_fill_id":
        payload.pop("fillId")
    fill = replace(fill, payload=payload)
    evidence = replace(evidence, evidence_items=(fill,) if fault == "fill_only" else (order, fill))
    decision = adjudicate_full_core_exchange_reconciliation_v1(
        identity=identity, snapshot=evidence, local_submit_outcome=LocalSubmitOutcome.TRANSPORT_ACK
    )
    assert decision.reasons == (
        (REASON_NEGATIVE_REMAINING,) if fault == "fill_only" else (REASON_FILL_EXCEEDS_ORDER,)
    )
    before = scope.state_path.read_bytes()
    assert receive(scope, identity, snapshot=evidence) is None
    assert scope.state_path.read_bytes() == before
    assert not scope.journal_path.exists()


def test_order_report_with_negative_remaining_is_independently_accepted(scope):
    identity = _identity()
    evidence = snapshot(identity)
    order, _ = evidence.evidence_items
    order = replace(
        order, payload={**order.payload, "accFillSz": str(Decimal(identity.final_quantity) + 1)}
    )
    receipt = receive(scope, identity, snapshot=replace(evidence, evidence_items=(order,)))
    assert receipt["reconciliation_reason"] == REASON_NEGATIVE_REMAINING
    assert receipt["source_check_id"] == "FILL_QUANTITY_INTEGRITY"
    assert receipt["source_outcome"] == "FAIL"
    assert receipt["source_traffic"] == "RED"
    assert receipt["venue_order_id"] == order.payload["ordId"]
    assert len(receipt["evidence_refs"]) == 1
    assert StatePersistence(str(scope.state_path)).load()["state"] == "KILLED"


@pytest.mark.parametrize(
    "fault",
    [
        "missing",
        "substituted_session",
        "substituted_venue_order",
        "substituted_evidence",
        "substituted_snapshot",
        "substituted_submit_outcome",
        "green",
    ],
)
def test_safety_rejects_missing_or_forged_producer_incident(scope, fault):
    args = delivery_args(scope)
    original = source_incident(args)
    if fault == "missing":
        claim = None
    elif fault == "substituted_session":
        claim = replace(original, session_id="foreign-session")
    elif fault == "substituted_venue_order":
        claim = replace(original, venue_order_id="foreign-venue-order")
    elif fault == "substituted_evidence":
        claim = replace(original, evidence_refs=("0" * 64,))
    elif fault == "substituted_snapshot":
        claim = original
        args["snapshot"] = replace(args["snapshot"], pending_orders_observation={"data": []})
    elif fault == "substituted_submit_outcome":
        claim = original
        args["local_submit_outcome"] = LocalSubmitOutcome.TRANSPORT_UNKNOWN
    else:
        claim = original
        args["snapshot"] = snapshot(args["identity"], fill_total=args["identity"].final_quantity)
    before = scope.state_path.read_bytes()
    with pytest.raises(
        incident.ExecutionIncidentSafetyError, match="INCIDENT_SOURCE_EVIDENCE_MISMATCH"
    ):
        incident.accept_offline_execution_incident_v1(**args, source_incident=claim)
    assert scope.state_path.read_bytes() == before
    assert not scope.journal_path.exists()


@pytest.mark.parametrize(
    "fault", ["session", "account", "environment", "future", "pre_session", "incomplete_identity"]
)
def test_foreign_or_temporally_unbound_input_is_rejected(scope, fault):
    kwargs = {
        "session": {"session_id": "other-session"},
        "account": {"identity": replace(_identity(), account_identity="other-account")},
        "environment": {"identity": replace(_identity(), execution_environment="LIVE")},
        "incomplete_identity": {"identity": replace(_identity(), envelope_digest="")},
        "future": {"observed_at": NOW + timedelta(seconds=1)},
        "pre_session": {"observed_at": scope.started_at - timedelta(seconds=1)},
    }[fault]
    before = scope.state_path.read_bytes()
    with pytest.raises(incident.ExecutionIncidentSafetyError, match="INCIDENT_"):
        receive(scope, **kwargs)
    assert scope.state_path.read_bytes() == before
    assert not scope.journal_path.exists()


def test_filegate_path_and_state_remain_original(scope, monkeypatch):
    foreign = scope.root / "foreign.json"
    monkeypatch.setenv("PEAK_KILL_SWITCH_STATE_PATH", str(foreign))
    with pytest.raises(incident.ExecutionIncidentSafetyError, match="SCOPE_MISMATCH"):
        receive(scope)
    assert not foreign.exists()
    monkeypatch.setenv("PEAK_KILL_SWITCH_STATE_PATH", str(scope.state_path))
    scope.state_path.write_bytes(b"{")
    with pytest.raises(incident.ExecutionIncidentSafetyError, match="FILEGATE_UNPROVEN"):
        receive(scope)
    assert scope.state_path.read_bytes() == b"{"
    scope.state_path.unlink()
    with pytest.raises(incident.ExecutionIncidentSafetyError, match="FILEGATE_UNPROVEN"):
        receive(scope)
    assert not scope.state_path.exists()
    assert not scope.journal_path.exists()


def test_concurrent_duplicates_and_stale_delivery_do_not_rewrite_state(scope):
    with ThreadPoolExecutor(max_workers=2) as pool:
        receipts = list(pool.map(lambda _: receive(scope), range(2)))
    assert receipts[0] == receipts[1]
    before = scope.state_path.read_bytes()
    journal_before = scope.journal_path.read_bytes()
    with pytest.raises(incident.ExecutionIncidentSafetyError, match="STALE_OR_AMBIGUOUS"):
        receive(
            scope,
            replace(_identity(), submit_attempt_id="older"),
            observed_at=NOW - timedelta(seconds=1),
        )
    assert scope.state_path.read_bytes() == before
    assert scope.journal_path.read_bytes() == journal_before
    newer = receive(
        scope,
        replace(_identity(), submit_attempt_id="newer"),
        observed_at=NOW + timedelta(seconds=1),
        evaluated_at=NOW + timedelta(seconds=1),
    )
    assert newer["disposition"] == "ALREADY_BLOCKED"
    assert scope.state_path.read_bytes() == before


def test_retry_after_kill_before_receipt_does_not_create_a_second_kill(scope, monkeypatch):
    def fail_write(**kwargs):
        raise OSError("injected journal write failure")

    with monkeypatch.context() as patch:
        patch.setattr(incident, "atomic_write_json", fail_write)
        with pytest.raises(OSError, match="injected journal"):
            receive(scope)
    before = scope.state_path.read_bytes()
    assert not scope.journal_path.exists()
    assert receive(replace(scope))["disposition"] == "KILL_PERSISTED"
    assert scope.state_path.read_bytes() == before


def test_new_incident_reasserts_kill_during_existing_recovery(scope):
    StatePersistence(str(scope.state_path)).save(KillSwitchState.RECOVERING)
    receipt = receive(scope)
    assert receipt["disposition"] == "KILL_PERSISTED"
    assert StatePersistence(str(scope.state_path)).load()["state"] == "KILLED"


@pytest.fixture
def post_submit_inputs(scope):
    envelope = _envelope()
    binding = replace(
        _binding(),
        session_id=scope.session_id,
        account_scope=scope.account,
        instrument_id=envelope.instrument_id,
        native_id=envelope.instrument_id,
        envelope_digest=envelope.envelope_digest,
        clordid=envelope.client_order_id,
        final_quantity=envelope.quantity,
        order_type=envelope.order_type,
        order_price=envelope.price,
    )
    ack = _ack_post_result()
    ack = replace(
        ack,
        payload={**ack.payload, "data": [{**ack.payload["data"][0], "clOrdId": binding.clordid}]},
    )
    post = join_full_core_post_result_to_lifecycle_v1(
        result=ack, sent_clordid=binding.clordid, submit_count=1
    )
    order_row = _order_row_join(
        state="partially_filled", sz=envelope.quantity, acc=envelope.quantity
    )
    row_identity = dict(clOrdId=binding.clordid, instId=binding.native_id, ordId=ORD)
    fixture = OfflineExchangeFixtureV1(
        order_history={"data": [{**order_row, **row_identity}]},
        fills={
            "data": [
                dict(**row_identity, fillId="fill", fillSz=str(Decimal(envelope.quantity) + 1))
            ]
        },
    )
    kwargs = {
        **_join_kwargs(),
        "envelope_identity": envelope.envelope_id,
        "binding": binding,
        "post_submit_join": post,
        "offline_fixture": fixture,
    }
    return envelope, kwargs


def test_post_submit_default_is_unchanged_and_offline_opt_in_delivers_original_decision(
    scope, post_submit_inputs
):
    envelope, kwargs = post_submit_inputs
    baseline = run_full_core_post_submit_lifecycle_reconciliation_join_v1(**kwargs)
    assert baseline.reconciliation.decision.reasons == (REASON_FILL_EXCEEDS_ORDER,)
    assert "execution_incident_receipt" not in baseline.to_dict()
    assert not scope.journal_path.exists()
    assert StatePersistence(str(scope.state_path)).load()["state"] == "ACTIVE"

    delivery = incident.OfflineExecutionIncidentDeliveryV1(scope, NOW, NOW)
    connected = run_full_core_post_submit_lifecycle_reconciliation_join_v1(
        **kwargs, incident_delivery=delivery
    )
    payload = connected.to_dict()
    receipt = payload.pop("execution_incident_receipt")
    assert payload == baseline.to_dict()
    assert connected.reconciliation.snapshot == baseline.reconciliation.snapshot
    assert connected.reconciliation.decision == baseline.reconciliation.decision
    assert connected.reconciliation.ghv_bundle == baseline.reconciliation.ghv_bundle
    assert receipt["reconciliation_reason"] == REASON_FILL_EXCEEDS_ORDER
    assert receipt["source_check_id"] == "FILL_QUANTITY_INTEGRITY"
    assert receipt["source_traffic"] == "RED"
    assert receipt["source_outcome"] == "FAIL"
    assert receipt["venue_order_id"] == ORD
    assert len(receipt["evidence_refs"]) == 2
    assert receipt["envelope_digest"] == envelope.envelope_digest
    assert receipt["disposition"] == "KILL_PERSISTED"
    diagnostic = incident.observe_offline_execution_incident_v1(scope=scope, envelope=envelope)
    assert diagnostic["incident_id"] == receipt["incident_id"]
    assert diagnostic["correlated_incident_veto"] is True


@pytest.mark.parametrize("fault", ["write", "get", "wrong_session", "wrong_mode", "close_feedback"])
def test_incident_join_rejects_foreign_scope_or_other_authority(scope, post_submit_inputs, fault):
    _, kwargs = post_submit_inputs
    before = scope.state_path.read_bytes()
    if fault == "write":
        kwargs.update(apply_durable_state=True, state_dir=scope.root / "original-store")
    elif fault == "get":
        kwargs.update(
            offline_fixture=None, read_only_get_transport=object(), pretrade_decision_id="fixture"
        )
    elif fault == "wrong_session":
        kwargs["binding"] = replace(kwargs["binding"], session_id="other-session")
    elif fault == "wrong_mode":
        kwargs["binding"] = replace(kwargs["binding"], execution_mode="LIVE")
    else:
        kwargs["post_close_feedback_request"] = object()

    with pytest.raises(
        (incident.ExecutionIncidentSafetyError, FullCorePostSubmitLifecycleReconciliationJoinError),
        match="INCIDENT_",
    ):
        run_full_core_post_submit_lifecycle_reconciliation_join_v1(
            **kwargs, incident_delivery=incident.OfflineExecutionIncidentDeliveryV1(scope, NOW, NOW)
        )
    assert scope.state_path.read_bytes() == before
    assert not scope.journal_path.exists()
    assert not (scope.root / "original-store").exists()


def test_diagnostic_keeps_observing_after_missing_state_or_damaged_receipt(
    scope, post_submit_inputs
):
    envelope, kwargs = post_submit_inputs
    result = run_full_core_post_submit_lifecycle_reconciliation_join_v1(
        **kwargs, incident_delivery=incident.OfflineExecutionIncidentDeliveryV1(scope, NOW, NOW)
    )
    receipt = result.reconciliation.execution_incident_receipt
    state_bytes = scope.state_path.read_bytes()
    journal_bytes = scope.journal_path.read_bytes()
    diagnostics = iter_offline_execution_incident_diagnostics_v1(
        scope=scope, envelope=envelope, interval_seconds=0.001, samples=4
    )
    assert next(diagnostics)["correlated_incident_veto"] is True
    scope.journal_path.write_bytes(b"{")
    damaged = next(diagnostics)
    assert damaged["incident_id"] == receipt["incident_id"]
    assert damaged["incident_evidence_error"] == "INCIDENT_JOURNAL_UNPROVEN"
    assert damaged["post_safety_veto"].endswith(":TRUSTED_PRESENT:KILLED")
    assert damaged["correlated_incident_veto"] is False
    assert scope.journal_path.read_bytes() == b"{"
    scope.state_path.unlink()
    missing = next(diagnostics)
    assert missing["evidence_status"] == "MISSING"
    assert "POST_SAFETY_DURABLE_VETO" in missing["post_safety_veto"]
    assert not scope.state_path.exists()
    scope.state_path.write_bytes(state_bytes)
    scope.journal_path.write_bytes(journal_bytes)
    recovered_read = next(diagnostics)
    assert recovered_read["correlated_incident_veto"] is True
    assert recovered_read["kill_revision"] == receipt["kill_revision"]
    assert scope.state_path.read_bytes() == state_bytes
    assert scope.journal_path.read_bytes() == journal_bytes


def test_diagnostic_recovers_from_transient_read_error(scope, post_submit_inputs, monkeypatch):
    envelope, kwargs = post_submit_inputs
    run_full_core_post_submit_lifecycle_reconciliation_join_v1(
        **kwargs, incident_delivery=incident.OfflineExecutionIncidentDeliveryV1(scope, NOW, NOW)
    )
    diagnostics = iter_offline_execution_incident_diagnostics_v1(
        scope=scope, envelope=envelope, interval_seconds=0.001, samples=2
    )

    def unreadable(*args, **kwargs):
        raise PermissionError("injected FILEGATE read error")

    with monkeypatch.context() as patch:
        patch.setattr(incident, "_state_observation", unreadable)
        assert next(diagnostics) == {
            "observation_status": "UNAVAILABLE",
            "observation_error": "INCIDENT_FILEGATE_READ_FAILED",
            "correlated_incident_veto": False,
        }
    assert next(diagnostics)["correlated_incident_veto"] is True


def diagnostic_command(scope, envelope):
    envelope_path = scope.root / "bound-envelope.json"
    envelope_path.write_text(json.dumps(envelope.to_runtime_json_v1()))
    launcher = Path(incident.__file__).resolve().parents[2] / "scripts/pt"
    return [
        str(launcher),
        "-m",
        "src.ops.execution_incident_diagnostics_v1",
        "--root",
        str(scope.root),
        "--account",
        scope.account,
        "--session-id",
        scope.session_id,
        "--started-at",
        scope.started_at.isoformat(),
        "--envelope",
        str(envelope_path),
    ]


def test_diagnostic_process_restarts_without_incident_id(scope, post_submit_inputs):
    envelope, kwargs = post_submit_inputs
    result = run_full_core_post_submit_lifecycle_reconciliation_join_v1(
        **kwargs, incident_delivery=incident.OfflineExecutionIncidentDeliveryV1(scope, NOW, NOW)
    )
    receipt = result.reconciliation.execution_incident_receipt
    state_bytes = scope.state_path.read_bytes()
    journal_bytes = scope.journal_path.read_bytes()
    command = diagnostic_command(scope, envelope)
    with subprocess.Popen(
        [*command, "--interval-seconds", "5", "--samples", "100"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        bufsize=0,
    ) as first:
        try:
            deadline = time.monotonic() + 15
            while time.monotonic() < deadline:
                ready, _, _ = select.select(
                    [first.stdout], [], [], max(0, deadline - time.monotonic())
                )
                if not ready:
                    pytest.fail("diagnostic did not emit a sample")
                line = first.stdout.readline()
                if line.startswith(b"{"):
                    first_sample = json.loads(line)
                    break
                if not line:
                    pytest.fail(f"diagnostic exited: {first.stderr.read().decode()}")
            else:
                pytest.fail("diagnostic did not emit a JSON observation")
            assert first.poll() is None
        finally:
            first.terminate()
            first.communicate(timeout=15)

    second = subprocess.run(
        [*command, "--interval-seconds", "0.001", "--samples", "2"],
        check=True,
        capture_output=True,
        text=True,
        timeout=15,
    )
    samples = [json.loads(line) for line in second.stdout.splitlines() if line.startswith("{")]
    assert first_sample["incident_id"] == receipt["incident_id"]
    assert first_sample["correlated_incident_veto"] is True
    assert samples == [first_sample, first_sample]
    assert scope.state_path.read_bytes() == state_bytes
    assert scope.journal_path.read_bytes() == journal_bytes


class ShadowReadPort(recovery_fixture.ReadPort):
    transport_class = TRANSPORT_CLASS_INJECTED_TEST_DOUBLE

    def get(self, *, endpoint, **kwargs):
        result = super().get(endpoint=endpoint, **kwargs)
        return replace(
            result,
            transport_class=self.transport_class,
            venue_live_contact=self.fault == "live-result",
        )


@pytest.fixture
def shadow_host(scope, monkeypatch):
    plan = recovery_fixture.try_bind_current_productive_venue_plan_v1

    def shadow_plan(**kwargs):
        return plan(**{**kwargs, "execution_mode": "SHADOW"})

    monkeypatch.setattr(recovery_fixture, "try_bind_current_productive_venue_plan_v1", shadow_plan)
    seeded, rid, _, envelope, _, plan = seed_with_origin(scope.root, monkeypatch)
    try:
        identity = seeded.owner.begin_execution_submit_v2(
            rid, envelope, seeded.owner.execution_plan_context_v1(rid, envelope), _permit(envelope)
        )
        assert plan.environment == identity.execution_environment == "SHADOW"
        held = seeded.owner.active_sum_v1()
        root = seeded.root
    finally:
        seeded.close()
    scope = replace(scope, account=identity.account_identity)
    read_port = ShadowReadPort(
        identity,
        state="partially_filled",
        filled=str(Decimal(identity.final_quantity) + 1),
    )
    host = PortfolioBudgetHostV1(
        root=root,
        private_rest_fetch=_fetch(uid=identity.account_identity),
        repository_sha="test-host-revision",
        session_id=scope.session_id,
        expected_account_identity=scope.account,
        clock=NOW.timestamp,
        reconciliation_transport=read_port,
        execution_environment="SHADOW",
    )
    try:
        yield host, scope, identity, envelope, held
    finally:
        host.close()


def test_original_shadow_host_get_to_persisted_budget_to_filegate(shadow_host):
    host, scope, identity, envelope, held = shadow_host
    rid = identity.portfolio_reservation_id
    bindings = {"LANE_1": recovery_fixture._bound()}

    default = host.observe_v1(bindings)
    assert StatePersistence(str(scope.state_path)).load()["state"] == "ACTIVE"
    assert not scope.journal_path.exists()
    calls = host.reconciliation_transport.calls[:]
    assert len(calls) == 6

    context, evidence = host.observe_execution_reconciliation_evidence_v1(bindings)
    assert context.execution_reconciliation == default.execution_reconciliation
    assert host.reconciliation_transport.calls == calls * 2
    assert evidence[rid].identity == identity
    assert evidence[rid].snapshot.simulation_mode == "OKX_TRANSPORT_INJECTED"
    original_link = host.owner.execution_links_v1()[rid]
    original_budget = (host.root / "owner" / "reservations.sqlite3").read_bytes()
    receipt = deliver_host_execution_incident_v1(
        scope=scope, context=context, evidence=evidence[rid]
    )
    assert receipt["reconciliation_reason"] == REASON_NEGATIVE_REMAINING
    assert receipt["disposition"] == "KILL_PERSISTED"
    assert (
        receipt["reconciliation_source"]["budget_snapshot_digest"]
        == (original_link["reconciliation"]["snapshot_digest"])
    )
    assert receipt["reconciliation_source"]["budget_revision"] == evidence[rid].revision_ref[0]
    assert (
        receipt["reconciliation_source"]["budget_revision_digest"] == evidence[rid].revision_ref[1]
    )
    assert host.owner.execution_links_v1()[rid] == original_link
    assert host.owner.active_sum_v1() == held > 0
    assert host.owner.budget_state_v1().recovery_required
    assert (host.root / "owner" / "reservations.sqlite3").read_bytes() == original_budget
    assert host.reconciliation_transport.calls == calls * 2
    state_bytes = scope.state_path.read_bytes()
    journal_bytes = scope.journal_path.read_bytes()
    assert (
        deliver_host_execution_incident_v1(scope=scope, context=context, evidence=evidence[rid])
        == receipt
    )
    assert scope.state_path.read_bytes() == state_bytes
    assert scope.journal_path.read_bytes() == journal_bytes

    host.close()
    readback = subprocess.run(
        [*diagnostic_command(scope, envelope), "--interval-seconds", "0.001", "--samples", "1"],
        check=True,
        capture_output=True,
        text=True,
        timeout=15,
    )
    observed = json.loads(readback.stdout.splitlines()[-1])
    assert observed["correlated_incident_veto"] is True
    assert observed["incident_id"] == receipt["incident_id"]
    assert observed["kill_revision"] == receipt["kill_revision"]
    assert scope.state_path.read_bytes() == state_bytes
    assert scope.journal_path.read_bytes() == journal_bytes


def test_explicit_shadow_host_cycle_delivers_without_a_separate_action(shadow_host):
    host, scope, identity, envelope, held = shadow_host
    bindings = {"LANE_1": recovery_fixture._bound()}
    rid = identity.portfolio_reservation_id
    context, receipt = observe_and_deliver_host_execution_incident_v1(
        host=host, bindings=bindings, scope=scope, reservation_id=rid
    )
    assert not context.execution_reconciliation[rid]["matched"]
    assert host.owner.active_sum_v1() == held
    assert len(host.reconciliation_transport.calls) == 6
    observed = incident.observe_offline_execution_incident_v1(scope=scope, envelope=envelope)
    assert observed["incident_id"] == receipt["incident_id"]
    assert observed["correlated_incident_veto"] is True


@pytest.mark.parametrize(
    "fault", ["account", "cached", "live-result", "live-port", "live-host", "wrong-endpoint"]
)
def test_shadow_host_requires_original_account_and_injected_get(shadow_host, fault):
    host, scope, identity, _, held = shadow_host
    host.reconciliation_transport.fault = fault
    bindings = {"LANE_1": recovery_fixture._bound()}
    before = scope.state_path.read_bytes()
    if fault == "live-host":
        host.execution_environment = "LIVE"
    elif fault == "live-port":
        host.reconciliation_transport.transport_class = "LIVE"
    if fault == "wrong-endpoint":
        context, evidence = host.observe_execution_reconciliation_evidence_v1(bindings)
        assert not context.execution_reconciliation[identity.portfolio_reservation_id]["matched"]
        assert (
            deliver_host_execution_incident_v1(
                scope=scope, context=context, evidence=evidence[identity.portfolio_reservation_id]
            )
            is None
        )
    else:
        with pytest.raises(ValueError, match="HOST_EXECUTION_"):
            host.observe_execution_reconciliation_evidence_v1(bindings)
    if fault in {"live-host", "live-port"}:
        assert host.reconciliation_transport.calls == []
    else:
        assert host.owner.active_sum_v1() == held
    assert scope.state_path.read_bytes() == before
    assert not scope.journal_path.exists()


@pytest.mark.parametrize(
    "fault",
    [
        "snapshot",
        "revision",
        "missing_revision_digest",
        "later_observation",
        "foreign_session",
        "stale",
        "owner_closed",
    ],
)
def test_safety_checks_the_original_host_revision(shadow_host, fault):
    host, scope, identity, _, held = shadow_host
    bindings = {"LANE_1": recovery_fixture._bound()}
    context, evidence_by_rid = host.observe_execution_reconciliation_evidence_v1(bindings)
    evidence = evidence_by_rid[identity.portfolio_reservation_id]
    if fault == "snapshot":
        evidence = replace(
            evidence, snapshot=replace(evidence.snapshot, pending_orders_observation={})
        )
    elif fault == "revision":
        evidence = replace(evidence, revision_ref=(evidence.revision_ref[0], "0" * 64))
    elif fault == "missing_revision_digest":
        evidence = replace(evidence, revision_ref=(evidence.revision_ref[0], None))
    elif fault == "later_observation":
        host.reconciliation_transport.filled = identity.final_quantity
        host.observe_v1(bindings)
    elif fault == "foreign_session":
        evidence = replace(evidence, session_id="foreign-session")
    elif fault == "stale":
        host.clock = lambda: NOW.timestamp() + 6
    else:
        host.close()
    before = scope.state_path.read_bytes()
    with pytest.raises(
        ValueError,
        match="INCIDENT_HOST_EVIDENCE|DURABLE_BUDGET_REVISION|EXECUTION_RECONCILIATION_READBACK",
    ):
        deliver_host_execution_incident_v1(scope=scope, context=context, evidence=evidence)
    assert host.owner.active_sum_v1() == held
    assert scope.state_path.read_bytes() == before
    assert not scope.journal_path.exists()
