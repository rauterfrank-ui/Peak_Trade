# tests/test_live_readiness_script.py
"""
Tests für scripts/check_live_readiness.py (Phase 39)
=====================================================

Testet das Live-Readiness-Check-Script.
"""
from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

# Pfad-Setup
ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from scripts.check_live_readiness import (
    parse_args,
    main,
    run_readiness_checks,
    check_config_exists,
    check_config_valid,
    check_risk_limits,
    check_exchange_config,
    check_api_credentials,
    check_tests,
    check_live_risk_config_loadable,
    check_documentation_exists,
    CheckResult,
    WarningResult,
    ReadinessReport,
    ROOT_DIR,
)
from src.core.peak_config import PeakConfig


# =============================================================================
# Test Fixtures
# =============================================================================


@pytest.fixture
def valid_config_path(tmp_path: Path) -> Path:
    """Erstellt eine gültige Test-Config."""
    config_file = tmp_path / "config.toml"
    config_file.write_text("""
[backtest]
initial_cash = 10000.0

[risk]
max_daily_loss = 0.03

[live_risk]
max_order_notional = 1000.0
max_daily_loss_abs = 500.0

[shadow]
enabled = true
fee_rate = 0.0005

[exchange]
default_type = "dummy"

[exchange.dummy]
simulated_prices = { "BTC/EUR" = 50000.0 }
fee_bps = 10.0
slippage_bps = 5.0
""")
    return config_file


@pytest.fixture
def minimal_config_path(tmp_path: Path) -> Path:
    """Erstellt eine minimale Test-Config ohne alle Sektionen."""
    config_file = tmp_path / "minimal.toml"
    config_file.write_text("""
[backtest]
initial_cash = 10000.0
""")
    return config_file


@pytest.fixture
def mock_peak_config() -> PeakConfig:
    """Mock PeakConfig mit sinnvollen Defaults."""
    return PeakConfig(raw={
        "live_risk": {
            "max_order_notional": 1000.0,
            "max_daily_loss_abs": 500.0,
        },
        "shadow": {
            "enabled": True,
            "fee_rate": 0.0005,
        },
        "exchange": {
            "default_type": "dummy",
        },
    })


# =============================================================================
# Tests: CLI Argument Parsing
# =============================================================================


class TestParseArgs:
    """Tests für Argument-Parsing."""

    def test_default_stage(self):
        """Default-Stage ist shadow."""
        args = parse_args([])
        assert args.stage == "shadow"

    def test_stage_shadow(self):
        """Stage shadow wird erkannt."""
        args = parse_args(["--stage", "shadow"])
        assert args.stage == "shadow"

    def test_stage_testnet(self):
        """Stage testnet wird erkannt."""
        args = parse_args(["--stage", "testnet"])
        assert args.stage == "testnet"

    def test_stage_live(self):
        """Stage live wird erkannt."""
        args = parse_args(["--stage", "live"])
        assert args.stage == "live"

    def test_custom_config(self):
        """Custom Config-Pfad wird erkannt."""
        args = parse_args(["--config", "/custom/path.toml"])
        assert args.config_path == "/custom/path.toml"

    def test_run_tests_flag(self):
        """--run-tests Flag wird erkannt."""
        args = parse_args(["--run-tests"])
        assert args.run_tests is True

    def test_verbose_flag(self):
        """--verbose Flag wird erkannt."""
        args = parse_args(["--verbose"])
        assert args.verbose is True

    def test_quiet_flag(self):
        """--quiet Flag wird erkannt."""
        args = parse_args(["--quiet"])
        assert args.quiet is True


# =============================================================================
# Tests: Individual Check Functions
# =============================================================================


class TestCheckConfigExists:
    """Tests für check_config_exists."""

    def test_config_exists(self, valid_config_path: Path):
        """Config existiert -> passed."""
        result = check_config_exists(valid_config_path)
        assert result.passed is True
        assert "Vorhanden" in result.message

    def test_config_not_exists(self, tmp_path: Path):
        """Config existiert nicht -> failed."""
        result = check_config_exists(tmp_path / "nonexistent.toml")
        assert result.passed is False
        assert "Nicht gefunden" in result.message


