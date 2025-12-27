#!/usr/bin/env python
from __future__ import annotations

import argparse
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path
from typing import Sequence

# Standard-Pfad für den Report (aus Repo-Root ausgeführt)
REPORT_PATH = Path("docs/research/R_AND_D_EL_KAROUI_VOL_MODEL_V1.md")

# Defaults – bei Bedarf anpassen
DEFAULT_SYMBOLS: list[str] = ["SPY", "QQQ", "EURUSD"]
DEFAULT_DATE_RANGES: list[str] = [
    "2008-01-01:2025-01-01",
    "2015-01-01:2025-01-01",
    "2020-01-01:2025-01-01",
]
DEFAULT_MAPPING_VARIANTS: list[str] = ["default", "conservative", "aggressive"]


# ---------------------------------------------------------------------------
# Data-Strukturen
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class BacktestRunConfig:
    """Konfiguration für einen einzelnen Backtest-Run."""

    symbol: str
    start_date: date
    end_date: date
    mapping_variant: str

    @property
    def date_range_label(self) -> str:
        return f"{self.start_date.isoformat()} – {self.end_date.isoformat()}"


@dataclass
class BacktestResult:
    """Kompaktes Backtest-Ergebnis für das Reporting."""

    symbol: str
    date_range_label: str
    mapping_variant: str
    sharpe: float
    max_drawdown: float  # z.B. -0.25 für -25%
    annual_return: float  # z.B. 0.12 für 12% p.a.
    volatility: float  # z.B. 0.20 für 20% p.a.
    time_in_market: float  # 0.0–1.0 (wird im Report in % umgerechnet)


# ---------------------------------------------------------------------------
# Helpers zum Erzeugen der Run-Konfigurationen
# ---------------------------------------------------------------------------


def parse_date_range(range_str: str) -> tuple[date, date]:
    """Parst 'YYYY-MM-DD:YYYY-MM-DD' in (start_date, end_date)."""
    try:
        start_str, end_str = range_str.split(":", 1)
    except ValueError as exc:
        raise ValueError(
            f"Ungültiges Date-Range-Format '{range_str}', erwartet 'YYYY-MM-DD:YYYY-MM-DD'."
        ) from exc

    start = datetime.strptime(start_str.strip(), "%Y-%m-%d").date()
    end = datetime.strptime(end_str.strip(), "%Y-%m-%d").date()
    return start, end


def generate_run_configs(
    symbols: Sequence[str],
    date_ranges: Sequence[str],
    mapping_variants: Sequence[str],
) -> list[BacktestRunConfig]:
    """Erzeugt das kartesische Produkt aller Runs."""
    configs: list[BacktestRunConfig] = []
    for symbol in symbols:
        for dr in date_ranges:
            start, end = parse_date_range(dr)
            for mv in mapping_variants:
                configs.append(
                    BacktestRunConfig(
                        symbol=symbol,
                        start_date=start,
                        end_date=end,
                        mapping_variant=mv,
                    )
                )
    return configs


# ---------------------------------------------------------------------------
# Backtest-Hook – HIER an die Peak_Trade-Infrastruktur andocken
# ---------------------------------------------------------------------------


def run_el_karoui_backtest(config: BacktestRunConfig) -> BacktestResult:
    """
    Führt einen einzelnen Backtest-Run für das El-Karoui-Volatilitätsmodell aus.

    WICHTIG:
    - Diese Funktion ist der Integration-Hook.
    - Bitte an eure bestehende Backtest-/Strategy-API anbinden
      (BacktestEngine + Strategy-Registry).
    - Es dürfen KEINE Live-/Paper-/Testnet-Orders ausgelöst werden,
      nur Backtest/Research.

    Beispiel (PSEUDO-CODE – BITTE ANPASSEN):

        from src.backtest.engine import run_single_strategy_backtest
        from src.strategies.registry import get_strategy_class

        def run_el_karoui_backtest(config: BacktestRunConfig) -> BacktestResult:
            strategy_cls = get_strategy_class("el_karoui_vol_model")
            result = run_single_strategy_backtest(
                symbol=config.symbol,
                start_date=config.start_date,
                end_date=config.end_date,
                strategy_cls=strategy_cls,
                strategy_kwargs={"mapping_variant": config.mapping_variant},
                run_mode="research",
            )
            return BacktestResult(
                symbol=config.symbol,
                date_range_label=config.date_range_label,
                mapping_variant=config.mapping_variant,
                sharpe=result.metrics.sharpe,
                max_drawdown=result.metrics.max_drawdown,
                annual_return=result.metrics.annual_return,
                volatility=result.metrics.volatility,
                time_in_market=result.metrics.time_in_market,
            )

    In dieser Vorlage raisen wir zunächst NotImplementedError,
    bis die Integration implementiert wird.
    """
    raise NotImplementedError(
        "Bitte run_el_karoui_backtest(...) an die echte Backtest-Infrastruktur anbinden."
    )


