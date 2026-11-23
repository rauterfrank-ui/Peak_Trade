"""Opening observation of a new, isolated USD Paper account before the Cap24 check."""

from dataclasses import replace
from decimal import Decimal
from hashlib import sha256
import json
from pathlib import Path

from src.ops.bounded_peaktrade_system_composition_v1.zkp_paper_market_v1 import (
    PAPER_ALLOCATION_USDC,
)
from src.ops.exit_policy_producer_binding_v1.models_v1 import canonical_digest_v1
from src.ops.productive_futures_accounting_runtime_binding_v1.accounting_engine_v1 import (
    ProductiveFuturesAccountingSessionV1,
)


def paper_account_opening_v1(*, config, market):
    """Observe the accounting owner's initialized state in the session's quote currency."""
    if (
        config["surface"] != "PAPER_EXCHANGE"
        or (market.slot.lane_id, market.slot.instrument_id, market.slot.native_id)
        != (config["lane"], config["canonical_instrument_id"], config["native_instrument_id"])
        or market.native_contract.quote_currency != "USD"
    ):
        raise ValueError("PAPER_ACCOUNT_OPENING_SCOPE")
    account = ProductiveFuturesAccountingSessionV1(
        contract=market.native_contract, initial_equity=PAPER_ALLOCATION_USDC * market.usd_per_usdc
    )
    return {
        "schema": "isolated_paper_account_opening.v1",
        "session": config["session_id"],
        "lane": config["lane"],
        "instrument": market.slot.instrument_id,
        "native_id": market.slot.native_id,
        "surface": "PAPER_EXCHANGE",
        "quote": market.native_contract.quote_currency,
        "n5_selection_digest": config["n5_source"]["selection_digest"],
        "contract_digest": market.native_contract.digest(),
        "allocation_usdc": str(PAPER_ALLOCATION_USDC),
        "usd_per_usdc": str(market.usd_per_usdc),
        "fx_source_sha256": market.source_hashes["usdc-index"],
        "observed_at_unix": market.observed_unix,
        "portfolio": account.portfolio_state().to_dict(),
    }


def read_paper_account_opening_v1(config, market):
    source = config["paper_account_opening"]
    path = Path(source["path"])
    if path != path.resolve() or path.parent.name != config["session_id"]:
        raise ValueError("PAPER_ACCOUNT_OPENING_SESSION")
    initial = json.loads(path.read_bytes())
    if canonical_digest_v1(initial) != source["digest"]:
        raise ValueError("PAPER_ACCOUNT_OPENING_DIGEST")
    market_dir = Path(source["market_dir"])
    if (
        market_dir != market_dir.resolve()
        or market_dir.parent != path.parent
        or not market_dir.name.startswith("opening-market-")
    ):
        raise ValueError("PAPER_ACCOUNT_OPENING_MARKET_ROOT")
    fx_path = market_dir / "usdc-index.json"
    fx_bytes = fx_path.read_bytes()
    receipt = json.loads((fx_path.parent / "receipts.json").read_bytes())["usdc-index"]
    if (
        receipt["file"] != str(fx_path)
        or receipt["endpoint"] != "/api/v5/market/index-tickers?instId=USDC-USD"
        or receipt["method"] != "GET"
        or receipt["auth_header_sent"] is not False
        or receipt["venue_live_contact"] is not True
        or receipt["get_performed"] is not True
        or receipt["http_status"] != 200
        or sha256(fx_bytes).hexdigest() != receipt["body_sha256"]
        or receipt["body_sha256"] != initial["fx_source_sha256"]
    ):
        raise ValueError("PAPER_ACCOUNT_OPENING_FX_SOURCE")
    payload = json.loads(fx_bytes)
    rows = payload["data"]
    if payload["code"] != "0" or len(rows) != 1 or rows[0]["instId"] != "USDC-USD":
        raise ValueError("PAPER_ACCOUNT_OPENING_FX_ID")
    fx = Decimal(rows[0]["idxPx"])
    # Recreate this same initial ledger from the retained original FX. Today's
    # market still supplies current risk valuation and live liquidity.
    opening_market = replace(
        market,
        usd_per_usdc=fx,
        observed_unix=initial["observed_at_unix"],
        source_hashes={**market.source_hashes, "usdc-index": receipt["body_sha256"]},
    )
    if (
        not fx.is_finite()
        or fx <= 0
        or paper_account_opening_v1(config=config, market=opening_market) != initial
    ):
        raise ValueError("PAPER_ACCOUNT_OPENING_READBACK")
    return initial