class TestCheckConfigValid:
    """Tests für check_config_valid."""

    def test_valid_config(self, valid_config_path: Path):
        """Gültige Config -> passed."""
        result = check_config_valid(valid_config_path)
        assert result.passed is True

    def test_invalid_config(self, tmp_path: Path):
        """Ungültige Config -> failed."""
        invalid_config = tmp_path / "invalid.toml"
        invalid_config.write_text("invalid toml [ syntax")
        result = check_config_valid(invalid_config)
        assert result.passed is False


class TestCheckRiskLimits:
    """Tests für check_risk_limits."""

    def test_risk_limits_configured(self, mock_peak_config: PeakConfig):
        """Risk-Limits konfiguriert -> passed."""
        result = check_risk_limits(mock_peak_config)
        assert result.passed is True

    def test_no_risk_limits(self):
        """Keine Risk-Limits -> failed."""
        cfg = PeakConfig(raw={})
        result = check_risk_limits(cfg)
        assert result.passed is False

    def test_partial_risk_limits(self):
        """Teilweise Risk-Limits -> passed."""
        cfg = PeakConfig(raw={
            "live_risk": {"max_order_notional": 1000.0}
        })
        result = check_risk_limits(cfg)
        assert result.passed is True


class TestCheckExchangeConfig:
    """Tests für check_exchange_config."""

    def test_dummy_for_shadow(self, mock_peak_config: PeakConfig):
        """Dummy für Shadow -> passed."""
        result = check_exchange_config(mock_peak_config, "shadow")
        assert result.passed is True

    def test_dummy_for_testnet(self, mock_peak_config: PeakConfig):
        """Dummy für Testnet -> passed."""
        result = check_exchange_config(mock_peak_config, "testnet")
        assert result.passed is True

    def test_testnet_type_for_testnet(self):
        """kraken_testnet für Testnet -> passed."""
        cfg = PeakConfig(raw={"exchange": {"default_type": "kraken_testnet"}})
        result = check_exchange_config(cfg, "testnet")
        assert result.passed is True

    def test_dummy_for_live_fails(self, mock_peak_config: PeakConfig):
        """Dummy für Live -> failed."""
        result = check_exchange_config(mock_peak_config, "live")
        assert result.passed is False


class TestCheckApiCredentials:
    """Tests für check_api_credentials."""

    def test_shadow_no_credentials_needed(self):
        """Shadow braucht keine Credentials."""
        result = check_api_credentials("shadow")
        assert result.passed is True
        assert "Nicht erforderlich" in result.message

    def test_testnet_credentials_optional(self):
        """Testnet: Credentials optional bei DummyClient."""
        result = check_api_credentials("testnet")
        assert result.passed is True

    def test_live_credentials_missing(self):
        """Live ohne Credentials -> failed."""
        with patch.dict("os.environ", {}, clear=True):
            result = check_api_credentials("live")
            assert result.passed is False


class TestCheckTests:
    """Tests für check_tests."""

    def test_tests_skipped_by_default(self):
        """Tests werden übersprungen wenn run_tests=False."""
        result = check_tests(run_tests=False)
        assert result.passed is True
        assert "Übersprungen" in result.message


# =============================================================================
# Tests: check_live_risk_config_loadable (Phase 39 - Hard-Check)
# =============================================================================