# ---------------------------------------------------------------------------
# Orchestrierung & Reporting
# ---------------------------------------------------------------------------


def run_research(
    symbols: Sequence[str] | None = None,
    date_ranges: Sequence[str] | None = None,
    mapping_variants: Sequence[str] | None = None,
) -> list[BacktestResult]:
    """
    Führt alle Backtests im Research-Grid aus und liefert aggregierte Ergebnisse.
    """
    symbols = list(symbols or DEFAULT_SYMBOLS)
    date_ranges = list(date_ranges or DEFAULT_DATE_RANGES)
    mapping_variants = list(mapping_variants or DEFAULT_MAPPING_VARIANTS)

    configs = generate_run_configs(symbols, date_ranges, mapping_variants)
    results: list[BacktestResult] = []

    for cfg in configs:
        result = run_el_karoui_backtest(cfg)
        results.append(result)

    return results


def _format_float(value: float, decimals: int = 2) -> str:
    return f"{value:.{decimals}f}"


def _format_pct(value: float, decimals: int = 1) -> str:
    return f"{value * 100:.{decimals}f}%"


def results_to_markdown(
    results: Sequence[BacktestResult],
    symbols: Sequence[str],
    date_ranges: Sequence[str],
    mapping_variants: Sequence[str],
) -> str:
    """
    Erzeugt einen Markdown-Report aus den Ergebnissen.

    - Gruppiert nach Symbol.
    - Pro Symbol eine Tabelle über Date-Range × Mapping-Variante.
    """
    lines: list[str] = []

    # Header
    lines.append("# R&D Report – El Karoui Volatility Model v1")
    lines.append("")
    lines.append(
        "_Dieser Report wurde automatisiert durch "
        "`scripts/research_el_karoui_vol_model.py` erzeugt._"
    )
    lines.append("")
    lines.append("## Experiment-Setup")
    lines.append("")
    lines.append("- **Strategie:** ElKarouiVolatilityStrategy (Vol-Regime-Modell)")
    lines.append(f"- **Symbole:** {', '.join(symbols)}")
    lines.append(f"- **Date-Ranges:** {', '.join(date_ranges)}")
    lines.append(f"- **Mapping-Varianten:** {', '.join(mapping_variants)}")
    lines.append("")

    # Ergebnisse nach Symbol gruppieren
    results_by_symbol: dict[str, list[BacktestResult]] = {}
    for r in results:
        results_by_symbol.setdefault(r.symbol, []).append(r)

    for symbol in sorted(results_by_symbol.keys()):
        lines.append(f"## Ergebnisse für {symbol}")
        lines.append("")
        lines.append(
            "| Date-Range | Mapping | Sharpe | Annual Return | "
            "Max Drawdown | Volatility | Time in Market |"
        )
        lines.append(
            "|------------|---------|--------|---------------|"
            "--------------|------------|----------------|"
        )

        # sortiere nach Date-Range, dann Mapping
        symbol_results = sorted(
            results_by_symbol[symbol],
            key=lambda r: (r.date_range_label, r.mapping_variant),
        )

        for r in symbol_results:
            lines.append(
                "| "
                f"{r.date_range_label} | "
                f"{r.mapping_variant} | "
                f"{_format_float(r.sharpe, 2)} | "
                f"{_format_pct(r.annual_return, 2)} | "
                f"{_format_pct(r.max_drawdown, 2)} | "
                f"{_format_pct(r.volatility, 2)} | "
                f"{_format_pct(r.time_in_market, 1)} |"
            )
        lines.append("")

    # kurze generische Interpretation
    lines.append("## Kurze Interpretation (generisch)")
    lines.append("")
    lines.append(
        "- **LOW-Vol-Regime:** Erwartet höhere Time-in-Market und tendenziell "
        "höhere Rendite bei moderater Volatilität."
    )
    lines.append(
        "- **MEDIUM-Vol-Regime:** Leicht reduzierte Exposure, moderater "
        "Kompromiss zwischen Rendite und Risiko."
    )
    lines.append(
        "- **HIGH-Vol-Regime:** Starke Exposurereduktion (flat oder nahezu flat), "
        "Ziel ist Reduktion von Drawdowns auf Kosten von Rendite."
    )
    lines.append("")
    lines.append(
        "Bitte spezifische Ergebnisse je Symbol/Zeitraum interpretieren und mit "
        "anderen Strategien/Modellen (z.B. Armstrong) vergleichen."
    )
    lines.append("")

    return "\n".join(lines)


