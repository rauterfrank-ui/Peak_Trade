# Runbook — Chat-geführte Offene-Features-/Gap-Erkennung (Peak_Trade)

> **Zweck:** Du startest **eine Chat-Session** mit klarem Ziel — der Assistent **führt** Recherche und Triage im Repo aus und liefert **Aufgaben als Arbeitspakete** zurück (kein „Kommando-Sammelsurium“ für dich).  
> **Scope:** NO-LIVE; keine Secrets; Evidence-first wenn etwas behauptet wird.

---

## 1. Wo Themen im **Repo** sichtbar sind

- Ein Thema muss **nicht** als fester String in Code oder Docs vorkommen. Wenn es **nirgends** im Repo (oder auf GitHub als Issue/PR) verankert ist, ist es **noch nicht** priorisiert — es kann später über Gap-Sessions oder neue PRs/Issues eingeordnet werden.
- **Sichtbare Anker:** `docs/ops/roadmap/CURRENT_FOCUS.md`, `docs/ops/roadmap/FINISH_PLAN.md`, offene **GitHub-Issues/PRs**, sowie konkrete Pfade unter `src/` und `docs/`. Es gibt **keine** einzelne zentrale Datei für „alles“; Themen werden **verteilt** über diese Stellen (oder bewusst neue Docs unter `docs/ops/`).

---

## 2. Was „alles implementiert“ hier **nicht** automatisch heißt

- Der **Finish Plan** und **CURRENT_FOCUS** beschreiben einen **abgeschlossenen Roadmap-Strang** (u. a. PR 6–8 + Follow-ups) — **nicht** jede historische Idee oder jeden experimentellen Branch.
- **Offene Arbeit** zeigt sich typischerweise als: `TODO`/`FIXME` im **`src/`**-Code, **absichtliche** `NotImplementedError` (Research-Stubs), **dokumentierte** Lücken („planned“, „optional“, „Phase …“), oder **fehlende Tests** für einen Pfad.

---

## 3. Kanonische Einstiege (vor jeder Gap-Session)

| Rolle | Pfad |
|--------|------|
| Wo stehen wir operativ | `docs/ops/roadmap/CURRENT_FOCUS.md` |
| Roadmap + DoD + PR-Slices | `docs/ops/roadmap/FINISH_PLAN.md` |
| Navigation Runbooks / Ops | `docs/WORKFLOW_FRONTDOOR.md` |
| Session-Bootstrap (Copy-Paste) | `docs/ops/runbooks/PEAK_TRADE_CHAT_CONTINUITY_BOOTSTRAP.md` |

---

## 4. Ablauf pro Chat-Session (Assistent-geführt)

**Du gibst:** 1–3 Sätze Ziel (z. B. „Learning Loop Lücken“, „Infostream Härten“, „Kill-Switch Adapter Follow-up“).

**Der Assistent macht (ohne dass du Shell-Wände einfügen musst):**

1. **Scope fixieren** — nur `src/` / nur `docs/ops/` / nur ein Modul; NO-LIVE beachten.  
2. **Signale sammeln** — gezielt nach `TODO`/`FIXME` im gewählten Bereich, plus Doku-Querverweise.  
3. **Klassifizieren** — *absichtlicher Stub (Research)* vs. *echte Lücke* vs. *Tech-Debt*.  
4. **Priorisieren** — Risiko, Nutzen, Abhängigkeiten, ob Tests existieren.  
5. **Lieferobjekt** — Tabelle **Backlog** + **ein** empfohlener nächster PR-/Docs-Slice + ggf. Evidence-Pfad.

**Optional (nur wenn nötig):** ein kurzer Verifikationsblock (Docs-Gates, gezielter pytest) — nicht als Standard für jede Frage.

---

## 5. Snapshot — repräsentative offene Signals (nicht vollständig)

> **Hinweis:** Das ist **kein** vollständiger Repo-Scan, sondern eine **Stichprobe** aus Code/Docs, die typische **„noch offen / später / Stub“**-Muster zeigt. Der Assistent soll sie bei einer echten Session **aktualisieren und verfeinern**.

