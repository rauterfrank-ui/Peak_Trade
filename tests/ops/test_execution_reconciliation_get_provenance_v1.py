"""Original K1 signing and HTTP GET code with simulated Keychain and HTTP boundaries."""

from base64 import b64encode
from contextlib import contextmanager
from dataclasses import asdict
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from hashlib import sha256
import hmac
import json
import os
from pathlib import Path
import plistlib
import sqlite3
import stat
import subprocess
import time
from types import SimpleNamespace
from urllib.parse import parse_qsl, urlsplit

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
        row = {
            "instId": identity.native_id,
            "clOrdId": identity.clordid,
            "ordId": "venue-order",
            "state": state,
            "sz": identity.final_quantity,
            "accFillSz": filled,
        }
        code = "0"
        rows = []
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
                if path.endswith("orders-algo-pending")
                else self.baseline(path, params)
            )
            return json.dumps(payload, separators=(",", ":")).encode()
        elif self.fault == "missing-order":
            if path.endswith("/order"):
                code = "51603"
        elif path.endswith(("orders-history", "/order")):
            rows = [row]
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


@pytest.fixture
def authenticated_host(tmp_path, monkeypatch):
    seeded, rid, _, envelope, _, _ = seed_with_origin(tmp_path, monkeypatch)
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
        max_request_count=20, k1_lookup_backend=_FakeKeychainBackend()
    ) as (transport, _):
        host = PortfolioBudgetHostV1(
            root=seeded.root,
            private_rest_fetch=_fetch(uid=identity.account_identity),
            repository_sha="test-host-revision",
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
    if final_state == "ACTIVE" or case == "already-killed":
        assert gate.read_bytes() == original_gate
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
        finally:
            restored.close()
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


def test_authenticated_incident_aborts_original_post_before_socket(tmp_path, monkeypatch):
    from fastapi.testclient import TestClient

    from src.ops.full_core_live_path_composition_root_v1.external_effect_permit_durable_consume_v1 import (
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

    class ForbiddenHttp:
        def open(self, *args, **kwargs):
            pytest.fail("authenticated incident must veto before HTTP")

    def inject_incident_before_final_check():
        nonlocal receipt, before_socket
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
    monkeypatch.setenv(ENV_INCIDENT_DIAGNOSTICS_ROOT, str(output))
    client = TestClient(app)
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
    gate_payload = json.loads(gate.read_bytes())
    StatePersistence(str(gate)).save(
        KillSwitchState.KILLED,
        killed_at=datetime.fromisoformat(gate_payload["killed_at"]) + timedelta(seconds=1),
        trigger_reason=gate_payload["trigger_reason"],
    )
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


def _receipt_args(host, scope, identity, proof_root, revision_ref):
    return {
        "root": proof_root,
        "budget_owner_root": host.root / "owner",
        "account": scope.account,
        "session_id": SESSION,
        "reservation_id": identity.portfolio_reservation_id,
        "revision_ref": revision_ref,
    }


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
