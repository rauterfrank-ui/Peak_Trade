"""Explicit slot-budget extension of the unchanged original outer entry policy.

No independent capital/sizing owner or automatic phase transition. Only the
original reservation owner stores this immutable policy alongside its holds.
"""

from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
import json

from src.ops.full_core_live_path_composition_root_v1.current_productive_entry_budget_policy_v1 import (
    EntryBudgetPolicyV1,
    EntryBudgetPolicyError,
)
from src.ops.current_mf_n5_isolated_lane_instance_topology_v1.constants_v1 import LANE_IDS


@dataclass(frozen=True, kw_only=True)
class BoundedSlotEntryBudgetV1(EntryBudgetPolicyV1):
    per_slot_reserved_notional_limit: Decimal
    allowed_slot_ids: tuple[str, ...]
    per_slot_test_loss_limit: Decimal | None = None
    require_opening_execution_costs: bool = False

    def validate_v1(self):
        super().validate_v1()
        limit, slots = self.per_slot_reserved_notional_limit, self.allowed_slot_ids
        if (
            not isinstance(limit, Decimal)
            or not limit.is_finite()
            or limit <= 0
            or not isinstance(slots, tuple)
            or not slots
            or any(type(slot) is not str or slot not in LANE_IDS for slot in slots)
            or len(set(slots)) != len(slots)
            or self.per_entry_notional_limit > limit
            or self.aggregate_reserved_notional_limit > limit * len(slots)
        ):
            raise EntryBudgetPolicyError("ENTRY_BUDGET_SLOT_POLICY_INVALID")
        if self.per_slot_test_loss_limit is not None and (
            type(self.per_slot_test_loss_limit) is not Decimal
            or not self.per_slot_test_loss_limit.is_finite()
            or self.per_slot_test_loss_limit != Decimal("25")
        ):
            raise EntryBudgetPolicyError("TEST_PHASE_SLOT_LOSS_LIMIT_MUST_BE_25_USDC")
        if (
            type(self.require_opening_execution_costs) is not bool
            or self.require_opening_execution_costs
            and self.per_slot_test_loss_limit is None
        ):
            raise EntryBudgetPolicyError("TEST_PHASE_OPENING_COST_POLICY_INVALID")

    def to_dict_v1(self):
        result = super().to_dict_v1()
        result = {
            **result,
            "schema": "entry_budget_policy.v2",
            "per_slot_reserved_notional_limit": str(self.per_slot_reserved_notional_limit),
            "allowed_slot_ids": list(self.allowed_slot_ids),
        }
        if self.per_slot_test_loss_limit is not None:
            result.update(
                schema="entry_budget_policy.v3",
                per_slot_test_loss_limit=str(self.per_slot_test_loss_limit),
                loss_limit_scope="EXPLICIT_TEST_PHASE_ONLY",
                automatic_loss_budget_refill_allowed=False,
            )
        if self.require_opening_execution_costs:
            result.update(schema="entry_budget_policy.v4", require_opening_execution_costs=True)
        return result


def parse_slot_entry_budget_v1(payload):
    cost_mode = isinstance(payload, dict) and payload.get("schema") == "entry_budget_policy.v4"
    loss_mode = isinstance(payload, dict) and payload.get("schema") in {
        "entry_budget_policy.v3",
        "entry_budget_policy.v4",
    }
    expected = {
        "schema",
        "policy_id",
        "revision",
        "currency",
        "per_entry_notional_limit",
        "aggregate_reserved_notional_limit",
        "automatic_increase_allowed",
        "expiry",
        "per_slot_reserved_notional_limit",
        "allowed_slot_ids",
    }
    if loss_mode:
        expected |= {
            "per_slot_test_loss_limit",
            "loss_limit_scope",
            "automatic_loss_budget_refill_allowed",
        }
    if cost_mode:
        expected.add("require_opening_execution_costs")
    if (
        not isinstance(payload, dict)
        or set(payload) != expected
        or payload["schema"]
        not in {"entry_budget_policy.v2", "entry_budget_policy.v3", "entry_budget_policy.v4"}
    ):
        raise EntryBudgetPolicyError("ENTRY_BUDGET_SLOT_SCHEMA_INVALID")
    data = dict(payload)
    data.pop("schema")
    if cost_mode and data.get("require_opening_execution_costs") is not True:
        raise EntryBudgetPolicyError("TEST_PHASE_OPENING_COST_POLICY_INVALID")
    if loss_mode:
        if (
            data.pop("loss_limit_scope") != "EXPLICIT_TEST_PHASE_ONLY"
            or data.pop("automatic_loss_budget_refill_allowed") is not False
            or type(data["per_slot_test_loss_limit"]) is not str
        ):
            raise EntryBudgetPolicyError("TEST_PHASE_SLOT_LOSS_POLICY_INVALID")
        data["per_slot_test_loss_limit"] = Decimal(data["per_slot_test_loss_limit"])
    for name in (
        "per_entry_notional_limit",
        "aggregate_reserved_notional_limit",
        "per_slot_reserved_notional_limit",
    ):
        if type(data[name]) is not str:
            raise EntryBudgetPolicyError("ENTRY_BUDGET_POLICY_DECIMAL_STRING_REQUIRED")
        data[name] = Decimal(data[name])
    if type(data["allowed_slot_ids"]) is not list:
        raise EntryBudgetPolicyError("ENTRY_BUDGET_SLOT_ARRAY_REQUIRED")
    data["allowed_slot_ids"] = tuple(data["allowed_slot_ids"])
    policy = BoundedSlotEntryBudgetV1(**data)
    policy.validate_v1()
    return policy


def load_slot_entry_budget_v1(path):
    try:
        return parse_slot_entry_budget_v1(json.loads(path.read_text()))
    except (OSError, ValueError, TypeError, KeyError, InvalidOperation) as exc:
        raise EntryBudgetPolicyError("ENTRY_BUDGET_SLOT_POLICY_UNAVAILABLE_OR_INVALID") from exc


@dataclass(frozen=True)
class BoundedSlotReconciliationScopeV1:
    """Explicit simulated inventory scope; exact MATCH only, no repair grant."""

    policy: BoundedSlotEntryBudgetV1
    bindings: tuple
    execution_environment: str

    def known_instruments_v1(self):
        from .recovery_v1 import lane_bindings_v1

        if (
            type(self.policy) is not BoundedSlotEntryBudgetV1
            or self.execution_environment != "INTERNAL_SIMULATED_EXECUTION"
            or type(self.bindings) is not tuple
        ):
            raise ValueError("BOUNDED_RECONCILIATION_SCOPE_INVALID")
        self.policy.validate_v1()
        bindings = dict(self.bindings)
        if (
            len(bindings) != len(self.bindings)
            or not bindings
            or set(bindings) - set(self.policy.allowed_slot_ids)
        ):
            raise ValueError("BOUNDED_RECONCILIATION_SCOPE_INVALID")
        rows = lane_bindings_v1(bindings)
        return frozenset(row["bound"]["instrument_id"] for row in rows.values())
