"""Original writer owns attempt/version identity; no synthetic authority aliases."""

from dataclasses import replace

import pytest

from src.ops.full_core_live_path_composition_root_v1.full_core_exchange_reconciliation_v1 import (
    PortfolioExecutionReconciliationIdentityV2,
    parse_exchange_reconciliation_identity_v1,
)
from tests.ops.test_n1_original_plan_origin_v1 import seed_with_origin
from tests.ops.test_n1_original_reservation_host_handoff_v1 import (
    synthetic_ports_and_isolation as synthetic_ports_and_isolation,
)
from tests.ops.test_original_budget_send_permit_handoff_v1 import cold_owner
from tests.ops.test_full_core_current_productive_envelope_bound_single_use_external_effect_send_seam_v1 import (
    _permit,
)


def test_plan_reference_is_read_only_and_has_no_attempt_or_send_permission(tmp_path, monkeypatch):
    host, rid, legacy, envelope, intent, plan = seed_with_origin(tmp_path, monkeypatch)
    try:
        before = host.owner.risk_snapshot_v1()
        sequence = host.owner._store.sequence
        context = host.owner.execution_plan_context_v1(rid, envelope)
        proof = host.owner.inspect_execution_plan_context_v1(rid, envelope, context)
        assert proof["context_kind"] == "ORIGINAL_PLAN_BEFORE_SUBMIT_ATTEMPT"
        assert "execution_identity_digest" not in proof
        assert "submit_attempt_id" not in vars(context)
        assert "authority_ref" not in vars(context)
        assert context.order_environment == plan.environment
        assert host.owner._store.sequence == sequence
        assert host.owner.risk_snapshot_v1() == before
    finally:
        host.close()


def test_original_budget_mints_once_and_binds_real_source_and_submit_revisions(
    tmp_path, monkeypatch
):
    host, rid, legacy, envelope, intent, plan = seed_with_origin(tmp_path, monkeypatch)
    try:
        context = host.owner.execution_plan_context_v1(rid, envelope)
        source_sequence, source_digest = host.owner._store.sequence, host.owner._store.head
        permit = _permit(envelope)
        identity = host.owner.begin_execution_submit_v2(rid, envelope, context, permit)
        assert type(identity) is PortfolioExecutionReconciliationIdentityV2
        assert identity.canonical_decision_id == intent.decision_id
        assert identity.canonical_intent_digest == intent.semantic_digest
        assert identity.instrument_id == intent.instrument_id != identity.native_id
        assert identity.native_id == plan.instrument_id
        assert identity.decision_outcome == intent.intent_action
        assert identity.final_quantity == envelope.quantity
        assert identity.budget_source_sequence == source_sequence
        assert identity.budget_source_digest == source_digest
        assert identity.budget_submit_sequence == host.owner._store.sequence == source_sequence + 1
        revision = host.owner._store.read_revision_v1(identity.budget_submit_sequence)
        assert revision["previous"] == source_digest
        assert revision["state"]["execution_links"][rid]["identity"] == identity.to_dict()
        assert identity.send_permit_id == permit.permit_id
        assert identity.send_authority_ref == permit.authority_ref != legacy.owner_go
        assert identity.submit_attempt_id != legacy.submit_attempt_id
        assert len(identity.submit_attempt_id) == 32
        assert (
            not {"owner_go", "atomic_consumption_key", "local_durable_state_version"}
            & identity.to_dict().keys()
        )
        assert parse_exchange_reconciliation_identity_v1(identity.to_dict()) == identity
        host.owner.inspect_started_execution_attempt_v2(rid, envelope, identity, permit)
        before = host.owner.risk_snapshot_v1()
        with pytest.raises(ValueError, match="REPLAY_OR_UNBOUND"):
            host.owner.begin_execution_submit_v2(rid, envelope, context, permit)
        with pytest.raises(ValueError, match="REPLAY_OR_UNBOUND|IDENTITY_TYPE_INVALID"):
            host.owner.mark_execution_submit_boundary_v1(rid, identity)
        assert host.owner.risk_snapshot_v1() == before
        restored = cold_owner(host)
        try:
            assert restored.execution_links_v1()[rid]["identity"] == identity.to_dict()
            assert restored.active_sum_v1() > 0 and restored.budget_state_v1().recovery_required
            with pytest.raises(ValueError, match="OWNER_FENCED"):
                restored.begin_execution_submit_v2(rid, envelope, context, permit)
        finally:
            restored.close()
    finally:
        host.close()


