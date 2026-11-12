"""Private immutable GET receipts and a credential-free historical readback."""

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from hashlib import sha256
import json
import os
from pathlib import Path
import re
import sqlite3
import stat
import tempfile

from src.ops.execution_reconciliation_get_provenance_v1 import (
    AuthenticatedExecutionReconciliationProofV1,
    ReconciliationGetProvenanceV1,
    _MAX_AGE_SECONDS,
    _reject_json_constant,
    _unique_json_object,
    adjudicate_reconciliation_quantity_incident_v1,
    require_futures_reconciliation_product_v1,
    resolve_reconciliation_query_options_v1,
)
from src.ops.full_core_live_path_composition_root_v1.fresh_pretrade_runtime_get_v1 import (
    ENDPOINT_ACCOUNT_CONFIG,
    GET_CACHE_POLICY_DYNAMIC_REFRESH_REQUIRED,
    TRANSPORT_CLASS_INJECTED_TEST_DOUBLE,
    FreshPretradeGetTransportResultV1,
)
from src.ops.full_core_live_path_composition_root_v1.full_core_exchange_reconciliation_okx_read_only_provider_v1 import (
    fetch_okx_read_only_reconciliation_snapshot_v1,
)
from src.ops.full_core_live_path_composition_root_v1.full_core_exchange_reconciliation_v1 import (
    FullCoreExchangeReconciliationSnapshotV1,
    PortfolioExecutionReconciliationIdentityV2,
    parse_exchange_reconciliation_identity_v1,
)
from src.ops.full_core_live_path_composition_root_v1.productive_read_only_get_transport_v1 import (
    AUTHORIZED_HOST,
)
from src.ops.portfolio_capital_reservation_budget_v1.durable_store_v1 import (
    read_budget_revision_read_only_v1,
)

_SCHEMA = "peaktrade.execution_reconciliation_get_proof.v1"


class ExecutionReconciliationProofStoreError(ValueError):
    """The private receipt or its budget binding could not be verified."""


@dataclass(frozen=True)
class AuthenticatedExecutionReconciliationSourceV1:
    proof: AuthenticatedExecutionReconciliationProofV1
    identity: PortfolioExecutionReconciliationIdentityV2
    snapshot: FullCoreExchangeReconciliationSnapshotV1 = field(repr=False)
    reconciliation: dict = field(repr=False)
    lane_binding: dict = field(repr=False)


def require_private_proof_root_v1(root) -> Path:
    root = Path(root)
    if not root.is_absolute() or root.resolve() != root or not root.is_dir():
        raise ExecutionReconciliationProofStoreError("GET_PROOF_ABSOLUTE_PRIVATE_ROOT_REQUIRED")
    info = root.stat()
    if info.st_uid != os.getuid() or info.st_mode & 0o077:
        raise ExecutionReconciliationProofStoreError("GET_PROOF_ROOT_NOT_PRIVATE")
    return root


def _proof_path(root, revision_ref):
    sequence, checksum = revision_ref
    if (
        type(sequence) is not int
        or sequence <= 0
        or type(checksum) is not str
        or re.fullmatch(r"[0-9a-f]{64}", checksum) is None
    ):
        raise ExecutionReconciliationProofStoreError("GET_PROOF_REVISION_REF_INVALID")
    return require_private_proof_root_v1(root) / f"{checksum}.json"


