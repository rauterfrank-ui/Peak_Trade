"""Original K1 GET provenance for PortfolioHost reconciliation, without Safety delivery."""

from dataclasses import dataclass
from datetime import datetime, timezone
from hashlib import sha256
import json
from urllib.parse import urlsplit

from src.data.safety import DataSourceKind
from src.ops.execution_ghosv_fill_quantity_v1 import (
    ExecutionFillQuantityIncidentV1,
    build_execution_fill_quantity_incident_v1,
)
from src.ops.full_core_live_path_composition_root_v1.checkout_independent_credential_okx_venue_auth_headers_v1 import (
    FullCoreK1BoundVenueAuthHandleV1,
)
from src.ops.full_core_live_path_composition_root_v1.fresh_pretrade_runtime_get_v1 import (
    ENDPOINT_ACCOUNT_CONFIG,
    ENDPOINT_ACCOUNT_POSITIONS,
    GET_CACHE_POLICY_DYNAMIC_REFRESH_REQUIRED,
    TRANSPORT_CLASS_PRODUCTIVE_READ_ONLY_GET,
    FreshPretradeGetTransportResultV1,
)
from src.ops.full_core_live_path_composition_root_v1.full_core_exchange_reconciliation_okx_read_only_provider_v1 import (
    ENDPOINT_ORDERS_HISTORY,
    ENDPOINT_ORDERS_PENDING,
    ENDPOINT_TRADE_FILLS,
    OkxReadOnlyReconciliationQueryOptionsV1,
)
from src.ops.full_core_live_path_composition_root_v1.current_productive_future_identity_semantics_v1 import (
    resolve_selected_future_market_type_v1,
)
from src.ops.full_core_live_path_composition_root_v1.full_core_exchange_reconciliation_v1 import (
    LocalSubmitOutcome,
    adjudicate_full_core_exchange_reconciliation_v1,
)
from src.ops.full_core_live_path_composition_root_v1.productive_read_only_get_transport_v1 import (
    AUTHORIZED_HOST,
    READ_ONLY_EXACT_ORDER_LOOKUP_PATH,
    FullCoreProductiveReadOnlyGetTransportV1,
)
from src.ops.okx_eea_private_account_state_runtime_v1.constants_v1 import (
    POSITION_OBSERVATION_FRESHNESS_MAX_AGE_MS,
)
from src.ops.portfolio_capital_reservation_budget_v1.execution_v1 import (
    read_persisted_execution_reconciliation_v1,
)
from trading.master_v2.double_play_futures_input import FuturesMarketType

_MAX_AGE_SECONDS = POSITION_OBSERVATION_FRESHNESS_MAX_AGE_MS / 1000
_ORDER_GETS = (
    ENDPOINT_ORDERS_PENDING,
    ENDPOINT_ORDERS_HISTORY,
    ENDPOINT_TRADE_FILLS,
    ENDPOINT_ACCOUNT_POSITIONS,
    READ_ONLY_EXACT_ORDER_LOOKUP_PATH,
)


class ExecutionReconciliationSourceError(ValueError):
    """The GET result could not be bound to the original source."""


def resolve_reconciliation_query_options_v1(*, instrument_id, native_id):
    market_type = resolve_selected_future_market_type_v1(
        instrument_id=instrument_id, venue_native_id=native_id
    )
    return OkxReadOnlyReconciliationQueryOptionsV1(
        inst_type="FUTURES" if market_type is FuturesMarketType.FUTURES else "SWAP"
    )


def require_futures_reconciliation_product_v1(snapshot):
    if any(
        item.payload.get("instType", "FUTURES") != "FUTURES" for item in snapshot.evidence_items
    ):
        raise ExecutionReconciliationSourceError("RECONCILIATION_GET_FUTURES_PRODUCT_MISMATCH")


def _unique_json_object(pairs):
    obj = dict(pairs)
    if len(obj) != len(pairs):
        raise ExecutionReconciliationSourceError("RECONCILIATION_GET_DUPLICATE_RESPONSE_KEY")
    return obj


def _reject_json_constant(_value):
    raise ExecutionReconciliationSourceError("RECONCILIATION_GET_INVALID_JSON_NUMBER")


