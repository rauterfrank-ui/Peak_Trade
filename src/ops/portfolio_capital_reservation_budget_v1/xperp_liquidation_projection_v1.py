"""Conditional liquidation projection for a proven USDC cross account."""

from dataclasses import dataclass, replace
from fractions import Fraction
import json
import re

from . import entry_execution_cost_v1 as cost
from .durable_store_v1 import canonical, digest
from .native_cost_cover_v1 import original_costs_v1

_CAPTURE_SCHEMA = "xperp_liquidation_custody.v1"
_BINDING_SCHEMA = "xperp_liquidation_binding.v1"


def capture_liquidation_custody_v1(owner, proof, *, candidate_id=None):
    from .host_v1 import FuturesFinancialCustodyV1

    if (
        type(proof) is not FuturesFinancialCustodyV1
        or proof.local_commitments.source_owner is not owner
    ):
        raise ValueError("XPERP_LIQUIDATION_ORIGINAL_CUSTODY_REQUIRED")
    inputs = proof.read_v1()
    if inputs.current_cross_balance_with_pnl_usdc is None:
        raise ValueError("XPERP_LIQUIDATION_CURRENT_CROSS_BALANCE_UNPROVEN")
    local = proof.local_commitments
    active = {
        row.reservation_id: row
        for row in local.commitments
        if row.state in {"RESERVED", "COMMITTED"}
    }
    candidate = active.pop(candidate_id, None)
    if candidate_id is not None and (
        candidate is None
        or (candidate.state, candidate.execution_phase) != ("COMMITTED", "PLAN_BOUND")
    ):
        raise ValueError("XPERP_LIQUIDATION_LATE_CANDIDATE_CUSTODY_UNPROVEN")
    positions = _capture_original_open_positions(owner, active, local.generation_digest)
    if positions:
        terms = proof.fetch_xperp_position_terms_v1(tuple(sorted(positions)))
        for native, sources in terms.items():
            positions[native]["sources"] = sources
    return dict(
        schema=_CAPTURE_SCHEMA,
        account_identity=local.account_identity,
        local_generation=local.generation_digest,
        evaluated_at_utc=cost.utc_now_iso_v1(),
        candidate_id=candidate_id,
        gets=inputs.gets,
        open_positions=positions,
    )


def _capture_original_open_positions(owner, active, generation):
    from .execution_v1 import validate_link_v1
    from .local_commitment_readback_v1 import read_local_commitments_locked_v1
    from src.ops.full_core_live_path_composition_root_v1.full_core_exchange_reconciliation_v1 import (
        OUTCOME_CONFIRMED_FILLED,
        parse_exchange_reconciliation_identity_v1,
    )

    positions = {}
    with owner._lock:
        if read_local_commitments_locked_v1(owner).generation_digest != generation:
            raise ValueError("XPERP_LIQUIDATION_LOCAL_GENERATION_CHANGED")
        durable_links = {}
        if active:
            store = owner._store
            revision = store.read_revision_v1(store.sequence, store.head)
            durable_links = revision["state"].get("execution_links", {})
        for rid, commitment in active.items():
            link = owner._execution_links.get(rid, {})
            reconciliation = link.get("reconciliation") or {}
            decision = reconciliation.get("decision", {})
            identity = link.get("identity") or {}
            sizing = owner._sizing_bindings.get(owner._by_id.get(rid))
            if (
                commitment.state != "COMMITTED"
                or reconciliation.get("matched") is not True
                or decision.get("reconciliation_complete") is not True
                or decision.get("outcome") != OUTCOME_CONFIRMED_FILLED
                or sizing is None
                or commitment.venue_native_id in positions
                or identity.get("native_id") != commitment.venue_native_id
                or identity.get("account_identity") != owner._account_identity
            ):
                raise ValueError("XPERP_LIQUIDATION_OTHER_LOCAL_OBLIGATIONS_UNPROVEN")
            identity_digest = parse_exchange_reconciliation_identity_v1(identity).identity_digest()
            if (
                durable_links.get(rid) != link
                or reconciliation["identity_digest"] != identity_digest
            ):
                raise ValueError("XPERP_LIQUIDATION_OPEN_FILL_READBACK_MISMATCH")
            validate_link_v1(owner, rid, link)
            quantity = Fraction(decision["cumulative_filled_qty"])
            side = identity["selected_side"].removeprefix("ENTER_")
            if quantity != Fraction(sizing.decision.final_quantity) or side not in {
                "LONG",
                "SHORT",
            }:
                raise ValueError("XPERP_LIQUIDATION_OPEN_FILL_MISMATCH")
            positions[commitment.venue_native_id] = dict(
                signed_quantity=str(quantity if side == "LONG" else -quantity),
                stop=sizing.monetary_source.native_protective_stop_price,
                closing=str(commitment.closing_cost_reserve),
                funding=str(commitment.funding_cost_reserve),
                reconciliation_identity_digest=identity_digest,
            )
    return positions


