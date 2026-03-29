# Config-Import-Leitfaden (Peak_Trade)

**Zweck:** Eine **einzige** Referenz für **welches** Config-Subsystem **wo** importiert wird — ohne vollständige API-Dokumentation aller Module.  
**Stand:** 2026-03-29  
**Runbook:** [RUNBOOK_UNIMPLEMENTED_FEATURES_ORDERED.md](../ops/runbooks/RUNBOOK_UNIMPLEMENTED_FEATURES_ORDERED.md) — Stufe A1.

---

## 1. Warum dieser Leitfaden?

Es gibt **mehrere** Loader mit ähnlichen Namen (`load_config`, `get_config`, `list_strategies`). Die Bedeutung hängt vom **Modul** ab. Besonders verwirrend:

| Import | Bedeutung |
|--------|-----------|
| `from src.core import load_config` | **Pydantic**-Loader (`config_pydantic.load_config`) |
| `from src.core.config import load_config` | **Peak/TOML**-Loader (`peak_config.load_config`) |

`src.core.config` ist die **Facade**, die beide Welten re-exportiert; `load_pydantic_config` ist dort der explizite Pydantic-Einstieg.

---

## 2. Vier Subsysteme (Kurz)

| Subsystem | Modul | Typische Rolle |
|-----------|--------|----------------|
| **Peak (TOML, OOP)** | `src/core/peak_config.py` | Live, Sweeps, Exchange-Setup, `PeakConfig` |
| **Pydantic (Legacy)** | `src/core/config_pydantic.py` | `Settings`, gecachte Helfer (`get_config`, …) |
| **Registry (Portfolio)** | `src/core/config_registry.py` | Dict-Registry, aktive Strategien, Backtest-Pipelines |
| **Simple (Dict)** | `src/core/config_simple.py` | Minimaler TOML→Dict-Loader (ältere Skripte/Demos) |

Vertiefung Registry: [CONFIG_REGISTRY_USAGE.md](../CONFIG_REGISTRY_USAGE.md).  
Ältere Einführung zum Dict-Loader: [CONFIG_SYSTEM.md](./CONFIG_SYSTEM.md) (Fokus `config_simple`).

---

## 3. Empfohlene Imports nach Anwendungsfall

### 3.1 Live-Session, Kraken, bounded Live-Limits

```python
from src.core.peak_config import (
    PeakConfig,
    load_config,
    load_config_with_live_overrides,
    load_config_with_bounded_live,  # falls verwendet
)
```

Oder über die Facade (Peak-Loader heißt dort `load_config`):

```python
from src.core.config import load_config, PeakConfig
```

### 3.2 Pydantic-Settings / Legacy-Skripte

```python
from src.core.config_pydantic import get_config, load_config, reset_config
# oder explizit:
from src.core.config_pydantic import load_config as load_pydantic_settings
```

Über Paket-Root (Pydantic ist hier **`load_config`**):

```python
from src.core import load_config  # Pydantic
from src.core import load_peak_config  # Peak/TOML
```

### 3.3 Portfolio-Registry / Walk-Forward / Kraken-Datenpfade mit Registry

```python
from src.core.config_registry import get_config, get_strategy_config, get_active_strategies
```

Paket-Root-Aliase (explizit):

```python
from src.core import get_registry_config, list_registry_strategies
```

### 3.4 Nur Dict, minimal (ältere Demos)

```python
from src.core.config_simple import load_config, list_strategies
```

Hinweis: `list_strategies` in `config_simple` erwartet ein **Config-Dict**; die Signatur unterscheidet sich von Pydantic/Registry.

---

## 4. Namens-Kollisionen außerhalb von `src.core`

| Symbol | Ort | Kein Konflikt mit `src.core`, weil … |
|--------|-----|--------------------------------------|
| `list_strategies(verbose=…)` | `src/strategies/registry.py` | eigene API (Strategie-Katalog) |
| `get_config()` | `src/execution/fault_injection.py` | liefert `FaultConfig` |

---

## 5. Verwandte Artefakte

- Facade: `src/core/config.py` (`__all__`, Re-exports)
- Spike-Notiz (Hotspot-Inventar): [A1_CONFIG_MODULE_INVENTORY_2026-03-29.md](../ops/spikes/A1_CONFIG_MODULE_INVENTORY_2026-03-29.md)