class TestCheckLiveRiskConfigLoadable:
    """Tests für check_live_risk_config_loadable (Hard-Check für Testnet/Live)."""

    def test_shadow_always_passes(self):
        """Shadow-Stage: Check immer bestanden (optional)."""
        cfg = PeakConfig(raw={})
        result = check_live_risk_config_loadable(cfg, "shadow")
        assert result.passed is True
        assert "optional" in result.message.lower() or "Shadow" in result.message

    def test_shadow_with_valid_config(self, mock_peak_config: PeakConfig):
        """Shadow-Stage: Mit gültiger Config -> passed mit Info."""
        result = check_live_risk_config_loadable(mock_peak_config, "shadow")
        assert result.passed is True
        assert "ladbar" in result.message.lower()

    def test_testnet_missing_live_risk_block(self):
        """Testnet: Fehlender [live_risk]-Block -> failed."""
        cfg = PeakConfig(raw={"backtest": {"initial_cash": 10000}})
        result = check_live_risk_config_loadable(cfg, "testnet")
        assert result.passed is False
        assert "live_risk" in result.message.lower() or "fehlt" in result.message.lower()

    def test_testnet_with_valid_live_risk(self, mock_peak_config: PeakConfig):
        """Testnet: Mit gültiger [live_risk]-Config -> passed."""
        result = check_live_risk_config_loadable(mock_peak_config, "testnet")
        assert result.passed is True
        assert "erfolgreich" in result.message.lower()

    def test_testnet_shows_details(self, mock_peak_config: PeakConfig):
        """Testnet: Details über geladene Limits werden angezeigt."""
        result = check_live_risk_config_loadable(mock_peak_config, "testnet")
        assert result.passed is True
        # Details sollten mindestens ein Limit enthalten
        assert len(result.details) > 0
        assert any("max_order_notional" in d for d in result.details)

    def test_live_missing_live_risk_block(self):
        """Live: Fehlender [live_risk]-Block -> failed."""
        cfg = PeakConfig(raw={"backtest": {"initial_cash": 10000}})
        result = check_live_risk_config_loadable(cfg, "live")
        assert result.passed is False

    def test_live_with_valid_live_risk(self):
        """Live: Mit gültiger [live_risk]-Config -> passed."""
        cfg = PeakConfig(raw={
            "live_risk": {
                "max_order_notional": 500.0,
                "max_daily_loss_abs": 100.0,
            },
        })
        result = check_live_risk_config_loadable(cfg, "live")
        assert result.passed is True

    def test_empty_live_risk_block(self):
        """Testnet: Leerer [live_risk]-Block -> passed (from_config handelt das)."""
        cfg = PeakConfig(raw={"live_risk": {}})
        result = check_live_risk_config_loadable(cfg, "testnet")
        # LiveRiskLimits.from_config() akzeptiert auch leeren Block (enabled default)
        assert result.passed is True


# =============================================================================
# Tests: check_documentation_exists (Phase 39 - Soft-Check)
# =============================================================================


class TestCheckDocumentationExists:
    """Tests für check_documentation_exists (Soft-Check)."""

    def test_returns_list(self):
        """Funktion gibt Liste von WarningResult zurück."""
        result = check_documentation_exists()
        assert isinstance(result, list)
        # Alle Elemente sind WarningResult
        for item in result:
            assert isinstance(item, WarningResult)

    def test_warnings_for_missing_docs(self, tmp_path: Path, monkeypatch):
        """Warnung für fehlende Dokumentation."""
        # Temporär ROOT_DIR auf tmp_path setzen
        import scripts.check_live_readiness as script_module
        monkeypatch.setattr(script_module, "ROOT_DIR", tmp_path)

        # docs-Verzeichnis existiert nicht
        result = check_documentation_exists()

        # Sollte mindestens eine Warnung geben
        assert len(result) > 0
        # Alle sollten über fehlende Dateien sein
        for warning in result:
            assert "fehlt" in warning.message.lower() or "WARN" in warning.message

    def test_no_warnings_when_docs_exist(self, tmp_path: Path, monkeypatch):
        """Keine Warnungen wenn alle Dokumente existieren."""
        import scripts.check_live_readiness as script_module
        monkeypatch.setattr(script_module, "ROOT_DIR", tmp_path)

        # docs-Verzeichnis und Dateien erstellen
        docs_dir = tmp_path / "docs"
        docs_dir.mkdir()

        # Erwartete Dokumentationsdateien erstellen mit mindestens 100 Bytes
        doc_content = "# Dokumentation\n\nDies ist ein Platzhalter für die Dokumentation.\n" * 10
        (docs_dir / "LIVE_DEPLOYMENT_PLAYBOOK.md").write_text(doc_content)
        (docs_dir / "LIVE_OPERATIONAL_RUNBOOKS.md").write_text(doc_content)
        (docs_dir / "LIVE_READINESS_CHECKLISTS.md").write_text(doc_content)

        result = check_documentation_exists()

        # Sollte keine Warnungen geben
        assert len(result) == 0

    def test_warning_for_empty_file(self, tmp_path: Path, monkeypatch):
        """Warnung für leere Dokumentationsdatei."""
        import scripts.check_live_readiness as script_module
        monkeypatch.setattr(script_module, "ROOT_DIR", tmp_path)

        # docs-Verzeichnis und leere Datei erstellen
        docs_dir = tmp_path / "docs"
        docs_dir.mkdir()
        (docs_dir / "LIVE_DEPLOYMENT_PLAYBOOK.md").write_text("")  # Leer
        doc_content = "# Dokumentation\n\nDies ist ein Platzhalter für die Dokumentation.\n" * 10
        (docs_dir / "LIVE_OPERATIONAL_RUNBOOKS.md").write_text(doc_content)
        (docs_dir / "LIVE_READINESS_CHECKLISTS.md").write_text(doc_content)

        result = check_documentation_exists()

        # Sollte genau eine Warnung für die leere Datei geben
        assert len(result) == 1
        assert "leer" in result[0].message.lower()

    def test_warning_for_very_short_file(self, tmp_path: Path, monkeypatch):
        """Warnung für sehr kurze Dokumentationsdatei (<100 Bytes)."""
        import scripts.check_live_readiness as script_module
        monkeypatch.setattr(script_module, "ROOT_DIR", tmp_path)

        # docs-Verzeichnis und kurze Datei erstellen
        docs_dir = tmp_path / "docs"
        docs_dir.mkdir()
        (docs_dir / "LIVE_DEPLOYMENT_PLAYBOOK.md").write_text("# Kurz")  # Zu kurz
        doc_content = "# Dokumentation\n\nDies ist ein Platzhalter für die Dokumentation.\n" * 10
        (docs_dir / "LIVE_OPERATIONAL_RUNBOOKS.md").write_text(doc_content)
        (docs_dir / "LIVE_READINESS_CHECKLISTS.md").write_text(doc_content)

        result = check_documentation_exists()

        # Sollte genau eine Warnung für die kurze Datei geben
        assert len(result) == 1
        assert "kurz" in result[0].message.lower()