def _account_basis(snapshot, account, available, now):
    from src.ops.okx_eea_private_account_state_runtime_v1.k1_source_v1 import (
        FUTURES_FINANCIAL_BASE_GETS,
        _cross_balance_with_pnl_v1,
        futures_financial_pending_gets_v1,
    )

    if (
        set(snapshot)
        != {
            "schema",
            "account_identity",
            "local_generation",
            "evaluated_at_utc",
            "candidate_id",
            "gets",
            "open_positions",
        }
        or snapshot["schema"] != _CAPTURE_SCHEMA
        or snapshot["account_identity"] != account
        or not re.fullmatch("[0-9a-f]{64}", snapshot["local_generation"])
    ):
        raise ValueError("XPERP_LIQUIDATION_CUSTODY_IDENTITY_INVALID")
    observed = snapshot["evaluated_at_utc"]
    cost.acquisition_age_seconds_v1(acquired_at_utc=observed, now_utc=now)
    config_path, balance_path, positions_path = FUTURES_FINANCIAL_BASE_GETS
    pending = futures_financial_pending_gets_v1()
    gets = snapshot["gets"]
    if set(gets) != {*FUTURES_FINANCIAL_BASE_GETS, *pending}:
        raise ValueError("XPERP_LIQUIDATION_INVENTORY_INCOMPLETE")
    session = gets[config_path]["pretrade_decision_id"]
    if not isinstance(session, str) or not session:
        raise ValueError("XPERP_LIQUIDATION_INVENTORY_SESSION_REQUIRED")
    for endpoint, raw in gets.items():
        row = cost.FreshPretradeGetTransportResultV1(**raw)
        if (
            row.endpoint != endpoint
            or row.method != "GET"
            or row.get_performed is not True
            or row.auth_header_sent is not True
            or row.venue_live_contact is not True
            or row.historical_reuse is not False
            or row.http_status != 200
            or row.error_class
            or row.pretrade_decision_id != session
            or not re.fullmatch("[0-9a-f]{64}", row.body_sha256 or "")
            or set(row.payload) - {"code", "msg", "data"}
        ):
            raise ValueError("XPERP_LIQUIDATION_ORIGINAL_INVENTORY_GET_REQUIRED")
        cost.acquisition_age_seconds_v1(acquired_at_utc=row.acquired_at_utc, now_utc=observed)
        cost.acquisition_age_seconds_v1(acquired_at_utc=row.acquired_at_utc, now_utc=now)
        data = cost._rows(row.payload)
        if endpoint in pending and data:
            raise ValueError("XPERP_LIQUIDATION_VENUE_PENDING_UNPROVEN")
    config = cost._rows(gets[config_path]["payload"])
    if len(config) != 1 or any(
        config[0].get(key) != expected
        for key, expected in (
            ("uid", account),
            ("acctLv", "2"),
            ("posMode", "net_mode"),
            ("settleCcy", "USDC"),
            ("autoLoan", False),
        )
    ):
        raise ValueError("XPERP_LIQUIDATION_ACCOUNT_SCOPE_UNPROVEN")
    balance = cost._rows(gets[balance_path]["payload"])
    if len(balance) != 1 or balance[0].get("uid", account) != account:
        raise ValueError("XPERP_LIQUIDATION_BALANCE_SCOPE_UNPROVEN")
    usdc = cost._one(balance[0]["details"], "ccy", "USDC")
    cross = _cross_balance_with_pnl_v1(usdc)
    positions = cost._rows(gets[positions_path]["payload"])
    known = snapshot["open_positions"]
    if len(positions) != len(known) or {row.get("instId") for row in positions} != set(known):
        raise ValueError("XPERP_LIQUIDATION_EXISTING_POSITION_UNPROVEN")
    if (
        cross is None
        or not positions
        and Fraction(usdc["frozenBal"]) != 0
        or Fraction(usdc["availEq"]) != Fraction(available)
        or any(
            usdc.get(key, "") not in ("", None) and _venue_decimal(usdc[key]) != 0
            for key in ("liab", "crossLiab", "isoLiab", "interest", "rewardBal")
        )
        or not positions
        and usdc.get("upl") not in (None, "", "0")
        and _venue_decimal(usdc["upl"]) != 0
    ):
        raise ValueError("XPERP_LIQUIDATION_FLAT_CAPITAL_BASIS_UNPROVEN")
    return cross, config[0], positions, session


