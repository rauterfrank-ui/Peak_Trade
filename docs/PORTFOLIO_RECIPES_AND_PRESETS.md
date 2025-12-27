# Portfolio Recipes & Presets

## Übersicht

Portfolio Recipes sind **vordefinierte Portfolio-Konfigurationen**, die per Namen geladen werden können. Sie vereinfachen die Verwendung der Research-CLI, indem sie Standard-Settings für Monte-Carlo & Stress-Tests, Gewichte, Top-N-Auswahl und weitere Parameter in einer TOML-Datei bündeln.

**Vorteile:**
- ✅ Wiederverwendbare, versionierte Portfolio-Definitionen
- ✅ Einfache CLI-Nutzung: `--portfolio-preset <name>`
- ✅ CLI-Argumente können Preset-Werte überschreiben
- ✅ Zentrale Verwaltung in `config/portfolio_recipes.toml`

---

## Struktur der TOML-Datei

Die Portfolio-Recipes werden in `config/portfolio_recipes.toml` definiert:

```toml
[portfolio_recipes.rsi_reversion_balanced]
id = "rsi_reversion_balanced"
portfolio_name = "RSI Reversion Balanced v1"
description = "3x RSI-Reversion Top-Konfigurationen mit moderaten Gewichten."

sweep_name = "rsi_reversion_basic"
top_n = 3
weights = [0.4, 0.3, 0.3]

run_montecarlo = true
mc_num_runs = 1000

run_stress_tests = true
stress_scenarios = ["single_crash_bar", "vol_spike"]
stress_severity = 0.2

format = "both"
risk_profile = "moderate"
tags = ["rsi", "reversion", "balanced"]
```

### Wichtige Felder

| Feld | Typ | Beschreibung |
|------|-----|--------------|
| `id` | string | Eindeutige ID des Rezepts (kann identisch zu Tabellen-Key sein) |
| `portfolio_name` | string | Name des Portfolios (wird in Reports verwendet) |
| `description` | string (optional) | Kurze Beschreibung des Rezepts |
| `sweep_name` | string | Name des Sweeps als Basis (z.B. `rsi_reversion_basic`) |
| `top_n` | integer | Anzahl Top-Konfigurationen aus dem Sweep |
| `weights` | array[float] | Liste von Gewichten (Länge muss = `top_n` sein) |
| `run_montecarlo` | boolean | Ob Monte-Carlo-Robustness ausgeführt werden soll |
| `mc_num_runs` | integer (optional) | Anzahl Monte-Carlo-Runs (nur wenn `run_montecarlo = true`) |
| `run_stress_tests` | boolean | Ob Stress-Tests ausgeführt werden sollen |
| `stress_scenarios` | array[string] | Liste von Stress-Szenarien (nur wenn `run_stress_tests = true`) |
| `stress_severity` | float (optional) | Severity für Stress-Tests (0.0-1.0) |
| `format` | string | Output-Format: `"md"`, `"html"` oder `"both"` |
| `risk_profile` | string (optional) | Informatives Risiko-Profil (z.B. "moderate", "aggressive") |
| `tags` | array[string] (optional) | Liste von Tags für Kategorisierung |

### Validierungsregeln

- `top_n` muss > 0 sein
- `weights` muss genau `top_n` Elemente haben
- `weights` müssen nicht-negativ sein (Summe sollte ~1.0 sein)
- `mc_num_runs` darf nur gesetzt sein, wenn `run_montecarlo = true`
- `stress_scenarios` und `stress_severity` dürfen nur gesetzt sein, wenn `run_stress_tests = true`
- `format` muss einer von `"md"`, `"html"`, `"both"` sein
- `stress_severity` muss zwischen 0.0 und 1.0 liegen

---

## Beispiel-Aufrufe

### 1. Standard-Run mit Preset

```bash
python scripts/research_cli.py portfolio \
  --config config/config.toml \
  --portfolio-preset rsi_reversion_balanced
```

**Was passiert:**
- Lädt Rezept `rsi_reversion_balanced` aus `config/portfolio_recipes.toml`
- Verwendet alle Default-Werte aus dem Rezept
- Führt Portfolio-Robustness mit Monte-Carlo (1000 Runs) und Stress-Tests aus

### 2. Preset + Override: Mehr Monte-Carlo-Runs

```bash
python scripts/research_cli.py portfolio \
  --config config/config.toml \
  --portfolio-preset rsi_reversion_balanced \
  --mc-num-runs 2000
```

**Was passiert:**
- Lädt Preset `rsi_reversion_balanced`
- Überschreibt `mc_num_runs` von 1000 (Preset) auf 2000 (CLI)

### 3. Preset + Override: Anderes Output-Format

