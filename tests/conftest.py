# tests/conftest.py
"""
Peak_Trade Test Configuration (Phase 36, erweitert Phase 59)
=============================================================

Dieses conftest.py setzt automatisch die Test-Config fuer alle Tests.

Funktionsweise:
    - ENV-Variable wird SOFORT bei Import gesetzt (bevor andere Module laden)
    - Alle Config-Loader (peak_config.py, config_pydantic.py) respektieren diese ENV-Variable
    - Tests laufen isoliert von Produktions-Config
    - Config-Cache wird vor jedem Test zurueckgesetzt
    - Warning-Filter für bekannte, harmlose Warnings (Phase 59)

Verwendung:
    # Tests einfach normal ausfuehren - Config wird automatisch gesetzt
    pytest tests/
    pytest tests/test_backtest_smoke.py -v

    # ENV-Variable kann auch manuell gesetzt werden:
    PEAK_TRADE_CONFIG_PATH=config/config.test.toml pytest tests/
"""

from __future__ import annotations

import os
import sys
import warnings
from pathlib import Path

import pytest

# ============================================================================
# Warning-Filter (Phase 59)
# ============================================================================
# Filter für bekannte, harmlose Warnings, die nicht behoben werden können
# oder von externen Libraries stammen.

# Pandas FutureWarnings (bekannte, harmlose Warnings von pandas/numpy)
warnings.filterwarnings(
    "ignore",
    category=FutureWarning,
    message=".*DataFrame.append.*",
    module="pandas",
)

# Weitere bekannte, harmlose Warnings können hier hinzugefügt werden
# mit klarem Kommentar, warum sie gefiltert werden.


# Projekt-Root ermitteln (relativ zu dieser Datei)
_PROJECT_ROOT = Path(__file__).resolve().parents[1]

# Ensure src/ is importable as a top-level package root for tests.
# Many tests import modules like `ai_orchestration.*` (package lives under src/).
_SRC_DIR = _PROJECT_ROOT / "src"
if _SRC_DIR.exists():
    src_str = str(_SRC_DIR)
    if src_str not in sys.path:
        sys.path.insert(0, src_str)

# Pfad zur Test-Config
_TEST_CONFIG_PATH = _PROJECT_ROOT / "config" / "config.test.toml"

# ============================================================================
# WICHTIG: ENV-Variable SOFORT setzen, BEVOR andere Module importiert werden!
# Dies muss auf Modul-Ebene passieren, nicht in einer Fixture.
# ============================================================================
if _TEST_CONFIG_PATH.exists():
    os.environ["PEAK_TRADE_CONFIG_PATH"] = str(_TEST_CONFIG_PATH)


def pytest_addoption(parser):
    """Add command-line options."""
    parser.addoption(
        "--run-perf",
        action="store_true",
        default=False,
        help="Run performance tests (otherwise skipped)",
    )


def pytest_configure(config):
    """
    Pytest Hook: Wird VOR Test-Collection ausgefuehrt.

    Setzt ENV-Variable und resettet Config-Caches, um sicherzustellen,
    dass alle Tests die Test-Config verwenden.

    Fügt auch Warning-Filter für bekannte, harmlose Warnungen hinzu.
    """
    # ENV-Variable erneut setzen (fuer den Fall, dass sie ueberschrieben wurde)
    os.environ["PEAK_TRADE_CONFIG_PATH"] = str(_TEST_CONFIG_PATH)

    # Config-Caches zuruecksetzen
    try:
        from src.core.config_pydantic import reset_config

        reset_config()
    except ImportError:
        pass

    # Warning-Filter für pytest hinzufügen (Phase 68 v1.0 Hardening)
    # Diese werden zur filterwarnings-Liste von pytest hinzugefügt
    config.addinivalue_line(
        "filterwarnings", "ignore:cannot collect test class:pytest.PytestCollectionWarning"
    )
    # urllib3 LibreSSL Warning (macOS system Python with LibreSSL)
    config.addinivalue_line("filterwarnings", "ignore:urllib3 v2 only supports OpenSSL")


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
