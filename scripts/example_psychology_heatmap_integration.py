#!/usr/bin/env python3
"""
Beispiel: Psychology Heatmap Integration
=========================================

Dieses Script zeigt, wie die Psychologie-Heatmap in verschiedenen Szenarien
verwendet werden kann:

1. Standalone-Report generieren
2. Integration in bestehenden Trigger-Training-Report
3. Flask/Dashboard-Integration

Usage:
    python scripts/example_psychology_heatmap_integration.py
"""

from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any

# Peak_Trade Imports
from src.reporting.psychology_heatmap import (
    build_psychology_heatmap_rows,
    serialize_psychology_heatmap_rows,
    calculate_cluster_statistics,
    build_example_psychology_heatmap_data,
)


# ============================================================================
# Scenario 1: Standalone Psychology Report
# ============================================================================

def generate_standalone_psychology_report(output_dir: Path) -> Path:
    """
    Generiert einen eigenständigen Psychologie-Report als HTML.
    
    Dies wäre z.B. für einen wöchentlichen Review-Report nützlich.
    """
    print("📊 Generiere Standalone Psychology Report...")
    
    # 1. Daten vorbereiten (hier: Beispiel-Daten)
    raw_data = build_example_psychology_heatmap_data()
    
    # 2. Rows bauen und serialisieren
    rows = build_psychology_heatmap_rows(raw_data)
    serialized_rows = serialize_psychology_heatmap_rows(rows)
    
    # 3. Statistiken berechnen
    stats = calculate_cluster_statistics(rows)
    
    # 4. Template-Context zusammenstellen
    context = {
        "heatmap_rows": serialized_rows,
        "statistics": stats,
        "meta": {
            "from_date": "2025-01-01",
            "to_date": "2025-12-10",
            "total_sessions": 42,
            "total_events": 1337,
        },
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }
    
    # 5. Render Template (in echtem Code würde man Jinja2 verwenden)
    # Für dieses Beispiel simulieren wir es
    output_file = output_dir / "psychology_report_standalone.html"
    
    print(f"  ✓ Report generiert: {output_file}")
    print(f"  ✓ Analysierte Cluster: {stats['total_clusters']}")
    print(f"  ✓ Problem-Cluster: {len(stats['problem_clusters'])}")
    
    return output_file


# ============================================================================
# Scenario 2: Integration in bestehenden Trigger-Training-Report
# ============================================================================