```bash
python scripts/research_cli.py portfolio \
  --config config/config.toml \
  --portfolio-preset rsi_reversion_balanced \
  --format markdown
```

**Was passiert:**
- Lädt Preset `rsi_reversion_balanced`
- Überschreibt `format` von `"both"` (Preset) auf `"md"` (CLI)

### 4. Preset + Override: Andere Gewichte

```bash
python scripts/research_cli.py portfolio \
  --config config/config.toml \
  --portfolio-preset rsi_reversion_balanced \
  --top-n 5 \
  --weights 0.2 0.2 0.2 0.2 0.2
```

**Was passiert:**
- Lädt Preset `rsi_reversion_balanced`
- Überschreibt `top_n` von 3 (Preset) auf 5 (CLI)
- Überschreibt `weights` von `[0.4, 0.3, 0.3]` (Preset) auf `[0.2, 0.2, 0.2, 0.2, 0.2]` (CLI)

### 5. Custom Recipes-Datei

```bash
python scripts/research_cli.py portfolio \
  --config config/config.toml \
  --recipes-config config/custom_recipes.toml \
  --portfolio-preset my_custom_preset
```

**Was passiert:**
- Lädt Rezepte aus `config/custom_recipes.toml` (statt Default)
- Verwendet Preset `my_custom_preset` aus dieser Datei

---

## Prioritätsregeln: Preset vs. CLI-Argumente

**Grundregel:** CLI-Argumente überschreiben Preset-Werte.

| Parameter | Preset-Wert | CLI-Argument | Ergebnis |
|-----------|-------------|--------------|----------|
| `sweep_name` | `rsi_reversion_basic` | `--sweep-name ma_crossover` | `ma_crossover` (CLI) |
| `top_n` | `3` | `--top-n 5` | `5` (CLI) |
| `weights` | `[0.4, 0.3, 0.3]` | `--weights 0.5 0.5` | `[0.5, 0.5]` (CLI) |
| `run_montecarlo` | `true` | `--run-montecarlo` (explizit) | `true` (CLI) |
| `mc_num_runs` | `1000` | `--mc-num-runs 2000` | `2000` (CLI) |
| `format` | `"both"` | `--format md` | `"md"` (CLI) |

**Wichtig:** Wenn ein CLI-Argument **nicht gesetzt** ist, wird der Preset-Wert verwendet.

---

## Best Practices

### 1. Halte `top_n` + `weights` in Sync

```toml
# ✅ RICHTIG
top_n = 3
weights = [0.4, 0.3, 0.3]  # Länge = 3

# ❌ FALSCH
top_n = 3
weights = [0.5, 0.5]  # Länge = 2, Fehler!
```

### 2. Nutze `risk_profile` und `tags` für Kategorisierung

```toml
[portfolio_recipes.aggressive_momentum]
# ...
risk_profile = "aggressive"
tags = ["momentum", "trend", "high-risk"]

[portfolio_recipes.conservative_reversion]
# ...
risk_profile = "conservative"
tags = ["reversion", "mean-reversion", "low-risk"]
```

### 3. Dokumentiere Rezepte mit `description`

```toml
[portfolio_recipes.rsi_reversion_balanced]
description = "3x RSI-Reversion Top-Konfigurationen mit moderaten Gewichten. \
               Optimiert für Range-Märkte. Verwendet 1000 MC-Runs und moderate Stress-Tests."
```

### 4. Versioniere Rezepte im Namen

```toml
[portfolio_recipes.rsi_reversion_balanced_v1]
portfolio_name = "RSI Reversion Balanced v1"
# ...

[portfolio_recipes.rsi_reversion_balanced_v2]
portfolio_name = "RSI Reversion Balanced v2"
# ... (verbesserte Version)
```

### 5. Nutze Presets für Standard-Workflows

Erstelle Presets für häufig verwendete Kombinationen:

```toml
# Quick-Test: Nur Baseline, keine MC/Stress
[portfolio_recipes.quick_test]
run_montecarlo = false
run_stress_tests = false

# Full-Robustness: Alles aktiviert
[portfolio_recipes.full_robustness]
run_montecarlo = true
mc_num_runs = 2000
run_stress_tests = true
stress_scenarios = ["single_crash_bar", "vol_spike", "drawdown_extension"]
```

---

## Wie man eigene Rezepte hinzufügt

1. **Öffne `config/portfolio_recipes.toml`**

2. **Füge ein neues Rezept hinzu:**

```toml
[portfolio_recipes.my_custom_preset]
id = "my_custom_preset"
portfolio_name = "My Custom Portfolio"
description = "Meine eigene Portfolio-Konfiguration"

sweep_name = "my_sweep"
top_n = 4
weights = [0.3, 0.3, 0.2, 0.2]

run_montecarlo = true
mc_num_runs = 1500

run_stress_tests = true
stress_scenarios = ["single_crash_bar"]
stress_severity = 0.15

format = "both"
```

