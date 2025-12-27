# Quickstart: Live-Overrides Integration

## 🎯 Was ist das?

Die **Live-Overrides-Integration** ermöglicht es dem **Promotion Loop v0**, Parameter-Anpassungen automatisch in die Live-Konfiguration einzuspielen, ohne dass du manuell `config.toml` editieren musst.

## 🚀 In 3 Schritten starten

### 1. Config-Loader anpassen

**Vorher:**
```python
from src.core.peak_config import load_config

cfg = load_config()
```

**Nachher:**
```python
from src.core.peak_config import load_config_with_live_overrides

cfg = load_config_with_live_overrides()
```

Das war's! In **Paper-Environments** verhält sich die Funktion identisch zu `load_config()`. In **Live-Environments** werden automatisch die Overrides aus `config&sol;live_overrides&sol;auto.toml (planned)` angewendet.

### 2. Promotion Loop konfigurieren

```bash
# bounded_auto Modus: Schreibt automatisch in auto.toml
python3 scripts/run_promotion_proposal_cycle.py --auto-apply-mode bounded_auto
```

Dies erzeugt/aktualisiert `config&sol;live_overrides&sol;auto.toml (planned)`:

```toml
[auto_applied]
"portfolio.leverage" = 1.75
"strategy.trigger_delay" = 8.0
"macro.regime_weight" = 0.35
```

### 3. Live-Session starten

```python
from src.core.peak_config import load_config_with_live_overrides

# Lädt config.toml + wendet auto.toml an (nur in Live/Testnet)
cfg = load_config_with_live_overrides()

# Die Werte sind jetzt automatisch überschrieben
print(cfg.get("portfolio.leverage"))  # -> 1.75 (statt 1.0)
print(cfg.get("strategy.trigger_delay"))  # -> 8.0 (statt 10.0)
```

## ✅ Was ist geschützt?

### Environment-basiertes Gating

```python
# Paper-Environment
cfg = load_config_with_live_overrides()
# -> auto.toml wird NICHT angewendet ✓

# Live/Testnet-Environment
cfg = load_config_with_live_overrides()
# -> auto.toml wird angewendet ✓
```

### Graceful Degradation

- Fehlende `auto.toml`? ✓ Kein Problem
- Ungültiges TOML? ✓ Warning, Config lädt trotzdem
- Nicht-existierender Pfad? ✓ Override wird ignoriert

### Bounded Auto-Apply (Promotion Loop)

Der Promotion Loop schreibt **nur** Werte innerhalb vordefinierter Bounds:

```python
# Im Promotion Loop definiert
leverage_bounds = AutoApplyBounds(
    min_value=1.0,
    max_value=2.0,
    max_step=0.25
)
```

Werte außerhalb dieser Grenzen werden automatisch abgelehnt.

## 📊 Demo & Tests

### Demo-Script

```bash
# Paper-Environment (keine Overrides)
python3 scripts/demo_live_overrides.py

# Mit Force-Apply (auch in Paper)
python3 scripts/demo_live_overrides.py --force
```

### Tests laufen lassen

```bash
# Basis-Tests
pytest tests/test_live_overrides_integration.py -v

# Realistische Szenarien
pytest tests/test_live_overrides_realistic_scenario.py -v

# Alle Override-Tests
pytest tests/test_live_overrides*.py -v
```

## 🔧 Erweiterte Nutzung

### Custom Pfade

```python
from pathlib import Path
from src.core.peak_config import load_config_with_live_overrides

cfg = load_config_with_live_overrides(
    path="config/my_config.toml",
    auto_overrides_path=Path("config/live_overrides/custom.toml")
)
```

### Force-Apply (für Tests)

```python
# Wendet Overrides auch in Paper an (nur für Tests!)
cfg = load_config_with_live_overrides(force_apply_overrides=True)
```

### Debug: Prüfen ob Overrides angewendet wurden

```python
from src.core.peak_config import (
    load_config,
    load_config_with_live_overrides,
    _load_live_auto_overrides,
    _is_live_like_environment,
)

# 1. Prüfe ob Environment als live-like erkannt wird
base_cfg = load_config()
is_live = _is_live_like_environment(base_cfg)
print(f"Is live-like: {is_live}")

# 2. Prüfe welche Overrides existieren
overrides = _load_live_auto_overrides()
print(f"Active overrides: {overrides}")

# 3. Vergleiche Werte
base_val = base_cfg.get("portfolio.leverage")
live_cfg = load_config_with_live_overrides()
live_val = live_cfg.get("portfolio.leverage")
print(f"Base: {base_val}, Live: {live_val}")
```

## 🎓 Best Practices

### ✅ Do's

- ✅ Nutze `load_config_with_live_overrides()` in Production-Code
- ✅ Verwende `bounded_auto` Modus im Promotion Loop
- ✅ Validiere Bounds im Promotion Loop vor dem Schreiben
- ✅ Logge alle angewandten Overrides für Audit-Trail
- ✅ Teste mit `force_apply_overrides=True` in Unittests

### ❌ Don'ts

- ❌ Nicht `force_apply_overrides=True` in Production
- ❌ Nicht manuell `auto.toml` editieren (nur via Promotion Loop)
- ❌ Nicht sensible Keys ohne Bounds freigeben
- ❌ Nicht R&D-Strategien über Auto-Overrides promoten

## 📖 Weiterführende Dokumentation

- **[LIVE_OVERRIDES_CONFIG_INTEGRATION.md](./LIVE_OVERRIDES_CONFIG_INTEGRATION.md)** - Vollständige technische Dokumentation
- **[PROMOTION_LOOP_V0.md](./PROMOTION_LOOP_V0.md)** - Promotion Loop Architektur
- **Tests:** `tests/test_live_overrides_*.py` - Beispiel-Code

## 🐛 Troubleshooting

### Problem: Overrides werden nicht angewendet

**Lösung:**
```python
# 1. Prüfe Environment
cfg = load_config()
print(cfg.get("environment.mode"))  # Sollte "live" oder "testnet" sein

# 2. Prüfe ob auto.toml existiert
from pathlib import Path
auto_path = Path("config/live_overrides/auto.toml")
print(auto_path.exists())  # Sollte True sein

# 3. Prüfe ob du die richtige Funktion nutzt
# ❌ Falsch
cfg = load_config()

# ✅ Richtig
cfg = load_config_with_live_overrides()
```

### Problem: Warning "Failed to load live auto overrides"

**Lösung:**
```bash
# Prüfe TOML-Syntax
python3 -c "import toml; print(toml.load('config/live_overrides/auto.toml'))"

# Häufiger Fehler: Keys ohne Anführungszeichen
# ❌ Falsch
[auto_applied]
portfolio.leverage = 1.75

# ✅ Richtig
[auto_applied]
"portfolio.leverage" = 1.75
```

### Problem: Wert wird nicht überschrieben

**Lösung:**
```python
# Prüfe ob der Pfad in der Basis-Config existiert
cfg = load_config()
print(cfg.get("portfolio.leverage"))  # Wenn None: Pfad existiert nicht

# Prüfe ob der Key in auto.toml korrekt ist
from src.core.peak_config import _load_live_auto_overrides
overrides = _load_live_auto_overrides()
print(overrides)  # Sollte deinen Key enthalten
```

## 🎉 Das war's!

Du bist jetzt bereit, Live-Overrides zu nutzen. Bei Fragen siehe:
- Dokumentation oben
- Tests als Beispiele
- Demo-Script: `scripts&sol;demo_live_overrides.py (planned)`

Happy Trading! 🚀
