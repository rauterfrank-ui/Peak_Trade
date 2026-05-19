# OPS Cockpit — Read-Only Status Summary

**Erstellt:** Bestandsaufnahme auf Basis von Repo-Lesezugriff (keine Codeänderungen durch diese Datei).
**Repo-Pfad (Session):** `&#47;Users&#47;frnkhrz&#47;Peak_Trade`
**Branch (Ziel):** `main` (nach `git pull --ff-only` laut Session; lokale Änderungen an anderen Dateien können die Arbeitskopie verunreinigen — siehe unten).

---

## 1. Executive Summary

**Gesicherte Evidenz:** Das OPS Cockpit ist als **read-only** Web-UI unter `GET &#47;ops` (HTML) und **`GET &#47;api&#47;ops-cockpit`** (JSON, gleiche Payload-Form) in `src&#47;webui&#47;app.py` angebunden. Zentrale Implementierung: `src&#47;webui&#47;ops_cockpit.py` (~4186 Zeilen) mit `build_ops_cockpit_payload`, `render_ops_cockpit_html` und zahlreichen `*_observation`-Aggregaten sowie Operator-Summary-Renderern.

**Dokumentation:** Drei kanonische Spez-Dateien unter `docs&#47;ops&#47;specs&#47;`: `OPS_COCKPIT_PAYLOAD_READ_MODEL_CONTRACT.md`, `OPS_COCKPIT_OPERATOR_SUMMARY_SURFACE.md`, `OPS_COCKPIT_VNEXT_REQUIRED_VIEWS_COVERAGE.md`. Die **Dashboard-Master-Checkliste** (`docs&#47;DASHBOARD_COMPLETION_MASTER_CHECKLIST.md`) verweist explizit auf diese Traceability — **ohne** Vollständigkeits-Freigabe (laut Checkliste).

**Jüngste Entwicklung (main, git log):** Eine Serie von PRs **#2570–#2581** hat **stabile HTML-`id`-Anker** für Operator-Summary-Blöcke und Hauptseiten-Karten ergänzt (Preamble, Status at a glance, System status, Evidence freshness, Go/No-Go, Phase 83/57, Balance/Stale/Exposure/Dependencies/Run/Incident-Rollup/Incident-read-model, Truth/Runtime-Hauptkarten).

**Interpretation (kennzeichnet):** Der Cockpit-Bereich wirkt für **Sichtbarkeit/Traceability** und **truth-first**-Lesesemantik weit ausgebaut; verbleibende Lücken betreffen eher **fehlende oder nicht verankerte Hilfs-UI** (z. B. innere Karten ohne äußeres `id`) und **Dokumentationspflege** — nicht zwingend fehlende Payload-Keys (Contract listet ~39 Top-Level-Keys).

---

## 2. Current State Snapshot

| Aspekt | Gesicherte Repo-Evidenz |
|--------|---------------------------|
| Routen | `src&#47;webui&#47;app.py`: `@app.get("&#47;ops")` → `render_ops_cockpit_html`; `@app.get("&#47;api&#47;ops-cockpit")` → `build_ops_cockpit_payload` (Zeilen ~2019–2061, Import `ops_cockpit` ~125–129). |
| Payload-Builder | `build_ops_cockpit_payload` in `src&#47;webui&#47;ops_cockpit.py`. |
| HTML | `render_ops_cockpit_html` in derselben Datei. |
| Contract (Keys) | `tests&#47;ops&#47;test_ops_cockpit_payload_top_level_contract.py` (~71 Zeilen). |
| WebUI-Regression | `tests&#47;webui&#47;test_ops_cockpit.py` (~2676 Zeilen); `rg '^def test_'` → **139** Testfunktionen in dieser Datei (Stand Inventur). |
| Lokale Git-Abweichung | Bei Inventur: `git status` zeigte u. a. `M docs&#47;ops&#47;MERGE_LOG_WORKFLOW.md`, `M docs&#47;ops&#47;README.md` — **unklar**, ob nur lokal; für „reiner main“-Stand ggf. prüfen/stashen. |

---

## 3. Source of Truth Map

