"""Offline bundle from retained GET captures into the existing admission validator.

AUTHORITY_EFFECT=NONE. This module does not call OKX, open a socket, write
portfolio state, or decide admission by itself. The only admission decision is
``validate_get_evidence_admission_v1``.

CURRENT reconciliation marks history and fills incomplete when a page reaches
its requested limit. No positive, endpoint-specific terminal condition is
defined for the six admission GETs. Pagination therefore stays UNPROVEN.
A short page is not treated as a complete history. Synthetic validator input
is explicit and is not an OKX terminal witness.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, Mapping

from src.ops.h1_get_evidence_admission_v1.constants_v1 import (
    ENDPOINT_ACCOUNT_POSITIONS,
    ENDPOINT_FILLS,
    ENDPOINT_ORDERS_HISTORY,
    ENDPOINT_ORDERS_PENDING,
    PAGINATED_ENDPOINTS,
)
from src.ops.h1_get_evidence_admission_v1.validate_v1 import (
    AdmissionParametersV1,
    AdmissionResultV1,
    CapturedGetResponseV1,
    validate_get_evidence_admission_v1,
)
from src.ops.okx_eea_private_account_state_runtime_v1.rest_baseline_v1 import (
    AdmissionRawCaptureV1,
    RestGetJson,
    admission_capture_record_v1,
    assert_get_path_allowlisted_v1,
    assert_no_rest_post_v1,
    explicit_captured_at_ms_v1,
)

OFFLINE_PAGE_BUDGET_V1 = 3
PAGINATION_TERMINAL_UNPROVEN = "UNPROVEN"
STATUS_UNPROVEN = PAGINATION_TERMINAL_UNPROVEN
STATUS_REPEATED_CURSOR = "REPEATED_CURSOR"
STATUS_CONTRADICTORY_PAGES = "CONTRADICTORY_PAGES"
STATUS_PAGE_BUDGET_EXCEEDED = "PAGE_BUDGET_EXCEEDED"

_TIME_FIELDS = ("uTime", "cTime")
_ROW_IDENTITY = {
    ENDPOINT_ACCOUNT_POSITIONS: "instId",
    ENDPOINT_ORDERS_PENDING: "ordId",
    ENDPOINT_ORDERS_HISTORY: "ordId",
    ENDPOINT_FILLS: "tradeId",
}


@dataclass(frozen=True)
class PaginationAssessmentV1:
    status: str
    page_row_count: int | None
    request_limit: int | None
    observed_cursor: str | None
    next_cursor: str | None
    pagination_terminal: bool | None
    pagination_terminal_source: str | None
    single_page: bool


def current_contract_next_cursor_v1(payload: Mapping[str, Any]) -> str | None:
    """No CURRENT six-GET contract exposes a positive next-cursor field."""
    del payload
    return None


def _positive_ms(value: object) -> int | None:
    if isinstance(value, bool) or isinstance(value, float):
        return None
    if isinstance(value, int):
        return value if value > 0 else None
    if isinstance(value, str) and value.isdigit():
        parsed = int(value)
        return parsed if parsed > 0 else None
    return None


def venue_timestamp_from_payload_v1(payload: Mapping[str, Any]) -> int | None:
    """Return one positive uTime/cTime. Zero, absent, or disagreeing values stay unset."""
    found: set[int] = set()
    data = payload.get("data")
    if not isinstance(data, list):
        return None
    for row in data:
        if not isinstance(row, Mapping):
            continue
        for key in _TIME_FIELDS:
            if key not in row:
                continue
            parsed = _positive_ms(row.get(key))
            if parsed is not None:
                found.add(parsed)
    if len(found) == 1:
        return next(iter(found))
    return None


def _canonical_row(row: Mapping[str, Any]) -> str:
    return json.dumps(dict(row), sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def _cursor_values(pages: tuple[AdmissionRawCaptureV1, ...]) -> list[str]:
    values: list[str] = []
    for page in pages:
        cursor = page.observed_cursor
        if isinstance(cursor, str) and cursor != "":
            values.append(cursor)
    return values


def _pages_contradict(endpoint: str, pages: tuple[AdmissionRawCaptureV1, ...]) -> bool:
    identity = _ROW_IDENTITY.get(endpoint)
    if identity is None:
        return False
    seen: dict[str, str] = {}
    for page in pages:
        data = page.payload.get("data")
        if not isinstance(data, list):
            continue
        for row in data:
            if not isinstance(row, Mapping) or identity not in row:
                continue
            key = row.get(identity)
            if not isinstance(key, str) or key == "":
                continue
            try:
                canonical = _canonical_row(row)
            except TypeError:
                return True
            previous = seen.get(key)
            if previous is None:
                seen[key] = canonical
            elif previous != canonical:
                return True
    return False


def assess_pagination_v1(
    endpoint: str,
    pages: tuple[AdmissionRawCaptureV1, ...],
    *,
    page_budget: int = OFFLINE_PAGE_BUDGET_V1,
) -> PaginationAssessmentV1:
    """Classify a page chain. A positive terminal is never inferred."""
    first = pages[0] if pages else None
    base = PaginationAssessmentV1(
        status=STATUS_UNPROVEN,
        page_row_count=None if first is None else first.page_row_count,
        request_limit=None if first is None else first.request_limit,
        observed_cursor=None if first is None else first.observed_cursor,
        next_cursor=None if first is None else first.next_cursor,
        pagination_terminal=None,
        pagination_terminal_source=None,
        single_page=len(pages) == 1,
    )
    if len(pages) > page_budget:
        return PaginationAssessmentV1(
            status=STATUS_PAGE_BUDGET_EXCEEDED,
            page_row_count=base.page_row_count,
            request_limit=base.request_limit,
            observed_cursor=base.observed_cursor,
            next_cursor=base.next_cursor,
            pagination_terminal=None,
            pagination_terminal_source=None,
            single_page=False,
        )
    cursors = _cursor_values(pages)
    if len(cursors) != len(set(cursors)):
        return PaginationAssessmentV1(
            status=STATUS_REPEATED_CURSOR,
            page_row_count=base.page_row_count,
            request_limit=base.request_limit,
            observed_cursor=base.observed_cursor,
            next_cursor=base.next_cursor,
            pagination_terminal=None,
            pagination_terminal_source=None,
            single_page=False,
        )
    if _pages_contradict(endpoint, pages):
        return PaginationAssessmentV1(
            status=STATUS_CONTRADICTORY_PAGES,
            page_row_count=base.page_row_count,
            request_limit=base.request_limit,
            observed_cursor=base.observed_cursor,
            next_cursor=base.next_cursor,
            pagination_terminal=None,
            pagination_terminal_source=None,
            single_page=False,
        )
    return base


def _group_pages(
    records: tuple[AdmissionRawCaptureV1, ...],
) -> dict[str, tuple[AdmissionRawCaptureV1, ...]]:
    grouped: dict[str, list[AdmissionRawCaptureV1]] = {}
    for record in records:
        grouped.setdefault(record.endpoint, []).append(record)
    return {endpoint: tuple(pages) for endpoint, pages in grouped.items()}


def _response_from_pages(
    endpoint: str,
    pages: tuple[AdmissionRawCaptureV1, ...],
    assessment: PaginationAssessmentV1,
) -> CapturedGetResponseV1:
    usable = assessment.status == STATUS_UNPROVEN and assessment.single_page and len(pages) == 1
    page = pages[0] if usable else None
    payload = page.payload if page is not None else None
    digest = page.body_digest if page is not None else None
    venue = venue_timestamp_from_payload_v1(payload) if payload is not None else None
    params = dict(page.request_params) if page is not None else None
    terminal = None
    source = None
    if endpoint in PAGINATED_ENDPOINTS:
        terminal = None
        source = None
    return CapturedGetResponseV1(
        endpoint=endpoint,
        request_params=params,
        payload=payload,
        body_digest=digest,
        captured_at_ms=None if page is None else page.captured_at_ms,
        venue_timestamp_ms=venue,
        pagination_terminal=terminal,
        pagination_terminal_source=source,
        admission_window_id=None,
    )


def map_captures_to_responses_v1(
    records: tuple[AdmissionRawCaptureV1, ...],
) -> tuple[CapturedGetResponseV1, ...]:
    """Map one logical response per endpoint. Incomplete pages are not merged."""
    grouped = _group_pages(records)
    responses: list[CapturedGetResponseV1] = []
    for endpoint in sorted(grouped):
        pages = grouped[endpoint]
        assessment = assess_pagination_v1(endpoint, pages)
        responses.append(_response_from_pages(endpoint, pages, assessment))
    return tuple(responses)


def collect_bounded_pagination_capture_v1(
    fetch_json: RestGetJson,
    *,
    endpoint: str,
    request_params: Mapping[str, str],
    captured_at_ms: object = None,
    page_budget: int = OFFLINE_PAGE_BUDGET_V1,
) -> tuple[AdmissionRawCaptureV1, ...]:
    """Injected page walk. Stops without inventing a terminal witness."""
    assert_get_path_allowlisted_v1(endpoint)
    assert_no_rest_post_v1("GET")
    explicit_ms = explicit_captured_at_ms_v1(captured_at_ms)
    pages: list[AdmissionRawCaptureV1] = []
    seen: set[str] = set()
    cursor: str | None = None
    base = {key: value for key, value in request_params.items() if key != "after"}
    for _ in range(page_budget):
        params = dict(base)
        if cursor is not None:
            if cursor in seen:
                break
            params["after"] = cursor
            seen.add(cursor)
        payload = fetch_json(endpoint, params)
        if not isinstance(payload, Mapping):
            break
        page = admission_capture_record_v1(endpoint, params, payload, captured_at_ms=explicit_ms)
        nxt = current_contract_next_cursor_v1(payload)
        if nxt is not None and nxt in seen:
            pages.append(page)
            break
        pages.append(page)
        if nxt is None or nxt == "":
            break
        cursor = nxt
    return tuple(pages)


def admit_offline_get_evidence_v1(
    records: tuple[AdmissionRawCaptureV1, ...] | None,
    parameters: AdmissionParametersV1 | None,
    *,
    synthetic_responses: tuple[object, ...] | None = None,
) -> AdmissionResultV1:
    """One validator call. Synthetic responses are not capture-derived OKX truth."""
    if synthetic_responses is not None and records is not None:
        return validate_get_evidence_admission_v1(("CONFLICTING_BUNDLE_INPUT",), parameters)
    if synthetic_responses is not None:
        ordered = tuple(
            sorted(
                synthetic_responses,
                key=lambda item: item.endpoint if isinstance(item, CapturedGetResponseV1) else "",
            )
        )
        return validate_get_evidence_admission_v1(ordered, parameters)
    if records is None:
        return validate_get_evidence_admission_v1(None, parameters)
    return validate_get_evidence_admission_v1(map_captures_to_responses_v1(records), parameters)
