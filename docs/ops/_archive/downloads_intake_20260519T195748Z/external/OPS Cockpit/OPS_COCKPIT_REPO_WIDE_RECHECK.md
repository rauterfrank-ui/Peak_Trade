# OPS Cockpit — Repo-weite Gegenprüfung (read-only)

**Erstellt:** Audit auf Basis von `main` im Repo `&#47;Users&#47;frnkhrz&#47;Peak_Trade` (Session).
**Modus:** rein informativ — keine Codeänderungen durch dieses Dokument.

**Hinweis zur Ausgangslage:** Der Brief verweist auf `&#47;mnt&#47;data&#47;OPS_COCKPIT_STATUS_SUMMARY.md` — **auf diesem System existiert dieser Pfad nicht** (`No such file or directory`). Eine frühere Summary liegt unter `&#47;tmp&#47;peak_trade_ops_cockpit_status_readonly&#47;OPS_COCKPIT_STATUS_SUMMARY.md` (falls vorhanden). Diese Gegenprüfung ist **unabhängig** neu aus dem Repo abgeleitet.

**Git (Session):** `main...origin&#47;main`; lokale Änderungen ohne Commit wurden u. a. an `docs&#47;ops&#47;MERGE_LOG_WORKFLOW.md` und `docs&#47;ops&#47;README.md` gesehen — **unklar**, ob nur lokal relevant.

---

## 1. Executive Summary

**Gesicherte Evidenz:** Das OPS Cockpit (`build_ops_cockpit_payload`, `render_ops_cockpit_html` in `src&#47;webui&#47;ops_cockpit.py`) ist die zentrale **read-only** Truth-/Operator-Leseansicht unter **`GET &#47;ops`** und **`GET &#47;api&#47;ops-cockpit`** (`src&#47;webui&#47;app.py`). Der **Top-Level-Payload** ist durch `docs&#47;ops&#47;specs&#47;OPS_COCKPIT_PAYLOAD_READ_MODEL_CONTRACT.md`, `tests&#47;ops&#47;test_ops_cockpit_payload_top_level_contract.py` und `tests&#47;webui&#47;test_ops_cockpit_api_json_contract.py` auf **39 Schlüssel** festgehalten; Test und HTTP-Contract fordern **exakt** dieselbe Key-Menge wie der Builder.

**Architektur:** Das Repo enthält **weitere** Web-Oberflächen unter `&#47;ops&#47;*`, die **nicht** identisch mit dem Cockpit sind: u. a. `ops_workflows_router` (`&#47;ops&#47;workflows`), `ops_ci_health_router` (`&#47;ops&#47;ci-health`), `ops_stage1_router` (`&#47;ops&#47;stage1`) — jeweils eigene Router-Dateien unter `src&#47;webui&#47;`. Die **Master-Checkliste** (`docs&#47;DASHBOARD_COMPLETION_MASTER_CHECKLIST.md`) stellt **R&D-Dashboard**, **OPS vNext** und **Web-Dashboard** bewusst **nebeneinander** (kein monolithisches „ein Dashboard“).

**Interpretation:** Ein „Drift“ zwischen „ganzem Repo“ und Cockpit ist **kein Bug per se**, solange das Cockpit nicht alle parallelen Surfaces spiegeln soll. Belastbare **Restlücken** im Cockpit selbst: einige **HTML-Wrapper ohne stabiles `id`** (konkrete Zeilennummern unten); **Runbook-Versionen** (`webui_ops_cockpit_v2_*.md`) vs. eine kanonische Surface-Datei — **vollständiger Abgleich** in dieser Session **nicht** zeilenweise erfolgt (**unklar auf Basis der aktuellen Repo-Evidenz** ohne manuelles Lesen aller Runbooks).

---

## 2. Current Cockpit vs Repo Alignment

| Thema | Repo kann (Evidenz) | Cockpit zeigt / API |
|--------|---------------------|---------------------|
| Payload Top-Level | `build_ops_cockpit_payload` aggregiert u. a. `truth_state`, `runtime_unknown_state`, `run_state`, `session_end_mismatch_state`, `transfer_ambiguity_state`, `stale_state`, `incident_state`, `dependencies_state` (inkl. verschachtelter Observations), `evidence_state`, `exposure_state`, `policy_state`, `guard_state`, `workflow_officer_state`, `update_officer_ui`, `phase83_eligibility_snapshot`, diverse `*_observation` | Gleiches Objekt unter `&#47;api&#47;ops-cockpit` und in `&#47;ops` HTML (Builder wird in `render_ops_cockpit_html` aufgerufen). |
| Parallele Ops-UIs | Separate Router: Workflows, CI-Health, Stage1 | **Nicht** Teil der Cockpit-Seite; **keine** automatische Spiegelung im Cockpit erwartet (architektonisch getrennt). |
| R&D / Experiments | Eigene Spuren (`src&#47;r_and_d&#47;`, R&D-Dashboard-Spec in Checkliste) | **Ausdrücklich nicht** OPS-Cockpit-Fokus laut Checkliste; Cockpit bleibt OPS-/truth-first-Linie. |
| Observability / Execution | Weitere Module unter `src&#47;execution`, `src&#47;live`, `src&#47;observability` | Cockpit **liest** nur über vorhandene Builder/Reader, die in `ops_cockpit.py` eingebunden sind — **kein** vollständiger Repo-weiter Export aller Observability-Features ohne Codeprüfung jedes Imports. | <!-- pt:ref-target-ignore -->

