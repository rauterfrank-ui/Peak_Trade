# Dashboard Governance: NO‑LIVE (unverhandelbar)

Dieses Dokument beschreibt **Governance‑Invarianten** für alle Dashboard-/Observability‑Komponenten in Peak_Trade (WebUI, Watch‑Only UI, Grafana/Prometheus).

**Kernaussage:** Dashboards und Observability sind **watch‑only / read‑only** und dürfen **niemals** Live‑Execution „freischalten“, auslösen oder indirekt ermöglichen.

---

## Grundprinzipien

- **Watch‑only bleibt watch‑only**: UI/HTTP‑Layer stellt Sichtbarkeit her, keine Ausführung.
- **Defense‑in‑Depth**: Live‑Safety wird durch mehrere Schichten abgesichert (Environment‑Mode, globale Flags, Risk‑Limits, SafetyGuard, Governance‑Prozesse).
- **Fail‑closed bei Unsicherheit**: Wenn unklar ist, ob etwas eine mutierende Aktion triggert → blockieren, nicht ausführen.

---

## Was Dashboards / Grafana / Prometheus niemals tun dürfen

- **Keine Orders erzeugen** (weder direkt noch über API‑Side‑Effects).
- **Keine Start/Stop/Mutations für Runs** (kein „Run starten“, kein „Trade ausführen“, kein „Override schreiben“).
- **Keine Secrets‑Exfiltration** (z.B. Exchange Keys, Tokens, ENV dumps).
- **Keine Umgehung von Gates** (Risk‑Limits, Live‑Mode‑Gate, SafetyGuard, Governance Locks).

---

## Technische Leitplanken (Iststand im Repo)

### Watch‑Only Live Dashboard v0 (Phase 67)

- **Read‑only API**: mutierende Methoden unter `/api/...` werden **hart** geblockt (HTTP 405).
- **Prometheus `/metrics`**: rein observability; optional aktivierbar; ohne Trading‑Side‑Effects.

Siehe:
- `src/live/web/app.py` (Middleware: reject mutating API methods)
- `docs/webui/DASHBOARD_V0_OVERVIEW.md` (Safety Gate + Observability Hinweise)

### WebUI v1.x (R&D / Live‑Track / Telemetry Viewer)

- Fokus: **read‑only Status‑Ansichten** (Sessions, Telemetry, Alerts).
- Execution/Live‑Fähigkeit ist governance‑locked und bleibt außerhalb der UI‑Pfadlogik.

Siehe:
- `src/webui/app.py`
- `docs/webui/DASHBOARD_OVERVIEW.md`

---

## Governance‑Schalter (Konzept & Referenzen)

Peak_Trade nutzt (mindestens) folgende Schichten, die **unabhängig** von Dashboard/Grafana bleiben müssen:

- **Environment‑Mode** (z.B. `paper`/`shadow`/`testnet`/`live`)
- **Globale Flags** (Beispiel aus Governance‑Doku: `enable_live_trading = false`)
- **Risk‑Limits** (z.B. Live‑Risk‑Limits, Max‑Loss, Notional Caps)
- **SafetyGuard / Live‑Mode‑Gate** (Hard‑Gates)

Wichtig: Die **exakte** Flag‑/Config‑Benennung kann je Layer variieren; Dashboards dürfen sie **nicht** verändern.

Referenzen:
- `docs/GOVERNANCE_AND_SAFETY_OVERVIEW.md` (Defense‑in‑Depth, `enable_live_trading = false` als Beispiel)
- `docs/LIVE_OVERRIDES_CONFIG_INTEGRATION.md` (Policy‑safe: beschreibt Mechanik, keine Live‑Enable‑Anleitung)
- `src/governance/live_mode_gate.py` (Live‑Mode Gate, code-level Governance)

---

## Observability Contract: Cardinality & Safety

- **Keine high‑cardinality Labels** in Prometheus (kein `run_id`, kein `intent_id`, keine Order‑IDs).
- High‑cardinality gehört in **Logs/Ledger**, nicht in Metrics.
- Grafana bleibt **Aggregations‑UI**; Deep Links dürfen nur auf **read‑only** Web‑Ansichten zeigen.

Siehe:
- `docs/webui/DASHBOARD_DATA_CONTRACT_OBS_v1.md`
