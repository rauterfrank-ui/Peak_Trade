#!/usr/bin/env python3
"""
Tests für view_r_and_d_experiments.py CLI-Tool.

Testet das Laden, Filtern und Formatieren von R&D-Experiment-Reports.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

# Projekt-Root zum Path hinzufügen
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from scripts.view_r_and_d_experiments import (
    load_experiment_json,
    load_all_experiments,
    filter_experiments,
    extract_date_from_timestamp,
    format_percent,
    format_number,
    format_timestamp,
    determine_status,
    truncate,
    get_safe,
    main,
)


# =============================================================================
# FIXTURES
# =============================================================================


@pytest.fixture
def sample_experiment() -> dict:
    """Beispiel-Experiment-Dict."""
    return {
        "experiment": {
            "preset_id": "test_preset_v1",
            "strategy": "test_strategy",
            "symbol": "BTC/USDT",
            "timeframe": "1h",
            "from_date": "2024-01-01",
            "to_date": "2024-12-31",
            "tag": "exp_test_v1",
            "timestamp": "20241208_120000",
            "hypothesis": "Test hypothesis",
            "focus_metrics": ["sharpe", "total_return"],
        },
        "parameters": {
            "param1": 10,
            "param2": 0.5,
        },
        "results": {
            "total_return": 0.15,
            "max_drawdown": -0.08,
            "sharpe": 1.5,
            "total_trades": 42,
            "win_rate": 0.55,
            "profit_factor": 1.8,
            "bars": 500,
        },
        "meta": {
            "tier": "r_and_d",
            "experimental": True,
            "allow_live": False,
            "seed": 42,
            "use_dummy_data": True,
        },
    }


@pytest.fixture
def sample_experiment_no_trades() -> dict:
    """Experiment ohne Trades."""
    return {
        "experiment": {
            "preset_id": "empty_preset",
            "strategy": "empty_strategy",
            "symbol": "ETH/USDT",
            "timeframe": "4h",
            "tag": "exp_empty",
            "timestamp": "20241207_100000",
        },
        "results": {
            "total_return": 0.0,
            "max_drawdown": 0.0,
            "sharpe": 0.0,
            "total_trades": 0,
            "win_rate": 0.0,
            "profit_factor": 0.0,
        },
        "meta": {
            "use_dummy_data": True,
        },
    }


@pytest.fixture
def temp_experiments_dir(tmp_path: Path, sample_experiment, sample_experiment_no_trades) -> Path:
    """Temporäres Verzeichnis mit Test-JSON-Dateien."""
    exp_dir = tmp_path / "experiments"
    exp_dir.mkdir()

    # Schreibe Beispiel-Experimente
    with open(exp_dir / "exp_test_v1_20241208_120000.json", "w") as f:
        json.dump(sample_experiment, f)

    with open(exp_dir / "exp_empty_20241207_100000.json", "w") as f:
        json.dump(sample_experiment_no_trades, f)

    # Kaputte JSON-Datei
    with open(exp_dir / "broken.json", "w") as f:
        f.write("{invalid json")

    return exp_dir


# =============================================================================
# UNIT TESTS
# =============================================================================


class TestLoadExperimentJson:
    """Tests für load_experiment_json."""

    def test_load_valid_json(self, tmp_path: Path, sample_experiment):
        """Lädt eine gültige JSON-Datei."""
        filepath = tmp_path / "test.json"
        with open(filepath, "w") as f:
            json.dump(sample_experiment, f)

        result = load_experiment_json(filepath)
        assert result is not None
        assert result["experiment"]["preset_id"] == "test_preset_v1"
        assert "_filepath" in result
        assert "_filename" in result

    def test_load_invalid_json(self, tmp_path: Path):
        """Gibt None zurück bei ungültigem JSON."""
        filepath = tmp_path / "invalid.json"
        with open(filepath, "w") as f:
            f.write("{broken json")

        result = load_experiment_json(filepath)
        assert result is None

    def test_load_nonexistent_file(self, tmp_path: Path):
        """Gibt None zurück bei nicht existierender Datei."""
        filepath = tmp_path / "nonexistent.json"
        result = load_experiment_json(filepath)
        assert result is None


class TestLoadAllExperiments:
    """Tests für load_all_experiments."""

    def test_load_all_from_directory(self, temp_experiments_dir):
        """Lädt alle gültigen JSON-Dateien aus Verzeichnis."""
        experiments = load_all_experiments(temp_experiments_dir)
        # 2 gültige, 1 kaputte -> 2 geladen
        assert len(experiments) == 2

    def test_load_from_nonexistent_directory(self, tmp_path: Path):
        """Gibt leere Liste zurück bei nicht existierendem Verzeichnis."""
        experiments = load_all_experiments(tmp_path / "nonexistent")
        assert experiments == []

    def test_sorted_by_timestamp(self, temp_experiments_dir):
        """Ergebnisse sind nach Timestamp sortiert (neueste zuerst)."""
        experiments = load_all_experiments(temp_experiments_dir)
        # 20241208 ist neuer als 20241207
        assert experiments[0]["experiment"]["timestamp"] == "20241208_120000"
        assert experiments[1]["experiment"]["timestamp"] == "20241207_100000"


class TestFilterExperiments:
    """Tests für filter_experiments."""

    def test_filter_by_preset(self, sample_experiment, sample_experiment_no_trades):
        """Filtert nach preset_id."""
        experiments = [sample_experiment, sample_experiment_no_trades]
        filtered = filter_experiments(experiments, preset="test_preset_v1")
        assert len(filtered) == 1
        assert filtered[0]["experiment"]["preset_id"] == "test_preset_v1"

    def test_filter_by_tag_substr(self, sample_experiment, sample_experiment_no_trades):
        """Filtert nach Tag-Substring."""
        experiments = [sample_experiment, sample_experiment_no_trades]
        filtered = filter_experiments(experiments, tag_substr="test")
        assert len(filtered) == 1
        assert "test" in filtered[0]["experiment"]["tag"]

    def test_filter_by_strategy(self, sample_experiment, sample_experiment_no_trades):
        """Filtert nach Strategy."""
        experiments = [sample_experiment, sample_experiment_no_trades]
        filtered = filter_experiments(experiments, strategy="test_strategy")
        assert len(filtered) == 1

    def test_filter_by_date_from(self, sample_experiment, sample_experiment_no_trades):
        """Filtert ab Datum."""
        experiments = [sample_experiment, sample_experiment_no_trades]
        filtered = filter_experiments(experiments, date_from="2024-12-08")
        assert len(filtered) == 1
        assert filtered[0]["experiment"]["timestamp"] == "20241208_120000"

    def test_filter_by_date_to(self, sample_experiment, sample_experiment_no_trades):
        """Filtert bis Datum."""
        experiments = [sample_experiment, sample_experiment_no_trades]
        filtered = filter_experiments(experiments, date_to="2024-12-07")
        assert len(filtered) == 1
        assert filtered[0]["experiment"]["timestamp"] == "20241207_100000"

    def test_combined_filters(self, sample_experiment, sample_experiment_no_trades):
        """Kombinierte Filter."""
        experiments = [sample_experiment, sample_experiment_no_trades]
        filtered = filter_experiments(
            experiments,
            preset="test_preset_v1",
            date_from="2024-12-01",
        )
        assert len(filtered) == 1


class TestFormatters:
    """Tests für Formatierungs-Funktionen."""

    def test_extract_date_from_timestamp(self):
        """Extrahiert Datum aus Timestamp."""
        from datetime import datetime

        result = extract_date_from_timestamp("20241208_120000")
        assert result == datetime(2024, 12, 8)

    def test_extract_date_invalid(self):
        """Gibt None bei ungültigem Timestamp."""
        assert extract_date_from_timestamp("invalid") is None
        assert extract_date_from_timestamp("") is None
        assert extract_date_from_timestamp(None) is None

    def test_format_percent(self):
        """Formatiert Prozent-Werte."""
        assert format_percent(0.15) == "15.0%"
        assert format_percent(-0.08) == "-8.0%"
        assert format_percent(0.0) == "0.0%"
        assert format_percent(None) == "-"
        assert format_percent("-") == "-"

    def test_format_number(self):
        """Formatiert numerische Werte."""
        assert format_number(1.5) == "1.50"
        assert format_number(0.0) == "0.00"
        assert format_number(None) == "-"

    def test_format_timestamp(self):
        """Formatiert Timestamp für Anzeige."""
        assert format_timestamp("20241208_120000") == "2024-12-08 12:00"
        assert format_timestamp("") == "-"
        assert format_timestamp(None) == "-"

    def test_truncate(self):
        """Kürzt lange Strings."""
        assert truncate("short", 10) == "short"
        assert truncate("verylongstring", 10) == "verylongs…"
        assert truncate("", 10) == "-"
        assert truncate(None, 10) == "-"


class TestDetermineStatus:
    """Tests für determine_status."""

    def test_status_ok(self, sample_experiment):
        """Status 'ok' bei Trades vorhanden."""
        assert determine_status(sample_experiment) == "ok"

    def test_status_no_trades(self, sample_experiment_no_trades):
        """Status 'no_trades' bei 0 Trades."""
        assert determine_status(sample_experiment_no_trades) == "no_trades"


class TestGetSafe:
    """Tests für get_safe."""

    def test_get_nested_value(self):
        """Holt verschachtelte Werte."""
        data = {"a": {"b": {"c": 42}}}
        assert get_safe(data, "a", "b", "c") == 42

    def test_get_missing_key(self):
        """Gibt Default bei fehlendem Key."""
        data = {"a": 1}
        assert get_safe(data, "b") == "-"
        assert get_safe(data, "b", default=None) is None

    def test_get_from_none(self):
        """Gibt Default bei None in Pfad."""
        data = {"a": None}
        assert get_safe(data, "a", "b") == "-"


# =============================================================================
# INTEGRATION TESTS (CLI)
# =============================================================================


class TestCLI:
    """Integration-Tests für CLI."""

    def test_main_with_empty_dir(self, tmp_path: Path):
        """CLI mit leerem Verzeichnis."""
        empty_dir = tmp_path / "empty"
        empty_dir.mkdir()
        exit_code = main(["--dir", str(empty_dir)])
        assert exit_code == 0

    def test_main_with_experiments(self, temp_experiments_dir):
        """CLI mit Test-Experimenten."""
        exit_code = main(["--dir", str(temp_experiments_dir)])
        assert exit_code == 0

    def test_main_with_json_output(self, temp_experiments_dir, capsys):
        """CLI mit JSON-Output."""
        exit_code = main(["--dir", str(temp_experiments_dir), "--output", "json"])
        assert exit_code == 0
        captured = capsys.readouterr()
        # Sollte gültiges JSON sein
        data = json.loads(captured.out)
        assert isinstance(data, list)
        assert len(data) == 2

    def test_main_with_preset_filter(self, temp_experiments_dir, capsys):
        """CLI mit Preset-Filter."""
        exit_code = main(
            [
                "--dir",
                str(temp_experiments_dir),
                "--preset",
                "test_preset_v1",
                "--output",
                "json",
            ]
        )
        assert exit_code == 0
        captured = capsys.readouterr()
        data = json.loads(captured.out)
        assert len(data) == 1
        assert data[0]["experiment"]["preset_id"] == "test_preset_v1"

    def test_main_with_run_id(self, temp_experiments_dir, capsys):
        """CLI mit Run-ID für Detail-Ansicht."""
        exit_code = main(
            [
                "--dir",
                str(temp_experiments_dir),
                "--run-id",
                "20241208_120000",
            ]
        )
        assert exit_code == 0
        captured = capsys.readouterr()
        # Sollte gültiges JSON sein (Detail-Ansicht)
        data = json.loads(captured.out)
        assert data["experiment"]["timestamp"] == "20241208_120000"

    def test_main_with_file(self, temp_experiments_dir, capsys):
        """CLI mit direkter Datei-Angabe."""
        filepath = temp_experiments_dir / "exp_test_v1_20241208_120000.json"
        exit_code = main(["--file", str(filepath)])
        assert exit_code == 0
        captured = capsys.readouterr()
        data = json.loads(captured.out)
        assert data["experiment"]["preset_id"] == "test_preset_v1"

    def test_main_with_nonexistent_file(self, tmp_path: Path):
        """CLI mit nicht existierender Datei."""
        exit_code = main(["--file", str(tmp_path / "nonexistent.json")])
        assert exit_code == 1

    def test_main_with_limit(self, temp_experiments_dir, capsys):
        """CLI mit Limit."""
        exit_code = main(
            [
                "--dir",
                str(temp_experiments_dir),
                "--limit",
                "1",
                "--output",
                "json",
            ]
        )
        assert exit_code == 0
        captured = capsys.readouterr()
        data = json.loads(captured.out)
        assert len(data) == 1

    def test_main_with_trades_filter(self, temp_experiments_dir, capsys):
        """CLI mit --with-trades Filter."""
        exit_code = main(
            [
                "--dir",
                str(temp_experiments_dir),
                "--with-trades",
                "--output",
                "json",
            ]
        )
        assert exit_code == 0
        captured = capsys.readouterr()
        data = json.loads(captured.out)
        # Nur das Experiment mit Trades (sample_experiment hat 42 Trades)
        assert len(data) == 1
        assert data[0]["results"]["total_trades"] == 42