def _venue_decimal(value):
    if (
        not isinstance(value, str)
        or len(value) > 128
        or re.fullmatch(r"-?[0-9]+(?:\.[0-9]+)?", value) is None
    ):
        raise ValueError("XPERP_LIQUIDATION_VENUE_NUMBER_INVALID")
    return Fraction(value)


def _open_position_cost(position, evidence, config, *, session, observed, now):
    from .native_initial_margin_v1 import _select_xperp_position_tier

    native = position["instId"]
    family = native.rsplit("-", 1)[0]
    signed = _venue_decimal(position["pos"])
    if (
        position.get("instType") != "FUTURES"
        or position.get("mgnMode") != "cross"
        or position.get("posSide") != "net"
        or position.get("ccy") != "USDC"
        or signed == 0
        or signed != Fraction(evidence["signed_quantity"])
        or not re.fullmatch("[0-9a-f]{64}", evidence["reconciliation_identity_digest"])
    ):
        raise ValueError("XPERP_LIQUIDATION_OPEN_POSITION_SCOPE_UNPROVEN")
    sources = evidence["sources"]
    if set(sources) != {"instrument", "fees", "tiers"}:
        raise ValueError("XPERP_LIQUIDATION_OPEN_TERMS_REQUIRED")
    terms = {}
    for key, endpoint, query, private in (
        (
            "instrument",
            "/api/v5/account/instruments",
            {"instType": ["FUTURES"], "instId": [native]},
            True,
        ),
        (
            "fees",
            "/api/v5/account/trade-fee",
            {"instType": ["FUTURES"], "instFamily": [family]},
            True,
        ),
        (
            "tiers",
            "/api/v5/public/position-tiers",
            {"instType": ["FUTURES"], "tdMode": ["cross"], "instFamily": [family]},
            False,
        ),
    ):
        result = cost.FreshPretradeGetTransportResultV1(**sources[key])
        if (
            result.method != "GET"
            or result.get_performed is not True
            or result.auth_header_sent is not private
            or result.venue_live_contact is not True
            or result.historical_reuse is not False
            or result.http_status != 200
            or result.error_class
            or result.pretrade_decision_id != session
            or not re.fullmatch("[0-9a-f]{64}", result.body_sha256 or "")
            or cost._query(result.endpoint, endpoint) != query
        ):
            raise ValueError("XPERP_LIQUIDATION_OPEN_TERMS_GET_INVALID")
        cost.acquisition_age_seconds_v1(acquired_at_utc=result.acquired_at_utc, now_utc=observed)
        cost.acquisition_age_seconds_v1(acquired_at_utc=result.acquired_at_utc, now_utc=now)
        terms[key] = result
    instrument = cost._one(cost._rows(terms["instrument"].payload), "instId", native)
    if (
        cost._instrument_source_path_v1(terms["instrument"], instrument, config)
        != "/api/v5/account/instruments"
        or instrument["instFamily"] != family
    ):
        raise ValueError("XPERP_LIQUIDATION_OPEN_INSTRUMENT_SCOPE_UNPROVEN")
    fees = cost._rows(terms["fees"].payload)
    if len(fees) != 1 or fees[0].get("instType") != "FUTURES":
        raise ValueError("XPERP_LIQUIDATION_OPEN_FEE_SCOPE_UNPROVEN")
    cost._event_clock(fees[0].get("ts"), terms["fees"].acquired_at_utc, now)
    taker = -_venue_decimal(
        cost._one(fees[0]["feeGroup"], "groupId", instrument["groupId"])["taker"]
    )
    _, _, _, maintenance = _select_xperp_position_tier(
        terms["tiers"].payload, instrument, abs(signed)
    )
    combined_rate = taker + Fraction(maintenance)
    units = abs(signed) * _venue_decimal(instrument["ctVal"]) * _venue_decimal(instrument["ctMult"])
    mark, stop = _venue_decimal(position["markPx"]), Fraction(evidence["stop"])
    direction = 1 if signed > 0 else -1
    closing, funding = Fraction(evidence["closing"]), Fraction(evidence["funding"])
    if min(units, mark, stop) <= 0 or min(taker, closing, funding) < 0 or combined_rate >= 1:
        raise ValueError("XPERP_LIQUIDATION_OPEN_TERMS_NUMERIC_DOMAIN")
    if direction * (mark - stop) <= 0:
        raise ValueError("XPERP_LIQUIDATION_OPEN_PROTECTIVE_STOP_REACHED")
    # Cross equity already includes current UPL. Charge only its adverse change
    # and the maximum margin-and-fee burden over the interval to the stop.
    current = units * mark * combined_rate
    stressed = units * stop * combined_rate - direction * units * (stop - mark)
    return family, max(current, stressed) + closing + funding


