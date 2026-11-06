"""Dedicated observation-read adapter and atomic legacy startup document export.

A caller-owned authorized session supplies the credential/transport pair. This
module never acquires secrets, opens a session, creates an owner or enables a
service. Transport evidence is checked, not manufactured.
"""

from __future__ import annotations

from contextlib import contextmanager
import json
import math
import os
from pathlib import Path
import re
import tempfile
import time
from urllib.parse import urlencode

from src.ops.full_core_live_path_composition_root_v1.fresh_pretrade_runtime_get_v1 import (
    GET_CACHE_POLICY_DYNAMIC_REFRESH_REQUIRED,
    FreshPretradeGetTransportResultV1,
)
from src.ops.okx_eea_private_account_state_runtime_v1.constants_v1 import (
    BASELINE_REST_RECOVERY_ALLOWLIST,
)
from src.ops.okx_eea_private_account_state_runtime_v1.credentials_v1 import (
    ObservationCredentialHandleV1,
    validate_credential_class_v1,
)
from src.ops.portfolio_capital_reservation_budget_v1.host_v1 import (
    collect_host_account_observation_v1,
)
from src.ops.productive_reconciliation_runtime_binding_v1.startup_portfolio_document_v1 import (
    read_startup_portfolio_document_v1,
)


ALGO_PENDING_PATH = "/api/v5/trade/orders-algo-pending"
SUPPORTED_ALGO_TYPES = ("conditional", "oco", "trigger", "move_order_stop")


class AccountObservationSourceError(ValueError):
    """Account source is not suitable for the existing startup contract."""


