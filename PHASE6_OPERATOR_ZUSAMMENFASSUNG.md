# Phase 6 — Strategy-Switch Sanity Check: Operator-Zusammenfassung

**Datum**: 12. Januar 2026  
**Status**: ✅ Abgeschlossen  
**Änderungen**: 1 Datei geändert, 2 Dateien neu (Dokumentation)

---

## Was wurde gemacht?

Der **Strategy-Switch Sanity Check** war bereits vollständig implementiert, hatte aber einen **PYTHONPATH-Bug** im CLI-Script. Dieser wurde behoben.

### Problem (vor dem Fix)

```bash
$ python3 scripts/run_strategy_switch_sanity_check.py --config config/config.toml
ModuleNotFoundError: No module named 'src'
```

**Auswirkung**:
- CLI-Script nicht standalone-lauffähig
- TestHealthAutomation-Profil `governance_strategy_switch_sanity` schlug fehl
- CI/CD-Integration blockiert

### Lösung

**Datei**: `scripts/run_strategy_switch_sanity_check.py`

**Änderung**: 3 Zeilen hinzugefügt (PYTHONPATH-Setup)

```python
# Ensure src is in path (for imports to work)
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
```

### Ergebnis (nach dem Fix)

```bash
$ python3 scripts/run_strategy_switch_sanity_check.py --config config/config.toml

✅ Strategy-Switch Sanity Check: OK
==================================================
Config:             config/config.toml
active_strategy_id: ma_crossover
allowed:            ['ma_crossover', 'rsi_reversion', 'breakout']

Meldungen:
  • Strategy-Switch-Konfiguration sieht gesund aus.
```

**Exit-Code**: `0` ✅

---

## Was macht der Strategy-Switch Sanity Check?

Der Check validiert die `[live_profile.strategy_switch]`-Konfiguration in `config/config.toml` und stellt sicher, dass:

1. ✅ **`allowed`-Liste nicht leer** ist
2. ✅ **`active_strategy_id` in `allowed`** enthalten ist
3. ✅ **Keine R&D-Strategien in `allowed`** sind (z.B. `armstrong_cycle`, `el_karoui_vol_model`)
4. ✅ **Alle Strategien in `allowed` in der Registry existieren**
5. ⚠️ **Warnung bei > 5 Strategien** in `allowed` (zu komplex)

### Wichtig: Read-Only!

Der Check führt **KEINE Änderungen** durch:
- ❌ Kein automatisches Switching
- ❌ Keine Config-Änderungen
- ❌ Keine Live-Execution
- ✅ Nur Validierung & Reporting

---

## Wie verwende ich den Check?

### 1. Standalone CLI

```bash
# Einfacher Check
python3 scripts/run_strategy_switch_sanity_check.py --config config/config.toml

# JSON-Output (maschinenlesbar)
python3 scripts/run_strategy_switch_sanity_check.py --config config/config.toml --json

# Quiet-Mode (nur Exit-Code)
python3 scripts/run_strategy_switch_sanity_check.py --config config/config.toml --quiet
```

**Exit-Codes**:
- `0` = OK (alles gesund)
- `1` = FAIL (kritische Violations)
- `2` = WARN (Warnungen)

### 2. TestHealthAutomation

```bash
# Governance-Profil ausführen
python3 scripts/run_test_health_profile.py --profile governance_strategy_switch_sanity

# Weekly-Core-Profil (inkl. Switch-Sanity)
python3 scripts/run_test_health_profile.py --profile weekly_core
```

---

## Was mache ich bei Fehlern?

### Fehler 1: R&D-Strategie in `allowed`

**Symptom**:
```
❌ Strategy-Switch Sanity Check: FAIL
R&D- oder nicht-live-ready-Strategien in allowed: armstrong_cycle
```

**Lösung**:
1. Öffne `config/config.toml`
2. Entferne R&D-Strategie aus `[live_profile.strategy_switch].allowed`
3. Re-run Check

**Beispiel**:
```toml
[live_profile.strategy_switch]
allowed = ["ma_crossover", "rsi_reversion"]  # armstrong_cycle entfernt
```

### Fehler 2: `active_strategy_id` nicht in `allowed`