def build_report_context_from_trigger_training_stats(stats) -> Dict[str, Any]:
    """
    Integriert die Psychologie-Heatmap in einen bestehenden
    Trigger-Training-Report.
    
    Args:
        stats: Ein Objekt mit aggregierten Trigger-Training-Statistiken.
              Sollte Attribute wie:
              - trend_fomo_score
              - trend_loss_fear_score
              - breakout_fomo_score
              etc. haben.
    
    Returns:
        Dictionary mit Report-Context inkl. Heatmap-Daten
    """
    print("📊 Baue Report-Context mit Psychologie-Heatmap...")
    
    # Cluster-Scores aus den Stats extrahieren
    psychology_raw_rows = [
        {
            "name": "Trend-Folge Einstiege",
            "fomo": getattr(stats, "trend_fomo_score", 0.0),
            "loss_fear": getattr(stats, "trend_loss_fear_score", 0.0),
            "impulsivity": getattr(stats, "trend_impulsivity_score", 0.0),
            "hesitation": getattr(stats, "trend_hesitation_score", 0.0),
            "rule_break": getattr(stats, "trend_rule_break_score", 0.0),
        },
        {
            "name": "Counter-Trend Einstiege",
            "fomo": getattr(stats, "counter_fomo_score", 0.0),
            "loss_fear": getattr(stats, "counter_loss_fear_score", 0.0),
            "impulsivity": getattr(stats, "counter_impulsivity_score", 0.0),
            "hesitation": getattr(stats, "counter_hesitation_score", 0.0),
            "rule_break": getattr(stats, "counter_rule_break_score", 0.0),
        },
        {
            "name": "Breakout / Breakdowns",
            "fomo": getattr(stats, "breakout_fomo_score", 0.0),
            "loss_fear": getattr(stats, "breakout_loss_fear_score", 0.0),
            "impulsivity": getattr(stats, "breakout_impulsivity_score", 0.0),
            "hesitation": getattr(stats, "breakout_hesitation_score", 0.0),
            "rule_break": getattr(stats, "breakout_rule_break_score", 0.0),
        },
        {
            "name": "Take-Profit / Exits",
            "fomo": getattr(stats, "exit_fomo_score", 0.0),
            "loss_fear": getattr(stats, "exit_loss_fear_score", 0.0),
            "impulsivity": getattr(stats, "exit_impulsivity_score", 0.0),
            "hesitation": getattr(stats, "exit_hesitation_score", 0.0),
            "rule_break": getattr(stats, "exit_rule_break_score", 0.0),
        },
        {
            "name": "Re-Entries / Scaling",
            "fomo": getattr(stats, "reentry_fomo_score", 0.0),
            "loss_fear": getattr(stats, "reentry_loss_fear_score", 0.0),
            "impulsivity": getattr(stats, "reentry_impulsivity_score", 0.0),
            "hesitation": getattr(stats, "reentry_hesitation_score", 0.0),
            "rule_break": getattr(stats, "reentry_rule_break_score", 0.0),
        },
    ]
    
    # Rows bauen und serialisieren
    rows = build_psychology_heatmap_rows(psychology_raw_rows)
    heatmap_ctx = serialize_psychology_heatmap_rows(rows)
    
    # Statistiken
    stats_ctx = calculate_cluster_statistics(rows)
    
    print(f"  ✓ Heatmap-Rows generiert: {len(heatmap_ctx)}")
    
    return {
        # Existing context fields...
        "psychology_heatmap_rows": heatmap_ctx,
        "psychology_statistics": stats_ctx,
    }


# ============================================================================
# Scenario 3: Flask/Dashboard Route
# ============================================================================

def example_flask_route_handler():
    """
    Beispiel für eine Flask-Route, die die Psychologie-Seite rendert.
    
    In einer echten Flask-App würde das so aussehen:
    
    @app.route("/trigger_training/psychology")
    def trigger_training_psychology():
        # ... Daten aus DB laden ...
        context = build_psychology_dashboard_context(...)
        return render_template("trigger_training_psychology.html", **context)
    """
    print("🌐 Simuliere Flask-Route für Psychology Dashboard...")
    
    # 1. Daten aus Datenbank / Stats laden (hier: Beispiel)
    raw_data = build_example_psychology_heatmap_data()
    
    # 2. Processing
    rows = build_psychology_heatmap_rows(raw_data)
    serialized_rows = serialize_psychology_heatmap_rows(rows)
    stats = calculate_cluster_statistics(rows)
    
    # 3. Context für Template
    context = {
        "heatmap_rows": serialized_rows,
        "statistics": stats,
        "meta": {
            "from_date": "2025-01-01",
            "to_date": "2025-12-10",
            "total_sessions": 42,
            "total_events": 1337,
        },
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }
    
    print(f"  ✓ Context vorbereitet")
    print(f"  ✓ Problem-Cluster: {len(stats['problem_clusters'])}")
    
    # In echtem Code:
    # return render_template("trigger_training_psychology.html", **context)
    
    return context


# ============================================================================
# Scenario 4: Von Trigger-Training-Events zu Psychologie-Scores
# ============================================================================