@pytest.mark.parametrize(
    "field",
    [
        "root",
        "account",
        "reservation_id",
        "envelope_id",
        "envelope_digest",
        "plan_origin_digest",
        "order_environment",
    ],
)
def test_foreign_plan_reference_cannot_mint_an_attempt(tmp_path, monkeypatch, field):
    host, rid, legacy, envelope, intent, plan = seed_with_origin(tmp_path, monkeypatch)
    try:
        context = host.owner.execution_plan_context_v1(rid, envelope)
        before = host.owner.risk_snapshot_v1()
        sequence = host.owner._store.sequence
        with pytest.raises(ValueError, match="CONTEXT_MISMATCH"):
            host.owner.begin_execution_submit_v2(
                rid, envelope, replace(context, **{field: "foreign"}), _permit(envelope)
            )
        assert host.owner.risk_snapshot_v1() == before
        assert host.owner._store.sequence == sequence
    finally:
        host.close()


@pytest.mark.parametrize(
    "field",
    [
        "budget_source_sequence",
        "budget_source_digest",
        "budget_submit_sequence",
        "submit_attempt_id",
        "send_authority_ref",
    ],
)
def test_cold_restore_rejects_identity_without_the_actual_original_commit(
    tmp_path, monkeypatch, field
):
    host, rid, legacy, envelope, intent, plan = seed_with_origin(tmp_path, monkeypatch)
    try:
        context = host.owner.execution_plan_context_v1(rid, envelope)
        identity = host.owner.begin_execution_submit_v2(rid, envelope, context, _permit(envelope))
        payload = host.owner.risk_snapshot_v1()["state"]
        raw = payload["execution_links"][rid]["identity"]
        raw[field] = (
            raw[field] + 1
            if type(raw[field]) is int
            else "f" * 32
            if field == "submit_attempt_id"
            else "foreign"
        )
        host.owner._store.save(payload)
        with pytest.raises(ValueError, match="DURABLE_BUDGET_SEMANTIC_RESTORE_UNPROVEN"):
            cold_owner(host)
    finally:
        host.close()


def test_original_host_reconciles_owned_identity_and_retains_attempt_version(tmp_path, monkeypatch):
    from tests.ops.test_portfolio_execution_recovery_v1 import ReadPort, NOW, _bound
    from tests.ops.test_portfolio_budget_host_v1 import _host, _fetch

    host, rid, legacy, envelope, intent, plan = seed_with_origin(tmp_path, monkeypatch)
    try:
        context = host.owner.execution_plan_context_v1(rid, envelope)
        identity = host.owner.begin_execution_submit_v2(rid, envelope, context, _permit(envelope))
    finally:
        host.close()
    restored = _host(
        tmp_path,
        _fetch(uid=identity.account_identity),
        clock=lambda: NOW,
        expected_account=identity.account_identity,
    )
    restored.reconciliation_transport = ReadPort(identity, state="canceled", filled="0")
    try:
        observed = restored.observe_v1({"LANE_1": _bound()})
        assert observed.execution_reconciliation[rid]["matched"]
        assert observed.execution_reconciliation[rid]["reservation_released"]
        assert restored.owner.execution_links_v1()[rid]["identity"] == identity.to_dict()
        assert restored.owner.active_sum_v1() == 0
        assert restored.owner.budget_state_v1().recovery_required
    finally:
        restored.close()


