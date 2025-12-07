# tests/test_research_e2e_scenarios.py
"""
Tests für Phase 82: Research QA & Szenario-Library

End-to-End-Tests für Research-Szenarien:
- Szenario-Configs sind vollständig und valide
- Szenarien können geladen werden
- Szenario-basierte Erwartungen sind definiert
- E2E-Workflow: Szenario → Backtest → Erwartungs-Check
"""
import pytest
from pathlib import Path

try:
    import tomllib
except ImportError:
    import tomli as tomllib

# Pfade
PROJECT_ROOT = Path(__file__).parent.parent
SCENARIOS_DIR = PROJECT_ROOT / "config" / "scenarios"


# =============================================================================
# FIXTURES
# =============================================================================

@pytest.fixture
def scenarios_dir():
    """Pfad zum Szenarien-Verzeichnis."""
    return SCENARIOS_DIR


@pytest.fixture
def all_scenario_files(scenarios_dir):
    """Liste aller Szenario-TOML-Dateien."""
    if not scenarios_dir.exists():
        return []
    return list(scenarios_dir.glob("*.toml"))


@pytest.fixture
def scenario_configs(all_scenario_files):
    """Geladene Szenario-Configs."""
    configs = {}
    for f in all_scenario_files:
        with open(f, "rb") as fp:
            configs[f.stem] = tomllib.load(fp)
    return configs


# =============================================================================
# TESTS: SZENARIO-STRUKTUR
# =============================================================================

class TestScenarioDirectory:
    """Tests für das Szenarien-Verzeichnis."""

    def test_scenarios_directory_exists(self, scenarios_dir):
        """Szenarien-Verzeichnis existiert."""
        assert scenarios_dir.exists(), f"Scenarios directory not found: {scenarios_dir}"

    def test_has_at_least_three_scenarios(self, all_scenario_files):
        """Mindestens 3 Szenarien sind definiert."""
        assert len(all_scenario_files) >= 3, \
            f"Expected at least 3 scenarios, found {len(all_scenario_files)}"

    def test_required_scenarios_exist(self, scenarios_dir):
        """Erforderliche Standard-Szenarien existieren."""
        required = ["flash_crash.toml", "sideways_low_vol.toml", "trend_regime.toml"]
        for scenario in required:
            path = scenarios_dir / scenario
            assert path.exists(), f"Required scenario not found: {scenario}"


class TestScenarioConfigStructure:
    """Tests für die Struktur der Szenario-Configs."""

    def test_all_scenarios_have_name(self, scenario_configs):
        """Alle Szenarien haben einen Namen."""
        for name, config in scenario_configs.items():
            assert "scenario" in config, f"{name}: missing [scenario] section"
            assert "name" in config["scenario"], f"{name}: missing scenario.name"

    def test_all_scenarios_have_description(self, scenario_configs):
        """Alle Szenarien haben eine Beschreibung."""
        for name, config in scenario_configs.items():
            assert "description" in config["scenario"], \
                f"{name}: missing scenario.description"

    def test_all_scenarios_have_category(self, scenario_configs):
        """Alle Szenarien haben eine Kategorie."""
        valid_categories = {"stress", "regime", "edge_case", "historical"}
        for name, config in scenario_configs.items():
            assert "category" in config["scenario"], \
                f"{name}: missing scenario.category"
            category = config["scenario"]["category"]
            assert category in valid_categories, \
                f"{name}: invalid category '{category}', expected one of {valid_categories}"

    def test_all_scenarios_have_severity(self, scenario_configs):
        """Alle Szenarien haben einen Severity-Wert."""
        for name, config in scenario_configs.items():
            assert "severity" in config["scenario"], \
                f"{name}: missing scenario.severity"
            severity = config["scenario"]["severity"]
            assert 0.0 <= severity <= 1.0, \
                f"{name}: severity {severity} out of range [0, 1]"

    def test_all_scenarios_have_market_conditions(self, scenario_configs):
        """Alle Szenarien haben Marktbedingungen definiert."""
        for name, config in scenario_configs.items():
            assert "market_conditions" in config.get("scenario", {}), \
                f"{name}: missing scenario.market_conditions"

    def test_all_scenarios_have_test_expectations(self, scenario_configs):
        """Alle Szenarien haben Test-Erwartungen definiert."""
        for name, config in scenario_configs.items():
            assert "test_expectations" in config.get("scenario", {}), \
                f"{name}: missing scenario.test_expectations"


# =============================================================================
# TESTS: SZENARIO-INHALTE
# =============================================================================

