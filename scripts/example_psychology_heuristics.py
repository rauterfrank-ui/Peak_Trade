#!/usr/bin/env python3
"""
Beispiel-Script: Psychologie-Heuristik-System
==============================================

Demonstriert die Verwendung des Psychologie-Heuristik-Systems für
Trigger-Training-Events.

Workflow:
1. Event-Features aus Rohdaten erstellen
2. Scores berechnen (pro Event & Achse)
3. Zu Cluster-Scores aggregieren
4. Heatmap-kompatible Daten generieren
5. Statistiken berechnen

Usage:
    python scripts/example_psychology_heuristics.py

Autor: Peak_Trade Quant-Psychologie-Heuristik-Designer
Datum: Dezember 2025
"""

from typing import List, Dict
from src.reporting.psychology_heuristics import (
    # Dataclasses
    TriggerTrainingPsychEventFeatures,
    TriggerTrainingPsychClusterScores,
    # Scoring
    score_fomo,
    score_loss_fear,
    score_impulsivity,
    score_hesitation,
    score_rule_break,
    # Aggregation
    aggregate_cluster_scores,
    compute_psychology_heatmap_from_events,
    # Beispiele
    create_example_mixed_events,
)
from src.reporting.psychology_heatmap import (
    calculate_cluster_statistics,
)
import json


def print_section(title: str):
    """Druckt eine formatierte Überschrift."""
    print("\n" + "=" * 80)
    print(f"  {title}")
    print("=" * 80 + "\n")


def demonstrate_event_scoring():
    """Zeigt Event-Level-Scoring für einzelne Events."""
    print_section("1️⃣  Event-Level Scoring")

    # Beispiel: FOMO-Event
    print("📌 FOMO-Event:")
    fomo_ev = TriggerTrainingPsychEventFeatures(
        cluster="Breakout / Breakdowns",
        event_type="ENTER",
        side="LONG",
        signal_strength=0.8,
        latency_s=6.0,  # Spät
        latency_window_s=3.0,
        price_move_since_signal_pct=0.8,  # Großer Move
        price_max_favorable_pct=0.9,
        price_max_adverse_pct=0.1,
        pnl_vs_ideal_bp=-25.0,
        had_valid_setup=True,
        entered_without_signal=False,
        opposite_to_signal=False,
        size_violation=False,
        risk_violation=False,
        recent_loss_streak=0,
        recent_skip_streak=0,
        manually_marked_fomo=True,
        manually_marked_fear=False,
        manually_marked_impulsive=False,
    )

    print(f"  Cluster: {fomo_ev.cluster}")
    print(f"  Type: {fomo_ev.event_type}")
    print(f"  Latency: {fomo_ev.latency_s}s (should be <= 3s)")
    print(f"  Price Move: {fomo_ev.price_move_since_signal_pct:.1%}")
    print(f"  Manual FOMO Mark: {fomo_ev.manually_marked_fomo}")
    print(f"\n  → Scores:")
    print(f"     FOMO:        {score_fomo(fomo_ev)} / 3")
    print(f"     Loss Fear:   {score_loss_fear(fomo_ev)} / 3")
    print(f"     Impulsivity: {score_impulsivity(fomo_ev)} / 3")
    print(f"     Hesitation:  {score_hesitation(fomo_ev)} / 3")
    print(f"     Rule Break:  {score_rule_break(fomo_ev)} / 3")

    # Beispiel: Regelbruch-Event
    print("\n📌 Regelbruch-Event:")
    rule_ev = TriggerTrainingPsychEventFeatures(
        cluster="Re-Entries / Scaling",
        event_type="ENTER",
        side="SHORT",
        signal_strength=0.8,
        latency_s=2.0,
        latency_window_s=3.0,
        price_move_since_signal_pct=0.2,
        price_max_favorable_pct=0.3,
        price_max_adverse_pct=0.1,
        pnl_vs_ideal_bp=-40.0,
        had_valid_setup=False,
        entered_without_signal=True,
        opposite_to_signal=True,  # Gegen Signal!
        size_violation=True,  # Zu groß!
        risk_violation=True,  # Risk verletzt!
        recent_loss_streak=0,
        recent_skip_streak=0,
        manually_marked_fomo=False,
        manually_marked_fear=False,
        manually_marked_impulsive=False,
    )

    print(f"  Cluster: {rule_ev.cluster}")
    print(f"  Type: {rule_ev.event_type}")
    print(f"  Opposite to Signal: {rule_ev.opposite_to_signal}")
    print(f"  Size Violation: {rule_ev.size_violation}")
    print(f"  Risk Violation: {rule_ev.risk_violation}")
    print(f"\n  → Scores:")
    print(f"     FOMO:        {score_fomo(rule_ev)} / 3")
    print(f"     Loss Fear:   {score_loss_fear(rule_ev)} / 3")
    print(f"     Impulsivity: {score_impulsivity(rule_ev)} / 3")
    print(f"     Hesitation:  {score_hesitation(rule_ev)} / 3")
    print(f"     Rule Break:  {score_rule_break(rule_ev)} / 3")


