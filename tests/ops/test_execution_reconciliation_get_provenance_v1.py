"""Original K1 signing and HTTP GET code with simulated Keychain and HTTP boundaries."""

from base64 import b64encode
from contextlib import closing, contextmanager
from dataclasses import asdict, replace
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from hashlib import sha256
from io import BytesIO
import hmac
import json
import os
from pathlib import Path
import plistlib
import shutil
import signal
import sqlite3
import stat
import subprocess
import sys
import time
from types import SimpleNamespace
from urllib.error import HTTPError
from urllib.parse import parse_qsl, urlencode, urlsplit
from urllib.request import BaseHandler, build_opener
from urllib.response import addinfourl

import pytest

from src.ops.execution_incident_diagnostics_v1 import (
    prepare_standing_diagnostics_launch_agent_v1,
    run_standing_execution_incident_diagnostics_v1,
)

from src.ops.execution_incident_safety_v1 import (
    AuthenticatedExecutionIncidentScopeV1,
    ExecutionIncidentHaltV1,
    ExecutionIncidentSafetyError,
    OfflineExecutionIncidentScopeV1,
    _apply_confirmed_execution_incident_v1,
    observe_authenticated_execution_incident_v1,
    observe_standing_execution_incident_v1,
    read_authenticated_execution_incident_origin_v1,
)
from src.ops.execution_reconciliation_get_provenance_v1 import ExecutionReconciliationSourceError
from src.ops import execution_reconciliation_proof_store_v1 as store
from src.ops.full_core_live_path_composition_root_v1 import (
    productive_read_only_get_transport_v1 as wire,
)
from src.ops.full_core_live_path_composition_root_v1.current_productive_governed_live_c1_get_only_fresh_pretrade_transport_bind_v1 import (
    open_governed_live_c1_get_only_fresh_pretrade_transport_v1,
)
from src.ops.full_core_live_path_composition_root_v1.full_core_exchange_reconciliation_v1 import (
    REASON_INCOMPLETE_PAGINATION,
    REASON_NEGATIVE_REMAINING,
    REASON_TRANSPORT_UNKNOWN,
)
from src.ops.portfolio_capital_reservation_budget_v1.execution_v1 import (
    read_persisted_execution_reconciliation_v1,
)
from src.ops.portfolio_capital_reservation_budget_v1.host_v1 import PortfolioBudgetHostV1
from src.ops.okx_eea_private_account_state_runtime_v1.k1_source_v1 import (
    K1AccountObservationSourceV1,
)
from src.risk_layer.kill_switch.persistence import StatePersistence
from src.risk_layer.kill_switch.state import KillSwitchState
from tests.ops.test_current_productive_governed_live_c1_get_only_fresh_pretrade_transport_bind_v1 import (
    FAKE_OPAQUE,
    _FakeKeychainBackend,
)
from tests.ops.test_full_core_current_productive_envelope_bound_single_use_external_effect_send_seam_v1 import (
    _permit,
)
from tests.ops.test_n1_original_plan_origin_v1 import seed_with_origin
from tests.ops.test_n1_original_reservation_host_handoff_v1 import (
    synthetic_ports_and_isolation as synthetic_ports_and_isolation,
)
from tests.ops.test_portfolio_budget_host_v1 import _fetch
from tests.ops.test_portfolio_execution_recovery_v1 import _bound


NOW = datetime(2026, 11, 11, 12, tzinfo=timezone.utc)
SESSION = "authenticated-reconciliation-probe"


class SignedReconciliationHttpFixture:
    def __init__(self, identity):
        self.identity = identity
        self.requests = []
        self.fault = None
        self.baseline = _fetch(uid=identity.account_identity)

    @contextmanager
    def open(self, request, timeout):
        url = urlsplit(request.full_url)
        assert request.get_method() == "GET" and request.data is None
        assert url.scheme == "https" and url.hostname == wire.AUTHORIZED_HOST
        assert not request.has_header("X-simulated-trading")
        fields = json.loads(FAKE_OPAQUE)
        timestamp = request.get_header("Ok-access-timestamp")
        query = f"?{url.query}" if url.query else ""
        signed = f"{timestamp}GET{url.path}{query}".encode()
        expected_sign = b64encode(hmac.digest(fields["secretKey"].encode(), signed, "sha256"))
        assert request.get_header("Ok-access-sign").encode() == expected_sign
        assert request.get_header("Ok-access-key") == fields["apiKey"]
        assert request.get_header("Ok-access-passphrase") == fields["passphrase"]
        body = self.body(url.path, dict(parse_qsl(url.query)))
        self.requests.append((url.path + query, sha256(body).hexdigest()))

        class Response:
            status = 200

            def read(self):
                return body

        response = Response()
        response.url = (
            f"https://{wire.AUTHORIZED_HOST}/api/v5/account/balance"
            if self.fault == "same-host-redirect"
            else request.full_url
        )
        yield response

    def body(self, path, params):
        identity = self.identity
        filled = str(Decimal(identity.final_quantity) + 1)
        state = "filled" if self.fault == "filled-anchor" else "partially_filled"
        if self.fault == "healthy-canceled":
            filled, state = "0", "canceled"
        if self.fault == "canceled-after-partial":
            assert Decimal(identity.final_quantity) > 1
            filled, state = "1", "canceled"
        row = {
            "instId": identity.native_id,
            "clOrdId": identity.clordid,
            "ordId": "venue-order",
            "state": state,
            "sz": identity.final_quantity,
            "accFillSz": filled,
        }
        if self.fault == "foreign-product-row":
            row["instType"] = "SWAP"
        code = "0"
        rows = []
        if self.fault == "canceled-after-partial" and path.endswith("/positions"):
            signed = (
                filled if identity.selected_side.upper() in {"LONG", "ENTER_LONG"} else "-" + filled
            )
            rows = [
                {
                    "instId": identity.native_id,
                    "instType": "FUTURES" if not identity.native_id.endswith("-SWAP") else "SWAP",
                    "pos": signed,
                    "posSide": "net",
                }
            ]
            return json.dumps({"code": "0", "data": rows}, separators=(",", ":")).encode()
        if path.endswith("/config"):
            account = "foreign-account" if self.fault == "account" else identity.account_identity
            if self.fault == "duplicate-account-field":
                return (
                    b'{"code":"0","data":[{"uid":"other","uid":'
                    + json.dumps(account).encode()
                    + b"}]}"
                )
            rows = self.baseline(path, params)["data"]
            rows[0]["uid"] = account
        elif "instId" not in params:
            payload = (
                {"code": "0", "data": []}
                if path.endswith("orders-algo-pending") or "/tradingBot/" in path
                else self.baseline(path, params)
            )
            return json.dumps(payload, separators=(",", ":")).encode()
        elif self.fault == "missing-order":
            if path.endswith("/order"):
                code = "51603"
        elif path.endswith(("orders-history", "/order")):
            rows = [row]
            if self.fault == "incomplete-page" and path.endswith("orders-history"):
                rows += [
                    dict(row, clOrdId=f"other{i}", ordId=f"other{i}")
                    for i in range(int(params["limit"]) - 1)
                ]
        elif path.endswith("/fills") and self.fault != "healthy-canceled":
            rows = [
                {
                    **row,
                    "ordId": "foreign-order" if self.fault == "foreign-fill" else row["ordId"],
                    "tradeId": "venue-fill",
                    "fillSz": filled,
                }
            ]
        return json.dumps({"code": code, "data": rows}, separators=(",", ":")).encode()


@pytest.mark.parametrize("initial_usdc,slot_count", [(15, 1), (25, 1), (25, 5)])
def test_live_enter_uses_the_funded_slot_allocation(tmp_path, initial_usdc, slot_count):
    from src.ops.full_core_live_path_composition_root_v1.current_productive_venue_plan_v1 import (
        try_bind_current_productive_venue_plan_v1,
    )
    from src.ops.full_core_live_path_composition_root_v1.final_order_envelope_v1 import (
        bind_final_order_envelope_from_venue_plan_v1,
    )
    from src.ops.portfolio_capital_reservation_budget_v1.slot_loss_budget_v1 import (
        SlotCapitalAllocationV1,
    )
    from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.constants_v1 import (
        REUSED_BINDING_ACCOUNT_SCOPE,
    )
    from tests.ops.test_outer_entry_budget_policy_v1 import (
        EPOCH,
        Slot,
        _balance_payload,
        _bound as entry_bound,
        _enter_replay,
        _host_enter_cycle,
        _injected,
        join,
    )

    account = REUSED_BINDING_ACCOUNT_SCOPE
    bound = entry_bound()
    bindings = {"LANE_1": bound}
    for index, symbol in enumerate(("ETH", "SOL", "XRP", "DOGE")[: slot_count - 1], start=2):
        bindings[f"LANE_{index}"] = replace(
            bound, instrument_id=f"{symbol}-X-PERP", venue_native_id=f"{symbol}-USD_UM-SWAP"
        )
    opening = Decimal(initial_usdc)
    with closing(
        PortfolioBudgetHostV1(
            root=tmp_path / "budget-host",
            private_rest_fetch=_fetch(uid=account),
            repository_sha="test-host-revision",
            session_id="funded-initial-entry",
            expected_account_identity=account,
            durable_mode="create",
            clock=lambda: datetime.fromisoformat(EPOCH.replace("Z", "+00:00")).timestamp(),
            live_slot_capital_allocation=SlotCapitalAllocationV1(
                account, "offline-explicit-allocation", tuple((slot, opening) for slot in bindings)
            ),
        )
    ) as host:
        recovery = host.observe_v1(bindings)
        _, cycle, _ = _host_enter_cycle()
        replay = _enter_replay(cycle)
        result = join(
            replay=replay,
            bound_instrument=bound,
            decision_epoch=EPOCH,
            injected=_injected(payload=_balance_payload(avail_eq="1000.00")),
            portfolio_budget_owner=host.owner,
            portfolio_slot=Slot("LANE_1", str(replay.evidence.decision_id), "initial-entry"),
            host_budget_recovery=recovery,
        )
        assert result.post_count == "0" and result.permit_created == "false"
        if initial_usdc == 15:
            # The same instrument needs a larger allocation for one native lot.
            assert result.status == "FAIL" and result.first_blocker == "ROUNDED_DOWN"
            assert not result.portfolio_reservation_id
            assert host.owner.stored_reservation_count_v1() == 0
            return
        assert result.status == "PASS", result.first_blocker
        assert result.replay.intermediate.canonical_order_intent is not None
        sizing = result.replay.intermediate.capital_risk_sizing_decision
        assert sizing.scope_capital_envelope.available_capital == Decimal("1000.00")
        assert sizing.scope_capital_envelope.per_order_cap == opening
        reserved = sizing.canonical_position_sizing.resulting_notional
        assert 0 < reserved <= opening
        assert host.owner.active_sum_v1() == reserved
        status, reasons, plan = try_bind_current_productive_venue_plan_v1(
            replay=result.replay,
            bound_instrument=bound,
            session_id="funded-initial-entry",
            run_id="funded-initial-entry",
            composed_epoch=EPOCH,
            execution_mode="LIVE",
        )
        assert status.value == "PASS", reasons
        envelope = bind_final_order_envelope_from_venue_plan_v1(
            plan,
            admission_ref="offline",
            provenance_ref="funded-initial-entry",
            creation_epoch=EPOCH,
        )
        assert Decimal(envelope.quantity) == sizing.final_quantity

        observation_id = host.owner.budget_state_v1().observation_id
        over_budget = host.owner.try_reserve_v1(
            slot_id="LANE_1",
            decision_id="second-hold",
            cycle_id="initial-entry",
            observation_id=observation_id,
            amount=opening,
        )
        assert over_budget.reason_codes == (
            "ENTRY_BUDGET_SLOT_LIMIT_EXCEEDED",
            "NO_PARTIAL_MUTATION",
        )
        assert host.owner.active_sum_v1() == reserved
        if slot_count == 5:
            for slot in bindings:
                remaining = opening - reserved if slot == "LANE_1" else opening
                additional = host.owner.try_reserve_v1(
                    slot_id=slot,
                    decision_id=f"test-capacity-{slot}",
                    cycle_id="initial-entry",
                    observation_id=observation_id,
                    amount=remaining,
                )
                assert additional.disposition.value == "ADMITTED", additional.reason_codes
            assert host.owner.active_sum_v1() == Decimal(125)


@pytest.fixture
def authenticated_host(tmp_path, monkeypatch, request):
    from src.ops.portfolio_capital_reservation_budget_v1.slot_loss_budget_v1 import (
        SlotCapitalAllocationV1,
    )
    from tests.ops import test_portfolio_execution_recovery_v1 as original
    from tests.ops.test_current_productive_actual_venue_post_with_fresh_envelope_bound_single_use_permit_v1 import (
        EXPECTED_BASELINE_ORIGIN_MAIN_SHA,
    )

    fault = getattr(request.node, "callspec", SimpleNamespace(params={})).params.get("fault")
    funded = fault in {
        "occupied-mark-direct-funded",
        "occupied-mark-direct-funded-timeout",
        "occupied-mark-direct-funded-revoked",
        "occupied-mark-direct-funded-booked",
        "occupied-mark-direct-funded-exception-close",
        "polled-mark-direct-funded",
        "occupied-mark-direct-stale-capital",
    }
    with monkeypatch.context() as patch:
        if funded:

            def funded_host(root, fetch, clock, expected_account):
                return PortfolioBudgetHostV1(
                    root=(
                        root / "private" / "portfolio_budget_host_v1"
                        if fault
                        in {
                            "occupied-mark-direct-funded-timeout",
                            "occupied-mark-direct-funded-booked",
                            "occupied-mark-direct-funded-exception-close",
                        }
                        else root / "stable-host"
                    ),
                    private_rest_fetch=fetch,
                    repository_sha="test-host-revision",
                    session_id="host-session",
                    expected_account_identity=expected_account,
                    durable_mode="create",
                    clock=clock,
                    live_slot_capital_allocation=SlotCapitalAllocationV1(
                        expected_account, "offline-explicit-allocation", (("LANE_1", Decimal(25)),)
                    ),
                )

            patch.setattr(original, "_host", funded_host)
        seeded, rid, _, envelope, _, _ = seed_with_origin(tmp_path, patch)
    try:
        identity = seeded.owner.begin_execution_submit_v2(
            rid, envelope, seeded.owner.execution_plan_context_v1(rid, envelope), _permit(envelope)
        )
        held = seeded.owner.active_sum_v1()
    finally:
        seeded.close()
    scope = OfflineExecutionIncidentScopeV1(
        tmp_path.resolve(), identity.account_identity, SESSION, NOW - timedelta(seconds=10)
    )
    monkeypatch.setenv("PEAK_KILL_SWITCH_STATE_PATH", str(scope.state_path))
    monkeypatch.delenv("PEAKTRADE_KILL_SWITCH_STATE_PATH", raising=False)
    StatePersistence(str(scope.state_path)).save(KillSwitchState.ACTIVE)
    opener = SignedReconciliationHttpFixture(identity)
    monkeypatch.setattr(wire, "build_opener", lambda *handlers: opener)
    monkeypatch.setattr(wire, "utc_now_iso_v1", NOW.isoformat)
    with open_governed_live_c1_get_only_fresh_pretrade_transport_v1(
        max_request_count=28, k1_lookup_backend=_FakeKeychainBackend()
    ) as (transport, _):
        host = PortfolioBudgetHostV1(
            root=seeded.root,
            private_rest_fetch=_fetch(uid=identity.account_identity),
            repository_sha=EXPECTED_BASELINE_ORIGIN_MAIN_SHA if funded else "test-host-revision",
            session_id=SESSION,
            expected_account_identity=scope.account,
            clock=NOW.timestamp,
            reconciliation_transport=transport,
        )
        try:
            yield host, identity, opener, scope, held
        finally:
            host.close()


@pytest.mark.parametrize(
    "case,reason,final_state,disposition",
    [
        ("confirmed", "EXECUTION_GHOSV_SAFETY_HALT", "KILLED", "KILL_PERSISTED"),
        ("pending", "EXECUTION_GHOSV_SAFETY_HALT", "KILLED", "KILL_PERSISTED"),
        ("already-killed", "EXECUTION_GHOSV_SAFETY_HALT", "KILLED", "ALREADY_BLOCKED"),
        ("managed", "EXECUTION_GHOSV_SAFETY_HALT", "KILLED", "ALREADY_BLOCKED"),
        ("recovering", "EXECUTION_GHOSV_SAFETY_HALT", "KILLED", "KILL_PERSISTED"),
        ("raw-proof-write-failed", "EXECUTION_GHOSV_SAFETY_HALT", "KILLED", "KILL_PERSISTED"),
        ("corrupt-journal", "INCIDENT_JOURNAL_UNPROVEN", "KILLED", None),
        ("foreign-account", "RECONCILIATION_GET_ACCOUNT_UNPROVEN", "ACTIVE", None),
        ("foreign-filegate", "INCIDENT_FILEGATE_SCOPE_MISMATCH", "ACTIVE", None),
        ("missing-port", "HOST_EXECUTION_READ_PORT_MISSING", "ACTIVE", None),
        ("unresolved", "HOST_BUDGET_EXECUTION_RECONCILIATION_UNRESOLVED", "ACTIVE", None),
        ("healthy-canceled", "STARTUP_ADMISSION_REACHED", "ACTIVE", None),
    ],
)
def test_standing_supervisor_delivers_confirmed_incident_before_startup_admission(
    authenticated_host, tmp_path, monkeypatch, case, reason, final_state, disposition
):
    from src.ops.full_core_live_path_composition_root_v1.final_order_envelope_v1 import (
        FinalOrderEnvelopeV1,
    )
    from src.ops.n1_standing_pre_external_runtime_supervisor_v1 import startup_binding_v1 as startup
    from src.ops.n1_standing_pre_external_runtime_supervisor_v1 import supervisor_v1 as supervisor
    from src.ops.n1_standing_pre_external_runtime_supervisor_v1.constants_v1 import (
        TRANSPORT_SCOPE_SCOPED_READONLY_GET,
    )
    from src.ops.portfolio_capital_reservation_budget_v1.contract_v1 import (
        PortfolioCapitalReservationBudgetOwnerV1,
    )
    from tests.ops.test_n1_standing_pre_external_runtime_supervisor_v1 import _continuous_auth

    host, identity, opener, offline_scope, held = authenticated_host
    rid = identity.portfolio_reservation_id
    bound = _bound()
    private = tmp_path / "supervisor-private"
    private.mkdir()
    (private / "portfolio_budget_host_v1").symlink_to(host.root, target_is_directory=True)
    gate = offline_scope.state_path
    live_scope = AuthenticatedExecutionIncidentScopeV1(
        host.root / "execution-incident-safety", identity.account_identity, gate
    )
    if case in {"already-killed", "recovering"}:
        state = KillSwitchState.KILLED if case == "already-killed" else KillSwitchState.RECOVERING
        StatePersistence(str(gate)).save(state, killed_at=NOW, trigger_reason="manual-incident")
    if case == "managed":
        from nacl.signing import SigningKey

        from src.ops.filegate_recovery_authority_v1 import FilegateRecoveryScopeV1
        from src.ops.managed_filegate_v1 import ROOT_ENV, ManagedFilegateV1

        independent = tmp_path.resolve().with_name(tmp_path.name + "-filegate-authority")
        independent.mkdir(mode=0o700)
        gate.unlink()
        managed = ManagedFilegateV1(state_path=gate, root=independent)
        monkeypatch.setenv(ROOT_ENV, str(independent))
        first_stop = managed.provision_v1(
            scope=FilegateRecoveryScopeV1(
                identity.account_identity,
                "LIVE",
                str(host.root),
                (bound.venue_native_id,),
                "a" * 64,
            ),
            issuer_public_key=bytes(SigningKey.generate().verify_key),
            owner_public_keys={
                role: bytes(SigningKey.generate().verify_key)
                for role in ("CAUSE", "ACCOUNT", "HOST")
            },
            recoverable_causes={"R03", "R04"},
        )
    if case == "corrupt-journal":
        live_scope.root.mkdir(mode=0o700)
        live_scope.journal_path.write_text("invalid journal")
    if case == "raw-proof-write-failed":

        def fail_raw_proof_publication(path, data):
            assert json.loads(gate.read_bytes())["state"] == "KILLED"
            assert live_scope.journal_path.is_file()
            raise OSError("synthetic proof storage failure")

        monkeypatch.setattr(store, "_publish", fail_raw_proof_publication)
    if case == "foreign-account":
        opener.fault = "account"
    elif case == "unresolved":
        opener.fault = "missing-order"
    elif case == "healthy-canceled":
        opener.fault = case
    original_gate = gate.read_bytes()
    config = supervisor.StandingSupervisorConfigV1(
        public_store_root=tmp_path / "public",
        private_store_root=private,
        lane_state_root=tmp_path / "lane",
        evidence_root=tmp_path / "standing-session",
        cap24_productivity_root=tmp_path / "cap24",
        expected_account_identity=identity.account_identity,
        venue_native_id=bound.venue_native_id,
        canonical_instrument_id=bound.instrument_id,
        kill_switch_state_path=str(
            tmp_path / "foreign.json" if case == "foreign-filegate" else gate
        ),
        transport_scope=TRANSPORT_SCOPE_SCOPED_READONLY_GET,
    )
    # Supply the already verified selection at the real startup reader boundary.
    # The actual startup gate, account observation, budget recovery and Safety run.
    inspection = SimpleNamespace(
        selection=SimpleNamespace(
            instrument_id=bound.instrument_id,
            venue_native_id=bound.venue_native_id,
            selection_id=bound.selection_id,
            integrity_digest=bound.selection_integrity_digest,
        ),
        ranking=SimpleNamespace(
            ranking_snapshot_id=bound.ranking_snapshot_id,
            integrity_digest=bound.ranking_integrity_digest,
        ),
        universe=SimpleNamespace(snapshot_id=bound.universe_snapshot_id),
    )
    monkeypatch.setattr(startup, "inspect_selection_v1", lambda **kwargs: inspection)
    monkeypatch.setattr(wire, "utc_now_iso_v1", lambda: datetime.now(timezone.utc).isoformat())

    def forbidden(*args, **kwargs):
        pytest.fail("the standing supervisor advanced after the tested startup boundary")

    def admit_selection(**kwargs):
        assert case == "healthy-canceled"
        raise ValueError("STARTUP_ADMISSION_REACHED")

    monkeypatch.setattr(
        startup,
        "acquire_current_productive_29p_cap24_bound_instrument_provenance_handoff_v1",
        admit_selection,
    )
    monkeypatch.setattr(supervisor, "_run_unified_recovery_v1", forbidden)
    private_requests = []
    with pytest.raises(ValueError, match=reason) as caught:
        supervisor.run_n1_standing_pre_external_supervisor_v1(
            config=config,
            origin_main_sha="test-host-revision",
            bound=bound,
            authorization=_continuous_auth(native_id=bound.venue_native_id, max_cycles=1),
            observation_source=None,
            g17_producers={},
            f1_m9_cycle_evaluator=forbidden,
            public_rest_fetch=forbidden,
            private_rest_fetch=_fetch(
                uid=identity.account_identity, pending=case == "pending", calls=private_requests
            ),
            pretrade_transport=None if case == "missing-port" else host.reconciliation_transport,
            skip_owner_go_validation=True,
        )
    assert len(private_requests) == 6
    assert len(opener.requests) == {
        "foreign-filegate": 0,
        "foreign-account": 1,
        "missing-port": 0,
    }.get(case, 6)
    assert host.reconciliation_transport.methods_used == ["GET"] * len(opener.requests)
    assert json.loads(gate.read_bytes())["state"] == final_state
    assert not config.lane_state_root.exists()
    assert not (config.evidence_root / "bounded_continuous_run_owner_go_consume_v1.json").exists()
    if final_state == "ACTIVE":
        assert gate.read_bytes() == original_gate
    if case == "already-killed":
        before = json.loads(original_gate)
        after = json.loads(gate.read_bytes())
        assert after["trigger_reason"] == before["trigger_reason"]
        assert after["killed_at"] == before["killed_at"]
        assert (
            after["latest_authenticated_execution_incident"]
            == caught.value.__cause__.receipt["incident_id"]
        )
    if case == "managed":
        stop = managed.inspect_stop_v1()
        assert stop["generation"] == first_stop["generation"] + 1
        assert stop["causes"] == ["R03", "R04"]
        assert stop["stop_id"] == caught.value.__cause__.receipt["incident_id"]
    if case == "corrupt-journal":
        assert live_scope.journal_path.read_text() == "invalid journal"
    if disposition is None:
        assert not live_scope.get_proof_root.exists()
    if disposition is not None:
        halt = caught.value.__cause__
        receipt = halt.receipt
        proof_status = "UNAVAILABLE" if case == "raw-proof-write-failed" else "PERSISTED"
        assert halt.raw_get_proof_status == proof_status
        assert receipt["disposition"] == disposition
        notice = json.loads((config.evidence_root / "runtime_liveness_latest_v1.json").read_bytes())
        assert notice["reason_code"] == "EXECUTION_GHOSV_SAFETY_HALT"
        assert notice["extra"]["execution_incident_id"] == receipt["incident_id"]
        assert notice["extra"]["execution_incident_kill_revision"] == receipt["kill_revision"]
        assert notice["extra"]["execution_incident_raw_get_proof_status"] == proof_status
        assert notice["extra"]["automatic_restart_allowed"] is False
        assert receipt["session_id"] == config.evidence_root.name
        assert receipt["reconciliation_source"]["reservation_id"] == rid
        assert [row["body_sha256"] for row in receipt["reconciliation_source"]["gets"]] == [
            body_hash for _, body_hash in opener.requests
        ]
        assert stat.S_IMODE(live_scope.get_proof_root.stat().st_mode) == 0o700
        proof_files = list(live_scope.get_proof_root.glob("*.json"))
        if case == "raw-proof-write-failed":
            assert not proof_files
        else:
            (proof_file,) = proof_files
            assert stat.S_IMODE(proof_file.stat().st_mode) == 0o600
        restored = PortfolioCapitalReservationBudgetOwnerV1(
            durable_root=host.root / "owner",
            durable_account_identity=identity.account_identity,
            durable_mode="recover",
            durable_lane_bindings={"LANE_1": bound},
        )
        try:
            assert restored.active_sum_v1() == held > 0
            assert restored.budget_state_v1().recovery_required
            link = restored.execution_links_v1()[rid]
            assert link["reconciliation"]["reservation_released"] is False
            envelope = FinalOrderEnvelopeV1(**link["envelope"])
            observed = observe_authenticated_execution_incident_v1(
                scope=live_scope, envelope=envelope, incident_id=receipt["incident_id"]
            )
            assert observed["state_name"] == "KILLED"
            assert observed["correlated_incident_veto"] is (disposition == "KILL_PERSISTED")
            assert observed["post_safety_veto"].endswith(":TRUSTED_PRESENT:KILLED")
            if case in {"already-killed", "managed"}:
                cold = observe_standing_execution_incident_v1(scope=live_scope)
                assert cold["kill_revision"] == receipt["kill_revision"]
                assert cold["incident_id"] == receipt["incident_id"]
                assert cold["original_post_veto_checked"] is True
                assert cold["incident_evidence_error"] is None
        finally:
            restored.close()
        if case == "managed":
            from src.ops import managed_account_recovery_v1 as recovery
            from src.ops.filegate_recovery_authority_v1 import FilegateAuthorityError

            incident_id = receipt["incident_id"]
            assert stop["execution_incident_ids"] == [incident_id]
            origin = read_authenticated_execution_incident_origin_v1(
                scope=live_scope, incident_id=incident_id
            )
            assert origin["reservation_id"] == rid
            assert origin["identity_digest"] == identity.identity_digest()
            assert origin["native_id"] == identity.native_id
            with pytest.raises(ExecutionIncidentSafetyError, match="INCIDENT_RECEIPT_MISSING"):
                read_authenticated_execution_incident_origin_v1(
                    scope=live_scope, incident_id="b" * 64
                )

            # The historical source is original. Isolate the exact join against
            # both unrelated and correct current stopped-account readbacks.
            stop = managed.kill_v1(cause="R03", reason="new integrity stop")
            assert stop["execution_incident_ids"] == [incident_id]
            host.execution_incident_state_path = gate
            result = {
                "matched": True,
                "original_submit_barrier": {"resubmit_allowed": False},
                "identity_digest": origin["identity_digest"],
            }
            account_readback = {
                "execution_reconciliation": {"unrelated-reservation": result},
                "execution_blocker": None,
                "portfolio_classification": recovery.ProductiveReconciliationClass.MATCH.value,
                "observed_at_unix": stop["killed_at"],
                "account_inventory_completed_unix": stop["killed_at"],
                "account_inventory_max_age_seconds": 5,
            }

            def capture_stopped_account(**kwargs):
                assert kwargs["required_execution_attempts"] == {rid: identity.identity_digest()}
                return account_readback

            monkeypatch.setattr(
                recovery, "capture_managed_stopped_account_v1", capture_stopped_account
            )
            args = dict(
                writer=managed,
                stop=stop,
                host=host,
                bindings={"LANE_1": bound},
                transport_scope=tmp_path,
                key=SigningKey.generate(),
            )
            with pytest.raises(FilegateAuthorityError, match="ORIGINAL_ATTEMPT_UNRESOLVED"):
                recovery.attest_managed_execution_resolution_v1(**args)
            account_readback["execution_reconciliation"] = {
                rid: {**result, "identity_digest": "f" * 64}
            }
            with pytest.raises(FilegateAuthorityError, match="ORIGINAL_ATTEMPT_UNRESOLVED"):
                recovery.attest_managed_execution_resolution_v1(**args)
            account_readback["execution_reconciliation"] = {rid: result}
            proof = recovery.attest_managed_execution_resolution_v1(**args)
            assert proof["body"]["stop"] == stop
            assert proof["body"]["cause"] == "R04"
            assert managed.inspect_stop_v1() == stop
            proof_file.unlink()
            with pytest.raises(
                ExecutionIncidentSafetyError, match="INCIDENT_ORIGINAL_GETS_UNPROVEN"
            ):
                recovery.attest_managed_execution_resolution_v1(**args)
        if case == "confirmed":
            gate_before = gate.read_bytes()
            journal_before = live_scope.journal_path.read_bytes()
            cold_reader = """
import json
from pathlib import Path
import sys
from src.ops.execution_incident_safety_v1 import (
    AuthenticatedExecutionIncidentScopeV1, observe_authenticated_execution_incident_v1,
)
from src.ops.full_core_live_path_composition_root_v1.final_order_envelope_v1 import (
    FinalOrderEnvelopeV1,
)
root, account, gate, envelope = sys.argv[1:]
print(json.dumps(observe_authenticated_execution_incident_v1(
    scope=AuthenticatedExecutionIncidentScopeV1(Path(root), account, Path(gate)),
    envelope=FinalOrderEnvelopeV1(**json.loads(envelope)),
)))
"""
            launcher = Path(__file__).resolve().parents[2] / "scripts/pt"
            child = subprocess.run(
                [
                    str(launcher),
                    "-c",
                    cold_reader,
                    str(live_scope.root),
                    live_scope.account,
                    str(gate),
                    json.dumps(link["envelope"]),
                ],
                check=True,
                capture_output=True,
                text=True,
                timeout=15,
            )
            assert json.loads(child.stdout.splitlines()[-1]) == observed
            assert gate.read_bytes() == gate_before
            assert live_scope.journal_path.read_bytes() == journal_before


