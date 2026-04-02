# -*- coding: utf-8 -*-
"""
Gemeinsame CLI-Defaults und Argument-Gruppe für Forward-/Portfolio-OHLCV (J1).

Drei Skripte teilen denselben Parametervertrag für ``--n-bars``/``--bars``,
``--ohlcv-source`` und ``--timeframe`` (Kraken; Dummy ignoriert ``timeframe`` intern 1h).

Keine neuen Datenquellen — gemeinsame CLI-Normalisierung; Kraken-Pagination für große ``n-bars`` liegt im Loader.

NO-LIVE: keine Order-Ausführung; Kraken-Pfad nur öffentliche OHLCV (Stub), siehe Epilog-Helfer unten.
"""

from __future__ import annotations

import argparse

from _shared_ohlcv_loader import (
    KRAKEN_OHLCV_MAX_BARS,
    OHLCV_SOURCE_DUMMY,
    OHLCV_SOURCES,
    normalize_ohlcv_source,
)

DEFAULT_FORWARD_N_BARS = 200
DEFAULT_OHLCV_TIMEFRAME = "1h"

# Für ``argparse``-Epilog (Generate / Evaluate / Portfolio): einheitlicher J1-Scope-Hinweis.
FORWARD_PIPELINE_OHLCV_SCOPE_EPILOG = """
Scope (J1, NO-LIVE):
  Kein Live-Handel und keine Order-Ausführung (kein C1-/Execution-Scope).
  OHLCV: Default --ohlcv-source=dummy (offline); kraken = öffentliche REST-OHLCV nur zum
  Laden von Kursreihen; opt-in, Netzwerk nötig. Kein neuer Anbieter.
""".strip()


def append_forward_ohlcv_scope_epilog(parser: argparse.ArgumentParser) -> None:
    """Hängt den gemeinsamen J1/NO-LIVE-Epilog an (vorhandenes ``epilog`` wird davor gesetzt)."""
    extra = FORWARD_PIPELINE_OHLCV_SCOPE_EPILOG
    if parser.epilog:
        parser.epilog = extra + "\n\n" + parser.epilog
    else:
        parser.epilog = extra


# Übliche ccxt/Kraken-Timeframes (an ``fetch_ohlcv_df`` übergeben; Dummy bleibt synthetisch 1h).
OHLCV_TIMEFRAME_CHOICES = ("1m", "5m", "15m", "1h", "4h", "1d")


def parse_symbols_cli_arg(symbols_csv: str | None) -> list[str] | None:
    """
    Kommagetrennte Symbole wie ``BTC/EUR,ETH/EUR`` → Liste; ``None``/leer → ``None``.
    """
    if not symbols_csv or not str(symbols_csv).strip():
        return None
    return [x.strip() for x in str(symbols_csv).split(",") if x.strip()]


def add_shared_ohlcv_cli_group(
    parser: argparse.ArgumentParser,
    *,
    n_bars_dest: str = "n_bars",
    n_bars_flags: tuple[str, ...] = ("--n-bars",),
    n_bars_metavar: str = "N",
) -> None:
    """
    Fügt ``--n-bars``/``--bars``, ``--ohlcv-source`` und ``--timeframe`` hinzu.

    Args:
        parser: Ziel-``ArgumentParser``.
        n_bars_dest: ``dest`` für die Bar-Anzahl (z. B. ``bars`` im Portfolio-Skript).
        n_bars_flags: Option-Strings (Portfolio: ``--bars`` und ``--n-bars`` mit gleichem dest).
        n_bars_metavar: Metavar für die Hilfe.
    """
    parser.add_argument(
        *n_bars_flags,
        type=int,
        default=DEFAULT_FORWARD_N_BARS,
        metavar=n_bars_metavar,
        dest=n_bars_dest,
        help=(
            f"Anzahl OHLCV-Bars pro Symbol (Default: {DEFAULT_FORWARD_N_BARS}). "
            "Gleiche Semantik in generate_forward_signals, evaluate_forward_signals "
            "und run_portfolio_backtest_v2. Kraken: bis "
            f"{KRAKEN_OHLCV_MAX_BARS} Bars pro Request; bei größerem Wert Pagination im Loader."
        ),
    )
    parser.add_argument(
        "--ohlcv-source",
        type=normalize_ohlcv_source,
        default=OHLCV_SOURCE_DUMMY,
        metavar="|".join(OHLCV_SOURCES),
        help=(
            "OHLCV-Quelle: dummy (offline, Default, NO-LIVE) oder kraken (öffentliche REST-OHLCV; "
            f"Netzwerk nötig; große Fenster: mehrere Abrufe à max. {KRAKEN_OHLCV_MAX_BARS} Bars). "
            "Groß-/Kleinschreibung egal (wie load_ohlcv). Keine Orders."
        ),
    )
    parser.add_argument(
        "--timeframe",
        choices=OHLCV_TIMEFRAME_CHOICES,
        default=DEFAULT_OHLCV_TIMEFRAME,
        help=(
            "OHLCV-Timeframe für Kraken. Bei ohlcv-source=dummy bleibt die Serie synthetisch "
            "1h-getaktet; das Argument dient dem Abgleich mit Generate/Evaluate/Portfolio."
        ),
    )
