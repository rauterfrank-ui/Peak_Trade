# D2 Kill-Switch Integration — Status (Ops / Execution)

**Stand:** 2026-03-29 · **Adapter-Migration (risk_layer):** abgeschlossen — [`TODO_KILL_SWITCH_ADAPTER_MIGRATION.md`](../../../TODO_KILL_SWITCH_ADAPTER_MIGRATION.md) (Repo-Root)

## Kurzfassung

Die Integration von **persistiertem Kill-Switch-State** (`data&#47;kill_switch&#47;state.json`) in **Ops- und Execution-Pfaden** ist umgesetzt. Der frühere Legacy-**`KillSwitchAdapter`** wurde in **D2 Slice 3** entfernt; **`RiskGate`** (`src&#47;risk_layer&#47;risk_gate.py`) nutzt optional direkt **`KillSwitch`** aus der Konfiguration (siehe `TODO_KILL_SWITCH_ADAPTER_MIGRATION.md`, abgeschlossen).

## Umgesetzte Bausteine

| Bereich | Inhalt |
|---------|--------|
| `src/ops/gates/risk_gate.py` | Resolver für State-Datei, Env-Pfad-Alias (`PEAK_KILL_SWITCH_STATE_PATH` / `PEAKTRADE_KILL_SWITCH_STATE_PATH`), `kill_switch_should_block_trading` |
| `src/live/safety.py` | Runbook-B-Guards: gleiche Block-Logik wie oben |
| `src/execution/pipeline.py` | Bounded-pilot: gemeinsamer Resolver; kein `PEAK_KILL_SWITCH`-Fallback in diesem Pfad |
| `src/execution/orchestrator.py` | Stufe-1-Abweisung bei aktivem Kill-Switch (Flag + Datei/Env) |
| `src/execution/risk_hook_impl.py` | `check_kill_switch()` an gleicher Logik |

## Referenzen

- **Spike-Notiz (Code-Auszüge, eingefroren):** [`D2_KILL_SWITCH_INTEGRATION_SPIKE_2026-03-28.txt`](./D2_KILL_SWITCH_INTEGRATION_SPIKE_2026-03-28.txt)
- **Adapter-Migration / `risk_layer`:** [`TODO_KILL_SWITCH_ADAPTER_MIGRATION.md`](../../../TODO_KILL_SWITCH_ADAPTER_MIGRATION.md)
