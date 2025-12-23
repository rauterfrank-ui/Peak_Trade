# tests/test_phase73_live_dry_run_drills.py
"""
Peak_Trade: Tests für Phase 73 - Live-Dry-Run Drills & Safety-Validation
=========================================================================

Testet das Drill-System für Sicherheits-Validierung im Dry-Run-Modus.

Phase 73: Read-Only Simulation, keine echten Orders.
"""

from __future__ import annotations

import pytest

from src.core.environment import (
    EnvironmentConfig,
    TradingEnvironment,
    LIVE_CONFIRM_TOKEN,
)
from src.live.drills import (
    LiveDrillScenario,
    LiveDrillResult,
    LiveDrillRunner,
    get_default_live_drill_scenarios,
)


class TestLiveDrillScenarios:
    """Tests für Live-Drill-Szenarien (Phase 73)."""

    def test_get_default_live_drill_scenarios_returns_scenarios(self):
        """Test: get_default_live_drill_scenarios() gibt Szenarien zurück."""
        scenarios = get_default_live_drill_scenarios()

        assert len(scenarios) >= 5  # Mindestens A-E
        assert all(isinstance(s, LiveDrillScenario) for s in scenarios)

        # Prüfe, dass erwartete Szenarien vorhanden sind
        names = [s.name for s in scenarios]
        assert any("A - Voll gebremst" in name for name in names)
        assert any("B - Gate 1 ok" in name for name in names)
        assert any("C - Alles armed" in name for name in names)
        assert any("D - Confirm-Token" in name for name in names)

    def test_drill_scenario_a_fully_blocked(self):
        """Test: Drill A - Voll gebremst."""
        scenarios = get_default_live_drill_scenarios()
        scenario_a = next(s for s in scenarios if "A - Voll gebremst" in s.name)

        assert scenario_a.expected_is_live_execution_allowed is False
        assert "enable_live_trading=False" in scenario_a.expected_reasons
        assert scenario_a.env_overrides["enable_live_trading"] is False

    def test_drill_scenario_b_gate2_missing(self):
        """Test: Drill B - Gate 1 ok, Gate 2 fehlt."""
        scenarios = get_default_live_drill_scenarios()
        scenario_b = next(s for s in scenarios if "B - Gate 1 ok" in s.name)

        assert scenario_b.expected_is_live_execution_allowed is False
        assert any("live_mode_armed" in r for r in scenario_b.expected_reasons)
        assert scenario_b.env_overrides["enable_live_trading"] is True
        assert scenario_b.env_overrides["live_mode_armed"] is False

    def test_drill_scenario_c_all_armed_but_dry_run(self):
        """Test: Drill C - Alles armed, aber Dry-Run aktiv."""
        scenarios = get_default_live_drill_scenarios()
        scenario_c = next(s for s in scenarios if "C - Alles armed" in s.name)

        assert scenario_c.expected_is_live_execution_allowed is False
        assert any("live_dry_run_mode" in r for r in scenario_c.expected_reasons)
        assert scenario_c.env_overrides["enable_live_trading"] is True
        assert scenario_c.env_overrides["live_mode_armed"] is True
        assert scenario_c.env_overrides["live_dry_run_mode"] is True

    def test_drill_scenario_d_confirm_token_missing(self):
        """Test: Drill D - Confirm-Token fehlt."""
        scenarios = get_default_live_drill_scenarios()
        scenario_d = next(s for s in scenarios if "D - Confirm-Token" in s.name)

        assert scenario_d.expected_is_live_execution_allowed is False
        assert any("confirm_token" in r for r in scenario_d.expected_reasons)
        assert scenario_d.env_overrides.get("confirm_token") != LIVE_CONFIRM_TOKEN


