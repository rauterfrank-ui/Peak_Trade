# Live-Overrides Config Integration

> ⚠️ **POLICY-SAFE NOTICE:**  
> This document describes configuration mechanisms and environment detection. It does **not** provide live-enable instructions.  
> All examples use safe defaults. Live mode activation requires formal governance approval.

## Überblick

Die `config&sol;live_overrides&sol;auto.toml (planned)` wird automatisch in die Laufzeit-Konfiguration eingebunden, wenn Peak_Trade in einem **Live-nahen Environment** läuft.

Dies ermöglicht dem **Promotion Loop v0**, Parameter-Anpassungen direkt in die Live-Config zu schreiben, ohne manuell `config.toml` zu editieren.

## Architecture

```
Promotion Loop v0
    ↓ schreibt
config/live_overrides/auto.toml
    ↓ wird geladen von
load_config_with_live_overrides()
    ↓ merged in
PeakConfig (Laufzeit)
```

## Live-nahe Environments

Auto-Overrides werden **nur** angewendet in:

- `environment.mode = "live"`
- `environment.mode = "testnet"`
- `environment.mode = "paper_live"` (falls verwendet)
- `environment.mode = "shadow"` (falls verwendet)
- **ODER** wenn live-enablement flag is set (requires governance approval; not shown here)

In reinen **Paper/Backtest-Environments** werden Overrides **NICHT** angewendet.

## Nutzung

### Standard (Empfohlen)

```python
from src.core.peak_config import load_config_with_live_overrides

# Lädt config.toml + wendet auto.toml an (nur in Live-Environments)
cfg = load_config_with_live_overrides()

# Verwenden
leverage = cfg.get("portfolio.leverage", 1.0)
trigger_delay = cfg.get("strategy.trigger_delay", 10.0)
```

### Mit explizitem Pfad

```python
from src.core.peak_config import load_config_with_live_overrides

# Custom config.toml
cfg = load_config_with_live_overrides("config/my_config.toml")

# Custom auto.toml
from pathlib import Path
cfg = load_config_with_live_overrides(
    "config/my_config.toml",
    auto_overrides_path=Path("config/live_overrides/custom_auto.toml")
)
```

### Force-Apply (für Tests)

```python
from src.core.peak_config import load_config_with_live_overrides

# Wendet Overrides auch in Paper-Environment an (für Tests)
cfg = load_config_with_live_overrides(force_apply_overrides=True)
```

### Ohne Overrides (Original-Verhalten)

```python
from src.core.peak_config import load_config

# Alte Funktion: lädt NUR config.toml (keine auto.toml)
cfg = load_config()
```

## Format: auto.toml

```toml
# config/live_overrides/auto.toml
[auto_applied]
"portfolio.leverage" = 1.75
"strategy.trigger_delay" = 8.0
"macro.regime_weight" = 0.35
"risk.max_position" = 0.15
```

**Wichtig:**
- Keys in **Anführungszeichen** (weil sie Punkte enthalten)
- Dotted-Notation für verschachtelte Pfade
- Nur numerische Werte (int/float) werden vom Promotion Loop geschrieben

## Verschachtelte Pfade

Auto-Overrides unterstützen beliebige Verschachtelungstiefe:

```toml
[auto_applied]
"portfolio.risk.max_position" = 0.15
"strategy.ma_crossover.fast_window" = 12
"live.risk_limits.max_notional" = 10000.0
```

wird zu:

```python
cfg.get("portfolio.risk.max_position")  # -> 0.15
cfg.get("strategy.ma_crossover.fast_window")  # -> 12
cfg.get("live.risk_limits.max_notional")  # -> 10000.0
```

## Migration für bestehenden Code

### Vorher (ohne Live-Overrides)

```python
from src.core.peak_config import load_config

cfg = load_config()
```

### Nachher (mit Live-Overrides)

```python
from src.core.peak_config import load_config_with_live_overrides

# Verhält sich identisch in Paper-Environments
# Wendet auto.toml an in Live-Environments
cfg = load_config_with_live_overrides()
```

**Empfehlung:** Migriere Produktionscode schrittweise zu `load_config_with_live_overrides()`.

## Sicherheits-Features

### 1. Environment-basiertes Gating

Overrides werden **nur** in Live-Environments angewendet:

```python
# Paper-Environment
cfg = load_config_with_live_overrides()
# -> auto.toml wird NICHT angewendet

# Live-Environment
cfg = load_config_with_live_overrides()
# -> auto.toml wird angewendet
```

### 2. Graceful Degradation

Wenn `auto.toml` fehlt oder ungültig ist:
- Keine Exception
- Warning wird geloggt
- Config wird ohne Overrides geladen

```python
# auto.toml existiert nicht
cfg = load_config_with_live_overrides()
# -> funktioniert, nutzt nur config.toml
```

### 3. Explizite Pfade

Kritische Parameter können NICHT versehentlich überschrieben werden.
Nur explizit in `auto.toml` gelistete Keys werden geändert.

