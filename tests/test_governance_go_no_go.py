"""
Unit-Tests für das Go/No-Go Governance Module.

Testet die Funktionen get_governance_status() und is_feature_approved_for_year()
gemäß der Spezifikation in docs/GO_NO_GO_2026_LIVE_ALERTS_CLUSTER_82_85.md.
"""

import pytest

from src.governance.go_no_go import (
    GovernanceStatus,
    get_governance_status,
    is_feature_approved_for_year,
)


class TestGetGovernanceStatus:
    """Tests für get_governance_status()."""

    def test_live_alerts_cluster_returns_approved_2026(self) -> None:
        """Live Alerts Cluster 82-85 ist für 2026 freigegeben."""
        result = get_governance_status("live_alerts_cluster_82_85")
        assert result == "approved_2026"

    def test_live_order_execution_returns_locked(self) -> None:
        """Live-Order-Execution ist gesperrt."""
        result = get_governance_status("live_order_execution")
        assert result == "locked"

    def test_unknown_feature_returns_unknown(self) -> None:
        """Unbekannte Features liefern 'unknown'."""
        result = get_governance_status("unknown_feature")
        assert result == "unknown"

    def test_empty_string_returns_unknown(self) -> None:
        """Leerer String liefert 'unknown'."""
        result = get_governance_status("")
        assert result == "unknown"

    def test_arbitrary_feature_returns_unknown(self) -> None:
        """Beliebige nicht-registrierte Features liefern 'unknown'."""
        result = get_governance_status("some_arbitrary_feature_xyz")
        assert result == "unknown"


class TestIsFeatureApprovedForYear:
    """Tests für is_feature_approved_for_year()."""

    def test_live_alerts_approved_for_2026(self) -> None:
        """Live Alerts Cluster ist für 2026 freigegeben."""
        result = is_feature_approved_for_year("live_alerts_cluster_82_85", 2026)
        assert result is True

    def test_live_alerts_not_approved_for_2025(self) -> None:
        """Live Alerts Cluster ist NICHT für 2025 freigegeben."""
        result = is_feature_approved_for_year("live_alerts_cluster_82_85", 2025)
        assert result is False

    def test_live_alerts_not_approved_for_2027(self) -> None:
        """Live Alerts Cluster ist NICHT für 2027 freigegeben."""
        result = is_feature_approved_for_year("live_alerts_cluster_82_85", 2027)
        assert result is False

    def test_live_order_execution_never_approved(self) -> None:
        """Live-Order-Execution ist für kein Jahr freigegeben (locked)."""
        # Teste mehrere Jahre
        for year in [2024, 2025, 2026, 2027, 2028, 2030]:
            result = is_feature_approved_for_year("live_order_execution", year)
            assert result is False, f"Sollte für Jahr {year} False sein"

    def test_unknown_feature_never_approved(self) -> None:
        """Unbekannte Features sind nie freigegeben."""
        result = is_feature_approved_for_year("unknown_feature", 2026)
        assert result is False

    def test_unknown_feature_not_approved_for_any_year(self) -> None:
        """Unbekannte Features sind für kein Jahr freigegeben."""
        for year in [2024, 2025, 2026, 2027, 2028]:
            result = is_feature_approved_for_year("some_random_feature", year)
            assert result is False, f"Sollte für Jahr {year} False sein"


class TestGovernanceStatusType:
    """Tests für GovernanceStatus Literal Type."""

    def test_valid_status_values(self) -> None:
        """Prüft, dass alle erwarteten Status-Werte zurückgegeben werden können."""
        # approved_2026
        assert get_governance_status("live_alerts_cluster_82_85") == "approved_2026"
        # locked
        assert get_governance_status("live_order_execution") == "locked"
        # unknown
        assert get_governance_status("nonexistent") == "unknown"


class TestEdgeCases:
    """Edge-Case Tests."""

    def test_year_zero(self) -> None:
        """Jahr 0 sollte False liefern."""
        result = is_feature_approved_for_year("live_alerts_cluster_82_85", 0)
        assert result is False

    def test_negative_year(self) -> None:
        """Negative Jahre sollten False liefern."""
        result = is_feature_approved_for_year("live_alerts_cluster_82_85", -2026)
        assert result is False

    def test_very_large_year(self) -> None:
        """Sehr große Jahre sollten False liefern."""
        result = is_feature_approved_for_year("live_alerts_cluster_82_85", 9999)
        assert result is False

    def test_case_sensitive_feature_key(self) -> None:
        """Feature-Keys sind case-sensitive."""
        # Großbuchstaben sollten nicht matchen
        result = get_governance_status("LIVE_ALERTS_CLUSTER_82_85")
        assert result == "unknown"

        result = get_governance_status("Live_Alerts_Cluster_82_85")
        assert result == "unknown"