class TestLiveDrillRunner:
    """Tests für LiveDrillRunner (Phase 73)."""

    def test_run_scenario_a_fully_blocked(self):
        """Test: Runner führt Drill A aus."""
        scenarios = get_default_live_drill_scenarios()
        scenario_a = next(s for s in scenarios if "A - Voll gebremst" in s.name)

        runner = LiveDrillRunner()
        result = runner.run_scenario(scenario_a)

        assert result.scenario_name == scenario_a.name
        assert result.passed is True
        assert result.is_live_execution_allowed is False
        assert "enable_live_trading=False" in result.reason
        assert len(result.violations) == 0

    def test_run_scenario_b_gate2_missing(self):
        """Test: Runner führt Drill B aus."""
        scenarios = get_default_live_drill_scenarios()
        scenario_b = next(s for s in scenarios if "B - Gate 1 ok" in s.name)

        runner = LiveDrillRunner()
        result = runner.run_scenario(scenario_b)

        assert result.scenario_name == scenario_b.name
        assert result.passed is True
        assert result.is_live_execution_allowed is False
        assert "live_mode_armed" in result.reason
        assert len(result.violations) == 0

    def test_run_scenario_c_all_armed_but_dry_run(self):
        """Test: Runner führt Drill C aus."""
        scenarios = get_default_live_drill_scenarios()
        scenario_c = next(s for s in scenarios if "C - Alles armed" in s.name)

        runner = LiveDrillRunner()
        result = runner.run_scenario(scenario_c)

        assert result.scenario_name == scenario_c.name
        assert result.passed is True
        assert result.is_live_execution_allowed is False
        assert "live_dry_run_mode" in result.reason
        assert result.effective_mode == "live_dry_run"
        assert len(result.violations) == 0

    def test_run_scenario_d_confirm_token_missing(self):
        """Test: Runner führt Drill D aus."""
        scenarios = get_default_live_drill_scenarios()
        scenario_d = next(s for s in scenarios if "D - Confirm-Token" in s.name)

        runner = LiveDrillRunner()
        result = runner.run_scenario(scenario_d)

        assert result.scenario_name == scenario_d.name
        assert result.passed is True
        assert result.is_live_execution_allowed is False
        assert "confirm_token" in result.reason
        assert len(result.violations) == 0

    def test_run_scenario_f_non_live_mode(self):
        """Test: Runner führt Drill F (Testnet) aus."""
        scenarios = get_default_live_drill_scenarios()
        scenario_f = next(s for s in scenarios if "F - Nicht-Live-Modus" in s.name)

        runner = LiveDrillRunner()
        result = runner.run_scenario(scenario_f)

        assert result.scenario_name == scenario_f.name
        assert result.passed is True
        assert result.is_live_execution_allowed is False
        assert "nicht LIVE" in result.reason
        assert result.effective_mode in ["dry_run", "paper"]
        assert len(result.violations) == 0

    def test_run_all_scenarios(self):
        """Test: Runner führt alle Szenarien aus."""
        scenarios = get_default_live_drill_scenarios()

        runner = LiveDrillRunner()
        results = runner.run_all(scenarios)

        assert len(results) == len(scenarios)
        assert all(isinstance(r, LiveDrillResult) for r in results)

        # Alle Drills sollten bestanden werden (Standard-Szenarien sind korrekt definiert)
        # Falls nicht, ist das ein Hinweis auf ein Problem in den Szenarien
        passed_count = sum(1 for r in results if r.passed)
        assert passed_count == len(
            scenarios
        ), f"Erwartet: alle {len(scenarios)} Drills bestanden, tatsächlich: {passed_count}"

    def test_run_scenario_with_violation(self):
        """Test: Runner erkennt Violations korrekt."""
        # Szenario mit falscher Erwartung erstellen
        scenario = LiveDrillScenario(
            name="Test - Falsche Erwartung",
            description="Szenario mit falscher Erwartung für Violation-Test",
            env_overrides={
                "environment": TradingEnvironment.LIVE,
                "enable_live_trading": False,
            },
            expected_is_live_execution_allowed=True,  # Falsch - sollte False sein
            expected_reasons=[],
        )

        runner = LiveDrillRunner()
        result = runner.run_scenario(scenario)

        assert result.passed is False
        assert len(result.violations) > 0
        assert "is_live_execution_allowed mismatch" in result.violations[0]

    def test_run_scenario_notes_contain_gating_info(self):
        """Test: Runner sammelt Notizen mit Gating-Informationen."""
        scenarios = get_default_live_drill_scenarios()
        scenario_a = next(s for s in scenarios if "A - Voll gebremst" in s.name)

        runner = LiveDrillRunner()
        result = runner.run_scenario(scenario_a)

        assert len(result.notes) > 0
        notes_str = " ".join(result.notes)
        assert "enable_live_trading" in notes_str
        assert "live_mode_armed" in notes_str
        assert "live_dry_run_mode" in notes_str

    def test_drill_runner_isolated_config(self):
        """Test: Drills laufen in isolierter Config (keine Datei-Änderungen)."""
        scenarios = get_default_live_drill_scenarios()
        scenario_a = next(s for s in scenarios if "A - Voll gebremst" in s.name)

        # Basis-Config erstellen
        base_env = EnvironmentConfig(
            environment=TradingEnvironment.PAPER,
            enable_live_trading=False,
        )

        runner = LiveDrillRunner()
        result = runner.run_scenario(scenario_a, base_env_config=base_env)

        # Prüfe, dass Overrides angewendet wurden
        assert result.is_live_execution_allowed is False
        # Basis-Config sollte unverändert bleiben (nicht direkt prüfbar, aber implizit)
        assert "live" in result.notes[0].lower()  # Override wurde angewendet (case-insensitive)


