# PR #551 — fix(pr-531): restore green CI (normalize research markers/IDs)

- **PR:** #551 (fix/pr-531-test-failures) — squash-merged via Auto-Merge
- **Merge Commit:** `8e2b888`
- **Merge Date:** 2026-01-04
- **Branch:** `fix/pr-531-test-failures` → `main`
- **Betreff:** Restore green CI for PR #531 test failures; normalize research strategy markers/IDs; align tests

---

## Summary

PR #551 wurde per Auto-Merge (Squash) in `main` integriert und stellt **grüne CI** wieder her, nachdem PR #531 durch inkonsistente Research-Strategie-Kontrakte (Marker/IDs/Typen) sowie ein Armstrong-Diagnostik-Edgecase Test-Failures erzeugt hatte.

**Scope:** 10 Dateien geändert, +301/-14 Zeilen (primär Dokumentation: `PR531_FIX_REPORT.md`)

---

## Why

- CI musste wieder grün werden, ohne inhaltlich „Live"-Pfad zu berühren.
- Research-only Strategien sollten konsistent markiert und über die Registry rückwärtskompatibel referenzierbar sein.
- Tests mussten den kanonischen Kontrakten (IDs/Marker/Typen) folgen.

---

## Changes

### Armstrong (Research-only)

- Entfernte redundanten/duplizierten Dictionary-Key `cycle_phase` im Cycle-Model (`src/strategies/armstrong/cycle_model.py`)
- Test-Fix: nutze **`cycle_position` (numerisch)** statt `cycle_phase` (String) in Assertions, um Typ-Inkonsistenzen zu vermeiden
- Normalisierung des Research-Markers auf **`RESEARCH-ONLY`** (statt `R&D-ONLY`)
- Repr-Marker aktualisiert in `armstrong_cycle_strategy.py`

### El Karoui (Research-only)

- Ruff-Formatierung von `vol_model.py`
- Kanonisierung der Strategy-ID auf **`el_karoui_vol_model`** (canonical)
- Registry-Alias **`el_karoui_vol_v1`** hinzugefügt für Backward Compatibility
- VolRegime.MEDIUM enum value normalisiert: `"medium"` → `"normal"`
- Normalisierung des Research-Markers auf **`RESEARCH-ONLY`**

### Registry / Backward Compatibility

**Datei:** `src/strategies/registry.py`

Neuer Registry-Eintrag für Backward Compatibility:
```python
"el_karoui_vol_v1": StrategySpec(
    key="el_karoui_vol_v1",
    cls=ElKarouiVolModelStrategy,
    config_section="strategy.el_karoui_vol_model",
    description="El Karoui Vol Model (Alias für el_karoui_vol_model, R&D-Only)",
    is_live_ready=True,
    tier="production",
    allowed_environments=("backtest", "paper", "live"),
)
```

### Tests / Contracts

**Geänderte Test-Dateien:**
1. `tests/strategies/armstrong/test_armstrong_cycle_strategy.py`
   - Marker: `R&D-ONLY` → `RESEARCH-ONLY`
2. `tests/strategies/el_karoui/test_el_karoui_volatility_strategy.py`
   - Marker: `R&D-ONLY` → `RESEARCH-ONLY`
   - Strategy-ID: `el_karoui_vol_v1` → `el_karoui_vol_model`
3. `tests/strategies/el_karoui/test_vol_model.py`
   - VolRegime enum: `"medium"` → `"normal"` (2 Stellen)
   - Valid values Set: `{"low", "medium", "high"}` → `{"low", "normal", "high"}`
4. `tests/test_research_strategies.py`
   - Armstrong cycle info test: `info["cycle_phase"]` → `info["cycle_position"]` (numerischer Wert)

---

## Verification

### CI Status (All Green ✅)

**GitHub Actions Required Checks:** 15/15 erfolgreich