@pytest.mark.parametrize(
    "state,filled",
    [
        ("live", "0"),
        ("partially_filled", "0.01"),
        ("filled", "all"),
        ("canceled", "0.01"),
        ("unknown", "0"),
    ],
)
def test_original_recovery_keeps_hold_for_open_partial_filled_or_unresolved_execution(
    tmp_path, monkeypatch, state, filled
):
    from tests.ops.test_portfolio_execution_recovery_v1 import ReadPort, NOW, _bound
    from tests.ops.test_portfolio_budget_host_v1 import _host, _fetch

    host, rid, _, envelope, _, _ = seed_with_origin(tmp_path, monkeypatch)
    context = host.owner.execution_plan_context_v1(rid, envelope)
    identity = host.owner.begin_execution_submit_v2(rid, envelope, context, _permit(envelope))
    filled = envelope.quantity if filled == "all" else filled
    held = host.owner.active_sum_v1()
    host.close()
    restored = _host(
        tmp_path,
        _fetch(
            uid=identity.account_identity,
            positions=[
                {
                    "instId": identity.native_id,
                    "posSide": "net",
                    "pos": filled,
                }
            ]
            if filled != "0"
            else (),
        ),
        clock=lambda: NOW,
        expected_account=identity.account_identity,
    )
    restored.reconciliation_transport = ReadPort(identity, state=state, filled=filled)
    try:
        observation = restored.observe_v1({"LANE_1": _bound()})
        result = observation.execution_reconciliation[rid]
        assert result["reservation_released"] is False
        assert restored.owner.active_sum_v1() == held > 0
        assert restored.owner.execution_links_v1()[rid]["identity"] == identity.to_dict()
        with pytest.raises(ValueError, match="OWNER_FENCED"):
            restored.owner.begin_execution_submit_v2(rid, envelope, context, _permit(envelope))
    finally:
        restored.close()


@pytest.mark.parametrize(
    "fault", ["missing_version", "unknown_version", "missing_field", "legacy_field", "extra"]
)
def test_new_identity_cannot_be_parsed_through_legacy_defaults(tmp_path, monkeypatch, fault):
    host, rid, legacy, envelope, _, _ = seed_with_origin(tmp_path, monkeypatch)
    try:
        # Historical V1, including its historical absent-marker form, remains
        # V1. No source, attempt or authority is manufactured during parsing.
        old = legacy.to_dict()
        assert parse_exchange_reconciliation_identity_v1(old) == legacy
        old.pop("contract_id")
        assert parse_exchange_reconciliation_identity_v1(old) == legacy
        context = host.owner.execution_plan_context_v1(rid, envelope)
        raw = host.owner.begin_execution_submit_v2(
            rid, envelope, context, _permit(envelope)
        ).to_dict()
        if fault == "missing_version":
            del raw["contract_id"]
        elif fault == "unknown_version":
            raw["contract_id"] = "UNKNOWN"
        elif fault == "missing_field":
            del raw["canonical_intent_digest"]
        elif fault == "legacy_field":
            raw["local_durable_state_version"] = raw.pop("budget_submit_sequence")
        else:
            raw["authority"] = "unowned"
        with pytest.raises(ValueError, match="CONTRACT_OR_SHAPE_INVALID"):
            parse_exchange_reconciliation_identity_v1(raw)
    finally:
        host.close()


