# scripts/_market_data_provenance.py
"""Reine Metadaten-Hilfen für Marktdaten-Provenance in CLI-Manifesten (NO-LIVE).

v1: Mappt kanonische ``ohlcv_source``-Werte (siehe ``_shared_ohlcv_loader``) auf auditierbare Flags.
Keine Secrets, keine I/O.
"""

from __future__ import annotations

from typing import Any

from _shared_ohlcv_loader import (
    OHLCV_SOURCE_CSV,
    OHLCV_SOURCE_DUMMY,
    OHLCV_SOURCE_KRAKEN,
    normalize_ohlcv_source,
)


def build_market_data_provenance_v1(
    *,
    ohlcv_source: str,
    symbols: list[str],
    timeframe: str,
    n_bars: int,
    fetched_at_utc: str,
    dry_run_execution: bool = True,
) -> dict[str, Any]:
    """
    Baut den Block ``market_data_provenance`` für Forward-Evaluation-Manifeste.

    Semantik (v1):
    - ``dummy``: synthetische interne Reihe (kein Exchange).
    - ``kraken``: öffentliche REST-OHLCV (historische Kerzen), kein Order-Trading.
    - ``csv`` (inkl. normalisiertes ``fixture``): lokale Datei — ``local_file``, kein „live real“-Claim.
    """
    src = normalize_ohlcv_source(ohlcv_source)

    if src == OHLCV_SOURCE_DUMMY:
        source_kind = "synthetic"
        provider = "dummy"
        exchange = "none"
        is_synthetic = True
        is_fixture = False
    elif src == OHLCV_SOURCE_KRAKEN:
        source_kind = "historical_real"
        provider = "kraken"
        exchange = "kraken"
        is_synthetic = False
        is_fixture = False
    elif src == OHLCV_SOURCE_CSV:
        source_kind = "local_file"
        provider = "csv"
        exchange = "none"
        is_synthetic = False
        is_fixture = True
    else:  # pragma: no cover — normalize_ohlcv_source wirft bei unbekanntem Wert
        source_kind = "unknown"
        provider = "unknown"
        exchange = "unknown"
        is_synthetic = False
        is_fixture = False

    return {
        "schema_version": "market_data_provenance_v1",
        "ohlcv_source": src,
        "source_kind": source_kind,
        "provider": provider,
        "exchange": exchange,
        "symbols": list(symbols),
        "timeframe": timeframe,
        "n_bars": int(n_bars),
        "fetched_at_utc": fetched_at_utc,
        "is_mock": False,
        "is_synthetic": is_synthetic,
        "is_fixture": is_fixture,
        "dry_run_execution": bool(dry_run_execution),
    }