def test_scoped_s5_halts_before_core_with_the_same_host_incident(
    authenticated_host, tmp_path, monkeypatch
):
    from src.ops.full_core_live_path_composition_root_v1 import (
        current_productive_persistent_natural_enter_convergence_v1 as convergence,
    )
    from tests.ops._current_productive_natural_mv2_dp_enter_fixture_v1 import (
        governed_productive_c1_event_ts_unix_v1,
        strong_uptrend_closes_v1,
    )
    from tests.ops.test_current_productive_persistent_natural_enter_convergence_v1 import (
        _observation_from_closes,
    )

    host, identity, opener, scope, held = authenticated_host
    host.execution_incident_state_path = scope.state_path
    bound = _bound()
    pairs = convergence.build_s8_occupied_lane_pairs_v1(
        lane_state_root=tmp_path / "lane", bound=bound
    )
    observation = _observation_from_closes(
        closes=strong_uptrend_closes_v1(),
        event_ts=governed_productive_c1_event_ts_unix_v1(),
        bound=bound,
    )

    def forbidden(**kwargs):
        pytest.fail("S5 reached sizing or Core after a confirmed execution incident")

    monkeypatch.setattr(
        convergence, "resolve_live_29p_injected_for_productive_s5_cycle_v1", forbidden
    )
    monkeypatch.setattr(convergence, "_t2_from_s7", forbidden)
    run = convergence.make_n1_occupied_lane_s5_runner_v1(
        composed_pairs=pairs,
        g17_producers={"LANE_1": object()},
        cycle_id_prefix_base="authenticated-s5",
        portfolio_budget_host=host,
    )
    with pytest.raises(ExecutionIncidentHaltV1) as caught:
        run(
            authorization=SimpleNamespace(native_id=bound.venue_native_id),
            origin_main_sha=host.repository_sha,
            cursor_store_root=Path(pairs["LANE_1"][0].lane_state_root),
            lock_root=tmp_path / "lock",
            evidence_root=tmp_path / "cycle",
            candles_payload=observation.candles_payload,
            mark_price_payload=observation.mark_price_payload,
            index_tickers_payload=observation.index_tickers_payload,
            mark_acquired_at_utc=observation.mark_acquired_at_utc,
        )
    assert caught.value.receipt["disposition"] == "KILL_PERSISTED"
    assert (
        caught.value.receipt["reconciliation_source"]["reservation_id"]
        == identity.portfolio_reservation_id
    )
    assert host.owner.active_sum_v1() == held > 0
    assert host.owner.budget_state_v1().recovery_required
    assert json.loads(scope.state_path.read_bytes())["state"] == "KILLED"
    assert len(opener.requests) == 6


@pytest.mark.parametrize("new_kill", [None, "before-veto", "after-veto"])
def test_authenticated_incident_aborts_original_post_before_socket(tmp_path, monkeypatch, new_kill):
    from fastapi.testclient import TestClient

    from src.ops.full_core_live_path_composition_root_v1.current_productive_post_safety_veto_v1 import (
        CurrentPostSafetyContextV1,
    )
    from src.ops.full_core_live_path_composition_root_v1.external_effect_permit_durable_consume_v1 import (
        OriginalPermitTransportAttemptV1,
        load_external_effect_durable_consume_v1,
    )
    from src.ops.full_core_live_path_composition_root_v1.full_core_exchange_reconciliation_v1 import (
        parse_exchange_reconciliation_identity_v1,
    )
    from tests.ops._current_post_safety_fixture_v1 import synthetic_current_post_pending_context_v1
    from tests.ops.test_prepost_original_budget_context_v1 import (
        AccountPort,
        _clean_post_integrity,
        caller,
    )
    from src.webui.app import app
    from src.webui.standing_incident_panel_v1 import ENV_INCIDENT_DIAGNOSTICS_ROOT

    host, rid, _, envelope, _, _ = seed_with_origin(tmp_path, monkeypatch)
    gate = tmp_path / "pre-socket-filegate.json"
    monkeypatch.setenv("PEAK_KILL_SWITCH_STATE_PATH", str(gate))
    monkeypatch.delenv("PEAKTRADE_KILL_SWITCH_STATE_PATH", raising=False)
    monkeypatch.delenv("PEAK_KILL_SWITCH", raising=False)
    StatePersistence(str(gate)).save(KillSwitchState.ACTIVE)
    monkeypatch.setattr(wire, "utc_now_iso_v1", NOW.isoformat)
    host.execution_incident_state_path = gate
    host.clock = NOW.timestamp
    store_root = tmp_path / "send"
    receipt = None
    before_socket = None
    incident_killed_at = None
    kill_at_veto = []
    kill_at_abort = []

    def killed_at():
        return json.loads(gate.read_bytes())["killed_at"]

    def supersede_kill():
        payload = json.loads(gate.read_bytes())
        StatePersistence(str(gate)).save(
            KillSwitchState.KILLED,
            killed_at=datetime.fromisoformat(payload["killed_at"]) + timedelta(microseconds=1),
            trigger_reason=payload["trigger_reason"],
        )

    original_inspect = CurrentPostSafetyContextV1.inspect_v1
    original_abort = OriginalPermitTransportAttemptV1.abort_before_transport_v1

    def inspect(context, *, stage):
        if stage == "BEFORE_SOCKET":
            assert context.state_path == str(gate)
            kill_at_veto.append(killed_at())
        return original_inspect(context, stage=stage)

    def persist_abort(attempt, *, reason_code):
        if new_kill == "after-veto":
            supersede_kill()
        kill_at_abort.append(killed_at())
        return original_abort(attempt, reason_code=reason_code)

    monkeypatch.setattr(CurrentPostSafetyContextV1, "inspect_v1", inspect)
    monkeypatch.setattr(
        OriginalPermitTransportAttemptV1, "abort_before_transport_v1", persist_abort
    )

    class ForbiddenHttp:
        def open(self, *args, **kwargs):
            pytest.fail("authenticated incident must veto before HTTP")

    def inject_incident_before_final_check():
        nonlocal receipt, before_socket, incident_killed_at
        before_socket = load_external_effect_durable_consume_v1(store_root=store_root)["record"]
        assert before_socket["transport_attempt"]["phase"] == "PRE_SOCKET"
        link = host.owner.execution_links_v1()[rid]
        identity = parse_exchange_reconciliation_identity_v1(link["identity"])
        opener = SignedReconciliationHttpFixture(identity)
        monkeypatch.setattr(wire, "build_opener", lambda *handlers: opener)
        with open_governed_live_c1_get_only_fresh_pretrade_transport_v1(
            max_request_count=6, k1_lookup_backend=_FakeKeychainBackend()
        ) as (transport, _):
            host.reconciliation_transport = transport
            with pytest.raises(ExecutionIncidentHaltV1) as stopped:
                host.observe_v1({"LANE_1": _bound()})
            assert transport.methods_used == ["GET"] * 6
        assert stopped.value.raw_get_proof_status == "PERSISTED"
        receipt = stopped.value.receipt
        incident_killed_at = killed_at()
        if new_kill == "before-veto":
            supersede_kill()
        return ForbiddenHttp()

    veto = "POST_SAFETY_DURABLE_VETO:BEFORE_SOCKET:TRUSTED_PRESENT:KILLED"
    try:
        account = host.owner.durable_scope_identity_v1()["account"]
        held = host.owner.active_sum_v1()
        args = dict(
            envelope=envelope,
            portfolio_budget_owner=host.owner,
            portfolio_reservation_id=rid,
            execution_plan_context=host.owner.execution_plan_context_v1(rid, envelope),
            post_pending_context=synthetic_current_post_pending_context_v1(
                envelope, account=account
            ),
        )
        with pytest.raises(caller.CurrentProductiveActualVenuePostError, match=veto):
            caller.execute_current_productive_actual_venue_post_with_fresh_envelope_bound_single_use_permit_v1(
                **args,
                owner_go=caller.OWNER_GO,
                baseline_origin_main_sha=caller.EXPECTED_BASELINE_ORIGIN_MAIN_SHA,
                store_root=store_root,
                evidence_root=tmp_path / "send-evidence",
                perform_real_venue_post=True,
                k1_backend=_FakeKeychainBackend(),
                opener_factory=inject_incident_before_final_check,
                read_only_get_transport=AccountPort(args),
                execution_integrity_backend=_clean_post_integrity(),
            )
        assert receipt["envelope_id"] == envelope.envelope_id
        assert receipt["envelope_digest"] == envelope.envelope_digest
        consumed = load_external_effect_durable_consume_v1(store_root=store_root)
        assert consumed["durable_consumed"] is True
        assert consumed["retry_allowed"] is consumed["resubmit_allowed"] is False
        permit = consumed["record"]
        assert permit["durable_state"] == "ABORTED_BEFORE_TRANSPORT"
        assert permit["permit_id"] == before_socket["permit_id"]
        assert permit["execution_identity_digest"] == receipt["identity_digest"]
        assert permit["envelope_digest"] == receipt["envelope_digest"]
        attempt = permit["transport_attempt"]
        assert attempt["claim_id"] == before_socket["transport_attempt"]["claim_id"]
        assert attempt["phase"] == "ABORTED" and attempt["reason_code"] == veto
        assert "socket_boundary_at_utc" not in attempt
        assert "kill_revision" not in attempt
        assert kill_at_veto == [killed_at() if new_kill == "before-veto" else incident_killed_at]
        assert kill_at_abort == [killed_at()]
        assert (killed_at() != incident_killed_at) is (new_kill is not None)
        assert host.owner.active_sum_v1() == held > 0
        assert host.owner.budget_state_v1().recovery_required
        assert not host.owner.execution_links_v1()[rid]["reconciliation"]["reservation_released"]
    finally:
        host.close()

    output = tmp_path / "diagnostics"

    def read_status():
        run_standing_execution_incident_diagnostics_v1(
            budget_host_root=host.root,
            filegate=gate,
            account=account,
            output_root=output,
            interval_seconds=1,
            samples=1,
        )
        return json.loads((output / "execution-incident-diagnostics-latest-v1.json").read_bytes())

    status = read_status()
    assert status["incident_id"] == receipt["incident_id"]
    monkeypatch.setenv(ENV_INCIDENT_DIAGNOSTICS_ROOT, str(output))
    client = TestClient(app)
    if new_kill is not None:
        assert status["state_name"] == "KILLED" and status["filegate_blocked"] is True
        assert status["kill_revision"] != receipt["kill_revision"]
        assert status["incident_evidence_error"] == "INCIDENT_KILL_GENERATION_MISMATCH"
        assert status["transport_abort"] is None and status["correlated_incident_veto"] is False
        assert "ABORTED_BEFORE_TRANSPORT" not in client.get("/ops").text
        return

    assert status["kill_revision"] == receipt["kill_revision"]
    assert status["raw_get_proof_status"] == "VERIFIED"
    assert status["correlated_incident_veto"] is True
    assert status["transport_abort"] == {
        "state": "ABORTED_BEFORE_TRANSPORT",
        "reason_code": veto,
        "aborted_at_utc": attempt["aborted_at_utc"],
        "record_sha256": sha256(json.dumps(permit, sort_keys=True).encode()).hexdigest(),
        "kill_revision": None,
    }
    page = client.get("/ops")
    assert page.status_code == 200 and page.headers["cache-control"] == "no-store"
    assert "EXECUTION GHOSV · Incident-Diagnose" in page.text
    assert "POST-Veto derselben Sperrgeneration" in page.text and "Bestätigt" in page.text
    assert "ABORTED_BEFORE_TRANSPORT" in page.text
    assert "Zuordnung zur Sperrgeneration offen" in page.text
    assert receipt["incident_id"] in page.text
    assert str(host.root) not in page.text and str(store_root) not in page.text

    permit_path = Path(consumed["path"])
    original_bytes = permit_path.read_bytes()
    permit_path.write_text(json.dumps({**permit, "execution_identity_digest": "f" * 64}))
    damaged = read_status()
    assert damaged["transport_abort"] is None
    assert damaged["correlated_incident_veto"] is True
    assert "ABORTED_BEFORE_TRANSPORT" not in client.get("/ops").text
    permit_path.write_bytes(original_bytes)
    supersede_kill()
    newer = read_status()
    assert newer["state_name"] == "KILLED" and newer["transport_abort"] is None
    assert newer["incident_evidence_error"] == "INCIDENT_KILL_GENERATION_MISMATCH"


def test_independent_standing_diagnostics_continues_under_kill_and_reopens_after_process_death(
    authenticated_host, tmp_path
):
    host, identity, opener, scope, _ = authenticated_host
    gate = scope.state_path
    output = tmp_path / "diagnostic-output"
    plist_path = tmp_path / "diagnostics.plist"
    prepared = prepare_standing_diagnostics_launch_agent_v1(
        destination=plist_path,
        budget_host_root=host.root,
        filegate=gate,
        account=identity.account_identity,
        output_root=output,
        interval_seconds=0.02,
    )
    assert prepared["service_activated"] is False
    assert stat.S_IMODE(plist_path.stat().st_mode) == 0o600
    plist = plistlib.loads(plist_path.read_bytes())
    assert plist["RunAtLoad"] and plist["KeepAlive"]
    assert plist["EnvironmentVariables"] == {"PEAK_KILL_SWITCH_STATE_PATH": str(gate)}
    assert not output.exists()
    latest = output / "execution-incident-diagnostics-latest-v1.json"

    def start():
        return subprocess.Popen(
            plist["ProgramArguments"],
            cwd=plist["WorkingDirectory"],
            env={**os.environ, **plist["EnvironmentVariables"]},
            stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE,
        )

    def wait_for(process, **expected):
        deadline = time.monotonic() + 10
        observed = None
        while time.monotonic() < deadline:
            if process.poll() is not None:
                pytest.fail(process.stderr.read().decode())
            try:
                observed = json.loads(latest.read_bytes())
            except FileNotFoundError:
                pass
            else:
                if observed["pid"] == process.pid and all(
                    observed.get(key) == value for key, value in expected.items()
                ):
                    return observed
            time.sleep(0.02)
        pytest.fail(f"Expected {expected}, observed {observed}")

    first = start()
    second = None
    try:
        active = wait_for(first, state_name="ACTIVE", original_post_veto_checked=False)
        assert active["runtime_authorization_effect"] == "NONE"
        host.execution_incident_state_path = gate
        with pytest.raises(ExecutionIncidentHaltV1) as stopped:
            host.observe_v1({"LANE_1": _bound()})
        host.close()
        receipt = stopped.value.receipt
        journal = host.root / "execution-incident-safety/execution-incident-receipts.json"
        budget = host.root / "owner/reservations.sqlite3"
        (proof,) = tuple((journal.parent / "authenticated-get-proofs").glob("*.json"))
        original = {path: path.read_bytes() for path in (gate, journal, budget, proof)}
        killed = wait_for(
            first,
            state_name="KILLED",
            filegate_blocked=True,
            incident_id=receipt["incident_id"],
            kill_revision=receipt["kill_revision"],
            correlated_incident_veto=True,
            raw_get_proof_status="VERIFIED",
        )
        assert killed["sample_sequence"] > active["sample_sequence"]
        assert killed["original_post_veto_checked"] is True
        assert killed["reconciliation_reason"] == REASON_NEGATIVE_REMAINING
        assert killed["source_scope"]["filegate"] == str(gate)
        assert (
            killed["incident_source"]["budget_revision_ref"]
            == receipt["reconciliation_source"]["revision_ref"]
        )
        assert killed["incident_source"]["reservation_id"] == identity.portfolio_reservation_id
        first.kill()
        first.wait(timeout=5)

        second = start()
        cold = wait_for(
            second,
            state_name="KILLED",
            incident_id=killed["incident_id"],
            kill_revision=killed["kill_revision"],
            correlated_incident_veto=True,
            raw_get_proof_status="VERIFIED",
        )
        assert cold["process_started_at_utc"] != killed["process_started_at_utc"]
        assert cold["pid"] != killed["pid"]
        assert {path: path.read_bytes() for path in original} == original
        assert len(opener.requests) == 6
        with pytest.raises(BlockingIOError):
            run_standing_execution_incident_diagnostics_v1(
                budget_host_root=host.root,
                filegate=gate,
                account=identity.account_identity,
                output_root=output,
                interval_seconds=1,
                samples=1,
            )

        proof.write_text("damaged raw GET proof")
        wait_for(
            second,
            state_name="KILLED",
            filegate_blocked=True,
            correlated_incident_veto=True,
            raw_get_proof_status="UNPROVEN",
        )
        proof.write_bytes(original[proof])
        wait_for(second, state_name="KILLED", raw_get_proof_status="VERIFIED")

        # A missing owner revision removes correlation while the original stop stays visible.
        moved_budget = tmp_path / "original-budget.sqlite3"
        budget.rename(moved_budget)
        wait_for(
            second,
            state_name="KILLED",
            filegate_blocked=True,
            incident_evidence_error="INCIDENT_BUDGET_REVISION_UNPROVEN",
            original_post_veto_checked=False,
            correlated_incident_veto=False,
        )
        moved_budget.rename(budget)
        wait_for(second, state_name="KILLED", correlated_incident_veto=True)

        journal.write_text("damaged journal")
        wait_for(
            second,
            state_name="KILLED",
            filegate_blocked=True,
            incident_evidence_error="INCIDENT_JOURNAL_UNPROVEN",
            correlated_incident_veto=False,
        )
        journal.write_bytes(original[journal])
        gate_payload = json.loads(original[gate])
        StatePersistence(str(gate)).save(
            KillSwitchState.RECOVERING,
            killed_at=datetime.fromisoformat(gate_payload["killed_at"]),
            trigger_reason=gate_payload["trigger_reason"],
        )
        wait_for(
            second,
            state_name="RECOVERING",
            kill_revision=killed["kill_revision"],
            filegate_blocked=True,
            correlated_incident_veto=False,
        )
        StatePersistence(str(gate)).save(
            KillSwitchState.KILLED,
            killed_at=datetime.fromisoformat(gate_payload["killed_at"]) + timedelta(seconds=1),
            trigger_reason=gate_payload["trigger_reason"],
        )
        wait_for(
            second,
            state_name="KILLED",
            incident_id=killed["incident_id"],
            incident_evidence_error="INCIDENT_KILL_GENERATION_MISMATCH",
            incident_source=None,
            correlated_incident_veto=False,
            raw_get_proof_status=None,
        )
        StatePersistence(str(gate)).save(
            KillSwitchState.KILLED, killed_at=NOW, trigger_reason="independent later kill"
        )
        newer = wait_for(
            second,
            state_name="KILLED",
            incident_id=None,
            filegate_blocked=True,
            correlated_incident_veto=False,
        )
        assert newer["kill_revision"] and newer["kill_revision"] != killed["kill_revision"]
        gate.write_text("damaged gate")
        wait_for(second, evidence_status="UNKNOWN_BLOCKED", filegate_blocked=None)
        gate.unlink()
        wait_for(second, evidence_status="MISSING", filegate_blocked=None)
        StatePersistence(str(gate)).save(
            KillSwitchState.KILLED, killed_at=NOW, trigger_reason="independent later kill"
        )
        wait_for(second, observation_status="OBSERVED", kill_revision=newer["kill_revision"])
        assert len(opener.requests) == 6
        assert {path.name for path in output.iterdir()} <= {
            latest.name,
            latest.name + ".tmp",
            "execution-incident-diagnostics.lock",
        }
    finally:
        for process in (first, second):
            if process is not None:
                if process.poll() is None:
                    process.kill()
                process.communicate(timeout=5)