**Symptom**:
```
❌ Strategy-Switch Sanity Check: FAIL
active_strategy_id 'unknown_strategy' ist NICHT in der allowed-Liste.
```

**Lösung**:
1. Prüfe ob `active_strategy_id` korrekt ist
2. Falls korrekt: Füge zu `allowed` hinzu
3. Falls falsch: Korrigiere `active_strategy_id`

**Beispiel**:
```toml
[live_profile.strategy_switch]
active_strategy_id = "ma_crossover"  # Korrigiert
allowed = ["ma_crossover", "rsi_reversion"]
```

### Fehler 3: Leere `allowed`-Liste

**Symptom**:
```
❌ Strategy-Switch Sanity Check: FAIL
allowed-Liste ist leer – kein Strategy-Switch möglich.
```

**Lösung**:
1. Füge mindestens eine live-ready Strategie zu `allowed` hinzu

**Beispiel**:
```toml
[live_profile.strategy_switch]
active_strategy_id = "ma_crossover"
allowed = ["ma_crossover"]
```

---

## Dokumentation

- **Operator-Guide**: `docs/ops/STRATEGY_SWITCH_SANITY_CHECK.md`
- **Evidence Pack**: `PHASE6_STRATEGY_SWITCH_SANITY_EVIDENCE.md`
- **Source Code**: `src/governance/strategy_switch_sanity_check.py`
- **Tests**: `tests/governance/test_strategy_switch_sanity_check.py`

---

## Tests

### Alle Tests grün ✅

```bash
# Unit-Tests (16 Tests)
python3 -m pytest tests/governance/test_strategy_switch_sanity_check.py -v
# 16 passed in 0.06s

# Integration-Tests (7 Tests)
python3 -m pytest tests/ops/test_test_health_v1.py::TestRunSwitchSanityCheck -v
# 7 passed in 0.09s
```

**Total**: 23 Tests, alle grün ✅

---

## Geänderte Dateien

### Modified

1. `scripts/run_strategy_switch_sanity_check.py`
   - **Änderung**: PYTHONPATH-Fix (3 Zeilen)
   - **Grund**: Standalone-Ausführung ermöglichen

### Created

2. `docs/ops/STRATEGY_SWITCH_SANITY_CHECK.md` (NEU)
   - **Inhalt**: Operator-Dokumentation (~500 Zeilen)
   - **Grund**: Self-Service für Operatoren

3. `PHASE6_STRATEGY_SWITCH_SANITY_EVIDENCE.md` (NEU)
   - **Inhalt**: Evidence Pack & Implementation Report (~600 Zeilen)
   - **Grund**: Audit-Trail

4. `PHASE6_OPERATOR_ZUSAMMENFASSUNG.md` (NEU, diese Datei)
   - **Inhalt**: Kurze Zusammenfassung auf Deutsch
   - **Grund**: Quick-Reference für Operatoren

---

## Risk Note

**Risk Level**: **MINIMAL**

- ✅ Nur 1 geänderte Datei (3 Zeilen)
- ✅ Keine Breaking Changes
- ✅ Keine Live-Execution
- ✅ Vollständig getestet (23 Tests)
- ✅ Read-Only (keine Config-Änderungen)

---

## Nächste Schritte

### Operator-Checklist

- [x] Tests ausgeführt (23/23 grün)
- [x] Dokumentation erstellt
- [x] Evidence Pack erstellt
- [x] Linter clean
- [ ] **CI/CD-Workflow verifizieren** (GitHub Actions)
- [ ] **Nightly-Run beobachten** (Test Health Automation)

### Optional (P2)

- [ ] Pre-Commit Hook für lokale Validierung
- [ ] Slack-Notifications bei FAIL konfigurieren

---

## Fragen?

- **Dokumentation**: `docs/ops/STRATEGY_SWITCH_SANITY_CHECK.md`
- **Troubleshooting**: Siehe Dokumentation, Abschnitt "Troubleshooting"
- **FAQ**: Siehe Dokumentation, Abschnitt "FAQ"

---

**Status**: ✅ **Production-Ready**

**Autor**: Cursor Agent  
**Review**: Pending Operator-Review  
**Datum**: 12. Januar 2026
