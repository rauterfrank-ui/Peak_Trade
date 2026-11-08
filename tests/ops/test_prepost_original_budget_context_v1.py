"""Original owner, real consumers, temporary stores and explicit synthetic ports only."""

from dataclasses import replace
from pathlib import Path
import json
import socket

import pytest
from tests.ops._current_post_safety_fixture_v1 import (
    synthetic_active_post_safety_v1 as synthetic_active_post_safety_v1,
)

from src.ops.full_core_live_path_composition_root_v1 import (
    current_productive_actual_venue_post_immediate_pre_mutation_freshness_v1 as freshness,
    current_productive_one_shot_fresh_envelope_permit_mint_durable_consume_and_post_join_v1 as lower,
)
from src.ops.full_core_live_path_composition_root_v1.envelope_bound_external_effect_send_seam_v1 import (
    FullCoreEnvelopeBoundSendSeamError,
    inspect_original_portfolio_execution_context_v1,
)
from src.ops.full_core_live_path_composition_root_v1.final_order_envelope_v1 import (
    build_final_order_envelope_v1,
)
from src.ops.full_core_live_path_composition_root_v1.fresh_pretrade_runtime_get_v1 import (
    ENDPOINT_ACCOUNT_CONFIG,
    ENDPOINT_ACCOUNT_BALANCE,
)
from src.ops.governed_productive_account_equity_authority_producer_v1 import (
    current_productive_actual_venue_post_with_fresh_envelope_bound_single_use_permit_v1 as caller,
)
from tests.ops.test_portfolio_execution_recovery_v1 import seed
from tests.ops.test_prepost_position_source_admission_v1 import Port, DECISION, _bound
from tests.ops.test_current_productive_actual_venue_post_with_fresh_envelope_bound_single_use_permit_v1 import (
    _FakeKeychainBackend,
    _TimeoutOpener,
    _clean_post_integrity,
)


@pytest.fixture(autouse=True)
def no_network(monkeypatch, tmp_path):
    from tests.ops._current_productive_pre_external_test_process_isolation_v1 import (
        establish_current_productive_pre_external_test_process_isolation_v1,
        reset_current_productive_pre_external_shared_test_process_state_v1,
    )

    establish_current_productive_pre_external_test_process_isolation_v1(
        monkeypatch=monkeypatch,
        f1_root=tmp_path / "synthetic-f1-m9-isolation",
        reseed_workspace_f1_m9=False,
    )

    def deny(*args, **kwargs):
        raise AssertionError("No venue or real credential port is allowed")

    monkeypatch.setattr(socket.socket, "connect", deny)
    monkeypatch.setattr(socket, "create_connection", deny)
    yield
    reset_current_productive_pre_external_shared_test_process_state_v1()


@pytest.fixture
def original(tmp_path):
    host, rid, identity, envelope = seed(tmp_path / "original-budget")
    try:
        yield (
            host,
            dict(
                envelope=envelope,
                portfolio_budget_owner=host.owner,
                portfolio_reservation_id=rid,
                execution_identity=identity,
            ),
        )
    finally:
        host.close()


def files(root):
    return {str(p.relative_to(root)): p.read_bytes() for p in root.rglob("*") if p.is_file()}


def rebuild(order, **changes):
    payload = order.to_canonical_payload_v1()
    payload.pop("schema_version")
    payload.pop("issued_for_exact_action")
    return build_final_order_envelope_v1(**{**payload, **changes})


class AccountPort(Port):
    """Original typed GET/DataSafety labels exercised by an explicit test double."""

    def __init__(self, args, *, uid=None, after_last=None):
        super().__init__()
        native = args["envelope"].instrument_id
        account = args["portfolio_budget_owner"].durable_scope_identity_v1()["account"]

        def bind(value):
            if isinstance(value, dict):
                return {k: account if k == "uid" else bind(v) for k, v in value.items()}
            if isinstance(value, list):
                return [bind(v) for v in value]
            return native if value == _bound().venue_native_id else value

        self.base.payloads = bind(self.base.payloads)
        if uid is not None:
            self.base.payloads[ENDPOINT_ACCOUNT_CONFIG]["data"][0]["uid"] = uid
        self.after_last = after_last

    def get(self, **kwargs):
        result = super().get(**kwargs)
        if len(self.requests) == 10 and self.after_last is not None:
            self.after_last()
        return result


