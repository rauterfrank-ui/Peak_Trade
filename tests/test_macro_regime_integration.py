"""
Integrationstest für Macro Regime Loader.

Testet, dass die echte config/macro_regimes/current.toml im Repo
geladen werden kann und valide Werte enthält.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from src.macro_regimes import load_current_macro_regime_config


@pytest.mark.integration
def test_current_macro_regime_file_can_be_loaded_from_repo_root(
    project_root: Path,
) -> None:
    """
    Integrationstest: Lädt die echte current.toml aus dem Repo.

    Dieser Test setzt voraus, dass config/macro_regimes/current.toml existiert.
    Er validiert nur, dass die Datei geladen werden kann und nicht leer ist.
    Schema-Checks kommen später in einem eigenen Block.
    """
    # Act
    cfg = load_current_macro_regime_config(base_dir=project_root)

    # Assert - Minimale Sanity-Checks
    assert cfg.raw, "Macro-Regime-Config darf nicht leer sein"
    assert cfg.path.exists(), "Pfad zur geladenen Config muss existieren"

    # Prüfe dass Kern-Sections vorhanden sind
    assert "regime" in cfg.raw, "Section [regime] muss existieren"
    assert "sizing" in cfg.raw, "Section [sizing] muss existieren"

    # Prüfe dass regime.primary gesetzt ist
    primary = cfg.get("regime.primary")
    assert primary is not None, "regime.primary muss gesetzt sein"
    assert isinstance(primary, str), "regime.primary muss ein String sein"

    # Prüfe dass sizing.max_allocation ein valider Float ist
    max_alloc = cfg.get("sizing.max_allocation")
    assert max_alloc is not None, "sizing.max_allocation muss gesetzt sein"
    assert isinstance(max_alloc, (int, float)), "sizing.max_allocation muss numerisch sein"
    assert 0.0 <= max_alloc <= 1.0, "sizing.max_allocation muss zwischen 0 und 1 liegen"


@pytest.mark.integration
def test_current_macro_regime_has_expected_schema_fields(
    project_root: Path,
) -> None:
    """
    Integrationstest: Prüft dass die wichtigsten Schema-Felder vorhanden sind.
    """
    cfg = load_current_macro_regime_config(base_dir=project_root)

    # Regime Section
    assert cfg.get("regime.primary") is not None
    assert cfg.get("regime.signal") in ("green", "yellow", "red", None)
    assert cfg.get("regime.bias") in ("risk_on", "neutral", "risk_off", None)

    # Sizing Section
    assert cfg.get("sizing.max_allocation") is not None

    # Watchlist Section (optional, aber wenn vorhanden muss primary eine Liste sein)
    watchlist_primary = cfg.get("watchlist.primary")
    if watchlist_primary is not None:
        assert isinstance(watchlist_primary, list), "watchlist.primary muss eine Liste sein"

    # Strategy Tilt Section
    strategy_prefer = cfg.get("strategy_tilt.prefer")
    if strategy_prefer is not None:
        assert strategy_prefer in (
            "mean_reversion",
            "trend_following",
            "balanced",
            "defensive",
        ), f"strategy_tilt.prefer hat ungültigen Wert: {strategy_prefer}"