| Kategorie | Signal (Kurz) | Beispiel-Ort / Hinweis |
|-----------|----------------|-------------------------|
| Learning / Promotion | End-to-End-Konzept + domänenspezifische **Producer** auf Bridge/Emitter — **iterativ** (**NO-LIVE**); Kern-API (`emit_learning_snippet`, `normalize_patches`) **DONE** laut Stufe F2 — siehe Zeile **Learning Loop (F2)** | [`LEARNING_PROMOTION_LOOP_V1_ARCHITECTURE.md`](../../LEARNING_PROMOTION_LOOP_V1_ARCHITECTURE.md) · [`emitter.py`](../../../src/meta/learning_loop/emitter.py) · [`bridge.py`](../../../src/meta/learning_loop/bridge.py) |
| Learning Loop (F2) | Emitter & Bridge (`emit_learning_snippet`, `normalize_patches`) — **DONE** laut geordnetem Runbook; domänenspezifische Folgearbeit **iterativ** (**NO-LIVE**) | [`emitter.py`](../../../src/meta/learning_loop/emitter.py) · [`bridge.py`](../../../src/meta/learning_loop/bridge.py) · [`test_learning_loop_emitter.py`](../../../tests/meta/test_learning_loop_emitter.py) · [`test_learning_loop_bridge.py`](../../../tests/meta/test_learning_loop_bridge.py) · [`RUNBOOK_UNIMPLEMENTED_FEATURES_ORDERED.md`](./RUNBOOK_UNIMPLEMENTED_FEATURES_ORDERED.md) Stufe F2 |
| Execution Telemetry (F5) | JSONL-/Composite-Telemetry für die Pipeline (Emitter, Logger) — **DONE** laut Stufe F5; erweiterte Betriebs-Nutzung **iterativ** (**NO-LIVE**) | [`telemetry.py`](../../../src/execution/telemetry.py) · [`test_execution_telemetry.py`](../../../tests/execution/test_execution_telemetry.py) · [`RUNBOOK_UNIMPLEMENTED_FEATURES_ORDERED.md`](./RUNBOOK_UNIMPLEMENTED_FEATURES_ORDERED.md) Stufe F5 |
| New Listings (F6) | Collector-Basis (`CollectorContext`, `RawEvent`, Protocol **Collector**) — **DONE** laut Stufe F6; weitere Börsen/Quellen **iterativ** (**NO-LIVE**) | [`base.py`](../../../src/research/new_listings/collectors/base.py) · [`test_p1_collector_contract.py`](../../../tests/research/new_listings/test_p1_collector_contract.py) · [`RUNBOOK_UNIMPLEMENTED_FEATURES_ORDERED.md`](./RUNBOOK_UNIMPLEMENTED_FEATURES_ORDERED.md) Stufe F6 |
| Knowledge (F4) | Vector-DB-Adapter (u. a. Chroma und Memory-Adapter) — **DONE** laut Stufe F4; optionale Backends und Embeddings **iterativ** (**NO-LIVE**) | [`vector_db.py`](../../../src/knowledge/vector_db.py) · [`test_vector_db_memory.py`](../../../tests/knowledge/test_vector_db_memory.py) · [`RUNBOOK_UNIMPLEMENTED_FEATURES_ORDERED.md`](./RUNBOOK_UNIMPLEMENTED_FEATURES_ORDERED.md) Stufe F4 |
| Infostream (F1) | Parser & Modell — **DONE** laut Stufe F1; Robustheit/Konfig-Folgearbeit **iterativ** (**NO-LIVE**) | [`evaluator.py`](../../../src/meta/infostream/evaluator.py) · [`test_infostream_basic.py`](../../../tests/meta/test_infostream_basic.py) · [`RUNBOOK_UNIMPLEMENTED_FEATURES_ORDERED.md`](./RUNBOOK_UNIMPLEMENTED_FEATURES_ORDERED.md) Stufe F1 |
| Infostream / Zyklus | **Implementiert:** vollständiger Zyklus (**run_infostream_cycle**) — TestHealth → IntelEvents → optionale KI-Eval → Learning-Log; lokale Artefakte unter dem Standard-Infostream-Verzeichnisbaum; Vertrag und Entry-Pfade in der rechten Spalte. **Iterativ:** KI- und Quellen-Erweiterung — **NO-LIVE** | [`infostream_run_cycle.py`](../../../scripts/infostream_run_cycle.py) · [`run_cycle.py`](../../../src/meta/infostream/run_cycle.py) · [`INFOSTREAM_DELIVERY_CONTRACT.md`](../INFOSTREAM_DELIVERY_CONTRACT.md) |
| Market Outlook | **MarketSentinel v0:** CLI **generate_market_outlook_daily.py** (Features + optional LLM; Flag **--skip-llm** für Tests ohne LLM); GitHub-Workflow **market_outlook_automation.yml**. **Iterativ:** Produktionsreife, weitere Datenquellen — **NO-LIVE** | [`generate_market_outlook_daily.py`](../../../scripts/generate_market_outlook_daily.py) · [`market_outlook_automation.yml`](../../../.github/workflows/market_outlook_automation.yml) |
| Observability (H1) | HTTP-Session (`start_session_http`) und Metrics-Server (`ensure_metrics_server`) — **DONE** laut Stufe H1; weitere Betriebs-Slices **iterativ** (**NO-LIVE**) | [`session.py`](../../../src/obs/session.py) · [`metrics_server.py`](../../../src/obs/metrics_server.py) · [`RUNBOOK_UNIMPLEMENTED_FEATURES_ORDERED.md`](./RUNBOOK_UNIMPLEMENTED_FEATURES_ORDERED.md) Stufe H1 |
| Evidence (G1) | Multi-Hop-Migrationen im Evidence-Pack-Schema (`_find_migration_path`, `migration_info.chain`) — **DONE** laut Stufe G1; weitere Evidence-/Orchestration-Folgearbeit **iterativ** (**NO-LIVE**) | [`evidence_pack_schema.py`](../../../src/ai_orchestration/evidence_pack_schema.py) · [`test_evidence_pack_schema.py`](../../../tests/ai_orchestration/test_evidence_pack_schema.py) · [`RUNBOOK_UNIMPLEMENTED_FEATURES_ORDERED.md`](./RUNBOOK_UNIMPLEMENTED_FEATURES_ORDERED.md) Stufe G1 |
| Evidence (G2) | Evidence-Generator **Redaction** (`_redact_content` auf proposer/critic `content` und `rationale`) — **DONE** laut Stufe G2; erweiterte Redaction/Orchestration-Folgearbeit **iterativ** (**NO-LIVE**) | [`evidence_pack_generator.py`](../../../src/ai_orchestration/evidence_pack_generator.py) · [`test_evidence_pack_generator.py`](../../../tests/ai_orchestration/test_evidence_pack_generator.py) · [`RUNBOOK_UNIMPLEMENTED_FEATURES_ORDERED.md`](./RUNBOOK_UNIMPLEMENTED_FEATURES_ORDERED.md) Stufe G2 |
| Evidence (G3) | Psychology-Heatmap „echte Analyse“ (`compute_psychology_heatmap_from_events`, `TriggerTrainingPsychEventFeatures`; Legacy-Extraktion in `psychology_heatmap.py` deprecated) — **DONE** laut Stufe G3; weitere Reporting-/Heatmap-Folgearbeit **iterativ** (**NO-LIVE**) | [`psychology_heuristics.py`](../../../src/reporting/psychology_heuristics.py) · [`test_psychology_heuristics.py`](../../../tests/reporting/test_psychology_heuristics.py) · [`RUNBOOK_UNIMPLEMENTED_FEATURES_ORDERED.md`](./RUNBOOK_UNIMPLEMENTED_FEATURES_ORDERED.md) Stufe G3 |
| Evidence (G4) | TestHealth-Runner **Historie** für Trends (`compute_test_health_stats_for_triggers` aus `history.json`) — **DONE** laut Stufe G4; weitere TestHealth-/Trend-Folgearbeit **iterativ** (**NO-LIVE**) | [`test_health_history.py`](../../../src/ops/test_health_history.py) · [`test_test_health_runner.py`](../../../tests/ops/test_test_health_runner.py) · [`RUNBOOK_UNIMPLEMENTED_FEATURES_ORDERED.md`](./RUNBOOK_UNIMPLEMENTED_FEATURES_ORDERED.md) Stufe G4 |
| Live / Safety | **SafetyGuard** + Execution-Guards (env-gated, offline in Tests); Blockpfade für Paper und Live; **keine** echten Live-Order-Calls (Architektur gemäß Modul-Doku); Wiring-Tests in der rechten Spalte — **NO-LIVE** | [`safety.py`](../../../src/live/safety.py) · [`test_safety_exec_guards_wiring.py`](../../../tests/live/test_safety_exec_guards_wiring.py) |
| Risk / Kill-Switch | **D2 erledigt:** Legacy-Adapter entfernt, State-Machine kanonisch (siehe geordnetes Runbook Stufe D2); Archiv-Note **TODO_KILL_SWITCH_ADAPTER_MIGRATION.md** dokumentiert Abschluss. **Iterativ:** vereinzelte historische Verweise in anderen Risk-Docs — **NO-LIVE** | [`TODO_KILL_SWITCH_ADAPTER_MIGRATION.md`](../../../TODO_KILL_SWITCH_ADAPTER_MIGRATION.md) |
| Execution / Orders (C1) | **STUB/GAP** laut Stufe C1: **LiveOrderExecutor** nur Dry-Run/Design; **ExchangeOrderExecutor**-Stub (Live-Exchange nicht implementiert); Testnet-Pfad (**testnet_executor**) separat und **keine** C1-Live-Freigabe — **NO-LIVE** | [`RUNBOOK_UNIMPLEMENTED_FEATURES_ORDERED.md`](./RUNBOOK_UNIMPLEMENTED_FEATURES_ORDERED.md) Stufe C1 · [`exchange.py`](../../../src/orders/exchange.py) · [`paper.py`](../../../src/orders/paper.py) |
| Backtest / Engine | Tracker-Integration — **I1 erledigt** (Fehler im Tracker brechen Backtest nicht ab; Tests) | [`RUNBOOK_UNIMPLEMENTED_FEATURES_ORDERED.md`](./RUNBOOK_UNIMPLEMENTED_FEATURES_ORDERED.md) Stufe I1 · [`tests/backtest/test_engine_tracking.py`](../../../tests/backtest/test_engine_tracking.py) |
| Research-Stubs | Bouchaud / Gatheral-Cont-Beispiele laut geordnetem Runbook **E3 DONE** (deterministische 0/1-Signale, OHLCV-Proxys); andere R&D-Strategien mit absichtlichen Stubs **iterativ** — **NO-LIVE** | [`bouchaud_microstructure_strategy.py`](../../../src/strategies/bouchaud/bouchaud_microstructure_strategy.py) · [`vol_regime_overlay_strategy.py`](../../../src/strategies/gatheral_cont/vol_regime_overlay_strategy.py) · [`test_bouchaud_gatheral_cont_strategies.py`](../../../tests/test_bouchaud_gatheral_cont_strategies.py) · [`RUNBOOK_UNIMPLEMENTED_FEATURES_ORDERED.md`](./RUNBOOK_UNIMPLEMENTED_FEATURES_ORDERED.md) Stufe E3 |
| ML / Meta-Labeling | Research-only (López-de-Prado-Meta-Labeling): **implementiert** — `apply_meta_model`, `compute_meta_labels`, `compute_bet_size`, `_create_model` (Random Forest, optional XGBoost); unbekannte `model_type` → `NotImplementedError`; weitere Backends / Pipeline-Orchestrierung **iterativ** — **NO-LIVE** | [`meta_labeling.py`](../../../src/research/ml/meta/meta_labeling.py) · [`test_meta_labeling.py`](../../../tests/test_meta_labeling.py) |
| Scripts | Evidence-Metadaten `symbol` via `resolve_backtest_symbol()` (**NO-LIVE**) | [`run_backtest.py`](../../../scripts/run_backtest.py) |
| J1 Forward (Scripts) | Operator-Kurzreferenz **NO-LIVE** (Quellen **dummy** oder **kraken**, ``--n-bars``, Portfolio, ``_shared_forward_args``); voller Markt-Ersatz für Dummy weiter **STUB** | PR #2267 · [Forward-Pipeline (Stufe J)](RUNBOOK_UNIMPLEMENTED_FEATURES_ORDERED.md#stufe-j--scripts--demo-daten-operativ-niedrig-priorisiert) · [`test_forward_generate_evaluate_integration_smoke.py`](../../../tests/test_forward_generate_evaluate_integration_smoke.py) |
| J1 Forward (Demo-Stub) | Offline **Generate→Evaluate** (Dummy); **as_of** wie Integrationssmoke; Ausgabe unter **.ops_local** (Unterordner **forward_dummy_pipeline_demo**, gitignored) — **NO-LIVE**; Operator-Kurzreferenz **§6** | PR #2297 · [`run_forward_dummy_pipeline_demo.sh`](../../../scripts/dev/run_forward_dummy_pipeline_demo.sh) · [Operator-Kurzreferenz (J1)](RUNBOOK_UNIMPLEMENTED_FEATURES_ORDERED.md#operator-kurzreferenz-j1-forward-no-live) · [`test_forward_generate_evaluate_integration_smoke.py`](../../../tests/test_forward_generate_evaluate_integration_smoke.py) |
| Ops / Navigation | Chat-led ↔ Stufe J (geordnete Stub-Liste) verlinkt | PR #2182 — [Verwandte Dokumente](#verwandte-dokumente) · [RUNBOOK_UNIMPLEMENTED_FEATURES_ORDERED.md](./RUNBOOK_UNIMPLEMENTED_FEATURES_ORDERED.md) |
| Truth / Docs governance | Repo-Truth-Claims + Docs-Drift-Kaskade für Branch-Protection-Registry (**NO-LIVE**) | PR #2256 / PR #2257 · [`TRUTH_CORE.md`](../registry/TRUTH_CORE.md) · [`repo_truth_claims.yaml`](../../../config/ops/repo_truth_claims.yaml) |
| J3 / Inventar | Lokales Placeholder-Inventar; optional **`--prefix`** für Teilbäume | PR #2259 · [`generate_placeholder_reports.py`](../../../scripts/ops/placeholders/generate_placeholder_reports.py) · [Stufe J](./RUNBOOK_UNIMPLEMENTED_FEATURES_ORDERED.md#stufe-j--scripts--demo-daten-operativ-niedrig-priorisiert) |

