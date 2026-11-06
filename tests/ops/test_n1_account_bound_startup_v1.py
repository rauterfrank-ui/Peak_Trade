"""Account-aware startup against the real selection/reconciliation seam, offline."""

from dataclasses import replace
from decimal import Decimal
import json
from types import SimpleNamespace
from unittest.mock import patch

import pytest

from src.ops.n1_standing_pre_external_runtime_supervisor_v1 import startup_binding_v1 as startup
from src.ops.portfolio_capital_reservation_budget_v1.host_v1 import PortfolioBudgetHostV1
from src.ops.productive_reconciliation_runtime_binding_v1.constants_v1 import (
    PORTFOLIO_STATE_FILENAME,
)
from src.ops.productive_reconciliation_runtime_binding_v1.persistence_v1 import (
    load_persisted_portfolio_state,
)
from tests.ops.test_observed_cap24_start_binding_v1 import (
    component,
    kwargs,
    observed,
    state,
    tree_bytes,
)
from tests.ops.test_portfolio_budget_host_v1 import _fetch


def call(state, **changes):
    epoch = component._binding_epoch_unix_v1(state[0]["binding_epoch"])
    values = dict(
        **kwargs(state),
        expected_account_identity="account-injected",
        session_id="n1-start",
        private_rest_fetch=_fetch(uid="account-injected"),
        clock=lambda: epoch,
    )
    values.update(changes)
    return startup.acquire_account_bound_n1_startup_v1(**values)


def test_flat_account_binding_uses_shared_collector_without_budget_store(state):
    with patch.object(
        PortfolioBudgetHostV1, "__init__", side_effect=AssertionError("second owner")
    ):
        result = call(state)
    assert result.observation.account == "account-injected"
    assert result.observation.observed.positions == ()
    assert result.handoff.selection_id == state[0]["selection"].selection_id
    assert not list(state[1].rglob("*.sqlite*"))


@pytest.mark.parametrize("qty", ["2", "-2"])
def test_private_open_position_is_retained_when_matched(state, qty):
    from src.ops.productive_reconciliation_runtime_binding_v1.models_v1 import PositionTruthV1

    chain, prod = state
    position = PositionTruthV1.from_signed(
        instrument_id=chain["instrument_id"], signed_quantity=qty
    )
    snapshot = observed(state, positions=(position,))
    recon = prod / "runtime_state/recon"
    (recon / PORTFOLIO_STATE_FILENAME).write_text(json.dumps(snapshot.to_dict()))
    before = tree_bytes(prod / "runtime_state/selection")
    result = call(
        state,
        private_rest_fetch=_fetch(
            uid="account-injected",
            positions=[{"instId": chain["venue_native_id"], "posSide": "net", "pos": qty}],
        ),
    )
    assert result.observation.observed.positions[0].signed_quantity == Decimal(qty)
    restored = load_persisted_portfolio_state(recon, require_present=True)
    assert restored.positions[0].signed_quantity == Decimal(qty)
    assert tree_bytes(prod / "runtime_state/selection") == before


@pytest.mark.parametrize(
    "fault,match",
    [
        ("missing_account", "ACCOUNT_IDENTITY_REQUIRED"),
        ("wrong_account", "PRIVATE_ACCOUNT_CHANGED"),
        ("missing_uid", "PRIVATE_ACCOUNT_UNPROVEN"),
        ("pending", "PENDING_ORDERS_UNRESOLVED"),
        ("stale", "PRIVATE_SNAPSHOT_STALE"),
        ("foreign", "POSITION_SCOPE_UNPROVEN"),
        ("bound_mismatch", "SELECTION_BINDING_MISMATCH"),
    ],
)
def test_bad_start_observation_never_reaches_binding(state, fault, match):
    values = {}
    if fault == "missing_account":
        values["expected_account_identity"] = ""
    elif fault == "wrong_account":
        values["private_rest_fetch"] = _fetch(uid="other")
    elif fault == "missing_uid":
        values["private_rest_fetch"] = _fetch(uid=None)
    elif fault == "pending":
        values["private_rest_fetch"] = _fetch(uid="account-injected", pending=True)
    elif fault == "stale":
        ts = component._binding_epoch_unix_v1(state[0]["binding_epoch"])
        ticks = iter([ts, ts + 6])
        values["clock"] = lambda: next(ticks)
    elif fault == "foreign":
        values["private_rest_fetch"] = _fetch(
            uid="account-injected", positions=[{"instId": "FOREIGN", "posSide": "net", "pos": "1"}]
        )
    else:
        selection = state[0]["selection"]
        values["expected_bound"] = SimpleNamespace(
            **{
                name: "wrong" if name == "instrument_id" else getattr(selection, name, "unused")
                for name in (
                    "instrument_id",
                    "venue_native_id",
                    "selection_id",
                    "ranking_snapshot_id",
                    "universe_snapshot_id",
                )
            }
        )
    before = tree_bytes(state[1])
    with patch.object(
        startup,
        "acquire_current_productive_29p_cap24_bound_instrument_provenance_handoff_v1",
        side_effect=AssertionError("binding invoked"),
    ):
        with pytest.raises(ValueError, match=match):
            call(state, **values)
    assert tree_bytes(state[1]) == before