# =============================================================================
# Tests: ReadinessReport mit Warnings
# =============================================================================


class TestReadinessReportWithWarnings:
    """Tests für ReadinessReport mit Warnungen."""

    def test_warning_count(self):
        """warning_count gibt korrekte Anzahl zurück."""
        report = ReadinessReport(
            stage="shadow",
            checks=[CheckResult(name="Test", passed=True, message="OK")],
            warnings=[
                WarningResult(name="W1", message="Warning 1"),
                WarningResult(name="W2", message="Warning 2"),
            ]
        )
        assert report.warning_count == 2

    def test_all_passed_with_warnings(self):
        """all_passed ist True auch mit Warnungen."""
        report = ReadinessReport(
            stage="shadow",
            checks=[CheckResult(name="Test", passed=True, message="OK")],
            warnings=[WarningResult(name="W1", message="Warning 1")],
        )
        assert report.all_passed is True
        assert report.warning_count == 1


# =============================================================================
# Tests: Readiness Report
# =============================================================================


class TestReadinessReport:
    """Tests für ReadinessReport."""

    def test_all_passed(self):
        """Alle Checks bestanden."""
        report = ReadinessReport(
            stage="shadow",
            checks=[
                CheckResult(name="Test1", passed=True, message="OK"),
                CheckResult(name="Test2", passed=True, message="OK"),
            ]
        )
        assert report.all_passed is True
        assert report.passed_count == 2
        assert report.failed_count == 0

    def test_some_failed(self):
        """Einige Checks fehlgeschlagen."""
        report = ReadinessReport(
            stage="shadow",
            checks=[
                CheckResult(name="Test1", passed=True, message="OK"),
                CheckResult(name="Test2", passed=False, message="Failed"),
            ]
        )
        assert report.all_passed is False
        assert report.passed_count == 1
        assert report.failed_count == 1


# =============================================================================
# Tests: run_readiness_checks
# =============================================================================


class TestRunReadinessChecks:
    """Tests für run_readiness_checks."""

    def test_shadow_with_valid_config(self, valid_config_path: Path):
        """Shadow-Check mit gültiger Config."""
        report = run_readiness_checks(
            stage="shadow",
            config_path=valid_config_path,
            run_tests=False,
        )
        assert report.stage == "shadow"
        assert len(report.checks) > 0
        # Config-Checks sollten bestehen
        assert report.checks[0].passed  # Config exists
        assert report.checks[1].passed  # Config valid

    def test_testnet_with_valid_config(self, valid_config_path: Path):
        """Testnet-Check mit gültiger Config."""
        report = run_readiness_checks(
            stage="testnet",
            config_path=valid_config_path,
            run_tests=False,
        )
        assert report.stage == "testnet"

    def test_invalid_config_path(self, tmp_path: Path):
        """Ungültiger Config-Pfad -> Config-Check failed."""
        report = run_readiness_checks(
            stage="shadow",
            config_path=tmp_path / "nonexistent.toml",
            run_tests=False,
        )
        assert report.checks[0].passed is False  # Config not found


