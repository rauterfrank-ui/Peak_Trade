# 🚀 Peak_Trade Strategien-Registry - Installation & Quick Start

## ✅ Status: Dateien erfolgreich installiert!

Die folgenden Dateien wurden in dein Projekt kopiert:

```
Peak_Trade/
├── README_REGISTRY.md                    # ← Diese Datei (Quick Start)
├── docs/CONFIG_REGISTRY_USAGE.md         # ✅ Vollständige Dokumentation
├── scripts/demo_config_registry.py       # ✅ Demo-Script
└── src/core/config_registry.py           # ✅ Registry-Modul
```

---

## 🎯 Was ist die Strategien-Registry?

Die Registry erweitert dein Peak_Trade-Framework um:

1. ✅ **Zentrale Verwaltung** aller Strategien in `config.toml`
2. ✅ **Active/Available-Listen** für dynamisches Portfolio-Management
3. ✅ **Default-Parameter** mit Override-Logik
4. ✅ **Metadata** für intelligente Strategie-Selektion
5. ✅ **Marktregime-Filtering** (trending/ranging/any)

---

## 🚀 Quick Start (3 Schritte)

### Schritt 1: Demo testen

```bash
cd ~/Peak_Trade
python scripts/demo_config_registry.py
```

**Erwartete Ausgabe:**
```
🎯 3 aktive Strategien:
   1. ma_crossover
   2. momentum_1h
   3. rsi_strategy

✅ ma_crossover: stop=2.0%
✅ momentum_1h: stop=2.5%
✅ rsi_strategy: stop=2.0%
```

---

### Schritt 2: In deinem Code nutzen

```python
from src.core.config_registry import (
    get_active_strategies,
    get_strategy_config
)

# Alle aktiven Strategien durchgehen
for name in get_active_strategies():
    cfg = get_strategy_config(name)

    # Zugriff auf Parameter (mit Fallback auf Defaults)
    print(f"{name}:")
    print(f"  Stop: {cfg.get('stop_pct'):.1%}")
    print(f"  Take-Profit: {cfg.get('take_profit_pct'):.1%}")
    print(f"  Position: {cfg.get('position_fraction'):.0%}")

    # Alle Parameter als Dict
    all_params = cfg.to_dict()
```

---

### Schritt 3: Config anpassen

Editiere `config/config.toml` und ändere die Active-Liste:

```toml
[strategies]
active = ["ma_crossover", "momentum_1h"]  # ← Nur diese 2 aktiv
available = ["ma_crossover", "momentum_1h", "rsi_strategy", ...]

[strategies.defaults]
stop_pct = 0.02              # Standard Stop-Loss 2%
take_profit_pct = 0.05       # Standard Take-Profit 5%
position_fraction = 0.25     # 25% des Kapitals pro Trade
```

---

## 📚 Vollständige Dokumentation

Siehe **`docs/CONFIG_REGISTRY_USAGE.md`** für:

- ✅ Vollständige API-Referenz
- ✅ Advanced Use Cases (Regime-Filtering, Portfolio-Rebalancing)
- ✅ Best Practices (Peak_Risk-Empfehlungen)
- ✅ Troubleshooting-Guide

---

## 🎯 Beispiel: Backtest-Integration

```python
from src.core.config_registry import get_active_strategies, get_strategy_config
from src.backtest import BacktestEngine

engine = BacktestEngine(initial_cash=10000)

# Dynamisch alle aktiven Strategien backtesten
for name in get_active_strategies():
    cfg = get_strategy_config(name)

    # Strategie mit merged Config erstellen
    strategy = create_strategy(name, **cfg.to_dict())

    # Backtest durchführen
    results = engine.run(strategy, data)
    print(f"✅ {name}: Sharpe={results.sharpe:.2f}")
```

**Vorteil:** Strategien in `config.toml` aktivieren/deaktivieren, ohne Code zu ändern!

---

## 🔧 Git-Integration

Committe die neuen Dateien:

```bash
git add README_REGISTRY.md \
        docs/CONFIG_REGISTRY_USAGE.md \
        scripts/demo_config_registry.py \
        src/core/config_registry.py \
        config/config.toml

git commit -m "feat: Add Strategien-Registry with metadata & regime filtering

- Zentrale Verwaltung aller Strategien in config.toml
- Active/Available-Listen für Portfolio-Management
- Default-Parameter mit Override-Logik
- Metadata für intelligente Strategie-Selektion
- Marktregime-Filtering (trending/ranging/any)
- Vollständige Dokumentation & Demo-Script"
```

---

## 📊 Nächste Schritte

Nach dem Quick Start:

1. ✅ **Teste die Registry** mit Demo-Script
2. ✅ **Passe Backtest-Skripte an** (siehe Beispiel oben)
3. ✅ **Erweitere Metadata** in `config.toml` (optional)
4. ✅ **Implementiere Regime-Detection** (siehe Usage Guide)
5. ✅ **Schreibe Unit-Tests** für deine Strategien

---

## 🚨 Als Peak_Risk: Wichtige Warnungen

### ⚠️ Config-Inkonsistenz gefunden!

Deine aktuelle `config.toml` hat:

```toml
[risk]
max_positions = 2           # Max. 2 parallele Positionen
max_position_size = 0.25    # Max. 25% pro Position
max_total_exposure = 0.75   # Max. 75% Gesamt-Exposure

[strategies]
active = ["ma_crossover", "momentum_1h", "rsi_strategy"]  # 3 Strategien!
```

**Problem:** 3 aktive Strategien × 25% = 75%, ABER `max_positions = 2` limitiert auf nur 2!

**Lösung Option A (konservativ):**
```toml
[risk]
max_positions = 2
max_total_exposure = 0.50   # 2 × 0.25 = 0.50 (konsistent!)

[strategies]
active = ["ma_crossover", "momentum_1h"]  # Nur 2 aktiv
```

**Lösung Option B (aggressiv):**
```toml
[risk]
max_positions = 3           # Erlaubt 3 parallele Positionen
max_total_exposure = 0.75   # 3 × 0.25 = 0.75 (konsistent!)
```

**Empfehlung:** Option A (konservativer!)

---

## 🎯 Quick Reference

```python
# Strategien laden
from src.core.config_registry import (
    get_active_strategies,      # → ["ma_crossover", ...]
    get_strategy_config,        # → StrategyConfig-Objekt
    list_strategies,            # → Alle definierten Strategien
    get_strategies_by_regime,   # → Filtering nach Marktregime
)

# Config-Objekt
cfg = get_strategy_config("ma_crossover")
cfg.name                    # → "ma_crossover"
cfg.active                  # → True/False
cfg.params                  # → Strategie-spezifische Parameter
cfg.defaults                # → Default-Parameter
cfg.metadata                # → Optional Metadata-Dict
cfg.get("stop_pct")         # → Parameter mit Fallback
cfg.to_dict()               # → Merged Dict
```

---

## 🔗 Weitere Ressourcen

- **docs/CONFIG_REGISTRY_USAGE.md** - API-Referenz & Examples
- **Peak_Trade_OVERVIEW.md** - Projekt-Übersicht
- **Peak_Trade_Data_Layer_Doku.md** - Data-Layer

---

**Stand:** Dezember 2024  
**Autor:** Peak_Trade Core Team 🚀
