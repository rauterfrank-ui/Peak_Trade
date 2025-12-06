# tests/conftest.py
"""
Peak_Trade Test Configuration (Phase 36)
=========================================

Dieses conftest.py setzt automatisch die Test-Config fuer alle Tests.

Funktionsweise:
    - ENV-Variable wird SOFORT bei Import gesetzt (bevor andere Module laden)
    - Alle Config-Loader (peak_config.py, config_pydantic.py) respektieren diese ENV-Variable
    - Tests laufen isoliert von Produktions-Config
    - Config-Cache wird vor jedem Test zurueckgesetzt

Verwendung:
    # Tests einfach normal ausfuehren - Config wird automatisch gesetzt
    pytest tests/
    pytest tests/test_backtest_smoke.py -v

    # ENV-Variable kann auch manuell gesetzt werden:
    PEAK_TRADE_CONFIG_PATH=config/config.test.toml pytest tests/
"""
from __future__ import annotations

import os
from pathlib import Path

import pytest


# Projekt-Root ermitteln (relativ zu dieser Datei)
_PROJECT_ROOT = Path(__file__).resolve().parents[1]

# Pfad zur Test-Config
_TEST_CONFIG_PATH = _PROJECT_ROOT / "config" / "config.test.toml"

# ============================================================================
# WICHTIG: ENV-Variable SOFORT setzen, BEVOR andere Module importiert werden!
# Dies muss auf Modul-Ebene passieren, nicht in einer Fixture.
# ============================================================================
if _TEST_CONFIG_PATH.exists():
    os.environ["PEAK_TRADE_CONFIG_PATH"] = str(_TEST_CONFIG_PATH)


def pytest_configure(config):
    """
    Pytest Hook: Wird VOR Test-Collection ausgefuehrt.

    Setzt ENV-Variable und resettet Config-Caches, um sicherzustellen,
    dass alle Tests die Test-Config verwenden.
    """
    # ENV-Variable erneut setzen (fuer den Fall, dass sie ueberschrieben wurde)
    os.environ["PEAK_TRADE_CONFIG_PATH"] = str(_TEST_CONFIG_PATH)

    # Config-Caches zuruecksetzen
    try:
        from src.core.config_pydantic import reset_config
        reset_config()
    except ImportError:
        pass


@pytest.fixture(autouse=True, scope="session")
def _set_test_config_env():
    """
    Session-scoped Fixture: Setzt PEAK_TRADE_CONFIG_PATH fuer alle Tests.

    Diese Fixture wird automatisch vor allen Tests ausgefuehrt (autouse=True)
    und gilt fuer die gesamte Test-Session (scope="session").

    Nach den Tests wird die ENV-Variable wieder entfernt (Cleanup).
    """
    # Sicherstellen, dass Test-Config existiert
    if not _TEST_CONFIG_PATH.exists():
        pytest.fail(
            f"Test-Config nicht gefunden: {_TEST_CONFIG_PATH}\n"
            f"Bitte config/config.test.toml erstellen."
        )

    # ENV-Variable setzen BEVOR irgendwelche Imports passieren
    old_value = os.environ.get("PEAK_TRADE_CONFIG_PATH")
    os.environ["PEAK_TRADE_CONFIG_PATH"] = str(_TEST_CONFIG_PATH)

    # Config-Caches zuruecksetzen (falls schon geladen)
    try:
        from src.core.config_pydantic import reset_config
        reset_config()
    except ImportError:
        pass

    yield

    # Cleanup: Alten Wert wiederherstellen oder Variable entfernen
    if old_value is not None:
        os.environ["PEAK_TRADE_CONFIG_PATH"] = old_value
    else:
        os.environ.pop("PEAK_TRADE_CONFIG_PATH", None)


@pytest.fixture(autouse=True)
def _reset_config_cache():
    """
    Reset Config-Cache vor jedem Test.

    Dies stellt sicher, dass jeder Test mit einer frischen Config startet
    und keine Cache-Pollution von vorherigen Tests uebernimmt.
    """
    try:
        from src.core.config_pydantic import reset_config
        reset_config()
    except ImportError:
        pass
    yield
    # Cleanup nach dem Test
    try:
        from src.core.config_pydantic import reset_config
        reset_config()
    except ImportError:
        pass


@pytest.fixture
def test_config_path() -> Path:
    """
    Fixture die den Pfad zur Test-Config zurueckgibt.

    Nuetzlich fuer Tests, die den Config-Pfad explizit benoetigen.

    Example:
        def test_something(test_config_path):
            cfg = load_config(test_config_path)
            assert cfg.get("backtest.initial_cash") == 10000.0
    """
    return _TEST_CONFIG_PATH


@pytest.fixture
def project_root() -> Path:
    """
    Fixture die das Projekt-Root-Verzeichnis zurueckgibt.

    Example:
        def test_file_exists(project_root):
            assert (project_root / "pyproject.toml").exists()
    """
    return _PROJECT_ROOT