def test_diagnostics_cannot_write_in_the_original_budget_root(authenticated_host):
    host, identity, _, scope, _ = authenticated_host
    with pytest.raises(ValueError, match="DIAGNOSTIC_OUTPUT_OVERLAPS_SOURCE"):
        run_standing_execution_incident_diagnostics_v1(
            budget_host_root=host.root,
            filegate=scope.state_path,
            account=identity.account_identity,
            output_root=host.root / "diagnostics",
            interval_seconds=1,
            samples=1,
        )
    assert not (host.root / "diagnostics").exists()


def test_original_signed_gets_bind_budget_and_quantity_incident_without_safety_write(
    authenticated_host,
):
    host, identity, opener, scope, held = authenticated_host
    rid = identity.portfolio_reservation_id
    bindings = {"LANE_1": _bound()}
    before = scope.state_path.read_bytes()
    original = host.observe_v1(bindings)
    ordinary_requests = opener.requests[:]
    context, proofs = host.observe_authenticated_execution_reconciliation_v1(bindings)
    proof = proofs[rid]
    assert len(ordinary_requests) == len(proof.gets) == 6
    assert opener.requests == ordinary_requests * 2
    assert [(read.endpoint, read.body_sha256) for read in proof.gets] == ordinary_requests
    assert {read.acquired_at for read in proof.gets} == {NOW}
    assert proof.gets[0].decision_id == f"{SESSION}:execution-recovery"
    assert all(read.decision_id == f"{SESSION}:{rid}" for read in proof.gets[1:])
    assert context.execution_reconciliation == original.execution_reconciliation
    assert host.reconciliation_transport.methods_used == ["GET"] * 12
    sequence, checksum, link = read_persisted_execution_reconciliation_v1(host.owner, rid)
    assert proof.revision_ref == (sequence, checksum)
    assert proof.snapshot_digest == link["reconciliation"]["snapshot_digest"]
    assert proof.identity_digest == identity.identity_digest()
    assert proof.quantity_incident.reconciliation_reason == REASON_NEGATIVE_REMAINING
    assert proof.quantity_incident.observed_at == NOW
    assert host.owner.active_sum_v1() == held > 0
    assert host.owner.budget_state_v1().recovery_required
    serialized = json.dumps(asdict(proof), default=str)
    assert (
        "sk-test" not in serialized and "pp-test" not in serialized and "ak-test" not in serialized
    )
    with pytest.raises(
        ExecutionIncidentSafetyError, match="INCIDENT_FILEGATE_SOURCE_SCOPE_MISMATCH"
    ):
        _apply_confirmed_execution_incident_v1(
            scope=scope, identity=identity, expected=proof.quantity_incident
        )
    assert scope.state_path.read_bytes() == before
    assert not scope.journal_path.exists()


def test_original_k1_account_collector_and_reconciliation_share_signed_session(authenticated_host):
    host, identity, opener, scope, held = authenticated_host
    transport = host.reconciliation_transport
    source = K1AccountObservationSourceV1(
        credential=transport._handle,
        transport=transport,
        expected_account_identity=scope.account,
        session_id=SESSION,
        clock=host.clock,
    )
    host.fetch = source
    try:
        # Warm the existing cache with a private config read. The account and
        # order observations must each acquire a new response from the opener.
        transport.get(
            endpoint="/api/v5/account/config", auth_required=True, pretrade_decision_id="warmup"
        )
        rid = identity.portfolio_reservation_id
        context, proofs = host.observe_authenticated_execution_reconciliation_v1(
            {"LANE_1": _bound()}
        )
        assert context.pending_source is source
        assert source.pending_observation_v1().account == scope.account
        assert source.transport.read_count == 10
        assert len(opener.requests) == 1 + 10 + 6
        assert [(read.endpoint, read.body_sha256) for read in proofs[rid].gets] == opener.requests[
            -6:
        ]
        assert proofs[rid].quantity_incident.reconciliation_reason == REASON_NEGATIVE_REMAINING
        assert host.owner.active_sum_v1() == held
        assert not scope.journal_path.exists()
    finally:
        source.close()


@pytest.mark.parametrize(
    "path",
    [
        "archive",
        "standing",
        "managed-r04",
        "unknown",
        "no-custody",
        "foreign-product-row",
        "canceled-after-partial",
        "incomplete-page",
        "existing-post-scope",
        "double-play-close",
        "double-play-net",
        "double-play-paged-net",
        "double-play-productive-paged-net",
        "double-play-shared-productive-paged-net",
    ],
)
def test_futures_reconciliation_uses_bound_product_through_private_replay(
    tmp_path, monkeypatch, proof_root, path, *, on_shared_send=None
):
    from src.ops.full_core_live_path_composition_root_v1.current_productive_venue_plan_v1 import (
        try_bind_current_productive_venue_plan_v1,
    )
    from src.ops.full_core_live_path_composition_root_v1.final_order_envelope_v1 import (
        bind_final_order_envelope_from_venue_plan_v1,
    )
    from tests.ops.test_current_usdc_xperp_financial_admission_v1 import EPOCH, join, prepare
    from tests.ops._legacy_l10_close_snapshot_fixture_v1 import seed_legacy_l10_close_snapshots

    seeded, args, _ = prepare(tmp_path, monkeypatch, scoped_reconciliation=True)
    close_readback, get_count = {
        "double-play-close": ("readback-flat", 84),
        "double-play-net": ("readback-booked", 85),
        "double-play-paged-net": ("readback-paged-booked", 78),
        "double-play-productive-paged-net": ("readback-productive-paged-booked", 87),
        "double-play-shared-productive-paged-net": ("readback-productive-paged-booked", 87),
    }.get(path, (None, 26))
    close_case = close_readback is not None
    if close_case:
        seed_legacy_l10_close_snapshots(monkeypatch)
    managed_case = path == "managed-r04"
    standing = path in {"standing", "managed-r04"}
    send_root = tmp_path / "send" if managed_case else None
    bound = args["bound_instrument"]
    args["injected"] = replace(
        args["injected"],
        funding_cost_observation=None,
        native_initial_margin_observation=None,
        absolute_movement_cost_observation=None,
    )
    try:
        entry = join(**args)
        assert entry.status == "PASS", entry.reason_codes
        status, reasons, plan = try_bind_current_productive_venue_plan_v1(
            replay=entry.replay,
            bound_instrument=bound,
            session_id=SESSION,
            run_id=SESSION,
            composed_epoch=EPOCH,
            execution_mode="LIVE",
        )
        assert status.value == "PASS", reasons
        envelope = bind_final_order_envelope_from_venue_plan_v1(
            plan, admission_ref=SESSION, provenance_ref=SESSION, creation_epoch=EPOCH
        )
        rid = entry.portfolio_reservation_id
        seeded.owner.commit_internal_pre_external_effect_v1(rid)
        seeded.owner.bind_execution_plan_v1(
            rid,
            envelope,
            canonical_intent=entry.replay.intermediate.canonical_order_intent,
            venue_plan=plan,
        )
        if path == "existing-post-scope":
            from src.ops.full_core_live_path_composition_root_v1.current_productive_post_pending_observation_v1 import (
                capture_current_post_pending_v1,
            )
            from src.ops.okx_eea_private_account_state_runtime_v1.k1_source_v1 import (
                open_k1_account_observation_source_v1,
            )
            from tests.ops.test_k1_account_observation_source_v1 import InjectedOpener
            from tests.ops.test_prepost_original_budget_context_v1 import caller, execute

            account = seeded.owner.durable_scope_identity_v1()["account"]
            gate = tmp_path / "futures-scope-filegate.json"
            StatePersistence(str(gate)).save(KillSwitchState.ACTIVE)
            monkeypatch.setenv("PEAK_KILL_SWITCH_STATE_PATH", str(gate))
            monkeypatch.delenv("PEAKTRADE_KILL_SWITCH_STATE_PATH", raising=False)
            monkeypatch.delenv("PEAK_KILL_SWITCH", raising=False)
            opener = InjectedOpener(account=account)
            monkeypatch.setattr(wire, "build_opener", lambda *handlers: opener)

            class ForbiddenPost:
                def open(self, *args, **kwargs):
                    pytest.fail("the SWAP POST scope must not open a FUTURES socket")

            before = seeded.owner.risk_snapshot_v1()
            with open_k1_account_observation_source_v1(
                expected_account_identity=account,
                session_id=SESSION,
                max_request_count=20,
                k1_lookup_backend=_FakeKeychainBackend(),
                account_inventory_guard=True,
                inventory_inst_type="FUTURES",
            ) as source:
                observation = source.collect_v1(
                    instrument_ids_by_native_id={bound.venue_native_id: bound.instrument_id}
                )
                assert observation.account_inventory_source is source
                request = dict(
                    envelope=envelope,
                    portfolio_budget_owner=seeded.owner,
                    portfolio_reservation_id=rid,
                    execution_plan_context=seeded.owner.execution_plan_context_v1(rid, envelope),
                    post_pending_context=capture_current_post_pending_v1(
                        envelope=envelope, source=source
                    ),
                )
                with pytest.raises(
                    caller.CurrentProductiveActualVenuePostError,
                    match="SUPPORTED_NEW_ENTRY_SWAP_SCOPE_REQUIRED",
                ):
                    execute(request, tmp_path, opener=ForbiddenPost())
            assert len(opener.requests) == 20
            assert seeded.owner.risk_snapshot_v1() == before
            assert not list((tmp_path / "send").glob("*.json"))
            return
        permit = _permit(envelope)
        identity = seeded.owner.begin_execution_submit_v2(
            rid,
            envelope,
            seeded.owner.execution_plan_context_v1(rid, envelope),
            permit,
            transport_store_root=send_root,
        )
        if managed_case:
            from src.ops.full_core_live_path_composition_root_v1.external_effect_permit_durable_consume_v1 import (
                DURABLE_STATE_SENT_INITIATED,
                claim_original_permit_transport_attempt_v1,
                persist_external_effect_durable_consume_v1,
            )

            persist_external_effect_durable_consume_v1(
                store_root=send_root,
                permit=permit,
                envelope=envelope,
                durable_state=DURABLE_STATE_SENT_INITIATED,
                post_count=0,
                outcome="SUBMIT_ATTEMPT_STARTED",
                execution_identity=identity,
            )
            claim_original_permit_transport_attempt_v1(
                store_root=send_root,
                permit_id=permit.permit_id,
                envelope_id=envelope.envelope_id,
                envelope_digest=envelope.envelope_digest,
            ).mark_socket_boundary_v1()
        held = seeded.owner.active_sum_v1()
    finally:
        seeded.close()

    scope = OfflineExecutionIncidentScopeV1(
        tmp_path.resolve(), identity.account_identity, SESSION, NOW - timedelta(seconds=10)
    )
    monkeypatch.setenv("PEAK_KILL_SWITCH_STATE_PATH", str(scope.state_path))
    monkeypatch.delenv("PEAKTRADE_KILL_SWITCH_STATE_PATH", raising=False)
    clock = [NOW]
    if managed_case:
        from nacl.signing import SigningKey
        from src.ops.filegate_recovery_authority_v1 import (
            FilegateRecoveryScopeV1,
            attest_filegate_owner_evidence_v1,
        )
        from src.ops.managed_filegate_v1 import ROOT_ENV, ManagedFilegateV1
        from tests.ops.test_offline_public_feed_account_reconciliation_v1 import ReconciliationVenue

        independent = tmp_path.with_name(tmp_path.name + "-authority")
        independent.mkdir(mode=0o700)
        monkeypatch.setenv(ROOT_ENV, str(independent))
        writer = ManagedFilegateV1(
            state_path=scope.state_path, root=independent, clock=lambda: clock[0].timestamp()
        )
        issuer = SigningKey.generate()
        keys = {role: SigningKey.generate() for role in ("CAUSE", "ACCOUNT", "HOST")}
        initial_stop = writer.provision_v1(
            scope=FilegateRecoveryScopeV1(
                identity.account_identity,
                "LIVE",
                str(seeded.root),
                (bound.venue_native_id,),
                "a" * 64,
            ),
            issuer_public_key=bytes(issuer.verify_key),
            owner_public_keys={role: bytes(key.verify_key) for role, key in keys.items()},
            recoverable_causes={"R03", "R04"},
        )

        def proof_for(role, stop):
            return attest_filegate_owner_evidence_v1(
                role=role,
                stop=stop,
                evidence_sha256="b" * 64,
                observed_at=clock[0].timestamp(),
                expires_at=clock[0].timestamp() + 5,
                key=keys[role],
            )

        initial_proofs = {role: proof_for(role, initial_stop) for role in keys}
        writer.release_v1(
            release=writer.issue_release_v1(evidence=initial_proofs, issuer_key=issuer),
            evidence=initial_proofs,
        )
        opener = ReconciliationVenue(identity)
    else:
        StatePersistence(str(scope.state_path)).save(KillSwitchState.ACTIVE)
        opener = SignedReconciliationHttpFixture(identity)
    if path in {"foreign-product-row", "canceled-after-partial", "incomplete-page"}:
        opener.fault = path
    elif path == "unknown":
        opener.fault = "missing-order"
    if close_case:
        original_body = opener.body
        quantity = identity.final_quantity
        timestamp = int(NOW.timestamp() * 1000)
        long = identity.selected_side == "LONG"
        position = {
            "instId": bound.venue_native_id,
            "instType": "FUTURES",
            "pos": quantity if long else "-" + quantity,
            "posSide": "net",
            "mgnMode": "cross",
            "avgPx": "2000",
            "tradeId": "22",
            "uTime": str(timestamp - 500),
        }
        if close_readback in {
            "readback-booked",
            "readback-paged-booked",
            "readback-productive-paged-booked",
        }:
            position.update(posId="8923", cTime=str(timestamp - 1000), ccy="USDC")

        def filled_entry_body(endpoint, params):
            response = json.loads(original_body(endpoint, params))
            if endpoint.endswith("/positions"):
                response["data"] = [position]
            if endpoint.endswith(("orders-history", "/order", "/fills")):
                for row in response["data"]:
                    row.update(state="filled", accFillSz=quantity, instType="FUTURES")
                    if endpoint.endswith("/fills"):
                        row.update(
                            tradeId="22",
                            fillSz=quantity,
                            fillPx="2000",
                            fillTime=str(timestamp - 1000),
                            posSide="net",
                            side="buy" if long else "sell",
                            fee="-0.03",
                            feeCcy="USDC",
                        )
            return json.dumps(response).encode()

        monkeypatch.setattr(opener, "body", filled_entry_body)
    monkeypatch.setattr(wire, "build_opener", lambda *handlers: opener)
    monkeypatch.setattr(wire, "utc_now_iso_v1", lambda: clock[0].isoformat())
    with open_governed_live_c1_get_only_fresh_pretrade_transport_v1(
        max_request_count=get_count,
        k1_lookup_backend=_FakeKeychainBackend(),
    ) as (transport, _):
        source = K1AccountObservationSourceV1(
            credential=transport._handle,
            transport=transport,
            expected_account_identity=scope.account,
            session_id=SESSION,
            clock=NOW.timestamp,
            account_inventory_guard=True,
            inventory_inst_type="FUTURES",
        )
        host = PortfolioBudgetHostV1(
            root=seeded.root,
            private_rest_fetch=_fetch(uid=scope.account) if path == "no-custody" else source,
            repository_sha=(
                seeded.repository_sha
                if managed_case
                else "b707632c51a3c192337ec181825697c15bac5ddf"
                if close_case
                else "test-futures-reconciliation"
            ),
            session_id=SESSION,
            expected_account_identity=scope.account,
            clock=lambda: clock[0].timestamp(),
            reconciliation_transport=transport,
            execution_incident_state_path=scope.state_path if standing or close_case else None,
        )
        try:
            if close_case:
                context, proofs = host.observe_authenticated_execution_reconciliation_v1(
                    {"LANE_1": bound}, proof_root=proof_root, deliver_authenticated_incidents=True
                )
                _assert_authenticated_occupied_mark_close(
                    tmp_path=tmp_path,
                    monkeypatch=monkeypatch,
                    context=context,
                    bound=bound,
                    proof_root=proof_root,
                    proof=proofs[rid],
                    quantity=quantity,
                    polled=True,
                    dispatch=close_readback,
                    opener=opener,
                    shared_post=path == "double-play-shared-productive-paged-net",
                    on_shared_send=on_shared_send,
                )
                assert transport.methods_used == ["GET"] * get_count
                assert host.owner.active_sum_v1() == held
                return
            if path in {"no-custody", "foreign-product-row"}:
                reason = (
                    "HOST_EXECUTION_FUTURES_CUSTODY_UNPROVEN"
                    if path == "no-custody"
                    else "RECONCILIATION_GET_FUTURES_PRODUCT_MISMATCH"
                )
                with pytest.raises(ValueError, match=reason):
                    host.observe_authenticated_execution_reconciliation_v1(
                        {"LANE_1": bound}, proof_root=proof_root
                    )
                assert len(opener.requests) == (0 if path == "no-custody" else 26)
                assert not list(proof_root.iterdir())
                assert host.owner.execution_links_v1()[rid]["reconciliation"] is None
                assert host.owner.active_sum_v1() == held > 0
                return
            if standing:
                with pytest.raises(ExecutionIncidentHaltV1) as stopped:
                    host.observe_v1({"LANE_1": bound})
                assert stopped.value.raw_get_proof_status == "PERSISTED"
                assert json.loads(scope.state_path.read_bytes())["state"] == "KILLED"
                revision = tuple(stopped.value.receipt["reconciliation_source"]["revision_ref"])
                proof_root = host.root / "execution-incident-safety" / "authenticated-get-proofs"
            else:
                context, proofs = host.observe_authenticated_execution_reconciliation_v1(
                    {"LANE_1": bound}, proof_root=proof_root
                )
                assert context.account_inventory_source is source and context.pending_source is None
                revision = proofs[rid].revision_ref
                if path in {"unknown", "incomplete-page", "canceled-after-partial"}:
                    reconciliation = context.execution_reconciliation[rid]
                    assert reconciliation["decision"]["reasons"] == [
                        {
                            "unknown": REASON_TRANSPORT_UNKNOWN,
                            "incomplete-page": REASON_INCOMPLETE_PAGINATION,
                            "canceled-after-partial": "CANCELED_AFTER_PARTIAL",
                        }[path]
                    ]
                    assert reconciliation["reservation_released"] is False
                    assert reconciliation["matched"] is (path == "canceled-after-partial")
                    if path == "canceled-after-partial":
                        assert reconciliation["decision"]["cumulative_filled_qty"] == "1"
                        assert reconciliation["decision"]["exposure_retained"] is True
            assert source.transport.read_count == 20
            assert transport.methods_used == ["GET"] * 26
            assert host.owner.active_sum_v1() == held > 0
            assert host.owner.budget_state_v1().recovery_required
        finally:
            host.close()
            source.close()

    proof_args = _receipt_args(host, scope, identity, proof_root, revision)
    proof = store.read_authenticated_execution_reconciliation_proof_v1(**proof_args)
    if path in {"unknown", "incomplete-page", "canceled-after-partial"}:
        assert proof.quantity_incident is None
    else:
        assert proof.quantity_incident.reconciliation_reason == REASON_NEGATIVE_REMAINING
    assert [(read.endpoint, read.body_sha256) for read in proof.gets] == opener.requests[-6:]
    for read in proof.gets[1:4]:
        query = dict(parse_qsl(urlsplit(read.endpoint).query))
        assert query["instType"] == "FUTURES" and query["instId"] == bound.venue_native_id
    if standing:
        output = tmp_path / "diagnostics"
        run_standing_execution_incident_diagnostics_v1(
            budget_host_root=host.root,
            filegate=scope.state_path,
            account=scope.account,
            output_root=output,
            interval_seconds=1,
            samples=1,
        )
        sample = json.loads((output / "execution-incident-diagnostics-latest-v1.json").read_bytes())
        assert sample["correlated_incident_veto"] is True
        assert sample["raw_get_proof_status"] == "VERIFIED"
    if managed_case:
        from src.ops.full_core_live_path_composition_root_v1.external_effect_permit_durable_consume_v1 import (
            load_external_effect_durable_consume_v1,
        )
        from src.ops.managed_account_recovery_v1 import (
            attest_managed_execution_resolution_v1,
            attest_managed_stopped_account_v1,
        )
        from src.ops.gates.risk_gate import kill_switch_should_block_trading

        stop = writer.inspect_stop_v1()
        assert stop["execution_incident_ids"] == [stop["stop_id"]]
        clock[0] = datetime.fromtimestamp(stop["killed_at"] + 1, timezone.utc)
        barrier = load_external_effect_durable_consume_v1(store_root=send_root)
        opener.fault = "healthy-canceled"

        @contextmanager
        def reopen():
            with open_governed_live_c1_get_only_fresh_pretrade_transport_v1(
                max_request_count=26, k1_lookup_backend=_FakeKeychainBackend()
            ) as (get_port, _):
                with closing(
                    K1AccountObservationSourceV1(
                        credential=get_port._handle,
                        transport=get_port,
                        expected_account_identity=scope.account,
                        session_id=SESSION,
                        clock=lambda: clock[0].timestamp(),
                        account_inventory_guard=True,
                        inventory_inst_type="FUTURES",
                    )
                ) as inventory:
                    reopened = PortfolioBudgetHostV1(
                        root=seeded.root,
                        private_rest_fetch=inventory,
                        repository_sha=seeded.repository_sha,
                        session_id=SESSION,
                        expected_account_identity=scope.account,
                        clock=lambda: clock[0].timestamp(),
                        reconciliation_transport=get_port,
                        execution_incident_state_path=scope.state_path,
                    )
                    try:
                        yield reopened, get_port
                    finally:
                        reopened.close()

        for run in range(2):
            with reopen() as (reopened, port):
                source_args = dict(
                    writer=writer,
                    stop=stop,
                    host=reopened,
                    bindings={"LANE_1": bound},
                    transport_scope=tmp_path,
                )
                proof = attest_managed_execution_resolution_v1(**source_args, key=keys["CAUSE"])
                assert proof["body"]["cause"] == "R04"
                assert reopened.owner.active_sum_v1() == 0
                assert port.methods_used == ["GET"] * 26
            clock[0] += timedelta(seconds=1)
        with reopen() as (reopened, port):
            account = attest_managed_stopped_account_v1(
                **{**source_args, "host": reopened}, key=keys["ACCOUNT"]
            )
            assert port.methods_used == ["GET"] * 20
        assert load_external_effect_durable_consume_v1(store_root=send_root) == barrier
        assert kill_switch_should_block_trading()
        evidence = {"CAUSE": proof, "ACCOUNT": account, "HOST": proof_for("HOST", stop)}
        release = writer.issue_release_v1(evidence=evidence, issuer_key=issuer)
        writer.release_v1(release=release, evidence=evidence)
        assert not kill_switch_should_block_trading()
        return

    (stored,) = tuple(proof_root.glob("*.json"))
    wrapper = json.loads(stored.read_bytes())
    for row in wrapper["record"]["gets"][1:4]:
        row["endpoint"] = row["endpoint"].replace("instType=FUTURES", "instType=SWAP")
    wrapper["sha256"] = sha256(store._encode(wrapper["record"])).hexdigest()
    stored.write_bytes(store._encode(wrapper))
    with pytest.raises(
        store.ExecutionReconciliationProofStoreError, match="REPLAY_REQUEST_MISMATCH"
    ):
        store.read_authenticated_execution_reconciliation_proof_v1(**proof_args)