def write_report(markdown: str, output_path: Path = REPORT_PATH) -> None:
    """
    Schreibt den Markdown-Report auf die Platte (idempotent).
    """
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(markdown, encoding="utf-8")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def _parse_cli_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Research-Workflow für das El-Karoui-Volatilitätsmodell. "
            "Führt Backtests über Symbol × Date-Range × Mapping-Variante aus "
            "und erzeugt einen Markdown-Report."
        )
    )
    parser.add_argument(
        "--symbols",
        type=str,
        default=",".join(DEFAULT_SYMBOLS),
        help=(
            "Komma-separierte Liste von Symbolen, z.B. 'SPY,QQQ,EURUSD'. "
            f"Default: {','.join(DEFAULT_SYMBOLS)}"
        ),
    )
    parser.add_argument(
        "--date-ranges",
        type=str,
        default=",".join(DEFAULT_DATE_RANGES),
        help=(
            "Komma-separierte Liste von Date-Ranges im Format "
            "'YYYY-MM-DD:YYYY-MM-DD'. "
            f"Default: {','.join(DEFAULT_DATE_RANGES)}"
        ),
    )
    parser.add_argument(
        "--mapping-variants",
        type=str,
        default=",".join(DEFAULT_MAPPING_VARIANTS),
        help=(
            "Komma-separierte Liste von Mapping-Varianten, z.B. "
            "'default,conservative,aggressive'. "
            f"Default: {','.join(DEFAULT_MAPPING_VARIANTS)}"
        ),
    )
    parser.add_argument(
        "--output-path",
        type=str,
        default=str(REPORT_PATH),
        help=(f"Pfad für den generierten Markdown-Report (Default: {REPORT_PATH.as_posix()})"),
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Zeigt nur die Run-Konfigurationen an, führt aber keine Backtests aus.",
    )
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    """
    CLI-Einstiegspunkt für den Research-Workflow.

    Returns:
        0 bei Erfolg, 1 bei Fehler.
    """
    args = _parse_cli_args(argv)

    symbols = [s.strip() for s in args.symbols.split(",") if s.strip()]
    date_ranges = [dr.strip() for dr in args.date_ranges.split(",") if dr.strip()]
    mapping_variants = [mv.strip() for mv in args.mapping_variants.split(",") if mv.strip()]
    output_path = Path(args.output_path)

    print("=" * 70)
    print("  El Karoui Volatility Model – Research Workflow")
    print("=" * 70)
    print(f"  Symbole:          {symbols}")
    print(f"  Date-Ranges:      {date_ranges}")
    print(f"  Mapping-Varianten: {mapping_variants}")
    print(f"  Output:           {output_path}")
    print("=" * 70)

    configs = generate_run_configs(symbols, date_ranges, mapping_variants)
    print(f"\n→ {len(configs)} Backtest-Runs geplant.\n")

    if args.dry_run:
        print("Dry-Run – keine Backtests ausgeführt.\n")
        for i, cfg in enumerate(configs, start=1):
            print(f"  [{i:3}] {cfg.symbol} | {cfg.date_range_label} | {cfg.mapping_variant}")
        return 0

    # Backtests ausführen
    try:
        results = run_research(
            symbols=symbols,
            date_ranges=date_ranges,
            mapping_variants=mapping_variants,
        )
    except NotImplementedError as exc:
        print(f"\n⚠️  FEHLER: {exc}\n")
        print(
            "Bitte implementiere run_el_karoui_backtest(...) und binde "
            "die Funktion an die Peak_Trade-Backtest-Infrastruktur an."
        )
        return 1

    # Report generieren
    markdown = results_to_markdown(
        results=results,
        symbols=symbols,
        date_ranges=date_ranges,
        mapping_variants=mapping_variants,
    )
    write_report(markdown, output_path)

    print(f"\n✓ Report geschrieben: {output_path}\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
