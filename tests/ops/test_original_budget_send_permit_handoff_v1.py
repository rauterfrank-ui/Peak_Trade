"""Actual permit lineage stays separate from the original reconciliation identity."""

from dataclasses import replace
import json
import socket

import pytest

from src.ops.full_core_live_path_composition_root_v1 import (
    envelope_bound_external_effect_send_seam_v1 as seam,
)
from src.ops.full_core_live_path_composition_root_v1.external_effect_permit_v1 import (
    issue_external_effect_permit_v1,
)
from src.ops.portfolio_capital_reservation_budget_v1.contract_v1 import (
    PortfolioCapitalReservationBudgetOwnerV1 as Owner,
)
from src.ops.single_selected_future_runtime_binding_v1.models_v1 import BoundInstrumentV1
from tests.ops.test_full_core_current_productive_envelope_bound_single_use_external_effect_send_seam_v1 import (
    _handle,
    _permit,
)
from tests.ops.test_portfolio_execution_recovery_v1 import seed


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

    def forbidden(*_args, **_kwargs):
        raise AssertionError("Synthetic permit lineage proof must not open a socket")

    monkeypatch.setattr(socket.socket, "connect", forbidden)
    monkeypatch.setattr(socket, "create_connection", forbidden)
    yield
    reset_current_productive_pre_external_shared_test_process_state_v1()


def permit_payload(permit):
    return {"permit_id": permit.permit_id, **permit.to_canonical_payload_v1()}


def cold_owner(host):
    snapshot = host.owner.risk_snapshot_v1()["state"]
    root = host.owner.durable_scope_identity_v1()["root"]
    host.close()
    return Owner(
        durable_root=root,
        durable_account_identity=snapshot["account_identity"],
        durable_mode="recover",
        durable_lane_bindings={
            lane: BoundInstrumentV1(**row["bound"])
            for lane, row in snapshot["lane_bindings"].items()
        },
    )


def test_actual_send_seam_preserves_exact_separate_permit_before_consume_and_cold_read(
    tmp_path, monkeypatch
):
    host, rid, identity, envelope = seed(tmp_path)
    permit = _permit(envelope)
    assert identity.owner_go != permit.authority_ref
    calls = []
    persist = seam.persist_external_effect_durable_consume_v1

    def consume(**kwargs):
        link = host.owner.execution_links_v1()[rid]
        assert link["phase"] == "SUBMIT_MAY_HAVE_OCCURRED"
        assert link["identity"] == identity.to_dict()
        assert link["external_effect_permit"] == permit_payload(permit)
        assert kwargs["permit"] is permit
        calls.append("consume")
        return persist(**kwargs)

    class Transport:
        def post_trade_order(self, **kwargs):
            record = json.loads(
                (tmp_path / "send/full_core_external_effect_permit_consume_v1.json").read_text()
            )
            assert record["durable_state"] == "SENT_INITIATED"
            assert record["permit_id"] == permit.permit_id == kwargs["permit_id"]
            calls.append("transport")
            raise TimeoutError("Synthetic uncertainty")

    monkeypatch.setattr(seam, "persist_external_effect_durable_consume_v1", consume)
    args = dict(
        envelope=envelope,
        permit=permit,
        store_root=tmp_path / "send",
        transport=Transport(),
        handle=_handle(),
        portfolio_budget_owner=host.owner,
        portfolio_reservation_id=rid,
        execution_identity=identity,
    )
    try:
        with pytest.raises(seam.FullCoreEnvelopeBoundSendSeamError, match="UNKNOWN_OUTCOME"):
            seam.attempt_envelope_bound_external_effect_send_v1(**args)
        assert calls == ["consume", "transport"]
        with pytest.raises(seam.FullCoreEnvelopeBoundSendSeamError, match="CONSUMED_PERMIT"):
            seam.attempt_envelope_bound_external_effect_send_v1(**args)
        saved = host.owner.execution_links_v1()[rid]
        held = host.owner.active_sum_v1()
        restored = cold_owner(host)
        try:
            assert restored.execution_links_v1()[rid] == saved
            assert restored.active_sum_v1() == held > 0
            assert restored.budget_state_v1().recovery_required
            with pytest.raises(ValueError, match="EXECUTION_SUBMIT_OWNER_FENCED"):
                restored.inspect_execution_submit_context_v1(rid, envelope, identity)
        finally:
            restored.close()
    finally:
        host.close()


