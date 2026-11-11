"""Explicit K1 account-read profile; never relabel K1 as a dedicated read key.

Uses the existing K1 OS-store/signing session and productive GET transport.
No fallback from the dedicated observer credential contract and no POST port.
"""

from contextlib import contextmanager
from dataclasses import dataclass, field
from pathlib import Path
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from fractions import Fraction
import json
import math
import re
from urllib.parse import parse_qsl, urlencode, urlsplit
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
    POSITION_OBSERVATION_FRESHNESS_MAX_AGE_MS,
)
from src.ops.okx_eea_private_account_state_runtime_v1.startup_source_v1 import (
    ALGO_PENDING_PATH,
    SUPPORTED_ALGO_TYPES,
    AccountObservationSourceError,
    AccountObservationSourceV1,
)

K1_ACCOUNT_READ_PROFILE = "K1_ACCOUNT_OBSERVATION_GET_ONLY_V1"
FUTURES_INVENTORY_ALGO_TYPES = SUPPORTED_ALGO_TYPES + ("chase", "iceberg", "twap", "smart_iceberg")
FUTURES_INVENTORY_BOT_QUERIES = (
    ("/api/v5/tradingBot/grid/orders-algo-pending", {"algoOrdType": "grid"}),
    ("/api/v5/tradingBot/grid/orders-algo-pending", {"algoOrdType": "contract_grid"}),
    ("/api/v5/tradingBot/dca/ongoing-list", {"algoOrdType": "spot_dca"}),
    ("/api/v5/tradingBot/dca/ongoing-list", {"algoOrdType": "contract_dca"}),
    ("/api/v5/tradingBot/signal/orders-algo-pending", {"algoOrdType": "contract"}),
    ("/api/v5/tradingBot/recurring/orders-algo-pending", {}),
)
FUTURES_INVENTORY_REQUEST_COUNT = (
    6 + len(FUTURES_INVENTORY_ALGO_TYPES) + len(FUTURES_INVENTORY_BOT_QUERIES)
)
_SIGNED_FIXED_DECIMAL = re.compile(r"-?[0-9]+(?:\.[0-9]+)?")


@dataclass(frozen=True)
class FuturesFinancialVenueInputsV1:
    gets: dict = field(repr=False)
    current_cross_balance_with_pnl_usdc: Fraction | None = field(repr=False)


def _cross_balance_with_pnl_v1(usdc):
    """Invert the documented floor only when the observed free margin is positive."""
    amounts = (usdc.get("availEq"), usdc.get("frozenBal"))
    if any(
        not isinstance(value, str) or len(value) > 128 or not _SIGNED_FIXED_DECIMAL.fullmatch(value)
        for value in amounts
    ):
        return None
    free, in_use = map(Fraction, amounts)
    # OKX Futures cross: availEq = max(0, cross balance + cross PnL - frozenBal).
    if free <= 0 or in_use < 0:
        return None
    return free + in_use