def prove(args, port=None):
    return freshness.prove_immediate_pre_mutation_freshness_for_actual_venue_post_v1(
        **args, read_only_get_transport=port or AccountPort(args), pretrade_decision_id=DECISION
    )


def execute(args, tmp_path, *, port=None, opener=None):
    return caller.execute_current_productive_actual_venue_post_with_fresh_envelope_bound_single_use_permit_v1(
        **args,
        owner_go=caller.OWNER_GO,
        baseline_origin_main_sha=caller.EXPECTED_BASELINE_ORIGIN_MAIN_SHA,
        store_root=tmp_path / "send",
        evidence_root=tmp_path / "evidence",
        perform_real_venue_post=True,
        k1_backend=_FakeKeychainBackend(),
        opener_factory=lambda: opener or _TimeoutOpener(),
        read_only_get_transport=port or AccountPort(args),
        execution_integrity_backend=_clean_post_integrity(),
    )


def test_original_context_inspection_does_not_advance_or_write(original, tmp_path):
    host, args = original
    before = files(tmp_path)
    proof = inspect_original_portfolio_execution_context_v1(**args)
    assert proof["account"] == host.owner.durable_scope_identity_v1()["account"]
    assert proof["execution_identity_digest"] == args["execution_identity"].identity_digest()
    assert proof["scope"] == "ORIGINAL_COMMITTED_PLAN_CONTEXT_ONLY"
    assert files(tmp_path) == before
    assert (
        host.owner.execution_links_v1()[args["portfolio_reservation_id"]]["phase"] == "PLAN_BOUND"
    )


def test_account_from_original_owner_reaches_original_get_consumer(original, tmp_path):
    host, args = original
    before = files(tmp_path)
    port = AccountPort(args)
    result = prove(args, port)
    assert result.all_required_pre_post_gates_pass, result.reason_codes
    assert result.position_truth == "FLAT"
    assert result.account_identity_binding_status == "TRUSTED_PRESENT"
    assert result.scope == "PREPOST_ORIGINAL_BUDGET_ACCOUNT_POSITION_AND_VENUE_QUANTITY_ONLY"
    assert result.account_source_binding["envelope_digest"] == args["envelope"].envelope_digest
    assert result.account_source_binding["reservation_id"] == args["portfolio_reservation_id"]
    assert (
        result.account_source_binding["execution_identity_digest"]
        == args["execution_identity"].identity_digest()
    )
    assert len(port.requests) == 10
    assert files(tmp_path) == before
    assert host.owner.active_sum_v1() > 0


@pytest.mark.parametrize("uid", ["foreign-account", "", " 123", 123, True, [], {}])
def test_foreign_or_malformed_account_is_not_bound(original, uid):
    _, args = original
    result = prove(args, AccountPort(args, uid=uid))
    assert not result.all_required_pre_post_gates_pass
    assert result.account_identity_binding_status != "TRUSTED_PRESENT"
    assert not result.account_source_binding


