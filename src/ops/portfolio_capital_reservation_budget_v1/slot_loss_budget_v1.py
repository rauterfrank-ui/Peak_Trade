"""Test-phase loss allowance within the original reservation owner's state.

No independent balance, PnL kernel, reserve top-up or instrument selection.
Every amount is reread from an original sealed accounting source and its held
monetary provenance. Exhaustion is latched for this explicit test policy.
"""

from decimal import Decimal
from datetime import datetime
import json

from .slot_economic_source_v1 import SlotCloseAccountingSourceV1, read_closed_slot_economics_v1
from src.ops.governed_productive_monetary_normalization_v1.contracts_v1 import (
    MonetaryNormalizationError,
)
from src.ops.exit_policy_producer_binding_v1.persistence_v1 import ExitPolicyPersistenceError


def enabled(policy):
    return policy is not None and policy.per_slot_test_loss_limit is not None


def empty_state(policy):
    return (
        {
            slot: {"records": [], "net_result_usdc": "0", "exhausted": False}
            for slot in policy.allowed_slot_ids
        }
        if enabled(policy)
        else {}
    )


def _summary(records, limit):
    net, stopped = Decimal(0), False
    for record in records:
        net += Decimal(record["net_result_usdc"])
        stopped |= limit + net <= 0
    return str(net), stopped


def admission_reason(owner, slot):
    policy = owner._entry_budget_policy
    if not enabled(policy):
        return None
    state = owner._slot_test_economics.get(slot)
    if state is None:
        return "TEST_SLOT_LOSS_STATE_MISSING"
    known = {record["reservation_id"] for record in state["records"]}
    for record in owner._by_key.values():
        if (
            str(record.slot_id) == slot
            and record.terminal_reason == "RECONCILED_POSITION_FLAT"
            and str(record.reservation_id) not in known
        ):
            return "TEST_SLOT_CLOSED_ECONOMICS_NOT_RECONCILED"
    if state["exhausted"]:
        return "TEST_SLOT_25_USDC_LOSS_BUDGET_EXHAUSTED"
    return None


def remaining_loss(owner, slot):
    state = owner._slot_test_economics[slot]
    if state["exhausted"]:
        return Decimal(0)
    limit = owner._entry_budget_policy.per_slot_test_loss_limit
    return max(Decimal(0), min(limit, limit + Decimal(state["net_result_usdc"])))


def build_record(owner, *, reservation_id, source, close_envelope):
    record = owner._by_key.get(owner._by_id.get(reservation_id))
    binding = owner._sizing_bindings.get(reservation_id)
    entry = owner._execution_links.get(reservation_id)
    if (
        record is None
        or binding is None
        or entry is None
        or record.terminal_reason != "RECONCILED_POSITION_FLAT"
        or binding.monetary_source is None
    ):
        raise ValueError("TEST_SLOT_ORIGINAL_CLOSED_RESERVATION_SOURCE_REQUIRED")
    binding.validate_v1(amount=record.amount, decision_id=record.decision_id)
    bound = owner._reservation_bindings[reservation_id]["bound"]
    try:
        result = read_closed_slot_economics_v1(
            source,
            monetary_source=binding.monetary_source,
            entry_envelope=entry["envelope"],
            close_envelope=close_envelope,
            slot_id=str(record.slot_id),
            account_identity=owner._account_identity,
            canonical_id=bound["instrument_id"],
            native_id=bound["venue_native_id"],
        )
    except (
        OSError,
        ValueError,
        TypeError,
        KeyError,
        AttributeError,
        ArithmeticError,
        MonetaryNormalizationError,
        ExitPolicyPersistenceError,
    ) as exc:
        raise ValueError("TEST_SLOT_ORIGINAL_ECONOMICS_SOURCE_UNPROVEN:" + str(exc)) from exc
    return {"reservation_id": reservation_id, **result}