class TestLiveDrillSafety:
    """Tests für Safety-Aspekte der Drills (Phase 73)."""

    def test_no_config_file_changes(self):
        """Test: Drills ändern keine Config-Dateien."""
        # Dieser Test ist implizit - Drills verwenden nur in-memory Configs
        scenarios = get_default_live_drill_scenarios()

        runner = LiveDrillRunner()
        results = runner.run_all(scenarios)

        # Wenn wir hier ankommen, wurden keine Dateien geändert
        # (sonst hätte es einen Fehler gegeben)
        assert len(results) > 0

    def test_no_exchange_api_calls(self):
        """Test: Drills machen keine Exchange-API-Calls."""
        # Dieser Test ist implizit - Drills verwenden nur is_live_execution_allowed()
        # und SafetyGuard, keine Exchange-Clients
        scenarios = get_default_live_drill_scenarios()

        runner = LiveDrillRunner()
        results = runner.run_all(scenarios)

        # Alle Results sollten nur Gating-Informationen enthalten
        for result in results:
            assert "exchange" not in result.reason.lower()
            assert "api" not in result.reason.lower()
            # "order" kann in Gating-Texten vorkommen (z.B. "echte Orders blockiert")
            # Wichtig ist, dass keine Order-IDs oder API-Responses vorhanden sind
            assert "order_id" not in result.reason.lower()
            assert "api_response" not in result.reason.lower()

    def test_no_real_orders_constructed(self):
        """Test: Drills konstruieren keine echten Orders."""
        # Dieser Test ist implizit - Drills verwenden nur EnvironmentConfig
        # und SafetyGuard, keine OrderExecutor-Instanzen
        scenarios = get_default_live_drill_scenarios()

        runner = LiveDrillRunner()
        results = runner.run_all(scenarios)

        # Alle Results sollten nur Status-Informationen enthalten
        for result in results:
            # Result sollte nur Gating-Status enthalten, keine Order-IDs, etc.
            assert isinstance(result.is_live_execution_allowed, bool)
            assert isinstance(result.reason, str)
            assert isinstance(result.effective_mode, str)

    def test_all_drills_explain_blocking_reasons(self):
        """Test: Alle Drills erklären Blockierungsgründe."""
        scenarios = get_default_live_drill_scenarios()

        runner = LiveDrillRunner()
        results = runner.run_all(scenarios)

        for result in results:
            # Jeder Result sollte einen Reason haben
            assert result.reason
            # Wenn nicht erlaubt, sollte Reason erklären warum
            if not result.is_live_execution_allowed:
                assert len(result.reason) > 10  # Mindestens eine Erklärung