| Artefakt | Rolle |
|----------|--------|
| `src&#47;webui&#47;ops_cockpit.py` | Builder, HTML, Observation-Aggregate, Operator Summary, Karten-Helper. |
| `src&#47;webui&#47;app.py` | Routing `&#47;ops`, `&#47;api&#47;ops-cockpit`. |
| `docs&#47;ops&#47;specs&#47;OPS_COCKPIT_PAYLOAD_READ_MODEL_CONTRACT.md` | Top-Level-Keys von `build_ops_cockpit_payload`; Verweis auf Summary-Surface und RV-Coverage. |
| `docs&#47;ops&#47;specs&#47;OPS_COCKPIT_OPERATOR_SUMMARY_SURFACE.md` | Payload ↔ HTML-Blöcke, `id`-Namen, Phase-E-Hinweise. |
| `docs&#47;ops&#47;specs&#47;OPS_COCKPIT_VNEXT_REQUIRED_VIEWS_COVERAGE.md` | RV1–7 ↔ Keys / HTML / Tests (Traceability-Matrix). |
| `docs&#47;DASHBOARD_COMPLETION_MASTER_CHECKLIST.md` | Meta-Checkliste inkl. Links zu Contract + RV-Coverage. |
| `tests&#47;webui&#47;test_ops_cockpit.py` | Breite HTML-/Payload-Regression. |
| `tests&#47;ops&#47;test_ops_cockpit_payload_top_level_contract.py` | Stabile Key-Menge (ohne Value-Snapshots). |
| Weitere Docs | Viele Runbooks `docs&#47;ops&#47;runbooks&#47;webui_ops_cockpit*.md`, Reviews unter `docs&#47;ops&#47;reviews&#47;…ops_cockpit…`. | <!-- pt:ref-target-ignore -->

---

## 4. Implemented Surfaces / Cards / Views

### 4.1 Payload-/Themenbereiche (Auszug — Contract)

`OPS_COCKPIT_PAYLOAD_READ_MODEL_CONTRACT.md` listet u. a.:
`truth_state`, `runtime_unknown_state`, `run_state`, `session_end_mismatch_state`, `transfer_ambiguity_state`, `stale_state`, `incident_state`, `dependencies_state`, `evidence_state`, `exposure_state`, `policy_state`, `guard_state`, `workflow_officer_state`, `update_officer_ui`, `phase83_eligibility_snapshot`, diverse `*_observation`-Keys, `safety_state`, `executive_summary`, `source_groups`, …

### 4.2 Stabile HTML-`id`s (gesichert via `rg 'id="' src&#47;webui&#47;ops_cockpit.py`)

**Operator Summary (Auswahl):**
`operator-summary-preamble`, `operator-summary-system-status`, `operator-summary-system-state-observation`, `operator-summary-phase83-eligibility`, `operator-summary-go-no-go-not-approval`, `operator-summary-policy-go-no-go-observation`, `operator-summary-operator-state`, `operator-summary-safety-posture-observation`, `operator-summary-safety-state-projection`, `operator-summary-governance-boundary-observation`, `operator-summary-workflow-officer`, `operator-summary-update-officer`, `operator-summary-phase57-snapshot-discoverability`, `operator-summary-run-session-observation`, `operator-summary-run-state`, `operator-summary-session-end-mismatch`, `operator-summary-transfer-ambiguity`, `operator-summary-stale-signals`, `operator-summary-health-drift-observation`, `operator-summary-dependencies-artifact-observations`, `operator-summary-exposure-risk-observation`, `operator-summary-exposure-state`, `operator-summary-balance-semantics`, `operator-summary-incident-safety-observation`, `operator-summary-incident-observation-read-only`, `operator-summary-evidence-audit-observation`, `operator-summary-evidence-freshness-observation-read-only`, `operator-summary-truth-state`, `operator-summary-truth-sources-runtime`, `operator-summary-status-at-a-glance`, `operator-summary-policy-governance-rv6`, …

**Weitere Oberflächen:**
`policy-governance-observation-surface`, `operator-workflow-observation-surface`, `operator-workflow-handoff-preview-observation`, `phase83-strategy-eligibility-card`, `phase57-live-snapshot-endpoints-card`, `incident-observed-rollup-observation-card`, `run-state-observation-card`, `update-officer-visibility-card`, …

**Haupt-Grid (`render_ops_cockpit_html`, Auszug):**
`truth-state-observation-card`, `runtime-unknown-state-observation-card`, `exposure-state-observation-card`, `transfer-ambiguity-observation-surface`, `stale-state-observation-card`, `balance-semantics-observation-card`, `session-end-mismatch-observation-surface`, `evidence-state-card`, `dependencies-state-observation-card`, `incident-state-read-model-observation-card`.

**Hinweis:** Es gibt weiterhin `<div class="card truth-card">` **ohne** äußeres `id` an mehreren Stellen (z. B. Policy-/Workflow-Innenlayouts, `_render_doc_card`, `_render_group_summary_block`) — **vollständige Liste der „fehlenden“ Anker** wäre eine eigene grep-Passage; hier nur qualitativ benannt.

---

## 5. Test Coverage Snapshot

| Testdatei | Zweck (Evidenz) |
|-----------|------------------|
| `tests&#47;webui&#47;test_ops_cockpit.py` | Viele Funktionen prüfen HTML-Strings, Operator-Summary-`id`s, Karteninhalte, Randfälle (`stale_state.order`, Registry, …). **139** `def test_*` in dieser Datei (Inventur). |
| `tests&#47;ops&#47;test_ops_cockpit_payload_top_level_contract.py` | Feste Top-Level-Key-Menge für Payload. |
| `tests&#47;webui&#47;test_ops_cockpit_api_json_contract.py` | (Datei existiert laut `find`; Details nicht im Detail gelesen — **für API-JSON-Kontrakt**). |

