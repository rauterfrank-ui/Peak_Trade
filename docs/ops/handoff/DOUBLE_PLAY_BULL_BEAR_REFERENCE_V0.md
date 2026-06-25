# Bull/Bear Double Play — Referenz v0 (read-only)

> **Zweck:** Handelslogik verstehen, ohne sie zu ändern.  
> In neuen Chat anhängen bei Fragen zu Bull/Bear, Long/Short, State Machine, Replay.

**Invariante:** Long und Short sind **nie gleichzeitig aktiv**. Replay ist **zero-order** (`orders=0`, `cancels=0`, `fills=0`).

---

## 1. Architektur-Überblick

```text
Market Ticks (Preis + Zeit)
    │
    ▼
offline_double_play_scenario_replay_v0
    │
    ├─ double_play_state.transition_state()     ← State Machine
    ├─ double_play_survival.evaluate_survival() ← Drawdown / Cooldown
    ├─ double_play_suitability.evaluate_suitability()
    ├─ double_play_capital_slot.evaluate_capital_slot()
    └─ double_play_composition.compose_double_play_decision()
           │
           ▼
    DoublePlayDecision (LONG / SHORT / FLAT / HOLD)
    → nur Digests/Evidence, keine Orders
```

**Instrument:** `ETH-PERP` (`SYNTHETIC_FUTURES_INSTRUMENT` im Replay)  
**Spec:** `docs/ops/specs/MASTER_V2_DOUBLE_PLAY_TRADING_LOGIC_MANIFEST_V0.md`

**Acceptance matrix:** docs/ops/specs/MASTER_V2_DOUBLE_PLAY_KILL_ALL_STATE_SWITCH_FAVORABLE_ADVERSE_EXTREME_MOVES_ACCEPTANCE_V0.md

---

## 2. State Machine (`double_play_state.py`)

### Zustände

| State | Bedeutung |
|-------|-----------|
| `FLAT` | Keine aktive Position |
| `LONG_ACTIVE` | Bull-Leg aktiv |
| `SHORT_ACTIVE` | Bear-Leg aktiv |
| `COOLDOWN` | Nach Exit, Wartezeit bis Re-Entry |

### ScopeEvents (pro Tick)

| Event | Wirkung |
|-------|---------|
| `NOOP` | Kein Zustandswechsel (typisch bei reinem Preis-Tick) |
| `ENTER_LONG` | FLAT → LONG_ACTIVE |
| `ENTER_SHORT` | FLAT → SHORT_ACTIVE |
| `EXIT_LONG` | LONG_ACTIVE → COOLDOWN oder FLAT |
| `EXIT_SHORT` | SHORT_ACTIVE → COOLDOWN oder FLAT |
| `COOLDOWN_EXPIRED` | COOLDOWN → FLAT |

### Harte Regel

`LONG_ACTIVE` und `SHORT_ACTIVE` **exklusiv** — niemals beide gleichzeitig.

---

## 3. Bull/Bear Logik (konzeptionell)

### Bull (Long)

- Aktivierung wenn Trend-/Boundary-Bedingungen für Aufwärtsrichtung erfüllt
- Survival prüft Drawdown-Limits und Exit-Signale
- Capital Slot begrenzt Exposure

### Bear (Short)

- Spiegelbildliche Logik für Abwärtsrichtung
- Gleiche Survival/Suitability/Capital-Pipeline
- Wechsel nur über definierte Transitions (nicht direkt Long↔Short)

### Composition Gate (`double_play_composition.py`)

Fasst Survival + Suitability + Capital Slot zu einer Entscheidung:

- `LONG` — Long-Entry oder Long-Hold
- `SHORT` — Short-Entry oder Short-Hold
- `FLAT` — keine Position
- `HOLD` — Position halten, kein neuer Entry

---

## 4. Offline Replay (`offline_double_play_scenario_replay_v0.py`)

**Einstiegspunkt für Testnet-Completion-Path:**

```python
run_offline_double_play_scenario_replay_v0(
    ticks: Sequence[OfflineDoublePlayScenarioTickV0],
    ...
)
```

**Pro Tick:**
1. Boundaries evaluieren
2. `transition_state` aufrufen
3. Survival → Suitability → Capital Slot → Composition
4. Digests/Evidence schreiben

**Testnet-Mapping:** Jeder gültige PF_ETHUSD-Ticker-Tick wird zu `OfflineDoublePlayScenarioTickV0` mit `ScopeEvent.NOOP` (nur Preis-Update, kein Trade-Event).

---

## 5. Wichtige Dateien (nur lesen)

| Datei | Rolle |
|-------|-------|
| `src/trading/master_v2/double_play_state.py` | State Machine |
| `src/trading/master_v2/double_play_composition.py` | Entscheidungs-Gate |
| `src/trading/master_v2/double_play_survival.py` | Drawdown / Exit |
| `src/trading/master_v2/double_play_suitability.py` | Markt-Eignung |
| `src/trading/master_v2/double_play_capital_slot.py` | Kapital-Allokation |
| `src/trading/master_v2/offline_double_play_scenario_replay_v0.py` | Replay-Orchestrator |
| `docs/ops/specs/MASTER_V2_DOUBLE_PLAY_TRADING_LOGIC_MANIFEST_V0.md` | Kanonische Spec |

### Separater Switch-Gate (nicht Master-V2-Core)

| Datei | Rolle |
|-------|-------|
| `src/ops/gates/switch_gate.py` | Operator-Switch-Gate |
| `src/ops/double_play/specialists.py` | Specialist-Logik |

---

## 6. Was der Agent NICHT tun darf (ohne explizites GO)

- Parameter in Survival/Suitability/Capital ändern
- State-Transitions erweitern oder lockern
- Orders/Cancels im Replay aktivieren
- `live_authorization=true` setzen
- Bull/Bear-Logik „vereinfachen“ oder Fixture-Truth einführen

---

## 7. Typische User-Fragen → wo nachschauen

| Frage | Antwort-Ort |
|-------|-------------|
| Wann wechselt Long zu Short? | `double_play_state.py` + Spec Manifest |
| Was passiert bei Drawdown? | `double_play_survival.py` |
| Wie kommt ein Testnet-Tick ins Replay? | `bounded_testnet_market_input_admission_wiring_v0.py` |
| Wo läuft der Replay im Testnet-Pfad? | `bounded_master_v2_testnet_completion_path_wiring_v0.py` |
| Gibt es Live-Orders? | Nein — zero-order invariant |

---

*Referenz-Stand: 2026-06-23. Handelslogik unverändert seit Testnet-Wiring-Integration.*
