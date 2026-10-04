"""Observation tick sources for bounded operational runs (injected or public EEA GET-only)."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Any, Protocol

from src.ops.integrated_paper_shadow_observation_session_v1.market_data_policy_v1 import (
    ObservationMarketTickV1,
)
from src.ops.integrated_paper_shadow_observation_wallclock_session_execution_v1.constants_v1 import (
    CANONICAL_INSTRUMENT_ID,
    MARKET_TYPE_FUTURES,
    VENUE_OKX,
)


@dataclass(frozen=True)
class ObservationFetchResultV1:
    ok: bool
    tick: ObservationMarketTickV1 | None
    reference_price: Decimal
    fatal: bool
    reason: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "ok": self.ok,
            "tick": None if self.tick is None else self.tick.mid_price,
            "fatal": self.fatal,
            "reason": self.reason,
        }


class ObservationTickSourceV1(Protocol):
    def next_tick(
        self,
        *,
        wall_now_unix: float,
        mono_now: float,
        sequence: int,
    ) -> ObservationFetchResultV1: ...


@dataclass
class InjectedObservationTickSourceV1:
    """Deterministic ticks for offline operational reproof (no network)."""

    ticks: tuple[ObservationMarketTickV1, ...]
    _index: int = 0
    repeat_last: bool = True

    def next_tick(
        self,
        *,
        wall_now_unix: float,
        mono_now: float,
        sequence: int,
    ) -> ObservationFetchResultV1:
        if self._index < len(self.ticks):
            tick = self.ticks[self._index]
            self._index += 1
            return ObservationFetchResultV1(
                ok=True,
                tick=tick,
                reference_price=Decimal(str(tick.mid_price)),
                fatal=False,
                reason="",
            )
        if self.ticks and self.repeat_last:
            tick = self.ticks[-1]
            return ObservationFetchResultV1(
                ok=True,
                tick=ObservationMarketTickV1(
                    instrument_id=tick.instrument_id,
                    venue=tick.venue,
                    market_type=tick.market_type,
                    sequence=sequence,
                    event_ts_unix=wall_now_unix,
                    receive_ts_unix=wall_now_unix,
                    mono_ts=mono_now,
                    mid_price=tick.mid_price,
                    source=tick.source,
                ),
                reference_price=Decimal(str(tick.mid_price)),
                fatal=False,
                reason="REPEAT_LAST_TICK",
            )
        return ObservationFetchResultV1(
            ok=False,
            tick=None,
            reference_price=Decimal("0"),
            fatal=False,
            reason="TICK_SOURCE_EXHAUSTED",
        )


@dataclass
class PublicEeaObservationTickSourceV1:
    """Public read-only MD via canonical EEA transport (no credentials, GET-only)."""

    transport: Any
    venue_mapping: Any | None = None
    max_stale_seconds: float = 30.0
    _sequence: int = 0
    _opened: bool = False

    def _ensure_open(self) -> None:
        if not self._opened:
            self.transport.open()
            self._opened = True

    def next_tick(
        self,
        *,
        wall_now_unix: float,
        mono_now: float,
        sequence: int,
    ) -> ObservationFetchResultV1:
        from src.ops.integrated_paper_shadow_observation_wallclock_session_execution_v1.eea_public_md_transport_v1 import (
            EeaPublicMdTransportError,
        )
        from src.ops.okx_native_instrument_and_mark_price_runtime_binding_fail_closed_v1.productive_md_fetch_v1 import (
            fetch_normalized_public_market_data_v1,
            resolve_mapping_with_transport_inventory_v1,
        )

        try:
            self._ensure_open()
            if self.venue_mapping is None:
                self.venue_mapping = resolve_mapping_with_transport_inventory_v1(
                    transport=self.transport,
                    canonical_instrument_id=CANONICAL_INSTRUMENT_ID,
                )
            normalized = fetch_normalized_public_market_data_v1(
                transport=self.transport,
                mapping=self.venue_mapping,
                receive_ts_unix=wall_now_unix,
                max_stale_seconds=float(self.max_stale_seconds),
                include_ticker=True,
            )
            self._sequence += 1
            tick = ObservationMarketTickV1(
                instrument_id=str(normalized.canonical_instrument_id or CANONICAL_INSTRUMENT_ID),
                venue=VENUE_OKX,
                market_type=MARKET_TYPE_FUTURES,
                sequence=self._sequence,
                event_ts_unix=float(normalized.event_ts_unix),
                receive_ts_unix=float(wall_now_unix),
                mono_ts=mono_now,
                mid_price=float(normalized.mark_px),
                source="eea_public_rest_mark_price",
            )
            return ObservationFetchResultV1(
                ok=True,
                tick=tick,
                reference_price=Decimal(str(normalized.mark_px)),
                fatal=False,
                reason="",
            )
        except EeaPublicMdTransportError as exc:
            return ObservationFetchResultV1(
                ok=False,
                tick=None,
                reference_price=Decimal("0"),
                fatal=True,
                reason=f"OBSERVATION_FATAL:{exc}",
            )
        except Exception as exc:
            return ObservationFetchResultV1(
                ok=False,
                tick=None,
                reference_price=Decimal("0"),
                fatal=True,
                reason=f"OBSERVATION_FATAL:{type(exc).__name__}:{exc}",
            )

    def close(self) -> None:
        if self._opened and getattr(self.transport, "opened", False):
            self.transport.close()
        self._opened = False
