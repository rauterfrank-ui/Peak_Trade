# Drift Cleanup Plan v1

**Status:** PLAN ONLY — keine Ausführung in diesem Slice  
**Erzeugt:** 2026-07-05  
**Branch:** `main` @ `2f1672bee8761f8d50def3f6ef31cc803824b2e9`  
**Inputs:**

- [`docs&#47;audit/feature_drift_reconciliation_report_v1.md`](../audit/feature_drift_reconciliation_report_v1.md) <!-- pt:ref-target-ignore -->
- [`docs&#47;governance/feature_state_map_v1.md`](feature_state_map_v1.md) <!-- pt:ref-target-ignore -->

**Scope:** READ-ONLY Analyse + Plan-Generierung. Keine Code-, Runtime-, CI- oder Wiring-Mutation.

---

## 1. Zweck

Dieser Plan transformiert die Feature State Map und den Drift-Report in eine **geordnete, ausführbare Docs-Alignment-Roadmap**. Er beschreibt nur **minimale sichere Dokumentations-Schritte** — keine automatische Authority-Auflösung, keine Feature-Deaktivierung, keine Code-Refactors.

### Klassifikations-Schema (pro Inkonsistenz)

| Klasse | Bedeutung | Ausführung in diesem Plan |
|--------|-----------|---------------------------|
| **SAFE DOC FIX** | Rename, Redirect, Link-Update, historischer Banner — kein Architektur-Urteil | Section A — ordered steps |
| **STRUCTURAL DOC DRIFT** | Docs müssen Architektur-Entscheidung oder Owner-Split explizit machen | Section B — flagged only |
| **BLOCKED** | Abhängig von Runtime-/Strategy-/Registry-Authority — nicht durch Docs allein lösbar | Section C / D |

### Strict Rules (verbindlich)

- Keine Code- oder Runtime-Logik-Änderung in diesem Plan
- Keine automatische Auflösung von Authority-Konflikten
- Keine Feature-Löschung oder Deaktivations-Annahme
- Nur beschreiben, nicht implementieren

---

## 2. DOC-01 bis DOC-12 — Gruppierung und Klassifikation

### 2.1 Typ a) Naming duplication

| ID | Stale / Duplicate | Canonical | Klasse | Begründung |
|----|-------------------|-----------|--------|------------|
| DOC-01 | `docs&#47;FEHLENDE_FEATURES_PEAK_TRADE.md` | `docs&#47;features/FEHLENDE_FEATURES_PEAK_TRADE.md` | **SAFE DOC FIX** | Root-Duplikat; Redirect-only ausreichend | <!-- pt:ref-target-ignore -->
| DOC-02 | `docs&#47;analysis/FEHLENDE_FEATURES_PEAK_TRADE.md` | `docs&#47;features/FEHLENDE_FEATURES_PEAK_TRADE.md` | **SAFE DOC FIX** | Analysis-Duplikat; Redirect-only | <!-- pt:ref-target-ignore -->
| DOC-09 | `el_karoui_vol_v1` in Legacy-Docs | `el_karoui_vol_model` | **SAFE DOC FIX** | Deprecation bereits in `registry.py`; nur Docs bereinigen |
| DOC-06 | `ecm_cycle` in `config&#47;config.toml` | `armstrong_cycle` in `registry.py` | **BLOCKED** | Config-Name vs Registry-ID — erfordert Governance-Entscheid (nicht nur Link) | <!-- pt:ref-target-ignore -->

### 2.2 Typ b) Stale references

