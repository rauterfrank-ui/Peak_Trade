"""Explicit offline risk inputs and numerical vetoes; no capital/order authority.

Signed, potentially leveraged futures exposures are projected to a portfolio
return series before the original single-series VaR library is called. The
sum-to-one portfolio helper would change those exposures and is not used.
"""

from dataclasses import asdict, dataclass
from decimal import Decimal
import json
import math

from src.ops.portfolio_capital_reservation_budget_v1.durable_store_v1 import digest


def encoded(value):
    return json.loads(json.dumps(asdict(value), default=str, allow_nan=False))


def number(value, *, positive=False, nonnegative=False):
    if type(value) is not Decimal or not value.is_finite():
        raise ValueError("RISK_FINITE_DECIMAL_REQUIRED")
    if positive and value <= 0 or nonnegative and value < 0:
        raise ValueError("RISK_NUMERIC_DOMAIN_INVALID")
    if not math.isfinite(float(value)) or value != 0 and float(value) == 0:
        raise ValueError("RISK_FLOAT_PROJECTION_NONFINITE")
    return value


def text(value):
    if type(value) is not str or not value or value != value.strip():
        raise ValueError("RISK_SOURCE_IDENTITY_REQUIRED")


def instant(value):
    if type(value) is not int or value <= 0:
        raise ValueError("RISK_EXPLICIT_TIME_REQUIRED")


@dataclass(frozen=True)
class ReturnObservationV1:
    close_ms: int
    known_ms: int
    simple_return: Decimal


@dataclass(frozen=True)
class BookLevelV1:
    price: Decimal
    contracts: Decimal


@dataclass(frozen=True)
class InstrumentRiskInputV1:
    canonical_id: str
    native_id: str
    instrument_epoch: str
    contract_kind: str
    quantity_unit: str
    contract_multiplier: Decimal
    quote_currency: str
    settlement_currency: str
    price: Decimal
    quote_to_capital: Decimal
    price_event_ms: int
    price_known_ms: int
    fx_event_ms: int
    fx_known_ms: int
    price_source_ref: str
    fx_source_ref: str
    return_period_ms: int
    returns: tuple[ReturnObservationV1, ...]
    bids: tuple[BookLevelV1, ...]
    asks: tuple[BookLevelV1, ...]
    book_event_ms: int
    book_known_ms: int
    book_source_ref: str
    adv_quote_notional: Decimal | None
    adv_window_ms: int
    adv_event_ms: int
    adv_known_ms: int
    adv_source_ref: str


@dataclass(frozen=True)
class PositionRiskInputV1:
    canonical_id: str
    signed_contracts: Decimal
    # Original execution reconciliation must prove these fills. An ordinary
    # position without linked reservations remains a separate explicit source.
    covered_reservation_ids: tuple[str, ...]


@dataclass(frozen=True)
class PortfolioRiskInputV1:
    account: str
    environment: str
    as_of_ms: int
    portfolio_event_ms: int
    portfolio_known_ms: int
    portfolio_source_ref: str
    capital_currency: str
    capital_denominator_kind: str
    capital_denominator: Decimal
    capital_event_ms: int
    capital_known_ms: int
    capital_source_ref: str
    positions: tuple[PositionRiskInputV1, ...]
    instruments: tuple[InstrumentRiskInputV1, ...]