**Interpretation:** Abdeckung ist für Cockpit **breit** auf WebUI-Ebene; vollständige Coverage-Metriken (coverage.py) wurden **nicht** eingeholt.

---

## 6. Docs Coverage Snapshot

- **Kanonisch (3 Dateien):** `OPS_COCKPIT_*.md` unter `docs&#47;ops&#47;specs&#47;` (siehe Abschnitt 3).
- **Runbooks:** Mehrere Versionen `webui_ops_cockpit_v2_*_truth_first.md` + Basis `webui_ops_cockpit.md` — potenziell **Versionsdrift** zwischen Runbook-Versionen und aktuellem Code; **nicht** Zeile für Zeile verglichen in dieser Inventur.
- **Checkliste:** `DASHBOARD_COMPLETION_MASTER_CHECKLIST.md` verknüpft RV-Coverage und Contract — explizit **keine** Produktfreigabe.

---

## 7. Recent Change History

**Gesichert:** `git log --oneline -n 15 -- src&#47;webui&#47;ops_cockpit.py` (Auszug):

- `b5109aa6` feat(ops-cockpit): add html ids for truth and runtime main cards (#2581)
- `26e24016` feat(ops-cockpit): add html id for incident state read model main card (#2580)
- `c9b2f832` feat(ops-cockpit): add html id for incident observed rollup main card (#2579)
- `917d2b6f` feat(ops-cockpit): add html id for run state main card (#2578)
- `4cce3615` feat(ops-cockpit): add html id for dependencies state main card (#2577)
- `f5f0364b` feat(ops-cockpit): add html id for exposure state main card (#2576)
- `7b864334` feat(ops-cockpit): add html id for stale state main card (#2575)
- `ba9a2b13` feat(ops-cockpit): add html id for balance semantics main card (#2574)
- `921c01c4` feat(ops-cockpit): add html id for phase57 main card (#2573)
- `02e9232e` feat(ops-cockpit): add html id for phase83 main card (#2572)
- `790f695a` feat(ops-cockpit): add stable summary anchor for operator summary preamble (#2571)
- `9940e978` feat(ops-cockpit): add stable summary anchor for status at a glance (#2570)
- …

Ältere Commits auf `main`, die nur `docs&#47;` betreffen, erscheinen im breiteren `git log` mit Pfad `docs` — nicht alle sind Cockpit-spezifisch.

---

## 8. Gaps / Unclear Areas

**Gesichert / strukturell:**

- Nicht jede **innere** Karte oder jeder **Hilfsblock** hat ein äußeres stabiles `id` (z. B. einige `card truth-card` ohne `id` in `ops_cockpit.py`).
- **Runbooks** in mehreren Versionen (`v2_1` … `v2_9`) vs. eine „aktuelle“ Wahrheit — **Versionsabgleich** mit `OPS_COCKPIT_OPERATOR_SUMMARY_SURFACE.md` ist **unklar auf Basis der aktuellen Repo-Evidenz** ohne manuelles Review.

**Interpretation (gekennzeichnet):**

- „Nächste größere Scheibe“ könnte **HTML-Anker für verbleibende Haupt- oder Hilfsflächen** sein *oder* **Konsolidierung/Deprecation älterer Runbook-Versionen** — Produktentscheid, nicht aus dem Code allein ableitbar.

---

## 9. Recommended Next Larger Slice (nur Empfehlung — keine Umsetzung)

**Empfehlung (analytisch, aus vorheriger Slice-Reihe und verbleibenden `card`-Wrappers):**

1. **Inventar + gezielte `id`s** für verbleibende **sichtbare** Cockpit-Blöcke oberhalb/unterhalb des Grids, die noch **kein** äußeres `id` haben (z. B. „Compact Source Summary“ / `group-block`, einzelne **Policy-Governance**-Innenkarten), *sofern* die Surface-Doku dieselbe Traceability erwartet — zuerst **grep-basierte Lückenliste**, dann kleine PRs.

2. Alternativ (docs-only, größerer redaktioneller Aufwand): **Runbook-Konsolidierung** (`webui_ops_cockpit_v2_*.md`) mit klarer „current“-Kennzeichnung — **nur** wenn das Team explizit Doc-Drift reduzieren will.

---

## Anhang: Brief-Datei für Multi-Agent

Der Auftraggeber-Brief liegt unter:

`&#47;tmp&#47;peak_trade_ops_cockpit_status_readonly&#47;CURSOR_MULTI_AGENT_BRIEF.md`