def demonstrate_cluster_aggregation():
    """Zeigt Aggregation von Events zu Cluster-Scores."""
    print_section("2️⃣  Cluster-Level Aggregation")

    # Erstelle mehrere Events für den gleichen Cluster
    events = [
        TriggerTrainingPsychEventFeatures(
            cluster="Trend-Folge Einstiege",
            event_type="ENTER",
            side="LONG",
            signal_strength=0.8,
            latency_s=5.0,
            latency_window_s=3.0,
            price_move_since_signal_pct=0.4,
            price_max_favorable_pct=0.5,
            price_max_adverse_pct=0.1,
            pnl_vs_ideal_bp=-20.0,
            had_valid_setup=True,
            entered_without_signal=False,
            opposite_to_signal=False,
            size_violation=False,
            risk_violation=False,
            recent_loss_streak=0,
            recent_skip_streak=0,
            manually_marked_fomo=True,
            manually_marked_fear=False,
            manually_marked_impulsive=False,
        ),
        TriggerTrainingPsychEventFeatures(
            cluster="Trend-Folge Einstiege",
            event_type="ENTER",
            side="LONG",
            signal_strength=0.9,
            latency_s=2.0,
            latency_window_s=3.0,
            price_move_since_signal_pct=0.1,
            price_max_favorable_pct=0.2,
            price_max_adverse_pct=0.05,
            pnl_vs_ideal_bp=-5.0,
            had_valid_setup=True,
            entered_without_signal=False,
            opposite_to_signal=False,
            size_violation=False,
            risk_violation=False,
            recent_loss_streak=0,
            recent_skip_streak=0,
            manually_marked_fomo=False,
            manually_marked_fear=False,
            manually_marked_impulsive=False,
        ),
        TriggerTrainingPsychEventFeatures(
            cluster="Trend-Folge Einstiege",
            event_type="NO_ACTION",
            side=None,
            signal_strength=0.9,
            latency_s=10.0,
            latency_window_s=3.0,
            price_move_since_signal_pct=0.6,
            price_max_favorable_pct=0.7,
            price_max_adverse_pct=0.05,
            pnl_vs_ideal_bp=-50.0,
            had_valid_setup=True,
            entered_without_signal=False,
            opposite_to_signal=False,
            size_violation=False,
            risk_violation=False,
            recent_loss_streak=0,
            recent_skip_streak=4,
            manually_marked_fomo=False,
            manually_marked_fear=False,
            manually_marked_impulsive=False,
        ),
    ]

    print(f"📊 Aggregiere {len(events)} Events für Cluster 'Trend-Folge Einstiege':")
    print(f"   - Event 1: ENTER mit FOMO (spät + großer Move)")
    print(f"   - Event 2: ENTER normal (rechtzeitig, kleiner Move)")
    print(f"   - Event 3: NO_ACTION mit Zögern (Setup verpasst, Skip-Streak)")

    cluster_scores = aggregate_cluster_scores(events)

    print(f"\n✅ Cluster-Score '{cluster_scores[0].cluster}':")
    print(f"   FOMO:        {cluster_scores[0].fomo} / 3")
    print(f"   Loss Fear:   {cluster_scores[0].loss_fear} / 3")
    print(f"   Impulsivity: {cluster_scores[0].impulsivity} / 3")
    print(f"   Hesitation:  {cluster_scores[0].hesitation} / 3")
    print(f"   Rule Break:  {cluster_scores[0].rule_break} / 3")

    print(f"\n💡 Interpretation:")
    if cluster_scores[0].fomo >= 2:
        print(f"   ⚠️  FOMO ist ein Thema (Score: {cluster_scores[0].fomo})")
    if cluster_scores[0].hesitation >= 2:
        print(f"   ⚠️  Zögern ist ein Thema (Score: {cluster_scores[0].hesitation})")
    if cluster_scores[0].fomo < 2 and cluster_scores[0].hesitation < 2:
        print(f"   ✅ Keine größeren Probleme in diesem Cluster")


