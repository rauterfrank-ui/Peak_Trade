"""
VaR Backtest Suite Report Formatter.

Generates deterministic JSON and Markdown reports for VaR backtest suite results.

Phase 8C: Suite Report & Regression Guard
"""

import json
from typing import Dict, Any

from .suite_runner import VaRBacktestSuiteResult


def format_suite_result_json(result: VaRBacktestSuiteResult) -> str:
    """
    Format suite result as deterministic JSON.

    Args:
        result: VaRBacktestSuiteResult instance

    Returns:
        JSON string (pretty-printed, stable key order, fixed precision)

    Example:
        >>> result = VaRBacktestSuiteResult(...)
        >>> json_str = format_suite_result_json(result)
        >>> print(json_str)
        {
          "overall_result": "PASS",
          ...
        }
    """
    # Build dict with stable key ordering (alphabetical within sections)
    # Convert numpy/pandas int64 to native Python int for JSON serialization
    data: Dict[str, Any] = {
        "suite_metadata": {
            "breaches": int(result.breaches),
            "confidence_level": float(result.confidence_level),
            "observations": int(result.observations),
        },
        "test_results": {
            "basel_traffic_light": {
                "result": result.basel_traffic_light,
            },
            "christoffersen_cc": {
                "p_value": result.christoffersen_cc_pvalue,
                "result": result.christoffersen_cc_result,
            },
            "christoffersen_ind": {
                "p_value": result.christoffersen_ind_pvalue,
                "result": result.christoffersen_ind_result,
            },
            "kupiec_pof": {
                "p_value": result.kupiec_pof_pvalue,
                "result": result.kupiec_pof_result,
            },
        },
        "overall_result": result.overall_result,
    }

    return json.dumps(data, indent=2, sort_keys=False)


def format_suite_result_markdown(result: VaRBacktestSuiteResult) -> str:
    """
    Format suite result as human-readable Markdown.

    Args:
        result: VaRBacktestSuiteResult instance

    Returns:
        Markdown string (deterministic formatting)

    Example:
        >>> result = VaRBacktestSuiteResult(...)
        >>> md_str = format_suite_result_markdown(result)
        >>> print(md_str)
        # VaR Backtest Suite Report
        ...
    """
    # Determine emoji for overall result
    emoji = "✅" if result.overall_result == "PASS" else "❌"

    lines = [
        "# VaR Backtest Suite Report",
        "",
        f"**Overall Result:** {emoji} {result.overall_result}",
        "",
        "---",
        "",
        "## Suite Metadata",
        "",
        f"- **Observations:** {result.observations}",
        f"- **Breaches:** {result.breaches}",
        f"- **Confidence Level:** {result.confidence_level:.2%}",
        "",
        "---",
        "",
        "## Test Results",
        "",
        "| Test | Result | Details |",
        "|------|--------|---------|",
        f"| Kupiec POF | {_format_result_badge(result.kupiec_pof_result)} | p-value: {result.kupiec_pof_pvalue:.6f} |",
        f"| Basel Traffic Light | {_format_traffic_light_badge(result.basel_traffic_light)} | Color: {result.basel_traffic_light} |",
        f"| Christoffersen IND | {_format_result_badge(result.christoffersen_ind_result)} | p-value: {result.christoffersen_ind_pvalue:.6f} |",
        f"| Christoffersen CC | {_format_result_badge(result.christoffersen_cc_result)} | p-value: {result.christoffersen_cc_pvalue:.6f} |",
        "",
        "---",
        "",
        "## Interpretation",
        "",
        _generate_interpretation(result),
        "",
    ]

    return "\n".join(lines)


def _format_result_badge(result: str) -> str:
    """Format test result as badge (PASS ✅ / FAIL ❌)."""
    if result == "PASS":
        return "✅ PASS"
    else:
        return "❌ FAIL"


def _format_traffic_light_badge(color: str) -> str:
    """Format Basel Traffic Light as badge with emoji."""
    if color == "GREEN":
        return "🟢 GREEN"
    elif color == "YELLOW":
        return "🟡 YELLOW"
    else:
        return "🔴 RED"


def _generate_interpretation(result: VaRBacktestSuiteResult) -> str:
    """Generate interpretation section based on test results."""
    lines = []

    # Overall assessment
    if result.overall_result == "PASS":
        lines.append("**Summary:** All tests passed. VaR model appears well-calibrated.")
        lines.append("")
        lines.append("- **Kupiec POF:** Breach rate statistically consistent with confidence level")
        lines.append("- **Basel Traffic Light:** GREEN zone (acceptable breach count)")
        lines.append(
            "- **Christoffersen IND:** Breaches are temporally independent (no clustering)"
        )
        lines.append(
            "- **Christoffersen CC:** Combined unconditional coverage + independence validated"
        )
    else:
        lines.append("**Summary:** One or more tests failed. VaR model requires review.")
        lines.append("")

        # Detail failures
        if result.kupiec_pof_result == "FAIL":
            lines.append(
                "- **Kupiec POF FAIL:** Breach rate significantly differs from expected level"
            )

        if result.basel_traffic_light != "GREEN":
            lines.append(
                f"- **Basel Traffic Light {result.basel_traffic_light}:** Breach count exceeds GREEN zone threshold"
            )

        if result.christoffersen_ind_result == "FAIL":
            lines.append(
                "- **Christoffersen IND FAIL:** Breaches show temporal clustering (not independent)"
            )

        if result.christoffersen_cc_result == "FAIL":
            lines.append(
                "- **Christoffersen CC FAIL:** Conditional coverage test rejected (UC or IND failure)"
            )

    return "\n".join(lines)