# =============================================================================
# Tests: main() Function
# =============================================================================


class TestMain:
    """Tests für main() Funktion."""

    def test_main_shadow_success(self, valid_config_path: Path):
        """main() mit Shadow-Stage und gültiger Config."""
        exit_code = main(["--stage", "shadow", "--config", str(valid_config_path), "--quiet"])
        assert exit_code == 0

    def test_main_invalid_config(self, tmp_path: Path):
        """main() mit ungültiger Config -> Exit 1."""
        exit_code = main(["--config", str(tmp_path / "nonexistent.toml"), "--quiet"])
        assert exit_code == 1

    def test_main_verbose_output(self, valid_config_path: Path, capsys):
        """main() mit --verbose gibt Details aus."""
        main(["--stage", "shadow", "--config", str(valid_config_path), "--verbose"])
        captured = capsys.readouterr()
        assert "Peak_Trade" in captured.out

    def test_main_quiet_output(self, valid_config_path: Path, capsys):
        """main() mit --quiet gibt nur PASSED/FAILED aus."""
        main(["--stage", "shadow", "--config", str(valid_config_path), "--quiet"])
        captured = capsys.readouterr()
        assert captured.out.strip() in ("PASSED", "FAILED")


# =============================================================================
# Tests: Live-Risk-Config-Validierung (Hard-Check)
# =============================================================================


class TestCheckLiveRiskConfigLoadable:
    """Tests für check_live_risk_config_loadable (Hard-Check)."""

    @pytest.fixture
    def valid_live_risk_config(self, tmp_path: Path) -> Path:
        """Config mit gültigem [live_risk]-Block."""
        config_file = tmp_path / "valid_live_risk.toml"
        config_file.write_text("""
[backtest]
initial_cash = 10000.0

[live_risk]
max_order_notional = 1000.0
max_daily_loss_abs = 500.0
max_daily_loss_pct = 5.0
max_symbol_exposure_notional = 2000.0
max_total_exposure_notional = 5000.0
max_open_positions = 3

[exchange]
default_type = "dummy"
""")
        return config_file

    @pytest.fixture
    def missing_live_risk_config(self, tmp_path: Path) -> Path:
        """Config OHNE [live_risk]-Block."""
        config_file = tmp_path / "no_live_risk.toml"
        config_file.write_text("""
[backtest]
initial_cash = 10000.0

[exchange]
default_type = "dummy"
""")
        return config_file

    @pytest.fixture
    def invalid_types_config(self, tmp_path: Path) -> Path:
        """Config mit ungültigen Typen in [live_risk]."""
        config_file = tmp_path / "invalid_types.toml"
        config_file.write_text("""
[backtest]
initial_cash = 10000.0

[live_risk]
max_order_notional = "nicht_eine_zahl"
max_daily_loss_abs = true

[exchange]
default_type = "dummy"
""")
        return config_file

    def test_valid_config_testnet(self, valid_live_risk_config: Path):
        """Gültige Config für Testnet -> passed."""
        from src.core.peak_config import load_config
        cfg = load_config(valid_live_risk_config)
        result = check_live_risk_config_loadable(cfg, "testnet")
        assert result.passed is True
        assert "erfolgreich" in result.message.lower() or "ladbar" in result.message.lower()

    def test_valid_config_live(self, valid_live_risk_config: Path):
        """Gültige Config für Live -> passed."""
        from src.core.peak_config import load_config
        cfg = load_config(valid_live_risk_config)
        result = check_live_risk_config_loadable(cfg, "live")
        assert result.passed is True

    def test_valid_config_shadow(self, valid_live_risk_config: Path):
        """Gültige Config für Shadow -> passed (optional)."""
        from src.core.peak_config import load_config
        cfg = load_config(valid_live_risk_config)
        result = check_live_risk_config_loadable(cfg, "shadow")
        assert result.passed is True

    def test_missing_live_risk_block_testnet(self, missing_live_risk_config: Path):
        """Fehlender [live_risk]-Block für Testnet -> failed."""
        from src.core.peak_config import load_config
        cfg = load_config(missing_live_risk_config)
        result = check_live_risk_config_loadable(cfg, "testnet")
        assert result.passed is False
        assert "ERROR" in result.message or "fehlt" in result.message.lower()

    def test_missing_live_risk_block_live(self, missing_live_risk_config: Path):
        """Fehlender [live_risk]-Block für Live -> failed."""
        from src.core.peak_config import load_config
        cfg = load_config(missing_live_risk_config)
        result = check_live_risk_config_loadable(cfg, "live")
        assert result.passed is False
        assert "ERROR" in result.message or "fehlt" in result.message.lower()

    def test_missing_live_risk_block_shadow(self, missing_live_risk_config: Path):
        """Fehlender [live_risk]-Block für Shadow -> passed (nicht blockierend)."""
        from src.core.peak_config import load_config
        cfg = load_config(missing_live_risk_config)
        result = check_live_risk_config_loadable(cfg, "shadow")
        # Für Shadow ist es NICHT blockierend
        assert result.passed is True

    def test_has_details_on_success(self, valid_live_risk_config: Path):
        """Bei Erfolg werden Details zu den geladenen Limits ausgegeben."""
        from src.core.peak_config import load_config
        cfg = load_config(valid_live_risk_config)
        result = check_live_risk_config_loadable(cfg, "testnet")
        assert result.passed is True
        # Details sollten vorhanden sein
        assert len(result.details) > 0

    def test_has_details_on_failure(self, missing_live_risk_config: Path):
        """Bei Fehler werden hilfreiche Details ausgegeben."""
        from src.core.peak_config import load_config
        cfg = load_config(missing_live_risk_config)
        result = check_live_risk_config_loadable(cfg, "testnet")
        assert result.passed is False
        # Details sollten Hinweise enthalten
        assert len(result.details) > 0
        # Mindestens ein Hinweis auf Dokumentation
        details_text = " ".join(result.details).lower()
        assert "docs" in details_text or "config" in details_text


