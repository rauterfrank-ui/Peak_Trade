"""Repo-native bounded network Testnet preflight contract (v0).

Offline fail-closed evaluator for bounded network Testnet preflight evidence.
Does not authorize Testnet execute, network access, credentials, or runtime start.
Charter: bounded_network_testnet_preflight_charter_no_run_v0_20260603T184700Z
"""

from __future__ import annotations

from typing import Any

from src.ops.wallclock_session_evidence_v0 import evaluate_wallclock_evidence_fields

PACKAGE_MARKER = "BOUNDED_NETWORK_TESTNET_PREFLIGHT_CONTRACT_V0=true"
CLASS4_SCOPED_EXCEPTION_MARKER = (
    "BOUNDED_NETWORK_TESTNET_PREFLIGHT_GUARD_CLASS4_SCOPED_EXCEPTION_V0=true"
)
CHARTER_BUNDLE_SUFFIX = "bounded_network_testnet_preflight_charter_no_run_v0_20260603T184700Z"
REQUIRED_EXECUTE_GO = "GO_EXECUTE_BOUNDED_NETWORK_TESTNET_PREFLIGHT_V0"

PUBLIC_ENDPOINTS: frozenset[str] = frozenset(
    {
        "/0/public/Time",
        "/0/public/Ticker",
        "/0/public/AssetPairs",
    }
)
PRIVATE_READONLY_ENDPOINTS: frozenset[str] = frozenset(
    {
        "/0/private/Balance",
        "/0/private/OpenOrders",
    }
)
FORBIDDEN_ORDER_ENDPOINTS: frozenset[str] = frozenset(
    {
        "/0/private/AddOrder",
        "/0/private/CancelOrder",
        "/0/private/AmendOrder",
        "/0/private/QueryOrders",
        "/0/private/TradeBalance",
    }
)
HOST_ALLOWLIST: frozenset[str] = frozenset({"https://api.kraken.com"})

PREFLIGHT_PLANNED_DURATION_SECONDS = 120
PREFLIGHT_MIN_REQUIRED_WALL_CLOCK_SECONDS = 60
PREFLIGHT_MAX_ACCEPTABLE_WALL_CLOCK_SECONDS = 180
PREFLIGHT_WALL_CLOCK_SLACK_SECONDS = 60
MAX_PUBLIC_CALLS = 8
MAX_PRIVATE_READONLY_CALLS = 4
MAX_REAL_ORDER_CALLS = 0
MIN_HEARTBEATS_REQUIRED = 2
MIN_HEARTBEAT_SPAN_SECONDS = 30


def evaluate_bounded_network_testnet_preflight_evidence(
    evidence: dict[str, Any],
) -> dict[str, Any]:
    """Fail-closed reference evaluator for future network preflight closeout (offline)."""
    result: dict[str, Any] = {
        "preflight_evidence_valid": False,
        "network_preflight_evidence_valid": False,
        "fail_reasons": [],
    }

    if evidence.get("operator_go") != REQUIRED_EXECUTE_GO:
        result["fail_reasons"].append("missing or wrong operator_go (explicit execute GO required)")

    if evidence.get("orders_allowed") is True:
        result["fail_reasons"].append("orders_allowed must be false (AB2)")
    if evidence.get("positions_allowed") is True:
        result["fail_reasons"].append("positions_allowed must be false")
    if evidence.get("scheduler_allowed") is True:
        result["fail_reasons"].append("scheduler_allowed must be false (AB6)")
    if evidence.get("runtime_allowed") is True:
        result["fail_reasons"].append("runtime_allowed must be false (AB6)")
    if evidence.get("testnet_session_allowed") is True:
        result["fail_reasons"].append("testnet_session_allowed must be false (AB5)")

    if evidence.get("credential_values_exported") is True:
        result["fail_reasons"].append("credential values exported (AB1/AB8)")
    if evidence.get("credentials_printed") is True:
        result["fail_reasons"].append("credentials printed (AB1)")

    host = evidence.get("network_host")
    if host and host not in HOST_ALLOWLIST:
        result["fail_reasons"].append(f"non-allowlisted network host (AB4): {host!r}")

    endpoints_called = evidence.get("endpoints_called") or []
    for endpoint in endpoints_called:
        if endpoint in FORBIDDEN_ORDER_ENDPOINTS:
            result["fail_reasons"].append(f"forbidden order endpoint called (AB2/AB3): {endpoint}")
        elif endpoint not in PUBLIC_ENDPOINTS and endpoint not in PRIVATE_READONLY_ENDPOINTS:
            result["fail_reasons"].append(f"non-allowlisted endpoint (AB4): {endpoint}")

    if evidence.get("validate_only_addorder_used") is True:
        result["fail_reasons"].append("validate_only AddOrder forbidden for preflight")

    max_order_calls = evidence.get("max_real_order_calls")
    if max_order_calls is not None and max_order_calls > MAX_REAL_ORDER_CALLS:
        result["fail_reasons"].append("MAX_REAL_ORDER_CALLS > 0 (AB16)")

    public_calls = evidence.get("public_calls", 0)
    private_calls = evidence.get("private_readonly_calls", 0)
    if public_calls > MAX_PUBLIC_CALLS:
        result["fail_reasons"].append("public calls exceed allowlist max (AB18)")
    if private_calls > MAX_PRIVATE_READONLY_CALLS:
        result["fail_reasons"].append("private readonly calls exceed allowlist max (AB19)")

    heartbeats = evidence.get("heartbeat_count", 0)
    heartbeat_span = evidence.get("heartbeat_span_seconds", 0)
    if heartbeats < MIN_HEARTBEATS_REQUIRED:
        result["fail_reasons"].append("insufficient heartbeats (AB20)")
    if heartbeat_span < MIN_HEARTBEAT_SPAN_SECONDS:
        result["fail_reasons"].append("heartbeat span below minimum (AB20)")

    if evidence.get("run_testnet_session_invoked") is True:
        result["fail_reasons"].append("run_testnet_session invoked (AB5)")

    for side_effect in (
        "preflight_lifted",
        "arming_changed",
        "bl002_path_b_touched",
        "shadow_hold_lifted",
    ):
        if evidence.get(side_effect) is True:
            result["fail_reasons"].append(f"forbidden side effect: {side_effect} (AB7)")

    if evidence.get("manifest_present") is False:
        result["fail_reasons"].append("missing MANIFEST.sha256 (AB23)")
    if evidence.get("manifest_verify_rc", 0) != 0:
        result["fail_reasons"].append("MANIFEST_VERIFY_RC != 0 (AB24)")
    if evidence.get("final_machine_lines_present") is False:
        result["fail_reasons"].append("missing FINAL_MACHINE_LINES.txt (AB25)")
    if evidence.get("evidence_root_under_tmp_only") is True:
        result["fail_reasons"].append("evidence root under /tmp only (AB26)")

    wallclock = evaluate_wallclock_evidence_fields(evidence)
    result["fail_reasons"].extend(wallclock["fail_reasons"])

    if not result["fail_reasons"]:
        result["preflight_evidence_valid"] = True
        result["network_preflight_evidence_valid"] = True

    return result