@pytest.mark.parametrize("environment", ["SHADOW", "PAPER", "TESTNET"])
@pytest.mark.parametrize("boundary", ["top", "lower", "freshness"])
def test_non_live_execution_context_cannot_enter_actual_venue_path(
    original, tmp_path, environment, boundary
):
    _, args = original
    args = {
        **args,
        "execution_identity": replace(
            args["execution_identity"], execution_environment=environment
        ),
    }
    before = files(tmp_path)
    probe = lower.OneShotJoinProbeV1()
    if boundary == "top":
        with pytest.raises(
            caller.CurrentProductiveActualVenuePostError, match="EXECUTION_ENVIRONMENT_MISMATCH"
        ):
            execute(args, tmp_path, port=object())
    elif boundary == "lower":
        with pytest.raises(
            lower.CurrentProductiveOneShotFreshEnvelopeJoinError,
            match="EXECUTION_ENVIRONMENT_MISMATCH",
        ):
            lower.attempt_current_productive_one_shot_fresh_envelope_permit_mint_durable_consume_and_post_join_v1(
                **args,
                post_owner_go=lower.POST_OWNER_GO,
                store_root=tmp_path / "send",
                k1_backend=_FakeKeychainBackend(),
                probe=probe,
            )
        assert not probe.permit_minted
    else:
        with pytest.raises(
            freshness.CurrentProductiveActualVenuePostPreMutationFreshnessError,
            match="EXECUTION_ENVIRONMENT_MISMATCH",
        ):
            prove(args, port=object())
    assert files(tmp_path) == before


@pytest.mark.parametrize(
    "fault", ["missing", "duplicate", "balance_conflict", "mode", "instrument"]
)
def test_original_identity_conjunction_is_not_replaced_by_uid_only(original, fault):
    _, args = original
    port = AccountPort(args)
    if fault == "missing":
        port.base.payloads[ENDPOINT_ACCOUNT_CONFIG]["data"][0].pop("uid")
    elif fault == "duplicate":
        port.base.payloads[ENDPOINT_ACCOUNT_CONFIG]["data"] *= 2
    elif fault == "balance_conflict":
        port.base.payloads[ENDPOINT_ACCOUNT_BALANCE]["data"][0]["uid"] = "foreign-account"
    elif fault == "mode":
        port.base.payloads[ENDPOINT_ACCOUNT_CONFIG]["data"][0]["tdMode"] = "isolated"
    else:
        for payload in port.base.payloads.values():
            if isinstance(payload, dict):
                for row in payload.get("data", []):
                    if row.get("instId") == args["envelope"].instrument_id:
                        row["instId"] = "foreign-instrument"
    result = prove(args, port)
    assert not result.all_required_pre_post_gates_pass
    assert result.account_identity_binding_status != "TRUSTED_PRESENT"


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("account_identity", "foreign-account"),
        ("canonical_decision_id", "foreign-decision"),
        ("native_id", "foreign-native"),
        ("instrument_id", "foreign-canonical"),
        ("envelope_identity", "foreign-envelope"),
        ("envelope_digest", "f" * 64),
        ("final_quantity", "999"),
        ("selected_side", "SHORT"),
        ("order_type", "limit"),
    ],
)
def test_original_budget_identity_predicates_deny_before_any_new_effect(
    original, tmp_path, field, value
):
    _, original_args = original
    args = {
        **original_args,
        "execution_identity": replace(original_args["execution_identity"], **{field: value}),
    }
    before = files(tmp_path)
    with pytest.raises(
        caller.CurrentProductiveActualVenuePostError, match="EXECUTION_IDENTITY_MISMATCH"
    ):
        execute(args, tmp_path, port=object())
    assert files(tmp_path) == before


@pytest.mark.parametrize("boundary", ["top", "lower", "freshness"])
def test_bound_reservation_without_original_context_denies_before_mint(
    original, tmp_path, boundary
):
    _, args = original
    order = rebuild(
        args["envelope"],
        admission_ref="execution:portfolio-reservation:" + args["portfolio_reservation_id"],
    )
    before = files(tmp_path)
    probe = lower.OneShotJoinProbeV1()
    if boundary == "top":
        with pytest.raises(caller.CurrentProductiveActualVenuePostError, match="CONTEXT_REQUIRED"):
            execute({"envelope": order}, tmp_path, port=object())
    elif boundary == "lower":
        with pytest.raises(
            lower.CurrentProductiveOneShotFreshEnvelopeJoinError, match="CONTEXT_REQUIRED"
        ):
            lower.attempt_current_productive_one_shot_fresh_envelope_permit_mint_durable_consume_and_post_join_v1(
                envelope=order,
                post_owner_go=lower.POST_OWNER_GO,
                store_root=tmp_path / "send",
                k1_backend=_FakeKeychainBackend(),
                probe=probe,
            )
        assert not probe.permit_minted
    else:
        with pytest.raises(
            freshness.CurrentProductiveActualVenuePostPreMutationFreshnessError,
            match="CONTEXT_REQUIRED",
        ):
            freshness.prove_immediate_pre_mutation_freshness_for_actual_venue_post_v1(
                envelope=order,
                read_only_get_transport=object(),
                pretrade_decision_id=DECISION,
            )
    assert files(tmp_path) == before