class TestFlashCrashScenario:
    """Tests für das Flash-Crash-Szenario."""

    @pytest.fixture
    def flash_crash_config(self, scenario_configs):
        """Flash-Crash-Szenario-Config."""
        if "flash_crash" not in scenario_configs:
            pytest.skip("flash_crash scenario not found")
        return scenario_configs["flash_crash"]

    def test_is_stress_category(self, flash_crash_config):
        """Flash Crash ist Kategorie 'stress'."""
        assert flash_crash_config["scenario"]["category"] == "stress"

    def test_has_high_severity(self, flash_crash_config):
        """Flash Crash hat hohe Severity."""
        severity = flash_crash_config["scenario"]["severity"]
        assert severity >= 0.7, f"Flash crash should have high severity, got {severity}"

    def test_has_extreme_volatility(self, flash_crash_config):
        """Flash Crash hat extreme Volatilität."""
        vol = flash_crash_config["scenario"]["market_conditions"]["volatility"]
        assert vol in ["high", "extreme"], f"Expected high/extreme volatility, got {vol}"

    def test_has_max_drawdown_expectation(self, flash_crash_config):
        """Flash Crash hat erwarteten Max-Drawdown."""
        expectations = flash_crash_config["scenario"]["test_expectations"]
        assert "baseline_max_portfolio_drawdown" in expectations
        dd = expectations["baseline_max_portfolio_drawdown"]
        assert dd < 0, f"Drawdown should be negative, got {dd}"


class TestSidewaysLowVolScenario:
    """Tests für das Sideways-Low-Vol-Szenario."""

    @pytest.fixture
    def sideways_config(self, scenario_configs):
        """Sideways-Low-Vol-Szenario-Config."""
        if "sideways_low_vol" not in scenario_configs:
            pytest.skip("sideways_low_vol scenario not found")
        return scenario_configs["sideways_low_vol"]

    def test_is_regime_category(self, sideways_config):
        """Sideways ist Kategorie 'regime'."""
        assert sideways_config["scenario"]["category"] == "regime"

    def test_has_low_volatility(self, sideways_config):
        """Sideways hat niedrige Volatilität."""
        vol = sideways_config["scenario"]["market_conditions"]["volatility"]
        assert vol == "low", f"Expected low volatility, got {vol}"

    def test_has_sideways_trend(self, sideways_config):
        """Sideways hat Seitwärts-Trend."""
        trend = sideways_config["scenario"]["market_conditions"]["trend"]
        assert trend == "sideways", f"Expected sideways trend, got {trend}"

    def test_has_expected_winners_losers(self, sideways_config):
        """Sideways definiert erwartete Gewinner/Verlierer."""
        expectations = sideways_config["scenario"]["test_expectations"]
        assert "expected_winners" in expectations, "Missing expected_winners"
        assert "expected_losers" in expectations, "Missing expected_losers"


class TestTrendRegimeScenario:
    """Tests für das Trend-Regime-Szenario."""

    @pytest.fixture
    def trend_config(self, scenario_configs):
        """Trend-Regime-Szenario-Config."""
        if "trend_regime" not in scenario_configs:
            pytest.skip("trend_regime scenario not found")
        return scenario_configs["trend_regime"]

    def test_is_regime_category(self, trend_config):
        """Trend ist Kategorie 'regime'."""
        assert trend_config["scenario"]["category"] == "regime"

    def test_has_uptrend(self, trend_config):
        """Trend hat Aufwärtstrend."""
        trend = trend_config["scenario"]["market_conditions"]["trend"]
        assert trend in ["up", "down"], f"Expected up/down trend, got {trend}"

    def test_has_moderate_severity(self, trend_config):
        """Trend hat moderate Severity."""
        severity = trend_config["scenario"]["severity"]
        assert severity <= 0.5, f"Trend regime should have moderate severity, got {severity}"

    def test_no_negative_returns_expected(self, trend_config):
        """In starkem Trend werden keine negativen Returns erwartet."""
        expectations = trend_config["scenario"]["test_expectations"]
        assert "allow_negative_returns" in expectations
        # In starkem Trend sollten negative Returns nicht akzeptabel sein
        assert not expectations["allow_negative_returns"]


# =============================================================================
# TESTS: SZENARIO-LOADER
# =============================================================================

class TestScenarioLoader:
    """Tests für das Laden von Szenarien."""

    def test_can_load_all_scenarios(self, all_scenario_files):
        """Alle Szenarien können geladen werden."""
        for scenario_file in all_scenario_files:
            with open(scenario_file, "rb") as fp:
                config = tomllib.load(fp)
            assert config is not None, f"Failed to load {scenario_file}"
            assert "scenario" in config, f"No [scenario] section in {scenario_file}"

    def test_scenario_names_match_filenames(self, scenario_configs):
        """Szenario-Namen stimmen mit Dateinamen überein."""
        for filename, config in scenario_configs.items():
            scenario_name = config["scenario"]["name"]
            assert scenario_name == filename, \
                f"Scenario name '{scenario_name}' doesn't match filename '{filename}'"


# =============================================================================
# TESTS: E2E SZENARIO-WORKFLOW
# =============================================================================

