# D2 — Adapter-Remove: Import- und Call-Site-Inventar (Archiv)

**Datum:** 2026-03-29 · **Aktualisiert:** 2026-03-29 (Post **Slice 3**)

**Ursprüngliches Ziel:** Grundlage für einen Delete-PR zu ``KillSwitchAdapter``, ``KillSwitchLayer`` und ``KillSwitchStatus``. **Erledigt:** ``src&#47;risk_layer&#47;kill_switch&#47;adapter.py`` entfernt, Re-Exports bereinigt, Smoke-Tests angepasst.

**Nachtrag Stand nach Slice 3 (2026-03-29):** Delete-PR ist gemergt; produktive Importe nutzen ``KillSwitch`` bzw. ``RiskGate`` wie unten. Historische Merge-Logs (z. B. PR 409) bleiben unverändert.

## Wichtig: ``risk_layer.risk_gate.RiskGate``

Die Klasse ``RiskGate`` in ``src&#47;risk_layer&#47;risk_gate.py`` nutzt optional direktes ``KillSwitch`` aus ``risk.kill_switch`` (PeakConfig); **kein** Legacy-Adapter.

## ``src`` — Paket-Exports (Root)

**Datei:** ``src&#47;risk_layer&#47;__init__.py``

| Export | Hinweis |
|--------|---------|
| ``order_to_dict``, ``to_order`` | Kanonische Order-Interop-API. |
| ``RiskGate`` | **Nicht** aus ``src.risk_layer`` exportiert — ``from src.risk_layer.risk_gate import RiskGate``. |

## ``src`` — Kill-Switch-Paket

**Datei:** ``src&#47;risk_layer&#47;kill_switch&#47;__init__.py``

- **Kein** ``adapter.py``; öffentliche Namen u. a. ``KillSwitch``, ``KillSwitchState``, ``ExecutionGate``, ``load_config``.

## Tests (Python)

| Datei | Relevanz |
|-------|----------|
| ``tests&#47;risk_layer&#47;test_risk_gate.py`` | ``RiskGate`` + ``KillSwitch``-Verdrahtung. |
| ``tests&#47;risk_layer&#47;test_imports_smoke.py`` | Import ``KillSwitch`` aus ``kill_switch``; minimale Konstruktion ohne Legacy-Adapter. |
| ``tests&#47;risk_layer&#47;kill_switch&#47;*.py`` | State-Machine, Persistenz, Integration. |

## Docs

- Kanonische Beispiele: ``docs&#47;risk&#47;RISK_LAYER_ALIGNMENT.md``, ``docs&#47;risk&#47;RISK_METRICS_SCHEMA.md``.
- Migration / Abschluss: ``TODO_KILL_SWITCH_ADAPTER_MIGRATION.md``.
