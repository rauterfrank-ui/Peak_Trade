"""
Tests für das Psychology Heatmap Modul
========================================

Unit-Tests für src.reporting.psychology_heatmap
"""

import pytest
from src.reporting.psychology_heatmap import (
    PsychologyHeatmapCell,
    PsychologyHeatmapRow,
    _score_to_heat_level,
    _create_heatmap_cell,
    build_psychology_heatmap_rows,
    serialize_psychology_heatmap_rows,
    build_example_psychology_heatmap_data,
    calculate_cluster_statistics,
)


class TestScoreToHeatLevel:
    """Tests für die Score-zu-Heat-Level-Konvertierung."""
    
    def test_level_0_boundary(self):
        """Test für Level 0 (kein Thema)."""
        assert _score_to_heat_level(0.0) == 0
        assert _score_to_heat_level(0.4) == 0
    
    def test_level_1_boundary(self):
        """Test für Level 1 (leicht)."""
        assert _score_to_heat_level(0.5) == 1
        assert _score_to_heat_level(1.0) == 1
        assert _score_to_heat_level(1.4) == 1
    
    def test_level_2_boundary(self):
        """Test für Level 2 (mittel)."""
        assert _score_to_heat_level(1.5) == 2
        assert _score_to_heat_level(2.0) == 2
        assert _score_to_heat_level(2.4) == 2
    
    def test_level_3_boundary(self):
        """Test für Level 3 (stark)."""
        assert _score_to_heat_level(2.5) == 3
        assert _score_to_heat_level(3.0) == 3
        assert _score_to_heat_level(5.0) == 3  # Auch Werte > 3 gehen auf Level 3


class TestCreateHeatmapCell:
    """Tests für die Heatmap-Cell-Erstellung."""
    
    def test_create_cell_level_0(self):
        """Test für Cell mit Level 0."""
        cell = _create_heatmap_cell(0.3)
        assert cell.value == 0.3
        assert cell.heat_level == 0
        assert cell.display_value == "0"
        assert cell.css_class == "heat-0"
    
    def test_create_cell_level_1(self):
        """Test für Cell mit Level 1."""
        cell = _create_heatmap_cell(1.0)
        assert cell.value == 1.0
        assert cell.heat_level == 1
        assert cell.display_value == "1"
        assert cell.css_class == "heat-1"
    
    def test_create_cell_level_2(self):
        """Test für Cell mit Level 2."""
        cell = _create_heatmap_cell(2.0)
        assert cell.value == 2.0
        assert cell.heat_level == 2
        assert cell.display_value == "2"
        assert cell.css_class == "heat-2"
    
    def test_create_cell_level_3(self):
        """Test für Cell mit Level 3."""
        cell = _create_heatmap_cell(3.0)
        assert cell.value == 3.0
        assert cell.heat_level == 3
        assert cell.display_value == "3"
        assert cell.css_class == "heat-3"
    
    def test_create_cell_rounding(self):
        """Test für Rundung der Display-Werte."""
        cell = _create_heatmap_cell(2.7)
        assert cell.display_value == "3"


class TestBuildPsychologyHeatmapRows:
    """Tests für build_psychology_heatmap_rows."""
    
    def test_build_single_row(self):
        """Test für einzelne Row."""
        raw_rows = [
            {
                "name": "Test Cluster",
                "fomo": 2.0,
                "loss_fear": 1.0,
                "impulsivity": 0.5,
                "hesitation": 2.5,
                "rule_break": 0.0,
            }
        ]
        
        rows = build_psychology_heatmap_rows(raw_rows)
        
        assert len(rows) == 1
        assert rows[0].name == "Test Cluster"
        assert rows[0].fomo.heat_level == 2
        assert rows[0].loss_fear.heat_level == 1
        assert rows[0].impulsivity.heat_level == 1
        assert rows[0].hesitation.heat_level == 3
        assert rows[0].rule_break.heat_level == 0
    
    def test_build_multiple_rows(self):
        """Test für mehrere Rows."""
        raw_rows = [
            {
                "name": "Cluster A",
                "fomo": 1.0,
                "loss_fear": 1.0,
                "impulsivity": 1.0,
                "hesitation": 1.0,
                "rule_break": 1.0,
            },
            {
                "name": "Cluster B",
                "fomo": 2.0,
                "loss_fear": 2.0,
                "impulsivity": 2.0,
                "hesitation": 2.0,
                "rule_break": 2.0,
            }
        ]
        
        rows = build_psychology_heatmap_rows(raw_rows)
        
        assert len(rows) == 2
        assert rows[0].name == "Cluster A"
        assert rows[1].name == "Cluster B"
    
    def test_build_missing_values(self):
        """Test für fehlende Werte (sollten auf 0.0 defaulten)."""
        raw_rows = [
            {
                "name": "Incomplete Cluster",
                "fomo": 1.0,
                # loss_fear fehlt
                # impulsivity fehlt
                # hesitation fehlt
                # rule_break fehlt
            }
        ]
        
        rows = build_psychology_heatmap_rows(raw_rows)
        
        assert len(rows) == 1
        assert rows[0].fomo.heat_level == 1
        assert rows[0].loss_fear.heat_level == 0
        assert rows[0].impulsivity.heat_level == 0
        assert rows[0].hesitation.heat_level == 0
        assert rows[0].rule_break.heat_level == 0