def assess_xperp_liquidation_v1(snapshot, *, sizing, evaluated_at_utc=None):
    """Evaluate the original stop against the venue's maintenance boundary."""
    margin, costs = original_costs_v1(
        replace(sizing, xperp_liquidation_binding=None, absolute_movement_cost_binding=None)
    )
    opening = json.loads(sizing.entry_cost_binding.receipt_json)
    component = margin.get("xperp_position_maintenance")
    if (
        component is None
        or margin["settlement_currency"] != "USDC"
        or opening["side"] not in {"LONG", "SHORT"}
    ):
        raise ValueError("XPERP_LIQUIDATION_ORIGINAL_USDC_TIER_REQUIRED")
    now = evaluated_at_utc or snapshot["evaluated_at_utc"]
    cross, config, positions, session = _account_basis(
        snapshot, margin["account_identity"], margin["available_native"], now
    )
    families = {component["instrument_family"]}
    other_cost = Fraction(0)
    for position in positions:
        family, requirement = _open_position_cost(
            position,
            snapshot["open_positions"][position["instId"]],
            config,
            session=session,
            observed=snapshot["evaluated_at_utc"],
            now=now,
        )
        if family in families:
            raise ValueError("XPERP_LIQUIDATION_SHARED_FAMILY_TIER_UNPROVEN")
        families.add(family)
        other_cost += requirement
    mark = Fraction(sizing.monetary_source.native_reference_price)
    stop = Fraction(sizing.monetary_source.native_protective_stop_price)
    quantity = Fraction(sizing.decision.final_quantity)
    units = quantity * Fraction(sizing.applied_input.instrument.contract_multiplier)
    direction = 1 if opening["side"] == "LONG" else -1
    if direction * (mark - stop) <= 0:
        raise ValueError("XPERP_LIQUIDATION_ADVERSE_STOP_REQUIRED")
    maintenance_rate = Fraction(component["maintenance_rate"])
    taker = -Fraction(opening["taker_rate"])
    if taker < 0 or maintenance_rate + taker >= 1:
        raise ValueError("XPERP_LIQUIDATION_FEE_RATE_UNPROVEN")
    requirement_rate = maintenance_rate + taker
    equity_at_mark = cross - other_cost - costs["opening"] - costs["closing"] - costs["funding"]
    surplus_at_mark = equity_at_mark - units * mark * requirement_rate
    surplus_at_stop = (
        equity_at_mark + direction * units * (stop - mark) - units * stop * requirement_rate
    )
    if min(surplus_at_mark, surplus_at_stop) <= 0:
        raise ValueError("XPERP_LIQUIDATION_BOUNDARY_REACHED_BEFORE_OR_AT_STOP")
    boundary = (direction * units * mark - equity_at_mark) / (
        units * (direction - requirement_rate)
    )
    body = dict(
        schema="xperp_liquidation_projection.v1",
        scope="DISTINCT_FAMILY_USDC_CROSS_MARK_TO_ORIGINAL_STOPS",
        decision_id=margin["decision_id"],
        native_id=margin["native_id"],
        quantity=margin["quantity"],
        side=opening["side"],
        cross_balance_usdc=str(cross),
        other_position_stress_and_cost_usdc=str(other_cost),
        maintenance_at_mark_usdc=str(units * mark * maintenance_rate),
        liquidation_fee_at_mark_usdc=str(units * mark * taker),
        surplus_at_stop_usdc=str(surplus_at_stop),
        positive_boundary_price=str(boundary) if boundary > 0 else None,
        distance_from_mark=str(abs(mark - boundary)) if boundary > 0 else None,
        custody_digest=digest(snapshot),
        native_margin_digest=margin["digest"],
        runtime_authorization_effect="NONE",
    )
    return {**body, "digest": digest(body)}


@dataclass(frozen=True)
class XPerpLiquidationBindingV1:
    custody_json: str
    receipt_json: str

    def validate_v1(self, *, sizing):
        snapshot = json.loads(self.custody_json)
        if snapshot.get("candidate_id") is not None:
            raise ValueError("XPERP_LIQUIDATION_ORIGINAL_PRE_RESERVE_CUSTODY_REQUIRED")
        if assess_xperp_liquidation_v1(snapshot, sizing=sizing) != json.loads(self.receipt_json):
            raise ValueError("XPERP_LIQUIDATION_RECEIPT_MISMATCH")

    def to_dict_v1(self):
        return dict(
            schema=_BINDING_SCHEMA,
            custody=json.loads(self.custody_json),
            receipt=json.loads(self.receipt_json),
        )

    @classmethod
    def from_dict_v1(cls, raw):
        if set(raw) != {"schema", "custody", "receipt"} or raw["schema"] != _BINDING_SCHEMA:
            raise ValueError("XPERP_LIQUIDATION_BINDING_SCHEMA_INVALID")
        return cls(canonical(raw["custody"]), canonical(raw["receipt"]))