def _validate_inventory_scope_v1(guard, inst_type):
    if type(guard) is not bool:
        raise AccountObservationSourceError("K1_ACCOUNT_INVENTORY_GUARD_INVALID")
    if (
        type(inst_type) is not str
        or inst_type not in ("SWAP", "FUTURES")
        or (inst_type == "FUTURES" and not guard)
    ):
        raise AccountObservationSourceError("K1_ACCOUNT_INVENTORY_PRODUCT_INVALID")


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
    def __init__(self, transport, *, inventory_inst_type):
        self._transport = transport
        self._inventory_inst_type = inventory_inst_type
        self._algo_types = (
            FUTURES_INVENTORY_ALGO_TYPES
            if inventory_inst_type == "FUTURES"
            else SUPPORTED_ALGO_TYPES
        )
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
            if params.get("ordType") not in self._algo_types:
                raise AccountObservationSourceError("K1_ALGO_TYPE_UNSUPPORTED")
            expected = {"instType": "SWAP", "ordType": params["ordType"]}
        elif (
            self._inventory_inst_type == "FUTURES"
            and (path, params) in FUTURES_INVENTORY_BOT_QUERIES
        ):
            expected = params
        elif path in {
            "/api/v5/account/bills-archive",
            "/api/v5/account/bills",
            "/api/v5/asset/bills-history",
        }:
            expected = params
        elif path == "/api/v5/account/subtypes":
            expected = {}
        elif path in {"/api/v5/trade/orders-history", "/api/v5/trade/fills"}:
            expected = {"instType": self._inventory_inst_type}
        elif path not in BASELINE_REST_RECOVERY_ALLOWLIST and path != "/api/v5/asset/balances":
            raise AccountObservationSourceError("K1_ACCOUNT_READ_ENDPOINT_FORBIDDEN")
        # Fixed scope-inspection reads may omit instType to expose products
        # outside the SWAP consumer contract. They cannot hide those products.
        full_scope = (
            path in {"/api/v5/account/positions", "/api/v5/trade/orders-pending"} and params == {}
        ) or (
            path == ALGO_PENDING_PATH
            and params == {"ordType": params.get("ordType")}
            and params.get("ordType") in self._algo_types
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

    def _assert_current_resource_pair_v1(self):
        super()._assert_current_resource_pair_v1()
        if (
            not isinstance(self.transport, _AccountReadTransportV1)
            or self.transport._transport._handle is not self.credential
        ):
            raise AccountObservationSourceError("K1_ACCOUNT_READ_HANDLE_BINDING_REQUIRED")

    def __init__(
        self,
        *,
        credential,
        transport,
        account_inventory_guard=False,
        inventory_inst_type="SWAP",
        **kwargs,
    ):
        _validate_inventory_scope_v1(account_inventory_guard, inventory_inst_type)
        if (
            not isinstance(transport, FullCoreProductiveReadOnlyGetTransportV1)
            or transport._handle is not credential
        ):
            raise AccountObservationSourceError("K1_ACCOUNT_READ_HANDLE_BINDING_REQUIRED")
        super().__init__(
            credential=credential,
            transport=_AccountReadTransportV1(transport, inventory_inst_type=inventory_inst_type),
            **kwargs,
        )
        self.account_inventory_guard = account_inventory_guard
        self.inventory_inst_type = inventory_inst_type

    def _pending_algo_types_v1(self):
        return (
            FUTURES_INVENTORY_ALGO_TYPES
            if self.inventory_inst_type == "FUTURES"
            else SUPPORTED_ALGO_TYPES
        )

    def _verified_get_v1(self, path, params):
        if not self.account_inventory_guard or params.get("instType") != "SWAP":
            return super()._verified_get_v1(path, params)
        # Position and pending custody is account-wide. History and fills
        # are bounded to the one product selected for this observer.
        query = dict(params)
        if path in {"/api/v5/account/positions", "/api/v5/trade/orders-pending", ALGO_PENDING_PATH}:
            query.pop("instType")
        else:
            query["instType"] = self.inventory_inst_type
        self._assert_current_resource_pair_v1()
        payload = super()._verified_get_v1(path, query)
        self._assert_current_resource_pair_v1()
        if path == "/api/v5/account/positions" and any(
            row.get("instType") != self.inventory_inst_type for row in payload["data"]
        ):
            raise AccountObservationSourceError(
                f"ACCOUNT_PRODUCTS_OUTSIDE_CURRENT_{self.inventory_inst_type}_CONSUMER"
            )
        if (
            path == "/api/v5/trade/orders-pending"
            and self.inventory_inst_type == "FUTURES"
            and not payload["data"]
        ):
            for bot_path, bot_query in FUTURES_INVENTORY_BOT_QUERIES:
                bot = super()._verified_get_v1(bot_path, bot_query)
                self._assert_current_resource_pair_v1()
                if bot["data"]:
                    raise AccountObservationSourceError("K1_FUTURES_ACCOUNT_BOT_CUSTODY_PRESENT")
        return payload

    def export_startup_document_v1(self, path, *, instrument_ids_by_native_id):
        if self.inventory_inst_type == "FUTURES":
            raise AccountObservationSourceError("K1_FUTURES_LEGACY_STARTUP_DOCUMENT_UNSUPPORTED")
        return super().export_startup_document_v1(
            path, instrument_ids_by_native_id=instrument_ids_by_native_id
        )

    def inspect_futures_financial_gets_v1(self, observation, *, read_count):
        """Read the completed original FUTURES inventory for financial observation."""
        if (
            self.closed
            or not self.account_inventory_guard
            or self.inventory_inst_type != "FUTURES"
            or self.transport.read_count != read_count
            or observation.account_inventory_source is not self
            or observation.account != self.expected_account_identity
            or observation.pending_orders
        ):
            raise AccountObservationSourceError("FUTURES_FINANCIAL_INVENTORY_SCOPE_CHANGED")
        self._assert_current_resource_pair_v1()
        self._validate_credential_v1(self.credential)
        snapshot = observation.observed
        started, completed = snapshot.event_time_unix, snapshot.wall_time_unix
        max_age = POSITION_OBSERVATION_FRESHNESS_MAX_AGE_MS / 1000
        now = self.clock()
        if (
            snapshot.source_id != "host-private-rest-futures"
            or snapshot.max_age_seconds != max_age
            or not all(math.isfinite(t) for t in (started, completed, now))
            or not 0 <= now - completed <= now - started <= max_age
        ):
            raise AccountObservationSourceError("FUTURES_FINANCIAL_INVENTORY_WINDOW_INVALID")
        config_path = "/api/v5/account/config"
        balance_path = "/api/v5/account/balance"
        positions_path = "/api/v5/account/positions"
        pending_path = "/api/v5/trade/orders-pending"
        empty_paths = [
            pending_path,
            *(
                f"{ALGO_PENDING_PATH}?{urlencode({'ordType': kind})}"
                for kind in self._pending_algo_types_v1()
            ),
            *(
                path + ("?" + urlencode(query) if query else "")
                for path, query in FUTURES_INVENTORY_BOT_QUERIES
            ),
        ]
        gets = {}
        for endpoint in (config_path, balance_path, positions_path, *empty_paths):
            record = self._observation_gets.get(endpoint)
            if record is None or record["pretrade_decision_id"] != self.session_id:
                raise AccountObservationSourceError("FUTURES_FINANCIAL_INVENTORY_GET_REQUIRED")
            acquired = datetime.fromisoformat(record["acquired_at_utc"].replace("Z", "+00:00"))
            if acquired.tzinfo is None or not started <= acquired.timestamp() <= completed:
                raise AccountObservationSourceError("FUTURES_FINANCIAL_INVENTORY_GET_TIME_INVALID")
            if endpoint in empty_paths and record["payload"]["data"] != []:
                raise AccountObservationSourceError("FUTURES_FINANCIAL_PENDING_CUSTODY_PRESENT")
            gets[endpoint] = record
        for endpoint, key in (
            (config_path, "CONFIG"),
            (positions_path, "POSITIONS"),
            (pending_path, "PENDING"),
        ):
            if gets[endpoint]["payload"] != observation.occupancy_payloads.get(key):
                raise AccountObservationSourceError("FUTURES_FINANCIAL_HOST_EVIDENCE_MISMATCH")
        config = gets[config_path]["payload"]["data"]
        if (
            len(config) != 1
            or config[0].get("uid") != observation.account
            or config[0].get("acctLv") != "2"
            or config[0].get("posMode") != "net_mode"
            or config[0].get("settleCcy") != "USDC"
        ):
            raise AccountObservationSourceError("FUTURES_FINANCIAL_USDC_NET_ACCOUNT_REQUIRED")
        balance = gets[balance_path]["payload"]["data"]
        details = balance[0].get("details") if len(balance) == 1 else None
        if (
            not isinstance(details, list)
            or balance[0].get("uid", observation.account) != observation.account
            or any(not isinstance(row, dict) for row in details)
        ):
            raise AccountObservationSourceError("FUTURES_FINANCIAL_USDC_BALANCE_SCOPE_UNPROVEN")
        usdc = [row for row in details if row.get("ccy") == "USDC"]
        if len(usdc) != 1:
            raise AccountObservationSourceError("FUTURES_FINANCIAL_USDC_BALANCE_SCOPE_UNPROVEN")
        if self.transport.read_count != read_count:
            raise AccountObservationSourceError("FUTURES_FINANCIAL_INVENTORY_SCOPE_CHANGED")
        return FuturesFinancialVenueInputsV1(
            gets=json.loads(json.dumps(gets, allow_nan=False)),
            current_cross_balance_with_pnl_usdc=_cross_balance_with_pnl_v1(usdc[0]),
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
            for kind in self._pending_algo_types_v1()
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

    def inspect_futures_margin_state_v1(self):
        """Report current USDC cross-margin evidence from the original signed GETs."""
        if self.closed:
            raise AccountObservationSourceError("OBSERVATION_SESSION_CLOSED")
        started = self.clock()
        config = self("/api/v5/account/config", {})["data"][0]
        self._assert_current_resource_pair_v1()
        blockers = []
        balance_row_present = None
        cross_position_present = None
        maintenance_fields_observed = False
        if (config.get("acctLv"), config.get("posMode"), config.get("settleCcy")) != (
            "2",
            "net_mode",
            "USDC",
        ):
            blockers.append("FUTURES_MARGIN_STATE_ACCOUNT_SCOPE_UNSUPPORTED")
        else:
            positions = self._verified_get_v1("/api/v5/account/positions", {})["data"]
            self._assert_current_resource_pair_v1()
            balances = self._verified_get_v1("/api/v5/account/balance", {})["data"]
            self._assert_current_resource_pair_v1()
            cross_position_present = False
            for row in positions:
                size = row.get("pos")
                mode = row.get("mgnMode")
                currency = row.get("ccy")
                if (
                    not isinstance(size, str)
                    or not _SIGNED_FIXED_DECIMAL.fullmatch(size)
                    or mode not in ("cross", "isolated")
                    or (
                        mode == "cross"
                        and (
                            not isinstance(currency, str)
                            or not re.fullmatch(r"[A-Z0-9]+", currency)
                        )
                    )
                ):
                    blockers.append("FUTURES_MARGIN_STATE_POSITION_SCOPE_UNPROVEN")
                    cross_position_present = None
                    break
                if mode == "cross" and currency == "USDC" and Decimal(size) != 0:
                    cross_position_present = True

            if len(balances) == 1 and balances[0].get("uid", self.expected_account_identity) != (
                self.expected_account_identity
            ):
                raise AccountObservationSourceError("OBSERVATION_ACCOUNT_MISMATCH")
            details = balances[0].get("details") if len(balances) == 1 else None
            if not isinstance(details, list) or any(
                not isinstance(row, dict)
                or not isinstance(row.get("ccy"), str)
                or not re.fullmatch(r"[A-Z0-9]+", row["ccy"])
                for row in details
            ):
                blockers.append("FUTURES_MARGIN_STATE_BALANCE_SCOPE_UNPROVEN")
            else:
                usdc = [row for row in details if row.get("ccy") == "USDC"]
                if len(usdc) > 1:
                    blockers.append("FUTURES_MARGIN_STATE_USDC_BALANCE_AMBIGUOUS")
                else:
                    balance_row_present = bool(usdc)
                    if cross_position_present:
                        maintenance_fields_observed = bool(usdc) and all(
                            isinstance(value, str)
                            and _SIGNED_FIXED_DECIMAL.fullmatch(value)
                            and Decimal(value) >= 0
                            for value in (usdc[0].get("mmr"), usdc[0].get("mgnRatio"))
                        )
                        if not maintenance_fields_observed:
                            blockers.append("FUTURES_MARGIN_STATE_USDC_MAINTENANCE_UNPROVEN")
        completed = self.clock()
        if not 0 <= completed - started <= 5:
            blockers.append("FUTURES_MARGIN_STATE_OBSERVATION_STALE")
        return {
            "profile": K1_ACCOUNT_READ_PROFILE,
            "configured_account_matched": True,
            "observed_at_unix": started,
            "completed_at_unix": completed,
            "usdc_balance_row_present": balance_row_present,
            "usdc_cross_position_observed": cross_position_present,
            "usdc_maintenance_fields_observed": maintenance_fields_observed,
            "observation_complete": not blockers,
            "blockers": blockers,
            "projected_entry_risk_proven": False,
            "liquidation_cover_proven": False,
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
    account_inventory_guard=False,
    inventory_inst_type="SWAP",
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
    _validate_inventory_scope_v1(account_inventory_guard, inventory_inst_type)
    minimum_requests = (
        FUTURES_INVENTORY_REQUEST_COUNT
        if inventory_inst_type == "FUTURES"
        else 6 + len(SUPPORTED_ALGO_TYPES)
    )
    if (
        isinstance(max_request_count, bool)
        or not isinstance(max_request_count, int)
        or max_request_count < minimum_requests
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
            account_inventory_guard=account_inventory_guard,
            inventory_inst_type=inventory_inst_type,
        )
        try:
            yield source
        finally:
            source.close()
            transport.payloads_by_path.clear()
            transport._cache.clear()
            transport.raw_response_sink_v1 = None
            transport._handle = None
