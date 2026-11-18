"""GET-only BTC Demo coverage and confirmed first-fill handoff to the V2 Exit owner."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
import json
import os
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import HTTPRedirectHandler, ProxyHandler, Request, build_opener

from src.ops.exit_policy_producer_binding_v1.authenticated_execution_entry_source_v1 import (
    confirmed_venue_entry_anchors_v1,
)
from src.ops.exit_policy_producer_binding_v1.models_v1 import canonical_digest_v1
from src.ops.exit_policy_producer_binding_v1.position_episode_binding_v1 import (
    IDENTITY_FILENAME,
    PositionEpisodeIdentityV1,
    PositionEpisodeScopeV1,
    open_position_episode_binding_v1,
)
from src.ops.full_core_live_path_composition_root_v1.final_order_envelope_v1 import (
    FinalOrderEnvelopeV1,
    assert_envelope_unmodified_v1,
)
from src.ops.full_core_live_path_composition_root_v1.full_core_exchange_reconciliation_v1 import (
    EvidenceLayer,
    ExchangeEvidenceItemV1,
    FullCoreExchangeReconciliationSnapshotV1,
    LocalSubmitOutcome,
    OUTCOME_CONFIRMED_FILLED,
    OUTCOME_CONFIRMED_PARTIALLY_FILLED,
    PortfolioExecutionReconciliationIdentityV2,
    adjudicate_full_core_exchange_reconciliation_v1,
    parse_exchange_reconciliation_identity_v1,
)
from src.ops.full_core_live_path_composition_root_v1.natural_enter_cross_session_outcome_closure_v1.retention_v1 import (
    exclusive_v1,
    immutable_json_v1,
)
from src.ops.offline_first_entry_position_v2 import publish_confirmed_first_entry_c1_v2
from src.ops.portfolio_capital_reservation_budget_v1.durable_store_v1 import (
    read_budget_revision_read_only_v1,
    require_budget_head_read_only_v1,
)
from src.ops.section_11_12_8_okx_eea_demo_xperp_venue_host_account_instrument_binding_v1.binding_contract_v1 import (
    canonical_binding_headers_v1,
    evaluate_okx_eea_demo_xperp_binding_v1,
)

_LANE = "LANE_3"
_BUDGET_USDC = Decimal("25")
_HEADERS = canonical_binding_headers_v1()
_DEMO = evaluate_okx_eea_demo_xperp_binding_v1(headers=_HEADERS)
_NATIVE = _DEMO.instrument_scope_exact
_FAMILY = _NATIVE.rsplit("-", 1)[0]
_CONFIG = "/api/v5/account/config"
_BALANCE = "/api/v5/account/balance"
_INSTRUMENTS = "/api/v5/account/instruments"
_FEE = "/api/v5/account/trade-fee"
_POSITIONS = "/api/v5/account/positions"
_ORDER = "/api/v5/trade/order"
_PENDING = "/api/v5/trade/orders-pending"
_FILLS = "/api/v5/trade/fills"
_FX = "/api/v5/market/index-tickers"
_PRIVATE_READS = {_CONFIG, _BALANCE, _INSTRUMENTS, _FEE, _POSITIONS, _ORDER, _PENDING, _FILLS}
_AUTH_FIELDS = {"OK-ACCESS-KEY", "OK-ACCESS-SIGN", "OK-ACCESS-TIMESTAMP", "OK-ACCESS-PASSPHRASE"}


class _RejectRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


class OkxEeaDemoReadsV1:
    """Use an explicitly supplied Demo SecretRef signer for bounded GETs."""

    def __init__(self, *, secret_reference, sign_get):
        if secret_reference != _DEMO.secret_reference or not callable(sign_get):
            raise ValueError("BTC_DEMO_SIGNER_SOURCE_REQUIRED")
        self._sign_get = sign_get
        self._opener = build_opener(ProxyHandler({}), _RejectRedirect())

    def read(self, path, **query):
        if path not in _PRIVATE_READS and (path, query) != (_FX, {"instId": "USDC-USD"}):
            raise ValueError("BTC_DEMO_GET_PATH_FORBIDDEN")
        endpoint = path + (f"?{urlencode(query)}" if query else "")
        headers = {
            "Accept": "application/json",
            "User-Agent": "PeakTrade-OKX-EEA-Demo-ReadOnly/1",
            **_HEADERS,
        }
        if path in _PRIVATE_READS:
            signed = self._sign_get(endpoint)
            if set(signed) != _AUTH_FIELDS or not all(signed.values()):
                raise ValueError("BTC_DEMO_SIGNED_HEADERS_REQUIRED")
            headers.update(signed)
        request = Request(_DEMO.rest_base + endpoint, headers=headers, method="GET")
        with self._opener.open(request, timeout=8) as response:  # noqa: S310
            if response.status != 200 or response.url != request.full_url:
                raise ValueError("BTC_DEMO_GET_RESPONSE_UNPROVEN")
            payload = json.load(response)
        acquired_at = datetime.now(timezone.utc)
        if (
            not isinstance(payload, dict)
            or payload.get("code") != "0"
            or not isinstance(payload.get("data"), list)
            or any(not isinstance(row, dict) for row in payload["data"])
        ):
            raise ValueError("BTC_DEMO_GET_RESPONSE_UNPROVEN")
        return payload, acquired_at


def _only(payload):
    if len(payload["data"]) != 1:
        raise ValueError("BTC_DEMO_SINGLE_ROW_REQUIRED")
    return payload["data"][0]


def _money(value):
    try:
        amount = Decimal(value) if isinstance(value, str) else Decimal("NaN")
    except InvalidOperation as exc:
        raise ValueError("BTC_DEMO_AMOUNT_INVALID") from exc
    if not amount.is_finite():
        raise ValueError("BTC_DEMO_AMOUNT_INVALID")
    return amount


def _account(reads, expected_uid):
    if (
        not isinstance(expected_uid, str)
        or not expected_uid.isascii()
        or not expected_uid.isdecimal()
    ):
        raise ValueError("BTC_DEMO_ACTUAL_ACCOUNT_ID_REQUIRED")
    config, acquired_at = reads.read(_CONFIG)
    row = _only(config)
    if row.get("uid") != expected_uid:
        raise ValueError("BTC_DEMO_ACCOUNT_MISMATCH")
    return row, acquired_at


def read_btc_demo_coverage_v2(*, reads: OkxEeaDemoReadsV1, expected_uid: str) -> dict:
    """Measure Demo availability and FX without taking a hold or funding a slot."""
    account, _ = _account(reads, expected_uid)
    balance, _ = reads.read(_BALANCE, ccy="USD,USDC")
    instruments, _ = reads.read(_INSTRUMENTS, instType="FUTURES", instId=_NATIVE)
    instrument = _only(instruments)
    if instrument.get("instId") != _NATIVE or instrument.get("state") != "live":
        raise ValueError("BTC_DEMO_ACCOUNT_INSTRUMENT_UNAVAILABLE")
    fees, _ = reads.read(_FEE, instType="FUTURES", instFamily=_FAMILY)
    fee_rows = [
        row
        for row in _only(fees).get("feeGroup", [])
        if row.get("groupId") == instrument.get("groupId")
    ]
    if len(fee_rows) != 1 or _only(fees).get("instType") != "FUTURES":
        raise ValueError("BTC_DEMO_ACCOUNT_FEE_GROUP_UNPROVEN")
    fx, acquired_at = reads.read(_FX, instId="USDC-USD")
    fx_row = _only(fx)
    rate = _money(fx_row.get("idxPx"))
    age = acquired_at.timestamp() - int(fx_row["ts"]) / 1000
    if fx_row.get("instId") != "USDC-USD" or rate <= 0 or not 0 <= age <= 10:
        raise ValueError("BTC_DEMO_USDC_USD_INDEX_UNPROVEN")
    details = _only(balance).get("details")
    if not isinstance(details, list) or any(not isinstance(row, dict) for row in details):
        raise ValueError("BTC_DEMO_AVAILABLE_EQUITY_UNPROVEN")
    amounts = {}
    for row in details:
        ccy = row.get("ccy")
        if ccy not in {"USDC", "USD"}:
            continue
        if ccy in amounts:
            raise ValueError("BTC_DEMO_AVAILABLE_EQUITY_AMBIGUOUS")
        amounts[ccy] = _money(row["availEq"]) if row.get("availEq") not in ("", None) else None
    available_usdc = amounts.get("USDC")
    return {
        "budget_usdc": str(_BUDGET_USDC),
        "budget_value_usd": str(_BUDGET_USDC * rate),
        "venue_settlement_currency": instrument["settleCcy"],
        "available_equity": {
            ccy: None if amount is None else str(amount) for ccy, amount in amounts.items()
        },
        "available_usdc_covers_declared_budget": None
        if available_usdc is None
        else available_usdc >= _BUDGET_USDC,
        "position_mode": account["posMode"],
        "taker_fee_rate_signed": str(_money(fee_rows[0].get("taker"))),
        "fx_captured_at": acquired_at.isoformat(),
    }


@dataclass(frozen=True)
class _FirstFill:
    price: Decimal
    time_ms: int
    anchors_digest: str
    order_id: str
    filled_quantity: str
    fee_rows: tuple[tuple[str, str, str], ...]
    confirmed_at_utc: str


def _confirmed_first_fill(reads, identity) -> _FirstFill:
    account, account_at = _account(reads, identity.account_identity)
    if account.get("posMode") != "net_mode":
        raise ValueError("BTC_DEMO_NET_POSITION_MODE_REQUIRED")
    pending, _ = reads.read(_PENDING, instType="FUTURES", instId=_NATIVE)
    order, _ = reads.read(_ORDER, instId=_NATIVE, clOrdId=identity.clordid)
    order_row = _only(order)
    if (
        order_row.get("instId") != _NATIVE
        or order_row.get("clOrdId") != identity.clordid
        or order_row.get("posSide") != "net"
        or str(order_row.get("reduceOnly")).lower() != "false"
        or order_row.get("side") != {"LONG": "buy", "SHORT": "sell"}[identity.selected_side]
    ):
        raise ValueError("BTC_DEMO_ORDER_SCOPE_MISMATCH")
    order_id = order_row["ordId"]
    if not isinstance(order_id, str) or not order_id.isascii() or not order_id.isdecimal():
        raise ValueError("BTC_DEMO_VENUE_ORDER_ID_REQUIRED")
    fills, _ = reads.read(_FILLS, instType="FUTURES", instId=_NATIVE, ordId=order_id, limit="100")
    positions, position_at = reads.read(_POSITIONS, instId=_NATIVE)
    if not 0 <= (position_at - account_at).total_seconds() <= 15:
        raise ValueError("BTC_DEMO_FILL_READ_WINDOW_EXPIRED")
    items = tuple(
        ExchangeEvidenceItemV1(
            layer=layer,
            source="OKX_EEA_DEMO_PRIVATE_GET",
            account=identity.account_identity,
            environment=identity.execution_environment,
            instrument=identity.instrument_id,
            observed_at=account_at.isoformat(),
            received_at=position_at.isoformat(),
            freshness_proven=True,
            query_scope="exact_demo_order",
            response_status="200",
            raw_reference="OKX_EEA_DEMO_PRIVATE_GET:" + canonical_digest_v1(row),
            canonical_identity_digest=identity.identity_digest(),
            payload=row,
        )
        for layer, rows in (
            (EvidenceLayer.EXCHANGE_ORDER_STATE, [order_row]),
            (EvidenceLayer.EXCHANGE_FILL_STATE, fills["data"]),
        )
        for row in rows
    )
    snapshot = FullCoreExchangeReconciliationSnapshotV1(
        provider="OKX_EEA_DEMO_PRIVATE_GET",
        simulation_mode="TESTNET",
        identity_digest=identity.identity_digest(),
        evidence_items=items,
        incomplete_pagination=len(fills["data"]) >= 100,
        history_unavailable=False,
        snapshot_freshness_proven=True,
        transport_failures=(),
        api_errors=(),
        pending_orders_observation={"freshness_proven": True, "response": pending},
        positions_observation={"freshness_proven": True, "response": positions},
    )
    decision = adjudicate_full_core_exchange_reconciliation_v1(
        identity=identity,
        snapshot=snapshot,
        local_submit_outcome=LocalSubmitOutcome.TRANSPORT_UNKNOWN,
    )
    if (
        decision.outcome not in {OUTCOME_CONFIRMED_FILLED, OUTCOME_CONFIRMED_PARTIALLY_FILLED}
        or not decision.reconciliation_complete
        or not decision.exposure_retained
        or decision.venue_ord_id != order_id
        or order_row.get("state") not in {"filled", "canceled"}
    ):
        raise ValueError("BTC_DEMO_TERMINAL_FILL_UNPROVEN")
    price, time_ms, anchors = confirmed_venue_entry_anchors_v1(
        identity,
        snapshot,
        side=identity.selected_side.lower(),
        order_id=order_id,
        filled_quantity=decision.cumulative_filled_qty,
        positions_acquired_at=position_at,
    )
    fees = {}
    for row in fills["data"]:
        trade_id, currency = row["tradeId"], row.get("feeCcy")
        if currency not in {"USD", "USDC"}:
            raise ValueError("BTC_DEMO_FILL_FEE_CURRENCY_UNPROVEN")
        fee = (trade_id, currency, str(_money(row.get("fee")).normalize()))
        if fees.setdefault(trade_id, fee) != fee:
            raise ValueError("BTC_DEMO_CONFLICTING_FILL_FEES")
    return _FirstFill(
        price,
        time_ms,
        anchors,
        order_id,
        decision.cumulative_filled_qty,
        tuple(sorted(fees.values())),
        position_at.astimezone(timezone.utc).isoformat().replace("+00:00", "Z"),
    )


def _demo_lane_root(testnet_root):
    root = Path(testnet_root)
    if not root.is_absolute() or root.resolve() != root:
        raise ValueError("BTC_DEMO_ISOLATED_ROOT_REQUIRED")
    profile = json.loads((root / "btc-lane3-testnet.json").read_bytes())
    lane_root = root / "testnet-state" / _LANE
    if (
        root.stat().st_uid != os.getuid()
        or root.stat().st_mode & 0o077
        or lane_root.resolve() != lane_root
        or profile["lane"] != _LANE
        or profile["instrument"] != _NATIVE
        or profile["environment"] != _DEMO.runtime_mode
        or profile["roots"]["lane"] != str(lane_root)
    ):
        raise ValueError("BTC_DEMO_ISOLATED_ROOT_REQUIRED")
    return lane_root


def _read_original_attempt(lane_root, expected_uid, reservation_id, revision_ref):
    budget_root = lane_root.parent / "budget-owner" / "owner"
    revision = read_budget_revision_read_only_v1(
        budget_root,
        account_identity=expected_uid,
        sequence=revision_ref[0],
        expected_digest=revision_ref[1],
    )
    state = revision["state"]
    link = state["execution_links"][reservation_id]
    identity = parse_exchange_reconciliation_identity_v1(link["identity"])
    bound = state["lane_bindings"][_LANE]["bound"]
    envelope = FinalOrderEnvelopeV1(**link["envelope"])
    created = datetime.fromisoformat(envelope.creation_epoch)
    if (
        not isinstance(identity, PortfolioExecutionReconciliationIdentityV2)
        or link["phase"] != "SUBMIT_MAY_HAVE_OCCURRED"
        or identity.portfolio_reservation_id != reservation_id
        or identity.budget_owner_root != str(budget_root)
        or identity.account_identity != expected_uid
        or (identity.execution_environment, identity.venue, identity.slot_id, identity.native_id)
        != (_DEMO.runtime_mode, _DEMO.venue, _LANE, _NATIVE)
        or (identity.instrument_id, identity.native_id)
        != (bound["instrument_id"], bound["venue_native_id"])
        or identity.selected_side not in {"LONG", "SHORT"}
        or identity.decision_outcome != "ENTER_" + identity.selected_side
        or envelope.client_order_id != identity.clordid
        or created.utcoffset() is None
    ):
        raise ValueError("BTC_DEMO_ORIGINAL_V2_ENTRY_ATTEMPT_REQUIRED")
    assert_envelope_unmodified_v1(
        envelope, expected_id=identity.envelope_identity, expected_digest=identity.envelope_digest
    )
    return identity, created, budget_root


def _episode_identity(identity):
    return PositionEpisodeIdentityV1(
        _LANE,
        identity.instrument_id,
        _NATIVE,
        identity.identity_digest(),
        identity.selected_side.lower(),
        PositionEpisodeScopeV1(identity.account_identity, _DEMO.runtime_mode),
    )


def _read_owner_json(root: Path, relative: Path):
    path = root / relative
    if path.resolve() != path:
        raise ValueError("BTC_DEMO_RESEARCH_SOURCE_SYMLINK_FORBIDDEN")
    return json.loads(path.read_bytes())


def read_btc_demo_first_fill_for_research_v1(testnet_root: Path, episode_id: str) -> dict:
    """Read a published V2 Demo observation and check the original owner bindings offline."""
    if len(episode_id) != 64 or any(char not in "0123456789abcdef" for char in episode_id):
        raise ValueError("BTC_DEMO_RESEARCH_EPISODE_ID_INVALID")
    lane_root = _demo_lane_root(testnet_root)
    receipt = _read_owner_json(lane_root, Path("research-first-fills") / f"{episode_id}.json")
    body = receipt["body"]
    if (
        body["schema"] != "btc_demo_v2_confirmed_entry_research.v1"
        or body["episode_id"] != episode_id
        or canonical_digest_v1(body) != receipt["digest"]
    ):
        raise ValueError("BTC_DEMO_RESEARCH_RECEIPT_MISMATCH")
    identity, created, _ = _read_original_attempt(
        lane_root, body["account_identity"], body["reservation_id"], body["budget_revision"]
    )
    evidence = _read_owner_json(lane_root, Path("confirmed-first-fills") / f"{episode_id}.json")
    episode = _read_owner_json(
        lane_root, Path("position-episodes") / episode_id / IDENTITY_FILENAME
    )
    entry_digest = episode.pop("content_digest")
    if (
        identity.identity_digest() != episode_id
        or evidence["attempt"] != episode_id
        or evidence["lane"] != _LANE
        or evidence["venue_native_id"] != _NATIVE
        or canonical_digest_v1(evidence) != body["opening_digest"]
        or _money(evidence["filled_quantity"]) <= 0
        or evidence["first_fill_time_ms"] / 1000 < created.timestamp()
        or evidence["first_fill_time_ms"] / 1000
        > datetime.fromisoformat(body["confirmed_at_utc"].replace("Z", "+00:00")).timestamp()
        or episode["identity"] != asdict(_episode_identity(identity))
        or episode["entry_source_ref"] != "okx_eea_demo_first_fill.v2:" + body["opening_digest"]
        or entry_digest != canonical_digest_v1(episode)
    ):
        raise ValueError("BTC_DEMO_RESEARCH_ORIGINAL_ENTRY_MISMATCH")
    return {
        "authority": "NONE",
        "execution_environment": _DEMO.runtime_mode,
        "venue": _DEMO.venue,
        "lane_id": _LANE,
        "session_id": body["session_id"],
        "episode_id": episode_id,
        "instrument_id": identity.instrument_id,
        "venue_native_id": identity.native_id,
        "decision_id": identity.canonical_decision_id,
        "decision_outcome": identity.decision_outcome,
        "cycle_id": identity.cycle_id,
        "envelope_created_utc": created.astimezone(timezone.utc).isoformat().replace("+00:00", "Z"),
        "confirmed_at_utc": body["confirmed_at_utc"],
        "repository_sha": body["repository_sha"],
        "config_digest": body["config_digest"],
        "source_digest": receipt["digest"],
        "opening_fill": evidence,
    }


def bind_btc_demo_first_fill_to_v2(
    *,
    reads: OkxEeaDemoReadsV1,
    testnet_root: Path,
    expected_uid: str,
    reservation_id: str,
    revision_ref: tuple[int, str],
    repository_sha: str,
    config_digest: str,
    writer_session_id: str,
    g17_producer,
):
    """Open/recover V2 from an original TESTNET submit attempt and exact venue readback."""
    lane_root = _demo_lane_root(testnet_root)
    cursor_root = lane_root / "cursor"
    if cursor_root.resolve() != cursor_root:
        raise ValueError("BTC_DEMO_ISOLATED_ROOT_REQUIRED")
    identity, created, budget_root = _read_original_attempt(
        lane_root, expected_uid, reservation_id, revision_ref
    )
    fill = _confirmed_first_fill(reads, identity)
    if fill.time_ms / 1000 < created.timestamp():
        raise ValueError("BTC_DEMO_FILL_PREDATES_V2_ATTEMPT")
    episode_id = identity.identity_digest()
    evidence = {
        "attempt": episode_id,
        "anchors": fill.anchors_digest,
        "order_id": fill.order_id,
        "venue_native_id": _NATIVE,
        "lane": _LANE,
        "filled_quantity": fill.filled_quantity,
        "entry_price_usd": str(fill.price),
        "first_fill_time_ms": fill.time_ms,
        "fees": [
            {"trade_id": trade_id, "currency": currency, "signed_amount": amount}
            for trade_id, currency, amount in fill.fee_rows
        ],
    }
    opening_digest = canonical_digest_v1(evidence)
    source_ref = "okx_eea_demo_first_fill.v2:" + opening_digest
    episode_root = lane_root / "position-episodes" / episode_id
    with exclusive_v1(lane_root / ".first-fill.lock"):
        require_budget_head_read_only_v1(
            budget_root, account_identity=expected_uid, expected_digest=revision_ref[1]
        )
        immutable_json_v1(lane_root / "confirmed-first-fills" / f"{episode_id}.json", evidence)
        existing = episode_root.exists()
        episode = open_position_episode_binding_v1(
            identity=_episode_identity(identity),
            state_root=episode_root,
            mode="recover" if existing else "create",
            repository_sha=repository_sha,
            config_digest=config_digest,
            writer_session_id=writer_session_id,
            entry_source_ref=source_ref,
            entry_price_basis="CONFIRMED_POSITION_ENTRY_PRICE",
            entry_price=None if existing else float(fill.price),
            entry_event_time=None if existing else fill.time_ms / 1000,
        )
        if (episode.binding.entry_price, episode.binding.entry_event_time) != (
            float(fill.price),
            fill.time_ms / 1000,
        ):
            raise ValueError("BTC_DEMO_ENTRY_ANCHOR_READBACK_MISMATCH")
        publication = publish_confirmed_first_entry_c1_v2(
            episode=episode,
            cursor_root=cursor_root,
            g17_producer=g17_producer,
            writer_session_id=writer_session_id,
            retain_opening=lambda: opening_digest,
        )
        research = {
            "schema": "btc_demo_v2_confirmed_entry_research.v1",
            "episode_id": episode_id,
            "account_identity": expected_uid,
            "reservation_id": reservation_id,
            "budget_revision": list(revision_ref),
            "session_id": writer_session_id,
            "repository_sha": repository_sha,
            "config_digest": config_digest,
            "opening_digest": opening_digest,
            "c1_open_unix": publication["c1_open_unix"],
        }
        research_path = Path("research-first-fills") / f"{episode_id}.json"
        if (lane_root / research_path).exists():
            original = _read_owner_json(lane_root, research_path)
            confirmed_at = original["body"]["confirmed_at_utc"]
        else:
            confirmed_at = fill.confirmed_at_utc
        research["confirmed_at_utc"] = confirmed_at
        immutable_json_v1(
            lane_root / research_path,
            {"digest": canonical_digest_v1(research), "body": research},
        )
    return episode, publication
