# TODO: Kill Switch Adapter Migration — **abgeschlossen** (D2 Slice 3, 2026-03)

## Ziel (erreicht)

Die alte evaluator-basierte Schicht (**`KillSwitchAdapter`**, **`KillSwitchLayer`**, **`KillSwitchStatus`**, **`to_violations`**) ist aus dem Code entfernt. **`RiskGate`** und Downstream nutzen die **State-Machine** (**`KillSwitch`**) direkt (siehe „Erreicht“ unten).

## Problem (historisch)

Der **`KillSwitchAdapter`** (früher unter `src&#47;risk_layer&#47;kill_switch&#47;adapter.py`, **gelöscht**) war eine temporäre Backward-Kompatibilitätsschicht für die alte Evaluator-API.

## Begriffsklärung: zwei „Risk Gate“-Schichten

| Modul | Rolle |
|--------|--------|
| `src&#47;ops&#47;gates&#47;risk_gate.py` | Reine Funktion `evaluate_risk(RiskLimits, RiskContext)`; von Live-Safety (`execution_guards`) und ähnlichen Pfaden genutzt. |
| `src&#47;risk_layer&#47;risk_gate.py` | `RiskGate`-Klasse (Audit, Order-Checks); optionales `KillSwitch` aus `risk.kill_switch`. |

Die unter „Erreicht: Ops / Execution“ beschriebene D2-Arbeit betrifft **persistierten State** in Ops/Execution; sie ist von der **`risk_layer`**-Integration getrennt beschrieben.

## Erreicht: Ops / Execution Kill-Switch (D2, 2026-03)

Kanonische Quelle für den persistierten Zustand: **`data&#47;kill_switch&#47;state.json`** (Feld `state`, u. a. `KILLED` oder `RECOVERING`).

- **`src&#47;ops&#47;gates&#47;risk_gate.py`:** `resolve_kill_switch_limit_from_state_file`, `kill_switch_state_path_from_env`, `kill_switch_should_block_trading`.
- **`src&#47;live&#47;safety.py`**, **`src&#47;execution&#47;pipeline.py`**, **`src&#47;execution&#47;orchestrator.py`**, **`src&#47;execution&#47;risk_hook_impl.py`:** siehe Spike-Status.

Detail-Spike: `docs&#47;ops&#47;spikes&#47;D2_KILL_SWITCH_INTEGRATION_SPIKE_2026-03-28.txt` · Kurzstatus: `docs&#47;ops&#47;spikes&#47;D2_KILL_SWITCH_INTEGRATION_STATUS.md`.

## Erreicht: D2 Slice 1 — `risk_layer` RiskGate + State-Machine (2026-03)

- **`src&#47;risk_layer&#47;risk_gate.py`:** Optional **`KillSwitch`** aus **`[risk.kill_switch]`**; **`evaluate()`** blockiert bei **`check_and_block()`** (**`KILLED`** oder **`RECOVERING`**).

## Erreicht: D2 Slice 2 — Doku (2026-03)

- Kanonische Kill-Switch-Beispiele in `docs&#47;risk&#47;RISK_LAYER_ALIGNMENT.md`, `docs&#47;risk&#47;RISK_METRICS_SCHEMA.md`.

## Erreicht: D2 Slice 3 — Adapter entfernt (2026-03)

- **Gelöscht:** `src&#47;risk_layer&#47;kill_switch&#47;adapter.py`
- **`src&#47;risk_layer&#47;kill_switch&#47;__init__.py`:** Keine Legacy-Symbole mehr (`KillSwitchAdapter`, `KillSwitchLayer`, `KillSwitchStatus`, `to_violations`).
- **`src&#47;risk_layer&#47;__init__.py`:** Nur noch `order_to_dict`, `to_order`.
- **Tests:** `tests&#47;risk_layer&#47;test_imports_smoke.py` importiert `KillSwitch` direkt.

## Optional (niedrige Priorität)

- `docs&#47;risk&#47;KILL_SWITCH_ARCHITECTURE.md`, `docs&#47;risk&#47;KILL_SWITCH.md`, `README_KILL_SWITCH.md` — vereinzelte historische Verweise bei Bedarf bereinigen (nicht blockierend).

## Referenzen

- **PR #409:** Einführung des Legacy-Adapters (historisch)
- **Deprecation (Spike):** `docs&#47;ops&#47;spikes&#47;D2_RISK_LAYER_ADAPTER_DEPRECATION_SPIKE_2026-03-28.md`
- **Inventar (Archiv):** `docs&#47;ops&#47;spikes&#47;D2_ADAPTER_REMOVE_INVENTORY_2026-03-29.md`
- **Roadmap:** `docs&#47;risk&#47;roadmaps&#47;ROADMAP_EMERGENCY_KILL_SWITCH.md`

---

**Status:** ✅ Abgeschlossen (Adapter entfernt; State-Machine kanonisch)  
**Letzte Doku-Aktualisierung:** 2026-03-29 (Slice 3)