---

## 3. Confirmed Coverage

| Bereich | Evidenz |
|---------|---------|
| Top-Level-Keys | **39** Keys in `EXPECTED_OPS_COCKPIT_PAYLOAD_TOP_LEVEL_KEYS` (`tests&#47;ops&#47;test_ops_cockpit_payload_top_level_contract.py`); gleiche Menge wie in `OPS_COCKPIT_PAYLOAD_READ_MODEL_CONTRACT.md` (Abschnitt „Stable top-level key set“). |
| HTTP-JSON | `tests&#47;webui&#47;test_ops_cockpit_api_json_contract.py`: `test_api_ops_cockpit_json_contract_top_level_keys` — `set(data.keys()) == EXPECTED_OPS_COCKPIT_PAYLOAD_TOP_LEVEL_KEYS`. |
| Observation-Module `src&#47;ops&#47;` | Dateien u. a. `health_drift_observation.py`, `policy_go_no_go_observation.py`, `exposure_risk_observation.py`, … — werden über Payload/Builder im Cockpit genutzt (indirekt über `build_ops_cockpit_payload` / verschachtelte Keys). |
| HTML-`id`s (Hauptkarten + Summary) | Viele stabile `id="..."` in `src&#47;webui&#47;ops_cockpit.py` (u. a. `truth-state-observation-card`, `runtime-unknown-state-observation-card`, `operator-summary-truth-state`, `incident-state-read-model-observation-card`, …); jüngste Commits `#2556–#2581` (git log) dokumentieren gezielte Anker-PRs. |
| Traceability-Docs | `OPS_COCKPIT_OPERATOR_SUMMARY_SURFACE.md`, `OPS_COCKPIT_VNEXT_REQUIRED_VIEWS_COVERAGE.md`, `DASHBOARD_COMPLETION_MASTER_CHECKLIST.md` — konsistent **keine** Produktfreigabe, Fokus Traceability. |

---

## 4. Confirmed Gaps Requiring Change Now

**Streng genommen:** Kein **automatisch beweisbarer** „Showstopper“ (z. B. Payload-Test schlägt fehl) wurde in dieser read-only Session ausgeführt.

**Belastbare technische Restflächen (optional verbesserungsfähig, nicht zwingend „jetzt broken“):**

1. **HTML-Wrapper ohne äußeres `id`:** `rg` auf `ops_cockpit.py` findet u. a. Zeilen **1003, 1394, 3125, 3207, 3225** mit `<div class="card` bzw. `truth-card` **ohne** `id=` in derselben öffnenden Zeile — betrifft innere/ Hilfskarten (z. B. Policy-Governance-Innenlayout, Workflow-Innenkarte, Doc-Preview-Karten, Group-Summary-Blöcke). **Ob** das für eure Betriebs-/Link-Kanäle „muss“ geändert werden, ist **Prozessentscheid**, nicht aus dem Code allein ableitbar.

2. **Lokale Doc-Modifikationen:** `git status` zeigte geänderte `docs&#47;ops&#47;*` — **unklar**, ob `main` auf der Maschine „clean“ ist; für reproduzierbare Audits sollte `main` sauber sein.

**Interpretation:** „Muss geändert werden“ im Sinne von **Compliance-Krise** — **nicht** aus dieser statischen Prüfung ableitbar. „Könnte verbessert werden“ — siehe Abschnitt 5 und 8.

---

## 5. Candidate Additive Extensions

*(Nur plausible, additive Ideen mit Repo-Anker — keine Umsetzung.)*

| Priorität (subjektiv) | Vorschlag | Repo-Anker |
|------------------------|-----------|------------|
| Hoch | Verbleibende **sichtbare** Blöcke mit stabilem `id` versehen, wo Traceability/Docs dasselbe Muster wie bei Hauptkarten erwarten | Zeilen ohne `id` oben; Muster PRs `#2572–#2581` |
| Mittel | **Runbooks** `docs&#47;ops&#47;runbooks&#47;webui_ops_cockpit_v2_*.md`: eine „current“-Kennzeichnung oder Konsolidierung | Viele Dateien unter `docs&#47;ops&#47;runbooks&#47;`; **Drift** vs. `OPS_COCKPIT_OPERATOR_SUMMARY_SURFACE.md` nicht vollständig vermessen |
| Niedrig | Querverweise von parallelen Ops-Routern (Workflows/CI-Health) **in** der Cockpit-Doku als „ verwandte Oberflächen“ | `src&#47;webui&#47;ops_workflows_router.py`, `ops_ci_health_router.py`, `app.py` Mounts |