@pytest.mark.parametrize(
    "fault",
    [
        "reservation",
        "envelope",
        "partial",
        "wrong_owner",
        "fenced",
        "closed",
        "released",
        "memory_owner",
    ],
)
def test_original_owner_and_plan_cannot_be_replaced(original, tmp_path, fault):
    host, original_args = original
    args = dict(original_args)
    if fault == "reservation":
        args["portfolio_reservation_id"] = "foreign-reservation"
    elif fault == "envelope":
        args["envelope"] = rebuild(
            args["envelope"],
            client_order_id="differentvalidplan",
            venue_plan_clordid="differentvalidplan",
        )
    elif fault == "partial":
        args["execution_identity"] = None
    elif fault == "wrong_owner":
        args["portfolio_budget_owner"] = object()
    elif fault == "fenced":
        host.owner.restart_fail_closed_v1()
    elif fault == "released":
        host.owner.release_sizing_or_admission_deny_v1(args["portfolio_reservation_id"])
    elif fault == "memory_owner":
        from src.ops.portfolio_capital_reservation_budget_v1.contract_v1 import (
            PortfolioCapitalReservationBudgetOwnerV1,
        )

        args["portfolio_budget_owner"] = PortfolioCapitalReservationBudgetOwnerV1()
    else:
        host.close()
    before = files(tmp_path)
    with pytest.raises(caller.CurrentProductiveActualVenuePostError):
        execute(args, tmp_path, port=object())
    assert files(tmp_path) == before


def test_owner_fenced_during_acquisition_is_rechecked_before_go(original, tmp_path):
    host, args = original
    port = AccountPort(args, after_last=host.owner.restart_fail_closed_v1)
    result = prove(args, port)
    assert not result.all_required_pre_post_gates_pass
    assert result.account_identity_binding_status != "TRUSTED_PRESENT"
    assert len(port.requests) == 10
    assert not (tmp_path / "send").exists()
    assert host.owner.active_sum_v1() > 0


def test_wrong_account_at_actual_caller_leaves_original_hold_and_go_unconsumed(original, tmp_path):
    host, args = original
    with pytest.raises(
        caller.CurrentProductiveActualVenuePostError, match="ORIGINAL_ACCOUNT_BINDING_NOT_TRUSTED"
    ):
        execute(args, tmp_path, port=AccountPort(args, uid="foreign-account"))
    assert not list((tmp_path / "send").glob("*.json"))
    assert (
        host.owner.execution_links_v1()[args["portfolio_reservation_id"]]["phase"] == "PLAN_BOUND"
    )
    assert host.owner.active_sum_v1() > 0


def test_actual_wrappers_reach_both_original_barriers_once_and_keep_unknown_hold(
    original, tmp_path
):
    host, args = original
    calls = []

    class BoundaryOpener:
        def open(self, request, timeout=0):
            link = host.owner.execution_links_v1()[args["portfolio_reservation_id"]]
            assert link["phase"] == "SUBMIT_MAY_HAVE_OCCURRED"
            assert link["identity"] == args["execution_identity"].to_dict()
            consume = json.loads(
                (tmp_path / "send/full_core_external_effect_permit_consume_v1.json").read_text()
            )
            assert consume["durable_state"] == "SENT_INITIATED"
            calls.append(request.full_url)
            raise TimeoutError("Explicit synthetic uncertainty, no socket")

    result = execute(args, tmp_path, opener=BoundaryOpener())
    assert result.post_outcome == "UNKNOWN_EXTERNAL_EFFECT_POSSIBLE"
    assert result.replay_attempt_blocked == "true"
    assert result.second_post_performed == "false"
    assert len(calls) == 1
    before = files(tmp_path)
    with pytest.raises(caller.CurrentProductiveActualVenuePostError):
        execute(args, tmp_path, port=object())
    assert len(calls) == 1
    assert files(tmp_path) == before
    assert host.owner.active_sum_v1() > 0


