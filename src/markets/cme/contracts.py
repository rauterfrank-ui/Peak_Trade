"""
CME Futures Contract Specs (Offline-First)
=========================================

Dieses Modul ist die **Code-Source-of-Truth** für ausgewählte CME Futures Specs,
insbesondere Equity Index Futures (NQ/MNQ) für den Offline/Backtest/Replay-Usecase.

Wichtig:
- NO-LIVE: Dieses Modul enthält **keine** Broker-Anbindung und keine Order-Ausführung.
- Specs können sich ändern (Exchange Rulebook). Operator muss pro Release verifizieren.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict


@dataclass(frozen=True, slots=True)
class FuturesContractSpec:
    """
    Minimaler Spec-Satz für Futures-Kontrakte (MVP).

    Attributes:
        symbol_root: Root Symbol (z.B. "NQ", "MNQ")
        multiplier: USD pro Indexpunkt
        min_tick: Minimaler Tick in Indexpunkten
        currency: Quote/Settlement Währung (default: USD)
        exchange: Exchange Identifier (default: CME)
    """

    symbol_root: str
    multiplier: float
    min_tick: float
    currency: str = "USD"
    exchange: str = "CME"

    @property
    def tick_value(self) -> float:
        """Dollarwert eines Ticks: min_tick * multiplier."""
        return float(self.min_tick) * float(self.multiplier)


def get_cme_equity_index_contract_specs() -> Dict[str, FuturesContractSpec]:
    """
    Gibt die bekannten Equity Index Futures Specs zurück (MVP: NQ/MNQ).

    Source of truth (Operator-verify):
    - NQ: multiplier=20 USD/Indexpunkt, min_tick=0.25
    - MNQ: multiplier=2 USD/Indexpunkt, min_tick=0.25
    """

    return {
        "NQ": FuturesContractSpec(symbol_root="NQ", multiplier=20.0, min_tick=0.25),
        "MNQ": FuturesContractSpec(symbol_root="MNQ", multiplier=2.0, min_tick=0.25),
    }


def get_contract_spec(symbol_root: str) -> FuturesContractSpec:
    """
    Convenience Getter.

    Args:
        symbol_root: z.B. "NQ" oder "MNQ"
    """

    specs = get_cme_equity_index_contract_specs()
    try:
        return specs[symbol_root.upper()]
    except KeyError as exc:
        raise KeyError(f"Unknown CME contract spec for symbol_root={symbol_root!r}") from exc


__all__ = [
    "FuturesContractSpec",
    "get_cme_equity_index_contract_specs",
    "get_contract_spec",
]
