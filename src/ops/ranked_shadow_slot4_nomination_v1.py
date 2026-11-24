"""Validate the approved, non-authoritative minimum-lot comparison against its public originals."""

from decimal import Decimal
from hashlib import sha256
from datetime import datetime, timezone
import json
from pathlib import Path
from urllib.parse import parse_qs, urlsplit

from src.ops.bounded_peaktrade_system_composition_v1.paper_market_liquidity_v1 import (
    PaperBookV1,
    _fresh,
    _one,
)
from src.ops.governed_productive_monetary_normalization_v1.usdt_usdc_index_observation_v1 import (
    build_usdt_usdc_conversion_edge_from_index_tickers_v1,
)
from src.ops.full_core_live_path_composition_root_v1.execution_admission_contract_v1 import (
    FreshPretradeGetStatusV1,
)
from src.ops.integrated_paper_shadow_observation_session_v1.portfolio_economics_model_v1 import (
    PortfolioEconomicsModelParamsV1,
)
from src.ops.okx_native_instrument_and_mark_price_runtime_binding_fail_closed_v1.i17_shadow_instrument_v1 import (
    swap_queries_v1,
)
from src.ops.peak_trade_public_market_data_runtime_v1.freshness_v1 import (
    classify_live_mark_price_freshness_v1,
    classify_live_best_bid_ask_freshness_v1,
)


