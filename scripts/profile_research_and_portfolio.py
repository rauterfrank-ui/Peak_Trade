#!/usr/bin/env python3
"""
Peak_Trade Performance Profiling Script (Phase 61)
===================================================

Dev-Tool zum Messen der Laufzeit typischer Research-/Portfolio-Szenarien.

Verwendung:
    # Alle Szenarien ausführen
    python scripts/profile_research_and_portfolio.py

    # Nur bestimmte Szenarien
    python scripts/profile_research_and_portfolio.py --scenario portfolio_multi_style_moderate

    # Szenarien auflisten
    python scripts/profile_research_and_portfolio.py --list
"""
from __future__ import annotations

import argparse
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional


@dataclass
class Scenario:
    """Ein Benchmark-Szenario mit Name und Command."""

    name: str
    command: List[str]
    description: str = ""


# Definiere Benchmark-Szenarien
SCENARIOS = [
    Scenario(
        name="portfolio_multi_style_moderate",
        command=[
            sys.executable,
            "scripts/research_cli.py",
            "portfolio",
            "--config",
            "config/config.toml",
            "--portfolio-preset",
            "multi_style_moderate",
            "--format",
            "both",
        ],
        description="Portfolio-Backtest & Reporting für multi_style_moderate",
    ),
    Scenario(
        name="pipeline_rsi_reversion_basic",
        command=[
            sys.executable,
            "scripts/research_cli.py",
            "pipeline",
            "--sweep-name",
            "rsi_reversion_basic",
            "--config",
            "config/config.toml",
            "--format",
            "both",
            "--with-plots",
            "--top-n",
            "3",
        ],
        description="Research-Pipeline v2 mit Sweep, Top-N, Plots",
    ),
    Scenario(
        name="portfolio_robustness_multi_style_moderate",
        command=[
            sys.executable,
            "scripts/run_portfolio_robustness.py",
            "--config",
            "config/config.toml",
            "--portfolio-preset",
            "multi_style_moderate",
            "--format",
            "both",
        ],
        description="Portfolio-Robustness-Analyse für multi_style_moderate",
    ),
]


def run_scenario(scenario: Scenario, verbose: bool = False) -> float:
    """
    Führt ein Szenario aus und misst die Laufzeit.

    Args:
        scenario: Das auszuführende Szenario
        verbose: Ob zusätzliche Ausgabe gewünscht ist

    Returns:
        Laufzeit in Sekunden

    Raises:
        subprocess.CalledProcessError: Wenn der Command fehlschlägt
    """
    if verbose:
        print(f"▶️  Starte: {scenario.name}")
        print(f"   Command: {' '.join(scenario.command)}")

    start = time.perf_counter()
    result = subprocess.run(
        scenario.command,
        check=True,
        capture_output=not verbose,
        cwd=Path(__file__).parent.parent,
    )
    end = time.perf_counter()

    duration = end - start

    if verbose:
        print(f"✅ Abgeschlossen: {scenario.name} ({duration:.2f}s)")
        if result.returncode != 0:
            print(f"   ⚠️  Returncode: {result.returncode}")

    return duration


def format_table(results: List[tuple[str, float]], markdown: bool = False) -> str:
    """
    Formatiert Ergebnisse als Tabelle.

    Args:
        results: Liste von (scenario_name, duration_seconds) Tupeln
        markdown: Ob Markdown-Format gewünscht ist

    Returns:
        Formatierte Tabelle als String
    """
    if not results:
        return "Keine Ergebnisse."

    if markdown:
        lines = [
            "| Scenario | Duration (s) |",
            "|----------|-------------|",
        ]
        for name, duration in results:
            lines.append(f"| {name} | {duration:.2f} |")
        return "\n".join(lines)
    else:
        # Text-Tabelle
        max_name_len = max(len(name) for name, _ in results)
        header = f"{'Scenario':<{max_name_len}}  Duration (s)"
        separator = "-" * len(header)
        lines = [header, separator]
        for name, duration in results:
            lines.append(f"{name:<{max_name_len}}  {duration:>10.2f}")
        return "\n".join(lines)


def list_scenarios() -> None:
    """Listet alle verfügbaren Szenarien auf."""
    print("Verfügbare Benchmark-Szenarien:\n")
    for i, scenario in enumerate(SCENARIOS, 1):
        print(f"{i}. {scenario.name}")
        print(f"   {scenario.description}")
        print(f"   Command: {' '.join(scenario.command)}")
        print()


def parse_args() -> argparse.Namespace:
    """Parst Command-Line-Argumente."""
    parser = argparse.ArgumentParser(
        description="Profile Peak_Trade research/portfolio scenarios.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Beispiele:
  # Alle Szenarien ausführen
  python scripts/profile_research_and_portfolio.py

  # Nur bestimmte Szenarien
  python scripts/profile_research_and_portfolio.py --scenario portfolio_multi_style_moderate

  # Szenarien auflisten
  python scripts/profile_research_and_portfolio.py --list
        """,
    )
    parser.add_argument(
        "--scenario",
        "-s",
        action="append",
        help="Name of scenario to run (can be used multiple times). If omitted, all scenarios run.",
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="List available scenarios and exit.",
    )
    parser.add_argument(
        "--markdown",
        action="store_true",
        help="Output results in Markdown format.",
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Verbose output during execution.",
    )
    return parser.parse_args()


def main() -> int:
    """Hauptfunktion."""
    args = parse_args()

    # Szenarien auflisten
    if args.list:
        list_scenarios()
        return 0

    # Szenarien filtern
    scenarios_to_run = SCENARIOS
    if args.scenario:
        scenario_names = set(args.scenario)
        scenarios_to_run = [s for s in SCENARIOS if s.name in scenario_names]
        if not scenarios_to_run:
            print(f"❌ Keine Szenarien gefunden für: {', '.join(args.scenario)}")
            print("\nVerfügbare Szenarien:")
            for s in SCENARIOS:
                print(f"  - {s.name}")
            return 1

    # Szenarien ausführen
    print("🚀 Peak_Trade Performance Profiling")
    print("=" * 70)
    print(f"Anzahl Szenarien: {len(scenarios_to_run)}\n")

    results: List[tuple[str, float]] = []

    for i, scenario in enumerate(scenarios_to_run, 1):
        print(f"[{i}/{len(scenarios_to_run)}] {scenario.name}...")
        try:
            duration = run_scenario(scenario, verbose=args.verbose)
            results.append((scenario.name, duration))
            print(f"✅ {scenario.name}: {duration:.2f}s\n")
        except subprocess.CalledProcessError as e:
            print(f"❌ {scenario.name}: Fehler (Returncode {e.returncode})")
            if not args.verbose and e.stderr:
                print(f"   Stderr: {e.stderr.decode()[:200]}")
            return 1
        except KeyboardInterrupt:
            print("\n⚠️  Abgebrochen durch Benutzer.")
            return 130
        except Exception as e:
            print(f"❌ {scenario.name}: Unerwarteter Fehler: {e}")
            return 1

    # Ergebnisse ausgeben
    print("\n" + "=" * 70)
    print("📊 Ergebnisse")
    print("=" * 70)
    print()
    print(format_table(results, markdown=args.markdown))
    print()

    return 0


if __name__ == "__main__":
    sys.exit(main())








