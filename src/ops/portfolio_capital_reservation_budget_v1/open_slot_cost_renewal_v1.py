"""Source-bound cost renewal inside the original budget owner's transaction.

Accounting remains the payment writer. Public history proves period coverage,
never an account cash amount. This adapter performs no network or order IO.
"""

from dataclasses import asdict, dataclass, fields, replace
from datetime import datetime
from decimal import Decimal, localcontext
import json
import re

from .durable_store_v1 import canonical, digest
from .entry_execution_cost_v1 import (
    FreshPretradeGetTransportResultV1,
    _money,
    _query,
    _rows,
    acquisition_age_seconds_v1,
    assess_current_open_slot_cost_v1,
    reserved_closing_cost_v1,
    reserved_funding_cost_v1,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.current_productive_29p_risk_capital_model_v1 import (
    CurrentProductive29PRiskCapitalOutputV1,
)


@dataclass(frozen=True)
class FundingSettlementAssignmentV1:
    funding_time_ms: int
    event_id: str
    amount: str
    currency: str
    instrument_id: str
    event_time_unix: float


@dataclass(frozen=True)
class OpenSlotCostRenewalContextV1:
    budget_sequence: int
    budget_digest: str
    capital_output_json: str
    settlements_json: str = "[]"
    history_sources_json: str = "[]"

    @classmethod
    def capture_v1(cls, *, owner, capital_output, settlements=(), history_sources=()):
        if (
            type(capital_output) is not CurrentProductive29PRiskCapitalOutputV1
            or any(type(v) is not FundingSettlementAssignmentV1 for v in settlements)
            or any(type(v) is not FreshPretradeGetTransportResultV1 for v in history_sources)
        ):
            raise ValueError("OPEN_SLOT_RENEWAL_ORIGINAL_TYPED_INPUTS_REQUIRED")
        # Snapshot only. The original owner checks this epoch again under its
        # lock before publishing reserves, capital and protection together.
        with owner._lock:
            if owner._store is None or owner._closed_owner or owner._storage_failed:
                raise ValueError("OPEN_SLOT_RENEWAL_ORIGINAL_STORE_REQUIRED")
            return cls(
                owner._store.sequence,
                owner._store.head,
                canonical(asdict(capital_output)),
                canonical([asdict(v) for v in settlements]),
                canonical([asdict(v) for v in history_sources]),
            )

    def to_dict_v1(self):
        return dict(schema="open_slot_cost_renewal_context.v1", **asdict(self))

    @classmethod
    def from_dict_v1(cls, raw):
        if (
            type(raw) is not dict
            or set(raw) != {"schema", *(f.name for f in fields(cls))}
            or raw["schema"] != "open_slot_cost_renewal_context.v1"
        ):
            raise ValueError("OPEN_SLOT_RENEWAL_CONTEXT_SCHEMA_INVALID")
        if (
            type(raw["budget_sequence"]) is not int
            or raw["budget_sequence"] <= 0
            or type(raw["budget_digest"]) is not str
            or not re.fullmatch("[0-9a-f]{64}", raw["budget_digest"])
            or any(
                type(raw[k]) is not str
                for k in ("capital_output_json", "settlements_json", "history_sources_json")
            )
        ):
            raise ValueError("OPEN_SLOT_RENEWAL_CONTEXT_BINDING_INVALID")
        return cls(**{k: v for k, v in raw.items() if k != "schema"})


def enabled(owner):
    return bool(
        owner._entry_budget_policy and owner._entry_budget_policy.renew_open_slot_cost_reserves
    )


def sum_money_v1(values, start=Decimal(0)):
    """Exact finite Decimal addition for the explicitly renewed hold ledger."""
    values = [start, *values]
    if not values:
        return Decimal(0)
    if any(not v.is_finite() for v in values):
        raise ValueError("OPEN_SLOT_RENEWAL_NONFINITE_HOLD")
    with localcontext() as context:
        context.prec = max(
            28,
            max(v.adjusted() for v in values)
            - min(v.as_tuple().exponent for v in values)
            + len(str(len(values)))
            + 2,
        )
        return sum(values, Decimal(0))


def effective_reserve_v1(owner, rid, ref=None):
    history = owner._open_slot_cost_reserves.get(rid, [])
    if ref is None:
        ref = history[-1]["digest"] if history else ""
    if ref:
        rows = [r for r in history if r["digest"] == ref]
        if len(rows) != 1:
            raise ValueError("OPEN_SLOT_RENEWAL_ORIGINAL_RESERVE_REFERENCE_REQUIRED")
        row = rows[0]
        return (
            Decimal(row["close_provision_usdc"]),
            Decimal(row["funding_provision_usdc"]),
            row["upcoming_funding_time_ms"],
        )
    binding = owner._sizing_bindings[rid]
    return (
        reserved_closing_cost_v1(binding),
        reserved_funding_cost_v1(binding),
        json.loads(binding.funding_cost_binding.receipt_json)["upcoming_funding_time_ms"],
    )


def bind_observation_locked_v1(owner, rid, observation):
    history = owner._open_slot_cost_reserves.get(rid, [])
    ref = history[-1]["digest"] if history else ""
    if observation.cost_reserve_ref and observation.cost_reserve_ref != ref:
        raise ValueError("OPEN_SLOT_RENEWAL_STALE_RESERVE_REFERENCE")
    return replace(observation, cost_reserve_ref=ref)


def _capital_v1(owner, context, observation, proof):
    from .contract_v1 import _producer_budget
    from .recovery_v1 import capital_scope_v1
    from src.ops.exit_policy_producer_binding_v1.position_episode_binding_v1 import (
        PositionEpisodeIdentityV1,
        PositionEpisodeScopeV1,
    )
    from src.ops.exit_policy_producer_binding_v1.simulated_accounting_progress_v1 import _source
    from src.ops.exit_policy_producer_binding_v1.simulated_accounting_entry_source_v1 import (
        latest_economic_event_time_v1,
    )

    raw = json.loads(context.capital_output_json)
    output = CurrentProductive29PRiskCapitalOutputV1(**raw)
    parsed = _producer_budget(output)
    if (
        parsed is None
        or output.bound_account_identity != owner._account_identity
        or capital_scope_v1(output) != owner._capital_scope
    ):
        raise ValueError("OPEN_SLOT_RENEWAL_ORIGINAL_CAPITAL_SCOPE_REQUIRED")
    identity = proof["identity"]
    episode = PositionEpisodeIdentityV1(
        **{**identity, "account_scope": PositionEpisodeScopeV1(**identity["account_scope"])}
    )
    payload, _ = _source(observation.current_source_ref, episode)
    latest_event = latest_economic_event_time_v1(payload)
    for epoch in (output.decision_epoch, output.observed_at_as_of):
        acquisition_age_seconds_v1(acquired_at_utc=epoch, now_utc=observation.valuation_epoch)
        if datetime.fromisoformat(epoch.replace("Z", "+00:00")).timestamp() < latest_event:
            raise ValueError("OPEN_SLOT_RENEWAL_CAPITAL_BEFORE_ACCOUNTING")
    return output, parsed


def _settlements_v1(owner, rid, observation, context, proof, old_horizon, new_horizon):
    from src.ops.exit_policy_producer_binding_v1.position_episode_binding_v1 import (
        PositionEpisodeIdentityV1,
        PositionEpisodeScopeV1,
    )
    from src.ops.exit_policy_producer_binding_v1.simulated_accounting_progress_v1 import _source

    assignments = [FundingSettlementAssignmentV1(**v) for v in json.loads(context.settlements_json)]
    pages = json.loads(context.history_sources_json)
    if new_horizon == old_horizon:
        if assignments or pages:
            raise ValueError("OPEN_SLOT_RENEWAL_UNEXPECTED_SETTLEMENT_INPUTS")
        return []
    now_ms = int(
        datetime.fromisoformat(observation.valuation_epoch.replace("Z", "+00:00")).timestamp()
        * 1000
    )
    if not old_horizon <= now_ms < new_horizon or not pages:
        raise ValueError("OPEN_SLOT_RENEWAL_SETTLEMENT_COVERAGE_REQUIRED")
    identity = proof["identity"]
    episode = PositionEpisodeIdentityV1(
        **{**identity, "account_scope": PositionEpisodeScopeV1(**identity["account_scope"])}
    )
    payload, anchors = _source(observation.current_source_ref, episode)
    initial, _ = _source(observation.initial_source_ref, episode)
    events = payload["accounting_checkpoint"]["funding_events"]
    native = identity["venue_native_id"]
    sources = json.loads(observation.cost_sources_json)
    acquisition_id = sources["funding"]["pretrade_decision_id"]
    kind = sources["funding"]["payload"]["data"][0]["instType"]
    times, after, complete = [], new_horizon, False
    # A bounded range with an exhausted last page proves all returned periods.
    # Pagination uses OKX's older-than `after`, with newer-than `before` fixed.
    for raw in pages:
        source = FreshPretradeGetTransportResultV1(**raw)
        if complete or (
            source.get_performed is not True
            or source.method != "GET"
            or source.http_status != 200
            or source.auth_header_sent is not False
            or source.historical_reuse is not False
            or source.error_class
            or source.pretrade_decision_id != acquisition_id
            or not re.fullmatch("[0-9a-f]{64}", source.body_sha256)
            or _query(source.endpoint, "/api/v5/public/funding-rate-history")
            != {
                "instId": [native],
                "before": [str(old_horizon - 1)],
                "after": [str(after)],
                "limit": ["400"],
            }
        ):
            raise ValueError("OPEN_SLOT_RENEWAL_HISTORY_GET_OR_RANGE_INVALID")
        acquisition_age_seconds_v1(
            acquired_at_utc=source.acquired_at_utc, now_utc=observation.valuation_epoch
        )
        rows = _rows(source.payload)
        if len(rows) > 400:
            raise ValueError("OPEN_SLOT_RENEWAL_HISTORY_PAGE_INVALID")
        page_times = []
        for row in rows:
            time = row.get("fundingTime")
            if (
                row.get("instId") != native
                or row.get("instType") != kind
                or type(time) is not str
                or not time.isdigit()
            ):
                raise ValueError("OPEN_SLOT_RENEWAL_HISTORY_PERIOD_INVALID")
            time = int(time)
            _money(row.get("realizedRate"))  # Rate evidence, never cash.
            if not old_horizon <= time < after or time > now_ms:
                raise ValueError("OPEN_SLOT_RENEWAL_HISTORY_PERIOD_OUTSIDE_RANGE")
            page_times.append(time)
        if any(a <= b for a, b in zip(page_times, page_times[1:])):
            raise ValueError("OPEN_SLOT_RENEWAL_HISTORY_ORDER_INVALID")
        times.extend(page_times)
        complete = len(rows) < 400
        if rows:
            after = page_times[-1]
    if not complete or not times or times[-1] != old_horizon:
        raise ValueError("OPEN_SLOT_RENEWAL_HISTORY_INCOMPLETE")
    if [v.funding_time_ms for v in assignments] != sorted(times) or len(
        {v.event_id for v in assignments}
    ) != len(assignments):
        raise ValueError("OPEN_SLOT_RENEWAL_PAYMENT_SEQUENCE_INCOMPLETE")
    expected_ids = {
        key
        for key, event in events.items()
        if old_horizon <= Decimal(str(event["event_time_unix"])) * 1000 < new_horizon
    }
    if {v.event_id for v in assignments} != expected_ids:
        raise ValueError("OPEN_SLOT_RENEWAL_UNASSIGNED_PERIOD_PAYMENT")
    used = {
        v["event_id"]
        for row in owner._open_slot_cost_reserves.get(rid, [])
        if row["digest"] != observation.cost_reserve_ref
        for v in row["settlements"]
        if v["funding_time_ms"] < old_horizon
    }
    retained = []
    for item in assignments:
        row = events.get(item.event_id)
        if (
            type(item.funding_time_ms) is not int
            or type(item.amount) is not str
            or row is None
            or item.event_id in used
            or item.event_id in initial["accounting_checkpoint"]["funding_events"]
            or item.currency != payload["accounting_checkpoint"]["contract"]["quote_currency"]
            or item.instrument_id != native
            or any(
                row.get(k) != getattr(item, k)
                for k in ("amount", "currency", "instrument_id", "event_time_unix")
            )
            or type(item.event_time_unix) not in (int, float)
            or Decimal(str(item.event_time_unix)) * 1000 != item.funding_time_ms
            or item.event_time_unix < anchors["entry_event_time"]
        ):
            raise ValueError("OPEN_SLOT_RENEWAL_ORIGINAL_PERIOD_PAYMENT_REQUIRED")
        _money(item.amount)  # Signed observed amount; explicit zero is allowed.
        retained.append({**asdict(item), "funding_sequence": row["funding_sequence"]})
    return retained


def assess_renewal_v1(owner, rid, observation, base):
    body = {k: v for k, v in base.items() if k != "digest"}
    body.update(
        schema="open_slot_loss_protection.v3",
        reserve_renewal=None,
        reserve_renewal_status="UNPROVEN_HELD_RESERVES_RETAINED",
        reserve_renewal_reasons=[],
    )
    old_close, old_funding, old_horizon = effective_reserve_v1(
        owner, rid, observation.cost_reserve_ref
    )
    body.update(
        held_close_provision_before_renewal_usdc=str(old_close),
        held_funding_provision_before_renewal_usdc=str(old_funding),
        held_upcoming_funding_time_ms=old_horizon,
        future_liability_basis="HELD_RESERVES_WITH_UNMAPPED_FUNDING_RETAINED",
    )
    try:
        sources = json.loads(observation.cost_sources_json)
        horizon = int(sources["funding"]["payload"]["data"][0]["fundingTime"])
        current = assess_current_open_slot_cost_v1(
            owner, rid, observation, body, funding_horizon_ms=horizon
        )
        current["total_future_cost_provision_usdc"] = str(
            sum_money_v1(
                Decimal(current[k]) for k in ("close_provision_usdc", "funding_provision_usdc")
            )
        )
        current["digest"] = digest({k: v for k, v in current.items() if k != "digest"})
        body.update(
            current_cost_provision=current, current_cost_status="OBSERVED_RENEWAL_CANDIDATE"
        )
        context = OpenSlotCostRenewalContextV1.from_dict_v1(
            json.loads(observation.renewal_context_json)
        )
        revision = owner._store.read_revision_v1(context.budget_sequence, context.budget_digest)
        prior = revision["state"]
        history = prior.get("open_slot_cost_reserves", {}).get(rid, [])
        ref = history[-1]["digest"] if history else ""
        if (
            ref != observation.cost_reserve_ref
            or prior.get("entry_budget_policy") != owner._entry_budget_policy.to_dict_v1()
            or prior["account_identity"] != owner._account_identity
            or not any(
                r["reservation_id"] == rid and r["state"] in {"RESERVED", "COMMITTED"}
                for r in prior["reservations"]
            )
        ):
            raise ValueError("OPEN_SLOT_RENEWAL_ORIGINAL_BUDGET_REVISION_MISMATCH")
        settlements = _settlements_v1(owner, rid, observation, context, body, old_horizon, horizon)
        output, (budget, observation_id) = _capital_v1(owner, context, observation, body)
        # Reconstruct obligations from the exact preceding original revision.
        from .sizing_binding_v1 import ReservationSizingBindingV1
        from .entry_execution_cost_v1 import reserved_opening_fee_v1

        operands = []
        for record in prior["reservations"]:
            if record["state"] not in {"RESERVED", "COMMITTED"}:
                continue
            key = record["reservation_id"]
            binding = ReservationSizingBindingV1.from_dict_v1(prior["sizing_bindings"][key])
            reserves = prior.get("open_slot_cost_reserves", {}).get(key, [])
            close = (
                Decimal(reserves[-1]["close_provision_usdc"])
                if reserves
                else reserved_closing_cost_v1(binding)
            )
            funding = (
                Decimal(reserves[-1]["funding_provision_usdc"])
                if reserves
                else reserved_funding_cost_v1(binding)
            )
            operands.extend(
                (Decimal(record["amount"]), reserved_opening_fee_v1(binding), close, funding)
            )
        held = sum_money_v1(operands)
        projected = sum_money_v1(
            (held, -old_close, -old_funding, Decimal(current["total_future_cost_provision_usdc"]))
        )
        allowance = Decimal(body["remaining_allowance_before_future_costs_usdc"])
        if projected > budget:
            body.update(
                close_required=True,
                reason="TEST_SLOT_RENEWED_CAPITAL_UNCOVERED",
                reserve_renewal_status="INSUFFICIENT_CAPITAL_HELD_RESERVES_RETAINED",
            )
        elif allowance <= Decimal(current["total_future_cost_provision_usdc"]):
            body.update(
                close_required=True,
                reason="TEST_SLOT_RENEWED_COST_PROVISIONS_UNCOVERED",
                reserve_renewal_status="INSUFFICIENT_LOSS_ALLOWANCE_HELD_RESERVES_RETAINED",
            )
        else:
            receipt = dict(
                schema="open_slot_cost_reserve_renewal.v1",
                reservation_id=rid,
                slot_id=body["slot_id"],
                observation=observation.to_dict_v1(),
                previous_reserve_ref=observation.cost_reserve_ref,
                close_provision_usdc=current["close_provision_usdc"],
                funding_provision_usdc=current["funding_provision_usdc"],
                upcoming_funding_time_ms=horizon,
                settlements=settlements,
                capital_output=asdict(output),
                capital_observation_id=observation_id,
                held_before_usdc=str(held),
                held_after_usdc=str(projected),
                cost_provision_digest=current["digest"],
                runtime_authorization_effect="NONE",
            )
            receipt = json.loads(canonical(receipt))
            receipt["digest"] = digest(receipt)
            body.update(
                reserve_renewal=receipt,
                reserve_renewal_status="RENEWAL_ADMITTED",
                funding_or_cost_rollover_admitted=True,
                future_liability_basis="RENEWED_RESERVES_PAYMENT_ALREADY_IN_ORIGINAL_ACCOUNTING",
            )
            # Proven payments are already part of native_result. Only future
            # obligations remain here, with no second debit of settled money.
            if not body["actual_loss_allowance_exhausted"]:
                body.update(close_required=False, reason="NO_OBSERVED_LOSS_CLOSE_TRIGGER")
    except (ValueError, TypeError, KeyError, AttributeError, ArithmeticError) as exc:
        body["reserve_renewal_reasons"] = [str(exc)]
    if body["reserve_renewal_status"] != "RENEWAL_ADMITTED":
        current = body.get("current_cost_provision")
        # Unmapped old funding must survive even after its clock has passed.
        required = old_close + old_funding
        if current:
            new_funding = Decimal(current["funding_provision_usdc"])
            funding = (
                old_funding + new_funding
                if current["upcoming_funding_time_ms"] != old_horizon
                else max(old_funding, new_funding)
            )
            required = max(old_close, Decimal(current["close_provision_usdc"])) + funding
        if (
            Decimal(body["remaining_allowance_before_future_costs_usdc"]) <= required
            and not body["close_required"]
        ):
            body.update(
                close_required=True, reason="TEST_SLOT_UNRESOLVED_COST_PROVISIONS_UNCOVERED"
            )
    return {**body, "digest": digest(body)}


def apply_renewal_locked_v1(owner, rid, proof):
    receipt = proof["reserve_renewal"]
    if receipt is None:
        return
    context = OpenSlotCostRenewalContextV1.from_dict_v1(
        json.loads(proof["observation"]["renewal_context_json"])
    )
    if (context.budget_sequence, context.budget_digest) != (
        owner._store.sequence,
        owner._store.head,
    ):
        raise ValueError("OPEN_SLOT_RENEWAL_BUDGET_EPOCH_CHANGED")
    if not owner._admitted or owner._recovery_required:
        raise ValueError("OPEN_SLOT_RENEWAL_ORIGINAL_RECOVERY_REQUIRED")
    if owner._held_capital_locked() != Decimal(receipt["held_before_usdc"]):
        raise ValueError("OPEN_SLOT_RENEWAL_HELD_CAPITAL_CHANGED")
    owner._open_slot_cost_reserves.setdefault(rid, []).append(receipt)
    owner._budget = Decimal(receipt["capital_output"]["value"])
    owner._observation_id = receipt["capital_observation_id"]


def restore_reserves_v1(owner, raw):
    if not enabled(owner):
        if raw is not None:
            raise ValueError("OPEN_SLOT_RENEWAL_OUTSIDE_EXPLICIT_POLICY")
        return {}
    if type(raw) is not dict or set(raw) - set(owner._sizing_bindings):
        raise ValueError("OPEN_SLOT_RENEWAL_STATE_REQUIRED")
    from .entry_execution_cost_v1 import OpenSlotLossObservationV1, assess_open_slot_loss_v1

    owner._open_slot_cost_reserves = {}
    for rid, history in raw.items():
        if type(history) is not list or not history:
            raise ValueError("OPEN_SLOT_RENEWAL_HISTORY_REQUIRED")
        for receipt in history:
            observation = OpenSlotLossObservationV1.from_dict_v1(receipt["observation"])
            rebuilt = assess_open_slot_loss_v1(owner, rid, observation)
            if rebuilt.get("reserve_renewal") != receipt:
                raise ValueError("OPEN_SLOT_RENEWAL_SOURCE_OR_SUMMARY_MISMATCH")
            owner._open_slot_cost_reserves.setdefault(rid, []).append(
                json.loads(canonical(receipt))
            )
    return owner._open_slot_cost_reserves


def entry_blocker_locked_v1(owner):
    if not enabled(owner):
        return None
    from .entry_execution_cost_v1 import utc_now_iso_v1

    now = datetime.fromisoformat(utc_now_iso_v1().replace("Z", "+00:00")).timestamp() * 1000
    for rid, record in owner._by_key.items():
        if not record.counts_against_budget:
            continue
        if now >= effective_reserve_v1(owner, rid)[2]:
            return "OPEN_SLOT_COST_RESERVES_EXPIRED_RENEWAL_REQUIRED"
        row = owner._open_slot_protection.get(str(record.slot_id))
        if (
            row
            and row["latest"]["reservation_id"] == rid
            and row["latest"].get("reserve_renewal_status") != "RENEWAL_ADMITTED"
        ):
            return "OPEN_SLOT_COST_RESERVE_RENEWAL_UNPROVEN"
    return None