def test_swap_original_one_shot_uses_signed_custody_and_cold_order_readback(
    tmp_path, monkeypatch, proof_root
):
    from src.ops.full_core_live_path_composition_root_v1.current_productive_post_pending_observation_v1 import (
        capture_current_post_pending_v1,
    )
    from src.ops.full_core_live_path_composition_root_v1.external_effect_permit_durable_consume_v1 import (
        load_external_effect_durable_consume_v1,
    )
    from src.ops.full_core_live_path_composition_root_v1.full_core_exchange_reconciliation_v1 import (
        parse_exchange_reconciliation_identity_v1,
    )
    from src.ops.okx_eea_private_account_state_runtime_v1.k1_source_v1 import (
        open_k1_account_observation_source_v1,
    )
    from tests.ops.test_k1_account_observation_source_v1 import InjectedOpener
    from tests.ops.test_prepost_original_budget_context_v1 import caller, execute

    host, rid, _, envelope, _, _ = seed_with_origin(tmp_path, monkeypatch)
    bound = _bound()
    account = host.owner.durable_scope_identity_v1()["account"]
    held = host.owner.active_sum_v1()
    gate = tmp_path / "one-shot-filegate.json"
    StatePersistence(str(gate)).save(KillSwitchState.ACTIVE)
    monkeypatch.setenv("PEAK_KILL_SWITCH_STATE_PATH", str(gate))
    monkeypatch.delenv("PEAKTRADE_KILL_SWITCH_STATE_PATH", raising=False)
    monkeypatch.delenv("PEAK_KILL_SWITCH", raising=False)
    account_get = InjectedOpener(account=account)
    monkeypatch.setattr(wire, "build_opener", lambda *handlers: account_get)
    attempts = []

    class LostResponse:
        def open(self, request, timeout=0):
            assert request.get_method() == "POST"
            original_link = host.owner.execution_links_v1()[rid]
            record = load_external_effect_durable_consume_v1(store_root=tmp_path / "send")["record"]
            assert record["durable_state"] == "SENT_INITIATED"
            assert original_link["phase"] == "SUBMIT_MAY_HAVE_OCCURRED"
            submitted = parse_exchange_reconciliation_identity_v1(original_link["identity"])
            assert submitted.identity_digest() == record["execution_identity_digest"]
            assert submitted.envelope_digest == envelope.envelope_digest
            attempts.append(submitted)
            raise TimeoutError("injected missing response")

    try:
        with open_k1_account_observation_source_v1(
            expected_account_identity=account,
            session_id=SESSION,
            max_request_count=10,
            k1_lookup_backend=_FakeKeychainBackend(),
        ) as source:
            sample = source.collect_v1(
                instrument_ids_by_native_id={bound.venue_native_id: bound.instrument_id}
            )
            assert sample.pending_source is source
            args = dict(
                envelope=envelope,
                portfolio_budget_owner=host.owner,
                portfolio_reservation_id=rid,
                execution_plan_context=host.owner.execution_plan_context_v1(rid, envelope),
                post_pending_context=capture_current_post_pending_v1(
                    envelope=envelope, source=source
                ),
            )
            result = execute(args, tmp_path, opener=LostResponse())
            assert result.post_outcome == "UNKNOWN_EXTERNAL_EFFECT_POSSIBLE"
            assert host.owner.active_sum_v1() == held > 0
            with pytest.raises(caller.CurrentProductiveActualVenuePostError):
                execute(args, tmp_path, opener=LostResponse())
            other_send_root = tmp_path / "second-send-scope"
            with pytest.raises(caller.CurrentProductiveActualVenuePostError):
                execute(args, other_send_root, opener=LostResponse())
            assert not other_send_root.exists()
            (identity,) = attempts
            assert len(account_get.requests) == 10
    finally:
        host.close()

    venue_get = SignedReconciliationHttpFixture(identity)
    venue_get.fault = "healthy-canceled"
    monkeypatch.setattr(wire, "build_opener", lambda *handlers: venue_get)
    with open_governed_live_c1_get_only_fresh_pretrade_transport_v1(
        max_request_count=16, k1_lookup_backend=_FakeKeychainBackend()
    ) as (transport, _):
        source = K1AccountObservationSourceV1(
            credential=transport._handle,
            transport=transport,
            expected_account_identity=account,
            session_id=SESSION,
        )
        reopened = PortfolioBudgetHostV1(
            root=host.root,
            private_rest_fetch=source,
            repository_sha=host.repository_sha,
            session_id=SESSION,
            expected_account_identity=account,
            reconciliation_transport=transport,
        )
        try:
            context, proofs = reopened.observe_authenticated_execution_reconciliation_v1(
                {"LANE_1": bound}, proof_root=proof_root
            )
            decision = context.execution_reconciliation[rid]
            assert decision["matched"] and decision["reservation_released"]
            assert decision["decision"]["cumulative_filled_qty"] == "0"
            assert reopened.owner.active_sum_v1() == 0
            assert reopened.owner.budget_state_v1().recovery_required
            assert transport.methods_used == ["GET"] * 16
            revision = proofs[rid].revision_ref
        finally:
            reopened.close()
            source.close()
    scope = OfflineExecutionIncidentScopeV1(tmp_path.resolve(), account, SESSION, NOW)
    proof = store.read_authenticated_execution_reconciliation_proof_v1(
        **_receipt_args(reopened, scope, identity, proof_root, revision)
    )
    assert proof.identity_digest == identity.identity_digest()
    assert proof.quantity_incident is None


@pytest.mark.parametrize(
    ("fault", "error"),
    [
        ("account", "ACCOUNT_UNPROVEN"),
        ("stale", "ACQUISITION_UNPROVEN"),
        ("future", "ACQUISITION_UNPROVEN"),
        ("duplicate-account-field", "RESPONSE_UNPROVEN"),
        ("changed-parsed-payload", "PAYLOAD_UNPROVEN"),
        ("same-host-redirect", "GET_RESPONSE_URL_MISMATCH"),
        ("foreign-port", "ORIGINAL_PORT_REQUIRED"),
    ],
)
def test_source_rejects_unbound_get_before_more_reads(
    authenticated_host, monkeypatch, fault, error
):
    host, identity, opener, scope, held = authenticated_host
    before = scope.state_path.read_bytes()
    opener.fault = fault
    if fault in {"stale", "future"}:
        offset = -6 if fault == "stale" else 1
        monkeypatch.setattr(wire, "utc_now_iso_v1", (NOW + timedelta(seconds=offset)).isoformat)
    elif fault == "changed-parsed-payload":

        def change_payload(*, result, body):
            result.payload["data"][0]["changed"] = "after-original-parse"

        host.reconciliation_transport.raw_response_sink_v1 = change_payload
    elif fault == "foreign-port":
        host.reconciliation_transport = object()
    with pytest.raises(
        (ExecutionReconciliationSourceError, wire.FullCoreProductiveReadOnlyGetError), match=error
    ):
        host.observe_authenticated_execution_reconciliation_v1({"LANE_1": _bound()})
    if fault == "foreign-port":
        assert not opener.requests
    else:
        assert len(opener.requests) == 1
        assert host.owner.active_sum_v1() == held
        assert (
            host.owner.execution_links_v1()[identity.portfolio_reservation_id]["reconciliation"]
            is None
        )
    assert scope.state_path.read_bytes() == before
    assert not scope.journal_path.exists()


@pytest.mark.parametrize(
    ("fault", "reason"),
    [("missing-order", REASON_TRANSPORT_UNKNOWN), ("foreign-fill", REASON_NEGATIVE_REMAINING)],
)
def test_authentic_get_proof_alone_does_not_establish_quantity_violation(
    authenticated_host, fault, reason
):
    host, identity, opener, scope, held = authenticated_host
    opener.fault = fault
    rid = identity.portfolio_reservation_id
    context, proofs = host.observe_authenticated_execution_reconciliation_v1({"LANE_1": _bound()})
    assert context.execution_reconciliation[rid]["decision"]["reasons"] == [reason]
    assert proofs[rid].quantity_incident is None
    assert len(proofs[rid].gets) == 6
    assert host.owner.active_sum_v1() == held > 0
    assert not scope.journal_path.exists()


@pytest.fixture
def proof_root(tmp_path):
    root = tmp_path.resolve() / "private-get-evidence"
    root.mkdir(mode=0o700)
    return root


def test_occupied_mark_proof_storage_failure_preserves_safety_halt(
    authenticated_host, proof_root, monkeypatch
):
    from src.ops import execution_reconciliation_proof_store_v1 as store

    host, _, _, scope, held = authenticated_host
    host.execution_incident_state_path = scope.state_path

    def fail_publication(path, data):
        assert json.loads(scope.state_path.read_bytes())["state"] == "KILLED"
        raise OSError("occupied mark proof storage unavailable")

    monkeypatch.setattr(store, "_publish", fail_publication)
    with pytest.raises(ExecutionIncidentHaltV1) as stopped:
        host.observe_authenticated_execution_reconciliation_v1(
            {"LANE_1": _bound()}, proof_root=proof_root, deliver_authenticated_incidents=True
        )
    assert stopped.value.raw_get_proof_status == "UNAVAILABLE"
    assert json.loads(scope.state_path.read_bytes())["state"] == "KILLED"
    assert host.owner.active_sum_v1() == held
    assert not list(proof_root.iterdir())


def _receipt_args(host, scope, identity, proof_root, revision_ref):
    return {
        "root": proof_root,
        "budget_owner_root": host.root / "owner",
        "account": scope.account,
        "session_id": SESSION,
        "reservation_id": identity.portfolio_reservation_id,
        "revision_ref": revision_ref,
    }


@pytest.mark.parametrize(
    "fault,reason",
    [
        (None, None),
        ("occupied-mark-direct", None),
        ("polled-mark-direct", None),
        ("occupied-mark-direct-funded", None),
        ("occupied-mark-direct-funded-timeout", None),
        ("occupied-mark-direct-funded-revoked", None),
        ("occupied-mark-direct-funded-booked", None),
        ("occupied-mark-direct-funded-exception-close", None),
        ("polled-mark-direct-funded", None),
        ("occupied-mark-direct-stale-capital", None),
        ("occupied-mark", None),
        ("polled-mark", None),
        ("polled-mark-close-ack", None),
        ("polled-mark-close-shared", None),
        ("polled-mark-close-shared-revoked", None),
        ("polled-mark-close-shared-stale-snapshot", None),
        ("polled-mark-close-timeout", None),
        ("polled-mark-close-venue-timeout", None),
        ("polled-mark-close-redirect", None),
        ("polled-mark-close-wrong-key", None),
        ("polled-mark-close-kill", None),
        ("polled-mark-close-stale-position", None),
        ("polled-mark-close-readback-flat", None),
        ("polled-mark-close-readback-booked", None),
        ("polled-mark-close-readback-paged-booked", None),
        ("polled-mark-close-readback-paged-missing", None),
        ("polled-mark-close-readback-paged-foreign", None),
        ("polled-mark-close-readback-paged-open-orders", None),
        ("polled-mark-close-readback-productive-paged-booked", None),
        ("polled-mark-close-readback-productive-paged-missing", None),
        ("polled-mark-close-readback-productive-paged-foreign", None),
        ("polled-mark-close-readback-productive-paged-foreign-product", None),
        ("polled-mark-close-readback-productive-paged-open-orders", None),
        ("polled-mark-close-readback-history-missing", None),
        ("polled-mark-close-readback-history-conflict", None),
        ("polled-mark-close-readback-history-foreign", None),
        ("polled-mark-close-readback-owner-go-lost", None),
        ("polled-mark-close-readback-partial", None),
        ("polled-mark-close-readback-unseen", None),
        ("polled-mark-close-readback-missing-fill", None),
        ("polled-mark-close-readback-page-orders-pending", None),
        ("polled-mark-close-readback-page-orders-history", None),
        ("polled-mark-close-readback-page-fills", None),
        ("polled-mark-close-readback-wrong-order", None),
        ("polled-mark-close-readback-stale-residual", None),
        ("polled-mark-close-readback-no-flat-anchor", None),
        ("terminal-partial", None),
        ("missing-fills", "VENUE_ENTRY_FILL_POSITION_LINK_UNPROVEN"),
        ("wrong-position-trade", "VENUE_ENTRY_FILL_POSITION_LINK_UNPROVEN"),
        ("future-fill", "VENUE_ENTRY_FILL_POSITION_LINK_UNPROVEN"),
        ("nonterminal", "VENUE_ENTRY_TERMINAL_FILL_UNPROVEN"),
    ],
)
def test_owned_entry_proof_reaches_original_position_episode(
    authenticated_host, proof_root, tmp_path, monkeypatch, fault, reason
):
    from src.ops.exit_policy_producer_binding_v1.authenticated_execution_entry_source_v1 import (
        open_position_episode_from_authenticated_execution_v1,
    )
    from src.ops.exit_policy_producer_binding_v1.position_episode_binding_v1 import (
        PositionEpisodeScopeV1,
    )
    from tests.ops._legacy_l10_close_snapshot_fixture_v1 import seed_legacy_l10_close_snapshots

    host, attempt, opener, scope, held = authenticated_host
    dispatch = (
        fault.removeprefix("polled-mark-close-")
        if fault and fault.startswith("polled-mark-close-")
        else None
    )
    direct = fault in {
        "occupied-mark-direct",
        "polled-mark-direct",
        "occupied-mark-direct-funded",
        "occupied-mark-direct-funded-timeout",
        "occupied-mark-direct-funded-revoked",
        "occupied-mark-direct-funded-booked",
        "occupied-mark-direct-funded-exception-close",
        "polled-mark-direct-funded",
        "occupied-mark-direct-stale-capital",
    }
    polled = (fault or "").startswith("polled-mark") or dispatch is not None
    occupied_mark = direct or fault == "occupied-mark" or polled
    if dispatch is not None:
        host.repository_sha = "b707632c51a3c192337ec181825697c15bac5ddf"
    body = opener.body
    stamp = int(NOW.timestamp() * 1000)
    filled_at = stamp - 1000
    long = attempt.selected_side == "LONG"
    entry_price = "2000" if occupied_mark else "98.25"
    quantity = (
        str(Decimal(attempt.final_quantity) / 2)
        if fault == "terminal-partial"
        else attempt.final_quantity
    )
    position = {
        "instId": attempt.native_id,
        "instType": "SWAP",
        "pos": quantity if long else "-" + quantity,
        "posSide": "net",
        "mgnMode": "cross",
        "avgPx": entry_price,
        "tradeId": "23" if fault == "wrong-position-trade" else "22",
        "uTime": str(stamp - 500),
    }
    with_history = dispatch in {
        "readback-booked",
        "readback-paged-booked",
        "readback-productive-paged-booked",
        "readback-history-missing",
        "readback-history-conflict",
        "readback-history-foreign",
        "readback-owner-go-lost",
    }
    if with_history:
        position.update(posId="8923", cTime=str(filled_at), ccy="USDT")
    if fault in {
        "occupied-mark-direct-funded-booked",
        "occupied-mark-direct-funded-exception-close",
    }:
        position.update(posId="8923", cTime=str(filled_at), ccy="USDT", fee="-0.03")
    host.fetch = _fetch(uid=scope.account, positions=(position,))

    def entry_body(path, params):
        response = json.loads(body(path, params))
        if path.endswith("/positions"):
            response["data"] = [position]
        if path.endswith("/fills") and fault == "missing-fills":
            response["data"] = []
        if path.endswith(("orders-history", "/order", "/fills")):
            state = {"nonterminal": "partially_filled", "terminal-partial": "canceled"}.get(
                fault, "filled"
            )
            for row in response["data"]:
                row.update(state=state, accFillSz=quantity)
                if path.endswith("/fills"):
                    row.update(
                        tradeId="22",
                        fillSz=quantity,
                        fillPx=entry_price,
                        side="buy" if long else "sell",
                        posSide="net",
                        fillTime=str(stamp + 1 if fault == "future-fill" else filled_at),
                        fee="-0.03",
                        feeCcy="USDT",
                    )
        return json.dumps(response).encode()

    monkeypatch.setattr(opener, "body", entry_body)
    bound = _bound()
    context, proofs = host.observe_authenticated_execution_reconciliation_v1(
        {"LANE_1": bound}, proof_root=proof_root
    )
    rid = attempt.portfolio_reservation_id
    account_scope = PositionEpisodeScopeV1(scope.account, "LIVE")
    episode_root = host.root / "position-episodes" / attempt.identity_digest()
    from src.ops.exit_policy_producer_binding_v1.constants_v1 import (
        FROZEN_PROFIT_PROTECTION_DISTANCE,
    )
    from trading.master_v2.layer_c_scope_event_distance_binding_v1 import (
        layer_c_derived_exit_policy_adverse_config_digest_v1,
    )

    args = dict(
        bound=bound,
        lane_id="LANE_1",
        account_scope=account_scope,
        proof_root=proof_root,
        budget_owner_root=host.root / "owner",
        source_session_id=SESSION,
        reservation_id=rid,
        revision_ref=proofs[rid].revision_ref,
        state_root=episode_root,
        repository_sha=host.repository_sha,
        config_digest=layer_c_derived_exit_policy_adverse_config_digest_v1(
            profit_protection_distance=FROZEN_PROFIT_PROTECTION_DISTANCE
        ),
        writer_session_id=SESSION,
    )
    host_args = dict(
        lane_id="LANE_1",
        proof_root=proof_root,
        proof=proofs[rid],
        config_digest=args["config_digest"],
    )
    if reason is not None:
        with pytest.raises(ValueError, match=reason):
            context.bind_current_authenticated_entry_episode_v1(**host_args)
        assert not episode_root.exists()
        return

    assert host.owner.active_sum_v1() == held
    request_count = len(opener.requests)
    with monkeypatch.context() as patch:
        patch.setattr(host, "clock", lambda: NOW.timestamp() + 6)
        with pytest.raises(ValueError, match="HOST_AUTHENTICATED_ENTRY_OBSERVATION_UNPROVEN"):
            context.bind_current_authenticated_entry_episode_v1(**host_args)
    assert not episode_root.exists()
    episode = context.bind_current_authenticated_entry_episode_v1(**host_args)
    replayed = context.bind_current_authenticated_entry_episode_v1(**host_args)
    assert replayed.input_binding_v1() == episode.input_binding_v1()
    if occupied_mark:
        if not direct:
            seed_legacy_l10_close_snapshots(monkeypatch)
        host.execution_incident_state_path = scope.state_path
        _assert_authenticated_occupied_mark_close(
            tmp_path=tmp_path,
            monkeypatch=monkeypatch,
            context=context,
            bound=bound,
            proof_root=proof_root,
            proof=proofs[rid],
            quantity=quantity,
            polled=polled,
            dispatch=dispatch,
            opener=opener,
            direct=direct,
            funding_case=fault.split("-direct", 1)[1] if direct else "",
        )
        expected_gets = 0 if direct and not polled else 12
        if (
            dispatch
            and dispatch.startswith("readback-")
            and not dispatch.startswith("readback-paged-")
        ):
            expected_gets += 6 + int(with_history)
        if dispatch in {
            "readback-productive-paged-booked",
            "readback-productive-paged-foreign",
            "readback-productive-paged-foreign-product",
        }:
            expected_gets += 2
        if dispatch == "readback-productive-paged-open-orders":
            expected_gets += 3
        if dispatch and dispatch.startswith("readback-page-"):
            expected_gets += 1
        if dispatch == "readback-productive-paged-missing":
            expected_gets -= 1  # The timeout arrives before the fixture records a response.
        if dispatch == "readback-owner-go-lost":
            expected_gets += 7
        assert len(opener.requests) - request_count == expected_gets
        assert host.owner.active_sum_v1() == held
        return
    if fault is None:
        later = NOW + timedelta(seconds=1)
        monkeypatch.setattr(host, "clock", later.timestamp)
        monkeypatch.setattr(wire, "utc_now_iso_v1", later.isoformat)
        refreshed_context, refreshed = host.observe_authenticated_execution_reconciliation_v1(
            {"LANE_1": bound}, proof_root=proof_root
        )
        assert refreshed[rid].revision_ref != proofs[rid].revision_ref
        assert (
            refreshed_context.bind_current_authenticated_entry_episode_v1(
                **{**host_args, "proof": refreshed[rid]}
            ).input_binding_v1()
            == episode.input_binding_v1()
        )
        request_count = len(opener.requests)
    assert episode.identity.episode_id == attempt.identity_digest()
    assert episode.identity.position_side == ("long" if long else "short")
    host.close()
    restored = open_position_episode_from_authenticated_execution_v1(**args, mode="recover")
    assert restored.input_binding_v1() == episode.input_binding_v1()
    prepared = restored.prepare_for_cycle_v1(
        instrument_id=bound.instrument_id,
        venue_native_id=bound.venue_native_id,
        position_side=episode.identity.position_side,
        venue_flat=False,
        event_time=NOW.timestamp(),
        lane_id="LANE_1",
        expected_scope=account_scope,
    )
    assert prepared.entry_price == 98.25
    assert prepared.entry_event_time == filled_at / 1000
    assert len(opener.requests) == request_count


def _assert_direct_reversal_order_stops_at_original_post_admission(
    tmp_path, envelope, context, proof, lane_pair, entry
):
    from src.ops.full_core_live_path_composition_root_v1.current_productive_double_play_reversal_v1 import (
        prepare_authenticated_net_reversal_post_v1,
    )
    from src.ops.full_core_live_path_composition_root_v1.current_productive_one_shot_fresh_envelope_permit_mint_durable_consume_and_post_join_v1 import (
        POST_OWNER_GO,
        CurrentProductiveOneShotFreshEnvelopeJoinError,
        OneShotJoinProbeV1,
        attempt_current_productive_one_shot_fresh_envelope_permit_mint_durable_consume_and_post_join_v1,
    )
    from src.ops.full_core_live_path_composition_root_v1.current_productive_shared_post_owner_authority_v1 import (
        SharedPostOwnerAuthorityError,
    )
    from src.ops.full_core_live_path_composition_root_v1.full_core_exchange_reconciliation_v1 import (
        parse_exchange_reconciliation_identity_v1,
    )
    from src.ops.full_core_live_path_composition_root_v1.external_effect_permit_durable_consume_v1 import (
        load_external_effect_durable_consume_v1,
    )
    from tests.ops.test_current_productive_actual_venue_post_with_fresh_envelope_bound_single_use_permit_v1 import (
        EXPECTED_BASELINE_ORIGIN_MAIN_SHA,
        _clean_post_integrity,
    )
    from tests.ops.test_current_productive_shared_post_owner_authority_v1 import (
        _claim_rows,
        signed_post_authorization,
    )

    grant_dir = tmp_path / "net-reversal-grant"
    grant_dir.mkdir()
    attempt_root = tmp_path / "net-reversal-send"
    auth, _ = signed_post_authorization(
        grant_dir, envelope, account=context.account, action="DIRECT_DOUBLE_PLAY_REVERSAL"
    )
    with pytest.raises(SharedPostOwnerAuthorityError, match="POST_GRANT_SCOPE_MISMATCH"):
        auth.consume_v1(
            account=context.account,
            action="ENTER",
            envelope_digest=envelope.envelope_digest,
            attempt_root=attempt_root,
        )
    assert _claim_rows(auth) == []

    def forbidden_opener():
        pytest.fail("An unadmitted reversal reached the OKX opener")

    def attempt(**owner_args):
        probe = OneShotJoinProbeV1()
        try:
            return attempt_current_productive_one_shot_fresh_envelope_permit_mint_durable_consume_and_post_join_v1(
                envelope=envelope,
                post_owner_go=POST_OWNER_GO,
                store_root=attempt_root,
                k1_backend=None,
                opener_factory=forbidden_opener,
                probe=probe,
                **owner_args,
            )
        finally:
            assert not probe.permit_minted and probe.http_post_attempts == 0

    with pytest.raises(
        CurrentProductiveOneShotFreshEnvelopeJoinError,
        match="HOST_PORTFOLIO_EXECUTION_CONTEXT_REQUIRED",
    ):
        attempt()
    owner = context.host.owner
    original_link = owner.execution_links_v1()[proof.reservation_id]
    original_identity = parse_exchange_reconciliation_identity_v1(original_link["identity"])
    with pytest.raises(
        CurrentProductiveOneShotFreshEnvelopeJoinError, match="EXECUTION_SUBMIT_REPLAY_OR_UNBOUND"
    ):
        attempt(
            portfolio_budget_owner=owner,
            portfolio_reservation_id=proof.reservation_id,
            execution_identity=original_identity,
        )
    assert owner.execution_links_v1()[proof.reservation_id] == original_link
    assert not attempt_root.exists()
    with pytest.raises(ValueError, match="ORIGINAL_HOLD_REQUIRED"):
        owner.live_reversal_slot_basis_v1(
            slot_id="LANE_2", bound=lane_pair[1], reservation_id=proof.reservation_id
        )
    args = dict(
        lane_pair=lane_pair,
        recovery=context,
        authenticated_entry=entry,
        baseline_origin_main_sha=EXPECTED_BASELINE_ORIGIN_MAIN_SHA,
        execution_integrity_backend=_clean_post_integrity(),
    )
    prepared = prepare_authenticated_net_reversal_post_v1(authorization=auth, **args)
    prepared.inspect_v1(envelope_id=envelope.envelope_id, envelope_digest=envelope.envelope_digest)
    record = load_external_effect_durable_consume_v1(store_root=prepared.store_root)["record"]
    assert record["transport_attempt"]["phase"] == "PRE_SOCKET" and record["post_count"] == 0
    assert _claim_rows(auth) == [(auth.grant.grant_id, 0)]
    with pytest.raises(ValueError, match="REVERSAL_ALREADY_CONSUMED"):
        prepare_authenticated_net_reversal_post_v1(
            authorization=replace(auth, authority=replace(auth.authority)), **args
        )
    assert owner.execution_links_v1()[proof.reservation_id] == original_link