def demonstrate_full_workflow():
    """Zeigt den vollständigen End-to-End-Workflow."""
    print_section("3️⃣  End-to-End Workflow")

    # 1. Erstelle gemischte Events
    print("📝 Schritt 1: Events erstellen")
    events = create_example_mixed_events()
    print(f"   Erstellt: {len(events)} Events")

    # Cluster-Übersicht
    clusters = {ev.cluster for ev in events}
    print(f"   Cluster: {', '.join(sorted(clusters))}")

    # 2. Heatmap-Daten berechnen
    print(f"\n🔥 Schritt 2: Heatmap-Daten berechnen")
    heatmap_data = compute_psychology_heatmap_from_events(events)
    print(f"   Generiert: {len(heatmap_data)} Heatmap-Rows")

    # 3. Ausgabe
    print(f"\n📊 Schritt 3: Heatmap-Daten (kompatibel mit Template)")
    for row in heatmap_data:
        print(f"\n   Cluster: {row['name']}")
        print(
            f"   ├─ FOMO:        Level {row['fomo']['heat_level']}, CSS: {row['fomo']['css_class']}"
        )
        print(
            f"   ├─ Loss Fear:   Level {row['loss_fear']['heat_level']}, CSS: {row['loss_fear']['css_class']}"
        )
        print(
            f"   ├─ Impulsivity: Level {row['impulsivity']['heat_level']}, CSS: {row['impulsivity']['css_class']}"
        )
        print(
            f"   ├─ Hesitation:  Level {row['hesitation']['heat_level']}, CSS: {row['hesitation']['css_class']}"
        )
        print(
            f"   └─ Rule Break:  Level {row['rule_break']['heat_level']}, CSS: {row['rule_break']['css_class']}"
        )

    # 4. Statistiken
    print(f"\n📈 Schritt 4: Statistiken berechnen")
    from src.reporting.psychology_heatmap import build_psychology_heatmap_rows

    rows = build_psychology_heatmap_rows(
        [
            {
                "name": row["name"],
                "fomo": row["fomo"]["value"],
                "loss_fear": row["loss_fear"]["value"],
                "impulsivity": row["impulsivity"]["value"],
                "hesitation": row["hesitation"]["value"],
                "rule_break": row["rule_break"]["value"],
            }
            for row in heatmap_data
        ]
    )
    stats = calculate_cluster_statistics(rows)

    print(f"\n   Total Clusters: {stats['total_clusters']}")
    print(f"\n   Average Scores:")
    for metric, value in stats["avg_scores"].items():
        print(f"     {metric:15s}: {value:.2f}")

    print(f"\n   Max Scores:")
    for metric, value in stats["max_scores"].items():
        print(f"     {metric:15s}: {value:.2f}")

    if stats["problem_clusters"]:
        print(f"\n   ⚠️  Problem-Cluster (Score >= 2.5):")
        for pc in stats["problem_clusters"]:
            print(f"     - {pc['name']}: Max-Score {pc['max_score']:.1f}")
    else:
        print(f"\n   ✅ Keine Problem-Cluster (alle Scores < 2.5)")