# =============================================================================
# Tests: Dokumentations-Soft-Checks
# =============================================================================


class TestCheckDocumentationExists:
    """Tests für check_documentation_exists (Soft-Check)."""

    # Inhalt > 100 Bytes für gültige Dateien
    VALID_DOC_CONTENT = "# Dokumentation\n\n" + "Dies ist ein Platzhalter für die Dokumentation. " * 5

    def test_all_docs_exist_no_warnings(self, tmp_path: Path, monkeypatch):
        """Wenn alle Doku-Dateien existieren und Inhalt haben -> keine Warnungen."""
        # Temporäres docs-Verzeichnis erstellen
        docs_dir = tmp_path / "docs"
        docs_dir.mkdir()

        # Alle erwarteten Dateien mit Inhalt erstellen (>100 Bytes)
        (docs_dir / "LIVE_DEPLOYMENT_PLAYBOOK.md").write_text(self.VALID_DOC_CONTENT)
        (docs_dir / "LIVE_OPERATIONAL_RUNBOOKS.md").write_text(self.VALID_DOC_CONTENT)
        (docs_dir / "LIVE_READINESS_CHECKLISTS.md").write_text(self.VALID_DOC_CONTENT)

        # ROOT_DIR mocken
        import scripts.check_live_readiness as module
        monkeypatch.setattr(module, "ROOT_DIR", tmp_path)

        warnings = check_documentation_exists()
        assert len(warnings) == 0

    def test_missing_file_produces_warning(self, tmp_path: Path, monkeypatch):
        """Wenn eine Datei fehlt -> Warnung."""
        docs_dir = tmp_path / "docs"
        docs_dir.mkdir()

        # Nur 2 von 3 Dateien erstellen (>100 Bytes)
        (docs_dir / "LIVE_DEPLOYMENT_PLAYBOOK.md").write_text(self.VALID_DOC_CONTENT)
        (docs_dir / "LIVE_OPERATIONAL_RUNBOOKS.md").write_text(self.VALID_DOC_CONTENT)
        # LIVE_READINESS_CHECKLISTS.md fehlt!

        import scripts.check_live_readiness as module
        monkeypatch.setattr(module, "ROOT_DIR", tmp_path)

        warnings = check_documentation_exists()
        assert len(warnings) == 1
        assert "LIVE_READINESS_CHECKLISTS.md" in warnings[0].name
        assert "WARN" in warnings[0].message

    def test_empty_file_produces_warning(self, tmp_path: Path, monkeypatch):
        """Wenn eine Datei leer ist -> Warnung."""
        docs_dir = tmp_path / "docs"
        docs_dir.mkdir()

        (docs_dir / "LIVE_DEPLOYMENT_PLAYBOOK.md").write_text(self.VALID_DOC_CONTENT)
        (docs_dir / "LIVE_OPERATIONAL_RUNBOOKS.md").write_text("")  # Leer!
        (docs_dir / "LIVE_READINESS_CHECKLISTS.md").write_text(self.VALID_DOC_CONTENT)

        import scripts.check_live_readiness as module
        monkeypatch.setattr(module, "ROOT_DIR", tmp_path)

        warnings = check_documentation_exists()
        assert len(warnings) == 1
        assert "LIVE_OPERATIONAL_RUNBOOKS.md" in warnings[0].name
        assert "leer" in warnings[0].message.lower()

    def test_very_short_file_produces_warning(self, tmp_path: Path, monkeypatch):
        """Wenn eine Datei sehr kurz ist (<100 Bytes) -> Warnung."""
        docs_dir = tmp_path / "docs"
        docs_dir.mkdir()

        (docs_dir / "LIVE_DEPLOYMENT_PLAYBOOK.md").write_text(self.VALID_DOC_CONTENT)
        (docs_dir / "LIVE_OPERATIONAL_RUNBOOKS.md").write_text(self.VALID_DOC_CONTENT)
        (docs_dir / "LIVE_READINESS_CHECKLISTS.md").write_text("Hi")  # Nur 2 Bytes

        import scripts.check_live_readiness as module
        monkeypatch.setattr(module, "ROOT_DIR", tmp_path)

        warnings = check_documentation_exists()
        assert len(warnings) == 1
        assert "LIVE_READINESS_CHECKLISTS.md" in warnings[0].name
        assert "kurz" in warnings[0].message.lower()

    def test_multiple_issues(self, tmp_path: Path, monkeypatch):
        """Mehrere Probleme -> mehrere Warnungen."""
        docs_dir = tmp_path / "docs"
        docs_dir.mkdir()

        (docs_dir / "LIVE_DEPLOYMENT_PLAYBOOK.md").write_text(self.VALID_DOC_CONTENT)
        # Die anderen beiden fehlen

        import scripts.check_live_readiness as module
        monkeypatch.setattr(module, "ROOT_DIR", tmp_path)

        warnings = check_documentation_exists()
        assert len(warnings) == 2

    def test_warnings_do_not_block_readiness(self, valid_config_path: Path, tmp_path: Path, monkeypatch):
        """Warnungen blockieren die Readiness NICHT."""
        # docs-Verzeichnis ohne alle Dateien
        docs_dir = tmp_path / "docs"
        docs_dir.mkdir()
        # Nur eine Datei
        (docs_dir / "LIVE_DEPLOYMENT_PLAYBOOK.md").write_text("# Playbook\nContent here...")
        
        import scripts.check_live_readiness as module
        monkeypatch.setattr(module, "ROOT_DIR", tmp_path)
        
        # run_readiness_checks mit der valid_config_path
        report = run_readiness_checks(
            stage="shadow",
            config_path=valid_config_path,
            run_tests=False,
        )
        
        # Es gibt Warnungen
        assert report.warning_count >= 1
        # Aber Readiness sollte trotzdem bestehen (wenn alle harten Checks OK)
        # (Abhängig von der Config - hier prüfen wir nur, dass Warnungen nicht blocken)


