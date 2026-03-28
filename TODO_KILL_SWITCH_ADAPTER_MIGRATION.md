# TODO: Kill Switch Adapter Migration

## Ziel
Refactoring der Risk-Gate Integration, um direkt die neue KillSwitch State-Machine API zu verwenden und den Legacy-Adapter zu entfernen.

## Problem
Der `KillSwitchAdapter` (`src/risk_layer/kill_switch/adapter.py`) wurde als temporäre Backward-Kompatibilitätsschicht eingeführt, um die alte evaluator-basierte API für die Risk-Gate Integration beizubehalten.

## Begriffsklärung: zwei „Risk Gate“-Schichten

| Modul | Rolle |
|--------|--------|
| `src/ops/gates/risk_gate.py` | Reine Funktion `evaluate_risk(RiskLimits, RiskContext)`; von Live-Safety (`execution_guards`) und ähnlichen Pfaden genutzt. **Kein** `KillSwitchAdapter`. |
| `src/risk_layer/risk_gate.py` | Eigene `RiskGate`-Klasse (Audit, Order-Checks). **Slice 1:** optionales `KillSwitch` aus `risk.kill_switch` (kein `KillSwitchAdapter`). Offen: Legacy-Adapter aus dem Paket entfernen (dieser **TODO**). |

Die unten unter „Erreicht“ beschriebene D2-Arbeit betrifft **Ops/Execution** und ersetzt **nicht** automatisch die Adapter-Entfernung in `risk_layer`.

## Erreicht: Ops / Execution Kill-Switch (D2, 2026-03)

Kanonische Quelle für den persistierten Zustand: **`data&#47;kill_switch&#47;state.json`** (Feld `state`, u. a. `KILLED` / `RECOVERING`).

- **`src/ops/gates/risk_gate.py`:** `resolve_kill_switch_limit_from_state_file`, `kill_switch_state_path_from_env` (Reihenfolge: `PEAK_KILL_SWITCH_STATE_PATH`, dann `PEAKTRADE_KILL_SWITCH_STATE_PATH`), `kill_switch_should_block_trading` (explizites Flag oder Datei oder Fallback `PEAK_KILL_SWITCH`).
- **`src/live/safety.py`:** Runbook-B-Guards nutzen `kill_switch_should_block_trading(explicit_active=False)`.
- **`src/execution/pipeline.py`:** `_is_kill_switch_blocking()` delegiert an denselben Resolver; bounded_pilot bleibt **dateibasiert** ohne `PEAK_KILL_SWITCH`-Fallback im Pipeline-Pfad.
- **`src/execution/orchestrator.py`:** Stufe 1 nutzt `kill_switch_should_block_trading(explicit_active=self.kill_switch_active)`.
- **`src/execution/risk_hook_impl.py`:** `check_kill_switch()` nutzt dieselbe Entscheidung.

Detail-Spike (Code-Auszüge): `docs/ops/spikes/D2_KILL_SWITCH_INTEGRATION_SPIKE_2026-03-28.txt` · Kurzstatus: `docs/ops/spikes/D2_KILL_SWITCH_INTEGRATION_STATUS.md`.

## Erreicht: D2 Slice 1 — `risk_layer` RiskGate + State-Machine (2026-03)

- **`src/risk_layer/risk_gate.py`:** Optional wird ein **`KillSwitch`** aus **`[risk.kill_switch]`** (PeakConfig: `risk.kill_switch`) gebaut; **`evaluate()`** bricht **vor** Order-Validierung ab, wenn **`check_and_block()`** wahr ist (**`KILLED`** / **`RECOVERING`**). Kein **`KillSwitchAdapter`**.
- **Tests:** `tests/risk_layer/test_risk_gate.py` deckt aktiv / gekillt / recovering / deaktiviert ab.

Offen für spätere Slices: Trigger-Schleifen und Recovery-Flows **innerhalb** von `RiskGate` (nicht nur Block bei bereits gesetztem Zustand), dann Adapter-Entfernung.

## Migration Plan (weiterhin offen: Legacy-Adapter entfernen)

### 1. Risk-Gate Refactoring (`risk_layer`) — Slice 1 erledigt; Feinarbeit offen
**Datei:** `src/risk_layer/risk_gate.py`

