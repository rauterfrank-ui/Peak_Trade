# D2 — Adapter-Remove: Import- und Call-Site-Inventar (Read-only)

**Datum:** 2026-03-29 · **Branch:** `feat/d2-adapter-remove-inventory` · **Basis:** `main` (Stand lokaler `rg`-Lauf)

**Ziel:** Grundlage für einen **späteren** Delete-PR zu ``KillSwitchAdapter``, ``KillSwitchLayer`` und ``KillSwitchStatus`` (siehe ``TODO_KILL_SWITCH_ADAPTER_MIGRATION.md``, Abschnitt „Removal criteria“). **Kein** Code geändert — nur diese Notiz.

## Wichtig: ``risk_layer.risk_gate.RiskGate`` ≠ Kill-Switch-Adapter

Die Klasse ``RiskGate`` in ``src&#47;risk_layer&#47;risk_gate.py`` importiert **keinen** ``KillSwitchAdapter``, ``KillSwitchLayer`` oder ``KillSwitch``. Sie ist ein Order-/Audit-Orchestrator (Skeleton). Die Legacy-Formulierung „used by risk_gate“ im Adapter-Modul bezieht sich auf **historische Planung**, nicht auf einen aktuellen Import in dieser Datei.

## ``src`` — Paket-Exports (Root)

**Datei:** ``src&#47;risk_layer&#47;__init__.py``

| Export | Hinweis |
|--------|---------|
| ``KillSwitchLayer``, ``KillSwitchStatus`` | Re-Export aus ``kill_switch``; Konstruktion von ``KillSwitchLayer`` löst ``DeprecationWarning`` aus (Adapter). |
| ``RiskGate`` | **Nicht** aus ``src.risk_layer`` exportiert (nur ``order_to_dict``, ``to_order``, Kill-Switch-Legacy-Symbole). Downstream-Imports ``from src.risk_layer import RiskGate`` in Docs sind **inkonsistent** mit dem aktuellen ``__all__``. |

## ``src`` — Kill-Switch-Paket

**Datei:** ``src&#47;risk_layer&#47;kill_switch&#47;__init__.py``

- Importiert ``KillSwitchAdapter``, ``KillSwitchStatus`` aus ``adapter.py``.
- Factory ``KillSwitchLayer(config)`` → ``KillSwitchAdapter(KillSwitch(...))``.
- Öffentliche Namen u. a. ``KillSwitch``, ``KillSwitchAdapter``, ``KillSwitchLayer``, ``KillSwitchStatus``.

## ``src`` — Sonstige Code-Referenzen (Auszug)

| Bereich | Inhalt |
|---------|--------|
| ``adapter.py`` | Definition ``KillSwitchAdapter`` und ``KillSwitchStatus``; ``DeprecationWarning`` bei Adapter-Konstruktion. |
| ``core.py`` | Kommentar zu Legacy-API (Property), kein Adapter-Import. |
| ``kill_switch&#47;cli.py`` | ``KillSwitch``, Config — **kein** ``KillSwitchAdapter`` in diesem Import. |

## Tests (Python)

| Datei | Relevanz |
|-------|----------|
| ``tests&#47;risk_layer&#47;test_risk_gate.py`` | Viele Aufrufe ``RiskGate(test_config)`` und ``RiskGate(cfg)`` — **RiskGate**, nicht Adapter. |
| ``tests&#47;risk_layer&#47;test_imports_smoke.py`` | Import ``KillSwitchLayer`` und ``KillSwitchStatus``; **einziger** bewusster Test-Pfad mit ``KillSwitchLayer({})`` + ``pytest.warns(DeprecationWarning)``. |
| ``tests&#47;risk_layer&#47;kill_switch&#47;*.py`` | Überwiegend ``KillSwitch`` (State-Machine), **kein** Adapter-Remove-Ziel für Slice 1. |

## Docs / Archiv (Vorkommen im ``rg``-Muster)

- **KillSwitchLayer-Beispiele:** u. a. ``docs&#47;risk&#47;RISK_METRICS_SCHEMA.md``, ``docs&#47;risk&#47;RISK_LAYER_ALIGNMENT.md``.
- **RiskGate aus ``risk_gate``-Modul:** mehrere Runbooks unter ``docs&#47;risk&#47;`` (``from src.risk_layer.risk_gate import RiskGate``).
- **Spikes / TODO:** ``D2_RISK_LAYER_ADAPTER_DEPRECATION_SPIKE_2026-03-28.md``, ``TODO_KILL_SWITCH_ADAPTER_MIGRATION.md``, Archiv-Kopie des TODO.

## Nächster Schritt (nicht Teil dieser Datei)

Vollständiger Delete-PR: Symbole entfernen, Tests und **alle** Doc-Beispiele anpassen, ``src.risk_layer``-Exporte bereinigen; vorher Ziel-API und Regression-Tests laut Root-TODO festlegen.