def test_missing_legacy_handoff_observation_is_explicit_and_read_only(state):
    before = tree_bytes(state[1])
    with pytest.raises(
        component.CurrentProductive29PCap24ProvenanceHandoffError,
        match="OBSERVED_PORTFOLIO_REQUIRED",
    ):
        component.acquire_current_productive_29p_cap24_bound_instrument_provenance_handoff_v1(
            **kwargs(state)
        )
    assert tree_bytes(state[1]) == before


def test_selection_change_between_observation_and_binding_stops_before_gate(state):
    context = component.inspect_selection_v1(**kwargs(state))
    changed = replace(context, selection=replace(context.selection, integrity_digest="changed"))
    before = tree_bytes(state[1])
    with (
        patch.object(component, "inspect_selection_v1", return_value=changed),
        patch.object(
            component,
            "run_single_selected_future_runtime_binding_gate_v1",
            side_effect=AssertionError("gate invoked"),
        ),
    ):
        with pytest.raises(
            component.CurrentProductive29PCap24ProvenanceHandoffError,
            match="SELECTION_CHANGED_DURING_OBSERVATION",
        ):
            call(state)
    assert tree_bytes(state[1]) == before


def test_observation_stale_after_collection_stays_blocked(state):
    ts = component._binding_epoch_unix_v1(state[0]["binding_epoch"])
    ticks = iter([ts, ts + 1, ts + 10])
    with pytest.raises(
        component.CurrentProductive29PCap24ProvenanceHandoffError, match="CAP24_BIND_FAIL_CLOSED"
    ):
        call(state, clock=lambda: next(ticks))


def test_matching_existing_bound_is_checked_against_all_snapshot_identities(state):
    inspected = component.inspect_selection_v1(**kwargs(state))
    selection = inspected.selection
    bound = SimpleNamespace(
        instrument_id=selection.instrument_id,
        venue_native_id=selection.venue_native_id,
        selection_id=selection.selection_id,
        selection_integrity_digest=selection.integrity_digest,
        ranking_snapshot_id=inspected.ranking.ranking_snapshot_id,
        ranking_integrity_digest=inspected.ranking.integrity_digest,
        universe_snapshot_id=inspected.universe.snapshot_id,
    )
    assert call(state, expected_bound=bound).handoff.instrument_id == bound.instrument_id
    before = tree_bytes(state[1])
    bound.universe_snapshot_id = "foreign-universe"
    with pytest.raises(ValueError, match="SELECTION_BINDING_MISMATCH"):
        call(state, expected_bound=bound)
    assert tree_bytes(state[1]) == before


def test_supervisor_requires_account_bound_start_before_recovery(state, tmp_path):
    from src.ops.n1_standing_pre_external_runtime_supervisor_v1 import supervisor_v1 as supervisor
    from src.ops.n1_standing_pre_external_runtime_supervisor_v1.constants_v1 import (
        TRANSPORT_SCOPE_SCOPED_READONLY_GET,
    )
    from tests.ops.test_n1_standing_pre_external_runtime_supervisor_v1 import _continuous_auth
    from types import SimpleNamespace

    bound = call(state).handoff.bound_instrument
    config = supervisor.StandingSupervisorConfigV1(
        public_store_root=tmp_path / "public",
        private_store_root=tmp_path / "private",
        lane_state_root=tmp_path / "lane",
        evidence_root=tmp_path / "evidence",
        lock_root=tmp_path / "lock",
        transport_scope=TRANSPORT_SCOPE_SCOPED_READONLY_GET,
        cap24_productivity_root=state[1],
        expected_account_identity="account-injected",
        venue_native_id=bound.venue_native_id,
        canonical_instrument_id=bound.instrument_id,
    )
    sentinel = RuntimeError("startup-marker")
    with (
        patch.object(
            supervisor,
            "_run_unified_recovery_v1",
            side_effect=AssertionError("recovery before account binding"),
        ),
        patch.object(startup, "acquire_account_bound_n1_startup_v1", side_effect=sentinel) as start,
    ):
        with pytest.raises(RuntimeError, match="startup-marker"):
            supervisor.run_n1_standing_pre_external_supervisor_v1(
                config=config,
                origin_main_sha=kwargs(state)["repository_sha"],
                bound=bound,
                authorization=_continuous_auth(native_id=bound.venue_native_id, max_cycles=1),
                observation_source=None,
                g17_producers={},
                f1_m9_cycle_evaluator=None,
                public_rest_fetch=None,
                private_rest_fetch=_fetch(uid="account-injected"),
                skip_owner_go_validation=True,
            )
    assert start.call_args.kwargs["expected_bound"] is bound
    assert start.call_args.kwargs["expected_account_identity"] == "account-injected"