| ID | Stale Reference | Canonical Truth | Klasse | Begründung |
|----|-----------------|-----------------|--------|------------|
| DOC-03 | `missing_features_plan.md` → `src&#47;features/pipeline.py` | ECM in `src&#47;strategies&#47;`; Feature-Engine deferred | **STRUCTURAL DOC DRIFT** | Plan beschreibt Zielarchitektur; Update braucht explizite „deferred“-Semantik | <!-- pt:ref-target-ignore -->
| DOC-04 | `REPO_AUDIT_REPORT.md` Feature-Matrix (Wave 16) | `feature_state_map_v1` + drift report v1 | **SAFE DOC FIX** | Historischer Snapshot; Banner + Crosslink |
| DOC-08 | `src&#47;docs&#47;peak_trade_documentation.md` → `ecm_cycle` | `registry.py` canonical IDs | **SAFE DOC FIX** | Einzelne Doku-Zeile; kein Registry-Urteil nötig | <!-- pt:ref-target-ignore -->
| DOC-10 | Feature-Engine ECM in älteren FEHLENDE-Kopien | Strategy-layer ECM konsolidiert | **SAFE DOC FIX** | Folgt aus DOC-01/02 Redirect + kanonischer Catalog-Pflege |
| DOC-12 | R&D „nicht implementiert“ in FEHLENDE-Kopien | Stubs in `src&#47;strategies&#47;` (ehlers, meta_labeling, bouchaud) | **STRUCTURAL DOC DRIFT** | Status-Gitter (stub vs missing) braucht einheitliche Docs-Grammatik | <!-- pt:ref-target-ignore -->

### 2.3 Typ c) Path drift (`src&#47;features/*` vs `strategies&#47;*`) <!-- pt:ref-target-ignore -->

| ID | Drift | Canonical | Klasse | Begründung |
|----|-------|-----------|--------|------------|
| DOC-05 | `DOCS_REFERENCE_TARGETS` → `src&#47;features` | `src&#47;strategies&#47;ecm.py` + deferred Feature-Engine | **SAFE DOC FIX** | JSON-Baseline-Target + Kommentar; kein Modul-Umzug | <!-- pt:ref-target-ignore -->
| DOC-07 | `docs&#47;features/psychology/` | `src&#47;reporting/psychology_*.py` | **SAFE DOC FIX** | Schicht-Umbenennung in Docs (Reporting, nicht Feature-Engine) | <!-- pt:ref-target-ignore -->
| DOC-10 | (siehe oben) | Strategy-layer ECM | **SAFE DOC FIX** | Path-Drift-Kernfall; mit DOC-01/02/05 gebündelt |

### 2.4 Typ d) Authority drift (ECM / cycle / registry / Double Play)

| ID | Drift | Canonical Authority | Klasse | Begründung |
|----|-------|---------------------|--------|------------|
| DOC-06 | `ecm_cycle` / `armstrong_cycle` / Config / functional loader | `armstrong_cycle` StrategySpec; `ecm.py` functional | **BLOCKED** | Registry-Alias vs Config-Migration — Operator-Entscheid |
| DOC-11 | Ops `evaluate_double_play` vs MV2 composition matrix | `double_play_composition_matrix_v1` (offline canonical) | **STRUCTURAL DOC DRIFT** | Authority-Marker in Ops-Docs verstärken; keine Runtime-Umverdrahtung |
| DOC-06 + WG-05 | (Wiring Gap) Config/Registry split | `STRATEGY_ECM_ARMSTRONG_WIRING_INVENTORY_READ_MODEL_V0` | **BLOCKED** | Bereits inventarisiert; Closure braucht Ratifikation |

---

## 3. Section A — Safe Documentation Fixes (ordered)

Ausführungsreihenfolge: **niedrigstes Risiko zuerst**, jede Stufe unabhängig revertierbar. Geschätzter Aufwand: **S** = kleiner Docs-PR.