def require_slot4_nomination_v1(path, approved_digest, *, target, rank, universe, occupied, now):
    """The pinned comparison nominates a candidate. Actual entry still requires original CRS and budget."""
    path = Path(path)
    raw = path.read_bytes()
    if sha256(raw).hexdigest() != approved_digest:
        raise ValueError("SHADOW_SLOT4_NOMINATION_DIGEST_MISMATCH")
    doc = json.loads(raw)
    if (
        doc["ranking_digest"] != rank.integrity_digest
        or doc["ranking_id"] != rank.ranking_snapshot_id
        or doc["test_limit_usdc"] != "10"
        or doc["authority"] != "NONE"
    ):
        raise ValueError("SHADOW_SLOT4_NOMINATION_SCOPE_MISMATCH")
    swaps = {
        i.canonical_instrument_id
        for i in universe.instruments
        if i.eligibility
        and (i.instrument_type, i.contract_type, i.quote_currency, i.settlement_currency)
        == ("SWAP", "linear_perpetual", "USDT", "USDT")
    }
    rows = {r["instrument"]: r for r in doc["rows"]}
    if len(rows) != len(doc["rows"]):
        raise ValueError("SHADOW_SLOT4_NOMINATION_DUPLICATE")
    for candidate in rank.ranked_candidates:
        if (
            candidate.canonical_instrument_id not in swaps
            or candidate.canonical_instrument_id in occupied
            or candidate.eligibility_status != "ELIGIBLE"
        ):
            continue
        row = rows.get(candidate.venue_native_id)
        if not row or row["rank"] != candidate.rank or row["freshness_blockers"]:
            raise ValueError("SHADOW_SLOT4_PRIOR_CANDIDATE_UNPROVEN")
        costs = row["costs_included_usdc"]
        if set(costs) != {"BUY_lower", "BUY_upper", "SELL_lower", "SELL_upper"}:
            raise ValueError("SHADOW_SLOT4_NOMINATION_COSTS_MISSING")
        if candidate.canonical_instrument_id == target.canonical_id:
            if (
                row["public_and_budget_screen"] is not True
                or row["within_cost_envelope"] is not True
                or any(
                    v is None or not Decimal(v).is_finite() or not 0 < Decimal(v) <= 10
                    for v in costs.values()
                )
            ):
                raise ValueError("SHADOW_SLOT4_MINIMUM_LOT_NOT_ADMITTED")
            break
        # An upper bound above budget alone cannot exclude a cheaper predecessor.
        if not all(
            costs[side + "_lower"] is not None and Decimal(costs[side + "_lower"]) > 10
            for side in ("BUY", "SELL")
        ):
            raise ValueError("SHADOW_SLOT4_PRIOR_CANDIDATE_NOT_EXCLUDED")
    else:
        raise ValueError("SHADOW_SLOT4_NOMINATION_NOT_RANKED")
    checks = {
        target.native_id + "." + k: v
        for k, v in swap_queries_v1(target.native_id, target.base + "-USDT").items()
    }
    checks[target.native_id + ".instrument"] = (
        "/api/v5/public/instruments",
        {"instType": "SWAP", "instId": target.native_id},
    )
    checks["fx"] = ("/api/v5/market/index-tickers", {"instId": "USDC-USDT"})
    receipts = doc["receipts"]
    originals = {}
    for key, (route, query) in checks.items():
        r = receipts[key]
        url = urlsplit(r["url"])
        body = path.with_name(key + ".json").read_bytes()
        if (
            sha256(body).hexdigest() != r["sha256"]
            or (url.scheme, url.netloc, url.path) != ("https", "eea.okx.com", route)
            or parse_qs(url.query) != {k: [v] for k, v in query.items()}
            or not r["started"] <= r["received"] <= now
        ):
            raise ValueError("SHADOW_SLOT4_NOMINATION_PUBLIC_SOURCE_MISMATCH")
        payload = json.loads(body)
        if payload["code"] != "0":
            raise ValueError("SHADOW_SLOT4_NOMINATION_PUBLIC_SOURCE_MISMATCH")
        originals[key.split(".")[-1]] = payload
        doc_row = _one(payload, None if key.endswith(".book") else query["instId"])
        if key.endswith(".funding"):
            if not (
                0 <= now - int(doc_row["ts"]) / 1000 <= 180
                and now < int(doc_row["fundingTime"]) / 1000
            ):
                raise ValueError("SHADOW_SLOT4_FUNDING_OUTSIDE_WINDOW")
        elif not key.endswith(".instrument"):
            _fresh(
                doc_row,
                r["received"],
                now,
                classify_live_best_bid_ask_freshness_v1
                if key.endswith(".book")
                else classify_live_mark_price_freshness_v1,
            )
    if receipts["fx"]["started"] < receipts[target.native_id + ".mark"]["received"]:
        raise ValueError("SHADOW_SLOT4_FX_BEFORE_MARK")
    from src.ops.ranked_shadow_first_purchase_v1 import (
        ranked_shadow_book_cost_limit_v1,
        _native_constraints,
    )

    instrument = next(
        i for i in universe.instruments if i.canonical_instrument_id == target.canonical_id
    )
    native = _native_constraints(originals["instrument"], instrument)
    mark = Decimal(_one(originals["mark"], target.native_id)["markPx"])
    epoch = datetime.fromtimestamp(now, timezone.utc).isoformat()
    fx = build_usdt_usdc_conversion_edge_from_index_tickers_v1(
        index_tickers_payload=originals["fx"],
        decision_epoch=epoch,
        observed_at=epoch,
        fresh_pretrade_get_status=FreshPretradeGetStatusV1.TRUSTED_PRESENT.value,
        pair_base_currency="USDC",
        pair_quote_currency="USDT",
        provenance_ref=receipts["fx"]["sha256"],
    ).normalized_rate
    book = PaperBookV1.from_okx_v1(
        _one(originals["book"]), tick=native.tick_size, lot=native.lot_size
    )
    base = native.minimum_quantity * native.contract_multiplier
    if (
        not mark.is_finite()
        or mark <= 0
        or Decimal(row["contracts"]) != native.minimum_quantity
        or Decimal(row["nominal_usdc"]) != base * mark * fx
    ):
        raise ValueError("SHADOW_SLOT4_MINIMUM_LOT_MISMATCH")
    for side in ("BUY", "SELL"):
        _, quote = ranked_shadow_book_cost_limit_v1(
            PortfolioEconomicsModelParamsV1(),
            book,
            originals["funding"],
            target.native_id,
            native,
            mark,
            side,
            Decimal(0),
            10 / fx,
            10 / fx,
        )
        minimum = quote(native.minimum_quantity)
        required = (
            max(
                base * Decimal(minimum["opening_book_usdt_per_base"]),
                base * mark + Decimal(minimum["cost_allowance_usdt"]),
            )
            * fx
        )
        if required != Decimal(costs[side + "_lower"]) or required > Decimal(
            costs[side + "_upper"]
        ):
            raise ValueError("SHADOW_SLOT4_MINIMUM_LOT_MISMATCH")
