# Developer Guide: Neues Portfolio-Rezept hinzufügen

## Ziel

Neues Portfolio-Rezept in `config/portfolio_recipes.toml` definieren und über Research-CLI nutzbar machen.

---

## Relevante Komponenten

- `config/portfolio_recipes.toml` – Rezept-Definitionen
- `src/experiments/portfolio_recipes.py` – Portfolio-Rezepte-Loader
- `scripts/research_cli.py` – Research-CLI (Portfolio-Subcommand)
- Doku: `PORTFOLIO_RECIPES_AND_PRESETS.md`, `PHASE_47_*`

---

## Workflow

### 1. Recipe-Definition im TOML

**In `config/portfolio_recipes.toml`:**

```toml
[portfolio_recipes.my_new_recipe]
id = "my_new_recipe"
portfolio_name = "My New Recipe v1"
description = "Kurze Beschreibung des Rezepts (z.B. konservatives RSI-Portfolio auf BTC/ETH)"

# Basis-Sweep (optional)
sweep_name = "rsi_reversion_basic"  # Name des Sweeps als Basis
top_n = 3  # Anzahl Top-Konfigurationen aus Sweep
weights = [0.4, 0.3, 0.3]  # Gewichte für Top-N (Summe sollte 1.0 sein)

# Oder: Direkte Strategie-Liste (ohne Sweep)
strategies = ["rsi_reversion_basic_btc", "rsi_reversion_basic_eth"]
weights = [0.6, 0.4]

# Monte-Carlo-Simulation
run_montecarlo = true
mc_num_runs = 2000

# Stress-Tests
run_stress_tests = true
stress_scenarios = ["single_crash_bar", "vol_spike"]
stress_severity = 0.2

# Reporting
format = "both"  # "text", "json", oder "both"
risk_profile = "moderate"  # "conservative", "moderate", "aggressive"
tags = ["rsi", "reversion", "balanced"]
```

**Wichtig:**
- `id` muss eindeutig sein
- `weights` müssen auf 1.0 summieren (wird in Tests validiert)
- `strategies` müssen in Registry existieren (wird in Tests validiert)

---

### 2. Validierung

**Tests prüfen automatisch:**

- Summe der Gewichte = 1.0
- Alle Strategien existieren in Registry
- Alle Sweeps existieren (falls `sweep_name` verwendet wird)

**Manuelle Validierung:**

```python
from src.experiments.portfolio_recipes import load_portfolio_recipes, get_portfolio_recipe
from pathlib import Path

# Alle Rezepte laden
recipes = load_portfolio_recipes(Path("config/portfolio_recipes.toml"))

# Einzelnes Rezept laden
recipe = get_portfolio_recipe(Path("config/portfolio_recipes.toml"), "my_new_recipe")

# Prüfen
assert recipe is not None
assert sum(recipe.weights) == 1.0
```

**Siehe:** `tests/test_portfolio_recipes.py` für Validierungs-Tests

---

### 3. Research-CLI-Nutzung

**Portfolio-Rezept ausführen:**

```bash
python scripts/research_cli.py portfolio \
  --config config/config.toml \
  --portfolio-preset my_new_recipe
```

**Mit zusätzlichen Optionen:**

```bash
python scripts/research_cli.py portfolio \
  --config config/config.toml \
  --portfolio-preset my_new_recipe \
  --format json \
  --output-dir reports/portfolio/my_new_recipe
```

**Ohne Preset (manuelle Konfiguration):**

```bash
python scripts/research_cli.py portfolio \
  --config config/config.toml \
  --strategies rsi_reversion_basic_btc,rsi_reversion_basic_eth \
  --weights 0.6,0.4
```

---

### 4. Tests

**Optional: Erweiterung von `tests/test_research_cli_portfolio_presets.py`:**

