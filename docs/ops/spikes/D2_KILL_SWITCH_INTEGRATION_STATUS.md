# D2 Kill-Switch Integration — Status (Ops / Execution)

**Stand:** 2026-03-28 · **Quelle der Wahrheit für offene Adapter-Arbeit:** [`TODO_KILL_SWITCH_ADAPTER_MIGRATION.md`](../../../TODO_KILL_SWITCH_ADAPTER_MIGRATION.md) (Repo-Root)

## Kurzfassung

Die Integration von **persistiertem Kill-Switch-State** (`data/kill_switch/state.json`) in **Ops- und Execution-Pfaden** ist umgesetzt. Der Legacy-**`KillSwitchAdapter`** (`src/risk_layer/kill_switch/adapter.py`) und die **`RiskGate`-Klasse** unter `src/risk_layer/risk_gate.py` sind davon **getrennt** und weiterhin Gegenstand des Adapter-Migration-TODOs.

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