def _assert_direct_reversal_dispatch(
    tmp_path, envelope, context, proof_root, lane_pair, entry, *, revoked, after_timeout=None
):
    from src.ops.full_core_live_path_composition_root_v1 import (
        current_productive_double_play_reversal_v1 as reversal,
        current_productive_one_shot_fresh_envelope_permit_mint_durable_consume_and_post_join_v1 as one_shot,
        full_core_productive_http_post_transport_v1 as http_post,
    )
    from src.ops.full_core_live_path_composition_root_v1.external_effect_permit_durable_consume_v1 import (
        load_external_effect_durable_consume_v1,
    )
    from tests.ops.test_current_productive_actual_venue_post_with_fresh_envelope_bound_single_use_permit_v1 import (
        _clean_post_integrity,
    )
    from tests.ops.test_current_productive_shared_post_owner_authority_v1 import (
        _claim_rows,
        revoke,
        signed_post_authorization,
    )

    host = context.host
    slot, bound = lane_pair
    proof = entry.proof
    root = host.root / "position-episodes" / proof.identity_digest / "net-reversal-submit"
    grant_root = tmp_path / "reversal-grant"
    grant_root.mkdir()
    authorization, signer = signed_post_authorization(
        grant_root, envelope, account=context.account, action=reversal.DIRECT_DOUBLE_PLAY_REVERSAL
    )
    before = host.owner.risk_snapshot_v1()
    (original_hold,) = (
        row
        for row in before["state"]["reservations"]
        if row["reservation_id"] == proof.reservation_id
    )
    assert original_hold["state"] == "COMMITTED" and original_hold["slot_id"] == slot.lane_id
    requests = []

    class TimeoutOpener:
        def open(self, request, timeout):
            assert (
                request.full_url
                == f"https://{http_post.AUTHORIZED_HOST}{http_post.TRADE_ORDER_PATH}"
            )
            assert request.get_method() == "POST"
            record = load_external_effect_durable_consume_v1(store_root=root)["record"]
            assert record["transport_attempt"]["phase"] == "MAY_HAVE_SENT"
            assert record["envelope_digest"] == envelope.envelope_digest
            assert _claim_rows(authorization) == [(authorization.grant.grant_id, 1)]
            payload = json.loads(request.data)
            assert payload == {
                "instId": bound.venue_native_id,
                "side": "sell",
                "sz": envelope.quantity,
                "ordType": "market",
                "tdMode": envelope.td_mode,
                "posSide": "net",
                "clOrdId": envelope.client_order_id,
            }
            timestamp = request.get_header("Ok-access-timestamp")
            key = json.loads(FAKE_OPAQUE)["secretKey"].encode()
            signed = (
                timestamp.encode() + b"POST" + http_post.TRADE_ORDER_PATH.encode() + request.data
            )
            assert request.get_header("Ok-access-sign").encode() == b64encode(
                hmac.digest(key, signed, "sha256")
            )
            assert host.owner.risk_snapshot_v1() == before
            requests.append(payload)
            raise TimeoutError("simulated OKX timeout after the socket boundary")

    def forbidden(*args, **kwargs):
        pytest.fail("a second POST must not reach the opener")

    args = dict(
        lane_pair=lane_pair,
        recovery=context,
        authenticated_entry=entry,
        authorization=authorization,
        baseline_origin_main_sha=host.repository_sha,
        perform_real_venue_post=True,
        k1_backend=_FakeKeychainBackend(),
        execution_integrity_backend=_clean_post_integrity(),
    )
    if revoked:

        def revoke_before_socket():
            revoke(authorization, signer)
            return SimpleNamespace(open=forbidden)

        with pytest.raises(
            http_post.FullCoreCurrentPostOwnerGrantVetoError, match="POST_GRANT_REVOKED"
        ):
            one_shot.execute_authenticated_net_reversal_post_v1(
                **args, opener_factory=revoke_before_socket
            )
        aborted = load_external_effect_durable_consume_v1(store_root=root)["record"]
        assert aborted["transport_attempt"]["phase"] == "ABORTED"
        assert aborted["post_count"] == 0
        assert _claim_rows(authorization) == [(authorization.grant.grant_id, 0)]
        assert host.owner.risk_snapshot_v1() == before
        return

    result = one_shot.execute_authenticated_net_reversal_post_v1(
        **args, opener_factory=TimeoutOpener
    )
    assert result.post_attempted and result.unknown_outcome and not result.venue_live_contact
    assert result.outcome_phase == http_post.TRANSPORT_FAILURE_BEFORE_RESPONSE
    assert len(requests) == 1
    consumed = load_external_effect_durable_consume_v1(store_root=root)
    assert consumed["record"]["outcome"] == "UNKNOWN"
    assert consumed["record"]["post_count"] == 1
    assert consumed["retry_allowed"] is False
    assert host.owner.risk_snapshot_v1() == before
    with pytest.raises(ValueError, match="POST_AUTHORITY_REVERSAL_ALREADY_CONSUMED"):
        one_shot.execute_authenticated_net_reversal_post_v1(**args, opener_factory=forbidden)

    host.close()
    if after_timeout is not None:
        after_timeout(consumed["record"], root)
        return
    before_restart = {
        path: path.read_bytes()
        for path in (
            host.root / "owner" / "reservations.sqlite3",
            Path(consumed["path"]),
            authorization.authority.path,
            authorization.authority.checkpoint_path,
        )
    }
    worker = """
import json
from pathlib import Path
import sys

def deny_sockets(event, args):
    if event.startswith("socket."):
        raise AssertionError("real sockets are unavailable during restart")

sys.addaudithook(deny_sockets)
from src.ops.full_core_live_path_composition_root_v1.current_productive_post_safety_veto_v1 import (
    resolve_current_post_safety_context_v1,
)
from src.ops.full_core_live_path_composition_root_v1.envelope_bound_external_effect_send_seam_v1 import (
    _payload_from_envelope_v1,
)
from src.ops.full_core_live_path_composition_root_v1.external_effect_permit_durable_consume_v1 import (
    OriginalPermitTransportAttemptV1, load_external_effect_durable_consume_v1,
)
from src.ops.full_core_live_path_composition_root_v1.final_order_envelope_v1 import FinalOrderEnvelopeV1
from src.ops.full_core_live_path_composition_root_v1.full_core_productive_http_post_transport_v1 import (
    FullCoreProductiveHttpPostError, FullCoreProductiveHttpTradeOrderTransportV1,
    FullCoreSendCredentialHandleV1,
)
from src.ops.n1_standing_pre_external_runtime_supervisor_v1 import supervisor_v1 as supervisor
from src.ops.single_selected_future_runtime_binding_v1.models_v1 import BoundInstrumentV1
from tests.ops.test_current_productive_persistent_natural_enter_convergence_v1 import _continuous_auth

tmp_path = Path(sys.argv[1])
inputs = json.loads(sys.argv[2])
bound = BoundInstrumentV1(**inputs["bound"])
envelope = FinalOrderEnvelopeV1(**inputs["envelope"])

def forbidden(*args, **kwargs):
    raise AssertionError("restart must stop before market data, private GET and POST")

config = supervisor.StandingSupervisorConfigV1(
    public_store_root=tmp_path / "public",
    private_store_root=tmp_path / "private",
    lane_state_root=tmp_path / "scope",
    evidence_root=tmp_path / "restart" / "net-reversal",
    expected_account_identity=inputs["account"],
    venue_native_id=bound.venue_native_id,
    canonical_instrument_id=bound.instrument_id,
    transport_scope=supervisor.TRANSPORT_SCOPE_SCOPED_READONLY_GET,
)
for proof_root in (Path(inputs["proof_root"]), None):
    run = supervisor.run_n1_standing_pre_external_supervisor_v1(
        config=config, origin_main_sha=inputs["revision"], bound=bound,
        authorization=_continuous_auth(native_id=bound.venue_native_id, max_cycles=1),
        observation_source=None, g17_producers={}, f1_m9_cycle_evaluator=forbidden,
        public_rest_fetch=forbidden, private_rest_fetch=forbidden, wp02_hook=forbidden,
        skip_owner_go_validation=True, occupied_mark_proof_root=proof_root,
    )
    assert not run.ok and run.trace.terminal_disposition == supervisor.DISPOSITION_FAIL_CLOSED
    assert run.trace.post_count == 0 and not run.owner_go_consumed and run.policy_result is None
    assert run.trace.extra["net_reversal_readback"] == inputs["expected"]

root = Path(inputs["attempt_root"])
record = load_external_effect_durable_consume_v1(store_root=root)["record"]
attempt = OriginalPermitTransportAttemptV1(
    str(root), record["permit_id"], record["envelope_id"], record["envelope_digest"],
    record["transport_attempt"]["claim_id"],
)
sender = FullCoreProductiveHttpTradeOrderTransportV1(
    handle=FullCoreSendCredentialHandleV1(handle_id="test", bound=True, material_loaded=False),
    transport_attempt=attempt, opener_factory=forbidden,
    post_safety_context=resolve_current_post_safety_context_v1(envelope, stage="OFFLINE_RESTART"),
)
try:
    sender.post_trade_order(
        payload=_payload_from_envelope_v1(envelope), permit_id=attempt.permit_id,
        envelope_id=envelope.envelope_id, envelope_digest=envelope.envelope_digest,
        one_shot_real_post=True,
    )
except FullCoreProductiveHttpPostError as exc:
    assert str(exc) == "ORIGINAL_TRANSPORT_CLAIM_CLOSED_OR_MISMATCH"
else:
    raise AssertionError("the old transport claim cannot submit again")
assert sender.post_count == 0
"""
    env = os.environ.copy()
    if env.get("GITHUB_ACTIONS") == "true":
        env.update(PT_RUNTIME_MODE="provisioned", PT_PROVISIONED_PYTHON=sys.executable)
    payload = {
        "bound": bound.to_dict(),
        "envelope": envelope.to_runtime_json_v1(),
        "revision": host.repository_sha,
        "account": context.account,
        "proof_root": str(proof_root),
        "attempt_root": str(root),
        "expected": {
            "episode_id": proof.identity_digest,
            "envelope_digest": envelope.envelope_digest,
            "client_order_id": envelope.client_order_id,
            "reservation_id": proof.reservation_id,
            "transport_phase": "MAY_HAVE_SENT",
            "outcome": "UNKNOWN",
        },
    }
    process = subprocess.run(
        ["./scripts/pt", "-B", "-c", worker, str(tmp_path), json.dumps(payload)],
        cwd=Path(__file__).resolve().parents[2],
        env=env,
        capture_output=True,
        text=True,
        timeout=40,
    )
    assert process.returncode == 0, (process.stdout, process.stderr)
    assert {path: path.read_bytes() for path in before_restart} == before_restart


def _assert_authenticated_occupied_mark_close(
    *,
    tmp_path,
    monkeypatch,
    context,
    bound,
    proof_root,
    proof,
    quantity,
    polled,
    dispatch,
    opener,
    shared_post=False,
    on_shared_send=None,
    direct=False,
    funding_case="",
):
    from src.ops.current_mf_n5_full_autonomy_occupied_lane_governed_cycle_n1_consumer_join_v1 import (
        invoke_join_v1 as occupied,
    )
    from src.ops.full_core_live_path_composition_root_v1.current_productive_persistent_natural_enter_convergence_v1 import (
        build_s8_occupied_lane_pairs_v1,
    )
    from src.ops.full_core_live_path_composition_root_v1.current_productive_governed_cycle_orchestrator_v1 import (
        LEDGER_FILENAME,
        read_retained_occupied_scope_close_v1,
    )
    from src.ops.portfolio_capital_reservation_budget_v1.host_v1 import (
        AuthenticatedEntryEpisodeRequestV1,
    )
    from src.ops.p5_productive_layered_core_authority_seam_v1.occupied_mark_state_v1 import (
        restore_layered_core_episode_v1,
    )
    from tests.ops import test_bounded_slot_connected_roundtrip_v1 as fixture
    from tests.ops.test_current_scope_mark_clock_v1 import provenance

    now = NOW.timestamp()
    event = now - 2
    pairs = build_s8_occupied_lane_pairs_v1(lane_state_root=tmp_path / "scope", bound=bound)
    root = Path(pairs["LANE_1"][0].lane_state_root)
    _, closes, _, _, _ = fixture.prepare(
        bound=bound,
        g17_typed_vol_producer=None,
        lane_state_root=root.parent,
        lane_id="LANE_1",
        arm_event_ts_unix=event - 20,
        g17_evidence_root=root,
    )
    prior = restore_layered_core_episode_v1(root, expected_instrument_id=bound.instrument_id)
    assert prior.regime.value == "bull"
    fixture.persist_applied_inventory(context.host.root / "reconciliation", context.observed, {})

    class Clock(datetime):
        @classmethod
        def now(cls, tz=None):
            return cls.fromtimestamp(now, tz)

    monkeypatch.setattr(occupied, "datetime", Clock)
    inputs = fixture.market(
        {"LANE_1": bound}, closes, event, "authenticated-mark", tmp_path / "g17"
    )
    mark = prior.running_reference.reference_price_r_t - 1.5 * prior.scope.d_t
    inputs.update(
        observed_unix=now,
        portfolio_budget_owner=context.host.owner,
        host_budget_recovery=context,
        occupied_scope_mark_lane_id="LANE_1",
        canonical_price_provenance_by_lane={
            "LANE_1": provenance(
                native=bound.venue_native_id,
                mark=mark,
                index=mark * 0.995,
                event=now - 0.125,
                captured=now,
            ),
        },
        authenticated_entry=AuthenticatedEntryEpisodeRequestV1(proof_root, proof),
    )
    if direct:
        from src.ops.full_core_live_path_composition_root_v1.envelope_bound_external_effect_send_seam_v1 import (
            _payload_from_envelope_v1,
        )
        from src.ops.full_core_live_path_composition_root_v1.final_order_envelope_v1 import (
            FinalOrderEnvelopeV1,
            assert_envelope_unmodified_v1,
        )
        from tests.ops.test_bounded_multislot_connected_cycle_v1 import ports

        def pretrade_inputs(decision_epoch, pretrade_cycle_id):
            observed_at = NOW.isoformat()
            carrier = ports(bound, decision_epoch, pretrade_cycle_id, account=context.account)
            limits = carrier.venue_quantity_limits
            limits = replace(
                limits,
                public_source=replace(limits.public_source, acquired_at_utc=observed_at),
                private_source=replace(limits.private_source, acquired_at_utc=observed_at),
            )
            return replace(
                carrier,
                observed_at=(NOW - timedelta(seconds=300)).isoformat()
                if funding_case == "-stale-capital"
                else observed_at,
                acquisition_decision_id=limits.acquisition_decision_id,
                venue_quantity_limits=replace(limits, integrity_digest=limits.digest_v1()),
            )

        inputs["live_29p_injected_by_lane"]["LANE_1"] = pretrade_inputs(
            NOW.isoformat(), "authenticated-mark:LANE_1"
        )

        def check_pre_dispatch(result, ledger):
            assert result.position_management_execution_handoff is None
            assert result.final_order_envelope is None
            if funding_case not in {
                "-funded",
                "-funded-timeout",
                "-funded-revoked",
                "-funded-booked",
                "-funded-exception-close",
            }:
                assert ledger["reason_code"] == (
                    "DIRECT_REVERSAL_FRESH_CAPITAL_REQUIRED"
                    if funding_case == "-stale-capital"
                    else "DIRECT_REVERSAL_FUNDED_LIVE_SLOT_REQUIRED"
                )
                assert result.position_management_reversal is None
                assert "direct_reversal_order" not in ledger
                return

            assert ledger["reason_code"] == "DIRECT_REVERSAL_EXECUTION_ADMISSION_REQUIRED"
            reversal = result.position_management_reversal
            assert reversal.episode.episode_id == proof.identity_digest
            assert reversal.old_reservation_id == proof.reservation_id
            assert reversal.episode.lane_id == "LANE_1"
            assert reversal.episode.instrument_id == bound.instrument_id
            assert reversal.selection_digest == bound.selection_integrity_digest
            assert reversal.slot_capital_basis_usdc == 25
            assert reversal.current_contracts == Decimal(quantity)
            assert reversal.target_contracts < 0
            assert reversal.protective_stop == reversal.reference_mark + reversal.scope_distance
            assert ledger["direct_reversal_digest"] == reversal.digest_v1()
            assert "occupied_scope_close" not in ledger
            order = ledger["direct_reversal_order"]
            assert order["venue_quantity_admission"]["allowed"]
            envelope = FinalOrderEnvelopeV1(**order["envelope"])
            assert_envelope_unmodified_v1(envelope)
            assert envelope.provenance_ref == reversal.digest_v1()
            body = _payload_from_envelope_v1(envelope)
            assert body["instId"] == bound.venue_native_id
            assert body["side"] == "sell" and body["posSide"] == "net"
            assert "reduceOnly" not in body
            assert Decimal(body["sz"]) == abs(
                reversal.target_contracts - reversal.current_contracts
            )
            if funding_case in {
                "-funded-timeout",
                "-funded-revoked",
                "-funded-booked",
                "-funded-exception-close",
            }:

                def after_timeout(record, submit_root):
                    from tests.ops.test_authenticated_net_reversal_booking_v1 import (
                        assert_original_net_reversal_booking_v1,
                    )

                    assert_original_net_reversal_booking_v1(
                        tmp_path=tmp_path,
                        monkeypatch=monkeypatch,
                        bound=bound,
                        proof_root=proof_root,
                        reversal=reversal,
                        envelope=envelope,
                        record=record,
                        submit_root=submit_root,
                        repository_sha=context.host.repository_sha,
                        closes=closes,
                        occupied=occupied,
                        exceptional_close=funding_case == "-funded-exception-close",
                    )

                _assert_direct_reversal_dispatch(
                    tmp_path,
                    envelope,
                    context,
                    proof_root,
                    pairs["LANE_1"],
                    inputs["authenticated_entry"],
                    revoked=funding_case == "-funded-revoked",
                    after_timeout=after_timeout
                    if funding_case in {"-funded-booked", "-funded-exception-close"}
                    else None,
                )
            elif not polled:
                _assert_direct_reversal_order_stops_at_original_post_admission(
                    tmp_path,
                    envelope,
                    context,
                    proof,
                    pairs["LANE_1"],
                    inputs["authenticated_entry"],
                )

    if direct and not polled:
        lane = occupied.invoke_occupied_lane_governed_cycle_n1_consumer_v1(pairs, **inputs)[
            "LANE_1"
        ]
        assert not lane.governed_cycle_result.permit_created
        assert lane.governed_cycle_result.post_count == 0
        check_pre_dispatch(
            lane.governed_cycle_result,
            json.loads((Path(lane.evidence_root) / LEDGER_FILENAME).read_bytes()),
        )
        return
    if polled:
        from src.ops.full_core_live_path_composition_root_v1 import (
            current_productive_governed_continuous_cycle_orchestrator_v1 as s6,
            current_productive_persistent_natural_enter_convergence_v1 as convergence,
        )
        from tests.ops import (
            test_current_productive_persistent_natural_enter_policy_governed_live_c1_v1 as policy_fixture,
        )
        from tests.ops.test_current_productive_persistent_natural_enter_convergence_v1 import (
            _continuous_auth,
        )

        monkeypatch.setattr(s6.time, "time", lambda: now)
        monkeypatch.setattr(convergence, "datetime", Clock)
        monkeypatch.setattr(
            convergence,
            "resolve_live_29p_injected_for_productive_s5_cycle_v1",
            lambda **kwargs: (
                pretrade_inputs(kwargs["decision_epoch"], kwargs["pretrade_cycle_id"])
                if direct
                else inputs["live_29p_injected_by_lane"]["LANE_1"]
            ),
        )
        floor = occupied._cursor_floor_or_zero(root)
        candles = inputs["candles_payload_by_lane"]["LANE_1"]

        def observation(price, source_time):
            return s6.InjectedContinuousObservationV1(
                candles_payload=candles,
                occupancy_payloads={},
                mark_price_payload={
                    "code": "0",
                    "data": [
                        {
                            "instId": bound.venue_native_id,
                            "markPx": str(price),
                            "idxPx": str(price * 0.995),
                            "ts": str(int(source_time * 1000)),
                        }
                    ],
                },
                mark_acquired_at_utc=NOW.isoformat(),
            )

        first = observation(
            prior.running_reference.reference_price_r_t - 0.25 * prior.scope.d_t, now - 0.25
        )
        policy_result = (
            convergence.run_policy_governed_persistent_natural_enter_live_c1_continuous_run_v1(
                authorization=replace(
                    _continuous_auth(native_id=bound.venue_native_id, max_cycles=2),
                    expected_cursor_floor=floor,
                ),
                origin_main_sha=policy_fixture.BASELINE_SHA,
                lane_state_root=tmp_path / "scope",
                bound=bound,
                g17_producers=inputs["g17_typed_vol_producers"],
                evidence_root=tmp_path / "continuous-mark",
                lock_root=tmp_path / "continuous-mark-lock",
                observation_source=s6.ScriptedContinuousObservationSourceV1(
                    [first, first, observation(mark, now - 0.125)]
                ),
                f1_m9_cycle_evaluator=policy_fixture._f1_m9_evaluator_factory(tmp_path),
                repo_root=policy_fixture.REPO,
                portfolio_budget_host=context.host,
                occupied_mark_proof_root=proof_root,
            )
        )
        run = policy_result.orchestrator_result
        if direct:
            assert run.disposition == s6.DISPOSITION_FAIL_CLOSED
            assert run.s5_invoke_count == 2 and run.accepted_c1_count == 0
            assert run.last_accepted_c1 == occupied._cursor_floor_or_zero(root) == floor
            assert all(cycle.final_order_envelope is None for cycle in run.cycle_records)
            assert not run.permit_created and run.post_count == 0
            terminal = run.cycle_records[-1]
            check_pre_dispatch(
                terminal,
                json.loads((Path(terminal.mark_evidence_root) / LEDGER_FILENAME).read_bytes()),
            )
            return
        assert run.disposition == s6.DISPOSITION_PRE_EXTERNAL_EFFECT, run.first_genuine_blocker
        assert run.s5_invoke_count == 2 and run.accepted_c1_count == 0
        assert [item.cycle_index for item in policy_result.iteration_evidence] == [0, 1, 2]
        assert run.last_accepted_c1 == occupied._cursor_floor_or_zero(root) == floor
        assert [cycle.mark_venue_event_time for cycle in run.cycle_records] == [
            now - 0.25,
            now - 0.125,
        ]
        assert run.cycle_records[0].final_order_envelope is None
        terminal = run.cycle_records[-1]
        parent = json.loads((tmp_path / "continuous-mark" / s6.LEDGER_FILENAME).read_bytes())
        assert parent["occupied_mark_cycles"][-1]["s5_evidence_root"] == terminal.mark_evidence_root
        handoff = terminal.position_management_execution_handoff
        assert handoff.l10_close.episode.episode_id == proof.identity_digest
        assert Decimal(handoff.envelope.quantity) == Decimal(quantity)
        assert (
            read_retained_occupied_scope_close_v1(Path(terminal.mark_evidence_root))["envelope"][
                "envelope_digest"
            ]
            == handoff.envelope.envelope_digest
        )
        assert not run.permit_created and run.post_count == 0
        assert run.cycle_records[0].position_close_post_context is None
        close_context = terminal.position_close_post_context
        assert close_context.execution == handoff
        if dispatch is not None:
            from src.ops.full_core_live_path_composition_root_v1 import (
                external_effect_permit_durable_consume_v1 as consume,
            )

            readback = (
                dispatch.removeprefix("readback-") if dispatch.startswith("readback-") else None
            )
            with monkeypatch.context() as patch:
                sent_at = NOW + timedelta(milliseconds=250)
                if readback is not None:
                    patch.setattr(consume, "_utc_now_iso_v1", sent_at.isoformat)
                if shared_post:
                    from src.ops.full_core_live_path_composition_root_v1 import (
                        current_productive_shared_post_owner_authority_v1 as shared_authority,
                    )

                    patch.setattr(shared_authority, "time", SimpleNamespace(time=sent_at.timestamp))
                shared_authorization = _assert_original_close_dispatch(
                    close_context,
                    "shared-timeout" if shared_post else "timeout" if readback else dispatch,
                    tmp_path,
                    now_unix=sent_at.timestamp() if shared_post else None,
                    on_shared_send=on_shared_send,
                )
            if readback is not None or dispatch == "kill":
                _assert_restarted_close_readback(
                    tmp_path,
                    monkeypatch,
                    close_context,
                    proof_root,
                    opener,
                    floor,
                    readback or "not-sent",
                    expected_switch_mark=mark,
                    shared_authorization=shared_authorization if shared_post else None,
                )
        return
    without_metadata = {**inputs, "live_29p_injected_by_lane": None}
    with pytest.raises(
        occupied.FullAutonomyOccupiedLaneGovernedCycleN1ConsumerJoinError,
        match="authenticated_scope_mark_close_metadata_required",
    ):
        occupied.invoke_occupied_lane_governed_cycle_n1_consumer_v1(pairs, **without_metadata)
    assert (
        restore_layered_core_episode_v1(root, expected_instrument_id=bound.instrument_id) == prior
    )
    lane = occupied.invoke_occupied_lane_governed_cycle_n1_consumer_v1(pairs, **inputs)["LANE_1"]
    result = lane.governed_cycle_result
    handoff = result.position_management_execution_handoff
    assert handoff is not None, (result.first_genuine_blocker, result.reason_code)
    decision = lane.s7_invocation.cycle_result.replay.intermediate.entry_exit_decision
    assert handoff.l10_close is not None, (decision.exit_class, decision.reason_codes)
    assert handoff.l10_close.episode.episode_id == proof.identity_digest
    assert handoff.l10_close.target_side == "short"
    assert handoff.envelope.instrument_id == bound.venue_native_id
    assert handoff.envelope.reduce_only is True
    assert Decimal(handoff.envelope.quantity) == Decimal(quantity)
    assert not result.permit_created and result.post_count == 0
    retained = read_retained_occupied_scope_close_v1(Path(lane.evidence_root))
    assert retained["envelope"]["envelope_digest"] == handoff.envelope.envelope_digest
    assert retained["binding"]["entry_source_ref"] == handoff.l10_close.entry_source_ref
    floor = occupied._cursor_floor_or_zero(root)
    from src.ops.n1_standing_pre_external_runtime_supervisor_v1 import supervisor_v1 as supervisor
    from src.ops.portfolio_capital_reservation_budget_v1 import host_v1 as budget_host
    from tests.ops.test_current_productive_persistent_natural_enter_convergence_v1 import (
        _continuous_auth,
    )

    previous_host = context.host
    previous_hold = previous_host.owner.active_sum_v1()
    previous_host.close()
    restarted_at = NOW + timedelta(seconds=1)
    monkeypatch.setattr(wire, "utc_now_iso_v1", restarted_at.isoformat)
    restarted_hosts = []

    def open_host(**kwargs):
        # The original fixture's durable root predates the supervisor layout.
        host = PortfolioBudgetHostV1(
            **{**kwargs, "root": previous_host.root, "clock": restarted_at.timestamp}
        )
        restarted_hosts.append(host)
        return host

    monkeypatch.setattr(budget_host, "PortfolioBudgetHostV1", open_host)

    def forbidden(*_args, **_kwargs):
        pytest.fail("Pending close must resume before public data, ranking and new cycle admission")

    config = supervisor.StandingSupervisorConfigV1(
        public_store_root=tmp_path / "public",
        private_store_root=tmp_path / "private",
        lane_state_root=tmp_path / "scope",
        evidence_root=tmp_path / "restart" / "new-host-session",
        expected_account_identity=previous_host.expected_account_identity,
        venue_native_id=bound.venue_native_id,
        canonical_instrument_id=bound.instrument_id,
        transport_scope=supervisor.TRANSPORT_SCOPE_SCOPED_READONLY_GET,
    )
    run_args = dict(
        config=config,
        origin_main_sha=previous_host.repository_sha,
        bound=bound,
        authorization=replace(
            _continuous_auth(native_id=bound.venue_native_id, max_cycles=1),
            expected_cursor_floor=floor,
        ),
        observation_source=None,
        g17_producers={},
        f1_m9_cycle_evaluator=forbidden,
        public_rest_fetch=forbidden,
        private_rest_fetch=previous_host.fetch,
        pretrade_transport=previous_host.reconciliation_transport,
        wp02_hook=forbidden,
        skip_owner_go_validation=True,
        occupied_mark_proof_root=proof_root,
    )
    resumed = supervisor.run_n1_standing_pre_external_supervisor_v1(**run_args)
    assert resumed.resumed_position_management_close == handoff
    assert resumed.ok and not resumed.owner_go_consumed and resumed.policy_result is None
    assert not resumed.trace.wp02_hook_invoked and resumed.trace.post_count == 0
    assert restarted_hosts[-1].closed and restarted_hosts[-1].owner.active_sum_v1() == previous_hold
    assert occupied._cursor_floor_or_zero(root) == floor
    assert read_retained_occupied_scope_close_v1(Path(lane.evidence_root)) == retained

    ledger_path = Path(lane.evidence_root) / LEDGER_FILENAME
    ledger = json.loads(ledger_path.read_bytes())
    ledger["occupied_scope_close"]["binding"]["scope_digest"] = "0" * 64
    ledger_path.write_text(json.dumps(ledger))
    with pytest.raises(ValueError, match="RETAINED_CLOSE_READBACK_INVALID"):
        supervisor.run_n1_standing_pre_external_supervisor_v1(**run_args)
    assert restarted_hosts[-1].closed and restarted_hosts[-1].owner.active_sum_v1() == previous_hold


