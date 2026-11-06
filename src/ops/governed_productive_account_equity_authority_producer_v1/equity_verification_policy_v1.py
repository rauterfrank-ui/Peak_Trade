"""Local verification policy. Never round the native ledger or authorize money.

The cap bounds presentation loss; it is not fuzzy equality. An observed string
must still equal the exact Decimal value or the named deterministic rendering.
No assertion about the venue's internal numeric implementation is made.
"""

from decimal import Decimal, localcontext
from pathlib import Path

from src.ops.governed_productive_account_equity_authority_producer_v1.real_equity_journal_v1 import (
    unique_json_v1,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.real_equity_replay_v1 import (
    amount_v1,
    compare_native_display_v1,
)
from src.ops.okx_eea_private_account_state_runtime_v1.bills_observation_v1 import (
    canonical_digest_v1,
)


def load_equity_verification_policy_v1(path):
    policy = unique_json_v1(Path(path).read_bytes())
    return validate_equity_verification_policy_v1(policy)


def validate_equity_verification_policy_v1(policy):
    pins = {
        "schema": "peaktrade.equity_verification_policy.v1",
        "comparison_mode": "EXACT_LEDGER_BOUNDED_BINARY64_DISPLAY",
        "unknown_currency": "EXACT_ONLY",
        "ledger_adjustments_allowed": False,
        "runtime_activation_authorized": False,
        "capital_admission_authorized": False,
        "real_continuous_observation_required": True,
    }
    if not isinstance(policy, dict) or set(policy) != set(pins) | {"max_display_gap_native"}:
        raise ValueError("EQUITY_POLICY_FIELDS_INVALID")
    if any(type(policy[k]) is not type(v) or policy[k] != v for k, v in pins.items()):
        raise ValueError("EQUITY_POLICY_SCOPE_INVALID")
    caps = policy["max_display_gap_native"]
    if (
        not isinstance(caps, dict)
        or set(caps) != {"USDC", "EUR", "BTC"}
        or any(not Decimal("0") < amount_v1(v) <= Decimal("0.000000000001") for v in caps.values())
    ):
        raise ValueError("EQUITY_POLICY_DISPLAY_CAP_INVALID")
    return policy


def _comparison_allowed(comparison, currency, policy):
    # Recompute; never trust a supplied diagnostic boolean to grant a PASS.
    exact = amount_v1(comparison["exact_decimal"])
    observed = comparison["observed_decimal"]
    computed = compare_native_display_v1(exact, observed)
    if computed["exact_equal"]:
        return True
    cap = policy["max_display_gap_native"].get(currency)
    return bool(
        cap is not None
        and computed["binary64_shortest_rendering_matches"]
        and abs(amount_v1(computed["observed_minus_exact"])) <= amount_v1(cap)
    )


def assess_equity_window_v1(result, policy):
    """Return a separate local decision, preserving the original full result."""
    with localcontext() as context:
        context.prec = 120
        return _assess(result, validate_equity_verification_policy_v1(policy))


def _assess(result, policy):
    if result.get("schema") != "peaktrade.real_equity_window_reconciliation.v1":
        raise ValueError("EQUITY_ASSESSMENT_SOURCE_INVALID")
    blockers = []
    required_true = (
        "historical_anchor_and_current_account_joined",
        "archive_and_recent_endpoint_pagination_exhausted",
        "retention_window_checked_under_89_days",
        "all_observed_window_trading_rows_classified",
        "current_positions_flat_observed_twice",
    )
    if any(result.get(k) is not True for k in required_true):
        blockers.append("OBSERVED_WINDOW_PRECONDITIONS_UNPROVEN")
    checks = [("OPENING_EQUITY", "USDC", result["initial_equity_display_comparison"])]
    for row in result["trading_currencies"]:
        for name in ("opening_published_cash_comparison", "end_published_equity_comparison"):
            if row[name] is not None:
                checks.append((name, row["currency"], row[name]))
    funding = result["funding"]
    differences = {}
    for comparison in funding["counterpart_representation_comparisons"]:
        currency = comparison["currency"]
        checks.append(("FUNDING_COUNTERPART", currency, comparison))
        differences[currency] = differences.get(currency, Decimal("0")) + amount_v1(
            comparison["observed_minus_exact"]
        )
    if funding["all_counterparty_flow_reconstructions_exact"] is not True:
        blockers.append("FUNDING_CONSERVATION_UNPROVEN")
    for row in funding["currency_balances"]:
        if amount_v1(row["observed_minus_replayed"]) != -differences.get(
            row["currency"], Decimal("0")
        ):
            blockers.append("FUNDING_RESIDUAL_NOT_EXPLAINED_BY_COUNTERPARTS")
    for label, currency, comparison in checks:
        if not _comparison_allowed(comparison, currency, policy):
            blockers.append("UNEXPLAINED_OR_EXCESSIVE_DISPLAY_GAP:" + label + ":" + currency)
    return {
        "schema": "peaktrade.equity_internal_assessment.v1",
        "policy_digest": canonical_digest_v1(policy),
        "source_result_digest": canonical_digest_v1(result),
        "status": "LOCAL_VERIFICATION_PASS_RUNTIME_BLOCKED"
        if not blockers
        else "LOCAL_VERIFICATION_BLOCKED",
        "comparison_count": len(checks),
        "blockers": sorted(set(blockers)),
        "native_ledger_modified": False,
        "venue_numeric_contract_assumed": False,
        "real_continuous_observation_proven": False,
        "runtime_activation_authorized": False,
        "capital_admitted": False,
    }