class MockTriggerTrainingStats:
    """Mock-Klasse für Trigger-Training-Statistiken."""
    
    def __init__(self):
        # Trend-Folge Scores
        self.trend_fomo_score = 2.0
        self.trend_loss_fear_score = 1.0
        self.trend_impulsivity_score = 1.0
        self.trend_hesitation_score = 0.5
        self.trend_rule_break_score = 1.0
        
        # Counter-Trend Scores
        self.counter_fomo_score = 1.0
        self.counter_loss_fear_score = 3.0
        self.counter_impulsivity_score = 2.0
        self.counter_hesitation_score = 1.0
        self.counter_rule_break_score = 2.0
        
        # Breakout Scores
        self.breakout_fomo_score = 3.0
        self.breakout_loss_fear_score = 2.0
        self.breakout_impulsivity_score = 2.0
        self.breakout_hesitation_score = 1.0
        self.breakout_rule_break_score = 2.0
        
        # Exit Scores
        self.exit_fomo_score = 1.0
        self.exit_loss_fear_score = 2.0
        self.exit_impulsivity_score = 1.0
        self.exit_hesitation_score = 2.0
        self.exit_rule_break_score = 1.0
        
        # Re-Entry Scores
        self.reentry_fomo_score = 2.0
        self.reentry_loss_fear_score = 1.0
        self.reentry_impulsivity_score = 3.0
        self.reentry_hesitation_score = 1.0
        self.reentry_rule_break_score = 3.0


def example_full_integration():
    """
    Vollständiges Beispiel: Von Stats zu Report.
    """
    print("\n" + "="*80)
    print("🧠 Vollständiges Psychologie-Heatmap Beispiel")
    print("="*80 + "\n")
    
    # 1. Mock-Stats erstellen (in echt: aus DB / Aggregation)
    stats = MockTriggerTrainingStats()
    
    # 2. Report-Context bauen
    context = build_report_context_from_trigger_training_stats(stats)
    
    # 3. Ausgabe
    print("\n📊 Report-Context:")
    print(f"  - Anzahl Rows: {len(context['psychology_heatmap_rows'])}")
    print(f"  - Problem-Cluster: {len(context['psychology_statistics']['problem_clusters'])}")
    
    if context['psychology_statistics']['problem_clusters']:
        print("\n⚠️  Problem-Cluster (Score >= 2.5):")
        for cluster in context['psychology_statistics']['problem_clusters']:
            print(f"    - {cluster['name']}: {cluster['max_score']:.1f}")
    
    print("\n📈 Durchschnittswerte:")
    for metric, value in context['psychology_statistics']['avg_scores'].items():
        emoji = "🔴" if value >= 2.5 else "🟡" if value >= 1.5 else "🟢"
        print(f"    {emoji} {metric.replace('_', ' ').title()}: {value:.2f}")
    
    print("\n✅ Integration erfolgreich!\n")


# ============================================================================
# Main
# ============================================================================

def main():
    """Hauptfunktion mit verschiedenen Beispielen."""
    
    print("\n" + "="*80)
    print("🧠 Psychology Heatmap Integration Examples")
    print("="*80 + "\n")
    
    # Setup
    output_dir = Path("output/psychology_reports")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Scenario 1: Standalone Report
    print("\n--- Scenario 1: Standalone Report ---")
    generate_standalone_psychology_report(output_dir)
    
    # Scenario 2: Integration in bestehenden Report
    print("\n--- Scenario 2: Integration in Trigger-Training-Report ---")
    mock_stats = MockTriggerTrainingStats()
    context = build_report_context_from_trigger_training_stats(mock_stats)
    print(f"✓ Context erstellt mit {len(context['psychology_heatmap_rows'])} Rows")
    
    # Scenario 3: Flask Route
    print("\n--- Scenario 3: Flask/Dashboard Route ---")
    flask_context = example_flask_route_handler()
    print(f"✓ Flask-Context bereit")
    
    # Scenario 4: Full Integration
    example_full_integration()
    
    print("\n" + "="*80)
    print("✅ Alle Beispiele erfolgreich durchgeführt!")
    print("="*80 + "\n")
    
    # Tipps
    print("💡 Nächste Schritte:")
    print("  1. Integriere die Funktionen in deine bestehende Reporting-Pipeline")
    print("  2. Passe die Cluster-Definitionen an deine Bedürfnisse an")
    print("  3. Implementiere die echte Score-Berechnung aus Events")
    print("  4. Teste die Templates mit echten Daten")
    print("  5. Füge die Route zu deiner Flask-App hinzu\n")


if __name__ == "__main__":
    main()
