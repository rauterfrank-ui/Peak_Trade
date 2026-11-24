"""Outer Operations entry limits, applied after the trading decision.

No fictional equity, E2E profile, Double-Play input, strategy or sizing engine.
The existing canonical sizer consumes reduced ceilings over unchanged Q0 capital.
"""

from dataclasses import dataclass, replace
from decimal import Decimal, InvalidOperation
from hashlib import sha256
import json
from pathlib import Path


POLICY_PATH = (
    Path(__file__).resolve().parents[3]
    / "config/ops/current_productive_entry_budget_policy_v1.json"
)


class EntryBudgetPolicyError(ValueError):
    pass


@dataclass(frozen=True)
class EntryBudgetPolicyV1:
    policy_id: str
    revision: int
    per_entry_notional_limit: Decimal
    aggregate_reserved_notional_limit: Decimal
    currency: str = "USDC"
    automatic_increase_allowed: bool = False
    expiry: str = "UNTIL_EXPLICIT_POLICY_CHANGE"

    def validate_v1(self):
        if (
            not isinstance(self.policy_id, str)
            or not self.policy_id
            or self.policy_id != self.policy_id.strip()
        ):
            raise EntryBudgetPolicyError("ENTRY_BUDGET_POLICY_ID_INVALID")
        if type(self.revision) is not int or self.revision < 1:
            raise EntryBudgetPolicyError("ENTRY_BUDGET_POLICY_REVISION_INVALID")
        if (
            self.currency != "USDC"
            or self.automatic_increase_allowed is not False
            or self.expiry != "UNTIL_EXPLICIT_POLICY_CHANGE"
        ):
            raise EntryBudgetPolicyError("ENTRY_BUDGET_POLICY_SCOPE_INVALID")
        for value in (self.per_entry_notional_limit, self.aggregate_reserved_notional_limit):
            if not isinstance(value, Decimal) or not value.is_finite() or value <= 0:
                raise EntryBudgetPolicyError("ENTRY_BUDGET_POLICY_LIMIT_INVALID")
        if self.per_entry_notional_limit > self.aggregate_reserved_notional_limit:
            raise EntryBudgetPolicyError("ENTRY_BUDGET_POLICY_LIMIT_ORDER_INVALID")

    def to_dict_v1(self):
        self.validate_v1()
        return {
            "schema": "entry_budget_policy.v1",
            "policy_id": self.policy_id,
            "revision": self.revision,
            "currency": self.currency,
            "per_entry_notional_limit": str(self.per_entry_notional_limit),
            "aggregate_reserved_notional_limit": str(self.aggregate_reserved_notional_limit),
            "automatic_increase_allowed": False,
            "expiry": self.expiry,
        }

    def digest_v1(self):
        return sha256(
            json.dumps(self.to_dict_v1(), sort_keys=True, separators=(",", ":")).encode()
        ).hexdigest()

    def constrain_entry_context_v1(self, context):
        """A derived sizing-only context; never passed back to a DP producer."""
        self.validate_v1()
        if context.capital_risk_mode != "LIVE_ACCOUNT_BOUND":
            raise EntryBudgetPolicyError("ENTRY_BUDGET_REQUIRES_ACCOUNT_BOUND_CONTEXT")
        original_equity = context.account_equity
        policy_digest = self.digest_v1()
        binding_digest = sha256(
            json.dumps(
                {
                    "source_config_digest": context.config_digest,
                    "source_policy_digest": context.policy_digest,
                    "entry_budget_policy_digest": policy_digest,
                },
                sort_keys=True,
            ).encode()
        ).hexdigest()
        result = replace(
            context,
            scope_capital_limit=min(context.scope_capital_limit, self.per_entry_notional_limit),
            total_capital_limit=min(
                context.total_capital_limit, self.aggregate_reserved_notional_limit
            ),
            config_digest=binding_digest,
            policy_digest=binding_digest,
        )
        if result.account_equity != original_equity:
            raise EntryBudgetPolicyError("ENTRY_BUDGET_MUST_NOT_CHANGE_EQUITY")
        return result


def load_entry_budget_policy_v1(path: Path | None = None):
    try:
        payload = json.loads((path if path is not None else POLICY_PATH).read_text())
        expected = {
            "schema",
            "policy_id",
            "revision",
            "currency",
            "per_entry_notional_limit",
            "aggregate_reserved_notional_limit",
            "automatic_increase_allowed",
            "expiry",
        }
        if (
            not isinstance(payload, dict)
            or set(payload) != expected
            or payload["schema"] != "entry_budget_policy.v1"
        ):
            raise EntryBudgetPolicyError("ENTRY_BUDGET_POLICY_SCHEMA_INVALID")
        for field in ("per_entry_notional_limit", "aggregate_reserved_notional_limit"):
            if not isinstance(payload[field], str):
                raise EntryBudgetPolicyError("ENTRY_BUDGET_POLICY_DECIMAL_STRING_REQUIRED")
        policy = EntryBudgetPolicyV1(
            policy_id=payload["policy_id"],
            revision=payload["revision"],
            per_entry_notional_limit=Decimal(payload["per_entry_notional_limit"]),
            aggregate_reserved_notional_limit=Decimal(payload["aggregate_reserved_notional_limit"]),
            currency=payload["currency"],
            automatic_increase_allowed=payload["automatic_increase_allowed"],
            expiry=payload["expiry"],
        )
        policy.validate_v1()
        return policy
    except (OSError, ValueError, TypeError, KeyError, InvalidOperation) as exc:
        raise EntryBudgetPolicyError("ENTRY_BUDGET_POLICY_UNAVAILABLE_OR_INVALID") from exc
