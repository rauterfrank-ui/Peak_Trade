"""Order-Capability demo instrument rules offline binding contract (v1).

Pure offline evaluation of demo host, credential class, instrument canonical binding,
and manifest-verified instrument rule fields. Does not authorize network, secrets,
order submission, cancel, live, preflight lift, or execute.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from enum import Enum
from typing import Any

from src.ops.bounded_futures_private_readonly_contract_v0 import DEMO_FUTURES_HOST
from src.ops.bounded_futures_testnet_contract_v0 import DEFAULT_INSTRUMENT

PACKAGE_MARKER = "ORDER_CAPABILITY_DEMO_INSTRUMENT_RULES_BINDING_CONTRACT_V1=true"
SCHEMA_VERSION = "order_capability_demo_instrument_rules_binding_result.v1"
AUTHORITY_IMPACT = "NO_AUTHORITY_CHANGE"

REQUIRED_DEMO_HOST = DEMO_FUTURES_HOST
ALLOWED_CREDENTIAL_CLASS = "kraken_futures_demo_only"
DEFAULT_MAX_NOTIONAL_EUR = Decimal("10.0")

FORBIDDEN_HOST_MARKERS = frozenset(
    {
        "live",
        "prod",
        "production",
        "mainnet",
        "futures.kraken.com",
    }
)
FORBIDDEN_CREDENTIAL_MARKERS = frozenset(
    {
        "live",
        "prod",
        "production",
        "mainnet",
        "spot",
        "kraken_spot",
        "kraken_futures_live",
    }
)
FORBIDDEN_SERIALIZATION_KEYS = frozenset(
    {
        "api_key",
        "api_secret",
        "secret",
        "password",
        "token",
        "credential",
        "credentials",
        "private_key",
    }
)

REASON_DEMO_HOST_MISMATCH = "DEMO_HOST_MISMATCH"
REASON_LIVE_HOST_REJECTED = "LIVE_HOST_REJECTED"
REASON_CREDENTIAL_CLASS_REJECTED = "CREDENTIAL_CLASS_REJECTED"
REASON_MISSING_INSTRUMENT = "MISSING_INSTRUMENT"
REASON_OFFLINE_RULES_NOT_BOUND = "OFFLINE_RULES_NOT_BOUND"
REASON_MISSING_MIN_SIZE = "MISSING_MIN_SIZE"
REASON_MISSING_QTY_STEP = "MISSING_QTY_STEP"
REASON_MISSING_PRICE_TICK = "MISSING_PRICE_TICK"
REASON_MISSING_QTY_PRECISION = "MISSING_QTY_PRECISION"
REASON_MISSING_PRICE_PRECISION = "MISSING_PRICE_PRECISION"
REASON_MIN_SIZE_NOT_POSITIVE = "MIN_SIZE_NOT_POSITIVE"
REASON_INFEASIBLE_UNDER_CAP_ENVELOPE = "INFEASIBLE_UNDER_CAP_ENVELOPE"
REASON_CAP_FEASIBILITY_INPUT_MISSING = "CAP_FEASIBILITY_INPUT_MISSING"
REASON_FORBIDDEN_ENDPOINT_CANCELALLORDERS = "FORBIDDEN_ENDPOINT_CANCELALLORDERS"
REASON_FORBIDDEN_ENDPOINT_BATCHORDER = "FORBIDDEN_ENDPOINT_BATCHORDER"
REASON_UNSAFE_AUTHORITY_FLAGS = "UNSAFE_AUTHORITY_FLAGS"
REASON_SECRET_MATERIAL_REJECTED = "SECRET_MATERIAL_REJECTED"

BLOCKER_MIN_SIZE_NOT_VERIFIED_OFFLINE = "BLOCKER_MIN_SIZE_NOT_VERIFIED_OFFLINE"


class DemoInstrumentRulesBindingError(ValueError):
    """Fail-closed demo instrument rules binding evaluation or validation error."""


class DemoInstrumentRulesBindingVerdictKind(str, Enum):
    BINDING_SATISFIED_FOR_DRY_ONLY = "BINDING_SATISFIED_FOR_DRY_ONLY"
    INFEASIBLE_UNDER_CAP = "INFEASIBLE_UNDER_CAP"
    FAIL_CLOSED = "FAIL_CLOSED"


@dataclass(frozen=True)
class DemoInstrumentOfflineRulesBound:
    min_size: Decimal | None
    qty_step: Decimal | None
    price_tick: Decimal | None
    qty_precision: int | None
    price_precision: int | None
    min_notional: Decimal | None = None
    offline_bound: bool = False
    source_ref: str = ""


@dataclass(frozen=True)
class OrderCapabilityDemoInstrumentRulesBindingInput:
    demo_host: str = ""
    credential_class: str = ""
    instrument: str = ""
    offline_rules: DemoInstrumentOfflineRulesBound | None = None
    cap_max_notional_eur: Decimal = DEFAULT_MAX_NOTIONAL_EUR
    reference_price_usd: Decimal | None = None
    fx_rate_usd_per_eur: Decimal | None = None
    cancelallorders: bool = False
    batchorder: bool = False
    execute_authorized: bool = False
    order_authorized: bool = False
    cancel_authorized: bool = False


@dataclass(frozen=True)
class OrderCapabilityDemoInstrumentRulesBindingResult:
    verdict: DemoInstrumentRulesBindingVerdictKind
    reason_codes: tuple[str, ...]
    blockers: tuple[str, ...]
    violations: tuple[str, ...]
    demo_instrument_rules_binding_prepared: bool
    instrument_rules_offline_bound: bool
    min_size_verified_offline: bool
    cap_feasible: bool
    operator_side_qty_price_decision_prep_allowed_next: bool
    demo_mutation_execute_allowed_now: bool
    order_authorized_now: bool
    cancel_authorized_now: bool
    execute_authorized_now: bool
    authority_impact: str
    blocker_min_size_not_verified_offline: bool
    value_redacted: bool
    no_secret_material: bool
    cancelallorders_allowed: bool
    batchorder_allowed: bool


def _normalize(text: str) -> str:
    return " ".join(text.strip().lower().split())


def _normalize_host(host: str) -> str:
    normalized = _normalize(host)
    if normalized.startswith("https://"):
        normalized = normalized[len("https://") :]
    if normalized.startswith("http://"):
        normalized = normalized[len("http://") :]
    return normalized.split("/", 1)[0]


def _contains_forbidden_marker(value: str, markers: frozenset[str]) -> bool:
    normalized = _normalize(value)
    return any(marker in normalized for marker in markers)


def _positive_decimal(value: Decimal | None) -> bool:
    if value is None:
        return False
    try:
        return value > 0
    except Exception:
        return False


def _validate_demo_host(demo_host: str) -> list[str]:
    normalized = _normalize_host(demo_host)
    if not normalized:
        return [REASON_DEMO_HOST_MISMATCH]
    if normalized == REQUIRED_DEMO_HOST:
        return []
    if _contains_forbidden_marker(normalized, FORBIDDEN_HOST_MARKERS):
        return [REASON_LIVE_HOST_REJECTED]
    return [REASON_DEMO_HOST_MISMATCH]


def _validate_credential_class(credential_class: str) -> list[str]:
    normalized = _normalize(credential_class).replace(" ", "_")
    if not normalized:
        return [REASON_CREDENTIAL_CLASS_REJECTED]
    if _contains_forbidden_marker(normalized, FORBIDDEN_CREDENTIAL_MARKERS):
        return [REASON_CREDENTIAL_CLASS_REJECTED]
    if normalized != ALLOWED_CREDENTIAL_CLASS:
        return [REASON_CREDENTIAL_CLASS_REJECTED]
    return []


def _validate_instrument(instrument: str) -> list[str]:
    if not instrument.strip():
        return [REASON_MISSING_INSTRUMENT]
    return []


def _validate_offline_rules(
    rules: DemoInstrumentOfflineRulesBound | None,
) -> tuple[list[str], bool]:
    if rules is None:
        return [REASON_OFFLINE_RULES_NOT_BOUND], False

    reasons: list[str] = []
    if not rules.offline_bound:
        reasons.append(REASON_OFFLINE_RULES_NOT_BOUND)
    if not rules.source_ref.strip():
        reasons.append(REASON_OFFLINE_RULES_NOT_BOUND)
    if not _positive_decimal(rules.min_size):
        reasons.append(REASON_MISSING_MIN_SIZE)
        if rules.min_size is not None and rules.min_size <= 0:
            reasons.append(REASON_MIN_SIZE_NOT_POSITIVE)
    if not _positive_decimal(rules.qty_step):
        reasons.append(REASON_MISSING_QTY_STEP)
    if not _positive_decimal(rules.price_tick):
        reasons.append(REASON_MISSING_PRICE_TICK)
    if rules.qty_precision is None or rules.qty_precision < 0:
        reasons.append(REASON_MISSING_QTY_PRECISION)
    if rules.price_precision is None or rules.price_precision < 0:
        reasons.append(REASON_MISSING_PRICE_PRECISION)

    min_size_verified = not any(
        code
        in {
            REASON_OFFLINE_RULES_NOT_BOUND,
            REASON_MISSING_MIN_SIZE,
            REASON_MIN_SIZE_NOT_POSITIVE,
            REASON_MISSING_QTY_STEP,
            REASON_MISSING_PRICE_TICK,
            REASON_MISSING_QTY_PRECISION,
            REASON_MISSING_PRICE_PRECISION,
        }
        for code in reasons
    )
    instrument_rules_offline_bound = min_size_verified
    return reasons, instrument_rules_offline_bound


def _validate_unsafe_authority_flags(
    inp: OrderCapabilityDemoInstrumentRulesBindingInput,
) -> list[str]:
    if inp.execute_authorized or inp.order_authorized or inp.cancel_authorized:
        return [REASON_UNSAFE_AUTHORITY_FLAGS]
    return []


def _validate_forbidden_endpoints(inp: OrderCapabilityDemoInstrumentRulesBindingInput) -> list[str]:
    reasons: list[str] = []
    if inp.cancelallorders:
        reasons.append(REASON_FORBIDDEN_ENDPOINT_CANCELALLORDERS)
    if inp.batchorder:
        reasons.append(REASON_FORBIDDEN_ENDPOINT_BATCHORDER)
    return reasons


def _estimate_cap_feasibility(
    *,
    rules: DemoInstrumentOfflineRulesBound | None,
    cap_max_notional_eur: Decimal,
    reference_price_usd: Decimal | None,
    fx_rate_usd_per_eur: Decimal | None,
    instrument_rules_offline_bound: bool,
) -> tuple[bool, list[str]]:
    if not instrument_rules_offline_bound or rules is None:
        return False, [REASON_CAP_FEASIBILITY_INPUT_MISSING]

    if reference_price_usd is None or fx_rate_usd_per_eur is None:
        return False, [REASON_CAP_FEASIBILITY_INPUT_MISSING]
    if not _positive_decimal(reference_price_usd) or not _positive_decimal(fx_rate_usd_per_eur):
        return False, [REASON_CAP_FEASIBILITY_INPUT_MISSING]
    if cap_max_notional_eur <= 0:
        return False, [REASON_INFEASIBLE_UNDER_CAP_ENVELOPE]

    min_notional_estimate_usd = rules.min_size * reference_price_usd  # type: ignore[operator]
    cap_usd = cap_max_notional_eur * fx_rate_usd_per_eur

    if rules.min_notional is not None and rules.min_notional > cap_usd:
        return False, [REASON_INFEASIBLE_UNDER_CAP_ENVELOPE]
    if min_notional_estimate_usd > cap_usd:
        return False, [REASON_INFEASIBLE_UNDER_CAP_ENVELOPE]
    return True, []


def _immutable_authority_fields(
    *,
    verdict: DemoInstrumentRulesBindingVerdictKind,
    reason_codes: list[str],
    blockers: list[str],
    demo_instrument_rules_binding_prepared: bool,
    instrument_rules_offline_bound: bool,
    min_size_verified_offline: bool,
    cap_feasible: bool,
    operator_side_qty_price_decision_prep_allowed_next: bool,
    cancelallorders: bool,
    batchorder: bool,
) -> OrderCapabilityDemoInstrumentRulesBindingResult:
    deduped_reasons = tuple(dict.fromkeys(reason_codes))
    deduped_blockers = tuple(dict.fromkeys(blockers))
    return OrderCapabilityDemoInstrumentRulesBindingResult(
        verdict=verdict,
        reason_codes=deduped_reasons,
        blockers=deduped_blockers,
        violations=deduped_reasons,
        demo_instrument_rules_binding_prepared=demo_instrument_rules_binding_prepared,
        instrument_rules_offline_bound=instrument_rules_offline_bound,
        min_size_verified_offline=min_size_verified_offline,
        cap_feasible=cap_feasible,
        operator_side_qty_price_decision_prep_allowed_next=operator_side_qty_price_decision_prep_allowed_next,
        demo_mutation_execute_allowed_now=False,
        order_authorized_now=False,
        cancel_authorized_now=False,
        execute_authorized_now=False,
        authority_impact=AUTHORITY_IMPACT,
        blocker_min_size_not_verified_offline=not min_size_verified_offline,
        value_redacted=True,
        no_secret_material=True,
        cancelallorders_allowed=False,
        batchorder_allowed=False,
    )


def evaluate_order_capability_demo_instrument_rules_binding(
    inp: OrderCapabilityDemoInstrumentRulesBindingInput,
) -> OrderCapabilityDemoInstrumentRulesBindingResult:
    """Evaluate demo instrument rules offline binding without authorizing execute or orders."""
    reasons: list[str] = []
    blockers: list[str] = []

    reasons.extend(_validate_demo_host(inp.demo_host))
    reasons.extend(_validate_credential_class(inp.credential_class))
    reasons.extend(_validate_instrument(inp.instrument))
    reasons.extend(_validate_unsafe_authority_flags(inp))
    reasons.extend(_validate_forbidden_endpoints(inp))

    rule_reasons, instrument_rules_offline_bound = _validate_offline_rules(inp.offline_rules)
    reasons.extend(rule_reasons)

    min_size_verified_offline = instrument_rules_offline_bound
    if not min_size_verified_offline:
        blockers.append(BLOCKER_MIN_SIZE_NOT_VERIFIED_OFFLINE)

    cap_feasible, cap_reasons = _estimate_cap_feasibility(
        rules=inp.offline_rules,
        cap_max_notional_eur=inp.cap_max_notional_eur,
        reference_price_usd=inp.reference_price_usd,
        fx_rate_usd_per_eur=inp.fx_rate_usd_per_eur,
        instrument_rules_offline_bound=instrument_rules_offline_bound,
    )
    reasons.extend(cap_reasons)

    deduped_reasons = list(dict.fromkeys(reasons))
    binding_prepared = instrument_rules_offline_bound and not any(
        code
        in {
            REASON_DEMO_HOST_MISMATCH,
            REASON_LIVE_HOST_REJECTED,
            REASON_CREDENTIAL_CLASS_REJECTED,
            REASON_MISSING_INSTRUMENT,
        }
        for code in deduped_reasons
    )

    operator_prep_allowed = (
        binding_prepared
        and min_size_verified_offline
        and cap_feasible
        and not blockers
        and not deduped_reasons
    )

    if deduped_reasons:
        if (
            instrument_rules_offline_bound
            and REASON_INFEASIBLE_UNDER_CAP_ENVELOPE in deduped_reasons
            and len(
                [code for code in deduped_reasons if code != REASON_INFEASIBLE_UNDER_CAP_ENVELOPE]
            )
            == 0
        ):
            return _immutable_authority_fields(
                verdict=DemoInstrumentRulesBindingVerdictKind.INFEASIBLE_UNDER_CAP,
                reason_codes=deduped_reasons,
                blockers=blockers,
                demo_instrument_rules_binding_prepared=binding_prepared,
                instrument_rules_offline_bound=instrument_rules_offline_bound,
                min_size_verified_offline=min_size_verified_offline,
                cap_feasible=False,
                operator_side_qty_price_decision_prep_allowed_next=False,
                cancelallorders=inp.cancelallorders,
                batchorder=inp.batchorder,
            )
        return _immutable_authority_fields(
            verdict=DemoInstrumentRulesBindingVerdictKind.FAIL_CLOSED,
            reason_codes=deduped_reasons,
            blockers=blockers,
            demo_instrument_rules_binding_prepared=False,
            instrument_rules_offline_bound=instrument_rules_offline_bound,
            min_size_verified_offline=min_size_verified_offline,
            cap_feasible=cap_feasible,
            operator_side_qty_price_decision_prep_allowed_next=False,
            cancelallorders=inp.cancelallorders,
            batchorder=inp.batchorder,
        )

    return _immutable_authority_fields(
        verdict=DemoInstrumentRulesBindingVerdictKind.BINDING_SATISFIED_FOR_DRY_ONLY,
        reason_codes=[],
        blockers=[],
        demo_instrument_rules_binding_prepared=True,
        instrument_rules_offline_bound=True,
        min_size_verified_offline=True,
        cap_feasible=True,
        operator_side_qty_price_decision_prep_allowed_next=operator_prep_allowed,
        cancelallorders=inp.cancelallorders,
        batchorder=inp.batchorder,
    )


def default_order_capability_demo_instrument_rules_binding_input() -> (
    OrderCapabilityDemoInstrumentRulesBindingInput
):
    return OrderCapabilityDemoInstrumentRulesBindingInput()


def reject_secret_like_mapping(mapping: dict[str, Any]) -> list[str]:
    reasons: list[str] = []
    for key in mapping:
        if key.lower() in FORBIDDEN_SERIALIZATION_KEYS:
            reasons.append(REASON_SECRET_MATERIAL_REJECTED)
    return reasons


def serialize_order_capability_demo_instrument_rules_binding_result(
    result: OrderCapabilityDemoInstrumentRulesBindingResult,
) -> dict[str, Any]:
    validate_order_capability_demo_instrument_rules_binding_result(result)
    data: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "contract_marker": PACKAGE_MARKER,
        "verdict": result.verdict.value,
        "reason_codes": list(result.reason_codes),
        "blockers": list(result.blockers),
        "violations": list(result.violations),
        "demo_instrument_rules_binding_prepared": result.demo_instrument_rules_binding_prepared,
        "instrument_rules_offline_bound": result.instrument_rules_offline_bound,
        "min_size_verified_offline": result.min_size_verified_offline,
        "cap_feasible": result.cap_feasible,
        "operator_side_qty_price_decision_prep_allowed_next": (
            result.operator_side_qty_price_decision_prep_allowed_next
        ),
        "demo_mutation_execute_allowed_now": result.demo_mutation_execute_allowed_now,
        "order_authorized_now": result.order_authorized_now,
        "cancel_authorized_now": result.cancel_authorized_now,
        "execute_authorized_now": result.execute_authorized_now,
        "authority_impact": result.authority_impact,
        "blocker_min_size_not_verified_offline": result.blocker_min_size_not_verified_offline,
        "value_redacted": result.value_redacted,
        "no_secret_material": result.no_secret_material,
        "cancelallorders_allowed": result.cancelallorders_allowed,
        "batchorder_allowed": result.batchorder_allowed,
        "default_instrument_reference": DEFAULT_INSTRUMENT,
        "required_demo_host": REQUIRED_DEMO_HOST,
        "allowed_credential_class": ALLOWED_CREDENTIAL_CLASS,
    }
    for key in data:
        if key.lower() in FORBIDDEN_SERIALIZATION_KEYS:
            raise DemoInstrumentRulesBindingError(
                f"serialized result must not include forbidden key {key!r}"
            )
    return data


def validate_order_capability_demo_instrument_rules_binding_result(
    result: OrderCapabilityDemoInstrumentRulesBindingResult,
) -> None:
    if result.authority_impact != AUTHORITY_IMPACT:
        raise DemoInstrumentRulesBindingError("authority_impact must remain NO_AUTHORITY_CHANGE")
    if (
        result.order_authorized_now
        or result.cancel_authorized_now
        or result.execute_authorized_now
        or result.demo_mutation_execute_allowed_now
    ):
        raise DemoInstrumentRulesBindingError("order/cancel/execute authority must remain false")
    if not result.value_redacted or not result.no_secret_material:
        raise DemoInstrumentRulesBindingError(
            "value_redacted and no_secret_material must remain true"
        )
    if result.cancelallorders_allowed or result.batchorder_allowed:
        raise DemoInstrumentRulesBindingError(
            "cancelallorders and batchorder must remain disallowed"
        )
    if result.blocker_min_size_not_verified_offline != (not result.min_size_verified_offline):
        raise DemoInstrumentRulesBindingError(
            "blocker_min_size_not_verified_offline must mirror min_size_verified_offline"
        )
    if result.verdict == DemoInstrumentRulesBindingVerdictKind.BINDING_SATISFIED_FOR_DRY_ONLY:
        if result.reason_codes or result.violations:
            raise DemoInstrumentRulesBindingError("BINDING_SATISFIED must have empty reason_codes")
        if not result.instrument_rules_offline_bound or not result.min_size_verified_offline:
            raise DemoInstrumentRulesBindingError(
                "BINDING_SATISFIED requires offline-bound instrument rules"
            )
        if not result.cap_feasible:
            raise DemoInstrumentRulesBindingError("BINDING_SATISFIED requires cap_feasible=true")
    elif result.verdict == DemoInstrumentRulesBindingVerdictKind.INFEASIBLE_UNDER_CAP:
        if REASON_INFEASIBLE_UNDER_CAP_ENVELOPE not in result.reason_codes:
            raise DemoInstrumentRulesBindingError(
                "INFEASIBLE_UNDER_CAP requires INFEASIBLE_UNDER_CAP_ENVELOPE reason"
            )
        if result.cap_feasible:
            raise DemoInstrumentRulesBindingError(
                "INFEASIBLE_UNDER_CAP requires cap_feasible=false"
            )
    else:
        if not result.reason_codes:
            raise DemoInstrumentRulesBindingError("FAIL_CLOSED requires non-empty reason_codes")