class TestSerializePsychologyHeatmapRows:
    """Tests für serialize_psychology_heatmap_rows."""
    
    def test_serialize_single_row(self):
        """Test für Serialisierung einer einzelnen Row."""
        raw_rows = [
            {
                "name": "Test Cluster",
                "fomo": 2.0,
                "loss_fear": 1.0,
                "impulsivity": 0.5,
                "hesitation": 2.5,
                "rule_break": 0.0,
            }
        ]
        
        rows = build_psychology_heatmap_rows(raw_rows)
        serialized = serialize_psychology_heatmap_rows(rows)
        
        assert len(serialized) == 1
        assert serialized[0]["name"] == "Test Cluster"
        assert serialized[0]["fomo"]["heat_level"] == 2
        assert serialized[0]["fomo"]["css_class"] == "heat-2"
        assert serialized[0]["fomo"]["display_value"] == "2"
    
    def test_serialize_preserves_all_fields(self):
        """Test dass alle Felder erhalten bleiben."""
        raw_rows = [{"name": "Test", "fomo": 1.0, "loss_fear": 1.0, "impulsivity": 1.0, "hesitation": 1.0, "rule_break": 1.0}]
        rows = build_psychology_heatmap_rows(raw_rows)
        serialized = serialize_psychology_heatmap_rows(rows)
        
        assert "name" in serialized[0]
        assert "fomo" in serialized[0]
        assert "loss_fear" in serialized[0]
        assert "impulsivity" in serialized[0]
        assert "hesitation" in serialized[0]
        assert "rule_break" in serialized[0]
        
        # Jedes Metric-Dict sollte alle Cell-Felder haben
        for metric in ["fomo", "loss_fear", "impulsivity", "hesitation", "rule_break"]:
            assert "value" in serialized[0][metric]
            assert "heat_level" in serialized[0][metric]
            assert "display_value" in serialized[0][metric]
            assert "css_class" in serialized[0][metric]


class TestBuildExamplePsychologyHeatmapData:
    """Tests für build_example_psychology_heatmap_data."""
    
    def test_example_data_structure(self):
        """Test dass Beispiel-Daten die richtige Struktur haben."""
        data = build_example_psychology_heatmap_data()
        
        assert isinstance(data, list)
        assert len(data) > 0
        
        for row in data:
            assert "name" in row
            assert "fomo" in row
            assert "loss_fear" in row
            assert "impulsivity" in row
            assert "hesitation" in row
            assert "rule_break" in row
    
    def test_example_data_values_in_range(self):
        """Test dass alle Beispiel-Werte im Bereich 0-3 liegen."""
        data = build_example_psychology_heatmap_data()
        
        for row in data:
            for metric in ["fomo", "loss_fear", "impulsivity", "hesitation", "rule_break"]:
                assert 0.0 <= row[metric] <= 3.0


