"""Read-only Category-C open algo-pending observer.

Reuses an injected LiveCanary GET client. Does not submit, cancel, amend,
flatten, or construct execution permits. Local mock/tests only in this slice;
this module does not authorize an Exchange GET.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from types import MappingProxyType
from typing import Any, Callable, Mapping, Protocol
from urllib.parse import quote

from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.constants_v1 import (
    DEFAULT_INST_TYPE,
    DEFAULT_INSTRUMENT_ID,
    ENDPOINT_ORDERS_ALGO_PENDING,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.http_client_v1 import (
    LiveCanaryHttpError,
    LiveCanaryHttpResponseV1,
    parse_json_object_v1,
)

CATEGORY_C_PAGE_LIMIT = 100
CATEGORY_C_INST_TYPE = DEFAULT_INST_TYPE
CATEGORY_C_ORD_TYPE_VARIANTS: tuple[str, ...] = (
    "conditional,oco",
    "trigger",
    "move_order_stop",
)
CATEGORY_C_NAMED_ORD_TYPES: frozenset[str] = frozenset(
    {"conditional", "oco", "trigger", "move_order_stop"}
)
CATEGORY_C_OPEN_STATES: frozenset[str] = frozenset({"live", "pause"})
CATEGORY_C_DEFAULT_MAX_REQUESTS = 30
CATEGORY_C_DEFAULT_MAX_PAGES_PER_VARIANT = 10
_EVIDENCE_KEYS: tuple[str, ...] = (
    "algoId",
    "instId",
    "ordType",
    "side",
    "sz",
    "state",
    "tpTriggerPx",
    "tpOrdPx",
    "slTriggerPx",
    "slOrdPx",
    "triggerPx",
    "reduceOnly",
    "attachAlgoOrds",
    "cTime",
    "uTime",
)


class CategoryCGetClientV1(Protocol):
    """GET-only client surface used by the observer."""

    rest_base: str

    def get(
        self,
        *,
        endpoint: str,
        headers: Mapping[str, str] | None = None,
    ) -> LiveCanaryHttpResponseV1:
        """Issue one GET. Must not be used as a POST dispatcher."""


class CategoryCObservationOutcomeV1(str, Enum):
    OBSERVATION_UNPROVEN = "OBSERVATION_UNPROVEN"
    CATEGORY_C_OBSERVATION_INCOMPLETE = "CATEGORY_C_OBSERVATION_INCOMPLETE"
    CATEGORY_C_UNKNOWN_TYPE_PRESENT = "CATEGORY_C_UNKNOWN_TYPE_PRESENT"
    TARGET_CATEGORY_C_NOT_OBSERVED = "TARGET_CATEGORY_C_NOT_OBSERVED"
    TARGET_CATEGORY_C_OBSERVED = "TARGET_CATEGORY_C_OBSERVED"


@dataclass(frozen=True)
class CategoryCAlgoPendingRowEvidenceV1:
    """Present-key snapshot only. Absent OKX fields are omitted."""

    values: Mapping[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return dict(self.values)


@dataclass(frozen=True)
class CategoryCOpenAlgoPendingObservationV1:
    outcome: CategoryCObservationOutcomeV1
    target_instrument_id: str
    request_count: int
    endpoints_requested: tuple[str, ...]
    variants_completed: tuple[str, ...]
    methods_used: tuple[str, ...]
    target_rows: tuple[CategoryCAlgoPendingRowEvidenceV1, ...]
    fail_closed_reason: str | None = None
    canonical_binding_status: str = "UNBOUND"
    runtime_authorization_effect: str = "NONE"

    def to_dict(self) -> dict[str, Any]:
        return {
            "outcome": self.outcome.value,
            "target_instrument_id": self.target_instrument_id,
            "request_count": self.request_count,
            "endpoints_requested": list(self.endpoints_requested),
            "variants_completed": list(self.variants_completed),
            "methods_used": list(self.methods_used),
            "target_rows": [row.to_dict() for row in self.target_rows],
            "fail_closed_reason": self.fail_closed_reason,
            "canonical_binding_status": self.canonical_binding_status,
            "runtime_authorization_effect": self.runtime_authorization_effect,
        }


def _enc(value: str) -> str:
    return quote(str(value), safe=",")


def build_category_c_orders_algo_pending_endpoint_v1(
    *,
    ord_type: str,
    instrument_id: str = DEFAULT_INSTRUMENT_ID,
    inst_type: str = CATEGORY_C_INST_TYPE,
    limit: int = CATEGORY_C_PAGE_LIMIT,
    after: str | None = None,
) -> str:
    """Deterministic GET path+query. Comma in ordType remains unencoded."""
    parts = [
        f"ordType={_enc(ord_type)}",
        f"instType={_enc(inst_type)}",
        f"instId={_enc(instrument_id)}",
        f"limit={int(limit)}",
    ]
    if after is not None:
        parts.append(f"after={_enc(after)}")
    return f"{ENDPOINT_ORDERS_ALGO_PENDING}?{'&'.join(parts)}"


def _result(
    *,
    outcome: CategoryCObservationOutcomeV1,
    target_instrument_id: str,
    request_count: int,
    endpoints_requested: list[str],
    variants_completed: list[str],
    methods_used: list[str],
    target_rows: list[CategoryCAlgoPendingRowEvidenceV1],
    fail_closed_reason: str | None = None,
) -> CategoryCOpenAlgoPendingObservationV1:
    return CategoryCOpenAlgoPendingObservationV1(
        outcome=outcome,
        target_instrument_id=target_instrument_id,
        request_count=request_count,
        endpoints_requested=tuple(endpoints_requested),
        variants_completed=tuple(variants_completed),
        methods_used=tuple(methods_used),
        target_rows=tuple(target_rows),
        fail_closed_reason=fail_closed_reason,
    )


def _evidence_from_row(row: Mapping[str, Any]) -> CategoryCAlgoPendingRowEvidenceV1:
    copied: dict[str, Any] = {}
    for key in _EVIDENCE_KEYS:
        if key in row:
            copied[key] = row[key]
    return CategoryCAlgoPendingRowEvidenceV1(values=MappingProxyType(copied))


def observe_category_c_open_algo_pending_v1(
    *,
    client: CategoryCGetClientV1,
    instrument_id: str = DEFAULT_INSTRUMENT_ID,
    headers: Mapping[str, str] | None = None,
    header_factory: Callable[[str], Mapping[str, str]] | None = None,
    max_requests: int = CATEGORY_C_DEFAULT_MAX_REQUESTS,
    max_pages_per_variant: int = CATEGORY_C_DEFAULT_MAX_PAGES_PER_VARIANT,
) -> CategoryCOpenAlgoPendingObservationV1:
    """Observe untriggered named Category-C algo families via GET only."""
    target = str(instrument_id or "").strip()
    endpoints_requested: list[str] = []
    variants_completed: list[str] = []
    methods_used: list[str] = []
    target_rows: list[CategoryCAlgoPendingRowEvidenceV1] = []
    request_count = 0

    def _done(
        outcome: CategoryCObservationOutcomeV1,
        reason: str | None = None,
    ) -> CategoryCOpenAlgoPendingObservationV1:
        return _result(
            outcome=outcome,
            target_instrument_id=target,
            request_count=request_count,
            endpoints_requested=endpoints_requested,
            variants_completed=variants_completed,
            methods_used=methods_used,
            target_rows=target_rows,
            fail_closed_reason=reason,
        )

    if not target:
        return _done(
            CategoryCObservationOutcomeV1.OBSERVATION_UNPROVEN,
            "TARGET_INSTRUMENT_REQUIRED",
        )
    if int(max_requests) <= 0 or int(max_pages_per_variant) <= 0:
        return _done(
            CategoryCObservationOutcomeV1.CATEGORY_C_OBSERVATION_INCOMPLETE,
            "REQUEST_OR_PAGE_GUARD_INVALID",
        )

    seen_algo_ids: set[str] = set()
    for variant in CATEGORY_C_ORD_TYPE_VARIANTS:
        after: str | None = None
        used_after: set[str] = set()
        pages = 0
        while True:
            if request_count >= int(max_requests):
                return _done(
                    CategoryCObservationOutcomeV1.CATEGORY_C_OBSERVATION_INCOMPLETE,
                    "REQUEST_GUARD_EXCEEDED",
                )
            if pages >= int(max_pages_per_variant):
                return _done(
                    CategoryCObservationOutcomeV1.CATEGORY_C_OBSERVATION_INCOMPLETE,
                    "PAGE_GUARD_EXCEEDED",
                )
            if after is not None:
                if after in used_after:
                    return _done(
                        CategoryCObservationOutcomeV1.OBSERVATION_UNPROVEN,
                        "CYCLIC_PAGINATION",
                    )
                used_after.add(after)
            endpoint = build_category_c_orders_algo_pending_endpoint_v1(
                ord_type=variant,
                instrument_id=target,
                after=after,
            )
            req_headers: dict[str, str] = {str(k): str(v) for k, v in dict(headers or {}).items()}
            if header_factory is not None:
                full_url = f"{str(client.rest_base).rstrip('/')}{endpoint}"
                req_headers.update(
                    {str(k): str(v) for k, v in dict(header_factory(full_url)).items()}
                )
            endpoints_requested.append(endpoint)
            request_count += 1
            pages += 1
            try:
                response = client.get(
                    endpoint=endpoint,
                    headers=req_headers or None,
                )
            except (KeyboardInterrupt, SystemExit):
                raise
            except Exception as exc:
                methods_used.append("GET")
                return _done(
                    CategoryCObservationOutcomeV1.OBSERVATION_UNPROVEN,
                    f"TRANSPORT_OR_CLIENT_ERROR:{type(exc).__name__}",
                )
            methods_used.append(str(response.method or "GET"))
            if str(response.method or "").upper() != "GET":
                return _done(
                    CategoryCObservationOutcomeV1.OBSERVATION_UNPROVEN,
                    "NON_GET_RESPONSE",
                )
            if int(response.status_code) != 200:
                return _done(
                    CategoryCObservationOutcomeV1.OBSERVATION_UNPROVEN,
                    f"HTTP_STATUS_{int(response.status_code)}",
                )
            try:
                payload = parse_json_object_v1(response.body_bytes)
            except LiveCanaryHttpError:
                return _done(
                    CategoryCObservationOutcomeV1.OBSERVATION_UNPROVEN,
                    "MALFORMED_RESPONSE",
                )
            if payload.get("code") != "0":
                return _done(
                    CategoryCObservationOutcomeV1.OBSERVATION_UNPROVEN,
                    "API_CODE_NOT_SUCCESS",
                )
            if "data" not in payload:
                return _done(
                    CategoryCObservationOutcomeV1.OBSERVATION_UNPROVEN,
                    "DATA_MISSING",
                )
            data = payload.get("data")
            if data is None:
                return _done(
                    CategoryCObservationOutcomeV1.OBSERVATION_UNPROVEN,
                    "DATA_NULL",
                )
            if not isinstance(data, list):
                return _done(
                    CategoryCObservationOutcomeV1.OBSERVATION_UNPROVEN,
                    "DATA_NOT_LIST",
                )
            if len(data) > CATEGORY_C_PAGE_LIMIT:
                return _done(
                    CategoryCObservationOutcomeV1.OBSERVATION_UNPROVEN,
                    "PAGE_EXCEEDS_LIMIT",
                )
            for row in data:
                if not isinstance(row, Mapping):
                    return _done(
                        CategoryCObservationOutcomeV1.OBSERVATION_UNPROVEN,
                        "ROW_NOT_OBJECT",
                    )
                if "instId" not in row or str(row.get("instId") or "").strip() == "":
                    return _done(
                        CategoryCObservationOutcomeV1.OBSERVATION_UNPROVEN,
                        "INSTID_MISSING",
                    )
                inst_s = str(row.get("instId")).strip()
                if inst_s != target:
                    return _done(
                        CategoryCObservationOutcomeV1.OBSERVATION_UNPROVEN,
                        "FOREIGN_INSTID",
                    )
                if "ordType" not in row or str(row.get("ordType") or "").strip() == "":
                    return _done(
                        CategoryCObservationOutcomeV1.OBSERVATION_UNPROVEN,
                        "ORDTYPE_MISSING",
                    )
                ord_type = str(row.get("ordType")).strip()
                if ord_type not in CATEGORY_C_NAMED_ORD_TYPES:
                    target_rows.append(_evidence_from_row(row))
                    return _done(
                        CategoryCObservationOutcomeV1.CATEGORY_C_UNKNOWN_TYPE_PRESENT,
                        f"UNKNOWN_ORDTYPE:{ord_type}",
                    )
                if "state" not in row or str(row.get("state") or "").strip() == "":
                    return _done(
                        CategoryCObservationOutcomeV1.OBSERVATION_UNPROVEN,
                        "STATE_MISSING",
                    )
                state = str(row.get("state")).strip()
                if state not in CATEGORY_C_OPEN_STATES:
                    return _done(
                        CategoryCObservationOutcomeV1.OBSERVATION_UNPROVEN,
                        f"STATE_UNEXPECTED:{state}",
                    )
                if "algoId" not in row or str(row.get("algoId") or "").strip() == "":
                    return _done(
                        CategoryCObservationOutcomeV1.OBSERVATION_UNPROVEN,
                        "ALGOID_MISSING",
                    )
                algo_id = str(row.get("algoId")).strip()
                if algo_id in seen_algo_ids:
                    return _done(
                        CategoryCObservationOutcomeV1.OBSERVATION_UNPROVEN,
                        "DUPLICATE_ALGO_ID",
                    )
                seen_algo_ids.add(algo_id)
                target_rows.append(_evidence_from_row(row))
            if len(data) < CATEGORY_C_PAGE_LIMIT:
                variants_completed.append(variant)
                break
            last_id = str(data[-1].get("algoId") or "").strip()
            if not last_id:
                return _done(
                    CategoryCObservationOutcomeV1.OBSERVATION_UNPROVEN,
                    "PAGINATION_CURSOR_MISSING",
                )
            after = last_id

    if len(variants_completed) != len(CATEGORY_C_ORD_TYPE_VARIANTS):
        return _done(
            CategoryCObservationOutcomeV1.CATEGORY_C_OBSERVATION_INCOMPLETE,
            "REQUIRED_VARIANTS_INCOMPLETE",
        )
    if target_rows:
        return _done(CategoryCObservationOutcomeV1.TARGET_CATEGORY_C_OBSERVED)
    return _done(CategoryCObservationOutcomeV1.TARGET_CATEGORY_C_NOT_OBSERVED)
