"""OKX EEA instrument discovery adapter (offline / injected payload only).

No network calls. Productive discovery supplies a sealed/public instruments payload
plus an optional mark-price support inventory. Dashboard/readmodel inputs are rejected.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping, Optional, Sequence

from src.ops.governed_futures_universe_producer_v1.constants_v1 import VENUE, VENUE_ALLOWED
from src.ops.governed_futures_universe_producer_v1.reason_codes_v1 import UniverseFailureCodeV1


@dataclass(frozen=True)
class OkxEeaDiscoveryResultV1:
    ok: bool
    venue: str
    instruments: tuple[Mapping[str, Any], ...]
    mark_price_supported_ids: frozenset[str]
    source_event_time: str
    failure_codes: tuple[str, ...]
    raw_payload_present: bool


_FORBIDDEN_SOURCE_MARKERS = frozenset(
    {
        "dashboard",
        "readmodel",
        "universe_selection_readmodel",
        "market_ranking_funnel",
        "market_surface",
        "webui",
        "fixture_as_authority",
    }
)


def _as_mapping(value: Any) -> Optional[Mapping[str, Any]]:
    return value if isinstance(value, Mapping) else None


def discover_okx_eea_instruments_v1(
    *,
    source_payload: Mapping[str, Any] | None,
    mark_price_payload: Mapping[str, Any] | Sequence[str] | None = None,
    source_event_time: str | None = None,
    venue: str = VENUE,
    source_kind: str | None = None,
) -> OkxEeaDiscoveryResultV1:
    """Parse and validate OKX EEA public instruments discovery input fail-closed."""
    if source_kind is not None:
        lowered = source_kind.strip().lower()
        if any(marker in lowered for marker in _FORBIDDEN_SOURCE_MARKERS):
            return OkxEeaDiscoveryResultV1(
                ok=False,
                venue=venue,
                instruments=(),
                mark_price_supported_ids=frozenset(),
                source_event_time=str(source_event_time or ""),
                failure_codes=(UniverseFailureCodeV1.DASHBOARD_INPUT_FORBIDDEN.value,),
                raw_payload_present=False,
            )

    venue_norm = str(venue or "").strip().lower()
    if venue_norm not in VENUE_ALLOWED:
        return OkxEeaDiscoveryResultV1(
            ok=False,
            venue=venue_norm,
            instruments=(),
            mark_price_supported_ids=frozenset(),
            source_event_time=str(source_event_time or ""),
            failure_codes=(UniverseFailureCodeV1.VENUE_NOT_OKX_EEA.value,),
            raw_payload_present=source_payload is not None,
        )

    if source_payload is None:
        return OkxEeaDiscoveryResultV1(
            ok=False,
            venue=venue_norm,
            instruments=(),
            mark_price_supported_ids=frozenset(),
            source_event_time=str(source_event_time or ""),
            failure_codes=(UniverseFailureCodeV1.OKX_SOURCE_UNAVAILABLE.value,),
            raw_payload_present=False,
        )

    payload = _as_mapping(source_payload)
    if payload is None:
        return OkxEeaDiscoveryResultV1(
            ok=False,
            venue=venue_norm,
            instruments=(),
            mark_price_supported_ids=frozenset(),
            source_event_time=str(source_event_time or ""),
            failure_codes=(UniverseFailureCodeV1.MALFORMED_SOURCE_PAYLOAD.value,),
            raw_payload_present=True,
        )

    # Reject dashboard-shaped authority envelopes.
    for key in ("readmodel_schema", "dashboard_authority", "universe_selection_readmodel"):
        if key in payload:
            return OkxEeaDiscoveryResultV1(
                ok=False,
                venue=venue_norm,
                instruments=(),
                mark_price_supported_ids=frozenset(),
                source_event_time=str(source_event_time or ""),
                failure_codes=(UniverseFailureCodeV1.DASHBOARD_INPUT_FORBIDDEN.value,),
                raw_payload_present=True,
            )

    code = str(payload.get("code", "0")).strip()
    if code not in {"0", ""}:
        return OkxEeaDiscoveryResultV1(
            ok=False,
            venue=venue_norm,
            instruments=(),
            mark_price_supported_ids=frozenset(),
            source_event_time=str(source_event_time or ""),
            failure_codes=(UniverseFailureCodeV1.OKX_SOURCE_UNAVAILABLE.value,),
            raw_payload_present=True,
        )

    data = payload.get("data")
    if not isinstance(data, list):
        return OkxEeaDiscoveryResultV1(
            ok=False,
            venue=venue_norm,
            instruments=(),
            mark_price_supported_ids=frozenset(),
            source_event_time=str(source_event_time or ""),
            failure_codes=(UniverseFailureCodeV1.MALFORMED_SOURCE_PAYLOAD.value,),
            raw_payload_present=True,
        )

    rows: list[Mapping[str, Any]] = []
    for item in data:
        mapped = _as_mapping(item)
        if mapped is None:
            return OkxEeaDiscoveryResultV1(
                ok=False,
                venue=venue_norm,
                instruments=(),
                mark_price_supported_ids=frozenset(),
                source_event_time=str(source_event_time or ""),
                failure_codes=(UniverseFailureCodeV1.MALFORMED_SOURCE_PAYLOAD.value,),
                raw_payload_present=True,
            )
        rows.append(mapped)

    event_time = str(source_event_time or payload.get("source_event_time") or "").strip()
    if not event_time:
        # Prefer provider ts if present on envelope; else fail closed later in eligibility.
        event_time = str(payload.get("ts") or "").strip()

    mark_ids: set[str] = set()
    if isinstance(mark_price_payload, Sequence) and not isinstance(
        mark_price_payload, (str, bytes)
    ):
        for item in mark_price_payload:
            if isinstance(item, str) and item.strip():
                mark_ids.add(item.strip())
            elif isinstance(item, Mapping):
                inst = str(item.get("instId") or "").strip()
                if inst:
                    mark_ids.add(inst)
    elif isinstance(mark_price_payload, Mapping):
        mark_code = str(mark_price_payload.get("code", "0")).strip()
        if mark_code not in {"0", ""}:
            return OkxEeaDiscoveryResultV1(
                ok=False,
                venue=venue_norm,
                instruments=tuple(rows),
                mark_price_supported_ids=frozenset(),
                source_event_time=event_time,
                failure_codes=(UniverseFailureCodeV1.OKX_SOURCE_UNAVAILABLE.value,),
                raw_payload_present=True,
            )
        mark_data = mark_price_payload.get("data")
        if not isinstance(mark_data, list):
            return OkxEeaDiscoveryResultV1(
                ok=False,
                venue=venue_norm,
                instruments=tuple(rows),
                mark_price_supported_ids=frozenset(),
                source_event_time=event_time,
                failure_codes=(UniverseFailureCodeV1.MALFORMED_SOURCE_PAYLOAD.value,),
                raw_payload_present=True,
            )
        for item in mark_data:
            if isinstance(item, Mapping):
                inst = str(item.get("instId") or "").strip()
                mark_px = item.get("markPx")
                if inst and mark_px not in (None, ""):
                    mark_ids.add(inst)

    return OkxEeaDiscoveryResultV1(
        ok=True,
        venue=venue_norm,
        instruments=tuple(rows),
        mark_price_supported_ids=frozenset(mark_ids),
        source_event_time=event_time,
        failure_codes=(),
        raw_payload_present=True,
    )
