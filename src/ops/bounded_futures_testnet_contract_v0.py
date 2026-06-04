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
DEFAULT_INSTRUMENT = "PF_XBTUSD"
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

    result["bounded_futures_testnet_pass"] = not result["fail_reasons"]
    return result
