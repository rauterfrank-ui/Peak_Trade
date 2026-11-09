"""Explicit slot-budget extension of the unchanged original outer entry policy.

No independent capital/sizing owner or automatic phase transition. Only the
original reservation owner stores this immutable policy alongside its holds.
"""

from dataclasses import dataclass, replace
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
    require_closing_execution_costs: bool = False
    require_next_funding_costs: bool = False
    enforce_open_slot_loss_protection: bool = False
    refresh_open_slot_cost_protection: bool = False
    renew_open_slot_cost_reserves: bool = False
    require_native_initial_margin: bool = False
    require_native_cost_cover: bool = False
    require_absolute_movement_cost_cover: bool = False
    require_usdc_settlement: bool = False

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
        if (
            type(self.require_closing_execution_costs) is not bool
            or self.require_closing_execution_costs
            and not self.require_opening_execution_costs
        ):
            raise EntryBudgetPolicyError("TEST_PHASE_CLOSING_COST_POLICY_INVALID")
        if (
            type(self.require_next_funding_costs) is not bool
            or self.require_next_funding_costs
            and not self.require_closing_execution_costs
        ):
            raise EntryBudgetPolicyError("TEST_PHASE_FUNDING_COST_POLICY_INVALID")
        if (
            type(self.enforce_open_slot_loss_protection) is not bool
            or self.enforce_open_slot_loss_protection
            and not self.require_next_funding_costs
        ):
            raise EntryBudgetPolicyError("TEST_PHASE_OPEN_SLOT_PROTECTION_POLICY_INVALID")
        if (
            type(self.refresh_open_slot_cost_protection) is not bool
            or self.refresh_open_slot_cost_protection
            and not self.enforce_open_slot_loss_protection
        ):
            raise EntryBudgetPolicyError("TEST_PHASE_CURRENT_OPEN_SLOT_COST_POLICY_INVALID")
        if (
            type(self.renew_open_slot_cost_reserves) is not bool
            or self.renew_open_slot_cost_reserves
            and not self.refresh_open_slot_cost_protection
        ):
            raise EntryBudgetPolicyError("TEST_PHASE_OPEN_SLOT_COST_RENEWAL_POLICY_INVALID")
        if (
            type(self.require_native_initial_margin) is not bool
            or self.require_native_initial_margin
            and not self.renew_open_slot_cost_reserves
        ):
            raise EntryBudgetPolicyError("TEST_PHASE_NATIVE_INITIAL_MARGIN_POLICY_INVALID")
        if (
            type(self.require_native_cost_cover) is not bool
            or self.require_native_cost_cover
            and not self.require_native_initial_margin
        ):
            raise EntryBudgetPolicyError("TEST_PHASE_NATIVE_COST_COVER_POLICY_INVALID")
        if (
            type(self.require_absolute_movement_cost_cover) is not bool
            or self.require_absolute_movement_cost_cover
            and not self.require_native_cost_cover
        ):
            raise EntryBudgetPolicyError("TEST_PHASE_ABSOLUTE_MOVEMENT_COST_POLICY_INVALID")
        if (
            type(self.require_usdc_settlement) is not bool
            or self.require_usdc_settlement
            and not self.require_absolute_movement_cost_cover
        ):
            raise EntryBudgetPolicyError("TEST_PHASE_USDC_SETTLEMENT_POLICY_INVALID")

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
        if self.require_closing_execution_costs:
            result.update(schema="entry_budget_policy.v5", require_closing_execution_costs=True)
        if self.require_next_funding_costs:
            result.update(schema="entry_budget_policy.v6", require_next_funding_costs=True)
        if self.enforce_open_slot_loss_protection:
            result.update(schema="entry_budget_policy.v7", enforce_open_slot_loss_protection=True)
        if self.refresh_open_slot_cost_protection:
            result.update(schema="entry_budget_policy.v8", refresh_open_slot_cost_protection=True)
        if self.renew_open_slot_cost_reserves:
            result.update(schema="entry_budget_policy.v9", renew_open_slot_cost_reserves=True)
        if self.require_native_initial_margin:
            result.update(schema="entry_budget_policy.v10", require_native_initial_margin=True)
        if self.require_native_cost_cover:
            result.update(schema="entry_budget_policy.v11", require_native_cost_cover=True)
        if self.require_absolute_movement_cost_cover:
            result.update(
                schema="entry_budget_policy.v12",
                require_absolute_movement_cost_cover=True,
                require_usdc_settlement=self.require_usdc_settlement,
            )
        return result


