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
import sqlite3
import stat
import subprocess
import time
from types import SimpleNamespace
from urllib.error import HTTPError
from urllib.parse import parse_qsl, urlsplit
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
        max_request_count=25, k1_lookup_backend=_FakeKeychainBackend()
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
    ],
)
def test_futures_reconciliation_uses_bound_product_through_private_replay(
    tmp_path, monkeypatch, proof_root, path
):
    from src.ops.full_core_live_path_composition_root_v1.current_productive_venue_plan_v1 import (
        try_bind_current_productive_venue_plan_v1,
    )
    from src.ops.full_core_live_path_composition_root_v1.final_order_envelope_v1 import (
        bind_final_order_envelope_from_venue_plan_v1,
    )
    from tests.ops.test_current_usdc_xperp_financial_admission_v1 import EPOCH, join, prepare

    seeded, args, _ = prepare(tmp_path, monkeypatch, scoped_reconciliation=True)
    close_case = path in {"double-play-close", "double-play-net"}
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
        if path == "double-play-net":
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
        max_request_count=(85 if path == "double-play-net" else 84) if close_case else 26,
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
                    dispatch="readback-booked" if path == "double-play-net" else "readback-flat",
                    opener=opener,
                )
                assert transport.methods_used == ["GET"] * (85 if path == "double-play-net" else 84)
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
        ("occupied-mark", None),
        ("polled-mark", None),
        ("polled-mark-close-ack", None),
        ("polled-mark-close-timeout", None),
        ("polled-mark-close-venue-timeout", None),
        ("polled-mark-close-redirect", None),
        ("polled-mark-close-wrong-key", None),
        ("polled-mark-close-kill", None),
        ("polled-mark-close-stale-position", None),
        ("polled-mark-close-readback-flat", None),
        ("polled-mark-close-readback-booked", None),
        ("polled-mark-close-readback-history-missing", None),
        ("polled-mark-close-readback-history-conflict", None),
        ("polled-mark-close-readback-history-foreign", None),
        ("polled-mark-close-readback-partial", None),
        ("polled-mark-close-readback-unseen", None),
        ("polled-mark-close-readback-missing-fill", None),
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

    host, attempt, opener, scope, held = authenticated_host
    dispatch = (
        fault.removeprefix("polled-mark-close-")
        if fault and fault.startswith("polled-mark-close-")
        else None
    )
    polled = fault == "polled-mark" or dispatch is not None
    occupied_mark = fault == "occupied-mark" or polled
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
        "readback-history-missing",
        "readback-history-conflict",
        "readback-history-foreign",
    }
    if with_history:
        position.update(posId="8923", cTime=str(filled_at), ccy="USDT")
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
        )
        assert len(opener.requests) - request_count == (
            18 + int(with_history) if dispatch and dispatch.startswith("readback-") else 12
        )
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
            lambda **_: inputs["live_29p_injected_by_lane"]["LANE_1"],
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
                if readback is not None:
                    patch.setattr(
                        consume, "_utc_now_iso_v1", (NOW + timedelta(milliseconds=250)).isoformat
                    )
                _assert_original_close_dispatch(
                    close_context, "timeout" if readback is not None else dispatch, tmp_path
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


def _assert_original_close_dispatch(context, case, tmp_path):
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
    from src.ops.governed_productive_account_equity_authority_producer_v1 import (
        current_productive_actual_venue_post_with_fresh_envelope_bound_single_use_permit_v1 as actual,
    )
    from tests.ops.test_current_productive_actual_venue_post_with_fresh_envelope_bound_single_use_permit_v1 import (
        MockCurrentProductive29PIntegrityBackendV1,
    )

    host = context.recovery.host
    envelope = context.execution.envelope
    store_root = context.store_root_v1()
    requests = []

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
            if case == "timeout":
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
    denials = {
        "wrong-key": "K1_VENUE_CREDENTIAL_MISMATCH",
        "kill": "POST_SAFETY_DURABLE_VETO:BEFORE_SOCKET",
        "stale-position": "BEFORE_SOCKET:HOST_AUTHENTICATED_ENTRY_OBSERVATION_UNPROVEN",
    }
    if case in denials:
        reason = denials[case]
        with pytest.raises(actual.CurrentProductiveActualVenuePostError, match=reason):
            submit(**args)
        assert requests == []
        record = load_external_effect_durable_consume_v1(store_root=store_root)["record"]
        assert record["durable_state"] == "ABORTED_BEFORE_TRANSPORT"
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
        "UNKNOWN" if case in {"timeout", "venue-timeout", "redirect"} else "ACKNOWLEDGED"
    )
    if case in {"venue-timeout", "redirect"}:
        assert result.post_submit_join.exchange_query_before_retry_required
    assert result.post_submit_join.resubmit_allowed is False
    assert result.post_submit_join.fill_observed is False
    with pytest.raises(actual.CurrentProductiveActualVenuePostError, match="CONSUMED_PERMIT"):
        submit(**args)
    assert len(requests) == 1


