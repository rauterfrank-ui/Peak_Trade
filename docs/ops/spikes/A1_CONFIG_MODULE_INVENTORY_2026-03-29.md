# A1 — Zentrale Config-Modulstruktur: Import-Story & Hotspot-Inventar

**Spike / Arbeitsnotiz** — kein Merge-Gate.  
**Branch-Kontext:** `feat/a1-central-config-module`  
**Stand:** 2026-03-29

**Runbook:** `docs/ops/runbooks/RUNBOOK_UNIMPLEMENTED_FEATURES_ORDERED.md` — A1 (GAP).

---

## 1. Zweck

Die „Lücke“ A1 ist **nicht** das Fehlen einer Datei `src/core/config.py` — diese **Facade existiert** und re-exportiert Pydantic + Peak. Die eigentliche Lücke ist die **fragmentierte Konfiguration** mit **gleichnamigen** öffentlichen Funktionen in mehreren Modulen und **unterschiedlicher Semantik** (`get_config`, `list_strategies`, `reset_config`, `resolve_config_path`, `load_config`).

Diese Notiz hält die **Import-Story** und **Hotspots** fest, bevor größere Refactors oder Deprecations diskutiert werden.

---

## 2. Vier Config-Pfade (Kern)

| Modul | Rolle | Typische Loader / API |
|--------|--------|-------------------------|
| `peak_config.py` | TOML, OOP `PeakConfig`, Live-Overrides | `load_config`, `load_config_default`, `load_config_with_live_overrides`, `resolve_config_path` |
| `config_pydantic.py` | Legacy Pydantic `Settings` | `load_config` (= Pydantic-Loader), `get_config`, `reset_config`, `list_strategies`, `resolve_config_path` |
| `config_registry.py` | Portfolio-Registry, Dict | `get_config()` → dict, `list_strategies()`, `reset_config()`, eigene `StrategyConfig`-Klasse |
| `config_simple.py` | Minimal / Dict | `load_config`, `list_strategies(config: dict)` — **andere Signatur** |

---

## 3. Öffentliche Facade vs. Paket-Export

### `src/core/config.py` (empfohlene **einzige** Modul-Facade)

- **`load_config`** = **Peak** (TOML).
- **`load_pydantic_config`** = Pydantic-Loader (in `config_pydantic` heißt die Funktion `load_config`).
- Re-exports: `PeakConfig`, `Settings`, `StrategyConfig`, `get_config`, `reset_config`, …

### `src/core/__init__.py`

- Exportiert **Pydantic** `load_config` **und** Alias `load_pydantic_config`.
- Peak: **`load_config as load_peak_config`** (damit weicht die **Namenskonvention** von `config.py` ab: dort heißt der Peak-Loader `load_config`).

**Konsequenz:** Zwei Einstiege (`from src.core import …` vs. `from src.core.config import …`) mit **leicht unterschiedlicher** Bedeutung von `load_config`.

### Registry-Entkopplung im Paket

- `get_config as get_registry_config`
- `list_strategies as list_registry_strategies`

---

## 4. Hotspot-Inventar (Produktion `src/`, ohne Tests/Scripts)

### `config_registry` (Backtest / Daten / Experimente)

- `src/backtest/engine.py` — **zusätzlich** `peak_config` (`PeakConfig`, `load_config`)
- `src/backtest/registry_engine.py`
- `src/backtest/walkforward.py`
- `src/data/kraken.py`, `kraken_pipeline.py`
- `src/experiments/base.py` (lokaler Import)

### Pydantic (`config_pydantic`)

- `src/portfolio/manager.py` — `get_config`, `get_strategy_cfg` via `from ..core.config_pydantic import …` (Slice 1).

**Slice-Stand (Import-Story):** Slice 1 (expliziter Import im PortfolioManager) und Slice 2 (Docstring-/Doctest-Beispiele in `config_pydantic.py` auf explizite Imports) sind umgesetzt. In `src/` gibt es **keine weiteren produktiven** Zeilen mehr vom Muster `from ..core import get_config` / `from src.core import get_config` für die Pydantic-Helfer (Stichprobe `rg`); andere `src.core`-Imports betreffen z. B. `resilience`, Registry, Peak oder eigene APIs.

### `peak_config` (Live, Exchange, Analytics, Risk, Execution, …)

- u. a. `src/sweeps/engine.py`, `src&#47;live&#47;*.py` (mehrere), `src/execution/live_session.py`, `src/exchange/kraken_testnet.py`, `src&#47;analytics&#47;*`, `src/portfolio/config.py`, `src/regime/config.py`, `src/risk_layer/risk_gate.py`, `src/strategies/diagnostics.py`, `src/orders/testnet_executor.py`

### Namens-Kollisionen (bewusst andere Bedeutung)

- `src/strategies/registry.py` — eigene **`list_strategies(verbose=…)`** (nicht `config_pydantic.list_strategies()`).
- `src/execution/fault_injection.py` — eigene **`get_config()`** → `FaultConfig` (kein `src.core`-`get_config`).

---

## 5. Empfohlene „saubere Import-Story“ (richtungsweise)

1. **Neuer Code:** bevorzugt **explizite** Submodule:  
   `from src.core.peak_config import …` **oder** `from src.core.config_pydantic import …` **oder** `from src.core.config_registry import …` — je nach Domäne (Live vs. Backtest-Registry vs. Pydantic).
2. **Oder** konsequent **`src.core.config`** als **einzige** Facade für Namen (`load_peak_config`/`load_pydantic_config` in Doku angleichen mit `__init__.py`).
3. **Nicht** ohne Kontext `from src.core import get_config` — ohne Lesen von `__init__.py` ist unklar, ob Pydantic oder (fälschlich) Registry erwartet wird; aktuell ist es **Pydantic** über `__init__.py`.

---

## 6. Nächste mögliche Arbeitsschritte (außerhalb dieser Notiz)

- ~~Kurz-Doku **ein** empfohlenes Muster pro Use-Case~~ — umgesetzt: [CONFIG_IMPORT_GUIDE.md](../../project_docs/CONFIG_IMPORT_GUIDE.md) (2026-03-29).
- Optional: Deprecation-Warnungen für verwirrende `from src.core import load_config` (Pydantic vs. Peak — nur nach Abstimmung).

---

## Verwandte Dateien

- `src/core/config.py`, `__init__.py`, `peak_config.py`, `config_pydantic.py`, `config_registry.py`, `config_simple.py`
- Beispiel-Hotspots: `src/backtest/engine.py`, `src/portfolio/manager.py`, `src/execution/live_session.py`