def _encode(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()


def _incident_payload(incident):
    if incident is None:
        return None
    return {
        **asdict(incident),
        "observed_at": incident.observed_at.isoformat(),
        "evidence_refs": list(incident.evidence_refs),
        "local_submit_outcome": incident.local_submit_outcome.value,
    }


def _read_private_file(path):
    flags = os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK
    with os.fdopen(os.open(path, flags), "rb") as stream:
        info = os.fstat(stream.fileno())
        if not stat.S_ISREG(info.st_mode) or info.st_uid != os.getuid() or info.st_mode & 0o077:
            raise ExecutionReconciliationProofStoreError("GET_PROOF_FILE_NOT_PRIVATE")
        return stream.read()


def _publish(path, data):
    with tempfile.NamedTemporaryFile(dir=path.parent, prefix=".get-proof-", delete=False) as stream:
        temporary = Path(stream.name)
        try:
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
            try:
                os.link(temporary, path)
            except FileExistsError:
                pass
            if _read_private_file(path) != data:
                raise ExecutionReconciliationProofStoreError("GET_PROOF_IMMUTABLE_CONFLICT")
            fd = os.open(path.parent, os.O_RDONLY)
            try:
                os.fsync(fd)
            finally:
                os.close(fd)
        finally:
            temporary.unlink(missing_ok=True)


def publish_authenticated_execution_reconciliation_proof_v1(
    *, root, proof, budget_owner_root, snapshot_received_at, position_coverage, bodies
):
    """Publish the exact acquired responses after the original budget commit."""
    path = _proof_path(root, proof.revision_ref)
    reads = []
    for get, body in zip(proof.gets, bodies, strict=True):
        if sha256(body).hexdigest() != get.body_sha256:
            raise ExecutionReconciliationProofStoreError("GET_PROOF_RAW_BODY_MISMATCH")
        reads.append(
            {
                **asdict(get),
                "acquired_at": get.acquired_at.isoformat(),
                "body": body.decode("utf-8"),
            }
        )
    record = {
        "schema": _SCHEMA,
        "venue_host": proof.venue_host,
        "account": proof.account,
        "session_id": proof.session_id,
        "reservation_id": proof.reservation_id,
        "identity_digest": proof.identity_digest,
        "budget_owner_root": budget_owner_root,
        "revision_ref": list(proof.revision_ref),
        "snapshot_digest": proof.snapshot_digest,
        "snapshot_received_at": snapshot_received_at.isoformat(),
        "position_interval": (
            None
            if position_coverage is None
            else [position_coverage["started_at_utc"], position_coverage["completed_at_utc"]]
        ),
        "gets": reads,
        "quantity_incident": _incident_payload(proof.quantity_incident),
    }
    data = _encode({"record": record, "sha256": sha256(_encode(record)).hexdigest()}) + b"\n"
    _publish(path, data)


def _aware(value):
    stamp = datetime.fromisoformat(value)
    if stamp.utcoffset() is None:
        raise ExecutionReconciliationProofStoreError("GET_PROOF_CLOCK_UNPROVEN")
    return stamp


def _decode_get(record):
    read = dict(record)
    body = read.pop("body").encode("utf-8")
    read["acquired_at"] = _aware(read["acquired_at"])
    get = ReconciliationGetProvenanceV1(**read)
    if sha256(body).hexdigest() != get.body_sha256:
        raise ExecutionReconciliationProofStoreError("GET_PROOF_RAW_BODY_MISMATCH")
    payload = json.loads(
        body, object_pairs_hook=_unique_json_object, parse_constant=_reject_json_constant
    )
    if (
        type(payload) is not dict
        or type(payload.get("code")) is not str
        or type(payload.get("data")) is not list
        or any(type(row) is not dict for row in payload["data"])
    ):
        raise ExecutionReconciliationProofStoreError("GET_PROOF_PAYLOAD_UNPROVEN")
    return get, payload


class _RecordedReconciliationGets:
    """Replay only the captured response in the original snapshot-builder call order."""

    def __init__(self, records):
        self._records = iter(records)

    def get(self, *, endpoint, auth_required, pretrade_decision_id, get_cache_policy):
        proof, payload = next(self._records)
        if (
            endpoint != proof.endpoint
            or pretrade_decision_id != proof.decision_id
            or auth_required is not True
            or get_cache_policy != GET_CACHE_POLICY_DYNAMIC_REFRESH_REQUIRED
        ):
            raise ExecutionReconciliationProofStoreError("GET_PROOF_REPLAY_REQUEST_MISMATCH")
        # Rebuild the original snapshot from the recorded response contract.
        # This injected port never supplies current venue or DataSafety evidence.
        return FreshPretradeGetTransportResultV1(
            get_performed=True,
            method="GET",
            endpoint=proof.endpoint,
            http_status=200,
            payload=payload,
            auth_header_sent=True,
            transport_class=TRANSPORT_CLASS_INJECTED_TEST_DOUBLE,
            venue_live_contact=False,
            historical_reuse=False,
            error_class="",
            body_sha256=proof.body_sha256,
            pretrade_decision_id=proof.decision_id,
            acquired_at_utc=proof.acquired_at.isoformat(),
        )


def read_authenticated_execution_reconciliation_proof_v1(
    *, root, budget_owner_root, account, session_id, reservation_id, revision_ref
) -> AuthenticatedExecutionReconciliationProofV1:
    return read_authenticated_execution_reconciliation_source_v1(
        root=root,
        budget_owner_root=budget_owner_root,
        account=account,
        session_id=session_id,
        reservation_id=reservation_id,
        revision_ref=revision_ref,
    ).proof


def read_authenticated_execution_reconciliation_source_v1(
    *, root, budget_owner_root, account, session_id, reservation_id, revision_ref
) -> AuthenticatedExecutionReconciliationSourceV1:
    """Read a historical receipt, then rebuild and verify its original budget input."""
    try:
        path = _proof_path(root, revision_ref)
        data = _read_private_file(path)
        envelope = json.loads(data, object_pairs_hook=_unique_json_object)
        record = envelope["record"]
        if (
            set(envelope) != {"record", "sha256"}
            or envelope["sha256"] != sha256(_encode(record)).hexdigest()
        ):
            raise ExecutionReconciliationProofStoreError("GET_PROOF_CONTENT_UNPROVEN")
        binding = {
            "schema": _SCHEMA,
            "venue_host": AUTHORIZED_HOST,
            "account": account,
            "session_id": session_id,
            "reservation_id": reservation_id,
            "budget_owner_root": str(budget_owner_root),
            "revision_ref": list(revision_ref),
        }
        if any(record.get(key) != value for key, value in binding.items()):
            raise ExecutionReconciliationProofStoreError("GET_PROOF_SCOPE_MISMATCH")
        revision = read_budget_revision_read_only_v1(
            Path(budget_owner_root),
            account_identity=account,
            sequence=revision_ref[0],
            expected_digest=revision_ref[1],
        )
        link = revision["state"]["execution_links"][reservation_id]
        identity = parse_exchange_reconciliation_identity_v1(link["identity"])
        if (
            type(identity) is not PortfolioExecutionReconciliationIdentityV2
            or identity.budget_owner_root != str(budget_owner_root)
            or identity.portfolio_reservation_id != reservation_id
            or identity.account_identity != account
            or identity.execution_environment != "LIVE"
            or identity.identity_digest() != record["identity_digest"]
            or link["phase"] != "SUBMIT_MAY_HAVE_OCCURRED"
        ):
            raise ExecutionReconciliationProofStoreError("GET_PROOF_BUDGET_IDENTITY_UNPROVEN")
        proof, snapshot = _replay(record, identity, link["reconciliation"], revision_ref)
        return AuthenticatedExecutionReconciliationSourceV1(
            proof,
            identity,
            snapshot,
            link["reconciliation"],
            revision["state"]["lane_bindings"].get(identity.slot_id, {}),
        )
    except ExecutionReconciliationProofStoreError:
        raise
    except (
        OSError,
        sqlite3.Error,
        AttributeError,
        KeyError,
        TypeError,
        ValueError,
        StopIteration,
    ) as exc:
        raise ExecutionReconciliationProofStoreError("GET_PROOF_READBACK_UNPROVEN") from exc


def _replay(record, identity, result, revision_ref):
    recorded_gets = tuple(_decode_get(row) for row in record["gets"])
    reads = tuple(get for get, _ in recorded_gets)
    if len(reads) != 6:
        raise ExecutionReconciliationProofStoreError("GET_PROOF_GET_COUNT_UNPROVEN")
    account_get, account_payload = recorded_gets[0]
    received_at = _aware(record["snapshot_received_at"])
    if (
        account_get.endpoint != ENDPOINT_ACCOUNT_CONFIG
        or account_get.decision_id != f"{record['session_id']}:execution-recovery"
        or account_payload.get("code") != "0"
        or len(account_payload["data"]) != 1
        or account_payload["data"][0].get("uid") != record["account"]
        or not account_get.acquired_at <= received_at <= reads[1].acquired_at
        or any(a.acquired_at > b.acquired_at for a, b in zip(reads, reads[1:]))
        or (reads[-1].acquired_at - account_get.acquired_at).total_seconds() > _MAX_AGE_SECONDS
    ):
        raise ExecutionReconciliationProofStoreError("GET_PROOF_GET_SEQUENCE_UNPROVEN")
    interval = record["position_interval"]
    if interval is not None and (
        type(interval) is not list
        or len(interval) != 2
        or _aware(interval[0]) > _aware(interval[1])
    ):
        raise ExecutionReconciliationProofStoreError("GET_PROOF_POSITION_INTERVAL_UNPROVEN")
    times = iter(interval if interval is not None else (received_at.isoformat(),) * 2)
    options = resolve_reconciliation_query_options_v1(
        instrument_id=identity.instrument_id, native_id=identity.native_id
    )
    snapshot = fetch_okx_read_only_reconciliation_snapshot_v1(
        identity=identity,
        options=options,
        read_only_get_transport=_RecordedReconciliationGets(recorded_gets[1:]),
        pretrade_decision_id=f"{record['session_id']}:{record['reservation_id']}",
        received_at=received_at.isoformat(),
        acquisition_clock=lambda: next(times),
    )
    if options.inst_type == "FUTURES":
        require_futures_reconciliation_product_v1(snapshot)
    snapshot_digest = sha256(json.dumps(snapshot.to_dict(), sort_keys=True).encode()).hexdigest()
    if (
        snapshot_digest != result["snapshot_digest"]
        or snapshot_digest != record["snapshot_digest"]
        or result["identity_digest"] != record["identity_digest"]
    ):
        raise ExecutionReconciliationProofStoreError("GET_PROOF_SNAPSHOT_UNPROVEN")
    finding = adjudicate_reconciliation_quantity_incident_v1(
        session_id=record["session_id"],
        observed_at=reads[-1].acquired_at.astimezone(timezone.utc),
        identity=identity,
        snapshot=snapshot,
        result=result,
    )
    if _incident_payload(finding) != record["quantity_incident"]:
        raise ExecutionReconciliationProofStoreError("GET_PROOF_INCIDENT_UNPROVEN")
    proof = AuthenticatedExecutionReconciliationProofV1(
        venue_host=record["venue_host"],
        account=record["account"],
        session_id=record["session_id"],
        reservation_id=record["reservation_id"],
        identity_digest=record["identity_digest"],
        revision_ref=revision_ref,
        snapshot_digest=snapshot_digest,
        gets=reads,
        quantity_incident=finding,
    )
    return proof, snapshot