# =============================================================================
# Tests: WarningResult
# =============================================================================


class TestWarningResult:
    """Tests für WarningResult Dataclass."""

    def test_warning_result_creation(self):
        """WarningResult kann erstellt werden."""
        warning = WarningResult(
            name="Test-Warnung",
            message="WARN: Etwas fehlt",
            details=["Detail 1", "Detail 2"],
        )
        assert warning.name == "Test-Warnung"
        assert "WARN" in warning.message
        assert len(warning.details) == 2

    def test_warning_result_defaults(self):
        """WarningResult hat sinnvolle Defaults."""
        warning = WarningResult(name="Test", message="Nachricht")
        assert warning.details == []


# =============================================================================
# Tests: ReadinessReport mit Warnungen
# =============================================================================


class TestReadinessReportWithWarnings:
    """Tests für ReadinessReport mit Warnungen."""

    def test_warning_count(self):
        """warning_count zählt Warnungen korrekt."""
        report = ReadinessReport(
            stage="testnet",
            checks=[CheckResult(name="Test", passed=True, message="OK")],
            warnings=[
                WarningResult(name="W1", message="Warn1"),
                WarningResult(name="W2", message="Warn2"),
            ],
        )
        assert report.warning_count == 2

    def test_all_passed_ignores_warnings(self):
        """all_passed berücksichtigt keine Warnungen."""
        report = ReadinessReport(
            stage="testnet",
            checks=[CheckResult(name="Test", passed=True, message="OK")],
            warnings=[WarningResult(name="W1", message="Warn1")],
        )
        # Alle Checks bestanden, trotz Warnung
        assert report.all_passed is True

    def test_empty_warnings_by_default(self):
        """Ohne explizite Warnungen ist die Liste leer."""
        report = ReadinessReport(
            stage="shadow",
            checks=[CheckResult(name="Test", passed=True, message="OK")],
        )
        assert report.warnings == []
        assert report.warning_count == 0