| Step | ID | Aktion | Datei(en) | Minimale Änderung | Abhängigkeit |
|------|-----|--------|-----------|-------------------|--------------|
| **A-01** | DOC-04 | Historischer Banner + Crosslink | `docs&#47;audit/REPO_AUDIT_REPORT.md` | Banner „Historisch / Wave 16“; Link zu `feature_state_map_v1.md` und `feature_drift_reconciliation_report_v1.md` | Keine | <!-- pt:ref-target-ignore -->
| **A-02** | DOC-01 | Redirect-only | `docs&#47;FEHLENDE_FEATURES_PEAK_TRADE.md` | Inhalt auf ≤10 Zeilen: SUPERSEDED + Link zu `docs&#47;features/FEHLENDE_FEATURES_PEAK_TRADE.md` | Keine | <!-- pt:ref-target-ignore -->
| **A-03** | DOC-02 | Redirect-only | `docs&#47;analysis/FEHLENDE_FEATURES_PEAK_TRADE.md` | Gleiches Muster wie A-02 | A-02 (optional parallel) | <!-- pt:ref-target-ignore -->
| **A-04** | DOC-09 | Alias-Bereinigung in Docs | Alle Treffer `el_karoui_vol_v1` in `docs&#47;` (grep-gestützt) | Ersetzen durch `el_karoui_vol_model`; Deprecation-Hinweis wo Kontext es braucht | Keine | <!-- pt:ref-target-ignore -->
| **A-05** | DOC-08 | Stale loader map | `src&#47;docs&#47;peak_trade_documentation.md` | `ecm_cycle` → Hinweis auf `armstrong_cycle` + Link zu ECM wiring inventory | Keine Code-Änderung an Loader | <!-- pt:ref-target-ignore -->
| **A-06** | DOC-07 | Schicht-Relabel | `docs&#47;features/psychology/*.md` | Titel/Intro: „Reporting layer“; Crosslink `src&#47;reporting/psychology_*.py`; optional später `docs&#47;reporting/psychology/` (nur wenn Operator GO für Pfad-Move) | Keine | <!-- pt:ref-target-ignore -->
| **A-07** | DOC-05 | Reference target update | `docs&#47;ops/DOCS_REFERENCE_TARGETS_BASELINE.json` | `src&#47;features` Target: Kommentar „deferred“; zusätzlicher Target-Eintrag `src&#47;strategies&#47;ecm.py` (additiv, nicht ersetzend ohne Review) | Docs-token Policy Guard beachten | <!-- pt:ref-target-ignore -->
| **A-08** | DOC-10 | Kanonischer Catalog sync | `docs&#47;features/FEHLENDE_FEATURES_PEAK_TRADE.md` | §2/§6: ECM ✅ strategy layer; `src&#47;features/` explizit „placeholder / deferred“; kein Widerspruch zu A-02/A-03 | A-02, A-03 | <!-- pt:ref-target-ignore -->
| **A-09** | — | Index-Verankerung | `docs&#47;INDEX.md`, `docs&#47;governance/` README falls vorhanden | Links zu `feature_state_map_v1.md`, `drift_cleanup_plan_v1.md` | A-01–A-08 | <!-- pt:ref-target-ignore -->

**Section A Erfolgskriterium:** Ein Reviewer findet für FEHLENDE_FEATURES, ECM-Pfad, Psychology und El-Karoui-Naming **einen** kanonischen Einstieg ohne widersprüchliche „fehlt/implementiert“-Aussagen in den redirecteten Duplikaten.

---

## 4. Section B — Structural Drift Items (flagged, no action yet)

Diese Punkte erfordern **Architektur- oder Status-Grammatik-Entscheid**, nicht nur Link-Fixes. In diesem Plan: **nur markiert**.

