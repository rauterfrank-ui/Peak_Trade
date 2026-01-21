# TODO: Kill Switch Adapter Migration

## Ziel
Refactoring der Risk-Gate Integration, um direkt die neue KillSwitch State-Machine API zu verwenden und den Legacy-Adapter zu entfernen.

## Problem
Der `KillSwitchAdapter` (`src/risk_layer/kill_switch/adapter.py`) wurde als temporäre Backward-Kompatibilitätsschicht eingeführt, um die alte evaluator-basierte API für die Risk-Gate Integration beizubehalten.

## Migration Plan

### 1. Risk-Gate Refactoring
**Datei:** `src/risk_layer/risk_gate.py`

**Aktuell (Legacy API):**
```python
kill_switch_status = self._kill_switch.evaluate(risk_metrics)
if kill_switch_status.armed:
    # Block order
```

**Ziel (State-Machine API):**
```python
# Direct state access
if self._kill_switch.is_killed:
    # Block order

# Trigger evaluation
for trigger in self._kill_switch.triggers:
    if trigger.should_trigger(risk_metrics):
        self._kill_switch.trigger(trigger_id=trigger.id, reason="...")

# Recovery workflow
if needs_recovery:
    request = self._kill_switch.request_recovery(operator_id="...")
    # ... health checks ...
    self._kill_switch.complete_recovery()
```

### 2. Test-Migration
**Dateien:**
- `tests/risk_layer/test_risk_gate.py`
- Alle Tests, die `KillSwitchAdapter` verwenden

**Änderungen:**
- Entferne `evaluate()` Aufrufe → nutze direkte State-Checks
- Entferne `reset()` Aufrufe → nutze Recovery-Workflow
- Entferne `_last_status` Zugriffe → nutze State-Properties

### 3. Adapter entfernen
**Datei zu löschen:** `src/risk_layer/kill_switch/adapter.py`

**Imports aufräumen:**
- `src/risk_layer/risk_gate.py` - Update imports
- Alle Tests - Update imports

### 4. Dokumentation aktualisieren
- `docs/risk/KILL_SWITCH_ARCHITECTURE.md` - Legacy-Adapter Referenzen entfernen
- `docs/risk/KILL_SWITCH.md` - Beispiele aktualisieren
- `README_KILL_SWITCH.md` - Migration Notes hinzufügen

## Verifizierung

Nach Migration müssen bestehen:
- ✅ Alle Kill-Switch Tests (`tests/risk_layer/kill_switch/`)
- ✅ Alle Risk-Gate Tests (`tests/risk_layer/test_risk_gate.py`)
- ✅ Integration Tests
- ✅ Keine Referenzen auf `adapter.py` im Code

## Timeline

**Target:** Q1 2026

**Voraussetzungen:**
- Risk-Gate läuft stabil in Produktion
- Keine kritischen Incidents mit Kill-Switch
- Team hat Zeit für Refactoring

## Referenzen

- **PR #409:** Einführung des Legacy-Adapters
- **Adapter-Code:** `src/risk_layer/kill_switch/adapter.py`
- **Deprecation-Notice:** Im Adapter als Kommentar markiert
- **Roadmap:** `docs/risk/roadmaps/ROADMAP_EMERGENCY_KILL_SWITCH.md`

## Owner

TBD - Assignment vor Start des Refactorings

---

**Status:** 📋 TODO  
**Priorität:** P2 (Medium)  
**Erstellt:** 2025-12-28  
**Target:** Q1 2026
