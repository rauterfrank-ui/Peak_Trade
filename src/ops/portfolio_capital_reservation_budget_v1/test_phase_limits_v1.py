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

    def to_dict_v1(self):
        result = super().to_dict_v1()
        return {
            **result,
            "schema": "entry_budget_policy.v2",
            "per_slot_reserved_notional_limit": str(self.per_slot_reserved_notional_limit),
            "allowed_slot_ids": list(self.allowed_slot_ids),
        }


def parse_slot_entry_budget_v1(payload):
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
    if (
        not isinstance(payload, dict)
        or set(payload) != expected
        or payload["schema"] != "entry_budget_policy.v2"
    ):
        raise EntryBudgetPolicyError("ENTRY_BUDGET_SLOT_SCHEMA_INVALID")
    data = dict(payload)
    data.pop("schema")
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