def test_actual_wrappers_supply_their_own_permit_without_relabelling_identity(tmp_path):
    from tests.ops.test_prepost_original_budget_context_v1 import execute
    from src.ops.full_core_live_path_composition_root_v1 import (
        current_productive_one_shot_fresh_envelope_permit_mint_durable_consume_and_post_join_v1 as lower,
    )

    host, rid, identity, envelope = seed(tmp_path)
    calls = []

    class Opener:
        def open(self, *_args, **_kwargs):
            link = host.owner.execution_links_v1()[rid]
            expected = issue_external_effect_permit_v1(envelope, authority_ref=lower.POST_OWNER_GO)
            assert link["external_effect_permit"] == permit_payload(expected)
            assert link["identity"] == identity.to_dict()
            assert identity.owner_go != link["external_effect_permit"]["authority_ref"]
            calls.append("opaque-fake-http")
            raise TimeoutError("Synthetic uncertainty without a socket")

    try:
        result = execute(
            dict(
                envelope=envelope,
                portfolio_budget_owner=host.owner,
                portfolio_reservation_id=rid,
                execution_identity=identity,
            ),
            tmp_path,
            opener=Opener(),
        )
        assert calls == ["opaque-fake-http"]
        assert result.post_outcome == "UNKNOWN_EXTERNAL_EFFECT_POSSIBLE"
        assert result.replay_attempt_blocked == "true"
        assert host.owner.active_sum_v1() > 0
    finally:
        host.close()


def test_crash_between_budget_and_permit_barriers_retains_lineage_without_consumption(
    tmp_path, monkeypatch
):
    from src.ops.full_core_live_path_composition_root_v1.external_effect_permit_durable_consume_v1 import (
        load_external_effect_durable_consume_v1,
    )

    host, rid, identity, envelope = seed(tmp_path)
    permit = _permit(envelope)

    def interrupted(**_kwargs):
        raise OSError("Synthetic interruption between original barriers")

    monkeypatch.setattr(seam, "persist_external_effect_durable_consume_v1", interrupted)
    try:
        with pytest.raises(OSError, match="between original barriers"):
            seam.attempt_envelope_bound_external_effect_send_v1(
                envelope=envelope,
                permit=permit,
                store_root=tmp_path / "send",
                transport=object(),
                handle=_handle(),
                portfolio_budget_owner=host.owner,
                portfolio_reservation_id=rid,
                execution_identity=identity,
            )
        assert not load_external_effect_durable_consume_v1(store_root=tmp_path / "send")[
            "durable_consumed"
        ]
        restored = cold_owner(host)
        try:
            link = restored.execution_links_v1()[rid]
            assert link["external_effect_permit"] == permit_payload(permit)
            assert link["identity"] == identity.to_dict()
            assert link["phase"] == "SUBMIT_MAY_HAVE_OCCURRED"
            assert restored.active_sum_v1() > 0
            with pytest.raises(ValueError, match="EXECUTION_SUBMIT_OWNER_FENCED"):
                restored.mark_execution_submit_boundary_v1(
                    rid, identity, external_effect_permit=permit
                )
        finally:
            restored.close()
    finally:
        host.close()


@pytest.mark.parametrize("fault", ["wrong-envelope", "digest", "authority", "type"])
def test_wrong_permit_cannot_advance_original_budget_or_lose_hold(tmp_path, fault):
    from src.ops.full_core_live_path_composition_root_v1.external_effect_permit_v1 import (
        FullCoreExternalEffectPermitError,
    )
    from tests.ops.test_prepost_original_budget_context_v1 import rebuild

    host, rid, identity, envelope = seed(tmp_path)
    permit = _permit(envelope)
    if fault == "wrong-envelope":
        permit = _permit(rebuild(envelope, provenance_ref="different-original-plan"))
    elif fault == "digest":
        permit = replace(permit, envelope_digest="f" * 64)
    elif fault == "authority":
        permit = replace(permit, authority_ref="unbound-replacement")
    else:
        permit = object()
    try:
        before = host.owner.risk_snapshot_v1()
        with pytest.raises((ValueError, FullCoreExternalEffectPermitError)):
            host.owner.mark_execution_submit_boundary_v1(
                rid, identity, external_effect_permit=permit
            )
        assert host.owner.risk_snapshot_v1() == before
        assert host.owner.active_sum_v1() > 0
    finally:
        host.close()


