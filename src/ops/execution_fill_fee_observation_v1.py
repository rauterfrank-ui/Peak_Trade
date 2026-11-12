"""Read signed venue fees from a reconciled order's retained K1 fills."""

from __future__ import annotations

import json
import re
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from fractions import Fraction
from hashlib import sha256
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit

from src.meta.learning_loop.contract_safety_v1 import compute_content_sha256
from src.ops.execution_reconciliation_proof_store_v1 import (
    read_authenticated_execution_reconciliation_source_v1,
)
from src.ops.full_core_live_path_composition_root_v1.full_core_exchange_reconciliation_okx_read_only_provider_v1 import (
    ENDPOINT_TRADE_FILLS,
)
from src.ops.full_core_live_path_composition_root_v1.full_core_exchange_reconciliation_v1 import (
    OUTCOME_CONFIRMED_FILLED,
    EvidenceLayer,
)

_EPOCH = datetime(1970, 1, 1, tzinfo=timezone.utc)
_SIDE = {"LONG": "buy", "ENTER_LONG": "buy", "SHORT": "sell", "ENTER_SHORT": "sell"}


def _decimal_field(value: Any, *, field: str, positive: bool = False) -> Decimal:
    if not isinstance(value, str) or not re.fullmatch(r"-?[0-9]+(?:\.[0-9]+)?", value):
        raise ValueError(f"FILL_FEE_MISSING_OR_INVALID:{field}")
    amount = Decimal(value)
    if positive and amount <= 0:
        raise ValueError(f"FILL_FEE_MISSING_OR_INVALID:{field}")
    return amount


def read_authenticated_execution_fill_fee_observation_v1(
    *,
    root: Path,
    budget_owner_root: Path,
    account: str,
    session_id: str,
    reservation_id: str,
    revision_ref: tuple[int, str],
) -> dict[str, Any]:
    """Project confirmed fills from the historical readback without recontacting the venue."""
    archived = read_authenticated_execution_reconciliation_source_v1(
        root=root,
        budget_owner_root=budget_owner_root,
        account=account,
        session_id=session_id,
        reservation_id=reservation_id,
        revision_ref=revision_ref,
    )
    proof, identity = archived.proof, archived.identity
    decision = archived.reconciliation["decision"]
    if (
        archived.reconciliation["matched"] is not True
        or decision["outcome"] != OUTCOME_CONFIRMED_FILLED
        or decision["reconciliation_complete"] is not True
        or not decision["venue_ord_id"]
    ):
        raise ValueError("FILL_FEE_CONFIRMED_FILLED_ORDER_REQUIRED")
    fills_gets = [get for get in proof.gets if urlsplit(get.endpoint).path == ENDPOINT_TRADE_FILLS]
    if len(fills_gets) != 1:
        raise ValueError("FILL_FEE_ORIGINAL_GET_REQUIRED")
    (fills_get,) = fills_gets
    filled_by_id = {}
    side = _SIDE.get(identity.selected_side.upper())
    if side is None or identity.quantity_unit.upper() not in {"CONTRACT", "CONTRACTS"}:
        raise ValueError("FILL_FEE_ORDER_UNITS_OR_SIDE_UNPROVEN")
    for item in archived.snapshot.evidence_items:
        if item.layer is not EvidenceLayer.EXCHANGE_FILL_STATE or item.source != "fills":
            continue
        row = item.payload
        trade_id = row.get("tradeId")
        if (
            row.get("instId") != identity.native_id
            or row.get("clOrdId") != identity.clordid
            or row.get("ordId") != decision["venue_ord_id"]
            or row.get("side") != side
            or not isinstance(trade_id, str)
            or not trade_id.strip()
            or trade_id != trade_id.strip()
        ):
            raise ValueError("FILL_FEE_IDENTITY_MISMATCH")
        quantity = _decimal_field(row.get("fillSz"), field="fillSz", positive=True)
        _decimal_field(row.get("fillPx"), field="fillPx", positive=True)
        _decimal_field(row.get("fee"), field="fee")
        currency = row.get("feeCcy")
        if not isinstance(currency, str) or not re.fullmatch(r"[A-Z0-9]+", currency):
            raise ValueError("FILL_FEE_CURRENCY_REQUIRED")
        if row.get("execType") not in ("M", "T"):
            raise ValueError("FILL_FEE_LIQUIDITY_ROLE_REQUIRED")
        timestamp = row.get("fillTime")
        if not isinstance(timestamp, str) or not re.fullmatch(r"[0-9]{1,16}", timestamp):
            raise ValueError("FILL_FEE_EVENT_TIME_REQUIRED")
        try:
            filled_at = _EPOCH + timedelta(milliseconds=int(timestamp))
        except OverflowError as exc:
            raise ValueError("FILL_FEE_EVENT_TIME_INVALID") from exc
        if not _EPOCH < filled_at <= fills_get.acquired_at:
            raise ValueError("FILL_FEE_EVENT_TIME_INVALID")
        fill = {
            "trade_id": trade_id,
            "side": side,
            "filled_at_utc": filled_at.isoformat(),
            "quantity_contracts": row["fillSz"],
            "fill_price": row["fillPx"],
            "fee": row["fee"],
            "fee_currency": currency,
            "execution_type": row["execType"],
        }
        if trade_id in filled_by_id and filled_by_id[trade_id][0] != fill:
            raise ValueError("FILL_FEE_CONFLICTING_TRADE_ID")
        filled_by_id[trade_id] = (fill, Fraction(quantity))

    if not filled_by_id or sum(quantity for _, quantity in filled_by_id.values()) != _decimal_field(
        decision["cumulative_filled_qty"], field="confirmed_quantity", positive=True
    ):
        raise ValueError("FILL_FEE_CONFIRMED_QUANTITY_NOT_COVERED")
    fills = sorted(
        (fill for fill, _ in filled_by_id.values()),
        key=lambda fill: (fill["filled_at_utc"], fill["trade_id"]),
    )
    body = {
        "schema_version": "execution_fill_fee_observation_v1",
        "authority": "NONE",
        "venue_host": proof.venue_host,
        "venue": identity.venue,
        "execution_environment": identity.execution_environment,
        "instrument_id": identity.instrument_id,
        "native_instrument_id": identity.native_id,
        "execution_identity_digest": proof.identity_digest,
        "reservation_id": reservation_id,
        "venue_order_id": decision["venue_ord_id"],
        "budget_revision_ref": list(proof.revision_ref),
        "reconciliation_snapshot_digest": proof.snapshot_digest,
        "fills_get_body_sha256": fills_get.body_sha256,
        "fills_known_at_utc": fills_get.acquired_at.astimezone(timezone.utc).isoformat(),
        "reconciliation_known_at_utc": proof.gets[-1]
        .acquired_at.astimezone(timezone.utc)
        .isoformat(),
        "fills": fills,
    }
    return {**body, "observation_digest": compute_content_sha256(body)}


