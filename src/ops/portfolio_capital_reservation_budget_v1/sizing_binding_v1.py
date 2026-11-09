"""Freeze the canonical sizing result with its reservation, without recalculation.

This is decision-state serialization, not another sizing algorithm or learning
producer. Replaying an acknowledged hold must preserve its quantity provenance.
"""

from dataclasses import asdict, dataclass, fields, is_dataclass
from collections.abc import Mapping
from decimal import Decimal
from enum import Enum
import json
from types import UnionType
from typing import Union, get_args, get_origin, get_type_hints

from src.governance.capital_risk_sizing_v1 import (
    CapitalRiskSizingDecisionV1,
    CapitalRiskSizingInputV1,
    CapitalRiskSizingOutcome,
)
from .durable_store_v1 import digest


def _encode(value):
    return json.loads(json.dumps(asdict(value), default=str, allow_nan=False))


def _decode(kind, value):
    origin, args = get_origin(kind), get_args(kind)
    if origin in (Union, UnionType):
        if value is None and type(None) in args:
            return None
        candidates = [x for x in args if x is not type(None)]
        if len(candidates) != 1:
            raise ValueError("SIZING_STATE_TYPE_UNSUPPORTED")
        return _decode(candidates[0], value)
    if origin is tuple:
        if not isinstance(value, list) or len(args) != 2 or args[1] is not Ellipsis:
            raise ValueError("SIZING_STATE_TUPLE_INVALID")
        return tuple(_decode(args[0], x) for x in value)
    if origin is Mapping:
        if not isinstance(value, dict) or len(args) != 2:
            raise ValueError("SIZING_STATE_MAPPING_INVALID")
        return {_decode(args[0], k): _decode(args[1], v) for k, v in value.items()}
    if kind is Decimal:
        if not isinstance(value, str):
            raise ValueError("SIZING_STATE_DECIMAL_INVALID")
        result = Decimal(value)
        if not result.is_finite():
            raise ValueError("SIZING_STATE_DECIMAL_NONFINITE")
        return result
    if is_dataclass(kind):
        if not isinstance(value, dict) or set(value) != {f.name for f in fields(kind)}:
            raise ValueError("SIZING_STATE_SHAPE_INVALID")
        hints = get_type_hints(kind)
        return kind(**{name: _decode(hints[name], item) for name, item in value.items()})
    if isinstance(kind, type) and issubclass(kind, Enum):
        return kind(value)
    if kind in (str, int, bool) and type(value) is kind:
        return value
    raise ValueError("SIZING_STATE_TYPE_INVALID")


def request_digest_v1(request: CapitalRiskSizingInputV1) -> str:
    payload = _encode(request)
    # Current other holds may change; the acknowledged decision remains fixed.
    # Prices, policy, account budget, instrument units and all identities must match.
    payload.pop("already_committed_capital")
    payload.pop("current_reconciled_exposure")
    return digest(payload)