@dataclass(frozen=True)
class OfflineRiskPolicyV1:
    policy_id: str
    source_ref: str
    purpose: str
    confidence: Decimal
    left_tail_probability: Decimal
    return_period_ms: int
    horizon_ms: int
    minimum_horizon_samples: int
    maximum_input_age_ms: int
    maximum_return_age_ms: int
    maximum_capture_skew_ms: int
    maximum_var_loss_fraction: Decimal
    maximum_stress_loss_fraction: Decimal
    stress_kind: str
    stress_statistic: str
    stress_magnitude: Decimal
    stress_periods: int
    maximum_spread_bps: Decimal
    maximum_slippage_bps: Decimal
    depth_band_bps: Decimal
    minimum_depth_multiple: Decimal
    maximum_adv_participation: Decimal
    adv_window_ms: int

    def validate_v1(self):
        text(self.policy_id)
        text(self.source_ref)
        if self.purpose != "EXPLICIT_OFFLINE_TEST_POLICY":
            raise ValueError("RISK_OFFLINE_POLICY_REQUIRED")
        number(self.confidence, positive=True)
        number(self.left_tail_probability, positive=True)
        if (
            not Decimal("0.5") < self.confidence < 1
            or not self.confidence + self.left_tail_probability == 1
        ):
            raise ValueError("RISK_CONFIDENCE_TAIL_CONTRACT_INVALID")
        for value in (
            self.return_period_ms,
            self.horizon_ms,
            self.maximum_input_age_ms,
            self.maximum_return_age_ms,
            self.maximum_capture_skew_ms,
            self.adv_window_ms,
        ):
            instant(value)
        if (
            self.horizon_ms % self.return_period_ms
            or type(self.minimum_horizon_samples) is not int
            or self.minimum_horizon_samples < 2
        ):
            raise ValueError("RISK_HORIZON_OR_SAMPLE_CONTRACT_INVALID")
        for value in (
            self.maximum_var_loss_fraction,
            self.maximum_stress_loss_fraction,
            self.maximum_spread_bps,
            self.maximum_slippage_bps,
            self.depth_band_bps,
            self.minimum_depth_multiple,
            self.maximum_adv_participation,
        ):
            number(value, positive=True)
        if self.maximum_adv_participation > 1 or self.depth_band_bps > 10000:
            raise ValueError("RISK_LIQUIDITY_POLICY_DOMAIN_INVALID")
        number(self.stress_magnitude)
        if type(self.stress_periods) is not int or self.stress_periods <= 0:
            raise ValueError("RISK_STRESS_PERIODS_REQUIRED")
        if self.stress_statistic not in {"HISTORICAL_VAR", "WORST_LOSS", "MEAN_LOSS"}:
            raise ValueError("RISK_STRESS_STATISTIC_UNSUPPORTED")
        if self.stress_kind == "vol_spike":
            if self.stress_magnitude <= 1 or self.stress_statistic == "MEAN_LOSS":
                raise ValueError("RISK_VOL_SPIKE_MEAN_IS_NOT_TAIL_STRESS")
        elif self.stress_kind in {"shock", "regime_bear"}:
            if not -1 < self.stress_magnitude < 0:
                raise ValueError("RISK_STRESS_SHOCK_DOMAIN_INVALID")
        else:
            raise ValueError("RISK_STRESS_SCENARIO_UNSUPPORTED")


@dataclass(frozen=True)
class OfflineRiskRequestV1:
    data: PortfolioRiskInputV1
    policy: OfflineRiskPolicyV1
    slot_id: str
    decision_id: str
    cycle_id: str
    canonical_id: str
    native_id: str
    instrument_epoch: str
    side: str
    order_type: str
    limit_price_quote: Decimal | None
    configured_quantity_cap: Decimal | None


def _clock(event, known, asof, max_age):
    for value in (event, known, asof):
        instant(value)
    if not event <= known <= asof or asof - event > max_age or asof - known > max_age:
        raise ValueError("RISK_PIT_OR_FRESHNESS_INVALID")


