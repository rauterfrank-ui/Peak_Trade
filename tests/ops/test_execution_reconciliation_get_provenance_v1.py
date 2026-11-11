"""Original K1 signing and HTTP GET code with simulated Keychain and HTTP boundaries."""

from base64 import b64encode
from contextlib import contextmanager
from dataclasses import asdict
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from hashlib import sha256
import hmac
import json
from pathlib import Path
import sqlite3
import stat
import subprocess
from urllib.parse import parse_qsl, urlsplit

import pytest

from src.ops.execution_incident_safety_v1 import (
    ExecutionIncidentSafetyError,
    OfflineExecutionIncidentScopeV1,
    _apply_confirmed_execution_incident_v1,
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
        row = {
            "instId": identity.native_id,
            "clOrdId": identity.clordid,
            "ordId": "venue-order",
            "state": "filled" if self.fault == "filled-anchor" else "partially_filled",
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
        elif path.endswith("/fills"):
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
