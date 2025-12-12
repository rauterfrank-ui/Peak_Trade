"""
Tests für scripts/check_bounded_auto_readiness.py

Diese Tests validieren, dass das Readiness-Check-Tool korrekt funktioniert
und die verschiedenen Go/No-Go-Kriterien prüft.
"""

from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# Add scripts to path for imports
SCRIPTS_DIR = Path(__file__).parent.parent.parent / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

from check_bounded_auto_readiness import CheckResult, ReadinessChecker


@pytest.fixture
def valid_config_data():
    """Fixture mit vollständiger, valider Config."""
    return {
        "promotion_loop": {
            "mode": "manual_only",
            "bounds": {
                "leverage_min": 1.0,
                "leverage_max": 2.0,
                "leverage_max_step": 0.25,
                "trigger_delay_min": 3.0,
                "trigger_delay_max": 15.0,
                "trigger_delay_max_step": 2.0,
                "macro_weight_min": 0.0,
                "macro_weight_max": 0.8,
                "macro_weight_max_step": 0.1,
            },
            "safety": {
                "auto_apply_blacklist": ["risk.stop_loss", "live.api_keys"],
                "blacklist_tags": ["r_and_d", "experimental"],
                "min_confidence_for_auto_apply": 0.80,
                "auto_apply_whitelist": ["portfolio.leverage"],
            },
            "governance": {
                "global_promotion_lock": False,
                "audit_log_path": "reports/promotion_audit/promotion_audit.jsonl",
            },
        }
    }


@pytest.fixture
def minimal_config_data():
    """Fixture mit minimaler Config (fehlende Bounds, Blacklist)."""
    return {
        "promotion_loop": {
            "mode": "manual_only",
            "safety": {},
            "governance": {
                "global_promotion_lock": False,
            },
        }
    }


class TestCheckResult:
    """Tests für CheckResult Dataclass."""

    def test_check_result_creation(self):
        """Test CheckResult kann erstellt werden."""
        result = CheckResult(
            name="Test Check",
            status="OK",
            message="Test message",
        )
        assert result.name == "Test Check"
        assert result.status == "OK"
        assert result.message == "Test message"
        assert result.details is None

    def test_check_result_with_details(self):
        """Test CheckResult mit Details."""
        result = CheckResult(
            name="Test Check",
            status="OK",
            message="Test message",
            details=["Detail 1", "Detail 2"],
        )
        assert result.details == ["Detail 1", "Detail 2"]