def _portfolio_quantities(request, owner_snapshot):
    """Positions plus remaining original holds, never fill + full hold twice."""
    state = owner_snapshot["state"]
    sizing = state["sizing_bindings"]
    reservations = {
        r["reservation_id"]: r
        for r in state["reservations"]
        if r["state"] in {"RESERVED", "COMMITTED"}
    }
    quantities, covered = {}, set()
    for position in request.data.positions:
        text(position.canonical_id)
        number(position.signed_contracts)
        if position.canonical_id in quantities or len(set(position.covered_reservation_ids)) != len(
            position.covered_reservation_ids
        ):
            raise ValueError("RISK_POSITION_OR_COVERAGE_DUPLICATE")
        filled = Decimal(0)
        for rid in position.covered_reservation_ids:
            if rid in covered or rid not in reservations:
                raise ValueError("RISK_RESERVATION_COVERAGE_UNPROVEN")
            record = reservations[rid]
            link = state["execution_links"].get(rid)
            result = link.get("reconciliation") if link else None
            if (
                not result
                or result.get("matched") is not True
                or record["binding"]["bound"]["instrument_id"] != position.canonical_id
            ):
                raise ValueError("RISK_RESERVATION_FILL_COVERAGE_UNPROVEN")
            signed = 1 if sizing[rid]["decision"]["selected_side"].upper() == "LONG" else -1
            filled += signed * Decimal(result["decision"]["cumulative_filled_qty"])
            covered.add(rid)
        if position.covered_reservation_ids and filled != position.signed_contracts:
            raise ValueError("RISK_POSITION_FILL_QUANTITY_MISMATCH")
        quantities[position.canonical_id] = position.signed_contracts
    for rid, record in reservations.items():
        binding = sizing.get(rid)
        if binding is None:
            raise ValueError("RISK_EXISTING_HOLD_QUANTITY_UNPROVEN")
        side = binding["decision"]["selected_side"].upper()
        if side not in {"LONG", "SHORT"}:
            raise ValueError("RISK_HOLD_SIDE_INVALID")
        qty = Decimal(binding["decision"]["final_quantity"])
        link = state["execution_links"].get(rid)
        if link and link["phase"] == "SUBMIT_MAY_HAVE_OCCURRED":
            result = link.get("reconciliation")
            if not result or result.get("matched") is not True or rid not in covered:
                raise ValueError("RISK_UNCERTAIN_SUBMIT_EXPOSURE")
            qty -= Decimal(result["decision"]["cumulative_filled_qty"])
        elif record["state"] == "COMMITTED" and link is None:
            raise ValueError("RISK_COMMITTED_HOLD_EXECUTION_UNPROVEN")
        if qty < 0:
            raise ValueError("RISK_HOLD_OVERFILLED")
        canonical = record["binding"]["bound"]["instrument_id"]
        quantities[canonical] = quantities.get(canonical, Decimal(0)) + (
            qty if side == "LONG" else -qty
        )
    return quantities