def test_actual_wrappers_create_identity_from_original_context_without_legacy_fields(
    tmp_path, monkeypatch
):
    import json
    from tests.ops.test_prepost_original_budget_context_v1 import execute
    from src.ops.full_core_live_path_composition_root_v1 import (
        current_productive_one_shot_fresh_envelope_permit_mint_durable_consume_and_post_join_v1 as lower,
    )
    from src.ops.governed_productive_account_equity_authority_producer_v1 import (
        current_productive_actual_venue_post_with_fresh_envelope_bound_single_use_permit_v1 as caller,
    )

    host, rid, legacy, envelope, intent, plan = seed_with_origin(tmp_path, monkeypatch)
    context = host.owner.execution_plan_context_v1(rid, envelope)
    calls = []

    class Opener:
        def open(self, *_args, **_kwargs):
            link = host.owner.execution_links_v1()[rid]
            identity = parse_exchange_reconciliation_identity_v1(link["identity"])
            assert type(identity) is PortfolioExecutionReconciliationIdentityV2
            assert identity.send_authority_ref == lower.POST_OWNER_GO
            assert identity.canonical_intent_digest == intent.semantic_digest
            assert identity.plan_origin_digest == context.plan_origin_digest
            consume = json.loads(
                (tmp_path / "send/full_core_external_effect_permit_consume_v1.json").read_text()
            )
            assert consume["durable_state"] == "SENT_INITIATED"
            assert consume["execution_identity"] == identity.to_dict()
            assert consume["execution_identity_digest"] == identity.identity_digest()
            assert consume["permit_id"] == identity.send_permit_id
            calls.append(identity)
            raise TimeoutError("Synthetic uncertainty without a socket")

    args = dict(
        envelope=envelope,
        portfolio_budget_owner=host.owner,
        portfolio_reservation_id=rid,
        execution_plan_context=context,
    )
    try:
        result = execute(args, tmp_path, opener=Opener())
        assert len(calls) == 1
        assert result.post_outcome == "UNKNOWN_EXTERNAL_EFFECT_POSSIBLE"
        assert result.replay_attempt_blocked == "true"
        assert host.owner.active_sum_v1() > 0
        version = host.owner._store.sequence
        with pytest.raises(caller.CurrentProductiveActualVenuePostError, match="REPLAY_OR_UNBOUND"):
            execute(args, tmp_path, port=object())
        assert host.owner._store.sequence == version
        assert len(calls) == 1
    finally:
        host.close()