@dataclass(frozen=True)
class ReconciliationGetProvenanceV1:
    endpoint: str
    decision_id: str
    acquired_at: datetime
    body_sha256: str

    def to_reference_v1(self) -> dict[str, str]:
        return {
            "endpoint": self.endpoint,
            "decision_id": self.decision_id,
            "acquired_at": self.acquired_at.isoformat(),
            "body_sha256": self.body_sha256,
        }


@dataclass(frozen=True)
class AuthenticatedExecutionReconciliationProofV1:
    venue_host: str
    account: str
    session_id: str
    reservation_id: str
    identity_digest: str
    revision_ref: tuple[int, str]
    snapshot_digest: str
    gets: tuple[ReconciliationGetProvenanceV1, ...]
    quantity_incident: ExecutionFillQuantityIncidentV1 | None


def adjudicate_reconciliation_quantity_incident_v1(
    *, session_id, observed_at, identity, snapshot, result
):
    local_outcome = LocalSubmitOutcome(result["local_submit_outcome"])
    decision = adjudicate_full_core_exchange_reconciliation_v1(
        identity=identity,
        snapshot=snapshot,
        local_submit_outcome=local_outcome,
        proven_never_submitted=result["local_submit_evidence"] is not None,
    )
    if decision.to_dict() != result["decision"]:
        raise ExecutionReconciliationSourceError("RECONCILIATION_GET_DECISION_UNPROVEN")
    if local_outcome is not LocalSubmitOutcome.TRANSPORT_UNKNOWN:
        return None
    return build_execution_fill_quantity_incident_v1(
        session_id=session_id,
        observed_at=observed_at,
        identity=identity,
        snapshot=snapshot,
        decision=decision,
        local_submit_outcome=local_outcome,
    )