def restore_state(owner, raw):
    policy = owner._entry_budget_policy
    if not enabled(policy):
        if raw is not None:
            raise ValueError("TEST_SLOT_LOSS_STATE_OUTSIDE_TEST_POLICY")
        return {}
    if not isinstance(raw, dict) or set(raw) != set(policy.allowed_slot_ids):
        raise ValueError("TEST_SLOT_LOSS_STATE_MISSING_OR_SCOPE_MISMATCH")
    ids, episodes = set(), set()
    for slot, state in raw.items():
        if (
            not isinstance(state, dict)
            or set(state) != {"records", "net_result_usdc", "exhausted"}
            or type(state["exhausted"]) is not bool
            or type(state["net_result_usdc"]) is not str
            or not isinstance(state["records"], list)
        ):
            raise ValueError("TEST_SLOT_LOSS_STATE_INVALID")
        last_epoch = None
        for record in state["records"]:
            rid = record["reservation_id"]
            rebuilt = build_record(
                owner,
                reservation_id=rid,
                source=SlotCloseAccountingSourceV1.from_dict_v1(record["source"]),
                close_envelope=record["close_envelope"],
            )
            epoch = datetime.fromisoformat(record["valuation_epoch"].replace("Z", "+00:00"))
            if (
                record != rebuilt
                or record["slot_id"] != slot
                or rid in ids
                or record["episode_id"] in episodes
                or last_epoch is not None
                and epoch < last_epoch
            ):
                raise ValueError("TEST_SLOT_LOSS_SOURCE_OR_SEQUENCE_MISMATCH")
            ids.add(rid)
            episodes.add(record["episode_id"])
            last_epoch = epoch
        if (state["net_result_usdc"], state["exhausted"]) != _summary(
            state["records"], policy.per_slot_test_loss_limit
        ):
            raise ValueError("TEST_SLOT_LOSS_SUMMARY_MISMATCH")
    return json.loads(json.dumps(raw, allow_nan=False))


def record_closed_locked(owner, request):
    if not enabled(owner._entry_budget_policy):
        raise ValueError("TEST_SLOT_LOSS_POLICY_REQUIRED")
    if request.budget_owner is not owner or len(request.closed_reservation_ids) != 1:
        raise ValueError("TEST_SLOT_ORIGINAL_CLOSE_REQUEST_REQUIRED")
    source = request.slot_accounting_source
    if source is None or source.valuation_epoch != request.observed_at_utc:
        raise ValueError("TEST_SLOT_CLOSE_ACCOUNTING_SOURCE_REQUIRED")
    rid = request.closed_reservation_ids[0]
    result = build_record(
        owner,
        reservation_id=rid,
        source=source,
        close_envelope=request.execution.envelope.to_runtime_json_v1(),
    )
    slot = result["slot_id"]
    state = owner._slot_test_economics[slot]
    prior = next((r for r in state["records"] if r["reservation_id"] == rid), None)
    if prior is not None:
        if prior != result:
            raise ValueError("TEST_SLOT_ECONOMIC_CLOSE_REPLAY_CONFLICT")
        return False
    if any(
        result["episode_id"] == r["episode_id"]
        for s in owner._slot_test_economics.values()
        for r in s["records"]
    ):
        raise ValueError("TEST_SLOT_EPISODE_ALREADY_ACCOUNTED")
    if state["records"] and (
        datetime.fromisoformat(result["valuation_epoch"].replace("Z", "+00:00"))
        < datetime.fromisoformat(state["records"][-1]["valuation_epoch"].replace("Z", "+00:00"))
    ):
        raise ValueError("TEST_SLOT_ECONOMIC_TIME_REGRESSION")
    rows = [*state["records"], result]
    net, exhausted = _summary(rows, owner._entry_budget_policy.per_slot_test_loss_limit)
    owner._slot_test_economics[slot] = dict(records=rows, net_result_usdc=net, exhausted=exhausted)
    return True
