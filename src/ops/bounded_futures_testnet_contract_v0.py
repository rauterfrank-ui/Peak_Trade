"""Repo-native bounded Futures Testnet contract (v0).

Offline contract evaluator for bounded-futures-normal-testnet-v0 session evidence.
Does not authorize Futures Testnet execute; FUTURES_SESSION_AUTHORIZED_NOW remains false.
Does not grant Master-V2 / Double-Play authority. Spot BTC/EUR evidence must not satisfy this contract.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

PACKAGE_MARKER = "BOUNDED_FUTURES_TESTNET_CONTRACT_V0=true"
FUTURES_SESSION_AUTHORIZED_NOW = False
DEFAULT_SESSION_CLASS = "bounded-futures-normal-testnet-v0"
DEFAULT_ORDER_POLICY = "normal-testnet-futures-bounded"
DEFAULT_INSTRUMENT = "PF_ETHUSD"
DEFAULT_MARKET_TYPE = "futures"
# Binance-style placeholder — must not be used as bounded futures testnet default.
REJECTED_FUTURES_INSTRUMENT_PLACEHOLDERS: frozenset[str] = frozenset({"BTCUSDT"})
DEFAULT_MARGIN_MODE = "isolated"
DEFAULT_POSITION_MODE = "one_way"
DEFAULT_MAX_LEVERAGE = 5.0
EVIDENCE_SOURCE_FUTURES_HARNESS = "archive_futures_testnet_harness"
EVIDENCE_SOURCE_REPO_NATIVE = "repo_native_futures_session"

# Spot paths from accepted BTC/EUR harness — must not appear in futures bounded evidence.
SPOT_KRAKEN_ENDPOINT_PREFIXES: frozenset[str] = frozenset(
    {
        "/0/public/Ticker",
        "/0/public/Time",
        "/0/public/AssetPairs",
        "/0/private/AddOrder",
        "/0/private/CancelOrder",
        "/0/private/Balance",
        "/0/private/OpenOrders",
    }
)
SPOT_SESSION_CLASSES: frozenset[str] = frozenset(
    {
        "bounded-normal-testnet-v0",
        "longer-bounded-normal-testnet-v0",
    }
)
SPOT_INSTRUMENTS: frozenset[str] = frozenset({"BTC/EUR", "ETH/EUR"})

ZERO_ORDER_REQUIRED_PUBLIC_ENDPOINTS: tuple[str, ...] = (
    "/derivatives/api/v3/tickers",
    "/derivatives/api/v3/instruments",
)

REQUIRED_FUTURES_EVIDENCE_FIELD_NAMES: tuple[str, ...] = (
    "session_class",
    "order_policy",
    "instrument",
    "market_type",
    "margin_mode",
    "max_leverage",
    "leverage_within_cap",
    "position_mode",
    "order_side_semantics",
    "reduce_only_supported",
    "order_attempt_count",
    "real_orders_created_count",
    "cancel_or_close_attempt_count",
    "order_notional_eur",
    "order_notional_within_cap",
    "position_flattened_by_end",
    "cancel_or_close_evidence_valid",
    "futures_endpoint_isolation_pass",
    "spot_endpoint_isolation_pass",
    "funding_risk_acknowledged",
    "liquidation_risk_acknowledged",
    "risk_killswitch_scope_active",
    "risk_killswitch_scope_pass",
    "master_v2_double_play_authority_used",
)


@dataclass(frozen=True)
class BoundedFuturesTestnetSpec:
    session_class: str
    order_policy: str
    instrument: str
    market_type: str
    margin_mode: str
    position_mode: str
    max_leverage: float
    max_real_orders: int
    max_order_attempts: int
    max_cancel_attempts: int
    max_notional_eur: float
    max_position_hold_seconds: int
    position_must_be_flattened: bool
    require_reduce_only_support: bool


def default_bounded_futures_normal_v0_spec() -> BoundedFuturesTestnetSpec:
    return BoundedFuturesTestnetSpec(
        session_class=DEFAULT_SESSION_CLASS,
        order_policy=DEFAULT_ORDER_POLICY,
        instrument=DEFAULT_INSTRUMENT,
        market_type=DEFAULT_MARKET_TYPE,
        margin_mode=DEFAULT_MARGIN_MODE,
        position_mode=DEFAULT_POSITION_MODE,
        max_leverage=DEFAULT_MAX_LEVERAGE,
        max_real_orders=1,
        max_order_attempts=1,
        max_cancel_attempts=1,
        max_notional_eur=10.0,
        max_position_hold_seconds=60,
        position_must_be_flattened=True,
        require_reduce_only_support=True,
    )


def default_bounded_futures_private_readonly_reachability_v0_spec() -> BoundedFuturesTestnetSpec:
    """Private-readonly reachability profile: no order attempts, no notional."""
    return BoundedFuturesTestnetSpec(
        session_class="bounded-futures-private-readonly-reachability-v0",
        order_policy=DEFAULT_ORDER_POLICY,
        instrument=DEFAULT_INSTRUMENT,
        market_type=DEFAULT_MARKET_TYPE,
        margin_mode=DEFAULT_MARGIN_MODE,
        position_mode=DEFAULT_POSITION_MODE,
        max_leverage=DEFAULT_MAX_LEVERAGE,
        max_real_orders=0,
        max_order_attempts=0,
        max_cancel_attempts=0,
        max_notional_eur=0.0,
        max_position_hold_seconds=300,
        position_must_be_flattened=True,
        require_reduce_only_support=True,
    )


def default_bounded_futures_zero_order_reachability_v0_spec() -> BoundedFuturesTestnetSpec:
    """Zero-order reachability profile: no order attempts, no notional."""
    return BoundedFuturesTestnetSpec(
        session_class=DEFAULT_SESSION_CLASS,
        order_policy=DEFAULT_ORDER_POLICY,
        instrument=DEFAULT_INSTRUMENT,
        market_type=DEFAULT_MARKET_TYPE,
        margin_mode=DEFAULT_MARGIN_MODE,
        position_mode=DEFAULT_POSITION_MODE,
        max_leverage=DEFAULT_MAX_LEVERAGE,
        max_real_orders=0,
        max_order_attempts=0,
        max_cancel_attempts=0,
        max_notional_eur=0.0,
        max_position_hold_seconds=300,
        position_must_be_flattened=True,
        require_reduce_only_support=True,
    )


def spot_evidence_misclassified_as_futures(evidence: dict[str, Any]) -> list[str]:
    """Fail-closed: spot BTC/EUR lineage must not pass futures bounded contract."""
    reasons: list[str] = []
    session_class = evidence.get("session_class")
    if session_class in SPOT_SESSION_CLASSES:
        reasons.append(f"session_class {session_class!r} is spot-tier, not futures")
    instrument = evidence.get("instrument")
    if instrument in REJECTED_FUTURES_INSTRUMENT_PLACEHOLDERS:
        reasons.append(
            f"instrument {instrument!r} is a rejected futures placeholder (use Kraken-native symbol)"
        )
    if instrument in SPOT_INSTRUMENTS:
        reasons.append(f"instrument {instrument!r} is spot, not futures perpetual")
    market_type = evidence.get("market_type")
    if market_type and market_type != DEFAULT_MARKET_TYPE:
        reasons.append(f"market_type must be {DEFAULT_MARKET_TYPE!r}")
    elif market_type is None and instrument in SPOT_INSTRUMENTS:
        reasons.append("market_type required for futures evidence")
    endpoints = evidence.get("endpoints_called") or []
    if isinstance(endpoints, list):
        for ep in endpoints:
            if ep in SPOT_KRAKEN_ENDPOINT_PREFIXES:
                reasons.append(f"spot endpoint not allowed in futures evidence: {ep}")
    if (
        evidence.get("network_host") == "https://api.kraken.com"
        and market_type == DEFAULT_MARKET_TYPE
    ):
        reasons.append("spot kraken.com host must not be used for futures bounded evidence")
    return reasons


def _is_zero_order_reachability_spec(spec: BoundedFuturesTestnetSpec) -> bool:
    return (
        spec.max_real_orders == 0
        and spec.max_order_attempts == 0
        and spec.max_cancel_attempts == 0
        and spec.session_class == DEFAULT_SESSION_CLASS
    )


def _zero_order_network_execution_attempted(evidence: dict[str, Any]) -> bool:
    request_count = evidence.get("request_count")
    if request_count is not None and int(request_count) > 0:
        return True
    network_calls = evidence.get("network_calls")
    if isinstance(network_calls, list) and network_calls:
        return True
    endpoints_called = evidence.get("endpoints_called")
    return isinstance(endpoints_called, list) and bool(endpoints_called)


def _evaluate_zero_order_reachability_gate(
    evidence: dict[str, Any],
    spec: BoundedFuturesTestnetSpec,
) -> tuple[list[str], dict[str, bool]]:
    """Fail-closed reachability gate for zero-order execute-network evidence."""
    flags = {
        "network_reachability_pass": False,
        "required_public_endpoints_2xx_pass": False,
        "bound_instrument_present_pass": False,
    }
    if not _is_zero_order_reachability_spec(spec):
        return [], flags
    if not _zero_order_network_execution_attempted(evidence):
        return [], flags

    fail_reasons: list[str] = []
    if evidence.get("network_reachability_proven") is not True:
        fail_reasons.append("network_reachability_proven must be true")

    endpoints_called = evidence.get("endpoints_called") or []
    if not isinstance(endpoints_called, list):
        fail_reasons.append("endpoints_called must be a list")
        endpoints_called = []
    missing_endpoints = [
        ep for ep in ZERO_ORDER_REQUIRED_PUBLIC_ENDPOINTS if ep not in endpoints_called
    ]
    if missing_endpoints:
        fail_reasons.append(
            "required zero-order public endpoints missing: " + ", ".join(sorted(missing_endpoints))
        )

    network_calls = evidence.get("network_calls") or []
    if not isinstance(network_calls, list):
        fail_reasons.append("network_calls must be a list")
        network_calls = []

    endpoint_statuses: dict[str, int] = {}
    for call in network_calls:
        if not isinstance(call, dict):
            fail_reasons.append("network_calls entries must be objects")
            continue
        endpoint = call.get("endpoint")
        status = call.get("http_status")
        if not isinstance(endpoint, str) or not isinstance(status, int):
            fail_reasons.append("network_calls entry missing endpoint or http_status")
            continue
        endpoint_statuses[endpoint] = status
        if not (200 <= status < 300):
            fail_reasons.append(f"required endpoint {endpoint!r} returned non-2xx HTTP {status}")
        if int(call.get("response_size_bytes") or 0) <= 0:
            fail_reasons.append(f"required endpoint {endpoint!r} returned empty body")

    for required_ep in ZERO_ORDER_REQUIRED_PUBLIC_ENDPOINTS:
        if required_ep not in endpoint_statuses:
            fail_reasons.append(f"required endpoint {required_ep!r} missing from network_calls")

    flags["required_public_endpoints_2xx_pass"] = not missing_endpoints and all(
        200 <= endpoint_statuses.get(ep, 0) < 300 for ep in ZERO_ORDER_REQUIRED_PUBLIC_ENDPOINTS
    )

    visibility = evidence.get("pf_xbtusd_symbol_visibility")
    if visibility != "visible":
        fail_reasons.append(
            f"bound instrument {spec.instrument!r} must be visible in instruments evidence "
            f"(got {visibility!r})"
        )
    flags["bound_instrument_present_pass"] = visibility == "visible"

    flags["network_reachability_pass"] = (
        evidence.get("network_reachability_proven") is True
        and flags["required_public_endpoints_2xx_pass"]
        and flags["bound_instrument_present_pass"]
        and not any(
            reason.startswith("required endpoint") or reason.startswith("network_calls")
            for reason in fail_reasons
        )
    )
    return fail_reasons, flags


def evaluate_bounded_futures_testnet_evidence(
    evidence: dict[str, Any],
    spec: BoundedFuturesTestnetSpec | None = None,
) -> dict[str, Any]:
    """Fail-closed bounded futures testnet evaluation (offline, no I/O)."""
    spec = spec or default_bounded_futures_normal_v0_spec()
    result: dict[str, Any] = {
        "bounded_futures_testnet_pass": False,
        "futures_instrument_pass": False,
        "futures_endpoint_isolation_pass": False,
        "margin_leverage_pass": False,
        "position_mode_pass": False,
        "order_cap_pass": False,
        "cancel_flatten_pass": False,
        "risk_killswitch_scope_pass": False,
        "master_v2_boundary_pass": False,
        "safety_execution_pass": False,
        "harness_contract_pass": False,
        "network_reachability_pass": False,
        "required_public_endpoints_2xx_pass": False,
        "bound_instrument_present_pass": False,
        "zero_order_objective_complete": False,
        "next_phase_ready": False,
        "fail_reasons": [],
    }

    for field in REQUIRED_FUTURES_EVIDENCE_FIELD_NAMES:
        if field not in evidence:
            result["fail_reasons"].append(f"missing required field: {field}")

    result["fail_reasons"].extend(spot_evidence_misclassified_as_futures(evidence))

    if evidence.get("session_class") != spec.session_class:
        result["fail_reasons"].append(
            f"session_class must be {spec.session_class!r} (got {evidence.get('session_class')!r})"
        )
    if evidence.get("order_policy") != spec.order_policy:
        result["fail_reasons"].append(
            f"order_policy must be {spec.order_policy!r} (got {evidence.get('order_policy')!r})"
        )
    if evidence.get("instrument") != spec.instrument:
        result["fail_reasons"].append(
            f"instrument must be {spec.instrument!r} (got {evidence.get('instrument')!r})"
        )
    if evidence.get("market_type") != spec.market_type:
        result["fail_reasons"].append(
            f"market_type must be {spec.market_type!r} (got {evidence.get('market_type')!r})"
        )

    margin_mode = evidence.get("margin_mode")
    if margin_mode != spec.margin_mode:
        result["fail_reasons"].append(
            f"margin_mode must be {spec.margin_mode!r} (got {margin_mode!r})"
        )
    if margin_mode == "cross":
        result["fail_reasons"].append("cross margin not allowed unless explicitly governed")

    max_lev = evidence.get("max_leverage")
    if max_lev is not None and float(max_lev) > spec.max_leverage:
        result["fail_reasons"].append("max_leverage exceeds cap")
    if not evidence.get("leverage_within_cap"):
        result["fail_reasons"].append("leverage_within_cap must be true")

    if evidence.get("position_mode") != spec.position_mode:
        result["fail_reasons"].append(
            f"position_mode must be {spec.position_mode!r} (got {evidence.get('position_mode')!r})"
        )

    side_sem = evidence.get("order_side_semantics")
    if side_sem not in ("long", "short", "long_or_short_bounded"):
        result["fail_reasons"].append("order_side_semantics must be long/short bounded")

    if spec.require_reduce_only_support and not evidence.get("reduce_only_supported"):
        result["fail_reasons"].append("reduce_only_supported must be true")

    if not evidence.get("futures_endpoint_isolation_pass"):
        result["fail_reasons"].append("futures_endpoint_isolation_pass must be true")
    if not evidence.get("spot_endpoint_isolation_pass"):
        result["fail_reasons"].append("spot_endpoint_isolation_pass must be true")

    if not evidence.get("funding_risk_acknowledged"):
        result["fail_reasons"].append("funding_risk_acknowledged must be true")
    if not evidence.get("liquidation_risk_acknowledged"):
        result["fail_reasons"].append("liquidation_risk_acknowledged must be true")

    order_attempts = evidence.get("order_attempt_count")
    if order_attempts is not None and order_attempts > spec.max_order_attempts:
        result["fail_reasons"].append("order_attempt_count exceeds cap")
    real_orders = evidence.get("real_orders_created_count")
    if real_orders is not None and real_orders > spec.max_real_orders:
        result["fail_reasons"].append("real_orders_created_count exceeds cap")
    cancel_attempts = evidence.get("cancel_or_close_attempt_count")
    if cancel_attempts is not None and cancel_attempts > spec.max_cancel_attempts:
        result["fail_reasons"].append("cancel_or_close_attempt_count exceeds cap")

    notional = evidence.get("order_notional_eur")
    if notional is not None and float(notional) > spec.max_notional_eur:
        result["fail_reasons"].append("order_notional_eur exceeds cap")

    if real_orders and int(real_orders) > 0:
        if not evidence.get("cancel_or_close_evidence_valid"):
            result["fail_reasons"].append("cancel_or_close_evidence_valid required")
    if spec.position_must_be_flattened and not evidence.get("position_flattened_by_end"):
        result["fail_reasons"].append("position_flattened_by_end required")

    if evidence.get("master_v2_double_play_authority_used"):
        result["fail_reasons"].append("master_v2_double_play_authority_used must be false")

    if evidence.get("scheduler_started"):
        result["fail_reasons"].append("scheduler_started must be false")
    if evidence.get("runtime_started"):
        result["fail_reasons"].append("runtime_started must be false")
    if evidence.get("live_env_present"):
        result["fail_reasons"].append("live_env_present must be false")
    if evidence.get("futures_session_authorized_now"):
        result["fail_reasons"].append("futures_session_authorized_now must be false")

    if evidence.get("fetch_failure"):
        result["fail_reasons"].append("private_readonly_fetch_failure")

    result["futures_instrument_pass"] = evidence.get("instrument") == spec.instrument
    result["futures_endpoint_isolation_pass"] = (
        evidence.get("futures_endpoint_isolation_pass") is True
        and evidence.get("spot_endpoint_isolation_pass") is True
        and not any(
            ep in SPOT_KRAKEN_ENDPOINT_PREFIXES
            for ep in (evidence.get("endpoints_called") or [])
            if isinstance(evidence.get("endpoints_called"), list)
        )
    )
    result["margin_leverage_pass"] = (
        margin_mode == spec.margin_mode
        and evidence.get("leverage_within_cap") is True
        and (max_lev is None or float(max_lev) <= spec.max_leverage)
    )
    result["position_mode_pass"] = evidence.get("position_mode") == spec.position_mode
    result["order_cap_pass"] = (
        order_attempts is not None
        and order_attempts <= spec.max_order_attempts
        and real_orders is not None
        and real_orders <= spec.max_real_orders
    )
    result["cancel_flatten_pass"] = evidence.get("position_flattened_by_end") is True
    result["risk_killswitch_scope_pass"] = evidence.get("risk_killswitch_scope_pass") is True
    result["master_v2_boundary_pass"] = not evidence.get("master_v2_double_play_authority_used")

    safety_fail_reasons = list(result["fail_reasons"])
    result["safety_execution_pass"] = not safety_fail_reasons
    result["harness_contract_pass"] = result["safety_execution_pass"]

    reachability_fail_reasons, reachability_flags = _evaluate_zero_order_reachability_gate(
        evidence,
        spec,
    )
    result.update(reachability_flags)
    result["fail_reasons"].extend(reachability_fail_reasons)

    zero_order_objective_complete = (
        _is_zero_order_reachability_spec(spec)
        and _zero_order_network_execution_attempted(evidence)
        and not reachability_fail_reasons
    )
    result["zero_order_objective_complete"] = zero_order_objective_complete
    result["next_phase_ready"] = zero_order_objective_complete

    result["bounded_futures_testnet_pass"] = not result["fail_reasons"]
    return result
