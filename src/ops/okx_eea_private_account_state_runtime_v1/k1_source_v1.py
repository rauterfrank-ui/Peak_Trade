"""Explicit K1 account-read profile; never relabel K1 as a dedicated read key.

Uses the existing K1 OS-store/signing session and productive GET transport.
No fallback from the dedicated observer credential contract and no POST port.
"""

from contextlib import contextmanager
from pathlib import Path
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
import json
from urllib.parse import parse_qsl, urlsplit
import time

from src.ops.full_core_live_path_composition_root_v1.checkout_independent_credential_okx_venue_auth_headers_v1 import (
    FullCoreK1BoundVenueAuthHandleV1,
)
from src.ops.full_core_live_path_composition_root_v1.current_productive_governed_live_c1_get_only_fresh_pretrade_transport_bind_v1 import (
    open_governed_live_c1_get_only_fresh_pretrade_transport_v1,
)
from src.ops.full_core_live_path_composition_root_v1.productive_read_only_get_transport_v1 import (
    FullCoreProductiveReadOnlyGetTransportV1,
)
from src.ops.okx_eea_private_account_state_runtime_v1.constants_v1 import (
    BASELINE_REST_RECOVERY_ALLOWLIST,
)
from src.ops.okx_eea_private_account_state_runtime_v1.startup_source_v1 import (
    ALGO_PENDING_PATH,
    SUPPORTED_ALGO_TYPES,
    AccountObservationSourceError,
    AccountObservationSourceV1,
)

K1_ACCOUNT_READ_PROFILE = "K1_ACCOUNT_OBSERVATION_GET_ONLY_V1"


