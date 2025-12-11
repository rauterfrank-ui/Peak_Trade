# Phase 36: Test-Suite & Config-Hygiene

## Zusammenfassung

Phase 36 behebt Config-Probleme die zu Test-Fehlern fuehrten und etabliert eine
saubere, reproduzierbare Test-Konfiguration.

**Status**: Abgeschlossen
**Tests**: 1178 passed, 4 skipped

## Problembeschreibung

Nach Phase 35 (Testnet-Integration) versagten 87 von 144 Tests aufgrund von
Config-Problemen:

1. **Duplicate TOML Key Error**:
   - Root `config.toml` hatte `[strategy.rsi_reversion]` doppelt (Zeilen 194 & 297)
   - Fehler: `toml.decoder.TomlDecodeError: What? rsi_reversion already exists?`

2. **Inkonsistente Config-Pfade**:
   - `config_pydantic.py` suchte im falschen Verzeichnis
   - Kein einheitlicher Mechanismus fuer Test-Configs

3. **Fehlende Test-Isolation**:
   - Tests nutzten Produktions-Config
   - Config-Cache-Pollution zwischen Tests

## Loesungen

### 1. TOML-Duplikat behoben

```toml
# config.toml (Zeile 297)
# Umbenannt von [strategy.rsi_reversion] zu:
[strategy.rsi_reversion_advanced]
```

### 2. Einheitliche ENV-Variable

Beide Config-Loader respektieren `PEAK_TRADE_CONFIG_PATH`:

```python
# src/core/peak_config.py & src/core/config_pydantic.py
PEAK_TRADE_CONFIG_ENV_VAR = "PEAK_TRADE_CONFIG_PATH"

def resolve_config_path(path=None):
    if path is not None:
        return Path(path)
    env_path = os.environ.get(PEAK_TRADE_CONFIG_ENV_VAR)
    if env_path:
        return Path(env_path)
    return _PROJECT_ROOT / "config" / "config.toml"
```

### 3. Dedizierte Test-Config

Neue `config/config.test.toml` mit:
- Test-freundliche Pfade (`test_results/`, `test_data/`, `test_runs/`)
- Sichere Default-Werte
- Alle notwendigen Strategy-Sektionen
- Keine echten API-Keys (nur ENV-Platzhalter)

### 4. Automatisches Test-Setup

`tests/conftest.py` setzt automatisch die Test-Config:

```python
# Modul-Level: Sofort bei Import setzen
if _TEST_CONFIG_PATH.exists():
    os.environ["PEAK_TRADE_CONFIG_PATH"] = str(_TEST_CONFIG_PATH)

def pytest_configure(config):
    """Pytest Hook: VOR Test-Collection ausgefuehrt."""
    os.environ["PEAK_TRADE_CONFIG_PATH"] = str(_TEST_CONFIG_PATH)
    try:
        from src.core.config_pydantic import reset_config
        reset_config()
    except ImportError:
        pass

@pytest.fixture(autouse=True)
def _reset_config_cache():
    """Reset Config-Cache vor jedem Test."""
    reset_config()
    yield
    reset_config()
```

## Geaenderte Dateien

| Datei | Aenderung |
|-------|-----------|
| `config.toml` | Duplikat `[strategy.rsi_reversion]` -> `[strategy.rsi_reversion_advanced]` |
| `config/config.test.toml` | Neue dedizierte Test-Config |
| `src/core/peak_config.py` | `load_config()` optional, `PEAK_TRADE_CONFIG_PATH` Support |
| `src/core/config_pydantic.py` | Default-Pfad auf `config/config.toml`, ENV-Variable Support |
| `tests/conftest.py` | Automatisches Test-Config-Setup mit Fixtures und Hooks |
| `tests/test_strategy_config.py` | Flexiblere Assertions fuer beide Naming-Conventions |

## Config-Hierarchie

```
Prioritaet (hoechste zuerst):
1. Explizit uebergebener path Parameter
2. Environment Variable PEAK_TRADE_CONFIG_PATH
3. Default: config/config.toml (relativ zum Projekt-Root)
```

## Verwendung

### Tests ausfuehren (automatisch Test-Config)

```bash
# Standard - Test-Config wird automatisch verwendet
pytest tests/

# Oder explizit
PEAK_TRADE_CONFIG_PATH=config/config.test.toml pytest tests/
```

### Produktions-/Dev-Config verwenden

```bash
# Development
python scripts/run_backtest.py  # nutzt config/config.toml

# Explizit eine andere Config
PEAK_TRADE_CONFIG_PATH=/path/to/custom.toml python scripts/...
```

## Config-Dateien Uebersicht

| Datei | Zweck |
|-------|-------|
| `config/config.toml` | Haupt-Config fuer Development/Production |
| `config/config.test.toml` | Dedizierte Test-Config (keine echten Keys) |
| `config.toml` (Root) | Legacy/Extended Config (27KB) |

## Lessons Learned

1. **Fruehe ENV-Variable setzen**: `conftest.py` Modul-Level ist kritisch
2. **Config-Cache beachten**: Singleton-Pattern erfordert explizites Reset
3. **Test-Isolation**: Jeder Test sollte mit frischer Config starten
4. **Flexible Assertions**: Tests sollten verschiedene Config-Varianten unterstuetzen

## Naechste Schritte

- [ ] Langfristig: Legacy root `config.toml` evaluieren (Consolidation?)
- [ ] CI/CD: `PEAK_TRADE_CONFIG_PATH` im GitHub Actions Workflow setzen
- [ ] Config-Validierung: Schema-basierte Validierung fuer Config-Dateien