class TestCalculateClusterStatistics:
    """Tests für calculate_cluster_statistics."""
    
    def test_statistics_empty_rows(self):
        """Test für leere Row-Liste."""
        rows = []
        stats = calculate_cluster_statistics(rows)
        
        assert stats["total_clusters"] == 0
        assert stats["avg_scores"] == {}
        assert stats["max_scores"] == {}
        assert stats["problem_clusters"] == []
    
    def test_statistics_single_row(self):
        """Test für einzelne Row."""
        raw_rows = [
            {
                "name": "Test Cluster",
                "fomo": 2.0,
                "loss_fear": 1.0,
                "impulsivity": 0.5,
                "hesitation": 2.5,
                "rule_break": 3.0,
            }
        ]
        
        rows = build_psychology_heatmap_rows(raw_rows)
        stats = calculate_cluster_statistics(rows)
        
        assert stats["total_clusters"] == 1
        assert stats["avg_scores"]["fomo"] == 2.0
        assert stats["avg_scores"]["loss_fear"] == 1.0
        assert stats["avg_scores"]["impulsivity"] == 0.5
        assert stats["avg_scores"]["hesitation"] == 2.5
        assert stats["avg_scores"]["rule_break"] == 3.0
        
        assert stats["max_scores"]["rule_break"] == 3.0
        
        # Sollte als Problem-Cluster erkannt werden (rule_break >= 2.5)
        assert len(stats["problem_clusters"]) == 1
        assert stats["problem_clusters"][0]["name"] == "Test Cluster"
    
    def test_statistics_multiple_rows(self):
        """Test für mehrere Rows."""
        raw_rows = [
            {
                "name": "Cluster A",
                "fomo": 1.0,
                "loss_fear": 2.0,
                "impulsivity": 0.5,
                "hesitation": 1.5,
                "rule_break": 1.0,
            },
            {
                "name": "Cluster B",
                "fomo": 3.0,
                "loss_fear": 1.0,
                "impulsivity": 2.5,
                "hesitation": 0.5,
                "rule_break": 2.0,
            }
        ]
        
        rows = build_psychology_heatmap_rows(raw_rows)
        stats = calculate_cluster_statistics(rows)
        
        assert stats["total_clusters"] == 2
        
        # Durchschnitt von 1.0 und 3.0
        assert stats["avg_scores"]["fomo"] == 2.0
        
        # Max von 3.0
        assert stats["max_scores"]["fomo"] == 3.0
        
        # Cluster B sollte als Problem erkannt werden (fomo=3.0, impulsivity=2.5)
        assert len(stats["problem_clusters"]) == 1
        assert stats["problem_clusters"][0]["name"] == "Cluster B"
    
    def test_statistics_no_problem_clusters(self):
        """Test für Rows ohne Problem-Cluster."""
        raw_rows = [
            {
                "name": "Good Cluster",
                "fomo": 1.0,
                "loss_fear": 1.5,
                "impulsivity": 1.0,
                "hesitation": 2.0,
                "rule_break": 1.5,
            }
        ]
        
        rows = build_psychology_heatmap_rows(raw_rows)
        stats = calculate_cluster_statistics(rows)
        
        # Alle Werte < 2.5, also keine Problem-Cluster
        assert len(stats["problem_clusters"]) == 0


class TestIntegration:
    """Integrations-Tests für komplette Workflows."""
    
    def test_full_workflow_example_data(self):
        """Test kompletter Workflow mit Beispiel-Daten."""
        # 1. Beispiel-Daten generieren
        raw_data = build_example_psychology_heatmap_data()
        
        # 2. Rows bauen
        rows = build_psychology_heatmap_rows(raw_data)
        
        # 3. Serialisieren
        serialized = serialize_psychology_heatmap_rows(rows)
        
        # 4. Statistiken berechnen
        stats = calculate_cluster_statistics(rows)
        
        # Assertions
        assert len(serialized) == len(raw_data)
        assert stats["total_clusters"] == len(raw_data)
        assert len(stats["problem_clusters"]) > 0  # Beispiel-Daten haben Problem-Cluster
    
    def test_template_context_structure(self):
        """Test dass der generierte Context die richtige Struktur für Templates hat."""
        raw_data = build_example_psychology_heatmap_data()
        rows = build_psychology_heatmap_rows(raw_data)
        serialized = serialize_psychology_heatmap_rows(rows)
        
        # Simuliere Template-Context
        context = {
            "heatmap_rows": serialized,
        }
        
        # Stelle sicher, dass Template-Zugriffe funktionieren würden
        for row in context["heatmap_rows"]:
            assert isinstance(row["name"], str)
            assert isinstance(row["fomo"]["display_value"], str)
            assert isinstance(row["fomo"]["css_class"], str)
            assert isinstance(row["fomo"]["heat_level"], int)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
