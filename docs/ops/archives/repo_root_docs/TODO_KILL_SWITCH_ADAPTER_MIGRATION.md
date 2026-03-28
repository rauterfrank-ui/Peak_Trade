# TODO: Kill Switch Adapter Migration

## Ziel
Refactoring der Risk-Gate Integration, um direkt die neue KillSwitch State-Machine API zu verwenden und den Legacy-Adapter zu entfernen.

## Problem
Der `KillSwitchAdapter` (`src/risk_layer/kill_switch/adapter.py`) wurde als temporäre Backward-Kompatibilitätsschicht eingeführt, um die alte evaluator-basierte API für die Risk-Gate Integration beizubehalten.

## Begriffsklärung: zwei „Risk Gate“-Schichten

| Modul | Rolle |
|--------|--------|
| `src/ops/gates/risk_gate.py` | Reine Funktion `evaluate_risk(RiskLimits, RiskContext)`; von Live-Safety (`execution_guards`) und ähnlichen Pfaden genutzt. **Kein** `KillSwitchAdapter`. |
| `src/risk_layer/risk_gate.py` | Eigene `RiskGate`-Klasse (Audit, Order-Checks). **Hier** lag die ursprünglich gedachte Adapter-Brücke; dieser **TODO** betrifft primär diese Datei + Adapter. |

Die unten unter „Erreicht“ beschriebene D2-Arbeit betrifft **Ops/Execution** und ersetzt **nicht** automatisch die Adapter-Entfernung in `risk_layer`.

## Erreicht: Ops / Execution Kill-Switch (D2, 2026-03)

Kanonische Quelle für den persistierten Zustand: **`data/kill_switch/state.json`** (Feld `state`, u. a. `KILLED` / `RECOVERING`).

- **`src/ops/gates/risk_gate.py`:** `resolve_kill_switch_limit_from_state_file`, `kill_switch_state_path_from_env` (Reihenfolge: `PEAK_KILL_SWITCH_STATE_PATH`, dann `PEAKTRADE_KILL_SWITCH_STATE_PATH`), `kill_switch_should_block_trading` (explizites Flag oder Datei oder Fallback `PEAK_KILL_SWITCH`).
- **`src/live/safety.py`:** Runbook-B-Guards nutzen `kill_switch_should_block_trading(explicit_active=False)`.
- **`src/execution/pipeline.py`:** `_is_kill_switch_blocking()` delegiert an denselben Resolver; bounded_pilot bleibt **dateibasiert** ohne `PEAK_KILL_SWITCH`-Fallback im Pipeline-Pfad.
- **`src/execution/orchestrator.py`:** Stufe 1 nutzt `kill_switch_should_block_trading(explicit_active=self.kill_switch_active)`.
- **`src/execution/risk_hook_impl.py`:** `check_kill_switch()` nutzt dieselbe Entscheidung.

Detail-Spike (Code-Auszüge): `docs/ops/spikes/D2_KILL_SWITCH_INTEGRATION_SPIKE_2026-03-28.txt` · Kurzstatus: `docs/ops/spikes/D2_KILL_SWITCH_INTEGRATION_STATUS.md`.

## Migration Plan (weiterhin offen: Adapter + `risk_layer`)

### 1. Risk-Gate Refactoring (`risk_layer`)
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

**Status:** 📋 TODO (Adapter + `src/risk_layer/risk_gate.py`; Ops/Execution D2 siehe Abschnitt „Erreicht“)  
**Priorität:** P2 (Medium)  
**Erstellt:** 2025-12-28  
**Target:** Q1 2026  
**Letzte Doku-Aktualisierung:** 2026-03-28