| Flag | Quelle | Thema | Warum structural | Minimaler Docs-Ansatz (wenn GO) |
|------|--------|-------|------------------|--------------------------------|
| **B-01** | DOC-03, R-04 | Feature-Engine / `missing_features_plan.md` | Plan referenziert zukünftige `src&#47;features/pipeline.py` | Plan-Header „deferred“; Verweis auf `feature_state_map_v1` Class C | <!-- pt:ref-target-ignore -->
| **B-02** | DOC-12, CR-P2-03 | R&D Strategy Status (stub vs missing) | **CLOSED (2026-07-17)** — Status-Tabelle `stub`/`research-only`/`missing` in FEHLENDE + `rd_strategy_status_grammar_v0` | Grammar-Owner: `docs&#47;features&#47;rd_strategy_status_grammar_v0.json` + `src&#47;governance&#47;rd_strategy_status_grammar_v0.py` | <!-- pt:ref-target-ignore -->
| **B-03** | DOC-11, WG-07 | Double Play authority visibility | Ops evaluator vs MV2 matrix vs Decision Packet | Ops-Runbook-Abschnitt: `LEGACY_NON_AUTHORITATIVE` + Link `MASTER_V2_DECISION_AUTHORITY_MAP_V1` Slice E |
| **B-04** | WG-01 | Registry → Suitability → Replay sequence | Kein Default-Runtime-Wiring dokumentiert | Neues read-only Spec (analog ECM inventory): „Registry-Suitability-Replay Read Model v0“ |
| **B-05** | WG-02, WG-03, R-06 | Scope Capital / Risk / Sizing owner split | Runbook v2.6: 3 Owner; Code: merged in `capital_risk_sizing_v1` | Architecture design note: „merged by intent“ vs „gap“ — **kein** Owner-Urteil in Safe-Fixes |
| **B-06** | WG-07 | Decision Packet vs Integrated Replay | Zwei parallele MV2-Pfade in `master_v2&#47;__init__.py` exports | Decision-authority map Ergänzung: welcher Pfad canonical replay owner ist | <!-- pt:ref-target-ignore -->
| **B-07** | DOC-03 | `missing_features_plan.md` DAG | Veraltete Abhängigkeitskante Feature-Engine → alles downstream | DAG-Fußnote: Validation Rule NON-OPERATIONAL für nicht-Core-Features |

**Section B Regel:** Kein Schritt in Section B ohne explizites Operator-GO und ggf. separates Architecture-Review-Packet.

---

## 5. Section C — Authority Conflicts (ECM, cycles, registry ownership)

**Nicht automatisch auflösen.** Jeder Konflikt bleibt **BLOCKED** bis Governance-Ratifikation.

### C.1 ECM / cycle / registry triangle

| Konflikt-ID | Beobachtung | Betroffene Surfaces | Mögliche Resolution (nur als Optionen, nicht empfohlen) | Blocker |
|-------------|-------------|---------------------|--------------------------------------------------------|---------|
| **AUTH-ECM-01** | `armstrong_cycle` = StrategySpec; `ecm_cycle` = functional loader ID | `registry.py`, `config&#47;config.toml`, `ecm.py` | (a) Registry-Alias `ecm_cycle` → `armstrong_cycle` **oder** (b) Config-Migration zu `armstrong_cycle` **oder** (c) dokumentierte Dual-ID mit load-path matrix | Erfordert Code und/oder Config — **out of scope** | <!-- pt:ref-target-ignore -->
| **AUTH-ECM-02** | ECM math in `src&#47;strategies&#47;ecm.py` vs Armstrong class in `armstrong&#47;` | Docs, Backtest callers | Klären ob `ecm.py` = shared lib vs separate strategy | Semantik-Entscheid Operator | <!-- pt:ref-target-ignore -->
| **AUTH-ECM-03** | `DOCS_REFERENCE_TARGETS` verankert `src&#47;features` | CI docs gate | A-07 docs-only Teilantwort; volle Closure = AUTH-ECM-01 | Registry/Config truth | <!-- pt:ref-target-ignore -->

**Read-model (bereits vorhanden, nicht ersetzen):** `docs&#47;ops/specs/STRATEGY_ECM_ARMSTRONG_WIRING_INVENTORY_READ_MODEL_V0.md` <!-- pt:ref-target-ignore -->

### C.2 Double Play authority

