"""Account-aware startup against the real selection/reconciliation seam, offline."""

from contextlib import nullcontext
from dataclasses import replace
from datetime import datetime, timezone
from decimal import Decimal
import json
from types import SimpleNamespace
from unittest.mock import patch
from urllib.parse import parse_qs, urlsplit

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


@pytest.mark.parametrize("futures_position", [False, True])
def test_k1_inventory_guard_at_original_startup_binding(state, futures_position):
    from src.ops.full_core_live_path_composition_root_v1 import (
        productive_read_only_get_transport_v1 as wire,
    )
    from src.ops.okx_eea_private_account_state_runtime_v1.k1_source_v1 import (
        open_k1_account_observation_source_v1,
    )
    from tests.ops.test_k1_account_observation_source_v1 import (
        InjectedOpener,
        _FakeKeychainBackend,
    )

    account = "account-injected"
    position = {
        "instId": "BTC-USD_UM_XPERP-310404",
        "instType": "FUTURES",
        "posSide": "net",
        "pos": "1",
    }
    opener = InjectedOpener(account=account, positions=[position] if futures_position else [])
    with patch.object(wire, "build_opener", return_value=opener):
        with open_k1_account_observation_source_v1(
            expected_account_identity=account,
            session_id="n1-start",
            max_request_count=10,
            k1_lookup_backend=_FakeKeychainBackend(),
            account_inventory_guard=True,
        ) as source:
            if futures_position:
                before = tree_bytes(state[1])
                with pytest.raises(
                    ValueError, match="ACCOUNT_PRODUCTS_OUTSIDE_CURRENT_SWAP_CONSUMER"
                ):
                    call(state, private_rest_fetch=source)
                assert tree_bytes(state[1]) == before
            else:
                result = call(state, private_rest_fetch=source)
                assert result.handoff.selection_id == state[0]["selection"].selection_id
                assert result.observation.pending_source is None
    assert any(url.endswith("/api/v5/account/positions") for url in opener.requests)


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


