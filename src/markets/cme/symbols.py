"""
CME Futures Symbols Utilities (NQ/MNQ)
=====================================

MVP Utilities für:
- Month-Code Mapping (F, G, H, ...)
- Kontrakt-Symbol Formatierung/Parsing

Design:
- Internes kanonisches Format: {ROOT}{MONTH_CODE}{YEAR4}, z.B. "NQH2026"
  (leicht deterministisch und eindeutig)
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import date
from typing import Dict, Iterable, Tuple


# CME month codes
# Jan..Dec => F,G,H,J,K,M,N,Q,U,V,X,Z
MONTH_CODE_BY_MONTH: Dict[int, str] = {
    1: "F",
    2: "G",
    3: "H",
    4: "J",
    5: "K",
    6: "M",
    7: "N",
    8: "Q",
    9: "U",
    10: "V",
    11: "X",
    12: "Z",
}

MONTH_BY_MONTH_CODE: Dict[str, int] = {v: k for k, v in MONTH_CODE_BY_MONTH.items()}


def month_code_for_month(month: int) -> str:
    if month not in MONTH_CODE_BY_MONTH:
        raise ValueError(f"Invalid month: {month}. Expected 1..12.")
    return MONTH_CODE_BY_MONTH[month]


def month_from_code(code: str) -> int:
    c = code.upper()
    if c not in MONTH_BY_MONTH_CODE:
        raise ValueError(f"Invalid CME month code: {code!r}")
    return MONTH_BY_MONTH_CODE[c]


@dataclass(frozen=True)
class CmeFuturesContract:
    """
    Repräsentiert einen CME Futures Kontrakt (kanonisches Format).
    """

    root: str
    month: int
    year: int

    @property
    def month_code(self) -> str:
        return month_code_for_month(self.month)

    @property
    def expiration_month(self) -> Tuple[int, int]:
        return (self.year, self.month)

    def to_symbol(self) -> str:
        return format_cme_contract_symbol(self.root, self.month, self.year)


_SYM_RE = re.compile(r"^(?P<root>[A-Z]{1,8})(?P<mcode>[FGHJKMNQUVXZ])(?P<year>\d{4})$")


def format_cme_contract_symbol(root: str, month: int, year: int) -> str:
    """
    Kanonisches Symbol: {ROOT}{MONTH_CODE}{YEAR4}, z.B. NQH2026.
    """
    r = root.upper()
    code = month_code_for_month(month)
    if year < 1900 or year > 2200:
        raise ValueError(f"Invalid year: {year}. Expected 1900..2200.")
    return f"{r}{code}{int(year):04d}"


def parse_cme_contract_symbol(symbol: str) -> CmeFuturesContract:
    """
    Parsen des kanonischen Formats: NQH2026.
    """
    s = symbol.strip().upper()
    m = _SYM_RE.match(s)
    if not m:
        raise ValueError(
            f"Invalid CME contract symbol format: {symbol!r} (expected e.g. 'NQH2026')"
        )
    root = m.group("root")
    month = month_from_code(m.group("mcode"))
    year = int(m.group("year"))
    return CmeFuturesContract(root=root, month=month, year=year)


def quarterly_months() -> Iterable[int]:
    """Standard quarterly cycle: Mar/Jun/Sep/Dec."""
    return (3, 6, 9, 12)


def next_quarterly_expiration_month(after: date) -> Tuple[int, int]:
    """
    Liefert (year, month) der nächsten quarterly expiration month NACH dem Datum.
    """
    y = after.year
    for m in quarterly_months():
        if (y, m) > (after.year, after.month):
            return (y, m)
    return (y + 1, 3)


__all__ = [
    "MONTH_CODE_BY_MONTH",
    "MONTH_BY_MONTH_CODE",
    "month_code_for_month",
    "month_from_code",
    "CmeFuturesContract",
    "format_cme_contract_symbol",
    "parse_cme_contract_symbol",
    "quarterly_months",
    "next_quarterly_expiration_month",
]