class AuthenticatedReconciliationGetV1:
    """Observe the concrete K1 transport and bind every raw response before consumption."""

    def __init__(self, transport, *, account, clock, proof_root=None, retain_response_bodies=False):
        if type(transport) is not FullCoreProductiveReadOnlyGetTransportV1:
            raise ExecutionReconciliationSourceError("RECONCILIATION_GET_ORIGINAL_PORT_REQUIRED")
        handle = transport._handle
        if type(handle) is not FullCoreK1BoundVenueAuthHandleV1:
            raise ExecutionReconciliationSourceError("RECONCILIATION_GET_K1_HANDLE_REQUIRED")
        self.transport = transport
        self._handle = handle
        self.account = account
        self.clock = clock
        if proof_root is not None:
            from src.ops.execution_reconciliation_proof_store_v1 import (
                require_private_proof_root_v1,
            )

            proof_root = require_private_proof_root_v1(proof_root)
        self.proof_root = proof_root
        self._retain_bodies = proof_root is not None or retain_response_bodies
        self.evidence: dict[str, AuthenticatedExecutionReconciliationProofV1] = {}
        self.account_position_mode = None
        self.position_margin_modes = {}
        self._gets: dict[str, list[ReconciliationGetProvenanceV1]] = {}
        self._bodies: dict[str, list[bytes]] = {}

    def reset_v1(self):
        self.evidence.clear()
        self.account_position_mode = None
        self.position_margin_modes.clear()
        self._gets.clear()
        self._bodies.clear()

    def get(self, *, endpoint, auth_required, pretrade_decision_id, get_cache_policy):
        parsed = urlsplit(endpoint)
        if (
            auth_required is not True
            or get_cache_policy != GET_CACHE_POLICY_DYNAMIC_REFRESH_REQUIRED
            or self.transport._handle is not self._handle
            or parsed.scheme
            or parsed.netloc
            or parsed.fragment
            or parsed.path not in (ENDPOINT_ACCOUNT_CONFIG, *_ORDER_GETS)
            or (parsed.path == ENDPOINT_ACCOUNT_CONFIG and endpoint != ENDPOINT_ACCOUNT_CONFIG)
        ):
            raise ExecutionReconciliationSourceError("RECONCILIATION_GET_REQUEST_UNPROVEN")
        started_at = self.clock()
        result, body = self.transport.get_authenticated_response_v1(
            endpoint=endpoint, pretrade_decision_id=pretrade_decision_id
        )
        completed_at = self.clock()
        if (
            self.transport._handle is not self._handle
            or type(result) is not FreshPretradeGetTransportResultV1
            or result.get_performed is not True
            or result.method != "GET"
            or result.endpoint != endpoint
            or result.pretrade_decision_id != pretrade_decision_id
            or result.http_status != 200
            or result.auth_header_sent is not True
            or result.historical_reuse is not False
            or result.venue_live_contact is not True
            or result.transport_class != TRANSPORT_CLASS_PRODUCTIVE_READ_ONLY_GET
            or result.data_safety_source_kind != DataSourceKind.REAL.value
            or result.error_class
            or not body
            or sha256(body).hexdigest() != result.body_sha256
        ):
            raise ExecutionReconciliationSourceError("RECONCILIATION_GET_RESPONSE_UNPROVEN")
        try:
            acquired = datetime.fromisoformat(result.acquired_at_utc.replace("Z", "+00:00"))
            payload = json.loads(
                body, object_pairs_hook=_unique_json_object, parse_constant=_reject_json_constant
            )
            same_payload = json.dumps(payload, sort_keys=True, allow_nan=False) == json.dumps(
                result.payload, sort_keys=True, allow_nan=False
            )
        except (AttributeError, TypeError, ValueError) as exc:
            raise ExecutionReconciliationSourceError(
                "RECONCILIATION_GET_RESPONSE_UNPROVEN"
            ) from exc
        if (
            acquired.utcoffset() is None
            or not started_at <= acquired.timestamp() <= completed_at
            or not 0 <= completed_at - started_at <= _MAX_AGE_SECONDS
        ):
            raise ExecutionReconciliationSourceError("RECONCILIATION_GET_ACQUISITION_UNPROVEN")
        if (
            type(payload) is not dict
            or not same_payload
            or type(payload.get("code")) is not str
            or type(payload.get("data")) is not list
            or any(type(row) is not dict for row in payload["data"])
        ):
            raise ExecutionReconciliationSourceError("RECONCILIATION_GET_PAYLOAD_UNPROVEN")
        if endpoint == ENDPOINT_ACCOUNT_CONFIG and (
            payload["code"] != "0"
            or len(payload["data"]) != 1
            or payload["data"][0].get("uid") != self.account
        ):
            raise ExecutionReconciliationSourceError("RECONCILIATION_GET_ACCOUNT_UNPROVEN")
        if endpoint == ENDPOINT_ACCOUNT_CONFIG:
            self.account_position_mode = payload["data"][0].get("posMode")
        self._gets.setdefault(pretrade_decision_id, []).append(
            ReconciliationGetProvenanceV1(
                endpoint=endpoint,
                decision_id=pretrade_decision_id,
                acquired_at=acquired,
                body_sha256=result.body_sha256,
            )
        )
        if self._retain_bodies:
            self._bodies.setdefault(pretrade_decision_id, []).append(body)
        return result

    def original_handle_v1(self):
        if self.transport._handle is not self._handle:
            raise ExecutionReconciliationSourceError("RECONCILIATION_GET_HANDLE_CHANGED")
        return self._handle

    def discard_response_bodies_v1(self):
        self._bodies.clear()

    def completed_order_read_set_v1(self, *, account_decision_id, order_decision_id, observed_at):
        self.original_handle_v1()
        account_reads = self._gets.get(account_decision_id, ())
        order_reads = self._gets.get(order_decision_id, ())
        reads = (*account_reads, *order_reads)
        if (
            len(account_reads) != 1
            or account_reads[0].endpoint != ENDPOINT_ACCOUNT_CONFIG
            or tuple(urlsplit(read.endpoint).path for read in order_reads) != _ORDER_GETS
        ):
            raise ExecutionReconciliationSourceError("RECONCILIATION_GET_SEQUENCE_UNPROVEN")
        first = reads[0].acquired_at.timestamp()
        if (
            not reads[0].acquired_at <= observed_at <= reads[1].acquired_at
            or any(a.acquired_at > b.acquired_at for a, b in zip(reads, reads[1:]))
            or not reads[-1].acquired_at.timestamp() <= self.clock() <= first + _MAX_AGE_SECONDS
        ):
            raise ExecutionReconciliationSourceError("RECONCILIATION_GET_WINDOW_UNPROVEN")
        bodies = (
            *self._bodies.get(account_decision_id, ()),
            *self._bodies.get(order_decision_id, ()),
        )
        return reads, bodies

    def record_v1(self, host, rid, identity, snapshot, observed_at, result, *, publish_proof=True):
        if (
            not (host.account == identity.account_identity == self.account)
            or identity.execution_environment != "LIVE"
            or identity.portfolio_reservation_id != rid
        ):
            raise ExecutionReconciliationSourceError("RECONCILIATION_GET_SEQUENCE_UNPROVEN")
        reads, _ = self.completed_order_read_set_v1(
            account_decision_id=f"{host.session_id}:execution-recovery",
            order_decision_id=f"{host.session_id}:{rid}",
            observed_at=observed_at,
        )
        sequence, checksum, link = read_persisted_execution_reconciliation_v1(host.owner, rid)
        snapshot_digest = sha256(
            json.dumps(snapshot.to_dict(), sort_keys=True).encode()
        ).hexdigest()
        identity_digest = identity.identity_digest()
        if (
            link["identity"] != identity.to_dict()
            or link["reconciliation"] != result
            or result["identity_digest"] != identity_digest
            or result["snapshot_digest"] != snapshot_digest
        ):
            raise ExecutionReconciliationSourceError("RECONCILIATION_GET_BUDGET_READBACK_UNPROVEN")
        finding = adjudicate_reconciliation_quantity_incident_v1(
            session_id=host.session_id,
            observed_at=reads[-1].acquired_at.astimezone(timezone.utc),
            identity=identity,
            snapshot=snapshot,
            result=result,
        )
        proof = AuthenticatedExecutionReconciliationProofV1(
            venue_host=AUTHORIZED_HOST,
            account=self.account,
            session_id=host.session_id,
            reservation_id=rid,
            identity_digest=identity_digest,
            revision_ref=(sequence, checksum),
            snapshot_digest=snapshot_digest,
            gets=reads,
            quantity_incident=finding,
        )
        if self.proof_root is not None and publish_proof:
            self._publish_proof_v1(
                root=self.proof_root,
                proof=proof,
                identity=identity,
                snapshot=snapshot,
                observed_at=observed_at,
            )
        self.evidence[rid] = proof
        positions = (snapshot.positions_observation or {}).get("response") or {}
        self.position_margin_modes[rid] = tuple(
            row.get("mgnMode")
            for row in positions.get("data", ())
            if row.get("instId") == identity.native_id
        )

    def publish_current_proof_v1(self, *, identity, snapshot, observed_at):
        if self.proof_root is None:
            return
        self._publish_proof_v1(
            root=self.proof_root,
            proof=self.evidence[identity.portfolio_reservation_id],
            identity=identity,
            snapshot=snapshot,
            observed_at=observed_at,
        )

    def publish_incident_proof_v1(self, *, root, identity, snapshot, observed_at):
        proof = self.evidence[identity.portfolio_reservation_id]
        if not self._retain_bodies or proof.quantity_incident is None:
            raise ExecutionReconciliationSourceError("RECONCILIATION_GET_INCIDENT_PROOF_MISSING")
        self._publish_proof_v1(
            root=root, proof=proof, identity=identity, snapshot=snapshot, observed_at=observed_at
        )

    def _publish_proof_v1(self, *, root, proof, identity, snapshot, observed_at):
        from src.ops.execution_reconciliation_proof_store_v1 import (
            publish_authenticated_execution_reconciliation_proof_v1,
        )

        publish_authenticated_execution_reconciliation_proof_v1(
            root=root,
            proof=proof,
            budget_owner_root=identity.budget_owner_root,
            snapshot_received_at=observed_at,
            position_coverage=(snapshot.positions_observation or {}).get("query_coverage"),
            bodies=(
                *self._bodies[f"{proof.session_id}:execution-recovery"],
                *self._bodies[f"{proof.session_id}:{proof.reservation_id}"],
            ),
        )
