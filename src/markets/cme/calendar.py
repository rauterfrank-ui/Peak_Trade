"""
CME Calendar & Roll Policy (Equity Index Futures)
================================================

MVP enthält:
- Roll-Date Policy für Equity Index Futures:
  "Monday prior to the third Friday of expiration month"
- Minimaler Session-Helper für Offline-Dataset-Checks (konfigurierbar)

Wichtig:
- Trading hours / holidays ändern sich. Für Produktions-Usecases muss ein
  verifizierter Kalender verwendet werden. Dieses Modul ist bewusst konservativ.
- NO-LIVE: Keine Live-Connectivity, keine Broker-Calls.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, time, timedelta, timezone
from typing import Optional, Tuple

try:
    from zoneinfo import ZoneInfo  # py3.9+
except Exception:  # pragma: no cover
    ZoneInfo = None  # type: ignore


def third_friday(year: int, month: int) -> date:
    """
    Berechnet den dritten Freitag eines Monats.
    """
    if month < 1 or month > 12:
        raise ValueError(f"Invalid month: {month}. Expected 1..12.")
    d = date(year, month, 1)
    # weekday: Mon=0 .. Sun=6, Fri=4
    days_until_fri = (4 - d.weekday()) % 7
    first_friday = d + timedelta(days=days_until_fri)
    return first_friday + timedelta(days=14)


def cme_equity_index_roll_date(year: int, month: int) -> date:
    """
    Default roll date (Equity Index Futures):
    Monday prior to the third Friday of expiration month.

    Implementation: third_friday - 4 days.
    """
    return third_friday(year, month) - timedelta(days=4)


@dataclass(frozen=True, slots=True)
class CmeEquityIndexSessionSpec:
    """
    Minimaler, konfigurierbarer Session-Spec (MVP) für Offline-Validation.

    Default orientiert sich am üblichen Globex-Muster (vereinfacht):
    - Session open: 18:00 ET (Vorabend)
    - Session close: 17:00 ET (Trade-Date)
    - Maintenance break: 17:00-18:00 ET

    Holiday schedule ist hier **nicht** modelliert.
    """

    tz_name: str = "America/New_York"
    session_open_et: time = time(18, 0)
    session_close_et: time = time(17, 0)
    maintenance_start_et: time = time(17, 0)
    maintenance_end_et: time = time(18, 0)

    def _tz(self) -> ZoneInfo:
        if ZoneInfo is None:  # pragma: no cover
            raise RuntimeError("zoneinfo not available; requires Python 3.9+")
        return ZoneInfo(self.tz_name)

    def to_utc_bounds_for_trade_date(self, trade_date: date) -> Tuple[datetime, datetime]:
        """
        Session bounds in UTC for a given trade_date.

        Interprets session as:
        - opens previous calendar day at session_open_et
        - closes trade_date at session_close_et
        """
        tz = self._tz()
        open_local = datetime.combine(
            trade_date - timedelta(days=1), self.session_open_et, tzinfo=tz
        )
        close_local = datetime.combine(trade_date, self.session_close_et, tzinfo=tz)
        return (open_local.astimezone(timezone.utc), close_local.astimezone(timezone.utc))

    def is_in_maintenance_break_utc(self, ts_utc: datetime) -> bool:
        """
        True, wenn ts_utc in der täglichen Maintenance-Break liegt.
        """
        tz = self._tz()
        ts_local = ts_utc.astimezone(tz)
        t = ts_local.timetz().replace(tzinfo=None)
        # maintenance break is same local-day interval [start, end)
        if self.maintenance_start_et <= self.maintenance_end_et:
            return self.maintenance_start_et <= t < self.maintenance_end_et
        # fallback (shouldn't happen with default)
        return t >= self.maintenance_start_et or t < self.maintenance_end_et


def infer_trade_date_from_timestamp(
    ts_utc: datetime, session: Optional[CmeEquityIndexSessionSpec] = None
) -> date:
    """
    Heuristik: mappt UTC timestamp auf trade_date in ET.
    Für die Globex-Session gilt: Zeiten nach 18:00 ET gehören zum nächsten trade_date.
    """
    sess = session or CmeEquityIndexSessionSpec()
    tz = sess._tz()
    local = ts_utc.astimezone(tz)
    # If local time >= session_open, it's "next day's" trade date.
    if local.timetz().replace(tzinfo=None) >= sess.session_open_et:
        return local.date() + timedelta(days=1)
    return local.date()


__all__ = [
    "third_friday",
    "cme_equity_index_roll_date",
    "CmeEquityIndexSessionSpec",
    "infer_trade_date_from_timestamp",
]