**Interpretation:** Viele Einträge sind **keine** „vergessenen Produktfeatures“, sondern **bewusste** Stufen (Research, NO-LIVE, Phase-X). Der Wert der Liste ist **Transparenz** und **Priorisierung**, nicht Schuldzuweisung.

---

## 6. Was du in den Chat schreiben kannst (kurze Vorlage)

```text
Ziel: Offene Features / Gaps im Bereich [THEMA] identifizieren und priorisieren.
Kanonisch: CURRENT_FOCUS + FINISH_PLAN + WORKFLOW_FRONTDOOR.
Bitte: Assistent-geführte Triage in src/… (und passende docs), Ergebnis als Tabelle + 1 empfohlener nächster Slice.
Constraints: NO-LIVE, keine Secrets, Evidence wenn Behauptungen über „fertig“.
```

---

## 7. Anhang — nur wenn du technisch verifizieren willst

Changed-scope Docs-Gates (nach Doc-Edits):

```bash
bash scripts/ops/pt_docs_gates_snapshot.sh --changed
```

---

## Verwandte Dokumente

- [Current focus](../roadmap/CURRENT_FOCUS.md)  
- [Finish Plan](../roadmap/FINISH_PLAN.md)  
- [Workflow Frontdoor](../../WORKFLOW_FRONTDOOR.md)  
- [Chat continuity bootstrap](./PEAK_TRADE_CHAT_CONTINUITY_BOOTSTRAP.md)
- [Unimplemented features (ordered)](./RUNBOOK_UNIMPLEMENTED_FEATURES_ORDERED.md) — u. a. **Stufe J** (Forward-Pipeline-Stub, Scripts/Demos); ergänzt diese Chat-Triage um priorisierte Repo-Anker (**kein** Ersatz für Gap-Sessions).