def demonstrate_json_export():
    """Zeigt JSON-Export für API/Frontend."""
    print_section("4️⃣  JSON Export (für API/Frontend)")

    events = create_example_mixed_events()
    heatmap_data = compute_psychology_heatmap_from_events(events)

    # Vereinfachtes Format für JSON-Export
    export_data = {
        "timestamp": "2025-12-10T12:00:00Z",
        "total_clusters": len(heatmap_data),
        "clusters": [
            {
                "name": row["name"],
                "scores": {
                    "fomo": row["fomo"]["heat_level"],
                    "loss_fear": row["loss_fear"]["heat_level"],
                    "impulsivity": row["impulsivity"]["heat_level"],
                    "hesitation": row["hesitation"]["heat_level"],
                    "rule_break": row["rule_break"]["heat_level"],
                },
            }
            for row in heatmap_data
        ],
    }

    json_str = json.dumps(export_data, indent=2)
    print("📤 JSON-Export:")
    print(json_str)


def demonstrate_integration_example():
    """Zeigt Integrations-Beispiel für Flask/Dashboard."""
    print_section("5️⃣  Integration in Flask/Dashboard")

    print("💡 Beispiel-Code für Flask-Route:\n")

    example_code = '''
from flask import render_template
from src.reporting.psychology_heuristics import (
    compute_psychology_heatmap_from_events,
    TriggerTrainingPsychEventFeatures,
)

@app.route("/trigger_training/psychology")
def trigger_training_psychology():
    """Zeigt Psychologie-Analyse."""

    # 1. Events aus DB laden (Beispiel)
    raw_events = load_trigger_training_events_from_db()

    # 2. In Event-Features konvertieren
    events = [
        TriggerTrainingPsychEventFeatures(
            cluster=determine_cluster(e),  # Deine Cluster-Logik
            event_type=e.event_type,
            side=e.side,
            signal_strength=e.signal_strength,
            latency_s=e.latency_s,
            latency_window_s=3.0,
            price_move_since_signal_pct=e.price_move_pct,
            price_max_favorable_pct=e.max_favorable_pct,
            price_max_adverse_pct=e.max_adverse_pct,
            pnl_vs_ideal_bp=e.pnl_diff_bp,
            had_valid_setup=e.had_setup,
            entered_without_signal=e.no_signal,
            opposite_to_signal=e.wrong_direction,
            size_violation=e.size_too_large,
            risk_violation=e.risk_violated,
            recent_loss_streak=calculate_loss_streak(e),
            recent_skip_streak=calculate_skip_streak(e),
            manually_marked_fomo=e.tags.get("fomo", False),
            manually_marked_fear=e.tags.get("fear", False),
            manually_marked_impulsive=e.tags.get("impulsive", False),
        )
        for e in raw_events
    ]

    # 3. Heatmap-Daten generieren
    heatmap_data = compute_psychology_heatmap_from_events(events)

    # 4. Template rendern
    return render_template(
        "trigger_training_psychology.html",
        heatmap_rows=heatmap_data,
        timestamp=datetime.now(),
    )
'''
    print(example_code)

    print("\n📄 Template-Code (Jinja2):\n")

    template_code = """
{% from 'psychology_heatmap_macro.html' import psychology_heatmap %}

<section class="psychology-analysis">
  <h1>Psychologie-Analyse: Trigger-Training</h1>

  {{ psychology_heatmap(heatmap_rows, show_legend=True, show_notes=True) }}

  <div class="mt-4">
    <a href="/trigger_training/drills" class="btn btn-primary">
      🎯 Gezieltes Training starten
    </a>
  </div>
</section>
"""
    print(template_code)


def main():
    """Hauptfunktion: Führt alle Demonstrationen aus."""
    print("\n")
    print("╔" + "═" * 78 + "╗")
    print("║" + " " * 78 + "║")
    print("║" + "  🧠 Psychologie-Heuristik-System für Peak_Trade".center(78) + "║")
    print("║" + "  Demonstration & Beispiele".center(78) + "║")
    print("║" + " " * 78 + "║")
    print("╚" + "═" * 78 + "╝")

    # Demonstrationen
    demonstrate_event_scoring()
    demonstrate_cluster_aggregation()
    demonstrate_full_workflow()
    demonstrate_json_export()
    demonstrate_integration_example()

    # Abschluss
    print_section("✅ Fertig!")
    print("📚 Weitere Informationen:")
    print("   - Modul:  src/reporting/psychology_heuristics.py")
    print("   - Tests:  tests/reporting/test_psychology_heuristics.py")
    print("   - Doku:   docs/psychology_heuristics.md")
    print("\n")


if __name__ == "__main__":
    main()