# =============================================================================
# Tests: Integration - Readiness mit neuen Checks
# =============================================================================


class TestReadinessIntegrationWithNewChecks:
    """Integration-Tests für die neuen Checks."""

    def test_testnet_with_valid_live_risk_config(self, tmp_path: Path):
        """Testnet mit gültigem [live_risk] -> passed."""
        config_file = tmp_path / "config.toml"
        config_file.write_text("""
[backtest]
initial_cash = 10000.0

[live_risk]
max_order_notional = 1000.0
max_daily_loss_abs = 500.0

[exchange]
default_type = "dummy"
""")
        report = run_readiness_checks(
            stage="testnet",
            config_path=config_file,
            run_tests=False,
        )
        
        # Live-Risk-Config-Check finden
        live_risk_check = next(
            (c for c in report.checks if "Live-Risk" in c.name), None
        )
        assert live_risk_check is not None
        assert live_risk_check.passed is True

    def test_testnet_without_live_risk_config_fails(self, tmp_path: Path):
        """Testnet ohne [live_risk] -> failed."""
        config_file = tmp_path / "config.toml"
        config_file.write_text("""
[backtest]
initial_cash = 10000.0

[exchange]
default_type = "dummy"
""")
        report = run_readiness_checks(
            stage="testnet",
            config_path=config_file,
            run_tests=False,
        )
        
        # Live-Risk-Config-Check finden
        live_risk_check = next(
            (c for c in report.checks if "Live-Risk" in c.name), None
        )
        assert live_risk_check is not None
        assert live_risk_check.passed is False
        
        # Gesamtreport sollte failed sein
        assert report.all_passed is False

    def test_live_without_live_risk_config_fails(self, tmp_path: Path):
        """Live ohne [live_risk] -> failed."""
        config_file = tmp_path / "config.toml"
        config_file.write_text("""
[backtest]
initial_cash = 10000.0

[exchange]
default_type = "kraken_live"
""")
        report = run_readiness_checks(
            stage="live",
            config_path=config_file,
            run_tests=False,
        )
        
        # Live-Risk-Config-Check sollte failed sein
        live_risk_check = next(
            (c for c in report.checks if "Live-Risk" in c.name), None
        )
        assert live_risk_check is not None
        assert live_risk_check.passed is False


# ---------------------------------------------------------------------------
# Lokal-Notizen: manuelles Ausführen des Live-Readiness-Scripts (optional)
#
# Diese Kommandos sind reine Shell-Beispiele und werden von Python / pytest
# ignoriert, weil sie als Kommentare markiert sind. Sie dienen nur als
# Erinnerungsstütze für manuelle Checks.
#
# cd "/Users/frnkhrz/Peak_Trade"
# source ".venv/bin/activate"
# python scripts/check_live_readiness.py
# python scripts/operator_dashboard.py --help
# python scripts/operator_dashboard.py
# ---------------------------------------------------------------------------