3. **Validiere das Rezept:**

```bash
# Teste ob das Rezept geladen werden kann
python -c "
from pathlib import Path
from src.experiments.portfolio_recipes import get_portfolio_recipe
recipe = get_portfolio_recipe(Path('config/portfolio_recipes.toml'), 'my_custom_preset')
print(f'✅ Rezept geladen: {recipe.portfolio_name}')
"
```

4. **Verwende das Rezept:**

```bash
python scripts/research_cli.py portfolio \
  --config config/config.toml \
  --portfolio-preset my_custom_preset
```

---

## Integration in Python-Code

### Rezepte programmatisch laden

```python
from pathlib import Path
from src.experiments.portfolio_recipes import (
    load_portfolio_recipes,
    get_portfolio_recipe,
)

# Alle Rezepte laden
recipes = load_portfolio_recipes(Path("config/portfolio_recipes.toml"))
print(f"Geladen: {len(recipes)} Rezepte")

# Einzelnes Rezept laden
recipe = get_portfolio_recipe(
    Path("config/portfolio_recipes.toml"),
    "rsi_reversion_balanced"
)

print(f"Portfolio: {recipe.portfolio_name}")
print(f"Sweep: {recipe.sweep_name}")
print(f"Top-N: {recipe.top_n}")
print(f"Weights: {recipe.weights}")
```

### Validierung

```python
from src.experiments.portfolio_recipes import PortfolioRecipe

recipe = PortfolioRecipe(
    key="test",
    id="test",
    portfolio_name="Test",
    description=None,
    sweep_name="test_sweep",
    top_n=3,
    weights=[0.4, 0.3, 0.3],
)

# Validiere
try:
    recipe.validate()
    print("✅ Rezept ist gültig")
except ValueError as e:
    print(f"❌ Validierungsfehler: {e}")
```

---

## Fehlerbehandlung

### Rezept nicht gefunden

```bash
$ python scripts/research_cli.py portfolio \
    --config config/config.toml \
    --portfolio-preset nonexistent

ERROR: Portfolio recipe 'nonexistent' not found in config/portfolio_recipes.toml.
       Available recipes: rsi_reversion_balanced, ma_crossover_equal
```

### Validierungsfehler

```bash
$ python scripts/research_cli.py portfolio \
    --config config/config.toml \
    --portfolio-preset invalid_recipe

ERROR: weights length (2) must match top_n (3) for recipe 'invalid_recipe'
```

### Datei nicht gefunden

```bash
$ python scripts/research_cli.py portfolio \
    --config config/config.toml \
    --recipes-config missing.toml \
    --portfolio-preset test

ERROR: Recipes-Config-Datei nicht gefunden: missing.toml
```

---

## Siehe auch

- `docs/CLI_CHEATSHEET.md` - CLI-Referenz
- `docs/PHASE_47_PORTFOLIO_ROBUSTNESS_AND_STRESS_TESTING.md` - Portfolio-Robustness-Dokumentation
- `config/portfolio_recipes.toml` - Rezept-Definitionen
- `src/experiments/portfolio_recipes.py` - Python-API

---

## Phase 53: Risk-Profile & Direkte Strategienamen

**Phase 53** erweitert die Portfolio-Recipes um:

1. **Direkte Strategienamen** (statt Sweep-basiert)
2. **Explizite Risk-Profile** (`conservative`, `moderate`, `aggressive`)
3. **Neue Rezepte** für verschiedene Risk-Profile

### Risk-Profile

Die drei Risk-Profile haben folgende Bedeutung:

| Profil      | Beschreibung                                                                 | Parameter-Charakteristik                                    |
| ----------- | --------------------------------------------------------------------------- | ----------------------------------------------------------- |
| `conservative` | Geringere Volatilität, breitere Stops, niedrigere Leverage/Position-Size | Längere Lookbacks, breitere Stops, niedrigere Trade-Frequenz |
| `moderate`  | "Balanced" – guter Kompromiss aus Return & Drawdown                        | Ausgewogene Parameter, moderate Trade-Frequenz              |
| `aggressive` | Höhere Volatilität, kürzere Lookbacks, mehr Trade-Frequenz                | Kürzere Lookbacks, engere Stops, höhere Trade-Frequenz     |

### Neue Rezepte (Phase 53)

