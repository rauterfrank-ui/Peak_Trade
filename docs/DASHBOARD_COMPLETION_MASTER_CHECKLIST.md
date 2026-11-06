# Dashboard — Master-Checkliste (Vollständigkeit)

**Status:** Referenz / Planungsüberblick  
**Letzte Aktualisierung:** 2026-04-13  
**Zweck:** Eine **kombinierte** Checkliste für „Dashboard“-Arbeit im Repo — ohne eine einzelne technische „fertig“-Definition vorzugeben (mehrere parallele Spuren).

**Hinweis:** Im Peak_Trade-Repo gibt es **kein** monolithisches „das eine Dashboard“, sondern u. a. **R&D-Dashboard (Phase 76)**, **OPS Suite / Dashboard vNext** und das **bestehende Web-Dashboard** (`src/webui/`). Priorität und Scope vor Umsetzung festlegen.

**Kanonische Quellen (vertiefen):**

- R&D Dashboard v0: [`PHASE_76_R_AND_D_DASHBOARD_V0_DESIGN.md`](PHASE_76_R_AND_D_DASHBOARD_V0_DESIGN.md)
- OPS vNext Spec: [`ops&#47;specs&#47;OPS_SUITE_DASHBOARD_VNEXT_SPEC.md`](ops&#47;specs&#47;OPS_SUITE_DASHBOARD_VNEXT_SPEC.md)
- OPS vNext Plan (Phasen A–E): [`ops&#47;runbooks&#47;RUNBOOK_OPS_SUITE_DASHBOARD_VNEXT_PLAN.md`](ops&#47;runbooks&#47;RUNBOOK_OPS_SUITE_DASHBOARD_VNEXT_PLAN.md)
- OPS vNext Required Views ↔ Cockpit (Traceability): [`ops&#47;specs&#47;OPS_COCKPIT_VNEXT_REQUIRED_VIEWS_COVERAGE.md`](ops&#47;specs&#47;OPS_COCKPIT_VNEXT_REQUIRED_VIEWS_COVERAGE.md)
- Phase E Governance Review: [`ops&#47;runbooks&#47;RUNBOOK_OPS_SUITE_PHASE_E_GOVERNANCE_REVIEW.md`](ops&#47;runbooks&#47;RUNBOOK_OPS_SUITE_PHASE_E_GOVERNANCE_REVIEW.md)
- Docs-Registry / Drift-Kontext: [`ops&#47;registry&#47;DOCS_TRUTH_MAP.md`](ops&#47;registry&#47;DOCS_TRUTH_MAP.md)

---

## 1. Scope klären (einmalig)

- [ ] **Zielbild:** Nur R&D v0, nur OPS vNext, oder beides — **Priorität** festlegen.
- [ ] **Non-Goals** der jeweiligen Spec/Runbooks einhalten (z. B. keine Execution-Autorität im UI, keine Gate-Abschwächung — siehe vNext-Dokumente).
- [ ] **Read-Model / APIs** vor UI-Polish: truth-first, reproduzierbare Payloads.

---

## 2. OPS Suite / Dashboard vNext (Runbook-Phasen)

Entspricht grob [`RUNBOOK_OPS_SUITE_DASHBOARD_VNEXT_PLAN.md`](ops&#47;runbooks&#47;RUNBOOK_OPS_SUITE_DASHBOARD_VNEXT_PLAN.md) und den „Required Views“ in [`OPS_SUITE_DASHBOARD_VNEXT_SPEC.md`](ops&#47;specs&#47;OPS_SUITE_DASHBOARD_VNEXT_SPEC.md). **Traceability Required Views §1–7 ↔ Cockpit:** [`OPS_COCKPIT_VNEXT_REQUIRED_VIEWS_COVERAGE.md`](ops&#47;specs&#47;OPS_COCKPIT_VNEXT_REQUIRED_VIEWS_COVERAGE.md) (repo-belegt; **keine** Vollständigkeits-Freigabe).

Die folgenden Checkboxen spiegeln den **Ist-Stand der read-only Ops-Cockpit-Linie** (Payload + `&#47;ops` HTML + Tests) nach den gelieferten Phasen **nicht** eine externe Produktfreigabe wider.

- [x] **Phase A — Discovery:** Inhaltlich durch die inventarisierten Payload-/Surface-Mappings in Operator Summary Surface, Payload-Contract und Runbook **Ist-Stand** abgedeckt (fortlaufend im Repo gepflegt).
- [x] **Phase B — Read-Model-Contract:** Top-Level-Contract für `build_ops_cockpit_payload`: [`OPS_COCKPIT_PAYLOAD_READ_MODEL_CONTRACT.md`](ops&#47;specs&#47;OPS_COCKPIT_PAYLOAD_READ_MODEL_CONTRACT.md); Test-Anker `tests&#47;ops&#47;test_ops_cockpit_payload_top_level_contract.py`.
- [x] **Phase C — UI:** Read-only Cockpit-Oberflächen aligned zu den Required Views (siehe Coverage-Matrix und Operator Summary Surface); **keine** neuen Write- oder Unlock-Aktionen.
- [x] **Phase D — Build:** Read-only zuerst; WebUI-/Contract-Tests vor bedienbaren Operator-Aktionen (keine Cockpit-POST-Workflows in dieser Linie).
- [x] **Phase E — Governance Review:** [`RUNBOOK_OPS_SUITE_PHASE_E_GOVERNANCE_REVIEW.md`](ops&#47;runbooks&#47;RUNBOOK_OPS_SUITE_PHASE_E_GOVERNANCE_REVIEW.md) — Interpretation vs. Autorität; kanonische Anker.

**Empfohlene Branch-Folge** (Runbook, geliefert als Merge-Reihenfolge der Ops-Slices — siehe [`RUNBOOK_OPS_SUITE_DASHBOARD_VNEXT_PLAN.md`](ops&#47;runbooks&#47;RUNBOOK_OPS_SUITE_DASHBOARD_VNEXT_PLAN.md)):

1. `feat/ops-suite-read-model-contract`  
2. `feat/ops-suite-system-policy-surface`  
3. `feat/ops-suite-incident-risk-surface`  
4. `feat/ops-suite-operator-workflow-visibility`  
5. `feat/ops-suite-phase-e-governance-review`  
6. `feat/ops-suite-vnext-coverage-matrix` (docs-only: diese Traceability-Matrix + Checklisten-Sync)

- [x] **Branch 6 (Runbook) — docs-only:** Required-Views-Coverage-Matrix [`OPS_COCKPIT_VNEXT_REQUIRED_VIEWS_COVERAGE.md`](ops&#47;specs&#47;OPS_COCKPIT_VNEXT_REQUIRED_VIEWS_COVERAGE.md) und diese Checkliste mit Ist-Code/Operator Summary zu **`stale_state.order`** / **`order_staleness_reader`** synchron gehalten ([`RUNBOOK_OPS_SUITE_DASHBOARD_VNEXT_PLAN.md`](ops&#47;runbooks&#47;RUNBOOK_OPS_SUITE_DASHBOARD_VNEXT_PLAN.md) Schritt 6). **Keine** Vollständigkeits- oder Produktfreigabe; nur Traceability.

---

## 3. R&D Dashboard v0 (Phase 76 — Auszug Definition of Done)

Siehe Milestones/DoD in [`PHASE_76_R_AND_D_DASHBOARD_V0_DESIGN.md`](PHASE_76_R_AND_D_DASHBOARD_V0_DESIGN.md).

- [x] Read-only **Listen-API** + defensive Read-Model-Schicht für lokale JSONs
      (`GET /api&#47;r_and_d&#47;experiments`, `src&#47;r_and_d&#47;experiments_read_model.py`) — Slice 1;
      Filter + `sort_by`/`sort_order`; keine Write-/Trigger-Routen.
- [x] Summary-/Overview-HTML: `GET &#47;r_and_d&#47;summary` mit gleicher Semantik wie `GET /api&#47;r_and_d&#47;summary` und `GET /api&#47;r_and_d&#47;stats` (bestehende Helfer; keine neuen API-Felder) — Phase 76 Slice 6.
- [x] List View: GET-Query-Parität zur Listen-API (Filter/Sort/Limit/Datum, read-only) — Phase 76 slice 2; weiterer UI-Ausbau optional.
- [x] Experiment-Detail inkl. Metriken + JSON-Rohsicht — read-only HTML `GET &#47;r_and_d&#47;experiments&#47;{run_id}` (Alias `&#47;r_and_d&#47;experiment&#47;{run_id}`); API `GET /api&#47;r_and_d&#47;experiments&#47;{run_id}` — Phase 76 slice 4.
- [x] Aggregationen (Preset / Strategy): read-only HTML (`GET &#47;r_and_d&#47;presets`, `GET &#47;r_and_d&#47;strategies`) aligned zu den bestehenden JSON-Endpunkten — Phase 76 slice 3.
- [x] Mind. zwei Charts: read-only HTML `GET &#47;r_and_d&#47;charts` (Sharpe-Histogramm, Total Return vs. Sharpe) — Phase 76 slice 5.
- [x] Tests + Doku für Slice 5 ergänzt (bestehende R&D-API-Testsuite erweitert).
- [x] Tests + Doku für Slice 6 (Summary-HTML) ergänzt.
- [x] Today-/Running-HTML: `GET &#47;r_and_d&#47;today` und `GET &#47;r_and_d&#47;running` mit gleicher Semantik wie die JSON-APIs — Phase 76 Slice 7.
- [x] Tests + Doku für Slice 7 ergänzt.
- [x] Categories-HTML: `GET &#47;r_and_d&#47;categories` mit gleicher Semantik wie `GET /api&#47;r_and_d&#47;categories` — Phase 76 Slice 8.
- [x] Tests + Doku für Slice 8 ergänzt.
- [x] Listen-HTML: `GET &#47;r_and_d&#47;experiments` dieselbe read-only Ansicht wie `GET &#47;r_and_d` (kein neues API) — Phase 76 Slice 9.
- [x] Tests + Doku für Slice 9 ergänzt.
- [x] R&D-HTML: primäre Zurück-/Hub-Links auf kanonische Listen-URL `GET &#47;r_and_d&#47;experiments` — Phase 76 Slice 10.
- [x] Tests + Doku für Slice 10 ergänzt.
- [x] Globale Web-Nav + Preset-/Strategy-Drilldown: kanonische Listen-URL `GET &#47;r_and_d&#47;experiments` — Phase 76 Slice 11.
- [x] Tests + Doku für Slice 11 ergänzt.

**Stand R&D Dashboard v0 read-only (Phase 76):** Die Checkboxen oben beschreiben den **gelieferten** Umfang (Slices 1–11). Er entspricht der **read-only**-Zielsetzung in [`PHASE_76_R_AND_D_DASHBOARD_V0_DESIGN.md`](PHASE_76_R_AND_D_DASHBOARD_V0_DESIGN.md) (§4.1.1). **Keine** darüber hinausgehende „Produktfertig“-Behauptung.

**Optional / später (nicht Teil des v0-DoD):** u. a. Listen-Pagination, zusätzliche Charts (z. B. Boxplot laut Design-Skizze), weiteres UI-Polish — siehe **Backlog** in [`PHASE_76_R_AND_D_DASHBOARD_V0_DESIGN.md`](PHASE_76_R_AND_D_DASHBOARD_V0_DESIGN.md) §4.1.2.

---

## 4. Querschnitt (empfohlen)

- [ ] Bei Doc-Änderungen: Referenz-Targets und Docs-Token-Policy einhalten (`scripts/ops/` — z. B. `verify_docs_reference_targets.sh`, Token-Validator).
- [ ] Smoke: kritische Web-Routen lokal prüfen, wenn UI geändert wird.
- [ ] Observability: Grafana-/Dashboard-Artefakte versioniert halten, wo Runbooks das verlangen.

---

## 5. Größenordnung (Planung, keine Garantie)

| Paket | Grobe Größenordnung |
|--------|---------------------|
| R&D Dashboard v0 (Design-Tabelle ~14 h reine Implementierung) | Wenige Tage bis ~2 Wochen Kalenderzeit (je nach Parallelität und Review) |
| OPS vNext „kernnutzbar“ (read-only, mehrere Flächen) | Mehrere Wochen |
| OPS vNext „Spec umfassend abgebildet“ + Governance | Typisch Monat(e) |

Diese Zeilen sind **Orientierung**, kein Festpreis — abhängig von Team, Scope-Schnitten und parallelen Arbeiten.

---

## docs_token

`DOCS_TOKEN_DASHBOARD_COMPLETION_MASTER_CHECKLIST`