class AccountObservationSourceV1:
    """Adapt one explicitly paired observation credential and GET-only transport.

    The trusted composition root must bind the transport to this credential.
    Matching declarations do not prove that a foreign transport authenticated.
    Direct callable compatibility lets existing N1/host consumers use this
    source without a second account collector or reservation owner.
    """

    def __init__(
        self, *, credential, transport, expected_account_identity, session_id, clock=time.time
    ):
        self._validate_credential_v1(credential)
        if (
            not isinstance(expected_account_identity, str)
            or not expected_account_identity.strip()
            or expected_account_identity != expected_account_identity.strip()
        ):
            raise AccountObservationSourceError("OBSERVATION_EXPECTED_ACCOUNT_REQUIRED")
        if not isinstance(session_id, str) or not session_id.strip():
            raise AccountObservationSourceError("OBSERVATION_SESSION_REQUIRED")
        if not callable(getattr(transport, "get", None)):
            raise AccountObservationSourceError("OBSERVATION_GET_PORT_REQUIRED")
        self.credential = credential
        self.transport = transport
        self.expected_account_identity = expected_account_identity
        self.session_id = session_id
        self.clock = clock
        self.closed = False

    def _validate_credential_v1(self, credential):
        if not isinstance(credential, ObservationCredentialHandleV1):
            raise AccountObservationSourceError("OBSERVATION_CREDENTIAL_REQUIRED")
        validate_credential_class_v1(credential.identity.credential_class)
        if (
            credential.identity.bound is not True
            or not credential.identity.uri
            or credential.signing_capable is not True
            or any(
                v is not False
                for v in (
                    credential.rest_post_authority,
                    credential.ws_order_send_authority,
                    credential.ws_amend_authority,
                    credential.ws_cancel_authority,
                    credential.k2_present,
                )
            )
        ):
            raise AccountObservationSourceError("OBSERVATION_CREDENTIAL_SCOPE_INVALID")

    def close(self):
        # The enclosing session provider owns transport/credential release.
        self.closed = True
        self.transport = None
        self.credential = None

    def __call__(self, path, params):
        if self.closed:
            raise AccountObservationSourceError("OBSERVATION_SESSION_CLOSED")
        if path not in BASELINE_REST_RECOVERY_ALLOWLIST:
            raise AccountObservationSourceError("OBSERVATION_ENDPOINT_NOT_ALLOWED")
        expected_params = (
            {}
            if path in {"/api/v5/account/config", "/api/v5/account/balance"}
            else {"instType": "SWAP"}
        )
        query = dict(params)
        if (
            path
            in {
                "/api/v5/trade/orders-pending",
                "/api/v5/trade/orders-history",
                "/api/v5/trade/fills",
            }
            and "instId" in query
        ):
            # Older private recovery supplies an instrument filter. Like the
            # shared host collector, widen that request to the account scope;
            # never hide another instrument's orders behind this old default.
            native = query.pop("instId")
            if not isinstance(native, str) or not native.strip():
                raise AccountObservationSourceError("OBSERVATION_ACCOUNT_SCOPE_REQUIRED")
        if query != expected_params:
            raise AccountObservationSourceError("OBSERVATION_ACCOUNT_SCOPE_REQUIRED")
        payload = self._verified_get_v1(path, expected_params)
        if path == "/api/v5/account/config":
            if (
                len(payload["data"]) != 1
                or payload["data"][0].get("uid") != self.expected_account_identity
            ):
                raise AccountObservationSourceError("OBSERVATION_ACCOUNT_MISMATCH")
        if path == "/api/v5/trade/orders-pending":
            if payload["data"]:
                raise AccountObservationSourceError("STARTUP_PENDING_ORDERS_UNRESOLVED")
            # Ordinary pending orders exclude untriggered algo orders. Their
            # absence must also be observed before claiming a clear SWAP book.
            for kind in SUPPORTED_ALGO_TYPES:
                algo = self._verified_get_v1(
                    ALGO_PENDING_PATH, {"instType": "SWAP", "ordType": kind}
                )
                if algo["data"]:
                    raise AccountObservationSourceError("STARTUP_PENDING_ALGO_ORDERS_UNRESOLVED")
        return payload

    def _verified_get_v1(self, path, params):
        # This private helper has only fixed internal callers; public callback
        # scope remains the existing recovery allowlist. No mutation endpoints.
        endpoint = path + ("?" + urlencode(params) if params else "")
        result = self.transport.get(
            endpoint=endpoint,
            auth_required=True,
            pretrade_decision_id=self.session_id,
            get_cache_policy=GET_CACHE_POLICY_DYNAMIC_REFRESH_REQUIRED,
        )
        if not isinstance(result, FreshPretradeGetTransportResultV1) or not (
            result.get_performed is True
            and result.method == "GET"
            and result.endpoint == endpoint
            and result.http_status == 200
            and result.auth_header_sent is True
            and result.venue_live_contact is True
            and result.historical_reuse is False
            and not result.error_class
            and re.fullmatch(r"[0-9a-f]{64}", result.body_sha256 or "")
        ):
            raise AccountObservationSourceError("OBSERVATION_GET_EVIDENCE_INVALID")
        payload = result.payload
        if (
            not isinstance(payload, dict)
            or str(payload.get("code")) != "0"
            or not isinstance(payload.get("data"), list)
            or any(not isinstance(row, dict) for row in payload["data"])
        ):
            raise AccountObservationSourceError("OBSERVATION_RESPONSE_INVALID")
        # Baseline endpoints expose plain response envelopes. Unknown envelope
        # fields (e.g. continuation metadata) need an explicit contract review.
        if set(payload) - {"code", "msg", "data"}:
            raise AccountObservationSourceError("OBSERVATION_RESPONSE_SCOPE_UNPROVEN")
        return payload

    def collect_v1(self, *, instrument_ids_by_native_id):
        return collect_host_account_observation_v1(
            private_rest_fetch=self,
            instrument_ids_by_native_id=instrument_ids_by_native_id,
            session_id=self.session_id,
            clock=self.clock,
            expected_account=self.expected_account_identity,
        )

    def export_startup_document_v1(self, path, *, instrument_ids_by_native_id):
        """Acquire and publish a fresh document once, never overwrite a file.

        Supported scope is SWAP positions plus ordinary pending orders and
        the four documented algo types; not all venue products/bot services.
        The parent must already be a private directory chosen by the caller.
        """
        target = Path(path)
        if not target.is_absolute() or not target.parent.is_dir():
            raise AccountObservationSourceError("STARTUP_EXPORT_PRIVATE_ABSOLUTE_PATH_REQUIRED")
        if target.exists() or target.is_symlink():
            raise AccountObservationSourceError("STARTUP_EXPORT_TARGET_EXISTS")
        observation = self.collect_v1(instrument_ids_by_native_id=instrument_ids_by_native_id)
        snap = observation.observed
        payload = {
            "schema": "peaktrade.startup_portfolio_observation.v1",
            "account_identity": observation.account,
            "instrument_type": "SWAP",
            "complete_account_scope": True,
            "pending_orders": observation.pending_orders,
            "source_id": snap.source_id,
            "event_time_unix": snap.event_time_unix,
            "wall_time_unix": snap.wall_time_unix,
            "positions": [
                {
                    "instrument_id": p.instrument_id,
                    "signed_quantity": str(p.signed_quantity),
                    "side": p.side,
                }
                for p in snap.positions
            ],
        }
        fd, temporary = tempfile.mkstemp(prefix=".startup-observation-", dir=target.parent)
        temp = Path(temporary)
        try:
            with os.fdopen(fd, "w") as stream:
                json.dump(payload, stream, allow_nan=False, sort_keys=True)
                stream.write("\n")
                stream.flush()
                os.fsync(stream.fileno())
            now = self.clock()
            if isinstance(now, bool) or not isinstance(now, (int, float)) or not math.isfinite(now):
                raise AccountObservationSourceError("STARTUP_EXPORT_CLOCK_INVALID")
            read_startup_portfolio_document_v1(
                temp, expected_account_identity=self.expected_account_identity, now_unix=now
            )
            # Same-directory link atomically publishes without replacing even
            # a concurrently created file/symlink. mkstemp permissions are 0600.
            os.link(temp, target)
        finally:
            temp.unlink(missing_ok=True)
        return observation


@contextmanager
def open_account_observation_source_v1(
    *, session_provider, expected_account_identity, session_id, clock=time.time
):
    """Compose a caller-authorized session, never synthesize an acquisition.

    provider() is a context manager yielding (dedicated credential, transport).
    Its acquisition, host, credential binding and cleanup remain provider-owned.
    No default provider or K1 fallback exists.
    """
    if not callable(session_provider):
        raise AccountObservationSourceError("OBSERVATION_SESSION_PROVIDER_REQUIRED")
    with session_provider() as (credential, transport):
        source = AccountObservationSourceV1(
            credential=credential,
            transport=transport,
            expected_account_identity=expected_account_identity,
            session_id=session_id,
            clock=clock,
        )
        try:
            yield source
        finally:
            source.close()