@pytest.mark.parametrize(
    "fault", ["missing-field", "null", "authority", "wrong-envelope", "plan-phase"]
)
def test_cold_restore_checks_present_permit_without_filling_missing_fields(tmp_path, fault):
    host, rid, identity, envelope = seed(tmp_path)
    try:
        host.owner.mark_execution_submit_boundary_v1(
            rid, identity, external_effect_permit=_permit(envelope)
        )
        payload = host.owner.risk_snapshot_v1()["state"]
        link = payload["execution_links"][rid]
        if fault == "missing-field":
            del link["external_effect_permit"]["retry_allowed"]
        elif fault == "null":
            link["external_effect_permit"] = None
        elif fault == "authority":
            link["external_effect_permit"]["authority_ref"] = "unbound-replacement"
        elif fault == "wrong-envelope":
            link["external_effect_permit"]["envelope_id"] = "foreign-envelope"
        else:
            link["phase"] = "PLAN_BOUND"
            link["identity"] = None
        # Synthetic corruption with a valid store digest isolates semantic
        # restore from the independent history-integrity gate.
        host.owner._store.save(payload)
        with pytest.raises(ValueError, match="DURABLE_BUDGET_SEMANTIC_RESTORE_UNPROVEN"):
            cold_owner(host)
    finally:
        host.close()


def test_legacy_submit_link_remains_without_invented_send_permit(tmp_path):
    host, rid, identity, envelope = seed(tmp_path)
    try:
        host.owner.mark_execution_submit_boundary_v1(rid, identity)
        restored = cold_owner(host)
        try:
            link = restored.execution_links_v1()[rid]
            assert "external_effect_permit" not in link
            assert link["identity"] == identity.to_dict()
            assert restored.active_sum_v1() > 0
            assert restored.budget_state_v1().recovery_required
        finally:
            restored.close()
    finally:
        host.close()


@pytest.mark.parametrize("filled", [False, True])
def test_original_host_reconciliation_consumes_identity_and_preserves_separate_permit(
    tmp_path, filled
):
    from tests.ops.test_portfolio_execution_recovery_v1 import ReadPort, NOW, _bound
    from tests.ops.test_portfolio_budget_host_v1 import _host, _fetch

    host, rid, identity, envelope = seed(tmp_path)
    permit = _permit(envelope)
    try:
        host.owner.mark_execution_submit_boundary_v1(rid, identity, external_effect_permit=permit)
        held = host.owner.active_sum_v1()
    finally:
        host.close()
    positions = (
        ({"instId": identity.native_id, "posSide": "net", "pos": identity.final_quantity},)
        if filled
        else ()
    )
    restored = _host(
        tmp_path,
        _fetch(uid=identity.account_identity, positions=positions),
        clock=lambda: NOW,
        expected_account=identity.account_identity,
    )
    restored.reconciliation_transport = ReadPort(
        identity,
        state="filled" if filled else "canceled",
        filled=identity.final_quantity if filled else "0",
    )
    try:
        context = restored.observe_v1({"LANE_1": _bound()})
        proof = context.execution_reconciliation[rid]
        assert proof["matched"]
        assert proof["reservation_released"] is not filled
        assert restored.owner.active_sum_v1() == (held if filled else 0)
        link = restored.owner.execution_links_v1()[rid]
        assert link["external_effect_permit"] == permit_payload(permit)
        assert link["identity"] == identity.to_dict()
        assert restored.owner.budget_state_v1().recovery_required
    finally:
        restored.close()