- ✅ **Python Test-Matrix:** 3.9 (4m2s) / 3.10 (3m57s) / 3.11 (7m7s)
- ✅ **Lint Gate (Always Run):** 8s
- ✅ **Lint:** 10s
- ✅ **Test Health Automation:** 1m5s (inkl. Pytest Strategies Smoke)
- ✅ **Audit:** 56s
- ✅ **CI Strategy-Smoke:** 1m12s
- ✅ **Quarto Smoke Test:** 24s
- ✅ **Policy Critic Gate:** 6s
- ✅ **Policy Guard - No Tracked Reports:** 5s
- ✅ **Docs Diff Guard Policy Gate:** 8s
- ✅ **Docs Reference Targets Gate:** 6s
- ✅ **CI/changes:** 5s
- ✅ **CI/ci-required-contexts-contract:** 6s

**Auto-Merge:** Erfolgreich getriggert und durchgeführt (Squash-Merge)

### Local Smoke Test

```bash
# Research strategies
pytest -q tests/strategies/armstrong/ tests/strategies/el_karoui/
# Expected: 164 passed

# Research strategies integration
pytest -q tests/test_research_strategies.py
# Expected: 33 passed
```

---

## Risk

**Niedrig bis moderat.**

- ✅ **Safe:** Änderungen betreffen primär **Research-only** Strategy Contracts und deren Tests/Registry-Aliases
- ✅ **Safe:** Keine Live-Execution-Pfade geändert
- ⚠️ **Moderate Risk:** Potenzielle Downstream-Abhängigkeiten, die noch auf alte Marker/IDs/Labels referenzieren:
  - Code, der explizit nach `"R&D-ONLY"` im repr sucht
  - Code, der `"el_karoui_vol_v1"` hardcodiert referenziert (aber Registry-Alias vorhanden)
  - Code, der `"medium"` als VolRegime-Enum-Wert erwartet (nun `"normal"`)

**Mitigation:** Registry-Aliases gewährleisten Backward Compatibility für Strategy-Lookups.

---

## Operator How-To

### Lokale Aktualisierung

```bash
# Main aktualisieren
git switch main && git pull --ff-only

# Optional: Lokalen Feature-Branch aufräumen
git branch -D fix/pr-531-test-failures
```

### Smoke Testing (Optional)

```bash
# Research strategies smoke
pytest -q tests/test_research_strategies.py

# Full research strategies test suite
pytest -q tests/strategies/armstrong/ tests/strategies/el_karoui/
```

### Erwartete Outputs

- **Alle Tests grün:** 164 passed (Armstrong + El Karoui)
- **Integration Tests:** 33 passed (test_research_strategies.py)
- **Keine Deprecation Warnings** für Research-Strategy-Referenzen

---

## Notable Commits (PR #551)

| Commit | Beschreibung |
|--------|--------------|
| `4cafd98` | fix(pr-531): restore green CI (initial) |
| `35ce8a1` | Merge branch 'main' into fix/pr-531-test-failures |
| `c2d9039` | fix: remove duplicate 'cycle_phase' key in cycle_model.py |
| `01e3118` | style: reformat vol_model.py with ruff |
| `4b56f9b` | test: update research strategy tests for normalized markers and IDs |
| `6a566a2` | test: fix test_armstrong_cycle_info to use cycle_position |

**Final Merge Commit (main):** `8e2b888`

---

## Related Documentation

- **PR Report:** `PR531_FIX_REPORT.md` (276 Zeilen, vollständiger Verification Log)
- **Root Cause:** PR #531 Test-Failures (Armstrong / El Karoui Research-only Contracts)
- **Strategy Registry:** `src/strategies/registry.py`
- **Armstrong Tests:** `tests/strategies/armstrong/`
- **El Karoui Tests:** `tests/strategies/el_karoui/`

---

## Follow-ups

**Keine blockierenden Follow-ups.**

Optionale Verbesserungen:
1. **Deprecation Warnings:** Falls andere Code-Teile noch alte Marker/IDs verwenden, könnten Deprecation-Warnungen hinzugefügt werden
2. **Documentation Sweep:** Prüfen, ob Docs noch alte Strategy-IDs/Marker referenzieren
3. **Golden Sample Tests:** Erwägen, golden sample fixtures für Research-Strategy-Outputs zu etablieren

---

*Merge log für PR #551 – Restore green CI for PR #531 (Research Strategy Contract Normalization)*