def _assert_original_close_dispatch(context, case, tmp_path, *, now_unix=None, on_shared_send=None):
    from src.ops.full_core_live_path_composition_root_v1 import (
        full_core_productive_http_post_transport_v1 as http_post,
    )
    from src.ops.full_core_live_path_composition_root_v1.current_productive_one_shot_fresh_envelope_permit_mint_durable_consume_and_post_join_v1 import (
        POST_OWNER_GO,
        CurrentProductiveOneShotFreshEnvelopeJoinError,
        attempt_current_productive_one_shot_fresh_envelope_permit_mint_durable_consume_and_post_join_v1 as send,
    )
    from src.ops.full_core_live_path_composition_root_v1.external_effect_permit_durable_consume_v1 import (
        load_external_effect_durable_consume_v1,
    )
    from src.ops.full_core_live_path_composition_root_v1.current_productive_actual_venue_post_owner_go_durable_consume_v1 import (
        SHARED_POST_OWNER_CLAIM_FIELD,
        load_durable_post_owner_go_consume_v1,
    )
    from src.ops.full_core_live_path_composition_root_v1.current_productive_shared_post_owner_authority_v1 import (
        SharedPostOwnerAuthorityError,
    )
    from src.ops.governed_productive_account_equity_authority_producer_v1 import (
        current_productive_actual_venue_post_with_fresh_envelope_bound_single_use_permit_v1 as actual,
    )
    from tests.ops.test_current_productive_actual_venue_post_with_fresh_envelope_bound_single_use_permit_v1 import (
        MockCurrentProductive29PIntegrityBackendV1,
    )
    from tests.ops.test_current_productive_shared_post_owner_authority_v1 import (
        _backup_post_store,
        _claim_rows,
        revoke,
        signed_post_authorization,
    )

    host = context.recovery.host
    envelope = context.execution.envelope
    store_root = context.store_root_v1()
    requests = []
    authorization, authority_key = (
        signed_post_authorization(
            tmp_path,
            envelope,
            account=context.recovery.account,
            action="L10_CLOSE",
            now_unix=now_unix,
        )
        if case.startswith("shared")
        else (None, None)
    )

    class Opener:
        @contextmanager
        def open(self, request, timeout):
            assert request.get_method() == "POST"
            payload = json.loads(request.data)
            assert payload == {
                "clOrdId": envelope.client_order_id,
                "instId": envelope.instrument_id,
                "side": envelope.side,
                "ordType": "market",
                "sz": envelope.quantity,
                "tdMode": envelope.td_mode,
                "reduceOnly": True,
                **({"posSide": envelope.pos_side} if envelope.pos_side else {}),
            }
            record = load_external_effect_durable_consume_v1(store_root=store_root)["record"]
            assert record["transport_attempt"]["phase"] == "MAY_HAVE_SENT"
            requests.append(payload)
            if case == "shared-timeout":
                # The grant, local witness and permit must already name the original
                # close attempt when the simulated socket is reached.
                attempt = record["transport_attempt"]
                assert record["envelope_digest"] == authorization.grant.envelope_digest
                witness = load_durable_post_owner_go_consume_v1(store_root=store_root)["record"]
                with closing(
                    sqlite3.connect(authorization.authority.path.as_uri() + "?mode=ro", uri=True)
                ) as db:
                    assert db.execute(
                        "SELECT grant_id, grant_digest, claim_digest, consumed_at, "
                        "dispatch_started_at FROM claims"
                    ).fetchall() == [
                        (
                            authorization.grant.grant_id,
                            sha256(authorization.grant.signing_bytes_v1()).hexdigest(),
                            witness[SHARED_POST_OWNER_CLAIM_FIELD],
                            now_unix,
                            datetime.fromisoformat(attempt["socket_boundary_at_utc"]).timestamp(),
                        )
                    ]
                if on_shared_send is not None:
                    on_shared_send(context, authorization, record)
            if case in {"timeout", "shared-timeout"}:
                raise TimeoutError("intercepted close submit")
            if case == "venue-timeout":
                raise HTTPError(
                    request.full_url, 400, "Bad Request", {}, BytesIO(b'{"code":"50004"}')
                )

            class Response:
                status = 200
                url = request.full_url

                def read(self):
                    return json.dumps(
                        {
                            "code": "0",
                            "data": [
                                {
                                    "sCode": "0",
                                    "clOrdId": envelope.client_order_id,
                                    "ordId": "91234",
                                }
                            ],
                        }
                    ).encode()

            yield Response()

    class RedirectResponseHandler(BaseHandler):
        handler_order = 100

        def https_open(self, request):
            assert request.host == http_post.AUTHORIZED_HOST
            assert request.has_header("Ok-access-sign")
            requests.append(request)
            response = addinfourl(
                BytesIO(b'{"code":"1"}'),
                {"location": "https://redirect.invalid/api/v5/trade/order"},
                request.full_url,
                302,
            )
            response.msg = "Found"
            return response

    class ForeignKeychain(_FakeKeychainBackend):
        def copy_matching_generic_password_value_data_v1(self, **kwargs):
            material = json.loads(super().copy_matching_generic_password_value_data_v1(**kwargs))
            material["apiKey"] = "different-test-key"
            return json.dumps(material).encode()

    def opener_factory():
        if case == "kill":
            StatePersistence(str(host.execution_incident_state_path)).save(KillSwitchState.KILLED)
        if case == "stale-position":
            host.clock = lambda: NOW.timestamp() + 6
        if case == "shared-stale-snapshot":
            snapshot = tmp_path / "close-before-revocation.sqlite3"
            _backup_post_store(authorization, snapshot)
            revoke(authorization, authority_key)
            shutil.copyfile(snapshot, authorization.authority.path)
        elif case == "shared-revoked":
            revoke(authorization, authority_key)
        return Opener()

    signing_backend = ForeignKeychain() if case == "wrong-key" else _FakeKeychainBackend()
    low_args = dict(
        envelope=envelope,
        post_position_close_context=context,
        post_owner_go=POST_OWNER_GO,
        store_root=store_root,
        k1_backend=signing_backend,
        opener_factory=opener_factory,
    )
    with pytest.raises(
        CurrentProductiveOneShotFreshEnvelopeJoinError, match="CLOSE_POST_OWNER_GO_REQUIRED"
    ):
        send(**low_args)
    assert not store_root.exists()
    with pytest.raises(
        CurrentProductiveOneShotFreshEnvelopeJoinError, match="CLOSE_SUBMIT_STORE_MISMATCH"
    ):
        send(**{**low_args, "store_root": tmp_path / "foreign-close-submit"})
    submit = actual.execute_current_productive_actual_l10_close_v1
    args = dict(
        context=context,
        owner_go=POST_OWNER_GO,
        baseline_origin_main_sha=actual.EXPECTED_BASELINE_ORIGIN_MAIN_SHA,
        perform_real_venue_post=True,
        k1_backend=signing_backend,
        opener_factory=opener_factory,
        execution_integrity_backend=MockCurrentProductive29PIntegrityBackendV1(
            origin_main=host.repository_sha, head=host.repository_sha, drift=""
        ),
    )
    with pytest.raises(
        actual.CurrentProductiveActualVenuePostError, match="ACTUAL_CLOSE_POST_OWNER_GO_REQUIRED"
    ):
        submit(**{**args, "owner_go": ""})
    assert not load_external_effect_durable_consume_v1(store_root=store_root)["durable_consumed"]
    if authorization is not None:
        foreign_grant = replace(authorization.grant, issuer_id="foreign")
        foreign_grant = replace(
            foreign_grant, signature=authority_key.sign(foreign_grant.signing_bytes_v1()).signature
        )
        with pytest.raises(
            actual.CurrentProductiveActualVenuePostError,
            match="POST_GRANT_ISSUER_OR_STORE_MISMATCH",
        ):
            submit(
                **args, shared_post_owner_authorization=replace(authorization, grant=foreign_grant)
            )
        assert not store_root.exists()
        args["shared_post_owner_authorization"] = authorization
    denials = {
        "wrong-key": "K1_VENUE_CREDENTIAL_MISMATCH",
        "kill": "POST_SAFETY_DURABLE_VETO:BEFORE_SOCKET",
        "stale-position": "BEFORE_SOCKET:HOST_AUTHENTICATED_ENTRY_OBSERVATION_UNPROVEN",
        "shared-revoked": "POST_GRANT_REVOKED",
        "shared-stale-snapshot": "POST_AUTHORITY_CHECKPOINT_MISMATCH",
    }
    if case in denials:
        reason = denials[case]
        with pytest.raises(actual.CurrentProductiveActualVenuePostError, match=reason):
            submit(**args)
        assert requests == []
        record = load_external_effect_durable_consume_v1(store_root=store_root)["record"]
        assert record["durable_state"] == "ABORTED_BEFORE_TRANSPORT"
        if authorization is not None:
            assert _claim_rows(authorization) == [(authorization.grant.grant_id, 0)]
        return

    if case == "redirect":
        from unittest.mock import patch

        def build_with_redirect(*handlers):
            return build_opener(RedirectResponseHandler(), *handlers)

        with patch.object(http_post, "build_opener", build_with_redirect):
            result = submit(**{**args, "opener_factory": None})
    else:
        result = submit(**args)
    assert result.http_post_attempts == 1
    # The production opener branch counts a response even when urllib's HTTPS
    # handler was replaced by a local fixture.
    assert result.external_effect_count == int(case == "redirect")
    assert result.post_submit_join.client_order_id == envelope.client_order_id
    assert result.post_submit_join.typed_outcome == (
        "UNKNOWN"
        if case in {"timeout", "shared-timeout", "venue-timeout", "redirect"}
        else "ACKNOWLEDGED"
    )
    if result.post_submit_join.typed_outcome == "UNKNOWN":
        assert result.post_submit_join.exchange_query_before_retry_required
    assert result.post_submit_join.resubmit_allowed is False
    assert result.post_submit_join.fill_observed is False
    if authorization is not None:
        assert _claim_rows(authorization) == [(authorization.grant.grant_id, 1)]
        authorization = replace(authorization, authority=replace(authorization.authority))
        args["shared_post_owner_authorization"] = authorization
        if case == "shared-timeout":
            with pytest.raises(SharedPostOwnerAuthorityError, match="POST_GRANT_ALREADY_CONSUMED"):
                authorization.consume_v1(
                    account=context.recovery.account,
                    action="L10_CLOSE",
                    envelope_digest=envelope.envelope_digest,
                    attempt_root=tmp_path / "second-close-attempt",
                )
    with pytest.raises(actual.CurrentProductiveActualVenuePostError, match="CONSUMED_PERMIT"):
        submit(**args)
    assert len(requests) == 1
    return authorization


def _assert_invalid_close_page_receipts_are_rejected(
    *, owner, execution, proof_root, close, history, repository_sha
):
    """Use digest-consistent copies so the booking reader must check the GET sequence."""

    def publish_copy(prefix, record):
        digest = sha256(store._encode(record)).hexdigest()
        path = proof_root / f"{prefix}-{digest}.json"
        store._publish(path, store._encode({"record": record, "sha256": digest}) + b"\n")
        return path, digest

    gets = close["gets"]
    paged = close["schema"] != store.CLOSE_GET_PROOF_V1
    assert len(gets) == (8 if paged else 6)
    index = 3 if paged else 2
    order_history = gets[index]
    endpoint = order_history["endpoint"]
    assert endpoint.startswith("/api/v5/trade/orders-history?")
    wrong_cursor = {**order_history, "endpoint": f"{endpoint.split('&after=', 1)[0]}&after=99999"}
    wrong_instrument = {
        **order_history,
        "endpoint": endpoint.replace(execution.envelope.instrument_id, "foreign-instrument"),
    }
    mismatched = "GET_PROOF_REPLAY_REQUEST_MISMATCH"
    wrong_count = "L10_CLOSE_BOOKING_ORIGINAL_GETS_UNPROVEN"
    for changed, reason in (
        (gets[:index] + gets[index + 1 :], mismatched if paged else wrong_count),
        (gets + [gets[-1]], "L10_CLOSE_BOOKING_EXTRA_GETS" if paged else wrong_count),
        (gets[:index] + [wrong_cursor] + gets[index + 1 :], mismatched),
        (gets[:index] + [wrong_instrument] + gets[index + 1 :], mismatched),
        (gets[:index] + [gets[index + 1], order_history] + gets[index + 2 :], mismatched),
    ):
        _, digest = publish_copy("close", {**close, "gets": changed})
        path, _ = publish_copy("close-history", {**history, "close_proof_digest": digest})
        with pytest.raises(ValueError, match=f"^{reason}$"):
            owner.record_authenticated_l10_close_v1(
                execution=execution,
                proof_path=path,
                proof_root=proof_root,
                repository_sha=repository_sha,
                offline_l10_close=close["schema"] == store.OFFLINE_CLOSE_GET_PROOF_V2,
            )