@dataclass(frozen=True)
class ReservationSizingBindingV1:
    request_digest: str
    applied_input: CapitalRiskSizingInputV1
    decision: CapitalRiskSizingDecisionV1
    risk_binding: object | None = None
    monetary_source: object | None = None
    entry_cost_binding: object | None = None
    close_cost_binding: object | None = None
    funding_cost_binding: object | None = None

    def validate_v1(self, *, amount: Decimal, decision_id: str) -> None:
        decision, applied = self.decision, self.applied_input
        sized, post, provenance = (
            decision.canonical_position_sizing,
            decision.post_sizing_risk,
            decision.quantity_provenance,
        )
        if not (
            len(self.request_digest) == 64
            and all(c in "0123456789abcdef" for c in self.request_digest)
            and decision.outcome is CapitalRiskSizingOutcome.PASS
            and sized is not None
            and post is not None
            and provenance is not None
            and decision.final_quantity > 0
            and decision.final_quantity
            == sized.rounded_quantity
            == post.final_allowed_quantity
            == provenance.final_quantity
            and sized.resulting_notional == post.resulting_notional == amount
            and applied.decision_id == sized.decision_id == provenance.decision_id == decision_id
            and applied.instrument_id == sized.instrument_id == applied.instrument.instrument_id
            and applied.selected_side.upper()
            == decision.selected_side.upper()
            == sized.side.upper()
            and decision.authority_effect == decision.runtime_effect == "NONE"
            and decision.adapter_compatible is False
        ):
            raise ValueError("RESERVATION_SIZING_BINDING_MISMATCH")
        if self.monetary_source is not None:
            from src.ops.governed_productive_monetary_normalization_v1.sizing_source_v1 import (
                SizingMonetarySourceV1,
            )
            from src.ops.governed_productive_monetary_normalization_v1.contracts_v1 import (
                MonetaryNormalizationError,
            )

            try:
                if type(self.monetary_source) is not SizingMonetarySourceV1:
                    raise ValueError("RESERVATION_TYPED_MONETARY_SOURCE_REQUIRED")
                self.monetary_source.validate_sizing_v1(applied)
            except (
                ValueError,
                TypeError,
                KeyError,
                ArithmeticError,
                MonetaryNormalizationError,
            ) as exc:
                raise ValueError("RESERVATION_MONETARY_SOURCE_INVALID:" + str(exc)) from exc
        if self.entry_cost_binding is not None:
            from .entry_execution_cost_v1 import EntryExecutionCostBindingV1

            if (
                type(self.entry_cost_binding) is not EntryExecutionCostBindingV1
                or self.monetary_source is None
            ):
                raise ValueError("RESERVATION_TYPED_ENTRY_COST_BINDING_REQUIRED")
            try:
                self.entry_cost_binding.validate_v1(
                    monetary_source=self.monetary_source, applied_input=applied, decision=decision
                )
            except (
                ValueError,
                TypeError,
                KeyError,
                AttributeError,
                ArithmeticError,
                MonetaryNormalizationError,
            ) as exc:
                raise ValueError("RESERVATION_ENTRY_COST_SOURCE_INVALID:" + str(exc)) from exc
        if self.close_cost_binding is not None:
            from .entry_execution_cost_v1 import CloseExecutionCostBindingV1

            if (
                type(self.close_cost_binding) is not CloseExecutionCostBindingV1
                or self.entry_cost_binding is None
            ):
                raise ValueError("RESERVATION_TYPED_CLOSE_COST_BINDING_REQUIRED")
            self.close_cost_binding.validate_v1(
                entry_binding=self.entry_cost_binding,
                monetary_source=self.monetary_source,
                applied_input=applied,
                decision=decision,
            )
        if self.funding_cost_binding is not None:
            from .entry_execution_cost_v1 import FundingCostBindingV1

            if (
                type(self.funding_cost_binding) is not FundingCostBindingV1
                or self.close_cost_binding is None
            ):
                raise ValueError("RESERVATION_TYPED_FUNDING_COST_BINDING_REQUIRED")
            self.funding_cost_binding.validate_v1(
                entry_binding=self.entry_cost_binding,
                close_binding=self.close_cost_binding,
                monetary_source=self.monetary_source,
                applied_input=applied,
                decision=decision,
            )
        if self.risk_binding is not None:
            from .restrictive_risk_binding_v1 import RiskAdmissionBindingV1

            if type(self.risk_binding) is not RiskAdmissionBindingV1:
                raise ValueError("RESERVATION_TYPED_RISK_BINDING_REQUIRED")
            self.risk_binding.validate_v1(amount=amount, decision_id=decision_id)
            if (
                Decimal(self.risk_binding.final_quantity) != decision.final_quantity
                or self.risk_binding.original_sizing_request_digest != self.request_digest
            ):
                raise ValueError("RESERVATION_RISK_QUANTITY_MISMATCH")

    def replay_v1(self, request: CapitalRiskSizingInputV1) -> CapitalRiskSizingDecisionV1:
        if request_digest_v1(request) != self.request_digest:
            raise ValueError("RESERVATION_SIZING_CONTEXT_CHANGED")
        # Envelope mappings are mutable even inside a frozen dataclass. A
        # downstream observer must not be able to alter stored decision state.
        return _decode(CapitalRiskSizingDecisionV1, _encode(self.decision))

    def to_dict_v1(self):
        result = {
            "schema": "reservation_sizing_binding.v2"
            if self.risk_binding is not None
            else "reservation_sizing_binding.v1",
            "request_digest": self.request_digest,
            "applied_input": _encode(self.applied_input),
            "decision": _encode(self.decision),
        }
        if self.risk_binding is not None:
            result["risk_binding"] = self.risk_binding.to_dict_v1()
        if self.monetary_source is not None:
            result["schema"] = "reservation_sizing_binding.v3"
            result["monetary_source"] = self.monetary_source.to_dict_v1()
        if self.entry_cost_binding is not None:
            result["schema"] = "reservation_sizing_binding.v4"
            result["entry_cost_binding"] = self.entry_cost_binding.to_dict_v1()
        if self.close_cost_binding is not None:
            result["schema"] = "reservation_sizing_binding.v5"
            result["close_cost_binding"] = self.close_cost_binding.to_dict_v1()
        if self.funding_cost_binding is not None:
            result["schema"] = "reservation_sizing_binding.v6"
            result["funding_cost_binding"] = self.funding_cost_binding.to_dict_v1()
        return result

    @classmethod
    def from_dict_v1(cls, payload):
        from .restrictive_risk_binding_v1 import RiskAdmissionBindingV1

        version2 = (
            isinstance(payload, dict) and payload.get("schema") == "reservation_sizing_binding.v2"
        )
        version3 = isinstance(payload, dict) and payload.get("schema") in {
            "reservation_sizing_binding.v3",
            "reservation_sizing_binding.v4",
            "reservation_sizing_binding.v5",
            "reservation_sizing_binding.v6",
        }
        version4 = isinstance(payload, dict) and payload.get("schema") in {
            "reservation_sizing_binding.v4",
            "reservation_sizing_binding.v5",
            "reservation_sizing_binding.v6",
        }
        version5 = isinstance(payload, dict) and payload.get("schema") in {
            "reservation_sizing_binding.v5",
            "reservation_sizing_binding.v6",
        }
        version6 = (
            isinstance(payload, dict) and payload.get("schema") == "reservation_sizing_binding.v6"
        )
        required = {"schema", "request_digest", "applied_input", "decision"}
        if version2 or version3 and "risk_binding" in payload:
            required.add("risk_binding")
        if version3:
            required.add("monetary_source")
        if version4:
            required.add("entry_cost_binding")
        if version5:
            required.add("close_cost_binding")
        if version6:
            required.add("funding_cost_binding")
        if (
            not isinstance(payload, dict)
            or set(payload) != required
            or payload["schema"]
            not in {
                "reservation_sizing_binding.v1",
                "reservation_sizing_binding.v2",
                "reservation_sizing_binding.v3",
                "reservation_sizing_binding.v4",
                "reservation_sizing_binding.v5",
                "reservation_sizing_binding.v6",
            }
        ):
            raise ValueError("RESERVATION_SIZING_STATE_SCHEMA_INVALID")
        from src.ops.governed_productive_monetary_normalization_v1.sizing_source_v1 import (
            SizingMonetarySourceV1,
        )
        from .entry_execution_cost_v1 import EntryExecutionCostBindingV1
        from .entry_execution_cost_v1 import CloseExecutionCostBindingV1
        from .entry_execution_cost_v1 import FundingCostBindingV1

        return cls(
            request_digest=payload["request_digest"],
            applied_input=_decode(CapitalRiskSizingInputV1, payload["applied_input"]),
            decision=_decode(CapitalRiskSizingDecisionV1, payload["decision"]),
            risk_binding=RiskAdmissionBindingV1.from_dict_v1(payload["risk_binding"])
            if version2 or version3 and "risk_binding" in payload
            else None,
            monetary_source=SizingMonetarySourceV1.from_dict_v1(payload["monetary_source"])
            if version3
            else None,
            entry_cost_binding=EntryExecutionCostBindingV1.from_dict_v1(
                payload["entry_cost_binding"]
            )
            if version4
            else None,
            close_cost_binding=CloseExecutionCostBindingV1.from_dict_v1(
                payload["close_cost_binding"]
            )
            if version5
            else None,
            funding_cost_binding=FundingCostBindingV1.from_dict_v1(payload["funding_cost_binding"])
            if version6
            else None,
        )