def evaluate_offline_risk_v1(request, *, quantity, owner_snapshot):
    """Original numerical models, explicit units/PIT, exact sized candidate."""
    if (
        type(request) is not OfflineRiskRequestV1
        or type(request.policy) is not OfflineRiskPolicyV1
        or type(request.data) is not PortfolioRiskInputV1
    ):
        raise ValueError("RISK_TYPED_COMPLETE_REQUEST_REQUIRED")
    policy, data = request.policy, request.data
    policy.validate_v1()
    number(quantity, positive=True)
    for value in (
        request.slot_id,
        request.decision_id,
        request.cycle_id,
        request.canonical_id,
        request.native_id,
        request.instrument_epoch,
        data.account,
        data.capital_currency,
        data.portfolio_source_ref,
        data.capital_source_ref,
    ):
        text(value)
    if (
        data.environment != "INTERNAL_SIMULATED_EXECUTION"
        or data.capital_denominator_kind != "ACCOUNT_EQUITY"
    ):
        raise ValueError("RISK_EXPLICIT_OFFLINE_ACCOUNT_EQUITY_REQUIRED")
    number(data.capital_denominator, positive=True)
    state = owner_snapshot["state"]
    if (
        not owner_snapshot["admitted"]
        or owner_snapshot["recovery_required"]
        or data.account != state["account_identity"]
    ):
        raise ValueError("RISK_ADMITTED_ACCOUNT_SNAPSHOT_REQUIRED")
    lane = state["lane_bindings"].get(request.slot_id)
    if lane is None or (
        lane["bound"]["instrument_id"],
        lane["bound"]["venue_native_id"],
        lane["instrument_epoch"],
    ) != (request.canonical_id, request.native_id, request.instrument_epoch):
        raise ValueError("RISK_LANE_INSTRUMENT_GENERATION_MISMATCH")
    if request.side not in {"LONG", "SHORT"} or request.order_type not in {"market", "limit"}:
        raise ValueError("RISK_SIDE_OR_ORDER_TYPE_INVALID")
    if request.order_type == "limit":
        number(request.limit_price_quote, positive=True)
    elif request.limit_price_quote is not None:
        raise ValueError("RISK_MARKET_PRICE_OVERRIDE_FORBIDDEN")
    if request.configured_quantity_cap is not None and quantity > number(
        request.configured_quantity_cap, nonnegative=True
    ):
        raise ValueError("RISK_QUANTITY_CAP_EXCEEDED")
    _clock(
        data.portfolio_event_ms, data.portfolio_known_ms, data.as_of_ms, policy.maximum_input_age_ms
    )
    _clock(data.capital_event_ms, data.capital_known_ms, data.as_of_ms, policy.maximum_input_age_ms)
    if (
        type(data.positions) is not tuple
        or type(data.instruments) is not tuple
        or any(
            type(p) is not PositionRiskInputV1 or type(p.covered_reservation_ids) is not tuple
            for p in data.positions
        )
    ):
        raise ValueError("RISK_IMMUTABLE_TYPED_PORTFOLIO_REQUIRED")
    if data.capital_currency != state["capital_scope"]["settlement_currency"]:
        raise ValueError("RISK_OWNER_CAPITAL_CURRENCY_MISMATCH")
    instruments = {i.canonical_id: i for i in data.instruments}
    if len(instruments) != len(data.instruments) or len(
        {i.native_id for i in data.instruments}
    ) != len(instruments):
        raise ValueError("RISK_INSTRUMENT_ALIAS_OR_DUPLICATE")
    before = _portfolio_quantities(request, owner_snapshot)
    after = dict(before)
    after[request.canonical_id] = after.get(request.canonical_id, Decimal(0)) + (
        quantity if request.side == "LONG" else -quantity
    )
    required = set(before) | {request.canonical_id}
    if required - set(instruments):
        raise ValueError("RISK_PORTFOLIO_INSTRUMENT_DATA_MISSING")
    rows, before_weights, after_weights, captures = (
        {},
        {},
        {},
        [data.portfolio_known_ms, data.capital_known_ms],
    )
    times = None
    original_identities = {
        row["bound"]["instrument_id"]: (row["bound"]["venue_native_id"], row["instrument_epoch"])
        for row in state["lane_bindings"].values()
    }
    for key in sorted(required):
        item = instruments[key]
        if original_identities.get(key) != (item.native_id, item.instrument_epoch):
            raise ValueError("RISK_PORTFOLIO_DATA_GENERATION_MISMATCH")
        if (
            type(item) is not InstrumentRiskInputV1
            or item.contract_kind != "LINEAR"
            or item.quantity_unit != "CONTRACTS"
            or item.settlement_currency not in {item.quote_currency, data.capital_currency}
        ):
            raise ValueError("RISK_FUTURES_CONTRACT_OR_SETTLEMENT_UNSUPPORTED")
        for source in (
            item.canonical_id,
            item.native_id,
            item.instrument_epoch,
            item.quote_currency,
            item.price_source_ref,
            item.fx_source_ref,
        ):
            text(source)
        for value in (item.contract_multiplier, item.price, item.quote_to_capital):
            number(value, positive=True)
        if item.quote_currency == data.capital_currency and item.quote_to_capital != 1:
            raise ValueError("RISK_SAME_CURRENCY_FX_MUST_BE_ONE")
        _clock(item.price_event_ms, item.price_known_ms, data.as_of_ms, policy.maximum_input_age_ms)
        _clock(item.fx_event_ms, item.fx_known_ms, data.as_of_ms, policy.maximum_input_age_ms)
        captures.extend((item.price_known_ms, item.fx_known_ms))
        if (
            type(item.return_period_ms) is not int
            or item.return_period_ms != policy.return_period_ms
            or type(item.returns) is not tuple
            or not item.returns
            or type(item.bids) is not tuple
            or type(item.asks) is not tuple
        ):
            raise ValueError("RISK_RETURN_PERIOD_OR_DATA_MISSING")
        clock = tuple(r.close_ms for r in item.returns)
        if (
            times is not None
            and times != clock
            or any(b - a != policy.return_period_ms for a, b in zip(clock, clock[1:]))
        ):
            raise ValueError("RISK_RETURN_ALIGNMENT_OR_GAP_INVALID")
        times = clock
        for row in item.returns:
            if type(row) is not ReturnObservationV1 or number(row.simple_return) <= -1:
                raise ValueError("RISK_SIMPLE_RETURN_INVALID")
            _clock(row.close_ms, row.known_ms, data.as_of_ms, policy.maximum_return_age_ms)
        captures.append(item.returns[-1].known_ms)
        step = policy.horizon_ms // policy.return_period_ms
        if len(item.returns) % step or len(item.returns) // step < policy.minimum_horizon_samples:
            raise ValueError("RISK_INSUFFICIENT_COMPLETE_HORIZON_SAMPLES")
        grouped = []
        for start in range(0, len(item.returns), step):
            total = Decimal(1)
            for row in item.returns[start : start + step]:
                total *= 1 + row.simple_return
            grouped.append(float(number(total - 1)))
        rows[key] = grouped
        unit = (
            item.contract_multiplier * item.price * item.quote_to_capital / data.capital_denominator
        )
        before_weights[key] = float(number(before.get(key, Decimal(0)) * unit))
        after_weights[key] = float(number(after.get(key, Decimal(0)) * unit))
    candidate = instruments[request.canonical_id]
    captures.extend((candidate.book_known_ms, candidate.adv_known_ms))
    if max(captures) - min(captures) > policy.maximum_capture_skew_ms:
        raise ValueError("RISK_SNAPSHOT_CAPTURE_SKEW")
    import pandas as pd
    from src.risk.var import historical_var
    from src.risk.stress import StressScenario, apply_scenario_to_returns

    frame = pd.DataFrame(rows)
    prior = sum((frame[k] * before_weights[k] for k in rows))
    projected = sum((frame[k] * after_weights[k] for k in rows))
    tail = float(policy.left_tail_probability)
    if policy.stress_periods > len(frame):
        raise ValueError("RISK_STRESS_PERIOD_EXCEEDS_HISTORY")
    params = (
        {"multiplier": float(policy.stress_magnitude)}
        if policy.stress_kind == "vol_spike"
        else {"shock_pct": float(policy.stress_magnitude), "days": policy.stress_periods}
        if policy.stress_kind == "shock"
        else {"drift_pct": float(policy.stress_magnitude), "duration_days": policy.stress_periods}
    )
    scenario = StressScenario(policy.policy_id, policy.stress_kind, params)

    def metrics(weights, series):
        # Shock underlying returns before signed exposure projection. Applying a
        # negative asset shock directly to a short portfolio would reverse PnL.
        stressed = sum((apply_scenario_to_returns(frame[k], scenario) * weights[k] for k in rows))
        loss = (
            historical_var(stressed, alpha=tail)
            if policy.stress_statistic == "HISTORICAL_VAR"
            else -stressed.min()
            if policy.stress_statistic == "WORST_LOSS"
            else -stressed.mean()
        )
        var = historical_var(series, alpha=tail)
        if not all(math.isfinite(float(x)) for x in (loss, var)):
            raise ValueError("RISK_MODEL_RESULT_NONFINITE")
        return {
            "var_loss_fraction": str(max(0.0, float(var))),
            "stress_loss_fraction": str(max(0.0, float(loss))),
        }

    previous, final = metrics(before_weights, prior), metrics(after_weights, projected)
    item = instruments[request.canonical_id]
    if (item.native_id, item.instrument_epoch) != (request.native_id, request.instrument_epoch):
        raise ValueError("RISK_CANDIDATE_DATA_GENERATION_MISMATCH")
    liquidity = _liquidity(request, item, quantity)
    reasons = []
    if Decimal(final["var_loss_fraction"]) > policy.maximum_var_loss_fraction:
        reasons.append("RISK_VAR_LIMIT")
    if Decimal(final["stress_loss_fraction"]) > policy.maximum_stress_loss_fraction:
        reasons.append("RISK_STRESS_LIMIT")
    reasons.extend(liquidity.pop("reason_codes"))
    return {
        "schema": "offline_decision_bound_risk_result.v1",
        "status": "BLOCK" if reasons else "PASS",
        "reason_codes": reasons,
        "before": previous,
        "after": final,
        "liquidity": liquidity,
        "quantity": str(quantity),
        "notional_capital": str(
            (item.price * item.quote_to_capital) * item.contract_multiplier * quantity
        ),
        "signed_before_contracts": {k: str(v) for k, v in sorted(before.items())},
        "signed_after_contracts": {k: str(v) for k, v in sorted(after.items())},
        "horizon_ms": policy.horizon_ms,
        "sample_period_ms": policy.return_period_ms,
        "horizon_samples": len(frame),
        "aggregation": "NONOVERLAPPING_COMPOUND_ASSET_RETURNS_STATIC_SIGNED_EXPOSURE",
        "capital_denominator_kind": data.capital_denominator_kind,
        "capital_currency": data.capital_currency,
        "owner_snapshot_digest": owner_snapshot["digest"],
        "request_digest": digest(encoded(request)),
        "authority_effect": "NONE",
    }