def _assert_close_booking_in_fresh_process(
    *, original_host, lane_state_root, proof_root, bound, booking, sizing
):
    replay = """
from contextlib import closing
from dataclasses import asdict
import json
from pathlib import Path
import sys

def forbid_network(event, args):
    if event.startswith("socket."):
        raise AssertionError("booked close readback attempted a socket operation")

sys.addaudithook(forbid_network)
from src.ops.full_core_live_path_composition_root_v1.current_productive_enter_live_29p_join_v1 import (
    check_authenticated_double_play_29p_admission_v1,
)
from src.ops.full_core_live_path_composition_root_v1.current_productive_l10_close_reconciliation_v1 import (
    reconcile_submitted_occupied_scope_close_v1,
)
from src.ops.full_core_live_path_composition_root_v1.current_productive_persistent_natural_enter_convergence_v1 import (
    build_s8_occupied_lane_pairs_v1,
)
from src.ops.full_core_live_path_composition_root_v1.productive_read_only_get_transport_v1 import (
    FullCoreProductiveReadOnlyGetTransportV1,
)
from src.ops.portfolio_capital_reservation_budget_v1.host_v1 import PortfolioBudgetHostV1
from src.ops.single_selected_future_runtime_binding_v1.models_v1 import BoundInstrumentV1

def forbidden_fetch(*args, **kwargs):
    raise AssertionError("booked close readback requested new account data")

data = json.loads(sys.argv[1])
bound = BoundInstrumentV1(**data["bound"])
lane_pair = build_s8_occupied_lane_pairs_v1(
    lane_state_root=Path(data["lane_state_root"]), bound=bound,
)["LANE_1"]
transport = FullCoreProductiveReadOnlyGetTransportV1()
with closing(PortfolioBudgetHostV1(
    root=Path(data["budget_root"]),
    private_rest_fetch=forbidden_fetch,
    repository_sha=data["repository_sha"],
    session_id="fresh-process-close-readback",
    expected_account_identity=data["account"],
    reconciliation_transport=transport,
)) as host:
    proof_root = Path(data["proof_root"])
    close = reconcile_submitted_occupied_scope_close_v1(
        lane_pair=lane_pair, budget_host=host, proof_root=proof_root,
    )
    assert close.status == "CLOSE_NET_BOOKED"
    sizing = check_authenticated_double_play_29p_admission_v1(
        request=close.counter_order_request, bound_instrument=bound,
        owner=host.owner, proof_root=proof_root,
    )
    hold, = (
        row for row in host.owner.local_commitment_readback_v1().commitments
        if row.reservation_id == close.net_booking["reservation_id"]
    )
    assert hold.state == "COMMITTED" and hold.slot_id == close.net_booking["slot_id"]
    assert host.owner.read_authenticated_l10_close_v1(close.net_booking["episode_id"]) == close.net_booking
    assert not transport.methods_used and sizing.get_count == 0
    assert not sizing.venue_plan_authorized and not sizing.portfolio_reservation_id
    print(json.dumps({
        "booking": close.net_booking,
        "blocker": sizing.first_blocker,
        "reasons": list(sizing.reason_codes),
        "timing": asdict(sizing.authenticated_close_timing),
    }))
"""
    args = {
        "bound": bound.to_dict(),
        "lane_state_root": str(lane_state_root),
        "budget_root": str(original_host.root),
        "repository_sha": original_host.repository_sha,
        "account": original_host.expected_account_identity,
        "proof_root": str(proof_root),
    }
    repo = Path(__file__).resolve().parents[2]
    process = subprocess.run(
        ["./scripts/pt", "-c", replay, json.dumps(args)],
        cwd=repo,
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert process.returncode == 0, process.stderr
    assert json.loads(process.stdout.splitlines()[-1]) == {
        "booking": booking,
        "blocker": sizing.first_blocker,
        "reasons": list(sizing.reason_codes),
        "timing": asdict(sizing.authenticated_close_timing),
    }


def _close_http_fixture(envelope, case, *, original_body, productive_paged, on_history=None):
    product = "SWAP" if envelope.instrument_id.endswith("-SWAP") else "FUTURES"
    currency = "USDC" if product == "FUTURES" else "USDT"
    quantity = Decimal(envelope.quantity)
    partial = case in {"partial", "stale-residual"}
    filled = quantity / 2 if partial else quantity
    stamp = int(NOW.timestamp() * 1000)
    order = {
        "instId": envelope.instrument_id,
        "instType": product,
        "clOrdId": envelope.client_order_id,
        "ordId": "91234",
        "side": envelope.side,
        "posSide": "net",
        "tdMode": envelope.td_mode,
        "ordType": envelope.order_type,
        "reduceOnly": "false" if case == "wrong-order" else "true",
        "state": "canceled" if partial else "filled",
        "sz": str(quantity),
        "accFillSz": str(filled),
        "uTime": str(stamp + 500),
    }
    fill = {
        **{
            key: order[key] for key in ("instId", "instType", "clOrdId", "ordId", "side", "posSide")
        },
        "tradeId": "123",
        "billId": "92234",
        "fillSz": str(filled),
        "fillPx": "1996",
        "fillTime": str(stamp + 400),
        "fillPnl": "0.15",
        "fee": "-0.02",
        "feeCcy": currency,
    }
    paged = case.startswith("paged-")
    with_history = case in {"booked", "paged-booked", "owner-go-lost"} or case.startswith(
        "history-"
    )

    def close_body(path, params):
        if path.endswith("/config"):
            return original_body(path, params)
        assert params["instId"] == envelope.instrument_id
        code, rows = "0", []
        if path.endswith("/positions-history"):
            assert with_history
            if on_history is not None:
                on_history()
            assert params == {
                "instId": envelope.instrument_id,
                "instType": product,
                "mgnMode": "cross",
                "posId": "8923",
                "limit": "100",
            }
            if case != "history-missing":
                rows = [
                    {
                        "instId": envelope.instrument_id if case != "history-foreign" else "other",
                        "instType": product,
                        "posSide": "net",
                        "mgnMode": "cross",
                        "ccy": currency,
                        "direction": "long" if envelope.side == "sell" else "short",
                        "posId": "8923",
                        "cTime": str(stamp - 1000),
                        "uTime": str(stamp + 500),
                        "type": "2",
                        "openMaxPos": str(quantity),
                        "closeTotalPos": str(quantity),
                        "pnl": "0.15",
                        "fee": "-0.05",
                        "fundingFee": "-0.01",
                        "liqPenalty": "0",
                        "settledPnl": "0.04" if product == "FUTURES" else "",
                        "realizedPnl": "0.13"
                        if product == "FUTURES"
                        else "0.99"
                        if case == "history-conflict"
                        else "0.09",
                    }
                ]
        elif paged and path.endswith(("/orders-history", "/fills")):
            is_fill = path.endswith("/fills")
            row, cursor_key = (fill, "billId") if is_fill else (order, "ordId")
            start = 200000 if is_fill else 100000
            if "after" in params:
                assert params["after"] == str(start - 99)
                if productive_paged and case == "paged-missing" and is_fill:
                    raise TimeoutError("simulated missing fills continuation")
                rows = [row]
                if case == "paged-foreign" and is_fill:
                    rows = [{**row, "instId": "foreign-instrument", "clOrdId": "foreign-order"}]
                if case == "paged-foreign-product" and is_fill:
                    rows = [{**row, "instType": "SPOT", "clOrdId": "foreign-order"}]
            else:
                rows = [
                    {**row, cursor_key: str(i), "ordId": str(i), "clOrdId": f"unrelated-{i}"}
                    for i in range(start, start - 100, -1)
                ]
        elif case == "paged-open-orders" and path.endswith("/orders-pending"):
            rows = [
                {**order, "ordId": str(i), "clOrdId": f"unrelated-{i}", "state": "live"}
                for i in (range(300000, 299900, -1) if "after" not in params else [299900])
            ]
        elif case == "unseen":
            if path.endswith("/order"):
                code = "51603"
        elif path.endswith("/order") or (
            path.endswith("/orders-history") and case != "no-flat-anchor"
        ):
            rows = [order]
        elif path.endswith("/fills") and case != "missing-fill":
            rows = [fill]
        elif path.endswith("/positions") and partial:
            remaining = quantity - filled
            rows = [
                {
                    "instId": envelope.instrument_id,
                    "instType": product,
                    "posSide": "net",
                    "mgnMode": envelope.td_mode,
                    "pos": str(remaining if envelope.side == "sell" else -remaining),
                    "uTime": str(stamp + (300 if case == "stale-residual" else 600)),
                }
            ]
        if case == f"page-{path.rsplit('/', 1)[-1]}":
            # A full first page leaves coverage open even with the matching
            # close order, full fill and empty scoped position response.
            if path.endswith("/fills"):
                template, row_ids = fill, ("ordId", "billId", "tradeId")
            elif path.endswith("/orders-pending"):
                template, row_ids = {**order, "state": "live", "accFillSz": "0"}, ("ordId",)
            else:
                template, row_ids = order, ("ordId",)
            count = int(params.get("limit", "100")) - len(rows)
            rows.extend(
                {**template, **dict.fromkeys(row_ids, str(i)), "clOrdId": f"unrelated-{i}"}
                for i in range(1000, 1000 - count, -1)
            )
        return json.dumps({"code": code, "data": rows}).encode()

    return close_body, order, fill, currency, with_history


def _paged_close_requests(envelope, product, case, with_history):
    scope_query = {"instType": product, "instId": envelope.instrument_id}
    list_query = {**scope_query, "limit": "100"}
    requests = [("/api/v5/account/config", {}), ("/api/v5/trade/orders-pending", scope_query)]
    if case == "paged-open-orders":
        requests.append(("/api/v5/trade/orders-pending", {**scope_query, "after": "299901"}))
    requests.extend(
        [
            ("/api/v5/trade/orders-history", list_query),
            ("/api/v5/trade/orders-history", {**list_query, "after": "99901"}),
            ("/api/v5/trade/fills", list_query),
            ("/api/v5/trade/fills", {**list_query, "after": "199901"}),
            ("/api/v5/account/positions", {"instId": envelope.instrument_id}),
            (
                "/api/v5/trade/order",
                {"instId": envelope.instrument_id, "clOrdId": envelope.client_order_id},
            ),
        ]
    )
    if with_history:
        requests.append(
            (
                "/api/v5/account/positions-history",
                {
                    **scope_query,
                    "mgnMode": "cross",
                    "posId": "8923",
                    "limit": "100",
                },
            )
        )
    return requests


def _run_shared_close_crash_stage(root, stage):
    """Each stage runs in a new interpreter against the same disposable stores."""
    from src.ops.full_core_live_path_composition_root_v1 import (
        checkout_independent_credential_os_native_store_acquisition_v1 as native,
    )
    from src.ops.full_core_live_path_composition_root_v1.current_productive_enter_live_29p_join_v1 import (
        check_authenticated_double_play_29p_admission_v1,
    )
    from src.ops.full_core_live_path_composition_root_v1.current_productive_l10_close_reconciliation_v1 import (
        reconcile_submitted_occupied_scope_close_v1,
    )
    from src.ops.full_core_live_path_composition_root_v1.current_productive_persistent_natural_enter_convergence_v1 import (
        build_s8_occupied_lane_pairs_v1,
    )
    from src.ops.portfolio_capital_reservation_budget_v1.contract_v1 import (
        PortfolioCapitalReservationBudgetOwnerV1,
    )
    from src.ops.single_selected_future_runtime_binding_v1.models_v1 import BoundInstrumentV1
    from tests.ops._current_productive_pre_external_test_process_isolation_v1 import (
        establish_current_productive_pre_external_test_process_isolation_v1,
    )

    inputs_path = root / "after-send-boundary.json"
    proof_root = root / "private-get-evidence"

    def kill_after_receipt(path, data):
        # This receipt is harness evidence. The production writer has already
        # committed its own state before the hook is called.
        path.write_text(json.dumps({"pid": os.getpid(), **data}))
        os.kill(os.getpid(), signal.SIGKILL)

    def forbidden(*args, **kwargs):
        pytest.fail("close crash probe requested an unplanned transport or account read")

    with pytest.MonkeyPatch.context() as patch:
        patch.setattr(native, "_sec_item_copy_matching_generic_password_payloads_v1", forbidden)
        if stage == "send":
            establish_current_productive_pre_external_test_process_isolation_v1(
                monkeypatch=patch, f1_root=root / "isolated-f1", reseed_workspace_f1_m9=False
            )
            proof_root.mkdir(mode=0o700)

            def at_socket(context, authorization, permit):
                host = context.recovery.host
                envelope = context.execution.envelope
                account = authorization.grant.account
                close_body, _, _, _, with_history = _close_http_fixture(
                    envelope,
                    "paged-booked",
                    original_body=lambda path, params: json.dumps(
                        _fetch(uid=account)(path, params)
                    ).encode(),
                    productive_paged=True,
                )
                responses = [
                    (path, query, close_body(path, query).decode())
                    for path, query in _paged_close_requests(
                        envelope, "FUTURES", "paged-booked", with_history
                    )
                ]
                kill_after_receipt(
                    inputs_path,
                    {
                        "budget_root": str(host.root),
                        "revision": host.repository_sha,
                        "account": account,
                        "bound": context.lane_pair[1].to_dict(),
                        "episode_id": context.execution.l10_close.episode.episode_id,
                        "reservation_id": context.authenticated_entry.proof.reservation_id,
                        "clordid": envelope.client_order_id,
                        "permit": permit,
                        "post_store": str(authorization.authority.path),
                        "checkpoint": str(authorization.authority.checkpoint_path),
                        "submit_root": str(context.store_root_v1()),
                        "responses": responses,
                    },
                )

            test_futures_reconciliation_uses_bound_product_through_private_replay(
                root,
                patch,
                proof_root,
                "double-play-shared-productive-paged-net",
                on_shared_send=at_socket,
            )
            pytest.fail("the simulated POST returned instead of being killed at MAY_HAVE_SENT")

        data = json.loads(inputs_path.read_bytes())
        bound = BoundInstrumentV1(**data["bound"])
        lane_pair = build_s8_occupied_lane_pairs_v1(lane_state_root=root / "scope", bound=bound)[
            "LANE_1"
        ]
        restart_time = NOW + timedelta(seconds=1)
        patch.setattr(wire, "utc_now_iso_v1", restart_time.isoformat)

        opener = SignedReconciliationHttpFixture(SimpleNamespace(account_identity=data["account"]))
        responses = {
            (path, tuple(sorted(query.items()))): body.encode()
            for path, query, body in data["responses"]
        }
        opener.body = lambda path, query: responses[path, tuple(sorted(query.items()))]
        patch.setattr(wire, "build_opener", forbidden)

        if stage == "book":
            patch.setattr(wire, "build_opener", lambda *handlers: opener)
            record_close = (
                PortfolioCapitalReservationBudgetOwnerV1.record_authenticated_l10_close_v1
            )

            def record_and_kill(owner, **kwargs):
                booking = record_close(owner, **kwargs)
                assert booking["episode_id"] == data["episode_id"]
                assert booking["reservation_id"] == data["reservation_id"]
                kill_after_receipt(
                    root / "after-booking-commit.json",
                    {"booking": booking, "gets": opener.requests},
                )

            patch.setattr(
                PortfolioCapitalReservationBudgetOwnerV1,
                "record_authenticated_l10_close_v1",
                record_and_kill,
            )

        with (
            open_governed_live_c1_get_only_fresh_pretrade_transport_v1(
                max_request_count=len(responses), k1_lookup_backend=_FakeKeychainBackend()
            ) as (transport, _),
            closing(
                PortfolioBudgetHostV1(
                    root=Path(data["budget_root"]),
                    private_rest_fetch=forbidden,
                    repository_sha=data["revision"],
                    session_id=f"shared-close-crash-{stage}",
                    expected_account_identity=data["account"],
                    clock=restart_time.timestamp,
                    reconciliation_transport=transport,
                )
            ) as host,
        ):
            close = reconcile_submitted_occupied_scope_close_v1(
                lane_pair=lane_pair, budget_host=host, proof_root=proof_root
            )
            assert stage == "replay" and close.status == "CLOSE_NET_BOOKED"
            booking = close.net_booking
            assert close.counter_order_request.net_booking.to_dict_v1() == booking
            sizing = check_authenticated_double_play_29p_admission_v1(
                request=close.counter_order_request,
                bound_instrument=bound,
                owner=host.owner,
                proof_root=proof_root,
            )
            (hold,) = host.owner.local_commitment_readback_v1().commitments
            assert (hold.reservation_id, hold.slot_id, hold.state) == (
                data["reservation_id"],
                booking["slot_id"],
                "COMMITTED",
            )
            assert not transport.methods_used and sizing.get_count == 0
            assert not sizing.venue_plan_authorized and not sizing.portfolio_reservation_id
            (root / "after-restart-29p.json").write_text(
                json.dumps(
                    {
                        "pid": os.getpid(),
                        "booking": booking,
                        "blocker": sizing.first_blocker,
                        "reasons": sizing.reason_codes,
                        "timing": asdict(sizing.authenticated_close_timing),
                        "gets": transport.methods_used,
                        "venue_plan_authorized": sizing.venue_plan_authorized,
                        "new_reservation_id": sizing.portfolio_reservation_id,
                    }
                )
            )


def test_shared_l10_close_recovery_after_send_and_booking_sigkill(tmp_path):
    from src.ops.full_core_live_path_composition_root_v1.external_effect_permit_durable_consume_v1 import (
        load_external_effect_durable_consume_v1,
    )

    worker = """
from pathlib import Path
import sys

def deny_sockets(event, args):
    if event.startswith("socket."):
        raise AssertionError("real sockets are unavailable in the close crash probe")

sys.addaudithook(deny_sockets)
from tests.ops.test_execution_reconciliation_get_provenance_v1 import _run_shared_close_crash_stage
_run_shared_close_crash_stage(Path(sys.argv[1]), sys.argv[2])
"""

    env = os.environ.copy()
    if env.get("GITHUB_ACTIONS") == "true":
        env.update(PT_RUNTIME_MODE="provisioned", PT_PROVISIONED_PYTHON=sys.executable)

    def run_stage(stage, expected_status):
        proc = subprocess.run(
            ["./scripts/pt", "-B", "-c", worker, str(tmp_path), stage],
            cwd=Path(__file__).resolve().parents[2],
            env=env,
            capture_output=True,
            text=True,
            timeout=40,
        )
        assert proc.returncode == expected_status, (proc.returncode, proc.stdout, proc.stderr)

    def read_rows(path, query):
        with closing(sqlite3.connect(path.as_uri() + "?mode=ro", uri=True)) as db:
            return db.execute(query).fetchall()

    run_stage("send", -signal.SIGKILL)
    send = json.loads((tmp_path / "after-send-boundary.json").read_bytes())
    post_store, checkpoint, submit_root = map(
        Path, (send["post_store"], send["checkpoint"], send["submit_root"])
    )
    budget = Path(send["budget_root"]) / "owner/reservations.sqlite3"

    def booking_history():
        return [
            json.loads(payload).get("live_l10_close_bookings", {})
            for (payload,) in read_rows(budget, "SELECT payload FROM states ORDER BY seq")
        ]

    assert not any(booking_history())
    (claim,) = read_rows(post_store, "SELECT grant_id, dispatch_started_at FROM claims")
    permit = send["permit"]
    attempt = permit["transport_attempt"]
    assert claim == (
        "one-grant",
        datetime.fromisoformat(attempt["socket_boundary_at_utc"]).timestamp(),
    )
    assert attempt["phase"] == "MAY_HAVE_SENT"
    assert permit["outcome"] == "SENT_INITIATED_UNKNOWN_UNTIL_TRANSPORT"
    assert permit["post_count"] == 1 and not permit["resubmit_allowed"]
    assert load_external_effect_durable_consume_v1(store_root=submit_root)["record"] == permit
    immutable = (post_store, checkpoint, *sorted(submit_root.glob("*.json")))
    original = {path: sha256(path.read_bytes()).hexdigest() for path in immutable}

    run_stage("book", -signal.SIGKILL)
    committed = json.loads((tmp_path / "after-booking-commit.json").read_bytes())
    booking = committed["booking"]
    assert booking["episode_id"] == send["episode_id"]
    assert booking["reservation_id"] == send["reservation_id"]
    assert booking["close_envelope_digest"] == permit["envelope_digest"]
    assert (booking["net_result"], booking["currency"]) == ("0.13", "USDC")
    expected_gets = [
        [f"{path}?{urlencode(query)}" if query else path, sha256(body.encode()).hexdigest()]
        for path, query, body in send["responses"]
    ]
    assert committed["gets"] == expected_gets
    history = booking_history()
    assert history[-1] == {send["episode_id"]: booking} and not any(history[:-1])
    proof_root = tmp_path / "private-get-evidence"
    close_proof = proof_root / f"close-{booking['close_proof_digest']}.json"
    history_proof = proof_root / f"close-history-{booking['history_proof_digest']}.json"
    record = json.loads(close_proof.read_bytes())["record"]
    assert record["schema"] == store.CLOSE_GET_PROOF_V2
    assert record["position_episode_id"] == send["episode_id"]
    identity = record["identity"]
    assert identity["submit_attempt_id"] == attempt["claim_id"]
    assert identity["atomic_consumption_key"] == permit["permit_id"]
    assert (identity["account_identity"], identity["clordid"]) == (send["account"], send["clordid"])
    order_page, fill_page = (record["gets"][index] for index in (3, 5))
    assert "after=" in order_page["endpoint"] and "after=" in fill_page["endpoint"]
    (order,) = json.loads(order_page["body"])["data"]
    (fill,) = json.loads(fill_page["body"])["data"]
    assert order["clOrdId"] == fill["clOrdId"] == send["clordid"]
    assert order["ordId"] == fill["ordId"] == "91234" and fill["tradeId"] == "123"
    booked_files = {
        p: sha256(p.read_bytes()).hexdigest() for p in (budget, close_proof, history_proof)
    }

    run_stage("replay", 0)
    replay = json.loads((tmp_path / "after-restart-29p.json").read_bytes())
    assert len({send["pid"], committed["pid"], replay["pid"]}) == 3
    assert replay["booking"] == booking
    assert replay["blocker"] == "DOUBLE_PLAY_29P_LIVE_PROTECTIVE_STOP_REQUIRED"
    assert "DOUBLE_PLAY_29P_LIVE_SLOT_CAPITAL_BASIS_REQUIRED" in replay["reasons"]
    for field in ("close_proof_digest", "history_proof_digest"):
        assert replay["timing"][field] == booking[field]
    assert booking_history() == history
    assert {
        p: sha256(p.read_bytes()).hexdigest() for p in original | booked_files
    } == original | booked_files


def _assert_restarted_close_readback(
    tmp_path,
    monkeypatch,
    context,
    proof_root,
    opener,
    floor,
    case,
    *,
    expected_switch_mark,
    shared_authorization=None,
):
    from src.ops.full_core_live_path_composition_root_v1.current_productive_actual_venue_post_owner_go_durable_consume_v1 import (
        durable_post_owner_go_path_v1,
    )
    from src.ops.full_core_live_path_composition_root_v1.external_effect_permit_durable_consume_v1 import (
        load_external_effect_durable_consume_v1,
    )
    from src.ops.n1_standing_pre_external_runtime_supervisor_v1 import supervisor_v1 as supervisor
    from src.ops.portfolio_capital_reservation_budget_v1 import host_v1 as budget_host
    from tests.ops.test_current_productive_persistent_natural_enter_convergence_v1 import (
        _continuous_auth,
    )

    original_host = context.recovery.host
    envelope = context.execution.envelope
    _, bound = context.lane_pair
    product = "SWAP" if envelope.instrument_id.endswith("-SWAP") else "FUTURES"
    productive_paged = case.startswith("productive-paged-")
    if productive_paged:
        case = case.removeprefix("productive-")
    paged = case.startswith("paged-")
    owner_go_loss_injected = False

    def remove_owner_go():
        nonlocal owner_go_loss_injected
        if not owner_go_loss_injected:
            mandate = durable_post_owner_go_path_v1(context.store_root_v1())
            mandate.rename(mandate.with_suffix(".retained"))
            owner_go_loss_injected = True

    close_body, order, fill, currency, with_history = _close_http_fixture(
        envelope,
        case,
        original_body=opener.body,
        productive_paged=productive_paged,
        on_history=remove_owner_go if case == "owner-go-lost" else None,
    )
    restarted_at = NOW + timedelta(seconds=1)
    monkeypatch.setattr(opener, "body", close_body)
    monkeypatch.setattr(wire, "utc_now_iso_v1", restarted_at.isoformat)
    restarted_hosts = []

    def open_host(**kwargs):
        host = PortfolioBudgetHostV1(
            **{**kwargs, "root": original_host.root, "clock": restarted_at.timestamp}
        )
        restarted_hosts.append(host)
        return host

    def forbidden(*_args, **_kwargs):
        pytest.fail("Close readback must precede market data, new admission and POST")

    source_transport = original_host.reconciliation_transport
    offline_receipts = []
    if paged and not productive_paged:
        requests = _paged_close_requests(envelope, product, case, with_history)
        responses = {
            f"{path}?{urlencode(query)}" if query else path: close_body(path, query)
            for path, query in requests
            if case != "paged-missing" or not (path.endswith("/fills") and "after" in query)
        }
        source_transport = wire.FullCoreProductiveReadOnlyGetTransportV1(
            handle=source_transport._handle,
            offline_l10_close_responses=responses,
        )

        def record_offline_response(*, result, body):
            assert result.auth_header_sent and not result.venue_live_contact
            assert result.data_safety_source_kind is None
            offline_receipts.append((result.endpoint, sha256(body).hexdigest()))

        source_transport.raw_response_sink_v1 = record_offline_response
        monkeypatch.setattr(wire, "build_opener", forbidden)
        signer = wire.build_k1_okx_venue_auth_headers_v1
        signed_requests = []

        def check_offline_signature(*, handle, url, method):
            headers = signer(handle=handle, url=url, method=method)
            parsed = urlsplit(url)
            endpoint = parsed.path + (f"?{parsed.query}" if parsed.query else "")
            message = f"{headers['OK-ACCESS-TIMESTAMP']}GET{endpoint}".encode()
            test_key = json.loads(FAKE_OPAQUE)["secretKey"].encode()
            assert method == "GET"
            assert (
                headers["OK-ACCESS-SIGN"]
                == b64encode(hmac.digest(test_key, message, "sha256")).decode()
            )
            signed_requests.append(endpoint)
            return headers

        monkeypatch.setattr(wire, "build_k1_okx_venue_auth_headers_v1", check_offline_signature)

    monkeypatch.setattr(budget_host, "PortfolioBudgetHostV1", open_host)
    config = supervisor.StandingSupervisorConfigV1(
        public_store_root=tmp_path / "public",
        private_store_root=tmp_path / "private",
        lane_state_root=tmp_path / "scope",
        evidence_root=tmp_path / "restart" / "post-close-session",
        expected_account_identity=original_host.expected_account_identity,
        venue_native_id=bound.venue_native_id,
        canonical_instrument_id=bound.instrument_id,
        transport_scope=supervisor.TRANSPORT_SCOPE_SCOPED_READONLY_GET,
    )
    store_root = context.store_root_v1()
    original_send = load_external_effect_durable_consume_v1(store_root=store_root)
    shared_state = {}
    if shared_authorization is not None:
        authority = shared_authorization.authority
        shared_state = {
            path: path.read_bytes() for path in (authority.path, authority.checkpoint_path)
        }
    request_count = len(opener.requests)
    held = original_host.owner.active_sum_v1()
    original_host.close()
    run_args = dict(
        config=config,
        origin_main_sha=original_host.repository_sha,
        bound=bound,
        authorization=replace(
            _continuous_auth(native_id=bound.venue_native_id, max_cycles=1),
            expected_cursor_floor=floor,
        ),
        observation_source=None,
        g17_producers={},
        f1_m9_cycle_evaluator=forbidden,
        public_rest_fetch=forbidden,
        private_rest_fetch=forbidden,
        pretrade_transport=source_transport,
        wp02_hook=forbidden,
        skip_owner_go_validation=True,
        occupied_mark_proof_root=proof_root,
    )
    resumed = supervisor.run_n1_standing_pre_external_supervisor_v1(**run_args)
    readback = resumed.close_readback
    assert readback is not None
    assert (
        readback.status
        == {
            "flat": "CLOSE_FLAT_CONFIRMED",
            "booked": "CLOSE_NET_BOOKED",
            "paged-booked": "CLOSE_NET_BOOKED",
            "paged-missing": "CLOSE_READBACK_BLOCKED",
            "paged-foreign": "CLOSE_READBACK_BLOCKED",
            "paged-foreign-product": "CLOSE_READBACK_BLOCKED",
            "paged-open-orders": "CLOSE_READBACK_BLOCKED",
            "history-missing": "CLOSE_FLAT_CONFIRMED",
            "history-conflict": "CLOSE_FLAT_CONFIRMED",
            "history-foreign": "CLOSE_FLAT_CONFIRMED",
            "owner-go-lost": "CLOSE_FLAT_CONFIRMED",
            "partial": "CLOSE_PARTIAL",
            "unseen": "CLOSE_AWAITING_VENUE",
            "missing-fill": "CLOSE_READBACK_BLOCKED",
            "page-orders-pending": "CLOSE_READBACK_BLOCKED",
            "page-orders-history": "CLOSE_READBACK_BLOCKED",
            "page-fills": "CLOSE_READBACK_BLOCKED",
            "wrong-order": "CLOSE_READBACK_BLOCKED",
            "stale-residual": "CLOSE_READBACK_BLOCKED",
            "no-flat-anchor": "CLOSE_READBACK_BLOCKED",
            "not-sent": "CLOSE_SUBMIT_NOT_PROVEN",
        }[case]
    ), readback.reason_codes
    assert readback.envelope_digest == envelope.envelope_digest
    assert resumed.ok is (case in {"flat", "owner-go-lost"} or case.startswith("history-"))
    assert resumed.trace.post_count == 0 and not resumed.owner_go_consumed
    assert resumed.policy_result is None
    assert restarted_hosts[-1].closed
    if restarted_hosts[-1].owner is not None:
        assert restarted_hosts[-1].owner.active_sum_v1() == held
    assert original_host.owner.active_sum_v1() == held
    assert load_external_effect_durable_consume_v1(store_root=store_root) == original_send
    if paged:
        if productive_paged:
            assert source_transport.venue_live_contact
        else:
            assert len(opener.requests) == request_count
            assert not source_transport.venue_live_contact
            assert readback.counter_order_request is None and resumed.counter_order_sizing is None
        if not with_history:
            assert readback.counter_order_request is None and resumed.counter_order_sizing is None
            assert readback.reason_codes == (
                {
                    "paged-missing": (
                        "RECONCILIATION_GET_RESPONSE_UNPROVEN"
                        if productive_paged
                        else "OFFLINE_L10_CLOSE_RESPONSE_MISSING"
                    ),
                    "paged-foreign": REASON_INCOMPLETE_PAGINATION,
                    "paged-foreign-product": REASON_INCOMPLETE_PAGINATION,
                    "paged-open-orders": "POST_CLOSE_PENDING_CUSTODY_NOT_CLEAR",
                }[case],
            )
            assert readback.proof_path is None and readback.net_booking is None
            assert not list(proof_root.glob("close-*.json"))
            assert not restarted_hosts[-1].owner._live_l10_close_bookings
            return
        booking = readback.net_booking
        assert booking["episode_id"] == context.execution.l10_close.episode.episode_id
        assert booking["reservation_id"] == context.authenticated_entry.proof.reservation_id
        assert booking["net_result"] == ("0.13" if product == "FUTURES" else "0.09")
        assert booking["currency"] == currency
        record = json.loads(readback.proof_path.read_bytes())["record"]
        actual_reads = [(get["endpoint"], get["body_sha256"]) for get in record["gets"]]
        if productive_paged:
            assert record["schema"] == store.CLOSE_GET_PROOF_V2
            assert record["venue_host"] == wire.AUTHORIZED_HOST
            assert actual_reads == opener.requests[request_count:-1]
            assert readback.counter_order_request.net_booking.to_dict_v1() == booking
            sizing = resumed.counter_order_sizing
            assert sizing.first_blocker == "DOUBLE_PLAY_29P_LIVE_PROTECTIVE_STOP_REQUIRED"
            assert not sizing.venue_plan_authorized
            assert (
                sizing.authenticated_close_timing.close_proof_digest
                == booking["close_proof_digest"]
            )
        else:
            assert record["schema"] == store.OFFLINE_CLOSE_GET_PROOF_V2
            assert actual_reads == offline_receipts[:-1]
            assert signed_requests == [endpoint for endpoint, _ in offline_receipts]
        assert json.loads(record["gets"][3]["body"])["data"] == [order]
        assert json.loads(record["gets"][5]["body"])["data"] == [fill]
        database = original_host.root / "owner" / "reservations.sqlite3"
        original_database = database.read_bytes()
        original_receipt = readback.proof_path.read_bytes()
        replay_transport = wire.FullCoreProductiveReadOnlyGetTransportV1(
            offline_l10_close_responses=None if productive_paged else {}
        )
        replay = supervisor.run_n1_standing_pre_external_supervisor_v1(
            **{
                **run_args,
                "config": replace(config, evidence_root=tmp_path / "paged-replay"),
                "pretrade_transport": replay_transport,
            }
        )
        assert replay.close_readback == readback
        assert replay.counter_order_sizing == resumed.counter_order_sizing
        assert not replay_transport.methods_used and replay.trace.post_count == 0
        assert database.read_bytes() == original_database
        assert readback.proof_path.read_bytes() == original_receipt
        history_path = proof_root / f"close-history-{booking['history_proof_digest']}.json"
        if shared_authorization is not None:
            send = original_send["record"]
            identity = record["identity"]
            assert send["transport_attempt"]["phase"] == "MAY_HAVE_SENT"
            assert identity["submit_attempt_id"] == send["transport_attempt"]["claim_id"]
            assert identity["atomic_consumption_key"] == send["permit_id"]
            assert identity["clordid"] == envelope.client_order_id
            assert identity["account_identity"] == shared_authorization.grant.account
            assert (
                shared_authorization.grant.envelope_digest
                == send["envelope_digest"]
                == identity["envelope_digest"]
                == booking["close_envelope_digest"]
            )
            assert "DOUBLE_PLAY_29P_LIVE_SLOT_CAPITAL_BASIS_REQUIRED" in sizing.reason_codes
            assert (
                sizing.authenticated_close_timing.history_proof_digest
                == booking["history_proof_digest"]
            )
            history_bytes = history_path.read_bytes()
            _assert_close_booking_in_fresh_process(
                original_host=original_host,
                lane_state_root=config.lane_state_root,
                proof_root=proof_root,
                bound=bound,
                booking=booking,
                sizing=sizing,
            )
            assert database.read_bytes() == original_database
            assert readback.proof_path.read_bytes() == original_receipt
            assert history_path.read_bytes() == history_bytes
            assert load_external_effect_durable_consume_v1(store_root=store_root) == original_send
            assert all(path.read_bytes() == before for path, before in shared_state.items())
        with closing(
            open_host(
                root=original_host.root,
                private_rest_fetch=forbidden,
                repository_sha=original_host.repository_sha,
                session_id="paged-proof-check",
                expected_account_identity=original_host.expected_account_identity,
                reconciliation_transport=replay_transport,
            )
        ) as host:
            owner = host.recover_owner_for_l10_close_booking_v1({"LANE_1": bound})
            _assert_invalid_close_page_receipts_are_rejected(
                owner=owner,
                execution=context.execution,
                proof_root=proof_root,
                close=record,
                history=json.loads(history_path.read_bytes())["record"],
                repository_sha=original_host.repository_sha,
            )
            assert owner.read_authenticated_l10_close_v1(booking["episode_id"]) == booking
        with pytest.raises(ValueError, match="CLOSE_PROOF_CONTENT_UNPROVEN"):
            supervisor.run_n1_standing_pre_external_supervisor_v1(
                **{
                    **run_args,
                    "config": replace(config, evidence_root=tmp_path / "paged-source-denied"),
                    "pretrade_transport": wire.FullCoreProductiveReadOnlyGetTransportV1(
                        offline_l10_close_responses={} if productive_paged else None
                    ),
                }
            )
        assert database.read_bytes() == original_database
        return
    assert len(opener.requests) - request_count == (
        0 if case == "not-sent" else 6 + int(with_history) + int(case.startswith("page-"))
    )
    if case == "flat" or with_history:
        assert readback.remaining_quantity == 0
        assert readback.filled_quantity == Decimal(envelope.quantity)
        path = readback.proof_path
        assert stat.S_IMODE(path.stat().st_mode) == 0o600
        record = json.loads(path.read_bytes())["record"]
        assert record["identity"]["envelope_digest"] == envelope.envelope_digest
        assert record["position_coverage"]["endpoint"] == (
            f"/api/v5/account/positions?instId={envelope.instrument_id}"
        )
        assert [
            (row["endpoint"], sha256(row["body"].encode()).hexdigest()) for row in record["gets"]
        ] == opener.requests[request_count : request_count + 6]
        assert json.loads(record["gets"][3]["body"])["data"] == [fill]
        if case == "booked":
            from src.ops.full_core_live_path_composition_root_v1.current_productive_enter_live_29p_join_v1 import (
                check_authenticated_double_play_29p_admission_v1,
            )
            from src.ops.full_core_live_path_composition_root_v1.current_productive_governed_continuous_cycle_orchestrator_v1 import (
                DISPOSITION_FAIL_CLOSED,
            )

            booking = readback.net_booking
            assert booking["net_result"] == ("0.13" if product == "FUTURES" else "0.09")
            assert booking["currency"] == currency
            assert booking["episode_id"] == context.execution.l10_close.episode.episode_id
            assert booking["reservation_id"] == context.authenticated_entry.proof.reservation_id
            assert booking["slot_id"] == "LANE_1"
            assert resumed.trace.extra["close_booking_digest"] == booking["booking_digest"]
            counter = readback.counter_order_request
            assert counter is not None
            assert counter.execution == context.execution
            assert counter.bound_instrument == bound
            assert counter.target_side == ("short" if envelope.side == "sell" else "long")
            assert counter.decision_id == f"l10:{envelope.envelope_digest}"
            assert counter.net_booking.to_dict_v1() == booking
            historical = readback.historical_sizing_reference
            assert historical is not None
            assert historical.source_role == "HISTORICAL_SWITCH_READBACK_ONLY"
            assert historical.scope_digest == context.execution.l10_close.scope_digest
            assert historical.scope_seal_id == context.execution.l10_close.scope_seal_id
            assert historical.canonical_instrument_id == bound.instrument_id
            assert historical.venue_native_id == envelope.instrument_id
            assert historical.target_side == counter.target_side
            assert float(historical.switch_mark_price) == expected_switch_mark
            distance = Decimal(historical.adverse_exit_distance)
            assert distance == Decimal(historical.scope_magnitude)
            assert Decimal(historical.counter_side_reference_price) == (
                Decimal(historical.switch_mark_price)
                + (distance if counter.target_side == "short" else -distance)
            )
            sizing = resumed.counter_order_sizing
            assert sizing is not None
            assert sizing.first_blocker == "DOUBLE_PLAY_29P_LIVE_PROTECTIVE_STOP_REQUIRED"
            assert "DOUBLE_PLAY_29P_LIVE_SLOT_CAPITAL_BASIS_REQUIRED" in sizing.reason_codes
            assert sizing.get_count == 0
            assert not sizing.portfolio_reservation_id and not sizing.venue_plan_authorized
            history_path = proof_root / f"close-history-{booking['history_proof_digest']}.json"
            history = json.loads(history_path.read_bytes())["record"]
            assert record["schema"] == "peaktrade.authenticated_close_get_proof.v1"
            assert history["schema"] == "peaktrade.authenticated_close_history.v1"
            original_receipts = (path.read_bytes(), history_path.read_bytes())
            close_timing = {
                "close_proof_digest": booking["close_proof_digest"],
                "history_proof_digest": booking["history_proof_digest"],
                "position_time_ms": record["position_time_ms"],
                "close_readback_acquired_at_utc": record["gets"][-1]["acquired_at"],
                "settlement_acquired_at_utc": history["get"]["acquired_at"],
            }
            assert asdict(sizing.authenticated_close_timing) == close_timing
            notice = json.loads(
                (config.evidence_root / "runtime_liveness_latest_v1.json").read_bytes()
            )
            assert notice["reason_code"] == sizing.first_blocker
            assert notice["extra"]["counter_order_sizing_reasons"] == list(sizing.reason_codes)
            assert notice["extra"]["counter_order_close_timing"] == close_timing
            assert "original slot" in notice["recovery_action"]
            assert "Retain the original hold." in notice["recovery_action"]
            assert not notice["post_allowed"] and not notice["external_effect_authorized"]
            assert resumed.trace.terminal_disposition == DISPOSITION_FAIL_CLOSED
            assert resumed.trace.extra["counter_order"]["decision_id"] == counter.decision_id
            assert resumed.trace.extra["counter_order"]["target_side"] == counter.target_side
            assert (
                resumed.trace.extra["counter_order"]["historical_sizing_reference"]["source_role"]
                == "HISTORICAL_SWITCH_READBACK_ONLY"
            )
            database = original_host.root / "owner" / "reservations.sqlite3"
            committed = database.read_bytes()
            before = len(opener.requests)
            replay = supervisor.run_n1_standing_pre_external_supervisor_v1(
                **{**run_args, "config": replace(config, evidence_root=tmp_path / "restart-again")}
            )
            assert replay.close_readback == readback
            assert replay.counter_order_sizing == sizing
            assert len(opener.requests) == before
            assert database.read_bytes() == committed

            verification_host = PortfolioBudgetHostV1(
                root=original_host.root,
                private_rest_fetch=forbidden,
                repository_sha=original_host.repository_sha,
                session_id="counter-order-proof-check",
                expected_account_identity=original_host.expected_account_identity,
            )
            try:
                owner = verification_host.recover_owner_for_l10_close_booking_v1({"LANE_1": bound})
                _assert_invalid_close_page_receipts_are_rejected(
                    owner=owner,
                    execution=context.execution,
                    proof_root=proof_root,
                    close=record,
                    history=history,
                    repository_sha=original_host.repository_sha,
                )
                assert owner.read_authenticated_l10_close_v1(booking["episode_id"]) == booking
                original_commitment = next(
                    row
                    for row in owner.local_commitment_readback_v1().commitments
                    if row.reservation_id == booking["reservation_id"]
                )
                assert original_commitment.state == "COMMITTED"
                assert original_commitment.slot_id == booking["slot_id"]
                assert original_commitment.venue_native_id == historical.venue_native_id
                assert owner.slot_capital_basis_v1(booking["slot_id"]) is None
                for retained_proof in (path, history_path):
                    backup = retained_proof.with_suffix(".saved")
                    retained_proof.rename(backup)
                    try:
                        blocked = check_authenticated_double_play_29p_admission_v1(
                            request=counter,
                            bound_instrument=bound,
                            owner=owner,
                            proof_root=proof_root,
                        )
                        assert (
                            blocked.first_blocker == "DOUBLE_PLAY_29P_BOOKED_CLOSE_PROOF_UNPROVEN"
                        )
                        assert blocked.get_count == 0 and not blocked.venue_plan_authorized
                        assert blocked.authenticated_close_timing is None
                    finally:
                        backup.rename(retained_proof)
                for changed, blocker in (
                    (
                        replace(counter, net_booking=replace(counter.net_booking, net_result="99")),
                        "DOUBLE_PLAY_29P_BOOKED_CLOSE_BINDING_MISMATCH",
                    ),
                    (
                        replace(counter, bound_instrument=replace(bound, selection_id="foreign")),
                        "DOUBLE_PLAY_29P_BOOKED_CLOSE_BINDING_MISMATCH",
                    ),
                    (
                        replace(counter, execution=replace(counter.execution, l10_close=None)),
                        "DOUBLE_PLAY_29P_BOOKED_CLOSE_EXECUTION_MISMATCH",
                    ),
                ):
                    blocked = check_authenticated_double_play_29p_admission_v1(
                        request=changed,
                        bound_instrument=changed.bound_instrument,
                        owner=owner,
                        proof_root=proof_root,
                    )
                    assert blocked.first_blocker == blocker
                    assert not blocked.venue_plan_authorized
                assert owner.active_sum_v1() == held
            finally:
                verification_host.close()
            assert database.read_bytes() == committed
            assert (path.read_bytes(), history_path.read_bytes()) == original_receipts
            assert len(opener.requests) == before
        else:
            assert readback.net_booking is None
            assert readback.counter_order_request is None
            assert readback.historical_sizing_reference is None
            assert resumed.counter_order_sizing is None
            assert readback.reason_codes[0] == "L10_CLOSE_NET_BOOKING_PENDING"
            if case == "owner-go-lost":
                assert readback.reason_codes[1] == "L10_CLOSE_BOOKING_POST_OWNER_GO_UNPROVEN"
                notice = json.loads(
                    (config.evidence_root / "runtime_liveness_latest_v1.json").read_bytes()
                )
                assert notice["reason_code"] == readback.reason_codes[1]
                assert notice["extra"]["close_readback_status"] == "CLOSE_FLAT_CONFIRMED"
                assert "original consumed POST Owner-GO" in notice["recovery_action"]
                assert not notice["post_allowed"] and not notice["external_effect_authorized"]
                mandate = durable_post_owner_go_path_v1(store_root)
                assert not mandate.exists()
                assert not restarted_hosts[-1].owner._live_l10_close_bookings
                mandate.with_suffix(".retained").rename(mandate)
                with open_governed_live_c1_get_only_fresh_pretrade_transport_v1(
                    max_request_count=7, k1_lookup_backend=_FakeKeychainBackend()
                ) as (recovery_transport, _):
                    recovered = supervisor.run_n1_standing_pre_external_supervisor_v1(
                        **{
                            **run_args,
                            "config": replace(config, evidence_root=tmp_path / "restart-restored"),
                            "pretrade_transport": recovery_transport,
                        }
                    )
                    assert recovery_transport.methods_used == ["GET"] * 7
                assert recovered.close_readback.status == "CLOSE_NET_BOOKED"
                assert recovered.counter_order_sizing.venue_plan_authorized is False
                assert recovered.trace.post_count == 0
                assert restarted_hosts[-1].owner.active_sum_v1() == held
                assert (
                    load_external_effect_durable_consume_v1(store_root=store_root) == original_send
                )
    else:
        assert readback.historical_sizing_reference is None
        assert readback.proof_path is None
        assert readback.net_booking is None
        assert readback.counter_order_request is None
        assert resumed.counter_order_sizing is None
        assert not list(proof_root.glob("close-*.json"))
        if case.startswith("page-"):
            assert readback.reason_codes == (REASON_INCOMPLETE_PAGINATION,)
            assert not restarted_hosts[-1].owner._live_l10_close_bookings
            followups = [
                urlsplit(endpoint).path
                for endpoint, _ in opener.requests[request_count:]
                if "after=" in endpoint
            ]
            assert followups == [f"/api/v5/trade/{case.removeprefix('page-')}"]
        if case == "partial":
            half_quantity = Decimal(envelope.quantity) / 2
            assert readback.filled_quantity == half_quantity
            assert readback.remaining_quantity == half_quantity


@pytest.mark.parametrize("filled_anchor", [False, True])
def test_private_receipt_rebuilds_in_a_fresh_process(authenticated_host, proof_root, filled_anchor):
    host, identity, opener, scope, held = authenticated_host
    if filled_anchor:
        opener.fault = "filled-anchor"
    rid = identity.portfolio_reservation_id
    filegate_before = scope.state_path.read_bytes()
    context, proofs = host.observe_authenticated_execution_reconciliation_v1(
        {"LANE_1": _bound()}, proof_root=proof_root
    )
    proof = proofs[rid]
    assert len(opener.requests) == 6
    assert host.owner.active_sum_v1() == held > 0
    assert host.owner.budget_state_v1().recovery_required
    assert context.execution_reconciliation[rid]["snapshot_digest"] == proof.snapshot_digest
    args = _receipt_args(host, scope, identity, proof_root, proof.revision_ref)
    path = proof_root / f"{proof.revision_ref[1]}.json"
    assert list(proof_root.iterdir()) == [path]
    assert stat.S_IMODE(path.stat().st_mode) == 0o600
    source = json.loads(path.read_bytes())["record"]
    assert (source["position_interval"] is not None) is filled_anchor
    assert [
        (row["endpoint"], sha256(row["body"].encode()).hexdigest()) for row in source["gets"]
    ] == (opener.requests)
    assert all(
        field not in path.read_text() for field in ("ak-test", "sk-test", "pp-test", "OK-ACCESS-")
    )
    assert store.read_authenticated_execution_reconciliation_proof_v1(**args) == proof
    host.close()
    database = host.root / "owner" / "reservations.sqlite3"
    db_before = database.read_bytes()
    receipt_before = path.read_bytes()
    cold = """
from dataclasses import asdict
import json
import socket
import sys

def deny_network(*args, **kwargs):
    raise AssertionError("readback attempted network")

socket.socket.connect = deny_network
socket.create_connection = deny_network
from src.ops.execution_reconciliation_proof_store_v1 import (
    read_authenticated_execution_reconciliation_proof_v1,
)
args = json.loads(sys.argv[1])
args["revision_ref"] = tuple(args["revision_ref"])
print(json.dumps(asdict(read_authenticated_execution_reconciliation_proof_v1(**args)), default=str))
"""
    launcher = Path(__file__).resolve().parents[2] / "scripts/pt"
    out = subprocess.run(
        [str(launcher), "-c", cold, json.dumps(args, default=str)],
        check=True,
        capture_output=True,
        text=True,
        timeout=15,
    )
    assert json.loads(out.stdout.splitlines()[-1]) == json.loads(
        json.dumps(asdict(proof), default=str)
    )
    assert path.read_bytes() == receipt_before
    assert database.read_bytes() == db_before
    assert scope.state_path.read_bytes() == filegate_before
    assert not scope.journal_path.exists()


@pytest.mark.parametrize(
    ("fault", "reason"),
    [
        ("raw-body", "RAW_BODY_MISMATCH"),
        ("new-raw-digest", "SNAPSHOT_UNPROVEN"),
        ("incident", "INCIDENT_UNPROVEN"),
        ("account", "SCOPE_MISMATCH"),
        ("reservation", "SCOPE_MISMATCH"),
        ("budget-sequence", "SCOPE_MISMATCH"),
        ("missing", "READBACK_UNPROVEN"),
        ("foreign-file", "READBACK_UNPROVEN"),
    ],
)
def test_cold_readback_refuses_unbound_receipts(authenticated_host, proof_root, fault, reason):
    host, identity, _, scope, _ = authenticated_host
    _, proofs = host.observe_authenticated_execution_reconciliation_v1(
        {"LANE_1": _bound()}, proof_root=proof_root
    )
    proof = proofs[identity.portfolio_reservation_id]
    path = proof_root / f"{proof.revision_ref[1]}.json"
    args = _receipt_args(host, scope, identity, proof_root, proof.revision_ref)
    if fault in {"raw-body", "new-raw-digest", "incident"}:
        envelope = json.loads(path.read_bytes())
        record = envelope["record"]
        if fault == "incident":
            record["quantity_incident"] = None
        else:
            reply = record["gets"][2]
            raw = json.loads(reply["body"])
            raw["data"][0]["accFillSz"] = "0"
            reply["body"] = json.dumps(raw)
            if fault == "new-raw-digest":
                reply["body_sha256"] = sha256(reply["body"].encode()).hexdigest()
        envelope["sha256"] = sha256(store._encode(record)).hexdigest()
        path.write_bytes(store._encode(envelope))
    elif fault == "account":
        args["account"] = "wrong-account"
    elif fault == "reservation":
        args["reservation_id"] = "wrong-reservation"
    elif fault == "budget-sequence":
        args["revision_ref"] = (proof.revision_ref[0] - 1, proof.revision_ref[1])
    elif fault == "missing":
        path.unlink()
    else:
        moved = path.with_suffix(".original")
        path.rename(moved)
        path.symlink_to(moved)
    host.close()
    with pytest.raises(store.ExecutionReconciliationProofStoreError, match=reason):
        store.read_authenticated_execution_reconciliation_proof_v1(**args)
    assert not scope.journal_path.exists()


def test_publication_failure_leaves_original_budget_fenced_and_retry_works(
    authenticated_host, proof_root, monkeypatch
):
    host, identity, opener, scope, held = authenticated_host
    rid = identity.portfolio_reservation_id
    bindings = {"LANE_1": _bound()}

    def refuse_link(*args, **kwargs):
        raise OSError("injected interrupted publication")

    with monkeypatch.context() as patch:
        patch.setattr(store.os, "link", refuse_link)
        with pytest.raises(OSError, match="interrupted publication"):
            host.observe_authenticated_execution_reconciliation_v1(bindings, proof_root=proof_root)
    assert not list(proof_root.iterdir())
    sequence, checksum, stored = read_persisted_execution_reconciliation_v1(host.owner, rid)
    assert host.owner.active_sum_v1() == held > 0
    assert host.owner.budget_state_v1().recovery_required
    assert stored["reconciliation"]["decision"]["reasons"] == [REASON_NEGATIVE_REMAINING]
    with pytest.raises(store.ExecutionReconciliationProofStoreError, match="READBACK_UNPROVEN"):
        store.read_authenticated_execution_reconciliation_proof_v1(
            **_receipt_args(host, scope, identity, proof_root, (sequence, checksum))
        )
    _, proofs = host.observe_authenticated_execution_reconciliation_v1(
        bindings, proof_root=proof_root
    )
    proof = proofs[rid]
    assert proof.revision_ref[0] > sequence
    assert len(opener.requests) == 12
    assert (
        store.read_authenticated_execution_reconciliation_proof_v1(
            **_receipt_args(host, scope, identity, proof_root, proof.revision_ref)
        )
        == proof
    )
    assert not scope.journal_path.exists()


def test_private_publication_is_idempotent_and_refuses_overwrite(proof_root):
    path = proof_root / "receipt"
    store._publish(path, b"original")
    identity = path.stat().st_ino
    store._publish(path, b"original")
    with pytest.raises(store.ExecutionReconciliationProofStoreError, match="IMMUTABLE_CONFLICT"):
        store._publish(path, b"changed")
    assert path.stat().st_ino == identity
    assert path.read_bytes() == b"original"
    assert list(proof_root.iterdir()) == [path]


def test_receipt_after_publication_and_before_ack_is_readable(
    authenticated_host, proof_root, monkeypatch
):
    host, identity, _, scope, held = authenticated_host
    fsync = store.os.fsync

    def interrupt_directory_ack(fd):
        if stat.S_ISDIR(store.os.fstat(fd).st_mode):
            raise OSError("injected lost receipt acknowledgement")
        fsync(fd)

    with monkeypatch.context() as patch:
        patch.setattr(store.os, "fsync", interrupt_directory_ack)
        with pytest.raises(OSError, match="lost receipt acknowledgement"):
            host.observe_authenticated_execution_reconciliation_v1(
                {"LANE_1": _bound()}, proof_root=proof_root
            )
    sequence, checksum, _ = read_persisted_execution_reconciliation_v1(
        host.owner, identity.portfolio_reservation_id
    )
    assert host.owner.active_sum_v1() == held
    host.close()
    proof = store.read_authenticated_execution_reconciliation_proof_v1(
        **_receipt_args(host, scope, identity, proof_root, (sequence, checksum))
    )
    assert proof.quantity_incident.reconciliation_reason == REASON_NEGATIVE_REMAINING
    assert list(proof_root.iterdir()) == [proof_root / f"{checksum}.json"]
    assert not scope.journal_path.exists()


def test_historical_receipt_rejects_damaged_original_budget_revision(
    authenticated_host, proof_root
):
    host, identity, _, scope, _ = authenticated_host
    _, proofs = host.observe_authenticated_execution_reconciliation_v1(
        {"LANE_1": _bound()}, proof_root=proof_root
    )
    proof = proofs[identity.portfolio_reservation_id]
    args = _receipt_args(host, scope, identity, proof_root, proof.revision_ref)
    host.close()
    database = host.root / "owner" / "reservations.sqlite3"
    with sqlite3.connect(database) as connection:
        connection.execute(
            "UPDATE states SET payload = ? WHERE seq = ?", ("{}", proof.revision_ref[0])
        )
    with pytest.raises(
        store.ExecutionReconciliationProofStoreError, match="READBACK_UNPROVEN"
    ) as exc:
        store.read_authenticated_execution_reconciliation_proof_v1(**args)
    assert "DURABLE_BUDGET_REVISION_UNPROVEN" in str(exc.value.__cause__)
    assert not scope.journal_path.exists()


def test_unprivate_proof_root_is_rejected_before_reads(authenticated_host, proof_root):
    host, _, opener, _, _ = authenticated_host
    proof_root.chmod(0o755)
    with pytest.raises(store.ExecutionReconciliationProofStoreError, match="ROOT_NOT_PRIVATE"):
        host.observe_authenticated_execution_reconciliation_v1(
            {"LANE_1": _bound()}, proof_root=proof_root
        )
    assert not opener.requests