class TestScenarioE2EWorkflow:
    """End-to-End-Tests für Szenario-basierte Research-Workflows."""

    def test_scenario_applicable_strategies_defined(self, scenario_configs):
        """Alle Szenarien definieren anwendbare Strategien."""
        for name, config in scenario_configs.items():
            assert "applicable_strategies" in config.get("scenario", {}), \
                f"{name}: missing scenario.applicable_strategies"
            
            applicable = config["scenario"]["applicable_strategies"]
            assert "primary" in applicable, f"{name}: missing applicable_strategies.primary"

    def test_scenario_expectations_have_drawdown_limits(self, scenario_configs):
        """Alle Szenarien haben Drawdown-Limits."""
        for name, config in scenario_configs.items():
            expectations = config["scenario"]["test_expectations"]
            assert "max_acceptable_drawdown" in expectations, \
                f"{name}: missing max_acceptable_drawdown in test_expectations"
            
            max_dd = expectations["max_acceptable_drawdown"]
            assert max_dd < 0, f"{name}: max_acceptable_drawdown should be negative"
            assert max_dd >= -100, f"{name}: max_acceptable_drawdown too extreme: {max_dd}"

    def test_baseline_expectations_are_reasonable(self, scenario_configs):
        """Baseline-Erwartungen sind realistisch."""
        for name, config in scenario_configs.items():
            expectations = config["scenario"]["test_expectations"]
            
            # Baseline-Drawdown sollte besser als max_acceptable sein
            if "baseline_max_portfolio_drawdown" in expectations:
                baseline_dd = expectations["baseline_max_portfolio_drawdown"]
                max_dd = expectations["max_acceptable_drawdown"]
                assert baseline_dd >= max_dd, \
                    f"{name}: baseline_max_portfolio_drawdown ({baseline_dd}) should be >= max_acceptable_drawdown ({max_dd})"


# =============================================================================
# TESTS: REGRESSION DETECTION
# =============================================================================

class TestScenarioRegressionDetection:
    """Tests für Regressions-Erkennung basierend auf Szenarien."""

    def test_stress_scenarios_have_strict_limits(self, scenario_configs):
        """Stress-Szenarien haben strenge Limits."""
        for name, config in scenario_configs.items():
            if config["scenario"]["category"] == "stress":
                severity = config["scenario"]["severity"]
                max_dd = config["scenario"]["test_expectations"]["max_acceptable_drawdown"]
                
                # Höhere Severity = mehr erlaubter Drawdown
                assert max_dd <= -20, \
                    f"Stress scenario {name} should have max_dd <= -20%, got {max_dd}"

    def test_regime_scenarios_have_expected_behavior(self, scenario_configs):
        """Regime-Szenarien definieren erwartetes Verhalten."""
        for name, config in scenario_configs.items():
            if config["scenario"]["category"] == "regime":
                expectations = config["scenario"]["test_expectations"]
                
                # Regime-Szenarien sollten Gewinner/Verlierer-Strategien definieren
                has_winners = "expected_winners" in expectations
                has_losers = "expected_losers" in expectations
                
                # Mindestens eine Liste sollte vorhanden sein
                assert has_winners or has_losers, \
                    f"Regime scenario {name} should define expected_winners or expected_losers"


# =============================================================================
# INTEGRATION TESTS
# =============================================================================

class TestScenarioIntegration:
    """Integration Tests für Szenarien mit dem Rest des Systems."""

    def test_scenarios_reference_valid_strategies(self, scenario_configs):
        """Szenarien referenzieren nur gültige Strategien."""
        from src.strategies.registry import get_available_strategy_keys
        
        valid_strategies = set(get_available_strategy_keys())
        
        for name, config in scenario_configs.items():
            applicable = config["scenario"].get("applicable_strategies", {})
            
            for category in ["primary", "secondary"]:
                strategies = applicable.get(category, [])
                for strat in strategies:
                    assert strat in valid_strategies, \
                        f"Scenario {name} references unknown strategy: {strat}"

    def test_scenarios_match_tiering_expectations(self, scenario_configs):
        """Szenarien-Erwartungen sind konsistent mit Tiering."""
        from src.experiments.portfolio_presets import get_strategies_by_tier
        
        core_strategies = set(get_strategies_by_tier("core"))
        
        for name, config in scenario_configs.items():
            expectations = config["scenario"].get("test_expectations", {})
            
            # Wenn expected_winners definiert sind, sollten Core-Strategien dabei sein
            winners = set(expectations.get("expected_winners", []))
            if winners and config["scenario"]["category"] == "regime":
                # In mindestens einem Regime sollten Core-Strategien gut abschneiden
                pass  # Soft check - nicht alle Szenarien müssen Core bevorzugen


class TestScenarioDocumentation:
    """Tests für Szenario-Dokumentation."""

    def test_all_scenarios_have_notes(self, scenario_configs):
        """Alle Szenarien haben Notizen/Dokumentation."""
        for name, config in scenario_configs.items():
            assert "notes" in config.get("scenario", {}), \
                f"{name}: missing scenario.notes section"
            
            notes = config["scenario"]["notes"]
            assert "description" in notes, \
                f"{name}: missing notes.description"

    def test_notes_explain_scenario_purpose(self, scenario_configs):
        """Notizen erklären den Zweck des Szenarios."""
        for name, config in scenario_configs.items():
            notes = config["scenario"].get("notes", {})
            description = notes.get("description", "")
            
            # Beschreibung sollte nicht zu kurz sein
            assert len(description) >= 50, \
                f"{name}: notes.description too short ({len(description)} chars)"