```python
"""
Tests für Portfolio-Presets
"""
from __future__ import annotations

import pytest
from pathlib import Path

from src.experiments.portfolio_recipes import get_portfolio_recipe


def test_my_new_recipe_loads():
    """Testet dass my_new_recipe korrekt geladen wird."""
    recipe = get_portfolio_recipe(
        Path("config/portfolio_recipes.toml"),
        "my_new_recipe"
    )

    assert recipe is not None
    assert recipe.id == "my_new_recipe"
    assert recipe.portfolio_name == "My New Recipe v1"
    assert len(recipe.weights) == len(recipe.strategies)
    assert abs(sum(recipe.weights) - 1.0) < 0.001  # Toleranz für Float


def test_my_new_recipe_weights_sum_to_one():
    """Testet dass Gewichte auf 1.0 summieren."""
    recipe = get_portfolio_recipe(
        Path("config/portfolio_recipes.toml"),
        "my_new_recipe"
    )

    assert abs(sum(recipe.weights) - 1.0) < 0.001
```

---

## Best Practices

### ✅ DO

- **Sprechende Namen**: Rezept-Namen sollten Strategy-Type & Risk-Level enthalten
  - Beispiel: `rsi_reversion_conservative`, `momentum_aggressive_btc_eth`
- **Klare Beschreibung**: `description` sollte kurz erklären, wann das Rezept sinnvoll ist
- **Tags**: Verwende Tags für Kategorisierung (`rsi`, `reversion`, `conservative`, etc.)
- **Dokumentation**: Erweitere `PORTFOLIO_RECIPES_AND_PRESETS.md` um 1–2 Sätze zum Rezept

### ❌ DON'T

- **Keine Hardcoded-Symbole**: Rezepte sollten für verschiedene Symbole funktionieren (falls möglich)
- **Keine zu komplexen Rezepte**: Halte Rezepte einfach und nachvollziehbar
- **Keine Duplikate**: Prüfe, ob ähnliche Rezepte bereits existieren

---

## Beispiel-Rezepte als Referenz

**In `config/portfolio_recipes.toml`:**

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

**Siehe:** `config/portfolio_recipes.toml` für weitere Beispiele

---

## Dokumentation

**In `PORTFOLIO_RECIPES_AND_PRESETS.md`:**

Füge eine kurze Beschreibung des neuen Rezepts hinzu:

```markdown
## My New Recipe

**Beschreibung:** Kurze Beschreibung (z.B. konservatives RSI-Portfolio auf BTC/ETH)

**Verwendung:** Wann ist dieses Rezept sinnvoll?
- Volatilität: Niedrig bis mittel
- Zeithorizont: Kurz- bis mittelfristig
- Märkte: BTC, ETH

**Beispiel:**
```bash
python scripts/research_cli.py portfolio \
  --portfolio-preset my_new_recipe
```
```

---

## Troubleshooting

**Problem:** Rezept wird nicht gefunden
- **Lösung:** Prüfe, ob `id` korrekt ist und Rezept in `portfolio_recipes.toml` existiert

**Problem:** Gewichte summieren nicht auf 1.0
- **Lösung:** Prüfe, ob alle Gewichte korrekt sind (Summe sollte 1.0 sein)

**Problem:** Strategien existieren nicht
- **Lösung:** Prüfe, ob alle Strategien in Registry registriert sind

**Problem:** Sweep existiert nicht
- **Lösung:** Prüfe, ob `sweep_name` korrekt ist und Sweep existiert

---

## Siehe auch

- `ARCHITECTURE_OVERVIEW.md` – Architektur-Übersicht
- `config/portfolio_recipes.toml` – Rezept-Definitionen
- `src/experiments/portfolio_recipes.py` – Portfolio-Rezepte-Loader
- `docs/PORTFOLIO_RECIPES_AND_PRESETS.md` – Portfolio-Rezepte-Doku
- `docs/PHASE_47_*.md` – Portfolio-Robustness
- `scripts/research_cli.py` – Research-CLI
