---

## 6. Docs / Tests / Contract Drift Check

| Prüfung | Ergebnis |
|---------|----------|
| Contract 39 Keys vs. Test | **Übereinstimmend** (Python-Zählung: `len(EXPECTED_…)=39`; Contract-Liste gleichlautend). |
| API-Test vs. Test-Fixture | **Identische** `EXPECTED_OPS_COCKPIT_PAYLOAD_TOP_LEVEL_KEYS`-Import. |
| Neue Payload-Keys ohne Doc/Test | **Würde** CI brechen, sobald `build_ops_cockpit_payload` Keys ändert ohne Anpassung von `EXPECTED_*` — **positiver** Drift-Schutz. |
| Runbooks vs. Code | **Nicht** vollständig zeilenweise verglichen — **unklar auf Basis der aktuellen Repo-Evidenz**. |

---

## 7. Recent Repo Signals Relevant To Cockpit

**Auszug `git log --oneline -n 25 -- src&#47;webui&#47;ops_cockpit.py`:** fortlaufende **`feat(ops-cockpit):`** PRs für HTML-Anker (#2556–#2581), zuletzt Truth/Runtime-Hauptkarten (#2581).

**Interpretation:** Aktive Pflegelinie = **Discoverability/Traceability** (IDs), nicht Umstellung des Payload-Schemas.

---

## 8. Recommended Next Larger Slice

**Empfehlung (analytisch, konsistent mit bisheriger Reihe):**

1. **Inventory-Grep:** alle `<div class="card` in `render_ops_cockpit_html` / Hilfsrenderern **ohne** `id` auflisten, priorisieren nach Sichtbarkeit (über dem Fold / im Haupt-Grid).
2. **Kleine PRs:** pro Blöckchen stabiles `id` + ein Test + Doku-Zeile in `OPS_COCKPIT_OPERATOR_SUMMARY_SURFACE.md` / RV-Coverage — gleiches Muster wie PRs #2572–#2581.

**Nicht** empfohlen ohne separates Produkt-OK: Cockpit zu einem „Super-Dashboard“ für **alle** `&#47;ops&#47;*`-Router zusammenzuziehen — widerspricht der expliziten **Multi-Dashboard**-Beschreibung in `DASHBOARD_COMPLETION_MASTER_CHECKLIST.md`.

---

## 9. Appendix: Evidence Table

| Artefakt | Pfad / Symbol |
|----------|----------------|
| Payload-Builder | `src&#47;webui&#47;ops_cockpit.py` — `build_ops_cockpit_payload` (ca. Zeile 2408) |
| HTML-Renderer | `src&#47;webui&#47;ops_cockpit.py` — `render_ops_cockpit_html` (ca. Zeile 3758) |
| Routen | `src&#47;webui&#47;app.py` — `ops_cockpit`, `ops_cockpit_api` (~2019–2061) |
| Key-Contract (Doc) | `docs&#47;ops&#47;specs&#47;OPS_COCKPIT_PAYLOAD_READ_MODEL_CONTRACT.md` |
| Operator Summary (Doc) | `docs&#47;ops&#47;specs&#47;OPS_COCKPIT_OPERATOR_SUMMARY_SURFACE.md` |
| RV-Coverage (Doc) | `docs&#47;ops&#47;specs&#47;OPS_COCKPIT_VNEXT_REQUIRED_VIEWS_COVERAGE.md` |
| Master-Checkliste | `docs&#47;DASHBOARD_COMPLETION_MASTER_CHECKLIST.md` |
| Payload-Test | `tests&#47;ops&#47;test_ops_cockpit_payload_top_level_contract.py` — `EXPECTED_OPS_COCKPIT_PAYLOAD_TOP_LEVEL_KEYS`, `test_build_ops_cockpit_payload_top_level_keys_contract` |
| API-JSON-Test | `tests&#47;webui&#47;test_ops_cockpit_api_json_contract.py` — `test_api_ops_cockpit_json_contract_top_level_keys` |
| WebUI-Regression | `tests&#47;webui&#47;test_ops_cockpit.py` — viele `test_ops_cockpit_*` |
| Parallel Ops Router | `src&#47;webui&#47;ops_workflows_router.py`, `ops_ci_health_router.py`, `ops_stage1_router.py` |
| Cockpit-Mode-String | `src&#47;webui&#47;ops_cockpit.py` — `"truth_first_ops_cockpit_v3"` (u. a. Zeile 332, 2912) |
| HTML ohne `id` (Stichprobe) | `src&#47;webui&#47;ops_cockpit.py` Zeilen **1003, 1394, 3125, 3207, 3225** |
| Brief (Multi-Agent) | `&#47;tmp&#47;peak_trade_ops_cockpit_repo_recheck&#47;CURSOR_MULTI_AGENT_BRIEF.md` |

---

*Ende der Gegenprüfung.*
