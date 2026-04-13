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

---

## 3. R&D Dashboard v0 (Phase 76 — Auszug Definition of Done)

Siehe Milestones/DoD in [`PHASE_76_R_AND_D_DASHBOARD_V0_DESIGN.md`](PHASE_76_R_AND_D_DASHBOARD_V0_DESIGN.md).

- [ ] Backend-Service bzw. Anbindung + API für Experimente und Summarys.
- [ ] List View + Filter (an CLI-Logik angelehnt).
- [ ] Experiment-Detail inkl. Metriken + JSON-Rohsicht.
- [ ] Aggregationen (Preset / Strategy).
- [ ] Mind. zwei Charts (z. B. Sharpe-Verteilung, Sharpe vs. Return).
- [ ] Tests (Design nennt u. a. mind. zehn API-Tests) + Doku aktualisieren.

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