@pytest.mark.parametrize("short", [False, True])
def test_actual_n1_plan_owner_reaches_account_consumer_without_any_send(
    tmp_path, monkeypatch, short
):
    from src.ops.portfolio_capital_reservation_budget_v1.contract_v1 import (
        PortfolioCapitalReservationBudgetOwnerV1 as Owner,
    )
    from src.ops.full_core_live_path_composition_root_v1.full_core_exchange_reconciliation_v1 import (
        FullCoreExchangeReconciliationIdentityV1 as Identity,
    )
    from src.ops.full_core_live_path_composition_root_v1.full_core_pre_post_capital_guard_binding_v1 import (
        compute_full_core_venue_plan_digest_from_envelope_v1,
    )
    from tests.ops._wp03_supervisor_golden_harness_v1 import _run_layered_entry_supervisor_v1

    original_bind = Owner.bind_execution_plan_v1
    proofs = []

    def bind(owner, rid, envelope, **kwargs):
        result = original_bind(owner, rid, envelope, **kwargs)
        state = owner.risk_snapshot_v1()["state"]
        reservation = next(row for row in state["reservations"] if row["reservation_id"] == rid)
        bound = reservation["binding"]["bound"]
        # Explicit synthetic caller-supplied execution identity. The natural
        # host/authorization producer for this input remains a separate join.
        identity = Identity(
            canonical_decision_id=reservation["decision_id"],
            decision_outcome="ENTER",
            selected_side=state["sizing_bindings"][rid]["decision"]["selected_side"],
            instrument_id=bound["instrument_id"],
            native_id=envelope.instrument_id,
            account_identity=state["account_identity"],
            execution_environment="LIVE",
            venue="OKX",
            venue_plan_identity=envelope.venue_plan_clordid,
            venue_plan_digest=compute_full_core_venue_plan_digest_from_envelope_v1(envelope),
            envelope_identity=envelope.envelope_id,
            envelope_digest=envelope.envelope_digest,
            final_quantity=envelope.quantity,
            quantity_unit=envelope.quantity_unit,
            order_type=envelope.order_type,
            order_price=envelope.price,
            clordid=envelope.client_order_id,
            exchange_ord_id=None,
            owner_go="SYNTHETIC_CALLER_CONTEXT_NOT_AUTHORITY",
            atomic_consumption_key="SYNTHETIC_CALLER_CONTEXT_NOT_AUTHORITY",
            submit_attempt_id="SYNTHETIC_NO_ATTEMPT",
            local_durable_state_version="SYNTHETIC_NO_SUBMIT",
        )
        args = dict(
            envelope=envelope,
            portfolio_budget_owner=owner,
            portfolio_reservation_id=rid,
            execution_identity=identity,
        )
        assert envelope.admission_ref.endswith(":portfolio-reservation:" + rid)
        before = files(tmp_path)
        port = AccountPort(args)
        proof = prove(args, port)
        assert proof.all_required_pre_post_gates_pass, proof.reason_codes
        assert proof.account_identity_binding_status == "TRUSTED_PRESENT"
        assert len(port.requests) == 10
        assert files(tmp_path) == before
        assert owner.execution_links_v1()[rid]["phase"] == "PLAN_BOUND"
        proofs.append(proof)
        return result

    monkeypatch.setattr(Owner, "bind_execution_plan_v1", bind)
    run = _run_layered_entry_supervisor_v1(tmp_path, short=short)
    assert len(proofs) == 1
    assert run.policy_result.orchestrator_result.post_count == 0
    assert run.policy_result.orchestrator_result.permit_created is False