@pytest.mark.parametrize(
    "product,public_fault",
    [
        ("FUTURES", None),
        ("SWAP", None),
        (None, None),
        ("FUTURES", "empty-mark"),
        ("FUTURES", "foreign-mark"),
        ("FUTURES", "invalid-mark-price"),
        ("FUTURES", "invalid-mark-time"),
        ("FUTURES", "wrong-ticker-product"),
        ("FUTURES", "wp02"),
        ("FUTURES", "wp02-gap"),
        ("FUTURES", "wp02-future"),
        ("FUTURES", "wp02-universe-mismatch"),
        ("FUTURES", "wp02-foreign-pretrade-account"),
    ],
)
def test_standing_xperp_startup_preserves_persisted_selection_and_inventory(
    tmp_path, product, public_fault
):
    from src.ops.current_mf_n5_durable_lane_assignment_persistence_v1.persistence_v1 import (
        recover_durable_lane_assignment_v1,
    )
    from src.ops.full_core_live_path_composition_root_v1 import (
        productive_read_only_get_transport_v1 as wire,
    )
    from src.ops.n1_standing_pre_external_runtime_supervisor_v1 import supervisor_v1 as supervisor
    from src.ops.n1_standing_pre_external_runtime_supervisor_v1.constants_v1 import (
        TRANSPORT_SCOPE_SCOPED_READONLY_GET,
    )
    from src.ops.n1_whole_system_hard_facts_integration_wp_v1.public_runtime_economic_md_adapter_v1 import (
        persist_bound_ranking_mark_window_v1,
    )
    from src.ops.okx_eea_private_account_state_runtime_v1.durable_store_v1 import (
        default_private_store_paths_v1,
        load_all_private_state_v1,
    )
    from src.ops.okx_eea_private_account_state_runtime_v1.k1_source_v1 import (
        open_k1_account_observation_source_v1,
    )
    from src.ops.portfolio_capital_reservation_budget_v1.contract_v1 import (
        PortfolioCapitalReservationBudgetOwnerV1,
    )
    from src.ops.peak_trade_public_market_data_runtime_v1.historical_query_v1 import (
        query_historical_facts_v1,
    )
    from src.ops.peak_trade_public_market_data_runtime_v1.rest_recovery_v1 import (
        PublicRestRecoveryError,
        public_instrument_ref_for_binding_v1,
    )
    from src.ops.productive_futures_ranking_producer_v1.persistence_v1 import (
        load_and_validate_ranking_snapshot_v1,
    )
    from src.ops.productive_reconciliation_runtime_binding_v1.models_v1 import PositionTruthV1
    from src.risk_layer.kill_switch.persistence import StatePersistence
    from src.risk_layer.kill_switch.state import KillSwitchState
    from tests.ops.test_current_usdc_xperp_financial_admission_v1 import instrument
    from tests.ops.test_full_core_current_productive_29p_cap24_bound_instrument_provenance_handoff_v1 import (
        _build_fresh_chain,
        _materialize_productivity_root,
    )
    from tests.ops.test_k1_account_observation_source_v1 import InjectedOpener, _FakeKeychainBackend
    from tests.ops.test_n1_standing_pre_external_runtime_supervisor_v1 import _continuous_auth
    from tests.ops.test_prepost_original_budget_context_v1 import AccountPort
    from tests.ops.test_single_selected_future_runtime_binding_v1 import _marks, _payload

    account = "account-injected"
    native = "ETH-USD_UM_XPERP-310404"
    row = instrument(settlement="USD")
    row.update(instId=native, uly="ETH-USD", instFamily="ETH-USD_UM_XPERP", ctValCcy="ETH")
    chain = _build_fresh_chain(tmp_path / "source", instrument_rows=[row])
    prod = _materialize_productivity_root(tmp_path, chain)
    state = chain, prod
    initial = component.acquire_current_productive_29p_cap24_bound_instrument_provenance_handoff_v1(
        **kwargs(state), observed_portfolio=observed(state)
    )
    bound = initial.bound_instrument
    assert bound.venue_native_id == native
    assert bound.instrument_id == "okx_eea:linear_dated_future:ETH:USD:USD:eth-usd_um_xperp-310404"
    recon = prod / "runtime_state/recon"
    if product == "FUTURES":
        snapshot = observed(
            state,
            positions=(
                PositionTruthV1.from_signed(
                    instrument_id=bound.instrument_id, signed_quantity="-2"
                ),
            ),
        )
        (recon / PORTFOLIO_STATE_FILENAME).write_text(json.dumps(snapshot.to_dict()))
    before = tree_bytes(prod)
    gate = tmp_path / "filegate.json"
    StatePersistence(str(gate)).save(
        KillSwitchState.KILLED, killed_at=datetime.now(timezone.utc), trigger_reason="test"
    )
    gate_before = gate.read_bytes()
    event_time = str(int(datetime.now(timezone.utc).timestamp() * 1000))
    exercise_wp02 = public_fault is not None and public_fault.startswith("wp02")
    universe_row = dict(row, settleCcy="USDC") if public_fault == "wp02-universe-mismatch" else row
    config = supervisor.StandingSupervisorConfigV1(
        public_store_root=tmp_path / "public",
        private_store_root=tmp_path / "private",
        lane_state_root=tmp_path / "lane",
        evidence_root=tmp_path / "standing",
        cap24_productivity_root=prod,
        expected_account_identity=account,
        venue_native_id=native,
        canonical_instrument_id=bound.instrument_id,
        transport_scope=TRANSPORT_SCOPE_SCOPED_READONLY_GET,
        kill_switch_state_path=str(gate),
        simulate_restart_before_continuous=True,
        wp02_universe_source_payload=_payload([universe_row]),
        wp02_universe_mark_price_payload=_marks(native),
        wp02_universe_source_event_time=event_time,
    )
    owner_root = supervisor.budget_owner_root_for_config_v1(config) / "owner"
    seed = PortfolioCapitalReservationBudgetOwnerV1(
        durable_root=owner_root,
        durable_account_identity=account,
        durable_mode="create",
        durable_lane_bindings={"LANE_1": bound},
    )
    pretrade = AccountPort(
        {"envelope": SimpleNamespace(instrument_id=native), "portfolio_budget_owner": seed},
        uid="foreign" if public_fault == "wp02-foreign-pretrade-account" else None,
    )
    seed.close()
    opener = InjectedOpener(
        account=account,
        positions=[{"instId": native, "instType": "FUTURES", "posSide": "net", "pos": "-2"}]
        if product == "FUTURES"
        else [],
    )
    legacy_requests = []
    reconcile = PortfolioBudgetHostV1.reconcile_standing_startup_observation_v1
    received = []
    public_requests = []
    mark_path = "/api/v5/public/mark-price"
    ticker_path = "/api/v5/market/ticker"
    history_path = "/api/v5/market/history-mark-price-candles"
    mark_query = {"instType": "FUTURES", "instId": native}
    ticker_query = {"instId": native}
    history_query = {"instId": native, "bar": "1m", "limit": "100"}
    current_minute = int(event_time) // 60_000 * 60_000
    history = [
        [str(current_minute - offset * 60_000), "100", "200", "99", str(100 + offset), "1"]
        for offset in range(1, 63)
    ]
    history.insert(0, [str(current_minute), "100", "200", "99", "999", "0"])
    if public_fault == "wp02-gap":
        history.pop(20)
    if public_fault == "wp02-future":
        for candle in history:
            candle[0] = str(int(candle[0]) + 86_400_000)

    def receive(host, bindings, observation):
        reconcile(host, bindings, observation)
        assert bindings == {"LANE_1": bound}
        assert host.owner.budget_state_v1().recovery_required
        received.append((host.fetch, observation))

    def public_fetch(path, query):
        public_requests.append((path, query))
        assert product == "FUTURES" and len(received) == 1
        if path == history_path:
            assert exercise_wp02 and query == history_query
            return _payload(history)
        row = {"instType": "FUTURES", "instId": native, "ts": event_time}
        if path == mark_path:
            assert query == mark_query
            row["markPx"] = "100.5"
            if public_fault == "empty-mark":
                return {"code": "0", "data": []}
            if public_fault == "foreign-mark":
                row["instId"] = "SOL-USD_UM_XPERP-310404"
            if public_fault == "invalid-mark-price":
                row["markPx"] = "NaN"
            if public_fault == "invalid-mark-time":
                row["ts"] = "0"
        else:
            assert path == ticker_path and query == ticker_query
            row["last"] = "100.2"
            row.update(bidPx="100.1", askPx="100.3")
            if public_fault == "wrong-ticker-product":
                row["instType"] = "SWAP"
        return {"code": "0", "data": [row]}

    def stop_after_supply(context):
        assert context.venue_native_id == native
        assert context.canonical_instrument_id == bound.instrument_id
        raise ValueError("PUBLIC_SUPPLY_COMPLETE")

    def stop_after_wp02(**kwargs):
        assert kwargs["bound"] == bound
        raise ValueError("PRETRADE_COMPLETE")

    with (
        patch.object(wire, "build_opener", return_value=opener),
        patch.object(supervisor, "canonical_kill_switch_state_path", return_value=str(gate)),
        patch.object(PortfolioBudgetHostV1, "reconcile_standing_startup_observation_v1", receive),
        patch.object(
            supervisor,
            "run_policy_governed_persistent_natural_enter_live_c1_continuous_run_v1",
            stop_after_wp02,
        ),
    ):
        source_context = (
            open_k1_account_observation_source_v1(
                expected_account_identity=account,
                session_id=config.evidence_root.name,
                max_request_count=30,
                k1_lookup_backend=_FakeKeychainBackend(),
                account_inventory_guard=True,
                inventory_inst_type=product,
            )
            if product is not None
            else nullcontext(_fetch(uid=account, calls=legacy_requests))
        )
        with source_context as source:
            if product != "FUTURES":
                expected = "HOST_BUDGET_BOUND_PRODUCT_SCOPE_UNPROVEN"
            elif public_fault == "wp02":
                expected = "PRETRADE_COMPLETE"
            elif public_fault == "wp02-gap":
                expected = "WP02_PUBLIC_PT1M_FAIL_CLOSED:PUBLIC_PT1M_WINDOW_UNPROVEN:MISSING_MARK_BAR_NO_IMPLICIT_FILL"
            elif public_fault == "wp02-future":
                expected = "WP02_PUBLIC_PT1M_FAIL_CLOSED:PUBLIC_PT1M_INTERVAL_UNPROVEN"
            elif public_fault == "wp02-universe-mismatch":
                expected = "PUBLIC_PT1M_BOUND_WINDOW_UNIVERSE_MISMATCH"
            elif public_fault == "wp02-foreign-pretrade-account":
                expected = "N1_PRETRADE_ACCOUNT_BINDING_UNPROVEN:.*LIVE_ACCOUNT_BOUND_DUPLICATE_AMBIGUOUS_ACCOUNT"
            elif public_fault:
                source_kind = "TICKER" if public_fault == "wrong-ticker-product" else "MARK"
                expected = f"UNIFIED_RECOVERY_FAIL_CLOSED:PUBLIC_{source_kind}_BOOTSTRAP_UNPROVEN"
            else:
                expected = "PUBLIC_SUPPLY_COMPLETE"
            with pytest.raises(ValueError, match=expected):
                supervisor.run_n1_standing_pre_external_supervisor_v1(
                    config=replace(config, require_pretrade_collection=exercise_wp02),
                    origin_main_sha=chain["repository_sha"],
                    bound=bound,
                    authorization=_continuous_auth(native_id=native, max_cycles=1),
                    observation_source=None,
                    g17_producers={},
                    f1_m9_cycle_evaluator=None,
                    public_rest_fetch=public_fetch,
                    private_rest_fetch=source,
                    pretrade_transport=pretrade,
                    public_ws_messages=[
                        {
                            "arg": {"channel": "mark-price", "instId": native},
                            "data": [{"instId": native, "markPx": "100.7", "ts": event_time}],
                        }
                    ],
                    wp02_hook=None if exercise_wp02 else stop_after_supply,
                    skip_owner_go_validation=True,
                )
    reached_pretrade = public_fault in {"wp02", "wp02-foreign-pretrade-account"}
    assert config.lane_state_root.exists() is (
        reached_pretrade or public_fault == "wp02-universe-mismatch"
    )
    pretrade_endpoints = [endpoint for endpoint, _, _ in pretrade.requests]
    if reached_pretrade:
        assert f"/api/v5/public/instruments?instType=FUTURES&instId={native}" in pretrade_endpoints
        assert (
            "/api/v5/public/instruments?instType=SWAP&instId=USDC-USDT-SWAP" in pretrade_endpoints
        )
        assert all(bound.instrument_id not in endpoint for endpoint in pretrade_endpoints)
    else:
        assert not pretrade_endpoints
    assert gate.read_bytes() == gate_before
    assert not (config.evidence_root / "bounded_continuous_run_owner_go_consume_v1.json").exists()
    private_paths = default_private_store_paths_v1(config.private_store_root)
    if product == "FUTURES":
        assert len(received) == 1
        fetch, observation = received[0]
        assert observation.account_inventory_source is fetch
        assert observation.observed.source_id == "host-private-rest-futures"
        assert observation.observed.positions[0].signed_quantity == Decimal("-2")
        early_public_failure = public_fault and not exercise_wp02
        assert len(opener.requests) == (10 if early_public_failure else 30)
        queries = [urlsplit(url) for url in opener.requests]
        for request in queries:
            query = parse_qs(request.query)
            if request.path.endswith(("/orders-history", "/fills")):
                assert query == {"instType": ["FUTURES"]}
            else:
                assert "instType" not in query and "instId" not in query
        restored = load_persisted_portfolio_state(recon, require_present=True)
        assert restored.positions[0].instrument_id == bound.instrument_id
        assert restored.positions[0].signed_quantity == Decimal("-2")
        assert {
            path: value
            for path, value in before.items()
            if not path.startswith("runtime_state/recon")
        } == {
            path: value
            for path, value in tree_bytes(prod).items()
            if not path.startswith("runtime_state/recon")
        }
        assert public_requests[:1] == [(mark_path, mark_query)]
        if early_public_failure:
            assert len(public_requests) == (2 if public_fault == "wrong-ticker-product" else 1)
            assert not private_paths.normalized_state.exists()
            assert not config.public_store_root.exists()
        else:
            expected_requests = [(mark_path, mark_query), (ticker_path, ticker_query)] * 3
            if exercise_wp02:
                expected_requests.append((history_path, history_query))
            assert public_requests == expected_requests
            private_records = load_all_private_state_v1(private_paths)
            assert len(private_records) == 2
            assert all(record["trusted_boundary_established"] for record in private_records)
            (mark,) = query_historical_facts_v1(
                config.public_store_root, venue_native_id=native, fact_kind="MarkPriceFactV1"
            ).facts
            assert mark["fact_kind"] == "MarkPriceFactV1" and mark["mark_px"] == "100.7"
            assert mark["instrument"]["canonical_instrument_id"] == bound.instrument_id
            assert mark["instrument"]["instrument_type"] == "FUTURES"
            assert mark["instrument"]["settlement_asset"] == "USD"
            assert mark["timestamps"]["venue_event_time_ms"] == int(event_time)
            capture = datetime.fromisoformat(mark["timestamps"]["captured_at"])
            assert int(capture.timestamp() * 1000) >= int(event_time)
            candles = query_historical_facts_v1(
                config.public_store_root,
                venue_native_id=native,
                fact_kind="FinalizedPt1mMarkFactV1",
            ).facts
            if reached_pretrade:
                assert len(candles) == 61
                assert [fact["interval_start_ms"] for fact in candles] == list(
                    range(current_minute - 61 * 60_000, current_minute, 60_000)
                )
                assert all(fact["instrument"] == mark["instrument"] for fact in candles)
                assert all(fact["confirm"] == "1" for fact in candles)
                rank = load_and_validate_ranking_snapshot_v1(
                    config.lane_state_root / "wp02_runtime/ranking",
                    expected_repository_sha=chain["repository_sha"],
                )
                assert rank.ok and rank.snapshot.eligible_candidate_count == 1
                (candidate,) = rank.snapshot.ranked_candidates
                assert candidate.canonical_instrument_id == bound.instrument_id
                assert candidate.venue_native_id == native
                topology = recover_durable_lane_assignment_v1(
                    topology_state_root_base=config.lane_state_root / "topology",
                    recovery_mode="RESTART",
                    expected_universe_snapshot_id=rank.snapshot.universe_snapshot_id,
                    expected_ranking_snapshot_id=rank.snapshot.ranking_snapshot_id,
                    expected_ranking_integrity_digest=rank.snapshot.integrity_digest,
                )
                assert topology.occupied_instrument_ids == (bound.instrument_id,)

                public_before = tree_bytes(config.public_store_root)
                params = dict(
                    store_root=config.public_store_root,
                    fetch_json=public_fetch,
                    instrument_ref=public_instrument_ref_for_binding_v1(bound),
                    session_id="replay",
                )
                window = persist_bound_ranking_mark_window_v1(**params)
                assert len(window.fact_digests) == 61
                assert tree_bytes(config.public_store_root) == public_before
                history[1][4] = "202"
                with pytest.raises(
                    PublicRestRecoveryError, match="PUBLIC_PT1M_STORED_FACT_CONFLICT"
                ):
                    persist_bound_ranking_mark_window_v1(**params)
                assert tree_bytes(config.public_store_root) == public_before
            elif public_fault == "wp02-universe-mismatch":
                assert len(candles) == 61
                assert not list(
                    config.lane_state_root.rglob("productive_futures_ranking_snapshot_v1.json")
                )
            else:
                assert candles == ()
    else:
        assert received == []
        assert not opener.requests and not legacy_requests
        assert not public_requests and not private_paths.normalized_state.exists()
        assert tree_bytes(prod) == before
