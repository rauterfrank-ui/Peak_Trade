"""Test-phase close accounting and loss allowance at the reservation owner.

No independent balance, PnL kernel, reserve top-up or instrument selection.
Every amount is reread from an original sealed accounting source and its held
monetary provenance. Exhaustion is latched for this explicit test policy.
"""

from dataclasses import asdict, dataclass
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
        if policy is not None
        else {}
    )


def _summary(records, limit):
    net, stopped = Decimal(0), False
    for record in records:
        net += Decimal(record["net_result_usdc"])
        if limit is not None:
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


@dataclass(frozen=True)
class SlotCapitalAllocationV1:
    """Explicit initial capital allocation for the bounded simulation."""

    account_identity: str
    source_ref: str
    initial_usdc_by_slot: tuple[tuple[str, Decimal], ...]

    def to_dict_v1(self):
        for value in (self.account_identity, self.source_ref):
            if type(value) is not str or not value or value != value.strip():
                raise ValueError("SLOT_CAPITAL_ALLOCATION_SOURCE_UNPROVEN")
        if type(self.initial_usdc_by_slot) is not tuple or not self.initial_usdc_by_slot:
            raise ValueError("SLOT_CAPITAL_ALLOCATION_AMOUNTS_REQUIRED")
        amounts = {}
        for slot_id, amount in self.initial_usdc_by_slot:
            if (
                type(slot_id) is not str
                or not slot_id
                or slot_id in amounts
                or type(amount) is not Decimal
                or not amount.is_finite()
                or amount <= 0
            ):
                raise ValueError("SLOT_CAPITAL_ALLOCATION_AMOUNTS_INVALID")
            amounts[slot_id] = str(amount)
        return {
            "account_identity": self.account_identity,
            "source_ref": self.source_ref,
            "initial_usdc_by_slot": amounts,
        }

    @classmethod
    def from_dict_v1(cls, value):
        if not isinstance(value, dict) or set(value) != {
            "account_identity",
            "source_ref",
            "initial_usdc_by_slot",
        }:
            raise ValueError("SLOT_CAPITAL_ALLOCATION_STATE_INVALID")
        allocation = cls(
            value["account_identity"],
            value["source_ref"],
            tuple(
                (slot, Decimal(amount)) for slot, amount in value["initial_usdc_by_slot"].items()
            ),
        )
        if allocation.to_dict_v1() != value:
            raise ValueError("SLOT_CAPITAL_ALLOCATION_STATE_INVALID")
        return allocation


@dataclass(frozen=True)
class SlotCapitalBasisV1:
    slot_id: str
    account_identity: str
    initial_usdc: Decimal
    booked_net_usdc: Decimal
    allocation_digest: str
    funding_observation_id: str
    latest_booking_digest: str | None

    @property
    def net_basis_usdc(self) -> Decimal:
        return self.initial_usdc + self.booked_net_usdc

    def to_dict(self):
        return {
            "slot_id": self.slot_id,
            "account_identity": self.account_identity,
            "initial_usdc": str(self.initial_usdc),
            "booked_net_usdc": str(self.booked_net_usdc),
            "net_basis_usdc": str(self.net_basis_usdc),
            "allocation_digest": self.allocation_digest,
            "funding_observation_id": self.funding_observation_id,
            "latest_booking_digest": self.latest_booking_digest,
        }


@dataclass(frozen=True)
class SlotCloseNetBookingV1:
    episode_id: str
    reservation_id: str
    episode_net_usdc: Decimal
    slot_booked_net_usdc: Decimal
    booking_digest: str

    def to_dict(self):
        return {
            "episode_id": self.episode_id,
            "reservation_id": self.reservation_id,
            "episode_net_usdc": str(self.episode_net_usdc),
            "slot_booked_net_usdc": str(self.slot_booked_net_usdc),
            "booking_digest": self.booking_digest,
        }


