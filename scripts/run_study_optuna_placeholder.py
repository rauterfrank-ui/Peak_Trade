#!/usr/bin/env python3
"""
Peak_Trade Optuna Study Runner (J2 minimal slice)
=================================================
Kleiner, lokaler Demo-Runner ohne Research-/Trading-Logik: Toy-Objective, In-Memory-Study,
Standard: Dry-Run (keine Optuna-Ausführung). Kein Netzwerk, keine Exchange-/Order-Pfade.

Siehe auch: ``scripts/run_optuna_study.py`` für die vollständige Strategy-Integration.
"""

from __future__ import annotations

import argparse
import sys
from typing import Any

# ---------------------------------------------------------------------------
# Optuna (optional)
# ---------------------------------------------------------------------------

try:
    import optuna

    OPTUNA_AVAILABLE = True
except ImportError:
    optuna = None  # type: ignore[assignment]
    OPTUNA_AVAILABLE = False


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Minimaler Optuna Demo-Study-Runner (Toy-Objective, In-Memory). "
            "Standard: Dry-Run — keine Study-Ausführung ohne --no-dry-run. "
            "NO-LIVE: kein Markt, keine Exchange-/Order-Pfade."
        ),
        epilog=(
            "Dieses Skript ist ein J2-Placeholder/Demo-Pfad (Toy-Objective), "
            "keine Markt- oder Live-Ausführung. "
            "Vollständige Strategy-Optimierung: scripts/run_optuna_study.py"
        ),
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--study-name",
        type=str,
        default="peak_trade_j2_toy_demo",
        help="Name der Optuna-Study (nur Metadaten/In-Memory).",
    )
    parser.add_argument(
        "--trials",
        type=int,
        default=5,
        metavar="N",
        help="Anzahl Trials für die Demo-Study.",
    )
    parser.add_argument(
        "--direction",
        type=str,
        choices=("minimize", "maximize"),
        default="minimize",
        help="Optimierungsrichtung für das Toy-Objective.",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Seed für den RandomSampler (reproduzierbare Demo-Runs).",
    )
    parser.add_argument(
        "--dry-run",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Nur Plan ausgeben (Standard: an). Mit --no-dry-run die Demo-Study ausführen.",
    )
    return parser.parse_args(argv)


def _toy_objective(trial: Any, direction: str) -> float:
    """Deterministisches Toy-Objective: Optimum bei a=b=0.5."""
    a = trial.suggest_float("a", 0.0, 1.0)
    b = trial.suggest_float("b", 0.0, 1.0)
    loss = (a - 0.5) ** 2 + (b - 0.5) ** 2
    if direction == "minimize":
        return float(loss)
    return float(1.0 - loss)


def run_toy_study(
    *,
    study_name: str,
    n_trials: int,
    direction: str,
    seed: int,
) -> dict[str, Any]:
    """Führt die In-Memory-Demo-Study aus (benötigt Optuna)."""
    if not OPTUNA_AVAILABLE or optuna is None:
        raise RuntimeError("Optuna ist nicht installiert.")

    sampler = optuna.samplers.RandomSampler(seed=seed)
    study = optuna.create_study(
        study_name=study_name,
        direction=direction,
        sampler=sampler,
    )

    def objective(trial: Any) -> float:
        return _toy_objective(trial, direction)

    study.optimize(objective, n_trials=n_trials, show_progress_bar=False)
    return {
        "study_name": study_name,
        "n_trials_complete": len(study.trials),
        "best_value": study.best_value,
        "best_params": study.best_params,
        "direction": direction,
        "seed": seed,
    }


def print_plan(args: argparse.Namespace) -> None:
    """Menschenlesbare Ausgabe: Was passieren würde."""
    print("=" * 72)
    print("Peak_Trade — Optuna Demo Study (J2 Placeholder Runner)")
    print("=" * 72)
    print()
    print("Modus:        DRY-RUN (keine Optuna-Optimierung gestartet)")
    print("Study-Name:  ", args.study_name)
    print("Trials:      ", args.trials)
    print("Richtung:    ", args.direction)
    print("Seed:        ", args.seed)
    print("Optuna:      ", "verfügbar" if OPTUNA_AVAILABLE else "nicht installiert")
    print()
    print("Bei --no-dry-run würde eine reine In-Memory-Demo-Study laufen:")
    print("  - Toy-Objective: quadratische Abweichung um a=b=0.5 (kein Backtest, kein Markt).")
    print("  - Kein Storage auf Disk (Standard), kein Netzwerk.")
    print()
    if not OPTUNA_AVAILABLE:
        print("Hinweis: pip install optuna  (oder uv pip install optuna)")
        print()
    print("=" * 72)


def print_execute_plan(args: argparse.Namespace) -> None:
    """Kurz vor echter Ausführung."""
    print("=" * 72)
    print("Starte Demo-Study (In-Memory, Toy-Objective)")
    print("=" * 72)
    print(f"  study-name: {args.study_name}")
    print(f"  trials:     {args.trials}")
    print(f"  direction:  {args.direction}")
    print(f"  seed:       {args.seed}")
    print()


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)

    if args.trials < 1:
        print("Fehler: --trials muss >= 1 sein.", file=sys.stderr)
        return 2

    if args.dry_run:
        print_plan(args)
        return 0

    if not OPTUNA_AVAILABLE:
        print(
            "Optuna ist nicht installiert — Demo-Study kann nicht ausgeführt werden.\n"
            "  pip install optuna\n"
            "Dry-Run: python scripts/run_study_optuna_placeholder.py",
            file=sys.stderr,
        )
        return 1

    print_execute_plan(args)
    result = run_toy_study(
        study_name=args.study_name,
        n_trials=args.trials,
        direction=args.direction,
        seed=args.seed,
    )
    print("Ergebnis:")
    print(f"  best_value:   {result['best_value']}")
    print(f"  best_params:  {result['best_params']}")
    print(f"  trials (OK): {result['n_trials_complete']}")
    print()
    print("Fertig (nur Toy-Objective, keine Strategie-/Marktdaten).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