class TestReadinessChecker:
    """Tests für ReadinessChecker."""

    def test_checker_initialization(self):
        """Test ReadinessChecker kann initialisiert werden."""
        checker = ReadinessChecker(verbose=False)
        assert checker.verbose is False
        assert checker.results == []
        assert checker.config_path.name == "promotion_loop_config.toml"

    def test_checker_verbose_mode(self):
        """Test verbose Modus wird korrekt gesetzt."""
        checker = ReadinessChecker(verbose=True)
        assert checker.verbose is True

    @patch("toml.load")
    @patch("pathlib.Path.exists")
    def test_check_config_loadable_success(
        self, mock_exists, mock_toml_load, valid_config_data
    ):
        """Test Config-Laden erfolgreich."""
        mock_exists.return_value = True
        mock_toml_load.return_value = valid_config_data

        checker = ReadinessChecker()
        checker._check_config_loadable()

        assert len(checker.results) == 1
        assert checker.results[0].status == "OK"
        assert "erfolgreich geladen" in checker.results[0].message

    @patch("pathlib.Path.exists")
    def test_check_config_loadable_file_not_found(self, mock_exists):
        """Test Config-Datei nicht gefunden."""
        mock_exists.return_value = False

        checker = ReadinessChecker()
        checker._check_config_loadable()

        assert len(checker.results) == 1
        assert checker.results[0].status == "ERR"
        assert "nicht gefunden" in checker.results[0].message

    def test_check_p0_blacklist_config_success(self, valid_config_data):
        """Test Blacklist-Config erfolgreich."""
        checker = ReadinessChecker()
        checker.config_data = valid_config_data
        checker._check_p0_blacklist_config()

        assert len(checker.results) == 1
        assert checker.results[0].status == "OK"
        assert "Blacklist-Konfiguration vorhanden" in checker.results[0].message

    def test_check_p0_blacklist_config_missing(self, minimal_config_data):
        """Test Blacklist-Config fehlt."""
        checker = ReadinessChecker()
        checker.config_data = minimal_config_data
        checker._check_p0_blacklist_config()

        assert len(checker.results) == 1
        assert checker.results[0].status == "WARN"
        assert "Keine Blacklist konfiguriert" in checker.results[0].message

    def test_check_p0_bounds_config_success(self, valid_config_data):
        """Test Bounds-Config erfolgreich."""
        checker = ReadinessChecker()
        checker.config_data = valid_config_data
        checker._check_p0_bounds_config()

        assert len(checker.results) == 1
        assert checker.results[0].status == "OK"
        assert "Alle Bounds konfiguriert" in checker.results[0].message

    def test_check_p0_bounds_config_missing(self, minimal_config_data):
        """Test Bounds-Config fehlt."""
        checker = ReadinessChecker()
        checker.config_data = minimal_config_data
        checker._check_p0_bounds_config()

        assert len(checker.results) == 1
        assert checker.results[0].status == "ERR"
        assert "Keine Bounds konfiguriert" in checker.results[0].message

    def test_check_p0_bounds_config_partial(self):
        """Test Bounds-Config nur teilweise vorhanden."""
        partial_config = {
            "promotion_loop": {
                "bounds": {
                    "leverage_min": 1.0,
                    "leverage_max": 2.0,
                    "leverage_max_step": 0.25,
                    # trigger und macro fehlen
                }
            }
        }

        checker = ReadinessChecker()
        checker.config_data = partial_config
        checker._check_p0_bounds_config()

        assert len(checker.results) == 1
        assert checker.results[0].status == "WARN"
        assert "teilweise konfiguriert" in checker.results[0].message

    def test_check_p0_guardrails_config_success(self, valid_config_data):
        """Test Guardrails-Config erfolgreich."""
        checker = ReadinessChecker()
        checker.config_data = valid_config_data
        checker._check_p0_guardrails_config()

        assert len(checker.results) == 1
        assert checker.results[0].status == "OK"
        assert "Guardrails im Code konfiguriert" in checker.results[0].message

    def test_check_p0_guardrails_config_no_mode(self):
        """Test Guardrails-Config ohne Modus."""
        no_mode_config = {"promotion_loop": {"safety": {}}}

        checker = ReadinessChecker()
        checker.config_data = no_mode_config
        checker._check_p0_guardrails_config()

        assert len(checker.results) == 1
        assert checker.results[0].status == "ERR"
        assert "Modus nicht konfiguriert" in checker.results[0].message

    def test_check_p1_promotion_lock_config_success(self, valid_config_data):
        """Test Promotion-Lock-Config erfolgreich."""
        checker = ReadinessChecker()
        checker.config_data = valid_config_data
        checker._check_p1_promotion_lock_config()

        assert len(checker.results) == 1
        assert checker.results[0].status == "OK"
        assert "Promotion-Lock konfiguriert" in checker.results[0].message

    def test_check_p1_promotion_lock_config_missing(self):
        """Test Promotion-Lock-Config fehlt."""
        no_lock_config = {"promotion_loop": {"governance": {}}}

        checker = ReadinessChecker()
        checker.config_data = no_lock_config
        checker._check_p1_promotion_lock_config()

        assert len(checker.results) == 1
        assert checker.results[0].status == "ERR"
        assert "nicht konfiguriert" in checker.results[0].message

    def test_check_p1_audit_log_config_success(self, valid_config_data):
        """Test Audit-Log-Config erfolgreich."""
        checker = ReadinessChecker()
        checker.config_data = valid_config_data
        checker._check_p1_audit_log_config()

        assert len(checker.results) == 1
        assert checker.results[0].status == "OK"
        assert "Audit-Log-Konfiguration vorhanden" in checker.results[0].message

    def test_check_p1_audit_log_config_missing(self):
        """Test Audit-Log-Config fehlt."""
        no_audit_config = {"promotion_loop": {"governance": {}}}

        checker = ReadinessChecker()
        checker.config_data = no_audit_config
        checker._check_p1_audit_log_config()

        assert len(checker.results) == 1
        assert checker.results[0].status == "WARN"
        assert "nicht konfiguriert" in checker.results[0].message

    @patch("toml.load")
    @patch("pathlib.Path.exists")
    def test_run_all_checks_success(
        self, mock_exists, mock_toml_load, valid_config_data, capsys
    ):
        """Test run_all_checks mit vollständiger Config (sollte READY sein)."""
        mock_exists.return_value = True
        mock_toml_load.return_value = valid_config_data

        checker = ReadinessChecker()
        is_ready = checker.run_all_checks()

        assert is_ready is True
        assert len(checker.results) == 6  # Alle 6 Checks durchgeführt
        assert all(r.status in ["OK", "WARN"] for r in checker.results)
        assert not any(r.status == "ERR" for r in checker.results)

        # Check output
        captured = capsys.readouterr()
        assert "READY (GO)" in captured.out

    @patch("toml.load")
    @patch("pathlib.Path.exists")
    def test_run_all_checks_failure(
        self, mock_exists, mock_toml_load, minimal_config_data, capsys
    ):
        """Test run_all_checks mit fehlerhafter Config (sollte NOT READY sein)."""
        mock_exists.return_value = True
        mock_toml_load.return_value = minimal_config_data

        checker = ReadinessChecker()
        is_ready = checker.run_all_checks()

        assert is_ready is False
        assert any(r.status == "ERR" for r in checker.results)

        # Check output
        captured = capsys.readouterr()
        assert "NOT READY (NO-GO)" in captured.out


class TestIntegration:
    """Integrationstests mit echter Config."""

    def test_integration_with_real_config(self):
        """Integration-Test mit echter promotion_loop_config.toml (falls vorhanden)."""
        checker = ReadinessChecker()
        
        # Prüfe ob Config existiert
        if not checker.config_path.exists():
            pytest.skip("promotion_loop_config.toml nicht gefunden")
        
        # Run checks ohne Print-Ausgabe (captured by pytest)
        is_ready = checker.run_all_checks()
        
        # Sollte mindestens Config laden können
        assert len(checker.results) >= 1
        
        # Erste Check sollte Config-Laden sein
        assert checker.results[0].name == "Config-Datei laden"
        
        # Bei echter Config sollten wir mindestens 6 Checks haben
        assert len(checker.results) == 6