def _assert_restarted_close_readback(
    tmp_path, monkeypatch, context, proof_root, opener, floor, case
):
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
        "fillSz": str(filled),
        "fillPx": "1996",
        "fillTime": str(stamp + 400),
        "fillPnl": "0.15",
        "fee": "-0.02",
        "feeCcy": currency,
    }
    original_body = opener.body
    with_history = case == "booked" or case.startswith("history-")

    def close_body(path, params):
        if path.endswith("/config"):
            return original_body(path, params)
        assert params["instId"] == envelope.instrument_id
        code, rows = "0", []
        if path.endswith("/positions-history"):
            assert with_history
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
        return json.dumps({"code": code, "data": rows}).encode()

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
        pretrade_transport=original_host.reconciliation_transport,
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
            "history-missing": "CLOSE_FLAT_CONFIRMED",
            "history-conflict": "CLOSE_FLAT_CONFIRMED",
            "history-foreign": "CLOSE_FLAT_CONFIRMED",
            "partial": "CLOSE_PARTIAL",
            "unseen": "CLOSE_AWAITING_VENUE",
            "missing-fill": "CLOSE_READBACK_BLOCKED",
            "wrong-order": "CLOSE_READBACK_BLOCKED",
            "stale-residual": "CLOSE_READBACK_BLOCKED",
            "no-flat-anchor": "CLOSE_READBACK_BLOCKED",
            "not-sent": "CLOSE_SUBMIT_NOT_PROVEN",
        }[case]
    ), readback.reason_codes
    assert readback.envelope_digest == envelope.envelope_digest
    assert resumed.ok is (case == "flat" or case.startswith("history-"))
    assert resumed.trace.post_count == 0 and not resumed.owner_go_consumed
    assert resumed.policy_result is None
    assert restarted_hosts[-1].closed
    if restarted_hosts[-1].owner is not None:
        assert restarted_hosts[-1].owner.active_sum_v1() == held
    assert original_host.owner.active_sum_v1() == held
    assert load_external_effect_durable_consume_v1(store_root=store_root) == original_send
    assert len(opener.requests) - request_count == (
        0 if case == "not-sent" else 6 + int(with_history)
    )
    if case == "flat" or with_history:
        assert readback.remaining_quantity == 0 and readback.filled_quantity == quantity
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
            sizing = resumed.counter_order_sizing
            assert sizing is not None
            assert sizing.first_blocker == "DOUBLE_PLAY_29P_LIVE_PROTECTIVE_STOP_REQUIRED"
            assert "DOUBLE_PLAY_29P_LIVE_SLOT_CAPITAL_BASIS_REQUIRED" in sizing.reason_codes
            assert sizing.get_count == 0
            assert not sizing.portfolio_reservation_id and not sizing.venue_plan_authorized
            notice = json.loads(
                (config.evidence_root / "runtime_liveness_latest_v1.json").read_bytes()
            )
            assert notice["reason_code"] == sizing.first_blocker
            assert "original slot" in notice["recovery_action"]
            assert "Retain the original hold." in notice["recovery_action"]
            assert not notice["post_allowed"] and not notice["external_effect_authorized"]
            assert resumed.trace.terminal_disposition == DISPOSITION_FAIL_CLOSED
            assert resumed.trace.extra["counter_order"]["decision_id"] == counter.decision_id
            assert resumed.trace.extra["counter_order"]["target_side"] == counter.target_side
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
                    )
                    assert blocked.first_blocker == blocker
                    assert not blocked.venue_plan_authorized
                assert owner.active_sum_v1() == held
            finally:
                verification_host.close()
            assert database.read_bytes() == committed
        else:
            assert readback.net_booking is None
            assert readback.counter_order_request is None
            assert resumed.counter_order_sizing is None
            assert readback.reason_codes[0] == "L10_CLOSE_NET_BOOKING_PENDING"
    else:
        assert readback.proof_path is None
        assert readback.counter_order_request is None
        assert resumed.counter_order_sizing is None
        assert not list(proof_root.glob("close-*.json"))
        if case == "partial":
            assert readback.filled_quantity == filled
            assert readback.remaining_quantity == quantity - filled


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
