"""AUTHORITY=NONE adapter from upstream public-MD observation to Landscape V3."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Mapping, Optional

from src.webui.market_dashboard_landscape_v3.candle_chart_v1 import LandscapeV3ChartStateV1
from src.webui.market_dashboard_landscape_v3.constants_v1 import (
    AUTHORITY,
    EEA_PUBLIC_MD_SOURCE_FAMILY,
    EXECUTION_AUTHORITY,
    READ_ONLY,
    RISK_AUTHORITY,
    SCHEMA_VERSION,
    SELECTION_AUTHORITY,
    SNAPSHOT_SCHEMA_VERSION,
)
from src.webui.market_dashboard_landscape_v3.contracts_v1 import SECTION_FIELD_NAMES, SECTION_IDS
from src.webui.market_dashboard_landscape_v3.unavailable_v1 import (
    available,
    missing_source,
    not_bound,
    unknown,
)


@dataclass
class LandscapeV3UpstreamObservationV1:
    venue_native_id: str
    transport_state: str = "DISCONNECTED"
    freshness_state: str = "UNKNOWN"
    mark_px: Optional[str] = None
    mark_captured_at: Optional[str] = None
    sequence_cursor: int = 0
    provenance: dict[str, Any] = field(default_factory=dict)
    rest_host: str = "eea.okx.com"
    chart: LandscapeV3ChartStateV1 = field(
        default_factory=lambda: LandscapeV3ChartStateV1("ETH-USDT-SWAP")
    )


def _count_field_states(sections: Mapping[str, Any]) -> tuple[int, int, int]:
    avail = unavail = other = 0
    for section in sections.values():
        fields = section.get("fields") or {}
        for envelope in fields.values():
            state = str((envelope or {}).get("availability", "UNKNOWN"))
            if state == "AVAILABLE":
                avail += 1
            elif state in {"MISSING_SOURCE", "NOT_BOUND"}:
                unavail += 1
            else:
                other += 1
    return avail, unavail, other


class LandscapeV3PresentationAdapterV1:
    """Consumes facts; never owns authoritative trading state."""

    def build_snapshot(
        self,
        obs: LandscapeV3UpstreamObservationV1,
        *,
        generated_at: datetime | None = None,
    ) -> dict[str, Any]:
        ts = generated_at or datetime.now(timezone.utc)
        sections = self._build_sections(obs)
        avail, unavail, other = _count_field_states(sections)
        return {
            "schema_version": SNAPSHOT_SCHEMA_VERSION,
            "presentation_schema": SCHEMA_VERSION,
            "authority": AUTHORITY,
            "read_only": READ_ONLY,
            "selection_authority": SELECTION_AUTHORITY,
            "risk_authority": RISK_AUTHORITY,
            "execution_authority": EXECUTION_AUTHORITY,
            "generated_at": ts.isoformat(),
            "instrument": {
                "venue_native_id": obs.venue_native_id,
                "source_family": EEA_PUBLIC_MD_SOURCE_FAMILY,
            },
            "transport": {
                "state": obs.transport_state,
                "freshness_state": obs.freshness_state,
                "sequence_cursor": obs.sequence_cursor,
            },
            "primary": self._primary_operator_strip(obs),
            "chart": {
                "candles": obs.chart.candles_payload_v1(),
                "sequence": obs.chart.sequence,
                "degraded": obs.transport_state != "CONNECTED",
            },
            "sections": sections,
            "field_counts": {
                "available": avail,
                "unavailable": unavail,
                "other": other,
            },
            "diagnostics": self._diagnostics(obs),
        }

    def build_incremental(
        self,
        obs: LandscapeV3UpstreamObservationV1,
        *,
        chart_events: list[dict[str, Any]],
        transport_patch: Mapping[str, Any] | None = None,
    ) -> dict[str, Any]:
        return {
            "schema_version": SNAPSHOT_SCHEMA_VERSION,
            "type": "incremental",
            "sequence_cursor": obs.sequence_cursor,
            "transport": transport_patch
            or {
                "state": obs.transport_state,
                "freshness_state": obs.freshness_state,
            },
            "chart_events": chart_events,
            "primary": self._primary_operator_strip(obs),
        }

    def _primary_operator_strip(self, obs: LandscapeV3UpstreamObservationV1) -> dict[str, Any]:
        return {
            "instrument": obs.venue_native_id,
            "connectivity": obs.transport_state,
            "freshness": obs.freshness_state,
            "mark_px": obs.mark_px,
            "selection": not_bound("LANDSCAPE_V3_SELECTION_AUTHORITY_NONE"),
            "decision": missing_source("CANONICAL_DECISION_NOT_BOUND_IN_V3"),
            "position": not_bound("ACCOUNT_POSITION_REQUIRE_CREDENTIALS"),
            "account": not_bound("ACCOUNT_POSITION_REQUIRE_CREDENTIALS"),
            "risk": not_bound("RISK_AUTHORITY_NONE"),
            "quality": available(obs.freshness_state)
            if obs.freshness_state != "UNKNOWN"
            else unknown("NO_FRESHNESS"),
            "blockers": self._blockers(obs),
        }

    def _blockers(self, obs: LandscapeV3UpstreamObservationV1) -> list[str]:
        blockers: list[str] = []
        if obs.transport_state == "DISCONNECTED":
            blockers.append("PUBLIC_MD_STREAM_DISCONNECTED")
        elif obs.transport_state == "STALE":
            blockers.append("PUBLIC_MD_STREAM_STALE")
        return blockers

    def _build_sections(self, obs: LandscapeV3UpstreamObservationV1) -> dict[str, Any]:
        out: dict[str, Any] = {}
        for section_id in SECTION_IDS:
            names = SECTION_FIELD_NAMES[section_id]
            fields: dict[str, Any] = {}
            for name in names:
                fields[name] = self._field_for(section_id, name, obs)
            out[section_id] = {"section_id": section_id, "fields": fields}
        return out

    def _field_for(
        self, section_id: str, field_name: str, obs: LandscapeV3UpstreamObservationV1
    ) -> dict[str, Any]:
        if section_id == "LIVE_MARKET_SYSTEM" and field_name == "market_facts":
            if obs.mark_px is None:
                return missing_source("NO_LIVE_MARK_FACT")
            return available(
                {
                    "mark_px": obs.mark_px,
                    "captured_at": obs.mark_captured_at,
                    "rest_host": obs.rest_host,
                },
                provenance=obs.provenance,
            )
        if section_id == "LIVE_MARKET_SYSTEM" and field_name == "selection":
            return not_bound("SELECTION_AUTHORITY_NONE")
        if section_id == "LIVE_MARKET_SYSTEM" and field_name in {"account", "position"}:
            return not_bound("NO_READ_ONLY_ACCOUNT_PROJECTION_WITHOUT_CREDENTIALS")
        if section_id == "LIVE_MARKET_SYSTEM" and field_name == "quality":
            return (
                available(obs.freshness_state)
                if obs.freshness_state != "UNKNOWN"
                else unknown("FRESHNESS_UNKNOWN")
            )
        if section_id == "REALIZED_BEHAVIOR" and field_name == "n_bars":
            n = len(obs.chart.candles)
            if n == 0:
                return missing_source("NO_HISTORICAL_BARS_BOOTSTRAPPED")
            return available({"n_bars": n, "interval": "PT1M_MARK"})
        if section_id == "MV2_DOUBLE_PLAY_ATTRIBUTION" and field_name == "decision_t":
            return missing_source("DECISION_PROJECTION_NOT_BOUND")
        return missing_source(f"NO_V3_SOURCE:{section_id}.{field_name}")

    def _diagnostics(self, obs: LandscapeV3UpstreamObservationV1) -> dict[str, Any]:
        return {
            "schema_ids": [SCHEMA_VERSION, SNAPSHOT_SCHEMA_VERSION],
            "source_family": EEA_PUBLIC_MD_SOURCE_FAMILY,
            "rest_host": obs.rest_host,
            "forbidden_global_rest": True,
            "direct_browser_okx": False,
            "provenance": obs.provenance,
            "transport_state": obs.transport_state,
            "sequence_cursor": obs.sequence_cursor,
        }
