"""P1 time-domain completeness witness for bound negative closeout (offline).

Derives TIME_DOMAIN_COMPLETE for P1 from ratified bound-query traversal inputs,
not from venue full-history traversal or genesis-point D5 window alone.
No GET. AUTHORITY_EFFECT=NONE.

RUNTIME_AUTHORIZATION_EFFECT=NONE
"""

from __future__ import annotations

from typing import Any, Mapping

WP_ID = "FULL_CORE_P1_FINAL_CLOSEOUT_PR1_OF_2_V1"
SCHEMA_CLASS = "P1_TIME_DOMAIN_COMPLETENESS_WITNESS_V1"
CONTRACT_VERSION = "v1"
AUTHORITY_EFFECT = "NONE"
FALSE_TOKEN = "false"
TRUE_TOKEN = "true"
NONE_TOKEN = "NONE"
_TIME_DOMAIN_SEMANTICS = (
    "P1_BOUND_INTEREST_ACCRUED_QUERY_SNAPSHOT_EXHAUSTION_AT_ACQUISITION_TIME_"
    "NOT_VENUE_DEFAULT_PAST_YEAR_FULL_TRAVERSAL"
)


class P1TimeDomainCompletenessWitnessError(ValueError):
    """Fail-closed P1 time-domain completeness witness violation."""


def _as_bool_token(value: object) -> bool:
    return str(value or "").lower() == TRUE_TOKEN


def build_p1_time_domain_completeness_witness_adjudication_v1(
    *,
    traversal_adjudication: Mapping[str, Any],
    cd_claims: Mapping[str, Any],
    usdc_claims: Mapping[str, Any],
    reopen_adjudication: Mapping[str, Any],
) -> dict[str, Any]:
    if not _as_bool_token(
        traversal_adjudication.get("P1_PAGINATION_QUERY_TRAVERSAL_EXHAUSTION_PROVEN")
    ):
        return _time_fail("PAGINATION_QUERY_TRAVERSAL_NOT_PROVEN")
    if (
        str(cd_claims.get("HTTP_STATUS", "")) != "200"
        or str(usdc_claims.get("HTTP_STATUS", "")) != "200"
    ):
        return _time_fail("SEALED_BOUND_GET_NOT_BOTH_HTTP_200")
    if str(reopen_adjudication.get("CD_CURSOR_USED", "")).lower() == TRUE_TOKEN:
        return _time_fail("CURSOR_USED_WITHOUT_EXHAUSTION_WITNESS")

    cd_ts = str(reopen_adjudication.get("CD_ACQUISITION_TIMESTAMP", ""))
    usdc_raw_ts = str(usdc_claims.get("PERSIST_AS_OF", ""))
    if not cd_ts or not usdc_raw_ts:
        return _time_fail("BOUND_QUERY_ACQUISITION_TIMESTAMPS_INCOMPLETE")

    return {
        "layer": "CANONICAL_AUTHORITY",
        "WP_ID": WP_ID,
        "SCHEMA_CLASS": SCHEMA_CLASS,
        "P1_TIME_DOMAIN_EXHAUSTION_PROVEN": TRUE_TOKEN,
        "P1_TIME_DOMAIN_DETAIL": (
            "P1 bound interest-accrued CD and USDC scoped queries both executed; "
            "pagination query traversal proven; time domain exhausted for bound "
            "single-page limit-only snapshots at acquisition timestamps "
            f"(CD={cd_ts}, USDC pack={usdc_raw_ts}); not venue past-year traversal"
        ),
        "TIME_DOMAIN_MISSING_FACT": NONE_TOKEN,
        "TIME_DOMAIN_SEMANTICS": _TIME_DOMAIN_SEMANTICS,
        "CD_TIME_SCOPE_ANNOTATION": str(reopen_adjudication.get("CD_TIME_SCOPE", "")),
        "CD_TIME_SCOPE_IS_NOT_P1_COMPLETENESS_CLAIM": TRUE_TOKEN,
    }


def _time_fail(detail: str) -> dict[str, Any]:
    return {
        "layer": "CANONICAL_AUTHORITY",
        "WP_ID": WP_ID,
        "SCHEMA_CLASS": SCHEMA_CLASS,
        "P1_TIME_DOMAIN_EXHAUSTION_PROVEN": FALSE_TOKEN,
        "P1_TIME_DOMAIN_DETAIL": detail,
        "TIME_DOMAIN_MISSING_FACT": detail,
        "TIME_DOMAIN_SEMANTICS": _TIME_DOMAIN_SEMANTICS,
        "CD_TIME_SCOPE_IS_NOT_P1_COMPLETENESS_CLAIM": TRUE_TOKEN,
    }


__all__ = [
    "AUTHORITY_EFFECT",
    "CONTRACT_VERSION",
    "P1TimeDomainCompletenessWitnessError",
    "SCHEMA_CLASS",
    "WP_ID",
    "build_p1_time_domain_completeness_witness_adjudication_v1",
]
