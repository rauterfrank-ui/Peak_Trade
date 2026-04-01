# Bounded Pilot Live Entry Gap Note

status: DRAFT  
last_updated: 2026-04-01  
owner: Peak_Trade  
purpose: **Historische** Gap-Analyse (März 2026) plus **aktueller Ist-Stand** nach Slice-4-Handoff; keine Ausweitung von Execution Authority.  
docs_token: DOCS_TOKEN_BOUNDED_PILOT_LIVE_ENTRY_GAP_NOTE

## 0. Operatives Runbook (maßgeblich)

**Operator-Prozedur** Bounded-Pilot-Live-Entry im aktuellen Repo:

- `docs/ops/runbooks/RUNBOOK_BOUNDED_PILOT_LIVE_ENTRY.md`

Technisch: **`run_bounded_pilot_session.py`** ruft bei grünen Gates (ohne `--no-invoke`) **`run_execution_session.py --mode bounded_pilot`** auf. Mit **`--no-invoke`** nur Gate-Check.

---

## 1. Intent

Dieses Dokument enthält:

1. **Abschnitt 2–4 unten:** die **historische** Beschreibung der einst identifizierten Lücken (Review vom März 2026), zur Nachvollziehbarkeit in Audits.  
2. **Abschnitt 5:** welche Punkte aus dieser Liste **im Code/den Runbooks** inzwischen **adressiert** sind.  
3. **Abschnitt 6:** verbleibende **operative** Voraussetzungen (keine implizite Freigabe).

Für den **täglichen Ablauf** gilt ausschließlich **`RUNBOOK_BOUNDED_PILOT_LIVE_ENTRY.md`**.

---

## 2. Historischer Ablauf (März 2026 — überholt)

| Step | Component | Status (historisch) |
|------|-----------|---------------------|
| 1 | `run_bounded_pilot_session.py` | Pre-Entry-Checks; exit 0 wenn Gates GREEN |
| 2 | Live-Session-Start | Wurde damals als **„not implemented“** geführt |

**Historische Beschreibung:** Der Gate-Wrapper endete ohne Aufruf des Session-Starters; es fehlte u. a. `--mode bounded_pilot` in der CLI.

---

## 3. Historische Blocker-Liste (März 2026)

| # | Blocker | Location |
|---|---------|----------|
| B1 | LiveSessionRunner lehnt `mode=live` ab | `src/execution/live_session.py` |
| B2 | Governance `live_order_execution=locked` (Broad Live) | `src/governance/go_no_go.py` |
| B3 | `run_execution_session` ohne `bounded_pilot` | `scripts/run_execution_session.py` |
| B4 | Environment nicht als Live/Pilot konfiguriert | `src/execution/live_session.py` |
| B5 | Kein Kraken-Live-Pfad in Session-Flow | — |
| B6 | Wrapper ruft Session-Starter nicht auf | `scripts/ops/run_bounded_pilot_session.py` |

---

## 4. Historische Dependency Chain (überholt)

```
run_bounded_pilot_session.py (Gates GREEN)
    → [historisch: no invocation]
run_execution_session.py --mode bounded_pilot
    → [historisch: mode not supported]
...
```

---

## 5. Stand nach Slice 4 (2026-04) — Abgleich mit historischer Liste

| ID | Historischer Blocker | Heute (Ist Repo, Bounded-Pilot-Pfad) |
|----|----------------------|--------------------------------------|
| B1 | `mode=live` weiterhin nicht der normale Eintrag | **`bounded_pilot`** ist der vorgesehene Modus; breites `live` bleibt separat geregelt. |
| B2 | Broad Live `locked` | **Unverändert sinnvoll:** `live_order_execution` bleibt **`locked`**. Für Pilot:** `live_order_execution_bounded_pilot`** ist im Code-Mapping **`approved_2026`** (`select_live_order_execution_key`). |
| B3 | Kein CLI-Modus | **Erledigt:** `run_execution_session.py` unterstützt **`bounded_pilot`**. |
| B4 | Env nicht live | **Erledigt für Pilot:** `LiveSessionRunner` / Config-Pfad setzt Pilot-Felder (u. a. `bounded_pilot_mode`, vgl. `live_session.py`). |
| B5 | Exchange im Flow | **Adressiert im Pilot-Pfad:** Kraken Live / `peak_config` gemäß Session-Konfiguration; **operative** Keys und `exchange.default_type` weiterhin Pflicht des Operators. |
| B6 | Kein Handoff | **Erledigt:** Wrapper subprocesst `run_execution_session.py --mode bounded_pilot` (ohne `--no-invoke`). |

**Residuales (keine Code-Lücken der oberen Art):** Betrieb (Go/No-Go, Caps, Keys, Kill-Switch, Evidence, PRBI/Org-Gates laut `live_pilot_execution_plan.md` falls verbindlich).

---

## 6. Relationship

- Operativ: `RUNBOOK_BOUNDED_PILOT_LIVE_ENTRY.md`
- Contract: `BOUNDED_REAL_MONEY_PILOT_ENTRY_CONTRACT.md`
- Boundary (Flow-Grenze): `BOUNDED_REAL_MONEY_PILOT_ENTRY_BOUNDARY_NOTE.md`
- Governance: `docs/governance/BOUNDED_PILOT_LIVE_ORDER_EXECUTION_DECISION_PACKAGE.md`
- Source Review: `bounded_pilot_wrapper_to_first_live_step_gap_review`

---

## 7. Non-Goals

- No execution authority  
- No governance bypass  
- No relaxation of gates  