def measure_linear_swap_taker_fee_v1(
    observation: dict[str, Any],
    *,
    metadata_path: Path,
    expected_metadata_sha256: str,
) -> dict[str, Any]:
    """Use a pinned historical OKX instruments capture to price the archived taker fills."""
    raw = metadata_path.read_bytes()
    if sha256(raw).hexdigest() != expected_metadata_sha256:
        raise ValueError("FILL_FEE_METADATA_DIGEST_MISMATCH")
    capture = json.loads(raw)
    response = capture["response"]
    native_id = observation["native_instrument_id"]
    if (
        capture["venue_host"] != observation["venue_host"]
        or capture["endpoint"] != "/api/v5/public/instruments"
        or observation["venue"].upper() != "OKX"
        or response["code"] != "0"
        or not native_id.endswith("-SWAP")
        or len(native_id.split("-")) != 3
    ):
        raise ValueError("FILL_FEE_METADATA_SOURCE_MISMATCH")
    base, quote, _ = native_id.split("-")
    rows = [row for row in response["data"] if row.get("instId") == native_id]
    if len(rows) != 1:
        raise ValueError("FILL_FEE_METADATA_INSTRUMENT_UNPROVEN")
    (row,) = rows
    if (
        row.get("instType") != "SWAP"
        or row.get("ctType") != "linear"
        or row.get("ctValCcy") != base
        or row.get("settleCcy") != quote
    ):
        raise ValueError("FILL_FEE_METADATA_UNITS_UNPROVEN")
    contract_value = Fraction(_decimal_field(row.get("ctVal"), field="ctVal", positive=True))
    if _decimal_field(row.get("ctMult"), field="ctMult", positive=True) != 1:
        raise ValueError("FILL_FEE_CONTRACT_MULTIPLIER_UNSUPPORTED")
    known_at = datetime.fromisoformat(capture["known_at_utc"])
    if known_at.utcoffset() is None or known_at > datetime.fromisoformat(
        observation["fills"][0]["filled_at_utc"]
    ):
        raise ValueError("FILL_FEE_METADATA_AS_OF_FILL_UNPROVEN")

    total_notional = Fraction()
    total_cost = Fraction()
    for fill in observation["fills"]:
        if fill["fee_currency"] != quote:
            raise ValueError("FILL_FEE_CURRENCY_NOT_COMPARABLE")
        if fill["execution_type"] != "T":
            raise ValueError("FILL_FEE_TAKER_COMPARISON_REQUIRED")
        total_notional += (
            Fraction(fill["quantity_contracts"]) * contract_value * Fraction(fill["fill_price"])
        )
        # OKX reports a charge as negative and a rebate as positive.
        total_cost -= Fraction(fill["fee"])
    rate_bps = total_cost * 10_000 / total_notional
    return {
        "observation_digest": observation["observation_digest"],
        "instrument_metadata_sha256": expected_metadata_sha256,
        "instrument_metadata_known_at_utc": known_at.astimezone(timezone.utc).isoformat(),
        "contract_value": row["ctVal"],
        "contract_value_currency": row["ctValCcy"],
        "contract_multiplier": row["ctMult"],
        "notional_currency": quote,
        "notional_quote_exact": str(total_notional),
        "fee_cost_quote_exact": str(total_cost),
        "fee_bps_exact": str(rate_bps),
    }