def _net_booking(record, net):
    return SlotCloseNetBookingV1(
        episode_id=record["episode_id"],
        reservation_id=record["reservation_id"],
        episode_net_usdc=Decimal(record["net_result_usdc"]),
        slot_booked_net_usdc=Decimal(net),
        booking_digest=record["digest"],
    )


def requires_close_accounting(owner, slot_id):
    allocation = owner._slot_capital_allocation
    return enabled(owner._entry_budget_policy) or (
        allocation is not None and slot_id in allocation["declaration"]["initial_usdc_by_slot"]
    )


def build_record(owner, *, reservation_id, source, close_envelope, l10_scope=None):
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
        if l10_scope is not None:
            from src.ops.full_core_live_path_composition_root_v1.current_productive_position_management_quantity_handoff_v1 import (
                occupied_l10_close_from_binding_v1,
            )

            switch = occupied_l10_close_from_binding_v1(l10_scope)
            if (
                type(source) is not SlotCloseAccountingSourceV1
                or source.identity_v1() != switch.episode
                or switch.admission_ref_v1() != close_envelope["admission_ref"]
            ):
                raise ValueError("TEST_SLOT_L10_ACCOUNTING_EPISODE_MISMATCH")
        elif not requires_close_accounting(owner, str(record.slot_id)):
            raise ValueError("TEST_SLOT_L10_CLOSE_PROOF_REQUIRED")
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
    record = {"reservation_id": reservation_id, **result}
    if l10_scope is not None:
        record["l10_scope"] = {
            "position_episode": asdict(switch.episode),
            "scope_digest": switch.scope_digest,
            "scope_seal_id": switch.scope_seal_id,
        }
    return record


def restore_state(owner, raw):
    policy = owner._entry_budget_policy
    if policy is None:
        if raw is not None:
            raise ValueError("TEST_SLOT_LOSS_STATE_OUTSIDE_TEST_POLICY")
        return {}
    if raw is None and not enabled(policy):
        return empty_state(policy)
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
                l10_scope=record.get("l10_scope"),
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
    policy = owner._entry_budget_policy
    switch = request.execution.l10_close
    slot_id = request.execution.source.quantity_handoff.lane_id
    if policy is None or (switch is None and not requires_close_accounting(owner, slot_id)):
        raise ValueError("TEST_SLOT_CLOSE_ACCOUNTING_POLICY_REQUIRED")
    if request.budget_owner is not owner or len(request.closed_reservation_ids) != 1:
        raise ValueError("TEST_SLOT_ORIGINAL_CLOSE_REQUEST_REQUIRED")
    source = request.slot_accounting_source
    if (
        type(source) is not SlotCloseAccountingSourceV1
        or source.valuation_epoch != request.observed_at_utc
    ):
        raise ValueError("TEST_SLOT_CLOSE_ACCOUNTING_SOURCE_REQUIRED")
    rid = request.closed_reservation_ids[0]
    result = build_record(
        owner,
        reservation_id=rid,
        source=source,
        close_envelope=request.execution.envelope.to_runtime_json_v1(),
        l10_scope=(
            None
            if switch is None
            else {
                "position_episode": asdict(switch.episode),
                "scope_digest": switch.scope_digest,
                "scope_seal_id": switch.scope_seal_id,
            }
        ),
    )
    slot = result["slot_id"]
    state = owner._slot_test_economics[slot]
    for index, prior in enumerate(state["records"]):
        if prior["reservation_id"] == rid:
            if prior != result:
                raise ValueError("TEST_SLOT_ECONOMIC_CLOSE_REPLAY_CONFLICT")
            net, _ = _summary(state["records"][: index + 1], policy.per_slot_test_loss_limit)
            return False, _net_booking(prior, net)
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
    net, exhausted = _summary(rows, policy.per_slot_test_loss_limit)
    owner._slot_test_economics[slot] = dict(records=rows, net_result_usdc=net, exhausted=exhausted)
    return True, _net_booking(result, net)
