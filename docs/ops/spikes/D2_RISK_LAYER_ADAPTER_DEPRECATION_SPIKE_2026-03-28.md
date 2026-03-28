# D2 — `risk_layer` Kill-Switch-Adapter: Inventar & Deprecation-Spike

**Datum:** 2026-03-28 · **Branch:** `feat/d2-risk-layer-adapter-deprecation-spike`

## Ziel

Legacy-API (`KillSwitchAdapter`, `KillSwitchLayer`, `KillSwitchStatus`) inventarisieren, von der **Ops/Execution-D2-Integration** abgrenzen und Laufzeit-**Deprecation** einziehen, ohne das Verhalten der State-Machine (`KillSwitch`) zu ändern.

## Nachtrag (Stand nach D2 Slice 3, 2026-03-29)

- **`KillSwitchAdapter`** und zugehörige Legacy-Symbole sind **aus dem Code entfernt** (u. a. ehemaliges Modul unter `src&#47;risk_layer&#47;kill_switch&#47;adapter.py`).
- Die Tabellen unten beschreiben den **Spike-Stand 2026-03-28** und bleiben als **historische** Referenz; kanonischer Abschluss: [`TODO_KILL_SWITCH_ADAPTER_MIGRATION.md`](../../../TODO_KILL_SWITCH_ADAPTER_MIGRATION.md).

## Begriffsklärung (kurz)

| Begriff | Bedeutung |
|---------|-----------|
| Ops/Execution D2 | `src&#47;ops&#47;gates&#47;risk_gate.py`, Live-Safety, Pipeline, Orchestrator — **ohne** `KillSwitchAdapter` |
| Dieser Spike | **`src&#47;risk_layer&#47;kill_switch&#47;adapter.py`** + Re-Exports unter `src&#47;risk_layer` |

Siehe auch: [`D2_KILL_SWITCH_INTEGRATION_STATUS.md`](./D2_KILL_SWITCH_INTEGRATION_STATUS.md), [`TODO_KILL_SWITCH_ADAPTER_MIGRATION.md`](../../../TODO_KILL_SWITCH_ADAPTER_MIGRATION.md).

## Inventar — Python-Referenzen (Stand Spike)

| Symbol | Definition | Produktive Nutzer (Repo) |
|--------|------------|-------------------------|
| `KillSwitchAdapter` | `adapter.py` | Keine direkten Imports außerhalb `src&#47;risk_layer&#47;kill_switch&#47;__init__.py` (siehe grep) |
| `KillSwitchLayer` | Factory in `src&#47;risk_layer&#47;kill_switch&#47;__init__.py` | Nur Re-Export `src&#47;risk_layer&#47;__init__.py`, Docs (`RISK_METRICS_SCHEMA`, `RISK_LAYER_ALIGNMENT`) |
| `KillSwitchStatus` | `adapter.py` | Re-Export `risk_layer`, Smoke-Tests |
| `to_violations` | `src&#47;risk_layer&#47;kill_switch&#47;__init__.py` | Legacy-Stub |

**Hinweis:** `src&#47;risk_layer&#47;risk_gate.py` ist eine **eigene** `RiskGate`-Klasse (Audit/Order); sie nutzt in diesem Branch **nicht** zwingend den Adapter — vollständige Migration bleibt im Root-TODO.

## Umgesetzt in diesem Spike

- **`DeprecationWarning`** bei Erzeugung eines **`KillSwitchAdapter`** (deckt `KillSwitchLayer(config)` mit ab).
- Keine Warnung pro `KillSwitchStatus`-Instanz (würde `evaluate()`-Pfade spammen); Status bleibt dokumentiert deprecated.

## Nächste Schritte (nicht Teil dieses PR)

- `risk_layer.risk_gate` / Call-Sites auf `KillSwitch` direkt umstellen.
- Adapter-Modul entfernen, Tests anpassen (siehe `TODO_KILL_SWITCH_ADAPTER_MIGRATION.md`).