| Konflikt-ID | Beobachtung | Canonical (frozen) | Blocker |
|-------------|-------------|-------------------|---------|
| **AUTH-DP-01** | `src&#47;ops/double_play/specialists.evaluate_double_play` | `double_play_composition_matrix_v1` + `integrated_offline_trading_logic_replay_v1` | Ops-Code bleibt; Docs dürfen nicht implizit Ops als authoritative darstellen | <!-- pt:ref-target-ignore -->
| **AUTH-DP-02** | `DoubleplayResolutionHandoffV1` (packet) vs runtime observations | Declarative handoff ≠ runtime mirror (`MASTER_V2_DECISION_AUTHORITY_MAP_V1` §95–101) | Packet/runtime sync = design change, nicht cleanup |

### C.3 Registry ownership / orphan modules

| Konflikt-ID | Beobachtung | Blocker |
|-------------|-------------|---------|
| **AUTH-REG-01** | `breakout_confirmation_v1.py` ohne `StrategySpec` | Registry-Eintrag vs experimental deprecation — Code-Entscheid |
| **AUTH-REG-02** | Functional IDs (`ecm_cycle`, `rsi_strategy`, `vol_breakout`, `mean_reversion_channel`) ohne vollständiges OOP-Spec | Alias-Policy vs promotion path |
| **AUTH-REG-03** | 23 Strategien „production“ in Registry, alle NON-OPERATIONAL per Validation Rule | Docs müssen NON-OPERATIONAL prominent machen; Registry-Tier ≠ Runtime operational |

**Section C Regel:** Cleanup-Plan **beschreibt** Konflikte; **löst** sie nicht. Nächster Schritt nach Operator-GO: separates „ECM Identity Decision Record“ (R-02 aus Drift-Report) — **Governance-Doc**, nicht Code.

---

## 6. Section D — Deferred Items (runtime truth resolution required)

Abhängig von Runtime-/Strategy-Truth — **keine Docs-Only-Closure möglich**.

| Defer-ID | Item | Abhängigkeit | Warum deferred |
|----------|------|--------------|----------------|
| **DEF-01** | Canonical Core Runtime Activation | `BOUND_NOT_ACTIVATED` Lift | Runtime GO + Evidence; nicht Drift-Cleanup |
| **DEF-02** | Strategy Library → Core auto-wiring (WG-01) | Suitability snapshot default path | Code/Runtime design |
| **DEF-03** | Scope Capital Replay integration (WG-02) | AUTH-B-05 architecture decision | Runbook owner vs code merge |
| **DEF-04** | Risk vs Sizing separate replay steps (WG-03) | `capital_risk_sizing_v1` semantics frozen | Architecture ratification |
| **DEF-05** | `breakout_confirmation_v1` disposition (WG-04) | AUTH-REG-01 | Code+Registry slice |
| **DEF-06** | Feature-Engine central layer (Class C) | Product/Roadmap priority | Bewusst deferred per KNOWN_LIMITATIONS |
| **DEF-07** | Meta-Labeling feature pipeline completion | R&D stub → implementation | Not docs cleanup |
| **DEF-08** | Live operational count > 0 | Full activation stack | Validation Rule: currently 0 |
| **DEF-09** | R-03 / R-06 / R-04 from drift report | Mix of code and architecture | Explicitly out of this plan's execution scope |

**Section D Regel:** Diese Items erscheinen in Docs nur als **„deferred — see feature_state_map_v1“**, nicht als erledigt.

---

## 7. Ausführungs-Matrix (Übersicht)

| ID | Typ | Klasse | Section | Ausführbar ohne Code? |
|----|-----|--------|---------|----------------------|
| DOC-01 | naming duplication | SAFE DOC FIX | A-02 | ✅ |
| DOC-02 | naming duplication | SAFE DOC FIX | A-03 | ✅ |
| DOC-03 | stale reference | STRUCTURAL | B-01 | Teilweise (Header/deferred) |
| DOC-04 | stale reference | SAFE DOC FIX | A-01 | ✅ |
| DOC-05 | path drift | SAFE DOC FIX | A-07 | ✅ (JSON/docs policy) |
| DOC-06 | authority drift | BLOCKED | C.1 | ❌ |
| DOC-07 | path drift | SAFE DOC FIX | A-06 | ✅ |
| DOC-08 | stale reference | SAFE DOC FIX | A-05 | ✅ |
| DOC-09 | naming duplication | SAFE DOC FIX | A-04 | ✅ |
| DOC-10 | path drift | SAFE DOC FIX | A-08 | ✅ |
| DOC-11 | authority drift | STRUCTURAL | B-03 | Teilweise (markers only) |
| DOC-12 | stale reference | STRUCTURAL | B-02 | **CLOSED** (grammar v0 + FEHLENDE §5.2.1) |