## Integration mit Promotion Loop

Der **Promotion Loop v0** schreibt automatisch in `auto.toml`:

```python
# Im Promotion Loop Engine
from src.governance.promotion_loop.engine import apply_proposals_to_live_overrides

apply_proposals_to_live_overrides(
    proposals,
    policy=policy,
    live_override_path=Path("config/live_overrides/auto.toml"),
)
```

Das erzeugt:

```toml
[auto_applied]
"portfolio.leverage" = 1.75
"strategy.trigger_delay" = 8.0
```

Beim nächsten Config-Load (in einem Live-Environment):

```python
cfg = load_config_with_live_overrides()
# -> portfolio.leverage = 1.75
# -> strategy.trigger_delay = 8.0
```

## Workflow: End-to-End

1. **Learning Loop** generiert ConfigPatch-Empfehlungen
2. **Promotion Loop** filtert und bündelt Patches
3. **In bounded_auto Modus:** Promotion Loop schreibt `auto.toml`
4. **Live-Session:** `load_config_with_live_overrides()` lädt Config
5. **Auto-Merge:** Overrides werden automatisch angewendet
6. **Execution:** Live-Trading nutzt angepasste Parameter

## Debugging

### Prüfen ob Overrides angewendet wurden

```python
cfg = load_config_with_live_overrides()

# Original-Wert (aus config.toml)
base_cfg = load_config()
print(f"Base leverage: {base_cfg.get('portfolio.leverage')}")

# Mit Overrides
print(f"Live leverage: {cfg.get('portfolio.leverage')}")

# Sollte in Live-Environment unterschiedlich sein
```

### Console-Output

Wenn Overrides angewendet werden, siehst du:

```
[peak_config] Applying 3 live auto-overrides from config/live_overrides/auto.toml
[peak_config]   portfolio.leverage = 1.75
[peak_config]   strategy.trigger_delay = 8.0
[peak_config]   macro.regime_weight = 0.35
```

### Validation

```python
from pathlib import Path
from src.core.peak_config import _load_live_auto_overrides, _is_live_like_environment

# Prüfe ob auto.toml valide ist
overrides = _load_live_auto_overrides()
print(f"Found {len(overrides)} overrides: {overrides}")

# Prüfe ob Environment als live-like erkannt wird
cfg = load_config()
is_live = _is_live_like_environment(cfg)
print(f"Is live-like environment: {is_live}")
```

## Best Practices

### 1. Verwende load_config_with_live_overrides() in Production

```python
# ✅ Empfohlen für Production
cfg = load_config_with_live_overrides()

# ❌ Nicht empfohlen (keine Auto-Overrides)
cfg = load_config()
```

### 2. Force-Apply nur in Tests

```python
# ✅ OK in Tests
cfg = load_config_with_live_overrides(force_apply_overrides=True)

# ❌ Nicht in Production (umgeht Environment-Gating)
```

### 3. Validiere Overrides vor dem Schreiben

Der Promotion Loop sollte nur valide Werte schreiben:

```python
# Im Promotion Loop
if not (1.0 <= new_leverage <= 2.0):
    reject_override("leverage out of bounds")
```

### 4. Audit Trail

Log alle angewandten Overrides:

```python
cfg = load_config_with_live_overrides()
# Console-Output zeigt alle angewandten Overrides
# Zusätzlich in Live-Logs aufzeichnen
```

## Troubleshooting

### Overrides werden nicht angewendet

**Problem:** `auto.toml` existiert, aber Werte ändern sich nicht

**Lösung:**
1. Prüfe Environment: Ist `environment.mode = "live"` oder `"testnet"`?
2. Prüfe Pfad: Nutzt du `load_config_with_live_overrides()`?
3. Prüfe Keys: Sind die dotted-keys korrekt? (z.B. `"portfolio.leverage"`)

### Invalid TOML Warning

**Problem:** `Failed to load live auto overrides`

**Lösung:**
1. Validiere `auto.toml` Syntax
2. Prüfe dass Keys in Anführungszeichen sind
3. Nutze `toml.loads()` zum Testen

### Verschachtelte Pfade funktionieren nicht

**Problem:** `"portfolio.risk.max_position"` wird nicht angewendet

**Lösung:**
1. Prüfe dass die verschachtelte Struktur in `config.toml` existiert
2. Nutze `cfg.get("portfolio.risk.max_position")` zum Lesen
3. Verwende `with_overrides()` direkt für Tests

## Status

✅ Implementiert (2025-12-11)
✅ Tests vollständig (13/13 grün)
✅ Integration mit Promotion Loop v0
✅ Backward-compatible (alte `load_config()` unverändert)

## Nächste Schritte (Optional)

1. **Audit-Trail erweitern**: Alle Overrides in separatem Log
2. **Notification Integration**: Slack-Alert bei Override-Änderung
3. **Rollback-Mechanismus**: Auto-Revert bei Problemen
4. **Multi-Environment**: Separate auto.toml per Environment
