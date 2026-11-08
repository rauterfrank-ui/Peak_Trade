"""Current original budget admission at late actual POST consumers."""

from dataclasses import replace
import pytest

from tests.ops._current_post_safety_fixture_v1 import (
    synthetic_active_post_safety_v1 as synthetic_active_post_safety_v1,
    synthetic_current_post_pending_context_v1,
)
from tests.ops.test_n1_original_reservation_host_handoff_v1 import (
    synthetic_ports_and_isolation as synthetic_ports_and_isolation,
)
from tests.ops.test_prepost_original_budget_context_v1 import (
    AccountPort,
    caller,
    no_network as no_network,
    _clean_post_integrity,
)
from tests.ops.test_current_productive_actual_venue_post_with_fresh_envelope_bound_single_use_permit_v1 import (
    _FakeKeychainBackend,
)


@pytest.mark.parametrize("phase", ["during_k1", "opener_factory"])
def test_actual_post_does_not_outlive_original_budget_fence(tmp_path, monkeypatch, phase):
    from tests.ops.test_n1_original_plan_origin_v1 import seed_with_origin

    host, rid, _, order, _, _ = seed_with_origin(tmp_path, monkeypatch)
    args = dict(
        envelope=order,
        portfolio_budget_owner=host.owner,
        portfolio_reservation_id=rid,
        execution_plan_context=host.owner.execution_plan_context_v1(rid, order),
    )
    args["post_pending_context"] = synthetic_current_post_pending_context_v1(
        order, account=host.owner.durable_scope_identity_v1()["account"]
    )
    calls = []

    class Backend(_FakeKeychainBackend):
        def copy_matching_generic_password_value_data_v1(self, **kw):
            result = super().copy_matching_generic_password_value_data_v1(**kw)
            if phase == "during_k1":
                host.owner.restart_fail_closed_v1()
            return result

    class Opener:
        def open(self, *a, **kw):
            calls.append("possible_socket")
            raise TimeoutError("injected")

    def factory():
        if phase == "opener_factory":
            host.owner.restart_fail_closed_v1()
        return Opener()

    held = host.owner.active_sum_v1()
    try:
        with pytest.raises(caller.CurrentProductiveActualVenuePostError, match="POST_BUDGET"):
            caller.execute_current_productive_actual_venue_post_with_fresh_envelope_bound_single_use_permit_v1(
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
        assert calls == []
        assert host.owner.active_sum_v1() == held > 0
    finally:
        host.close()


def seeded(tmp_path, monkeypatch, modern):
    if modern:
        from tests.ops.test_n1_original_plan_origin_v1 import seed_with_origin

        host, rid, _, order, _, _ = seed_with_origin(tmp_path, monkeypatch)
        args = dict(execution_plan_context=host.owner.execution_plan_context_v1(rid, order))
    else:
        from tests.ops.test_portfolio_execution_recovery_v1 import seed

        host, rid, identity, order = seed(tmp_path)
        args = dict(execution_identity=identity)
    return host, dict(
        envelope=order, portfolio_budget_owner=host.owner, portfolio_reservation_id=rid, **args
    )


def started(tmp_path, monkeypatch, modern):
    from src.ops.full_core_live_path_composition_root_v1 import (
        external_effect_permit_durable_consume_v1 as store,
    )
    from tests.ops.test_full_core_current_productive_envelope_bound_single_use_external_effect_send_seam_v1 import (
        _permit,
    )
    from src.ops.full_core_live_path_composition_root_v1.current_productive_post_budget_admission_v1 import (
        capture_current_post_budget_admission_v1,
    )

    host, args = seeded(tmp_path / "budget", monkeypatch, modern)
    owner, rid, order = host.owner, args["portfolio_reservation_id"], args["envelope"]
    permit = _permit(order)
    if modern:
        identity = owner.begin_execution_submit_v2(
            rid,
            order,
            args["execution_plan_context"],
            permit,
            transport_store_root=tmp_path / "send",
        )
    else:
        identity = args["execution_identity"]
        owner.mark_execution_submit_boundary_v1(rid, identity, external_effect_permit=permit)
    store.persist_external_effect_durable_consume_v1(
        store_root=tmp_path / "send",
        permit=permit,
        envelope=order,
        durable_state="SENT_INITIATED",
        post_count=1,
        outcome="UNKNOWN",
        **({"execution_identity": identity} if modern else {}),
    )
    claim = store.claim_original_permit_transport_attempt_v1(
        store_root=tmp_path / "send",
        permit_id=permit.permit_id,
        envelope_id=order.envelope_id,
        envelope_digest=order.envelope_digest,
    )
    context = capture_current_post_budget_admission_v1(
        owner=owner,
        reservation_id=rid,
        envelope=order,
        identity=None if modern else identity,
        permit=permit,
        transport_attempt=claim,
    )
    return host, args, context


@pytest.mark.parametrize("modern", [False, True])
def test_original_started_reader_remains_read_only_and_keeps_actual_identity_version(
    tmp_path, monkeypatch, modern
):
    from tests.ops.test_prepost_original_budget_context_v1 import files

    host, args, context = started(tmp_path, monkeypatch, modern)
    before = files(tmp_path)
    sequence = host.owner._store.sequence
    try:
        proof = context.inspect_v1(envelope=args["envelope"], stage="READ_ONLY")
        assert proof["scope"] == "CURRENT_ORIGINAL_BUDGET_EXECUTION_ADMISSION_ONLY"
        assert proof["execution_identity_contract"] == context.identity.to_dict()["contract_id"]
        assert proof["execution_identity_digest"] == context.identity.identity_digest()
        assert host.owner._store.sequence == sequence
        assert files(tmp_path) == before
    finally:
        host.close()


@pytest.mark.parametrize("modern", [False, True])
def test_actual_positive_owner_reaches_four_late_readbacks_without_new_get_or_mutation(
    tmp_path, monkeypatch, modern
):
    from tests.ops.test_prepost_original_budget_context_v1 import execute

    host, args = seeded(tmp_path / "budget", monkeypatch, modern)
    calls = []
    original = host.owner.inspect_started_execution_attempt_v1

    def read(*a, **kw):
        result = original(*a, **kw)
        calls.append(result)
        return result

    monkeypatch.setattr(host.owner, "inspect_started_execution_attempt_v1", read)
    order = args["envelope"]
    wire = order.to_runtime_json_v1()
    sequence, held = host.owner._store.sequence, host.owner.active_sum_v1()
    port = AccountPort(args)
    try:
        result = execute(args, tmp_path, port=port)
        assert result.post_outcome == "UNKNOWN_EXTERNAL_EFFECT_POSSIBLE"
        assert len(calls) == 4  # before K1, public/internal HTTP, after opener
        assert len(port.requests) == 11  # ten pre-mutation and original follow-on position snapshot
        assert host.owner._store.sequence == sequence + 1
        assert host.owner.active_sum_v1() == held > 0
        assert order.to_runtime_json_v1() == wire
    finally:
        host.close()


@pytest.mark.parametrize("modern", [False, True])
@pytest.mark.parametrize("fault", ["recovery", "closed", "storage_failed", "not_admitted"])
@pytest.mark.parametrize("phase", ["during_k1", "opener_factory"])
def test_actual_original_owner_withdrawal_is_consumed_at_later_http_boundaries(
    tmp_path, monkeypatch, modern, fault, phase
):
    from src.ops.full_core_live_path_composition_root_v1.external_effect_permit_durable_consume_v1 import (
        load_external_effect_durable_consume_v1,
    )

    host, args = seeded(tmp_path / "budget", monkeypatch, modern)
    owner = host.owner

    def withdraw():
        if fault == "recovery":
            owner.restart_fail_closed_v1()
        elif fault == "closed":
            owner.close()
        elif fault == "storage_failed":
            owner._storage_failed = True  # Negative fault only.
        else:
            owner._admitted = False  # Negative fault only; never grants admission.

    class Backend(_FakeKeychainBackend):
        def copy_matching_generic_password_value_data_v1(self, **kw):
            result = super().copy_matching_generic_password_value_data_v1(**kw)
            if phase == "during_k1":
                withdraw()
            return result

    calls = []

    class Opener:
        def open(self, *a, **kw):
            calls.append("socket")
            raise AssertionError("No HTTP call after original budget withdrawal")

    def factory():
        if phase == "opener_factory":
            withdraw()
        return Opener()

    args["post_pending_context"] = synthetic_current_post_pending_context_v1(
        args["envelope"], account=owner.durable_scope_identity_v1()["account"]
    )
    port = AccountPort(args)
    held = owner.active_sum_v1()
    sequence = owner._store.sequence
    try:
        with pytest.raises(caller.CurrentProductiveActualVenuePostError, match="POST_BUDGET"):
            caller.execute_current_productive_actual_venue_post_with_fresh_envelope_bound_single_use_permit_v1(
                **args,
                owner_go=caller.OWNER_GO,
                baseline_origin_main_sha=caller.EXPECTED_BASELINE_ORIGIN_MAIN_SHA,
                store_root=tmp_path / "send",
                evidence_root=tmp_path / "evidence",
                perform_real_venue_post=True,
                k1_backend=Backend(),
                opener_factory=factory,
                read_only_get_transport=port,
                execution_integrity_backend=_clean_post_integrity(),
            )
        assert calls == []
        assert len(port.requests) == 10
        assert owner.active_sum_v1() == held > 0
        assert owner._store.sequence == sequence + 1 + int(fault == "recovery")
        record = load_external_effect_durable_consume_v1(store_root=tmp_path / "send")["record"]
        assert record["durable_state"] == "ABORTED_BEFORE_TRANSPORT"
        assert record["transport_attempt"]["phase"] == "ABORTED"
        assert record["transport_attempt"]["reason_code"].startswith("POST_BUDGET")
    finally:
        host.close()


@pytest.mark.parametrize("modern", [False, True])
@pytest.mark.parametrize(
    "phase", ["after_permit_before_claim", "after_claim", "during_signing", "after_socket"]
)
def test_original_claim_boundary_preserves_uncertainty_and_never_uses_counters_as_negative_proof(
    tmp_path, monkeypatch, modern, phase
):
    from tests.ops.test_prepost_original_budget_context_v1 import lower
    from src.ops.full_core_live_path_composition_root_v1 import (
        full_core_productive_http_post_transport_v1 as http,
    )
    from src.ops.full_core_live_path_composition_root_v1.external_effect_permit_durable_consume_v1 import (
        load_external_effect_durable_consume_v1,
    )

    host, args = seeded(tmp_path / "budget", monkeypatch, modern)
    owner = host.owner

    def wrap(target, name):
        original = getattr(target, name)

        def wrapped(*a, **kw):
            result = original(*a, **kw)
            owner.restart_fail_closed_v1()
            return result

        monkeypatch.setattr(target, name, wrapped)

    if phase == "after_permit_before_claim":
        from src.ops.full_core_live_path_composition_root_v1 import (
            envelope_bound_external_effect_send_seam_v1 as seam,
        )

        wrap(seam, "persist_external_effect_durable_consume_v1")
    elif phase == "after_claim":
        wrap(lower, "claim_original_permit_transport_attempt_v1")
    elif phase == "during_signing":
        wrap(http, "build_k1_okx_venue_auth_headers_v1")
    calls = []

    class Opener:
        def open(self, *a, **kw):
            calls.append("possible_socket")
            owner.restart_fail_closed_v1()
            raise http.FullCoreCurrentPostBudgetVetoError("POST_BUDGET_FORGED_AFTER_SOCKET")

    args["post_pending_context"] = synthetic_current_post_pending_context_v1(
        args["envelope"], account=owner.durable_scope_identity_v1()["account"]
    )
    port = AccountPort(args)
    held = owner.active_sum_v1()
    try:
        # Original V2 reader fences before any transport claim in this phase.
        # Keep its existing ValueError contract, not a fabricated new abort.
        error = (
            ValueError
            if phase == "after_permit_before_claim" and modern
            else caller.CurrentProductiveActualVenuePostError
        )
        with pytest.raises(error):
            caller.execute_current_productive_actual_venue_post_with_fresh_envelope_bound_single_use_permit_v1(
                **args,
                owner_go=caller.OWNER_GO,
                baseline_origin_main_sha=caller.EXPECTED_BASELINE_ORIGIN_MAIN_SHA,
                store_root=tmp_path / "send",
                evidence_root=tmp_path / "evidence",
                perform_real_venue_post=True,
                k1_backend=_FakeKeychainBackend(),
                opener_factory=lambda: Opener(),
                read_only_get_transport=port,
                execution_integrity_backend=_clean_post_integrity(),
            )
        record = load_external_effect_durable_consume_v1(store_root=tmp_path / "send")["record"]
        assert calls == (["possible_socket"] if phase == "after_socket" else [])
        assert owner.active_sum_v1() == held > 0
        assert len(port.requests) == 10
        if phase == "after_permit_before_claim" and modern:
            assert record["durable_state"] == "SENT_INITIATED"
            assert "transport_attempt" not in record
        elif phase == "after_socket":
            assert record["durable_state"] == "SENT_INITIATED"
            assert record["transport_attempt"]["phase"] == "MAY_HAVE_SENT"
        else:
            assert record["durable_state"] == "ABORTED_BEFORE_TRANSPORT"
            assert record["transport_attempt"]["phase"] == "ABORTED"
    finally:
        host.close()


@pytest.mark.parametrize("modern", [False, True])
@pytest.mark.parametrize(
    "fault", ["owner", "reservation", "identity", "permit", "claim", "envelope"]
)
def test_foreign_or_changed_original_context_cannot_be_positive_budget_admission(
    tmp_path, monkeypatch, modern, fault
):
    from src.ops.full_core_live_path_composition_root_v1.current_productive_post_budget_admission_v1 import (
        CurrentPostBudgetAdmissionError,
    )
    from src.ops.portfolio_capital_reservation_budget_v1.contract_v1 import (
        PortfolioCapitalReservationBudgetOwnerV1 as Owner,
    )

    host, args, context = started(tmp_path, monkeypatch, modern)
    if fault == "owner":
        context = replace(context, owner=Owner())
    elif fault == "reservation":
        context = replace(context, reservation_id="foreign")
    elif fault == "identity":
        context = replace(context, identity=replace(context.identity, account_identity="foreign"))
    elif fault == "permit":
        context = replace(context, permit=replace(context.permit, authority_ref="foreign"))
    elif fault == "claim":
        context = replace(
            context, transport_attempt=replace(context.transport_attempt, claim_id="foreign")
        )
    else:
        context = replace(context, envelope=replace(args["envelope"], quantity="999"))
    try:
        with pytest.raises(CurrentPostBudgetAdmissionError, match="POST_BUDGET"):
            context.inspect_v1(envelope=args["envelope"], stage="FOREIGN")
        assert host.owner.active_sum_v1() > 0
    finally:
        host.close()


@pytest.mark.parametrize("entry", ["public", "internal"])
def test_modern_dual_barrier_http_cannot_omit_original_owner_reference(
    tmp_path, monkeypatch, entry
):
    from tests.ops._current_post_safety_fixture_v1 import synthetic_current_post_quantity_context_v1
    from tests.ops.test_full_core_current_productive_envelope_bound_single_use_external_effect_send_seam_v1 import (
        _handle,
    )
    from src.ops.full_core_live_path_composition_root_v1.full_core_productive_http_post_transport_v1 import (
        FullCoreProductiveHttpTradeOrderTransportV1,
        FullCoreProductiveHttpPostError,
    )
    from src.ops.full_core_live_path_composition_root_v1.current_productive_post_safety_veto_v1 import (
        resolve_current_post_safety_context_v1,
    )
    from src.ops.full_core_live_path_composition_root_v1.envelope_bound_external_effect_send_seam_v1 import (
        _payload_from_envelope_v1,
    )

    host, args, context = started(tmp_path, monkeypatch, True)
    order = args["envelope"]
    transport = FullCoreProductiveHttpTradeOrderTransportV1(
        handle=_handle(),
        signing_handle=object(),
        transport_attempt=context.transport_attempt,
        post_safety_context=resolve_current_post_safety_context_v1(order, stage="TEST"),
        post_quantity_context=synthetic_current_post_quantity_context_v1(order),
        post_pending_context=synthetic_current_post_pending_context_v1(
            order, account=host.owner.durable_scope_identity_v1()["account"]
        ),
    )
    try:
        with pytest.raises(FullCoreProductiveHttpPostError, match="POST_BUDGET"):
            if entry == "internal":
                transport._perform_http_post_v1(payload=_payload_from_envelope_v1(order))
            else:
                transport.post_trade_order(
                    payload=_payload_from_envelope_v1(order),
                    permit_id=context.permit.permit_id,
                    envelope_id=order.envelope_id,
                    envelope_digest=order.envelope_digest,
                    one_shot_real_post=True,
                )
        assert transport.post_count == 0
        context.transport_attempt.inspect_v1()
    finally:
        host.close()


def test_wholly_unbound_legacy_path_is_explicitly_not_assessed(tmp_path):
    from tests.ops.test_original_permit_transport_abort_v1 import raw_claim
    from src.ops.full_core_live_path_composition_root_v1.current_productive_post_budget_admission_v1 import (
        inspect_current_post_budget_admission_v1,
    )

    claim, _, order = raw_claim(tmp_path)
    assert inspect_current_post_budget_admission_v1(
        None, envelope=order, transport_attempt=claim, stage="LEGACY"
    ) == {"scope": "LEGACY_ORIGINAL_BUDGET_NOT_ASSESSED"}


def test_current_budget_consumer_and_original_locked_reader_are_source_integrity_protected():
    from src.ops.full_core_live_path_composition_root_v1.current_productive_actual_venue_post_baseline_v1 import (
        PROTECTED_CURRENT_PRODUCTIVE_POST_SLICE_SURFACE_PATHS as paths,
    )

    assert (
        "src/ops/full_core_live_path_composition_root_v1/current_productive_post_budget_admission_v1.py"
        in paths
    )
    for name in ("contract_v1.py", "attempt_v2.py", "execution_v1.py", "durable_store_v1.py"):
        assert "src/ops/portfolio_capital_reservation_budget_v1/" + name in paths