| Preset                       | Typ          | Assets   | Style(s)                        | Risk-Profil  | Kommentar                             |
| ---------------------------- | ------------ | -------- | ------------------------------- | ------------ | ------------------------------------- |
| `rsi_reversion_conservative` | Single-Style | BTC, ETH | RSI-Reversion                   | conservative | Längere Lookbacks, 1h TF              |
| `rsi_reversion_moderate`     | Single-Style | BTC, ETH | RSI-Reversion                   | moderate     | Balanced 1h TF                        |
| `rsi_reversion_aggressive`   | Single-Style | BTC, ETH | RSI-Reversion                   | aggressive   | 15m TF, höhere Trade-Frequenz         |
| `multi_style_moderate`       | Multi-Style  | BTC, ETH | Trend-Following + MeanReversion | moderate     | 4 Strategien, alle gleich gewichtet   |
| `multi_style_aggressive`     | Multi-Style  | BTC, ETH | Trend-Following + MeanReversion | aggressive   | Aggressive Varianten der 4 Strategien |

### Beispiel-Workflows (Phase 53)

#### 1. Research-Portfolio-Pipeline – moderate Multi-Style

```bash
# 1) Run Portfolio-Research mit Preset
python scripts/research_cli.py portfolio \
  --config config/config.toml \
  --portfolio-preset multi_style_moderate \
  --format both

# 2) Portfolio-Robustness explizit
python scripts/run_portfolio_robustness.py \
  --config config/config.toml \
  --portfolio-preset multi_style_moderate \
  --format both
```

#### 2. Research-Portfolio – aggressive Multi-Style

```bash
python scripts/research_cli.py portfolio \
  --config config/config.toml \
  --portfolio-preset multi_style_aggressive \
  --format both
```

#### 3. Conservative RSI-Reversion

```bash
python scripts/run_portfolio_robustness.py \
  --config config/config.toml \
  --portfolio-preset rsi_reversion_conservative \
  --format both
```

### Rezepte mit direkten Strategienamen (Phase 53)

Ab Phase 53 können Rezepte **direkte Strategienamen** verwenden statt Sweep-basiert zu sein:

```toml
[portfolio_recipes.rsi_reversion_conservative]
id = "rsi_reversion_conservative"
portfolio_name = "RSI Reversion Conservative"
description = "Konservatives RSI-Reversion-Portfolio auf BTC und ETH"

# Direkte Strategienamen (statt sweep_name + top_n)
strategies = [
  "rsi_reversion_btc_conservative",
  "rsi_reversion_eth_conservative",
]
weights = [0.6, 0.4]

run_montecarlo = true
mc_num_runs = 2000

run_stress_tests = true
stress_scenarios = ["single_crash_bar", "vol_spike"]
stress_severity = 0.2

format = "both"
risk_profile = "conservative"
tags = ["rsi", "reversion", "conservative"]
```

**Wichtig:**
- Entweder `strategies` (Phase 53) **oder** `sweep_name` + `top_n` (Legacy) muss gesetzt sein
- `weights` Länge muss mit `len(strategies)` übereinstimmen
- `risk_profile` sollte eines von `conservative`, `moderate`, `aggressive` sein

### Strategy-Konfigurationen (Phase 53)

Phase 53 fügt neue Strategy-Konfigurationen in `config/config.toml` hinzu:

- **RSI-Reversion**: `rsi_reversion_btc_conservative`, `rsi_reversion_btc_moderate`, `rsi_reversion_btc_aggressive`, etc.
- **MA-Crossover**: `ma_trend_btc_conservative`, `ma_trend_btc_moderate`, `ma_trend_btc_aggressive`
- **Trend-Following**: `trend_following_eth_conservative`, `trend_following_eth_moderate`, `trend_following_eth_aggressive`

Diese Konfigurationen folgen dem Naming-Schema: `<family>_<market>_<profile>`.

Siehe auch: `docs/PHASE_53_STRATEGY_AND_PORTFOLIO_LIBRARY_PUSH.md` (falls vorhanden)

### End-to-End-Prozess zur Portfolio-Aktivierung

Für einen empfohlenen End-to-End-Prozess zur Bewertung und Aktivierung von Portfolio-Recipes siehe [`PLAYBOOK_RESEARCH_TO_LIVE_PORTFOLIOS.md`](PLAYBOOK_RESEARCH_TO_LIVE_PORTFOLIOS.md) (Phase 54).

Dieses Playbook beschreibt:
- Wie Portfolio-Presets durch die Research-Pipeline v2 geschickt werden
- Go/No-Go-Kriterien basierend auf Metriken
- Mapping von Research-Konfigurationen auf Live-/Testnet-Setups
- Shadow-/Testnet-/Live-Aktivierung mit Checklisten & Runbooks
- Laufendes Monitoring & Re-Kalibrierung

---

**Built with ❤️ and reusable configurations**