def load_k1_account_source_config_v1(path):
    """Load identifier-only explicit K1 selection; never acquire a credential."""
    from src.ops.full_core_live_path_composition_root_v1.checkout_independent_credential_concrete_backend_item_identity_v1 import (
        KEYCHAIN_SERVICE_ID,
        KEYCHAIN_ACCOUNT_ID,
        SOURCE_REF_URI,
    )

    def unique(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise AccountObservationSourceError("K1_SOURCE_CONFIG_DUPLICATE_FIELD")
            result[key] = value
        return result

    value = json.loads(Path(path).read_text(), object_pairs_hook=unique)
    expected = {
        "schema": "peaktrade.k1_account_source.v1",
        "profile": K1_ACCOUNT_READ_PROFILE,
        "keychain_service": KEYCHAIN_SERVICE_ID,
        "keychain_account": KEYCHAIN_ACCOUNT_ID,
        "source_ref": SOURCE_REF_URI,
        "rest_host": "eea.okx.com",
        "max_request_count": 10,
        "service_activation_authorized": False,
    }
    if not isinstance(value, dict) or set(value) != set(expected) | {"expected_account_identity"}:
        raise AccountObservationSourceError("K1_SOURCE_CONFIG_FIELDS_INVALID")
    if any(type(value[k]) is not type(v) or value[k] != v for k, v in expected.items()):
        raise AccountObservationSourceError("K1_SOURCE_CONFIG_SCOPE_INVALID")
    account = value["expected_account_identity"]
    if not isinstance(account, str) or not account or account != account.strip():
        raise AccountObservationSourceError("OBSERVATION_EXPECTED_ACCOUNT_REQUIRED")
    return value


class _AccountReadTransportV1:
    def __init__(self, transport):
        self._transport = transport
        self.last_read = None
        self.read_count = 0

    def get(self, *, endpoint, auth_required, **kwargs):
        parsed = urlsplit(endpoint)
        pairs = parse_qsl(parsed.query, keep_blank_values=True)
        params = dict(pairs)
        if (
            parsed.scheme
            or parsed.netloc
            or parsed.fragment
            or len(params) != len(pairs)
            or auth_required is not True
        ):
            raise AccountObservationSourceError("K1_ACCOUNT_READ_SCOPE_INVALID")
        path = parsed.path
        if path in {
            "/api/v5/account/bills-archive",
            "/api/v5/account/bills",
            "/api/v5/asset/bills-history",
        }:
            if (
                params.get("limit") != "100"
                or set(params) not in ({"limit"}, {"limit", "after"})
                or (
                    "after" in params
                    and (
                        not params["after"].isascii()
                        or not params["after"].isdigit()
                        or not 1 <= len(params["after"]) <= 40
                        or int(params["after"]) <= 0
                    )
                )
            ):
                raise AccountObservationSourceError("K1_ACCOUNT_READ_SCOPE_INVALID")
        expected = (
            {}
            if path
            in {
                "/api/v5/account/config",
                "/api/v5/account/balance",
                "/api/v5/asset/balances",
                "/api/v5/account/subtypes",
            }
            else {"instType": "SWAP"}
        )
        if path == ALGO_PENDING_PATH:
            if params.get("ordType") not in SUPPORTED_ALGO_TYPES:
                raise AccountObservationSourceError("K1_ALGO_TYPE_UNSUPPORTED")
            expected = {"instType": "SWAP", "ordType": params["ordType"]}
        elif path in {
            "/api/v5/account/bills-archive",
            "/api/v5/account/bills",
            "/api/v5/asset/bills-history",
        }:
            expected = params
        elif path == "/api/v5/account/subtypes":
            expected = {}
        elif path not in BASELINE_REST_RECOVERY_ALLOWLIST and path != "/api/v5/asset/balances":
            raise AccountObservationSourceError("K1_ACCOUNT_READ_ENDPOINT_FORBIDDEN")
        # Fixed scope-inspection reads may omit instType to expose products
        # outside the SWAP consumer contract. They cannot hide those products.
        full_scope = (
            path in {"/api/v5/account/positions", "/api/v5/trade/orders-pending"} and params == {}
        ) or (
            path == ALGO_PENDING_PATH
            and params == {"ordType": params.get("ordType")}
            and params.get("ordType") in SUPPORTED_ALGO_TYPES
        )
        if params != expected and not full_scope:
            raise AccountObservationSourceError("K1_ACCOUNT_READ_SCOPE_INVALID")
        self.read_count += 1
        self.last_read = {"endpoint_path": path, "method": "GET", "completion_evidence": False}
        result = self._transport.get(endpoint=endpoint, auth_required=True, **kwargs)
        self.last_read = {
            "endpoint_path": path,
            "method": result.method,
            "http_status": result.http_status,
            "get_performed": result.get_performed,
            "transport_error_present": bool(result.error_class),
            "historical_reuse": result.historical_reuse,
        }
        return result


class K1AccountObservationSourceV1(AccountObservationSourceV1):
    """Share normalization/export with the dedicated profile, retain K1 identity."""

    credential_profile = K1_ACCOUNT_READ_PROFILE

    def __init__(self, *, credential, transport, **kwargs):
        if (
            not isinstance(transport, FullCoreProductiveReadOnlyGetTransportV1)
            or transport._handle is not credential
        ):
            raise AccountObservationSourceError("K1_ACCOUNT_READ_HANDLE_BINDING_REQUIRED")
        super().__init__(
            credential=credential, transport=_AccountReadTransportV1(transport), **kwargs
        )

    def inspect_accounting_bills_v1(self, *, max_pages=6):
        """Bounded, unfiltered archive pagination; no stock or sizing adoption.

        Deliberately query through an empty page, rather than treating a short
        page as a completeness proof. Even exhaustion proves only that this
        endpoint returned no older rows, not a classified complete event stream.
        Returns hashes/counts, never raw rows or account amounts. No retries.
        """
        from src.ops.okx_eea_private_account_state_runtime_v1.bills_observation_v1 import (
            audit_bill_pages_v1,
            canonical_digest_v1,
            BillsObservationError,
        )

        if self.closed:
            raise AccountObservationSourceError("OBSERVATION_SESSION_CLOSED")
        if type(max_pages) is not int or not 1 <= max_pages <= 6:
            raise AccountObservationSourceError("BILL_PAGE_BUDGET_INVALID")
        started = self.clock()
        self("/api/v5/account/config", {})
        binding = canonical_digest_v1(
            {
                "account_identity": self.expected_account_identity,
                "venue_host": "eea.okx.com",
            }
        )
        pages = []
        cursor = None
        exhausted = False
        for _ in range(max_pages):
            params = {"limit": "100"}
            if cursor is not None:
                params["after"] = str(cursor)
            path = "/api/v5/account/bills-archive"
            rows = self._verified_get_v1(path, params)["data"]
            page = {"account_binding_digest": binding, "endpoint_path": path, "rows": rows}
            # Validate before trusting native IDs as pagination cursors.
            audit_bill_pages_v1([page], account_binding_digest=binding)
            ids = [int(row["billId"]) for row in rows]
            if any(a <= b for a, b in zip(ids, ids[1:])) or (
                cursor is not None and any(bid >= cursor for bid in ids)
            ):
                raise BillsObservationError("BILL_PAGINATION_NOT_PROGRESSING")
            pages.append(page)
            if not rows:
                exhausted = True
                break
            cursor = ids[-1]
        report = audit_bill_pages_v1(pages, account_binding_digest=binding)
        report.update(
            profile=K1_ACCOUNT_READ_PROFILE,
            configured_account_matched=True,
            observed_at_unix=started,
            completed_at_unix=self.clock(),
            page_count=len(pages),
            endpoint_pagination_exhausted=exhausted,
            retention_coverage_proven=False,
            opening_anchor_bound=False,
            observation_only=True,
            blockers=[
                "CLASSIFIED_EVENT_STREAM_COMPLETENESS_UNPROVEN",
                "CURRENT_OPENING_STOCK_BRIDGE_UNPROVEN",
            ]
            + ([] if exhausted else ["BILL_PAGE_BUDGET_EXHAUSTED"])
            + ([] if report["observed_chain_consistent"] else ["BILL_BALANCE_CHAIN_BREAK"]),
        )
        return report

    def inspect_account_scope_v1(self):
        """Seven fresh read-only queries; no amounts, UID or raw rows returned.

        Audit all-position/order product coverage before relying on SWAP-only
        consumers. This is an observation, never an account adoption or mint.
        Other products and missing instrument types remain explicit blockers.
        """
        if self.closed:
            raise AccountObservationSourceError("OBSERVATION_SESSION_CLOSED")
        started = self.clock()
        self("/api/v5/account/config", {})
        positions = self._verified_get_v1("/api/v5/account/positions", {})["data"]
        pending = self._verified_get_v1("/api/v5/trade/orders-pending", {})["data"]
        algos = {
            kind: len(self._verified_get_v1(ALGO_PENDING_PATH, {"ordType": kind})["data"])
            for kind in SUPPORTED_ALGO_TYPES
        }
        product_counts = {}
        for row in positions:
            kind = row.get("instType")
            if kind not in {"SWAP", "FUTURES", "MARGIN", "OPTION", "SPOT", "EVENTS"}:
                kind = "UNKNOWN"
            product_counts[kind] = product_counts.get(kind, 0) + 1
        completed = self.clock()
        blockers = []
        if not 0 <= completed - started <= 5:
            blockers.append("ACCOUNT_SCOPE_OBSERVATION_STALE")
        if set(product_counts) - {"SWAP"}:
            blockers.append("ACCOUNT_PRODUCTS_OUTSIDE_CURRENT_SWAP_CONSUMER")
        if pending or any(algos.values()):
            blockers.append("ACCOUNT_PENDING_CUSTODY_PRESENT")
        return {
            "profile": K1_ACCOUNT_READ_PROFILE,
            "configured_account_matched": True,
            "observed_at_unix": started,
            "completed_at_unix": completed,
            "position_product_counts": product_counts,
            "ordinary_pending_count": len(pending),
            "algo_pending_counts": algos,
            "supported_scope_clear": not blockers,
            "blockers": blockers,
            "equity_reconstructed": False,
            "capital_admitted": False,
        }

    def inspect_treasury_inputs_v1(self):
        """Three explicit reads; observe source presence without admitting money.

        Funding balances reuse the existing funding parser. Trading USDC
        selection is an input-readiness check, never the 29P producer itself.
        No fiat/USDT/USD substitution, conversion, transfer or reconstructed EQ.
        """
        if self.closed:
            raise AccountObservationSourceError("OBSERVATION_SESSION_CLOSED")
        from src.ops.offline_funding_balance_read_producer_v1.observation_v1 import (
            parse_funding_account_balance_observation_v1,
        )
        from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.available_margin_observation_v1 import (
            _require_non_negative_decimal as parse_margin_decimal,
            LiveCanaryAvailableMarginObservationError,
        )

        started = self.clock()
        self("/api/v5/account/config", {})
        trading = self._verified_get_v1("/api/v5/account/balance", {})["data"]
        funding = self._verified_get_v1("/api/v5/asset/balances", {})
        funding_observation = parse_funding_account_balance_observation_v1(
            body_bytes=json.dumps(funding).encode(),
            http_status=200,
            observed_at_utc=datetime.fromtimestamp(started, timezone.utc).isoformat(),
            venue="okx",
            rest_host="eea.okx.com",
            endpoint="/api/v5/asset/balances",
            headers={},
            transport_class="FULL_CORE_PRODUCTIVE_READ_ONLY_GET_V1",
            get_performed=True,
        )
        completed = self.clock()
        blockers = []
        usdc_status = "ABSENT_NOT_ZERO"
        target_observed = False

        def numeric(raw, *, nonnegative=False):
            try:
                if nonnegative:
                    return (
                        isinstance(raw, str)
                        and parse_margin_decimal(raw, field="availEq").is_finite()
                    )
                value = Decimal(raw) if isinstance(raw, str) and raw.strip() else Decimal("NaN")
                return value.is_finite() and (not nonnegative or value >= 0)
            except (
                InvalidOperation,
                TypeError,
                ValueError,
                LiveCanaryAvailableMarginObservationError,
            ):
                return False

        if len(trading) != 1 or not isinstance(trading[0].get("details"), list):
            blockers.append("TRADING_BALANCE_SCOPE_UNPROVEN")
        else:
            row = trading[0]
            if row.get("uid") is not None and row["uid"] != self.expected_account_identity:
                raise AccountObservationSourceError("OBSERVATION_ACCOUNT_MISMATCH")
            target_observed = numeric(row.get("totalEq"))
            details = row["details"]
            if any(not isinstance(d, dict) for d in details):
                blockers.append("TRADING_CURRENCY_ROWS_INVALID")
            else:
                rows = [d for d in details if d.get("ccy") == "USDC"]
                if len(rows) > 1:
                    usdc_status = "DUPLICATE_UNPROVEN"
                elif len(rows) == 1:
                    usdc_status = (
                        "OBSERVED_NUMERIC"
                        if numeric(rows[0].get("availEq"), nonnegative=True)
                        else "NUMERIC_UNPROVEN"
                    )
        if usdc_status != "OBSERVED_NUMERIC":
            blockers.append("TRADING_USDC_AVAILABLE_MARGIN_NOT_OBSERVED")
        if not 0 <= completed - started <= 5:
            blockers.append("TREASURY_INPUT_OBSERVATION_STALE")
        return {
            "profile": K1_ACCOUNT_READ_PROFILE,
            "configured_account_matched": True,
            "observed_at_unix": started,
            "completed_at_unix": completed,
            "trading_usdc_avail_eq_status": usdc_status,
            "funding_usdc_row_status": funding_observation.usdc_row_status,
            "funding_observation_class": funding_observation.observation_class,
            "account_equity_target_observed": target_observed,
            "account_equity_is_reconciliation_target_only": True,
            "inputs_ready": not blockers,
            "blockers": blockers,
            "equity_reconstructed": False,
            "capital_admitted": False,
            "currency_substitution_or_transfer": False,
        }

    def _validate_credential_v1(self, credential):
        if (
            not isinstance(credential, FullCoreK1BoundVenueAuthHandleV1)
            or credential.bound is not True
            or credential.can_sign is not True
            or credential.material_loaded is not False
        ):
            raise AccountObservationSourceError("K1_ACCOUNT_READ_HANDLE_INVALID")


@contextmanager
def open_k1_account_observation_source_v1(
    *,
    expected_account_identity,
    session_id,
    max_request_count,
    k1_lookup_backend=None,
    clock=time.time,
):
    """Explicit K1 source selection, bounded by its existing acquisition gates.

    Expected account is independently configured, never inferred from a GET.
    This API does not consume the dedicated observer policy/SecretRef. Opening
    it with the real backend is a real credential operation, not a dry run.
    """
    if (
        not isinstance(expected_account_identity, str)
        or not expected_account_identity
        or expected_account_identity != expected_account_identity.strip()
    ):
        raise AccountObservationSourceError("OBSERVATION_EXPECTED_ACCOUNT_REQUIRED")
    if not isinstance(session_id, str) or not session_id.strip():
        raise AccountObservationSourceError("OBSERVATION_SESSION_REQUIRED")
    if (
        isinstance(max_request_count, bool)
        or not isinstance(max_request_count, int)
        or max_request_count < 10
    ):
        raise AccountObservationSourceError("K1_ACCOUNT_BASELINE_QUOTA_REQUIRED")
    with open_governed_live_c1_get_only_fresh_pretrade_transport_v1(
        max_request_count=max_request_count, k1_lookup_backend=k1_lookup_backend
    ) as (transport, _proof):
        source = K1AccountObservationSourceV1(
            credential=transport._handle,
            transport=transport,
            expected_account_identity=expected_account_identity,
            session_id=session_id,
            clock=clock,
        )
        try:
            yield source
        finally:
            source.close()
            transport.payloads_by_path.clear()
            transport._cache.clear()
            transport.raw_response_sink_v1 = None
            transport._handle = None