def _liquidity(request, item, quantity):
    policy, data = request.policy, request.data
    _clock(item.book_event_ms, item.book_known_ms, data.as_of_ms, policy.maximum_input_age_ms)
    _clock(item.adv_event_ms, item.adv_known_ms, data.as_of_ms, policy.maximum_input_age_ms)
    text(item.book_source_ref)
    text(item.adv_source_ref)
    if (
        max(item.book_known_ms, item.adv_known_ms, data.portfolio_known_ms)
        - min(item.book_known_ms, item.adv_known_ms, data.portfolio_known_ms)
        > policy.maximum_capture_skew_ms
    ):
        raise ValueError("RISK_LIQUIDITY_CAPTURE_SKEW")
    if item.adv_window_ms != policy.adv_window_ms:
        raise ValueError("RISK_ADV_WINDOW_MISMATCH")
    adv = number(item.adv_quote_notional, positive=True)
    if not item.bids or not item.asks:
        raise ValueError("RISK_REQUIRED_DEPTH_MISSING")
    for levels, descending in ((item.bids, True), (item.asks, False)):
        for level in levels:
            if type(level) is not BookLevelV1:
                raise ValueError("RISK_BOOK_LEVEL_TYPE_INVALID")
            number(level.price, positive=True)
            number(level.contracts, positive=True)
        if any(
            (a.price <= b.price if descending else a.price >= b.price)
            for a, b in zip(levels, levels[1:])
        ):
            raise ValueError("RISK_BOOK_ORDER_OR_DUPLICATE_INVALID")
    bid, ask = item.bids[0].price, item.asks[0].price
    if bid > ask:
        raise ValueError("RISK_CROSSED_BOOK")
    spread = (ask - bid) / ((ask + bid) / 2) * 10000
    side = item.asks if request.side == "LONG" else item.bids
    best = side[0].price
    remaining, cost, capacity = quantity, Decimal(0), Decimal(0)
    for level in side:
        distance = abs(level.price / best - 1) * 10000
        if distance <= policy.depth_band_bps:
            capacity += level.contracts
        executable = request.order_type == "market" or (
            level.price <= request.limit_price_quote
            if request.side == "LONG"
            else level.price >= request.limit_price_quote
        )
        if executable:
            taken = min(remaining, level.contracts)
            cost += taken * level.price
            remaining -= taken
    slippage = abs(cost / quantity / best - 1) * 10000 if remaining == 0 else None
    notional_quote = quantity * item.contract_multiplier * item.price
    participation = notional_quote / adv
    reasons = []
    if remaining or capacity < quantity * policy.minimum_depth_multiple:
        reasons.append("RISK_DEPTH_OR_IMMEDIATE_EXECUTION_CAPACITY")
    if spread > policy.maximum_spread_bps:
        reasons.append("RISK_SPREAD_LIMIT")
    if slippage is not None and slippage > policy.maximum_slippage_bps:
        reasons.append("RISK_SLIPPAGE_LIMIT")
    if participation > policy.maximum_adv_participation:
        reasons.append("RISK_ADV_PARTICIPATION_LIMIT")
    return {
        "spread_bps": str(spread),
        "slippage_bps": str(slippage) if slippage is not None else None,
        "depth_contracts_in_band": str(capacity),
        "adv_participation": str(participation),
        "execution_policy": "IMMEDIATE_EXECUTION_ONLY",
        "reason_codes": reasons,
    }