**Umgesetzt (State-Machine, Slice 1):**
```python
if self._kill_switch is not None and self._kill_switch.check_and_block():
    # Block order (KILLED or RECOVERING)
```

**Später (optional, nicht Slice 1):** Metrik-getriebene **`trigger()`** / **`request_recovery()`** / **`complete_recovery()`** aus `RiskGate` heraus — nur wenn Produkt/Ops das in dieser Schicht wollen; Ops/Execution nutzen weiter die in „Erreicht: Ops / Execution“ genannten Pfade für persistierten State.

### 2. Test-Migration
**Dateien:**
- `tests/risk_layer/test_risk_gate.py` — **Slice 1:** State-Machine-Blockade abgedeckt.
- Alle Tests, die **`KillSwitchAdapter`** / **`KillSwitchLayer`** noch explizit nutzen (z. B. `tests/risk_layer/test_imports_smoke.py`).

**Änderungen (für Adapter-Remove-PR):**
- Legacy-**`evaluate()`** am Adapter → in neuen Tests wo nötig **State-Checks** / **`KillSwitch`** direkt.
- Entferne **`reset()`**-Pfade am Adapter → Recovery-Workflow an der State-Machine.
- Entferne **`_last_status`**-Zugriffe → Status über **`KillSwitch.state`** / **`get_status()`**.

### 3. Adapter entfernen
**Datei zu löschen:** `src/risk_layer/kill_switch/adapter.py`

**Imports aufräumen:**
- `src/risk_layer/risk_gate.py` - Update imports
- Alle Tests - Update imports

### 4. Dokumentation aktualisieren
- `docs/risk/KILL_SWITCH_ARCHITECTURE.md` - Legacy-Adapter Referenzen entfernen
- `docs/risk/KILL_SWITCH.md` - Beispiele aktualisieren
- `README_KILL_SWITCH.md` - Migration Notes hinzufügen

## Removal criteria (vor Delete-PR)

Ein separater PR-Track soll den Adapter erst entfernen, wenn:

1. **Inventar:** Vollständige Liste der Import-/Call-Sites zu ``KillSwitchAdapter``, ``KillSwitchLayer``, ``KillSwitchStatus`` und ``to_violations`` (``src/risk_layer/risk_gate.py`` nutzt **keinen** Adapter — Slice 1; Rest: Tests, Re-Exports, Downstream-Docs).
2. **Ziel-API:** Festgelegtes Nutzungsmodell (typisch: ``KillSwitch`` + State-Machine, ggf. Trigger/Recovery), abgestimmt mit Ops/Execution-Pfaden aus dem D2-Abschnitt „Erreicht“.
3. **Regression:** Angepasste oder neue Tests ohne versehentliche Legacy-Konstruktion; bestehende Kill-Switch-Test-Suite grün.
4. **Doku:** Beispiele unter ``docs&#47;risk&#47;`` und READMEs ohne veraltete ``KillSwitchLayer``-Factory, wo nicht absichtlich historisch.

Bis dahin bleiben Deprecation-Warnungen beim Konstruieren von ``KillSwitchAdapter`` der sichtbare Legacy-Hinweis.

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
- **Deprecation (Spike):** `docs/ops/spikes/D2_RISK_LAYER_ADAPTER_DEPRECATION_SPIKE_2026-03-28.md`
- **Ops/Execution D2 (Kontext):** `docs/ops/spikes/D2_KILL_SWITCH_INTEGRATION_STATUS.md`
- **Roadmap:** `docs/risk/roadmaps/ROADMAP_EMERGENCY_KILL_SWITCH.md`

## Owner

TBD - Assignment vor Start des Refactorings

---

**Status:** 📋 TODO (Legacy-**Adapter**-Entfernung + Doku; **RiskGate** nutzt State-Machine siehe „Erreicht: D2 Slice 1“; Ops/Execution D2 siehe „Erreicht: Ops / Execution“)  
**Priorität:** P2 (Medium)  
**Erstellt:** 2025-12-28  
**Target:** Q1 2026  
**Letzte Doku-Aktualisierung:** 2026-03-29 (Slice 2: kanonische KillSwitch-Doku, Inventar)