def parse_slot_entry_budget_v1(payload):
    if isinstance(payload, dict) and payload.get("schema") == "entry_budget_policy.v12":
        previous = dict(payload)
        if previous.pop("require_absolute_movement_cost_cover", None) is not True:
            raise EntryBudgetPolicyError("TEST_PHASE_ABSOLUTE_MOVEMENT_COST_POLICY_INVALID")
        usdc = previous.pop("require_usdc_settlement", None)
        if type(usdc) is not bool:
            raise EntryBudgetPolicyError("TEST_PHASE_USDC_SETTLEMENT_POLICY_INVALID")
        previous["schema"] = "entry_budget_policy.v11"
        policy = replace(
            parse_slot_entry_budget_v1(previous),
            require_absolute_movement_cost_cover=True,
            require_usdc_settlement=usdc,
        )
        policy.validate_v1()
        return policy
    native_cost_mode = (
        isinstance(payload, dict) and payload.get("schema") == "entry_budget_policy.v11"
    )
    margin_mode = isinstance(payload, dict) and payload.get("schema") in {
        "entry_budget_policy.v10",
        "entry_budget_policy.v11",
    }
    renewal_mode = isinstance(payload, dict) and payload.get("schema") in {
        "entry_budget_policy.v9",
        "entry_budget_policy.v10",
        "entry_budget_policy.v11",
    }
    refresh_mode = isinstance(payload, dict) and payload.get("schema") in {
        "entry_budget_policy.v8",
        "entry_budget_policy.v9",
        "entry_budget_policy.v10",
        "entry_budget_policy.v11",
    }
    protection_mode = isinstance(payload, dict) and payload.get("schema") in {
        "entry_budget_policy.v7",
        "entry_budget_policy.v8",
        "entry_budget_policy.v9",
        "entry_budget_policy.v10",
        "entry_budget_policy.v11",
    }
    funding_mode = isinstance(payload, dict) and payload.get("schema") in {
        "entry_budget_policy.v6",
        "entry_budget_policy.v7",
        "entry_budget_policy.v8",
        "entry_budget_policy.v9",
        "entry_budget_policy.v10",
        "entry_budget_policy.v11",
    }
    close_mode = isinstance(payload, dict) and payload.get("schema") in {
        "entry_budget_policy.v5",
        "entry_budget_policy.v6",
        "entry_budget_policy.v7",
        "entry_budget_policy.v8",
        "entry_budget_policy.v9",
        "entry_budget_policy.v10",
        "entry_budget_policy.v11",
    }
    cost_mode = isinstance(payload, dict) and payload.get("schema") in {
        "entry_budget_policy.v4",
        "entry_budget_policy.v5",
        "entry_budget_policy.v6",
        "entry_budget_policy.v7",
        "entry_budget_policy.v8",
        "entry_budget_policy.v9",
        "entry_budget_policy.v10",
        "entry_budget_policy.v11",
    }
    loss_mode = isinstance(payload, dict) and payload.get("schema") in {
        "entry_budget_policy.v3",
        "entry_budget_policy.v4",
        "entry_budget_policy.v5",
        "entry_budget_policy.v6",
        "entry_budget_policy.v7",
        "entry_budget_policy.v8",
        "entry_budget_policy.v9",
        "entry_budget_policy.v10",
        "entry_budget_policy.v11",
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
    if close_mode:
        expected.add("require_closing_execution_costs")
    if funding_mode:
        expected.add("require_next_funding_costs")
    if protection_mode:
        expected.add("enforce_open_slot_loss_protection")
    if refresh_mode:
        expected.add("refresh_open_slot_cost_protection")
    if renewal_mode:
        expected.add("renew_open_slot_cost_reserves")
    if margin_mode:
        expected.add("require_native_initial_margin")
    if native_cost_mode:
        expected.add("require_native_cost_cover")
    if (
        not isinstance(payload, dict)
        or set(payload) != expected
        or payload["schema"]
        not in {
            "entry_budget_policy.v2",
            "entry_budget_policy.v3",
            "entry_budget_policy.v4",
            "entry_budget_policy.v5",
            "entry_budget_policy.v6",
            "entry_budget_policy.v7",
            "entry_budget_policy.v8",
            "entry_budget_policy.v9",
            "entry_budget_policy.v10",
            "entry_budget_policy.v11",
        }
    ):
        raise EntryBudgetPolicyError("ENTRY_BUDGET_SLOT_SCHEMA_INVALID")
    data = dict(payload)
    data.pop("schema")
    if native_cost_mode and data.get("require_native_cost_cover") is not True:
        raise EntryBudgetPolicyError("TEST_PHASE_NATIVE_COST_COVER_POLICY_INVALID")
    if margin_mode and data.get("require_native_initial_margin") is not True:
        raise EntryBudgetPolicyError("TEST_PHASE_NATIVE_INITIAL_MARGIN_POLICY_INVALID")
    if cost_mode and data.get("require_opening_execution_costs") is not True:
        raise EntryBudgetPolicyError("TEST_PHASE_OPENING_COST_POLICY_INVALID")
    if close_mode and data.get("require_closing_execution_costs") is not True:
        raise EntryBudgetPolicyError("TEST_PHASE_CLOSING_COST_POLICY_INVALID")
    if funding_mode and data.get("require_next_funding_costs") is not True:
        raise EntryBudgetPolicyError("TEST_PHASE_FUNDING_COST_POLICY_INVALID")
    if protection_mode and data.get("enforce_open_slot_loss_protection") is not True:
        raise EntryBudgetPolicyError("TEST_PHASE_OPEN_SLOT_PROTECTION_POLICY_INVALID")
    if refresh_mode and data.get("refresh_open_slot_cost_protection") is not True:
        raise EntryBudgetPolicyError("TEST_PHASE_CURRENT_OPEN_SLOT_COST_POLICY_INVALID")
    if renewal_mode and data.get("renew_open_slot_cost_reserves") is not True:
        raise EntryBudgetPolicyError("TEST_PHASE_OPEN_SLOT_COST_RENEWAL_POLICY_INVALID")
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