@pytest.mark.parametrize("short", [False, True])
def test_native_n1_s5_s6_reference_reopens_original_owner_then_reaches_send_and_recovery(
    tmp_path, monkeypatch, short
):
    from datetime import datetime, timezone
    from pathlib import Path
    from tests.ops._wp03_supervisor_golden_harness_v1 import _run_layered_entry_supervisor_v1
    from tests.ops.test_n1_original_plan_origin_v1 import Owner, n1
    from tests.ops.test_portfolio_budget_host_v1 import _fetch
    from tests.ops.test_portfolio_capital_reservation_budget_contract_v1 import (
        _obs,
        _p01,
        _eligibility,
        produce_current_productive_29p_risk_capital_v1,
    )
    from src.ops.portfolio_capital_reservation_budget_v1.host_v1 import PortfolioBudgetHostV1
    from src.ops.single_selected_future_runtime_binding_v1.models_v1 import BoundInstrumentV1
    from tests.ops.test_prepost_original_budget_context_v1 import execute
    from tests.ops.test_portfolio_execution_recovery_v1 import ReadPort

    original_context = Owner.execution_plan_context_v1
    original_plan = n1.try_bind_current_productive_venue_plan_v1
    captured, produced = [], []

    def context(owner, rid, envelope):
        value = original_context(owner, rid, envelope)
        captured.append((owner, rid, envelope, value, owner.risk_snapshot_v1()["state"]))
        return value

    def plan(**kwargs):
        result = original_plan(**kwargs)
        if result[2] is not None:
            produced.append((kwargs["replay"].intermediate.canonical_order_intent, result[2]))
        return result

    with monkeypatch.context() as patch:
        patch.setattr(Owner, "execution_plan_context_v1", context)
        patch.setattr(n1, "try_bind_current_productive_venue_plan_v1", plan)
        supervisor = _run_layered_entry_supervisor_v1(tmp_path / "native", short=short)
    assert supervisor.ok and len(captured) == len(produced) == 1
    closed, rid, envelope, reference, snapshot = captured[0]
    record = supervisor.policy_result.orchestrator_result.cycle_records[-1]
    assert record.execution_plan_context is reference
    assert record.portfolio_reservation_id == rid
    assert record.final_order_envelope is envelope
    assert supervisor.trace.post_count == 0
    assert closed.execution_links_v1()[rid]["identity"] is None
    with pytest.raises(ValueError, match="OWNER_FENCED"):
        closed.inspect_execution_plan_context_v1(rid, envelope, reference)

    root = Path(reference.root).parent
    account = snapshot["account_identity"]
    bindings = {
        lane: BoundInstrumentV1(**row["bound"]) for lane, row in snapshot["lane_bindings"].items()
    }
    instant = datetime.now(timezone.utc).replace(microsecond=0)
    epoch = instant.isoformat().replace("+00:00", "Z")
    # A NEW original capital-producer output from explicit fresh synthetic
    # facts; never alter persisted times or turn a closed handle into authority.
    scope = dict(
        bound_account_identity=account,
        **{
            key: snapshot["capital_scope"][key] for key in ("bound_venue_identity", "bound_td_mode")
        },
    )
    fresh = produce_current_productive_29p_risk_capital_v1(
        observation=replace(_obs(value="1000.00", epoch=epoch), **scope),
        p01=replace(_p01(epoch), **scope),
        eligibility=replace(_eligibility(epoch), **scope),
    )
    assert fresh.produced == "true", fresh.reason_codes
    host = PortfolioBudgetHostV1(
        root=root,
        private_rest_fetch=_fetch(uid=account),
        repository_sha="synthetic-native-continuation",
        session_id="native-continuation",
        expected_account_identity=account,
        clock=lambda: instant.timestamp(),
    )
    identity = None
    try:
        recovery = host.observe_v1(bindings)
        assert host.owner.budget_state_v1().recovery_required
        with pytest.raises(ValueError, match="OWNER_FENCED"):
            host.owner.inspect_execution_plan_context_v1(rid, envelope, reference)
        recovery.recover_v1(host.owner, fresh)
        assert host.owner.budget_state_v1().admitted
        args = dict(
            envelope=envelope,
            portfolio_budget_owner=host.owner,
            portfolio_reservation_id=rid,
            execution_plan_context=reference,
        )

        class Opener:
            def open(self, *_args, **_kwargs):
                nonlocal identity
                identity = parse_exchange_reconciliation_identity_v1(
                    host.owner.execution_links_v1()[rid]["identity"]
                )
                intent, venue_plan = produced[0]
                assert identity.canonical_intent_digest == intent.semantic_digest
                assert identity.native_id == venue_plan.instrument_id
                assert identity.selected_side.upper() == ("SHORT" if short else "LONG")
                raise TimeoutError("Synthetic socket-free native continuation")

        result = execute(args, tmp_path / "continuation", opener=Opener())
        assert result.post_outcome == "UNKNOWN_EXTERNAL_EFFECT_POSSIBLE"
        assert identity is not None and host.owner.active_sum_v1() > 0
    finally:
        host.close()
    reopened = PortfolioBudgetHostV1(
        root=root,
        private_rest_fetch=_fetch(uid=account),
        repository_sha="synthetic-native-reconcile",
        session_id="native-reconcile",
        expected_account_identity=account,
        clock=lambda: instant.timestamp(),
        reconciliation_transport=ReadPort(identity, state="canceled", filled="0"),
    )
    try:
        observed = reopened.observe_v1(bindings)
        assert observed.execution_reconciliation[rid]["matched"]
        assert observed.execution_reconciliation[rid]["reservation_released"]
        assert reopened.owner.execution_links_v1()[rid]["identity"] == identity.to_dict()
        assert reopened.owner.active_sum_v1() == 0
    finally:
        reopened.close()