---

## 8. Empfohlene Operator-Sequenz (nach diesem Plan)

```text
Phase 1 (Safe):     A-01 → A-02 → A-03 → A-04 → A-05 → A-06 → A-07 → A-08 → A-09
Phase 2 (Structural, GO required): B-01, B-02, B-03, B-04 (docs-only specs)
Phase 3 (Authority, GO required):   AUTH-ECM-01 decision record (governance doc only)
Phase 4 (Deferred):                 DEF-* — track only, no cleanup claim
```

**Geschätzter Phase-1-Umfang:** 1 bounded Docs-PR, keine Python-Dateien außer optional `src&#47;docs&#47;peak_trade_documentation.md` (A-05 — immer noch Docs-only Inhalt). <!-- pt:ref-target-ignore -->

---

## 9. Non-Goals und Abgrenzung

| Explizit ausgeschlossen | Grund |
|-------------------------|-------|
| Registry-Alias für `ecm_cycle` | AUTH-ECM-01 BLOCKED |
| `config&#47;config.toml` Migration | Code/Config surface | <!-- pt:ref-target-ignore -->
| `breakout_confirmation_v1` Registry-Eintrag | AUTH-REG-01 / DEF-05 |
| Runtime bridge activation | DEF-01 |
| CI-Workflow-Änderung | Out of scope (A-07 nur Baseline-JSON) |
| Feature deletion / deactivation | Strict rule |
| Strategy-Layer-Refactor | Strict rule |

---

## 10. Cross-References und Closure-Kriterien

| Artefakt | Rolle nach Cleanup Phase 1 |
|----------|----------------------------|
| [`feature_state_map_v1.md`](feature_state_map_v1.md) | Kanonische Feature-Wahrheit |
| [`feature_drift_reconciliation_report_v1.md`](../audit/feature_drift_reconciliation_report_v1.md) | Frozen evidence |
| [`FEHLENDE_FEATURES_PEAK_TRADE.md`](../features/FEHLENDE_FEATURES_PEAK_TRADE.md) | Einziger gepflegter Feature Catalog |
| [`STRATEGY_ECM_ARMSTRONG_WIRING_INVENTORY_READ_MODEL_V0.md`](../ops/specs/STRATEGY_ECM_ARMSTRONG_WIRING_INVENTORY_READ_MODEL_V0.md) | ECM authority read-model (unchanged) |

**Phase-1 Closure Checklist:**

- [ ] DOC-01, DOC-02: redirect-only, kein widersprüchlicher Volltext
- [ ] DOC-04: historischer Banner gesetzt
- [ ] DOC-05, DOC-07, DOC-08, DOC-09, DOC-10: addressed in Section A steps
- [ ] DOC-06, DOC-11: remain flagged in B/C/D — **not closed**
- [x] DOC-12 / B-02: closed via `rd_strategy_status_grammar_v0` (2026-07-17)
- [ ] Kein Claim „live operational features > 0“
- [ ] Kein Claim „ECM identity resolved“ ohne AUTH-ECM-01 record

---

**Plan-Owner:** Drift Cleanup Plan v1  
**Evidence frozen at:** `2f1672bee8761f8d50def3f6ef31cc803824b2e9`  
**Nächster Schritt:** Operator GO für Phase 1 (Section A) als separater Docs-only PR
