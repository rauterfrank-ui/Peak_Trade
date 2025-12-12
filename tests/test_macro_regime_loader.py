"""
Tests für den Macro Regime Loader.

Testet das Laden von config/macro_regimes/current.toml und den
Zugriff auf verschachtelte Keys.
"""

from __future__ import annotations

from pathlib import Path
from textwrap import dedent

import pytest

from src.macro_regimes.loader import (
    MacroRegimeConfig,
    load_current_macro_regime_config,
)


def _write_current_toml(tmp_path: Path, content: str = "") -> Path:
    """Helper: Erstellt eine current.toml im tmp_path mit passender Verzeichnisstruktur."""
    config_dir = tmp_path / "config" / "macro_regimes"
    config_dir.mkdir(parents=True, exist_ok=True)

    if not content:
        content = dedent(
            """
            [meta]
            date = 2025-12-11
            analyst = "Frank"

            [regime]
            primary = "fed_pause"
            secondary = "tariff_uncertainty"
            signal = "yellow"
            bias = "neutral"

            [sizing]
            max_allocation = 0.70
            rationale = "Test rationale"

            [watchlist]
            primary = ["BTCUSDT", "ETHUSDT"]
            secondary = ["EURUSD"]
            avoid = []

            [strategy_tilt]
            prefer = "mean_reversion"
            rationale = "Seitwärtsmarkt"
            """
        ).lstrip()

    path = config_dir / "current.toml"
    path.write_text(content, encoding="utf-8")
    return path


def test_load_current_macro_regime_config_happy_path(tmp_path: Path) -> None:
    """Test: Lädt current.toml erfolgreich und parsed alle Sections."""
    # Arrange
    _write_current_toml(tmp_path)

    # Act
    cfg = load_current_macro_regime_config(base_dir=tmp_path)

    # Assert
    assert isinstance(cfg, MacroRegimeConfig)
    assert cfg.path.name == "current.toml"
    assert "meta" in cfg.raw
    assert "regime" in cfg.raw
    assert "sizing" in cfg.raw
    assert "watchlist" in cfg.raw
    assert "strategy_tilt" in cfg.raw

    # Nested access via get()
    assert cfg.get("regime.primary") == "fed_pause"
    assert cfg.get("regime.secondary") == "tariff_uncertainty"
    assert cfg.get("regime.signal") == "yellow"
    assert cfg.get("sizing.max_allocation") == 0.70
    assert cfg.get("watchlist.primary") == ["BTCUSDT", "ETHUSDT"]
    assert cfg.get("strategy_tilt.prefer") == "mean_reversion"


def test_load_current_macro_regime_config_missing_file(tmp_path: Path) -> None:
    """Test: FileNotFoundError wenn current.toml nicht existiert."""
    # Arrange: kein current.toml anlegen

    # Act & Assert
    with pytest.raises(FileNotFoundError) as exc_info:
        load_current_macro_regime_config(base_dir=tmp_path)

    assert "Macro-regime-Config" in str(exc_info.value)
    assert "current.toml" in str(exc_info.value)


def test_get_returns_default_for_unknown_key(tmp_path: Path) -> None:
    """Test: get() gibt default zurück wenn Key nicht existiert."""
    # Arrange
    _write_current_toml(tmp_path)
    cfg = load_current_macro_regime_config(base_dir=tmp_path)

    # Act & Assert
    assert cfg.get("does.not.exist") is None
    assert cfg.get("does.not.exist", default="fallback") == "fallback"
    assert cfg.get("regime.unknown_field", default=42) == 42


def test_get_handles_partial_path(tmp_path: Path) -> None:
    """Test: get() gibt default zurück wenn nur Teil des Pfads existiert."""
    # Arrange
    _write_current_toml(tmp_path)
    cfg = load_current_macro_regime_config(base_dir=tmp_path)

    # Act & Assert - regime existiert, aber regime.foo.bar nicht
    assert cfg.get("regime.primary.nonexistent", default="nope") == "nope"


def test_get_returns_section_as_dict(tmp_path: Path) -> None:
    """Test: get() kann auch ganze Sections als Dict zurückgeben."""
    # Arrange
    _write_current_toml(tmp_path)
    cfg = load_current_macro_regime_config(base_dir=tmp_path)

    # Act
    regime_section = cfg.get("regime")

    # Assert
    assert isinstance(regime_section, dict)
    assert regime_section["primary"] == "fed_pause"
    assert regime_section["signal"] == "yellow"


def test_load_with_custom_filename(tmp_path: Path) -> None:
    """Test: Kann auch andere Dateien als current.toml laden (für Archive)."""
    # Arrange
    config_dir = tmp_path / "config" / "macro_regimes"
    config_dir.mkdir(parents=True, exist_ok=True)
    archive_file = config_dir / "2025-12-01_briefing.toml"
    archive_file.write_text(
        dedent(
            """
            [meta]
            date = 2025-12-01
            [regime]
            primary = "risk_on"
            """
        ).lstrip(),
        encoding="utf-8",
    )

    # Act
    cfg = load_current_macro_regime_config(
        base_dir=tmp_path, filename="2025-12-01_briefing.toml"
    )

    # Assert
    assert cfg.get("regime.primary") == "risk_on"
    assert cfg.path.name == "2025-12-01_briefing.toml"


def test_macro_regime_config_is_frozen(tmp_path: Path) -> None:
    """Test: MacroRegimeConfig ist immutable (frozen dataclass)."""
    # Arrange
    _write_current_toml(tmp_path)
    cfg = load_current_macro_regime_config(base_dir=tmp_path)

    # Act & Assert - sollte FrozenInstanceError werfen
    with pytest.raises(Exception):  # FrozenInstanceError ist ein AttributeError
        cfg.path = Path("/other/path")  # type: ignore[misc]
